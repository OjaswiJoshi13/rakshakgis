"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Map as MapLibreMap, NavigationControl, GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  GeoJSONFeatureCollection,
  MapLayerConfig,
  SelectedFeatureInfo,
  calculateBounds,
} from "@/types/gis";
import { getMapStyle } from "./mapStyle";
import { DEFAULT_MAP_LAYERS } from "./layerConfig";

// Conceptual layer order (Bottom to Top above basemap)
const STRICT_LAYER_ORDER = [
  "village-boundaries-polygons",
  "red-zones-polygons",
  "candidate-sites-boundaries",
  "village-boundaries-polygons-stroke",
  "red-zones-polygons-stroke",
  "routes-lines",
  "habitations-points",
  "candidate-sites-points",
  "earthquakes-ncs",
  "earthquakes-usgs",
  "hazards-extents",
];

export interface MapCanvasProps {
  /** Map layers configuration */
  layers?: MapLayerConfig[];
  /** Layer visibility map keyed by layer ID */
  layerVisibility?: Record<string, boolean>;
  /** GeoJSON sources data dictionary keyed by sourceId */
  sourcesData?: Record<string, GeoJSONFeatureCollection>;
  /** Callback fired when a feature on an interactive layer is clicked */
  onFeatureSelect?: (feature: SelectedFeatureInfo | null) => void;
  /** Currently selected feature */
  selectedFeature?: SelectedFeatureInfo | null;
  /** Initial center coordinates [longitude, latitude]. If null, auto-fits to loaded geometry */
  initialCenter?: [number, number];
  /** Initial zoom level */
  initialZoom?: number;
  /** Bounding box override to fit [[minLon, minLat], [maxLon, maxLat]] */
  bounds?: [[number, number], [number, number]] | null;
  /** Class name for the outer map wrapper */
  className?: string;
  /** Map accessibility label */
  ariaLabel?: string;
  /** Indicates whether GIS layer data is currently loading */
  isLoading?: boolean;
}

