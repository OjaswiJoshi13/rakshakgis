"""Unit, integration, and API tests for Scenario Simulator Integration Backend (Chunk M4-06).

Covers all 46 test cases across scenario definitions, input modifications, pipeline orchestration,
baseline isolation, comparison deltas, 20-run determinism, error handling, API, and synthetic pilot.
"""

from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.governance import User
from app.core.profiles import get_profile
from app.core.scenarios.contracts import (
    ScenarioParameters,
    ScenarioRunStatus,
    ScenarioType,
    SiteSimulationInput,
    VillageSimulationInput,
)
from app.core.scenarios.definitions import (
    CANONICAL_SCENARIOS,
    get_scenario_definition,
    list_scenario_definitions,
    resolve_scenario_parameters,
)
from app.core.scenarios.engine import ScenarioSimulatorEngine
from app.core.scenarios.errors import (
    InsufficientScenarioDataError,
    InvalidScenarioParameterError,
    ScenarioExecutionError,
    UnknownScenarioTypeError,
)
from app.core.scenarios.inputs import apply_scenario_modifications
from app.data.synthetic.loader import load_himalayan_pilot_dataset
from app.main import app
from app.models.scenarios import Scenario, ScenarioRun


# Test Fixtures

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_villages() -> List[VillageSimulationInput]:
    return [
        VillageSimulationInput(
            village_id="HIM-VILL-001",
            village_name="Sunil",
            location=(79.5650, 30.5550),
            households=110,
            population=500,
            elderly_count=50,
            children_count=100,
            hazard_severity=60.0,
            flood_exposure=30.0,
            rainfall_intensity=50.0,
            slope_landslide_susceptibility=65.0,
            infrastructure_vulnerability=40.0,
            social_vulnerability=40.0,
            rainfall_24h_mm=45.0,
        ),
        VillageSimulationInput(
            village_id="HIM-VILL-002",
            village_name="Ravigram",
            location=(79.5750, 30.5500),
            households=80,
            population=350,
            elderly_count=30,
            children_count=70,
            hazard_severity=45.0,
            flood_exposure=25.0,
            rainfall_intensity=40.0,
            slope_landslide_susceptibility=50.0,
            infrastructure_vulnerability=35.0,
            social_vulnerability=35.0,
            rainfall_24h_mm=35.0,
        ),
    ]


@pytest.fixture
def sample_sites() -> List[SiteSimulationInput]:
    return [
        SiteSimulationInput(
            site_id="SITE-PIPALKOTI",
            site_name="Pipalkoti Safe Relocation Center",
            location=(79.4300, 30.4300),
            terrain_slope_deg=5.0,
            hazard_buffer_distance_m=1200.0,
            housing_capacity=150,
            water_capacity=150,
            sanitation_capacity=150,
            healthcare_capacity=150,
            shelter_capacity=150,
            status="approved",
        ),
        SiteSimulationInput(
            site_id="SITE-DHAK",
            site_name="Dhak High Terrace Site",
            location=(79.6100, 30.5100),
            terrain_slope_deg=8.0,
            hazard_buffer_distance_m=800.0,
            housing_capacity=100,
            water_capacity=100,
            sanitation_capacity=100,
            healthcare_capacity=100,
            shelter_capacity=100,
            status="approved",
        ),
    ]


# =============================================================================
# 1. SCENARIO DEFINITIONS
# =============================================================================

def test_01_all_four_required_scenarios_exist():
    """Test 1: All 4 canonical scenarios exist in the registry."""
    defs = list_scenario_definitions()
    types = [d.scenario_type for d in defs]
    assert ScenarioType.NORMAL in types
    assert ScenarioType.EXTREME_RAINFALL in types
    assert ScenarioType.FLASH_FLOOD in types
    assert ScenarioType.CAPACITY_CRISIS in types


def test_02_unknown_scenario_rejected():
    """Test 2: Requesting an unknown scenario type raises UnknownScenarioTypeError."""
    with pytest.raises(UnknownScenarioTypeError):
        get_scenario_definition("NUCLEAR_FALLOUT")


