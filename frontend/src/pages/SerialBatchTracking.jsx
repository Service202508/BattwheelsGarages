import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Hash, Package, AlertTriangle, CheckCircle, Clock, Search, Plus, 
  Settings, RefreshCw, Barcode, Calendar, Truck, Archive, History,
  Filter, Download, Upload, ChevronRight, Eye, Edit
} from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";

const statusColors = {
  available: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25",
  sold: "bg-blue-100 text-bw-blue",
  returned: "bg-yellow-100 text-bw-amber",
  damaged: "bg-bw-red/10 text-bw-red border border-bw-red/25",
  reserved: "bg-purple-100 text-bw-purple",
  active: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25",
  depleted: "bg-white/5 text-bw-white/35",
  expired: "bg-bw-red/10 text-bw-red border border-bw-red/25"
};

export default function SerialBatchTracking() {
  const [activeTab, setActiveTab] = useState("serials");
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  
  // Data
  const [serials, setSerials] = useState([]);
  const [batches, setBatches] = useState([]);
  const [trackingItems, setTrackingItems] = useState([]);
  const [serialSummary, setSerialSummary] = useState(null);
  const [batchSummary, setBatchSummary] = useState(null);
  const [expiringBatches, setExpiringBatches] = useState([]);
  
  // Dialogs
  const [showCreateSerialDialog, setShowCreateSerialDialog] = useState(false);
  const [showCreateBatchDialog, setShowCreateBatchDialog] = useState(false);
  const [showBulkSerialDialog, setShowBulkSerialDialog] = useState(false);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedSerial, setSelectedSerial] = useState(null);
  const [selectedBatch, setSelectedBatch] = useState(null);
  
  // Forms
  const [newSerial, setNewSerial] = useState({
    item_id: "", serial_number: "", warehouse_id: "", cost_price: 0, warranty_expiry: "", notes: ""
  });
  const [bulkSerial, setBulkSerial] = useState({
    item_id: "", prefix: "", start_number: 1, count: 10, warehouse_id: "", cost_price: 0
  });
  const [newBatch, setNewBatch] = useState({
    item_id: "", batch_number: "", warehouse_id: "", quantity: 0, 
    manufacturing_date: "", expiry_date: "", cost_price: 0, notes: ""
  });
  const [itemConfig, setItemConfig] = useState({
    enable_serial: false, enable_batch: false, serial_prefix: "", batch_prefix: "",
    require_on_sale: true, require_on_purchase: true, auto_generate_serial: false
  });

  const fetchSerials = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ per_page: "100" });
      if (searchTerm) params.append("search", searchTerm);
      if (statusFilter) params.append("status", statusFilter);
      
      const res = await fetch(`${API}/serial-batch/serials?${params}`);
      const data = await res.json();
      if (data.code === 0) setSerials(data.serials || []);
    } catch (e) {
      console.error("Error fetching serials:", e);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, statusFilter]);

  const fetchBatches = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ per_page: "100" });
      if (searchTerm) params.append("search", searchTerm);
      if (statusFilter) params.append("status", statusFilter);
      
      const res = await fetch(`${API}/serial-batch/batches?${params}`);
      const data = await res.json();
      if (data.code === 0) setBatches(data.batches || []);
    } catch (e) {
      console.error("Error fetching batches:", e);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, statusFilter]);

  const fetchSummaries = async () => {
    try {
      const [serialRes, batchRes, expiringRes, itemsRes] = await Promise.all([
        fetch(`${API}/serial-batch/reports/serial-summary`),
        fetch(`${API}/serial-batch/reports/batch-summary`),
        fetch(`${API}/serial-batch/batches/expiring?days=30`),
        fetch(`${API}/serial-batch/items/tracking-enabled`)
      ]);
      
      const [serialData, batchData, expiringData, itemsData] = await Promise.all([
        serialRes.json(), batchRes.json(), expiringRes.json(), itemsRes.json()
      ]);
      
      if (serialData.code === 0) setSerialSummary(serialData.summary);
      if (batchData.code === 0) setBatchSummary(batchData.summary);
      if (expiringData.code === 0) setExpiringBatches(expiringData.expiring_batches || []);
      if (itemsData.code === 0) setTrackingItems(itemsData.items || []);
    } catch (e) {
      console.error("Error fetching summaries:", e);
    }
  };

  useEffect(() => {
    fetchSummaries();
  }, []);

  useEffect(() => {
    if (activeTab === "serials") fetchSerials();
    else if (activeTab === "batches") fetchBatches();
  }, [activeTab, fetchSerials, fetchBatches]);

  const handleCreateSerial = async () => {
    if (!newSerial.item_id || !newSerial.serial_number) {
      toast.error("Item and serial number are required");
      return;
    }
    
    try {
      const res = await fetch(`${API}/serial-batch/serials`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newSerial)
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success("Serial number created");
        setShowCreateSerialDialog(false);
        setNewSerial({ item_id: "", serial_number: "", warehouse_id: "", cost_price: 0, warranty_expiry: "", notes: "" });
        fetchSerials();
        fetchSummaries();
      } else {
        toast.error(data.detail || "Failed to create serial");
      }
    } catch (e) {
      toast.error("Error creating serial number");
    }
  };

  const handleBulkCreateSerials = async () => {
    if (!bulkSerial.item_id || bulkSerial.count < 1) {
      toast.error("Item and count are required");
      return;
    }
    
    try {
      const res = await fetch(`${API}/serial-batch/serials/bulk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bulkSerial)
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success(`Created ${data.created?.length || 0} serial numbers`);
        setShowBulkSerialDialog(false);
        setBulkSerial({ item_id: "", prefix: "", start_number: 1, count: 10, warehouse_id: "", cost_price: 0 });
        fetchSerials();
        fetchSummaries();
      } else {
        toast.error(data.detail || "Failed to create serials");
      }
    } catch (e) {
      toast.error("Error creating serial numbers");
    }
  };

  const handleCreateBatch = async () => {
    if (!newBatch.item_id || !newBatch.batch_number || newBatch.quantity <= 0) {
      toast.error("Item, batch number, and quantity are required");
      return;
    }
    
    try {
      const res = await fetch(`${API}/serial-batch/batches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...newBatch, available_quantity: newBatch.quantity })
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success("Batch number created");
        setShowCreateBatchDialog(false);
        setNewBatch({ item_id: "", batch_number: "", warehouse_id: "", quantity: 0, manufacturing_date: "", expiry_date: "", cost_price: 0, notes: "" });
        fetchBatches();
        fetchSummaries();
      } else {
        toast.error(data.detail || "Failed to create batch");
      }
    } catch (e) {
      toast.error("Error creating batch number");
    }
  };

  const handleConfigureItem = async () => {
    if (!selectedItem) return;
    
    try {
      const res = await fetch(`${API}/serial-batch/items/${selectedItem}/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: selectedItem, ...itemConfig })
      });
      const data = await res.json();
      
      if (data.code === 0) {
        toast.success("Item tracking configured");
        setShowConfigDialog(false);
        fetchSummaries();
      } else {
        toast.error(data.detail || "Failed to configure");
      }
    } catch (e) {
      toast.error("Error configuring item");
    }
  };

  const formatDate = (date) => date ? new Date(date).toLocaleDateString("en-IN") : "-";
  const formatCurrency = (amount) => `₹${(amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;

  return (
    <div className="space-y-6" data-testid="serial-batch-tracking-page">
      <PageHeader
        title="Serial & Batch Tracking"
        description="Track individual serial numbers and batch/lot numbers for inventory items"
        icon={Barcode}
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-white border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/[0.45] uppercase tracking-wide">Serial Numbers</p>
                <p className="text-2xl font-bold text-bw-blue">{serialSummary?.total_serials || 0}</p>
                <p className="text-xs text-green-600">{serialSummary?.available || 0} available</p>
              </div>
              <Hash className="h-10 w-10 text-blue-300" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-white border-purple-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/[0.45] uppercase tracking-wide">Batch Numbers</p>
                <p className="text-2xl font-bold text-bw-purple">{batchSummary?.total_batches || 0}</p>
                <p className="text-xs text-green-600">{batchSummary?.active_batches || 0} active</p>
              </div>
              <Package className="h-10 w-10 text-purple-300" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-50 to-white border-orange-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/[0.45] uppercase tracking-wide">Expiring Soon</p>
                <p className="text-2xl font-bold text-bw-orange">{batchSummary?.expiring_soon || 0}</p>
                <p className="text-xs text-bw-white/[0.45]">within 30 days</p>
              </div>
              <AlertTriangle className="h-10 w-10 text-orange-300" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-white border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-bw-white/[0.45] uppercase tracking-wide">Tracked Items</p>
                <p className="text-2xl font-bold text-green-700">{trackingItems.length}</p>
                <p className="text-xs text-bw-white/[0.45]">with tracking enabled</p>
              </div>
              <Settings className="h-10 w-10 text-green-300" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Expiring Batches Alert */}
      {expiringBatches.length > 0 && (
        <Card className="border-orange-300 bg-bw-orange/[0.08]">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-bw-orange mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-orange-800">Batches Expiring Soon</p>
                <p className="text-sm text-bw-orange mt-1">
                  {expiringBatches.length} batch(es) will expire within the next 30 days. 
                  Review and take necessary action.
                </p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {expiringBatches.slice(0, 5).map(batch => (
                    <Badge key={batch.batch_id} variant="outline" className="border-orange-400 text-bw-orange">
                      {batch.batch_number} ({batch.days_to_expiry}d)
                    </Badge>
                  ))}
                  {expiringBatches.length > 5 && (
                    <Badge variant="outline" className="border-orange-400 text-bw-orange">
                      +{expiringBatches.length - 5} more
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between mb-4">
          <TabsList>
            <TabsTrigger value="serials" className="flex items-center gap-2">
              <Hash className="h-4 w-4" /> Serial Numbers
            </TabsTrigger>
            <TabsTrigger value="batches" className="flex items-center gap-2">
              <Package className="h-4 w-4" /> Batch Numbers
            </TabsTrigger>
            <TabsTrigger value="items" className="flex items-center gap-2">
              <Settings className="h-4 w-4" /> Tracked Items
            </TabsTrigger>
          </TabsList>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => activeTab === "serials" ? fetchSerials() : fetchBatches()}>
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
            {activeTab === "serials" && (
              <>
                <Button size="sm" variant="outline" onClick={() => setShowBulkSerialDialog(true)}>
                  <Upload className="h-4 w-4 mr-1" /> Bulk Create
                </Button>
                <Button size="sm" onClick={() => setShowCreateSerialDialog(true)}>
                  <Plus className="h-4 w-4 mr-1" /> Add Serial
                </Button>
              </>
            )}
            {activeTab === "batches" && (
              <Button size="sm" onClick={() => setShowCreateBatchDialog(true)}>
                <Plus className="h-4 w-4 mr-1" /> Add Batch
              </Button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-bw-white/[0.45]" />
            <Input
              placeholder={activeTab === "serials" ? "Search serial numbers..." : "Search batch numbers..."}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
              data-testid="tracking-search-input"
            />
          </div>
          <Select value={statusFilter || "all"} onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              {activeTab === "serials" ? (
                <>
                  <SelectItem value="available">Available</SelectItem>
                  <SelectItem value="sold">Sold</SelectItem>
                  <SelectItem value="returned">Returned</SelectItem>
                  <SelectItem value="damaged">Damaged</SelectItem>
                  <SelectItem value="reserved">Reserved</SelectItem>
                </>
              ) : (
                <>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="depleted">Depleted</SelectItem>
                  <SelectItem value="expired">Expired</SelectItem>
                </>
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Serial Numbers Tab */}
        <TabsContent value="serials">
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-6 w-6 animate-spin text-bw-white/[0.45]" />
                </div>
              ) : serials.length === 0 ? (
                <div className="text-center py-12 text-bw-white/[0.45]">
                  <Hash className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No serial numbers found</p>
                  <p className="text-sm mt-1">Create serial numbers to track individual units</p>
                </div>
              ) : (
                <div className="divide-y">
                  {serials.map(serial => (
                    <div 
                      key={serial.serial_id}
                      className="flex items-center justify-between p-4 hover:bg-bw-panel cursor-pointer"
                      onClick={() => setSelectedSerial(serial)}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                          <Hash className="h-5 w-5 text-bw-blue" />
                        </div>
                        <div>
                          <p className="font-medium">{serial.serial_number}</p>
                          <p className="text-sm text-bw-white/[0.45]">{serial.item_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        {serial.warranty_expiry && (
                          <div className="text-right text-sm">
                            <p className="text-bw-white/[0.45]">Warranty</p>
                            <p>{formatDate(serial.warranty_expiry)}</p>
                          </div>
                        )}
                        <Badge className={statusColors[serial.status]}>{serial.status}</Badge>
                        <ChevronRight className="h-5 w-5 text-bw-white/[0.45]" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Batch Numbers Tab */}
        <TabsContent value="batches">
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-6 w-6 animate-spin text-bw-white/[0.45]" />
                </div>
              ) : batches.length === 0 ? (
                <div className="text-center py-12 text-bw-white/[0.45]">
                  <Package className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No batch numbers found</p>
                  <p className="text-sm mt-1">Create batch/lot numbers to track inventory batches</p>
                </div>
              ) : (
                <div className="divide-y">
                  {batches.map(batch => (
                    <div 
                      key={batch.batch_id}
                      className="flex items-center justify-between p-4 hover:bg-bw-panel cursor-pointer"
                      onClick={() => setSelectedBatch(batch)}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          batch.is_expired ? "bg-red-100" : batch.days_to_expiry && batch.days_to_expiry < 30 ? "bg-orange-100" : "bg-purple-100"
                        }`}>
                          <Package className={`h-5 w-5 ${
                            batch.is_expired ? "text-red-600" : batch.days_to_expiry && batch.days_to_expiry < 30 ? "text-bw-orange" : "text-purple-600"
                          }`} />
                        </div>
                        <div>
                          <p className="font-medium">{batch.batch_number}</p>
                          <p className="text-sm text-bw-white/[0.45]">{batch.item_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="font-medium">{batch.available_quantity} / {batch.quantity}</p>
                          <p className="text-xs text-bw-white/[0.45]">available / total</p>
                        </div>
                        {batch.expiry_date && (
                          <div className="text-right text-sm">
                            <p className={batch.is_expired ? "text-red-600" : batch.days_to_expiry < 30 ? "text-bw-orange" : "text-bw-white/[0.45]"}>
                              {batch.is_expired ? "Expired" : `${batch.days_to_expiry}d left`}
                            </p>
                            <p className="text-xs text-bw-white/[0.45]">{formatDate(batch.expiry_date)}</p>
                          </div>
                        )}
                        <Badge className={statusColors[batch.status]}>{batch.status}</Badge>
                        <ChevronRight className="h-5 w-5 text-bw-white/[0.45]" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tracked Items Tab */}
        <TabsContent value="items">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Items with Tracking Enabled</CardTitle>
              <CardDescription>Configure serial or batch tracking for inventory items</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {trackingItems.length === 0 ? (
                <div className="text-center py-12 text-bw-white/[0.45]">
                  <Settings className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No items with tracking enabled</p>
                  <p className="text-sm mt-1">Configure tracking from the Items module</p>
                </div>
              ) : (
                <div className="divide-y">
                  {trackingItems.map(item => (
                    <div key={item.item_id} className="flex items-center justify-between p-4 hover:bg-bw-panel">
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-sm text-bw-white/[0.45]">{item.sku || "No SKU"}</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex gap-2">
                          {item.enable_serial_tracking && (
                            <Badge variant="outline" className="border-blue-300 text-bw-blue">
                              <Hash className="h-3 w-3 mr-1" /> Serial ({item.serial_count || 0})
                            </Badge>
                          )}
                          {item.enable_batch_tracking && (
                            <Badge variant="outline" className="border-purple-300 text-bw-purple">
                              <Package className="h-3 w-3 mr-1" /> Batch ({item.batch_count || 0})
                            </Badge>
                          )}
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => {
                            setSelectedItem(item.item_id);
                            setItemConfig({
                              enable_serial: item.enable_serial_tracking || false,
                              enable_batch: item.enable_batch_tracking || false,
                              serial_prefix: item.serial_prefix || "",
                              batch_prefix: item.batch_prefix || "",
                              require_on_sale: item.require_tracking_on_sale !== false,
                              require_on_purchase: item.require_tracking_on_purchase !== false,
                              auto_generate_serial: item.auto_generate_serial || false
                            });
                            setShowConfigDialog(true);
                          }}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Serial Dialog */}
      <Dialog open={showCreateSerialDialog} onOpenChange={setShowCreateSerialDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Serial Number</DialogTitle>
            <DialogDescription>Create a new serial number for an inventory item</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Item ID *</Label>
              <Input
                placeholder="Enter item ID"
                value={newSerial.item_id}
                onChange={(e) => setNewSerial({ ...newSerial, item_id: e.target.value })}
                data-testid="new-serial-item-id"
              />
            </div>
            <div className="space-y-2">
              <Label>Serial Number *</Label>
              <Input
                placeholder="e.g., SN-001234"
                value={newSerial.serial_number}
                onChange={(e) => setNewSerial({ ...newSerial, serial_number: e.target.value })}
                data-testid="new-serial-number"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Cost Price</Label>
                <Input
                  type="number"
                  value={newSerial.cost_price}
                  onChange={(e) => setNewSerial({ ...newSerial, cost_price: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label>Warranty Expiry</Label>
                <Input
                  type="date"
                  value={newSerial.warranty_expiry}
                  onChange={(e) => setNewSerial({ ...newSerial, warranty_expiry: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Input
                placeholder="Optional notes"
                value={newSerial.notes}
                onChange={(e) => setNewSerial({ ...newSerial, notes: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateSerialDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateSerial} data-testid="create-serial-btn">Create Serial</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Create Serials Dialog */}
      <Dialog open={showBulkSerialDialog} onOpenChange={setShowBulkSerialDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Create Serial Numbers</DialogTitle>
            <DialogDescription>Generate multiple serial numbers with auto-numbering</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Item ID *</Label>
              <Input
                placeholder="Enter item ID"
                value={bulkSerial.item_id}
                onChange={(e) => setBulkSerial({ ...bulkSerial, item_id: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Prefix</Label>
                <Input
                  placeholder="e.g., SN-"
                  value={bulkSerial.prefix}
                  onChange={(e) => setBulkSerial({ ...bulkSerial, prefix: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Start Number</Label>
                <Input
                  type="number"
                  value={bulkSerial.start_number}
                  onChange={(e) => setBulkSerial({ ...bulkSerial, start_number: parseInt(e.target.value) || 1 })}
                />
              </div>
              <div className="space-y-2">
                <Label>Count *</Label>
                <Input
                  type="number"
                  min="1"
                  max="1000"
                  value={bulkSerial.count}
                  onChange={(e) => setBulkSerial({ ...bulkSerial, count: parseInt(e.target.value) || 1 })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Cost Price (per unit)</Label>
              <Input
                type="number"
                value={bulkSerial.cost_price}
                onChange={(e) => setBulkSerial({ ...bulkSerial, cost_price: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div className="bg-bw-panel p-3 rounded-lg text-sm">
              <p className="font-medium">Preview:</p>
              <p className="text-bw-white/35">
                {bulkSerial.prefix}{String(bulkSerial.start_number).padStart(6, '0')} to {bulkSerial.prefix}{String(bulkSerial.start_number + bulkSerial.count - 1).padStart(6, '0')}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBulkSerialDialog(false)}>Cancel</Button>
            <Button onClick={handleBulkCreateSerials}>Create {bulkSerial.count} Serials</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Batch Dialog */}
      <Dialog open={showCreateBatchDialog} onOpenChange={setShowCreateBatchDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Batch Number</DialogTitle>
            <DialogDescription>Create a new batch/lot number for an inventory item</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Item ID *</Label>
              <Input
                placeholder="Enter item ID"
                value={newBatch.item_id}
                onChange={(e) => setNewBatch({ ...newBatch, item_id: e.target.value })}
                data-testid="new-batch-item-id"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Batch Number *</Label>
                <Input
                  placeholder="e.g., LOT-2026-001"
                  value={newBatch.batch_number}
                  onChange={(e) => setNewBatch({ ...newBatch, batch_number: e.target.value })}
                  data-testid="new-batch-number"
                />
              </div>
              <div className="space-y-2">
                <Label>Quantity *</Label>
                <Input
                  type="number"
                  value={newBatch.quantity}
                  onChange={(e) => setNewBatch({ ...newBatch, quantity: parseFloat(e.target.value) || 0 })}
                  data-testid="new-batch-quantity"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Manufacturing Date</Label>
                <Input
                  type="date"
                  value={newBatch.manufacturing_date}
                  onChange={(e) => setNewBatch({ ...newBatch, manufacturing_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Expiry Date</Label>
                <Input
                  type="date"
                  value={newBatch.expiry_date}
                  onChange={(e) => setNewBatch({ ...newBatch, expiry_date: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Cost Price (per unit)</Label>
              <Input
                type="number"
                value={newBatch.cost_price}
                onChange={(e) => setNewBatch({ ...newBatch, cost_price: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Input
                placeholder="Optional notes"
                value={newBatch.notes}
                onChange={(e) => setNewBatch({ ...newBatch, notes: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateBatchDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateBatch} data-testid="create-batch-btn">Create Batch</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Item Config Dialog */}
      <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Configure Item Tracking</DialogTitle>
            <DialogDescription>Enable and configure serial or batch tracking for this item</DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable Serial Tracking</Label>
                <p className="text-sm text-bw-white/[0.45]">Track individual units with unique serial numbers</p>
              </div>
              <Switch
                checked={itemConfig.enable_serial}
                onCheckedChange={(v) => setItemConfig({ ...itemConfig, enable_serial: v })}
              />
            </div>
            
            {itemConfig.enable_serial && (
              <div className="pl-4 border-l-2 border-blue-200 space-y-4">
                <div className="space-y-2">
                  <Label>Serial Prefix</Label>
                  <Input
                    placeholder="e.g., SN-"
                    value={itemConfig.serial_prefix}
                    onChange={(e) => setItemConfig({ ...itemConfig, serial_prefix: e.target.value })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Auto-generate Serial Numbers</Label>
                  <Switch
                    checked={itemConfig.auto_generate_serial}
                    onCheckedChange={(v) => setItemConfig({ ...itemConfig, auto_generate_serial: v })}
                  />
                </div>
              </div>
            )}
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable Batch Tracking</Label>
                <p className="text-sm text-bw-white/[0.45]">Track inventory in batches with expiry dates</p>
              </div>
              <Switch
                checked={itemConfig.enable_batch}
                onCheckedChange={(v) => setItemConfig({ ...itemConfig, enable_batch: v })}
              />
            </div>
            
            {itemConfig.enable_batch && (
              <div className="pl-4 border-l-2 border-purple-200 space-y-4">
                <div className="space-y-2">
                  <Label>Batch Prefix</Label>
                  <Input
                    placeholder="e.g., LOT-"
                    value={itemConfig.batch_prefix}
                    onChange={(e) => setItemConfig({ ...itemConfig, batch_prefix: e.target.value })}
                  />
                </div>
              </div>
            )}
            
            <Separator />
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Require on Sale</Label>
                <Switch
                  checked={itemConfig.require_on_sale}
                  onCheckedChange={(v) => setItemConfig({ ...itemConfig, require_on_sale: v })}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Require on Purchase</Label>
                <Switch
                  checked={itemConfig.require_on_purchase}
                  onCheckedChange={(v) => setItemConfig({ ...itemConfig, require_on_purchase: v })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfigDialog(false)}>Cancel</Button>
            <Button onClick={handleConfigureItem}>Save Configuration</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
