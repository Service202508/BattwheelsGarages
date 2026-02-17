import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { toast } from "sonner";
import { format } from "date-fns";
import { 
  Printer, CheckCircle, PlusCircle, Trash2, Send, Check, Play, Flag, 
  FileText, UserCog, Paperclip, Download, ExternalLink, Phone, Mail, MapPin, Brain
} from "lucide-react";
import { API } from "@/App";
import EFISidePanel from "./EFISidePanel";

const statusColors = {
  open: "bg-yellow-500",
  technician_assigned: "bg-blue-500",
  estimate_shared: "bg-purple-500",
  estimate_approved: "bg-indigo-500",
  in_progress: "bg-orange-500",
  resolved: "bg-green-500",
  closed: "bg-gray-500",
};

const statusLabels = {
  open: "Open",
  technician_assigned: "Technician Assigned",
  estimate_shared: "Estimate Shared",
  estimate_approved: "Estimate Approved",
  in_progress: "In Progress",
  resolved: "Resolved",
  closed: "Closed",
};

export default function JobCard({ ticket, user, onUpdate, onClose }) {
  const [localTicket, setLocalTicket] = useState(ticket);
  const [technicians, setTechnicians] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [services, setServices] = useState([]);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedTechnician, setSelectedTechnician] = useState("");
  const [itemsOpen, setItemsOpen] = useState(false);
  const [itemSearch, setItemSearch] = useState("");
  const [itemType, setItemType] = useState("part");
  const [selectedItem, setSelectedItem] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // EFI Panel state
  const [efiPanelOpen, setEfiPanelOpen] = useState(true);
  
  // Items state
  const [estimatedItems, setEstimatedItems] = useState(localTicket.estimated_items || { parts: [], services: [] });
  const [actualItems, setActualItems] = useState(localTicket.actual_items || { parts: [], services: [] });
  const [statusHistory, setStatusHistory] = useState(localTicket.status_history || []);

  useEffect(() => {
    fetchTechnicians();
    fetchInventory();
    fetchServices();
  }, []);

  useEffect(() => {
    setLocalTicket(ticket);
    setEstimatedItems(ticket.estimated_items || { parts: [], services: [] });
    setActualItems(ticket.actual_items || { parts: [], services: [] });
    setStatusHistory(ticket.status_history || []);
  }, [ticket]);

  const fetchTechnicians = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/technicians`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setTechnicians(data);
      }
    } catch (error) {
      console.error("Failed to fetch technicians:", error);
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
        const data = await response.json();
        setInventory(data);
      }
    } catch (error) {
      console.error("Failed to fetch inventory:", error);
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
        const data = await response.json();
        setServices(data);
      }
    } catch (error) {
      console.error("Failed to fetch services:", error);
    }
  };

  const updateTicketStatus = async (newStatus, additionalData = {}) => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/tickets/${localTicket.ticket_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ status: newStatus, ...additionalData }),
      });

      if (response.ok) {
        const updatedTicket = await response.json();
        setLocalTicket(updatedTicket);
        setStatusHistory(prev => [...prev, {
          status: newStatus,
          timestamp: new Date().toISOString(),
          updated_by: user?.name || "System"
        }]);
        toast.success(`Status updated to ${statusLabels[newStatus] || newStatus}`);
        onUpdate && onUpdate(updatedTicket);
      } else {
        toast.error("Failed to update status");
      }
    } catch (error) {
      toast.error("Error updating ticket");
    } finally {
      setLoading(false);
    }
  };

  const handleAssignTechnician = async () => {
    if (!selectedTechnician) {
      toast.error("Please select a technician");
      return;
    }
    
    const tech = technicians.find(t => t.user_id === selectedTechnician);
    await updateTicketStatus("technician_assigned", {
      assigned_technician_id: selectedTechnician,
      assigned_technician_name: tech?.name
    });
    setAssignDialogOpen(false);
  };

  const handleAddItem = () => {
    if (!selectedItem) return;
    
    const isEstimateStage = ["open", "technician_assigned", "estimate_shared"].includes(localTicket.status);
    const newItem = {
      item_id: selectedItem.item_id || selectedItem.service_id,
      name: selectedItem.name,
      sku: selectedItem.sku || "-",
      quantity: 1,
      unit_price: selectedItem.unit_price || selectedItem.base_price || 0,
      gst_rate: 18,
      type: itemType
    };

    if (isEstimateStage) {
      if (itemType === "part") {
        setEstimatedItems(prev => ({ ...prev, parts: [...prev.parts, newItem] }));
      } else {
        setEstimatedItems(prev => ({ ...prev, services: [...prev.services, newItem] }));
      }
    } else {
      if (itemType === "part") {
        setActualItems(prev => ({ ...prev, parts: [...prev.parts, newItem] }));
      } else {
        setActualItems(prev => ({ ...prev, services: [...prev.services, newItem] }));
      }
    }
    
    setSelectedItem(null);
    setItemsOpen(false);
  };

  const handleRemoveItem = (index, type, isEstimate) => {
    if (isEstimate) {
      if (type === "part") {
        setEstimatedItems(prev => ({ ...prev, parts: prev.parts.filter((_, i) => i !== index) }));
      } else {
        setEstimatedItems(prev => ({ ...prev, services: prev.services.filter((_, i) => i !== index) }));
      }
    } else {
      if (type === "part") {
        setActualItems(prev => ({ ...prev, parts: prev.parts.filter((_, i) => i !== index) }));
      } else {
        setActualItems(prev => ({ ...prev, services: prev.services.filter((_, i) => i !== index) }));
      }
    }
  };

  const handleShareEstimate = async () => {
    await updateTicketStatus("estimate_shared", { estimated_items: estimatedItems });
    toast.success("Estimate shared with customer");
  };

  const handleApproveEstimate = async () => {
    await updateTicketStatus("estimate_approved", { actual_items: estimatedItems });
    setActualItems(estimatedItems);
  };

  const handleStartWork = async () => {
    await updateTicketStatus("in_progress");
  };

  const handleMarkResolved = async () => {
    await updateTicketStatus("resolved", { actual_items: actualItems });
  };

  const handleGenerateInvoice = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/invoices`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({
          ticket_id: localTicket.ticket_id,
          customer_name: localTicket.customer_name,
          customer_email: localTicket.customer_email,
          vehicle_number: localTicket.vehicle_number,
          items: [...actualItems.parts, ...actualItems.services],
        }),
      });

      if (response.ok) {
        await updateTicketStatus("closed");
        toast.success("Invoice generated and ticket closed");
      } else {
        toast.error("Failed to generate invoice");
      }
    } catch (error) {
      toast.error("Error generating invoice");
    } finally {
      setLoading(false);
    }
  };

  // Calculate totals
  const isEstimateStage = ["open", "technician_assigned", "estimate_shared"].includes(localTicket.status);
  const items = isEstimateStage ? estimatedItems : actualItems;
  
  const partsSubtotal = (items.parts || []).reduce((sum, p) => sum + (p.unit_price * (p.quantity || 1)), 0);
  const servicesSubtotal = (items.services || []).reduce((sum, s) => sum + (s.unit_price * (s.quantity || 1)), 0);
  const subtotal = partsSubtotal + servicesSubtotal;
  
  const partsTax = (items.parts || []).reduce((sum, p) => sum + (p.unit_price * (p.quantity || 1) * (p.gst_rate || 18) / 100), 0);
  const servicesTax = (items.services || []).reduce((sum, s) => sum + (s.unit_price * (s.quantity || 1) * (s.gst_rate || 18) / 100), 0);
  const totalTax = partsTax + servicesTax;
  
  const grandTotal = subtotal + totalTax;

  const availableItems = itemType === "part" 
    ? inventory.filter(i => i.name.toLowerCase().includes(itemSearch.toLowerCase()))
    : services.filter(s => s.name.toLowerCase().includes(itemSearch.toLowerCase()));

  const isAdmin = user?.role === "admin";
  const isTechnician = user?.role === "technician";
  const isCustomer = user?.role === "customer";

  // Handle EFI estimate suggestion
  const handleEfiEstimateSuggested = (estimate) => {
    if (!estimate) return;
    
    // Convert EFI parts to estimate format
    const efiParts = (estimate.parts || estimate.parts_required || []).map(p => ({
      item_id: p.part_id || `efi_${Date.now()}`,
      name: p.name,
      sku: p.sku || "-",
      quantity: p.quantity || 1,
      unit_price: p.price || 0,
      gst_rate: 18,
      type: "part"
    }));

    // Add labor as service
    const laborService = {
      service_id: `labor_${Date.now()}`,
      name: estimate.resolution?.title || "Diagnostic Repair Labor",
      quantity: 1,
      unit_price: estimate.labor_total || (estimate.labor_hours || 1) * (estimate.labor_rate || 500),
      gst_rate: 18,
      type: "service"
    };

    // Update estimated items
    setEstimatedItems(prev => ({
      parts: [...prev.parts, ...efiParts],
      services: [...prev.services, laborService]
    }));

    toast.success("EFI estimate applied to job card");
  };

  return (
    <div className="flex h-full" data-testid="job-card">
      {/* Main Job Card Content */}
      <div className="flex-1 flex flex-col bg-muted/20 overflow-auto">
        <div className="p-4 space-y-4">
          {/* Header */}
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold">Battwheels OS</h1>
              <p className="text-muted-foreground text-sm">Service & Repair Center</p>
            </div>
            <div className="flex items-start gap-4">
              {/* EFI Toggle Button */}
              {(isTechnician || isAdmin) && (
                <Button
                  variant={efiPanelOpen ? "default" : "outline"}
                  size="sm"
                  onClick={() => setEfiPanelOpen(!efiPanelOpen)}
                  className="gap-2"
                  data-testid="efi-header-toggle"
                >
                  <Brain className="h-4 w-4" />
                  {efiPanelOpen ? "Hide" : "Show"} EFI
                </Button>
              )}
              <div className="text-right">
                <h3 className="text-xl font-semibold">Job Card</h3>
                <p className="text-muted-foreground font-mono">{localTicket.ticket_id}</p>
                <Badge className={statusColors[localTicket.status] || "bg-gray-500"}>
                  {statusLabels[localTicket.status] || localTicket.status}
                </Badge>
              </div>
            </div>
          </div>

          {/* Customer & Vehicle Details */}
          <Card>
            <CardHeader>
              <CardTitle>Customer & Vehicle Details</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-x-8 gap-y-4 text-sm">
              <div>
                <p className="text-muted-foreground">Customer</p>
                <p className="font-semibold">{localTicket.customer_name || "N/A"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Customer Type</p>
                <p className="font-semibold">{localTicket.customer_type || "Individual"}</p>
              </div>
              <div>
                <p className="text-muted-foreground flex items-center gap-1">
                  <Phone className="h-3 w-3" /> Phone
                </p>
                <p className="font-semibold">{localTicket.contact_number || "N/A"}</p>
              </div>
              <div>
                <p className="text-muted-foreground flex items-center gap-1">
                  <Mail className="h-3 w-3" /> Email
                </p>
                <p className="font-semibold">{localTicket.customer_email || "N/A"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vehicle Number</p>
                <p className="font-semibold font-mono">{localTicket.vehicle_number || "N/A"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vehicle Model</p>
                <p className="font-semibold">{localTicket.vehicle_model || "N/A"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vehicle Type</p>
                <p className="font-semibold capitalize">{localTicket.vehicle_type?.replace("_", " ") || "N/A"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Technician Assigned</p>
                <p className="font-semibold">{localTicket.assigned_technician_name || "Not Assigned"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Priority</p>
                <Badge variant="outline" className="capitalize">{localTicket.priority}</Badge>
              </div>
              <div>
                <p className="text-muted-foreground">Resolution Type</p>
                <p className="font-semibold capitalize">{localTicket.resolution_type?.replace("_", " ") || "Workshop"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Issue Type</p>
                <p className="font-semibold capitalize">{localTicket.issue_type || localTicket.category}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Created At</p>
                <p className="font-semibold">{localTicket.created_at ? format(new Date(localTicket.created_at), "PPP p") : "N/A"}</p>
              </div>
            </CardContent>
          </Card>

          {/* Issue Details */}
          <Card>
            <CardHeader>
              <CardTitle>Issue Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold">Issue Reported</h4>
                <p className="text-muted-foreground mt-1">{localTicket.title}</p>
              </div>
              <div>
                <h4 className="font-semibold">Detailed Description</h4>
                <p className="text-muted-foreground mt-1">{localTicket.description || "N/A"}</p>
              </div>
              {localTicket.incident_location && (
                <div>
                  <h4 className="font-semibold flex items-center gap-1">
                    <MapPin className="h-4 w-4" /> Incident Location
                  </h4>
                  <p className="text-muted-foreground mt-1">{localTicket.incident_location}</p>
                </div>
              )}
              {localTicket.attachments_count > 0 && (
                <div>
                  <h4 className="font-semibold flex items-center gap-1">
                    <Paperclip className="h-4 w-4" /> Attachments
                  </h4>
                  <p className="text-muted-foreground mt-1">{localTicket.attachments_count} file(s) attached</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Items and Costing - Only show after technician assigned */}
          {localTicket.status !== "open" && (
            <Card>
              <CardHeader>
                <CardTitle>{isEstimateStage ? "Estimated Cost" : "Final Bill"}</CardTitle>
                <CardDescription>
                  {isEstimateStage && !isCustomer 
                    ? "Add or remove items to generate the cost estimate."
                    : "Parts and services for this job."}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Add Items UI - Only for admin/technician in estimate stage */}
                {!isCustomer && isEstimateStage && (
                  <div className="my-4 p-4 border rounded-lg bg-background">
                    <h4 className="font-semibold mb-2">Add Items to Estimate</h4>
                    <div className="flex gap-2">
                      <Select value={itemType} onValueChange={(v) => { setItemType(v); setSelectedItem(null); }}>
                        <SelectTrigger className="w-[120px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="part">Part</SelectItem>
                          <SelectItem value="service">Service</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      <Popover open={itemsOpen} onOpenChange={setItemsOpen}>
                        <PopoverTrigger asChild>
                          <Button variant="outline" className="flex-1 justify-between">
                            {selectedItem ? selectedItem.name : `Select a ${itemType}...`}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="p-0 w-[300px]">
                          <Command>
                            <CommandInput 
                              placeholder={`Search ${itemType}s...`}
                              value={itemSearch}
                              onValueChange={setItemSearch}
                            />
                            <CommandList>
                              <CommandEmpty>No items found</CommandEmpty>
                              <CommandGroup>
                                {availableItems.slice(0, 10).map((item) => (
                                  <CommandItem
                                    key={item.item_id || item.service_id}
                                    onSelect={() => {
                                      setSelectedItem(item);
                                      setItemsOpen(false);
                                    }}
                                  >
                                    <span className="truncate">{item.name}</span>
                                    <span className="ml-auto text-xs text-muted-foreground">
                                      ₹{(item.unit_price || item.base_price || 0).toLocaleString()}
                                    </span>
                                  </CommandItem>
                                ))}
                              </CommandGroup>
                            </CommandList>
                          </Command>
                        </PopoverContent>
                      </Popover>
                      
                      <Button onClick={handleAddItem} disabled={!selectedItem}>
                        <PlusCircle className="mr-2 h-4 w-4" />
                        Add
                      </Button>
                    </div>
                  </div>
                )}

                {/* Items Table */}
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>GST</TableHead>
                      <TableHead>Qty</TableHead>
                      <TableHead className="text-right">Cost</TableHead>
                      {!isCustomer && isEstimateStage && <TableHead className="text-right">Actions</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(items.services || []).map((service, index) => (
                      <TableRow key={`service-${index}`}>
                        <TableCell>{service.name}</TableCell>
                        <TableCell><Badge variant="secondary">Service</Badge></TableCell>
                        <TableCell>{service.gst_rate || 18}%</TableCell>
                        <TableCell>{service.quantity || 1}</TableCell>
                        <TableCell className="text-right font-mono">
                          ₹{((service.unit_price || 0) * (service.quantity || 1)).toLocaleString()}
                        </TableCell>
                        {!isCustomer && isEstimateStage && (
                          <TableCell className="text-right">
                            <Button variant="ghost" size="icon" onClick={() => handleRemoveItem(index, "service", isEstimateStage)}>
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                    {(items.parts || []).map((part, index) => (
                      <TableRow key={`part-${index}`}>
                        <TableCell>{part.name}</TableCell>
                        <TableCell><Badge variant="outline">Part</Badge></TableCell>
                        <TableCell>{part.gst_rate || 18}%</TableCell>
                        <TableCell>{part.quantity || 1}</TableCell>
                        <TableCell className="text-right font-mono">
                          ₹{((part.unit_price || 0) * (part.quantity || 1)).toLocaleString()}
                        </TableCell>
                        {!isCustomer && isEstimateStage && (
                          <TableCell className="text-right">
                            <Button variant="ghost" size="icon" onClick={() => handleRemoveItem(index, "part", isEstimateStage)}>
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                    {(!items.services?.length && !items.parts?.length) && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground h-24">
                          No items added yet.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
              <CardFooter>
                <div className="w-full max-w-sm space-y-2 ml-auto text-right text-sm">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span className="font-mono">₹{subtotal.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Tax (GST)</span>
                    <span className="font-mono">₹{totalTax.toLocaleString()}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between font-bold text-lg">
                    <p>Grand Total</p>
                    <p className="font-mono">₹{grandTotal.toLocaleString()}</p>
                  </div>
                </div>
              </CardFooter>
            </Card>
          )}

          {/* Status History */}
          <Card>
            <CardHeader>
              <CardTitle>Status History</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {statusHistory.length > 0 ? statusHistory.map((historyItem, index) => (
                  <li key={index} className="flex items-start gap-4">
                    <div className="flex flex-col items-center">
                      <div className="bg-primary rounded-full h-8 w-8 flex items-center justify-center">
                        <CheckCircle className="h-5 w-5 text-primary-foreground" />
                      </div>
                      {index < statusHistory.length - 1 && <div className="w-px h-8 bg-border"></div>}
                    </div>
                    <div>
                      <p className="font-medium">{statusLabels[historyItem.status] || historyItem.status}</p>
                      <p className="text-sm text-muted-foreground">
                        {historyItem.timestamp && format(new Date(historyItem.timestamp), "PPP p")}
                      </p>
                      {historyItem.updated_by && (
                        <p className="text-xs text-muted-foreground">by {historyItem.updated_by}</p>
                      )}
                    </div>
                  </li>
                )) : (
                  <li className="text-muted-foreground text-center py-4">No status updates yet</li>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>

      {/* Action Buttons */}
      <div className="pt-4 flex flex-wrap justify-end gap-2 border-t bg-background p-4">
        {/* Assign Technician - Admin only, when Open */}
        {isAdmin && localTicket.status === "open" && (
          <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <UserCog className="mr-2 h-4 w-4" />
                Assign Technician
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Assign Technician</DialogTitle>
                <DialogDescription>Choose an available technician for this service ticket.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <Select value={selectedTechnician} onValueChange={setSelectedTechnician}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a technician" />
                  </SelectTrigger>
                  <SelectContent>
                    {technicians.map((tech) => (
                      <SelectItem key={tech.user_id} value={tech.user_id}>
                        {tech.name} - {tech.designation || "Technician"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleAssignTechnician} className="w-full" disabled={loading}>
                  {loading ? "Assigning..." : "Assign"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {/* Share Estimate - Admin/Technician, when Technician Assigned and has items */}
        {!isCustomer && localTicket.status === "technician_assigned" && 
         (estimatedItems.parts.length > 0 || estimatedItems.services.length > 0) && (
          <Button onClick={handleShareEstimate} disabled={loading}>
            <Send className="mr-2 h-4 w-4" />
            Share Estimate
          </Button>
        )}

        {/* Approve Estimate - When Estimate Shared */}
        {localTicket.status === "estimate_shared" && (
          <Button onClick={handleApproveEstimate} variant="outline" disabled={loading}>
            <Check className="mr-2 h-4 w-4" />
            {isCustomer ? "Approve Estimate" : "Approve on Customer Behalf"}
          </Button>
        )}

        {/* Start Work - Technician, when Estimate Approved */}
        {isTechnician && localTicket.status === "estimate_approved" && (
          <Button onClick={handleStartWork} disabled={loading}>
            <Play className="mr-2 h-4 w-4" />
            Start Work
          </Button>
        )}

        {/* Mark as Resolved - Technician, when In Progress */}
        {isTechnician && localTicket.status === "in_progress" && (
          <Button onClick={handleMarkResolved} disabled={loading}>
            <Flag className="mr-2 h-4 w-4" />
            Mark as Resolved
          </Button>
        )}

        {/* Generate Invoice - Admin/Technician, when Resolved */}
        {!isCustomer && localTicket.status === "resolved" && (
          <Button onClick={handleGenerateInvoice} disabled={loading}>
            <FileText className="mr-2 h-4 w-4" />
            Generate Invoice & Close
          </Button>
        )}

        {/* Download PDF - Always available */}
        <Button variant="outline" onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" />
          Print / Download
        </Button>
      </div>
    </div>
  );
}
