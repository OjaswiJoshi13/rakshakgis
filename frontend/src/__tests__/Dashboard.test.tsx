import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DashboardKpiStrip } from "@/components/dashboard/DashboardKpiStrip";
import { TelemetryHealthCard } from "@/components/dashboard/TelemetryHealthCard";
import { CandidateSitesTable } from "@/components/dashboard/CandidateSitesTable";
import { RelocationAssignmentsCard } from "@/components/dashboard/RelocationAssignmentsCard";
import { ScenarioReadinessCard } from "@/components/dashboard/ScenarioReadinessCard";
import { AlertsNoticeCard } from "@/components/dashboard/AlertsNoticeCard";
import ExecutiveDashboardPage from "@/app/dashboard/page";
import { AuthProvider } from "@/context/AuthContext";
import { OperationalProvider } from "@/context/OperationalContext";
import * as authService from "@/lib/auth";
import * as apiModule from "@/lib/api";
import {
  CandidateSiteRead,
  DataSourceTelemetryRead,
  RelocationAssignmentRead,
  ScenarioDefinitionRead,
  TelemetryOverviewRead,
} from "@/types/dashboard";

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

const mockTelemetryOverview: TelemetryOverviewRead = {
  total_sources: 5,
  healthy_count: 4,
  degraded_count: 1,
  unavailable_count: 0,
  fresh_count: 4,
  stale_count: 1,
  unknown_count: 0,
  synthetic_count: 5,
  evaluated_at: "2026-09-06T12:00:00Z",
};

const mockSources: DataSourceTelemetryRead[] = [
  {
    source_id: 1,
    name: "IMD Weather Station Joshimath",
    source_type: "weather_station",
    provider: "IMD",
    provider_id: "IMD-01",
    category: "weather",
    provider_mode: "synthetic_mock",
    provider_health: "HEALTHY",
    freshness: {
      status: "FRESH",
      age_seconds: 120,
      threshold_seconds: 3600,
      is_usable: true,
      reason: "Within 1h threshold",
      evaluated_at: "2026-09-06T12:00:00Z",
    },
    last_successful_update: "2026-09-06T11:58:00Z",
    last_attempted_update: "2026-09-06T11:58:00Z",
    latest_run_status: "SUCCESS",
    is_synthetic: true,
    is_active: true,
    records_ingested_total: 1540,
    records_failed_total: 0,
  },
];

