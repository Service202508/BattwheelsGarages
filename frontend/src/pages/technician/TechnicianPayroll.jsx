import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  Wallet, Download, Loader2, IndianRupee, Calendar,
  TrendingUp, FileText, CheckCircle, Clock, ChevronRight
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  paid: "bg-[rgba(200,255,0,0.08)]0/20 text-[#C8FF00] text-400 border-[rgba(200,255,0,0.50)]/30",
  pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  processing: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

export default function TechnicianPayroll({ user }) {
  const [payslips, setPayslips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPayslip, setSelectedPayslip] = useState(null);

  useEffect(() => {
    fetchPayroll();
  }, []);

  const fetchPayroll = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/technician/payroll?months=12`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setPayslips(data.payslips || []);
      }
    } catch (error) {
      console.error("Failed to fetch payroll:", error);
      toast.error("Failed to load payroll data");
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

  const getMonthYear = (monthStr) => {
    if (!monthStr || typeof monthStr !== 'string') return "N/A";
    try {
      const parts = monthStr.split("-");
      if (parts.length < 2) return monthStr;
      const [year, month] = parts;
      return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString("en-US", { 
        month: "long", 
        year: "numeric" 
      });
    } catch (e) {
      return monthStr || "N/A";
    }
  };

  // Calculate totals from payslips
  const currentMonth = payslips[0];
  const ytdEarnings = payslips.reduce((sum, p) => sum + (p.net_pay || 0), 0);
  const avgMonthly = payslips.length > 0 ? ytdEarnings / payslips.length : 0;

  return (
    <div className="space-y-6" data-testid="technician-payroll">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Payroll</h1>
          <p className="text-slate-400">View your salary and payslips</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-green-500/20 via-emerald-500/10 to-slate-900 border border-green-500/20">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-[rgba(34,197,94,0.08)]0/20">
                <IndianRupee className="h-5 w-5 text-green-400" />
              </div>
              <Badge className="bg-[rgba(34,197,94,0.08)]0/20 text-green-400 border-green-500/30">Latest</Badge>
            </div>
            <p className="text-sm text-slate-400">Latest Salary</p>
            <p className="text-3xl font-bold text-white mt-1">
              {formatCurrency(currentMonth?.net_pay)}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {currentMonth ? getMonthYear(currentMonth.month) : "N/A"}
            </p>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-[rgba(255,255,255,0.07)] border-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <TrendingUp className="h-5 w-5 text-blue-400" />
              </div>
            </div>
            <p className="text-sm text-slate-400">YTD Earnings</p>
            <p className="text-3xl font-bold text-white mt-1">
              {formatCurrency(ytdEarnings)}
            </p>
            <p className="text-xs text-slate-500 mt-1">{payslips.length} payslips</p>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-[rgba(255,255,255,0.07)] border-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-[rgba(139,92,246,0.08)]0/10">
                <Wallet className="h-5 w-5 text-purple-400" />
              </div>
            </div>
            <p className="text-sm text-slate-400">Avg Monthly</p>
            <p className="text-3xl font-bold text-white mt-1">
              {formatCurrency(avgMonthly)}
            </p>
            <p className="text-xs text-slate-500 mt-1">per month</p>
          </CardContent>
        </Card>
      </div>

      {/* Latest Payslip Detail */}
      {currentMonth && (
        <Card className="bg-slate-900/50 border-[rgba(255,255,255,0.07)] border-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white">Latest Payslip</CardTitle>
                <CardDescription>{getMonthYear(currentMonth.month)}</CardDescription>
              </div>
              <Badge className={statusColors[currentMonth.status || 'paid']}>
                {currentMonth.status || 'paid'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              {/* Earnings */}
              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-3">Earnings</h4>
                <div className="space-y-2">
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">Basic Salary</span>
                    <span className="text-white font-medium">{formatCurrency(currentMonth.basic || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">HRA</span>
                    <span className="text-white font-medium">{formatCurrency(currentMonth.hra || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">Allowances</span>
                    <span className="text-white font-medium">{formatCurrency(currentMonth.allowances || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">Overtime</span>
                    <span className="text-white font-medium">{formatCurrency(currentMonth.overtime || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-[rgba(34,197,94,0.08)]0/10 border border-green-500/20">
                    <span className="text-green-400 font-medium">Gross Earnings</span>
                    <span className="text-green-400 font-bold">{formatCurrency(currentMonth.gross_pay || 0)}</span>
                  </div>
                </div>
              </div>
              
              {/* Deductions */}
              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-3">Deductions</h4>
                <div className="space-y-2">
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">PF</span>
                    <span className="text-red-400 font-medium">-{formatCurrency(currentMonth.pf || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">ESI</span>
                    <span className="text-red-400 font-medium">-{formatCurrency(currentMonth.esi || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">Professional Tax</span>
                    <span className="text-red-400 font-medium">-{formatCurrency(currentMonth.pt || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-300">TDS</span>
                    <span className="text-red-400 font-medium">-{formatCurrency(currentMonth.tds || 0)}</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-[rgba(255,59,47,0.08)]0/10 border border-red-500/20">
                    <span className="text-red-400 font-medium">Total Deductions</span>
                    <span className="text-red-400 font-bold">{formatCurrency(currentMonth.total_deductions || 0)}</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Net Pay */}
            <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-300">Net Pay</p>
                  <p className="text-3xl font-bold text-white">{formatCurrency(currentMonth.net_pay)}</p>
                </div>
                <Button className="bg-[#22C55E] hover:bg-[#16a34a]">
                  <Download className="h-4 w-4 mr-2" />
                  Download Payslip
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payslip History */}
      <Card className="bg-slate-900/50 border-[rgba(255,255,255,0.07)] border-800">
        <CardHeader>
          <CardTitle className="text-white">Payslip History</CardTitle>
          <CardDescription>Past 12 months</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-green-500" />
            </div>
          ) : payslips.length === 0 ? (
            <div className="py-12 text-center">
              <FileText className="h-12 w-12 mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">No payslips found</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {payslips.map((payslip, index) => (
                <div 
                  key={payslip.month || index} 
                  className="flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors cursor-pointer"
                  onClick={() => setSelectedPayslip(payslip)}
                  data-testid={`payslip-row-${payslip.month}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2.5 rounded-xl bg-slate-800">
                      <Calendar className="h-5 w-5 text-slate-400" />
                    </div>
                    <div>
                      <p className="text-white font-medium">{getMonthYear(payslip.month)}</p>
                      <p className="text-xs text-slate-500">
                        Gross: {formatCurrency(payslip.gross_pay)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-400">{formatCurrency(payslip.net_pay)}</p>
                      <Badge className={statusColors[payslip.status || 'paid']}>
                        {payslip.status || 'paid'}
                      </Badge>
                    </div>
                    <ChevronRight className="h-5 w-5 text-slate-500" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
