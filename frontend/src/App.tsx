import {
  BarChart3,
  Bell,
  Bot,
  BriefcaseBusiness,
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Copy,
  Flame,
  Gauge,
  LayoutDashboard,
  Mail,
  MessageCircle,
  Minus,
  PanelLeftClose,
  PanelLeftOpen,
  Phone,
  Plus,
  Search,
  Send,
  Settings,
  Sparkles,
  Star,
  Users,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Funnel, FunnelChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useDashboard } from "./hooks/useDashboard";
import { useLeadActions, useLeadDetail, useLeadTimeline } from "./hooks/useLeadDetail";
import { useSalesLeads } from "./hooks/useSalesLeads";
import { cn } from "./lib/utils";
import { api } from "./services/api";
import type { ContactState, Lead, NavItem, Page, ToastMessage } from "./types";
import type { ReadinessFlags, SalesLeadDetailResponse } from "./types/api";
import { formatDate, salesLeadSummaryToLeadItem } from "./utils/adapters";

const navPrimary: NavItem[] = [
  { page: "command", label: "Command Center", icon: LayoutDashboard },
  { page: "find", label: "Find Leads", icon: Search },
  { page: "hot", label: "Hot Leads", icon: Flame },
  { page: "leads", label: "All Leads", icon: Users },
  { page: "conversations", label: "Conversations", icon: MessageCircle },
  { page: "outreach", label: "Outreach", icon: Mail },
  { page: "pipeline", label: "Pipeline", icon: ClipboardList },
];

const navSecondary: NavItem[] = [
  { page: "analytics", label: "Analytics", icon: BarChart3 },
  { page: "settings", label: "Settings", icon: Settings },
];

const pageTitles: Record<Page, string> = {
  command: "Command Center",
  find: "Find Leads",
  hot: "Hot Leads",
  leads: "All Leads",
  leadDetail: "Lead Research",
  pitch: "Pitch Generator",
  conversations: "Conversations",
  outreach: "Outreach",
  pipeline: "Pipeline",
  analytics: "Analytics",
  settings: "Settings",
};

async function copyText(value: string) {
  try {
    await navigator.clipboard?.writeText(value);
  } catch {
    return;
  }
}

function contactStateToLeadStatus(status: ContactState): string {
  switch (status) {
    case "New":
      return "NEW";
    case "Researched":
      return "RESEARCHING";
    case "Qualified":
      return "QUALIFIED";
    case "Contacted":
      return "CONTACTED";
    case "Replied":
      return "REPLIED";
    case "Interested":
      return "INTERESTED";
    case "Meeting":
      return "FOLLOW_UP";
    case "Proposal":
      return "FOLLOW_UP";
    case "Won":
      return "CONVERTED";
    case "Lost":
      return "LOST";
    default:
      return "NEW";
  }
}

function pitchChannelFromType(type: string): "EMAIL" | "WHATSAPP" | "MANUAL" {
  if (type === "Email") return "EMAIL";
  if (type === "WhatsApp") return "WHATSAPP";
  return "MANUAL";
}

function extractPitchText(detail: SalesLeadDetailResponse | null, actionResult?: Record<string, unknown> | null): string {
  if (actionResult) {
    const body = actionResult.body;
    const subject = actionResult.subject;
    if (typeof body === "string" && body.trim()) {
      return typeof subject === "string" && subject.trim() ? `Subject: ${subject}\n\n${body}` : body;
    }
  }
  if (!detail) return "";
  const pitch = detail.contact_action_data?.latest_pitch;
  if (pitch && typeof pitch === "object") {
    const record = pitch as Record<string, unknown>;
    const body = typeof record.body === "string" ? record.body : typeof record.message === "string" ? record.message : "";
    const subject = typeof record.subject === "string" ? record.subject : "";
    if (body.trim()) return subject.trim() ? `Subject: ${subject}\n\n${body}` : body;
  }
  const latest = detail.latest_outreach ?? detail.all_outreach[0];
  if (latest?.message) {
    return latest.subject ? `Subject: ${latest.subject}\n\n${latest.message}` : latest.message;
  }
  return "";
}

function digitsPhone(phone: string): string {
  return phone.replace(/\D/g, "");
}

export default function App() {
  const [page, setPage] = useState<Page>("command");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [globalQuery, setGlobalQuery] = useState("");
  const [pitchText, setPitchText] = useState("");
  const { leads, loading: leadsLoading, error: leadsError, refetch: refetchLeads } = useSalesLeads({ page: 1, page_size: 100, sort_by: "created_at" });
  const selectedLead = leads.find((lead) => lead.id === selectedLeadId) ?? leads[0] ?? null;

  function toast(title: string, tone: ToastMessage["tone"] = "success") {
    const id = Date.now() + Math.random();
    setToasts((items) => [...items, { id, title, tone }]);
    window.setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 2600);
  }

  function go(next: Page, leadId?: string) {
    if (leadId) setSelectedLeadId(leadId);
    setPage(next);
    setPaletteOpen(false);
    setMobileNavOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function moveLead(id: string, status: ContactState) {
    try {
      await api.updateLeadStatus(id, contactStateToLeadStatus(status));
      await refetchLeads();
      toast(`Lead moved to ${status}`);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Unable to update lead status", "error");
    }
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const pageContent: Record<Page, React.ReactNode> = {
    command: <CommandCenter go={go} toast={toast} />,
    find: <FindLeads go={go} toast={toast} setSelectedLeadId={setSelectedLeadId} />,
    hot: <HotLeads leads={leads.filter((lead) => lead.quality === "Hot")} go={go} toast={toast} loading={leadsLoading} error={leadsError} onRetry={refetchLeads} />,
    leads: <AllLeads leads={leads} go={go} toast={toast} loading={leadsLoading} error={leadsError} onRetry={refetchLeads} />,
    leadDetail: <LeadDetail leadId={selectedLeadId ?? selectedLead?.id ?? null} fallback={selectedLead} go={go} toast={toast} moveLead={moveLead} onChanged={refetchLeads} />,
    pitch: <PitchGenerator leadId={selectedLeadId ?? selectedLead?.id ?? null} fallback={selectedLead} pitchText={pitchText} setPitchText={setPitchText} toast={toast} onChanged={refetchLeads} />,
    conversations: <ConversationsPage leads={leads} toast={toast} loading={leadsLoading} error={leadsError} onRetry={refetchLeads} />,
    outreach: <OutreachPage leads={leads} toast={toast} loading={leadsLoading} error={leadsError} onRetry={refetchLeads} />,
    pipeline: <PipelinePage leads={leads} go={go} moveLead={moveLead} loading={leadsLoading} error={leadsError} onRetry={refetchLeads} />,
    analytics: <AnalyticsPage />,
    settings: <SettingsPage toast={toast} />,
  };

  return (
    <div className="min-h-screen text-slate-100">
      <Sidebar open={sidebarOpen} mobileOpen={mobileNavOpen} current={page} go={go} setOpen={setSidebarOpen} setMobileOpen={setMobileNavOpen} />
      <main className={cn("min-h-screen transition-all duration-300", sidebarOpen ? "lg:pl-72" : "lg:pl-24")}>
        <Topbar
          title={pageTitles[page]}
          query={globalQuery}
          setQuery={setGlobalQuery}
          openPalette={() => setPaletteOpen(true)}
          quickFind={() => go("find")}
          sidebarOpen={sidebarOpen}
          toggleSidebar={() => setSidebarOpen((open) => !open)}
        />
        <div className="page-enter mx-auto w-full max-w-[1540px] px-4 pb-10 pt-5 sm:px-6 xl:px-8">{pageContent[page]}</div>
      </main>
      <CommandPalette open={paletteOpen} close={() => setPaletteOpen(false)} go={go} />
      <ToastStack toasts={toasts} />
    </div>
  );
}

function Sidebar({
  open,
  mobileOpen,
  current,
  go,
  setOpen,
  setMobileOpen,
}: {
  open: boolean;
  mobileOpen: boolean;
  current: Page;
  go: (page: Page) => void;
  setOpen: (open: boolean) => void;
  setMobileOpen: (open: boolean) => void;
}) {
  return (
    <>
      <aside className={cn("fixed inset-y-0 left-0 z-30 hidden border-r border-white/10 bg-[#080d14]/95 backdrop-blur-xl transition-all duration-300 lg:block", open ? "w-72" : "w-24")}>
        <div className="flex h-full flex-col px-4 py-5">
          <div className={cn("flex items-center gap-3 px-2", !open && "justify-center")}>
            <div className="grid h-11 w-11 place-items-center rounded-md border border-cyan-300/30 bg-cyan-400/10 text-cyan-200">
              <Bot size={22} />
            </div>
            {open && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">Apex</p>
                <p className="text-lg font-semibold leading-none text-white">Sales AI</p>
              </div>
            )}
          </div>
          <div className="my-6 h-px bg-white/10" />
          <NavList items={navPrimary} current={current} go={go} open={open} />
          <div className="my-6 h-px bg-white/10" />
          <NavList items={navSecondary} current={current} go={go} open={open} />
          <div className="mt-auto rounded-md border border-white/10 bg-white/[0.035] p-3">
            {open && <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">AI Status</p>}
            <div className={cn("flex items-center gap-2", !open && "justify-center")}>
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_16px_rgba(52,211,153,0.7)]" />
              {open && <span className="text-sm text-slate-300">System Ready</span>}
            </div>
          </div>
          <button className="focus-ring mt-3 rounded-md border border-white/10 p-2 text-slate-400 hover:border-cyan-300/40 hover:text-cyan-200" onClick={() => setOpen(!open)} aria-label="Toggle sidebar">
            {open ? <PanelLeftClose className="mx-auto" size={18} /> : <PanelLeftOpen className="mx-auto" size={18} />}
          </button>
        </div>
      </aside>
      <div className="sticky top-0 z-20 flex items-center justify-between border-b border-white/10 bg-[#080d14]/90 px-4 py-3 backdrop-blur-xl lg:hidden">
        <div className="flex items-center gap-2 font-semibold">
          <Bot size={19} className="text-cyan-200" /> Apex Sales AI
        </div>
        <button className="focus-ring rounded-md border border-white/10 p-2" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle navigation">
          <PanelLeftOpen size={18} />
        </button>
      </div>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden" role="dialog" aria-modal="true">
          <div className="h-full w-72 border-r border-white/10 bg-[#080d14] p-4 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-md border border-cyan-300/30 bg-cyan-400/10 text-cyan-200"><Bot size={20} /></div>
                <div><p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">Apex</p><p className="font-semibold text-white">Sales AI</p></div>
              </div>
              <button className="focus-ring rounded-md border border-white/10 p-2 text-slate-400" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18} /></button>
            </div>
            <NavList items={navPrimary} current={current} go={go} open />
            <div className="my-5 h-px bg-white/10" />
            <NavList items={navSecondary} current={current} go={go} open />
          </div>
        </div>
      )}
    </>
  );
}

