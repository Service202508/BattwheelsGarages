import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Plus, Search, Package, Edit, Trash2, AlertTriangle, Link as LinkIcon, ArrowUpDown } from "lucide-react";
import { API } from "@/App";

const categories = [
  { value: "battery", label: "Battery" },
  { value: "motor", label: "Motor" },
  { value: "charging_equipment", label: "Charging Equipment" },
  { value: "tools", label: "Tools" },
  { value: "consumables", label: "Consumables" },
];

export default function Inventory({ user }) {
  const [items, setItems] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    sku: "",
    category: "",
    quantity: 0,
    unit_price: 0,
    cost_price: 0,
    min_stock_level: 0,
    max_stock_level: 1000,
    reorder_quantity: 10,
    supplier_id: "",
    location: "",
  });

  useEffect(() => {
    fetchInventory();
    fetchSuppliers();
  }, []);

  const fetchInventory = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/inventory`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setItems(data);
      }
    } catch (error) {
      console.error("Failed to fetch inventory:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/suppliers`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setSuppliers(data);
      }
    } catch (error) {
      console.error("Failed to fetch suppliers:", error);
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.category) {
      toast.error("Name and category are required");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const url = editItem ? `${API}/inventory/${editItem.item_id}` : `${API}/inventory`;
      const method = editItem ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success(editItem ? "Item updated!" : "Item added!");
        fetchInventory();
        resetForm();
      } else {
        toast.error("Operation failed");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const handleDelete = async (itemId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/inventory/${itemId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include",
      });
      if (response.ok) {
        toast.success("Item deleted");
        fetchInventory();
      }
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      sku: "",
      category: "",
      quantity: 0,
      unit_price: 0,
      cost_price: 0,
      min_stock_level: 0,
      max_stock_level: 1000,
      reorder_quantity: 10,
      supplier_id: "",
      location: "",
    });
    setEditItem(null);
    setIsAddOpen(false);
  };

  const openEdit = (item) => {
    setEditItem(item);
    setFormData({
      name: item.name,
      sku: item.sku || "",
      category: item.category,
      quantity: item.quantity,
      unit_price: item.unit_price,
      cost_price: item.cost_price || 0,
      min_stock_level: item.min_stock_level,
      max_stock_level: item.max_stock_level || 1000,
      reorder_quantity: item.reorder_quantity || 10,
      supplier_id: item.supplier_id || "",
      location: item.location || "",
    });
    setIsAddOpen(true);
  };

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const lowStockItems = items.filter(item => item.quantity < item.min_stock_level);
  const totalValue = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  const totalCost = items.reduce((sum, item) => sum + (item.quantity * (item.cost_price || 0)), 0);

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="inventory-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Inventory Management</h1>
          <p className="text-muted-foreground mt-1">Track stock, allocate materials, manage suppliers.</p>
        </div>
        {(user?.role === "admin" || user?.role === "technician") && (
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button className="glow-primary" data-testid="add-item-btn">
                <Plus className="h-4 w-4 mr-2" />
                Add Item
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editItem ? "Edit Item" : "Add New Item"}</DialogTitle>
                <DialogDescription>
                  {editItem ? "Update inventory item details." : "Add a new item to the inventory."}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="bg-background/50"
                      data-testid="item-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>SKU</Label>
                    <Input
                      value={formData.sku}
                      onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                      className="bg-background/50"
                      placeholder="e.g., BAT-48V-001"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Category *</Label>
                    <Select
                      value={formData.category}
                      onValueChange={(value) => setFormData({ ...formData, category: value })}
                    >
                      <SelectTrigger className="bg-background/50" data-testid="item-category-select">
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((cat) => (
                          <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Supplier</Label>
                    <Select
                      value={formData.supplier_id}
                      onValueChange={(value) => setFormData({ ...formData, supplier_id: value })}
                    >
                      <SelectTrigger className="bg-background/50">
                        <SelectValue placeholder="Select supplier" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">None</SelectItem>
                        {suppliers.map((sup) => (
                          <SelectItem key={sup.supplier_id} value={sup.supplier_id}>{sup.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <Label>Quantity</Label>
                    <Input
                      type="number"
                      value={formData.quantity}
                      onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 0 })}
                      className="bg-background/50"
                      data-testid="item-quantity-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Cost Price (₹)</Label>
                    <Input
                      type="number"
                      value={formData.cost_price}
                      onChange={(e) => setFormData({ ...formData, cost_price: parseFloat(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Sale Price (₹)</Label>
                    <Input
                      type="number"
                      value={formData.unit_price}
                      onChange={(e) => setFormData({ ...formData, unit_price: parseFloat(e.target.value) || 0 })}
                      className="bg-background/50"
                      data-testid="item-price-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Location</Label>
                    <Input
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      className="bg-background/50"
                      placeholder="e.g., Warehouse A"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Min Stock</Label>
                    <Input
                      type="number"
                      value={formData.min_stock_level}
                      onChange={(e) => setFormData({ ...formData, min_stock_level: parseInt(e.target.value) || 0 })}
                      className="bg-background/50"
                      data-testid="item-min-stock-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Max Stock</Label>
                    <Input
                      type="number"
                      value={formData.max_stock_level}
                      onChange={(e) => setFormData({ ...formData, max_stock_level: parseInt(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Reorder Qty</Label>
                    <Input
                      type="number"
                      value={formData.reorder_quantity}
                      onChange={(e) => setFormData({ ...formData, reorder_quantity: parseInt(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm} className="border-white/10">
                  Cancel
                </Button>
                <Button onClick={handleSubmit} className="glow-primary" data-testid="save-item-btn">
                  {editItem ? "Update" : "Add Item"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Items</p>
            <p className="text-2xl font-bold mono">{items.length}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Inventory Value</p>
            <p className="text-2xl font-bold mono">₹{totalValue.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Cost Value</p>
            <p className="text-2xl font-bold mono">₹{totalCost.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className={`metric-card ${lowStockItems.length > 0 ? 'border-orange-500/30' : ''}`}>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Low Stock Items</p>
            <p className={`text-2xl font-bold mono ${lowStockItems.length > 0 ? 'text-orange-400' : ''}`}>
              {lowStockItems.length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <Card className="border-orange-500/30 bg-orange-500/10">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-orange-400" />
            <p className="text-sm text-orange-400">
              <span className="font-semibold">{lowStockItems.length} items</span> are below minimum stock level. Consider creating a purchase order.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name or SKU..."
              className="pl-10 bg-background/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="search-inventory-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Inventory Table */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading inventory...</div>
          ) : filteredItems.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No items found. Add your first inventory item to get started.
            </div>
          ) : (
            <Table className="data-table">
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>Item</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">In Stock</TableHead>
                  <TableHead className="text-right">Reserved</TableHead>
                  <TableHead className="text-right">Available</TableHead>
                  <TableHead className="text-right">Cost</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead>Supplier</TableHead>
                  <TableHead>Status</TableHead>
                  {(user?.role === "admin" || user?.role === "technician") && (
                    <TableHead className="text-right">Actions</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((item) => (
                  <TableRow key={item.item_id} className="border-white/10">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Package className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{item.name}</p>
                          <p className="text-xs text-muted-foreground">{item.location || 'No location'}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="mono text-sm">{item.sku || '-'}</TableCell>
                    <TableCell className="capitalize">{item.category.replace("_", " ")}</TableCell>
                    <TableCell className="text-right mono">{item.quantity}</TableCell>
                    <TableCell className="text-right mono text-muted-foreground">{item.reserved_quantity || 0}</TableCell>
                    <TableCell className="text-right mono font-semibold">
                      {item.quantity - (item.reserved_quantity || 0)}
                    </TableCell>
                    <TableCell className="text-right mono text-muted-foreground">₹{(item.cost_price || 0).toLocaleString()}</TableCell>
                    <TableCell className="text-right mono">₹{item.unit_price.toLocaleString()}</TableCell>
                    <TableCell className="text-sm">{item.supplier_name || '-'}</TableCell>
                    <TableCell>
                      {item.quantity < item.min_stock_level ? (
                        <Badge className="badge-danger" variant="outline">Low Stock</Badge>
                      ) : item.quantity > item.max_stock_level ? (
                        <Badge className="badge-warning" variant="outline">Overstocked</Badge>
                      ) : (
                        <Badge className="badge-success" variant="outline">In Stock</Badge>
                      )}
                    </TableCell>
                    {(user?.role === "admin" || user?.role === "technician") && (
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => openEdit(item)}
                            data-testid={`edit-item-${item.item_id}`}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          {user?.role === "admin" && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDelete(item.item_id)}
                              className="hover:text-destructive"
                              data-testid={`delete-item-${item.item_id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
