import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import GisMapPage from "@/app/gis/page";
import { MapCanvas } from "@/components/map/MapCanvas";
import { FeatureDetailPanel } from "@/components/map/FeatureDetailPanel";
import { LayerControlPanel } from "@/components/map/LayerControlPanel";
import { GIS_ACTIVE_MAP_LAYERS, DEFAULT_MAP_LAYERS } from "@/components/map/layerConfig";
import {
  calculateBounds,
  candidateSiteBoundariesToGeoJSON,
  candidateSitesToGeoJSON,
  isValidGeometry,
  isValidLinearRing,
  isValidPosition,
  redZonesToGeoJSON,
  routesToGeoJSON,
  villagesToGeoJSON,
  GeoJSONFeatureCollection,
  GeoJSONMultiPolygonGeometry,
  PermanentRedZoneCandidate,
  RedZoneRead,
  RouteRead,
  SelectedFeatureInfo,
  VillageRead,
} from "@/types/gis";
import { CandidateSiteRead } from "@/types/dashboard";
import {
  apiClient,
  apiCache,
  fetchCandidateSites,
  fetchRoutes,
  fetchRedZones,
  fetchVillages,
} from "@/lib/api";
import { AuthProvider } from "@/context/AuthContext";
import { OperationalProvider } from "@/context/OperationalContext";
import * as authService from "@/lib/auth";

const mockOfficerUser = {
  id: 1,
  username: "district_collector_chamoli",
  email: "collector@chamoli.gov.in",
  full_name: "District Collector Chamoli",
  role: "district_officer" as const,
  department: "District Administration",
  is_active: true,
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-01T00:00:00Z",
};

// Mock ResizeObserver for jsdom
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock MapLibre GL
const mockAddSource = vi.fn();
const mockAddLayer = vi.fn();
const mockSetData = vi.fn();
const mockSetLayoutProperty = vi.fn();
const mockMapRemove = vi.fn();
const mockFitBounds = vi.fn();
const mockLayerListeners: Record<string, (e: unknown) => void> = {};

vi.mock("maplibre-gl", () => {
  class MockMap {
    container: HTMLElement;
    style: unknown;
    center: unknown;
    zoom: unknown;
    sources: Record<string, { setData: (data: unknown) => void }> = {};
    layers: Record<string, unknown> = {};
    listeners: Record<string, ((data?: unknown) => void)[]> = {};

    constructor(options: { container: HTMLElement; style: unknown; center: unknown; zoom: unknown }) {
      this.container = options.container;
      this.style = options.style;
      this.center = options.center;
      this.zoom = options.zoom;
      setTimeout(() => {
        this.emit("load");
      }, 0);
    }

    on(event: string, ...args: unknown[]) {
      const handler = args[args.length - 1] as (data?: unknown) => void;
      if (args.length === 2 && typeof args[0] === "string") {
        const layerId = args[0];
        mockLayerListeners[`${event}:${layerId}`] = handler;
      }
      if (!this.listeners[event]) this.listeners[event] = [];
      this.listeners[event].push(handler);
      return this;
    }

    emit(event: string, data?: unknown) {
      if (this.listeners[event]) {
        this.listeners[event].forEach((fn) => fn(data));
      }
    }

    addControl() {
      return this;
    }

    remove() {
      mockMapRemove();
    }

    getSource(id: string) {
      return this.sources[id];
    }

    addSource(id: string, source: { type: string; data: unknown }) {
      mockAddSource(id, source);
      this.sources[id] = {
        setData: (data: unknown) => {
          mockSetData(id, data);
        },
      };
      return this;
    }

    getLayer(id: string) {
      return this.layers[id];
    }

    addLayer(layer: { id: string }) {
      mockAddLayer(layer);
      this.layers[layer.id] = layer;
      return this;
    }

    setLayoutProperty(layerId: string, name: string, value: unknown) {
      mockSetLayoutProperty(layerId, name, value);
    }

    fitBounds(bounds: unknown, options: unknown) {
      mockFitBounds(bounds, options);
    }

    resize() {}

    getCanvas() {
      return { style: { cursor: "" } };
    }
  }

  class MockNavigationControl {}

  return {
    Map: MockMap,
    NavigationControl: MockNavigationControl,
  };
});

