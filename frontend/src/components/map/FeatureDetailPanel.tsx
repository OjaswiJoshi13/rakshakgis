"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SelectedFeatureInfo } from "@/types/gis";

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
  if (!feature) return null;

  const props = feature.properties || {};

  const renderCandidateSiteDetails = () => (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-sky-400">
            Candidate Safe Haven #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-slate-100 leading-snug">
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

      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800">
        <div>
          <span className="text-slate-400 block text-[10px]">Elevation</span>
          <span className="font-semibold text-slate-200">
            {props.elevation_m !== null && props.elevation_m !== undefined
              ? `${props.elevation_m} m`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">Terrain Slope</span>
          <span className="font-semibold text-slate-200">
            {props.terrain_slope_deg !== null && props.terrain_slope_deg !== undefined
              ? `${props.terrain_slope_deg}°`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">Surveyed Area</span>
          <span className="font-semibold text-slate-200">
            {props.area_sq_m !== null && props.area_sq_m !== undefined
              ? `${Number(props.area_sq_m).toLocaleString()} m²`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">District Code</span>
          <span className="font-semibold text-slate-200">
            {props.district_id !== undefined ? `DIST-${props.district_id}` : "—"}
          </span>
        </div>
      </div>

      {feature.coordinates && (
        <div className="text-[10px] font-mono text-slate-400">
          Location: {feature.coordinates[0].toFixed(5)}, {feature.coordinates[1].toFixed(5)} (WGS84)
        </div>
      )}
    </div>
  );

  const renderRouteDetails = () => (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400">
            Evacuation Corridor #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-slate-100 leading-snug">
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

      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800">
        <div>
          <span className="text-slate-400 block text-[10px]">Distance</span>
          <span className="font-semibold text-slate-200">
            {props.distance_km !== undefined ? `${props.distance_km} km` : "—"}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">Estimated Transit</span>
          <span className="font-semibold text-slate-200">
            {props.estimated_travel_time_min !== null && props.estimated_travel_time_min !== undefined
              ? `${props.estimated_travel_time_min} min`
              : "—"}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">Route Classification</span>
          <span className="font-semibold text-slate-200 capitalize">
            {String(props.route_type || "Standard")}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">Max Incline</span>
          <span className="font-semibold text-slate-200">
            {props.max_slope_deg !== null && props.max_slope_deg !== undefined
              ? `${props.max_slope_deg}°`
              : "—"}
          </span>
        </div>
      </div>

      {Boolean(props.origin_village_name || props.destination_site_name) && (
        <div className="text-[11px] bg-slate-900/50 p-2 rounded border border-slate-800/80 space-y-1">
          <div className="text-slate-400">
            From: <strong className="text-slate-200">{String(props.origin_village_name || "—")}</strong>
          </div>
          <div className="text-slate-400">
            To: <strong className="text-slate-200">{String(props.destination_site_name || "—")}</strong>
          </div>
        </div>
      )}

      {Boolean(props.is_blocked && props.blockage_reason) && (
        <div className="text-[11px] text-red-300 bg-red-950/50 border border-red-900/80 p-2 rounded font-mono">
          Hazard Notice: {String(props.blockage_reason)}
        </div>
      )}
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
            <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400">
              Red Zone #{feature.id}
            </span>
            <h3 className="text-sm font-bold text-slate-100 leading-snug">
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

        <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800">
          <div>
            <span className="text-slate-400 block text-[10px]">Threat Type</span>
            <span className="font-semibold text-slate-200 capitalize">
              {zoneType}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">Demarcated Area</span>
            <span className="font-semibold text-slate-200">
              {area}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">Status</span>
            <span className="font-semibold text-amber-400">
              {props.is_active ? "Active Statutory" : "Proposed Candidate"}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px]">Contributing Settlements</span>
            <span className="font-semibold text-slate-200">
              {contributingCount > 0 ? `${contributingCount} Habitations` : "None recorded"}
            </span>
          </div>
        </div>

        {Array.isArray(props.contributing_village_ids) && props.contributing_village_ids.length > 0 && (
          <div className="text-[10px] font-mono text-slate-400 bg-slate-900/40 p-2 rounded border border-slate-800/60">
            Village IDs: {props.contributing_village_ids.join(", ")}
          </div>
        )}

        <div className="text-[10px] text-amber-300 bg-amber-950/40 border border-amber-800/60 p-2 rounded font-mono leading-relaxed">
          <strong className="text-amber-400 block mb-0.5">RULE 12 GOVERNANCE INVARIANT:</strong>
          {governanceNotice}
        </div>
      </div>
    );
  };

  const renderHabitationDetails = () => (
    <div className="space-y-3" data-testid="habitation-detail-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400">
            Habitation Settlement #{feature.id}
          </span>
          <h3 className="text-sm font-bold text-slate-100 leading-snug">
            {String(props.name || `Village #${feature.id}`)}
          </h3>
        </div>
        <Badge variant="outline" size="sm" className="font-mono">
          {props.census_code ? `Census: ${props.census_code}` : "Settlement"}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800">
        <div>
          <span className="text-slate-400 block text-[10px]">Elevation</span>
          <span className="font-semibold text-slate-200">
            {props.elevation_m !== null && props.elevation_m !== undefined ? `${props.elevation_m} m` : "—"}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">Slope Angle</span>
          <span className="font-semibold text-slate-200">
            {props.slope_deg !== null && props.slope_deg !== undefined ? `${props.slope_deg}°` : "—"}
          </span>
        </div>
      </div>

      {feature.coordinates && (
        <div className="text-[10px] font-mono text-slate-400">
          Coords: {feature.coordinates[0].toFixed(5)}, {feature.coordinates[1].toFixed(5)}
        </div>
      )}
    </div>
  );

  const renderGenericDetails = () => (
    <div className="space-y-2">
      <h3 className="text-sm font-bold text-slate-100">
        Feature #{feature.id} ({feature.geometryType})
      </h3>
      <div className="max-h-48 overflow-y-auto space-y-1 text-xs font-mono">
        {Object.entries(props).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between border-b border-slate-800/40 py-1">
            <span className="text-slate-400 capitalize">{key.replace(/_/g, " ")}:</span>
            <span className="text-slate-200 font-semibold">{String(value ?? "—")}</span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div
      className={`bg-slate-950/95 backdrop-blur-md border border-slate-800 rounded-xl shadow-2xl p-4 text-xs z-20 max-w-sm w-full ${className}`}
      data-testid="feature-detail-panel"
      role="dialog"
      aria-labelledby="feature-detail-title"
    >
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-3">
        <span
          id="feature-detail-title"
          className="font-mono text-[11px] uppercase tracking-wider text-slate-400 font-semibold"
        >
          Spatial Feature Inspector
        </span>
        <Button
          variant="secondary"
          size="sm"
          onClick={onClose}
          className="h-6 w-6 p-0 text-slate-400 hover:text-slate-100"
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
        : renderGenericDetails()}
    </div>
  );
};
