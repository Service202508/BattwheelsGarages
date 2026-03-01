import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Plus, Building2, ArrowUpDown, Search, CreditCard, 
  CheckCircle2, Clock, TrendingUp, TrendingDown,
  Banknote, Eye, RefreshCw, ArrowRightLeft, Wallet,
  IndianRupee, Filter, Check
} from "lucide-react";
import { API } from "@/App";

const accountTypes = [
  { value: "CURRENT", label: "Current Account" },
  { value: "SAVINGS", label: "Savings Account" },
  { value: "CASH", label: "Cash Account" },
  { value: "CREDIT_CARD", label: "Credit Card" }
];

const transactionCategories = [
  { value: "CUSTOMER_PAYMENT", label: "Customer Payment" },
  { value: "VENDOR_PAYMENT", label: "Vendor Payment" },
  { value: "EXPENSE", label: "Expense" },
  { value: "SALARY", label: "Salary" },
  { value: "TAX", label: "Tax" },
  { value: "TRANSFER", label: "Transfer" },
  { value: "OTHER", label: "Other" }
];

const getHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token")}`
});

const formatCurrency = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val || 0);

export default function Banking() {
  const [summary, setSummary] = useState({ accounts: [], total_balance: 0 });
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [reconciledFilter, setReconciledFilter] = useState("all");
  
  // Dialogs
  const [showCreateAccount, setShowCreateAccount] = useState(false);
  const [showAddTransaction, setShowAddTransaction] = useState(false);
  const [showTransferDialog, setShowTransferDialog] = useState(false);
  
  // Selected transactions for bulk reconciliation
  const [selectedTxns, setSelectedTxns] = useState([]);
  
  // Account form
  const [accountForm, setAccountForm] = useState({
    account_name: "",
    bank_name: "",
    account_number: "",
    ifsc_code: "",
    account_type: "CURRENT",
    opening_balance: 0,
    opening_balance_date: new Date().toISOString().split("T")[0],
    upi_id: "",
    is_default: false
  });
  
  // Transaction form
  const [txnForm, setTxnForm] = useState({
    transaction_date: new Date().toISOString().split("T")[0],
    description: "",
    transaction_type: "CREDIT",
    amount: 0,
    category: "OTHER",
    reference_number: ""
  });
  
  // Transfer form
  const [transferForm, setTransferForm] = useState({
    from_account_id: "",
    to_account_id: "",
    amount: 0,
    transfer_date: new Date().toISOString().split("T")[0],
    reference: "",
    notes: ""
  });

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchTransactions();
    }
  }, [selectedAccount, dateFrom, dateTo, categoryFilter, reconciledFilter]);

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/banking/summary`, { headers: getHeaders() });
      const data = await res.json();
      if (data.summary) {
        setSummary(data.summary);
        // Auto-select first account if none selected
        if (data.summary.accounts?.length > 0 && !selectedAccount) {
          setSelectedAccount(data.summary.accounts[0]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch banking summary:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    if (!selectedAccount) return;
    
    try {
      let url = `${API}/banking/accounts/${selectedAccount.account_id}/transactions?limit=100`;
      if (dateFrom) url += `&date_from=${dateFrom}`;
      if (dateTo) url += `&date_to=${dateTo}`;
      if (categoryFilter && categoryFilter !== "all") url += `&category=${categoryFilter}`;
      if (reconciledFilter === "yes") url += `&reconciled=true`;
      if (reconciledFilter === "no") url += `&reconciled=false`;
      
      const res = await fetch(url, { headers: getHeaders() });
      const data = await res.json();
      setTransactions(data.transactions || []);
      setSelectedTxns([]);
    } catch (err) {
      console.error("Failed to fetch transactions:", err);
    }
  };

  const handleCreateAccount = async () => {
    if (!accountForm.account_name || !accountForm.bank_name || !accountForm.account_number) {
      return toast.error("Fill required fields (Name, Bank, Account Number)");
    }
    
    try {
      const res = await fetch(`${API}/banking/accounts`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(accountForm)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Account "${data.account.account_name}" created`);
        if (data.account.opening_journal_entry_id) {
          toast.success("Opening balance journal entry posted");
        }
        setShowCreateAccount(false);
        resetAccountForm();
        fetchSummary();
      } else {
        toast.error(data.detail || "Failed to create account");
      }
    } catch (err) {
      toast.error("Error creating account");
    }
  };

  const handleAddTransaction = async () => {
    if (!txnForm.description || txnForm.amount <= 0) {
      return toast.error("Enter valid description and amount");
    }
    
    try {
      const res = await fetch(`${API}/banking/accounts/${selectedAccount.account_id}/transactions`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(txnForm)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success("Transaction recorded");
        setShowAddTransaction(false);
        resetTxnForm();
        fetchSummary();
        fetchTransactions();
      } else {
        toast.error(data.detail || "Failed to record transaction");
      }
    } catch (err) {
      toast.error("Error recording transaction");
    }
  };

  const handleTransfer = async () => {
    if (!transferForm.from_account_id || !transferForm.to_account_id || transferForm.amount <= 0) {
      return toast.error("Select accounts and enter valid amount");
    }
    if (transferForm.from_account_id === transferForm.to_account_id) {
      return toast.error("Cannot transfer to same account");
    }
    
    try {
      const res = await fetch(`${API}/banking/transfer`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(transferForm)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Transferred ${formatCurrency(transferForm.amount)}`);
        setShowTransferDialog(false);
        resetTransferForm();
        fetchSummary();
        if (selectedAccount) fetchTransactions();
      } else {
        toast.error(data.detail || "Transfer failed");
      }
    } catch (err) {
      toast.error("Error processing transfer");
    }
  };

  const handleReconcile = async (txnId, reconciled) => {
    try {
      await fetch(`${API}/banking/reconcile/${txnId}?reconciled=${reconciled}`, {
        method: "POST",
        headers: getHeaders()
      });
      fetchTransactions();
      toast.success(reconciled ? "Transaction reconciled" : "Reconciliation removed");
    } catch (err) {
      toast.error("Error updating reconciliation");
    }
  };

  const handleBulkReconcile = async () => {
    if (selectedTxns.length === 0) return;
    
    try {
      const res = await fetch(`${API}/banking/reconcile`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ transaction_ids: selectedTxns, reconciled: true })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`${data.modified_count} transactions reconciled`);
        setSelectedTxns([]);
        fetchTransactions();
      }
    } catch (err) {
      toast.error("Error reconciling transactions");
    }
  };

  const toggleTxnSelection = (txnId) => {
    setSelectedTxns(prev => 
      prev.includes(txnId) 
        ? prev.filter(id => id !== txnId)
        : [...prev, txnId]
    );
  };

  const selectAllUnreconciled = () => {
    const unreconciledIds = transactions.filter(t => !t.reconciled).map(t => t.transaction_id);
    setSelectedTxns(unreconciledIds);
  };

  const resetAccountForm = () => setAccountForm({
    account_name: "", bank_name: "", account_number: "", ifsc_code: "",
    account_type: "CURRENT", opening_balance: 0, opening_balance_date: new Date().toISOString().split("T")[0],
    upi_id: "", is_default: false
  });
  
  const resetTxnForm = () => setTxnForm({
    transaction_date: new Date().toISOString().split("T")[0], description: "",
    transaction_type: "CREDIT", amount: 0, category: "OTHER", reference_number: ""
  });
  
  const resetTransferForm = () => setTransferForm({
    from_account_id: "", to_account_id: "", amount: 0,
    transfer_date: new Date().toISOString().split("T")[0], reference: "", notes: ""
  });

  return (
    <div data-testid="banking-page" className="min-h-screen bg-bw-black text-bw-white p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Banking</h1>
          <p className="text-sm text-bw-white/[0.65]">Manage bank accounts and transactions</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => setShowTransferDialog(true)} className="border-bw-white/15 text-bw-white hover:bg-bw-white/5">
            <ArrowRightLeft className="w-4 h-4 mr-2" />
            Transfer
          </Button>
          <Button onClick={() => { resetAccountForm(); setShowCreateAccount(true); }} className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover">
            <Plus className="w-4 h-4 mr-2" />
            New Account
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-bw-panel border-bw-white/[0.08]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/50 uppercase tracking-wide">Total Balance</p>
                <p className="text-xl font-bold text-bw-volt">{formatCurrency(summary.total_balance)}</p>
              </div>
              <Wallet className="w-8 h-8 text-bw-volt" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-bw-white/[0.08]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/50 uppercase tracking-wide">Accounts</p>
                <p className="text-xl font-bold text-bw-white">{summary.total_accounts || summary.accounts?.length || 0}</p>
              </div>
              <Building2 className="w-8 h-8 text-bw-blue" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-bw-white/[0.08]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/50 uppercase tracking-wide">This Month Credits</p>
                <p className="text-xl font-bold text-bw-teal">{formatCurrency(summary.this_month?.credits)}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-bw-teal" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-bw-white/[0.08]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/50 uppercase tracking-wide">This Month Debits</p>
                <p className="text-xl font-bold text-bw-red">{formatCurrency(summary.this_month?.debits)}</p>
              </div>
              <TrendingDown className="w-8 h-8 text-bw-red" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Account Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {summary.accounts?.map(acc => (
          <Card 
            key={acc.account_id}
            className={`bg-bw-panel border-bw-white/[0.08] cursor-pointer transition-all ${selectedAccount?.account_id === acc.account_id ? 'ring-2 ring-bw-volt' : 'hover:border-bw-white/20'}`}
            onClick={() => setSelectedAccount(acc)}
          >
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {acc.account_type === "CASH" ? <Banknote className="w-5 h-5 text-bw-amber" /> : <CreditCard className="w-5 h-5 text-bw-blue" />}
                  <span className="text-xs text-bw-white/50 uppercase">{acc.account_type}</span>
                </div>
                {acc.is_default && <Badge className="bg-bw-volt/15 text-bw-volt border-0 text-[10px]">Default</Badge>}
              </div>
              <p className="font-medium text-bw-white truncate">{acc.account_name}</p>
              <p className="text-xs text-bw-white/50">{acc.bank_name} {acc.account_number_last4 && `****${acc.account_number_last4}`}</p>
              <p className="text-xl font-bold mt-3 font-mono">{formatCurrency(acc.current_balance)}</p>
            </CardContent>
          </Card>
        ))}
        
        {(summary.accounts?.length || 0) === 0 && !loading && (
          <Card className="bg-bw-panel border-bw-white/[0.08] border-dashed col-span-full">
            <CardContent className="py-12 text-center">
              <Building2 className="w-12 h-12 text-bw-white/20 mx-auto mb-3" />
              <p className="text-bw-white/50">No bank accounts yet</p>
              <Button variant="link" onClick={() => setShowCreateAccount(true)} className="text-bw-volt">
                Add your first account
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Transactions Section */}
      {selectedAccount && (
        <Card className="bg-bw-panel border-bw-white/[0.08]">
          <CardHeader className="border-b border-bw-white/[0.08]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <ArrowUpDown className="w-5 h-5 text-bw-blue" />
                {selectedAccount.account_name} - Transactions
              </CardTitle>
              <div className="flex items-center gap-2">
                {selectedTxns.length > 0 && (
                  <Button size="sm" onClick={handleBulkReconcile} className="bg-bw-teal text-black hover:bg-bw-teal">
                    <Check className="w-4 h-4 mr-1" />
                    Reconcile ({selectedTxns.length})
                  </Button>
                )}
                <Button variant="outline" size="sm" onClick={selectAllUnreconciled} className="border-bw-white/15 text-bw-white">
                  Select Unreconciled
                </Button>
                <Button size="sm" onClick={() => { resetTxnForm(); setShowAddTransaction(true); }} className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover">
                  <Plus className="w-4 h-4 mr-1" />
                  Add Transaction
                </Button>
              </div>
            </div>
            
            {/* Filters */}
            <div className="flex flex-wrap gap-3 mt-4">
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-bw-black border-bw-white/[0.08] text-bw-white w-36"
                placeholder="From"
              />
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-bw-black border-bw-white/[0.08] text-bw-white w-36"
                placeholder="To"
              />
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="bg-bw-black border-bw-white/[0.08] text-bw-white w-40">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent className="bg-bw-panel border-bw-white/15">
                  <SelectItem value="all" className="text-bw-white">All Categories</SelectItem>
                  {transactionCategories.map(c => <SelectItem key={c.value} value={c.value} className="text-bw-white">{c.label}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={reconciledFilter} onValueChange={setReconciledFilter}>
                <SelectTrigger className="bg-bw-black border-bw-white/[0.08] text-bw-white w-36">
                  <SelectValue placeholder="Reconciled" />
                </SelectTrigger>
                <SelectContent className="bg-bw-panel border-bw-white/15">
                  <SelectItem value="all" className="text-bw-white">All</SelectItem>
                  <SelectItem value="yes" className="text-bw-white">Reconciled</SelectItem>
                  <SelectItem value="no" className="text-bw-white">Unreconciled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-bw-white/[0.08]">
                    <th className="w-8 p-3"></th>
                    <th className="text-left p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Date</th>
                    <th className="text-left p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Description</th>
                    <th className="text-left p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Category</th>
                    <th className="text-left p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Reference</th>
                    <th className="text-right p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Debit</th>
                    <th className="text-right p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Credit</th>
                    <th className="text-right p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Balance</th>
                    <th className="text-center p-3 text-xs font-medium text-bw-white/50 uppercase tracking-wide">Recon</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length === 0 ? (
                    <tr><td colSpan={9} className="text-center p-8 text-bw-white/50">No transactions found</td></tr>
                  ) : (
                    transactions.map(txn => (
                      <tr key={txn.transaction_id} className="border-b border-bw-white/5 hover:bg-bw-white/[0.02]">
                        <td className="p-3">
                          <Checkbox
                            checked={selectedTxns.includes(txn.transaction_id)}
                            onCheckedChange={() => toggleTxnSelection(txn.transaction_id)}
                            className="border-bw-white/30 data-[state=checked]:bg-bw-volt data-[state=checked]:border-bw-volt"
                          />
                        </td>
                        <td className="p-3 text-sm">{txn.transaction_date}</td>
                        <td className="p-3 text-sm">{txn.description}</td>
                        <td className="p-3"><Badge variant="outline" className="border-bw-white/20 text-bw-white/70 text-xs">{txn.category}</Badge></td>
                        <td className="p-3 text-sm text-bw-white/50">{txn.reference_number || "—"}</td>
                        <td className="p-3 text-right font-mono text-bw-red">{txn.transaction_type === "DEBIT" ? formatCurrency(txn.amount) : "—"}</td>
                        <td className="p-3 text-right font-mono text-bw-teal">{txn.transaction_type === "CREDIT" ? formatCurrency(txn.amount) : "—"}</td>
                        <td className="p-3 text-right font-mono">{formatCurrency(txn.balance_after)}</td>
                        <td className="p-3 text-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleReconcile(txn.transaction_id, !txn.reconciled)}
                            className={txn.reconciled ? "text-bw-teal" : "text-bw-white/30"}
                          >
                            {txn.reconciled ? <CheckCircle2 className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Account Dialog */}
      <Dialog open={showCreateAccount} onOpenChange={setShowCreateAccount}>
        <DialogContent className="bg-bw-panel border-bw-white/15 text-bw-white max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-bw-volt" />
              New Bank Account
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-bw-white/70">Account Name *</Label>
                <Input
                  value={accountForm.account_name}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, account_name: e.target.value }))}
                  placeholder="e.g., Main Business Account"
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
              <div>
                <Label className="text-bw-white/70">Bank Name *</Label>
                <Input
                  value={accountForm.bank_name}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, bank_name: e.target.value }))}
                  placeholder="e.g., HDFC Bank"
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-bw-white/70">Account Number *</Label>
                <Input
                  value={accountForm.account_number}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, account_number: e.target.value }))}
                  placeholder="50100123456789"
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
              <div>
                <Label className="text-bw-white/70">IFSC Code</Label>
                <Input
                  value={accountForm.ifsc_code}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, ifsc_code: e.target.value.toUpperCase() }))}
                  placeholder="HDFC0001234"
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-bw-white/70">Account Type</Label>
                <Select value={accountForm.account_type} onValueChange={(v) => setAccountForm(prev => ({ ...prev, account_type: v }))}>
                  <SelectTrigger className="bg-bw-black border-bw-white/15 text-bw-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-bw-panel border-bw-white/15">
                    {accountTypes.map(t => <SelectItem key={t.value} value={t.value} className="text-bw-white">{t.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-bw-white/70">UPI ID</Label>
                <Input
                  value={accountForm.upi_id}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, upi_id: e.target.value }))}
                  placeholder="business@hdfcbank"
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-bw-white/70">Opening Balance</Label>
                <Input
                  type="number"
                  value={accountForm.opening_balance}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, opening_balance: parseFloat(e.target.value) || 0 }))}
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
              <div>
                <Label className="text-bw-white/70">Balance Date</Label>
                <Input
                  type="date"
                  value={accountForm.opening_balance_date}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, opening_balance_date: e.target.value }))}
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Checkbox
                id="is_default"
                checked={accountForm.is_default}
                onCheckedChange={(c) => setAccountForm(prev => ({ ...prev, is_default: !!c }))}
                className="border-bw-white/30"
              />
              <Label htmlFor="is_default" className="text-sm text-bw-white/70">Set as default account</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateAccount(false)} className="border-bw-white/15 text-bw-white">
              Cancel
            </Button>
            <Button onClick={handleCreateAccount} className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover">
              Create Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Transaction Dialog */}
      <Dialog open={showAddTransaction} onOpenChange={setShowAddTransaction}>
        <DialogContent className="bg-bw-panel border-bw-white/15 text-bw-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ArrowUpDown className="w-5 h-5 text-bw-blue" />
              Add Transaction
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-bw-white/70">Date</Label>
                <Input
                  type="date"
                  value={txnForm.transaction_date}
                  onChange={(e) => setTxnForm(prev => ({ ...prev, transaction_date: e.target.value }))}
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
              <div>
                <Label className="text-bw-white/70">Type</Label>
                <Select value={txnForm.transaction_type} onValueChange={(v) => setTxnForm(prev => ({ ...prev, transaction_type: v }))}>
                  <SelectTrigger className="bg-bw-black border-bw-white/15 text-bw-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-bw-panel border-bw-white/15">
                    <SelectItem value="CREDIT" className="text-bw-teal">Credit (Money In)</SelectItem>
                    <SelectItem value="DEBIT" className="text-bw-red">Debit (Money Out)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label className="text-bw-white/70">Description *</Label>
              <Input
                value={txnForm.description}
                onChange={(e) => setTxnForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Transaction description"
                className="bg-bw-black border-bw-white/15 text-bw-white"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-bw-white/70">Amount *</Label>
                <Input
                  type="number"
                  value={txnForm.amount}
                  onChange={(e) => setTxnForm(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
              <div>
                <Label className="text-bw-white/70">Category</Label>
                <Select value={txnForm.category} onValueChange={(v) => setTxnForm(prev => ({ ...prev, category: v }))}>
                  <SelectTrigger className="bg-bw-black border-bw-white/15 text-bw-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-bw-panel border-bw-white/15">
                    {transactionCategories.map(c => <SelectItem key={c.value} value={c.value} className="text-bw-white">{c.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label className="text-bw-white/70">Reference Number</Label>
              <Input
                value={txnForm.reference_number}
                onChange={(e) => setTxnForm(prev => ({ ...prev, reference_number: e.target.value }))}
                placeholder="UTR/Cheque/Reference #"
                className="bg-bw-black border-bw-white/15 text-bw-white"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddTransaction(false)} className="border-bw-white/15 text-bw-white">
              Cancel
            </Button>
            <Button onClick={handleAddTransaction} className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover">
              Add Transaction
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Transfer Dialog */}
      <Dialog open={showTransferDialog} onOpenChange={setShowTransferDialog}>
        <DialogContent className="bg-bw-panel border-bw-white/15 text-bw-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ArrowRightLeft className="w-5 h-5 text-bw-amber" />
              Transfer Between Accounts
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label className="text-bw-white/70">From Account</Label>
              <Select value={transferForm.from_account_id} onValueChange={(v) => setTransferForm(prev => ({ ...prev, from_account_id: v }))}>
                <SelectTrigger className="bg-bw-black border-bw-white/15 text-bw-white">
                  <SelectValue placeholder="Select source account" />
                </SelectTrigger>
                <SelectContent className="bg-bw-panel border-bw-white/15">
                  {summary.accounts?.map(acc => (
                    <SelectItem key={acc.account_id} value={acc.account_id} className="text-bw-white">
                      {acc.account_name} ({formatCurrency(acc.current_balance)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-bw-white/70">To Account</Label>
              <Select value={transferForm.to_account_id} onValueChange={(v) => setTransferForm(prev => ({ ...prev, to_account_id: v }))}>
                <SelectTrigger className="bg-bw-black border-bw-white/15 text-bw-white">
                  <SelectValue placeholder="Select destination account" />
                </SelectTrigger>
                <SelectContent className="bg-bw-panel border-bw-white/15">
                  {summary.accounts?.filter(a => a.account_id !== transferForm.from_account_id).map(acc => (
                    <SelectItem key={acc.account_id} value={acc.account_id} className="text-bw-white">
                      {acc.account_name} ({formatCurrency(acc.current_balance)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-bw-white/70">Amount</Label>
                <Input
                  type="number"
                  value={transferForm.amount}
                  onChange={(e) => setTransferForm(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
              <div>
                <Label className="text-bw-white/70">Date</Label>
                <Input
                  type="date"
                  value={transferForm.transfer_date}
                  onChange={(e) => setTransferForm(prev => ({ ...prev, transfer_date: e.target.value }))}
                  className="bg-bw-black border-bw-white/15 text-bw-white"
                />
              </div>
            </div>
            
            <div>
              <Label className="text-bw-white/70">Reference</Label>
              <Input
                value={transferForm.reference}
                onChange={(e) => setTransferForm(prev => ({ ...prev, reference: e.target.value }))}
                placeholder="Transfer reference"
                className="bg-bw-black border-bw-white/15 text-bw-white"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTransferDialog(false)} className="border-bw-white/15 text-bw-white">
              Cancel
            </Button>
            <Button onClick={handleTransfer} className="bg-bw-amber text-black hover:bg-bw-amber">
              Transfer Funds
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
