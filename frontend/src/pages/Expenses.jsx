import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { 
  Search, Plus, Receipt, Calendar, Building2, 
  IndianRupee, CreditCard, Wallet, TrendingDown, Save
} from "lucide-react";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const expenseCategories = [
  "Advertising And Marketing",
  "Automobile Expense",
  "Bank Fees and Charges", 
  "Consultant Expense",
  "Credit Card Charges",
  "Depreciation And Amortisation",
  "Employee Advance",
  "Fuel/Mileage Expenses",
  "IT and Internet Expenses",
  "Insurance",
  "Janitorial Expense",
  "Lodging",
  "Meals and Entertainment",
  "Office Supplies",
  "Other Expenses",
  "Postage",
  "Printing and Stationery",
  "Rent Expense",
  "Repairs and Maintenance",
  "Salaries and Employee Wages",
  "Telephone Expense",
  "Travel Expense",
  "Bad Debt"
];

const paymentMethods = [
  "Petty Cash",
  "Cash",
  "Kotak Mahindra Bank",
  "HDFC Bank",
  "ICICI Bank",
  "UPI"
];

export default function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [total, setTotal] = useState(0);
  const [expenseTotal, setExpenseTotal] = useState(0);

  const initialExpenseData = {
    expense_date: new Date().toISOString().split('T')[0],
    expense_account: "",
    amount: 0,
    paid_through: "Petty Cash",
    vendor_name: "",
    description: "",
    tax_rate: 0
  };

  const [newExpense, setNewExpense] = useState(initialExpenseData);

  // Auto-save for Expense form
  const expensePersistence = useFormPersistence(
    'expense_new',
    newExpense,
    initialExpenseData,
    {
      enabled: showAddDialog,
      isDialogOpen: showAddDialog,
      setFormData: setNewExpense,
      debounceMs: 2000,
      entityName: 'Expense'
    }
  );

  useEffect(() => { fetchExpenses(); }, [search]);

  const fetchExpenses = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/erp/expenses?expense_account=${search}&limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setExpenses(data.expenses || []);
      setTotal(data.total || 0);
      setExpenseTotal(data.expense_total || 0);
    } catch (error) {
      console.error("Failed to fetch expenses:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddExpense = async () => {
    if (!newExpense.expense_account) return toast.error("Select expense category");
    if (newExpense.amount <= 0) return toast.error("Enter valid amount");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/erp/expenses`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newExpense)
      });
      if (res.ok) {
        toast.success("Expense recorded");
        expensePersistence.onSuccessfulSave();
        setShowAddDialog(false);
        setNewExpense(initialExpenseData);
        fetchExpenses();
      }
    } catch { toast.error("Error recording expense"); }
  };

  // Group expenses by category
  const expensesByCategory = expenses.reduce((acc, exp) => {
    const cat = exp.expense_account || 'Other';
    if (!acc[cat]) acc[cat] = { total: 0, count: 0 };
    acc[cat].total += exp.amount || 0;
    acc[cat].count += 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6" data-testid="expenses-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Expenses</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">{total} expense records</p>
        </div>
        <Dialog 
          open={showAddDialog} 
          onOpenChange={(open) => {
            if (!open && expensePersistence.isDirty) {
              expensePersistence.setShowCloseConfirm(true);
            } else {
              if (!open) expensePersistence.clearSavedData();
              setShowAddDialog(open);
            }
          }}
        >
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
              <Plus className="h-4 w-4 mr-2" /> Record Expense
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <div className="flex items-center justify-between">
                <DialogTitle>Record Expense</DialogTitle>
                <AutoSaveIndicator 
                  lastSaved={expensePersistence.lastSaved} 
                  isSaving={expensePersistence.isSaving} 
                  isDirty={expensePersistence.isDirty} 
                />
              </div>
            </DialogHeader>
            
            <DraftRecoveryBanner
              show={expensePersistence.showRecoveryBanner}
              savedAt={expensePersistence.savedDraftInfo?.timestamp}
              onRestore={expensePersistence.handleRestoreDraft}
              onDiscard={expensePersistence.handleDiscardDraft}
            />
            
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Date</Label>
                  <Input type="date" value={newExpense.expense_date}
                    onChange={(e) => setNewExpense({...newExpense, expense_date: e.target.value})} />
                </div>
                <div>
                  <Label>Amount (₹) *</Label>
                  <Input type="number" value={newExpense.amount}
                    onChange={(e) => setNewExpense({...newExpense, amount: parseFloat(e.target.value)})} />
                </div>
              </div>
              <div>
                <Label>Expense Category *</Label>
                <Select value={newExpense.expense_account} onValueChange={(v) => setNewExpense({...newExpense, expense_account: v})}>
                  <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                  <SelectContent>
                    {expenseCategories.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Paid Through</Label>
                <Select value={newExpense.paid_through} onValueChange={(v) => setNewExpense({...newExpense, paid_through: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {paymentMethods.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Vendor/Payee</Label>
                <Input value={newExpense.vendor_name}
                  onChange={(e) => setNewExpense({...newExpense, vendor_name: e.target.value})}
                  placeholder="Who was this paid to?" />
              </div>
              <div>
                <Label>Description</Label>
                <Input value={newExpense.description}
                  onChange={(e) => setNewExpense({...newExpense, description: e.target.value})}
                  placeholder="What was this expense for?" />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  if (expensePersistence.isDirty) {
                    expensePersistence.setShowCloseConfirm(true);
                  } else {
                    setShowAddDialog(false);
                  }
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleAddExpense} className="bg-[#C8FF00] text-[#080C0F] font-bold">Record Expense</Button>
            </div>
          </DialogContent>
        </Dialog>
        
        {/* Unsaved Changes Confirmation Dialog */}
        <FormCloseConfirmDialog
          open={expensePersistence.showCloseConfirm}
          onClose={() => expensePersistence.setShowCloseConfirm(false)}
          onSave={handleAddExpense}
          onDiscard={() => {
            expensePersistence.clearSavedData();
            setNewExpense(initialExpenseData);
            setShowAddDialog(false);
          }}
          entityName="Expense"
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Expenses</p>
                <p className="text-2xl font-bold text-red-600">₹{expenseTotal.toLocaleString('en-IN')}</p>
              </div>
              <TrendingDown className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Records</p>
                <p className="text-2xl font-bold text-[#F4F6F0]">{total}</p>
              </div>
              <Receipt className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Categories</p>
                <p className="text-2xl font-bold text-[#F4F6F0]">{Object.keys(expensesByCategory).length}</p>
              </div>
              <Wallet className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Avg per Record</p>
                <p className="text-2xl font-bold text-[#F4F6F0]">₹{total > 0 ? Math.round(expenseTotal / total).toLocaleString('en-IN') : 0}</p>
              </div>
              <IndianRupee className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Breakdown */}
      <Card>
        <CardContent className="p-4">
          <h3 className="font-semibold mb-4">Expenses by Category</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(expensesByCategory).slice(0, 8).map(([cat, data]) => (
              <div key={cat} className="p-3 bg-[#111820] rounded-lg">
                <p className="text-xs text-[rgba(244,246,240,0.45)] truncate">{cat}</p>
                <p className="font-semibold text-red-600">₹{data.total.toLocaleString('en-IN')}</p>
                <p className="text-xs text-[rgba(244,246,240,0.45)]">{data.count} records</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
        <Input placeholder="Search by category..." value={search}
          onChange={(e) => setSearch(e.target.value)} className="pl-10" />
      </div>

      {/* Expense List */}
      {loading ? <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</div> :
        expenses.length === 0 ? <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No expenses found</CardContent></Card> :
        <div className="space-y-3">
          {expenses.map(exp => (
            <Card key={exp.expense_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold">{exp.expense_number}</h3>
                      <Badge variant="outline" className="text-xs">{exp.expense_account}</Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{exp.expense_date}</span>
                      {exp.vendor_name && <span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{exp.vendor_name}</span>}
                      <span className="flex items-center gap-1"><CreditCard className="h-3.5 w-3.5" />{exp.paid_through}</span>
                    </div>
                    {exp.description && <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">{exp.description}</p>}
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg text-red-600">₹{exp.amount?.toLocaleString('en-IN')}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      }
    </div>
  );
}
