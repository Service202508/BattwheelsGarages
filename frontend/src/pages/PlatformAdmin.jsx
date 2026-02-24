import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";
import { toast } from "sonner";
import {
  Building2, Users, BarChart3, ShieldAlert, CheckCircle,
  XCircle, TrendingUp, Search, RefreshCw, ChevronRight,
  Crown, Loader2, AlertTriangle, ArrowLeft, Settings,
  IndianRupee, Activity, UserPlus, Flame, Play, X, PhoneCall
} from "lucide-react";

const PLAN_COLORS = {
  enterprise: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  professional: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  starter: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  free: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  free_trial: "bg-amber-500/20 text-amber-300 border-amber-500/30",
};

const STATUS_COLORS = {
  active: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  suspended: "bg-red-500/20 text-red-400 border-red-500/30",
};

function StatCard({ icon: Icon, label, value, sub, color = "emerald" }) {
  const colorMap = {
    emerald: "text-emerald-400 bg-emerald-400/10",
    blue: "text-blue-400 bg-blue-400/10",
    amber: "text-amber-400 bg-amber-400/10",
    red: "text-red-400 bg-red-400/10",
    volt: "text-[#C8FF00] bg-[rgba(200,255,0,0.08)]",
  };
  return (
    <div className="bg-[#111827] border border-[rgba(255,255,255,0.07)] rounded-xl p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
      <p className="text-sm text-[rgba(244,246,240,0.55)] mt-1">{label}</p>
      {sub && <p className="text-xs text-[rgba(244,246,240,0.35)] mt-0.5">{sub}</p>}
    </div>
  );
}

