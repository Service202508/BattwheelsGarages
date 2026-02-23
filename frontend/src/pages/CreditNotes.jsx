import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { 
  Plus, FileText, Calendar, User, ArrowRight, Trash2, Receipt
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  open: "bg-blue-100 text-[#3B9EFF]",
  closed: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]"
};

export default function CreditNotes() {
  const [creditNotes, setCreditNotes] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showApplyDialog, setShowApplyDialog] = useState(false);
  const [selectedCN, setSelectedCN] = useState(null);

  const [newCN, setNewCN] = useState({
    customer_id: "",
    customer_name: "",
    reason: "",
    line_items: [],
    notes: ""
  });

  const [newLineItem, setNewLineItem] = useState({
    name: "", rate: 0, quantity: 1, tax_percentage: 18
  });

  const [applyAmount, setApplyAmount] = useState(0);
  const [selectedInvoice, setSelectedInvoice] = useState("");

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [cnRes, custRes, invRes] = await Promise.all([
        fetch(`${API}/zoho/creditnotes?per_page=100`, { headers }),
        fetch(`${API}/zoho/contacts?contact_type=customer&per_page=200`, { headers }),
        fetch(`${API}/zoho/invoices?per_page=200`, { headers })
      ]);
      const [cnData, custData, invData] = await Promise.all([
        cnRes.json(), custRes.json(), invRes.json()
      ]);
      setCreditNotes(cnData.creditnotes || []);
      setCustomers(custData.contacts || []);
      setInvoices(invData.invoices || []);
    } catch (error) {
      console.error("Failed to fetch:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.name || newLineItem.rate <= 0) return toast.error("Enter item details");
    setNewCN({ ...newCN, line_items: [...newCN.line_items, { ...newLineItem }] });
    setNewLineItem({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });
  };

  const calculateTotal = () => newCN.line_items.reduce((sum, i) => {
    const sub = i.quantity * i.rate;
    const tax = sub * (i.tax_percentage / 100);
    return sum + sub + tax;
  }, 0);

  const handleCreateCN = async () => {
    if (!newCN.customer_id) return toast.error("Select a customer");
    if (!newCN.reason) return toast.error("Enter reason");
    if (!newCN.line_items.length) return toast.error("Add at least one item");
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/creditnotes`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newCN)
      });
      if (res.ok) {
        toast.success("Credit note created");
        setShowCreateDialog(false);
        setNewCN({ customer_id: "", customer_name: "", reason: "", line_items: [], notes: "" });
        fetchData();
      }
    } catch { toast.error("Error creating credit note"); }
  };

  const handleApplyToInvoice = async () => {
    if (!selectedCN || !selectedInvoice || applyAmount <= 0) return toast.error("Select invoice and enter amount");
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/creditnotes/${selectedCN.creditnote_id}/invoices/${selectedInvoice}/apply?amount=${applyAmount}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Credit applied to invoice");
        setShowApplyDialog(false);
        setApplyAmount(0);
        setSelectedInvoice("");
        fetchData();
      }
    } catch { toast.error("Error applying credit"); }
  };

  const customerInvoices = invoices.filter(i => i.customer_id === selectedCN?.customer_id && i.balance > 0);

  return (
    <div className="space-y-6" data-testid="credit-notes-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Credit Notes</h1>
          <p className="text-gray-500 text-sm mt-1">Customer refunds & adjustments</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-cn-btn">
              <Plus className="h-4 w-4 mr-2" /> New Credit Note
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Credit Note</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Customer *</Label>
                  <Select onValueChange={(v) => {
                    const cust = customers.find(x => x.contact_id === v);
                    if (cust) setNewCN({ ...newCN, customer_id: cust.contact_id, customer_name: cust.contact_name });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select customer" /></SelectTrigger>
                    <SelectContent>
                      {customers.map(c => <SelectItem key={c.contact_id} value={c.contact_id}>{c.contact_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Reason *</Label>
                  <Select value={newCN.reason} onValueChange={(v) => setNewCN({ ...newCN, reason: v })}>
                    <SelectTrigger><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Sales Return">Sales Return</SelectItem>
                      <SelectItem value="Defective Product">Defective Product</SelectItem>
                      <SelectItem value="Price Adjustment">Price Adjustment</SelectItem>
                      <SelectItem value="Service Issue">Service Issue</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="border rounded-lg p-4 bg-[#111820]">
                <h3 className="font-medium mb-3">Add Items</h3>
                <div className="grid grid-cols-4 gap-3">
                  <Input value={newLineItem.name} onChange={(e) => setNewLineItem({ ...newLineItem, name: e.target.value })} placeholder="Item name" />
                  <Input type="number" value={newLineItem.quantity} onChange={(e) => setNewLineItem({ ...newLineItem, quantity: parseFloat(e.target.value) })} placeholder="Qty" />
                  <Input type="number" value={newLineItem.rate} onChange={(e) => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) })} placeholder="Rate" />
                  <Button onClick={handleAddLineItem} className="bg-[#C8FF00] text-[#080C0F] font-bold">Add</Button>
                </div>
              </div>

              {newCN.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-3 py-2 text-left">Item</th>
                        <th className="px-3 py-2 text-right">Qty</th>
                        <th className="px-3 py-2 text-right">Rate</th>
                        <th className="px-3 py-2 text-right">Amount</th>
                        <th className="px-3 py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {newCN.line_items.map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{item.name}</td>
                          <td className="px-3 py-2 text-right">{item.quantity}</td>
                          <td className="px-3 py-2 text-right">₹{item.rate}</td>
                          <td className="px-3 py-2 text-right">₹{(item.quantity * item.rate * (1 + item.tax_percentage/100)).toLocaleString('en-IN')}</td>
                          <td className="px-3 py-2">
                            <Button variant="ghost" size="icon" onClick={() => setNewCN({ ...newCN, line_items: newCN.line_items.filter((_, i) => i !== idx) })}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-[#111820] font-semibold">
                      <tr><td colSpan={3} className="px-3 py-2 text-right">Total Credit:</td><td className="px-3 py-2 text-right">₹{calculateTotal().toLocaleString('en-IN')}</td><td></td></tr>
                    </tfoot>
                  </table>
                </div>
              )}

              <div>
                <Label>Notes</Label>
                <Textarea value={newCN.notes} onChange={(e) => setNewCN({ ...newCN, notes: e.target.value })} placeholder="Additional notes..." />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreateCN} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create Credit Note</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
        creditNotes.length === 0 ? <Card><CardContent className="py-12 text-center text-gray-500">No credit notes found</CardContent></Card> :
        <div className="space-y-3">
          {creditNotes.map(cn => (
            <Card key={cn.creditnote_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold">{cn.creditnote_number}</h3>
                      <Badge className={statusColors[cn.status]}>{cn.status}</Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" />{cn.customer_name}</span>
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{cn.date}</span>
                      <span className="flex items-center gap-1"><FileText className="h-3.5 w-3.5" />{cn.reason}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-bold text-lg">₹{cn.total?.toLocaleString('en-IN')}</p>
                      {cn.credits_remaining > 0 && <p className="text-xs text-[#3B9EFF]">Available: ₹{cn.credits_remaining?.toLocaleString('en-IN')}</p>}
                    </div>
                    {cn.credits_remaining > 0 && (
                      <Button size="sm" className="bg-[#C8FF00] text-[#080C0F] font-bold" onClick={() => { setSelectedCN(cn); setApplyAmount(cn.credits_remaining); setShowApplyDialog(true); }}>
                        <ArrowRight className="h-4 w-4 mr-1" /> Apply
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      }

      {/* Apply to Invoice Dialog */}
      <Dialog open={showApplyDialog} onOpenChange={setShowApplyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Apply Credit to Invoice</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Select Invoice *</Label>
              <Select value={selectedInvoice} onValueChange={setSelectedInvoice}>
                <SelectTrigger><SelectValue placeholder="Select invoice" /></SelectTrigger>
                <SelectContent>
                  {customerInvoices.map(inv => (
                    <SelectItem key={inv.invoice_id} value={inv.invoice_id}>
                      {inv.invoice_number} - ₹{inv.balance?.toLocaleString('en-IN')} due
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Amount to Apply *</Label>
              <Input type="number" value={applyAmount} onChange={(e) => setApplyAmount(parseFloat(e.target.value))} max={selectedCN?.credits_remaining} />
              <p className="text-xs text-gray-500 mt-1">Max: ₹{selectedCN?.credits_remaining?.toLocaleString('en-IN')}</p>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowApplyDialog(false)}>Cancel</Button>
            <Button onClick={handleApplyToInvoice} className="bg-[#C8FF00] text-[#080C0F] font-bold">Apply Credit</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
