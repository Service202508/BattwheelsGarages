import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { 
  Plus, Truck, Package, ArrowRight, Building2, Search, RefreshCw,
  Send, CheckCircle2, XCircle, Clock, Filter, MoreVertical, Loader2,
  ArrowLeftRight, Warehouse, PackageCheck, PackageX
} from "lucide-react";
import { API } from "@/App";

const statusConfig = {
  draft: { label: "Draft", color: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]", icon: Clock },
  pending: { label: "Pending", color: "bg-yellow-100 text-[#EAB308]", icon: Clock },
  in_transit: { label: "In Transit", color: "bg-blue-100 text-[#3B9EFF]", icon: Truck },
  received: { label: "Received", color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]", icon: CheckCircle2 },
  void: { label: "Void", color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]", icon: XCircle },
};

export default function StockTransfers() {
  const [transfers, setTransfers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedTransfer, setSelectedTransfer] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // Create form state
  const [newTransfer, setNewTransfer] = useState({
    source_warehouse_id: "",
    destination_warehouse_id: "",
    notes: "",
    items: []
  });
  const [selectedItemId, setSelectedItemId] = useState("");
  const [selectedItemQty, setSelectedItemQty] = useState(1);

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (activeTab !== "all") params.append("status", activeTab);
      const queryStr = params.toString() ? `?${params}` : "";

      const [transfersRes, warehousesRes, statsRes] = await Promise.all([
        fetch(`${API}/stock-transfers/${queryStr}`, { headers }),
        fetch(`${API}/inventory-enhanced/warehouses`, { headers }),
        fetch(`${API}/stock-transfers/stats/summary`, { headers })
      ]);

      const transfersData = await transfersRes.json();
      const warehousesData = await warehousesRes.json();
      const statsData = await statsRes.json();

      setTransfers(transfersData.transfers || []);
      setWarehouses(warehousesData.warehouses || []);
      setStats(statsData.stats || statsData);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to load transfers");
    } finally {
      setLoading(false);
    }
  };

  const fetchItemsForWarehouse = async (warehouseId) => {
    try {
      const res = await fetch(`${API}/inventory-enhanced/stock?warehouse_id=${warehouseId}`, { headers });
      const data = await res.json();
      setItems(data.stock || []);
    } catch (error) {
      console.error("Error fetching items:", error);
    }
  };

  const handleCreateTransfer = async () => {
    if (!newTransfer.source_warehouse_id || !newTransfer.destination_warehouse_id) {
      return toast.error("Select source and destination warehouses");
    }
    if (newTransfer.source_warehouse_id === newTransfer.destination_warehouse_id) {
      return toast.error("Source and destination must be different");
    }
    if (newTransfer.items.length === 0) {
      return toast.error("Add at least one item");
    }

    try {
      const res = await fetch(`${API}/stock-transfers/`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          source_warehouse_id: newTransfer.source_warehouse_id,
          destination_warehouse_id: newTransfer.destination_warehouse_id,
          notes: newTransfer.notes,
          line_items: newTransfer.items
        })
      });
      
      if (res.ok) {
        toast.success("Transfer created successfully");
        setShowCreateDialog(false);
        resetCreateForm();
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create transfer");
      }
    } catch (error) {
      toast.error("Error creating transfer");
    }
  };

  const handleShipTransfer = async (transferId) => {
    try {
      const res = await fetch(`${API}/stock-transfers/${transferId}/ship`, {
        method: "POST",
        headers
      });
      
      if (res.ok) {
        toast.success("Transfer shipped");
        fetchData();
        setShowDetailDialog(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to ship transfer");
      }
    } catch (error) {
      toast.error("Error shipping transfer");
    }
  };

  const handleReceiveTransfer = async (transferId) => {
    try {
      const res = await fetch(`${API}/stock-transfers/${transferId}/receive`, {
        method: "POST",
        headers
      });
      
      if (res.ok) {
        toast.success("Transfer received");
        fetchData();
        setShowDetailDialog(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to receive transfer");
      }
    } catch (error) {
      toast.error("Error receiving transfer");
    }
  };

  const handleVoidTransfer = async (transferId) => {
    if (!confirm("Are you sure you want to void this transfer?")) return;
    
    try {
      const res = await fetch(`${API}/stock-transfers/${transferId}/void`, {
        method: "POST",
        headers
      });
      
      if (res.ok) {
        toast.success("Transfer voided");
        fetchData();
        setShowDetailDialog(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to void transfer");
      }
    } catch (error) {
      toast.error("Error voiding transfer");
    }
  };

  const resetCreateForm = () => {
    setNewTransfer({
      source_warehouse_id: "",
      destination_warehouse_id: "",
      notes: "",
      items: []
    });
    setItems([]);
    setSelectedItemId("");
    setSelectedItemQty(1);
  };

  const addItemToTransfer = () => {
    if (!selectedItemId || selectedItemQty < 1) return;
    
    const item = items.find(i => i.item_id === selectedItemId);
    if (!item) return;
    
    if (selectedItemQty > item.available_quantity) {
      return toast.error(`Only ${item.available_quantity} available`);
    }

    const existing = newTransfer.items.find(i => i.item_id === selectedItemId);
    if (existing) {
      setNewTransfer({
        ...newTransfer,
        items: newTransfer.items.map(i => 
          i.item_id === selectedItemId 
            ? { ...i, quantity: i.quantity + selectedItemQty }
            : i
        )
      });
    } else {
      setNewTransfer({
        ...newTransfer,
        items: [...newTransfer.items, {
          item_id: item.item_id,
          item_name: item.item_name,
          sku: item.sku,
          quantity: selectedItemQty
        }]
      });
    }
    
    setSelectedItemId("");
    setSelectedItemQty(1);
  };

  const removeItemFromTransfer = (itemId) => {
    setNewTransfer({
      ...newTransfer,
      items: newTransfer.items.filter(i => i.item_id !== itemId)
    });
  };

  const filteredTransfers = transfers.filter(t => 
    searchQuery === "" ||
    t.transfer_order_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.source_warehouse_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.destination_warehouse_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "2-digit", month: "short", year: "numeric"
    });
  };

  return (
    <div className="space-y-6" data-testid="stock-transfers-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Stock Transfers</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Transfer inventory between warehouses</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-transfer-btn">
                <Plus className="h-4 w-4 mr-2" /> New Transfer
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Stock Transfer</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {/* Warehouse Selection */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Source Warehouse *</Label>
                    <Select 
                      value={newTransfer.source_warehouse_id} 
                      onValueChange={(v) => {
                        setNewTransfer({ ...newTransfer, source_warehouse_id: v, items: [] });
                        fetchItemsForWarehouse(v);
                      }}
                    >
                      <SelectTrigger data-testid="source-warehouse-select">
                        <SelectValue placeholder="Select source" />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses.map(w => (
                          <SelectItem key={w.warehouse_id} value={w.warehouse_id}>
                            {w.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Destination Warehouse *</Label>
                    <Select 
                      value={newTransfer.destination_warehouse_id} 
                      onValueChange={(v) => setNewTransfer({ ...newTransfer, destination_warehouse_id: v })}
                    >
                      <SelectTrigger data-testid="dest-warehouse-select">
                        <SelectValue placeholder="Select destination" />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses.filter(w => w.warehouse_id !== newTransfer.source_warehouse_id).map(w => (
                          <SelectItem key={w.warehouse_id} value={w.warehouse_id}>
                            {w.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Visual Arrow */}
                {newTransfer.source_warehouse_id && newTransfer.destination_warehouse_id && (
                  <div className="flex items-center justify-center gap-4 py-2">
                    <div className="flex items-center gap-2 px-3 py-2 bg-[rgba(255,255,255,0.05)] rounded-lg">
                      <Warehouse className="h-4 w-4 text-[rgba(244,246,240,0.35)]" />
                      <span className="text-sm font-medium">
                        {warehouses.find(w => w.warehouse_id === newTransfer.source_warehouse_id)?.name}
                      </span>
                    </div>
                    <ArrowRight className="h-5 w-5 text-[#C8FF00]" />
                    <div className="flex items-center gap-2 px-3 py-2 bg-[#C8FF00]/10 rounded-lg">
                      <Warehouse className="h-4 w-4 text-[#C8FF00]" />
                      <span className="text-sm font-medium">
                        {warehouses.find(w => w.warehouse_id === newTransfer.destination_warehouse_id)?.name}
                      </span>
                    </div>
                  </div>
                )}

                {/* Item Selection */}
                {newTransfer.source_warehouse_id && (
                  <div className="space-y-3">
                    <Label>Add Items</Label>
                    <div className="flex gap-2">
                      <Select value={selectedItemId} onValueChange={setSelectedItemId}>
                        <SelectTrigger className="flex-1" data-testid="item-select">
                          <SelectValue placeholder="Select item" />
                        </SelectTrigger>
                        <SelectContent>
                          {items.map(item => (
                            <SelectItem key={item.item_id} value={item.item_id}>
                              {item.item_name} ({item.available_quantity} available)
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Input 
                        type="number" 
                        min="1" 
                        value={selectedItemQty} 
                        onChange={(e) => setSelectedItemQty(parseInt(e.target.value) || 1)}
                        className="w-24"
                        placeholder="Qty"
                      />
                      <Button type="button" onClick={addItemToTransfer} variant="outline">
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Selected Items */}
                    {newTransfer.items.length > 0 && (
                      <div className="border rounded-lg overflow-hidden">
                        <Table>
                          <TableHeader>
                            <TableRow className="bg-[#111820]">
                              <TableHead>Item</TableHead>
                              <TableHead className="text-right">Quantity</TableHead>
                              <TableHead className="w-12"></TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {newTransfer.items.map((item, idx) => (
                              <TableRow key={idx}>
                                <TableCell>
                                  <div className="font-medium">{item.item_name}</div>
                                  <div className="text-xs text-[rgba(244,246,240,0.45)]">{item.sku}</div>
                                </TableCell>
                                <TableCell className="text-right">{item.quantity}</TableCell>
                                <TableCell>
                                  <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    onClick={() => removeItemFromTransfer(item.item_id)}
                                  >
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    )}
                  </div>
                )}

                {/* Notes */}
                <div>
                  <Label>Notes (Optional)</Label>
                  <Input 
                    value={newTransfer.notes} 
                    onChange={(e) => setNewTransfer({ ...newTransfer, notes: e.target.value })}
                    placeholder="Transfer reason or notes"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => { setShowCreateDialog(false); resetCreateForm(); }}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleCreateTransfer} 
                  className="bg-[#C8FF00] text-[#080C0F] font-bold"
                  disabled={newTransfer.items.length === 0}
                >
                  Create Transfer
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[rgba(255,255,255,0.05)] rounded-lg">
                  <Package className="h-5 w-5 text-[rgba(244,246,240,0.35)]" />
                </div>
                <div>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">Total Transfers</p>
                  <p className="text-xl font-bold">{stats.total_transfers || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Clock className="h-5 w-5 text-[#EAB308]" />
                </div>
                <div>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">Pending</p>
                  <p className="text-xl font-bold">{stats.by_status?.draft || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Truck className="h-5 w-5 text-[#3B9EFF]" />
                </div>
                <div>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">In Transit</p>
                  <p className="text-xl font-bold">{stats.by_status?.in_transit || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">Received</p>
                  <p className="text-xl font-bold">{stats.by_status?.received || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="draft">Draft</TabsTrigger>
            <TabsTrigger value="in_transit">In Transit</TabsTrigger>
            <TabsTrigger value="received">Received</TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
          <Input 
            placeholder="Search transfers..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Transfers List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
            </div>
          ) : filteredTransfers.length === 0 ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">
              <ArrowLeftRight className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
              <p>No transfers found</p>
              <p className="text-sm">Create a new transfer to move stock between warehouses</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-[#111820]">
                  <TableHead>Transfer #</TableHead>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                  <TableHead className="text-center">Items</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTransfers.map(transfer => {
                  const status = statusConfig[transfer.status] || statusConfig.draft;
                  const StatusIcon = status.icon;
                  return (
                    <TableRow key={transfer.transfer_id} className="hover:bg-[#111820]">
                      <TableCell className="font-medium">
                        {transfer.transfer_order_number}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                          {transfer.source_warehouse_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                          {transfer.destination_warehouse_name}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline">{transfer.items?.length || 0}</Badge>
                      </TableCell>
                      <TableCell>{formatDate(transfer.created_at)}</TableCell>
                      <TableCell>
                        <Badge className={status.color}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          {transfer.status === "draft" && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleShipTransfer(transfer.transfer_id)}
                              data-testid={`ship-${transfer.transfer_id}`}
                            >
                              <Send className="h-3 w-3 mr-1" /> Ship
                            </Button>
                          )}
                          {transfer.status === "in_transit" && (
                            <Button 
                              size="sm" 
                              className="bg-green-600 hover:bg-green-700 text-white"
                              onClick={() => handleReceiveTransfer(transfer.transfer_id)}
                              data-testid={`receive-${transfer.transfer_id}`}
                            >
                              <PackageCheck className="h-3 w-3 mr-1" /> Receive
                            </Button>
                          )}
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={() => {
                              setSelectedTransfer(transfer);
                              setShowDetailDialog(true);
                            }}
                          >
                            View
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Transfer Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Transfer Details</DialogTitle>
          </DialogHeader>
          {selectedTransfer && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold">{selectedTransfer.transfer_order_number}</span>
                <Badge className={statusConfig[selectedTransfer.status]?.color}>
                  {statusConfig[selectedTransfer.status]?.label}
                </Badge>
              </div>
              
              <div className="flex items-center justify-center gap-4 py-4 bg-[#111820] rounded-lg">
                <div className="text-center">
                  <Building2 className="h-6 w-6 mx-auto text-[rgba(244,246,240,0.45)] mb-1" />
                  <p className="text-sm font-medium">{selectedTransfer.source_warehouse_name}</p>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">Source</p>
                </div>
                <ArrowRight className="h-6 w-6 text-[#C8FF00]" />
                <div className="text-center">
                  <Building2 className="h-6 w-6 mx-auto text-[#C8FF00] mb-1" />
                  <p className="text-sm font-medium">{selectedTransfer.destination_warehouse_name}</p>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">Destination</p>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Items ({selectedTransfer.items?.length || 0})</h4>
                <div className="border rounded-lg divide-y max-h-48 overflow-y-auto">
                  {selectedTransfer.items?.map((item, idx) => (
                    <div key={idx} className="p-3 flex justify-between">
                      <div>
                        <p className="font-medium">{item.item_name}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">{item.sku}</p>
                      </div>
                      <Badge variant="outline">{item.quantity} units</Badge>
                    </div>
                  ))}
                </div>
              </div>

              {selectedTransfer.notes && (
                <div>
                  <h4 className="font-medium mb-1">Notes</h4>
                  <p className="text-sm text-[rgba(244,246,240,0.35)]">{selectedTransfer.notes}</p>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-4 border-t">
                {selectedTransfer.status === "draft" && (
                  <>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => handleVoidTransfer(selectedTransfer.transfer_id)}
                    >
                      <PackageX className="h-4 w-4 mr-1" /> Void
                    </Button>
                    <Button 
                      size="sm"
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                      onClick={() => handleShipTransfer(selectedTransfer.transfer_id)}
                    >
                      <Send className="h-4 w-4 mr-1" /> Ship Transfer
                    </Button>
                  </>
                )}
                {selectedTransfer.status === "in_transit" && (
                  <>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => handleVoidTransfer(selectedTransfer.transfer_id)}
                    >
                      <PackageX className="h-4 w-4 mr-1" /> Void
                    </Button>
                    <Button 
                      size="sm"
                      className="bg-green-600 hover:bg-green-700 text-white"
                      onClick={() => handleReceiveTransfer(selectedTransfer.transfer_id)}
                    >
                      <PackageCheck className="h-4 w-4 mr-1" /> Receive
                    </Button>
                  </>
                )}
                {selectedTransfer.status === "received" && (
                  <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
                    Close
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
