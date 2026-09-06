import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { MapCanvas } from "@/components/map/MapCanvas";
import { LayerControlPanel } from "@/components/map/LayerControlPanel";
import { FeatureDetailPanel } from "@/components/map/FeatureDetailPanel";
import { MapHeader } from "@/components/map/MapHeader";
import GisMapPage from "@/app/gis/page";
import { DEFAULT_MAP_LAYERS } from "@/components/map/layerConfig";
import { getMapStyle, CREDENTIAL_FREE_OSM_STYLE } from "@/components/map/mapStyle";
import {
  calculateBounds,
  candidateSiteBoundariesToGeoJSON,
  candidateSitesToGeoJSON,
  isValidGeometry,
  isValidLinearRing,
  isValidPosition,
  routesToGeoJSON,
  GeoJSONFeature,
  GeoJSONMultiPolygonGeometry,
  SelectedFeatureInfo,
} from "@/types/gis";
import { CandidateSiteRead } from "@/types/dashboard";
import { RouteRead } from "@/types/gis";
import { AuthProvider } from "@/context/AuthContext";
import { OperationalProvider, useOperational } from "@/context/OperationalContext";
import * as authService from "@/lib/auth";
import * as apiModule from "@/lib/api";

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

// Mock maplibre-gl
const mockMapRemove = vi.fn();
const mockFitBounds = vi.fn();
const mockSetLayoutProperty = vi.fn();
const mockMapConstructor = vi.fn();
const mockLayerListeners: Record<string, (e: unknown) => void> = {};

