# Finance Calculator Service
# Centralized calculation engine for Battwheels financial computations
# Ensures consistent rounding, tax calculation, and discount application

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# ========================= CONSTANTS =========================

# GST Rate Slabs (India)
GST_RATES = [0, 5, 12, 18, 28]

# Rounding precision (2 decimal places for INR)
CURRENCY_PRECISION = Decimal('0.01')

# ========================= DATA CLASSES =========================

@dataclass
class LineItemCalc:
    """Line item calculation result"""
    name: str
    quantity: Decimal
    rate: Decimal
    amount: Decimal  # quantity * rate
    discount_amount: Decimal
    taxable_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    item_total: Decimal
    hsn_sac: str = ""
    unit: str = ""

@dataclass
class InvoiceTotals:
    """Invoice-level totals"""
    sub_total: Decimal
    discount_total: Decimal
    taxable_total: Decimal
    tax_total: Decimal
    cgst_total: Decimal
    sgst_total: Decimal
    igst_total: Decimal
    shipping_charge: Decimal
    adjustment: Decimal
    grand_total: Decimal
    amount_paid: Decimal
    balance_due: Decimal

# ========================= ROUNDING FUNCTIONS =========================

def round_currency(amount: float | Decimal, precision: Decimal = CURRENCY_PRECISION) -> Decimal:
    """Round to currency precision using banker's rounding (ROUND_HALF_UP)"""
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    return amount.quantize(precision, rounding=ROUND_HALF_UP)

def round_to_nearest(amount: Decimal, nearest: int = 1) -> Decimal:
    """Round to nearest value (e.g., nearest 1, 5, 10)"""
    if nearest == 1:
        return round_currency(amount, Decimal('1'))
    factor = Decimal(str(nearest))
    return (amount / factor).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * factor

# ========================= LINE ITEM CALCULATIONS =========================

def calculate_line_item(
    name: str,
    quantity: float,
    rate: float,
    tax_rate: float = 18,
    discount_percent: float = 0,
    discount_amount: float = 0,
    is_igst: bool = False,
    is_inclusive_tax: bool = False,
    hsn_sac: str = "",
    unit: str = "pcs"
) -> LineItemCalc:
    """
    Calculate line item totals following Zoho Books logic.
    
    Rules:
    1. Base amount = quantity * rate
    2. Apply discount (either % or fixed amount)
    3. Calculate tax on discounted amount
    4. If inclusive tax, back-calculate base from total
    """
    qty = Decimal(str(quantity))
    unit_rate = Decimal(str(rate))
    tax_pct = Decimal(str(tax_rate))
    disc_pct = Decimal(str(discount_percent))
    disc_amt = Decimal(str(discount_amount))
    
    # Step 1: Calculate base amount
    base_amount = round_currency(qty * unit_rate)
    
    # Step 2: Calculate discount
    if disc_pct > 0:
        discount = round_currency(base_amount * disc_pct / Decimal('100'))
    elif disc_amt > 0:
        discount = round_currency(disc_amt)
    else:
        discount = Decimal('0')
    
    # Step 3: Calculate taxable amount
    if is_inclusive_tax:
        # Back-calculate: total includes tax
        # taxable = total / (1 + tax_rate/100)
        total_with_tax = base_amount - discount
        taxable = round_currency(total_with_tax / (1 + tax_pct / Decimal('100')))
        tax = round_currency(total_with_tax - taxable)
        item_total = total_with_tax
    else:
        taxable = base_amount - discount
        tax = round_currency(taxable * tax_pct / Decimal('100'))
        item_total = round_currency(taxable + tax)
    
    # Step 4: Split tax (CGST/SGST or IGST)
    if is_igst:
        cgst = Decimal('0')
        sgst = Decimal('0')
        igst = tax
    else:
        # Split equally between CGST and SGST
        half_tax = round_currency(tax / 2)
        cgst = half_tax
        sgst = tax - half_tax  # Handle rounding remainder
        igst = Decimal('0')
    
    return LineItemCalc(
        name=name,
        quantity=qty,
        rate=unit_rate,
        amount=base_amount,
        discount_amount=discount,
        taxable_amount=taxable,
        tax_rate=tax_pct,
        tax_amount=tax,
        cgst_amount=cgst,
        sgst_amount=sgst,
        igst_amount=igst,
        item_total=item_total,
        hsn_sac=hsn_sac,
        unit=unit
    )

def calculate_line_items(
    items: List[Dict],
    is_igst: bool = False,
    is_inclusive_tax: bool = False
) -> List[LineItemCalc]:
    """Calculate multiple line items"""
    results = []
    for item in items:
        calc = calculate_line_item(
            name=item.get("name", ""),
            quantity=item.get("quantity", 1),
            rate=item.get("rate", 0),
            tax_rate=item.get("tax_rate", item.get("tax_percentage", 18)),
            discount_percent=item.get("discount_percent", item.get("discount_percentage", 0)),
            discount_amount=item.get("discount_amount", 0),
            is_igst=is_igst,
            is_inclusive_tax=is_inclusive_tax,
            hsn_sac=item.get("hsn_sac", item.get("hsn_or_sac", "")),
            unit=item.get("unit", "pcs")
        )
        results.append(calc)
    return results