const mockCandidateSites: CandidateSiteRead[] = [
  {
    id: 101,
    name: "Pipalkoti Safe Terrace Site A",
    district_id: 1,
    location: { type: "Point", coordinates: [79.4321, 30.4123] },
    area_sq_m: 45000,
    terrain_slope_deg: 8.5,
    elevation_m: 1350,
    status: "approved",
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
  {
    id: 102,
    name: "Gauchar Relocation Haven",
    district_id: 1,
    location: { type: "Point", coordinates: [79.1554, 30.2876] },
    area_sq_m: 85000,
    terrain_slope_deg: 5.2,
    elevation_m: 820,
    status: "active",
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
];

const mockAssignments: RelocationAssignmentRead[] = [
  {
    id: 201,
    village_id: 10,
    village_name: "Sunil Village Lower Sector",
    candidate_site_id: 101,
    candidate_site_name: "Pipalkoti Safe Terrace Site A",
    assigned_households: 42,
    assigned_population: 180,
    status: "approved",
    approved_by_officer_id: 1,
    assigned_at: "2026-09-05T14:30:00Z",
    updated_at: "2026-09-05T14:30:00Z",
  },
];

const mockScenarios: ScenarioDefinitionRead[] = [
  {
    scenario_type: "EXTREME_RAINFALL",
    name: "Monsoon Surge (+40% Rainfall)",
    description: "High precipitation stress testing carrying capacity and valley routes.",
    default_parameters: {
      rainfall_multiplier: 1.4,
      seismic_intensity_mmi: null,
      road_blockage_percentage: 25,
    },
    is_canonical: true,
    tags: ["precipitation", "monsoon"],
  },
  {
    scenario_type: "FLASH_FLOOD",
    name: "Glacial / Flash Flood Exceedance",
    description: "Riverine overflow blocking valley corridors.",
    default_parameters: {
      rainfall_multiplier: 1.2,
      seismic_intensity_mmi: null,
      road_blockage_percentage: 50,
    },
    is_canonical: true,
    tags: ["hydrology", "flood"],
  },
];

describe("Executive Dashboard UI (Chunk M5-04)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
    apiModule.apiCache.clear();
  });

  describe("DashboardHeader component", () => {
    it("renders title, region, and data mode indicators correctly", () => {
      render(
        <OperationalProvider initialState={{ dataMode: "demo", activeRegion: "chamoli_district" }}>
          <DashboardHeader telemetryOverview={mockTelemetryOverview} />
        </OperationalProvider>
      );

      expect(screen.getByRole("heading", { name: /Executive Command Dashboard/i })).toBeInTheDocument();
      expect(screen.getByText(/Region: chamoli_district/i)).toBeInTheDocument();
      expect(screen.getByTestId("data-mode-indicator")).toHaveTextContent("DEMO (Synthetic)");
      expect(screen.getByText("4/5 Feeds Healthy")).toBeInTheDocument();
    });

    it("displays LIVE mode when dataMode is live", () => {
      render(
        <OperationalProvider initialState={{ dataMode: "live", activeRegion: "uttarkashi" }}>
          <DashboardHeader telemetryOverview={mockTelemetryOverview} />
        </OperationalProvider>
      );

      expect(screen.getByTestId("data-mode-indicator")).toHaveTextContent("LIVE (Telemetry)");
    });

    it("triggers refresh callback when refresh button is clicked", () => {
      const onRefresh = vi.fn();
      render(
        <OperationalProvider>
          <DashboardHeader onRefresh={onRefresh} />
        </OperationalProvider>
      );

      const refreshBtn = screen.getByRole("button", { name: /refresh/i });
      fireEvent.click(refreshBtn);
      expect(onRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe("DashboardKpiStrip component", () => {
    it("renders all 6 metric cards with loaded backend data", () => {
      render(
        <DashboardKpiStrip
          sitesData={{
            success: true,
            data: mockCandidateSites,
            pagination: {
              total: 12,
              page: 1,
              page_size: 10,
              total_pages: 2,
              has_next: true,
              has_prev: false,
            },
          }}
          assignmentsData={{
            success: true,
            data: mockAssignments,
            pagination: {
              total: 8,
              page: 1,
              page_size: 10,
              total_pages: 1,
              has_next: false,
              has_prev: false,
            },
          }}
          telemetryOverview={mockTelemetryOverview}
          scenariosData={mockScenarios}
        />
      );

      expect(screen.getByText("Candidate Safe Sites")).toBeInTheDocument();
      expect(screen.getByText("12")).toBeInTheDocument();

      expect(screen.getByText("Planned Relocations")).toBeInTheDocument();
      expect(screen.getByText("8")).toBeInTheDocument();

      expect(screen.getByText("Telemetry Feeds")).toBeInTheDocument();
      expect(screen.getByText("Data Freshness")).toBeInTheDocument();
      expect(screen.getByText("4/5")).toBeInTheDocument();

      expect(screen.getByText("Scenario Models")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();

      expect(screen.getByText("Habitations Layer")).toBeInTheDocument();
      expect(screen.getByText("M5-06")).toBeInTheDocument();
    });

    it("displays loading and unavailable states when queries fail or load", () => {
      render(
        <DashboardKpiStrip
          sitesLoading={true}
          assignmentsError={true}
          telemetryError={true}
          scenariosLoading={true}
        />
      );

      expect(screen.getByText("API Error")).toBeInTheDocument();
      expect(screen.getAllByText("Unavailable").length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("TelemetryHealthCard component", () => {
    it("renders provider health, freshness distribution, and sources table", () => {
      render(
        <TelemetryHealthCard
          overview={mockTelemetryOverview}
          sources={mockSources}
        />
      );

      expect(screen.getByText("Data Sources & Telemetry Health")).toBeInTheDocument();
      expect(screen.getByText("Synthetic Feeds: 5/5")).toBeInTheDocument();
      expect(screen.getByText("IMD Weather Station Joshimath")).toBeInTheDocument();
      expect(screen.getByText("HEALTHY")).toBeInTheDocument();
      expect(screen.getByText("FRESH")).toBeInTheDocument();
    });

    it("handles error state cleanly", () => {
      render(<TelemetryHealthCard isError={true} errorMessage="Telemetry backend timeout" />);
      expect(screen.getByText("Telemetry Service Unavailable")).toBeInTheDocument();
      expect(screen.getByText("Telemetry backend timeout")).toBeInTheDocument();
    });
  });

  describe("CandidateSitesTable component", () => {
    it("renders site rows with name, status badge, elevation, and area", () => {
      render(<CandidateSitesTable sites={mockCandidateSites} totalCount={2} />);

      expect(screen.getByText("Candidate Relocation Sites")).toBeInTheDocument();
      expect(screen.getByText("Pipalkoti Safe Terrace Site A")).toBeInTheDocument();
      expect(screen.getByText("Gauchar Relocation Haven")).toBeInTheDocument();
      expect(screen.getByText("Approved")).toBeInTheDocument();
      expect(screen.getByText("Active")).toBeInTheDocument();
      expect(screen.getByText("1350m")).toBeInTheDocument();
      expect(screen.getByText("45,000 m²")).toBeInTheDocument();
    });

    it("handles empty sites list", () => {
      render(<CandidateSitesTable sites={[]} totalCount={0} />);
      expect(screen.getByText(/No candidate relocation sites found/i)).toBeInTheDocument();
    });
  });

  describe("RelocationAssignmentsCard component", () => {
    it("renders planned settlement relocations", () => {
      render(<RelocationAssignmentsCard assignments={mockAssignments} totalCount={1} />);

      expect(screen.getByText("Planned Relocation Assignments")).toBeInTheDocument();
      expect(screen.getByText("Sunil Village Lower Sector")).toBeInTheDocument();
      expect(screen.getByText("Pipalkoti Safe Terrace Site A")).toBeInTheDocument();
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("180")).toBeInTheDocument();
    });

    it("handles empty assignments gracefully", () => {
      render(<RelocationAssignmentsCard assignments={[]} totalCount={0} />);
      expect(screen.getByText(/No active settlement relocation assignments found/i)).toBeInTheDocument();
    });
  });

  describe("ScenarioReadinessCard component", () => {
    it("renders scenario cards with parameters and descriptions", () => {
      render(<ScenarioReadinessCard scenarios={mockScenarios} />);

      expect(screen.getByText("Contingency & Scenario Models")).toBeInTheDocument();
      expect(screen.getByText("Monsoon Surge (+40% Rainfall)")).toBeInTheDocument();
      expect(screen.getByText("Glacial / Flash Flood Exceedance")).toBeInTheDocument();
      expect(screen.getByText("1.4x")).toBeInTheDocument();
      expect(screen.getByText("25%")).toBeInTheDocument();
    });
  });

  describe("AlertsNoticeCard component", () => {
    it("renders early warning standards and SOP-RZ-01 notice", () => {
      render(<AlertsNoticeCard />);

      expect(screen.getByText("Operational Alerts & Threshold Triggers")).toBeInTheDocument();
      expect(screen.getByText("64.5 mm / 24h")).toBeInTheDocument();
      expect(screen.getByText(/500 m Buffer/i)).toBeInTheDocument();
    });
  });

  describe("ExecutiveDashboardPage full integration", () => {
    it("renders full dashboard with API query responses", async () => {
      // Mock authenticated session
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      // Mock apiClient.get for each endpoint
      vi.spyOn(apiModule.apiClient, "get").mockImplementation(async (path: string) => {
        if (path.includes("/telemetry/overview")) {
          return { success: true, data: mockTelemetryOverview };
        }
        if (path.includes("/telemetry/sources")) {
          return {
            success: true,
            data: mockSources,
            pagination: { total: 1, page: 1, page_size: 10, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        if (path.includes("/sites")) {
          return {
            success: true,
            data: mockCandidateSites,
            pagination: { total: 2, page: 1, page_size: 10, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        if (path.includes("/relocation/assignments")) {
          return {
            success: true,
            data: mockAssignments,
            pagination: { total: 1, page: 1, page_size: 10, total_pages: 1, has_next: false, has_prev: false },
          };
        }
        if (path.includes("/scenarios")) {
          return { success: true, data: mockScenarios };
        }
        return { success: true, data: {} };
      });

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider>
            <ExecutiveDashboardPage />
          </OperationalProvider>
        </AuthProvider>
      );

      // Wait for queries to resolve and assert presence of major dashboard sections
      await waitFor(() => {
        expect(screen.getByRole("heading", { name: /Executive Command Dashboard/i })).toBeInTheDocument();
      });

      expect(screen.getByText("Candidate Safe Sites")).toBeInTheDocument();
      expect(screen.getByText("Planned Relocations")).toBeInTheDocument();
      expect(screen.getByText("Data Sources & Telemetry Health")).toBeInTheDocument();
      expect(screen.getByText("Contingency & Scenario Models")).toBeInTheDocument();
      expect(screen.getByText("Operational Alerts & Threshold Triggers")).toBeInTheDocument();
    });

    it("ensures a single failed API query does not crash the rest of the dashboard", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      // Sites query rejects with an ApiError, while others succeed
      vi.spyOn(apiModule.apiClient, "get").mockImplementation(async (path: string) => {
        if (path.includes("/sites")) {
          throw new apiModule.ApiError({
            message: "Database connection refused",
            status: 503,
            code: "SERVICE_UNAVAILABLE",
          });
        }
        if (path.includes("/telemetry/overview")) {
          return { success: true, data: mockTelemetryOverview };
        }
        if (path.includes("/scenarios")) {
          return { success: true, data: mockScenarios };
        }
        return { success: true, data: [] };
      });

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider>
            <ExecutiveDashboardPage />
          </OperationalProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: /Executive Command Dashboard/i })).toBeInTheDocument();
      });

      // Failed section displays user-safe error message
      expect(screen.getByText("Failed to Load Candidate Sites")).toBeInTheDocument();
      expect(screen.getByText("Database connection refused")).toBeInTheDocument();

      // Other sections remain completely functional and visible
      expect(screen.getByText("Contingency & Scenario Models")).toBeInTheDocument();
      expect(screen.getByText("Operational Alerts & Threshold Triggers")).toBeInTheDocument();
    });
  });
});
