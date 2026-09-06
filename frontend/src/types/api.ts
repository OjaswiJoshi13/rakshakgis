/**
 * Centralized API & Networking Types
 * Conforms strictly to backend Chunk M2-04 Common API Error & Envelope Contracts.
 */

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface PaginationMetadata {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ResponseEnvelope<T> {
  success: boolean;
  data: T;
  request_id?: string | null;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: PaginationMetadata;
  request_id?: string | null;
  timestamp?: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  status_code: number;
  request_id?: string | null;
  details?: unknown;
  timestamp?: string;
}

export interface ErrorResponse {
  success: false;
  error: ApiErrorDetail;
}

export interface RequestOptions {
  /** Optional URL query parameters serialized into the URL */
  params?: Record<string, string | number | boolean | undefined | null>;
  /** Optional custom headers */
  headers?: Record<string, string>;
  /** Optional request body (automatically serialized to JSON if object) */
  body?: unknown;
  /**
   * Whether to attach Authorization: Bearer <token> automatically.
   * Defaults to true if an access token exists.
   */
  auth?: boolean;
  /** Optional AbortSignal for request cancellation / race-condition protection */
  signal?: AbortSignal;
  /** Optional request timeout in milliseconds */
  timeoutMs?: number;
  /** Standard fetch cache option */
  cache?: RequestCache;
}

export type QueryStatus = "idle" | "loading" | "success" | "error";

export interface QueryState<T> {
  data: T | null;
  error: import("@/lib/api/error").ApiError | null;
  isLoading: boolean;
  isFetching: boolean;
  isSuccess: boolean;
  isError: boolean;
  status: QueryStatus;
  refetch: () => Promise<T | null>;
  abort: () => void;
}

export interface QueryOptions<T> {
  /** Whether the query should execute automatically. Defaults to true. */
  enabled?: boolean;
  /** Cache time-to-live in milliseconds. Defaults to 0 (no cache). */
  cacheTtlMs?: number;
  /** Initial data before fetch resolves */
  initialData?: T;
  /** Callback fired on successful query completion */
  onSuccess?: (data: T) => void;
  /** Callback fired on query error */
  onError?: (error: import("@/lib/api/error").ApiError) => void;
}

export interface MutationState<TData, TVariables> {
  data: TData | null;
  error: import("@/lib/api/error").ApiError | null;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
  mutate: (variables?: TVariables) => Promise<TData>;
  reset: () => void;
}

export interface MutationOptions<TData> {
  /** Callback fired on successful mutation completion */
  onSuccess?: (data: TData) => void;
  /** Callback fired on mutation error */
  onError?: (error: import("@/lib/api/error").ApiError) => void;
}
