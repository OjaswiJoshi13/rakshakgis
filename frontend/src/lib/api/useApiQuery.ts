"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { QueryOptions, QueryState, QueryStatus } from "@/types/api";
import { apiCache } from "./cache";
import { ApiError, normalizeApiError } from "./error";

/**
 * Declarative hook for fetching and caching server state.
 * Supports auto-cancellation via AbortSignal, race-condition safety, and TTL caching.
 */
export function useApiQuery<T>(
  key: string | null,
  queryFn: (signal: AbortSignal) => Promise<T>,
  options: QueryOptions<T> = {}
): QueryState<T> {
  const {
    enabled = true,
    cacheTtlMs = 0,
    initialData,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState<T | null>(initialData ?? null);
  const [error, setError] = useState<ApiError | null>(null);
  const [status, setStatus] = useState<QueryStatus>(
    key && enabled ? "loading" : "idle"
  );
  const [isFetching, setIsFetching] = useState<boolean>(Boolean(key && enabled));

  const statusRef = useRef<QueryStatus>(status);
  statusRef.current = status;

  const activeControllerRef = useRef<AbortController | null>(null);
  const currentKeyRef = useRef<string | null>(key);
  const requestCounterRef = useRef<number>(0);

  // Keep latest callbacks in refs to avoid re-triggering effects
  const onSuccessRef = useRef(onSuccess);
  onSuccessRef.current = onSuccess;
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;
  const queryFnRef = useRef(queryFn);
  queryFnRef.current = queryFn;

  const executeFetch = useCallback(
    async (isManualRefetch = false): Promise<T | null> => {
      if (!key || (!enabled && !isManualRefetch)) {
        setStatus("idle");
        setIsFetching(false);
        return null;
      }

      // Check cache first if not manually refetching
      if (!isManualRefetch && cacheTtlMs > 0) {
        const cached = apiCache.get<T>(key);
        if (cached !== null) {
          setData(cached);
          setError(null);
          setStatus("success");
          setIsFetching(false);
          return cached;
        }
      }

      // Cancel any ongoing in-flight request for previous query
      if (activeControllerRef.current) {
        activeControllerRef.current.abort();
      }

      const controller = new AbortController();
      activeControllerRef.current = controller;
      const thisRequestId = ++requestCounterRef.current;

      setIsFetching(true);
      if (statusRef.current !== "success" || isManualRefetch) {
        setStatus("loading");
      }
      setError(null);

      try {
        const result = await queryFnRef.current(controller.signal);

        // Guard against race conditions: verify this request is still current
        if (
          thisRequestId === requestCounterRef.current &&
          !controller.signal.aborted
        ) {
          if (cacheTtlMs > 0) {
            apiCache.set(key, result, cacheTtlMs);
          }
          setData(result);
          setError(null);
          setStatus("success");
          setIsFetching(false);
          onSuccessRef.current?.(result);
          return result;
        }
        return null;
      } catch (err) {
        const normalized = normalizeApiError(err);

        // Do not update error state if the request was deliberately aborted
        if (normalized.isAborted) {
          return null;
        }

        if (thisRequestId === requestCounterRef.current) {
          setError(normalized);
          setStatus("error");
          setIsFetching(false);
          onErrorRef.current?.(normalized);
        }
        return null;
      }
    },
    [key, enabled, cacheTtlMs]
  );

  useEffect(() => {
    currentKeyRef.current = key;
    if (key && enabled) {
      executeFetch(false);
    } else {
      setStatus("idle");
      setIsFetching(false);
    }

    return () => {
      if (activeControllerRef.current) {
        activeControllerRef.current.abort();
      }
    };
  }, [key, enabled, executeFetch]);

  const refetch = useCallback(() => {
    return executeFetch(true);
  }, [executeFetch]);

  const abort = useCallback(() => {
    if (activeControllerRef.current) {
      activeControllerRef.current.abort();
    }
  }, []);

  return {
    data,
    error,
    isLoading: status === "loading",
    isFetching,
    isSuccess: status === "success",
    isError: status === "error",
    status,
    refetch,
    abort,
  };
}
