import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricCard } from "@/components/ui/MetricCard";

describe("MetricCard component", () => {
  it("renders label, value, and unit correctly", () => {
    render(
      <MetricCard
        label="Rainfall Intensity"
        value={124.5}
        unit="mm/24h"
        subtext="IMD Station 421"
      />
    );

    expect(screen.getByText("Rainfall Intensity")).toBeInTheDocument();
    expect(screen.getByText("124.5")).toBeInTheDocument();
    expect(screen.getByText("mm/24h")).toBeInTheDocument();
    expect(screen.getByText("IMD Station 421")).toBeInTheDocument();
  });

  it("renders trend indicator when provided", () => {
    render(
      <MetricCard
        label="Slope Velocity"
        value="1.8"
        trend="up"
        trendLabel="+15% vs yesterday"
        status="warning"
      />
    );

    expect(screen.getByText("▲ +15% vs yesterday")).toBeInTheDocument();
  });

  it("applies status color styling", () => {
    const { container } = render(
      <MetricCard
        label="Red Zone Status"
        value="Active"
        status="critical"
      />
    );

    expect(container.firstChild).toHaveClass("border-red-800/80");
  });
});
