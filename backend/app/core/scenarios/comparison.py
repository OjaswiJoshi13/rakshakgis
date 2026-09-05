"""Deterministic before-vs-after scenario comparison engine (Chunk M4-06)."""

from typing import Any, Dict, List

from app.core.scenarios.contracts import (
    ScenarioComparison,
    ScenarioParameters,
    StagePipelineResult,
)


class ScenarioComparator:
    """Computes exact mathematical and categorical deltas between baseline and scenario runs."""

    @staticmethod
    def compare(
        baseline: StagePipelineResult,
        scenario: StagePipelineResult,
        parameters: ScenarioParameters,
    ) -> ScenarioComparison:
        # 1. Risk Comparison
        b_risk_map = {r.village_id: r for r in baseline.risk_results}
        s_risk_map = {r.village_id: r for r in scenario.risk_results}

        risk_score_deltas: Dict[str, float] = {}
        risk_band_shifts: List[Dict[str, Any]] = []
        villages_escalated_to_critical: List[str] = []

        total_risk_delta = 0.0
        for vid, s_risk in sorted(s_risk_map.items()):
            b_risk = b_risk_map.get(vid)
            if b_risk is not None:
                delta = round(s_risk.risk_score - b_risk.risk_score, 4)
                risk_score_deltas[vid] = delta
                total_risk_delta += delta

                if s_risk.risk_band != b_risk.risk_band:
                    risk_band_shifts.append(
                        {
                            "village_id": vid,
                            "village_name": s_risk.village_name,
                            "baseline_band": b_risk.risk_band,
                            "scenario_band": s_risk.risk_band,
                            "score_delta": delta,
                        }
                    )
                if s_risk.risk_band.upper() == "CRITICAL" and b_risk.risk_band.upper() != "CRITICAL":
                    villages_escalated_to_critical.append(vid)

        avg_risk_delta = round(total_risk_delta / max(1, len(risk_score_deltas)), 4) if risk_score_deltas else 0.0

        # 2. Red Zone Comparison
        b_rz_villages = set(baseline.red_zone_result.triggered_village_ids)
        s_rz_villages = set(scenario.red_zone_result.triggered_village_ids)
        new_red_zone_villages = sorted(list(s_rz_villages - b_rz_villages))

        # 3. Priority Comparison
        b_prio_map = {p.village_id: p for p in baseline.priority_results}
        s_prio_map = {p.village_id: p for p in scenario.priority_results}

        priority_score_deltas: Dict[str, float] = {}
        priority_band_shifts: List[Dict[str, Any]] = []
        villages_escalated_to_immediate: List[str] = []

        for vid, s_prio in sorted(s_prio_map.items()):
            b_prio = b_prio_map.get(vid)
            if b_prio is not None:
                p_delta = round(s_prio.priority_score - b_prio.priority_score, 4)
                priority_score_deltas[vid] = p_delta

                if s_prio.priority_band != b_prio.priority_band:
                    priority_band_shifts.append(
                        {
                            "village_id": vid,
                            "village_name": s_prio.village_name,
                            "baseline_band": b_prio.priority_band,
                            "scenario_band": s_prio.priority_band,
                            "priority_delta": p_delta,
                        }
                    )
                if s_prio.priority_band.upper() == "IMMEDIATE" and b_prio.priority_band.upper() != "IMMEDIATE":
                    villages_escalated_to_immediate.append(vid)

        # 4. Capacity Comparison
        b_cap_map = {c.site_id: c for c in baseline.capacity_results}
        s_cap_map = {c.site_id: c for c in scenario.capacity_results}

        site_capacity_deltas: Dict[str, int] = {}
        newly_infeasible_sites: List[str] = []

        for sid, s_cap in sorted(s_cap_map.items()):
            b_cap = b_cap_map.get(sid)
            if b_cap is not None:
                c_delta = s_cap.effective_capacity - b_cap.effective_capacity
                site_capacity_deltas[sid] = c_delta
                if b_cap.is_feasible and not s_cap.is_feasible:
                    newly_infeasible_sites.append(sid)

        # 5. Matching Comparison
        b_match_map = {a.village_id: a for a in baseline.matching_result.assignments}
        s_match_map = {a.village_id: a for a in scenario.matching_result.assignments}

        site_reallocations: List[Dict[str, Any]] = []
        newly_unassigned_villages: List[str] = []

        for vid, s_assign in sorted(s_match_map.items()):
            b_assign = b_match_map.get(vid)
            if b_assign is not None:
                if b_assign.is_assigned and not s_assign.is_assigned:
                    newly_unassigned_villages.append(vid)
                elif (
                    b_assign.is_assigned
                    and s_assign.is_assigned
                    and b_assign.assigned_site_id != s_assign.assigned_site_id
                ):
                    site_reallocations.append(
                        {
                            "village_id": vid,
                            "village_name": s_assign.village_name,
                            "baseline_site_id": b_assign.assigned_site_id,
                            "baseline_site_name": b_assign.assigned_site_name,
                            "scenario_site_id": s_assign.assigned_site_id,
                            "scenario_site_name": s_assign.assigned_site_name,
                        }
                    )

        # 6. Routing Comparison
        b_route_map = {r.village_id: r for r in baseline.routing_result.routes}
        s_route_map = {r.village_id: r for r in scenario.routing_result.routes}

        route_distance_deltas: Dict[str, float] = {}
        corridors_diverted: List[str] = []
        newly_severed_routes: List[str] = []

        for vid, s_r in sorted(s_route_map.items()):
            b_r = b_route_map.get(vid)
            if b_r is not None:
                if b_r.is_feasible and not s_r.is_feasible:
                    newly_severed_routes.append(vid)
                elif b_r.is_feasible and s_r.is_feasible:
                    if b_r.distance_km is not None and s_r.distance_km is not None:
                        dist_delta = round(s_r.distance_km - b_r.distance_km, 2)
                        route_distance_deltas[vid] = dist_delta
                        if dist_delta > 0.05 or s_r.blocked_avoided_count > b_r.blocked_avoided_count:
                            corridors_diverted.append(vid)

        # 7. Comparison Narrative Synthesis
        narrative_lines = [
            f"Scenario '{parameters.scenario_type.value}' evaluated against baseline across 7 pipeline stages:",
            f"  - Risk: Average risk delta of {avg_risk_delta:+.2f} points across {len(risk_score_deltas)} villages.",
        ]
        if risk_band_shifts:
            narrative_lines.append(
                f"  - Risk Band Shifts: {len(risk_band_shifts)} villages changed risk classification "
                f"({len(villages_escalated_to_critical)} escalated to CRITICAL)."
            )
        if new_red_zone_villages:
            narrative_lines.append(
                f"  - Dynamic Red Zones: {len(new_red_zone_villages)} new settlements triggered temporary red zones."
            )
        if priority_band_shifts:
            narrative_lines.append(
                f"  - Relocation Priority: {len(priority_band_shifts)} villages shifted priority bands "
                f"({len(villages_escalated_to_immediate)} reached IMMEDIATE action status)."
            )
        if site_capacity_deltas and any(d != 0 for d in site_capacity_deltas.values()):
            narrative_lines.append(
                f"  - Capacity: Effective capacity reduced across {len([d for d in site_capacity_deltas.values() if d < 0])} sites; "
                f"{len(newly_infeasible_sites)} sites became infeasible."
            )
        if newly_unassigned_villages or site_reallocations:
            narrative_lines.append(
                f"  - Matching Impact: {len(newly_unassigned_villages)} villages became UNASSIGNED due to capacity/hazard constraints; "
                f"{len(site_reallocations)} villages were diverted to alternative sites."
            )
        if corridors_diverted or newly_severed_routes:
            narrative_lines.append(
                f"  - Evacuation Routing: {len(corridors_diverted)} routes diverted due to hazard cut-offs; "
                f"{len(newly_severed_routes)} evacuation routes became physically severed."
            )

        return ScenarioComparison(
            risk_score_deltas=risk_score_deltas,
            average_risk_delta=avg_risk_delta,
            risk_band_shifts=risk_band_shifts,
            villages_escalated_to_critical=villages_escalated_to_critical,
            baseline_red_zones_count=len(b_rz_villages),
            scenario_red_zones_count=len(s_rz_villages),
            new_red_zone_villages=new_red_zone_villages,
            priority_score_deltas=priority_score_deltas,
            priority_band_shifts=priority_band_shifts,
            villages_escalated_to_immediate=villages_escalated_to_immediate,
            site_capacity_deltas=site_capacity_deltas,
            newly_infeasible_sites=newly_infeasible_sites,
            baseline_unassigned_count=baseline.matching_result.unassigned_count,
            scenario_unassigned_count=scenario.matching_result.unassigned_count,
            newly_unassigned_villages=newly_unassigned_villages,
            site_reallocations=site_reallocations,
            route_distance_deltas=route_distance_deltas,
            corridors_diverted=corridors_diverted,
            newly_severed_routes=newly_severed_routes,
            comparison_narrative="\n".join(narrative_lines),
        )
