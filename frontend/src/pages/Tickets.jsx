import { useState, useEffect, useCallback, useRef } from "react";
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
  open: "bg-bw-amber/10",
  technician_assigned: "bg-blue-500",
  estimate_shared: "bg-bw-purple/10",
  estimate_approved: "bg-indigo-500",
  in_progress: "bg-bw-orange/10",
  resolved: "bg-bw-green/10",
  closed: "bg-bw-panel0",
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
  low: "bg-bw-volt/20 text-bw-volt",
  medium: "bg-bw-amber/20 text-yellow-400",
  high: "bg-bw-orange/20 text-orange-400",
  critical: "bg-bw-red/20 text-red-400"
};

export default function Tickets({ user }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState(null);
  const [ticketTypeFilter, setTicketTypeFilter] = useState(null); // null = all, "onsite", "workshop"
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
      if (ticketTypeFilter) {
        params.append("ticket_type", ticketTypeFilter);
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
        // Handle paginated {data:[...]} format, legacy {tickets:[...]} format, and plain array
        let data = Array.isArray(responseData) ? responseData : (responseData.data || responseData.tickets || []);
        
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
  }, [statusFilter, ticketTypeFilter, searchTerm]);

  const fetchKPIs = useCallback(async () => {
    try {
      const response = await fetch(`${API}/tickets/stats`, {
        credentials: "include",
        headers: getAuthHeaders(),
      });
      
      if (response.ok) {
        const stats = await response.json();
        const byStatus = stats.by_status || {};
        setKpiData({
          open: byStatus.open ?? stats.open ?? 0,
          technician_assigned: byStatus.technician_assigned ?? 0,
          estimate_shared: byStatus.estimate_shared ?? 0,
          in_progress: byStatus.in_progress ?? stats.in_progress ?? 0,
          resolved_this_week: (byStatus.resolved ?? 0) + (byStatus.closed ?? 0),
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

  // Refresh tickets every 60s to keep SLA countdowns accurate
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTickets();
    }, 60000);
    return () => clearInterval(interval);
  }, [fetchTickets]);

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

  // SLA cell — defined inside component to avoid babel-metadata-plugin issues
  const SLACell = ({ ticket }) => {
    if (!ticket.sla_resolution_due_at) return <span style={{ color: "rgba(244,246,240,0.25)" }}>—</span>;
    const now = new Date();
    const resDue = new Date(ticket.sla_resolution_due_at);
    const minsRemaining = (resDue - now) / 60000;

    if (ticket.sla_resolution_breached) {
      return (
        <span style={{
          background: "rgba(255,59,47,0.10)",
          color: "rgb(var(--bw-red))",
          border: "1px solid rgba(255,59,47,0.25)",
          fontFamily: "monospace",
          fontSize: "10px",
          padding: "3px 8px",
          borderRadius: "2px"
        }}>BREACHED</span>
      );
    }
    if (minsRemaining < 120) {
      return <span style={{ color: "rgb(var(--bw-orange))" }}>{Math.floor(minsRemaining)}m left</span>;
    }
    if (minsRemaining < 1440) {
      const hrs = Math.floor(minsRemaining / 60);
      return <span style={{ color: "rgb(var(--bw-white))" }}>{hrs}h left</span>;
    }
    return <span style={{ color: "rgba(244,246,240,0.35)" }}>On track</span>;
  };

  return (
    <div className="space-y-4 overflow-x-hidden w-full" data-testid="complaint-dashboard">
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

      {/* Ticket Type Filter Tabs */}
      <div className="flex items-center gap-2" data-testid="ticket-type-filter">
        {[
          { key: null, label: "All Tickets" },
          { key: "onsite", label: "Onsite" },
          { key: "workshop", label: "Workshop" },
        ].map((tab) => (
          <Button
            key={tab.key || "all"}
            variant={ticketTypeFilter === tab.key ? "default" : "outline"}
            size="sm"
            onClick={() => { setTicketTypeFilter(tab.key); setPage(1); }}
            data-testid={`filter-${tab.key || "all"}`}
            className={ticketTypeFilter === tab.key ? "" : "border-white/10 text-muted-foreground"}
          >
            {tab.label}
          </Button>
        ))}
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

      {/* Tickets — Table (desktop) / Cards (mobile) */}
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
            <>
              {/* Desktop Table */}
              <div className="hidden md:block overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Ticket ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Vehicle</TableHead>
                      <TableHead>Issue</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Technician</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead style={{ fontFamily: "JetBrains Mono, monospace" }}>SLA</TableHead>
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
                          <Badge 
                            className={ticket.ticket_type === "workshop" 
                              ? "bg-bw-blue/15 text-bw-blue border border-bw-blue/25" 
                              : "bg-bw-volt/10 text-bw-volt border border-bw-volt/20"}
                            data-testid={`ticket-type-${ticket.ticket_id}`}
                          >
                            {ticket.ticket_type === "workshop" ? "Workshop" : "Onsite"}
                          </Badge>
                        </TableCell>
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
                          <Badge className={priorityColors[ticket.priority] || "bg-bw-panel"}>
                            {ticket.priority}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={statusColors[ticket.status] || "bg-bw-panel"}>
                            {statusLabels[ticket.status] || ticket.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{ticket.assigned_technician_name || "-"}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {ticket.created_at ? format(new Date(ticket.created_at), "MMM dd, HH:mm") : "N/A"}
                        </TableCell>
                        <TableCell data-testid={`sla-cell-${ticket.ticket_id}`}>
                          <SLACell ticket={ticket} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden divide-y divide-white/[0.06]">
                {paginatedTickets.map((ticket) => (
                  <div
                    key={ticket.ticket_id}
                    data-testid={`ticket-row-${ticket.ticket_id}`}
                    className="p-4 w-full min-w-0"
                    style={{ background: "rgba(17,24,32,0.5)" }}
                  >
                    {/* Top row: ID + Priority + Status */}
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs text-bw-white/40">
                        {ticket.ticket_id}
                      </span>
                      <div className="flex items-center gap-2">
                        <Badge className={priorityColors[ticket.priority] || "bg-bw-panel"} style={{ fontSize: "10px", padding: "2px 6px" }}>
                          {ticket.priority}
                        </Badge>
                        <Badge className={statusColors[ticket.status] || "bg-bw-panel"} style={{ fontSize: "10px", padding: "2px 6px" }}>
                          {statusLabels[ticket.status] || ticket.status}
                        </Badge>
                      </div>
                    </div>

                    {/* Middle: Customer + Vehicle + Title */}
                    <p className="font-semibold text-bw-white text-sm mb-0.5">{ticket.customer_name || "N/A"}</p>
                    <p className="text-xs text-bw-white/[0.45] mb-1">
                      {ticket.vehicle_number || "—"} {ticket.vehicle_type ? `· ${ticket.vehicle_type.replace("_", " ")}` : ""}
                    </p>
                    <p className="text-sm text-bw-white/70 truncate mb-3">{ticket.title}</p>

                    {/* Bottom: SLA + Start Work button */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <SLACell ticket={ticket} data-testid={`sla-cell-${ticket.ticket_id}`} />
                        {ticket.assigned_technician_name && (
                          <span className="text-xs text-bw-white/35">· {ticket.assigned_technician_name}</span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {ticket.status === "open" || ticket.status === "technician_assigned" ? (
                          <button
                            data-testid={`start-work-${ticket.ticket_id}`}
                            onClick={async (e) => {
                              e.stopPropagation();
                              try {
                                const res = await fetch(`${API}/tickets/${ticket.ticket_id}/start-work`, {
                                  method: "POST", headers: getAuthHeaders()
                                });
                                if (res.ok) {
                                  toast.success("Status → In Progress");
                                  fetchTickets();
                                }
                              } catch {}
                            }}
                            style={{
                              minHeight: "44px", padding: "0 16px",
                              background: "rgba(200,255,0,0.10)",
                              border: "1px solid rgba(200,255,0,0.25)",
                              borderRadius: "4px", color: "rgb(var(--bw-volt))",
                              fontSize: "12px", fontFamily: "Syne, sans-serif",
                              cursor: "pointer", display: "flex", alignItems: "center", gap: "4px"
                            }}
                          >
                            ▶ Start Work
                          </button>
                        ) : null}
                        <button
                          onClick={() => handleRowClick(ticket)}
                          style={{
                            minHeight: "44px", padding: "0 16px",
                            background: "rgba(255,255,255,0.05)",
                            border: "1px solid rgba(255,255,255,0.10)",
                            borderRadius: "4px", color: "rgba(244,246,240,0.70)",
                            fontSize: "12px", fontFamily: "Syne, sans-serif",
                            cursor: "pointer"
                          }}
                        >
                          View
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
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
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>Job Card / Service Ticket</DialogTitle>
                <DialogDescription>
                  Manage all aspects of the service ticket from assignment to resolution.
                </DialogDescription>
              </div>
              {selectedTicket && (
                <Link to={`/tickets/${selectedTicket.ticket_id}`} className="text-xs text-bw-volt hover:underline font-mono" data-testid="view-full-page-link">
                  Open Full Page →
                </Link>
              )}
            </div>
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
