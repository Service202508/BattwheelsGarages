"""
Battwheels OS — Demo Organisation Seeder
Creates "Volt Motors" demo org with realistic 3-month operating history.

Usage:
  python scripts/seed_demo_org.py --env development   # seed dev db
  python scripts/seed_demo_org.py --env staging       # seed staging db

NEVER run with --env production.
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import random
import uuid
import bcrypt

# ── SAFETY GUARD ──────────────────────────────────────────────────────────────
def safety_check(env: str, auto_confirm: bool = False):
    if env == "production":
        print("BLOCKED: Cannot seed demo data into production environment.")
        print("   Use --env development or --env staging only.")
        sys.exit(1)
    if not auto_confirm:
        confirm = input(f"\nAbout to seed DEMO data into {env} database.\n   Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

# ── DEMO DATA CONSTANTS ────────────────────────────────────────────────────────
DEMO_ORG_ID = "demo-volt-motors-001"
DEMO_ORG_SLUG = "volt-motors-demo"

DEMO_CUSTOMERS = [
    {"name": "Arjun Mehta", "phone": "9811234567", "email": "arjun.mehta@gmail.com", "city": "Delhi"},
    {"name": "Priya Sharma", "phone": "9823456789", "email": "priya.s@gmail.com", "city": "Gurugram"},
    {"name": "Vikram Singh", "phone": "9834567890", "email": "vikram@ymail.com", "city": "Noida"},
    {"name": "Sunita Rao", "phone": "9845678901", "email": "sunita.rao@hotmail.com", "city": "Delhi"},
    {"name": "Rohit Kapoor", "phone": "9856789012", "email": "rohit.k@gmail.com", "city": "Faridabad"},
    {"name": "Kavya Nair", "phone": "9867890123", "email": "kavya.n@gmail.com", "city": "Delhi"},
    {"name": "Sanjay Gupta", "phone": "9878901234", "email": "sanjay.g@gmail.com", "city": "Gurugram"},
    {"name": "Meera Joshi", "phone": "9889012345", "email": "meera.j@gmail.com", "city": "Delhi"},
]

DEMO_VEHICLES = [
    {"model": "Ola S1 Pro", "year": 2023, "registration": "DL01AB1234"},
    {"model": "Ather 450X", "year": 2022, "registration": "DL02CD5678"},
    {"model": "TVS iQube", "year": 2023, "registration": "HR26EF9012"},
    {"model": "Tata Nexon EV", "year": 2022, "registration": "DL03GH3456"},
    {"model": "Ola S1 Air", "year": 2023, "registration": "UP16IJ7890"},
    {"model": "Ather 450S", "year": 2023, "registration": "DL04KL1234"},
    {"model": "Bajaj Chetak", "year": 2022, "registration": "HR51MN5678"},
    {"model": "Tata Tigor EV", "year": 2021, "registration": "DL05OP9012"},
]

DEMO_COMPLAINTS = [
    {"complaint": "Battery not charging, stuck at 45%", "fault": "BMS calibration drift", "resolution": "BMS recalibrated, charging restored to 100%"},
    {"complaint": "Range reduced — only 35km per charge", "fault": "Battery cell degradation (2 cells)", "resolution": "Cell balancing performed, range restored to 82km"},
    {"complaint": "Motor noise at speeds above 40kmph", "fault": "Motor bearing wear", "resolution": "Bearing replaced, noise eliminated"},
    {"complaint": "Regenerative braking not working", "fault": "Regen controller fault", "resolution": "Regen controller firmware updated"},
    {"complaint": "Display showing error code E07", "fault": "BMS communication fault", "resolution": "BMS harness connector reseated, error cleared"},
    {"complaint": "Scooter won't start, no response", "fault": "Main fuse blown", "resolution": "Fuse replaced, root cause: short in accessory port"},
    {"complaint": "Brake feel spongy, poor stopping", "fault": "Brake fluid contamination", "resolution": "Brake fluid flushed, pads inspected and replaced"},
    {"complaint": "Throttle lag and jerky acceleration", "fault": "Motor controller thermal throttling", "resolution": "Cooling vent cleaned, throttle response restored"},
    {"complaint": "Battery draining overnight (10% loss)", "fault": "Parasitic drain from GPS module", "resolution": "GPS module replaced, overnight drain < 1%"},
    {"complaint": "Charging port damaged, won't connect", "fault": "Charging port pin bent", "resolution": "Charging port assembly replaced"},
]

DEMO_INVENTORY_ITEMS = [
    {"name": "BMS Module — Ola Gen2", "sku": "BMS-OLA-002", "purchase_rate": 2800, "selling_rate": 3800, "stock": 8, "reorder": 2},
    {"name": "Motor Bearing Set", "sku": "BRG-MOT-001", "purchase_rate": 380, "selling_rate": 650, "stock": 15, "reorder": 4},
    {"name": "Brake Pad Set — 2W", "sku": "BRK-2W-001", "purchase_rate": 420, "selling_rate": 680, "stock": 22, "reorder": 5},
    {"name": "Charging Port Assembly", "sku": "CHG-PORT-001", "purchase_rate": 1200, "selling_rate": 1800, "stock": 6, "reorder": 2},
    {"name": "Main Fuse 30A", "sku": "FUSE-30A-001", "purchase_rate": 45, "selling_rate": 120, "stock": 50, "reorder": 10},
    {"name": "BMS Harness Connector", "sku": "BMS-HRN-001", "purchase_rate": 280, "selling_rate": 450, "stock": 12, "reorder": 3},
    {"name": "Motor Controller — Ather", "sku": "MCT-ATH-001", "purchase_rate": 9500, "selling_rate": 13500, "stock": 3, "reorder": 1},
    {"name": "GPS Module Replacement", "sku": "GPS-MOD-001", "purchase_rate": 850, "selling_rate": 1400, "stock": 5, "reorder": 2},
    {"name": "Brake Fluid DOT4 500ml", "sku": "BRK-FLD-001", "purchase_rate": 180, "selling_rate": 320, "stock": 18, "reorder": 5},
    {"name": "Throttle Sensor", "sku": "THR-SEN-001", "purchase_rate": 620, "selling_rate": 980, "stock": 9, "reorder": 2},
]

DEMO_EMPLOYEES = [
    {"name": "Ravi Kumar", "role": "Lead Technician", "salary": 28000, "pf": True, "esi": False},
    {"name": "Mohan Singh", "role": "Technician", "salary": 18000, "pf": True, "esi": True},
    {"name": "Deepa Verma", "role": "Service Advisor", "salary": 22000, "pf": True, "esi": False},
]


async def seed_demo(db):
    print(f"\nSeeding demo org: {DEMO_ORG_SLUG}")

    # ── ORGANISATION ──────────────────────────────────────────────────────────
    await db.organizations.delete_one({"organization_id": DEMO_ORG_ID})
    await db.organizations.insert_one({
        "organization_id": DEMO_ORG_ID,
        "name": "Volt Motors",
        "slug": DEMO_ORG_SLUG,
        "is_active": True,
        "is_demo": True,
        "city": "Delhi",
        "state": "Delhi",
        "gstin": "07AABCV9603R1ZX",
        "address": "Shop 14, Sector 18 Market, Noida, Delhi NCR",
        "phone": "9800000001",
        "email": "demo@voltmotors.in",
        "plan": "professional",
        "trial_end": None,
        "created_at": datetime.utcnow() - timedelta(days=90),
    })
    print("  Organisation created: Volt Motors")

    # ── DEMO ADMIN USER ───────────────────────────────────────────────────────
    hashed = bcrypt.hashpw(b"Demo@12345", bcrypt.gensalt()).decode()
    await db.users.delete_many({"organization_id": DEMO_ORG_ID})
    await db.users.insert_one({
        "user_id": "user-demo-owner-001",
        "organization_id": DEMO_ORG_ID,
        "name": "Demo Admin",
        "email": "demo@voltmotors.in",
        "password": hashed,
        "role": "owner",
        "is_active": True,
        "created_at": datetime.utcnow() - timedelta(days=90),
    })
    print("  Demo user: demo@voltmotors.in / Demo@12345")

    # ── PURGE OLD DEMO DATA ───────────────────────────────────────────────────
    for col in ["tickets", "invoices", "contacts", "vehicles", "inventory",
                "journal_entries", "accounts", "employees", "payroll_runs",
                "efi_failures", "estimates", "estimates_enhanced", "ticket_estimates",
                "ticket_payments", "ticket_activities", "bills", "expenses"]:
        await db[col].delete_many({"organization_id": DEMO_ORG_ID})

    # ── CHART OF ACCOUNTS ─────────────────────────────────────────────────────
    accounts = [
        {"code": "1001", "name": "Cash", "type": "Asset", "balance": 87450},
        {"code": "1100", "name": "Accounts Receivable", "type": "Asset", "balance": 12800},
        {"code": "1200", "name": "Inventory Asset", "type": "Asset", "balance": 68240},
        {"code": "2001", "name": "Accounts Payable", "type": "Liability", "balance": 18500},
        {"code": "2100", "name": "GST Payable", "type": "Liability", "balance": 9840},
        {"code": "3001", "name": "Owner Equity", "type": "Equity", "balance": 140150},
        {"code": "4001", "name": "Service Revenue", "type": "Revenue", "balance": 284600},
        {"code": "5001", "name": "Cost of Goods Sold", "type": "Expense", "balance": 118420},
        {"code": "5100", "name": "Salary Expense", "type": "Expense", "balance": 68000},
        {"code": "5200", "name": "Rent Expense", "type": "Expense", "balance": 24000},
        {"code": "5300", "name": "Utilities", "type": "Expense", "balance": 8400},
    ]
    for acc in accounts:
        acc["organization_id"] = DEMO_ORG_ID
        acc["account_id"] = f"acc-{DEMO_ORG_ID}-{acc['code']}"
        acc["created_at"] = datetime.utcnow() - timedelta(days=90)
    await db.accounts.insert_many(accounts)
    print("  Chart of accounts seeded (11 accounts)")

    # ── CUSTOMERS ─────────────────────────────────────────────────────────────
    customer_ids = []
    for i, c in enumerate(DEMO_CUSTOMERS):
        cid = f"cust-demo-{i+1:03d}"
        customer_ids.append(cid)
        await db.contacts.insert_one({
            "contact_id": cid,
            "organization_id": DEMO_ORG_ID,
            "name": c["name"],
            "phone": c["phone"],
            "email": c["email"],
            "city": c["city"],
            "type": "customer",
            "total_visits": random.randint(1, 5),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(10, 85)),
        })
    print(f"  {len(DEMO_CUSTOMERS)} customers created")

    # ── VEHICLES ──────────────────────────────────────────────────────────────
    vehicle_ids = []
    for i, v in enumerate(DEMO_VEHICLES):
        vid = f"veh-demo-{i+1:03d}"
        vehicle_ids.append(vid)
        await db.vehicles.insert_one({
            "vehicle_id": vid,
            "organization_id": DEMO_ORG_ID,
            "contact_id": customer_ids[i],
            "model": v["model"],
            "year": v["year"],
            "registration": v["registration"],
            "odometer_km": random.randint(2000, 22000),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(10, 85)),
        })
    print(f"  {len(DEMO_VEHICLES)} vehicles created")

    # ── INVENTORY ─────────────────────────────────────────────────────────────
    for item in DEMO_INVENTORY_ITEMS:
        iid = f"inv-demo-{item['sku']}"
        await db.inventory.insert_one({
            "item_id": iid,
            "organization_id": DEMO_ORG_ID,
            "name": item["name"],
            "sku": item["sku"],
            "purchase_rate": item["purchase_rate"],
            "selling_rate": item["selling_rate"],
            "stock": item["stock"],
            "reorder_level": item["reorder"],
            "created_at": datetime.utcnow() - timedelta(days=80),
        })
    print(f"  {len(DEMO_INVENTORY_ITEMS)} inventory items created")

    # ── EMPLOYEES ─────────────────────────────────────────────────────────────
    for i, emp in enumerate(DEMO_EMPLOYEES):
        await db.employees.insert_one({
            "employee_id": f"emp-demo-{i+1:03d}",
            "organization_id": DEMO_ORG_ID,
            "name": emp["name"],
            "role": emp["role"],
            "basic_salary": emp["salary"],
            "pf_eligible": emp["pf"],
            "esi_eligible": emp["esi"],
            "state": "Delhi",
            "status": "active",
            "join_date": (datetime.utcnow() - timedelta(days=85)).strftime("%Y-%m-%d"),
            "pan": f"ABCDE{1000+i}F",
            "created_at": datetime.utcnow() - timedelta(days=85),
        })
    print(f"  {len(DEMO_EMPLOYEES)} employees created")

    # ── TICKETS (mix of statuses across 3 months) ─────────────────────────────
    statuses = ["resolved"] * 8 + ["in_progress"] * 2 + ["open"] * 4
    invoice_num = 1

    for i, status in enumerate(statuses):
        tkt_id = f"tkt-demo-{uuid.uuid4().hex[:12]}"
        complaint = DEMO_COMPLAINTS[i % len(DEMO_COMPLAINTS)]
        days_ago = random.randint(1, 85)
        cust_idx = i % len(customer_ids)
        veh_idx = i % len(vehicle_ids)
        part = DEMO_INVENTORY_ITEMS[i % len(DEMO_INVENTORY_ITEMS)]
        labour_amount = random.choice([850, 1200, 1500, 2000, 2500])
        part_amount = part["selling_rate"]
        subtotal = part_amount + labour_amount
        gst = round(subtotal * 0.18, 2)
        total = round(subtotal + gst, 2)

        await db.tickets.insert_one({
            "ticket_id": tkt_id,
            "organization_id": DEMO_ORG_ID,
            "contact_id": customer_ids[cust_idx],
            "vehicle_id": vehicle_ids[veh_idx],
            "customer_name": DEMO_CUSTOMERS[cust_idx]["name"],
            "vehicle_model": DEMO_VEHICLES[veh_idx]["model"],
            "vehicle_registration": DEMO_VEHICLES[veh_idx]["registration"],
            "complaint": complaint["complaint"],
            "resolution": complaint["resolution"] if status == "resolved" else None,
            "status": status,
            "priority": random.choice(["high", "medium", "normal"]),
            "assigned_to": DEMO_EMPLOYEES[i % len(DEMO_EMPLOYEES)]["name"],
            "parts_used": [{"item_id": f"inv-demo-{part['sku']}", "name": part["name"], "qty": 1, "rate": part["selling_rate"]}],
            "labour": [{"description": "Diagnostic + Repair Labour", "hours": labour_amount / 500, "rate": 500, "amount": labour_amount}],
            "subtotal": subtotal,
            "gst_amount": gst,
            "total_amount": total,
            "created_at": datetime.utcnow() - timedelta(days=days_ago),
            "resolved_at": (datetime.utcnow() - timedelta(days=days_ago - 1)) if status == "resolved" else None,
            "efi_used": random.choice([True, False]),
            "efi_fault": complaint["fault"] if random.random() > 0.4 else None,
            "efi_confidence": round(random.uniform(0.72, 0.94), 2) if random.random() > 0.4 else None,
        })

        # Create paid invoice for resolved tickets
        if status == "resolved":
            inv_id = f"INV-DEMO-{invoice_num:05d}"
            invoice_num += 1
            await db.invoices.insert_one({
                "invoice_id": inv_id,
                "invoice_number": inv_id,
                "organization_id": DEMO_ORG_ID,
                "ticket_id": tkt_id,
                "contact_id": customer_ids[cust_idx],
                "customer_name": DEMO_CUSTOMERS[cust_idx]["name"],
                "line_items": [
                    {"description": part["name"], "qty": 1, "rate": part["selling_rate"], "amount": part["selling_rate"], "tax_rate": 18},
                    {"description": "Labour", "qty": 1, "rate": labour_amount, "amount": labour_amount, "tax_rate": 18},
                ],
                "subtotal": subtotal,
                "cgst": round(gst / 2, 2),
                "sgst": round(gst / 2, 2),
                "igst": 0,
                "total_amount": total,
                "status": "paid",
                "payment_method": random.choice(["cash", "upi", "card"]),
                "created_at": datetime.utcnow() - timedelta(days=days_ago),
                "paid_at": datetime.utcnow() - timedelta(days=days_ago - 1),
            })

    print(f"  14 tickets created (8 resolved, 2 in_progress, 4 open)")
    print(f"  8 paid invoices created")

    # ── PAYROLL RUNS (2 months) ───────────────────────────────────────────────
    for month_offset in [2, 1]:
        month_date = datetime.utcnow() - timedelta(days=30 * month_offset)
        await db.payroll_runs.insert_one({
            "run_id": f"payroll-demo-{month_offset}",
            "organization_id": DEMO_ORG_ID,
            "period": month_date.strftime("%B %Y"),
            "total_gross": 68000,
            "total_net": 60840,
            "total_pf_employee": 5520,
            "total_esi_employee": 135,
            "total_pt": 400,
            "status": "processed",
            "processed_at": month_date,
        })
    print("  2 payroll runs created")

    print(f"""
{'='*58}
  DEMO ORG SEEDED SUCCESSFULLY
{'='*58}
  Org:        Volt Motors
  Slug:       volt-motors-demo
  Login:      demo@voltmotors.in
  Password:   Demo@12345
{'='*58}
  Data seeded:
    8 customers + 8 vehicles
   10 inventory items
   14 tickets (8 resolved, 2 WIP, 4 open)
    8 paid invoices
   11 chart of accounts
    3 employees
    2 payroll runs
{'='*58}
""")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True, choices=["development", "staging"],
                        help="Target environment. NEVER production.")
    parser.add_argument("--yes", action="store_true",
                        help="Skip confirmation prompt (for CI/scripts).")
    args = parser.parse_args()

    safety_check(args.env, auto_confirm=args.yes)

    url = os.environ.get("MONGO_URL")
    if not url:
        print("ERROR: MONGO_URL environment variable not set.")
        sys.exit(1)

    client = AsyncIOMotorClient(url)

    # Use correct DB for environment
    db_name = "battwheels_dev" if args.env == "development" else "battwheels_staging"
    db = client[db_name]

    await seed_demo(db)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
