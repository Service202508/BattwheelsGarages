/**
 * EstimateDetail — Detail dialog showing full estimate info.
 * Renders: header, price list badge, line items table, totals, EstimateActions, secondary info.
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { IndianRupee } from "lucide-react";
import { EstimateStatusBadge, EstimateLineItemsTable, EstimateTotalsBlock } from "@/components/estimates";
import { EstimateActions } from "./EstimateActions";

export function EstimateDetail({ open, onOpenChange, estimate, handlers }) {
  if (!estimate) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <>
          <DialogHeader className="flex-shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle className="flex items-center gap-2">
                  {estimate.estimate_number}
                  <EstimateStatusBadge status={estimate.status} />
                  {estimate.is_expired && <Badge variant="destructive">Expired</Badge>}
                </DialogTitle>
                <DialogDescription>{estimate.customer_name}</DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto space-y-4 py-4 min-h-0" data-testid="estimate-detail-content">
            {/* Price List Info */}
            {estimate.price_list_name && (
              <div className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.25)] rounded-lg px-3 py-2 text-sm flex items-center gap-2">
                <IndianRupee className="h-4 w-4 text-[#22C55E]" />
                <span className="text-[#22C55E]">
                  Price List Applied: <strong>{estimate.price_list_name}</strong>
                </span>
              </div>
            )}

            <Separator />

            {/* Line Items */}
            <div>
              <h4 className="font-medium mb-2">Line Items ({estimate.line_items?.length || 0})</h4>
              <EstimateLineItemsTable lineItems={estimate.line_items} estimate={estimate} readOnly={true} />
            </div>

            {/* Totals */}
            <div className="flex justify-end">
              <EstimateTotalsBlock
                subtotal={estimate.subtotal}
                discount={estimate.total_discount}
                taxAmount={estimate.total_tax}
                total={estimate.grand_total}
                shippingCharge={estimate.shipping_charge}
                adjustment={estimate.adjustment}
                gstType={estimate.gst_type}
              />
            </div>

            <Separator />

            {/* Actions — includes Convert to Invoice/SO, ticket links, history */}
            <EstimateActions estimate={estimate} handlers={handlers} />
          </div>
        </>
      </DialogContent>
    </Dialog>
  );
}
