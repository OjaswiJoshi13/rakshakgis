import React from "react";
import { render, screen, fireEvent, waitFor, act, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AlertsOperationsPage from "@/app/operations/alerts/page";
import * as alertsApi from "@/lib/api/alerts";

// Mock Next.js navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations/alerts",
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

describe("Real-Time Alerts & Threshold Warnings UI Suite (Chunk M6-05)", () => {
  let mockAlerts: alertsApi.OperationalAlertItem[];

  beforeEach(() => {
    vi.clearAllMocks();
    mockAlerts = JSON.parse(JSON.stringify(alertsApi.HIMALAYAN_PILOT_ALERT_DATASET));

    vi.spyOn(alertsApi, "listAlerts").mockImplementation(async (filters) => {
      let filtered = [...mockAlerts];

      if (filters?.severity && filters.severity !== "all") {
        filtered = filtered.filter((a) => a.severity === filters.severity);
      }
      if (filters?.status && filters.status !== "all") {
        filtered = filtered.filter((a) => a.status === filters.status);
      }
      if (filters?.indicator && filters.indicator !== "all") {
        filtered = filtered.filter((a) => a.indicator === filters.indicator);
      }
      if (filters?.is_acknowledged !== undefined && filters.is_acknowledged !== "all") {
        filtered = filtered.filter((a) => a.is_acknowledged === filters.is_acknowledged);
      }
      if (filters?.search && filters.search.trim()) {
        const q = filters.search.toLowerCase().trim();
        filtered = filtered.filter(
          (a) =>
            a.headline.toLowerCase().includes(q) ||
            a.message.toLowerCase().includes(q) ||
            (a.village_name && a.village_name.toLowerCase().includes(q)) ||
            (a.candidate_id && a.candidate_id.toLowerCase().includes(q)) ||
            a.id.toLowerCase().includes(q)
        );
      }

      return { success: true, data: filtered };
    });

    vi.spyOn(alertsApi, "getAlertSummaryMetrics").mockImplementation(async () => ({
      success: true,
      data: {
        total_alerts: mockAlerts.length,
        triggered_count: mockAlerts.filter((a) => a.status === "triggered").length,
        pending_acknowledgment: mockAlerts.filter((a) => !a.is_acknowledged).length,
        insufficient_data_count: mockAlerts.filter((a) => a.status === "insufficient_data").length,
        critical_extreme_count: mockAlerts.filter(
          (a) => a.severity === "extreme" || a.severity === "severe"
        ).length,
      },
    }));

    vi.spyOn(alertsApi, "getThresholdConfig").mockResolvedValue({
      success: true,
      data: alertsApi.HIMALAYAN_PILOT_THRESHOLDS,
    });

    vi.spyOn(alertsApi, "acknowledgeAlert").mockImplementation(async (id, officerName) => {
      const idx = mockAlerts.findIndex((a) => a.id === id);
      if (idx !== -1) {
        mockAlerts[idx] = {
          ...mockAlerts[idx],
          is_acknowledged: true,
          acknowledged_at: new Date().toISOString(),
          acknowledged_by: officerName || "District Magistrate (Duty Officer)",
        };
        return { success: true, data: mockAlerts[idx] };
      }
      throw new Error(`Alert with id '${id}' not found.`);
    });

    vi.spyOn(alertsApi, "acknowledgeAllAlerts").mockImplementation(async (officerName) => {
      let count = 0;
      const now = new Date().toISOString();
      mockAlerts = mockAlerts.map((a) => {
        if (!a.is_acknowledged) {
          count++;
          return {
            ...a,
            is_acknowledged: true,
            acknowledged_at: now,
            acknowledged_by: officerName || "District Magistrate (Duty Officer)",
          };
        }
        return a;
      });
      return { success: true, data: { acknowledged_count: count } };
    });
  });

  const renderWithAuth = () => {
    return render(
      <div data-testid="test-root">
        <AlertsOperationsPage />
      </div>
    );
  };

  describe("Workspace Header, Run Controls & Summary Cards", () => {
    it("renders page title, chunk badge, and operational descriptions", async () => {
      renderWithAuth();

      expect(
        await screen.findByRole("heading", { name: /Real-Time Alerts & Warnings/i })
      ).toBeInTheDocument();

      expect(screen.getByText("M6-05")).toBeInTheDocument();
      expect(screen.getByText("Real-Time Alerts & Threshold Warnings UI")).toBeInTheDocument();
      expect(
        screen.getByText(/Chunk M3-11 \(Dynamic Red Zone Engine — COMMITTED\)/i)
      ).toBeInTheDocument();
    });

    it("renders summary metric cards with initial telemetry counts", async () => {
      renderWithAuth();

      expect(await screen.findByText("Total Monitored Feeds")).toBeInTheDocument();
      expect(screen.getByText("Triggered Threshold Breaches")).toBeInTheDocument();
      expect(screen.getAllByText("Pending Acknowledgment").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Sensor Telemetry Gaps")).toBeInTheDocument();

      // Himalayan baseline has 5 total feeds
      expect(screen.getAllByText("5").length).toBeGreaterThanOrEqual(1);
    });

    it("renders authoritative regional profile threshold configuration panel", async () => {
      renderWithAuth();

      expect(
        await screen.findByText("Authoritative Dynamic Trigger Thresholds")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Himalayan Pilot \(Chamoli \/ Joshimath District\)/i)
      ).toBeInTheDocument();

      // Expand thresholds panel
      const expandBtn = screen.getByLabelText(/Expand thresholds/i);
      await act(async () => {
        fireEvent.click(expandBtn);
      });

      // Verify regional trigger thresholds from himalayan.py
      expect(screen.getByText("24h Rainfall")).toBeInTheDocument();
      expect(screen.getByText(/≥ 64.5 mm/)).toBeInTheDocument();
      expect(screen.getByText("Seismic Intensity")).toBeInTheDocument();
      expect(screen.getByText(/≥ 6 MMI/)).toBeInTheDocument();
      expect(screen.getByText("Critical Slope")).toBeInTheDocument();
      expect(screen.getByText(/≥ 25°/)).toBeInTheDocument();
      expect(screen.getByText("500 m")).toBeInTheDocument();
    });
  });

  describe("Alerts List & Threshold Breaches", () => {
    it("renders baseline alerts list with severity badges and observed vs threshold comparisons", async () => {
      renderWithAuth();

      // Joshimath Rainfall Threshold Exceedance
      expect(
        await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge")
      ).toBeInTheDocument();
      expect(screen.getByText("EXTREME")).toBeInTheDocument();
      expect(screen.getAllByText("TRIGGERED (CANDIDATE)").length).toBeGreaterThanOrEqual(1);

      // Observed 84.2 mm >= 64.5 mm
      expect(screen.getByText("84.2 mm")).toBeInTheDocument();
      expect(screen.getAllByText("64.5 mm").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("(Exceeded)").length).toBeGreaterThanOrEqual(1);

      // Pipalkoti Seismic Tremor Exceedance
      expect(
        screen.getByText("Seismic Tremor Exceedance (6.4 MMI) — Pipalkoti Corridor")
      ).toBeInTheDocument();
      expect(screen.getByText("6.4 MMI")).toBeInTheDocument();

      // Helang River Stage Breach
      expect(
        screen.getByText("Hydrological River Stage Breach (+2.1m) — Helang Riverine Zone")
      ).toBeInTheDocument();
    });

    it("renders INSUFFICIENT_DATA alert with safe gap indicator and null telemetry note", async () => {
      renderWithAuth();

      // Urgam Valley Telemetry Gap
      expect(
        await screen.findByText("Sensor Telemetry Unavailable — Urgam Debris Volume Transducer")
      ).toBeInTheDocument();
      expect(screen.getByText("INSUFFICIENT DATA (GAP)")).toBeInTheDocument();
      expect(
        screen.getByText(/Telemetry null\/offline — safe gap halt/i)
      ).toBeInTheDocument();
    });
  });

  describe("Filtering & Search Controls", () => {
    it("filters alerts by severity", async () => {
      renderWithAuth();

      await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge");

      const severitySelect = screen.getByLabelText(/Severity/i);
      await act(async () => {
        fireEvent.change(severitySelect, { target: { value: "extreme" } });
      });

      // Extreme alert should be visible
      await waitFor(() => {
        expect(
          screen.getByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("Seismic Tremor Exceedance (6.4 MMI) — Pipalkoti Corridor")
        ).not.toBeInTheDocument();
        expect(
          screen.queryByText("Sensor Telemetry Unavailable — Urgam Debris Volume Transducer")
        ).not.toBeInTheDocument();
      });
    });

    it("filters alerts by M3-11 status", async () => {
      renderWithAuth();

      await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge");

      const statusSelect = screen.getByLabelText(/M3-11 Status/i);
      await act(async () => {
        fireEvent.change(statusSelect, { target: { value: "insufficient_data" } });
      });

      // Only Urgam sensor gap should be visible
      await waitFor(() => {
        expect(
          screen.getByText("Sensor Telemetry Unavailable — Urgam Debris Volume Transducer")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge")
        ).not.toBeInTheDocument();
      });
    });

    it("searches alerts by text query", async () => {
      renderWithAuth();

      await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge");

      const searchInput = screen.getByPlaceholderText(/Search by settlement, district/i);
      await act(async () => {
        fireEvent.change(searchInput, { target: { value: "Pipalkoti" } });
      });

      // Pipalkoti alert should be visible
      await waitFor(() => {
        expect(
          screen.getByText("Seismic Tremor Exceedance (6.4 MMI) — Pipalkoti Corridor")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge")
        ).not.toBeInTheDocument();
      });
    });

    it("renders empty state when search returns no matches and allows reset", async () => {
      renderWithAuth();

      await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge");

      const searchInput = screen.getByPlaceholderText(/Search by settlement, district/i);
      await act(async () => {
        fireEvent.change(searchInput, { target: { value: "NonExistentVillageXYZ" } });
      });

      await waitFor(() => {
        expect(
          screen.getByText("No Alerts Match Current Filter Criteria")
        ).toBeInTheDocument();
      });

      // Reset
      const resetBtn = screen.getByRole("button", { name: /Reset Filter Criteria/i });
      await act(async () => {
        fireEvent.click(resetBtn);
      });

      expect(
        await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge")
      ).toBeInTheDocument();
    });
  });

  describe("Officer Acknowledgment Flow", () => {
    it("allows duty officer to acknowledge a single alert", async () => {
      renderWithAuth();

      await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge");

      // Find Acknowledge button on the first unacknowledged card (exact text "Acknowledge", not "Acknowledge All")
      const ackButtons = screen.getAllByRole("button", { name: /^Acknowledge$/i });
      expect(ackButtons.length).toBeGreaterThanOrEqual(1);

      await act(async () => {
        fireEvent.click(ackButtons[0]);
      });

      // Verification: Success banner appears
      expect(
        await screen.findByText(/has been successfully acknowledged/i)
      ).toBeInTheDocument();

      // Acknowledged badge should show officer attribution
      expect(
        screen.getAllByText(/Acknowledged by District Magistrate \(Duty Officer\)/i).length
      ).toBeGreaterThanOrEqual(1);
    });

    it("executes bulk Acknowledge All action from action toolbar", async () => {
      renderWithAuth();

      await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge");

      const bulkAckBtn = screen.getByRole("button", { name: /Acknowledge All/i });
      expect(bulkAckBtn).not.toBeDisabled();

      await act(async () => {
        fireEvent.click(bulkAckBtn);
      });

      // Verification: Success message displayed
      expect(
        await screen.findByText(/Successfully acknowledged/i)
      ).toBeInTheDocument();

      // Pending count should now be 0 and button disabled
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Acknowledge All \(0\)/i })).toBeDisabled();
      });
    });
  });

  describe("Alert Detail Modal & M3-11 Explainability Audit", () => {
    it("opens detail modal, displays single trigger evaluations, and statutory notice", async () => {
      renderWithAuth();

      await screen.findByText("Critical Rainfall Threshold Exceeded — Joshimath Upper Ridge");

      // Click Audit Trail button on Joshimath alert
      const auditButtons = screen.getAllByRole("button", { name: /Audit Trail/i });
      await act(async () => {
        fireEvent.click(auditButtons[0]);
      });

      // Dialog opens
      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();

      // Granular evaluation table scoped inside dialog
      expect(within(dialog).getByText("M3-11 Deterministic Trigger Evaluations")).toBeInTheDocument();
      expect(within(dialog).getByText("rainfall_24h")).toBeInTheDocument();
      expect(within(dialog).getByText("slope_deg")).toBeInTheDocument();

      // Statutory Rule 12 Mandate Banner
      expect(
        within(dialog).getByText(/Statutory Mandate: Candidate Advisory Status/i)
      ).toBeInTheDocument();
      expect(
        within(dialog).getByText(/PROPOSED DYNAMIC ALERT CANDIDATE ONLY/i)
      ).toBeInTheDocument();

      // Close modal
      const closeBtn = within(dialog).getByRole("button", { name: /^Close$/i });
      await act(async () => {
        fireEvent.click(closeBtn);
      });

      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });
});
