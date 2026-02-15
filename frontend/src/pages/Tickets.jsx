import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Search, Filter, Eye, UserPlus } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  open: "badge-warning",
  in_progress: "badge-info",
  resolved: "badge-success",
  closed: "bg-muted text-muted-foreground"
};

const priorityColors = {
  low: "bg-emerald-500/20 text-emerald-400",
  medium: "badge-warning",
  high: "badge-danger",
  critical: "bg-red-600 text-white"
};

export default function Tickets({ user }) {
  const [tickets, setTickets] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedTicket, setSelectedTicket] = useState(null);

  useEffect(() => {
    fetchTickets();
    fetchTechnicians();
  }, [statusFilter]);

  const fetchTickets = async () => {
    try {
      const token = localStorage.getItem("token");
      const url = statusFilter && statusFilter !== "all" 
        ? `${API}/tickets?status=${statusFilter}` 
        : `${API}/tickets`;
      const response = await fetch(url, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setTickets(data);
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
    } finally {
      setLoading(false);
    }
  };

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

  const updateTicket = async (ticketId, updates) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/tickets/${ticketId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(updates),
      });
      if (response.ok) {
        toast.success("Ticket updated successfully");
        fetchTickets();
      } else {
        toast.error("Failed to update ticket");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const filteredTickets = tickets.filter(ticket =>
    ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ticket.ticket_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="tickets-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Complaint Dashboard</h1>
          <p className="text-muted-foreground mt-1">Manage and track all service tickets.</p>
        </div>
        <Link to="/tickets/new">
          <Button className="glow-primary" data-testid="new-ticket-btn">
            <Plus className="h-4 w-4 mr-2" />
            New Ticket
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tickets..."
                className="pl-10 bg-background/50"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                data-testid="search-tickets-input"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48 bg-background/50" data-testid="status-filter">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tickets Table */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading tickets...</div>
          ) : filteredTickets.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No tickets found. Create your first ticket to get started.
            </div>
          ) : (
            <Table className="data-table">
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>Ticket ID</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Assigned To</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTickets.map((ticket) => (
                  <TableRow key={ticket.ticket_id} className="border-white/10">
                    <TableCell className="mono text-sm">{ticket.ticket_id}</TableCell>
                    <TableCell className="font-medium max-w-[200px] truncate">{ticket.title}</TableCell>
                    <TableCell className="capitalize">{ticket.category}</TableCell>
                    <TableCell>
                      <Badge className={priorityColors[ticket.priority]} variant="outline">
                        {ticket.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[ticket.status]} variant="outline">
                        {ticket.status.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user?.role !== "customer" ? (
                        <Select
                          value={ticket.assigned_technician_id || "unassigned"}
                          onValueChange={(value) => 
                            updateTicket(ticket.ticket_id, { 
                              assigned_technician_id: value === "unassigned" ? null : value 
                            })
                          }
                        >
                          <SelectTrigger className="w-36 h-8 text-xs bg-background/50">
                            <SelectValue placeholder="Assign" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="unassigned">Unassigned</SelectItem>
                            {technicians.map((tech) => (
                              <SelectItem key={tech.user_id} value={tech.user_id}>
                                {tech.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <span className="text-muted-foreground text-sm">
                          {ticket.assigned_technician_id ? "Assigned" : "Pending"}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => setSelectedTicket(ticket)}
                            data-testid={`view-ticket-${ticket.ticket_id}`}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-card border-white/10 max-w-2xl">
                          <DialogHeader>
                            <DialogTitle>{ticket.title}</DialogTitle>
                            <DialogDescription>Ticket ID: {ticket.ticket_id}</DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4 mt-4">
                            <div>
                              <p className="text-sm text-muted-foreground mb-1">Description</p>
                              <p className="text-sm">{ticket.description}</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm text-muted-foreground mb-1">Category</p>
                                <p className="capitalize">{ticket.category}</p>
                              </div>
                              <div>
                                <p className="text-sm text-muted-foreground mb-1">Vehicle ID</p>
                                <p className="mono text-sm">{ticket.vehicle_id}</p>
                              </div>
                            </div>
                            {ticket.ai_diagnosis && (
                              <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                                <p className="text-sm text-muted-foreground mb-2">AI Diagnosis</p>
                                <p className="text-sm">{ticket.ai_diagnosis}</p>
                              </div>
                            )}
                            {user?.role !== "customer" && (
                              <div className="flex gap-2 pt-4">
                                <Select
                                  value={ticket.status}
                                  onValueChange={(value) => updateTicket(ticket.ticket_id, { status: value })}
                                >
                                  <SelectTrigger className="flex-1 bg-background/50">
                                    <SelectValue placeholder="Update Status" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="open">Open</SelectItem>
                                    <SelectItem value="in_progress">In Progress</SelectItem>
                                    <SelectItem value="resolved">Resolved</SelectItem>
                                    <SelectItem value="closed">Closed</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            )}
                          </div>
                        </DialogContent>
                      </Dialog>
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
