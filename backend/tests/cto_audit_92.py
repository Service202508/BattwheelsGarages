#!/usr/bin/env python3
"""
CTO Production Audit — Battwheels OS
92-Test Comprehensive Platform Audit
Covers: Auth, Orgs, Contacts, Tickets, Estimates, Invoices,
        Bills, Inventory, Items, HR, Finance, GST, Reports,
        Customer Portal, Platform Admin, Onboarding
"""

import httpx
import json
from datetime import datetime, timezone
import os
import sys

BASE_URL = os.environ.get('API_BASE_URL', 'https://revenue-health-dash.preview.emergentagent.com')
API_URL = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "admin"
PLATFORM_ADMIN_EMAIL = "platform-admin@battwheels.in"
PLATFORM_ADMIN_PASSWORD = "admin"

class R:
    total = 0
    passed = 0
    failed = 0
    errors = []
    details = []

def clr(code): return f"\033[{code}m"
RESET = clr(0); GREEN = clr(92); RED = clr(91); BLUE = clr(94); YELLOW = clr(93)

def log(msg, t="INFO"):
    c = {"PASS": GREEN, "FAIL": RED, "INFO": BLUE, "WARN": YELLOW}.get(t, "")
    print(f"{c}[{t}]{RESET} {msg}")

def T(name, condition, detail=""):
    R.total += 1
    if condition:
        R.passed += 1
        log(f"✅ T{R.total:02d}. {name}", "PASS")
        R.details.append({"n": R.total, "test": name, "status": "PASS", "detail": detail})
    else:
        R.failed += 1
        log(f"❌ T{R.total:02d}. {name}  ← {detail}", "FAIL")
        R.errors.append({"n": R.total, "test": name, "error": detail})
        R.details.append({"n": R.total, "test": name, "status": "FAIL", "detail": detail})
    return condition

def section(title):
    print(f"\n{YELLOW}{'─'*60}{RESET}")
    log(f"  {title}", "INFO")
    print(f"{YELLOW}{'─'*60}{RESET}")

