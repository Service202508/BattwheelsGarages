import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Plus, Repeat, Calendar, User, Play, Pause, FileText, Trash2 } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  active: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  stopped: "bg-[#141E27] text-gray-600",
  expired: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]"
};

export default function RecurringTransactions() {
  const [recurringInvoices, setRecurringInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const [newRI, setNewRI] = useState({
    customer_id: "", customer_name: "", recurrence_name: "", recurrence_frequency: "monthly",
    repeat_every: 1, start_date: "", never_expires: true, line_items: [], payment_terms: 15
  });
  const [newLineItem, setNewLineItem] = useState({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [riRes, custRes] = await Promise.all([
        fetch(`${API}/zoho/recurring-invoices`, { headers }),
        fetch(`${API}/zoho/contacts?contact_type=customer&per_page=200`, { headers })
      ]);
      const [riData, custData] = await Promise.all([riRes.json(), custRes.json()]);
      setRecurringInvoices(riData.recurring_invoices || []);
      setCustomers(custData.contacts || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.name || newLineItem.rate <= 0) return toast.error("Enter item details");
    setNewRI({ ...newRI, line_items: [...newRI.line_items, { ...newLineItem }] });
    setNewLineItem({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });
  };

  const calculateTotal = () => newRI.line_items.reduce((sum, i) => sum + i.quantity * i.rate * (1 + i.tax_percentage / 100), 0);

  const handleCreate = async () => {
    if (!newRI.customer_id) return toast.error("Select a customer");
    if (!newRI.recurrence_name) return toast.error("Enter profile name");
    if (!newRI.start_date) return toast.error("Select start date");
    if (!newRI.line_items.length) return toast.error("Add at least one item");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/recurring-invoices`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newRI)
      });
      if (res.ok) {
        toast.success("Recurring invoice created");
        setShowCreateDialog(false);
        setNewRI({ customer_id: "", customer_name: "", recurrence_name: "", recurrence_frequency: "monthly", repeat_every: 1, start_date: "", never_expires: true, line_items: [], payment_terms: 15 });
        fetchData();
      }
    } catch { toast.error("Error creating recurring invoice"); }
  };

  const handleStop = async (riId) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/zoho/recurring-invoices/${riId}/stop`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      toast.success("Recurring invoice stopped");
      fetchData();
    } catch { toast.error("Error stopping"); }
  };

  const handleResume = async (riId) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/zoho/recurring-invoices/${riId}/resume`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      toast.success("Recurring invoice resumed");
      fetchData();
    } catch { toast.error("Error resuming"); }
  };

  const handleGenerateNow = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/recurring-invoices/generate`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      toast.success(data.message);
      fetchData();
    } catch { toast.error("Error generating invoices"); }
  };

  return (
    <div className="space-y-6" data-testid="recurring-transactions-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Recurring Transactions</h1>
          <p className="text-gray-500 text-sm mt-1">Auto-generate invoices on schedule</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleGenerateNow}>
            <Play className="h-4 w-4 mr-2" /> Generate Due Invoices
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-recurring-btn">
                <Plus className="h-4 w-4 mr-2" /> New Recurring Invoice
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader><DialogTitle>Create Recurring Invoice</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Customer *</Label>
                    <Select onValueChange={(v) => {
                      const cust = customers.find(x => x.contact_id === v);
                      if (cust) setNewRI({ ...newRI, customer_id: cust.contact_id, customer_name: cust.contact_name });
                    }}>
                      <SelectTrigger><SelectValue placeholder="Select customer" /></SelectTrigger>
                      <SelectContent>{customers.map(c => <SelectItem key={c.contact_id} value={c.contact_id}>{c.contact_name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Profile Name *</Label>
                    <Input value={newRI.recurrence_name} onChange={(e) => setNewRI({ ...newRI, recurrence_name: e.target.value })} placeholder="e.g., Monthly Maintenance" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Frequency</Label>
                    <Select value={newRI.recurrence_frequency} onValueChange={(v) => setNewRI({ ...newRI, recurrence_frequency: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="yearly">Yearly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Repeat Every</Label>
                    <Input type="number" value={newRI.repeat_every} onChange={(e) => setNewRI({ ...newRI, repeat_every: parseInt(e.target.value) })} min={1} />
                  </div>
                  <div>
                    <Label>Start Date *</Label>
                    <Input type="date" value={newRI.start_date} onChange={(e) => setNewRI({ ...newRI, start_date: e.target.value })} />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Switch checked={newRI.never_expires} onCheckedChange={(v) => setNewRI({ ...newRI, never_expires: v })} />
                  <Label>Never Expires</Label>
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
                {newRI.line_items.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-[#111820]"><tr><th className="px-3 py-2 text-left">Item</th><th className="px-3 py-2 text-right">Qty</th><th className="px-3 py-2 text-right">Rate</th><th className="px-3 py-2 text-right">Amount</th><th></th></tr></thead>
                      <tbody>
                        {newRI.line_items.map((item, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="px-3 py-2">{item.name}</td>
                            <td className="px-3 py-2 text-right">{item.quantity}</td>
                            <td className="px-3 py-2 text-right">₹{item.rate}</td>
                            <td className="px-3 py-2 text-right">₹{(item.quantity * item.rate * (1 + item.tax_percentage / 100)).toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2"><Button variant="ghost" size="icon" onClick={() => setNewRI({ ...newRI, line_items: newRI.line_items.filter((_, i) => i !== idx) })}><Trash2 className="h-4 w-4 text-red-500" /></Button></td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-[#111820] font-semibold"><tr><td colSpan={3} className="px-3 py-2 text-right">Total per Invoice:</td><td className="px-3 py-2 text-right">₹{calculateTotal().toLocaleString('en-IN')}</td><td></td></tr></tfoot>
                    </table>
                  </div>
                )}
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                <Button onClick={handleCreate} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
        recurringInvoices.length === 0 ? <Card><CardContent className="py-12 text-center text-gray-500">No recurring invoices found</CardContent></Card> :
        <div className="space-y-3">
          {recurringInvoices.map(ri => (
            <Card key={ri.recurring_invoice_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <Repeat className="h-5 w-5 text-[#C8FF00]" />
                      <h3 className="font-semibold">{ri.recurrence_name}</h3>
                      <Badge className={statusColors[ri.status]}>{ri.status}</Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" />{ri.customer_name}</span>
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />Next: {ri.next_invoice_date}</span>
                      <span className="capitalize">{ri.recurrence_frequency}</span>
                      <span>{ri.invoices_generated} generated</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-bold text-lg">₹{ri.total?.toLocaleString('en-IN')}</p>
                      <p className="text-xs text-gray-500">per invoice</p>
                    </div>
                    {ri.status === "active" ? (
                      <Button size="sm" variant="outline" onClick={() => handleStop(ri.recurring_invoice_id)}>
                        <Pause className="h-4 w-4" />
                      </Button>
                    ) : ri.status === "stopped" ? (
                      <Button size="sm" variant="outline" onClick={() => handleResume(ri.recurring_invoice_id)}>
                        <Play className="h-4 w-4" />
                      </Button>
                    ) : null}
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
