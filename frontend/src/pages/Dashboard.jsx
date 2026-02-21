import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Car, Wrench, Clock, Users, MapPin, Building2, Truck, Wifi, TrendingUp, CheckCircle2, AlertCircle, Zap, Target } from "lucide-react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { MetricCard } from "@/components/ui/stat-card";
import { API, getAuthHeaders } from "@/App";

// Clean, consistent color palette with emerald as primary brand color
const BRAND_COLORS = {
  emerald: {
    primary: "#10B981",
    light: "#34D399",
    dark: "#059669",
    bg: "rgba(16, 185, 129, 0.1)",
    border: "rgba(16, 185, 129, 0.3)"
  },
  blue: {
    primary: "#3B82F6",
    light: "#60A5FA",
    dark: "#2563EB",
    bg: "rgba(59, 130, 246, 0.1)",
    border: "rgba(59, 130, 246, 0.3)"
  },
  amber: {
    primary: "#F59E0B",
    light: "#FBBF24",
    dark: "#D97706",
    bg: "rgba(245, 158, 11, 0.1)",
    border: "rgba(245, 158, 11, 0.3)"
  },
  violet: {
    primary: "#8B5CF6",
    light: "#A78BFA",
    dark: "#7C3AED",
    bg: "rgba(139, 92, 246, 0.1)",
    border: "rgba(139, 92, 246, 0.3)"
  },
  slate: {
    bg: "#F8FAFC",
    card: "#FFFFFF",
    border: "#E2E8F0",
    text: "#334155",
    muted: "#64748B"
  }
};

// Enhanced Stat Card Component for Service Tickets
const ServiceMetricCard = ({ title, value, subtitle, icon: Icon, color = "emerald", className = "" }) => {
  const colorStyles = BRAND_COLORS[color] || BRAND_COLORS.emerald;
  
  return (
    <Card className={`relative overflow-hidden bg-white border border-slate-200 hover:border-slate-300 hover:shadow-lg transition-all duration-300 ${className}`}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <p className="text-3xl font-bold text-slate-800">{value}</p>
            <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
          </div>
          <div 
            className="p-3 rounded-xl" 
            style={{ backgroundColor: colorStyles.bg }}
          >
            <Icon className="h-5 w-5" style={{ color: colorStyles.primary }} />
          </div>
        </div>
        {/* Accent line at bottom */}
        <div 
          className="absolute bottom-0 left-0 right-0 h-1 opacity-60"
          style={{ backgroundColor: colorStyles.primary }}
        />
      </CardContent>
    </Card>
  );
};

