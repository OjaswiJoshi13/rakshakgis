import type { StyleSpecification } from "maplibre-gl";

/**
 * Credential-free default basemap style using public OpenStreetMap raster tiles.
 * Designed for offline or zero-credential DEMO / LIVE operations without external API keys.
 */
export const CREDENTIAL_FREE_OSM_STYLE: StyleSpecification = {
  version: 8,
  name: "RakshakGIS Neutral OpenStreetMap Basemap",
  sources: {
    "osm-tiles": {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [
    {
      id: "osm-tiles-layer",
      type: "raster",
      source: "osm-tiles",
      minzoom: 0,
      maxzoom: 19,
      paint: {
        "raster-opacity": 0.85,
        "raster-saturation": -0.15,
      },
    },
  ],
};

/**
 * Resolves configured map style.
 * Uses NEXT_PUBLIC_MAP_STYLE environment variable when provided, falling back to credential-free OSM tiles.
 */
export function getMapStyle(): string | StyleSpecification {
  if (
    typeof process !== "undefined" &&
    process.env &&
    process.env.NEXT_PUBLIC_MAP_STYLE &&
    process.env.NEXT_PUBLIC_MAP_STYLE.trim().length > 0
  ) {
    return process.env.NEXT_PUBLIC_MAP_STYLE.trim();
  }
  return CREDENTIAL_FREE_OSM_STYLE;
}
