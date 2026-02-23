/**
 * useEstimateCalculations
 *
 * Pure calculation hook for estimate totals.
 * Derives subtotal, tax, discount, and grand total from the
 * newEstimate form object — no API calls, no side effects.
 *
 * @param {Object} newEstimate  The in-progress estimate form state
 * @returns {{ subtotal: number, totalTax: number, discount: number, grandTotal: number }}
 */
export function useEstimateCalculations(newEstimate) {
  const lineItems = newEstimate?.line_items ?? [];

  const subtotal = lineItems.reduce((sum, item) => sum + (item.taxable_amount || 0), 0);
  const totalTax = lineItems.reduce((sum, item) => sum + (item.tax_amount || 0), 0);

  let discount = 0;
  if (newEstimate?.discount_type === "percent") {
    discount = subtotal * ((newEstimate.discount_value || 0) / 100);
  } else if (newEstimate?.discount_type === "amount") {
    discount = newEstimate.discount_value || 0;
  }

  const grandTotal =
    subtotal -
    discount +
    totalTax +
    (newEstimate?.shipping_charge || 0) +
    (newEstimate?.adjustment || 0);

  return { subtotal, totalTax, discount, grandTotal };
}

/**
 * calculateLineItemTotals
 *
 * Pure utility — computes derived fields for a single line item.
 * Call before pushing a new item into newEstimate.line_items.
 *
 * @param {{ quantity: number, rate: number, discount_type: string,
 *            discount_percent: number, discount_value: number, tax_percentage: number }} lineItem
 * @returns {{ grossAmount, discountAmount, taxableAmount, taxAmount, total }}
 */
export function calculateLineItemTotals(lineItem) {
  const qty = lineItem.quantity || 1;
  const rate = lineItem.rate || 0;
  const grossAmount = qty * rate;

  let discountAmount = 0;
  if (lineItem.discount_type === "amount") {
    discountAmount = lineItem.discount_value || 0;
  } else {
    discountAmount = (grossAmount * (lineItem.discount_percent || 0)) / 100;
  }

  const taxableAmount = grossAmount - discountAmount;
  const taxAmount = taxableAmount * ((lineItem.tax_percentage || 0) / 100);
  const total = taxableAmount + taxAmount;

  return { grossAmount, discountAmount, taxableAmount, taxAmount, total };
}
