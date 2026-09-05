import type {
  AcquisitionCandidate,
  AcquisitionCandidateInput,
  AcquisitionSearchResponse,
  ApiError,
  DashboardSummaryResponse,
  Outreach,
  Qualification,
  ReadinessFlags,
  SalesActionResponse,
  SalesLeadDetailResponse,
  SalesLeadSummary,
  TimelineEvent,
} from "../types/api";
import type {
  ContactState,
  Lead,
  LeadQuality,
  WebsiteState,
} from "../types";

// ---------------------------------------------------------------------------
// Status mapping helpers (shared)
// ---------------------------------------------------------------------------

function toTitleCase(input: string): string {
  if (!input) return "";
  const normalized = input.replace(/[_-]+/g, " ").trim().toLowerCase();
  return normalized
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function leadStatusToContactState(status: string): ContactState {
  switch (status.toUpperCase()) {
    case "NEW":
      return "New";
    case "RESEARCHING":
      return "Researched";
    case "QUALIFIED":
      return "Qualified";
    case "CONTACTED":
      return "Contacted";
    case "REPLIED":
      return "Replied";
    case "INTERESTED":
      return "Interested";
    case "FOLLOW_UP":
      return "Qualified";
    case "CONVERTED":
      return "Won";
    case "NOT_INTERESTED":
      return "Lost";
    case "INVALID":
      return "Lost";
    case "LOST":
      return "Lost";
    case "DO_NOT_CONTACT":
      return "Lost";
    default:
      return "New";
  }
}

function scoreToQuality(score: number): LeadQuality {
  if (score >= 80) return "Hot";
  if (score >= 60) return "Good";
  return "Maybe";
}

function websiteStateFor(hasWebsite: boolean, hasAudit: boolean): WebsiteState {
  if (!hasWebsite) return "No website";
  return hasAudit ? "Weak conversion" : "Outdated website";
}

// ---------------------------------------------------------------------------
// Date formatting helper
// ---------------------------------------------------------------------------

export function formatDate(iso?: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Sales lead list adapter
// ---------------------------------------------------------------------------

export function salesLeadSummaryToLeadItem(summary: SalesLeadSummary): Lead {
  const score = summary.qualification_score ?? 0;
  const status = leadStatusToContactState(summary.lead_status);

  return {
    id: summary.lead_id,
    name: summary.business_name,
    industry: summary.category ?? "General Business",
    location: summary.city ?? "Not Specified",
    score,
    quality: scoreToQuality(score),
    rating: 0,
    reviews: 0,
    websiteState: websiteStateFor(summary.has_website, summary.has_audit),
    opportunity: summary.has_website
      ? "Online experience & conversion optimization"
      : "Missing dedicated business website",
    phone: summary.phone ?? "",
    email: summary.email ?? "",
    website: summary.website ?? null,
    instagram: "",
    googleListing: summary.verification_status
      ? `Verification: ${toTitleCase(summary.verification_status)}`
      : "Unverified",
    address: summary.city ?? "",
    status,
    value: "$1,500 - $3,000",
    lastAction: `Status: ${toTitleCase(summary.lead_status)}`,
    nextAction: summary.has_pitch ? "Send Outreach Draft" : "Qualify / Generate Pitch",
    foundAt: formatDate(summary.created_at) || "Recently",
    overview: `Lead record for ${summary.business_name}.`,
    reasons: [
      summary.has_website ? "Has existing domain" : "Needs website creation",
      summary.verification_status
        ? `Verification: ${toTitleCase(summary.verification_status)}`
        : "Unverified status",
      score > 0 ? `Qualification Score: ${score}` : "Needs AI qualification",
    ],
    competitors: [],
    conversationState: summary.has_pitch ? "Draft ready" : "Unread",
  };
}

// ---------------------------------------------------------------------------
// Sales lead detail adapter
// ---------------------------------------------------------------------------

function readStringField(source: unknown, keys: string[]): string | null {
  if (!source || typeof source !== "object") return null;
  const record = source as Record<string, unknown>;
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.length > 0) return value;
  }
  return null;
}

function readNumberField(source: unknown, keys: string[]): number | null {
  if (!source || typeof source !== "object") return null;
  const record = source as Record<string, unknown>;
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "number" && !Number.isNaN(value)) return value;
  }
  return null;
}

