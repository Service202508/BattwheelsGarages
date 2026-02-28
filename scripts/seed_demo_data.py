# Sprint 6D-03: Seed demo account with realistic EV workshop data
#
# Seeds the Volt Motors demo org (demo-volt-motors-001) with:
# - 5 customers, 3 employees, 10 tickets, 3 invoices, 1 payroll run
#
# Usage:
#   python scripts/seed_demo_data.py
#
# SAFETY: Hard-coded to ONLY run against battwheels_dev.

import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

DEMO_ORG_ID = "demo-volt-motors-001"
DB_NAME = "battwheels_dev"

now = datetime.now(timezone.utc)


def ts(days_ago: int = 0, hours_ago: int = 0) -> str:
    return (now - timedelta(days=days_ago, hours=hours_ago)).isoformat()


def uid():
    return uuid.uuid4().hex[:12]


CUSTOMERS = [
    {"contact_id": f"cust_{uid()}", "name": "Arjun Mehta", "email": "arjun.mehta@gmail.com",
     "phone": "+91-9876543210", "city": "Delhi", "vehicle_type": "Ola S1 Pro",
     "vehicle_registration": "DL-01-EV-1234", "contact_type": "customer"},
    {"contact_id": f"cust_{uid()}", "name": "Priya Sharma", "email": "priya.sharma@outlook.com",
     "phone": "+91-9876543211", "city": "Gurugram", "vehicle_type": "TVS iQube",
     "vehicle_registration": "HR-26-EV-5678", "contact_type": "customer"},
    {"contact_id": f"cust_{uid()}", "name": "Rahul Verma", "email": "rahul.verma@yahoo.com",
     "phone": "+91-9876543212", "city": "Noida", "vehicle_type": "Ather 450X",
     "vehicle_registration": "UP-16-EV-9012", "contact_type": "customer"},
    {"contact_id": f"cust_{uid()}", "name": "Sunita Patel", "email": "sunita.patel@gmail.com",
     "phone": "+91-9876543213", "city": "Delhi", "vehicle_type": "Hero Optima",
     "vehicle_registration": "DL-05-EV-3456", "contact_type": "customer"},
    {"contact_id": f"cust_{uid()}", "name": "Vikram Singh", "email": "vikram.singh@hotmail.com",
     "phone": "+91-9876543214", "city": "Faridabad", "vehicle_type": "Bajaj Chetak",
     "vehicle_registration": "HR-32-EV-7890", "contact_type": "customer"},
]

EMPLOYEES = [
    {"employee_id": f"emp_{uid()}", "name": "Ravi Kumar", "email": "ravi.kumar@voltmotors.in",
     "phone": "+91-9988776601", "department": "Service", "designation": "Senior EV Technician",
     "role": "technician", "status": "active", "basic_salary": 35000,
     "state_code": "MH", "date_of_joining": ts(180)},
    {"employee_id": f"emp_{uid()}", "name": "Ankit Sharma", "email": "ankit.sharma@voltmotors.in",
     "phone": "+91-9988776602", "department": "Service", "designation": "EV Technician",
     "role": "technician", "status": "active", "basic_salary": 22000,
     "state_code": "DL", "date_of_joining": ts(90)},
    {"employee_id": f"emp_{uid()}", "name": "Meena Gupta", "email": "meena.gupta@voltmotors.in",
     "phone": "+91-9988776603", "department": "Front Office", "designation": "Service Advisor",
     "role": "service_advisor", "status": "active", "basic_salary": 18000,
     "state_code": "DL", "date_of_joining": ts(120)},
]


def make_ticket(idx, customer, title, description, status, days_ago,
                resolution=None, assigned_to=None, efi_used=False,
                vehicle_type=None, vehicle_reg=None):
    tid = f"tkt_demo_{uid()}"
    t = {
        "ticket_id": tid,
        "organization_id": DEMO_ORG_ID,
        "title": title,
        "description": description,
        "status": status,
        "priority": "high" if idx <= 3 else "medium",
        "category": "electrical",
        "ticket_type": "workshop",
        "customer_id": customer["contact_id"],
        "customer_name": customer["name"],
        "customer_phone": customer["phone"],
        "vehicle_type": vehicle_type or customer["vehicle_type"],
        "vehicle_registration": vehicle_reg or customer["vehicle_registration"],
        "created_at": ts(days_ago, hours_ago=idx),
        "updated_at": ts(max(0, days_ago - 1)),
    }
    if assigned_to:
        t["assigned_technician_id"] = assigned_to["employee_id"]
        t["assigned_technician_name"] = assigned_to["name"]
    if resolution:
        t["resolution_notes"] = resolution
        t["resolved_at"] = ts(max(0, days_ago - 1))
    if efi_used:
        t["efi_used"] = True
        t["efi_suggested_fault"] = "battery"
    return t


