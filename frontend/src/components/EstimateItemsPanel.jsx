/**
 * EstimateItemsPanel - Job Card Estimate Management
 * 
 * This component manages estimate line items for service tickets.
 * Key features:
 * - Auto-creates estimate on mount (if ticket has technician)
 * - Add/Edit/Remove line items (parts, labour, fees)
 * - Real-time total calculations (server-driven)
 * - Status management (draft, sent, approved, locked)
 * - Optimistic concurrency with conflict resolution
 * - Parts catalog search integration
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { AlertCircle, Lock, Plus, Trash2, Send, Check, Pencil, ExternalLink, RefreshCw, Package, Wrench, Receipt } from "lucide-react";
import { toast } from "sonner";
import { API } from "@/App";

// Status colors for estimate
const estimateStatusColors = {
  draft: "bg-yellow-100 text-yellow-800 border-yellow-300",
  sent: "bg-blue-100 text-blue-800 border-blue-300",
  approved: "bg-green-100 text-green-800 border-green-300",
  rejected: "bg-red-100 text-red-800 border-red-300",
  converted: "bg-purple-100 text-purple-800 border-purple-300",
  void: "bg-gray-100 text-gray-800 border-gray-300",
};

const estimateStatusLabels = {
  draft: "Draft",
  sent: "Sent to Customer",
  approved: "Approved",
  rejected: "Rejected",
  converted: "Converted to Invoice",
  void: "Void",
};

const lineItemTypeIcons = {
  part: Package,
  labour: Wrench,
  fee: Receipt,
};

export default function EstimateItemsPanel({ 
  ticket, 
  user, 
  organizationId,
  onEstimateChange,  // Callback when estimate changes
}) {
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Add item dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedLineItem, setSelectedLineItem] = useState(null);
  
  // New item form state
  const [newItem, setNewItem] = useState({
    type: "part",
    name: "",
    description: "",
    qty: 1,
    unit: "pcs",
    unit_price: 0,
    discount: 0,
    tax_rate: 18,
    item_id: null,
    hsn_code: "",
  });
  
  // Parts catalog search
  const [itemSearch, setItemSearch] = useState("");
  const [catalogItems, setCatalogItems] = useState([]);
  const [searchOpen, setSearchOpen] = useState(false);
  
  // Conflict state
  const [conflictData, setConflictData] = useState(null);

  const token = localStorage.getItem("token");
  const isAdmin = user?.role === "admin";
  const isManager = user?.role === "manager";
  const isTechnician = user?.role === "technician";
  const canEdit = !estimate?.locked_at && (isAdmin || isManager || isTechnician);
  const canApprove = isAdmin || isManager || isTechnician;
  const canLock = isAdmin || isManager;
  
  // Fetch or create estimate
  const ensureEstimate = useCallback(async () => {
    if (!ticket?.ticket_id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API}/tickets/${ticket.ticket_id}/estimate/ensure`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Organization-ID": organizationId || ticket.organization_id,
          "Content-Type": "application/json",
        },
      });
      
      if (!response.ok) {
        throw new Error("Failed to load estimate");
      }
      
      const data = await response.json();
      setEstimate(data.estimate);
      
      if (onEstimateChange) {
        onEstimateChange(data.estimate);
      }
    } catch (err) {
      console.error("Error ensuring estimate:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [ticket?.ticket_id, token, organizationId, onEstimateChange]);
  
  // Load estimate on mount
  useEffect(() => {
    // Only load if technician is assigned
    if (ticket?.assigned_technician_id) {
      ensureEstimate();
    }
  }, [ticket?.ticket_id, ticket?.assigned_technician_id, ensureEstimate]);
  
  // Search parts catalog
  const searchCatalog = useCallback(async (query) => {
    try {
      // Build URL with or without search query
      let url = `${API}/items-enhanced/?per_page=20&item_type=inventory`;
      if (query && query.length >= 2) {
        url += `&search=${encodeURIComponent(query)}`;
      }
      
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Organization-ID": organizationId || ticket.organization_id,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setCatalogItems(data.items || []);
      }
    } catch (err) {
      console.error("Error searching catalog:", err);
    }
  }, [token, organizationId, ticket?.organization_id]);
  
  // Load initial items when popover opens
  const loadInitialCatalog = useCallback(() => {
    if (catalogItems.length === 0) {
      searchCatalog("");
    }
  }, [searchCatalog, catalogItems.length]);
  
  // Add line item
  const handleAddLineItem = async () => {
    if (!newItem.name) {
      toast.error("Item name is required");
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/ticket-estimates/${estimate.estimate_id}/line-items`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-Organization-ID": organizationId || ticket.organization_id,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...newItem,
            version: estimate.version,
          }),
        }
      );
      
      if (response.status === 409) {
        // Concurrency conflict
        const data = await response.json();
        setConflictData(data.detail?.current_estimate);
        toast.error("Estimate was modified. Refreshing...");
        await ensureEstimate();
        return;
      }
      
      if (response.status === 423) {
        toast.error("Estimate is locked and cannot be modified");
        return;
      }
      
      if (!response.ok) {
        throw new Error("Failed to add item");
      }
      
      const data = await response.json();
      setEstimate(data.estimate);
      setAddDialogOpen(false);
      resetNewItem();
      toast.success("Item added successfully");
      
      if (onEstimateChange) {
        onEstimateChange(data.estimate);
      }
    } catch (err) {
      console.error("Error adding line item:", err);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Update line item
  const handleUpdateLineItem = async () => {
    if (!selectedLineItem) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/ticket-estimates/${estimate.estimate_id}/line-items/${selectedLineItem.line_item_id}`,
        {
          method: "PATCH",
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-Organization-ID": organizationId || ticket.organization_id,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: selectedLineItem.name,
            description: selectedLineItem.description,
            qty: selectedLineItem.qty,
            unit_price: selectedLineItem.unit_price,
            discount: selectedLineItem.discount,
            tax_rate: selectedLineItem.tax_rate,
            version: estimate.version,
          }),
        }
      );
      
      if (response.status === 409) {
        toast.error("Estimate was modified. Refreshing...");
        await ensureEstimate();
        return;
      }
      
      if (response.status === 423) {
        toast.error("Estimate is locked and cannot be modified");
        return;
      }
      
      if (!response.ok) {
        throw new Error("Failed to update item");
      }
      
      const data = await response.json();
      setEstimate(data.estimate);
      setEditDialogOpen(false);
      setSelectedLineItem(null);
      toast.success("Item updated successfully");
      
      if (onEstimateChange) {
        onEstimateChange(data.estimate);
      }
    } catch (err) {
      console.error("Error updating line item:", err);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Delete line item
  const handleDeleteLineItem = async (lineItemId) => {
    if (!confirm("Are you sure you want to remove this item?")) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/ticket-estimates/${estimate.estimate_id}/line-items/${lineItemId}?version=${estimate.version}`,
        {
          method: "DELETE",
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-Organization-ID": organizationId || ticket.organization_id,
          },
        }
      );
      
      if (response.status === 409) {
        toast.error("Estimate was modified. Refreshing...");
        await ensureEstimate();
        return;
      }
      
      if (response.status === 423) {
        toast.error("Estimate is locked and cannot be modified");
        return;
      }
      
      if (!response.ok) {
        throw new Error("Failed to delete item");
      }
      
      const data = await response.json();
      setEstimate(data.estimate);
      toast.success("Item removed");
      
      if (onEstimateChange) {
        onEstimateChange(data.estimate);
      }
    } catch (err) {
      console.error("Error deleting line item:", err);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Send estimate
  const handleSendEstimate = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/ticket-estimates/${estimate.estimate_id}/send`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-Organization-ID": organizationId || ticket.organization_id,
            "Content-Type": "application/json",
          },
        }
      );
      
      if (!response.ok) {
        throw new Error("Failed to send estimate");
      }
      
      const data = await response.json();
      setEstimate(data.estimate);
      toast.success("Estimate sent to customer");
      
      if (onEstimateChange) {
        onEstimateChange(data.estimate);
      }
    } catch (err) {
      console.error("Error sending estimate:", err);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Approve estimate
  const handleApproveEstimate = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/ticket-estimates/${estimate.estimate_id}/approve`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-Organization-ID": organizationId || ticket.organization_id,
            "Content-Type": "application/json",
          },
        }
      );
      
      if (!response.ok) {
        throw new Error("Failed to approve estimate");
      }
      
      const data = await response.json();
      setEstimate(data.estimate);
      toast.success("Estimate approved!");
      
      if (onEstimateChange) {
        onEstimateChange(data.estimate);
      }
    } catch (err) {
      console.error("Error approving estimate:", err);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Lock estimate
  const handleLockEstimate = async () => {
    const reason = prompt("Enter lock reason:");
    if (!reason) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/ticket-estimates/${estimate.estimate_id}/lock`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-Organization-ID": organizationId || ticket.organization_id,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ reason }),
        }
      );
      
      if (!response.ok) {
        throw new Error("Failed to lock estimate");
      }
      
      const data = await response.json();
      setEstimate(data.estimate);
      toast.success("Estimate locked");
      
      if (onEstimateChange) {
        onEstimateChange(data.estimate);
      }
    } catch (err) {
      console.error("Error locking estimate:", err);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Reset new item form
  const resetNewItem = () => {
    setNewItem({
      type: "part",
      name: "",
      description: "",
      qty: 1,
      unit: "pcs",
      unit_price: 0,
      discount: 0,
      tax_rate: 18,
      item_id: null,
      hsn_code: "",
    });
    setItemSearch("");
    setCatalogItems([]);
  };
  
  // Select item from catalog
  const handleSelectCatalogItem = (item) => {
    setNewItem({
      ...newItem,
      name: item.name,
      description: item.description || "",
      unit_price: item.rate || item.selling_price || 0,
      item_id: item.item_id,
      hsn_code: item.hsn_sac_code || item.hsn_code || "",
      tax_rate: item.tax_percentage || 18,
      unit: item.unit || "pcs",
    });
    setSearchOpen(false);
    setItemSearch("");
  };
  
  // If no technician assigned, show message
  if (!ticket?.assigned_technician_id) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Estimate Items</CardTitle>
          <CardDescription>Assign a technician to create an estimate.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-24 text-muted-foreground">
            <AlertCircle className="h-5 w-5 mr-2" />
            Technician must be assigned before adding estimate items.
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Loading state
  if (loading && !estimate) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Estimate Items</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-24">
            <RefreshCw className="h-5 w-5 animate-spin mr-2" />
            Loading estimate...
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Error state
  if (error && !estimate) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Estimate Items</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-24 text-destructive">
            <AlertCircle className="h-5 w-5 mr-2" />
            {error}
            <Button variant="outline" size="sm" className="mt-2" onClick={ensureEstimate}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (!estimate) {
    return null;
  }
  
  const lineItems = estimate.line_items || [];
  const TypeIcon = lineItemTypeIcons[newItem.type] || Package;
  
  return (
    <Card data-testid="estimate-items-panel">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Estimate Items
              <Badge 
                variant="outline" 
                className={estimateStatusColors[estimate.status] || ""}
              >
                {estimateStatusLabels[estimate.status] || estimate.status}
              </Badge>
            </CardTitle>
            <CardDescription className="flex items-center gap-2 mt-1">
              <span className="font-mono text-xs">{estimate.estimate_number}</span>
              <a 
                href={`/estimates/${estimate.estimate_id}`}
                className="text-xs text-primary flex items-center gap-1 hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                Open in Estimates <ExternalLink className="h-3 w-3" />
              </a>
            </CardDescription>
          </div>
          
          {/* Refresh button */}
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={ensureEstimate}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
        
        {/* Lock Banner */}
        {estimate.locked_at && (
          <div className="mt-2 p-3 bg-orange-50 border border-orange-200 rounded-lg flex items-center gap-2 text-orange-800">
            <Lock className="h-4 w-4" />
            <div className="text-sm">
              <strong>Estimate Locked</strong>
              <span className="ml-2">{estimate.lock_reason}</span>
              <span className="text-xs ml-2 text-orange-600">
                by {estimate.locked_by_name} on {new Date(estimate.locked_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        {/* Add Item Button */}
        {canEdit && (
          <div className="mb-4">
            <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="w-full" data-testid="add-estimate-item-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Item
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Add Item to Estimate</DialogTitle>
                  <DialogDescription>
                    Add a part, labour charge, or fee to the estimate.
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4 py-4">
                  {/* Type Selection */}
                  <div className="space-y-2">
                    <Label>Item Type</Label>
                    <Select 
                      value={newItem.type} 
                      onValueChange={(v) => setNewItem({ ...newItem, type: v, name: "", item_id: null })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="part">
                          <div className="flex items-center gap-2">
                            <Package className="h-4 w-4" /> Part
                          </div>
                        </SelectItem>
                        <SelectItem value="labour">
                          <div className="flex items-center gap-2">
                            <Wrench className="h-4 w-4" /> Labour
                          </div>
                        </SelectItem>
                        <SelectItem value="fee">
                          <div className="flex items-center gap-2">
                            <Receipt className="h-4 w-4" /> Fee
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Parts Catalog Search (only for parts) */}
                  {newItem.type === "part" && (
                    <div className="space-y-2">
                      <Label>Search Parts Catalog</Label>
                      <Popover open={searchOpen} onOpenChange={setSearchOpen}>
                        <PopoverTrigger asChild>
                          <Button variant="outline" className="w-full justify-start">
                            {newItem.item_id ? newItem.name : "Search parts..."}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="p-0 w-[350px]">
                          <Command>
                            <CommandInput 
                              placeholder="Search parts..." 
                              value={itemSearch}
                              onValueChange={(v) => {
                                setItemSearch(v);
                                searchCatalog(v);
                              }}
                            />
                            <CommandList>
                              <CommandEmpty>No parts found</CommandEmpty>
                              <CommandGroup>
                                {catalogItems.map((item) => (
                                  <CommandItem
                                    key={item.item_id}
                                    onSelect={() => handleSelectCatalogItem(item)}
                                  >
                                    <div className="flex justify-between w-full">
                                      <span className="truncate">{item.name}</span>
                                      <span className="text-muted-foreground">
                                        ₹{(item.rate || item.selling_price || 0).toLocaleString()}
                                      </span>
                                    </div>
                                  </CommandItem>
                                ))}
                              </CommandGroup>
                            </CommandList>
                          </Command>
                        </PopoverContent>
                      </Popover>
                    </div>
                  )}
                  
                  {/* Name */}
                  <div className="space-y-2">
                    <Label>Name *</Label>
                    <Input 
                      value={newItem.name}
                      onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                      placeholder={
                        newItem.type === "part" ? "Part name" :
                        newItem.type === "labour" ? "e.g., Installation Labour" :
                        "e.g., Diagnosis Fee"
                      }
                    />
                  </div>
                  
                  {/* Description */}
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Input 
                      value={newItem.description}
                      onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                      placeholder="Optional description"
                    />
                  </div>
                  
                  {/* Qty, Unit, Price Grid */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-2">
                      <Label>Quantity</Label>
                      <Input 
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={newItem.qty}
                        onChange={(e) => setNewItem({ ...newItem, qty: parseFloat(e.target.value) || 1 })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Unit</Label>
                      <Select 
                        value={newItem.unit} 
                        onValueChange={(v) => setNewItem({ ...newItem, unit: v })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="pcs">pcs</SelectItem>
                          <SelectItem value="hrs">hrs</SelectItem>
                          <SelectItem value="kg">kg</SelectItem>
                          <SelectItem value="ltr">ltr</SelectItem>
                          <SelectItem value="set">set</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Unit Price (₹)</Label>
                      <Input 
                        type="number"
                        min="0"
                        step="0.01"
                        value={newItem.unit_price}
                        onChange={(e) => setNewItem({ ...newItem, unit_price: parseFloat(e.target.value) || 0 })}
                      />
                    </div>
                  </div>
                  
                  {/* Discount and Tax */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label>Discount (₹)</Label>
                      <Input 
                        type="number"
                        min="0"
                        step="0.01"
                        value={newItem.discount}
                        onChange={(e) => setNewItem({ ...newItem, discount: parseFloat(e.target.value) || 0 })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Tax Rate (%)</Label>
                      <Select 
                        value={String(newItem.tax_rate)} 
                        onValueChange={(v) => setNewItem({ ...newItem, tax_rate: parseFloat(v) })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">0%</SelectItem>
                          <SelectItem value="5">5%</SelectItem>
                          <SelectItem value="12">12%</SelectItem>
                          <SelectItem value="18">18%</SelectItem>
                          <SelectItem value="28">28%</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  {/* Line Total Preview */}
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="flex justify-between text-sm">
                      <span>Line Total</span>
                      <span className="font-mono font-semibold">
                        ₹{(
                          (newItem.qty * newItem.unit_price - newItem.discount) * 
                          (1 + newItem.tax_rate / 100)
                        ).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                </div>
                
                <DialogFooter>
                  <Button variant="outline" onClick={() => { setAddDialogOpen(false); resetNewItem(); }}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddLineItem} disabled={loading || !newItem.name}>
                    {loading ? "Adding..." : "Add Item"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        )}
        
        {/* Items Table */}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Item</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-right">Qty</TableHead>
              <TableHead className="text-right">Rate</TableHead>
              <TableHead className="text-right">Tax</TableHead>
              <TableHead className="text-right">Total</TableHead>
              {canEdit && <TableHead className="text-right w-[100px]">Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {lineItems.map((item) => {
              const ItemIcon = lineItemTypeIcons[item.type] || Package;
              return (
                <TableRow key={item.line_item_id} data-testid={`line-item-${item.line_item_id}`}>
                  <TableCell>
                    <div>
                      <p className="font-medium">{item.name}</p>
                      {item.description && (
                        <p className="text-xs text-muted-foreground">{item.description}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize flex items-center gap-1 w-fit">
                      <ItemIcon className="h-3 w-3" />
                      {item.type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {item.qty} {item.unit}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    ₹{item.unit_price?.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    {item.tax_rate}%
                  </TableCell>
                  <TableCell className="text-right font-mono font-semibold">
                    ₹{item.line_total?.toLocaleString()}
                  </TableCell>
                  {canEdit && (
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => {
                            setSelectedLineItem({ ...item });
                            setEditDialogOpen(true);
                          }}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => handleDeleteLineItem(item.line_item_id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              );
            })}
            {lineItems.length === 0 && (
              <TableRow>
                <TableCell colSpan={canEdit ? 7 : 6} className="text-center h-24 text-muted-foreground">
                  No items added yet. Click "Add Item" to get started.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
      
      <CardFooter className="flex-col">
        {/* Totals */}
        <div className="w-full max-w-xs ml-auto space-y-2 text-sm mb-4">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span className="font-mono">₹{estimate.subtotal?.toLocaleString()}</span>
          </div>
          {estimate.discount_total > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discount</span>
              <span className="font-mono">-₹{estimate.discount_total?.toLocaleString()}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span>Tax (GST)</span>
            <span className="font-mono">₹{estimate.tax_total?.toLocaleString()}</span>
          </div>
          <Separator />
          <div className="flex justify-between font-bold text-lg">
            <span>Grand Total</span>
            <span className="font-mono">₹{estimate.grand_total?.toLocaleString()}</span>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="w-full flex flex-wrap justify-end gap-2 pt-4 border-t">
          {/* Send Estimate - When draft and has items */}
          {estimate.status === "draft" && lineItems.length > 0 && canEdit && (
            <Button onClick={handleSendEstimate} disabled={loading} variant="outline">
              <Send className="h-4 w-4 mr-2" />
              Send Estimate
            </Button>
          )}
          
          {/* Approve - When draft or sent */}
          {(estimate.status === "draft" || estimate.status === "sent") && lineItems.length > 0 && canApprove && (
            <Button onClick={handleApproveEstimate} disabled={loading}>
              <Check className="h-4 w-4 mr-2" />
              Approve Estimate
            </Button>
          )}
          
          {/* Lock - Admin/Manager only, when not locked */}
          {!estimate.locked_at && estimate.status === "approved" && canLock && (
            <Button onClick={handleLockEstimate} disabled={loading} variant="destructive">
              <Lock className="h-4 w-4 mr-2" />
              Lock Estimate
            </Button>
          )}
        </div>
      </CardFooter>
      
      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Line Item</DialogTitle>
          </DialogHeader>
          
          {selectedLineItem && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input 
                  value={selectedLineItem.name}
                  onChange={(e) => setSelectedLineItem({ ...selectedLineItem, name: e.target.value })}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Description</Label>
                <Input 
                  value={selectedLineItem.description || ""}
                  onChange={(e) => setSelectedLineItem({ ...selectedLineItem, description: e.target.value })}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Quantity</Label>
                  <Input 
                    type="number"
                    value={selectedLineItem.qty}
                    onChange={(e) => setSelectedLineItem({ ...selectedLineItem, qty: parseFloat(e.target.value) || 1 })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Unit Price (₹)</Label>
                  <Input 
                    type="number"
                    value={selectedLineItem.unit_price}
                    onChange={(e) => setSelectedLineItem({ ...selectedLineItem, unit_price: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Discount (₹)</Label>
                  <Input 
                    type="number"
                    value={selectedLineItem.discount || 0}
                    onChange={(e) => setSelectedLineItem({ ...selectedLineItem, discount: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tax Rate (%)</Label>
                  <Select 
                    value={String(selectedLineItem.tax_rate || 18)} 
                    onValueChange={(v) => setSelectedLineItem({ ...selectedLineItem, tax_rate: parseFloat(v) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">0%</SelectItem>
                      <SelectItem value="5">5%</SelectItem>
                      <SelectItem value="12">12%</SelectItem>
                      <SelectItem value="18">18%</SelectItem>
                      <SelectItem value="28">28%</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => { setEditDialogOpen(false); setSelectedLineItem(null); }}>
              Cancel
            </Button>
            <Button onClick={handleUpdateLineItem} disabled={loading}>
              {loading ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