function readIssuesArray(source: unknown): string[] {
  if (!source || typeof source !== "object") return [];
  const record = source as Record<string, unknown>;
  const candidates: unknown[] = [
    record.issues,
    record.findings,
    record.problems,
  ];
  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      const titles = candidate
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object") {
            const obj = item as Record<string, unknown>;
            const title = obj.title ?? obj.name ?? obj.description ?? obj.issue;
            if (typeof title === "string") return title;
          }
          return null;
        })
        .filter((item): item is string => typeof item === "string");
      if (titles.length > 0) return titles;
    }
  }
  return [];
}

function deriveWebsiteState(
  business: { website: string | null },
  audit: Record<string, unknown> | null,
): WebsiteState {
  if (!business.website) return "No website";
  const issues = readIssuesArray(audit);
  return issues.length > 0 ? "Weak conversion" : "Outdated website";
}

function deriveOverview(
  detail: SalesLeadDetailResponse,
  businessName: string,
  category: string | null,
): string {
  const researchDescription = readStringField(detail.latest_research, [
    "business_summary",
    "description",
    "summary",
  ]);
  if (researchDescription) return researchDescription;
  return `Lead record for ${businessName} in ${category ?? "general business"}.`;
}

function deriveReasons(detail: SalesLeadDetailResponse, qualification: Qualification): string[] {
  const reason = qualification.qualification_reason;
  if (reason && reason.length > 0) return [reason];
  return [
    detail.business.website ? "Has registered website domain" : "No active website domain found",
    detail.business.phone ? "Phone contact available" : "No phone contact found",
    detail.business.email ? "Email address detected" : "No direct email address found",
  ];
}

function deriveCompetitors(audit: Record<string, unknown> | null): Lead["competitors"] {
  if (!audit || typeof audit !== "object") return [];
  const record = audit as Record<string, unknown>;
  const list = record.competitors ?? record.competitors_analyzed;
  if (!Array.isArray(list)) return [];
  return list
    .map((item): Lead["competitors"][number] | null => {
      if (!item || typeof item !== "object") return null;
      const obj = item as Record<string, unknown>;
      const name = typeof obj.name === "string" ? obj.name : null;
      if (!name) return null;
      return {
        name,
        website: Boolean(obj.has_website ?? obj.website),
        booking: Boolean(obj.has_booking ?? obj.booking),
      };
    })
    .filter((item): item is Lead["competitors"][number] => item !== null);
}

export function salesLeadDetailToLead(detail: SalesLeadDetailResponse): Lead {
  const { business, qualification, latest_website_audit, all_outreach } = detail;
  const score =
    readNumberField(detail.pipeline_state, ["qualification_score"]) ??
    qualification.qualification_score ??
    0;

  const status = leadStatusToContactState(detail.pipeline_state.lead_status);
  const websiteState = deriveWebsiteState(business, latest_website_audit);
  const explicitReason = readStringField(qualification, ["qualification_reason"]);

  return {
    id: detail.lead.id,
    name: business.name,
    industry: business.category ?? "General Business",
    location: [business.city, business.state].filter(Boolean).join(", ") || "Location Not Specified",
    score,
    quality: scoreToQuality(score),
    rating: 0,
    reviews: 0,
    websiteState,
    opportunity:
      explicitReason ??
      (business.website
        ? "Website optimization and lead capture"
        : "High potential for new website development"),
    phone: business.phone ?? "",
    email: business.email ?? "",
    website: business.website ?? null,
    instagram: business.social_profiles?.instagram ?? "",
    googleListing: business.verification_status
      ? `Verification: ${toTitleCase(business.verification_status)}`
      : "Verified Business",
    address: [business.address, business.city, business.state].filter(Boolean).join(", ") || "",
    status,
    value: "$1,500 - $3,500",
    lastAction: detail.next_recommended_action
      ? `Next Step: ${toTitleCase(detail.next_recommended_action)}`
      : "Ready for action",
    nextAction: detail.next_recommended_action || "Run Intelligence",
    foundAt: formatDate(detail.lead.created_at) || "Recently",
    overview: deriveOverview(detail, business.name, business.category),
    reasons: deriveReasons(detail, qualification),
    competitors: deriveCompetitors(latest_website_audit),
    conversationState: all_outreach.length > 0 ? "Draft ready" : "Unread",
  };
}

// ---------------------------------------------------------------------------
// Dashboard summary adapter
// ---------------------------------------------------------------------------

export interface DashboardKpi {
  label: string;
  value: number;
  trend: string;
}