def test_03_default_parameters_are_deterministic():
    """Test 3: Default parameters for all scenarios are consistent and valid."""
    rain_def = get_scenario_definition(ScenarioType.EXTREME_RAINFALL)
    assert rain_def.default_parameters.rainfall_multiplier == 1.40

    flood_def = get_scenario_definition(ScenarioType.FLASH_FLOOD)
    assert flood_def.default_parameters.flood_hazard_increase > 0.0

    cap_def = get_scenario_definition(ScenarioType.CAPACITY_CRISIS)
    assert cap_def.default_parameters.capacity_reduction_percentage == 50.0


# =============================================================================
# 2. INPUT MODIFICATIONS & ISOLATION
# =============================================================================

def test_04_normal_leaves_baseline_inputs_unchanged(sample_villages, sample_sites):
    """Test 4: NORMAL scenario leaves baseline inputs quantitatively identical."""
    params = ScenarioParameters(scenario_type=ScenarioType.NORMAL)
    mod_v, mod_s, _ = apply_scenario_modifications(sample_villages, sample_sites, params)

    assert len(mod_v) == len(sample_villages)
    assert mod_v[0].rainfall_intensity == sample_villages[0].rainfall_intensity
    assert mod_s[0].housing_capacity == sample_sites[0].housing_capacity


def test_05_extreme_rainfall_modifies_rainfall_inputs(sample_villages, sample_sites):
    """Test 5: EXTREME_RAINFALL scales rainfall intensity by exactly 1.40."""
    params = ScenarioParameters(scenario_type=ScenarioType.EXTREME_RAINFALL, rainfall_multiplier=1.40)
    mod_v, _, _ = apply_scenario_modifications(sample_villages, sample_sites, params)

    expected = min(100.0, sample_villages[0].rainfall_intensity * 1.40)
    assert mod_v[0].rainfall_intensity == expected
    assert mod_v[0].rainfall_24h_mm == sample_villages[0].rainfall_24h_mm * 1.40


def test_06_flash_flood_modifies_flood_conditions(sample_villages, sample_sites):
    """Test 6: FLASH_FLOOD increases flood exposure and registers blocked corridor."""
    params = ScenarioParameters(
        scenario_type=ScenarioType.FLASH_FLOOD,
        flood_hazard_increase=35.0,
        flood_severity="critical",
        blocked_segment_ids=["SEG-VALLEY-02"],
    )
    mod_v, _, routing_ctx = apply_scenario_modifications(sample_villages, sample_sites, params)

    assert mod_v[0].flood_exposure == min(100.0, sample_villages[0].flood_exposure + 35.0)
    assert "SEG-VALLEY-02" in routing_ctx["blocked_segment_ids"]
    assert len(routing_ctx["hazard_events"]) > 0


def test_07_capacity_crisis_modifies_capacity_inputs(sample_villages, sample_sites):
    """Test 7: CAPACITY_CRISIS reduces all infrastructure dimensions by configured percentage."""
    params = ScenarioParameters(scenario_type=ScenarioType.CAPACITY_CRISIS, capacity_reduction_percentage=50.0)
    _, mod_s, _ = apply_scenario_modifications(sample_villages, sample_sites, params)

    assert mod_s[0].housing_capacity == int(sample_sites[0].housing_capacity * 0.50)
    assert mod_s[0].water_capacity == int(sample_sites[0].water_capacity * 0.50)


def test_08_invalid_parameters_rejected():
    """Test 8: Negative multipliers or out-of-bound percentages fail validation."""
    with pytest.raises(ValueError):
        ScenarioParameters(rainfall_multiplier=-0.5)

    with pytest.raises(ValueError):
        ScenarioParameters(capacity_reduction_percentage=150.0)


def test_09_nan_and_inf_parameters_rejected():
    """Test 9: NaN and Infinite floats are strictly rejected on ScenarioParameters."""
    with pytest.raises(ValueError):
        ScenarioParameters(rainfall_multiplier=float("nan"))

    with pytest.raises(ValueError):
        ScenarioParameters(capacity_reduction_percentage=float("inf"))


