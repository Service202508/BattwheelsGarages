import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import { 
  FileText, CheckCircle, XCircle, Download, Paperclip, 
  Lock, Calendar, Building2, AlertTriangle, Eye, Loader2
} from "lucide-react";
import { API } from "@/App";

const statusColors = {
  draft: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  sent: "bg-blue-100 text-[#3B9EFF]",
  customer_viewed: "bg-[rgba(26,255,228,0.10)] text-[#1AFFE4] border border-[rgba(26,255,228,0.25)]",
  accepted: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  declined: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
  expired: "bg-orange-100 text-[#FF8C00]",
  converted: "bg-purple-100 text-[#8B5CF6]"
};

const statusLabels = {
  draft: "Draft",
  sent: "Sent",
  customer_viewed: "Viewed",
  accepted: "Accepted",
  declined: "Declined",
  expired: "Expired",
  converted: "Invoiced"
};

export default function PublicQuoteView() {
  const { shareToken } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [password, setPassword] = useState("");
  const [estimate, setEstimate] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [canAccept, setCanAccept] = useState(false);
  const [canDecline, setCanDecline] = useState(false);
  
  // Action dialogs
  const [showAcceptDialog, setShowAcceptDialog] = useState(false);
  const [showDeclineDialog, setShowDeclineDialog] = useState(false);
  const [actionComments, setActionComments] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchEstimate = async (pwd = null) => {
    setLoading(true);
    setError(null);
    try {
      let url = `${API}/estimates-enhanced/public/${shareToken}`;
      if (pwd) {
        url += `?password=${encodeURIComponent(pwd)}`;
      }
      
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.code === 2 && data.password_protected) {
        setPasswordRequired(true);
        setLoading(false);
        return;
      }
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to load estimate");
      }
      
      setEstimate(data.estimate);
      setAttachments(data.attachments || []);
      setCanAccept(data.can_accept);
      setCanDecline(data.can_decline);
      setPasswordRequired(false);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (shareToken) {
      fetchEstimate();
    }
  }, [shareToken]);

  const handlePasswordSubmit = () => {
    if (!password.trim()) {
      toast.error("Please enter the password");
      return;
    }
    fetchEstimate(password);
  };

  const handleAccept = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/estimates-enhanced/public/${shareToken}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "accept", comments: actionComments })
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to accept estimate");
      }
      
      toast.success("Estimate accepted successfully!");
      setShowAcceptDialog(false);
      // Refresh to show updated status
      fetchEstimate(password || null);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDecline = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/estimates-enhanced/public/${shareToken}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "decline", comments: actionComments })
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to decline estimate");
      }
      
      toast.success("Estimate declined");
      setShowDeclineDialog(false);
      fetchEstimate(password || null);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadPDF = () => {
    window.open(`${API}/estimates-enhanced/public/${shareToken}/pdf`, '_blank');
  };

  const handleDownloadAttachment = (attachmentId, filename) => {
    const url = `${API}/estimates-enhanced/public/${shareToken}/attachment/${attachmentId}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0B0F] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-[#0B462F] mx-auto mb-4" />
          <p className="text-gray-600">Loading estimate...</p>
        </div>
      </div>
    );
  }

  // Password required
  if (passwordRequired) {
    return (
      <div className="min-h-screen bg-[#0B0B0F] flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <Lock className="h-12 w-12 text-[#0B462F] mx-auto mb-4" />
            <CardTitle>Password Protected</CardTitle>
            <p className="text-sm text-gray-500 mt-2">This estimate is password protected. Please enter the password to view.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Password</Label>
              <Input 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                onKeyUp={(e) => e.key === 'Enter' && handlePasswordSubmit()}
              />
            </div>
            <Button onClick={handlePasswordSubmit} className="w-full bg-[#0B462F] hover:bg-[#0d5739]">
              View Estimate
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#0B0B0F] flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-[#F4F6F0] mb-2">Unable to Load Estimate</h2>
            <p className="text-gray-600">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main estimate view
  return (
    <div className="min-h-screen bg-[#0B0B0F] py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-[#0B462F] text-white rounded-t-xl p-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl font-bold">Battwheels OS</h1>
              <p className="text-green-200 text-sm">Your Onsite EV Resolution Partner</p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold">ESTIMATE</p>
              <p className="text-green-200">{estimate?.estimate_number}</p>
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div className="bg-[#111820] border-x border-b p-4 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <Badge className={`${statusColors[estimate?.status]} px-3 py-1 text-sm`}>
              {statusLabels[estimate?.status]}
            </Badge>
            {estimate?.status === "customer_viewed" && (
              <span className="text-sm text-[#1AFFE4] flex items-center gap-1">
                <Eye className="h-4 w-4" /> You are viewing this estimate
              </span>
            )}
          </div>
          <Button variant="outline" onClick={handleDownloadPDF} className="gap-2">
            <Download className="h-4 w-4" /> Download PDF
          </Button>
        </div>

        {/* Main Content */}
        <Card className="rounded-t-none">
          <CardContent className="p-6 space-y-6">
            {/* Customer & Date Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs text-gray-500 uppercase mb-1">Bill To</p>
                <p className="font-semibold text-lg">{estimate?.customer_name}</p>
                {estimate?.customer_email && (
                  <p className="text-gray-600 text-sm">{estimate?.customer_email}</p>
                )}
                {estimate?.customer_gstin && (
                  <p className="text-gray-600 text-sm font-mono">GSTIN: {estimate?.customer_gstin}</p>
                )}
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-gray-500 uppercase">Date</p>
                    <p className="font-medium">{estimate?.date}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase">Valid Until</p>
                    <p className="font-medium">{estimate?.expiry_date}</p>
                  </div>
                  {estimate?.reference_number && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase">Reference</p>
                      <p className="font-medium">{estimate?.reference_number}</p>
                    </div>
                  )}
                  {estimate?.subject && (
                    <div className="col-span-2">
                      <p className="text-xs text-gray-500 uppercase">Subject</p>
                      <p className="font-medium">{estimate?.subject}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <Separator />

            {/* Line Items */}
            <div>
              <h3 className="font-semibold mb-3">Items</h3>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[#0B462F] text-white">
                    <tr>
                      <th className="px-4 py-3 text-left">#</th>
                      <th className="px-4 py-3 text-left">Item & Description</th>
                      <th className="px-4 py-3 text-center">HSN/SAC</th>
                      <th className="px-4 py-3 text-right">Qty</th>
                      <th className="px-4 py-3 text-right">Rate</th>
                      <th className="px-4 py-3 text-right">Tax</th>
                      <th className="px-4 py-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {estimate?.line_items?.map((item, idx) => (
                      <tr key={idx} className="border-t">
                        <td className="px-4 py-3">{idx + 1}</td>
                        <td className="px-4 py-3">
                          <p className="font-medium">{item.name}</p>
                          {item.description && (
                            <p className="text-xs text-gray-500">{item.description}</p>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center font-mono text-xs">{item.hsn_code || '-'}</td>
                        <td className="px-4 py-3 text-right">{item.quantity} {item.unit}</td>
                        <td className="px-4 py-3 text-right">₹{item.rate?.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 text-right">{item.tax_percentage}%</td>
                        <td className="px-4 py-3 text-right font-semibold">₹{item.total?.toLocaleString('en-IN')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Totals */}
            <div className="flex justify-end">
              <div className="w-80 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal:</span>
                  <span>₹{estimate?.subtotal?.toLocaleString('en-IN')}</span>
                </div>
                {estimate?.total_discount > 0 && (
                  <div className="flex justify-between text-red-600">
                    <span>Discount:</span>
                    <span>-₹{estimate?.total_discount?.toLocaleString('en-IN')}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax ({estimate?.gst_type?.toUpperCase()}):</span>
                  <span>₹{estimate?.total_tax?.toLocaleString('en-IN')}</span>
                </div>
                {estimate?.shipping_charge > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Shipping:</span>
                    <span>₹{estimate?.shipping_charge?.toLocaleString('en-IN')}</span>
                  </div>
                )}
                {estimate?.adjustment !== 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Adjustment:</span>
                    <span>₹{estimate?.adjustment?.toLocaleString('en-IN')}</span>
                  </div>
                )}
                <Separator />
                <div className="flex justify-between text-lg font-bold text-[#0B462F]">
                  <span>Grand Total:</span>
                  <span>₹{estimate?.grand_total?.toLocaleString('en-IN')}</span>
                </div>
              </div>
            </div>

            {/* Terms & Notes */}
            {(estimate?.terms_and_conditions || estimate?.notes) && (
              <>
                <Separator />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {estimate?.terms_and_conditions && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 uppercase mb-2">Terms & Conditions</p>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{estimate?.terms_and_conditions}</p>
                    </div>
                  )}
                  {estimate?.notes && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 uppercase mb-2">Notes</p>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{estimate?.notes}</p>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Attachments */}
            {attachments.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Paperclip className="h-4 w-4" /> Attachments
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {attachments.map((att) => (
                      <div 
                        key={att.attachment_id} 
                        className="flex items-center justify-between bg-gray-50 rounded-lg p-3 cursor-pointer hover:bg-[rgba(255,255,255,0.05)]"
                        onClick={() => handleDownloadAttachment(att.attachment_id, att.filename)}
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium truncate">{att.filename}</p>
                            <p className="text-xs text-gray-400">{(att.file_size / 1024).toFixed(1)} KB</p>
                          </div>
                        </div>
                        <Download className="h-4 w-4 text-gray-400" />
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Action Buttons */}
            {(canAccept || canDecline) && (
              <>
                <Separator />
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm text-blue-800 mb-4">
                    Please review the estimate above. You can accept to proceed or decline if you have concerns.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    {canAccept && (
                      <Button 
                        onClick={() => setShowAcceptDialog(true)}
                        className="bg-green-600 hover:bg-green-700 gap-2"
                        data-testid="public-accept-btn"
                      >
                        <CheckCircle className="h-4 w-4" /> Accept Estimate
                      </Button>
                    )}
                    {canDecline && (
                      <Button 
                        variant="outline"
                        onClick={() => setShowDeclineDialog(true)}
                        className="text-red-600 border-red-300 hover:bg-[rgba(255,59,47,0.08)] gap-2"
                        data-testid="public-decline-btn"
                      >
                        <XCircle className="h-4 w-4" /> Decline
                      </Button>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* Already Accepted/Declined Message */}
            {estimate?.status === "accepted" && (
              <div className="bg-[rgba(34,197,94,0.08)] rounded-lg p-4 text-center">
                <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <p className="text-green-800 font-medium">This estimate has been accepted</p>
                {estimate?.accepted_date && (
                  <p className="text-green-600 text-sm">Accepted on {estimate.accepted_date}</p>
                )}
              </div>
            )}
            {estimate?.status === "declined" && (
              <div className="bg-[rgba(255,59,47,0.08)] rounded-lg p-4 text-center">
                <XCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
                <p className="text-red-800 font-medium">This estimate has been declined</p>
                {estimate?.decline_reason && (
                  <p className="text-red-600 text-sm">Reason: {estimate.decline_reason}</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center py-4 text-xs text-gray-400">
          <p>Powered by Battwheels OS</p>
        </div>
      </div>

      {/* Accept Dialog */}
      <Dialog open={showAcceptDialog} onOpenChange={setShowAcceptDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-700">
              <CheckCircle className="h-5 w-5" /> Accept Estimate
            </DialogTitle>
            <DialogDescription>
              By accepting this estimate, you agree to the terms and pricing outlined above.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Comments (optional)</Label>
            <Textarea 
              value={actionComments}
              onChange={(e) => setActionComments(e.target.value)}
              placeholder="Add any comments or special requests..."
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAcceptDialog(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button 
              onClick={handleAccept} 
              className="bg-green-600 hover:bg-green-700"
              disabled={submitting}
            >
              {submitting ? "Processing..." : "Confirm Acceptance"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Decline Dialog */}
      <Dialog open={showDeclineDialog} onOpenChange={setShowDeclineDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-700">
              <XCircle className="h-5 w-5" /> Decline Estimate
            </DialogTitle>
            <DialogDescription>
              Please let us know why you're declining this estimate.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Reason for declining</Label>
            <Textarea 
              value={actionComments}
              onChange={(e) => setActionComments(e.target.value)}
              placeholder="Please provide a reason for declining..."
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeclineDialog(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button 
              onClick={handleDecline} 
              variant="destructive"
              disabled={submitting}
            >
              {submitting ? "Processing..." : "Confirm Decline"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
