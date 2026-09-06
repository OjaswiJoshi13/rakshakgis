import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import SitesOperationsPage from "@/app/operations/sites/page";
import { AuthProvider } from "@/context/AuthContext";
import * as sitesApi from "@/lib/api/sites";

// Mock next/navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations/sites",
  useSearchParams: () => mockSearchParams,
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

describe("Relocation Site Details & Infrastructure UI Suite (Chunk M6-03)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams.delete("siteId");

    vi.spyOn(sitesApi, "listCandidateSites").mockResolvedValue({
      success: true,
      data: sitesApi.HIMALAYAN_PILOT_SAMPLE_SITES,
      pagination: {
        total: 3,
        page: 1,
        page_size: 20,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      },
    });

    vi.spyOn(sitesApi, "getCandidateSiteDetail").mockImplementation(async (id: number) => ({
      success: true,
      data:
        sitesApi.HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[id] ||
        sitesApi.HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[101],
    }));

    vi.spyOn(sitesApi, "getCandidateSiteSuitability").mockImplementation(async (id: number) => ({
      success: true,
      data:
        sitesApi.HIMALAYAN_PILOT_SAMPLE_SUITABILITY[id] ||
        sitesApi.HIMALAYAN_PILOT_SAMPLE_SUITABILITY[101],
    }));

    vi.spyOn(sitesApi, "getCandidateSiteCapacity").mockImplementation(async (id: number) => ({
      success: true,
      data:
        sitesApi.HIMALAYAN_PILOT_SAMPLE_CAPACITY[id] ||
        sitesApi.HIMALAYAN_PILOT_SAMPLE_CAPACITY[101],
    }));
  });

  const renderWithAuth = () => {
    return render(
      <AuthProvider>
        <SitesOperationsPage />
      </AuthProvider>
    );
  };

  describe("Workspace Header & Candidate Sites Selector", () => {
    it("renders page title, chunk badge, Rule 12 protocol, and site selector", async () => {
      renderWithAuth();

      // Heading & breadcrumb
      expect(
        screen.getByRole("heading", { name: "Relocation Sites & Infrastructure" })
      ).toBeInTheDocument();
      expect(screen.getByText("M6-03")).toBeInTheDocument();
      expect(screen.getByText("Relocation Site Details & Infrastructure UI")).toBeInTheDocument();
      expect(screen.getByText(/Rule 12 Mandate/i)).toBeInTheDocument();

      // Selector list
      expect(await screen.findByText(/Candidate Sites \(3\)/i)).toBeInTheDocument();
      expect(screen.getAllByText("Joshimath Safe Terrace").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Pipalkoti Plateau")).toBeInTheDocument();
      expect(screen.getByText("Urgam North Ridge")).toBeInTheDocument();
    });

    it("displays default selected site topography and coordinates", async () => {
      renderWithAuth();

      // Topographic metrics for default site (Joshimath Safe Terrace)
      expect(await screen.findByText(/79.563°E, 30.556°N/i)).toBeInTheDocument();
      expect(screen.getByText(/(120,000|1,20,000) m²/)).toBeInTheDocument();
      expect(screen.getAllByText(/8.5°/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Safe ≤15°/i)).toBeInTheDocument();
      expect(screen.getByText("1890 m AMSL")).toBeInTheDocument();
    });
  });

  describe("Overview & Infrastructure Assets Tab", () => {
    it("renders site capacity KPI cards and infrastructure assets inventory table", async () => {
      renderWithAuth();

      // Capacity KPI cards
      expect(await screen.findByText("Housing Capacity")).toBeInTheDocument();
      expect(screen.getByText("85")).toBeInTheDocument();
      expect(screen.getByText("Available Capacity")).toBeInTheDocument();
      expect(screen.getByText("8")).toBeInTheDocument();
      expect(screen.getByText("Water Supply")).toBeInTheDocument();
      expect(screen.getByText("35,000")).toBeInTheDocument();
      expect(screen.getByText("Sanitation Units")).toBeInTheDocument();
      expect(screen.getByText("25")).toBeInTheDocument();

      // Infrastructure assets table
      expect(screen.getByText(/On-Site Infrastructure Assets \(4\)/i)).toBeInTheDocument();
      expect(screen.getByText("Joshimath Gravity Water Supply")).toBeInTheDocument();
      expect(
        screen.getByText("Helipad & Emergency Evacuation Staging Point")
      ).toBeInTheDocument();
      expect(screen.getByText("Joshimath Terrace Access Road")).toBeInTheDocument();
      expect(screen.getByText("Primary Health Sub-Center")).toBeInTheDocument();

      // Operational status badges
      const functionalBadges = screen.getAllByText("functional");
      expect(functionalBadges.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe("Multi-Criteria Suitability (M4-02) Tab", () => {
    it("renders M4-02 classification, overall score, hard constraints, and 9 criteria decomposition", async () => {
      renderWithAuth();

      // Switch to Suitability tab
      const suitabilityTab = await screen.findByRole("tab", {
        name: /Suitability Criteria \(M4-02\)/i,
      });
      fireEvent.click(suitabilityTab);

      // Verify classification and score
      expect(await screen.findByText("M4-02 Classification")).toBeInTheDocument();
      expect(screen.getByText("SUITABLE")).toBeInTheDocument();
      expect(screen.getByText("88.2")).toBeInTheDocument();
      expect(screen.getByText("Eligible")).toBeInTheDocument();

      // Verify hard constraint gates
      expect(screen.getByText("Terrain Slope <= 15°")).toBeInTheDocument();
      expect(screen.getByText("Hazard Buffer >= 500m")).toBeInTheDocument();
      expect(screen.getByText("Usable Capacity >= 20 HH")).toBeInTheDocument();
      const passBadges = screen.getAllByText("PASS");
      expect(passBadges.length).toBeGreaterThanOrEqual(3);

      // Verify 9 criteria decomposition
      expect(screen.getByText("Hazard Safety")).toBeInTheDocument();
      expect(screen.getByText("Capacity & Resource Limits")).toBeInTheDocument();
      expect(screen.getByText("Road & Transport Access")).toBeInTheDocument();
      expect(screen.getByText("Water Availability")).toBeInTheDocument();
      expect(screen.getByText("Healthcare Access")).toBeInTheDocument();
      expect(screen.getByText("School Access")).toBeInTheDocument();
      expect(screen.getByText("Emergency Services")).toBeInTheDocument();
      expect(screen.getByText("Livelihood Access")).toBeInTheDocument();
      expect(screen.getByText("Expansion Potential")).toBeInTheDocument();
    });
  });

  describe("Carrying Capacity & Sizing (M4-03) Tab", () => {
    it("renders weakest-link invariant, limiting factor, and 5-dimensional sizing grid", async () => {
      renderWithAuth();

      // Switch to Capacity tab
      const capacityTab = await screen.findByRole("tab", {
        name: /Carrying Capacity & Sizing \(M4-03\)/i,
      });
      fireEvent.click(capacityTab);

      // Verify weakest-link invariant
      expect(await screen.findByText(/Weakest-Link Bottleneck Invariant/i)).toBeInTheDocument();
      expect(
        screen.getAllByText(/min\(housing, water, sanitation, healthcare, shelter\)/i).length
      ).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Limiting Bottleneck Factor")).toBeInTheDocument();

      // Verify dimensions
      expect(screen.getByText("Habitable Land & Housing")).toBeInTheDocument();
      expect(screen.getByText(/Water Supply \(70 LPD\/capita\)/i)).toBeInTheDocument();
      expect(screen.getByText("Sanitation Facilities")).toBeInTheDocument();
      expect(screen.getByText("Healthcare Capacity")).toBeInTheDocument();
      expect(screen.getByText("Emergency Shelter")).toBeInTheDocument();
    });
  });

  describe("Site Selection & Unsuitable / Rejected Site Inspection", () => {
    it("switches to Pipalkoti Plateau when clicked in selector", async () => {
      renderWithAuth();

      // Click Pipalkoti Plateau button in selector
      const siteButton = await screen.findByRole("button", { name: /Pipalkoti Plateau/i });
      fireEvent.click(siteButton);

      // Header should update
      expect(await screen.findByText(/79.432°E, 30.428°N/i)).toBeInTheDocument();
      expect(screen.getByText("95,000 m²")).toBeInTheDocument();
      expect(screen.getByText("1350 m AMSL")).toBeInTheDocument();
      expect(screen.getByText(/Pipalkoti Lift Water System/i)).toBeInTheDocument();
    });

    it("correctly audits rejected site Urgam North Ridge with failed hard constraints", async () => {
      renderWithAuth();

      // Select Urgam North Ridge
      const rejectedSiteButton = await screen.findByRole("button", {
        name: /Urgam North Ridge/i,
      });
      fireEvent.click(rejectedSiteButton);

      // Verify slope warning
      expect(await screen.findByText(/18.4°/)).toBeInTheDocument();
      expect(screen.getByText(/Unsafe >15°/i)).toBeInTheDocument();

      // Switch to Suitability tab
      const suitabilityTab = screen.getByRole("tab", {
        name: /Suitability Criteria \(M4-02\)/i,
      });
      fireEvent.click(suitabilityTab);

      // Verify UNSUITABLE decision and FAIL badges
      expect(await screen.findByText("UNSUITABLE")).toBeInTheDocument();
      expect(screen.getByText("41.0")).toBeInTheDocument();
      expect(screen.getByText("Ineligible")).toBeInTheDocument();
      const failBadges = screen.getAllByText("FAIL");
      expect(failBadges.length).toBeGreaterThanOrEqual(2);
    });
  });
});
