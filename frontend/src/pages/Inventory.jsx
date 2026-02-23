import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Search, Plus, Wrench, Package, IndianRupee, Edit, 
  AlertTriangle, CheckCircle, Tag, FileText
} from "lucide-react";
import { API } from "@/App";

export default function Inventory() {
  const [services, setServices] = useState([]);
  const [parts, setParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("services");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [totals, setTotals] = useState({ services: 0, parts: 0 });

  const [newItem, setNewItem] = useState({
    name: "",
    sku: "",
    hsn_sac: "",
    rate: 0,
    description: "",
    tax_rate: 18,
    stock_quantity: 0,
    reorder_level: 5
  });

  useEffect(() => {
    fetchData();
  }, [search]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };

      const [srvRes, prtRes] = await Promise.all([
        fetch(`${API}/books/services?search=${search}&limit=200`, { headers }),
        fetch(`${API}/books/parts?search=${search}&limit=200`, { headers })
      ]);

      const [srvData, prtData] = await Promise.all([
        srvRes.json(),
        prtRes.json()
      ]);

      setServices(srvData.items || []);
      setParts(prtData.items || []);
      setTotals({
        services: srvData.total || 0,
        parts: prtData.total || 0
      });
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = async () => {
    if (!newItem.name) {
      toast.error("Item name is required");
      return;
    }

    const endpoint = activeTab === "services" ? "/books/services" : "/books/parts";
    const payload = {
      ...newItem,
      type: activeTab === "services" ? "service" : "goods"
    };

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        toast.success(`${activeTab === "services" ? "Service" : "Part"} added successfully`);
        setShowAddDialog(false);
        setNewItem({
          name: "", sku: "", hsn_sac: "", rate: 0, description: "",
          tax_rate: 18, stock_quantity: 0, reorder_level: 5
        });
        fetchData();
      } else {
        toast.error("Failed to add item");
      }
    } catch (error) {
      toast.error("Error adding item");
    }
  };

  const lowStockParts = parts.filter(p => (p.stock_quantity || 0) <= (p.reorder_level || 5));

  return (
    <div className="space-y-6" data-testid="inventory-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Inventory</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">
            {totals.services} services, {totals.parts} parts
          </p>
        </div>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="add-item-btn">
              <Plus className="h-4 w-4 mr-2" />
              Add {activeTab === "services" ? "Service" : "Part"}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Add New {activeTab === "services" ? "Service" : "Part"}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>Name *</Label>
                <Input
                  value={newItem.name}
                  onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                  placeholder="Item name"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>SKU</Label>
                  <Input
                    value={newItem.sku}
                    onChange={(e) => setNewItem({...newItem, sku: e.target.value})}
                    placeholder="SKU code"
                  />
                </div>
                <div>
                  <Label>HSN/SAC</Label>
                  <Input
                    value={newItem.hsn_sac}
                    onChange={(e) => setNewItem({...newItem, hsn_sac: e.target.value})}
                    placeholder="HSN/SAC code"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Rate (₹)</Label>
                  <Input
                    type="number"
                    value={newItem.rate}
                    onChange={(e) => setNewItem({...newItem, rate: parseFloat(e.target.value)})}
                  />
                </div>
                <div>
                  <Label>Tax Rate (%)</Label>
                  <Input
                    type="number"
                    value={newItem.tax_rate}
                    onChange={(e) => setNewItem({...newItem, tax_rate: parseFloat(e.target.value)})}
                  />
                </div>
              </div>
              {activeTab === "parts" && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Stock Quantity</Label>
                    <Input
                      type="number"
                      value={newItem.stock_quantity}
                      onChange={(e) => setNewItem({...newItem, stock_quantity: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Reorder Level</Label>
                    <Input
                      type="number"
                      value={newItem.reorder_level}
                      onChange={(e) => setNewItem({...newItem, reorder_level: parseInt(e.target.value)})}
                    />
                  </div>
                </div>
              )}
              <div>
                <Label>Description</Label>
                <Input
                  value={newItem.description}
                  onChange={(e) => setNewItem({...newItem, description: e.target.value})}
                  placeholder="Item description"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
              <Button onClick={handleAddItem} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                Add {activeTab === "services" ? "Service" : "Part"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Services</p>
                <p className="text-2xl font-bold text-[#F4F6F0]">{totals.services}</p>
              </div>
              <Wrench className="h-8 w-8 text-[#C8FF00]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Parts</p>
                <p className="text-2xl font-bold text-[#F4F6F0]">{totals.parts}</p>
              </div>
              <Package className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Low Stock Items</p>
                <p className="text-2xl font-bold text-[#FF8C00]">{lowStockParts.length}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">In Stock</p>
                <p className="text-2xl font-bold text-green-600">{parts.length - lowStockParts.length}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
        <Input
          placeholder="Search items..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          data-testid="inventory-search"
        />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="services" className="data-[state=active]:bg-[#C8FF00] data-[state=active]:text-[#080C0F] font-bold">
            <Wrench className="h-4 w-4 mr-2" />
            Services ({services.length})
          </TabsTrigger>
          <TabsTrigger value="parts" className="data-[state=active]:bg-[#C8FF00] data-[state=active]:text-[#080C0F] font-bold">
            <Package className="h-4 w-4 mr-2" />
            Parts ({parts.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="services" className="mt-4">
          {loading ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading services...</div>
          ) : services.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
                No services found. Add your first service to get started.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {services.map((service) => (
                <Card key={service.item_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-semibold text-[#F4F6F0]">{service.name}</h3>
                          {service.hsn_sac && (
                            <Badge variant="outline" className="text-xs">
                              HSN: {service.hsn_sac}
                            </Badge>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                          {service.sku && (
                            <span className="flex items-center gap-1">
                              <Tag className="h-3.5 w-3.5" />
                              {service.sku}
                            </span>
                          )}
                          {service.description && (
                            <span className="flex items-center gap-1">
                              <FileText className="h-3.5 w-3.5" />
                              {service.description.substring(0, 50)}...
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-[#F4F6F0]">₹{service.rate?.toLocaleString('en-IN')}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">+ {service.tax_rate || 18}% GST</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="parts" className="mt-4">
          {loading ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading parts...</div>
          ) : parts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
                No parts found. Add your first part to get started.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {parts.map((part) => {
                const isLowStock = (part.stock_quantity || 0) <= (part.reorder_level || 5);
                return (
                  <Card key={part.item_id} className={`border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors ${isLowStock ? 'border-orange-200 bg-[rgba(255,140,0,0.08)]/50' : ''}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-1">
                            <h3 className="font-semibold text-[#F4F6F0]">{part.name}</h3>
                            {isLowStock && (
                              <Badge className="bg-orange-100 text-[#FF8C00] text-xs">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Low Stock
                              </Badge>
                            )}
                            {part.hsn_sac && (
                              <Badge variant="outline" className="text-xs">
                                HSN: {part.hsn_sac}
                              </Badge>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                            {part.sku && (
                              <span className="flex items-center gap-1">
                                <Tag className="h-3.5 w-3.5" />
                                {part.sku}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Package className="h-3.5 w-3.5" />
                              Stock: {part.stock_quantity || 0}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-[#F4F6F0]">₹{part.rate?.toLocaleString('en-IN')}</p>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">+ {part.tax_rate || 18}% GST</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
