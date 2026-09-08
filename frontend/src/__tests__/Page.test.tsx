import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "@/app/page";
import { AuthProvider } from "@/context/AuthContext";
import { User } from "@/types/auth";
import * as navigation from "next/navigation";

const mockOfficerUser: User = {
  id: 1,
  username: "test_auth_officer",
  email: "officer@rakshakgis.gov.in",
  full_name: "Disaster Management Officer",
  role: "district_officer",
  is_active: true,
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-01T00:00:00Z",
};

describe("HomePage (/) Route Entry Flow", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("1. Unauthenticated root access renders the Login page UI", () => {
    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <HomePage />
      </AuthProvider>
    );

    expect(screen.getByText("RakshakGIS")).toBeInTheDocument();
    expect(screen.getByText("Authority Access")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Authority Sign In/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Sign In to Command Center/i })
    ).toBeInTheDocument();

    // Verify obsolete Command Center Shell is not rendered
    expect(
      screen.queryByText(/RakshakGIS Command Center Shell/i)
    ).not.toBeInTheDocument();
  });

  it("2. Authenticated root access cleanly redirects to /dashboard", () => {
    const replaceMock = vi.fn();
    vi.spyOn(navigation, "useRouter").mockReturnValue({
      push: vi.fn(),
      replace: replaceMock,
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    });

    render(
      <AuthProvider
        initialState={{
          isLoading: false,
          isAuthenticated: true,
          user: mockOfficerUser,
        }}
      >
        <HomePage />
      </AuthProvider>
    );

    expect(replaceMock).toHaveBeenCalledWith("/dashboard");
    expect(
      screen.queryByText(/RakshakGIS Command Center Shell/i)
    ).not.toBeInTheDocument();
  });

  it("3. Displays accessible session verification indicator while checking auth", () => {
    render(
      <AuthProvider initialState={{ isLoading: true, isAuthenticated: false }}>
        <HomePage />
      </AuthProvider>
    );

    expect(screen.getByText(/Verifying Authority Session/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /Authority Sign In/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/RakshakGIS Command Center Shell/i)
    ).not.toBeInTheDocument();
  });
});
