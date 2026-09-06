import { describe, it, expect } from "vitest";
import { ApiError, normalizeApiError } from "@/lib/api/error";

describe("ApiError & normalizeApiError", () => {
  describe("ApiError class", () => {
    it("correctly assigns constructor properties", () => {
      const err = new ApiError({
        message: "Resource not found",
        status: 404,
        code: "NOT_FOUND",
        requestId: "req-123",
        details: { entity: "ShelterSite", id: 99 },
        timestamp: "2026-09-06T12:00:00Z",
        isNetworkError: false,
        isAborted: false,
      });

      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(ApiError);
      expect(err.name).toBe("ApiError");
      expect(err.message).toBe("Resource not found");
      expect(err.status).toBe(404);
      expect(err.code).toBe("NOT_FOUND");
      expect(err.requestId).toBe("req-123");
      expect(err.details).toEqual({ entity: "ShelterSite", id: 99 });
      expect(err.timestamp).toBe("2026-09-06T12:00:00Z");
      expect(err.isNetworkError).toBe(false);
      expect(err.isAborted).toBe(false);
    });

    it("evaluates helper getters correctly", () => {
      const authErr = new ApiError({ message: "Auth required", status: 401, code: "UNAUTHORIZED" });
      expect(authErr.isAuthError).toBe(true);
      expect(authErr.isForbidden).toBe(false);
      expect(authErr.isNotFound).toBe(false);
      expect(authErr.isValidationError).toBe(false);

      const forbiddenErr = new ApiError({ message: "Forbidden", status: 403, code: "FORBIDDEN" });
      expect(forbiddenErr.isForbidden).toBe(true);
      expect(forbiddenErr.isAuthError).toBe(false);

      const notFoundErr = new ApiError({ message: "Not found", status: 404, code: "NOT_FOUND" });
      expect(notFoundErr.isNotFound).toBe(true);

      const valErr = new ApiError({ message: "Invalid input", status: 422, code: "VALIDATION_ERROR" });
      expect(valErr.isValidationError).toBe(true);
    });
  });

  describe("normalizeApiError", () => {
    it("returns existing ApiError unchanged", () => {
      const original = new ApiError({ message: "Original", status: 400, code: "ERR" });
      const normalized = normalizeApiError(original);
      expect(normalized).toBe(original);
    });

    it("normalizes DOMException AbortError into REQUEST_ABORTED", () => {
      const abortDom = new DOMException("Operation aborted", "AbortError");
      const normalized = normalizeApiError(abortDom);

      expect(normalized.isAborted).toBe(true);
      expect(normalized.code).toBe("REQUEST_ABORTED");
      expect(normalized.status).toBe(0);
    });

    it("normalizes Error with name AbortError into REQUEST_ABORTED", () => {
      const err = new Error("User cancelled");
      err.name = "AbortError";
      const normalized = normalizeApiError(err);

      expect(normalized.isAborted).toBe(true);
      expect(normalized.code).toBe("REQUEST_ABORTED");
      expect(normalized.status).toBe(0);
    });

    it("extracts M2-04 standardized ErrorResponse payload", () => {
      const m204Payload = {
        success: false,
        error: {
          code: "INVALID_CREDENTIALS",
          message: "Incorrect username or password provided.",
          status_code: 401,
          request_id: "req-xyz-789",
          details: { attempt: 3 },
          timestamp: "2026-09-06T12:00:00Z",
        },
      };

      const response = new Response(JSON.stringify(m204Payload), {
        status: 401,
        headers: { "x-request-id": "req-xyz-789" },
      });

      const normalized = normalizeApiError(new Error("HTTP 401"), response, m204Payload);

      expect(normalized.status).toBe(401);
      expect(normalized.code).toBe("INVALID_CREDENTIALS");
      expect(normalized.message).toBe("Incorrect username or password provided.");
      expect(normalized.requestId).toBe("req-xyz-789");
      expect(normalized.details).toEqual({ attempt: 3 });
      expect(normalized.timestamp).toBe("2026-09-06T12:00:00Z");
      expect(normalized.isAuthError).toBe(true);
    });

    it("maps HTTP status codes with default messages when no payload details exist", () => {
      const testCases = [
        { status: 400, expectedCode: "BAD_REQUEST" },
        { status: 401, expectedCode: "UNAUTHORIZED" },
        { status: 403, expectedCode: "FORBIDDEN" },
        { status: 404, expectedCode: "NOT_FOUND" },
        { status: 422, expectedCode: "VALIDATION_ERROR" },
        { status: 500, expectedCode: "INTERNAL_SERVER_ERROR" },
        { status: 502, expectedCode: "BAD_GATEWAY" },
        { status: 503, expectedCode: "SERVICE_UNAVAILABLE" },
        { status: 418, expectedCode: "HTTP_418" },
      ];

      for (const tc of testCases) {
        const response = new Response(null, {
          status: tc.status,
          headers: { "x-request-id": `req-${tc.status}` },
        });

        const normalized = normalizeApiError(new Error(), response);
        expect(normalized.status).toBe(tc.status);
        expect(normalized.code).toBe(tc.expectedCode);
        expect(normalized.requestId).toBe(`req-${tc.status}`);
      }
    });

    it("normalizes network failures", () => {
      const typeErr = new TypeError("Failed to fetch");
      const normalized = normalizeApiError(typeErr);

      expect(normalized.isNetworkError).toBe(true);
      expect(normalized.status).toBe(0);
      expect(normalized.code).toBe("NETWORK_ERROR");
      expect(normalized.message).toContain("network connectivity");
    });

    it("normalizes network error when Error message contains 'network'", () => {
      const netErr = new Error("Network request failed");
      const normalized = normalizeApiError(netErr);

      expect(normalized.isNetworkError).toBe(true);
      expect(normalized.status).toBe(0);
      expect(normalized.code).toBe("NETWORK_ERROR");
    });

    it("handles generic fallback for unexpected non-error primitives", () => {
      const normalized = normalizeApiError("something unusual");

      expect(normalized.status).toBe(500);
      expect(normalized.code).toBe("UNEXPECTED_ERROR");
      expect(normalized.message).toBe("An unexpected error occurred.");
    });
  });
});
