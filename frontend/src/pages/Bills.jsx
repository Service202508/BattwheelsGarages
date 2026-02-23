import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Plus, Receipt, Download, Search, Calendar, Building2, 
  CheckCircle2, XCircle, Clock, CreditCard, Banknote,
  FileText, AlertCircle, ChevronRight, Trash2, Eye,
  IndianRupee, Users, ArrowUp, ArrowDown
} from "lucide-react";
import { API } from "@/App";

const statusConfig = {
  DRAFT: { label: "Draft", bg: "bg-[rgba(244,246,240,0.10)]", text: "text-[rgba(244,246,240,0.65)]" },
  RECEIVED: { label: "Received", bg: "bg-[rgba(59,158,255,0.10)]", text: "text-[#3B9EFF]" },
  APPROVED: { label: "Approved", bg: "bg-[rgba(200,255,0,0.10)]", text: "text-[#C8FF00]" },
  PARTIAL_PAID: { label: "Partial", bg: "bg-[rgba(255,179,0,0.10)]", text: "text-[#FFB300]" },
  PAID: { label: "Paid", bg: "bg-[rgba(26,255,228,0.10)]", text: "text-[#1AFFE4]" },
  OVERDUE: { label: "Overdue", bg: "bg-[rgba(255,59,47,0.10)]", text: "text-[#FF3B2F]" },
  CANCELLED: { label: "Cancelled", bg: "bg-[rgba(128,128,128,0.10)]", text: "text-gray-500" }
};

const paymentModes = [
  { value: "BANK", label: "Bank Transfer" },
  { value: "CASH", label: "Cash" },
  { value: "UPI", label: "UPI" },
  { value: "CHEQUE", label: "Cheque" }
];

const gstRates = [0, 5, 12, 18, 28];

const getHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token")}`
});

const formatCurrency = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val || 0);

