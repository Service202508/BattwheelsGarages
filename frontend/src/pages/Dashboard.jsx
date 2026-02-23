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
    <Card className={`group relative overflow-hidden bg-[#111820] border border-[rgba(255,255,255,0.07)] rounded hover:border-[rgba(200,255,0,0.20)] hover:bg-[#141E27] transition-[background,border-color] duration-200 ease-out ${className}`}>
      {/* Top reveal line - scales from left on hover */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#C8FF00] to-[#1AFFE4] scale-x-0 origin-left transition-transform duration-[400ms] ease-[cubic-bezier(0.4,0,0.2,1)] group-hover:scale-x-100" />
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-[rgba(244,246,240,0.45)] uppercase tracking-[0.1em] font-mono">{title}</p>
            <p className={`text-3xl font-bold ${isZero ? 'text-[rgba(244,246,240,0.20)]' : 'text-[#C8FF00]'}`} style={!isZero ? { textShadow: '0 0 24px rgba(200,255,0,0.2)' } : undefined}>{value}</p>
            <p className="text-[11px] text-[rgba(244,246,240,0.25)] mt-1">{subtitle}</p>
          </div>
          <div className="p-3 rounded bg-[rgba(200,255,0,0.08)] border border-[rgba(200,255,0,0.15)]">
            <Icon className="h-5 w-5 text-[#C8FF00]" />
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
    <Card className="bg-[#111820] border border-[rgba(255,255,255,0.07)] rounded hover:border-[rgba(200,255,0,0.15)] transition-all duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          {Icon && (
            <div className="p-1.5 rounded bg-[rgba(200,255,0,0.08)] border border-[rgba(200,255,0,0.15)]">
              <Icon className="h-4 w-4 text-[#C8FF00]" />
            </div>
          )}
          <div>
            <CardTitle className="text-base font-semibold text-[#F4F6F0]">{title}</CardTitle>
            <CardDescription className="text-xs text-[rgba(244,246,240,0.45)]">{description}</CardDescription>
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

  if (loading) {
    return (
      <div className="space-y-6 p-1">
        <div className="h-8 bg-[rgba(255,255,255,0.05)] rounded-lg w-48 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-[rgba(255,255,255,0.05)] rounded animate-pulse" />
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
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Dashboard</h1>
          <p className="text-sm text-[rgba(244,246,240,0.45)] mt-0.5">A high-level overview of your garage's operations.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[rgba(200,255,0,0.08)] border border-[rgba(200,255,0,0.20)] rounded-full">
          <div className="h-2 w-2 rounded-full bg-[#C8FF00] animate-pulse" />
          <span className="text-xs font-medium text-[#C8FF00]">Live</span>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-[#111820] border border-[rgba(255,255,255,0.07)] p-1 rounded-lg">
          <TabsTrigger 
            value="workshop" 
            className="data-[state=active]:bg-[rgba(200,255,0,0.12)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-t-2 data-[state=active]:border-t-[#C8FF00] rounded px-4 py-2 text-sm font-medium text-[rgba(244,246,240,0.45)]"
            data-testid="workshop-tab"
          >
            Workshop Overview
          </TabsTrigger>
          <TabsTrigger 
            value="service-tickets" 
            className="data-[state=active]:bg-[rgba(200,255,0,0.12)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-t-2 data-[state=active]:border-t-[#C8FF00] rounded px-4 py-2 text-sm font-medium text-[rgba(244,246,240,0.45)]"
            data-testid="service-tickets-tab"
          >
            Service Tickets
          </TabsTrigger>
          <TabsTrigger 
            value="receivables" 
            className="data-[state=active]:bg-[rgba(200,255,0,0.12)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-t-2 data-[state=active]:border-t-[#C8FF00] rounded px-4 py-2 text-sm font-medium text-[rgba(244,246,240,0.45)]"
            data-testid="receivables-tab"
          >
            Receivables Overview
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
            <Card className="bg-[#111820] border border-[rgba(255,255,255,0.07)]" data-testid="vehicle-status-chart">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-[#F4F6F0]">Vehicle Status Distribution</CardTitle>
                <CardDescription className="text-xs text-[rgba(244,246,240,0.45)]">Live breakdown of vehicle statuses</CardDescription>
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
                            color: '#F4F6F0'
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
                      <span className="text-xs text-[rgba(244,246,240,0.45)]">{entry.name}: {entry.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Repair Time Trend */}
            <Card className="bg-[#111820] border border-[rgba(255,255,255,0.07)]" data-testid="repair-trend-chart">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-[#F4F6F0]">Repair Time Trend</CardTitle>
                <CardDescription className="text-xs text-[rgba(244,246,240,0.45)]">Monthly average time per repair order</CardDescription>
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
                            color: '#F4F6F0'
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
                  <span className="text-4xl font-bold text-[#C8FF00]" style={{ textShadow: '0 0 24px rgba(200,255,0,0.2)' }}>
                    {serviceTicketStats.onsite_resolution_percentage}%
                  </span>
                  <Badge 
                    className={`${serviceTicketStats.onsite_resolution_percentage >= 40 
                      ? 'bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border-[rgba(200,255,0,0.25)]' 
                      : 'bg-[rgba(234,179,8,0.10)] text-[#EAB308] border-[rgba(234,179,8,0.25)]'} border text-xs font-medium`}
                  >
                    {serviceTicketStats.onsite_resolution_percentage >= 40 ? 'On Target' : 'Improving'}
                  </Badge>
                </div>
                <div className="h-2 bg-[rgba(255,255,255,0.05)] rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500"
                    style={{ 
                      width: `${serviceTicketStats.onsite_resolution_percentage}%`,
                      backgroundColor: BRAND_COLORS.emerald.primary
                    }}
                  />
                </div>
                <p className="text-xs text-[rgba(244,246,240,0.45)]">
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
                <div className="flex items-center justify-between p-3 bg-[rgba(234,179,8,0.08)] border border-[rgba(234,179,8,0.20)] rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 bg-[rgba(234,179,8,0.12)] border border-[rgba(234,179,8,0.25)] rounded-lg">
                      <Truck className="h-4 w-4 text-[#EAB308]" />
                    </div>
                    <span className="text-sm font-medium text-[#F4F6F0]">Pickup Service</span>
                  </div>
                  <span className="text-xl font-bold text-[#EAB308]">{serviceTicketStats.pickup}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-[rgba(139,92,246,0.08)] border border-[rgba(139,92,246,0.20)] rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 bg-[rgba(139,92,246,0.12)] border border-[rgba(139,92,246,0.25)] rounded-lg">
                      <Wifi className="h-4 w-4 text-[#8B5CF6]" />
                    </div>
                    <span className="text-sm font-medium text-[#F4F6F0]">Remote Support</span>
                  </div>
                  <span className="text-xl font-bold text-[#8B5CF6]">{serviceTicketStats.remote}</span>
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
                  <p className="text-4xl font-bold text-[#C8FF00]" style={{ textShadow: '0 0 24px rgba(200,255,0,0.2)' }}>{serviceTicketStats.total_resolved_30d}</p>
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-0.5">Total Resolved</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="text-center p-2.5 bg-[rgba(200,255,0,0.08)] border border-[rgba(200,255,0,0.20)] rounded-lg">
                    <p className="text-lg font-bold text-[#C8FF00]">{serviceTicketStats.total_onsite_resolved_30d}</p>
                    <p className="text-xs text-[rgba(244,246,240,0.45)]">Onsite</p>
                  </div>
                  <div className="text-center p-2.5 bg-[rgba(59,158,255,0.08)] border border-[rgba(59,158,255,0.20)] rounded-lg">
                    <p className="text-lg font-bold text-[#3B9EFF]">
                      {serviceTicketStats.total_resolved_30d - serviceTicketStats.total_onsite_resolved_30d}
                    </p>
                    <p className="text-xs text-[rgba(244,246,240,0.45)]">Workshop/Other</p>
                  </div>
                </div>
              </div>
            </KPICard>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Ticket Distribution Pie Chart */}
            <Card className="bg-[#111820] border border-[rgba(255,255,255,0.07)]" data-testid="ticket-distribution-chart">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-[#F4F6F0]">Open Tickets by Type</CardTitle>
                <CardDescription className="text-xs text-[rgba(244,246,240,0.45)]">Distribution of active service tickets</CardDescription>
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
                              color: '#F4F6F0'
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="text-center">
                        <CheckCircle2 className="h-10 w-10 text-[#C8FF00] mx-auto mb-2" />
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">No open tickets</p>
                      </div>
                    )}
                  </div>
                </ChartContainer>
                <div className="flex flex-wrap justify-center gap-3 mt-2">
                  {ticketDistributionData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-1.5">
                      <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.fill }} />
                      <span className="text-xs text-[rgba(244,246,240,0.45)]">{entry.name}: {entry.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Resolution Efficiency */}
            <Card className="bg-[#111820] border border-[rgba(255,255,255,0.07)]">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-[#F4F6F0]">Resolution Efficiency</CardTitle>
                <CardDescription className="text-xs text-[rgba(244,246,240,0.45)]">Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Onsite vs Workshop Comparison */}
                  <div>
                    <div className="flex justify-between mb-1.5">
                      <span className="text-xs text-[rgba(244,246,240,0.45)]">Onsite vs Workshop (Open)</span>
                      <span className="text-xs font-medium text-[#F4F6F0]">
                        {serviceTicketStats.onsite_resolution} : {serviceTicketStats.workshop_visit}
                      </span>
                    </div>
                    <div className="flex h-3 rounded-full overflow-hidden bg-[rgba(255,255,255,0.05)]">
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
                      <span className="text-[10px] text-[#C8FF00] font-medium">Onsite</span>
                      <span className="text-[10px] text-[#3B9EFF] font-medium">Workshop</span>
                    </div>
                  </div>

                  {/* Performance Metrics */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.07)] rounded-lg">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Target className="h-3 w-3 text-[rgba(244,246,240,0.35)]" />
                        <p className="text-[10px] text-[rgba(244,246,240,0.45)] uppercase tracking-wide font-mono">Target Resolution</p>
                      </div>
                      <p className="text-xl font-bold text-[#F4F6F0]">8 hrs</p>
                      <p className={`text-[10px] mt-0.5 font-medium ${serviceTicketStats.avg_resolution_time_hours <= 8 ? 'text-[#C8FF00]' : 'text-[#EAB308]'}`}>
                        {serviceTicketStats.avg_resolution_time_hours <= 8 ? '✓ On Target' : '⚠ Above Target'}
                      </p>
                    </div>
                    <div className="p-3 bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.07)] rounded-lg">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Target className="h-3 w-3 text-[rgba(244,246,240,0.35)]" />
                        <p className="text-[10px] text-[rgba(244,246,240,0.45)] uppercase tracking-wide font-mono">Onsite Target</p>
                      </div>
                      <p className="text-xl font-bold text-[#F4F6F0]">40%</p>
                      <p className={`text-[10px] mt-0.5 font-medium ${serviceTicketStats.onsite_resolution_percentage >= 40 ? 'text-[#C8FF00]' : 'text-[#EAB308]'}`}>
                        {serviceTicketStats.onsite_resolution_percentage >= 40 ? '✓ On Target' : '⚠ Below Target'}
                      </p>
                    </div>
                  </div>

                  {/* Real-time Sync Indicator */}
                  <div className="flex items-center justify-center gap-2 pt-3 border-t border-[rgba(255,255,255,0.07)]">
                    <div className="h-1.5 w-1.5 rounded-full bg-[#C8FF00] animate-pulse" />
                    <span className="text-[10px] text-[rgba(244,246,240,0.35)]">Real-time sync enabled (30s refresh)</span>
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
      </Tabs>
    </div>
  );
}
