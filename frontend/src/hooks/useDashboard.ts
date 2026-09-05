import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";
import type { DashboardSummaryResponse } from "../types/api";
import { dashboardToKpis, type DashboardKpi } from "../utils/adapters";

interface UseDashboardResult {
  summary: DashboardSummaryResponse | null;
  kpis: DashboardKpi[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useDashboard(): UseDashboardResult {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      setSummary(null);
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetch();
  }, [fetch]);

  const kpis = summary ? dashboardToKpis(summary) : [];

  const refetch = useCallback(async () => {
    await fetch();
  }, [fetch]);

  return { summary, kpis, loading, error, refetch };
}