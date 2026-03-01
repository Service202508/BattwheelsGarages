import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Building2, Calendar, FileText, ArrowRight, Trash2 } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  open: "bg-blue-100 text-bw-blue",
  closed: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25"
};

export default function VendorCredits() {
  const [credits, setCredits] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showApplyDialog, setShowApplyDialog] = useState(false);
  const [selectedVC, setSelectedVC] = useState(null);

  const [newVC, setNewVC] = useState({ vendor_id: "", vendor_name: "", reason: "", line_items: [], notes: "" });
  const [newLineItem, setNewLineItem] = useState({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });
  const [applyAmount, setApplyAmount] = useState(0);
  const [selectedBill, setSelectedBill] = useState("");

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [vcRes, vendorsRes, billsRes] = await Promise.all([
        fetch(`${API}/zoho/vendorcredits?per_page=100`, { headers }),
        fetch(`${API}/zoho/contacts?contact_type=vendor&per_page=200`, { headers }),
        fetch(`${API}/zoho/bills?per_page=200`, { headers })
      ]);
      const [vcData, vendorsData, billsData] = await Promise.all([vcRes.json(), vendorsRes.json(), billsRes.json()]);
      setCredits(vcData.vendorcredits || []);
      setVendors(vendorsData.contacts || []);
      setBills(billsData.bills || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.name || newLineItem.rate <= 0) return toast.error("Enter item details");
    setNewVC({ ...newVC, line_items: [...newVC.line_items, { ...newLineItem }] });
    setNewLineItem({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });
  };

  const calculateTotal = () => newVC.line_items.reduce((sum, i) => sum + i.quantity * i.rate * (1 + i.tax_percentage / 100), 0);

  const handleCreate = async () => {
    if (!newVC.vendor_id) return toast.error("Select a vendor");
    if (!newVC.reason) return toast.error("Enter reason");
    if (!newVC.line_items.length) return toast.error("Add at least one item");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/vendorcredits`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newVC)
      });
      if (res.ok) {
        toast.success("Vendor credit created");
        setShowCreateDialog(false);
        setNewVC({ vendor_id: "", vendor_name: "", reason: "", line_items: [], notes: "" });
        fetchData();
      }
    } catch { toast.error("Error creating vendor credit"); }
  };

  const handleApplyToBill = async () => {
    if (!selectedVC || !selectedBill || applyAmount <= 0) return toast.error("Select bill and enter amount");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/vendorcredits/${selectedVC.vendorcredit_id}/bills/${selectedBill}/apply?amount=${applyAmount}`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Credit applied to bill");
        setShowApplyDialog(false);
        setApplyAmount(0);
        setSelectedBill("");
        fetchData();
      }
    } catch { toast.error("Error applying credit"); }
  };

  const vendorBills = bills.filter(b => b.vendor_id === selectedVC?.vendor_id && b.balance > 0);

  return (
    <div className="space-y-6" data-testid="vendor-credits-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-bw-white">Vendor Credits</h1>
          <p className="text-bw-white/[0.45] text-sm mt-1">Credits from vendors</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold" data-testid="create-vc-btn">
              <Plus className="h-4 w-4 mr-2" /> New Vendor Credit
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Create Vendor Credit</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Vendor *</Label>
                  <Select onValueChange={(v) => {
                    const vendor = vendors.find(x => x.contact_id === v);
                    if (vendor) setNewVC({ ...newVC, vendor_id: vendor.contact_id, vendor_name: vendor.contact_name });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select vendor" /></SelectTrigger>
                    <SelectContent>{vendors.map(v => <SelectItem key={v.contact_id} value={v.contact_id}>{v.contact_name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Reason *</Label>
                  <Select value={newVC.reason} onValueChange={(v) => setNewVC({ ...newVC, reason: v })}>
                    <SelectTrigger><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Purchase Return">Purchase Return</SelectItem>
                      <SelectItem value="Defective Goods">Defective Goods</SelectItem>
                      <SelectItem value="Price Adjustment">Price Adjustment</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="border rounded-lg p-4 bg-bw-panel">
                <h3 className="font-medium mb-3">Add Items</h3>
                <div className="grid grid-cols-4 gap-3">
                  <Input value={newLineItem.name} onChange={(e) => setNewLineItem({ ...newLineItem, name: e.target.value })} placeholder="Item name" />
                  <Input type="number" value={newLineItem.quantity} onChange={(e) => setNewLineItem({ ...newLineItem, quantity: parseFloat(e.target.value) })} placeholder="Qty" />
                  <Input type="number" value={newLineItem.rate} onChange={(e) => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) })} placeholder="Rate" />
                  <Button onClick={handleAddLineItem} className="bg-bw-volt text-bw-black font-bold">Add</Button>
                </div>
              </div>
              {newVC.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-bw-panel"><tr><th className="px-3 py-2 text-left">Item</th><th className="px-3 py-2 text-right">Qty</th><th className="px-3 py-2 text-right">Rate</th><th className="px-3 py-2 text-right">Amount</th><th></th></tr></thead>
                    <tbody>
                      {newVC.line_items.map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{item.name}</td>
                          <td className="px-3 py-2 text-right">{item.quantity}</td>
                          <td className="px-3 py-2 text-right">₹{item.rate}</td>
                          <td className="px-3 py-2 text-right">₹{(item.quantity * item.rate * (1 + item.tax_percentage / 100)).toLocaleString('en-IN')}</td>
                          <td className="px-3 py-2"><Button variant="ghost" size="icon" onClick={() => setNewVC({ ...newVC, line_items: newVC.line_items.filter((_, i) => i !== idx) })}><Trash2 className="h-4 w-4 text-red-500" /></Button></td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-bw-panel font-semibold"><tr><td colSpan={3} className="px-3 py-2 text-right">Total:</td><td className="px-3 py-2 text-right">₹{calculateTotal().toLocaleString('en-IN')}</td><td></td></tr></tfoot>
                  </table>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreate} className="bg-bw-volt text-bw-black font-bold">Create</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? <div className="text-center py-12 text-bw-white/[0.45]">Loading...</div> :
        credits.length === 0 ? <Card><CardContent className="py-12 text-center text-bw-white/[0.45]">No vendor credits found</CardContent></Card> :
        <div className="space-y-3">
          {credits.map(vc => (
            <Card key={vc.vendorcredit_id} className="border border-white/[0.07] hover:border-bw-volt/20 transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold">{vc.vendorcredit_number}</h3>
                      <Badge className={statusColors[vc.status]}>{vc.status}</Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-bw-white/[0.45]">
                      <span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{vc.vendor_name}</span>
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{vc.date}</span>
                      <span className="flex items-center gap-1"><FileText className="h-3.5 w-3.5" />{vc.reason}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-bold text-lg">₹{vc.total?.toLocaleString('en-IN')}</p>
                      {vc.credits_remaining > 0 && <p className="text-xs text-bw-blue">Available: ₹{vc.credits_remaining?.toLocaleString('en-IN')}</p>}
                    </div>
                    {vc.credits_remaining > 0 && (
                      <Button size="sm" className="bg-bw-volt text-bw-black font-bold" onClick={() => { setSelectedVC(vc); setApplyAmount(vc.credits_remaining); setShowApplyDialog(true); }}>
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

      <Dialog open={showApplyDialog} onOpenChange={setShowApplyDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Apply Credit to Bill</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Select Bill *</Label>
              <Select value={selectedBill} onValueChange={setSelectedBill}>
                <SelectTrigger><SelectValue placeholder="Select bill" /></SelectTrigger>
                <SelectContent>
                  {vendorBills.map(bill => <SelectItem key={bill.bill_id} value={bill.bill_id}>{bill.bill_number} - ₹{bill.balance?.toLocaleString('en-IN')} due</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Amount to Apply *</Label>
              <Input type="number" value={applyAmount} onChange={(e) => setApplyAmount(parseFloat(e.target.value))} max={selectedVC?.credits_remaining} />
              <p className="text-xs text-bw-white/[0.45] mt-1">Max: ₹{selectedVC?.credits_remaining?.toLocaleString('en-IN')}</p>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowApplyDialog(false)}>Cancel</Button>
            <Button onClick={handleApplyToBill} className="bg-bw-volt text-bw-black font-bold">Apply Credit</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
