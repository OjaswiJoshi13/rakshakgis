"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import {
  useApiQuery,
  fetchMapLayers,
} from "@/lib/api";
import { useOperational } from "@/context/OperationalContext";
import { ResponseEnvelope } from "@/types/api";
import {
  GeoJSONFeatureCollection,
  SelectedFeatureInfo,
  calculateBounds,
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
  const lastFittedRegionRef = useRef<string | null>(null);
  const [layerVisibility, setLayerVisibility] = useState<Record<string, boolean>>({
    "village-boundaries-polygons": true,
    "habitations-points": true,
    "earthquakes-ncs": true,
    "earthquakes-usgs": true,
    "candidate-sites-points": true,
    "candidate-sites-boundaries": false,
    "routes-lines": true,
    "red-zones-polygons": true,
    "hazards-extents": false,
  });

  // Reset region-specific UI state on activeRegion transition to prevent stale feature/viewport leak
  useEffect(() => {
    setSelectedFeature(null);
    setViewportBounds(null);
    lastFittedRegionRef.current = null;
  }, [activeRegion]);

  // Canonical Vector Map Layers via GET /map/layers?region_id=...
  // Strictly consumes real Survey of India cadastral boundaries (150), Census habitations (188),
  // NCS earthquakes (150), live USGS earthquakes, candidate sites (12), routes (53), and red zones (7).
  // No synthetic 40-village or fixture fallback is permitted.
  const effectiveRegion = activeRegion || "himalayan_pilot";
  const {
    data: mapLayersEnvelope,
    isLoading: mapLayersLoading,
    isError: mapLayersError,
    error: mapLayersErrObj,
    refetch: refetchMapLayers,
  } = useApiQuery<ResponseEnvelope<Record<string, any>>>(
    `gis-map-layers-${effectiveRegion}`,
    (signal) => fetchMapLayers(undefined, effectiveRegion, signal),
    { cacheTtlMs: 60000 }
  );

  const emptyFeatureCollection: GeoJSONFeatureCollection = useMemo(
    () => ({ type: "FeatureCollection", features: [] }),
    []
  );

  // Directly bind authoritative GeoJSON layers from /map/layers
  const sitesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.sites || mapLayersEnvelope?.data?.candidate_sites;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.sites, mapLayersEnvelope?.data?.candidate_sites, emptyFeatureCollection]);

  const siteBoundariesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.site_boundaries || mapLayersEnvelope?.data?.candidate_site_boundaries;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.site_boundaries, mapLayersEnvelope?.data?.candidate_site_boundaries, emptyFeatureCollection]);

  const routesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.routes;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.routes, emptyFeatureCollection]);

  const redZonesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.red_zones;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.red_zones, emptyFeatureCollection]);

  const villagesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.villages;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.villages, emptyFeatureCollection]);

  const villageBoundariesGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.village_boundaries;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.village_boundaries, emptyFeatureCollection]);

  const earthquakesNcsGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.earthquakes_ncs;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.earthquakes_ncs, emptyFeatureCollection]);

  const earthquakesUsgsGeoJSON = useMemo(() => {
    const layer = mapLayersEnvelope?.data?.earthquakes_usgs;
    if (layer?.features && Array.isArray(layer.features)) {
      return layer as GeoJSONFeatureCollection;
    }
    return emptyFeatureCollection;
  }, [mapLayersEnvelope?.data?.earthquakes_usgs, emptyFeatureCollection]);

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

  // Dynamic feature counts for layer controls.
  // Preserves distinction between unavailable data and genuine zero features:
  // When API errors or data is not yet loaded, counts are undefined and UI displays 'Unavailable'.
  // When API returns empty feature list, count is 0 and UI displays '0 features'.
  const featureCounts: Record<string, number | undefined> = useMemo(() => {
    if (mapLayersError || !mapLayersEnvelope?.data) {
      return {};
    }
    return {
      "village-boundaries-polygons": mapLayersEnvelope.data.village_boundaries?.features?.length,
      "habitations-points": mapLayersEnvelope.data.villages?.features?.length,
      "earthquakes-ncs": mapLayersEnvelope.data.earthquakes_ncs?.features?.length,
      "earthquakes-usgs": mapLayersEnvelope.data.earthquakes_usgs?.features?.length,
      "candidate-sites-points": (mapLayersEnvelope.data.sites || mapLayersEnvelope.data.candidate_sites)?.features?.length,
      "candidate-sites-boundaries": (mapLayersEnvelope.data.site_boundaries || mapLayersEnvelope.data.candidate_site_boundaries)?.features?.length,
      "routes-lines": mapLayersEnvelope.data.routes?.features?.length,
      "red-zones-polygons": mapLayersEnvelope.data.red_zones?.features?.length,
    };
  }, [mapLayersError, mapLayersEnvelope?.data]);

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
      await refetchMapLayers?.();
    } finally {
      setIsRefreshing(false);
    }
  };

  // Compute bounding box across all active operational features
  // Strictly excludes macro-seismic catalogs (NCS/USGS) to prevent nationwide viewport expansion
  const computedBounds = useMemo(() => {
    const operationalFeatures = [
      ...villageBoundariesGeoJSON.features,
      ...sitesGeoJSON.features,
      ...siteBoundariesGeoJSON.features,
      ...routesGeoJSON.features,
      ...redZonesGeoJSON.features,
      ...villagesGeoJSON.features,
    ];
    if (operationalFeatures.length > 0) {
      const calculated = calculateBounds(operationalFeatures);
      if (calculated) return calculated;
    }
    if (mapLayersEnvelope?.data?.bounds && Array.isArray(mapLayersEnvelope.data.bounds)) {
      return mapLayersEnvelope.data.bounds as [[number, number], [number, number]];
    }
    return null;
  }, [
    villageBoundariesGeoJSON,
    sitesGeoJSON,
    siteBoundariesGeoJSON,
    routesGeoJSON,
    redZonesGeoJSON,
    villagesGeoJSON,
    mapLayersEnvelope?.data?.bounds,
  ]);

  // Automatically fit viewport to active region features when data arrives or region changes
  useEffect(() => {
    if (computedBounds && lastFittedRegionRef.current !== effectiveRegion) {
      setViewportBounds([[...computedBounds[0]], [...computedBounds[1]]]);
      lastFittedRegionRef.current = effectiveRegion;
    }
  }, [computedBounds, effectiveRegion]);

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

  const isMapLoading = mapLayersLoading;
  const hasMapErrors = mapLayersError;

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
                <strong className="text-amber-700 dark:text-amber-400">Layer Notice:</strong> Spatial layers could
                not be retrieved from backend: {mapLayersErrObj?.message || "Not available in source"}. Available layers remain operational.
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
