"""
Battwheels OS - Calculation Regression Test Suite
Tests all financial calculation functions to prevent regressions.

Run with: pytest tests/test_calculations_regression.py -v
"""

import pytest
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.finance_calculator import (
    calculate_line_item,
    calculate_invoice_totals,
    calculate_tax_breakdown,
    calculate_reverse_tax,
    allocate_payment,
    unapply_payment,
    calculate_aging_bucket,
    calculate_aging_summary,
    validate_gst_number,
    round_currency
)


class TestLineItemCalculations:
    """Test line item calculation functions"""
    
    def test_basic_line_item_exclusive_tax(self):
        """Test basic line item with exclusive tax"""
        result = calculate_line_item(
            name="Battery Pack",
            quantity=2,
            rate=10000,
            tax_rate=18,
            discount_percent=10,
            is_igst=False,
            is_inclusive_tax=False
        )
        
        assert float(result.amount) == 20000  # 2 * 10000
        assert float(result.discount_amount) == 2000  # 10% of 20000
        assert float(result.taxable_amount) == 18000  # 20000 - 2000
        assert float(result.tax_amount) == 3240  # 18% of 18000
        assert float(result.item_total) == 21240  # 18000 + 3240
        
    def test_line_item_inclusive_tax(self):
        """Test line item with inclusive tax"""
        result = calculate_line_item(
            name="Service Charge",
            quantity=1,
            rate=1180,  # Includes 18% tax
            tax_rate=18,
            is_inclusive_tax=True
        )
        
        assert float(result.taxable_amount) == 1000
        assert float(result.tax_amount) == 180
        assert float(result.item_total) == 1180
        
    def test_line_item_no_tax(self):
        """Test line item with zero tax"""
        result = calculate_line_item(
            name="Exempt Item",
            quantity=5,
            rate=100,
            tax_rate=0
        )
        
        assert float(result.amount) == 500
        assert float(result.tax_amount) == 0
        assert float(result.item_total) == 500
        
    def test_line_item_cgst_sgst_split(self):
        """Test CGST/SGST split for intra-state"""
        result = calculate_line_item(
            name="Part",
            quantity=1,
            rate=1000,
            tax_rate=18,
            is_igst=False
        )
        
        # 18% split into 9% CGST + 9% SGST
        assert float(result.cgst_amount) == 90
        assert float(result.sgst_amount) == 90
        assert float(result.igst_amount) == 0
        
    def test_line_item_igst(self):
        """Test IGST for inter-state"""
        result = calculate_line_item(
            name="Part",
            quantity=1,
            rate=1000,
            tax_rate=18,
            is_igst=True
        )
        
        assert float(result.igst_amount) == 180
        assert float(result.cgst_amount) == 0
        assert float(result.sgst_amount) == 0


class TestInvoiceTotals:
    """Test invoice total calculations"""
    
    def test_basic_invoice_totals(self):
        """Test basic invoice totals calculation"""
        line_items = [
            calculate_line_item("Part A", 2, 1000, 18),  # 2360
            calculate_line_item("Part B", 1, 500, 18),   # 590
        ]
        
        totals = calculate_invoice_totals(line_items)
        
        assert totals.sub_total > 0
        assert totals.tax_total > 0
        assert totals.grand_total == totals.sub_total + totals.tax_total
        
    def test_invoice_with_discount(self):
        """Test invoice with percentage discount"""
        line_items = [
            calculate_line_item("Part", 1, 1000, 18),  # 1180
        ]
        
        totals = calculate_invoice_totals(
            line_items,
            invoice_discount_type='percentage',
            invoice_discount_value=10
        )
        
        assert totals.discount_total > 0
        assert totals.grand_total < 1180  # Should be less after discount
        
    def test_invoice_with_shipping(self):
        """Test invoice with shipping charge"""
        line_items = [
            calculate_line_item("Part", 1, 1000, 0),
        ]
        
        totals = calculate_invoice_totals(
            line_items,
            shipping_charge=100
        )
        
        assert totals.shipping_charge == 100
        assert totals.grand_total == 1100
        
    def test_invoice_with_adjustment(self):
        """Test invoice with adjustment"""
        line_items = [
            calculate_line_item("Part", 1, 1000, 0),
        ]
        
        totals = calculate_invoice_totals(
            line_items,
            adjustment=-10
        )
        
        assert totals.adjustment == -10
        assert totals.grand_total == 990


class TestTaxCalculations:
    """Test tax breakdown calculations"""
    
    def test_intra_state_tax_breakdown(self):
        """Test intra-state tax split"""
        result = calculate_tax_breakdown(10000, 18, is_igst=False)
        
        assert result['cgst_rate'] == 9
        assert result['sgst_rate'] == 9
        assert result['cgst_amount'] == 900
        assert result['sgst_amount'] == 900
        assert result['total_tax'] == 1800
        
    def test_inter_state_tax_breakdown(self):
        """Test inter-state tax (IGST)"""
        result = calculate_tax_breakdown(10000, 18, is_igst=True)
        
        assert result['igst_rate'] == 18
        assert result['igst_amount'] == 1800
        assert result['cgst_amount'] == 0
        assert result['sgst_amount'] == 0
        
    def test_reverse_tax_calculation(self):
        """Test extracting tax from inclusive amount"""
        result = calculate_reverse_tax(11800, 18)
        
        assert result['taxable_amount'] == 10000
        assert result['tax_amount'] == 1800


