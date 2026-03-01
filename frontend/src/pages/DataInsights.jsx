import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import {
  TrendingUp, TrendingDown, Minus, IndianRupee, Ticket, Clock,
  Users, Star, Package, AlertTriangle, Zap, Target, Award,
  BarChart3, Activity, Calendar, RefreshCw, ChevronRight,
  Cpu, ShoppingCart, Boxes
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

// ─── Constants ──────────────────────────────────────────────────────────────
const VOLT = "#C8FF00";
const VOLT_DIM = "rgba(200,255,0,0.08)";
const VOLT_BORDER = "rgba(200,255,0,0.20)";
const CYAN = "#1AFFE4";
const AMBER = "#EAB308";
const RED = "#EF4444";
const BLUE = "#3B9EFF";
const GRID = "rgba(255,255,255,0.05)";
const DIM_TEXT = "rgba(244,246,240,0.45)";
const CHART_COLORS = [VOLT, CYAN, AMBER, BLUE, "#A78BFA", "#F472B6"];

const PERIODS = [
  { label: "This Week", value: "week" },
  { label: "This Month", value: "month" },
  { label: "This Quarter", value: "quarter" },
  { label: "Custom", value: "custom" },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getDateRange(period) {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const today = fmt(now);

  if (period === "week") {
    const d = new Date(now);
    d.setDate(d.getDate() - d.getDay());
    return { from: fmt(d), to: today };
  }
  if (period === "month") {
    return { from: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`, to: today };
  }
  if (period === "quarter") {
    const qStart = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
    return { from: fmt(qStart), to: today };
  }
  return null;
}

function fmtCurrency(val) {
  if (val === null || val === undefined) return "—";
  if (val >= 1_00_00_000) return `₹${(val / 1_00_00_000).toFixed(1)}Cr`;
  if (val >= 1_00_000) return `₹${(val / 1_00_000).toFixed(1)}L`;
  if (val >= 1_000) return `₹${(val / 1_000).toFixed(1)}K`;
  return `₹${val.toFixed(0)}`;
}

function fmtNum(val) {
  if (val === null || val === undefined) return "—";
  return val.toLocaleString("en-IN");
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const ChartTooltipStyle = {
  backgroundColor: "#1a1f24",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: "8px",
  color: "rgb(var(--bw-white))",
  fontSize: 12,
};

function CustomTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={ChartTooltipStyle} className="px-3 py-2">
      <p className="text-xs mb-1" style={{ color: DIM_TEXT }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || VOLT }} className="text-xs font-medium">
          {p.name}: {formatter ? formatter(p.value) : p.value}
        </p>
      ))}
    </div>
  );
}

function Delta({ val, suffix = "%" }) {
  if (val === null || val === undefined) return null;
  const up = val >= 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-medium ${up ? "text-green-400" : "text-red-400"}`}>
      {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
      {up ? "+" : ""}{val}{suffix}
    </span>
  );
}

function KpiCard({ icon: Icon, label, value, delta, sub, color = VOLT, warn = false, testId }) {
  return (
    <Card
      data-testid={testId}
      className="border relative overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.02)",
        borderColor: warn ? "rgba(234,179,8,0.3)" : "rgba(255,255,255,0.07)",
      }}
    >
      <CardContent className="pt-4 pb-4 px-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-xs mb-1 truncate" style={{ color: DIM_TEXT }}>{label}</p>
            <p className="text-xl font-bold tracking-tight" style={{ color, fontFamily: "Syne, sans-serif" }}>
              {value}
            </p>
            {(delta !== null && delta !== undefined) && (
              <div className="mt-1"><Delta val={delta} /></div>
            )}
            {sub && <p className="text-xs mt-1 truncate" style={{ color: DIM_TEXT }}>{sub}</p>}
          </div>
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: `${color}18`, border: `1px solid ${color}30` }}
          >
            <Icon size={16} style={{ color }} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SectionHeader({ icon: Icon, title, sub }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div
        className="w-9 h-9 rounded-lg flex items-center justify-center"
        style={{ background: VOLT_DIM, border: `1px solid ${VOLT_BORDER}` }}
      >
        <Icon size={16} style={{ color: VOLT }} />
      </div>
      <div>
        <h2 className="text-base font-semibold" style={{ fontFamily: "Syne, sans-serif", color: "rgb(var(--bw-white))" }}>
          {title}
        </h2>
        {sub && <p className="text-xs" style={{ color: DIM_TEXT }}>{sub}</p>}
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, message, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
        style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
      >
        <Icon size={20} style={{ color: DIM_TEXT }} />
      </div>
      <p className="text-sm mb-1" style={{ color: DIM_TEXT }}>No data yet for this period</p>
      {action && <p className="text-xs" style={{ color: DIM_TEXT }}>{action}</p>}
    </div>
  );
}

