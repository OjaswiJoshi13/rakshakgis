"""Risk Normalization Engine for RakshakGIS.

Sole responsibility:
Transform validated heterogeneous hazard/exposure-related observations into comparable
normalized factor values on a common 0.0 — 100.0 scale.

Explicit Scope Boundary:
This engine does NOT compute multi-hazard composite risk (0.30H + 0.20F + ...),
risk bands (SAFE/MODERATE/HIGH/CRITICAL), Red Zones, or relocation priorities.
Those are deferred to M3-06, M3-07, M3-10, and M3-12 respectively.
Demographic exposure and vulnerability scoring are deferred to M3-09.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.profiles import get_profile
from app.core.profiles.models import RegionProfile
from app.core.risk.normalization.contracts import (
    CategoricalSeverityPolicy,
    FactorCategory,
    LinearRangeConfig,
    NormalizationExplainability,
    NormalizationMethod,
    NormalizationResult,
    NormalizationStatus,
    PiecewiseThresholdConfig,
)
from app.core.risk.normalization.errors import (
    InvalidInputError,
    NormalizationConfigError,
    NormalizationError,
    UnsupportedFactorError,
)
from app.core.risk.normalization.methods import (
    categorical_severity_normalize,
    linear_normalize,
    piecewise_threshold_normalize,
)
from app.data.ingestion.schemas import (
    CanonicalFloodRecord,
    CanonicalHazardObservationRecord,
    CanonicalLandslideRecord,
    CanonicalPopulationRecord,
    CanonicalRainfallRecord,
)
from app.data.providers.contracts import (
    NormalizedFloodRecord,
    NormalizedHazardObservationRecord,
    NormalizedLandslideRecord,
    NormalizedPopulationRecord,
    NormalizedRainfallRecord,
    ProviderProvenance,
)


class RiskNormalizationEngine:
    """Deterministic, region-agnostic engine that transforms raw hazard observations into 0-100 factors.

    Thresholds and regional parameters are sourced dynamically from the active RegionProfile (M3-01),
    ensuring that the mathematical engine itself contains no hardcoded regional constants.
    """

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        severity_policy: Optional[CategoricalSeverityPolicy] = None,
        custom_flood_config: Optional[LinearRangeConfig] = None,
        custom_landslide_config: Optional[LinearRangeConfig] = None,
    ):
        """Initialize the normalization engine with a regional profile and normalization policies.

        Args:
            profile: Regional configuration profile (defaults to the active Himalayan pilot profile).
            severity_policy: Policy mapping categorical severity strings to [0.0, 100.0] scores.
            custom_flood_config: Optional override for flood water level range scaling.
            custom_landslide_config: Optional override for landslide debris volume range scaling.
        """
        self.profile = profile if profile is not None else get_profile("himalayan_pilot")
        self.severity_policy = severity_policy if severity_policy is not None else CategoricalSeverityPolicy()

        # 1. Source canonical rainfall thresholds directly from regional profile
        rainfall_heavy = self.profile.hazard_parameters.thresholds.rainfall_heavy_24h_mm
        rainfall_very_heavy = self.profile.hazard_parameters.thresholds.rainfall_very_heavy_24h_mm

        # IMD defines extremely heavy rainfall as >= 204.4 mm / 24h
        extreme_rainfall_benchmark = max(rainfall_very_heavy * 1.75, 204.4)

        # Benchmarks: (0mm -> 0.0), (Heavy -> 50.0), (Very Heavy -> 80.0), (Extreme -> 100.0)
        self.rainfall_piecewise_config = PiecewiseThresholdConfig(
            benchmarks=[
                (0.0, 0.0),
                (rainfall_heavy, 50.0),
                (rainfall_very_heavy, 80.0),
                (extreme_rainfall_benchmark, 100.0),
            ]
        )

        # 2. Configure flood scaling (water level in meters above danger mark)
        # Default: 0.0 m above danger -> 0.0 factor; 5.0 m above danger -> 100.0 factor
        self.flood_config = (
            custom_flood_config
            if custom_flood_config is not None
            else LinearRangeConfig(min_value=0.0, max_value=5.0)
        )

        # 3. Configure landslide scaling (debris volume in cubic meters)
        # Default: 0.0 m³ -> 0.0 factor; 10,000 m³ -> 100.0 factor
        self.landslide_config = (
            custom_landslide_config
            if custom_landslide_config is not None
            else LinearRangeConfig(min_value=0.0, max_value=10000.0)
        )

        # 4. Source seismic bounds from regional scenario parameters
        min_seismic = self.profile.scenario_bounds.min_seismic_intensity_mmi
        max_seismic = self.profile.scenario_bounds.max_seismic_intensity_mmi
        critical_seismic = self.profile.hazard_parameters.thresholds.seismic_critical_mmi or 7.0

        self.seismic_piecewise_config = PiecewiseThresholdConfig(
            benchmarks=[
                (min_seismic, 0.0),
                (critical_seismic, 75.0),
                (max_seismic, 100.0),
            ]
        )

    # =========================================================================
    # Direct Factor Normalization APIs
    # =========================================================================

    def normalize_linear(
        self,
        value: Optional[float],
        config: LinearRangeConfig,
        factor_category: FactorCategory,
        record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> NormalizationResult:
        """Normalize a continuous numeric observation using two-point linear scaling."""
        if value is None:
            return self._build_unavailable_result(
                factor_category=factor_category,
                record_id=record_id,
                method=NormalizationMethod.LINEAR,
                reason="Input numeric value is None/missing; cannot normalize unknown hazard state.",
                provenance=provenance,
            )

        try:
            score, was_clamped, clamp_reason = linear_normalize(value, config)
            explainability = NormalizationExplainability(
                method=NormalizationMethod.LINEAR,
                parameters_used={
                    "min_value": config.min_value,
                    "max_value": config.max_value,
                    "clamp_min": config.clamp_min,
                    "clamp_max": config.clamp_max,
                },
                input_domain_range=(config.min_value, config.max_value),
                formula_description=f"Linear range normalization: {config.min_value} -> 0.0, {config.max_value} -> 100.0",
                clamping_reason=clamp_reason,
            )
            return NormalizationResult(
                record_id=record_id,
                factor_category=factor_category,
                status=NormalizationStatus.NORMALIZED,
                raw_input_value=value,
                normalized_value=score,
                was_clamped=was_clamped,
                is_unknown_or_unavailable=False,
                explainability=explainability,
                provenance=provenance,
            )
        except InvalidInputError as e:
            return self._build_invalid_result(
                factor_category=factor_category,
                record_id=record_id,
                raw_value=value,
                method=NormalizationMethod.LINEAR,
                reason=str(e),
                provenance=provenance,
            )

    def normalize_piecewise(
        self,
        value: Optional[float],
        config: PiecewiseThresholdConfig,
        factor_category: FactorCategory,
        record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        thresholds_applied: Optional[Dict[str, float]] = None,
        formula_description: Optional[str] = None,
    ) -> NormalizationResult:
        """Normalize a continuous numeric observation using piecewise threshold interpolation."""
        if value is None:
            return self._build_unavailable_result(
                factor_category=factor_category,
                record_id=record_id,
                method=NormalizationMethod.THRESHOLD_PIECEWISE,
                reason="Input numeric value is None/missing; cannot normalize unknown hazard state.",
                provenance=provenance,
            )

        try:
            score, was_clamped, clamp_reason = piecewise_threshold_normalize(value, config)
            explainability = NormalizationExplainability(
                method=NormalizationMethod.THRESHOLD_PIECEWISE,
                parameters_used={"benchmarks": config.benchmarks},
                thresholds_applied=thresholds_applied,
                input_domain_range=(config.benchmarks[0][0], config.benchmarks[-1][0]),
                formula_description=(
                    formula_description
                    or "Piecewise linear interpolation through configured domain thresholds."
                ),
                clamping_reason=clamp_reason,
            )
            return NormalizationResult(
                record_id=record_id,
                factor_category=factor_category,
                status=NormalizationStatus.NORMALIZED,
                raw_input_value=value,
                normalized_value=score,
                was_clamped=was_clamped,
                is_unknown_or_unavailable=False,
                explainability=explainability,
                provenance=provenance,
            )
        except InvalidInputError as e:
            return self._build_invalid_result(
                factor_category=factor_category,
                record_id=record_id,
                raw_value=value,
                method=NormalizationMethod.THRESHOLD_PIECEWISE,
                reason=str(e),
                provenance=provenance,
            )

    def normalize_categorical(
        self,
        severity: Optional[str],
        factor_category: FactorCategory,
        policy: Optional[CategoricalSeverityPolicy] = None,
        record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> NormalizationResult:
        """Normalize a qualitative severity string into a deterministic factor score."""
        if severity is None or not str(severity).strip():
            return self._build_unavailable_result(
                factor_category=factor_category,
                record_id=record_id,
                method=NormalizationMethod.CATEGORICAL_SEVERITY,
                reason="Severity label is missing or empty; cannot normalize unknown severity.",
                provenance=provenance,
            )

        active_policy = policy if policy is not None else self.severity_policy
        try:
            score, was_clamped, clamp_reason = categorical_severity_normalize(severity, active_policy)
            explainability = NormalizationExplainability(
                method=NormalizationMethod.CATEGORICAL_SEVERITY,
                parameters_used={"mappings": active_policy.mappings},
                formula_description="Deterministic categorical severity mapping to [0.0, 100.0].",
                clamping_reason=clamp_reason,
            )
            return NormalizationResult(
                record_id=record_id,
                factor_category=factor_category,
                status=NormalizationStatus.NORMALIZED,
                raw_input_value=severity,
                normalized_value=score,
                was_clamped=was_clamped,
                is_unknown_or_unavailable=False,
                explainability=explainability,
                provenance=provenance,
            )
        except InvalidInputError as e:
            return self._build_invalid_result(
                factor_category=factor_category,
                record_id=record_id,
                raw_value=severity,
                method=NormalizationMethod.CATEGORICAL_SEVERITY,
                reason=str(e),
                provenance=provenance,
            )

    # =========================================================================
    # Hazard-Specific Normalization APIs
    # =========================================================================

    def normalize_rainfall(
        self,
        rainfall_24h_mm: Optional[float],
        record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        is_heavy_rain: Optional[bool] = None,
        is_very_heavy_rain: Optional[bool] = None,
    ) -> NormalizationResult:
        """Normalize precipitation observation using M3-01 profile thresholds.

        Note: is_heavy_rain and is_very_heavy_rain are cumulative exceedance flags from M3-03.
        They are recorded in explainability metadata and are not treated as mutually exclusive buckets.
        """
        heavy_thresh = self.profile.hazard_parameters.thresholds.rainfall_heavy_24h_mm
        very_heavy_thresh = self.profile.hazard_parameters.thresholds.rainfall_very_heavy_24h_mm

        thresholds_applied = {
            "rainfall_heavy_24h_mm": heavy_thresh,
            "rainfall_very_heavy_24h_mm": very_heavy_thresh,
        }
        formula_desc = (
            f"Piecewise linear interpolation based on {self.profile.metadata.name} rainfall thresholds: "
            f"0mm -> 0.0, Heavy ({heavy_thresh}mm) -> 50.0, Very Heavy ({very_heavy_thresh}mm) -> 80.0, "
            f"Extreme ({self.rainfall_piecewise_config.benchmarks[-1][0]:.1f}mm) -> 100.0."
        )

        res = self.normalize_piecewise(
            value=rainfall_24h_mm,
            config=self.rainfall_piecewise_config,
            factor_category=FactorCategory.RAINFALL,
            record_id=record_id,
            provenance=provenance,
            thresholds_applied=thresholds_applied,
            formula_description=formula_desc,
        )

        # Preserve cumulative exceedance flags in parameters_used if provided
        if is_heavy_rain is not None or is_very_heavy_rain is not None:
            updated_params = dict(res.explainability.parameters_used)
            updated_params["cumulative_flags"] = {
                "is_heavy_rain": is_heavy_rain,
                "is_very_heavy_rain": is_very_heavy_rain,
            }
            res = res.model_copy(
                update={
                    "explainability": res.explainability.model_copy(
                        update={"parameters_used": updated_params}
                    )
                }
            )

        return res

    def normalize_flood(
        self,
        water_level_m_above_danger: Optional[float],
        record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        flood_type: Optional[str] = None,
    ) -> NormalizationResult:
        """Normalize hydrological flood observation based on meters above danger mark."""
        res = self.normalize_linear(
            value=water_level_m_above_danger,
            config=self.flood_config,
            factor_category=FactorCategory.FLOOD,
            record_id=record_id,
            provenance=provenance,
        )
        if flood_type is not None:
            updated_params = dict(res.explainability.parameters_used)
            updated_params["flood_type"] = flood_type
            res = res.model_copy(
                update={
                    "explainability": res.explainability.model_copy(
                        update={"parameters_used": updated_params}
                    )
                }
            )
        return res

    def normalize_landslide(
        self,
        debris_volume_cu_m: Optional[float],
        record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        road_blocked: Optional[bool] = None,
    ) -> NormalizationResult:
        """Normalize landslide debris volume observation into a 0-100 hazard factor."""
        res = self.normalize_linear(
            value=debris_volume_cu_m,
            config=self.landslide_config,
            factor_category=FactorCategory.LANDSLIDE,
            record_id=record_id,
            provenance=provenance,
        )
        if road_blocked is not None:
            updated_params = dict(res.explainability.parameters_used)
            updated_params["road_blocked"] = road_blocked
            res = res.model_copy(
                update={
                    "explainability": res.explainability.model_copy(
                        update={"parameters_used": updated_params}
                    )
                }
            )
        return res

    def normalize_hazard_observation(
        self,
        intensity_value: Optional[float],
        hazard_type: Optional[str],
        record_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        severity: Optional[str] = None,
    ) -> NormalizationResult:
        """Normalize generalized multi-hazard telemetry observation."""
        if not hazard_type or not str(hazard_type).strip():
            return self._build_invalid_result(
                factor_category=FactorCategory.HAZARD_OBSERVATION,
                record_id=record_id,
                raw_value=intensity_value,
                method=NormalizationMethod.LINEAR,
                reason="Hazard type is missing or empty.",
                provenance=provenance,
            )

        clean_type = hazard_type.strip().lower()

        if clean_type == "rainfall":
            return self.normalize_rainfall(
                rainfall_24h_mm=intensity_value,
                record_id=record_id,
                provenance=provenance,
            )
        elif clean_type in ("flood", "flash_flood"):
            return self.normalize_flood(
                water_level_m_above_danger=intensity_value,
                record_id=record_id,
                provenance=provenance,
                flood_type=clean_type,
            )
        elif clean_type == "landslide":
            return self.normalize_landslide(
                debris_volume_cu_m=intensity_value,
                record_id=record_id,
                provenance=provenance,
            )
        elif clean_type == "seismic":
            thresholds_applied = {
                "min_seismic_mmi": self.profile.scenario_bounds.min_seismic_intensity_mmi,
                "critical_seismic_mmi": self.profile.hazard_parameters.thresholds.seismic_critical_mmi or 7.0,
                "max_seismic_mmi": self.profile.scenario_bounds.max_seismic_intensity_mmi,
            }
            return self.normalize_piecewise(
                value=intensity_value,
                config=self.seismic_piecewise_config,
                factor_category=FactorCategory.SEISMIC,
                record_id=record_id,
                provenance=provenance,
                thresholds_applied=thresholds_applied,
                formula_description="Seismic intensity MMI normalization through regional critical thresholds.",
            )
        else:
            # If intensity value is not directly mapped for custom hazard, fall back to categorical severity
            if severity is not None and str(severity).strip():
                return self.normalize_categorical(
                    severity=severity,
                    factor_category=FactorCategory.HAZARD_OBSERVATION,
                    record_id=record_id,
                    provenance=provenance,
                )
            return self._build_invalid_result(
                factor_category=FactorCategory.HAZARD_OBSERVATION,
                record_id=record_id,
                raw_value=intensity_value,
                method=NormalizationMethod.LINEAR,
                reason=f"Unsupported hazard type '{hazard_type}' with no valid severity fallback.",
                provenance=provenance,
            )

    # =========================================================================
    # Universal Record Ingestion & Normalization API
    # =========================================================================

    def normalize_record(self, record: Any) -> NormalizationResult:
        """Normalize an ingested canonical record or provider normalized record.

        Accepts:
        - CanonicalRainfallRecord / NormalizedRainfallRecord
        - CanonicalFloodRecord / NormalizedFloodRecord
        - CanonicalLandslideRecord / NormalizedLandslideRecord
        - CanonicalHazardObservationRecord / NormalizedHazardObservationRecord
        - CanonicalPopulationRecord / NormalizedPopulationRecord (deferred to M3-09)
        """
        if record is None:
            return self._build_unavailable_result(
                factor_category=FactorCategory.HAZARD_OBSERVATION,
                record_id=None,
                method=NormalizationMethod.LINEAR,
                reason="Input record is None.",
            )

        # 1. Rainfall Records
        if isinstance(record, (CanonicalRainfallRecord, NormalizedRainfallRecord)):
            return self.normalize_rainfall(
                rainfall_24h_mm=getattr(record, "rainfall_24h_mm", None),
                record_id=getattr(record, "record_id", None),
                provenance=getattr(record, "provenance", None),
                is_heavy_rain=getattr(record, "is_heavy_rain", None),
                is_very_heavy_rain=getattr(record, "is_very_heavy_rain", None),
            )

        # 2. Flood Records
        if isinstance(record, (CanonicalFloodRecord, NormalizedFloodRecord)):
            return self.normalize_flood(
                water_level_m_above_danger=getattr(record, "water_level_m_above_danger", None),
                record_id=getattr(record, "record_id", None),
                provenance=getattr(record, "provenance", None),
                flood_type=getattr(record, "flood_type", None),
            )

        # 3. Landslide Records
        if isinstance(record, (CanonicalLandslideRecord, NormalizedLandslideRecord)):
            return self.normalize_landslide(
                debris_volume_cu_m=getattr(record, "debris_volume_cu_m", None),
                record_id=getattr(record, "record_id", None),
                provenance=getattr(record, "provenance", None),
                road_blocked=getattr(record, "road_blocked", None),
            )

        # 4. Multi-Hazard Sensor Observation Records
        if isinstance(record, (CanonicalHazardObservationRecord, NormalizedHazardObservationRecord)):
            return self.normalize_hazard_observation(
                intensity_value=getattr(record, "intensity_value", None),
                hazard_type=getattr(record, "hazard_type", None),
                record_id=getattr(record, "record_id", None),
                provenance=getattr(record, "provenance", None),
                severity=getattr(record, "severity", None),
            )

        # 5. Population / Exposure Records (Explicitly deferred to M3-09)
        if isinstance(record, (CanonicalPopulationRecord, NormalizedPopulationRecord)):
            explainability = NormalizationExplainability(
                method=NormalizationMethod.DEFERRED,
                parameters_used={
                    "total_population": getattr(record, "total_population", 0),
                    "village_id": getattr(record, "village_id", None),
                },
                formula_description="Demographic exposure and vulnerability scoring is deferred to chunk M3-09.",
            )
            return NormalizationResult(
                record_id=getattr(record, "village_id", None),
                factor_category=FactorCategory.POPULATION_EXPOSURE,
                status=NormalizationStatus.DEFERRED,
                raw_input_value=getattr(record, "total_population", None),
                normalized_value=None,
                was_clamped=False,
                is_unknown_or_unavailable=True,
                diagnostic_message=(
                    "Population exposure and demographic vulnerability scoring is deferred to chunk M3-09. "
                    "Per specification, M3-05 handles hazard factor normalization only."
                ),
                explainability=explainability,
                provenance=getattr(record, "provenance", None),
            )

        # 6. Fallback for unknown object or dictionary
        record_id = getattr(record, "record_id", None) if hasattr(record, "record_id") else None
        if isinstance(record, dict):
            record_id = record.get("record_id")
            if "rainfall_24h_mm" in record:
                return self.normalize_rainfall(
                    rainfall_24h_mm=record.get("rainfall_24h_mm"),
                    record_id=record_id,
                    provenance=record.get("provenance"),
                    is_heavy_rain=record.get("is_heavy_rain"),
                    is_very_heavy_rain=record.get("is_very_heavy_rain"),
                )
            if "water_level_m_above_danger" in record:
                return self.normalize_flood(
                    water_level_m_above_danger=record.get("water_level_m_above_danger"),
                    record_id=record_id,
                    provenance=record.get("provenance"),
                    flood_type=record.get("flood_type"),
                )
            if "debris_volume_cu_m" in record:
                return self.normalize_landslide(
                    debris_volume_cu_m=record.get("debris_volume_cu_m"),
                    record_id=record_id,
                    provenance=record.get("provenance"),
                    road_blocked=record.get("road_blocked"),
                )
            if "intensity_value" in record and "hazard_type" in record:
                return self.normalize_hazard_observation(
                    intensity_value=record.get("intensity_value"),
                    hazard_type=record.get("hazard_type"),
                    record_id=record_id,
                    provenance=record.get("provenance"),
                    severity=record.get("severity"),
                )
            if "severity" in record:
                return self.normalize_categorical(
                    severity=record.get("severity"),
                    factor_category=FactorCategory.HAZARD_OBSERVATION,
                    record_id=record_id,
                    provenance=record.get("provenance"),
                )

        return self._build_invalid_result(
            factor_category=FactorCategory.HAZARD_OBSERVATION,
            record_id=record_id,
            raw_value=None,
            method=NormalizationMethod.LINEAR,
            reason=f"Unsupported record type: {type(record).__name__}",
        )

    # =========================================================================
    # Internal Helper Methods
    # =========================================================================

    def _build_unavailable_result(
        self,
        factor_category: FactorCategory,
        record_id: Optional[str],
        method: NormalizationMethod,
        reason: str,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> NormalizationResult:
        """Construct a strongly typed UNAVAILABLE result, strictly ensuring normalized_value is None."""
        explainability = NormalizationExplainability(
            method=method,
            parameters_used={"unavailable_reason": reason},
            formula_description="Safety guard: Missing or unmonitored observations never produce a zero score.",
        )
        return NormalizationResult(
            record_id=record_id,
            factor_category=factor_category,
            status=NormalizationStatus.UNAVAILABLE,
            raw_input_value=None,
            normalized_value=None,
            was_clamped=False,
            is_unknown_or_unavailable=True,
            diagnostic_message=reason,
            explainability=explainability,
            provenance=provenance,
        )

    def _build_invalid_result(
        self,
        factor_category: FactorCategory,
        record_id: Optional[str],
        raw_value: Any,
        method: NormalizationMethod,
        reason: str,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> NormalizationResult:
        """Construct a strongly typed INVALID result, strictly ensuring normalized_value is None."""
        explainability = NormalizationExplainability(
            method=method,
            parameters_used={"error": reason},
            formula_description="Input rejected due to data or configuration invalidity.",
        )
        return NormalizationResult(
            record_id=record_id,
            factor_category=factor_category,
            status=NormalizationStatus.INVALID,
            raw_input_value=raw_value if isinstance(raw_value, (int, float, str)) else None,
            normalized_value=None,
            was_clamped=False,
            is_unknown_or_unavailable=False,
            diagnostic_message=reason,
            explainability=explainability,
            provenance=provenance,
        )
