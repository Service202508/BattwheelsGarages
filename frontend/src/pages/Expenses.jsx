import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Plus, Receipt, Download, Search, Calendar, Building2, 
  CheckCircle2, XCircle, Clock, CreditCard, Banknote,
  FileText, AlertCircle, ChevronRight, Upload, Eye
} from "lucide-react";
import { API } from "@/App";

const statusConfig = {
  DRAFT: { label: "Draft", bg: "bg-bw-white/10", text: "text-bw-white/[0.65]" },
  SUBMITTED: { label: "Submitted", bg: "bg-bw-blue/10", text: "text-bw-blue" },
  APPROVED: { label: "Approved", bg: "bg-bw-volt/10", text: "text-bw-volt" },
  REJECTED: { label: "Rejected", bg: "bg-bw-red/10", text: "text-bw-red" },
  PAID: { label: "Paid", bg: "bg-bw-teal/10", text: "text-bw-teal" }
};

const paymentModes = [
  { value: "PENDING", label: "Pending" },
  { value: "CASH", label: "Cash" },
  { value: "BANK", label: "Bank Transfer" },
  { value: "CREDIT_CARD", label: "Credit Card" },
  { value: "UPI", label: "UPI" }
];

const gstRates = [0, 5, 12, 18, 28];

const getHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token")}`
});

