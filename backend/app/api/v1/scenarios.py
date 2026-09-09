"""FastAPI router for scenario simulation and what-if analysis (Chunk M4-06)."""

from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import UserRole, get_current_user, require_roles
from app.core.database import get_db
from app.core.profiles import get_profile
from app.models.governance import User
from app.core.scenarios.contracts import (
    ScenarioParameters,
    ScenarioSimulationOutput,
    ScenarioType,
    SiteSimulationInput,
    VillageSimulationInput,
)
from app.core.scenarios.definitions import (
    CANONICAL_SCENARIOS,
    ScenarioDefinition,
    get_scenario_definition,
    list_scenario_definitions,
)
from app.core.scenarios.engine import ScenarioSimulatorEngine
from app.core.scenarios.errors import (
    InsufficientScenarioDataError,
    InvalidScenarioParameterError,
    ScenarioError,
    ScenarioExecutionError,
    UnknownScenarioTypeError,
)
from app.data.synthetic.loader import load_himalayan_pilot_dataset
from app.models.scenarios import Scenario, ScenarioRun
from app.schemas.common import ResponseEnvelope
from app.schemas.scenarios import (
    ScenarioCreate,
    ScenarioDefinitionRead,
    ScenarioRead,
    ScenarioRunRecordRead,
    ScenarioRunRequest,
)

scenarios_router = APIRouter()


def _extract_lon_lat(geometry_or_coords: Any, default: Tuple[float, float] = (79.50, 30.50)) -> Tuple[float, float]:
    """Deterministically extract a (lon, lat) tuple from Point or Polygon geometries."""
    if not geometry_or_coords:
        return default
    c = getattr(geometry_or_coords, "coordinates", geometry_or_coords)
    while isinstance(c, (list, tuple)) and len(c) > 0 and isinstance(c[0], (list, tuple)):
        c = c[0]
    if isinstance(c, (list, tuple)) and len(c) >= 2:
        try:
            return (float(c[0]), float(c[1]))
        except (ValueError, TypeError):
            return default
    return default


