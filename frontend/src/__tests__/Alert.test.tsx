import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Alert } from "@/components/ui/Alert";

describe("Alert component", () => {
  it("renders with role alert and title", () => {
    render(
      <Alert severity="warning" title="Threshold Trigger">
        Rainfall exceeded 64.5mm warning threshold.
      </Alert>
    );

    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(screen.getByText("Threshold Trigger")).toBeInTheDocument();
    expect(
      screen.getByText("Rainfall exceeded 64.5mm warning threshold.")
    ).toBeInTheDocument();
  });

  it("handles dismissal callback", () => {
    const handleClose = vi.fn();
    render(
      <Alert severity="info" onClose={handleClose}>
        Dismissible note.
      </Alert>
    );

    const dismissBtn = screen.getByRole("button", { name: /dismiss alert/i });
    fireEvent.click(dismissBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("applies danger severity classes", () => {
    render(
      <Alert severity="danger" title="Red Zone Alert">
        Evacuation protocol initiated.
      </Alert>
    );

    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("bg-red-950");
  });
});
