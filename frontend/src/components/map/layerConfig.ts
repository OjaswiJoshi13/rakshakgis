import { MapLayerConfig } from "@/types/gis";

/**
 * Standard Layer Registry for the RakshakGIS Map Canvas.
 * Only layers with actual backend endpoints are marked 'available'.
 * Missing backend layers are declared with explicit pending dependency notes to prevent fake data.
 */
export const DEFAULT_MAP_LAYERS: MapLayerConfig[] = [
  {
    id: "candidate-sites-points",
    name: "Candidate Safe Havens",
    category: "candidate_sites",
    description: "Verified relocation safe havens evaluated against slope, buffers, and capacity.",
    sourceId: "candidate-sites-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: true,
    status: "available",
    paint: {
      "circle-radius": 7,
      "circle-color": [
        "match",
        ["get", "status"],
        "active",
        "#10b981", // Emerald 500
        "approved",
        "#38bdf8", // Sky 400
        "proposed",
        "#fbbf24", // Amber 400
        "rejected",
        "#f43f5e", // Rose 500
        "#94a3b8", // Slate 400 fallback
      ],
      "circle-stroke-width": 2,
      "circle-stroke-color": "#090d16",
    },
  },
  {
    id: "candidate-sites-boundaries",
    name: "Safe Haven Boundaries",
    category: "candidate_sites",
    description: "Spatial boundary polygons for candidate safe havens where surveyed.",
    sourceId: "candidate-site-boundaries-source",
    layerType: "fill",
    geometryType: "Polygon",
    defaultVisible: true,
    status: "available",
    paint: {
      "fill-color": "#38bdf8",
      "fill-opacity": 0.2,
      "fill-outline-color": "#0284c7",
    },
  },
  {
    id: "routes-lines",
    name: "Evacuation Corridors",
    category: "routes",
    description: "Dijkstra-evaluated evacuation, alternate, and relief road networks.",
    sourceId: "routes-source",
    layerType: "line",
    geometryType: "LineString",
    defaultVisible: true,
    status: "available",
    paint: {
      "line-width": 3.5,
      "line-color": [
        "case",
        ["get", "is_blocked"],
        "#ef4444", // Red 500 for blocked
        [
          "match",
          ["get", "route_type"],
          "evacuation",
          "#10b981", // Emerald 500
          "alternate",
          "#f59e0b", // Amber 500
          "relief",
          "#818cf8", // Indigo 400
          "#38bdf8", // Sky 400
        ],
      ],
    },
    layout: {
      "line-cap": "round",
      "line-join": "round",
    },
  },
  {
    id: "habitations-points",
    name: "Monitored Habitations",
    category: "habitations",
    description: "Settlements and habitations undergoing vulnerability and risk scoring.",
    sourceId: "habitations-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: false,
    status: "pending_dependency",
    pendingNote: "Pending Chunk M5-06 (Village Vulnerability Analysis UI)",
    paint: {
      "circle-radius": 6,
      "circle-color": "#f59e0b",
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "#090d16",
    },
  },
  {
    id: "red-zones-polygons",
    name: "Permanent & Dynamic Red Zones",
    category: "red_zones",
    description: "Active high-hazard demarcation perimeters requiring officer review.",
    sourceId: "red-zones-source",
    layerType: "fill",
    geometryType: "Polygon",
    defaultVisible: false,
    status: "pending_dependency",
    pendingNote: "Pending Chunk M5-07 (GIS API Integration & GeoJSON Layers)",
    paint: {
      "fill-color": "#dc2626",
      "fill-opacity": 0.35,
      "fill-outline-color": "#b91c1c",
    },
  },
  {
    id: "hazards-extents",
    name: "Hazard Footprints & Observations",
    category: "hazards",
    description: "Active landslide scars, riverine flood zones, and telemetry observation stations.",
    sourceId: "hazards-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: false,
    status: "pending_dependency",
    pendingNote: "Pending Real-Time Hazards Telemetry Backend Integration",
    paint: {
      "circle-radius": 5,
      "circle-color": "#ea580c",
      "circle-stroke-width": 1,
      "circle-stroke-color": "#ffffff",
    },
  },
];

/**
 * Active Map Layers Registry for GIS Command Center (Chunk M5-07).
 * Activates real Survey of India village boundaries, habitations, NCS and USGS earthquakes,
 * and Red Zones with deterministic styling.
 */