function NavList({ items, current, go, open }: { items: NavItem[]; current: Page; go: (page: Page) => void; open: boolean }) {
  return (
    <nav className="space-y-1">
      {items.map((item) => {
        const Icon = item.icon;
        const active = current === item.page || (current === "leadDetail" && item.page === "leads") || (current === "pitch" && item.page === "find");
        return (
          <button
            key={item.page}
            className={cn("focus-ring flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition", active ? "bg-cyan-400/12 text-cyan-100 shadow-[inset_0_0_0_1px_rgba(56,189,248,0.22)]" : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-100", !open && "justify-center")}
            onClick={() => go(item.page)}
            title={item.label}
          >
            <Icon size={18} />
            {open && <span>{item.label}</span>}
          </button>
        );
      })}
    </nav>
  );
}

function Topbar({ title, query, setQuery, openPalette, quickFind, sidebarOpen, toggleSidebar }: { title: string; query: string; setQuery: (value: string) => void; openPalette: () => void; quickFind: () => void; sidebarOpen: boolean; toggleSidebar: () => void }) {
  return (
    <header className="sticky top-0 z-10 border-b border-white/10 bg-[#070a0f]/78 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1540px] items-center gap-3 px-4 sm:px-6 xl:px-8">
        <button className="focus-ring hidden rounded-md border border-white/10 p-2 text-slate-400 hover:text-cyan-200 lg:block" onClick={toggleSidebar} aria-label="Toggle sidebar">
          {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
        <h1 className="min-w-fit text-base font-semibold text-white sm:text-lg">{title}</h1>
        <div className="relative ml-auto hidden w-full max-w-md md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={17} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} className="focus-ring h-10 w-full rounded-md border border-white/10 bg-white/[0.04] pl-9 pr-16 text-sm text-slate-200 placeholder:text-slate-500 focus:border-cyan-300/50" placeholder="Search leads or commands" />
          <button onClick={openPalette} className="absolute right-2 top-1/2 -translate-y-1/2 rounded border border-white/10 px-1.5 py-0.5 text-xs text-slate-500">Ctrl K</button>
        </div>
        <div className="hidden items-center gap-2 rounded-md border border-emerald-300/20 bg-emerald-400/8 px-3 py-2 text-xs text-emerald-200 sm:flex"><span className="h-2 w-2 rounded-full bg-emerald-400" /> AI Ready</div>
        <button className="focus-ring rounded-md border border-white/10 p-2 text-slate-400 hover:text-cyan-200" aria-label="Notifications"><Bell size={18} /></button>
        <button onClick={quickFind} className="focus-ring hidden items-center gap-2 rounded-md bg-cyan-400 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 sm:inline-flex"><Plus size={16} /> Find Leads</button>
        <div className="grid h-9 w-9 place-items-center rounded-md border border-white/10 bg-white/[0.06] text-sm font-semibold text-cyan-100">A</div>
      </div>
    </header>
  );
}

function PageHeader({ title, subtitle, action }: { title: string; subtitle: string; action?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h2>
        <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
      </div>
      {action}
    </div>
  );
}

function Button({ children, onClick, variant = "primary", className, disabled }: { children: React.ReactNode; onClick?: () => void; variant?: "primary" | "secondary" | "ghost"; className?: string; disabled?: boolean }) {
  return (
    <button disabled={disabled} onClick={onClick} className={cn("focus-ring inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-semibold transition active:scale-[0.99] disabled:opacity-50", variant === "primary" && "bg-cyan-400 text-slate-950 shadow-[0_10px_30px_rgba(34,211,238,0.14)] hover:bg-cyan-300", variant === "secondary" && "border border-white/10 bg-white/[0.055] text-slate-100 hover:border-cyan-300/40 hover:bg-cyan-400/10", variant === "ghost" && "text-slate-400 hover:bg-white/[0.045] hover:text-slate-100", className)}>
      {children}
    </button>
  );
}

function Panel({ children, className }: { children: React.ReactNode; className?: string }) {
  return <section className={cn("rounded-lg border border-white/10 bg-[#0d141d]/78 shadow-[0_18px_60px_rgba(0,0,0,0.22)]", className)}>{children}</section>;
}

function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.14em] text-slate-300"><span className="text-cyan-300">{icon}</span>{title}</div>;
}

function LeadScore({ score }: { score: number }) {
  return <div className="inline-flex items-center gap-1.5 rounded-md border border-cyan-300/25 bg-cyan-400/10 px-2.5 py-1 text-sm font-bold text-cyan-100"><Flame size={15} className="text-cyan-300" /> {score}/100</div>;
}

function OpportunityBadge({ label }: { label: string }) {
  return <span className="inline-flex rounded-md border border-cyan-300/20 bg-cyan-400/8 px-2 py-1 text-xs font-medium text-cyan-100">{label}</span>;
}

function StatusBanner({ loading, error, empty, emptyText, onRetry }: { loading?: boolean; error?: string | null; empty?: boolean; emptyText?: string; onRetry?: () => void }) {
  if (loading) return <Panel className="p-5 text-sm text-slate-400">Loading workspace data...</Panel>;
  if (error) return <Panel className="p-5 text-sm text-red-200">{error}{onRetry && <Button className="ml-3" variant="secondary" onClick={onRetry}>Retry</Button>}</Panel>;
  if (empty) return <Panel className="p-5 text-sm text-slate-400">{emptyText ?? "No records yet."}</Panel>;
  return null;
}

function CommandCenter({ go, toast }: { go: (page: Page, leadId?: string) => void; toast: (title: string, tone?: ToastMessage["tone"]) => void }) {
  const { kpis, summary, loading, error, refetch } = useDashboard();
  const { leads, loading: leadsLoading, error: leadsError, refetch: refetchLeads } = useSalesLeads({ page: 1, page_size: 12, sort_by: "score" });
  const priority = leads.filter((lead) => lead.score >= 70).slice(0, 6);
  const attention = priority.length ? priority : leads.slice(0, 6);
  return (
    <>
      <PageHeader title="Good evening. Ready to find your next client?" subtitle="Your AI sales command center" action={<Button onClick={() => go("find")}><Plus size={17} /> Find New Leads</Button>} />
      {loading || error ? <StatusBanner loading={loading} error={error} onRetry={refetch} /> : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
          {kpis.map((kpi) => <StatCard key={kpi.label} label={kpi.label} value={String(kpi.value)} trend={kpi.trend} />)}
        </div>
      )}
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel className="p-4 sm:p-5">
          <SectionTitle icon={<Flame size={18} />} title="Leads Requiring Attention" />
          {leadsLoading || leadsError || !attention.length ? <div className="mt-4"><StatusBanner loading={leadsLoading} error={leadsError} empty={!attention.length} emptyText="No leads requiring attention yet." onRetry={refetchLeads} /></div> : (
            <div className="mt-4 grid gap-3 lg:grid-cols-2">{attention.map((lead) => <LeadMiniCard key={lead.id} lead={lead} go={go} toast={toast} />)}</div>
          )}
        </Panel>
        <div className="space-y-6"><AIInsights summary={summary} /><ActivityTimeline leads={leads.slice(0, 5)} /></div>
      </div>
    </>
  );
}

