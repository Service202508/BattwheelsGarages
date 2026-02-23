/**
 * EstimateLineItemRow - Pure UI component for single line item display
 * Props: { item, index, onRemove, readOnly }
 * No state, no API calls
 */
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";

export function EstimateLineItemRow({ item, index, onRemove, readOnly = false }) {
  return (
    <tr 
      className="border-b border-[rgba(255,255,255,0.04)] hover:bg-[#111820]"
      data-testid={`line-item-row-${index}`}
    >
      <td className="px-3 py-2">
        <div className="font-medium text-[#F4F6F0]">{item.name}</div>
        {item.description && (
          <div className="text-xs text-[rgba(244,246,240,0.45)]">{item.description}</div>
        )}
        {item.hsn_code && (
          <div className="text-xs text-[rgba(244,246,240,0.25)]">HSN: {item.hsn_code}</div>
        )}
        {item.price_list_applied && (
          <span className="text-[10px] text-[#22C55E] bg-[rgba(34,197,94,0.08)] px-1 rounded">
            {item.price_list_applied}
          </span>
        )}
      </td>
      <td className="px-3 py-2 text-center text-[rgba(244,246,240,0.70)]">
        {item.quantity} {item.unit}
      </td>
      <td className="px-3 py-2 text-center">
        <span className="text-[#F4F6F0]">₹{item.rate?.toLocaleString('en-IN')}</span>
        {item.base_rate && item.base_rate !== item.rate && (
          <div className="text-[10px] text-[rgba(244,246,240,0.25)] line-through">
            ₹{item.base_rate}
          </div>
        )}
      </td>
      <td className="px-3 py-2 text-center text-[rgba(244,246,240,0.70)]">
        {item.discount_type === 'amount' ? (
          <span>₹{item.discount_value || 0}</span>
        ) : (
          <span>{item.discount_percent || 0}%</span>
        )}
      </td>
      <td className="px-3 py-2 text-center">
        <Badge 
          variant="outline" 
          className="text-xs bg-transparent border-[rgba(255,255,255,0.15)] text-[rgba(244,246,240,0.70)]"
        >
          {item.tax_percentage}% GST
        </Badge>
      </td>
      <td className="px-3 py-2 text-right font-medium text-[#C8FF00]">
        ₹{(item.total || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
      </td>
      {!readOnly && (
        <td className="px-3 py-2">
          <Button 
            size="icon" 
            variant="ghost" 
            onClick={() => onRemove(index)} 
            className="h-7 w-7 hover:bg-[rgba(255,59,47,0.1)]"
            data-testid={`remove-item-${index}`}
          >
            <X className="h-4 w-4 text-[#FF3B2F]" />
          </Button>
        </td>
      )}
    </tr>
  );
}

export default EstimateLineItemRow;
