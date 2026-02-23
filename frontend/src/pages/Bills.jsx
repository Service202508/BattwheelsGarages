import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Plus, FileText, Calendar, Building2, Eye, CheckCircle, 
  Clock, IndianRupee, Trash2, CreditCard
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  open: "bg-blue-100 text-[#3B9EFF]",
  partially_paid: "bg-yellow-100 text-[#EAB308]",
  paid: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  overdue: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  void: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.25)] border border-[rgba(255,255,255,0.08)]"
};

export default function Bills() {
  const [bills, setBills] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [selectedBill, setSelectedBill] = useState(null);

  const [newBill, setNewBill] = useState({
    vendor_id: "",
    vendor_name: "",
    bill_number: "",
    line_items: [],
    payment_terms: 30,
    notes: ""
  });

  const [newLineItem, setNewLineItem] = useState({
    name: "", rate: 0, quantity: 1, tax_percentage: 18
  });

  const [payment, setPayment] = useState({
    amount: 0, payment_mode: "Bank Transfer", reference_number: "", bill_ids: []
  });

  useEffect(() => { fetchData(); }, [statusFilter]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [billsRes, vendorsRes, itemsRes] = await Promise.all([
        fetch(`${API}/zoho/bills?status=${statusFilter}&per_page=100`, { headers }),
        fetch(`${API}/zoho/contacts?contact_type=vendor&per_page=200`, { headers }),
        fetch(`${API}/zoho/items?per_page=200`, { headers })
      ]);
      const [billsData, vendorsData, itemsData] = await Promise.all([
        billsRes.json(), vendorsRes.json(), itemsRes.json()
      ]);
      setBills(billsData.bills || []);
      setVendors(vendorsData.contacts || []);
      setItems(itemsData.items || []);
    } catch (error) {
      console.error("Failed to fetch:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.name || newLineItem.rate <= 0) return toast.error("Enter item details");
    setNewBill({ ...newBill, line_items: [...newBill.line_items, { ...newLineItem }] });
    setNewLineItem({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });
  };

  const calculateTotal = () => newBill.line_items.reduce((sum, i) => {
    const sub = i.quantity * i.rate;
    const tax = sub * (i.tax_percentage / 100);
    return sum + sub + tax;
  }, 0);

  const handleCreateBill = async () => {
    if (!newBill.vendor_id) return toast.error("Select a vendor");
    if (!newBill.bill_number) return toast.error("Enter bill number");
    if (!newBill.line_items.length) return toast.error("Add at least one item");
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/bills`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newBill)
      });
      if (res.ok) {
        toast.success("Bill created");
        setShowCreateDialog(false);
        setNewBill({ vendor_id: "", vendor_name: "", bill_number: "", line_items: [], payment_terms: 30, notes: "" });
        fetchData();
      }
    } catch { toast.error("Error creating bill"); }
  };

  const handleRecordPayment = async () => {
    if (!selectedBill || payment.amount <= 0) return toast.error("Enter valid amount");
    
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/vendorpayments`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          vendor_id: selectedBill.vendor_id,
          vendor_name: selectedBill.vendor_name,
          amount: payment.amount,
          payment_mode: payment.payment_mode,
          reference_number: payment.reference_number,
          bill_ids: [selectedBill.bill_id]
        })
      });
      if (res.ok) {
        toast.success("Payment recorded");
        setShowPaymentDialog(false);
        setPayment({ amount: 0, payment_mode: "Bank Transfer", reference_number: "", bill_ids: [] });
        fetchData();
      }
    } catch { toast.error("Error recording payment"); }
  };

  return (
    <div className="space-y-6" data-testid="bills-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Bills</h1>
          <p className="text-gray-500 text-sm mt-1">Vendor invoices & payables</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-bill-btn">
              <Plus className="h-4 w-4 mr-2" /> New Bill
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Bill</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Vendor *</Label>
                  <Select onValueChange={(v) => {
                    const vendor = vendors.find(x => x.contact_id === v);
                    if (vendor) setNewBill({ ...newBill, vendor_id: vendor.contact_id, vendor_name: vendor.contact_name });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select vendor" /></SelectTrigger>
                    <SelectContent>
                      {vendors.map(v => <SelectItem key={v.contact_id} value={v.contact_id}>{v.contact_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Bill Number *</Label>
                  <Input value={newBill.bill_number} onChange={(e) => setNewBill({ ...newBill, bill_number: e.target.value })} placeholder="VND-INV-001" />
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

              {newBill.line_items.length > 0 && (
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
                      {newBill.line_items.map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{item.name}</td>
                          <td className="px-3 py-2 text-right">{item.quantity}</td>
                          <td className="px-3 py-2 text-right">₹{item.rate}</td>
                          <td className="px-3 py-2 text-right">₹{(item.quantity * item.rate * (1 + item.tax_percentage/100)).toLocaleString('en-IN')}</td>
                          <td className="px-3 py-2">
                            <Button variant="ghost" size="icon" onClick={() => setNewBill({ ...newBill, line_items: newBill.line_items.filter((_, i) => i !== idx) })}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-[#111820] font-semibold">
                      <tr><td colSpan={3} className="px-3 py-2 text-right">Total:</td><td className="px-3 py-2 text-right">₹{calculateTotal().toLocaleString('en-IN')}</td><td></td></tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreateBill} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create Bill</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["", "open", "partially_paid", "paid", "overdue"].map(s => (
          <Button key={s} size="sm" variant={statusFilter === s ? "default" : "outline"}
            onClick={() => setStatusFilter(s)}
            className={statusFilter === s ? "bg-[#C8FF00] text-[#080C0F] font-bold" : ""}>
            {s || "All"}
          </Button>
        ))}
      </div>

      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
        bills.length === 0 ? <Card><CardContent className="py-12 text-center text-gray-500">No bills found</CardContent></Card> :
        <div className="space-y-3">
          {bills.map(bill => (
            <Card key={bill.bill_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold">{bill.bill_number}</h3>
                      <Badge className={statusColors[bill.status]}>{bill.status}</Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{bill.vendor_name}</span>
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{bill.date}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />Due: {bill.due_date}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-bold text-lg">₹{bill.total?.toLocaleString('en-IN')}</p>
                      {bill.balance > 0 && <p className="text-xs text-[#FF8C00]">Due: ₹{bill.balance?.toLocaleString('en-IN')}</p>}
                    </div>
                    {bill.balance > 0 && (
                      <Button size="sm" className="bg-[#C8FF00] text-[#080C0F] font-bold" onClick={() => { setSelectedBill(bill); setPayment({ ...payment, amount: bill.balance }); setShowPaymentDialog(true); }}>
                        <CreditCard className="h-4 w-4 mr-1" /> Pay
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      }

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment - {selectedBill?.bill_number}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Amount *</Label>
              <Input type="number" value={payment.amount} onChange={(e) => setPayment({ ...payment, amount: parseFloat(e.target.value) })} />
            </div>
            <div>
              <Label>Payment Mode</Label>
              <Select value={payment.payment_mode} onValueChange={(v) => setPayment({ ...payment, payment_mode: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Bank Transfer">Bank Transfer</SelectItem>
                  <SelectItem value="NEFT">NEFT</SelectItem>
                  <SelectItem value="RTGS">RTGS</SelectItem>
                  <SelectItem value="Cheque">Cheque</SelectItem>
                  <SelectItem value="Cash">Cash</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Reference Number</Label>
              <Input value={payment.reference_number} onChange={(e) => setPayment({ ...payment, reference_number: e.target.value })} placeholder="Transaction ID" />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowPaymentDialog(false)}>Cancel</Button>
            <Button onClick={handleRecordPayment} className="bg-[#C8FF00] text-[#080C0F] font-bold">Record Payment</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
