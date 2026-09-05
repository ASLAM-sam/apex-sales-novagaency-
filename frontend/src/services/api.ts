import { apiClient } from "./apiClient";
import type {
  AcquisitionCandidate,
  AcquisitionImportResponse,
  AcquisitionSearchResponse,
  DashboardSummaryResponse,
  GetSalesLeadsParams,
  LeadTimelineResponse,
  Outreach,
  PrepareLeadResponse,
  ReadinessFlags,
  SalesActionResponse,
  SalesLeadDetailResponse,
  SalesLeadListResponse,
  TimelineEvent,
} from "../types/api";

export interface SearchAcquisitionParams {
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
}

export interface PrepareLeadActionResult {
  lead_id: string;
  readiness_flags: ReadinessFlags;
  next_recommended_action: string;
}

export interface TriggerSalesActionResult {
  action: string;
  success: boolean;
  lead_id: string;
  message: string;
  result: Record<string, unknown> | null;
}

export const api = {
  // Dashboard
  getDashboardSummary(): Promise<DashboardSummaryResponse> {
    return apiClient.get<DashboardSummaryResponse>("/api/v1/dashboard/summary");
  },

  // Acquisition
  searchAcquisition(params: SearchAcquisitionParams): Promise<AcquisitionSearchResponse> {
    return apiClient.post<AcquisitionSearchResponse>("/api/v1/acquisition/search", {
      source: params.source || "manual",
      query: params.query || undefined,
      category: params.category || undefined,
      city: params.city || undefined,
      state: params.state || undefined,
      country: params.country || undefined,
      limit: params.limit || 20,
      manual_candidates: params.manual_candidates
        ? params.manual_candidates.map((c) => ({
            name: c.name,
            website: c.website,
            phone: c.phone,
            email: c.email,
            address: c.address,
            city: c.city,
            state: c.state,
            country: c.country,
            category: c.category,
            source_name: c.source_name ?? "manual",
            source_id: c.source_id,
          }))
        : undefined,
    });
  },

  importCandidates(candidates: AcquisitionCandidate[]): Promise<AcquisitionImportResponse> {
    return apiClient.post<AcquisitionImportResponse>("/api/v1/acquisition/import", {
      candidates: candidates.map((cand) => ({
        name: cand.name,
        website: cand.website || undefined,
        phone: cand.phone || undefined,
        email: cand.email || undefined,
        address: cand.address || undefined,
        city: cand.city || undefined,
        state: cand.state || undefined,
        country: cand.country || undefined,
        category: cand.category || undefined,
        source_name: cand.source || "manual",
      })),
    });
  },

  // Sales Workspace Leads
  getSalesLeads(params: GetSalesLeadsParams = {}): Promise<SalesLeadListResponse> {
    const searchParams = new URLSearchParams();
    if (params.lead_status) searchParams.append("lead_status", params.lead_status);
    if (params.pipeline_stage) searchParams.append("pipeline_stage", params.pipeline_stage);
    if (params.min_score !== undefined) searchParams.append("min_score", params.min_score.toString());
    if (params.max_score !== undefined) searchParams.append("max_score", params.max_score.toString());
    if (params.service_type) searchParams.append("service_type", params.service_type);
    if (params.city) searchParams.append("city", params.city);
    if (params.category) searchParams.append("category", params.category);
    if (params.lead_source) searchParams.append("lead_source", params.lead_source);
    if (params.verification_status) searchParams.append("verification_status", params.verification_status);
    if (params.has_website !== undefined) searchParams.append("has_website", params.has_website.toString());
    if (params.has_audit !== undefined) searchParams.append("has_audit", params.has_audit.toString());
    if (params.has_pitch !== undefined) searchParams.append("has_pitch", params.has_pitch.toString());
    if (params.sort_by) searchParams.append("sort_by", params.sort_by);
    if (params.page !== undefined) searchParams.append("page", params.page.toString());
    if (params.page_size !== undefined) searchParams.append("page_size", params.page_size.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/sales/leads${queryString ? `?${queryString}` : ""}`;
    return apiClient.get<SalesLeadListResponse>(endpoint);
  },

  getSalesLeadDetail(leadId: string): Promise<SalesLeadDetailResponse> {
    return apiClient.get<SalesLeadDetailResponse>(`/api/v1/sales/leads/${leadId}`);
  },

  getSalesLeadTimeline(leadId: string): Promise<LeadTimelineResponse> {
    return apiClient.get<LeadTimelineResponse>(`/api/v1/sales/leads/${leadId}/timeline`);
  },

  prepareSalesLeadAction(leadId: string): Promise<PrepareLeadActionResult> {
    return apiClient.post<PrepareLeadActionResult>(`/api/v1/sales/leads/${leadId}/prepare`);
  },

  triggerSalesLeadAction(
    leadId: string,
    actionType: "RUN_INTELLIGENCE" | "QUALIFY" | "GENERATE_PITCH",
    options?: { channel?: "EMAIL" | "WHATSAPP" | "MANUAL"; force_refresh?: boolean },
  ): Promise<TriggerSalesActionResult> {
    const body: Record<string, unknown> = {};
    if (options?.channel) body.channel = options.channel;
    if (options?.force_refresh !== undefined) body.force_refresh = options.force_refresh;
    return apiClient.post<TriggerSalesActionResult>(
      `/api/v1/sales/leads/${leadId}/actions/${actionType}`,
      body,
    );
  },

  updateOutreachDraft(
    outreachId: string,
    updates: { subject?: string; body?: string },
  ): Promise<Outreach> {
    return apiClient.patch<Outreach>(`/api/v1/outreach/${outreachId}`, updates);
  },
};

// Re-export commonly used types for Wave B convenience.
export type {
  AcquisitionCandidate,
  AcquisitionImportResponse,
  AcquisitionSearchResponse,
  DashboardSummaryResponse,
  LeadTimelineResponse,
  Outreach,
  PrepareLeadResponse,
  ReadinessFlags,
  SalesActionResponse,
  SalesLeadDetailResponse,
  SalesLeadListResponse,
  TimelineEvent,
};