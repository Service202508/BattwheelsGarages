import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  BarChart3, PieChart, TrendingUp, TrendingDown, DollarSign, Users, 
  Receipt, AlertTriangle, Calendar, RefreshCw, ArrowUpRight, ArrowDownRight,
  Wallet, Target, Clock, CheckCircle
} from "lucide-react";
import { GradientStatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";

// Simple chart components using CSS
const BarChartSimple = ({ data, labels, colors, height = 200, horizontal = false }) => {
  const maxVal = Math.max(...data.map(d => typeof d === 'object' ? d.value : d), 1);
  const values = data.map(d => typeof d === 'object' ? d.value : d);
  
  if (horizontal) {
    return (
      <div className="space-y-2">
        {labels.map((label, idx) => (
          <div key={idx} className="flex items-center gap-3">
            <span className="text-xs w-24 truncate text-bw-white/35">{label}</span>
            <div className="flex-1 bg-white/5 rounded-full h-6 overflow-hidden">
              <div 
                className="h-full rounded-full flex items-center justify-end pr-2"
                style={{ 
                  width: `${(values[idx] / maxVal) * 100}%`, 
                  backgroundColor: colors?.[idx] || '#3B82F6',
                  minWidth: values[idx] > 0 ? '40px' : '0'
                }}
              >
                <span className="text-xs font-medium text-white">₹{(values[idx]/1000).toFixed(0)}K</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  return (
    <div className="flex items-end justify-around gap-2" style={{ height }}>
      {labels.map((label, idx) => (
        <div key={idx} className="flex flex-col items-center flex-1">
          <div 
            className="w-full rounded-t transition-all duration-300 hover:opacity-80"
            style={{ 
              height: `${(values[idx] / maxVal) * (height - 30)}px`,
              backgroundColor: colors?.[idx] || '#3B82F6',
              minHeight: values[idx] > 0 ? '4px' : '0'
            }}
          />
          <span className="text-xs mt-2 text-bw-white/[0.45] truncate w-full text-center">{label}</span>
        </div>
      ))}
    </div>
  );
};

const DonutChart = ({ data, labels, colors, size = 180 }) => {
  const total = data.reduce((a, b) => a + b, 0);
  let cumulative = 0;
  
  const segments = data.map((value, idx) => {
    const start = (cumulative / total) * 100;
    cumulative += value;
    const end = (cumulative / total) * 100;
    return { value, start, end, color: colors[idx], label: labels[idx] };
  });
  
  // Create conic gradient
  const gradient = segments.map(s => `${s.color} ${s.start}% ${s.end}%`).join(', ');
  
  return (
    <div className="flex items-center gap-6">
      <div 
        className="rounded-full flex items-center justify-center"
        style={{ 
          width: size, 
          height: size, 
          background: `conic-gradient(${gradient})`,
          position: 'relative'
        }}
      >
        <div className="absolute bg-bw-panel rounded-full flex items-center justify-center" style={{ width: size * 0.6, height: size * 0.6 }}>
          <span className="text-lg font-bold">{data.reduce((a,b) => a+b, 0)}</span>
        </div>
      </div>
      <div className="space-y-2">
        {labels.map((label, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors[idx] }} />
            <span className="text-sm">{label}: {data[idx]}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const LineChart = ({ data, labels, height = 150, color = "#3B82F6" }) => {
  const maxVal = Math.max(...data, 1);
  const minVal = Math.min(...data, 0);
  const range = maxVal - minVal || 1;
  
  const points = data.map((val, idx) => {
    const x = (idx / (data.length - 1)) * 100;
    const y = 100 - ((val - minVal) / range) * 100;
    return `${x},${y}`;
  }).join(' ');
  
  return (
    <div style={{ height }}>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
        <defs>
          <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,100 ${points} 100,100`} fill="url(#lineGradient)" />
        <polyline points={points} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
        {data.map((val, idx) => {
          const x = (idx / (data.length - 1)) * 100;
          const y = 100 - ((val - minVal) / range) * 100;
          return <circle key={idx} cx={x} cy={y} r="1.5" fill={color} />;
        })}
      </svg>
      <div className="flex justify-between mt-2">
        {labels.map((label, idx) => (
          <span key={idx} className="text-xs text-bw-white/[0.45]">{label}</span>
        ))}
      </div>
    </div>
  );
};

const FunnelChart = ({ data }) => {
  const maxCount = Math.max(...data.map(d => d.count), 1);
  
  return (
    <div className="space-y-2">
      {data.map((item, idx) => (
        <div key={idx} className="flex items-center gap-3">
          <span className="text-sm w-20 text-bw-white/35">{item.stage}</span>
          <div className="flex-1 relative">
            <div 
              className="h-10 rounded flex items-center justify-between px-3"
              style={{ 
                width: `${(item.count / maxCount) * 100}%`,
                backgroundColor: item.color,
                minWidth: '80px'
              }}
            >
              <span className="text-sm font-medium text-white">{item.count}</span>
              <span className="text-xs text-white/80">₹{(item.value/1000).toFixed(0)}K</span>
            </div>
            {item.conversion && (
              <span className="absolute right-0 top-1/2 -translate-y-1/2 text-xs text-bw-white/[0.45] ml-2">
                {item.conversion}%
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default function ReportsAdvanced() {
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  
  // Report data
  const [dashboardSummary, setDashboardSummary] = useState(null);
  const [monthlyRevenue, setMonthlyRevenue] = useState(null);
  const [quarterlyRevenue, setQuarterlyRevenue] = useState(null);
  const [agingData, setAgingData] = useState(null);
  const [topCustomers, setTopCustomers] = useState(null);
  const [topOutstanding, setTopOutstanding] = useState(null);
  const [salesFunnel, setSalesFunnel] = useState(null);
  const [statusDistribution, setStatusDistribution] = useState(null);
  const [paymentTrend, setPaymentTrend] = useState(null);
  const [paymentModes, setPaymentModes] = useState(null);
  const [customerAcquisition, setCustomerAcquisition] = useState(null);

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchAllReports();
  }, []);

  const fetchAllReports = async () => {
    setLoading(true);
    await Promise.all([
      fetchDashboardSummary(),
      fetchMonthlyRevenue(),
      fetchAgingData(),
      fetchTopCustomers(),
      fetchSalesFunnel(),
      fetchStatusDistribution(),
      fetchPaymentTrend(),
      fetchPaymentModes()
    ]);
    setLoading(false);
  };

  const fetchDashboardSummary = async () => {
    try {
      const res = await fetch(`${API}/reports-advanced/dashboard-summary`, { headers });
      if (res.ok) {
        const data = await res.json();
        setDashboardSummary(data.summary);
      }
    } catch (e) { console.error(e); }
  };

  const fetchMonthlyRevenue = async () => {
    try {
      const res = await fetch(`${API}/reports-advanced/revenue/monthly?months=6`, { headers });
      if (res.ok) {
        const data = await res.json();
        setMonthlyRevenue(data);
      }
    } catch (e) { console.error(e); }
  };

  const fetchAgingData = async () => {
    try {
      const res = await fetch(`${API}/reports-advanced/receivables/aging`, { headers });
      if (res.ok) {
        const data = await res.json();
        setAgingData(data);
      }
    } catch (e) { console.error(e); }
  };

  const fetchTopCustomers = async () => {
    try {
      const [revenue, outstanding] = await Promise.all([
        fetch(`${API}/reports-advanced/customers/top-revenue?limit=5`, { headers }),
        fetch(`${API}/reports-advanced/customers/top-outstanding?limit=5`, { headers })
      ]);
      if (revenue.ok) setTopCustomers((await revenue.json()).data);
      if (outstanding.ok) setTopOutstanding((await outstanding.json()).data);
    } catch (e) { console.error(e); }
  };

  const fetchSalesFunnel = async () => {
    try {
      const res = await fetch(`${API}/reports-advanced/sales/funnel`, { headers });
      if (res.ok) {
        const data = await res.json();
        setSalesFunnel(data);
      }
    } catch (e) { console.error(e); }
  };

  const fetchStatusDistribution = async () => {
    try {
      const res = await fetch(`${API}/reports-advanced/invoices/status-distribution`, { headers });
      if (res.ok) {
        const data = await res.json();
        setStatusDistribution(data);
      }
    } catch (e) { console.error(e); }
  };

  const fetchPaymentTrend = async () => {
    try {
      const res = await fetch(`${API}/reports-advanced/payments/trend?months=6`, { headers });
      if (res.ok) {
        const data = await res.json();
        setPaymentTrend(data);
      }
    } catch (e) { console.error(e); }
  };

  const fetchPaymentModes = async () => {
    try {
      const res = await fetch(`${API}/reports-advanced/payments/by-mode`, { headers });
      if (res.ok) {
        const data = await res.json();
        setPaymentModes(data);
      }
    } catch (e) { console.error(e); }
  };

  const formatCurrency = (amount) => `₹${(amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 0 })}`;
  const formatCurrencyK = (amount) => `₹${((amount || 0)/1000).toFixed(1)}K`;

  return (
    <div className="space-y-6" data-testid="reports-advanced-page">
      {/* Header */}
      <PageHeader
        title="Analytics & Reports"
        description="Visual insights into your business performance"
        icon={BarChart3}
        actions={
          <Button onClick={fetchAllReports} variant="outline" className="gap-2" disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
        }
      />

      {/* KPI Cards */}
      {dashboardSummary && (
        <StatCardGrid columns={4}>
          <GradientStatCard
            title="This Month Revenue"
            value={formatCurrencyCompact(dashboardSummary.this_month?.revenue)}
            subtitle={`${dashboardSummary.this_month?.invoices} invoices`}
            icon={TrendingUp}
            gradient="from-blue-500 to-blue-600"
          />
          <GradientStatCard
            title="Year to Date"
            value={formatCurrencyCompact(dashboardSummary.year_to_date?.revenue)}
            icon={DollarSign}
            gradient="from-green-500 to-green-600"
          />
          <GradientStatCard
            title="Total Outstanding"
            value={formatCurrencyCompact(dashboardSummary.receivables?.total_outstanding)}
            icon={Wallet}
            gradient="from-orange-500 to-orange-600"
          />
          <GradientStatCard
            title="Overdue Amount"
            value={formatCurrencyCompact(dashboardSummary.receivables?.overdue_amount)}
            subtitle={`${dashboardSummary.receivables?.overdue_count} invoices`}
            icon={AlertTriangle}
            gradient={dashboardSummary.receivables?.overdue_count > 0 ? "from-red-500 to-red-600" : "from-gray-500 to-gray-600"}
          />
        </StatCardGrid>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
          <TabsTrigger value="receivables">Receivables</TabsTrigger>
          <TabsTrigger value="customers">Customers</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Monthly Revenue Chart */}
            {monthlyRevenue && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-blue-500" /> Monthly Revenue
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <BarChartSimple 
                    data={monthlyRevenue.datasets?.[0]?.data || []}
                    labels={monthlyRevenue.labels || []}
                    colors={monthlyRevenue.datasets?.map(d => d.color) || ['#3B82F6']}
                    height={180}
                  />
                  <div className="flex gap-4 mt-4 justify-center">
                    {monthlyRevenue.datasets?.map((ds, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded" style={{ backgroundColor: ds.color }} />
                        <span className="text-sm text-bw-white/35">{ds.label}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Invoice Status Distribution */}
            {statusDistribution && statusDistribution.data?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <PieChart className="h-5 w-5 text-purple-500" /> Invoice Status
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <DonutChart 
                    data={statusDistribution.values || []}
                    labels={statusDistribution.labels || []}
                    colors={statusDistribution.colors || ['#3B82F6']}
                    size={160}
                  />
                </CardContent>
              </Card>
            )}

            {/* Sales Funnel */}
            {salesFunnel && salesFunnel.data?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Target className="h-5 w-5 text-green-500" /> Sales Funnel
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FunnelChart data={salesFunnel.data || []} />
                </CardContent>
              </Card>
            )}

            {/* Payment Trend */}
            {paymentTrend && paymentTrend.values?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-teal-500" /> Payment Collections
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <LineChart 
                    data={paymentTrend.values || []}
                    labels={paymentTrend.labels || []}
                    height={150}
                    color="#14B8A6"
                  />
                  <p className="text-center mt-4 text-sm text-bw-white/[0.45]">
                    Total Collected: <span className="font-bold text-green-600">{formatCurrency(paymentTrend.total_collected)}</span>
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Revenue Tab */}
        <TabsContent value="revenue" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {monthlyRevenue && (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-lg">Revenue Trend (Last 6 Months)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-6 gap-4">
                    {monthlyRevenue.data?.map((item, idx) => (
                      <div key={idx} className="bg-bw-panel p-4 rounded-lg text-center">
                        <p className="text-xs text-bw-white/[0.45]">{item.month_name}</p>
                        <p className="text-lg font-bold text-bw-blue mt-1">{formatCurrencyK(item.invoiced)}</p>
                        <p className="text-xs text-green-600">{formatCurrencyK(item.collected)} collected</p>
                        <p className="text-xs text-bw-white/[0.45] mt-1">{item.invoice_count} invoices</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {paymentModes && paymentModes.data?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <PieChart className="h-5 w-5" /> Payment Methods
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <DonutChart 
                    data={paymentModes.values || []}
                    labels={paymentModes.labels || []}
                    colors={paymentModes.colors || ['#3B82F6']}
                    size={150}
                  />
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Receivables Tab */}
        <TabsContent value="receivables" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Aging Chart */}
            {agingData && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Clock className="h-5 w-5 text-orange-500" /> Receivables Aging
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {agingData.data?.map((bucket, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <span className="text-sm w-20 text-bw-white/35">{bucket.label}</span>
                        <div className="flex-1 bg-white/5 rounded-full h-8 overflow-hidden">
                          <div 
                            className="h-full rounded-full flex items-center justify-end pr-3"
                            style={{ 
                              width: `${(bucket.amount / (agingData.total_outstanding || 1)) * 100}%`,
                              backgroundColor: bucket.color,
                              minWidth: bucket.amount > 0 ? '60px' : '0'
                            }}
                          >
                            <span className="text-xs font-medium text-white">{formatCurrency(bucket.amount)}</span>
                          </div>
                        </div>
                        <span className="text-xs text-bw-white/[0.45] w-8">{bucket.count}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t text-center">
                    <p className="text-sm text-bw-white/[0.45]">Total Outstanding</p>
                    <p className="text-2xl font-bold text-bw-orange">{formatCurrency(agingData.total_outstanding)}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Top Outstanding Customers */}
            {topOutstanding && topOutstanding.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-500" /> Top Outstanding
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <BarChartSimple 
                    data={topOutstanding.map(c => c.outstanding)}
                    labels={topOutstanding.map(c => c.name)}
                    colors={topOutstanding.map(() => '#EF4444')}
                    horizontal={true}
                  />
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Customers Tab */}
        <TabsContent value="customers" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Top Revenue Customers */}
            {topCustomers && topCustomers.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-500" /> Top Customers by Revenue
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <BarChartSimple 
                    data={topCustomers.map(c => c.revenue)}
                    labels={topCustomers.map(c => c.name)}
                    colors={topCustomers.map(() => '#3B82F6')}
                    horizontal={true}
                  />
                </CardContent>
              </Card>
            )}

            {/* Customer Summary */}
            {dashboardSummary && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Users className="h-5 w-5 text-green-500" /> Customer Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg text-center">
                      <p className="text-3xl font-bold text-bw-blue">{dashboardSummary.customers?.active || 0}</p>
                      <p className="text-sm text-bw-white/35">Active Customers</p>
                    </div>
                    <div className="bg-bw-amber/[0.08] p-4 rounded-lg text-center">
                      <p className="text-3xl font-bold text-bw-amber">{dashboardSummary.pipeline?.pending_estimates || 0}</p>
                      <p className="text-sm text-bw-white/35">Pending Estimates</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
