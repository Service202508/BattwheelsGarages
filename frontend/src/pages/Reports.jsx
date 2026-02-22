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
  Loader2, ArrowUp, ArrowDown
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
              <span className="text-sm text-gray-500">From</span>
              <Input 
                type="date" 
                value={dateRange.start_date} 
                onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
                className="w-40"
                data-testid="start-date-input"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">To</span>
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
            <span className="text-sm text-gray-500">As of</span>
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
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Financial Reports</h1>
          <p className="text-gray-500 text-sm mt-1">Comprehensive business analytics & exports</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5 h-auto">
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
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : profitLoss && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="bg-[rgba(34,197,94,0.08)] border-green-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-green-700 font-medium">Total Income</p>
                        <p className="text-xl font-bold text-green-800">{formatCurrency(profitLoss.total_income)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-[rgba(255,140,0,0.08)] border-orange-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-[#FF8C00] font-medium">Cost of Goods</p>
                        <p className="text-xl font-bold text-orange-800">{formatCurrency(profitLoss.total_cogs)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-blue-50 border-blue-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-[#3B9EFF] font-medium">Gross Profit</p>
                        <p className="text-xl font-bold text-blue-800">{formatCurrency(profitLoss.gross_profit)}</p>
                      </CardContent>
                    </Card>
                    <Card className={`${profitLoss.net_profit >= 0 ? 'bg-[rgba(200,255,0,0.08)] border-emerald-200' : 'bg-[rgba(255,59,47,0.08)] border-red-200'}`}>
                      <CardContent className="p-4">
                        <p className={`text-xs font-medium ${profitLoss.net_profit >= 0 ? 'text-[#C8FF00] text-700' : 'text-red-700'}`}>Net Profit</p>
                        <p className={`text-xl font-bold ${profitLoss.net_profit >= 0 ? 'text-[#C8FF00] text-800' : 'text-red-800'}`}>
                          {formatCurrency(profitLoss.net_profit)}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Detailed Breakdown */}
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead className="font-semibold">Account</TableHead>
                        <TableHead className="text-right font-semibold">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow className="bg-[rgba(34,197,94,0.08)]/50">
                        <TableCell className="font-semibold text-green-800">INCOME</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="pl-8">Operating Income (Sales)</TableCell>
                        <TableCell className="text-right">{formatCurrency(profitLoss.total_income)}</TableCell>
                      </TableRow>
                      <TableRow className="bg-gray-50">
                        <TableCell className="font-semibold">Total Income</TableCell>
                        <TableCell className="text-right font-semibold">{formatCurrency(profitLoss.total_income)}</TableCell>
                      </TableRow>
                      
                      <TableRow className="bg-[rgba(255,140,0,0.08)]/50">
                        <TableCell className="font-semibold text-orange-800">COST OF GOODS SOLD</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="pl-8">Direct Costs (Purchases/Bills)</TableCell>
                        <TableCell className="text-right">{formatCurrency(profitLoss.total_cogs)}</TableCell>
                      </TableRow>
                      <TableRow className="bg-blue-50">
                        <TableCell className="font-semibold text-blue-800">Gross Profit</TableCell>
                        <TableCell className="text-right font-semibold text-blue-800">{formatCurrency(profitLoss.gross_profit)}</TableCell>
                      </TableRow>
                      
                      <TableRow className="bg-[rgba(255,59,47,0.08)]/50">
                        <TableCell className="font-semibold text-red-800">OPERATING EXPENSES</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      {profitLoss.expenses_breakdown && Object.entries(profitLoss.expenses_breakdown).map(([cat, amt]) => (
                        <TableRow key={cat}>
                          <TableCell className="pl-8">{cat}</TableCell>
                          <TableCell className="text-right">{formatCurrency(amt)}</TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-gray-50">
                        <TableCell className="font-semibold">Total Expenses</TableCell>
                        <TableCell className="text-right font-semibold">{formatCurrency(profitLoss.total_expenses)}</TableCell>
                      </TableRow>
                      
                      <TableRow className="bg-[#22EDA9]/20">
                        <TableCell className="font-bold text-lg">NET PROFIT</TableCell>
                        <TableCell className={`text-right font-bold text-lg ${profitLoss.net_profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                          {formatCurrency(profitLoss.net_profit)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  {/* Margins */}
                  <div className="flex gap-4 text-sm text-gray-600">
                    <span>Gross Margin: <strong>{profitLoss.margins?.gross_margin_percent || 0}%</strong></span>
                    <span>Net Margin: <strong>{profitLoss.margins?.net_margin_percent || 0}%</strong></span>
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
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : balanceSheet && (
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Assets */}
                  <Card className="border-green-200">
                    <CardHeader className="bg-[rgba(34,197,94,0.08)] py-3">
                      <CardTitle className="text-lg text-green-800">Assets</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Accounts Receivable</span>
                        <span className="font-medium">{formatCurrency(balanceSheet.assets?.accounts_receivable)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Bank Balance</span>
                        <span className="font-medium">{formatCurrency(balanceSheet.assets?.bank_balance)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Inventory Value</span>
                        <span className="font-medium">{formatCurrency(balanceSheet.assets?.inventory_value)}</span>
                      </div>
                      <div className="flex justify-between pt-3 border-t border-green-200">
                        <span className="font-semibold text-green-800">Total Assets</span>
                        <span className="font-bold text-green-800">{formatCurrency(balanceSheet.assets?.total)}</span>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Liabilities & Equity */}
                  <div className="space-y-4">
                    <Card className="border-red-200">
                      <CardHeader className="bg-[rgba(255,59,47,0.08)] py-3">
                        <CardTitle className="text-lg text-red-800">Liabilities</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Accounts Payable</span>
                          <span className="font-medium">{formatCurrency(balanceSheet.liabilities?.accounts_payable)}</span>
                        </div>
                        <div className="flex justify-between pt-3 border-t border-red-200">
                          <span className="font-semibold text-red-800">Total Liabilities</span>
                          <span className="font-bold text-red-800">{formatCurrency(balanceSheet.liabilities?.total)}</span>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border-blue-200">
                      <CardHeader className="bg-blue-50 py-3">
                        <CardTitle className="text-lg text-blue-800">Equity</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Retained Earnings</span>
                          <span className="font-medium">{formatCurrency(balanceSheet.equity?.retained_earnings)}</span>
                        </div>
                        <div className="flex justify-between pt-3 border-t border-blue-200">
                          <span className="font-semibold text-blue-800">Total Equity</span>
                          <span className="font-bold text-blue-800">{formatCurrency(balanceSheet.equity?.total)}</span>
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
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : arAging && (
                <div className="space-y-6">
                  {/* Aging Buckets */}
                  <div className="grid grid-cols-5 gap-3">
                    <Card className="border-l-4 border-l-green-500">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">Current</p>
                        <p className="text-lg font-bold text-green-700">{formatCurrency(arAging.aging_data?.current)}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-yellow-400">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">1-30 Days</p>
                        <p className="text-lg font-bold text-[#EAB308]">{formatCurrency(arAging.aging_data?.["1_30"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-orange-400">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">31-60 Days</p>
                        <p className="text-lg font-bold text-[#FF8C00]">{formatCurrency(arAging.aging_data?.["31_60"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-orange-600">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">61-90 Days</p>
                        <p className="text-lg font-bold text-orange-800">{formatCurrency(arAging.aging_data?.["61_90"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-red-500">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">90+ Days</p>
                        <p className="text-lg font-bold text-red-700">{formatCurrency(arAging.aging_data?.over_90)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Total */}
                  <div className="bg-[#22EDA9]/10 p-4 rounded-lg flex justify-between items-center">
                    <span className="font-semibold text-gray-700">Total Accounts Receivable</span>
                    <span className="text-2xl font-bold text-[#F4F6F0]">{formatCurrency(arAging.total_ar)}</span>
                  </div>

                  {/* Invoice Details Table */}
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-gray-50">
                          <TableHead>Invoice #</TableHead>
                          <TableHead>Customer</TableHead>
                          <TableHead>Due Date</TableHead>
                          <TableHead className="text-center">Days Overdue</TableHead>
                          <TableHead className="text-right">Balance</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {arAging.invoices?.slice(0, 20).map((inv, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{inv.invoice_number}</TableCell>
                            <TableCell>{inv.customer_name}</TableCell>
                            <TableCell>{inv.due_date}</TableCell>
                            <TableCell className="text-center">
                              <Badge variant={
                                inv.days_overdue <= 0 ? "success" :
                                inv.days_overdue <= 30 ? "warning" :
                                "destructive"
                              }>
                                {inv.days_overdue} days
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(inv.balance)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    {arAging.invoices?.length > 20 && (
                      <div className="p-3 bg-gray-50 text-center text-sm text-gray-500">
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
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : apAging && (
                <div className="space-y-6">
                  {/* Aging Buckets */}
                  <div className="grid grid-cols-5 gap-3">
                    <Card className="border-l-4 border-l-green-500">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">Current</p>
                        <p className="text-lg font-bold text-green-700">{formatCurrency(apAging.aging_data?.current)}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-yellow-400">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">1-30 Days</p>
                        <p className="text-lg font-bold text-[#EAB308]">{formatCurrency(apAging.aging_data?.["1_30"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-orange-400">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">31-60 Days</p>
                        <p className="text-lg font-bold text-[#FF8C00]">{formatCurrency(apAging.aging_data?.["31_60"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-orange-600">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">61-90 Days</p>
                        <p className="text-lg font-bold text-orange-800">{formatCurrency(apAging.aging_data?.["61_90"])}</p>
                      </CardContent>
                    </Card>
                    <Card className="border-l-4 border-l-red-500">
                      <CardContent className="p-3 text-center">
                        <p className="text-xs text-gray-500">90+ Days</p>
                        <p className="text-lg font-bold text-red-700">{formatCurrency(apAging.aging_data?.over_90)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Total */}
                  <div className="bg-[rgba(255,59,47,0.08)] p-4 rounded-lg flex justify-between items-center">
                    <span className="font-semibold text-gray-700">Total Accounts Payable</span>
                    <span className="text-2xl font-bold text-red-700">{formatCurrency(apAging.total_ap)}</span>
                  </div>

                  {/* Bill Details Table */}
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-gray-50">
                          <TableHead>Bill #</TableHead>
                          <TableHead>Vendor</TableHead>
                          <TableHead>Due Date</TableHead>
                          <TableHead className="text-center">Days Overdue</TableHead>
                          <TableHead className="text-right">Balance</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {apAging.bills?.slice(0, 20).map((bill, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{bill.bill_number}</TableCell>
                            <TableCell>{bill.vendor_name}</TableCell>
                            <TableCell>{bill.due_date}</TableCell>
                            <TableCell className="text-center">
                              <Badge variant={
                                bill.days_overdue <= 0 ? "success" :
                                bill.days_overdue <= 30 ? "warning" :
                                "destructive"
                              }>
                                {bill.days_overdue} days
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(bill.balance)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    {apAging.bills?.length > 20 && (
                      <div className="p-3 bg-gray-50 text-center text-sm text-gray-500">
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
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : salesByCustomer && (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="grid grid-cols-2 gap-4">
                    <Card className="bg-blue-50 border-blue-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-[#3B9EFF] font-medium">Total Invoices</p>
                        <p className="text-2xl font-bold text-blue-800">{salesByCustomer.total_invoices || 0}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-[rgba(34,197,94,0.08)] border-green-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-green-700 font-medium">Total Sales</p>
                        <p className="text-2xl font-bold text-green-800">{formatCurrency(salesByCustomer.total_sales)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Customer Table */}
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-gray-50">
                          <TableHead className="w-12">#</TableHead>
                          <TableHead>Customer Name</TableHead>
                          <TableHead className="text-center">Invoices</TableHead>
                          <TableHead className="text-right">Total Sales</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {salesByCustomer.sales_data?.map((item, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="text-gray-500">{idx + 1}</TableCell>
                            <TableCell className="font-medium">{item.customer_name}</TableCell>
                            <TableCell className="text-center">{item.invoice_count}</TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(item.total_sales)}</TableCell>
                          </TableRow>
                        ))}
                        <TableRow className="bg-[#22EDA9]/20 font-bold">
                          <TableCell></TableCell>
                          <TableCell>TOTAL</TableCell>
                          <TableCell className="text-center">{salesByCustomer.total_invoices}</TableCell>
                          <TableCell className="text-right">{formatCurrency(salesByCustomer.total_sales)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
