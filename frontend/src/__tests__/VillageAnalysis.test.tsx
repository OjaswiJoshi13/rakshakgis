import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import {
  VillageSelectorBar,
  VillageIdentityHeader,
  PopulationExposureCard,
  VulnerabilityAnalysisCard,
  MultiHazardRiskCard,
  RelocationPriorityCard,
  HistoricalEventsCard,
  CriticalInfrastructureCard,
  ExplainabilitySummary,
} from "@/components/villages";
import VillageAnalysisPage from "@/app/villages/page";
import { AuthProvider } from "@/context/AuthContext";
import { OperationalProvider, useOperational } from "@/context/OperationalContext";
import * as authService from "@/lib/auth";
import * as apiModule from "@/lib/api";
import { HabitationDetail, ScenarioSimulationOutput } from "@/types/villages";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  usePathname: () => "/villages",
  useSearchParams: () => new URLSearchParams(),
}));

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

const mockHabitationA: HabitationDetail = {
  id: "VILL-001",
  name: "Ravigram Upper Sector",
  census_code: "CENS-04821",
  region_profile_id: "himalayan_pilot",
  district: "Chamoli",
  block: "Joshimath",
  coordinates: [79.5678, 30.5543],
  elevation_m: 1890,
  slope_deg: 24.5,
  demographics: {
    total_population: 340,
    households: 78,
    elderly_count: 42,
    children_count: 65,
    disabled_count: null,
  },
  vulnerability: {
    social_vulnerability_score: 55.4,
    infrastructure_vulnerability_score: 62.0,
    vulnerability_band: "HIGH",
  },
  risk: {
    risk_score: 72.8,
    risk_band: "critical",
    raw_band_string: "CRITICAL",
    factors: {
      hazard_severity: 85.0,
      flood_exposure: 40.0,
      rainfall_intensity: 65.0,
      slope_landslide_susceptibility: 82.0,
      infrastructure_vulnerability: 62.0,
      social_vulnerability: 55.4,
    },
    is_red_zone_triggered: true,
  },
  relocation: {
    priority_score: 76.4,
    priority_band: "immediate",
    raw_priority_band_string: "IMMEDIATE",
    is_assigned: true,
    assigned_site_id: "SITE-101",
    assigned_site_name: "Pipalkoti Safe Terrace Site A",
    demanded_households: 78,
    allocated_households: 78,
    unassigned_code: null,
  },
  evacuation: {
    route_feasible: true,
    distance_km: 18.4,
    estimated_time_minutes: 42.0,
    blocked_corridors_count: 1,
    route_status: "active",
  },
};

const mockHabitationB: HabitationDetail = {
  id: "VILL-002",
  name: "Marwari Valley Cluster",
  census_code: null,
  region_profile_id: "himalayan_pilot",
  district: null,
  block: null,
  coordinates: null,
  elevation_m: null,
  slope_deg: null,
  demographics: {
    total_population: 180,
    households: 45,
    elderly_count: null,
    children_count: null,
    disabled_count: null,
  },
  vulnerability: {
    social_vulnerability_score: 38.0,
    infrastructure_vulnerability_score: 45.0,
  },
  risk: {
    risk_score: 44.5,
    risk_band: "moderate",
    raw_band_string: "MODERATE",
    factors: {
      hazard_severity: 40.0,
      flood_exposure: 60.0,
      rainfall_intensity: 35.0,
      slope_landslide_susceptibility: 30.0,
      infrastructure_vulnerability: 45.0,
      social_vulnerability: 38.0,
    },
    is_red_zone_triggered: false,
  },
  relocation: {
    priority_score: 48.0,
    priority_band: "medium_term",
    is_assigned: false,
    assigned_site_id: null,
    assigned_site_name: null,
    demanded_households: 45,
    allocated_households: 0,
    unassigned_code: "INSUFFICIENT_CAPACITY",
  },
};

