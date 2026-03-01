import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Car, Wrench, Clock, Users, MapPin, Building2, Truck, Wifi, TrendingUp, CheckCircle2, AlertCircle, Zap, Target, Trophy, ChevronRight } from "lucide-react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { MetricCard } from "@/components/ui/stat-card";
import { API, getAuthHeaders } from "@/App";
import { OnboardingBanner } from "@/components/OnboardingBanner";

// Wrapper component to prevent chart dimension warnings in hidden tabs
const ChartContainer = ({ children, isVisible, height = "240px" }) => {
  if (!isVisible) {
    return <div style={{ height }} className="flex items-center justify-center" />;
  }
  return children;
};

// Clean, consistent color palette with volt as primary brand color
const BRAND_COLORS = {
  volt: {
    primary: "#C8FF00",
    secondary: "#1AFFE4",
    bg: "rgba(200,255,0,0.08)",
    border: "rgba(200,255,0,0.2)"
  },
  emerald: {
    primary: "#C8FF00",
    light: "#d4ff1a",
    dark: "#a6d400",
    bg: "rgba(200,255,0,0.08)",
    border: "rgba(200,255,0,0.2)"
  },
  blue: {
    primary: "#3B9EFF",
    light: "#60A5FA",
    dark: "#2563EB",
    bg: "rgba(59,158,255,0.1)",
    border: "rgba(59,158,255,0.25)"
  },
  amber: {
    primary: "#EAB308",
    light: "#FBBF24",
    dark: "#D97706",
    bg: "rgba(234,179,8,0.1)",
    border: "rgba(234,179,8,0.25)"
  },
  violet: {
    primary: "#8B5CF6",
    light: "#A78BFA",
    dark: "#7C3AED",
    bg: "rgba(139,92,246,0.1)",
    border: "rgba(139,92,246,0.25)"
  },
  slate: {
    bg: "#111820",
    card: "#111820",
    border: "rgba(255,255,255,0.07)",
    text: "#F4F6F0",
    muted: "rgba(244,246,240,0.45)"
  }
};

