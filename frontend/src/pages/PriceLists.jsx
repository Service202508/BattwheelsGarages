import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Plus, List, IndianRupee, Edit, Trash2, Tag, Package, 
  Download, Upload, RefreshCw, Search, ChevronDown, ChevronUp,
  Percent, Loader2, FileSpreadsheet, CheckCircle, AlertTriangle,
  Eye, MoreHorizontal
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  active: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  inactive: "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.35)]",
  deleted: "bg-red-100 text-red-600"
};

export default function PriceLists() {
  const [priceLists, setPriceLists] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedPriceLists, setExpandedPriceLists] = useState({});
  
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showAddItemDialog, setShowAddItemDialog] = useState(false);
  const [showBulkAddDialog, setShowBulkAddDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  
  const [selectedPriceList, setSelectedPriceList] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Form states
  const [newPriceList, setNewPriceList] = useState({
    price_list_name: "", description: "", currency_code: "INR",
    price_type: "sales", is_default: false, round_off_to: "never",
    percentage_type: "", percentage_value: 0
  });
  
  const [newPriceItem, setNewPriceItem] = useState({ 
    item_id: "", pricelist_rate: 0, discount: 0, discount_type: "percentage" 
  });
  
  // Bulk add state
  const [bulkAddItems, setBulkAddItems] = useState([]);
  const [bulkPercentageType, setBulkPercentageType] = useState("none");
  const [bulkPercentageValue, setBulkPercentageValue] = useState(0);
  
  // Import state
  const [importCsvData, setImportCsvData] = useState("");
  const [importing, setImporting] = useState(false);
  
  // Processing states
  const [syncing, setSyncing] = useState(false);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return { 
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    };
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const [plRes, itemsRes] = await Promise.all([
        fetch(`${API}/zoho/price-lists?include_items=true`, { headers }),
        fetch(`${API}/zoho/items?per_page=500`, { headers })
      ]);
      const [plData, itemsData] = await Promise.all([plRes.json(), itemsRes.json()]);
      setPriceLists(plData.price_lists || []);
      setItems(itemsData.items || []);
    } catch (error) { 
      console.error("Failed to fetch:", error);
      toast.error("Failed to load data");
    } finally { 
      setLoading(false); 
    }
  }, [getAuthHeaders]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    if (!newPriceList.price_list_name) return toast.error("Enter price list name");
    try {
      const res = await fetch(`${API}/zoho/price-lists`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(newPriceList)
      });
      if (res.ok) {
        toast.success("Price list created");
        setShowCreateDialog(false);
        setNewPriceList({ price_list_name: "", description: "", currency_code: "INR", price_type: "sales", is_default: false, round_off_to: "never", percentage_type: "", percentage_value: 0 });
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create price list");
      }
    } catch { toast.error("Error creating price list"); }
  };

  const handleUpdate = async () => {
    if (!selectedPriceList) return;
    const plId = selectedPriceList?.price_list_id || selectedPriceList?.pricelist_id;
    try {
      const res = await fetch(`${API}/zoho/price-lists/${plId}`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify(newPriceList)
      });
      if (res.ok) {
        toast.success("Price list updated");
        setShowEditDialog(false);
        fetchData();
      }
    } catch { toast.error("Error updating price list"); }
  };

  const handleDelete = async (plId) => {
    if (!confirm("Are you sure you want to delete this price list?")) return;
    try {
      const res = await fetch(`${API}/zoho/price-lists/${plId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        toast.success("Price list deleted");
        fetchData();
      }
    } catch { toast.error("Error deleting price list"); }
  };

  const handleAddItem = async () => {
    if (!newPriceItem.item_id || newPriceItem.pricelist_rate < 0) return toast.error("Select item and enter rate");
    const plId = selectedPriceList?.price_list_id || selectedPriceList?.pricelist_id;
    try {
      const res = await fetch(
        `${API}/zoho/price-lists/${plId}/items?item_id=${newPriceItem.item_id}&pricelist_rate=${newPriceItem.pricelist_rate}&discount=${newPriceItem.discount}&discount_type=${newPriceItem.discount_type}`,
        { method: "POST", headers: getAuthHeaders() }
      );
      if (res.ok) {
        toast.success("Item added to price list");
        setShowAddItemDialog(false);
        setNewPriceItem({ item_id: "", pricelist_rate: 0, discount: 0, discount_type: "percentage" });
        fetchData();
      }
    } catch { toast.error("Error adding item"); }
  };

  const handleUpdateItem = async (plId, itemId, rate, discount) => {
    try {
      const res = await fetch(
        `${API}/zoho/price-lists/${plId}/items/${itemId}?pricelist_rate=${rate}&discount=${discount}`,
        { method: "PUT", headers: getAuthHeaders() }
      );
      if (res.ok) {
        toast.success("Item updated");
        fetchData();
      }
    } catch { toast.error("Error updating item"); }
  };

  const handleRemoveItem = async (priceListId, itemId) => {
    try {
      await fetch(`${API}/zoho/price-lists/${priceListId}/items/${itemId}`, {
        method: "DELETE", headers: getAuthHeaders()
      });
      toast.success("Item removed from price list");
      fetchData();
    } catch { toast.error("Error removing item"); }
  };

  const handleBulkAdd = async () => {
    if (bulkAddItems.length === 0) return toast.error("Select at least one item");
    const plId = selectedPriceList?.price_list_id || selectedPriceList?.pricelist_id;
    try {
      const res = await fetch(`${API}/zoho/price-lists/${plId}/bulk-add`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          item_ids: bulkAddItems,
          percentage_type: bulkPercentageType,
          percentage_value: bulkPercentageValue
        })
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Added ${data.count} items`);
        setShowBulkAddDialog(false);
        setBulkAddItems([]);
        setBulkPercentageType("none");
        setBulkPercentageValue(0);
        fetchData();
      }
    } catch { toast.error("Error adding items"); }
  };

  const handleExport = async (plId) => {
    try {
      window.open(`${API}/zoho/price-lists/${plId}/export`, '_blank');
      toast.success("Download started");
    } catch { toast.error("Error exporting"); }
  };

  const handleImport = async () => {
    if (!importCsvData.trim()) return toast.error("Paste CSV data");
    const plId = selectedPriceList?.price_list_id || selectedPriceList?.pricelist_id;
    setImporting(true);
    try {
      const res = await fetch(`${API}/zoho/price-lists/${plId}/import`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ csv_data: importCsvData })
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Imported ${data.imported_count} items`);
        if (data.errors?.length > 0) {
          toast.warning(`${data.errors.length} errors occurred`);
        }
        setShowImportDialog(false);
        setImportCsvData("");
        fetchData();
      }
    } catch { toast.error("Error importing"); }
    finally { setImporting(false); }
  };

  const handleSync = async (plId) => {
    setSyncing(true);
    try {
      const res = await fetch(`${API}/zoho/price-lists/${plId}/sync-items`, {
        method: "POST",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Synced ${data.synced_count} items`);
        fetchData();
      }
    } catch { toast.error("Error syncing"); }
    finally { setSyncing(false); }
  };

  const toggleExpand = (plId) => {
    setExpandedPriceLists(prev => ({ ...prev, [plId]: !prev[plId] }));
  };

  const openEditDialog = (pl) => {
    setSelectedPriceList(pl);
    setNewPriceList({
      price_list_name: pl.price_list_name || pl.name || "",
      description: pl.description || "",
      currency_code: pl.currency_code || "INR",
      price_type: pl.price_type || "sales",
      is_default: pl.is_default || false,
      round_off_to: pl.round_off_to || "never",
      percentage_type: pl.percentage_type || "",
      percentage_value: pl.percentage_value || 0
    });
    setShowEditDialog(true);
  };

  const filteredItems = items.filter(item => 
    !searchQuery || 
    item.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.sku?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatCurrency = (amount) => `₹${(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  return (
    <div className="space-y-6" data-testid="price-lists-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Price Lists</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Manage custom pricing for items (Zoho Books compatible)</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-pricelist-btn">
                <Plus className="h-4 w-4 mr-2" /> New Price List
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Create Price List</DialogTitle>
                <DialogDescription>Create a new price list for custom item pricing</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>Price List Name *</Label>
                  <Input value={newPriceList.price_list_name} onChange={(e) => setNewPriceList({ ...newPriceList, price_list_name: e.target.value })} placeholder="e.g., Wholesale Prices" data-testid="pricelist-name-input" />
                </div>
                <div>
                  <Label>Description</Label>
                  <Textarea value={newPriceList.description} onChange={(e) => setNewPriceList({ ...newPriceList, description: e.target.value })} placeholder="Optional description" rows={2} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Price Type</Label>
                    <Select value={newPriceList.price_type} onValueChange={(v) => setNewPriceList({ ...newPriceList, price_type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sales">Sales</SelectItem>
                        <SelectItem value="purchase">Purchase</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Round Off To</Label>
                    <Select value={newPriceList.round_off_to} onValueChange={(v) => setNewPriceList({ ...newPriceList, round_off_to: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="never">Never</SelectItem>
                        <SelectItem value="nearest_1">Nearest ₹1</SelectItem>
                        <SelectItem value="nearest_5">Nearest ₹5</SelectItem>
                        <SelectItem value="nearest_10">Nearest ₹10</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Default Percentage Type</Label>
                    <Select value={newPriceList.percentage_type || "none"} onValueChange={(v) => setNewPriceList({ ...newPriceList, percentage_type: v === "none" ? "" : v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="markup_percentage">Markup %</SelectItem>
                        <SelectItem value="markdown_percentage">Markdown %</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Percentage Value</Label>
                    <Input type="number" value={newPriceList.percentage_value} onChange={(e) => setNewPriceList({ ...newPriceList, percentage_value: parseFloat(e.target.value) || 0 })} />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={newPriceList.is_default} onCheckedChange={(v) => setNewPriceList({ ...newPriceList, is_default: v })} />
                  <Label>Set as default price list</Label>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                <Button onClick={handleCreate} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="submit-pricelist-btn">Create Price List</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Price Lists */}
      {loading ? (
        <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
          Loading price lists...
        </div>
      ) : priceLists.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
            <List className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
            <p>No price lists found</p>
            <p className="text-sm mt-1">Create a price list to set custom pricing for different customers</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {priceLists.map(pl => (
            <Card key={pl.price_list_id || pl.pricelist_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors" data-testid={`pricelist-${pl.price_list_id || pl.pricelist_id}`}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 cursor-pointer" onClick={() => toggleExpand(pl.price_list_id || pl.pricelist_id)}>
                    <div className="p-2 bg-[#C8FF00]/10 rounded-lg">
                      <List className="h-5 w-5 text-[#C8FF00]" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-lg">{pl.price_list_name || pl.name}</CardTitle>
                        {expandedPriceLists[pl.price_list_id || pl.pricelist_id] ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </div>
                      {pl.description && <p className="text-sm text-[rgba(244,246,240,0.45)]">{pl.description}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="capitalize">{pl.price_type || 'sales'}</Badge>
                    {pl.is_default && <Badge className="bg-blue-100 text-[#3B9EFF]">Default</Badge>}
                    <Badge variant="outline">{pl.item_count || pl.items?.length || 0} items</Badge>
                    
                    {/* Actions */}
                    <Button size="sm" variant="outline" onClick={() => { setSelectedPriceList(pl); setShowAddItemDialog(true); }} data-testid={`add-item-${pl.price_list_id || pl.pricelist_id}`}>
                      <Plus className="h-4 w-4 mr-1" /> Add Item
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => { setSelectedPriceList(pl); setShowBulkAddDialog(true); }}>
                      <Package className="h-4 w-4 mr-1" /> Bulk Add
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleExport(pl.price_list_id || pl.pricelist_id)} data-testid={`export-${pl.price_list_id || pl.pricelist_id}`}>
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => { setSelectedPriceList(pl); setShowImportDialog(true); }}>
                      <Upload className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleSync(pl.price_list_id || pl.pricelist_id)} disabled={syncing}>
                      <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => openEditDialog(pl)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => handleDelete(pl.price_list_id || pl.pricelist_id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              {/* Expanded Items Table - Zoho Books Format */}
              {expandedPriceLists[pl.price_list_id || pl.pricelist_id] && (
                <CardContent>
                  {pl.items?.length > 0 ? (
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-[#111820]">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium">Item ID</th>
                            <th className="px-4 py-2 text-left font-medium">Item Name</th>
                            <th className="px-4 py-2 text-left font-medium">SKU</th>
                            <th className="px-4 py-2 text-center font-medium">Status</th>
                            <th className="px-4 py-2 text-center font-medium">Combo</th>
                            <th className="px-4 py-2 text-right font-medium">Item Price</th>
                            <th className="px-4 py-2 text-right font-medium">PriceList Rate</th>
                            <th className="px-4 py-2 text-right font-medium">Discount</th>
                            <th className="px-4 py-2 text-right font-medium">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {pl.items.map(item => (
                            <tr key={item.item_id} className="border-t hover:bg-[#111820]">
                              <td className="px-4 py-2 font-mono text-xs text-[rgba(244,246,240,0.45)]">{item.item_id}</td>
                              <td className="px-4 py-2">
                                <div className="flex items-center gap-2">
                                  <Package className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                                  <span>{item.item_name || item.synced_item_name || 'Unknown'}</span>
                                </div>
                              </td>
                              <td className="px-4 py-2 text-[rgba(244,246,240,0.35)]">{item.sku || item.synced_sku || '-'}</td>
                              <td className="px-4 py-2 text-center">
                                <Badge className={statusColors[item.item_status || item.synced_status || 'active']}>
                                  {item.item_status || item.synced_status || 'active'}
                                </Badge>
                              </td>
                              <td className="px-4 py-2 text-center">
                                {(item.is_combo_product || item.synced_is_combo) ? 
                                  <CheckCircle className="h-4 w-4 text-green-500 mx-auto" /> : 
                                  <span className="text-[rgba(244,246,240,0.20)]">-</span>
                                }
                              </td>
                              <td className="px-4 py-2 text-right text-[rgba(244,246,240,0.45)]">
                                {formatCurrency(item.item_price || item.synced_item_price || 0)}
                              </td>
                              <td className="px-4 py-2 text-right font-medium text-[#C8FF00]">
                                {formatCurrency(item.pricelist_rate || item.custom_rate || 0)}
                              </td>
                              <td className="px-4 py-2 text-right">
                                {item.discount > 0 ? (
                                  <Badge variant="outline" className="bg-[rgba(255,140,0,0.08)] text-[#FF8C00]">
                                    {item.discount}%
                                  </Badge>
                                ) : '-'}
                              </td>
                              <td className="px-4 py-2 text-right">
                                <Button size="icon" variant="ghost" onClick={() => handleRemoveItem(pl.price_list_id, item.item_id)}>
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-6 text-[rgba(244,246,240,0.45)] text-sm border rounded-lg border-dashed">
                      No items added to this price list yet
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Add Item Dialog */}
      <Dialog open={showAddItemDialog} onOpenChange={setShowAddItemDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add Item to Price List</DialogTitle>
            <DialogDescription>Add an item with custom pricing to "{selectedPriceList?.price_list_name}"</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
              <Input 
                placeholder="Search items..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div>
              <Label>Select Item *</Label>
              <Select value={newPriceItem.item_id} onValueChange={(v) => {
                const item = items.find(i => i.item_id === v);
                setNewPriceItem({ ...newPriceItem, item_id: v, pricelist_rate: item?.rate || 0 });
              }}>
                <SelectTrigger data-testid="item-select"><SelectValue placeholder="Choose an item" /></SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  {filteredItems.map(item => (
                    <SelectItem key={item.item_id} value={item.item_id}>
                      <div className="flex justify-between w-full gap-4">
                        <span>{item.name}</span>
                        <span className="text-[rgba(244,246,240,0.45)]">{formatCurrency(item.rate)}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>PriceList Rate *</Label>
                <Input 
                  type="number" 
                  value={newPriceItem.pricelist_rate} 
                  onChange={(e) => setNewPriceItem({ ...newPriceItem, pricelist_rate: parseFloat(e.target.value) || 0 })} 
                  data-testid="pricelist-rate-input"
                />
              </div>
              <div>
                <Label>Discount %</Label>
                <Input 
                  type="number" 
                  value={newPriceItem.discount} 
                  onChange={(e) => setNewPriceItem({ ...newPriceItem, discount: parseFloat(e.target.value) || 0 })}
                  min={0}
                  max={100}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddItemDialog(false)}>Cancel</Button>
            <Button onClick={handleAddItem} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="add-item-submit">Add Item</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Add Dialog */}
      <Dialog open={showBulkAddDialog} onOpenChange={setShowBulkAddDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Bulk Add Items</DialogTitle>
            <DialogDescription>Select multiple items to add to "{selectedPriceList?.price_list_name}" with optional markup/markdown</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Pricing Adjustment</Label>
                <Select value={bulkPercentageType} onValueChange={setBulkPercentageType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Use Original Price</SelectItem>
                    <SelectItem value="markup_percentage">Markup %</SelectItem>
                    <SelectItem value="markdown_percentage">Markdown %</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {bulkPercentageType !== "none" && (
                <div>
                  <Label>Percentage Value</Label>
                  <Input 
                    type="number" 
                    value={bulkPercentageValue} 
                    onChange={(e) => setBulkPercentageValue(parseFloat(e.target.value) || 0)}
                    min={0}
                    max={100}
                  />
                </div>
              )}
            </div>
            
            <Separator />
            
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
              <Input 
                placeholder="Search items..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="border rounded-lg max-h-[300px] overflow-y-auto">
              {filteredItems.map(item => (
                <div key={item.item_id} className="flex items-center gap-3 p-3 hover:bg-[#111820] border-b last:border-b-0">
                  <Checkbox 
                    checked={bulkAddItems.includes(item.item_id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setBulkAddItems([...bulkAddItems, item.item_id]);
                      } else {
                        setBulkAddItems(bulkAddItems.filter(id => id !== item.item_id));
                      }
                    }}
                  />
                  <div className="flex-1">
                    <div className="font-medium">{item.name}</div>
                    <div className="text-xs text-[rgba(244,246,240,0.45)]">{item.sku || item.item_id}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(item.rate)}</div>
                    {bulkPercentageType !== "none" && bulkPercentageValue > 0 && (
                      <div className="text-xs text-[#C8FF00]">
                        → {formatCurrency(
                          bulkPercentageType === "markup_percentage" 
                            ? item.rate * (1 + bulkPercentageValue / 100)
                            : item.rate * (1 - bulkPercentageValue / 100)
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="text-sm text-[rgba(244,246,240,0.45)]">
              {bulkAddItems.length} items selected
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowBulkAddDialog(false); setBulkAddItems([]); }}>Cancel</Button>
            <Button onClick={handleBulkAdd} className="bg-[#C8FF00] text-[#080C0F] font-bold" disabled={bulkAddItems.length === 0}>
              Add {bulkAddItems.length} Items
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Import Items from CSV</DialogTitle>
            <DialogDescription>
              Import items to "{selectedPriceList?.price_list_name}" using Zoho Books CSV format
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-3 bg-[#111820] rounded-lg text-xs font-mono">
              <p className="font-semibold mb-1">Expected CSV Format:</p>
              <p>Item ID,Item Name,SKU,Status,is_combo_product,Item Price,PriceList Rate,Discount</p>
            </div>
            <div>
              <Label>Paste CSV Data</Label>
              <Textarea 
                rows={10}
                value={importCsvData}
                onChange={(e) => setImportCsvData(e.target.value)}
                placeholder="Item ID,Item Name,SKU,Status,is_combo_product,Item Price,PriceList Rate,Discount&#10;ITEM-001,Sample Product,SKU001,active,false,1000,900,10"
                className="font-mono text-xs"
                data-testid="import-csv-textarea"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowImportDialog(false); setImportCsvData(""); }}>Cancel</Button>
            <Button onClick={handleImport} className="bg-[#C8FF00] text-[#080C0F] font-bold" disabled={importing} data-testid="import-submit-btn">
              {importing ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Importing...</> : <><Upload className="h-4 w-4 mr-2" />Import</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Price List Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Price List</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Price List Name *</Label>
              <Input value={newPriceList.price_list_name} onChange={(e) => setNewPriceList({ ...newPriceList, price_list_name: e.target.value })} />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={newPriceList.description} onChange={(e) => setNewPriceList({ ...newPriceList, description: e.target.value })} rows={2} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Price Type</Label>
                <Select value={newPriceList.price_type} onValueChange={(v) => setNewPriceList({ ...newPriceList, price_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sales">Sales</SelectItem>
                    <SelectItem value="purchase">Purchase</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Round Off To</Label>
                <Select value={newPriceList.round_off_to} onValueChange={(v) => setNewPriceList({ ...newPriceList, round_off_to: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="never">Never</SelectItem>
                    <SelectItem value="nearest_1">Nearest ₹1</SelectItem>
                    <SelectItem value="nearest_5">Nearest ₹5</SelectItem>
                    <SelectItem value="nearest_10">Nearest ₹10</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={newPriceList.is_default} onCheckedChange={(v) => setNewPriceList({ ...newPriceList, is_default: v })} />
              <Label>Set as default price list</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
            <Button onClick={handleUpdate} className="bg-[#C8FF00] text-[#080C0F] font-bold">Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
