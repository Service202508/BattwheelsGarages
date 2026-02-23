import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { 
  Building, CreditCard, Wallet, Plus, ArrowUpRight, ArrowDownLeft, RefreshCw,
  TrendingUp, TrendingDown, IndianRupee, Calculator, FileText, BookOpen,
  CheckCircle2, Clock, Scale, Layers, PieChart, BarChart3, Loader2,
  ArrowRight, Check, X, AlertCircle
} from "lucide-react";
import { API } from "@/App";

const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

export default function Accountant() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(false);
  
  // Dashboard data
  const [dashboardStats, setDashboardStats] = useState(null);
  
  // Bank Accounts
  const [bankAccounts, setBankAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  
  // Reconciliation
  const [reconciliations, setReconciliations] = useState([]);
  const [activeRecon, setActiveRecon] = useState(null);
  const [showReconDialog, setShowReconDialog] = useState(false);
  const [reconForm, setReconForm] = useState({ bank_account_id: "", statement_date: "", statement_balance: 0 });
  
  // Journal Entries
  const [journalEntries, setJournalEntries] = useState([]);
  const [showJournalDialog, setShowJournalDialog] = useState(false);
  const [journalForm, setJournalForm] = useState({
    entry_date: new Date().toISOString().split('T')[0],
    reference: "",
    notes: "",
    lines: [{ account_id: "", account_name: "", debit: 0, credit: 0 }]
  });
  
  // Chart of Accounts
  const [chartOfAccounts, setChartOfAccounts] = useState([]);
  
  // Trial Balance
  const [trialBalance, setTrialBalance] = useState(null);
  
  // Reports
  const [profitLoss, setProfitLoss] = useState(null);
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchDashboard();
    fetchBankAccounts();
    fetchChartOfAccounts();
  }, []);

  useEffect(() => {
    if (activeTab === "reconciliation") fetchReconciliations();
    if (activeTab === "journal") fetchJournalEntries();
    if (activeTab === "trial-balance") fetchTrialBalance();
    if (activeTab === "reports") fetchReports();
  }, [activeTab]);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API}/banking/dashboard/stats`, { headers });
      const data = await res.json();
      setDashboardStats(data.stats);
    } catch (error) {
      console.error("Error fetching dashboard:", error);
    }
  };

  const fetchBankAccounts = async () => {
    try {
      const res = await fetch(`${API}/banking/accounts`, { headers });
      const data = await res.json();
      setBankAccounts(data.bank_accounts || []);
    } catch (error) {
      console.error("Error fetching accounts:", error);
    }
  };

  const fetchTransactions = async (accountId) => {
    try {
      const res = await fetch(`${API}/banking/transactions?bank_account_id=${accountId}`, { headers });
      const data = await res.json();
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error("Error fetching transactions:", error);
    }
  };

  const fetchReconciliations = async () => {
    try {
      const res = await fetch(`${API}/banking/reconciliation/history`, { headers });
      const data = await res.json();
      setReconciliations(data.reconciliations || []);
    } catch (error) {
      console.error("Error fetching reconciliations:", error);
    }
  };

  const fetchJournalEntries = async () => {
    try {
      const res = await fetch(`${API}/banking/journal-entries`, { headers });
      const data = await res.json();
      setJournalEntries(data.journal_entries || []);
    } catch (error) {
      console.error("Error fetching journal entries:", error);
    }
  };

  const fetchChartOfAccounts = async () => {
    try {
      const res = await fetch(`${API}/banking/chart-of-accounts`, { headers });
      const data = await res.json();
      setChartOfAccounts(data.chart_of_accounts || []);
    } catch (error) {
      console.error("Error fetching chart of accounts:", error);
    }
  };

  const fetchTrialBalance = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/banking/reports/trial-balance`, { headers });
      const data = await res.json();
      setTrialBalance(data);
    } catch (error) {
      console.error("Error fetching trial balance:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async () => {
    setLoading(true);
    try {
      const [plRes, bsRes, cfRes] = await Promise.all([
        fetch(`${API}/banking/reports/profit-loss`, { headers }),
        fetch(`${API}/banking/reports/balance-sheet`, { headers }),
        fetch(`${API}/banking/reports/cash-flow`, { headers })
      ]);
      const [plData, bsData, cfData] = await Promise.all([plRes.json(), bsRes.json(), cfRes.json()]);
      setProfitLoss(plData);
      setBalanceSheet(bsData);
      setCashFlow(cfData);
    } catch (error) {
      console.error("Error fetching reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartReconciliation = async () => {
    if (!reconForm.bank_account_id || !reconForm.statement_date) {
      return toast.error("Select account and statement date");
    }
    try {
      const res = await fetch(`${API}/banking/reconciliation/start`, {
        method: "POST",
        headers,
        body: JSON.stringify(reconForm)
      });
      const data = await res.json();
      if (res.ok) {
        setActiveRecon(data.reconciliation);
        toast.success("Reconciliation started");
      }
    } catch (error) {
      toast.error("Error starting reconciliation");
    }
  };

  const handleReconcileTransaction = async (txnId) => {
    try {
      await fetch(`${API}/banking/transactions/${txnId}/reconcile`, { method: "POST", headers });
      if (activeRecon) {
        setActiveRecon({
          ...activeRecon,
          unreconciled_transactions: activeRecon.unreconciled_transactions.filter(t => t.transaction_id !== txnId)
        });
      }
      toast.success("Transaction reconciled");
    } catch (error) {
      toast.error("Error reconciling transaction");
    }
  };

  const handleCompleteReconciliation = async () => {
    if (!activeRecon) return;
    try {
      await fetch(`${API}/banking/reconciliation/${activeRecon.reconciliation_id}/complete`, {
        method: "POST",
        headers,
        body: JSON.stringify({ transaction_ids: [] })
      });
      setActiveRecon(null);
      setShowReconDialog(false);
      fetchReconciliations();
      toast.success("Reconciliation completed");
    } catch (error) {
      toast.error("Error completing reconciliation");
    }
  };

  const handleAddJournalLine = () => {
    setJournalForm({
      ...journalForm,
      lines: [...journalForm.lines, { account_id: "", account_name: "", debit: 0, credit: 0 }]
    });
  };

  const handleRemoveJournalLine = (idx) => {
    setJournalForm({
      ...journalForm,
      lines: journalForm.lines.filter((_, i) => i !== idx)
    });
  };

  const handleCreateJournalEntry = async () => {
    const totalDebit = journalForm.lines.reduce((sum, l) => sum + (parseFloat(l.debit) || 0), 0);
    const totalCredit = journalForm.lines.reduce((sum, l) => sum + (parseFloat(l.credit) || 0), 0);
    
    if (Math.abs(totalDebit - totalCredit) > 0.01) {
      return toast.error(`Entry not balanced. Debit: ${formatCurrency(totalDebit)}, Credit: ${formatCurrency(totalCredit)}`);
    }
    
    if (journalForm.lines.some(l => !l.account_id)) {
      return toast.error("Select account for all lines");
    }
    
    try {
      const res = await fetch(`${API}/banking/journal-entries`, {
        method: "POST",
        headers,
        body: JSON.stringify(journalForm)
      });
      if (res.ok) {
        toast.success("Journal entry created");
        setShowJournalDialog(false);
        setJournalForm({
          entry_date: new Date().toISOString().split('T')[0],
          reference: "",
          notes: "",
          lines: [{ account_id: "", account_name: "", debit: 0, credit: 0 }]
        });
        fetchJournalEntries();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create entry");
      }
    } catch (error) {
      toast.error("Error creating journal entry");
    }
  };

  const accountTypeColors = {
    asset: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
    liability: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
    equity: "bg-blue-100 text-[#3B9EFF]",
    income: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] text-700",
    expense: "bg-orange-100 text-[#FF8C00]"
  };

  return (
    <div className="space-y-6" data-testid="accountant-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Accountant</h1>
          <p className="text-gray-500 text-sm mt-1">Complete accounting module with reconciliation & reports</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5 h-auto">
          <TabsTrigger value="dashboard" className="text-xs sm:text-sm py-2">
            <BarChart3 className="h-4 w-4 mr-1 hidden sm:block" /> Dashboard
          </TabsTrigger>
          <TabsTrigger value="reconciliation" className="text-xs sm:text-sm py-2">
            <Scale className="h-4 w-4 mr-1 hidden sm:block" /> Reconciliation
          </TabsTrigger>
          <TabsTrigger value="journal" className="text-xs sm:text-sm py-2">
            <BookOpen className="h-4 w-4 mr-1 hidden sm:block" /> Journal
          </TabsTrigger>
          <TabsTrigger value="trial-balance" className="text-xs sm:text-sm py-2">
            <Calculator className="h-4 w-4 mr-1 hidden sm:block" /> Trial Balance
          </TabsTrigger>
          <TabsTrigger value="reports" className="text-xs sm:text-sm py-2">
            <FileText className="h-4 w-4 mr-1 hidden sm:block" /> Reports
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-green-50 to-white">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <IndianRupee className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Total Bank Balance</p>
                    <p className="text-xl font-bold">{formatCurrency(dashboardStats?.total_bank_balance)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Building className="h-5 w-5 text-[#3B9EFF]" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Bank Accounts</p>
                    <p className="text-xl font-bold">{dashboardStats?.bank_accounts_count || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[rgba(200,255,0,0.10)] rounded-lg">
                    <ArrowDownLeft className="h-5 w-5 text-[#C8FF00] text-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Monthly Deposits</p>
                    <p className="text-xl font-bold text-[#C8FF00] text-600">{formatCurrency(dashboardStats?.monthly_deposits)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <ArrowUpRight className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Monthly Withdrawals</p>
                    <p className="text-xl font-bold text-red-600">{formatCurrency(dashboardStats?.monthly_withdrawals)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Bank Accounts and Transactions */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-3">
              <h3 className="font-semibold text-[#F4F6F0]">Bank Accounts</h3>
              {bankAccounts.map(acc => (
                <Card 
                  key={acc.bank_account_id}
                  className={`cursor-pointer transition-colors ${selectedAccount?.bank_account_id === acc.bank_account_id ? "ring-2 ring-[#C8FF00]" : ""}`}
                  onClick={() => { setSelectedAccount(acc); fetchTransactions(acc.bank_account_id); }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[rgba(255,255,255,0.05)] rounded-lg">
                          <Building className="h-5 w-5 text-gray-600" />
                        </div>
                        <div>
                          <p className="font-medium">{acc.account_name}</p>
                          <p className="text-xs text-gray-500">{acc.bank_name}</p>
                        </div>
                      </div>
                      <p className="font-bold">{formatCurrency(acc.current_balance)}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="lg:col-span-2 space-y-3">
              <h3 className="font-semibold text-[#F4F6F0]">
                Recent Transactions {selectedAccount && `- ${selectedAccount.account_name}`}
              </h3>
              <Card>
                <CardContent className="p-0">
                  {transactions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      {selectedAccount ? "No transactions found" : "Select an account to view transactions"}
                    </div>
                  ) : (
                    <div className="divide-y max-h-96 overflow-y-auto">
                      {transactions.slice(0, 10).map(txn => (
                        <div key={txn.transaction_id} className="p-4 flex items-center justify-between hover:bg-[#111820]">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-full ${txn.transaction_type === 'deposit' ? 'bg-green-100' : 'bg-red-100'}`}>
                              {txn.transaction_type === 'deposit' 
                                ? <ArrowDownLeft className="h-4 w-4 text-green-600" />
                                : <ArrowUpRight className="h-4 w-4 text-red-600" />
                              }
                            </div>
                            <div>
                              <p className="font-medium">{txn.payee || txn.description || 'Transaction'}</p>
                              <p className="text-xs text-gray-500">{txn.transaction_date}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className={`font-bold ${txn.transaction_type === 'deposit' ? 'text-green-600' : 'text-red-600'}`}>
                              {txn.transaction_type === 'deposit' ? '+' : '-'}{formatCurrency(txn.amount)}
                            </p>
                            {txn.is_reconciled && <Badge variant="outline" className="text-xs">Reconciled</Badge>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Reconciliation Tab */}
        <TabsContent value="reconciliation" className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold">Bank Reconciliation</h3>
            <Dialog open={showReconDialog} onOpenChange={setShowReconDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                  <Plus className="h-4 w-4 mr-2" /> Start Reconciliation
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Bank Reconciliation</DialogTitle>
                </DialogHeader>
                {!activeRecon ? (
                  <div className="space-y-4 py-4">
                    <div>
                      <Label>Bank Account</Label>
                      <Select value={reconForm.bank_account_id} onValueChange={(v) => setReconForm({ ...reconForm, bank_account_id: v })}>
                        <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                        <SelectContent>
                          {bankAccounts.map(acc => (
                            <SelectItem key={acc.bank_account_id} value={acc.bank_account_id}>
                              {acc.account_name} ({formatCurrency(acc.current_balance)})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Statement Date</Label>
                      <Input type="date" value={reconForm.statement_date} onChange={(e) => setReconForm({ ...reconForm, statement_date: e.target.value })} />
                    </div>
                    <div>
                      <Label>Statement Ending Balance</Label>
                      <Input type="number" value={reconForm.statement_balance} onChange={(e) => setReconForm({ ...reconForm, statement_balance: parseFloat(e.target.value) })} />
                    </div>
                    <Button onClick={handleStartReconciliation} className="w-full bg-[#C8FF00] text-[#080C0F] font-bold">
                      Start Reconciliation
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4 p-4 bg-[#111820] rounded-lg">
                      <div>
                        <p className="text-xs text-gray-500">Book Balance</p>
                        <p className="text-lg font-bold">{formatCurrency(activeRecon.book_balance)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Statement Balance</p>
                        <p className="text-lg font-bold">{formatCurrency(activeRecon.statement_balance)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Difference</p>
                        <p className={`text-lg font-bold ${Math.abs(activeRecon.difference) < 0.01 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(activeRecon.difference)}
                        </p>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Unreconciled Transactions ({activeRecon.unreconciled_transactions?.length || 0})</h4>
                      <div className="border rounded-lg max-h-64 overflow-y-auto">
                        {activeRecon.unreconciled_transactions?.map(txn => (
                          <div key={txn.transaction_id} className="p-3 flex items-center justify-between border-b last:border-0 hover:bg-[#111820]">
                            <div>
                              <p className="font-medium">{txn.payee || txn.description}</p>
                              <p className="text-xs text-gray-500">{txn.transaction_date}</p>
                            </div>
                            <div className="flex items-center gap-3">
                              <p className={`font-bold ${txn.transaction_type === 'deposit' ? 'text-green-600' : 'text-red-600'}`}>
                                {formatCurrency(txn.amount)}
                              </p>
                              <Button size="sm" variant="outline" onClick={() => handleReconcileTransaction(txn.transaction_id)}>
                                <Check className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" onClick={() => setActiveRecon(null)}>Cancel</Button>
                      <Button onClick={handleCompleteReconciliation} className="bg-green-600 text-white">
                        Complete Reconciliation
                      </Button>
                    </div>
                  </div>
                )}
              </DialogContent>
            </Dialog>
          </div>

          {/* Reconciliation History */}
          <Card>
            <CardHeader>
              <CardTitle>Reconciliation History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Statement Date</TableHead>
                    <TableHead className="text-right">Statement Balance</TableHead>
                    <TableHead className="text-right">Book Balance</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Completed</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reconciliations.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        No reconciliations yet
                      </TableCell>
                    </TableRow>
                  ) : reconciliations.map(rec => (
                    <TableRow key={rec.reconciliation_id}>
                      <TableCell className="font-medium">{rec.bank_account_name}</TableCell>
                      <TableCell>{rec.statement_date}</TableCell>
                      <TableCell className="text-right">{formatCurrency(rec.statement_balance)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(rec.book_balance)}</TableCell>
                      <TableCell>
                        <Badge className={rec.status === 'completed' ? 'bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]' : 'bg-yellow-100 text-[#EAB308]'}>
                          {rec.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{rec.completed_at ? new Date(rec.completed_at).toLocaleDateString() : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Journal Entries Tab */}
        <TabsContent value="journal" className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold">Journal Entries</h3>
            <Dialog open={showJournalDialog} onOpenChange={setShowJournalDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                  <Plus className="h-4 w-4 mr-2" /> New Journal Entry
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create Journal Entry</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Entry Date</Label>
                      <Input type="date" value={journalForm.entry_date} onChange={(e) => setJournalForm({ ...journalForm, entry_date: e.target.value })} />
                    </div>
                    <div>
                      <Label>Reference</Label>
                      <Input value={journalForm.reference} onChange={(e) => setJournalForm({ ...journalForm, reference: e.target.value })} placeholder="Optional reference" />
                    </div>
                  </div>
                  
                  <div>
                    <Label>Notes</Label>
                    <Textarea value={journalForm.notes} onChange={(e) => setJournalForm({ ...journalForm, notes: e.target.value })} placeholder="Entry description" rows={2} />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Label>Line Items</Label>
                      <Button size="sm" variant="outline" onClick={handleAddJournalLine}>
                        <Plus className="h-3 w-3 mr-1" /> Add Line
                      </Button>
                    </div>
                    <div className="border rounded-lg overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-[#111820]">
                            <TableHead>Account</TableHead>
                            <TableHead className="w-32">Debit</TableHead>
                            <TableHead className="w-32">Credit</TableHead>
                            <TableHead className="w-12"></TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {journalForm.lines.map((line, idx) => (
                            <TableRow key={idx}>
                              <TableCell>
                                <Select 
                                  value={line.account_id} 
                                  onValueChange={(v) => {
                                    const acc = chartOfAccounts.find(a => a.account_id === v);
                                    const newLines = [...journalForm.lines];
                                    newLines[idx] = { ...line, account_id: v, account_name: acc?.account_name };
                                    setJournalForm({ ...journalForm, lines: newLines });
                                  }}
                                >
                                  <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                                  <SelectContent>
                                    {chartOfAccounts.map(acc => (
                                      <SelectItem key={acc.account_id} value={acc.account_id}>
                                        {acc.account_code} - {acc.account_name}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </TableCell>
                              <TableCell>
                                <Input 
                                  type="number" 
                                  value={line.debit || ""} 
                                  onChange={(e) => {
                                    const newLines = [...journalForm.lines];
                                    newLines[idx] = { ...line, debit: parseFloat(e.target.value) || 0, credit: 0 };
                                    setJournalForm({ ...journalForm, lines: newLines });
                                  }}
                                  className="text-right"
                                />
                              </TableCell>
                              <TableCell>
                                <Input 
                                  type="number" 
                                  value={line.credit || ""} 
                                  onChange={(e) => {
                                    const newLines = [...journalForm.lines];
                                    newLines[idx] = { ...line, credit: parseFloat(e.target.value) || 0, debit: 0 };
                                    setJournalForm({ ...journalForm, lines: newLines });
                                  }}
                                  className="text-right"
                                />
                              </TableCell>
                              <TableCell>
                                {journalForm.lines.length > 1 && (
                                  <Button size="sm" variant="ghost" onClick={() => handleRemoveJournalLine(idx)}>
                                    <X className="h-4 w-4 text-red-500" />
                                  </Button>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                          <TableRow className="bg-[#111820] font-bold">
                            <TableCell>Total</TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(journalForm.lines.reduce((s, l) => s + (parseFloat(l.debit) || 0), 0))}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(journalForm.lines.reduce((s, l) => s + (parseFloat(l.credit) || 0), 0))}
                            </TableCell>
                            <TableCell></TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </div>
                    {Math.abs(journalForm.lines.reduce((s, l) => s + (parseFloat(l.debit) || 0), 0) - journalForm.lines.reduce((s, l) => s + (parseFloat(l.credit) || 0), 0)) > 0.01 && (
                      <div className="flex items-center gap-2 text-red-600 text-sm">
                        <AlertCircle className="h-4 w-4" />
                        Entry is not balanced. Debits must equal credits.
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setShowJournalDialog(false)}>Cancel</Button>
                  <Button onClick={handleCreateJournalEntry} className="bg-[#C8FF00] text-[#080C0F] font-bold">
                    Create Entry
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#111820]">
                    <TableHead>Entry #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Reference</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {journalEntries.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        No journal entries yet
                      </TableCell>
                    </TableRow>
                  ) : journalEntries.map(entry => (
                    <TableRow key={entry.entry_id}>
                      <TableCell className="font-medium">{entry.entry_number}</TableCell>
                      <TableCell>{entry.entry_date}</TableCell>
                      <TableCell>{entry.reference || "-"}</TableCell>
                      <TableCell className="text-right">{formatCurrency(entry.total_debit)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(entry.total_credit)}</TableCell>
                      <TableCell>
                        <Badge className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]">{entry.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trial Balance Tab */}
        <TabsContent value="trial-balance" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Trial Balance</CardTitle>
                  <CardDescription>As of {trialBalance?.as_of_date || new Date().toISOString().split('T')[0]}</CardDescription>
                </div>
                <Button variant="outline" onClick={fetchTrialBalance} disabled={loading}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
                </div>
              ) : trialBalance ? (
                <div className="space-y-4">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-[#111820]">
                        <TableHead>Code</TableHead>
                        <TableHead>Account</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead className="text-right">Debit</TableHead>
                        <TableHead className="text-right">Credit</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {trialBalance.accounts?.map((acc, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-mono text-sm">{acc.account_code}</TableCell>
                          <TableCell className="font-medium">{acc.account_name}</TableCell>
                          <TableCell>
                            <Badge className={accountTypeColors[acc.account_type]}>{acc.account_type}</Badge>
                          </TableCell>
                          <TableCell className="text-right">{acc.debit > 0 ? formatCurrency(acc.debit) : "-"}</TableCell>
                          <TableCell className="text-right">{acc.credit > 0 ? formatCurrency(acc.credit) : "-"}</TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-[#C8FF00]/20 font-bold text-lg">
                        <TableCell colSpan={3}>TOTALS</TableCell>
                        <TableCell className="text-right">{formatCurrency(trialBalance.total_debit)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(trialBalance.total_credit)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                  <div className="flex items-center justify-center gap-2 p-4 bg-[#111820] rounded-lg">
                    {trialBalance.is_balanced ? (
                      <>
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                        <span className="text-green-700 font-medium">Trial Balance is Balanced</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-5 w-5 text-red-600" />
                        <span className="text-red-700 font-medium">Trial Balance is NOT Balanced - Difference: {formatCurrency(Math.abs(trialBalance.total_debit - trialBalance.total_credit))}</span>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">No data available</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* P&L Summary */}
              <Card>
                <CardHeader className="bg-gradient-to-r from-green-50 to-white">
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    Profit & Loss
                  </CardTitle>
                  <CardDescription>{profitLoss?.period?.start_date} to {profitLoss?.period?.end_date}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-4">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Total Income</span>
                    <span className="font-bold text-green-600">{formatCurrency(profitLoss?.income?.total)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Total Expenses</span>
                    <span className="font-bold text-red-600">{formatCurrency(profitLoss?.expenses?.total)}</span>
                  </div>
                  <div className="flex justify-between py-2 bg-[#C8FF00]/20 px-2 rounded">
                    <span className="font-bold">Net Profit</span>
                    <span className={`font-bold text-lg ${profitLoss?.net_profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                      {formatCurrency(profitLoss?.net_profit)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 text-center">
                    Profit Margin: {profitLoss?.profit_margin || 0}%
                  </div>
                </CardContent>
              </Card>

              {/* Balance Sheet Summary */}
              <Card>
                <CardHeader className="bg-gradient-to-r from-blue-50 to-white">
                  <CardTitle className="flex items-center gap-2">
                    <Scale className="h-5 w-5 text-[#3B9EFF]" />
                    Balance Sheet
                  </CardTitle>
                  <CardDescription>As of {balanceSheet?.as_of_date}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-4">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Total Assets</span>
                    <span className="font-bold text-green-600">{formatCurrency(balanceSheet?.assets?.total)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Total Liabilities</span>
                    <span className="font-bold text-red-600">{formatCurrency(balanceSheet?.liabilities?.total)}</span>
                  </div>
                  <div className="flex justify-between py-2 bg-blue-50 px-2 rounded">
                    <span className="font-bold">Total Equity</span>
                    <span className="font-bold text-lg text-[#3B9EFF]">{formatCurrency(balanceSheet?.equity?.total)}</span>
                  </div>
                  <div className="text-sm text-center">
                    {balanceSheet?.is_balanced ? (
                      <span className="text-green-600 flex items-center justify-center gap-1">
                        <CheckCircle2 className="h-4 w-4" /> Balanced
                      </span>
                    ) : (
                      <span className="text-red-600">Not Balanced</span>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Cash Flow Summary */}
              <Card className="md:col-span-2">
                <CardHeader className="bg-gradient-to-r from-purple-50 to-white">
                  <CardTitle className="flex items-center gap-2">
                    <ArrowRight className="h-5 w-5 text-purple-600" />
                    Cash Flow Summary
                  </CardTitle>
                  <CardDescription>{cashFlow?.period?.start_date} to {cashFlow?.period?.end_date}</CardDescription>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <Card className="bg-[rgba(34,197,94,0.08)] border-green-200">
                      <CardContent className="p-4 text-center">
                        <ArrowDownLeft className="h-6 w-6 mx-auto text-green-600 mb-2" />
                        <p className="text-xs text-green-700">Cash Inflows</p>
                        <p className="text-xl font-bold text-green-800">{formatCurrency(cashFlow?.cash_inflows)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-[rgba(255,59,47,0.08)] border-red-200">
                      <CardContent className="p-4 text-center">
                        <ArrowUpRight className="h-6 w-6 mx-auto text-red-600 mb-2" />
                        <p className="text-xs text-red-700">Cash Outflows</p>
                        <p className="text-xl font-bold text-red-800">{formatCurrency(cashFlow?.cash_outflows)}</p>
                      </CardContent>
                    </Card>
                    <Card className={`${cashFlow?.net_cash_flow >= 0 ? 'bg-[rgba(200,255,0,0.08)] border-[rgba(200,255,0,0.20)]' : 'bg-[rgba(255,140,0,0.08)] border-orange-200'}`}>
                      <CardContent className="p-4 text-center">
                        <IndianRupee className={`h-6 w-6 mx-auto mb-2 ${cashFlow?.net_cash_flow >= 0 ? 'text-[#C8FF00] text-600' : 'text-[#FF8C00]'}`} />
                        <p className={`text-xs ${cashFlow?.net_cash_flow >= 0 ? 'text-[#C8FF00] text-700' : 'text-[#FF8C00]'}`}>Net Cash Flow</p>
                        <p className={`text-xl font-bold ${cashFlow?.net_cash_flow >= 0 ? 'text-[#C8FF00] text-800' : 'text-orange-800'}`}>
                          {formatCurrency(cashFlow?.net_cash_flow)}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
