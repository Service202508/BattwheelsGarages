import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Switch } from "../components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator
} from "../components/ui/dropdown-menu";
import {
  Tabs, TabsContent, TabsList, TabsTrigger
} from "../components/ui/tabs";
import {
  Package, Plus, Search, RefreshCw, Layers, Box, Hammer,
  Trash2, Edit, Eye, MoreHorizontal, AlertTriangle,
  CheckCircle, XCircle, ArrowDown, ArrowUp, Wrench, BarChart3
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CompositeItems() {
  const [loading, setLoading] = useState(true);
  const [compositeItems, setCompositeItems] = useState([]);
  const [summary, setSummary] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showBuildDialog, setShowBuildDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  // Available inventory items
  const [inventoryItems, setInventoryItems] = useState([]);

  // Create form
  const [form, setForm] = useState({
    name: "",
    sku: "",
    description: "",
    type: "kit",
    selling_price: 0,
    auto_calculate_price: true,
    markup_percentage: 0,
    track_inventory: true,
    auto_build: false,
    min_build_quantity: 1,
    category: "",
    components: []
  });

  // Component add form
  const [componentForm, setComponentForm] = useState({
    item_id: "",
    quantity: 1,
    unit: "pcs",
    waste_percentage: 0
  });

  // Build form
  const [buildQty, setBuildQty] = useState(1);
  const [buildNotes, setBuildNotes] = useState("");
  const [availability, setAvailability] = useState(null);

  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${localStorage.getItem("token")}`
  };

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [itemsRes, summaryRes, inventoryRes] = await Promise.all([
        fetch(`${API}/composite-items?is_active=true`, { headers }),
        fetch(`${API}/composite-items/summary`, { headers }),
        fetch(`${API}/items-enhanced/?per_page=500`, { headers })
      ]);
      const [itemsData, summaryData, inventoryData] = await Promise.all([
        itemsRes.json(), summaryRes.json(), inventoryRes.json()
      ]);
      setCompositeItems(itemsData.composite_items || []);
      setSummary(summaryData);
      setInventoryItems((inventoryData.items || []).filter(i => !i.is_composite));
    } catch (e) {
      console.error("Failed to fetch:", e);
    }
    setLoading(false);
  };

  const addComponent = () => {
    if (!componentForm.item_id) {
      toast.error("Select an item");
      return;
    }
    if (form.components.some(c => c.item_id === componentForm.item_id)) {
      toast.error("Item already added");
      return;
    }
    const item = inventoryItems.find(i => i.item_id === componentForm.item_id);
    setForm({
      ...form,
      components: [...form.components, {
        ...componentForm,
        item_name: item?.name || ""
      }]
    });
    setComponentForm({ item_id: "", quantity: 1, unit: "pcs", waste_percentage: 0 });
  };

  const removeComponent = (idx) => {
    setForm({ ...form, components: form.components.filter((_, i) => i !== idx) });
  };

  const createCompositeItem = async () => {
    if (!form.name) { toast.error("Enter item name"); return; }
    if (form.components.length === 0) { toast.error("Add at least one component"); return; }
    try {
      const res = await fetch(`${API}/composite-items`, {
        method: "POST", headers, body: JSON.stringify(form)
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Composite item created");
        setShowCreateDialog(false);
        resetForm();
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create");
      }
    } catch (e) {
      toast.error("Failed to create composite item");
    }
  };

  const resetForm = () => {
    setForm({
      name: "", sku: "", description: "", type: "kit",
      selling_price: 0, auto_calculate_price: true, markup_percentage: 0,
      track_inventory: true, auto_build: false, min_build_quantity: 1,
      category: "", components: []
    });
  };

  const viewDetail = async (compositeId) => {
    try {
      const res = await fetch(`${API}/composite-items/${compositeId}`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setSelectedItem(data.composite_item);
        setShowDetailDialog(true);
      }
    } catch (e) {
      toast.error("Failed to load details");
    }
  };

  const openBuildDialog = async (item) => {
    setSelectedItem(item);
    setBuildQty(1);
    setBuildNotes("");
    setAvailability(null);
    setShowBuildDialog(true);
    // Check availability
    try {
      const res = await fetch(`${API}/composite-items/${item.composite_id}/availability?quantity=1`, { headers });
      const data = await res.json();
      if (data.code === 0) setAvailability(data);
    } catch (e) { /* ignore */ }
  };

  const checkAvailability = async (qty) => {
    if (!selectedItem) return;
    try {
      const res = await fetch(`${API}/composite-items/${selectedItem.composite_id}/availability?quantity=${qty}`, { headers });
      const data = await res.json();
      if (data.code === 0) setAvailability(data);
    } catch (e) { /* ignore */ }
  };

  const buildItem = async () => {
    if (!selectedItem) return;
    try {
      const res = await fetch(`${API}/composite-items/${selectedItem.composite_id}/build`, {
        method: "POST", headers,
        body: JSON.stringify({ quantity: buildQty, notes: buildNotes })
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
        setShowBuildDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Build failed");
      }
    } catch (e) {
      toast.error("Failed to build");
    }
  };

  const unbuildItem = async (compositeId) => {
    try {
      const res = await fetch(`${API}/composite-items/${compositeId}/unbuild`, {
        method: "POST", headers,
        body: JSON.stringify({ quantity: 1 })
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
        fetchData();
      } else {
        toast.error(data.detail || "Unbuild failed");
      }
    } catch (e) {
      toast.error("Failed to unbuild");
    }
  };

  const deleteItem = async (compositeId) => {
    if (!confirm("Delete this composite item? This cannot be undone.")) return;
    try {
      const res = await fetch(`${API}/composite-items/${compositeId}`, {
        method: "DELETE", headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Composite item deleted");
        fetchData();
      }
    } catch (e) {
      toast.error("Failed to delete");
    }
  };

  const formatCurrency = (v) => `₹${(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  const filteredItems = compositeItems.filter(item => {
    const matchesSearch = !searchQuery ||
      item.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.sku?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = !filterType || item.type === filterType;
    return matchesSearch && matchesType;
  });

  const typeLabels = { kit: "Kit", assembly: "Assembly", bundle: "Bundle" };
  const typeColors = {
    kit: "bg-blue-100 text-[#3B9EFF]",
    assembly: "bg-purple-100 text-[#8B5CF6]",
    bundle: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]"
  };

  return (
    <div className="p-6 space-y-6" data-testid="composite-items-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold" data-testid="page-title">Composite Items</h1>
          <p className="text-gray-500">Manage kits, assemblies, and product bundles</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
          <Button onClick={() => setShowCreateDialog(true)} data-testid="create-composite-btn">
            <Plus className="h-4 w-4 mr-2" /> New Composite Item
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4" data-testid="summary-cards">
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">Total Items</p>
              <p className="text-2xl font-bold" data-testid="total-items">{summary.total_items}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(34,197,94,0.08)] border-green-200">
            <CardContent className="p-4">
              <p className="text-sm text-green-600">Active</p>
              <p className="text-2xl font-bold text-green-700" data-testid="active-count">{summary.active}</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <p className="text-sm text-[#3B9EFF]">Kits</p>
              <p className="text-2xl font-bold text-[#3B9EFF]">{summary.kits}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(139,92,246,0.08)] border-purple-200">
            <CardContent className="p-4">
              <p className="text-sm text-purple-600">Assemblies</p>
              <p className="text-2xl font-bold text-[#8B5CF6]">{summary.assemblies}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(200,255,0,0.08)] border-[rgba(200,255,0,0.20)]">
            <CardContent className="p-4">
              <p className="text-sm text-[#C8FF00] text-600">Bundles</p>
              <p className="text-2xl font-bold text-[#C8FF00] text-700">{summary.bundles}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(255,140,0,0.08)] border-orange-200">
            <CardContent className="p-4">
              <p className="text-sm text-[#FF8C00]">Inventory Value</p>
              <p className="text-xl font-bold text-[#FF8C00]" data-testid="inventory-value">{formatCurrency(summary.inventory_value)}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by name or SKU..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            data-testid="search-input"
          />
        </div>
        <Select value={filterType || "all"} onValueChange={(v) => setFilterType(v === "all" ? "" : v)}>
          <SelectTrigger className="w-[180px]" data-testid="type-filter">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="kit">Kits</SelectItem>
            <SelectItem value="assembly">Assemblies</SelectItem>
            <SelectItem value="bundle">Bundles</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Items Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-center py-12 text-gray-500">Loading composite items...</p>
          ) : filteredItems.length === 0 ? (
            <div className="text-center py-12" data-testid="empty-state">
              <Layers className="h-12 w-12 mx-auto text-[rgba(244,246,240,0.20)] mb-3" />
              <p className="text-gray-500 font-medium">No composite items yet</p>
              <p className="text-sm text-gray-400 mb-4">Create kits, assemblies, or bundles from your inventory items</p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" /> Create First Composite Item
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="composite-items-table">
                <thead className="bg-[#111820] border-b">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Name</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">SKU</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Type</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Components</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Cost</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Selling Price</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Stock</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Available</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredItems.map((item) => (
                    <tr key={item.composite_id} className="hover:bg-[#111820]" data-testid={`item-row-${item.composite_id}`}>
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium">{item.name}</p>
                          {item.description && (
                            <p className="text-xs text-gray-400 truncate max-w-[200px]">{item.description}</p>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">{item.sku}</td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={typeColors[item.type] || ""}>{typeLabels[item.type] || item.type}</Badge>
                      </td>
                      <td className="px-4 py-3 text-center">{item.components?.length || 0}</td>
                      <td className="px-4 py-3 text-right text-gray-500">{formatCurrency(item.current_component_cost || item.component_cost)}</td>
                      <td className="px-4 py-3 text-right font-medium">{formatCurrency(item.selling_price)}</td>
                      <td className="px-4 py-3 text-center font-medium">{item.stock_on_hand || 0}</td>
                      <td className="px-4 py-3 text-center">
                        {item.components_available ? (
                          <Badge className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]">Ready</Badge>
                        ) : (
                          <Badge className="bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]">Shortage</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" data-testid={`actions-${item.composite_id}`}>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => viewDetail(item.composite_id)}>
                              <Eye className="h-4 w-4 mr-2" /> View Details
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => openBuildDialog(item)}>
                              <Hammer className="h-4 w-4 mr-2" /> Build
                            </DropdownMenuItem>
                            {item.stock_on_hand > 0 && (
                              <DropdownMenuItem onClick={() => unbuildItem(item.composite_id)}>
                                <Wrench className="h-4 w-4 mr-2" /> Unbuild (1)
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-red-600" onClick={() => deleteItem(item.composite_id)}>
                              <Trash2 className="h-4 w-4 mr-2" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Composite Item Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Composite Item</DialogTitle>
            <DialogDescription>Bundle multiple items into a single sellable product</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Item Name *</Label>
                <Input
                  placeholder="e.g., EV Service Kit"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  data-testid="form-name"
                />
              </div>
              <div>
                <Label>SKU (auto-generated if blank)</Label>
                <Input
                  placeholder="KIT-001"
                  value={form.sku}
                  onChange={(e) => setForm({ ...form, sku: e.target.value })}
                  data-testid="form-sku"
                />
              </div>
            </div>

            <div>
              <Label>Description</Label>
              <Input
                placeholder="Brief description"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Type</Label>
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                  <SelectTrigger data-testid="form-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="kit">Kit - Pre-packaged set</SelectItem>
                    <SelectItem value="assembly">Assembly - Built from parts</SelectItem>
                    <SelectItem value="bundle">Bundle - Sold together</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Category</Label>
                <Input
                  placeholder="e.g., Service Kits"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Markup %</Label>
                <Input
                  type="number"
                  value={form.markup_percentage}
                  onChange={(e) => setForm({ ...form, markup_percentage: parseFloat(e.target.value) || 0 })}
                />
                <p className="text-xs text-gray-500 mt-1">Applied on top of component cost</p>
              </div>
              <div>
                <Label>Min Build Quantity</Label>
                <Input
                  type="number" min="1"
                  value={form.min_build_quantity}
                  onChange={(e) => setForm({ ...form, min_build_quantity: parseInt(e.target.value) || 1 })}
                />
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  checked={form.auto_calculate_price}
                  onCheckedChange={(v) => setForm({ ...form, auto_calculate_price: v })}
                />
                <Label>Auto-calculate price</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={form.auto_build}
                  onCheckedChange={(v) => setForm({ ...form, auto_build: v })}
                />
                <Label>Auto-build on sale</Label>
              </div>
            </div>

            {!form.auto_calculate_price && (
              <div>
                <Label>Selling Price</Label>
                <Input
                  type="number"
                  value={form.selling_price}
                  onChange={(e) => setForm({ ...form, selling_price: parseFloat(e.target.value) || 0 })}
                />
              </div>
            )}

            <Separator />

            {/* Components Section */}
            <div>
              <Label className="text-base font-semibold mb-3 block">Components (Bill of Materials)</Label>
              <div className="grid grid-cols-12 gap-2 mb-3">
                <div className="col-span-5">
                  <Select value={componentForm.item_id} onValueChange={(v) => setComponentForm({ ...componentForm, item_id: v })}>
                    <SelectTrigger data-testid="component-select">
                      <SelectValue placeholder="Select item" />
                    </SelectTrigger>
                    <SelectContent>
                      {inventoryItems.map(item => (
                        <SelectItem key={item.item_id} value={item.item_id}>
                          {item.name} {item.stock_on_hand > 0 ? `(${item.stock_on_hand} in stock)` : "(0 stock)"}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-2">
                  <Input
                    type="number" placeholder="Qty" min="0.1" step="0.1"
                    value={componentForm.quantity}
                    onChange={(e) => setComponentForm({ ...componentForm, quantity: parseFloat(e.target.value) || 1 })}
                  />
                </div>
                <div className="col-span-2">
                  <Input
                    placeholder="Unit"
                    value={componentForm.unit}
                    onChange={(e) => setComponentForm({ ...componentForm, unit: e.target.value })}
                  />
                </div>
                <div className="col-span-2">
                  <Input
                    type="number" placeholder="Waste %" min="0"
                    value={componentForm.waste_percentage}
                    onChange={(e) => setComponentForm({ ...componentForm, waste_percentage: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="col-span-1">
                  <Button onClick={addComponent} className="w-full" data-testid="add-component-btn">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {form.components.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-3 py-2 text-left">Component</th>
                        <th className="px-3 py-2 text-right">Qty</th>
                        <th className="px-3 py-2 text-center">Unit</th>
                        <th className="px-3 py-2 text-right">Waste %</th>
                        <th className="px-3 py-2"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {form.components.map((comp, idx) => (
                        <tr key={idx}>
                          <td className="px-3 py-2">{comp.item_name || comp.item_id}</td>
                          <td className="px-3 py-2 text-right">{comp.quantity}</td>
                          <td className="px-3 py-2 text-center">{comp.unit}</td>
                          <td className="px-3 py-2 text-right">{comp.waste_percentage}%</td>
                          <td className="px-3 py-2 text-right">
                            <Button size="sm" variant="ghost" onClick={() => removeComponent(idx)}>
                              <XCircle className="h-4 w-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCreateDialog(false); resetForm(); }}>Cancel</Button>
            <Button onClick={createCompositeItem} data-testid="submit-create-btn">Create Composite Item</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedItem && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {selectedItem.name}
                  <Badge className={typeColors[selectedItem.type] || ""}>{typeLabels[selectedItem.type]}</Badge>
                </DialogTitle>
                <DialogDescription>
                  SKU: {selectedItem.sku} | Created: {selectedItem.created_at?.split('T')[0]}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                {/* Quick Stats */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="p-3 bg-[#111820] rounded-lg text-center">
                    <p className="text-xs text-gray-500">Component Cost</p>
                    <p className="font-bold">{formatCurrency(selectedItem.current_component_cost || selectedItem.component_cost)}</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg text-center">
                    <p className="text-xs text-[#3B9EFF]">Selling Price</p>
                    <p className="font-bold text-[#3B9EFF]">{formatCurrency(selectedItem.selling_price)}</p>
                  </div>
                  <div className="p-3 bg-[rgba(34,197,94,0.08)] rounded-lg text-center">
                    <p className="text-xs text-green-600">Stock On Hand</p>
                    <p className="font-bold text-green-700">{selectedItem.stock_on_hand || 0}</p>
                  </div>
                  <div className="p-3 bg-[rgba(255,140,0,0.08)] rounded-lg text-center">
                    <p className="text-xs text-[#FF8C00]">Total Builds</p>
                    <p className="font-bold text-[#FF8C00]">{selectedItem.total_builds || 0}</p>
                  </div>
                </div>

                {/* Components */}
                <div>
                  <h4 className="font-semibold mb-2">Bill of Materials</h4>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-[#111820]">
                        <tr>
                          <th className="px-3 py-2 text-left">Component</th>
                          <th className="px-3 py-2 text-right">Qty Required</th>
                          <th className="px-3 py-2 text-right">In Stock</th>
                          <th className="px-3 py-2 text-right">Unit Cost</th>
                          <th className="px-3 py-2 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {(selectedItem.component_details || selectedItem.components || []).map((comp, idx) => (
                          <tr key={idx}>
                            <td className="px-3 py-2 font-medium">{comp.item_name || comp.item_id}</td>
                            <td className="px-3 py-2 text-right">{comp.quantity_required || comp.quantity}</td>
                            <td className="px-3 py-2 text-right">{comp.stock_available ?? "-"}</td>
                            <td className="px-3 py-2 text-right">{comp.unit_cost ? formatCurrency(comp.unit_cost) : "-"}</td>
                            <td className="px-3 py-2 text-center">
                              {comp.available !== undefined ? (
                                comp.available ?
                                  <CheckCircle className="h-4 w-4 text-green-500 mx-auto" /> :
                                  <AlertTriangle className="h-4 w-4 text-red-500 mx-auto" />
                              ) : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Recent Builds */}
                {selectedItem.recent_builds?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Recent Build History</h4>
                    <div className="space-y-2">
                      {selectedItem.recent_builds.map((build, idx) => (
                        <div key={idx} className="flex justify-between items-center p-2 bg-[#111820] rounded-lg text-sm">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{build.type === "build" ? "Built" : "Unbuilt"}</Badge>
                            <span>Qty: {build.quantity_built || build.quantity_unbuilt}</span>
                          </div>
                          <span className="text-gray-500 text-xs">{(build.built_at || build.unbuilt_at)?.split('T')[0]}</span>
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

      {/* Build Dialog */}
      <Dialog open={showBuildDialog} onOpenChange={setShowBuildDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Hammer className="h-5 w-5" /> Build {selectedItem?.name}
            </DialogTitle>
            <DialogDescription>Assemble from component items. Stock will be deducted from components.</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label>Build Quantity</Label>
              <Input
                type="number" min="1"
                value={buildQty}
                onChange={(e) => {
                  const q = parseInt(e.target.value) || 1;
                  setBuildQty(q);
                  checkAvailability(q);
                }}
                data-testid="build-quantity"
              />
            </div>

            <div>
              <Label>Notes (optional)</Label>
              <Input
                placeholder="Build notes"
                value={buildNotes}
                onChange={(e) => setBuildNotes(e.target.value)}
              />
            </div>

            {/* Availability Check */}
            {availability && (
              <div className={`p-4 rounded-lg border ${availability.can_build ? 'bg-[rgba(34,197,94,0.08)] border-green-200' : 'bg-[rgba(255,59,47,0.08)] border-red-200'}`}>
                <div className="flex items-center gap-2 mb-2">
                  {availability.can_build ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                  )}
                  <span className="font-medium">
                    {availability.can_build ? "Components available" : "Insufficient components"}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-1">Max buildable: {availability.max_buildable}</p>
                <p className="text-sm text-gray-600">Estimated cost: {formatCurrency(availability.estimated_cost)}</p>

                {availability.shortages?.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-sm font-medium text-red-600">Shortages:</p>
                    {availability.shortages.map((s, idx) => (
                      <p key={idx} className="text-xs text-red-500">
                        {s.item_name}: need {s.required}, have {s.available} (short {s.shortage})
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBuildDialog(false)}>Cancel</Button>
            <Button
              onClick={buildItem}
              disabled={availability && !availability.can_build}
              data-testid="confirm-build-btn"
            >
              <Hammer className="h-4 w-4 mr-2" /> Build {buildQty} Unit{buildQty > 1 ? 's' : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
