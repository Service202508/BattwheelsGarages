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
          <TabsTrigger value="variants">Variants</TabsTrigger>
          <TabsTrigger value="bundles">Bundles</TabsTrigger>
          <TabsTrigger value="serial-batch">Serial/Batch</TabsTrigger>
          <TabsTrigger value="shipments">Shipments</TabsTrigger>
          <TabsTrigger value="returns">Returns</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Low Stock Alert */}
          {lowStockItems.length > 0 && (
            <Card className="border-l-4 border-l-red-500">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2 text-red-700">
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
                        <p className="text-red-600 font-bold">{item.total_stock} in stock</p>
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
          {loading ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</div>
          ) : warehouses.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No warehouses. Create one to start tracking inventory by location.</CardContent></Card>
          ) : (
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
          )}
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
          {serialBatches.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">No serial numbers or batches. Track individual units or lot numbers for traceability.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {serialBatches.map(sb => (
                <Card key={sb.serial_batch_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors cursor-pointer" onClick={() => viewDetail('serial', sb.serial_batch_id)}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <Barcode className="h-8 w-8 text-[rgba(244,246,240,0.45)]" />
                        <div>
                          <h3 className="font-semibold">{sb.number}</h3>
                          <p className="text-sm text-[rgba(244,246,240,0.45)]">{sb.tracking_type === 'serial' ? 'Serial Number' : `Batch (Qty: ${sb.quantity})`}</p>
                        </div>
                      </div>
                      <Badge className={statusColors[sb.status]}>{sb.status}</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
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
      </Tabs>

      {/* ========== DIALOGS ========== */}

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
