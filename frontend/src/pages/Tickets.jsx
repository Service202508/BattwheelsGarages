import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { format } from "date-fns";
import { 
  Plus, Search, Download, Loader2, ChevronLeft, ChevronRight,
  Ticket, UserCheck, Clock, CheckCircle, AlertTriangle, Save
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";
import JobCard from "@/components/JobCard";

const statusColors = {
  open: "bg-[rgba(234,179,8,0.10)]",
  technician_assigned: "bg-blue-500",
  estimate_shared: "bg-[rgba(139,92,246,0.10)]",
  estimate_approved: "bg-indigo-500",
  in_progress: "bg-[rgba(255,140,0,0.10)]",
  resolved: "bg-[rgba(34,197,94,0.10)]",
  closed: "bg-[#111820]0",
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

const priorityColors = {
  low: "bg-[rgba(200,255,0,0.20)] text-[#C8FF00]",
  medium: "bg-[rgba(234,179,8,0.20)] text-yellow-400",
  high: "bg-[rgba(255,140,0,0.20)] text-orange-400",
  critical: "bg-[rgba(255,59,47,0.20)] text-red-400"
};

function getSLAIndicator(ticket) {
  const now = new Date();
  const due = ticket.sla_resolution_due_at ? new Date(ticket.sla_resolution_due_at) : null;
  const breached = ticket.sla_resolution_breached;

  if (!due) return null;
  if (breached || ["resolved", "closed"].includes(ticket.status)) {
    if (["resolved", "closed"].includes(ticket.status)) return null; // don't show on resolved
    return { label: "SLA Breached", class: "bg-red-500/15 text-red-400 border border-red-500/20", dot: "bg-red-400" };
  }

  const remaining = (due - now) / 60000; // minutes
  if (remaining <= 0) return { label: "SLA Breached", class: "bg-red-500/15 text-red-400 border border-red-500/20", dot: "bg-red-400" };
  if (remaining <= 120) {
    const hrs = Math.floor(remaining / 60);
    const mins = Math.round(remaining % 60);
    return { label: hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`, class: "bg-amber-500/15 text-amber-400 border border-amber-500/20", dot: "bg-amber-400" };
  }
  return { label: "On Track", class: "bg-green-500/10 text-green-400 border border-green-500/20", dot: "bg-green-400" };
}

export default function Tickets({ user }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [kpiData, setKpiData] = useState({
    open: 0,
    technician_assigned: 0,
    estimate_shared: 0,
    in_progress: 0,
    resolved_this_week: 0,
  });

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API}/tickets`;
      const params = new URLSearchParams();
      
      if (statusFilter && statusFilter !== "resolved_this_week") {
        params.append("status", statusFilter);
      }
      if (searchTerm) {
        params.append("search", searchTerm);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await fetch(url, {
        credentials: "include",
        headers: getAuthHeaders(),
      });
      
      if (response.ok) {
        const responseData = await response.json();
        // Handle both array and {tickets: [...]} response formats
        let data = Array.isArray(responseData) ? responseData : (responseData.tickets || []);
        
        // Filter for resolved this week if needed
        if (statusFilter === "resolved_this_week") {
          const oneWeekAgo = new Date();
          oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
          data = data.filter(t => 
            t.status === "resolved" && 
            new Date(t.updated_at) >= oneWeekAgo
          );
        }
        
        // Client-side search
        if (searchTerm) {
          const search = searchTerm.toLowerCase();
          data = data.filter(t => 
            t.title?.toLowerCase().includes(search) ||
            t.ticket_id?.toLowerCase().includes(search) ||
            t.customer_name?.toLowerCase().includes(search) ||
            t.vehicle_number?.toLowerCase().includes(search)
          );
        }
        
        setTickets(data);
        setTotalPages(Math.ceil(data.length / 10) || 1);
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
      toast.error("Failed to load tickets");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, searchTerm]);

  const fetchKPIs = useCallback(async () => {
    try {
      const response = await fetch(`${API}/tickets`, {
        credentials: "include",
        headers: getAuthHeaders(),
      });
      
      if (response.ok) {
        const responseData = await response.json();
        // Handle both array and {tickets: [...]} response formats
        const data = Array.isArray(responseData) ? responseData : (responseData.tickets || []);
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
        
        setKpiData({
          open: data.filter(t => t.status === "open").length,
          technician_assigned: data.filter(t => t.status === "technician_assigned").length,
          estimate_shared: data.filter(t => t.status === "estimate_shared").length,
          in_progress: data.filter(t => t.status === "in_progress").length,
          resolved_this_week: data.filter(t => 
            t.status === "resolved" && 
            new Date(t.updated_at) >= oneWeekAgo
          ).length,
        });
      }
    } catch (error) {
      console.error("Failed to fetch KPIs:", error);
    }
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    fetchKPIs();
  }, [fetchKPIs]);

  const fetchTicketDetails = async (ticketId) => {
    setDetailsLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/tickets/${ticketId}`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedTicket(data);
      }
    } catch (error) {
      console.error("Failed to fetch ticket details:", error);
      toast.error("Failed to load ticket details");
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleRowClick = (ticket) => {
    fetchTicketDetails(ticket.ticket_id);
  };

  const handleCloseDialog = () => {
    setSelectedTicket(null);
    fetchTickets();
    fetchKPIs();
  };

  const handleDownloadCSV = () => {
    const headers = ["Ticket ID", "Customer", "Vehicle", "Issue", "Priority", "Status", "Created At"];
    const rows = tickets.map(t => [
      t.ticket_id,
      t.customer_name || "N/A",
      t.vehicle_number || "N/A",
      t.title,
      t.priority,
      t.status,
      t.created_at ? format(new Date(t.created_at), "yyyy-MM-dd HH:mm") : "N/A"
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `complaints-${format(new Date(), "yyyy-MM-dd")}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("CSV downloaded");
  };

  const handleStatusFilterClick = (filter) => {
    if (statusFilter === filter) {
      setStatusFilter(null);
    } else {
      setStatusFilter(filter);
    }
    setPage(1);
  };

  const paginatedTickets = tickets.slice((page - 1) * 10, page * 10);

  return (
    <div className="space-y-4" data-testid="complaint-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Complaint Dashboard</h1>
          <p className="text-muted-foreground">Monitor, manage, filter, and sort all service tickets.</p>
        </div>
        <div className="flex gap-2">
          {statusFilter && (
            <Button variant="ghost" onClick={() => { setStatusFilter(null); setPage(1); }}>
              Clear Filter: {statusLabels[statusFilter] || statusFilter.replace("_", " ")}
            </Button>
          )}
          <Button variant="outline" onClick={handleDownloadCSV} disabled={loading}>
            <Download className="mr-2 h-4 w-4" />
            Download CSV
          </Button>
          <Link to="/tickets/new">
            <Button data-testid="new-ticket-btn">
              <Plus className="mr-2 h-4 w-4" />
              New Ticket
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card 
          onClick={() => handleStatusFilterClick("open")} 
          className={`cursor-pointer hover:bg-muted/50 transition-colors ${statusFilter === "open" ? "ring-2 ring-primary" : ""}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium">Open Tickets</CardTitle>
            <Ticket className="h-5 w-5 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{kpiData.open}</p>
          </CardContent>
        </Card>
        
        <Card 
          onClick={() => handleStatusFilterClick("technician_assigned")} 
          className={`cursor-pointer hover:bg-muted/50 transition-colors ${statusFilter === "technician_assigned" ? "ring-2 ring-primary" : ""}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium">Technician Assigned</CardTitle>
            <UserCheck className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{kpiData.technician_assigned}</p>
          </CardContent>
        </Card>
        
        <Card 
          onClick={() => handleStatusFilterClick("estimate_shared")} 
          className={`cursor-pointer hover:bg-muted/50 transition-colors ${statusFilter === "estimate_shared" ? "ring-2 ring-primary" : ""}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium">Awaiting Approval</CardTitle>
            <AlertTriangle className="h-5 w-5 text-purple-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{kpiData.estimate_shared}</p>
          </CardContent>
        </Card>
        
        <Card 
          onClick={() => handleStatusFilterClick("in_progress")} 
          className={`cursor-pointer hover:bg-muted/50 transition-colors ${statusFilter === "in_progress" ? "ring-2 ring-primary" : ""}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium">Work In Progress</CardTitle>
            <Clock className="h-5 w-5 text-orange-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{kpiData.in_progress}</p>
          </CardContent>
        </Card>
        
        <Card 
          onClick={() => handleStatusFilterClick("resolved_this_week")} 
          className={`cursor-pointer hover:bg-muted/50 transition-colors ${statusFilter === "resolved_this_week" ? "ring-2 ring-primary" : ""}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium">Resolved This Week</CardTitle>
            <CheckCircle className="h-5 w-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{kpiData.resolved_this_week}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by ticket ID, customer, vehicle..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            className="pl-10"
            data-testid="search-input"
          />
        </div>
      </div>

      {/* Tickets Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center items-center h-96">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : paginatedTickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
              <Ticket className="h-12 w-12 mb-4 opacity-50" />
              <p>No tickets found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ticket ID</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Issue</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>SLA</TableHead>
                  <TableHead>Technician</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedTickets.map((ticket) => (
                  <TableRow 
                    key={ticket.ticket_id} 
                    onClick={() => handleRowClick(ticket)}
                    className="cursor-pointer hover:bg-muted/50"
                    data-testid={`ticket-row-${ticket.ticket_id}`}
                  >
                    <TableCell className="font-mono text-sm">{ticket.ticket_id}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{ticket.customer_name || "N/A"}</p>
                        <p className="text-xs text-muted-foreground">{ticket.contact_number || ""}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-mono">{ticket.vehicle_number || "N/A"}</p>
                        <p className="text-xs text-muted-foreground capitalize">{ticket.vehicle_type?.replace("_", " ") || ""}</p>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">{ticket.title}</TableCell>
                    <TableCell>
                      <Badge className={priorityColors[ticket.priority] || "bg-[#111820]0"}>
                        {ticket.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[ticket.status] || "bg-[#111820]0"}>
                        {statusLabels[ticket.status] || ticket.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <SLABadge ticket={ticket} />
                    </TableCell>
                    <TableCell>{ticket.assigned_technician_name || "-"}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {ticket.created_at ? format(new Date(ticket.created_at), "MMM dd, HH:mm") : "N/A"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, tickets.length)} of {tickets.length} tickets
          </p>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage(p => p + 1)}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Job Card Dialog */}
      <Dialog open={!!selectedTicket} onOpenChange={(open) => !open && handleCloseDialog()}>
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col p-0" data-testid="job-card-dialog">
          <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
            <DialogTitle>Job Card / Service Ticket</DialogTitle>
            <DialogDescription>
              Manage all aspects of the service ticket from assignment to resolution.
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto min-h-0">
            {detailsLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : selectedTicket ? (
              <JobCard 
                ticket={selectedTicket} 
                user={user} 
                onUpdate={(updated) => setSelectedTicket(updated)}
                onClose={handleCloseDialog}
              />
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
