"""Pydantic validation and serialization schemas for real-time alerts (Chunk M3-11 / M6-05)."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


class AlertAcknowledgeRequest(BaseModel):
    """Payload for acknowledging an operational alert."""

    officer_name: str = Field("District Disaster Officer", description="Name of acknowledging officer")


class OperationalAlertRead(BaseModel):
    """Operational alert item conforming to M3-11 / M6-05 frontend contracts."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Alert classification type")
    severity: str = Field(..., description="Severity level (info, warning, severe, extreme)")
    danger_level: Optional[str] = Field(None, description="Corroborated danger level")
    status: str = Field("triggered", description="Trigger status (no_trigger, triggered, insufficient_data)")
    headline: str = Field(..., description="Short broadcast headline")
    message: str = Field(..., description="Detailed emergency instruction")
    village_id: Optional[str] = Field(None, description="Associated village ID")
    village_name: Optional[str] = Field(None, description="Associated village name")
    district_id: Optional[str] = Field(None, description="Associated district ID")
    district_name: Optional[str] = Field(None, description="Associated district name")
    coordinates: Optional[Tuple[float, float]] = Field(None, description="[lon, lat] WGS84")
    indicator: str = Field("rainfall_24h", description="Physical trigger indicator")
    observed_value: Optional[float] = Field(None, description="Measured sensor/telemetry value")
    configured_threshold: Optional[float] = Field(None, description="Trigger limit threshold")
    operator: str = Field(">=", description="Comparison operator")
    unit: Optional[str] = Field("mm", description="Measurement unit")
    buffer_m: Optional[float] = Field(500.0, description="Hazard perimeter buffer in meters")
    is_acknowledged: bool = Field(False, description="Duty officer acknowledgment status")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    acknowledged_by: Optional[str] = Field(None, description="Officer who acknowledged the alert")
    issued_at: datetime = Field(..., description="Alert issuance timestamp")
    expires_at: Optional[datetime] = Field(None, description="Alert expiration timestamp")
    candidate_id: Optional[str] = Field(None, description="Associated dynamic red zone candidate ID")
    source_id: Optional[str] = Field(None, description="Telemetry provider source identifier")
    is_synthetic: bool = Field(True, description="Synthetic demo flag")
    explainability: Optional[Dict[str, Any]] = Field(None, description="Trigger audit and explainability details")
