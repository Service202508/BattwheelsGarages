#!/usr/bin/env python3
"""
Volt Motors Comprehensive Seed Script — Structure (Part 1)
===========================================================
Creates: Organization update, Users, Contacts, Vehicles, Inventory Items.
IDEMPOTENT: Uses upsert patterns. Safe to run multiple times.
Only touches organization_id = "demo-volt-motors-001".
"""

import asyncio
import os
import sys
import uuid
import bcrypt
from datetime import datetime, timezone, timedelta

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_dev")
ORG_ID = "demo-volt-motors-001"
SEED_TAG = "seed_comprehensive_v1"
NOW = datetime.now(timezone.utc)


def iso(dt=None):
    return (dt or NOW).isoformat()


def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def uid(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:12]}"


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    counts = {}

    # ================================================================
    # SECTION A — Organization Settings
    # ================================================================
    print("[A] Updating organization settings...")
    await db.organizations.update_one(
        {"organization_id": ORG_ID},
        {"$set": {
            "name": "Volt Motors EV Service",
            "slug": "volt-motors",
            "plan": "professional",
            "plan_type": "professional",
            "status": "active",
            "is_active": True,
            "settings": {
                "gstin": "07AABCV9603R1ZX",
                "state": "Delhi",
                "state_code": "07",
                "address": "2 FIEE Complex, Okhla Industrial Estate, New Delhi - 110020",
                "city": "New Delhi",
                "pincode": "110020",
                "phone": "+91-9876543210",
                "email": "service@voltmotors.in",
                "financial_year_start": "2025-04-01",
                "currency": "INR",
            },
            "updated_at": iso(),
        }},
        upsert=True,
    )
    print("  Organization updated: Volt Motors EV Service")

    # ================================================================
    # SECTION B — Users (5 users)
    # ================================================================
    print("[B] Seeding users...")

    demo_password = os.environ.get("DEMO_USER_PASSWORD", "Demo@12345")

    USERS = [
        {
            "user_id": "user-demo-owner-001",
            "email": "demo@voltmotors.in",
            "name": "Demo Admin",
            "role": "owner",
            "password": None,  # Don't touch existing password
        },
        {
            "user_id": "user_priya_manager",
            "email": "priya@voltmotors.in",
            "name": "Priya Sharma",
            "role": "manager",
            "password": demo_password,
        },
        {
            "user_id": "user_ankit_tech",
            "email": "ankit@voltmotors.in",
            "name": "Ankit Verma",
            "role": "technician",
            "password": demo_password,
        },
        {
            "user_id": "user_ravi_tech",
            "email": "ravi@voltmotors.in",
            "name": "Ravi Kumar",
            "role": "technician",
            "password": demo_password,
        },
        {
            "user_id": "user_neha_acct",
            "email": "neha@voltmotors.in",
            "name": "Neha Gupta",
            "role": "accountant",
            "password": demo_password,
        },
    ]

    user_count = 0
    for u in USERS:
        existing = await db.users.find_one({"user_id": u["user_id"]})
        update_fields = {
            "email": u["email"],
            "name": u["name"],
            "role": u["role"],
            "is_active": True,
        }
        if u["password"] and not existing:
            update_fields["password_hash"] = hash_pw(u["password"])
        elif u["password"] and existing and not existing.get("password_hash"):
            update_fields["password_hash"] = hash_pw(u["password"])

        result = await db.users.update_one(
            {"user_id": u["user_id"]},
            {"$set": update_fields, "$setOnInsert": {"created_at": iso()}},
            upsert=True,
        )
        # Organization membership
        await db.organization_users.update_one(
            {"user_id": u["user_id"], "organization_id": ORG_ID},
            {"$set": {
                "role": u["role"],
                "status": "active",
            }, "$setOnInsert": {"created_at": iso()}},
            upsert=True,
        )
        action = "updated" if existing else "created"
        user_count += 1
        print(f"  {action}: {u['name']} ({u['role']})")

    counts["users"] = user_count

    # ================================================================
    # SECTION C — Contacts (10 customers)
    # ================================================================
    print("[C] Seeding contacts...")

    CONTACTS = [
        {
            "contact_id": "CON-rajesh-001",
            "name": "Rajesh Kumar",
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "email": "rajesh.kumar@gmail.com",
            "phone": "9876543201",
            "customer_type": "individual",
            "gst_treatment": "consumer",
            "place_of_supply": "07",
            "city": "Delhi",
        },
        {
            "contact_id": "CON-sunita-002",
            "name": "Sunita Patel",
            "first_name": "Sunita",
            "last_name": "Patel",
            "email": "sunita.patel@gmail.com",
            "phone": "9876543202",
            "customer_type": "individual",
            "gst_treatment": "consumer",
            "place_of_supply": "27",
            "city": "Mumbai",
            "portal_enabled": True,
            "portal_token": "PORTAL-SUNITA-2026",
        },
        {
            "contact_id": "CON-manoj-003",
            "name": "Manoj Tiwari",
            "first_name": "Manoj",
            "last_name": "Tiwari",
            "email": "manoj.tiwari@gmail.com",
            "phone": "9876543203",
            "customer_type": "individual",
            "gst_treatment": "consumer",
            "place_of_supply": "07",
            "city": "Delhi",
            "portal_enabled": True,
            "portal_token": "PORTAL-MANOJ-2026",
        },
        {
            "contact_id": "CON-deepak-004",
            "name": "Deepak Singh",
            "first_name": "Deepak",
            "last_name": "Singh",
            "email": "deepak.singh@gmail.com",
            "phone": "9876543204",
            "customer_type": "individual",
            "gst_treatment": "consumer",
            "place_of_supply": "09",
            "city": "Noida",
        },
        {
            "contact_id": "CON-amit-005",
            "name": "Amit Sharma",
            "first_name": "Amit",
            "last_name": "Sharma",
            "email": "amit.sharma@gmail.com",
            "phone": "9876543205",
            "customer_type": "individual",
            "gst_treatment": "consumer",
            "place_of_supply": "06",
            "city": "Gurgaon",
        },
        {
            "contact_id": "CON-devfleet-006",
            "name": "Delhi EV Fleet Pvt Ltd",
            "company_name": "Delhi EV Fleet Pvt Ltd",
            "email": "fleet@delhievfleet.in",
            "phone": "9876543206",
            "customer_type": "business",
            "gst_treatment": "registered",
            "gstin": "07AABCF1234R1Z1",
            "place_of_supply": "07",
            "city": "Delhi",
        },
        {
            "contact_id": "CON-greenride-007",
            "name": "GreenRide Logistics",
            "company_name": "GreenRide Logistics",
            "email": "ops@greenridelogistics.in",
            "phone": "9876543207",
            "customer_type": "business",
            "gst_treatment": "registered",
            "gstin": "27AABCG5678R1Z2",
            "place_of_supply": "27",
            "city": "Mumbai",
        },
        {
            "contact_id": "CON-priyaent-008",
            "name": "Priya Enterprises",
            "company_name": "Priya Enterprises",
            "email": "info@priyaenterprises.co.in",
            "phone": "9876543208",
            "customer_type": "business",
            "gst_treatment": "registered",
            "gstin": "09AABCP9012R1Z3",
            "place_of_supply": "09",
            "city": "Lucknow",
        },
        {
            "contact_id": "CON-quickcharge-009",
            "name": "Quick Charge Services",
            "first_name": "Quick Charge",
            "last_name": "Services",
            "email": "hello@quickcharge.in",
            "phone": "9876543209",
            "customer_type": "individual",
            "gst_treatment": "consumer",
            "place_of_supply": "29",
            "city": "Bangalore",
        },
        {
            "contact_id": "CON-metroev-010",
            "name": "Metro EV Solutions",
            "company_name": "Metro EV Solutions",
            "email": "support@metroev.in",
            "phone": "9876543210",
            "customer_type": "business",
            "gst_treatment": "registered",
            "gstin": "06AABCM3456R1Z4",
            "place_of_supply": "06",
            "city": "Gurgaon",
        },
    ]

    contact_count = 0
    for c in CONTACTS:
        doc = {
            "contact_id": c["contact_id"],
            "organization_id": ORG_ID,
            "contact_type": "customer",
            "name": c["name"],
            "display_name": c["name"],
            "company_name": c.get("company_name", ""),
            "first_name": c.get("first_name", ""),
            "last_name": c.get("last_name", ""),
            "email": c.get("email", ""),
            "phone": c.get("phone", ""),
            "mobile": c.get("phone", ""),
            "currency_code": "INR",
            "payment_terms": 30,
            "credit_limit": 0,
            "opening_balance": 0,
            "opening_balance_type": "credit",
            "gstin": c.get("gstin", ""),
            "pan": "",
            "place_of_supply": c.get("place_of_supply", "07"),
            "gst_treatment": c.get("gst_treatment", "consumer"),
            "tax_treatment": "business_gst" if c["customer_type"] == "business" else "non_business",
            "customer_type": c["customer_type"],
            "customer_segment": "",
            "industry": "",
            "portal_enabled": c.get("portal_enabled", False),
            "portal_token": c.get("portal_token", ""),
            "is_active": True,
            "outstanding_receivable": 0,
            "outstanding_payable": 0,
            "unused_credits": 0,
            "notes": "",
            "tags": [SEED_TAG],
            "source": "direct",
            "created_time": iso(),
            "updated_time": iso(),
            "last_activity_time": iso(),
        }

        result = await db.contacts.update_one(
            {"contact_id": c["contact_id"], "organization_id": ORG_ID},
            {"$set": doc, "$setOnInsert": {"contact_number": f"C-{contact_count + 1:04d}"}},
            upsert=True,
        )
        action = "updated" if result.matched_count > 0 else "created"
        portal_tag = " [PORTAL]" if c.get("portal_enabled") else ""
        print(f"  {action}: {c['name']} ({c['customer_type']}){portal_tag}")
        contact_count += 1

    counts["contacts"] = contact_count

    # ================================================================
    # SECTION D — Vehicles (8 vehicles)
    # ================================================================
    print("[D] Seeding vehicles...")

    VEHICLES = [
        {
            "vehicle_id": "VH-rajesh-ola-001",
            "contact_id": "CON-rajesh-001",
            "make": "Ola",
            "model": "Ola S1 Pro",
            "category": "2W",
            "year": 2024,
            "registration_number": "DL01AB1234",
        },
        {
            "vehicle_id": "VH-sunita-ather-002",
            "contact_id": "CON-sunita-002",
            "make": "Ather",
            "model": "Ather 450X",
            "category": "2W",
            "year": 2024,
            "registration_number": "MH01CD5678",
        },
        {
            "vehicle_id": "VH-manoj-tvs-003",
            "contact_id": "CON-manoj-003",
            "make": "TVS",
            "model": "TVS iQube",
            "category": "2W",
            "year": 2023,
            "registration_number": "DL02EF9012",
        },
        {
            "vehicle_id": "VH-deepak-nexon-004",
            "contact_id": "CON-deepak-004",
            "make": "Tata",
            "model": "Tata Nexon EV",
            "category": "4W",
            "year": 2024,
            "registration_number": "UP16GH3456",
        },
        {
            "vehicle_id": "VH-fleet-chetak-005",
            "contact_id": "CON-devfleet-006",
            "make": "Bajaj",
            "model": "Bajaj Chetak",
            "category": "2W",
            "year": 2024,
            "registration_number": "DL03IJ7890",
        },
        {
            "vehicle_id": "VH-fleet-chetak-006",
            "contact_id": "CON-devfleet-006",
            "make": "Bajaj",
            "model": "Bajaj Chetak",
            "category": "2W",
            "year": 2024,
            "registration_number": "DL03IJ7891",
        },
        {
            "vehicle_id": "VH-greenride-xuv-007",
            "contact_id": "CON-greenride-007",
            "make": "Mahindra",
            "model": "Mahindra XUV400",
            "category": "4W",
            "year": 2024,
            "registration_number": "MH02KL1234",
        },
        {
            "vehicle_id": "VH-amit-hero-008",
            "contact_id": "CON-amit-005",
            "make": "Hero",
            "model": "Hero Electric Optima",
            "category": "2W",
            "year": 2023,
            "registration_number": "HR01MN5678",
        },
    ]

    vehicle_count = 0
    for v in VEHICLES:
        doc = {
            "vehicle_id": v["vehicle_id"],
            "organization_id": ORG_ID,
            "contact_id": v["contact_id"],
            "make": v["make"],
            "model": v["model"],
            "category": v["category"],
            "year": v["year"],
            "registration_number": v["registration_number"],
            "vin": f"VIN{uuid.uuid4().hex[:10].upper()}",
            "color": "White",
            "odometer_km": 5000,
            "status": "active",
            "created_at": iso(),
            "updated_at": iso(),
            "_seed": SEED_TAG,
        }
        result = await db.vehicles.update_one(
            {"vehicle_id": v["vehicle_id"], "organization_id": ORG_ID},
            {"$set": doc},
            upsert=True,
        )
        action = "updated" if result.matched_count > 0 else "created"
        print(f"  {action}: {v['model']} ({v['registration_number']}) -> {v['contact_id']}")
        vehicle_count += 1

    counts["vehicles"] = vehicle_count

    # ================================================================
    # SECTION E — Inventory Items (15 items: 10 parts + 5 services)
    # ================================================================
    print("[E] Seeding inventory items...")

    PARTS = [
        {"item_id": "ITEM-bms-001", "name": "BMS Module", "sku": "BMS-001", "purchase": 3200, "sell": 4500, "stock": 10, "hsn": "85076000"},
        {"item_id": "ITEM-battery-002", "name": "Battery Cell Pack", "sku": "BAT-001", "purchase": 8500, "sell": 12000, "stock": 5, "hsn": "85076000"},
        {"item_id": "ITEM-motor-003", "name": "Motor Controller", "sku": "MOT-001", "purchase": 2800, "sell": 4200, "stock": 8, "hsn": "85044090"},
        {"item_id": "ITEM-throttle-004", "name": "Throttle Sensor", "sku": "THR-001", "purchase": 450, "sell": 750, "stock": 20, "hsn": "90318090"},
        {"item_id": "ITEM-brake-005", "name": "Brake Pad Set (EV)", "sku": "BRK-001", "purchase": 350, "sell": 650, "stock": 25, "hsn": "87083099"},
        {"item_id": "ITEM-chargeport-006", "name": "Charging Port Assembly", "sku": "CPA-001", "purchase": 1200, "sell": 1800, "stock": 12, "hsn": "85366990"},
        {"item_id": "ITEM-display-007", "name": "Display Unit", "sku": "DSP-001", "purchase": 1500, "sell": 2200, "stock": 7, "hsn": "85285900"},
        {"item_id": "ITEM-wiring-008", "name": "Wiring Harness", "sku": "WRH-001", "purchase": 800, "sell": 1200, "stock": 15, "hsn": "85441990"},
        {"item_id": "ITEM-fuse-009", "name": "Fuse Set", "sku": "FUS-001", "purchase": 120, "sell": 250, "stock": 50, "hsn": "85351000"},
        {"item_id": "ITEM-coolant-010", "name": "Coolant Pump", "sku": "CLP-001", "purchase": 950, "sell": 1500, "stock": 6, "hsn": "84138190"},
    ]

    SERVICES = [
        {"item_id": "ITEM-diag-011", "name": "Basic Diagnostic", "sku": "SVC-DIAG", "sell": 500, "sac": "998714"},
        {"item_id": "ITEM-bmsrecal-012", "name": "BMS Recalibration", "sku": "SVC-BMS", "sell": 1500, "sac": "998714"},
        {"item_id": "ITEM-motorserv-013", "name": "Motor Servicing", "sku": "SVC-MOT", "sell": 2000, "sac": "998714"},
        {"item_id": "ITEM-inspect-014", "name": "Full Vehicle Inspection", "sku": "SVC-INSP", "sell": 800, "sac": "998714"},
        {"item_id": "ITEM-swupdate-015", "name": "Software Update", "sku": "SVC-SWU", "sell": 1000, "sac": "998714"},
    ]

    item_count = 0

    for p in PARTS:
        doc = {
            "item_id": p["item_id"],
            "organization_id": ORG_ID,
            "name": p["name"],
            "sku": p["sku"],
            "description": p["name"],
            "item_type": "inventory",
            "product_type": "goods",
            "rate": p["sell"],
            "sales_rate": p["sell"],
            "purchase_rate": p["purchase"],
            "unit": "pcs",
            "usage_unit": "pcs",
            "stock_on_hand": p["stock"],
            "opening_stock": p["stock"],
            "opening_stock_value": p["stock"] * p["purchase"],
            "opening_stock_rate": p["purchase"],
            "available_stock": p["stock"],
            "committed_stock": 0,
            "reorder_level": max(3, p["stock"] // 4),
            "hsn_code": p["hsn"],
            "sac_code": "",
            "hsn_or_sac": p["hsn"],
            "taxable": True,
            "tax_preference": "taxable",
            "tax_percentage": 18,
            "intra_state_tax_rate": 18,
            "inter_state_tax_rate": 18,
            "intra_state_tax_name": "GST18",
            "inter_state_tax_name": "IGST18",
            "sellable": True,
            "purchasable": True,
            "track_inventory": True,
            "status": "active",
            "is_active": True,
            "created_time": iso(),
            "updated_time": iso(),
            "_seed": SEED_TAG,
        }
        result = await db.items.update_one(
            {"item_id": p["item_id"], "organization_id": ORG_ID},
            {"$set": doc},
            upsert=True,
        )
        action = "updated" if result.matched_count > 0 else "created"
        print(f"  {action}: {p['name']} (stock: {p['stock']}, ₹{p['purchase']}→₹{p['sell']})")
        item_count += 1

    for s in SERVICES:
        doc = {
            "item_id": s["item_id"],
            "organization_id": ORG_ID,
            "name": s["name"],
            "sku": s["sku"],
            "description": s["name"],
            "item_type": "service",
            "product_type": "service",
            "rate": s["sell"],
            "sales_rate": s["sell"],
            "purchase_rate": 0,
            "unit": "nos",
            "usage_unit": "nos",
            "stock_on_hand": 0,
            "opening_stock": 0,
            "available_stock": 0,
            "hsn_code": "",
            "sac_code": s["sac"],
            "hsn_or_sac": s["sac"],
            "taxable": True,
            "tax_preference": "taxable",
            "tax_percentage": 18,
            "intra_state_tax_rate": 18,
            "inter_state_tax_rate": 18,
            "intra_state_tax_name": "GST18",
            "inter_state_tax_name": "IGST18",
            "sellable": True,
            "purchasable": False,
            "track_inventory": False,
            "status": "active",
            "is_active": True,
            "created_time": iso(),
            "updated_time": iso(),
            "_seed": SEED_TAG,
        }
        result = await db.items.update_one(
            {"item_id": s["item_id"], "organization_id": ORG_ID},
            {"$set": doc},
            upsert=True,
        )
        action = "updated" if result.matched_count > 0 else "created"
        print(f"  {action}: {s['name']} (service, ₹{s['sell']})")
        item_count += 1

    counts["items"] = item_count

    # ================================================================
    # SECTION G — Employees
    # ================================================================
    print("[G] Seeding employees...")
    employees = [
        {"employee_id": "EMP-001", "name": "Vikram Mehta", "email": "vikram@voltmotors.in",
         "role": "technician", "department": "Service", "designation": "Senior Technician",
         "phone": "+91-9876500001", "status": "active", "date_of_joining": "2024-03-15"},
        {"employee_id": "EMP-002", "name": "Anita Reddy", "email": "anita@voltmotors.in",
         "role": "technician", "department": "Service", "designation": "EV Specialist",
         "phone": "+91-9876500002", "status": "active", "date_of_joining": "2024-06-01"},
        {"employee_id": "EMP-003", "name": "Karan Joshi", "email": "karan@voltmotors.in",
         "role": "manager", "department": "Operations", "designation": "Service Manager",
         "phone": "+91-9876500003", "status": "active", "date_of_joining": "2024-01-10"},
    ]
    emp_count = 0
    for emp in employees:
        doc = {
            **emp,
            "organization_id": ORG_ID,
            "is_active": True,
            "created_at": iso(),
            "updated_at": iso(),
            "_seed": SEED_TAG,
        }
        await db.employees.update_one(
            {"employee_id": emp["employee_id"], "organization_id": ORG_ID},
            {"$set": doc}, upsert=True,
        )
        emp_count += 1
        print(f"  {emp['name']} ({emp['role']})")
    counts["employees"] = emp_count

    # ================================================================
    # SECTION H — Invoices
    # ================================================================
    print("[H] Seeding invoices...")
    invoice_defs = [
        {"invoice_number": "INV-2026-001", "customer_id": "CON-rajesh-001", "customer_name": "Rajesh Kumar",
         "total": 8500, "status": "paid", "days_ago": 45},
        {"invoice_number": "INV-2026-002", "customer_id": "CON-sunita-002", "customer_name": "Sunita Patel",
         "total": 12200, "status": "paid", "days_ago": 30},
        {"invoice_number": "INV-2026-003", "customer_id": "CON-devfleet-006", "customer_name": "Delhi EV Fleet Pvt Ltd",
         "total": 35000, "status": "sent", "days_ago": 15},
        {"invoice_number": "INV-2026-004", "customer_id": "CON-greenride-007", "customer_name": "GreenRide Logistics",
         "total": 22750, "status": "overdue", "days_ago": 60},
        {"invoice_number": "INV-2026-005", "customer_id": "CON-manoj-003", "customer_name": "Manoj Tiwari",
         "total": 5400, "status": "draft", "days_ago": 3},
    ]
    inv_count = 0
    for inv in invoice_defs:
        inv_date = (NOW - timedelta(days=inv["days_ago"])).strftime("%Y-%m-%d")
        due_date = (NOW - timedelta(days=inv["days_ago"]) + timedelta(days=30)).strftime("%Y-%m-%d")
        balance = 0 if inv["status"] == "paid" else inv["total"]
        doc = {
            "invoice_id": uid("inv-"),
            "invoice_number": inv["invoice_number"],
            "organization_id": ORG_ID,
            "customer_id": inv["customer_id"],
            "customer_name": inv["customer_name"],
            "invoice_date": inv_date,
            "due_date": due_date,
            "sub_total": inv["total"],
            "tax_total": round(inv["total"] * 0.18, 2),
            "total": round(inv["total"] * 1.18, 2),
            "balance_due": round(balance * 1.18, 2),
            "amount_due": round(balance * 1.18, 2),
            "status": inv["status"],
            "currency_code": "INR",
            "line_items": [{"item_name": "EV Service", "quantity": 1, "rate": inv["total"], "amount": inv["total"]}],
            "created_at": iso(NOW - timedelta(days=inv["days_ago"])),
            "updated_at": iso(),
            "_seed": SEED_TAG,
        }
        await db.invoices.update_one(
            {"invoice_number": inv["invoice_number"], "organization_id": ORG_ID},
            {"$set": doc}, upsert=True,
        )
        inv_count += 1
        print(f"  {inv['invoice_number']}: {inv['customer_name']} ₹{inv['total']} ({inv['status']})")
    counts["invoices"] = inv_count

    # ================================================================
    # SECTION I — Estimates
    # ================================================================
    print("[I] Seeding estimates...")
    estimate_defs = [
        {"estimate_number": "EST-2026-001", "customer_id": "CON-amit-005", "customer_name": "Amit Sharma",
         "total": 15000, "status": "accepted", "days_ago": 20},
        {"estimate_number": "EST-2026-002", "customer_id": "CON-deepak-004", "customer_name": "Deepak Singh",
         "total": 7800, "status": "sent", "days_ago": 10},
        {"estimate_number": "EST-2026-003", "customer_id": "CON-priyaent-008", "customer_name": "Priya Enterprises",
         "total": 42000, "status": "accepted", "days_ago": 35},
        {"estimate_number": "EST-2026-004", "customer_id": "CON-quickcharge-009", "customer_name": "Quick Charge Services",
         "total": 18500, "status": "draft", "days_ago": 5},
        {"estimate_number": "EST-2026-005", "customer_id": "CON-metroev-010", "customer_name": "Metro EV Solutions",
         "total": 29000, "status": "declined", "days_ago": 40},
    ]
    est_count = 0
    for est in estimate_defs:
        est_date = (NOW - timedelta(days=est["days_ago"])).strftime("%Y-%m-%d")
        expiry_date = (NOW - timedelta(days=est["days_ago"]) + timedelta(days=30)).strftime("%Y-%m-%d")
        doc = {
            "estimate_id": uid("est-"),
            "estimate_number": est["estimate_number"],
            "organization_id": ORG_ID,
            "customer_id": est["customer_id"],
            "customer_name": est["customer_name"],
            "estimate_date": est_date,
            "expiry_date": expiry_date,
            "sub_total": est["total"],
            "tax_total": round(est["total"] * 0.18, 2),
            "total": round(est["total"] * 1.18, 2),
            "status": est["status"],
            "currency_code": "INR",
            "line_items": [{"item_name": "EV Service Estimate", "quantity": 1, "rate": est["total"], "amount": est["total"]}],
            "created_at": iso(NOW - timedelta(days=est["days_ago"])),
            "updated_at": iso(),
            "_seed": SEED_TAG,
        }
        await db.estimates.update_one(
            {"estimate_number": est["estimate_number"], "organization_id": ORG_ID},
            {"$set": doc}, upsert=True,
        )
        est_count += 1
        print(f"  {est['estimate_number']}: {est['customer_name']} ₹{est['total']} ({est['status']})")
    counts["estimates"] = est_count

    # ================================================================
    # SECTION J — Chart of Accounts
    # ================================================================
    print("[J] Seeding chart of accounts...")
    coa_templates = [
        {"account_code": "1000", "account_name": "Cash", "account_type": "asset", "sub_type": "current_asset"},
        {"account_code": "1100", "account_name": "Accounts Receivable", "account_type": "asset", "sub_type": "current_asset"},
        {"account_code": "1200", "account_name": "Inventory", "account_type": "asset", "sub_type": "current_asset"},
        {"account_code": "1300", "account_name": "Prepaid Expenses", "account_type": "asset", "sub_type": "current_asset"},
        {"account_code": "1500", "account_name": "Equipment", "account_type": "asset", "sub_type": "fixed_asset"},
        {"account_code": "2000", "account_name": "Accounts Payable", "account_type": "liability", "sub_type": "current_liability"},
        {"account_code": "2100", "account_name": "GST Payable", "account_type": "liability", "sub_type": "current_liability"},
        {"account_code": "2200", "account_name": "TDS Payable", "account_type": "liability", "sub_type": "current_liability"},
        {"account_code": "2500", "account_name": "Loans Payable", "account_type": "liability", "sub_type": "long_term_liability"},
        {"account_code": "3000", "account_name": "Owner's Equity", "account_type": "equity", "sub_type": "equity"},
        {"account_code": "3100", "account_name": "Retained Earnings", "account_type": "equity", "sub_type": "equity"},
        {"account_code": "4000", "account_name": "Service Revenue", "account_type": "income", "sub_type": "revenue"},
        {"account_code": "4100", "account_name": "Parts Sales", "account_type": "income", "sub_type": "revenue"},
        {"account_code": "4200", "account_name": "AMC Revenue", "account_type": "income", "sub_type": "revenue"},
        {"account_code": "5000", "account_name": "Cost of Goods Sold", "account_type": "expense", "sub_type": "cost_of_goods"},
        {"account_code": "5100", "account_name": "Parts & Materials", "account_type": "expense", "sub_type": "cost_of_goods"},
        {"account_code": "6000", "account_name": "Salaries & Wages", "account_type": "expense", "sub_type": "operating_expense"},
        {"account_code": "6100", "account_name": "Rent", "account_type": "expense", "sub_type": "operating_expense"},
        {"account_code": "6200", "account_name": "Utilities", "account_type": "expense", "sub_type": "operating_expense"},
        {"account_code": "6300", "account_name": "Insurance", "account_type": "expense", "sub_type": "operating_expense"},
    ]
    coa_count = 0
    for acct in coa_templates:
        doc = {
            "account_id": uid("acct-"),
            "account_code": acct["account_code"],
            "account_name": acct["account_name"],
            "account_type": acct["account_type"],
            "sub_type": acct["sub_type"],
            "organization_id": ORG_ID,
            "is_active": True,
            "balance": 0,
            "description": f"{acct['account_name']} account",
            "created_at": iso(),
            "_seed": SEED_TAG,
        }
        await db.chart_of_accounts.update_one(
            {"account_code": acct["account_code"], "organization_id": ORG_ID},
            {"$set": doc}, upsert=True,
        )
        coa_count += 1
    counts["chart_of_accounts"] = coa_count
    print(f"  {coa_count} accounts seeded")

    # ================================================================
    # SUMMARY
    # ================================================================
    print("\n" + "=" * 50)
    print("SEED COMPLETE — Summary:")
    print("=" * 50)
    for key, val in counts.items():
        print(f"  {key}: {val}")

    # Verify final counts
    print("\nDatabase counts:")
    for col_name in ["organizations", "users", "organization_users", "contacts", "vehicles", "items",
                     "employees", "invoices", "estimates", "chart_of_accounts"]:
        c = await db[col_name].count_documents({})
        org_c = await db[col_name].count_documents({"organization_id": ORG_ID}) if col_name != "users" else c
        print(f"  {col_name}: {c} total ({org_c} for demo org)")

    # Verify portal contacts
    portal_count = await db.contacts.count_documents({"organization_id": ORG_ID, "portal_enabled": True})
    print(f"\n  Portal-enabled contacts: {portal_count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
