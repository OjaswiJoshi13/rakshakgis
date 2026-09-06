import React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ReviewOperationsPage from "@/app/operations/review/page";
import * as reviewApi from "@/lib/api/review";

// Mock Next.js navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations/review",
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
      id: 101,
      email: "ddmo_chamoli@rakshakgis.gov.in",
      role: "district_officer",
      name: "Suhani Amnerkar (DDMO)",
    },
    isAuthenticated: true,
  }),
}));

describe("Officer Review & Action Sign-Off UI Suite (Chunk M6-08)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    reviewApi.resetReviewCache();
  });

  it("1. Renders Officer Review Section Shell with M6-08 badge, title, and Rule 12 authority posture", async () => {
    render(<ReviewOperationsPage />);

    // Header & Section Shell
    expect(await screen.findByRole("heading", { name: "Officer Review & Sign-Off" })).toBeInTheDocument();
    expect(screen.getByText("M6-08")).toBeInTheDocument();
    expect(screen.getByText("Officer Review & Action Sign-Off Workflow")).toBeInTheDocument();

    // Authority Posture
    expect(screen.getByText(/Authority Level:/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Suhani Amnerkar \(DDMO\)/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/3 Pending Sign-Off/i)).toBeInTheDocument();
  });

  it("2. Renders Review Queue with seed dossiers, type badges, and urgency levels", async () => {
    render(<ReviewOperationsPage />);

    const queue = await screen.findByTestId("review-queue");
    expect(within(queue).getByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();
    expect(within(queue).getByText("Extreme Rainfall Shock Escalation (+40%)")).toBeInTheDocument();
    expect(within(queue).getByText("Flash Flood & GLOF Inundation Surge")).toBeInTheDocument();

    // Queue header and count badge
    expect(screen.getByText("Review Queue")).toBeInTheDocument();
    expect(screen.getByText("3 Total")).toBeInTheDocument();
  });

  it("3. Switches Queue Filter Tabs between All, Pending, and Decided", async () => {
    render(<ReviewOperationsPage />);

    const queue = await screen.findByTestId("review-queue");
    expect(within(queue).getByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Pending tab
    const pendingTab = screen.getByTestId("filter-tab-pending");
    fireEvent.click(pendingTab);
    expect(within(queue).getByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Decided tab (initially 0 decided)
    const decidedTab = screen.getByTestId("filter-tab-decided");
    fireEvent.click(decidedTab);
    expect(
      screen.getByText("No recommendation dossiers found in this view.")
    ).toBeInTheDocument();

    // Return to All tab
    const allTab = screen.getByTestId("filter-tab-all");
    fireEvent.click(allTab);
    expect(within(queue).getByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();
  });

  it("4. Filters Review Queue items using the search input", async () => {
    render(<ReviewOperationsPage />);

    const queue = await screen.findByTestId("review-queue");
    expect(within(queue).getByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/Search dossier by name, ID, or action/i);
    fireEvent.change(searchInput, { target: { value: "Flash Flood" } });

    // Should only show the Flash Flood dossier in the queue
    expect(within(queue).getByText("Flash Flood & GLOF Inundation Surge")).toBeInTheDocument();
    expect(within(queue).queryByText("Chamoli Monsoon Priority Relocation Plan")).not.toBeInTheDocument();
  });

  it("5. Inspects selected recommendation and renders analytical details, KPIs, and village plan", async () => {
    render(<ReviewOperationsPage />);

    // First dossier (Relocation Plan) is selected by default
    expect(await screen.findByText("PROPOSED OPERATIONAL DIRECTIVE")).toBeInTheDocument();
    expect(
      screen.getAllByText(/Execute formal village-to-site relocation allocations for 3 vulnerable settlements/i).length
    ).toBeGreaterThan(0);

    // KPI Metrics
    expect(screen.getByText("Target Settlements")).toBeInTheDocument();
    expect(screen.getByText("Allocated Sites")).toBeInTheDocument();
    expect(screen.getByText("320 / 380")).toBeInTheDocument();
    expect(screen.getByText("60 HH")).toBeInTheDocument();

    // Village allocation table
    expect(screen.getByText("Proposed Settlement Allocation Plan")).toBeInTheDocument();
    expect(screen.getByText("Raini")).toBeInTheDocument();
    expect(screen.getByText("Peng")).toBeInTheDocument();
    expect(screen.getByText("Tapovan Upper")).toBeInTheDocument();
    expect(screen.getByText("Malari Outpost")).toBeInTheDocument();
    expect(screen.getByText("None (Capacity Exhausted)")).toBeInTheDocument();
  });

  it("6. Selecting a scenario dossier switches inspector to scenario simulation parameters", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Select the Extreme Rainfall scenario
    const scenarioButton = screen.getByText("Extreme Rainfall Shock Escalation (+40%)");
    fireEvent.click(scenarioButton);

    // Inspector updates
    expect(await screen.findByText("Simulated Scenario Parameters & Threat Response")).toBeInTheDocument();
    expect(screen.getByText("Rainfall Surge Multiplier")).toBeInTheDocument();
    expect(screen.getByText("1.4x")).toBeInTheDocument();
    expect(screen.getByText("Transit Road Blockage")).toBeInTheDocument();
  });

  it("7. Approve Action: requires statutory confirmation checkbox before approval", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Submit button without checking confirmation
    const submitBtn = screen.getByRole("button", { name: /Sign Off & Enact Action/i });
    fireEvent.click(submitBtn);

    // Should display validation error
    expect(
      await screen.findByText(/You must confirm the statutory Rule 12 verification checkbox before approving/i)
    ).toBeInTheDocument();
  });

  it("8. Approve Action: successfully approves recommendation when statutory confirmation is checked", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Check the Rule 12 verification checkbox
    const confirmCheckbox = screen.getByRole("checkbox", {
      name: /Rule 12 Ground Verification Certification/i,
    });
    fireEvent.click(confirmCheckbox);

    // Enter optional notes
    const textarea = screen.getByRole("textbox", {
      name: /Administrative Directives \/ Notes/i,
    });
    fireEvent.change(textarea, {
      target: { value: "Approved following field inspection by Tehsildar Joshimath." },
    });

    // Click Sign Off
    const submitBtn = screen.getByRole("button", { name: /Sign Off & Enact Action/i });
    fireEvent.click(submitBtn);

    // Check success feedback notification
    expect(
      await screen.findByText(/has been approved for operational execution/i)
    ).toBeInTheDocument();

    // Check that DecisionStatusBanner is now visible
    expect(
      screen.getByText("OFFICIALLY APPROVED UNDER RULE 12 PROTOCOL")
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Suhani Amnerkar \(DDMO\)/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Approved following field inspection by Tehsildar Joshimath/i)
    ).toBeInTheDocument();

    // Authority header counters updated: 2 Pending, 1 Enacted
    expect(screen.getByText(/2 Pending Sign-Off/i)).toBeInTheDocument();
    expect(screen.getByText(/1 Enacted/i)).toBeInTheDocument();
  });

  it("9. Reject Action: requires mandatory rationale and displays validation error when empty", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Switch to Reject mode
    const rejectModeBtn = screen.getByRole("button", { name: /Reject Action/i });
    fireEvent.click(rejectModeBtn);

    // Submit without rationale
    const submitBtn = screen.getByRole("button", { name: /Submit Official Rejection/i });
    fireEvent.click(submitBtn);

    // Should display validation error
    expect(
      await screen.findByText(/Official rationale is mandatory when rejecting an operational recommendation/i)
    ).toBeInTheDocument();
  });

  it("10. Reject Action: successfully records official rejection with rationale", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Switch to Reject mode
    const rejectModeBtn = screen.getByRole("button", { name: /Reject Action/i });
    fireEvent.click(rejectModeBtn);

    // Enter mandatory rationale
    const textarea = screen.getByRole("textbox", {
      name: /Official Justification for Rejection/i,
    });
    fireEvent.change(textarea, {
      target: { value: "Rejected due to active fissure detection on northern slope of Pipalkoti site." },
    });

    // Submit Rejection
    const submitBtn = screen.getByRole("button", { name: /Submit Official Rejection/i });
    fireEvent.click(submitBtn);

    // Check success feedback and status banner
    expect(
      await screen.findByText(/has been officially rejected/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("OFFICIALLY REJECTED BY DISTRICT OFFICER")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/active fissure detection on northern slope/i)
    ).toBeInTheDocument();
  });

  it("11. Return for Revision Action: requires mandatory revision instructions", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Switch to Revision mode
    const revisionModeBtn = screen.getByRole("button", { name: /Return for Revision/i });
    fireEvent.click(revisionModeBtn);

    // Submit without instructions
    const submitBtn = screen.getByRole("button", { name: /Return for Technical Revision/i });
    fireEvent.click(submitBtn);

    // Should display validation error
    expect(
      await screen.findByText(/Specific revision instructions are mandatory when returning a recommendation for revision/i)
    ).toBeInTheDocument();
  });

  it("12. Return for Revision Action: successfully records revision request with instructions", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // Switch to Revision mode
    const revisionModeBtn = screen.getByRole("button", { name: /Return for Revision/i });
    fireEvent.click(revisionModeBtn);

    // Enter instructions
    const textarea = screen.getByRole("textbox", {
      name: /Specific Revision Instructions/i,
    });
    fireEvent.change(textarea, {
      target: { value: "Re-run matching with Joshimath Safe Terrace expanded capacity to accommodate Malari Outpost." },
    });

    // Submit
    const submitBtn = screen.getByRole("button", { name: /Return for Technical Revision/i });
    fireEvent.click(submitBtn);

    // Check feedback & status banner
    expect(
      await screen.findByText(/has been returned for technical planner revision/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("RETURNED TO TECHNICAL PLANNERS FOR REVISION")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/expanded capacity to accommodate Malari Outpost/i)
    ).toBeInTheDocument();
  });

  it("13. Allows reopening / re-evaluating a decided recommendation", async () => {
    render(<ReviewOperationsPage />);

    expect(await screen.findByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();

    // First approve it
    const confirmCheckbox = screen.getByRole("checkbox", {
      name: /Rule 12 Ground Verification Certification/i,
    });
    fireEvent.click(confirmCheckbox);

    const submitBtn = screen.getByRole("button", { name: /Sign Off & Enact Action/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText("OFFICIALLY APPROVED UNDER RULE 12 PROTOCOL")
    ).toBeInTheDocument();

    // Click "Re-evaluate Decision"
    const reopenBtn = screen.getByRole("button", { name: /Re-evaluate Decision/i });
    fireEvent.click(reopenBtn);

    // Reverts back to pending review state and shows decision form again
    expect(
      await screen.findByText(/reopened for re-evaluation/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Awaiting Officer Sign-Off")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign Off & Enact Action/i })).toBeInTheDocument();
  });

  it("14. Statutory Rule 12 Notice is rendered prominently across the workspace", async () => {
    render(<ReviewOperationsPage />);

    expect(
      await screen.findByText(/Statutory Rule 12 Protocol — Mandatory Officer Authorization/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/have zero legal effect until signed off by the reviewing officer/i)
    ).toBeInTheDocument();
  });
});
