import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Search, Receipt, Eye, Send, DollarSign, CreditCard, Banknote, Smartphone } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-muted text-muted-foreground",
  sent: "badge-info",
  partially_paid: "badge-warning",
  paid: "badge-success",
  overdue: "badge-danger",
  cancelled: "badge-danger"
};

const paymentMethods = [
  { value: "cash", label: "Cash", icon: Banknote },
  { value: "card", label: "Card", icon: CreditCard },
  { value: "upi", label: "UPI", icon: Smartphone },
  { value: "bank_transfer", label: "Bank Transfer", icon: DollarSign },
];

export default function Invoices({ user }) {
  const [invoices, setInvoices] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isPaymentOpen, setIsPaymentOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [formData, setFormData] = useState({
    ticket_id: "",
    line_items: [],
    discount_amount: 0,
    due_days: 30,
    notes: ""
  });
  const [paymentData, setPaymentData] = useState({
    amount: 0,
    payment_method: "cash",
    reference_number: "",
    notes: ""
  });
  const [newItem, setNewItem] = useState({ description: "", quantity: 1, rate: 0 });

  useEffect(() => {
    fetchInvoices();
    fetchTickets();
  }, []);

  const fetchInvoices = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/invoices`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        setInvoices(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch invoices:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTickets = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/tickets`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setTickets(data.filter(t => !t.has_invoice && (t.status === "resolved" || t.status === "closed")));
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
    }
  };

  const addLineItem = () => {
    if (!newItem.description || newItem.rate <= 0) {
      toast.error("Enter description and rate");
      return;
    }
    setFormData({
      ...formData,
      line_items: [...formData.line_items, {
        description: newItem.description,
        quantity: newItem.quantity,
        rate: newItem.rate,
        amount: newItem.quantity * newItem.rate
      }]
    });
    setNewItem({ description: "", quantity: 1, rate: 0 });
  };

  const removeLineItem = (idx) => {
    setFormData({ ...formData, line_items: formData.line_items.filter((_, i) => i !== idx) });
  };

  const handleCreateInvoice = async () => {
    if (!formData.ticket_id) {
      toast.error("Select a ticket");
      return;
    }
    if (formData.line_items.length === 0) {
      toast.error("Add at least one line item");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/invoices`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Invoice created!");
        fetchInvoices();
        fetchTickets();
        resetForm();
      } else {
        toast.error("Failed to create invoice");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const handleRecordPayment = async () => {
    if (!selectedInvoice || paymentData.amount <= 0) {
      toast.error("Enter a valid amount");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/payments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({
          invoice_id: selectedInvoice.invoice_id,
          ...paymentData
        }),
      });

      if (response.ok) {
        toast.success("Payment recorded!");
        fetchInvoices();
        setIsPaymentOpen(false);
        setSelectedInvoice(null);
        setPaymentData({ amount: 0, payment_method: "cash", reference_number: "", notes: "" });
      } else {
        toast.error("Failed to record payment");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const resetForm = () => {
    setFormData({ ticket_id: "", line_items: [], discount_amount: 0, due_days: 30, notes: "" });
    setNewItem({ description: "", quantity: 1, rate: 0 });
    setIsCreateOpen(false);
  };

  const openPayment = (invoice) => {
    setSelectedInvoice(invoice);
    setPaymentData({ ...paymentData, amount: invoice.balance_due });
    setIsPaymentOpen(true);
  };

  const filteredInvoices = invoices.filter(inv =>
    inv.invoice_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    inv.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const subtotal = formData.line_items.reduce((s, item) => s + item.amount, 0);
  const taxAmount = (subtotal - formData.discount_amount) * 0.18;
  const total = subtotal - formData.discount_amount + taxAmount;

  const totalReceivables = invoices.filter(i => i.payment_status !== "paid").reduce((s, i) => s + (i.balance_due || 0), 0);
  const totalCollected = invoices.reduce((s, i) => s + (i.amount_paid || 0), 0);

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="invoices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Invoices</h1>
          <p className="text-muted-foreground mt-1">Generate invoices and track payments.</p>
        </div>
        {(user?.role === "admin" || user?.role === "technician") && (
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="glow-primary" data-testid="create-invoice-btn">
                <Plus className="h-4 w-4 mr-2" />
                Create Invoice
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-white/10 max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Invoice</DialogTitle>
                <DialogDescription>Generate an invoice from a completed ticket.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Select Ticket *</Label>
                    <Select
                      value={formData.ticket_id}
                      onValueChange={(value) => setFormData({ ...formData, ticket_id: value })}
                    >
                      <SelectTrigger className="bg-background/50">
                        <SelectValue placeholder="Select a completed ticket" />
                      </SelectTrigger>
                      <SelectContent>
                        {tickets.map((t) => (
                          <SelectItem key={t.ticket_id} value={t.ticket_id}>
                            {t.ticket_id} - {t.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Due in (days)</Label>
                    <Input
                      type="number"
                      value={formData.due_days}
                      onChange={(e) => setFormData({ ...formData, due_days: parseInt(e.target.value) || 30 })}
                      className="bg-background/50"
                    />
                  </div>
                </div>

                {/* Line Items */}
                <div className="p-4 rounded-lg bg-background/50 space-y-3">
                  <Label>Line Items</Label>
                  <div className="grid grid-cols-4 gap-2">
                    <Input
                      placeholder="Description"
                      value={newItem.description}
                      onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                      className="bg-background/50 col-span-2"
                    />
                    <Input
                      type="number"
                      placeholder="Qty"
                      value={newItem.quantity || ""}
                      onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
                      className="bg-background/50"
                    />
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        placeholder="Rate"
                        value={newItem.rate || ""}
                        onChange={(e) => setNewItem({ ...newItem, rate: parseFloat(e.target.value) || 0 })}
                        className="bg-background/50"
                      />
                      <Button onClick={addLineItem} variant="outline" className="border-white/10">Add</Button>
                    </div>
                  </div>

                  {formData.line_items.length > 0 && (
                    <Table>
                      <TableHeader>
                        <TableRow className="border-white/10">
                          <TableHead>Description</TableHead>
                          <TableHead className="text-right">Qty</TableHead>
                          <TableHead className="text-right">Rate</TableHead>
                          <TableHead className="text-right">Amount</TableHead>
                          <TableHead></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {formData.line_items.map((item, idx) => (
                          <TableRow key={idx} className="border-white/10">
                            <TableCell>{item.description}</TableCell>
                            <TableCell className="text-right mono">{item.quantity}</TableCell>
                            <TableCell className="text-right mono">₹{item.rate}</TableCell>
                            <TableCell className="text-right mono">₹{item.amount.toLocaleString()}</TableCell>
                            <TableCell>
                              <Button size="sm" variant="ghost" onClick={() => removeLineItem(idx)}>×</Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Discount (₹)</Label>
                    <Input
                      type="number"
                      value={formData.discount_amount}
                      onChange={(e) => setFormData({ ...formData, discount_amount: parseFloat(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Notes</Label>
                    <Input
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      className="bg-background/50"
                    />
                  </div>
                </div>

                {/* Summary */}
                <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="mono">₹{subtotal.toLocaleString()}</span>
                  </div>
                  {formData.discount_amount > 0 && (
                    <div className="flex justify-between text-sm text-emerald-400">
                      <span>Discount</span>
                      <span className="mono">-₹{formData.discount_amount.toLocaleString()}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">GST (18%)</span>
                    <span className="mono">₹{taxAmount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t border-white/10 pt-2">
                    <span>Total</span>
                    <span className="mono text-primary">₹{total.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm} className="border-white/10">Cancel</Button>
                <Button onClick={handleCreateInvoice} className="glow-primary">Create Invoice</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Invoices</p>
            <p className="text-2xl font-bold mono">{invoices.length}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Collected</p>
            <p className="text-2xl font-bold mono text-emerald-400">₹{totalCollected.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className={`metric-card ${totalReceivables > 0 ? 'border-orange-500/30' : ''}`}>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Outstanding</p>
            <p className={`text-2xl font-bold mono ${totalReceivables > 0 ? 'text-orange-400' : ''}`}>
              ₹{totalReceivables.toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Paid Invoices</p>
            <p className="text-2xl font-bold mono">{invoices.filter(i => i.payment_status === "paid").length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search invoices..."
              className="pl-10 bg-background/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Invoices Table */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading invoices...</div>
          ) : filteredInvoices.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No invoices found. Create your first invoice from a completed ticket.
            </div>
          ) : (
            <Table className="data-table">
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>Invoice #</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Vehicle</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Paid</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredInvoices.map((invoice) => (
                  <TableRow key={invoice.invoice_id} className="border-white/10">
                    <TableCell className="mono font-semibold">{invoice.invoice_number}</TableCell>
                    <TableCell>{invoice.customer_name || '-'}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{invoice.vehicle_details || '-'}</TableCell>
                    <TableCell className="text-right mono">₹{(invoice.total_amount || 0).toLocaleString()}</TableCell>
                    <TableCell className="text-right mono text-emerald-400">₹{(invoice.amount_paid || 0).toLocaleString()}</TableCell>
                    <TableCell className="text-right mono font-semibold">₹{(invoice.balance_due || 0).toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge className={statusColors[invoice.status]} variant="outline">
                        {invoice.status?.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {invoice.balance_due > 0 && (
                          <Button size="sm" variant="outline" onClick={() => openPayment(invoice)} className="border-white/10">
                            <DollarSign className="h-4 w-4 mr-1" /> Pay
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Payment Dialog */}
      <Dialog open={isPaymentOpen} onOpenChange={setIsPaymentOpen}>
        <DialogContent className="bg-card border-white/10">
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
            <DialogDescription>
              Invoice: {selectedInvoice?.invoice_number} | Balance: ₹{selectedInvoice?.balance_due?.toLocaleString()}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Amount (₹)</Label>
              <Input
                type="number"
                value={paymentData.amount}
                onChange={(e) => setPaymentData({ ...paymentData, amount: parseFloat(e.target.value) || 0 })}
                className="bg-background/50"
                max={selectedInvoice?.balance_due}
              />
            </div>
            <div className="space-y-2">
              <Label>Payment Method</Label>
              <div className="grid grid-cols-4 gap-2">
                {paymentMethods.map((method) => {
                  const Icon = method.icon;
                  return (
                    <button
                      key={method.value}
                      type="button"
                      onClick={() => setPaymentData({ ...paymentData, payment_method: method.value })}
                      className={`p-3 rounded-lg border transition-all ${
                        paymentData.payment_method === method.value
                          ? "border-primary bg-primary/10"
                          : "border-white/10 hover:border-white/20"
                      }`}
                    >
                      <Icon className={`h-5 w-5 mx-auto mb-1 ${
                        paymentData.payment_method === method.value ? "text-primary" : "text-muted-foreground"
                      }`} />
                      <p className="text-xs">{method.label}</p>
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="space-y-2">
              <Label>Reference Number</Label>
              <Input
                value={paymentData.reference_number}
                onChange={(e) => setPaymentData({ ...paymentData, reference_number: e.target.value })}
                className="bg-background/50"
                placeholder="Transaction ID, Cheque #, etc."
              />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={paymentData.notes}
                onChange={(e) => setPaymentData({ ...paymentData, notes: e.target.value })}
                className="bg-background/50"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPaymentOpen(false)} className="border-white/10">Cancel</Button>
            <Button onClick={handleRecordPayment} className="glow-primary">Record Payment</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
