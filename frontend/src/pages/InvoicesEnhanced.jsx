import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Plus, Search, RefreshCw, Receipt, Eye, Send, Copy, Ban, Trash2, 
  DollarSign, CreditCard, Calendar, Clock, AlertTriangle, CheckCircle,
  FileText, ArrowRight, Download, Filter, MoreVertical, Users, Building2,
  TrendingUp, TrendingDown, Wallet, PieChart
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";

const statusColors = {
  draft: "bg-gray-100 text-gray-700",
  sent: "bg-blue-100 text-blue-700",
  viewed: "bg-purple-100 text-purple-700",
  partially_paid: "bg-yellow-100 text-yellow-700",
  paid: "bg-green-100 text-green-700",
  overdue: "bg-red-100 text-red-700",
  void: "bg-gray-200 text-gray-500",
  written_off: "bg-orange-100 text-orange-700"
};

const statusLabels = {
  draft: "Draft",
  sent: "Sent",
  viewed: "Viewed",
  partially_paid: "Partial",
  paid: "Paid",
  overdue: "Overdue",
  void: "Void",
  written_off: "Written Off"
};

export default function InvoicesEnhanced() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState("invoices");
  const [invoices, setInvoices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [customers, setCustomers] = useState([]);
  const [items, setItems] = useState([]);
  
  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [customerFilter, setCustomerFilter] = useState(searchParams.get("customer_id") || "");
  
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  
  // Form state
  const [newInvoice, setNewInvoice] = useState({
    customer_id: searchParams.get("customer_id") || "",
    invoice_date: new Date().toISOString().split("T")[0],
    payment_terms: 30,
    line_items: [{ name: "", description: "", quantity: 1, rate: 0, tax_rate: 18 }],
    discount_type: "percentage",
    discount_value: 0,
    shipping_charge: 0,
    customer_notes: "",
    terms_conditions: "",
    send_email: false
  });
  
  const [newPayment, setNewPayment] = useState({
    amount: 0,
    payment_mode: "bank_transfer",
    reference_number: "",
    payment_date: new Date().toISOString().split("T")[0],
    notes: ""
  });

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchInvoices(), fetchSummary(), fetchCustomers(), fetchItems()]);
    setLoading(false);
  }, []);

  const fetchInvoices = async () => {
    try {
      let url = `${API}/invoices-enhanced/?per_page=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      if (customerFilter) url += `&customer_id=${customerFilter}`;
      
      const res = await fetch(url, { headers });
      const data = await res.json();
      setInvoices(data.invoices || []);
    } catch (e) {
      console.error("Failed to fetch invoices:", e);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/summary`, { headers });
      const data = await res.json();
      setSummary(data.summary || null);
    } catch (e) {
      console.error("Failed to fetch summary:", e);
    }
  };

  const fetchCustomers = async () => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/?contact_type=customer&per_page=200`, { headers });
      const data = await res.json();
      setCustomers(data.contacts || []);
    } catch (e) {
      console.error("Failed to fetch customers:", e);
    }
  };

  const fetchItems = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/?per_page=200`, { headers });
      const data = await res.json();
      setItems(data.items || []);
    } catch (e) {
      console.error("Failed to fetch items:", e);
    }
  };

  const fetchInvoiceDetail = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}`, { headers });
      const data = await res.json();
      setSelectedInvoice(data.invoice);
      setShowDetailDialog(true);
    } catch (e) {
      toast.error("Failed to fetch invoice details");
    }
  };

  // Invoice CRUD
  const handleCreateInvoice = async () => {
    if (!newInvoice.customer_id) return toast.error("Please select a customer");
    if (!newInvoice.line_items.some(li => li.name && li.rate > 0)) return toast.error("Add at least one line item");
    
    try {
      const payload = {
        ...newInvoice,
        line_items: newInvoice.line_items.filter(li => li.name && li.rate > 0)
      };
      
      const res = await fetch(`${API}/invoices-enhanced/`, { method: "POST", headers, body: JSON.stringify(payload) });
      if (res.ok) {
        toast.success("Invoice created successfully");
        setShowCreateDialog(false);
        resetForm();
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to create invoice");
      }
    } catch (e) {
      toast.error("Error creating invoice");
    }
  };

  const handleSendInvoice = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/send`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Invoice sent successfully");
        fetchInvoiceDetail(invoiceId);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to send invoice");
      }
    } catch (e) {
      toast.error("Error sending invoice");
    }
  };

  const handleMarkSent = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/mark-sent`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Invoice marked as sent");
        fetchInvoiceDetail(invoiceId);
        fetchData();
      }
    } catch (e) {
      toast.error("Error marking invoice as sent");
    }
  };

  const handleCloneInvoice = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/clone`, { method: "POST", headers });
      if (res.ok) {
        const data = await res.json();
        toast.success("Invoice cloned as new draft");
        fetchData();
        fetchInvoiceDetail(data.invoice.invoice_id);
      }
    } catch (e) {
      toast.error("Error cloning invoice");
    }
  };

  const handleVoidInvoice = async (invoiceId) => {
    if (!confirm("Are you sure you want to void this invoice?")) return;
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/void`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Invoice voided");
        setShowDetailDialog(false);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to void invoice");
      }
    } catch (e) {
      toast.error("Error voiding invoice");
    }
  };

  const handleDeleteInvoice = async (invoiceId) => {
    if (!confirm("Delete this invoice?")) return;
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Invoice deleted");
        setShowDetailDialog(false);
        fetchData();
      } else {
        const err = await res.json();
        if (err.detail?.includes("draft") || err.detail?.includes("payments")) {
          if (confirm(err.detail + " Void instead?")) {
            await handleVoidInvoice(invoiceId);
          }
        } else {
          toast.error(err.detail || "Failed to delete invoice");
        }
      }
    } catch (e) {
      toast.error("Error deleting invoice");
    }
  };

  // Payments
  const handleRecordPayment = async () => {
    if (!newPayment.amount || newPayment.amount <= 0) return toast.error("Enter valid amount");
    try {
      const res = await fetch(`${API}/invoices-enhanced/${selectedInvoice.invoice_id}/payments`, {
        method: "POST",
        headers,
        body: JSON.stringify(newPayment)
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Payment recorded. New balance: ₹${data.new_balance?.toLocaleString("en-IN")}`);
        setShowPaymentDialog(false);
        setNewPayment({ amount: 0, payment_mode: "bank_transfer", reference_number: "", payment_date: new Date().toISOString().split("T")[0], notes: "" });
        fetchInvoiceDetail(selectedInvoice.invoice_id);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to record payment");
      }
    } catch (e) {
      toast.error("Error recording payment");
    }
  };

  const handleDeletePayment = async (paymentId) => {
    if (!confirm("Delete this payment?")) return;
    try {
      const res = await fetch(`${API}/invoices-enhanced/${selectedInvoice.invoice_id}/payments/${paymentId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Payment deleted");
        fetchInvoiceDetail(selectedInvoice.invoice_id);
        fetchData();
      }
    } catch (e) {
      toast.error("Error deleting payment");
    }
  };

  // Line Items
  const addLineItem = () => {
    setNewInvoice(prev => ({
      ...prev,
      line_items: [...prev.line_items, { name: "", description: "", quantity: 1, rate: 0, tax_rate: 18 }]
    }));
  };

  const updateLineItem = (index, field, value) => {
    setNewInvoice(prev => {
      const updated = [...prev.line_items];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, line_items: updated };
    });
  };

  const removeLineItem = (index) => {
    setNewInvoice(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const selectItem = (index, itemId) => {
    const item = items.find(i => i.item_id === itemId);
    if (item) {
      updateLineItem(index, "name", item.name);
      updateLineItem(index, "rate", item.selling_price || item.rate || 0);
      updateLineItem(index, "description", item.description || "");
      updateLineItem(index, "item_id", itemId);
    }
  };

  const calculateSubtotal = () => {
    return newInvoice.line_items.reduce((sum, item) => sum + (item.quantity * item.rate), 0);
  };

  const calculateTax = () => {
    return newInvoice.line_items.reduce((sum, item) => {
      const amount = item.quantity * item.rate;
      return sum + (amount * (item.tax_rate || 0) / 100);
    }, 0);
  };

  const calculateTotal = () => {
    const subtotal = calculateSubtotal();
    const tax = calculateTax();
    const discount = newInvoice.discount_type === "percentage" 
      ? subtotal * (newInvoice.discount_value / 100)
      : newInvoice.discount_value;
    return subtotal + tax - discount + (newInvoice.shipping_charge || 0);
  };

  const resetForm = () => {
    setNewInvoice({
      customer_id: "",
      invoice_date: new Date().toISOString().split("T")[0],
      payment_terms: 30,
      line_items: [{ name: "", description: "", quantity: 1, rate: 0, tax_rate: 18 }],
      discount_type: "percentage",
      discount_value: 0,
      shipping_charge: 0,
      customer_notes: "",
      terms_conditions: "",
      send_email: false
    });
  };

  const formatCurrency = (amount) => `₹${(amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  const formatDate = (date) => date ? new Date(date).toLocaleDateString("en-IN") : "-";

  return (
    <div className="space-y-6" data-testid="invoices-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Invoices"
        description="Manage invoices, payments, and receivables"
        icon={Receipt}
        actions={
          <div className="flex gap-2">
            <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
            <Button onClick={() => setShowCreateDialog(true)} className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-invoice-btn">
              <Plus className="h-4 w-4" /> New Invoice
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      {summary && (
        <StatCardGrid columns={6}>
          <StatCard
            title="Total Invoices"
            value={summary.total_invoices}
            icon={Receipt}
            variant="info"
          />
          <StatCard
            title="Draft"
            value={summary.draft}
            icon={FileText}
            variant="default"
          />
          <StatCard
            title="Overdue"
            value={summary.overdue}
            icon={AlertTriangle}
            variant="danger"
          />
          <StatCard
            title="Paid"
            value={summary.paid}
            icon={CheckCircle}
            variant="success"
          />
          <StatCard
            title="Total Invoiced"
            value={formatCurrencyCompact(summary.total_invoiced)}
            icon={TrendingUp}
            variant="info"
          />
          <StatCard
            title="Outstanding"
            value={formatCurrencyCompact(summary.total_outstanding)}
            icon={Wallet}
            variant="warning"
          />
        </StatCardGrid>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="invoices">All Invoices</TabsTrigger>
          <TabsTrigger value="overdue">Overdue</TabsTrigger>
          <TabsTrigger value="drafts">Drafts</TabsTrigger>
        </TabsList>

        <TabsContent value="invoices" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 max-w-3xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input 
                  value={search} 
                  onChange={(e) => setSearch(e.target.value)} 
                  onKeyUp={(e) => e.key === "Enter" && fetchInvoices()}
                  placeholder="Search invoices..." 
                  className="pl-10" 
                  data-testid="search-invoices" 
                />
              </div>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setTimeout(fetchInvoices, 100); }}>
                <SelectTrigger className="w-36"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="sent">Sent</SelectItem>
                  <SelectItem value="partially_paid">Partial</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="overdue">Overdue</SelectItem>
                  <SelectItem value="void">Void</SelectItem>
                </SelectContent>
              </Select>
              <Select value={customerFilter || "all_customers"} onValueChange={(v) => { setCustomerFilter(v === "all_customers" ? "" : v); setTimeout(fetchInvoices, 100); }}>
                <SelectTrigger className="w-48"><SelectValue placeholder="All Customers" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all_customers">All Customers</SelectItem>
                  {customers.map(c => <SelectItem key={c.contact_id} value={c.contact_id}>{c.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Invoice List */}
          {loading ? (
            <Card><CardContent className="py-12 text-center"><RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" /></CardContent></Card>
          ) : invoices.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                <Receipt className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No invoices found</p>
                <Button onClick={() => setShowCreateDialog(true)} className="mt-4 bg-[#22EDA9] text-black">Create First Invoice</Button>
              </CardContent>
            </Card>
          ) : (
            <div className="bg-white rounded-lg border overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Invoice #</th>
                    <th className="px-4 py-3 text-left">Customer</th>
                    <th className="px-4 py-3 text-left">Date</th>
                    <th className="px-4 py-3 text-left">Due Date</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                    <th className="px-4 py-3 text-right">Balance</th>
                    <th className="px-4 py-3 text-center">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {invoices.map(inv => (
                    <tr key={inv.invoice_id} className="hover:bg-gray-50 cursor-pointer" onClick={() => fetchInvoiceDetail(inv.invoice_id)} data-testid={`invoice-row-${inv.invoice_id}`}>
                      <td className="px-4 py-3 font-medium text-blue-600">{inv.invoice_number}</td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium">{inv.customer_name}</p>
                          {inv.reference_number && <p className="text-xs text-gray-500">Ref: {inv.reference_number}</p>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">{formatDate(inv.invoice_date)}</td>
                      <td className="px-4 py-3 text-sm">{formatDate(inv.due_date)}</td>
                      <td className="px-4 py-3 text-right font-medium">{formatCurrency(inv.grand_total)}</td>
                      <td className="px-4 py-3 text-right">
                        <span className={inv.balance_due > 0 ? "text-red-600 font-medium" : "text-green-600"}>
                          {formatCurrency(inv.balance_due)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={statusColors[inv.status] || "bg-gray-100"}>{statusLabels[inv.status] || inv.status}</Badge>
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button size="icon" variant="ghost" onClick={() => fetchInvoiceDetail(inv.invoice_id)}><Eye className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        <TabsContent value="overdue">
          {invoices.filter(i => i.status === "overdue").length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-300" /><p>No overdue invoices!</p></CardContent></Card>
          ) : (
            <div className="grid gap-4">
              {invoices.filter(i => i.status === "overdue").map(inv => (
                <Card key={inv.invoice_id} className="border-red-200 bg-red-50 cursor-pointer hover:shadow-md" onClick={() => fetchInvoiceDetail(inv.invoice_id)}>
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold text-lg">{inv.invoice_number}</p>
                        <p className="text-gray-600">{inv.customer_name}</p>
                        <p className="text-sm text-red-600">Due: {formatDate(inv.due_date)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-red-600">{formatCurrency(inv.balance_due)}</p>
                        <Badge className="bg-red-100 text-red-700">Overdue</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="drafts">
          {invoices.filter(i => i.status === "draft").length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No draft invoices</p></CardContent></Card>
          ) : (
            <div className="grid gap-4">
              {invoices.filter(i => i.status === "draft").map(inv => (
                <Card key={inv.invoice_id} className="cursor-pointer hover:shadow-md" onClick={() => fetchInvoiceDetail(inv.invoice_id)}>
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold text-lg">{inv.invoice_number}</p>
                        <p className="text-gray-600">{inv.customer_name}</p>
                        <p className="text-sm text-gray-500">Created: {formatDate(inv.created_time)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold">{formatCurrency(inv.grand_total)}</p>
                        <Badge className="bg-gray-100 text-gray-700">Draft</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Invoice Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={(open) => { setShowCreateDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Invoice</DialogTitle>
            <DialogDescription>Create a new invoice for a customer</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Customer & Basic Info */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Customer *</Label>
                <Select value={newInvoice.customer_id} onValueChange={(v) => setNewInvoice({ ...newInvoice, customer_id: v })}>
                  <SelectTrigger data-testid="customer-select"><SelectValue placeholder="Select customer" /></SelectTrigger>
                  <SelectContent>
                    {customers.map(c => <SelectItem key={c.contact_id} value={c.contact_id}>{c.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Invoice Date</Label>
                <Input type="date" value={newInvoice.invoice_date} onChange={(e) => setNewInvoice({ ...newInvoice, invoice_date: e.target.value })} />
              </div>
              <div>
                <Label>Payment Terms (days)</Label>
                <Input type="number" value={newInvoice.payment_terms} onChange={(e) => setNewInvoice({ ...newInvoice, payment_terms: parseInt(e.target.value) || 30 })} />
              </div>
            </div>

            <Separator />

            {/* Line Items */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <Label className="text-lg">Line Items</Label>
                <Button size="sm" variant="outline" onClick={addLineItem}><Plus className="h-4 w-4 mr-1" /> Add Item</Button>
              </div>
              
              <div className="space-y-3">
                {newInvoice.line_items.map((item, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-end bg-gray-50 p-3 rounded-lg">
                    <div className="col-span-4">
                      <Label className="text-xs">Item</Label>
                      <Select onValueChange={(v) => selectItem(idx, v)}>
                        <SelectTrigger><SelectValue placeholder="Select or type" /></SelectTrigger>
                        <SelectContent>
                          {items.map(i => <SelectItem key={i.item_id} value={i.item_id}>{i.name}</SelectItem>)}
                        </SelectContent>
                      </Select>
                      <Input 
                        className="mt-1" 
                        placeholder="Or enter item name" 
                        value={item.name} 
                        onChange={(e) => updateLineItem(idx, "name", e.target.value)} 
                      />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs">Qty</Label>
                      <Input type="number" value={item.quantity} onChange={(e) => updateLineItem(idx, "quantity", parseFloat(e.target.value) || 1)} />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs">Rate</Label>
                      <Input type="number" value={item.rate} onChange={(e) => updateLineItem(idx, "rate", parseFloat(e.target.value) || 0)} />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs">Tax %</Label>
                      <Select value={String(item.tax_rate)} onValueChange={(v) => updateLineItem(idx, "tax_rate", parseFloat(v))}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">0%</SelectItem>
                          <SelectItem value="5">5%</SelectItem>
                          <SelectItem value="12">12%</SelectItem>
                          <SelectItem value="18">18%</SelectItem>
                          <SelectItem value="28">28%</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-1 text-right">
                      <p className="text-sm font-medium">{formatCurrency(item.quantity * item.rate)}</p>
                    </div>
                    <div className="col-span-1">
                      {newInvoice.line_items.length > 1 && (
                        <Button size="icon" variant="ghost" onClick={() => removeLineItem(idx)}><Trash2 className="h-4 w-4 text-red-400" /></Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Totals */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <Label>Customer Notes</Label>
                  <Textarea value={newInvoice.customer_notes} onChange={(e) => setNewInvoice({ ...newInvoice, customer_notes: e.target.value })} placeholder="Notes to display on invoice" rows={2} />
                </div>
                <div>
                  <Label>Terms & Conditions</Label>
                  <Textarea value={newInvoice.terms_conditions} onChange={(e) => setNewInvoice({ ...newInvoice, terms_conditions: e.target.value })} placeholder="Payment terms, etc." rows={2} />
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <div className="flex justify-between"><span>Sub Total:</span><span className="font-medium">{formatCurrency(calculateSubtotal())}</span></div>
                <div className="flex gap-2 items-center">
                  <span>Discount:</span>
                  <Select value={newInvoice.discount_type} onValueChange={(v) => setNewInvoice({ ...newInvoice, discount_type: v })}>
                    <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="percentage">%</SelectItem>
                      <SelectItem value="amount">₹</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input type="number" className="w-24" value={newInvoice.discount_value} onChange={(e) => setNewInvoice({ ...newInvoice, discount_value: parseFloat(e.target.value) || 0 })} />
                </div>
                <div className="flex justify-between"><span>Tax:</span><span>{formatCurrency(calculateTax())}</span></div>
                <div className="flex gap-2 items-center">
                  <span>Shipping:</span>
                  <Input type="number" className="w-24" value={newInvoice.shipping_charge} onChange={(e) => setNewInvoice({ ...newInvoice, shipping_charge: parseFloat(e.target.value) || 0 })} />
                </div>
                <Separator />
                <div className="flex justify-between text-lg font-bold"><span>Total:</span><span className="text-green-600">{formatCurrency(calculateTotal())}</span></div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="send-email" checked={newInvoice.send_email} onChange={(e) => setNewInvoice({ ...newInvoice, send_email: e.target.checked })} />
              <Label htmlFor="send-email">Send invoice via email after creating</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateInvoice} className="bg-[#22EDA9] text-black" data-testid="create-invoice-submit">Create Invoice</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Invoice Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={(open) => { setShowDetailDialog(open); if (!open) setSelectedInvoice(null); }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedInvoice && (
            <>
              <DialogHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      {selectedInvoice.invoice_number}
                      <Badge className={statusColors[selectedInvoice.status]}>{statusLabels[selectedInvoice.status]}</Badge>
                    </DialogTitle>
                    <DialogDescription>{selectedInvoice.customer_name}</DialogDescription>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{formatCurrency(selectedInvoice.grand_total)}</p>
                    {selectedInvoice.balance_due > 0 && (
                      <p className="text-sm text-red-600">Balance: {formatCurrency(selectedInvoice.balance_due)}</p>
                    )}
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-6 py-4">
                {/* Info Grid */}
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div><span className="text-gray-500">Invoice Date:</span><br/><span className="font-medium">{formatDate(selectedInvoice.invoice_date)}</span></div>
                  <div><span className="text-gray-500">Due Date:</span><br/><span className="font-medium">{formatDate(selectedInvoice.due_date)}</span></div>
                  <div><span className="text-gray-500">Reference:</span><br/><span className="font-medium">{selectedInvoice.reference_number || "-"}</span></div>
                  <div><span className="text-gray-500">Payment Terms:</span><br/><span className="font-medium">{selectedInvoice.payment_terms} days</span></div>
                </div>

                {/* Line Items */}
                {selectedInvoice.line_items?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3">Line Items</h4>
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-3 py-2 text-left">Item</th>
                              <th className="px-3 py-2 text-right">Qty</th>
                              <th className="px-3 py-2 text-right">Rate</th>
                              <th className="px-3 py-2 text-right">Tax</th>
                              <th className="px-3 py-2 text-right">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedInvoice.line_items.map((item, idx) => (
                              <tr key={idx} className="border-t">
                                <td className="px-3 py-2">
                                  <p className="font-medium">{item.name}</p>
                                  {item.description && <p className="text-xs text-gray-500">{item.description}</p>}
                                </td>
                                <td className="px-3 py-2 text-right">{item.quantity}</td>
                                <td className="px-3 py-2 text-right">{formatCurrency(item.rate)}</td>
                                <td className="px-3 py-2 text-right">{item.tax_rate}%</td>
                                <td className="px-3 py-2 text-right font-medium">{formatCurrency(item.total)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}

                {/* Totals */}
                <div className="bg-gray-50 p-4 rounded-lg w-64 ml-auto space-y-1 text-sm">
                  <div className="flex justify-between"><span>Sub Total:</span><span>{formatCurrency(selectedInvoice.sub_total)}</span></div>
                  {selectedInvoice.total_discount > 0 && <div className="flex justify-between text-red-600"><span>Discount:</span><span>-{formatCurrency(selectedInvoice.total_discount)}</span></div>}
                  <div className="flex justify-between"><span>Tax:</span><span>{formatCurrency(selectedInvoice.tax_total)}</span></div>
                  {selectedInvoice.shipping_charge > 0 && <div className="flex justify-between"><span>Shipping:</span><span>{formatCurrency(selectedInvoice.shipping_charge)}</span></div>}
                  <Separator />
                  <div className="flex justify-between font-bold text-base"><span>Total:</span><span>{formatCurrency(selectedInvoice.grand_total)}</span></div>
                  {selectedInvoice.amount_paid > 0 && <div className="flex justify-between text-green-600"><span>Paid:</span><span>-{formatCurrency(selectedInvoice.amount_paid)}</span></div>}
                  <div className="flex justify-between font-bold text-lg"><span>Balance:</span><span className={selectedInvoice.balance_due > 0 ? "text-red-600" : "text-green-600"}>{formatCurrency(selectedInvoice.balance_due)}</span></div>
                </div>

                {/* Payments */}
                {selectedInvoice.payments?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2"><DollarSign className="h-4 w-4" /> Payments Received</h4>
                      <div className="space-y-2">
                        {selectedInvoice.payments.map(payment => (
                          <div key={payment.payment_id} className="flex justify-between items-center bg-green-50 p-3 rounded-lg">
                            <div>
                              <p className="font-medium">{formatCurrency(payment.amount)}</p>
                              <p className="text-xs text-gray-500">{formatDate(payment.payment_date)} • {payment.payment_mode}</p>
                              {payment.reference_number && <p className="text-xs text-gray-500">Ref: {payment.reference_number}</p>}
                            </div>
                            <Button size="icon" variant="ghost" onClick={() => handleDeletePayment(payment.payment_id)}><Trash2 className="h-4 w-4 text-red-400" /></Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {/* History */}
                {selectedInvoice.history?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2"><Clock className="h-4 w-4" /> History</h4>
                      <div className="space-y-1 text-xs text-gray-600 max-h-32 overflow-y-auto">
                        {selectedInvoice.history.slice(0, 10).map((h, idx) => (
                          <p key={idx}><span className="text-gray-400">{formatDate(h.timestamp)}</span> - {h.action}: {h.details}</p>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                <Separator />

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  {selectedInvoice.status === "draft" && (
                    <>
                      <Button variant="outline" size="sm" onClick={() => handleSendInvoice(selectedInvoice.invoice_id)}><Send className="h-4 w-4 mr-1" /> Send</Button>
                      <Button variant="outline" size="sm" onClick={() => handleMarkSent(selectedInvoice.invoice_id)}><CheckCircle className="h-4 w-4 mr-1" /> Mark Sent</Button>
                    </>
                  )}
                  {selectedInvoice.status !== "draft" && selectedInvoice.balance_due > 0 && (
                    <Button 
                      size="sm" 
                      className="bg-green-500 hover:bg-green-600 text-white" 
                      onClick={() => { setNewPayment({ ...newPayment, amount: selectedInvoice.balance_due }); setShowPaymentDialog(true); }}
                      data-testid="record-payment-btn"
                    >
                      <DollarSign className="h-4 w-4 mr-1" /> Record Payment
                    </Button>
                  )}
                  <Button variant="outline" size="sm" onClick={() => handleCloneInvoice(selectedInvoice.invoice_id)}><Copy className="h-4 w-4 mr-1" /> Clone</Button>
                  {selectedInvoice.status !== "void" && selectedInvoice.status !== "paid" && (
                    <Button variant="outline" size="sm" onClick={() => handleVoidInvoice(selectedInvoice.invoice_id)}><Ban className="h-4 w-4 mr-1" /> Void</Button>
                  )}
                  <Button variant="destructive" size="sm" onClick={() => handleDeleteInvoice(selectedInvoice.invoice_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Record Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
            <DialogDescription>Record a payment for invoice {selectedInvoice?.invoice_number}</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex justify-between">
                <span>Balance Due:</span>
                <span className="font-bold text-red-600">{formatCurrency(selectedInvoice?.balance_due)}</span>
              </div>
            </div>
            
            <div>
              <Label>Amount *</Label>
              <Input 
                type="number" 
                value={newPayment.amount} 
                onChange={(e) => setNewPayment({ ...newPayment, amount: parseFloat(e.target.value) || 0 })} 
                max={selectedInvoice?.balance_due}
                data-testid="payment-amount-input"
              />
            </div>
            
            <div>
              <Label>Payment Mode</Label>
              <Select value={newPayment.payment_mode} onValueChange={(v) => setNewPayment({ ...newPayment, payment_mode: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                  <SelectItem value="cheque">Cheque</SelectItem>
                  <SelectItem value="card">Card</SelectItem>
                  <SelectItem value="upi">UPI</SelectItem>
                  <SelectItem value="online">Online</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Payment Date</Label>
              <Input type="date" value={newPayment.payment_date} onChange={(e) => setNewPayment({ ...newPayment, payment_date: e.target.value })} />
            </div>
            
            <div>
              <Label>Reference Number</Label>
              <Input value={newPayment.reference_number} onChange={(e) => setNewPayment({ ...newPayment, reference_number: e.target.value })} placeholder="Transaction ID, Cheque #, etc." />
            </div>
            
            <div>
              <Label>Notes</Label>
              <Textarea value={newPayment.notes} onChange={(e) => setNewPayment({ ...newPayment, notes: e.target.value })} rows={2} />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPaymentDialog(false)}>Cancel</Button>
            <Button onClick={handleRecordPayment} className="bg-green-500 hover:bg-green-600 text-white" data-testid="submit-payment-btn">Record Payment</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
