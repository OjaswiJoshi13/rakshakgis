"""Deterministic Relocation Matching & Assignment Engine coordinator (Chunk M4-04)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.core.profiles.models import RegionProfile
from app.core.profiles.registry import get_profile
from app.core.relocation.capacity import CarryingCapacityEngine, SiteCapacityResult
from app.core.relocation.matching.contracts import (
    AssignmentStatus,
    CandidateEvaluationAudit,
    MatchingAlgorithmType,
    MatchingSiteCandidate,
    RejectionReasonCode,
    RelocationMatchingResult,
    VillageAssignmentResult,
    VillageDemandInput,
)
from app.core.relocation.matching.errors import (
    InvalidMatchingInputError,
    MatchingConfigurationError,
)
from app.core.relocation.matching.ranking import (
    calculate_haversine_distance_km,
    compute_matching_rank_score,
    sort_feasible_candidates,
)
from app.core.relocation.suitability import (
    SiteSuitabilityEngine,
    SiteSuitabilityResult,
    SuitabilityDecision,
)


class RelocationMatchingEngine:
    """Evaluates multi-village to multi-site relocation matching deterministically using greedy allocation."""

    def __init__(
        self,
        region_profile_id: str = "himalayan_pilot",
        profile: Optional[RegionProfile] = None,
    ) -> None:
        self.region_profile_id = region_profile_id
        if profile is not None:
            self.profile = profile
        else:
            self.profile = get_profile(region_profile_id)

        self.suitability_engine = SiteSuitabilityEngine.from_region_profile(self.profile)
        self.capacity_engine = CarryingCapacityEngine.from_region_profile(self.profile)

    @classmethod
    def from_region_profile(cls, profile: RegionProfile) -> "RelocationMatchingEngine":
        """Factory method to construct engine from a strongly typed RegionProfile."""
        return cls(region_profile_id=profile.id, profile=profile)

    def match(
        self,
        villages: List[VillageDemandInput],
        sites: List[MatchingSiteCandidate],
    ) -> RelocationMatchingResult:
        """Execute deterministic greedy matching of prioritized villages to candidate sites.

        Workflow:
          Step A: Sort villages descending by relocation priority score (stable tie-breaking on village_id).
          Step B: Determine and validate household relocation demand per village.
          Step C: Evaluate candidate sites using M4-02 suitability and M4-03 carrying capacity.
          Step D: Rank feasible candidate sites by composite suitability and proximity score.
          Step E: Greedily allocate the top-ranked site and decrement available capacity dynamically.
          Step F: If no site satisfies all constraints, designate village as UNASSIGNED with structured reasons.

        Returns:
          RelocationMatchingResult with full explainability audit.
        """
        # Validate input sets
        if not villages:
            return RelocationMatchingResult(
                matching_id=str(uuid.uuid4()),
                algorithm=MatchingAlgorithmType.GREEDY_PRIORITY,
                total_villages=0,
                assigned_villages_count=0,
                unassigned_villages_count=0,
                total_households_demanded=0,
                total_households_allocated=0,
                total_households_unassigned=0,
                assignments=[],
                site_remaining_capacities={},
                summary_narrative="No villages were provided for relocation matching.",
                execution_timestamp=datetime.now(timezone.utc),
                region_profile_id=self.region_profile_id,
            )

        # Step A: Order villages descending by priority score, stable tie-break by village_id
        def village_sort_key(v: VillageDemandInput):
            return (-round(v.priority_score, 4), str(v.village_id))

        sorted_villages = sorted(villages, key=village_sort_key)

        # Step C: Initialize candidate site suitability & capacity state
        site_suitabilities: Dict[Union[int, str], SiteSuitabilityResult] = {}
        site_unknown_capacity: Dict[Union[int, str], bool] = {}
        remaining_capacities: Dict[str, int] = {}

        for site in sites:
            s_id = site.site_id
            s_key = str(s_id)

            # 1. Evaluate suitability if not precomputed
            if site.precomputed_suitability:
                suit_res = site.precomputed_suitability
            elif site.suitability_input:
                suit_res = self.suitability_engine.evaluate(site.suitability_input)
            else:
                raise InvalidMatchingInputError(
                    f"Candidate site '{site.site_name}' ({s_id}) missing suitability input or precomputed result."
                )
            site_suitabilities[s_id] = suit_res

            # 2. Evaluate initial carrying capacity if not precomputed
            if site.initial_available_capacity is not None:
                site_unknown_capacity[s_id] = False
                remaining_capacities[s_key] = max(0, site.initial_available_capacity)
            elif site.precomputed_capacity:
                cap_res = site.precomputed_capacity
                is_unknown = bool(cap_res.unknown_dimensions or cap_res.effective_capacity_households is None)
                site_unknown_capacity[s_id] = is_unknown
                avail = cap_res.available_capacity_households if not is_unknown else 0
                remaining_capacities[s_key] = max(0, avail or 0)
            elif site.capacity_input:
                cap_res = self.capacity_engine.evaluate(site.capacity_input)
                is_unknown = bool(cap_res.unknown_dimensions or cap_res.effective_capacity_households is None)
                site_unknown_capacity[s_id] = is_unknown
                avail = cap_res.available_capacity_households if not is_unknown else 0
                remaining_capacities[s_key] = max(0, avail or 0)
            else:
                # Capacity completely unspecified -> treat as UNKNOWN (never unlimited)
                site_unknown_capacity[s_id] = True
                remaining_capacities[s_key] = 0

        # Sequential Allocation
        village_assignments: List[VillageAssignmentResult] = []
        total_demanded = sum(v.incoming_households for v in sorted_villages)
        total_allocated = 0
        total_unassigned = 0

        for village in sorted_villages:
            demand = village.incoming_households
            v_audits: List[CandidateEvaluationAudit] = []
            feasible_candidates: List[Dict[str, Any]] = []

            for site in sites:
                s_id = site.site_id
                s_key = str(s_id)
                suit_res = site_suitabilities[s_id]

                # Check 1: Explicit site rejection / inactivity
                if site.status in ("rejected", "inactive"):
                    v_audits.append(
                        CandidateEvaluationAudit(
                            site_id=s_id,
                            site_name=site.site_name,
                            is_feasible=False,
                            rejection_code=RejectionReasonCode.SITE_UNAVAILABLE,
                            rejection_reasons=[f"Site status is '{site.status}' in repository registry."],
                            suitability_score=suit_res.overall_score,
                            suitability_decision=suit_res.decision.value,
                            available_capacity_before=remaining_capacities.get(s_key, 0),
                            capacity_margin=None,
                        )
                    )
                    continue

                # Check 2: Hard safety constraints
                if not suit_res.is_eligible:
                    failed_names = [c.name for c in suit_res.hard_constraints if not c.passed]
                    reasons = []
                    for c in suit_res.hard_constraints:
                        if not c.passed:
                            c_lower = c.name.lower()
                            if "slope" in c_lower:
                                reasons.append("Safety constraint failed: Terrain slope exceeds the configured safe threshold.")
                            elif "buffer" in c_lower or "hazard" in c_lower:
                                reasons.append("Safety constraint failed: Site is within the active hazard buffer perimeter.")
                            elif "capacity" in c_lower:
                                reasons.append("Safety constraint failed: Usable site carrying capacity is zero or indeterminate.")
                            else:
                                reasons.append(f"Safety constraint failed: {c.name}.")
                    if not reasons:
                        reasons = [f"Safety constraint failed: {', '.join(failed_names)}."]
                    v_audits.append(
                        CandidateEvaluationAudit(
                            site_id=s_id,
                            site_name=site.site_name,
                            is_feasible=False,
                            rejection_code=RejectionReasonCode.UNSAFE_SITE,
                            rejection_reasons=reasons,
                            suitability_score=suit_res.overall_score,
                            suitability_decision=suit_res.decision.value,
                            available_capacity_before=remaining_capacities.get(s_key, 0),
                            capacity_margin=None,
                        )
                    )
                    continue

                # Check 3: M4-02 Overall suitability decision
                if suit_res.decision == SuitabilityDecision.UNSUITABLE:
                    v_audits.append(
                        CandidateEvaluationAudit(
                            site_id=s_id,
                            site_name=site.site_name,
                            is_feasible=False,
                            rejection_code=RejectionReasonCode.LOW_SUITABILITY,
                            rejection_reasons=[
                                f"Site classified as UNSUITABLE (Overall score {suit_res.overall_score:.1f} < threshold)."
                            ],
                            suitability_score=suit_res.overall_score,
                            suitability_decision=suit_res.decision.value,
                            available_capacity_before=remaining_capacities.get(s_key, 0),
                            capacity_margin=None,
                        )
                    )
                    continue

                # Check 4: M4-03 Unknown capacity safety invariant
                if site_unknown_capacity.get(s_id, False):
                    v_audits.append(
                        CandidateEvaluationAudit(
                            site_id=s_id,
                            site_name=site.site_name,
                            is_feasible=False,
                            rejection_code=RejectionReasonCode.UNKNOWN_CAPACITY,
                            rejection_reasons=[
                                "Critical carrying capacity dimensions are missing or unknown; "
                                "cannot treat unknown capacity as unlimited."
                            ],
                            suitability_score=suit_res.overall_score,
                            suitability_decision=suit_res.decision.value,
                            available_capacity_before=None,
                            capacity_margin=None,
                        )
                    )
                    continue

                # Check 5: M4-03 Dynamic available capacity sufficiency
                curr_avail = remaining_capacities.get(s_key, 0)
                margin = curr_avail - demand

                if curr_avail <= 0:
                    v_audits.append(
                        CandidateEvaluationAudit(
                            site_id=s_id,
                            site_name=site.site_name,
                            is_feasible=False,
                            rejection_code=RejectionReasonCode.INSUFFICIENT_CAPACITY,
                            rejection_reasons=[
                                f"Available capacity is 0 households, below the required {demand} households (deficit: {demand})."
                            ],
                            suitability_score=suit_res.overall_score,
                            suitability_decision=suit_res.decision.value,
                            available_capacity_before=curr_avail,
                            capacity_margin=margin,
                        )
                    )
                    continue

                if margin < 0:
                    v_audits.append(
                        CandidateEvaluationAudit(
                            site_id=s_id,
                            site_name=site.site_name,
                            is_feasible=False,
                            rejection_code=RejectionReasonCode.INSUFFICIENT_CAPACITY,
                            rejection_reasons=[
                                f"Available capacity is {curr_avail} households, below the required {demand} households (deficit: {abs(margin)})."
                            ],
                            suitability_score=suit_res.overall_score,
                            suitability_decision=suit_res.decision.value,
                            available_capacity_before=curr_avail,
                            capacity_margin=margin,
                        )
                    )
                    continue

                # Candidate is Feasible for this village!
                dist_km = calculate_haversine_distance_km(village.location, site.location)
                rank_score = compute_matching_rank_score(suit_res.overall_score, dist_km)

                audit_record = CandidateEvaluationAudit(
                    site_id=s_id,
                    site_name=site.site_name,
                    is_feasible=True,
                    rejection_code=None,
                    rejection_reasons=[],
                    suitability_score=suit_res.overall_score,
                    suitability_decision=suit_res.decision.value,
                    available_capacity_before=curr_avail,
                    capacity_margin=margin,
                    distance_km=dist_km,
                    rank_score=rank_score,
                )
                v_audits.append(audit_record)

                feasible_candidates.append(
                    {
                        "site": site,
                        "site_id": s_id,
                        "site_name": site.site_name,
                        "suitability_score": suit_res.overall_score,
                        "distance_km": dist_km,
                        "rank_score": rank_score,
                        "audit": audit_record,
                    }
                )

            # Step D & E: Allocate top site or mark UNASSIGNED
            if not feasible_candidates:
                # Step F: UNASSIGNED
                total_unassigned += demand

                # Summarize reasons
                codes = [a.rejection_code for a in v_audits if a.rejection_code]
                if all(c == RejectionReasonCode.INSUFFICIENT_CAPACITY for c in codes):
                    primary_code = RejectionReasonCode.INSUFFICIENT_CAPACITY
                    reason = f"All {len(sites)} candidate sites have insufficient remaining capacity for {demand} households."
                elif all(c in (RejectionReasonCode.UNSAFE_SITE, RejectionReasonCode.LOW_SUITABILITY) for c in codes):
                    primary_code = RejectionReasonCode.UNSAFE_SITE
                    reason = f"All {len(sites)} candidate sites failed safety constraints or suitability thresholds."
                elif all(c == RejectionReasonCode.UNKNOWN_CAPACITY for c in codes):
                    primary_code = RejectionReasonCode.UNKNOWN_CAPACITY
                    reason = f"All {len(sites)} candidate sites have unmeasured or unknown critical capacity."
                else:
                    primary_code = RejectionReasonCode.NO_FEASIBLE_SITE
                    reason = (
                        f"No candidate site satisfies all safety, suitability, and capacity requirements for village "
                        f"'{village.village_name}' ({len(v_audits)} candidates evaluated)."
                    )

                village_assignments.append(
                    VillageAssignmentResult(
                        village_id=village.village_id,
                        village_name=village.village_name,
                        priority_score=village.priority_score,
                        priority_band=village.priority_band,
                        incoming_households=demand,
                        incoming_population=village.incoming_population,
                        status=AssignmentStatus.UNASSIGNED,
                        assigned_site_id=None,
                        assigned_site_name=None,
                        suitability_score=None,
                        distance_km=None,
                        available_capacity_before=None,
                        available_capacity_after=None,
                        selection_reason=None,
                        unassigned_reason=reason,
                        unassigned_code=primary_code,
                        evaluated_candidates=v_audits,
                    )
                )
            else:
                # Rank feasible candidates deterministically
                sorted_feasible = sort_feasible_candidates(feasible_candidates)
                selected = sorted_feasible[0]
                sel_site = selected["site"]
                sel_s_key = str(sel_site.site_id)

                # Reserve capacity
                cap_before = remaining_capacities[sel_s_key]
                cap_after = cap_before - demand
                if cap_after < 0:
                    raise MatchingConfigurationError(
                        f"Inconsistent capacity reservation for site '{sel_site.site_name}': "
                        f"before={cap_before}, demand={demand}, after={cap_after}"
                    )
                remaining_capacities[sel_s_key] = cap_after
                total_allocated += demand

                dist_str = f", Distance: {selected['distance_km']:.1f} km" if selected["distance_km"] is not None else ""
                sel_reason = (
                    f"Selected top-ranked site '{sel_site.site_name}' "
                    f"(Suitability: {selected['suitability_score']:.1f}, Rank Score: {selected['rank_score']:.2f}{dist_str}). "
                    f"Reserved {demand} households; remaining site capacity: {cap_after} households."
                )

                village_assignments.append(
                    VillageAssignmentResult(
                        village_id=village.village_id,
                        village_name=village.village_name,
                        priority_score=village.priority_score,
                        priority_band=village.priority_band,
                        incoming_households=demand,
                        incoming_population=village.incoming_population,
                        status=AssignmentStatus.ASSIGNED,
                        assigned_site_id=sel_site.site_id,
                        assigned_site_name=sel_site.site_name,
                        suitability_score=selected["suitability_score"],
                        distance_km=selected["distance_km"],
                        available_capacity_before=cap_before,
                        available_capacity_after=cap_after,
                        selection_reason=sel_reason,
                        unassigned_reason=None,
                        unassigned_code=None,
                        evaluated_candidates=v_audits,
                    )
                )

        assigned_cnt = sum(1 for a in village_assignments if a.status == AssignmentStatus.ASSIGNED)
        unassigned_cnt = sum(1 for a in village_assignments if a.status == AssignmentStatus.UNASSIGNED)

        narrative = (
            f"Relocation matching evaluated {len(sorted_villages)} prioritized village(s) against {len(sites)} candidate site(s). "
            f"Successfully assigned {assigned_cnt} village(s) ({total_allocated} households); "
            f"{unassigned_cnt} village(s) ({total_unassigned} households) remain UNASSIGNED due to capacity or safety constraints."
        )

        return RelocationMatchingResult(
            matching_id=str(uuid.uuid4()),
            algorithm=MatchingAlgorithmType.GREEDY_PRIORITY,
            total_villages=len(sorted_villages),
            assigned_villages_count=assigned_cnt,
            unassigned_villages_count=unassigned_cnt,
            total_households_demanded=total_demanded,
            total_households_allocated=total_allocated,
            total_households_unassigned=total_unassigned,
            assignments=village_assignments,
            site_remaining_capacities=remaining_capacities,
            summary_narrative=narrative,
            execution_timestamp=datetime.now(timezone.utc),
            region_profile_id=self.region_profile_id,
        )
