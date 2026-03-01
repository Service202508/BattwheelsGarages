import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Plus, Package, Wrench, Search, Edit, Trash2, Upload, Download, FileSpreadsheet, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { API } from "@/App";

const itemTypeColors = {
  goods: "bg-blue-100 text-bw-blue",
  service: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25",
  inventory: "bg-blue-100 text-bw-blue",
  sales: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25",
  sales_and_purchases: "bg-purple-100 text-bw-purple"
};

export default function Items() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [importing, setImporting] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const fileInputRef = useRef(null);

  const [newItem, setNewItem] = useState({
    name: "", sku: "", description: "", item_type: "goods",
    rate: 0, purchase_rate: 0, tax_percentage: 18,
    hsn_or_sac: "", unit: "pcs", stock_on_hand: 0, reorder_level: 10,
    is_taxable: true
  });

  useEffect(() => { fetchItems(); }, [search]);

  const fetchItems = async () => {
    try {
      const token = localStorage.getItem("token");
      let url = `${API}/zoho/items?per_page=500`;
      if (search) url += `&search_text=${encodeURIComponent(search)}`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setItems(data.items || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleExport = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/items/export?format=csv`, { headers: { Authorization: `Bearer ${token}` } });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'items_export.csv';
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Items exported successfully");
    } catch { toast.error("Failed to export items"); }
  };

  const handleDownloadTemplate = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/items/import-template`, { headers: { Authorization: `Bearer ${token}` } });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'items_import_template.csv';
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Template downloaded");
    } catch { toast.error("Failed to download template"); }
  };

  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportResult(null);
    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API}/zoho/items/bulk-import`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      setImportResult(data);
      if (data.summary?.created > 0 || data.summary?.updated > 0) {
        toast.success(data.message);
        fetchItems();
      } else if (data.summary?.errors > 0) {
        toast.error(`Import completed with ${data.summary.errors} errors`);
      }
    } catch (error) {
      toast.error("Failed to import items");
      setImportResult({ error: error.message });
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const isGoodsType = (type) => ["goods", "inventory", "sales_and_purchases"].includes(type);
  const isServiceType = (type) => ["service", "sales"].includes(type);
  const filteredItems = activeTab === "all" ? items : activeTab === "goods" ? items.filter(i => isGoodsType(i.item_type)) : items.filter(i => isServiceType(i.item_type));
  const goodsCount = items.filter(i => isGoodsType(i.item_type)).length;
  const servicesCount = items.filter(i => isServiceType(i.item_type)).length;

  const handleCreate = async () => {
    if (!newItem.name) return toast.error("Enter item name");
    if (newItem.rate <= 0) return toast.error("Enter valid rate");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newItem)
      });
      if (res.ok) {
        toast.success("Item created");
        setShowCreateDialog(false);
        setNewItem({ name: "", sku: "", description: "", item_type: "goods", rate: 0, purchase_rate: 0, tax_percentage: 18, hsn_or_sac: "", unit: "pcs", stock_on_hand: 0, reorder_level: 10, is_taxable: true });
        fetchItems();
      }
    } catch { toast.error("Error creating item"); }
  };

  const handleUpdate = async () => {
    if (!editItem) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/items/${editItem.item_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(editItem)
      });
      if (res.ok) {
        toast.success("Item updated");
        setEditItem(null);
        fetchItems();
      }
    } catch { toast.error("Error updating item"); }
  };

  const handleDelete = async (itemId) => {
    if (!confirm("Delete this item?")) return;
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/zoho/items/${itemId}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      toast.success("Item deleted");
      fetchItems();
    } catch { toast.error("Error deleting item"); }
  };

  return (
    <div className="space-y-6" data-testid="items-page">
      {/* Header with Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-bw-white">Items</h1>
          <p className="text-bw-white/[0.45] text-sm mt-1">Manage products and services</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" onClick={handleDownloadTemplate} data-testid="download-template-btn">
            <FileSpreadsheet className="h-4 w-4 mr-2" /> Template
          </Button>
          <Button variant="outline" onClick={handleExport} data-testid="export-items-btn">
            <Download className="h-4 w-4 mr-2" /> Export
          </Button>
          <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" data-testid="import-items-btn">
                <Upload className="h-4 w-4 mr-2" /> Import
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-xl">
              <DialogHeader><DialogTitle>Bulk Import Items</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div className="border-2 border-dashed rounded-lg p-6 text-center bg-bw-panel">
                  <Upload className="h-10 w-10 mx-auto mb-3 text-bw-white/[0.45]" />
                  <p className="text-sm text-bw-white/35 mb-2">Upload a CSV file with your items</p>
                  <p className="text-xs text-bw-white/[0.45] mb-4">Columns: name, sku, description, rate, purchase_rate, item_type, unit, hsn_or_sac, tax_percentage, stock_on_hand, reorder_level</p>
                  <input ref={fileInputRef} type="file" accept=".csv" onChange={handleImport} className="hidden" id="import-file" />
                  <div className="flex gap-2 justify-center">
                    <Button onClick={() => fileInputRef.current?.click()} disabled={importing} className="bg-bw-volt text-bw-black font-bold">
                      {importing ? "Importing..." : "Select CSV File"}
                    </Button>
                    <Button variant="outline" onClick={handleDownloadTemplate}><Download className="h-4 w-4 mr-1" /> Get Template</Button>
                  </div>
                </div>
                {importResult && (
                  <div className="space-y-3">
                    {importResult.summary && (
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-bw-green/[0.08] border border-green-200 rounded-lg p-3 text-center">
                          <CheckCircle className="h-5 w-5 text-green-600 mx-auto mb-1" />
                          <p className="text-lg font-bold text-green-700">{importResult.summary.created}</p>
                          <p className="text-xs text-green-600">Created</p>
                        </div>
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                          <AlertCircle className="h-5 w-5 text-bw-blue mx-auto mb-1" />
                          <p className="text-lg font-bold text-bw-blue">{importResult.summary.updated}</p>
                          <p className="text-xs text-bw-blue">Updated</p>
                        </div>
                        <div className="bg-bw-red/[0.08] border border-red-200 rounded-lg p-3 text-center">
                          <XCircle className="h-5 w-5 text-red-600 mx-auto mb-1" />
                          <p className="text-lg font-bold text-red-700">{importResult.summary.errors}</p>
                          <p className="text-xs text-red-600">Errors</p>
                        </div>
                      </div>
                    )}
                    {importResult.errors?.length > 0 && (
                      <div className="bg-bw-red/[0.08] border border-red-200 rounded-lg p-3 max-h-40 overflow-y-auto">
                        <p className="text-sm font-medium text-red-700 mb-2">Errors:</p>
                        {importResult.errors.map((err, idx) => (
                          <p key={idx} className="text-xs text-red-600">Row {err.row}: {err.error}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="flex justify-end">
                <Button variant="outline" onClick={() => { setShowImportDialog(false); setImportResult(null); }}>Close</Button>
              </div>
            </DialogContent>
          </Dialog>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold" data-testid="create-item-btn">
                <Plus className="h-4 w-4 mr-2" /> New Item
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
                        <SelectItem value="goods">Goods</SelectItem>
                        <SelectItem value="service">Service</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Name *</Label>
                    <Input value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} placeholder="Item name" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div><Label>SKU</Label><Input value={newItem.sku} onChange={(e) => setNewItem({ ...newItem, sku: e.target.value })} placeholder="SKU code" /></div>
                  <div><Label>HSN/SAC</Label><Input value={newItem.hsn_or_sac} onChange={(e) => setNewItem({ ...newItem, hsn_or_sac: e.target.value })} placeholder="HSN/SAC code" /></div>
                  <div>
                    <Label>Unit</Label>
                    <Select value={newItem.unit} onValueChange={(v) => setNewItem({ ...newItem, unit: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pcs">Pieces</SelectItem>
                        <SelectItem value="nos">Numbers</SelectItem>
                        <SelectItem value="hrs">Hours</SelectItem>
                        <SelectItem value="kg">Kilograms</SelectItem>
                        <SelectItem value="ltr">Liters</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div><Label>Description</Label><Textarea value={newItem.description} onChange={(e) => setNewItem({ ...newItem, description: e.target.value })} placeholder="Item description" /></div>
                <div className="grid grid-cols-3 gap-4">
                  <div><Label>Selling Rate *</Label><Input type="number" value={newItem.rate} onChange={(e) => setNewItem({ ...newItem, rate: parseFloat(e.target.value) })} /></div>
                  <div><Label>Purchase Rate</Label><Input type="number" value={newItem.purchase_rate} onChange={(e) => setNewItem({ ...newItem, purchase_rate: parseFloat(e.target.value) })} /></div>
                  <div><Label>Tax %</Label><Input type="number" value={newItem.tax_percentage} onChange={(e) => setNewItem({ ...newItem, tax_percentage: parseFloat(e.target.value) })} /></div>
                </div>
                {newItem.item_type === "goods" && (
                  <div className="grid grid-cols-2 gap-4">
                    <div><Label>Opening Stock</Label><Input type="number" value={newItem.stock_on_hand} onChange={(e) => setNewItem({ ...newItem, stock_on_hand: parseInt(e.target.value) })} /></div>
                    <div><Label>Reorder Level</Label><Input type="number" value={newItem.reorder_level} onChange={(e) => setNewItem({ ...newItem, reorder_level: parseInt(e.target.value) })} /></div>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Switch checked={newItem.is_taxable} onCheckedChange={(v) => setNewItem({ ...newItem, is_taxable: v })} />
                  <Label>Taxable Item</Label>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                <Button onClick={handleCreate} className="bg-bw-volt text-bw-black font-bold">Create Item</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><CardContent className="pt-6"><div className="flex items-center justify-between"><div><p className="text-sm text-bw-white/[0.45]">Total Items</p><p className="text-2xl font-bold">{items.length}</p></div><Package className="h-8 w-8 text-bw-volt" /></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center justify-between"><div><p className="text-sm text-bw-white/[0.45]">Goods</p><p className="text-2xl font-bold">{goodsCount}</p></div><Package className="h-8 w-8 text-blue-500" /></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center justify-between"><div><p className="text-sm text-bw-white/[0.45]">Services</p><p className="text-2xl font-bold">{servicesCount}</p></div><Wrench className="h-8 w-8 text-green-500" /></div></CardContent></Card>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-bw-white/[0.45]" />
        <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search items..." className="pl-10 max-w-md" />
      </div>

      {/* Tabs and Table */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All Items</TabsTrigger>
          <TabsTrigger value="goods">Goods</TabsTrigger>
          <TabsTrigger value="service">Services</TabsTrigger>
        </TabsList>
        <TabsContent value={activeTab} className="mt-6">
          {loading ? <div className="text-center py-12 text-bw-white/[0.45]">Loading...</div> :
            filteredItems.length === 0 ? (
              <Card><CardContent className="py-12 text-center text-bw-white/[0.45]"><Package className="h-12 w-12 mx-auto mb-4 text-bw-white/20" /><p>No items found</p></CardContent></Card>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-bw-panel">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium">Item</th>
                      <th className="px-4 py-3 text-left font-medium">SKU</th>
                      <th className="px-4 py-3 text-left font-medium">Type</th>
                      <th className="px-4 py-3 text-right font-medium">Rate</th>
                      <th className="px-4 py-3 text-right font-medium">Stock</th>
                      <th className="px-4 py-3 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredItems.map(item => (
                      <tr key={item.item_id} className="border-t hover:bg-bw-panel">
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium">{item.name}</p>
                            {item.description && <p className="text-xs text-bw-white/[0.45] truncate max-w-xs">{item.description}</p>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-bw-white/35">{item.sku || '-'}</td>
                        <td className="px-4 py-3"><Badge className={itemTypeColors[item.item_type] || "bg-bw-white/5 text-bw-white/35 border border-white/[0.08]"}>{item.item_type}</Badge></td>
                        <td className="px-4 py-3 text-right font-medium">₹{item.rate?.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 text-right">
                          {isGoodsType(item.item_type) ? (
                            <span className={item.stock_on_hand <= (item.reorder_level || 0) ? "text-red-600 font-medium" : ""}>{item.stock_on_hand || 0}</span>
                          ) : '-'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-1">
                            <Button size="icon" variant="ghost" onClick={() => setEditItem(item)}><Edit className="h-4 w-4" /></Button>
                            <Button size="icon" variant="ghost" onClick={() => handleDelete(item.item_id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
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
                      <SelectItem value="goods">Goods</SelectItem>
                      <SelectItem value="service">Service</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Name *</Label><Input value={editItem.name} onChange={(e) => setEditItem({ ...editItem, name: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>SKU</Label><Input value={editItem.sku || ""} onChange={(e) => setEditItem({ ...editItem, sku: e.target.value })} /></div>
                <div><Label>HSN/SAC</Label><Input value={editItem.hsn_or_sac || ""} onChange={(e) => setEditItem({ ...editItem, hsn_or_sac: e.target.value })} /></div>
                <div><Label>Unit</Label><Input value={editItem.unit || ""} onChange={(e) => setEditItem({ ...editItem, unit: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>Selling Rate</Label><Input type="number" value={editItem.rate || 0} onChange={(e) => setEditItem({ ...editItem, rate: parseFloat(e.target.value) })} /></div>
                <div><Label>Purchase Rate</Label><Input type="number" value={editItem.purchase_rate || 0} onChange={(e) => setEditItem({ ...editItem, purchase_rate: parseFloat(e.target.value) })} /></div>
                <div><Label>Tax %</Label><Input type="number" value={editItem.tax_percentage || 0} onChange={(e) => setEditItem({ ...editItem, tax_percentage: parseFloat(e.target.value) })} /></div>
              </div>
              {isGoodsType(editItem.item_type) && (
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>Stock on Hand</Label><Input type="number" value={editItem.stock_on_hand || 0} onChange={(e) => setEditItem({ ...editItem, stock_on_hand: parseInt(e.target.value) })} /></div>
                  <div><Label>Reorder Level</Label><Input type="number" value={editItem.reorder_level || 0} onChange={(e) => setEditItem({ ...editItem, reorder_level: parseInt(e.target.value) })} /></div>
                </div>
              )}
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setEditItem(null)}>Cancel</Button>
            <Button onClick={handleUpdate} className="bg-bw-volt text-bw-black font-bold">Update Item</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
