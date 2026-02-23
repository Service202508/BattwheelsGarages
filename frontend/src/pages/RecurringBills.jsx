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
  Plus, RefreshCw, Calendar, Building, Pause, Play, Trash2, 
  IndianRupee, Clock, FileText
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  active: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  stopped: "bg-yellow-100 text-[#EAB308]",
  expired: "bg-[rgba(255,255,255,0.05)] text-gray-600"
};

const frequencyLabels = {
  weekly: "Weekly",
  monthly: "Monthly",
  yearly: "Yearly",
  custom: "Custom"
};

export default function RecurringBills() {
  const [bills, setBills] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedBill, setSelectedBill] = useState(null);

  const [newBill, setNewBill] = useState({
    vendor_id: "",
    vendor_name: "",
    recurrence_name: "",
    recurrence_frequency: "monthly",
    repeat_every: 1,
    start_date: new Date().toISOString().split("T")[0],
    end_date: "",
    never_expires: true,
    line_items: [],
    payment_terms: 30,
    notes: ""
  });

  const [newLineItem, setNewLineItem] = useState({
    name: "", description: "", quantity: 1, rate: 0, tax_percentage: 18
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [billsRes, vendorsRes] = await Promise.all([
        fetch(`${API}/zoho/recurring-bills`, { headers }),
        fetch(`${API}/zoho/contacts?contact_type=vendor&per_page=200`, { headers })
      ]);
      const [billsData, vendorsData] = await Promise.all([
        billsRes.json(), vendorsRes.json()
      ]);
      setBills(billsData.recurring_bills || []);
      setVendors(vendorsData.contacts || []);
    } catch (error) {
      console.error("Failed to fetch:", error);
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.name || newLineItem.rate <= 0) {
      return toast.error("Enter item name and rate");
    }
    setNewBill({ ...newBill, line_items: [...newBill.line_items, { ...newLineItem }] });
    setNewLineItem({ name: "", description: "", quantity: 1, rate: 0, tax_percentage: 18 });
  };

  const removeLineItem = (index) => {
    setNewBill({ 
      ...newBill, 
      line_items: newBill.line_items.filter((_, i) => i !== index) 
    });
  };

  const calculateTotal = () => newBill.line_items.reduce((sum, item) => {
    const subtotal = item.quantity * item.rate;
    const tax = subtotal * (item.tax_percentage / 100);
    return sum + subtotal + tax;
  }, 0);

  const handleCreate = async () => {
    if (!newBill.vendor_id) return toast.error("Select a vendor");
    if (!newBill.recurrence_name) return toast.error("Enter a name for this recurring bill");
    if (!newBill.line_items.length) return toast.error("Add at least one line item");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/recurring-bills`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newBill)
      });
      if (res.ok) {
        toast.success("Recurring bill created");
        setShowCreateDialog(false);
        setNewBill({
          vendor_id: "", vendor_name: "", recurrence_name: "",
          recurrence_frequency: "monthly", repeat_every: 1,
          start_date: new Date().toISOString().split("T")[0],
          end_date: "", never_expires: true, line_items: [],
          payment_terms: 30, notes: ""
        });
        fetchData();
      } else {
        toast.error("Failed to create recurring bill");
      }
    } catch {
      toast.error("Error creating recurring bill");
    }
  };

  const handleAction = async (billId, action) => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/recurring-bills/${billId}/${action}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success(`Recurring bill ${action === "stop" ? "stopped" : "resumed"}`);
        fetchData();
      }
    } catch {
      toast.error("Action failed");
    }
  };

  const handleDelete = async (billId) => {
    if (!confirm("Delete this recurring bill?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/recurring-bills/${billId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Recurring bill deleted");
        fetchData();
      }
    } catch {
      toast.error("Failed to delete");
    }
  };

  const handleGenerateDue = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/recurring-bills/generate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      toast.success(data.message);
      fetchData();
    } catch {
      toast.error("Failed to generate bills");
    }
  };

  const activeBills = bills.filter(b => b.status === "active");
  const stoppedBills = bills.filter(b => b.status === "stopped");
  const totalMonthly = activeBills.reduce((sum, b) => {
    if (b.recurrence_frequency === "monthly") return sum + b.total;
    if (b.recurrence_frequency === "weekly") return sum + (b.total * 4);
    if (b.recurrence_frequency === "yearly") return sum + (b.total / 12);
    return sum;
  }, 0);

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6" data-testid="recurring-bills-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Recurring Bills</h1>
          <p className="text-gray-500">Automate your vendor payments</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleGenerateDue} data-testid="generate-due-btn">
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate Due Bills
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button data-testid="create-recurring-bill-btn">
                <Plus className="h-4 w-4 mr-2" />
                New Recurring Bill
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Recurring Bill</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Vendor *</Label>
                    <Select
                      value={newBill.vendor_id}
                      onValueChange={(value) => {
                        const vendor = vendors.find(v => v.contact_id === value);
                        setNewBill({ 
                          ...newBill, 
                          vendor_id: value,
                          vendor_name: vendor?.contact_name || ""
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select vendor" />
                      </SelectTrigger>
                      <SelectContent>
                        {vendors.map(v => (
                          <SelectItem key={v.contact_id} value={v.contact_id}>
                            {v.contact_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Recurrence Name *</Label>
                    <Input
                      value={newBill.recurrence_name}
                      onChange={e => setNewBill({ ...newBill, recurrence_name: e.target.value })}
                      placeholder="e.g., Monthly Office Rent"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Frequency</Label>
                    <Select
                      value={newBill.recurrence_frequency}
                      onValueChange={v => setNewBill({ ...newBill, recurrence_frequency: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="yearly">Yearly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Repeat Every</Label>
                    <Input
                      type="number"
                      min="1"
                      value={newBill.repeat_every}
                      onChange={e => setNewBill({ ...newBill, repeat_every: parseInt(e.target.value) || 1 })}
                    />
                  </div>
                  <div>
                    <Label>Payment Terms (days)</Label>
                    <Input
                      type="number"
                      value={newBill.payment_terms}
                      onChange={e => setNewBill({ ...newBill, payment_terms: parseInt(e.target.value) || 30 })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Start Date *</Label>
                    <Input
                      type="date"
                      value={newBill.start_date}
                      onChange={e => setNewBill({ ...newBill, start_date: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>End Date (optional)</Label>
                    <Input
                      type="date"
                      value={newBill.end_date}
                      onChange={e => setNewBill({ ...newBill, end_date: e.target.value, never_expires: !e.target.value })}
                    />
                  </div>
                </div>

                {/* Line Items */}
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-3">Line Items</h4>
                  <div className="grid grid-cols-5 gap-2 mb-2">
                    <Input
                      placeholder="Item Name"
                      value={newLineItem.name}
                      onChange={e => setNewLineItem({ ...newLineItem, name: e.target.value })}
                    />
                    <Input
                      type="number"
                      placeholder="Qty"
                      value={newLineItem.quantity}
                      onChange={e => setNewLineItem({ ...newLineItem, quantity: parseInt(e.target.value) || 1 })}
                    />
                    <Input
                      type="number"
                      placeholder="Rate"
                      value={newLineItem.rate}
                      onChange={e => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) || 0 })}
                    />
                    <Input
                      type="number"
                      placeholder="Tax %"
                      value={newLineItem.tax_percentage}
                      onChange={e => setNewLineItem({ ...newLineItem, tax_percentage: parseFloat(e.target.value) || 0 })}
                    />
                    <Button type="button" onClick={handleAddLineItem} variant="outline">Add</Button>
                  </div>

                  {newBill.line_items.length > 0 && (
                    <div className="space-y-2 mt-3">
                      {newBill.line_items.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center bg-[#111820] p-2 rounded">
                          <span>{item.name} × {item.quantity}</span>
                          <span>₹{(item.quantity * item.rate * (1 + item.tax_percentage/100)).toLocaleString()}</span>
                          <Button size="sm" variant="ghost" onClick={() => removeLineItem(idx)}>
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      ))}
                      <div className="text-right font-bold pt-2 border-t">
                        Total: ₹{calculateTotal().toLocaleString()}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <Label>Notes</Label>
                  <Input
                    value={newBill.notes}
                    onChange={e => setNewBill({ ...newBill, notes: e.target.value })}
                    placeholder="Optional notes"
                  />
                </div>

                <Button className="w-full" onClick={handleCreate}>Create Recurring Bill</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <RefreshCw className="h-5 w-5 text-[#3B9EFF]" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Profiles</p>
                <p className="text-2xl font-bold">{bills.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Play className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Active</p>
                <p className="text-2xl font-bold">{activeBills.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Pause className="h-5 w-5 text-[#EAB308]" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Stopped</p>
                <p className="text-2xl font-bold">{stoppedBills.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <IndianRupee className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Monthly Estimate</p>
                <p className="text-2xl font-bold">₹{totalMonthly.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bills List */}
      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active">Active ({activeBills.length})</TabsTrigger>
          <TabsTrigger value="stopped">Stopped ({stoppedBills.length})</TabsTrigger>
          <TabsTrigger value="all">All ({bills.length})</TabsTrigger>
        </TabsList>

        {["active", "stopped", "all"].map(tab => (
          <TabsContent key={tab} value={tab}>
            <Card>
              <CardContent className="p-0">
                <table className="w-full">
                  <thead className="bg-[#111820] border-b">
                    <tr>
                      <th className="text-left p-4 font-medium">Name</th>
                      <th className="text-left p-4 font-medium">Vendor</th>
                      <th className="text-left p-4 font-medium">Frequency</th>
                      <th className="text-left p-4 font-medium">Next Bill</th>
                      <th className="text-right p-4 font-medium">Amount</th>
                      <th className="text-center p-4 font-medium">Status</th>
                      <th className="text-right p-4 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(tab === "all" ? bills : bills.filter(b => b.status === tab)).map(bill => (
                      <tr key={bill.recurring_bill_id} className="border-b hover:bg-[#111820]">
                        <td className="p-4">
                          <div className="font-medium">{bill.recurrence_name}</div>
                          <div className="text-sm text-gray-500">{bill.bills_generated} bills generated</div>
                        </td>
                        <td className="p-4">{bill.vendor_name}</td>
                        <td className="p-4">
                          Every {bill.repeat_every > 1 ? `${bill.repeat_every} ` : ""}{frequencyLabels[bill.recurrence_frequency] || bill.recurrence_frequency}
                        </td>
                        <td className="p-4">{bill.next_bill_date}</td>
                        <td className="p-4 text-right font-medium">₹{bill.total?.toLocaleString()}</td>
                        <td className="p-4 text-center">
                          <Badge className={statusColors[bill.status]}>{bill.status}</Badge>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex justify-end gap-1">
                            {bill.status === "active" ? (
                              <Button size="sm" variant="ghost" onClick={() => handleAction(bill.recurring_bill_id, "stop")}>
                                <Pause className="h-4 w-4" />
                              </Button>
                            ) : bill.status === "stopped" ? (
                              <Button size="sm" variant="ghost" onClick={() => handleAction(bill.recurring_bill_id, "resume")}>
                                <Play className="h-4 w-4" />
                              </Button>
                            ) : null}
                            <Button size="sm" variant="ghost" onClick={() => handleDelete(bill.recurring_bill_id)}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {(tab === "all" ? bills : bills.filter(b => b.status === tab)).length === 0 && (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-gray-500">
                          No recurring bills found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
