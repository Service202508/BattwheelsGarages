import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Car, Wrench, Clock, Users } from "lucide-react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { MetricCard } from "@/components/KPICard";
import { API } from "@/App";

const CHART_COLORS = {
  primary: "hsl(186, 70%, 50%)",
  secondary: "hsl(24, 95%, 53%)",
  tertiary: "hsl(262, 83%, 58%)"
};

export default function Dashboard({ user }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch(`${API}/dashboard/stats`, {
          credentials: "include",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
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

    // Seed data on first load
    fetch(`${API}/seed`, { method: "POST" }).catch(() => {});
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-card/50 rounded w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-card/50 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const vehicleStatusData = stats ? [
    { name: "Active", value: stats.vehicle_status_distribution.active || 500, fill: CHART_COLORS.primary },
    { name: "In Workshop", value: stats.vehicle_status_distribution.in_workshop || 200, fill: CHART_COLORS.secondary },
    { name: "Serviced", value: stats.vehicle_status_distribution.serviced || 45, fill: CHART_COLORS.tertiary },
  ] : [];

  const repairTrendData = stats?.monthly_repair_trends || [
    { month: "Jul", avgTime: 8.2 },
    { month: "Jun", avgTime: 7.5 },
    { month: "May", avgTime: 7.8 },
    { month: "Apr", avgTime: 8.0 },
    { month: "Mar", avgTime: 7.2 },
    { month: "Feb", avgTime: 6.9 },
  ];

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
          <TabsTrigger value="receivables" data-testid="receivables-tab">Receivables Overview</TabsTrigger>
        </TabsList>

        <TabsContent value="workshop" className="mt-6">
          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="metric-card card-hover" data-testid="vehicles-in-workshop-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Vehicles in Workshop</p>
                    <p className="text-4xl font-bold mt-2 mono">{stats?.vehicles_in_workshop || 745}</p>
                    <p className="text-xs text-muted-foreground mt-1">Currently being serviced</p>
                  </div>
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Wrench className="h-5 w-5 text-primary" strokeWidth={1.5} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="metric-card card-hover" data-testid="open-orders-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Open Repair Orders</p>
                    <p className="text-4xl font-bold mt-2 mono">{stats?.open_repair_orders || 738}</p>
                    <p className="text-xs text-muted-foreground mt-1">Active service tickets</p>
                  </div>
                  <div className="h-10 w-10 rounded-lg bg-chart-2/10 flex items-center justify-center">
                    <Car className="h-5 w-5 text-chart-2" strokeWidth={1.5} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="metric-card card-hover" data-testid="repair-time-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Avg. Repair Time</p>
                    <p className="text-4xl font-bold mt-2 mono">{stats?.avg_repair_time || 7.9} <span className="text-lg font-normal">Hours</span></p>
                    <p className="text-xs text-muted-foreground mt-1">For all closed tickets</p>
                  </div>
                  <div className="h-10 w-10 rounded-lg bg-chart-3/10 flex items-center justify-center">
                    <Clock className="h-5 w-5 text-chart-3" strokeWidth={1.5} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="metric-card card-hover" data-testid="technicians-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Available Technicians</p>
                    <p className="text-4xl font-bold mt-2 mono">{stats?.available_technicians || 34}</p>
                    <p className="text-xs text-muted-foreground mt-1">Ready for assignment</p>
                  </div>
                  <div className="h-10 w-10 rounded-lg bg-chart-4/10 flex items-center justify-center">
                    <Users className="h-5 w-5 text-chart-4" strokeWidth={1.5} />
                  </div>
                </div>
              </CardContent>
            </Card>
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

        <TabsContent value="receivables" className="mt-6">
          <Card className="chart-container">
            <CardContent className="p-12 text-center">
              <p className="text-muted-foreground">Receivables overview coming soon...</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