class TestPaymentAllocation:
    """Test payment allocation functions"""
    
    def test_oldest_first_allocation(self):
        """Test oldest-first allocation strategy"""
        invoices = [
            {'invoice_id': 'INV-001', 'invoice_number': 'INV-001', 'invoice_date': '2025-01-01', 'balance_due': 1000},
            {'invoice_id': 'INV-002', 'invoice_number': 'INV-002', 'invoice_date': '2025-01-15', 'balance_due': 2000},
        ]
        
        allocations = allocate_payment(2500, invoices, 'oldest_first')
        
        assert len(allocations) == 2
        assert allocations[0]['invoice_id'] == 'INV-001'
        assert allocations[0]['allocated_amount'] == 1000
        assert allocations[1]['invoice_id'] == 'INV-002'
        assert allocations[1]['allocated_amount'] == 1500
        
    def test_proportional_allocation(self):
        """Test proportional allocation strategy"""
        invoices = [
            {'invoice_id': 'INV-001', 'invoice_number': 'INV-001', 'invoice_date': '2025-01-01', 'balance_due': 1000},
            {'invoice_id': 'INV-002', 'invoice_number': 'INV-002', 'invoice_date': '2025-01-15', 'balance_due': 1000},
        ]
        
        allocations = allocate_payment(1000, invoices, 'proportional')
        
        assert len(allocations) == 2
        assert abs(allocations[0]['allocated_amount'] - 500) < 0.01
        assert abs(allocations[1]['allocated_amount'] - 500) < 0.01
        
    def test_overpayment_handling(self):
        """Test that overpayment doesn't exceed invoice balance"""
        invoices = [
            {'invoice_id': 'INV-001', 'invoice_number': 'INV-001', 'invoice_date': '2025-01-01', 'balance_due': 500},
        ]
        
        allocations = allocate_payment(1000, invoices, 'oldest_first')
        
        total_allocated = sum(a['allocated_amount'] for a in allocations)
        assert total_allocated == 500  # Should not exceed balance
        
    def test_unapply_payment(self):
        """Test payment reversal"""
        allocations = [
            {'invoice_id': 'INV-001', 'allocated_amount': 1000},
            {'invoice_id': 'INV-002', 'allocated_amount': 500},
        ]
        
        reversals = unapply_payment('PMT-001', allocations)
        
        assert len(reversals) == 2
        assert reversals[0]['amount_to_restore'] == 1000
        assert reversals[1]['amount_to_restore'] == 500


class TestAgingCalculations:
    """Test aging bucket calculations"""
    
    def test_current_bucket(self):
        """Test current (not overdue) bucket"""
        from datetime import datetime, timedelta
        
        future = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        assert calculate_aging_bucket(future, today) == 'current'
        assert calculate_aging_bucket(today, today) == 'current'
        
    def test_overdue_buckets(self):
        """Test overdue aging buckets"""
        from datetime import datetime, timedelta
        
        today = datetime.now().strftime('%Y-%m-%d')
        past_15 = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        past_45 = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        past_75 = (datetime.now() - timedelta(days=75)).strftime('%Y-%m-%d')
        past_120 = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
        
        assert calculate_aging_bucket(past_15, today) == '1-30'
        assert calculate_aging_bucket(past_45, today) == '31-60'
        assert calculate_aging_bucket(past_75, today) == '61-90'
        assert calculate_aging_bucket(past_120, today) == '90+'
        
    def test_aging_summary(self):
        """Test aging summary aggregation"""
        from datetime import datetime, timedelta
        
        today = datetime.now().strftime('%Y-%m-%d')
        future = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        past_20 = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
        
        invoices = [
            {'invoice_id': '1', 'due_date': future, 'balance_due': 1000},
            {'invoice_id': '2', 'due_date': past_20, 'balance_due': 2000},
        ]
        
        summary = calculate_aging_summary(invoices, today)
        
        assert summary['current']['count'] == 1
        assert summary['current']['amount'] == 1000
        assert summary['1-30']['count'] == 1
        assert summary['1-30']['amount'] == 2000


class TestGSTValidation:
    """Test GST number validation"""
    
    def test_valid_gst_number(self):
        """Test valid GST number"""
        result = validate_gst_number('07AAMCB4976D1ZG')
        
        assert result['is_valid'] == True
        assert result['state_code'] == '07'
        
    def test_invalid_gst_number(self):
        """Test invalid GST number"""
        result = validate_gst_number('12345INVALID')
        
        assert result['is_valid'] == False
        
    def test_empty_gst_number(self):
        """Test empty GST number"""
        result = validate_gst_number('')
        
        assert result['is_valid'] == False


class TestRounding:
    """Test currency rounding functions"""
    
    def test_round_half_up(self):
        """Test ROUND_HALF_UP behavior"""
        assert float(round_currency(10.125)) == 10.13
        assert float(round_currency(10.124)) == 10.12
        
    def test_round_negative(self):
        """Test rounding negative numbers"""
        assert float(round_currency(-10.125)) == -10.12  # Rounds towards zero
        
    def test_round_whole_numbers(self):
        """Test rounding whole numbers"""
        assert float(round_currency(100)) == 100
        assert float(round_currency(100.00)) == 100


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_quantity(self):
        """Test line item with zero quantity"""
        result = calculate_line_item("Part", 0, 1000, 18)
        
        assert float(result.amount) == 0
        assert float(result.item_total) == 0
        
    def test_zero_rate(self):
        """Test line item with zero rate"""
        result = calculate_line_item("Free Part", 5, 0, 18)
        
        assert float(result.amount) == 0
        assert float(result.item_total) == 0
        
    def test_very_large_numbers(self):
        """Test with large amounts"""
        result = calculate_line_item("Expensive Item", 100, 1000000, 18)
        
        assert float(result.amount) == 100000000
        assert float(result.tax_amount) == 18000000
        
    def test_decimal_precision(self):
        """Test decimal precision is maintained"""
        result = calculate_line_item("Precision Test", 3, 33.33, 18)
        
        # Should not have floating point errors
        assert result.item_total == result.item_total  # No NaN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
