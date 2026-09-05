import type { LucideIcon } from "lucide-react";

export type Page =
  | "command"
  | "find"
  | "hot"
  | "leads"
  | "leadDetail"
  | "pitch"
  | "conversations"
  | "outreach"
  | "pipeline"
  | "analytics"
  | "settings";

export type WebsiteState =
  | "No website"
  | "Outdated website"
  | "Poor mobile experience"
  | "Poor SEO"
  | "No online booking"
  | "No online ordering"
  | "Weak conversion"
  | "Website redesign";

export type LeadQuality = "Hot" | "Good" | "Maybe";
export type ContactState = "New" | "Researched" | "Qualified" | "Contacted" | "Replied" | "Interested" | "Meeting" | "Proposal" | "Won" | "Lost";
export type Channel = "WhatsApp" | "Email" | "Instagram";

export interface Lead {
  id: string;
  name: string;
  industry: string;
  location: string;
  score: number;
  quality: LeadQuality;
  rating: number;
  reviews: number;
  websiteState: WebsiteState;
  opportunity: string;
  phone: string;
  email: string;
  website: string | null;
  instagram: string;
  googleListing: string;
  address: string;
  status: ContactState;
  value: string;
  lastAction: string;
  nextAction: string;
  foundAt: string;
  overview: string;
  reasons: string[];
  competitors: Array<{ name: string; website: boolean; booking: boolean }>;
  conversationState: "Unread" | "Waiting" | "Draft ready" | "Follow-up due" | "Closed";
}

export interface Conversation {
  id: string;
  leadId: string;
  channel: Channel;
  messages: Array<{ from: "You" | "Client" | "AI"; text: string; time: string }>;
  suggestedReply: string;
}

export interface Campaign {
  id: string;
  leadId: string;
  channel: Channel;
  message: string;
  status: "Draft" | "Ready to send" | "Scheduled" | "Sent" | "Reply received" | "Follow-up due";
  sent: string;
  reply: string;
  nextFollowUp: string;
}

export interface ToastMessage {
  id: number;
  tone: "success" | "info" | "error";
  title: string;
}

export interface NavItem {
  page: Page;
  label: string;
  icon: LucideIcon;
}
