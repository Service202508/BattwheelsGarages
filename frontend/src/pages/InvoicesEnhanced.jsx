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
  TrendingUp, TrendingDown, Wallet, PieChart, ExternalLink, Edit, Share2,
  Paperclip, MessageSquare, Printer, History, Link, X, Upload, Save, Link2, Loader2,
  FileCheck, QrCode, XCircle, Info
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const statusColors = {
  draft: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  sent: "bg-[rgba(59,158,255,0.10)] text-[#3B9EFF] border border-[rgba(59,158,255,0.25)]",
  viewed: "bg-[rgba(139,92,246,0.10)] text-[#8B5CF6] border border-[rgba(139,92,246,0.25)]",
  partially_paid: "bg-[rgba(234,179,8,0.10)] text-[#EAB308] border border-[rgba(234,179,8,0.25)]",
  paid: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  overdue: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  void: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.25)] border border-[rgba(255,255,255,0.08)]",
  written_off: "bg-[rgba(255,140,0,0.10)] text-[#FF8C00] border border-[rgba(255,140,0,0.25)]"
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
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [showAttachmentDialog, setShowAttachmentDialog] = useState(false);
  const [showCommentsDialog, setShowCommentsDialog] = useState(false);
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [detailViewMode, setDetailViewMode] = useState("details"); // details or pdf
  
  // Share link state
  const [shareLink, setShareLink] = useState(null);
  const [shareLoading, setShareLoading] = useState(false);
  const [shareConfig, setShareConfig] = useState({
    expiry_days: 30,
    allow_payment: true,
    password_protected: false,
    password: ""
  });
  
  // Attachments state
  const [attachments, setAttachments] = useState([]);
  const [uploadingAttachment, setUploadingAttachment] = useState(false);
  
  // Comments state
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  
  // History state
  const [history, setHistory] = useState([]);
  
  // Send email state
  const [sendEmail, setSendEmail] = useState("");
  const [sendMessage, setSendMessage] = useState("");
  
  // Form state
  const initialInvoiceData = {
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
  };
  
  const [newInvoice, setNewInvoice] = useState(initialInvoiceData);
  
  // Auto-save for Invoice form
  const invoicePersistence = useFormPersistence(
    'invoice_new',
    newInvoice,
    initialInvoiceData,
    {
      enabled: showCreateDialog,
      isDialogOpen: showCreateDialog,
      setFormData: setNewInvoice,
      debounceMs: 2000,
      entityName: 'Invoice'
    }
  );
  
  // Edit form state
  const [editInvoice, setEditInvoice] = useState(null);
  
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
        invoicePersistence.onSuccessfulSave();
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
    // Check if IRN is required but not generated
    const invoice = invoices.find(i => i.invoice_id === invoiceId) || selectedInvoice;
    if (einvoiceEnabled && isB2BInvoice(invoice) && !invoice.irn) {
      toast.error("IRN registration required before sending. Generate IRN first.");
      return;
    }
    
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

  const handleApplyCredit = async (creditId, amount) => {
    if (!confirm(`Apply credit of ₹${amount.toLocaleString("en-IN")} to this invoice?`)) return;
    try {
      const res = await fetch(`${API}/payments-received/apply-credit`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          credit_id: creditId,
          invoice_id: selectedInvoice.invoice_id,
          amount: amount
        })
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(`Credit applied. New balance: ₹${data.new_invoice_balance?.toLocaleString("en-IN")}`);
        fetchInvoiceDetail(selectedInvoice.invoice_id);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to apply credit");
      }
    } catch (e) {
      toast.error("Error applying credit");
    }
  };

  // Online Payment - Razorpay
  const [razorpayLoading, setRazorpayLoading] = useState(false);
  const [razorpayConfigured, setRazorpayConfigured] = useState(false);
  
  // Check Razorpay config on mount
  useEffect(() => {
    const checkRazorpayConfig = async () => {
      try {
        const res = await fetch(`${API}/payments/config`, { headers });
        const data = await res.json();
        setRazorpayConfigured(data.configured || false);
      } catch (e) {
        console.error("Failed to check Razorpay config:", e);
      }
    };
    checkRazorpayConfig();
  }, []);
  
  const handleCreatePaymentLink = async (invoiceId) => {
    setRazorpayLoading(true);
    try {
      const res = await fetch(`${API}/payments/create-payment-link/${invoiceId}`, {
        method: "POST",
        headers,
      });
      const data = await res.json();
      if (data.code === 0 && data.payment_link?.short_url) {
        toast.success("Payment link created!");
        // Update invoice with the payment link
        setSelectedInvoice(prev => ({
          ...prev,
          payment_link_url: data.payment_link.short_url,
          payment_link_id: data.payment_link.id,
          has_payment_link: true
        }));
        // Copy to clipboard
        await navigator.clipboard.writeText(data.payment_link.short_url);
        toast.success("Payment link copied to clipboard!");
        // Optionally open in new tab
        window.open(data.payment_link.short_url, "_blank");
      } else {
        toast.error(data.detail || "Failed to create payment link");
      }
    } catch (e) {
      toast.error("Error creating payment link. Please configure Razorpay in Organization Settings.");
    } finally {
      setRazorpayLoading(false);
    }
  };
  
  // Create Razorpay order for checkout modal
  const handleRazorpayCheckout = async (invoice) => {
    setRazorpayLoading(true);
    try {
      // Create order
      const res = await fetch(`${API}/payments/create-order`, {
        method: "POST",
        headers,
        body: JSON.stringify({ invoice_id: invoice.invoice_id })
      });
      const data = await res.json();
      
      if (data.code !== 0) {
        toast.error(data.detail || "Failed to create payment order");
        return;
      }
      
      // Load Razorpay checkout
      const options = {
        key: data.key_id,
        amount: data.order.amount,
        currency: data.order.currency || "INR",
        name: "Battwheels OS",
        description: `Payment for Invoice ${invoice.invoice_number}`,
        order_id: data.order.id,
        handler: async function(response) {
          // Verify payment
          try {
            const verifyRes = await fetch(`${API}/payments/verify`, {
              method: "POST",
              headers,
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
                invoice_id: invoice.invoice_id
              })
            });
            const verifyData = await verifyRes.json();
            if (verifyData.code === 0) {
              toast.success("Payment successful! Invoice updated.");
              fetchData();
              setShowDetailDialog(false);
            } else {
              toast.error("Payment verification failed");
            }
          } catch (e) {
            toast.error("Payment verification error");
          }
        },
        prefill: {
          name: data.customer_name || invoice.customer_name,
          email: data.customer_email || invoice.customer_email,
          contact: data.customer_phone || ""
        },
        theme: {
          color: "#C8FF00"
        },
        modal: {
          ondismiss: function() {
            setRazorpayLoading(false);
          }
        }
      };
      
      // Check if Razorpay is loaded
      if (typeof window.Razorpay === "undefined") {
        // Load Razorpay script
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = () => {
          const rzp = new window.Razorpay(options);
          rzp.open();
        };
        document.body.appendChild(script);
      } else {
        const rzp = new window.Razorpay(options);
        rzp.open();
      }
    } catch (e) {
      toast.error("Error initiating payment");
    } finally {
      setRazorpayLoading(false);
    }
  };

  // Check for payment return
  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    const paymentSuccess = searchParams.get("payment_success");
    const paymentCancelled = searchParams.get("payment_cancelled");
    
    if (sessionId && paymentSuccess) {
      // Poll for payment status
      const pollPaymentStatus = async () => {
        try {
          const res = await fetch(`${API}/invoice-payments/status/${sessionId}`, { headers });
          const data = await res.json();
          if (data.payment_status === "paid") {
            toast.success("Payment successful! Invoice updated.");
            // Clear URL params
            navigate("/invoices-enhanced", { replace: true });
            fetchData();
          } else if (data.status === "expired") {
            toast.error("Payment session expired");
            navigate("/invoices-enhanced", { replace: true });
          } else {
            // Continue polling
            setTimeout(pollPaymentStatus, 2000);
          }
        } catch (e) {
          console.error("Payment status check failed:", e);
        }
      };
      pollPaymentStatus();
    } else if (paymentCancelled) {
      toast.info("Payment cancelled");
      navigate("/invoices-enhanced", { replace: true });
    }
  }, [searchParams]);

  // ==================== E-INVOICE / IRN STATE ====================
  const [einvoiceEnabled, setEinvoiceEnabled] = useState(false);
  const [irnLoading, setIrnLoading] = useState(false);
  const [irnValidationErrors, setIrnValidationErrors] = useState([]);
  const [showIrnCancelDialog, setShowIrnCancelDialog] = useState(false);
  const [irnCancelReason, setIrnCancelReason] = useState("");
  const [irnCancelRemarks, setIrnCancelRemarks] = useState("");
  const [irnQrCode, setIrnQrCode] = useState(null);
  
  // Check E-Invoice config on mount
  useEffect(() => {
    const checkEinvoiceConfig = async () => {
      try {
        const res = await fetch(`${API}/einvoice/eligibility`, { headers });
        const data = await res.json();
        setEinvoiceEnabled(data.eligible || false);
      } catch (e) {
        console.error("Failed to check E-Invoice config:", e);
      }
    };
    checkEinvoiceConfig();
  }, []);
  
  // Check if invoice is B2B (has buyer GSTIN)
  const isB2BInvoice = (invoice) => {
    return invoice && invoice.customer_gstin && invoice.customer_gstin !== "URP" && invoice.customer_gstin.length === 15;
  };
  
  // Check if invoice needs IRN
  const needsIRN = (invoice) => {
    return einvoiceEnabled && 
           isB2BInvoice(invoice) && 
           invoice.status !== "draft" && 
           !invoice.irn;
  };
  
  // Check if IRN is within cancellation window (24 hours)
  const canCancelIRN = (invoice) => {
    if (!invoice.irn || !invoice.irn_generated_at) return false;
    const generatedAt = new Date(invoice.irn_generated_at);
    const now = new Date();
    const hoursDiff = (now - generatedAt) / (1000 * 60 * 60);
    return hoursDiff < 24;
  };
  
  // Validate invoice for E-Invoice compliance
  const validateForEInvoice = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/einvoice/validate-invoice/${invoiceId}`, { headers });
      const data = await res.json();
      return data;
    } catch (e) {
      return { is_valid: false, errors: ["Failed to validate invoice"] };
    }
  };
  
  // Generate IRN for invoice
  const handleGenerateIRN = async (invoiceId) => {
    setIrnLoading(true);
    setIrnValidationErrors([]);
    
    try {
      // First validate
      const validation = await validateForEInvoice(invoiceId);
      if (!validation.is_valid) {
        setIrnValidationErrors(validation.errors || []);
        toast.error("Invoice validation failed. Fix the errors and try again.");
        setIrnLoading(false);
        return;
      }
      
      // Generate IRN
      const res = await fetch(`${API}/einvoice/generate-irn`, {
        method: "POST",
        headers,
        body: JSON.stringify({ invoice_id: invoiceId })
      });
      
      const data = await res.json();
      
      if (data.code === 0 && data.success) {
        toast.success("IRN generated successfully!");
        // Refresh invoice details
        fetchInvoiceDetail(invoiceId);
        fetchData();
        // Fetch QR code
        fetchIrnQrCode(invoiceId);
      } else if (data.skip_irn) {
        toast.info(data.message || "E-Invoice not required for this invoice");
      } else {
        setIrnValidationErrors(data.errors || [data.message || "IRN generation failed"]);
        toast.error("IRN generation failed");
      }
    } catch (e) {
      toast.error("Failed to generate IRN");
      console.error("IRN generation error:", e);
    } finally {
      setIrnLoading(false);
    }
  };
  
  // Cancel IRN (5A)
  const handleCancelIRN = async () => {
    if (!selectedInvoice?.irn || !irnCancelReason) {
      toast.error("Please select a cancellation reason");
      return;
    }
    
    setIrnLoading(true);
    try {
      const res = await fetch(`${API}/einvoice/cancel-irn`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          irn: selectedInvoice.irn,
          reason: irnCancelReason,
          remarks: irnCancelRemarks
        })
      });
      
      const data = await res.json();
      
      if (data.code === 0 && data.success) {
        toast.success("IRN cancelled successfully. Raise a new invoice with a new invoice number.", {
          duration: 5000
        });
        setShowIrnCancelDialog(false);
        setIrnCancelReason("");
        setIrnCancelRemarks("");
        fetchInvoiceDetail(selectedInvoice.invoice_id);
        fetchData();
      } else {
        // Enhanced error handling (5A)
        const errorMsg = data.message || "Failed to cancel IRN";
        if (errorMsg.toLowerCase().includes("24 hour") || errorMsg.toLowerCase().includes("window") || errorMsg.toLowerCase().includes("expired")) {
          toast.error("IRN cancellation window has expired. Contact your CA or GST consultant for amendment procedures.", {
            duration: 8000
          });
        } else {
          // Display exact IRP error message for resolution
          toast.error(errorMsg, { duration: 6000 });
        }
      }
    } catch (e) {
      toast.error("Failed to cancel IRN. Please try again.");
    } finally {
      setIrnLoading(false);
    }
  };
  
  // Fetch IRN QR code
  const fetchIrnQrCode = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/einvoice/qr-code/${invoiceId}`, { headers });
      const data = await res.json();
      if (data.has_qr) {
        setIrnQrCode(data.qr_code_data_uri);
      } else {
        setIrnQrCode(null);
      }
    } catch (e) {
      console.error("Failed to fetch QR code:", e);
      setIrnQrCode(null);
    }
  };
  
  // Fetch QR code when invoice with IRN is selected
  useEffect(() => {
    if (selectedInvoice?.irn && selectedInvoice?.irn_status === "registered") {
      fetchIrnQrCode(selectedInvoice.invoice_id);
    } else {
      setIrnQrCode(null);
    }
  }, [selectedInvoice?.irn]);

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
    setNewInvoice(initialInvoiceData);
  };

  // ========================= EDIT INVOICE =========================
  const handleOpenEdit = (invoice) => {
    setEditInvoice({
      invoice_id: invoice.invoice_id,
      reference_number: invoice.reference_number || "",
      invoice_date: invoice.invoice_date || "",
      due_date: invoice.due_date || "",
      payment_terms: invoice.payment_terms || 30,
      line_items: invoice.line_items || [],
      discount_type: invoice.discount_type || "percentage",
      discount_value: invoice.discount_value || 0,
      shipping_charge: invoice.shipping_charge || 0,
      customer_notes: invoice.customer_notes || "",
      terms_conditions: invoice.terms_conditions || ""
    });
    setShowEditDialog(true);
  };

  const updateEditLineItem = (index, field, value) => {
    setEditInvoice(prev => {
      const updated = [...prev.line_items];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, line_items: updated };
    });
  };

  const addEditLineItem = () => {
    setEditInvoice(prev => ({
      ...prev,
      line_items: [...prev.line_items, { name: "", description: "", quantity: 1, rate: 0, tax_rate: 18 }]
    }));
  };

  const removeEditLineItem = (index) => {
    setEditInvoice(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const handleUpdateInvoice = async () => {
    if (!editInvoice) return;
    try {
      const res = await fetch(`${API}/invoices-enhanced/${editInvoice.invoice_id}`, {
        method: "PUT",
        headers,
        body: JSON.stringify(editInvoice)
      });
      if (res.ok) {
        toast.success("Invoice updated successfully");
        setShowEditDialog(false);
        fetchInvoiceDetail(editInvoice.invoice_id);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to update invoice");
      }
    } catch (e) {
      toast.error("Error updating invoice");
    }
  };

  // ========================= PDF DOWNLOAD =========================
  const handleDownloadPDF = async (invoiceId) => {
    try {
      toast.info("Generating PDF...");
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/pdf`, { headers });
      
      if (res.headers.get('content-type')?.includes('application/pdf')) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `Invoice_${invoiceId}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
        toast.success("PDF downloaded!");
      } else {
        // Might be HTML for print
        const html = await res.text();
        const printWindow = window.open("", "_blank");
        printWindow.document.write(html);
        printWindow.document.close();
        toast.info("PDF preview opened in new window");
      }
    } catch (e) {
      console.error("PDF error:", e);
      toast.error("Failed to generate PDF");
    }
  };

  // ========================= SHARE LINK =========================
  const handleCreateShareLink = async () => {
    if (!selectedInvoice) return;
    setShareLoading(true);
    try {
      const res = await fetch(`${API}/invoices-enhanced/${selectedInvoice.invoice_id}/share`, {
        method: "POST",
        headers,
        body: JSON.stringify(shareConfig)
      });
      const data = await res.json();
      if (res.ok) {
        const fullUrl = `${window.location.origin}${data.share_link.public_url}`;
        setShareLink({ ...data.share_link, full_url: fullUrl });
        toast.success("Share link created!");
      } else {
        toast.error(data.detail || "Failed to create share link");
      }
    } catch (e) {
      toast.error("Error creating share link");
    } finally {
      setShareLoading(false);
    }
  };

  const copyShareLink = () => {
    if (shareLink?.full_url) {
      navigator.clipboard.writeText(shareLink.full_url);
      toast.success("Link copied to clipboard!");
    }
  };

  // ========================= ATTACHMENTS =========================
  const fetchAttachments = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/attachments`, { headers });
      const data = await res.json();
      setAttachments(data.attachments || []);
    } catch (e) {
      console.error("Failed to fetch attachments:", e);
    }
  };

  const handleUploadAttachment = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedInvoice) return;
    
    if (file.size > 10 * 1024 * 1024) {
      toast.error("File size exceeds 10MB limit");
      return;
    }
    
    setUploadingAttachment(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const res = await fetch(`${API}/invoices-enhanced/${selectedInvoice.invoice_id}/attachments`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Attachment uploaded");
        fetchAttachments(selectedInvoice.invoice_id);
      } else {
        toast.error(data.detail || "Failed to upload");
      }
    } catch (e) {
      toast.error("Error uploading attachment");
    } finally {
      setUploadingAttachment(false);
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!confirm("Delete this attachment?")) return;
    try {
      const res = await fetch(`${API}/invoices-enhanced/${selectedInvoice.invoice_id}/attachments/${attachmentId}`, {
        method: "DELETE",
        headers
      });
      if (res.ok) {
        toast.success("Attachment deleted");
        fetchAttachments(selectedInvoice.invoice_id);
      } else {
        toast.error("Failed to delete attachment");
      }
    } catch (e) {
      toast.error("Error deleting attachment");
    }
  };

  const downloadAttachment = (attachmentId, filename) => {
    const url = `${API}/invoices-enhanced/${selectedInvoice.invoice_id}/attachments/${attachmentId}`;
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
  };

  // ========================= COMMENTS =========================
  const fetchComments = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/comments`, { headers });
      const data = await res.json();
      setComments(data.comments || []);
    } catch (e) {
      console.error("Failed to fetch comments:", e);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim() || !selectedInvoice) return;
    try {
      const res = await fetch(`${API}/invoices-enhanced/${selectedInvoice.invoice_id}/comments`, {
        method: "POST",
        headers,
        body: JSON.stringify({ comment: newComment, is_internal: true })
      });
      if (res.ok) {
        toast.success("Comment added");
        setNewComment("");
        fetchComments(selectedInvoice.invoice_id);
      } else {
        toast.error("Failed to add comment");
      }
    } catch (e) {
      toast.error("Error adding comment");
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!confirm("Delete this comment?")) return;
    try {
      const res = await fetch(`${API}/invoices-enhanced/${selectedInvoice.invoice_id}/comments/${commentId}`, {
        method: "DELETE",
        headers
      });
      if (res.ok) {
        toast.success("Comment deleted");
        fetchComments(selectedInvoice.invoice_id);
      }
    } catch (e) {
      toast.error("Error deleting comment");
    }
  };

  // ========================= HISTORY =========================
  const fetchHistory = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoices-enhanced/${invoiceId}/history`, { headers });
      const data = await res.json();
      setHistory(data.history || []);
    } catch (e) {
      console.error("Failed to fetch history:", e);
    }
  };

  // ========================= SEND EMAIL =========================
  const handleSendInvoiceEmail = async () => {
    if (!selectedInvoice || !sendEmail) {
      toast.error("Please enter email address");
      return;
    }
    try {
      const url = `${API}/invoices-enhanced/${selectedInvoice.invoice_id}/send?email_to=${encodeURIComponent(sendEmail)}&message=${encodeURIComponent(sendMessage)}`;
      const res = await fetch(url, { method: "POST", headers });
      if (res.ok) {
        toast.success("Invoice sent!");
        setShowSendDialog(false);
        setSendEmail("");
        setSendMessage("");
        fetchInvoiceDetail(selectedInvoice.invoice_id);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to send invoice");
      }
    } catch (e) {
      toast.error("Error sending invoice");
    }
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
            <Button onClick={() => setShowCreateDialog(true)} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2" data-testid="new-invoice-btn">
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
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.25)]" />
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
            <Card><CardContent className="py-12 text-center"><RefreshCw className="h-8 w-8 animate-spin mx-auto text-[rgba(244,246,240,0.25)]" /></CardContent></Card>
          ) : invoices.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
                <Receipt className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
                <p>No invoices found</p>
                <Button onClick={() => setShowCreateDialog(true)} className="mt-4 bg-[#C8FF00] text-[#080C0F] font-bold">Create First Invoice</Button>
              </CardContent>
            </Card>
          ) : (
            <div className="bg-[#111820] rounded-lg border overflow-hidden">
              <table className="w-full">
                <thead className="bg-[#111820] text-xs text-[rgba(244,246,240,0.45)] uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Invoice #</th>
                    <th className="px-4 py-3 text-left">Customer</th>
                    <th className="px-4 py-3 text-left">Date</th>
                    <th className="px-4 py-3 text-left">Due Date</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                    <th className="px-4 py-3 text-right">Balance</th>
                    <th className="px-4 py-3 text-center">Status</th>
                    {einvoiceEnabled && <th className="px-4 py-3 text-center">IRN</th>}
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-[rgba(255,255,255,0.04)]">
                  {invoices.map(inv => (
                    <tr key={inv.invoice_id} className="hover:bg-[#111820] cursor-pointer" onClick={() => fetchInvoiceDetail(inv.invoice_id)} data-testid={`invoice-row-${inv.invoice_id}`}>
                      <td className="px-4 py-3 font-medium text-[#3B9EFF]">{inv.invoice_number}</td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium">{inv.customer_name}</p>
                          {inv.reference_number && <p className="text-xs text-[rgba(244,246,240,0.45)]">Ref: {inv.reference_number}</p>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">{formatDate(inv.invoice_date)}</td>
                      <td className="px-4 py-3 text-sm">{formatDate(inv.due_date)}</td>
                      <td className="px-4 py-3 text-right font-medium">{formatCurrency(inv.grand_total)}</td>
                      <td className="px-4 py-3 text-right">
                        <span className={inv.balance_due > 0 ? "text-[#FF3B2F] font-medium" : "text-[#22C55E]"}>
                          {formatCurrency(inv.balance_due)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={statusColors[inv.status] || "bg-[rgba(255,255,255,0.05)]"}>{statusLabels[inv.status] || inv.status}</Badge>
                      </td>
                      {einvoiceEnabled && (
                        <td className="px-4 py-3 text-center">
                          {inv.irn && inv.irn_status === "registered" ? (
                            <Badge className="bg-[rgba(34,197,94,0.20)] text-green-400 border-green-500/30 text-xs">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              IRN ✓
                            </Badge>
                          ) : inv.irn_status === "cancelled" ? (
                            <Badge className="bg-[rgba(255,59,47,0.15)] text-[#FF3B2F] border-red-500/30 text-xs">
                              Cancelled
                            </Badge>
                          ) : isB2BInvoice(inv) && inv.status !== "draft" ? (
                            <Badge 
                              className="bg-[rgba(255,140,0,0.15)] text-[#FF8C00] border-orange-500/30 text-xs cursor-pointer hover:bg-[rgba(255,140,0,0.25)]"
                              onClick={(e) => { e.stopPropagation(); fetchInvoiceDetail(inv.invoice_id); }}
                            >
                              IRN Pending
                            </Badge>
                          ) : null}
                        </td>
                      )}
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
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]"><CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-300" /><p>No overdue invoices!</p></CardContent></Card>
          ) : (
            <div className="grid gap-4">
              {invoices.filter(i => i.status === "overdue").map(inv => (
                <Card key={inv.invoice_id} className="border-red-200 bg-[rgba(255,59,47,0.08)] cursor-pointer hover:border-[rgba(200,255,0,0.2)]" onClick={() => fetchInvoiceDetail(inv.invoice_id)}>
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold text-lg">{inv.invoice_number}</p>
                        <p className="text-[rgba(244,246,240,0.45)]">{inv.customer_name}</p>
                        <p className="text-sm text-[#FF3B2F]">Due: {formatDate(inv.due_date)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-[#FF3B2F]">{formatCurrency(inv.balance_due)}</p>
                        <Badge className="bg-red-100 text-[#FF3B2F]">Overdue</Badge>
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
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]"><FileText className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" /><p>No draft invoices</p></CardContent></Card>
          ) : (
            <div className="grid gap-4">
              {invoices.filter(i => i.status === "draft").map(inv => (
                <Card key={inv.invoice_id} className="cursor-pointer hover:border-[rgba(200,255,0,0.2)]" onClick={() => fetchInvoiceDetail(inv.invoice_id)}>
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold text-lg">{inv.invoice_number}</p>
                        <p className="text-[rgba(244,246,240,0.45)]">{inv.customer_name}</p>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">Created: {formatDate(inv.created_time)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold">{formatCurrency(inv.grand_total)}</p>
                        <Badge className="bg-[rgba(255,255,255,0.05)] text-[#F4F6F0]">Draft</Badge>
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
      <Dialog 
        open={showCreateDialog} 
        onOpenChange={(open) => {
          if (!open && invoicePersistence.isDirty) {
            invoicePersistence.setShowCloseConfirm(true);
          } else {
            if (!open) {
              invoicePersistence.clearSavedData();
              resetForm();
            }
            setShowCreateDialog(open);
          }
        }}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>Create New Invoice</DialogTitle>
                <DialogDescription>Create a new invoice for a customer</DialogDescription>
              </div>
              <AutoSaveIndicator 
                lastSaved={invoicePersistence.lastSaved} 
                isSaving={invoicePersistence.isSaving} 
                isDirty={invoicePersistence.isDirty} 
              />
            </div>
          </DialogHeader>
          
          <DraftRecoveryBanner
            show={invoicePersistence.showRecoveryBanner}
            savedAt={invoicePersistence.savedDraftInfo?.timestamp}
            onRestore={invoicePersistence.handleRestoreDraft}
            onDiscard={invoicePersistence.handleDiscardDraft}
          />
          
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
                  <div key={idx} className="grid grid-cols-12 gap-2 items-end bg-[#111820] p-3 rounded-lg">
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
              
              <div className="bg-[#111820] p-4 rounded-lg space-y-2">
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
                <div className="flex justify-between text-lg font-bold"><span>Total:</span><span className="text-[#22C55E]">{formatCurrency(calculateTotal())}</span></div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="send-email" checked={newInvoice.send_email} onChange={(e) => setNewInvoice({ ...newInvoice, send_email: e.target.checked })} />
              <Label htmlFor="send-email">Send invoice via email after creating</Label>
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                if (invoicePersistence.isDirty) {
                  invoicePersistence.setShowCloseConfirm(true);
                } else {
                  setShowCreateDialog(false);
                }
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateInvoice} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-invoice-submit">Create Invoice</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Invoice Unsaved Changes Dialog */}
      <FormCloseConfirmDialog
        open={invoicePersistence.showCloseConfirm}
        onClose={() => invoicePersistence.setShowCloseConfirm(false)}
        onSave={handleCreateInvoice}
        onDiscard={() => {
          invoicePersistence.clearSavedData();
          resetForm();
          setShowCreateDialog(false);
        }}
        entityName="Invoice"
      />

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
                      <p className="text-sm text-[#FF3B2F]">Balance: {formatCurrency(selectedInvoice.balance_due)}</p>
                    )}
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-6 py-4">
                {/* Info Grid */}
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div><span className="text-[rgba(244,246,240,0.45)]">Invoice Date:</span><br/><span className="font-medium">{formatDate(selectedInvoice.invoice_date)}</span></div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Due Date:</span><br/><span className="font-medium">{formatDate(selectedInvoice.due_date)}</span></div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Reference:</span><br/><span className="font-medium">{selectedInvoice.reference_number || "-"}</span></div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Payment Terms:</span><br/><span className="font-medium">{selectedInvoice.payment_terms} days</span></div>
                </div>

                {/* ==================== E-INVOICE / IRN STATUS PANEL ==================== */}
                {isB2BInvoice(selectedInvoice) && einvoiceEnabled && selectedInvoice.status !== "draft" && (
                  <>
                    <Separator />
                    {/* State 1: IRN Pending */}
                    {needsIRN(selectedInvoice) && !irnLoading && (
                      <div className="p-4 bg-[rgba(255,140,0,0.08)] border border-[rgba(255,140,0,0.25)] border-l-[3px] border-l-[#FF8C00] rounded">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className="w-3 h-3 rounded-full bg-[#FF8C00] animate-pulse mt-1" />
                            <div>
                              <h4 className="font-medium text-[#FF8C00]">IRN Registration Pending</h4>
                              <p className="text-sm text-[rgba(244,246,240,0.65)] mt-1">
                                This B2B invoice requires IRN registration before dispatch
                              </p>
                              <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                                Invoice date: {formatDate(selectedInvoice.invoice_date)} · Must register within 3 days of invoice date
                              </p>
                            </div>
                          </div>
                          <Button 
                            onClick={() => handleGenerateIRN(selectedInvoice.invoice_id)}
                            className="bg-[#C8FF00] hover:bg-[#a8d900] text-[#080C0F]"
                            data-testid="generate-irn-btn"
                          >
                            <FileCheck className="h-4 w-4 mr-2" />
                            Generate IRN Now
                          </Button>
                        </div>
                        
                        {/* Validation Errors */}
                        {irnValidationErrors.length > 0 && (
                          <div className="mt-4 p-3 bg-[rgba(255,59,47,0.08)] border border-[rgba(255,59,47,0.25)] border-l-[3px] border-l-[#FF3B2F] rounded">
                            <h5 className="font-medium text-[#FF3B2F] text-sm">Cannot Generate IRN — Validation Failed</h5>
                            <ul className="mt-2 space-y-1">
                              {irnValidationErrors.map((error, idx) => (
                                <li key={idx} className="text-sm text-[rgba(244,246,240,0.65)] flex items-start gap-2">
                                  <XCircle className="h-4 w-4 text-[#FF3B2F] mt-0.5 flex-shrink-0" />
                                  {error}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* State 2: IRN Generating (Loading) */}
                    {irnLoading && (
                      <div className="p-6 bg-[rgba(200,255,0,0.04)] border border-[rgba(200,255,0,0.15)] rounded">
                        <div className="flex flex-col items-center justify-center gap-3">
                          <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
                          <div className="text-center">
                            <p className="font-medium">Submitting to IRP portal...</p>
                            <p className="text-sm text-[rgba(244,246,240,0.45)]">This usually takes 5–10 seconds</p>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* State 3: IRN Registered */}
                    {selectedInvoice.irn && selectedInvoice.irn_status === "registered" && !irnLoading && (
                      <div className="p-4 bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.25)] border-l-[3px] border-l-[#22C55E] rounded">
                        <div className="flex items-start gap-3">
                          <CheckCircle className="h-5 w-5 text-[#22C55E] mt-0.5 flex-shrink-0" />
                          <div className="flex-1 space-y-4">
                            {/* IRN Number */}
                            <div>
                              <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)]">IRN</Label>
                              <div className="flex items-center gap-2 mt-1">
                                <code className="text-[11px] font-mono text-[#C8FF00] tracking-wider break-all">
                                  {selectedInvoice.irn}
                                </code>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6"
                                  onClick={() => {
                                    navigator.clipboard.writeText(selectedInvoice.irn);
                                    toast.success("IRN copied to clipboard");
                                  }}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                            
                            {/* Ack Number and Date */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)]">Ack Number</Label>
                                <p className="font-mono text-[#C8FF00] mt-1">{selectedInvoice.irn_ack_no || "-"}</p>
                              </div>
                              <div>
                                <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)]">Ack Date</Label>
                                <p className="font-mono text-[rgba(244,246,240,0.65)] mt-1">{selectedInvoice.irn_ack_date || "-"}</p>
                              </div>
                            </div>
                            
                            {/* QR Code */}
                            {irnQrCode && (
                              <div className="flex items-start gap-4 pt-2">
                                <div className="p-2 bg-white rounded">
                                  <img src={irnQrCode} alt="E-Invoice QR Code" className="w-32 h-32" />
                                </div>
                                <div className="flex-1">
                                  <p className="text-xs text-[rgba(244,246,240,0.45)]">Scan to verify on IRP portal</p>
                                  
                                  {/* Cancel IRN Button - only within 24 hours */}
                                  {canCancelIRN(selectedInvoice) ? (
                                    <Button 
                                      variant="ghost" 
                                      className="mt-4 text-[#FF3B2F] hover:text-red-300 hover:bg-[rgba(255,59,47,0.08)]"
                                      onClick={() => setShowIrnCancelDialog(true)}
                                      data-testid="cancel-irn-btn"
                                    >
                                      <XCircle className="h-4 w-4 mr-2" />
                                      Cancel IRN
                                    </Button>
                                  ) : (
                                    <div className="mt-4 text-xs text-[rgba(244,246,240,0.35)]">
                                      <Info className="h-3 w-3 inline mr-1" />
                                      IRN cancellation window (24 hrs) has passed
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* State 4: IRN Cancelled */}
                    {selectedInvoice.irn_status === "cancelled" && (
                      <div className="p-4 bg-[rgba(255,59,47,0.08)] border border-[rgba(255,59,47,0.25)] border-l-[3px] border-l-[#FF3B2F] rounded">
                        <div className="flex items-start gap-3">
                          <XCircle className="h-5 w-5 text-[#FF3B2F] mt-0.5 flex-shrink-0" />
                          <div>
                            <h4 className="font-medium text-[#FF3B2F]">IRN CANCELLED</h4>
                            {selectedInvoice.irn_cancel_reason && (
                              <p className="text-sm text-[rgba(244,246,240,0.65)] mt-1">
                                Reason: {selectedInvoice.irn_cancel_reason === "1" ? "Duplicate invoice" : 
                                        selectedInvoice.irn_cancel_reason === "2" ? "Invoice raised in error" :
                                        selectedInvoice.irn_cancel_reason === "3" ? "Wrong GSTIN entered" :
                                        selectedInvoice.irn_cancel_reason === "4" ? "Wrong invoice amount" : "Other"}
                              </p>
                            )}
                            <p className="text-xs font-mono text-[rgba(244,246,240,0.35)] mt-2">{selectedInvoice.irn}</p>
                            <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                              A new invoice must be raised with a new invoice number
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Line Items */}
                {selectedInvoice.line_items?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3">Line Items</h4>
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-[#111820]">
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
                                  {item.description && <p className="text-xs text-[rgba(244,246,240,0.45)]">{item.description}</p>}
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
                <div className="bg-[#111820] p-4 rounded-lg w-64 ml-auto space-y-1 text-sm">
                  <div className="flex justify-between"><span>Sub Total:</span><span>{formatCurrency(selectedInvoice.sub_total)}</span></div>
                  {selectedInvoice.total_discount > 0 && <div className="flex justify-between text-[#FF3B2F]"><span>Discount:</span><span>-{formatCurrency(selectedInvoice.total_discount)}</span></div>}
                  <div className="flex justify-between"><span>Tax:</span><span>{formatCurrency(selectedInvoice.tax_total)}</span></div>
                  {selectedInvoice.shipping_charge > 0 && <div className="flex justify-between"><span>Shipping:</span><span>{formatCurrency(selectedInvoice.shipping_charge)}</span></div>}
                  <Separator />
                  <div className="flex justify-between font-bold text-base"><span>Total:</span><span>{formatCurrency(selectedInvoice.grand_total)}</span></div>
                  {selectedInvoice.amount_paid > 0 && <div className="flex justify-between text-[#22C55E]"><span>Paid:</span><span>-{formatCurrency(selectedInvoice.amount_paid)}</span></div>}
                  <div className="flex justify-between font-bold text-lg"><span>Balance:</span><span className={selectedInvoice.balance_due > 0 ? "text-[#FF3B2F]" : "text-[#22C55E]"}>{formatCurrency(selectedInvoice.balance_due)}</span></div>
                </div>

                {/* Payments */}
                {selectedInvoice.payments?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2"><DollarSign className="h-4 w-4" /> Payments Received</h4>
                      <div className="space-y-2">
                        {selectedInvoice.payments.map(payment => (
                          <div key={payment.payment_id} className="flex justify-between items-center bg-[rgba(34,197,94,0.08)] p-3 rounded-lg">
                            <div>
                              <p className="font-medium">{formatCurrency(payment.amount)}</p>
                              <p className="text-xs text-[rgba(244,246,240,0.45)]">{formatDate(payment.payment_date)} • {payment.payment_mode}</p>
                              {payment.reference_number && <p className="text-xs text-[rgba(244,246,240,0.45)]">Ref: {payment.reference_number}</p>}
                            </div>
                            <Button size="icon" variant="ghost" onClick={() => handleDeletePayment(payment.payment_id)}><Trash2 className="h-4 w-4 text-red-400" /></Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {/* Payments from Payments Received Module */}
                {selectedInvoice.payments_received?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2"><CreditCard className="h-4 w-4" /> Payments (New System)</h4>
                      <div className="space-y-2">
                        {selectedInvoice.payments_received.map(payment => (
                          <div key={payment.payment_id} className="flex justify-between items-center bg-[rgba(34,197,94,0.08)] p-3 rounded-lg">
                            <div>
                              <p className="font-medium">{formatCurrency(payment.amount_applied)}</p>
                              <p className="text-xs text-[rgba(244,246,240,0.45)]">{payment.payment_number} • {formatDate(payment.payment_date)} • {payment.payment_mode}</p>
                            </div>
                            <Badge variant="outline" className="text-[#22C55E]">Applied</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {/* Available Credits */}
                {selectedInvoice.balance_due > 0 && selectedInvoice.available_credits?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2 text-[#FF8C00]"><Wallet className="h-4 w-4" /> Available Credits ({formatCurrency(selectedInvoice.total_available_credits)})</h4>
                      <div className="space-y-2">
                        {selectedInvoice.available_credits.map(credit => (
                          <div key={credit.credit_id} className="flex justify-between items-center bg-[rgba(255,140,0,0.08)] p-3 rounded-lg">
                            <div>
                              <p className="font-medium text-[#FF8C00]">{formatCurrency(credit.amount)}</p>
                              <p className="text-xs text-[rgba(244,246,240,0.45)]">{credit.source_number} • {credit.source_type}</p>
                            </div>
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="text-[#FF8C00] border-orange-300 hover:bg-orange-100"
                              onClick={() => handleApplyCredit(credit.credit_id, Math.min(credit.amount, selectedInvoice.balance_due))}
                            >
                              Apply
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {/* Online Payment Option - Razorpay */}
                {selectedInvoice.balance_due > 0 && selectedInvoice.status !== "draft" && (
                  <>
                    <Separator />
                    <div className="p-4 bg-[rgba(200,255,0,0.05)] rounded-lg border border-[rgba(200,255,0,0.15)]">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium flex items-center gap-2">
                            <CreditCard className="h-4 w-4 text-[#C8FF00]" /> 
                            Collect Payment Online
                          </h4>
                          <p className="text-sm text-[rgba(244,246,240,0.45)] mt-1">
                            Accept UPI, Cards, Net Banking, Wallets via Razorpay
                          </p>
                        </div>
                      </div>
                      
                      {/* Payment Status Display */}
                      {selectedInvoice.razorpay_payment_id && (
                        <div className="mb-3 p-3 bg-[rgba(34,197,94,0.10)] rounded-lg border border-green-500/20">
                          <div className="flex items-center gap-2 text-green-400 text-sm">
                            <CheckCircle className="h-4 w-4" />
                            <span className="font-medium">Payment Received</span>
                          </div>
                          <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-[rgba(244,246,240,0.65)]">
                            <div>
                              <span className="text-[rgba(244,246,240,0.45)]">Transaction ID:</span>
                              <br />
                              <code className="text-[#C8FF00]">{selectedInvoice.razorpay_payment_id}</code>
                            </div>
                            {selectedInvoice.razorpay_payment_method && (
                              <div>
                                <span className="text-[rgba(244,246,240,0.45)]">Method:</span>
                                <br />
                                <span className="capitalize">{selectedInvoice.razorpay_payment_method}</span>
                              </div>
                            )}
                            {selectedInvoice.razorpay_payment_date && (
                              <div>
                                <span className="text-[rgba(244,246,240,0.45)]">Date:</span>
                                <br />
                                {formatDate(selectedInvoice.razorpay_payment_date)}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Payment Link Status */}
                      {(selectedInvoice.payment_link_url || selectedInvoice.has_payment_link) && (
                        <div className="mb-3 p-3 bg-[rgba(59,158,255,0.08)] rounded-lg border border-blue-500/20">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm">
                              <Badge variant="outline" className="text-[#3B9EFF] border-blue-500/30">
                                Payment Link Active
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-[#3B9EFF] hover:text-blue-300"
                                onClick={() => navigator.clipboard.writeText(selectedInvoice.payment_link_url).then(() => toast.success("Link copied!"))}
                              >
                                <Copy className="h-4 w-4 mr-1" /> Copy
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-[#3B9EFF] hover:text-blue-300"
                                onClick={() => window.open(selectedInvoice.payment_link_url, "_blank")}
                              >
                                <ExternalLink className="h-4 w-4 mr-1" /> Open
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Action Buttons */}
                      {razorpayConfigured ? (
                        <div className="flex flex-wrap gap-2">
                          <Button 
                            onClick={() => handleRazorpayCheckout(selectedInvoice)}
                            className="bg-[#C8FF00] hover:bg-[#a8d900] text-[#080C0F]"
                            disabled={razorpayLoading}
                            data-testid="pay-now-btn"
                          >
                            {razorpayLoading ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <CreditCard className="h-4 w-4 mr-2" />
                            )}
                            Pay Now
                          </Button>
                          <Button 
                            variant="outline"
                            onClick={() => handleCreatePaymentLink(selectedInvoice.invoice_id)}
                            disabled={razorpayLoading}
                            data-testid="create-payment-link-btn"
                          >
                            <Link2 className="h-4 w-4 mr-2" />
                            Create Payment Link
                          </Button>
                        </div>
                      ) : (
                        <div className="p-3 bg-[rgba(234,179,8,0.08)] rounded-lg border border-yellow-500/20">
                          <p className="text-sm text-yellow-400 flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4" />
                            Razorpay not configured. Go to Organization Settings → Finance to connect.
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                )}

                {/* History */}
                {selectedInvoice.history?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2"><Clock className="h-4 w-4" /> History</h4>
                      <div className="space-y-1 text-xs text-[rgba(244,246,240,0.45)] max-h-32 overflow-y-auto">
                        {selectedInvoice.history.slice(0, 10).map((h, idx) => (
                          <p key={idx}><span className="text-[rgba(244,246,240,0.25)]">{formatDate(h.timestamp)}</span> - {h.action}: {h.details}</p>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                <Separator />

                {/* View Toggle */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-sm text-[rgba(244,246,240,0.45)]">View:</span>
                  <Button 
                    size="sm" 
                    variant={detailViewMode === "details" ? "default" : "outline"}
                    onClick={() => setDetailViewMode("details")}
                  >
                    <Eye className="h-4 w-4 mr-1" /> Details
                  </Button>
                  <Button 
                    size="sm" 
                    variant={detailViewMode === "pdf" ? "default" : "outline"}
                    onClick={() => handleDownloadPDF(selectedInvoice.invoice_id)}
                    disabled={selectedInvoice.status === "cancelled"}
                  >
                    <FileText className="h-4 w-4 mr-1" /> PDF Preview
                  </Button>
                </div>

                {/* Cancelled Invoice Banner (5A) */}
                {selectedInvoice.status === "cancelled" && (
                  <div className="p-4 bg-[rgba(255,59,47,0.12)] border border-[rgba(255,59,47,0.4)] rounded-lg">
                    <div className="flex items-center gap-3">
                      <Ban className="h-5 w-5 text-[#FF3B2F]" />
                      <div>
                        <h4 className="font-semibold text-[#FF3B2F]">This invoice has been cancelled</h4>
                        <p className="text-sm text-[rgba(244,246,240,0.65)] mt-1">
                          {selectedInvoice.irn ? (
                            <>IRN: <code className="font-mono text-xs">{selectedInvoice.irn}</code> was cancelled on {formatDate(selectedInvoice.irn_cancelled_at || selectedInvoice.updated_time)}.</>
                          ) : (
                            <>Cancelled on {formatDate(selectedInvoice.updated_time)}.</>
                          )}
                        </p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                          Raise a fresh invoice with a new invoice number.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Primary Actions */}
                <div className="flex flex-wrap gap-2">
                  {/* Edit - Only for draft invoices (not cancelled) */}
                  {selectedInvoice.status === "draft" && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleOpenEdit(selectedInvoice)}
                      data-testid="edit-invoice-btn"
                    >
                      <Edit className="h-4 w-4 mr-1" /> Edit
                    </Button>
                  )}
                  
                  {selectedInvoice.status === "draft" && (
                    <>
                      <Button variant="outline" size="sm" onClick={() => { setSendEmail(selectedInvoice.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Send</Button>
                      <Button variant="outline" size="sm" onClick={() => handleMarkSent(selectedInvoice.invoice_id)}><CheckCircle className="h-4 w-4 mr-1" /> Mark Sent</Button>
                    </>
                  )}
                  {/* Record Payment - not for cancelled invoices */}
                  {selectedInvoice.status !== "draft" && selectedInvoice.status !== "cancelled" && selectedInvoice.balance_due > 0 && (
                    <Button 
                      size="sm" 
                      className="bg-[#22C55E] hover:bg-green-600 text-[#080C0F]" 
                      onClick={() => { setNewPayment({ ...newPayment, amount: selectedInvoice.balance_due }); setShowPaymentDialog(true); }}
                      data-testid="record-payment-btn"
                    >
                      <DollarSign className="h-4 w-4 mr-1" /> Record Payment
                    </Button>
                  )}
                  
                  <Separator orientation="vertical" className="h-8" />
                  
                  {/* Share Link - not for cancelled invoices */}
                  {selectedInvoice.status !== "draft" && selectedInvoice.status !== "cancelled" && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => { setShareLink(null); setShowShareDialog(true); }}
                      data-testid="share-invoice-btn"
                    >
                      <Share2 className="h-4 w-4 mr-1" /> Share
                    </Button>
                  )}
                  
                  {/* Attachments */}
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => { fetchAttachments(selectedInvoice.invoice_id); setShowAttachmentDialog(true); }}
                    data-testid="attachments-btn"
                  >
                    <Paperclip className="h-4 w-4 mr-1" /> Attachments
                  </Button>
                  
                  {/* Comments */}
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => { fetchComments(selectedInvoice.invoice_id); fetchHistory(selectedInvoice.invoice_id); setShowCommentsDialog(true); }}
                    data-testid="comments-btn"
                  >
                    <MessageSquare className="h-4 w-4 mr-1" /> Notes
                  </Button>
                  
                  {/* Download PDF - disabled for cancelled */}
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => handleDownloadPDF(selectedInvoice.invoice_id)} 
                    disabled={selectedInvoice.status === "cancelled"}
                    data-testid="download-pdf-btn"
                  >
                    <Download className="h-4 w-4 mr-1" /> PDF
                  </Button>
                  
                  {/* Clone */}
                  <Button variant="outline" size="sm" onClick={() => handleCloneInvoice(selectedInvoice.invoice_id)}><Copy className="h-4 w-4 mr-1" /> Clone</Button>
                  
                  {/* Void - not for cancelled */}
                  {selectedInvoice.status !== "void" && selectedInvoice.status !== "paid" && selectedInvoice.status !== "cancelled" && (
                    <Button variant="outline" size="sm" onClick={() => handleVoidInvoice(selectedInvoice.invoice_id)}><Ban className="h-4 w-4 mr-1" /> Void</Button>
                  )}
                  
                  {/* Delete */}
                  <Button variant="destructive" size="sm" onClick={() => handleDeleteInvoice(selectedInvoice.invoice_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                </div>

                {/* History Section */}
                {selectedInvoice.history?.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2 flex items-center gap-2"><History className="h-4 w-4" /> Recent Activity</h4>
                    <div className="space-y-1 text-sm max-h-32 overflow-y-auto">
                      {selectedInvoice.history.slice(0, 5).map((h, idx) => (
                        <div key={idx} className="flex justify-between text-[rgba(244,246,240,0.45)] py-1">
                          <span>{h.action}: {h.details}</span>
                          <span className="text-xs text-[rgba(244,246,240,0.25)]">{new Date(h.timestamp).toLocaleString("en-IN")}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Invoice Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Invoice</DialogTitle>
            <DialogDescription>Modify invoice details (only available for draft invoices)</DialogDescription>
          </DialogHeader>
          
          {editInvoice && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Reference Number</Label>
                  <Input 
                    value={editInvoice.reference_number} 
                    onChange={(e) => setEditInvoice({...editInvoice, reference_number: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Invoice Date</Label>
                  <Input 
                    type="date" 
                    value={editInvoice.invoice_date} 
                    onChange={(e) => setEditInvoice({...editInvoice, invoice_date: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Payment Terms (days)</Label>
                  <Input 
                    type="number" 
                    value={editInvoice.payment_terms} 
                    onChange={(e) => setEditInvoice({...editInvoice, payment_terms: parseInt(e.target.value) || 30})}
                  />
                </div>
              </div>
              
              {/* Line Items */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <Label>Line Items</Label>
                  <Button size="sm" variant="outline" onClick={addEditLineItem}><Plus className="h-4 w-4 mr-1" /> Add Item</Button>
                </div>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-3 py-2 text-left">Item</th>
                        <th className="px-3 py-2 text-right w-20">Qty</th>
                        <th className="px-3 py-2 text-right w-28">Rate</th>
                        <th className="px-3 py-2 text-right w-20">Tax %</th>
                        <th className="px-3 py-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {editInvoice.line_items.map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">
                            <Input 
                              value={item.name} 
                              onChange={(e) => updateEditLineItem(idx, "name", e.target.value)}
                              placeholder="Item name"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Input 
                              type="number" 
                              value={item.quantity} 
                              onChange={(e) => updateEditLineItem(idx, "quantity", parseFloat(e.target.value) || 1)}
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Input 
                              type="number" 
                              value={item.rate} 
                              onChange={(e) => updateEditLineItem(idx, "rate", parseFloat(e.target.value) || 0)}
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Select value={String(item.tax_rate)} onValueChange={(v) => updateEditLineItem(idx, "tax_rate", parseFloat(v))}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="0">0%</SelectItem>
                                <SelectItem value="5">5%</SelectItem>
                                <SelectItem value="12">12%</SelectItem>
                                <SelectItem value="18">18%</SelectItem>
                                <SelectItem value="28">28%</SelectItem>
                              </SelectContent>
                            </Select>
                          </td>
                          <td className="px-3 py-2 text-center">
                            <Button size="icon" variant="ghost" onClick={() => removeEditLineItem(idx)}><X className="h-4 w-4 text-red-500" /></Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Customer Notes</Label>
                  <Textarea 
                    value={editInvoice.customer_notes} 
                    onChange={(e) => setEditInvoice({...editInvoice, customer_notes: e.target.value})}
                    rows={2}
                  />
                </div>
                <div>
                  <Label>Terms & Conditions</Label>
                  <Textarea 
                    value={editInvoice.terms_conditions} 
                    onChange={(e) => setEditInvoice({...editInvoice, terms_conditions: e.target.value})}
                    rows={2}
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Discount</Label>
                  <div className="flex gap-2">
                    <Select value={editInvoice.discount_type} onValueChange={(v) => setEditInvoice({...editInvoice, discount_type: v})}>
                      <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">%</SelectItem>
                        <SelectItem value="amount">₹</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input 
                      type="number" 
                      value={editInvoice.discount_value} 
                      onChange={(e) => setEditInvoice({...editInvoice, discount_value: parseFloat(e.target.value) || 0})}
                    />
                  </div>
                </div>
                <div>
                  <Label>Shipping Charge</Label>
                  <Input 
                    type="number" 
                    value={editInvoice.shipping_charge} 
                    onChange={(e) => setEditInvoice({...editInvoice, shipping_charge: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
            <Button onClick={handleUpdateInvoice} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="save-invoice-btn">Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Share Link Dialog */}
      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Share2 className="h-5 w-5" /> Share Invoice</DialogTitle>
            <DialogDescription>Generate a public link for customers to view and pay this invoice.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {!shareLink ? (
              <>
                <div className="space-y-3">
                  <div>
                    <Label>Link Expires In (days)</Label>
                    <Input 
                      type="number" 
                      value={shareConfig.expiry_days} 
                      onChange={(e) => setShareConfig({...shareConfig, expiry_days: parseInt(e.target.value) || 30})}
                      min={1} max={365}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Allow Online Payment</Label>
                    <input 
                      type="checkbox" 
                      checked={shareConfig.allow_payment} 
                      onChange={(e) => setShareConfig({...shareConfig, allow_payment: e.target.checked})}
                      className="h-4 w-4"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Password Protected</Label>
                    <input 
                      type="checkbox" 
                      checked={shareConfig.password_protected} 
                      onChange={(e) => setShareConfig({...shareConfig, password_protected: e.target.checked})}
                      className="h-4 w-4"
                    />
                  </div>
                  {shareConfig.password_protected && (
                    <div>
                      <Label>Password</Label>
                      <Input 
                        type="password" 
                        value={shareConfig.password} 
                        onChange={(e) => setShareConfig({...shareConfig, password: e.target.value})}
                        placeholder="Enter password"
                      />
                    </div>
                  )}
                </div>
                <Button 
                  onClick={handleCreateShareLink} 
                  disabled={shareLoading}
                  className="w-full bg-[#C8FF00] text-[#080C0F] font-bold"
                  data-testid="generate-share-link-btn"
                >
                  {shareLoading ? "Generating..." : "Generate Share Link"}
                </Button>
              </>
            ) : (
              <div className="space-y-4">
                <div className="bg-[rgba(34,197,94,0.08)] border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-[#22C55E] mb-2">Share link created successfully!</p>
                  <div className="flex items-center gap-2">
                    <Input value={shareLink.full_url} readOnly className="text-xs" />
                    <Button size="sm" onClick={copyShareLink}><Link className="h-4 w-4" /></Button>
                  </div>
                </div>
                <p className="text-xs text-[rgba(244,246,240,0.45)]">Expires: {new Date(shareLink.expiry_date).toLocaleDateString("en-IN")}</p>
                <Button variant="outline" className="w-full" onClick={() => setShareLink(null)}>Create New Link</Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Attachments Dialog */}
      <Dialog open={showAttachmentDialog} onOpenChange={setShowAttachmentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Paperclip className="h-5 w-5" /> Attachments</DialogTitle>
            <DialogDescription>Upload supporting documents (max 5 files, 10MB each)</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Upload Area */}
            <div className="border-2 border-dashed rounded-lg p-6 text-center">
              <input 
                type="file" 
                id="attachment-upload" 
                className="hidden" 
                onChange={handleUploadAttachment}
                disabled={uploadingAttachment}
              />
              <label htmlFor="attachment-upload" className="cursor-pointer">
                <Upload className="h-8 w-8 mx-auto text-[rgba(244,246,240,0.25)] mb-2" />
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Click to upload or drag & drop</p>
                <p className="text-xs text-[rgba(244,246,240,0.25)]">PDF, DOC, XLS, Images (max 10MB)</p>
              </label>
              {uploadingAttachment && <p className="text-sm text-[#3B9EFF] mt-2">Uploading...</p>}
            </div>
            
            {/* Attachments List */}
            {attachments.length > 0 ? (
              <div className="space-y-2">
                {attachments.map(att => (
                  <div key={att.attachment_id} className="flex items-center justify-between p-3 bg-[#111820] rounded-lg">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-[#3B9EFF]" />
                      <div>
                        <p className="text-sm font-medium">{att.filename}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">{(att.size_bytes / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button size="icon" variant="ghost" onClick={() => downloadAttachment(att.attachment_id, att.filename)}><Download className="h-4 w-4" /></Button>
                      <Button size="icon" variant="ghost" onClick={() => handleDeleteAttachment(att.attachment_id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-[rgba(244,246,240,0.45)] py-4">No attachments yet</p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Comments & History Dialog */}
      <Dialog open={showCommentsDialog} onOpenChange={setShowCommentsDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><MessageSquare className="h-5 w-5" /> Notes & History</DialogTitle>
            <DialogDescription>Internal notes and activity log for this invoice</DialogDescription>
          </DialogHeader>
          <Tabs defaultValue="comments" className="py-4">
            <TabsList className="w-full">
              <TabsTrigger value="comments" className="flex-1">Notes ({comments.length})</TabsTrigger>
              <TabsTrigger value="history" className="flex-1">History ({history.length})</TabsTrigger>
            </TabsList>
            
            <TabsContent value="comments" className="space-y-4 mt-4">
              {/* Add Comment */}
              <div className="flex gap-2">
                <Textarea 
                  value={newComment} 
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a note..."
                  rows={2}
                  className="flex-1"
                />
                <Button onClick={handleAddComment} disabled={!newComment.trim()}><Plus className="h-4 w-4" /></Button>
              </div>
              
              {/* Comments List */}
              {comments.length > 0 ? (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {comments.map(c => (
                    <div key={c.comment_id} className="p-3 bg-[#111820] rounded-lg">
                      <div className="flex justify-between items-start">
                        <p className="text-sm">{c.comment}</p>
                        <Button size="icon" variant="ghost" onClick={() => handleDeleteComment(c.comment_id)}><X className="h-3 w-3" /></Button>
                      </div>
                      <p className="text-xs text-[rgba(244,246,240,0.25)] mt-1">{new Date(c.created_time).toLocaleString("en-IN")}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-[rgba(244,246,240,0.45)] py-8">No notes yet</p>
              )}
            </TabsContent>
            
            <TabsContent value="history" className="mt-4">
              {history.length > 0 ? (
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {history.map((h, idx) => (
                    <div key={idx} className="flex justify-between items-center py-2 border-b last:border-0">
                      <div>
                        <p className="text-sm font-medium">{h.action}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">{h.details}</p>
                      </div>
                      <span className="text-xs text-[rgba(244,246,240,0.25)]">{new Date(h.timestamp).toLocaleString("en-IN")}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-[rgba(244,246,240,0.45)] py-8">No history available</p>
              )}
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* Send Email Dialog */}
      <Dialog open={showSendDialog} onOpenChange={setShowSendDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Invoice</DialogTitle>
            <DialogDescription>Email this invoice to the customer</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Email To</Label>
              <Input value={sendEmail} onChange={(e) => setSendEmail(e.target.value)} placeholder="customer@example.com" />
            </div>
            <div>
              <Label>Message (optional)</Label>
              <Textarea value={sendMessage} onChange={(e) => setSendMessage(e.target.value)} placeholder="Add a personal message..." rows={3} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSendDialog(false)}>Cancel</Button>
            <Button onClick={handleSendInvoiceEmail} className="bg-[#C8FF00] text-[#080C0F] font-bold">Send Invoice</Button>
          </DialogFooter>
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
            <div className="bg-[#111820] p-3 rounded-lg">
              <div className="flex justify-between">
                <span>Balance Due:</span>
                <span className="font-bold text-[#FF3B2F]">{formatCurrency(selectedInvoice?.balance_due)}</span>
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
            <Button onClick={handleRecordPayment} className="bg-[#22C55E] hover:bg-green-600 text-[#080C0F]" data-testid="submit-payment-btn">Record Payment</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* IRN Cancellation Dialog */}
      <Dialog open={showIrnCancelDialog} onOpenChange={setShowIrnCancelDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-[#FF3B2F]" />
              Cancel IRN Registration
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Warning */}
            <div className="p-3 bg-[rgba(255,59,47,0.08)] border-l-[3px] border-l-[#FF3B2F] rounded">
              <p className="text-sm text-[rgba(244,246,240,0.70)]">
                Cancelling this IRN will invalidate the invoice. This action cannot be undone after submission to the IRP portal.
              </p>
            </div>
            
            {/* Cancellation Reason */}
            <div className="space-y-2">
              <Label className="text-sm">Cancellation Reason *</Label>
              <Select value={irnCancelReason} onValueChange={setIrnCancelReason}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a reason" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Duplicate invoice</SelectItem>
                  <SelectItem value="2">Invoice raised in error</SelectItem>
                  <SelectItem value="3">Wrong GSTIN entered</SelectItem>
                  <SelectItem value="4">Wrong invoice amount</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Remarks */}
            <div className="space-y-2">
              <Label className="text-sm">Additional Remarks (optional)</Label>
              <Input 
                value={irnCancelRemarks}
                onChange={(e) => setIrnCancelRemarks(e.target.value)}
                placeholder="Enter additional details..."
                maxLength={100}
              />
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="ghost" onClick={() => setShowIrnCancelDialog(false)}>
              Keep IRN
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleCancelIRN}
              disabled={!irnCancelReason || irnLoading}
              className="bg-[#FF3B2F] hover:bg-red-600"
              data-testid="confirm-cancel-irn-btn"
            >
              {irnLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <XCircle className="h-4 w-4 mr-2" />}
              Cancel IRN
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
