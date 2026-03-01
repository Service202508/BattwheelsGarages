import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { FileText, AlertTriangle, Loader2, Download, ArrowLeft, Minus } from "lucide-react";
import { API } from "@/App";

const cnStatusColors = {
  issued: "bg-bw-blue/10 text-bw-blue border border-bw-blue/25",
  applied: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25",
  refunded: "bg-bw-green/10 text-bw-green border border-bw-green/25",
};

const cnStatusLabels = { issued: "Issued", applied: "Applied", refunded: "Refunded" };

function formatCurrency(val) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(val || 0);
}

export function CreditNoteCreateModal({ open, onOpenChange, invoice, headers, onCreated }) {
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [lineItems, setLineItems] = useState([]);
  const [loading, setLoading] = useState(false);

  // Pre-populate from invoice line items
  useEffect(() => {
    if (invoice?.line_items) {
      setLineItems(
        invoice.line_items.map((item) => ({
          name: item.name || item.item_name || "",
          description: item.description || "",
          hsn_sac: item.hsn_sac || item.hsn || "",
          quantity: item.quantity || 1,
          rate: item.rate || 0,
          tax_rate: item.tax_rate || item.gst_percent || 18,
          max_quantity: item.quantity || 1,
          max_rate: item.rate || 0,
        }))
      );
      setReason("");
      setNotes("");
    }
  }, [invoice]);

  const updateLine = (idx, field, value) => {
    setLineItems((prev) => {
      const updated = [...prev];
      const item = { ...updated[idx] };
      const numVal = parseFloat(value) || 0;

      if (field === "quantity") {
        item.quantity = Math.min(Math.max(0, numVal), item.max_quantity);
      } else if (field === "rate") {
        item.rate = Math.min(Math.max(0, numVal), item.max_rate);
      }
      updated[idx] = item;
      return updated;
    });
  };

  const computeTotals = () => {
    let subtotal = 0, tax = 0;
    lineItems.forEach((item) => {
      const amt = (item.quantity || 0) * (item.rate || 0);
      subtotal += amt;
      tax += amt * (item.tax_rate || 0) / 100;
    });
    return { subtotal: Math.round(subtotal * 100) / 100, tax: Math.round(tax * 100) / 100, total: Math.round((subtotal + tax) * 100) / 100 };
  };

  const { subtotal, tax, total } = computeTotals();
  const invoiceTotal = invoice?.grand_total || invoice?.total || 0;
  const alreadyCredited = invoice?.total_credits_applied || 0;
  const remaining = Math.round((invoiceTotal - alreadyCredited) * 100) / 100;

  const handleSubmit = async () => {
    if (!reason.trim()) { toast.error("Reason is required"); return; }
    if (total <= 0) { toast.error("Credit note total must be greater than zero"); return; }
    if (total > remaining) { toast.error(`Credit note total (${formatCurrency(total)}) exceeds remaining creditable amount (${formatCurrency(remaining)})`); return; }

    setLoading(true);
    try {
      const res = await fetch(`${API}/credit-notes/`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          original_invoice_id: invoice.invoice_id,
          reason,
          notes,
          line_items: lineItems.filter((i) => i.quantity > 0 && i.rate > 0).map(({ max_quantity, max_rate, ...rest }) => rest),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Credit Note ${data.credit_note?.credit_note_number} created`);
        onCreated?.(data.credit_note);
        onOpenChange(false);
      } else {
        toast.error(data.detail || "Failed to create credit note");
      }
    } catch {
      toast.error("Error creating credit note");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="credit-note-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2" data-testid="cn-modal-title">
            <FileText className="h-5 w-5 text-bw-orange" />
            Issue Credit Note
          </DialogTitle>
          <DialogDescription>
            Against Invoice {invoice?.invoice_number} — {invoice?.customer_name}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Invoice reference summary */}
          <div className="p-3 bg-bw-panel rounded-lg text-sm flex justify-between items-center" data-testid="cn-invoice-ref">
            <div>
              <span className="text-bw-white/[0.45]">Original Invoice:</span>{" "}
              <span className="font-medium">{invoice?.invoice_number}</span>
              <span className="mx-2 text-bw-white/15">|</span>
              <span className="text-bw-white/[0.45]">Total:</span>{" "}
              <span className="font-medium">{formatCurrency(invoiceTotal)}</span>
            </div>
            {alreadyCredited > 0 && (
              <div className="text-bw-orange text-xs">
                Already credited: {formatCurrency(alreadyCredited)} — Remaining: {formatCurrency(remaining)}
              </div>
            )}
          </div>

          {/* Reason */}
          <div>
            <Label htmlFor="cn-reason">Reason for Credit Note *</Label>
            <Textarea
              id="cn-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Defective goods returned, Pricing correction, Service not rendered"
              className="mt-1"
              data-testid="cn-reason-input"
            />
          </div>

          {/* Line items */}
          <div>
            <Label>Line Items (adjust quantities/rates downward only)</Label>
            <div className="border rounded-lg overflow-hidden mt-2">
              <table className="w-full text-sm">
                <thead className="bg-bw-panel">
                  <tr>
                    <th className="px-3 py-2 text-left">Item</th>
                    <th className="px-3 py-2 text-right w-24">Qty</th>
                    <th className="px-3 py-2 text-right w-28">Rate</th>
                    <th className="px-3 py-2 text-right w-20">Tax %</th>
                    <th className="px-3 py-2 text-right w-28">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {lineItems.map((item, idx) => {
                    const lineTotal = (item.quantity || 0) * (item.rate || 0) * (1 + (item.tax_rate || 0) / 100);
                    return (
                      <tr key={idx} className="border-t" data-testid={`cn-line-item-${idx}`}>
                        <td className="px-3 py-2">
                          <p className="font-medium">{item.name}</p>
                          {item.description && <p className="text-xs text-bw-white/[0.45]">{item.description}</p>}
                          <p className="text-xs text-bw-white/25">Max: {item.max_quantity} x {formatCurrency(item.max_rate)}</p>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Input
                            type="number"
                            min={0}
                            max={item.max_quantity}
                            step="any"
                            value={item.quantity}
                            onChange={(e) => updateLine(idx, "quantity", e.target.value)}
                            className="w-20 text-right ml-auto"
                            data-testid={`cn-qty-${idx}`}
                          />
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Input
                            type="number"
                            min={0}
                            max={item.max_rate}
                            step="any"
                            value={item.rate}
                            onChange={(e) => updateLine(idx, "rate", e.target.value)}
                            className="w-24 text-right ml-auto"
                            data-testid={`cn-rate-${idx}`}
                          />
                        </td>
                        <td className="px-3 py-2 text-right text-bw-white/[0.45]">{item.tax_rate}%</td>
                        <td className="px-3 py-2 text-right font-medium">{formatCurrency(lineTotal)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Totals */}
          <div className="bg-bw-panel p-4 rounded-lg w-64 ml-auto space-y-1 text-sm" data-testid="cn-totals">
            <div className="flex justify-between"><span>Sub Total:</span><span>{formatCurrency(subtotal)}</span></div>
            <div className="flex justify-between"><span>GST:</span><span>{formatCurrency(tax)}</span></div>
            <Separator />
            <div className="flex justify-between font-bold text-base">
              <span>Credit Note Total:</span>
              <span className={total > remaining ? "text-bw-red" : ""}>{formatCurrency(total)}</span>
            </div>
            {total > remaining && (
              <p className="text-xs text-bw-red flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Exceeds remaining creditable amount</p>
            )}
          </div>

          {/* Notes */}
          <div>
            <Label htmlFor="cn-notes">Additional Notes</Label>
            <Textarea id="cn-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional internal notes" className="mt-1" data-testid="cn-notes-input" />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="cn-cancel-btn">Cancel</Button>
          <Button
            onClick={handleSubmit}
            disabled={loading || total <= 0 || total > remaining || !reason.trim()}
            className="bg-bw-orange hover:bg-bw-orange text-bw-black"
            data-testid="cn-submit-btn"
          >
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Minus className="h-4 w-4 mr-2" />}
            Issue Credit Note — {formatCurrency(total)}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function CreditNoteViewModal({ open, onOpenChange, creditNote, headers }) {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadPDF = async () => {
    if (!creditNote) return;
    setDownloading(true);
    try {
      const res = await fetch(`${API}/credit-notes/${creditNote.credit_note_id}/pdf`, { headers });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${creditNote.credit_note_number}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        toast.error("Failed to download PDF");
      }
    } catch {
      toast.error("Error downloading PDF");
    } finally {
      setDownloading(false);
    }
  };

  if (!creditNote) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="credit-note-view-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2" data-testid="cn-view-title">
            {creditNote.credit_note_number}
            <Badge className={cnStatusColors[creditNote.status]}>{cnStatusLabels[creditNote.status] || creditNote.status}</Badge>
          </DialogTitle>
          <DialogDescription>
            Credit Note against {creditNote.original_invoice_number}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-sm">
          <div className="grid grid-cols-3 gap-4">
            <div><span className="text-bw-white/[0.45]">Date:</span><br />{creditNote.created_at?.slice(0, 10)}</div>
            <div><span className="text-bw-white/[0.45]">Customer:</span><br />{creditNote.customer_name}</div>
            <div>
              <span className="text-bw-white/[0.45]">Original Invoice:</span><br />
              <button className="text-bw-blue underline" data-testid="cn-invoice-link">{creditNote.original_invoice_number}</button>
            </div>
          </div>

          <div className="p-3 bg-bw-orange/[0.06] border border-bw-orange/20 rounded">
            <strong className="text-bw-orange">Reason:</strong> {creditNote.reason}
          </div>

          {/* Line items */}
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-bw-panel">
                <tr>
                  <th className="px-3 py-2 text-left">Item</th>
                  <th className="px-3 py-2 text-right">Qty</th>
                  <th className="px-3 py-2 text-right">Rate</th>
                  <th className="px-3 py-2 text-right">Tax</th>
                  <th className="px-3 py-2 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {creditNote.line_items?.map((item, idx) => (
                  <tr key={idx} className="border-t">
                    <td className="px-3 py-2">{item.name}</td>
                    <td className="px-3 py-2 text-right">{item.quantity}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(item.rate)}</td>
                    <td className="px-3 py-2 text-right">{item.tax_rate}%</td>
                    <td className="px-3 py-2 text-right font-medium">{formatCurrency(item.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-bw-panel p-4 rounded-lg w-64 ml-auto space-y-1">
            <div className="flex justify-between"><span>Sub Total:</span><span>{formatCurrency(creditNote.subtotal)}</span></div>
            {creditNote.gst_treatment === "igst" ? (
              <div className="flex justify-between"><span>IGST:</span><span>{formatCurrency(creditNote.igst_amount)}</span></div>
            ) : (
              <>
                <div className="flex justify-between"><span>CGST:</span><span>{formatCurrency(creditNote.cgst_amount)}</span></div>
                <div className="flex justify-between"><span>SGST:</span><span>{formatCurrency(creditNote.sgst_amount)}</span></div>
              </>
            )}
            <Separator />
            <div className="flex justify-between font-bold text-base"><span>Total:</span><span>{formatCurrency(creditNote.total)}</span></div>
          </div>

          {creditNote.notes && (
            <div className="text-xs text-bw-white/[0.45]"><strong>Notes:</strong> {creditNote.notes}</div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
          <Button onClick={handleDownloadPDF} disabled={downloading} data-testid="cn-download-pdf-btn">
            {downloading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Download className="h-4 w-4 mr-2" />}
            Download PDF
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