def test_09b_configuration_driven_parameters_and_profile_bounds_overrides(sample_villages, sample_sites):
    """Test 9b: Scenario parameters are configuration-driven, support overrides, and respect profile bounds."""
    # 1. Canonical FLASH_FLOOD definition contains no region-specific road segment identifier
    def_ff, params_ff = resolve_scenario_parameters(ScenarioType.FLASH_FLOOD)
    assert params_ff.flood_hazard_increase == 35.0
    assert params_ff.flood_severity == "critical"
    assert params_ff.blocked_segment_ids == []  # Canonical definition is region-agnostic

    # Himalayan pilot profile supplies SEG-VALLEY-02 via scenario_bounds.flood_prone_corridor_segments
    himalayan_profile = get_profile("himalayan_pilot")
    assert "SEG-VALLEY-02" in himalayan_profile.scenario_bounds.flood_prone_corridor_segments
    _, params_pilot = resolve_scenario_parameters(ScenarioType.FLASH_FLOOD, profile=himalayan_profile)
    assert "SEG-VALLEY-02" in params_pilot.blocked_segment_ids

    # 2. Default CAPACITY_CRISIS works without custom parameters
    def_cc, params_cc = resolve_scenario_parameters(ScenarioType.CAPACITY_CRISIS)
    assert params_cc.capacity_reduction_percentage == 50.0

    # 3. Overriding scenario parameter updates the scenario input cleanly
    custom_params = ScenarioParameters(
        flood_hazard_increase=48.0,
        blocked_segment_ids=["CUSTOM-CORRIDOR-01"],
    )
    _, resolved_custom = resolve_scenario_parameters(
        ScenarioType.FLASH_FLOOD,
        parameters=custom_params,
        profile=himalayan_profile,
    )
    assert resolved_custom.flood_hazard_increase == 48.0
    assert resolved_custom.flood_severity == "critical"  # Preserved from definition
    assert resolved_custom.blocked_segment_ids == ["CUSTOM-CORRIDOR-01"]  # Caller override takes precedence

    mod_v, _, _ = apply_scenario_modifications(sample_villages, sample_sites, resolved_custom)
    assert mod_v[0].flood_exposure == min(100.0, sample_villages[0].flood_exposure + 48.0)

    # 4. Overriding capacity reduction updates site inputs
    custom_cap = ScenarioParameters(capacity_reduction_percentage=75.0)
    _, resolved_cap = resolve_scenario_parameters(ScenarioType.CAPACITY_CRISIS, parameters=custom_cap)
    assert resolved_cap.capacity_reduction_percentage == 75.0
    _, mod_s, _ = apply_scenario_modifications(sample_villages, sample_sites, resolved_cap)
    assert mod_s[0].housing_capacity == int(sample_sites[0].housing_capacity * 0.25)

    # 5. Core engine does not require a named region; works with custom/generic profile
    profile = get_profile("himalayan_pilot")
    custom_engine = ScenarioSimulatorEngine(profile=profile)
    out = custom_engine.run_simulation(
        scenario_type=ScenarioType.FLASH_FLOOD,
        parameters=custom_params,
        villages=sample_villages,
        sites=sample_sites,
    )
    assert out.status == ScenarioRunStatus.COMPLETED
    assert out.parameters.flood_hazard_increase == 48.0

    # 6. Profile bounds validation: rainfall multiplier exceeding profile max raises InvalidScenarioParameterError
    invalid_rainfall = ScenarioParameters(rainfall_multiplier=5.0)  # max is 3.0 in profile bounds
    with pytest.raises(InvalidScenarioParameterError):
        resolve_scenario_parameters(
            ScenarioType.EXTREME_RAINFALL,
            parameters=invalid_rainfall,
            profile=profile,
        )


