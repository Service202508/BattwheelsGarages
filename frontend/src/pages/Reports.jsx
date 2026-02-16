import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  TrendingUp, TrendingDown, IndianRupee, Users, FileText,
  Calendar, Download, RefreshCw, BarChart3, PieChart
} from "lucide-react";
import { API } from "@/App";

export default function Reports() {
  const [dashboard, setDashboard] = useState(null);
  const [profitLoss, setProfitLoss] = useState(null);
  const [receivables, setReceivables] = useState(null);
  const [payables, setPayables] = useState(null);
  const [gst, setGst] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");

  const [dateRange, setDateRange] = useState({
    start_date: new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => { fetchReports(); }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const [dashRes, plRes, recRes, payRes, gstRes] = await Promise.all([
        fetch(`${API}/zoho/reports/dashboard`, { headers }),
        fetch(`${API}/zoho/reports/profitandloss?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`, { headers }),
        fetch(`${API}/zoho/reports/receivables`, { headers }),
        fetch(`${API}/zoho/reports/payables`, { headers }),
        fetch(`${API}/zoho/reports/gst?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`, { headers })
      ]);

      const [dashData, plData, recData, payData, gstData] = await Promise.all([
        dashRes.json(), plRes.json(), recRes.json(), payRes.json(), gstRes.json()
      ]);

      setDashboard(dashData);
      setProfitLoss(plData);
      setReceivables(recData);
      setPayables(payData);
      setGst(gstData);
    } catch (error) {
      console.error("Failed to fetch reports:", error);
      toast.error("Error loading reports");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN')}`;

  return (
    <div className="space-y-6" data-testid="reports-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Financial Reports</h1>
          <p className="text-gray-500 text-sm mt-1">Business insights & analytics</p>
        </div>
        <div className="flex items-center gap-2">
          <Input 
            type="date" 
            value={dateRange.start_date} 
            onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
            className="w-36"
          />
          <span className="text-gray-500">to</span>
          <Input 
            type="date" 
            value={dateRange.end_date} 
            onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
            className="w-36"
          />
          <Button onClick={fetchReports} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="profitloss">Profit & Loss</TabsTrigger>
          <TabsTrigger value="receivables">Receivables</TabsTrigger>
          <TabsTrigger value="payables">Payables</TabsTrigger>
          <TabsTrigger value="gst">GST Summary</TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {loading ? <div className="text-center py-12">Loading...</div> : dashboard && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Total Revenue</p>
                        <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboard.financials?.total_revenue)}</p>
                      </div>
                      <IndianRupee className="h-8 w-8 text-green-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Receivables</p>
                        <p className="text-2xl font-bold text-orange-600">{formatCurrency(dashboard.financials?.receivables)}</p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-orange-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Payables</p>
                        <p className="text-2xl font-bold text-red-600">{formatCurrency(dashboard.financials?.outstanding_payables)}</p>
                      </div>
                      <TrendingDown className="h-8 w-8 text-red-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Expenses</p>
                        <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboard.financials?.total_expenses)}</p>
                      </div>
                      <BarChart3 className="h-8 w-8 text-gray-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Pipeline Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Sales Pipeline</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Estimates</span>
                      <div className="text-right">
                        <span className="font-semibold">{dashboard.sales_pipeline?.estimates?.total}</span>
                        <span className="text-xs text-gray-500 ml-2">({dashboard.sales_pipeline?.estimates?.open} open)</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Sales Orders</span>
                      <div className="text-right">
                        <span className="font-semibold">{dashboard.sales_pipeline?.salesorders?.total}</span>
                        <span className="text-xs text-gray-500 ml-2">({dashboard.sales_pipeline?.salesorders?.open} open)</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Invoices</span>
                      <div className="text-right">
                        <span className="font-semibold">{dashboard.sales_pipeline?.invoices?.total}</span>
                        <span className="text-xs text-orange-600 ml-2">({dashboard.sales_pipeline?.invoices?.unpaid} unpaid)</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Purchase Pipeline</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Purchase Orders</span>
                      <div className="text-right">
                        <span className="font-semibold">{dashboard.purchase_pipeline?.purchaseorders?.total}</span>
                        <span className="text-xs text-gray-500 ml-2">({dashboard.purchase_pipeline?.purchaseorders?.open} open)</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Bills</span>
                      <div className="text-right">
                        <span className="font-semibold">{dashboard.purchase_pipeline?.bills?.total}</span>
                        <span className="text-xs text-red-600 ml-2">({dashboard.purchase_pipeline?.bills?.unpaid} unpaid)</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Master Data */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Master Data</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-3xl font-bold text-gray-900">{dashboard.master_data?.customers}</p>
                      <p className="text-sm text-gray-500">Customers</p>
                    </div>
                    <div>
                      <p className="text-3xl font-bold text-gray-900">{dashboard.master_data?.vendors}</p>
                      <p className="text-sm text-gray-500">Vendors</p>
                    </div>
                    <div>
                      <p className="text-3xl font-bold text-gray-900">{dashboard.master_data?.items}</p>
                      <p className="text-sm text-gray-500">Items</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Profit & Loss Tab */}
        <TabsContent value="profitloss" className="space-y-6">
          {loading ? <div className="text-center py-12">Loading...</div> : profitLoss && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Profit & Loss Statement</CardTitle>
                  <p className="text-sm text-gray-500">{profitLoss.period?.start_date} to {profitLoss.period?.end_date}</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Income */}
                  <div className="border-b pb-4">
                    <h3 className="font-semibold text-green-700 mb-3">Income</h3>
                    <div className="flex justify-between">
                      <span>Operating Income</span>
                      <span className="font-medium">{formatCurrency(profitLoss.income?.operating_income)}</span>
                    </div>
                  </div>

                  {/* COGS */}
                  <div className="border-b pb-4">
                    <h3 className="font-semibold text-red-700 mb-3">Cost of Goods Sold</h3>
                    <div className="flex justify-between">
                      <span>Total COGS</span>
                      <span className="font-medium">{formatCurrency(profitLoss.cost_of_goods_sold?.total)}</span>
                    </div>
                  </div>

                  {/* Gross Profit */}
                  <div className="border-b pb-4 bg-gray-50 p-3 rounded-lg">
                    <div className="flex justify-between">
                      <span className="font-semibold">Gross Profit</span>
                      <span className={`font-bold text-lg ${profitLoss.gross_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(profitLoss.gross_profit)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Margin: {profitLoss.margins?.gross_margin_percent}%</p>
                  </div>

                  {/* Operating Expenses */}
                  <div className="border-b pb-4">
                    <h3 className="font-semibold text-orange-700 mb-3">Operating Expenses</h3>
                    {profitLoss.operating_expenses?.by_category && Object.entries(profitLoss.operating_expenses.by_category).map(([cat, amt]) => (
                      <div key={cat} className="flex justify-between text-sm py-1">
                        <span className="text-gray-600">{cat}</span>
                        <span>{formatCurrency(amt)}</span>
                      </div>
                    ))}
                    <div className="flex justify-between font-medium mt-2 pt-2 border-t">
                      <span>Total Expenses</span>
                      <span>{formatCurrency(profitLoss.operating_expenses?.total)}</span>
                    </div>
                  </div>

                  {/* Net Profit */}
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-lg">Net Profit</span>
                      <span className={`font-bold text-2xl ${profitLoss.net_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(profitLoss.net_profit)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">Net Margin: {profitLoss.margins?.net_margin_percent}%</p>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Receivables Tab */}
        <TabsContent value="receivables" className="space-y-6">
          {loading ? <div className="text-center py-12">Loading...</div> : receivables && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Receivables Aging</CardTitle>
                  <p className="text-sm text-gray-500">Total Outstanding: {formatCurrency(receivables.total_receivables)}</p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-5 gap-4 mb-6">
                    {Object.entries(receivables.aging_summary || {}).map(([period, data]) => (
                      <div key={period} className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">{period.replace('_', ' ').replace('days', ' days')}</p>
                        <p className="text-lg font-bold">{formatCurrency(data.amount)}</p>
                        <p className="text-xs text-gray-400">{data.count} invoices</p>
                      </div>
                    ))}
                  </div>
                  
                  {receivables.customer_breakdown && Object.keys(receivables.customer_breakdown).length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-3">By Customer</h4>
                      <div className="space-y-2">
                        {Object.entries(receivables.customer_breakdown).slice(0, 10).map(([customer, data]) => (
                          <div key={customer} className="flex justify-between items-center py-2 border-b">
                            <span className="text-gray-700">{customer}</span>
                            <span className="font-medium">{formatCurrency(data.total)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Payables Tab */}
        <TabsContent value="payables" className="space-y-6">
          {loading ? <div className="text-center py-12">Loading...</div> : payables && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Payables Aging</CardTitle>
                  <p className="text-sm text-gray-500">Total Outstanding: {formatCurrency(payables.total_payables)}</p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-5 gap-4 mb-6">
                    {Object.entries(payables.aging_summary || {}).map(([period, data]) => (
                      <div key={period} className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">{period.replace('_', ' ').replace('days', ' days')}</p>
                        <p className="text-lg font-bold">{formatCurrency(data.amount)}</p>
                        <p className="text-xs text-gray-400">{data.count} bills</p>
                      </div>
                    ))}
                  </div>
                  
                  {payables.vendor_breakdown && Object.keys(payables.vendor_breakdown).length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-3">By Vendor</h4>
                      <div className="space-y-2">
                        {Object.entries(payables.vendor_breakdown).slice(0, 10).map(([vendor, data]) => (
                          <div key={vendor} className="flex justify-between items-center py-2 border-b">
                            <span className="text-gray-700">{vendor}</span>
                            <span className="font-medium">{formatCurrency(data.total)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* GST Tab */}
        <TabsContent value="gst" className="space-y-6">
          {loading ? <div className="text-center py-12">Loading...</div> : gst && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">GSTR-1 (Outward)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(gst.gstr1_outward_supplies?.total_gst)}</p>
                    <p className="text-sm text-gray-500">{gst.gstr1_outward_supplies?.invoice_count} invoices</p>
                    <p className="text-sm text-gray-500">Taxable: {formatCurrency(gst.gstr1_outward_supplies?.taxable_value)}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">GSTR-2 (Inward)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-bold text-blue-600">{formatCurrency(gst.gstr2_inward_supplies?.total_gst)}</p>
                    <p className="text-sm text-gray-500">{gst.gstr2_inward_supplies?.bill_count} bills</p>
                    <p className="text-sm text-gray-500">Taxable: {formatCurrency(gst.gstr2_inward_supplies?.taxable_value)}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">GSTR-3B (Net)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className={`text-2xl font-bold ${gst.gstr3b_summary?.net_gst_payable >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(Math.abs(gst.gstr3b_summary?.net_gst_payable))}
                    </p>
                    <p className="text-sm text-gray-500">
                      {gst.gstr3b_summary?.net_gst_payable >= 0 ? 'GST Payable' : 'GST Refund'}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>GST Summary</CardTitle>
                  <p className="text-sm text-gray-500">{gst.period?.start_date} to {gst.period?.end_date}</p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between py-2 border-b">
                      <span>Output GST (Sales)</span>
                      <span className="font-medium text-green-600">+ {formatCurrency(gst.gstr3b_summary?.output_gst)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span>Input GST Credit (Purchases)</span>
                      <span className="font-medium text-blue-600">- {formatCurrency(gst.gstr3b_summary?.input_gst_credit)}</span>
                    </div>
                    <div className="flex justify-between py-3 bg-gray-50 px-3 rounded-lg">
                      <span className="font-semibold">Net GST Payable</span>
                      <span className={`font-bold text-lg ${gst.gstr3b_summary?.net_gst_payable >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {formatCurrency(gst.gstr3b_summary?.net_gst_payable)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
