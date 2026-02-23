import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Truck, Calendar, User, FileText, ArrowRight, CheckCircle, Trash2 } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  delivered: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  invoiced: "bg-blue-100 text-[#3B9EFF]"
};

const challanTypes = {
  delivery: "Delivery Challan",
  job_work: "Job Work",
  supply_on_approval: "Supply on Approval"
};

export default function DeliveryChallans() {
  const [challans, setChallans] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const [newChallan, setNewChallan] = useState({
    customer_id: "", customer_name: "", challan_type: "delivery",
    reference_number: "", line_items: [], notes: ""
  });
  const [newLineItem, setNewLineItem] = useState({ name: "", rate: 0, quantity: 1 });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [challansRes, customersRes, itemsRes] = await Promise.all([
        fetch(`${API}/zoho/delivery-challans`, { headers }),
        fetch(`${API}/zoho/contacts?contact_type=customer&per_page=200`, { headers }),
        fetch(`${API}/zoho/items?per_page=200`, { headers })
      ]);
      const [challansData, customersData, itemsData] = await Promise.all([
        challansRes.json(), customersRes.json(), itemsRes.json()
      ]);
      setChallans(challansData.delivery_challans || []);
      setCustomers(customersData.contacts || []);
      setItems(itemsData.items || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.name || newLineItem.rate <= 0) return toast.error("Enter item details");
    setNewChallan({ ...newChallan, line_items: [...newChallan.line_items, { ...newLineItem }] });
    setNewLineItem({ name: "", rate: 0, quantity: 1 });
  };

  const handleSelectItem = (itemId) => {
    const item = items.find(i => i.item_id === itemId);
    if (item) {
      setNewLineItem({ name: item.name, rate: item.rate || 0, quantity: 1 });
    }
  };

  const calculateTotal = () => newChallan.line_items.reduce((sum, i) => sum + i.quantity * i.rate, 0);

  const handleCreate = async () => {
    if (!newChallan.customer_id) return toast.error("Select a customer");
    if (!newChallan.line_items.length) return toast.error("Add at least one item");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/delivery-challans`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newChallan)
      });
      if (res.ok) {
        toast.success("Delivery challan created");
        setShowCreateDialog(false);
        setNewChallan({ customer_id: "", customer_name: "", challan_type: "delivery", reference_number: "", line_items: [], notes: "" });
        fetchData();
      }
    } catch { toast.error("Error creating delivery challan"); }
  };

  const handleMarkDelivered = async (dcId) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/zoho/delivery-challans/${dcId}/status/delivered`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Marked as delivered");
      fetchData();
    } catch { toast.error("Error updating status"); }
  };

  const handleConvertToInvoice = async (dcId) => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/delivery-challans/${dcId}/convert-to-invoice`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Invoice ${data.invoice?.invoice_number} created`);
        fetchData();
      }
    } catch { toast.error("Error converting to invoice"); }
  };

  return (
    <div className="space-y-6" data-testid="delivery-challans-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Delivery Challans</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Track goods dispatched to customers</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-challan-btn">
              <Plus className="h-4 w-4 mr-2" /> New Delivery Challan
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Create Delivery Challan</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Customer *</Label>
                  <Select onValueChange={(v) => {
                    const customer = customers.find(c => c.contact_id === v);
                    if (customer) setNewChallan({ ...newChallan, customer_id: customer.contact_id, customer_name: customer.contact_name });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select customer" /></SelectTrigger>
                    <SelectContent>
                      {customers.map(c => <SelectItem key={c.contact_id} value={c.contact_id}>{c.contact_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Challan Type</Label>
                  <Select value={newChallan.challan_type} onValueChange={(v) => setNewChallan({ ...newChallan, challan_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="delivery">Delivery Challan</SelectItem>
                      <SelectItem value="job_work">Job Work</SelectItem>
                      <SelectItem value="supply_on_approval">Supply on Approval</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label>Reference Number</Label>
                <Input value={newChallan.reference_number} onChange={(e) => setNewChallan({ ...newChallan, reference_number: e.target.value })} placeholder="e.g., PO-12345" />
              </div>

              <div className="border rounded-lg p-4 bg-[#111820]">
                <h3 className="font-medium mb-3">Add Items</h3>
                <div className="grid grid-cols-4 gap-3 mb-3">
                  <div className="col-span-2">
                    <Select onValueChange={handleSelectItem}>
                      <SelectTrigger><SelectValue placeholder="Select item..." /></SelectTrigger>
                      <SelectContent>
                        {items.map(item => <SelectItem key={item.item_id} value={item.item_id}>{item.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2 text-sm text-[rgba(244,246,240,0.45)] flex items-center">Or enter manually below</div>
                </div>
                <div className="grid grid-cols-4 gap-3">
                  <Input value={newLineItem.name} onChange={(e) => setNewLineItem({ ...newLineItem, name: e.target.value })} placeholder="Item name" />
                  <Input type="number" value={newLineItem.quantity} onChange={(e) => setNewLineItem({ ...newLineItem, quantity: parseFloat(e.target.value) })} placeholder="Qty" min={1} />
                  <Input type="number" value={newLineItem.rate} onChange={(e) => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) })} placeholder="Rate" />
                  <Button onClick={handleAddLineItem} className="bg-[#C8FF00] text-[#080C0F] font-bold">Add</Button>
                </div>
              </div>

              {newChallan.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-3 py-2 text-left">Item</th>
                        <th className="px-3 py-2 text-right">Qty</th>
                        <th className="px-3 py-2 text-right">Rate</th>
                        <th className="px-3 py-2 text-right">Amount</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {newChallan.line_items.map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{item.name}</td>
                          <td className="px-3 py-2 text-right">{item.quantity}</td>
                          <td className="px-3 py-2 text-right">₹{item.rate.toLocaleString('en-IN')}</td>
                          <td className="px-3 py-2 text-right">₹{(item.quantity * item.rate).toLocaleString('en-IN')}</td>
                          <td className="px-3 py-2">
                            <Button variant="ghost" size="icon" onClick={() => setNewChallan({ ...newChallan, line_items: newChallan.line_items.filter((_, i) => i !== idx) })}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-[#111820] font-semibold">
                      <tr>
                        <td colSpan={3} className="px-3 py-2 text-right">Total:</td>
                        <td className="px-3 py-2 text-right">₹{calculateTotal().toLocaleString('en-IN')}</td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}

              <div>
                <Label>Notes</Label>
                <Input value={newChallan.notes} onChange={(e) => setNewChallan({ ...newChallan, notes: e.target.value })} placeholder="Additional notes..." />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreate} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create Challan</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</div> :
        challans.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
              <Truck className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
              <p>No delivery challans found</p>
              <p className="text-sm mt-1">Create your first delivery challan to track goods dispatched</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {challans.map(dc => (
              <Card key={dc.delivery_challan_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <Truck className="h-5 w-5 text-[#C8FF00]" />
                        <h3 className="font-semibold">{dc.challan_number}</h3>
                        <Badge className={statusColors[dc.status]}>{dc.status}</Badge>
                        <Badge variant="outline">{challanTypes[dc.challan_type] || dc.challan_type}</Badge>
                      </div>
                      <div className="flex gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                        <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" />{dc.customer_name}</span>
                        <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{dc.date}</span>
                        {dc.reference_number && <span className="flex items-center gap-1"><FileText className="h-3.5 w-3.5" />Ref: {dc.reference_number}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="font-bold text-lg">₹{dc.sub_total?.toLocaleString('en-IN')}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">{dc.line_items?.length || 0} items</p>
                      </div>
                      <div className="flex flex-col gap-1">
                        {dc.status === "draft" && (
                          <Button size="sm" variant="outline" onClick={() => handleMarkDelivered(dc.delivery_challan_id)}>
                            <CheckCircle className="h-4 w-4 mr-1" /> Delivered
                          </Button>
                        )}
                        {dc.status === "delivered" && !dc.is_invoiced && (
                          <Button size="sm" className="bg-[#C8FF00] text-[#080C0F] font-bold" onClick={() => handleConvertToInvoice(dc.delivery_challan_id)}>
                            <ArrowRight className="h-4 w-4 mr-1" /> Convert to Invoice
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )
      }
    </div>
  );
}
