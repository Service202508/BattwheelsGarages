import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import {
  Ticket, Plus, Search, Loader2, Car, Clock, MapPin,
  AlertCircle, CheckCircle, ArrowRight, Filter, RefreshCw,
  Calendar, Wrench, FileText
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  open: "bg-blue-100 text-bw-blue border-blue-200",
  assigned: "bg-purple-100 text-bw-purple border-purple-200",
  technician_assigned: "bg-purple-100 text-bw-purple border-purple-200",
  work_in_progress: "bg-amber-100 text-amber-700 border-amber-200",
  estimate_sent: "bg-bw-teal/10 text-bw-teal border border-bw-teal/25 border-cyan-200",
  estimate_approved: "bg-bw-volt/10 text-bw-volt text-700 border-bw-volt/20",
  work_completed: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25 border-green-200",
  closed: "bg-white/5 text-slate-600 border-white/[0.07] border-200",
  resolved: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25 border-green-200",
};

const priorityColors = {
  low: "bg-bw-green/[0.08] text-green-600",
  medium: "bg-bw-amber/[0.08] text-bw-amber",
  high: "bg-bw-orange/[0.08] text-bw-orange",
  critical: "bg-bw-red/[0.08] text-red-600",
};

export default function BusinessTickets({ user }) {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewTicketDialog, setShowNewTicketDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [fleet, setFleet] = useState([]);
  
  const [formData, setFormData] = useState({
    vehicle_number: "",
    title: "",
    description: "",
    issue_type: "",
    priority: "medium",
    ticket_type: "workshop",
    incident_location: ""
  });

  useEffect(() => {
    fetchTickets();
    fetchFleet();
  }, [statusFilter]);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      let url = `${API}/business/tickets?limit=100`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      
      const res = await fetch(url, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setTickets(data.tickets || []);
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
      toast.error("Failed to load tickets");
    } finally {
      setLoading(false);
    }
  };

  const fetchFleet = async () => {
    try {
      const res = await fetch(`${API}/business/fleet`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setFleet(data.vehicles || []);
      }
    } catch (error) {
      console.error("Failed to fetch fleet:", error);
    }
  };

  const handleCreateTicket = async () => {
    if (!formData.vehicle_number || !formData.title || !formData.issue_type) {
      toast.error("Please fill in all required fields");
      return;
    }
    
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/business/tickets`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Ticket ${data.ticket_id} created successfully`);
        setShowNewTicketDialog(false);
        setFormData({
          vehicle_number: "",
          title: "",
          description: "",
          issue_type: "",
          priority: "medium",
          ticket_type: "workshop",
          incident_location: ""
        });
        fetchTickets();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to create ticket");
      }
    } catch (error) {
      toast.error("Failed to create ticket");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredTickets = tickets.filter(t => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      t.ticket_id?.toLowerCase().includes(search) ||
      t.title?.toLowerCase().includes(search) ||
      t.vehicle_number?.toLowerCase().includes(search)
    );
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  const stats = {
    total: tickets.length,
    active: tickets.filter(t => ["open", "assigned", "work_in_progress", "estimate_sent"].includes(t.status)).length,
    completed: tickets.filter(t => ["work_completed", "closed", "resolved"].includes(t.status)).length
  };

  return (
    <div className="space-y-6" data-testid="business-tickets">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Service Tickets</h1>
          <p className="text-slate-500">Track and manage your service requests</p>
        </div>
        <Button 
          onClick={() => setShowNewTicketDialog(true)}
          className="bg-indigo-600 hover:bg-indigo-700 hover:shadow-[0_0_20px_rgba(99,102,241,0.30)]"
          data-testid="raise-ticket-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Raise Ticket
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Tickets</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <div className="p-3 rounded bg-indigo-50">
                <Ticket className="h-5 w-5 text-indigo-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active</p>
                <p className="text-2xl font-bold text-amber-600">{stats.active}</p>
              </div>
              <div className="p-3 rounded bg-amber-50">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Completed</p>
                <p className="text-2xl font-bold text-bw-volt text-600">{stats.completed}</p>
              </div>
              <div className="p-3 rounded bg-bw-volt/[0.08]">
                <CheckCircle className="h-5 w-5 text-bw-volt text-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs & Filters */}
      <Tabs value={statusFilter} onValueChange={setStatusFilter}>
        <div className="flex items-center justify-between">
          <TabsList className="bg-white/5">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>
          
          <div className="flex items-center gap-4">
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search tickets..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline" onClick={fetchTickets}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Tickets List */}
        <TabsContent value={statusFilter} className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
          ) : filteredTickets.length === 0 ? (
            <Card className="bg-bw-panel border-white/[0.07] border-200">
              <CardContent className="py-12 text-center">
                <Ticket className="h-16 w-16 mx-auto text-slate-300 mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">No tickets found</h3>
                <p className="text-slate-500">
                  {searchTerm ? "Try adjusting your search" : "Raise a new ticket to get started"}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredTickets.map((ticket) => (
                <Card 
                  key={ticket.ticket_id} 
                  className="bg-bw-panel border-white/[0.07] border-200 hover:border-bw-volt/20 transition-colors cursor-pointer"
                  onClick={() => navigate(`/business/tickets/${ticket.ticket_id}`)}
                  data-testid={`ticket-card-${ticket.ticket_id}`}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        {/* Status & Priority */}
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className={statusColors[ticket.status] || statusColors.open}>
                            {ticket.status?.replace(/_/g, ' ')}
                          </Badge>
                          <Badge variant="outline" className={priorityColors[ticket.priority]}>
                            {ticket.priority}
                          </Badge>
                          <span className="text-xs text-slate-400 font-mono">{ticket.ticket_id}</span>
                        </div>
                        
                        {/* Title */}
                        <h3 className="text-lg font-medium text-slate-900 mb-2">{ticket.title}</h3>
                        
                        {/* Vehicle & Details */}
                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                          <div className="flex items-center gap-1">
                            <Car className="h-4 w-4" />
                            <span>{ticket.vehicle_number}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Wrench className="h-4 w-4" />
                            <span>{ticket.vehicle_model || ticket.vehicle_oem || "N/A"}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            <span>{formatDate(ticket.created_at)}</span>
                          </div>
                          {ticket.ticket_type && (
                            <Badge variant="outline" className="text-xs">
                              {ticket.ticket_type.replace(/_/g, ' ')}
                            </Badge>
                          )}
                        </div>
                        
                        {/* Estimate Info */}
                        {ticket.estimate_total && (
                          <div className="mt-3 flex items-center gap-2 text-sm">
                            <FileText className="h-4 w-4 text-indigo-500" />
                            <span className="text-indigo-600 font-medium">
                              Estimate: ₹{ticket.estimate_total?.toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <ArrowRight className="h-5 w-5 text-slate-400 flex-shrink-0" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* New Ticket Dialog */}
      <Dialog open={showNewTicketDialog} onOpenChange={setShowNewTicketDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Raise Service Ticket</DialogTitle>
            <DialogDescription>Create a new service request for your fleet vehicle</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Vehicle *</Label>
              <Select 
                value={formData.vehicle_number}
                onValueChange={(value) => setFormData(prev => ({ ...prev, vehicle_number: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle from fleet" />
                </SelectTrigger>
                <SelectContent>
                  {fleet.map(v => (
                    <SelectItem key={v.vehicle_id} value={v.vehicle_number}>
                      {v.vehicle_number} - {v.vehicle_model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Issue Title *</Label>
              <Input
                placeholder="Brief description of the issue"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Issue Type *</Label>
              <Select 
                value={formData.issue_type}
                onValueChange={(value) => setFormData(prev => ({ ...prev, issue_type: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select issue type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="battery">Battery Issue</SelectItem>
                  <SelectItem value="motor">Motor Problem</SelectItem>
                  <SelectItem value="charging">Charging Issue</SelectItem>
                  <SelectItem value="brake">Brake System</SelectItem>
                  <SelectItem value="electrical">Electrical Fault</SelectItem>
                  <SelectItem value="suspension">Suspension</SelectItem>
                  <SelectItem value="body">Body Damage</SelectItem>
                  <SelectItem value="tire">Tire/Wheel</SelectItem>
                  <SelectItem value="software">Software/Display</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Detailed description of the issue..."
                className="min-h-[100px]"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select 
                  value={formData.priority}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, priority: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select priority" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Resolution Type</Label>
                <Select 
                  value={formData.ticket_type}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, ticket_type: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="workshop">Workshop Visit</SelectItem>
                    <SelectItem value="on_site">On-Site Service</SelectItem>
                    <SelectItem value="pickup">Pickup & Delivery</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {formData.ticket_type === "on_site" && (
              <div className="space-y-2">
                <Label>Location</Label>
                <Input
                  placeholder="Service location address"
                  value={formData.incident_location}
                  onChange={(e) => setFormData(prev => ({ ...prev, incident_location: e.target.value }))}
                />
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewTicketDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateTicket}
              disabled={submitting}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
              Create Ticket
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
