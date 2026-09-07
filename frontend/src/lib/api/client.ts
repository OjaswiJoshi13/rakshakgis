/**
 * Centralized Typed API Client
 * Reusable HTTP networking client for RakshakGIS frontend modules.
 * Integrates directly with M5-02 session tokens and M2-04 error contracts.
 */

import { getApiBaseUrl, getStoredToken, isTokenExpired } from "@/lib/auth";
import { HttpMethod, RequestOptions } from "@/types/api";
import { ApiError, normalizeApiError } from "./error";

export class ApiClient {
  private customBaseUrl?: string;

  constructor(customBaseUrl?: string) {
    this.customBaseUrl = customBaseUrl;
  }

  /**
   * Retrieves the normalized API base URL.
   */
  public getBaseUrl(): string {
    if (this.customBaseUrl) {
      return this.customBaseUrl.replace(/\/+$/, "");
    }
    return getApiBaseUrl();
  }

  /**
   * Constructs a fully-qualified URL with properly formatted query parameters.
   */
  public buildUrl(
    path: string,
    params?: Record<string, string | number | boolean | undefined | null>
  ): string {
    const isAbsolute = /^https?:\/\//i.test(path);
    const baseUrl = this.getBaseUrl();
    let cleanPath = path.replace(/^\/+/, "");
    if (baseUrl.endsWith("/api/v1") && cleanPath.startsWith("api/v1/")) {
      cleanPath = cleanPath.slice("api/v1/".length);
    } else if (baseUrl.endsWith("/api/v1") && cleanPath === "api/v1") {
      cleanPath = "";
    }
    const fullPath = isAbsolute ? path : cleanPath ? `${baseUrl}/${cleanPath}` : baseUrl;

    if (!params || Object.keys(params).length === 0) {
      return fullPath;
    }

    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    }

    const queryString = searchParams.toString();
    if (!queryString) {
      return fullPath;
    }

    const separator = fullPath.includes("?") ? "&" : "?";
    return `${fullPath}${separator}${queryString}`;
  }

  /**
   * Dispatches a typed HTTP request.
   */
  public async request<T = unknown>(
    path: string,
    method: HttpMethod = "GET",
    options: RequestOptions = {}
  ): Promise<T> {
    const url = this.buildUrl(path, options.params);

    const headers: Record<string, string> = {
      Accept: "application/json",
      ...(options.headers || {}),
    };

    // Inject Bearer token if auth is not explicitly disabled
    const shouldAuthenticate = options.auth !== false;
    if (shouldAuthenticate && !headers["Authorization"]) {
      const token = getStoredToken();
      if (token && !isTokenExpired()) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    let requestBody: BodyInit | null | undefined = undefined;
    if (options.body !== undefined && options.body !== null) {
      if (
        typeof options.body === "object" &&
        !(options.body instanceof FormData) &&
        !(options.body instanceof Blob)
      ) {
        headers["Content-Type"] = "application/json";
        requestBody = JSON.stringify(options.body);
      } else {
        requestBody = options.body as BodyInit;
      }
    }

    // Set up AbortController with optional timeout
    let timeoutId: NodeJS.Timeout | undefined = undefined;
    let signal = options.signal;

    if (options.timeoutMs && options.timeoutMs > 0) {
      const controller = new AbortController();
      timeoutId = setTimeout(() => {
        controller.abort();
      }, options.timeoutMs);

      if (options.signal) {
        options.signal.addEventListener("abort", () => controller.abort());
      }
      signal = controller.signal;
    }

    let response: Response;
    try {
      response = await fetch(url, {
        method,
        headers,
        body: requestBody,
        signal,
        cache: options.cache,
      });
    } catch (fetchError) {
      if (timeoutId) clearTimeout(timeoutId);
      throw normalizeApiError(fetchError);
    } finally {
      if (timeoutId) clearTimeout(timeoutId);
    }

    // Handle 204 No Content or zero-length responses
    if (response.status === 204) {
      return {} as T;
    }

    const contentLength = response.headers.get("content-length");
    if (contentLength === "0") {
      return {} as T;
    }

    let responseData: unknown = null;
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      try {
        responseData = await response.json();
      } catch {
        responseData = null;
      }
    } else {
      try {
        const text = await response.text();
        responseData = text ? { message: text } : {};
      } catch {
        responseData = null;
      }
    }

    if (!response.ok) {
      throw normalizeApiError(new Error(), response, responseData);
    }

    return responseData as T;
  }

  public get<T = unknown>(
    path: string,
    options?: Omit<RequestOptions, "body">
  ): Promise<T> {
    return this.request<T>(path, "GET", options);
  }

  public post<T = unknown>(
    path: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(path, "POST", { ...options, body });
  }

  public put<T = unknown>(
    path: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(path, "PUT", { ...options, body });
  }

  public patch<T = unknown>(
    path: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(path, "PATCH", { ...options, body });
  }

  public delete<T = unknown>(
    path: string,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(path, "DELETE", options);
  }
}

/**
 * Singleton API client instance configured with the environment base URL.
 */
export const apiClient = new ApiClient();
