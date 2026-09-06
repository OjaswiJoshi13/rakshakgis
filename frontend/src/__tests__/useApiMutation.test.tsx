import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useApiMutation } from "@/lib/api/useApiMutation";
import { ApiError } from "@/lib/api/error";

describe("useApiMutation", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("initializes with clean idle state", () => {
    const mutationFn = vi.fn();
    const { result } = renderHook(() => useApiMutation(mutationFn));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it("executes mutation successfully and triggers onSuccess", async () => {
    const responsePayload = { scenarioId: "sc-101", status: "SIMULATING" };
    const mutationFn = vi.fn().mockResolvedValue(responsePayload);
    const onSuccess = vi.fn();

    const { result } = renderHook(() =>
      useApiMutation(mutationFn, { onSuccess })
    );

    let returned: unknown;
    await act(async () => {
      returned = await result.current.mutate({ rainfall_multiplier: 1.5 });
    });

    expect(returned).toEqual(responsePayload);
    expect(result.current.data).toEqual(responsePayload);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(true);
    expect(result.current.isError).toBe(false);
    expect(result.current.error).toBeNull();
    expect(mutationFn).toHaveBeenCalledWith(
      { rainfall_multiplier: 1.5 },
      expect.any(AbortSignal)
    );
    expect(onSuccess).toHaveBeenCalledWith(responsePayload);
  });

  it("handles mutation failure and triggers onError", async () => {
    const apiError = new ApiError({
      message: "Simulation budget exceeded",
      status: 400,
      code: "BAD_REQUEST",
    });
    const mutationFn = vi.fn().mockRejectedValue(apiError);
    const onError = vi.fn();

    const { result } = renderHook(() =>
      useApiMutation(mutationFn, { onError })
    );

    await act(async () => {
      try {
        await result.current.mutate({ invalid: true });
      } catch {
        // Expected throw from mutate()
      }
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.isError).toBe(true);
    expect(result.current.error).toBe(apiError);
    expect(result.current.data).toBeNull();
    expect(onError).toHaveBeenCalledWith(apiError);
  });

  it("resets state when reset is called", async () => {
    const mutationFn = vi.fn().mockResolvedValue({ id: 1 });
    const { result } = renderHook(() => useApiMutation(mutationFn));

    await act(async () => {
      await result.current.mutate();
    });

    expect(result.current.isSuccess).toBe(true);
    expect(result.current.data).toEqual({ id: 1 });

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.isError).toBe(false);
  });
});