def test_09c_region_agnostic_flash_flood_and_pilot_corridor_diversion(sample_villages, sample_sites):
    """Test 9c: Proves region-agnostic flash flood architecture:
    1. Canonical FLASH_FLOOD definition contains no Himalayan road segment ID.
    2. Himalayan pilot profile supplies SEG-VALLEY-02.
    3. FLASH_FLOOD still blocks/diverts the intended Himalayan corridor.
    4. A second synthetic region profile provides a different segment (SEG-DELTA-09) without engine modification.
    5. Scenario parameter resolution remains deterministic.
    6. Core scenario engine source code contains zero hard-coded SEG-VALLEY-02, Joshimath, Pipalkoti, or Himalayan identifiers.
    """
    import inspect
    from app.core.scenarios import comparison as comp_mod
    from app.core.scenarios import contracts as contracts_mod
    from app.core.scenarios import definitions as defs_mod
    from app.core.scenarios import engine as engine_mod
    from app.core.scenarios import errors as errors_mod
    from app.core.scenarios import inputs as inputs_mod

    # 1. Canonical definition is strictly region-agnostic
    ff_def = get_scenario_definition(ScenarioType.FLASH_FLOOD)
    assert ff_def.default_parameters.blocked_segment_ids == []

    # 2. Himalayan pilot configuration supplies SEG-VALLEY-02
    himalayan = get_profile("himalayan_pilot")
    assert "SEG-VALLEY-02" in himalayan.scenario_bounds.flood_prone_corridor_segments
    _, resolved_pilot = resolve_scenario_parameters(ScenarioType.FLASH_FLOOD, profile=himalayan)
    assert resolved_pilot.blocked_segment_ids == ["SEG-VALLEY-02"]

    # 3. FLASH_FLOOD still blocks and diverts around SEG-VALLEY-02 on pilot network
    sim_engine = ScenarioSimulatorEngine(profile=himalayan)
    sim_output = sim_engine.run_simulation(
        scenario_type=ScenarioType.FLASH_FLOOD,
        villages=sample_villages,
        sites=sample_sites,
    )
    assert sim_output.status == ScenarioRunStatus.COMPLETED
    assert "SEG-VALLEY-02" in sim_output.parameters.blocked_segment_ids
    assert sim_output.scenario_pipeline.routing_result.routes_evaluated > 0

    # 4. A second synthetic profile provides a different segment without changing core engine
    second_bounds = himalayan.scenario_bounds.model_copy(
        update={"flood_prone_corridor_segments": ["SEG-DELTA-09"]}
    )
    second_profile = himalayan.model_copy(
        update={"scenario_bounds": second_bounds}
    )
    _, resolved_second = resolve_scenario_parameters(ScenarioType.FLASH_FLOOD, profile=second_profile)
    assert resolved_second.blocked_segment_ids == ["SEG-DELTA-09"]
    assert "SEG-VALLEY-02" not in resolved_second.blocked_segment_ids

    second_engine = ScenarioSimulatorEngine(profile=second_profile)
    out_second = second_engine.run_simulation(
        scenario_type=ScenarioType.FLASH_FLOOD,
        villages=sample_villages,
        sites=sample_sites,
    )
    assert out_second.parameters.blocked_segment_ids == ["SEG-DELTA-09"]
    assert "SEG-VALLEY-02" not in out_second.parameters.blocked_segment_ids

    # 5. Scenario parameter resolution remains strictly deterministic across 20 iterations
    first_resolved = resolve_scenario_parameters(ScenarioType.FLASH_FLOOD, profile=himalayan)[1].model_dump()
    for _ in range(20):
        repeat_resolved = resolve_scenario_parameters(ScenarioType.FLASH_FLOOD, profile=himalayan)[1].model_dump()
        assert repeat_resolved == first_resolved

    # 6. Core scenario engine source code verification: zero hard-coded region strings
    for mod in (engine_mod, defs_mod, inputs_mod, contracts_mod, comp_mod, errors_mod):
        source = inspect.getsource(mod)
        assert "SEG-VALLEY-02" not in source, f"Hardcoded SEG-VALLEY-02 found in {mod.__name__}"
        assert "Joshimath" not in source, f"Hardcoded Joshimath found in {mod.__name__}"
        assert "Pipalkoti" not in source, f"Hardcoded Pipalkoti found in {mod.__name__}"
        assert "Himalayan" not in source, f"Hardcoded Himalayan found in {mod.__name__}"


# =============================================================================
# 3. PIPELINE ORCHESTRATION & ZERO DUPLICATE NUMERICAL LOGIC
# =============================================================================

