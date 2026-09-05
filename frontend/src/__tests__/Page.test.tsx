import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "@/app/page";

describe("HomePage (Chunk M5-01 Foundation Landing)", () => {
  it("renders main heading and hero section", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /RakshakGIS Command Center Shell/i })
    ).toBeInTheDocument();
    expect(screen.getByText("Chunk M5-01")).toBeInTheDocument();
  });

  it("renders architecture parameter metric cards", () => {
    render(<HomePage />);
    expect(screen.getByText("Region Profile")).toBeInTheDocument();
    expect(screen.getByText("Multi-Hazard Model")).toBeInTheDocument();
    expect(screen.getByText("Relocation Priority")).toBeInTheDocument();
    expect(screen.getByText("Coordinate System")).toBeInTheDocument();
  });

  it("renders authoritative risk band classifications", () => {
    render(<HomePage />);
    expect(screen.getByText("Composite Risk Score Classifications")).toBeInTheDocument();
    expect(screen.getByText("0–25")).toBeInTheDocument();
    expect(screen.getByText("25–50")).toBeInTheDocument();
    expect(screen.getByText("50–70")).toBeInTheDocument();
    expect(screen.getByText("70–85")).toBeInTheDocument();
    expect(screen.getByText("85–100")).toBeInTheDocument();
  });

  it("renders operational alert banners", () => {
    render(<HomePage />);
    expect(
      screen.getByText(/CRITICAL: Dynamic Red Zone Threshold Exceeded/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/WEATHER WATCH: IMD Rainfall Warning/i)
    ).toBeInTheDocument();
  });
});
