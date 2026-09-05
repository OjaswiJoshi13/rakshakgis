import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge, RiskBadge, RelocationBadge } from "@/components/ui/Badge";
import { getRiskBandFromScore, getRelocationPriorityBand } from "@/design-system/tokens";

describe("Badge and RiskBadge components", () => {
  it("renders generic badge with variants", () => {
    const { rerender } = render(<Badge variant="default">Status</Badge>);
    expect(screen.getByText("Status")).toBeInTheDocument();

    rerender(<Badge variant="success">Online</Badge>);
    expect(screen.getByText("Online")).toBeInTheDocument();
  });

  it("renders all 5 authoritative Risk Bands correctly", () => {
    const bands = ["safe", "moderate", "high", "very_high", "critical"] as const;

    bands.forEach((band) => {
      const { unmount } = render(<RiskBadge band={band} />);
      expect(screen.getByTitle(new RegExp(`Risk Band:`, "i"))).toBeInTheDocument();
      unmount();
    });
  });

  it("maps numerical risk scores to correct specification bands", () => {
    expect(getRiskBandFromScore(10)).toBe("safe");
    expect(getRiskBandFromScore(25)).toBe("moderate");
    expect(getRiskBandFromScore(55)).toBe("high");
    expect(getRiskBandFromScore(75)).toBe("very_high");
    expect(getRiskBandFromScore(90)).toBe("critical");
  });

  it("renders RiskBadge with numeric score", () => {
    render(<RiskBadge score={88.4} />);
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("[88.4]")).toBeInTheDocument();
  });

  it("maps relocation priority scores to correct specification bands", () => {
    expect(getRelocationPriorityBand(85)).toBe("immediate");
    expect(getRelocationPriorityBand(65)).toBe("short_term");
    expect(getRelocationPriorityBand(45)).toBe("medium_term");
    expect(getRelocationPriorityBand(20)).toBe("monitor");
  });

  it("renders RelocationBadge with numeric score", () => {
    render(<RelocationBadge score={82.0} />);
    expect(screen.getByText("Immediate Action")).toBeInTheDocument();
    expect(screen.getByText("(82.0)")).toBeInTheDocument();
  });
});