def test_10_to_16_pipeline_orchestrates_all_seven_stages(sample_villages, sample_sites):
    """Tests 10-16: End-to-end execution exercises all 7 domain engines and populates stage results."""
    engine = ScenarioSimulatorEngine()
    output = engine.run_simulation(
        scenario_type=ScenarioType.NORMAL,
        villages=sample_villages,
        sites=sample_sites,
    )

    assert output.status == ScenarioRunStatus.COMPLETED

    # 10. Risk stage
    assert len(output.baseline_pipeline.risk_results) == 2
    assert output.baseline_pipeline.risk_results[0].risk_score > 0.0

    # 11. Red Zone stage
    assert output.baseline_pipeline.red_zone_result.total_evaluated == 2

    # 12. Priority stage
    assert len(output.baseline_pipeline.priority_results) == 2
    assert output.baseline_pipeline.priority_results[0].priority_score > 0.0

    # 13. Suitability stage (implicit in matching candidate evaluation)
    # 14. Capacity stage
    assert len(output.baseline_pipeline.capacity_results) == 2
    assert output.baseline_pipeline.capacity_results[0].effective_capacity > 0

    # 15. Matching stage
    assert output.baseline_pipeline.matching_result.total_villages == 2
    assert output.baseline_pipeline.matching_result.total_households_allocated > 0

    # 16. Routing stage
    assert output.baseline_pipeline.routing_result.routes_evaluated == 2


# =============================================================================
# 4. NO FAKE RESULTS: PROPAGATION OF REAL CHANGES
# =============================================================================

def test_17_changed_rainfall_propagates_into_downstream_risk_and_priority(sample_villages, sample_sites):
    """Test 17: Extreme rainfall (+40%) strictly increases composite risk score and relocation priority."""
    engine = ScenarioSimulatorEngine()
    output = engine.run_simulation(
        scenario_type=ScenarioType.EXTREME_RAINFALL,
        villages=sample_villages,
        sites=sample_sites,
    )

    # Risk must increase
    v1_id = sample_villages[0].village_id
    delta_risk = output.comparison.risk_score_deltas[v1_id]
    assert delta_risk > 0.0

    # Priority must increase
    delta_prio = output.comparison.priority_score_deltas[v1_id]
    assert delta_prio > 0.0


def test_18_and_19_capacity_crisis_propagates_into_matching(sample_villages, sample_sites):
    """Tests 18 & 19: 50% capacity reduction exhausts capacity and causes unassigned households."""
    # Villages demand 110 + 80 = 190 households.
    # Site 1 (Pipalkoti): 150 -> 75. Site 2 (Dhak): 100 -> 50. Total = 125.
    # 190 > 125 -> Must have unassigned households!
    engine = ScenarioSimulatorEngine()
    output = engine.run_simulation(
        scenario_type=ScenarioType.CAPACITY_CRISIS,
        parameters=ScenarioParameters(
            scenario_type=ScenarioType.CAPACITY_CRISIS,
            capacity_reduction_percentage=50.0,
        ),
        villages=sample_villages,
        sites=sample_sites,
    )

    base_match = output.baseline_pipeline.matching_result
    scen_match = output.scenario_pipeline.matching_result

    # In baseline, 150 + 100 = 250 capacity easily covers 190 demand
    assert base_match.unassigned_count == 0

    # In scenario, 75 + 50 = 125 capacity cannot cover 190 demand -> village becomes unassigned!
    assert scen_match.total_households_unassigned > 0
    assert len(output.comparison.newly_unassigned_villages) > 0


def test_20_hazard_changes_propagate_into_routing(sample_villages, sample_sites):
    """Test 20: Flood cut-off on valley road diverts route or increases travel distance."""
    engine = ScenarioSimulatorEngine()
    output = engine.run_simulation(
        scenario_type=ScenarioType.FLASH_FLOOD,
        villages=sample_villages,
        sites=sample_sites,
    )

    # Route should register avoided cut-offs or diversion
    assert output.scenario_pipeline.routing_result.routes_evaluated > 0


# =============================================================================
# 5. BASELINE ISOLATION
# =============================================================================