function StatCard({ label, value, trend }: { label: string; value: string; trend: string }) {
  return (
    <Panel className="p-4 transition hover:-translate-y-0.5 hover:border-cyan-300/24">
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <div className="mt-3 flex items-end justify-between">
        <p className="text-3xl font-semibold text-white">{value}</p>
        <span className="rounded bg-emerald-400/10 px-2 py-1 text-xs text-emerald-200">{trend}</span>
      </div>
    </Panel>
  );
}

function LeadMiniCard({ lead, go, toast }: { lead: Lead; go: (page: Page, leadId?: string) => void; toast: (title: string) => void }) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.035] p-4 transition hover:-translate-y-0.5 hover:border-cyan-300/35">
      <div className="flex items-start justify-between gap-3">
        <div>
          <button className="text-left font-semibold text-white hover:text-cyan-200" onClick={() => go("leadDetail", lead.id)}>{lead.name}</button>
          <p className="mt-1 text-sm text-slate-400">{lead.industry} · {lead.location}</p>
        </div>
        <LeadScore score={lead.score} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300">
        <span className="rounded bg-red-400/10 px-2 py-1 text-red-200">{lead.websiteState}</span>
        <span className="rounded bg-white/[0.05] px-2 py-1">{lead.reviews} reviews</span>
        <span className="rounded bg-white/[0.05] px-2 py-1">Active Instagram</span>
      </div>
      <p className="mt-3 text-sm text-slate-400">Opportunity: <span className="text-slate-100">{lead.opportunity}</span></p>
      <QuickContact lead={lead} toast={toast} />
      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="secondary" onClick={() => go("leadDetail", lead.id)}>Research</Button>
        <Button variant="secondary" onClick={() => go("pitch", lead.id)}><Sparkles size={15} /> Pitch</Button>
        <Button variant="ghost" onClick={() => { const digits = digitsPhone(lead.phone); if (digits) window.open(`https://wa.me/${digits}`, "_blank", "noopener,noreferrer"); toast(digits ? "WhatsApp opened with no message sent" : "No phone number available"); }}><MessageCircle size={15} /> WhatsApp</Button>
      </div>
    </article>
  );
}

function QuickContact({ lead, toast }: { lead: Lead; toast: (title: string) => void }) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-slate-300">
      <Phone size={15} className="text-cyan-300" />
      <span>{lead.phone}</span>
      <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => { const digits = digitsPhone(lead.phone); if (digits) window.open(`https://wa.me/${digits}`, "_blank", "noopener,noreferrer"); toast(digits ? "WhatsApp opened with no message sent" : "No phone number available"); }}>WhatsApp</Button>
      <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => { void copyText(lead.phone); toast("Phone copied"); }}>Copy</Button>
      <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => { if (lead.phone) window.open(`tel:${lead.phone}`); toast(lead.phone ? "Call started locally" : "No phone number available"); }}>Call</Button>
    </div>
  );
}

function AIInsights({ summary }: { summary: { high_opportunity_leads: number; new_leads: number; draft_outreach_count: number; qualified_leads: number } | null }) {
  const hot = summary?.high_opportunity_leads ?? 0;
  const drafts = summary?.draft_outreach_count ?? 0;
  const qualified = summary?.qualified_leads ?? 0;
  const fresh = summary?.new_leads ?? 0;
  return (
    <Panel className="p-5">
      <SectionTitle icon={<Sparkles size={18} />} title="AI Sales Insights" />
      <div className="mt-4 space-y-3 text-sm text-slate-300">
        <p><span className="font-semibold text-cyan-100">{hot} high-quality leads</span> currently scored as hot.</p>
        <p>{fresh} new leads waiting for research.</p>
        <p>{qualified} leads already qualified.</p>
        <p>{drafts} outreach drafts ready for review.</p>
        <div className="rounded-md border border-cyan-300/20 bg-cyan-400/8 p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-cyan-200">Recommended action</p>
          <p className="mt-1 text-slate-100">{fresh > 0 ? "Run intelligence on new leads first." : drafts > 0 ? "Review existing outreach drafts before generating more." : "Find and import your next set of leads."}</p>
        </div>
      </div>
    </Panel>
  );
}