export default function Bills() {
  const [bills, setBills] = useState([]);
  const [vendorAging, setVendorAging] = useState({ vendors: [], totals: {} });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showPayDialog, setShowPayDialog] = useState(false);
  const [selectedBill, setSelectedBill] = useState(null);
  
  // Payment form
  const [paymentData, setPaymentData] = useState({
    amount: 0,
    payment_date: new Date().toISOString().split("T")[0],
    payment_mode: "BANK",
    reference_number: ""
  });
  
  // Bill form
  const emptyLineItem = { description: "", quantity: 1, unit: "nos", rate: 0, gst_rate: 18, is_igst: false, account_code: "5000" };
  const [formData, setFormData] = useState({
    bill_number: "",
    vendor_id: "",
    vendor_name: "",
    vendor_gstin: "",
    bill_date: new Date().toISOString().split("T")[0],
    due_date: "",
    line_items: [{ ...emptyLineItem }],
    notes: ""
  });

  useEffect(() => {
    fetchBills();
    fetchVendorAging();
  }, [activeTab, dateFrom, dateTo]);

  const fetchBills = async () => {
    try {
      let url = `${API}/bills?limit=100`;
      if (activeTab !== "all") url += `&status=${activeTab.toUpperCase()}`;
      if (dateFrom) url += `&date_from=${dateFrom}`;
      if (dateTo) url += `&date_to=${dateTo}`;
      
      const res = await fetch(url, { headers: getHeaders() });
      const data = await res.json();
      setBills(data.bills || []);
    } catch (err) {
      console.error("Failed to fetch bills:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchVendorAging = async () => {
    try {
      const res = await fetch(`${API}/bills/aging/vendor`, { headers: getHeaders() });
      const data = await res.json();
      setVendorAging({ vendors: data.vendors || [], totals: data.totals || {} });
    } catch (err) {
      console.error("Failed to fetch vendor aging:", err);
    }
  };

  const fetchBillDetails = async (billId) => {
    try {
      const res = await fetch(`${API}/bills/${billId}`, { headers: getHeaders() });
      const data = await res.json();
      if (data.bill) {
        setSelectedBill(data.bill);
        setShowDetailDialog(true);
      }
    } catch (err) {
      console.error("Failed to fetch bill details:", err);
    }
  };

  // Calculate line item totals
  const calculateTotals = useMemo(() => {
    let subtotal = 0, cgst = 0, sgst = 0, igst = 0;
    
    formData.line_items.forEach(item => {
      const amount = (parseFloat(item.quantity) || 0) * (parseFloat(item.rate) || 0);
      const rate = (item.gst_rate || 0) / 100;
      
      subtotal += amount;
      if (item.is_igst) {
        igst += amount * rate;
      } else {
        cgst += amount * (rate / 2);
        sgst += amount * (rate / 2);
      }
    });
    
    return {
      subtotal: subtotal.toFixed(2),
      cgst: cgst.toFixed(2),
      sgst: sgst.toFixed(2),
      igst: igst.toFixed(2),
      total: (subtotal + cgst + sgst + igst).toFixed(2)
    };
  }, [formData.line_items]);

  const handleAddLineItem = () => {
    setFormData(prev => ({
      ...prev,
      line_items: [...prev.line_items, { ...emptyLineItem }]
    }));
  };

  const handleRemoveLineItem = (index) => {
    if (formData.line_items.length === 1) return;
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const handleLineItemChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const handleCreateBill = async () => {
    if (!formData.bill_number || !formData.vendor_name || formData.line_items.every(i => !i.description)) {
      return toast.error("Please fill required fields (Invoice #, Vendor, Line Items)");
    }
    
    try {
      const res = await fetch(`${API}/bills`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          ...formData,
          vendor_id: formData.vendor_id || `v_${Date.now()}`
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(`Bill ${data.bill.internal_ref} created`);
        setShowCreateDialog(false);
        resetForm();
        fetchBills();
        fetchVendorAging();
      } else {
        toast.error(data.detail || "Failed to create bill");
      }
    } catch (err) {
      toast.error("Error creating bill");
    }
  };

  const handleApprove = async (bill) => {
    try {
      const res = await fetch(`${API}/bills/${bill.bill_id}/approve`, {
        method: "POST",
        headers: getHeaders()
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success("Bill approved");
        if (data.journal_entry_id) {
          toast.success("Journal entry posted");
        }
        fetchBills();
        fetchVendorAging();
        setShowDetailDialog(false);
      } else {
        toast.error(data.detail || "Failed to approve");
      }
    } catch (err) {
      toast.error("Error approving bill");
    }
  };

  const handleRecordPayment = async () => {
    if (paymentData.amount <= 0) return toast.error("Enter valid amount");
    if (paymentData.amount > selectedBill.balance_due) return toast.error("Amount exceeds balance due");
    
    try {
      const res = await fetch(`${API}/bills/${selectedBill.bill_id}/record-payment`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(paymentData)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(data.message);
        setShowPayDialog(false);
        setShowDetailDialog(false);
        fetchBills();
        fetchVendorAging();
      } else {
        toast.error(data.detail || "Failed to record payment");
      }
    } catch (err) {
      toast.error("Error recording payment");
    }
  };

  const handleExport = async () => {
    try {
      let url = `${API}/bills/export?`;
      if (activeTab !== "all") url += `status=${activeTab.toUpperCase()}&`;
      if (dateFrom) url += `date_from=${dateFrom}&`;
      if (dateTo) url += `date_to=${dateTo}`;
      
      const res = await fetch(url, { headers: getHeaders() });
      
      if (res.ok) {
        const blob = await res.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `bills_${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(downloadUrl);
        toast.success("Bills exported");
      }
    } catch (err) {
      toast.error("Error exporting bills");
    }
  };

  const resetForm = () => {
    setFormData({
      bill_number: "",
      vendor_id: "",
      vendor_name: "",
      vendor_gstin: "",
      bill_date: new Date().toISOString().split("T")[0],
      due_date: "",
      line_items: [{ ...emptyLineItem }],
      notes: ""
    });
  };

  const filteredBills = useMemo(() => {
    if (!searchQuery) return bills;
    const q = searchQuery.toLowerCase();
    return bills.filter(b => 
      b.internal_ref?.toLowerCase().includes(q) ||
      b.bill_number?.toLowerCase().includes(q) ||
      b.vendor_name?.toLowerCase().includes(q)
    );
  }, [bills, searchQuery]);

  // Stats
  const stats = useMemo(() => {
    const total = bills.reduce((sum, b) => sum + (b.total_amount || 0), 0);
    const paid = bills.reduce((sum, b) => sum + (b.amount_paid || 0), 0);
    const pending = bills.filter(b => !["PAID", "CANCELLED"].includes(b.status)).length;
    const overdue = bills.filter(b => b.status === "OVERDUE" || (b.due_date < new Date().toISOString().split("T")[0] && b.status !== "PAID")).length;
    return { total, paid, pending, overdue };
  }, [bills]);

  return (
    <div data-testid="bills-page" className="min-h-screen bg-[#0B0B0F] text-[#F4F6F0] p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Vendor Bills</h1>
          <p className="text-sm text-[rgba(244,246,240,0.65)]">Manage vendor invoices and payments</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleExport} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0] hover:bg-[rgba(244,246,240,0.05)]">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button onClick={() => { resetForm(); setShowCreateDialog(true); }} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00]">
            <Plus className="w-4 h-4 mr-2" />
            New Bill
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Total Bills</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{formatCurrency(stats.total)}</p>
              </div>
              <Receipt className="w-8 h-8 text-[#3B9EFF]" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Paid</p>
                <p className="text-xl font-bold text-[#1AFFE4]">{formatCurrency(stats.paid)}</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-[#1AFFE4]" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Pending</p>
                <p className="text-xl font-bold text-[#FFB300]">{stats.pending}</p>
              </div>
              <Clock className="w-8 h-8 text-[#FFB300]" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Overdue</p>
                <p className="text-xl font-bold text-[#FF3B2F]">{stats.overdue}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-[#FF3B2F]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs and Filters */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full md:w-auto">
          <TabsList className="bg-[#14141B] border border-[rgba(244,246,240,0.08)]">
            <TabsTrigger value="all" className="data-[state=active]:bg-[#C8FF00] data-[state=active]:text-black">All</TabsTrigger>
            <TabsTrigger value="draft" className="data-[state=active]:bg-[#C8FF00] data-[state=active]:text-black">Draft</TabsTrigger>
            <TabsTrigger value="approved" className="data-[state=active]:bg-[#C8FF00] data-[state=active]:text-black">Approved</TabsTrigger>
            <TabsTrigger value="partial_paid" className="data-[state=active]:bg-[#C8FF00] data-[state=active]:text-black">Partial</TabsTrigger>
            <TabsTrigger value="paid" className="data-[state=active]:bg-[#C8FF00] data-[state=active]:text-black">Paid</TabsTrigger>
          </TabsList>
        </Tabs>
        
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(244,246,240,0.4)]" />
            <Input
              placeholder="Search bills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-[#14141B] border-[rgba(244,246,240,0.08)] text-[#F4F6F0] w-64"
            />
          </div>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="bg-[#14141B] border-[rgba(244,246,240,0.08)] text-[#F4F6F0] w-36"
          />
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="bg-[#14141B] border-[rgba(244,246,240,0.08)] text-[#F4F6F0] w-36"
          />
        </div>
      </div>

      {/* Bills Table */}
      <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[rgba(244,246,240,0.08)]">
                  <th className="text-left p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Ref #</th>
                  <th className="text-left p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Vendor Invoice</th>
                  <th className="text-left p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Vendor</th>
                  <th className="text-left p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Date</th>
                  <th className="text-left p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Due Date</th>
                  <th className="text-right p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Total</th>
                  <th className="text-right p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Balance</th>
                  <th className="text-center p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Status</th>
                  <th className="text-center p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={9} className="text-center p-8 text-[rgba(244,246,240,0.5)]">Loading...</td></tr>
                ) : filteredBills.length === 0 ? (
                  <tr><td colSpan={9} className="text-center p-8 text-[rgba(244,246,240,0.5)]">No bills found</td></tr>
                ) : (
                  filteredBills.map(bill => {
                    const config = statusConfig[bill.status] || statusConfig.DRAFT;
                    const isOverdue = bill.due_date < new Date().toISOString().split("T")[0] && !["PAID", "CANCELLED"].includes(bill.status);
                    return (
                      <tr key={bill.bill_id} className="border-b border-[rgba(244,246,240,0.05)] hover:bg-[rgba(244,246,240,0.02)] cursor-pointer" onClick={() => fetchBillDetails(bill.bill_id)}>
                        <td className="p-4 font-mono text-sm">{bill.internal_ref}</td>
                        <td className="p-4 text-sm">{bill.bill_number}</td>
                        <td className="p-4">
                          <p className="text-sm font-medium">{bill.vendor_name || "—"}</p>
                          {bill.vendor_gstin && <p className="text-xs text-[rgba(244,246,240,0.5)]">{bill.vendor_gstin}</p>}
                        </td>
                        <td className="p-4 text-sm">{bill.bill_date}</td>
                        <td className={`p-4 text-sm ${isOverdue ? 'text-[#FF3B2F]' : ''}`}>{bill.due_date}</td>
                        <td className="p-4 text-right font-mono">{formatCurrency(bill.total_amount)}</td>
                        <td className="p-4 text-right font-mono">{formatCurrency(bill.balance_due)}</td>
                        <td className="p-4 text-center">
                          <Badge className={`${config.bg} ${config.text} border-0`}>{config.label}</Badge>
                        </td>
                        <td className="p-4 text-center" onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="sm" onClick={() => fetchBillDetails(bill.bill_id)}>
                            <Eye className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Vendor Aging Report */}
      <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
        <CardHeader className="border-b border-[rgba(244,246,240,0.08)]">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Users className="w-5 h-5 text-[#3B9EFF]" />
            Vendor Aging Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[rgba(244,246,240,0.08)]">
                  <th className="text-left p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Vendor</th>
                  <th className="text-right p-4 text-xs font-medium text-[#1AFFE4] uppercase tracking-wide">Current</th>
                  <th className="text-right p-4 text-xs font-medium text-[#FFB300] uppercase tracking-wide">1-30 Days</th>
                  <th className="text-right p-4 text-xs font-medium text-[#FF8C00] uppercase tracking-wide">31-60 Days</th>
                  <th className="text-right p-4 text-xs font-medium text-[#FF5722] uppercase tracking-wide">61-90 Days</th>
                  <th className="text-right p-4 text-xs font-medium text-[#FF3B2F] uppercase tracking-wide">90+ Days</th>
                  <th className="text-right p-4 text-xs font-medium text-[rgba(244,246,240,0.5)] uppercase tracking-wide">Total</th>
                </tr>
              </thead>
              <tbody>
                {vendorAging.vendors.length === 0 ? (
                  <tr><td colSpan={7} className="text-center p-8 text-[rgba(244,246,240,0.5)]">No outstanding bills</td></tr>
                ) : (
                  <>
                    {vendorAging.vendors.map(v => (
                      <tr key={v.vendor_id} className="border-b border-[rgba(244,246,240,0.05)] hover:bg-[rgba(244,246,240,0.02)]">
                        <td className="p-4 text-sm font-medium">{v.vendor_name}</td>
                        <td className="p-4 text-right font-mono text-[#1AFFE4]">{v.current > 0 ? formatCurrency(v.current) : '—'}</td>
                        <td className="p-4 text-right font-mono text-[#FFB300]">{v.days_1_30 > 0 ? formatCurrency(v.days_1_30) : '—'}</td>
                        <td className="p-4 text-right font-mono text-[#FF8C00]">{v.days_31_60 > 0 ? formatCurrency(v.days_31_60) : '—'}</td>
                        <td className="p-4 text-right font-mono text-[#FF5722]">{v.days_61_90 > 0 ? formatCurrency(v.days_61_90) : '—'}</td>
                        <td className="p-4 text-right font-mono text-[#FF3B2F]">{v.days_over_90 > 0 ? formatCurrency(v.days_over_90) : '—'}</td>
                        <td className="p-4 text-right font-mono font-bold">{formatCurrency(v.total)}</td>
                      </tr>
                    ))}
                    {/* Totals Row */}
                    <tr className="bg-[rgba(244,246,240,0.03)] font-bold">
                      <td className="p-4 text-sm">TOTAL</td>
                      <td className="p-4 text-right font-mono text-[#1AFFE4]">{formatCurrency(vendorAging.totals.current)}</td>
                      <td className="p-4 text-right font-mono text-[#FFB300]">{formatCurrency(vendorAging.totals.days_1_30)}</td>
                      <td className="p-4 text-right font-mono text-[#FF8C00]">{formatCurrency(vendorAging.totals.days_31_60)}</td>
                      <td className="p-4 text-right font-mono text-[#FF5722]">{formatCurrency(vendorAging.totals.days_61_90)}</td>
                      <td className="p-4 text-right font-mono text-[#FF3B2F]">{formatCurrency(vendorAging.totals.days_over_90)}</td>
                      <td className="p-4 text-right font-mono">{formatCurrency(vendorAging.totals.grand_total)}</td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Create Bill Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)] text-[#F4F6F0] max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-[#C8FF00]" />
              New Vendor Bill
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Vendor Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Vendor Invoice # *</Label>
                <Input
                  value={formData.bill_number}
                  onChange={(e) => setFormData(prev => ({ ...prev, bill_number: e.target.value }))}
                  placeholder="e.g., INV-2024-001"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Vendor Name *</Label>
                <Input
                  value={formData.vendor_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, vendor_name: e.target.value }))}
                  placeholder="Vendor company name"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Vendor GSTIN</Label>
                <Input
                  value={formData.vendor_gstin}
                  onChange={(e) => setFormData(prev => ({ ...prev, vendor_gstin: e.target.value.toUpperCase() }))}
                  placeholder="29ABCDE1234F1Z5"
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-[rgba(244,246,240,0.7)]">Bill Date</Label>
                  <Input
                    type="date"
                    value={formData.bill_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, bill_date: e.target.value }))}
                    className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                  />
                </div>
                <div>
                  <Label className="text-[rgba(244,246,240,0.7)]">Due Date</Label>
                  <Input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                    className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                  />
                </div>
              </div>
            </div>

            {/* Line Items */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label className="text-[rgba(244,246,240,0.7)]">Line Items</Label>
                <Button type="button" variant="outline" size="sm" onClick={handleAddLineItem} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                  <Plus className="w-4 h-4 mr-1" /> Add Item
                </Button>
              </div>
              
              <div className="space-y-3">
                {formData.line_items.map((item, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-end p-3 bg-[#0B0B0F] rounded-lg">
                    <div className="col-span-4">
                      <Label className="text-xs text-[rgba(244,246,240,0.5)]">Description</Label>
                      <Input
                        value={item.description}
                        onChange={(e) => handleLineItemChange(idx, 'description', e.target.value)}
                        placeholder="Item description"
                        className="bg-transparent border-[rgba(244,246,240,0.1)] text-[#F4F6F0] text-sm"
                      />
                    </div>
                    <div className="col-span-1">
                      <Label className="text-xs text-[rgba(244,246,240,0.5)]">Qty</Label>
                      <Input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => handleLineItemChange(idx, 'quantity', e.target.value)}
                        className="bg-transparent border-[rgba(244,246,240,0.1)] text-[#F4F6F0] text-sm"
                      />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs text-[rgba(244,246,240,0.5)]">Rate</Label>
                      <Input
                        type="number"
                        value={item.rate}
                        onChange={(e) => handleLineItemChange(idx, 'rate', e.target.value)}
                        className="bg-transparent border-[rgba(244,246,240,0.1)] text-[#F4F6F0] text-sm"
                      />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs text-[rgba(244,246,240,0.5)]">GST %</Label>
                      <Select value={String(item.gst_rate)} onValueChange={(v) => handleLineItemChange(idx, 'gst_rate', parseInt(v))}>
                        <SelectTrigger className="bg-transparent border-[rgba(244,246,240,0.1)] text-[#F4F6F0] text-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                          {gstRates.map(r => <SelectItem key={r} value={String(r)} className="text-[#F4F6F0]">{r}%</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-2 text-right">
                      <Label className="text-xs text-[rgba(244,246,240,0.5)]">Amount</Label>
                      <p className="font-mono text-[#C8FF00]">{formatCurrency((parseFloat(item.quantity) || 0) * (parseFloat(item.rate) || 0))}</p>
                    </div>
                    <div className="col-span-1 text-center">
                      {formData.line_items.length > 1 && (
                        <Button type="button" variant="ghost" size="sm" onClick={() => handleRemoveLineItem(idx)} className="text-[#FF3B2F]">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Totals */}
            <div className="bg-[#0B0B0F] rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-[rgba(244,246,240,0.5)]">Subtotal</span>
                <span className="font-mono">{formatCurrency(parseFloat(calculateTotals.subtotal))}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[rgba(244,246,240,0.5)]">CGST</span>
                <span className="font-mono">{formatCurrency(parseFloat(calculateTotals.cgst))}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[rgba(244,246,240,0.5)]">SGST</span>
                <span className="font-mono">{formatCurrency(parseFloat(calculateTotals.sgst))}</span>
              </div>
              {parseFloat(calculateTotals.igst) > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-[rgba(244,246,240,0.5)]">IGST</span>
                  <span className="font-mono">{formatCurrency(parseFloat(calculateTotals.igst))}</span>
                </div>
              )}
              <div className="flex justify-between text-lg font-bold border-t border-[rgba(244,246,240,0.1)] pt-2">
                <span>Total Amount</span>
                <span className="text-[#C8FF00] font-mono">{formatCurrency(parseFloat(calculateTotals.total))}</span>
              </div>
            </div>

            {/* Notes */}
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">Notes</Label>
              <Textarea
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Additional notes..."
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
              Cancel
            </Button>
            <Button onClick={handleCreateBill} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00]">
              Create Bill
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bill Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)] text-[#F4F6F0] max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedBill && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-[#3B9EFF]" />
                    {selectedBill.internal_ref}
                  </span>
                  <Badge className={`${statusConfig[selectedBill.status]?.bg} ${statusConfig[selectedBill.status]?.text} border-0`}>
                    {statusConfig[selectedBill.status]?.label}
                  </Badge>
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {/* Vendor Info */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-[#0B0B0F] rounded-lg">
                  <div>
                    <p className="text-xs text-[rgba(244,246,240,0.5)]">Vendor Invoice #</p>
                    <p className="font-medium">{selectedBill.bill_number}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[rgba(244,246,240,0.5)]">Vendor</p>
                    <p className="font-medium">{selectedBill.vendor_name || "—"}</p>
                    {selectedBill.vendor_gstin && <p className="text-xs text-[rgba(244,246,240,0.5)]">{selectedBill.vendor_gstin}</p>}
                  </div>
                  <div>
                    <p className="text-xs text-[rgba(244,246,240,0.5)]">Bill Date</p>
                    <p className="font-medium">{selectedBill.bill_date}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[rgba(244,246,240,0.5)]">Due Date</p>
                    <p className={`font-medium ${selectedBill.due_date < new Date().toISOString().split("T")[0] && selectedBill.status !== "PAID" ? 'text-[#FF3B2F]' : ''}`}>{selectedBill.due_date}</p>
                  </div>
                </div>

                {/* Line Items */}
                {selectedBill.line_items && selectedBill.line_items.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2">Line Items</p>
                    <div className="border border-[rgba(244,246,240,0.1)] rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-[#0B0B0F]">
                          <tr>
                            <th className="text-left p-2 text-xs text-[rgba(244,246,240,0.5)]">Description</th>
                            <th className="text-right p-2 text-xs text-[rgba(244,246,240,0.5)]">Qty</th>
                            <th className="text-right p-2 text-xs text-[rgba(244,246,240,0.5)]">Rate</th>
                            <th className="text-right p-2 text-xs text-[rgba(244,246,240,0.5)]">GST</th>
                            <th className="text-right p-2 text-xs text-[rgba(244,246,240,0.5)]">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedBill.line_items.map((item, idx) => (
                            <tr key={idx} className="border-t border-[rgba(244,246,240,0.05)]">
                              <td className="p-2">{item.item_description}</td>
                              <td className="p-2 text-right">{item.quantity}</td>
                              <td className="p-2 text-right font-mono">{formatCurrency(item.rate)}</td>
                              <td className="p-2 text-right">{item.gst_rate}%</td>
                              <td className="p-2 text-right font-mono">{formatCurrency(item.total)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Totals */}
                <div className="bg-[#0B0B0F] rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-[rgba(244,246,240,0.5)]">Subtotal</span>
                    <span className="font-mono">{formatCurrency(selectedBill.subtotal)}</span>
                  </div>
                  {selectedBill.cgst > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-[rgba(244,246,240,0.5)]">CGST</span>
                      <span className="font-mono">{formatCurrency(selectedBill.cgst)}</span>
                    </div>
                  )}
                  {selectedBill.sgst > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-[rgba(244,246,240,0.5)]">SGST</span>
                      <span className="font-mono">{formatCurrency(selectedBill.sgst)}</span>
                    </div>
                  )}
                  {selectedBill.igst > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-[rgba(244,246,240,0.5)]">IGST</span>
                      <span className="font-mono">{formatCurrency(selectedBill.igst)}</span>
                    </div>
                  )}
                  <div className="flex justify-between font-bold border-t border-[rgba(244,246,240,0.1)] pt-2">
                    <span>Total Amount</span>
                    <span className="text-[#C8FF00] font-mono">{formatCurrency(selectedBill.total_amount)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[rgba(244,246,240,0.5)]">Amount Paid</span>
                    <span className="font-mono text-[#1AFFE4]">{formatCurrency(selectedBill.amount_paid)}</span>
                  </div>
                  <div className="flex justify-between font-bold">
                    <span>Balance Due</span>
                    <span className={`font-mono ${selectedBill.balance_due > 0 ? 'text-[#FF3B2F]' : 'text-[#1AFFE4]'}`}>{formatCurrency(selectedBill.balance_due)}</span>
                  </div>
                </div>

                {/* Payments */}
                {selectedBill.payments && selectedBill.payments.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2">Payment History</p>
                    <div className="space-y-2">
                      {selectedBill.payments.map(p => (
                        <div key={p.payment_id} className="flex justify-between items-center p-3 bg-[#0B0B0F] rounded-lg text-sm">
                          <div>
                            <p className="font-medium">{formatCurrency(p.amount)}</p>
                            <p className="text-xs text-[rgba(244,246,240,0.5)]">{p.payment_date} | {p.payment_mode}</p>
                          </div>
                          {p.reference_number && <span className="text-xs text-[rgba(244,246,240,0.5)]">Ref: {p.reference_number}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <DialogFooter className="flex gap-2">
                {selectedBill.status === "DRAFT" && (
                  <Button onClick={() => handleApprove(selectedBill)} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00]">
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Approve
                  </Button>
                )}
                {["APPROVED", "PARTIAL_PAID"].includes(selectedBill.status) && selectedBill.balance_due > 0 && (
                  <Button onClick={() => { setPaymentData({ amount: selectedBill.balance_due, payment_date: new Date().toISOString().split("T")[0], payment_mode: "BANK", reference_number: "" }); setShowPayDialog(true); }} className="bg-[#3B9EFF] text-white hover:bg-[#2A8EEE]">
                    <Banknote className="w-4 h-4 mr-2" /> Record Payment
                  </Button>
                )}
                <Button variant="outline" onClick={() => setShowDetailDialog(false)} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                  Close
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={showPayDialog} onOpenChange={setShowPayDialog}>
        <DialogContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Banknote className="w-5 h-5 text-[#1AFFE4]" />
              Record Payment
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="p-3 bg-[#0B0B0F] rounded-lg">
              <p className="text-xs text-[rgba(244,246,240,0.5)]">Balance Due</p>
              <p className="text-xl font-bold text-[#FF3B2F] font-mono">{formatCurrency(selectedBill?.balance_due)}</p>
            </div>
            
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">Amount *</Label>
              <Input
                type="number"
                value={paymentData.amount}
                onChange={(e) => setPaymentData(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Payment Date</Label>
                <Input
                  type="date"
                  value={paymentData.payment_date}
                  onChange={(e) => setPaymentData(prev => ({ ...prev, payment_date: e.target.value }))}
                  className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
                />
              </div>
              <div>
                <Label className="text-[rgba(244,246,240,0.7)]">Payment Mode</Label>
                <Select value={paymentData.payment_mode} onValueChange={(v) => setPaymentData(prev => ({ ...prev, payment_mode: v }))}>
                  <SelectTrigger className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#14141B] border-[rgba(244,246,240,0.15)]">
                    {paymentModes.map(m => <SelectItem key={m.value} value={m.value} className="text-[#F4F6F0]">{m.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label className="text-[rgba(244,246,240,0.7)]">Reference Number</Label>
              <Input
                value={paymentData.reference_number}
                onChange={(e) => setPaymentData(prev => ({ ...prev, reference_number: e.target.value }))}
                placeholder="NEFT/UTR/Cheque #"
                className="bg-[#0B0B0F] border-[rgba(244,246,240,0.15)] text-[#F4F6F0]"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPayDialog(false)} className="border-[rgba(244,246,240,0.15)] text-[#F4F6F0]">
              Cancel
            </Button>
            <Button onClick={handleRecordPayment} className="bg-[#1AFFE4] text-black hover:bg-[#00E5CC]">
              Record Payment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