describe("GIS API Integration & GeoJSON Layers (Chunk M5-07)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiCache.clear();
    Object.keys(mockLayerListeners).forEach((k) => delete mockLayerListeners[k]);
    vi.spyOn(authService, "getStoredToken").mockReturnValue("mock-valid-jwt");
    vi.spyOn(authService, "getStoredTokenExpiry").mockReturnValue(Date.now() + 3600000);
    vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);
  });

  // =========================================================================
  // 1. GIS API request uses existing API client
  // =========================================================================
  describe("1. GIS API Service Network Operations", () => {
    it("dispatches fetchCandidateSites via apiClient with correct query parameters", async () => {
      const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { total: 0, page: 1, page_size: 20, total_pages: 0, has_next: false, has_prev: false },
      });

      const abortCtrl = new AbortController();
      await fetchCandidateSites({ page: 2, page_size: 10, district_id: 5 }, abortCtrl.signal);

      expect(getSpy).toHaveBeenCalledWith("/sites", {
        params: { page: 2, page_size: 10, district_id: 5 },
        signal: abortCtrl.signal,
      });
    });

    it("dispatches fetchRoutes via apiClient with correct endpoint and parameters", async () => {
      const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { total: 0, page: 1, page_size: 20, total_pages: 0, has_next: false, has_prev: false },
      });

      await fetchRoutes({ origin_village_id: 101, is_blocked: false });

      expect(getSpy).toHaveBeenCalledWith("/routes", {
        params: { origin_village_id: 101, is_blocked: false },
        signal: undefined,
      });
    });

    it("dispatches fetchRedZones via apiClient for M3-10 contracts", async () => {
      const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { total: 0, page: 1, page_size: 20, total_pages: 0, has_next: false, has_prev: false },
      });

      await fetchRedZones({ zone_type: "landslide_danger", is_active: false });

      expect(getSpy).toHaveBeenCalledWith("/red-zones", {
        params: { zone_type: "landslide_danger", is_active: false },
        signal: undefined,
      });
    });

    it("dispatches fetchVillages via apiClient for habitation settlements", async () => {
      const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({
        success: true,
        data: [],
        pagination: { total: 0, page: 1, page_size: 20, total_pages: 0, has_next: false, has_prev: false },
      });

      await fetchVillages({ district_id: 1, page: 1 });

      expect(getSpy).toHaveBeenCalledWith("/villages", {
        params: { district_id: 1, page: 1 },
        signal: undefined,
      });
    });
  });

  // =========================================================================
  // 2, 3, 4, 10, 12. GeoJSON Contracts & Validation
  // =========================================================================
  describe("2. GeoJSON Contracts, Validation & Safe Data Transformation", () => {
    const sampleMultiPolygon: GeoJSONMultiPolygonGeometry = {
      type: "MultiPolygon",
      coordinates: [
        [
          [
            [79.4, 30.4],
            [79.5, 30.4],
            [79.5, 30.5],
            [79.4, 30.5],
            [79.4, 30.4],
          ],
        ],
      ],
    };

    it("accepts and transforms valid RedZoneRead into GeoJSON FeatureCollection without recalculating", () => {
      const backendRedZone: RedZoneRead = {
        id: "RZ-CHAMOLI-001",
        name: "Joshimath Fissure Exclusion Zone",
        zone_type: "active_subsidence",
        danger_level: "uninhabitable",
        geometry: sampleMultiPolygon,
        area_sq_km: 4.85,
        is_active: false,
        contributing_village_ids: ["VILL-01", "VILL-02"],
        explainability: {
          decision_reason: "Active ground subsidence detected with multiple structural fissures",
          governance_notice: "PROPOSED CANDIDATE ONLY: Statutory declaration requires officer review",
        },
      };

      const collection = redZonesToGeoJSON([backendRedZone]);

      expect(collection.type).toBe("FeatureCollection");
      expect(collection.features.length).toBe(1);
      const feature = collection.features[0];
      expect(feature.id).toBe("RZ-CHAMOLI-001");
      expect(feature.geometry.type).toBe("MultiPolygon");
      // Preserves backend-produced values exactly
      expect(feature.properties.area_sq_km).toBe(4.85);
      expect(feature.properties.danger_level).toBe("uninhabitable");
      expect(feature.properties.zone_type).toBe("active_subsidence");
      expect(feature.properties.contributing_village_ids).toEqual(["VILL-01", "VILL-02"]);
      expect(feature.properties.category).toBe("red_zones");
    });

    it("accepts and transforms M3-10 PermanentRedZoneCandidate models", () => {
      const candidate: PermanentRedZoneCandidate = {
        candidate_id: "CAND-RZ-09",
        name: "Helang Landslide Perimeter",
        status: "proposed",
        zone_type: "landslide_danger",
        danger_level: "critical",
        geometry: sampleMultiPolygon,
        area_sq_km: 2.31,
        contributing_village_ids: ["VILL-HELANG"],
        is_candidate: true,
        is_active: false,
      };

      const collection = redZonesToGeoJSON([candidate]);

      expect(collection.features.length).toBe(1);
      expect(collection.features[0].id).toBe("CAND-RZ-09");
      expect(collection.features[0].properties.danger_level).toBe("critical");
    });

    it("handles empty FeatureCollection gracefully", () => {
      const collection = redZonesToGeoJSON([]);
      expect(collection.type).toBe("FeatureCollection");
      expect(collection.features).toEqual([]);
    });

    it("safely drops malformed or unclosed polygon rings without generating fake coordinates or [0,0]", () => {
      const unclosedPolygon = {
        type: "Polygon" as const,
        coordinates: [
          [
            [79.4, 30.4],
            [79.5, 30.4],
            [79.5, 30.5],
            [79.4, 30.5],
            // Missing closure [79.4, 30.4]
          ],
        ],
      };

      const badRedZone: RedZoneRead = {
        id: "BAD-RZ-01",
        name: "Malformed Zone",
        zone_type: "landslide_danger",
        danger_level: "critical",
        geometry: unclosedPolygon as any,
      };

      const collection = redZonesToGeoJSON([badRedZone]);
      expect(collection.features.length).toBe(0); // Safely dropped
    });

    it("safely rejects coordinates containing NaN or Infinite values", () => {
      expect(isValidPosition([NaN, 30.5])).toBe(false);
      expect(isValidPosition([79.5, Infinity])).toBe(false);
      expect(isValidPosition([200, 30.5])).toBe(false); // Out of bounds
    });

    it("safely drops villages with invalid coordinates and never generates [0,0] coordinates", () => {
      const villages: VillageRead[] = [
        {
          id: 1,
          name: "Valid Village",
          location: { type: "Point", coordinates: [79.5, 30.5] },
        },
        {
          id: 2,
          name: "Corrupt Village",
          location: { type: "Point", coordinates: [NaN, 30.5] as any },
        },
        {
          id: 3,
          name: "Missing Coord Village",
          location: null as any,
        },
      ];

      const collection = villagesToGeoJSON(villages);
      expect(collection.features.length).toBe(1);
      expect(collection.features[0].id).toBe(1);
      // Verify no feature is placed at [0, 0]
      const allCoords = collection.features.map((f) => f.geometry.coordinates);
      expect(allCoords).not.toContainEqual([0, 0]);
    });

    it("calculates accurate bounding box across MultiPolygon and Point features", () => {
      const rzCollection = redZonesToGeoJSON([
        {
          id: 1,
          name: "RZ 1",
          zone_type: "landslide_danger",
          danger_level: "critical",
          geometry: sampleMultiPolygon,
        },
      ]);
      const vCollection = villagesToGeoJSON([
        {
          id: 1,
          name: "Village 1",
          location: { type: "Point", coordinates: [79.6, 30.6] },
        },
      ]);

      const bounds = calculateBounds([...rzCollection.features, ...vCollection.features]);
      expect(bounds).not.toBeNull();
      expect(bounds![0][0]).toBeCloseTo(79.4);
      expect(bounds![0][1]).toBeCloseTo(30.4);
      expect(bounds![1][0]).toBeCloseTo(79.6);
      expect(bounds![1][1]).toBeCloseTo(30.6);
    });
  });

  // =========================================================================
  // 7, 8, 9. MapLibre Source & Layer Lifecycle
  // =========================================================================
  describe("3. MapLibre Source & Layer Idempotency & Lifecycle", () => {
    it("registers sources and layers exactly once and updates via setData on subsequent renders", async () => {
      const mockSourcesData: Record<string, GeoJSONFeatureCollection> = {
        "candidate-sites-source": { type: "FeatureCollection", features: [] },
        "routes-source": { type: "FeatureCollection", features: [] },
        "red-zones-source": { type: "FeatureCollection", features: [] },
      };

      const { rerender } = render(
        <MapCanvas
          layers={GIS_ACTIVE_MAP_LAYERS}
          layerVisibility={{ "red-zones-polygons": true }}
          sourcesData={mockSourcesData}
        />
      );

      await waitFor(() => {
        expect(mockAddSource).toHaveBeenCalledWith("candidate-sites-source", expect.any(Object));
        expect(mockAddSource).toHaveBeenCalledWith("routes-source", expect.any(Object));
        expect(mockAddSource).toHaveBeenCalledWith("red-zones-source", expect.any(Object));
      });

      const initialSourceCalls = mockAddSource.mock.calls.length;

      // Duplicate re-render with updated data
      const updatedSourcesData: Record<string, GeoJSONFeatureCollection> = {
        ...mockSourcesData,
        "red-zones-source": {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              id: "RZ-1",
              geometry: {
                type: "Polygon",
                coordinates: [
                  [
                    [79.4, 30.4],
                    [79.5, 30.4],
                    [79.5, 30.5],
                    [79.4, 30.5],
                    [79.4, 30.4],
                  ],
                ],
              },
              properties: {},
            },
          ],
        },
      };

      rerender(
        <MapCanvas
          layers={GIS_ACTIVE_MAP_LAYERS}
          layerVisibility={{ "red-zones-polygons": true }}
          sourcesData={updatedSourcesData}
        />
      );

      // Verify no duplicate addSource was called; setData was called instead
      expect(mockAddSource.mock.calls.length).toBe(initialSourceCalls);
      expect(mockSetData).toHaveBeenCalledWith("red-zones-source", updatedSourcesData["red-zones-source"]);
    });

    it("invokes onFeatureSelect when red-zones-polygons layer feature is clicked", async () => {
      const onSelect = vi.fn();
      const mockSourcesData: Record<string, GeoJSONFeatureCollection> = {
        "red-zones-source": { type: "FeatureCollection", features: [] },
      };

      render(
        <MapCanvas
          layers={GIS_ACTIVE_MAP_LAYERS}
          layerVisibility={{ "red-zones-polygons": true }}
          sourcesData={mockSourcesData}
          onFeatureSelect={onSelect}
        />
      );

      await waitFor(() => {
        expect(mockLayerListeners["click:red-zones-polygons"]).toBeDefined();
      });

      // Simulate MapLibre click event
      const clickHandler = mockLayerListeners["click:red-zones-polygons"];
      clickHandler({
        features: [
          {
            id: "RZ-999",
            geometry: { type: "MultiPolygon" },
            properties: {
              name: "Gaurikund Debris Sector",
              danger_level: "critical",
              zone_type: "landslide_danger",
            },
          },
        ],
        lngLat: { lng: 79.5123, lat: 30.5432 },
      });

      expect(onSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "RZ-999",
          layerId: "red-zones-polygons",
          layerCategory: "red_zones",
          coordinates: [79.5123, 30.5432],
        })
      );
    });
  });

  // =========================================================================
  // 11. FeatureDetailPanel Red Zone Inspection
  // =========================================================================
  describe("4. FeatureDetailPanel & Governance Notice Inspection", () => {
    it("renders Red Zone spatial inspector with danger level, threat type, and Rule 12 governance invariant", () => {
      const selectedFeature: SelectedFeatureInfo = {
        id: "RZ-JOSHIMATH-01",
        layerId: "red-zones-polygons",
        layerCategory: "red_zones",
        geometryType: "MultiPolygon",
        coordinates: [79.56, 30.55],
        properties: {
          name: "Joshimath Core Subsidence Zone",
          danger_level: "uninhabitable",
          zone_type: "active_subsidence",
          area_sq_km: 3.42,
          is_active: false,
          contributing_village_ids: ["VILL-101", "VILL-102"],
          governance_notice: "PROPOSED CANDIDATE ONLY: Statutory legal declaration requires officer review (M6-08 workflow).",
        },
      };

      render(<FeatureDetailPanel feature={selectedFeature} onClose={vi.fn()} />);

      expect(screen.getByText(/Red Zone #RZ-JOSHIMATH-01/i)).toBeInTheDocument();
      expect(screen.getByText("Joshimath Core Subsidence Zone")).toBeInTheDocument();
      expect(screen.getByText("uninhabitable")).toBeInTheDocument();
      expect(screen.getByText("active subsidence")).toBeInTheDocument();
      expect(screen.getByText("3.42 km²")).toBeInTheDocument();
      expect(screen.getByText("Proposed Candidate")).toBeInTheDocument();
      expect(screen.getByText("2 Habitations")).toBeInTheDocument();
      expect(screen.getByText(/RULE 12 GOVERNANCE INVARIANT/i)).toBeInTheDocument();
      expect(screen.getByText(/PROPOSED CANDIDATE ONLY/i)).toBeInTheDocument();
    });
  });

  // =========================================================================
  // 5, 6. GisMapPage Full Integration & Error Handling
  // =========================================================================
  describe("5. GisMapPage Integration, Loading, and Partial Failure States", () => {
    it("renders full GIS map with candidate sites, routes, and red zones", async () => {
      vi.spyOn(apiClient, "get").mockImplementation((url) => {
        if (url.includes("/sites")) {
          return Promise.resolve({
            success: true,
            data: [
              {
                id: 1,
                name: "Safe Site Pipalkoti",
                district_id: 1,
                location: { type: "Point", coordinates: [79.4, 30.4] },
                boundary: null,
                status: "approved",
              },
            ],
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          });
        }
        if (url.includes("/routes")) {
          return Promise.resolve({
            success: true,
            data: [
              {
                id: 10,
                name: "NH-7 Evacuation Corridor",
                path: {
                  type: "LineString",
                  coordinates: [
                    [79.4, 30.4],
                    [79.5, 30.5],
                  ],
                },
                distance_km: 14.5,
                route_type: "evacuation",
                is_blocked: false,
              },
            ],
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          });
        }
        if (url.includes("/red-zones")) {
          return Promise.resolve({
            success: true,
            data: [
              {
                id: "RZ-1",
                name: "High Slope Buffer Zone",
                zone_type: "landslide_danger",
                danger_level: "critical",
                geometry: {
                  type: "MultiPolygon",
                  coordinates: [
                    [
                      [
                        [79.4, 30.4],
                        [79.5, 30.4],
                        [79.5, 30.5],
                        [79.4, 30.5],
                        [79.4, 30.4],
                      ],
                    ],
                  ],
                },
                area_sq_km: 1.5,
                is_active: false,
              },
            ],
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          });
        }
        return Promise.resolve({
          success: true,
          data: [],
          pagination: { total: 0, page: 1, page_size: 50, total_pages: 0, has_next: false, has_prev: false },
        });
      });

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider>
            <GisMapPage />
          </OperationalProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Command GIS Map Canvas" })).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText(/1 Havens/i)).toBeInTheDocument();
        expect(screen.getByText(/1 Corridors/i)).toBeInTheDocument();
        expect(screen.getByText(/1 Red Zones/i)).toBeInTheDocument();
      });
    });

    it("displays section-level user-safe error notice when an endpoint fails without crashing map", async () => {
      vi.spyOn(apiClient, "get").mockImplementation((url) => {
        if (url.includes("/red-zones")) {
          return Promise.reject(new Error("Red Zones backend service temporarily unavailable"));
        }
        return Promise.resolve({
          success: true,
          data: [],
          pagination: { total: 0, page: 1, page_size: 50, total_pages: 0, has_next: false, has_prev: false },
        });
      });

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider>
            <GisMapPage />
          </OperationalProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId("gis-error-banner")).toBeInTheDocument();
        expect(screen.getByText(/Some spatial layers could not be retrieved/i)).toBeInTheDocument();
        expect(screen.getByText(/Red Zones: Red Zones backend service temporarily unavailable/i)).toBeInTheDocument();
      });

      // Map canvas still renders operational
      expect(screen.getByTestId("maplibre-canvas")).toBeInTheDocument();
    });

    it("displays loading state overlay when spatial layers are fetching", () => {
      // Simulate pending query
      vi.spyOn(apiClient, "get").mockImplementation(() => new Promise(() => {}));

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider>
            <GisMapPage />
          </OperationalProvider>
        </AuthProvider>
      );

      expect(screen.getByTestId("map-loading-overlay")).toBeInTheDocument();
      expect(screen.getByText("Updating Spatial Layers...")).toBeInTheDocument();
    });

    it("toggles Red Zone layer visibility in LayerControlPanel", () => {
      const onToggle = vi.fn();
      render(
        <LayerControlPanel
          layers={GIS_ACTIVE_MAP_LAYERS}
          layerVisibility={{ "red-zones-polygons": true }}
          onToggleLayer={onToggle}
          featureCounts={{ "red-zones-polygons": 3 }}
        />
      );

      expect(screen.getByText("Permanent & Dynamic Red Zones")).toBeInTheDocument();
      expect(screen.getByText("3 features")).toBeInTheDocument();
      const checkbox = screen.getByLabelText("Toggle visibility of Permanent & Dynamic Red Zones");
      expect(checkbox).not.toBeDisabled();
      fireEvent.click(checkbox);
      expect(onToggle).toHaveBeenCalledWith("red-zones-polygons");
    });
  });
});
