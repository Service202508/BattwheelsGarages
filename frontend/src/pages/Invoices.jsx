import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Search, Plus, FileText, IndianRupee, Calendar, User, 
  CheckCircle, Clock, AlertCircle, Eye, Download, Send, Trash2
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  sent: "bg-[rgba(59,158,255,0.10)] text-[#3B9EFF] border border-[rgba(59,158,255,0.25)]",
  viewed: "bg-[rgba(139,92,246,0.10)] text-[#8B5CF6] border border-[rgba(139,92,246,0.25)]",
  paid: "bg-[rgba(34,197,94,0.10)] text-[#22C55E] border border-[rgba(34,197,94,0.25)]",
  partially_paid: "bg-[rgba(234,179,8,0.10)] text-[#EAB308] border border-[rgba(234,179,8,0.25)]",
  overdue: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  void: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.25)] border border-[rgba(255,255,255,0.08)]"
};

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [services, setServices] = useState([]);
  const [parts, setParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  const [newInvoice, setNewInvoice] = useState({
    customer_id: "",
    customer_name: "",
    line_items: [],
    place_of_supply: "DL",
    gst_treatment: "business_gst",
    notes: "",
    terms: ""
  });

  const [newLineItem, setNewLineItem] = useState({
    item_id: "",
    item_name: "",
    quantity: 1,
    rate: 0,
    discount_percent: 0,
    tax_rate: 18
  });

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };

      const [invRes, custRes, srvRes, prtRes, analyticsRes] = await Promise.all([
        fetch(`${API}/books/invoices?status=${statusFilter}&limit=100`, { headers }),
        fetch(`${API}/books/customers?limit=200`, { headers }),
        fetch(`${API}/books/services?limit=200`, { headers }),
        fetch(`${API}/books/parts?limit=200`, { headers }),
        fetch(`${API}/books/analytics/summary`, { headers })
      ]);

      const [invData, custData, srvData, prtData, analyticsData] = await Promise.all([
        invRes.json(),
        custRes.json(),
        srvRes.json(),
        prtRes.json(),
        analyticsRes.json()
      ]);

      setInvoices(invData.invoices || []);
      setCustomers(custData.customers || []);
      setServices(srvData.items || []);
      setParts(prtData.items || []);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.item_name || newLineItem.rate <= 0) {
      toast.error("Please select an item");
      return;
    }
    setNewInvoice({
      ...newInvoice,
      line_items: [...newInvoice.line_items, { ...newLineItem }]
    });
    setNewLineItem({ item_id: "", item_name: "", quantity: 1, rate: 0, discount_percent: 0, tax_rate: 18 });
  };

  const handleRemoveLineItem = (index) => {
    setNewInvoice({
      ...newInvoice,
      line_items: newInvoice.line_items.filter((_, i) => i !== index)
    });
  };

  const handleSelectItem = (itemId, type) => {
    const items = type === 'service' ? services : parts;
    const item = items.find(i => i.item_id === itemId);
    if (item) {
      setNewLineItem({
        ...newLineItem,
        item_id: item.item_id,
        item_name: item.name,
        rate: item.rate || 0,
        tax_rate: item.tax_rate || 18
      });
    }
  };

  const handleSelectCustomer = (customerId) => {
    const customer = customers.find(c => c.customer_id === customerId);
    if (customer) {
      setNewInvoice({
        ...newInvoice,
        customer_id: customer.customer_id,
        customer_name: customer.display_name
      });
    }
  };

  const calculateTotal = () => {
    return newInvoice.line_items.reduce((sum, item) => {
      const subtotal = item.quantity * item.rate;
      const discount = subtotal * (item.discount_percent / 100);
      const taxable = subtotal - discount;
      const tax = taxable * (item.tax_rate / 100);
      return sum + taxable + tax;
    }, 0);
  };

  const handleCreateInvoice = async () => {
    if (!newInvoice.customer_id) {
      toast.error("Please select a customer");
      return;
    }
    if (newInvoice.line_items.length === 0) {
      toast.error("Please add at least one item");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/books/invoices`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newInvoice)
      });

      if (res.ok) {
        toast.success("Invoice created successfully");
        setShowCreateDialog(false);
        setNewInvoice({
          customer_id: "", customer_name: "", line_items: [],
          place_of_supply: "DL", gst_treatment: "business_gst", notes: "", terms: ""
        });
        fetchData();
      } else {
        toast.error("Failed to create invoice");
      }
    } catch (error) {
      toast.error("Error creating invoice");
    }
  };

  const handleUpdateStatus = async (invoiceId, status) => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/books/invoices/${invoiceId}/status?status=${status}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success(`Invoice marked as ${status}`);
        fetchData();
      }
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  return (
    <div className="space-y-6" data-testid="invoices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Invoices</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Manage your sales invoices</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-invoice-btn">
              <Plus className="h-4 w-4 mr-2" />
              Create Invoice
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" aria-describedby="create-invoice-description">
            <DialogHeader>
              <DialogTitle>Create New Invoice</DialogTitle>
              <p id="create-invoice-description" className="text-sm text-[rgba(244,246,240,0.45)]">Add customer and line items to generate a GST invoice</p>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Customer Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Customer *</Label>
                  <Select onValueChange={handleSelectCustomer}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select customer" />
                    </SelectTrigger>
                    <SelectContent>
                      {customers.map(c => (
                        <SelectItem key={c.customer_id} value={c.customer_id}>
                          {c.display_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Place of Supply</Label>
                  <Select value={newInvoice.place_of_supply} onValueChange={(v) => setNewInvoice({...newInvoice, place_of_supply: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DL">Delhi</SelectItem>
                      <SelectItem value="HR">Haryana</SelectItem>
                      <SelectItem value="UP">Uttar Pradesh</SelectItem>
                      <SelectItem value="RJ">Rajasthan</SelectItem>
                      <SelectItem value="MH">Maharashtra</SelectItem>
                      <SelectItem value="KA">Karnataka</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Add Line Items */}
              <div className="border rounded-lg p-4 bg-[#111820]">
                <h3 className="font-medium mb-4">Add Items</h3>
                <Tabs defaultValue="services">
                  <TabsList className="mb-4">
                    <TabsTrigger value="services">Services</TabsTrigger>
                    <TabsTrigger value="parts">Parts</TabsTrigger>
                  </TabsList>
                  <TabsContent value="services">
                    <Select onValueChange={(v) => handleSelectItem(v, 'service')}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a service" />
                      </SelectTrigger>
                      <SelectContent>
                        {services.map(s => (
                          <SelectItem key={s.item_id} value={s.item_id}>
                            {s.name} - ₹{s.rate}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TabsContent>
                  <TabsContent value="parts">
                    <Select onValueChange={(v) => handleSelectItem(v, 'part')}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a part" />
                      </SelectTrigger>
                      <SelectContent>
                        {parts.map(p => (
                          <SelectItem key={p.item_id} value={p.item_id}>
                            {p.name} - ₹{p.rate}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TabsContent>
                </Tabs>

                {newLineItem.item_name && (
                  <div className="mt-4 grid grid-cols-4 gap-4">
                    <div>
                      <Label>Item</Label>
                      <Input value={newLineItem.item_name} readOnly className="bg-[#111820]" />
                    </div>
                    <div>
                      <Label>Qty</Label>
                      <Input
                        type="number"
                        value={newLineItem.quantity}
                        onChange={(e) => setNewLineItem({...newLineItem, quantity: parseFloat(e.target.value)})}
                      />
                    </div>
                    <div>
                      <Label>Rate (₹)</Label>
                      <Input
                        type="number"
                        value={newLineItem.rate}
                        onChange={(e) => setNewLineItem({...newLineItem, rate: parseFloat(e.target.value)})}
                      />
                    </div>
                    <div className="flex items-end">
                      <Button onClick={handleAddLineItem} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                        Add Item
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              {/* Line Items Table */}
              {newInvoice.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-[rgba(244,246,240,0.45)]">Item</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-[rgba(244,246,240,0.45)]">Qty</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-[rgba(244,246,240,0.45)]">Rate</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-[rgba(244,246,240,0.45)]">Tax</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-[rgba(244,246,240,0.45)]">Amount</th>
                        <th className="px-4 py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {newInvoice.line_items.map((item, idx) => {
                        const subtotal = item.quantity * item.rate;
                        const tax = subtotal * (item.tax_rate / 100);
                        return (
                          <tr key={idx} className="border-t">
                            <td className="px-4 py-2 text-sm">{item.item_name}</td>
                            <td className="px-4 py-2 text-sm text-right">{item.quantity}</td>
                            <td className="px-4 py-2 text-sm text-right">₹{item.rate.toLocaleString('en-IN')}</td>
                            <td className="px-4 py-2 text-sm text-right">{item.tax_rate}%</td>
                            <td className="px-4 py-2 text-sm text-right font-medium">₹{(subtotal + tax).toLocaleString('en-IN')}</td>
                            <td className="px-4 py-2">
                              <Button variant="ghost" size="icon" onClick={() => handleRemoveLineItem(idx)}>
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot className="bg-[#111820]">
                      <tr className="border-t">
                        <td colSpan={4} className="px-4 py-3 text-right font-semibold">Total:</td>
                        <td className="px-4 py-3 text-right font-bold text-lg">₹{calculateTotal().toLocaleString('en-IN')}</td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}

              {/* Notes */}
              <div>
                <Label>Notes</Label>
                <Input
                  value={newInvoice.notes}
                  onChange={(e) => setNewInvoice({...newInvoice, notes: e.target.value})}
                  placeholder="Additional notes..."
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreateInvoice} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                Create Invoice
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Revenue</p>
                  <p className="text-2xl font-bold text-[#F4F6F0]">₹{analytics.revenue.total.toLocaleString('en-IN')}</p>
                </div>
                <IndianRupee className="h-8 w-8 text-[#C8FF00]" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[rgba(244,246,240,0.45)]">Collected</p>
                  <p className="text-2xl font-bold text-[#22C55E]">₹{analytics.revenue.collected.toLocaleString('en-IN')}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[rgba(244,246,240,0.45)]">Outstanding</p>
                  <p className="text-2xl font-bold text-[#FF8C00]">₹{analytics.revenue.outstanding.toLocaleString('en-IN')}</p>
                </div>
                <Clock className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Invoices</p>
                  <p className="text-2xl font-bold text-[#F4F6F0]">{analytics.invoices.total}</p>
                </div>
                <FileText className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2">
        <Button
          variant={statusFilter === "" ? "default" : "outline"}
          size="sm"
          onClick={() => setStatusFilter("")}
          className={statusFilter === "" ? "bg-[#C8FF00] text-[#080C0F] font-bold hover:bg-[#d4ff1a]" : ""}
        >
          All
        </Button>
        {["draft", "sent", "paid", "partially_paid", "overdue"].map(status => (
          <Button
            key={status}
            variant={statusFilter === status ? "default" : "outline"}
            size="sm"
            onClick={() => setStatusFilter(status)}
            className={statusFilter === status ? "bg-[#C8FF00] text-[#080C0F] font-bold hover:bg-[#d4ff1a]" : ""}
          >
            {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </Button>
        ))}
      </div>

      {/* Invoice List */}
      {loading ? (
        <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading invoices...</div>
      ) : invoices.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
            No invoices found. Create your first invoice to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {invoices.map((invoice) => (
            <Card key={invoice.invoice_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors" data-testid={`invoice-card-${invoice.invoice_id}`}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-[#F4F6F0]">{invoice.invoice_number}</h3>
                      <Badge className={statusColors[invoice.status]}>
                        {invoice.status.replace('_', ' ')}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                      <span className="flex items-center gap-1">
                        <User className="h-3.5 w-3.5" />
                        {invoice.customer_name}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" />
                        {invoice.invoice_date}
                      </span>
                      <span className="flex items-center gap-1">
                        <FileText className="h-3.5 w-3.5" />
                        {invoice.line_items?.length || 0} items
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-xs text-[rgba(244,246,240,0.25)]">Total</p>
                      <p className="font-bold text-lg">₹{invoice.total?.toLocaleString('en-IN')}</p>
                      {invoice.balance_due > 0 && (
                        <p className="text-xs text-[#FF8C00]">Due: ₹{invoice.balance_due?.toLocaleString('en-IN')}</p>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="icon" onClick={() => setSelectedInvoice(invoice)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                          <DialogHeader>
                            <DialogTitle>Invoice {invoice.invoice_number}</DialogTitle>
                          </DialogHeader>
                          <div className="space-y-4 py-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <p className="text-[rgba(244,246,240,0.25)]">Customer</p>
                                <p className="font-medium">{invoice.customer_name}</p>
                              </div>
                              <div>
                                <p className="text-[rgba(244,246,240,0.25)]">Status</p>
                                <Badge className={statusColors[invoice.status]}>{invoice.status}</Badge>
                              </div>
                              <div>
                                <p className="text-[rgba(244,246,240,0.25)]">Invoice Date</p>
                                <p className="font-medium">{invoice.invoice_date}</p>
                              </div>
                              <div>
                                <p className="text-[rgba(244,246,240,0.25)]">Due Date</p>
                                <p className="font-medium">{invoice.due_date}</p>
                              </div>
                            </div>

                            <div className="border rounded-lg overflow-hidden">
                              <table className="w-full">
                                <thead className="bg-[#111820]">
                                  <tr>
                                    <th className="px-4 py-2 text-left text-xs font-medium text-[rgba(244,246,240,0.45)]">Item</th>
                                    <th className="px-4 py-2 text-right text-xs font-medium text-[rgba(244,246,240,0.45)]">Qty</th>
                                    <th className="px-4 py-2 text-right text-xs font-medium text-[rgba(244,246,240,0.45)]">Rate</th>
                                    <th className="px-4 py-2 text-right text-xs font-medium text-[rgba(244,246,240,0.45)]">Amount</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {invoice.line_items?.map((item, idx) => (
                                    <tr key={idx} className="border-t">
                                      <td className="px-4 py-2 text-sm">{item.item_name}</td>
                                      <td className="px-4 py-2 text-sm text-right">{item.quantity}</td>
                                      <td className="px-4 py-2 text-sm text-right">₹{item.rate?.toLocaleString('en-IN')}</td>
                                      <td className="px-4 py-2 text-sm text-right">₹{item.total?.toLocaleString('en-IN')}</td>
                                    </tr>
                                  ))}
                                </tbody>
                                <tfoot className="bg-[#111820]">
                                  <tr className="border-t">
                                    <td colSpan={3} className="px-4 py-2 text-right text-sm">Subtotal:</td>
                                    <td className="px-4 py-2 text-right">₹{invoice.subtotal?.toLocaleString('en-IN')}</td>
                                  </tr>
                                  <tr>
                                    <td colSpan={3} className="px-4 py-2 text-right text-sm">Tax:</td>
                                    <td className="px-4 py-2 text-right">₹{invoice.tax_total?.toLocaleString('en-IN')}</td>
                                  </tr>
                                  <tr className="font-bold">
                                    <td colSpan={3} className="px-4 py-2 text-right">Total:</td>
                                    <td className="px-4 py-2 text-right text-lg">₹{invoice.total?.toLocaleString('en-IN')}</td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>

                            <div className="flex gap-2 justify-end pt-4">
                              {invoice.status === "draft" && (
                                <Button onClick={() => handleUpdateStatus(invoice.invoice_id, "sent")} className="bg-[#3B9EFF] hover:bg-blue-600 text-[#080C0F]">
                                  <Send className="h-4 w-4 mr-2" />
                                  Mark as Sent
                                </Button>
                              )}
                              {["draft", "sent", "partially_paid"].includes(invoice.status) && (
                                <Button onClick={() => handleUpdateStatus(invoice.invoice_id, "paid")} className="bg-[#22C55E] hover:bg-[#16a34a] text-[#080C0F]">
                                  <CheckCircle className="h-4 w-4 mr-2" />
                                  Mark as Paid
                                </Button>
                              )}
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
