"""Risk Classification & Grading Engine for RakshakGIS.

Authoritative Risk Bands:
- [0.0, 25.0)   -> SAFE
- [25.0, 50.0)  -> MODERATE
- [50.0, 70.0)  -> HIGH
- [70.0, 85.0)  -> VERY_HIGH
- [85.0, 100.0] -> CRITICAL

Scope Boundary:
- Sole responsibility: Classify an already computed composite risk score into its authoritative risk band.
- Zero risk re-computation (M3-06).
- Zero Red Zone demarcation (M3-10 / M3-11).
- Zero relocation priority (M3-12).
"""

import math
from typing import Optional, Union

from app.core.profiles import get_profile
from app.core.profiles.models import RegionProfile, RiskBand
from app.core.risk.classification.contracts import (
    RiskClassificationExplainability,
    RiskClassificationResult,
    RiskScoreBandsConfig,
)
from app.core.risk.classification.errors import InvalidRiskScoreError
from app.core.risk.computation.contracts import (
    CompositeRiskResult,
    RiskComputationStatus,
)


class RiskClassificationEngine:
    """Deterministic, region-agnostic engine that classifies composite risk scores into authoritative risk bands."""

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        bands_config: Optional[RiskScoreBandsConfig] = None,
    ):
        """Initialize the classification engine with configured cutoffs or active regional profile.

        Args:
            profile: Optional regional profile to source cutoffs from (defaults to Himalayan pilot).
            bands_config: Optional explicit RiskScoreBandsConfig override.
        """
        if bands_config is not None:
            self.bands_config = bands_config
            self.profile = profile
        else:
            self.profile = profile if profile is not None else get_profile("himalayan_pilot")
            self.bands_config = RiskScoreBandsConfig.from_profile(self.profile)

    def classify(
        self,
        score_or_result: Union[float, int, CompositeRiskResult],
        village_id: Optional[str] = None,
    ) -> RiskClassificationResult:
        """Classify a 0.0 - 100.0 composite risk score or CompositeRiskResult into its authoritative risk band.

        Args:
            score_or_result: Numeric float score or an M3-06 CompositeRiskResult.
            village_id: Optional village identifier override.

        Returns:
            RiskClassificationResult with preserved score, RiskBand enum, and explainability audit metadata.

        Raises:
            InvalidRiskScoreError: If score is outside [0.0, 100.0], NaN, Inf, non-numeric, or from an uncomputed result.
        """
        composite_result: Optional[CompositeRiskResult] = None
        target_village_id: Optional[str] = village_id

        # 1. Unpack CompositeRiskResult if provided
        if isinstance(score_or_result, CompositeRiskResult):
            composite_result = score_or_result
            if target_village_id is None:
                target_village_id = composite_result.village_id

            if composite_result.status != RiskComputationStatus.COMPUTED or composite_result.score is None:
                raise InvalidRiskScoreError(
                    f"Cannot classify incomplete composite risk result: status='{composite_result.status.value}', "
                    f"score={composite_result.score}. Only successfully COMPUTED results can be classified."
                )
            raw_score = composite_result.score
        elif isinstance(score_or_result, bool):
            # Booleans are subclasses of int in Python; explicitly reject
            raise InvalidRiskScoreError(
                f"Invalid risk score type 'bool': value {score_or_result} cannot be classified."
            )
        elif isinstance(score_or_result, (int, float)):
            raw_score = float(score_or_result)
        else:
            raise InvalidRiskScoreError(
                f"Unsupported risk score input type '{type(score_or_result).__name__}'. "
                f"Expected float, int, or CompositeRiskResult."
            )

        # 2. Validate numerical domain invariants
        if math.isnan(raw_score) or math.isinf(raw_score):
            raise InvalidRiskScoreError(
                f"Invalid risk score: cannot classify NaN or infinite value ({raw_score})."
            )

        if not (0.0 <= raw_score <= 100.0):
            raise InvalidRiskScoreError(
                f"Risk score {raw_score} out of valid bounds [0.0, 100.0]. "
                f"Safety guard: Invalid classification scores are strictly rejected and never clamped."
            )

        # 3. Determine authoritative risk band
        cfg = self.bands_config

        if 0.0 <= raw_score < cfg.safe_max:
            band = RiskBand.SAFE
            lower_bound = 0.0
            upper_bound = cfg.safe_max
            lower_inclusive = True
            upper_inclusive = False
            interval_notation = f"[0.0, {cfg.safe_max:.1f})"
        elif cfg.safe_max <= raw_score < cfg.moderate_max:
            band = RiskBand.MODERATE
            lower_bound = cfg.safe_max
            upper_bound = cfg.moderate_max
            lower_inclusive = True
            upper_inclusive = False
            interval_notation = f"[{cfg.safe_max:.1f}, {cfg.moderate_max:.1f})"
        elif cfg.moderate_max <= raw_score < cfg.high_max:
            band = RiskBand.HIGH
            lower_bound = cfg.moderate_max
            upper_bound = cfg.high_max
            lower_inclusive = True
            upper_inclusive = False
            interval_notation = f"[{cfg.moderate_max:.1f}, {cfg.high_max:.1f})"
        elif cfg.high_max <= raw_score < cfg.very_high_max:
            band = RiskBand.VERY_HIGH
            lower_bound = cfg.high_max
            upper_bound = cfg.very_high_max
            lower_inclusive = True
            upper_inclusive = False
            interval_notation = f"[{cfg.high_max:.1f}, {cfg.very_high_max:.1f})"
        else:
            # cfg.very_high_max <= raw_score <= cfg.critical_max
            band = RiskBand.CRITICAL
            lower_bound = cfg.very_high_max
            upper_bound = cfg.critical_max
            lower_inclusive = True
            upper_inclusive = True
            interval_notation = f"[{cfg.very_high_max:.1f}, {cfg.critical_max:.1f}]"

        band_name_upper = band.name  # SAFE, MODERATE, HIGH, VERY_HIGH, CRITICAL
        audit_trail = (
            f"Score {raw_score:.4f} classified as {band_name_upper} based on interval {interval_notation}."
        )

        explainability = RiskClassificationExplainability(
            band=band,
            band_name=band_name_upper,
            score=raw_score,
            interval_notation=interval_notation,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            lower_inclusive=lower_inclusive,
            upper_inclusive=upper_inclusive,
            audit_trail=audit_trail,
        )

        return RiskClassificationResult(
            score=raw_score,
            band=band,
            village_id=target_village_id,
            explainability=explainability,
            composite_result=composite_result,
        )
