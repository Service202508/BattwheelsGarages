"""
Battwheels OS - Invoice Validation Service
Server-side validation for invoice calculations to prevent data inconsistencies.
"""

from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, validator, root_validator
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)


class LineItemValidation(BaseModel):
    """Validates a single line item"""
    name: str
    quantity: float
    rate: float
    discount: float = 0
    tax_rate: float = 0
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    line_total: Optional[float] = None
    
    @validator('quantity')
    def quantity_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v
    
    @validator('rate')
    def rate_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Rate cannot be negative')
        return v
    
    @validator('discount')
    def discount_must_be_reasonable(cls, v, values):
        if v < 0:
            raise ValueError('Discount cannot be negative')
        rate = values.get('rate', 0)
        quantity = values.get('quantity', 0)
        max_discount = rate * quantity
        if v > max_discount:
            raise ValueError(f'Discount {v} exceeds line amount {max_discount}')
        return v


class InvoiceValidation(BaseModel):
    """Validates complete invoice data"""
    invoice_number: str
    organization_id: str
    customer_id: Optional[str] = None
    line_items: List[Dict] = []
    subtotal: float = 0
    total_tax: float = 0
    total_discount: float = 0
    shipping_charge: float = 0
    adjustment: float = 0
    grand_total: float = 0
    amount_paid: float = 0
    balance_due: Optional[float] = None
    
    @validator('subtotal', 'total_tax', 'shipping_charge', 'amount_paid')
    def must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Value cannot be negative')
        return v


