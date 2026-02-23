/**
 * Battwheels OS - Zoho Books-style Financial Home Dashboard
 * Main landing page with financial overview, cash flow, and business metrics
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Receipt, 
  CreditCard, 
  Wallet,
  Plus,
  RefreshCw,
  ArrowRight,
  AlertCircle,
  Building2,
  Clock,
  FileText,
  Users,
  Package
} from "lucide-react";
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart, Legend
} from "recharts";
import { Link } from "react-router-dom";
import { API, getAuthHeaders } from "@/App";
import { toast } from "sonner";

// Chart colors
const COLORS = {
  primary: "#10B981",
  secondary: "#3B82F6", 
  danger: "#EF4444",
  warning: "#F59E0B",
  purple: "#8B5CF6",
  gray: "#6B7280",
  incoming: "#10B981",
  outgoing: "#EF4444"
};

const EXPENSE_COLORS = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6", "#6B7280"];

// Format currency (Indian Rupees)
const formatCurrency = (amount, compact = false) => {
  if (amount === undefined || amount === null) return "₹0";
  const num = parseFloat(amount);
  if (compact) {
    if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)}Cr`;
    if (num >= 100000) return `₹${(num / 100000).toFixed(2)}L`;
    if (num >= 1000) return `₹${(num / 1000).toFixed(1)}K`;
  }
  return new Intl.NumberFormat('en-IN', { 
    style: 'currency', 
    currency: 'INR',
    minimumFractionDigits: 2 
  }).format(num);
};

// Metric Card Component
const MetricCard = ({ title, value, subtitle, icon: Icon, trend, trendValue, onClick, badge, badgeVariant = "default" }) => (
  <Card 
    className={`relative overflow-hidden transition-all duration-200 ${onClick ? 'cursor-pointer hover:border-[rgba(200,255,0,0.2)]' : ''}`}
    onClick={onClick}
    data-testid={`metric-${title?.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          {trend && (
            <div className={`flex items-center gap-1 text-xs ${trend === 'up' ? 'text-green-500' : 'text-red-500'}`}>
              {trend === 'up' ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              <span>{trendValue}</span>
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          {badge && (
            <Badge variant={badgeVariant} className="text-xs">
              {badge}
            </Badge>
          )}
          {Icon && (
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Icon className="h-5 w-5 text-primary" />
            </div>
          )}
        </div>
      </div>
    </CardContent>
  </Card>
);

// Receivables/Payables Widget
const ReceivablesPayablesWidget = ({ type, data, loading }) => {
  const isReceivable = type === "receivables";
  const title = isReceivable ? "Total Receivables" : "Total Payables";
  const Icon = isReceivable ? TrendingUp : TrendingDown;
  const color = isReceivable ? COLORS.primary : COLORS.danger;
  
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-4 w-full" />
          <div className="flex gap-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-24" />
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const total = data?.total || 0;
  const current = data?.current || 0;
  const overdue = data?.overdue || 0;
  const overduePercent = total > 0 ? (overdue / total) * 100 : 0;
  
  return (
    <Card className="h-full" data-testid={`widget-${type}`}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
        <Link to={isReceivable ? "/invoices-enhanced" : "/bills-enhanced"}>
          <Button variant="outline" size="sm" className="h-7 gap-1">
            <Plus className="h-3 w-3" />
            New
          </Button>
        </Link>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-xs text-muted-foreground mb-1">
            Total Unpaid {isReceivable ? "Invoices" : "Bills"}
          </p>
          <p className="text-3xl font-bold">{formatCurrency(total)}</p>
        </div>
        
        {/* Progress bar */}
        <div className="h-2 w-full bg-[#141E27] rounded-full overflow-hidden">
          <div 
            className="h-full transition-all duration-500"
            style={{ 
              width: `${overduePercent}%`,
              backgroundColor: COLORS.warning
            }}
          />
        </div>
        
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-blue-500" />
            <span>Current: {formatCurrency(current)}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-[#FF8C00]" />
            <span>Overdue: {formatCurrency(overdue)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Cash Flow Chart Widget
const CashFlowWidget = ({ data, loading, period, onPeriodChange }) => {
  if (loading) {
    return (
      <Card className="col-span-full">
        <CardHeader>
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }
  
  const monthlyData = data?.monthly_data || [];
  const totalIncoming = data?.total_incoming || 0;
  const totalOutgoing = data?.total_outgoing || 0;
  const closingBalance = data?.closing_balance || 0;
  
  return (
    <Card className="col-span-full" data-testid="cash-flow-widget">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg">Cash Flow</CardTitle>
          <CardDescription>Monthly cash movement</CardDescription>
        </div>
        <Select value={period} onValueChange={onPeriodChange}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fiscal_year">This Fiscal Year</SelectItem>
            <SelectItem value="last_12_months">Last 12 Months</SelectItem>
            <SelectItem value="last_6_months">Last 6 Months</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 h-[280px]">
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <AreaChart data={monthlyData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="month_short" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fill: '#888', fontSize: 12 }}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fill: '#888', fontSize: 12 }}
                  tickFormatter={(v) => `${(v / 100000).toFixed(0)}L`}
                />
                <Tooltip 
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="running_balance" 
                  stroke={COLORS.primary}
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorNet)" 
                  name="Cash Balance"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          <div className="lg:w-64 space-y-4 p-4 bg-muted/30 rounded-lg">
            <div>
              <p className="text-xs text-muted-foreground">Opening Balance</p>
              <p className="text-lg font-semibold">{formatCurrency(data?.opening_balance || 0)}</p>
            </div>
            <div className="flex items-center gap-2 text-[#22C55E]">
              <TrendingUp className="h-4 w-4" />
              <div>
                <p className="text-xs text-muted-foreground">Incoming</p>
                <p className="text-lg font-semibold">{formatCurrency(totalIncoming)}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-[#FF3B2F]">
              <TrendingDown className="h-4 w-4" />
              <div>
                <p className="text-xs text-muted-foreground">Outgoing</p>
                <p className="text-lg font-semibold">{formatCurrency(totalOutgoing)}</p>
              </div>
            </div>
            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground">Closing Balance</p>
              <p className="text-xl font-bold text-primary">{formatCurrency(closingBalance)}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Income vs Expense Widget
const IncomeExpenseWidget = ({ data, loading, method, onMethodChange }) => {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-4 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    );
  }
  
  const monthlyData = data?.monthly_data || [];
  const totalIncome = data?.total_income || 0;
  const totalExpense = data?.total_expense || 0;
  
  return (
    <Card data-testid="income-expense-widget">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-lg">Income and Expense</CardTitle>
          <CardDescription>This Fiscal Year</CardDescription>
        </div>
        <div className="flex gap-2">
          <Button 
            variant={method === "accrual" ? "default" : "outline"} 
            size="sm"
            onClick={() => onMethodChange("accrual")}
          >
            Accrual
          </Button>
          <Button 
            variant={method === "cash" ? "default" : "outline"} 
            size="sm"
            onClick={() => onMethodChange("cash")}
          >
            Cash
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6 mb-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-sm bg-[#22C55E]" />
            <span>Total Income</span>
            <span className="font-semibold">{formatCurrency(totalIncome, true)}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-sm bg-[#FF3B2F]" />
            <span>Total Expenses</span>
            <span className="font-semibold">{formatCurrency(totalExpense, true)}</span>
          </div>
        </div>
        
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={monthlyData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <XAxis 
                dataKey="month" 
                axisLine={false} 
                tickLine={false}
                tick={{ fill: '#888', fontSize: 11 }}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false}
                tick={{ fill: '#888', fontSize: 11 }}
                tickFormatter={(v) => `${(v / 100000).toFixed(0)}L`}
              />
              <Tooltip 
                formatter={(value) => formatCurrency(value)}
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="income" fill={COLORS.primary} radius={[4, 4, 0, 0]} name="Income" />
              <Bar dataKey="expense" fill={COLORS.danger} radius={[4, 4, 0, 0]} name="Expense" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <p className="text-xs text-muted-foreground mt-2">
          * Income and expense values displayed are exclusive of taxes.
        </p>
      </CardContent>
    </Card>
  );
};

// Top Expenses Widget
const TopExpensesWidget = ({ data, loading }) => {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    );
  }
  
  const categories = data?.categories || [];
  const total = data?.total || 0;
  
  return (
    <Card data-testid="top-expenses-widget">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-lg">Top Expenses</CardTitle>
          <CardDescription>This Fiscal Year</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6">
          <div className="w-40 h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categories}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  paddingAngle={2}
                  dataKey="amount"
                  nameKey="category"
                >
                  {categories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || EXPENSE_COLORS[index % EXPENSE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="text-center -mt-24">
              <p className="text-xs text-muted-foreground">All Expenses</p>
              <p className="text-sm font-bold">{formatCurrency(total, true)}</p>
            </div>
          </div>
          
          <div className="flex-1 space-y-2">
            {categories.map((cat, index) => (
              <div key={cat.category} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div 
                    className="h-3 w-3 rounded-sm" 
                    style={{ backgroundColor: cat.color || EXPENSE_COLORS[index % EXPENSE_COLORS.length] }}
                  />
                  <span className="truncate max-w-[150px]">{cat.category}</span>
                </div>
                <span className="font-medium">{formatCurrency(cat.amount, true)}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Projects Watchlist Widget
const ProjectsWidget = ({ projects, loading }) => {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card data-testid="projects-widget">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Work Orders</CardTitle>
        <CardDescription>Active service tickets</CardDescription>
      </CardHeader>
      <CardContent>
        {projects.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No active work orders</p>
            <Link to="/tickets/new">
              <Button variant="link" className="mt-2">
                Create New Ticket
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {projects.slice(0, 5).map((project) => (
              <Link 
                key={project.project_id} 
                to={`/tickets?id=${project.project_id}`}
                className="block p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-sm">{project.project_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {project.customer_name} • {project.vehicle_number}
                    </p>
                  </div>
                  <Badge variant={project.status === "in_progress" ? "default" : "secondary"}>
                    {project.status?.replace("_", " ")}
                  </Badge>
                </div>
                {project.unbilled_amount > 0 && (
                  <p className="text-xs text-[#FF8C00] mt-1">
                    Unbilled: {formatCurrency(project.unbilled_amount)}
                  </p>
                )}
              </Link>
            ))}
            <Link to="/tickets">
              <Button variant="ghost" className="w-full mt-2">
                View All Tickets <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Bank Accounts Widget
const BankAccountsWidget = ({ data, loading }) => {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-4 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }
  
  const accounts = data?.accounts || [];
  const totalUncategorized = data?.total_uncategorized || 0;
  
  return (
    <Card data-testid="bank-accounts-widget">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Bank and Credit Cards</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {totalUncategorized > 0 && (
          <div className="flex items-center justify-between p-3 bg-[rgba(255,140,0,0.08)] dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-orange-500" />
              <span className="text-sm">{totalUncategorized} Uncategorized Transactions</span>
            </div>
            <Link to="/banking">
              <Button variant="link" size="sm" className="text-[#FF8C00]">
                Categorize now <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            </Link>
          </div>
        )}
        
        {accounts.map((account) => (
          <div 
            key={account.account_id} 
            className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
          >
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                {account.account_type === "credit_card" ? (
                  <CreditCard className="h-4 w-4 text-primary" />
                ) : (
                  <Building2 className="h-4 w-4 text-primary" />
                )}
              </div>
              <div>
                <p className="font-medium text-sm">{account.account_name}</p>
                {account.uncategorized_count > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {account.uncategorized_count} Uncategorized
                  </p>
                )}
              </div>
            </div>
            <p className="font-semibold">{formatCurrency(account.balance)}</p>
          </div>
        ))}
        
        {accounts.length === 0 && (
          <div className="text-center py-6 text-muted-foreground">
            <Wallet className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No bank accounts connected</p>
            <Link to="/banking">
              <Button variant="link" className="mt-2">
                Connect Bank Account
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Main Home Dashboard Component
export default function Home({ user }) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [period, setPeriod] = useState("fiscal_year");
  const [method, setMethod] = useState("accrual");
  
  const [summary, setSummary] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);
  const [incomeExpense, setIncomeExpense] = useState(null);
  const [topExpenses, setTopExpenses] = useState(null);
  const [bankAccounts, setBankAccounts] = useState(null);
  const [projects, setProjects] = useState([]);
  const [quickStats, setQuickStats] = useState(null);
  
  const headers = getAuthHeaders();
  
  // Ensure organization is initialized before fetching
  const ensureOrgInitialized = async () => {
    const existingOrg = localStorage.getItem("organization_id");
    if (existingOrg) return true;
    
    // Try to fetch org
    try {
      const token = localStorage.getItem("token");
      if (!token) return false;
      
      const response = await fetch(`${API}/org`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const org = await response.json();
        if (org.organization_id) {
          localStorage.setItem("organization_id", org.organization_id);
          return true;
        }
      }
    } catch (e) {
      console.error("Failed to fetch org:", e);
    }
    return false;
  };
  
  const fetchDashboardData = useCallback(async (showRefreshToast = false) => {
    try {
      if (showRefreshToast) setRefreshing(true);
      
      const [
        summaryRes,
        cashFlowRes,
        incomeRes,
        expensesRes,
        bankRes,
        projectsRes,
        statsRes
      ] = await Promise.all([
        fetch(`${API}/dashboard/financial/summary`, { headers }),
        fetch(`${API}/dashboard/financial/cash-flow?period=${period}`, { headers }),
        fetch(`${API}/dashboard/financial/income-expense?period=${period}&method=${method}`, { headers }),
        fetch(`${API}/dashboard/financial/top-expenses?period=${period}`, { headers }),
        fetch(`${API}/dashboard/financial/bank-accounts`, { headers }),
        fetch(`${API}/dashboard/financial/projects-watchlist`, { headers }),
        fetch(`${API}/dashboard/financial/quick-stats`, { headers })
      ]);
      
      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setSummary(data.summary);
      }
      
      if (cashFlowRes.ok) {
        const data = await cashFlowRes.json();
        setCashFlow(data.cash_flow);
      }
      
      if (incomeRes.ok) {
        const data = await incomeRes.json();
        setIncomeExpense(data.income_expense);
      }
      
      if (expensesRes.ok) {
        const data = await expensesRes.json();
        setTopExpenses(data.top_expenses);
      }
      
      if (bankRes.ok) {
        const data = await bankRes.json();
        setBankAccounts(data.bank_accounts);
      }
      
      if (projectsRes.ok) {
        const data = await projectsRes.json();
        setProjects(data.projects || []);
      }
      
      if (statsRes.ok) {
        const data = await statsRes.json();
        setQuickStats(data.quick_stats);
      }
      
      if (showRefreshToast) {
        toast.success("Dashboard refreshed");
      }
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      if (showRefreshToast) {
        toast.error("Failed to refresh dashboard");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [headers, period, method]);
  
  useEffect(() => {
    const initAndFetch = async () => {
      await ensureOrgInitialized();
      fetchDashboardData();
    };
    initAndFetch();
  }, [fetchDashboardData]);
  
  return (
    <div className="space-y-6" data-testid="financial-home-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Hello, {user?.name || "Welcome"}</h1>
          <p className="text-muted-foreground">
            {quickStats?.month || "Financial Overview"} • All Locations
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => fetchDashboardData(true)}
          disabled={refreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>
      
      {/* Tabs */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="getting-started">Getting Started</TabsTrigger>
          <TabsTrigger value="updates">Recent Updates</TabsTrigger>
        </TabsList>
        
        <TabsContent value="dashboard" className="mt-6 space-y-6">
          {/* Top Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ReceivablesPayablesWidget 
              type="receivables" 
              data={summary?.receivables} 
              loading={loading} 
            />
            <ReceivablesPayablesWidget 
              type="payables" 
              data={summary?.payables} 
              loading={loading} 
            />
          </div>
          
          {/* Cash Flow Chart */}
          <CashFlowWidget 
            data={cashFlow} 
            loading={loading} 
            period={period}
            onPeriodChange={setPeriod}
          />
          
          {/* Income/Expense and Top Expenses Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <IncomeExpenseWidget 
              data={incomeExpense} 
              loading={loading}
              method={method}
              onMethodChange={setMethod}
            />
            <TopExpensesWidget 
              data={topExpenses} 
              loading={loading} 
            />
          </div>
          
          {/* Projects and Bank Accounts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ProjectsWidget 
              projects={projects} 
              loading={loading} 
            />
            <BankAccountsWidget 
              data={bankAccounts} 
              loading={loading} 
            />
          </div>
          
          {/* Quick Stats Row */}
          {quickStats && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <MetricCard
                title="Invoices This Month"
                value={quickStats.invoices_this_month}
                icon={Receipt}
                onClick={() => window.location.href = "/invoices-enhanced"}
              />
              <MetricCard
                title="Estimates This Month"
                value={quickStats.estimates_this_month}
                icon={FileText}
                onClick={() => window.location.href = "/estimates"}
              />
              <MetricCard
                title="Active Customers"
                value={quickStats.active_customers}
                icon={Users}
                onClick={() => window.location.href = "/contacts"}
              />
              <MetricCard
                title="Active Vendors"
                value={quickStats.active_vendors}
                icon={Building2}
                onClick={() => window.location.href = "/contacts?type=vendor"}
              />
              <MetricCard
                title="Total Items"
                value={quickStats.total_items}
                icon={Package}
                onClick={() => window.location.href = "/items"}
              />
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="getting-started" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Getting Started with Battwheels OS</CardTitle>
              <CardDescription>Complete these steps to set up your workspace</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 p-4 rounded-lg border">
                <div className="h-10 w-10 rounded-full bg-[rgba(34,197,94,0.10)] flex items-center justify-center">
                  <span className="text-[#22C55E] font-bold">✓</span>
                </div>
                <div className="flex-1">
                  <p className="font-medium">Connect Zoho Books</p>
                  <p className="text-sm text-muted-foreground">Sync your accounting data</p>
                </div>
                <Badge variant="outline" className="text-[#22C55E]">Complete</Badge>
              </div>
              
              <div className="flex items-center gap-4 p-4 rounded-lg border">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-primary font-bold">2</span>
                </div>
                <div className="flex-1">
                  <p className="font-medium">Add Bank Accounts</p>
                  <p className="text-sm text-muted-foreground">Connect your bank for automatic feeds</p>
                </div>
                <Link to="/banking">
                  <Button size="sm">Set Up</Button>
                </Link>
              </div>
              
              <div className="flex items-center gap-4 p-4 rounded-lg border">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-primary font-bold">3</span>
                </div>
                <div className="flex-1">
                  <p className="font-medium">Configure Tax Settings</p>
                  <p className="text-sm text-muted-foreground">Set up GST and tax compliance</p>
                </div>
                <Link to="/all-settings">
                  <Button size="sm">Configure</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="updates" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Updates</CardTitle>
              <CardDescription>Latest changes and improvements</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 p-4 rounded-lg bg-muted/50">
                <Badge>New</Badge>
                <div>
                  <p className="font-medium">Zoho-style Financial Dashboard</p>
                  <p className="text-sm text-muted-foreground">
                    Complete financial overview with receivables, payables, cash flow, and expense analytics.
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">February 19, 2026</p>
                </div>
              </div>
              
              <div className="flex gap-4 p-4 rounded-lg bg-muted/50">
                <Badge variant="secondary">Feature</Badge>
                <div>
                  <p className="font-medium">Time Tracking Module</p>
                  <p className="text-sm text-muted-foreground">
                    Track technician hours, manage timers, and convert to invoices.
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">February 19, 2026</p>
                </div>
              </div>
              
              <div className="flex gap-4 p-4 rounded-lg bg-muted/50">
                <Badge variant="secondary">Feature</Badge>
                <div>
                  <p className="font-medium">Documents Module</p>
                  <p className="text-sm text-muted-foreground">
                    Store and manage receipts, attachments, and service photos.
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">February 19, 2026</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
