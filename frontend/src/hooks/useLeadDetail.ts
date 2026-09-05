import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";
import type { Lead } from "../types";
import type { SalesLeadDetailResponse, LeadTimelineResponse, SalesActionResponse, PrepareLeadResponse, ReadinessFlags } from "../types/api";
import { salesLeadDetailToLead, timelineEventToDisplay, type TimelineEventDisplay } from "../utils/adapters";

interface UseLeadDetailResult {
  lead: Lead | null;
  rawDetail: SalesLeadDetailResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useLeadDetail(leadId: string | null): UseLeadDetailResult {
  const [rawDetail, setRawDetail] = useState<SalesLeadDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!leadId) {
      setRawDetail(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSalesLeadDetail(leadId);
      setRawDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load lead detail");
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => {
    void fetch();
  }, [fetch]);

  const lead = rawDetail ? salesLeadDetailToLead(rawDetail) : null;

  const refetch = useCallback(async () => {
    await fetch();
  }, [fetch]);

  return { lead, rawDetail, loading, error, refetch };
}

interface UseLeadTimelineResult {
  events: TimelineEventDisplay[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useLeadTimeline(leadId: string | null): UseLeadTimelineResult {
  const [events, setEvents] = useState<TimelineEventDisplay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!leadId) {
      setEvents([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response: LeadTimelineResponse = await api.getSalesLeadTimeline(leadId);
      setEvents(response.events.map(timelineEventToDisplay));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load timeline");
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => {
    void fetch();
  }, [fetch]);

  const refetch = useCallback(async () => {
    await fetch();
  }, [fetch]);

  return { events, loading, error, refetch };
}

interface UseLeadActionsResult {
  readinessFlags: ReadinessFlags | null;
  nextAction: string | null;
  loading: boolean;
  error: string | null;
  prepare: () => Promise<void>;
  runIntelligence: (forceRefresh?: boolean) => Promise<SalesActionResponse | null>;
  qualify: (forceRefresh?: boolean) => Promise<SalesActionResponse | null>;
  generatePitch: (channel?: "EMAIL" | "WHATSAPP" | "MANUAL", forceRefresh?: boolean) => Promise<SalesActionResponse | null>;
}

export function useLeadActions(leadId: string | null): UseLeadActionsResult {
  const [readinessFlags, setReadinessFlags] = useState<ReadinessFlags | null>(null);
  const [nextAction, setNextAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const prepare = useCallback(async () => {
    if (!leadId) return;
    setLoading(true);
    setError(null);
    try {
      const response: PrepareLeadResponse = await api.prepareSalesLeadAction(leadId);
      setReadinessFlags(response.readiness_flags);
      setNextAction(response.next_recommended_action);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to prepare lead");
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  const runAction = useCallback(async (
    actionType: "RUN_INTELLIGENCE" | "QUALIFY" | "GENERATE_PITCH",
    options?: { channel?: "EMAIL" | "WHATSAPP" | "MANUAL"; force_refresh?: boolean },
  ): Promise<SalesActionResponse | null> => {
    if (!leadId) return null;
    setLoading(true);
    setError(null);
    try {
      const response = await api.triggerSalesLeadAction(leadId, actionType, options);
      await prepare();
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to run ${actionType}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [leadId, prepare]);

  return {
    readinessFlags,
    nextAction,
    loading,
    error,
    prepare,
    runIntelligence: (forceRefresh) => runAction("RUN_INTELLIGENCE", { force_refresh: forceRefresh }),
    qualify: (forceRefresh) => runAction("QUALIFY", { force_refresh: forceRefresh }),
    generatePitch: (channel, forceRefresh) => runAction("GENERATE_PITCH", { channel, force_refresh: forceRefresh }),
  };
}