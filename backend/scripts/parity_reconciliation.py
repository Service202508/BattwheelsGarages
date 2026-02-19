#!/usr/bin/env python3
"""
Parity Reconciliation Script
Compares Battwheels OS data with Zoho Books export to identify discrepancies

Usage:
    python parity_reconciliation.py --zoho-export /path/to/zoho_export.json
    python parity_reconciliation.py --check-internal
    python parity_reconciliation.py --fix-discrepancies
"""

import asyncio
import argparse
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional
import motor.motor_asyncio

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ========================= RECONCILIATION CLASSES =========================

class Discrepancy:
    """Represents a data discrepancy"""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        field: str,
        zoho_value: Any,
        clone_value: Any,
        severity: str = "medium"  # low, medium, high, critical
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.field = field
        self.zoho_value = zoho_value
        self.clone_value = clone_value
        self.severity = severity
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "field": self.field,
            "zoho_value": self.zoho_value,
            "clone_value": self.clone_value,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "difference": self._calculate_difference()
        }
    
    def _calculate_difference(self) -> Any:
        if isinstance(self.zoho_value, (int, float)) and isinstance(self.clone_value, (int, float)):
            return round(self.zoho_value - self.clone_value, 2)
        return None

class ReconciliationReport:
    """Aggregates reconciliation results"""
    
    def __init__(self):
        self.discrepancies: List[Discrepancy] = []
        self.entities_checked = 0
        self.entities_matched = 0
        self.start_time = datetime.now(timezone.utc)
        self.end_time = None
    
    def add_discrepancy(self, discrepancy: Discrepancy):
        self.discrepancies.append(discrepancy)
    
    def finalize(self):
        self.end_time = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        critical = [d for d in self.discrepancies if d.severity == "critical"]
        high = [d for d in self.discrepancies if d.severity == "high"]
        medium = [d for d in self.discrepancies if d.severity == "medium"]
        low = [d for d in self.discrepancies if d.severity == "low"]
        
        parity_score = (self.entities_matched / self.entities_checked * 100) if self.entities_checked > 0 else 0
        
        return {
            "summary": {
                "entities_checked": self.entities_checked,
                "entities_matched": self.entities_matched,
                "total_discrepancies": len(self.discrepancies),
                "critical_discrepancies": len(critical),
                "high_discrepancies": len(high),
                "medium_discrepancies": len(medium),
                "low_discrepancies": len(low),
                "parity_score": round(parity_score, 2),
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None
            },
            "discrepancies_by_type": self._group_by_type(),
            "all_discrepancies": [d.to_dict() for d in self.discrepancies]
        }
    
    def _group_by_type(self) -> Dict:
        grouped = {}
        for d in self.discrepancies:
            if d.entity_type not in grouped:
                grouped[d.entity_type] = []
            grouped[d.entity_type].append(d.to_dict())
        return grouped

# ========================= COMPARISON FUNCTIONS =========================

def compare_values(zoho_val: Any, clone_val: Any, tolerance: float = 0.01) -> bool:
    """Compare two values with tolerance for numerical values"""
    if zoho_val is None and clone_val is None:
        return True
    if zoho_val is None or clone_val is None:
        return False
    
    # Numeric comparison with tolerance
    if isinstance(zoho_val, (int, float)) and isinstance(clone_val, (int, float)):
        return abs(zoho_val - clone_val) <= tolerance
    
    # String comparison (case insensitive)
    if isinstance(zoho_val, str) and isinstance(clone_val, str):
        return zoho_val.strip().lower() == clone_val.strip().lower()
    
    # Date comparison
    if isinstance(zoho_val, str) and isinstance(clone_val, str):
        try:
            # Try parsing as dates
            z_date = zoho_val[:10]  # YYYY-MM-DD
            c_date = clone_val[:10]
            return z_date == c_date
        except:
            pass
    
    return zoho_val == clone_val

# ========================= INTERNAL CONSISTENCY CHECKS =========================

