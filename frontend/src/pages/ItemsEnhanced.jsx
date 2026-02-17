import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Plus, Package, Search, Edit, Trash2, Warehouse, FolderTree, Tags, AlertTriangle, ArrowUpDown, BarChart3, RefreshCw } from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";

const itemTypeColors = {
  inventory: "bg-blue-100 text-blue-700",
  non_inventory: "bg-gray-100 text-gray-700",
  service: "bg-green-100 text-green-700",
  sales: "bg-purple-100 text-purple-700",
  sales_and_purchases: "bg-orange-100 text-orange-700"
};

export default function ItemsEnhanced() {
  const [activeTab, setActiveTab] = useState("items");
  const [items, setItems] = useState([]);
  const [groups, setGroups] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [priceLists, setPriceLists] = useState([]);
  const [adjustments, setAdjustments] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  const [stockSummary, setStockSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Dialogs
  const [showItemDialog, setShowItemDialog] = useState(false);
  const [showGroupDialog, setShowGroupDialog] = useState(false);
  const [showWarehouseDialog, setShowWarehouseDialog] = useState(false);
  const [showPriceListDialog, setShowPriceListDialog] = useState(false);
  const [showAdjustmentDialog, setShowAdjustmentDialog] = useState(false);
  const [editItem, setEditItem] = useState(null);

  // Form states
  const [newItem, setNewItem] = useState({ name: "", sku: "", description: "", item_type: "inventory", sales_rate: 0, purchase_rate: 0, unit: "pcs", tax_percentage: 18, hsn_code: "", initial_stock: 0, reorder_level: 10, group_id: "" });
  const [newGroup, setNewGroup] = useState({ name: "", description: "", parent_group_id: "" });
  const [newWarehouse, setNewWarehouse] = useState({ name: "", location: "", is_primary: false });
  const [newPriceList, setNewPriceList] = useState({ name: "", description: "", discount_percentage: 0, markup_percentage: 0 });
  const [newAdjustment, setNewAdjustment] = useState({ item_id: "", warehouse_id: "", adjustment_type: "add", quantity: 0, reason: "other", notes: "" });

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchItems(), fetchGroups(), fetchWarehouses(), fetchPriceLists(), fetchAdjustments(), fetchLowStock(), fetchStockSummary()]);
    setLoading(false);
  };

  const fetchItems = async () => {
    try {
      const url = search ? `${API}/items-enhanced?search=${encodeURIComponent(search)}` : `${API}/items-enhanced`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setItems(data.items || []);
    } catch (e) { console.error("Failed to fetch items:", e); }
  };

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/groups?include_inactive=true`, { headers });
      const data = await res.json();
      setGroups(data.groups || []);
    } catch (e) { console.error("Failed to fetch groups:", e); }
  };

  const fetchWarehouses = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/warehouses?include_inactive=true`, { headers });
      const data = await res.json();
      setWarehouses(data.warehouses || []);
    } catch (e) { console.error("Failed to fetch warehouses:", e); }
  };

  const fetchPriceLists = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/price-lists?include_inactive=true`, { headers });
      const data = await res.json();
      setPriceLists(data.price_lists || []);
    } catch (e) { console.error("Failed to fetch price lists:", e); }
  };

  const fetchAdjustments = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/adjustments`, { headers });
      const data = await res.json();
      setAdjustments(data.adjustments || []);
    } catch (e) { console.error("Failed to fetch adjustments:", e); }
  };

  const fetchLowStock = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/low-stock`, { headers });
      const data = await res.json();
      setLowStockItems(data.low_stock_items || []);
    } catch (e) { console.error("Failed to fetch low stock:", e); }
  };

  const fetchStockSummary = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/reports/stock-summary`, { headers });
      const data = await res.json();
      setStockSummary(data.stock_summary || null);
    } catch (e) { console.error("Failed to fetch stock summary:", e); }
  };

  // CRUD operations
  const handleCreateItem = async () => {
    if (!newItem.name) return toast.error("Item name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/`, { method: "POST", headers, body: JSON.stringify(newItem) });
      if (res.ok) {
        toast.success("Item created");
        setShowItemDialog(false);
        setNewItem({ name: "", sku: "", description: "", item_type: "inventory", sales_rate: 0, purchase_rate: 0, unit: "pcs", tax_percentage: 18, hsn_code: "", initial_stock: 0, reorder_level: 10, group_id: "" });
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to create item");
      }
    } catch (e) { toast.error("Error creating item"); }
  };

  const handleUpdateItem = async () => {
    if (!editItem) return;
    try {
      const res = await fetch(`${API}/items-enhanced/${editItem.item_id}`, { method: "PUT", headers, body: JSON.stringify(editItem) });
      if (res.ok) {
        toast.success("Item updated");
        setEditItem(null);
        fetchData();
      }
    } catch (e) { toast.error("Error updating item"); }
  };

  const handleDeleteItem = async (itemId) => {
    if (!confirm("Delete this item?")) return;
    try {
      const res = await fetch(`${API}/items-enhanced/${itemId}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Item deleted"); fetchData(); }
      else { const err = await res.json(); toast.error(err.detail || "Cannot delete item"); }
    } catch (e) { toast.error("Error deleting item"); }
  };

  const handleCreateGroup = async () => {
    if (!newGroup.name) return toast.error("Group name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/groups`, { method: "POST", headers, body: JSON.stringify(newGroup) });
      if (res.ok) {
        toast.success("Item group created");
        setShowGroupDialog(false);
        setNewGroup({ name: "", description: "", parent_group_id: "" });
        fetchGroups();
      }
    } catch (e) { toast.error("Error creating group"); }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!confirm("Delete this group?")) return;
    try {
      const res = await fetch(`${API}/items-enhanced/groups/${groupId}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Group deleted"); fetchGroups(); }
      else { const err = await res.json(); toast.error(err.detail || "Cannot delete group"); }
    } catch (e) { toast.error("Error deleting group"); }
  };

  const handleCreateWarehouse = async () => {
    if (!newWarehouse.name) return toast.error("Warehouse name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/warehouses`, { method: "POST", headers, body: JSON.stringify(newWarehouse) });
      if (res.ok) {
        toast.success("Warehouse created");
        setShowWarehouseDialog(false);
        setNewWarehouse({ name: "", location: "", is_primary: false });
        fetchWarehouses();
      }
    } catch (e) { toast.error("Error creating warehouse"); }
  };

  const handleCreatePriceList = async () => {
    if (!newPriceList.name) return toast.error("Price list name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/price-lists`, { method: "POST", headers, body: JSON.stringify(newPriceList) });
      if (res.ok) {
        toast.success("Price list created");
        setShowPriceListDialog(false);
        setNewPriceList({ name: "", description: "", discount_percentage: 0, markup_percentage: 0 });
        fetchPriceLists();
      }
    } catch (e) { toast.error("Error creating price list"); }
  };

  const handleDeletePriceList = async (pricelistId) => {
    if (!confirm("Delete this price list?")) return;
    try {
      const res = await fetch(`${API}/items-enhanced/price-lists/${pricelistId}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Price list deleted"); fetchPriceLists(); }
    } catch (e) { toast.error("Error deleting price list"); }
  };

  const handleCreateAdjustment = async () => {
    if (!newAdjustment.item_id || !newAdjustment.warehouse_id || newAdjustment.quantity <= 0) {
      return toast.error("Select item, warehouse and enter quantity > 0");
    }
    try {
      const res = await fetch(`${API}/items-enhanced/adjustments`, { method: "POST", headers, body: JSON.stringify(newAdjustment) });
      if (res.ok) {
        toast.success("Inventory adjusted");
        setShowAdjustmentDialog(false);
        setNewAdjustment({ item_id: "", warehouse_id: "", adjustment_type: "add", quantity: 0, reason: "other", notes: "" });
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to adjust inventory");
      }
    } catch (e) { toast.error("Error adjusting inventory"); }
  };

  const inventoryItems = items.filter(i => i.item_type === "inventory" || i.item_type === "sales_and_purchases");

  return (
    <div className="space-y-6" data-testid="items-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Inventory Management"
        description="Items, Groups, Warehouses, Price Lists & Adjustments"
        icon={Package}
        actions={
          <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        }
      />

      {/* Summary Cards */}
      <StatCardGrid columns={6}>
        <StatCard
          title="Total Items"
          value={items.length}
          icon={Package}
          variant="info"
        />
        <StatCard
          title="Item Groups"
          value={groups.length}
          icon={FolderTree}
          variant="purple"
        />
        <StatCard
          title="Warehouses"
          value={warehouses.length}
          icon={Warehouse}
          variant="success"
        />
        <StatCard
          title="Price Lists"
          value={priceLists.length}
          icon={Tags}
          variant="warning"
        />
        <StatCard
          title="Low Stock"
          value={lowStockItems.length}
          icon={AlertTriangle}
          variant={lowStockItems.length > 0 ? "danger" : "default"}
        />
        <StatCard
          title="Stock Value"
          value={formatCurrencyCompact(stockSummary?.total_stock_value || 0)}
          icon={BarChart3}
          variant="teal"
        />
      </StatCardGrid>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-flex">
          <TabsTrigger value="items">Items</TabsTrigger>
          <TabsTrigger value="groups">Groups</TabsTrigger>
          <TabsTrigger value="warehouses">Warehouses</TabsTrigger>
          <TabsTrigger value="priceLists">Price Lists</TabsTrigger>
          <TabsTrigger value="adjustments">Adjustments</TabsTrigger>
        </TabsList>

        {/* Items Tab */}
        <TabsContent value="items" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input value={search} onChange={(e) => setSearch(e.target.value)} onKeyUp={(e) => e.key === 'Enter' && fetchItems()} placeholder="Search items..." className="pl-10" data-testid="search-items" />
            </div>
            <Dialog open={showItemDialog} onOpenChange={setShowItemDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-item-btn">
                  <Plus className="h-4 w-4" /> New Item
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader><DialogTitle>Create Item</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Item Type *</Label>
                      <Select value={newItem.item_type} onValueChange={(v) => setNewItem({ ...newItem, item_type: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="inventory">Inventory</SelectItem>
                          <SelectItem value="non_inventory">Non-Inventory</SelectItem>
                          <SelectItem value="service">Service</SelectItem>
                          <SelectItem value="sales">Sales Only</SelectItem>
                          <SelectItem value="sales_and_purchases">Sales & Purchases</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Name *</Label>
                      <Input value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} placeholder="Item name" data-testid="item-name-input" />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div><Label>SKU</Label><Input value={newItem.sku} onChange={(e) => setNewItem({ ...newItem, sku: e.target.value })} placeholder="SKU code" /></div>
                    <div><Label>HSN Code</Label><Input value={newItem.hsn_code} onChange={(e) => setNewItem({ ...newItem, hsn_code: e.target.value })} placeholder="HSN code" /></div>
                    <div>
                      <Label>Unit</Label>
                      <Select value={newItem.unit} onValueChange={(v) => setNewItem({ ...newItem, unit: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="pcs">Pieces</SelectItem>
                          <SelectItem value="nos">Numbers</SelectItem>
                          <SelectItem value="kg">Kilograms</SelectItem>
                          <SelectItem value="ltr">Liters</SelectItem>
                          <SelectItem value="hrs">Hours</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label>Item Group</Label>
                    <Select value={newItem.group_id || "none"} onValueChange={(v) => setNewItem({ ...newItem, group_id: v === "none" ? "" : v })}>
                      <SelectTrigger><SelectValue placeholder="Select group (optional)" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Group</SelectItem>
                        {groups.map(g => <SelectItem key={g.group_id} value={g.group_id}>{g.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div><Label>Description</Label><Textarea value={newItem.description} onChange={(e) => setNewItem({ ...newItem, description: e.target.value })} placeholder="Item description" /></div>
                  <div className="grid grid-cols-3 gap-4">
                    <div><Label>Sales Rate *</Label><Input type="number" value={newItem.sales_rate} onChange={(e) => setNewItem({ ...newItem, sales_rate: parseFloat(e.target.value) || 0 })} /></div>
                    <div><Label>Purchase Rate</Label><Input type="number" value={newItem.purchase_rate} onChange={(e) => setNewItem({ ...newItem, purchase_rate: parseFloat(e.target.value) || 0 })} /></div>
                    <div><Label>Tax %</Label><Input type="number" value={newItem.tax_percentage} onChange={(e) => setNewItem({ ...newItem, tax_percentage: parseFloat(e.target.value) || 0 })} /></div>
                  </div>
                  {(newItem.item_type === "inventory" || newItem.item_type === "sales_and_purchases") && (
                    <div className="grid grid-cols-2 gap-4">
                      <div><Label>Initial Stock</Label><Input type="number" value={newItem.initial_stock} onChange={(e) => setNewItem({ ...newItem, initial_stock: parseFloat(e.target.value) || 0 })} /></div>
                      <div><Label>Reorder Level</Label><Input type="number" value={newItem.reorder_level} onChange={(e) => setNewItem({ ...newItem, reorder_level: parseFloat(e.target.value) || 0 })} /></div>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowItemDialog(false)}>Cancel</Button>
                  <Button onClick={handleCreateItem} className="bg-[#22EDA9] text-black" data-testid="create-item-submit">Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? <div className="text-center py-8">Loading...</div> : items.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><Package className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No items found</p></CardContent></Card>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Item</th>
                    <th className="px-4 py-3 text-left font-medium">SKU</th>
                    <th className="px-4 py-3 text-left font-medium">Type</th>
                    <th className="px-4 py-3 text-left font-medium">Group</th>
                    <th className="px-4 py-3 text-right font-medium">Sales Rate</th>
                    <th className="px-4 py-3 text-right font-medium">Stock</th>
                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(item => (
                    <tr key={item.item_id} className="border-t hover:bg-gray-50" data-testid={`item-row-${item.item_id}`}>
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium">{item.name}</p>
                          {item.hsn_code && <p className="text-xs text-gray-500">HSN: {item.hsn_code}</p>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{item.sku || '-'}</td>
                      <td className="px-4 py-3"><Badge className={itemTypeColors[item.item_type] || "bg-gray-100 text-gray-700"}>{item.item_type}</Badge></td>
                      <td className="px-4 py-3 text-gray-600">{item.group_name || '-'}</td>
                      <td className="px-4 py-3 text-right font-medium">₹{(item.sales_rate || item.rate || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right">
                        {(item.item_type === "inventory" || item.item_type === "sales_and_purchases") ? (
                          <span className={(item.total_stock || item.stock_on_hand || 0) <= (item.reorder_level || 0) ? "text-red-600 font-medium" : ""}>
                            {item.total_stock || item.stock_on_hand || 0}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="icon" variant="ghost" onClick={() => setEditItem(item)} data-testid={`edit-item-${item.item_id}`}><Edit className="h-4 w-4" /></Button>
                          <Button size="icon" variant="ghost" onClick={() => handleDeleteItem(item.item_id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        {/* Groups Tab */}
        <TabsContent value="groups" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={showGroupDialog} onOpenChange={setShowGroupDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-group-btn">
                  <Plus className="h-4 w-4" /> New Group
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Item Group</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div><Label>Name *</Label><Input value={newGroup.name} onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })} placeholder="Group name" data-testid="group-name-input" /></div>
                  <div><Label>Description</Label><Textarea value={newGroup.description} onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })} placeholder="Description" /></div>
                  <div>
                    <Label>Parent Group</Label>
                    <Select value={newGroup.parent_group_id || "none"} onValueChange={(v) => setNewGroup({ ...newGroup, parent_group_id: v === "none" ? "" : v })}>
                      <SelectTrigger><SelectValue placeholder="Select parent (optional)" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Parent</SelectItem>
                        {groups.map(g => <SelectItem key={g.group_id} value={g.group_id}>{g.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowGroupDialog(false)}>Cancel</Button>
                  <Button onClick={handleCreateGroup} className="bg-[#22EDA9] text-black" data-testid="create-group-submit">Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {groups.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><FolderTree className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No item groups yet</p></CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map(group => (
                <Card key={group.group_id} data-testid={`group-card-${group.group_id}`}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg">{group.name}</CardTitle>
                      <Button size="icon" variant="ghost" onClick={() => handleDeleteGroup(group.group_id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2">{group.description || "No description"}</p>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Items:</span>
                      <span className="font-medium">{group.item_count || 0}</span>
                    </div>
                    {group.parent_group_name && (
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-gray-500">Parent:</span>
                        <span>{group.parent_group_name}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Warehouses Tab */}
        <TabsContent value="warehouses" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={showWarehouseDialog} onOpenChange={setShowWarehouseDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-warehouse-btn">
                  <Plus className="h-4 w-4" /> New Warehouse
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Warehouse</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div><Label>Name *</Label><Input value={newWarehouse.name} onChange={(e) => setNewWarehouse({ ...newWarehouse, name: e.target.value })} placeholder="Warehouse name" data-testid="warehouse-name-input" /></div>
                  <div><Label>Location</Label><Input value={newWarehouse.location} onChange={(e) => setNewWarehouse({ ...newWarehouse, location: e.target.value })} placeholder="Address or location" /></div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" id="isPrimary" checked={newWarehouse.is_primary} onChange={(e) => setNewWarehouse({ ...newWarehouse, is_primary: e.target.checked })} className="rounded" />
                    <Label htmlFor="isPrimary">Primary Warehouse</Label>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowWarehouseDialog(false)}>Cancel</Button>
                  <Button onClick={handleCreateWarehouse} className="bg-[#22EDA9] text-black" data-testid="create-warehouse-submit">Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {warehouses.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><Warehouse className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No warehouses yet</p></CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {warehouses.map(wh => (
                <Card key={wh.warehouse_id} className={wh.is_primary ? "border-green-300 bg-green-50" : ""} data-testid={`warehouse-card-${wh.warehouse_id}`}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-lg">{wh.name}</CardTitle>
                        {wh.is_primary && <Badge className="bg-green-100 text-green-700 text-xs">Primary</Badge>}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-3">{wh.location || "No location set"}</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-gray-100 rounded p-2 text-center">
                        <p className="text-gray-500 text-xs">Items</p>
                        <p className="font-bold">{wh.total_items || 0}</p>
                      </div>
                      <div className="bg-gray-100 rounded p-2 text-center">
                        <p className="text-gray-500 text-xs">Stock</p>
                        <p className="font-bold">{wh.total_stock || 0}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Price Lists Tab */}
        <TabsContent value="priceLists" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={showPriceListDialog} onOpenChange={setShowPriceListDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-pricelist-btn">
                  <Plus className="h-4 w-4" /> New Price List
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Price List</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div><Label>Name *</Label><Input value={newPriceList.name} onChange={(e) => setNewPriceList({ ...newPriceList, name: e.target.value })} placeholder="Price list name" data-testid="pricelist-name-input" /></div>
                  <div><Label>Description</Label><Textarea value={newPriceList.description} onChange={(e) => setNewPriceList({ ...newPriceList, description: e.target.value })} placeholder="Description" /></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div><Label>Discount %</Label><Input type="number" value={newPriceList.discount_percentage} onChange={(e) => setNewPriceList({ ...newPriceList, discount_percentage: parseFloat(e.target.value) || 0 })} /></div>
                    <div><Label>Markup %</Label><Input type="number" value={newPriceList.markup_percentage} onChange={(e) => setNewPriceList({ ...newPriceList, markup_percentage: parseFloat(e.target.value) || 0 })} /></div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowPriceListDialog(false)}>Cancel</Button>
                  <Button onClick={handleCreatePriceList} className="bg-[#22EDA9] text-black" data-testid="create-pricelist-submit">Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {priceLists.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><Tags className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No price lists yet</p></CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {priceLists.map(pl => (
                <Card key={pl.pricelist_id} data-testid={`pricelist-card-${pl.pricelist_id}`}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg">{pl.name}</CardTitle>
                      <Button size="icon" variant="ghost" onClick={() => handleDeletePriceList(pl.pricelist_id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-3">{pl.description || "No description"}</p>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="bg-gray-100 rounded p-2 text-center">
                        <p className="text-gray-500 text-xs">Discount</p>
                        <p className="font-bold">{pl.discount_percentage || 0}%</p>
                      </div>
                      <div className="bg-gray-100 rounded p-2 text-center">
                        <p className="text-gray-500 text-xs">Markup</p>
                        <p className="font-bold">{pl.markup_percentage || 0}%</p>
                      </div>
                      <div className="bg-gray-100 rounded p-2 text-center">
                        <p className="text-gray-500 text-xs">Items</p>
                        <p className="font-bold">{pl.item_count || 0}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Adjustments Tab */}
        <TabsContent value="adjustments" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={showAdjustmentDialog} onOpenChange={setShowAdjustmentDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-adjustment-btn">
                  <Plus className="h-4 w-4" /> New Adjustment
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Inventory Adjustment</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label>Item *</Label>
                    <Select value={newAdjustment.item_id} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, item_id: v })}>
                      <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                      <SelectContent>
                        {inventoryItems.map(item => <SelectItem key={item.item_id} value={item.item_id}>{item.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Warehouse *</Label>
                    <Select value={newAdjustment.warehouse_id} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, warehouse_id: v })}>
                      <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                      <SelectContent>
                        {warehouses.map(wh => <SelectItem key={wh.warehouse_id} value={wh.warehouse_id}>{wh.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Adjustment Type *</Label>
                      <Select value={newAdjustment.adjustment_type} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, adjustment_type: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="add">Add Stock</SelectItem>
                          <SelectItem value="subtract">Remove Stock</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Quantity *</Label>
                      <Input type="number" min="1" value={newAdjustment.quantity} onChange={(e) => setNewAdjustment({ ...newAdjustment, quantity: parseInt(e.target.value) || 0 })} data-testid="adjustment-quantity-input" />
                    </div>
                  </div>
                  <div>
                    <Label>Reason</Label>
                    <Select value={newAdjustment.reason} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, reason: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="initial">Initial Stock</SelectItem>
                        <SelectItem value="purchase">Purchase</SelectItem>
                        <SelectItem value="sale">Sale</SelectItem>
                        <SelectItem value="damage">Damage</SelectItem>
                        <SelectItem value="recount">Physical Recount</SelectItem>
                        <SelectItem value="transfer">Transfer</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div><Label>Notes</Label><Textarea value={newAdjustment.notes} onChange={(e) => setNewAdjustment({ ...newAdjustment, notes: e.target.value })} placeholder="Additional notes" /></div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowAdjustmentDialog(false)}>Cancel</Button>
                  <Button onClick={handleCreateAdjustment} className="bg-[#22EDA9] text-black" data-testid="create-adjustment-submit">Create Adjustment</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {adjustments.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><ArrowUpDown className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No inventory adjustments yet</p></CardContent></Card>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Item</th>
                    <th className="px-4 py-3 text-left font-medium">Warehouse</th>
                    <th className="px-4 py-3 text-center font-medium">Type</th>
                    <th className="px-4 py-3 text-right font-medium">Qty</th>
                    <th className="px-4 py-3 text-left font-medium">Reason</th>
                    <th className="px-4 py-3 text-right font-medium">Stock After</th>
                  </tr>
                </thead>
                <tbody>
                  {adjustments.map(adj => (
                    <tr key={adj.adjustment_id} className="border-t hover:bg-gray-50" data-testid={`adjustment-row-${adj.adjustment_id}`}>
                      <td className="px-4 py-3 text-gray-600">{new Date(adj.date || adj.created_time).toLocaleDateString('en-IN')}</td>
                      <td className="px-4 py-3 font-medium">{adj.item_name}</td>
                      <td className="px-4 py-3">{adj.warehouse_name}</td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={adj.adjustment_type === "add" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}>
                          {adj.adjustment_type === "add" ? "+" : "-"}{adj.quantity}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">{adj.quantity}</td>
                      <td className="px-4 py-3 capitalize">{adj.reason}</td>
                      <td className="px-4 py-3 text-right font-medium">{adj.stock_after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Edit Item Dialog */}
      <Dialog open={!!editItem} onOpenChange={(open) => !open && setEditItem(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>Edit Item</DialogTitle></DialogHeader>
          {editItem && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Item Type</Label>
                  <Select value={editItem.item_type} onValueChange={(v) => setEditItem({ ...editItem, item_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="inventory">Inventory</SelectItem>
                      <SelectItem value="non_inventory">Non-Inventory</SelectItem>
                      <SelectItem value="service">Service</SelectItem>
                      <SelectItem value="sales">Sales Only</SelectItem>
                      <SelectItem value="sales_and_purchases">Sales & Purchases</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Name *</Label><Input value={editItem.name} onChange={(e) => setEditItem({ ...editItem, name: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>SKU</Label><Input value={editItem.sku || ""} onChange={(e) => setEditItem({ ...editItem, sku: e.target.value })} /></div>
                <div><Label>HSN Code</Label><Input value={editItem.hsn_code || ""} onChange={(e) => setEditItem({ ...editItem, hsn_code: e.target.value })} /></div>
                <div><Label>Unit</Label><Input value={editItem.unit || ""} onChange={(e) => setEditItem({ ...editItem, unit: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>Sales Rate</Label><Input type="number" value={editItem.sales_rate || 0} onChange={(e) => setEditItem({ ...editItem, sales_rate: parseFloat(e.target.value) || 0 })} /></div>
                <div><Label>Purchase Rate</Label><Input type="number" value={editItem.purchase_rate || 0} onChange={(e) => setEditItem({ ...editItem, purchase_rate: parseFloat(e.target.value) || 0 })} /></div>
                <div><Label>Tax %</Label><Input type="number" value={editItem.tax_percentage || 0} onChange={(e) => setEditItem({ ...editItem, tax_percentage: parseFloat(e.target.value) || 0 })} /></div>
              </div>
              {(editItem.item_type === "inventory" || editItem.item_type === "sales_and_purchases") && (
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>Reorder Level</Label><Input type="number" value={editItem.reorder_level || 0} onChange={(e) => setEditItem({ ...editItem, reorder_level: parseInt(e.target.value) || 0 })} /></div>
                  <div>
                    <Label>Stock (read-only)</Label>
                    <Input type="number" value={editItem.total_stock || editItem.stock_on_hand || 0} disabled className="bg-gray-100" />
                    <p className="text-xs text-gray-500 mt-1">Use Adjustments tab to modify stock</p>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditItem(null)}>Cancel</Button>
            <Button onClick={handleUpdateItem} className="bg-[#22EDA9] text-black">Update Item</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Low Stock Alert Section */}
      {lowStockItems.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" /> Low Stock Alerts ({lowStockItems.length} items)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {lowStockItems.slice(0, 6).map(item => (
                <div key={item.item_id} className="bg-white rounded-lg p-3 border border-red-200">
                  <p className="font-medium text-sm">{item.name}</p>
                  <div className="flex justify-between mt-1 text-xs">
                    <span className="text-gray-500">Current: <span className="text-red-600 font-bold">{item.current_stock}</span></span>
                    <span className="text-gray-500">Reorder: {item.reorder_level}</span>
                  </div>
                  <p className="text-xs text-red-600 mt-1">Shortage: {item.shortage} units</p>
                </div>
              ))}
            </div>
            {lowStockItems.length > 6 && (
              <p className="text-sm text-red-600 mt-3">+ {lowStockItems.length - 6} more items need attention</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
