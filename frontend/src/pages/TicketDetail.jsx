import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Clock, User, Car, FileText, DollarSign, Activity, AlertTriangle, CheckCircle, Wrench, Loader2, Send, Plus, Trash2, Brain, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { API } from "../App";

const STATUS_CONFIG = {
  open: { label: "Open", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  in_progress: { label: "In Progress", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  resolved: { label: "Resolved", color: "bg-bw-volt/20 text-bw-volt border-bw-volt/30" },
  closed: { label: "Closed", color: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30" },
  waiting_for_parts: { label: "Waiting Parts", color: "bg-orange-500/20 text-orange-400 border-orange-500/30" },
};

const PRIORITY_CONFIG = {
  low: { label: "Low", color: "text-zinc-400" },
  medium: { label: "Medium", color: "text-amber-400" },
  high: { label: "High", color: "text-orange-400" },
  critical: { label: "Critical", color: "text-red-400" },
};

export default function TicketDetail({ user }) {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [newNote, setNewNote] = useState("");
  const [addingNote, setAddingNote] = useState(false);
  const [estimate, setEstimate] = useState(null);
  const [estimateLoading, setEstimateLoading] = useState(false);
  const [creatingEstimate, setCreatingEstimate] = useState(false);
  const orgId = user?.current_organization?.organization_id;
  
  // Failure Card modal state
  const [failureCardModal, setFailureCardModal] = useState(false);
  const [failureCard, setFailureCard] = useState(null);
  const [failureCardForm, setFailureCardForm] = useState({
    confirmed_root_cause: "",
    efi_suggestion_correct: "",
    resolution_steps: "",
    technician_notes: "",
  });
  const [failureCardSubmitting, setFailureCardSubmitting] = useState(false);

  const headers = {
    Authorization: `Bearer ${localStorage.getItem("token")}`,
    "Content-Type": "application/json",
    ...(orgId ? { "X-Organization-ID": orgId } : {}),
  };

  const fetchTicket = useCallback(async () => {
    try {
      const res = await fetch(`${API}/tickets/${ticketId}`, { headers });
      if (!res.ok) throw new Error("Failed to fetch ticket");
      const data = await res.json();
      setTicket(data);
    } catch (err) {
      toast.error("Failed to load ticket details");
    }
  }, [ticketId]);

  const fetchActivities = useCallback(async () => {
    try {
      const res = await fetch(`${API}/tickets/${ticketId}/activities`, { headers });
      if (res.ok) {
        const data = await res.json();
        setActivities(Array.isArray(data) ? data : data.activities || []);
      }
    } catch (err) { /* silently fail */ }
  }, [ticketId]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await Promise.all([fetchTicket(), fetchActivities(), fetchEstimate()]);
      setLoading(false);
    })();
  }, [fetchTicket, fetchActivities]);

  const fetchEstimate = async () => {
    setEstimateLoading(true);
    try {
      const res = await fetch(`${API}/ticket-estimates/tickets/${ticketId}/estimate`, { headers });
      if (res.ok) {
        const data = await res.json();
        setEstimate(data);
      }
    } catch (err) { /* no estimate yet */ }
    setEstimateLoading(false);
  };

  const handleCreateEstimate = async () => {
    setCreatingEstimate(true);
    try {
      const res = await fetch(`${API}/ticket-estimates/tickets/${ticketId}/estimate/ensure`, {
        method: "POST", headers
      });
      if (!res.ok) throw new Error("Failed to create estimate");
      const data = await res.json();
      setEstimate(data.estimate || data);
      toast.success("Estimate created and linked to ticket");
    } catch (err) {
      toast.error("Failed to create estimate");
    }
    setCreatingEstimate(false);
  };

  const handleStatusUpdate = async (newStatus) => {
    // If closing/resolving, show failure card modal first
    if (newStatus === "closed" || newStatus === "resolved") {
      setStatusUpdating(true);
      try {
        // First update the ticket status
        const res = await fetch(`${API}/tickets/${ticketId}`, {
          method: "PUT",
          headers,
          body: JSON.stringify({ status: newStatus }),
        });
        if (!res.ok) throw new Error("Update failed");
        const updated = await res.json();
        setTicket(updated);
        toast.success(`Status updated to ${STATUS_CONFIG[newStatus]?.label || newStatus}`);
        fetchActivities();

        // Fetch failure card for this ticket
        try {
          const fcRes = await fetch(`${API}/failure-cards?ticket_id=${ticketId}`, { headers });
          if (fcRes.ok) {
            const fcData = await fcRes.json();
            const cards = Array.isArray(fcData) ? fcData : fcData.data || [];
            if (cards.length > 0) {
              setFailureCard(cards[0]);
              setFailureCardForm({
                confirmed_root_cause: cards[0].confirmed_root_cause || cards[0].initial_diagnosis || "",
                efi_suggestion_correct: "",
                resolution_steps: cards[0].resolution_steps || "",
                technician_notes: cards[0].technician_notes || "",
              });
            }
          }
        } catch (e) {
          console.warn("Failure card fetch failed:", e);
        }
        setFailureCardModal(true);
      } catch (err) {
        toast.error("Failed to update status");
      }
      setStatusUpdating(false);
      return;
    }

    setStatusUpdating(true);
    try {
      const res = await fetch(`${API}/tickets/${ticketId}`, {
        method: "PUT",
        headers,
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error("Update failed");
      const updated = await res.json();
      setTicket(updated);
      toast.success(`Status updated to ${STATUS_CONFIG[newStatus]?.label || newStatus}`);
      fetchActivities();
    } catch (err) {
      toast.error("Failed to update status");
    }
    setStatusUpdating(false);
  };

  const handleFailureCardSubmit = async () => {
    if (!failureCard) return;
    setFailureCardSubmitting(true);
    try {
      const res = await fetch(`${API}/failure-cards/${failureCard.failure_card_id}`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          confirmed_root_cause: failureCardForm.confirmed_root_cause,
          efi_suggestion_correct: failureCardForm.efi_suggestion_correct === "yes",
          resolution_steps: failureCardForm.resolution_steps,
          technician_notes: failureCardForm.technician_notes,
          status: "completed",
        }),
      });
      if (!res.ok) throw new Error("Update failed");
      toast.success("Failure card completed — data fed to EFI brain");
      setFailureCardModal(false);
    } catch (err) {
      toast.error("Failed to update failure card");
    }
    setFailureCardSubmitting(false);
  };

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    setAddingNote(true);
    try {
      const res = await fetch(`${API}/tickets/${ticketId}/activities`, {
        method: "POST",
        headers,
        body: JSON.stringify({ type: "note", content: newNote, is_internal: true }),
      });
      if (!res.ok) throw new Error("Add note failed");
      setNewNote("");
      fetchActivities();
      toast.success("Note added");
    } catch (err) {
      toast.error("Failed to add note");
    }
    setAddingNote(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]" data-testid="ticket-detail-loading">
        <Loader2 className="w-8 h-8 animate-spin text-bw-volt" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4" data-testid="ticket-detail-not-found">
        <AlertTriangle className="w-12 h-12 text-amber-400" />
        <p className="text-zinc-400">Ticket not found</p>
        <Button variant="outline" onClick={() => navigate("/tickets")} data-testid="back-to-tickets-btn">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Tickets
        </Button>
      </div>
    );
  }

  const st = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
  const pr = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
  const created = ticket.created_at ? new Date(ticket.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—";

  return (
    <div className="space-y-6" data-testid="ticket-detail-page">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/tickets")} data-testid="ticket-back-btn">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold font-mono text-bw-volt" data-testid="ticket-number">
              {ticket.ticket_number || ticketId}
            </h1>
            <p className="text-sm text-zinc-400">{ticket.title}</p>
          </div>
          <Badge className={`${st.color} border font-mono text-xs ml-2`} data-testid="ticket-status-badge">{st.label}</Badge>
          <Badge variant="outline" className={`${pr.color} border-current/30 font-mono text-xs`} data-testid="ticket-priority-badge">{pr.label}</Badge>
        </div>
        <div className="text-xs text-zinc-500 flex items-center gap-1">
          <Clock className="w-3 h-3" /> Created: {created}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content — left 2 cols */}
        <div className="lg:col-span-2 space-y-6">
          {/* Section 1: Customer & Vehicle */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-customer-section">
            <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2"><User className="w-4 h-4" /> Customer & Vehicle</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-zinc-500">Customer</span><p className="text-zinc-200 font-medium">{ticket.customer_name || "—"}</p></div>
              <div><span className="text-zinc-500">Contact</span><p className="text-zinc-200">{ticket.contact_number || "—"}</p></div>
              <div><span className="text-zinc-500">Vehicle</span><p className="text-zinc-200">{[ticket.vehicle_make, ticket.vehicle_model].filter(Boolean).join(" ") || "—"}</p></div>
              <div><span className="text-zinc-500">Reg Number</span><p className="text-zinc-200 font-mono">{ticket.vehicle_number || "—"}</p></div>
            </CardContent>
          </Card>

          {/* Section 2: Service Details */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-service-section">
            <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2"><Wrench className="w-4 h-4" /> Service Details</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div><span className="text-zinc-500">Issue Description</span><p className="text-zinc-200 mt-1">{ticket.description || "No description"}</p></div>
              <div className="grid grid-cols-3 gap-4">
                <div><span className="text-zinc-500">Category</span><p className="text-zinc-200">{ticket.category || "—"}</p></div>
                <div><span className="text-zinc-500">Issue Type</span><p className="text-zinc-200">{ticket.issue_type || "—"}</p></div>
                <div><span className="text-zinc-500">Ticket Type</span><p className="text-zinc-200 capitalize">{ticket.ticket_type || "—"}</p></div>
              </div>
            </CardContent>
          </Card>

          {/* Section 3: Costs */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-costs-section">
            <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2"><DollarSign className="w-4 h-4" /> Financials</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div><span className="text-zinc-500">Estimated</span><p className="text-zinc-200 font-mono">{ticket.estimated_cost != null ? `₹${Number(ticket.estimated_cost).toLocaleString("en-IN")}` : "—"}</p></div>
              <div><span className="text-zinc-500">Parts Cost</span><p className="text-zinc-200 font-mono">{ticket.parts_cost != null ? `₹${Number(ticket.parts_cost).toLocaleString("en-IN")}` : "—"}</p></div>
              <div><span className="text-zinc-500">Labor Cost</span><p className="text-zinc-200 font-mono">{ticket.labor_cost != null ? `₹${Number(ticket.labor_cost).toLocaleString("en-IN")}` : "—"}</p></div>
              <div><span className="text-zinc-500">Actual Cost</span><p className="text-bw-volt font-mono font-bold">{ticket.actual_cost != null ? `₹${Number(ticket.actual_cost).toLocaleString("en-IN")}` : "—"}</p></div>
            </CardContent>
          </Card>

          {/* Section 4: Estimate */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-estimate-section">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2"><FileText className="w-4 h-4" /> Estimate</CardTitle>
                {estimate && (
                  <Badge className={estimate.status === "approved" ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : estimate.status === "sent" ? "bg-blue-500/20 text-blue-400 border-blue-500/30" : "bg-zinc-500/20 text-zinc-400 border-zinc-500/30"} data-testid="estimate-status-badge">
                    {estimate.status || "Draft"}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {estimateLoading ? (
                <div className="flex items-center justify-center py-4"><Loader2 className="w-5 h-5 animate-spin text-zinc-400" /></div>
              ) : estimate ? (
                <div className="space-y-3" data-testid="estimate-details">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="text-zinc-500">Estimate #</span><p className="text-zinc-200 font-mono">{estimate.estimate_number || estimate.estimate_id}</p></div>
                    <div><span className="text-zinc-500">Total</span><p className="text-bw-volt font-mono font-bold">{estimate.grand_total != null ? `₹${Number(estimate.grand_total).toLocaleString("en-IN")}` : "—"}</p></div>
                  </div>
                  {estimate.line_items && estimate.line_items.length > 0 && (
                    <div className="border-t border-zinc-800 pt-2">
                      <p className="text-xs text-zinc-500 mb-2">{estimate.line_items.length} line item(s)</p>
                      {estimate.line_items.slice(0, 3).map((item, i) => (
                        <div key={i} className="flex justify-between text-xs text-zinc-400 py-1">
                          <span>{item.description || item.name || `Item ${i + 1}`}</span>
                          <span className="font-mono">₹{Number(item.amount || item.total || 0).toLocaleString("en-IN")}</span>
                        </div>
                      ))}
                      {estimate.line_items.length > 3 && <p className="text-xs text-zinc-600">+ {estimate.line_items.length - 3} more</p>}
                    </div>
                  )}
                  <Button variant="outline" size="sm" className="w-full border-zinc-700 text-zinc-300" onClick={() => navigate(`/estimates?id=${estimate.estimate_id}`)} data-testid="view-full-estimate-btn">
                    View Full Estimate
                  </Button>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-zinc-500 text-sm mb-3">No estimate created for this ticket yet</p>
                  <Button size="sm" onClick={handleCreateEstimate} disabled={creatingEstimate} className="bg-bw-volt text-black hover:bg-bw-volt-hover" data-testid="create-estimate-btn">
                    {creatingEstimate ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                    Create Estimate
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Section 5: Activity Timeline */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-activity-section">
            <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2"><Activity className="w-4 h-4" /> Activity Timeline</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Textarea
                  placeholder="Add an internal note..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  className="bg-zinc-800 border-zinc-700 text-zinc-200 text-sm min-h-[60px]"
                  data-testid="ticket-note-input"
                />
                <Button size="sm" onClick={handleAddNote} disabled={addingNote || !newNote.trim()} className="bg-bw-volt text-black hover:bg-bw-volt-hover self-end" data-testid="ticket-add-note-btn">
                  {addingNote ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
              </div>
              {activities.length === 0 ? (
                <p className="text-zinc-500 text-sm text-center py-4">No activity recorded yet</p>
              ) : (
                <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                  {activities.map((a, i) => (
                    <div key={a.activity_id || i} className="flex gap-3 text-sm border-l-2 border-zinc-700 pl-3" data-testid={`activity-item-${i}`}>
                      <div className="flex-1">
                        <p className="text-zinc-300">{a.content || a.description || a.type}</p>
                        <p className="text-zinc-600 text-xs mt-1">
                          {a.user_name || "System"} · {a.created_at ? new Date(a.created_at).toLocaleString("en-IN") : ""}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar — right col */}
        <div className="space-y-6">
          {/* Status & Actions */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-actions-section">
            <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-zinc-300">Status & Actions</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs text-zinc-500 mb-1 block">Update Status</label>
                <Select value={ticket.status} onValueChange={handleStatusUpdate} disabled={statusUpdating}>
                  <SelectTrigger className="bg-zinc-800 border-zinc-700 text-zinc-200" data-testid="ticket-status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="waiting_for_parts">Waiting for Parts</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs text-zinc-500 mb-1 block">Assigned To</label>
                <p className="text-sm text-zinc-200">{ticket.assigned_technician_name || ticket.assigned_technician_id || "Unassigned"}</p>
              </div>
              {ticket.resolution && (
                <div>
                  <label className="text-xs text-zinc-500 mb-1 block">Resolution</label>
                  <p className="text-sm text-zinc-200">{ticket.resolution}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Invoice Info */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-invoice-section">
            <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2"><FileText className="w-4 h-4" /> Invoice</CardTitle></CardHeader>
            <CardContent>
              {ticket.invoice_id ? (
                <div className="space-y-2 text-sm">
                  <p className="text-zinc-200">Invoice: <span className="font-mono text-bw-volt">{ticket.invoice_number || ticket.invoice_id}</span></p>
                  {ticket.invoice_status && <Badge variant="outline" className="text-xs">{ticket.invoice_status}</Badge>}
                </div>
              ) : (
                <p className="text-zinc-500 text-sm">No invoice generated yet</p>
              )}
            </CardContent>
          </Card>

          {/* Failure Card Indicator */}
          {(ticket.status === "closed" || ticket.status === "resolved") && (
            <Card className="bg-zinc-900/60 border-zinc-800 border-l-2 border-l-amber-500" data-testid="ticket-failure-card-section">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                  <Brain className="w-4 h-4 text-amber-400" /> Failure Card
                </CardTitle>
              </CardHeader>
              <CardContent>
                {failureCard && failureCard.status === "completed" ? (
                  <div className="space-y-2 text-sm">
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">Completed</Badge>
                    <p className="text-zinc-400 text-xs mt-1">Resolution data fed to EFI brain</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30" data-testid="failure-card-draft-badge">Draft — Needs Review</Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full border-amber-500/40 text-amber-400 hover:bg-amber-500/10 mt-2"
                      onClick={() => {
                        if (!failureCard) {
                          fetch(`${API}/failure-cards?ticket_id=${ticketId}`, { headers })
                            .then(r => r.json())
                            .then(d => {
                              const cards = Array.isArray(d) ? d : d.data || [];
                              if (cards.length > 0) {
                                setFailureCard(cards[0]);
                                setFailureCardForm({
                                  confirmed_root_cause: cards[0].confirmed_root_cause || cards[0].initial_diagnosis || "",
                                  efi_suggestion_correct: "",
                                  resolution_steps: cards[0].resolution_steps || "",
                                  technician_notes: cards[0].technician_notes || "",
                                });
                              }
                              setFailureCardModal(true);
                            });
                        } else {
                          setFailureCardModal(true);
                        }
                      }}
                      data-testid="failure-card-complete-btn"
                    >
                      <Brain className="w-3 h-3 mr-1" /> Complete Failure Card
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Quick Details */}
          <Card className="bg-zinc-900/60 border-zinc-800" data-testid="ticket-quick-details">
            <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-zinc-300">Quick Details</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {ticket.sla_deadline && (
                <div className="flex justify-between">
                  <span className="text-zinc-500">SLA Deadline</span>
                  <span className="text-zinc-200 font-mono text-xs">{new Date(ticket.sla_deadline).toLocaleString("en-IN")}</span>
                </div>
              )}
              {ticket.error_codes_reported?.length > 0 && (
                <div>
                  <span className="text-zinc-500">Error Codes</span>
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {ticket.error_codes_reported.map((c) => (
                      <Badge key={c} variant="outline" className="text-xs font-mono">{c}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Failure Card Completion Modal */}
      <Dialog open={failureCardModal} onOpenChange={(open) => !open && setFailureCardModal(false)}>
        <DialogContent className="bg-zinc-900 border-zinc-700 text-zinc-200 max-w-lg" data-testid="failure-card-modal">
          <DialogHeader>
            <DialogTitle className="text-bw-volt font-mono flex items-center gap-2">
              <Brain className="w-5 h-5" /> Complete Failure Card
            </DialogTitle>
            <p className="text-xs text-zinc-500 mt-1">This data improves the EFI diagnostic AI</p>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {failureCard?.initial_diagnosis && (
              <div className="bg-zinc-800/50 p-3 rounded border border-zinc-700">
                <Label className="text-xs text-zinc-500">EFI Initial Diagnosis</Label>
                <p className="text-sm text-zinc-300 mt-1">{failureCard.initial_diagnosis}</p>
              </div>
            )}

            <div>
              <Label className="text-xs text-zinc-400" htmlFor="fc-root-cause">Confirmed Root Cause *</Label>
              <Textarea
                id="fc-root-cause"
                className="bg-zinc-800 border-zinc-700 text-zinc-200 mt-1"
                placeholder="What was the actual root cause?"
                value={failureCardForm.confirmed_root_cause}
                onChange={(e) => setFailureCardForm(p => ({ ...p, confirmed_root_cause: e.target.value }))}
                data-testid="fc-root-cause-input"
              />
            </div>

            <div>
              <Label className="text-xs text-zinc-400">Was the EFI suggestion correct?</Label>
              <Select
                value={failureCardForm.efi_suggestion_correct}
                onValueChange={(v) => setFailureCardForm(p => ({ ...p, efi_suggestion_correct: v }))}
              >
                <SelectTrigger className="bg-zinc-800 border-zinc-700 text-zinc-200 mt-1" data-testid="fc-efi-correct-select">
                  <SelectValue placeholder="Select..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes">Yes — EFI was correct</SelectItem>
                  <SelectItem value="no">No — Different root cause</SelectItem>
                  <SelectItem value="partial">Partial — Partially correct</SelectItem>
                  <SelectItem value="na">N/A — No EFI suggestion</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-xs text-zinc-400" htmlFor="fc-resolution">Resolution Steps</Label>
              <Textarea
                id="fc-resolution"
                className="bg-zinc-800 border-zinc-700 text-zinc-200 mt-1"
                placeholder="What steps resolved the issue?"
                value={failureCardForm.resolution_steps}
                onChange={(e) => setFailureCardForm(p => ({ ...p, resolution_steps: e.target.value }))}
                data-testid="fc-resolution-input"
              />
            </div>

            <div>
              <Label className="text-xs text-zinc-400" htmlFor="fc-notes">Additional Notes</Label>
              <Textarea
                id="fc-notes"
                className="bg-zinc-800 border-zinc-700 text-zinc-200 mt-1"
                placeholder="Any additional observations..."
                value={failureCardForm.technician_notes}
                onChange={(e) => setFailureCardForm(p => ({ ...p, technician_notes: e.target.value }))}
                data-testid="fc-notes-input"
              />
            </div>
          </div>

          <DialogFooter className="flex gap-2">
            <Button
              variant="ghost"
              onClick={() => setFailureCardModal(false)}
              className="text-zinc-400 hover:text-zinc-200"
              data-testid="fc-dismiss-btn"
            >
              Save as Draft
            </Button>
            <Button
              onClick={handleFailureCardSubmit}
              disabled={failureCardSubmitting || !failureCardForm.confirmed_root_cause}
              className="bg-bw-volt text-black hover:bg-bw-volt/80 font-medium"
              data-testid="fc-submit-btn"
            >
              {failureCardSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Brain className="w-4 h-4 mr-1" />}
              Complete & Feed EFI
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
