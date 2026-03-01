import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { 
  Search, Ticket, Car, User, Calendar, Clock, MapPin,
  CheckCircle, XCircle, AlertCircle, Loader2, Zap,
  Phone, Mail, IndianRupee, FileText, CreditCard,
  ChevronRight, RefreshCw, History, Receipt
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Resolve workshop slug from subdomain or ?org query param
function getOrgSlug() {
  const hostname = window.location.hostname;
  const parts = hostname.split(".");
  if (parts.length >= 3 && !["www", "app", "api", "platform"].includes(parts[0])) {
    return parts[0];
  }
  const params = new URLSearchParams(window.location.search);
  return params.get("org") || null;
}

function getPublicHeaders(extra = {}) {
  const slug = getOrgSlug();
  const headers = { "Content-Type": "application/json", ...extra };
  if (slug) headers["X-Organization-Slug"] = slug;
  return headers;
}

// Status colors and icons
const statusConfig = {
  pending_payment: { label: "Pending Payment", color: "bg-amber-500", icon: CreditCard },
  open: { label: "Open", color: "bg-blue-500", icon: Ticket },
  assigned: { label: "Technician Assigned", color: "bg-bw-purple/[0.08]0", icon: User },
  technician_assigned: { label: "Technician Assigned", color: "bg-bw-purple/[0.08]0", icon: User },
  estimate_sent: { label: "Estimate Shared", color: "bg-cyan-500", icon: FileText },
  estimate_approved: { label: "Estimate Approved", color: "bg-bw-green/[0.08]0", icon: CheckCircle },
  work_in_progress: { label: "Work In Progress", color: "bg-bw-orange/[0.08]0", icon: Loader2 },
  work_completed: { label: "Work Completed", color: "bg-bw-volt/[0.08]0", icon: CheckCircle },
  closed: { label: "Closed", color: "bg-slate-500", icon: CheckCircle },
};

const priorityColors = {
  low: "bg-bw-green/[0.08]0/20 text-green-400",
  medium: "bg-bw-amber/[0.08]0/20 text-yellow-400",
  high: "bg-bw-orange/[0.08]0/20 text-orange-400",
  critical: "bg-bw-red/[0.08]0/20 text-red-400",
};

export default function TrackTicket() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // State
  const [loading, setLoading] = useState(false);
  const [lookupMethod, setLookupMethod] = useState("ticket_id"); // ticket_id, contact
  const [lookupValue, setLookupValue] = useState("");
  const [ticketList, setTicketList] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketDetails, setTicketDetails] = useState(null);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [approving, setApproving] = useState(false);
  
  // Check URL params on load
  useEffect(() => {
    const ticketId = searchParams.get("id");
    const token = searchParams.get("token");
    const contact = searchParams.get("contact");
    
    if (ticketId) {
      setLookupValue(ticketId);
      setLookupMethod("ticket_id");
      if (token || contact) {
        fetchTicketDetails(ticketId, token, contact);
      }
    }
  }, [searchParams]);

  const handleLookup = async () => {
    if (!lookupValue.trim()) {
      toast.error("Please enter a ticket ID or contact number");
      return;
    }
    
    setLoading(true);
    
    try {
      const body = {};
      if (lookupMethod === "ticket_id") {
        body.ticket_id = lookupValue.trim();
      } else {
        // Check if it's an email or phone
        if (lookupValue.includes("@")) {
          body.email = lookupValue.trim();
        } else {
          body.contact_number = lookupValue.trim();
        }
      }
      
      const res = await fetch(`${API}/public/tickets/lookup`, {
        method: "POST",
        headers: getPublicHeaders(),
        body: JSON.stringify(body)
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "No tickets found");
      }
      
      if (data.tickets.length === 1) {
        // Single ticket - fetch details directly
        const ticket = data.tickets[0];
        fetchTicketDetails(ticket.ticket_id, ticket.public_access_token, lookupValue);
      } else {
        // Multiple tickets - show list
        setTicketList(data.tickets);
        setSelectedTicket(null);
        setTicketDetails(null);
      }
    } catch (error) {
      toast.error(error.message || "Failed to find tickets");
      setTicketList([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTicketDetails = async (ticketId, token = null, contact = null) => {
    setLoading(true);
    
    try {
      let url = `${API}/public/tickets/${ticketId}?`;
      if (token) url += `token=${token}`;
      else if (contact) url += `contact=${encodeURIComponent(contact)}`;
      
      const res = await fetch(url, { headers: getPublicHeaders() });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to fetch ticket details");
      }
      
      setSelectedTicket(ticketId);
      setTicketDetails(data);
      
      // Store token for future use
      if (data.ticket?.public_access_token) {
        localStorage.setItem(`ticket_token_${ticketId}`, data.ticket.public_access_token);
      }
    } catch (error) {
      toast.error(error.message || "Failed to load ticket details");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTicket = (ticket) => {
    const token = ticket.public_access_token || localStorage.getItem(`ticket_token_${ticket.ticket_id}`);
    fetchTicketDetails(ticket.ticket_id, token, lookupValue);
  };

  const handleApproveEstimate = async () => {
    if (!ticketDetails?.ticket?.ticket_id) return;
    
    setApproving(true);
    
    try {
      const ticketId = ticketDetails.ticket.ticket_id;
      const token = ticketDetails.ticket.public_access_token || localStorage.getItem(`ticket_token_${ticketId}`);
      
      const res = await fetch(`${API}/public/tickets/${ticketId}/approve-estimate?token=${token}`, {
        method: "POST",
        headers: getPublicHeaders()
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to approve estimate");
      }
      
      toast.success("Estimate approved! Work will begin shortly.");
      setShowApproveDialog(false);
      
      // Refresh ticket details
      fetchTicketDetails(ticketId, token);
    } catch (error) {
      toast.error(error.message || "Failed to approve estimate");
    } finally {
      setApproving(false);
    }
  };

  const getStatusInfo = (status) => {
    return statusConfig[status] || { label: status, color: "bg-slate-500", icon: Ticket };
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  // Lookup Form
  const LookupForm = () => (
    <Card className="border-white/[0.07] border-700 bg-slate-800/50 backdrop-blur">
      <CardHeader className="text-center">
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-bw-green/[0.08]0/20 rounded-full">
            <Search className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <CardTitle className="text-white">Track Your Service Request</CardTitle>
        <CardDescription>Enter your ticket ID or contact details to view status</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs value={lookupMethod} onValueChange={setLookupMethod} className="w-full">
          <TabsList className="w-full bg-slate-700/50">
            <TabsTrigger value="ticket_id" className="flex-1">Ticket ID</TabsTrigger>
            <TabsTrigger value="contact" className="flex-1">Phone / Email</TabsTrigger>
          </TabsList>
        </Tabs>
        
        <div className="space-y-2">
          <Label className="text-slate-300">
            {lookupMethod === "ticket_id" ? "Ticket ID" : "Phone Number or Email"}
          </Label>
          <Input
            placeholder={lookupMethod === "ticket_id" ? "e.g., tkt_abc123def456" : "e.g., 9876543210 or email@example.com"}
            className="bg-slate-700/50 border-white/[0.07] border-600"
            value={lookupValue}
            onChange={(e) => setLookupValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLookup()}
            data-testid="lookup-input"
          />
        </div>
        
        <Button
          onClick={handleLookup}
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700"
          data-testid="lookup-btn"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
          Find Ticket
        </Button>
        
        <div className="text-center">
          <Button
            variant="link"
            onClick={() => navigate("/submit-ticket")}
            className="text-green-400"
          >
            Submit a new service request
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  // Ticket List
  const TicketList = () => (
    <Card className="border-white/[0.07] border-700 bg-slate-800/50 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">Your Tickets</CardTitle>
          <Button variant="ghost" size="sm" onClick={() => { setTicketList([]); setLookupValue(""); }}>
            <Search className="h-4 w-4 mr-2" />
            New Search
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {ticketList.map((ticket) => {
          const status = getStatusInfo(ticket.status);
          const StatusIcon = status.icon;
          return (
            <div
              key={ticket.ticket_id}
              onClick={() => handleSelectTicket(ticket)}
              className="p-4 bg-slate-700/50 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors"
              data-testid={`ticket-item-${ticket.ticket_id}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${status.color}/20`}>
                    <StatusIcon className={`h-4 w-4 ${status.color.replace("bg-", "text-")}`} />
                  </div>
                  <div>
                    <p className="text-white font-mono text-sm">{ticket.ticket_id}</p>
                    <p className="text-slate-400 text-sm truncate max-w-[200px]">{ticket.title}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={status.color}>{status.label}</Badge>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </div>
              </div>
              <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Car className="h-3 w-3" />
                  {ticket.vehicle_number}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatDate(ticket.created_at)}
                </span>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );

  // Ticket Details
  const TicketDetails = () => {
    if (!ticketDetails) return null;
    
    const ticket = ticketDetails.ticket;
    const estimate = ticketDetails.estimate;
    const invoice = ticketDetails.invoice;
    const activities = ticketDetails.activities || [];
    const payments = ticketDetails.payments || [];
    
    const status = getStatusInfo(ticket.status);
    const StatusIcon = status.icon;
    
    return (
      <div className="space-y-6">
        {/* Header Card */}
        <Card className="border-white/[0.07] border-700 bg-slate-800/50 backdrop-blur">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <Button variant="ghost" onClick={() => { setSelectedTicket(null); setTicketDetails(null); }}>
                ← Back
              </Button>
              <Button variant="ghost" size="sm" onClick={() => fetchTicketDetails(ticket.ticket_id, ticket.public_access_token)}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
            
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-full ${status.color}/20`}>
                <StatusIcon className={`h-6 w-6 ${status.color.replace("bg-", "text-")}`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className={status.color}>{status.label}</Badge>
                  <Badge className={priorityColors[ticket.priority]}>{ticket.priority}</Badge>
                </div>
                <h2 className="text-xl font-semibold text-white">{ticket.title}</h2>
                <p className="text-slate-400 font-mono text-sm">{ticket.ticket_id}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-4 border-t border-white/[0.07] border-700">
              <div>
                <p className="text-slate-400 text-xs">Vehicle</p>
                <p className="text-white font-medium">{ticket.vehicle_number}</p>
                <p className="text-slate-400 text-xs">{ticket.vehicle_model} ({ticket.vehicle_oem})</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Customer</p>
                <p className="text-white font-medium">{ticket.customer_name}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Service Type</p>
                <p className="text-white font-medium capitalize">{ticket.ticket_type?.replace("_", " ")}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Created</p>
                <p className="text-white font-medium">{formatDate(ticket.created_at)}</p>
              </div>
            </div>
            
            {ticket.assigned_technician_name && (
              <div className="mt-4 p-3 bg-slate-700/50 rounded-lg flex items-center gap-3">
                <User className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-slate-400 text-xs">Assigned Technician</p>
                  <p className="text-white font-medium">{ticket.assigned_technician_name}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Estimate Card */}
        {estimate && (
          <Card className="border-white/[0.07] border-700 bg-slate-800/50 backdrop-blur">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2">
                  <FileText className="h-5 w-5 text-green-500" />
                  Service Estimate
                </CardTitle>
                <Badge className={
                  estimate.status === "approved" ? "bg-bw-green/[0.08]0" :
                  estimate.status === "sent" ? "bg-blue-500" :
                  estimate.status === "locked" ? "bg-slate-500" :
                  "bg-amber-500"
                }>
                  {estimate.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Line Items */}
              {estimate.line_items?.length > 0 && (
                <div className="space-y-2">
                  {estimate.line_items.map((item, idx) => (
                    <div key={idx} className="flex justify-between p-2 bg-slate-700/50 rounded">
                      <div>
                        <p className="text-white text-sm">{item.name}</p>
                        <p className="text-slate-400 text-xs">
                          {item.quantity} × {formatCurrency(item.unit_price)}
                        </p>
                      </div>
                      <p className="text-white font-medium">{formatCurrency(item.line_total)}</p>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Totals */}
              <div className="pt-3 border-t border-white/[0.07] border-700 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Subtotal</span>
                  <span className="text-white">{formatCurrency(estimate.subtotal)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Tax</span>
                  <span className="text-white">{formatCurrency(estimate.tax_total)}</span>
                </div>
                <div className="flex justify-between text-lg font-semibold">
                  <span className="text-white">Total</span>
                  <span className="text-green-400">{formatCurrency(estimate.grand_total)}</span>
                </div>
              </div>
              
              {/* Approve Button */}
              {estimate.can_approve && (
                <Button
                  onClick={() => setShowApproveDialog(true)}
                  className="w-full bg-green-600 hover:bg-green-700"
                  data-testid="approve-estimate-btn"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve Estimate
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Invoice Card */}
        {invoice && (
          <Card className="border-white/[0.07] border-700 bg-slate-800/50 backdrop-blur">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2">
                  <Receipt className="h-5 w-5 text-green-500" />
                  Invoice
                </CardTitle>
                <Badge className={
                  invoice.status === "paid" ? "bg-bw-green/[0.08]0" :
                  invoice.status === "partial" ? "bg-amber-500" :
                  "bg-blue-500"
                }>
                  {invoice.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <div>
                  <p className="text-slate-400 text-xs">Invoice Number</p>
                  <p className="text-white font-mono">{invoice.invoice_number}</p>
                </div>
                <div className="text-right">
                  <p className="text-slate-400 text-xs">Balance Due</p>
                  <p className="text-green-400 text-xl font-bold">{formatCurrency(invoice.balance)}</p>
                </div>
              </div>
              
              {invoice.balance > 0 && invoice.payment_link_url && (
                <Button
                  onClick={() => window.open(invoice.payment_link_url, "_blank")}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  <CreditCard className="h-4 w-4 mr-2" />
                  Pay Now - {formatCurrency(invoice.balance)}
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Activity Timeline */}
        {activities.length > 0 && (
          <Card className="border-white/[0.07] border-700 bg-slate-800/50 backdrop-blur">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <History className="h-5 w-5 text-green-500" />
                Activity History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activities.map((activity, idx) => (
                  <div key={idx} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-2 h-2 rounded-full bg-bw-green/[0.08]0" />
                      {idx < activities.length - 1 && <div className="w-0.5 h-full bg-slate-700 mt-1" />}
                    </div>
                    <div className="flex-1 pb-4">
                      <p className="text-white text-sm">{activity.description}</p>
                      <p className="text-slate-400 text-xs mt-1">
                        {activity.user_name} • {formatDate(activity.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Payments */}
        {payments.length > 0 && (
          <Card className="border-white/[0.07] border-700 bg-slate-800/50 backdrop-blur">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <IndianRupee className="h-5 w-5 text-green-500" />
                Payment History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {payments.map((payment, idx) => (
                  <div key={idx} className="flex justify-between p-3 bg-slate-700/50 rounded">
                    <div>
                      <p className="text-white text-sm">{payment.description || payment.type}</p>
                      <p className="text-slate-400 text-xs">{formatDate(payment.created_at)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-green-400 font-medium">{formatCurrency(payment.amount)}</p>
                      <Badge className="bg-bw-green/[0.08]0/20 text-green-400 text-xs">{payment.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4">
      <div className="max-w-2xl mx-auto" data-testid="track-ticket-page">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Zap className="h-10 w-10 text-green-500" />
            <h1 className="text-3xl font-bold text-white">Battwheels Service</h1>
          </div>
        </div>

        {/* Content */}
        {selectedTicket && ticketDetails ? (
          <TicketDetails />
        ) : ticketList.length > 0 ? (
          <TicketList />
        ) : (
          <LookupForm />
        )}

        {/* Approve Dialog */}
        <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
          <DialogContent className="bg-slate-800 border-white/[0.07] border-700">
            <DialogHeader>
              <DialogTitle className="text-white">Approve Service Estimate</DialogTitle>
              <DialogDescription>
                By approving, you authorize Battwheels to proceed with the service at the estimated cost.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <div className="p-4 bg-slate-700/50 rounded-lg">
                <p className="text-slate-400 text-sm">Estimated Total</p>
                <p className="text-green-400 text-2xl font-bold">
                  {formatCurrency(ticketDetails?.estimate?.grand_total)}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowApproveDialog(false)}>Cancel</Button>
              <Button
                onClick={handleApproveEstimate}
                disabled={approving}
                className="bg-green-600 hover:bg-green-700"
              >
                {approving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                Confirm Approval
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 mt-8">
          <p>© 2026 Battwheels Services Pvt Ltd. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
