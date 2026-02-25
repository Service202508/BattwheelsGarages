/**
 * EstimateActions — Action buttons shown in the Detail dialog.
 * Contains: Edit, Send, Accept/Decline, Convert to Invoice/SO, Share, Attachments, PDF, Clone
 * Also shows: Linked Ticket banner, Converted To display, Customer Viewed info, History
 */
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Edit, Send, Trash2, CheckCircle, XCircle, ArrowRightLeft, Share2, Paperclip, Download, Copy, Eye, ExternalLink, Wrench } from "lucide-react";

export function EstimateActions({ estimate, handlers }) {
  const {
    handleOpenEdit, handleDeleteEstimate, handleConvertToInvoice, handleConvertToSO,
    handleMarkAccepted, handleMarkDeclined, handleClone, handleDownloadPDF,
    setSendEmail, setShowSendDialog, setShareLink, setShowShareDialog,
    fetchAttachments, setShowAttachmentDialog,
  } = handlers;

  return (
    <>
      {/* Linked Ticket Banner — For ticket estimates */}
      {estimate.is_ticket_estimate && estimate.ticket_id && (
        <div className="bg-[rgba(59,158,255,0.08)] border border-[rgba(59,158,255,0.25)] rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Wrench className="h-5 w-5 text-[#3B9EFF]" />
            <div>
              <p className="text-sm font-medium text-[#3B9EFF]">Linked Service Ticket</p>
              <p className="text-xs text-[#3B9EFF]">{estimate.ticket_id}</p>
            </div>
          </div>
          <Button
            size="sm" variant="outline"
            className="text-[#3B9EFF] border-[rgba(59,158,255,0.25)]"
            onClick={() => window.open(`/tickets?id=${estimate.ticket_id}`, '_blank')}
            data-testid="open-job-card-btn"
          >
            <ExternalLink className="h-4 w-4 mr-1" />
            Open Job Card
          </Button>
        </div>
      )}

      {/* Vehicle Info for Ticket Estimates */}
      {estimate.is_ticket_estimate && estimate.vehicle_number && (
        <div className="bg-[rgba(200,255,0,0.06)] border border-[rgba(200,255,0,0.15)] rounded-lg p-3 text-sm">
          <span className="text-[rgba(244,246,240,0.45)]">Vehicle: </span>
          <span className="font-medium text-[#F4F6F0]">{estimate.vehicle_number}</span>
          {estimate.vehicle_make && <span className="text-[rgba(244,246,240,0.45)]"> ({estimate.vehicle_make} {estimate.vehicle_model})</span>}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2" data-testid="estimate-actions">
        {/* Edit — Available for all statuses except converted and void */}
        {estimate.status !== "converted" && estimate.status !== "void" && (
          <Button variant="outline" onClick={() => handleOpenEdit(estimate)} data-testid="edit-estimate-btn">
            <Edit className="h-4 w-4 mr-1" /> Edit
          </Button>
        )}

        {/* Draft actions */}
        {estimate.status === "draft" && (
          <>
            <Button variant="outline" onClick={() => { setSendEmail(estimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Send</Button>
            <Button variant="destructive" size="sm" onClick={() => handleDeleteEstimate(estimate.estimate_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
          </>
        )}

        {/* Sent / Customer Viewed actions */}
        {(estimate.status === "sent" || estimate.status === "customer_viewed") && (
          <>
            <Button variant="outline" onClick={() => { setSendEmail(estimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Resend</Button>
            <Button onClick={() => handleMarkAccepted(estimate.estimate_id)} className="bg-[#22C55E] hover:bg-[rgba(34,197,94,0.85)] text-[#080C0F]"><CheckCircle className="h-4 w-4 mr-1" /> Mark Accepted</Button>
            <Button variant="outline" onClick={() => handleMarkDeclined(estimate.estimate_id)}><XCircle className="h-4 w-4 mr-1" /> Mark Declined</Button>
          </>
        )}

        {/* Accepted — Convert to Invoice / Sales Order */}
        {estimate.status === "accepted" && (
          <>
            <Button onClick={() => handleConvertToInvoice(estimate.estimate_id)} className="bg-[#8B5CF6] hover:bg-purple-600 text-white" data-testid="convert-to-invoice-btn">
              <ArrowRightLeft className="h-4 w-4 mr-1" /> Convert to Invoice
            </Button>
            <Button variant="outline" onClick={() => handleConvertToSO(estimate.estimate_id)} data-testid="convert-to-so-btn">
              <ArrowRightLeft className="h-4 w-4 mr-1" /> Convert to Sales Order
            </Button>
          </>
        )}

        {/* Declined / Expired */}
        {(estimate.status === "declined" || estimate.status === "expired") && (
          <Button variant="outline" onClick={() => { setSendEmail(estimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Resend</Button>
        )}

        {/* Common Actions */}
        <Separator orientation="vertical" className="h-8" />
        <Button variant="outline" onClick={() => { setShareLink(null); setShowShareDialog(true); }} data-testid="share-btn"><Share2 className="h-4 w-4 mr-1" /> Share</Button>
        <Button variant="outline" onClick={() => { fetchAttachments(estimate.estimate_id); setShowAttachmentDialog(true); }} data-testid="attachments-btn"><Paperclip className="h-4 w-4 mr-1" /> Attachments</Button>
        <Button variant="outline" onClick={() => handleDownloadPDF(estimate.estimate_id)} data-testid="download-pdf-btn"><Download className="h-4 w-4 mr-1" /> PDF</Button>
        <Button variant="outline" onClick={() => handleClone(estimate.estimate_id)}><Copy className="h-4 w-4 mr-1" /> Clone</Button>
      </div>

      {/* Customer Viewed Info */}
      {estimate.status === "customer_viewed" && estimate.first_viewed_at && (
        <div className="bg-[rgba(26,255,228,0.08)] border border-[rgba(26,255,228,0.20)] rounded-lg p-3">
          <p className="text-sm text-[#1AFFE4] flex items-center gap-2">
            <Eye className="h-4 w-4" />
            <strong>Customer viewed on:</strong> {new Date(estimate.first_viewed_at).toLocaleString('en-IN')}
          </p>
        </div>
      )}

      {/* Converted To */}
      {estimate.converted_to && (
        <div className="bg-[rgba(139,92,246,0.08)] rounded-lg p-3" data-testid="converted-to-display">
          <p className="text-sm text-[#8B5CF6]">
            <strong>Converted to:</strong> {estimate.converted_to}
          </p>
        </div>
      )}

      {/* History */}
      {estimate.history?.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">History</h4>
          <div className="space-y-2 text-sm">
            {estimate.history.slice(0, 5).map((h, idx) => (
              <div key={idx} className="flex justify-between text-[rgba(244,246,240,0.45)]">
                <span>{h.action}: {h.details}</span>
                <span className="text-xs">{new Date(h.timestamp).toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