# ========================= INVOICE-LEVEL CALCULATIONS =========================

def calculate_invoice_totals(
    line_items: List[LineItemCalc],
    invoice_discount_type: str = "percentage",
    invoice_discount_value: float = 0,
    shipping_charge: float = 0,
    adjustment: float = 0,
    amount_paid: float = 0,
    round_off: bool = True,
    round_to: int = 1
) -> InvoiceTotals:
    """
    Calculate invoice-level totals following Zoho Books logic.
    
    Order of operations:
    1. Sum line item subtotals
    2. Apply invoice-level discount to subtotal
    3. Sum all taxes
    4. Add shipping charge
    5. Apply adjustment
    6. Round off (if enabled)
    7. Calculate balance
    """
    disc_type = invoice_discount_type
    disc_value = Decimal(str(invoice_discount_value))
    shipping = Decimal(str(shipping_charge))
    adj = Decimal(str(adjustment))
    paid = Decimal(str(amount_paid))
    
    # Step 1: Sum line items
    sub_total = sum(item.taxable_amount for item in line_items)
    line_discount_total = sum(item.discount_amount for item in line_items)
    tax_total = sum(item.tax_amount for item in line_items)
    cgst_total = sum(item.cgst_amount for item in line_items)
    sgst_total = sum(item.sgst_amount for item in line_items)
    igst_total = sum(item.igst_amount for item in line_items)
    
    # Step 2: Invoice-level discount
    if disc_type == "percentage" and disc_value > 0:
        invoice_discount = round_currency(sub_total * disc_value / Decimal('100'))
    elif disc_type == "amount" and disc_value > 0:
        invoice_discount = round_currency(disc_value)
    else:
        invoice_discount = Decimal('0')
    
    total_discount = line_discount_total + invoice_discount
    taxable_total = sub_total - invoice_discount
    
    # Step 3: Calculate grand total
    grand_total = taxable_total + tax_total + shipping + adj
    
    # Step 4: Round off
    if round_off:
        rounded_total = round_to_nearest(grand_total, round_to)
        adjustment_for_rounding = rounded_total - grand_total
        adj += adjustment_for_rounding
        grand_total = rounded_total
    
    # Step 5: Balance
    balance = round_currency(grand_total - paid)
    
    return InvoiceTotals(
        sub_total=round_currency(sub_total),
        discount_total=round_currency(total_discount),
        taxable_total=round_currency(taxable_total),
        tax_total=round_currency(tax_total),
        cgst_total=round_currency(cgst_total),
        sgst_total=round_currency(sgst_total),
        igst_total=round_currency(igst_total),
        shipping_charge=round_currency(shipping),
        adjustment=round_currency(adj),
        grand_total=round_currency(grand_total),
        amount_paid=round_currency(paid),
        balance_due=balance
    )

# ========================= PAYMENT ALLOCATION =========================

def allocate_payment(
    payment_amount: float,
    invoices: List[Dict],
    allocation_method: str = "oldest_first"
) -> List[Dict]:
    """
    Allocate payment across multiple invoices.
    
    Methods:
    - oldest_first: Apply to oldest invoice first (default)
    - proportional: Apply proportionally by balance
    - manual: Use provided allocations
    """
    amount = Decimal(str(payment_amount))
    allocations = []
    
    if allocation_method == "oldest_first":
        # Sort by date (oldest first)
        sorted_invoices = sorted(invoices, key=lambda x: x.get("invoice_date", ""))
        remaining = amount
        
        for inv in sorted_invoices:
            if remaining <= 0:
                break
            balance = Decimal(str(inv.get("balance_due", 0)))
            allocated = min(remaining, balance)
            if allocated > 0:
                allocations.append({
                    "invoice_id": inv.get("invoice_id"),
                    "invoice_number": inv.get("invoice_number"),
                    "allocated_amount": float(allocated),
                    "invoice_balance_before": float(balance),
                    "invoice_balance_after": float(balance - allocated)
                })
                remaining -= allocated
    
    elif allocation_method == "proportional":
        total_balance = sum(Decimal(str(inv.get("balance_due", 0))) for inv in invoices)
        if total_balance > 0:
            for inv in invoices:
                balance = Decimal(str(inv.get("balance_due", 0)))
                proportion = balance / total_balance
                allocated = round_currency(amount * proportion)
                if allocated > balance:
                    allocated = balance
                if allocated > 0:
                    allocations.append({
                        "invoice_id": inv.get("invoice_id"),
                        "invoice_number": inv.get("invoice_number"),
                        "allocated_amount": float(allocated),
                        "invoice_balance_before": float(balance),
                        "invoice_balance_after": float(balance - allocated)
                    })
    
    return allocations

