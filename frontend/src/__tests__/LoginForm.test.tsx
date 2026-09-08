import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LoginForm } from "@/components/auth/LoginForm";
import { AuthProvider } from "@/context/AuthContext";
import * as authService from "@/lib/auth";

describe("LoginForm Component", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders username/email, password fields and accessible labels", () => {
    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginForm />
      </AuthProvider>
    );

    expect(
      screen.getByLabelText(/Username or Official Email/i)
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Sign In to Command Center/i })
    ).toBeInTheDocument();
  });

  it("blocks submission and shows client validation error when fields are empty", async () => {
    const loginSpy = vi.spyOn(authService, "loginApi");

    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginForm />
      </AuthProvider>
    );

    fireEvent.click(
      screen.getByRole("button", { name: /Sign In to Command Center/i })
    );

    expect(
      screen.getByText(/Username or registered email address is required/i)
    ).toBeInTheDocument();
    expect(loginSpy).not.toHaveBeenCalled();
  });

  it("blocks submission when only username is filled", async () => {
    const loginSpy = vi.spyOn(authService, "loginApi");

    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginForm />
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText(/Username or Official Email/i), {
      target: { value: "officer@rakshakgis.gov.in" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Sign In to Command Center/i })
    );

    expect(
      screen.getByText(/Account password is required/i)
    ).toBeInTheDocument();
    expect(loginSpy).not.toHaveBeenCalled();
  });

  it("submits valid credentials and triggers onSuccess callback", async () => {
    vi.spyOn(authService, "loginApi").mockResolvedValueOnce({
      access_token: "mock-token",
      token_type: "bearer",
      expires_in: 3600,
    });
    vi.spyOn(authService, "getMeApi").mockResolvedValueOnce({
      id: 1,
      username: "officer",
      email: "officer@rakshakgis.gov.in",
      full_name: "District Officer",
      role: "district_officer",
      department: "Chamoli DDMA",
      is_active: true,
      created_at: "2026-09-01T00:00:00Z",
      updated_at: "2026-09-01T00:00:00Z",
    });

    const onSuccessMock = vi.fn();

    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginForm onSuccess={onSuccessMock} />
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText(/Username or Official Email/i), {
      target: { value: "officer@rakshakgis.gov.in" },
    });
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: "CorrectPassword123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Sign In to Command Center/i })
    );

    await waitFor(() => {
      expect(onSuccessMock).toHaveBeenCalledTimes(1);
    });
  });

  it("displays server error alert when authentication fails", async () => {
    vi.spyOn(authService, "loginApi").mockRejectedValueOnce(
      new Error("Invalid username or password.")
    );

    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginForm />
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText(/Username or Official Email/i), {
      target: { value: "bad_officer" },
    });
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: "wrong_password" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Sign In to Command Center/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText("Invalid username or password.")
      ).toBeInTheDocument();
    });

    // Dismiss alert
    fireEvent.click(screen.getByLabelText(/Dismiss alert/i));
    expect(
      screen.queryByText("Invalid username or password.")
    ).not.toBeInTheDocument();
  });

  it("authenticates via Demo District Officer button and triggers onSuccess", async () => {
    const onSuccessMock = vi.fn();

    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginForm onSuccess={onSuccessMock} />
      </AuthProvider>
    );

    const demoButton = screen.getByRole("button", {
      name: /Sign In as Demo District Officer/i,
    });
    expect(demoButton).toBeInTheDocument();

    fireEvent.click(demoButton);

    await waitFor(() => {
      expect(onSuccessMock).toHaveBeenCalledTimes(1);
    });

    expect(window.localStorage.getItem(authService.TOKEN_STORAGE_KEY)).toBe(
      authService.DEMO_AUTH_TOKEN
    );
  });

  it("has password hidden by default, toggles visibility on button click, preserves password value, and updates accessible label", () => {
    render(
      <AuthProvider initialState={{ isLoading: false, isAuthenticated: false }}>
        <LoginForm />
      </AuthProvider>
    );

    const passwordInput = screen.getByLabelText(/^Password$/i) as HTMLInputElement;
    expect(passwordInput.type).toBe("password");

    const toggleButton = screen.getByRole("button", { name: /Show password/i });
    expect(toggleButton).toBeInTheDocument();

    // Type a password
    fireEvent.change(passwordInput, { target: { value: "SecretPass987!" } });
    expect(passwordInput.value).toBe("SecretPass987!");
    expect(passwordInput.type).toBe("password");

    // Click show password
    fireEvent.click(toggleButton);
    expect(passwordInput.type).toBe("text");
    expect(passwordInput.value).toBe("SecretPass987!");
    expect(screen.getByRole("button", { name: /Hide password/i })).toBeInTheDocument();

    // Click hide password
    fireEvent.click(screen.getByRole("button", { name: /Hide password/i }));
    expect(passwordInput.type).toBe("password");
    expect(passwordInput.value).toBe("SecretPass987!");
    expect(screen.getByRole("button", { name: /Show password/i })).toBeInTheDocument();
  });
});
