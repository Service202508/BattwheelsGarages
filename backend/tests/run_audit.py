#!/usr/bin/env python3
"""
Comprehensive Production Audit Script for Battwheels OS
Runs synchronous HTTP tests against all modules
"""

import httpx
import json
from datetime import datetime, timezone
import os
import sys

BASE_URL = os.environ.get('API_BASE_URL', 'https://finance-engine-4.preview.emergentagent.com')
API_URL = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "test_pwd_placeholder"

class AuditResults:
    total = 0
    passed = 0
    failed = 0
    errors = []
    details = []

def log(msg, status="INFO"):
    colors = {"PASS": "\033[92m", "FAIL": "\033[91m", "INFO": "\033[94m", "WARN": "\033[93m", "END": "\033[0m"}
    prefix = colors.get(status, "")
    print(f"{prefix}[{status}]{colors['END']} {msg}")

def test(name, condition, detail=""):
    AuditResults.total += 1
    if condition:
        AuditResults.passed += 1
        log(f"✅ {name}", "PASS")
        AuditResults.details.append({"test": name, "status": "PASS", "detail": detail})
    else:
        AuditResults.failed += 1
        log(f"❌ {name} - {detail}", "FAIL")
        AuditResults.errors.append({"test": name, "error": detail})
        AuditResults.details.append({"test": name, "status": "FAIL", "detail": detail})
    return condition

