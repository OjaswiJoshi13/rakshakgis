import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DataSourcesOperationsPage from "@/app/operations/sources/page";
import * as telemetryApi from "@/lib/api/telemetry";

// Mock Next.js navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations/sources",
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => mockSearchParams,
}));

// Mock AuthContext
vi.mock("@/context/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
  useAuth: () => ({
    user: {
      id: 1,
      email: "dm_chamoli@rakshakgis.gov.in",
      role: "district_officer",
      name: "District Magistrate (Duty Officer)",
    },
    isAuthenticated: true,
  }),
}));

describe("Data Sources & Freshness Monitoring UI Suite (Chunk M6-06)", () => {
  let mockSources: telemetryApi.DataSourceTelemetryRead[];
  let mockOverview: telemetryApi.TelemetryOverviewRead;

  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams.delete("sourceId");

    mockSources = JSON.parse(JSON.stringify(telemetryApi.HIMALAYAN_PILOT_DATA_SOURCES));
    mockOverview = JSON.parse(JSON.stringify(telemetryApi.HIMALAYAN_PILOT_TELEMETRY_OVERVIEW));

    vi.spyOn(telemetryApi, "getTelemetryOverview").mockImplementation(async () => {
      return mockOverview;
    });

    vi.spyOn(telemetryApi, "listDataSources").mockImplementation(async (filters) => {
      let filtered = [...mockSources];

      if (filters?.search) {
        const q = filters.search.toLowerCase().trim();
        filtered = filtered.filter(
          (s) =>
            s.name.toLowerCase().includes(q) ||
            s.provider.toLowerCase().includes(q) ||
            (s.provider_id && s.provider_id.toLowerCase().includes(q))
        );
      }

      if (filters?.category && filters.category !== "all") {
        filtered = filtered.filter((s) => s.category === filters.category);
      }

      if (filters?.health && filters.health !== "all") {
        filtered = filtered.filter(
          (s) => s.provider_health.toLowerCase() === filters.health?.toLowerCase()
        );
      }

      if (filters?.freshness && filters.freshness !== "all") {
        filtered = filtered.filter(
          (s) => s.freshness.status.toLowerCase() === filters.freshness?.toLowerCase()
        );
      }

      if (filters?.mode && filters.mode !== "all") {
        filtered = filtered.filter(
          (s) => s.provider_mode.toLowerCase() === filters.mode?.toLowerCase()
        );
      }

      return {
        success: true,
        data: filtered,
        pagination: {
          total: filtered.length,
          page: 1,
          page_size: 20,
          total_pages: 1,
          has_next: false,
          has_prev: false,
        },
      };
    });

    vi.spyOn(telemetryApi, "getDataSourceDetail").mockImplementation(async (id) => {
      const numericId = typeof id === "number" ? id : parseInt(id.toString(), 10);
      const found =
        mockSources.find(
          (s) => s.source_id === numericId || s.provider_id === id.toString()
        ) || mockSources[0];

      return {
        ...found,
        recent_runs: telemetryApi.HIMALAYAN_PILOT_INGESTION_RUNS[found.source_id] || [],
        metadata_json: {
          region_profile: "himalayan_pilot",
          disclaimer: "SYNTHETIC DEMO DATASET strictly adhering to Rule 8",
        },
      };
    });

    vi.spyOn(telemetryApi, "probeDataSource").mockImplementation(async (id) => {
      const numericId = typeof id === "number" ? id : parseInt(id.toString(), 10);
      const found =
        mockSources.find(
          (s) => s.source_id === numericId || s.provider_id === id.toString()
        ) || mockSources[0];

      const now = new Date().toISOString();
      const probed: telemetryApi.DataSourceTelemetryRead = {
        ...found,
        provider_health: "healthy",
        freshness: {
          ...found.freshness,
          status: "fresh",
          age_seconds: 0,
          is_usable: true,
          reason: "Health probe verified provider response; fresh observation recorded.",
          evaluated_at: now,
        },
        last_successful_update: now,
        last_attempted_update: now,
        latest_run_status: "success",
      };

      // update in mock list
      mockSources = mockSources.map((s) => (s.source_id === found.source_id ? probed : s));
      return probed;
    });
  });

  const renderComponent = () => {
    return render(<DataSourcesOperationsPage />);
  };

  describe("Workspace Header, Run Controls & Summary Cards", () => {
    it("renders page title, chunk badge, and operational descriptions", async () => {
      renderComponent();

      expect(
        await screen.findByRole("heading", { name: /Data Sources & Freshness Monitoring/i })
      ).toBeInTheDocument();

      expect(screen.getByText("M6-06")).toBeInTheDocument();
      expect(screen.getByText("Data Sources & Freshness Monitoring UI")).toBeInTheDocument();
      expect(
        screen.getByText(/Chunk M3-13 \(Data Source Freshness & Telemetry Backend — COMMITTED\)/i)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Refresh Diagnostics/i })
      ).toBeInTheDocument();
    });

    it("renders summary metric cards with initial telemetry counts", async () => {
      renderComponent();

      expect(await screen.findByText("Registered Data Feeds")).toBeInTheDocument();
      expect(screen.getByText("Adapter Health")).toBeInTheDocument();
      expect(screen.getAllByText("Freshness Status").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Demo Provenance")).toBeInTheDocument();

      // Counts from overview
      expect(screen.getByText("4/5")).toBeInTheDocument();
      expect(screen.getByText("4 Fresh")).toBeInTheDocument();
      expect(screen.getByText("5 Synthetic")).toBeInTheDocument();
    });

    it("renders collapsible platform freshness thresholds reference card", async () => {
      renderComponent();

      const triggerBtn = await screen.findByRole("button", {
        name: /Platform Freshness Thresholds & Clock-Skew Policies/i,
      });
      expect(triggerBtn).toBeInTheDocument();

      // Initially collapsed
      expect(screen.queryByText(/Precipitation Telemetry/i)).not.toBeInTheDocument();

      // Expand card
      fireEvent.click(triggerBtn);

      expect(await screen.findByText("Precipitation Telemetry")).toBeInTheDocument();
      expect(screen.getByText("Riverine Flood Gauges")).toBeInTheDocument();
      expect(screen.getByText("Geological Survey Inventory")).toBeInTheDocument();
      expect(screen.getByText("In-Situ IoT Hazard Sensors")).toBeInTheDocument();
      expect(screen.getByText("Census & Vulnerability Records")).toBeInTheDocument();
      expect(screen.getByText("Clock-Skew Guard")).toBeInTheDocument();
    });
  });

  describe("Data Sources Table & Diagnostics Listing", () => {
    it("renders all 5 registered data sources with health and freshness badges", async () => {
      renderComponent();

      expect(
        await screen.findByText("IMD Automated Weather Station (Precipitation)")
      ).toBeInTheDocument();
      expect(
        screen.getByText("CWC Hydrological River Gauges (Water Level)")
      ).toBeInTheDocument();
      expect(
        screen.getByText("GSI Landslide Inventory & Slope Displacement")
      ).toBeInTheDocument();
      expect(
        screen.getByText("In-Situ Multi-Hazard IoT Sensor Cluster")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Census Demographic & Vulnerability Records")
      ).toBeInTheDocument();

      // Health badges
      expect(screen.getAllByText("HEALTHY").length).toBe(4);
      expect(screen.getByText("DEGRADED")).toBeInTheDocument();

      // Freshness badges
      expect(screen.getAllByText("FRESH").length).toBe(4);
      expect(screen.getByText("STALE")).toBeInTheDocument();

      // Synthetic markers
      expect(screen.getAllByText("SYNTHETIC").length).toBe(5);
    });

    it("displays age and threshold comparisons without client-side formula invention", async () => {
      renderComponent();

      // 900s age / 3600s max -> 15m old / 1.0h max
      expect(await screen.findByText(/15m old \/ 1\.0h max/i)).toBeInTheDocument();

      // 14400s age / 86400s max -> 4.0h old / 1.0d max
      expect(screen.getByText(/4\.0h old \/ 1\.0d max/i)).toBeInTheDocument();

      // Stale IoT sensor: 5400s age / 3600s max -> 1.5h old / 1.0h max
      expect(screen.getByText(/1\.5h old \/ 1\.0h max/i)).toBeInTheDocument();
    });
  });

  describe("Search & Multi-Dimensional Filtering", () => {
    it("filters data sources by text search query", async () => {
      renderComponent();

      expect(
        await screen.findByText("IMD Automated Weather Station (Precipitation)")
      ).toBeInTheDocument();

      const searchInput = screen.getByLabelText(/Search Data Sources/i);
      fireEvent.change(searchInput, { target: { value: "Alaknanda" } });

      await waitFor(() => {
        expect(
          screen.getByText("CWC Hydrological River Gauges (Water Level)")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("IMD Automated Weather Station (Precipitation)")
        ).not.toBeInTheDocument();
        expect(
          screen.queryByText("GSI Landslide Inventory & Slope Displacement")
        ).not.toBeInTheDocument();
      });
    });

    it("filters data sources by source category dropdown", async () => {
      renderComponent();

      expect(
        await screen.findByText("IMD Automated Weather Station (Precipitation)")
      ).toBeInTheDocument();

      const categorySelect = screen.getByLabelText(/^Category$/i);
      fireEvent.change(categorySelect, { target: { value: "landslide" } });

      await waitFor(() => {
        expect(
          screen.getByText("GSI Landslide Inventory & Slope Displacement")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("IMD Automated Weather Station (Precipitation)")
        ).not.toBeInTheDocument();
      });
    });

    it("filters data sources by provider health dropdown", async () => {
      renderComponent();

      expect(
        await screen.findByText("IMD Automated Weather Station (Precipitation)")
      ).toBeInTheDocument();

      const healthSelect = screen.getByLabelText(/Provider Health/i);
      fireEvent.change(healthSelect, { target: { value: "degraded" } });

      await waitFor(() => {
        expect(
          screen.getByText("In-Situ Multi-Hazard IoT Sensor Cluster")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("IMD Automated Weather Station (Precipitation)")
        ).not.toBeInTheDocument();
      });
    });

    it("filters data sources by freshness status dropdown", async () => {
      renderComponent();

      expect(
        await screen.findByText("IMD Automated Weather Station (Precipitation)")
      ).toBeInTheDocument();

      const freshnessSelect = screen.getByLabelText(/Freshness Status/i);
      fireEvent.change(freshnessSelect, { target: { value: "stale" } });

      await waitFor(() => {
        expect(
          screen.getByText("In-Situ Multi-Hazard IoT Sensor Cluster")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("IMD Automated Weather Station (Precipitation)")
        ).not.toBeInTheDocument();
      });
    });

    it("renders empty state and allows resetting filters", async () => {
      renderComponent();

      expect(
        await screen.findByText("IMD Automated Weather Station (Precipitation)")
      ).toBeInTheDocument();

      const searchInput = screen.getByLabelText(/Search Data Sources/i);
      fireEvent.change(searchInput, { target: { value: "nonexistent_provider_xyz" } });

      await waitFor(() => {
        expect(
          screen.getByText("No Data Sources Match Filter Criteria")
        ).toBeInTheDocument();
      });

      // Reset filters
      const resetBtn = screen.getByRole("button", { name: /Reset Filters/i });
      fireEvent.click(resetBtn);

      await waitFor(() => {
        expect(
          screen.getByText("IMD Automated Weather Station (Precipitation)")
        ).toBeInTheDocument();
      });
    });
  });

  describe("History Modal & Health Probe Execution", () => {
    it("opens source detail modal and inspects recent ingestion runs", async () => {
      renderComponent();

      expect(
        await screen.findByText("IMD Automated Weather Station (Precipitation)")
      ).toBeInTheDocument();

      const historyBtns = screen.getAllByRole("button", { name: /History/i });
      fireEvent.click(historyBtns[0]); // IMD AWS

      expect(
        await screen.findByRole("dialog", { hidden: true })
      ).toBeInTheDocument();

      expect(
        screen.getByRole("heading", { name: "IMD Automated Weather Station (Precipitation)" })
      ).toBeInTheDocument();

      expect(screen.getByText("Deterministic Freshness Evaluation")).toBeInTheDocument();
      expect(
        screen.getByText("Recent AWS observation within 3600s threshold")
      ).toBeInTheDocument();

      // Recent ingestion runs table
      expect(screen.getByText("Recent Ingestion Execution Runs")).toBeInTheDocument();
      expect(screen.getByText("#101")).toBeInTheDocument();
      expect(
        screen.getByText("Batch 101: 25 meteorological precipitation readings ingested successfully.")
      ).toBeInTheDocument();

      // Statutory Rule 8 disclosure
      expect(
        screen.getByText(/Statutory Governance & Provenance Disclosure/i)
      ).toBeInTheDocument();

      // Close modal
      const closeBtn = screen.getByRole("button", { name: /^Close$/i });
      fireEvent.click(closeBtn);

      await waitFor(() => {
        expect(
          screen.queryByRole("dialog", { hidden: true })
        ).not.toBeInTheDocument();
      });
    });

    it("triggers provider health probe and receives updated fresh observation", async () => {
      renderComponent();

      expect(
        await screen.findByText("In-Situ Multi-Hazard IoT Sensor Cluster")
      ).toBeInTheDocument();

      // Probe degraded IoT sensor (4th item)
      const probeBtns = screen.getAllByRole("button", { name: /Probe/i });
      fireEvent.click(probeBtns[3]);

      await waitFor(() => {
        expect(telemetryApi.probeDataSource).toHaveBeenCalledWith(4);
      });

      expect(
        await screen.findByText(/Successfully probed provider adapter: "In-Situ Multi-Hazard IoT Sensor Cluster"/i)
      ).toBeInTheDocument();
    });

    it("supports URL search parameter deep-linking to auto-open inspection modal", async () => {
      mockSearchParams.set("sourceId", "2");

      renderComponent();

      expect(
        await screen.findByRole("dialog", { hidden: true })
      ).toBeInTheDocument();

      expect(
        screen.getByRole("heading", { name: "CWC Hydrological River Gauges (Water Level)" })
      ).toBeInTheDocument();
      expect(screen.getByText("Source #2")).toBeInTheDocument();
    });
  });
});