def unapply_payment(
    payment_id: str,
    allocations: List[Dict]
) -> List[Dict]:
    """
    Reverse payment allocation - return amounts to add back to invoice balances.
    """
    reversals = []
    for alloc in allocations:
        reversals.append({
            "invoice_id": alloc.get("invoice_id"),
            "amount_to_restore": alloc.get("allocated_amount", 0),
            "payment_id": payment_id
        })
    return reversals

# ========================= TAX CALCULATIONS =========================

def calculate_tax_breakdown(
    taxable_amount: float,
    tax_rate: float,
    is_igst: bool = False
) -> Dict:
    """
    Calculate tax breakdown for a taxable amount.
    Returns CGST/SGST or IGST based on transaction type.
    """
    taxable = Decimal(str(taxable_amount))
    rate = Decimal(str(tax_rate))
    
    total_tax = round_currency(taxable * rate / Decimal('100'))
    
    if is_igst:
        return {
            "cgst_rate": 0,
            "cgst_amount": 0,
            "sgst_rate": 0,
            "sgst_amount": 0,
            "igst_rate": float(rate),
            "igst_amount": float(total_tax),
            "total_tax": float(total_tax)
        }
    else:
        half_rate = rate / 2
        half_tax = round_currency(total_tax / 2)
        return {
            "cgst_rate": float(half_rate),
            "cgst_amount": float(half_tax),
            "sgst_rate": float(half_rate),
            "sgst_amount": float(total_tax - half_tax),
            "igst_rate": 0,
            "igst_amount": 0,
            "total_tax": float(total_tax)
        }

def calculate_reverse_tax(
    total_with_tax: float,
    tax_rate: float
) -> Dict:
    """
    Back-calculate taxable amount from total (for inclusive tax).
    """
    total = Decimal(str(total_with_tax))
    rate = Decimal(str(tax_rate))
    
    taxable = round_currency(total / (1 + rate / Decimal('100')))
    tax = round_currency(total - taxable)
    
    return {
        "taxable_amount": float(taxable),
        "tax_amount": float(tax),
        "total": float(total)
    }

# ========================= AGING CALCULATIONS =========================

def calculate_aging_bucket(
    due_date: str,
    current_date: str
) -> str:
    """
    Determine aging bucket for an invoice.
    Returns: current, 1-30, 31-60, 61-90, 90+
    """
    from datetime import datetime
    
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d")
        current = datetime.strptime(current_date, "%Y-%m-%d")
        days_overdue = (current - due).days
        
        if days_overdue <= 0:
            return "current"
        elif days_overdue <= 30:
            return "1-30"
        elif days_overdue <= 60:
            return "31-60"
        elif days_overdue <= 90:
            return "61-90"
        else:
            return "90+"
    except:
        return "unknown"

def calculate_aging_summary(invoices: List[Dict], current_date: str) -> Dict:
    """
    Calculate aging summary for a list of invoices.
    """
    buckets = {
        "current": {"count": 0, "amount": Decimal('0')},
        "1-30": {"count": 0, "amount": Decimal('0')},
        "31-60": {"count": 0, "amount": Decimal('0')},
        "61-90": {"count": 0, "amount": Decimal('0')},
        "90+": {"count": 0, "amount": Decimal('0')}
    }
    
    for inv in invoices:
        balance = Decimal(str(inv.get("balance_due", 0)))
        if balance > 0:
            bucket = calculate_aging_bucket(inv.get("due_date", ""), current_date)
            if bucket in buckets:
                buckets[bucket]["count"] += 1
                buckets[bucket]["amount"] += balance
    
    # Convert to float for JSON serialization
    return {
        bucket: {
            "count": data["count"],
            "amount": float(data["amount"])
        }
        for bucket, data in buckets.items()
    }

# ========================= UTILITY FUNCTIONS =========================

def format_currency(amount: float | Decimal, currency: str = "INR") -> str:
    """Format amount as currency string"""
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    amount = round_currency(amount)
    
    if currency == "INR":
        return f"₹{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def parse_currency(amount_str: str) -> float:
    """Parse currency string to float"""
    import re
    # Remove currency symbols and commas
    cleaned = re.sub(r'[₹$,\s]', '', amount_str)
    try:
        return float(cleaned)
    except:
        return 0.0

def validate_gst_number(gstin: str) -> Dict:
    """Validate Indian GST number format"""
    import re
    
    # GST format: 22AAAAA0000A1Z5
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    is_valid = bool(re.match(pattern, gstin.upper()))
    
    state_code = gstin[:2] if len(gstin) >= 2 else ""
    pan = gstin[2:12] if len(gstin) >= 12 else ""
    
    return {
        "is_valid": is_valid,
        "state_code": state_code,
        "pan": pan,
        "gstin": gstin.upper()
    }