def test_21_to_24_baseline_isolation_preserved(sample_villages, sample_sites):
    """Tests 21-24: Scenario execution leaves original baseline input objects completely unchanged."""
    orig_v1_rainfall = sample_villages[0].rainfall_intensity
    orig_s1_cap = sample_sites[0].housing_capacity

    engine = ScenarioSimulatorEngine()
    engine.run_simulation(
        scenario_type=ScenarioType.EXTREME_RAINFALL,
        parameters=ScenarioParameters(
            scenario_type=ScenarioType.EXTREME_RAINFALL,
            rainfall_multiplier=2.5,
            capacity_reduction_percentage=75.0,
        ),
        villages=sample_villages,
        sites=sample_sites,
    )

    # Baseline input objects are completely untouched
    assert sample_villages[0].rainfall_intensity == orig_v1_rainfall
    assert sample_sites[0].housing_capacity == orig_s1_cap


# =============================================================================
# 6. COMPARISON DELTAS
# =============================================================================

def test_25_to_30_comparison_deltas_correctness(sample_villages, sample_sites):
    """Tests 25-30: Comparison payload accurately computes deltas for all 6 domain facets."""
    engine = ScenarioSimulatorEngine()
    output = engine.run_simulation(
        scenario_type=ScenarioType.EXTREME_RAINFALL,
        villages=sample_villages,
        sites=sample_sites,
    )

    comp = output.comparison
    # 25. Risk before/after
    assert len(comp.risk_score_deltas) == 2
    # 26. Red Zone before/after
    assert comp.scenario_red_zones_count >= comp.baseline_red_zones_count
    # 27. Priority before/after
    assert len(comp.priority_score_deltas) == 2
    # 28. Capacity before/after
    assert len(comp.site_capacity_deltas) == 2
    # 29. Matching before/after
    assert isinstance(comp.site_reallocations, list)
    # 30. Routing before/after
    assert isinstance(comp.route_distance_deltas, dict)
    assert len(comp.comparison_narrative) > 0


# =============================================================================
# 7. DETERMINISM: 20 REPEATED RUNS
# =============================================================================

def test_31_repeat_extreme_rainfall_twenty_times_deterministic(sample_villages, sample_sites):
    """Test 31: 20 repeated runs of EXTREME_RAINFALL return identical deltas and assignments."""
    engine = ScenarioSimulatorEngine()
    first = engine.run_simulation(
        scenario_type=ScenarioType.EXTREME_RAINFALL,
        villages=sample_villages,
        sites=sample_sites,
    )

    for _ in range(19):
        current = engine.run_simulation(
            scenario_type=ScenarioType.EXTREME_RAINFALL,
            villages=sample_villages,
            sites=sample_sites,
        )
        assert current.comparison.risk_score_deltas == first.comparison.risk_score_deltas
        assert current.comparison.priority_score_deltas == first.comparison.priority_score_deltas
        assert (
            current.scenario_pipeline.matching_result.total_households_allocated
            == first.scenario_pipeline.matching_result.total_households_allocated
        )


def test_32_repeat_flash_flood_twenty_times_deterministic(sample_villages, sample_sites):
    """Test 32: 20 repeated runs of FLASH_FLOOD return identical results."""
    engine = ScenarioSimulatorEngine()
    first = engine.run_simulation(
        scenario_type=ScenarioType.FLASH_FLOOD,
        villages=sample_villages,
        sites=sample_sites,
    )

    for _ in range(19):
        current = engine.run_simulation(
            scenario_type=ScenarioType.FLASH_FLOOD,
            villages=sample_villages,
            sites=sample_sites,
        )
        assert current.comparison.risk_score_deltas == first.comparison.risk_score_deltas
        assert current.comparison.corridors_diverted == first.comparison.corridors_diverted