def _get_region_inputs(db: Session, region_id: str) -> Tuple[List[VillageSimulationInput], List[SiteSimulationInput]]:
    """Load canonical operational inputs from the database for the active region."""
    from sqlalchemy.orm import joinedload
    from geoalchemy2.shape import to_shape
    from app.core.regions.resolver import resolve_region_scope, apply_region_scope_to_village_query
    from app.models.geographic import Village
    from app.models.relocation import CandidateSite

    scope = resolve_region_scope(db, region_id)
    v_query = db.query(Village).options(
        joinedload(Village.population_profile),
        joinedload(Village.vulnerability_profile),
        joinedload(Village.risk_scores),
    )
    v_query = apply_region_scope_to_village_query(v_query, scope)
    v_records = v_query.all()

    villages: List[VillageSimulationInput] = []
    for v in v_records:
        coords = (79.565, 30.555)
        if v.location:
            try:
                pt = to_shape(v.location)
                coords = (float(pt.x), float(pt.y))
            except Exception:
                pass

        pop = v.population_profile.total_population if v.population_profile else 100
        hh = v.population_profile.households if v.population_profile else max(1, pop // 4)
        elderly = v.population_profile.elderly_count if v.population_profile else 0
        children = v.population_profile.children_count if v.population_profile else 0
        disabled = v.population_profile.disabled_count if v.population_profile else 0

        current_risk = next((r for r in v.risk_scores if r.is_current), None)
        if not current_risk and v.risk_scores:
            current_risk = v.risk_scores[0]

        score = float(current_risk.score) if current_risk and current_risk.score is not None else 50.0

        villages.append(
            VillageSimulationInput(
                village_id=str(v.id),
                village_name=v.name,
                location=coords,
                households=int(hh),
                population=int(pop),
                elderly_count=int(elderly),
                children_count=int(children),
                disabled_count=int(disabled),
                hazard_severity=score,
                flood_exposure=score * 0.7,
                rainfall_intensity=score * 0.8,
                slope_landslide_susceptibility=float(v.slope_deg) if v.slope_deg else score * 0.9,
                rainfall_24h_mm=45.0,
            )
        )

    # Load candidate sites for region
    sites_query = db.query(CandidateSite).options(joinedload(CandidateSite.capacities))
    if scope.district_ids:
        sites_query = sites_query.filter(CandidateSite.district_id.in_(scope.district_ids))
    site_records = sites_query.all()

    sites: List[SiteSimulationInput] = []
    for s in site_records:
        coords = (79.430, 30.430)
        if s.location:
            try:
                pt = to_shape(s.location)
                coords = (float(pt.x), float(pt.y))
            except Exception:
                pass

        cap = s.capacities[0] if s.capacities else None
        max_hh = cap.max_households if cap else 100

        sites.append(
            SiteSimulationInput(
                site_id=str(s.id),
                site_name=s.name,
                location=coords,
                terrain_slope_deg=float(s.terrain_slope_deg) if s.terrain_slope_deg else 5.0,
                hazard_buffer_distance_m=1000.0,
                housing_capacity=int(max_hh),
                water_capacity=int(max_hh),
                sanitation_capacity=int(max_hh),
                healthcare_capacity=int(max_hh),
                shelter_capacity=int(max_hh),
            )
        )

    return villages, sites


Tuple_Inputs = tuple[List[VillageSimulationInput], List[SiteSimulationInput]]


# =============================================================================
# Scenarios Catalog & CRUD
# =============================================================================

@scenarios_router.get(
    "",
    response_model=ResponseEnvelope[List[ScenarioDefinitionRead]],
    summary="List available scenario definitions",
)
def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[List[ScenarioDefinitionRead]]:
    """Return catalog of built-in canonical scenarios and registered custom scenarios."""
    canonical = list_scenario_definitions()
    items: List[ScenarioDefinitionRead] = [
        ScenarioDefinitionRead(
            scenario_type=c.scenario_type.value,
            name=c.name,
            description=c.description,
            default_parameters=c.default_parameters,
            is_canonical=True,
            tags=c.tags,
        )
        for c in canonical
    ]

    # Include custom scenarios from database if any
    custom_records = db.query(Scenario).all()
    for rec in custom_records:
        items.append(
            ScenarioDefinitionRead(
                scenario_type=f"CUSTOM_{rec.id}",
                name=rec.name,
                description=rec.description or "Custom scenario",
                default_parameters=ScenarioParameters(
                    scenario_type=ScenarioType.CUSTOM,
                    rainfall_multiplier=rec.rainfall_multiplier,
                    road_blockage_percentage=rec.road_blockage_percentage,
                    seismic_intensity_mmi=rec.seismic_intensity_mmi,
                    custom_overrides=rec.parameters_json or {},
                ),
                is_canonical=False,
                tags=["custom", f"id:{rec.id}"],
            )
        )

    return ResponseEnvelope(data=items)


@scenarios_router.post(
    "",
    response_model=ResponseEnvelope[ScenarioRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a custom scenario definition",
)
def create_custom_scenario(
    payload: ScenarioCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER)),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ScenarioRead]:
    """Persist a new custom scenario definition to the database."""
    scenario = Scenario(
        name=payload.name,
        description=payload.description,
        created_by_user_id=current_user.id,
        rainfall_multiplier=payload.rainfall_multiplier,
        seismic_intensity_mmi=payload.seismic_intensity_mmi,
        road_blockage_percentage=payload.road_blockage_percentage,
        parameters_json=payload.parameters_json,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return ResponseEnvelope(data=ScenarioRead.model_validate(scenario))


@scenarios_router.get(
    "/{scenario_id}",
    response_model=ResponseEnvelope[ScenarioRead],
    summary="Retrieve custom scenario definition by ID",
)
def get_scenario_by_id(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ScenarioRead]:
    """Retrieve a persisted custom scenario definition."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID {scenario_id} not found.",
        )
    return ResponseEnvelope(data=ScenarioRead.model_validate(scenario))


# =============================================================================
# Scenario Simulation Execution
# =============================================================================

@scenarios_router.post(
    "/run",
    response_model=ResponseEnvelope[ScenarioSimulationOutput],
    summary="Execute end-to-end what-if scenario simulation",
)
def run_scenario_simulation(
    payload: ScenarioRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ScenarioSimulationOutput]:
    """Execute scenario simulation pipeline across all 7 domain engines.

    Runs baseline pipeline, applies input modifications, runs scenario pipeline,
    computes deterministic before-vs-after comparison, and returns detailed results.
    """
    # 1. Validate scenario type
    st_raw = payload.scenario_type.strip().upper()
    try:
        scenario_type = ScenarioType(st_raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario_type '{payload.scenario_type}'. Supported types: {[t.value for t in ScenarioType]}",
        )

    # 2. Resolve Region Profile
    prof_id = payload.region_profile_id or "himalayan_pilot"
    try:
        profile = get_profile(prof_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region profile '{prof_id}' not found: {str(e)}",
        )

    # 3. Resolve Inputs (Caller-provided or query canonical database for region)
    if payload.villages and payload.sites:
        villages = payload.villages
        sites = payload.sites
    else:
        db_vills, db_sites = _get_region_inputs(db, prof_id)
        villages = payload.villages or db_vills
        sites = payload.sites or db_sites

    if not villages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No operational settlements found for region '{prof_id}'.",
        )

    # 4. Instantiate and run simulator engine
    engine = ScenarioSimulatorEngine(profile=profile)

    try:
        sim_output = engine.run_simulation(
            scenario_type=scenario_type,
            parameters=payload.parameters,
            villages=villages,
            sites=sites,
            region_profile_id=prof_id,
        )
    except InvalidScenarioParameterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except InsufficientScenarioDataError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except ScenarioExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage '{e.stage}' failed: {e.message}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario execution failed: {str(e)}",
        )

    # 5. Handle optional persistence
    if payload.persist:
        # Find or create a matching Scenario record
        sc_record = (
            db.query(Scenario)
            .filter(Scenario.name == sim_output.scenario_name)
            .first()
        )
        if not sc_record:
            sc_record = Scenario(
                name=sim_output.scenario_name,
                description=f"Auto-generated scenario record for {scenario_type.value}",
                created_by_user_id=current_user.id,
                rainfall_multiplier=sim_output.parameters.rainfall_multiplier,
                road_blockage_percentage=sim_output.parameters.road_blockage_percentage,
                seismic_intensity_mmi=sim_output.parameters.seismic_intensity_mmi,
                parameters_json=sim_output.parameters.model_dump(),
            )
            db.add(sc_record)
            db.commit()
            db.refresh(sc_record)

        run_record = ScenarioRun(
            scenario_id=sc_record.id,
            executed_by_user_id=current_user.id,
            status="completed",
            simulated_affected_villages=sim_output.scenario_metrics.get("critical_risk_villages", 0),
            simulated_displaced_population=sim_output.scenario_metrics.get("unassigned_households", 0),
            results_summary_json=sim_output.model_dump(),
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)
        sim_output.scenario_id = sc_record.id

    return ResponseEnvelope(data=sim_output)


@scenarios_router.get(
    "/runs/{run_id}",
    response_model=ResponseEnvelope[ScenarioRunRecordRead],
    summary="Retrieve persisted scenario run by ID",
)
def get_scenario_run_by_id(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ScenarioRunRecordRead]:
    """Retrieve execution metrics and results of a persisted scenario run."""
    run_rec = db.query(ScenarioRun).filter(ScenarioRun.id == run_id).first()
    if not run_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario run record with ID {run_id} not found.",
        )
    return ResponseEnvelope(data=ScenarioRunRecordRead.model_validate(run_rec))
