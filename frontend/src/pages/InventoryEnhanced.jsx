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
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { 
  Package, Plus, Search, Eye, Edit, Trash2, RefreshCw, AlertTriangle, 
  TrendingUp, TrendingDown, ArrowRightLeft, Clock, CheckCircle, XCircle, 
  Warehouse, BarChart3, History, Upload, Download, Filter, Box, IndianRupee, Layers, Barcode, ArrowUpDown, Truck, RotateCcw
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";

const statusColors = {
  available: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  sold: "bg-blue-100 text-[#3B9EFF]",
  returned: "bg-yellow-100 text-[#EAB308]",
  damaged: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  packed: "bg-purple-100 text-[#8B5CF6]",
  shipped: "bg-indigo-100 text-indigo-700",
  delivered: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  pending: "bg-yellow-100 text-[#EAB308]",
  processed: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]"
};

export default function InventoryEnhanced() {
  const [activeTab, setActiveTab] = useState("overview");
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [warehouses, setWarehouses] = useState([]);
  const [variants, setVariants] = useState([]);
  const [bundles, setBundles] = useState([]);
  const [serialBatches, setSerialBatches] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [returns, setReturns] = useState([]);
  const [adjustments, setAdjustments] = useState([]);
  const [stockReport, setStockReport] = useState(null);
  const [lowStockItems, setLowStockItems] = useState([]);
  
  // Dialog states
  const [showWarehouseDialog, setShowWarehouseDialog] = useState(false);
  const [showVariantDialog, setShowVariantDialog] = useState(false);
  const [showBundleDialog, setShowBundleDialog] = useState(false);
  const [showSerialDialog, setShowSerialDialog] = useState(false);
  const [showAdjustmentDialog, setShowAdjustmentDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [detailType, setDetailType] = useState("");
  const [detailData, setDetailData] = useState(null);
  
  // Items list for dropdowns
  const [items, setItems] = useState([]);

  // Form states
  const [newWarehouse, setNewWarehouse] = useState({ name: "", code: "", address: "", city: "", state: "", pincode: "", is_primary: false });
  const [newVariant, setNewVariant] = useState({ item_id: "", variant_name: "", sku: "", additional_rate: 0, attributes: {}, initial_stock: 0, warehouse_id: "" });
  const [newBundle, setNewBundle] = useState({ name: "", sku: "", description: "", rate: 0, components: [], auto_calculate_rate: true });
  const [newSerial, setNewSerial] = useState({ item_id: "", tracking_type: "serial", number: "", warehouse_id: "", expiry_date: "", quantity: 1, notes: "" });
  const [newAdjustment, setNewAdjustment] = useState({ item_id: "", warehouse_id: "", adjustment_type: "add", quantity: 0, reason: "", reference_number: "", notes: "" });
  const [bundleComponent, setBundleComponent] = useState({ item_id: "", quantity: 1 });

  // New feature states
  const [reorderSuggestions, setReorderSuggestions] = useState(null);
  const [loadingReorder, setLoadingReorder] = useState(false);
  const [stockTransfers, setStockTransfers] = useState([]);
  const [showTransferDialog, setShowTransferDialog] = useState(false);
  const [newTransfer, setNewTransfer] = useState({ from_warehouse_id: "", to_warehouse_id: "", items: [], notes: "" });
  const [transferLine, setTransferLine] = useState({ item_id: "", quantity: 1 });
  const [stocktakes, setStocktakes] = useState([]);
  const [activeStocktake, setActiveStocktake] = useState(null);
  const [showStocktakeDialog, setShowStocktakeDialog] = useState(false);
  const [newStocktake, setNewStocktake] = useState({ warehouse_id: "", name: "", notes: "" });
  const [loadingStocktake, setLoadingStocktake] = useState(false);
  const [serialSearch, setSerialSearch] = useState("");

  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

  useEffect(() => { fetchAllData(); }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [summaryRes, warehouseRes, variantsRes, bundlesRes, serialRes, shipmentsRes, returnsRes, itemsRes, lowStockRes] = await Promise.all([
        fetch(`${API}/inventory-enhanced/summary`, { headers }),
        fetch(`${API}/inventory-enhanced/warehouses`, { headers }),
        fetch(`${API}/inventory-enhanced/variants`, { headers }),
        fetch(`${API}/inventory-enhanced/bundles`, { headers }),
        fetch(`${API}/inventory-enhanced/serial-batches?status=all`, { headers }),
        fetch(`${API}/inventory-enhanced/shipments`, { headers }),
        fetch(`${API}/inventory-enhanced/returns`, { headers }),
        fetch(`${API}/items-enhanced/?per_page=500`, { headers }),
        fetch(`${API}/inventory-enhanced/reports/low-stock`, { headers })
      ]);

      const [summaryData, warehouseData, variantsData, bundlesData, serialData, shipmentsData, returnsData, itemsData, lowStockData] = await Promise.all([
        summaryRes.json(), warehouseRes.json(), variantsRes.json(), bundlesRes.json(), 
        serialRes.json(), shipmentsRes.json(), returnsRes.json(), itemsRes.json(), lowStockRes.json()
      ]);

      setSummary(summaryData.summary || {});
      setWarehouses(warehouseData.warehouses || []);
      setVariants(variantsData.variants || []);
      setBundles(bundlesData.bundles || []);
      setSerialBatches(serialData.serial_batches || []);
      setShipments(shipmentsData.shipments || []);
      setReturns(returnsData.returns || []);
      setItems(itemsData.items || []);
      setLowStockItems(lowStockData.report?.low_stock_items || []);

      // Fetch transfers and stocktakes
      const [transfersRes, stocktakesRes] = await Promise.all([
        fetch(`${API}/inventory-enhanced/stock-transfers?limit=20`, { headers }),
        fetch(`${API}/inventory-enhanced/stocktakes`, { headers }),
      ]);
      if (transfersRes.ok) { const d = await transfersRes.json(); setStockTransfers(d.transfers || []); }
      if (stocktakesRes.ok) { const d = await stocktakesRes.json(); setStocktakes(d.stocktakes || []); }
    } catch (error) {
      console.error("Failed to fetch:", error);
      toast.error("Failed to load inventory data");
    } finally {
      setLoading(false);
    }
  };

  // ========== WAREHOUSE CRUD ==========
  const handleCreateWarehouse = async () => {
    if (!newWarehouse.name) return toast.error("Enter warehouse name");
    try {
      const res = await fetch(`${API}/inventory-enhanced/warehouses`, { method: "POST", headers, body: JSON.stringify(newWarehouse) });
      const data = await res.json();
      if (res.ok) {
        toast.success("Warehouse created");
        setShowWarehouseDialog(false);
        setNewWarehouse({ name: "", code: "", address: "", city: "", state: "", pincode: "", is_primary: false });
        fetchAllData();
      } else {
        toast.error(data.detail || "Failed to create warehouse");
      }
    } catch { toast.error("Error creating warehouse"); }
  };

  // ========== STOCK TRANSFER ==========
  const handleCreateTransfer = async () => {
    if (!newTransfer.from_warehouse_id || !newTransfer.to_warehouse_id) return toast.error("Select both warehouses");
    if (!newTransfer.items.length) return toast.error("Add at least one item");
    try {
      const res = await fetch(`${API}/inventory-enhanced/stock-transfers`, {
        method: "POST", headers, body: JSON.stringify(newTransfer)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Stock transferred successfully");
        if (data.warnings?.length) toast.warning(data.warnings.join("; "));
        setShowTransferDialog(false);
        setNewTransfer({ from_warehouse_id: "", to_warehouse_id: "", items: [], notes: "" });
        setTransferLine({ item_id: "", quantity: 1 });
        fetchAllData();
      } else {
        toast.error(data.detail || "Transfer failed");
      }
    } catch { toast.error("Error creating transfer"); }
  };

  // ========== REORDER SUGGESTIONS ==========
  const fetchReorderSuggestions = async () => {
    setLoadingReorder(true);
    try {
      const res = await fetch(`${API}/inventory-enhanced/reorder-suggestions`, { headers });
      if (res.ok) { const data = await res.json(); setReorderSuggestions(data); }
      else toast.error("Failed to load reorder suggestions");
    } catch { toast.error("Error loading suggestions"); }
    finally { setLoadingReorder(false); }
  };

  const handleCreatePoFromGroup = async (vendorGroup) => {
    try {
      const body = {
        vendor_id: vendorGroup.vendor_id,
        items: vendorGroup.items.map(i => ({
          item_id: i.item_id, quantity: i.suggested_order_qty, unit_cost: i.unit_cost
        })),
        notes: "Auto-generated from reorder suggestions"
      };
      const res = await fetch(`${API}/inventory-enhanced/reorder-suggestions/create-po`, {
        method: "POST", headers, body: JSON.stringify(body)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`PO ${data.purchase_order?.po_number} created`);
      } else {
        toast.error(data.detail || "Failed to create PO");
      }
    } catch { toast.error("Error creating PO"); }
  };

  // ========== STOCKTAKE ==========
  const handleCreateStocktake = async () => {
    if (!newStocktake.warehouse_id) return toast.error("Select a warehouse");
    setLoadingStocktake(true);
    try {
      const res = await fetch(`${API}/inventory-enhanced/stocktakes`, {
        method: "POST", headers, body: JSON.stringify(newStocktake)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Stocktake session started");
        setShowStocktakeDialog(false);
        setNewStocktake({ warehouse_id: "", name: "", notes: "" });
        setActiveStocktake(data.stocktake);
        setStocktakes(prev => [data.stocktake, ...prev]);
      } else {
        toast.error(data.detail || "Failed to create stocktake");
      }
    } catch { toast.error("Error creating stocktake"); }
    finally { setLoadingStocktake(false); }
  };

  const handleLoadStocktake = async (id) => {
    try {
      const res = await fetch(`${API}/inventory-enhanced/stocktakes/${id}`, { headers });
      if (res.ok) { const data = await res.json(); setActiveStocktake(data.stocktake); }
    } catch { toast.error("Failed to load stocktake"); }
  };

  const handleSubmitCount = async (stocktakeId, itemId, countedQty) => {
    try {
      const res = await fetch(`${API}/inventory-enhanced/stocktakes/${stocktakeId}/lines/${itemId}`, {
        method: "PUT", headers, body: JSON.stringify({ counted_quantity: countedQty, notes: "" })
      });
      const data = await res.json();
      if (res.ok) {
        setActiveStocktake(prev => ({
          ...prev,
          lines: prev.lines.map(ln =>
            ln.item_id === itemId
              ? { ...ln, counted_quantity: countedQty, variance: data.variance, counted: true }
              : ln
          ),
          counted_lines: (prev.counted_lines || 0) + (prev.lines.find(ln => ln.item_id === itemId)?.counted ? 0 : 1)
        }));
      } else {
        toast.error(data.detail || "Failed to update count");
      }
    } catch { toast.error("Error updating count"); }
  };

  const handleFinalizeStocktake = async (stocktakeId) => {
    if (!window.confirm("Finalize this stocktake? All variances will be applied as stock adjustments.")) return;
    try {
      const res = await fetch(`${API}/inventory-enhanced/stocktakes/${stocktakeId}/finalize`, {
        method: "POST", headers
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        setActiveStocktake(prev => ({ ...prev, status: "finalized", finalized_at: new Date().toISOString() }));
        fetchAllData();
      } else {
        toast.error(data.detail || "Failed to finalize");
      }
    } catch { toast.error("Error finalizing stocktake"); }
  };

  // ========== VARIANT CRUD ==========
  const handleCreateVariant = async () => {
    if (!newVariant.item_id || !newVariant.variant_name) return toast.error("Select item and enter variant name");
    try {
      const res = await fetch(`${API}/inventory-enhanced/variants`, { method: "POST", headers, body: JSON.stringify(newVariant) });
      const data = await res.json();
      if (res.ok) {
        toast.success("Variant created");
        setShowVariantDialog(false);
        setNewVariant({ item_id: "", variant_name: "", sku: "", additional_rate: 0, attributes: {}, initial_stock: 0, warehouse_id: "" });
        fetchAllData();
      } else {
        toast.error(data.detail || "Failed to create variant");
      }
    } catch { toast.error("Error creating variant"); }
  };

  // ========== BUNDLE CRUD ==========
  const handleAddBundleComponent = () => {
    if (!bundleComponent.item_id) return toast.error("Select an item");
    const item = items.find(i => i.item_id === bundleComponent.item_id);
    setNewBundle({
      ...newBundle,
      components: [...newBundle.components, { ...bundleComponent, item_name: item?.name }]
    });
    setBundleComponent({ item_id: "", quantity: 1 });
  };

  const handleCreateBundle = async () => {
    if (!newBundle.name || newBundle.components.length === 0) return toast.error("Enter name and add components");
    try {
      const res = await fetch(`${API}/inventory-enhanced/bundles`, { method: "POST", headers, body: JSON.stringify(newBundle) });
      const data = await res.json();
      if (res.ok) {
        toast.success("Bundle created");
        setShowBundleDialog(false);
        setNewBundle({ name: "", sku: "", description: "", rate: 0, components: [], auto_calculate_rate: true });
        fetchAllData();
      } else {
        toast.error(data.detail || "Failed to create bundle");
      }
    } catch { toast.error("Error creating bundle"); }
  };

  const handleAssembleBundle = async (bundleId) => {
    const warehouse = warehouses.find(w => w.is_primary) || warehouses[0];
    if (!warehouse) return toast.error("No warehouse available");
    
    try {
      const res = await fetch(`${API}/inventory-enhanced/bundles/${bundleId}/assemble?quantity=1&warehouse_id=${warehouse.warehouse_id}`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        fetchAllData();
      } else {
        toast.error(data.detail || "Failed to assemble bundle");
      }
    } catch { toast.error("Error assembling bundle"); }
  };

  // ========== SERIAL/BATCH CRUD ==========
  const handleCreateSerial = async () => {
    if (!newSerial.item_id || !newSerial.number) return toast.error("Select item and enter number");
    try {
      const res = await fetch(`${API}/inventory-enhanced/serial-batches`, { method: "POST", headers, body: JSON.stringify(newSerial) });
      const data = await res.json();
      if (res.ok) {
        toast.success(`${newSerial.tracking_type} created`);
        setShowSerialDialog(false);
        setNewSerial({ item_id: "", tracking_type: "serial", number: "", warehouse_id: "", expiry_date: "", quantity: 1, notes: "" });
        fetchAllData();
      } else {
        toast.error(data.detail || "Failed to create");
      }
    } catch { toast.error("Error creating serial/batch"); }
  };

  // ========== ADJUSTMENT CRUD ==========
  const handleCreateAdjustment = async () => {
    if (!newAdjustment.item_id || !newAdjustment.warehouse_id || !newAdjustment.reason) {
      return toast.error("Select item, warehouse and enter reason");
    }
    try {
      const res = await fetch(`${API}/inventory-enhanced/adjustments`, { method: "POST", headers, body: JSON.stringify(newAdjustment) });
      const data = await res.json();
      if (res.ok) {
        toast.success("Adjustment recorded");
        setShowAdjustmentDialog(false);
        setNewAdjustment({ item_id: "", warehouse_id: "", adjustment_type: "add", quantity: 0, reason: "", reference_number: "", notes: "" });
        fetchAllData();
      } else {
        toast.error(data.detail || "Failed to create adjustment");
      }
    } catch { toast.error("Error creating adjustment"); }
  };

  // ========== SHIPMENT ACTIONS ==========
  const handleShipmentAction = async (shipmentId, action) => {
    try {
      const res = await fetch(`${API}/inventory-enhanced/shipments/${shipmentId}/${action}`, { method: "POST", headers });
      if (res.ok) {
        toast.success(`Shipment ${action === 'ship' ? 'shipped' : 'delivered'}`);
        fetchAllData();
      }
    } catch { toast.error("Action failed"); }
  };

  // ========== RETURN ACTIONS ==========
  const handleProcessReturn = async (returnId) => {
    try {
      const res = await fetch(`${API}/inventory-enhanced/returns/${returnId}/process`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Return processed");
        fetchAllData();
      }
    } catch { toast.error("Failed to process return"); }
  };

  // ========== VIEW DETAIL ==========
  const viewDetail = async (type, id) => {
    try {
      let endpoint = "";
      if (type === "warehouse") endpoint = `warehouses/${id}`;
      else if (type === "variant") endpoint = `variants/${id}`;
      else if (type === "bundle") endpoint = `bundles/${id}`;
      else if (type === "serial") endpoint = `serial-batches/${id}`;
      else if (type === "shipment") endpoint = `shipments/${id}`;
      else if (type === "return") endpoint = `returns/${id}`;
      
      const res = await fetch(`${API}/inventory-enhanced/${endpoint}`, { headers });
      const data = await res.json();
      if (res.ok) {
        setDetailType(type);
        setDetailData(data[type] || data.warehouse || data.variant || data.bundle || data.serial_batch || data.shipment || data.return);
        setShowDetailDialog(true);
      }
    } catch { toast.error("Failed to load details"); }
  };

  // Inline count input component for stocktake
  const CountInput = ({ defaultValue, onSubmit }) => {
    const [val, setVal] = useState(defaultValue !== null && defaultValue !== undefined ? String(defaultValue) : "");
    return (
      <div className="flex items-center gap-1">
        <Input
          type="number"
          value={val}
          onChange={e => setVal(e.target.value)}
          className="w-20 h-7 text-sm text-center font-mono"
          onKeyDown={e => { if (e.key === "Enter") onSubmit(parseFloat(val) || 0); }}
        />
        <Button size="sm" variant="outline" className="h-7 px-2 text-xs" onClick={() => onSubmit(parseFloat(val) || 0)}>
          Save
        </Button>
      </div>
    );
  };

  return (
    <div className="space-y-6" data-testid="inventory-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Inventory Management"
        description="Variants, Bundles, Shipments & Returns"
        icon={Package}
        actions={
          <div className="flex gap-2 flex-wrap">
            <Button variant="outline" size="sm" onClick={() => setShowWarehouseDialog(true)}>
              <Warehouse className="h-4 w-4 mr-1" /> Warehouse
            </Button>
            <Button variant="outline" size="sm" onClick={() => setShowVariantDialog(true)}>
              <Layers className="h-4 w-4 mr-1" /> Variant
            </Button>
            <Button variant="outline" size="sm" onClick={() => setShowBundleDialog(true)}>
              <Package className="h-4 w-4 mr-1" /> Bundle
            </Button>
            <Button variant="outline" size="sm" onClick={() => setShowSerialDialog(true)}>
              <Barcode className="h-4 w-4 mr-1" /> Serial/Batch
            </Button>
            <Button className="bg-[#C8FF00] text-[#080C0F] font-bold" size="sm" onClick={() => setShowAdjustmentDialog(true)}>
              <ArrowUpDown className="h-4 w-4 mr-1" /> Adjust Stock
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <StatCardGrid columns={6}>
        <StatCard
          title="Items"
          value={summary.total_items || 0}
          icon={Box}
          variant="info"
        />
        <StatCard
          title="Variants"
          value={summary.total_variants || 0}
          icon={Layers}
          variant="default"
        />
        <StatCard
          title="Bundles"
          value={summary.total_bundles || 0}
          icon={Package}
          variant="info"
        />
        <StatCard
          title="Warehouses"
          value={summary.total_warehouses || 0}
          icon={Warehouse}
          variant="default"
        />
        <StatCard
          title="Stock Value"
          value={formatCurrencyCompact(summary.total_stock_value || 0)}
          icon={IndianRupee}
          variant="success"
        />
        <StatCard
          title="Low Stock"
          value={summary.low_stock_count || 0}
          icon={AlertTriangle}
          variant={summary.low_stock_count > 0 ? "danger" : "default"}
        />
      </StatCardGrid>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex-wrap">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="warehouses">Warehouses</TabsTrigger>
          <TabsTrigger value="serial-batch">Serial/Batch</TabsTrigger>
          <TabsTrigger value="reorder-alerts" data-testid="reorder-alerts-tab">Reorder Alerts</TabsTrigger>
          <TabsTrigger value="stocktake" data-testid="stocktake-tab">Stocktake</TabsTrigger>
          <TabsTrigger value="variants">Variants</TabsTrigger>
          <TabsTrigger value="bundles">Bundles</TabsTrigger>
          <TabsTrigger value="shipments">Shipments</TabsTrigger>
          <TabsTrigger value="returns">Returns</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Low Stock Alert */}
          {lowStockItems.length > 0 && (
            <Card className="border-l-4 border-l-[#FF3B2F]">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2 text-[#FF3B2F]">
                  <AlertTriangle className="h-5 w-5" /> Low Stock Alert
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {lowStockItems.slice(0, 5).map(item => (
                    <div key={item.item_id} className="flex justify-between items-center p-2 bg-[rgba(255,59,47,0.08)] rounded">
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">{item.sku}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[#FF3B2F] font-bold">{item.total_stock} in stock</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">Reorder at: {item.reorder_level}</p>
                      </div>
                    </div>
                  ))}
                  {lowStockItems.length > 5 && (
                    <p className="text-sm text-[rgba(244,246,240,0.45)] text-center">+{lowStockItems.length - 5} more items</p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Activity */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Pending Shipments */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Truck className="h-5 w-5" /> Pending Shipments
                </CardTitle>
              </CardHeader>
              <CardContent>
                {shipments.filter(s => s.status !== 'delivered').length === 0 ? (
                  <p className="text-[rgba(244,246,240,0.45)] text-center py-4">No pending shipments</p>
                ) : (
                  <div className="space-y-2">
                    {shipments.filter(s => s.status !== 'delivered').slice(0, 5).map(s => (
                      <div key={s.shipment_id} className="flex justify-between items-center p-2 bg-[#111820] rounded cursor-pointer hover:bg-[rgba(255,255,255,0.05)]" onClick={() => viewDetail('shipment', s.shipment_id)}>
                        <div>
                          <p className="font-medium">{s.package_number}</p>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">{s.customer_name}</p>
                        </div>
                        <Badge className={statusColors[s.status]}>{s.status}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Pending Returns */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <RotateCcw className="h-5 w-5" /> Pending Returns
                </CardTitle>
              </CardHeader>
              <CardContent>
                {returns.filter(r => r.status === 'pending').length === 0 ? (
                  <p className="text-[rgba(244,246,240,0.45)] text-center py-4">No pending returns</p>
                ) : (
                  <div className="space-y-2">
                    {returns.filter(r => r.status === 'pending').slice(0, 5).map(r => (
                      <div key={r.return_id} className="flex justify-between items-center p-2 bg-[rgba(234,179,8,0.08)] rounded cursor-pointer hover:bg-yellow-100" onClick={() => viewDetail('return', r.return_id)}>
                        <div>
                          <p className="font-medium">{r.customer_name}</p>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">{r.reason}</p>
                        </div>
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleProcessReturn(r.return_id); }}>
                          Process
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Warehouses Tab */}
        <TabsContent value="warehouses">
          <div className="space-y-4">
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowTransferDialog(true)} data-testid="transfer-stock-btn">
                <ArrowRightLeft className="h-4 w-4 mr-2" /> Transfer Stock
              </Button>
            </div>
            {loading ? (
              <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</div>
            ) : warehouses.length === 0 ? (
              <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No warehouses. Create one to start tracking inventory by location.</CardContent></Card>
            ) : (
              <>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {warehouses.map(wh => (
                    <Card key={wh.warehouse_id} className={`cursor-pointer border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors ${wh.is_primary ? 'border-[#C8FF00] border-2' : ''}`} onClick={() => viewDetail('warehouse', wh.warehouse_id)}>
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-semibold">{wh.name}</h3>
                            {wh.code && <p className="text-xs text-[rgba(244,246,240,0.45)]">{wh.code}</p>}
                          </div>
                          {wh.is_primary && <Badge className="bg-[#C8FF00] text-[#080C0F] font-bold">Primary</Badge>}
                        </div>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">{wh.city}{wh.state ? `, ${wh.state}` : ''}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                {/* Recent Transfers */}
                {stockTransfers.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2"><ArrowRightLeft className="h-4 w-4" /> Recent Stock Transfers</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {stockTransfers.slice(0, 5).map(t => (
                        <div key={t.transfer_id} className="flex justify-between items-center p-2 bg-[rgba(255,255,255,0.03)] rounded border border-[rgba(255,255,255,0.06)]">
                          <div>
                            <p className="text-sm font-medium">{t.from_warehouse_name} → {t.to_warehouse_name}</p>
                            <p className="text-xs text-[rgba(244,246,240,0.45)]">{t.items?.length} item(s) · {t.created_at?.split("T")[0]}</p>
                          </div>
                          <Badge className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]">{t.status}</Badge>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </div>
        </TabsContent>

        {/* Variants Tab */}
        <TabsContent value="variants">
          {variants.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No variants. Create variants for items with multiple options (size, color, etc.)</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {variants.map(v => (
                <Card key={v.variant_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors cursor-pointer" onClick={() => viewDetail('variant', v.variant_id)}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="font-semibold">{v.variant_name}</h3>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">Base: {v.item_name} | SKU: {v.sku}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">₹{(v.effective_rate || 0).toLocaleString('en-IN')}</p>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">Stock: {v.available_stock || 0}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Bundles Tab */}
        <TabsContent value="bundles">
          {bundles.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No bundles. Create bundles/kits to sell composite items.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {bundles.map(b => (
                <Card key={b.bundle_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors cursor-pointer" onClick={() => viewDetail('bundle', b.bundle_id)}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="font-semibold">{b.name}</h3>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">SKU: {b.sku} | {b.component_count} components</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <p className="font-bold">₹{(b.rate || 0).toLocaleString('en-IN')}</p>
                        </div>
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleAssembleBundle(b.bundle_id); }}>
                          Assemble
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Serial/Batch Tab */}
        <TabsContent value="serial-batch">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                <Input
                  placeholder="Search by serial/batch number..."
                  value={serialSearch}
                  onChange={e => setSerialSearch(e.target.value)}
                  className="pl-9"
                  data-testid="serial-search-input"
                />
              </div>
              <Button variant="outline" size="sm" onClick={() => setSerialSearch("")}>Clear</Button>
            </div>
          {(() => {
            const filtered = serialBatches.filter(sb =>
              !serialSearch || sb.number?.toLowerCase().includes(serialSearch.toLowerCase())
            );
            return filtered.length === 0 ? (
              <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
                {serialSearch ? `No results for "${serialSearch}"` : "No serial numbers or batches. Track individual units or lot numbers for traceability."}
              </CardContent></Card>
            ) : (
              <div className="space-y-2">
                {filtered.map(sb => (
                  <Card key={sb.serial_batch_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors cursor-pointer" onClick={() => viewDetail('serial', sb.serial_batch_id)}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                          <Barcode className="h-8 w-8 text-[rgba(244,246,240,0.45)]" />
                          <div>
                            <h3 className="font-semibold font-mono">{sb.number}</h3>
                            <p className="text-xs text-[rgba(244,246,240,0.45)]">{sb.tracking_type === 'serial' ? 'Serial Number' : `Batch (Qty: ${sb.quantity})`}</p>
                            {sb.warehouse_id && <p className="text-xs text-[rgba(244,246,240,0.35)]">WH: {warehouses.find(w => w.warehouse_id === sb.warehouse_id)?.name || sb.warehouse_id}</p>}
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge className={statusColors[sb.status] || "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.45)]"}>{sb.status}</Badge>
                          {sb.expiry_date && <p className="text-xs text-[rgba(244,246,240,0.35)] mt-1">Exp: {sb.expiry_date}</p>}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            );
          })()}
          </div>
        </TabsContent>

        {/* Shipments Tab */}
        <TabsContent value="shipments">
          {shipments.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No shipments yet. Shipments are created from Sales Orders.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {shipments.map(s => (
                <Card key={s.shipment_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors cursor-pointer" onClick={() => viewDetail('shipment', s.shipment_id)}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{s.package_number}</h3>
                          <Badge className={statusColors[s.status]}>{s.status}</Badge>
                        </div>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">{s.customer_name} | {s.carrier || 'No carrier'}</p>
                        {s.tracking_number && <p className="text-xs text-[rgba(244,246,240,0.45)]">Tracking: {s.tracking_number}</p>}
                      </div>
                      <div className="flex gap-2">
                        {s.status === 'packed' && (
                          <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleShipmentAction(s.shipment_id, 'ship'); }}>
                            <Truck className="h-4 w-4 mr-1" /> Ship
                          </Button>
                        )}
                        {s.status === 'shipped' && (
                          <Button size="sm" className="bg-[#C8FF00] text-[#080C0F] font-bold" onClick={(e) => { e.stopPropagation(); handleShipmentAction(s.shipment_id, 'deliver'); }}>
                            <CheckCircle className="h-4 w-4 mr-1" /> Deliver
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

        {/* Returns Tab */}
        <TabsContent value="returns">
          {returns.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No returns recorded.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {returns.map(r => (
                <Card key={r.return_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors cursor-pointer" onClick={() => viewDetail('return', r.return_id)}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{r.customer_name}</h3>
                          <Badge className={statusColors[r.status]}>{r.status}</Badge>
                        </div>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">{r.reason}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">{r.restock ? 'Restocked' : 'Not restocked'} | Value: ₹{(r.restocked_value || 0).toLocaleString('en-IN')}</p>
                      </div>
                      {r.status === 'pending' && (
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleProcessReturn(r.return_id); }}>
                          Process
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ========== REORDER ALERTS TAB ========== */}
        <TabsContent value="reorder-alerts" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-[#F4F6F0]">Reorder Point Alerts</h3>
              <p className="text-xs text-[rgba(244,246,240,0.45)]">Items below reorder level — auto-grouped by vendor for PO creation</p>
            </div>
            <Button onClick={fetchReorderSuggestions} disabled={loadingReorder} size="sm" data-testid="refresh-reorder-btn">
              {loadingReorder ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-1" />}
              Refresh
            </Button>
          </div>

          {!reorderSuggestions && !loadingReorder && (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
              Click Refresh to check reorder levels
            </CardContent></Card>
          )}

          {loadingReorder && (
            <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-[#C8FF00]" /></div>
          )}

          {reorderSuggestions && !loadingReorder && (
            <>
              {reorderSuggestions.total_items_below_reorder === 0 ? (
                <Card><CardContent className="py-12 text-center">
                  <CheckCircle className="h-10 w-10 text-[#22C55E] mx-auto mb-3" />
                  <p className="text-sm text-[rgba(244,246,240,0.65)]">All items are at or above reorder levels</p>
                </CardContent></Card>
              ) : (
                <>
                  <div className="flex items-center gap-3 p-3 rounded bg-[rgba(255,59,47,0.08)] border border-[rgba(255,59,47,0.20)]">
                    <AlertTriangle className="h-5 w-5 text-[#FF3B2F] flex-shrink-0" />
                    <p className="text-sm text-[#FF3B2F] font-medium">{reorderSuggestions.total_items_below_reorder} item(s) below reorder point</p>
                  </div>

                  {reorderSuggestions.grouped_by_vendor?.map((group, gi) => (
                    <Card key={gi} className="border border-[rgba(255,255,255,0.07)]">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-sm">{group.vendor_name}</CardTitle>
                            <CardDescription className="text-xs">{group.items.length} items · Est. ₹{group.total_estimated_cost.toLocaleString('en-IN', {maximumFractionDigits: 0})}</CardDescription>
                          </div>
                          <Button size="sm" onClick={() => handleCreatePoFromGroup(group)} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid={`create-po-btn-${gi}`}>
                            <Plus className="h-4 w-4 mr-1" /> Create PO
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="space-y-2">
                          {group.items.map(item => (
                            <div key={item.item_id} className="flex items-center justify-between p-2 bg-[rgba(255,255,255,0.03)] rounded">
                              <div>
                                <p className="text-sm font-medium">{item.item_name}</p>
                                <p className="text-xs font-mono text-[rgba(244,246,240,0.45)]">{item.sku}</p>
                              </div>
                              <div className="text-right text-xs">
                                <p className="text-[#FF3B2F]">{item.current_stock} / {item.reorder_level} (short by {item.shortage})</p>
                                <p className="text-[rgba(244,246,240,0.45)]">Suggest: <span className="text-[#C8FF00] font-mono">{item.suggested_order_qty} units</span></p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </>
              )}
            </>
          )}
        </TabsContent>

        {/* ========== STOCKTAKE TAB ========== */}
        <TabsContent value="stocktake" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-[#F4F6F0]">Inventory Count / Stocktake</h3>
              <p className="text-xs text-[rgba(244,246,240,0.45)]">Create count sessions, enter physical quantities, apply variances</p>
            </div>
            <Button onClick={() => setShowStocktakeDialog(true)} size="sm" data-testid="new-stocktake-btn">
              <Plus className="h-4 w-4 mr-1" /> New Stocktake
            </Button>
          </div>

          {/* Active / Open Stocktake */}
          {activeStocktake && (
            <Card className={`border ${activeStocktake.status === 'finalized' ? 'border-[rgba(200,255,0,0.25)]' : 'border-[rgba(59,158,255,0.25)]'}`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm flex items-center gap-2">
                      {activeStocktake.status === 'finalized'
                        ? <CheckCircle className="h-4 w-4 text-[#C8FF00]" />
                        : <Clock className="h-4 w-4 text-[#3B9EFF]" />
                      }
                      {activeStocktake.name}
                    </CardTitle>
                    <CardDescription className="text-xs">{activeStocktake.warehouse_name} · {activeStocktake.counted_lines || 0}/{activeStocktake.total_lines} counted · Variance: {activeStocktake.total_variance > 0 ? '+' : ''}{activeStocktake.total_variance}</CardDescription>
                  </div>
                  {activeStocktake.status === 'in_progress' && (
                    <Button size="sm" onClick={() => handleFinalizeStocktake(activeStocktake.stocktake_id)} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="finalize-stocktake-btn">
                      Finalize & Apply
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {(activeStocktake.lines || []).map(line => (
                    <div key={line.item_id} className={`flex items-center gap-3 p-2 rounded ${line.counted ? 'bg-[rgba(200,255,0,0.04)]' : 'bg-[rgba(255,255,255,0.02)]'}`}>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{line.item_name}</p>
                        <p className="text-xs font-mono text-[rgba(244,246,240,0.45)]">{line.item_sku} · System: {line.system_quantity}</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {activeStocktake.status === 'in_progress' ? (
                          <CountInput
                            key={line.item_id}
                            defaultValue={line.counted_quantity ?? line.system_quantity}
                            onSubmit={(val) => handleSubmitCount(activeStocktake.stocktake_id, line.item_id, val)}
                          />
                        ) : (
                          <span className="text-sm font-mono">{line.counted_quantity ?? '—'}</span>
                        )}
                        {line.counted && (
                          <span className={`text-xs font-mono font-bold ${line.variance > 0 ? 'text-[#22C55E]' : line.variance < 0 ? 'text-[#FF3B2F]' : 'text-[rgba(244,246,240,0.35)]'}`}>
                            {line.variance > 0 ? '+' : ''}{line.variance}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Stocktake History */}
          {stocktakes.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Stocktake History</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {stocktakes.map(st => (
                  <div key={st.stocktake_id} className="flex items-center justify-between p-2 bg-[rgba(255,255,255,0.03)] rounded border border-[rgba(255,255,255,0.06)]">
                    <div>
                      <p className="text-sm font-medium">{st.name}</p>
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">{st.warehouse_name} · {st.counted_lines}/{st.total_lines} counted · {st.created_at?.split("T")[0]}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={st.status === 'finalized' ? 'bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]' : 'bg-[rgba(59,158,255,0.10)] text-[#3B9EFF] border border-[rgba(59,158,255,0.25)]'}>{st.status}</Badge>
                      {st.status === 'in_progress' && (
                        <Button variant="outline" size="sm" onClick={() => handleLoadStocktake(st.stocktake_id)}>Open</Button>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* ========== DIALOGS ========== */}

      {/* Stock Transfer Dialog */}
      <Dialog open={showTransferDialog} onOpenChange={setShowTransferDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Transfer Stock Between Warehouses</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>From Warehouse *</Label>
                <Select onValueChange={v => setNewTransfer(t => ({ ...t, from_warehouse_id: v }))}>
                  <SelectTrigger><SelectValue placeholder="Source" /></SelectTrigger>
                  <SelectContent>{warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>To Warehouse *</Label>
                <Select onValueChange={v => setNewTransfer(t => ({ ...t, to_warehouse_id: v }))}>
                  <SelectTrigger><SelectValue placeholder="Destination" /></SelectTrigger>
                  <SelectContent>{warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            <Separator />
            <div className="space-y-2">
              <Label>Add Items</Label>
              <div className="flex gap-2">
                <Select onValueChange={v => setTransferLine(tl => ({ ...tl, item_id: v }))}>
                  <SelectTrigger className="flex-1"><SelectValue placeholder="Select item" /></SelectTrigger>
                  <SelectContent>{items.map(i => <SelectItem key={i.item_id} value={i.item_id}>{i.name}</SelectItem>)}</SelectContent>
                </Select>
                <Input type="number" min="1" value={transferLine.quantity} onChange={e => setTransferLine(tl => ({ ...tl, quantity: parseInt(e.target.value) || 1 }))} className="w-20" />
                <Button variant="outline" size="sm" onClick={() => {
                  if (!transferLine.item_id) return toast.error("Select an item");
                  const item = items.find(i => i.item_id === transferLine.item_id);
                  setNewTransfer(t => ({
                    ...t,
                    items: [...t.items, { item_id: transferLine.item_id, item_name: item?.name || "", quantity: transferLine.quantity }]
                  }));
                  setTransferLine({ item_id: "", quantity: 1 });
                }}>Add</Button>
              </div>
              {newTransfer.items.length > 0 && (
                <div className="space-y-1 mt-2">
                  {newTransfer.items.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center p-2 bg-[rgba(255,255,255,0.03)] rounded text-sm">
                      <span>{item.item_name}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono">{item.quantity} units</span>
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-[#FF3B2F]" onClick={() => setNewTransfer(t => ({ ...t, items: t.items.filter((_, i) => i !== idx) }))}>×</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div><Label>Notes</Label><Input value={newTransfer.notes} onChange={e => setNewTransfer(t => ({ ...t, notes: e.target.value }))} placeholder="Optional notes" /></div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowTransferDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateTransfer} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="confirm-transfer-btn">Transfer</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* New Stocktake Dialog */}
      <Dialog open={showStocktakeDialog} onOpenChange={setShowStocktakeDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Start New Stocktake</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Warehouse *</Label>
              <Select onValueChange={v => setNewStocktake(s => ({ ...s, warehouse_id: v }))}>
                <SelectTrigger><SelectValue placeholder="Select warehouse to count" /></SelectTrigger>
                <SelectContent>{warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div><Label>Session Name</Label><Input value={newStocktake.name} onChange={e => setNewStocktake(s => ({ ...s, name: e.target.value }))} placeholder={`Stocktake ${new Date().toLocaleDateString()}`} /></div>
            <div><Label>Notes</Label><Input value={newStocktake.notes} onChange={e => setNewStocktake(s => ({ ...s, notes: e.target.value }))} placeholder="Optional notes" /></div>
            <p className="text-xs text-[rgba(244,246,240,0.45)]">All items with stock in the selected warehouse will be included for counting.</p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowStocktakeDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateStocktake} disabled={loadingStocktake} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="start-stocktake-btn">
              {loadingStocktake ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Start Stocktake
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Warehouse Dialog */}
      <Dialog open={showWarehouseDialog} onOpenChange={setShowWarehouseDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Warehouse</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Name *</Label><Input value={newWarehouse.name} onChange={(e) => setNewWarehouse({...newWarehouse, name: e.target.value})} /></div>
              <div><Label>Code</Label><Input value={newWarehouse.code} onChange={(e) => setNewWarehouse({...newWarehouse, code: e.target.value})} placeholder="e.g., WH-01" /></div>
            </div>
            <div><Label>Address</Label><Input value={newWarehouse.address} onChange={(e) => setNewWarehouse({...newWarehouse, address: e.target.value})} /></div>
            <div className="grid grid-cols-3 gap-4">
              <div><Label>City</Label><Input value={newWarehouse.city} onChange={(e) => setNewWarehouse({...newWarehouse, city: e.target.value})} /></div>
              <div><Label>State</Label><Input value={newWarehouse.state} onChange={(e) => setNewWarehouse({...newWarehouse, state: e.target.value})} /></div>
              <div><Label>Pincode</Label><Input value={newWarehouse.pincode} onChange={(e) => setNewWarehouse({...newWarehouse, pincode: e.target.value})} /></div>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="primary" checked={newWarehouse.is_primary} onChange={(e) => setNewWarehouse({...newWarehouse, is_primary: e.target.checked})} />
              <Label htmlFor="primary">Set as primary warehouse</Label>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowWarehouseDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateWarehouse} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Variant Dialog */}
      <Dialog open={showVariantDialog} onOpenChange={setShowVariantDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Item Variant</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Base Item *</Label>
              <Select onValueChange={(v) => setNewVariant({...newVariant, item_id: v})}>
                <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                <SelectContent>
                  {items.map(i => <SelectItem key={i.item_id} value={i.item_id}>{i.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Variant Name *</Label><Input value={newVariant.variant_name} onChange={(e) => setNewVariant({...newVariant, variant_name: e.target.value})} placeholder="e.g., Large - Red" /></div>
              <div><Label>SKU</Label><Input value={newVariant.sku} onChange={(e) => setNewVariant({...newVariant, sku: e.target.value})} placeholder="Auto-generated if empty" /></div>
            </div>
            <div><Label>Additional Rate (₹)</Label><Input type="number" value={newVariant.additional_rate} onChange={(e) => setNewVariant({...newVariant, additional_rate: parseFloat(e.target.value) || 0})} /></div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Initial Stock</Label>
                <Input type="number" value={newVariant.initial_stock} onChange={(e) => setNewVariant({...newVariant, initial_stock: parseInt(e.target.value) || 0})} />
              </div>
              <div>
                <Label>Warehouse</Label>
                <Select onValueChange={(v) => setNewVariant({...newVariant, warehouse_id: v})}>
                  <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                  <SelectContent>
                    {warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowVariantDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateVariant} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Bundle Dialog */}
      <Dialog open={showBundleDialog} onOpenChange={setShowBundleDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader><DialogTitle>Create Bundle / Kit</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Bundle Name *</Label><Input value={newBundle.name} onChange={(e) => setNewBundle({...newBundle, name: e.target.value})} /></div>
              <div><Label>SKU</Label><Input value={newBundle.sku} onChange={(e) => setNewBundle({...newBundle, sku: e.target.value})} /></div>
            </div>
            <div><Label>Description</Label><Textarea value={newBundle.description} onChange={(e) => setNewBundle({...newBundle, description: e.target.value})} /></div>
            
            <div className="border rounded p-4 bg-[#111820]">
              <h4 className="font-medium mb-3">Components</h4>
              <div className="flex gap-2 mb-3">
                <Select onValueChange={(v) => setBundleComponent({...bundleComponent, item_id: v})}>
                  <SelectTrigger className="flex-1"><SelectValue placeholder="Select item" /></SelectTrigger>
                  <SelectContent>
                    {items.map(i => <SelectItem key={i.item_id} value={i.item_id}>{i.name}</SelectItem>)}
                  </SelectContent>
                </Select>
                <Input type="number" className="w-24" placeholder="Qty" value={bundleComponent.quantity} onChange={(e) => setBundleComponent({...bundleComponent, quantity: parseInt(e.target.value) || 1})} />
                <Button onClick={handleAddBundleComponent}>Add</Button>
              </div>
              {newBundle.components.length > 0 && (
                <div className="space-y-2">
                  {newBundle.components.map((c, idx) => (
                    <div key={idx} className="flex justify-between items-center p-2 bg-[#111820] rounded border">
                      <span>{c.item_name || c.item_id}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[rgba(244,246,240,0.45)]">x{c.quantity}</span>
                        <Button variant="ghost" size="icon" onClick={() => setNewBundle({...newBundle, components: newBundle.components.filter((_, i) => i !== idx)})}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="autoRate" checked={newBundle.auto_calculate_rate} onChange={(e) => setNewBundle({...newBundle, auto_calculate_rate: e.target.checked})} />
              <Label htmlFor="autoRate">Auto-calculate rate from components</Label>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowBundleDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateBundle} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Serial/Batch Dialog */}
      <Dialog open={showSerialDialog} onOpenChange={setShowSerialDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Serial / Batch</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Item *</Label>
              <Select onValueChange={(v) => setNewSerial({...newSerial, item_id: v})}>
                <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                <SelectContent>
                  {items.map(i => <SelectItem key={i.item_id} value={i.item_id}>{i.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Tracking Type</Label>
                <Select value={newSerial.tracking_type} onValueChange={(v) => setNewSerial({...newSerial, tracking_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="serial">Serial Number</SelectItem>
                    <SelectItem value="batch">Batch / Lot</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>{newSerial.tracking_type === 'serial' ? 'Serial Number' : 'Batch Number'} *</Label><Input value={newSerial.number} onChange={(e) => setNewSerial({...newSerial, number: e.target.value})} /></div>
            </div>
            {newSerial.tracking_type === 'batch' && (
              <div><Label>Quantity</Label><Input type="number" value={newSerial.quantity} onChange={(e) => setNewSerial({...newSerial, quantity: parseInt(e.target.value) || 1})} /></div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Warehouse</Label>
                <Select onValueChange={(v) => setNewSerial({...newSerial, warehouse_id: v})}>
                  <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                  <SelectContent>
                    {warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Expiry Date</Label><Input type="date" value={newSerial.expiry_date} onChange={(e) => setNewSerial({...newSerial, expiry_date: e.target.value})} /></div>
            </div>
            <div><Label>Notes</Label><Textarea value={newSerial.notes} onChange={(e) => setNewSerial({...newSerial, notes: e.target.value})} /></div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowSerialDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateSerial} className="bg-[#C8FF00] text-[#080C0F] font-bold">Create</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Stock Adjustment Dialog */}
      <Dialog open={showAdjustmentDialog} onOpenChange={setShowAdjustmentDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Stock Adjustment</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Item *</Label>
              <Select onValueChange={(v) => setNewAdjustment({...newAdjustment, item_id: v})}>
                <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                <SelectContent>
                  {items.map(i => <SelectItem key={i.item_id} value={i.item_id}>{i.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Warehouse *</Label>
              <Select onValueChange={(v) => setNewAdjustment({...newAdjustment, warehouse_id: v})}>
                <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                <SelectContent>
                  {warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Adjustment Type</Label>
                <Select value={newAdjustment.adjustment_type} onValueChange={(v) => setNewAdjustment({...newAdjustment, adjustment_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="add">Add Stock</SelectItem>
                    <SelectItem value="subtract">Subtract Stock</SelectItem>
                    <SelectItem value="set">Set Stock Level</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Quantity *</Label><Input type="number" value={newAdjustment.quantity} onChange={(e) => setNewAdjustment({...newAdjustment, quantity: parseFloat(e.target.value) || 0})} /></div>
            </div>
            <div><Label>Reason *</Label><Input value={newAdjustment.reason} onChange={(e) => setNewAdjustment({...newAdjustment, reason: e.target.value})} placeholder="e.g., Inventory count, Damaged goods" /></div>
            <div><Label>Reference Number</Label><Input value={newAdjustment.reference_number} onChange={(e) => setNewAdjustment({...newAdjustment, reference_number: e.target.value})} /></div>
            <div><Label>Notes</Label><Textarea value={newAdjustment.notes} onChange={(e) => setNewAdjustment({...newAdjustment, notes: e.target.value})} /></div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowAdjustmentDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateAdjustment} className="bg-[#C8FF00] text-[#080C0F] font-bold">Apply Adjustment</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="capitalize">{detailType} Details</DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh]">
            {detailData && (
              <div className="space-y-4 p-1">
                {detailType === 'warehouse' && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Name</p><p className="font-medium">{detailData.name}</p></div>
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Code</p><p className="font-medium">{detailData.code || '-'}</p></div>
                    </div>
                    <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Address</p><p>{detailData.address} {detailData.city} {detailData.state} {detailData.pincode}</p></div>
                    <div className="grid grid-cols-2 gap-4">
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Items</p><p className="font-medium">{detailData.item_count || 0}</p></div>
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Total Units</p><p className="font-medium">{detailData.total_units || 0}</p></div>
                    </div>
                    {detailData.stock_items?.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Stock Items</h4>
                        <div className="border rounded max-h-48 overflow-y-auto">
                          <table className="w-full text-sm">
                            <thead className="bg-[#111820] sticky top-0"><tr><th className="px-3 py-2 text-left">Item</th><th className="px-3 py-2 text-right">Available</th><th className="px-3 py-2 text-right">Reserved</th></tr></thead>
                            <tbody>
                              {detailData.stock_items.map((si, idx) => (
                                <tr key={idx} className="border-t"><td className="px-3 py-2">{si.item_name}</td><td className="px-3 py-2 text-right">{si.available_stock}</td><td className="px-3 py-2 text-right">{si.reserved_stock || 0}</td></tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </>
                )}
                {detailType === 'bundle' && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Name</p><p className="font-medium">{detailData.name}</p></div>
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">SKU</p><p className="font-medium">{detailData.sku}</p></div>
                    </div>
                    <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Description</p><p>{detailData.description || '-'}</p></div>
                    <div className="grid grid-cols-2 gap-4">
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Rate</p><p className="font-bold text-lg">₹{(detailData.rate || 0).toLocaleString('en-IN')}</p></div>
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Max Assemblable</p><p className="font-medium">{detailData.max_assemblable || 0} units</p></div>
                    </div>
                    {detailData.components?.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Components</h4>
                        <div className="space-y-2">
                          {detailData.components.map((c, idx) => (
                            <div key={idx} className="flex justify-between items-center p-2 bg-[#111820] rounded">
                              <span>{c.item_name}</span>
                              <div className="text-right">
                                <span className="font-medium">x{c.quantity}</span>
                                <span className="text-xs text-[rgba(244,246,240,0.45)] ml-2">(Stock: {c.available_stock})</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
                {detailType === 'shipment' && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Package #</p><p className="font-medium">{detailData.package_number}</p></div>
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Status</p><Badge className={statusColors[detailData.status]}>{detailData.status}</Badge></div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Customer</p><p>{detailData.customer_name}</p></div>
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Sales Order</p><p>{detailData.sales_order_number}</p></div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Carrier</p><p>{detailData.carrier || '-'}</p></div>
                      <div><p className="text-sm text-[rgba(244,246,240,0.45)]">Tracking #</p><p>{detailData.tracking_number || '-'}</p></div>
                    </div>
                    {detailData.items?.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Shipped Items</h4>
                        <div className="space-y-2">
                          {detailData.items.map((i, idx) => (
                            <div key={idx} className="flex justify-between p-2 bg-[#111820] rounded">
                              <span>{i.item_name}</span>
                              <span>Qty: {i.quantity_shipped}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
                {(detailType === 'variant' || detailType === 'serial' || detailType === 'return') && (
                  <pre className="bg-[#111820] p-4 rounded text-xs overflow-auto">{JSON.stringify(detailData, null, 2)}</pre>
                )}
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}