def make_invoice(ticket, amount_before_tax, description_line, days_ago):
    tax = round(amount_before_tax * 0.18, 2)
    total = round(amount_before_tax + tax, 2)
    inv_id = f"INV-DEMO-{uid().upper()}"
    return {
        "invoice_id": inv_id,
        "invoice_number": inv_id,
        "organization_id": DEMO_ORG_ID,
        "customer_id": ticket["customer_id"],
        "customer_name": ticket["customer_name"],
        "ticket_id": ticket["ticket_id"],
        "invoice_date": (now - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
        "due_date": (now - timedelta(days=days_ago - 15)).strftime("%Y-%m-%d"),
        "status": "paid",
        "items": [{
            "description": description_line,
            "quantity": 1,
            "unit_price": amount_before_tax,
            "amount": amount_before_tax,
            "hsn_code": "998714",
        }],
        "subtotal": amount_before_tax,
        "tax_amount": tax,
        "cgst_amount": round(tax / 2, 2),
        "sgst_amount": round(tax / 2, 2),
        "igst_amount": 0,
        "total_amount": total,
        "amount_paid": total,
        "amount_due": 0,
        "currency": "INR",
        "place_of_supply": "07",
        "created_at": ts(days_ago),
        "updated_at": ts(days_ago),
    }


async def seed():
    if os.environ.get("DB_NAME", DB_NAME) != DB_NAME:
        raise Exception(f"SAFETY: Only runs against {DB_NAME}")

    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[DB_NAME]

    # Verify demo org exists
    org = await db.organizations.find_one(
        {"organization_id": DEMO_ORG_ID}, {"_id": 0, "organization_id": 1, "name": 1}
    )
    if not org:
        print(f"ERROR: Demo org {DEMO_ORG_ID} not found. Cannot seed.")
        return
    print(f"Seeding demo data for: {org.get('name')} ({DEMO_ORG_ID})")

    # Clean existing demo data (re-seedable)
    for coll in ["tickets", "invoices_enhanced", "employees", "contacts",
                  "payroll_runs", "payroll_slips"]:
        r = await db[coll].delete_many({"organization_id": DEMO_ORG_ID})
        if r.deleted_count:
            print(f"  Cleaned {coll}: {r.deleted_count} docs")

    # 1. Seed customers
    for c in CUSTOMERS:
        c["organization_id"] = DEMO_ORG_ID
        c["created_at"] = ts(60)
        c["updated_at"] = ts(60)
    await db.contacts.insert_many(CUSTOMERS)
    print(f"  Customers seeded: {len(CUSTOMERS)}")

    # 2. Seed employees
    for e in EMPLOYEES:
        e["organization_id"] = DEMO_ORG_ID
        e["created_at"] = e["date_of_joining"]
        e["updated_at"] = ts(0)
    await db.employees.insert_many(EMPLOYEES)
    print(f"  Employees seeded: {len(EMPLOYEES)}")

    # 3. Seed tickets
    ravi = EMPLOYEES[0]
    ankit = EMPLOYEES[1]

    tickets = [
        make_ticket(1, CUSTOMERS[0],
                    "Battery not charging above 80%",
                    "Customer reports Ola S1 Pro battery stops charging at 80%. "
                    "Charger shows green but SOC stuck. Issue started after firmware update.",
                    "resolved", 14,
                    resolution="BMS calibration drift detected. Recalibrated BMS parameters. "
                               "Charging now restored to 100%. Firmware rollback not needed.",
                    assigned_to=ravi, efi_used=True),
        make_ticket(2, CUSTOMERS[1],
                    "Sudden power cutoff at high speed",
                    "TVS iQube loses power suddenly above 45 kmph. Dashboard shows thermal warning briefly. "
                    "Happens on highway rides in afternoon heat.",
                    "resolved", 7,
                    resolution="Motor controller thermal throttle triggered. Cooling fan intake "
                               "clogged with dust. Cleaned cooling system, applied thermal paste. "
                               "Thermal test passed at 50 kmph for 30 min.",
                    assigned_to=ravi, efi_used=True),
        make_ticket(3, CUSTOMERS[2],
                    "Range reduced by 40% suddenly",
                    "Ather 450X range dropped from 85 km to ~50 km overnight. "
                    "No error codes on dashboard. Battery shows 100% but depletes fast.",
                    "resolved", 3,
                    resolution="Cell group 3 showing 0.4V imbalance. Battery pack rebalancing "
                               "cycle performed (12hr controlled charge/discharge). Post-rebalance "
                               "range restored to 82 km.",
                    assigned_to=ankit, efi_used=True),
        make_ticket(4, CUSTOMERS[3],
                    "Charger shows error E201, not charging",
                    "Hero Optima charger displays E201 error code. Red LED blinking. "
                    "Tried two different power outlets, same result.",
                    "in_progress", 2,
                    assigned_to=ravi),
        make_ticket(5, CUSTOMERS[4],
                    "Display not showing battery percentage",
                    "Bajaj Chetak dashboard shows dashes instead of battery %. "
                    "Vehicle runs fine otherwise. Issue intermittent — sometimes shows correctly.",
                    "in_progress", 1,
                    assigned_to=ankit),
        make_ticket(6, CUSTOMERS[0],
                    "Regen braking feels weaker than before",
                    "Repeat customer. Ola S1 Pro regen braking noticeably weaker. "
                    "Previously had strong regen, now barely noticeable on downhill.",
                    "open", 0),
        make_ticket(7, CUSTOMERS[1],
                    "Squeaking noise from rear wheel",
                    "TVS iQube making squeaking noise from rear wheel at low speeds. "
                    "Gets louder when braking. Started after riding through waterlogged road.",
                    "open", 0),
        make_ticket(8, CUSTOMERS[2],
                    "Mobile app not connecting to vehicle",
                    "Ather 450X Bluetooth connection to Ather app keeps dropping. "
                    "Cannot update firmware or view ride stats. Tried re-pairing.",
                    "open", 0),
        make_ticket(9, CUSTOMERS[3],
                    "Motor making whining noise at startup",
                    "Hero Optima motor produces high-pitched whine for first 2-3 minutes "
                    "after cold start. Goes away once warmed up.",
                    "in_progress", 1,
                    assigned_to=ravi),
        make_ticket(10, CUSTOMERS[4],
                     "Turn indicators not auto-cancelling",
                     "Bajaj Chetak left turn indicator stays on after completing turn. "
                     "Right indicator works fine. Physical switch feels normal.",
                     "open", 0),
    ]
    await db.tickets.insert_many(tickets)
    print(f"  Tickets seeded: {len(tickets)}")

    # 4. Seed invoices for the 3 resolved tickets
    invoices = [
        make_invoice(tickets[0], 2500,
                     "BMS Calibration + System Inspection — Ola S1 Pro", 13),
        make_invoice(tickets[1], 3200,
                     "Controller Cooling System Service + Labour — TVS iQube", 6),
        make_invoice(tickets[2], 4800,
                     "Battery Pack Rebalancing + Cell Testing — Ather 450X", 2),
    ]
    await db.invoices_enhanced.insert_many(invoices)
    print(f"  Invoices seeded: {len(invoices)}")

    # 5. Seed payroll run (last month)
    last_month = now.replace(day=1) - timedelta(days=1)
    payroll_month = last_month.month
    payroll_year = last_month.year
    run_id = f"pr_{uid()}"

    slips = []
    for emp in EMPLOYEES:
        basic = emp["basic_salary"]
        hra = round(basic * 0.4)
        gross = basic + hra
        pf_employee = min(round(basic * 0.12), 1800)
        pf_employer = pf_employee
        pt = 200 if emp["state_code"] == "MH" else 0
        net = gross - pf_employee - pt

        slips.append({
            "slip_id": f"ps_{uid()}",
            "payroll_run_id": run_id,
            "organization_id": DEMO_ORG_ID,
            "employee_id": emp["employee_id"],
            "employee_name": emp["name"],
            "month": payroll_month,
            "year": payroll_year,
            "basic_salary": basic,
            "hra": hra,
            "gross_salary": gross,
            "pf_employee": pf_employee,
            "pf_employer": pf_employer,
            "professional_tax": pt,
            "net_salary": net,
            "status": "paid",
            "created_at": ts(5),
        })

    payroll_run = {
        "payroll_run_id": run_id,
        "organization_id": DEMO_ORG_ID,
        "month": payroll_month,
        "year": payroll_year,
        "status": "completed",
        "total_gross": sum(s["gross_salary"] for s in slips),
        "total_net": sum(s["net_salary"] for s in slips),
        "total_pf": sum(s["pf_employee"] for s in slips),
        "employee_count": len(slips),
        "created_at": ts(5),
        "completed_at": ts(4),
    }

    await db.payroll_runs.insert_one(payroll_run)
    await db.payroll_slips.insert_many(slips)
    print(f"  Payroll run seeded: {payroll_month}/{payroll_year}, {len(slips)} slips")

    # Summary
    print(f"\n{'='*60}")
    print(f"  DEMO DATA SEEDED SUCCESSFULLY")
    print(f"{'='*60}")
    for coll in ["contacts", "employees", "tickets", "invoices_enhanced",
                  "payroll_runs", "payroll_slips"]:
        count = await db[coll].count_documents({"organization_id": DEMO_ORG_ID})
        print(f"  {coll}: {count}")

    # Ticket status breakdown
    pipeline = [
        {"$match": {"organization_id": DEMO_ORG_ID}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    statuses = await db.tickets.aggregate(pipeline).to_list(10)
    print(f"\n  Ticket statuses:")
    for s in statuses:
        print(f"    {s['_id']}: {s['count']}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
