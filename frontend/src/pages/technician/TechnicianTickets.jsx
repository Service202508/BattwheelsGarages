import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  Search, Filter, Ticket, Car, Clock, User, MapPin,
  Play, CheckCircle, ArrowRight, Loader2, AlertCircle,
  FileText, Calendar, Phone, Mail
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  open: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  assigned: "bg-bw-purple/[0.08]0/20 text-purple-400 border-purple-500/30",
  technician_assigned: "bg-bw-purple/[0.08]0/20 text-purple-400 border-purple-500/30",
  work_in_progress: "bg-bw-orange/[0.08]0/20 text-orange-400 border-orange-500/30",
  estimate_sent: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  estimate_approved: "bg-bw-volt/[0.08]0/20 text-bw-volt text-400 border-bw-volt/50/30",
  work_completed: "bg-bw-green/[0.08]0/20 text-green-400 border-green-500/30",
  closed: "bg-slate-500/20 text-slate-400 border-white/[0.07] border-500/30",
  resolved: "bg-bw-green/[0.08]0/20 text-green-400 border-green-500/30",
};

const priorityColors = {
  low: "bg-bw-green/[0.08]0/10 text-green-400",
  medium: "bg-bw-amber/[0.08]0/10 text-yellow-400",
  high: "bg-bw-orange/[0.08]0/10 text-orange-400",
  critical: "bg-bw-red/[0.08]0/10 text-red-400 animate-pulse",
};

