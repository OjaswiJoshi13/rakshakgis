import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within, waitFor } from "@testing-library/react";
import AuditOperationsPage from "@/app/operations/audit/page";
import * as auditApi from "@/lib/api/audit";

// Mock next/navigation
const mockPush = vi.fn();
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/operations/audit",
  useSearchParams: () => mockSearchParams,
}));

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
});

describe("Audit Log & Traceability UI Suite (Chunk M6-09)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auditApi.resetAuditCache();
  });

  it("1. Renders Audit Section Shell with M6-09 badge, title, and statutory governance posture", async () => {
    render(<AuditOperationsPage />);

    expect(await screen.findByRole("heading", { name: "Audit Log & Traceability" })).toBeInTheDocument();
    expect(screen.getByText("M6-09")).toBeInTheDocument();
    expect(screen.getByText("Audit Log & Traceability UI")).toBeInTheDocument();

    // Governance Posture
    expect(screen.getByText(/Statutory Governance & Compliance Ledger/i)).toBeInTheDocument();
    expect(screen.getByText(/Tamper-Evident SHA-256 Ledger/i)).toBeInTheDocument();
    expect(screen.getByText(/Read-Only Statutory Archive/i)).toBeInTheDocument();
  });

  it("2. Renders 4 executive summary KPI cards with accurate baseline counts", async () => {
    render(<AuditOperationsPage />);

    const summaryCards = await screen.findByTestId("audit-summary-cards");
    expect(summaryCards).toBeInTheDocument();

    expect(within(summaryCards).getByText("Total Audit Events")).toBeInTheDocument();
    expect(within(summaryCards).getByText("Officer Sign-Offs")).toBeInTheDocument();
    expect(within(summaryCards).getByText("Automated Events")).toBeInTheDocument();
    expect(within(summaryCards).getByText("Chain Integrity")).toBeInTheDocument();

    // Baseline counts from seed (8 total: 3 officer decisions, 5 automated operations)
    expect(within(summaryCards).getByText("8")).toBeInTheDocument();
    expect(within(summaryCards).getByText("3")).toBeInTheDocument();
    expect(within(summaryCards).getByText("5")).toBeInTheDocument();
    expect(within(summaryCards).getByText("100%")).toBeInTheDocument();
  });

  it("3. Renders Audit Table with seed records, actor identities, status badges, and resource IDs", async () => {
    render(<AuditOperationsPage />);

    const table = await screen.findByTestId("audit-table");
    expect(table).toBeInTheDocument();

    // Verify key seed events
    expect(within(table).getByText("AUD-2026-001")).toBeInTheDocument();
    expect(within(table).getByText("AUD-2026-002")).toBeInTheDocument();
    expect(within(table).getByText("AUD-2026-003")).toBeInTheDocument();

    // Verify actor names
    expect(within(table).getAllByText("Suhani Amnerkar (DDMO)").length).toBeGreaterThan(0);
    expect(within(table).getByText("Autonomous Relocation Engine")).toBeInTheDocument();
    expect(within(table).getByText("District Collector Chamoli")).toBeInTheDocument();

    // Verify action labels
    expect(within(table).getByText("Rule 12 Officer Sign-Off & Enactment")).toBeInTheDocument();
    expect(within(table).getByText("Relocation Batch Assignment Commit")).toBeInTheDocument();
    expect(within(table).getByText("Returned for Technical Revision")).toBeInTheDocument();

    // Verify target entities
    expect(within(table).getByText("Chamoli Monsoon Priority Relocation Plan")).toBeInTheDocument();
    expect(within(table).getByText("Relocation Matching Batch (320 HH Allocated)")).toBeInTheDocument();
  });

  it("4. Searches audit records using keyword input across actor, entity, and reason", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    const searchInput = screen.getByTestId("audit-search-input");
    fireEvent.change(searchInput, { target: { value: "Malari" } });

    await waitFor(() => {
      const table = screen.getByTestId("audit-table");
      // Should display Malari rejection record
      expect(within(table).getByText("AUD-2026-004")).toBeInTheDocument();
      expect(within(table).getByText("Urgent Malari Outpost Terrace Encampment")).toBeInTheDocument();

      // Should NOT display unrelated records
      expect(within(table).queryByText("AUD-2026-002")).not.toBeInTheDocument();
    });
  });

  it("5. Filters audit records by category dropdown (e.g. Officer Decisions only)", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    const categorySelect = screen.getByTestId("audit-category-select");
    fireEvent.change(categorySelect, { target: { value: "officer_decision" } });

    await waitFor(() => {
      const table = screen.getByTestId("audit-table");
      // Should display officer records
      expect(within(table).getByText("AUD-2026-001")).toBeInTheDocument();
      expect(within(table).getByText("AUD-2026-003")).toBeInTheDocument();
      expect(within(table).getByText("AUD-2026-004")).toBeInTheDocument();

      // Should NOT display automated records
      expect(within(table).queryByText("AUD-2026-002")).not.toBeInTheDocument();
      expect(within(table).queryByText("AUD-2026-005")).not.toBeInTheDocument();
    });
  });

  it("6. Filters audit records by decision status dropdown (e.g. Rejected)", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    const statusSelect = screen.getByTestId("audit-status-select");
    fireEvent.change(statusSelect, { target: { value: "rejected" } });

    await waitFor(() => {
      const table = screen.getByTestId("audit-table");
      expect(within(table).getByText("AUD-2026-004")).toBeInTheDocument();
      expect(within(table).queryByText("AUD-2026-001")).not.toBeInTheDocument();
    });
  });

  it("7. Displays empty state when filters match zero records and provides reset action", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    const searchInput = screen.getByTestId("audit-search-input");
    fireEvent.change(searchInput, { target: { value: "NonExistentEventXYZ" } });

    expect(await screen.findByTestId("audit-empty-state")).toBeInTheDocument();
    expect(screen.getByText("No audit records found matching your filters.")).toBeInTheDocument();

    // Click Reset
    const resetBtn = screen.getByTestId("audit-reset-filters-btn");
    fireEvent.click(resetBtn);

    // Full table restored
    expect(await screen.findByTestId("audit-table")).toBeInTheDocument();
    expect(screen.getByText("AUD-2026-001")).toBeInTheDocument();
  });

  it("8. Deep Inspection: clicking Inspect opens AuditDetailModal with complete traceability fields", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    const inspectBtn = screen.getByTestId("inspect-audit-AUD-2026-001");
    fireEvent.click(inspectBtn);

    // Modal opens
    const modal = await screen.findByTestId("audit-detail-modal");
    expect(modal).toBeInTheDocument();

    // Header & Action
    expect(within(modal).getByText("Rule 12 Officer Sign-Off & Enactment")).toBeInTheDocument();
    expect(within(modal).getByText("Rule 12 Protocol")).toBeInTheDocument();

    // Actor Credentials
    expect(within(modal).getByText("Suhani Amnerkar (DDMO)")).toBeInTheDocument();
    expect(within(modal).getByText(/ddmo_chamoli@rakshakgis.gov.in/i)).toBeInTheDocument();

    // Rationale Quote
    expect(
      within(modal).getByText(/geotechnical stability verification of Pipalkoti terrace/i)
    ).toBeInTheDocument();

    // Source Engine & Statutory Authority
    expect(within(modal).getByText("M6-08 Officer Review & Sign-Off Workflow")).toBeInTheDocument();
    expect(
      within(modal).getByText(/NDMA Disaster Management Act 2005 § 30\(2\)/i)
    ).toBeInTheDocument();

    // Cryptographic Hash & Before/After State
    expect(within(modal).getByText(/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/i)).toBeInTheDocument();
    expect(within(modal).getByText("State Transition Payloads (Before / After)")).toBeInTheDocument();

    // Close Modal
    const closeBtn = screen.getByRole("button", { name: "Close Inspector" });
    fireEvent.click(closeBtn);
    expect(screen.queryByTestId("audit-detail-modal")).not.toBeInTheDocument();
  });

  it("9. Strict Read-Only Verification: confirms zero delete, edit, or purge controls exist in workspace or modal", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    // Assert absence of modifying controls in page
    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /purge/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /modify/i })).not.toBeInTheDocument();

    // Open detail modal
    const inspectBtn = screen.getByTestId("inspect-audit-AUD-2026-001");
    fireEvent.click(inspectBtn);

    const modal = await screen.findByTestId("audit-detail-modal");
    expect(within(modal).queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
    expect(within(modal).queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
    expect(within(modal).getByText(/Sealed Immutable Audit Record • Zero Modification Rights/i)).toBeInTheDocument();
  });

  it("10. Cryptographic Hash Integrity: clicking Verify Cryptographic Hashes confirms 100% verifiable seal", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    const verifyBtn = screen.getByTestId("verify-hashes-btn");
    fireEvent.click(verifyBtn);

    // Verification alert displays positive confirmation
    expect(
      await screen.findByText(/Cryptographic Audit Verification Passed: 100% of recorded actions/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/SHA-256 \(HMAC-Verifiable Audit Chain\)/i)).toBeInTheDocument();
  });

  it("11. Action Toolbar: Refresh Trail triggers data reload", async () => {
    render(<AuditOperationsPage />);

    await screen.findByTestId("audit-table");

    const refreshBtn = screen.getByTestId("refresh-audit-btn");
    fireEvent.click(refreshBtn);

    expect(await screen.findByTestId("audit-table")).toBeInTheDocument();
    expect(screen.getByText("AUD-2026-001")).toBeInTheDocument();
  });

  it("12. Dynamic Integration: records an officer decision audit entry into the session log", async () => {
    // Record a new officer decision via the dynamic bridge
    auditApi.recordOfficerDecisionAudit(
      {
        id: "DEC-TEST-999",
        officer_id: 101,
        officer_name: "Suhani Amnerkar (DDMO)",
        officer_role: "District Disaster Management Officer",
        decision_type: "relocation_plan",
        target_entity_type: "relocation_plan",
        target_entity_id: "DOSSIER-RELOC-001",
        action_taken: "approved",
        rationale: "Live dynamic test approval.",
        overridden_recommendation: false,
        decided_at: "2026-09-06T21:00:00Z",
      },
      {
        id: "DOSSIER-RELOC-001",
        title: "Chamoli Monsoon Priority Relocation Plan",
        type: "relocation_plan",
        source_engine: "M4-04 Relocation Matching Engine",
        region_profile_id: "himalayan_pilot",
        created_at: "2026-09-06T18:00:00Z",
        urgency_level: "critical",
        proposed_action: "Execute allocations",
        executive_summary: "Summary",
        metrics: [],
        status: "pending_review",
        statutory_mandate: "SDMA Rule 12",
      }
    );

    render(<AuditOperationsPage />);

    const table = await screen.findByTestId("audit-table");
    expect(within(table).getByText(/Live dynamic test approval/i)).toBeInTheDocument();
    expect(screen.getAllByText("9").length).toBeGreaterThan(0); // 8 + 1 = 9 total events
  });
});
