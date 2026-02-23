import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { 
  LogIn, LogOut, Receipt, FileText, CreditCard, User, Building2, 
  Calendar, DollarSign, AlertTriangle, CheckCircle, Clock, Eye,
  Download, ChevronRight, RefreshCw, Ticket, Plus, MessageSquare,
  Car, Send, Loader2
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  sent: "bg-blue-100 text-[#3B9EFF]",
  viewed: "bg-purple-100 text-[#8B5CF6]",
  partially_paid: "bg-yellow-100 text-[#EAB308]",
  paid: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  overdue: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  accepted: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  declined: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  // Ticket statuses
  open: "bg-blue-100 text-[#3B9EFF]",
  in_progress: "bg-yellow-100 text-[#EAB308]",
  resolved: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  closed: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
};

const priorityColors = {
  low: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  medium: "bg-yellow-100 text-[#EAB308]",
  high: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
};

export default function CustomerPortal() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [sessionToken, setSessionToken] = useState("");
  const [portalToken, setPortalToken] = useState("");
  const [contact, setContact] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  
  // Data
  const [invoices, setInvoices] = useState([]);
  const [estimates, setEstimates] = useState([]);
  const [payments, setPayments] = useState([]);
  const [statement, setStatement] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  
  // Detail dialogs
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [selectedEstimate, setSelectedEstimate] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showInvoiceDialog, setShowInvoiceDialog] = useState(false);
  const [showEstimateDialog, setShowEstimateDialog] = useState(false);
  const [showTicketDialog, setShowTicketDialog] = useState(false);
  
  // Create ticket dialog
  const [showCreateTicket, setShowCreateTicket] = useState(false);
  const [creatingTicket, setCreatingTicket] = useState(false);
  const [newTicket, setNewTicket] = useState({
    subject: "",
    description: "",
    priority: "medium",
    category: "general",
    vehicle_id: ""
  });
  
  // Comment state
  const [ticketComment, setTicketComment] = useState("");
  const [addingComment, setAddingComment] = useState(false);

  useEffect(() => {
    // Check for existing session
    const savedToken = localStorage.getItem("portal_session");
    if (savedToken) {
      setSessionToken(savedToken);
      validateSession(savedToken);
    }
  }, []);

  const validateSession = async (token) => {
    try {
      const res = await fetch(`${API}/customer-portal/session?session_token=${token}`);
      if (res.ok) {
        const data = await res.json();
        setIsLoggedIn(true);
        setContact(data.session);
        fetchDashboard(token);
      } else {
        localStorage.removeItem("portal_session");
      }
    } catch (e) {
      console.error("Session validation failed:", e);
    }
  };

  const handleLogin = async () => {
    if (!portalToken) return toast.error("Please enter your portal token");
    setLoading(true);
    
    try {
      const res = await fetch(`${API}/customer-portal/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: portalToken })
      });
      
      if (res.ok) {
        const data = await res.json();
        setSessionToken(data.session_token);
        setContact(data.contact);
        setIsLoggedIn(true);
        localStorage.setItem("portal_session", data.session_token);
        toast.success("Login successful!");
        fetchDashboard(data.session_token);
      } else {
        const err = await res.json();
        toast.error(err.detail || "Invalid portal token");
      }
    } catch (e) {
      toast.error("Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API}/customer-portal/logout?session_token=${sessionToken}`, { method: "POST" });
    } catch (e) {}
    
    setIsLoggedIn(false);
    setSessionToken("");
    setContact(null);
    setDashboard(null);
    localStorage.removeItem("portal_session");
    toast.success("Logged out");
  };

  const fetchDashboard = async (token) => {
    try {
      const res = await fetch(`${API}/customer-portal/dashboard?session_token=${token}`);
      if (res.ok) {
        const data = await res.json();
        setDashboard(data.dashboard);
      }
    } catch (e) {
      console.error("Failed to fetch dashboard:", e);
    }
  };

  const fetchInvoices = async () => {
    try {
      const res = await fetch(`${API}/customer-portal/invoices?session_token=${sessionToken}&per_page=50`);
      if (res.ok) {
        const data = await res.json();
        setInvoices(data.invoices || []);
      }
    } catch (e) {
      console.error("Failed to fetch invoices:", e);
    }
  };

  const fetchInvoiceDetail = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/customer-portal/invoices/${invoiceId}?session_token=${sessionToken}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedInvoice(data.invoice);
        setShowInvoiceDialog(true);
      }
    } catch (e) {
      toast.error("Failed to load invoice");
    }
  };

  const fetchEstimates = async () => {
    try {
      const res = await fetch(`${API}/customer-portal/estimates?session_token=${sessionToken}&per_page=50`);
      if (res.ok) {
        const data = await res.json();
        setEstimates(data.estimates || []);
      }
    } catch (e) {
      console.error("Failed to fetch estimates:", e);
    }
  };

  const fetchEstimateDetail = async (estimateId) => {
    try {
      const res = await fetch(`${API}/customer-portal/estimates/${estimateId}?session_token=${sessionToken}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedEstimate(data.estimate);
        setShowEstimateDialog(true);
      }
    } catch (e) {
      toast.error("Failed to load estimate");
    }
  };

  const handleAcceptEstimate = async (estimateId) => {
    try {
      const res = await fetch(`${API}/customer-portal/estimates/${estimateId}/accept?session_token=${sessionToken}`, { method: "POST" });
      if (res.ok) {
        toast.success("Estimate accepted!");
        setShowEstimateDialog(false);
        fetchEstimates();
        fetchDashboard(sessionToken);
      }
    } catch (e) {
      toast.error("Failed to accept estimate");
    }
  };

  const handleDeclineEstimate = async (estimateId) => {
    try {
      const res = await fetch(`${API}/customer-portal/estimates/${estimateId}/decline?session_token=${sessionToken}`, { method: "POST" });
      if (res.ok) {
        toast.success("Estimate declined");
        setShowEstimateDialog(false);
        fetchEstimates();
      }
    } catch (e) {
      toast.error("Failed to decline estimate");
    }
  };

  const fetchPayments = async () => {
    try {
      const res = await fetch(`${API}/customer-portal/payments?session_token=${sessionToken}&per_page=50`);
      if (res.ok) {
        const data = await res.json();
        setPayments(data.payments || []);
      }
    } catch (e) {
      console.error("Failed to fetch payments:", e);
    }
  };

  const fetchStatement = async () => {
    try {
      const res = await fetch(`${API}/customer-portal/statement?session_token=${sessionToken}`);
      if (res.ok) {
        const data = await res.json();
        setStatement(data.statement);
      }
    } catch (e) {
      console.error("Failed to fetch statement:", e);
    }
  };

  const fetchTickets = async () => {
    try {
      const res = await fetch(`${API}/customer-portal/tickets?session_token=${sessionToken}`);
      if (res.ok) {
        const data = await res.json();
        setTickets(data.tickets || []);
      }
    } catch (e) {
      console.error("Failed to fetch tickets:", e);
    }
  };

  const fetchVehicles = async () => {
    try {
      const res = await fetch(`${API}/customer-portal/vehicles?session_token=${sessionToken}`);
      if (res.ok) {
        const data = await res.json();
        setVehicles(data.vehicles || []);
      }
    } catch (e) {
      console.error("Failed to fetch vehicles:", e);
    }
  };

  const viewTicketDetails = async (ticketId) => {
    try {
      const res = await fetch(`${API}/customer-portal/tickets/${ticketId}?session_token=${sessionToken}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedTicket(data.ticket);
        setShowTicketDialog(true);
      }
    } catch (e) {
      toast.error("Failed to load ticket details");
    }
  };

  const createSupportTicket = async () => {
    if (!newTicket.subject.trim() || !newTicket.description.trim()) {
      toast.error("Subject and description are required");
      return;
    }
    
    setCreatingTicket(true);
    try {
      const res = await fetch(`${API}/customer-portal/tickets?session_token=${sessionToken}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newTicket)
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Support request ${data.ticket.ticket_id} created`);
        setShowCreateTicket(false);
        setNewTicket({ subject: "", description: "", priority: "medium", category: "general", vehicle_id: "" });
        fetchTickets();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create support request");
      }
    } catch (e) {
      toast.error("Failed to create support request");
    } finally {
      setCreatingTicket(false);
    }
  };

  const addCommentToTicket = async () => {
    if (!ticketComment.trim() || !selectedTicket) return;
    
    setAddingComment(true);
    try {
      const res = await fetch(
        `${API}/customer-portal/tickets/${selectedTicket.ticket_id}/comment?session_token=${sessionToken}&comment=${encodeURIComponent(ticketComment)}`,
        { method: "POST" }
      );
      
      if (res.ok) {
        toast.success("Comment added");
        setTicketComment("");
        viewTicketDetails(selectedTicket.ticket_id); // Refresh ticket
      } else {
        toast.error("Failed to add comment");
      }
    } catch (e) {
      toast.error("Failed to add comment");
    } finally {
      setAddingComment(false);
    }
  };

  useEffect(() => {
    if (isLoggedIn && sessionToken) {
      if (activeTab === "invoices") fetchInvoices();
      else if (activeTab === "estimates") fetchEstimates();
      else if (activeTab === "payments") fetchPayments();
      else if (activeTab === "statement") fetchStatement();
      else if (activeTab === "support") {
        fetchTickets();
        fetchVehicles();
      }
    }
  }, [activeTab, isLoggedIn, sessionToken]);

  const formatCurrency = (amount) => `₹${(amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  const formatDate = (date) => date ? new Date(date).toLocaleDateString("en-IN") : "-";

  // Login Screen
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4" data-testid="portal-login-page">
        <Card className="w-full max-w-md bg-[#111820]/10 backdrop-blur-lg border-white/20">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-[#C8FF00] rounded-full flex items-center justify-center mb-4">
              <Building2 className="h-8 w-8 text-[#080C0F] font-bold" />
            </div>
            <CardTitle className="text-2xl text-white">Customer Portal</CardTitle>
            <p className="text-[rgba(244,246,240,0.45)] text-sm mt-2">Access your invoices, estimates, and statements</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-[rgba(244,246,240,0.20)] mb-2 block">Portal Access Token</label>
              <Input
                value={portalToken}
                onChange={(e) => setPortalToken(e.target.value)}
                onKeyUp={(e) => e.key === "Enter" && handleLogin()}
                placeholder="Enter your portal token"
                className="bg-[#111820]/10 border-white/20 text-white placeholder:text-[rgba(244,246,240,0.45)]"
                data-testid="portal-token-input"
              />
              <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">Your portal token was sent to your email</p>
            </div>
            <Button 
              onClick={handleLogin} 
              disabled={loading}
              className="w-full bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold"
              data-testid="portal-login-btn"
            >
              {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <LogIn className="h-4 w-4 mr-2" />}
              {loading ? "Logging in..." : "Login to Portal"}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Portal Dashboard
  return (
    <div className="min-h-screen bg-[#111820]" data-testid="customer-portal-dashboard">
      {/* Header */}
      <header className="bg-[#111820] border-b px-6 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#C8FF00] rounded-full flex items-center justify-center">
              <Building2 className="h-5 w-5 text-[#080C0F] font-bold" />
            </div>
            <div>
              <h1 className="font-bold text-lg">{contact?.contact_name || dashboard?.contact?.name}</h1>
              <p className="text-xs text-[rgba(244,246,240,0.45)]">{contact?.company_name || dashboard?.contact?.company}</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" /> Logout
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-[#111820] border">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="invoices">Invoices</TabsTrigger>
            <TabsTrigger value="estimates">Estimates</TabsTrigger>
            <TabsTrigger value="payments">Payments</TabsTrigger>
            <TabsTrigger value="statement">Statement</TabsTrigger>
            <TabsTrigger value="support" data-testid="support-tab">
              <Ticket className="h-4 w-4 mr-1" />
              Support
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {dashboard && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-3">
                        <Receipt className="h-8 w-8 text-blue-500" />
                        <div>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">Total Invoiced</p>
                          <p className="text-xl font-bold text-[#3B9EFF]">{formatCurrency(dashboard.summary.total_invoiced)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[rgba(34,197,94,0.08)] border-green-200">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="h-8 w-8 text-green-500" />
                        <div>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">Total Paid</p>
                          <p className="text-xl font-bold text-green-700">{formatCurrency(dashboard.summary.total_paid)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[rgba(255,140,0,0.08)] border-orange-200">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-3">
                        <DollarSign className="h-8 w-8 text-orange-500" />
                        <div>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">Outstanding</p>
                          <p className="text-xl font-bold text-[#FF8C00]">{formatCurrency(dashboard.summary.total_outstanding)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className={dashboard.summary.overdue_invoices > 0 ? "bg-[rgba(255,59,47,0.08)] border-red-200" : "bg-[#111820]"}>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className={`h-8 w-8 ${dashboard.summary.overdue_invoices > 0 ? "text-red-500" : "text-[rgba(244,246,240,0.45)]"}`} />
                        <div>
                          <p className="text-xs text-[rgba(244,246,240,0.45)]">Overdue</p>
                          <p className={`text-xl font-bold ${dashboard.summary.overdue_invoices > 0 ? "text-red-700" : "text-[rgba(244,246,240,0.45)]"}`}>{dashboard.summary.overdue_invoices}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Invoices */}
                {dashboard.recent_invoices?.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Receipt className="h-5 w-5" /> Recent Invoices
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {dashboard.recent_invoices.map(inv => (
                          <div 
                            key={inv.invoice_id} 
                            className="flex justify-between items-center p-3 bg-[#111820] rounded-lg hover:bg-[rgba(255,255,255,0.05)] cursor-pointer"
                            onClick={() => fetchInvoiceDetail(inv.invoice_id)}
                          >
                            <div>
                              <p className="font-medium">{inv.invoice_number}</p>
                              <p className="text-xs text-[rgba(244,246,240,0.45)]">{formatDate(inv.invoice_date)}</p>
                            </div>
                            <div className="text-right flex items-center gap-3">
                              <div>
                                <p className="font-medium">{formatCurrency(inv.grand_total)}</p>
                                <Badge className={statusColors[inv.status] || "bg-[rgba(255,255,255,0.05)]"}>{inv.status}</Badge>
                              </div>
                              <ChevronRight className="h-5 w-5 text-[rgba(244,246,240,0.45)]" />
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Pending Estimates */}
                {dashboard.summary.pending_estimates > 0 && (
                  <Card className="border-yellow-200 bg-[rgba(234,179,8,0.08)]">
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileText className="h-8 w-8 text-[#EAB308]" />
                          <div>
                            <p className="font-medium">Pending Estimates</p>
                            <p className="text-sm text-[rgba(244,246,240,0.35)]">You have {dashboard.summary.pending_estimates} estimate(s) awaiting your review</p>
                          </div>
                        </div>
                        <Button size="sm" onClick={() => setActiveTab("estimates")}>View <ChevronRight className="h-4 w-4 ml-1" /></Button>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>

          {/* Invoices Tab */}
          <TabsContent value="invoices">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Receipt className="h-5 w-5" /> Your Invoices</CardTitle>
              </CardHeader>
              <CardContent>
                {invoices.length === 0 ? (
                  <p className="text-center text-[rgba(244,246,240,0.45)] py-8">No invoices found</p>
                ) : (
                  <div className="space-y-2">
                    {invoices.map(inv => (
                      <div 
                        key={inv.invoice_id}
                        className="flex justify-between items-center p-4 border rounded-lg hover:bg-[#111820] cursor-pointer"
                        onClick={() => fetchInvoiceDetail(inv.invoice_id)}
                      >
                        <div>
                          <p className="font-medium text-[#3B9EFF]">{inv.invoice_number}</p>
                          <p className="text-sm text-[rgba(244,246,240,0.45)]">Date: {formatDate(inv.invoice_date)} | Due: {formatDate(inv.due_date)}</p>
                        </div>
                        <div className="text-right flex items-center gap-3">
                          <div>
                            <p className="font-bold">{formatCurrency(inv.grand_total)}</p>
                            {inv.balance_due > 0 && <p className="text-xs text-red-600">Due: {formatCurrency(inv.balance_due)}</p>}
                          </div>
                          <Badge className={statusColors[inv.status]}>{inv.status}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Estimates Tab */}
          <TabsContent value="estimates">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5" /> Your Estimates</CardTitle>
              </CardHeader>
              <CardContent>
                {estimates.length === 0 ? (
                  <p className="text-center text-[rgba(244,246,240,0.45)] py-8">No estimates found</p>
                ) : (
                  <div className="space-y-2">
                    {estimates.map(est => (
                      <div 
                        key={est.estimate_id}
                        className="flex justify-between items-center p-4 border rounded-lg hover:bg-[#111820] cursor-pointer"
                        onClick={() => fetchEstimateDetail(est.estimate_id)}
                      >
                        <div>
                          <p className="font-medium text-[#3B9EFF]">{est.estimate_number}</p>
                          <p className="text-sm text-[rgba(244,246,240,0.45)]">Date: {formatDate(est.estimate_date)} | Expires: {formatDate(est.expiry_date)}</p>
                        </div>
                        <div className="text-right flex items-center gap-3">
                          <p className="font-bold">{formatCurrency(est.grand_total)}</p>
                          <Badge className={statusColors[est.status]}>{est.status}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Payments Tab */}
          <TabsContent value="payments">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><CreditCard className="h-5 w-5" /> Payment History</CardTitle>
              </CardHeader>
              <CardContent>
                {payments.length === 0 ? (
                  <p className="text-center text-[rgba(244,246,240,0.45)] py-8">No payments found</p>
                ) : (
                  <div className="space-y-2">
                    {payments.map(p => (
                      <div key={p.payment_id} className="flex justify-between items-center p-4 border rounded-lg">
                        <div>
                          <p className="font-medium">{formatCurrency(p.amount)}</p>
                          <p className="text-sm text-[rgba(244,246,240,0.45)]">{formatDate(p.payment_date)} • {p.payment_mode}</p>
                          {p.reference_number && <p className="text-xs text-[rgba(244,246,240,0.45)]">Ref: {p.reference_number}</p>}
                        </div>
                        <Badge className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]">Received</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Statement Tab */}
          <TabsContent value="statement">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5" /> Account Statement</CardTitle>
              </CardHeader>
              <CardContent>
                {statement && (
                  <div className="space-y-6">
                    {/* Summary */}
                    <div className="grid grid-cols-3 gap-4 bg-[#111820] p-4 rounded-lg">
                      <div className="text-center">
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Invoiced</p>
                        <p className="text-xl font-bold">{formatCurrency(statement.summary.total_invoiced)}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">Total Paid</p>
                        <p className="text-xl font-bold text-green-600">{formatCurrency(statement.summary.total_paid)}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">Balance Due</p>
                        <p className="text-xl font-bold text-red-600">{formatCurrency(statement.summary.balance_due)}</p>
                      </div>
                    </div>
                    
                    {/* Transactions */}
                    <div>
                      <h4 className="font-medium mb-3">Transactions</h4>
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-[#111820]">
                            <tr>
                              <th className="px-4 py-2 text-left">Date</th>
                              <th className="px-4 py-2 text-left">Description</th>
                              <th className="px-4 py-2 text-right">Amount</th>
                              <th className="px-4 py-2 text-center">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {statement.invoices?.map(inv => (
                              <tr key={inv.invoice_id} className="border-t">
                                <td className="px-4 py-2">{formatDate(inv.invoice_date)}</td>
                                <td className="px-4 py-2">Invoice {inv.invoice_number}</td>
                                <td className="px-4 py-2 text-right">{formatCurrency(inv.grand_total)}</td>
                                <td className="px-4 py-2 text-center"><Badge className={statusColors[inv.status]}>{inv.status}</Badge></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Support Tab */}
          <TabsContent value="support" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold">Support Requests</h2>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">View your service tickets and submit new requests</p>
              </div>
              <Button onClick={() => setShowCreateTicket(true)} data-testid="create-ticket-btn">
                <Plus className="h-4 w-4 mr-2" />
                New Request
              </Button>
            </div>
            
            <Card>
              <CardContent className="p-0">
                {tickets.length === 0 ? (
                  <div className="p-8 text-center text-[rgba(244,246,240,0.45)]">
                    <Ticket className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
                    <p>No support requests found</p>
                    <Button variant="outline" className="mt-4" onClick={() => setShowCreateTicket(true)}>
                      Submit Your First Request
                    </Button>
                  </div>
                ) : (
                  <div className="divide-y">
                    {tickets.map((ticket) => (
                      <div
                        key={ticket.ticket_id}
                        className="p-4 hover:bg-[#111820] cursor-pointer flex justify-between items-center"
                        onClick={() => viewTicketDetails(ticket.ticket_id)}
                        data-testid={`ticket-${ticket.ticket_id}`}
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-[rgba(244,246,240,0.45)]">{ticket.ticket_id}</span>
                            <Badge className={statusColors[ticket.status]}>{ticket.status?.replace("_", " ")}</Badge>
                            <Badge variant="outline" className={priorityColors[ticket.priority]}>{ticket.priority}</Badge>
                          </div>
                          <p className="font-medium mt-1">{ticket.subject}</p>
                          <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">Created: {formatDate(ticket.created_at)}</p>
                        </div>
                        <ChevronRight className="h-5 w-5 text-[rgba(244,246,240,0.45)]" />
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Create Ticket Dialog */}
      <Dialog open={showCreateTicket} onOpenChange={setShowCreateTicket}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              New Support Request
            </DialogTitle>
            <DialogDescription>
              Submit a support or service request. We'll get back to you as soon as possible.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Subject *</Label>
              <Input
                placeholder="Brief description of your issue"
                value={newTicket.subject}
                onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                data-testid="ticket-subject-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Description *</Label>
              <Textarea
                placeholder="Please provide details about your request..."
                rows={4}
                value={newTicket.description}
                onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                data-testid="ticket-description-input"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Category</Label>
                <Select value={newTicket.category} onValueChange={(v) => setNewTicket({ ...newTicket, category: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General Inquiry</SelectItem>
                    <SelectItem value="service">Service Request</SelectItem>
                    <SelectItem value="billing">Billing</SelectItem>
                    <SelectItem value="technical">Technical Issue</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select value={newTicket.priority} onValueChange={(v) => setNewTicket({ ...newTicket, priority: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {vehicles.length > 0 && (
              <div className="space-y-2">
                <Label>Related Vehicle (Optional)</Label>
                <Select value={newTicket.vehicle_id} onValueChange={(v) => setNewTicket({ ...newTicket, vehicle_id: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a vehicle" />
                  </SelectTrigger>
                  <SelectContent>
                    {vehicles.map((v) => (
                      <SelectItem key={v.vehicle_id} value={v.vehicle_id}>
                        <div className="flex items-center gap-2">
                          <Car className="h-4 w-4" />
                          {v.registration_number || v.model || v.vehicle_id}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateTicket(false)}>Cancel</Button>
            <Button onClick={createSupportTicket} disabled={creatingTicket} data-testid="submit-ticket-btn">
              {creatingTicket ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Submitting...</>
              ) : (
                <><Send className="h-4 w-4 mr-2" />Submit Request</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Ticket Detail Dialog */}
      <Dialog open={showTicketDialog} onOpenChange={setShowTicketDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
          {selectedTicket && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <span className="font-mono text-sm text-[rgba(244,246,240,0.45)]">{selectedTicket.ticket_id}</span>
                  <Badge className={statusColors[selectedTicket.status]}>{selectedTicket.status?.replace("_", " ")}</Badge>
                </DialogTitle>
                <DialogDescription>{selectedTicket.subject}</DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-[rgba(244,246,240,0.45)]">Category:</span> {selectedTicket.category}</div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Priority:</span> <Badge variant="outline" className={priorityColors[selectedTicket.priority]}>{selectedTicket.priority}</Badge></div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Created:</span> {formatDate(selectedTicket.created_at)}</div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Updated:</span> {formatDate(selectedTicket.updated_at)}</div>
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="font-medium mb-2">Description</h4>
                  <p className="text-sm text-[rgba(244,246,240,0.35)] whitespace-pre-wrap">{selectedTicket.description}</p>
                </div>
                
                {selectedTicket.updates?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3">Updates</h4>
                      <div className="space-y-3">
                        {selectedTicket.updates.map((update, idx) => (
                          <div key={idx} className={`p-3 rounded-lg text-sm ${update.author_type === "customer" ? "bg-blue-50 ml-8" : "bg-[#111820] mr-8"}`}>
                            <div className="flex justify-between mb-1">
                              <span className="font-medium">{update.author}</span>
                              <span className="text-xs text-[rgba(244,246,240,0.45)]">{formatDate(update.created_at)}</span>
                            </div>
                            <p className="text-[rgba(244,246,240,0.35)]">{update.comment}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
                
                {selectedTicket.status !== "closed" && selectedTicket.status !== "resolved" && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <Label>Add Comment</Label>
                      <div className="flex gap-2">
                        <Textarea
                          placeholder="Type your message..."
                          value={ticketComment}
                          onChange={(e) => setTicketComment(e.target.value)}
                          rows={2}
                          className="flex-1"
                        />
                        <Button onClick={addCommentToTicket} disabled={addingComment || !ticketComment.trim()}>
                          {addingComment ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
      <Dialog open={showInvoiceDialog} onOpenChange={setShowInvoiceDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedInvoice && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {selectedInvoice.invoice_number}
                  <Badge className={statusColors[selectedInvoice.status]}>{selectedInvoice.status}</Badge>
                </DialogTitle>
                <DialogDescription>Invoice Details</DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-[rgba(244,246,240,0.45)]">Date:</span> {formatDate(selectedInvoice.invoice_date)}</div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Due:</span> {formatDate(selectedInvoice.due_date)}</div>
                </div>
                
                {selectedInvoice.line_items?.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-[#111820]">
                        <tr>
                          <th className="px-3 py-2 text-left">Item</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-right">Rate</th>
                          <th className="px-3 py-2 text-right">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedInvoice.line_items.map((item, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="px-3 py-2">{item.name}</td>
                            <td className="px-3 py-2 text-right">{item.quantity}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(item.rate)}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(item.total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                
                <div className="bg-[#111820] p-4 rounded-lg space-y-1 text-sm w-48 ml-auto">
                  <div className="flex justify-between"><span>Sub Total:</span><span>{formatCurrency(selectedInvoice.sub_total)}</span></div>
                  <div className="flex justify-between"><span>Tax:</span><span>{formatCurrency(selectedInvoice.tax_total)}</span></div>
                  <Separator />
                  <div className="flex justify-between font-bold"><span>Total:</span><span>{formatCurrency(selectedInvoice.grand_total)}</span></div>
                  {selectedInvoice.amount_paid > 0 && <div className="flex justify-between text-green-600"><span>Paid:</span><span>-{formatCurrency(selectedInvoice.amount_paid)}</span></div>}
                  <div className="flex justify-between font-bold text-lg"><span>Balance:</span><span className={selectedInvoice.balance_due > 0 ? "text-red-600" : "text-green-600"}>{formatCurrency(selectedInvoice.balance_due)}</span></div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Estimate Detail Dialog */}
      <Dialog open={showEstimateDialog} onOpenChange={setShowEstimateDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedEstimate && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {selectedEstimate.estimate_number}
                  <Badge className={statusColors[selectedEstimate.status]}>{selectedEstimate.status}</Badge>
                </DialogTitle>
                <DialogDescription>Estimate Details</DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-[rgba(244,246,240,0.45)]">Date:</span> {formatDate(selectedEstimate.estimate_date)}</div>
                  <div><span className="text-[rgba(244,246,240,0.45)]">Expires:</span> {formatDate(selectedEstimate.expiry_date)}</div>
                </div>
                
                {selectedEstimate.line_items?.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-[#111820]">
                        <tr>
                          <th className="px-3 py-2 text-left">Item</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-right">Rate</th>
                          <th className="px-3 py-2 text-right">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedEstimate.line_items.map((item, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="px-3 py-2">{item.name}</td>
                            <td className="px-3 py-2 text-right">{item.quantity}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(item.rate)}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(item.total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                
                <div className="bg-[#111820] p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold">{formatCurrency(selectedEstimate.grand_total)}</p>
                </div>
                
                {selectedEstimate.status === "sent" && (
                  <div className="flex gap-3 justify-center">
                    <Button onClick={() => handleAcceptEstimate(selectedEstimate.estimate_id)} className="bg-[#22C55E] hover:bg-[#16a34a] text-[#080C0F]">
                      <CheckCircle className="h-4 w-4 mr-2" /> Accept Estimate
                    </Button>
                    <Button variant="outline" onClick={() => handleDeclineEstimate(selectedEstimate.estimate_id)}>
                      Decline
                    </Button>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
