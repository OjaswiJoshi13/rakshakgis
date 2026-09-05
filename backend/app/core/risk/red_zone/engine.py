"""Permanent Red Zone Demarcation Engine (Chunk M3-10).

Analytical engine identifying candidate/proposed permanent red zones based on
authoritative regional geophysical profiles, subsidence observations, and composite risk corroboration.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from shapely.geometry import MultiPolygon, Point, mapping

from app.core.profiles import get_profile
from app.core.profiles.models import DangerLevel, RegionProfile, RegionProfileId
from app.core.risk.classification.contracts import RiskBand
from app.core.risk.red_zone.contracts import (
    GeophysicalObservationInput,
    PermanentRedZoneCandidate,
    PermanentRedZoneExplainability,
    RedZoneStatus,
    RedZoneType,
    TriggerAudit,
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
    dissolve_overlapping_candidates,
    normalize_to_multipolygon,
)
from app.data.providers.contracts import ProviderProvenance


class PermanentRedZoneEngine:
    """Analytical candidate evaluation engine for Permanent Red Zone Demarcation (M3-10).

    Formalized Rules (Option 1):
      1. Trigger: active_subsidence == True OR (slope_deg >= min_slope_deg AND historical_landslides >= min_historical_landslides).
      2. Upstream Risk Integration:
         - CRITICAL corroborates the candidate.
         - SAFE or MODERATE + steep slope without active subsidence -> designated as MONITOR rather than red zone.
      3. Point Buffering: Point-based village locations are buffered with a geodesic circle of hazard_buffer_m.
      4. Overlap Dissolve: Continuous high-risk areas are dissolved preserving full provenance and village IDs.
      5. Missing Data Safety: Missing required indicators strictly yield INSUFFICIENT_DATA (never defaulted to safe or 0).
      6. Governance Invariant: Outputs are PROPOSED / CANDIDATE only (is_active=False, declared_by_officer_id=None).
    """

    def __init__(
        self,
        profile: Optional[RegionProfile] = None,
        buffer_m: Optional[float] = None,
    ) -> None:
        self.profile = profile or get_profile(RegionProfileId.HIMALAYAN_PILOT)

        # Extract criteria from regional profile
        try:
            if hasattr(self.profile, "red_zone_thresholds") and hasattr(self.profile.red_zone_thresholds, "permanent_criteria"):
                prz_criteria = self.profile.red_zone_thresholds.permanent_criteria
            elif hasattr(self.profile, "permanent_red_zone_criteria"):
                prz_criteria = self.profile.permanent_red_zone_criteria
            else:
                raise AttributeError("RegionProfile missing red_zone_thresholds.permanent_criteria")

            self.min_slope_deg: float = float(prz_criteria.min_slope_deg)
            self.min_historical_landslides: int = int(prz_criteria.min_historical_landslides)
            self.active_subsidence_triggers: bool = bool(
                getattr(prz_criteria, "active_subsidence_triggers_permanent", getattr(prz_criteria, "active_subsidence_triggers", True))
            )
            self.default_danger_level: DangerLevel = getattr(prz_criteria, "default_danger_level", DangerLevel.UNINHABITABLE)
        except Exception as e:
            raise RedZoneConfigError(f"Failed to load permanent red zone criteria from profile: {e}") from e

        # Extract buffer distance from profile if not explicitly overridden
        if buffer_m is not None:
            if buffer_m <= 0.0:
                raise RedZoneConfigError(f"buffer_m must be strictly positive, got {buffer_m}.")
            self.buffer_m: float = float(buffer_m)
        else:
            try:
                self.buffer_m = float(self.profile.site_capacity_assumptions.hazard_buffer_m)
            except Exception:
                self.buffer_m = 500.0  # Fallback to Himalayan pilot 500m specification

    @classmethod
    def from_profile(
        cls,
        profile_id_or_profile: Union[str, RegionProfile],
        buffer_m: Optional[float] = None,
    ) -> "PermanentRedZoneEngine":
        """Factory initializing the engine from a profile ID or instance."""
        if isinstance(profile_id_or_profile, str):
            profile = get_profile(profile_id_or_profile)
        else:
            profile = profile_id_or_profile
        return cls(profile=profile, buffer_m=buffer_m)

    # =====================================================================
    # Single Settlement Evaluation
    # =====================================================================

    def evaluate_village(
        self,
        input_data: Union[
            GeophysicalObservationInput,
            Dict[str, Any],
            Any,
        ],
        village_id: Optional[str] = None,
        provenance: Optional[Union[ProviderProvenance, Dict[str, Any]]] = None,
        strict: bool = False,
    ) -> PermanentRedZoneCandidate:
        """Evaluate a single settlement / location for Permanent Red Zone candidate status."""
        obs = self._coerce_observation_input(input_data, village_id=village_id, provenance=provenance)

        target_id = obs.village_id or "UNKNOWN-VILLAGE"
        target_name = obs.name or obs.village_name or target_id
        src_provenance = [obs.provenance] if isinstance(obs.provenance, dict) else (
            [obs.provenance.model_dump()] if hasattr(obs.provenance, "model_dump") else []
        )

        # 1. Missing Data Safety Check
        # If active_subsidence is explicitly True, it qualifies immediately.
        # Otherwise, we MUST evaluate slope and historical landslide count.
        is_subsidence_true = obs.active_subsidence is True

        missing_indicators: List[str] = []
        if not is_subsidence_true:
            if obs.slope_deg is None:
                missing_indicators.append("slope_deg")
            if obs.historical_landslide_count is None:
                missing_indicators.append("historical_landslide_count")
            if obs.active_subsidence is None:
                missing_indicators.append("active_subsidence")

        if missing_indicators:
            if strict:
                raise InsufficientGeophysicalDataError(
                    f"Missing required geophysical indicators for village {target_id}: {missing_indicators}",
                    missing_fields=missing_indicators,
                )

            # Safety Invariant: missing data is never assumed safe
            trigger_summary = (
                f"Missing required geophysical indicator(s): {missing_indicators}. "
                "Safety policy strictly forbids interpreting missing data as safe."
            )
            trigger_audit = TriggerAudit(
                village_id=target_id,
                active_subsidence_triggered=False,
                compound_landslide_triggered=False,
                compound_hazard_triggered=False,
                slope_threshold_deg=self.min_slope_deg,
                observed_slope_deg=obs.slope_deg,
                slope_threshold_met=False,
                landslide_threshold_count=self.min_historical_landslides,
                observed_landslide_count=obs.historical_landslide_count,
                historical_landslides_threshold_met=False,
                active_subsidence_observed=obs.active_subsidence,
                risk_corroboration=None,
                risk_band_corroborated=False,
                missing_indicators=missing_indicators,
            )
            explainability = PermanentRedZoneExplainability(
                decision_reason=trigger_summary,
                trigger_summary=trigger_summary,
                trigger_audit=trigger_audit,
                trigger_audits=[trigger_audit],
                active_subsidence_triggered=False,
                compound_hazard_triggered=False,
                slope_threshold_met=False,
                historical_landslides_threshold_met=False,
                risk_band_corroborated=False,
                monitoring_recommended=False,
                missing_required_indicators=missing_indicators,
                source_village_ids=[target_id],
                source_village_provenance={target_id: src_provenance[0]} if src_provenance else {},
                source_provenance=src_provenance,
                is_dissolved=False,
                dissolved_zone_count=1,
                profile_id=self.profile.metadata.id.value if hasattr(self.profile.metadata.id, "value") else str(self.profile.metadata.id),
                buffer_applied_m=None,
            )
            return PermanentRedZoneCandidate(
                candidate_id=f"PRZ-CAND-{target_id}",
                zone_id=f"PRZ-CAND-{target_id}",
                name=f"Permanent Red Zone Candidate ({target_name})",
                status=RedZoneStatus.INSUFFICIENT_DATA,
                zone_type=None,
                danger_level=None,
                geometry=None,
                srid=4326,
                area_sq_km=None,
                buffer_distance_applied_m=None,
                contributing_village_ids=[target_id],
                is_candidate=False,
                is_active=False,
                declared_by_officer_id=None,
                declared_at=None,
                explainability=explainability,
                metadata_json={"missing_indicators": missing_indicators},
            )

        # 2. Evaluate Geophysical Triggers
        subsidence_triggered = bool(obs.active_subsidence and self.active_subsidence_triggers)
        slope_threshold_met = bool(obs.slope_deg is not None and obs.slope_deg >= self.min_slope_deg)
        landslides_threshold_met = bool(
            obs.historical_landslide_count is not None
            and obs.historical_landslide_count >= self.min_historical_landslides
        )
        compound_landslide_triggered = slope_threshold_met and landslides_threshold_met

        geophysical_breach = subsidence_triggered or compound_landslide_triggered

        # 3. Check Risk Classification Corroboration & Monitoring Rule
        risk_band_val = obs.upstream_risk_band or obs.risk_band
        risk_band_str = None
        if risk_band_val is not None:
            risk_band_str = risk_band_val.value if hasattr(risk_band_val, "value") else str(risk_band_val).upper()

        risk_corroboration = None
        risk_corroborated = False
        if risk_band_str:
            if risk_band_str == RiskBand.CRITICAL.value or risk_band_str == "CRITICAL":
                risk_corroboration = "Corroborated by upstream composite risk classification CRITICAL."
                risk_corroborated = True
            else:
                risk_corroboration = f"Evaluated under composite risk band: {risk_band_str}."

        # Rule: SAFE or MODERATE combined with steep slope WITHOUT active subsidence -> MONITOR
        is_safe_or_moderate = risk_band_str in (RiskBand.SAFE.value, RiskBand.MODERATE.value, "SAFE", "MODERATE")
        is_monitor_override = (
            compound_landslide_triggered
            and not subsidence_triggered
            and is_safe_or_moderate
        )

        # 4. Resolve Decision Status & Threat Classification
        if is_monitor_override:
            status = RedZoneStatus.MONITOR
            zone_type = RedZoneType.LANDSLIDE_DANGER
            danger_level = None
            is_candidate = False
            decision_reason = (
                f"Steep slope ({obs.slope_deg:.1f}°) and landslide history ({obs.historical_landslide_count}) "
                f"detected, but classified under {risk_band_str} composite risk without active subsidence; "
                "downgraded from proposed red zone to MONITOR status."
            )
        elif geophysical_breach:
            status = RedZoneStatus.PROPOSED
            is_candidate = True
            # Danger level is strictly the profile-configured default (no unapproved per-trigger mappings)
            danger_level = self.default_danger_level

            if subsidence_triggered and compound_landslide_triggered:
                zone_type = RedZoneType.COMPOUND_DANGER
                decision_reason = (
                    f"Breached compound criteria: active ground subsidence confirmed AND "
                    f"slope ({obs.slope_deg:.1f}°) >= threshold ({self.min_slope_deg:.1f}°) with "
                    f"historical landslides ({obs.historical_landslide_count}) >= {self.min_historical_landslides}."
                )
            elif subsidence_triggered:
                zone_type = RedZoneType.ACTIVE_SUBSIDENCE
                decision_reason = "Active ground subsidence and fissure propagation confirmed."
            else:
                zone_type = RedZoneType.LANDSLIDE_DANGER
                decision_reason = (
                    f"Steep slope ({obs.slope_deg:.1f}°) >= threshold ({self.min_slope_deg:.1f}°) AND "
                    f"historical landslides ({obs.historical_landslide_count}) >= {self.min_historical_landslides}."
                )

            if risk_corroborated:
                decision_reason += " Corroborated by upstream composite risk classification CRITICAL."
        else:
            status = RedZoneStatus.NOT_DEMARCATED
            zone_type = None
            danger_level = None
            is_candidate = False
            decision_reason = (
                f"Geophysical criteria not breached (slope={obs.slope_deg}° < {self.min_slope_deg}° or "
                f"historical landslides={obs.historical_landslide_count} < {self.min_historical_landslides}, "
                "and no active subsidence detected)."
            )

        # 5. Spatial Geometry Generation
        mp_geom: Optional[MultiPolygon] = None
        area_sq_km: Optional[float] = None
        buffer_applied: Optional[float] = None

        if status in (RedZoneStatus.PROPOSED, RedZoneStatus.MONITOR):
            mp_geom = self._resolve_geometry(obs)
            if mp_geom is not None:
                area_sq_km = calculate_geodesic_area_sq_km(mp_geom)
                is_point = (
                    obs.location is not None
                    or (obs.location_geometry is not None and hasattr(obs.location_geometry, "geom_type") and obs.location_geometry.geom_type == "Point")
                    or (obs.geometry is not None and hasattr(obs.geometry, "geom_type") and obs.geometry.geom_type == "Point")
                )
                if is_point:
                    buffer_applied = self.buffer_m

        trigger_audit = TriggerAudit(
            village_id=target_id,
            active_subsidence_triggered=subsidence_triggered,
            compound_landslide_triggered=compound_landslide_triggered,
            compound_hazard_triggered=compound_landslide_triggered,
            slope_threshold_deg=self.min_slope_deg,
            observed_slope_deg=obs.slope_deg,
            slope_threshold_met=slope_threshold_met,
            landslide_threshold_count=self.min_historical_landslides,
            observed_landslide_count=obs.historical_landslide_count,
            historical_landslides_threshold_met=landslides_threshold_met,
            active_subsidence_observed=obs.active_subsidence,
            risk_corroboration=risk_corroboration,
            risk_band_corroborated=risk_corroborated,
            missing_indicators=[],
        )

        explainability = PermanentRedZoneExplainability(
            decision_reason=decision_reason,
            trigger_summary=decision_reason,
            trigger_audit=trigger_audit,
            trigger_audits=[trigger_audit],
            active_subsidence_triggered=subsidence_triggered,
            compound_hazard_triggered=compound_landslide_triggered,
            slope_threshold_met=slope_threshold_met,
            historical_landslides_threshold_met=landslides_threshold_met,
            risk_band_corroborated=risk_corroborated,
            monitoring_recommended=(status == RedZoneStatus.MONITOR),
            missing_required_indicators=[],
            source_village_ids=[target_id],
            source_village_provenance={target_id: src_provenance[0]} if src_provenance else {target_id: obs.model_dump() if hasattr(obs, "model_dump") else {}},
            source_provenance=src_provenance,
            is_dissolved=False,
            dissolved_zone_count=1,
            profile_id=self.profile.metadata.id.value if hasattr(self.profile.metadata.id, "value") else str(self.profile.metadata.id),
            buffer_applied_m=buffer_applied,
        )

        return PermanentRedZoneCandidate(
            candidate_id=f"PRZ-CAND-{target_id}",
            zone_id=f"PRZ-CAND-{target_id}",
            name=f"Permanent Red Zone Candidate ({target_name})",
            status=status,
            zone_type=zone_type,
            danger_level=danger_level,
            geometry=mp_geom,
            srid=4326,
            area_sq_km=area_sq_km,
            buffer_distance_applied_m=buffer_applied,
            contributing_village_ids=[target_id],
            is_candidate=is_candidate,
            is_active=False,
            declared_by_officer_id=None,
            declared_at=None,
            explainability=explainability,
            metadata_json={
                "village_id": target_id,
                "village_name": target_name,
                "slope_deg": obs.slope_deg,
                "historical_landslide_count": obs.historical_landslide_count,
                "active_subsidence": obs.active_subsidence,
                "risk_score": obs.risk_score,
                "risk_band": risk_band_str,
            },
        )

    # =====================================================================
    # Multi-Settlement Demarcation & Dissolve
    # =====================================================================

    def demarcate_permanent_red_zones(
        self,
        inputs: Sequence[Any],
        dissolve_overlaps: bool = True,
        dissolve: Optional[bool] = None,
    ) -> List[PermanentRedZoneCandidate]:
        """Demarcate permanent red zone candidates across multiple settlements with optional overlap dissolve."""
        should_dissolve = dissolve if dissolve is not None else dissolve_overlaps
        evaluated_candidates = [self.evaluate_village(item) for item in inputs]

        if not should_dissolve:
            return evaluated_candidates

        return dissolve_overlapping_candidates(
            evaluated_candidates,
            default_danger_level=self.default_danger_level,
        )

    # =====================================================================
    # Geometry Resolution Helpers
    # =====================================================================

    def _resolve_geometry(self, obs: GeophysicalObservationInput) -> Optional[MultiPolygon]:
        """Resolve and normalize geometry: Polygon/MultiPolygon directly, Point via geodesic circular buffer."""
        # 1. Check direct Polygon/MultiPolygon hazard geometry
        hazard_geom = obs.geometry or obs.location_geometry
        if hazard_geom is not None:
            if hasattr(hazard_geom, "geom_type") and hazard_geom.geom_type == "Point":
                return create_geodesic_buffer(hazard_geom, buffer_distance_m=self.buffer_m)
            return normalize_to_multipolygon(hazard_geom)

        # 2. Check location point representation
        loc = obs.location
        if loc is not None:
            if hasattr(loc, "geom_type") and loc.geom_type == "Point":
                return create_geodesic_buffer(loc, buffer_distance_m=self.buffer_m)
            lon, lat = self._extract_lon_lat(loc)
            return create_geodesic_buffer(lon, lat, self.buffer_m)

        return None

    def _extract_lon_lat(self, loc: Any) -> Tuple[float, float]:
        if hasattr(loc, "x") and hasattr(loc, "y"):
            return float(loc.x), float(loc.y)
        if isinstance(loc, (list, tuple)) and len(loc) >= 2:
            return float(loc[0]), float(loc[1])
        if isinstance(loc, dict):
            if "coordinates" in loc and isinstance(loc["coordinates"], (list, tuple)):
                coords = loc["coordinates"]
                return float(coords[0]), float(coords[1])
            if "lon" in loc and "lat" in loc:
                return float(loc["lon"]), float(loc["lat"])
            if "longitude" in loc and "latitude" in loc:
                return float(loc["longitude"]), float(loc["latitude"])
        raise SpatialGeometryError(f"Unable to extract (lon, lat) from location: {loc}")

    def _coerce_observation_input(
        self,
        input_data: Any,
        village_id: Optional[str] = None,
        provenance: Optional[Any] = None,
    ) -> GeophysicalObservationInput:
        """Coerce raw dictionaries, objects, or GeophysicalObservationInput."""
        if isinstance(input_data, GeophysicalObservationInput):
            return input_data

        if isinstance(input_data, dict):
            # Check for synthetic GeoJSON feature structure
            props = input_data.get("properties", input_data)
            geom = input_data.get("geometry")

            v_id = village_id or props.get("id") or props.get("village_id")
            v_name = props.get("name") or props.get("village_name") or v_id

            # Extract location if geom is a Point
            loc = None
            hazard_geom = None
            if geom and isinstance(geom, dict):
                if geom.get("type") == "Point":
                    loc = geom.get("coordinates")
                elif geom.get("type") in ("Polygon", "MultiPolygon"):
                    hazard_geom = geom

            if loc is None and "location" in props:
                loc = props["location"]
            if loc is None and "location_geometry" in props:
                loc = props["location_geometry"]

            # Extract hazards sub-dictionary if present (synthetic schemas)
            hazards = props.get("hazards", {})
            if not isinstance(hazards, dict):
                hazards = {}

            slope = props.get("slope_deg", hazards.get("slope_deg"))
            landslides = props.get("historical_landslide_count", hazards.get("historical_landslide_count"))
            subsidence = props.get("active_subsidence", hazards.get("active_subsidence"))

            prov = provenance or props.get("provenance")

            return GeophysicalObservationInput(
                village_id=v_id,
                name=v_name,
                village_name=v_name,
                location=loc,
                geometry=hazard_geom or props.get("geometry"),
                slope_deg=slope,
                historical_landslide_count=landslides,
                active_subsidence=subsidence,
                risk_score=props.get("risk_score"),
                risk_band=props.get("risk_band") or props.get("upstream_risk_band"),
                upstream_risk_band=props.get("upstream_risk_band") or props.get("risk_band"),
                provenance=prov,
            )

        # Check for model object with attributes
        v_id = village_id or getattr(input_data, "village_id", getattr(input_data, "id", None))
        v_name = getattr(input_data, "name", getattr(input_data, "village_name", v_id))
        loc = getattr(input_data, "location", getattr(input_data, "location_geometry", None))
        geom = getattr(input_data, "geometry", None)
        slope = getattr(input_data, "slope_deg", None)
        landslides = getattr(input_data, "historical_landslide_count", None)
        subsidence = getattr(input_data, "active_subsidence", None)
        risk_sc = getattr(input_data, "risk_score", None)
        risk_bd = getattr(input_data, "risk_band", getattr(input_data, "upstream_risk_band", None))
        prov = provenance or getattr(input_data, "provenance", None)

        return GeophysicalObservationInput(
            village_id=v_id,
            name=v_name,
            village_name=v_name,
            location=loc,
            geometry=geom,
            slope_deg=slope,
            historical_landslide_count=landslides,
            active_subsidence=subsidence,
            risk_score=risk_sc,
            risk_band=risk_bd,
            upstream_risk_band=risk_bd,
            provenance=prov,
        )