const mockScenarioOutput: ScenarioSimulationOutput = {
  scenario_name: "Baseline Operational Normal",
  scenario_type: "NORMAL",
  region_profile_id: "himalayan_pilot",
  run_id: "RUN-TEST-001",
  status: "COMPLETED",
  started_at: "2026-09-06T12:00:00Z",
  completed_at: "2026-09-06T12:00:02Z",
  baseline_pipeline: {
    risk_results: [
      {
        village_id: "VILL-001",
        village_name: "Ravigram Upper Sector",
        risk_score: 72.8,
        risk_band: "CRITICAL",
        factor_breakdown: {
          hazard_severity: 85.0,
          flood_exposure: 40.0,
          rainfall_intensity: 65.0,
          slope_landslide_susceptibility: 82.0,
          infrastructure_vulnerability: 62.0,
          social_vulnerability: 55.4,
        },
      },
      {
        village_id: "VILL-002",
        village_name: "Marwari Valley Cluster",
        risk_score: 44.5,
        risk_band: "MODERATE",
        factor_breakdown: {
          hazard_severity: 40.0,
          flood_exposure: 60.0,
          rainfall_intensity: 35.0,
          slope_landslide_susceptibility: 30.0,
          infrastructure_vulnerability: 45.0,
          social_vulnerability: 38.0,
        },
      },
    ],
    red_zone_result: {
      total_evaluated: 2,
      triggered_count: 1,
      triggered_village_ids: ["VILL-001"],
      candidate_ids: ["VILL-001"],
    },
    priority_results: [
      {
        village_id: "VILL-001",
        village_name: "Ravigram Upper Sector",
        priority_score: 76.4,
        priority_band: "immediate",
      },
      {
        village_id: "VILL-002",
        village_name: "Marwari Valley Cluster",
        priority_score: 48.0,
        priority_band: "medium_term",
      },
    ],
    matching_result: {
      total_villages: 2,
      assigned_count: 1,
      unassigned_count: 1,
      assignments: [
        {
          village_id: "VILL-001",
          village_name: "Ravigram Upper Sector",
          assigned_site_id: "SITE-101",
          assigned_site_name: "Pipalkoti Safe Terrace Site A",
          is_assigned: true,
          demanded_households: 78,
          allocated_households: 78,
        },
        {
          village_id: "VILL-002",
          village_name: "Marwari Valley Cluster",
          is_assigned: false,
          demanded_households: 45,
          allocated_households: 0,
          unassigned_code: "INSUFFICIENT_CAPACITY",
        },
      ],
    },
    routing_result: {
      routes_evaluated: 1,
      feasible_routes_count: 1,
      unroutable_count: 0,
      routes: [
        {
          village_id: "VILL-001",
          site_id: "SITE-101",
          is_feasible: true,
          distance_km: 18.4,
          estimated_time_minutes: 42.0,
          blocked_avoided_count: 1,
          route_status: "active",
        },
      ],
    },
  },
  scenario_pipeline: {
    risk_results: [],
    red_zone_result: { total_evaluated: 0, triggered_count: 0, triggered_village_ids: [], candidate_ids: [] },
    priority_results: [],
  },
};

