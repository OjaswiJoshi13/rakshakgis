import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SelectedFeatureInfo } from "@/types/gis";
import { fetchVillageAnalysis } from "@/lib/api/gis";
import { apiClient } from "@/lib/api/client";

export interface FeatureDetailPanelProps {
  feature: SelectedFeatureInfo | null;
  onClose: () => void;
  className?: string;
}

export const FeatureDetailPanel: React.FC<FeatureDetailPanelProps> = ({
  feature,
  onClose,
  className = "",
}) => {
  const [authoritativeData, setAuthoritativeData] = useState<any>(null);
  const [isLoadingAuthoritative, setIsLoadingAuthoritative] = useState<boolean>(false);

  useEffect(() => {
    if (!feature || !feature.id) {
      setAuthoritativeData(null);
      return;
    }
    let isMounted = true;
    const fetchAuthoritative = async () => {
      setIsLoadingAuthoritative(true);
      try {
        const cat = feature.layerCategory;
        const eType = feature.properties?.entity_type;
        if (cat === "habitations" || eType === "village") {
          const res = await fetchVillageAnalysis(feature.id);
          if (isMounted && res.data) setAuthoritativeData(res.data);
        } else if (cat === "candidate_sites" || eType === "candidate_site") {
          const res = await apiClient.get<any>(`/sites/${feature.id}`);
          if (isMounted && res.data) setAuthoritativeData(res.data);
        } else if (cat === "red_zones" || eType === "red_zone") {
          const res = await apiClient.get<any>(`/red-zones/${feature.id}`);
          if (isMounted && res.data) setAuthoritativeData(res.data);
        }
      } catch (err) {
        // Fall back to GeoJSON properties
      } finally {
        if (isMounted) setIsLoadingAuthoritative(false);
      }
    };
    fetchAuthoritative();
    return () => {
      isMounted = false;
    };
  }, [feature]);

  if (!feature) return null;

  const props = feature.properties || {};

  const renderCandidateSiteDetails = () => (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-sky-600 dark:text-sky-400">
            Proposed Candidate Site #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-text-primary leading-snug">
            {String(props.name || `Site #${feature.id}`)}
          </h3>
        </div>
        <Badge
          variant={
            String(props.status).toLowerCase() === "active"
              ? "success"
              : String(props.status).toLowerCase() === "approved"
              ? "info"
              : String(props.status).toLowerCase() === "rejected"
              ? "danger"
              : "outline"
          }
          size="sm"
          className="capitalize"
        >
          {String(props.status || "Unknown")}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-surface-elevated p-2.5 rounded border border-border-subtle">
        <div>
          <span className="text-text-muted block text-[10px]">Elevation</span>
          <span className="font-semibold text-text-primary">
            {props.elevation_m !== null && props.elevation_m !== undefined
              ? `${props.elevation_m} m`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Terrain Slope</span>
          <span className="font-semibold text-text-primary">
            {props.terrain_slope_deg !== null && props.terrain_slope_deg !== undefined
              ? `${props.terrain_slope_deg}°`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Surveyed Area</span>
          <span className="font-semibold text-text-primary">
            {props.area_sq_m !== null && props.area_sq_m !== undefined
              ? `${Number(props.area_sq_m).toLocaleString()} m²`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">District Code</span>
          <span className="font-semibold text-text-primary">
            {props.district_id !== undefined ? `DIST-${props.district_id}` : "—"}
          </span>
        </div>
      </div>

      {feature.coordinates && (
        <div className="text-[10px] font-mono text-text-muted">
          Location: {feature.coordinates[0].toFixed(5)}, {feature.coordinates[1].toFixed(5)} (WGS84)
        </div>
      )}

      <div className="text-[10px] font-mono bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20 p-2 rounded">
        <strong>PROVENANCE:</strong> {String(props.provenance || "SYNTHETIC / PROPOSED — Candidate Relocation Site")}
      </div>
    </div>
  );

  const renderRouteDetails = () => (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
            Evacuation Corridor #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-text-primary leading-snug">
            {String(props.name || `Route #${feature.id}`)}
          </h3>
        </div>
        <Badge
          variant={props.is_blocked ? "danger" : "success"}
          size="sm"
          className="uppercase text-[9px]"
        >
          {props.is_blocked ? "Blocked" : "Open Passable"}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-surface-elevated p-2.5 rounded border border-border-subtle">
        <div>
          <span className="text-text-muted block text-[10px]">Distance</span>
          <span className="font-semibold text-text-primary">
            {props.distance_km !== undefined ? `${props.distance_km} km` : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Estimated Transit</span>
          <span className="font-semibold text-text-primary">
            {props.estimated_travel_time_min !== null && props.estimated_travel_time_min !== undefined
              ? `${props.estimated_travel_time_min} min`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Route Classification</span>
          <span className="font-semibold text-text-primary capitalize">
            {String(props.route_type || "Standard")}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Max Incline</span>
          <span className="font-semibold text-text-primary">
            {props.max_slope_deg !== null && props.max_slope_deg !== undefined
              ? `${props.max_slope_deg}°`
              : "—"}
          </span>
        </div>
      </div>

      {Boolean(props.origin_village_name || props.destination_site_name) && (
        <div className="text-[11px] bg-surface-elevated/70 p-2 rounded border border-border-subtle space-y-1">
          <div className="text-text-muted">
            From: <strong className="text-text-primary">{String(props.origin_village_name || "—")}</strong>
          </div>
          <div className="text-text-muted">
            To: <strong className="text-text-primary">{String(props.destination_site_name || "—")}</strong>
          </div>
        </div>
      )}

      {Boolean(props.is_blocked && props.blockage_reason) && (
        <div className="text-[11px] text-red-700 dark:text-red-300 bg-red-500/10 border border-red-500/30 p-2 rounded font-mono">
          Hazard Notice: {String(props.blockage_reason)}
        </div>
      )}

      <div className="text-[10px] font-mono bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 p-2 rounded">
        <strong>PROVENANCE:</strong> {String(props.provenance || "SYNTHETIC / DERIVED — Evacuation Corridors")}
      </div>
    </div>
  );

  const renderRedZoneDetails = () => {
    const dangerLevel = String(props.danger_level || "critical").toLowerCase();
    const zoneType = String(props.zone_type || "landslide_danger").replace(/_/g, " ");
    const area =
      props.area_sq_km !== null && props.area_sq_km !== undefined
        ? `${Number(props.area_sq_km).toFixed(2)} km²`
        : "—";
    const contributingCount = Array.isArray(props.contributing_village_ids)
      ? props.contributing_village_ids.length
      : 0;
    const governanceNotice = String(
      props.governance_notice ||
        "PROPOSED CANDIDATE ONLY: Statutory legal declaration requires officer review (M6-08 workflow)."
    );

    return (
      <div className="space-y-3" data-testid="red-zone-detail-card">
        <div className="flex items-start justify-between gap-2">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-rose-600 dark:text-rose-400">
              Red Zone #{feature.id}
            </span>
            <h3 className="text-sm font-bold text-text-primary leading-snug">
              {String(props.name || `Red Zone #${feature.id}`)}
            </h3>
          </div>
          <Badge
            variant={
              dangerLevel === "uninhabitable"
                ? "danger"
                : dangerLevel === "critical"
                ? "danger"
                : "warning"
            }
            size="sm"
            className="uppercase text-[9px] font-bold"
          >
            {dangerLevel}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-surface-elevated p-2.5 rounded border border-border-subtle">
          <div>
            <span className="text-text-muted block text-[10px]">Threat Type</span>
            <span className="font-semibold text-text-primary capitalize">
              {zoneType}
            </span>
          </div>
          <div>
            <span className="text-text-muted block text-[10px]">Demarcated Area</span>
            <span className="font-semibold text-text-primary">
              {area}
            </span>
          </div>
          <div>
            <span className="text-text-muted block text-[10px]">Status</span>
            <span className="font-semibold text-amber-600 dark:text-amber-400">
              {props.is_active ? "Active Statutory" : "Proposed Candidate"}
            </span>
          </div>
          <div>
            <span className="text-text-muted block text-[10px]">Contributing Settlements</span>
            <span className="font-semibold text-text-primary">
              {contributingCount > 0 ? `${contributingCount} Habitations` : "None recorded"}
            </span>
          </div>
        </div>

        {Array.isArray(props.contributing_village_ids) && props.contributing_village_ids.length > 0 && (
          <div className="text-[10px] font-mono text-text-muted bg-surface-elevated/70 p-2 rounded border border-border-subtle">
            Village IDs: {props.contributing_village_ids.join(", ")}
          </div>
        )}

        <div className="text-[10px] text-amber-800 dark:text-amber-300 bg-amber-500/10 border border-amber-500/30 p-2 rounded font-mono leading-relaxed">
          <strong className="text-amber-700 dark:text-amber-400 block mb-0.5">RULE 12 GOVERNANCE INVARIANT:</strong>
          {governanceNotice}
        </div>

        <div className="text-[10px] font-mono bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20 p-2 rounded">
          <strong>PROVENANCE:</strong> {String(props.provenance || "DERIVED / DEMONSTRATION — Permanent & Dynamic Red Zone Spatial Engine")}
        </div>
      </div>
    );
  };

  const renderHabitationDetails = () => (
    <div className="space-y-3" data-testid="habitation-detail-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-600 dark:text-amber-400">
            Habitation Settlement #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-text-primary leading-snug">
            {String(props.name || `Village #${feature.id}`)}
          </h3>
        </div>
        <Badge variant="outline" size="sm" className="font-mono text-text-secondary border-border-strong">
          {props.census_code ? `Census: ${props.census_code}` : "Settlement"}
        </Badge>
      </div>

      {isLoadingAuthoritative && (
        <div className="text-[10px] text-sky-600 dark:text-sky-400 font-mono animate-pulse">
          Querying authoritative backend entity records...
        </div>
      )}

      {/* Authoritative Population & Demographics (Census 2011) */}
      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-surface-elevated p-2.5 rounded border border-border-subtle">
        <div>
          <span className="text-text-muted block text-[10px]">Population (Census)</span>
          <span className="font-semibold text-text-primary">
            {authoritativeData?.population?.total !== null && authoritativeData?.population?.total !== undefined
              ? `${Number(authoritativeData.population.total).toLocaleString()} persons`
              : props.population !== undefined && props.population !== null
              ? `${Number(props.population).toLocaleString()} persons`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Households</span>
          <span className="font-semibold text-text-primary">
            {authoritativeData?.population?.households !== null && authoritativeData?.population?.households !== undefined
              ? `${Number(authoritativeData.population.households).toLocaleString()} HH`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Elevation</span>
          <span className="font-semibold text-text-primary">
            {props.elevation_m !== null && props.elevation_m !== undefined ? `${props.elevation_m} m` : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Slope Angle</span>
          <span className="font-semibold text-text-primary">
            {props.slope_deg !== null && props.slope_deg !== undefined ? `${props.slope_deg}°` : "—"}
          </span>
        </div>
      </div>

      {/* Authoritative Risk Assessment */}
      {(authoritativeData?.risk?.score !== null && authoritativeData?.risk?.score !== undefined || props.risk_score !== undefined) && (
        <div className="bg-surface-elevated border border-border-subtle rounded p-2.5 space-y-1.5 font-mono text-[11px]">
          <div className="flex items-center justify-between">
            <span className="text-text-muted text-[10px] uppercase">Composite Risk</span>
            <Badge
              variant={
                (authoritativeData?.risk?.band || props.risk_band) === "CRITICAL"
                  ? "danger"
                  : (authoritativeData?.risk?.band || props.risk_band) === "HIGH" || (authoritativeData?.risk?.band || props.risk_band) === "VERY_HIGH"
                  ? "warning"
                  : "info"
              }
              size="sm"
            >
              Score: {authoritativeData?.risk?.score ?? props.risk_score} ({authoritativeData?.risk?.band ?? props.risk_band})
            </Badge>
          </div>

          {authoritativeData?.red_zone?.is_in_red_zone && (
            <div className="text-[10px] text-red-700 dark:text-red-300 bg-red-500/10 border border-red-500/30 p-1.5 rounded">
              <strong className="text-red-700 dark:text-red-400">RED ZONE WARNING:</strong> Habitation located within declared Red Zone perimeter ({authoritativeData.red_zone.details?.danger_level?.toUpperCase()}).
            </div>
          )}
        </div>
      )}

      {feature.coordinates && (
        <div className="text-[10px] font-mono text-text-muted">
          Coords: {feature.coordinates[0].toFixed(5)}, {feature.coordinates[1].toFixed(5)}
        </div>
      )}

      <div className="text-[10px] font-mono bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 p-2 rounded">
        <strong>PROVENANCE:</strong> {String(props.provenance || "REAL — Census 2011 Habitation Settlement")}
      </div>
    </div>
  );

  const renderVillageBoundaryDetails = () => (
    <div className="space-y-3" data-testid="village-boundary-detail-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-sky-600 dark:text-sky-400">
            Cadastral Boundary #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-text-primary leading-snug">
            {String(props.name || `Village #${feature.id}`)}
          </h3>
        </div>
        <Badge variant="info" size="sm" className="font-mono text-xs">
          Survey of India
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-surface-elevated p-2.5 rounded border border-border-subtle">
        <div>
          <span className="text-text-muted block text-[10px]">Population (Census)</span>
          <span className="font-semibold text-text-primary">
            {props.population !== null && props.population !== undefined ? `${Number(props.population).toLocaleString()} persons` : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Households</span>
          <span className="font-semibold text-text-primary">
            {props.households !== null && props.households !== undefined ? `${Number(props.households).toLocaleString()} HH` : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Elevation</span>
          <span className="font-semibold text-text-primary">
            {props.elevation_m !== null && props.elevation_m !== undefined ? `${props.elevation_m} m` : "—"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Slope Angle</span>
          <span className="font-semibold text-text-primary">
            {props.slope_deg !== null && props.slope_deg !== undefined ? `${props.slope_deg}°` : "—"}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between bg-surface-elevated p-2 rounded border border-border-subtle font-mono text-[11px]">
        <span className="text-text-muted uppercase text-[10px]">Composite Risk</span>
        <Badge variant={String(props.risk_band) === "CRITICAL" ? "danger" : String(props.risk_band) === "HIGH" ? "warning" : "success"} size="sm">
          {Number(props.risk_score || props.composite_risk || 0).toFixed(1)} / 100 ({String(props.risk_band || "LOW")})
        </Badge>
      </div>

      <div className="text-[10px] font-mono bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20 p-2 rounded">
        <strong>PROVENANCE:</strong> {String(props.provenance || "REAL — Survey of India (Boundary) + Census 2011 (Demographics)")}
      </div>
    </div>
  );

  const renderEarthquakeDetails = () => (
    <div className="space-y-3" data-testid="earthquake-detail-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-rose-600 dark:text-rose-400">
            Seismic Event #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-text-primary leading-snug">
            Magnitude {Number(props.magnitude || 0).toFixed(1)} Richter
          </h3>
        </div>
        <Badge variant={Number(props.magnitude || 0) >= 5.0 ? "danger" : Number(props.magnitude || 0) >= 3.5 ? "warning" : "info"} size="sm">
          {Number(props.magnitude || 0) >= 6.0 ? "MAJOR" : Number(props.magnitude || 0) >= 4.5 ? "MODERATE" : "LIGHT"}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-surface-elevated p-2.5 rounded border border-border-subtle">
        <div>
          <span className="text-text-muted block text-[10px]">Hypocenter Depth</span>
          <span className="font-semibold text-text-primary">
            {props.depth_km !== undefined ? `${props.depth_km} km` : "10 km"}
          </span>
        </div>
        <div>
          <span className="text-text-muted block text-[10px]">Observed Date</span>
          <span className="font-semibold text-text-primary">
            {props.observed_at ? String(props.observed_at).slice(0, 10) : "Recorded"}
          </span>
        </div>
      </div>

      {Boolean(props.description) && (
        <div className="text-[11px] text-text-secondary bg-surface-elevated p-2 rounded border border-border-subtle">
          {String(props.description)}
        </div>
      )}

      <div className="text-[10px] font-mono bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20 p-2 rounded">
        <strong>PROVENANCE:</strong> {String(props.provenance || "REAL HISTORICAL — NCS MoES")}
      </div>
    </div>
  );

  const renderGenericDetails = () => (
    <div className="space-y-2">
      <h3 className="text-sm font-bold text-text-primary">
        Feature #{feature.id} ({feature.geometryType})
      </h3>
      <div className="max-h-48 overflow-y-auto space-y-1 text-xs font-mono">
        {Object.entries(props).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between border-b border-border-subtle py-1">
            <span className="text-text-muted capitalize">{key.replace(/_/g, " ")}:</span>
            <span className="text-text-primary font-semibold">{String(value ?? "—")}</span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div
      className={`bg-surface-panel/95 backdrop-blur-md border border-border-subtle rounded-xl shadow-2xl p-4 text-xs z-20 max-w-sm w-full ${className}`}
      data-testid="feature-detail-panel"
      role="dialog"
      aria-labelledby="feature-detail-title"
    >
      <div className="flex items-center justify-between border-b border-border-subtle pb-2 mb-3">
        <span
          id="feature-detail-title"
          className="font-mono text-[11px] uppercase tracking-wider text-text-muted font-semibold"
        >
          Spatial Feature Inspector
        </span>
        <Button
          variant="secondary"
          size="sm"
          onClick={onClose}
          className="h-6 w-6 p-0 text-text-muted hover:text-text-primary"
          aria-label="Close feature details"
        >
          &times;
        </Button>
      </div>

      {feature.layerCategory === "candidate_sites"
        ? renderCandidateSiteDetails()
        : feature.layerCategory === "routes"
        ? renderRouteDetails()
        : feature.layerCategory === "red_zones"
        ? renderRedZoneDetails()
        : feature.layerCategory === "habitations"
        ? renderHabitationDetails()
        : feature.layerCategory === "village_boundaries"
        ? renderVillageBoundaryDetails()
        : feature.layerCategory === "earthquakes"
        ? renderEarthquakeDetails()
        : renderGenericDetails()}
    </div>
  );
};
