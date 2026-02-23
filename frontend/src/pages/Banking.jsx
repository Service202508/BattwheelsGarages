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
    <div data-testid="banking-page" className="min-h-screen bg-[#0B0B0F] text-[#F4F6F0] p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Banking</h1>
          <p className="text-sm text-[rgba(244,246,240,0.65)]">Manage bank accounts and transactions</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => setShowTransferDialog(true)} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0] hover:bg-[rgba(244,246,240,0.05)]">
            <ArrowRightLeft className="w-4 h-4 mr-2" />
            Transfer
          </Button>
          <Button onClick={() => { resetAccountForm(); setShowCreateAccount(true); }} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00]">
            <Plus className="w-4 h-4 mr-2" />
            New Account
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Total Balance</p>
                <p className="text-xl font-bold text-[#C8FF00]">{formatCurrency(summary.total_balance)}</p>
              </div>
              <Wallet className="w-8 h-8 text-[#C8FF00]" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Accounts</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{summary.total_accounts || summary.accounts?.length || 0}</p>
              </div>
              <Building2 className="w-8 h-8 text-[#3B9EFF]" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">This Month Credits</p>
                <p className="text-xl font-bold text-[#1AFFE4]">{formatCurrency(summary.this_month?.credits)}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-[#1AFFE4]" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">This Month Debits</p>
                <p className="text-xl font-bold text-[#FF3B2F]">{formatCurrency(summary.this_month?.debits)}</p>
              </div>
              <TrendingDown className="w-8 h-8 text-[#FF3B2F]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Account Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {summary.accounts?.map(acc => (
          <Card 
            key={acc.account_id}
            className={`bg-[#14141B] border-[rgba(244,246,240,0.08)] cursor-pointer transition-all ${selectedAccount?.account_id === acc.account_id ? 'ring-2 ring-[#C8FF00]' : 'hover:border-[rgba(244,246,240,0.2)]'}`}
            onClick={() => setSelectedAccount(acc)}
          >
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {acc.account_type === "CASH" ? <Banknote className="w-5 h-5 text-[#FFB300]" /> : <CreditCard className="w-5 h-5 text-[#3B9EFF]" />}
                  <span className="text-xs text-[rgba(244,246,240,0.5)] uppercase">{acc.account_type}</span>
                </div>
                {acc.is_default && <Badge className="bg-[rgba(200,255,0,0.15)] text-[#C8FF00] border-0 text-[10px]">Default</Badge>}
              </div>
              <p className="font-medium text-[#F4F6F0] truncate">{acc.account_name}</p>
              <p className="text-xs text-[rgba(244,246,240,0.5)]">{acc.bank_name} {acc.account_number_last4 && `****${acc.account_number_last4}`}</p>
              <p className="text-xl font-bold mt-3 font-mono">{formatCurrency(acc.current_balance)}</p>
            </CardContent>
          </Card>
        ))}
        
        {(summary.accounts?.length || 0) === 0 && !loading && (
          <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)] border-dashed col-span-full">
            <CardContent className="py-12 text-center">
              <Building2 className="w-12 h-12 text-[rgba(244,246,240,0.2)] mx-auto mb-3" />
              <p className="text-[rgba(244,246,240,0.5)]">No bank accounts yet</p>
              <Button variant="link" onClick={() => setShowCreateAccount(true)} className="text-[#C8FF00]">
                Add your first account
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Transactions Section */}
      {selectedAccount && (
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardHeader className="border-b border-[rgba(244,246,240,0.08)]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <ArrowUpDown className="w-5 h-5 text-[#3B9EFF]" />
                {selectedAccount.account_name} - Transactions
              </CardTitle>
              <div className="flex items-center gap-2">
                {selectedTxns.length > 0 && (
                  <Button size="sm" onClick={handleBulkReconcile} className="bg-[#1AFFE4] text-black hover:bg-[#00E5CC]">
                    <Check className="w-4 h-4 mr-1" />
                    Reconcile ({selectedTxns.length})
                  </Button>
                )}
                <Button variant="outline" size="sm" onClick={selectAllUnreconciled} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                  Select Unreconciled
                </Button>
                <Button size="sm" onClick={() => { resetTxnForm(); setShowAddTransaction(true); }} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00]">
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
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.08)] text-[#F4F6F0] w-36"
                placeholder="From"
              />
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.08)] text-[#F4F6F0] w-36"
                placeholder="To"
              />
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.08)] text-[#F4F6F0] w-40">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                  <SelectItem value="all" className="text-[#F4F6F0]">All Categories</SelectItem>
                  {transactionCategories.map(c => <SelectItem key={c.value} value={c.value} className="text-[#F4F6F0]">{c.label}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={reconciledFilter} onValueChange={setReconciledFilter}>
                <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.08)] text-[#F4F6F0] w-36">
                  <SelectValue placeholder="Reconciled" />
                </SelectTrigger>
                <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                  <SelectItem value="all" className="text-[#F4F6F0]">All</SelectItem>
                  <SelectItem value="yes" className="text-[#F4F6F0]">Reconciled</SelectItem>
                  <SelectItem value="no" className="text-[#F4F6F0]">Unreconciled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[rgba(244,246,240,0.08)]">
                    <th className="w-8 p-3"></th>
                    <th className="text-left p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Date</th>
                    <th className="text-left p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Description</th>
                    <th className="text-left p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Category</th>
                    <th className="text-left p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Reference</th>
                    <th className="text-right p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Debit</th>
                    <th className="text-right p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Credit</th>
                    <th className="text-right p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Balance</th>
                    <th className="text-center p-3 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Recon</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length === 0 ? (
                    <tr><td colSpan={9} className="text-center p-8 text-[rgba(244,246,240,0.5)]">No transactions found</td></tr>
                  ) : (
                    transactions.map(txn => (
                      <tr key={txn.transaction_id} className="border-b border-[rgba(244,246,240,0.05)] hover:bg-[rgba(244,246,240,0.02)]">
                        <td className="p-3">
                          <Checkbox
                            checked={selectedTxns.includes(txn.transaction_id)}
                            onCheckedChange={() => toggleTxnSelection(txn.transaction_id)}
                            className="border-[rgba(244,246,240,0.3)] data-[state=checked]:bg-[#C8FF00] data-[state=checked]:border-[#C8FF00]"
                          />
                        </td>
                        <td className="p-3 text-sm">{txn.transaction_date}</td>
                        <td className="p-3 text-sm">{txn.description}</td>
                        <td className="p-3"><Badge variant="outline" className="border-[rgba(244,246,240,0.2)] text-[rgba(244,246,240,0.7)] text-xs">{txn.category}</Badge></td>
                        <td className="p-3 text-sm text-[rgba(244,246,240,0.5)]">{txn.reference_number || "—"}</td>
                        <td className="p-3 text-right font-mono text-[#FF3B2F]">{txn.transaction_type === "DEBIT" ? formatCurrency(txn.amount) : "—"}</td>
                        <td className="p-3 text-right font-mono text-[#1AFFE4]">{txn.transaction_type === "CREDIT" ? formatCurrency(txn.amount) : "—"}</td>
                        <td className="p-3 text-right font-mono">{formatCurrency(txn.balance_after)}</td>
                        <td className="p-3 text-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleReconcile(txn.transaction_id, !txn.reconciled)}
                            className={txn.reconciled ? "text-[#1AFFE4]" : "text-[rgba(244,246,240,0.3)]"}
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
        <DialogContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)] text-[#F4F6F0] max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-[#C8FF00]" />
              New Bank Account
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Account Name *</Label>
                <Input
                  value={accountForm.account_name}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, account_name: e.target.value }))}
                  placeholder="e.g., Main Business Account"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Bank Name *</Label>
                <Input
                  value={accountForm.bank_name}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, bank_name: e.target.value }))}
                  placeholder="e.g., HDFC Bank"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Account Number *</Label>
                <Input
                  value={accountForm.account_number}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, account_number: e.target.value }))}
                  placeholder="50100123456789"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">IFSC Code</Label>
                <Input
                  value={accountForm.ifsc_code}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, ifsc_code: e.target.value.toUpperCase() }))}
                  placeholder="HDFC0001234"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Account Type</Label>
                <Select value={accountForm.account_type} onValueChange={(v) => setAccountForm(prev => ({ ...prev, account_type: v }))}>
                  <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                    {accountTypes.map(t => <SelectItem key={t.value} value={t.value} className="text-[#F4F6F0]">{t.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">UPI ID</Label>
                <Input
                  value={accountForm.upi_id}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, upi_id: e.target.value }))}
                  placeholder="business@hdfcbank"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Opening Balance</Label>
                <Input
                  type="number"
                  value={accountForm.opening_balance}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, opening_balance: parseFloat(e.target.value) || 0 }))}
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Balance Date</Label>
                <Input
                  type="date"
                  value={accountForm.opening_balance_date}
                  onChange={(e) => setAccountForm(prev => ({ ...prev, opening_balance_date: e.target.value }))}
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Checkbox
                id="is_default"
                checked={accountForm.is_default}
                onCheckedChange={(c) => setAccountForm(prev => ({ ...prev, is_default: !!c }))}
                className="border-[rgba(244,246,240,0.3)]"
              />
              <Label htmlFor="is_default" className="text-sm text-[rgba(244,246,240,0.7)]">Set as default account</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateAccount(false)} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
              Cancel
            </Button>
            <Button onClick={handleCreateAccount} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00]">
              Create Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Transaction Dialog */}
      <Dialog open={showAddTransaction} onOpenChange={setShowAddTransaction}>
        <DialogContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ArrowUpDown className="w-5 h-5 text-[#3B9EFF]" />
              Add Transaction
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Date</Label>
                <Input
                  type="date"
                  value={txnForm.transaction_date}
                  onChange={(e) => setTxnForm(prev => ({ ...prev, transaction_date: e.target.value }))}
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Type</Label>
                <Select value={txnForm.transaction_type} onValueChange={(v) => setTxnForm(prev => ({ ...prev, transaction_type: v }))}>
                  <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                    <SelectItem value="CREDIT" className="text-[#1AFFE4]">Credit (Money In)</SelectItem>
                    <SelectItem value="DEBIT" className="text-[#FF3B2F]">Debit (Money Out)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">Description *</Label>
              <Input
                value={txnForm.description}
                onChange={(e) => setTxnForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Transaction description"
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Amount *</Label>
                <Input
                  type="number"
                  value={txnForm.amount}
                  onChange={(e) => setTxnForm(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Category</Label>
                <Select value={txnForm.category} onValueChange={(v) => setTxnForm(prev => ({ ...prev, category: v }))}>
                  <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                    {transactionCategories.map(c => <SelectItem key={c.value} value={c.value} className="text-[#F4F6F0]">{c.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">Reference Number</Label>
              <Input
                value={txnForm.reference_number}
                onChange={(e) => setTxnForm(prev => ({ ...prev, reference_number: e.target.value }))}
                placeholder="UTR/Cheque/Reference #"
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddTransaction(false)} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
              Cancel
            </Button>
            <Button onClick={handleAddTransaction} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00]">
              Add Transaction
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Transfer Dialog */}
      <Dialog open={showTransferDialog} onOpenChange={setShowTransferDialog}>
        <DialogContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ArrowRightLeft className="w-5 h-5 text-[#FFB300]" />
              Transfer Between Accounts
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">From Account</Label>
              <Select value={transferForm.from_account_id} onValueChange={(v) => setTransferForm(prev => ({ ...prev, from_account_id: v }))}>
                <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                  <SelectValue placeholder="Select source account" />
                </SelectTrigger>
                <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                  {summary.accounts?.map(acc => (
                    <SelectItem key={acc.account_id} value={acc.account_id} className="text-[#F4F6F0]">
                      {acc.account_name} ({formatCurrency(acc.current_balance)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">To Account</Label>
              <Select value={transferForm.to_account_id} onValueChange={(v) => setTransferForm(prev => ({ ...prev, to_account_id: v }))}>
                <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                  <SelectValue placeholder="Select destination account" />
                </SelectTrigger>
                <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                  {summary.accounts?.filter(a => a.account_id !== transferForm.from_account_id).map(acc => (
                    <SelectItem key={acc.account_id} value={acc.account_id} className="text-[#F4F6F0]">
                      {acc.account_name} ({formatCurrency(acc.current_balance)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Amount</Label>
                <Input
                  type="number"
                  value={transferForm.amount}
                  onChange={(e) => setTransferForm(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Date</Label>
                <Input
                  type="date"
                  value={transferForm.transfer_date}
                  onChange={(e) => setTransferForm(prev => ({ ...prev, transfer_date: e.target.value }))}
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
            </div>
            
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">Reference</Label>
              <Input
                value={transferForm.reference}
                onChange={(e) => setTransferForm(prev => ({ ...prev, reference: e.target.value }))}
                placeholder="Transfer reference"
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTransferDialog(false)} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
              Cancel
            </Button>
            <Button onClick={handleTransfer} className="bg-[#FFB300] text-black hover:bg-[#E5A000]">
              Transfer Funds
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
