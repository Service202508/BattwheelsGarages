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
  FileText, UserCog, Paperclip, Download, ExternalLink, Phone, Mail, MapPin, Brain,
  ClipboardList, CheckSquare, Clock, XCircle, ChevronLeft
} from "lucide-react";
import { API } from "@/App";
import EFISidePanel from "./EFISidePanel";
import EFIGuidancePanel from "./ai/EFIGuidancePanel";
import EstimateItemsPanel from "./EstimateItemsPanel";

const statusColors = {
  open: "bg-[rgba(234,179,8,0.08)]0",
  technician_assigned: "bg-blue-500",
  estimate_shared: "bg-[rgba(139,92,246,0.08)]0",
  estimate_approved: "bg-indigo-500",
  work_in_progress: "bg-[rgba(255,140,0,0.08)]0",
  work_completed: "bg-teal-500",
  resolved: "bg-[rgba(34,197,94,0.08)]0",
  closed: "bg-[#111820]0",
  in_progress: "bg-[rgba(255,140,0,0.08)]0",  // Legacy alias
};

const statusLabels = {
  open: "Open",
  technician_assigned: "Technician Assigned",
  estimate_shared: "Estimate Shared",
  estimate_approved: "Estimate Approved",
  work_in_progress: "Work In Progress",
  work_completed: "Work Completed",
  resolved: "Resolved",
  closed: "Closed",
  in_progress: "In Progress",  // Legacy alias
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
  
  // Close ticket dialog state
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [closeResolution, setCloseResolution] = useState("");
  const [closeConfirmedFault, setCloseConfirmedFault] = useState("");
  
  // EFI Panel state
  const [efiPanelOpen, setEfiPanelOpen] = useState(true);
  const [efiMode, setEfiMode] = useState("guidance"); // "guidance" or "legacy"
  
  // Items state
  const [estimatedItems, setEstimatedItems] = useState(localTicket.estimated_items || { parts: [], services: [] });
  const [actualItems, setActualItems] = useState(localTicket.actual_items || { parts: [], services: [] });
  const [statusHistory, setStatusHistory] = useState(localTicket.status_history || []);
  
  // Linked estimate state (from ticket-estimate integration)
  const [linkedEstimate, setLinkedEstimate] = useState(null);
  
  // Activity log state
  const [activities, setActivities] = useState([]);
  const [showActivities, setShowActivities] = useState(false);

  useEffect(() => {
    fetchTechnicians();
    fetchInventory();
    fetchServices();
    fetchActivities();
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
        // API returns {data: [...], pagination: {...}} — extract the array
        setInventory(Array.isArray(data) ? data : (data.data || data.items || data.inventory || []));
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
  
  const fetchActivities = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/tickets/${ticket.ticket_id}/activities`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setActivities(data.activities || []);
      }
    } catch (error) {
      console.error("Error fetching activities:", error);
    }
  };
  
  const addActivity = async (action, description) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/tickets/${localTicket.ticket_id}/activities`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ action, description }),
      });
      
      if (response.ok) {
        fetchActivities();
        toast.success("Activity logged");
      }
    } catch (error) {
      console.error("Error adding activity:", error);
    }
  };
  
  const handleAddNote = () => {
    const note = prompt("Enter activity note:");
    if (note) {
      addActivity("note", note);
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
    try {
      setLoading(true);
      const response = await fetch(`${API}/tickets/${localTicket.ticket_id}/start-work`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ notes: "Work started" }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to start work");
      }
      
      const updatedTicket = await response.json();
      setLocalTicket(updatedTicket);
      setStatusHistory(updatedTicket.status_history || []);
      if (onUpdate) onUpdate(updatedTicket);
      toast.success("Work started!");
      fetchActivities();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteWork = async () => {
    const summary = prompt("Enter work summary:");
    if (!summary) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API}/tickets/${localTicket.ticket_id}/complete-work`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ 
          work_summary: summary,
          notes: "Work completed successfully"
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to complete work");
      }
      
      const updatedTicket = await response.json();
      setLocalTicket(updatedTicket);
      setStatusHistory(updatedTicket.status_history || []);
      if (onUpdate) onUpdate(updatedTicket);
      toast.success("Work completed!");
      fetchActivities();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkResolved = async () => {
    await updateTicketStatus("resolved", { actual_items: actualItems });
  };

  const handleCloseTicket = async () => {
    if (!closeResolution.trim()) {
      toast.error("Resolution summary is required");
      return;
    }
    
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const closeData = { 
        resolution: closeResolution.trim(),
        resolution_outcome: "success",
        resolution_notes: "Ticket closed after work completion"
      };
      if (closeConfirmedFault.trim()) {
        closeData.confirmed_fault = closeConfirmedFault.trim();
      }
      const response = await fetch(`${API}/tickets/${localTicket.ticket_id}/close`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(closeData),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to close ticket");
      }
      
      const updatedTicket = await response.json();
      setLocalTicket(updatedTicket);
      setStatusHistory(updatedTicket.status_history || []);
      if (onUpdate) onUpdate(updatedTicket);
      setCloseDialogOpen(false);
      setCloseResolution("");
      setCloseConfirmedFault("");
      toast.success("Ticket closed successfully!");
      fetchActivities();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
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
                <Badge className={statusColors[localTicket.status] || "bg-[#111820]0"}>
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
                <p className="font-semibold capitalize">{localTicket.ticket_type?.replace("_", " ") || "Workshop"}</p>
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

          {/* Estimate Items Panel - Only show after technician assigned */}
          {localTicket.status !== "open" && (
            <EstimateItemsPanel
              ticket={localTicket}
              user={user}
              organizationId={localTicket.organization_id}
              onEstimateChange={(estimate) => {
                setLinkedEstimate(estimate);
                // Update ticket grand_total from estimate if needed
                if (estimate?.grand_total) {
                  setLocalTicket(prev => ({
                    ...prev,
                    grand_total: estimate.grand_total
                  }));
                }
              }}
            />
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
          
          {/* Activity Log */}
          {(isTechnician || isAdmin) && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <ClipboardList className="h-5 w-5" />
                  Activity Log
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setShowActivities(!showActivities)}>
                  {showActivities ? "Hide" : "Show"}
                </Button>
              </CardHeader>
              {showActivities && (
                <CardContent>
                  <ul className="space-y-3 max-h-64 overflow-y-auto">
                    {activities.length > 0 ? activities.map((activity) => (
                      <li key={activity.activity_id} className="border-b pb-2 last:border-0">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-sm font-medium capitalize">{activity.action.replace(/_/g, " ")}</p>
                            <p className="text-sm text-muted-foreground">{activity.description}</p>
                          </div>
                          <div className="text-right text-xs text-muted-foreground">
                            <p>{activity.timestamp && format(new Date(activity.timestamp), "MMM d, p")}</p>
                            <p>by {activity.user_name}</p>
                          </div>
                        </div>
                        {activity.edited_at && (
                          <p className="text-xs text-[#EAB308] mt-1">Edited by {activity.edited_by}</p>
                        )}
                      </li>
                    )) : (
                      <li className="text-muted-foreground text-center py-4">No activities logged yet</li>
                    )}
                  </ul>
                </CardContent>
              )}
            </Card>
          )}
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

        {/* Share Estimate - Now handled by EstimateItemsPanel */}
        {/* The Send button is in EstimateItemsPanel */}

        {/* Approve Estimate - Now handled by EstimateItemsPanel */}
        {/* The Approve button is in EstimateItemsPanel */}

        {/* Start Work - When estimate is approved (auto-triggered but can be manual) */}
        {(isTechnician || isAdmin) && localTicket.status === "estimate_approved" && (
          <Button onClick={handleStartWork} disabled={loading} data-testid="start-work-btn">
            <Play className="mr-2 h-4 w-4" />
            {loading ? "Starting..." : "Start Work"}
          </Button>
        )}

        {/* Complete Work - When work is in progress */}
        {(isTechnician || isAdmin) && (localTicket.status === "work_in_progress" || localTicket.status === "in_progress") && (
          <Button onClick={handleCompleteWork} disabled={loading} data-testid="complete-work-btn">
            <CheckSquare className="mr-2 h-4 w-4" />
            {loading ? "Completing..." : "Complete Work"}
          </Button>
        )}

        {/* Add Note - Always available for tech/admin on open tickets */}
        {(isTechnician || isAdmin) && localTicket.status !== "closed" && (
          <Button variant="outline" onClick={handleAddNote} data-testid="add-note-btn">
            <ClipboardList className="mr-2 h-4 w-4" />
            Add Note
          </Button>
        )}

        {/* Close Ticket - Admin/Technician, when work is completed */}
        {(isTechnician || isAdmin) && localTicket.status === "work_completed" && (
          <Dialog open={closeDialogOpen} onOpenChange={setCloseDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="default" data-testid="close-ticket-btn">
                <XCircle className="mr-2 h-4 w-4" />
                Close Ticket
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md bg-slate-900 border-slate-700 text-slate-100">
              <DialogHeader>
                <DialogTitle>Close Ticket</DialogTitle>
                <DialogDescription className="text-slate-400">
                  Provide a resolution summary and optionally confirm the actual fault for EFI learning.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-2">
                <div className="space-y-2">
                  <Label htmlFor="close-resolution" className="text-slate-300">Resolution Summary *</Label>
                  <Input
                    id="close-resolution"
                    data-testid="close-resolution-input"
                    placeholder="Describe how the issue was resolved..."
                    value={closeResolution}
                    onChange={(e) => setCloseResolution(e.target.value)}
                    className="bg-slate-800 border-slate-600 text-slate-100 placeholder:text-slate-500"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="close-confirmed-fault" className="text-slate-300">
                    Confirmed Fault <span className="text-slate-500 font-normal">(optional — trains EFI predictions)</span>
                  </Label>
                  <Input
                    id="close-confirmed-fault"
                    data-testid="close-confirmed-fault-input"
                    placeholder="e.g. BMS cell balancing failure"
                    value={closeConfirmedFault}
                    onChange={(e) => setCloseConfirmedFault(e.target.value)}
                    className="bg-slate-800 border-slate-600 text-slate-100 placeholder:text-slate-500"
                  />
                  <p className="text-xs text-slate-500">
                    This helps the EFI engine learn from real outcomes and improve future predictions.
                  </p>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setCloseDialogOpen(false)} className="border-slate-600 text-slate-300">
                  Cancel
                </Button>
                <Button
                  onClick={handleCloseTicket}
                  disabled={loading || !closeResolution.trim()}
                  data-testid="confirm-close-ticket-btn"
                >
                  {loading ? "Closing..." : "Close Ticket"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {/* Generate Invoice - Admin/Technician, when Resolved or Work Completed */}
        {!isCustomer && (localTicket.status === "resolved" || localTicket.status === "work_completed") && (
          <Button onClick={handleGenerateInvoice} disabled={loading} variant="outline">
            <FileText className="mr-2 h-4 w-4" />
            Generate Invoice
          </Button>
        )}

        {/* Download PDF - Always available */}
        <Button variant="outline" onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" />
          Print / Download
        </Button>
      </div>
      </div>

      {/* EFI Side Panel - Only for technicians and admins */}
      {(isTechnician || isAdmin) && efiPanelOpen && (
        <div className="w-[420px] border-l border-[rgba(255,255,255,0.07)] border-700 bg-slate-900/95 flex flex-col overflow-hidden">
          {/* Panel Header with Mode Toggle */}
          <div className="p-3 border-b border-[rgba(255,255,255,0.07)] border-700 flex items-center justify-between bg-slate-800/50">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-[#C8FF00] text-400" />
              <span className="font-semibold text-white">EFI Assistant</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex bg-slate-700 rounded p-0.5 text-xs">
                <button
                  className={`px-2 py-1 rounded ${efiMode === "guidance" ? "bg-[#C8FF00] text-[#080C0F] font-bold" : "text-[rgba(244,246,240,0.45)]"}`}
                  onClick={() => setEfiMode("guidance")}
                >
                  Hinglish
                </button>
                <button
                  className={`px-2 py-1 rounded ${efiMode === "legacy" ? "bg-[#C8FF00] text-[#080C0F] font-bold" : "text-[rgba(244,246,240,0.45)]"}`}
                  onClick={() => setEfiMode("legacy")}
                >
                  Classic
                </button>
              </div>
              <button
                onClick={() => setEfiPanelOpen(false)}
                className="text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] p-1"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          {/* Panel Content */}
          <div className="flex-1 overflow-y-auto">
            {efiMode === "guidance" ? (
              <EFIGuidancePanel
                ticketId={localTicket.ticket_id}
                user={user}
                vehicleInfo={{
                  make: localTicket.vehicle_oem,
                  model: localTicket.vehicle_model,
                  variant: localTicket.vehicle_variant
                }}
                symptoms={localTicket.symptoms || []}
                dtcCodes={localTicket.dtc_codes || []}
                category={localTicket.category || "general"}
                description={localTicket.description || localTicket.title}
                onEstimateUpdated={() => fetchLinkedEstimate()}
              />
            ) : (
              <EFISidePanel
                ticket={localTicket}
                user={user}
                isOpen={true}
                onToggle={() => {}}
                onEstimateSuggested={handleEfiEstimateSuggested}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
