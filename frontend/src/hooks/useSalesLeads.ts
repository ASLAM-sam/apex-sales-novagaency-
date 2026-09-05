import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";
import type { SalesLeadListResponse, GetSalesLeadsParams, SalesLeadSummary } from "../types/api";
import { salesLeadSummaryToLeadItem } from "../utils/adapters";
import type { Lead } from "../types";

interface UseSalesLeadsResult {
  leads: Lead[];
  rawSummaries: SalesLeadSummary[];
  loading: boolean;
  error: string | null;
  pagination: { page: number; pageSize: number; total: number; pages: number } | null;
  refetch: () => Promise<void>;
  setParams: (params: Partial<GetSalesLeadsParams>) => void;
  params: GetSalesLeadsParams;
}

export function useSalesLeads(initialParams: GetSalesLeadsParams = {}): UseSalesLeadsResult {
  const [params, setParamsState] = useState<GetSalesLeadsParams>(initialParams);
  const [rawSummaries, setRawSummaries] = useState<SalesLeadSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<UseSalesLeadsResult["pagination"]>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response: SalesLeadListResponse = await api.getSalesLeads(params);
      setRawSummaries(response.leads);
      setPagination({
        page: response.pagination.page,
        pageSize: response.pagination.page_size,
        total: response.pagination.total,
        pages: response.pagination.pages,
      });
    } catch (err) {
      setRawSummaries([]);
      setPagination(null);
      setError(err instanceof Error ? err.message : "Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    void fetch();
  }, [fetch]);

  const leads = rawSummaries.map(salesLeadSummaryToLeadItem);

  const refetch = useCallback(async () => {
    await fetch();
  }, [fetch]);

  const setParams = useCallback((next: Partial<GetSalesLeadsParams>) => {
    setParamsState((prev) => ({ ...prev, ...next }));
  }, []);

  return { leads, rawSummaries, loading, error, pagination, refetch, setParams, params };
}