import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import type { Lead } from "../types";
import type { SalesLeadDetailResponse, LeadTimelineResponse, SalesActionResponse, PrepareLeadResponse, ReadinessFlags } from "../types/api";
import { salesLeadDetailToLead, timelineEventToDisplay, type TimelineEventDisplay } from "../utils/adapters";

const inflightActions = new Set<string>();

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
      setRawDetail(null);
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
        setEvents([]);
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
  preparing: boolean;
  error: string | null;
  lastMessage: string | null;
  prepare: () => Promise<PrepareLeadResponse | null>;
  runIntelligence: (forceRefresh?: boolean) => Promise<SalesActionResponse | null>;
  qualify: (forceRefresh?: boolean) => Promise<SalesActionResponse | null>;
  generatePitch: (channel?: "EMAIL" | "WHATSAPP" | "MANUAL", forceRefresh?: boolean) => Promise<SalesActionResponse | null>;
}

export function useLeadActions(leadId: string | null): UseLeadActionsResult {
  const [readinessFlags, setReadinessFlags] = useState<ReadinessFlags | null>(null);
  const [nextAction, setNextAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const refreshReadiness = useCallback(async (id: string) => {
    const response: PrepareLeadResponse = await api.prepareSalesLeadAction(id);
    if (!mounted.current) return response;
    setReadinessFlags(response.readiness_flags);
    setNextAction(response.next_recommended_action);
    return response;
  }, []);

  const prepare = useCallback(async (): Promise<PrepareLeadResponse | null> => {
    if (!leadId) return null;
    const key = `${leadId}:prepare`;
    if (inflightActions.has(key)) return null;
    inflightActions.add(key);
    setPreparing(true);
    setError(null);
    try {
      const response = await refreshReadiness(leadId);
      if (mounted.current) setLastMessage("Lead is ready for the next sales action.");
      return response;
    } catch (err) {
      if (mounted.current) setError(err instanceof Error ? err.message : "Failed to prepare lead");
      return null;
    } finally {
      inflightActions.delete(key);
      if (mounted.current) setPreparing(false);
    }
  }, [leadId, refreshReadiness]);

  const runAction = useCallback(async (
    actionType: "RUN_INTELLIGENCE" | "QUALIFY" | "GENERATE_PITCH",
    options?: { channel?: "EMAIL" | "WHATSAPP" | "MANUAL"; force_refresh?: boolean },
  ): Promise<SalesActionResponse | null> => {
    if (!leadId) return null;
    const key = `${leadId}:${actionType}`;
    if (inflightActions.has(key)) return null;
    inflightActions.add(key);
    setLoading(true);
    setError(null);
    setLastMessage(null);
    try {
      const response = await api.triggerSalesLeadAction(leadId, actionType, options);
      try {
        await refreshReadiness(leadId);
      } catch {
        // Action succeeded; readiness refresh is best-effort.
      }
      if (mounted.current) setLastMessage(response.message);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Failed to run ${actionType}`;
      if (mounted.current) setError(message);
      throw err instanceof Error ? err : new Error(message);
    } finally {
      inflightActions.delete(key);
      if (mounted.current) setLoading(false);
    }
  }, [leadId, refreshReadiness]);

  return {
    readinessFlags,
    nextAction,
    loading,
    preparing,
    error,
    lastMessage,
    prepare,
    runIntelligence: (forceRefresh) => runAction("RUN_INTELLIGENCE", { force_refresh: forceRefresh }),
    qualify: (forceRefresh) => runAction("QUALIFY", { force_refresh: forceRefresh }),
    generatePitch: (channel, forceRefresh) => runAction("GENERATE_PITCH", { channel, force_refresh: forceRefresh }),
  };
}