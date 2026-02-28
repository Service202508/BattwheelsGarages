import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Users, Ticket, Clock, TrendingUp, Award, Star,
  BarChart3, AlertTriangle, CheckCircle, ArrowUpRight,
  ArrowDownRight, Minus, Eye, Download, Calendar
} from "lucide-react";
import { API } from "@/App";

export default function TechnicianProductivity({ user }) {
  const [summary, setSummary] = useState(null);
  const [technicians, setTechnicians] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [trends, setTrends] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState("month");
  const [selectedTechnician, setSelectedTechnician] = useState(null);
  const [technicianDetail, setTechnicianDetail] = useState(null);

  useEffect(() => {
    fetchData();
  }, [period]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      // Fetch summary
      const summaryRes = await fetch(`${API}/productivity/summary`, { headers, credentials: "include" });
      if (summaryRes.ok) setSummary(await summaryRes.json());
      
      // Fetch technician productivity
      const techRes = await fetch(`${API}/productivity/technicians?period=${period}`, { headers, credentials: "include" });
      if (techRes.ok) setTechnicians(await techRes.json());
      
      // Fetch KPIs
      const kpisRes = await fetch(`${API}/productivity/kpis`, { headers, credentials: "include" });
      if (kpisRes.ok) setKpis(await kpisRes.json());
      
      // Fetch trends
      const trendsRes = await fetch(`${API}/productivity/trends`, { headers, credentials: "include" });
      if (trendsRes.ok) setTrends(await trendsRes.json());
      
      // Fetch leaderboard
      const leaderRes = await fetch(`${API}/productivity/leaderboard?period=${period}`, { headers, credentials: "include" });
      if (leaderRes.ok) setLeaderboard(await leaderRes.json());
      
    } catch (error) {
      console.error("Failed to fetch productivity data:", error);
      toast.error("Failed to load productivity data");
    } finally {
      setLoading(false);
    }
  };

  const fetchTechnicianDetail = async (techId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/productivity/technicians/${techId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setTechnicianDetail(data);
        setSelectedTechnician(techId);
      }
    } catch (error) {
      toast.error("Failed to load technician details");
    }
  };

  const getPerformanceColor = (value, metric) => {
    if (metric === "resolution_time") {
      if (value <= 4) return "text-green-600";
      if (value <= 8) return "text-[#EAB308]";
      return "text-red-600";
    }
    if (metric === "tickets") {
      if (value >= 10) return "text-green-600";
      if (value >= 5) return "text-[#EAB308]";
      return "text-red-600";
    }
    return "text-[rgba(244,246,240,0.35)]";
  };

  const getPerformanceBadge = (tickets, avgTime) => {
    if (tickets >= 10 && avgTime <= 4) return { label: "Excellent", color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]" };
    if (tickets >= 5 && avgTime <= 8) return { label: "Good", color: "bg-blue-100 text-[#3B9EFF]" };
    if (tickets >= 3) return { label: "Average", color: "bg-yellow-100 text-[#EAB308]" };
    return { label: "Needs Improvement", color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]" };
  };

  // Simple bar chart using divs
  const SimpleBarChart = ({ data, maxValue }) => {
    const max = maxValue || Math.max(...data.map(d => d.value), 1);
    return (
      <div className="flex items-end gap-1 h-32">
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div 
              className="w-full bg-[#C8FF00] rounded-t transition-all duration-300 hover:bg-[#d4ff1a]"
              style={{ height: `${(item.value / max) * 100}%`, minHeight: item.value > 0 ? '4px' : '0' }}
            />
            <span className="text-xs text-[rgba(244,246,240,0.45)] mt-1 truncate w-full text-center">{item.label}</span>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="technician-productivity">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Technician Productivity</h1>
          <p className="text-[rgba(244,246,240,0.35)]">Monitor and analyze technician performance metrics.</p>
        </div>
        <div className="flex gap-2">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-36">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="all">All Time</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Users className="h-5 w-5 text-[#3B9EFF]" />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.35)]">Active Technicians</p>
                <p className="text-2xl font-bold">{summary?.active_technicians || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[rgba(34,197,94,0.10)]">
                <Ticket className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.35)]">Total Tickets Resolved</p>
                <p className="text-2xl font-bold">{summary?.total_tickets_resolved || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-100">
                <Clock className="h-5 w-5 text-[#FF8C00]" />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.35)]">Overall Avg. Resolution Time</p>
                <p className="text-2xl font-bold">{summary?.avg_resolution_time_hours || 0} hrs</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <CheckCircle className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.35)]">SLA Compliance</p>
                <p className="text-2xl font-bold">{kpis?.sla_compliance_percent || 0}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* KPI Alerts */}
      {kpis && (kpis.overdue_tickets > 0 || kpis.pending_tickets > 5) && (
        <Card className="border-orange-200 bg-[rgba(255,140,0,0.08)]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-[#FF8C00]" />
              <div className="flex-1">
                <p className="font-medium text-orange-900">Attention Required</p>
                <p className="text-sm text-[#FF8C00]">
                  {kpis.overdue_tickets > 0 && `${kpis.overdue_tickets} overdue tickets. `}
                  {kpis.pending_tickets > 5 && `${kpis.pending_tickets} tickets pending assignment.`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Productivity Breakdown Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Productivity Breakdown</CardTitle>
              <CardDescription>Individual technician performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              {technicians.length === 0 ? (
                <div className="text-center py-8 text-[rgba(244,246,240,0.45)]">
                  <Users className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
                  <p>No technician data available</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Technician</TableHead>
                      <TableHead className="text-right">Tickets Resolved</TableHead>
                      <TableHead className="text-right">Avg. Time (Hours)</TableHead>
                      <TableHead className="text-right">High/Critical</TableHead>
                      <TableHead className="text-right">Performance</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {technicians.map((tech, index) => {
                      const performance = getPerformanceBadge(tech.tickets_resolved, tech.avg_resolution_hours);
                      return (
                        <TableRow key={tech.technician_id || index}>
                          <TableCell>
                            <div>
                              <p className="font-medium">{tech.technician_name}</p>
                              <p className="text-xs text-[rgba(244,246,240,0.45)]">{tech.email}</p>
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <span className={`font-semibold ${getPerformanceColor(tech.tickets_resolved, 'tickets')}`}>
                              {tech.tickets_resolved}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <span className={getPerformanceColor(tech.avg_resolution_hours, 'resolution_time')}>
                              {tech.avg_resolution_hours || '-'}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">{tech.high_critical_tickets}</TableCell>
                          <TableCell className="text-right">
                            <Badge className={performance.color}>{performance.label}</Badge>
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => fetchTechnicianDetail(tech.technician_id)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Leaderboard */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5 text-yellow-500" />
                Top Performers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {leaderboard.slice(0, 5).map((tech, index) => (
                  <div key={tech.technician_id} className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                      index === 0 ? 'bg-[rgba(234,179,8,0.10)]' :
                      index === 1 ? 'bg-[rgba(244,246,240,0.35)]' :
                      index === 2 ? 'bg-amber-600' :
                      'bg-[#141E27]'
                    }`}>
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{tech.technician_name}</p>
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">{tech.tickets_resolved} tickets</p>
                    </div>
                    <div className="flex items-center gap-1 text-yellow-500">
                      <Star className="h-4 w-4 fill-current" />
                      <span className="text-sm">{tech.customer_rating}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Tickets Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-[#C8FF00] text-500" />
                Tickets Resolved (Weekly)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {trends.length > 0 ? (
                <SimpleBarChart 
                  data={trends.map(t => ({ label: t.week, value: t.tickets_resolved }))}
                />
              ) : (
                <div className="h-32 flex items-center justify-center text-[rgba(244,246,240,0.45)]">
                  No trend data
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Today's Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[rgba(244,246,240,0.35)]">Resolved Today</span>
                <span className="font-bold text-green-600">{kpis?.tickets_resolved_today || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[rgba(244,246,240,0.35)]">Pending Assignment</span>
                <span className="font-bold text-[#EAB308]">{kpis?.pending_tickets || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[rgba(244,246,240,0.45)]">Overdue (&gt;48hrs)</span>
                <span className="font-bold text-[#FF3B2F]">{kpis?.overdue_tickets || 0}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Technician Detail Dialog */}
      <Dialog open={!!selectedTechnician} onOpenChange={() => setSelectedTechnician(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {technicianDetail && (
            <>
              <DialogHeader>
                <DialogTitle>{technicianDetail.technician?.name} - Performance Details</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-6 py-4">
                {/* Technician Info */}
                <div className="flex items-center gap-4 p-4 bg-[#111820] rounded-lg">
                  <div className="h-12 w-12 rounded-full bg-[rgba(200,255,0,0.10)] flex items-center justify-center">
                    <span className="text-[#C8FF00] text-700 font-bold text-lg">
                      {technicianDetail.technician?.name?.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <p className="font-semibold">{technicianDetail.technician?.name}</p>
                    <p className="text-sm text-[rgba(244,246,240,0.45)]">{technicianDetail.technician?.email}</p>
                  </div>
                </div>

                {/* Status Breakdown */}
                <div>
                  <h4 className="font-semibold mb-3">Ticket Status Breakdown</h4>
                  <div className="grid grid-cols-5 gap-2">
                    {Object.entries(technicianDetail.status_breakdown || {}).map(([status, count]) => (
                      <div key={status} className="text-center p-2 rounded-lg bg-[#111820]">
                        <p className="text-xl font-bold">{count}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)] capitalize">{status.replace('_', ' ')}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Priority Breakdown */}
                <div>
                  <h4 className="font-semibold mb-3">Resolved by Priority</h4>
                  <div className="space-y-2">
                    {Object.entries(technicianDetail.priority_breakdown || {}).map(([priority, count]) => (
                      <div key={priority} className="flex items-center gap-3">
                        <span className="w-20 text-sm capitalize text-[rgba(244,246,240,0.35)]">{priority}</span>
                        <Progress value={(count / (Object.values(technicianDetail.priority_breakdown).reduce((a, b) => a + b, 0) || 1)) * 100} className="flex-1 h-2" />
                        <span className="w-8 text-right font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Monthly Trend */}
                <div>
                  <h4 className="font-semibold mb-3">Monthly Performance</h4>
                  <SimpleBarChart 
                    data={(technicianDetail.monthly_trend || []).map(m => ({ 
                      label: m.month, 
                      value: m.tickets_resolved 
                    }))}
                  />
                </div>

                {/* Recent Tickets */}
                <div>
                  <h4 className="font-semibold mb-3">Recent Tickets</h4>
                  <div className="space-y-2">
                    {(technicianDetail.recent_tickets || []).slice(0, 5).map((ticket) => (
                      <div key={ticket.ticket_id} className="flex items-center justify-between p-2 rounded border">
                        <div>
                          <p className="text-sm font-medium">{ticket.title}</p>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">{ticket.vehicle_number}</p>
                        </div>
                        <Badge className={
                          ticket.status === 'resolved' || ticket.status === 'closed' 
                            ? 'bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]' 
                            : 'bg-blue-100 text-[#3B9EFF]'
                        }>
                          {ticket.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
