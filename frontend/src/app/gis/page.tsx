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
  fetchMapLayers,
} from "@/lib/api";
import { useOperational } from "@/context/OperationalContext";
import { PaginatedResponse, ResponseEnvelope } from "@/types/api";
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
  earthquakesToGeoJSON,
  redZonesToGeoJSON,
  routesToGeoJSON,
  villageBoundariesToGeoJSON,
  villagesToGeoJSON,
} from "@/types/gis";
import {
  GIS_ACTIVE_MAP_LAYERS,
  FeatureDetailPanel,
  GisSearchBar,
  GisSearchResult,
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
    "village-boundaries-polygons": true,
    "habitations-points": true,
    "earthquakes-ncs": true,
    "earthquakes-usgs": true,
    "candidate-sites-points": true,
    "candidate-sites-boundaries": true,
    "routes-lines": true,
    "red-zones-polygons": true,
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

  // 5. Fetch Real Vector Map Layers via GET /map/layers
  // (Survey of India cadastral boundaries, Census habitations, NCS earthquakes, USGS live feed)
  const {
    data: mapLayersEnvelope,
    isLoading: mapLayersLoading,
    isError: mapLayersError,
    error: mapLayersErrObj,
    refetch: refetchMapLayers,
  } = useApiQuery<ResponseEnvelope<Record<string, any>>>(
    `gis-map-layers-${activeRegion}`,
    (signal) => fetchMapLayers(undefined, activeRegion, signal),
    { cacheTtlMs: 60000 }
  );

  // Transform backend models to standard GeoJSON FeatureCollections
  const sitesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.sites || mapLayersEnvelope?.data?.candidate_sites;
    if (layer?.features?.length) {
      return layer as GeoJSONFeatureCollection;
    }
    return candidateSitesToGeoJSON(sitesEnvelope?.data || []);
  }, [mapLayersEnvelope?.data?.sites, mapLayersEnvelope?.data?.candidate_sites, sitesEnvelope?.data]);

  const siteBoundariesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.site_boundaries || mapLayersEnvelope?.data?.candidate_site_boundaries;
    if (layer?.features?.length) {
      return layer as GeoJSONFeatureCollection;
    }
    return candidateSiteBoundariesToGeoJSON(sitesEnvelope?.data || []);
  }, [mapLayersEnvelope?.data?.site_boundaries, mapLayersEnvelope?.data?.candidate_site_boundaries, sitesEnvelope?.data]);

  const routesGeoJSON = useMemo(() => {
    if (mapLayersEnvelope?.data?.routes?.features?.length) {
      return mapLayersEnvelope.data.routes as GeoJSONFeatureCollection;
    }
    return routesToGeoJSON(routesEnvelope?.data || []);
  }, [mapLayersEnvelope?.data?.routes, routesEnvelope?.data]);

  const redZonesGeoJSON = useMemo(() => {
    if (mapLayersEnvelope?.data?.red_zones?.features?.length) {
      return mapLayersEnvelope.data.red_zones as GeoJSONFeatureCollection;
    }
    return redZonesToGeoJSON(redZonesEnvelope?.data || []);
  }, [mapLayersEnvelope?.data?.red_zones, redZonesEnvelope?.data]);

  // STRICT REQUIREMENT: No silent fallback to 40 demo villages.
  // Must strictly consume real region-scoped habitation records from /map/layers.
  const villagesGeoJSON = useMemo(() => {
    if (mapLayersEnvelope?.data?.villages?.features?.length) {
      return mapLayersEnvelope.data.villages as GeoJSONFeatureCollection;
    }
    return { type: "FeatureCollection" as const, features: [] };
  }, [mapLayersEnvelope?.data?.villages]);

  // STRICT REQUIREMENT: No silent fallback to 0 boundaries.
  // Must strictly consume real Survey of India cadastral boundaries from /map/layers.
  const villageBoundariesGeoJSON = useMemo(() => {
    if (mapLayersEnvelope?.data?.village_boundaries?.features?.length) {
      return mapLayersEnvelope.data.village_boundaries as GeoJSONFeatureCollection;
    }
    return { type: "FeatureCollection" as const, features: [] };
  }, [mapLayersEnvelope?.data?.village_boundaries]);

  const earthquakesNcsGeoJSON = useMemo(() => {
    if (mapLayersEnvelope?.data?.earthquakes_ncs?.features?.length) {
      return mapLayersEnvelope.data.earthquakes_ncs as GeoJSONFeatureCollection;
    }
    return { type: "FeatureCollection" as const, features: [] };
  }, [mapLayersEnvelope?.data?.earthquakes_ncs]);

  const earthquakesUsgsGeoJSON = useMemo(() => {
    if (mapLayersEnvelope?.data?.earthquakes_usgs?.features?.length) {
      return mapLayersEnvelope.data.earthquakes_usgs as GeoJSONFeatureCollection;
    }
    return { type: "FeatureCollection" as const, features: [] };
  }, [mapLayersEnvelope?.data?.earthquakes_usgs]);

  // Dictionary of GeoJSON sources fed to MapLibre
  const sourcesData: Record<string, GeoJSONFeatureCollection> = useMemo(() => {
    return {
      "village-boundaries-source": villageBoundariesGeoJSON,
      "habitations-source": villagesGeoJSON,
      "earthquakes-ncs-source": earthquakesNcsGeoJSON,
      "earthquakes-usgs-source": earthquakesUsgsGeoJSON,
      "candidate-sites-source": sitesGeoJSON,
      "candidate-site-boundaries-source": siteBoundariesGeoJSON,
      "routes-source": routesGeoJSON,
      "red-zones-source": redZonesGeoJSON,
    };
  }, [
    villageBoundariesGeoJSON,
    villagesGeoJSON,
    earthquakesNcsGeoJSON,
    earthquakesUsgsGeoJSON,
    sitesGeoJSON,
    siteBoundariesGeoJSON,
    routesGeoJSON,
    redZonesGeoJSON,
  ]);

  // Dynamic feature counts for layer controls
  const featureCounts = useMemo(() => {
    return {
      "village-boundaries-polygons": villageBoundariesGeoJSON.features.length,
      "habitations-points": villagesGeoJSON.features.length,
      "earthquakes-ncs": earthquakesNcsGeoJSON.features.length,
      "earthquakes-usgs": earthquakesUsgsGeoJSON.features.length,
      "candidate-sites-points": sitesGeoJSON.features.length,
      "candidate-sites-boundaries": siteBoundariesGeoJSON.features.length,
      "routes-lines": routesGeoJSON.features.length,
      "red-zones-polygons": redZonesGeoJSON.features.length,
    };
  }, [
    villageBoundariesGeoJSON,
    villagesGeoJSON,
    earthquakesNcsGeoJSON,
    earthquakesUsgsGeoJSON,
    sitesGeoJSON,
    siteBoundariesGeoJSON,
    routesGeoJSON,
    redZonesGeoJSON,
  ]);

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
        refetchMapLayers?.(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Compute bounding box across all active features
  const computedBounds = useMemo(() => {
    if (mapLayersEnvelope?.data?.bounds && Array.isArray(mapLayersEnvelope.data.bounds)) {
      return mapLayersEnvelope.data.bounds as [[number, number], [number, number]];
    }
    const allFeatures = [
      ...villageBoundariesGeoJSON.features,
      ...sitesGeoJSON.features,
      ...siteBoundariesGeoJSON.features,
      ...routesGeoJSON.features,
      ...redZonesGeoJSON.features,
      ...villagesGeoJSON.features,
    ];
    return calculateBounds(allFeatures);
  }, [
    mapLayersEnvelope?.data?.bounds,
    villageBoundariesGeoJSON,
    sitesGeoJSON,
    siteBoundariesGeoJSON,
    routesGeoJSON,
    redZonesGeoJSON,
    villagesGeoJSON,
  ]);

  const handleResetView = () => {
    if (computedBounds) {
      setViewportBounds([[...computedBounds[0]], [...computedBounds[1]]]);
    }
  };

  const handleSelectSearchResult = (result: GisSearchResult) => {
    if (result.coordinates && Array.isArray(result.coordinates)) {
      const [lon, lat] = result.coordinates;
      setViewportBounds([
        [lon - 0.02, lat - 0.02],
        [lon + 0.02, lat + 0.02],
      ]);
    }
    let layerId = "habitations-points";
    let layerCategory: "habitations" | "candidate_sites" | "red_zones" = "habitations";
    if (result.entity_type === "candidate_site") {
      layerId = "candidate-sites-points";
      layerCategory = "candidate_sites";
    } else if (result.entity_type === "red_zone") {
      layerId = "red-zones-polygons";
      layerCategory = "red_zones";
    }

    setSelectedFeature({
      id: result.id,
      layerId,
      layerCategory,
      properties: {
        id: result.id,
        name: result.name,
        code: result.code,
        entity_type: result.entity_type,
        elevation_m: result.elevation_m,
        slope_deg: result.slope_deg,
      },
      geometryType: "Point",
      coordinates: result.coordinates || undefined,
    });
  };

  const isMapLoading = mapLayersLoading || sitesLoading || routesLoading || redZonesLoading || villagesLoading;
  const hasMapErrors = mapLayersError || sitesError || routesError || redZonesError || villagesError;

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
              className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-200 flex items-center justify-between font-mono"
            >
              <div>
                <strong className="text-amber-700 dark:text-amber-400">Layer Notice:</strong> Some spatial layers could
                not be retrieved from backend (
                {[
                  mapLayersError && `Authoritative GIS Layers: ${mapLayersErrObj?.message || "Unavailable"}`,
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
          <div className="relative w-full h-[calc(100vh-210px)] min-h-[580px] rounded-xl overflow-hidden shadow-lg border border-border-subtle">
            {/* Interactive Map Canvas */}
            <MapCanvas
              layers={GIS_ACTIVE_MAP_LAYERS}
              layerVisibility={layerVisibility}
              sourcesData={sourcesData}
              onFeatureSelect={setSelectedFeature}
              selectedFeature={selectedFeature}
              initialCenter={[79.5, 30.4]}
              initialZoom={10}
              bounds={viewportBounds}
              isLoading={isMapLoading}
              className="w-full h-full"
            />

            {/* Floating Spatial Search Bar (Top-Center) */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 w-80 md:w-96 pointer-events-auto">
              <GisSearchBar onSelectResult={handleSelectSearchResult} />
            </div>

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