// Enhanced Stat Card Component for Service Tickets - Dark Volt Theme
const ServiceMetricCard = ({ title, value, subtitle, icon: Icon, color = "emerald", className = "" }) => {
  const isZero = value === 0 || value === "0";
  
  return (
    <Card className={`group relative overflow-hidden bg-bw-panel border border-white/[0.07] rounded hover:border-bw-volt/20 hover:bg-bw-card transition-[background,border-color] duration-200 ease-out ${className}`}>
      {/* Top reveal line - scales from left on hover */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-bw-volt to-bw-teal scale-x-0 origin-left transition-transform duration-[400ms] ease-[cubic-bezier(0.4,0,0.2,1)] group-hover:scale-x-100" />
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-bw-white/[0.45] uppercase tracking-[0.1em] font-mono">{title}</p>
            <p className={`text-3xl font-bold ${isZero ? 'text-bw-white/20' : 'text-bw-volt'}`} style={!isZero ? { textShadow: '0 0 24px rgba(200,255,0,0.2)' } : undefined}>{value}</p>
            <p className="text-[11px] text-bw-white/25 mt-1">{subtitle}</p>
          </div>
          <div className="p-3 rounded bg-bw-volt/[0.08] border border-bw-volt/15">
            <Icon className="h-5 w-5 text-bw-volt" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// KPI Card with progress - Dark Volt Theme
const KPICard = ({ title, description, value, unit = "", target, icon: Icon, color = "emerald", children }) => {
  const percentage = target ? Math.min((parseFloat(value) / target) * 100, 100) : 0;
  const isOnTarget = target ? parseFloat(value) >= target : true;
  const isZero = value === 0 || value === "0" || value === "0%";
  
  return (
    <Card className="bg-bw-panel border border-white/[0.07] rounded hover:border-bw-volt/15 transition-all duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          {Icon && (
            <div className="p-1.5 rounded bg-bw-volt/[0.08] border border-bw-volt/15">
              <Icon className="h-4 w-4 text-bw-volt" />
            </div>
          )}
          <div>
            <CardTitle className="text-base font-semibold text-bw-white">{title}</CardTitle>
            <CardDescription className="text-xs text-bw-white/[0.45]">{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {children}
      </CardContent>
    </Card>
  );
};

export default function Dashboard({ user }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("service-tickets");
  const [leaderboard, setLeaderboard] = useState([]);
  const [leaderboardPeriod, setLeaderboardPeriod] = useState("this_month");
  const [leaderboardLoading, setLeaderboardLoading] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`${API}/dashboard/stats`, {
          credentials: "include",
          headers: getAuthHeaders(),
        });
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();

    // Refresh every 30 seconds for real-time sync
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchLeaderboard = async (period = leaderboardPeriod) => {
    setLeaderboardLoading(true);
    try {
      const response = await fetch(`${API}/reports/technician-performance?period=${period}`, {
        credentials: "include",
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data.technicians || []);
      }
    } catch (err) {
      console.error("Failed to fetch leaderboard:", err);
    } finally {
      setLeaderboardLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "technicians") {
      fetchLeaderboard(leaderboardPeriod);
    }
  }, [activeTab, leaderboardPeriod]);

  if (loading) {
    return (
      <div className="space-y-6 p-1">
        <div className="h-8 bg-white/5 rounded-lg w-48 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const serviceTicketStats = stats?.service_ticket_stats || {
    total_open: 0,
    onsite_resolution: 0,
    workshop_visit: 0,
    pickup: 0,
    remote: 0,
    avg_resolution_time_hours: 0,
    onsite_resolution_percentage: 0,
    total_resolved_30d: 0,
    total_onsite_resolved_30d: 0
  };

  const vehicleStatusData = stats ? [
    { name: "Active", value: stats.vehicle_status_distribution.active || 0, fill: BRAND_COLORS.emerald.primary },
    { name: "In Workshop", value: stats.vehicle_status_distribution.in_workshop || 0, fill: BRAND_COLORS.blue.primary },
    { name: "Serviced", value: stats.vehicle_status_distribution.serviced || 0, fill: BRAND_COLORS.violet.primary },
  ] : [];

  const repairTrendData = stats?.monthly_repair_trends || [];

  // Service ticket distribution for pie chart
  const ticketDistributionData = [
    { name: "Onsite", value: serviceTicketStats.onsite_resolution, fill: BRAND_COLORS.emerald.primary },
    { name: "Workshop", value: serviceTicketStats.workshop_visit, fill: BRAND_COLORS.blue.primary },
    { name: "Pickup", value: serviceTicketStats.pickup, fill: BRAND_COLORS.amber.primary },
    { name: "Remote", value: serviceTicketStats.remote, fill: BRAND_COLORS.violet.primary },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-bw-white">Dashboard</h1>
          <p className="text-sm text-bw-white/[0.45] mt-0.5">A high-level overview of your garage's operations.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-bw-volt/[0.08] border border-bw-volt/20 rounded-full">
          <div className="h-2 w-2 rounded-full bg-bw-volt animate-pulse" />
          <span className="text-xs font-medium text-bw-volt">Live</span>
        </div>
      </div>

      {/* Onboarding Banner - only shown for new orgs */}
      <OnboardingBanner />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-bw-panel border border-white/[0.07] p-1 rounded-lg">
          <TabsTrigger 
            value="workshop" 
            className="data-[state=active]:bg-bw-volt/[0.12] data-[state=active]:text-bw-volt data-[state=active]:border-t-2 data-[state=active]:border-t-bw-volt rounded px-4 py-2 text-sm font-medium text-bw-white/[0.45]"
            data-testid="workshop-tab"
          >
            Workshop Overview
          </TabsTrigger>
          <TabsTrigger 
            value="service-tickets" 
            className="data-[state=active]:bg-bw-volt/[0.12] data-[state=active]:text-bw-volt data-[state=active]:border-t-2 data-[state=active]:border-t-bw-volt rounded px-4 py-2 text-sm font-medium text-bw-white/[0.45]"
            data-testid="service-tickets-tab"
          >
            Service Tickets
          </TabsTrigger>
          <TabsTrigger 
            value="receivables" 
            className="data-[state=active]:bg-bw-volt/[0.12] data-[state=active]:text-bw-volt data-[state=active]:border-t-2 data-[state=active]:border-t-bw-volt rounded px-4 py-2 text-sm font-medium text-bw-white/[0.45]"
            data-testid="receivables-tab"
          >
            Receivables Overview
          </TabsTrigger>
          <TabsTrigger 
            value="technicians" 
            className="data-[state=active]:bg-bw-volt/[0.12] data-[state=active]:text-bw-volt data-[state=active]:border-t-2 data-[state=active]:border-t-bw-volt rounded px-4 py-2 text-sm font-medium text-bw-white/[0.45]"
            data-testid="technicians-tab"
          >
            <Trophy className="h-3.5 w-3.5 mr-1.5 inline" />
            Leaderboard
          </TabsTrigger>
        </TabsList>

        {/* ==================== WORKSHOP OVERVIEW TAB ==================== */}
        <TabsContent value="workshop" className="mt-6">
          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <ServiceMetricCard
              title="Vehicles in Workshop"
              value={stats?.vehicles_in_workshop || 0}
              subtitle="Currently being serviced"
              icon={Wrench}
              color="emerald"
            />
            <ServiceMetricCard
              title="Open Repair Orders"
              value={stats?.open_repair_orders || 0}
              subtitle="Active service tickets"
              icon={Car}
              color="blue"
            />
            <ServiceMetricCard
              title="Avg. Repair Time"
              value={<>{stats?.avg_repair_time || 0}<span className="text-lg font-normal text-slate-400 ml-1">hrs</span></>}
              subtitle="For all closed tickets"
              icon={Clock}
              color="amber"
            />
            <ServiceMetricCard
              title="Available Technicians"
              value={stats?.available_technicians || 0}
              subtitle="Ready for assignment"
              icon={Users}
              color="violet"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Vehicle Status Distribution */}
            <Card className="bg-bw-panel border border-white/[0.07]" data-testid="vehicle-status-chart">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-bw-white">Vehicle Status Distribution</CardTitle>
                <CardDescription className="text-xs text-bw-white/[0.45]">Live breakdown of vehicle statuses</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer isVisible={activeTab === "workshop"} height="240px">
                  <div className="h-[240px] flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={vehicleStatusData}
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={80}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          {vehicleStatusData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#111820', 
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '4px',
                            color: 'rgb(var(--bw-white))'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartContainer>
                <div className="flex justify-center gap-4 mt-2">
                  {vehicleStatusData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-1.5">
                      <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.fill }} />
                      <span className="text-xs text-bw-white/[0.45]">{entry.name}: {entry.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Repair Time Trend */}
            <Card className="bg-bw-panel border border-white/[0.07]" data-testid="repair-trend-chart">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-bw-white">Repair Time Trend</CardTitle>
                <CardDescription className="text-xs text-bw-white/[0.45]">Monthly average time per repair order</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer isVisible={activeTab === "workshop"} height="260px">
                  <div className="h-[260px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={repairTrendData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                        <XAxis 
                          dataKey="month" 
                          axisLine={false} 
                          tickLine={false}
                          tick={{ fill: 'rgba(244,246,240,0.45)', fontSize: 11 }}
                        />
                        <YAxis 
                          axisLine={false} 
                          tickLine={false}
                          tick={{ fill: 'rgba(244,246,240,0.45)', fontSize: 11 }}
                          tickFormatter={(value) => `${value}h`}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#111820', 
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '4px',
                            color: 'rgb(var(--bw-white))'
                          }}
                          formatter={(value) => [`${value} hours`, 'Avg Time']}
                        />
                        <Bar 
                          dataKey="avgTime" 
                          fill={BRAND_COLORS.emerald.primary} 
                          radius={[6, 6, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ==================== SERVICE TICKETS TAB ==================== */}
        <TabsContent value="service-tickets" className="mt-6">
          {/* Service Ticket Metric Cards - Clean Light Design */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <ServiceMetricCard
              title="Total Open Tickets"
              value={serviceTicketStats.total_open}
              subtitle="Active service requests"
              icon={AlertCircle}
              color="blue"
            />
            <ServiceMetricCard
              title="Onsite Resolution"
              value={serviceTicketStats.onsite_resolution}
              subtitle="At customer location"
              icon={MapPin}
              color="emerald"
            />
            <ServiceMetricCard
              title="Workshop Visit"
              value={serviceTicketStats.workshop_visit}
              subtitle="At service center"
              icon={Building2}
              color="blue"
            />
            <ServiceMetricCard
              title="Avg. Resolution Time"
              value={<>{serviceTicketStats.avg_resolution_time_hours}<span className="text-lg font-normal text-slate-400 ml-1">hrs</span></>}
              subtitle="All closed tickets"
              icon={Clock}
              color="amber"
            />
          </div>

          {/* Second Row - KPIs */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
            {/* Onsite Resolution Rate */}
            <KPICard
              title="Onsite Resolution Rate"
              description="Last 30 days performance"
              icon={TrendingUp}
              color="emerald"
            >
              <div className="space-y-3">
                <div className="flex items-baseline justify-between">
                  <span className="text-4xl font-bold text-bw-volt" style={{ textShadow: '0 0 24px rgba(200,255,0,0.2)' }}>
                    {serviceTicketStats.onsite_resolution_percentage}%
                  </span>
                  <Badge 
                    className={`${serviceTicketStats.onsite_resolution_percentage >= 40 
                      ? 'bg-bw-volt/10 text-bw-volt border-bw-volt/25' 
                      : 'bg-bw-amber/10 text-bw-amber border-bw-amber/25'} border text-xs font-medium`}
                  >
                    {serviceTicketStats.onsite_resolution_percentage >= 40 ? 'On Target' : 'Improving'}
                  </Badge>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500"
                    style={{ 
                      width: `${serviceTicketStats.onsite_resolution_percentage}%`,
                      backgroundColor: BRAND_COLORS.emerald.primary
                    }}
                  />
                </div>
                <p className="text-xs text-bw-white/[0.45]">
                  {serviceTicketStats.total_onsite_resolved_30d} of {serviceTicketStats.total_resolved_30d} tickets resolved onsite
                </p>
              </div>
            </KPICard>

            {/* Pickup & Remote */}
            <KPICard
              title="Other Resolution Types"
              description="Pickup & Remote support tickets"
              color="amber"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-bw-amber/[0.08] border border-bw-amber/20 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 bg-bw-amber/[0.12] border border-bw-amber/25 rounded-lg">
                      <Truck className="h-4 w-4 text-bw-amber" />
                    </div>
                    <span className="text-sm font-medium text-bw-white">Pickup Service</span>
                  </div>
                  <span className="text-xl font-bold text-bw-amber">{serviceTicketStats.pickup}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-bw-purple/[0.08] border border-bw-purple/20 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 bg-bw-purple/[0.12] border border-bw-purple/25 rounded-lg">
                      <Wifi className="h-4 w-4 text-bw-purple" />
                    </div>
                    <span className="text-sm font-medium text-bw-white">Remote Support</span>
                  </div>
                  <span className="text-xl font-bold text-bw-purple">{serviceTicketStats.remote}</span>
                </div>
              </div>
            </KPICard>

            {/* Resolution Summary */}
            <KPICard
              title="30-Day Summary"
              description="Tickets resolved in last month"
              icon={CheckCircle2}
              color="emerald"
            >
              <div className="space-y-3">
                <div className="text-center py-2">
                  <p className="text-4xl font-bold text-bw-volt" style={{ textShadow: '0 0 24px rgba(200,255,0,0.2)' }}>{serviceTicketStats.total_resolved_30d}</p>
                  <p className="text-xs text-bw-white/[0.45] mt-0.5">Total Resolved</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="text-center p-2.5 bg-bw-volt/[0.08] border border-bw-volt/20 rounded-lg">
                    <p className="text-lg font-bold text-bw-volt">{serviceTicketStats.total_onsite_resolved_30d}</p>
                    <p className="text-xs text-bw-white/[0.45]">Onsite</p>
                  </div>
                  <div className="text-center p-2.5 bg-bw-blue/[0.08] border border-bw-blue/20 rounded-lg">
                    <p className="text-lg font-bold text-bw-blue">
                      {serviceTicketStats.total_resolved_30d - serviceTicketStats.total_onsite_resolved_30d}
                    </p>
                    <p className="text-xs text-bw-white/[0.45]">Workshop/Other</p>
                  </div>
                </div>
              </div>
            </KPICard>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Ticket Distribution Pie Chart */}
            <Card className="bg-bw-panel border border-white/[0.07]" data-testid="ticket-distribution-chart">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-bw-white">Open Tickets by Type</CardTitle>
                <CardDescription className="text-xs text-bw-white/[0.45]">Distribution of active service tickets</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer isVisible={activeTab === "service-tickets"} height="240px">
                  <div className="h-[240px] flex items-center justify-center">
                    {ticketDistributionData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={ticketDistributionData}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={80}
                            paddingAngle={4}
                            dataKey="value"
                          >
                            {ticketDistributionData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.fill} />
                            ))}
                          </Pie>
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#111820', 
                              border: '1px solid rgba(255,255,255,0.1)',
                              borderRadius: '4px',
                              color: 'rgb(var(--bw-white))'
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="text-center">
                        <CheckCircle2 className="h-10 w-10 text-bw-volt mx-auto mb-2" />
                        <p className="text-sm text-bw-white/[0.45]">No open tickets</p>
                      </div>
                    )}
                  </div>
                </ChartContainer>
                <div className="flex flex-wrap justify-center gap-3 mt-2">
                  {ticketDistributionData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-1.5">
                      <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.fill }} />
                      <span className="text-xs text-bw-white/[0.45]">{entry.name}: {entry.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Resolution Efficiency */}
            <Card className="bg-bw-panel border border-white/[0.07]">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-bw-white">Resolution Efficiency</CardTitle>
                <CardDescription className="text-xs text-bw-white/[0.45]">Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Onsite vs Workshop Comparison */}
                  <div>
                    <div className="flex justify-between mb-1.5">
                      <span className="text-xs text-bw-white/[0.45]">Onsite vs Workshop (Open)</span>
                      <span className="text-xs font-medium text-bw-white">
                        {serviceTicketStats.onsite_resolution} : {serviceTicketStats.workshop_visit}
                      </span>
                    </div>
                    <div className="flex h-3 rounded-full overflow-hidden bg-white/5">
                      <div 
                        className="transition-all duration-500 rounded-l-full"
                        style={{ 
                          width: `${serviceTicketStats.total_open > 0 
                            ? (serviceTicketStats.onsite_resolution / serviceTicketStats.total_open) * 100 
                            : 0}%`,
                          backgroundColor: BRAND_COLORS.emerald.primary
                        }}
                      />
                      <div 
                        className="transition-all duration-500"
                        style={{ 
                          width: `${serviceTicketStats.total_open > 0 
                            ? (serviceTicketStats.workshop_visit / serviceTicketStats.total_open) * 100 
                            : 0}%`,
                          backgroundColor: BRAND_COLORS.blue.primary
                        }}
                      />
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-[10px] text-bw-volt font-medium">Onsite</span>
                      <span className="text-[10px] text-bw-blue font-medium">Workshop</span>
                    </div>
                  </div>

                  {/* Performance Metrics */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-white/[0.03] border border-white/[0.07] rounded-lg">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Target className="h-3 w-3 text-bw-white/35" />
                        <p className="text-[10px] text-bw-white/[0.45] uppercase tracking-wide font-mono">Target Resolution</p>
                      </div>
                      <p className="text-xl font-bold text-bw-white">8 hrs</p>
                      <p className={`text-[10px] mt-0.5 font-medium ${serviceTicketStats.avg_resolution_time_hours <= 8 ? 'text-bw-volt' : 'text-bw-amber'}`}>
                        {serviceTicketStats.avg_resolution_time_hours <= 8 ? '✓ On Target' : '⚠ Above Target'}
                      </p>
                    </div>
                    <div className="p-3 bg-white/[0.03] border border-white/[0.07] rounded-lg">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Target className="h-3 w-3 text-bw-white/35" />
                        <p className="text-[10px] text-bw-white/[0.45] uppercase tracking-wide font-mono">Onsite Target</p>
                      </div>
                      <p className="text-xl font-bold text-bw-white">40%</p>
                      <p className={`text-[10px] mt-0.5 font-medium ${serviceTicketStats.onsite_resolution_percentage >= 40 ? 'text-bw-volt' : 'text-bw-amber'}`}>
                        {serviceTicketStats.onsite_resolution_percentage >= 40 ? '✓ On Target' : '⚠ Below Target'}
                      </p>
                    </div>
                  </div>

                  {/* Real-time Sync Indicator */}
                  <div className="flex items-center justify-center gap-2 pt-3 border-t border-white/[0.07]">
                    <div className="h-1.5 w-1.5 rounded-full bg-bw-volt animate-pulse" />
                    <span className="text-[10px] text-bw-white/35">Real-time sync enabled (30s refresh)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ==================== RECEIVABLES TAB ==================== */}
        <TabsContent value="receivables" className="mt-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <ServiceMetricCard
              title="Total Revenue"
              value={<>₹{(stats?.total_revenue || 0).toLocaleString('en-IN')}</>}
              subtitle="All time"
              icon={TrendingUp}
              color="emerald"
            />
            <ServiceMetricCard
              title="Pending Invoices"
              value={<>₹{(stats?.pending_invoices || 0).toLocaleString('en-IN')}</>}
              subtitle="Outstanding amount"
              icon={AlertCircle}
              color="amber"
            />
            <ServiceMetricCard
              title="Inventory Value"
              value={<>₹{(stats?.inventory_value || 0).toLocaleString('en-IN')}</>}
              subtitle="Current stock"
              icon={Building2}
              color="blue"
            />
            <ServiceMetricCard
              title="Pending POs"
              value={stats?.pending_purchase_orders || 0}
              subtitle="Open orders"
              icon={Truck}
              color="violet"
            />
          </div>
        </TabsContent>

        {/* ==================== TECHNICIAN LEADERBOARD TAB ==================== */}
        <TabsContent value="technicians" className="mt-6">
          <Card className="bg-bw-panel border border-white/[0.07]">
            <CardHeader className="pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-bw-white flex items-center gap-2">
                  <Trophy className="h-4 w-4 text-bw-volt" />
                  Technician Performance
                </CardTitle>
                <CardDescription className="text-xs text-bw-white/[0.45] mt-0.5">
                  {leaderboardPeriod === "this_week" ? "This week" : leaderboardPeriod === "this_month" ? "This month" : "This quarter"} · Updated live
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {/* Period selector */}
                <div className="flex rounded border border-white/[0.07] overflow-hidden text-xs">
                  {[["this_week","Week"],["this_month","Month"],["this_quarter","Quarter"]].map(([val, label]) => (
                    <button
                      key={val}
                      onClick={() => setLeaderboardPeriod(val)}
                      className={`px-3 py-1.5 transition-colors ${leaderboardPeriod === val ? "bg-bw-volt/15 text-bw-volt" : "text-bw-white/[0.45] hover:text-bw-white"}`}
                      data-testid={`leaderboard-period-${val}`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <Link to="/reports?tab=technician-performance">
                  <button className="flex items-center gap-1 text-xs text-bw-volt hover:text-bw-volt-hover transition-colors">
                    View Full Report <ChevronRight className="h-3 w-3" />
                  </button>
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {leaderboardLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="h-5 w-5 border-2 border-bw-volt border-t-transparent rounded-full animate-spin" />
                </div>
              ) : leaderboard.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-bw-white/35">
                  <Trophy className="h-10 w-10 mb-3 opacity-30" />
                  <p className="text-sm">No ticket data available for this period</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {leaderboard.slice(0, 5).map((tech) => {
                    const rankStyle = tech.rank === 1
                      ? { background: "rgba(200,255,0,0.15)", color: "rgb(var(--bw-volt))", border: "1px solid rgba(200,255,0,0.30)" }
                      : tech.rank === 2
                      ? { background: "rgba(244,246,240,0.08)", color: "rgb(var(--bw-white))", border: "1px solid rgba(244,246,240,0.15)" }
                      : tech.rank === 3
                      ? { background: "rgba(255,140,0,0.10)", color: "rgb(var(--bw-orange))", border: "1px solid rgba(255,140,0,0.20)" }
                      : { background: "transparent", color: "rgb(var(--bw-white) / 0.35)", border: "1px solid transparent" };

                    const slaColor = tech.sla_compliance_rate_pct >= 90 ? "#22C55E" : tech.sla_compliance_rate_pct >= 70 ? "#EAB308" : "#FF3B2F";
                    const avgResDisplay = tech.avg_resolution_time_minutes
                      ? tech.avg_resolution_time_minutes < 60
                        ? `${Math.round(tech.avg_resolution_time_minutes)}m`
                        : `${Math.round(tech.avg_resolution_time_minutes / 60)}h ${Math.round(tech.avg_resolution_time_minutes % 60)}m`
                      : "N/A";

                    return (
                      <div
                        key={tech.technician_id}
                        className="group flex items-center gap-3 p-3 rounded-lg hover:bg-bw-volt/[0.04] transition-colors cursor-pointer"
                        data-testid={`leaderboard-row-${tech.rank}`}
                      >
                        {/* Rank */}
                        <div className="w-8 h-8 flex items-center justify-center rounded text-xs font-mono font-bold flex-shrink-0"
                          style={rankStyle}>
                          #{tech.rank}
                        </div>

                        {/* Avatar */}
                        <div className="w-8 h-8 rounded-full bg-bw-volt/[0.12] border border-bw-volt/25 flex items-center justify-center flex-shrink-0">
                          <span className="text-[10px] font-bold text-bw-volt">{tech.avatar_initials}</span>
                        </div>

                        {/* Name + stats */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <div>
                              <p className="text-sm font-semibold text-bw-white leading-none">{tech.technician_name}</p>
                              <p style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px" }} className="text-bw-white/35 mt-0.5">Technician</p>
                            </div>
                            <span className="text-xs font-mono" style={{ color: slaColor }}>{tech.sla_compliance_rate_pct}%</span>
                          </div>
                          {/* Stats */}
                          <div className="flex items-center gap-3 text-[10px] text-bw-white/[0.45] mb-1.5">
                            <span>Resolved: <span className="text-bw-white">{tech.total_tickets_resolved}</span></span>
                            <span>Avg: <span className="text-bw-white">{avgResDisplay}</span></span>
                            <span>SLA: <span style={{ color: slaColor }}>{tech.sla_compliance_rate_pct}%</span></span>
                          </div>
                          {/* SLA bar */}
                          <div className="h-1 rounded-full bg-white/[0.07] overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{ width: `${tech.sla_compliance_rate_pct}%`, backgroundColor: slaColor }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
