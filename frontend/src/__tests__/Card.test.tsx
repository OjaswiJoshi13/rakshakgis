import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/Card";

describe("Card component suite", () => {
  it("renders card structure with header, title, description, and content", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Hazard Observation</CardTitle>
          <CardDescription>Telemetry from GSI Slope Station</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Displacement: 4.2mm</p>
        </CardContent>
        <CardFooter>
          <span>Verified 2m ago</span>
        </CardFooter>
      </Card>
    );

    expect(screen.getByText("Hazard Observation")).toBeInTheDocument();
    expect(screen.getByText("Telemetry from GSI Slope Station")).toBeInTheDocument();
    expect(screen.getByText("Displacement: 4.2mm")).toBeInTheDocument();
    expect(screen.getByText("Verified 2m ago")).toBeInTheDocument();
  });

  it("applies compact density styles", () => {
    const { container } = render(
      <Card density="compact">
        <CardContent>Compact Card</CardContent>
      </Card>
    );

    expect(container.firstChild).toHaveClass("p-3");
  });

  it("applies elevated variant styles", () => {
    const { container } = render(
      <Card variant="elevated">
        <CardContent>Elevated Card</CardContent>
      </Card>
    );

    expect(container.firstChild).toHaveClass("shadow-md");
  });
});
