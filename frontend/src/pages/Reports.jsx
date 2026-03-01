import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  TrendingUp, TrendingDown, IndianRupee, Users, FileText,
  Calendar, Download, RefreshCw, BarChart3, PieChart, FileSpreadsheet,
  Loader2, ArrowUp, ArrowDown, ShieldAlert, Trophy
} from "lucide-react";
import { API } from "@/App";

export default function Reports() {
  const [activeTab, setActiveTab] = useState("profit-loss");
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  
  // Date ranges
  const [dateRange, setDateRange] = useState({
    start_date: new Date(Date.now() - 365*24*60*60*1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  
  // Report data
  const [profitLoss, setProfitLoss] = useState(null);
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [arAging, setArAging] = useState(null);
  const [apAging, setApAging] = useState(null);
  const [salesByCustomer, setSalesByCustomer] = useState(null);
  const [slaReport, setSlaReport] = useState(null);
  const [techReport, setTechReport] = useState(null);
  const [techPeriod, setTechPeriod] = useState("this_month");
  const [selectedTech, setSelectedTech] = useState(null);

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchActiveReport();
  }, [activeTab]);

  const fetchActiveReport = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case "profit-loss":
          await fetchProfitLoss();
          break;
        case "balance-sheet":
          await fetchBalanceSheet();
          break;
        case "ar-aging":
          await fetchArAging();
          break;
        case "ap-aging":
          await fetchApAging();
          break;
        case "sales-by-customer":
          await fetchSalesByCustomer();
          break;
        case "sla-performance":
          await fetchSlaReport();
          break;
        case "technician-performance":
          await fetchTechReport();
          break;
      }
    } catch (error) {
      console.error("Failed to fetch report:", error);
      toast.error("Error loading report");
    } finally {
      setLoading(false);
    }
  };

  const fetchProfitLoss = async () => {
    const res = await fetch(
      `${API}/reports/profit-loss?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`,
      { headers }
    );
    const data = await res.json();
    setProfitLoss(data);
  };

  const fetchBalanceSheet = async () => {
    const res = await fetch(`${API}/reports/balance-sheet?as_of_date=${asOfDate}`, { headers });
    const data = await res.json();
    setBalanceSheet(data);
  };

  const fetchArAging = async () => {
    const res = await fetch(`${API}/reports/ar-aging?as_of_date=${asOfDate}`, { headers });
    const data = await res.json();
    setArAging(data);
  };

  const fetchApAging = async () => {
    const res = await fetch(`${API}/reports/ap-aging?as_of_date=${asOfDate}`, { headers });
    const data = await res.json();
    setApAging(data);
  };

  const fetchSalesByCustomer = async () => {
    const res = await fetch(
      `${API}/reports/sales-by-customer?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`,
      { headers }
    );
    const data = await res.json();
    setSalesByCustomer(data);
  };

  const fetchSlaReport = async () => {
    const res = await fetch(
      `${API}/sla/breach-report?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`,
      { headers }
    );
    if (res.ok) {
      const data = await res.json();
      setSlaReport(data);
    } else {
      toast.error("Failed to load SLA report");
    }
  };

  const fetchTechReport = async (period = techPeriod) => {
    const params = period === "custom"
      ? `period=custom&date_from=${dateRange.start_date}&date_to=${dateRange.end_date}`
      : `period=${period}`;
    const res = await fetch(`${API}/reports/technician-performance?${params}`, { headers });
    if (res.ok) {
      const data = await res.json();
      setTechReport(data);
    } else {
      toast.error("Failed to load technician report");
    }
  };

  const exportTechReportCsv = () => {
    if (!techReport?.technicians?.length) { toast.error("No data to export"); return; }
    const cols = ["Rank","Technician","Assigned","Resolved","Resolution %","Avg Response (min)","Avg Resolution (min)","SLA Compliance %","SLA Breaches (Resp)","SLA Breaches (Res)"];
    const rows = techReport.technicians.map(t => [
      t.rank, t.technician_name, t.total_tickets_assigned, t.total_tickets_resolved,
      t.resolution_rate_pct, t.avg_response_time_minutes ?? "N/A", t.avg_resolution_time_minutes ?? "N/A",
      t.sla_compliance_rate_pct, t.sla_breaches_response, t.sla_breaches_resolution
    ]);
    const csv = [cols, ...rows].map(r => r.map(v => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = `Technician_Performance_${techPeriod}.csv`; a.click();
    URL.revokeObjectURL(url);
    toast.success("CSV exported");
  };

  const exportSlaReportCsv = () => {
    if (!slaReport?.breaches?.length) { toast.error("No data to export"); return; }
    const cols = ["Ticket ID", "Customer", "Priority", "Technician", "Breach Type", "Breach Time", "Reassigned"];
    const rows = slaReport.breaches.map(t => [
      t.ticket_id, t.customer_name || "N/A", t.priority,
      t.assigned_technician_name || "Unassigned",
      t.sla_resolution_breached ? "Resolution" : "Response",
      t.sla_resolution_breached_at || t.sla_response_breached_at || "N/A",
      t.sla_auto_reassigned ? "Yes" : "No"
    ]);
    const csv = [cols, ...rows].map(r => r.map(v => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `SLA_Breach_Report_${dateRange.start_date}_${dateRange.end_date}.csv`; a.click();
    URL.revokeObjectURL(url);
    toast.success("CSV exported");
  };

  const exportReport = async (format) => {
    setExporting(true);
    try {
      let url = "";
      let filename = "";
      
      switch (activeTab) {
        case "profit-loss":
          url = `${API}/reports/profit-loss?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}&format=${format}`;
          filename = `profit_loss_${dateRange.start_date}_to_${dateRange.end_date}`;
          break;
        case "balance-sheet":
          url = `${API}/reports/balance-sheet?as_of_date=${asOfDate}&format=${format}`;
          filename = `balance_sheet_${asOfDate}`;
          break;
        case "ar-aging":
          url = `${API}/reports/ar-aging?as_of_date=${asOfDate}&format=${format}`;
          filename = `ar_aging_${asOfDate}`;
          break;
        case "ap-aging":
          url = `${API}/reports/ap-aging?as_of_date=${asOfDate}&format=${format}`;
          filename = `ap_aging_${asOfDate}`;
          break;
        case "sales-by-customer":
          url = `${API}/reports/sales-by-customer?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}&format=${format}`;
          filename = `sales_by_customer_${dateRange.start_date}_to_${dateRange.end_date}`;
          break;
      }

      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error("Export failed");
      
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${filename}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error("Export failed:", error);
      toast.error("Failed to export report");
    } finally {
      setExporting(false);
    }
  };

  const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  const renderDateFilters = () => {
    const isPeriodReport = ["profit-loss", "sales-by-customer"].includes(activeTab);
    
    return (
      <div className="flex flex-wrap items-center gap-3">
        {isPeriodReport ? (
          <>
            <div className="flex items-center gap-2">
              <span className="text-sm text-bw-white/[0.45]">From</span>
              <Input 
                type="date" 
                value={dateRange.start_date} 
                onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
                className="w-40"
                data-testid="start-date-input"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-bw-white/[0.45]">To</span>
              <Input 
                type="date" 
                value={dateRange.end_date} 
                onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
                className="w-40"
                data-testid="end-date-input"
              />
            </div>
          </>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-sm text-bw-white/[0.45]">As of</span>
            <Input 
              type="date" 
              value={asOfDate} 
              onChange={(e) => setAsOfDate(e.target.value)}
              className="w-40"
              data-testid="as-of-date-input"
            />
          </div>
        )}
        <Button onClick={fetchActiveReport} variant="outline" size="sm" data-testid="refresh-report-btn">
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </Button>
        <div className="flex gap-2">
          <Button 
            onClick={() => exportReport("pdf")} 
            variant="outline" 
            size="sm"
            disabled={exporting}
            data-testid="export-pdf-btn"
          >
            {exporting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileText className="h-4 w-4 mr-2" />}
            PDF
          </Button>
          <Button 
            onClick={() => exportReport("excel")} 
            variant="outline" 
            size="sm"
            disabled={exporting}
            data-testid="export-excel-btn"
          >
            {exporting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileSpreadsheet className="h-4 w-4 mr-2" />}
            Excel
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6" data-testid="reports-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-bw-white">Financial Reports</h1>
          <p className="text-bw-white/[0.45] text-sm mt-1">Comprehensive business analytics & exports</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-7 h-auto">
          <TabsTrigger value="profit-loss" className="text-xs sm:text-sm py-2">
            <TrendingUp className="h-4 w-4 mr-1 hidden sm:block" />
            P&L
          </TabsTrigger>
          <TabsTrigger value="balance-sheet" className="text-xs sm:text-sm py-2">
            <BarChart3 className="h-4 w-4 mr-1 hidden sm:block" />
            Balance Sheet
          </TabsTrigger>
          <TabsTrigger value="ar-aging" className="text-xs sm:text-sm py-2">
            <ArrowUp className="h-4 w-4 mr-1 hidden sm:block" />
            AR Aging
          </TabsTrigger>
          <TabsTrigger value="ap-aging" className="text-xs sm:text-sm py-2">
            <ArrowDown className="h-4 w-4 mr-1 hidden sm:block" />
            AP Aging
          </TabsTrigger>
          <TabsTrigger value="sales-by-customer" className="text-xs sm:text-sm py-2">
            <Users className="h-4 w-4 mr-1 hidden sm:block" />
            Sales
          </TabsTrigger>
          <TabsTrigger value="sla-performance" className="text-xs sm:text-sm py-2" data-testid="sla-report-tab">
            <ShieldAlert className="h-4 w-4 mr-1 hidden sm:block" />
            SLA
          </TabsTrigger>
          <TabsTrigger value="technician-performance" className="text-xs sm:text-sm py-2" data-testid="tech-report-tab">
            <Trophy className="h-4 w-4 mr-1 hidden sm:block" />
            Technicians
          </TabsTrigger>
        </TabsList>

        {/* Profit & Loss Tab */}
        <TabsContent value="profit-loss" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Profit & Loss Statement</CardTitle>
                  <CardDescription>Income Statement for the period</CardDescription>
                </div>
                {renderDateFilters()}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-bw-volt" />
                </div>
              ) : profitLoss && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="bg-bw-panel border border-white/[0.07]">
                      <CardContent className="p-4">
                        <p className="text-xs text-bw-green font-medium">Total Income</p>
                        <p className="text-xl font-bold text-bw-green">{formatCurrency(profitLoss.total_income)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07]">
                      <CardContent className="p-4">
                        <p className="text-xs text-bw-orange font-medium">Cost of Goods</p>
                        <p className="text-xl font-bold text-bw-orange">{formatCurrency(profitLoss.total_cogs)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07]">
                      <CardContent className="p-4">
                        <p className="text-xs text-bw-blue font-medium">Gross Profit</p>
                        <p className="text-xl font-bold text-bw-blue">{formatCurrency(profitLoss.gross_profit)}</p>
                      </CardContent>
                    </Card>
                    <Card className={`bg-bw-panel border ${profitLoss.net_profit >= 0 ? 'border-bw-volt/25' : 'border-bw-red/25'}`}>
                      <CardContent className="p-4">
                        <p className={`text-xs font-medium ${profitLoss.net_profit >= 0 ? 'text-bw-volt' : 'text-bw-red'}`}>Net Profit</p>
                        <p className={`text-xl font-bold ${profitLoss.net_profit >= 0 ? 'text-bw-volt' : 'text-bw-red'}`}>
                          {formatCurrency(profitLoss.net_profit)}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Detailed Breakdown */}
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-bw-panel border-b border-white/[0.07]">
                        <TableHead className="font-semibold text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Account</TableHead>
                        <TableHead className="text-right font-semibold text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow className="bg-bw-green/[0.08] border-b border-white/[0.07]">
                        <TableCell className="font-semibold text-bw-green">INCOME</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow className="border-b border-white/[0.07]">
                        <TableCell className="pl-8 text-bw-white">Operating Income (Sales)</TableCell>
                        <TableCell className="text-right text-bw-white">{formatCurrency(profitLoss.total_income)}</TableCell>
                      </TableRow>
                      <TableRow className="bg-white/[0.03] border-b border-white/[0.07]">
                        <TableCell className="font-semibold text-bw-white">Total Income</TableCell>
                        <TableCell className="text-right font-semibold text-bw-green">{formatCurrency(profitLoss.total_income)}</TableCell>
                      </TableRow>
                      
                      <TableRow className="bg-bw-orange/[0.08] border-b border-white/[0.07]">
                        <TableCell className="font-semibold text-bw-orange">COST OF GOODS SOLD</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow className="border-b border-white/[0.07]">
                        <TableCell className="pl-8 text-bw-white">Direct Costs (Purchases/Bills)</TableCell>
                        <TableCell className="text-right text-bw-white">{formatCurrency(profitLoss.total_cogs)}</TableCell>
                      </TableRow>
                      <TableRow className="bg-bw-blue/[0.08] border-b border-white/[0.07]">
                        <TableCell className="font-semibold text-bw-blue">Gross Profit</TableCell>
                        <TableCell className="text-right font-semibold text-bw-blue">{formatCurrency(profitLoss.gross_profit)}</TableCell>
                      </TableRow>
                      
                      <TableRow className="bg-bw-red/[0.08] border-b border-white/[0.07]">
                        <TableCell className="font-semibold text-bw-red">OPERATING EXPENSES</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      {profitLoss.expenses_breakdown && Object.entries(profitLoss.expenses_breakdown).map(([cat, amt]) => (
                        <TableRow key={cat} className="border-b border-white/[0.07]">
                          <TableCell className="pl-8 text-bw-white">{cat}</TableCell>
                          <TableCell className="text-right text-bw-white">{formatCurrency(amt)}</TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-white/[0.03] border-b border-white/[0.07]">
                        <TableCell className="font-semibold text-bw-white">Total Expenses</TableCell>
                        <TableCell className="text-right font-semibold text-bw-red">{formatCurrency(profitLoss.total_expenses)}</TableCell>
                      </TableRow>
                      
                      <TableRow className="bg-bw-volt/10">
                        <TableCell className="font-bold text-lg text-bw-volt">NET PROFIT</TableCell>
                        <TableCell className={`text-right font-bold text-lg ${profitLoss.net_profit >= 0 ? 'text-bw-green' : 'text-bw-red'}`}>
                          {formatCurrency(profitLoss.net_profit)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  {/* Margins */}
                  <div className="flex gap-4 text-sm text-bw-white/[0.45]">
                    <span>Gross Margin: <strong className="text-bw-white">{profitLoss.margins?.gross_margin_percent || 0}%</strong></span>
                    <span>Net Margin: <strong className="text-bw-white">{profitLoss.margins?.net_margin_percent || 0}%</strong></span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Balance Sheet Tab */}
        <TabsContent value="balance-sheet" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Balance Sheet</CardTitle>
                  <CardDescription>Financial position as of a specific date</CardDescription>
                </div>
                {renderDateFilters()}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-bw-volt" />
                </div>
              ) : balanceSheet && (
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Assets */}
                  <Card className="bg-bw-panel border border-white/[0.07]">
                    <CardHeader className="bg-bw-green/[0.08] py-3 border-b border-white/[0.07]">
                      <CardTitle className="text-lg text-bw-green">Assets</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-3">
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.45]">Accounts Receivable</span>
                        <span className="font-medium text-bw-white">{formatCurrency(balanceSheet.assets?.accounts_receivable)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.45]">Bank Balance</span>
                        <span className="font-medium text-bw-white">{formatCurrency(balanceSheet.assets?.bank_balance)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.45]">Inventory Value</span>
                        <span className="font-medium text-bw-white">{formatCurrency(balanceSheet.assets?.inventory_value)}</span>
                      </div>
                      <div className="flex justify-between pt-3 border-t border-white/[0.07]">
                        <span className="font-semibold text-bw-green">Total Assets</span>
                        <span className="font-bold text-bw-green">{formatCurrency(balanceSheet.assets?.total)}</span>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Liabilities & Equity */}
                  <div className="space-y-4">
                    <Card className="bg-bw-panel border border-white/[0.07]">
                      <CardHeader className="bg-bw-red/[0.08] py-3 border-b border-white/[0.07]">
                        <CardTitle className="text-lg text-bw-red">Liabilities</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-3">
                        <div className="flex justify-between">
                          <span className="text-bw-white/[0.45]">Accounts Payable</span>
                          <span className="font-medium text-bw-white">{formatCurrency(balanceSheet.liabilities?.accounts_payable)}</span>
                        </div>
                        <div className="flex justify-between pt-3 border-t border-white/[0.07]">
                          <span className="font-semibold text-bw-red">Total Liabilities</span>
                          <span className="font-bold text-bw-red">{formatCurrency(balanceSheet.liabilities?.total)}</span>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="bg-bw-panel border border-white/[0.07]">
                      <CardHeader className="bg-bw-blue/[0.08] py-3 border-b border-white/[0.07]">
                        <CardTitle className="text-lg text-bw-blue">Equity</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-3">
                        <div className="flex justify-between">
                          <span className="text-bw-white/[0.45]">Retained Earnings</span>
                          <span className="font-medium text-bw-white">{formatCurrency(balanceSheet.equity?.retained_earnings)}</span>
                        </div>
                        <div className="flex justify-between pt-3 border-t border-white/[0.07]">
                          <span className="font-semibold text-bw-blue">Total Equity</span>
                          <span className="font-bold text-bw-blue">{formatCurrency(balanceSheet.equity?.total)}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* AR Aging Tab */}
        <TabsContent value="ar-aging" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Accounts Receivable Aging</CardTitle>
                  <CardDescription>Outstanding customer invoices by age</CardDescription>
                </div>
                {renderDateFilters()}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-bw-volt" />
                </div>
              ) : arAging && (
                <div className="space-y-6">
                  {/* Aging Buckets */}
                  <div className="grid grid-cols-5 gap-3">
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-green">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">Current</p>
                        <p className="text-lg font-bold text-bw-green">{formatCurrency(arAging.aging_data?.current)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-amber">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">1-30 Days</p>
                        <p className="text-lg font-bold text-bw-amber">{formatCurrency(arAging.aging_data?.["1_30"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-orange">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">31-60 Days</p>
                        <p className="text-lg font-bold text-bw-orange">{formatCurrency(arAging.aging_data?.["31_60"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-orange-600">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">61-90 Days</p>
                        <p className="text-lg font-bold text-orange-600">{formatCurrency(arAging.aging_data?.["61_90"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-red">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">90+ Days</p>
                        <p className="text-lg font-bold text-bw-red">{formatCurrency(arAging.aging_data?.over_90)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Total */}
                  <div className="bg-bw-volt/10 p-4 rounded border border-bw-volt/25 flex justify-between items-center">
                    <span className="font-semibold text-bw-white">Total Accounts Receivable</span>
                    <span className="text-2xl font-bold text-bw-volt">{formatCurrency(arAging.total_ar)}</span>
                  </div>

                  {/* Invoice Details Table */}
                  <div className="border border-white/[0.07] rounded overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-bw-panel border-b border-white/[0.07]">
                          <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Invoice #</TableHead>
                          <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Customer</TableHead>
                          <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Due Date</TableHead>
                          <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Days Overdue</TableHead>
                          <TableHead className="text-right text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Balance</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {arAging.invoices?.slice(0, 20).map((inv, idx) => (
                          <TableRow key={idx} className="border-b border-white/[0.07]">
                            <TableCell className="font-medium text-bw-white">{inv.invoice_number}</TableCell>
                            <TableCell className="text-bw-white">{inv.customer_name}</TableCell>
                            <TableCell className="text-bw-white">{inv.due_date}</TableCell>
                            <TableCell className="text-center">
                              <Badge variant={
                                inv.days_overdue <= 0 ? "success" :
                                inv.days_overdue <= 30 ? "warning" :
                                "destructive"
                              }>
                                {inv.days_overdue} days
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right font-medium text-bw-white">{formatCurrency(inv.balance)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    {arAging.invoices?.length > 20 && (
                      <div className="p-3 bg-bw-panel text-center text-sm text-bw-white/[0.45] border-t border-white/[0.07]">
                        Showing 20 of {arAging.invoices.length} invoices. Export to see all.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* AP Aging Tab */}
        <TabsContent value="ap-aging" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Accounts Payable Aging</CardTitle>
                  <CardDescription>Outstanding vendor bills by age</CardDescription>
                </div>
                {renderDateFilters()}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-bw-volt" />
                </div>
              ) : apAging && (
                <div className="space-y-6">
                  {/* Aging Buckets */}
                  <div className="grid grid-cols-5 gap-3">
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-green">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">Current</p>
                        <p className="text-lg font-bold text-bw-green">{formatCurrency(apAging.aging_data?.current)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-amber">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">1-30 Days</p>
                        <p className="text-lg font-bold text-bw-amber">{formatCurrency(apAging.aging_data?.["1_30"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-orange">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">31-60 Days</p>
                        <p className="text-lg font-bold text-bw-orange">{formatCurrency(apAging.aging_data?.["31_60"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-orange-600">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">61-90 Days</p>
                        <p className="text-lg font-bold text-orange-600">{formatCurrency(apAging.aging_data?.["61_90"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07] border-l-4 border-l-bw-red">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-bw-white/[0.45]">90+ Days</p>
                        <p className="text-lg font-bold text-bw-red">{formatCurrency(apAging.aging_data?.over_90)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Total */}
                  <div className="bg-bw-red/10 p-4 rounded border border-bw-red/25 flex justify-between items-center">
                    <span className="font-semibold text-bw-white">Total Accounts Payable</span>
                    <span className="text-2xl font-bold text-bw-red">{formatCurrency(apAging.total_ap)}</span>
                  </div>

                  {/* Bill Details Table */}
                  <div className="border border-white/[0.07] rounded overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-bw-panel border-b border-white/[0.07]">
                          <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Bill #</TableHead>
                          <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Vendor</TableHead>
                          <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Due Date</TableHead>
                          <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Days Overdue</TableHead>
                          <TableHead className="text-right text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Balance</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {apAging.bills?.slice(0, 20).map((bill, idx) => (
                          <TableRow key={idx} className="border-b border-white/[0.07]">
                            <TableCell className="font-medium text-bw-white">{bill.bill_number}</TableCell>
                            <TableCell className="text-bw-white">{bill.vendor_name}</TableCell>
                            <TableCell className="text-bw-white">{bill.due_date}</TableCell>
                            <TableCell className="text-center">
                              <Badge variant={
                                bill.days_overdue <= 0 ? "success" :
                                bill.days_overdue <= 30 ? "warning" :
                                "destructive"
                              }>
                                {bill.days_overdue} days
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right font-medium text-bw-white">{formatCurrency(bill.balance)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    {apAging.bills?.length > 20 && (
                      <div className="p-3 bg-bw-panel text-center text-sm text-bw-white/[0.45] border-t border-white/[0.07]">
                        Showing 20 of {apAging.bills.length} bills. Export to see all.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sales by Customer Tab */}
        <TabsContent value="sales-by-customer" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Sales by Customer</CardTitle>
                  <CardDescription>Revenue breakdown by customer for the period</CardDescription>
                </div>
                {renderDateFilters()}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-bw-volt" />
                </div>
              ) : salesByCustomer && (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="grid grid-cols-2 gap-4">
                    <Card className="bg-bw-panel border border-white/[0.07]">
                      <CardContent className="p-4">
                        <p className="text-xs text-bw-blue font-medium">Total Invoices</p>
                        <p className="text-2xl font-bold text-bw-blue">{salesByCustomer.total_invoices || 0}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-bw-panel border border-white/[0.07]">
                      <CardContent className="p-4">
                        <p className="text-xs text-bw-green font-medium">Total Sales</p>
                        <p className="text-2xl font-bold text-bw-green">{formatCurrency(salesByCustomer.total_sales)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Customer Table */}
                  <div className="border border-white/[0.07] rounded overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-bw-panel border-b border-white/[0.07]">
                          <TableHead className="w-12 text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">#</TableHead>
                          <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Customer Name</TableHead>
                          <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Invoices</TableHead>
                          <TableHead className="text-right text-bw-white/25 uppercase text-[10px] tracking-[0.12em] font-mono">Total Sales</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {salesByCustomer.sales_data?.map((item, idx) => (
                          <TableRow key={idx} className="border-b border-white/[0.07]">
                            <TableCell className="text-bw-white/[0.45]">{idx + 1}</TableCell>
                            <TableCell className="font-medium text-bw-white">{item.customer_name}</TableCell>
                            <TableCell className="text-center text-bw-white">{item.invoice_count}</TableCell>
                            <TableCell className="text-right font-medium text-bw-white">{formatCurrency(item.total_sales)}</TableCell>
                          </TableRow>
                        ))}
                        <TableRow className="bg-bw-volt/10 font-bold">
                          <TableCell></TableCell>
                          <TableCell className="text-bw-volt">TOTAL</TableCell>
                          <TableCell className="text-center text-bw-white">{salesByCustomer.total_invoices}</TableCell>
                          <TableCell className="text-right text-bw-volt">{formatCurrency(salesByCustomer.total_sales)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* SLA Performance Tab */}
        <TabsContent value="sla-performance" className="space-y-4">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <ShieldAlert className="h-5 w-5 text-red-400" />
                    SLA Performance Report
                  </CardTitle>
                  <CardDescription>SLA breaches, compliance rate, and auto-reassignments</CardDescription>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Input type="date" value={dateRange.start_date} onChange={e => setDateRange(p => ({ ...p, start_date: e.target.value }))} className="w-36 text-sm" />
                  <span className="text-muted-foreground text-xs">to</span>
                  <Input type="date" value={dateRange.end_date} onChange={e => setDateRange(p => ({ ...p, end_date: e.target.value }))} className="w-36 text-sm" />
                  <Button size="sm" variant="outline" onClick={fetchSlaReport} disabled={loading}>
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  </Button>
                  <Button size="sm" variant="outline" onClick={exportSlaReportCsv} data-testid="sla-export-csv-btn">
                    <Download className="h-4 w-4 mr-1" /> CSV
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-bw-volt" />
                </div>
              ) : slaReport ? (
                <div className="space-y-6">
                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {[
                      { label: "Total Tickets", value: slaReport.summary?.total_tickets_in_period ?? 0, color: "rgb(var(--bw-white))" },
                      { label: "Within SLA", value: slaReport.summary?.within_sla_count ?? 0, color: "rgb(var(--bw-green))" },
                      { label: "Response Breaches", value: slaReport.summary?.response_sla_breaches ?? 0, color: "rgb(var(--bw-red))" },
                      { label: "Resolution Breaches", value: slaReport.summary?.resolution_sla_breaches ?? 0, color: "rgb(var(--bw-orange))" },
                      { label: "Auto-Reassigned", value: slaReport.summary?.auto_reassignments_triggered ?? 0, color: "rgb(var(--bw-volt))" },
                    ].map(({ label, value, color }) => (
                      <Card key={label} className="bg-bw-panel border border-white/[0.07]">
                        <CardContent className="p-3">
                          <p className="text-xs text-bw-white/[0.45] mb-1">{label}</p>
                          <p className="text-2xl font-bold font-mono" style={{ color }}>{value}</p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Compliance % */}
                  <div className="flex items-center gap-3 p-4 rounded-lg border border-white/[0.07] bg-bw-panel">
                    <div className="text-4xl font-mono font-bold text-bw-volt">
                      {slaReport.summary?.sla_compliance_pct ?? 100}%
                    </div>
                    <div>
                      <p className="font-medium">SLA Compliance Rate</p>
                      <p className="text-xs text-muted-foreground">Period: {slaReport.period?.start_date?.split("T")[0]} → {slaReport.period?.end_date?.split("T")[0]}</p>
                    </div>
                  </div>

                  {/* Breach Table */}
                  {slaReport.breaches?.length > 0 ? (
                    <div className="border border-white/[0.07] rounded overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-bw-panel border-b border-white/[0.07]">
                            <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Ticket</TableHead>
                            <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Customer</TableHead>
                            <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Priority</TableHead>
                            <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Technician</TableHead>
                            <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Breach Type</TableHead>
                            <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Reassigned?</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {slaReport.breaches.map((t) => (
                            <TableRow key={t.ticket_id} className="border-b border-white/5" data-testid={`sla-breach-row-${t.ticket_id}`}>
                              <TableCell className="font-mono text-xs text-bw-blue">{t.ticket_id}</TableCell>
                              <TableCell className="text-bw-white">{t.customer_name || "N/A"}</TableCell>
                              <TableCell>
                                <span style={{
                                  padding: "2px 6px", borderRadius: "2px", fontSize: "10px", fontFamily: "monospace",
                                  background: t.priority === "critical" ? "rgba(255,59,47,0.15)" : t.priority === "high" ? "rgba(255,140,0,0.15)" : "rgba(234,179,8,0.15)",
                                  color: t.priority === "critical" ? "rgb(var(--bw-red))" : t.priority === "high" ? "rgb(var(--bw-orange))" : "rgb(var(--bw-amber))"
                                }}>{t.priority?.toUpperCase()}</span>
                              </TableCell>
                              <TableCell className="text-bw-white/[0.65]">{t.assigned_technician_name || "Unassigned"}</TableCell>
                              <TableCell>
                                {t.sla_resolution_breached && <span className="text-bw-red text-xs">Resolution</span>}
                                {!t.sla_resolution_breached && t.sla_response_breached && <span className="text-bw-orange text-xs">Response</span>}
                              </TableCell>
                              <TableCell>
                                {t.sla_auto_reassigned
                                  ? <span className="text-bw-volt text-xs">Yes → {t.assigned_technician_name}</span>
                                  : <span className="text-bw-white/25 text-xs">No</span>
                                }
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                      <ShieldAlert className="h-10 w-10 mb-3 opacity-30" />
                      <p className="text-sm">No SLA breaches in selected period</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <ShieldAlert className="h-10 w-10 mb-3 opacity-30" />
                  <p className="text-sm">Select a date range and click refresh to load SLA report</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Technician Performance Tab */}
        <TabsContent value="technician-performance" className="space-y-4">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="h-5 w-5 text-bw-volt" />
                    Technician Performance
                  </CardTitle>
                  <CardDescription>Ranking, resolution rates, and SLA compliance by technician</CardDescription>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {/* Period selector */}
                  <div className="flex rounded border border-white/[0.07] overflow-hidden text-xs">
                    {[["this_week","Week"],["this_month","Month"],["this_quarter","Quarter"],["custom","Custom"]].map(([val, label]) => (
                      <button key={val} onClick={() => { setTechPeriod(val); }}
                        className={`px-2.5 py-1.5 transition-colors ${techPeriod === val ? "bg-bw-volt/15 text-bw-volt" : "text-bw-white/[0.45] hover:text-bw-white"}`}>
                        {label}
                      </button>
                    ))}
                  </div>
                  {techPeriod === "custom" && (
                    <>
                      <Input type="date" value={dateRange.start_date} onChange={e => setDateRange(p => ({ ...p, start_date: e.target.value }))} className="w-32 text-xs h-7" />
                      <span className="text-xs text-muted-foreground">to</span>
                      <Input type="date" value={dateRange.end_date} onChange={e => setDateRange(p => ({ ...p, end_date: e.target.value }))} className="w-32 text-xs h-7" />
                    </>
                  )}
                  <Button size="sm" variant="outline" onClick={() => fetchTechReport(techPeriod)} disabled={loading}>
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  </Button>
                  <Button size="sm" variant="outline" onClick={exportTechReportCsv} data-testid="tech-export-csv-btn">
                    <Download className="h-4 w-4 mr-1" /> CSV
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-bw-volt" />
                </div>
              ) : techReport ? (
                <div className="space-y-4">
                  {techReport.technicians?.length > 0 ? (
                    <>
                      <div className="border border-white/[0.07] rounded overflow-hidden">
                        <Table>
                          <TableHeader>
                            <TableRow className="bg-bw-panel border-b border-white/[0.07]">
                              <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono w-12">Rank</TableHead>
                              <TableHead className="text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Technician</TableHead>
                              <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Assigned</TableHead>
                              <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Resolved</TableHead>
                              <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Res. Rate</TableHead>
                              <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Avg Resp.</TableHead>
                              <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Avg Res.</TableHead>
                              <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">SLA %</TableHead>
                              <TableHead className="text-center text-bw-white/25 uppercase text-[10px] tracking-wide font-mono">Breaches</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {techReport.technicians.map((tech) => {
                              const rankStyle = tech.rank === 1
                                ? { background: "rgba(200,255,0,0.15)", color: "rgb(var(--bw-volt))", border: "1px solid rgba(200,255,0,0.30)" }
                                : tech.rank === 2
                                ? { background: "rgba(244,246,240,0.08)", color: "rgb(var(--bw-white))", border: "1px solid rgba(244,246,240,0.15)" }
                                : tech.rank === 3
                                ? { background: "rgba(255,140,0,0.10)", color: "rgb(var(--bw-orange))", border: "1px solid rgba(255,140,0,0.20)" }
                                : {};
                              const resRateColor = tech.resolution_rate_pct >= 80 ? "rgb(var(--bw-green))" : tech.resolution_rate_pct >= 60 ? "rgb(var(--bw-amber))" : "rgb(var(--bw-red))";
                              const slaColor = tech.sla_compliance_rate_pct >= 90 ? "rgb(var(--bw-green))" : tech.sla_compliance_rate_pct >= 70 ? "rgb(var(--bw-amber))" : "rgb(var(--bw-red))";
                              const breachTotal = tech.sla_breaches_response + tech.sla_breaches_resolution;
                              const breachColor = breachTotal === 0 ? "rgba(244,246,240,0.25)" : breachTotal <= 3 ? "rgb(var(--bw-amber))" : "rgb(var(--bw-red))";
                              const fmtTime = (mins) => !mins ? "N/A" : mins < 60 ? `${Math.round(mins)}m` : `${Math.round(mins/60)}h ${Math.round(mins%60)}m`;
                              return (
                                <TableRow
                                  key={tech.technician_id}
                                  className="border-b border-white/5 cursor-pointer hover:bg-bw-volt/[0.03]"
                                  onClick={() => setSelectedTech(selectedTech?.technician_id === tech.technician_id ? null : tech)}
                                  data-testid={`tech-row-${tech.rank}`}
                                >
                                  <TableCell>
                                    <span className="w-8 h-6 inline-flex items-center justify-center rounded text-xs font-mono font-bold" style={rankStyle}>#{tech.rank}</span>
                                  </TableCell>
                                  <TableCell>
                                    <div className="flex items-center gap-2">
                                      <div className="w-7 h-7 rounded-full bg-bw-volt/10 border border-bw-volt/20 flex items-center justify-center flex-shrink-0">
                                        <span className="text-[9px] font-bold text-bw-volt">{tech.avatar_initials}</span>
                                      </div>
                                      <span className="font-medium text-bw-white text-sm">{tech.technician_name}</span>
                                    </div>
                                  </TableCell>
                                  <TableCell className="text-center text-bw-white/[0.65] font-mono">{tech.total_tickets_assigned}</TableCell>
                                  <TableCell className="text-center text-bw-white/[0.65] font-mono">{tech.total_tickets_resolved}</TableCell>
                                  <TableCell className="text-center font-mono font-bold" style={{ color: resRateColor }}>{tech.resolution_rate_pct}%</TableCell>
                                  <TableCell className="text-center text-bw-white/[0.45] font-mono text-xs">{fmtTime(tech.avg_response_time_minutes)}</TableCell>
                                  <TableCell className="text-center text-bw-white/[0.45] font-mono text-xs">{fmtTime(tech.avg_resolution_time_minutes)}</TableCell>
                                  <TableCell className="text-center font-mono font-bold" style={{ color: slaColor }}>{tech.sla_compliance_rate_pct}%</TableCell>
                                  <TableCell className="text-center font-mono" style={{ color: breachColor }}>
                                    {breachTotal === 0 ? <span className="text-xs">None</span> : breachTotal}
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      </div>

                      {/* Drill-down panel */}
                      {selectedTech && (
                        <Card className="bg-bw-panel border border-bw-volt/15">
                          <CardHeader className="pb-3">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-full bg-bw-volt/[0.12] border border-bw-volt/25 flex items-center justify-center">
                                <span className="text-sm font-bold text-bw-volt">{selectedTech.avatar_initials}</span>
                              </div>
                              <div>
                                <CardTitle className="text-base text-bw-white">{selectedTech.technician_name}</CardTitle>
                                <CardDescription className="text-xs">Rank #{selectedTech.rank} · {techPeriod.replace("_"," ")}</CardDescription>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                              {[
                                { label: "Assigned", val: selectedTech.total_tickets_assigned, color: "rgb(var(--bw-white))" },
                                { label: "Resolved", val: selectedTech.total_tickets_resolved, color: "rgb(var(--bw-green))" },
                                { label: "Res. Rate", val: `${selectedTech.resolution_rate_pct}%`, color: selectedTech.resolution_rate_pct >= 80 ? "rgb(var(--bw-green))" : "rgb(var(--bw-amber))" },
                                { label: "SLA Compliance", val: `${selectedTech.sla_compliance_rate_pct}%`, color: selectedTech.sla_compliance_rate_pct >= 90 ? "rgb(var(--bw-green))" : selectedTech.sla_compliance_rate_pct >= 70 ? "rgb(var(--bw-amber))" : "rgb(var(--bw-red))" },
                                { label: "SLA Breaches (Resp)", val: selectedTech.sla_breaches_response, color: selectedTech.sla_breaches_response === 0 ? "rgba(244,246,240,0.25)" : "rgb(var(--bw-amber))" },
                                { label: "SLA Breaches (Res)", val: selectedTech.sla_breaches_resolution, color: selectedTech.sla_breaches_resolution === 0 ? "rgba(244,246,240,0.25)" : "rgb(var(--bw-red))" },
                                { label: "Avg Response", val: selectedTech.avg_response_time_minutes ? (selectedTech.avg_response_time_minutes < 60 ? `${Math.round(selectedTech.avg_response_time_minutes)}m` : `${Math.round(selectedTech.avg_response_time_minutes/60)}h`) : "N/A", color: "rgb(var(--bw-white))" },
                                { label: "Avg Resolution", val: selectedTech.avg_resolution_time_minutes ? (selectedTech.avg_resolution_time_minutes < 60 ? `${Math.round(selectedTech.avg_resolution_time_minutes)}m` : `${Math.round(selectedTech.avg_resolution_time_minutes/60)}h`) : "N/A", color: "rgb(var(--bw-white))" },
                              ].map(({ label, val, color }) => (
                                <div key={label} className="p-3 rounded bg-white/[0.03] border border-white/[0.06]">
                                  <p className="text-[10px] text-bw-white/35 uppercase tracking-wide mb-1">{label}</p>
                                  <p className="text-xl font-bold font-mono" style={{ color }}>{val}</p>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                      <Trophy className="h-10 w-10 mb-3 opacity-30" />
                      <p className="text-sm">No technician data for selected period</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <Trophy className="h-10 w-10 mb-3 opacity-30" />
                  <p className="text-sm">Click refresh to load technician performance data</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
