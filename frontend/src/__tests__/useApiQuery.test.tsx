import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useApiQuery } from "@/lib/api/useApiQuery";
import { apiCache } from "@/lib/api/cache";
import { ApiError } from "@/lib/api/error";

describe("useApiQuery", () => {
  beforeEach(() => {
    apiCache.clear();
    vi.restoreAllMocks();
  });

  it("fetches data successfully and updates state", async () => {
    const mockData = { villages: ["Joshimath", "Helang"], count: 2 };
    const queryFn = vi.fn().mockResolvedValue(mockData);
    const onSuccess = vi.fn();

    const { result } = renderHook(() =>
      useApiQuery("villages-key", queryFn, { onSuccess })
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.status).toBe("loading");
    expect(result.current.data).toBeNull();

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(queryFn).toHaveBeenCalledTimes(1);
    expect(onSuccess).toHaveBeenCalledWith(mockData);
  });

  it("does not fetch when enabled is false", async () => {
    const queryFn = vi.fn().mockResolvedValue({ status: "ok" });

    const { result } = renderHook(() =>
      useApiQuery("disabled-key", queryFn, { enabled: false })
    );

    expect(result.current.status).toBe("idle");
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeNull();
    expect(queryFn).not.toHaveBeenCalled();
  });

  it("handles errors and updates error state", async () => {
    const testError = new ApiError({
      message: "Resource unavailable",
      status: 503,
      code: "SERVICE_UNAVAILABLE",
    });
    const queryFn = vi.fn().mockRejectedValue(testError);
    const onError = vi.fn();

    const { result } = renderHook(() =>
      useApiQuery("error-key", queryFn, { onError })
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect(result.current.error?.code).toBe("SERVICE_UNAVAILABLE");
    expect(result.current.data).toBeNull();
    expect(onError).toHaveBeenCalledWith(testError);
  });

  it("returns cached data immediately when cacheTtlMs is active and valid", async () => {
    const cachedData = { cached: true, timestamp: 12345 };
    apiCache.set("cached-key", cachedData, 60000);

    const queryFn = vi.fn().mockResolvedValue({ cached: false });

    const { result } = renderHook(() =>
      useApiQuery("cached-key", queryFn, { cacheTtlMs: 60000 })
    );

    expect(result.current.data).toEqual(cachedData);
    expect(result.current.isSuccess).toBe(true);
    expect(queryFn).not.toHaveBeenCalled();
  });

  it("refetches when refetch is called, bypassing cache", async () => {
    let callCount = 0;
    const queryFn = vi.fn().mockImplementation(async () => {
      callCount++;
      return { run: callCount };
    });

    const { result } = renderHook(() =>
      useApiQuery("refetch-key", queryFn, { cacheTtlMs: 60000 })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual({ run: 1 });
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual({ run: 2 });
    expect(queryFn).toHaveBeenCalledTimes(2);
  });

  it("aborts previous request when query key changes rapidly", async () => {
    let abortedFirst = false;

    const queryFn = vi.fn().mockImplementation((signal: AbortSignal) => {
      return new Promise((resolve, reject) => {
        signal.addEventListener("abort", () => {
          abortedFirst = true;
          reject(new DOMException("Aborted", "AbortError"));
        });
        setTimeout(() => resolve({ done: true }), 100);
      });
    });

    const { rerender } = renderHook(
      ({ key }) => useApiQuery(key, queryFn),
      { initialProps: { key: "initial-key" } }
    );

    // Rapidly change key to test race condition / abort
    rerender({ key: "updated-key" });

    await waitFor(() => {
      expect(abortedFirst).toBe(true);
    });
  });

  it("supports manual abort invocation", async () => {
    let signalReceived: AbortSignal | null = null;
    const queryFn = vi.fn().mockImplementation((signal: AbortSignal) => {
      signalReceived = signal;
      return new Promise<void>(() => {}); // never resolves
    });

    const { result } = renderHook(() => useApiQuery("abort-key", queryFn));

    act(() => {
      result.current.abort();
    });

    const isAborted = (signalReceived as AbortSignal | null)?.aborted;
    expect(isAborted).toBe(true);
  });
});
