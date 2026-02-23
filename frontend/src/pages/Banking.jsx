import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Plus, Building, CreditCard, Wallet, ArrowUpRight, ArrowDownLeft,
  Calendar, IndianRupee, TrendingUp, TrendingDown, Save
} from "lucide-react";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

export default function Banking() {
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [showAccountDialog, setShowAccountDialog] = useState(false);
  const [showTxnDialog, setShowTxnDialog] = useState(false);

  const initialAccountData = {
    account_name: "",
    account_type: "bank",
    account_number: "",
    bank_name: "",
    opening_balance: 0
  };

  const initialTxnData = {
    account_id: "",
    amount: 0,
    transaction_type: "deposit",
    reference_number: "",
    description: "",
    payee: ""
  };

  const [newAccount, setNewAccount] = useState(initialAccountData);
  const [newTxn, setNewTxn] = useState(initialTxnData);

  // Auto-save for Account form
  const accountPersistence = useFormPersistence(
    'banking_account_new',
    newAccount,
    initialAccountData,
    {
      enabled: showAccountDialog,
      isDialogOpen: showAccountDialog,
      setFormData: setNewAccount,
      debounceMs: 2000,
      entityName: 'Bank Account'
    }
  );

  // Auto-save for Transaction form
  const txnPersistence = useFormPersistence(
    'banking_txn_new',
    newTxn,
    initialTxnData,
    {
      enabled: showTxnDialog,
      isDialogOpen: showTxnDialog,
      setFormData: setNewTxn,
      debounceMs: 2000,
      entityName: 'Transaction'
    }
  );

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [accRes, txnRes] = await Promise.all([
        fetch(`${API}/zoho/bankaccounts`, { headers }),
        fetch(`${API}/zoho/banktransactions?per_page=100`, { headers })
      ]);
      const [accData, txnData] = await Promise.all([
        accRes.json(), txnRes.json()
      ]);
      setAccounts(accData.bankaccounts || []);
      setTransactions(txnData.transactions || []);
    } catch (error) {
      console.error("Failed to fetch:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = async () => {
    if (!newAccount.account_name) return toast.error("Enter account name");
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/bankaccounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newAccount)
      });
      if (res.ok) {
        toast.success("Account created");
        accountPersistence.onSuccessfulSave();
        setShowAccountDialog(false);
        setNewAccount(initialAccountData);
        fetchData();
      }
    } catch { toast.error("Error creating account"); }
  };

  const handleCreateTransaction = async () => {
    if (!newTxn.account_id || newTxn.amount <= 0) return toast.error("Select account and enter amount");
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/banktransactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newTxn)
      });
      if (res.ok) {
        toast.success("Transaction recorded");
        txnPersistence.onSuccessfulSave();
        setShowTxnDialog(false);
        setNewTxn(initialTxnData);
        fetchData();
      }
    } catch { toast.error("Error recording transaction"); }
  };

  const totalBalance = accounts.reduce((sum, acc) => sum + (acc.balance || 0), 0);
  const accountTxns = selectedAccount 
    ? transactions.filter(t => t.account_id === selectedAccount.account_id)
    : transactions;

  const accountTypeIcons = {
    bank: Building,
    credit_card: CreditCard,
    cash: Wallet,
    payment_gateway: IndianRupee
  };

  return (
    <div className="space-y-6" data-testid="banking-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Banking</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Bank accounts & transactions</p>
        </div>
        <div className="flex gap-2">
          <Dialog 
            open={showAccountDialog} 
            onOpenChange={(open) => {
              if (!open && accountPersistence.isDirty) {
                accountPersistence.setShowCloseConfirm(true);
              } else {
                if (!open) accountPersistence.clearSavedData();
                setShowAccountDialog(open);
              }
            }}
          >
            <DialogTrigger asChild>
              <Button variant="outline" data-testid="add-account-btn">
                <Building className="h-4 w-4 mr-2" /> Add Account
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <DialogTitle>Add Bank Account</DialogTitle>
                  <AutoSaveIndicator 
                    lastSaved={accountPersistence.lastSaved} 
                    isSaving={accountPersistence.isSaving} 
                    isDirty={accountPersistence.isDirty} 
                  />
                </div>
              </DialogHeader>
              
              <DraftRecoveryBanner
                show={accountPersistence.showRecoveryBanner}
                savedAt={accountPersistence.savedDraftInfo?.timestamp}
                onRestore={accountPersistence.handleRestoreDraft}
                onDiscard={accountPersistence.handleDiscardDraft}
              />
              
              <div className="space-y-4 py-4">
                <div>
                  <Label>Account Name *</Label>
                  <Input value={newAccount.account_name} onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })} placeholder="Main Business Account" />
                </div>
                <div>
                  <Label>Account Type</Label>
                  <Select value={newAccount.account_type} onValueChange={(v) => setNewAccount({ ...newAccount, account_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="bank">Bank Account</SelectItem>
                      <SelectItem value="credit_card">Credit Card</SelectItem>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="payment_gateway">Payment Gateway</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Bank Name</Label>
                  <Input value={newAccount.bank_name} onChange={(e) => setNewAccount({ ...newAccount, bank_name: e.target.value })} placeholder="HDFC Bank" />
                </div>
                <div>
                  <Label>Account Number</Label>
                  <Input value={newAccount.account_number} onChange={(e) => setNewAccount({ ...newAccount, account_number: e.target.value })} placeholder="XXXX1234" />
                </div>
                <div>
                  <Label>Opening Balance</Label>
                  <Input type="number" value={newAccount.opening_balance} onChange={(e) => setNewAccount({ ...newAccount, opening_balance: parseFloat(e.target.value) })} />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    if (accountPersistence.isDirty) {
                      accountPersistence.setShowCloseConfirm(true);
                    } else {
                      setShowAccountDialog(false);
                    }
                  }}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateAccount} className="bg-[#C8FF00] text-[#080C0F] font-bold">Add Account</Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog 
            open={showTxnDialog} 
            onOpenChange={(open) => {
              if (!open && txnPersistence.isDirty) {
                txnPersistence.setShowCloseConfirm(true);
              } else {
                if (!open) txnPersistence.clearSavedData();
                setShowTxnDialog(open);
              }
            }}
          >
            <DialogTrigger asChild>
              <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="add-txn-btn">
                <Plus className="h-4 w-4 mr-2" /> Add Transaction
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <DialogTitle>Record Transaction</DialogTitle>
                  <AutoSaveIndicator 
                    lastSaved={txnPersistence.lastSaved} 
                    isSaving={txnPersistence.isSaving} 
                    isDirty={txnPersistence.isDirty} 
                  />
                </div>
              </DialogHeader>
              
              <DraftRecoveryBanner
                show={txnPersistence.showRecoveryBanner}
                savedAt={txnPersistence.savedDraftInfo?.timestamp}
                onRestore={txnPersistence.handleRestoreDraft}
                onDiscard={txnPersistence.handleDiscardDraft}
              />
              
              <div className="space-y-4 py-4">
                <div>
                  <Label>Account *</Label>
                  <Select value={newTxn.account_id} onValueChange={(v) => setNewTxn({ ...newTxn, account_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                    <SelectContent>
                      {accounts.map(acc => <SelectItem key={acc.account_id} value={acc.account_id}>{acc.account_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Type</Label>
                  <Select value={newTxn.transaction_type} onValueChange={(v) => setNewTxn({ ...newTxn, transaction_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="deposit">Deposit (Money In)</SelectItem>
                      <SelectItem value="withdrawal">Withdrawal (Money Out)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Amount *</Label>
                  <Input type="number" value={newTxn.amount} onChange={(e) => setNewTxn({ ...newTxn, amount: parseFloat(e.target.value) })} />
                </div>
                <div>
                  <Label>Payee/Payer</Label>
                  <Input value={newTxn.payee} onChange={(e) => setNewTxn({ ...newTxn, payee: e.target.value })} placeholder="Customer/Vendor name" />
                </div>
                <div>
                  <Label>Reference Number</Label>
                  <Input value={newTxn.reference_number} onChange={(e) => setNewTxn({ ...newTxn, reference_number: e.target.value })} placeholder="Transaction ID" />
                </div>
                <div>
                  <Label>Description</Label>
                  <Input value={newTxn.description} onChange={(e) => setNewTxn({ ...newTxn, description: e.target.value })} placeholder="Payment for..." />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    if (txnPersistence.isDirty) {
                      txnPersistence.setShowCloseConfirm(true);
                    } else {
                      setShowTxnDialog(false);
                    }
                  }}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateTransaction} className="bg-[#C8FF00] text-[#080C0F] font-bold">Record Transaction</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      
      {/* Unsaved Changes Confirmation Dialogs */}
      <FormCloseConfirmDialog
        open={accountPersistence.showCloseConfirm}
        onClose={() => accountPersistence.setShowCloseConfirm(false)}
        onSave={handleCreateAccount}
        onDiscard={() => {
          accountPersistence.clearSavedData();
          setNewAccount(initialAccountData);
          setShowAccountDialog(false);
        }}
        entityName="Bank Account"
      />
      
      <FormCloseConfirmDialog
        open={txnPersistence.showCloseConfirm}
        onClose={() => txnPersistence.setShowCloseConfirm(false)}
        onSave={handleCreateTransaction}
        onDiscard={() => {
          txnPersistence.clearSavedData();
          setNewTxn(initialTxnData);
          setShowTxnDialog(false);
        }}
        entityName="Transaction"
      />

      {/* Summary Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Balance</p>
              <p className="text-3xl font-bold text-[#F4F6F0]">₹{totalBalance.toLocaleString('en-IN')}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-[rgba(244,246,240,0.45)]">{accounts.length} Accounts</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Accounts List */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-[#F4F6F0]">Accounts</h2>
          <Button 
            variant={selectedAccount === null ? "default" : "outline"} 
            className={`w-full justify-start ${selectedAccount === null ? "bg-[#C8FF00] text-[#080C0F] font-bold" : ""}`}
            onClick={() => setSelectedAccount(null)}
          >
            All Accounts
          </Button>
          {accounts.map(acc => {
            const Icon = accountTypeIcons[acc.account_type] || Building;
            return (
              <Card 
                key={acc.account_id} 
                className={`cursor-pointer transition-colors ${selectedAccount?.account_id === acc.account_id ? "ring-2 ring-[#C8FF00]" : ""}`}
                onClick={() => setSelectedAccount(acc)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[rgba(255,255,255,0.05)] rounded-lg">
                      <Icon className="h-5 w-5 text-[rgba(244,246,240,0.35)]" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium">{acc.account_name}</h3>
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">{acc.bank_name || acc.account_type}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold">₹{acc.balance?.toLocaleString('en-IN')}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Transactions */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-lg font-semibold text-[#F4F6F0]">
            Transactions {selectedAccount && `- ${selectedAccount.account_name}`}
          </h2>
          {loading ? <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</div> :
            accountTxns.length === 0 ? <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No transactions found</CardContent></Card> :
            <div className="space-y-2">
              {accountTxns.map(txn => (
                <Card key={txn.transaction_id} className="hover:shadow-sm transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${txn.transaction_type === 'deposit' ? 'bg-green-100' : 'bg-red-100'}`}>
                          {txn.transaction_type === 'deposit' 
                            ? <ArrowDownLeft className="h-4 w-4 text-green-600" />
                            : <ArrowUpRight className="h-4 w-4 text-red-600" />
                          }
                        </div>
                        <div>
                          <p className="font-medium">{txn.payee || txn.description || 'Transaction'}</p>
                          <div className="flex gap-2 text-xs text-[rgba(244,246,240,0.45)]">
                            <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{txn.date}</span>
                            {txn.reference_number && <span>Ref: {txn.reference_number}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold ${txn.transaction_type === 'deposit' ? 'text-green-600' : 'text-red-600'}`}>
                          {txn.transaction_type === 'deposit' ? '+' : '-'}₹{txn.amount?.toLocaleString('en-IN')}
                        </p>
                        <Badge variant="outline" className="text-xs">{txn.status}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          }
        </div>
      </div>
    </div>
  );
}
