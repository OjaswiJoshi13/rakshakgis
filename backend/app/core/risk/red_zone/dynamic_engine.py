"""Dynamic Red Zone & Threshold Trigger Engine (Chunk M3-11).

Real-time and event-driven analytical engine evaluating hazard observations
against regional profile trigger thresholds to identify temporary red zone candidates.
"""

from datetime import datetime
import hashlib
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from shapely.geometry import MultiPolygon, Point, mapping
from shapely.ops import unary_union

from app.core.profiles import get_profile
from app.core.profiles.models import DangerLevel, RegionProfile, RegionProfileId
from app.core.risk.red_zone.contracts import RedZoneType
from app.core.risk.red_zone.dynamic_contracts import (
    ComparisonOperator,
    DynamicHazardIndicator,
    DynamicHazardObservation,
    DynamicRedZoneCandidate,
    DynamicRedZoneExplainability,
    DynamicThresholdConfig,
    DynamicTriggerStatus,
    SingleTriggerEvaluation,
)
from app.core.risk.red_zone.errors import (
    InsufficientGeophysicalDataError,
    InvalidGeophysicalDataError,
    RedZoneConfigError,
    SpatialGeometryError,
)
from app.core.risk.red_zone.geometry import (
    calculate_geodesic_area_sq_km,
    create_geodesic_buffer,
    normalize_to_multipolygon,
)
from app.data.providers.contracts import ProviderProvenance