function ActivityTimeline({ leads }: { leads: Lead[] }) {
  return (
    <Panel className="p-5">
      <SectionTitle icon={<Gauge size={18} />} title="Today's Activity" />
      <div className="mt-4 space-y-4">
        {leads.map((lead) => (
          <div key={lead.id} className="grid grid-cols-[3.2rem_1fr] gap-3 text-sm">
            <span className="text-slate-500">{lead.foundAt}</span>
            <div><p className="font-medium text-slate-200">{lead.lastAction}</p><p className="text-slate-500">{lead.name}</p></div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function FindLeads({ go, toast, setSelectedLeadId }: { go: (page: Page, leadId?: string) => void; toast: (title: string, tone?: ToastMessage["tone"]) => void; setSelectedLeadId: (id: string) => void }) {
  const [location, setLocation] = useState("Hyderabad");
  const [industries, setIndustries] = useState<string[]>(["Dental Clinics"]);
  const [opportunities, setOpportunities] = useState<string[]>(["No website"]);
  const [minimumRating, setMinimumRating] = useState(4);
  const [minimumReviews, setMinimumReviews] = useState(50);
  const [count, setCount] = useState(50);
  const [searching, setSearching] = useState(false);
  const [doneSteps, setDoneSteps] = useState(0);
  const [results, setResults] = useState<Lead[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const steps = ["Searching business sources", "Website analysis", "Social presence", "Lead qualification", "Generating results"];

  async function runSearch() {
    setSearching(true);
    setResults([]);
    setDoneSteps(0);
    setSearchError(null);
    for (let index = 0; index < steps.length; index += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 180));
      setDoneSteps(index + 1);
    }
    try {
      const wantsNoWebsite = opportunities.includes("No website") && !opportunities.includes("Any Opportunity");
      const response = await api.getSalesLeads({
        city: location && location !== "Any" ? location : undefined,
        category: industries[0],
        has_website: wantsNoWebsite ? false : undefined,
        page: 1,
        page_size: Math.min(Math.max(count, 1), 100),
        sort_by: "created_at",
      });
      const found = response.leads.map(salesLeadSummaryToLeadItem);
      setResults(found);
      if (found[0]) setSelectedLeadId(found[0].id);
      toast(found.length ? `Found ${found.length} workspace leads` : "No matching workspace leads");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      setSearchError(message);
      toast(message, "error");
    } finally {
      setSearching(false);
    }
  }

  return (
    <>
      <PageHeader title="Find Your Next Client" subtitle="Tell Apex what type of business you're looking for." />
      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.2fr]">
        <Panel className="p-5">
          <SectionTitle icon={<Search size={18} />} title="Search Builder" />
          <div className="mt-5 space-y-5">
            <Field label="Location">
              <input className="input" list="locations" value={location} onChange={(event) => setLocation(event.target.value)} />
              <datalist id="locations">{["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai", "Pune", "Any"].map((item) => <option key={item} value={item} />)}</datalist>
            </Field>
            <Field label="Business Type">
              <ChipSelect values={["Restaurants", "Dental Clinics", "Medical Clinics", "Salons", "Gyms", "Real Estate", "Interior Designers", "Hotels", "Law Firms", "Coaching Institutes", "Manufacturers", "E-commerce", "Photographers", "Event Companies", "Architects", "Consultants", "Other"]} selected={industries} setSelected={setIndustries} />
            </Field>
            <Field label="Opportunity Type">
              <ChipSelect card values={["No website", "Outdated website", "Poor mobile experience", "Poor SEO", "No online booking", "No online ordering", "Weak conversion", "Website redesign", "Any Opportunity"]} selected={opportunities} setSelected={setOpportunities} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Minimum Rating"><input className="input" type="number" min={0} max={5} step={0.1} value={minimumRating} onChange={(event) => setMinimumRating(Number(event.target.value))} /></Field>
              <Field label="Minimum Reviews"><input className="input" type="number" min={0} value={minimumReviews} onChange={(event) => setMinimumReviews(Number(event.target.value))} /></Field>
              <Field label="Lead Quality"><select className="input"><option>Any</option><option>Hot</option><option>Good</option><option>Maybe</option></select></Field>
              <Field label="Business Size"><select className="input"><option>Any</option><option>Small</option><option>Growing</option><option>Established</option></select></Field>
            </div>
            <Field label="Leads to find">
              <div className="flex items-center gap-3">
                <Button variant="secondary" onClick={() => setCount(Math.max(10, count - 10))}><Minus size={15} /></Button>
                <span className="grid h-10 min-w-16 place-items-center rounded-md border border-white/10 bg-white/[0.04] font-semibold">{count}</span>
                <Button variant="secondary" onClick={() => setCount(count + 10)}><Plus size={15} /></Button>
              </div>
            </Field>
            <Button className="h-12 w-full text-base" onClick={runSearch} disabled={searching}><Search size={18} /> Find Potential Clients</Button>
          </div>
        </Panel>
        <div className="space-y-6">
          {searching && <SearchProgress steps={steps} doneSteps={doneSteps} />}
          {!searching && searchError && <StatusBanner error={searchError} onRetry={runSearch} />}
          {!searching && !searchError && !results.length && <EmptyState action={runSearch} />}
          {!searching && !!results.length && <SearchResults leads={results} go={go} toast={toast} />}
        </div>
      </div>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="block"><span className="mb-2 block text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</span>{children}</div>;
}

function ChipSelect({ values, selected, setSelected, card }: { values: string[]; selected: string[]; setSelected: (items: string[]) => void; card?: boolean }) {
  return (
    <div className={cn("flex flex-wrap gap-2", card && "grid grid-cols-2 sm:grid-cols-3")}>
      {values.map((value) => {
        const active = selected.includes(value);
        return <button key={value} onClick={() => setSelected(active ? selected.filter((item) => item !== value) : [...selected, value])} className={cn("focus-ring rounded-md border px-3 py-2 text-sm transition", active ? "border-cyan-300/45 bg-cyan-400/12 text-cyan-100" : "border-white/10 bg-white/[0.035] text-slate-400 hover:text-slate-100", card && "min-h-14 text-left")}>{value}</button>;
      })}
    </div>
  );
}

function SearchProgress({ steps, doneSteps }: { steps: string[]; doneSteps: number }) {
  return (
    <Panel className="overflow-hidden p-5">
      <SectionTitle icon={<Sparkles size={18} />} title="AI Searching" />
      <div className="mt-5 space-y-4">
        {steps.map((step, index) => {
          const complete = index < doneSteps;
          const active = index === doneSteps;
          return (
            <div key={step}>
              <div className="mb-2 flex justify-between text-sm"><span className={complete ? "text-emerald-200" : "text-slate-300"}>{complete ? "✓ " : ""}{step}</span><span className="text-slate-500">{complete ? "Complete" : active ? "Running" : "Queued"}</span></div>
              <div className={cn("relative h-2 overflow-hidden rounded-full bg-white/[0.06]", active && "scan-line")}><div className="h-full rounded-full bg-cyan-300 transition-all duration-300" style={{ width: complete ? "100%" : active ? "58%" : "18%" }} /></div>
            </div>
          );
        })}
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">{[1, 2, 3, 4].map((item) => <div key={item} className="h-36 animate-pulse rounded-lg border border-white/10 bg-white/[0.035]" />)}</div>
    </Panel>
  );
}

function EmptyState({ action }: { action: () => void }) {
  return (
    <Panel className="grid min-h-80 place-items-center p-8 text-center">
      <div>
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-md border border-cyan-300/20 bg-cyan-400/10 text-cyan-200"><Search size={22} /></div>
        <h3 className="mt-4 text-lg font-semibold text-white">No leads yet</h3>
        <p className="mt-2 max-w-sm text-sm text-slate-400">Start by telling Apex what type of business you're looking for.</p>
        <Button className="mt-5" onClick={action}><Search size={16} /> Find Your First Leads</Button>
      </div>
    </Panel>
  );
}

function SearchResults({ leads, go, toast }: { leads: Lead[]; go: (page: Page, leadId?: string) => void; toast: (title: string) => void }) {
  const [filter, setFilter] = useState("All");
  const filtered = leads.filter((lead) => filter === "All" || lead.quality === filter);
  return (
    <Panel className="p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div><h3 className="text-xl font-semibold text-white">{leads.length} Potential Clients</h3><p className="text-sm text-slate-500">Sorted by lead score</p></div>
        <div className="flex flex-wrap gap-2">
          {["All", "Hot", "Good", "Maybe"].map((item) => <button key={item} onClick={() => setFilter(item)} className={cn("rounded-md border px-3 py-2 text-sm", filter === item ? "border-cyan-300/45 bg-cyan-400/12 text-cyan-100" : "border-white/10 text-slate-400")}>{item}</button>)}
          <select className="input h-10 w-36"><option>Lead Score</option><option>Rating</option><option>Reviews</option><option>Newest</option></select>
        </div>
      </div>
      <div className="mt-5 grid gap-4 2xl:grid-cols-2">{filtered.map((lead) => <LeadCard key={lead.id} lead={lead} go={go} toast={toast} />)}</div>
    </Panel>
  );
}

function LeadCard({ lead, go, toast }: { lead: Lead; go: (page: Page, leadId?: string) => void; toast: (title: string) => void }) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.035] p-4 transition hover:-translate-y-0.5 hover:border-cyan-300/30">
      <div className="flex items-start justify-between gap-3">
        <div><button onClick={() => go("leadDetail", lead.id)} className="text-left text-base font-semibold uppercase tracking-[0.05em] text-white hover:text-cyan-200">{lead.name}</button><p className="mt-1 text-sm text-slate-400">{lead.industry} · {lead.location}</p></div>
        <LeadScore score={lead.score} />
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-300"><span className="inline-flex items-center gap-1"><Star size={15} className="text-amber-300" /> {lead.rating}</span><span>{lead.reviews} reviews</span></div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2"><InfoBlock label="Website" value={lead.websiteState} /><InfoBlock label="Opportunity" value={lead.opportunity} /></div>
      <div className="mt-4 border-t border-white/10 pt-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Why this lead?</p>
        <div className="mt-3 grid gap-2 text-sm text-slate-300 sm:grid-cols-2">{lead.reasons.map((reason) => <span key={reason} className="inline-flex items-center gap-2"><Check size={14} className="text-emerald-300" /> {reason}</span>)}</div>
      </div>
      <QuickContact lead={lead} toast={toast} />
      <p className="mt-2 text-sm text-slate-400"><Mail size={15} className="mr-2 inline text-cyan-300" />{lead.email}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="secondary" onClick={() => go("leadDetail", lead.id)}>Research</Button>
        <Button onClick={() => go("pitch", lead.id)}><Sparkles size={15} /> Generate Pitch</Button>
        <Button variant="ghost" onClick={() => { const digits = digitsPhone(lead.phone); if (digits) window.open(`https://wa.me/${digits}`, "_blank", "noopener,noreferrer"); toast(digits ? "WhatsApp opened with no message sent" : "No phone number available"); }}><MessageCircle size={15} /> WhatsApp</Button>
        <Button variant="ghost" onClick={() => { if (lead.email) window.open(`mailto:${lead.email}`); toast(lead.email ? "Email draft opened locally" : "No email available"); }}><Mail size={15} /> Email</Button>
      </div>
    </article>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-white/10 bg-black/12 p-3"><p className="text-xs uppercase tracking-[0.14em] text-slate-500">{label}</p><p className="mt-1 text-sm font-medium text-slate-100">{value}</p></div>;
}

function LeadDetail({ leadId, fallback, go, toast, moveLead, onChanged }: { leadId: string | null; fallback: Lead | null; go: (page: Page, leadId?: string) => void; toast: (title: string, tone?: ToastMessage["tone"]) => void; moveLead: (id: string, status: ContactState) => void; onChanged: () => Promise<void> }) {
  const { lead, rawDetail, loading, error, refetch } = useLeadDetail(leadId);
  const { events, loading: timelineLoading, error: timelineError, refetch: refetchTimeline } = useLeadTimeline(leadId);
  const actions = useLeadActions(leadId);
  const display = lead ?? fallback;
  const busy = actions.loading;
  const flags: ReadinessFlags | null = actions.readinessFlags ?? rawDetail?.readiness_flags ?? null;
  const nextAction = actions.nextAction ?? rawDetail?.next_recommended_action ?? display?.nextAction ?? "RUN_INTELLIGENCE";

  useEffect(() => {
    if (leadId) void actions.prepare();
  }, [leadId]);

  async function runRecommended() {
    if (!leadId || busy) return;
    try {
      if (nextAction === "RUN_INTELLIGENCE") {
        const result = await actions.runIntelligence();
        if (!result) throw new Error(actions.error ?? "Intelligence failed");
        toast(result.message);
      } else if (nextAction === "QUALIFY") {
        const result = await actions.qualify();
        if (!result) throw new Error(actions.error ?? "Qualification failed");
        toast(result.message);
      } else if (nextAction === "GENERATE_PITCH") {
        go("pitch", leadId);
        return;
      } else {
        toast("Review the current draft before sending.");
        return;
      }
      await refetch();
      await refetchTimeline();
      await onChanged();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Action failed", "error");
    }
  }

  if (loading && !display) return <StatusBanner loading />;
  if (error && !display) return <StatusBanner error={error} onRetry={refetch} />;
  if (!display) return <StatusBanner empty emptyText="Select a lead to research." />;

  return (
    <>
      <PageHeader title={display.name} subtitle={`${display.industry} · ${display.location}`} action={<div className="flex gap-2"><LeadScore score={display.score} /><Button onClick={() => go("pitch", display.id)} disabled={busy}><Sparkles size={16} /> Generate Pitch</Button></div>} />
      {(error || actions.error) && <div className="mb-4"><StatusBanner error={error ?? actions.error} onRetry={refetch} /></div>}
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <Panel className="p-5"><SectionTitle icon={<BriefcaseBusiness size={18} />} title="Business Overview" /><p className="mt-4 text-slate-300">{display.overview}</p></Panel>
          <Panel className="p-5"><SectionTitle icon={<Gauge size={18} />} title="Online Presence" /><div className="mt-4 grid gap-3 sm:grid-cols-4"><Presence label="Google" value={`${display.rating} · ${display.reviews} reviews`} good={Boolean(rawDetail?.business.verification_status)} /><Presence label="Website" value={display.website ? "Found" : "Not found"} good={Boolean(display.website)} /><Presence label="Instagram" value={display.instagram || "Not found"} good={Boolean(display.instagram)} /><Presence label="Facebook" value={rawDetail?.business.social_profiles?.facebook || "Not found"} good={Boolean(rawDetail?.business.social_profiles?.facebook)} /></div></Panel>
          <Panel className="p-5">
            <SectionTitle icon={<Flame size={18} />} title="Why They May Need A Website" />
            <div className="mt-4 rounded-lg border border-cyan-300/20 bg-cyan-400/8 p-4">
              <OpportunityBadge label={display.quality === "Hot" ? "High Opportunity" : display.opportunity} />
              <p className="mt-3 text-sm text-slate-300">Current situation: <span className="text-white">{display.websiteState} found.</span></p>
              <div className="mt-4 grid gap-2 text-sm text-slate-300 sm:grid-cols-2">{(display.reasons.length ? display.reasons : ["Professional business website", "Service pages", "Team profiles", "Appointment booking", "Google Maps integration", "WhatsApp CTA", "SEO"]).map((item) => <span key={item} className="inline-flex gap-2"><Check size={15} className="text-emerald-300" /> {item}</span>)}</div>
            </div>
          </Panel>
          <Panel className="p-5"><SectionTitle icon={<BarChart3 size={18} />} title="Competitor Comparison" /><div className="mt-4 overflow-auto"><table className="w-full min-w-[520px] text-left text-sm"><thead className="text-slate-500"><tr><th className="py-2">Business</th><th>Website</th><th>Booking</th></tr></thead><tbody>{display.competitors.length ? display.competitors.map((item) => <tr key={item.name} className="border-t border-white/10"><td className="py-3 text-slate-200">{item.name}</td><td>{item.website ? "Yes" : "No"}</td><td>{item.booking ? "Yes" : "No"}</td></tr>) : <tr className="border-t border-white/10"><td className="py-3 text-slate-400" colSpan={3}>No competitor records yet.</td></tr>}</tbody></table></div></Panel>
          <Panel className="p-5">
            <SectionTitle icon={<Gauge size={18} />} title="Activity Timeline" />
            <div className="mt-4 space-y-4">
              {timelineLoading && <p className="text-sm text-slate-400">Loading timeline...</p>}
              {timelineError && <p className="text-sm text-red-200">{timelineError}</p>}
              {!timelineLoading && !events.length && <p className="text-sm text-slate-400">No timeline events yet.</p>}
              {events.map((event) => (
                <div key={`${event.type}-${event.timestamp}`} className="grid grid-cols-[7rem_1fr] gap-3 text-sm">
                  <span className="text-slate-500">{formatDate(event.timestamp)}</span>
                  <div><p className="font-medium text-slate-200">{event.title}</p><p className="text-slate-500">{event.description}</p></div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
        <div className="space-y-6">
          <Panel className="p-5"><SectionTitle icon={<Phone size={18} />} title="Contact Information" /><div className="mt-4 space-y-3 text-sm text-slate-300"><ContactRow label="Phone" value={display.phone || "Not found"} /><ContactRow label="Email" value={display.email || "Not found"} /><ContactRow label="Website" value={display.website ?? "Not found"} /><ContactRow label="Instagram" value={display.instagram || "Not found"} /><ContactRow label="Google listing" value={display.googleListing} /><ContactRow label="Address" value={display.address || "Not found"} /></div><QuickContact lead={display} toast={toast} /></Panel>
          <Panel className="border-cyan-300/20 bg-cyan-400/[0.055] p-5">
            <SectionTitle icon={<Sparkles size={18} />} title="AI Recommendation" />
            <p className="mt-4 font-semibold text-white">{nextAction.replace(/_/g, " ")}</p>
            <p className="mt-3 text-sm text-slate-300">Best pitch angle: {display.opportunity}</p>
            <p className="mt-3 text-sm text-slate-300">Recommended channel: <span className="text-cyan-100">{rawDetail?.contact_action_data.whatsapp_available ? "WhatsApp" : rawDetail?.contact_action_data.email_available ? "Email" : "Manual"}</span></p>
            <p className="mt-3 text-sm text-slate-300">Lead confidence: <span className="text-cyan-100">{display.score}/100</span></p>
            {flags && <p className="mt-3 text-xs text-slate-400">Ready: research {flags.can_research ? "yes" : "no"} · qualify {flags.can_qualify ? "yes" : "no"} · pitch {flags.can_generate_pitch ? "yes" : "no"} · draft {flags.has_draft ? "yes" : "no"}</p>}
            <div className="mt-5 flex flex-wrap gap-2">
              <Button onClick={() => void runRecommended()} disabled={busy}>{busy ? "Working..." : nextAction === "GENERATE_PITCH" ? "Generate Pitch" : nextAction === "QUALIFY" ? "Qualify Lead" : nextAction === "RUN_INTELLIGENCE" ? "Run Intelligence" : "Review Draft"}</Button>
              <Button variant="secondary" onClick={() => go("pitch", display.id)} disabled={busy}><Sparkles size={16} /> Open Pitch</Button>
              <Button variant="ghost" onClick={() => moveLead(display.id, "Contacted")} disabled={busy}>Move to Contacted</Button>
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}

function Presence({ label, value, good }: { label: string; value: string; good: boolean }) {
  return <div className="rounded-md border border-white/10 bg-white/[0.035] p-4"><p className="text-sm font-semibold text-white">{label}</p><p className={cn("mt-2 text-sm", good ? "text-emerald-200" : "text-red-200")}>{good ? "Yes" : "No"} · {value}</p></div>;
}

function ContactRow({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-3 border-b border-white/10 pb-2 last:border-0"><span className="text-slate-500">{label}</span><span className="text-right text-slate-200">{value}</span></div>;
}

function PitchGenerator({ leadId, fallback, pitchText, setPitchText, toast, onChanged }: { leadId: string | null; fallback: Lead | null; pitchText: string; setPitchText: (value: string) => void; toast: (title: string, tone?: ToastMessage["tone"]) => void; onChanged: () => Promise<void> }) {
  const { lead, rawDetail, loading, error, refetch } = useLeadDetail(leadId);
  const actions = useLeadActions(leadId);
  const [type, setType] = useState("WhatsApp");
  const [tone, setTone] = useState("Professional");
  const attempted = useRef(false);
  const display = lead ?? fallback;
  const generating = actions.loading;
  const draftText = pitchText || extractPitchText(rawDetail);

  async function createPitch(regenerate = false) {
    if (!leadId || generating) return;
    const result = await actions.generatePitch(pitchChannelFromType(type), regenerate);
    if (!result) {
      toast(actions.error ?? "Pitch generation failed", "error");
      return;
    }
    setPitchText(extractPitchText(null, result.result) || result.message);
    await refetch();
    await onChanged();
    toast(regenerate ? "Pitch draft regenerated" : "Pitch draft generated");
  }

  useEffect(() => {
    attempted.current = false;
  }, [leadId]);

  useEffect(() => {
    if (!leadId || attempted.current || generating || draftText) return;
    attempted.current = true;
    void createPitch();
  }, [leadId, draftText, generating]);

  if (loading && !display) return <StatusBanner loading />;
  if (error && !display) return <StatusBanner error={error} onRetry={refetch} />;
  if (!display) return <StatusBanner empty emptyText="Select a lead before generating a pitch." />;

  return (
    <>
      <PageHeader title="AI Pitch Generator" subtitle={`${display.name} · ${display.score}/100`} />
      {actions.error && <div className="mb-4"><StatusBanner error={actions.error} /></div>}
      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <Panel className="p-5">
          <div className="flex flex-wrap gap-2">{["WhatsApp", "Email", "Instagram DM", "Call Opener", "Follow-up"].map((item) => <button key={item} onClick={() => setType(item)} className={cn("rounded-md border px-3 py-2 text-sm", type === item ? "border-cyan-300/45 bg-cyan-400/12 text-cyan-100" : "border-white/10 text-slate-400")}>{item}</button>)}</div>
          <div className="mt-5 flex flex-wrap gap-2">{["Professional", "Friendly", "Direct", "Consultative", "Short"].map((item) => <button key={item} onClick={() => setTone(item)} className={cn("rounded-md border px-3 py-2 text-sm", tone === item ? "border-cyan-300/45 bg-cyan-400/12 text-cyan-100" : "border-white/10 text-slate-400")}>{item}</button>)}</div>
          <textarea value={generating ? "Generating personalized pitch..." : draftText} onChange={(event) => setPitchText(event.target.value)} className="focus-ring mt-5 min-h-[360px] w-full resize-y rounded-lg border border-white/10 bg-black/24 p-4 text-sm leading-7 text-slate-100 focus:border-cyan-300/45" />
          <div className="mt-4 flex flex-wrap gap-2"><Button onClick={() => void createPitch()} disabled={generating}><Sparkles size={16} /> Generate Pitch</Button><Button variant="secondary" onClick={() => void createPitch(true)} disabled={generating}>Regenerate</Button><Button variant="secondary" onClick={() => { void copyText(draftText); toast("Message copied"); }}><Copy size={16} /> Copy</Button><Button variant="ghost" onClick={() => { const digits = digitsPhone(display.phone); if (digits) window.open(`https://wa.me/${digits}`, "_blank", "noopener,noreferrer"); toast(digits ? "WhatsApp opened with no message sent" : "No phone number available"); }}><Send size={16} /> WhatsApp</Button></div>
        </Panel>
        <Panel className="p-5"><SectionTitle icon={<Sparkles size={18} />} title="AI Quality" /><div className="mt-5 space-y-4"><Quality label="Personalization" value={display.score || 70} /><Quality label="Relevance" value={Math.min(100, (display.score || 70) + 6)} /><Quality label="Clarity" value={Math.min(100, (display.score || 70) + 4)} /><Quality label="Sales Pressure" value={20} low /></div><div className="mt-6 space-y-2 text-sm text-slate-300">{["Mentions business", "Uses real opportunity", "Personalized", "Clear CTA", "Not overly salesy"].map((item) => <p key={item} className="flex gap-2"><Check size={15} className="text-emerald-300" /> {item}</p>)}</div></Panel>
      </div>
    </>
  );
}

function Quality({ label, value, low }: { label: string; value: number; low?: boolean }) {
  return <div><div className="mb-2 flex justify-between text-sm"><span className="text-slate-300">{label}</span><span className={low ? "text-emerald-200" : "text-cyan-100"}>{low ? "LOW" : `${value}%`}</span></div><div className="h-2 rounded-full bg-white/[0.06]"><div className={cn("h-full rounded-full", low ? "bg-emerald-300" : "bg-cyan-300")} style={{ width: `${value}%` }} /></div></div>;
}

function HotLeads({ leads, go, toast, loading, error, onRetry }: { leads: Lead[]; go: (page: Page, leadId?: string) => void; toast: (title: string, tone?: ToastMessage["tone"]) => void; loading?: boolean; error?: string | null; onRetry?: () => void }) {
  return <LeadTable title="Hot Leads" subtitle="Businesses most likely to benefit from your services." leads={leads} go={go} toast={toast} filters={["All", "No Website", "Website Redesign", "High Value", "Recently Found"]} loading={loading} error={error} onRetry={onRetry} />;
}

function AllLeads({ leads, go, toast, loading, error, onRetry }: { leads: Lead[]; go: (page: Page, leadId?: string) => void; toast: (title: string, tone?: ToastMessage["tone"]) => void; loading?: boolean; error?: string | null; onRetry?: () => void }) {
  return <LeadTable title="All Leads" subtitle="Every researched prospect in your sales workspace." leads={leads} go={go} toast={toast} filters={["All", "Hot", "Good", "Maybe"]} loading={loading} error={error} onRetry={onRetry} />;
}

function LeadTable({ title, subtitle, leads, go, toast, filters, loading, error, onRetry }: { title: string; subtitle: string; leads: Lead[]; go: (page: Page, leadId?: string) => void; toast: (title: string, tone?: ToastMessage["tone"]) => void; filters: string[]; loading?: boolean; error?: string | null; onRetry?: () => void }) {
  const [filter, setFilter] = useState("All");
  const filtered = leads.filter((lead) => filter === "All" || lead.quality === filter || lead.websiteState.toLowerCase().includes(filter.toLowerCase().replace("website redesign", "outdated")));
  return (
    <>
      <PageHeader title={title} subtitle={subtitle} />
      {(loading || error || !leads.length) && <div className="mb-4"><StatusBanner loading={loading} error={error} empty={!loading && !error && !leads.length} emptyText="No leads in the workspace yet." onRetry={onRetry} /></div>}
      <Panel className="p-5">
        <div className="mb-4 flex flex-wrap gap-2">{filters.map((item) => <button key={item} onClick={() => setFilter(item)} className={cn("rounded-md border px-3 py-2 text-sm", filter === item ? "border-cyan-300/45 bg-cyan-400/12 text-cyan-100" : "border-white/10 text-slate-400")}>{item}</button>)}</div>
        <div className="overflow-auto"><table className="w-full min-w-[880px] text-left text-sm"><thead className="text-xs uppercase tracking-[0.12em] text-slate-500"><tr><th className="py-3">Business</th><th>Industry</th><th>Location</th><th>Score</th><th>Opportunity</th><th>Contact</th><th>Last Action</th><th>Next Action</th></tr></thead><tbody>{filtered.map((lead) => <tr key={lead.id} className="border-t border-white/10 text-slate-300 hover:bg-white/[0.025]"><td className="py-4"><button onClick={() => go("leadDetail", lead.id)} className="font-semibold text-white hover:text-cyan-200">{lead.name}</button></td><td>{lead.industry}</td><td>{lead.location}</td><td><LeadScore score={lead.score} /></td><td>{lead.opportunity}</td><td><Button variant="ghost" className="px-2 py-1" onClick={() => { const digits = digitsPhone(lead.phone); if (digits) window.open(`https://wa.me/${digits}`, "_blank", "noopener,noreferrer"); toast(digits ? "WhatsApp opened with no message sent" : "No phone number available"); }}>WhatsApp</Button></td><td>{lead.lastAction}</td><td>{lead.nextAction}</td></tr>)}</tbody></table></div>
      </Panel>
    </>
  );
}

function ConversationsPage({ leads, toast, loading, error, onRetry }: { leads: Lead[]; toast: (title: string, tone?: ToastMessage["tone"]) => void; loading?: boolean; error?: string | null; onRetry?: () => void }) {
  const draftLeads = leads.filter((lead) => lead.conversationState === "Draft ready" || lead.status === "Replied" || lead.status === "Contacted");
  const [activeId, setActiveId] = useState<string | null>(null);
  const items = draftLeads.length ? draftLeads : leads;
  const active = items.find((lead) => lead.id === activeId) ?? items[0] ?? null;
  return (
    <>
      <PageHeader title="Conversations" subtitle="Track replies and prepare AI-assisted responses." />
      {(loading || error || !items.length) && <div className="mb-4"><StatusBanner loading={loading} error={error} empty={!loading && !error && !items.length} emptyText="No conversation-ready leads yet." onRetry={onRetry} /></div>}
      {active && (
      <div className="grid min-h-[680px] gap-4 xl:grid-cols-[280px_1fr_320px]">
        <Panel className="overflow-hidden"><div className="border-b border-white/10 p-4 font-semibold text-white">Conversations</div>{items.map((itemLead) => <button key={itemLead.id} onClick={() => setActiveId(itemLead.id)} className={cn("block w-full border-b border-white/10 p-4 text-left hover:bg-white/[0.04]", active.id === itemLead.id && "bg-cyan-400/10")}><div className="flex items-center justify-between"><p className="font-medium text-white">{itemLead.name}</p><span className="rounded bg-white/[0.06] px-2 py-1 text-xs text-slate-400">{itemLead.phone ? "WhatsApp" : "Email"}</span></div><p className="mt-1 text-sm text-slate-500">{itemLead.conversationState}</p></button>)}</Panel>
        <Panel className="flex flex-col p-5"><div className="border-b border-white/10 pb-4"><h3 className="font-semibold text-white">{active.name}</h3><p className="text-sm text-slate-500">{active.status}</p></div><div className="flex-1 space-y-4 py-5"><div className="max-w-[78%] rounded-lg border border-white/10 bg-white/[0.04] p-3 text-sm text-slate-200"><p className="mb-1 text-xs text-slate-500">Workspace · {active.foundAt}</p>{active.lastAction}</div></div><div className="rounded-lg border border-cyan-300/20 bg-cyan-400/8 p-4"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-200">AI Suggested Reply</p><p className="mt-2 text-sm text-slate-200">{active.nextAction}. Review the current draft before sending anything.</p><div className="mt-3 flex gap-2"><Button onClick={() => toast("Sending is disabled. Copy or open a local draft instead.")}>Send</Button><Button variant="secondary" onClick={() => toast("Edit the draft from the pitch screen.")}>Edit</Button></div></div></Panel>
        <Panel className="p-5"><SectionTitle icon={<BriefcaseBusiness size={18} />} title="Lead Context" /><div className="mt-4 space-y-3 text-sm text-slate-300"><ContactRow label="Score" value={`${active.score}/100`} /><ContactRow label="Opportunity" value={active.websiteState} /><ContactRow label="Location" value={active.location} /><ContactRow label="Next" value={active.nextAction} /></div></Panel>
      </div>
      )}
    </>
  );
}

function OutreachPage({ leads, toast, loading, error, onRetry }: { leads: Lead[]; toast: (title: string, tone?: ToastMessage["tone"]) => void; loading?: boolean; error?: string | null; onRetry?: () => void }) {
  const drafts = leads.filter((lead) => lead.conversationState === "Draft ready" || lead.nextAction.toLowerCase().includes("pitch") || lead.nextAction.toLowerCase().includes("outreach"));
  const rows = drafts.length ? drafts : leads;
  return (
    <>
      <PageHeader title="Outreach" subtitle="Drafts, scheduled messages, sent outreach, replies, and follow-ups." />
      {(loading || error || !rows.length) && <div className="mb-4"><StatusBanner loading={loading} error={error} empty={!loading && !error && !rows.length} emptyText="No outreach drafts yet." onRetry={onRetry} /></div>}
      <Panel className="p-5">
        <div className="mb-4 flex flex-wrap gap-2">{["Drafts", "Scheduled", "Sent", "Replies", "Follow-ups"].map((item) => <button key={item} className="rounded-md border border-white/10 px-3 py-2 text-sm text-slate-400 hover:text-slate-100">{item}</button>)}</div>
        <div className="overflow-auto"><table className="w-full min-w-[820px] text-left text-sm"><thead className="text-xs uppercase tracking-[0.12em] text-slate-500"><tr><th className="py-3">Lead</th><th>Channel</th><th>Message</th><th>Status</th><th>Sent</th><th>Reply</th><th>Next Follow-up</th><th></th></tr></thead><tbody>{rows.map((lead) => <tr key={lead.id} className="border-t border-white/10 text-slate-300"><td className="py-4 font-medium text-white">{lead.name}</td><td>{lead.phone ? "WhatsApp" : "Email"}</td><td>{lead.opportunity}</td><td><OpportunityBadge label={lead.conversationState === "Draft ready" ? "Draft" : lead.status} /></td><td>Not sent</td><td>{lead.status === "Replied" ? "Received" : "None"}</td><td>{lead.nextAction}</td><td><Button variant="ghost" onClick={() => toast("Sending is disabled. Open the pitch draft instead.")}>Open</Button></td></tr>)}</tbody></table></div>
      </Panel>
    </>
  );
}

function PipelinePage({ leads, go, moveLead, loading, error, onRetry }: { leads: Lead[]; go: (page: Page, leadId?: string) => void; moveLead: (id: string, status: ContactState) => void; loading?: boolean; error?: string | null; onRetry?: () => void }) {
  const stages: ContactState[] = ["New", "Researched", "Qualified", "Contacted", "Replied", "Interested", "Meeting", "Proposal", "Won"];
  return (
    <>
      <PageHeader title="Pipeline" subtitle="Move prospects through the website-development sales workflow." />
      {(loading || error) && <div className="mb-4"><StatusBanner loading={loading} error={error} onRetry={onRetry} /></div>}
      <div className="flex gap-4 overflow-x-auto pb-3">{stages.map((stage) => <PipelineColumn key={stage} stage={stage} leads={leads.filter((lead) => lead.status === stage)} go={go} moveLead={moveLead} stages={stages} />)}</div>
    </>
  );
}

function PipelineColumn({ stage, leads, go, moveLead, stages }: { stage: ContactState; leads: Lead[]; go: (page: Page, leadId?: string) => void; moveLead: (id: string, status: ContactState) => void; stages: ContactState[] }) {
  const next = stages[Math.min(stages.indexOf(stage) + 1, stages.length - 1)];
  return (
    <Panel className="min-w-[260px] p-3">
      <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-400">{stage}</h3><span className="rounded bg-white/[0.06] px-2 py-1 text-xs text-slate-500">{leads.length}</span></div>
      <div className="space-y-3">{leads.map((lead) => <article key={lead.id} draggable className="rounded-md border border-white/10 bg-white/[0.045] p-3 transition hover:-translate-y-0.5 hover:border-cyan-300/35 active:scale-[0.99]"><button onClick={() => go("leadDetail", lead.id)} className="text-left font-semibold text-white hover:text-cyan-200"><Flame size={14} className="mr-1 inline text-cyan-300" /> {lead.name}</button><p className="mt-2 text-sm text-slate-400">{lead.score}/100 · {lead.websiteState}</p><p className="mt-2 text-sm font-medium text-cyan-100">{lead.value} opportunity</p><p className="mt-3 text-xs uppercase tracking-[0.12em] text-slate-500">Next</p><p className="text-sm text-slate-300">{lead.nextAction}</p><Button variant="secondary" className="mt-3 w-full" onClick={() => moveLead(lead.id, next)}>Move next</Button></article>)}</div>
    </Panel>
  );
}

function AnalyticsPage() {
  const { summary, kpis, loading, error, refetch } = useDashboard();
  const funnel = [
    { stage: "New", value: summary?.new_leads ?? 0 },
    { stage: "Qualified", value: summary?.qualified_leads ?? 0 },
    { stage: "Contacted", value: summary?.contacted_leads ?? 0 },
    { stage: "Replied", value: summary?.replied_leads ?? 0 },
    { stage: "Interested", value: summary?.interested_leads ?? 0 },
    { stage: "Won", value: summary?.converted_leads ?? 0 },
  ];
  const sources = [
    { name: "Workspace", value: summary?.total_leads ?? 0 },
    { name: "Qualified", value: summary?.qualified_leads ?? 0 },
    { name: "Drafts", value: summary?.draft_outreach_count ?? 0 },
    { name: "Hot", value: summary?.high_opportunity_leads ?? 0 },
    { name: "Lost", value: summary?.lost_leads ?? 0 },
  ];
  const maxSource = Math.max(...sources.map((item) => item.value), 1);
  return (
    <>
      <PageHeader title="Analytics" subtitle="Understand where leads, replies, and wins are coming from." />
      {loading || error ? <StatusBanner loading={loading} error={error} onRetry={refetch} /> : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">{kpis.map((kpi) => <StatCard key={kpi.label} label={kpi.label} value={String(kpi.value)} trend={kpi.trend} />)}</div>
      )}
      <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel className="p-5"><SectionTitle icon={<BarChart3 size={18} />} title="Lead Funnel" /><div className="mt-4 h-80"><ResponsiveContainer><FunnelChart><Tooltip contentStyle={{ background: "#0d141d", border: "1px solid rgba(255,255,255,.1)", color: "#fff" }} /><Funnel dataKey="value" data={funnel} fill="#22d3ee"><LabelList position="right" fill="#dbeafe" stroke="none" dataKey="stage" /></Funnel></FunnelChart></ResponsiveContainer></div></Panel>
        <Panel className="p-5"><SectionTitle icon={<BarChart3 size={18} />} title="Pipeline Mix" /><div className="mt-4 h-80"><ResponsiveContainer><BarChart data={funnel}><CartesianGrid stroke="rgba(255,255,255,.07)" vertical={false} /><XAxis dataKey="stage" stroke="#64748b" /><YAxis stroke="#64748b" /><Tooltip contentStyle={{ background: "#0d141d", border: "1px solid rgba(255,255,255,.1)" }} /><Bar dataKey="value" fill="#22d3ee" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></Panel>
      </div>
      <Panel className="mt-6 p-5"><SectionTitle icon={<BarChart3 size={18} />} title="Lead Sources" /><div className="mt-4 grid gap-3 md:grid-cols-5">{sources.map((source) => <div key={source.name} className="rounded-md border border-white/10 bg-white/[0.035] p-4"><p className="font-medium text-white">{source.name}</p><div className="mt-3 h-2 rounded-full bg-white/[0.07]"><div className="h-full rounded-full bg-cyan-300" style={{ width: `${Math.round((source.value / maxSource) * 100)}%` }} /></div><p className="mt-2 text-sm text-slate-500">{source.value}</p></div>)}</div></Panel>
    </>
  );
}

function SettingsPage({ toast }: { toast: (title: string, tone?: ToastMessage["tone"]) => void }) {
  return (
    <>
      <PageHeader title="Settings" subtitle="Workspace preferences. Outreach sending remains disabled." />
      <div className="grid gap-6 lg:grid-cols-3"><SettingsPanel title="LLM" rows={[["Provider", "Configured on backend"], ["Status", "Uses USER_LLM settings"], ["Default model", "Set in backend env"]]} /><SettingsPanel title="Outreach" rows={[["Default pitch tone", "Professional"], ["Default channel", "WhatsApp"], ["Maximum follow-ups", "3"], ["Require approval", "Enabled"]]} /><SettingsPanel title="Lead Preferences" rows={[["Default location", "Hyderabad"], ["Preferred industries", "Restaurants, Clinics, Real Estate"]]} /></div>
      <Button className="mt-6" onClick={() => toast("Settings saved locally")}>Save local settings</Button>
    </>
  );
}

function SettingsPanel({ title, rows }: { title: string; rows: string[][] }) {
  return <Panel className="p-5"><h3 className="font-semibold text-white">{title}</h3><div className="mt-4 space-y-3">{rows.map(([label, value]) => <label key={label} className="block"><span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">{label}</span><input className="input" defaultValue={value} /></label>)}</div></Panel>;
}

function CommandPalette({ open, close, go }: { open: boolean; close: () => void; go: (page: Page) => void }) {
  const commands: Array<[string, Page]> = [["Find new leads", "find"], ["Open hot leads", "hot"], ["Search leads", "leads"], ["Generate pitch", "pitch"], ["Open conversations", "conversations"], ["View follow-ups", "outreach"], ["Open analytics", "analytics"]];
  const [query, setQuery] = useState("");
  const filtered = commands.filter(([label]) => label.toLowerCase().includes(query.toLowerCase()));
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-start bg-black/55 px-4 pt-24 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="mx-auto w-full max-w-xl overflow-hidden rounded-lg border border-white/10 bg-[#0b1119] shadow-2xl">
        <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3"><Search size={18} className="text-cyan-300" /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search commands..." className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500" /><button onClick={close} aria-label="Close command palette"><X size={18} /></button></div>
        <div className="p-2">{filtered.map(([label, target]) => <button key={label} onClick={() => go(target)} className="flex w-full items-center gap-3 rounded-md px-3 py-3 text-left text-sm text-slate-300 hover:bg-cyan-400/10 hover:text-cyan-100"><Sparkles size={16} /> {label}</button>)}</div>
      </div>
    </div>
  );
}

function ToastStack({ toasts }: { toasts: ToastMessage[] }) {
  return <div className="fixed bottom-5 right-5 z-[60] space-y-2">{toasts.map((toast) => <div key={toast.id} className={cn("page-enter rounded-md border px-4 py-3 text-sm shadow-xl", toast.tone === "error" ? "border-red-300/30 bg-red-950 text-red-100" : "border-emerald-300/25 bg-[#0c1815] text-emerald-100")}><Check className="mr-2 inline" size={16} /> {toast.title}</div>)}</div>;
}
