import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { 
  Plus, FileText, Calendar, Building2, Eye, CheckCircle, Send,
  Clock, IndianRupee, Trash2, CreditCard, Copy, XCircle, Receipt,
  AlertTriangle, TrendingUp, Truck, MoreHorizontal, Search, Filter, Save
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const statusColors = {
  draft: "bg-bw-white/5 text-bw-white/35 border border-white/[0.08]",
  open: "bg-blue-100 text-bw-blue",
  partially_paid: "bg-yellow-100 text-bw-amber",
  paid: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25",
  overdue: "bg-bw-red/10 text-bw-red border border-bw-red/25",
  void: "bg-bw-white/5 text-bw-white/25 border border-white/[0.08]"
};

const poStatusColors = {
  draft: "bg-bw-white/5 text-bw-white/35 border border-white/[0.08]",
  issued: "bg-blue-100 text-bw-blue",
  received: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25",
  billed: "bg-purple-100 text-bw-purple",
  void: "bg-bw-white/5 text-bw-white/25 border border-white/[0.08]"
};

export default function BillsEnhanced() {
  const [activeTab, setActiveTab] = useState("bills");
  const [bills, setBills] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [summary, setSummary] = useState({});
  const [poSummary, setPoSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  
  // Dialogs
  const [showCreateBill, setShowCreateBill] = useState(false);
  const [showCreatePO, setShowCreatePO] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showPODetailDialog, setShowPODetailDialog] = useState(false);
  const [selectedBill, setSelectedBill] = useState(null);
  const [selectedPO, setSelectedPO] = useState(null);
  const [billDetail, setBillDetail] = useState(null);
  const [poDetail, setPoDetail] = useState(null);

  // Form state
  const initialBillData = {
    vendor_id: "",
    bill_number: "",
    reference_number: "",
    bill_date: new Date().toISOString().split('T')[0],
    payment_terms: 30,
    line_items: [],
    discount_type: "percentage",
    discount_value: 0,
    tds_applicable: false,
    tds_rate: 0,
    vendor_notes: ""
  };

  const initialPOData = {
    vendor_id: "",
    reference_number: "",
    order_date: new Date().toISOString().split('T')[0],
    expected_delivery_date: "",
    delivery_address: "",
    line_items: [],
    discount_type: "percentage",
    discount_value: 0,
    shipping_charge: 0,
    vendor_notes: "",
    terms_conditions: ""
  };

  const [newBill, setNewBill] = useState(initialBillData);
  const [newPO, setNewPO] = useState(initialPOData);

  const [newLineItem, setNewLineItem] = useState({
    name: "", description: "", hsn_sac_code: "", quantity: 1, unit: "pcs", rate: 0, tax_rate: 18
  });

  const [payment, setPayment] = useState({
    amount: 0, payment_mode: "bank_transfer", reference_number: "", payment_date: new Date().toISOString().split('T')[0], notes: ""
  });

  // Auto-save for Bill form
  const billPersistence = useFormPersistence(
    'bill_new',
    newBill,
    initialBillData,
    {
      enabled: showCreateBill,
      isDialogOpen: showCreateBill,
      setFormData: setNewBill,
      debounceMs: 2000,
      entityName: 'Bill'
    }
  );

  // Auto-save for Purchase Order form
  const poPersistence = useFormPersistence(
    'bill_po_new',
    newPO,
    initialPOData,
    {
      enabled: showCreatePO,
      isDialogOpen: showCreatePO,
      setFormData: setNewPO,
      debounceMs: 2000,
      entityName: 'Purchase Order'
    }
  );

  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

  useEffect(() => { fetchData(); }, [statusFilter, searchQuery]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append("status", statusFilter);
      if (searchQuery) params.append("search", searchQuery);

      const [billsRes, poRes, vendorsRes, summaryRes, poSummaryRes] = await Promise.all([
        fetch(`${API}/bills-enhanced/?${params}`, { headers }),
        fetch(`${API}/bills-enhanced/purchase-orders?${params}`, { headers }),
        fetch(`${API}/contacts-enhanced/?contact_type=vendor&per_page=500`, { headers }),
        fetch(`${API}/bills-enhanced/summary`, { headers }),
        fetch(`${API}/bills-enhanced/purchase-orders/summary`, { headers })
      ]);

      const [billsData, poData, vendorsData, summaryData, poSummaryData] = await Promise.all([
        billsRes.json(), poRes.json(), vendorsRes.json(), summaryRes.json(), poSummaryRes.json()
      ]);

      setBills(billsData.bills || []);
      setPurchaseOrders(poData.purchase_orders || []);
      setVendors(vendorsData.contacts || []);
      setSummary(summaryData.summary || {});
      setPoSummary(poSummaryData.summary || {});
    } catch (error) {
      console.error("Failed to fetch:", error);
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  // Bill operations
  const handleAddLineItem = (target = "bill") => {
    if (!newLineItem.name || newLineItem.rate <= 0) {
      return toast.error("Enter item name and rate");
    }
    const item = { ...newLineItem };
    if (target === "bill") {
      setNewBill({ ...newBill, line_items: [...newBill.line_items, item] });
    } else {
      setNewPO({ ...newPO, line_items: [...newPO.line_items, item] });
    }
    setNewLineItem({ name: "", description: "", hsn_sac_code: "", quantity: 1, unit: "pcs", rate: 0, tax_rate: 18 });
  };

  const removeLineItem = (index, target = "bill") => {
    if (target === "bill") {
      setNewBill({ ...newBill, line_items: newBill.line_items.filter((_, i) => i !== index) });
    } else {
      setNewPO({ ...newPO, line_items: newPO.line_items.filter((_, i) => i !== index) });
    }
  };

  const calculateLineTotal = (items) => {
    return items.reduce((sum, item) => {
      const amount = item.quantity * item.rate;
      const tax = amount * (item.tax_rate / 100);
      return sum + amount + tax;
    }, 0);
  };

  const handleCreateBill = async () => {
    if (!newBill.vendor_id) return toast.error("Select a vendor");
    if (!newBill.line_items.length) return toast.error("Add at least one item");

    try {
      const res = await fetch(`${API}/bills-enhanced/`, {
        method: "POST",
        headers,
        body: JSON.stringify(newBill)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Bill created successfully");
        billPersistence.onSuccessfulSave();
        setShowCreateBill(false);
        resetBillForm();
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create bill");
      }
    } catch (error) {
      toast.error("Error creating bill");
    }
  };

  const handleCreatePO = async () => {
    if (!newPO.vendor_id) return toast.error("Select a vendor");
    if (!newPO.line_items.length) return toast.error("Add at least one item");

    try {
      const res = await fetch(`${API}/bills-enhanced/purchase-orders`, {
        method: "POST",
        headers,
        body: JSON.stringify(newPO)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Purchase order created");
        poPersistence.onSuccessfulSave();
        setShowCreatePO(false);
        resetPOForm();
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create PO");
      }
    } catch (error) {
      toast.error("Error creating purchase order");
    }
  };

  const resetBillForm = () => {
    setNewBill(initialBillData);
  };

  const resetPOForm = () => {
    setNewPO(initialPOData);
  };

  const viewBillDetail = async (billId) => {
    try {
      const res = await fetch(`${API}/bills-enhanced/${billId}`, { headers });
      const data = await res.json();
      if (res.ok) {
        setBillDetail(data.bill);
        setSelectedBill(data.bill);
        setShowDetailDialog(true);
      }
    } catch (error) {
      toast.error("Failed to load bill details");
    }
  };

  const viewPODetail = async (poId) => {
    try {
      const res = await fetch(`${API}/bills-enhanced/purchase-orders/${poId}`, { headers });
      const data = await res.json();
      if (res.ok) {
        setPoDetail(data.purchase_order);
        setSelectedPO(data.purchase_order);
        setShowPODetailDialog(true);
      }
    } catch (error) {
      toast.error("Failed to load PO details");
    }
  };

  const openBill = async (billId) => {
    try {
      const res = await fetch(`${API}/bills-enhanced/${billId}/open`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Bill opened");
        fetchData();
        if (showDetailDialog) viewBillDetail(billId);
      }
    } catch { toast.error("Failed to open bill"); }
  };

  const voidBill = async (billId, reason = "") => {
    try {
      const res = await fetch(`${API}/bills-enhanced/${billId}/void?reason=${encodeURIComponent(reason)}`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Bill voided");
        fetchData();
        setShowDetailDialog(false);
      }
    } catch { toast.error("Failed to void bill"); }
  };

  const cloneBill = async (billId) => {
    try {
      const res = await fetch(`${API}/bills-enhanced/${billId}/clone`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Bill cloned");
        fetchData();
      }
    } catch { toast.error("Failed to clone bill"); }
  };

  const recordPayment = async () => {
    if (!selectedBill || payment.amount <= 0) return toast.error("Enter valid amount");

    try {
      const res = await fetch(`${API}/bills-enhanced/${selectedBill.bill_id}/payments`, {
        method: "POST",
        headers,
        body: JSON.stringify(payment)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Payment recorded");
        setShowPaymentDialog(false);
        setPayment({ amount: 0, payment_mode: "bank_transfer", reference_number: "", payment_date: new Date().toISOString().split('T')[0], notes: "" });
        fetchData();
        if (showDetailDialog) viewBillDetail(selectedBill.bill_id);
      } else {
        toast.error(data.detail || "Failed to record payment");
      }
    } catch (error) {
      toast.error("Error recording payment");
    }
  };

  const issuePO = async (poId) => {
    try {
      const res = await fetch(`${API}/bills-enhanced/purchase-orders/${poId}/issue`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Purchase order issued");
        fetchData();
        if (showPODetailDialog) viewPODetail(poId);
      }
    } catch { toast.error("Failed to issue PO"); }
  };

  const receivePO = async (poId) => {
    try {
      const res = await fetch(`${API}/bills-enhanced/purchase-orders/${poId}/receive`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Purchase order marked as received");
        fetchData();
        if (showPODetailDialog) viewPODetail(poId);
      }
    } catch { toast.error("Failed to mark PO received"); }
  };

  const convertPOToBill = async (poId) => {
    try {
      const res = await fetch(`${API}/bills-enhanced/purchase-orders/${poId}/convert-to-bill`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Bill ${data.bill?.bill_number || ''} created from PO`);
        fetchData();
        setShowPODetailDialog(false);
      } else {
        toast.error(data.detail || "Failed to convert PO to bill");
      }
    } catch { toast.error("Failed to convert PO to bill"); }
  };

  return (
    <div className="space-y-6" data-testid="bills-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Purchases"
        description="Bills, Purchase Orders & Vendor Payments"
        icon={FileText}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowCreatePO(true)} data-testid="create-po-btn">
              <Truck className="h-4 w-4 mr-2" /> New PO
            </Button>
            <Button className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold" onClick={() => setShowCreateBill(true)} data-testid="create-bill-btn">
              <Plus className="h-4 w-4 mr-2" /> New Bill
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <StatCardGrid columns={6}>
        <StatCard
          title="Total Bills"
          value={summary.total_bills || 0}
          icon={Receipt}
          variant="info"
        />
        <StatCard
          title="Draft"
          value={summary.draft || 0}
          icon={FileText}
          variant="default"
        />
        <StatCard
          title="Open"
          value={summary.open || 0}
          icon={Clock}
          variant="info"
        />
        <StatCard
          title="Overdue"
          value={summary.overdue || 0}
          icon={AlertTriangle}
          variant="danger"
        />
        <StatCard
          title="Total Payable"
          value={formatCurrencyCompact(summary.total_payable || 0)}
          icon={IndianRupee}
          variant="warning"
        />
        <StatCard
          title="Total Paid"
          value={formatCurrencyCompact(summary.total_paid || 0)}
          icon={CheckCircle}
          variant="success"
        />
      </StatCardGrid>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
          <TabsList>
            <TabsTrigger value="bills" data-testid="tab-bills">Bills</TabsTrigger>
            <TabsTrigger value="purchase-orders" data-testid="tab-purchase-orders">Purchase Orders</TabsTrigger>
            <TabsTrigger value="overdue" data-testid="tab-overdue">Overdue</TabsTrigger>
          </TabsList>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-bw-white/[0.45]" />
              <Input 
                placeholder="Search..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 w-64"
              />
            </div>
            <Select value={statusFilter || "all"} onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="partially_paid">Partially Paid</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="overdue">Overdue</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Bills Tab */}
        <TabsContent value="bills">
          {loading ? (
            <div className="text-center py-12 text-bw-white/[0.45]">Loading...</div>
          ) : bills.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-bw-white/[0.45]">No bills found</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {bills.map(bill => (
                <Card key={bill.bill_id} className="border border-white/[0.07] hover:border-bw-volt/20 transition-colors cursor-pointer" onClick={() => viewBillDetail(bill.bill_id)}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-semibold">{bill.bill_number}</h3>
                          <Badge className={statusColors[bill.status]}>{bill.status?.replace('_', ' ')}</Badge>
                        </div>
                        <div className="flex gap-4 text-sm text-bw-white/[0.45]">
                          <span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{bill.vendor_name}</span>
                          <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{bill.bill_date}</span>
                          <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />Due: {bill.due_date}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-bold text-lg">₹{(bill.grand_total || 0).toLocaleString('en-IN')}</p>
                          {bill.balance_due > 0 && (
                            <p className="text-xs text-bw-orange">Due: ₹{bill.balance_due.toLocaleString('en-IN')}</p>
                          )}
                        </div>
                        {bill.status !== "paid" && bill.status !== "void" && bill.status !== "draft" && (
                          <Button 
                            size="sm" 
                            className="bg-bw-volt text-bw-black font-bold"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedBill(bill);
                              setPayment({ ...payment, amount: bill.balance_due });
                              setShowPaymentDialog(true);
                            }}
                          >
                            <CreditCard className="h-4 w-4 mr-1" /> Pay
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Purchase Orders Tab */}
        <TabsContent value="purchase-orders">
          {loading ? (
            <div className="text-center py-12 text-bw-white/[0.45]">Loading...</div>
          ) : purchaseOrders.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-bw-white/[0.45]">No purchase orders found</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {purchaseOrders.map(po => (
                <Card key={po.po_id} className="border border-white/[0.07] hover:border-bw-volt/20 transition-colors cursor-pointer" onClick={() => viewPODetail(po.po_id)}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-semibold">{po.po_number}</h3>
                          <Badge className={poStatusColors[po.status]}>{po.status}</Badge>
                        </div>
                        <div className="flex gap-4 text-sm text-bw-white/[0.45]">
                          <span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{po.vendor_name}</span>
                          <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{po.order_date}</span>
                          {po.expected_delivery_date && (
                            <span className="flex items-center gap-1"><Truck className="h-3.5 w-3.5" />Expected: {po.expected_delivery_date}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <p className="font-bold text-lg">₹{(po.grand_total || 0).toLocaleString('en-IN')}</p>
                        {po.status === "draft" && (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={(e) => { e.stopPropagation(); issuePO(po.po_id); }}
                          >
                            <Send className="h-4 w-4 mr-1" /> Issue
                          </Button>
                        )}
                        {po.status === "issued" && (
                          <Button 
                            size="sm" 
                            className="bg-bw-volt text-bw-black font-bold"
                            onClick={(e) => { e.stopPropagation(); receivePO(po.po_id); }}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" /> Receive
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Overdue Tab */}
        <TabsContent value="overdue">
          {loading ? (
            <div className="text-center py-12 text-bw-white/[0.45]">Loading...</div>
          ) : (
            <div className="space-y-3">
              {bills.filter(b => b.status === "overdue").length === 0 ? (
                <Card><CardContent className="py-12 text-center text-bw-white/[0.45] flex flex-col items-center gap-2">
                  <CheckCircle className="h-12 w-12 text-green-300" />
                  <p>No overdue bills!</p>
                </CardContent></Card>
              ) : (
                bills.filter(b => b.status === "overdue").map(bill => (
                  <Card key={bill.bill_id} className="border border-white/[0.07] hover:border-bw-volt/20 transition-colors border-l-4 border-l-red-500 cursor-pointer" onClick={() => viewBillDetail(bill.bill_id)}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-3 mb-1">
                            <h3 className="font-semibold">{bill.bill_number}</h3>
                            <Badge className="bg-bw-red/10 text-bw-red border border-bw-red/25">Overdue</Badge>
                          </div>
                          <div className="flex gap-4 text-sm text-bw-white/[0.45]">
                            <span><Building2 className="h-3.5 w-3.5 inline mr-1" />{bill.vendor_name}</span>
                            <span className="text-red-600"><AlertTriangle className="h-3.5 w-3.5 inline mr-1" />Due: {bill.due_date}</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-lg text-red-600">₹{(bill.balance_due || 0).toLocaleString('en-IN')}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Bill Dialog */}
      <Dialog 
        open={showCreateBill} 
        onOpenChange={(open) => {
          if (!open && billPersistence.isDirty) {
            billPersistence.setShowCloseConfirm(true);
          } else {
            if (!open) billPersistence.clearSavedData();
            setShowCreateBill(open);
          }
        }}
      >
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle>Create New Bill</DialogTitle>
              <AutoSaveIndicator 
                lastSaved={billPersistence.lastSaved} 
                isSaving={billPersistence.isSaving} 
                isDirty={billPersistence.isDirty} 
              />
            </div>
          </DialogHeader>
          
          <DraftRecoveryBanner
            show={billPersistence.showRecoveryBanner}
            savedAt={billPersistence.savedDraftInfo?.timestamp}
            onRestore={billPersistence.handleRestoreDraft}
            onDiscard={billPersistence.handleDiscardDraft}
          />
          
          <ScrollArea className="max-h-[calc(90vh-120px)]">
            <div className="space-y-4 p-1">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Vendor *</Label>
                  <Select onValueChange={(v) => setNewBill({ ...newBill, vendor_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select vendor" /></SelectTrigger>
                    <SelectContent>
                      {vendors.map(v => <SelectItem key={v.contact_id} value={v.contact_id}>{v.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Bill Number</Label>
                  <Input 
                    value={newBill.bill_number} 
                    onChange={(e) => setNewBill({ ...newBill, bill_number: e.target.value })} 
                    placeholder="Auto-generated if empty"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Bill Date</Label>
                  <Input type="date" value={newBill.bill_date} onChange={(e) => setNewBill({ ...newBill, bill_date: e.target.value })} />
                </div>
                <div>
                  <Label>Payment Terms (Days)</Label>
                  <Input type="number" value={newBill.payment_terms} onChange={(e) => setNewBill({ ...newBill, payment_terms: parseInt(e.target.value) })} />
                </div>
                <div>
                  <Label>Reference Number</Label>
                  <Input value={newBill.reference_number} onChange={(e) => setNewBill({ ...newBill, reference_number: e.target.value })} placeholder="Vendor Invoice #" />
                </div>
              </div>

              {/* Line Items */}
              <div className="border rounded-lg p-4 bg-bw-panel">
                <h3 className="font-medium mb-3">Line Items</h3>
                <div className="grid grid-cols-6 gap-2 mb-3">
                  <Input className="col-span-2" placeholder="Item name *" value={newLineItem.name} onChange={(e) => setNewLineItem({ ...newLineItem, name: e.target.value })} />
                  <Input type="number" placeholder="Qty" value={newLineItem.quantity} onChange={(e) => setNewLineItem({ ...newLineItem, quantity: parseFloat(e.target.value) || 1 })} />
                  <Input type="number" placeholder="Rate *" value={newLineItem.rate || ""} onChange={(e) => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) || 0 })} />
                  <Input type="number" placeholder="Tax %" value={newLineItem.tax_rate} onChange={(e) => setNewLineItem({ ...newLineItem, tax_rate: parseFloat(e.target.value) || 0 })} />
                  <Button onClick={() => handleAddLineItem("bill")} className="bg-bw-volt text-bw-black font-bold">Add</Button>
                </div>

                {newBill.line_items.length > 0 && (
                  <div className="border rounded overflow-hidden bg-bw-panel">
                    <table className="w-full text-sm">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="px-3 py-2 text-left">Item</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-right">Rate</th>
                          <th className="px-3 py-2 text-right">Tax</th>
                          <th className="px-3 py-2 text-right">Amount</th>
                          <th className="px-3 py-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {newBill.line_items.map((item, idx) => {
                          const amount = item.quantity * item.rate;
                          const tax = amount * (item.tax_rate / 100);
                          return (
                            <tr key={idx} className="border-t">
                              <td className="px-3 py-2">{item.name}</td>
                              <td className="px-3 py-2 text-right">{item.quantity}</td>
                              <td className="px-3 py-2 text-right">₹{item.rate.toLocaleString('en-IN')}</td>
                              <td className="px-3 py-2 text-right">{item.tax_rate}%</td>
                              <td className="px-3 py-2 text-right">₹{(amount + tax).toLocaleString('en-IN')}</td>
                              <td className="px-3 py-2">
                                <Button variant="ghost" size="icon" onClick={() => removeLineItem(idx, "bill")}>
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                      <tfoot className="bg-bw-panel font-semibold">
                        <tr>
                          <td colSpan={4} className="px-3 py-2 text-right">Total:</td>
                          <td className="px-3 py-2 text-right">₹{calculateLineTotal(newBill.line_items).toLocaleString('en-IN')}</td>
                          <td></td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </div>

              <div>
                <Label>Notes</Label>
                <Textarea value={newBill.vendor_notes} onChange={(e) => setNewBill({ ...newBill, vendor_notes: e.target.value })} placeholder="Internal notes" />
              </div>
            </div>
          </ScrollArea>
          <div className="flex justify-end gap-2 mt-4">
            <Button 
              variant="outline" 
              onClick={() => {
                if (billPersistence.isDirty) {
                  billPersistence.setShowCloseConfirm(true);
                } else {
                  setShowCreateBill(false);
                  resetBillForm();
                }
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateBill} className="bg-bw-volt text-bw-black font-bold">Create Bill</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create PO Dialog */}
      <Dialog 
        open={showCreatePO} 
        onOpenChange={(open) => {
          if (!open && poPersistence.isDirty) {
            poPersistence.setShowCloseConfirm(true);
          } else {
            if (!open) poPersistence.clearSavedData();
            setShowCreatePO(open);
          }
        }}
      >
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle>Create Purchase Order</DialogTitle>
              <AutoSaveIndicator 
                lastSaved={poPersistence.lastSaved} 
                isSaving={poPersistence.isSaving} 
                isDirty={poPersistence.isDirty} 
              />
            </div>
          </DialogHeader>
          
          <DraftRecoveryBanner
            show={poPersistence.showRecoveryBanner}
            savedAt={poPersistence.savedDraftInfo?.timestamp}
            onRestore={poPersistence.handleRestoreDraft}
            onDiscard={poPersistence.handleDiscardDraft}
          />
          
          <ScrollArea className="max-h-[calc(90vh-120px)]">
            <div className="space-y-4 p-1">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Vendor *</Label>
                  <Select onValueChange={(v) => setNewPO({ ...newPO, vendor_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select vendor" /></SelectTrigger>
                    <SelectContent>
                      {vendors.map(v => <SelectItem key={v.contact_id} value={v.contact_id}>{v.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Reference Number</Label>
                  <Input value={newPO.reference_number} onChange={(e) => setNewPO({ ...newPO, reference_number: e.target.value })} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Order Date</Label>
                  <Input type="date" value={newPO.order_date} onChange={(e) => setNewPO({ ...newPO, order_date: e.target.value })} />
                </div>
                <div>
                  <Label>Expected Delivery</Label>
                  <Input type="date" value={newPO.expected_delivery_date} onChange={(e) => setNewPO({ ...newPO, expected_delivery_date: e.target.value })} />
                </div>
              </div>

              <div>
                <Label>Delivery Address</Label>
                <Textarea value={newPO.delivery_address} onChange={(e) => setNewPO({ ...newPO, delivery_address: e.target.value })} placeholder="Shipping address" />
              </div>

              {/* Line Items */}
              <div className="border rounded-lg p-4 bg-bw-panel">
                <h3 className="font-medium mb-3">Line Items</h3>
                <div className="grid grid-cols-6 gap-2 mb-3">
                  <Input className="col-span-2" placeholder="Item name *" value={newLineItem.name} onChange={(e) => setNewLineItem({ ...newLineItem, name: e.target.value })} />
                  <Input type="number" placeholder="Qty" value={newLineItem.quantity} onChange={(e) => setNewLineItem({ ...newLineItem, quantity: parseFloat(e.target.value) || 1 })} />
                  <Input type="number" placeholder="Rate *" value={newLineItem.rate || ""} onChange={(e) => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) || 0 })} />
                  <Input type="number" placeholder="Tax %" value={newLineItem.tax_rate} onChange={(e) => setNewLineItem({ ...newLineItem, tax_rate: parseFloat(e.target.value) || 0 })} />
                  <Button onClick={() => handleAddLineItem("po")} className="bg-bw-volt text-bw-black font-bold">Add</Button>
                </div>

                {newPO.line_items.length > 0 && (
                  <div className="border rounded overflow-hidden bg-bw-panel">
                    <table className="w-full text-sm">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="px-3 py-2 text-left">Item</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-right">Rate</th>
                          <th className="px-3 py-2 text-right">Tax</th>
                          <th className="px-3 py-2 text-right">Amount</th>
                          <th className="px-3 py-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {newPO.line_items.map((item, idx) => {
                          const amount = item.quantity * item.rate;
                          const tax = amount * (item.tax_rate / 100);
                          return (
                            <tr key={idx} className="border-t">
                              <td className="px-3 py-2">{item.name}</td>
                              <td className="px-3 py-2 text-right">{item.quantity}</td>
                              <td className="px-3 py-2 text-right">₹{item.rate.toLocaleString('en-IN')}</td>
                              <td className="px-3 py-2 text-right">{item.tax_rate}%</td>
                              <td className="px-3 py-2 text-right">₹{(amount + tax).toLocaleString('en-IN')}</td>
                              <td className="px-3 py-2">
                                <Button variant="ghost" size="icon" onClick={() => removeLineItem(idx, "po")}>
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                      <tfoot className="bg-bw-panel font-semibold">
                        <tr>
                          <td colSpan={4} className="px-3 py-2 text-right">Total:</td>
                          <td className="px-3 py-2 text-right">₹{calculateLineTotal(newPO.line_items).toLocaleString('en-IN')}</td>
                          <td></td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </div>

              <div>
                <Label>Notes to Vendor</Label>
                <Textarea value={newPO.vendor_notes} onChange={(e) => setNewPO({ ...newPO, vendor_notes: e.target.value })} />
              </div>
            </div>
          </ScrollArea>
          <div className="flex justify-end gap-2 mt-4">
            <Button 
              variant="outline" 
              onClick={() => {
                if (poPersistence.isDirty) {
                  poPersistence.setShowCloseConfirm(true);
                } else {
                  setShowCreatePO(false);
                  resetPOForm();
                }
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreatePO} className="bg-bw-volt text-bw-black font-bold">Create PO</Button>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Unsaved Changes Confirmation Dialogs */}
      <FormCloseConfirmDialog
        open={billPersistence.showCloseConfirm}
        onClose={() => billPersistence.setShowCloseConfirm(false)}
        onSave={handleCreateBill}
        onDiscard={() => {
          billPersistence.clearSavedData();
          resetBillForm();
          setShowCreateBill(false);
        }}
        entityName="Bill"
      />
      
      <FormCloseConfirmDialog
        open={poPersistence.showCloseConfirm}
        onClose={() => poPersistence.setShowCloseConfirm(false)}
        onSave={handleCreatePO}
        onDiscard={() => {
          poPersistence.clearSavedData();
          resetPOForm();
          setShowCreatePO(false);
        }}
        entityName="Purchase Order"
      />

      {/* Bill Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <Receipt className="h-5 w-5" />
              {billDetail?.bill_number}
              <Badge className={statusColors[billDetail?.status]}>{billDetail?.status?.replace('_', ' ')}</Badge>
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[calc(90vh-180px)]">
            {billDetail && (
              <div className="space-y-6 p-1">
                {/* Header Info */}
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-sm text-bw-white/[0.45]">Vendor</p>
                    <p className="font-medium">{billDetail.vendor_name}</p>
                    {billDetail.vendor_gstin && <p className="text-xs text-bw-white/[0.45]">GSTIN: {billDetail.vendor_gstin}</p>}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-bw-white/[0.45]">Amount</p>
                    <p className="text-2xl font-bold">₹{(billDetail.grand_total || 0).toLocaleString('en-IN')}</p>
                    {billDetail.balance_due > 0 && (
                      <p className="text-sm text-bw-orange">Balance Due: ₹{billDetail.balance_due.toLocaleString('en-IN')}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div><span className="text-bw-white/[0.45]">Bill Date:</span><br/><span className="font-medium">{billDetail.bill_date}</span></div>
                  <div><span className="text-bw-white/[0.45]">Due Date:</span><br/><span className="font-medium">{billDetail.due_date}</span></div>
                  <div><span className="text-bw-white/[0.45]">Reference:</span><br/><span className="font-medium">{billDetail.reference_number || '-'}</span></div>
                  <div><span className="text-bw-white/[0.45]">Payment Terms:</span><br/><span className="font-medium">{billDetail.payment_terms} days</span></div>
                </div>

                {/* Line Items */}
                {billDetail.line_items?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Line Items</h4>
                    <div className="border rounded overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-bw-panel">
                          <tr>
                            <th className="px-3 py-2 text-left">Item</th>
                            <th className="px-3 py-2 text-right">Qty</th>
                            <th className="px-3 py-2 text-right">Rate</th>
                            <th className="px-3 py-2 text-right">Tax</th>
                            <th className="px-3 py-2 text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {billDetail.line_items.map((item, idx) => (
                            <tr key={idx} className="border-t">
                              <td className="px-3 py-2">
                                <p className="font-medium">{item.name}</p>
                                {item.description && <p className="text-xs text-bw-white/[0.45]">{item.description}</p>}
                              </td>
                              <td className="px-3 py-2 text-right">{item.quantity} {item.unit}</td>
                              <td className="px-3 py-2 text-right">₹{(item.rate || 0).toLocaleString('en-IN')}</td>
                              <td className="px-3 py-2 text-right">{item.tax_rate}%</td>
                              <td className="px-3 py-2 text-right font-medium">₹{(item.total || 0).toLocaleString('en-IN')}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Totals */}
                <div className="flex justify-end">
                  <div className="w-64 space-y-1 text-sm">
                    <div className="flex justify-between"><span>Sub Total:</span><span>₹{(billDetail.sub_total || 0).toLocaleString('en-IN')}</span></div>
                    {billDetail.total_discount > 0 && <div className="flex justify-between text-green-600"><span>Discount:</span><span>-₹{billDetail.total_discount.toLocaleString('en-IN')}</span></div>}
                    <div className="flex justify-between"><span>Tax:</span><span>₹{(billDetail.tax_total || 0).toLocaleString('en-IN')}</span></div>
                    {billDetail.tds_amount > 0 && <div className="flex justify-between text-red-600"><span>TDS ({billDetail.tds_rate}%):</span><span>-₹{billDetail.tds_amount.toLocaleString('en-IN')}</span></div>}
                    <div className="flex justify-between font-bold text-lg border-t pt-1"><span>Total:</span><span>₹{(billDetail.grand_total || 0).toLocaleString('en-IN')}</span></div>
                    {billDetail.amount_paid > 0 && <div className="flex justify-between text-green-600"><span>Paid:</span><span>₹{billDetail.amount_paid.toLocaleString('en-IN')}</span></div>}
                    {billDetail.balance_due > 0 && <div className="flex justify-between text-bw-orange font-medium"><span>Balance Due:</span><span>₹{billDetail.balance_due.toLocaleString('en-IN')}</span></div>}
                  </div>
                </div>

                {/* Payments */}
                {billDetail.payments?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Payments</h4>
                    <div className="space-y-2">
                      {billDetail.payments.map(pmt => (
                        <div key={pmt.payment_id} className="flex justify-between items-center p-3 bg-bw-green/[0.08] rounded-lg border border-green-100">
                          <div>
                            <p className="font-medium">₹{pmt.amount.toLocaleString('en-IN')}</p>
                            <p className="text-xs text-bw-white/[0.45]">{pmt.payment_mode} - {pmt.payment_date}</p>
                          </div>
                          {pmt.reference_number && <span className="text-xs bg-bw-panel px-2 py-1 rounded">{pmt.reference_number}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* History */}
                {billDetail.history?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Activity</h4>
                    <div className="space-y-2 text-sm">
                      {billDetail.history.map(h => (
                        <div key={h.history_id} className="flex gap-3 text-bw-white/35">
                          <span className="text-bw-white/[0.45] w-32">{new Date(h.timestamp).toLocaleDateString()}</span>
                          <span>{h.details}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
          <div className="flex justify-between mt-4">
            <div className="flex gap-2">
              {billDetail?.status === "draft" && (
                <Button variant="outline" onClick={() => openBill(billDetail.bill_id)}>
                  <CheckCircle className="h-4 w-4 mr-1" /> Open Bill
                </Button>
              )}
              <Button variant="outline" onClick={() => cloneBill(billDetail?.bill_id)}>
                <Copy className="h-4 w-4 mr-1" /> Clone
              </Button>
              {billDetail?.status !== "void" && billDetail?.status !== "paid" && (
                <Button variant="outline" className="text-red-600" onClick={() => voidBill(billDetail?.bill_id)}>
                  <XCircle className="h-4 w-4 mr-1" /> Void
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              {billDetail?.balance_due > 0 && billDetail?.status !== "draft" && (
                <Button className="bg-bw-volt text-bw-black font-bold" onClick={() => {
                  setSelectedBill(billDetail);
                  setPayment({ ...payment, amount: billDetail.balance_due });
                  setShowPaymentDialog(true);
                }}>
                  <CreditCard className="h-4 w-4 mr-1" /> Record Payment
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* PO Detail Dialog */}
      <Dialog open={showPODetailDialog} onOpenChange={setShowPODetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <Truck className="h-5 w-5" />
              {poDetail?.po_number}
              <Badge className={poStatusColors[poDetail?.status]}>{poDetail?.status}</Badge>
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[calc(90vh-180px)]">
            {poDetail && (
              <div className="space-y-6 p-1">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-sm text-bw-white/[0.45]">Vendor</p>
                    <p className="font-medium">{poDetail.vendor_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-bw-white/[0.45]">Total Amount</p>
                    <p className="text-2xl font-bold">₹{(poDetail.grand_total || 0).toLocaleString('en-IN')}</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div><span className="text-bw-white/[0.45]">Order Date:</span><br/><span className="font-medium">{poDetail.order_date}</span></div>
                  <div><span className="text-bw-white/[0.45]">Expected Delivery:</span><br/><span className="font-medium">{poDetail.expected_delivery_date || '-'}</span></div>
                  <div><span className="text-bw-white/[0.45]">Reference:</span><br/><span className="font-medium">{poDetail.reference_number || '-'}</span></div>
                </div>

                {poDetail.delivery_address && (
                  <div>
                    <p className="text-sm text-bw-white/[0.45]">Delivery Address</p>
                    <p className="text-sm">{poDetail.delivery_address}</p>
                  </div>
                )}

                {/* Line Items */}
                {poDetail.line_items?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Items</h4>
                    <div className="border rounded overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-bw-panel">
                          <tr>
                            <th className="px-3 py-2 text-left">Item</th>
                            <th className="px-3 py-2 text-right">Qty</th>
                            <th className="px-3 py-2 text-right">Rate</th>
                            <th className="px-3 py-2 text-right">Tax</th>
                            <th className="px-3 py-2 text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {poDetail.line_items.map((item, idx) => (
                            <tr key={idx} className="border-t">
                              <td className="px-3 py-2">{item.name}</td>
                              <td className="px-3 py-2 text-right">{item.quantity}</td>
                              <td className="px-3 py-2 text-right">₹{(item.rate || 0).toLocaleString('en-IN')}</td>
                              <td className="px-3 py-2 text-right">{item.tax_rate}%</td>
                              <td className="px-3 py-2 text-right font-medium">₹{(item.total || 0).toLocaleString('en-IN')}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
          <div className="flex justify-between mt-4">
            <div></div>
            <div className="flex gap-2">
              {poDetail?.status === "draft" && (
                <Button variant="outline" onClick={() => issuePO(poDetail.po_id)}>
                  <Send className="h-4 w-4 mr-1" /> Issue PO
                </Button>
              )}
              {poDetail?.status === "issued" && (
                <Button variant="outline" onClick={() => receivePO(poDetail.po_id)}>
                  <CheckCircle className="h-4 w-4 mr-1" /> Mark Received
                </Button>
              )}
              {(poDetail?.status === "received" || poDetail?.status === "issued") && !poDetail?.bill_id && (
                <Button className="bg-bw-volt text-bw-black font-bold" onClick={() => convertPOToBill(poDetail.po_id)}>
                  <Receipt className="h-4 w-4 mr-1" /> Convert to Bill
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment - {selectedBill?.bill_number}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Amount *</Label>
              <Input 
                type="number" 
                value={payment.amount} 
                onChange={(e) => setPayment({ ...payment, amount: parseFloat(e.target.value) || 0 })} 
              />
              <p className="text-xs text-bw-white/[0.45] mt-1">Balance Due: ₹{(selectedBill?.balance_due || 0).toLocaleString('en-IN')}</p>
            </div>
            <div>
              <Label>Payment Mode</Label>
              <Select value={payment.payment_mode} onValueChange={(v) => setPayment({ ...payment, payment_mode: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                  <SelectItem value="neft">NEFT</SelectItem>
                  <SelectItem value="rtgs">RTGS</SelectItem>
                  <SelectItem value="cheque">Cheque</SelectItem>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="upi">UPI</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Payment Date</Label>
              <Input type="date" value={payment.payment_date} onChange={(e) => setPayment({ ...payment, payment_date: e.target.value })} />
            </div>
            <div>
              <Label>Reference Number</Label>
              <Input value={payment.reference_number} onChange={(e) => setPayment({ ...payment, reference_number: e.target.value })} placeholder="Transaction ID / UTR" />
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea value={payment.notes} onChange={(e) => setPayment({ ...payment, notes: e.target.value })} />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowPaymentDialog(false)}>Cancel</Button>
            <Button onClick={recordPayment} className="bg-bw-volt text-bw-black font-bold">Record Payment</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