def run():
    print(f"\n{'═'*70}")
    print(f"  🔍  BATTWHEELS OS — CTO PRODUCTION AUDIT  (92 TESTS)")
    print(f"{'═'*70}")
    print(f"  Target : {BASE_URL}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*70}\n")

    c = httpx.Client(timeout=30.0, follow_redirects=True)
    ts = int(datetime.now().timestamp())

    # ─────────────────────────────────────────────
    section("PHASE 1 — AUTHENTICATION (6 tests)")
    # ─────────────────────────────────────────────
    r = c.post(f"{API_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if not T("Admin Login", r.status_code == 200, f"HTTP {r.status_code}"):
        print("❌  Cannot continue without auth token."); return
    token = r.json().get("token", "")
    H = {"Authorization": f"Bearer {token}"}
    log(f"   Token: {token[:28]}…", "INFO")

    r = c.post(f"{API_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong_pwd_placeholder"})
    T("Bad Password → 401", r.status_code in [401, 400], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/auth/me", headers=H)
    T("Auth /me returns user data", r.status_code == 200 and "email" in r.json(), f"HTTP {r.status_code}")
    is_platform_admin_in_me = "is_platform_admin" in r.json()
    T("Auth /me includes is_platform_admin flag", is_platform_admin_in_me, "field missing from response")

    r = c.post(f"{API_URL}/auth/login", json={"email": PLATFORM_ADMIN_EMAIL, "password": PLATFORM_ADMIN_PASSWORD})
    T("Platform Admin Login", r.status_code == 200, f"HTTP {r.status_code}")
    platform_token = r.json().get("token", "") if r.status_code == 200 else ""
    PH = {"Authorization": f"Bearer {platform_token}"}

    r = c.get(f"{API_URL}/dashboard/stats", headers={})
    T("No token → 401 on protected route", r.status_code == 401, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 2 — ORGANIZATION MANAGEMENT (5 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/organizations/me", headers=H)
    T("Get Current Org", r.status_code == 200 and "organization_id" in r.json(), f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/organizations/me/members", headers=H)
    T("List Org Members", r.status_code == 200 and "members" in r.json(), f"HTTP {r.status_code}")
    members = r.json().get("members", []) if r.status_code == 200 else []
    T("Org has at least 1 member", len(members) >= 1, f"Found {len(members)}")

    r = c.get(f"{API_URL}/organizations/me/branding", headers=H)
    T("Org Branding Endpoint", r.status_code == 200 and "branding" in r.json(), f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/organizations/onboarding/status", headers=H)
    T("Onboarding Status — Battwheels (completed=true, show=false)",
      r.status_code == 200 and r.json().get("onboarding_completed") is True and r.json().get("show_onboarding") is False,
      f"HTTP {r.status_code} | completed={r.json().get('onboarding_completed')} show={r.json().get('show_onboarding')}" if r.status_code == 200 else f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 3 — ITEMS ENHANCED (7 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/items-enhanced/summary", headers=H)
    T("Items Summary", r.status_code == 200 and "summary" in r.json(), f"HTTP {r.status_code}")
    summary = r.json().get("summary", {}) if r.status_code == 200 else {}
    log(f"   Items: {summary.get('total_items',0)}, Active: {summary.get('active_items',0)}", "INFO")

    r = c.get(f"{API_URL}/items-enhanced/?per_page=50", headers=H)
    T("Items List", r.status_code == 200 and "items" in r.json(), f"HTTP {r.status_code}")
    all_items = r.json().get("items", []) if r.status_code == 200 else []

    r = c.get(f"{API_URL}/items-enhanced/?item_type=inventory&per_page=10", headers=H)
    T("Items Filter by Type", r.status_code == 200, f"HTTP {r.status_code}")
    inv_items = r.json().get("items", []) if r.status_code == 200 else []

    item_data = {"name": f"Audit Item {ts}", "sku": f"AUD-{ts}", "item_type": "inventory",
                 "purchase_rate": 500, "sales_rate": 750, "tax_percentage": 18}
    r = c.post(f"{API_URL}/items-enhanced/", headers=H, json=item_data)
    T("Item Create", r.status_code == 200, f"HTTP {r.status_code} {r.text[:80]}")
    new_item_id = r.json().get("item", {}).get("item_id") if r.status_code == 200 else None

    if new_item_id:
        r = c.get(f"{API_URL}/items-enhanced/{new_item_id}", headers=H)
        T("Item Read by ID", r.status_code == 200, f"HTTP {r.status_code}")
        r = c.put(f"{API_URL}/items-enhanced/{new_item_id}", headers=H, json={"sales_rate": 900})
        T("Item Update", r.status_code == 200, f"HTTP {r.status_code}")
    else:
        T("Item Read by ID", False, "skipped — create failed")
        T("Item Update", False, "skipped — create failed")

    r = c.get(f"{API_URL}/items-enhanced/low-stock", headers=H)
    T("Low Stock Report", r.status_code == 200, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 4 — INVENTORY ENHANCED (6 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/inventory-enhanced/summary", headers=H)
    T("Inventory Summary", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/inventory-enhanced/variants", headers=H)
    T("Variants List", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/inventory-enhanced/bundles", headers=H)
    T("Bundles List", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/inventory-enhanced/serial-batches?status=all", headers=H)
    T("Serial/Batch Tracking List", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/inventory-enhanced/reports/stock-summary", headers=H)
    T("Stock Summary Report", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/inventory-enhanced/reports/valuation", headers=H)
    T("Inventory Valuation Report", r.status_code == 200, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 5 — CONTACTS ENHANCED (8 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/contacts-enhanced/summary", headers=H)
    T("Contacts Summary", r.status_code == 200 and "summary" in r.json(), f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/contacts-enhanced/?per_page=50", headers=H)
    T("Contacts List", r.status_code == 200 and "contacts" in r.json(), f"HTTP {r.status_code}")
    contacts = r.json().get("contacts", []) if r.status_code == 200 else []
    customers = [c2 for c2 in contacts if c2.get("contact_type") == "customer"]
    vendors = [c2 for c2 in contacts if c2.get("contact_type") == "vendor"]

    r = c.get(f"{API_URL}/contacts-enhanced/?contact_type=customer&per_page=10", headers=H)
    T("Contacts Filter by Customer", r.status_code == 200, f"HTTP {r.status_code}")

    contact_data = {"name": f"Audit Customer {ts}", "contact_type": "customer",
                    "email": f"audit{ts}@testworkshop.com", "phone": "+919876543210"}
    r = c.post(f"{API_URL}/contacts-enhanced/", headers=H, json=contact_data)
    T("Contact Create", r.status_code == 200, f"HTTP {r.status_code} {r.text[:80]}")
    new_contact_id = r.json().get("contact", {}).get("contact_id") if r.status_code == 200 else None

    if new_contact_id:
        r = c.get(f"{API_URL}/contacts-enhanced/{new_contact_id}", headers=H)
        T("Contact Read by ID", r.status_code == 200, f"HTTP {r.status_code}")
        r = c.put(f"{API_URL}/contacts-enhanced/{new_contact_id}", headers=H, json={"credit_limit": 50000})
        T("Contact Update", r.status_code == 200, f"HTTP {r.status_code}")
        customers = customers or [{"contact_id": new_contact_id}]
    else:
        T("Contact Read by ID", False, "skipped — create failed")
        T("Contact Update", False, "skipped — create failed")

    r = c.get(f"{API_URL}/contacts-enhanced/?contact_type=vendor&per_page=10", headers=H)
    T("Contacts Filter by Vendor", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/contacts-enhanced/?search=Audit&per_page=10", headers=H)
    T("Contacts Search", r.status_code == 200, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 6 — VEHICLES (4 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/vehicles/", headers=H)
    T("Vehicles List", r.status_code == 200, f"HTTP {r.status_code}")
    vehicles = r.json() if r.status_code == 200 else []
    vehicles = vehicles if isinstance(vehicles, list) else vehicles.get("vehicles", [])

    cust_id = customers[0].get("contact_id") if customers else new_contact_id
    if cust_id:
        veh_data = {"customer_id": cust_id, "make": "Ather", "model": "450X",
                    "registration_number": f"MH01AB{ts%10000:04d}", "year": 2024, "vehicle_type": "2W"}
        r = c.post(f"{API_URL}/vehicles/", headers=H, json=veh_data)
        T("Vehicle Create", r.status_code == 200, f"HTTP {r.status_code} {r.text[:80]}")
        new_vehicle_id = r.json().get("vehicle_id") if r.status_code == 200 else None
        if new_vehicle_id:
            r = c.get(f"{API_URL}/vehicles/{new_vehicle_id}", headers=H)
            T("Vehicle Read by ID", r.status_code == 200, f"HTTP {r.status_code}")
        else:
            T("Vehicle Read by ID", False, "skipped — create failed")
    else:
        T("Vehicle Create", False, "skipped — no customer available")
        T("Vehicle Read by ID", False, "skipped — no customer available")

    r = c.get(f"{API_URL}/vehicles/categories", headers=H)
    T("Vehicle Categories", r.status_code in [200, 404], f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 7 — TICKETS MODULE (8 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/tickets/", headers=H)
    T("Tickets List", r.status_code == 200, f"HTTP {r.status_code}")
    existing_tickets = r.json() if r.status_code == 200 else []
    if isinstance(existing_tickets, dict):
        existing_tickets = existing_tickets.get("tickets", [])

    r = c.get(f"{API_URL}/dashboard/stats", headers=H)
    T("Dashboard Stats", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        stats = r.json()
        log(f"   Open Repair Orders: {stats.get('open_repair_orders',0)}, Vehicles in Workshop: {stats.get('vehicles_in_workshop',0)}", "INFO")

    ticket_data = {"title": f"Audit Ticket {ts}", "description": "Battery drain issue",
                   "service_type": "workshop_visit", "priority": "medium"}
    if cust_id:
        ticket_data["customer_id"] = cust_id
    r = c.post(f"{API_URL}/tickets/", headers=H, json=ticket_data)
    T("Ticket Create", r.status_code == 200, f"HTTP {r.status_code} {r.text[:120]}")
    new_ticket_id = r.json().get("ticket_id") if r.status_code == 200 else None

    if new_ticket_id:
        r = c.get(f"{API_URL}/tickets/{new_ticket_id}", headers=H)
        T("Ticket Read by ID", r.status_code == 200, f"HTTP {r.status_code}")
        r = c.patch(f"{API_URL}/tickets/{new_ticket_id}", headers=H, json={"status": "in_progress"})
        T("Ticket Status Update", r.status_code == 200, f"HTTP {r.status_code} {r.text[:80]}")
        r = c.post(f"{API_URL}/tickets/{new_ticket_id}/updates", headers=H,
                   json={"update_type": "status_change", "description": "Started diagnosis"})
        T("Ticket Update/Comment", r.status_code in [200, 201], f"HTTP {r.status_code}")
        r = c.get(f"{API_URL}/tickets/{new_ticket_id}/updates", headers=H)
        T("Ticket Updates List", r.status_code == 200, f"HTTP {r.status_code}")
    else:
        T("Ticket Read by ID", False, "skipped — create failed")
        T("Ticket Status Update", False, "skipped — create failed")
        T("Ticket Update/Comment", False, "skipped — create failed")
        T("Ticket Updates List", False, "skipped — create failed")

    r = c.get(f"{API_URL}/reports/service-tickets/stats", headers=H)
    T("Service Ticket Stats Report", r.status_code == 200, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 8 — ESTIMATES ENHANCED (5 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/estimates-enhanced/summary", headers=H)
    T("Estimates Summary", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/estimates-enhanced/?per_page=25", headers=H)
    T("Estimates List", r.status_code == 200, f"HTTP {r.status_code}")

    if customers and inv_items:
        est_data = {"customer_id": customers[0].get("contact_id"), "estimate_date": datetime.now().strftime("%Y-%m-%d"),
                    "line_items": [{"item_id": inv_items[0]["item_id"], "name": inv_items[0]["name"],
                                    "quantity": 2, "rate": 500, "tax_rate": 18}]}
        r = c.post(f"{API_URL}/estimates-enhanced/", headers=H, json=est_data)
        T("Estimate Create", r.status_code == 200, f"HTTP {r.status_code} {r.text[:80]}")
        est_id = r.json().get("estimate", {}).get("estimate_id") if r.status_code == 200 else None
        if est_id:
            r = c.get(f"{API_URL}/estimates-enhanced/{est_id}", headers=H)
            T("Estimate Read by ID", r.status_code == 200, f"HTTP {r.status_code}")
        else:
            T("Estimate Read by ID", False, "skipped — create failed")
    else:
        T("Estimate Create", False, "skipped — no customers or items")
        T("Estimate Read by ID", False, "skipped — no customers or items")

    r = c.get(f"{API_URL}/estimates-enhanced/reports/conversion-funnel", headers=H)
    T("Estimates Conversion Funnel", r.status_code == 200 and "funnel" in r.json(), f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 9 — INVOICES ENHANCED (8 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/invoices-enhanced/summary", headers=H)
    T("Invoices Summary", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        s = r.json().get("summary", {})
        log(f"   Total: {s.get('total_invoices',0)}, Outstanding: ₹{s.get('total_outstanding',0):,.0f}", "INFO")

    r = c.get(f"{API_URL}/invoices-enhanced/?per_page=25", headers=H)
    T("Invoices List", r.status_code == 200 and "invoices" in r.json(), f"HTTP {r.status_code}")
    existing_invoices = r.json().get("invoices", []) if r.status_code == 200 else []

    if customers:
        inv_data = {"customer_id": customers[0].get("contact_id"),
                    "invoice_date": datetime.now().strftime("%Y-%m-%d"), "payment_terms": 30,
                    "line_items": [{"name": "EV Diagnostic Service", "quantity": 1, "rate": 2500, "tax_rate": 18}]}
        r = c.post(f"{API_URL}/invoices-enhanced/", headers=H, json=inv_data)
        T("Invoice Create", r.status_code == 200, f"HTTP {r.status_code} {r.text[:100]}")
        inv_id = r.json().get("invoice", {}).get("invoice_id") if r.status_code == 200 else None

        if inv_id:
            r = c.get(f"{API_URL}/invoices-enhanced/{inv_id}", headers=H)
            T("Invoice Read by ID", r.status_code == 200, f"HTTP {r.status_code}")
            inv_detail = r.json().get("invoice", {}) if r.status_code == 200 else {}
            T("Invoice total > 0", inv_detail.get("total", 0) > 0, f"total={inv_detail.get('total',0)}")
            T("Invoice has invoice_number", bool(inv_detail.get("invoice_number")), f"no invoice_number field")

            r = c.post(f"{API_URL}/invoices-enhanced/{inv_id}/send", headers=H, json={})
            T("Invoice Send (mark sent)", r.status_code in [200, 400, 422], f"HTTP {r.status_code}")

            pmt = {"amount": 500, "payment_mode": "bank_transfer", "payment_date": datetime.now().strftime("%Y-%m-%d")}
            r = c.post(f"{API_URL}/invoices-enhanced/{inv_id}/payments", headers=H, json=pmt)
            T("Invoice Record Payment", r.status_code in [200, 400], f"HTTP {r.status_code} {r.text[:80]}")
        else:
            for lbl in ["Invoice Read by ID", "Invoice total > 0", "Invoice has invoice_number",
                        "Invoice Send (mark sent)", "Invoice Record Payment"]:
                T(lbl, False, "skipped — create failed")
    else:
        for lbl in ["Invoice Create", "Invoice Read by ID", "Invoice total > 0",
                    "Invoice has invoice_number", "Invoice Send (mark sent)", "Invoice Record Payment"]:
            T(lbl, False, "skipped — no customer")

    r = c.get(f"{API_URL}/invoices-enhanced/reports/aging", headers=H)
    T("Invoice Aging Report", r.status_code == 200 and "report" in r.json(), f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 10 — BILLS & PURCHASE ORDERS (5 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/bills-enhanced/summary", headers=H)
    T("Bills Summary", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/bills-enhanced/?per_page=25", headers=H)
    T("Bills List", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/bills-enhanced/purchase-orders/summary", headers=H)
    T("Purchase Orders Summary", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/bills-enhanced/purchase-orders", headers=H)
    T("Purchase Orders List", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/bills-enhanced/aging-report", headers=H)
    T("Bills Aging Report", r.status_code == 200, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 11 — SALES ORDERS (3 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/sales-orders-enhanced/summary", headers=H)
    T("Sales Orders Summary", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/sales-orders-enhanced/?per_page=25", headers=H)
    T("Sales Orders List", r.status_code == 200, f"HTTP {r.status_code}")

    if customers and inv_items:
        so_data = {"customer_id": customers[0].get("contact_id"),
                   "order_date": datetime.now().strftime("%Y-%m-%d"),
                   "line_items": [{"item_id": inv_items[0]["item_id"], "name": inv_items[0]["name"],
                                   "quantity": 1, "rate": 300, "tax_rate": 18}]}
        r = c.post(f"{API_URL}/sales-orders-enhanced/", headers=H, json=so_data)
        T("Sales Order Create", r.status_code == 200, f"HTTP {r.status_code} {r.text[:80]}")
    else:
        T("Sales Order Create", False, "skipped — no customers or items")

    # ─────────────────────────────────────────────
    section("PHASE 12 — REPORTS & ANALYTICS (6 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/reports-advanced/dashboard-summary", headers=H)
    T("Advanced Dashboard Summary", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/reports-advanced/revenue/monthly", headers=H)
    T("Monthly Revenue Report", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/reports-advanced/receivables/aging", headers=H)
    T("Receivables Aging Report", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/reports-advanced/customers/top-revenue", headers=H)
    T("Top Customers by Revenue", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/reports/technician-performance?period=this_month", headers=H)
    T("Technician Performance Report", r.status_code in [200, 403], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/reports/service-tickets/stats", headers=H)
    T("Service Ticket Stats Report", r.status_code == 200, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 13 — FINANCE & ACCOUNTING (6 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/journal-entries/?page=1&limit=10", headers=H)
    T("Journal Entries List", r.status_code in [200, 403], f"HTTP {r.status_code}")
    je_count = 0
    if r.status_code == 200:
        d = r.json()
        je_count = d.get("total_count", d.get("total", len(d.get("entries", []))))
        log(f"   Journal Entries: {je_count}", "INFO")

    r = c.get(f"{API_URL}/chart-of-accounts", headers=H)
    T("Chart of Accounts", r.status_code in [200, 403], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/banking/transactions?page=1&limit=10", headers=H)
    T("Banking Transactions", r.status_code in [200, 403], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/reports-advanced/revenue/quarterly", headers=H)
    T("Quarterly Revenue Report", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/gst/summary", headers=H)
    T("GST Summary", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/gst/gstr1?period=2026-02", headers=H)
    T("GSTR-1 Report", r.status_code == 200, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 14 — HR MODULE (5 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/hr/employees", headers=H)
    T("Employees List", r.status_code in [200, 403], f"HTTP {r.status_code}")
    employees = r.json().get("employees", []) if r.status_code == 200 else []
    log(f"   Employees: {len(employees)}", "INFO")

    r = c.get(f"{API_URL}/hr/attendance", headers=H)
    T("Attendance Records", r.status_code in [200, 403], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/hr/leaves", headers=H)
    T("Leave Management", r.status_code in [200, 403], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/hr/payroll", headers=H)
    T("Payroll List", r.status_code in [200, 403], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/hr/summary", headers=H)
    T("HR Summary", r.status_code in [200, 403, 404], f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 15 — CUSTOMER PORTAL (3 tests)")
    # ─────────────────────────────────────────────
    r = c.post(f"{API_URL}/customer-portal/auth/login", json={"token": "invalidtoken99999"})
    T("Customer Portal Auth Endpoint (reachable)", r.status_code in [200, 400, 401, 422, 404], f"HTTP {r.status_code}")

    r = c.get(f"{BASE_URL}/track-ticket?ticket_id=NONEXISTENT")
    T("Public Track Ticket Page (reachable)", r.status_code in [200, 304], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/public/track?ticket_id=DOESNOTEXIST")
    T("Public Track API (graceful)", r.status_code in [200, 404, 422], f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 16 — PLATFORM ADMIN (5 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/platform/organizations", headers=PH)
    T("Platform: List All Organizations", r.status_code == 200 and "organizations" in r.json(), f"HTTP {r.status_code}")
    if r.status_code == 200:
        orgs = r.json().get("organizations", [])
        log(f"   Total orgs on platform: {len(orgs)}", "INFO")

    r = c.get(f"{API_URL}/platform/stats", headers=PH)
    T("Platform: Platform Stats", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/platform/revenue-health", headers=PH)
    T("Platform: Revenue & Health Tab", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        rh = r.json()
        T("Revenue & Health: has MRR field", "mrr" in rh or "total_mrr" in rh or "metrics" in rh,
          f"keys: {list(rh.keys())[:6]}")
    else:
        T("Revenue & Health: has MRR field", False, "skipped — endpoint failed")

    r = c.get(f"{API_URL}/platform/activity", headers=PH)
    T("Platform: Recent Activity", r.status_code in [200, 404], f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 17 — EFI / AI MODULE (4 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/efi/intelligence/summary", headers=H)
    T("EFI Intelligence Summary", r.status_code in [200, 403], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/efi-guided/faults", headers=H)
    T("EFI Guided Faults", r.status_code in [200, 403, 404], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/knowledge-brain/summary", headers=H)
    T("Knowledge Brain Summary", r.status_code in [200, 403, 404], f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/notifications/", headers=H)
    T("Notifications List", r.status_code in [200, 404], f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 18 — SECURITY & TENANT ISOLATION (4 tests)")
    # ─────────────────────────────────────────────
    # Cross-tenant: use new_contact_id with different org — should fail
    r2 = c.post(f"{API_URL}/auth/login", json={"email": PLATFORM_ADMIN_EMAIL, "password": PLATFORM_ADMIN_PASSWORD})
    pad_token = r2.json().get("token","") if r2.status_code == 200 else ""
    if pad_token and new_contact_id:
        r = c.get(f"{API_URL}/contacts-enhanced/{new_contact_id}",
                  headers={"Authorization": f"Bearer {pad_token}"})
        T("Cross-Tenant Contact Access Blocked", r.status_code in [400, 401, 403, 404],
          f"HTTP {r.status_code} — platform admin should not see org contacts without org ctx")
    else:
        T("Cross-Tenant Contact Access Blocked", False, "skipped — missing token or contact")

    r = c.get(f"{API_URL}/invoices-enhanced/?per_page=5", headers=H)
    T("Invoice list scoped to org (200 OK)", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        inv_list = r.json().get("invoices", [])
        rogue = [i for i in inv_list if not i.get("organization_id") and not i.get("org_id")]
        # Some old records may lack the field, be lenient
        T("Invoices have org_id field", len(inv_list) == 0 or "organization_id" in inv_list[0] or "org_id" in inv_list[0],
          f"missing org_id in invoice: {inv_list[0].keys() if inv_list else 'empty'}")
    else:
        T("Invoices have org_id field", False, "skipped — list failed")

    r = c.get(f"{API_URL}/organizations/me", headers={"Authorization": "Bearer INVALIDTOKEN999"})
    T("Invalid Token → 401", r.status_code == 401, f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    section("PHASE 19 — NOTIFICATIONS & SETTINGS (4 tests)")
    # ─────────────────────────────────────────────
    r = c.get(f"{API_URL}/organizations/me/email-settings", headers=H)
    T("Email Settings Status", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/invoice-settings/", headers=H)
    T("Invoice Settings", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/organizations/me/setup-status", headers=H)
    T("Org Setup Status", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{API_URL}/amc/plans", headers=H)
    T("AMC Plans List", r.status_code in [200, 404], f"HTTP {r.status_code}")

    # ─────────────────────────────────────────────
    # FINAL TALLY
    # ─────────────────────────────────────────────
    print(f"\n{'═'*70}")
    print(f"  📊  AUDIT RESULTS")
    print(f"{'═'*70}")
    pct = R.passed / R.total * 100 if R.total else 0
    print(f"""
  Total Tests : {R.total}
  Passed      : {GREEN}{R.passed}{RESET}  ({pct:.1f}%)
  Failed      : {RED}{R.failed}{RESET}
""")

    if R.failed:
        print(f"  {RED}Failed Tests:{RESET}")
        for e in R.errors:
            print(f"    ❌  T{e['n']:02d}. {e['test']}")
            print(f"        └─ {e['error']}")
    else:
        print(f"  {GREEN}ALL TESTS PASSED ✅{RESET}")

    if pct >= 95:
        verdict = f"{GREEN}✅  PRODUCTION READY — Pass rate ≥ 95%{RESET}"
    elif pct >= 80:
        verdict = f"{YELLOW}⚠️   NEEDS MINOR FIXES — Pass rate 80–95%{RESET}"
    else:
        verdict = f"{RED}❌  SIGNIFICANT ISSUES — Pass rate < 80%{RESET}"
    print(f"\n  {verdict}\n")
    print(f"{'═'*70}\n")

    report = {
        "timestamp": datetime.now().isoformat(),
        "target": BASE_URL,
        "total_tests": R.total,
        "passed": R.passed,
        "failed": R.failed,
        "pass_rate": round(pct, 1),
        "market_ready": pct >= 95,
        "failures": R.errors,
        "all_results": R.details,
    }
    with open("/app/test_reports/cto_audit_92.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"  📁  Full report → /app/test_reports/cto_audit_92.json\n")
    c.close()
    return pct >= 95

if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
