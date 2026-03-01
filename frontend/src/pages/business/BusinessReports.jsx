import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import {
  BarChart3, PieChart, Loader2, Download, Calendar,
  Ticket, Car, IndianRupee, TrendingUp, Clock, AlertCircle
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

export default function BusinessReports({ user }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState("month");

  useEffect(() => {
    fetchReportData();
  }, [dateRange]);

  const getDateRange = () => {
    const now = new Date();
    let startDate, endDate;
    
    switch (dateRange) {
      case "week":
        startDate = new Date(now.setDate(now.getDate() - 7));
        break;
      case "month":
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case "quarter":
        startDate = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
        break;
      case "year": {
        // Indian Financial Year: April 1 to March 31
        const month = new Date().getMonth() + 1;
        const fyStart = month >= 4 ? new Date().getFullYear() : new Date().getFullYear() - 1;
        startDate = new Date(fyStart, 3, 1);
        break;
      }
      default:
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
    }
    
    endDate = new Date();
    
    return {
      start: startDate.toISOString().split("T")[0],
      end: endDate.toISOString().split("T")[0]
    };
  };

  const fetchReportData = async () => {
    setLoading(true);
    try {
      const { start, end } = getDateRange();
      const res = await fetch(`${API}/business/reports/summary?start_date=${start}&end_date=${end}`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setReportData(data);
      }
    } catch (error) {
      console.error("Failed to fetch report:", error);
      toast.error("Failed to load report data");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const statusColorMap = {
    open: "#3B82F6",
    assigned: "#8B5CF6",
    work_in_progress: "#F59E0B",
    work_completed: "#10B981",
    closed: "#6B7280"
  };

  const priorityColorMap = {
    low: "#10B981",
    medium: "#F59E0B",
    high: "#F97316",
    critical: "#EF4444"
  };

  return (
    <div className="space-y-6" data-testid="business-reports">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Reports & Analytics</h1>
          <p className="text-slate-500">Insights into your fleet operations</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="week">Last 7 Days</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      ) : (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-4">
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Total Tickets</p>
                    <p className="text-2xl font-bold text-slate-900">{reportData?.tickets?.total || 0}</p>
                  </div>
                  <div className="p-3 rounded bg-indigo-50">
                    <Ticket className="h-5 w-5 text-indigo-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Total Invoiced</p>
                    <p className="text-2xl font-bold text-slate-900">{formatCurrency(reportData?.financials?.total_invoiced)}</p>
                  </div>
                  <div className="p-3 rounded bg-bw-volt/[0.08]">
                    <IndianRupee className="h-5 w-5 text-bw-volt text-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Paid</p>
                    <p className="text-2xl font-bold text-bw-volt text-600">{formatCurrency(reportData?.financials?.total_paid)}</p>
                  </div>
                  <div className="p-3 rounded bg-bw-volt/[0.08]">
                    <TrendingUp className="h-5 w-5 text-bw-volt text-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Outstanding</p>
                    <p className="text-2xl font-bold text-amber-600">{formatCurrency(reportData?.financials?.outstanding)}</p>
                  </div>
                  <div className="p-3 rounded bg-amber-50">
                    <Clock className="h-5 w-5 text-amber-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Tickets by Status */}
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5 text-indigo-600" />
                  Tickets by Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(reportData?.tickets?.by_status || {}).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: statusColorMap[status] || "#6B7280" }}
                        />
                        <span className="text-sm text-slate-600 capitalize">{status.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div 
                          className="h-2 rounded-full bg-white/5"
                          style={{ width: "100px" }}
                        >
                          <div 
                            className="h-2 rounded-full"
                            style={{ 
                              width: `${(count / (reportData?.tickets?.total || 1)) * 100}%`,
                              backgroundColor: statusColorMap[status] || "#6B7280"
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-900 w-8 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Tickets by Priority */}
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-amber-600" />
                  Tickets by Priority
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(reportData?.tickets?.by_priority || {}).map(([priority, count]) => (
                    <div key={priority} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: priorityColorMap[priority] || "#6B7280" }}
                        />
                        <span className="text-sm text-slate-600 capitalize">{priority}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div 
                          className="h-2 rounded-full bg-white/5"
                          style={{ width: "100px" }}
                        >
                          <div 
                            className="h-2 rounded-full"
                            style={{ 
                              width: `${(count / (reportData?.tickets?.total || 1)) * 100}%`,
                              backgroundColor: priorityColorMap[priority] || "#6B7280"
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-900 w-8 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Vehicle Breakdown */}
          <Card className="bg-bw-panel border-white/[0.07] border-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Car className="h-5 w-5 text-indigo-600" />
                Tickets by Vehicle
              </CardTitle>
              <CardDescription>Top 10 vehicles by service frequency</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.entries(reportData?.tickets?.by_vehicle || {}).slice(0, 10).map(([vehicle, count]) => (
                  <div key={vehicle} className="p-4 rounded bg-slate-50 text-center">
                    <Car className="h-6 w-6 text-slate-400 mx-auto mb-2" />
                    <p className="font-medium text-slate-900">{vehicle}</p>
                    <p className="text-2xl font-bold text-indigo-600">{count}</p>
                    <p className="text-xs text-slate-500">tickets</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Financial Summary */}
          <Card className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white border border-white/[0.13]">
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-indigo-100 mb-4">Financial Summary</h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <p className="text-indigo-100 text-sm">Total Invoiced</p>
                  <p className="text-3xl font-bold mt-1">{formatCurrency(reportData?.financials?.total_invoiced)}</p>
                </div>
                <div>
                  <p className="text-indigo-100 text-sm">Total Paid</p>
                  <p className="text-3xl font-bold mt-1">{formatCurrency(reportData?.financials?.total_paid)}</p>
                </div>
                <div>
                  <p className="text-indigo-100 text-sm">Outstanding</p>
                  <p className="text-3xl font-bold mt-1">{formatCurrency(reportData?.financials?.outstanding)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
