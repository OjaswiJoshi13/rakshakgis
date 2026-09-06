import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { OperationsNav } from "@/components/operations/OperationsNav";
import { OperationsShell } from "@/components/operations/OperationsShell";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import OperationsHubPage from "@/app/operations/page";
import { AuthProvider } from "@/context/AuthContext";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations",
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

describe("Operations UI Shell & Navigation Suite (Chunk M6-01)", () => {
  describe("OperationsNav component", () => {
    it("renders all 8 officer operations navigation links with chunk badges", () => {
      render(<OperationsNav />);

      expect(screen.getByRole("navigation", { name: /Operations Navigation/i })).toBeInTheDocument();

      // Verify all operational areas exist as functional links
      expect(screen.getByText("Operations Hub")).toBeInTheDocument();
      expect(screen.getByText("Relocation")).toBeInTheDocument();
      expect(screen.getByText("Sites")).toBeInTheDocument();
      expect(screen.getByText("Scenarios")).toBeInTheDocument();
      expect(screen.getByText("Alerts")).toBeInTheDocument();
      expect(screen.getByText("Reports")).toBeInTheDocument();
      expect(screen.getByText("Officer Review")).toBeInTheDocument();
      expect(screen.getByText("Audit Log")).toBeInTheDocument();

      // Verify chunk badges
      expect(screen.getByText("M6-01")).toBeInTheDocument();
      expect(screen.getByText("M6-02")).toBeInTheDocument();
      expect(screen.getByText("M6-03")).toBeInTheDocument();
      expect(screen.getByText("M6-04")).toBeInTheDocument();
      expect(screen.getByText("M6-05")).toBeInTheDocument();
      expect(screen.getByText("M6-07")).toBeInTheDocument();
      expect(screen.getByText("M6-08")).toBeInTheDocument();
      expect(screen.getByText("M6-09")).toBeInTheDocument();
    });

    it("marks active page with aria-current='page'", () => {
      render(<OperationsNav />);
      const activeLink = screen.getByRole("link", { name: /Operations Hub/i });
      expect(activeLink).toHaveAttribute("aria-current", "page");
    });
  });

  describe("OperationsShell component", () => {
    it("renders operations header with branding, region and mode", () => {
      render(
        <AuthProvider>
          <OperationsShell>
            <div data-testid="test-ops-child">Operations Workspace Content</div>
          </OperationsShell>
        </AuthProvider>
      );

      expect(screen.getByText(/Operations Console • Chunk M6-01/i)).toBeInTheDocument();
      expect(screen.getByText("Disaster Response & Relocation Decision System")).toBeInTheDocument();
      expect(screen.getByText("Himalayan Pilot (Chamoli)")).toBeInTheDocument();
      expect(screen.getByText(/DEMO MODE/i)).toBeInTheDocument();
      expect(screen.getByTestId("test-ops-child")).toBeInTheDocument();
    });
  });

  describe("OperationsSectionShell component", () => {
    it("renders breadcrumb, title, chunk badge, Rule 12 protocol, and action toolbar", () => {
      render(
        <OperationsSectionShell
          title="Relocation Planner"
          description="Interactive relocation matching workflow."
          chunkId="M6-02"
          chunkTitle="Relocation Planner Workflow UI"
          prerequisiteChunk="Chunk M4-04 (Relocation Matching Engine)"
          actionToolbar={<button data-testid="custom-action">Run Matching</button>}
        >
          <div data-testid="section-content">Relocation Canvas Mount Point</div>
        </OperationsSectionShell>
      );

      expect(screen.getByText("Operations")).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Relocation Planner" })).toBeInTheDocument();
      expect(screen.getByText("M6-02")).toBeInTheDocument();
      expect(screen.getByText("Relocation Planner Workflow UI")).toBeInTheDocument();
      expect(screen.getByText(/Interactive relocation matching workflow/i)).toBeInTheDocument();
      expect(screen.getByText(/Rule 12 Mandate/i)).toBeInTheDocument();
      expect(screen.getByText(/Chunk M4-04/i)).toBeInTheDocument();
      expect(screen.getByTestId("custom-action")).toBeInTheDocument();
      expect(screen.getByTestId("section-content")).toBeInTheDocument();
    });
  });

  describe("OperationsHubPage component", () => {
    it("renders operational readiness parameters and 7 domain launch cards", () => {
      render(<OperationsHubPage />);

      expect(
        screen.getByRole("heading", {
          name: /Operations Management & Decision Support Console/i,
        })
      ).toBeInTheDocument();

      // Parameter metric cards
      expect(screen.getByText("Rule 12")).toBeInTheDocument();
      expect(screen.getByText("Active Operation Areas")).toBeInTheDocument();
      expect(screen.getByText("Spatial Coordinate System")).toBeInTheDocument();
      expect(screen.getByText("Decision Traceability")).toBeInTheDocument();

      // Module cards
      expect(screen.getByText("Relocation Planner Workflow UI")).toBeInTheDocument();
      expect(screen.getByText("Relocation Site Details & Infrastructure UI")).toBeInTheDocument();
      expect(screen.getByText("Scenario Simulator UI")).toBeInTheDocument();
      expect(screen.getByText("Real-Time Alerts & Threshold Warnings UI")).toBeInTheDocument();
      expect(screen.getByText("Report Generation & Export UI")).toBeInTheDocument();
      expect(screen.getByText("Officer Review & Action Sign-Off Workflow")).toBeInTheDocument();
      expect(screen.getByText("Audit Log & Traceability UI")).toBeInTheDocument();

      // Statutory Rule 12 Alert
      expect(
        screen.getByText(/Statutory Decision Governance — Rule 12 Compliance/i)
      ).toBeInTheDocument();
    });
  });
});
