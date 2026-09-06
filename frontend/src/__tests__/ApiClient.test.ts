import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { ApiClient } from "@/lib/api/client";
import { ApiError } from "@/lib/api/error";
import * as authLib from "@/lib/auth";

describe("ApiClient", () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient("http://localhost:8000/api/v1");
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  describe("URL Construction and Normalization", () => {
    it("normalizes base URL by stripping trailing slashes", () => {
      const c = new ApiClient("http://api.rakshakgis.gov.in/api/v1///");
      expect(c.getBaseUrl()).toBe("http://api.rakshakgis.gov.in/api/v1");
    });

    it("joins relative path with base URL and strips leading slashes", () => {
      const url = client.buildUrl("/sites/evaluate");
      expect(url).toBe("http://localhost:8000/api/v1/sites/evaluate");
    });

    it("respects fully-qualified absolute URLs", () => {
      const url = client.buildUrl("https://external-gis.gov.in/tiles/metadata.json");
      expect(url).toBe("https://external-gis.gov.in/tiles/metadata.json");
    });

    it("correctly serializes query parameters", () => {
      const url = client.buildUrl("relocation/candidates", {
        district_id: 10,
        include_scores: true,
        priority: "HIGH",
        skipped: null,
        ignored: undefined,
      });

      expect(url).toBe(
        "http://localhost:8000/api/v1/relocation/candidates?district_id=10&include_scores=true&priority=HIGH"
      );
    });

    it("appends parameters with ampersand if path already contains a query string", () => {
      const url = client.buildUrl("routes?profile=himalayan", {
        limit: 5,
      });
      expect(url).toBe("http://localhost:8000/api/v1/routes?profile=himalayan&limit=5");
    });
  });

  describe("HTTP Requests and Headers", () => {
    it("dispatches GET request with default headers", async () => {
      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ status: "online", version: "v1" }),
      } as unknown as Response);

      const result = await client.get<{ status: string }>("");

      expect(fetchSpy).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Accept: "application/json",
          }),
        })
      );
      expect(result.status).toBe("online");
    });

    it("dispatches POST request with serialized JSON body and Content-Type header", async () => {
      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ site_id: 42, result: "created" }),
      } as unknown as Response);

      const payload = { site_name: "Chamoli Shelter A", capacity: 500 };
      const result = await client.post<{ site_id: number }>("/sites", payload);

      expect(fetchSpy).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/sites",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
            Accept: "application/json",
          }),
          body: JSON.stringify(payload),
        })
      );
      expect(result.site_id).toBe(42);
    });

    it("dispatches PUT, PATCH, and DELETE requests correctly", async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ success: true }),
      } as unknown as Response;

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(mockResponse);

      await client.put("/sites/1", { status: "active" });
      expect(fetchSpy).toHaveBeenLastCalledWith(
        expect.stringContaining("/sites/1"),
        expect.objectContaining({ method: "PUT" })
      );

      await client.patch("/sites/1", { notes: "Updated" });
      expect(fetchSpy).toHaveBeenLastCalledWith(
        expect.stringContaining("/sites/1"),
        expect.objectContaining({ method: "PATCH" })
      );

      await client.delete("/sites/1");
      expect(fetchSpy).toHaveBeenLastCalledWith(
        expect.stringContaining("/sites/1"),
        expect.objectContaining({ method: "DELETE" })
      );
    });

    it("handles 204 No Content gracefully without failing JSON parsing", async () => {
      vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 204,
        headers: new Headers(),
      } as unknown as Response);

      const result = await client.delete("/items/1");
      expect(result).toEqual({});
    });
  });

  describe("Authentication Header Injection", () => {
    it("automatically injects Authorization Bearer token when token exists in storage", async () => {
      authLib.setStoredToken("test-jwt-token", 3600);

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ user: "officer" }),
      } as unknown as Response);

      await client.get("/auth/me");

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test-jwt-token",
          }),
        })
      );
    });

    it("omits Authorization header when auth is explicitly set to false", async () => {
      authLib.setStoredToken("test-jwt-token", 3600);

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ status: "healthy" }),
      } as unknown as Response);

      await client.get("/health", { auth: false });

      const calledHeaders = fetchSpy.mock.calls[0][1]?.headers as Record<string, string>;
      expect(calledHeaders["Authorization"]).toBeUndefined();
    });

    it("does not inject Authorization header if no token is stored", async () => {
      authLib.clearStoredToken();

      const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ status: "online" }),
      } as unknown as Response);

      await client.get("/api/v1");

      const calledHeaders = fetchSpy.mock.calls[0][1]?.headers as Record<string, string>;
      expect(calledHeaders["Authorization"]).toBeUndefined();
    });
  });

  describe("Error Handling", () => {
    it("throws normalized ApiError with M2-04 backend error details on failure", async () => {
      const errorResponse = {
        success: false,
        error: {
          code: "NOT_FOUND",
          message: "The requested candidate relocation site was not found.",
          status_code: 404,
          request_id: "req-abc-123",
        },
      };

      vi.spyOn(global, "fetch").mockResolvedValueOnce({
        ok: false,
        status: 404,
        headers: new Headers({
          "content-type": "application/json",
          "x-request-id": "req-abc-123",
        }),
        json: async () => errorResponse,
      } as unknown as Response);

      try {
        await client.get("/sites/999");
        expect.fail("Expected ApiClient to throw ApiError");
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.status).toBe(404);
        expect(apiErr.code).toBe("NOT_FOUND");
        expect(apiErr.message).toBe(
          "The requested candidate relocation site was not found."
        );
        expect(apiErr.requestId).toBe("req-abc-123");
        expect(apiErr.isNotFound).toBe(true);
      }
    });

    it("converts network failure into ApiError with isNetworkError flag", async () => {
      vi.spyOn(global, "fetch").mockRejectedValueOnce(new TypeError("Failed to fetch"));

      try {
        await client.get("/telemetry");
        expect.fail("Expected ApiClient to throw ApiError");
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.isNetworkError).toBe(true);
        expect(apiErr.status).toBe(0);
        expect(apiErr.code).toBe("NETWORK_ERROR");
      }
    });

    it("handles request cancellation via AbortSignal", async () => {
      const abortError = new DOMException("The user aborted a request.", "AbortError");
      vi.spyOn(global, "fetch").mockRejectedValueOnce(abortError);

      try {
        const controller = new AbortController();
        controller.abort();
        await client.get("/scenarios", { signal: controller.signal });
        expect.fail("Expected ApiClient to throw");
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.isAborted).toBe(true);
        expect(apiErr.code).toBe("REQUEST_ABORTED");
      }
    });
  });
});
