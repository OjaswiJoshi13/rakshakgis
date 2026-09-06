import React from "react";
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import * as authService from "@/lib/auth";
import { User } from "@/types/auth";

const mockOfficerUser: User = {
  id: 42,
  username: "district_collector_chamoli",
  email: "collector@chamoli.gov.in",
  full_name: "District Collector Chamoli",
  role: "district_officer",
  department: "District Administration",
  is_active: true,
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-01T00:00:00Z",
};

// Test consumer component exposing auth hook states and operations
const TestConsumer: React.FC = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    hasRole,
    clearError,
  } = useAuth();

  return (
    <div>
      <div data-testid="loading-state">{isLoading ? "loading" : "idle"}</div>
      <div data-testid="auth-state">
        {isAuthenticated ? "authenticated" : "unauthenticated"}
      </div>
      <div data-testid="user-name">{user?.full_name || "none"}</div>
      <div data-testid="user-role">{user?.role || "none"}</div>
      <div data-testid="error-message">{error || "none"}</div>
      <div data-testid="has-officer-role">
        {hasRole("district_officer") ? "yes" : "no"}
      </div>
      <div data-testid="has-admin-role">{hasRole("admin") ? "yes" : "no"}</div>

      <button
        onClick={() =>
          login({
            username: "collector@chamoli.gov.in",
            password: "SecurePassword123!",
          })
        }
      >
        Trigger Login
      </button>
      <button onClick={logout}>Trigger Logout</button>
      <button onClick={clearError}>Trigger Clear Error</button>
    </div>
  );
};

describe("AuthContext and Session Lifecycle", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("initializes as unauthenticated when no stored token exists", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading-state").textContent).toBe("idle");
    });

    expect(screen.getByTestId("auth-state").textContent).toBe("unauthenticated");
    expect(screen.getByTestId("user-name").textContent).toBe("none");
  });

  it("restores authenticated session when valid token is present in storage", async () => {
    authService.setStoredToken("stored-valid-token", 3600);
    vi.spyOn(authService, "getMeApi").mockResolvedValueOnce(mockOfficerUser);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading-state").textContent).toBe("idle");
    });

    expect(screen.getByTestId("auth-state").textContent).toBe("authenticated");
    expect(screen.getByTestId("user-name").textContent).toBe(
      "District Collector Chamoli"
    );
    expect(screen.getByTestId("user-role").textContent).toBe("district_officer");
    expect(screen.getByTestId("has-officer-role").textContent).toBe("yes");
    expect(screen.getByTestId("has-admin-role").textContent).toBe("no");
  });

  it("clears storage and remains unauthenticated if stored token validation fails", async () => {
    authService.setStoredToken("invalid-server-token", 3600);
    vi.spyOn(authService, "getMeApi").mockRejectedValueOnce(
      new Error("Authentication token has expired.")
    );

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading-state").textContent).toBe("idle");
    });

    expect(screen.getByTestId("auth-state").textContent).toBe("unauthenticated");
    expect(authService.getStoredToken()).toBeNull();
  });

  it("executes successful login, persists token, and populates user session", async () => {
    vi.spyOn(authService, "loginApi").mockResolvedValueOnce({
      access_token: "new-signed-token",
      token_type: "bearer",
      expires_in: 3600,
    });
    vi.spyOn(authService, "getMeApi").mockResolvedValueOnce(mockOfficerUser);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading-state").textContent).toBe("idle");
    });

    await act(async () => {
      screen.getByText("Trigger Login").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-state").textContent).toBe("authenticated");
    });

    expect(screen.getByTestId("user-name").textContent).toBe(
      "District Collector Chamoli"
    );
    expect(authService.getStoredToken()).toBe("new-signed-token");
  });

  it("handles login failure, sets error state, and remains unauthenticated", async () => {
    vi.spyOn(authService, "loginApi").mockRejectedValueOnce(
      new Error("Invalid username or password.")
    );

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading-state").textContent).toBe("idle");
    });

    await act(async () => {
      screen.getByText("Trigger Login").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("error-message").textContent).toBe(
        "Invalid username or password."
      );
    });

    expect(screen.getByTestId("auth-state").textContent).toBe("unauthenticated");
    expect(authService.getStoredToken()).toBeNull();

    // Clear error
    act(() => {
      screen.getByText("Trigger Clear Error").click();
    });
    expect(screen.getByTestId("error-message").textContent).toBe("none");
  });

  it("clears user and session on logout", async () => {
    authService.setStoredToken("active-token", 3600);
    vi.spyOn(authService, "getMeApi").mockResolvedValueOnce(mockOfficerUser);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-state").textContent).toBe("authenticated");
    });

    act(() => {
      screen.getByText("Trigger Logout").click();
    });

    expect(screen.getByTestId("auth-state").textContent).toBe("unauthenticated");
    expect(screen.getByTestId("user-name").textContent).toBe("none");
    expect(authService.getStoredToken()).toBeNull();
  });
});
