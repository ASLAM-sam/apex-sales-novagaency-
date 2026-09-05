import type { Campaign, Conversation, Lead } from "../types";

const industries = [
  "Dental Clinic",
  "Interior Designers",
  "Restaurant",
  "Fitness Studio",
  "Salon",
  "Medical Clinic",
  "Real Estate",
  "Hotel",
  "Law Firm",
  "Coaching Institute",
  "Manufacturer",
  "Event Company",
  "Architects",
  "Photographers",
  "Consultants",
];

const locations = ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai", "Pune"];
const states = ["No website", "Outdated website", "Poor mobile experience", "Poor SEO", "No online booking", "Weak conversion"] as const;
const names = [
  "ABC Dental Clinic",
  "UrbanNest Interiors",
  "Royal Table Restaurant",
  "PrimeFit Studio",
  "GlowCraft Salon",
  "CityCare Medical",
  "MetroSquare Realty",
  "BlueVista Hotel",
  "LexBridge Law",
  "BrightPath Academy",
  "Veda Manufacturing",
  "Eventory Studios",
  "ArchiLine Design",
  "FrameWorks Photo",
  "ScaleWise Consulting",
  "Lotus Dental Lounge",
  "Spice Meridian",
  "NorthPeak Gym",
  "CasaForm Interiors",
  "Nova Skin Clinic",
  "EstateGrid Advisors",
  "HarborStay Suites",
  "JusticePoint Legal",
  "LearnEdge Institute",
  "MakersHub India",
  "Pulse Events",
  "Studio Axis",
  "LensLab Weddings",
  "GrowthMint Advisors",
  "ZenBite Cafe",
];

export const leads: Lead[] = names.map((name, index) => {
  const score = [94, 89, 86, 82, 78, 91, 74, 84, 69, 87][index % 10] - Math.floor(index / 10) * 2;
  const websiteState = states[index % states.length];
  const industry = industries[index % industries.length];
  const location = locations[index % locations.length];
  const reviews = 386 - index * 7 > 58 ? 386 - index * 7 : 58 + index * 3;
  return {
    id: `lead-${index + 1}`,
    name,
    industry,
    location,
    score,
    quality: score >= 84 ? "Hot" : score >= 74 ? "Good" : "Maybe",
    rating: Number((4.9 - (index % 7) * 0.1).toFixed(1)),
    reviews,
    websiteState,
    opportunity:
      websiteState === "No website"
        ? "Website + online appointment flow"
        : websiteState === "No online booking"
          ? "Booking conversion upgrade"
          : websiteState === "Poor mobile experience"
            ? "Mobile-first redesign"
            : "Website redesign + SEO",
    phone: `+91 9000${String(100000 + index * 913).slice(0, 6)}`,
    email: `hello${index + 1}@demo-${name.toLowerCase().replaceAll(" ", "-").replaceAll(".", "")}.test`,
    website: websiteState === "No website" ? null : `https://demo-${index + 1}.example`,
    instagram: `@${name.toLowerCase().replace(/[^a-z]/g, "").slice(0, 18)}`,
    googleListing: "Demo Google Business listing",
    address: `${12 + index}, Market Road, ${location}`,
    status: (["New", "Researched", "Qualified", "Contacted", "Replied", "Interested", "Meeting", "Proposal"] as const)[index % 8],
    value: `₹${35 + (index % 7) * 5}K`,
    lastAction: ["Lead discovered", "AI research completed", "Pitch generated", "Email prepared", "Marked Interested"][index % 5],
    nextAction: ["Research", "Generate pitch", "Send pitch", "Follow up", "Schedule meeting"][index % 5],
    foundAt: ["09:32", "09:45", "10:02", "10:18", "11:05"][index % 5],
    overview: `${name} is an active ${industry.toLowerCase()} in ${location} with visible demand signals and a clear website-development opportunity.`,
    reasons: [
      "Strong Google presence",
      `${reviews} customer reviews`,
      "Active business signals",
      websiteState === "No website" ? "No dedicated website" : "Current website experience needs work",
      "Nearby competitors have stronger conversion paths",
    ],
    competitors: [
      { name, website: websiteState !== "No website", booking: false },
      { name: `Prime ${industry.split(" ")[0]}`, website: true, booking: true },
      { name: `City ${industry.split(" ")[0]}`, website: true, booking: true },
      { name: `Elite ${industry.split(" ")[0]}`, website: true, booking: index % 2 === 0 },
    ],
    conversationState: (["Unread", "Waiting", "Draft ready", "Follow-up due", "Closed"] as const)[index % 5],
  };
});

export const conversations: Conversation[] = leads.slice(0, 9).map((lead, index) => ({
  id: `conv-${lead.id}`,
  leadId: lead.id,
  channel: (["WhatsApp", "Email", "Instagram"] as const)[index % 3],
  messages: [
    { from: "You", text: `Hi, I had a quick website idea for ${lead.name}.`, time: "10:12" },
    { from: "Client", text: index % 2 === 0 ? "How much does it cost?" : "Can you share more details?", time: "10:24" },
  ],
  suggestedReply: `Absolutely. Based on your current online presence, a focused website for ${lead.name} could start with service pages, trust signals, and a clear contact path. I can share a quick demo direction first.`,
}));

export const campaigns: Campaign[] = leads.slice(0, 12).map((lead, index) => ({
  id: `campaign-${lead.id}`,
  leadId: lead.id,
  channel: (["WhatsApp", "Email", "WhatsApp"] as const)[index % 3],
  message: index % 3 === 0 ? "Personalized pitch" : index % 3 === 1 ? "Website redesign pitch" : "Follow-up",
  status: (["Ready to send", "Sent", "Follow-up due", "Draft", "Reply received"] as const)[index % 5],
  sent: index % 2 === 0 ? "Not sent" : `${index + 1}h ago`,
  reply: index % 5 === 4 ? "Positive" : "-",
  nextFollowUp: index % 3 === 2 ? "Tomorrow" : "Queued",
}));

export const analytics = {
  kpis: [
    ["Leads Found", "1,248"],
    ["Qualified", "284"],
    ["Contacted", "142"],
    ["Replies", "31"],
    ["Interested", "14"],
    ["Meetings", "6"],
    ["Won", "2"],
  ],
  funnel: [
    { stage: "Found", value: 1248 },
    { stage: "Qualified", value: 284 },
    { stage: "Contacted", value: 142 },
    { stage: "Replied", value: 31 },
    { stage: "Interested", value: 14 },
    { stage: "Meeting", value: 6 },
    { stage: "Won", value: 2 },
  ],
  sources: [
    { name: "Google", value: 46 },
    { name: "Directories", value: 22 },
    { name: "Referrals", value: 11 },
    { name: "Social", value: 14 },
    { name: "Manual", value: 7 },
  ],
  industries: [
    { name: "Restaurants", replies: 11, contacted: 42 },
    { name: "Dental", replies: 8, contacted: 25 },
    { name: "Real Estate", replies: 5, contacted: 19 },
    { name: "Interior", replies: 4, contacted: 18 },
    { name: "Clinics", replies: 3, contacted: 15 },
  ],
};