export default function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showPayDialog, setShowPayDialog] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [paymentMode, setPaymentMode] = useState("BANK");
  
  // Form state
  const [formData, setFormData] = useState({
    expense_date: new Date().toISOString().split("T")[0],
    vendor_name: "",
    description: "",
    amount: 0,
    category_id: "",
    vendor_gstin: "",
    gst_rate: 18,
    is_igst: false,
    hsn_sac_code: "",
    payment_mode: "PENDING",
    notes: "",
    receipt_url: ""
  });
  
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchExpenses();
    fetchCategories();
    fetchSummary();
  }, [activeTab, dateFrom, dateTo]);

  const fetchExpenses = async () => {
    try {
      let url = `${API}/expenses?limit=100`;
      if (activeTab !== "all") url += `&status=${activeTab.toUpperCase()}`;
      if (dateFrom) url += `&date_from=${dateFrom}`;
      if (dateTo) url += `&date_to=${dateTo}`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      
      const res = await fetch(url, { headers: getHeaders() });
      const data = await res.json();
      setExpenses(data.expenses || []);
    } catch (err) {
      console.error("Failed to fetch expenses:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API}/expenses/categories`, { headers: getHeaders() });
      const data = await res.json();
      setCategories(data.categories || []);
    } catch (err) {
      console.error("Failed to fetch categories:", err);
    }
  };

  const fetchSummary = async () => {
    try {
      let url = `${API}/expenses/summary`;
      if (dateFrom) url += `?date_from=${dateFrom}`;
      if (dateTo) url += `${dateFrom ? '&' : '?'}date_to=${dateTo}`;
      
      const res = await fetch(url, { headers: getHeaders() });
      const data = await res.json();
      setSummary(data.summary || {});
    } catch (err) {
      console.error("Failed to fetch summary:", err);
    }
  };

  // Calculate GST amounts
  const gstCalculation = useMemo(() => {
    const base = parseFloat(formData.amount) || 0;
    const rate = formData.gst_rate / 100;
    
    let cgst = 0, sgst = 0, igst = 0;
    if (formData.is_igst) {
      igst = base * rate;
    } else {
      cgst = base * (rate / 2);
      sgst = base * (rate / 2);
    }
    
    return {
      base: base.toFixed(2),
      cgst: cgst.toFixed(2),
      sgst: sgst.toFixed(2),
      igst: igst.toFixed(2),
      total: (base + cgst + sgst + igst).toFixed(2)
    };
  }, [formData.amount, formData.gst_rate, formData.is_igst]);

  // Check GSTIN validity
  const isValidGstin = useMemo(() => {
    if (!formData.vendor_gstin) return null;
    const pattern = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/;
    return pattern.test(formData.vendor_gstin.toUpperCase());
  }, [formData.vendor_gstin]);

  const handleCreateExpense = async (submitForApproval = false) => {
    if (!formData.description || !formData.amount || !formData.category_id) {
      return toast.error("Please fill required fields");
    }
    
    try {
      const method = isEditing ? "PUT" : "POST";
      const url = isEditing ? `${API}/expenses/${selectedExpense.expense_id}` : `${API}/expenses`;
      
      const res = await fetch(url, {
        method,
        headers: getHeaders(),
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(isEditing ? "Expense updated" : "Expense created");
        
        // Submit for approval if requested
        if (submitForApproval && !isEditing) {
          await fetch(`${API}/expenses/${data.expense.expense_id}/submit`, {
            method: "POST",
            headers: getHeaders()
          });
          toast.success("Expense submitted for approval");
        }
        
        setShowCreateDialog(false);
        resetForm();
        fetchExpenses();
        fetchSummary();
      } else {
        toast.error(data.detail || "Failed to save expense");
      }
    } catch (err) {
      toast.error("Error saving expense");
    }
  };

  const handleSubmit = async (expense) => {
    try {
      const res = await fetch(`${API}/expenses/${expense.expense_id}/submit`, {
        method: "POST",
        headers: getHeaders()
      });
      
      if (res.ok) {
        toast.success("Expense submitted for approval");
        fetchExpenses();
        fetchSummary();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to submit");
      }
    } catch (err) {
      toast.error("Error submitting expense");
    }
  };

  const handleApprove = async (expense) => {
    try {
      const res = await fetch(`${API}/expenses/${expense.expense_id}/approve`, {
        method: "POST",
        headers: getHeaders()
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success("Expense approved");
        if (data.journal_entry_id) {
          toast.success("Journal entry posted");
        }
        fetchExpenses();
        fetchSummary();
        setShowDetailDialog(false);
      } else {
        toast.error(data.detail || "Failed to approve");
      }
    } catch (err) {
      toast.error("Error approving expense");
    }
  };

  const handleReject = async () => {
    if (!rejectReason) return toast.error("Please provide a reason");
    
    try {
      const res = await fetch(`${API}/expenses/${selectedExpense.expense_id}/reject`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ reason: rejectReason })
      });
      
      if (res.ok) {
        toast.success("Expense rejected");
        setShowRejectDialog(false);
        setShowDetailDialog(false);
        setRejectReason("");
        fetchExpenses();
        fetchSummary();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to reject");
      }
    } catch (err) {
      toast.error("Error rejecting expense");
    }
  };

  const handleMarkPaid = async () => {
    try {
      const res = await fetch(`${API}/expenses/${selectedExpense.expense_id}/mark-paid`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ payment_mode: paymentMode })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Expense marked as paid via ${paymentMode}`);
        setShowPayDialog(false);
        setShowDetailDialog(false);
        fetchExpenses();
        fetchSummary();
      } else {
        toast.error(data.detail || "Failed to mark as paid");
      }
    } catch (err) {
      toast.error("Error marking as paid");
    }
  };

  const handleDelete = async (expense) => {
    if (!confirm("Delete this expense?")) return;
    
    try {
      const res = await fetch(`${API}/expenses/${expense.expense_id}`, {
        method: "DELETE",
        headers: getHeaders()
      });
      
      if (res.ok) {
        toast.success("Expense deleted");
        fetchExpenses();
        fetchSummary();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to delete");
      }
    } catch (err) {
      toast.error("Error deleting expense");
    }
  };

  const handleExport = async () => {
    try {
      let url = `${API}/expenses/export?`;
      if (activeTab !== "all") url += `status=${activeTab.toUpperCase()}&`;
      if (dateFrom) url += `date_from=${dateFrom}&`;
      if (dateTo) url += `date_to=${dateTo}`;
      
      const res = await fetch(url, { headers: getHeaders() });
      
      if (res.ok) {
        const blob = await res.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `expenses_${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(downloadUrl);
        toast.success("Expenses exported");
      }
    } catch (err) {
      toast.error("Error exporting expenses");
    }
  };

  const resetForm = () => {
    setFormData({
      expense_date: new Date().toISOString().split("T")[0],
      vendor_name: "",
      description: "",
      amount: 0,
      category_id: "",
      vendor_gstin: "",
      gst_rate: 18,
      is_igst: false,
      hsn_sac_code: "",
      payment_mode: "PENDING",
      notes: "",
      receipt_url: ""
    });
    setIsEditing(false);
    setSelectedExpense(null);
  };

  const openEdit = (expense) => {
    setFormData({
      expense_date: expense.expense_date,
      vendor_name: expense.vendor_name || "",
      description: expense.description || "",
      amount: expense.amount || 0,
      category_id: expense.category_id || "",
      vendor_gstin: expense.vendor_gstin || "",
      gst_rate: expense.gst_rate || 18,
      is_igst: expense.is_igst || false,
      hsn_sac_code: expense.hsn_sac_code || "",
      payment_mode: expense.payment_mode || "PENDING",
      notes: expense.notes || "",
      receipt_url: expense.receipt_url || ""
    });
    setSelectedExpense(expense);
    setIsEditing(true);
    setShowCreateDialog(true);
  };

  const openDetail = (expense) => {
    setSelectedExpense(expense);
    setShowDetailDialog(true);
  };

  // Stats calculations
  const stats = useMemo(() => {
    const byStatus = summary.by_status || {};
    const itc = summary.itc_summary || {};
    
    const thisMonth = new Date().toISOString().slice(0, 7);
    const monthlyData = (summary.by_month || []).find(m => m.month === thisMonth);
    
    return {
      totalThisMonth: monthlyData?.total || 0,
      pendingCount: (byStatus.SUBMITTED?.count || 0),
      approvedThisMonth: (byStatus.APPROVED?.total || 0) + (byStatus.PAID?.total || 0),
      itcAmount: itc.total_itc || 0,
      rejectedCount: byStatus.REJECTED?.count || 0
    };
  }, [summary]);

  return (
    <div className="space-y-6" data-testid="expenses-page">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-bw-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
            Expenses
          </h1>
          <p className="text-bw-white/[0.45] text-sm mt-1">
            Record, approve and track business expenditure
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={(open) => { setShowCreateDialog(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold" data-testid="new-expense-btn">
              <Plus className="h-4 w-4 mr-2" /> New Expense
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{isEditing ? "Edit Expense" : "New Expense"}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Expense Date *</Label>
                  <Input type="date" value={formData.expense_date} onChange={(e) => setFormData({...formData, expense_date: e.target.value})} />
                </div>
                <div>
                  <Label>Category *</Label>
                  <Select value={formData.category_id} onValueChange={(v) => setFormData({...formData, category_id: v})}>
                    <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                    <SelectContent>
                      {categories.map(c => (
                        <SelectItem key={c.category_id} value={c.category_id}>
                          {c.name} {c.is_itc_eligible && <span className="text-bw-teal">(ITC)</span>}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <Label>Description *</Label>
                <Input value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} placeholder="What was this expense for?" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Vendor Name</Label>
                  <Input value={formData.vendor_name} onChange={(e) => setFormData({...formData, vendor_name: e.target.value})} placeholder="Vendor/Supplier name" />
                </div>
                <div>
                  <Label>Vendor GSTIN</Label>
                  <Input 
                    value={formData.vendor_gstin} 
                    onChange={(e) => setFormData({...formData, vendor_gstin: e.target.value.toUpperCase()})} 
                    placeholder="e.g., 27AABCU9603R1ZM"
                    className={isValidGstin === false ? "border-bw-red" : isValidGstin ? "border-bw-volt" : ""}
                  />
                  {isValidGstin && (
                    <p className="text-xs text-bw-teal mt-1">ITC eligible - GST amounts will be tracked for input credit</p>
                  )}
                  {isValidGstin === false && formData.vendor_gstin && (
                    <p className="text-xs text-bw-red mt-1">Invalid GSTIN format</p>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Base Amount (₹) *</Label>
                  <Input type="number" value={formData.amount} onChange={(e) => setFormData({...formData, amount: parseFloat(e.target.value) || 0})} min={0} step={0.01} />
                </div>
                <div>
                  <Label>GST Rate</Label>
                  <Select value={String(formData.gst_rate)} onValueChange={(v) => setFormData({...formData, gst_rate: parseInt(v)})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {gstRates.map(r => <SelectItem key={r} value={String(r)}>{r}%</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Tax Type</Label>
                  <Select value={formData.is_igst ? "igst" : "cgst_sgst"} onValueChange={(v) => setFormData({...formData, is_igst: v === "igst"})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cgst_sgst">CGST + SGST (Same State)</SelectItem>
                      <SelectItem value="igst">IGST (Inter-State)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {/* GST Calculation Preview */}
              <div className="bg-bw-card p-4 rounded-lg border border-white/[0.07]">
                <div className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">Base Amount:</span>
                    <span>₹{gstCalculation.base}</span>
                  </div>
                  {formData.is_igst ? (
                    <div className="flex justify-between">
                      <span className="text-bw-white/[0.45]">IGST ({formData.gst_rate}%):</span>
                      <span>₹{gstCalculation.igst}</span>
                    </div>
                  ) : (
                    <>
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.45]">CGST ({formData.gst_rate/2}%):</span>
                        <span>₹{gstCalculation.cgst}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.45]">SGST ({formData.gst_rate/2}%):</span>
                        <span>₹{gstCalculation.sgst}</span>
                      </div>
                    </>
                  )}
                  <div className="flex justify-between border-t border-white/[0.07] pt-2 mt-2">
                    <span className="font-medium">Total:</span>
                    <span className="font-bold text-bw-volt">₹{gstCalculation.total}</span>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>HSN/SAC Code</Label>
                  <Input value={formData.hsn_sac_code} onChange={(e) => setFormData({...formData, hsn_sac_code: e.target.value})} placeholder="Optional" />
                </div>
                <div>
                  <Label>Payment Mode</Label>
                  <Select value={formData.payment_mode} onValueChange={(v) => setFormData({...formData, payment_mode: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {paymentModes.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} placeholder="Additional notes..." />
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => { setShowCreateDialog(false); resetForm(); }}>Cancel</Button>
              <Button variant="outline" onClick={() => handleCreateExpense(false)}>Save as Draft</Button>
              {!isEditing && (
                <Button onClick={() => handleCreateExpense(true)} className="bg-bw-volt text-bw-black font-bold">
                  Save & Submit
                </Button>
              )}
              {isEditing && (
                <Button onClick={() => handleCreateExpense(false)} className="bg-bw-volt text-bw-black font-bold">
                  Save Changes
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Strip */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Total This Month</div>
            <div className="text-2xl font-bold text-bw-volt" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              ₹{stats.totalThisMonth.toLocaleString('en-IN')}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Pending Approval</div>
            <div className="text-2xl font-bold text-bw-orange" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {stats.pendingCount}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Approved This Month</div>
            <div className="text-2xl font-bold text-bw-teal" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              ₹{stats.approvedThisMonth.toLocaleString('en-IN')}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">ITC Eligible</div>
            <div className="text-2xl font-bold text-bw-teal" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              ₹{stats.itcAmount.toLocaleString('en-IN')}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Rejected</div>
            <div className="text-2xl font-bold text-bw-red" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {stats.rejectedCount}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-shrink-0">
          <TabsList className="bg-bw-panel border border-white/[0.07]">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="draft">Draft</TabsTrigger>
            <TabsTrigger value="submitted">Submitted</TabsTrigger>
            <TabsTrigger value="approved">Approved</TabsTrigger>
            <TabsTrigger value="rejected">Rejected</TabsTrigger>
            <TabsTrigger value="paid">Paid</TabsTrigger>
          </TabsList>
        </Tabs>
        
        <div className="flex items-center gap-2">
          <Input 
            type="date" 
            value={dateFrom} 
            onChange={(e) => setDateFrom(e.target.value)} 
            className="w-36"
            placeholder="From"
          />
          <span className="text-bw-white/[0.45]">to</span>
          <Input 
            type="date" 
            value={dateTo} 
            onChange={(e) => setDateTo(e.target.value)} 
            className="w-36"
          />
        </div>
        
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-bw-white/35" />
          <Input 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
            onKeyDown={(e) => e.key === 'Enter' && fetchExpenses()}
            placeholder="Search expenses..."
            className="pl-9"
          />
        </div>
        
        <Button variant="outline" onClick={handleExport}>
          <Download className="h-4 w-4 mr-2" /> Export CSV
        </Button>
      </div>

      {/* Expenses Table */}
      <Card className="bg-bw-panel border-white/[0.07]">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.07]">
                  <th className="text-left p-3 text-xs text-bw-white/[0.45]">Expense No.</th>
                  <th className="text-left p-3 text-xs text-bw-white/[0.45]">Date</th>
                  <th className="text-left p-3 text-xs text-bw-white/[0.45]">Vendor</th>
                  <th className="text-left p-3 text-xs text-bw-white/[0.45]">Category</th>
                  <th className="text-left p-3 text-xs text-bw-white/[0.45]">Description</th>
                  <th className="text-right p-3 text-xs text-bw-white/[0.45]">Amount</th>
                  <th className="text-right p-3 text-xs text-bw-white/[0.45]">GST</th>
                  <th className="text-right p-3 text-xs text-bw-white/[0.45]">Total</th>
                  <th className="text-center p-3 text-xs text-bw-white/[0.45]">ITC</th>
                  <th className="text-center p-3 text-xs text-bw-white/[0.45]">Status</th>
                  <th className="text-right p-3 text-xs text-bw-white/[0.45]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={11} className="text-center py-8 text-bw-white/[0.45]">Loading...</td></tr>
                ) : expenses.length === 0 ? (
                  <tr><td colSpan={11} className="text-center py-8 text-bw-white/[0.45]">No expenses found</td></tr>
                ) : expenses.map(expense => {
                  const status = statusConfig[expense.status] || statusConfig.DRAFT;
                  const gstAmount = (expense.cgst_amount || 0) + (expense.sgst_amount || 0) + (expense.igst_amount || 0);
                  
                  return (
                    <tr key={expense.expense_id} className="border-b border-white/[0.07] hover:bg-white/[0.02]">
                      <td className="p-3">
                        <span className="font-mono text-sm text-bw-volt">{expense.expense_number}</span>
                      </td>
                      <td className="p-3">
                        <span className="font-mono text-sm text-bw-white/[0.65]">{expense.expense_date}</span>
                      </td>
                      <td className="p-3 text-sm">{expense.vendor_name || '-'}</td>
                      <td className="p-3">
                        <Badge variant="outline" className="text-xs">{expense.category_name || 'Unknown'}</Badge>
                      </td>
                      <td className="p-3 text-sm text-bw-white/[0.65] max-w-[200px] truncate">{expense.description}</td>
                      <td className="p-3 text-sm text-right font-mono">₹{expense.amount?.toLocaleString('en-IN')}</td>
                      <td className="p-3 text-sm text-right font-mono text-bw-white/[0.45]">₹{gstAmount.toLocaleString('en-IN')}</td>
                      <td className="p-3 text-sm text-right font-bold font-mono text-bw-volt">₹{expense.total_amount?.toLocaleString('en-IN')}</td>
                      <td className="p-3 text-center">
                        {expense.is_itc_eligible ? (
                          <Badge className="bg-bw-teal/10 text-bw-teal text-xs">ITC</Badge>
                        ) : (
                          <span className="text-xs text-bw-white/35">No ITC</span>
                        )}
                      </td>
                      <td className="p-3 text-center">
                        <Badge className={`${status.bg} ${status.text}`}>{status.label}</Badge>
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => openDetail(expense)}>
                            <Eye className="h-3 w-3" />
                          </Button>
                          {expense.status === 'DRAFT' && (
                            <>
                              <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => openEdit(expense)}>Edit</Button>
                              <Button size="sm" variant="ghost" className="h-7 text-xs text-bw-blue" onClick={() => handleSubmit(expense)}>Submit</Button>
                              <Button size="sm" variant="ghost" className="h-7 text-xs text-bw-red" onClick={() => handleDelete(expense)}>Delete</Button>
                            </>
                          )}
                          {expense.status === 'SUBMITTED' && (
                            <>
                              <Button size="sm" variant="ghost" className="h-7 text-xs text-bw-volt" onClick={() => handleApprove(expense)}>Approve</Button>
                              <Button size="sm" variant="ghost" className="h-7 text-xs text-bw-red" onClick={() => { setSelectedExpense(expense); setShowRejectDialog(true); }}>Reject</Button>
                            </>
                          )}
                          {expense.status === 'APPROVED' && (
                            <Button size="sm" variant="ghost" className="h-7 text-xs text-bw-teal" onClick={() => { setSelectedExpense(expense); setShowPayDialog(true); }}>Mark Paid</Button>
                          )}
                          {expense.status === 'REJECTED' && (
                            <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => openEdit(expense)}>Re-submit</Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Expense Details</DialogTitle>
          </DialogHeader>
          {selectedExpense && (
            <div className="space-y-4 py-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-mono text-lg text-bw-volt">{selectedExpense.expense_number}</p>
                  <p className="text-sm text-bw-white/[0.45]">{selectedExpense.expense_date}</p>
                </div>
                <Badge className={`${statusConfig[selectedExpense.status]?.bg} ${statusConfig[selectedExpense.status]?.text}`}>
                  {statusConfig[selectedExpense.status]?.label}
                </Badge>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-bw-white/[0.45]">Vendor</span>
                  <p className="font-medium">{selectedExpense.vendor_name || '-'}</p>
                </div>
                <div>
                  <span className="text-bw-white/[0.45]">GSTIN</span>
                  <p className="font-mono">{selectedExpense.vendor_gstin || '-'}</p>
                </div>
                <div>
                  <span className="text-bw-white/[0.45]">Category</span>
                  <p>{selectedExpense.category_name || 'Unknown'}</p>
                </div>
                <div>
                  <span className="text-bw-white/[0.45]">Payment Mode</span>
                  <p>{selectedExpense.payment_mode}</p>
                </div>
              </div>
              
              <div>
                <span className="text-bw-white/[0.45] text-sm">Description</span>
                <p>{selectedExpense.description}</p>
              </div>
              
              <div className="bg-bw-card p-4 rounded-lg">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">Base Amount:</span>
                    <span>₹{selectedExpense.amount?.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">GST Rate:</span>
                    <span>{selectedExpense.gst_rate}%</span>
                  </div>
                  {selectedExpense.is_igst ? (
                    <div className="flex justify-between">
                      <span className="text-bw-white/[0.45]">IGST:</span>
                      <span>₹{selectedExpense.igst_amount?.toLocaleString('en-IN')}</span>
                    </div>
                  ) : (
                    <>
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.45]">CGST:</span>
                        <span>₹{selectedExpense.cgst_amount?.toLocaleString('en-IN')}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.45]">SGST:</span>
                        <span>₹{selectedExpense.sgst_amount?.toLocaleString('en-IN')}</span>
                      </div>
                    </>
                  )}
                </div>
                <div className="flex justify-between border-t border-white/[0.07] pt-2 mt-2">
                  <span className="font-medium">Total:</span>
                  <span className="font-bold text-bw-volt">₹{selectedExpense.total_amount?.toLocaleString('en-IN')}</span>
                </div>
                {selectedExpense.is_itc_eligible && (
                  <div className="mt-2 text-xs text-bw-teal">
                    ITC Eligible - Input tax credit can be claimed
                  </div>
                )}
              </div>
              
              {selectedExpense.rejection_reason && (
                <div className="bg-bw-red/10 p-3 rounded text-sm">
                  <span className="text-bw-red font-medium">Rejection Reason:</span>
                  <p className="mt-1">{selectedExpense.rejection_reason}</p>
                </div>
              )}
              
              {selectedExpense.journal_entry_id && (
                <div className="text-xs text-bw-white/[0.45]">
                  Journal Entry: {selectedExpense.journal_entry_id}
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Close</Button>
            {selectedExpense?.status === 'SUBMITTED' && (
              <>
                <Button variant="outline" className="text-bw-red" onClick={() => setShowRejectDialog(true)}>Reject</Button>
                <Button onClick={() => handleApprove(selectedExpense)} className="bg-bw-volt text-bw-black">Approve</Button>
              </>
            )}
            {selectedExpense?.status === 'APPROVED' && (
              <Button onClick={() => setShowPayDialog(true)} className="bg-bw-teal text-bw-black">Mark Paid</Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reject Expense</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Label>Reason for Rejection *</Label>
            <Textarea 
              value={rejectReason} 
              onChange={(e) => setRejectReason(e.target.value)} 
              placeholder="Please provide a reason..."
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowRejectDialog(false); setRejectReason(""); }}>Cancel</Button>
            <Button onClick={handleReject} className="bg-bw-red text-white">Reject Expense</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Mark Paid Dialog */}
      <Dialog open={showPayDialog} onOpenChange={setShowPayDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Mark as Paid</DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div>
              <Label>Payment Mode</Label>
              <Select value={paymentMode} onValueChange={setPaymentMode}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="BANK">Bank Transfer</SelectItem>
                  <SelectItem value="CASH">Cash</SelectItem>
                  <SelectItem value="UPI">UPI</SelectItem>
                  <SelectItem value="CREDIT_CARD">Credit Card</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {selectedExpense && (
              <div className="bg-bw-card p-3 rounded text-sm">
                <div className="flex justify-between">
                  <span className="text-bw-white/[0.45]">Amount:</span>
                  <span className="font-bold">₹{selectedExpense.total_amount?.toLocaleString('en-IN')}</span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPayDialog(false)}>Cancel</Button>
            <Button onClick={handleMarkPaid} className="bg-bw-teal text-bw-black">Confirm Payment</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