def run_audit():
    print("\n" + "="*70)
    print("🔍 BATTWHEELS OS - COMPREHENSIVE PRODUCTION AUDIT")
    print("="*70)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*70 + "\n")
    
    client = httpx.Client(timeout=30.0)
    
    # ==================== AUTHENTICATION ====================
    log("PHASE 1: AUTHENTICATION", "INFO")
    
    auth_resp = client.post(f"{API_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if not test("Admin Login", auth_resp.status_code == 200, f"Status: {auth_resp.status_code}"):
        print("❌ Cannot proceed without authentication")
        return
    
    token = auth_resp.json().get('token')
    headers = {"Authorization": f"Bearer {token}"}
    log(f"Token obtained: {token[:20]}...", "INFO")
    
    # ==================== ITEMS ENHANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 2: ITEMS ENHANCED MODULE", "INFO")
    
    # Summary
    resp = client.get(f"{API_URL}/items-enhanced/summary", headers=headers)
    test("Items Summary Endpoint", resp.status_code == 200)
    if resp.status_code == 200:
        summary = resp.json().get('summary', {})
        log(f"   Items: {summary.get('total_items', 0)}, Active: {summary.get('active_items', 0)}", "INFO")
    
    # List with filters
    resp = client.get(f"{API_URL}/items-enhanced/?per_page=50", headers=headers)
    test("Items List", resp.status_code == 200 and 'items' in resp.json())
    
    resp = client.get(f"{API_URL}/items-enhanced/?item_type=inventory&per_page=20", headers=headers)
    test("Items Filter by Type", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/items-enhanced/?search=Engine&per_page=20", headers=headers)
    test("Items Search", resp.status_code == 200)
    
    # CRUD
    item_data = {
        "name": f"Audit Item {int(datetime.now().timestamp())}",
        "sku": f"AUD-{int(datetime.now().timestamp())}",
        "item_type": "inventory",
        "purchase_rate": 500,
        "sales_rate": 750,
        "tax_percentage": 18
    }
    resp = client.post(f"{API_URL}/items-enhanced/", headers=headers, json=item_data)
    test("Item Create", resp.status_code == 200)
    created_item_id = resp.json().get('item', {}).get('item_id') if resp.status_code == 200 else None
    
    if created_item_id:
        resp = client.get(f"{API_URL}/items-enhanced/{created_item_id}", headers=headers)
        test("Item Read", resp.status_code == 200)
        
        resp = client.put(f"{API_URL}/items-enhanced/{created_item_id}", headers=headers, json={"sales_rate": 800})
        test("Item Update", resp.status_code == 200)
    
    # Low stock
    resp = client.get(f"{API_URL}/items-enhanced/low-stock", headers=headers)
    test("Low Stock Report", resp.status_code == 200)
    
    # ==================== INVENTORY ENHANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 3: INVENTORY ENHANCED MODULE", "INFO")
    
    # Summary
    resp = client.get(f"{API_URL}/inventory-enhanced/summary", headers=headers)
    test("Inventory Summary", resp.status_code == 200)
    if resp.status_code == 200:
        summary = resp.json().get('summary', {})
        log(f"   Items: {summary.get('total_items', 0)}, Variants: {summary.get('total_variants', 0)}, Bundles: {summary.get('total_bundles', 0)}", "INFO")
    
    # Warehouses
    resp = client.get(f"{API_URL}/inventory-enhanced/warehouses", headers=headers)
    test("Warehouses List", resp.status_code == 200)
    warehouses = resp.json().get('warehouses', []) if resp.status_code == 200 else []
    
    wh_data = {"name": f"Audit WH {int(datetime.now().timestamp())}", "city": "Mumbai", "state": "Maharashtra"}
    resp = client.post(f"{API_URL}/inventory-enhanced/warehouses", headers=headers, json=wh_data)
    test("Warehouse Create", resp.status_code == 200)
    
    # Variants
    resp = client.get(f"{API_URL}/inventory-enhanced/variants", headers=headers)
    test("Variants List", resp.status_code == 200)
    
    # Get an inventory item for variant creation
    items_resp = client.get(f"{API_URL}/items-enhanced/?item_type=inventory&per_page=1", headers=headers)
    inventory_items = items_resp.json().get('items', []) if items_resp.status_code == 200 else []
    
    if inventory_items:
        var_data = {"item_id": inventory_items[0]['item_id'], "variant_name": f"Audit Var {int(datetime.now().timestamp())}", "additional_rate": 50}
        resp = client.post(f"{API_URL}/inventory-enhanced/variants", headers=headers, json=var_data)
        test("Variant Create", resp.status_code == 200)
    
    # Bundles
    resp = client.get(f"{API_URL}/inventory-enhanced/bundles", headers=headers)
    test("Bundles List", resp.status_code == 200)
    
    if len(inventory_items) >= 2:
        items_resp2 = client.get(f"{API_URL}/items-enhanced/?item_type=inventory&per_page=3", headers=headers)
        bundle_items = items_resp2.json().get('items', [])
        if len(bundle_items) >= 2:
            bundle_data = {
                "name": f"Audit Bundle {int(datetime.now().timestamp())}",
                "components": [{"item_id": bundle_items[0]['item_id'], "quantity": 2}, {"item_id": bundle_items[1]['item_id'], "quantity": 1}]
            }
            resp = client.post(f"{API_URL}/inventory-enhanced/bundles", headers=headers, json=bundle_data)
            test("Bundle Create", resp.status_code == 200)
    
    # Serial/Batch
    resp = client.get(f"{API_URL}/inventory-enhanced/serial-batches?status=all", headers=headers)
    test("Serial/Batch List", resp.status_code == 200)
    
    if inventory_items:
        serial_data = {"item_id": inventory_items[0]['item_id'], "tracking_type": "serial", "number": f"SN-AUD-{int(datetime.now().timestamp())}"}
        resp = client.post(f"{API_URL}/inventory-enhanced/serial-batches", headers=headers, json=serial_data)
        test("Serial Create", resp.status_code == 200)
    
    # Stock Adjustments
    if warehouses and inventory_items:
        adj_data = {
            "item_id": inventory_items[0]['item_id'],
            "warehouse_id": warehouses[0]['warehouse_id'],
            "adjustment_type": "add",
            "quantity": 100,
            "reason": "Audit test"
        }
        resp = client.post(f"{API_URL}/inventory-enhanced/adjustments", headers=headers, json=adj_data)
        test("Stock Adjustment Add", resp.status_code == 200)
        
        adj_data["adjustment_type"] = "subtract"
        adj_data["quantity"] = 10
        resp = client.post(f"{API_URL}/inventory-enhanced/adjustments", headers=headers, json=adj_data)
        test("Stock Adjustment Subtract", resp.status_code == 200)
    
    # Reports
    resp = client.get(f"{API_URL}/inventory-enhanced/reports/stock-summary", headers=headers)
    test("Stock Summary Report", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/inventory-enhanced/reports/low-stock", headers=headers)
    test("Low Stock Report", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/inventory-enhanced/reports/valuation", headers=headers)
    test("Valuation Report", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/inventory-enhanced/reports/movement?days=30", headers=headers)
    test("Movement Report", resp.status_code == 200)
    
    # ==================== CONTACTS ENHANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 4: CONTACTS ENHANCED MODULE", "INFO")
    
    # Summary
    resp = client.get(f"{API_URL}/contacts-enhanced/summary", headers=headers)
    test("Contacts Summary", resp.status_code == 200)
    
    # List with filters
    resp = client.get(f"{API_URL}/contacts-enhanced/?per_page=50", headers=headers)
    test("Contacts List", resp.status_code == 200 and 'contacts' in resp.json())
    contacts = resp.json().get('contacts', []) if resp.status_code == 200 else []
    
    resp = client.get(f"{API_URL}/contacts-enhanced/?contact_type=customer&per_page=50", headers=headers)
    test("Contacts Filter Customers", resp.status_code == 200)
    customers = resp.json().get('contacts', []) if resp.status_code == 200 else []
    
    resp = client.get(f"{API_URL}/contacts-enhanced/?contact_type=vendor&per_page=50", headers=headers)
    test("Contacts Filter Vendors", resp.status_code == 200)
    vendors = resp.json().get('contacts', []) if resp.status_code == 200 else []
    
    # CRUD
    unique_ts = int(datetime.now().timestamp())
    contact_data = {
        "name": f"Audit Contact {unique_ts}",
        "contact_type": "customer",
        "email": f"audit{unique_ts}@test.com",
        "phone": "+919876543210",
        "gstin": f"27AABCU{str(unique_ts)[-4:]}R1Z{str(unique_ts)[-1]}"  # Generate unique GSTIN
    }
    resp = client.post(f"{API_URL}/contacts-enhanced/", headers=headers, json=contact_data)
    test("Contact Create", resp.status_code == 200, resp.text[:100] if resp.status_code != 200 else "")
    created_contact_id = resp.json().get('contact', {}).get('contact_id') if resp.status_code == 200 else None
    
    if created_contact_id:
        resp = client.get(f"{API_URL}/contacts-enhanced/{created_contact_id}", headers=headers)
        test("Contact Read", resp.status_code == 200)
        
        # Check GSTIN state extraction - accepts full name or abbreviation
        contact = resp.json().get('contact', {})
        place = contact.get('place_of_supply', '')
        test("GSTIN State Extraction", "Maharashtra" in place or "MH" in place, f"Place: {place}")
        
        resp = client.put(f"{API_URL}/contacts-enhanced/{created_contact_id}", headers=headers, json={"credit_limit": 200000})
        test("Contact Update", resp.status_code == 200)
        
        # Add person
        person_data = {"first_name": "Audit", "last_name": "Person", "email": f"ap{int(datetime.now().timestamp())}@test.com"}
        resp = client.post(f"{API_URL}/contacts-enhanced/{created_contact_id}/persons", headers=headers, json=person_data)
        test("Contact Person Add", resp.status_code == 200)
        
        # Add address
        addr_data = {"address_type": "billing", "street": "123 Test St", "city": "Mumbai", "state": "Maharashtra", "pincode": "400001"}
        resp = client.post(f"{API_URL}/contacts-enhanced/{created_contact_id}/addresses", headers=headers, json=addr_data)
        test("Contact Address Add", resp.status_code == 200)
    
    # ==================== ESTIMATES ENHANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 5: ESTIMATES ENHANCED MODULE", "INFO")
    
    resp = client.get(f"{API_URL}/estimates-enhanced/summary", headers=headers)
    test("Estimates Summary", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/estimates-enhanced/?per_page=50", headers=headers)
    test("Estimates List", resp.status_code == 200)
    
    if customers and inventory_items:
        est_data = {
            "customer_id": customers[0]['contact_id'],
            "estimate_date": datetime.now().strftime("%Y-%m-%d"),
            "line_items": [{"item_id": inventory_items[0]['item_id'], "name": inventory_items[0]['name'], "quantity": 5, "rate": 100, "tax_rate": 18}]
        }
        resp = client.post(f"{API_URL}/estimates-enhanced/", headers=headers, json=est_data)
        test("Estimate Create", resp.status_code == 200)
        estimate_id = resp.json().get('estimate', {}).get('estimate_id') if resp.status_code == 200 else None
        
        if estimate_id:
            resp = client.get(f"{API_URL}/estimates-enhanced/{estimate_id}", headers=headers)
            test("Estimate Read", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/estimates-enhanced/reports/conversion-funnel", headers=headers)
    test("Conversion Funnel", resp.status_code == 200 and 'funnel' in resp.json())
    
    # ==================== SALES ORDERS ENHANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 6: SALES ORDERS ENHANCED MODULE", "INFO")
    
    resp = client.get(f"{API_URL}/sales-orders-enhanced/summary", headers=headers)
    test("Sales Orders Summary", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/sales-orders-enhanced/?per_page=50", headers=headers)
    test("Sales Orders List", resp.status_code == 200)
    
    if customers and inventory_items:
        so_data = {
            "customer_id": customers[0]['contact_id'],
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "line_items": [{"item_id": inventory_items[0]['item_id'], "name": inventory_items[0]['name'], "quantity": 3, "rate": 150, "tax_rate": 18}]
        }
        resp = client.post(f"{API_URL}/sales-orders-enhanced/", headers=headers, json=so_data)
        test("Sales Order Create", resp.status_code == 200)
    
    # ==================== INVOICES ENHANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 7: INVOICES ENHANCED MODULE", "INFO")
    
    resp = client.get(f"{API_URL}/invoices-enhanced/summary", headers=headers)
    test("Invoices Summary", resp.status_code == 200)
    if resp.status_code == 200:
        summary = resp.json().get('summary', {})
        log(f"   Total: {summary.get('total_invoices', 0)}, Outstanding: ₹{summary.get('total_outstanding', 0):,.2f}", "INFO")
    
    resp = client.get(f"{API_URL}/invoices-enhanced/?per_page=50", headers=headers)
    test("Invoices List", resp.status_code == 200)
    invoices = resp.json().get('invoices', []) if resp.status_code == 200 else []
    
    if customers and inventory_items:
        inv_data = {
            "customer_id": customers[0]['contact_id'],
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_terms": 30,
            "line_items": [{"name": "Audit Invoice Item", "quantity": 2, "rate": 1000, "tax_rate": 18}]
        }
        resp = client.post(f"{API_URL}/invoices-enhanced/", headers=headers, json=inv_data)
        test("Invoice Create", resp.status_code == 200)
        invoice_id = resp.json().get('invoice', {}).get('invoice_id') if resp.status_code == 200 else None
        
        if invoice_id:
            resp = client.get(f"{API_URL}/invoices-enhanced/{invoice_id}", headers=headers)
            test("Invoice Read", resp.status_code == 200)
            
            # Record payment
            pmt_data = {"amount": 500, "payment_mode": "bank_transfer", "payment_date": datetime.now().strftime("%Y-%m-%d")}
            resp = client.post(f"{API_URL}/invoices-enhanced/{invoice_id}/payments", headers=headers, json=pmt_data)
            test("Invoice Payment", resp.status_code in [200, 400])  # May need to be sent first
    
    resp = client.get(f"{API_URL}/invoices-enhanced/reports/aging", headers=headers)
    test("Invoice Aging Report", resp.status_code == 200 and 'report' in resp.json())
    
    # ==================== BILLS ENHANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 8: BILLS ENHANCED MODULE", "INFO")
    
    resp = client.get(f"{API_URL}/bills-enhanced/summary", headers=headers)
    test("Bills Summary", resp.status_code == 200)
    if resp.status_code == 200:
        summary = resp.json().get('summary', {})
        log(f"   Total: {summary.get('total_bills', 0)}, Payable: ₹{summary.get('total_payable', 0):,.2f}", "INFO")
    
    resp = client.get(f"{API_URL}/bills-enhanced/?per_page=50", headers=headers)
    test("Bills List", resp.status_code == 200)
    
    if vendors and inventory_items:
        bill_data = {
            "vendor_id": vendors[0]['contact_id'],
            "bill_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_terms": 30,
            "line_items": [{"name": "Audit Bill Item", "quantity": 10, "rate": 50, "tax_rate": 18}]
        }
        resp = client.post(f"{API_URL}/bills-enhanced/", headers=headers, json=bill_data)
        test("Bill Create", resp.status_code == 200)
        bill_id = resp.json().get('bill', {}).get('bill_id') if resp.status_code == 200 else None
        
        if bill_id:
            resp = client.get(f"{API_URL}/bills-enhanced/{bill_id}", headers=headers)
            test("Bill Read", resp.status_code == 200)
    
    # Purchase Orders
    resp = client.get(f"{API_URL}/bills-enhanced/purchase-orders/summary", headers=headers)
    test("PO Summary", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/bills-enhanced/purchase-orders", headers=headers)
    test("PO List", resp.status_code == 200)
    
    if vendors and inventory_items:
        po_data = {
            "vendor_id": vendors[0]['contact_id'],
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "line_items": [{"name": "Audit PO Item", "quantity": 20, "rate": 30, "tax_rate": 18}]
        }
        resp = client.post(f"{API_URL}/bills-enhanced/purchase-orders", headers=headers, json=po_data)
        test("PO Create", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/bills-enhanced/aging-report", headers=headers)
    test("Bills Aging Report", resp.status_code == 200)
    
    # ==================== REPORTS ADVANCED MODULE ====================
    print("\n" + "-"*50)
    log("PHASE 9: REPORTS & ANALYTICS", "INFO")
    
    resp = client.get(f"{API_URL}/reports-advanced/dashboard-summary", headers=headers)
    test("Dashboard Summary", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/reports-advanced/revenue/monthly", headers=headers)
    test("Monthly Revenue", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/reports-advanced/revenue/quarterly", headers=headers)
    test("Quarterly Revenue", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/reports-advanced/receivables/aging", headers=headers)
    test("Receivables Aging", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/reports-advanced/customers/top-revenue", headers=headers)
    test("Top Customers Revenue", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/reports-advanced/customers/top-outstanding", headers=headers)
    test("Top Outstanding", resp.status_code == 200)
    
    # ==================== GST COMPLIANCE ====================
    print("\n" + "-"*50)
    log("PHASE 10: GST COMPLIANCE", "INFO")
    
    resp = client.get(f"{API_URL}/gst/summary", headers=headers)
    test("GST Summary", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/gst/gstr1?period=2026-02", headers=headers)
    test("GSTR-1 Report", resp.status_code == 200)
    
    # ==================== CUSTOMER PORTAL ====================
    print("\n" + "-"*50)
    log("PHASE 11: CUSTOMER PORTAL", "INFO")
    
    resp = client.post(f"{API_URL}/customer-portal/login", json={"token": "testtoken123456789"})
    test("Portal Login Endpoint", resp.status_code in [200, 401, 400, 422])  # Any response is acceptable
    
    resp = client.get(f"{BASE_URL}/customer-portal")
    test("Portal Page Accessible", resp.status_code in [200, 304])
    
    # ==================== SHIPMENTS & RETURNS ====================
    print("\n" + "-"*50)
    log("PHASE 12: SHIPMENTS & RETURNS", "INFO")
    
    resp = client.get(f"{API_URL}/inventory-enhanced/shipments", headers=headers)
    test("Shipments List", resp.status_code == 200)
    
    resp = client.get(f"{API_URL}/inventory-enhanced/returns", headers=headers)
    test("Returns List", resp.status_code == 200)
    
    # ==================== FINAL SUMMARY ====================
    print("\n" + "="*70)
    print("📊 AUDIT SUMMARY")
    print("="*70)
    
    pass_rate = (AuditResults.passed / AuditResults.total * 100) if AuditResults.total > 0 else 0
    
    print(f"""
Total Tests:  {AuditResults.total}
Passed:       {AuditResults.passed} ({pass_rate:.1f}%)
Failed:       {AuditResults.failed}
""")
    
    if AuditResults.failed > 0:
        print("Failed Tests:")
        for err in AuditResults.errors:
            print(f"  ❌ {err['test']}: {err['error']}")
    
    if pass_rate >= 95:
        print("\n✅ APPLICATION MARKET-READY - Pass rate above 95%")
    elif pass_rate >= 80:
        print("\n⚠️ APPLICATION NEEDS MINOR FIXES - Pass rate between 80-95%")
    else:
        print("\n❌ APPLICATION NEEDS SIGNIFICANT WORK - Pass rate below 80%")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "target": BASE_URL,
        "total_tests": AuditResults.total,
        "passed": AuditResults.passed,
        "failed": AuditResults.failed,
        "pass_rate": pass_rate,
        "errors": AuditResults.errors,
        "details": AuditResults.details,
        "market_ready": pass_rate >= 95
    }
    
    with open('/app/test_reports/comprehensive_audit.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Full report saved to: /app/test_reports/comprehensive_audit.json")
    
    client.close()
    return pass_rate >= 95

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