async def check_invoice_totals(report: ReconciliationReport):
    """Verify invoice totals match line item sums"""
    print("Checking invoice totals consistency...")
    
    invoices = await db["invoices_enhanced"].find({}, {"_id": 0}).to_list(10000)
    line_items_collection = db["invoice_line_items"]
    
    for inv in invoices:
        report.entities_checked += 1
        invoice_id = inv.get("invoice_id")
        
        # Get line items
        items = await line_items_collection.find(
            {"invoice_id": invoice_id},
            {"_id": 0}
        ).to_list(100)
        
        # Calculate expected totals
        calculated_subtotal = sum(item.get("item_total", 0) for item in items)
        calculated_tax = sum(item.get("tax_amount", 0) for item in items)
        stored_subtotal = inv.get("sub_total", 0)
        stored_tax = inv.get("tax_total", 0)
        stored_total = inv.get("grand_total", 0)
        
        has_discrepancy = False
        
        # Check subtotal
        if not compare_values(calculated_subtotal, stored_subtotal, 1.0):
            report.add_discrepancy(Discrepancy(
                "invoice", invoice_id, "sub_total",
                calculated_subtotal, stored_subtotal, "high"
            ))
            has_discrepancy = True
        
        # Check tax
        if not compare_values(calculated_tax, stored_tax, 1.0):
            report.add_discrepancy(Discrepancy(
                "invoice", invoice_id, "tax_total",
                calculated_tax, stored_tax, "medium"
            ))
            has_discrepancy = True
        
        # Check grand total
        expected_total = calculated_subtotal + calculated_tax + inv.get("shipping_charge", 0) + inv.get("adjustment", 0)
        if not compare_values(expected_total, stored_total, 1.0):
            report.add_discrepancy(Discrepancy(
                "invoice", invoice_id, "grand_total",
                expected_total, stored_total, "critical"
            ))
            has_discrepancy = True
        
        if not has_discrepancy:
            report.entities_matched += 1

async def check_payment_allocations(report: ReconciliationReport):
    """Verify payment allocations match invoice balances"""
    print("Checking payment allocations consistency...")
    
    invoices = await db["invoices_enhanced"].find(
        {"status": {"$ne": "draft"}},
        {"_id": 0, "invoice_id": 1, "grand_total": 1, "amount_paid": 1, "balance_due": 1}
    ).to_list(10000)
    
    for inv in invoices:
        report.entities_checked += 1
        invoice_id = inv.get("invoice_id")
        
        # Calculate expected balance
        expected_balance = inv.get("grand_total", 0) - inv.get("amount_paid", 0)
        stored_balance = inv.get("balance_due", 0)
        
        if not compare_values(expected_balance, stored_balance, 0.01):
            report.add_discrepancy(Discrepancy(
                "invoice", invoice_id, "balance_due",
                expected_balance, stored_balance, "critical"
            ))
        else:
            report.entities_matched += 1

async def check_customer_balances(report: ReconciliationReport):
    """Verify customer outstanding balances"""
    print("Checking customer balances consistency...")
    
    customers = await db["contacts_enhanced"].find(
        {"contact_type": {"$in": ["customer", "both"]}},
        {"_id": 0, "contact_id": 1, "display_name": 1, "outstanding_receivable_amount": 1}
    ).to_list(10000)
    
    for customer in customers:
        report.entities_checked += 1
        customer_id = customer.get("contact_id")
        
        # Calculate outstanding from invoices
        invoices = await db["invoices_enhanced"].find(
            {"customer_id": customer_id, "status": {"$nin": ["draft", "void"]}},
            {"_id": 0, "balance_due": 1}
        ).to_list(1000)
        
        calculated_outstanding = sum(inv.get("balance_due", 0) for inv in invoices)
        stored_outstanding = customer.get("outstanding_receivable_amount", 0)
        
        if not compare_values(calculated_outstanding, stored_outstanding, 1.0):
            report.add_discrepancy(Discrepancy(
                "customer", customer_id, "outstanding_receivable_amount",
                calculated_outstanding, stored_outstanding, "high"
            ))
        else:
            report.entities_matched += 1

async def check_inventory_levels(report: ReconciliationReport):
    """Verify inventory stock levels"""
    print("Checking inventory levels consistency...")
    
    items = await db["items"].find(
        {"item_type": {"$in": ["inventory", "sales_and_purchases"]}},
        {"_id": 0, "item_id": 1, "name": 1, "stock_on_hand": 1, "on_hand_stock": 1}
    ).to_list(10000)
    
    for item in items:
        report.entities_checked += 1
        item_id = item.get("item_id")
        
        stock_on_hand = item.get("stock_on_hand", item.get("on_hand_stock", 0))
        
        # Check for negative stock
        if stock_on_hand < 0:
            report.add_discrepancy(Discrepancy(
                "item", item_id, "stock_on_hand",
                0, stock_on_hand, "critical"
            ))
        else:
            report.entities_matched += 1

async def check_estimate_invoice_links(report: ReconciliationReport):
    """Verify estimate to invoice conversion links"""
    print("Checking estimate-invoice links consistency...")
    
    estimates = await db["estimates_enhanced"].find(
        {"status": "invoiced"},
        {"_id": 0, "estimate_id": 1, "estimate_number": 1, "invoice_id": 1}
    ).to_list(10000)
    
    for est in estimates:
        report.entities_checked += 1
        estimate_id = est.get("estimate_id")
        invoice_id = est.get("invoice_id")
        
        if invoice_id:
            # Verify invoice exists
            invoice = await db["invoices_enhanced"].find_one({"invoice_id": invoice_id})
            if not invoice:
                report.add_discrepancy(Discrepancy(
                    "estimate", estimate_id, "invoice_id",
                    invoice_id, None, "high"
                ))
            else:
                report.entities_matched += 1
        else:
            report.entities_matched += 1