export function dashboardToKpis(summary: DashboardSummaryResponse): DashboardKpi[] {
  return [
    { label: "New Leads", value: summary.new_leads, trend: "today" },
    { label: "Hot Leads", value: summary.high_opportunity_leads, trend: "scored >= 80" },
    { label: "Contacted", value: summary.contacted_leads, trend: "in pipeline" },
    { label: "Replies", value: summary.replied_leads, trend: "engaged" },
    { label: "Interested", value: summary.interested_leads, trend: "warm" },
    { label: "Meetings", value: summary.follow_up_leads, trend: "scheduled" },
  ];
}

// ---------------------------------------------------------------------------
// Acquisition candidate adapter
// ---------------------------------------------------------------------------

export interface AcquisitionCandidateDisplay {
  name: string;
  website: string | null;
  phone: string | null;
  email: string | null;
  city: string | null;
  category: string | null;
  source: string;
  already_exists: boolean;
  existing_business_id: string | null;
  existing_lead_id: string | null;
  statusLabel: "NEW" | "ALREADY_EXISTS" | "ALREADY_IMPORTED";
}

export function acquisitionCandidateToDisplay(
  candidate: AcquisitionCandidate,
): AcquisitionCandidateDisplay {
  const statusLabel: AcquisitionCandidateDisplay["statusLabel"] = candidate.already_exists
    ? candidate.existing_lead_id
      ? "ALREADY_IMPORTED"
      : "ALREADY_EXISTS"
    : "NEW";

  return {
    name: candidate.name,
    website: candidate.website ?? null,
    phone: candidate.phone ?? null,
    email: candidate.email ?? null,
    city: candidate.city ?? candidate.location?.city ?? null,
    category: candidate.category ?? null,
    source: candidate.source,
    already_exists: candidate.already_exists,
    existing_business_id: candidate.existing_business_id ?? null,
    existing_lead_id: candidate.existing_lead_id ?? null,
    statusLabel,
  };
}

// ---------------------------------------------------------------------------
// Timeline event adapter
// ---------------------------------------------------------------------------

export type TimelineIconName =
  | "Search"
  | "Check"
  | "Sparkles"
  | "Flame"
  | "Mail"
  | "MessageCircle"
  | "Phone"
  | "ClipboardList"
  | "Gauge"
  | "Bot";

export interface TimelineEventDisplay {
  type: string;
  title: string;
  description: string | null;
  timestamp: string;
  iconName: TimelineIconName;
}

export function timelineEventToDisplay(event: TimelineEvent): TimelineEventDisplay {
  const type = (event.event_type ?? "").toUpperCase();
  let iconName: TimelineIconName = "Sparkles";

  if (type.includes("SEARCH") || type.includes("DISCOVER")) iconName = "Search";
  else if (type.includes("VERIF")) iconName = "Check";
  else if (type.includes("QUALIF")) iconName = "Flame";
  else if (type.includes("AUDIT")) iconName = "Gauge";
  else if (type.includes("PITCH")) iconName = "Sparkles";
  else if (type.includes("EMAIL") || type.includes("SENT")) iconName = "Mail";
  else if (type.includes("WHATSAPP") || type.includes("REPLY") || type.includes("CONVERS"))
    iconName = "MessageCircle";
  else if (type.includes("CALL") || type.includes("PHONE")) iconName = "Phone";
  else if (type.includes("PIPELINE") || type.includes("STATUS") || type.includes("STAGE"))
    iconName = "ClipboardList";
  else if (type.includes("RESEARCH")) iconName = "Bot";

  return {
    type: event.event_type,
    title: event.title,
    description: event.description ?? null,
    timestamp: event.timestamp,
    iconName,
  };
}

// ---------------------------------------------------------------------------
// Action / error helpers
// ---------------------------------------------------------------------------

export function describeApiError(error: unknown): string {
  if (error instanceof Error) {
    const maybeApi = error as ApiError;
    if (maybeApi.status === 0) {
      return "Unable to reach the Apex Sales AI backend. Verify the API is running.";
    }
    if (maybeApi.status >= 500) {
      return `Server error (${maybeApi.status}). ${error.message}`;
    }
    return error.message;
  }
  return "An unexpected error occurred.";
}

export type {
  AcquisitionCandidate,
  AcquisitionCandidateInput,
  AcquisitionSearchResponse,
  Outreach,
  Qualification,
  ReadinessFlags,
  SalesActionResponse,
  SalesLeadDetailResponse,
  SalesLeadSummary,
  TimelineEvent,
};