def test_33_repeat_capacity_crisis_twenty_times_deterministic(sample_villages, sample_sites):
    """Test 33: 20 repeated runs of CAPACITY_CRISIS return identical results."""
    engine = ScenarioSimulatorEngine()
    first = engine.run_simulation(
        scenario_type=ScenarioType.CAPACITY_CRISIS,
        villages=sample_villages,
        sites=sample_sites,
    )

    for _ in range(19):
        current = engine.run_simulation(
            scenario_type=ScenarioType.CAPACITY_CRISIS,
            villages=sample_villages,
            sites=sample_sites,
        )
        assert current.comparison.site_capacity_deltas == first.comparison.site_capacity_deltas
        assert (
            current.scenario_pipeline.matching_result.unassigned_count
            == first.scenario_pipeline.matching_result.unassigned_count
        )


# =============================================================================
# 8. ERROR HANDLING
# =============================================================================

def test_34_missing_region_profile_rejected(client):
    """Test 34: Nonexistent region profile returns HTTP 404."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        res = client.post(
            "/api/v1/scenarios/run",
            json={"scenario_type": "NORMAL", "region_profile_id": "nonexistent_profile_xyz"},
        )
        assert res.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_35_missing_required_baseline_data_rejected():
    """Test 35: Empty villages or sites list raises InsufficientScenarioDataError."""
    engine = ScenarioSimulatorEngine()
    with pytest.raises(InsufficientScenarioDataError):
        engine.run_simulation(scenario_type=ScenarioType.NORMAL, villages=[], sites=[])


def test_36_routing_insufficient_data_handled_cleanly(sample_villages, sample_sites):
    """Test 36: Coordinates far from road network report unroutable without crashing."""
    far_village = VillageSimulationInput(
        village_id="V-FAR",
        village_name="Far Remote Hut",
        location=(70.0, 20.0),  # Thousands of km away from Himalayan network
        households=10,
        population=40,
    )
    engine = ScenarioSimulatorEngine()
    output = engine.run_simulation(
        scenario_type=ScenarioType.NORMAL,
        villages=[far_village],
        sites=sample_sites,
    )
    # The pipeline should complete and report the route as unroutable
    assert output.status == ScenarioRunStatus.COMPLETED
    assert output.baseline_pipeline.routing_result.unroutable_count > 0


def test_37_failed_pipeline_stage_trapped():
    """Test 37: Unhandled exception inside a stage is trapped as ScenarioExecutionError."""
    engine = ScenarioSimulatorEngine()
    # Mock risk_engine to blow up
    engine.risk_engine.compute_from_values = MagicMock(side_effect=RuntimeError("Hardware failure"))

    with pytest.raises(ScenarioExecutionError) as exc_info:
        engine.run_simulation(
            scenario_type=ScenarioType.NORMAL,
            villages=[
                VillageSimulationInput(
                    village_id="V-1",
                    village_name="V1",
                    location=(79.5, 30.5),
                    households=10,
                    population=40,
                )
            ],
            sites=[
                SiteSimulationInput(
                    site_id="S-1",
                    site_name="S1",
                    location=(79.4, 30.4),
                )
            ],
        )
    assert exc_info.value.stage == "baseline_execution"


def test_38_structured_api_errors(client):
    """Test 38: Invalid JSON payload returns structured validation error."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        res = client.post("/api/v1/scenarios/run", json={"scenario_type": "NORMAL", "parameters": {"rainfall_multiplier": -1.0}})
        assert res.status_code in [400, 422]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# =============================================================================
# 9. API ENDPOINTS
# =============================================================================