# ========================= ZOHO EXPORT COMPARISON =========================

async def compare_with_zoho_export(zoho_data: Dict, report: ReconciliationReport):
    """Compare clone data with Zoho Books export"""
    
    # Compare invoices
    if "invoices" in zoho_data:
        print(f"Comparing {len(zoho_data['invoices'])} invoices...")
        for zoho_inv in zoho_data["invoices"]:
            report.entities_checked += 1
            
            # Find matching invoice in clone
            clone_inv = await db["invoices_enhanced"].find_one(
                {"invoice_number": zoho_inv.get("invoice_number")},
                {"_id": 0}
            )
            
            if not clone_inv:
                report.add_discrepancy(Discrepancy(
                    "invoice", zoho_inv.get("invoice_number"), "existence",
                    "exists", "missing", "critical"
                ))
                continue
            
            # Compare key fields
            fields_to_compare = [
                ("grand_total", "total", "critical"),
                ("sub_total", "sub_total", "high"),
                ("tax_total", "tax_total", "medium"),
                ("balance_due", "balance", "critical"),
                ("status", "status", "high")
            ]
            
            has_discrepancy = False
            for clone_field, zoho_field, severity in fields_to_compare:
                zoho_val = zoho_inv.get(zoho_field, zoho_inv.get(clone_field))
                clone_val = clone_inv.get(clone_field)
                
                if not compare_values(zoho_val, clone_val):
                    report.add_discrepancy(Discrepancy(
                        "invoice", clone_inv.get("invoice_id"), clone_field,
                        zoho_val, clone_val, severity
                    ))
                    has_discrepancy = True
            
            if not has_discrepancy:
                report.entities_matched += 1
    
    # Compare customers
    if "contacts" in zoho_data or "customers" in zoho_data:
        contacts = zoho_data.get("contacts", zoho_data.get("customers", []))
        print(f"Comparing {len(contacts)} contacts...")
        
        for zoho_contact in contacts:
            report.entities_checked += 1
            
            clone_contact = await db["contacts_enhanced"].find_one(
                {"$or": [
                    {"contact_id": zoho_contact.get("contact_id")},
                    {"display_name": zoho_contact.get("contact_name", zoho_contact.get("display_name"))}
                ]},
                {"_id": 0}
            )
            
            if not clone_contact:
                report.add_discrepancy(Discrepancy(
                    "contact", zoho_contact.get("contact_name"), "existence",
                    "exists", "missing", "medium"
                ))
            else:
                report.entities_matched += 1
    
    # Compare items
    if "items" in zoho_data:
        print(f"Comparing {len(zoho_data['items'])} items...")
        for zoho_item in zoho_data["items"]:
            report.entities_checked += 1
            
            clone_item = await db["items"].find_one(
                {"$or": [
                    {"item_id": zoho_item.get("item_id")},
                    {"sku": zoho_item.get("sku")},
                    {"name": zoho_item.get("name")}
                ]},
                {"_id": 0}
            )
            
            if not clone_item:
                report.add_discrepancy(Discrepancy(
                    "item", zoho_item.get("name"), "existence",
                    "exists", "missing", "medium"
                ))
            else:
                # Compare stock
                zoho_stock = zoho_item.get("stock_on_hand", zoho_item.get("available_stock", 0))
                clone_stock = clone_item.get("stock_on_hand", clone_item.get("on_hand_stock", 0))
                
                if not compare_values(zoho_stock, clone_stock, 1.0):
                    report.add_discrepancy(Discrepancy(
                        "item", clone_item.get("item_id"), "stock_on_hand",
                        zoho_stock, clone_stock, "high"
                    ))
                else:
                    report.entities_matched += 1

# ========================= FIX FUNCTIONS =========================

async def fix_invoice_balances():
    """Fix incorrect invoice balance_due values"""
    print("Fixing invoice balances...")
    
    invoices = await db["invoices_enhanced"].find({}, {"_id": 0}).to_list(10000)
    fixed_count = 0
    
    for inv in invoices:
        invoice_id = inv.get("invoice_id")
        expected_balance = inv.get("grand_total", 0) - inv.get("amount_paid", 0)
        stored_balance = inv.get("balance_due", 0)
        
        if abs(expected_balance - stored_balance) > 0.01:
            await db["invoices_enhanced"].update_one(
                {"invoice_id": invoice_id},
                {"$set": {"balance_due": expected_balance}}
            )
            fixed_count += 1
    
    print(f"Fixed {fixed_count} invoice balances")
    return fixed_count

