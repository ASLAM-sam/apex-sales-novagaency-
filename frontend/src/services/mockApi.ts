import { analytics, campaigns, conversations, leads } from "../data/mockData";
import { delay } from "../lib/utils";
import type { Campaign, ContactState, Lead } from "../types";

export interface LeadSearchParams {
  location: string;
  industries: string[];
  opportunities: string[];
  minimumRating: number;
  minimumReviews: number;
  count: number;
}

export async function findLeads(params: LeadSearchParams): Promise<Lead[]> {
  await delay(450);
  return leads
    .filter((lead) => (params.location && params.location !== "Any" ? lead.location === params.location : true))
    .filter((lead) =>
      params.industries.length
        ? params.industries.some((industry) => lead.industry.includes(industry.replace(/s$/, "")) || lead.industry === industry)
        : true,
    )
    .filter((lead) =>
      params.opportunities.length && !params.opportunities.includes("Any Opportunity")
        ? params.opportunities.includes(lead.websiteState)
        : true,
    )
    .filter((lead) => lead.rating >= params.minimumRating && lead.reviews >= params.minimumReviews)
    .slice(0, params.count);
}

export async function getLead(id: string) {
  await delay(120);
  return leads.find((lead) => lead.id === id) ?? leads[0];
}

export async function analyzeLead(id: string) {
  await delay(250);
  return getLead(id);
}

export async function generatePitch(lead: Lead, tone = "Professional", type = "WhatsApp") {
  await delay(350);
  const opener = type === "Email" ? `Subject: Website idea for ${lead.name}\n\nHi,` : "Hi,";
  return `${opener} I came across ${lead.name} while looking at ${lead.industry.toLowerCase()}s in ${lead.location}.\n\nI noticed you already have a strong Google presence with ${lead.rating} stars and ${lead.reviews} reviews, but the current online experience shows a clear opportunity: ${lead.opportunity.toLowerCase()}.\n\nI build modern websites for businesses like yours that make it easier for customers to understand services, trust the business, and take action quickly.\n\nI had a few ${tone.toLowerCase()} ideas for how ${lead.name} could look online. Would you be open to seeing a quick example?`;
}

export async function sendWhatsApp() {
  await delay(180);
  return { simulated: true };
}

export async function sendEmail() {
  await delay(180);
  return { simulated: true };
}

export async function getConversations() {
  await delay(120);
  return conversations;
}

export async function getAnalytics() {
  await delay(120);
  return analytics;
}

export async function updateLeadStatus(leadList: Lead[], id: string, status: ContactState) {
  await delay(120);
  return leadList.map((lead) =>
    lead.id === id
      ? { ...lead, status, lastAction: `Moved to ${status}`, nextAction: status === "Contacted" ? "Wait for reply" : "Follow up" }
      : lead,
  );
}

export async function getCampaigns(): Promise<Campaign[]> {
  await delay(120);
  return campaigns;
}
