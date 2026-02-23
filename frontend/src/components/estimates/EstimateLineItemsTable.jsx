/**
 * EstimateLineItemsTable - Pure UI component for line items table in detail dialog
 * Props: { lineItems, estimate, readOnly }
 * No state, no API calls - uses EstimateLineItemRow internally
 */

export function EstimateLineItemsTable({ lineItems = [], estimate = {}, readOnly = true }) {
  if (!lineItems || lineItems.length === 0) {
    return (
      <div className="text-center py-8 text-[rgba(244,246,240,0.35)]">
        No line items
      </div>
    );
  }

  return (
    <div className="border border-[rgba(255,255,255,0.07)] rounded-lg overflow-hidden" data-testid="estimate-line-items-table">
      <table className="w-full text-sm">
        <thead className="bg-[#111820]">
          <tr>
            <th className="px-3 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">
              Item
            </th>
            <th className="px-3 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">
              HSN
            </th>
            <th className="px-3 py-2 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">
              Qty
            </th>
            <th className="px-3 py-2 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">
              Rate
            </th>
            <th className="px-3 py-2 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">
              Tax
            </th>
            <th className="px-3 py-2 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          {lineItems.map((item, idx) => (
            <tr key={idx} className="border-t border-[rgba(255,255,255,0.04)]">
              <td className="px-3 py-2">
                <p className="font-medium text-[#F4F6F0]">{item.name}</p>
                {item.description && (
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">{item.description}</p>
                )}
                {item.price_list_applied && (
                  <span className="text-[10px] text-[#22C55E] bg-[rgba(34,197,94,0.08)] px-1 rounded">
                    {item.price_list_applied}
                  </span>
                )}
              </td>
              <td className="px-3 py-2 font-mono text-xs text-[rgba(244,246,240,0.45)]">
                {item.hsn_code || '-'}
              </td>
              <td className="px-3 py-2 text-right text-[rgba(244,246,240,0.70)]">
                {item.quantity} {item.unit}
              </td>
              <td className="px-3 py-2 text-right">
                <span className="text-[#F4F6F0]">₹{item.rate?.toLocaleString('en-IN')}</span>
                {item.base_rate && item.base_rate !== item.rate && (
                  <span className="text-[10px] text-[rgba(244,246,240,0.25)] line-through ml-1">
                    ₹{item.base_rate}
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-right text-[rgba(244,246,240,0.70)]">
                {item.tax_percentage}%
              </td>
              <td className="px-3 py-2 text-right font-medium text-[#C8FF00]">
                ₹{item.total?.toLocaleString('en-IN')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default EstimateLineItemsTable;