async def fix_negative_stock():
    """Fix items with negative stock"""
    print("Fixing negative stock levels...")
    
    result = await db["items"].update_many(
        {"$or": [
            {"stock_on_hand": {"$lt": 0}},
            {"on_hand_stock": {"$lt": 0}}
        ]},
        {"$set": {"stock_on_hand": 0, "on_hand_stock": 0}}
    )
    
    print(f"Fixed {result.modified_count} items with negative stock")
    return result.modified_count

async def fix_customer_balances():
    """Recalculate and fix customer outstanding balances"""
    print("Fixing customer balances...")
    
    customers = await db["contacts_enhanced"].find(
        {"contact_type": {"$in": ["customer", "both"]}},
        {"_id": 0, "contact_id": 1}
    ).to_list(10000)
    
    fixed_count = 0
    for customer in customers:
        customer_id = customer.get("contact_id")
        
        # Calculate outstanding
        invoices = await db["invoices_enhanced"].find(
            {"customer_id": customer_id, "status": {"$nin": ["draft", "void"]}},
            {"_id": 0, "balance_due": 1}
        ).to_list(1000)
        
        calculated_outstanding = sum(inv.get("balance_due", 0) for inv in invoices)
        
        result = await db["contacts_enhanced"].update_one(
            {"contact_id": customer_id},
            {"$set": {"outstanding_receivable_amount": calculated_outstanding}}
        )
        
        if result.modified_count > 0:
            fixed_count += 1
    
    print(f"Fixed {fixed_count} customer balances")
    return fixed_count

# ========================= MAIN EXECUTION =========================

async def run_internal_checks() -> Dict:
    """Run all internal consistency checks"""
    report = ReconciliationReport()
    
    await check_invoice_totals(report)
    await check_payment_allocations(report)
    await check_customer_balances(report)
    await check_inventory_levels(report)
    await check_estimate_invoice_links(report)
    
    report.finalize()
    return report.to_dict()

async def run_zoho_comparison(zoho_file: str) -> Dict:
    """Compare with Zoho export file"""
    with open(zoho_file, 'r') as f:
        zoho_data = json.load(f)
    
    report = ReconciliationReport()
    await compare_with_zoho_export(zoho_data, report)
    report.finalize()
    return report.to_dict()

async def run_fixes() -> Dict:
    """Run all fix functions"""
    results = {
        "invoice_balances_fixed": await fix_invoice_balances(),
        "negative_stock_fixed": await fix_negative_stock(),
        "customer_balances_fixed": await fix_customer_balances()
    }
    return results

def main():
    parser = argparse.ArgumentParser(description="Parity Reconciliation Script")
    parser.add_argument("--zoho-export", help="Path to Zoho Books export JSON file")
    parser.add_argument("--check-internal", action="store_true", help="Run internal consistency checks")
    parser.add_argument("--fix-discrepancies", action="store_true", help="Fix identified discrepancies")
    parser.add_argument("--output", default="/app/parity_report.json", help="Output file path")
    
    args = parser.parse_args()
    
    async def execute():
        results = {}
        
        if args.check_internal:
            print("\n=== Running Internal Consistency Checks ===\n")
            results["internal_checks"] = await run_internal_checks()
        
        if args.zoho_export:
            print(f"\n=== Comparing with Zoho Export: {args.zoho_export} ===\n")
            results["zoho_comparison"] = await run_zoho_comparison(args.zoho_export)
        
        if args.fix_discrepancies:
            print("\n=== Fixing Discrepancies ===\n")
            results["fixes_applied"] = await run_fixes()
        
        # Default: run internal checks
        if not (args.check_internal or args.zoho_export or args.fix_discrepancies):
            print("\n=== Running Internal Consistency Checks (default) ===\n")
            results["internal_checks"] = await run_internal_checks()
        
        # Save report
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n=== Report saved to {args.output} ===")
        
        # Print summary
        if "internal_checks" in results:
            summary = results["internal_checks"]["summary"]
            print(f"\nParity Score: {summary['parity_score']}%")
            print(f"Entities Checked: {summary['entities_checked']}")
            print(f"Entities Matched: {summary['entities_matched']}")
            print(f"Total Discrepancies: {summary['total_discrepancies']}")
            print(f"  - Critical: {summary['critical_discrepancies']}")
            print(f"  - High: {summary['high_discrepancies']}")
            print(f"  - Medium: {summary['medium_discrepancies']}")
            print(f"  - Low: {summary['low_discrepancies']}")
        
        return results
    
    return asyncio.run(execute())

if __name__ == "__main__":
    main()