class DynamicRedZoneEngine:
    """Analytical evaluation engine for Dynamic Red Zones & Threshold Triggers (M3-11).

    Key Invariants:
      1. Zero hardcoded regional constants: All thresholds resolve strictly from RegionProfile.
      2. Strict 3-state evaluation: NO_TRIGGER, TRIGGERED, INSUFFICIENT_DATA.
      3. Missing data safety: Missing/unavailable data strictly returns INSUFFICIENT_DATA (never safe or 0).
      4. Invalid data rejection: NaN, Inf, or out-of-physical-bounds values raise InvalidGeophysicalDataError.
      5. Geometry accuracy: Geodesic circular buffers around point sensors; valid MultiPolygons.
      6. Provenance & Explainability: Complete audit record of observed values, thresholds, operators, and sources.
      7. Governance invariant: Outputs are PROPOSED / CANDIDATE only (is_active=False, declared_by_officer_id=None).
      8. Semantic separation: Dynamic zones have is_temporary=True, preserving distinction from M3-10 permanent zones.
    """

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        threshold_config: Optional[DynamicThresholdConfig] = None,
        buffer_m: Optional[float] = None,
    ) -> None:
        self.profile = profile or get_profile(RegionProfileId.HIMALAYAN_PILOT)

        if threshold_config is not None:
            self.config = threshold_config
        else:
            self.config = DynamicThresholdConfig.from_profile(
                self.profile,
                buffer_distance_m=buffer_m,
            )

        self.buffer_m = self.config.buffer_distance_m
        self.default_danger_level = self.config.default_danger_level

    @classmethod
    def from_profile(
        cls,
        profile_id_or_profile: Union[str, RegionProfile],
        *,
        water_level_trigger_m: Optional[float] = None,
        landslide_debris_volume_trigger_m3: Optional[float] = None,
        buffer_m: Optional[float] = None,
        rainfall_operator: Optional[ComparisonOperator] = None,
        seismic_operator: Optional[ComparisonOperator] = None,
        slope_operator: Optional[ComparisonOperator] = None,
    ) -> "DynamicRedZoneEngine":
        """Factory initializing the engine from a profile ID or instance with optional threshold parameters."""
        if isinstance(profile_id_or_profile, str):
            profile = get_profile(profile_id_or_profile)
        else:
            profile = profile_id_or_profile

        threshold_config = DynamicThresholdConfig.from_profile(
            profile,
            water_level_trigger_m=water_level_trigger_m,
            landslide_debris_volume_trigger_m3=landslide_debris_volume_trigger_m3,
            buffer_distance_m=buffer_m,
            rainfall_operator=rainfall_operator,
            seismic_operator=seismic_operator,
            slope_operator=slope_operator,
        )
        return cls(profile=profile, threshold_config=threshold_config, buffer_m=buffer_m)

    # =========================================================================
    # Single Observation Evaluation
    # =========================================================================

    def evaluate_observation(
        self,
        observation: Union[DynamicHazardObservation, Dict[str, Any], Any],
        village_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        strict: bool = False,
    ) -> DynamicRedZoneCandidate:
        """Evaluate an individual telemetry reading or hazard observation against dynamic thresholds."""
        obs = self._coerce_observation(observation, village_id=village_id, provenance=provenance)

        target_obs_id = obs.observation_id or f"OBS-{hashlib.sha256(str(id(obs)).encode()).hexdigest()[:8]}"
        target_village_id = obs.village_id or "UNKNOWN-VILLAGE"
        target_name = obs.name or obs.village_name or f"Dynamic Zone {target_village_id}"

        src_provenance = (
            [obs.provenance]
            if isinstance(obs.provenance, dict)
            else [obs.provenance.model_dump()]
            if hasattr(obs.provenance, "model_dump")
            else []
        )

        # 1. Missing Data Safety Guard: is_available flag
        if not obs.is_available:
            if strict:
                raise InsufficientGeophysicalDataError(
                    f"Observation '{target_obs_id}' is marked unavailable (is_available=False)."
                )
            audit = SingleTriggerEvaluation(
                indicator=str(obs.indicator or obs.hazard_type or "unknown"),
                observed_value=None,
                configured_threshold=None,
                triggered=False,
                status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                audit_note="Observation is marked unavailable (is_available=False).",
            )
            explainability = DynamicRedZoneExplainability(
                decision_reason="Evaluation yielded INSUFFICIENT_DATA: Observation marked unavailable.",
                summary="Dynamic hazard observation unavailable; cannot evaluate trigger.",
                profile_id=getattr(self.profile, "id", "custom"),
                profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
                if hasattr(self.profile, "metadata")
                else "Custom Profile",
                trigger_evaluations=[audit],
                missing_indicators=["unavailable_observation"],
                source_observation_ids=[target_obs_id],
                source_village_ids=[target_village_id],
                source_provenance=src_provenance,
            )
            return DynamicRedZoneCandidate(
                candidate_id=f"DYN-{target_village_id}-{target_obs_id}",
                name=target_name,
                status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                zone_type=None,
                danger_level=None,
                geometry=None,
                area_sq_km=None,
                buffer_distance_applied_m=None,
                contributing_observation_ids=[target_obs_id],
                contributing_village_ids=[target_village_id],
                is_temporary=True,
                is_candidate=False,
                explainability=explainability,
            )

        # 2. Identify indicator and execute deterministic threshold comparison
        indicator_key, observed_val, thresh_val, op, unit, z_type = self._resolve_indicator_evaluation_params(obs)

        # Check for missing observed value
        if observed_val is None:
            if strict:
                raise InsufficientGeophysicalDataError(
                    f"Missing required numerical observation for indicator '{indicator_key}'."
                )
            audit = SingleTriggerEvaluation(
                indicator=indicator_key,
                observed_value=None,
                configured_threshold=thresh_val,
                operator=op,
                triggered=False,
                status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                unit=unit,
                audit_note=f"Observation data for '{indicator_key}' is missing or null.",
            )
            explainability = DynamicRedZoneExplainability(
                decision_reason=f"Evaluation yielded INSUFFICIENT_DATA: Missing '{indicator_key}' observation value.",
                summary=f"Missing observation value for dynamic indicator '{indicator_key}'.",
                profile_id=getattr(self.profile, "id", "custom"),
                profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
                if hasattr(self.profile, "metadata")
                else "Custom Profile",
                trigger_evaluations=[audit],
                missing_indicators=[indicator_key],
                source_observation_ids=[target_obs_id],
                source_village_ids=[target_village_id],
                source_provenance=src_provenance,
            )
            return DynamicRedZoneCandidate(
                candidate_id=f"DYN-{target_village_id}-{target_obs_id}",
                name=target_name,
                status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                zone_type=None,
                danger_level=None,
                geometry=None,
                area_sq_km=None,
                buffer_distance_applied_m=None,
                contributing_observation_ids=[target_obs_id],
                contributing_village_ids=[target_village_id],
                is_temporary=True,
                is_candidate=False,
                explainability=explainability,
            )

        # Check if threshold is configured for this indicator
        if thresh_val is None:
            if strict:
                raise InsufficientGeophysicalDataError(
                    f"Required dynamic threshold configuration for indicator '{indicator_key}' is unavailable in regional profile.",
                    missing_fields=[f"threshold_for_{indicator_key}"],
                )
            audit = SingleTriggerEvaluation(
                indicator=indicator_key,
                observed_value=observed_val,
                configured_threshold=None,
                operator=op,
                triggered=False,
                status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                unit=unit,
                audit_note=f"Required threshold configuration is unavailable/unconfigured for indicator '{indicator_key}' in regional profile.",
            )
            explainability = DynamicRedZoneExplainability(
                decision_reason=f"INSUFFICIENT_DATA: Required dynamic threshold configuration is unavailable for indicator '{indicator_key}'.",
                summary=f"Indicator '{indicator_key}' observed at {observed_val}{unit or ''}, but required trigger threshold is not configured in regional profile.",
                profile_id=getattr(self.profile, "id", "custom"),
                profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
                if hasattr(self.profile, "metadata")
                else "Custom Profile",
                trigger_evaluations=[audit],
                missing_indicators=[f"threshold_for_{indicator_key}"],
                source_observation_ids=[target_obs_id],
                source_village_ids=[target_village_id],
                source_provenance=src_provenance,
            )
            return DynamicRedZoneCandidate(
                candidate_id=f"DYN-{target_village_id}-{target_obs_id}",
                name=target_name,
                status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                zone_type=None,
                danger_level=None,
                geometry=None,
                area_sq_km=None,
                buffer_distance_applied_m=None,
                contributing_observation_ids=[target_obs_id],
                contributing_village_ids=[target_village_id],
                is_temporary=True,
                is_candidate=False,
                explainability=explainability,
            )

        # 3. Deterministic threshold evaluation
        is_triggered = op.evaluate(observed_val, thresh_val)
        status = DynamicTriggerStatus.TRIGGERED if is_triggered else DynamicTriggerStatus.NO_TRIGGER

        audit_note = (
            f"Observed {observed_val}{unit or ''} {op.value} threshold {thresh_val}{unit or ''} -> "
            f"{'TRIGGER BREACHED' if is_triggered else 'Below trigger threshold'}."
        )

        single_audit = SingleTriggerEvaluation(
            indicator=indicator_key,
            observed_value=observed_val,
            configured_threshold=thresh_val,
            operator=op,
            triggered=is_triggered,
            status=status,
            unit=unit,
            audit_note=audit_note,
        )

        # 4. Spatial geometry derivation
        geom, area_sq_km, applied_buffer_m = self._derive_spatial_geometry(obs)

        # 5. Build explainability audit trail
        if is_triggered:
            decision_reason = (
                f"TRIGGERED: Observed {indicator_key} ({observed_val}{unit or ''}) breached configured threshold "
                f"({op.value} {thresh_val}{unit or ''}). Candidate dynamic red zone demarcated."
            )
            summary = (
                f"Dynamic hazard trigger breached: {indicator_key} reached {observed_val}{unit or ''} "
                f"(threshold: {thresh_val}{unit or ''})."
            )
            triggered_indicators = [indicator_key]
            danger_level = self.default_danger_level
            zone_type = z_type
        else:
            decision_reason = (
                f"NO_TRIGGER: Observed {indicator_key} ({observed_val}{unit or ''}) does not breach configured threshold "
                f"({op.value} {thresh_val}{unit or ''})."
            )
            summary = (
                f"Dynamic hazard conditions safe: {indicator_key} at {observed_val}{unit or ''} "
                f"(threshold: {thresh_val}{unit or ''})."
            )
            triggered_indicators = []
            danger_level = None
            zone_type = None

        explainability = DynamicRedZoneExplainability(
            decision_reason=decision_reason,
            summary=summary,
            profile_id=getattr(self.profile, "id", "custom"),
            profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
            if hasattr(self.profile, "metadata")
            else "Custom Profile",
            trigger_evaluations=[single_audit],
            triggered_indicators=triggered_indicators,
            missing_indicators=[],
            source_observation_ids=[target_obs_id],
            source_village_ids=[target_village_id],
            source_provenance=src_provenance,
            buffer_applied_m=applied_buffer_m,
        )

        return DynamicRedZoneCandidate(
            candidate_id=f"DYN-{target_village_id}-{target_obs_id}",
            name=target_name,
            status=status,
            zone_type=zone_type,
            danger_level=danger_level,
            geometry=geom if is_triggered else None,
            area_sq_km=area_sq_km if is_triggered else None,
            buffer_distance_applied_m=applied_buffer_m if is_triggered else None,
            contributing_observation_ids=[target_obs_id],
            contributing_village_ids=[target_village_id],
            is_temporary=True,
            is_candidate=is_triggered,
            explainability=explainability,
        )

    # =========================================================================
    # Multi-Observation Evaluation for a Village / Location
    # =========================================================================

    def evaluate_village_observations(
        self,
        observations: Sequence[Union[DynamicHazardObservation, Dict[str, Any], Any]],
        village_id: Optional[str] = None,
        location: Optional[Any] = None,
        geometry: Optional[Any] = None,
        village_name: Optional[str] = None,
        strict: bool = False,
    ) -> DynamicRedZoneCandidate:
        """Evaluate a set of concurrent telemetry observations for a settlement or monitoring zone.

        Preserves all contributing observations, provenance, and evaluates compound triggers.
        """
        if not observations:
            if strict:
                raise InsufficientGeophysicalDataError("No observations provided for village evaluation.")
            explainability = DynamicRedZoneExplainability(
                decision_reason="Evaluation yielded INSUFFICIENT_DATA: Observation list is empty.",
                summary="Zero observations provided for dynamic threshold evaluation.",
                profile_id=getattr(self.profile, "id", "custom"),
                profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
                if hasattr(self.profile, "metadata")
                else "Custom Profile",
                missing_indicators=["hazard_observations"],
                source_village_ids=[village_id] if village_id else [],
            )
            return DynamicRedZoneCandidate(
                candidate_id=f"DYN-{village_id or 'UNKNOWN'}",
                name=village_name or f"Dynamic Zone {village_id or 'UNKNOWN'}",
                status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                zone_type=None,
                danger_level=None,
                geometry=None,
                contributing_observation_ids=[],
                contributing_village_ids=[village_id] if village_id else [],
                is_temporary=True,
                is_candidate=False,
                explainability=explainability,
            )

        evaluated_audits: List[SingleTriggerEvaluation] = []
        triggered_indicators: List[str] = []
        missing_indicators: List[str] = []
        obs_ids: List[str] = []
        village_ids: List[str] = [village_id] if village_id else []
        all_provenance: List[Dict[str, Any]] = []
        trigger_types: List[RedZoneType] = []

        has_triggered = False
        has_insufficient_data = False

        # Evaluate individual observations
        for item in observations:
            res = self.evaluate_observation(item, village_id=village_id, strict=strict)
            obs_ids.extend(res.contributing_observation_ids)
            for vid in res.contributing_village_ids:
                if vid not in village_ids:
                    village_ids.append(vid)

            all_provenance.extend(res.explainability.source_provenance)
            evaluated_audits.extend(res.explainability.trigger_evaluations)
            missing_indicators.extend(res.explainability.missing_indicators)

            if res.status == DynamicTriggerStatus.TRIGGERED:
                has_triggered = True
                triggered_indicators.extend(res.explainability.triggered_indicators)
                if res.zone_type and res.zone_type not in trigger_types:
                    trigger_types.append(res.zone_type)
            elif res.status == DynamicTriggerStatus.INSUFFICIENT_DATA:
                has_insufficient_data = True

        # Check for compound slope trigger if both rainfall and slope observations are present
        compound_result = self._check_compound_slope_trigger(observations)
        if compound_result is not None:
            comp_audit, comp_triggered = compound_result
            evaluated_audits.append(comp_audit)
            if comp_triggered:
                has_triggered = True
                if "compound_rainfall_slope" not in triggered_indicators:
                    triggered_indicators.append("compound_rainfall_slope")
                if RedZoneType.COMPOUND_DANGER not in trigger_types:
                    trigger_types.append(RedZoneType.COMPOUND_DANGER)
            elif comp_audit.status == DynamicTriggerStatus.INSUFFICIENT_DATA:
                has_insufficient_data = True
                missing_indicators.append("threshold_for_compound_rainfall_slope")

        # Determine overall status:
        # 1. Any trigger -> TRIGGERED (safety priority)
        # 2. No trigger but missing data -> INSUFFICIENT_DATA (never assume safe when data is missing)
        # 3. All evaluated and safe -> NO_TRIGGER
        if has_triggered:
            overall_status = DynamicTriggerStatus.TRIGGERED
            danger_level = self.default_danger_level
            if len(trigger_types) > 1:
                zone_type = RedZoneType.COMPOUND_DANGER
            elif trigger_types:
                zone_type = trigger_types[0]
            else:
                zone_type = RedZoneType.COMPOUND_DANGER
        elif has_insufficient_data:
            overall_status = DynamicTriggerStatus.INSUFFICIENT_DATA
            danger_level = None
            zone_type = None
        else:
            overall_status = DynamicTriggerStatus.NO_TRIGGER
            danger_level = None
            zone_type = None

        # Derive geometry from explicitly supplied village location/geometry or first available observation
        geom: Optional[MultiPolygon] = None
        area_sq_km: Optional[float] = None
        applied_buffer_m: Optional[float] = None

        if overall_status == DynamicTriggerStatus.TRIGGERED:
            if geometry is not None:
                geom = normalize_to_multipolygon(geometry)
                area_sq_km = calculate_geodesic_area_sq_km(geom)
            elif location is not None:
                if isinstance(location, Point):
                    pt = location
                elif isinstance(location, (list, tuple)) and len(location) >= 2:
                    pt = Point(float(location[0]), float(location[1]))
                elif isinstance(location, dict) and "coordinates" in location:
                    pt = Point(float(location["coordinates"][0]), float(location["coordinates"][1]))
                else:
                    pt = location
                geom = create_geodesic_buffer(pt, buffer_distance_m=self.buffer_m)
                area_sq_km = calculate_geodesic_area_sq_km(geom)
                applied_buffer_m = self.buffer_m
            else:
                # Try finding geometry from individual observations
                for obs_item in observations:
                    coerced = self._coerce_observation(obs_item)
                    g, a, b = self._derive_spatial_geometry(coerced)
                    if g is not None:
                        geom = g
                        area_sq_km = a
                        applied_buffer_m = b
                        break

        # Construct explainability
        if overall_status == DynamicTriggerStatus.TRIGGERED:
            decision_reason = (
                f"TRIGGERED: {len(triggered_indicators)} dynamic hazard indicator(s) breached threshold: "
                f"{', '.join(triggered_indicators)}. Candidate dynamic red zone demarcated."
            )
            summary = f"Dynamic hazard triggers breached across indicators: {', '.join(triggered_indicators)}."
        elif overall_status == DynamicTriggerStatus.INSUFFICIENT_DATA:
            decision_reason = (
                f"INSUFFICIENT_DATA: Missing required observation data or threshold configuration for: {', '.join(set(missing_indicators))}."
            )
            summary = "Incomplete telemetry observations or unavailable trigger threshold configuration; dynamic trigger status cannot be safely established."
        else:
            decision_reason = "NO_TRIGGER: All evaluated hazard indicators remain strictly below regional trigger thresholds."
            summary = "All real-time hazard observations are within configured regional safety thresholds."

        explainability = DynamicRedZoneExplainability(
            decision_reason=decision_reason,
            summary=summary,
            profile_id=getattr(self.profile, "id", "custom"),
            profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
            if hasattr(self.profile, "metadata")
            else "Custom Profile",
            trigger_evaluations=evaluated_audits,
            triggered_indicators=list(set(triggered_indicators)),
            missing_indicators=list(set(missing_indicators)),
            source_observation_ids=list(set(obs_ids)),
            source_village_ids=village_ids,
            source_provenance=all_provenance,
            buffer_applied_m=applied_buffer_m,
        )

        return DynamicRedZoneCandidate(
            candidate_id=f"DYN-{village_id or 'ZONE'}-{hashlib.sha256(str(obs_ids).encode()).hexdigest()[:8]}",
            name=village_name or f"Dynamic Zone {village_id or 'Settlement'}",
            status=overall_status,
            zone_type=zone_type,
            danger_level=danger_level,
            geometry=geom,
            area_sq_km=area_sq_km,
            buffer_distance_applied_m=applied_buffer_m,
            contributing_observation_ids=list(set(obs_ids)),
            contributing_village_ids=village_ids,
            is_temporary=True,
            is_candidate=(overall_status == DynamicTriggerStatus.TRIGGERED),
            explainability=explainability,
        )

    # =========================================================================
    # Overlap Resolution & Dissolution
    # =========================================================================

    def dissolve_overlapping_dynamic_zones(
        self,
        candidates: Sequence[DynamicRedZoneCandidate],
        *,
        default_danger_level: Optional[DangerLevel] = None,
    ) -> List[DynamicRedZoneCandidate]:
        """Dissolve overlapping dynamic candidate perimeters into unified zones.

        Preserves all contributing observations, village IDs, and provenance records.
        Strictly adheres to DangerLevel invariants: never invents unapproved danger levels.
        """
        # Filter for candidates with valid geometries that are in TRIGGERED status
        active_candidates = [
            c for c in candidates if c.status == DynamicTriggerStatus.TRIGGERED and c.geometry is not None
        ]
        non_dissolvable = [
            c for c in candidates if c.status != DynamicTriggerStatus.TRIGGERED or c.geometry is None
        ]

        if not active_candidates:
            return list(candidates)

        # Spatial cluster grouping via intersection graph
        clusters: List[List[DynamicRedZoneCandidate]] = []
        for cand in active_candidates:
            geom = cand.geometry
            matched_clusters = []
            for cluster in clusters:
                if any(geom.intersects(c.geometry) for c in cluster):
                    matched_clusters.append(cluster)

            if not matched_clusters:
                clusters.append([cand])
            elif len(matched_clusters) == 1:
                matched_clusters[0].append(cand)
            else:
                merged: List[DynamicRedZoneCandidate] = [cand]
                for c in matched_clusters:
                    merged.extend(c)
                    clusters.remove(c)
                clusters.append(merged)

        results: List[DynamicRedZoneCandidate] = list(non_dissolvable)

        for cluster in clusters:
            if len(cluster) == 1:
                results.append(cluster[0])
                continue

            # Union overlapping geometries
            polys = [c.geometry for c in cluster]
            union_geom = unary_union(polys)
            norm_geom = normalize_to_multipolygon(union_geom)
            area_sq_km = calculate_geodesic_area_sq_km(norm_geom)

            # Aggregate provenance, IDs, and trigger audits
            all_obs_ids: List[str] = []
            all_vids: List[str] = []
            all_provenance: List[Dict[str, Any]] = []
            all_audits: List[SingleTriggerEvaluation] = []
            all_triggered: List[str] = []
            zone_types: List[RedZoneType] = []

            for c in cluster:
                all_obs_ids.extend(c.contributing_observation_ids)
                all_vids.extend(c.contributing_village_ids)
                all_provenance.extend(c.explainability.source_provenance)
                all_audits.extend(c.explainability.trigger_evaluations)
                all_triggered.extend(c.explainability.triggered_indicators)
                if c.zone_type and c.zone_type not in zone_types:
                    zone_types.append(c.zone_type)

            dedup_obs_ids = sorted(list(set(all_obs_ids)))
            dedup_vids = sorted(list(set(all_vids)))
            dedup_triggered = sorted(list(set(all_triggered)))

            # Resolved DangerLevel: use explicit default, or existing danger level from cluster
            resolved_danger_level = (
                default_danger_level
                or cluster[0].danger_level
                or self.default_danger_level
            )

            # Zone type: compound if multiple types present
            dissolved_zone_type = (
                RedZoneType.COMPOUND_DANGER
                if len(zone_types) > 1
                else zone_types[0]
                if zone_types
                else RedZoneType.COMPOUND_DANGER
            )

            dissolved_explainability = DynamicRedZoneExplainability(
                decision_reason=(
                    f"DISSOLVED: Contiguous dynamic exclusion zone created from {len(cluster)} overlapping candidate zones. "
                    f"Contributing triggers: {', '.join(dedup_triggered)}."
                ),
                summary=f"Unified dynamic hazard zone encompassing {len(dedup_vids)} settlement(s).",
                profile_id=getattr(self.profile, "id", "custom"),
                profile_name=getattr(self.profile.metadata, "name", "Custom Profile")
                if hasattr(self.profile, "metadata")
                else "Custom Profile",
                trigger_evaluations=all_audits,
                triggered_indicators=dedup_triggered,
                missing_indicators=[],
                source_observation_ids=dedup_obs_ids,
                source_village_ids=dedup_vids,
                source_provenance=all_provenance,
                is_dissolved=True,
                dissolved_count=len(cluster),
            )

            dissolved_candidate = DynamicRedZoneCandidate(
                candidate_id=f"DYN-DISSOLVED-{hashlib.sha256('-'.join(dedup_obs_ids).encode()).hexdigest()[:8]}",
                name=f"Contiguous Dynamic Hazard Perimeter ({len(dedup_vids)} settlements)",
                status=DynamicTriggerStatus.TRIGGERED,
                zone_type=dissolved_zone_type,
                danger_level=resolved_danger_level,
                geometry=norm_geom,
                area_sq_km=area_sq_km,
                buffer_distance_applied_m=cluster[0].buffer_distance_applied_m,
                contributing_observation_ids=dedup_obs_ids,
                contributing_village_ids=dedup_vids,
                is_temporary=True,
                is_candidate=True,
                explainability=dissolved_explainability,
            )
            results.append(dissolved_candidate)

        return results

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _coerce_observation(
        self,
        observation: Union[DynamicHazardObservation, Dict[str, Any], Any],
        village_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
    ) -> DynamicHazardObservation:
        """Coerce heterogeneous hazard observation inputs into a validated DynamicHazardObservation."""
        if isinstance(observation, DynamicHazardObservation):
            if village_id and not observation.village_id:
                observation.village_id = village_id
            if provenance and not observation.provenance:
                observation.provenance = provenance
            return observation

        if isinstance(observation, dict):
            data = dict(observation)
            if village_id and not data.get("village_id"):
                data["village_id"] = village_id
            if provenance and not data.get("provenance"):
                data["provenance"] = provenance
            return DynamicHazardObservation(**data)

        # Object attribute extraction (e.g. NormalizedRainfallRecord, NormalizedFloodRecord, HazardObservation)
        data = {
            "observation_id": getattr(
                observation,
                "observation_id",
                getattr(observation, "record_id", getattr(observation, "id", None)),
            ),
            "village_id": getattr(observation, "village_id", village_id),
            "village_name": getattr(observation, "village_name", getattr(observation, "name", None)),
            "hazard_type": getattr(observation, "hazard_type", None),
            "rainfall_24h_mm": getattr(observation, "rainfall_24h_mm", None),
            "water_level_m_above_danger": getattr(observation, "water_level_m_above_danger", None),
            "debris_volume_cu_m": getattr(observation, "debris_volume_cu_m", None),
            "seismic_intensity_mmi": getattr(observation, "seismic_intensity_mmi", None),
            "observed_value": getattr(observation, "observed_value", getattr(observation, "intensity_value", None)),
            "unit": getattr(observation, "unit", getattr(observation, "intensity_unit", None)),
            "location": getattr(observation, "location", getattr(observation, "location_coordinates", None)),
            "geometry": getattr(observation, "geometry", getattr(observation, "inundation_polygon", None)),
            "observed_at": getattr(observation, "observed_at", getattr(observation, "event_date", None)),
            "is_available": getattr(observation, "is_available", True),
            "provenance": getattr(observation, "provenance", provenance),
        }
        return DynamicHazardObservation(**data)

    def _resolve_indicator_evaluation_params(
        self,
        obs: DynamicHazardObservation,
    ) -> Tuple[str, Optional[float], Optional[float], ComparisonOperator, Optional[str], RedZoneType]:
        """Resolve indicator key, observed value, configured threshold, operator, unit, and zone type."""
        ind = obs.indicator
        h_type = (obs.hazard_type or "").lower().strip()

        # 1. Rainfall
        if ind == DynamicHazardIndicator.RAINFALL_24H or h_type == "rainfall" or obs.rainfall_24h_mm is not None:
            val = obs.rainfall_24h_mm if obs.rainfall_24h_mm is not None else obs.observed_value
            thresh = self.config.rainfall_trigger_24h_mm
            op = self.config.rainfall_operator
            return "rainfall_24h", val, thresh, op, "mm", RedZoneType.FLOOD_INUNDATION

        # 2. Seismic
        if ind == DynamicHazardIndicator.SEISMIC_MMI or h_type == "seismic" or obs.seismic_intensity_mmi is not None:
            val = obs.seismic_intensity_mmi if obs.seismic_intensity_mmi is not None else obs.observed_value
            thresh = self.config.seismic_trigger_mmi
            op = self.config.seismic_operator
            return "seismic_mmi", val, thresh, op, "MMI", RedZoneType.ACTIVE_SUBSIDENCE

        # 3. Water level / Flood
        if (
            ind == DynamicHazardIndicator.WATER_LEVEL_ABOVE_DANGER
            or h_type in ("flood", "flash_flood")
            or obs.water_level_m_above_danger is not None
        ):
            val = obs.water_level_m_above_danger if obs.water_level_m_above_danger is not None else obs.observed_value
            thresh = self.config.water_level_trigger_m_above_danger
            op = self.config.water_level_operator
            return "water_level_above_danger", val, thresh, op, "m", RedZoneType.FLOOD_INUNDATION

        # 4. Landslide
        if (
            ind in (DynamicHazardIndicator.LANDSLIDE_DEBRIS_VOLUME, DynamicHazardIndicator.LANDSLIDE_ACTIVITY)
            or h_type == "landslide"
            or obs.debris_volume_cu_m is not None
        ):
            val = obs.debris_volume_cu_m if obs.debris_volume_cu_m is not None else obs.observed_value
            thresh = self.config.landslide_debris_volume_trigger_m3
            op = self.config.landslide_operator
            return "landslide_debris_volume", val, thresh, op, "m3", RedZoneType.LANDSLIDE_DANGER

        # 5. Slope
        if ind == DynamicHazardIndicator.SLOPE_DEG or h_type == "slope" or obs.slope_deg is not None:
            val = obs.slope_deg if obs.slope_deg is not None else obs.observed_value
            thresh = self.config.slope_trigger_min_deg
            op = self.config.slope_operator
            return "slope_deg", val, thresh, op, "deg", RedZoneType.LANDSLIDE_DANGER

        # Generic fallback
        key = str(ind or h_type or "hazard_observation")
        return key, obs.observed_value, None, ComparisonOperator.GREATER_THAN_OR_EQUAL, obs.unit, RedZoneType.COMPOUND_DANGER

    def _derive_spatial_geometry(
        self,
        obs: DynamicHazardObservation,
    ) -> Tuple[Optional[MultiPolygon], Optional[float], Optional[float]]:
        """Derive valid MultiPolygon geometry and calculate area; returns None if geometry cannot be safely derived."""
        # 1. Polygonal geometry
        if obs.geometry is not None:
            try:
                poly = normalize_to_multipolygon(obs.geometry)
                area = calculate_geodesic_area_sq_km(poly)
                return poly, area, None
            except SpatialGeometryError:
                raise
            except Exception as e:
                raise SpatialGeometryError(f"Failed to normalize polygon geometry for observation: {e}") from e

        # 2. Point location
        if obs.location is not None:
            try:
                if isinstance(obs.location, Point):
                    pt = obs.location
                elif isinstance(obs.location, (list, tuple)) and len(obs.location) >= 2:
                    pt = Point(float(obs.location[0]), float(obs.location[1]))
                elif isinstance(obs.location, dict) and "coordinates" in obs.location:
                    coords = obs.location["coordinates"]
                    pt = Point(float(coords[0]), float(coords[1]))
                else:
                    raise SpatialGeometryError(f"Unrecognized location structure: {obs.location}")

                poly = create_geodesic_buffer(pt, buffer_distance_m=self.buffer_m)
                area = calculate_geodesic_area_sq_km(poly)
                return poly, area, self.buffer_m
            except SpatialGeometryError:
                raise
            except Exception as e:
                raise SpatialGeometryError(f"Failed to compute geodesic buffer for observation point: {e}") from e

        # No spatial representation available
        return None, None, None

    def _check_compound_slope_trigger(
        self,
        observations: Sequence[Union[DynamicHazardObservation, Dict[str, Any], Any]],
    ) -> Optional[Tuple[SingleTriggerEvaluation, bool]]:
        """Check for compound hazard conditions: e.g. Rainfall exceeding trigger combined with steep slope."""
        rainfall_val: Optional[float] = None
        slope_val: Optional[float] = None

        for item in observations:
            obs = self._coerce_observation(item)
            if obs.rainfall_24h_mm is not None:
                rainfall_val = obs.rainfall_24h_mm
            elif obs.hazard_type == "rainfall" and obs.observed_value is not None:
                rainfall_val = obs.observed_value

            if obs.slope_deg is not None:
                slope_val = obs.slope_deg
            elif obs.hazard_type == "slope" and obs.observed_value is not None:
                slope_val = obs.observed_value

        if rainfall_val is not None and slope_val is not None:
            rain_thresh = self.config.rainfall_trigger_24h_mm
            slope_thresh = self.config.slope_trigger_min_deg
            rain_op = self.config.rainfall_operator
            slope_op = self.config.slope_operator

            if rain_thresh is None or slope_thresh is None:
                missing = []
                if rain_thresh is None:
                    missing.append("threshold_for_rainfall_24h")
                if slope_thresh is None:
                    missing.append("threshold_for_slope_deg")
                audit_note = (
                    f"Compound Rainfall-Slope: Required threshold configuration is unavailable ({', '.join(missing)})."
                )
                audit = SingleTriggerEvaluation(
                    indicator="compound_rainfall_slope",
                    observed_value=rainfall_val,
                    configured_threshold=None,
                    operator=rain_op,
                    triggered=False,
                    status=DynamicTriggerStatus.INSUFFICIENT_DATA,
                    audit_note=audit_note,
                )
                return audit, False

            rain_triggered = rain_op.evaluate(rainfall_val, rain_thresh)
            slope_triggered = slope_op.evaluate(slope_val, slope_thresh)

            compound_triggered = rain_triggered and slope_triggered
            status = DynamicTriggerStatus.TRIGGERED if compound_triggered else DynamicTriggerStatus.NO_TRIGGER
            audit_note = (
                f"Compound Rainfall-Slope: Rain {rainfall_val}mm ({rain_op.value} {rain_thresh}mm: {rain_triggered}) "
                f"AND Slope {slope_val}deg ({slope_op.value} {slope_thresh}deg: {slope_triggered}) -> "
                f"{'TRIGGERED' if compound_triggered else 'NO_TRIGGER'}."
            )
            audit = SingleTriggerEvaluation(
                indicator="compound_rainfall_slope",
                observed_value=rainfall_val,
                configured_threshold=rain_thresh,
                operator=rain_op,
                triggered=compound_triggered,
                status=status,
                audit_note=audit_note,
            )
            return audit, compound_triggered

        return None
