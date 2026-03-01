/**
 * EstimateTotalsBlock - Pure UI component for totals summary display
 * Props: { subtotal, discount, taxAmount, total, shippingCharge, adjustment, currency }
 * No state, no calculations - receives pre-calculated values
 */

export function EstimateTotalsBlock({ 
  subtotal = 0, 
  discount = 0, 
  taxAmount = 0, 
  total = 0,
  shippingCharge = 0,
  adjustment = 0,
  currency = "₹",
  gstType = ""
}) {
  const formatAmount = (amount) => {
    return `${currency}${(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="w-64 space-y-2 text-sm" data-testid="estimate-totals-block">
      {/* Subtotal */}
      <div className="flex justify-between">
        <span className="text-bw-white/[0.45]">Subtotal:</span>
        <span className="text-bw-white">{formatAmount(subtotal)}</span>
      </div>
      
      {/* Discount - only show if > 0 */}
      {discount > 0 && (
        <div className="flex justify-between">
          <span className="text-bw-white/[0.45]">Discount:</span>
          <span className="text-bw-red">-{formatAmount(discount)}</span>
        </div>
      )}
      
      {/* Tax */}
      <div className="flex justify-between">
        <span className="text-bw-white/[0.45]">
          Tax{gstType ? ` (${gstType.toUpperCase()})` : ''}:
        </span>
        <span className="text-bw-white">{formatAmount(taxAmount)}</span>
      </div>
      
      {/* Shipping - only show if > 0 */}
      {shippingCharge > 0 && (
        <div className="flex justify-between">
          <span className="text-bw-white/[0.45]">Shipping:</span>
          <span className="text-bw-white">{formatAmount(shippingCharge)}</span>
        </div>
      )}
      
      {/* Adjustment - only show if != 0 */}
      {adjustment !== 0 && (
        <div className="flex justify-between">
          <span className="text-bw-white/[0.45]">Adjustment:</span>
          <span className="text-bw-white">{formatAmount(adjustment)}</span>
        </div>
      )}
      
      {/* Divider */}
      <div 
        className="border-t border-white/[0.07]" 
        style={{ margin: '8px 0' }}
      />
      
      {/* Grand Total */}
      <div 
        className="flex justify-between items-center py-2 px-3 -mx-3 rounded"
        style={{
          backgroundColor: 'rgba(200,255,0,0.06)',
          borderTop: '2px solid rgba(200,255,0,0.20)'
        }}
      >
        <span 
          className="uppercase"
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '11px',
            letterSpacing: '0.08em',
            color: 'rgb(var(--bw-volt))'
          }}
        >
          Grand Total:
        </span>
        <span 
          className="text-lg"
          style={{
            fontWeight: 700,
            color: 'rgb(var(--bw-volt))'
          }}
        >
          {formatAmount(total)}
        </span>
      </div>
    </div>
  );
}

export default EstimateTotalsBlock;
