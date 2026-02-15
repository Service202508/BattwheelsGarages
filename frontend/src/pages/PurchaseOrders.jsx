import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Search, Truck, Eye, CheckCircle, XCircle, Package } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-muted text-muted-foreground",
  pending_approval: "badge-warning",
  approved: "badge-info",
  ordered: "badge-info",
  partially_received: "badge-warning",
  received: "badge-success",
  cancelled: "badge-danger"
};

export default function PurchaseOrders({ user }) {
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedPO, setSelectedPO] = useState(null);
  const [isReceiveOpen, setIsReceiveOpen] = useState(false);
  const [formData, setFormData] = useState({
    supplier_id: "",
    items: [],
    expected_delivery: "",
    notes: "",
  });
  const [newItem, setNewItem] = useState({ item_id: "", quantity: 0, unit_price: 0 });

  useEffect(() => {
    fetchOrders();
    fetchSuppliers();
    fetchInventory();
  }, []);

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/purchase-orders`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setOrders(data);
      }
    } catch (error) {
      console.error("Failed to fetch orders:", error);
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
        setSuppliers(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch suppliers:", error);
    }
  };

  const fetchInventory = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/inventory`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        setInventory(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch inventory:", error);
    }
  };

  const addItemToOrder = () => {
    if (!newItem.item_id || newItem.quantity <= 0) {
      toast.error("Select item and quantity");
      return;
    }
    const item = inventory.find(i => i.item_id === newItem.item_id);
    if (!item) return;

    setFormData({
      ...formData,
      items: [...formData.items, {
        item_id: newItem.item_id,
        item_name: item.name,
        quantity: newItem.quantity,
        unit_price: newItem.unit_price || item.cost_price || item.unit_price
      }]
    });
    setNewItem({ item_id: "", quantity: 0, unit_price: 0 });
  };

  const removeItemFromOrder = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index)
    });
  };

  const handleCreatePO = async () => {
    if (!formData.supplier_id || formData.items.length === 0) {
      toast.error("Select supplier and add items");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/purchase-orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Purchase order created!");
        fetchOrders();
        resetForm();
      } else {
        toast.error("Failed to create PO");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const handleApprove = async (poId, approve) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/purchase-orders/${poId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ approval_status: approve ? "approved" : "rejected" }),
      });

      if (response.ok) {
        toast.success(approve ? "PO Approved!" : "PO Rejected");
        fetchOrders();
      }
    } catch (error) {
      toast.error("Action failed");
    }
  };

  const handleReceiveStock = async () => {
    if (!selectedPO) return;
    
    const itemsToReceive = selectedPO.items
      .filter(item => (item.quantity - (item.received_quantity || 0)) > 0)
      .map(item => ({
        item_id: item.item_id,
        quantity: item.quantity - (item.received_quantity || 0)
      }));

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/purchase-orders/${selectedPO.po_id}/receive`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(itemsToReceive),
      });

      if (response.ok) {
        toast.success("Stock received!");
        fetchOrders();
        fetchInventory();
        setIsReceiveOpen(false);
        setSelectedPO(null);
      }
    } catch (error) {
      toast.error("Failed to receive stock");
    }
  };

  const resetForm = () => {
    setFormData({ supplier_id: "", items: [], expected_delivery: "", notes: "" });
    setNewItem({ item_id: "", quantity: 0, unit_price: 0 });
    setIsCreateOpen(false);
  };

  const filteredOrders = orders.filter(o =>
    o.po_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    o.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const pendingApproval = orders.filter(o => o.approval_status === "pending").length;
  const totalValue = orders.reduce((sum, o) => sum + (o.total_amount || 0), 0);

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="purchase-orders-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Purchase Orders</h1>
          <p className="text-muted-foreground mt-1">Manage procurement and stock receiving.</p>
        </div>
        {(user?.role === "admin" || user?.role === "technician") && (
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="glow-primary" data-testid="create-po-btn">
                <Plus className="h-4 w-4 mr-2" />
                Create PO
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-white/10 max-w-3xl">
              <DialogHeader>
                <DialogTitle>Create Purchase Order</DialogTitle>
                <DialogDescription>Create a new purchase order for inventory restocking.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Supplier *</Label>
                    <Select
                      value={formData.supplier_id}
                      onValueChange={(value) => setFormData({ ...formData, supplier_id: value })}
                    >
                      <SelectTrigger className="bg-background/50">
                        <SelectValue placeholder="Select supplier" />
                      </SelectTrigger>
                      <SelectContent>
                        {suppliers.map((s) => (
                          <SelectItem key={s.supplier_id} value={s.supplier_id}>{s.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Expected Delivery</Label>
                    <Input
                      type="date"
                      value={formData.expected_delivery}
                      onChange={(e) => setFormData({ ...formData, expected_delivery: e.target.value })}
                      className="bg-background/50"
                    />
                  </div>
                </div>

                {/* Add Items */}
                <div className="p-4 rounded-lg bg-background/50 space-y-4">
                  <Label>Add Items</Label>
                  <div className="grid grid-cols-4 gap-2">
                    <Select
                      value={newItem.item_id}
                      onValueChange={(value) => {
                        const item = inventory.find(i => i.item_id === value);
                        setNewItem({ 
                          ...newItem, 
                          item_id: value,
                          unit_price: item?.cost_price || item?.unit_price || 0
                        });
                      }}
                    >
                      <SelectTrigger className="bg-background/50">
                        <SelectValue placeholder="Select item" />
                      </SelectTrigger>
                      <SelectContent>
                        {inventory.map((item) => (
                          <SelectItem key={item.item_id} value={item.item_id}>
                            {item.name} (Stock: {item.quantity})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Input
                      type="number"
                      placeholder="Qty"
                      value={newItem.quantity || ""}
                      onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                    <Input
                      type="number"
                      placeholder="Unit Price"
                      value={newItem.unit_price || ""}
                      onChange={(e) => setNewItem({ ...newItem, unit_price: parseFloat(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                    <Button onClick={addItemToOrder} variant="outline" className="border-white/10">
                      Add
                    </Button>
                  </div>

                  {/* Items List */}
                  {formData.items.length > 0 && (
                    <Table>
                      <TableHeader>
                        <TableRow className="border-white/10">
                          <TableHead>Item</TableHead>
                          <TableHead className="text-right">Qty</TableHead>
                          <TableHead className="text-right">Price</TableHead>
                          <TableHead className="text-right">Total</TableHead>
                          <TableHead></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {formData.items.map((item, idx) => (
                          <TableRow key={idx} className="border-white/10">
                            <TableCell>{item.item_name}</TableCell>
                            <TableCell className="text-right mono">{item.quantity}</TableCell>
                            <TableCell className="text-right mono">₹{item.unit_price}</TableCell>
                            <TableCell className="text-right mono">₹{(item.quantity * item.unit_price).toLocaleString()}</TableCell>
                            <TableCell>
                              <Button size="sm" variant="ghost" onClick={() => removeItemFromOrder(idx)}>
                                <XCircle className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                        <TableRow className="border-white/10 font-semibold">
                          <TableCell colSpan={3}>Subtotal</TableCell>
                          <TableCell className="text-right mono">
                            ₹{formData.items.reduce((s, i) => s + i.quantity * i.unit_price, 0).toLocaleString()}
                          </TableCell>
                          <TableCell></TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="bg-background/50"
                    rows={2}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm} className="border-white/10">Cancel</Button>
                <Button onClick={handleCreatePO} className="glow-primary">Create PO</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total POs</p>
            <p className="text-2xl font-bold mono">{orders.length}</p>
          </CardContent>
        </Card>
        <Card className={`metric-card ${pendingApproval > 0 ? 'border-orange-500/30' : ''}`}>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Pending Approval</p>
            <p className={`text-2xl font-bold mono ${pendingApproval > 0 ? 'text-orange-400' : ''}`}>{pendingApproval}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Awaiting Delivery</p>
            <p className="text-2xl font-bold mono">{orders.filter(o => o.status === "ordered" || o.status === "approved").length}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Value</p>
            <p className="text-2xl font-bold mono">₹{totalValue.toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by PO number or supplier..."
              className="pl-10 bg-background/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading orders...</div>
          ) : filteredOrders.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No purchase orders found. Create your first PO to get started.
            </div>
          ) : (
            <Table className="data-table">
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>PO Number</TableHead>
                  <TableHead>Supplier</TableHead>
                  <TableHead>Items</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Approval</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.po_id} className="border-white/10">
                    <TableCell className="mono font-semibold">{order.po_number}</TableCell>
                    <TableCell>{order.supplier_name}</TableCell>
                    <TableCell>{order.items?.length || 0} items</TableCell>
                    <TableCell className="text-right mono">₹{(order.total_amount || 0).toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge className={statusColors[order.status]} variant="outline">
                        {order.status?.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={order.approval_status === "approved" ? "badge-success" : order.approval_status === "rejected" ? "badge-danger" : "badge-warning"} variant="outline">
                        {order.approval_status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {user?.role === "admin" && order.approval_status === "pending" && (
                          <>
                            <Button size="sm" variant="ghost" onClick={() => handleApprove(order.po_id, true)} className="text-emerald-400">
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => handleApprove(order.po_id, false)} className="text-red-400">
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                        {order.status === "approved" || order.status === "ordered" || order.status === "partially_received" ? (
                          <Button size="sm" variant="outline" onClick={() => { setSelectedPO(order); setIsReceiveOpen(true); }} className="border-white/10">
                            <Package className="h-4 w-4 mr-1" /> Receive
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Receive Stock Dialog */}
      <Dialog open={isReceiveOpen} onOpenChange={setIsReceiveOpen}>
        <DialogContent className="bg-card border-white/10">
          <DialogHeader>
            <DialogTitle>Receive Stock</DialogTitle>
            <DialogDescription>Mark items as received for PO: {selectedPO?.po_number}</DialogDescription>
          </DialogHeader>
          {selectedPO && (
            <div className="space-y-4">
              <Table>
                <TableHeader>
                  <TableRow className="border-white/10">
                    <TableHead>Item</TableHead>
                    <TableHead className="text-right">Ordered</TableHead>
                    <TableHead className="text-right">Received</TableHead>
                    <TableHead className="text-right">Pending</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {selectedPO.items?.map((item, idx) => (
                    <TableRow key={idx} className="border-white/10">
                      <TableCell>{item.item_name}</TableCell>
                      <TableCell className="text-right mono">{item.quantity}</TableCell>
                      <TableCell className="text-right mono">{item.received_quantity || 0}</TableCell>
                      <TableCell className="text-right mono font-semibold">
                        {item.quantity - (item.received_quantity || 0)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsReceiveOpen(false)} className="border-white/10">Cancel</Button>
            <Button onClick={handleReceiveStock} className="glow-primary">Receive All Pending</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
