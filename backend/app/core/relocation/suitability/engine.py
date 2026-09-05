"""Multi-Criteria Site Suitability Engine coordinator."""

from typing import Dict, List, Optional

from app.core.profiles.models import RegionProfile
from app.core.relocation.suitability.constraints import HardConstraintEvaluator
from app.core.relocation.suitability.contracts import (
    ConstraintEvaluation,
    CriterionScoreResult,
    CriterionType,
    SiteSuitabilityInput,
    SiteSuitabilityResult,
    SuitabilityDecision,
    SuitabilityThresholdsConfig,
    SuitabilityWeightsConfig,
)
from app.core.relocation.suitability.scoring import (
    score_capacity,
    score_emergency_services,
    score_expansion_potential,
    score_hazard_safety,
    score_healthcare_access,
    score_livelihood_access,
    score_road_access,
    score_school_access,
    score_water_availability,
)


class SiteSuitabilityEngine:
    """Deterministic Multi-Criteria Site Suitability Engine for candidate relocation sites.

    Evaluates candidate sites across 9 weighted criteria:
      1. Hazard Safety       - 30%
      2. Capacity            - 20%
      3. Road Access         - 10%
      4. Water Availability  - 10%
      5. Healthcare Access   - 10%
      6. School Access       -  5%
      7. Emergency Services  -  5%
      8. Livelihood Access   -  5%
      9. Expansion Potential -  5%
    Total: 100%.

    Strict Invariants:
      - Hard safety and capacity constraints are evaluated before weighted scoring.
      - A hard constraint failure strictly sets is_eligible=False and decision=INELIGIBLE.
      - A high weighted score can NEVER override a hard constraint failure.
      - Unknown critical information is never silently assumed safe or unlimited.
    """

    def __init__(
        self,
        weights: Optional[SuitabilityWeightsConfig] = None,
        thresholds: Optional[SuitabilityThresholdsConfig] = None,
    ) -> None:
        self.weights = weights or SuitabilityWeightsConfig()
        self.thresholds = thresholds or SuitabilityThresholdsConfig()
        self.constraint_evaluator = HardConstraintEvaluator(self.thresholds)

    @classmethod
    def from_region_profile(
        cls,
        profile: RegionProfile,
        weights: Optional[SuitabilityWeightsConfig] = None,
    ) -> "SiteSuitabilityEngine":
        """Construct engine configured with regional profile thresholds."""
        thresholds = SuitabilityThresholdsConfig.from_profile(profile)
        return cls(weights=weights, thresholds=thresholds)

    def evaluate(self, site: SiteSuitabilityInput) -> SiteSuitabilityResult:
        """Evaluate a candidate site and return a structured, explainable result."""
        # Step 1: Evaluate hard constraints
        hard_pass, constraint_evals, failure_reasons = self.constraint_evaluator.evaluate_all(site)

        # Step 2: Compute individual criterion scores and contributions
        criteria_scores: Dict[str, CriterionScoreResult] = {}
        total_weighted_score = 0.0

        scorers = [
            (CriterionType.HAZARD_SAFETY, score_hazard_safety),
            (CriterionType.CAPACITY, score_capacity),
            (CriterionType.ROAD_ACCESS, score_road_access),
            (CriterionType.WATER_AVAILABILITY, score_water_availability),
            (CriterionType.HEALTHCARE_ACCESS, score_healthcare_access),
            (CriterionType.SCHOOL_ACCESS, score_school_access),
            (CriterionType.EMERGENCY_SERVICES, score_emergency_services),
            (CriterionType.LIVELIHOOD_ACCESS, score_livelihood_access),
            (CriterionType.EXPANSION_POTENTIAL, score_expansion_potential),
        ]

        for crit_type, scorer_fn in scorers:
            raw_score, desc, audit = scorer_fn(site, self.thresholds)
            weight = self.weights.get_weight(crit_type)
            weighted_contrib = round(raw_score * weight, 4)
            total_weighted_score += weighted_contrib

            criteria_scores[crit_type.value] = CriterionScoreResult(
                criterion=crit_type,
                criterion_name=crit_type.label,
                raw_score=round(raw_score, 2),
                weight=round(weight, 4),
                weighted_contribution=round(weighted_contrib, 2),
                description=desc,
                audit_notes=audit,
            )

        overall_score = round(min(100.0, max(0.0, total_weighted_score)), 2)

        # Step 3: Determine eligibility and categorical decision
        summary_reasons: List[str] = []

        if not hard_pass:
            # INVARIANT: Hard constraint failure strictly overrides weighted score
            is_eligible = False
            decision = SuitabilityDecision.INELIGIBLE
            summary_reasons.extend(failure_reasons)
            summary_reasons.append(
                f"Site is disqualified due to {len(failure_reasons)} hard constraint failure(s). "
                f"Calculated weighted score ({overall_score:.1f}) cannot override hard safety/capacity limits."
            )
        else:
            # Check capacity bottleneck constraint
            avail_hh = site.available_households if site.available_households is not None else site.max_households
            is_capacity_bottleneck = avail_hh is not None and avail_hh < self.thresholds.min_viable_households

            if overall_score >= self.thresholds.suitable_score_threshold:
                if is_capacity_bottleneck:
                    is_eligible = True
                    decision = SuitabilityDecision.CONSTRAINED
                    summary_reasons.append(
                        f"Site score ({overall_score:.1f}/100) is high, but available capacity ({avail_hh} households) "
                        f"is below standard community transfer threshold ({self.thresholds.min_viable_households} households). "
                        "Classified as CONSTRAINED."
                    )
                else:
                    is_eligible = True
                    decision = SuitabilityDecision.SUITABLE
                    summary_reasons.append(
                        f"Site meets all hard safety and capacity standards with overall suitability score of {overall_score:.1f}/100. "
                        "Recommended as SUITABLE for relocation."
                    )
            elif overall_score >= self.thresholds.constrained_score_threshold:
                is_eligible = True
                decision = SuitabilityDecision.CONSTRAINED
                summary_reasons.append(
                    f"Site passed hard constraints but received moderate suitability score ({overall_score:.1f}/100). "
                    "Classified as CONSTRAINED: infrastructure or access upgrades advised."
                )
            else:
                is_eligible = False
                decision = SuitabilityDecision.UNSUITABLE
                summary_reasons.append(
                    f"Site score ({overall_score:.1f}/100) falls below minimum acceptable threshold "
                    f"({self.thresholds.constrained_score_threshold:.1f}/100). Classified as UNSUITABLE."
                )

        # Identify failed constraints list
        failed_constraint_names = [e.name for e in constraint_evals if not e.passed]

        return SiteSuitabilityResult(
            site_id=site.site_id,
            site_name=site.name,
            is_eligible=is_eligible,
            decision=decision,
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            hard_constraints=constraint_evals,
            failed_constraints=failed_constraint_names,
            summary_reasons=summary_reasons,
        )