export default function TechnicianTickets({ user }) {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("active");
  const [priorityFilter, setPriorityFilter] = useState("all");
  
  // Action dialogs
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showStartWorkDialog, setShowStartWorkDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Complete work form
  const [completeForm, setCompleteForm] = useState({
    work_summary: "",
    labor_hours: "",
    notes: ""
  });

  useEffect(() => {
    fetchTickets();
  }, [statusFilter, priorityFilter]);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      let url = `${API}/technician/tickets?limit=100`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      if (priorityFilter !== "all") url += `&priority=${priorityFilter}`;
      
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

  const handleStartWork = async () => {
    if (!selectedTicket) return;
    setActionLoading(true);
    
    try {
      const res = await fetch(`${API}/technician/tickets/${selectedTicket.ticket_id}/start-work`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ notes: "Work started" })
      });
      
      if (res.ok) {
        toast.success("Work started successfully!");
        setShowStartWorkDialog(false);
        fetchTickets();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to start work");
      }
    } catch (error) {
      toast.error("Failed to start work");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompleteWork = async () => {
    if (!selectedTicket) return;
    if (!completeForm.work_summary || !completeForm.labor_hours) {
      toast.error("Please fill in work summary and labor hours");
      return;
    }
    
    setActionLoading(true);
    
    try {
      const res = await fetch(`${API}/technician/tickets/${selectedTicket.ticket_id}/complete-work`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          work_summary: completeForm.work_summary,
          labor_hours: parseFloat(completeForm.labor_hours),
          notes: completeForm.notes
        })
      });
      
      if (res.ok) {
        toast.success("Work completed successfully!");
        setShowCompleteDialog(false);
        setCompleteForm({ work_summary: "", labor_hours: "", notes: "" });
        fetchTickets();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to complete work");
      }
    } catch (error) {
      toast.error("Failed to complete work");
    } finally {
      setActionLoading(false);
    }
  };

  const filteredTickets = tickets.filter(ticket => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      ticket.ticket_id?.toLowerCase().includes(search) ||
      ticket.title?.toLowerCase().includes(search) ||
      ticket.vehicle_number?.toLowerCase().includes(search) ||
      ticket.customer_name?.toLowerCase().includes(search)
    );
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <div className="space-y-6" data-testid="technician-tickets">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">My Tickets</h1>
        <p className="text-slate-400">Tickets assigned to you for service</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search tickets..."
            className="pl-10 bg-slate-900/50 border-white/[0.07] border-700"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40 bg-slate-900/50 border-white/[0.07] border-700">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="work_in_progress">In Progress</SelectItem>
            <SelectItem value="estimate_sent">Estimate Sent</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-40 bg-slate-900/50 border-white/[0.07] border-700">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
        
        <Button variant="outline" onClick={fetchTickets} className="border-white/[0.07] border-700">
          <Filter className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Tickets List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-green-500" />
        </div>
      ) : filteredTickets.length === 0 ? (
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="py-12 text-center">
            <Ticket className="h-16 w-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No tickets found</h3>
            <p className="text-slate-400">
              {searchTerm ? "Try adjusting your search" : "No tickets are currently assigned to you"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredTickets.map((ticket) => (
            <Card 
              key={ticket.ticket_id} 
              className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-green-500/30 transition-all"
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* Status & Priority */}
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className={statusColors[ticket.status] || statusColors.open}>
                        {ticket.status?.replace(/_/g, ' ')}
                      </Badge>
                      <Badge className={priorityColors[ticket.priority] || priorityColors.medium}>
                        {ticket.priority}
                      </Badge>
                      <span className="text-xs text-slate-500 font-mono">{ticket.ticket_id}</span>
                    </div>
                    
                    {/* Title */}
                    <h3 className="text-lg font-medium text-white mb-2">{ticket.title}</h3>
                    
                    {/* Vehicle & Customer Info */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                      <div className="flex items-center gap-2 text-slate-400">
                        <Car className="h-4 w-4 text-slate-500" />
                        <span>{ticket.vehicle_number}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-400">
                        <Ticket className="h-4 w-4 text-slate-500" />
                        <span>{ticket.vehicle_model || ticket.vehicle_oem || "N/A"}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-400">
                        <User className="h-4 w-4 text-slate-500" />
                        <span>{ticket.customer_name || "N/A"}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-400">
                        <Calendar className="h-4 w-4 text-slate-500" />
                        <span>{formatDate(ticket.created_at)}</span>
                      </div>
                    </div>
                    
                    {/* Resolution Type & Location */}
                    {(ticket.ticket_type || ticket.incident_location) && (
                      <div className="flex items-center gap-4 mt-3 text-sm">
                        {ticket.ticket_type && (
                          <Badge variant="outline" className="border-white/[0.07] border-700 text-slate-400">
                            {ticket.ticket_type.replace(/_/g, ' ')}
                          </Badge>
                        )}
                        {ticket.incident_location && (
                          <div className="flex items-center gap-1 text-slate-400">
                            <MapPin className="h-3.5 w-3.5" />
                            <span className="truncate max-w-[200px]">{ticket.incident_location}</span>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Estimate Status */}
                    {ticket.estimate && (
                      <div className="mt-3 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-cyan-400" />
                        <span className="text-sm text-cyan-400">
                          Estimate: {ticket.estimate.status} - ₹{ticket.estimate.grand_total?.toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex flex-col gap-2">
                    <Link to={`/technician/tickets/${ticket.ticket_id}`}>
                      <Button variant="outline" size="sm" className="w-full border-white/[0.07] border-700">
                        View Details
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Button>
                    </Link>
                    
                    {["open", "assigned", "technician_assigned", "estimate_approved"].includes(ticket.status) && (
                      <Button 
                        size="sm" 
                        className="bg-bw-green hover:bg-bw-green-hover"
                        onClick={() => { setSelectedTicket(ticket); setShowStartWorkDialog(true); }}
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Start Work
                      </Button>
                    )}
                    
                    {ticket.status === "work_in_progress" && (
                      <Button 
                        size="sm" 
                        className="bg-blue-600 hover:bg-blue-700"
                        onClick={() => { setSelectedTicket(ticket); setShowCompleteDialog(true); }}
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Complete
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Start Work Dialog */}
      <Dialog open={showStartWorkDialog} onOpenChange={setShowStartWorkDialog}>
        <DialogContent className="bg-slate-900 border-white/[0.07] border-800">
          <DialogHeader>
            <DialogTitle className="text-white">Start Work</DialogTitle>
            <DialogDescription>
              Begin working on ticket: {selectedTicket?.title}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="p-4 rounded-lg bg-slate-800/50 border border-white/[0.07] border-700">
              <div className="flex items-center gap-3 text-sm">
                <Car className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-white font-medium">{selectedTicket?.vehicle_number}</p>
                  <p className="text-slate-400">{selectedTicket?.vehicle_model}</p>
                </div>
              </div>
            </div>
            <p className="text-sm text-slate-400 mt-4">
              This will update the ticket status to "Work in Progress" and record the start time.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStartWorkDialog(false)} className="border-white/[0.07] border-700">
              Cancel
            </Button>
            <Button 
              onClick={handleStartWork}
              disabled={actionLoading}
              className="bg-bw-green hover:bg-bw-green-hover"
            >
              {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
              Start Work
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Complete Work Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent className="bg-slate-900 border-white/[0.07] border-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Complete Work</DialogTitle>
            <DialogDescription>
              Mark this ticket as work completed
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-300">Work Summary *</Label>
              <Textarea
                placeholder="Describe the work performed..."
                className="bg-slate-800/50 border-white/[0.07] border-700 min-h-[100px]"
                value={completeForm.work_summary}
                onChange={(e) => setCompleteForm(prev => ({ ...prev, work_summary: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Labor Hours *</Label>
              <Input
                type="number"
                step="0.5"
                min="0.5"
                placeholder="e.g., 2.5"
                className="bg-slate-800/50 border-white/[0.07] border-700"
                value={completeForm.labor_hours}
                onChange={(e) => setCompleteForm(prev => ({ ...prev, labor_hours: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Additional Notes</Label>
              <Textarea
                placeholder="Any additional notes..."
                className="bg-slate-800/50 border-white/[0.07] border-700"
                value={completeForm.notes}
                onChange={(e) => setCompleteForm(prev => ({ ...prev, notes: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompleteDialog(false)} className="border-white/[0.07] border-700">
              Cancel
            </Button>
            <Button 
              onClick={handleCompleteWork}
              disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
              Mark Complete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