vi.mock("maplibre-gl", () => {
  class MockMap {
    container: HTMLElement;
    style: unknown;
    center: unknown;
    zoom: unknown;
    sources: Record<string, unknown> = {};
    layers: Record<string, unknown> = {};
    listeners: Record<string, ((data?: unknown) => void)[]> = {};

    constructor(options: { container: HTMLElement; style: unknown; center: unknown; zoom: unknown }) {
      mockMapConstructor(options);
      this.container = options.container;
      this.style = options.style;
      this.center = options.center;
      this.zoom = options.zoom;
      // Trigger load on next tick
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

    resize() {}

    fitBounds(...args: unknown[]) {
      mockFitBounds(...args);
    }

    getSource(id: string) {
      return this.sources[id];
    }

    addSource(id: string, src: unknown) {
      this.sources[id] = src;
      return this;
    }

    getLayer(id: string) {
      return this.layers[id];
    }

    addLayer(layer: { id: string }) {
      this.layers[layer.id] = layer;
      return this;
    }

    setLayoutProperty(...args: unknown[]) {
      mockSetLayoutProperty(...args);
    }

    getCanvas() {
      return { style: {} };
    }
  }

  class MockNavigationControl {}

  return {
    Map: MockMap,
    NavigationControl: MockNavigationControl,
  };
});

const mockCandidateSites: CandidateSiteRead[] = [
  {
    id: 101,
    name: "Safe Haven Pipalkoti Terrace",
    district_id: 1,
    location: { type: "Point", coordinates: [79.4321, 30.4123] },
    boundary: {
      type: "Polygon",
      coordinates: [
        [
          [79.43, 30.41],
          [79.44, 30.41],
          [79.44, 30.42],
          [79.43, 30.42],
          [79.43, 30.41],
        ],
      ],
    },
    area_sq_m: 54000,
    terrain_slope_deg: 9.2,
    elevation_m: 1320,
    status: "approved",
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
];

const mockRoutes: RouteRead[] = [
  {
    id: 501,
    name: "NH-07 Valley Access Corridor",
    origin_village_id: 10,
    origin_village_name: "Sunil Village",
    destination_site_id: 101,
    destination_site_name: "Safe Haven Pipalkoti Terrace",
    path: {
      type: "LineString",
      coordinates: [
        [79.43, 30.41],
        [79.45, 30.42],
        [79.47, 30.44],
      ],
    },
    distance_km: 14.8,
    estimated_travel_time_min: 35,
    route_type: "evacuation",
    is_blocked: false,
    blockage_reason: null,
    elevation_gain_m: 240,
    max_slope_deg: 8.5,
    is_active: true,
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
];

describe("MapLibre GIS Interactive Map Canvas (Chunk M5-05)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiModule.apiCache.clear();
  });

  describe("GeoJSON Validators & Geometry Utilities", () => {
    it("validates coordinates correctly with isValidPosition", () => {
      expect(isValidPosition([78.5, 30.2])).toBe(true);
      expect(isValidPosition([180.0, -90.0])).toBe(true);
      expect(isValidPosition([-181.0, 30.0])).toBe(false);
      expect(isValidPosition([78.5, 95.0])).toBe(false);
      expect(isValidPosition("invalid")).toBe(false);
      expect(isValidPosition([NaN, 30.0])).toBe(false);
    });

    it("guards malformed geometry with isValidGeometry", () => {
      expect(isValidGeometry({ type: "Point", coordinates: [79.0, 30.0] })).toBe(true);
      expect(
        isValidGeometry({
          type: "LineString",
          coordinates: [
            [79.0, 30.0],
            [79.1, 30.1],
          ],
        })
      ).toBe(true);
      // Closed Polygon conforms to RFC 7946
      expect(
        isValidGeometry({
          type: "Polygon",
          coordinates: [
            [
              [79.0, 30.0],
              [79.1, 30.0],
              [79.1, 30.1],
              [79.0, 30.1],
              [79.0, 30.0], // explicitly closed
            ],
          ],
        })
      ).toBe(true);
      // Malformed LineString with only 1 point
      expect(isValidGeometry({ type: "LineString", coordinates: [[79.0, 30.0]] })).toBe(false);
      // Malformed Polygon with < 4 points
      expect(isValidGeometry({ type: "Polygon", coordinates: [[[79.0, 30.0]]] })).toBe(false);
      expect(isValidGeometry(null)).toBe(false);
    });

    it("enforces RFC 7946 linear ring closure for Polygon geometries", () => {
      // Valid closed polygon ring: first point matches last point
      const closedPolygon = {
        type: "Polygon",
        coordinates: [
          [
            [10.0, 20.0],
            [11.0, 20.0],
            [11.0, 21.0],
            [10.0, 21.0],
            [10.0, 20.0],
          ],
        ],
      };
      expect(isValidGeometry(closedPolygon)).toBe(true);
      expect(isValidLinearRing(closedPolygon.coordinates[0])).toBe(true);

      // Unclosed polygon ring: 4 points but endpoint does not match startpoint
      const unclosedPolygon = {
        type: "Polygon",
        coordinates: [
          [
            [10.0, 20.0],
            [11.0, 20.0],
            [11.0, 21.0],
            [10.0, 21.0], // not closed
          ],
        ],
      };
      expect(isValidGeometry(unclosedPolygon)).toBe(false);
      expect(isValidLinearRing(unclosedPolygon.coordinates[0])).toBe(false);
    });

    it("enforces RFC 7946 linear ring closure for MultiPolygon geometries", () => {
      const closedMultiPolygon = {
        type: "MultiPolygon",
        coordinates: [
          [
            [
              [10.0, 20.0],
              [11.0, 20.0],
              [11.0, 21.0],
              [10.0, 21.0],
              [10.0, 20.0],
            ],
          ],
          [
            [
              [30.0, 40.0],
              [31.0, 40.0],
              [31.0, 41.0],
              [30.0, 41.0],
              [30.0, 40.0],
            ],
          ],
        ],
      };
      expect(isValidGeometry(closedMultiPolygon)).toBe(true);

      const unclosedMultiPolygon = {
        type: "MultiPolygon",
        coordinates: [
          [
            [
              [10.0, 20.0],
              [11.0, 20.0],
              [11.0, 21.0],
              [10.0, 21.0], // unclosed ring in polygon 1
            ],
          ],
        ],
      };
      expect(isValidGeometry(unclosedMultiPolygon)).toBe(false);
    });

    it("calculates accurate bounding box with calculateBounds including MultiPolygon", () => {
      const geo = candidateSitesToGeoJSON(mockCandidateSites);
      const bounds = calculateBounds(geo.features);

      expect(bounds).not.toBeNull();
      if (bounds) {
        expect(bounds[0][0]).toBeCloseTo(79.3821, 2); // padded min lon
        expect(bounds[1][0]).toBeCloseTo(79.4821, 2); // padded max lon
      }

      // MultiPolygon bounds calculation
      const multiPolyFeat: GeoJSONFeature<GeoJSONMultiPolygonGeometry> = {
        type: "Feature",
        id: "mp-1",
        geometry: {
          type: "MultiPolygon",
          coordinates: [
            [
              [
                [10.0, 20.0],
                [15.0, 20.0],
                [15.0, 25.0],
                [10.0, 25.0],
                [10.0, 20.0],
              ],
            ],
            [
              [
                [30.0, 40.0],
                [35.0, 40.0],
                [35.0, 45.0],
                [30.0, 45.0],
                [30.0, 40.0],
              ],
            ],
          ],
        },
        properties: {},
      };
      const mpBounds = calculateBounds([multiPolyFeat]);
      expect(mpBounds).toEqual([
        [10.0, 20.0],
        [35.0, 45.0],
      ]);
    });

    it("transforms backend CandidateSites into valid GeoJSON FeatureCollection", () => {
      const geo = candidateSitesToGeoJSON(mockCandidateSites);
      expect(geo.type).toBe("FeatureCollection");
      expect(geo.features).toHaveLength(1);
      expect(geo.features[0].geometry.type).toBe("Point");
      expect(geo.features[0].properties.name).toBe("Safe Haven Pipalkoti Terrace");
      expect(geo.features[0].properties.status).toBe("approved");
    });

    it("transforms backend CandidateSites polygon boundaries into GeoJSON", () => {
      const geo = candidateSiteBoundariesToGeoJSON(mockCandidateSites);
      expect(geo.type).toBe("FeatureCollection");
      expect(geo.features).toHaveLength(1);
      expect(geo.features[0].geometry.type).toBe("Polygon");
      expect(geo.features[0].properties.site_id).toBe(101);
    });

    it("transforms backend Routes into valid GeoJSON FeatureCollection", () => {
      const geo = routesToGeoJSON(mockRoutes);
      expect(geo.type).toBe("FeatureCollection");
      expect(geo.features).toHaveLength(1);
      expect(geo.features[0].geometry.type).toBe("LineString");
      expect(geo.features[0].properties.distance_km).toBe(14.8);
      expect(geo.features[0].properties.is_blocked).toBe(false);
    });
  });

  describe("Basemap Style Configuration", () => {
    it("returns credential-free OpenStreetMap style by default without API keys", () => {
      delete process.env.NEXT_PUBLIC_MAP_STYLE;
      const style = getMapStyle();
      expect(style).toEqual(CREDENTIAL_FREE_OSM_STYLE);
      expect(CREDENTIAL_FREE_OSM_STYLE.sources["osm-tiles"]).toBeDefined();
    });

    it("respects NEXT_PUBLIC_MAP_STYLE when configured", () => {
      process.env.NEXT_PUBLIC_MAP_STYLE = "https://tiles.rakshakgis.gov.in/style.json";
      const style = getMapStyle();
      expect(style).toBe("https://tiles.rakshakgis.gov.in/style.json");
      delete process.env.NEXT_PUBLIC_MAP_STYLE;
    });
  });

  describe("MapCanvas Component", () => {
    it("renders map container and canvas node", () => {
      render(<MapCanvas />);
      expect(screen.getByTestId("maplibre-container")).toBeInTheDocument();
      expect(screen.getByTestId("maplibre-canvas")).toBeInTheDocument();
    });

    it("displays loading indicator when isLoading is true", () => {
      render(<MapCanvas isLoading={true} />);
      expect(screen.getByTestId("map-loading-overlay")).toBeInTheDocument();
      expect(screen.getByText("Updating Spatial Layers...")).toBeInTheDocument();
    });

    it("cleans up map instance on unmount", () => {
      const { unmount } = render(<MapCanvas />);
      unmount();
      expect(mockMapRemove).toHaveBeenCalled();
    });

    it("initializes with a neutral global viewport [0, 20] and zoom 2 by default without hardcoded regional coordinates", () => {
      render(<MapCanvas />);
      expect(mockMapConstructor).toHaveBeenCalledWith(
        expect.objectContaining({
          center: [0, 20],
          zoom: 2,
        })
      );
      // Ensure no Himalayan/Chamoli center coordinates are used as defaults
      expect(mockMapConstructor).not.toHaveBeenCalledWith(
        expect.objectContaining({
          center: [79.5, 30.5],
        })
      );
    });
  });

  describe("LayerControlPanel Component", () => {
    it("renders layer control panel with available and pending layers", () => {
      const onToggle = vi.fn();
      render(
        <LayerControlPanel
          layers={DEFAULT_MAP_LAYERS}
          layerVisibility={{ "candidate-sites-points": true }}
          onToggleLayer={onToggle}
          featureCounts={{ "candidate-sites-points": 5 }}
        />
      );

      expect(screen.getByText("GIS Layer Controls")).toBeInTheDocument();
      expect(screen.getByText("Candidate Safe Havens")).toBeInTheDocument();
      expect(screen.getByText("Evacuation Corridors")).toBeInTheDocument();
      expect(screen.getByText("5 features")).toBeInTheDocument();
      // Pending layers explicitly disclosed
      expect(screen.getByText("Monitored Habitations")).toBeInTheDocument();
      expect(screen.getByText(/Pending Chunk M5-06/i)).toBeInTheDocument();
      expect(screen.getByText(/Pending Chunk M5-07/i)).toBeInTheDocument();
    });

    it("toggles layer visibility when an available layer checkbox is clicked", () => {
      const onToggle = vi.fn();
      render(
        <LayerControlPanel
          layers={DEFAULT_MAP_LAYERS}
          layerVisibility={{ "candidate-sites-points": true }}
          onToggleLayer={onToggle}
        />
      );

      const checkbox = screen.getByLabelText("Toggle visibility of Candidate Safe Havens");
      fireEvent.click(checkbox);
      expect(onToggle).toHaveBeenCalledWith("candidate-sites-points");
    });

    it("disables checkboxes for pending dependency layers to prevent fake data", () => {
      render(
        <LayerControlPanel
          layers={DEFAULT_MAP_LAYERS}
          layerVisibility={{}}
          onToggleLayer={vi.fn()}
        />
      );

      const pendingCheckbox = screen.getByLabelText("Toggle visibility of Monitored Habitations");
      expect(pendingCheckbox).toBeDisabled();
    });
  });

  describe("FeatureDetailPanel Component", () => {
    it("renders candidate site properties accurately from backend data", () => {
      const selectedSite: SelectedFeatureInfo = {
        id: 101,
        layerId: "candidate-sites-points",
        layerCategory: "candidate_sites",
        geometryType: "Point",
        coordinates: [79.4321, 30.4123],
        properties: {
          name: "Safe Haven Pipalkoti Terrace",
          status: "approved",
          elevation_m: 1320,
          terrain_slope_deg: 9.2,
          area_sq_m: 54000,
          district_id: 1,
        },
      };

      render(<FeatureDetailPanel feature={selectedSite} onClose={vi.fn()} />);

      expect(screen.getByText("Safe Haven Pipalkoti Terrace")).toBeInTheDocument();
      expect(screen.getByText(/approved/i)).toBeInTheDocument();
      expect(screen.getByText("1320 m")).toBeInTheDocument();
      expect(screen.getByText("9.2°")).toBeInTheDocument();
      expect(screen.getByText("54,000 m²")).toBeInTheDocument();
      expect(screen.getByText("DIST-1")).toBeInTheDocument();
    });

    it("renders route properties including blockage status and corridor info", () => {
      const selectedRoute: SelectedFeatureInfo = {
        id: 501,
        layerId: "routes-lines",
        layerCategory: "routes",
        geometryType: "LineString",
        properties: {
          name: "NH-07 Valley Access Corridor",
          distance_km: 14.8,
          estimated_travel_time_min: 35,
          route_type: "evacuation",
          is_blocked: true,
          blockage_reason: "Debris flow at km 12",
          origin_village_name: "Sunil Village",
          destination_site_name: "Safe Haven Pipalkoti Terrace",
          max_slope_deg: 8.5,
        },
      };

      render(<FeatureDetailPanel feature={selectedRoute} onClose={vi.fn()} />);

      expect(screen.getByText("NH-07 Valley Access Corridor")).toBeInTheDocument();
      expect(screen.getByText(/blocked/i)).toBeInTheDocument();
      expect(screen.getByText("14.8 km")).toBeInTheDocument();
      expect(screen.getByText("35 min")).toBeInTheDocument();
      expect(screen.getByText("Hazard Notice: Debris flow at km 12")).toBeInTheDocument();
    });

    it("renders missing fields safely as '—' without fabricating numbers", () => {
      const partialSite: SelectedFeatureInfo = {
        id: 102,
        layerId: "candidate-sites-points",
        layerCategory: "candidate_sites",
        geometryType: "Point",
        properties: {
          name: "Unsurveyed Safe Site",
          status: "proposed",
          elevation_m: null,
          terrain_slope_deg: null,
          area_sq_m: null,
        },
      };

      render(<FeatureDetailPanel feature={partialSite} onClose={vi.fn()} />);

      expect(screen.getByText("Unsurveyed Safe Site")).toBeInTheDocument();
      // Elevation, slope, and area render as "—"
      const dashes = screen.getAllByText("—");
      expect(dashes.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe("MapHeader Component", () => {
    it("renders active region and operational mode correctly", () => {
      render(
        <OperationalProvider initialState={{ activeRegion: "chamoli_pilot", dataMode: "demo" }}>
          <MapHeader totalSites={5} totalRoutes={2} />
        </OperationalProvider>
      );

      expect(screen.getByRole("heading", { name: "Command GIS Map Canvas" })).toBeInTheDocument();
      expect(screen.getByText(/Region: chamoli_pilot/i)).toBeInTheDocument();
      expect(screen.getByTestId("map-data-mode")).toHaveTextContent("DEMO (Synthetic)");
      expect(screen.getByText(/5 Havens • 2 Corridors/i)).toBeInTheDocument();
    });

    it("displays LIVE mode when dataMode is live", () => {
      render(
        <OperationalProvider initialState={{ activeRegion: "uttarkashi", dataMode: "live" }}>
          <MapHeader totalSites={0} totalRoutes={0} />
        </OperationalProvider>
      );

      expect(screen.getByTestId("map-data-mode")).toHaveTextContent("LIVE (Telemetry)");
    });
  });

  describe("GisMapPage Full Integration", () => {
    it("renders full GIS map page with API query integration", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      vi.spyOn(apiModule.apiClient, "get").mockImplementation(async (path: string) => {
        if (path.includes("/sites")) {
          return {
            success: true,
            data: mockCandidateSites,
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        if (path.includes("/routes")) {
          return {
            success: true,
            data: mockRoutes,
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        return { success: true, data: [] };
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

      expect(screen.getByTestId("maplibre-canvas")).toBeInTheDocument();
      expect(screen.getByTestId("layer-control-panel")).toBeInTheDocument();
      expect(screen.getByText("Candidate Safe Havens")).toBeInTheDocument();
      expect(screen.getByText("Evacuation Corridors")).toBeInTheDocument();
    });

    it("displays user-safe warning when backend GIS endpoints fail without crashing map", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      vi.spyOn(apiModule.apiClient, "get").mockImplementation(async (path: string) => {
        if (path.includes("/routes")) {
          throw new apiModule.ApiError({
            message: "Routes service connection timed out",
            status: 504,
            code: "GATEWAY_TIMEOUT",
          });
        }
        if (path.includes("/sites")) {
          return {
            success: true,
            data: mockCandidateSites,
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        return { success: true, data: [] };
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

      // Error banner displays safe message
      expect(screen.getByTestId("gis-error-banner")).toBeInTheDocument();
      expect(screen.getByText(/Routes service connection timed out/i)).toBeInTheDocument();
      // Map canvas still renders smoothly
      expect(screen.getByTestId("maplibre-canvas")).toBeInTheDocument();
    });

    it("resets selected feature and viewport bounds when activeRegion changes", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      vi.spyOn(apiModule.apiClient, "get").mockImplementation(async (path: string) => {
        if (path.includes("/sites")) {
          return {
            success: true,
            data: mockCandidateSites,
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        if (path.includes("/routes")) {
          return {
            success: true,
            data: mockRoutes,
            pagination: { total: 1, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        return { success: true, data: [] };
      });

      const RegionTransitionHarness: React.FC = () => {
        const { setActiveRegion } = useOperational();
        return (
          <div>
            <button
              onClick={() => setActiveRegion("pithoragarh_sector")}
              data-testid="switch-region-btn"
            >
              Switch Region
            </button>
            <GisMapPage />
          </div>
        );
      };

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider initialState={{ activeRegion: "chamoli_pilot" }}>
            <RegionTransitionHarness />
          </OperationalProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Command GIS Map Canvas" })).toBeInTheDocument();
      });

      // Simulate feature click from layer listener inside act
      expect(mockLayerListeners["click:candidate-sites-points"]).toBeDefined();
      act(() => {
        mockLayerListeners["click:candidate-sites-points"]({
          features: [
            {
              id: 101,
              geometry: { type: "Point", coordinates: [79.4321, 30.4123] },
              properties: {
                name: "Safe Haven Pipalkoti Terrace",
                status: "approved",
                elevation_m: 1320,
                terrain_slope_deg: 9.2,
                area_sq_m: 54000,
              },
            },
          ],
          lngLat: { lng: 79.4321, lat: 30.4123 },
        });
      });

      // Feature detail panel should now be visible
      await waitFor(() => {
        expect(screen.getByTestId("feature-detail-panel")).toBeInTheDocument();
      });
      expect(screen.getByText("Safe Haven Pipalkoti Terrace")).toBeInTheDocument();

      // Click button to switch region inside act
      act(() => {
        fireEvent.click(screen.getByTestId("switch-region-btn"));
      });

      // Feature detail panel should be cleared on region change
      await waitFor(() => {
        expect(screen.queryByTestId("feature-detail-panel")).not.toBeInTheDocument();
      });
    });
  });
});
