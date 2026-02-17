import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Plus, FileText, Search, Edit, Trash2, RefreshCw, Send, CheckCircle, XCircle, 
  Eye, Copy, ArrowRightLeft, Clock, Calendar, User, Building2, Package,
  TrendingUp, AlertTriangle, ChevronRight, Percent, IndianRupee
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-gray-100 text-gray-700",
  sent: "bg-blue-100 text-blue-700",
  accepted: "bg-green-100 text-green-700",
  declined: "bg-red-100 text-red-700",
  expired: "bg-orange-100 text-orange-700",
  converted: "bg-purple-100 text-purple-700",
  void: "bg-gray-200 text-gray-500"
};

const statusLabels = {
  draft: "Draft",
  sent: "Sent",
  accepted: "Accepted",
  declined: "Declined",
  expired: "Expired",
  converted: "Converted",
  void: "Void"
};

export default function EstimatesEnhanced() {
  const [activeTab, setActiveTab] = useState("estimates");
  const [estimates, setEstimates] = useState([]);
  const [summary, setSummary] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [selectedEstimate, setSelectedEstimate] = useState(null);

  // Contact search
  const [contacts, setContacts] = useState([]);
  const [contactSearch, setContactSearch] = useState("");
  const [selectedContact, setSelectedContact] = useState(null);

  // Items search
  const [items, setItems] = useState([]);

  // Form states
  const [newEstimate, setNewEstimate] = useState({
    customer_id: "", reference_number: "", date: new Date().toISOString().split('T')[0],
    expiry_date: "", subject: "", salesperson_name: "", terms_and_conditions: "", notes: "",
    discount_type: "none", discount_value: 0, shipping_charge: 0, adjustment: 0,
    adjustment_description: "", line_items: []
  });
  const [newLineItem, setNewLineItem] = useState({
    item_id: "", name: "", description: "", quantity: 1, unit: "pcs", rate: 0,
    discount_percent: 0, tax_percentage: 18, hsn_code: ""
  });
  const [sendEmail, setSendEmail] = useState("");
  const [sendMessage, setSendMessage] = useState("");

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchEstimates(), fetchSummary(), fetchFunnel(), fetchItems()]);
    setLoading(false);
  }, []);

  const fetchEstimates = async () => {
    try {
      let url = `${API}/estimates-enhanced/?per_page=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setEstimates(data.estimates || []);
    } catch (e) { console.error("Failed to fetch estimates:", e); }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/summary`, { headers });
      const data = await res.json();
      setSummary(data.summary || null);
    } catch (e) { console.error("Failed to fetch summary:", e); }
  };

  const fetchFunnel = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/reports/conversion-funnel`, { headers });
      const data = await res.json();
      setFunnel(data.funnel || null);
    } catch (e) { console.error("Failed to fetch funnel:", e); }
  };

  const fetchItems = async () => {
    try {
      const res = await fetch(`${API}/items?per_page=200`, { headers });
      const data = await res.json();
      setItems(data.items || []);
    } catch (e) { console.error("Failed to fetch items:", e); }
  };

  const searchContacts = async (query) => {
    if (!query || query.length < 2) {
      setContacts([]);
      return;
    }
    try {
      const res = await fetch(`${API}/contact-integration/contacts/search?q=${encodeURIComponent(query)}&contact_type=customer&limit=10`, { headers });
      const data = await res.json();
      setContacts(data.contacts || []);
    } catch (e) { console.error("Failed to search contacts:", e); }
  };

  const fetchEstimateDetail = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}`, { headers });
      const data = await res.json();
      setSelectedEstimate(data.estimate);
      setShowDetailDialog(true);
    } catch (e) { toast.error("Failed to fetch estimate details"); }
  };

  // CRUD
  const handleCreateEstimate = async () => {
    if (!newEstimate.customer_id) return toast.error("Please select a customer");
    if (newEstimate.line_items.length === 0) return toast.error("Add at least one line item");
    try {
      const res = await fetch(`${API}/estimates-enhanced/`, { method: "POST", headers, body: JSON.stringify(newEstimate) });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Estimate ${data.estimate.estimate_number} created`);
        setShowCreateDialog(false);
        resetForm();
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create estimate");
      }
    } catch (e) { toast.error("Error creating estimate"); }
  };

  const handleDeleteEstimate = async (estimateId) => {
    if (!confirm("Delete this estimate?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Estimate deleted");
        setShowDetailDialog(false);
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Cannot delete estimate");
      }
    } catch (e) { toast.error("Error deleting estimate"); }
  };

  const handleSendEstimate = async () => {
    if (!selectedEstimate) return;
    try {
      const url = `${API}/estimates-enhanced/${selectedEstimate.estimate_id}/send?email_to=${encodeURIComponent(sendEmail)}&message=${encodeURIComponent(sendMessage)}`;
      const res = await fetch(url, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success("Estimate sent!");
        setShowSendDialog(false);
        setSendEmail("");
        setSendMessage("");
        fetchEstimateDetail(selectedEstimate.estimate_id);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to send estimate");
      }
    } catch (e) { toast.error("Error sending estimate"); }
  };

  const handleMarkAccepted = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/mark-accepted`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Estimate marked as accepted");
        fetchEstimateDetail(estimateId);
        fetchData();
      }
    } catch (e) { toast.error("Error updating status"); }
  };

  const handleMarkDeclined = async (estimateId) => {
    const reason = prompt("Enter decline reason (optional):");
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/mark-declined?reason=${encodeURIComponent(reason || "")}`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Estimate marked as declined");
        fetchEstimateDetail(estimateId);
        fetchData();
      }
    } catch (e) { toast.error("Error updating status"); }
  };

  const handleConvertToInvoice = async (estimateId) => {
    if (!confirm("Convert this estimate to an invoice?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/convert-to-invoice`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Converted to Invoice ${data.invoice_number}`);
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to convert");
      }
    } catch (e) { toast.error("Error converting estimate"); }
  };

  const handleConvertToSO = async (estimateId) => {
    if (!confirm("Convert this estimate to a sales order?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/convert-to-sales-order`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Converted to Sales Order ${data.salesorder_number}`);
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to convert");
      }
    } catch (e) { toast.error("Error converting estimate"); }
  };

  const handleClone = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/clone`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Cloned as ${data.estimate_number}`);
        fetchData();
      }
    } catch (e) { toast.error("Error cloning estimate"); }
  };

  // Line items
  const addLineItem = () => {
    if (!newLineItem.name) return toast.error("Item name is required");
    const item = {
      ...newLineItem,
      gross_amount: newLineItem.quantity * newLineItem.rate,
      discount: (newLineItem.quantity * newLineItem.rate * newLineItem.discount_percent) / 100,
      taxable_amount: newLineItem.quantity * newLineItem.rate * (1 - newLineItem.discount_percent / 100),
      tax_amount: newLineItem.quantity * newLineItem.rate * (1 - newLineItem.discount_percent / 100) * (newLineItem.tax_percentage / 100),
      total: newLineItem.quantity * newLineItem.rate * (1 - newLineItem.discount_percent / 100) * (1 + newLineItem.tax_percentage / 100)
    };
    setNewEstimate(prev => ({ ...prev, line_items: [...prev.line_items, item] }));
    setNewLineItem({ item_id: "", name: "", description: "", quantity: 1, unit: "pcs", rate: 0, discount_percent: 0, tax_percentage: 18, hsn_code: "" });
  };

  const removeLineItem = (index) => {
    setNewEstimate(prev => ({ ...prev, line_items: prev.line_items.filter((_, i) => i !== index) }));
  };

  const selectItem = (item) => {
    setNewLineItem({
      item_id: item.item_id,
      name: item.name,
      description: item.description || "",
      quantity: 1,
      unit: item.unit || "pcs",
      rate: item.rate || item.sales_rate || 0,
      discount_percent: 0,
      tax_percentage: item.tax_percentage || 18,
      hsn_code: item.hsn_code || ""
    });
  };

  const calculateTotals = () => {
    const subtotal = newEstimate.line_items.reduce((sum, item) => sum + (item.taxable_amount || 0), 0);
    const totalTax = newEstimate.line_items.reduce((sum, item) => sum + (item.tax_amount || 0), 0);
    let discount = 0;
    if (newEstimate.discount_type === "percent") discount = subtotal * (newEstimate.discount_value / 100);
    else if (newEstimate.discount_type === "amount") discount = newEstimate.discount_value;
    const grandTotal = subtotal - discount + totalTax + (newEstimate.shipping_charge || 0) + (newEstimate.adjustment || 0);
    return { subtotal, totalTax, discount, grandTotal };
  };

  const resetForm = () => {
    setNewEstimate({
      customer_id: "", reference_number: "", date: new Date().toISOString().split('T')[0],
      expiry_date: "", subject: "", salesperson_name: "", terms_and_conditions: "", notes: "",
      discount_type: "none", discount_value: 0, shipping_charge: 0, adjustment: 0,
      adjustment_description: "", line_items: []
    });
    setSelectedContact(null);
    setContactSearch("");
  };

  const totals = calculateTotals();

  return (
    <div className="space-y-6" data-testid="estimates-enhanced-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Estimates & Quotes</h1>
          <p className="text-gray-500 text-sm mt-1">Create, send, and convert estimates to invoices</p>
        </div>
        <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="text-xs text-gray-500">Total</p>
                  <p className="text-xl font-bold">{summary.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Draft</p>
              <p className="text-lg font-bold">{summary.by_status?.draft || 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Sent</p>
              <p className="text-lg font-bold text-blue-700">{summary.by_status?.sent || 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-green-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Accepted</p>
              <p className="text-lg font-bold text-green-700">{summary.by_status?.accepted || 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-orange-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Expired</p>
              <p className="text-lg font-bold text-orange-700">{summary.by_status?.expired || 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-purple-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Converted</p>
              <p className="text-lg font-bold text-purple-700">{summary.by_status?.converted || 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-green-100 border-green-300">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Total Value</p>
              <p className="text-lg font-bold text-green-700">₹{(summary.total_value || 0).toLocaleString('en-IN')}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Conversion Funnel */}
      {funnel && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><TrendingUp className="h-4 w-4" /> Conversion Funnel</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between text-xs">
              <div className="text-center">
                <p className="text-gray-500">Created</p>
                <p className="text-xl font-bold">{funnel.total_created}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-300" />
              <div className="text-center">
                <p className="text-gray-500">Sent</p>
                <p className="text-xl font-bold">{funnel.sent_to_customer}</p>
                <p className="text-blue-600">{funnel.send_rate}%</p>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-300" />
              <div className="text-center">
                <p className="text-gray-500">Accepted</p>
                <p className="text-xl font-bold">{funnel.accepted}</p>
                <p className="text-green-600">{funnel.acceptance_rate}%</p>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-300" />
              <div className="text-center">
                <p className="text-gray-500">Converted</p>
                <p className="text-xl font-bold">{funnel.converted}</p>
                <p className="text-purple-600">{funnel.conversion_rate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="estimates">Estimates</TabsTrigger>
          <TabsTrigger value="create">Create New</TabsTrigger>
        </TabsList>

        {/* Estimates Tab */}
        <TabsContent value="estimates" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 max-w-xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input value={search} onChange={(e) => setSearch(e.target.value)} onKeyUp={(e) => e.key === 'Enter' && fetchEstimates()} placeholder="Search estimates..." className="pl-10" data-testid="search-estimates" />
              </div>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setTimeout(fetchEstimates, 100); }}>
                <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="sent">Sent</SelectItem>
                  <SelectItem value="accepted">Accepted</SelectItem>
                  <SelectItem value="declined">Declined</SelectItem>
                  <SelectItem value="expired">Expired</SelectItem>
                  <SelectItem value="converted">Converted</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setActiveTab("create")} className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-estimate-btn">
              <Plus className="h-4 w-4" /> New Estimate
            </Button>
          </div>

          {loading ? <div className="text-center py-8">Loading...</div> : estimates.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No estimates found</p></CardContent></Card>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Estimate #</th>
                    <th className="px-4 py-3 text-left font-medium">Customer</th>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Expiry</th>
                    <th className="px-4 py-3 text-right font-medium">Amount</th>
                    <th className="px-4 py-3 text-center font-medium">Status</th>
                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {estimates.map(est => (
                    <tr key={est.estimate_id} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => fetchEstimateDetail(est.estimate_id)} data-testid={`estimate-row-${est.estimate_id}`}>
                      <td className="px-4 py-3 font-mono font-medium">{est.estimate_number}</td>
                      <td className="px-4 py-3">{est.customer_name}</td>
                      <td className="px-4 py-3 text-gray-600">{est.date}</td>
                      <td className="px-4 py-3 text-gray-600">{est.expiry_date}</td>
                      <td className="px-4 py-3 text-right font-medium">₹{(est.grand_total || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={statusColors[est.status]}>{statusLabels[est.status]}</Badge>
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button size="icon" variant="ghost" onClick={() => fetchEstimateDetail(est.estimate_id)}><Eye className="h-4 w-4" /></Button>
                        <Button size="icon" variant="ghost" onClick={() => handleClone(est.estimate_id)}><Copy className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        {/* Create Tab */}
        <TabsContent value="create" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Create New Estimate</CardTitle>
              <CardDescription>Fill in the details and add line items</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Customer Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Customer *</Label>
                  <div className="relative">
                    <Input 
                      value={contactSearch} 
                      onChange={(e) => { setContactSearch(e.target.value); searchContacts(e.target.value); }}
                      placeholder="Search customer..."
                      data-testid="customer-search"
                    />
                    {contacts.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                        {contacts.map(c => (
                          <div 
                            key={c.contact_id} 
                            className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                            onClick={() => {
                              setSelectedContact(c);
                              setNewEstimate(prev => ({ ...prev, customer_id: c.contact_id }));
                              setContactSearch(c.name);
                              setContacts([]);
                            }}
                          >
                            <p className="font-medium">{c.name}</p>
                            <p className="text-xs text-gray-500">{c.company_name} {c.gstin && `• ${c.gstin}`}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedContact && (
                    <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                      <p><strong>{selectedContact.name}</strong></p>
                      {selectedContact.email && <p>{selectedContact.email}</p>}
                      {selectedContact.gstin && <p>GSTIN: {selectedContact.gstin}</p>}
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Date</Label>
                    <Input type="date" value={newEstimate.date} onChange={(e) => setNewEstimate({...newEstimate, date: e.target.value})} />
                  </div>
                  <div>
                    <Label>Expiry Date</Label>
                    <Input type="date" value={newEstimate.expiry_date} onChange={(e) => setNewEstimate({...newEstimate, expiry_date: e.target.value})} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div><Label>Reference #</Label><Input value={newEstimate.reference_number} onChange={(e) => setNewEstimate({...newEstimate, reference_number: e.target.value})} placeholder="PO-123" /></div>
                <div><Label>Subject</Label><Input value={newEstimate.subject} onChange={(e) => setNewEstimate({...newEstimate, subject: e.target.value})} placeholder="Quote for..." /></div>
                <div><Label>Salesperson</Label><Input value={newEstimate.salesperson_name} onChange={(e) => setNewEstimate({...newEstimate, salesperson_name: e.target.value})} /></div>
              </div>

              <Separator />

              {/* Line Items */}
              <div>
                <h4 className="font-medium mb-3">Line Items</h4>
                
                {/* Add Item Form */}
                <div className="grid grid-cols-12 gap-2 mb-4 items-end">
                  <div className="col-span-3">
                    <Label className="text-xs">Item</Label>
                    <Select value={newLineItem.item_id || "custom"} onValueChange={(v) => {
                      if (v === "custom") {
                        setNewLineItem({...newLineItem, item_id: "", name: ""});
                      } else {
                        const item = items.find(i => i.item_id === v);
                        if (item) selectItem(item);
                      }
                    }}>
                      <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="custom">Custom Item</SelectItem>
                        {items.map(item => (
                          <SelectItem key={item.item_id} value={item.item_id}>{item.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-xs">Name</Label>
                    <Input value={newLineItem.name} onChange={(e) => setNewLineItem({...newLineItem, name: e.target.value})} placeholder="Item name" />
                  </div>
                  <div className="col-span-1">
                    <Label className="text-xs">Qty</Label>
                    <Input type="number" value={newLineItem.quantity} onChange={(e) => setNewLineItem({...newLineItem, quantity: parseFloat(e.target.value) || 0})} min="0" />
                  </div>
                  <div className="col-span-1">
                    <Label className="text-xs">Rate</Label>
                    <Input type="number" value={newLineItem.rate} onChange={(e) => setNewLineItem({...newLineItem, rate: parseFloat(e.target.value) || 0})} min="0" />
                  </div>
                  <div className="col-span-1">
                    <Label className="text-xs">Disc %</Label>
                    <Input type="number" value={newLineItem.discount_percent} onChange={(e) => setNewLineItem({...newLineItem, discount_percent: parseFloat(e.target.value) || 0})} min="0" max="100" />
                  </div>
                  <div className="col-span-1">
                    <Label className="text-xs">Tax %</Label>
                    <Input type="number" value={newLineItem.tax_percentage} onChange={(e) => setNewLineItem({...newLineItem, tax_percentage: parseFloat(e.target.value) || 0})} min="0" />
                  </div>
                  <div className="col-span-1">
                    <Label className="text-xs">HSN</Label>
                    <Input value={newLineItem.hsn_code} onChange={(e) => setNewLineItem({...newLineItem, hsn_code: e.target.value})} />
                  </div>
                  <div className="col-span-2">
                    <Button onClick={addLineItem} className="w-full"><Plus className="h-4 w-4 mr-1" /> Add</Button>
                  </div>
                </div>

                {/* Line Items Table */}
                {newEstimate.line_items.length > 0 && (
                  <div className="border rounded-lg overflow-hidden mb-4">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left">Item</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-right">Rate</th>
                          <th className="px-3 py-2 text-right">Disc</th>
                          <th className="px-3 py-2 text-right">Tax</th>
                          <th className="px-3 py-2 text-right">Total</th>
                          <th className="px-3 py-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {newEstimate.line_items.map((item, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="px-3 py-2">{item.name}</td>
                            <td className="px-3 py-2 text-right">{item.quantity}</td>
                            <td className="px-3 py-2 text-right">₹{item.rate}</td>
                            <td className="px-3 py-2 text-right">{item.discount_percent}%</td>
                            <td className="px-3 py-2 text-right">{item.tax_percentage}%</td>
                            <td className="px-3 py-2 text-right font-medium">₹{item.total?.toFixed(2)}</td>
                            <td className="px-3 py-2"><Button size="icon" variant="ghost" onClick={() => removeLineItem(idx)}><Trash2 className="h-4 w-4 text-red-500" /></Button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Totals */}
                <div className="flex justify-end">
                  <div className="w-64 space-y-2 text-sm">
                    <div className="flex justify-between"><span>Subtotal:</span><span>₹{totals.subtotal.toFixed(2)}</span></div>
                    <div className="flex justify-between items-center gap-2">
                      <span>Discount:</span>
                      <div className="flex gap-1">
                        <Select value={newEstimate.discount_type} onValueChange={(v) => setNewEstimate({...newEstimate, discount_type: v})}>
                          <SelectTrigger className="w-20 h-7"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            <SelectItem value="percent">%</SelectItem>
                            <SelectItem value="amount">₹</SelectItem>
                          </SelectContent>
                        </Select>
                        {newEstimate.discount_type !== "none" && (
                          <Input type="number" className="w-16 h-7" value={newEstimate.discount_value} onChange={(e) => setNewEstimate({...newEstimate, discount_value: parseFloat(e.target.value) || 0})} />
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between"><span>Tax:</span><span>₹{totals.totalTax.toFixed(2)}</span></div>
                    <div className="flex justify-between items-center">
                      <span>Shipping:</span>
                      <Input type="number" className="w-24 h-7" value={newEstimate.shipping_charge} onChange={(e) => setNewEstimate({...newEstimate, shipping_charge: parseFloat(e.target.value) || 0})} />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Adjustment:</span>
                      <Input type="number" className="w-24 h-7" value={newEstimate.adjustment} onChange={(e) => setNewEstimate({...newEstimate, adjustment: parseFloat(e.target.value) || 0})} />
                    </div>
                    <Separator />
                    <div className="flex justify-between font-bold text-lg"><span>Grand Total:</span><span>₹{totals.grandTotal.toFixed(2)}</span></div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Notes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><Label>Terms & Conditions</Label><Textarea value={newEstimate.terms_and_conditions} onChange={(e) => setNewEstimate({...newEstimate, terms_and_conditions: e.target.value})} rows={3} /></div>
                <div><Label>Notes</Label><Textarea value={newEstimate.notes} onChange={(e) => setNewEstimate({...newEstimate, notes: e.target.value})} rows={3} /></div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={resetForm}>Reset</Button>
                <Button onClick={handleCreateEstimate} className="bg-[#22EDA9] text-black" data-testid="create-estimate-submit">Create Estimate</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedEstimate && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      {selectedEstimate.estimate_number}
                      <Badge className={statusColors[selectedEstimate.status]}>{statusLabels[selectedEstimate.status]}</Badge>
                      {selectedEstimate.is_expired && <Badge variant="destructive">Expired</Badge>}
                    </DialogTitle>
                    <DialogDescription>{selectedEstimate.customer_name}</DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {/* Info Grid */}
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div><p className="text-gray-500">Date</p><p className="font-medium">{selectedEstimate.date}</p></div>
                  <div><p className="text-gray-500">Expiry</p><p className="font-medium">{selectedEstimate.expiry_date}</p></div>
                  <div><p className="text-gray-500">Reference</p><p className="font-medium">{selectedEstimate.reference_number || '-'}</p></div>
                  <div><p className="text-gray-500">GSTIN</p><p className="font-medium font-mono text-xs">{selectedEstimate.customer_gstin || '-'}</p></div>
                </div>

                <Separator />

                {/* Line Items */}
                <div>
                  <h4 className="font-medium mb-2">Line Items ({selectedEstimate.line_items?.length || 0})</h4>
                  {selectedEstimate.line_items?.length > 0 && (
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-left">Item</th>
                            <th className="px-3 py-2 text-left">HSN</th>
                            <th className="px-3 py-2 text-right">Qty</th>
                            <th className="px-3 py-2 text-right">Rate</th>
                            <th className="px-3 py-2 text-right">Tax</th>
                            <th className="px-3 py-2 text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedEstimate.line_items.map((item, idx) => (
                            <tr key={idx} className="border-t">
                              <td className="px-3 py-2">
                                <p className="font-medium">{item.name}</p>
                                {item.description && <p className="text-xs text-gray-500">{item.description}</p>}
                              </td>
                              <td className="px-3 py-2 font-mono text-xs">{item.hsn_code || '-'}</td>
                              <td className="px-3 py-2 text-right">{item.quantity} {item.unit}</td>
                              <td className="px-3 py-2 text-right">₹{item.rate?.toLocaleString('en-IN')}</td>
                              <td className="px-3 py-2 text-right">{item.tax_percentage}%</td>
                              <td className="px-3 py-2 text-right font-medium">₹{item.total?.toLocaleString('en-IN')}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Totals */}
                <div className="flex justify-end">
                  <div className="w-64 space-y-1 text-sm">
                    <div className="flex justify-between"><span>Subtotal:</span><span>₹{selectedEstimate.subtotal?.toLocaleString('en-IN')}</span></div>
                    {selectedEstimate.total_discount > 0 && <div className="flex justify-between text-red-600"><span>Discount:</span><span>-₹{selectedEstimate.total_discount?.toLocaleString('en-IN')}</span></div>}
                    <div className="flex justify-between"><span>Tax ({selectedEstimate.gst_type?.toUpperCase()}):</span><span>₹{selectedEstimate.total_tax?.toLocaleString('en-IN')}</span></div>
                    {selectedEstimate.shipping_charge > 0 && <div className="flex justify-between"><span>Shipping:</span><span>₹{selectedEstimate.shipping_charge?.toLocaleString('en-IN')}</span></div>}
                    {selectedEstimate.adjustment !== 0 && <div className="flex justify-between"><span>Adjustment:</span><span>₹{selectedEstimate.adjustment?.toLocaleString('en-IN')}</span></div>}
                    <Separator />
                    <div className="flex justify-between font-bold text-lg"><span>Grand Total:</span><span>₹{selectedEstimate.grand_total?.toLocaleString('en-IN')}</span></div>
                  </div>
                </div>

                <Separator />

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  {selectedEstimate.status === "draft" && (
                    <>
                      <Button variant="outline" onClick={() => { setSendEmail(selectedEstimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Send</Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteEstimate(selectedEstimate.estimate_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                    </>
                  )}
                  {selectedEstimate.status === "sent" && (
                    <>
                      <Button onClick={() => handleMarkAccepted(selectedEstimate.estimate_id)} className="bg-green-500 hover:bg-green-600"><CheckCircle className="h-4 w-4 mr-1" /> Mark Accepted</Button>
                      <Button variant="outline" onClick={() => handleMarkDeclined(selectedEstimate.estimate_id)}><XCircle className="h-4 w-4 mr-1" /> Mark Declined</Button>
                    </>
                  )}
                  {selectedEstimate.status === "accepted" && (
                    <>
                      <Button onClick={() => handleConvertToInvoice(selectedEstimate.estimate_id)} className="bg-purple-500 hover:bg-purple-600"><ArrowRightLeft className="h-4 w-4 mr-1" /> Convert to Invoice</Button>
                      <Button variant="outline" onClick={() => handleConvertToSO(selectedEstimate.estimate_id)}><ArrowRightLeft className="h-4 w-4 mr-1" /> Convert to Sales Order</Button>
                    </>
                  )}
                  {(selectedEstimate.status === "declined" || selectedEstimate.status === "expired") && (
                    <Button variant="outline" onClick={() => { setSendEmail(selectedEstimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Resend</Button>
                  )}
                  <Button variant="outline" onClick={() => handleClone(selectedEstimate.estimate_id)}><Copy className="h-4 w-4 mr-1" /> Clone</Button>
                </div>

                {/* Converted To */}
                {selectedEstimate.converted_to && (
                  <div className="bg-purple-50 rounded-lg p-3">
                    <p className="text-sm text-purple-700">
                      <strong>Converted to:</strong> {selectedEstimate.converted_to}
                    </p>
                  </div>
                )}

                {/* History */}
                {selectedEstimate.history?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">History</h4>
                    <div className="space-y-2 text-sm">
                      {selectedEstimate.history.slice(0, 5).map((h, idx) => (
                        <div key={idx} className="flex justify-between text-gray-600">
                          <span>{h.action}: {h.details}</span>
                          <span className="text-xs">{new Date(h.timestamp).toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Send Dialog */}
      <Dialog open={showSendDialog} onOpenChange={setShowSendDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Estimate</DialogTitle>
            <DialogDescription>Email this estimate to the customer</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Email To</Label>
              <Input value={sendEmail} onChange={(e) => setSendEmail(e.target.value)} placeholder="customer@example.com" />
            </div>
            <div>
              <Label>Message (optional)</Label>
              <Textarea value={sendMessage} onChange={(e) => setSendMessage(e.target.value)} placeholder="Add a personal message..." rows={3} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSendDialog(false)}>Cancel</Button>
            <Button onClick={handleSendEstimate} className="bg-[#22EDA9] text-black">Send Estimate</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