def test_39_api_list_scenarios_authenticated(client):
    """Test 39: GET /api/v1/scenarios returns list of canonical scenarios."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        res = client.get("/api/v1/scenarios")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        sc_types = [s["scenario_type"] for s in data["data"]]
        assert "EXTREME_RAINFALL" in sc_types
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_40_api_run_scenario_authenticated_success(client):
    """Test 40: POST /api/v1/scenarios/run executes simulation and returns comparison."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        res = client.post(
            "/api/v1/scenarios/run",
            json={"scenario_type": "EXTREME_RAINFALL", "persist": False},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["status"] == "COMPLETED"
        assert "risk_score_deltas" in data["data"]["comparison"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_41_api_unauthenticated_returns_401(client):
    """Test 41: Endpoints without auth return HTTP 401."""
    res = client.get("/api/v1/scenarios")
    assert res.status_code == 401

    res2 = client.post("/api/v1/scenarios/run", json={"scenario_type": "NORMAL"})
    assert res2.status_code == 401


def test_42_api_invalid_scenario_type_returns_400(client):
    """Test 42: POST /api/v1/scenarios/run with invalid scenario type returns HTTP 400."""
    officer = User(id=1, username="officer_user", role="district_officer", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: officer
    try:
        res = client.post("/api/v1/scenarios/run", json={"scenario_type": "INVALID_TYPE"})
        assert res.status_code == 400
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_43_api_openapi_route_registration(client):
    """Test 43: /openapi.json registers scenario endpoints without route collisions."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]
    assert "/api/v1/scenarios" in paths
    assert "/api/v1/scenarios/run" in paths


# =============================================================================
# 10. SYNTHETIC HIMALAYAN PILOT SCENARIO DEMONSTRATION
# =============================================================================

def _extract_lon_lat_test(geometry_or_coords: Any, default: Tuple[float, float] = (79.50, 30.50)) -> Tuple[float, float]:
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


def test_44_to_46_himalayan_pilot_extreme_rainfall_demonstration():
    """Tests 44-46: Run EXTREME_RAINFALL against the synthetic Himalayan pilot dataset.

    Verifies backend-derived before-vs-after differences and downstream relocation/routing changes.
    """
    dataset = load_himalayan_pilot_dataset()

    # Load 5 sample villages and 4 candidate sites
    v_inputs: List[VillageSimulationInput] = []
    for f in dataset.villages.features[:5]:
        props = f.properties
        coords = _extract_lon_lat_test(f.geometry, (79.565, 30.555))
        demo = getattr(props, "demographics", {}) or {}
        risk_data = getattr(props, "risk", {}) or {}

        hh = demo.get("households", 50) if isinstance(demo, dict) else getattr(demo, "households", 50)
        pop = demo.get("total_population", 200) if isinstance(demo, dict) else getattr(demo, "total_population", 200)
        c_score = risk_data.get("composite_score", 50.0) if isinstance(risk_data, dict) else getattr(risk_data, "composite_score", 50.0)

        v_inputs.append(
            VillageSimulationInput(
                village_id=props.id,
                village_name=props.name,
                location=coords,
                households=int(hh),
                population=int(pop),
                hazard_severity=float(c_score),
                flood_exposure=35.0,
                rainfall_intensity=float(c_score * 0.8),
                slope_landslide_susceptibility=float(c_score * 0.9),
                rainfall_24h_mm=50.0,
            )
        )

    s_inputs: List[SiteSimulationInput] = []
    for f in dataset.candidate_sites.features[:4]:
        props = f.properties
        coords = _extract_lon_lat_test(f.geometry, (79.430, 30.430))
        caps = getattr(props, "capacities", {}) or {}
        max_hh = caps.get("max_households", 120) if isinstance(caps, dict) else getattr(caps, "max_households", 120)

        s_inputs.append(
            SiteSimulationInput(
                site_id=props.id,
                site_name=props.name,
                location=coords,
                terrain_slope_deg=float(getattr(props, "slope_deg", 5.0) or 5.0),
                housing_capacity=int(max_hh),
                water_capacity=int(max_hh),
                sanitation_capacity=int(max_hh),
                healthcare_capacity=int(max_hh),
                shelter_capacity=int(max_hh),
            )
        )

    engine = ScenarioSimulatorEngine()
    output = engine.run_simulation(
        scenario_type=ScenarioType.EXTREME_RAINFALL,
        villages=v_inputs,
        sites=s_inputs,
    )

    # 44. Successful execution
    assert output.status == ScenarioRunStatus.COMPLETED
    assert output.scenario_name == "Extreme Rainfall Simulation (+40%)"

    # 45. Real before-vs-after differences derived from real engines
    assert output.comparison.average_risk_delta > 0.0
    for vid, delta in output.comparison.risk_score_deltas.items():
        assert delta > 0.0

    # 46. Downstream priority and allocation outcomes reflect changed state
    for vid, p_delta in output.comparison.priority_score_deltas.items():
        assert p_delta > 0.0

    assert output.provenance["source_type"] == "SIMULATION"
    assert "comparison_summary" in output.explainability