function SectionCard({ title, icon: Icon, iconColor = "text-blue-400", children }) {
  return (
    <div className="bg-[#111827] border border-[rgba(255,255,255,0.07)] rounded-xl p-5">
      <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
        <Icon className={`w-4 h-4 ${iconColor}`} />
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function PlatformAdmin({ user }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("orgs");
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);
  const [orgs, setOrgs] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [actionLoading, setActionLoading] = useState({});

  // Audit state
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [lastAudit, setLastAudit] = useState(null);
  const [showAuditPanel, setShowAuditPanel] = useState(false);

  // Leads state
  const [leads, setLeads] = useState([]);
  const [leadsSummary, setLeadsSummary] = useState(null);
  const [leadsLoading, setLeadsLoading] = useState(false);
  const [expandedNotes, setExpandedNotes] = useState({});

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  async function fetchMetrics() {
    const res = await fetch(`${API}/platform/metrics`, { headers });
    if (res.ok) setMetrics(await res.json());
  }

  async function fetchHealth() {
    const res = await fetch(`${API}/platform/revenue-health`, { headers });
    if (res.ok) setHealth(await res.json());
  }

  async function fetchAuditStatus() {
    const res = await fetch(`${API}/platform/audit-status`, { headers });
    if (res.ok) {
      const data = await res.json();
      if (data.timestamp) setLastAudit(data);
    }
  }

  async function runAudit() {
    setAuditRunning(true);
    setShowAuditPanel(true);
    setAuditResult(null);
    try {
      const res = await fetch(`${API}/platform/run-audit`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        setAuditResult(data);
        setLastAudit(data);
      } else {
        toast.error(data.detail || "Audit failed");
        setShowAuditPanel(false);
      }
    } catch (e) {
      toast.error("Audit request failed");
      setShowAuditPanel(false);
    } finally {
      setAuditRunning(false);
    }
  }

  async function fetchOrgs() {
    const params = new URLSearchParams({ page, limit: 25 });
    if (search) params.set("search", search);
    if (planFilter) params.set("plan", planFilter);
    if (statusFilter) params.set("status", statusFilter);
    const res = await fetch(`${API}/platform/organizations?${params}`, { headers });
    if (res.ok) {
      const data = await res.json();
      setOrgs(data.organizations || []);
      setTotal(data.total || 0);
    } else if (res.status === 403) {
      toast.error("Platform admin access required");
      navigate("/dashboard");
    }
  }

  async function load() {
    setLoading(true);
    await Promise.all([fetchMetrics(), fetchOrgs(), fetchHealth(), fetchAuditStatus()]);
    setLoading(false);
  }

  useEffect(() => { load(); }, [page, planFilter, statusFilter]);

  useEffect(() => {
    const t = setTimeout(() => fetchOrgs(), 400);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    if (activeTab === "leads") fetchLeads();
  }, [activeTab]);

  async function fetchLeads() {
    setLeadsLoading(true);
    try {
      const res = await fetch(`${API}/platform/leads`, { headers });
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads || []);
        setLeadsSummary(data.summary || null);
      }
    } finally {
      setLeadsLoading(false);
    }
  }

  async function updateLeadStatus(leadId, status) {
    const res = await fetch(`${API}/platform/leads/${leadId}/status`, {
      method: "PATCH", headers, body: JSON.stringify({ status })
    });
    if (res.ok) {
      setLeads(prev => prev.map(l => l.lead_id === leadId ? { ...l, status } : l));
      setLeadsSummary(null); // trigger re-fetch of summary on next visit
    } else {
      toast.error("Failed to update status");
    }
  }

  async function saveLeadNotes(leadId, notes) {
    await fetch(`${API}/platform/leads/${leadId}/notes`, {
      method: "PATCH", headers, body: JSON.stringify({ notes })
    });
  }

  async function suspend(orgId, orgName) {
    if (!window.confirm(`Suspend "${orgName}"? All users will lose access.`)) return;
    setActionLoading(p => ({ ...p, [orgId]: "suspending" }));
    const res = await fetch(`${API}/platform/organizations/${orgId}/suspend`, { method: "POST", headers });
    const data = await res.json();
    if (res.ok) { toast.success(data.message); fetchOrgs(); }
    else toast.error(data.detail || "Failed to suspend");
    setActionLoading(p => ({ ...p, [orgId]: null }));
  }

  async function activate(orgId, orgName) {
    setActionLoading(p => ({ ...p, [orgId]: "activating" }));
    const res = await fetch(`${API}/platform/organizations/${orgId}/activate`, { method: "POST", headers });
    const data = await res.json();
    if (res.ok) { toast.success(data.message); fetchOrgs(); }
    else toast.error(data.detail || "Failed to activate");
    setActionLoading(p => ({ ...p, [orgId]: null }));
  }

  async function changePlan(orgId, orgName, newPlan) {
    setActionLoading(p => ({ ...p, [orgId]: "plan" }));
    const res = await fetch(`${API}/platform/organizations/${orgId}/plan`, {
      method: "PUT", headers, body: JSON.stringify({ plan_type: newPlan })
    });
    const data = await res.json();
    if (res.ok) { toast.success(data.message); fetchOrgs(); }
    else toast.error(data.detail || "Failed to change plan");
    setActionLoading(p => ({ ...p, [orgId]: null }));
  }

  const fmtINR = (n) => n >= 1000
    ? `₹${(n / 1000).toFixed(1)}k`
    : `₹${n}`;

  const fmtDate = (d) => d
    ? new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
    : "—";

  const fmtAgo = (iso) => {
    if (!iso) return null;
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#080C0F] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#080C0F] text-[rgba(244,246,240,0.87)]">
      {/* Header */}
      <div className="border-b border-[rgba(255,255,255,0.07)] bg-[#0D1117] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate("/dashboard")} className="text-[rgba(244,246,240,0.45)] hover:text-white transition">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <Crown className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <h1 className="font-semibold text-white text-sm">Platform Admin</h1>
              <p className="text-xs text-[rgba(244,246,240,0.35)]">Battwheels OS — Operator Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Run Audit button */}
            <div className="flex flex-col items-end gap-0.5">
              <button
                data-testid="run-audit-btn"
                onClick={runAudit}
                disabled={auditRunning}
                style={{
                  background: "transparent",
                  border: "1px solid rgba(200,255,0,0.30)",
                  color: "#C8FF00",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: "11px",
                  letterSpacing: "0.08em",
                  padding: "6px 14px",
                  borderRadius: "4px",
                  cursor: auditRunning ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  opacity: auditRunning ? 0.7 : 1,
                  transition: "border-color 0.15s, opacity 0.15s",
                }}
              >
                {auditRunning ? (
                  <Loader2 style={{ width: "11px", height: "11px", animation: "spin 1s linear infinite" }} />
                ) : (
                  <Play style={{ width: "11px", height: "11px" }} />
                )}
                {auditRunning ? "Running..." : "Run Audit"}
              </button>
              {lastAudit && !auditRunning && (
                <span
                  data-testid="audit-last-run"
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: "10px",
                    color: "rgba(244,246,240,0.30)",
                  }}
                >
                  Last audit: {fmtAgo(lastAudit.timestamp)} · {lastAudit.passed}/{lastAudit.total}
                </span>
              )}
            </div>

            <button onClick={load} className="flex items-center gap-2 text-xs text-[rgba(244,246,240,0.45)] hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-white/5">
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Audit Result Panel */}
      {showAuditPanel && (
        <div className="border-b border-[rgba(255,255,255,0.07)] bg-[#0D1117] px-6 py-4">
          <div className="max-w-7xl mx-auto">
            {auditRunning ? (
              <div
                style={{
                  background: "rgba(200,255,0,0.04)",
                  border: "1px solid rgba(200,255,0,0.15)",
                  borderRadius: "4px",
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <Loader2 style={{ width: "16px", height: "16px", color: "#C8FF00", flexShrink: 0, animation: "spin 1s linear infinite" }} />
                <div>
                  <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "13px", color: "#C8FF00", margin: 0 }}>
                    Running 103-test audit…
                  </p>
                  <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "rgba(244,246,240,0.35)", margin: "2px 0 0 0" }}>
                    This takes ~30–60 seconds
                  </p>
                </div>
              </div>
            ) : auditResult && (
              <div
                data-testid="audit-result-panel"
                style={{
                  background: auditResult.failed === 0 ? "rgba(34,197,94,0.08)" : "rgba(255,59,47,0.08)",
                  border: `1px solid ${auditResult.failed === 0 ? "rgba(34,197,94,0.20)" : "rgba(255,59,47,0.25)"}`,
                  borderRadius: "4px",
                  padding: "16px 20px",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                  <div style={{ flex: 1 }}>
                    <p style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: "14px",
                      color: auditResult.failed === 0 ? "#22C55E" : "#FF3B2F",
                      margin: 0,
                      fontWeight: 600,
                    }}>
                      {auditResult.failed === 0
                        ? `✅ ${auditResult.passed}/${auditResult.total} — All systems operational`
                        : `⚠️ ${auditResult.passed}/${auditResult.total} — ${auditResult.failed} failure${auditResult.failed !== 1 ? "s" : ""} detected`}
                    </p>
                    <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "rgba(244,246,240,0.40)", margin: "4px 0 0 0" }}>
                      Completed in {auditResult.duration_seconds}s · {new Date(auditResult.timestamp).toLocaleTimeString()}
                    </p>

                    {auditResult.failed > 0 && auditResult.failures && auditResult.failures.length > 0 && (
                      <div style={{ marginTop: "12px" }}>
                        <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "rgba(244,246,240,0.50)", marginBottom: "6px" }}>
                          FAILED TESTS:
                        </p>
                        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                          {auditResult.failures.map((f, i) => (
                            <div key={i} style={{
                              background: "rgba(255,59,47,0.06)",
                              border: "1px solid rgba(255,59,47,0.15)",
                              borderRadius: "3px",
                              padding: "6px 10px",
                              display: "flex",
                              alignItems: "flex-start",
                              gap: "8px",
                            }}>
                              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#FF3B2F", flexShrink: 0 }}>
                                T{String(f.n).padStart(2, "0")}.
                              </span>
                              <div>
                                <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "rgba(244,246,240,0.80)", margin: 0 }}>{f.test}</p>
                                <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "10px", color: "rgba(244,246,240,0.40)", margin: "1px 0 0 0" }}>{f.error}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setShowAuditPanel(false)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(244,246,240,0.35)", padding: "0 0 0 16px", flexShrink: 0 }}
                  >
                    <X style={{ width: "14px", height: "14px" }} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* KPI strip */}
        {metrics && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard icon={Building2} label="Total Organisations" value={metrics.total_organizations} color="emerald" />
            <StatCard icon={CheckCircle} label="Active" value={metrics.active_organizations} sub={`+${metrics.new_this_month} this month`} color="blue" />
            <StatCard icon={Users} label="Platform Users" value={metrics.total_users} color="amber" />
            <StatCard icon={IndianRupee} label="MRR" value={health ? fmtINR(health.total_mrr) : "—"} sub="Monthly Recurring Revenue" color="volt" />
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 bg-[#111827] border border-[rgba(255,255,255,0.07)] rounded-xl p-1 w-fit">
          {[
            { id: "orgs",    label: "Organisations",    icon: Building2 },
            { id: "health",  label: "Revenue & Health", icon: TrendingUp },
            { id: "leads",   label: "Leads",            icon: PhoneCall },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === tab.id
                  ? "bg-[#0D1117] text-white border border-[rgba(255,255,255,0.07)]"
                  : "text-[rgba(244,246,240,0.45)] hover:text-white"
              }`}
              data-testid={`tab-${tab.id}`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── TAB: ORGANISATIONS ── */}
        {activeTab === "orgs" && (
          <>
            {metrics?.organizations_by_plan && (
              <div className="bg-[#111827] border border-[rgba(255,255,255,0.07)] rounded-xl p-5">
                <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-400" />
                  Organisations by Plan
                </h3>
                <div className="flex flex-wrap gap-3">
                  {Object.entries(metrics.organizations_by_plan).map(([plan, count]) => (
                    <div key={plan} className="flex items-center gap-2 px-3 py-1.5 bg-[#0D1117] rounded-lg border border-[rgba(255,255,255,0.07)]">
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${PLAN_COLORS[plan] || "bg-slate-500/20 text-slate-300"}`}>{plan}</span>
                      <span className="text-white font-semibold text-sm">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-[#111827] border border-[rgba(255,255,255,0.07)] rounded-xl overflow-hidden">
              <div className="p-5 border-b border-[rgba(255,255,255,0.07)] flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(244,246,240,0.35)]" />
                  <input type="text" placeholder="Search by name or email…" value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-[#0D1117] border border-[rgba(255,255,255,0.07)] rounded-lg text-sm text-white placeholder:text-[rgba(244,246,240,0.35)] focus:outline-none focus:border-emerald-500/40"
                  />
                </div>
                <select value={planFilter} onChange={e => { setPlanFilter(e.target.value); setPage(1); }}
                  className="px-3 py-2 bg-[#0D1117] border border-[rgba(255,255,255,0.07)] rounded-lg text-sm text-white focus:outline-none">
                  <option value="">All Plans</option>
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="professional">Professional</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
                  className="px-3 py-2 bg-[#0D1117] border border-[rgba(255,255,255,0.07)] rounded-lg text-sm text-white focus:outline-none">
                  <option value="">All Status</option>
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[rgba(255,255,255,0.05)]">
                      {["Organisation", "Plan", "Status", "Members", "Created", "Actions"].map(h => (
                        <th key={h} className="text-left text-xs font-medium text-[rgba(244,246,240,0.35)] px-5 py-3 uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {orgs.length === 0 ? (
                      <tr><td colSpan={6} className="text-center py-12 text-[rgba(244,246,240,0.35)] text-sm">No organisations found</td></tr>
                    ) : orgs.map(org => (
                      <tr key={org.organization_id} className="border-b border-[rgba(255,255,255,0.04)] hover:bg-white/[0.02] transition">
                        <td className="px-5 py-4">
                          <div>
                            <p className="text-sm font-medium text-white">{org.name}</p>
                            <p className="text-xs text-[rgba(244,246,240,0.35)]">{org.email || org.slug}</p>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <select value={org.plan_type || "free"}
                            onChange={e => changePlan(org.organization_id, org.name, e.target.value)}
                            disabled={!!actionLoading[org.organization_id]}
                            className={`text-xs px-2 py-1 rounded-full border font-medium capitalize cursor-pointer bg-transparent focus:outline-none ${PLAN_COLORS[org.plan_type] || "bg-slate-500/20 text-slate-300"}`}>
                            {["free", "starter", "professional", "enterprise"].map(p => (
                              <option key={p} value={p} className="bg-[#1a2433] capitalize">{p}</option>
                            ))}
                          </select>
                        </td>
                        <td className="px-5 py-4">
                          <span className={`text-xs px-2 py-1 rounded-full border font-medium capitalize ${STATUS_COLORS[org.status] || ""}`}>
                            {org.status}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-sm text-[rgba(244,246,240,0.55)]">{org.member_count}</td>
                        <td className="px-5 py-4 text-xs text-[rgba(244,246,240,0.35)]">{fmtDate(org.created_at)}</td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            {actionLoading[org.organization_id] ? (
                              <Loader2 className="w-4 h-4 text-[rgba(244,246,240,0.35)] animate-spin" />
                            ) : org.status === "active" ? (
                              <button onClick={() => suspend(org.organization_id, org.name)}
                                className="text-xs px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition">
                                Suspend
                              </button>
                            ) : (
                              <button onClick={() => activate(org.organization_id, org.name)}
                                className="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition">
                                Activate
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {total > 25 && (
                <div className="px-5 py-4 border-t border-[rgba(255,255,255,0.07)] flex items-center justify-between text-sm text-[rgba(244,246,240,0.45)]">
                  <span>{total} total organisations</span>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-30 transition">Prev</button>
                    <span>Page {page}</span>
                    <button onClick={() => setPage(p => p + 1)} disabled={orgs.length < 25} className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-30 transition">Next</button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* ── TAB: REVENUE & HEALTH ── */}
        {activeTab === "health" && health && (
          <div className="space-y-6">
            {/* MRR summary */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StatCard icon={IndianRupee} label="Total MRR" value={fmtINR(health.total_mrr)} sub="Monthly Recurring Revenue" color="volt" />
              <StatCard icon={Activity}    label="Trial Pipeline" value={health.trial_pipeline.count} sub="Free & trial orgs" color="amber" />
              <StatCard icon={Flame}        label="Churn Risk" value={health.churn_risk.count} sub="Inactive 30+ days" color="red" />
            </div>

            {/* MRR by plan */}
            <SectionCard title="MRR by Plan Tier" icon={BarChart3} iconColor="text-[#C8FF00]">
              {health.mrr_by_plan.length === 0 ? (
                <p className="text-sm text-[rgba(244,246,240,0.35)]">No paid plans yet</p>
              ) : (
                <div className="space-y-3">
                  {health.mrr_by_plan.map(item => {
                    const pct = health.total_mrr > 0 ? (item.mrr / health.total_mrr) * 100 : 0;
                    return (
                      <div key={item.plan}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${PLAN_COLORS[item.plan] || "bg-slate-500/20 text-slate-300"}`}>
                              {item.plan}
                            </span>
                            <span className="text-xs text-[rgba(244,246,240,0.45)]">{item.count} org{item.count !== 1 ? "s" : ""}</span>
                          </div>
                          <span className="text-sm font-semibold text-white">{fmtINR(item.mrr)}<span className="text-[rgba(244,246,240,0.35)] text-xs">/mo</span></span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-[#C8FF00] rounded-full" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </SectionCard>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Trial pipeline */}
              <SectionCard title={`Trial Pipeline (${health.trial_pipeline.count})`} icon={TrendingUp} iconColor="text-amber-400">
                {health.trial_pipeline.count === 0 ? (
                  <p className="text-sm text-[rgba(244,246,240,0.35)]">No free/trial orgs — all customers are on paid plans.</p>
                ) : (
                  <div className="space-y-2">
                    {health.trial_pipeline.orgs.map((org, i) => (
                      <div key={i} className="flex items-center justify-between py-2 border-b border-[rgba(255,255,255,0.04)] last:border-0">
                        <div>
                          <p className="text-sm text-white">{org.name}</p>
                          <p className="text-xs text-[rgba(244,246,240,0.35)]">{fmtDate(org.created_at)}</p>
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${PLAN_COLORS[org.plan_type] || ""}`}>{org.plan_type}</span>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>

              {/* Churn risk */}
              <SectionCard title={`Churn Risk (${health.churn_risk.count})`} icon={AlertTriangle} iconColor="text-red-400">
                {health.churn_risk.count === 0 ? (
                  <p className="text-sm text-[rgba(244,246,240,0.35)]">No orgs at risk — all have recent activity.</p>
                ) : (
                  <div className="space-y-2">
                    {health.churn_risk.orgs.map((org, i) => (
                      <div key={i} className="flex items-center justify-between py-2 border-b border-[rgba(255,255,255,0.04)] last:border-0">
                        <div>
                          <p className="text-sm text-white">{org.name}</p>
                          <p className="text-xs text-red-400">{org.last_activity}</p>
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${PLAN_COLORS[org.plan] || ""}`}>{org.plan}</span>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>

            {/* Recent signups */}
            <SectionCard title="Recent Signups" icon={UserPlus} iconColor="text-emerald-400">
              {health.recent_signups.length === 0 ? (
                <p className="text-sm text-[rgba(244,246,240,0.35)]">No signups yet</p>
              ) : (
                <div className="divide-y divide-[rgba(255,255,255,0.04)]">
                  {health.recent_signups.map((org, i) => (
                    <div key={i} className="flex items-center justify-between py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center">
                          <Building2 className="w-4 h-4 text-emerald-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">{org.name}</p>
                          <p className="text-xs text-[rgba(244,246,240,0.35)]">{org.email || "—"}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${PLAN_COLORS[org.plan_type] || "bg-slate-500/20 text-slate-300"}`}>
                          {org.plan_type || "free"}
                        </span>
                        <p className="text-xs text-[rgba(244,246,240,0.35)] mt-1">{fmtDate(org.created_at)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          </div>
        )}
        {/* ── TAB: LEADS ── */}
        {activeTab === "leads" && (
          <div className="space-y-5" data-testid="leads-tab">
            {/* Summary row */}
            {leadsSummary && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard icon={PhoneCall}    label="Total Leads"     value={leadsSummary.total}          color="blue" />
                <StatCard icon={UserPlus}     label="New This Week"   value={leadsSummary.new_this_week}  color="amber" />
                <StatCard icon={CheckCircle}  label="Qualified"       value={leadsSummary.qualified}      color="volt" />
                <StatCard icon={TrendingUp}   label="Conversion Rate" value={`${leadsSummary.conversion_rate}%`} sub={`${leadsSummary.closed_won} closed won`} color="emerald" />
              </div>
            )}

            {/* Leads table */}
            <div className="bg-[#111827] border border-[rgba(255,255,255,0.07)] rounded-xl overflow-hidden">
              <div className="p-5 border-b border-[rgba(255,255,255,0.07)] flex items-center justify-between">
                <h3 className="text-sm font-medium text-white flex items-center gap-2">
                  <PhoneCall className="w-4 h-4 text-[#C8FF00]" />
                  Demo Requests
                </h3>
                <button onClick={fetchLeads} className="text-xs text-[rgba(244,246,240,0.45)] hover:text-white flex items-center gap-1 transition" data-testid="refresh-leads-btn">
                  <RefreshCw className="w-3 h-3" /> Refresh
                </button>
              </div>

              {leadsLoading ? (
                <div className="flex justify-center items-center h-40">
                  <Loader2 className="w-6 h-6 animate-spin text-[rgba(244,246,240,0.35)]" />
                </div>
              ) : leads.length === 0 ? (
                <div className="text-center py-16 text-[rgba(244,246,240,0.35)] text-sm">
                  No demo requests yet. They'll appear here when prospects click "Book Demo".
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-[rgba(255,255,255,0.05)]">
                        {["Date", "Name", "Workshop", "City", "Phone", "Fleet Size", "Status", "Notes"].map(h => (
                          <th key={h} className="text-left text-xs font-medium text-[rgba(244,246,240,0.35)] px-4 py-3 uppercase tracking-wider whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {leads.map(lead => (
                        <LeadRow
                          key={lead.lead_id}
                          lead={lead}
                          expanded={expandedNotes[lead.lead_id]}
                          onToggleNotes={() => setExpandedNotes(prev => ({ ...prev, [lead.lead_id]: !prev[lead.lead_id] }))}
                          onStatusChange={(status) => updateLeadStatus(lead.lead_id, status)}
                          onNotesSave={(notes) => saveLeadNotes(lead.lead_id, notes)}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
