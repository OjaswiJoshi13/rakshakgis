import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { OperationalProvider, useOperational } from "@/context/OperationalContext";

const Consumer: React.FC = () => {
  const { dataMode, activeRegion, setDataMode, setActiveRegion } = useOperational();

  return (
    <div>
      <div data-testid="data-mode">{dataMode}</div>
      <div data-testid="active-region">{activeRegion}</div>
      <button onClick={() => setDataMode("live")}>Set Live</button>
      <button onClick={() => setActiveRegion("chamoli_district")}>Set Chamoli</button>
    </div>
  );
};

describe("OperationalContext", () => {
  it("provides default operational configuration", () => {
    render(
      <OperationalProvider>
        <Consumer />
      </OperationalProvider>
    );

    expect(screen.getByTestId("data-mode").textContent).toBe("demo");
    expect(screen.getByTestId("active-region").textContent).toBe("himalayan_pilot");
  });

  it("respects initialState provided to provider", () => {
    render(
      <OperationalProvider initialState={{ dataMode: "live", activeRegion: "uttarkashi" }}>
        <Consumer />
      </OperationalProvider>
    );

    expect(screen.getByTestId("data-mode").textContent).toBe("live");
    expect(screen.getByTestId("active-region").textContent).toBe("uttarkashi");
  });

  it("allows updating dataMode and activeRegion", () => {
    render(
      <OperationalProvider>
        <Consumer />
      </OperationalProvider>
    );

    act(() => {
      screen.getByText("Set Live").click();
    });
    expect(screen.getByTestId("data-mode").textContent).toBe("live");

    act(() => {
      screen.getByText("Set Chamoli").click();
    });
    expect(screen.getByTestId("active-region").textContent).toBe("chamoli_district");
  });
});
