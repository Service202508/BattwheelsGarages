#!/usr/bin/env python3
"""
Zoho Books API v3 Complete Migration Audit and Gap Analysis
Identifies missing modules, endpoints, and features for Battwheels OS
"""

import os
import json

# Complete Zoho Books API v3 Module Specification
ZOHO_BOOKS_MODULES = {
    "contacts": {
        "endpoints": [
            "GET /contacts", "POST /contacts", "PUT /contacts/{id}", "GET /contacts/{id}",
            "DELETE /contacts/{id}", "POST /contacts/{id}/markasactive", "POST /contacts/{id}/markasinactive",
            "POST /contacts/{id}/enableportalaccess", "POST /contacts/{id}/disableportalaccess",
            "POST /contacts/{id}/emailstatement", "GET /contacts/{id}/statementmailcontent",
            "POST /contacts/{id}/email"
        ],
        "features": ["persons", "addresses", "portal_access", "statements", "tags", "custom_fields", "1099_tracking"],
        "battwheels_route": "/app/backend/routes/contacts_enhanced_v2.py"
    },
    "contact_persons": {
        "endpoints": [
            "POST /contact-persons", "PUT /contact-persons/{id}", "DELETE /contact-persons/{id}",
            "GET /contact-persons", "GET /contact-persons/{id}", "POST /contact-persons/{id}/markasprimary"
        ],
        "features": ["primary_contact", "email", "phone", "designation"],
        "battwheels_route": "/app/backend/routes/contacts_enhanced_v2.py"
    },
    "items": {
        "endpoints": [
            "GET /items", "POST /items", "PUT /items/{id}", "GET /items/{id}",
            "DELETE /items/{id}", "POST /items/{id}/active", "POST /items/{id}/inactive",
            "GET /itemdetails"
        ],
        "features": ["inventory_tracking", "variants", "bundles", "serial_tracking", "batch_tracking", 
                     "reorder_levels", "multi_warehouse", "price_lists", "hsn_sac_codes", "custom_fields"],
        "battwheels_route": "/app/backend/routes/items_enhanced.py"
    },
    "estimates": {
        "endpoints": [
            "POST /estimates", "PUT /estimates/{id}", "GET /estimates", "GET /estimates/{id}",
            "DELETE /estimates/{id}", "POST /estimates/{id}/marksent", "POST /estimates/{id}/markaccepted",
            "POST /estimates/{id}/markdeclined", "POST /estimates/{id}/email",
            "GET /estimates/{id}/emailcontent", "POST /estimates/{id}/submitforapproval",
            "POST /estimates/{id}/approve", "POST /estimates/{id}/convert"
        ],
        "features": ["status_workflow", "email", "pdf", "line_items", "discounts", "taxes", 
                     "templates", "comments", "attachments", "approvals", "conversions"],
        "battwheels_route": "/app/backend/routes/estimates_enhanced.py"
    },
    "sales_orders": {
        "endpoints": [
            "POST /salesorders", "PUT /salesorders/{id}", "GET /salesorders", "GET /salesorders/{id}",
            "DELETE /salesorders/{id}", "POST /salesorders/{id}/markopen", "POST /salesorders/{id}/markvoid",
            "POST /salesorders/{id}/email", "POST /salesorders/{id}/convert-to-invoice"
        ],
        "features": ["status_workflow", "fulfillment", "shipments", "conversions", "templates"],
        "battwheels_route": "/app/backend/routes/sales_orders_enhanced.py"
    },
    "invoices": {
        "endpoints": [
            "POST /invoices", "PUT /invoices/{id}", "GET /invoices", "GET /invoices/{id}",
            "DELETE /invoices/{id}", "POST /invoices/{id}/marksent", "POST /invoices/{id}/void",
            "POST /invoices/{id}/markdraft", "POST /invoices/{id}/email", "POST /invoices/{id}/remind",
            "POST /invoices/{id}/writeoff", "POST /invoices/{id}/cancelwriteoff",
            "GET /invoices/{id}/paymentlink", "POST /invoices/{id}/applycredits"
        ],
        "features": ["payments", "credits", "write_offs", "reminders", "payment_links", 
                     "attachments", "templates", "recurring", "line_items"],
        "battwheels_route": "/app/backend/routes/invoices_enhanced.py"
    },
    "recurring_invoices": {
        "endpoints": [
            "POST /recurring-invoices", "PUT /recurring-invoices/{id}", "GET /recurring-invoices",
            "GET /recurring-invoices/{id}", "DELETE /recurring-invoices/{id}",
            "POST /recurring-invoices/{id}/stop", "POST /recurring-invoices/{id}/resume"
        ],
        "features": ["frequency", "auto_generation", "email", "child_invoices"],
        "battwheels_route": "/app/backend/routes/invoices_enhanced.py"
    },
    "credit_notes": {
        "endpoints": [
            "POST /creditnotes", "PUT /creditnotes/{id}", "GET /creditnotes", "GET /creditnotes/{id}",
            "DELETE /creditnotes/{id}", "POST /creditnotes/{id}/email", "POST /creditnotes/{id}/void",
            "POST /creditnotes/{id}/credit-to-invoice"
        ],
        "features": ["line_items", "apply_to_invoice", "refunds", "templates"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "customer_payments": {
        "endpoints": [
            "POST /customerpayments", "GET /customerpayments", "PUT /customerpayments/{id}",
            "GET /customerpayments/{id}", "DELETE /customerpayments/{id}",
            "POST /customerpayments/{id}/refund"
        ],
        "features": ["invoice_allocation", "bank_account", "payment_modes", "refunds"],
        "battwheels_route": "PARTIAL - in invoices_enhanced.py"
    },
    "expenses": {
        "endpoints": [
            "POST /expenses", "GET /expenses", "PUT /expenses/{id}", "GET /expenses/{id}",
            "DELETE /expenses/{id}", "POST /expenses/{id}/add-receipt",
            "POST /expenses/{id}/delete-receipt"
        ],
        "features": ["categories", "receipts", "billable", "customer_link", "project_link"],
        "battwheels_route": "PARTIAL - basic exists"
    },
    "recurring_expenses": {
        "endpoints": [
            "POST /recurring-expenses", "GET /recurring-expenses", "PUT /recurring-expenses/{id}",
            "GET /recurring-expenses/{id}", "DELETE /recurring-expenses/{id}",
            "POST /recurring-expenses/{id}/stop", "POST /recurring-expenses/{id}/resume"
        ],
        "features": ["frequency", "auto_generation"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "retainer_invoices": {
        "endpoints": [
            "POST /retainerinvoices", "GET /retainerinvoices", "PUT /retainerinvoices/{id}",
            "GET /retainerinvoices/{id}", "DELETE /retainerinvoices/{id}",
            "POST /retainerinvoices/{id}/email"
        ],
        "features": ["advance_payments", "utilization"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "purchase_orders": {
        "endpoints": [
            "POST /purchaseorders", "GET /purchaseorders", "PUT /purchaseorders/{id}",
            "GET /purchaseorders/{id}", "DELETE /purchaseorders/{id}",
            "POST /purchaseorders/{id}/markopen", "POST /purchaseorders/{id}/markbilled",
            "POST /purchaseorders/{id}/email", "POST /purchaseorders/{id}/convert-to-bill"
        ],
        "features": ["status_workflow", "conversions", "approvals", "templates"],
        "battwheels_route": "/app/backend/routes/bills_enhanced.py"
    },
    "bills": {
        "endpoints": [
            "POST /bills", "GET /bills", "PUT /bills/{id}", "GET /bills/{id}",
            "DELETE /bills/{id}", "POST /bills/{id}/void", "POST /bills/{id}/markopen",
            "POST /bills/{id}/apply-credits", "POST /bills/{id}/payments"
        ],
        "features": ["payments", "credits", "line_items", "recurring"],
        "battwheels_route": "/app/backend/routes/bills_enhanced.py"
    },
    "recurring_bills": {
        "endpoints": [
            "POST /recurring-bills", "GET /recurring-bills", "PUT /recurring-bills/{id}",
            "GET /recurring-bills/{id}", "DELETE /recurring-bills/{id}",
            "POST /recurring-bills/{id}/stop", "POST /recurring-bills/{id}/resume"
        ],
        "features": ["frequency", "auto_generation"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "vendor_credits": {
        "endpoints": [
            "POST /vendorcredits", "GET /vendorcredits", "PUT /vendorcredits/{id}",
            "GET /vendorcredits/{id}", "DELETE /vendorcredits/{id}",
            "POST /vendorcredits/{id}/apply-credits-to-bill"
        ],
        "features": ["line_items", "apply_to_bill", "refunds"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "vendor_payments": {
        "endpoints": [
            "POST /vendorpayments", "GET /vendorpayments", "PUT /vendorpayments/{id}",
            "GET /vendorpayments/{id}", "DELETE /vendorpayments/{id}",
            "POST /vendorpayments/{id}/refund"
        ],
        "features": ["bill_allocation", "payment_modes", "refunds"],
        "battwheels_route": "PARTIAL - basic exists"
    },
    "bank_accounts": {
        "endpoints": [
            "POST /bankaccounts", "GET /bankaccounts", "PUT /bankaccounts/{id}",
            "GET /bankaccounts/{id}", "DELETE /bankaccounts/{id}"
        ],
        "features": ["account_types", "balance_tracking", "bank_feeds"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "bank_transactions": {
        "endpoints": [
            "GET /banktransactions", "POST /banktransactions", "PUT /banktransactions/{id}",
            "GET /banktransactions/{id}", "DELETE /banktransactions/{id}",
            "POST /banktransactions/{id}/categorize", "POST /banktransactions/{id}/match",
            "POST /banktransactions/{id}/exclude", "POST /banktransactions/{id}/restore"
        ],
        "features": ["categorization", "matching", "reconciliation", "rules"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "chart_of_accounts": {
        "endpoints": [
            "GET /chartofaccounts", "POST /chartofaccounts", "PUT /chartofaccounts/{id}",
            "DELETE /chartofaccounts/{id}", "POST /chartofaccounts/{id}/active",
            "POST /chartofaccounts/{id}/inactive"
        ],
        "features": ["account_types", "hierarchy", "transactions", "balance"],
        "battwheels_route": "PARTIAL - basic exists"
    },
    "journals": {
        "endpoints": [
            "POST /journals", "GET /journals", "PUT /journals/{id}",
            "GET /journals/{id}", "DELETE /journals/{id}",
            "POST /journals/{id}/status/publish"
        ],
        "features": ["debit_credit", "attachments", "publish"],
        "battwheels_route": "PARTIAL - basic exists"
    },
    "fixed_assets": {
        "endpoints": [
            "POST /fixedassets", "GET /fixedassets", "PUT /fixedassets/{id}",
            "GET /fixedassets/{id}", "DELETE /fixedassets/{id}",
            "POST /fixedassets/{id}/depreciate", "POST /fixedassets/{id}/sell",
            "POST /fixedassets/{id}/writeoff"
        ],
        "features": ["depreciation", "disposal", "types", "schedules"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "projects": {
        "endpoints": [
            "POST /projects", "GET /projects", "PUT /projects/{id}",
            "GET /projects/{id}", "DELETE /projects/{id}",
            "POST /projects/{id}/users", "GET /projects/{id}/tasks",
            "POST /projects/{id}/timeentries"
        ],
        "features": ["time_tracking", "billing", "tasks", "users"],
        "battwheels_route": "PARTIAL - basic exists"
    },
    "taxes": {
        "endpoints": [
            "GET /taxes", "POST /taxes", "PUT /taxes/{id}",
            "GET /taxes/{id}", "DELETE /taxes/{id}"
        ],
        "features": ["tax_groups", "exemptions", "gst_rates"],
        "battwheels_route": "/app/backend/routes/gst.py"
    },
    "custom_modules": {
        "endpoints": [
            "POST /custommodules", "GET /custommodules",
            "GET /custommodules/{id}/records", "POST /custommodules/{id}/records",
            "PUT /custommodules/{id}/records/{record_id}",
            "DELETE /custommodules/{id}/records/{record_id}"
        ],
        "features": ["dynamic_schemas", "relationships", "validations"],
        "battwheels_route": "MISSING - NEEDS IMPLEMENTATION"
    },
    "users": {
        "endpoints": [
            "GET /users", "POST /users/invite", "PUT /users/{id}",
            "DELETE /users/{id}", "GET /users/{id}"
        ],
        "features": ["roles", "permissions", "invitations"],
        "battwheels_route": "/app/backend/server.py"
    },
    "organizations": {
        "endpoints": [
            "GET /organizations", "PUT /organizations/{id}"
        ],
        "features": ["settings", "preferences", "currencies"],
        "battwheels_route": "PARTIAL"
    },
    "reports": {
        "endpoints": [
            "GET /reports/profitandloss", "GET /reports/balancesheet",
            "GET /reports/araging", "GET /reports/apaging",
            "GET /reports/salesbycustomer", "GET /reports/purchasesbyvendor",
            "GET /reports/inventorysummary", "GET /reports/gstr1", "GET /reports/gstr3b",
            "GET /reports/cashflow", "GET /reports/trialbalance"
        ],
        "features": ["date_ranges", "filters", "exports", "charts"],
        "battwheels_route": "/app/backend/routes/reports_advanced.py"
    }
}

def audit_battwheels():
    """Audit Battwheels OS against Zoho Books requirements"""
    results = {
        "implemented": [],
        "partial": [],
        "missing": [],
        "total_modules": len(ZOHO_BOOKS_MODULES),
        "gaps": []
    }
    
    for module, spec in ZOHO_BOOKS_MODULES.items():
        route_file = spec.get("battwheels_route", "")
        
        if "MISSING" in route_file:
            results["missing"].append({
                "module": module,
                "endpoints_needed": len(spec["endpoints"]),
                "features_needed": spec["features"]
            })
            results["gaps"].append(f"Module '{module}' not implemented - {len(spec['endpoints'])} endpoints needed")
        elif "PARTIAL" in route_file:
            results["partial"].append({
                "module": module,
                "route": route_file.replace("PARTIAL - ", ""),
                "missing_features": []
            })
        else:
            results["implemented"].append({
                "module": module,
                "route": route_file
            })
    
    return results

if __name__ == "__main__":
    results = audit_battwheels()
    
    print("\n" + "="*70)
    print("📊 ZOHO BOOKS API v3 - BATTWHEELS OS GAP ANALYSIS")
    print("="*70)
    
    print(f"\n✅ IMPLEMENTED: {len(results['implemented'])} modules")
    for m in results['implemented']:
        print(f"   - {m['module']}")
    
    print(f"\n⚠️  PARTIAL: {len(results['partial'])} modules")
    for m in results['partial']:
        print(f"   - {m['module']} ({m['route']})")
    
    print(f"\n❌ MISSING: {len(results['missing'])} modules")
    for m in results['missing']:
        print(f"   - {m['module']}: {m['endpoints_needed']} endpoints, features: {', '.join(m['features_needed'][:3])}...")
    
    print(f"\n📋 IMPLEMENTATION PRIORITY:")
    priority_order = [
        "credit_notes",
        "vendor_credits", 
        "bank_accounts",
        "bank_transactions",
        "fixed_assets",
        "recurring_expenses",
        "recurring_bills",
        "retainer_invoices",
        "custom_modules"
    ]
    
    for i, module in enumerate(priority_order, 1):
        if module in [m['module'] for m in results['missing']]:
            spec = ZOHO_BOOKS_MODULES[module]
            print(f"   P{i}: {module} - {len(spec['endpoints'])} endpoints")
    
    # Save results
    with open('/app/test_reports/zoho_migration_audit.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Full audit saved to: /app/test_reports/zoho_migration_audit.json")
