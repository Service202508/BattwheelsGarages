import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import {
  FileText, Search, Loader2, CreditCard, Download, Eye,
  CheckCircle, Clock, AlertCircle, IndianRupee, RefreshCw
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  paid: "bg-bw-volt/10 text-bw-volt text-700 border-bw-volt/20",
  unpaid: "bg-amber-100 text-amber-700 border-amber-200",
  overdue: "bg-bw-red/10 text-bw-red border border-bw-red/25 border-red-200",
  partial: "bg-blue-100 text-bw-blue border-blue-200",
  draft: "bg-white/5 text-slate-600 border-white/[0.07] border-200",
};

export default function BusinessInvoices({ user }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedInvoices, setSelectedInvoices] = useState([]);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [summary, setSummary] = useState({ total_invoiced: 0, pending_payment: 0 });

  useEffect(() => {
    fetchInvoices();
  }, [statusFilter]);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      let url = `${API}/business/invoices?limit=100`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      
      const res = await fetch(url, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setInvoices(data.invoices || []);
        setSummary(data.summary || { total_invoiced: 0, pending_payment: 0 });
      }
    } catch (error) {
      console.error("Failed to fetch invoices:", error);
      toast.error("Failed to load invoices");
    } finally {
      setLoading(false);
    }
  };

  const toggleInvoiceSelection = (invoiceId) => {
    setSelectedInvoices(prev => 
      prev.includes(invoiceId) 
        ? prev.filter(id => id !== invoiceId)
        : [...prev, invoiceId]
    );
  };

  const selectAllUnpaid = () => {
    const unpaidIds = invoices
      .filter(inv => inv.status !== "paid" && inv.balance > 0)
      .map(inv => inv.invoice_id);
    setSelectedInvoices(unpaidIds);
  };

  const getSelectedTotal = () => {
    return invoices
      .filter(inv => selectedInvoices.includes(inv.invoice_id))
      .reduce((sum, inv) => sum + (inv.balance || 0), 0);
  };

  const initiateBulkPayment = async () => {
    if (selectedInvoices.length === 0) {
      toast.error("Please select invoices to pay");
      return;
    }
    
    setPaymentLoading(true);
    try {
      const res = await fetch(`${API}/business/invoices/bulk-payment`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          invoice_ids: selectedInvoices,
          payment_method: "razorpay"
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        
        if (data.is_mock) {
          toast.success("Payment simulated successfully (Mock Mode)");
          setShowPaymentDialog(false);
          setSelectedInvoices([]);
          fetchInvoices();
        } else {
          // Open Razorpay checkout
          const options = {
            key: data.razorpay_key,
            amount: data.amount_paise,
            currency: data.currency,
            name: "Battwheels",
            description: `Payment for ${data.invoice_count} invoice(s)`,
            order_id: data.order_id,
            handler: function (response) {
              toast.success("Payment successful!");
              setShowPaymentDialog(false);
              setSelectedInvoices([]);
              fetchInvoices();
            },
            prefill: {
              email: user?.email,
              contact: user?.phone
            },
            theme: {
              color: "#4F46E5"
            }
          };
          
          const rzp = new window.Razorpay(options);
          rzp.open();
        }
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to initiate payment");
      }
    } catch (error) {
      toast.error("Failed to initiate payment");
    } finally {
      setPaymentLoading(false);
    }
  };

  const filteredInvoices = invoices.filter(inv => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      inv.invoice_id?.toLowerCase().includes(search) ||
      inv.invoice_number?.toLowerCase().includes(search) ||
      inv.ticket_id?.toLowerCase().includes(search)
    );
  });

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  return (
    <div className="space-y-6" data-testid="business-invoices">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Invoices</h1>
          <p className="text-slate-500">View and pay your service invoices</p>
        </div>
        {selectedInvoices.length > 0 && (
          <Button 
            onClick={() => setShowPaymentDialog(true)}
            className="bg-indigo-600 hover:bg-indigo-700 hover:shadow-[0_0_20px_rgba(99,102,241,0.30)]"
            data-testid="pay-selected-btn"
          >
            <CreditCard className="h-4 w-4 mr-2" />
            Pay Selected ({formatCurrency(getSelectedTotal())})
          </Button>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Invoiced</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(summary.total_invoiced)}</p>
              </div>
              <div className="p-3 rounded bg-indigo-50">
                <FileText className="h-5 w-5 text-indigo-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Pending Payment</p>
                <p className="text-2xl font-bold text-amber-600">{formatCurrency(summary.pending_payment)}</p>
              </div>
              <div className="p-3 rounded bg-amber-50">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Paid</p>
                <p className="text-2xl font-bold text-bw-volt text-600">
                  {formatCurrency(summary.total_invoiced - summary.pending_payment)}
                </p>
              </div>
              <div className="p-3 rounded bg-bw-volt/[0.08]">
                <CheckCircle className="h-5 w-5 text-bw-volt text-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs & Filters */}
      <Tabs value={statusFilter} onValueChange={setStatusFilter}>
        <div className="flex items-center justify-between">
          <TabsList className="bg-white/5">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="unpaid">Unpaid</TabsTrigger>
            <TabsTrigger value="paid">Paid</TabsTrigger>
          </TabsList>
          
          <div className="flex items-center gap-4">
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search invoices..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline" onClick={selectAllUnpaid}>
              Select All Unpaid
            </Button>
            <Button variant="outline" onClick={fetchInvoices}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Invoices Table */}
        <TabsContent value={statusFilter} className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
          ) : filteredInvoices.length === 0 ? (
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardContent className="py-12 text-center">
                <FileText className="h-16 w-16 mx-auto text-slate-300 mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">No invoices found</h3>
                <p className="text-slate-500">
                  {searchTerm ? "Try adjusting your search" : "No invoices available"}
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox 
                        checked={selectedInvoices.length === filteredInvoices.filter(i => i.status !== "paid").length}
                        onCheckedChange={(checked) => {
                          if (checked) selectAllUnpaid();
                          else setSelectedInvoices([]);
                        }}
                      />
                    </TableHead>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Ticket</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Balance</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-24">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredInvoices.map((invoice) => (
                    <TableRow key={invoice.invoice_id} data-testid={`invoice-row-${invoice.invoice_id}`}>
                      <TableCell>
                        {invoice.status !== "paid" && invoice.balance > 0 && (
                          <Checkbox 
                            checked={selectedInvoices.includes(invoice.invoice_id)}
                            onCheckedChange={() => toggleInvoiceSelection(invoice.invoice_id)}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-slate-900">{invoice.invoice_number}</p>
                          <p className="text-xs text-slate-500">{invoice.invoice_id}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-600">{formatDate(invoice.date)}</TableCell>
                      <TableCell>
                        {invoice.ticket_id ? (
                          <Badge variant="outline" className="font-mono text-xs">
                            {invoice.ticket_id}
                          </Badge>
                        ) : "-"}
                      </TableCell>
                      <TableCell className="font-medium">{formatCurrency(invoice.total)}</TableCell>
                      <TableCell className={invoice.balance > 0 ? "font-medium text-amber-600" : "text-slate-400"}>
                        {formatCurrency(invoice.balance)}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[invoice.status] || statusColors.unpaid}>
                          {invoice.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Payment Confirmation Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Payment</DialogTitle>
            <DialogDescription>
              You are about to pay for {selectedInvoices.length} invoice(s)
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <div className="p-4 rounded bg-indigo-50 border border-indigo-100">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-indigo-700">Total Amount</span>
                <span className="text-2xl font-bold text-indigo-700">{formatCurrency(getSelectedTotal())}</span>
              </div>
              <p className="text-xs text-indigo-600">
                {selectedInvoices.length} invoice(s) selected
              </p>
            </div>
            
            <div className="mt-4 space-y-2">
              {invoices
                .filter(inv => selectedInvoices.includes(inv.invoice_id))
                .map(inv => (
                  <div key={inv.invoice_id} className="flex justify-between text-sm p-2 bg-slate-50 rounded">
                    <span className="text-slate-600">{inv.invoice_number}</span>
                    <span className="font-medium">{formatCurrency(inv.balance)}</span>
                  </div>
                ))
              }
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPaymentDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={initiateBulkPayment}
              disabled={paymentLoading}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {paymentLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CreditCard className="h-4 w-4 mr-2" />}
              Pay {formatCurrency(getSelectedTotal())}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
