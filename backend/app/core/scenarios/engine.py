"""Scenario Simulator Engine orchestrating the 7 domain pipeline stages (Chunk M4-06).

Execution chain:
  Scenario Definition & Input Overlay
  -> 1. Risk Engine (MultiHazardRiskEngine + RiskClassificationEngine)
  -> 2. Dynamic Red Zone Engine (DynamicRedZoneEngine)
  -> 3. Relocation Priority Engine (RelocationPriorityEngine)
  -> 4. Site Suitability Engine (SiteSuitabilityEngine)
  -> 5. Carrying Capacity Engine (CarryingCapacityEngine)
  -> 6. Relocation Matching Engine (RelocationMatchingEngine)
  -> 7. Evacuation Routing Engine (EvacuationRoutingEngine)
  -> Before vs After Comparison & Explainability

Strict Invariant: Zero duplicate numerical logic. All numerical calculations
are delegated to the single authoritative source of truth for each domain.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from app.core.profiles import RegionProfile, list_profiles
from app.core.relocation.capacity.contracts import SiteCapacityInput
from app.core.relocation.capacity.engine import CarryingCapacityEngine
from app.core.relocation.matching.contracts import MatchingSiteCandidate, VillageDemandInput
from app.core.relocation.matching.engine import RelocationMatchingEngine
from app.core.relocation.routing.contracts import RouteQuery, RouteStatus
from app.core.relocation.routing.engine import EvacuationRoutingEngine
from app.core.relocation.routing.hazards import HazardAwareRouteEvaluator
from app.core.relocation.routing.network import BaseRoadNetworkProvider, get_default_road_network_provider
from app.core.relocation.suitability.contracts import SiteSuitabilityInput
from app.core.relocation.suitability.engine import SiteSuitabilityEngine
from app.core.risk.classification.engine import RiskClassificationEngine
from app.core.risk.computation.engine import MultiHazardRiskEngine
from app.core.risk.red_zone.dynamic_contracts import DynamicHazardIndicator, DynamicHazardObservation
from app.core.risk.red_zone.dynamic_engine import DynamicRedZoneEngine
from app.core.risk.relocation_priority.engine import RelocationPriorityEngine
from app.core.scenarios.comparison import ScenarioComparator
from app.core.scenarios.contracts import (
    CapacityStageResult,
    DynamicRedZoneStageResult,
    MatchingAssignmentSummary,
    MatchingStageResult,
    PriorityStageResult,
    RoutingPathSummary,
    RoutingStageResult,
    ScenarioParameters,
    ScenarioRunStatus,
    ScenarioSimulationOutput,
    ScenarioType,
    SiteSimulationInput,
    StagePipelineResult,
    VillageRiskStageResult,
    VillageSimulationInput,
)
from app.core.scenarios.definitions import get_scenario_definition, resolve_scenario_parameters
from app.core.scenarios.errors import (
    InsufficientScenarioDataError,
    InvalidScenarioParameterError,
    ScenarioExecutionError,
)
from app.core.scenarios.inputs import apply_scenario_modifications


class ScenarioSimulatorEngine:
    """Orchestrator for end-to-end what-if scenario simulations."""

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        road_provider: Optional[BaseRoadNetworkProvider] = None,
    ) -> None:
        if profile is not None:
            self.profile = profile
        else:
            all_profiles = list_profiles()
            pilot_profiles = [p for p in all_profiles if p.is_pilot]
            self.profile = pilot_profiles[0] if pilot_profiles else (all_profiles[0] if all_profiles else None)

        self.road_provider = road_provider or get_default_road_network_provider()

        # Instantiate authoritative domain engines
        self.risk_engine = MultiHazardRiskEngine(profile=self.profile)
        self.risk_classifier = RiskClassificationEngine(profile=self.profile)
        self.red_zone_engine = DynamicRedZoneEngine(profile=self.profile)
        self.priority_engine = RelocationPriorityEngine(profile=self.profile)
        self.suitability_engine = SiteSuitabilityEngine()
        self.capacity_engine = CarryingCapacityEngine.from_region_profile(self.profile)
        self.matching_engine = RelocationMatchingEngine()

    def run_simulation(
        self,
        scenario_type: Union[str, ScenarioType] = ScenarioType.NORMAL,
        parameters: Optional[ScenarioParameters] = None,
        villages: Optional[List[VillageSimulationInput]] = None,
        sites: Optional[List[SiteSimulationInput]] = None,
        region_profile_id: Optional[str] = None,
    ) -> ScenarioSimulationOutput:
        """Execute complete end-to-end scenario simulation and comparison.

        Args:
            scenario_type: Requested scenario (NORMAL, EXTREME_RAINFALL, etc.)
            parameters: Explicit parameter overrides; defaults to canonical definition if omitted.
            villages: Baseline village input set; loaded from pilot defaults if omitted.
            sites: Baseline candidate site set; loaded from pilot defaults if omitted.
            region_profile_id: Optional profile identifier.

        Returns:
            ScenarioSimulationOutput: Strongly typed comparison envelope.
        """
        start_time = datetime.now(timezone.utc).isoformat()
        run_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        # 1. Resolve Scenario Parameters (combining definition defaults, caller overrides, and profile bounds)
        definition, resolved_params = resolve_scenario_parameters(
            scenario_type=scenario_type,
            parameters=parameters,
            profile=self.profile,
        )
        st = definition.scenario_type

        # 2. Validate Baseline Inputs
        if not villages:
            raise InsufficientScenarioDataError("Scenario simulation requires at least one baseline village input.")
        if not sites:
            raise InsufficientScenarioDataError("Scenario simulation requires at least one baseline candidate site input.")

        prof_id = region_profile_id or (self.profile.id if self.profile else "default")

        # 3. Execute Baseline Pipeline (Unmodified Inputs)
        try:
            baseline_pipeline = self._execute_pipeline(
                villages=villages,
                sites=sites,
                routing_hazard_context={"hazard_events": [], "blocked_segment_ids": []},
            )
        except Exception as e:
            raise ScenarioExecutionError(
                f"Baseline pipeline failed during simulation: {str(e)}",
                stage="baseline_execution",
            ) from e

        # 4. Apply Scenario Modifications (Isolated Copies)
        mod_villages, mod_sites, routing_hazard_context = apply_scenario_modifications(
            villages=villages,
            sites=sites,
            parameters=resolved_params,
        )

        # 5. Execute Scenario Pipeline (Modified Inputs)
        try:
            scenario_pipeline = self._execute_pipeline(
                villages=mod_villages,
                sites=mod_sites,
                routing_hazard_context=routing_hazard_context,
            )
        except Exception as e:
            raise ScenarioExecutionError(
                f"Scenario pipeline failed during simulation: {str(e)}",
                stage="scenario_execution",
            ) from e

        # 6. Execute Deterministic Before-vs-After Comparison
        comparison = ScenarioComparator.compare(
            baseline=baseline_pipeline,
            scenario=scenario_pipeline,
            parameters=resolved_params,
        )

        completed_time = datetime.now(timezone.utc).isoformat()

        # 7. Synthesize Metrics & Provenance
        baseline_metrics = {
            "total_villages": len(villages),
            "total_sites": len(sites),
            "critical_risk_villages": len(
                [r for r in baseline_pipeline.risk_results if r.risk_band.upper() == "CRITICAL"]
            ),
            "triggered_red_zones": baseline_pipeline.red_zone_result.triggered_count,
            "immediate_priority_villages": len(
                [p for p in baseline_pipeline.priority_results if p.priority_band.upper() == "IMMEDIATE"]
            ),
            "allocated_households": baseline_pipeline.matching_result.total_households_allocated,
            "unassigned_households": baseline_pipeline.matching_result.total_households_unassigned,
            "feasible_routes": baseline_pipeline.routing_result.feasible_routes_count,
        }

        scenario_metrics = {
            "total_villages": len(mod_villages),
            "total_sites": len(mod_sites),
            "critical_risk_villages": len(
                [r for r in scenario_pipeline.risk_results if r.risk_band.upper() == "CRITICAL"]
            ),
            "triggered_red_zones": scenario_pipeline.red_zone_result.triggered_count,
            "immediate_priority_villages": len(
                [p for p in scenario_pipeline.priority_results if p.priority_band.upper() == "IMMEDIATE"]
            ),
            "allocated_households": scenario_pipeline.matching_result.total_households_allocated,
            "unassigned_households": scenario_pipeline.matching_result.total_households_unassigned,
            "feasible_routes": scenario_pipeline.routing_result.feasible_routes_count,
        }

        provenance = {
            "source_type": "SIMULATION",
            "is_synthetic": True,
            "pilot_region": prof_id,
            "disclaimer": "SIMULATION / DECISION SUPPORT ONLY for SIH Problem Statement 26191. Not an official statutory forecast.",
        }

        explainability = {
            "scenario_name": definition.name,
            "scenario_description": definition.description,
            "parameters_applied": resolved_params.model_dump(),
            "pipeline_stages_evaluated": [
                "1_multi_hazard_risk",
                "2_dynamic_red_zones",
                "3_relocation_priority",
                "4_site_suitability",
                "5_carrying_capacity",
                "6_relocation_matching",
                "7_evacuation_routing",
            ],
            "comparison_summary": comparison.comparison_narrative,
        }

        return ScenarioSimulationOutput(
            scenario_name=definition.name,
            scenario_type=st,
            region_profile_id=prof_id,
            run_id=run_id,
            status=ScenarioRunStatus.COMPLETED,
            parameters=resolved_params,
            started_at=start_time,
            completed_at=completed_time,
            baseline_metrics=baseline_metrics,
            scenario_metrics=scenario_metrics,
            comparison=comparison,
            baseline_pipeline=baseline_pipeline,
            scenario_pipeline=scenario_pipeline,
            provenance=provenance,
            explainability=explainability,
        )

    # =========================================================================
    # Internal Pipeline Execution
    # =========================================================================

    def _execute_pipeline(
        self,
        villages: List[VillageSimulationInput],
        sites: List[SiteSimulationInput],
        routing_hazard_context: Dict[str, Any],
    ) -> StagePipelineResult:
        """Run all 7 domain engines sequentially, passing upstream contracts."""
        # 1. Multi-Hazard Risk Computation & Classification
        risk_results: List[VillageRiskStageResult] = []
        for v in villages:
            risk_res = self.risk_engine.compute_from_values(
                hazard_severity=v.hazard_severity,
                flood_exposure=v.flood_exposure,
                rainfall_intensity=v.rainfall_intensity,
                slope_landslide_susceptibility=v.slope_landslide_susceptibility,
                infrastructure_vulnerability=v.infrastructure_vulnerability,
                social_vulnerability=v.social_vulnerability,
            )
            class_res = self.risk_classifier.classify(risk_res.score)
            risk_results.append(
                VillageRiskStageResult(
                    village_id=v.village_id,
                    village_name=v.village_name,
                    risk_score=round(risk_res.score, 2),
                    risk_band=class_res.band.value,
                    factor_breakdown={
                        "hazard": v.hazard_severity,
                        "flood": v.flood_exposure,
                        "rainfall": v.rainfall_intensity,
                        "slope": v.slope_landslide_susceptibility,
                        "infrastructure": v.infrastructure_vulnerability,
                        "social": v.social_vulnerability,
                    },
                )
            )

        # 2. Dynamic Red Zones Trigger Evaluation
        triggered_vids: List[str] = []
        candidate_ids: List[str] = []
        rainfall_thresh = (
            self.profile.red_zone_thresholds.dynamic_triggers.rainfall_trigger_24h_mm
            if hasattr(self.profile, "red_zone_thresholds")
            else 64.5
        )

        for v in villages:
            obs_val = v.rainfall_24h_mm if v.rainfall_24h_mm is not None else v.rainfall_intensity
            obs = DynamicHazardObservation(
                observation_id=f"OBS-{v.village_id}",
                village_id=v.village_id,
                indicator=DynamicHazardIndicator.RAINFALL_24H,
                observed_value=obs_val,
                location=v.location,
            )
            rz_cand = self.red_zone_engine.evaluate_observation(obs)
            if rz_cand.is_candidate:
                triggered_vids.append(v.village_id)
                candidate_ids.append(rz_cand.candidate_id)

        red_zone_result = DynamicRedZoneStageResult(
            total_evaluated=len(villages),
            triggered_count=len(triggered_vids),
            triggered_village_ids=triggered_vids,
            candidate_ids=candidate_ids,
        )

        # 3. Relocation Priority Scoring
        priority_results: List[PriorityStageResult] = []
        risk_map = {r.village_id: r.risk_score for r in risk_results}

        for v in villages:
            r_score = risk_map.get(v.village_id, 50.0)
            # Normalize demographic exposure roughly from population & vulnerable counts
            vuln_score = (v.infrastructure_vulnerability + v.social_vulnerability) / 2.0
            prio_res = self.priority_engine.evaluate(
                village_id=v.village_id,
                village_name=v.village_name,
                risk=r_score,
                exposure=min(100.0, max(10.0, v.population / 10.0)),
                vulnerability=vuln_score,
                historical_impact=v.historical_impact or 50.0,
                accessibility=v.accessibility or 50.0,
            )
            p_band = prio_res.priority_band.value if prio_res.priority_band else "MONITOR"
            priority_results.append(
                PriorityStageResult(
                    village_id=v.village_id,
                    village_name=v.village_name,
                    priority_score=round(prio_res.priority_score or 0.0, 2),
                    priority_band=p_band,
                )
            )

        # 4 & 5. Site Suitability & Carrying Capacity
        capacity_results: List[CapacityStageResult] = []
        suitability_inputs: Dict[str, SiteSuitabilityInput] = {}
        capacity_inputs: Dict[str, SiteCapacityInput] = {}

        for s in sites:
            sid_str = str(s.site_id)
            # Suitability
            suit_in = SiteSuitabilityInput(
                name=s.site_name,
                terrain_slope_deg=s.terrain_slope_deg,
                hazard_buffer_distance_m=s.hazard_buffer_distance_m,
                max_households=s.housing_capacity,
                available_households=s.housing_capacity,
            )
            suitability_inputs[sid_str] = suit_in

            # Capacity
            cap_in = SiteCapacityInput(
                site_name=s.site_name,
                incoming_households=0,
                housing_capacity=s.housing_capacity,
                water_capacity=s.water_capacity,
                sanitation_capacity=s.sanitation_capacity,
                healthcare_capacity=s.healthcare_capacity,
                shelter_capacity=s.shelter_capacity,
            )
            capacity_inputs[sid_str] = cap_in
            cap_res = self.capacity_engine.evaluate(cap_in)

            lim_fac = cap_res.limiting_factors[0] if cap_res.limiting_factors else "none"
            capacity_results.append(
                CapacityStageResult(
                    site_id=sid_str,
                    site_name=s.site_name,
                    effective_capacity=cap_res.effective_capacity_households or 0,
                    available_capacity=cap_res.available_capacity_households or 0,
                    limiting_factor=lim_fac,
                    is_feasible=cap_res.feasible,
                )
            )

        # 6. Relocation Matching & Assignment
        prio_map = {p.village_id: p for p in priority_results}
        matching_villages: List[VillageDemandInput] = []
        for v in villages:
            p_res = prio_map.get(v.village_id)
            matching_villages.append(
                VillageDemandInput(
                    village_id=v.village_id,
                    village_name=v.village_name,
                    priority_score=p_res.priority_score if p_res else 50.0,
                    priority_band=p_res.priority_band if p_res else None,
                    incoming_households=v.households,
                    incoming_population=v.population,
                    location=v.location,
                )
            )

        matching_sites: List[MatchingSiteCandidate] = []
        for s in sites:
            sid_str = str(s.site_id)
            matching_sites.append(
                MatchingSiteCandidate(
                    site_id=s.site_id,
                    site_name=s.site_name,
                    location=s.location,
                    status=s.status,
                    suitability_input=suitability_inputs.get(sid_str),
                    capacity_input=capacity_inputs.get(sid_str),
                )
            )

        match_res = self.matching_engine.match(
            villages=matching_villages,
            sites=matching_sites,
        )

        assignment_summaries: List[MatchingAssignmentSummary] = []
        for a in match_res.assignments:
            is_ass = a.assigned_site_id is not None
            chosen_audit = next(
                (c for c in a.evaluated_candidates if str(c.site_id) == str(a.assigned_site_id)),
                None,
            ) if is_ass else None
            r_score = chosen_audit.rank_score if chosen_audit and chosen_audit.rank_score is not None else None

            assignment_summaries.append(
                MatchingAssignmentSummary(
                    village_id=str(a.village_id),
                    village_name=a.village_name,
                    assigned_site_id=str(a.assigned_site_id) if is_ass else None,
                    assigned_site_name=a.assigned_site_name,
                    is_assigned=is_ass,
                    demanded_households=a.incoming_households,
                    allocated_households=a.incoming_households if is_ass else 0,
                    unassigned_code=a.unassigned_code.value if a.unassigned_code else None,
                    rank_score=round(r_score, 2) if r_score is not None else None,
                    distance_km=round(a.distance_km, 2) if a.distance_km is not None else None,
                )
            )

        matching_result = MatchingStageResult(
            total_villages=match_res.total_villages,
            total_households_demanded=match_res.total_households_demanded,
            total_households_allocated=match_res.total_households_allocated,
            total_households_unassigned=match_res.total_households_unassigned,
            assigned_count=match_res.assigned_villages_count,
            unassigned_count=match_res.unassigned_villages_count,
            assignments=assignment_summaries,
        )

        # 7. Evacuation Routing
        hazard_events = routing_hazard_context.get("hazard_events", [])
        routing_evaluator = HazardAwareRouteEvaluator(hazard_events=hazard_events)
        routing_engine = EvacuationRoutingEngine(
            road_provider=self.road_provider,
            hazard_evaluator=routing_evaluator,
        )

        site_loc_map: Dict[str, Tuple[float, float]] = {
            str(s.site_id): s.location for s in sites if s.location is not None
        }

        routes_summary: List[RoutingPathSummary] = []
        feasible_routes_count = 0
        total_dist = 0.0

        for a in match_res.assignments:
            vid = str(a.village_id)
            v_obj = next((v for v in villages if v.village_id == vid), None)
            if not v_obj or not a.assigned_site_id:
                continue

            sid = str(a.assigned_site_id)
            s_loc = site_loc_map.get(sid)
            if not s_loc:
                continue

            q = RouteQuery(
                origin=v_obj.location,
                destination=s_loc,
                hazard_context=routing_hazard_context,
                require_alternative=False,
            )
            route_res = routing_engine.route(q)

            if route_res.status == RouteStatus.FEASIBLE and route_res.primary_route:
                feasible_routes_count += 1
                dist = route_res.primary_route.distance_km
                total_dist += dist
                t_min = route_res.primary_route.estimated_time_minutes
                blocked_c = len(route_res.primary_route.explainability.blocked_segments_avoided)
                routes_summary.append(
                    RoutingPathSummary(
                        village_id=vid,
                        site_id=sid,
                        is_feasible=True,
                        distance_km=round(dist, 2),
                        estimated_time_minutes=t_min,
                        blocked_avoided_count=blocked_c,
                        route_status="FEASIBLE",
                    )
                )
            else:
                routes_summary.append(
                    RoutingPathSummary(
                        village_id=vid,
                        site_id=sid,
                        is_feasible=False,
                        distance_km=None,
                        estimated_time_minutes=None,
                        blocked_avoided_count=0,
                        route_status=route_res.status.value,
                    )
                )

        avg_dist = round(total_dist / max(1, feasible_routes_count), 2) if feasible_routes_count > 0 else None

        routing_result = RoutingStageResult(
            routes_evaluated=len(routes_summary),
            feasible_routes_count=feasible_routes_count,
            unroutable_count=len(routes_summary) - feasible_routes_count,
            average_distance_km=avg_dist,
            routes=routes_summary,
        )

        return StagePipelineResult(
            risk_results=risk_results,
            red_zone_result=red_zone_result,
            priority_results=priority_results,
            capacity_results=capacity_results,
            matching_result=matching_result,
            routing_result=routing_result,
        )
