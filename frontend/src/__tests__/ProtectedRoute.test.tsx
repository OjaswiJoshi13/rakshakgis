import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AuthProvider } from "@/context/AuthContext";
import { User } from "@/types/auth";

const testOfficer: User = {
  id: 10,
  username: "test_officer",
  email: "officer@rakshakgis.gov.in",
  full_name: "Operations Officer",
  role: "district_officer",
  is_active: true,
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-01T00:00:00Z",
};

describe("ProtectedRoute Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders accessible loading state during authentication check", () => {
    render(
      <AuthProvider initialState={{ isLoading: true, isAuthenticated: false }}>
        <ProtectedRoute>
          <div data-testid="protected-content">Secret Operational Data</div>
        </ProtectedRoute>
      </AuthProvider>
    );

    expect(screen.getByText(/Verifying Authority Session/i)).toBeInTheDocument();
    expect(
      screen.queryByTestId("protected-content")
    ).not.toBeInTheDocument();
  });

  it("blocks unauthenticated users and shows redirecting indicator", () => {
    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <ProtectedRoute>
          <div data-testid="protected-content">Secret Operational Data</div>
        </ProtectedRoute>
      </AuthProvider>
    );

    expect(
      screen.getByText(/Redirecting to authority login/i)
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("protected-content")
    ).not.toBeInTheDocument();
  });

  it("renders protected children when user is authenticated", () => {
    render(
      <AuthProvider
        initialState={{
          isLoading: false,
          isAuthenticated: true,
          user: testOfficer,
        }}
      >
        <ProtectedRoute>
          <div data-testid="protected-content">Secret Operational Data</div>
        </ProtectedRoute>
      </AuthProvider>
    );

    expect(screen.getByTestId("protected-content")).toBeInTheDocument();
    expect(screen.getByText("Secret Operational Data")).toBeInTheDocument();
  });

  it("enforces role requirements and blocks unauthorized roles", () => {
    render(
      <AuthProvider
        initialState={{
          isLoading: false,
          isAuthenticated: true,
          user: testOfficer, // role is district_officer
        }}
      >
        <ProtectedRoute requiredRoles={["admin"]}>
          <div data-testid="admin-only-content">Admin Settings Panel</div>
        </ProtectedRoute>
      </AuthProvider>
    );

    expect(
      screen.getByText(/Access Restricted: Insufficient Role Permissions/i)
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("admin-only-content")
    ).not.toBeInTheDocument();
  });

  it("allows access when user matches one of multiple required roles", () => {
    render(
      <AuthProvider
        initialState={{
          isLoading: false,
          isAuthenticated: true,
          user: testOfficer, // role is district_officer
        }}
      >
        <ProtectedRoute requiredRoles={["admin", "district_officer"]}>
          <div data-testid="officer-content">Evacuation Relocation Queue</div>
        </ProtectedRoute>
      </AuthProvider>
    );

    expect(screen.getByTestId("officer-content")).toBeInTheDocument();
    expect(screen.getByText("Evacuation Relocation Queue")).toBeInTheDocument();
  });
});
