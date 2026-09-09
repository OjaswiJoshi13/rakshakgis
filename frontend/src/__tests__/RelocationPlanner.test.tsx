import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import RelocationOperationsPage from "@/app/operations/relocation/page";
import { AuthProvider } from "@/context/AuthContext";
import * as relocationApi from "@/lib/api/relocation";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations/relocation",
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

describe("Relocation Planner Workflow UI Suite (Chunk M6-02)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithAuth = (props?: { defaultUseDatabase?: boolean }) => {
    return render(
      <AuthProvider>
        <RelocationOperationsPage defaultUseDatabase={props?.defaultUseDatabase ?? false} />
      </AuthProvider>
    );
  };

  describe("Page Header, Run Controls & Summary Cards", () => {
    it("renders page title, chunk badges, Rule 12 mandate, and initial summary cards", () => {
      renderWithAuth();

      // Verify breadcrumb & headings
      expect(screen.getByRole("heading", { name: "Relocation Planner" })).toBeInTheDocument();
      expect(screen.getByText("M6-02")).toBeInTheDocument();
      expect(screen.getByText("Relocation Planner Workflow UI")).toBeInTheDocument();
      expect(screen.getByText(/Chunk M4-04/i)).toBeInTheDocument();

      // Verify Rule 12 protocol notice
      expect(screen.getByText(/Rule 12 Mandate — Statutory Decision Support/i)).toBeInTheDocument();

      // Verify KPI Metric Cards
      expect(screen.getByText("Demanded Households")).toBeInTheDocument();
      expect(screen.getByText("155")).toBeInTheDocument();
      expect(screen.getByText("Allocated Households")).toBeInTheDocument();
      expect(screen.getByText("105")).toBeInTheDocument();
      expect(screen.getByText("Unassigned Deficit")).toBeInTheDocument();
      expect(screen.getByText("50")).toBeInTheDocument();
      expect(screen.getByText("Remaining Capacity")).toBeInTheDocument();
      expect(screen.getByText("40")).toBeInTheDocument(); // 8 + 32 + 0 = 40
    });

    it("displays algorithm and regional profile parameters", () => {
      renderWithAuth();

      expect(screen.getByText(/himalayan_pilot \(Chamoli\)/i)).toBeInTheDocument();
      expect(screen.getAllByText(/greedy_priority/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByRole("button", { name: /Pilot Evaluation Set/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Live Database/i })).toBeInTheDocument();
    });
  });

  describe("Village Assignment Table & Filtering", () => {
    it("renders all evaluated villages with status, priority, and destination sites", () => {
      renderWithAuth();

      // Check villages rendered
      expect(screen.getByText("Raini")).toBeInTheDocument();
      expect(screen.getByText("Peng")).toBeInTheDocument();
      expect(screen.getByText("Tapovan Upper")).toBeInTheDocument();
      expect(screen.getByText("Malari Outpost")).toBeInTheDocument();

      // Check destinations
      expect(screen.getAllByText("Joshimath Safe Terrace").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Pipalkoti Plateau")).toBeInTheDocument();

      // Check unassigned code
      expect(screen.getByText(/Code: \[insufficient_capacity\]/i)).toBeInTheDocument();
    });

    it("filters villages by status tabs (All, Assigned, Unassigned)", () => {
      renderWithAuth();

      // Click Unassigned tab
      const unassignedTab = screen.getByRole("tab", { name: /Unassigned \(1\)/i });
      fireEvent.click(unassignedTab);

      // Malari Outpost should be present, Raini should be filtered out
      expect(screen.getByText("Malari Outpost")).toBeInTheDocument();
      expect(screen.queryByText("Raini")).not.toBeInTheDocument();

      // Click Assigned tab
      const assignedTab = screen.getByRole("tab", { name: /Assigned \(3\)/i });
      fireEvent.click(assignedTab);

      expect(screen.getByText("Raini")).toBeInTheDocument();
      expect(screen.getByText("Peng")).toBeInTheDocument();
      expect(screen.queryByText("Malari Outpost")).not.toBeInTheDocument();
    });

    it("filters villages by search query", () => {
      renderWithAuth();

      const searchInput = screen.getByPlaceholderText(/Search village or site\.\.\./i);
      fireEvent.change(searchInput, { target: { value: "Tapovan" } });

      expect(screen.getByText("Tapovan Upper")).toBeInTheDocument();
      expect(screen.queryByText("Raini")).not.toBeInTheDocument();
      expect(screen.queryByText("Peng")).not.toBeInTheDocument();
    });
  });

  describe("Candidate Evaluation Explainability Audit Modal", () => {
    it("opens audit modal on clicking Audit button and displays candidate explainability", () => {
      renderWithAuth();

      // Find audit buttons (one per row)
      const auditButtons = screen.getAllByRole("button", { name: /Audit/i });
      // Click the audit button for Malari Outpost (index 3)
      fireEvent.click(auditButtons[3]);

      // Verify modal opens
      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();
      expect(within(dialog).getByText("Explainability Audit")).toBeInTheDocument();
      expect(within(dialog).getByText(/Village Unassigned: Code \[insufficient_capacity\]/i)).toBeInTheDocument();

      // Verify individual candidate site constraints inside dialog
      expect(within(dialog).getByText("Joshimath Safe Terrace")).toBeInTheDocument();
      expect(within(dialog).getByText("Urgam North Ridge")).toBeInTheDocument();
      expect(within(dialog).getByText(/Safety constraint failed/i)).toBeInTheDocument();

      // Close modal using footer Close Audit button
      const closeButton = within(dialog).getByRole("button", { name: "Close Audit" });
      fireEvent.click(closeButton);

      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  describe("View Mode Switching & Persisted Ledger", () => {
    it("switches between Matching Evaluation and Persisted Assignments Ledger", async () => {
      renderWithAuth();

      const ledgerTab = screen.getByRole("tab", { name: /Persisted Assignments Ledger/i });
      fireEvent.click(ledgerTab);

      // Verify ledger view header
      expect(
        await screen.findByText(/Persisted Relocation Assignments Ledger/i)
      ).toBeInTheDocument();

      // Verify sample persisted records loaded after async fetch
      expect(await screen.findByText("#1001")).toBeInTheDocument();
      expect(await screen.findByText("#1002")).toBeInTheDocument();

      // Switch back to matching run
      const matchingTab = screen.getByRole("tab", { name: /Matching Evaluation Run/i });
      fireEvent.click(matchingTab);

      expect(screen.getByText("Demanded Households")).toBeInTheDocument();
    });
  });

  describe("Batch Commit Assignments Dialog", () => {
    it("opens commit dialog, allows status/capacity selection, and shows success notice", async () => {
      const batchSpy = vi.spyOn(relocationApi, "batchCreateRelocationAssignments").mockResolvedValue({
        success: true,
        data: relocationApi.HIMALAYAN_PILOT_SAMPLE_ASSIGNMENTS,
      });

      renderWithAuth();

      // Open commit dialog
      const commitButton = screen.getByRole("button", { name: /Commit Assignments \(3\)/i });
      fireEvent.click(commitButton);

      // Verify dialog is open
      expect(screen.getByRole("dialog", { name: /Persist Relocation Assignments/i })).toBeInTheDocument();
      expect(screen.getByText(/Draft \(Recommended\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Commit Site Capacity Consumption/i)).toBeInTheDocument();

      // Toggle capacity checkbox
      const capacityCheckbox = screen.getByRole("checkbox");
      fireEvent.click(capacityCheckbox);
      expect(capacityCheckbox).toBeChecked();

      // Click Confirm & Persist
      const confirmButton = screen.getByRole("button", { name: /Confirm & Persist \(3\)/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(batchSpy).toHaveBeenCalledTimes(1);
      });

      // Dialog should close and success banner should appear
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      expect(
        await screen.findByText(/Successfully persisted 3 relocation assignments/i)
      ).toBeInTheDocument();
    });
  });

  describe("Live Database Default Mode", () => {
    it("defaults to Live Database when rendered without props and queries backend on mount", async () => {
      const matchSpy = vi
        .spyOn(relocationApi, "evaluateRelocationMatching")
        .mockResolvedValue({
          success: true,
          data: relocationApi.HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT,
        });

      render(
        <AuthProvider>
          <RelocationOperationsPage />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(matchSpy).toHaveBeenCalledWith({
          use_database_villages: true,
          use_database_sites: true,
          region_profile_id: "himalayan_pilot",
        });
      });
    });
  });
});
