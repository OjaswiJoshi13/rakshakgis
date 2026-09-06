"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { MutationOptions, MutationState } from "@/types/api";
import { ApiError, normalizeApiError } from "./error";

/**
 * Declarative hook for executing mutations (POST, PUT, PATCH, DELETE operations).
 */
export function useApiMutation<TData, TVariables = void>(
  mutationFn: (variables: TVariables, signal: AbortSignal) => Promise<TData>,
  options: MutationOptions<TData> = {}
): MutationState<TData, TVariables> {
  const [data, setData] = useState<TData | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);
  const [isError, setIsError] = useState<boolean>(false);

  const activeControllerRef = useRef<AbortController | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;
  const mutationFnRef = useRef(mutationFn);
  mutationFnRef.current = mutationFn;

  useEffect(() => {
    return () => {
      if (activeControllerRef.current) {
        activeControllerRef.current.abort();
      }
    };
  }, []);

  const mutate = useCallback(async (variables?: TVariables): Promise<TData> => {
    if (activeControllerRef.current) {
      activeControllerRef.current.abort();
    }

    const controller = new AbortController();
    activeControllerRef.current = controller;

    setIsLoading(true);
    setError(null);
    setIsSuccess(false);
    setIsError(false);

    try {
      const result = await mutationFnRef.current(variables as TVariables, controller.signal);
      setData(result);
      setIsLoading(false);
      setIsSuccess(true);
      setIsError(false);
      optionsRef.current.onSuccess?.(result);
      return result;
    } catch (err) {
      const normalized = normalizeApiError(err);
      setError(normalized);
      setIsLoading(false);
      setIsSuccess(false);
      setIsError(true);
      optionsRef.current.onError?.(normalized);
      throw normalized;
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
    setIsSuccess(false);
    setIsError(false);
  }, []);

  return {
    data,
    error,
    isLoading,
    isSuccess,
    isError,
    mutate,
    reset,
  };
}
