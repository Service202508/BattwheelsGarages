import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Tabs, TabsContent, TabsList, TabsTrigger
} from "../components/ui/tabs";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator
} from "../components/ui/dropdown-menu";
import { Checkbox } from "../components/ui/checkbox";
import { Textarea } from "../components/ui/textarea";
import {
  Plus, Search, Filter, MoreHorizontal, Download, Upload, Trash2,
  Eye, RefreshCw, IndianRupee, CreditCard, Building2, Calendar,
  FileText, Send, ArrowUpRight, Wallet, Receipt, ChevronDown, X,
  CheckCircle2, AlertCircle, Clock, Banknote, User
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function PaymentsReceived() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [payments, setPayments] = useState([]);
  const [summary, setSummary] = useState({});
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0 });
  
  // Filters
  const [filters, setFilters] = useState({
    search: "",
    payment_type: "",
    payment_mode: "",
    start_date: "",
    end_date: ""
  });
  
  // Dialogs
  const [showRecordDialog, setShowRecordDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showRefundDialog, setShowRefundDialog] = useState(false);
  const [showApplyCreditDialog, setShowApplyCreditDialog] = useState(false);
  
  // Selected data
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [selectedPayments, setSelectedPayments] = useState([]);
  
  // Record payment form
  const [paymentForm, setPaymentForm] = useState({
    customer_id: "",
    payment_date: new Date().toISOString().split('T')[0],
    amount: 0,
    payment_mode: "bank_transfer",
    deposit_to_account: "Bank Account",
    reference_number: "",
    bank_charges: 0,
    tax_deducted: false,
    tax_amount: 0,
    notes: "",
    allocations: [],
    is_retainer: false,
    send_thank_you: false
  });
  
  // Customer search
  const [customers, setCustomers] = useState([]);
  const [customerSearch, setCustomerSearch] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerInvoices, setCustomerInvoices] = useState([]);
  const [customerCredits, setCustomerCredits] = useState([]);
  
  // Refund form
  const [refundForm, setRefundForm] = useState({
    amount: 0,
    refund_date: new Date().toISOString().split('T')[0],
    payment_mode: "bank_transfer",
    reference_number: "",
    notes: ""
  });
  
  // Credits
  const [allCredits, setAllCredits] = useState([]);

  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${localStorage.getItem("token")}`
  };

  // Fetch payments
  const fetchPayments = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        page: pagination.page,
        per_page: pagination.per_page,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v))
      });
      
      const res = await fetch(`${API}/api/payments-received/?${params}`, { headers });
      const data = await res.json();
      
      if (data.code === 0) {
        setPayments(data.payments || []);
        setPagination(prev => ({ ...prev, total: data.total || 0 }));
      }
    } catch (e) {
      console.error("Failed to fetch payments:", e);
    }
  }, [pagination.page, pagination.per_page, filters]);

  // Fetch summary
  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/api/payments-received/summary?period=this_month`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setSummary(data.summary || {});
      }
    } catch (e) {
      console.error("Failed to fetch summary:", e);
    }
  };

  // Fetch all credits
  const fetchCredits = async () => {
    try {
      const res = await fetch(`${API}/api/payments-received/credits?status=available`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setAllCredits(data.credits || []);
      }
    } catch (e) {
      console.error("Failed to fetch credits:", e);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchPayments(), fetchSummary(), fetchCredits()]);
      setLoading(false);
    };
    loadData();
  }, [fetchPayments]);

  // Search customers
  const searchCustomers = async (query) => {
    if (query.length < 2) {
      setCustomers([]);
      return;
    }
    try {
      const res = await fetch(`${API}/contact-integration/contacts/search?q=${encodeURIComponent(query)}&limit=10`, { headers });
      const data = await res.json();
      setCustomers(data.contacts || []);
    } catch (e) {
      console.error("Customer search failed:", e);
    }
  };

  // Fetch customer invoices for payment
  const fetchCustomerInvoices = async (customerId) => {
    try {
      const res = await fetch(`${API}/api/payments-received/customer/${customerId}/open-invoices`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setCustomerInvoices(data.open_invoices || []);
        setCustomerCredits(data.available_credits || []);
      }
    } catch (e) {
      console.error("Failed to fetch customer invoices:", e);
    }
  };

  // Select customer
  const selectCustomer = (customer) => {
    setSelectedCustomer(customer);
    setPaymentForm(prev => ({ ...prev, customer_id: customer.contact_id }));
    setCustomerSearch(customer.name);
    setCustomers([]);
    fetchCustomerInvoices(customer.contact_id);
  };

  // Toggle invoice allocation
  const toggleInvoiceAllocation = (invoice, amount) => {
    setPaymentForm(prev => {
      const existing = prev.allocations.find(a => a.invoice_id === invoice.invoice_id);
      if (existing) {
        // Update amount
        return {
          ...prev,
          allocations: prev.allocations.map(a => 
            a.invoice_id === invoice.invoice_id ? { ...a, amount } : a
          ).filter(a => a.amount > 0)
        };
      } else if (amount > 0) {
        // Add new allocation
        return {
          ...prev,
          allocations: [...prev.allocations, { invoice_id: invoice.invoice_id, amount }]
        };
      }
      return prev;
    });
  };

  // Pay full amount for invoice
  const payFullInvoice = (invoice) => {
    toggleInvoiceAllocation(invoice, invoice.balance_due);
  };

  // Clear allocation
  const clearAllocation = (invoiceId) => {
    setPaymentForm(prev => ({
      ...prev,
      allocations: prev.allocations.filter(a => a.invoice_id !== invoiceId)
    }));
  };

  // Calculate totals
  const calculatePaymentTotals = () => {
    const totalAllocated = paymentForm.allocations.reduce((sum, a) => sum + (a.amount || 0), 0);
    const excess = paymentForm.amount - totalAllocated - paymentForm.bank_charges;
    return { totalAllocated, excess: Math.max(0, excess) };
  };

  // Record payment
  const recordPayment = async () => {
    if (!paymentForm.customer_id) {
      toast.error("Please select a customer");
      return;
    }
    if (paymentForm.amount <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    try {
      const res = await fetch(`${API}/api/payments-received/`, {
        method: "POST",
        headers,
        body: JSON.stringify(paymentForm)
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success(`Payment ${data.payment?.payment_number} recorded successfully`);
        if (data.overpayment_credited) {
          toast.info(`₹${data.overpayment_credited.toLocaleString('en-IN')} added as customer credit`);
        }
        setShowRecordDialog(false);
        resetPaymentForm();
        fetchPayments();
        fetchSummary();
        fetchCredits();
      } else {
        toast.error(data.detail || "Failed to record payment");
      }
    } catch (e) {
      toast.error("Failed to record payment");
    }
  };

  // Reset payment form
  const resetPaymentForm = () => {
    setPaymentForm({
      customer_id: "",
      payment_date: new Date().toISOString().split('T')[0],
      amount: 0,
      payment_mode: "bank_transfer",
      deposit_to_account: "Bank Account",
      reference_number: "",
      bank_charges: 0,
      tax_deducted: false,
      tax_amount: 0,
      notes: "",
      allocations: [],
      is_retainer: false,
      send_thank_you: false
    });
    setSelectedCustomer(null);
    setCustomerSearch("");
    setCustomerInvoices([]);
    setCustomerCredits([]);
  };

  // View payment details
  const viewPayment = async (paymentId) => {
    try {
      const res = await fetch(`${API}/api/payments-received/${paymentId}`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setSelectedPayment({ ...data.payment, invoice_details: data.invoice_details, history: data.history });
        setShowDetailDialog(true);
      }
    } catch (e) {
      toast.error("Failed to load payment details");
    }
  };

  // Delete payment
  const deletePayment = async (paymentId) => {
    if (!window.confirm("Are you sure you want to delete this payment? This will reverse all invoice payments.")) {
      return;
    }
    
    try {
      const res = await fetch(`${API}/api/payments-received/${paymentId}`, {
        method: "DELETE",
        headers
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success("Payment deleted");
        fetchPayments();
        fetchSummary();
        fetchCredits();
        setShowDetailDialog(false);
      } else {
        toast.error(data.detail || "Failed to delete payment");
      }
    } catch (e) {
      toast.error("Failed to delete payment");
    }
  };

  // Refund payment
  const processRefund = async () => {
    if (!selectedPayment) return;
    
    try {
      const res = await fetch(`${API}/api/payments-received/${selectedPayment.payment_id}/refund`, {
        method: "POST",
        headers,
        body: JSON.stringify(refundForm)
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success("Refund processed successfully");
        setShowRefundDialog(false);
        setRefundForm({
          amount: 0,
          refund_date: new Date().toISOString().split('T')[0],
          payment_mode: "bank_transfer",
          reference_number: "",
          notes: ""
        });
        fetchPayments();
        fetchSummary();
        fetchCredits();
      } else {
        toast.error(data.detail || "Failed to process refund");
      }
    } catch (e) {
      toast.error("Failed to process refund");
    }
  };

  // Bulk delete
  const bulkDelete = async () => {
    if (!window.confirm(`Delete ${selectedPayments.length} payments?`)) return;
    
    try {
      const res = await fetch(`${API}/api/payments-received/bulk-action`, {
        method: "POST",
        headers,
        body: JSON.stringify({ payment_ids: selectedPayments, action: "delete" })
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success(data.message);
        setSelectedPayments([]);
        fetchPayments();
        fetchSummary();
      }
    } catch (e) {
      toast.error("Bulk delete failed");
    }
  };

  // Export payments
  const exportPayments = async () => {
    try {
      const params = new URLSearchParams(
        Object.fromEntries(Object.entries(filters).filter(([_, v]) => v))
      );
      const res = await fetch(`${API}/api/payments-received/export?${params}`, { headers });
      const data = await res.json();
      
      if (data.code === 0) {
        const blob = new Blob([data.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        a.click();
        toast.success("Export completed");
      }
    } catch (e) {
      toast.error("Export failed");
    }
  };

  // Status badge
  const getStatusBadge = (payment) => {
    if (payment.status === "refunded") {
      return <Badge variant="destructive">Refunded</Badge>;
    }
    if (payment.is_retainer) {
      return <Badge className="bg-purple-100 text-bw-purple">Retainer</Badge>;
    }
    return <Badge className="bg-bw-volt/10 text-bw-volt border border-bw-volt/25">Recorded</Badge>;
  };

  // Payment mode icon
  const getPaymentModeIcon = (mode) => {
    switch (mode) {
      case "cash": return <Banknote className="h-4 w-4" />;
      case "card": return <CreditCard className="h-4 w-4" />;
      case "bank_transfer": return <Building2 className="h-4 w-4" />;
      case "upi": return <Wallet className="h-4 w-4" />;
      default: return <Receipt className="h-4 w-4" />;
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="payments-received-page">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Payments Received</h1>
          <p className="text-bw-white/[0.45]">Record and manage customer payments</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportPayments}>
            <Download className="h-4 w-4 mr-2" /> Export
          </Button>
          <Button onClick={() => setShowRecordDialog(true)} data-testid="record-payment-btn">
            <Plus className="h-4 w-4 mr-2" /> Record Payment
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-bw-white/[0.45]">This Month</p>
                <p className="text-2xl font-bold">₹{(summary.total_received || 0).toLocaleString('en-IN')}</p>
              </div>
              <IndianRupee className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-bw-white/[0.45]">Invoice Payments</p>
                <p className="text-2xl font-bold">₹{(summary.invoice_payments || 0).toLocaleString('en-IN')}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-bw-white/[0.45]">Retainer Payments</p>
                <p className="text-2xl font-bold">₹{(summary.retainer_payments || 0).toLocaleString('en-IN')}</p>
              </div>
              <Wallet className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-bw-white/[0.45]">Unused Credits</p>
                <p className="text-2xl font-bold">₹{(summary.unused_credits || 0).toLocaleString('en-IN')}</p>
              </div>
              <CreditCard className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="all" className="space-y-4">
        <div className="flex justify-between items-center">
          <TabsList>
            <TabsTrigger value="all">All Payments</TabsTrigger>
            <TabsTrigger value="invoice">Invoice Payments</TabsTrigger>
            <TabsTrigger value="retainer">Retainer/Advances</TabsTrigger>
            <TabsTrigger value="credits">Customer Credits</TabsTrigger>
          </TabsList>
          
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-bw-white/[0.45]" />
              <Input
                className="pl-9 w-64"
                placeholder="Search payments..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                data-testid="payment-search"
              />
            </div>
            <Select value={filters.payment_mode || "all"} onValueChange={(v) => setFilters(prev => ({ ...prev, payment_mode: v === "all" ? "" : v }))}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Payment Mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Modes</SelectItem>
                <SelectItem value="cash">Cash</SelectItem>
                <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                <SelectItem value="card">Card</SelectItem>
                <SelectItem value="upi">UPI</SelectItem>
                <SelectItem value="cheque">Cheque</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon" onClick={() => { fetchPayments(); fetchSummary(); }}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* All Payments Tab */}
        <TabsContent value="all">
          <Card>
            <CardContent className="p-0">
              {/* Bulk Actions */}
              {selectedPayments.length > 0 && (
                <div className="p-3 bg-blue-50 border-b flex items-center gap-4">
                  <span className="text-sm font-medium">{selectedPayments.length} selected</span>
                  <Button size="sm" variant="destructive" onClick={bulkDelete}>
                    <Trash2 className="h-4 w-4 mr-1" /> Delete
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setSelectedPayments([])}>
                    Clear
                  </Button>
                </div>
              )}
              
              {/* Payments Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-bw-panel border-b">
                    <tr>
                      <th className="px-4 py-3 text-left w-10">
                        <Checkbox
                          checked={selectedPayments.length === payments.length && payments.length > 0}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedPayments(payments.map(p => p.payment_id));
                            } else {
                              setSelectedPayments([]);
                            }
                          }}
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Payment #</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Customer</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Invoice #</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Mode</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-bw-white/[0.45] uppercase">Amount</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-bw-white/[0.45] uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-bw-white/[0.45] uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {loading ? (
                      <tr>
                        <td colSpan={9} className="px-4 py-8 text-center text-bw-white/[0.45]">Loading...</td>
                      </tr>
                    ) : payments.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="px-4 py-8 text-center text-bw-white/[0.45]">No payments found</td>
                      </tr>
                    ) : (
                      payments.map((payment) => (
                        <tr key={payment.payment_id} className="hover:bg-bw-panel">
                          <td className="px-4 py-3">
                            <Checkbox
                              checked={selectedPayments.includes(payment.payment_id)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setSelectedPayments(prev => [...prev, payment.payment_id]);
                                } else {
                                  setSelectedPayments(prev => prev.filter(id => id !== payment.payment_id));
                                }
                              }}
                            />
                          </td>
                          <td className="px-4 py-3 text-sm">{payment.payment_date}</td>
                          <td className="px-4 py-3">
                            <button
                              className="text-bw-blue hover:underline font-medium"
                              onClick={() => viewPayment(payment.payment_id)}
                            >
                              {payment.payment_number}
                            </button>
                          </td>
                          <td className="px-4 py-3 text-sm">{payment.customer_name}</td>
                          <td className="px-4 py-3 text-sm">
                            {payment.invoice_numbers?.length > 0 ? (
                              payment.invoice_numbers.join(", ")
                            ) : (
                              <span className="text-bw-white/[0.45]">—</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 text-sm">
                              {getPaymentModeIcon(payment.payment_mode)}
                              <span className="capitalize">{payment.payment_mode.replace("_", " ")}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right font-medium">
                            ₹{payment.amount?.toLocaleString('en-IN')}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {getStatusBadge(payment)}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => viewPayment(payment.payment_id)}>
                                  <Eye className="h-4 w-4 mr-2" /> View Details
                                </DropdownMenuItem>
                                {payment.overpayment_amount > 0 && (
                                  <DropdownMenuItem onClick={() => {
                                    setSelectedPayment(payment);
                                    setRefundForm(prev => ({ ...prev, amount: payment.overpayment_amount }));
                                    setShowRefundDialog(true);
                                  }}>
                                    <ArrowUpRight className="h-4 w-4 mr-2" /> Refund
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuSeparator />
                                <DropdownMenuItem 
                                  className="text-red-600"
                                  onClick={() => deletePayment(payment.payment_id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" /> Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              {pagination.total > pagination.per_page && (
                <div className="p-4 border-t flex justify-between items-center">
                  <p className="text-sm text-bw-white/[0.45]">
                    Showing {((pagination.page - 1) * pagination.per_page) + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page === 1}
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page * pagination.per_page >= pagination.total}
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invoice Payments Tab */}
        <TabsContent value="invoice">
          <Card>
            <CardContent className="p-4">
              <p className="text-bw-white/[0.45]">Payments applied to specific invoices</p>
              {/* Reuse similar table structure with filtered data */}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Retainer Tab */}
        <TabsContent value="retainer">
          <Card>
            <CardContent className="p-4">
              <p className="text-bw-white/[0.45]">Advance payments and retainers</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Credits Tab */}
        <TabsContent value="credits">
          <Card>
            <CardHeader>
              <CardTitle>Customer Credits</CardTitle>
              <CardDescription>Available credits from overpayments and retainers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-bw-panel border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Customer</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Source</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-bw-white/[0.45] uppercase">Type</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-bw-white/[0.45] uppercase">Amount</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-bw-white/[0.45] uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {allCredits.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-bw-white/[0.45]">No available credits</td>
                      </tr>
                    ) : (
                      allCredits.map((credit) => (
                        <tr key={credit.credit_id} className="hover:bg-bw-panel">
                          <td className="px-4 py-3 font-medium">{credit.customer_name}</td>
                          <td className="px-4 py-3 text-sm">{credit.source_number}</td>
                          <td className="px-4 py-3">
                            <Badge variant="outline" className="capitalize">{credit.source_type}</Badge>
                          </td>
                          <td className="px-4 py-3 text-right font-medium text-green-600">
                            ₹{credit.amount?.toLocaleString('en-IN')}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <Badge className="bg-bw-volt/10 text-bw-volt border border-bw-volt/25">Available</Badge>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Record Payment Dialog */}
      <Dialog open={showRecordDialog} onOpenChange={setShowRecordDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
            <DialogDescription>Record a payment received from a customer</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Customer Selection */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Customer *</Label>
                <div className="relative">
                  <Input
                    value={customerSearch}
                    onChange={(e) => { setCustomerSearch(e.target.value); searchCustomers(e.target.value); }}
                    placeholder="Search customer..."
                    data-testid="payment-customer-search"
                  />
                  {customers.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-bw-panel border border-white/[0.13] rounded max-h-48 overflow-y-auto">
                      {customers.map(c => (
                        <div
                          key={c.contact_id}
                          className="px-3 py-2 hover:bg-white/5 cursor-pointer"
                          onClick={() => selectCustomer(c)}
                        >
                          <p className="font-medium">{c.name}</p>
                          <p className="text-xs text-bw-white/[0.45]">{c.company_name}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {selectedCustomer && (
                  <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                    <p className="font-medium">{selectedCustomer.name}</p>
                    <p className="text-xs text-bw-white/35">{selectedCustomer.email}</p>
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Payment Date</Label>
                  <Input
                    type="date"
                    value={paymentForm.payment_date}
                    onChange={(e) => setPaymentForm(prev => ({ ...prev, payment_date: e.target.value }))}
                  />
                </div>
                <div>
                  <Label>Amount Received *</Label>
                  <Input
                    type="number"
                    value={paymentForm.amount || ""}
                    onChange={(e) => setPaymentForm(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                    placeholder="0.00"
                    data-testid="payment-amount"
                  />
                </div>
              </div>
            </div>

            {/* Payment Details */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Payment Mode</Label>
                <Select
                  value={paymentForm.payment_mode}
                  onValueChange={(v) => setPaymentForm(prev => ({ ...prev, payment_mode: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                    <SelectItem value="card">Card</SelectItem>
                    <SelectItem value="upi">UPI</SelectItem>
                    <SelectItem value="cheque">Cheque</SelectItem>
                    <SelectItem value="online">Online</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Deposit To</Label>
                <Select
                  value={paymentForm.deposit_to_account}
                  onValueChange={(v) => setPaymentForm(prev => ({ ...prev, deposit_to_account: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Bank Account">Bank Account</SelectItem>
                    <SelectItem value="Petty Cash">Petty Cash</SelectItem>
                    <SelectItem value="Undeposited Funds">Undeposited Funds</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Reference #</Label>
                <Input
                  value={paymentForm.reference_number}
                  onChange={(e) => setPaymentForm(prev => ({ ...prev, reference_number: e.target.value }))}
                  placeholder="Transaction ID"
                />
              </div>
            </div>

            {/* Bank Charges */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Bank Charges</Label>
                <Input
                  type="number"
                  value={paymentForm.bank_charges || ""}
                  onChange={(e) => setPaymentForm(prev => ({ ...prev, bank_charges: parseFloat(e.target.value) || 0 }))}
                  placeholder="0.00"
                />
              </div>
              <div className="flex items-end gap-2">
                <Checkbox
                  id="tax_deducted"
                  checked={paymentForm.tax_deducted}
                  onCheckedChange={(checked) => setPaymentForm(prev => ({ ...prev, tax_deducted: checked }))}
                />
                <Label htmlFor="tax_deducted">Tax Deducted (TDS)</Label>
              </div>
              {paymentForm.tax_deducted && (
                <div>
                  <Label>Tax Amount</Label>
                  <Input
                    type="number"
                    value={paymentForm.tax_amount || ""}
                    onChange={(e) => setPaymentForm(prev => ({ ...prev, tax_amount: parseFloat(e.target.value) || 0 }))}
                  />
                </div>
              )}
            </div>

            {/* Invoice Allocation */}
            {selectedCustomer && customerInvoices.length > 0 && (
              <div>
                <Label className="text-base font-medium">Apply to Invoices</Label>
                <div className="mt-2 border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-bw-panel">
                      <tr>
                        <th className="px-3 py-2 text-left">Invoice Date</th>
                        <th className="px-3 py-2 text-left">Invoice #</th>
                        <th className="px-3 py-2 text-right">Invoice Amount</th>
                        <th className="px-3 py-2 text-right">Amount Due</th>
                        <th className="px-3 py-2 text-right">Payment</th>
                        <th className="px-3 py-2 text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {customerInvoices.map((inv) => {
                        const allocation = paymentForm.allocations.find(a => a.invoice_id === inv.invoice_id);
                        return (
                          <tr key={inv.invoice_id}>
                            <td className="px-3 py-2">{inv.date}</td>
                            <td className="px-3 py-2 font-medium">{inv.invoice_number}</td>
                            <td className="px-3 py-2 text-right">₹{inv.grand_total?.toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-right text-red-600">₹{inv.balance_due?.toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-right">
                              <Input
                                type="number"
                                className="w-28 text-right"
                                value={allocation?.amount || ""}
                                onChange={(e) => toggleInvoiceAllocation(inv, parseFloat(e.target.value) || 0)}
                                max={inv.balance_due}
                              />
                            </td>
                            <td className="px-3 py-2 text-center">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => payFullInvoice(inv)}
                              >
                                Pay in Full
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Available Credits */}
            {customerCredits.length > 0 && (
              <div className="p-3 bg-bw-green/[0.08] rounded-lg">
                <p className="text-sm font-medium text-green-700">
                  Available Credits: ₹{customerCredits.reduce((sum, c) => sum + c.amount, 0).toLocaleString('en-IN')}
                </p>
                <p className="text-xs text-green-600">Credits can be applied to invoices separately</p>
              </div>
            )}

            {/* Retainer Option */}
            {paymentForm.allocations.length === 0 && paymentForm.amount > 0 && (
              <div className="flex items-center gap-2 p-3 bg-bw-purple/[0.08] rounded-lg">
                <Checkbox
                  id="is_retainer"
                  checked={paymentForm.is_retainer}
                  onCheckedChange={(checked) => setPaymentForm(prev => ({ ...prev, is_retainer: checked }))}
                />
                <Label htmlFor="is_retainer" className="text-bw-purple">
                  Record as Retainer/Advance Payment (will be available as customer credit)
                </Label>
              </div>
            )}

            {/* Summary */}
            {paymentForm.amount > 0 && (
              <div className="p-4 bg-bw-panel rounded-lg">
                <div className="flex justify-between text-sm mb-2">
                  <span>Amount Received:</span>
                  <span className="font-medium">₹{paymentForm.amount.toLocaleString('en-IN')}</span>
                </div>
                {paymentForm.bank_charges > 0 && (
                  <div className="flex justify-between text-sm mb-2 text-bw-white/35">
                    <span>Bank Charges:</span>
                    <span>-₹{paymentForm.bank_charges.toLocaleString('en-IN')}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm mb-2">
                  <span>Amount Used for Payments:</span>
                  <span className="font-medium">₹{calculatePaymentTotals().totalAllocated.toLocaleString('en-IN')}</span>
                </div>
                {calculatePaymentTotals().excess > 0 && (
                  <div className="flex justify-between text-sm text-green-600">
                    <span>Excess Amount (will be credited):</span>
                    <span className="font-medium">₹{calculatePaymentTotals().excess.toLocaleString('en-IN')}</span>
                  </div>
                )}
              </div>
            )}

            {/* Notes */}
            <div>
              <Label>Notes</Label>
              <Textarea
                value={paymentForm.notes}
                onChange={(e) => setPaymentForm(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Internal notes..."
                rows={2}
              />
            </div>

            {/* Thank You */}
            <div className="flex items-center gap-2">
              <Checkbox
                id="send_thank_you"
                checked={paymentForm.send_thank_you}
                onCheckedChange={(checked) => setPaymentForm(prev => ({ ...prev, send_thank_you: checked }))}
              />
              <Label htmlFor="send_thank_you">Send thank you email to customer</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowRecordDialog(false); resetPaymentForm(); }}>
              Cancel
            </Button>
            <Button onClick={recordPayment} data-testid="save-payment-btn">
              <CheckCircle2 className="h-4 w-4 mr-2" /> Record Payment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payment Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Payment Details</DialogTitle>
          </DialogHeader>
          
          {selectedPayment && (
            <div className="space-y-4">
              {/* Header Info */}
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold">{selectedPayment.payment_number}</h3>
                  <p className="text-bw-white/[0.45]">{selectedPayment.customer_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-600">₹{selectedPayment.amount?.toLocaleString('en-IN')}</p>
                  {getStatusBadge(selectedPayment)}
                </div>
              </div>

              <Separator />

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-bw-white/[0.45]">Payment Date</p>
                  <p className="font-medium">{selectedPayment.payment_date}</p>
                </div>
                <div>
                  <p className="text-bw-white/[0.45]">Payment Mode</p>
                  <p className="font-medium capitalize flex items-center gap-1">
                    {getPaymentModeIcon(selectedPayment.payment_mode)}
                    {selectedPayment.payment_mode?.replace("_", " ")}
                  </p>
                </div>
                <div>
                  <p className="text-bw-white/[0.45]">Deposit Account</p>
                  <p className="font-medium">{selectedPayment.deposit_to_account}</p>
                </div>
                <div>
                  <p className="text-bw-white/[0.45]">Reference #</p>
                  <p className="font-medium">{selectedPayment.reference_number || "—"}</p>
                </div>
              </div>

              {/* Applied Invoices */}
              {selectedPayment.invoice_details?.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Applied to Invoices</h4>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-bw-panel">
                        <tr>
                          <th className="px-3 py-2 text-left">Invoice #</th>
                          <th className="px-3 py-2 text-left">Date</th>
                          <th className="px-3 py-2 text-right">Invoice Total</th>
                          <th className="px-3 py-2 text-right">Amount Applied</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {selectedPayment.invoice_details.map((inv, idx) => (
                          <tr key={idx}>
                            <td className="px-3 py-2 font-medium">{inv.invoice_number}</td>
                            <td className="px-3 py-2">{inv.date}</td>
                            <td className="px-3 py-2 text-right">₹{inv.grand_total?.toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-right text-green-600">₹{inv.amount_applied?.toLocaleString('en-IN')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Overpayment */}
              {selectedPayment.overpayment_amount > 0 && (
                <div className="p-3 bg-bw-green/[0.08] rounded-lg flex justify-between items-center">
                  <div>
                    <p className="font-medium text-green-700">Overpayment Credited</p>
                    <p className="text-sm text-green-600">Available for future invoices</p>
                  </div>
                  <p className="text-xl font-bold text-green-600">₹{selectedPayment.overpayment_amount?.toLocaleString('en-IN')}</p>
                </div>
              )}

              {/* Notes */}
              {selectedPayment.notes && (
                <div>
                  <h4 className="font-medium mb-1">Notes</h4>
                  <p className="text-sm text-bw-white/35">{selectedPayment.notes}</p>
                </div>
              )}

              <Separator />

              {/* Actions */}
              <div className="flex justify-between">
                <Button variant="destructive" onClick={() => deletePayment(selectedPayment.payment_id)}>
                  <Trash2 className="h-4 w-4 mr-2" /> Delete
                </Button>
                {selectedPayment.overpayment_amount > 0 && (
                  <Button variant="outline" onClick={() => {
                    setRefundForm(prev => ({ ...prev, amount: selectedPayment.overpayment_amount }));
                    setShowRefundDialog(true);
                  }}>
                    <ArrowUpRight className="h-4 w-4 mr-2" /> Refund Overpayment
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Refund Dialog */}
      <Dialog open={showRefundDialog} onOpenChange={setShowRefundDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Process Refund</DialogTitle>
            <DialogDescription>Refund overpayment or credit to customer</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Refund Amount</Label>
              <Input
                type="number"
                value={refundForm.amount}
                onChange={(e) => setRefundForm(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
              />
            </div>
            <div>
              <Label>Refund Date</Label>
              <Input
                type="date"
                value={refundForm.refund_date}
                onChange={(e) => setRefundForm(prev => ({ ...prev, refund_date: e.target.value }))}
              />
            </div>
            <div>
              <Label>Payment Mode</Label>
              <Select
                value={refundForm.payment_mode}
                onValueChange={(v) => setRefundForm(prev => ({ ...prev, payment_mode: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="cheque">Cheque</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Reference #</Label>
              <Input
                value={refundForm.reference_number}
                onChange={(e) => setRefundForm(prev => ({ ...prev, reference_number: e.target.value }))}
              />
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea
                value={refundForm.notes}
                onChange={(e) => setRefundForm(prev => ({ ...prev, notes: e.target.value }))}
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRefundDialog(false)}>Cancel</Button>
            <Button onClick={processRefund}>Process Refund</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
