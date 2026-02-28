import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Search, ShoppingCart, Eye, CheckCircle, XCircle, FileText } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-muted text-muted-foreground",
  pending_approval: "badge-warning",
  approved: "badge-success",
  invoiced: "badge-info",
  completed: "badge-success"
};

const approvalColors = {
  pending: "badge-warning",
  level1_approved: "badge-info",
  level2_approved: "badge-success",
  rejected: "badge-danger"
};

export default function SalesOrders({ user }) {
  const [orders, setOrders] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [services, setServices] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [formData, setFormData] = useState({
    ticket_id: "",
    services: [],
    parts: [],
    labor_charges: 0,
    discount_percent: 0
  });

  useEffect(() => {
    fetchOrders();
    fetchTickets();
    fetchServices();
    fetchInventory();
  }, []);

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/sales-orders`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        setOrders(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch orders:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTickets = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/tickets`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        // Only tickets without sales orders
        setTickets((data.data || data || []).filter(t => !t.has_sales_order && t.status !== "closed"));
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
    }
  };

  const fetchServices = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/services`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        setServices(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch services:", error);
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

  const addService = (serviceId) => {
    const service = services.find(s => s.service_id === serviceId);
    if (!service) return;
    if (formData.services.find(s => s.service_id === serviceId)) {
      toast.error("Service already added");
      return;
    }
    setFormData({
      ...formData,
      services: [...formData.services, {
        service_id: serviceId,
        name: service.name,
        price: service.base_price,
        quantity: 1
      }]
    });
  };

  const addPart = (itemId) => {
    const item = inventory.find(i => i.item_id === itemId);
    if (!item) return;
    if (formData.parts.find(p => p.item_id === itemId)) {
      toast.error("Part already added");
      return;
    }
    setFormData({
      ...formData,
      parts: [...formData.parts, {
        item_id: itemId,
        name: item.name,
        price: item.unit_price,
        quantity: 1
      }]
    });
  };

  const updateServiceQty = (idx, qty) => {
    const updated = [...formData.services];
    updated[idx].quantity = qty;
    setFormData({ ...formData, services: updated });
  };

  const updatePartQty = (idx, qty) => {
    const updated = [...formData.parts];
    updated[idx].quantity = qty;
    setFormData({ ...formData, parts: updated });
  };

  const removeService = (idx) => {
    setFormData({ ...formData, services: formData.services.filter((_, i) => i !== idx) });
  };

  const removePart = (idx) => {
    setFormData({ ...formData, parts: formData.parts.filter((_, i) => i !== idx) });
  };

  const handleCreateOrder = async () => {
    if (!formData.ticket_id) {
      toast.error("Select a ticket");
      return;
    }
    if (formData.services.length === 0 && formData.parts.length === 0) {
      toast.error("Add at least one service or part");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/sales-orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Sales order created!");
        fetchOrders();
        fetchTickets();
        resetForm();
      } else {
        toast.error("Failed to create order");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const handleApprove = async (salesId, level) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/sales-orders/${salesId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ approval_status: level }),
      });

      if (response.ok) {
        toast.success("Order updated!");
        fetchOrders();
      }
    } catch (error) {
      toast.error("Action failed");
    }
  };

  const resetForm = () => {
    setFormData({ ticket_id: "", services: [], parts: [], labor_charges: 0, discount_percent: 0 });
    setIsCreateOpen(false);
  };

  const filteredOrders = orders.filter(o =>
    o.sales_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    o.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const calculateTotal = () => {
    const servicesTotal = formData.services.reduce((s, srv) => s + srv.price * srv.quantity, 0);
    const partsTotal = formData.parts.reduce((s, p) => s + p.price * p.quantity, 0);
    const subtotal = servicesTotal + partsTotal + formData.labor_charges;
    const discount = subtotal * (formData.discount_percent / 100);
    const taxable = subtotal - discount;
    const tax = taxable * 0.18;
    return { servicesTotal, partsTotal, subtotal, discount, tax, total: taxable + tax };
  };

  const totals = calculateTotal();
  const totalRevenue = orders.reduce((s, o) => s + (o.total_amount || 0), 0);

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="sales-orders-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Sales Orders</h1>
          <p className="text-muted-foreground mt-1">Manage service quotes and sales from tickets.</p>
        </div>
        {(user?.role === "admin" || user?.role === "technician") && (
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="glow-primary" data-testid="create-sales-btn">
                <Plus className="h-4 w-4 mr-2" />
                Create Sales Order
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-white/10 max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Sales Order</DialogTitle>
                <DialogDescription>Create a sales order from a service ticket.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Select Ticket *</Label>
                  <Select
                    value={formData.ticket_id}
                    onValueChange={(value) => setFormData({ ...formData, ticket_id: value })}
                  >
                    <SelectTrigger className="bg-background/50">
                      <SelectValue placeholder="Select a ticket" />
                    </SelectTrigger>
                    <SelectContent>
                      {tickets.map((t) => (
                        <SelectItem key={t.ticket_id} value={t.ticket_id}>
                          {t.ticket_id} - {t.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Services */}
                <div className="p-4 rounded-lg bg-background/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Services</Label>
                    <Select onValueChange={addService}>
                      <SelectTrigger className="w-48 bg-background/50">
                        <SelectValue placeholder="Add service" />
                      </SelectTrigger>
                      <SelectContent>
                        {services.map((s) => (
                          <SelectItem key={s.service_id} value={s.service_id}>
                            {s.name} - ₹{s.base_price}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {formData.services.length > 0 && (
                    <Table>
                      <TableBody>
                        {formData.services.map((srv, idx) => (
                          <TableRow key={idx} className="border-white/10">
                            <TableCell>{srv.name}</TableCell>
                            <TableCell className="w-24">
                              <Input
                                type="number"
                                min={1}
                                value={srv.quantity}
                                onChange={(e) => updateServiceQty(idx, parseInt(e.target.value) || 1)}
                                className="bg-background/50 h-8"
                              />
                            </TableCell>
                            <TableCell className="text-right mono">₹{srv.price}</TableCell>
                            <TableCell className="text-right mono">₹{(srv.price * srv.quantity).toLocaleString()}</TableCell>
                            <TableCell>
                              <Button size="sm" variant="ghost" onClick={() => removeService(idx)}>
                                <XCircle className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>

                {/* Parts */}
                <div className="p-4 rounded-lg bg-background/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Parts</Label>
                    <Select onValueChange={addPart}>
                      <SelectTrigger className="w-48 bg-background/50">
                        <SelectValue placeholder="Add part" />
                      </SelectTrigger>
                      <SelectContent>
                        {inventory.map((i) => (
                          <SelectItem key={i.item_id} value={i.item_id}>
                            {i.name} - ₹{i.unit_price}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {formData.parts.length > 0 && (
                    <Table>
                      <TableBody>
                        {formData.parts.map((part, idx) => (
                          <TableRow key={idx} className="border-white/10">
                            <TableCell>{part.name}</TableCell>
                            <TableCell className="w-24">
                              <Input
                                type="number"
                                min={1}
                                value={part.quantity}
                                onChange={(e) => updatePartQty(idx, parseInt(e.target.value) || 1)}
                                className="bg-background/50 h-8"
                              />
                            </TableCell>
                            <TableCell className="text-right mono">₹{part.price}</TableCell>
                            <TableCell className="text-right mono">₹{(part.price * part.quantity).toLocaleString()}</TableCell>
                            <TableCell>
                              <Button size="sm" variant="ghost" onClick={() => removePart(idx)}>
                                <XCircle className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>

                {/* Charges & Discount */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Labor Charges (₹)</Label>
                    <Input
                      type="number"
                      value={formData.labor_charges}
                      onChange={(e) => setFormData({ ...formData, labor_charges: parseFloat(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Discount (%)</Label>
                    <Input
                      type="number"
                      value={formData.discount_percent}
                      onChange={(e) => setFormData({ ...formData, discount_percent: parseFloat(e.target.value) || 0 })}
                      className="bg-background/50"
                    />
                  </div>
                </div>

                {/* Summary */}
                <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Services</span>
                    <span className="mono">₹{totals.servicesTotal.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Parts</span>
                    <span className="mono">₹{totals.partsTotal.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Labor</span>
                    <span className="mono">₹{formData.labor_charges.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm border-t border-white/10 pt-2">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="mono">₹{totals.subtotal.toLocaleString()}</span>
                  </div>
                  {formData.discount_percent > 0 && (
                    <div className="flex justify-between text-sm text-[#C8FF00] text-400">
                      <span>Discount ({formData.discount_percent}%)</span>
                      <span className="mono">-₹{totals.discount.toLocaleString()}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">GST (18%)</span>
                    <span className="mono">₹{totals.tax.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t border-white/10 pt-2">
                    <span>Total</span>
                    <span className="mono text-primary">₹{totals.total.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm} className="border-white/10">Cancel</Button>
                <Button onClick={handleCreateOrder} className="glow-primary">Create Order</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Orders</p>
            <p className="text-2xl font-bold mono">{orders.length}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Pending Approval</p>
            <p className="text-2xl font-bold mono">{orders.filter(o => o.approval_status === "pending").length}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Approved</p>
            <p className="text-2xl font-bold mono">{orders.filter(o => o.status === "approved").length}</p>
          </CardContent>
        </Card>
        <Card className="metric-card">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total Revenue</p>
            <p className="text-2xl font-bold mono">₹{totalRevenue.toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search orders..."
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
              No sales orders found. Create your first order from a ticket.
            </div>
          ) : (
            <Table className="data-table">
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>Order ID</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Ticket</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Approval</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.sales_id} className="border-white/10">
                    <TableCell className="mono font-semibold">{order.sales_id}</TableCell>
                    <TableCell>{order.customer_name || '-'}</TableCell>
                    <TableCell className="mono text-sm">{order.ticket_id}</TableCell>
                    <TableCell className="text-right mono">₹{(order.total_amount || 0).toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge className={statusColors[order.status]} variant="outline">
                        {order.status?.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={approvalColors[order.approval_status]} variant="outline">
                        {order.approval_status?.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {user?.role === "admin" && order.approval_status === "pending" && (
                          <>
                            <Button size="sm" variant="ghost" onClick={() => handleApprove(order.sales_id, "level1_approved")} className="text-[#C8FF00] text-400">
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => handleApprove(order.sales_id, "rejected")} className="text-red-400">
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                        {order.approval_status === "level1_approved" && user?.role === "admin" && (
                          <Button size="sm" variant="outline" onClick={() => handleApprove(order.sales_id, "level2_approved")} className="border-white/10">
                            Final Approve
                          </Button>
                        )}
                      </div>
                    </TableCell>
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
