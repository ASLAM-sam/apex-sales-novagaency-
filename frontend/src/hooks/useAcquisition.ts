import { useCallback, useState } from "react";
import { api } from "../services/api";
import type { AcquisitionCandidate, AcquisitionSearchResponse, AcquisitionImportResponse } from "../types/api";
import { acquisitionCandidateToDisplay, type AcquisitionCandidateDisplay } from "../utils/adapters";

interface UseAcquisitionSearchResult {
  candidates: AcquisitionCandidateDisplay[];
  loading: boolean;
  error: string | null;
  search: (params: {
    source?: string;
    query?: string;
    category?: string;
    city?: string;
    state?: string;
    country?: string;
    limit?: number;
    manual_candidates?: Array<{
      name: string;
      website?: string;
      phone?: string;
      email?: string;
      address?: string;
      city?: string;
      state?: string;
      country?: string;
      category?: string;
      source_name?: string;
      source_id?: string;
    }>;
  }) => Promise<void>;
}

export function useAcquisitionSearch(): UseAcquisitionSearchResult {
  const [candidates, setCandidates] = useState<AcquisitionCandidateDisplay[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (params: {
    source?: string;
    query?: string;
    category?: string;
    city?: string;
    state?: string;
    country?: string;
    limit?: number;
    manual_candidates?: Array<{
      name: string;
      website?: string;
      phone?: string;
      email?: string;
      address?: string;
      city?: string;
      state?: string;
      country?: string;
      category?: string;
      source_name?: string;
      source_id?: string;
    }>;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const response: AcquisitionSearchResponse = await api.searchAcquisition(params);
      setCandidates(response.candidates.map(acquisitionCandidateToDisplay));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }, []);

  return { candidates, loading, error, search };
}

interface UseAcquisitionImportResult {
  loading: boolean;
  error: string | null;
  result: AcquisitionImportResponse | null;
  import: (candidates: AcquisitionCandidate[]) => Promise<void>;
}

export function useAcquisitionImport(): UseAcquisitionImportResult {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AcquisitionImportResponse | null>(null);

  const importCandidates = useCallback(async (selectedCandidates: AcquisitionCandidate[]) => {
    setLoading(true);
    setError(null);
    try {
      const response: AcquisitionImportResponse = await api.importCandidates(selectedCandidates);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, result, import: importCandidates };
}