// KPI Card with progress
const KPICard = ({ title, description, value, unit = "", target, icon: Icon, color = "emerald", children }) => {
  const colorStyles = BRAND_COLORS[color] || BRAND_COLORS.emerald;
  const percentage = target ? Math.min((parseFloat(value) / target) * 100, 100) : 0;
  const isOnTarget = target ? parseFloat(value) >= target : true;
  
  return (
    <Card className="bg-white border border-slate-200 hover:shadow-md transition-all duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          {Icon && (
            <div className="p-1.5 rounded-lg" style={{ backgroundColor: colorStyles.bg }}>
              <Icon className="h-4 w-4" style={{ color: colorStyles.primary }} />
            </div>
          )}
          <div>
            <CardTitle className="text-base font-semibold text-slate-700">{title}</CardTitle>
            <CardDescription className="text-xs">{description}</CardDescription>
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
        <div className="h-8 bg-slate-100 rounded-lg w-48 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-100 rounded-xl animate-pulse" />
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
    <div className="space-y-6 animate-fadeIn" data-testid="dashboard-page">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">A high-level overview of your garage's operations.</p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="workshop" className="w-full">
        <TabsList className="bg-card/50 border border-white/10">
          <TabsTrigger value="workshop" data-testid="workshop-tab">Workshop Overview</TabsTrigger>
          <TabsTrigger value="service-tickets" data-testid="service-tickets-tab">Service Tickets</TabsTrigger>
          <TabsTrigger value="receivables" data-testid="receivables-tab">Receivables Overview</TabsTrigger>
        </TabsList>

        {/* ==================== WORKSHOP OVERVIEW TAB ==================== */}
        <TabsContent value="workshop" className="mt-6">
          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
            <MetricCard
              title="Vehicles in Workshop"
              value={stats?.vehicles_in_workshop || 0}
              subtitle="Currently being serviced"
              icon={Wrench}
              iconClassName="bg-primary/10"
              data-testid="vehicles-in-workshop-card"
            />

            <MetricCard
              title="Open Repair Orders"
              value={stats?.open_repair_orders || 0}
              subtitle="Active service tickets"
              icon={Car}
              iconClassName="bg-chart-2/10"
              data-testid="open-orders-card"
            />

            <MetricCard
              title="Avg. Repair Time"
              value={<>{stats?.avg_repair_time || 0} <span className="text-base sm:text-lg font-normal">Hours</span></>}
              subtitle="For all closed tickets"
              icon={Clock}
              iconClassName="bg-chart-3/10"
              data-testid="repair-time-card"
            />

            <MetricCard
              title="Available Technicians"
              value={stats?.available_technicians || 0}
              subtitle="Ready for assignment"
              icon={Users}
              iconClassName="bg-chart-4/10"
              data-testid="technicians-card"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Vehicle Status Distribution */}
            <Card className="chart-container" data-testid="vehicle-status-chart">
              <CardHeader>
                <CardTitle className="text-xl">Vehicle Status Distribution</CardTitle>
                <CardDescription>Live breakdown of vehicle statuses in the workshop.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[280px] flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={vehicleStatusData}
                        cx="50%"
                        cy="50%"
                        innerRadius={70}
                        outerRadius={100}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {vehicleStatusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(217 33% 17%)', 
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                          color: 'white'
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  {vehicleStatusData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full" style={{ backgroundColor: entry.fill }} />
                      <span className="text-sm text-muted-foreground">{entry.name}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Repair Time Trend */}
            <Card className="chart-container" data-testid="repair-trend-chart">
              <CardHeader>
                <CardTitle className="text-xl">Repair Time Trend</CardTitle>
                <CardDescription>Monthly average time (in hours) per repair order.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={repairTrendData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                      <XAxis 
                        dataKey="month" 
                        axisLine={false} 
                        tickLine={false}
                        tick={{ fill: 'hsl(215 20% 65%)', fontSize: 12 }}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false}
                        tick={{ fill: 'hsl(215 20% 65%)', fontSize: 12 }}
                        tickFormatter={(value) => `${value}h`}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(217 33% 17%)', 
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                          color: 'white'
                        }}
                        formatter={(value) => [`${value} hours`, 'Avg Time']}
                      />
                      <Bar 
                        dataKey="avgTime" 
                        fill={CHART_COLORS.primary} 
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ==================== SERVICE TICKETS TAB ==================== */}
        <TabsContent value="service-tickets" className="mt-6">
          {/* Service Ticket Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
            {/* Total Open Tickets */}
            <Card className="bg-gradient-to-br from-slate-800/80 to-slate-900 border-slate-700" data-testid="total-open-tickets-card">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Total Open Tickets</p>
                    <p className="text-4xl font-bold text-white">{serviceTicketStats.total_open}</p>
                    <p className="text-xs text-slate-500 mt-2">Active service requests</p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-lg">
                    <AlertCircle className="h-6 w-6 text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Onsite Resolution */}
            <Card className="bg-gradient-to-br from-emerald-900/30 to-slate-900 border-emerald-700/50" data-testid="onsite-tickets-card">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-emerald-400 mb-1">Onsite Resolution</p>
                    <p className="text-4xl font-bold text-white">{serviceTicketStats.onsite_resolution}</p>
                    <p className="text-xs text-slate-500 mt-2">At customer location</p>
                  </div>
                  <div className="p-3 bg-emerald-500/10 rounded-lg">
                    <MapPin className="h-6 w-6 text-emerald-400" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Workshop Visit */}
            <Card className="bg-gradient-to-br from-blue-900/30 to-slate-900 border-blue-700/50" data-testid="workshop-tickets-card">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-blue-400 mb-1">Workshop Visit</p>
                    <p className="text-4xl font-bold text-white">{serviceTicketStats.workshop_visit}</p>
                    <p className="text-xs text-slate-500 mt-2">At service center</p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-lg">
                    <Building2 className="h-6 w-6 text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Avg Resolution Time */}
            <Card className="bg-gradient-to-br from-amber-900/30 to-slate-900 border-amber-700/50" data-testid="avg-resolution-card">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-amber-400 mb-1">Avg. Resolution Time</p>
                    <p className="text-4xl font-bold text-white">
                      {serviceTicketStats.avg_resolution_time_hours}
                      <span className="text-lg font-normal text-slate-400 ml-1">hrs</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-2">All closed tickets</p>
                  </div>
                  <div className="p-3 bg-amber-500/10 rounded-lg">
                    <Clock className="h-6 w-6 text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Second Row - KPIs */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Onsite Resolution Rate */}
            <Card className="bg-slate-800/50 border-slate-700" data-testid="onsite-rate-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-emerald-400" />
                  Onsite Resolution Rate
                </CardTitle>
                <CardDescription>Last 30 days performance</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-baseline justify-between">
                    <span className="text-5xl font-bold text-white">
                      {serviceTicketStats.onsite_resolution_percentage}%
                    </span>
                    <Badge 
                      variant="outline" 
                      className={`${serviceTicketStats.onsite_resolution_percentage >= 50 ? 'border-emerald-500 text-emerald-400' : 'border-amber-500 text-amber-400'}`}
                    >
                      {serviceTicketStats.onsite_resolution_percentage >= 50 ? 'Good' : 'Improving'}
                    </Badge>
                  </div>
                  <Progress 
                    value={serviceTicketStats.onsite_resolution_percentage} 
                    className="h-2 bg-slate-700"
                  />
                  <p className="text-sm text-slate-400">
                    {serviceTicketStats.total_onsite_resolved_30d} of {serviceTicketStats.total_resolved_30d} tickets resolved onsite
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Pickup & Remote */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Other Resolution Types</CardTitle>
                <CardDescription>Pickup & Remote support tickets</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-amber-500/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Truck className="h-5 w-5 text-amber-400" />
                      <span className="text-white">Pickup Service</span>
                    </div>
                    <span className="text-2xl font-bold text-amber-400">{serviceTicketStats.pickup}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-violet-500/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Wifi className="h-5 w-5 text-violet-400" />
                      <span className="text-white">Remote Support</span>
                    </div>
                    <span className="text-2xl font-bold text-violet-400">{serviceTicketStats.remote}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Resolution Summary */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  30-Day Summary
                </CardTitle>
                <CardDescription>Tickets resolved in last month</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center py-4">
                    <p className="text-5xl font-bold text-white">{serviceTicketStats.total_resolved_30d}</p>
                    <p className="text-sm text-slate-400 mt-1">Total Resolved</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-2 bg-emerald-500/10 rounded-lg">
                      <p className="text-xl font-bold text-emerald-400">{serviceTicketStats.total_onsite_resolved_30d}</p>
                      <p className="text-xs text-slate-400">Onsite</p>
                    </div>
                    <div className="text-center p-2 bg-blue-500/10 rounded-lg">
                      <p className="text-xl font-bold text-blue-400">
                        {serviceTicketStats.total_resolved_30d - serviceTicketStats.total_onsite_resolved_30d}
                      </p>
                      <p className="text-xs text-slate-400">Workshop/Other</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Ticket Distribution Pie Chart */}
            <Card className="chart-container" data-testid="ticket-distribution-chart">
              <CardHeader>
                <CardTitle className="text-xl">Open Tickets by Type</CardTitle>
                <CardDescription>Distribution of active service tickets by resolution type.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[280px] flex items-center justify-center">
                  {ticketDistributionData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={ticketDistributionData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={95}
                          paddingAngle={4}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value}`}
                          labelLine={false}
                        >
                          {ticketDistributionData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'hsl(217 33% 17%)', 
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '8px',
                            color: 'white'
                          }}
                        />
                        <Legend 
                          verticalAlign="bottom"
                          formatter={(value) => <span style={{ color: 'hsl(215 20% 75%)' }}>{value}</span>}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-slate-400">No open tickets</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats Summary */}
            <Card className="chart-container">
              <CardHeader>
                <CardTitle className="text-xl">Resolution Efficiency</CardTitle>
                <CardDescription>Key performance indicators for service tickets.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Onsite vs Workshop Comparison */}
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm text-slate-400">Onsite vs Workshop (Open)</span>
                      <span className="text-sm text-slate-400">
                        {serviceTicketStats.onsite_resolution} : {serviceTicketStats.workshop_visit}
                      </span>
                    </div>
                    <div className="flex h-4 rounded-full overflow-hidden bg-slate-700">
                      <div 
                        className="bg-emerald-500 transition-all duration-500"
                        style={{ 
                          width: `${serviceTicketStats.total_open > 0 
                            ? (serviceTicketStats.onsite_resolution / serviceTicketStats.total_open) * 100 
                            : 0}%` 
                        }}
                      />
                      <div 
                        className="bg-blue-500 transition-all duration-500"
                        style={{ 
                          width: `${serviceTicketStats.total_open > 0 
                            ? (serviceTicketStats.workshop_visit / serviceTicketStats.total_open) * 100 
                            : 0}%` 
                        }}
                      />
                    </div>
                  </div>

                  {/* Performance Metrics */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-700/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Target Resolution</p>
                      <p className="text-2xl font-bold text-white">8 hrs</p>
                      <p className="text-xs text-emerald-400 mt-1">
                        {serviceTicketStats.avg_resolution_time_hours <= 8 ? '✓ On Target' : '⚠ Above Target'}
                      </p>
                    </div>
                    <div className="p-4 bg-slate-700/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Onsite Target</p>
                      <p className="text-2xl font-bold text-white">40%</p>
                      <p className="text-xs text-emerald-400 mt-1">
                        {serviceTicketStats.onsite_resolution_percentage >= 40 ? '✓ On Target' : '⚠ Below Target'}
                      </p>
                    </div>
                  </div>

                  {/* Real-time Sync Indicator */}
                  <div className="flex items-center justify-center gap-2 pt-4 border-t border-slate-700">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs text-slate-400">Real-time sync enabled (30s refresh)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ==================== RECEIVABLES TAB ==================== */}
        <TabsContent value="receivables" className="mt-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
            <MetricCard
              title="Total Revenue"
              value={<>₹{(stats?.total_revenue || 0).toLocaleString('en-IN')}</>}
              subtitle="All time"
              icon={TrendingUp}
              iconClassName="bg-emerald-500/10"
            />
            <MetricCard
              title="Pending Invoices"
              value={<>₹{(stats?.pending_invoices || 0).toLocaleString('en-IN')}</>}
              subtitle="Outstanding amount"
              icon={AlertCircle}
              iconClassName="bg-amber-500/10"
            />
            <MetricCard
              title="Inventory Value"
              value={<>₹{(stats?.inventory_value || 0).toLocaleString('en-IN')}</>}
              subtitle="Current stock"
              icon={Building2}
              iconClassName="bg-blue-500/10"
            />
            <MetricCard
              title="Pending POs"
              value={stats?.pending_purchase_orders || 0}
              subtitle="Open orders"
              icon={Truck}
              iconClassName="bg-violet-500/10"
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
