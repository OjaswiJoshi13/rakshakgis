/**
 * Normalized API Error Handling
 * Integrates directly with backend Chunk M2-04 standardized ErrorResponse contract.
 */

import { ApiErrorDetail, ErrorResponse } from "@/types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string | null;
  readonly details?: unknown;
  readonly timestamp?: string;
  readonly isNetworkError: boolean;
  readonly isAborted: boolean;

  constructor(options: {
    message: string;
    status: number;
    code: string;
    requestId?: string | null;
    details?: unknown;
    timestamp?: string;
    isNetworkError?: boolean;
    isAborted?: boolean;
  }) {
    super(options.message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.requestId = options.requestId;
    this.details = options.details;
    this.timestamp = options.timestamp;
    this.isNetworkError = options.isNetworkError ?? false;
    this.isAborted = options.isAborted ?? false;

    // Maintain standard Error prototype chain
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  get isAuthError(): boolean {
    return this.status === 401;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isValidationError(): boolean {
    return this.status === 422;
  }
}

/**
 * Normalizes an unknown error, HTTP response, or parsed error payload into a strongly-typed ApiError.
 */
export function normalizeApiError(
  error: unknown,
  response?: Response,
  data?: unknown
): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  // Handle AbortController cancellation
  if (
    (error instanceof DOMException && error.name === "AbortError") ||
    (error instanceof Error && error.name === "AbortError")
  ) {
    return new ApiError({
      message: "The requested operation was cancelled.",
      status: 0,
      code: "REQUEST_ABORTED",
      isAborted: true,
    });
  }

  // Handle structured M2-04 ErrorResponse if data is provided
  if (data && typeof data === "object") {
    const errorEnvelope = data as Partial<ErrorResponse>;
    if (errorEnvelope.error && typeof errorEnvelope.error === "object") {
      const detail = errorEnvelope.error as ApiErrorDetail;
      return new ApiError({
        message: detail.message || "An API error occurred.",
        status: detail.status_code || response?.status || 500,
        code: detail.code || "API_ERROR",
        requestId: detail.request_id || response?.headers.get("x-request-id"),
        details: detail.details,
        timestamp: detail.timestamp,
      });
    }
  }

  // Handle standard HTTP status codes when response is present
  if (response) {
    const status = response.status;
    const requestId = response.headers.get("x-request-id");

    const defaultMessages: Record<number, { code: string; message: string }> = {
      400: { code: "BAD_REQUEST", message: "Bad request. Please verify inputs." },
      401: { code: "UNAUTHORIZED", message: "Invalid credentials or session expired." },
      403: { code: "FORBIDDEN", message: "Access forbidden: insufficient role permissions." },
      404: { code: "NOT_FOUND", message: "Requested disaster GIS resource not found." },
      422: { code: "VALIDATION_ERROR", message: "Request payload validation failed." },
      500: { code: "INTERNAL_SERVER_ERROR", message: "Internal disaster platform server error." },
      502: { code: "BAD_GATEWAY", message: "Bad gateway. Decision support service unavailable." },
      503: { code: "SERVICE_UNAVAILABLE", message: "Disaster management service temporarily unavailable." },
    };

    const fallback = defaultMessages[status] || {
      code: `HTTP_${status}`,
      message: `Request failed with status code ${status}.`,
    };

    return new ApiError({
      message: fallback.message,
      status,
      code: fallback.code,
      requestId,
    });
  }

  // Handle network connectivity failures
  if (error instanceof TypeError || (error instanceof Error && /fetch|network/i.test(error.message))) {
    return new ApiError({
      message: "Unable to connect to RakshakGIS backend service. Please check network connectivity.",
      status: 0,
      code: "NETWORK_ERROR",
      isNetworkError: true,
    });
  }

  // Fallback for generic errors
  const fallbackMessage =
    error instanceof Error ? error.message : "An unexpected error occurred.";

  return new ApiError({
    message: fallbackMessage,
    status: 500,
    code: "UNEXPECTED_ERROR",
  });
}