def validate_line_item_calculation(item: Dict) -> Tuple[bool, str, Dict]:
    """
    Validate and recalculate a line item.
    
    Returns:
        (is_valid, error_message, corrected_values)
    """
    qty = item.get('quantity', 1) or 1
    rate = item.get('rate', 0) or 0
    discount = item.get('discount', 0) or 0
    tax_rate = item.get('tax_rate', item.get('tax_percentage', 0)) or 0
    
    # Calculate expected values
    amount = Decimal(str(qty)) * Decimal(str(rate))
    taxable = amount - Decimal(str(discount))
    tax = (taxable * Decimal(str(tax_rate)) / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    line_total = (taxable + tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Get stored values
    stored_amount = item.get('amount', item.get('item_amount'))
    stored_tax = item.get('tax_amount')
    stored_total = item.get('line_total', item.get('total'))
    
    errors = []
    
    if stored_amount is not None and abs(float(amount) - float(stored_amount)) > 0.01:
        errors.append(f"Amount mismatch: expected {amount}, got {stored_amount}")
    
    if stored_tax is not None and abs(float(tax) - float(stored_tax)) > 0.01:
        errors.append(f"Tax mismatch: expected {tax}, got {stored_tax}")
    
    if stored_total is not None and abs(float(line_total) - float(stored_total)) > 0.01:
        errors.append(f"Line total mismatch: expected {line_total}, got {stored_total}")
    
    corrected = {
        'amount': float(amount),
        'tax_amount': float(tax),
        'line_total': float(line_total),
        'taxable_amount': float(taxable)
    }
    
    if errors:
        return False, "; ".join(errors), corrected
    
    return True, "", corrected


def validate_invoice_totals(invoice: Dict) -> Tuple[bool, List[str], Dict]:
    """
    Validate invoice total calculations.
    
    Returns:
        (is_valid, error_messages, corrected_values)
    """
    line_items = invoice.get('line_items', [])
    errors = []
    corrected = {}
    
    # Calculate subtotal from line items
    calc_subtotal = Decimal('0')
    calc_tax = Decimal('0')
    
    for item in line_items:
        qty = Decimal(str(item.get('quantity', 1) or 1))
        rate = Decimal(str(item.get('rate', 0) or 0))
        discount = Decimal(str(item.get('discount', 0) or 0))
        tax_rate = Decimal(str(item.get('tax_rate', item.get('tax_percentage', 0)) or 0))
        
        amount = qty * rate
        taxable = amount - discount
        tax = (taxable * tax_rate / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        calc_subtotal += taxable
        calc_tax += tax
    
    # Get stored values
    stored_subtotal = Decimal(str(invoice.get('subtotal', invoice.get('sub_total', 0)) or 0))
    stored_tax = Decimal(str(invoice.get('total_tax', invoice.get('tax_total', 0)) or 0))
    invoice_discount = Decimal(str(invoice.get('total_discount', 0) or 0))
    shipping = Decimal(str(invoice.get('shipping_charge', 0) or 0))
    adjustment = Decimal(str(invoice.get('adjustment', 0) or 0))
    stored_grand_total = Decimal(str(invoice.get('grand_total', 0) or 0))
    amount_paid = Decimal(str(invoice.get('amount_paid', 0) or 0))
    stored_balance = Decimal(str(invoice.get('balance_due') or 0))
    
    # Validate subtotal
    if line_items and abs(calc_subtotal - stored_subtotal) > Decimal('1'):
        errors.append(f"Subtotal mismatch: calculated {calc_subtotal}, stored {stored_subtotal}")
        corrected['subtotal'] = float(calc_subtotal)
    
    # Validate tax total
    if line_items and abs(calc_tax - stored_tax) > Decimal('1'):
        errors.append(f"Tax total mismatch: calculated {calc_tax}, stored {stored_tax}")
        corrected['total_tax'] = float(calc_tax)
    
    # Calculate expected grand total
    expected_grand_total = calc_subtotal + calc_tax - invoice_discount + shipping + adjustment
    expected_grand_total = expected_grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Validate grand total
    if line_items and abs(expected_grand_total - stored_grand_total) > Decimal('1'):
        errors.append(f"Grand total mismatch: calculated {expected_grand_total}, stored {stored_grand_total}")
        corrected['grand_total'] = float(expected_grand_total)
    
    # Validate balance_due
    final_grand_total = corrected.get('grand_total', float(stored_grand_total))
    expected_balance = Decimal(str(final_grand_total)) - amount_paid
    
    if abs(expected_balance - stored_balance) > Decimal('0.01'):
        errors.append(f"Balance due mismatch: calculated {expected_balance}, stored {stored_balance}")
        corrected['balance_due'] = float(expected_balance)
    
    return len(errors) == 0, errors, corrected


def validate_and_correct_invoice(invoice: Dict, auto_correct: bool = False) -> Dict:
    """
    Validate invoice and optionally auto-correct calculations.
    
    Args:
        invoice: Invoice data dictionary
        auto_correct: If True, return corrected values
        
    Returns:
        {
            'is_valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'corrected_values': Dict (if auto_correct=True),
            'original_values': Dict
        }
    """
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'corrected_values': {},
        'original_values': {}
    }
    
    # Validate line items
    line_items = invoice.get('line_items', [])
    for i, item in enumerate(line_items):
        is_valid, error, corrected = validate_line_item_calculation(item)
        if not is_valid:
            result['warnings'].append(f"Line item {i+1}: {error}")
            if auto_correct:
                result['corrected_values'][f'line_items.{i}'] = corrected
    
    # Validate invoice totals
    is_valid, errors, corrected = validate_invoice_totals(invoice)
    if not is_valid:
        result['is_valid'] = False
        result['errors'].extend(errors)
        if auto_correct:
            result['corrected_values'].update(corrected)
    
    # Store original values for reference
    result['original_values'] = {
        'subtotal': invoice.get('subtotal'),
        'total_tax': invoice.get('total_tax'),
        'grand_total': invoice.get('grand_total'),
        'balance_due': invoice.get('balance_due')
    }
    
    return result


def pre_save_validation(invoice: Dict) -> Dict:
    """
    Run validation before saving invoice.
    Raises ValueError if critical validation fails.
    
    Returns corrected invoice data.
    """
    validation = validate_and_correct_invoice(invoice, auto_correct=True)
    
    if validation['errors']:
        logger.warning(f"Invoice validation errors: {validation['errors']}")
        
        # Apply corrections
        corrected_invoice = invoice.copy()
        for key, value in validation['corrected_values'].items():
            if '.' not in key:  # Top-level field
                corrected_invoice[key] = value
        
        logger.info(f"Auto-corrected invoice values: {validation['corrected_values']}")
        return corrected_invoice
    
    return invoice