describe("Village Vulnerability Detail / Habitation Analysis (Chunk M5-06)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
    apiModule.apiCache.clear();
  });

  describe("VillageSelectorBar Component", () => {
    it("renders selector bar with search input, count, and operational context", () => {
      const handleSelect = vi.fn();
      const handleSearch = vi.fn();

      render(
        <OperationalProvider initialState={{ dataMode: "demo", activeRegion: "himalayan_pilot" }}>
          <VillageSelectorBar
            villages={[mockHabitationA, mockHabitationB]}
            selectedVillageId="VILL-001"
            onSelectVillage={handleSelect}
            searchQuery=""
            onSearchChange={handleSearch}
          />
        </OperationalProvider>
      );

      expect(screen.getByRole("region", { name: /Habitation Selector/i })).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search settlements by name or ID/i)).toBeInTheDocument();
      expect(screen.getByText("DEMO MODE")).toBeInTheDocument();
      expect(screen.getByText("Region: himalayan_pilot")).toBeInTheDocument();
      expect(screen.getByText("2 Baseline Settlements")).toBeInTheDocument();
    });

    it("triggers onSelectVillage when dropdown selection changes", () => {
      const handleSelect = vi.fn();
      render(
        <OperationalProvider>
          <VillageSelectorBar
            villages={[mockHabitationA, mockHabitationB]}
            selectedVillageId="VILL-001"
            onSelectVillage={handleSelect}
            searchQuery=""
            onSearchChange={vi.fn()}
          />
        </OperationalProvider>
      );

      const dropdown = screen.getByLabelText(/Select habitation/i);
      fireEvent.change(dropdown, { target: { value: "VILL-002" } });
      expect(handleSelect).toHaveBeenCalledWith("VILL-002");
    });
  });

  describe("VillageIdentityHeader Component", () => {
    it("renders settlement identity, census code, and dynamic Red Zone active trigger", () => {
      render(<VillageIdentityHeader habitation={mockHabitationA} />);

      expect(screen.getByText("Ravigram Upper Sector")).toBeInTheDocument();
      expect(screen.getByText("ID: VILL-001")).toBeInTheDocument();
      expect(screen.getByText("Census: CENS-04821")).toBeInTheDocument();
      expect(screen.getByText(/RED ZONE TRIGGER ACTIVE/i)).toBeInTheDocument();
      expect(screen.getByText(/30.5543° N, 79.5678° E/i)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: /View Ravigram Upper Sector on GIS Interactive Map/i })).toHaveAttribute(
        "href",
        "/gis"
      );
    });

    it("renders standard monitoring status when Red Zone trigger is not active", () => {
      render(<VillageIdentityHeader habitation={mockHabitationB} />);

      expect(screen.getByText("Marwari Valley Cluster")).toBeInTheDocument();
      expect(screen.getByText(/STANDARD MONITORING/i)).toBeInTheDocument();
      expect(screen.getByText("Coordinates unavailable")).toBeInTheDocument();
    });

    it("never fabricates physical slope degrees from normalized landslide susceptibility index", () => {
      const habitationWithoutSlope: HabitationDetail = {
        ...mockHabitationA,
        slope_deg: null,
        risk: {
          ...mockHabitationA.risk,
          factors: {
            slope_landslide_susceptibility: 82.0,
          },
        },
      };

      render(<VillageIdentityHeader habitation={habitationWithoutSlope} />);
      // 82 * 0.45 = 36.9
      expect(screen.queryByText(/36\.9/)).not.toBeInTheDocument();
      expect(screen.queryByText(/°.*slope/i)).not.toBeInTheDocument();
    });
  });

  describe("PopulationExposureCard Component", () => {
    it("renders total population, households, and demographic groups", () => {
      render(<PopulationExposureCard habitation={mockHabitationA} />);

      expect(screen.getByText("Demographics & Exposure")).toBeInTheDocument();
      expect(screen.getByText("340")).toBeInTheDocument();
      expect(screen.getByText("78")).toBeInTheDocument();
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("65")).toBeInTheDocument();
    });

    it("clearly distinguishes unavailable fields with proper placeholder", () => {
      render(<PopulationExposureCard habitation={mockHabitationB} />);

      expect(screen.getByText("180")).toBeInTheDocument();
      expect(screen.getByText("45")).toBeInTheDocument();
      expect(screen.getByText("Unavailable from backend")).toBeInTheDocument();
    });

    it("never fabricates population from households (e.g. demanded_households * 4)", () => {
      const habitationWithoutPop: HabitationDetail = {
        ...mockHabitationA,
        demographics: {
          total_population: null,
          households: 78,
          elderly_count: null,
          children_count: null,
        },
      };

      render(<PopulationExposureCard habitation={habitationWithoutPop} />);

      expect(screen.getByText("Census record unavailable")).toBeInTheDocument();
      expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("78")).toBeInTheDocument();
      // Ensure 78 * 4 = 312 is NEVER rendered in the document
      expect(screen.queryByText("312")).not.toBeInTheDocument();
    });
  });

  describe("VulnerabilityAnalysisCard Component", () => {
    it("renders social and infrastructure vulnerability factors", () => {
      render(<VulnerabilityAnalysisCard habitation={mockHabitationA} />);

      expect(screen.getByText("Vulnerability & Isolation")).toBeInTheDocument();
      expect(screen.getByText("55.4 / 100")).toBeInTheDocument();
      expect(screen.getByText("62.0 / 100")).toBeInTheDocument();
      expect(screen.getByLabelText("Social Vulnerability Score")).toHaveAttribute("aria-valuenow", "55.4");
      expect(screen.getByLabelText("Infrastructure Isolation Score")).toHaveAttribute("aria-valuenow", "62");
    });

    it("does not calculate or render client-side demographic dependency ratio", () => {
      render(<VulnerabilityAnalysisCard habitation={mockHabitationA} />);

      // mockHabitationA has elderly: 42, children: 65, total: 340 (which would be 31.5%)
      expect(screen.queryByText(/Dependency:/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/31\.5%/)).not.toBeInTheDocument();
      expect(screen.getByText("Socio-economic & demographic sensitivity")).toBeInTheDocument();
    });
  });

  describe("MultiHazardRiskCard Component", () => {
    it("renders composite risk score, risk band, and 6-factor decomposition", () => {
      render(<MultiHazardRiskCard habitation={mockHabitationA} />);

      expect(screen.getByText("Multi-Hazard Risk Assessment")).toBeInTheDocument();
      expect(screen.getByText("72.8 / 100")).toBeInTheDocument();
      expect(screen.getByText(/CRITICAL/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Hazard Severity/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Flood Exposure/i)).toBeInTheDocument();
      expect(screen.getByText(/Rainfall Intensity/i)).toBeInTheDocument();
      expect(screen.getByText(/Slope \/ Landslide/i)).toBeInTheDocument();
      expect(screen.getByText(/Primary Risk Driver/i)).toBeInTheDocument();
    });

    it("ensures authoritative backend risk band takes strict precedence over generic frontend thresholds", () => {
      // Score 55 would generically map to "high" (50-70), but backend overrides as "critical"
      const backendCriticalHabitation: HabitationDetail = {
        ...mockHabitationA,
        risk: {
          risk_score: 55.0,
          risk_band: "critical",
          raw_band_string: "CRITICAL",
          factors: {
            hazard_severity: 55.0,
          },
          is_red_zone_triggered: false,
        },
      };

      render(<MultiHazardRiskCard habitation={backendCriticalHabitation} />);

      expect(screen.getByText("55.0 / 100")).toBeInTheDocument();
      // Must display Critical (backend classification), not High (generic threshold)
      expect(screen.getByText(/Critical/i)).toBeInTheDocument();
      expect(screen.queryByText(/^High$/i)).not.toBeInTheDocument();
    });
  });

  describe("RelocationPriorityCard Component", () => {
    it("renders relocation priority score, assignment, and evacuation routing path", () => {
      render(<RelocationPriorityCard habitation={mockHabitationA} />);

      expect(screen.getByText("Relocation Priority & Evacuation")).toBeInTheDocument();
      expect(screen.getByText("76.4 / 100")).toBeInTheDocument();
      expect(screen.getByText(/SITE ASSIGNED/i)).toBeInTheDocument();
      expect(screen.getByText(/Pipalkoti Safe Terrace Site A/i)).toBeInTheDocument();
      expect(screen.getByText("FEASIBLE CORRIDOR")).toBeInTheDocument();
      expect(screen.getByText("18.4 km")).toBeInTheDocument();
      expect(screen.getByText("42 mins")).toBeInTheDocument();
    });

    it("displays unassigned status code when site is not assigned", () => {
      render(<RelocationPriorityCard habitation={mockHabitationB} />);

      expect(screen.getByText("48.0 / 100")).toBeInTheDocument();
      expect(screen.getByText("INSUFFICIENT_CAPACITY")).toBeInTheDocument();
    });

    it("ensures authoritative backend relocation priority band takes precedence", () => {
      // Score 45 would generically map to "medium_term", but backend overrides as "immediate"
      const backendImmediateHabitation: HabitationDetail = {
        ...mockHabitationA,
        relocation: {
          priority_score: 45.0,
          priority_band: "immediate",
          raw_priority_band_string: "IMMEDIATE",
          is_assigned: true,
          assigned_site_id: "SITE-101",
          assigned_site_name: "Safe Site",
          demanded_households: 78,
          allocated_households: 78,
          unassigned_code: null,
        },
      };

      render(<RelocationPriorityCard habitation={backendImmediateHabitation} />);

      expect(screen.getByText("45.0 / 100")).toBeInTheDocument();
      // Must display Immediate Action (backend classification), not Medium Term (generic threshold)
      expect(screen.getByText(/Immediate Action/i)).toBeInTheDocument();
      expect(screen.queryByText(/Medium Term/i)).not.toBeInTheDocument();
    });
  });

  describe("HistoricalEventsCard & CriticalInfrastructureCard Components", () => {
    it("renders historical events card with informative unavailable status note", () => {
      render(<HistoricalEventsCard />);

      expect(screen.getByText("Historical Disaster Events")).toBeInTheDocument();
      expect(screen.getByText("Historical Event Registry Unavailable")).toBeInTheDocument();
      expect(screen.getByText(/no historical events are fabricated/i)).toBeInTheDocument();
    });

    it("renders critical infrastructure card with informative unavailable status note", () => {
      render(<CriticalInfrastructureCard />);

      expect(screen.getByText("Critical Infrastructure & Public Assets")).toBeInTheDocument();
      expect(screen.getByText("Infrastructure Asset Inventory Unavailable")).toBeInTheDocument();
      expect(screen.getByText(/no assets are fabricated/i)).toBeInTheDocument();
    });
  });

  describe("ExplainabilitySummary Component", () => {
    it("renders 4-stage officer decision-support trace pipeline", () => {
      render(<ExplainabilitySummary habitation={mockHabitationA} />);

      expect(screen.getByText("Officer Decision Support Pipeline")).toBeInTheDocument();
      expect(screen.getByText("1. Settlement")).toBeInTheDocument();
      expect(screen.getByText("2. Exposure & Vulnerability")).toBeInTheDocument();
      expect(screen.getByText("3. Multi-Hazard Risk")).toBeInTheDocument();
      expect(screen.getByText("4. Relocation Urgency")).toBeInTheDocument();
      expect(screen.getByText(/Zero LLM numerical calculation/i)).toBeInTheDocument();
    });
  });

  describe("VillageAnalysisPage Full Integration", () => {
    it("renders page with backend scenario baseline and allows switching settlements", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      vi.spyOn(apiModule.apiClient, "post").mockImplementation(async (path: string) => {
        if (path.includes("/scenarios/run")) {
          return { success: true, data: mockScenarioOutput };
        }
        return { success: true, data: {} };
      });

      vi.spyOn(apiModule.apiClient, "get").mockImplementation(async (path: string) => {
        if (path.includes("/relocation/assignments")) {
          return { success: true, data: [], pagination: { total: 0, page: 1, page_size: 50, total_pages: 0, has_next: false, has_prev: false } };
        }
        if (path.includes("/routes")) {
          return { success: true, data: [], pagination: { total: 0, page: 1, page_size: 50, total_pages: 0, has_next: false, has_prev: false } };
        }
        return { success: true, data: {} };
      });

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider initialState={{ activeRegion: "himalayan_pilot", dataMode: "demo" }}>
            <VillageAnalysisPage />
          </OperationalProvider>
        </AuthProvider>
      );

      // Verify that primary settlement loads
      await waitFor(() => {
        expect(screen.getByRole("heading", { level: 1, name: "Ravigram Upper Sector" })).toBeInTheDocument();
      });

      expect(screen.getByText("2 Baseline Settlements")).toBeInTheDocument();
      expect(screen.getByText(/Baseline Assessment Scope/i)).toBeInTheDocument();
      expect(screen.getByText("72.8 / 100")).toBeInTheDocument();

      // Switch to second settlement via selector dropdown
      const dropdown = screen.getByLabelText(/Select habitation/i);
      fireEvent.change(dropdown, { target: { value: "VILL-002" } });

      await waitFor(() => {
        expect(screen.getByRole("heading", { level: 1, name: "Marwari Valley Cluster" })).toBeInTheDocument();
      });
      expect(screen.getByText("44.5 / 100")).toBeInTheDocument();
    });

    it("handles empty habitations response gracefully", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      vi.spyOn(apiModule.apiClient, "post").mockResolvedValue({
        success: true,
        data: {
          ...mockScenarioOutput,
          baseline_pipeline: {
            risk_results: [],
            red_zone_result: { total_evaluated: 0, triggered_count: 0, triggered_village_ids: [], candidate_ids: [] },
            priority_results: [],
          },
        },
      });

      vi.spyOn(apiModule.apiClient, "get").mockResolvedValue({
        success: true,
        data: [],
        pagination: { total: 0, page: 1, page_size: 50, total_pages: 0, has_next: false, has_prev: false },
      });

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider initialState={{ activeRegion: "himalayan_pilot" }}>
            <VillageAnalysisPage />
          </OperationalProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByRole("region", { name: /No habitations available/i })).toBeInTheDocument();
      });
      expect(screen.getByText(/No Settlements Available for Region/i)).toBeInTheDocument();
    });

    it("handles API error state with retry option", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      vi.spyOn(apiModule.apiClient, "post").mockRejectedValue(new Error("Connection refused by backend gateway"));
      vi.spyOn(apiModule.apiClient, "get").mockResolvedValue({ success: true, data: [] });

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider>
            <VillageAnalysisPage />
          </OperationalProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByRole("alert")).toBeInTheDocument();
      });
      expect(screen.getByText("Failed to Load Settlement Vulnerability Data")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Retry Assessment/i })).toBeInTheDocument();
    });

    it("resets selected village when activeRegion changes", async () => {
      authService.setStoredToken("valid-officer-token", 3600);
      vi.spyOn(authService, "getMeApi").mockResolvedValue(mockOfficerUser);

      vi.spyOn(apiModule.apiClient, "post").mockResolvedValue({
        success: true,
        data: mockScenarioOutput,
      });
      vi.spyOn(apiModule.apiClient, "get").mockResolvedValue({ success: true, data: [] });

      const RegionSwitcher: React.FC = () => {
        const { setActiveRegion } = useOperational();
        return (
          <button onClick={() => setActiveRegion("riverine_delta")}>
            Switch Region
          </button>
        );
      };

      render(
        <AuthProvider initialState={{ user: mockOfficerUser, isAuthenticated: true, token: "valid-officer-token" }}>
          <OperationalProvider initialState={{ activeRegion: "himalayan_pilot" }}>
            <RegionSwitcher />
            <VillageAnalysisPage />
          </OperationalProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { level: 1, name: "Ravigram Upper Sector" })).toBeInTheDocument();
      });

      // Trigger active region transition via context
      fireEvent.click(screen.getByText("Switch Region"));

      // Verify region pill updated to riverine_delta
      await waitFor(() => {
        expect(screen.getByText("Region: riverine_delta")).toBeInTheDocument();
      });
    });
  });
});
