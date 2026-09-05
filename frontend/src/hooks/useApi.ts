import { useCallback, useEffect, useState } from "react";
import type { ApiError } from "../services/apiClient";

export interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function extractErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const apiError = error as ApiError;
    if (apiError.status === 0) {
      return "Unable to reach the Apex Sales AI backend. Verify the API is running.";
    }
    if (apiError.status >= 500) {
      return `Server error (${apiError.status}). ${apiError.message}`;
    }
    return apiError.message;
  }
  return "An unexpected error occurred.";
}

/**
 * Minimal generic data-fetching hook.
 *
 * Runs the supplied async `fetcher` on mount and whenever any value in
 * `deps` changes (by reference equality). Returns `{ data, loading, error,
 * refetch }`. `refetch` re-runs the fetcher and resolves once the new
 * attempt has completed (whether it succeeded or failed).
 */
export function useApi<T>(fetcher: () => Promise<T>, deps?: ReadonlyArray<unknown>): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (caught) {
      setError(extractErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  }, deps ?? []);

  useEffect(() => {
    void run();
  }, [run]);

  const refetch = useCallback(async (): Promise<void> => {
    await run();
  }, [run]);

  return { data, loading, error, refetch };
}

export default useApi;