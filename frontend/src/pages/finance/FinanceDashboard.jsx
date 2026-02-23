import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { 
  Wallet, Users, Receipt, Clock, AlertTriangle, TrendingUp,
  TrendingDown, Building2, CreditCard, Banknote, Check, X,
  ArrowRight, Calendar, FileText, ChevronRight
} from "lucide-react";
import { BarChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart } from "recharts";
import { API } from "@/App";

const getHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token")}`
});

const formatCurrency = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val || 0);
const formatCompact = (val) => {
  if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
  if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
  if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`;
  return formatCurrency(val);
};

export default function FinanceDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API}/finance/dashboard`, { headers: getHeaders() });
      const data = await res.json();
      if (data.dashboard) {
        setDashboard(data.dashboard);
      }
    } catch (err) {
      console.error("Failed to fetch dashboard:", err);
      toast.error("Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveExpense = async (expenseId) => {
    try {
      const res = await fetch(`${API}/expenses/${expenseId}/approve`, {
        method: "POST",
        headers: getHeaders()
      });
      if (res.ok) {
        toast.success("Expense approved");
        fetchDashboard();
      }
    } catch (err) {
      toast.error("Failed to approve expense");
    }
  };

  const handleRejectExpense = async (expenseId) => {
    try {
      const res = await fetch(`${API}/expenses/${expenseId}/reject`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ rejection_reason: "Rejected from dashboard" })
      });
      if (res.ok) {
        toast.success("Expense rejected");
        fetchDashboard();
      }
    } catch (err) {
      toast.error("Failed to reject expense");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0B0F] text-[#F4F6F0] p-6 flex items-center justify-center">
        <div className="text-[rgba(244,246,240,0.5)]">Loading dashboard...</div>
      </div>
    );
  }

  const cp = dashboard?.cash_position || {};
  const cashFlow = dashboard?.cash_flow_chart || { data: [], totals: {} };
  const bankAccounts = dashboard?.bank_accounts || { accounts: [], total_balance: 0 };
  const overdueBills = dashboard?.overdue_bills || { bills: [], total_count: 0 };
  const pendingExpenses = dashboard?.pending_expenses || { expenses: [], total_count: 0 };
  const upcomingBills = dashboard?.upcoming_bills || { bills: [], total_count: 0, total_amount: 0 };

  return (
    <div data-testid="finance-dashboard" className="min-h-screen bg-[#0B0B0F] text-[#F4F6F0] p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Finance Dashboard</h1>
          <p className="text-sm text-[rgba(244,246,240,0.65)]">Financial health at a glance</p>
        </div>
        <div className="text-xs text-[rgba(244,246,240,0.4)] font-mono">
          Updated: {new Date(dashboard?.generated_at).toLocaleString()}
        </div>
      </div>

      {/* ROW 1 — Cash Position Strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Card 1: Total Bank Balance */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between mb-2">
              <Wallet className="w-5 h-5 text-[#C8FF00]" />
            </div>
            <p className={`text-xl font-bold font-mono ${cp.total_bank_balance?.value >= 0 ? 'text-[#C8FF00]' : 'text-[#FF3B2F]'}`}>
              {formatCompact(cp.total_bank_balance?.value)}
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.5)] mt-1">Total Bank Balance</p>
            <p className="text-[10px] text-[rgba(244,246,240,0.35)]">Across {cp.total_bank_balance?.num_accounts} accounts</p>
          </CardContent>
        </Card>

        {/* Card 2: Accounts Receivable */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between mb-2">
              <TrendingUp className="w-5 h-5 text-[#C8FF00]" />
            </div>
            <p className="text-xl font-bold font-mono text-[#C8FF00]">
              {formatCompact(cp.accounts_receivable?.value)}
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.5)] mt-1">Accounts Receivable</p>
            <p className="text-[10px] text-[rgba(244,246,240,0.35)]">{cp.accounts_receivable?.count} invoices pending</p>
          </CardContent>
        </Card>

        {/* Card 3: Accounts Payable */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between mb-2">
              <TrendingDown className="w-5 h-5 text-[#FF8C00]" />
            </div>
            <p className="text-xl font-bold font-mono text-[#FF8C00]">
              {formatCompact(cp.accounts_payable?.value)}
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.5)] mt-1">Accounts Payable</p>
            <p className="text-[10px] text-[rgba(244,246,240,0.35)]">{cp.accounts_payable?.count} bills pending</p>
          </CardContent>
        </Card>

        {/* Card 4: Expenses Pending Approval */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between mb-2">
              <Clock className={`w-5 h-5 ${cp.pending_expenses?.count > 0 ? 'text-[#FFB300]' : 'text-[rgba(244,246,240,0.3)]'}`} />
            </div>
            <p className={`text-xl font-bold font-mono ${cp.pending_expenses?.count > 0 ? 'text-[#FFB300]' : 'text-[rgba(244,246,240,0.3)]'}`}>
              {cp.pending_expenses?.count || 0}
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.5)] mt-1">Pending Approval</p>
            <p className="text-[10px] text-[rgba(244,246,240,0.35)]">{formatCurrency(cp.pending_expenses?.amount)} pending</p>
          </CardContent>
        </Card>

        {/* Card 5: Overdue Bills */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between mb-2">
              <AlertTriangle className={`w-5 h-5 ${cp.overdue_bills?.count > 0 ? 'text-[#FF3B2F]' : 'text-[rgba(244,246,240,0.3)]'}`} />
            </div>
            <p className={`text-xl font-bold font-mono ${cp.overdue_bills?.count > 0 ? 'text-[#FF3B2F]' : 'text-[rgba(244,246,240,0.3)]'}`}>
              {cp.overdue_bills?.count || 0}
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.5)] mt-1">Overdue Bills</p>
            <p className="text-[10px] text-[rgba(244,246,240,0.35)]">{formatCurrency(cp.overdue_bills?.amount)} overdue</p>
          </CardContent>
        </Card>

        {/* Card 6: Net Cash Flow */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between mb-2">
              {cp.net_cash_flow?.value >= 0 ? (
                <TrendingUp className="w-5 h-5 text-[#1AFFE4]" />
              ) : (
                <TrendingDown className="w-5 h-5 text-[#FF3B2F]" />
              )}
            </div>
            <p className={`text-xl font-bold font-mono ${cp.net_cash_flow?.value >= 0 ? 'text-[#1AFFE4]' : 'text-[#FF3B2F]'}`}>
              {formatCompact(cp.net_cash_flow?.value)}
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.5)] mt-1">Net Cash Flow</p>
            <p className="text-[10px] text-[rgba(244,246,240,0.35)]">+{formatCompact(cp.net_cash_flow?.credits)} in · -{formatCompact(cp.net_cash_flow?.debits)} out</p>
          </CardContent>
        </Card>
      </div>

      {/* ROW 2 — Chart + Bank Accounts */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* LEFT: Cash Flow Chart (60%) */}
        <Card className="lg:col-span-3 bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium">Cash Flow — Last 6 Months</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={cashFlow.data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis 
                    dataKey="month_label" 
                    tick={{ fill: 'rgba(244,246,240,0.5)', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  />
                  <YAxis 
                    tick={{ fill: 'rgba(244,246,240,0.5)', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    tickFormatter={(v) => formatCompact(v)}
                    axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      background: '#111820', 
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                    labelStyle={{ color: '#F4F6F0', fontWeight: 600 }}
                    formatter={(value, name) => [formatCurrency(value), name === 'credits' ? 'Income' : name === 'debits' ? 'Expenses' : 'Net']}
                  />
                  <Bar dataKey="credits" name="credits" fill="#C8FF00" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="debits" name="debits" fill="#FF8C00" radius={[4, 4, 0, 0]} />
                  <Line type="monotone" dataKey="net" name="net" stroke="#1AFFE4" strokeWidth={2} dot={{ fill: '#1AFFE4', r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            
            {/* Summary Pills */}
            <div className="flex items-center gap-3 mt-4 pt-4 border-t border-[rgba(255,255,255,0.05)]">
              <div className="px-3 py-1.5 rounded-full bg-[rgba(200,255,0,0.1)] text-[#C8FF00] text-xs font-mono">
                Total In: {formatCurrency(cashFlow.totals?.total_in)}
              </div>
              <div className="px-3 py-1.5 rounded-full bg-[rgba(255,140,0,0.1)] text-[#FF8C00] text-xs font-mono">
                Total Out: {formatCurrency(cashFlow.totals?.total_out)}
              </div>
              <div className={`px-3 py-1.5 rounded-full text-xs font-mono ${cashFlow.totals?.net >= 0 ? 'bg-[rgba(200,255,0,0.1)] text-[#C8FF00]' : 'bg-[rgba(255,59,47,0.1)] text-[#FF3B2F]'}`}>
                Net: {formatCurrency(cashFlow.totals?.net)}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* RIGHT: Bank Accounts (40%) */}
        <Card className="lg:col-span-2 bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Building2 className="w-4 h-4 text-[#3B9EFF]" />
              Bank Accounts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {bankAccounts.accounts.length === 0 ? (
              <div className="text-center py-8 text-[rgba(244,246,240,0.4)]">
                No bank accounts configured
              </div>
            ) : (
              <>
                {bankAccounts.accounts.map((acc, idx) => (
                  <div key={acc.account_id} className={`py-3 ${idx > 0 ? 'border-t border-[rgba(255,255,255,0.05)]' : ''}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        {acc.account_type === "CASH" ? (
                          <Banknote className="w-4 h-4 text-[#FFB300]" />
                        ) : (
                          <CreditCard className="w-4 h-4 text-[#3B9EFF]" />
                        )}
                        <div>
                          <p className="text-sm font-semibold text-[#F4F6F0]">{acc.account_name}</p>
                          <p className="text-[11px] text-[rgba(244,246,240,0.4)]">{acc.bank_name}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className="text-[10px] border-[rgba(244,246,240,0.2)] text-[rgba(244,246,240,0.5)] mb-1">
                          {acc.account_type}
                        </Badge>
                        <p className={`font-bold font-mono text-sm ${acc.current_balance >= 0 ? 'text-[#C8FF00]' : 'text-[#FF3B2F]'}`}>
                          {formatCurrency(acc.current_balance)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Total Footer */}
                <div className="mt-2 pt-3 border-t-2 border-[rgba(200,255,0,0.2)] bg-[rgba(200,255,0,0.04)] -mx-6 px-6 py-3 rounded-b-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[rgba(244,246,240,0.6)]">TOTAL BALANCE</span>
                    <span className="text-lg font-bold font-mono text-[#C8FF00]">{formatCurrency(bankAccounts.total_balance)}</span>
                  </div>
                </div>
              </>
            )}
            
            {/* Link */}
            <Button 
              variant="link" 
              onClick={() => navigate('/banking')} 
              className="text-[#C8FF00] p-0 h-auto text-[11px] font-mono mt-2"
            >
              View All Transactions <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* ROW 3 — Three Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT: Overdue Bills */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)] border-l-[3px] border-l-[#FF3B2F]">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium">Overdue Bills</CardTitle>
            <p className="text-xs text-[rgba(244,246,240,0.5)]">Require immediate attention</p>
          </CardHeader>
          <CardContent>
            {overdueBills.bills.length === 0 ? (
              <div className="flex items-center gap-2 py-4 text-[#1AFFE4]">
                <Check className="w-4 h-4" />
                <span className="text-sm">No overdue bills</span>
              </div>
            ) : (
              <div className="space-y-3">
                {overdueBills.bills.map(bill => (
                  <div key={bill.bill_id} className="py-2 border-b border-[rgba(255,255,255,0.05)] last:border-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm text-[#F4F6F0]">{bill.vendor_name}</p>
                        <p className="text-[11px] font-mono text-[#C8FF00]">{bill.internal_ref}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[11px] font-mono text-[#FF3B2F]">{bill.due_date}</span>
                          <Badge className="text-[10px] bg-[rgba(255,59,47,0.15)] text-[#FF3B2F] border-0">
                            {bill.days_overdue} days overdue
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm font-bold font-mono text-[#FF3B2F]">{formatCurrency(bill.balance_due)}</p>
                    </div>
                  </div>
                ))}
                
                {overdueBills.total_count > 5 && (
                  <Button 
                    variant="link" 
                    onClick={() => navigate('/bills')} 
                    className="text-[#FF3B2F] p-0 h-auto text-xs"
                  >
                    View all {overdueBills.total_count} overdue bills <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* MIDDLE: Expenses Pending Approval */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)] border-l-[3px] border-l-[#FF8C00]">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium">Pending Approvals</CardTitle>
            <p className="text-xs text-[rgba(244,246,240,0.5)]">Expenses awaiting your action</p>
          </CardHeader>
          <CardContent>
            {pendingExpenses.expenses.length === 0 ? (
              <div className="flex items-center gap-2 py-4 text-[#1AFFE4]">
                <Check className="w-4 h-4" />
                <span className="text-sm">No pending approvals</span>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingExpenses.expenses.map(exp => (
                  <div key={exp.expense_id} className="py-2 border-b border-[rgba(255,255,255,0.05)] last:border-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-[#F4F6F0]">{exp.submitted_by_name || 'Employee'}</p>
                        <Badge variant="outline" className="text-[10px] border-[rgba(244,246,240,0.2)] text-[rgba(244,246,240,0.5)] mt-1">
                          {exp.category_name || 'Expense'}
                        </Badge>
                        <p className="text-[11px] text-[rgba(244,246,240,0.4)] truncate mt-1">{exp.description}</p>
                        <p className="text-[10px] font-mono text-[rgba(244,246,240,0.35)]">{exp.submitted_date || exp.expense_date}</p>
                      </div>
                      <div className="text-right ml-2">
                        <p className="text-sm font-bold font-mono text-[#C8FF00]">{formatCurrency(exp.total_amount)}</p>
                        <div className="flex items-center gap-1 mt-2">
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            onClick={() => handleApproveExpense(exp.expense_id)}
                            className="h-6 w-6 p-0 text-[#1AFFE4] hover:bg-[rgba(26,255,228,0.1)]"
                          >
                            <Check className="w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={() => handleRejectExpense(exp.expense_id)}
                            className="h-6 w-6 p-0 text-[#FF3B2F] hover:bg-[rgba(255,59,47,0.1)]"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {pendingExpenses.total_count > 5 && (
                  <Button 
                    variant="link" 
                    onClick={() => navigate('/expenses')} 
                    className="text-[#FF8C00] p-0 h-auto text-xs"
                  >
                    View all {pendingExpenses.total_count} pending <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* RIGHT: Upcoming Bill Payments */}
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)] border-l-[3px] border-l-[#EAB308]">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium">Due This Week</CardTitle>
            <p className="text-xs text-[rgba(244,246,240,0.5)]">Bills due in next 7 days</p>
          </CardHeader>
          <CardContent>
            {upcomingBills.bills.length === 0 ? (
              <div className="flex items-center gap-2 py-4 text-[#1AFFE4]">
                <Check className="w-4 h-4" />
                <span className="text-sm">No bills due this week</span>
              </div>
            ) : (
              <div className="space-y-3">
                {upcomingBills.bills.map(bill => (
                  <div key={bill.bill_id} className="py-2 border-b border-[rgba(255,255,255,0.05)] last:border-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm text-[#F4F6F0]">{bill.vendor_name}</p>
                        <p className="text-[11px] font-mono text-[#C8FF00]">{bill.internal_ref}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Calendar className="w-3 h-3 text-[rgba(244,246,240,0.4)]" />
                          <span className="text-[11px] font-mono text-[rgba(244,246,240,0.5)]">{bill.due_date}</span>
                          <Badge className="text-[10px] bg-[rgba(234,179,8,0.15)] text-[#EAB308] border-0">
                            {bill.days_until_due === 0 ? 'Due today' : `${bill.days_until_due} days`}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm font-bold font-mono text-[#EAB308]">{formatCurrency(bill.balance_due)}</p>
                    </div>
                  </div>
                ))}
                
                {/* Summary Footer */}
                <div className="pt-2 border-t border-[rgba(255,255,255,0.05)]">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[rgba(244,246,240,0.5)]">Total due this week</span>
                    <span className="font-bold font-mono text-[#EAB308]">{formatCurrency(upcomingBills.total_amount)}</span>
                  </div>
                </div>
                
                {upcomingBills.total_count > 5 && (
                  <Button 
                    variant="link" 
                    onClick={() => navigate('/bills')} 
                    className="text-[#EAB308] p-0 h-auto text-xs"
                  >
                    View all {upcomingBills.total_count} upcoming <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