export const MapCanvas: React.FC<MapCanvasProps> = ({
  layers = DEFAULT_MAP_LAYERS,
  layerVisibility = {},
  sourcesData = {},
  onFeatureSelect,
  selectedFeature,
  initialCenter = [0, 20],
  initialZoom = 2,
  bounds,
  className = "w-full h-full min-h-[500px]",
  ariaLabel = "Interactive GIS Disaster Management Map Canvas",
  isLoading = false,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<MapLibreMap | null>(null);
  const [styleVersion, setStyleVersion] = useState<number>(0);
  const [isStyleLoaded, setIsStyleLoaded] = useState<boolean>(false);
  const [mapError, setMapError] = useState<string | null>(null);

  const onFeatureSelectRef = useRef(onFeatureSelect);
  useEffect(() => {
    onFeatureSelectRef.current = onFeatureSelect;
  }, [onFeatureSelect]);

  // Initialize MapLibre GL instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    try {
      const map = new MapLibreMap({
        container: mapContainerRef.current,
        style: getMapStyle(),
        center: initialCenter,
        zoom: initialZoom,
        attributionControl: false,
      });

      // Accessible navigation control
      map.addControl(
        new NavigationControl({ showCompass: true, showZoom: true, visualizePitch: true }),
        "bottom-right"
      );

      // Listen to both load and style.load to reliably handle initial setup and style switches
      const onStyleReady = () => {
        setIsStyleLoaded(true);
        setStyleVersion((v) => v + 1);
        try {
          map.resize();
        } catch {
          // ignore resize errors on early load
        }
      };

      map.on("load", onStyleReady);
      map.on("style.load", onStyleReady);

      map.on("error", (e) => {
        // Suppress non-critical tile 404s, but record serious WebGL/style failures
        if (e && e.error && e.error.message && !e.error.message.includes("404")) {
          setMapError(e.error.message);
        }
      });

      if (typeof map.isStyleLoaded === "function" && map.isStyleLoaded()) {
        onStyleReady();
      }

      mapInstanceRef.current = map;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to initialize WebGL map canvas";
      setMapError(msg);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Resize handler on container dimension changes
  useEffect(() => {
    const container = mapContainerRef.current;
    if (!container) return;

    const resizeObserver = new ResizeObserver(() => {
      if (mapInstanceRef.current && typeof mapInstanceRef.current.resize === "function") {
        mapInstanceRef.current.resize();
      }
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  // Synchronize GeoJSON sources and layers when style is ready or data updates
  useEffect(() => {
    const map = mapInstanceRef.current;
    const isReady = isStyleLoaded || (typeof map?.isStyleLoaded === "function" ? map.isStyleLoaded() : false);
    if (!map || !isReady) return;

    // 1. Add or update GeoJSON Sources
    Object.entries(sourcesData).forEach(([sourceId, collection]) => {
      const safeCollection: GeoJSONFeatureCollection =
        collection && collection.type === "FeatureCollection" && Array.isArray(collection.features)
          ? collection
          : { type: "FeatureCollection", features: [] };

      const existingSource = map.getSource(sourceId) as GeoJSONSource | undefined;
      if (existingSource && typeof existingSource.setData === "function") {
        try {
          existingSource.setData(safeCollection);
        } catch (err) {
          console.error(`[GIS] Error updating source ${sourceId}:`, err);
        }
      } else if (!existingSource) {
        try {
          map.addSource(sourceId, {
            type: "geojson",
            data: safeCollection,
          });
        } catch (err) {
          console.error(`[GIS] Error adding source ${sourceId}:`, err);
        }
      }
    });

    // 2. Add or update Map Layers
    layers.forEach((layerConfig) => {
      if (layerConfig.status !== "available") return;
      const sourceExists = Boolean(map.getSource(layerConfig.sourceId));
      if (!sourceExists) return;

      const existingLayer = map.getLayer(layerConfig.id);
      const isVisible = layerVisibility[layerConfig.id] ?? layerConfig.defaultVisible;

      if (!existingLayer) {
        try {
          const maplibreLayer: any = {
            id: layerConfig.id,
            type: layerConfig.layerType,
            source: layerConfig.sourceId,
            paint: layerConfig.paint,
            layout: {
              ...(layerConfig.layout || {}),
              visibility: isVisible ? "visible" : "none",
            },
          };
          map.addLayer(maplibreLayer);

          // Click interaction for feature selection
          map.on("click", layerConfig.id, (e) => {
            if (!e.features || e.features.length === 0) return;
            const feat = e.features[0];
            const coordinates: [number, number] = [e.lngLat.lng, e.lngLat.lat];

            onFeatureSelectRef.current?.({
              id: (feat.id ?? feat.properties?.id ?? "unknown") as string | number,
              layerId: layerConfig.id,
              layerCategory: layerConfig.category,
              geometryType: feat.geometry.type,
              coordinates,
              properties: (feat.properties as Record<string, unknown>) || {},
            });
          });

          // Pointer cursor on hover
          map.on("mouseenter", layerConfig.id, () => {
            map.getCanvas().style.cursor = "pointer";
          });
          map.on("mouseleave", layerConfig.id, () => {
            map.getCanvas().style.cursor = "";
          });
        } catch (err) {
          console.error(`[GIS Layer Error] Failed to add layer ${layerConfig.id}:`, err);
        }
      } else {
        // Layer exists: update visibility
        try {
          map.setLayoutProperty(
            layerConfig.id,
            "visibility",
            isVisible ? "visible" : "none"
          );
        } catch (err) {
          console.error(`[GIS Layer Error] Failed to update visibility for ${layerConfig.id}:`, err);
        }
      }

      // 3. Add companion high-contrast boundary stroke for polygon fills
      if (layerConfig.layerType === "fill") {
        const strokeLayerId = `${layerConfig.id}-stroke`;
        const existingStroke = map.getLayer(strokeLayerId);
        if (!existingStroke) {
          try {
            const outlineColor =
              layerConfig.id === "red-zones-polygons"
                ? "#b91c1c"
                : ((layerConfig.paint as any)?.["fill-outline-color"] || "#1d4ed8");
            const strokeLayer: any = {
              id: strokeLayerId,
              type: "line",
              source: layerConfig.sourceId,
              paint: {
                "line-color": outlineColor,
                "line-width": layerConfig.id === "red-zones-polygons" ? 3 : 2,
                "line-opacity": 0.95,
                ...(layerConfig.id === "red-zones-polygons" ? { "line-dasharray": [3, 1] } : {}),
              },
              layout: {
                visibility: isVisible ? "visible" : "none",
              },
            };
            map.addLayer(strokeLayer);
          } catch (err) {
            console.error(`[GIS Layer Error] Failed to add companion stroke layer ${strokeLayerId}:`, err);
          }
        } else {
          try {
            map.setLayoutProperty(
              strokeLayerId,
              "visibility",
              isVisible ? "visible" : "none"
            );
          } catch (err) {
            console.error(`[GIS Layer Error] Failed to update stroke layer ${strokeLayerId} visibility:`, err);
          }
        }
      }
    });

    // 4. Enforce strict layer rendering order (bottom-to-top)
    for (const layerId of STRICT_LAYER_ORDER) {
      if (map.getLayer(layerId)) {
        try {
          map.moveLayer(layerId);
        } catch {
          // moveLayer collision safely guarded
        }
      }
    }

    // 5. Development Diagnostics (Console only, not visible in officer UI)
    if (process.env.NODE_ENV !== "production") {
      const vbCount = sourcesData["village-boundaries-source"]?.features?.length || 0;
      const vCount = sourcesData["habitations-source"]?.features?.length || 0;
      const rzCount = sourcesData["red-zones-source"]?.features?.length || 0;
      const rtCount = sourcesData["routes-source"]?.features?.length || 0;
      const csCount = sourcesData["candidate-sites-source"]?.features?.length || 0;
      console.log(`[GIS] village_boundaries: ${vbCount} Polygon features`);
      console.log(`[GIS] villages: ${vCount} Point features`);
      console.log(`[GIS] red_zones: ${rzCount} MultiPolygon features`);
      console.log(`[GIS] routes: ${rtCount} LineString features`);
      console.log(`[GIS] candidate_sites: ${csCount} Point features`);
    }
  }, [styleVersion, isStyleLoaded, sourcesData, layers, layerVisibility]);

  // Fit bounds when bounds prop changes or geometry updates
  useEffect(() => {
    const map = mapInstanceRef.current;
    const isReady = isStyleLoaded || (typeof map?.isStyleLoaded === "function" ? map.isStyleLoaded() : false);
    if (!map || !isReady) return;

    if (bounds) {
      try {
        map.fitBounds(bounds, { padding: 40, maxZoom: 14, duration: 800 });
      } catch (err) {
        console.error("[GIS] Bounds fitting error:", err);
      }
      return;
    }

    // Auto-calculate bounds from active regional operational sources (strictly excluding macro-seismic catalogs)
    const REGIONAL_OPERATIONAL_SOURCES = [
      "village-boundaries-source",
      "habitations-source",
      "candidate-sites-source",
      "candidate-site-boundaries-source",
      "routes-source",
      "red-zones-source",
    ];
    const regionalFeatures = REGIONAL_OPERATIONAL_SOURCES
      .flatMap((sourceKey) => sourcesData[sourceKey]?.features || []);

    const featuresForBounds = regionalFeatures.length > 0
      ? regionalFeatures
      : Object.values(sourcesData).flatMap((c) => c.features);

    const calculated = calculateBounds(featuresForBounds);
    if (calculated) {
      try {
        map.fitBounds(calculated, { padding: 40, maxZoom: 14, duration: 800 });
      } catch (err) {
        console.error("[GIS] Auto bounds fitting error:", err);
      }
    }
  }, [bounds, sourcesData, isStyleLoaded, styleVersion]);

  // Handle map click on empty space to deselect
  const handleMapBackgroundClick = useCallback(
    (e: React.MouseEvent) => {
      // If clicking directly on the canvas without hitting a layer feature, deselect
      if ((e.target as HTMLElement).tagName === "CANVAS" && !selectedFeature) {
        onFeatureSelect?.(null);
      }
    },
    [onFeatureSelect, selectedFeature]
  );

  return (
    <div
      className={`relative rounded-xl overflow-hidden border border-border-subtle bg-surface-panel ${className}`}
      aria-label={ariaLabel}
      role="region"
      onClick={handleMapBackgroundClick}
      data-testid="maplibre-container"
    >
      {/* MapLibre DOM Mount Node */}
      <div
        ref={mapContainerRef}
        className="w-full h-full min-h-[500px]"
        data-testid="maplibre-canvas"
      />

      {/* Loading Overlay */}
      {isLoading && (
        <div
          data-testid="map-loading-overlay"
          className="absolute inset-0 bg-surface-panel/60 backdrop-blur-xs flex items-center justify-center pointer-events-none z-20"
        >
          <div className="bg-surface-elevated border border-border-subtle px-4 py-2.5 rounded-lg text-xs font-mono text-text-primary flex items-center gap-2.5 shadow-xl">
            <span className="w-3.5 h-3.5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
            <span>Updating Spatial Layers...</span>
          </div>
        </div>
      )}

      {/* Map Error Banner */}
      {mapError && (
        <div
          data-testid="map-error-banner"
          className="absolute top-4 left-4 right-4 z-30 bg-red-50 dark:bg-red-950/90 border border-red-200 dark:border-red-800 text-red-900 dark:text-red-200 px-4 py-3 rounded-lg text-xs font-mono flex items-center justify-between shadow-md"
        >
          <div className="flex items-center gap-2">
            <span className="text-red-700 dark:text-red-400 font-bold">MAP ENGINE NOTICE:</span>
            <span>{mapError}</span>
          </div>
          <button
            onClick={() => setMapError(null)}
            className="text-red-400 hover:text-red-100 px-2 py-0.5"
            aria-label="Dismiss map error"
          >
            &times;
          </button>
        </div>
      )}
    </div>
  );
};
