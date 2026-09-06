/**
 * Apex Sales AI — Backend API type definitions.
 *
 * These types model the REAL response/request shapes exposed by the FastAPI
 * backend (see `backend/app/sales/schemas.py`, `backend/app/schemas/*.py`,
 * and `backend/app/acquisition/schemas.py`). They are the single source of
 * truth for every service-layer call in the frontend.
 *
 * No `any` is used in the public surface. Truly dynamic payloads use
 * `unknown` or `Record<string, unknown>` to force consumers to narrow them.
 */

// ---------------------------------------------------------------------------
// Shared / envelope types
// ---------------------------------------------------------------------------

export interface PaginationMetadata {
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export type ApiErrorData = unknown;

// `ApiError` mirrors the shape thrown by `apiClient` so callers can narrow
// on `instanceof ApiError` for friendly messages. Implementation lives in
// `services/apiClient.ts`.
export type ApiError = Error & {
  name: "ApiError";
  status: number;
  data: ApiErrorData;
};

// ---------------------------------------------------------------------------
// Core domain types (derived from backend schemas)
// ---------------------------------------------------------------------------

export type LeadStatusCode =
  | "NEW"
  | "RESEARCHING"
  | "QUALIFIED"
  | "CONTACTED"
  | "REPLIED"
  | "INTERESTED"
  | "FOLLOW_UP"
  | "CONVERTED"
  | "NOT_INTERESTED"
  | "INVALID"
  | "LOST"
  | "DO_NOT_CONTACT";

export type PipelineStageCode =
  | "NEW"
  | "RESEARCH"
  | "QUALIFIED"
  | "PITCH_READY"
  | "OUTREACH"
  | "CONVERSATION"
  | "PROPOSAL"
  | "NEGOTIATION"
  | "WON"
  | "LOST";

export type OutreachChannelCode = "EMAIL" | "WHATSAPP" | "MANUAL" | "OTHER";
export type OutreachDirectionCode = "OUTBOUND" | "INBOUND";
export type OutreachMessageTypeCode =
  | "INITIAL_PITCH"
  | "FOLLOW_UP"
  | "REPLY"
  | "INTRODUCTION"
  | "PROPOSAL"
  | "OTHER";
export type OutreachStatusCode =
  | "DRAFT"
  | "READY"
  | "QUEUED"
  | "SENT"
  | "DELIVERED"
  | "FAILED"
  | "CANCELLED";

export interface SocialProfiles {
  instagram: string | null;
  facebook: string | null;
  linkedin: string | null;
  youtube: string | null;
  other: string[];
}

export interface Business {
  id: string;
  name: string;
  normalized_name: string | null;
  description: string | null;
  category: string | null;
  sub_category: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  website: string | null;
  normalized_domain: string | null;
  phone: string | null;
  normalized_phone: string | null;
  email: string | null;
  social_profiles: SocialProfiles;
  business_status: string;
  verification_status: string;
  created_at: string;
  updated_at: string;
}

export interface Qualification {
  is_genuine_business: boolean | null;
  has_contact_method: boolean | null;
  website_quality: number | null;
  website_need: number | null;
  service_fit: number | null;
  buying_signal: number | null;
  qualification_score: number | null;
  qualification_reason: string | null;
}

export interface LeadContact {
  name: string | null;
  first_name: string | null;
  last_name: string | null;
  role: string | null;
  email: string | null;
  phone: string | null;
  whatsapp: string | null;
  linkedin: string | null;
}

export interface Lead {
  id: string;
  business_id: string;
  contact: LeadContact;
  lead_source: string;
  lead_status: LeadStatusCode | string;
  pipeline_stage: PipelineStageCode | string;
  qualification: Qualification;
  score: number | null;
  service_opportunity: {
    primary_service: string;
    secondary_services: string[];
    opportunity_score: number | null;
    reason: string | null;
  } | null;
  evidence: Array<{
    type: string;
    description: string;
    source_url: string | null;
    observed_at: string;
    confidence: number | null;
  }>;
  last_contacted_at: string | null;
  next_follow_up_at: string | null;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface Outreach {
  id: string;
  lead_id: string;
  business_id: string;
  channel: OutreachChannelCode | string;
  direction: OutreachDirectionCode | string;
  message_type: OutreachMessageTypeCode | string;
  subject: string | null;
  message: string;
  generated_by: string | null;
  generation_id: string | null;
  status: OutreachStatusCode | string;
  sent_at: string | null;
  delivered_at: string | null;
  opened_at: string | null;
  replied_at: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Sales workspace responses
// ---------------------------------------------------------------------------

export interface DashboardSummaryResponse {
  total_businesses: number;
  total_leads: number;
  new_leads: number;
  qualified_leads: number;
  high_opportunity_leads: number;
  contacted_leads: number;
  replied_leads: number;
  interested_leads: number;
  follow_up_leads: number;
  converted_leads: number;
  lost_leads: number;
  draft_outreach_count: number;
}

export interface SalesLeadSummary {
  lead_id: string;
  business_id: string;
  business_name: string;
  website: string | null;
  phone: string | null;
  email: string | null;
  city: string | null;
  category: string | null;
  lead_status: string;
  pipeline_stage: string;
  qualification_score: number | null;
  qualification_status: string | null;
  primary_service: string | null;
  verification_status: string | null;
  has_website: boolean;
  has_audit: boolean;
  has_pitch: boolean;
  created_at: string;
  next_follow_up_at: string | null;
}

export interface SalesLeadListResponse {
  leads: SalesLeadSummary[];
  pagination: PaginationMetadata;
}

export interface ReadinessFlags {
  can_verify: boolean;
  can_research: boolean;
  can_audit: boolean;
  can_qualify: boolean;
  can_generate_pitch: boolean;
  has_email: boolean;
  has_phone: boolean;
  has_website: boolean;
  has_draft: boolean;
  is_do_not_contact: boolean;
}

export interface ContactEmailDraft {
  email: string;
  subject: string;
  body: string;
  outreach_id: string | null;
  status: string | null;
  is_available: boolean;
}

export interface ContactActionData {
  phone: string | null;
  email: string | null;
  website: string | null;
  whatsapp_available: boolean;
  whatsapp_url: string | null;
  email_available: boolean;
  email_draft: ContactEmailDraft | null;
  latest_pitch: Record<string, unknown> | null;
  pitch_channel: string | null;
  pitch_status: string | null;
}

export interface SalesLeadPipelineState {
  lead_status: string;
  pipeline_stage: string;
  qualification_score: number | null;
  verification_status: string;
}

export interface SalesLeadDetailResponse {
  lead: Lead;
  business: Business;
  latest_research: Record<string, unknown> | null;
  latest_verification: string | null;
  latest_website_audit: Record<string, unknown> | null;
  qualification: Qualification;
  latest_outreach: Outreach | null;
  all_outreach: Outreach[];
  conversation_metadata: Record<string, unknown> | null;
  pipeline_state: SalesLeadPipelineState;
  readiness_flags: ReadinessFlags;
  next_recommended_action: string;
  contact_action_data: ContactActionData;
}

export interface TimelineEvent {
  event_type: string;
  title: string;
  description: string | null;
  timestamp: string;
  metadata: Record<string, unknown> | null;
}

export interface LeadTimelineResponse {
  lead_id: string;
  events: TimelineEvent[];
}

export interface PrepareLeadResponse {
  lead_id: string;
  readiness_flags: ReadinessFlags;
  next_recommended_action: string;
}

export interface SalesActionResponse {
  success: boolean;
  action: string;
  lead_id: string;
  message: string;
  result: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// Acquisition types
// ---------------------------------------------------------------------------

export interface AcquisitionLocation {
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
}

export interface AcquisitionCandidate {
  candidate_id: string;
  name: string;
  website: string | null;
  phone: string | null;
  email: string | null;
  location: AcquisitionLocation | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  category: string | null;
  description: string | null;
  source: string;
  already_exists: boolean;
  existing_business_id: string | null;
  existing_lead_id: string | null;
  qualification_state: string | null;
  raw_data: Record<string, unknown> | null;
}

export interface AcquisitionSearchParams {
  query?: string;
  category?: string;
  city?: string;
  state?: string;
  country?: string;
  website_required?: boolean;
  limit?: number;
  source?: string;
  manual_candidates?: AcquisitionCandidateInput[];
}

export interface AcquisitionSearchResponse {
  candidates: AcquisitionCandidate[];
  total: number;
  source: string;
}

export interface AcquisitionCandidateInput {
  name?: string | null;
  website?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  category?: string | null;
  description?: string | null;
  social_profiles?: Record<string, unknown> | null;
  source_name?: string | null;
  source_id?: string | null;
  raw_data?: Record<string, unknown> | null;
}

/**
 * Qualification / intelligence result payloads returned by the sales action
 * endpoints. These mirror the backend response schemas exactly:
 *  - `app/qualification/schemas.py::LeadQualificationResponse`
 *  - `app/schemas/intelligence.py::LeadIntelligenceResponse`
 */
export interface QualificationRecommendedService {
  service: string;
  reason: string;
  confidence: number;
  evidence: string[];
}

export interface QualificationOutput {
  qualification_score: number;
  qualification_label: string;
  confidence: number;
  recommended_services: QualificationRecommendedService[];
  reasons: string[];
  positive_signals: string[];
  negative_signals: string[];
  evidence: string[];
  risks: string[];
  summary: string;
}

export interface LeadQualificationResult {
  lead_id: string;
  business_id: string;
  business_name: string;
  qualification: QualificationOutput;
  run_id: string | null;
}

export interface IntelligenceVerificationResult {
  verification_status: string;
  business_exists_evidence: boolean;
  website_accessible: boolean;
  domain_matches: boolean;
  business_name_found: boolean;
  phone_present: boolean;
  email_present: boolean;
  notes: string | null;
}

export interface IntelligenceAuditResult {
  audit_id: string | null;
  website_exists: boolean;
  http_status: number | null;
  overall_score: number | null;
  total_issues: number;
  high_critical_issues: number;
  top_recommendation: string | null;
}

export interface LeadIntelligenceResult {
  lead_id: string;
  business_id: string;
  business_name: string;
  processing_status: string;
  verification: IntelligenceVerificationResult;
  research: Record<string, unknown> | null;
  website_audit: IntelligenceAuditResult | null;
  run_id: string | null;
}

export interface AcquisitionImportRequest {
  candidates: AcquisitionCandidateInput[];
}

export interface AcquisitionImportResponse {
  imported: number;
  already_exists: number;
  duplicates: number;
  invalid: number;
  failed: number;
  business_ids: string[];
  lead_ids: string[];
  details: Array<Record<string, unknown>>;
}

// ---------------------------------------------------------------------------
// Sales leads listing query parameters
// ---------------------------------------------------------------------------

export interface GetSalesLeadsParams {
  lead_status?: string;
  pipeline_stage?: string;
  min_score?: number;
  max_score?: number;
  service_type?: string;
  city?: string;
  category?: string;
  lead_source?: string;
  verification_status?: string;
  has_website?: boolean;
  has_audit?: boolean;
  has_pitch?: boolean;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}