import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Plus, ShoppingCart, Search, Trash2, RefreshCw, Send, CheckCircle, XCircle, 
  Eye, Copy, ArrowRightLeft, Package, Truck, Calendar, User, 
  TrendingUp, ChevronRight, Receipt, Box, IndianRupee, Clock, Save
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const statusColors = {
  draft: "bg-white/5 text-bw-white",
  confirmed: "bg-blue-100 text-bw-blue",
  open: "bg-bw-green/10 text-bw-green",
  partially_fulfilled: "bg-yellow-100 text-bw-amber",
  fulfilled: "bg-purple-100 text-bw-purple",
  closed: "bg-bw-card text-bw-white/[0.45]",
  void: "bg-red-100 text-red-500"
};

const statusLabels = {
  draft: "Draft",
  confirmed: "Confirmed",
  open: "Open",
  partially_fulfilled: "Partial",
  fulfilled: "Fulfilled",
  closed: "Closed",
  void: "Void"
};

const fulfillmentColors = {
  unfulfilled: "bg-red-100 text-bw-red",
  partially_fulfilled: "bg-yellow-100 text-bw-amber",
  fulfilled: "bg-bw-green/10 text-bw-green"
};

export default function SalesOrdersEnhanced() {
  const [activeTab, setActiveTab] = useState("orders");
  const [orders, setOrders] = useState([]);
  const [summary, setSummary] = useState(null);
  const [fulfillmentSummary, setFulfillmentSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [fulfillmentFilter, setFulfillmentFilter] = useState("all");

  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showFulfillDialog, setShowFulfillDialog] = useState(false);
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  // Contact search
  const [contacts, setContacts] = useState([]);
  const [contactSearch, setContactSearch] = useState("");
  const [selectedContact, setSelectedContact] = useState(null);

  // Items
  const [items, setItems] = useState([]);

  // Form states
  const initialOrderData = {
    customer_id: "", reference_number: "", date: new Date().toISOString().split('T')[0],
    expected_shipment_date: "", salesperson_name: "", terms_and_conditions: "", notes: "",
    discount_type: "none", discount_value: 0, shipping_charge: 0, adjustment: 0,
    delivery_method: "", line_items: []
  };
  
  const [newOrder, setNewOrder] = useState(initialOrderData);
  
  // Auto-save for Sales Order form
  const orderPersistence = useFormPersistence(
    'sales_order_new',
    newOrder,
    initialOrderData,
    {
      enabled: activeTab === "create",
      isDialogOpen: activeTab === "create",
      setFormData: setNewOrder,
      debounceMs: 2000,
      entityName: 'Sales Order'
    }
  );
  
  const [newLineItem, setNewLineItem] = useState({
    item_id: "", name: "", description: "", quantity: 1, unit: "pcs", rate: 0,
    discount_percent: 0, tax_percentage: 18, hsn_code: ""
  });
  const [fulfillmentItems, setFulfillmentItems] = useState([]);
  const [sendEmail, setSendEmail] = useState("");
  const [sendMessage, setSendMessage] = useState("");

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchOrders(), fetchSummary(), fetchFulfillmentSummary(), fetchItems()]);
    setLoading(false);
  }, []);

  const fetchOrders = async () => {
    try {
      let url = `${API}/sales-orders-enhanced/?per_page=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      if (fulfillmentFilter !== "all") url += `&fulfillment_status=${fulfillmentFilter}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setOrders(data.salesorders || []);
    } catch (e) { console.error("Failed to fetch orders:", e); }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/summary`, { headers });
      const data = await res.json();
      setSummary(data.summary || null);
    } catch (e) { console.error("Failed to fetch summary:", e); }
  };

  const fetchFulfillmentSummary = async () => {
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/reports/fulfillment-summary`, { headers });
      const data = await res.json();
      setFulfillmentSummary(data.summary || null);
    } catch (e) { console.error("Failed to fetch fulfillment summary:", e); }
  };

  const fetchItems = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/?per_page=200`, { headers });
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

  const fetchOrderDetail = async (orderId) => {
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/${orderId}`, { headers });
      const data = await res.json();
      setSelectedOrder(data.salesorder);
      setShowDetailDialog(true);
      // Prepare fulfillment items
      if (data.salesorder?.line_items) {
        setFulfillmentItems(data.salesorder.line_items.map(li => ({
          line_item_id: li.line_item_id,
          name: li.name,
          quantity_ordered: li.quantity_ordered || li.quantity,
          quantity_fulfilled: li.quantity_fulfilled || 0,
          quantity_to_fulfill: 0
        })));
      }
    } catch (e) { toast.error("Failed to fetch order details"); }
  };

  // CRUD
  const handleCreateOrder = async () => {
    if (!newOrder.customer_id) return toast.error("Please select a customer");
    if (newOrder.line_items.length === 0) return toast.error("Add at least one line item");
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/`, { method: "POST", headers, body: JSON.stringify(newOrder) });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Sales Order ${data.salesorder.salesorder_number} created`);
        orderPersistence.onSuccessfulSave();
        resetForm();
        setActiveTab("orders");
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create order");
      }
    } catch (e) { toast.error("Error creating order"); }
  };

  const handleDeleteOrder = async (orderId) => {
    if (!confirm("Delete this sales order?")) return;
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/${orderId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Sales Order deleted");
        setShowDetailDialog(false);
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Cannot delete order");
      }
    } catch (e) { toast.error("Error deleting order"); }
  };

  const handleConfirm = async (orderId) => {
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/${orderId}/confirm`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Sales Order confirmed & stock reserved");
        fetchOrderDetail(orderId);
        fetchData();
      }
    } catch (e) { toast.error("Error confirming order"); }
  };

  const handleVoid = async (orderId) => {
    const reason = prompt("Enter void reason:");
    if (reason === null) return;
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/${orderId}/void?reason=${encodeURIComponent(reason)}`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Sales Order voided");
        fetchOrderDetail(orderId);
        fetchData();
      }
    } catch (e) { toast.error("Error voiding order"); }
  };

  const handleFulfill = async () => {
    if (!selectedOrder) return;
    const itemsToFulfill = fulfillmentItems.filter(i => i.quantity_to_fulfill > 0);
    if (itemsToFulfill.length === 0) return toast.error("Enter quantities to fulfill");
    
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/${selectedOrder.salesorder_id}/fulfill`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          line_items: itemsToFulfill,
          shipment_date: new Date().toISOString().split('T')[0]
        })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Fulfillment created");
        setShowFulfillDialog(false);
        fetchOrderDetail(selectedOrder.salesorder_id);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to fulfill");
      }
    } catch (e) { toast.error("Error creating fulfillment"); }
  };

  const handleConvertToInvoice = async (orderId) => {
    if (!confirm("Convert this sales order to an invoice?")) return;
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/${orderId}/convert-to-invoice`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Converted to Invoice ${data.invoice_number}`);
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to convert");
      }
    } catch (e) { toast.error("Error converting order"); }
  };

  const handleSendOrder = async () => {
    if (!selectedOrder) return;
    try {
      const url = `${API}/sales-orders-enhanced/${selectedOrder.salesorder_id}/send?email_to=${encodeURIComponent(sendEmail)}&message=${encodeURIComponent(sendMessage)}`;
      const res = await fetch(url, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success("Sales Order sent!");
        setShowSendDialog(false);
        setSendEmail("");
        setSendMessage("");
        fetchOrderDetail(selectedOrder.salesorder_id);
      } else {
        toast.error(data.detail || "Failed to send");
      }
    } catch (e) { toast.error("Error sending order"); }
  };

  const handleClone = async (orderId) => {
    try {
      const res = await fetch(`${API}/sales-orders-enhanced/${orderId}/clone`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Cloned as ${data.salesorder_number}`);
        fetchData();
      }
    } catch (e) { toast.error("Error cloning order"); }
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
    setNewOrder(prev => ({ ...prev, line_items: [...prev.line_items, item] }));
    setNewLineItem({ item_id: "", name: "", description: "", quantity: 1, unit: "pcs", rate: 0, discount_percent: 0, tax_percentage: 18, hsn_code: "" });
  };

  const removeLineItem = (index) => {
    setNewOrder(prev => ({ ...prev, line_items: prev.line_items.filter((_, i) => i !== index) }));
  };

  const selectItem = (item) => {
    setNewLineItem({
      item_id: item.item_id,
      name: item.name,
      description: item.description || "",
      quantity: 1,
      unit: item.unit || "pcs",
      rate: item.sales_rate || item.rate || 0,
      discount_percent: 0,
      tax_percentage: item.tax_percentage || 18,
      hsn_code: item.hsn_code || ""
    });
  };

  const calculateTotals = () => {
    const subtotal = newOrder.line_items.reduce((sum, item) => sum + (item.taxable_amount || 0), 0);
    const totalTax = newOrder.line_items.reduce((sum, item) => sum + (item.tax_amount || 0), 0);
    let discount = 0;
    if (newOrder.discount_type === "percent") discount = subtotal * (newOrder.discount_value / 100);
    else if (newOrder.discount_type === "amount") discount = newOrder.discount_value;
    const grandTotal = subtotal - discount + totalTax + (newOrder.shipping_charge || 0) + (newOrder.adjustment || 0);
    return { subtotal, totalTax, discount, grandTotal };
  };

  const resetForm = () => {
    setNewOrder(initialOrderData);
    setSelectedContact(null);
    setContactSearch("");
  };

  const totals = calculateTotals();

  return (
    <div className="space-y-6" data-testid="sales-orders-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Sales Orders"
        description="Manage orders, fulfillments, and invoicing"
        icon={ShoppingCart}
        actions={
          <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        }
      />

      {/* Summary Cards */}
      {loading ? (
        <StatCardGrid columns={7}>
          {[...Array(7)].map((_, i) => (
            <StatCard key={i} loading title="" value="" />
          ))}
        </StatCardGrid>
      ) : summary && (
        <StatCardGrid columns={7}>
          <StatCard
            title="Total Orders"
            value={summary.total}
            icon={ShoppingCart}
            variant="info"
          />
          <StatCard
            title="Draft"
            value={summary.by_status?.draft || 0}
            icon={Clock}
            variant="default"
          />
          <StatCard
            title="Confirmed"
            value={summary.by_status?.confirmed || 0}
            icon={CheckCircle}
            variant="info"
          />
          <StatCard
            title="Open"
            value={summary.by_status?.open || 0}
            icon={Package}
            variant="success"
          />
          <StatCard
            title="Closed"
            value={summary.by_status?.closed || 0}
            icon={CheckCircle}
            variant="purple"
          />
          <StatCard
            title="Total Value"
            value={formatCurrencyCompact(summary.total_value || 0)}
            icon={IndianRupee}
            variant="success"
          />
          <StatCard
            title="Pending Invoice"
            value={formatCurrencyCompact(summary.pending_invoice || 0)}
            icon={Receipt}
            variant="warning"
          />
        </StatCardGrid>
      )}

      {/* Fulfillment Pipeline */}
      {fulfillmentSummary && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><Package className="h-4 w-4" /> Fulfillment Pipeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between text-xs">
              <div className="text-center">
                <p className="text-bw-white/[0.45]">Unfulfilled</p>
                <p className="text-xl font-bold text-bw-red">{fulfillmentSummary.unfulfilled}</p>
                <p className="text-bw-white/25">₹{(fulfillmentSummary.unfulfilled_value || 0).toLocaleString('en-IN')}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-bw-white/20" />
              <div className="text-center">
                <p className="text-bw-white/[0.45]">Partially Fulfilled</p>
                <p className="text-xl font-bold text-bw-amber">{fulfillmentSummary.partially_fulfilled}</p>
                <p className="text-bw-white/25">₹{(fulfillmentSummary.partially_fulfilled_value || 0).toLocaleString('en-IN')}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-bw-white/20" />
              <div className="text-center">
                <p className="text-bw-white/[0.45]">Fulfilled</p>
                <p className="text-xl font-bold text-bw-green">{fulfillmentSummary.fulfilled}</p>
                <p className="text-bw-white/25">₹{(fulfillmentSummary.fulfilled_value || 0).toLocaleString('en-IN')}</p>
              </div>
              <div className="text-center ml-8 border-l pl-8">
                <p className="text-bw-white/[0.45]">Fulfillment Rate</p>
                <p className="text-2xl font-bold text-bw-green">{fulfillmentSummary.fulfillment_rate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="orders">Sales Orders</TabsTrigger>
          <TabsTrigger value="create">Create New</TabsTrigger>
        </TabsList>

        {/* Orders Tab */}
        <TabsContent value="orders" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 max-w-2xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-bw-white/25" />
                <Input value={search} onChange={(e) => setSearch(e.target.value)} onKeyUp={(e) => e.key === 'Enter' && fetchOrders()} placeholder="Search orders..." className="pl-10" data-testid="search-orders" />
              </div>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setTimeout(fetchOrders, 100); }}>
                <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="confirmed">Confirmed</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="fulfilled">Fulfilled</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
              <Select value={fulfillmentFilter} onValueChange={(v) => { setFulfillmentFilter(v); setTimeout(fetchOrders, 100); }}>
                <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Fulfillment</SelectItem>
                  <SelectItem value="unfulfilled">Unfulfilled</SelectItem>
                  <SelectItem value="partially_fulfilled">Partial</SelectItem>
                  <SelectItem value="fulfilled">Fulfilled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setActiveTab("create")} className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold gap-2" data-testid="new-order-btn">
              <Plus className="h-4 w-4" /> New Sales Order
            </Button>
          </div>

          {loading ? <div className="text-center py-8">Loading...</div> : orders.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-bw-white/[0.45]"><ShoppingCart className="h-12 w-12 mx-auto mb-4 text-bw-white/20" /><p>No sales orders found</p></CardContent></Card>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-bw-panel">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Order #</th>
                    <th className="px-4 py-3 text-left font-medium">Customer</th>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Shipment</th>
                    <th className="px-4 py-3 text-right font-medium">Amount</th>
                    <th className="px-4 py-3 text-center font-medium">Status</th>
                    <th className="px-4 py-3 text-center font-medium">Fulfillment</th>
                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map(order => (
                    <tr key={order.salesorder_id} className="border-b border-white/[0.04] hover:bg-bw-panel cursor-pointer" onClick={() => fetchOrderDetail(order.salesorder_id)} data-testid={`order-row-${order.salesorder_id}`}>
                      <td className="px-4 py-3 font-mono font-medium">{order.salesorder_number}</td>
                      <td className="px-4 py-3">{order.customer_name}</td>
                      <td className="px-4 py-3 text-bw-white/[0.45]">{order.date}</td>
                      <td className="px-4 py-3 text-bw-white/[0.45]">{order.expected_shipment_date}</td>
                      <td className="px-4 py-3 text-right font-medium">₹{(order.grand_total || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={statusColors[order.status]}>{statusLabels[order.status]}</Badge>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={fulfillmentColors[order.fulfillment_status]}>{order.fulfillment_status?.replace('_', ' ')}</Badge>
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button size="icon" variant="ghost" onClick={() => fetchOrderDetail(order.salesorder_id)}><Eye className="h-4 w-4" /></Button>
                        <Button size="icon" variant="ghost" onClick={() => handleClone(order.salesorder_id)}><Copy className="h-4 w-4" /></Button>
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
          <DraftRecoveryBanner
            show={orderPersistence.showRecoveryBanner}
            savedAt={orderPersistence.savedDraftInfo?.timestamp}
            onRestore={orderPersistence.handleRestoreDraft}
            onDiscard={orderPersistence.handleDiscardDraft}
          />
          
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Create New Sales Order</CardTitle>
                  <CardDescription>Fill in the details and add line items</CardDescription>
                </div>
                <AutoSaveIndicator 
                  lastSaved={orderPersistence.lastSaved} 
                  isSaving={orderPersistence.isSaving} 
                  isDirty={orderPersistence.isDirty} 
                />
              </div>
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
                      <div className="absolute z-10 w-full mt-1 bg-bw-panel border border-white/[0.13] rounded max-h-48 overflow-y-auto">
                        {contacts.map((c, idx) => (
                          <div 
                            key={`contact-${c.contact_id}-${idx}`} 
                            className="px-3 py-2 hover:bg-white/5 cursor-pointer"
                            onClick={() => {
                              setSelectedContact(c);
                              setNewOrder(prev => ({ ...prev, customer_id: c.contact_id }));
                              setContactSearch(c.name);
                              setContacts([]);
                            }}
                          >
                            <p className="font-medium">{c.name}</p>
                            <p className="text-xs text-bw-white/[0.45]">{c.company_name} {c.gstin && `• ${c.gstin}`}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedContact && (
                    <div className="mt-2 p-2 bg-bw-panel rounded text-xs">
                      <p><strong>{selectedContact.name}</strong></p>
                      {selectedContact.email && <p>{selectedContact.email}</p>}
                      {selectedContact.gstin && <p>GSTIN: {selectedContact.gstin}</p>}
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Order Date</Label>
                    <Input type="date" value={newOrder.date} onChange={(e) => setNewOrder({...newOrder, date: e.target.value})} />
                  </div>
                  <div>
                    <Label>Expected Shipment</Label>
                    <Input type="date" value={newOrder.expected_shipment_date} onChange={(e) => setNewOrder({...newOrder, expected_shipment_date: e.target.value})} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div><Label>Reference #</Label><Input value={newOrder.reference_number} onChange={(e) => setNewOrder({...newOrder, reference_number: e.target.value})} placeholder="PO-123" /></div>
                <div><Label>Salesperson</Label><Input value={newOrder.salesperson_name} onChange={(e) => setNewOrder({...newOrder, salesperson_name: e.target.value})} /></div>
                <div>
                  <Label>Delivery Method</Label>
                  <Select value={newOrder.delivery_method} onValueChange={(v) => setNewOrder({...newOrder, delivery_method: v})}>
                    <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pickup">Pickup</SelectItem>
                      <SelectItem value="delivery">Delivery</SelectItem>
                      <SelectItem value="shipping">Shipping</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
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
                {newOrder.line_items.length > 0 && (
                  <div className="border rounded-lg overflow-hidden mb-4">
                    <table className="w-full text-sm">
                      <thead className="bg-bw-panel">
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
                        {newOrder.line_items.map((item, idx) => (
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
                        <Select value={newOrder.discount_type} onValueChange={(v) => setNewOrder({...newOrder, discount_type: v})}>
                          <SelectTrigger className="w-20 h-7"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            <SelectItem value="percent">%</SelectItem>
                            <SelectItem value="amount">₹</SelectItem>
                          </SelectContent>
                        </Select>
                        {newOrder.discount_type !== "none" && (
                          <Input type="number" className="w-16 h-7" value={newOrder.discount_value} onChange={(e) => setNewOrder({...newOrder, discount_value: parseFloat(e.target.value) || 0})} />
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between"><span>Tax:</span><span>₹{totals.totalTax.toFixed(2)}</span></div>
                    <div className="flex justify-between items-center">
                      <span>Shipping:</span>
                      <Input type="number" className="w-24 h-7" value={newOrder.shipping_charge} onChange={(e) => setNewOrder({...newOrder, shipping_charge: parseFloat(e.target.value) || 0})} />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Adjustment:</span>
                      <Input type="number" className="w-24 h-7" value={newOrder.adjustment} onChange={(e) => setNewOrder({...newOrder, adjustment: parseFloat(e.target.value) || 0})} />
                    </div>
                    <Separator />
                    <div className="flex justify-between font-bold text-lg"><span>Grand Total:</span><span>₹{totals.grandTotal.toFixed(2)}</span></div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Notes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><Label>Terms & Conditions</Label><Textarea value={newOrder.terms_and_conditions} onChange={(e) => setNewOrder({...newOrder, terms_and_conditions: e.target.value})} rows={3} /></div>
                <div><Label>Notes</Label><Textarea value={newOrder.notes} onChange={(e) => setNewOrder({...newOrder, notes: e.target.value})} rows={3} /></div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={resetForm}>Reset</Button>
                <Button onClick={handleCreateOrder} className="bg-bw-volt text-bw-black font-bold" data-testid="create-order-submit">Create Sales Order</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedOrder && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      {selectedOrder.salesorder_number}
                      <Badge className={statusColors[selectedOrder.status]}>{statusLabels[selectedOrder.status]}</Badge>
                      <Badge className={fulfillmentColors[selectedOrder.fulfillment_status]}>{selectedOrder.fulfillment_status?.replace('_', ' ')}</Badge>
                    </DialogTitle>
                    <DialogDescription>{selectedOrder.customer_name}</DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {/* Info Grid */}
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div><p className="text-bw-white/[0.45]">Order Date</p><p className="font-medium">{selectedOrder.date}</p></div>
                  <div><p className="text-bw-white/[0.45]">Expected Shipment</p><p className="font-medium">{selectedOrder.expected_shipment_date}</p></div>
                  <div><p className="text-bw-white/[0.45]">Reference</p><p className="font-medium">{selectedOrder.reference_number || '-'}</p></div>
                  <div><p className="text-bw-white/[0.45]">GSTIN</p><p className="font-medium font-mono text-xs">{selectedOrder.customer_gstin || '-'}</p></div>
                </div>

                {selectedOrder.from_estimate_number && (
                  <div className="bg-bw-blue/[0.08] rounded-lg p-3 text-sm">
                    <strong>From Estimate:</strong> {selectedOrder.from_estimate_number}
                  </div>
                )}

                <Separator />

                {/* Line Items */}
                <div>
                  <h4 className="font-medium mb-2">Line Items ({selectedOrder.line_items?.length || 0})</h4>
                  {selectedOrder.line_items?.length > 0 && (
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-bw-panel">
                          <tr>
                            <th className="px-3 py-2 text-left">Item</th>
                            <th className="px-3 py-2 text-right">Ordered</th>
                            <th className="px-3 py-2 text-right">Fulfilled</th>
                            <th className="px-3 py-2 text-right">Remaining</th>
                            <th className="px-3 py-2 text-right">Rate</th>
                            <th className="px-3 py-2 text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedOrder.line_items.map((item, idx) => (
                            <tr key={idx} className="border-t">
                              <td className="px-3 py-2">
                                <p className="font-medium">{item.name}</p>
                                {item.hsn_code && <p className="text-xs text-bw-white/[0.45]">HSN: {item.hsn_code}</p>}
                              </td>
                              <td className="px-3 py-2 text-right">{item.quantity_ordered || item.quantity} {item.unit}</td>
                              <td className="px-3 py-2 text-right text-bw-green">{item.quantity_fulfilled || 0}</td>
                              <td className="px-3 py-2 text-right text-bw-orange">{(item.quantity_ordered || item.quantity) - (item.quantity_fulfilled || 0)}</td>
                              <td className="px-3 py-2 text-right">₹{item.rate?.toLocaleString('en-IN')}</td>
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
                    <div className="flex justify-between"><span>Subtotal:</span><span>₹{selectedOrder.subtotal?.toLocaleString('en-IN')}</span></div>
                    {selectedOrder.total_discount > 0 && <div className="flex justify-between text-bw-red"><span>Discount:</span><span>-₹{selectedOrder.total_discount?.toLocaleString('en-IN')}</span></div>}
                    <div className="flex justify-between"><span>Tax ({selectedOrder.gst_type?.toUpperCase()}):</span><span>₹{selectedOrder.total_tax?.toLocaleString('en-IN')}</span></div>
                    {selectedOrder.shipping_charge > 0 && <div className="flex justify-between"><span>Shipping:</span><span>₹{selectedOrder.shipping_charge?.toLocaleString('en-IN')}</span></div>}
                    <Separator />
                    <div className="flex justify-between font-bold text-lg"><span>Grand Total:</span><span>₹{selectedOrder.grand_total?.toLocaleString('en-IN')}</span></div>
                    {selectedOrder.invoiced_amount > 0 && (
                      <div className="flex justify-between text-bw-green"><span>Invoiced:</span><span>₹{selectedOrder.invoiced_amount?.toLocaleString('en-IN')}</span></div>
                    )}
                  </div>
                </div>

                <Separator />

                {/* Fulfillments */}
                {selectedOrder.fulfillments?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Fulfillments</h4>
                    <div className="space-y-2">
                      {selectedOrder.fulfillments.map((f, idx) => (
                        <div key={idx} className="bg-bw-panel rounded-lg p-3 text-sm">
                          <div className="flex justify-between">
                            <span className="font-medium">{f.fulfillment_id}</span>
                            <span className="text-bw-white/[0.45]">{f.shipment_date}</span>
                          </div>
                          {f.tracking_number && <p className="text-xs">Tracking: {f.tracking_number}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  {selectedOrder.status === "draft" && (
                    <>
                      <Button onClick={() => handleConfirm(selectedOrder.salesorder_id)} className="bg-bw-blue hover:bg-blue-600 text-bw-black"><CheckCircle className="h-4 w-4 mr-1" /> Confirm Order</Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteOrder(selectedOrder.salesorder_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                    </>
                  )}
                  {["confirmed", "open", "partially_fulfilled"].includes(selectedOrder.status) && (
                    <>
                      <Button onClick={() => setShowFulfillDialog(true)} className="bg-bw-green hover:bg-bw-green-hover text-bw-black"><Package className="h-4 w-4 mr-1" /> Create Fulfillment</Button>
                      <Button variant="outline" onClick={() => handleConvertToInvoice(selectedOrder.salesorder_id)}><Receipt className="h-4 w-4 mr-1" /> Convert to Invoice</Button>
                    </>
                  )}
                  {selectedOrder.status !== "void" && selectedOrder.status !== "closed" && (
                    <>
                      <Button variant="outline" onClick={() => { setSendEmail(selectedOrder.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Send</Button>
                      <Button variant="destructive" onClick={() => handleVoid(selectedOrder.salesorder_id)}><XCircle className="h-4 w-4 mr-1" /> Void</Button>
                    </>
                  )}
                  <Button variant="outline" onClick={() => handleClone(selectedOrder.salesorder_id)}><Copy className="h-4 w-4 mr-1" /> Clone</Button>
                </div>

                {/* Converted To */}
                {selectedOrder.converted_to && (
                  <div className="bg-bw-purple/[0.08] rounded-lg p-3">
                    <p className="text-sm text-bw-purple">
                      <strong>Converted to:</strong> {selectedOrder.converted_to}
                    </p>
                  </div>
                )}

                {/* History */}
                {selectedOrder.history?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">History</h4>
                    <div className="space-y-2 text-sm">
                      {selectedOrder.history.slice(0, 5).map((h, idx) => (
                        <div key={idx} className="flex justify-between text-bw-white/[0.45]">
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

      {/* Fulfillment Dialog */}
      <Dialog open={showFulfillDialog} onOpenChange={setShowFulfillDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create Fulfillment</DialogTitle>
            <DialogDescription>Enter quantities to ship/fulfill</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-bw-panel">
                  <tr>
                    <th className="px-3 py-2 text-left">Item</th>
                    <th className="px-3 py-2 text-right">Ordered</th>
                    <th className="px-3 py-2 text-right">Fulfilled</th>
                    <th className="px-3 py-2 text-right">Remaining</th>
                    <th className="px-3 py-2 text-right">Qty to Fulfill</th>
                  </tr>
                </thead>
                <tbody>
                  {fulfillmentItems.map((item, idx) => {
                    const remaining = item.quantity_ordered - item.quantity_fulfilled;
                    return (
                      <tr key={idx} className="border-t">
                        <td className="px-3 py-2">{item.name}</td>
                        <td className="px-3 py-2 text-right">{item.quantity_ordered}</td>
                        <td className="px-3 py-2 text-right text-bw-green">{item.quantity_fulfilled}</td>
                        <td className="px-3 py-2 text-right text-bw-orange">{remaining}</td>
                        <td className="px-3 py-2 text-right">
                          <Input 
                            type="number" 
                            className="w-20 h-7 text-right" 
                            value={item.quantity_to_fulfill}
                            min={0}
                            max={remaining}
                            onChange={(e) => {
                              const val = Math.min(parseFloat(e.target.value) || 0, remaining);
                              setFulfillmentItems(prev => prev.map((fi, i) => 
                                i === idx ? {...fi, quantity_to_fulfill: val} : fi
                              ));
                            }}
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFulfillDialog(false)}>Cancel</Button>
            <Button onClick={handleFulfill} className="bg-bw-volt text-bw-black font-bold">Create Fulfillment</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Send Dialog */}
      <Dialog open={showSendDialog} onOpenChange={setShowSendDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Sales Order</DialogTitle>
            <DialogDescription>Email this sales order to the customer</DialogDescription>
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
            <Button onClick={handleSendOrder} className="bg-bw-volt text-bw-black font-bold">Send Order</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
