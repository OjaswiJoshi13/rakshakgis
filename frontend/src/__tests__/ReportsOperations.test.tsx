import React from "react";
import { render, screen, fireEvent, waitFor, act, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ReportsOperationsPage from "@/app/operations/reports/page";
import * as reportsApi from "@/lib/api/reports";
import * as sitesApi from "@/lib/api/sites";
import * as relocationApi from "@/lib/api/relocation";

// Mock Next.js navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  usePathname: () => "/operations/reports",
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

describe("Report Generation & Export UI Suite (Chunk M6-07)", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Setup window.print mock
    window.print = vi.fn();

    // Setup URL create/revoke mocks
    if (typeof window.URL.createObjectURL === "undefined") {
      window.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    } else {
      vi.spyOn(window.URL, "createObjectURL").mockReturnValue("blob:mock-url");
    }
    if (typeof window.URL.revokeObjectURL === "undefined") {
      window.URL.revokeObjectURL = vi.fn();
    } else {
      vi.spyOn(window.URL, "revokeObjectURL").mockImplementation(() => {});
    }

    vi.spyOn(sitesApi, "listCandidateSites").mockResolvedValue({
      success: true,
      count: sitesApi.HIMALAYAN_PILOT_SAMPLE_SITES.length,
      data: sitesApi.HIMALAYAN_PILOT_SAMPLE_SITES,
    });

    vi.spyOn(relocationApi, "evaluateRelocationMatching").mockResolvedValue({
      success: true,
      data: relocationApi.HIMALAYAN_PILOT_SAMPLE_MATCH_RESULT,
    });
  });

  it("1. Renders Reports Section Shell with M6-07 badge, title, and initial empty state", async () => {
    render(<ReportsOperationsPage />);

    expect(
      screen.getAllByText("Report Generation & Export").length
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("M6-07")).toBeInTheDocument();
    expect(screen.getByText("Report Generation & Export UI")).toBeInTheDocument();
    expect(
      screen.getByText(/Authoritative relocation dossiers, multi-hazard risk summaries/i)
    ).toBeInTheDocument();

    // Empty state should be visible before compilation
    expect(
      screen.getByText("Select a Report Template to Compile Dossier")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Compile Relocation Allocation Plan/i })
    ).toBeInTheDocument();
  });

  it("2. Renders all 4 report templates in the template selector", async () => {
    render(<ReportsOperationsPage />);

    expect(
      screen.getByTestId("template-btn-relocation_allocation")
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("template-btn-site_infrastructure")
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("template-btn-suitability_capacity")
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("template-btn-comprehensive_dossier")
    ).toBeInTheDocument();
  });

  it("3. Template selection toggles applicable operational parameters", async () => {
    render(<ReportsOperationsPage />);

    // Default template (relocation_allocation) has status filter and includeAudits, but NOT siteSelector
    expect(screen.getByText("Village Assignment Status")).toBeInTheDocument();
    expect(
      screen.getByText("Include Candidate Rejection Audits")
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/Target Candidate Site/i)).not.toBeInTheDocument();

    // Select "Candidate Relocation Sites & Infrastructure Inventory"
    const sitesTmplBtn = screen.getByTestId("template-btn-site_infrastructure");
    fireEvent.click(sitesTmplBtn);

    // Should now show site selector, but not status filter
    expect(screen.getByLabelText(/Target Candidate Site/i)).toBeInTheDocument();
    expect(screen.queryByText("Village Assignment Status")).not.toBeInTheDocument();

    // Select "Site Suitability & Carrying Capacity Assessment"
    const suitTmplBtn = screen.getByTestId("template-btn-suitability_capacity");
    fireEvent.click(suitTmplBtn);

    expect(screen.getByLabelText(/Target Candidate Site/i)).toBeInTheDocument();
    expect(
      screen.getByText("Include Infrastructure Deficit Analysis")
    ).toBeInTheDocument();
  });

  it("4. Compiling Relocation Allocation Plan renders summary metrics and allocation ledger", async () => {
    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    // Summary Metric Cards
    await waitFor(() => {
      expect(screen.getByText("Total Habitations")).toBeInTheDocument();
      expect(screen.getByText("Assigned Habitations")).toBeInTheDocument();
      expect(screen.getByText("Unassigned Habitations")).toBeInTheDocument();
      expect(screen.getByText("Allocated Households")).toBeInTheDocument();
    });

    // Official Dossier Document Header
    expect(
      screen.getByText("OFFICIAL OPERATIONAL DOSSIER • DECISION SUPPORT")
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Relocation Matching & Allocation Plan").length
    ).toBeGreaterThanOrEqual(1);

    // Ledger table should render villages
    expect(screen.getByText("Raini")).toBeInTheDocument();
    expect(screen.getByText("Malari Outpost")).toBeInTheDocument();
    expect(
      screen.getAllByText("Joshimath Safe Terrace").length
    ).toBeGreaterThanOrEqual(1);
  });

  it("5. Filters assignments by status correctly", async () => {
    render(<ReportsOperationsPage />);

    // Select "unassigned" status filter
    const unassignedFilterBtn = screen.getByRole("button", {
      name: /unassigned/i,
    });
    fireEvent.click(unassignedFilterBtn);

    // Compile dossier
    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("Malari Outpost")).toBeInTheDocument();
    });

    // Assigned village should NOT be in the filtered table
    expect(screen.queryByText("Raini")).not.toBeInTheDocument();
  });

  it("6. Toggles candidate evaluation audits per village", async () => {
    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("Raini")).toBeInTheDocument();
    });

    // Audit toggle button with data-testid audit-toggle-btn-1
    const auditBtn = screen.getByTestId("audit-toggle-btn-1");
    expect(auditBtn).toBeInTheDocument();

    // Click audit toggle for village Raini
    await act(async () => {
      fireEvent.click(auditBtn);
    });

    // Audit card should expand showing evaluated candidate sites
    await waitFor(() => {
      expect(
        screen.getByText(/Candidate Sites Evaluation Audit for Raini:/i)
      ).toBeInTheDocument();
    });
  });

  it("7. Compiling Candidate Sites Inventory renders sites table and infrastructure assets", async () => {
    render(<ReportsOperationsPage />);

    const sitesTmplBtn = screen.getByTestId("template-btn-site_infrastructure");
    fireEvent.click(sitesTmplBtn);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("Candidate Sites")).toBeInTheDocument();
      expect(
        screen.getByText(/Candidate Relocation Sites Inventory/i)
      ).toBeInTheDocument();
    });

    // Table rows
    expect(screen.getAllByText("Joshimath Safe Terrace").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Pipalkoti Plateau")).toBeInTheDocument();

    // Infrastructure asset profile
    expect(
      screen.getByText(/Infrastructure Assets Profile: Joshimath Safe Terrace/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Joshimath Gravity Water Supply")).toBeInTheDocument();
  });

  it("8. Compiling Suitability & Capacity Assessment renders 9 criteria and 5 dimensions", async () => {
    render(<ReportsOperationsPage />);

    const suitTmplBtn = screen.getByTestId("template-btn-suitability_capacity");
    fireEvent.click(suitTmplBtn);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("Suitability Decision")).toBeInTheDocument();
      expect(screen.getByText("Effective Capacity")).toBeInTheDocument();
      expect(screen.getByText("Limiting Factors")).toBeInTheDocument();
      expect(screen.getByText("Hard Safety Gates")).toBeInTheDocument();
    });

    // 9 Authoritative Criteria
    expect(
      screen.getByText("9 Authoritative Suitability Criteria")
    ).toBeInTheDocument();
    expect(screen.getByText("Hazard Safety")).toBeInTheDocument();
    expect(screen.getByText("Road & Transport Access")).toBeInTheDocument();

    // 5 Critical Infrastructure Dimensions
    expect(
      screen.getByText("5 Critical Infrastructure Dimensions")
    ).toBeInTheDocument();
  });

  it("9. Action Toolbar: Export JSON downloads structured payload", async () => {
    const downloadSpy = vi.spyOn(reportsApi, "downloadFile");

    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Export JSON/i })).toBeInTheDocument();
    });

    const exportJsonBtn = screen.getByRole("button", { name: /Export JSON/i });
    fireEvent.click(exportJsonBtn);

    expect(downloadSpy).toHaveBeenCalledWith(
      expect.stringMatching(/^dossier-.*\.json$/),
      expect.stringContaining('"id":'),
      "application/json"
    );

    // Export success notice banner
    expect(
      screen.getByText(/Dossier exported successfully as JSON/i)
    ).toBeInTheDocument();
  });

  it("10. Action Toolbar: Export CSV downloads tabular data", async () => {
    const downloadSpy = vi.spyOn(reportsApi, "downloadFile");

    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Export CSV/i })).toBeInTheDocument();
    });

    const exportCsvBtn = screen.getByRole("button", { name: /Export CSV/i });
    fireEvent.click(exportCsvBtn);

    expect(downloadSpy).toHaveBeenCalledWith(
      expect.stringMatching(/^dossier-.*-assignments\.csv$/),
      expect.stringContaining("Village ID,Village Name"),
      "text/csv;charset=utf-8;"
    );

    expect(
      screen.getByText(/Village assignments exported as CSV/i)
    ).toBeInTheDocument();
  });

  it("11. Action Toolbar: Print Dossier invokes window.print", async () => {
    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Print Dossier/i })).toBeInTheDocument();
    });

    const printBtn = screen.getByRole("button", { name: /Print Dossier/i });
    fireEvent.click(printBtn);

    expect(window.print).toHaveBeenCalledTimes(1);
  });

  it("12. Reset action returns to empty state", async () => {
    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /New Report/i })).toBeInTheDocument();
    });

    const newReportBtn = screen.getByRole("button", { name: /New Report/i });
    fireEvent.click(newReportBtn);

    expect(
      screen.getByText("Select a Report Template to Compile Dossier")
    ).toBeInTheDocument();
  });

  it("13. Displays compilation error banner with retry option if service fails", async () => {
    vi.spyOn(reportsApi, "compileReportDossier").mockRejectedValueOnce(
      new Error("Database connection timed out during dossier aggregation.")
    );

    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("Compilation Error")).toBeInTheDocument();
      expect(
        screen.getByText("Database connection timed out during dossier aggregation.")
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
    });
  });

  it("14. Prominently displays Rule 12 and Rule 8 statutory governance callouts", async () => {
    render(<ReportsOperationsPage />);

    const compileBtn = screen.getByRole("button", {
      name: /Compile Operational Dossier/i,
    });
    await act(async () => {
      fireEvent.click(compileBtn);
    });

    await waitFor(() => {
      expect(
        screen.getByText("Rule 12 Statutory Decision-Support Mandate")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Does NOT constitute a statutory disaster declaration/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText("Rule 8 Analytical Provenance & Audit Trail")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Zero random numbers or generative LLM outputs/i)
      ).toBeInTheDocument();
    });
  });
});
