import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import {
  clearStoredToken,
  getApiBaseUrl,
  getStoredToken,
  getStoredTokenExpiry,
  isTokenExpired,
  loginApi,
  getMeApi,
  parseAuthError,
  setStoredToken,
  TOKEN_STORAGE_KEY,
  EXPIRY_STORAGE_KEY,
} from "@/lib/auth";

describe("AuthService and Token Storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("stores and retrieves token and expiration timestamp", () => {
    expect(getStoredToken()).toBeNull();
    expect(getStoredTokenExpiry()).toBeNull();

    const testToken = "header.payload.signature";
    const expiresIn = 3600; // 1 hour

    const before = Date.now();
    setStoredToken(testToken, expiresIn);
    const after = Date.now();

    expect(getStoredToken()).toBe(testToken);
    const expiry = getStoredTokenExpiry();
    expect(expiry).not.toBeNull();
    expect(expiry).toBeGreaterThanOrEqual(before + expiresIn * 1000);
    expect(expiry).toBeLessThanOrEqual(after + expiresIn * 1000);
  });

  it("clears stored token and expiry correctly", () => {
    setStoredToken("sample-token", 1800);
    expect(getStoredToken()).toBe("sample-token");

    clearStoredToken();
    expect(getStoredToken()).toBeNull();
    expect(getStoredTokenExpiry()).toBeNull();
  });

  it("detects expired vs valid tokens accurately", () => {
    // Missing token is considered expired
    expect(isTokenExpired()).toBe(true);

    // Active token in future is not expired
    setStoredToken("active-token", 3600);
    expect(isTokenExpired()).toBe(false);

    // Expired token (past timestamp)
    window.localStorage.setItem(TOKEN_STORAGE_KEY, "expired-token");
    window.localStorage.setItem(EXPIRY_STORAGE_KEY, (Date.now() - 10000).toString());
    expect(isTokenExpired()).toBe(true);
  });

  it("returns configured or default API base URL", () => {
    const url = getApiBaseUrl();
    expect(url).toBeDefined();
    expect(url.endsWith("/")).toBe(false);
  });

  describe("parseAuthError", () => {
    it("extracts structured error message from M2-04 ErrorResponse", () => {
      const payload = {
        success: false,
        error: {
          code: "UNAUTHORIZED",
          message: "Invalid username or password.",
          status_code: 401,
          request_id: "req-12345",
        },
      };
      const msg = parseAuthError(401, payload);
      expect(msg).toBe("Invalid username or password.");
    });

    it("falls back to standard messages for HTTP status codes when no detail is provided", () => {
      expect(parseAuthError(401, null)).toContain("Invalid username or password");
      expect(parseAuthError(403, null)).toContain("insufficient permissions");
      expect(parseAuthError(422, null)).toContain("Invalid credentials format");
      expect(parseAuthError(500, null)).toContain("server unavailable");
    });
  });

  describe("loginApi", () => {
    it("successfully authenticates and returns TokenResponse", async () => {
      const mockResponse = {
        access_token: "jwt.test.token",
        token_type: "bearer",
        expires_in: 1800,
      };

      vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      } as Response);

      const result = await loginApi({
        username: "officer@rakshakgis.gov.in",
        password: "SecretPassword123!",
      });

      expect(result.access_token).toBe("jwt.test.token");
      expect(result.token_type).toBe("bearer");
      expect(result.expires_in).toBe(1800);
    });

    it("throws error with backend message when credentials are invalid (401)", async () => {
      const errorPayload = {
        success: false,
        error: {
          code: "UNAUTHORIZED",
          message: "Invalid username or password.",
          status_code: 401,
        },
      };

      vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => errorPayload,
      } as Response);

      await expect(
        loginApi({ username: "bad_user", password: "wrong_password" })
      ).rejects.toThrow("Invalid username or password.");
    });

    it("handles network failure gracefully", async () => {
      vi.spyOn(global, "fetch").mockRejectedValueOnce(new Error("Failed to fetch"));

      await expect(
        loginApi({ username: "user", password: "password" })
      ).rejects.toThrow(/Unable to connect to authentication server/i);
    });
  });

  describe("getMeApi", () => {
    it("successfully retrieves user profile with Bearer header", async () => {
      const mockUser = {
        id: 1,
        username: "test_auth_admin",
        email: "admin@rakshakgis.gov.in",
        full_name: "Admin Officer",
        role: "admin",
        department: "State Disaster Management Authority",
        is_active: true,
        created_at: "2026-09-01T00:00:00Z",
        updated_at: "2026-09-01T00:00:00Z",
      };

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUser,
      } as Response);

      const user = await getMeApi("bearer-token-xyz");

      expect(user.id).toBe(1);
      expect(user.username).toBe("test_auth_admin");
      expect(user.role).toBe("admin");
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/auth/me"),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer bearer-token-xyz",
          }),
        })
      );
    });

    it("throws unauthorized error on 401 response", async () => {
      vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          success: false,
          error: {
            code: "UNAUTHORIZED",
            message: "Authentication token has expired.",
            status_code: 401,
          },
        }),
      } as Response);

      await expect(getMeApi("expired-token")).rejects.toThrow(
        "Authentication token has expired."
      );
    });
  });
});
