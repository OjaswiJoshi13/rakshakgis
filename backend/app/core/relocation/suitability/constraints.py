"""Hard safety and capacity constraint evaluation for candidate relocation sites."""

from typing import List, Tuple

from app.core.relocation.suitability.contracts import (
    ConstraintEvaluation,
    HardConstraintType,
    SiteSuitabilityInput,
    SuitabilityThresholdsConfig,
)


class HardConstraintEvaluator:
    """Evaluates mandatory hard safety and capacity constraints prior to weighted scoring."""

    def __init__(self, thresholds: SuitabilityThresholdsConfig) -> None:
        self.thresholds = thresholds

    def evaluate_all(
        self, site: SiteSuitabilityInput
    ) -> Tuple[bool, List[ConstraintEvaluation], List[str]]:
        """Evaluate all hard constraints on a candidate site.

        Returns:
            Tuple of:
              - all_passed: bool (True only if every constraint passed)
              - evaluations: List[ConstraintEvaluation]
              - failure_reasons: List[str]
        """
        evaluations: List[ConstraintEvaluation] = []
        failure_reasons: List[str] = []

        # 1. Hazard Slope Safety
        eval_slope = self._evaluate_slope_safety(site)
        evaluations.append(eval_slope)
        if not eval_slope.passed:
            failure_reasons.append(eval_slope.reason or "Failed slope safety constraint")

        # 2. Hazard Buffer Distance
        eval_buffer = self._evaluate_hazard_buffer(site)
        evaluations.append(eval_buffer)
        if not eval_buffer.passed:
            failure_reasons.append(eval_buffer.reason or "Failed hazard buffer constraint")

        # 3. Known Usable Capacity
        eval_capacity = self._evaluate_usable_capacity(site)
        evaluations.append(eval_capacity)
        if not eval_capacity.passed:
            failure_reasons.append(eval_capacity.reason or "Failed usable capacity constraint")

        all_passed = all(e.passed for e in evaluations)
        return all_passed, evaluations, failure_reasons


    def _evaluate_slope_safety(self, site: SiteSuitabilityInput) -> ConstraintEvaluation:
        """Check terrain slope safety against configured max safe slope."""
        if site.terrain_slope_deg is None:
            return ConstraintEvaluation(
                constraint_type=HardConstraintType.HAZARD_SLOPE,
                name="Terrain Slope Safety",
                passed=False,
                actual_value=None,
                threshold_value=self.thresholds.max_safe_slope_deg,
                reason="Terrain slope is unknown; cannot verify hazard slope safety.",
            )

        passed = site.terrain_slope_deg <= self.thresholds.max_safe_slope_deg
        reason = (
            None
            if passed
            else (
                f"Terrain slope {site.terrain_slope_deg:.1f}° exceeds maximum safe limit "
                f"({self.thresholds.max_safe_slope_deg:.1f}°); severe landslide/creep hazard."
            )
        )
        return ConstraintEvaluation(
            constraint_type=HardConstraintType.HAZARD_SLOPE,
            name="Terrain Slope Safety",
            passed=passed,
            actual_value=site.terrain_slope_deg,
            threshold_value=self.thresholds.max_safe_slope_deg,
            reason=reason,
        )

    def _evaluate_hazard_buffer(self, site: SiteSuitabilityInput) -> ConstraintEvaluation:
        """Check hazard exclusion buffer distance."""
        if site.hazard_buffer_distance_m is None:
            # If not explicitly specified, pass with note (cannot fail if external observation not present)
            return ConstraintEvaluation(
                constraint_type=HardConstraintType.HAZARD_BUFFER,
                name="Hazard Exclusion Buffer",
                passed=True,
                actual_value=None,
                threshold_value=self.thresholds.min_hazard_buffer_m,
                reason="Hazard buffer distance not provided; assumed outside active hazard runout zone.",
            )

        passed = site.hazard_buffer_distance_m >= self.thresholds.min_hazard_buffer_m
        reason = (
            None
            if passed
            else (
                f"Hazard buffer distance {site.hazard_buffer_distance_m:.1f}m is within the "
                f"{self.thresholds.min_hazard_buffer_m:.1f}m mandatory hazard exclusion buffer."
            )
        )
        return ConstraintEvaluation(
            constraint_type=HardConstraintType.HAZARD_BUFFER,
            name="Hazard Exclusion Buffer",
            passed=passed,
            actual_value=site.hazard_buffer_distance_m,
            threshold_value=self.thresholds.min_hazard_buffer_m,
            reason=reason,
        )

    def _evaluate_usable_capacity(self, site: SiteSuitabilityInput) -> ConstraintEvaluation:
        """Check that site has known, valid, and positive usable capacity."""
        avail_hh = site.available_households
        max_hh = site.max_households

        # Both cannot be None (missing capacity must never be treated as unlimited)
        if avail_hh is None and max_hh is None:
            return ConstraintEvaluation(
                constraint_type=HardConstraintType.USABLE_CAPACITY,
                name="Known Usable Capacity",
                passed=False,
                actual_value=None,
                threshold_value="> 0 households",
                reason="Capacity data is missing/unknown; cannot treat site as having unlimited capacity.",
            )

        effective_hh = avail_hh if avail_hh is not None else max_hh
        if effective_hh is None or effective_hh <= 0:
            return ConstraintEvaluation(
                constraint_type=HardConstraintType.USABLE_CAPACITY,
                name="Known Usable Capacity",
                passed=False,
                actual_value=effective_hh,
                threshold_value="> 0 households",
                reason=f"Usable household capacity is {effective_hh}; site cannot accommodate any relocation.",
            )

        return ConstraintEvaluation(
            constraint_type=HardConstraintType.USABLE_CAPACITY,
            name="Known Usable Capacity",
            passed=True,
            actual_value=effective_hh,
            threshold_value="> 0 households",
            reason=None,
        )
