import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ScenariosOperationsPage from "@/app/operations/scenarios/page";
import { AuthProvider } from "@/context/AuthContext";
import * as scenariosApi from "@/lib/api/scenarios";

// Mock Next.js navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations/scenarios",
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => ({
    get: (key: string) => (key === "scenario" ? "EXTREME_RAINFALL" : null),
  }),
}));

// Mock AuthContext
vi.mock("@/context/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
  useAuth: () => ({
    user: {
      id: 1,
      email: "officer@rakshakgis.gov.in",
      role: "district_officer",
      name: "District Magistrate",
    },
    isAuthenticated: true,
  }),
}));

describe("Scenario Simulator UI Suite (Chunk M6-04)", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(scenariosApi, "listScenarioDefinitions").mockResolvedValue({
      success: true,
      data: scenariosApi.CANONICAL_SCENARIO_CATALOG,
    });

    vi.spyOn(scenariosApi, "runScenarioSimulation").mockImplementation(
      async (req) => {
        const st = (req.scenario_type || "EXTREME_RAINFALL").toUpperCase() as scenariosApi.ScenarioType;
        return {
          success: true,
          data:
            scenariosApi.HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS[st] ||
            scenariosApi.HIMALAYAN_PILOT_SAMPLE_SIMULATION_OUTPUTS.EXTREME_RAINFALL,
        };
      }
    );
  });

  const renderWithAuth = () => {
    return render(
      <AuthProvider>
        <ScenariosOperationsPage />
      </AuthProvider>
    );
  };

  describe("Workspace Header & Configuration Panel", () => {
    it("renders page title, chunk badge, Rule 12 mandate, and canonical presets", async () => {
      renderWithAuth();

      // Heading & Chunk Badge
      expect(
        screen.getByRole("heading", { name: "Scenario Simulator" })
      ).toBeInTheDocument();
      expect(screen.getByText("M6-04")).toBeInTheDocument();
      expect(screen.getByText("Scenario Simulator UI")).toBeInTheDocument();
      expect(screen.getAllByText(/Rule 12 Mandate/i).length).toBeGreaterThanOrEqual(1);

      // Canonical Presets
      expect(screen.getByText("Normal / Baseline State")).toBeInTheDocument();
      expect(
        screen.getAllByText("Extreme Rainfall Simulation (+40%)").length
      ).toBeGreaterThanOrEqual(1);
      expect(
        screen.getAllByText("Flash Flood / GLOF Valley Inundation").length
      ).toBeGreaterThanOrEqual(1);
      expect(
        screen.getAllByText("Relocation Capacity Crisis (-50%)").length
      ).toBeGreaterThanOrEqual(1);

      // Initial Parameter Controls
      expect(screen.getByText("Rainfall Multiplier")).toBeInTheDocument();
      expect(screen.getAllByText(/1.40x/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Road Network Blockage")).toBeInTheDocument();
      expect(screen.getAllByText(/0%/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Site Capacity Reduction")).toBeInTheDocument();
      expect(screen.getByText("+10 pts")).toBeInTheDocument();
    });
  });

  describe("Scenario Preset Switching & Parameter Controls", () => {
    it("switches to Flash Flood preset and updates parameters accordingly", async () => {
      renderWithAuth();

      // Click Flash Flood preset card
      const flashFloodBtn = screen.getAllByText("Flash Flood / GLOF Valley Inundation")[0];
      await act(async () => {
        fireEvent.click(flashFloodBtn);
      });

      // Parameters should update to 1.20x rainfall, 15% road blockage, +35 pts flood hazard
      expect(screen.getAllByText(/1.20x/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/15%/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/\+35 pts/).length).toBeGreaterThanOrEqual(1);
    });

    it("switches to Capacity Crisis preset and shows 50% capacity reduction", async () => {
      renderWithAuth();

      // Click Capacity Crisis preset
      const capacityBtn = screen.getAllByText("Relocation Capacity Crisis (-50%)")[0];
      await act(async () => {
        fireEvent.click(capacityBtn);
      });

      // Parameters should show 50% capacity reduction
      expect(screen.getAllByText(/50%/).length).toBeGreaterThanOrEqual(1);
    });

    it("resets parameters to defaults when Reset Defaults is clicked", async () => {
      renderWithAuth();

      // Switch to Flash Flood
      await act(async () => {
        fireEvent.click(screen.getAllByText("Flash Flood / GLOF Valley Inundation")[0]);
      });
      expect(screen.getAllByText(/1.20x/).length).toBeGreaterThanOrEqual(1);

      // Click Reset Defaults
      const resetBtn = screen.getByRole("button", { name: /Reset Defaults/i });
      await act(async () => {
        fireEvent.click(resetBtn);
      });

      // Still at Flash Flood defaults
      expect(screen.getAllByText(/1.20x/).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Simulation Execution & Comparison Summary", () => {
    it("executes simulation run and displays delta KPI metrics and narrative", async () => {
      renderWithAuth();

      // Execute simulation
      const runBtn = screen.getByRole("button", { name: /Execute Simulation/i });
      fireEvent.click(runBtn);

      await waitFor(() => {
        expect(scenariosApi.runScenarioSimulation).toHaveBeenCalled();
      });

      // Delta comparison summary cards
      expect(screen.getByText("Average Risk Score")).toBeInTheDocument();
      expect(screen.getByText("Red Zones Triggered")).toBeInTheDocument();
      expect(screen.getByText("Immediate Urgency")).toBeInTheDocument();
      expect(screen.getByText("Unassigned Deficit")).toBeInTheDocument();
      expect(screen.getByText("Route Corridors")).toBeInTheDocument();

      // Analytical narrative
      expect(screen.getByText(/M4-06 Scenario Impact Synthesis/i)).toBeInTheDocument();
      expect(
        screen.getByText(/40% rainfall surge causes widespread risk escalation/i)
      ).toBeInTheDocument();
    });
  });

  describe("Domain Impact Tabs (Risk, Relocation, Routing)", () => {
    it("renders Risk & Red Zones tab with village shifts and dynamic red zones", async () => {
      renderWithAuth();

      // Risk tab should be active by default
      expect(
        screen.getByText(/Multi-Hazard Risk Escalation & Dynamic Red Zones/i)
      ).toBeInTheDocument();

      // Village risk rows
      expect(screen.getByText("Sunil")).toBeInTheDocument();
      expect(screen.getByText("Ravigram")).toBeInTheDocument();
      expect(screen.getByText("Marwari")).toBeInTheDocument();
      expect(screen.getByText("Manohar Bagh")).toBeInTheDocument();

      // Band shifts and Red Zone triggered badges
      const triggeredBadges = screen.getAllByText("Triggered");
      expect(triggeredBadges.length).toBeGreaterThanOrEqual(1);
    });

    it("switches to Relocation & Capacity tab and shows unassigned deficits", async () => {
      renderWithAuth();

      // Click Relocation tab
      const relocationTab = screen.getByRole("tab", {
        name: /Relocation & Capacity/i,
      });
      fireEvent.click(relocationTab);

      expect(
        screen.getByText(/Candidate Sites Capacity & Relocation Matching Impact/i)
      ).toBeInTheDocument();
      expect(
        screen.getAllByText("Joshimath Safe Terrace").length
      ).toBeGreaterThanOrEqual(1);
      expect(
        screen.getAllByText("Pipalkoti Plateau").length
      ).toBeGreaterThanOrEqual(1);
    });

    it("switches to Evacuation Routing tab and displays corridor severance and bypasses", async () => {
      renderWithAuth();

      // First select Flash Flood so we have diverted and cut-off routes
      act(() => {
        fireEvent.click(
          screen.getAllByText("Flash Flood / GLOF Valley Inundation")[0]
        );
      });

      // Click Evacuation Routing tab
      const routingTab = screen.getByRole("tab", {
        name: /Evacuation Routing/i,
      });
      act(() => {
        fireEvent.click(routingTab);
      });

      // Verify routing analysis table
      expect(
        screen.getByText(/M4-05 Evacuation Routing & Corridor Severance Analysis/i)
      ).toBeInTheDocument();
      expect(screen.getByText("Origin Village")).toBeInTheDocument();
      expect(screen.getByText("Destination Site")).toBeInTheDocument();
      expect(screen.getByText("Route Status")).toBeInTheDocument();
      expect(screen.getByText("Obstacles Avoided")).toBeInTheDocument();

      // Verify Diverted and Cut Off status badges
      const divertedBadges = screen.getAllByText("Diverted");
      expect(divertedBadges.length).toBeGreaterThanOrEqual(1);
      const cutOffBadges = screen.getAllByText("Cut Off");
      expect(cutOffBadges.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Error State Handling", () => {
    it("displays error banner when simulation execution fails", async () => {
      vi.spyOn(scenariosApi, "runScenarioSimulation").mockRejectedValueOnce(
        new Error("Network connection to M4-06 simulation engine timed out.")
      );

      renderWithAuth();

      const runBtn = screen.getByRole("button", { name: /Execute Simulation/i });
      fireEvent.click(runBtn);

      await waitFor(() => {
        expect(
          screen.getByText(/Network connection to M4-06 simulation engine timed out/i)
        ).toBeInTheDocument();
      });
    });
  });
});