function LoadingCard({ rows = 3 }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-6 w-full bg-white/5 rounded" />
      ))}
    </div>
  );
}

// ─── Section 1: Revenue Intelligence ──────────────────────────────────────────
function RevenueSection({ data, loading }) {
  if (loading) return <LoadingCard rows={5} />;
  if (!data) return <EmptyState icon={IndianRupee} message="No data" action="Create your first invoice to see revenue data" />;

  const { kpis, trend, by_type } = data;
  const hasData = kpis.paid_count > 0;

  return (
    <div className="space-y-5" data-testid="revenue-section">
      {/* KPI Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          icon={IndianRupee}
          label="Revenue This Period"
          value={fmtCurrency(kpis.revenue)}
          delta={kpis.revenue_delta}
          color={VOLT}
          testId="revenue-kpi-revenue"
        />
        <KpiCard
          icon={BarChart3}
          label="Avg Invoice Value"
          value={fmtCurrency(kpis.avg_invoice)}
          delta={kpis.avg_invoice_delta}
          color={CYAN}
          testId="revenue-kpi-avg"
        />
        <KpiCard
          icon={Target}
          label="Collection Rate"
          value={kpis.collection_rate != null ? `${kpis.collection_rate}%` : "—"}
          sub={`${kpis.paid_count} of ${kpis.total_count} invoices`}
          color={kpis.collection_rate < 60 ? RED : kpis.collection_rate < 80 ? AMBER : VOLT}
          warn={kpis.collection_rate < 80}
          testId="revenue-kpi-collection"
        />
        <KpiCard
          icon={AlertTriangle}
          label="Outstanding AR"
          value={fmtCurrency(kpis.ar)}
          color={AMBER}
          warn={kpis.ar > 0}
          testId="revenue-kpi-ar"
        />
      </div>

      {/* Charts */}
      {!hasData ? (
        <EmptyState icon={TrendingUp} action="Mark invoices as paid to see revenue trends" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Revenue Trend */}
          <Card className="lg:col-span-2 border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Revenue Trend</CardTitle>
            </CardHeader>
            <CardContent className="px-2 pb-4">
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={trend} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={VOLT} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={VOLT} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v) => fmtCurrency(v)} width={55} />
                  <Tooltip content={<CustomTooltip formatter={fmtCurrency} />} />
                  <Line type="monotone" dataKey="revenue" stroke={VOLT} strokeWidth={2} dot={false} name="Revenue" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* By Service Type */}
          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>By Service Type</CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-4 space-y-3">
              {by_type.length === 0 ? (
                <EmptyState icon={BarChart3} />
              ) : (
                by_type.map((item, i) => {
                  const max = Math.max(...by_type.map((b) => b.revenue));
                  const pct = max > 0 ? (item.revenue / max) * 100 : 0;
                  return (
                    <div key={i}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs" style={{ color: "rgb(var(--bw-white))" }}>{item.type}</span>
                        <span className="text-xs font-semibold" style={{ color: VOLT }}>{fmtCurrency(item.revenue)}</span>
                      </div>
                      <div className="h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
                        <div
                          className="h-1.5 rounded-full transition-all"
                          style={{ width: `${pct}%`, background: CHART_COLORS[i % CHART_COLORS.length] }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// ─── Section 2: Workshop Operations ───────────────────────────────────────────
function OperationsSection({ data, loading }) {
  if (loading) return <LoadingCard rows={5} />;
  if (!data) return <EmptyState icon={Ticket} action="Start tracking tickets to see performance" />;

  const { kpis, volume, vehicle_dist } = data;
  const hasData = kpis.total_tickets > 0;

  const slaColor = kpis.sla_compliance_rate == null ? DIM_TEXT :
    kpis.sla_compliance_rate >= 90 ? VOLT : kpis.sla_compliance_rate >= 70 ? AMBER : RED;

  return (
    <div className="space-y-5" data-testid="operations-section">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard icon={Ticket} label="Tickets Resolved" value={fmtNum(kpis.tickets_resolved)} delta={kpis.tickets_delta} color={VOLT} testId="ops-kpi-resolved" />
        <KpiCard icon={Clock} label="Avg Resolution" value={kpis.avg_resolution_hours != null ? `${kpis.avg_resolution_hours}h` : "—"} color={CYAN} testId="ops-kpi-avg-time" />
        <KpiCard
          icon={Target}
          label="SLA Compliance"
          value={kpis.sla_compliance_rate != null ? `${kpis.sla_compliance_rate}%` : "—"}
          sub="Target: 90%+"
          color={slaColor}
          warn={kpis.sla_compliance_rate != null && kpis.sla_compliance_rate < 90}
          testId="ops-kpi-sla"
        />
        <KpiCard icon={Award} label="First-Time Fix" value={kpis.first_fix_rate != null ? `${kpis.first_fix_rate}%` : "—"} color={BLUE} testId="ops-kpi-firstfix" />
      </div>

      {!hasData ? (
        <EmptyState icon={Activity} action="Start tracking tickets to see operations data" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2 border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Daily Ticket Volume</CardTitle>
            </CardHeader>
            <CardContent className="px-2 pb-4">
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={volume} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="closed" name="Closed" stackId="a" fill={VOLT} radius={[0, 0, 0, 0]} />
                  <Bar dataKey="in_progress" name="In Progress" stackId="a" fill={AMBER} />
                  <Bar dataKey="open" name="Open" stackId="a" fill={BLUE} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Vehicle Type Mix</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center pb-4">
              {vehicle_dist.length === 0 ? (
                <EmptyState icon={BarChart3} />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={140}>
                    <PieChart>
                      <Pie data={vehicle_dist} dataKey="count" nameKey="type" cx="50%" cy="50%" innerRadius={38} outerRadius={58} paddingAngle={3}>
                        {vehicle_dist.map((_, i) => (
                          <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v, n) => [v, n]} contentStyle={ChartTooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1 w-full px-2">
                    {vehicle_dist.map((v, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                          <span style={{ color: "rgb(var(--bw-white))" }}>{v.type}</span>
                        </span>
                        <span style={{ color: DIM_TEXT }}>{v.count}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// ─── Section 3: Technician Performance ────────────────────────────────────────
function TechnicianSection({ data, loading }) {
  const [sortBy, setSortBy] = useState("tickets_closed");
  if (loading) return <LoadingCard rows={5} />;
  if (!data) return <EmptyState icon={Users} action="Assign technicians to tickets to see performance data" />;

  const { leaderboard, heatmap, vehicle_types } = data;
  if (!leaderboard.length) return <EmptyState icon={Users} action="Close some tickets with assigned technicians to see this" />;

  const sorted = [...leaderboard].sort((a, b) => (b[sortBy] ?? -1) - (a[sortBy] ?? -1));

  const maxTickets = Math.max(...leaderboard.map((t) => t.tickets_closed));

  return (
    <div className="space-y-5" data-testid="technician-section">
      {/* Leaderboard */}
      <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
        <CardHeader className="pb-2 pt-4 px-4 flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Technician Leaderboard</CardTitle>
          <div className="flex gap-1 flex-wrap">
            {["tickets_closed", "avg_hours", "avg_rating", "sla_compliance"].map((k) => (
              <button
                key={k}
                onClick={() => setSortBy(k)}
                className="px-2 py-0.5 rounded text-xs transition-all"
                style={{
                  background: sortBy === k ? VOLT_DIM : "transparent",
                  color: sortBy === k ? VOLT : DIM_TEXT,
                  border: `1px solid ${sortBy === k ? VOLT_BORDER : "transparent"}`,
                }}
              >
                {k === "tickets_closed" ? "Tickets" : k === "avg_hours" ? "Speed" : k === "avg_rating" ? "Rating" : "SLA"}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                  {["#", "Technician", "Resolved", "Avg Time", "Rating", "SLA %"].map((h) => (
                    <th key={h} className="pb-2 pr-3 text-left font-medium" style={{ color: DIM_TEXT }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((tech, i) => {
                  const isTop = i === 0;
                  const isLow = tech.avg_rating != null && tech.avg_rating < 3;
                  return (
                    <tr
                      key={tech.id}
                      data-testid={`tech-row-${tech.id}`}
                      style={{
                        borderLeft: isTop ? `3px solid ${VOLT}` : isLow ? `3px solid ${RED}` : "3px solid transparent",
                        borderBottom: "1px solid rgba(255,255,255,0.04)",
                      }}
                    >
                      <td className="py-2 pr-3 pl-2" style={{ color: DIM_TEXT }}>{i + 1}</td>
                      <td className="py-2 pr-3 font-medium" style={{ color: "rgb(var(--bw-white))" }}>{tech.name}</td>
                      <td className="py-2 pr-3">
                        <div className="flex items-center gap-1.5">
                          <div className="h-1 rounded-full" style={{ width: 40, background: "rgba(255,255,255,0.06)" }}>
                            <div className="h-1 rounded-full" style={{ width: `${maxTickets > 0 ? (tech.tickets_closed / maxTickets) * 40 : 0}px`, background: VOLT }} />
                          </div>
                          <span style={{ color: VOLT }}>{tech.tickets_closed}</span>
                        </div>
                      </td>
                      <td className="py-2 pr-3" style={{ color: "rgb(var(--bw-white))" }}>
                        {tech.avg_hours != null ? `${tech.avg_hours}h` : "—"}
                      </td>
                      <td className="py-2 pr-3" style={{ color: AMBER }}>
                        {tech.avg_rating != null ? (
                          <span>{tech.avg_rating} <span style={{ color: DIM_TEXT }}>★</span></span>
                        ) : "—"}
                      </td>
                      <td className="py-2" style={{ color: tech.sla_compliance != null && tech.sla_compliance >= 90 ? VOLT : tech.sla_compliance != null ? AMBER : DIM_TEXT }}>
                        {tech.sla_compliance != null ? `${tech.sla_compliance}%` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Specialisation Heatmap */}
      {heatmap.length > 0 && vehicle_types.length > 0 && (
        <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Specialisation Map</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 overflow-x-auto">
            <table className="text-xs">
              <thead>
                <tr>
                  <th className="pb-2 pr-4 text-left font-medium" style={{ color: DIM_TEXT, minWidth: 120 }}>Technician</th>
                  {vehicle_types.map((v) => (
                    <th key={v} className="pb-2 px-2 text-center font-medium" style={{ color: DIM_TEXT, minWidth: 70 }}>{v}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {heatmap.map((row) => {
                  const max = Math.max(...vehicle_types.map((v) => row[v] || 0));
                  return (
                    <tr key={row.tech_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <td className="py-2 pr-4 font-medium" style={{ color: "rgb(var(--bw-white))" }}>{row.tech_name}</td>
                      {vehicle_types.map((v) => {
                        const cnt = row[v] || 0;
                        const intensity = max > 0 ? cnt / max : 0;
                        return (
                          <td key={v} className="py-2 px-2 text-center" style={{
                            background: `rgba(200,255,0,${intensity * 0.4})`,
                            color: intensity > 0.5 ? "#0a0f0d" : "#f4f6f0",
                            borderRadius: 4,
                          }}>
                            {cnt || "·"}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Section 4: EFI Intelligence ──────────────────────────────────────────────
function EfiSection({ data, loading }) {
  if (loading) return <LoadingCard rows={4} />;
  if (!data) return <EmptyState icon={Cpu} action="Run your first diagnostic to see AI insights" />;

  const { stats, failure_patterns, vehicle_fault_chart, fault_types } = data;
  const hasData = failure_patterns.length > 0;

  return (
    <div className="space-y-5" data-testid="efi-section">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard icon={Zap} label="Diagnoses Run" value={fmtNum(stats.diagnoses_run)} color={VOLT} testId="efi-kpi-diagnoses" />
        <KpiCard icon={Cpu} label="Fault Types Found" value={fmtNum(stats.total_fault_types)} color={CYAN} testId="efi-kpi-faults" />
        <KpiCard icon={Activity} label="Tickets in Period" value={fmtNum(stats.total_in_period)} color={BLUE} testId="efi-kpi-total" />
        <KpiCard icon={Target} label="Top Fault" value={stats.most_diagnosed || "—"} color={AMBER} testId="efi-kpi-top" />
      </div>

      {!hasData ? (
        <EmptyState icon={Zap} action="Create tickets with categories to see fault analysis" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Top Failure Patterns */}
          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Top Failure Patterns</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                      {["Fault Type", "Count", "Avg Fix Time", "Avg Cost"].map((h) => (
                        <th key={h} className="pb-2 pr-3 text-left font-medium" style={{ color: DIM_TEXT }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {failure_patterns.map((p, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                        <td className="py-2 pr-3 font-medium capitalize" style={{ color: "rgb(var(--bw-white))" }}>{p.fault_type}</td>
                        <td className="py-2 pr-3" style={{ color: VOLT }}>{p.count}</td>
                        <td className="py-2 pr-3" style={{ color: "rgb(var(--bw-white))" }}>
                          {p.avg_fix_hours != null ? `${p.avg_fix_hours}h` : "—"}
                        </td>
                        <td className="py-2" style={{ color: AMBER }}>{fmtCurrency(p.avg_cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Failure by Vehicle */}
          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Faults by Vehicle Type</CardTitle>
            </CardHeader>
            <CardContent className="px-2 pb-4">
              {vehicle_fault_chart.length === 0 ? (
                <EmptyState icon={BarChart3} />
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={vehicle_fault_chart} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                    <XAxis dataKey="vehicle" tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={ChartTooltipStyle} />
                    {fault_types.map((f, i) => (
                      <Bar key={f} dataKey={f} name={f} stackId="a" fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// ─── Section 5: Customer Intelligence ─────────────────────────────────────────
function CustomerSection({ data, loading }) {
  if (loading) return <LoadingCard rows={5} />;
  if (!data) return <EmptyState icon={Users} action="Add customers and close tickets to see intelligence" />;

  const { kpis, rating_trend, top_customers, vehicle_makes } = data;
  const hasData = top_customers.length > 0 || kpis.new_customers > 0;

  const ratingColor = kpis.avg_rating == null ? DIM_TEXT :
    kpis.avg_rating >= 4 ? VOLT : kpis.avg_rating >= 3 ? AMBER : RED;

  return (
    <div className="space-y-5" data-testid="customer-section">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard icon={Users} label="New Customers" value={fmtNum(kpis.new_customers)} color={VOLT} testId="cust-kpi-new" />
        <KpiCard icon={ChevronRight} label="Returning" value={fmtNum(kpis.returning_customers)} color={CYAN} testId="cust-kpi-returning" />
        <KpiCard icon={Star} label="Avg Rating" value={kpis.avg_rating != null ? `${kpis.avg_rating} / 5` : "—"} color={ratingColor} testId="cust-kpi-rating" />
        <KpiCard icon={Activity} label="Survey Response" value={kpis.response_rate != null ? `${kpis.response_rate}%` : "—"} color={BLUE} testId="cust-kpi-response" />
      </div>

      {!hasData ? (
        <EmptyState icon={Users} action="Add customers and collect feedback to see data here" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Top Customers */}
          <Card className="lg:col-span-2 border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Top Customers by Revenue</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {top_customers.length === 0 ? (
                <EmptyState icon={Users} />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                        {["Customer", "Invoices", "Total Spent", "Last Visit"].map((h) => (
                          <th key={h} className="pb-2 pr-3 text-left font-medium" style={{ color: DIM_TEXT }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {top_customers.map((c, i) => (
                        <tr key={i} data-testid={`cust-row-${c.id}`} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                          <td className="py-2 pr-3">
                            <div className="flex items-center gap-1.5">
                              <span className="font-medium" style={{ color: "rgb(var(--bw-white))" }}>{c.name}</span>
                              {c.at_risk && (
                                <Badge className="text-xs px-1 py-0" style={{ background: "rgba(234,179,8,0.15)", color: AMBER, border: `1px solid ${AMBER}30` }}>
                                  At Risk
                                </Badge>
                              )}
                            </div>
                          </td>
                          <td className="py-2 pr-3" style={{ color: DIM_TEXT }}>{c.invoice_count}</td>
                          <td className="py-2 pr-3 font-semibold" style={{ color: VOLT }}>{fmtCurrency(c.total_spent)}</td>
                          <td className="py-2" style={{ color: c.at_risk ? AMBER : DIM_TEXT }}>{c.last_visit || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Vehicle Make Dist */}
          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Fleet by Make</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center pb-4">
              {vehicle_makes.length === 0 ? (
                <EmptyState icon={BarChart3} />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={140}>
                    <PieChart>
                      <Pie data={vehicle_makes} dataKey="count" nameKey="make" cx="50%" cy="50%" innerRadius={38} outerRadius={58} paddingAngle={3}>
                        {vehicle_makes.map((_, i) => (
                          <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={ChartTooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1 w-full px-2">
                    {vehicle_makes.slice(0, 6).map((m, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                          <span style={{ color: "rgb(var(--bw-white))" }}>{m.make}</span>
                        </span>
                        <span style={{ color: DIM_TEXT }}>{m.count}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Satisfaction Trend */}
      {rating_trend.length > 0 && (
        <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Satisfaction Trend</CardTitle>
          </CardHeader>
          <CardContent className="px-2 pb-4">
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={rating_trend} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                <XAxis dataKey="date" tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis domain={[1, 5]} tick={{ fill: DIM_TEXT, fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip formatter={(v) => `${v} ★`} />} />
                <Line type="monotone" dataKey="rating" stroke={AMBER} strokeWidth={2} dot={false} name="Avg Rating" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Section 6: Inventory Intelligence ────────────────────────────────────────
function InventorySection({ data, loading }) {
  if (loading) return <LoadingCard rows={5} />;
  if (!data) return <EmptyState icon={Boxes} action="Add inventory items to see intelligence" />;

  const { kpis, stock_health, fast_movers, dead_stock } = data;
  const hasData = kpis.total_value > 0 || kpis.below_reorder > 0;

  return (
    <div className="space-y-5" data-testid="inventory-section">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard icon={Package} label="Inventory Value" value={fmtCurrency(kpis.total_value)} color={VOLT} testId="inv-kpi-value" />
        <KpiCard icon={AlertTriangle} label="Below Reorder" value={fmtNum(kpis.below_reorder)} color={kpis.below_reorder > 0 ? AMBER : VOLT} warn={kpis.below_reorder > 0} testId="inv-kpi-reorder" />
        <KpiCard icon={ShoppingCart} label="Parts Used" value={fmtNum(kpis.parts_used)} color={CYAN} testId="inv-kpi-used" />
        <KpiCard icon={Boxes} label="Dead Stock Items" value={fmtNum(kpis.dead_stock_count)} color={kpis.dead_stock_count > 0 ? AMBER : VOLT} warn={kpis.dead_stock_count > 0} testId="inv-kpi-dead" />
      </div>

      {!hasData ? (
        <EmptyState icon={Package} action="Add inventory items and raise invoices to see insights" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Stock Health Bar */}
          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>Stock Health</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              <div className="h-3 rounded-full overflow-hidden flex mb-4" style={{ background: "rgba(255,255,255,0.06)" }}>
                {stock_health.filter((s) => s.value > 0).map((s, i) => (
                  <div
                    key={i}
                    style={{ width: `${s.value}%`, background: s.color, transition: "width 0.5s ease" }}
                    title={`${s.label}: ${s.value}%`}
                  />
                ))}
              </div>
              <div className="space-y-2">
                {stock_health.map((s, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                      <span style={{ color: "rgb(var(--bw-white))" }}>{s.label}</span>
                    </span>
                    <span style={{ color: DIM_TEXT }}>{s.count} items ({s.value}%)</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Fast Movers */}
          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>
                <span style={{ color: VOLT }}>▲</span> Fast Movers
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {fast_movers.length === 0 ? (
                <EmptyState icon={ShoppingCart} />
              ) : (
                <div className="space-y-2">
                  {fast_movers.map((f, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <span className="font-medium truncate pr-2" style={{ color: "rgb(var(--bw-white))", maxWidth: 120 }}>{f.name}</span>
                      <div className="flex gap-3 flex-shrink-0">
                        <span style={{ color: VOLT }}>{f.qty} used</span>
                        <span style={{ color: DIM_TEXT }}>{fmtCurrency(f.value)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Dead Stock */}
          <Card className="border" style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.07)" }}>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-medium" style={{ color: DIM_TEXT }}>
                <span style={{ color: AMBER }}>▲</span> Dead Stock
                <span className="ml-1 text-xs" style={{ color: DIM_TEXT }}>(no movement 90d)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {dead_stock.length === 0 ? (
                <EmptyState icon={Boxes} />
              ) : (
                <div className="space-y-2">
                  {dead_stock.map((d, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <span className="font-medium truncate pr-2" style={{ color: "rgb(var(--bw-white))", maxWidth: 120 }}>{d.name}</span>
                      <div className="flex gap-3 flex-shrink-0">
                        <span style={{ color: AMBER }}>{d.stock} in stock</span>
                        <span style={{ color: DIM_TEXT }}>{fmtCurrency(d.value)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function DataInsights({ user }) {
  const [period, setPeriod] = useState("month");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");
  const [showCustom, setShowCustom] = useState(false);

  const [revenue, setRevenue] = useState(null);
  const [operations, setOperations] = useState(null);
  const [technicians, setTechnicians] = useState(null);
  const [efi, setEfi] = useState(null);
  const [customers, setCustomers] = useState(null);
  const [inventory, setInventory] = useState(null);

  const [loading, setLoading] = useState({
    revenue: true, operations: true, technicians: true, efi: true, customers: true, inventory: true,
  });

  const getParams = useCallback(() => {
    const dr = period === "custom" ? { from: customFrom, to: customTo } : getDateRange(period);
    if (!dr || !dr.from || !dr.to) return "";
    return `?date_from=${dr.from}&date_to=${dr.to}`;
  }, [period, customFrom, customTo]);

  const fetchSection = useCallback(async (key, path, setter) => {
    setLoading((prev) => ({ ...prev, [key]: true }));
    try {
      const params = getParams();
      const res = await fetch(`${API}/insights/${path}${params}`, {
        headers: getAuthHeaders(),
        credentials: "include",
      });
      if (res.ok) setter(await res.json());
    } catch (e) {
      console.error(`Insights ${key} error:`, e);
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }));
    }
  }, [getParams]);

  const fetchAll = useCallback(() => {
    fetchSection("revenue", "revenue", setRevenue);
    fetchSection("operations", "operations", setOperations);
    fetchSection("technicians", "technicians", setTechnicians);
    fetchSection("efi", "efi", setEfi);
    fetchSection("customers", "customers", setCustomers);
    fetchSection("inventory", "inventory", setInventory);
  }, [fetchSection]);

  useEffect(() => {
    if (period !== "custom") fetchAll();
  }, [period, fetchAll]);

  const handleCustomApply = () => {
    if (customFrom && customTo) fetchAll();
  };

  const sections = [
    {
      key: "revenue", icon: IndianRupee, title: "Revenue Intelligence",
      sub: "Invoice collection, trends and service mix",
      component: <RevenueSection data={revenue} loading={loading.revenue} />,
    },
    {
      key: "operations", icon: Activity, title: "Workshop Operations",
      sub: "Ticket volume, resolution times and SLA tracking",
      component: <OperationsSection data={operations} loading={loading.operations} />,
    },
    {
      key: "technicians", icon: Users, title: "Technician Performance",
      sub: "Leaderboard, resolution speed and specialisation",
      component: <TechnicianSection data={technicians} loading={loading.technicians} />,
    },
    {
      key: "efi", icon: Cpu, title: "EFI Intelligence",
      sub: "Fault patterns, vehicle diagnostics and trends",
      component: <EfiSection data={efi} loading={loading.efi} />,
    },
    {
      key: "customers", icon: Star, title: "Customer Intelligence",
      sub: "Satisfaction, retention and fleet composition",
      component: <CustomerSection data={customers} loading={loading.customers} />,
    },
    {
      key: "inventory", icon: Package, title: "Inventory Intelligence",
      sub: "Stock health, fast movers and dead stock",
      component: <InventorySection data={inventory} loading={loading.inventory} />,
    },
  ];

  return (
    <div className="min-h-screen" style={{ background: "var(--bw-bg, #0a0f0d)" }} data-testid="data-insights-page">
      {/* Page Header */}
      <div className="px-4 sm:px-6 pt-6 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1
            className="text-2xl sm:text-3xl font-bold"
            style={{ fontFamily: "Syne, sans-serif", color: "rgb(var(--bw-white))" }}
          >
            Data Insights
          </h1>
          <p className="text-sm mt-0.5" style={{ color: DIM_TEXT }}>
            Business intelligence for your workshop
          </p>
        </div>

        {/* Date Range Selector */}
        <div className="flex flex-wrap items-center gap-2" data-testid="date-range-selector">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              data-testid={`period-btn-${p.value}`}
              onClick={() => {
                setPeriod(p.value);
                setShowCustom(p.value === "custom");
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{
                background: period === p.value ? VOLT_DIM : "rgba(255,255,255,0.04)",
                color: period === p.value ? VOLT : DIM_TEXT,
                border: `1px solid ${period === p.value ? VOLT_BORDER : "rgba(255,255,255,0.07)"}`,
              }}
            >
              {p.label}
            </button>
          ))}
          <Button
            size="sm"
            variant="ghost"
            data-testid="refresh-btn"
            onClick={fetchAll}
            className="h-8 w-8 p-0 rounded-lg"
            style={{ color: DIM_TEXT, background: "rgba(255,255,255,0.04)" }}
          >
            <RefreshCw size={13} />
          </Button>
        </div>
      </div>

      {/* Custom Date Range */}
      {showCustom && (
        <div className="px-4 sm:px-6 pb-4 flex flex-wrap items-center gap-2">
          <input
            type="date"
            value={customFrom}
            onChange={(e) => setCustomFrom(e.target.value)}
            data-testid="custom-from"
            className="text-xs px-3 py-1.5 rounded-lg"
            style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: "rgb(var(--bw-white))",
            }}
          />
          <span style={{ color: DIM_TEXT }} className="text-xs">to</span>
          <input
            type="date"
            value={customTo}
            onChange={(e) => setCustomTo(e.target.value)}
            data-testid="custom-to"
            className="text-xs px-3 py-1.5 rounded-lg"
            style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: "rgb(var(--bw-white))",
            }}
          />
          <Button
            size="sm"
            data-testid="apply-custom-btn"
            onClick={handleCustomApply}
            style={{ background: VOLT, color: "rgb(var(--bw-black))", height: 32, fontSize: 12 }}
          >
            Apply
          </Button>
        </div>
      )}

      {/* Sections */}
      <div className="px-4 sm:px-6 pb-10 space-y-10">
        {sections.map((s) => (
          <section key={s.key} data-testid={`section-${s.key}`}>
            <SectionHeader icon={s.icon} title={s.title} sub={s.sub} />
            {s.component}
          </section>
        ))}
      </div>
    </div>
  );
}
