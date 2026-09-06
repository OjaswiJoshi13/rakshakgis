/**
 * Authentication Service and Token Storage Utilities
 * Implements client communication for Chunk M2-05 backend endpoints:
 * - POST /api/v1/auth/login
 * - GET /api/v1/auth/me
 */

import { AuthErrorResponse, LoginRequest, TokenResponse, User } from "@/types/auth";

export const TOKEN_STORAGE_KEY = "rakshakgis_auth_token";
export const EXPIRY_STORAGE_KEY = "rakshakgis_auth_token_expiry";

/**
 * Returns the configured backend API base URL.
 * Falls back to local development URL if not configured in environment.
 */
export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000/api/v1"
  ).replace(/\/+$/, "");
}

/**
 * Safely retrieve the stored JWT access token from localStorage.
 */
export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

/**
 * Safely retrieve stored token expiration epoch in milliseconds.
 */
export function getStoredTokenExpiry(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const expiryStr = window.localStorage.getItem(EXPIRY_STORAGE_KEY);
    if (!expiryStr) return null;
    const expiry = parseInt(expiryStr, 10);
    return Number.isFinite(expiry) ? expiry : null;
  } catch {
    return null;
  }
}

/**
 * Store JWT access token and its calculated expiration timestamp.
 */
export function setStoredToken(token: string, expiresInSeconds: number): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    const expiryMs = Date.now() + expiresInSeconds * 1000;
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    window.localStorage.setItem(EXPIRY_STORAGE_KEY, expiryMs.toString());
  } catch (error) {
    console.error("Failed to persist authentication token:", error);
  }
}

/**
 * Clear stored credentials and session data from localStorage.
 */
export function clearStoredToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    window.localStorage.removeItem(EXPIRY_STORAGE_KEY);
  } catch (error) {
    console.error("Failed to clear authentication token:", error);
  }
}

/**
 * Check if the stored session token is missing or has expired.
 */
export function isTokenExpired(): boolean {
  const token = getStoredToken();
  if (!token) return true;

  const expiry = getStoredTokenExpiry();
  if (expiry === null) return false;

  // Add 5-second buffer for clock skew
  return Date.now() >= expiry - 5000;
}

/**
 * Parse structured backend error response conforming to M2-04 ErrorResponse.
 */
export function parseAuthError(statusCode: number, data: unknown): string {
  if (data && typeof data === "object") {
    const errorResponse = data as Partial<AuthErrorResponse>;
    if (errorResponse.error?.message) {
      return errorResponse.error.message;
    }
  }

  if (statusCode === 401) {
    return "Invalid username or password. Please verify your credentials.";
  }
  if (statusCode === 403) {
    return "Access restricted: insufficient permissions for this operation.";
  }
  if (statusCode === 422) {
    return "Invalid credentials format. Please ensure all fields are filled.";
  }
  if (statusCode >= 500) {
    return "Disaster decision support server unavailable. Please try again later.";
  }

  return "An unexpected authentication error occurred. Please try again.";
}

/**
 * Authenticate against M2-05 POST /api/v1/auth/login.
 */
export async function loginApi(credentials: LoginRequest): Promise<TokenResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/auth/login`;

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        username: credentials.username.trim(),
        password: credentials.password,
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network error";
    throw new Error(
      `Unable to connect to authentication server (${message}). Please check network connectivity.`
    );
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const errorMessage = parseAuthError(response.status, data);
    throw new Error(errorMessage);
  }

  const tokenData = data as TokenResponse;
  if (!tokenData.access_token) {
    throw new Error("Invalid token response received from server.");
  }

  return tokenData;
}

/**
 * Fetch current authenticated user profile against M2-05 GET /api/v1/auth/me.
 */
export async function getMeApi(token: string): Promise<User> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/auth/me`;

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network error";
    throw new Error(
      `Unable to connect to authentication server (${message}). Please check network connectivity.`
    );
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const errorMessage = parseAuthError(response.status, data);
    throw new Error(errorMessage);
  }

  return data as User;
}
