"use client";

import React, { useState, useMemo, useEffect } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import {
  useApiQuery,
  fetchCandidateSites,
  fetchRoutes,
  fetchRedZones,
  fetchVillages,
} from "@/lib/api";
import { useOperational } from "@/context/OperationalContext";
import { PaginatedResponse } from "@/types/api";
import { CandidateSiteRead } from "@/types/dashboard";
import {
  GeoJSONFeatureCollection,
  RedZoneRead,
  RouteRead,
  SelectedFeatureInfo,
  VillageRead,
  calculateBounds,
  candidateSiteBoundariesToGeoJSON,
  candidateSitesToGeoJSON,
  redZonesToGeoJSON,
  routesToGeoJSON,
  villagesToGeoJSON,
} from "@/types/gis";
import {
  GIS_ACTIVE_MAP_LAYERS,
  FeatureDetailPanel,
  LayerControlPanel,
  MapCanvas,
  MapHeader,
} from "@/components/map";

export default function GisMapPage() {
  const { activeRegion } = useOperational();

  const [selectedFeature, setSelectedFeature] = useState<SelectedFeatureInfo | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [viewportBounds, setViewportBounds] = useState<[[number, number], [number, number]] | null>(
    null
  );
  const [layerVisibility, setLayerVisibility] = useState<Record<string, boolean>>({
    "candidate-sites-points": true,
    "candidate-sites-boundaries": true,
    "routes-lines": true,
    "red-zones-polygons": true,
    "habitations-points": true,
    "hazards-extents": false,
  });

  // Reset region-specific UI state on activeRegion transition to prevent stale feature/viewport leak
  useEffect(() => {
    setSelectedFeature(null);
    setViewportBounds(null);
  }, [activeRegion]);

  // 1. Fetch Candidate Relocation Sites (Points & Boundaries)
  const {
    data: sitesEnvelope,
    isLoading: sitesLoading,
    isError: sitesError,
    error: sitesErrObj,
    refetch: refetchSites,
  } = useApiQuery<PaginatedResponse<CandidateSiteRead>>(
    `gis-sites-${activeRegion}`,
    (signal) => fetchCandidateSites({ page: 1, page_size: 50 }, signal),
    { cacheTtlMs: 60000 }
  );

  // 2. Fetch Evacuation & Access Routes (LineStrings)
  const {
    data: routesEnvelope,
    isLoading: routesLoading,
    isError: routesError,
    error: routesErrObj,
    refetch: refetchRoutes,
  } = useApiQuery<PaginatedResponse<RouteRead>>(
    `gis-routes-${activeRegion}`,
    (signal) => fetchRoutes({ page: 1, page_size: 50 }, signal),
    { cacheTtlMs: 60000 }
  );

  // 3. Fetch Permanent & Dynamic Red Zones (Polygons / MultiPolygons)
  const {
    data: redZonesEnvelope,
    isLoading: redZonesLoading,
    isError: redZonesError,
    error: redZonesErrObj,
    refetch: refetchRedZones,
  } = useApiQuery<PaginatedResponse<RedZoneRead>>(
    `gis-red-zones-${activeRegion}`,
    (signal) => fetchRedZones({ page: 1, page_size: 50 }, signal),
    { cacheTtlMs: 60000 }
  );

  // 4. Fetch Administrative Habitations / Settlements (Points)
  const {
    data: villagesEnvelope,
    isLoading: villagesLoading,
    isError: villagesError,
    error: villagesErrObj,
    refetch: refetchVillages,
  } = useApiQuery<PaginatedResponse<VillageRead>>(
    `gis-villages-${activeRegion}`,
    (signal) => fetchVillages({ page: 1, page_size: 50 }, signal),
    { cacheTtlMs: 60000 }
  );

  // Transform backend models to standard GeoJSON FeatureCollections
  const sitesGeoJSON = useMemo(() => {
    return candidateSitesToGeoJSON(sitesEnvelope?.data || []);
  }, [sitesEnvelope?.data]);

  const siteBoundariesGeoJSON = useMemo(() => {
    return candidateSiteBoundariesToGeoJSON(sitesEnvelope?.data || []);
  }, [sitesEnvelope?.data]);

  const routesGeoJSON = useMemo(() => {
    return routesToGeoJSON(routesEnvelope?.data || []);
  }, [routesEnvelope?.data]);

  const redZonesGeoJSON = useMemo(() => {
    return redZonesToGeoJSON(redZonesEnvelope?.data || []);
  }, [redZonesEnvelope?.data]);

  const villagesGeoJSON = useMemo(() => {
    return villagesToGeoJSON(villagesEnvelope?.data || []);
  }, [villagesEnvelope?.data]);

  // Dictionary of GeoJSON sources fed to MapLibre
  const sourcesData: Record<string, GeoJSONFeatureCollection> = useMemo(() => {
    return {
      "candidate-sites-source": sitesGeoJSON,
      "candidate-site-boundaries-source": siteBoundariesGeoJSON,
      "routes-source": routesGeoJSON,
      "red-zones-source": redZonesGeoJSON,
      "habitations-source": villagesGeoJSON,
    };
  }, [sitesGeoJSON, siteBoundariesGeoJSON, routesGeoJSON, redZonesGeoJSON, villagesGeoJSON]);

  // Dynamic feature counts for layer controls
  const featureCounts = useMemo(() => {
    return {
      "candidate-sites-points": sitesGeoJSON.features.length,
      "candidate-sites-boundaries": siteBoundariesGeoJSON.features.length,
      "routes-lines": routesGeoJSON.features.length,
      "red-zones-polygons": redZonesGeoJSON.features.length,
      "habitations-points": villagesGeoJSON.features.length,
    };
  }, [sitesGeoJSON, siteBoundariesGeoJSON, routesGeoJSON, redZonesGeoJSON, villagesGeoJSON]);

  // Toggle individual layer visibility
  const handleToggleLayer = (layerId: string) => {
    setLayerVisibility((prev) => ({
      ...prev,
      [layerId]: !prev[layerId],
    }));
  };

  // Manual refresh across all spatial layers
  const handleRefreshAll = async () => {
    setIsRefreshing(true);
    try {
      await Promise.allSettled([
        refetchSites(),
        refetchRoutes(),
        refetchRedZones(),
        refetchVillages(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Compute bounding box across all active features
  const computedBounds = useMemo(() => {
    const allFeatures = [
      ...sitesGeoJSON.features,
      ...siteBoundariesGeoJSON.features,
      ...routesGeoJSON.features,
      ...redZonesGeoJSON.features,
      ...villagesGeoJSON.features,
    ];
    return calculateBounds(allFeatures);
  }, [sitesGeoJSON, siteBoundariesGeoJSON, routesGeoJSON, redZonesGeoJSON, villagesGeoJSON]);

  const handleResetView = () => {
    if (computedBounds) {
      setViewportBounds([[...computedBounds[0]], [...computedBounds[1]]]);
    }
  };

  const isMapLoading = sitesLoading || routesLoading || redZonesLoading || villagesLoading;
  const hasMapErrors = sitesError || routesError || redZonesError || villagesError;

  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="space-y-4">
          {/* Header & Operational Bar */}
          <MapHeader
            totalSites={sitesGeoJSON.features.length}
            totalRoutes={routesGeoJSON.features.length}
            totalRedZones={redZonesGeoJSON.features.length}
            totalVillages={villagesGeoJSON.features.length}
            isRefreshing={isRefreshing}
            onRefresh={handleRefreshAll}
            onResetView={handleResetView}
          />

          {/* Section-level User-Safe Error Notice if an endpoint failed */}
          {hasMapErrors && (
            <div
              data-testid="gis-error-banner"
              className="rounded-lg border border-amber-800/80 bg-amber-950/40 p-3 text-xs text-amber-200 flex items-center justify-between font-mono"
            >
              <div>
                <strong className="text-amber-400">Layer Notice:</strong> Some spatial layers could
                not be retrieved from backend (
                {[
                  sitesError && `Sites: ${sitesErrObj?.message || "Unavailable"}`,
                  routesError && `Routes: ${routesErrObj?.message || "Unavailable"}`,
                  redZonesError && `Red Zones: ${redZonesErrObj?.message || "Unavailable"}`,
                  villagesError && `Habitations: ${villagesErrObj?.message || "Unavailable"}`,
                ]
                  .filter(Boolean)
                  .join(" | ")}
                ). Available layers remain operational.
              </div>
            </div>
          )}

          {/* Map Viewport Area */}
          <div className="relative w-full h-[calc(100vh-210px)] min-h-[580px] rounded-xl overflow-hidden shadow-2xl border border-slate-800">
            {/* Interactive Map Canvas */}
            <MapCanvas
              layers={GIS_ACTIVE_MAP_LAYERS}
              layerVisibility={layerVisibility}
              sourcesData={sourcesData}
              onFeatureSelect={setSelectedFeature}
              selectedFeature={selectedFeature}
              bounds={viewportBounds}
              isLoading={isMapLoading}
              className="w-full h-full"
            />

            {/* Floating Layer Control Panel (Top-Left) */}
            <div className="absolute top-4 left-4 max-w-xs w-full pointer-events-auto">
              <LayerControlPanel
                layers={GIS_ACTIVE_MAP_LAYERS}
                layerVisibility={layerVisibility}
                onToggleLayer={handleToggleLayer}
                featureCounts={featureCounts}
              />
            </div>

            {/* Floating Feature Inspector (Bottom-Left / Top-Right) */}
            {selectedFeature && (
              <div className="absolute bottom-4 left-4 pointer-events-auto">
                <FeatureDetailPanel
                  feature={selectedFeature}
                  onClose={() => setSelectedFeature(null)}
                />
              </div>
            )}
          </div>
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}
