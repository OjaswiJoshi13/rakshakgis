"""API v1 router for real-time alerts and threshold warnings (Chunk M3-11 / M6-05)."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import UserRole, require_roles
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.governance import User
from app.models.telemetry import Alert
from app.schemas.alerts import AlertAcknowledgeRequest, OperationalAlertRead
from app.schemas.common import ResponseEnvelope

alerts_router = APIRouter()


def _db_alert_to_operational(alert: Alert) -> OperationalAlertRead:
    """Convert SQLAlchemy Alert model to OperationalAlertRead."""
    meta = (getattr(alert.village, "metadata_json", {}) if alert.village else {}) or {}
    alert_meta = getattr(alert, "metadata_json", {}) or {}

    coords = None
    if alert.village and hasattr(alert.village.location, "data"):
        from geoalchemy2.shape import to_shape
        try:
            pt = to_shape(alert.village.location)
            coords = (float(pt.x), float(pt.y))
        except Exception:
            pass

    headline = alert.headline
    message = alert.message
    source_id = alert_meta.get("source_id", "synthetic_rainfall_gauge")
    indicator = alert_meta.get("indicator", "rainfall_24h")

    # Truthfulness correction: If an alert claims satellite InSAR or field observation from a synthetic source, make the synthetic nature explicit
    if "insar" in (message or "").lower() or "insar" in (headline or "").lower():
        headline = "SIMULATION / SYNTHETIC WARNING: Ground Deformation Threshold Breach"
        message = (
            "Simulated ground-deformation threshold breach (>15mm/month) in synthetic simulation input. "
            "Scenario evaluation parameter — not an official observed satellite InSAR measurement."
        )
        source_id = "synthetic_simulation_input"
        indicator = "simulated_ground_deformation"

    return OperationalAlertRead(
        id=f"ALT-{alert.id}",
        alert_type=alert.alert_type,
        severity=alert.severity,
        danger_level=alert_meta.get("danger_level", "HIGH"),
        status=alert_meta.get("status", "triggered"),
        headline=headline,
        message=message,
        village_id=str(alert.village_id) if alert.village_id else None,
        village_name=alert.village.name if alert.village else alert_meta.get("village_name"),
        district_id=str(alert.district_id) if alert.district_id else None,
        district_name=alert.district.name if alert.district else "Chamoli District",
        coordinates=coords,
        indicator=indicator,
        observed_value=alert_meta.get("observed_value"),
        configured_threshold=alert_meta.get("configured_threshold"),
        operator=alert_meta.get("operator", ">="),
        unit=alert_meta.get("unit", "mm"),
        buffer_m=alert_meta.get("buffer_m", 500.0),
        is_acknowledged=alert.is_acknowledged,
        acknowledged_at=getattr(alert, "acknowledged_at", None),
        acknowledged_by=alert.acknowledged_by.full_name if alert.acknowledged_by else alert_meta.get("acknowledged_by"),
        issued_at=alert.issued_at,
        expires_at=alert.expires_at,
        candidate_id=alert_meta.get("candidate_id"),
        source_id=source_id,
        is_synthetic=True,
        explainability=alert_meta.get("explainability"),
    )


@alerts_router.get(
    "",
    response_model=ResponseEnvelope[List[OperationalAlertRead]],
    summary="List operational alerts",
    description="Retrieve threshold breach alerts with optional status and severity filtering.",
)
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by alert severity"),
    status: Optional[str] = Query(None, description="Filter by trigger status"),
    indicator: Optional[str] = Query(None, description="Filter by physical hazard indicator"),
    is_acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    search: Optional[str] = Query(None, description="Search keyword in headline, message, or settlement"),
    db: Session = Depends(get_db),
):
    """Retrieve operational alerts."""
    query = db.query(Alert)

    if severity is not None and severity != "all":
        query = query.filter(Alert.severity == severity.lower().strip())

    if is_acknowledged is not None:
        query = query.filter(Alert.is_acknowledged == is_acknowledged)

    if search is not None and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(Alert.headline.ilike(pattern) | Alert.message.ilike(pattern))

    alerts = query.order_by(Alert.issued_at.desc()).all()
    items = [_db_alert_to_operational(a) for a in alerts]

    # In-memory filter for metadata attributes if needed
    if indicator and indicator != "all":
        items = [i for i in items if i.indicator == indicator]
    if status and status != "all":
        items = [i for i in items if i.status == status]

    return ResponseEnvelope(success=True, data=items)


@alerts_router.get(
    "/{id}",
    response_model=ResponseEnvelope[OperationalAlertRead],
    summary="Get alert details by ID",
    description="Retrieve full alert trigger details, explainability, and audit trail.",
)
def get_alert(
    id: str = Path(..., description="Alert identifier (ALT-1 or integer)"),
    db: Session = Depends(get_db),
):
    """Retrieve single alert by ID."""
    clean_id = id.replace("ALT-", "").strip()
    try:
        numeric_id = int(clean_id)
    except ValueError:
        raise NotFoundError(message=f"Alert with ID '{id}' was not found.")

    alert = db.query(Alert).filter(Alert.id == numeric_id).first()
    if not alert:
        raise NotFoundError(message=f"Alert with ID '{id}' was not found.")

    return ResponseEnvelope(success=True, data=_db_alert_to_operational(alert))


@alerts_router.post(
    "/{id}/acknowledge",
    response_model=ResponseEnvelope[OperationalAlertRead],
    summary="Acknowledge alert",
    description="Record officer sign-off and acknowledgment for an operational alert.",
)
def acknowledge_alert(
    id: str = Path(..., description="Alert identifier (ALT-1 or integer)"),
    payload: Optional[AlertAcknowledgeRequest] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)),
    db: Session = Depends(get_db),
):
    """Acknowledge single alert."""
    clean_id = id.replace("ALT-", "").strip()
    try:
        numeric_id = int(clean_id)
    except ValueError:
        raise NotFoundError(message=f"Alert with ID '{id}' was not found.")

    alert = db.query(Alert).filter(Alert.id == numeric_id).first()
    if not alert:
        raise NotFoundError(message=f"Alert with ID '{id}' was not found.")

    officer_name = payload.officer_name if (payload and payload.officer_name) else (current_user.full_name or current_user.username)

    alert.is_acknowledged = True
    alert.acknowledged_by_user_id = current_user.id
    db.commit()
    db.refresh(alert)

    read_model = _db_alert_to_operational(alert)
    read_model.is_acknowledged = True
    read_model.acknowledged_by = officer_name
    read_model.acknowledged_at = datetime.now(timezone.utc)

    return ResponseEnvelope(success=True, data=read_model)


@alerts_router.post(
    "/acknowledge-all",
    response_model=ResponseEnvelope[dict],
    summary="Acknowledge all alerts",
    description="Bulk acknowledge all unacknowledged active alerts.",
)
def acknowledge_all_alerts(
    payload: Optional[AlertAcknowledgeRequest] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)),
    db: Session = Depends(get_db),
):
    """Bulk acknowledge active alerts."""
    unacked = db.query(Alert).filter(Alert.is_acknowledged == False).all()
    count = len(unacked)

    for a in unacked:
        a.is_acknowledged = True
        a.acknowledged_by_user_id = current_user.id

    db.commit()
    return ResponseEnvelope(success=True, data={"acknowledged_count": count})
