import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import LoginPage from "@/app/login/page";
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

describe("LoginPage (/login)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders page header branding, authority context, and login form", () => {
    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginPage />
      </AuthProvider>
    );

    expect(screen.getByText("RakshakGIS")).toBeInTheDocument();
    expect(screen.getByText("Authority Access")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Authority Sign In/i })
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Username or Official Email/i)
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Sign In to Command Center/i })
    ).toBeInTheDocument();
  });

  it("renders accessible loading indicator during initial session resolution", () => {
    render(
      <AuthProvider initialState={{ isLoading: true, isAuthenticated: false }}>
        <LoginPage />
      </AuthProvider>
    );

    expect(screen.getByText(/Verifying Authority Session/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /Authority Sign In/i })
    ).not.toBeInTheDocument();
  });

  it("redirects authenticated users away from the login page to /dashboard", () => {
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
        <LoginPage />
      </AuthProvider>
    );

    expect(replaceMock).toHaveBeenCalledWith("/dashboard");
  });
});
