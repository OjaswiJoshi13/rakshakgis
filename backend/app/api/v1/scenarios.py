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


def _get_default_pilot_inputs() -> Tuple[List[VillageSimulationInput], List[SiteSimulationInput]]:
    """Load default representative inputs from the deterministic Himalayan pilot dataset."""
    dataset = load_himalayan_pilot_dataset()

    # Load 5 sample villages representing valley and high slope corridors
    sample_villages: List[VillageSimulationInput] = []
    for f in dataset.villages.features[:5]:
        props = f.properties
        coords = _extract_lon_lat(f.geometry, (79.565, 30.555))
        demo = getattr(props, "demographics", {}) or {}
        risk_data = getattr(props, "risk", {}) or {}

        hh = demo.get("households", 50) if isinstance(demo, dict) else getattr(demo, "households", 50)
        pop = demo.get("total_population", 200) if isinstance(demo, dict) else getattr(demo, "total_population", 200)
        c_score = risk_data.get("composite_score", 50.0) if isinstance(risk_data, dict) else getattr(risk_data, "composite_score", 50.0)

        sample_villages.append(
            VillageSimulationInput(
                village_id=props.id,
                village_name=props.name,
                location=coords,
                households=int(hh),
                population=int(pop),
                elderly_count=int(demo.get("elderly", 10) if isinstance(demo, dict) else 10),
                children_count=int(demo.get("children", 20) if isinstance(demo, dict) else 20),
                hazard_severity=float(c_score),
                flood_exposure=40.0,
                rainfall_intensity=float(c_score * 0.8),
                slope_landslide_susceptibility=float(c_score * 0.9),
                rainfall_24h_mm=45.0,
            )
        )

    # Load 4 sample candidate sites
    sample_sites: List[SiteSimulationInput] = []
    for f in dataset.candidate_sites.features[:4]:
        props = f.properties
        coords = _extract_lon_lat(f.geometry, (79.430, 30.430))
        caps = getattr(props, "capacities", {}) or {}

        max_hh = caps.get("max_households", 120) if isinstance(caps, dict) else getattr(caps, "max_households", 120)

        sample_sites.append(
            SiteSimulationInput(
                site_id=props.id,
                site_name=props.name,
                location=coords,
                terrain_slope_deg=float(getattr(props, "slope_deg", 5.0) or 5.0),
                hazard_buffer_distance_m=1000.0,
                housing_capacity=int(max_hh),
                water_capacity=int(max_hh),
                sanitation_capacity=int(max_hh),
                healthcare_capacity=int(max_hh),
                shelter_capacity=int(max_hh),
            )
        )

    return sample_villages, sample_sites

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

    # 3. Resolve Inputs (Caller-provided or fallback to synthetic pilot defaults)
    if payload.villages and payload.sites:
        villages = payload.villages
        sites = payload.sites
    else:
        def_vills, def_sites = _get_default_pilot_inputs()
        villages = payload.villages or def_vills
        sites = payload.sites or def_sites

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
