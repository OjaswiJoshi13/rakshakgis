import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CommandHeader } from "@/components/layout/CommandHeader";
import { Sidebar } from "@/components/layout/Sidebar";
import { StatusBar } from "@/components/layout/StatusBar";
import { AppLayout } from "@/components/layout/AppLayout";

describe("Layout components suite", () => {
  it("renders CommandHeader with platform branding and mode", () => {
    render(<CommandHeader />);
    expect(screen.getByText("RakshakGIS")).toBeInTheDocument();
    expect(screen.getByText("SIH 26191")).toBeInTheDocument();
    expect(screen.getByText("Himalayan Pilot (Chamoli)")).toBeInTheDocument();
    expect(screen.getByText(/DEMO MODE/i)).toBeInTheDocument();
  });

  it("renders Sidebar with module navigation items and chunk badges", () => {
    render(<Sidebar isOpen={true} />);
    expect(screen.getByText("Platform Core")).toBeInTheDocument();
    expect(screen.getByText("System Foundation")).toBeInTheDocument();
    expect(screen.getByText("Executive Dashboard")).toBeInTheDocument();
    expect(screen.getByText("MapLibre GIS Canvas")).toBeInTheDocument();
    expect(screen.getByText("M5-01")).toBeInTheDocument();
    expect(screen.getByText("M5-04")).toBeInTheDocument();

    // Officer Operations Section
    expect(screen.getByText("Officer Operations")).toBeInTheDocument();
    expect(screen.getByText("Operations Hub")).toBeInTheDocument();
    expect(screen.getByText("Relocation Planner")).toBeInTheDocument();
    expect(screen.getByText("Relocation Sites")).toBeInTheDocument();
    expect(screen.getByText("Scenario Simulator")).toBeInTheDocument();
    expect(screen.getByText("Threshold Warnings")).toBeInTheDocument();
    expect(screen.getByText("Reports & Export")).toBeInTheDocument();
    expect(screen.getByText("Officer Sign-Off")).toBeInTheDocument();
    expect(screen.getByText("Audit & Traceability")).toBeInTheDocument();
    expect(screen.getByText("M6-01")).toBeInTheDocument();
    expect(screen.getByText("M6-02")).toBeInTheDocument();
    expect(screen.getByText("M6-01 READY")).toBeInTheDocument();
  });

  it("renders StatusBar with CRS, region, and version", () => {
    render(<StatusBar />);
    expect(screen.getByText("EPSG:4326 (WGS 84)")).toBeInTheDocument();
    expect(screen.getByText("himalayan_pilot (Chamoli)")).toBeInTheDocument();
    expect(screen.getByText("SYSTEM: NORMAL")).toBeInTheDocument();
  });

  it("renders AppLayout wrapping child content", () => {
    render(
      <AppLayout>
        <div data-testid="test-content">Operational Canvas Content</div>
      </AppLayout>
    );

    expect(screen.getByTestId("test-content")).toBeInTheDocument();
    expect(screen.getByText("Skip to main content")).toBeInTheDocument();
  });
});
