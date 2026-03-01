import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Calculator, TrendingUp, TrendingDown, DollarSign, ArrowUpRight, ArrowDownRight, FileText, Search } from "lucide-react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { API } from "@/App";

const CHART_COLORS = {
  revenue: "hsl(186, 70%, 50%)",
  expense: "hsl(24, 95%, 53%)",
  asset: "hsl(262, 83%, 58%)",
  liability: "hsl(340, 75%, 55%)"
};

const accountTypes = [
  { value: "all", label: "All Types" },
  { value: "revenue", label: "Revenue" },
  { value: "expense", label: "Expense" },
  { value: "asset", label: "Asset" },
  { value: "liability", label: "Liability" },
];

export default function Accounting({ user }) {
  const [summary, setSummary] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");

  useEffect(() => {
    fetchSummary();
    fetchLedger();
  }, [filterType]);

  const fetchSummary = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/accounting/summary`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        setSummary(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch summary:", error);
    }
  };

  const fetchLedger = async () => {
    try {
      const token = localStorage.getItem("token");
      const url = filterType && filterType !== "all" 
        ? `${API}/ledger?account_type=${filterType}`
        : `${API}/ledger`;
      const response = await fetch(url, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        setLedger(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch ledger:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLedger = ledger.filter(entry =>
    entry.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entry.account_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entry.reference_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Prepare chart data
  const accountTypeData = [
    { name: "Revenue", value: summary?.total_revenue || 0, fill: CHART_COLORS.revenue },
    { name: "Expenses", value: summary?.total_expenses || 0, fill: CHART_COLORS.expense },
    { name: "Receivables", value: summary?.total_receivables || 0, fill: CHART_COLORS.asset },
    { name: "Payables", value: summary?.total_payables || 0, fill: CHART_COLORS.liability },
  ];

  // Group ledger by date for trend
  const trendData = ledger.reduce((acc, entry) => {
    const date = entry.entry_date?.split('T')[0];
    if (!acc[date]) {
      acc[date] = { date, revenue: 0, expense: 0 };
    }
    if (entry.account_type === 'revenue') {
      acc[date].revenue += entry.credit;
    } else if (entry.account_type === 'expense') {
      acc[date].expense += entry.debit;
    }
    return acc;
  }, {});
  
  const trendChartData = Object.values(trendData).slice(-7);

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="accounting-page">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Accounting</h1>
        <p className="text-muted-foreground mt-1">Financial overview, ledger entries, and reconciliation.</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="metric-card card-hover">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Revenue</p>
                <p className="text-3xl font-bold mt-2 mono text-primary">
                  ₹{(summary?.total_revenue || 0).toLocaleString()}
                </p>
                <div className="flex items-center gap-1 mt-1 text-bw-volt text-400 text-sm">
                  <ArrowUpRight className="h-4 w-4" />
                  <span>Income</span>
                </div>
              </div>
              <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card card-hover">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Expenses</p>
                <p className="text-3xl font-bold mt-2 mono text-chart-2">
                  ₹{(summary?.total_expenses || 0).toLocaleString()}
                </p>
                <div className="flex items-center gap-1 mt-1 text-red-400 text-sm">
                  <ArrowDownRight className="h-4 w-4" />
                  <span>Costs</span>
                </div>
              </div>
              <div className="h-12 w-12 rounded-xl bg-chart-2/10 flex items-center justify-center">
                <TrendingDown className="h-6 w-6 text-chart-2" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card card-hover">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Accounts Receivable</p>
                <p className="text-3xl font-bold mt-2 mono">
                  ₹{(summary?.total_receivables || 0).toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground mt-1">Outstanding invoices</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-chart-3/10 flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-chart-3" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card card-hover">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Net Profit</p>
                <p className={`text-3xl font-bold mt-2 mono ${(summary?.net_profit || 0) >= 0 ? 'text-bw-volt text-400' : 'text-red-400'}`}>
                  ₹{(summary?.net_profit || 0).toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground mt-1">Revenue - Expenses</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-bw-volt/10 flex items-center justify-center">
                <Calculator className="h-6 w-6 text-bw-volt text-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Account Distribution */}
        <Card className="chart-container">
          <CardHeader>
            <CardTitle>Account Distribution</CardTitle>
            <CardDescription>Breakdown of financial accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={accountTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {accountTypeData.map((entry, index) => (
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
                    formatter={(value) => [`₹${value.toLocaleString()}`, '']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap justify-center gap-4 mt-4">
              {accountTypeData.map((entry, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: entry.fill }} />
                  <span className="text-sm text-muted-foreground">{entry.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Revenue vs Expenses Trend */}
        <Card className="chart-container">
          <CardHeader>
            <CardTitle>Revenue vs Expenses</CardTitle>
            <CardDescription>Daily financial trend</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendChartData.length > 0 ? trendChartData : [{ date: 'No Data', revenue: 0, expense: 0 }]}>
                  <XAxis 
                    dataKey="date" 
                    axisLine={false} 
                    tickLine={false}
                    tick={{ fill: 'hsl(215 20% 65%)', fontSize: 12 }}
                    tickFormatter={(value) => value.slice(-5)}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false}
                    tick={{ fill: 'hsl(215 20% 65%)', fontSize: 12 }}
                    tickFormatter={(value) => `₹${value/1000}k`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(217 33% 17%)', 
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      color: 'white'
                    }}
                    formatter={(value, name) => [`₹${value.toLocaleString()}`, name === 'revenue' ? 'Revenue' : 'Expense']}
                  />
                  <Bar dataKey="revenue" fill={CHART_COLORS.revenue} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="expense" fill={CHART_COLORS.expense} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ledger Section */}
      <Card className="border-white/10 bg-card/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            General Ledger
          </CardTitle>
          <CardDescription>Complete audit trail of all financial transactions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search ledger entries..."
                className="pl-10 bg-background/50"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-48 bg-background/50">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                {accountTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Ledger Table */}
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading ledger...</div>
          ) : filteredLedger.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No ledger entries found. Financial transactions will appear here.
            </div>
          ) : (
            <Table className="data-table">
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>Date</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Reference</TableHead>
                  <TableHead className="text-right">Debit</TableHead>
                  <TableHead className="text-right">Credit</TableHead>
                  <TableHead>Type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLedger.slice(0, 50).map((entry) => (
                  <TableRow key={entry.entry_id} className="border-white/10">
                    <TableCell className="mono text-sm">
                      {entry.entry_date?.split('T')[0]}
                    </TableCell>
                    <TableCell className="font-medium">{entry.account_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
                      {entry.description}
                    </TableCell>
                    <TableCell className="mono text-xs">{entry.reference_id}</TableCell>
                    <TableCell className="text-right mono">
                      {entry.debit > 0 ? `₹${entry.debit.toLocaleString()}` : '-'}
                    </TableCell>
                    <TableCell className="text-right mono">
                      {entry.credit > 0 ? `₹${entry.credit.toLocaleString()}` : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant="outline"
                        className={
                          entry.account_type === 'revenue' ? 'badge-success' :
                          entry.account_type === 'expense' ? 'badge-danger' :
                          entry.account_type === 'asset' ? 'badge-info' :
                          'badge-warning'
                        }
                      >
                        {entry.account_type}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          
          {filteredLedger.length > 50 && (
            <p className="text-center text-sm text-muted-foreground">
              Showing 50 of {filteredLedger.length} entries
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