export const GIS_ACTIVE_MAP_LAYERS: MapLayerConfig[] = [
  {
    id: "village-boundaries-polygons",
    name: "Survey of India Village Boundaries",
    category: "village_boundaries",
    description: "Official Survey of India revenue village cadastral boundaries with Census 2011 demographics.",
    sourceId: "village-boundaries-source",
    layerType: "fill",
    geometryType: "Polygon",
    defaultVisible: true,
    status: "available",
    paint: {
      "fill-color": [
        "interpolate",
        ["linear"],
        ["coalesce", ["get", "composite_risk"], 0],
        0, "#10b981",    // Low risk: Emerald
        35, "#38bdf8",   // Moderate-Low: Sky
        55, "#fbbf24",   // Moderate: Amber
        75, "#ea580c",   // High: Orange
        88, "#dc2626"    // Critical: Red
      ],
      "fill-opacity": 0.22,
      "fill-outline-color": "#475569",
    },
  },
  {
    id: "habitations-points",
    name: "Census Habitation Centroids",
    category: "habitations",
    description: "Census 2011 habitations and settlements undergoing continuous risk scoring.",
    sourceId: "habitations-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: true,
    status: "available",
    paint: {
      "circle-radius": 5.5,
      "circle-color": "#f59e0b",
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "#090d16",
    },
  },
  {
    id: "earthquakes-ncs",
    name: "Historical Earthquakes (NCS)",
    category: "earthquakes",
    description: "National Center for Seismology recorded events (1991–2024, Chamoli M6.8 & regional).",
    sourceId: "earthquakes-ncs-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: true,
    status: "available",
    paint: {
      "circle-radius": [
        "interpolate",
        ["linear"],
        ["coalesce", ["get", "magnitude"], 3.0],
        2.5, 4,
        4.5, 7,
        6.8, 14
      ],
      "circle-color": "#dc2626",
      "circle-opacity": 0.75,
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "#fee2e2",
    },
  },
  {
    id: "earthquakes-usgs",
    name: "Live Earthquakes (USGS)",
    category: "earthquakes",
    description: "Real-time seismic telemetry from USGS Earthquake Hazards Program.",
    sourceId: "earthquakes-usgs-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: true,
    status: "available",
    paint: {
      "circle-radius": 6,
      "circle-color": "#9333ea",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#faf5ff",
    },
  },
  {
    id: "candidate-sites-points",
    name: "Candidate Safe Havens",
    category: "candidate_sites",
    description: "Verified relocation safe havens evaluated against slope, buffers, and capacity.",
    sourceId: "candidate-sites-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: true,
    status: "available",
    paint: {
      "circle-radius": 7,
      "circle-color": [
        "match",
        ["get", "status"],
        "active",
        "#10b981", // Emerald 500
        "approved",
        "#38bdf8", // Sky 400
        "proposed",
        "#fbbf24", // Amber 400
        "rejected",
        "#f43f5e", // Rose 500
        "#94a3b8", // Slate 400 fallback
      ],
      "circle-stroke-width": 2,
      "circle-stroke-color": "#090d16",
    },
  },
  {
    id: "candidate-sites-boundaries",
    name: "Safe Haven Boundaries",
    category: "candidate_sites",
    description: "Spatial boundary polygons for candidate safe havens where surveyed.",
    sourceId: "candidate-site-boundaries-source",
    layerType: "fill",
    geometryType: "Polygon",
    defaultVisible: true,
    status: "available",
    paint: {
      "fill-color": "#38bdf8",
      "fill-opacity": 0.2,
      "fill-outline-color": "#0284c7",
    },
  },
  {
    id: "routes-lines",
    name: "Evacuation Corridors",
    category: "routes",
    description: "Dijkstra-evaluated evacuation, alternate, and relief road networks.",
    sourceId: "routes-source",
    layerType: "line",
    geometryType: "LineString",
    defaultVisible: true,
    status: "available",
    paint: {
      "line-width": 3.5,
      "line-color": [
        "case",
        ["get", "is_blocked"],
        "#ef4444", // Red 500 for blocked
        [
          "match",
          ["get", "route_type"],
          "evacuation",
          "#10b981", // Emerald 500
          "alternate",
          "#f59e0b", // Amber 500
          "relief",
          "#818cf8", // Indigo 400
          "#38bdf8", // Sky 400
        ],
      ],
    },
    layout: {
      "line-cap": "round",
      "line-join": "round",
    },
  },
  {
    id: "red-zones-polygons",
    name: "Permanent & Dynamic Red Zones",
    category: "red_zones",
    description: "Active high-hazard demarcation perimeters requiring officer review.",
    sourceId: "red-zones-source",
    layerType: "fill",
    geometryType: "MultiPolygon",
    defaultVisible: true,
    status: "available",
    paint: {
      "fill-color": [
        "match",
        ["get", "danger_level"],
        "uninhabitable",
        "#7f1d1d",
        "critical",
        "#dc2626",
        "very_high",
        "#ea580c",
        "#b91c1c",
      ],
      "fill-opacity": 0.4,
      "fill-outline-color": "#7f1d1d",
    },
  },
  {
    id: "hazards-extents",
    name: "Hazard Footprints & Observations",
    category: "hazards",
    description: "Active landslide scars, riverine flood zones, and telemetry observation stations.",
    sourceId: "hazards-source",
    layerType: "circle",
    geometryType: "Point",
    defaultVisible: false,
    status: "pending_dependency",
    pendingNote: "Pending Real-Time Hazards Telemetry Backend Integration",
    paint: {
      "circle-radius": 5,
      "circle-color": "#ea580c",
      "circle-stroke-width": 1,
      "circle-stroke-color": "#ffffff",
    },
  },
];
