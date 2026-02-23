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
  Search, Plus, FileText, Calendar, User, ArrowRight, 
  Eye, Send, Check, X, Clock
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  sent: "bg-blue-100 text-[#3B9EFF]",
  accepted: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  declined: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  expired: "bg-orange-100 text-[#FF8C00]",
  invoiced: "bg-purple-100 text-[#8B5CF6]"
};

export default function Quotes() {
  const [quotes, setQuotes] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [services, setServices] = useState([]);
  const [parts, setParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);

  const [newQuote, setNewQuote] = useState({
    customer_id: "",
    customer_name: "",
    line_items: [],
    place_of_supply: "DL",
    notes: ""
  });

  const [newLineItem, setNewLineItem] = useState({
    item_id: "", item_name: "", item_type: "service",
    quantity: 1, rate: 0, discount_percent: 0, tax_rate: 18
  });

  useEffect(() => { fetchData(); }, [statusFilter]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [qRes, cRes, sRes, pRes] = await Promise.all([
        fetch(`${API}/erp/quotes?status=${statusFilter}&limit=100`, { headers }),
        fetch(`${API}/books/customers?limit=200`, { headers }),
        fetch(`${API}/books/services?limit=200`, { headers }),
        fetch(`${API}/books/parts?limit=200`, { headers })
      ]);
      const [qData, cData, sData, pData] = await Promise.all([
        qRes.json(), cRes.json(), sRes.json(), pRes.json()
      ]);
      setQuotes(qData.quotes || []);
      setCustomers(cData.customers || []);
      setServices(sData.items || []);
      setParts(pData.items || []);
    } catch (error) {
      console.error("Failed to fetch:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectItem = (itemId, type) => {
    const items = type === 'service' ? services : parts;
    const item = items.find(i => i.item_id === itemId);
    if (item) {
      setNewLineItem({
        ...newLineItem, item_id: item.item_id, item_name: item.name,
        item_type: type, rate: item.rate || 0, tax_rate: item.tax_rate || 18
      });
    }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.item_name) return toast.error("Select an item");
    setNewQuote({ ...newQuote, line_items: [...newQuote.line_items, { ...newLineItem }] });
    setNewLineItem({ item_id: "", item_name: "", item_type: "service", quantity: 1, rate: 0, discount_percent: 0, tax_rate: 18 });
  };

  const calculateTotal = () => newQuote.line_items.reduce((sum, i) => {
    const sub = i.quantity * i.rate;
    const tax = sub * (i.tax_rate / 100);
    return sum + sub + tax;
  }, 0);

  const handleCreateQuote = async () => {
    if (!newQuote.customer_id) return toast.error("Select a customer");
    if (!newQuote.line_items.length) return toast.error("Add at least one item");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/erp/quotes`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newQuote)
      });
      if (res.ok) {
        toast.success("Quote created");
        setShowCreateDialog(false);
        setNewQuote({ customer_id: "", customer_name: "", line_items: [], place_of_supply: "DL", notes: "" });
        fetchData();
      }
    } catch { toast.error("Error creating quote"); }
  };

  const handleConvert = async (quoteId, target) => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/erp/quotes/${quoteId}/convert-to-${target}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success(`Converted to ${target}`);
        fetchData();
      }
    } catch { toast.error("Conversion failed"); }
  };

  return (
    <div className="space-y-6" data-testid="quotes-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Quotes / Estimates</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">{quotes.length} quotes</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
              <Plus className="h-4 w-4 mr-2" /> New Quote
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Quote</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Customer *</Label>
                  <Select onValueChange={(v) => {
                    const c = customers.find(x => x.customer_id === v);
                    if (c) setNewQuote({ ...newQuote, customer_id: c.customer_id, customer_name: c.display_name });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select customer" /></SelectTrigger>
                    <SelectContent>
                      {customers.map(c => <SelectItem key={c.customer_id} value={c.customer_id}>{c.display_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Place of Supply</Label>
                  <Select value={newQuote.place_of_supply} onValueChange={(v) => setNewQuote({ ...newQuote, place_of_supply: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DL">Delhi</SelectItem>
                      <SelectItem value="HR">Haryana</SelectItem>
                      <SelectItem value="UP">Uttar Pradesh</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="border rounded-lg p-4 bg-[#111820]">
                <h3 className="font-medium mb-3">Add Items</h3>
                <Tabs defaultValue="services">
                  <TabsList className="mb-3">
                    <TabsTrigger value="services">Services</TabsTrigger>
                    <TabsTrigger value="parts">Parts</TabsTrigger>
                  </TabsList>
                  <TabsContent value="services">
                    <Select onValueChange={(v) => handleSelectItem(v, 'service')}>
                      <SelectTrigger><SelectValue placeholder="Select service" /></SelectTrigger>
                      <SelectContent>
                        {services.slice(0,50).map(s => <SelectItem key={s.item_id} value={s.item_id}>{s.name} - ₹{s.rate}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </TabsContent>
                  <TabsContent value="parts">
                    <Select onValueChange={(v) => handleSelectItem(v, 'part')}>
                      <SelectTrigger><SelectValue placeholder="Select part" /></SelectTrigger>
                      <SelectContent>
                        {parts.slice(0,50).map(p => <SelectItem key={p.item_id} value={p.item_id}>{p.name} - ₹{p.rate}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </TabsContent>
                </Tabs>
                {newLineItem.item_name && (
                  <div className="mt-3 grid grid-cols-4 gap-3">
                    <Input value={newLineItem.item_name} readOnly className="bg-[#111820]" />
                    <Input type="number" value={newLineItem.quantity} onChange={(e) => setNewLineItem({ ...newLineItem, quantity: parseFloat(e.target.value) })} placeholder="Qty" />
                    <Input type="number" value={newLineItem.rate} onChange={(e) => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) })} placeholder="Rate" />
                    <Button onClick={handleAddLineItem} className="bg-[#C8FF00] text-[#080C0F] font-bold">Add</Button>
                  </div>
                )}
              </div>

              {newQuote.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-3 py-2 text-left">Item</th>
                        <th className="px-3 py-2 text-right">Qty</th>
                        <th className="px-3 py-2 text-right">Rate</th>
                        <th className="px-3 py-2 text-right">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {newQuote.line_items.map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{item.item_name}</td>
                          <td className="px-3 py-2 text-right">{item.quantity}</td>
                          <td className="px-3 py-2 text-right">₹{item.rate}</td>
                          <td className="px-3 py-2 text-right">₹{(item.quantity * item.rate * (1 + item.tax_rate/100)).toLocaleString('en-IN')}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-[#111820] font-semibold">
                      <tr><td colSpan={3} className="px-3 py-2 text-right">Total:</td><td className="px-3 py-2 text-right">₹{calculateTotal().toLocaleString('en-IN')}</td></tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreateQuote} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create Quote</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["", "draft", "sent", "accepted", "expired"].map(s => (
          <Button key={s} size="sm" variant={statusFilter === s ? "default" : "outline"}
            onClick={() => setStatusFilter(s)}
            className={statusFilter === s ? "bg-[#C8FF00] text-[#080C0F] font-bold" : ""}>
            {s || "All"}
          </Button>
        ))}
      </div>

      {loading ? <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</div> :
        quotes.length === 0 ? <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No quotes found</CardContent></Card> :
        <div className="space-y-3">
          {quotes.map(q => (
            <Card key={q.quote_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold">{q.quote_number}</h3>
                      <Badge className={statusColors[q.status]}>{q.status}</Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                      <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" />{q.customer_name}</span>
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{q.quote_date}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />Expires: {q.expiry_date}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-bold text-lg">₹{q.total?.toLocaleString('en-IN')}</p>
                    </div>
                    {q.status === "draft" && (
                      <div className="flex gap-1">
                        <Button size="sm" variant="outline" onClick={() => handleConvert(q.quote_id, 'salesorder')}>
                          <ArrowRight className="h-4 w-4 mr-1" /> SO
                        </Button>
                        <Button size="sm" className="bg-[#C8FF00] text-[#080C0F] font-bold" onClick={() => handleConvert(q.quote_id, 'invoice')}>
                          <ArrowRight className="h-4 w-4 mr-1" /> Invoice
                        </Button>
                      </div>
                    )}
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
