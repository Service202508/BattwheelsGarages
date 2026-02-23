import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";
import { toast } from "sonner";
import {
  Building2, Users, BarChart3, ShieldAlert, CheckCircle,
  XCircle, TrendingUp, Search, RefreshCw, ChevronRight,
  Crown, Loader2, AlertTriangle, ArrowLeft, Settings
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

export default function PlatformAdmin({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [orgs, setOrgs] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [actionLoading, setActionLoading] = useState({});

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  async function fetchMetrics() {
    const res = await fetch(`${API}/platform/metrics`, { headers });
    if (res.ok) setMetrics(await res.json());
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
    await Promise.all([fetchMetrics(), fetchOrgs()]);
    setLoading(false);
  }

  useEffect(() => { load(); }, [page, planFilter, statusFilter]);

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => fetchOrgs(), 400);
    return () => clearTimeout(t);
  }, [search]);

  async function suspend(orgId, orgName) {
    if (!window.confirm(`Suspend "${orgName}"? All users will lose access.`)) return;
    setActionLoading(p => ({ ...p, [orgId]: "suspending" }));
    const res = await fetch(`${API}/platform/organizations/${orgId}/suspend`, { method: "POST", headers });
    const data = await res.json();
    if (res.ok) {
      toast.success(data.message);
      fetchOrgs();
    } else {
      toast.error(data.detail || "Failed to suspend");
    }
    setActionLoading(p => ({ ...p, [orgId]: null }));
  }

  async function activate(orgId, orgName) {
    setActionLoading(p => ({ ...p, [orgId]: "activating" }));
    const res = await fetch(`${API}/platform/organizations/${orgId}/activate`, { method: "POST", headers });
    const data = await res.json();
    if (res.ok) {
      toast.success(data.message);
      fetchOrgs();
    } else {
      toast.error(data.detail || "Failed to activate");
    }
    setActionLoading(p => ({ ...p, [orgId]: null }));
  }

  async function changePlan(orgId, orgName, newPlan) {
    setActionLoading(p => ({ ...p, [orgId]: "plan" }));
    const res = await fetch(`${API}/platform/organizations/${orgId}/plan`, {
      method: "PUT", headers, body: JSON.stringify({ plan_type: newPlan })
    });
    const data = await res.json();
    if (res.ok) {
      toast.success(data.message);
      fetchOrgs();
    } else {
      toast.error(data.detail || "Failed to change plan");
    }
    setActionLoading(p => ({ ...p, [orgId]: null }));
  }

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
            <button
              onClick={() => navigate("/dashboard")}
              className="text-[rgba(244,246,240,0.45)] hover:text-white transition"
            >
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
          <button
            onClick={load}
            className="flex items-center gap-2 text-xs text-[rgba(244,246,240,0.45)] hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-white/5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Metrics */}
        {metrics && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard icon={Building2} label="Total Organisations" value={metrics.total_organizations} color="emerald" />
            <StatCard icon={CheckCircle} label="Active" value={metrics.active_organizations} sub={`+${metrics.new_this_month} this month`} color="blue" />
            <StatCard icon={Users} label="Platform Users" value={metrics.total_users} color="amber" />
            <StatCard icon={ShieldAlert} label="Suspended" value={metrics.suspended_organizations} color="red" />
          </div>
        )}

        {/* Plan breakdown */}
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

        {/* Organisations table */}
        <div className="bg-[#111827] border border-[rgba(255,255,255,0.07)] rounded-xl overflow-hidden">
          <div className="p-5 border-b border-[rgba(255,255,255,0.07)] flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(244,246,240,0.35)]" />
              <input
                type="text"
                placeholder="Search by name or email…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-[#0D1117] border border-[rgba(255,255,255,0.07)] rounded-lg text-sm text-white placeholder:text-[rgba(244,246,240,0.35)] focus:outline-none focus:border-emerald-500/40"
              />
            </div>
            <select
              value={planFilter}
              onChange={e => { setPlanFilter(e.target.value); setPage(1); }}
              className="px-3 py-2 bg-[#0D1117] border border-[rgba(255,255,255,0.07)] rounded-lg text-sm text-white focus:outline-none"
            >
              <option value="">All Plans</option>
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
            </select>
            <select
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
              className="px-3 py-2 bg-[#0D1117] border border-[rgba(255,255,255,0.07)] rounded-lg text-sm text-white focus:outline-none"
            >
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
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-[rgba(244,246,240,0.35)] text-sm">
                      No organisations found
                    </td>
                  </tr>
                ) : orgs.map(org => (
                  <tr key={org.organization_id} className="border-b border-[rgba(255,255,255,0.04)] hover:bg-white/[0.02] transition">
                    <td className="px-5 py-4">
                      <div>
                        <p className="text-sm font-medium text-white">{org.name}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.35)]">{org.email || org.slug}</p>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <select
                        value={org.plan_type || "free"}
                        onChange={e => changePlan(org.organization_id, org.name, e.target.value)}
                        disabled={!!actionLoading[org.organization_id]}
                        className={`text-xs px-2 py-1 rounded-full border font-medium capitalize cursor-pointer bg-transparent focus:outline-none ${PLAN_COLORS[org.plan_type] || "bg-slate-500/20 text-slate-300"}`}
                      >
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
                    <td className="px-5 py-4 text-xs text-[rgba(244,246,240,0.35)]">
                      {org.created_at ? new Date(org.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        {actionLoading[org.organization_id] ? (
                          <Loader2 className="w-4 h-4 text-[rgba(244,246,240,0.35)] animate-spin" />
                        ) : org.status === "active" ? (
                          <button
                            onClick={() => suspend(org.organization_id, org.name)}
                            className="text-xs px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition"
                          >
                            Suspend
                          </button>
                        ) : (
                          <button
                            onClick={() => activate(org.organization_id, org.name)}
                            className="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition"
                          >
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

          {/* Pagination */}
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
      </div>
    </div>
  );
}
