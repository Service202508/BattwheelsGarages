import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Search, Plus, FileText, Calendar, Building2, ArrowRight, 
  Truck, Package, CheckCircle, RefreshCw, ShoppingCart, Save
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { EmptyState } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const statusColors = {
  draft: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  issued: "bg-blue-100 text-[#3B9EFF]",
  partially_billed: "bg-yellow-100 text-[#EAB308]",
  billed: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  closed: "bg-purple-100 text-[#8B5CF6]",
  cancelled: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]"
};

export default function PurchaseOrders() {
  const [orders, setOrders] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [parts, setParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const initialPOData = {
    vendor_id: "",
    vendor_name: "",
    line_items: [],
    source_of_supply: "DL",
    destination_of_supply: "DL",
    notes: ""
  };

  const [newPO, setNewPO] = useState(initialPOData);

  const [newLineItem, setNewLineItem] = useState({
    item_id: "", item_name: "", item_type: "goods",
    quantity: 1, rate: 0, tax_rate: 18
  });

  // Auto-save for Purchase Order form
  const poPersistence = useFormPersistence(
    'purchase_order_new',
    newPO,
    initialPOData,
    {
      enabled: showCreateDialog,
      isDialogOpen: showCreateDialog,
      setFormData: setNewPO,
      debounceMs: 2000,
      entityName: 'Purchase Order'
    }
  );

  useEffect(() => { fetchData(); }, [statusFilter]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [poRes, vRes, pRes] = await Promise.all([
        fetch(`${API}/erp/purchase-orders?status=${statusFilter}&limit=100`, { headers }),
        fetch(`${API}/books/vendors?limit=200`, { headers }),
        fetch(`${API}/books/parts?limit=200`, { headers })
      ]);
      const [poData, vData, pData] = await Promise.all([poRes.json(), vRes.json(), pRes.json()]);
      setOrders(poData.purchase_orders || []);
      setVendors(vData.vendors || []);
      setParts(pData.items || []);
    } catch (error) {
      console.error("Failed to fetch:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectItem = (itemId) => {
    const item = parts.find(i => i.item_id === itemId);
    if (item) {
      setNewLineItem({
        ...newLineItem, item_id: item.item_id, item_name: item.name,
        rate: item.rate || 0, tax_rate: item.tax_rate || 18
      });
    }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.item_name) return toast.error("Select an item");
    setNewPO({ ...newPO, line_items: [...newPO.line_items, { ...newLineItem }] });
    setNewLineItem({ item_id: "", item_name: "", item_type: "goods", quantity: 1, rate: 0, tax_rate: 18 });
  };

  const calculateTotal = () => newPO.line_items.reduce((sum, i) => {
    const sub = i.quantity * i.rate;
    const tax = sub * (i.tax_rate / 100);
    return sum + sub + tax;
  }, 0);

  const handleCreatePO = async () => {
    if (!newPO.vendor_id) return toast.error("Select a vendor");
    if (!newPO.line_items.length) return toast.error("Add at least one item");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/erp/purchase-orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newPO)
      });
      if (res.ok) {
        toast.success("Purchase Order created");
        poPersistence.onSuccessfulSave(); // Clear auto-saved draft
        setShowCreateDialog(false);
        setNewPO(initialPOData);
        fetchData();
      }
    } catch { toast.error("Error creating PO"); }
  };

  const handleConvertToBill = async (poId) => {
    const billNumber = `BILL-${Date.now()}`;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/erp/purchase-orders/${poId}/convert-to-bill?bill_number=${billNumber}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Converted to Bill");
        fetchData();
      }
    } catch { toast.error("Conversion failed"); }
  };

  // Calculate summary stats
  const statusCounts = orders.reduce((acc, po) => {
    acc[po.status] = (acc[po.status] || 0) + 1;
    return acc;
  }, {});
  const totalValue = orders.reduce((sum, po) => sum + (po.total || 0), 0);

  return (
    <div className="space-y-6" data-testid="purchase-orders-page">
      <PageHeader
        title="Purchase Orders"
        description={`${orders.length} purchase orders`}
        icon={ShoppingCart}
        actions={
          <div className="flex gap-2">
            <Button onClick={fetchData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
            <Dialog open={showCreateDialog} onOpenChange={(open) => {
              if (!open && poPersistence.isDirty) {
                poPersistence.setShowCloseConfirm(true);
              } else {
                setShowCreateDialog(open);
                if (!open) poPersistence.clearSavedData();
              }
            }}>
              <DialogTrigger asChild>
                <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                  <Plus className="h-4 w-4 mr-2" /> New Purchase Order
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <div className="flex justify-between items-start">
                    <DialogTitle>Create Purchase Order</DialogTitle>
                    <AutoSaveIndicator 
                      lastSaved={poPersistence.lastSaved} 
                      isSaving={poPersistence.isSaving} 
                      isDirty={poPersistence.isDirty} 
                    />
                  </div>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  {/* Draft Recovery Banner */}
                  <DraftRecoveryBanner
                    show={poPersistence.showRecoveryBanner}
                    savedAt={poPersistence.savedDraftInfo?.timestamp}
                    onRestore={poPersistence.handleRestoreDraft}
                    onDiscard={poPersistence.handleDiscardDraft}
                  />
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Vendor *</Label>
                      <Select onValueChange={(v) => {
                        const vnd = vendors.find(x => x.vendor_id === v);
                        if (vnd) setNewPO({ ...newPO, vendor_id: vnd.vendor_id, vendor_name: vnd.display_name });
                      }}>
                        <SelectTrigger><SelectValue placeholder="Select vendor" /></SelectTrigger>
                        <SelectContent>
                          {vendors.map(v => <SelectItem key={v.vendor_id} value={v.vendor_id}>{v.display_name}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Destination</Label>
                      <Select value={newPO.destination_of_supply} onValueChange={(v) => setNewPO({ ...newPO, destination_of_supply: v })}>
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
                    <h3 className="font-medium mb-3">Add Parts/Items</h3>
                    <Select onValueChange={handleSelectItem}>
                      <SelectTrigger><SelectValue placeholder="Select part" /></SelectTrigger>
                      <SelectContent>
                        {parts.slice(0, 50).map(p => <SelectItem key={p.item_id} value={p.item_id}>{p.name} - ₹{p.rate}</SelectItem>)}
                      </SelectContent>
                    </Select>
                    {newLineItem.item_name && (
                      <div className="mt-3 grid grid-cols-4 gap-3">
                        <Input value={newLineItem.item_name} readOnly className="bg-[#111820]" />
                        <Input type="number" value={newLineItem.quantity} onChange={(e) => setNewLineItem({ ...newLineItem, quantity: parseFloat(e.target.value) })} placeholder="Qty" />
                        <Input type="number" value={newLineItem.rate} onChange={(e) => setNewLineItem({ ...newLineItem, rate: parseFloat(e.target.value) })} placeholder="Rate" />
                        <Button onClick={handleAddLineItem} className="bg-[#C8FF00] text-[#080C0F] font-bold">Add</Button>
                      </div>
                    )}
                  </div>

                  {newPO.line_items.length > 0 && (
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
                          {newPO.line_items.map((item, idx) => (
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
                  <Button variant="outline" onClick={() => {
                    if (poPersistence.isDirty) {
                      poPersistence.setShowCloseConfirm(true);
                    } else {
                      setShowCreateDialog(false);
                    }
                  }}>Cancel</Button>
                  <Button onClick={handleCreatePO} className="bg-[#C8FF00] text-[#080C0F] font-bold">
                    <Save className="h-4 w-4 mr-2" /> Create PO
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      {/* Purchase Order Close Confirmation */}
      <FormCloseConfirmDialog
        open={poPersistence.showCloseConfirm}
        onClose={() => poPersistence.setShowCloseConfirm(false)}
        onSave={async () => {
          await handleCreatePO();
        }}
        onDiscard={() => {
          poPersistence.clearSavedData();
          setShowCreateDialog(false);
          setNewPO(initialPOData);
        }}
        isSaving={false}
        entityName="Purchase Order"
      />

      {/* Summary Cards */}
      <StatCardGrid columns={5}>
        <StatCard
          title="Total POs"
          value={orders.length}
          icon={ShoppingCart}
          variant="info"
        />
        <StatCard
          title="Draft"
          value={statusCounts.draft || 0}
          icon={FileText}
          variant="default"
        />
        <StatCard
          title="Issued"
          value={statusCounts.issued || 0}
          icon={Truck}
          variant="info"
        />
        <StatCard
          title="Billed"
          value={statusCounts.billed || 0}
          icon={CheckCircle}
          variant="success"
        />
        <StatCard
          title="Total Value"
          value={formatCurrencyCompact(totalValue)}
          icon={Package}
          variant="success"
        />
      </StatCardGrid>

      <div className="flex gap-2 flex-wrap">
        {["", "draft", "issued", "partially_billed", "billed"].map(s => (
          <Button key={s} size="sm" variant={statusFilter === s ? "default" : "outline"}
            onClick={() => setStatusFilter(s)}
            className={statusFilter === s ? "bg-[#C8FF00] text-[#080C0F] font-bold" : ""}>
            {s ? s.replace('_', ' ') : "All"}
          </Button>
        ))}
      </div>

      {loading ? <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</div> :
        orders.length === 0 ? (
          <Card>
            <EmptyState
              icon={ShoppingCart}
              title="No purchase orders found"
              description="Create a purchase order to start ordering from vendors."
              actionLabel="New Purchase Order"
              onAction={() => setShowCreateDialog(true)}
              actionIcon={Plus}
            />
          </Card>
        ) :
        <div className="space-y-3">
          {orders.map(po => (
            <Card key={po.po_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold">{po.po_number}</h3>
                      <Badge className={statusColors[po.status]}>{po.status?.replace('_', ' ')}</Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                      <span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{po.vendor_name}</span>
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{po.order_date}</span>
                      <span className="flex items-center gap-1"><Package className="h-3.5 w-3.5" />{po.line_items?.length || 0} items</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-bold text-lg">₹{po.total?.toLocaleString('en-IN')}</p>
                    </div>
                    {po.status === "draft" && (
                      <Button size="sm" className="bg-[#C8FF00] text-[#080C0F] font-bold" onClick={() => handleConvertToBill(po.po_id)}>
                        <ArrowRight className="h-4 w-4 mr-1" /> Create Bill
                      </Button>
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
