#!/usr/bin/env python3
"""
Volt Motors Comprehensive Seed — Part 2: Transactions (Sections F-N)
=====================================================================
Creates: Tickets, Estimates, Invoices, Payments, COGS, Credit Notes, Payroll, AMC, EVFI
IDEMPOTENT: Uses upsert patterns. Safe to run multiple times.
"""

import asyncio
import os
import sys
import uuid
import random
import hashlib
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_dev")
ORG_ID = "demo-volt-motors-001"
SEED_TAG = "seed_comprehensive_v1"
NOW = datetime.now(timezone.utc)
TODAY = NOW.strftime("%Y-%m-%d")

def iso(dt=None): return (dt or NOW).isoformat()
def uid(prefix=""): return f"{prefix}{uuid.uuid4().hex[:12]}"
def days_ago(n): return NOW - timedelta(days=n)

# ── Staff IDs ──
TECH_ANKIT = {"id": "user_ankit_tech", "name": "Ankit Verma"}
TECH_RAVI  = {"id": "user_ravi_tech",  "name": "Ravi Kumar"}
OWNER      = {"id": "user-demo-owner-001", "name": "Demo Admin"}

# ── Chart of Accounts ──
COA = {
    "BANK":     {"code": "1100", "name": "Bank Account - Current",    "type": "asset"},
    "AR":       {"code": "1200", "name": "Accounts Receivable",       "type": "asset"},
    "INV":      {"code": "1300", "name": "Inventory Asset",           "type": "asset"},
    "CGST_PAY": {"code": "2100", "name": "GST Payable - CGST",       "type": "liability"},
    "SGST_PAY": {"code": "2101", "name": "GST Payable - SGST",       "type": "liability"},
    "IGST_PAY": {"code": "2102", "name": "GST Payable - IGST",       "type": "liability"},
    "PF_PAY":   {"code": "2200", "name": "PF Payable",               "type": "liability"},
    "TDS_PAY":  {"code": "2202", "name": "TDS Payable",              "type": "liability"},
    "PT_PAY":   {"code": "2203", "name": "Professional Tax Payable",  "type": "liability"},
    "SAL_PAY":  {"code": "2300", "name": "Salary Payable",           "type": "liability"},
    "REVENUE":  {"code": "4100", "name": "Sales Revenue",            "type": "revenue"},
    "COGS":     {"code": "5100", "name": "Cost of Goods Sold",       "type": "expense"},
    "SALARY":   {"code": "6100", "name": "Salary Expense",           "type": "expense"},
}

def jl(account_key, debit=0, credit=0, desc=""):
    a = COA[account_key]
    return {
        "line_id": f"jel_{uuid.uuid4().hex[:12]}",
        "account_id": f"coa_{account_key.lower()}",
        "account_name": a["name"], "account_code": a["code"],
        "account_type": a["type"],
        "debit_amount": debit, "credit_amount": credit,
        "description": desc,
    }

ORG_STATE = "07"  # Delhi

def gst_split(subtotal, customer_state):
    """Returns (cgst, sgst, igst) based on customer state vs org state."""
    tax = round(subtotal * 0.18, 2)
    if customer_state == ORG_STATE:
        half = round(tax / 2, 2)
        return half, half, 0
    return 0, 0, tax


# ══════════════════════════════════════════════════════════════════
# TICKET DEFINITIONS
# ══════════════════════════════════════════════════════════════════

TICKET_DEFS = [
    # --- 5 CLOSED ---
    {"idx": 1, "id": "STKT-001", "status": "closed", "customer": "CON-rajesh-001", "cname": "Rajesh Kumar", "cphone": "9876543201", "cstate": "07",
     "vehicle_id": "VH-rajesh-ola-001", "vtype": "2W", "vmake": "Ola", "vmodel": "Ola S1 Pro", "vreg": "DL01AB1234",
     "title": "Battery drain - SOC drops 20% overnight", "category": "battery", "priority": "high",
     "symptoms": ["Battery draining overnight", "SOC drop"], "dtc": ["BMS_001"],
     "resolution": "Replaced faulty BMS module. Battery drain resolved.", "tech": TECH_ANKIT,
     "parts_used": [("ITEM-bms-001", "BMS Module", 3200, 4500, "85076000")],
     "services_used": [("ITEM-diag-011", "Basic Diagnostic", 500, "998714")]},
    {"idx": 2, "id": "STKT-002", "status": "closed", "customer": "CON-sunita-002", "cname": "Sunita Patel", "cphone": "9876543202", "cstate": "27",
     "vehicle_id": "VH-sunita-ather-002", "vtype": "2W", "vmake": "Ather", "vmodel": "Ather 450X", "vreg": "MH01CD5678",
     "title": "Motor making unusual noise at high speed", "category": "motor", "priority": "medium",
     "symptoms": ["Unusual motor noise", "Vibration at speed"], "dtc": ["MOT_003"],
     "resolution": "Motor controller replaced. Noise eliminated.", "tech": TECH_RAVI,
     "parts_used": [("ITEM-motor-003", "Motor Controller", 2800, 4200, "85044090")],
     "services_used": [("ITEM-motorserv-013", "Motor Servicing", 2000, "998714")]},
    {"idx": 3, "id": "STKT-003", "status": "closed", "customer": "CON-manoj-003", "cname": "Manoj Tiwari", "cphone": "9876543203", "cstate": "07",
     "vehicle_id": "VH-manoj-tvs-003", "vtype": "2W", "vmake": "TVS", "vmodel": "TVS iQube", "vreg": "DL02EF9012",
     "title": "BMS error code — won't charge", "category": "battery", "priority": "critical",
     "symptoms": ["BMS error", "Charging failure"], "dtc": ["BMS_005", "CHG_002"],
     "resolution": "Battery cell pack replaced and BMS recalibrated.", "tech": TECH_ANKIT,
     "parts_used": [("ITEM-battery-002", "Battery Cell Pack", 8500, 12000, "85076000")],
     "services_used": [("ITEM-bmsrecal-012", "BMS Recalibration", 1500, "998714")]},
    {"idx": 4, "id": "STKT-004", "status": "closed", "customer": "CON-deepak-004", "cname": "Deepak Singh", "cphone": "9876543204", "cstate": "09",
     "vehicle_id": "VH-deepak-nexon-004", "vtype": "4W", "vmake": "Tata", "vmodel": "Tata Nexon EV", "vreg": "UP16GH3456",
     "title": "Charging port connector loose", "category": "charging", "priority": "medium",
     "symptoms": ["Loose charging port", "Intermittent charging"], "dtc": ["CHG_001"],
     "resolution": "Charging port assembly replaced. Connector secure.", "tech": TECH_RAVI,
     "parts_used": [("ITEM-chargeport-006", "Charging Port Assembly", 1200, 1800, "85366990")],
     "services_used": [("ITEM-diag-011", "Basic Diagnostic", 500, "998714")]},
    {"idx": 5, "id": "STKT-005", "status": "closed", "customer": "CON-devfleet-006", "cname": "Delhi EV Fleet Pvt Ltd", "cphone": "9876543206", "cstate": "07",
     "vehicle_id": "VH-fleet-chetak-005", "vtype": "2W", "vmake": "Bajaj", "vmodel": "Bajaj Chetak", "vreg": "DL03IJ7890",
     "title": "Display flickering intermittently", "category": "electrical", "priority": "low",
     "symptoms": ["Display flicker", "Screen blank"], "dtc": ["DSP_001"],
     "resolution": "Display unit replaced. Firmware updated.", "tech": TECH_ANKIT,
     "parts_used": [("ITEM-display-007", "Display Unit", 1500, 2200, "85285900")],
     "services_used": [("ITEM-inspect-014", "Full Vehicle Inspection", 800, "998714")]},
    # --- 3 WORK_COMPLETED ---
    {"idx": 6, "id": "STKT-006", "status": "work_completed", "customer": "CON-amit-005", "cname": "Amit Sharma", "cphone": "9876543205", "cstate": "06",
     "vehicle_id": "VH-amit-hero-008", "vtype": "2W", "vmake": "Hero", "vmodel": "Hero Electric Optima", "vreg": "HR01MN5678",
     "title": "Brake regeneration not working", "category": "brakes", "priority": "high",
     "symptoms": ["No regen braking", "Reduced range"], "dtc": [], "tech": TECH_RAVI,
     "parts_used": [("ITEM-brake-005", "Brake Pad Set (EV)", 350, 650, "87083099")],
     "services_used": [("ITEM-motorserv-013", "Motor Servicing", 2000, "998714")]},
    {"idx": 7, "id": "STKT-007", "status": "work_completed", "customer": "CON-greenride-007", "cname": "GreenRide Logistics", "cphone": "9876543207", "cstate": "27",
     "vehicle_id": "VH-greenride-xuv-007", "vtype": "4W", "vmake": "Mahindra", "vmodel": "Mahindra XUV400", "vreg": "MH02KL1234",
     "title": "Software update failed — dashboard frozen", "category": "software", "priority": "high",
     "symptoms": ["Dashboard frozen", "No response"], "dtc": ["SW_001"], "tech": TECH_ANKIT,
     "parts_used": [],
     "services_used": [("ITEM-swupdate-015", "Software Update", 1000, "998714"), ("ITEM-diag-011", "Basic Diagnostic", 500, "998714")]},
    {"idx": 8, "id": "STKT-008", "status": "work_completed", "customer": "CON-devfleet-006", "cname": "Delhi EV Fleet Pvt Ltd", "cphone": "9876543206", "cstate": "07",
     "vehicle_id": "VH-fleet-chetak-006", "vtype": "2W", "vmake": "Bajaj", "vmodel": "Bajaj Chetak", "vreg": "DL03IJ7891",
     "title": "Throttle response delay", "category": "electrical", "priority": "medium",
     "symptoms": ["Throttle lag", "Delayed acceleration"], "dtc": ["THR_001"], "tech": TECH_RAVI,
     "parts_used": [("ITEM-throttle-004", "Throttle Sensor", 450, 750, "90318090")],
     "services_used": [("ITEM-diag-011", "Basic Diagnostic", 500, "998714")]},
    # --- 4 WORK_IN_PROGRESS ---
    {"idx": 9, "id": "STKT-009", "status": "work_in_progress", "customer": "CON-rajesh-001", "cname": "Rajesh Kumar", "cphone": "9876543201", "cstate": "07",
     "vehicle_id": "VH-rajesh-ola-001", "vtype": "2W", "vmake": "Ola", "vmodel": "Ola S1 Pro", "vreg": "DL01AB1234",
     "title": "Wiring harness melted near battery", "category": "electrical", "priority": "critical",
     "symptoms": ["Burnt smell", "Wiring damage"], "dtc": ["ELC_002"], "tech": TECH_ANKIT},
    {"idx": 10, "id": "STKT-010", "status": "work_in_progress", "customer": "CON-sunita-002", "cname": "Sunita Patel", "cphone": "9876543202", "cstate": "27",
     "vehicle_id": "VH-sunita-ather-002", "vtype": "2W", "vmake": "Ather", "vmodel": "Ather 450X", "vreg": "MH01CD5678",
     "title": "Coolant pump leaking", "category": "cooling", "priority": "high",
     "symptoms": ["Coolant leak", "Overheating warning"], "dtc": ["CLN_001"], "tech": TECH_RAVI},
    {"idx": 11, "id": "STKT-011", "status": "work_in_progress", "customer": "CON-manoj-003", "cname": "Manoj Tiwari", "cphone": "9876543203", "cstate": "07",
     "vehicle_id": "VH-manoj-tvs-003", "vtype": "2W", "vmake": "TVS", "vmodel": "TVS iQube", "vreg": "DL02EF9012",
     "title": "Fuse blown — no power to motor", "category": "electrical", "priority": "high",
     "symptoms": ["No power", "Fuse blown"], "dtc": ["ELC_005"], "tech": TECH_ANKIT},
    {"idx": 12, "id": "STKT-012", "status": "work_in_progress", "customer": "CON-deepak-004", "cname": "Deepak Singh", "cphone": "9876543204", "cstate": "09",
     "vehicle_id": "VH-deepak-nexon-004", "vtype": "4W", "vmake": "Tata", "vmodel": "Tata Nexon EV", "vreg": "UP16GH3456",
     "title": "Motor controller overheating", "category": "motor", "priority": "critical",
     "symptoms": ["Overheating", "Reduced power"], "dtc": ["MOT_007"], "tech": TECH_RAVI},
    # --- 3 TECHNICIAN_ASSIGNED ---
    {"idx": 13, "id": "STKT-013", "status": "technician_assigned", "customer": "CON-amit-005", "cname": "Amit Sharma", "cphone": "9876543205", "cstate": "06",
     "vehicle_id": "VH-amit-hero-008", "vtype": "2W", "vmake": "Hero", "vmodel": "Hero Electric Optima", "vreg": "HR01MN5678",
     "title": "Battery cell pack degradation — range reduced", "category": "battery", "priority": "medium",
     "symptoms": ["Reduced range", "SOC inaccurate"], "dtc": ["BMS_010"], "tech": TECH_ANKIT},
    {"idx": 14, "id": "STKT-014", "status": "technician_assigned", "customer": "CON-quickcharge-009", "cname": "Quick Charge Services", "cphone": "9876543209", "cstate": "29",
     "title": "General inspection for fleet vehicle", "category": "general", "priority": "low",
     "symptoms": ["Routine inspection"], "dtc": [], "tech": TECH_RAVI},
    {"idx": 15, "id": "STKT-015", "status": "technician_assigned", "customer": "CON-metroev-010", "cname": "Metro EV Solutions", "cphone": "9876543210", "cstate": "06",
     "title": "Pre-purchase inspection for used EV", "category": "general", "priority": "low",
     "symptoms": ["Pre-purchase check"], "dtc": [], "tech": TECH_ANKIT},
    # --- 3 OPEN ---
    {"idx": 16, "id": "STKT-016", "status": "open", "customer": "CON-rajesh-001", "cname": "Rajesh Kumar", "cphone": "9876543201", "cstate": "07",
     "vehicle_id": "VH-rajesh-ola-001", "vtype": "2W", "vmake": "Ola", "vmodel": "Ola S1 Pro", "vreg": "DL01AB1234",
     "title": "Charging slow after rain exposure", "category": "charging", "priority": "medium",
     "symptoms": ["Slow charging", "Moisture ingress"], "dtc": []},
    {"idx": 17, "id": "STKT-017", "status": "open", "customer": "CON-priyaent-008", "cname": "Priya Enterprises", "cphone": "9876543208", "cstate": "09",
     "title": "Bulk vehicle checkup request for 5 units", "category": "general", "priority": "low",
     "symptoms": ["Fleet maintenance request"], "dtc": []},
    {"idx": 18, "id": "STKT-018", "status": "open", "customer": "CON-greenride-007", "cname": "GreenRide Logistics", "cphone": "9876543207", "cstate": "27",
     "vehicle_id": "VH-greenride-xuv-007", "vtype": "4W", "vmake": "Mahindra", "vmodel": "Mahindra XUV400", "vreg": "MH02KL1234",
     "title": "AC not cooling — compressor issue suspected", "category": "hvac", "priority": "medium",
     "symptoms": ["AC not cooling", "Warm air"], "dtc": ["HVAC_002"]},
    # --- 2 INVOICED ---
    {"idx": 19, "id": "STKT-019", "status": "invoiced", "customer": "CON-sunita-002", "cname": "Sunita Patel", "cphone": "9876543202", "cstate": "27",
     "vehicle_id": "VH-sunita-ather-002", "vtype": "2W", "vmake": "Ather", "vmodel": "Ather 450X", "vreg": "MH01CD5678",
     "title": "BMS recalibration after 6-month storage", "category": "battery", "priority": "medium",
     "symptoms": ["BMS recalibration needed", "Long storage"], "dtc": ["BMS_008"], "tech": TECH_ANKIT,
     "resolution": "BMS recalibrated, software updated. All cells balanced.",
     "parts_used": [("ITEM-bms-001", "BMS Module", 3200, 4500, "85076000")],
     "services_used": [("ITEM-bmsrecal-012", "BMS Recalibration", 1500, "998714"), ("ITEM-swupdate-015", "Software Update", 1000, "998714")]},
    {"idx": 20, "id": "STKT-020", "status": "invoiced", "customer": "CON-devfleet-006", "cname": "Delhi EV Fleet Pvt Ltd", "cphone": "9876543206", "cstate": "07",
     "vehicle_id": "VH-fleet-chetak-005", "vtype": "2W", "vmake": "Bajaj", "vmodel": "Bajaj Chetak", "vreg": "DL03IJ7890",
     "title": "Annual maintenance + full inspection", "category": "general", "priority": "low",
     "symptoms": ["Annual service", "Routine check"], "dtc": [], "tech": TECH_RAVI,
     "resolution": "Full inspection complete. Software updated. All systems normal.",
     "parts_used": [],
     "services_used": [("ITEM-inspect-014", "Full Vehicle Inspection", 800, "998714"), ("ITEM-inspect-014", "Full Vehicle Inspection", 800, "998714"), ("ITEM-swupdate-015", "Software Update", 1000, "998714")]},
]


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    counts = {}
    je_counter = [0]  # mutable counter for journal entry numbering

    def next_je_ref(prefix="JE"):
        je_counter[0] += 1
        return f"{prefix}-SEED-{je_counter[0]:05d}"

    # ================================================================
    # SECTION F — TICKETS (20)
    # ================================================================
    print("[F] Seeding 20 tickets...")
    ticket_count = 0
    for t in TICKET_DEFS:
        created = days_ago(30 - t["idx"])
        doc = {
            "ticket_id": t["id"],
            "organization_id": ORG_ID,
            "title": t["title"],
            "description": t["title"],
            "status": t["status"],
            "priority": t["priority"],
            "category": t["category"],
            "ticket_type": "workshop",
            "customer_id": t["customer"],
            "customer_name": t["cname"],
            "customer_phone": t["cphone"],
            "vehicle_type": t.get("vtype", ""),
            "vehicle_category": t.get("vtype", ""),
            "vehicle_registration": t.get("vreg", ""),
            "vehicle_oem": t.get("vmake", ""),
            "vehicle_model": t.get("vmodel", ""),
            "vehicle_info": {"make": t.get("vmake", ""), "model": t.get("vmodel", "")},
            "vehicle_id": t.get("vehicle_id", ""),
            "symptoms": t.get("symptoms", []),
            "dtc_codes": t.get("dtc", []),
            "created_at": iso(created),
            "updated_at": iso(created + timedelta(days=2)),
            "_seed": SEED_TAG,
        }
        if t.get("tech"):
            doc["assigned_technician_id"] = t["tech"]["id"]
            doc["assigned_technician_name"] = t["tech"]["name"]
            doc["assigned_to"] = t["tech"]["id"]
        if t.get("resolution"):
            doc["resolution_notes"] = t["resolution"]
            doc["resolved_at"] = iso(created + timedelta(days=3))

        await db.tickets.update_one(
            {"ticket_id": t["id"], "organization_id": ORG_ID},
            {"$set": doc}, upsert=True)
        ticket_count += 1

    counts["tickets"] = ticket_count
    print(f"  {ticket_count} tickets seeded")

    # ================================================================
    # SECTION G — ESTIMATES (10)
    # ================================================================
    print("[G] Seeding 10 estimates...")

    # Map: estimate links to ticket, with line items and status
    EST_MAP = [
        # (est_id, ticket_def_idx, status)
        ("SEST-001", 8,  "draft"),     # T8 work_completed
        ("SEST-002", 9,  "draft"),     # T9 work_in_progress
        ("SEST-003", 12, "draft"),     # T12 work_in_progress
        ("SEST-004", 5,  "sent"),      # T5 closed
        ("SEST-005", 10, "sent"),      # T10 work_in_progress
        ("SEST-006", 11, "sent"),      # T11 work_in_progress
        ("SEST-007", 6,  "approved"),  # T6 work_completed
        ("SEST-008", 7,  "approved"),  # T7 work_completed
        ("SEST-009", 19, "converted"), # T19 invoiced
        ("SEST-010", 20, "converted"), # T20 invoiced
    ]

    # Line items for estimates: pick parts+services from the ticket or reasonable items
    EST_LINES = {
        "SEST-001": [("part", "ITEM-throttle-004", "Throttle Sensor", 1, 750, "90318090"), ("service", "ITEM-diag-011", "Basic Diagnostic", 1, 500, "998714")],
        "SEST-002": [("part", "ITEM-wiring-008", "Wiring Harness", 1, 1200, "85441990")],
        "SEST-003": [("part", "ITEM-motor-003", "Motor Controller", 1, 4200, "85044090"), ("service", "ITEM-diag-011", "Basic Diagnostic", 1, 500, "998714")],
        "SEST-004": [("part", "ITEM-display-007", "Display Unit", 1, 2200, "85285900"), ("service", "ITEM-inspect-014", "Full Vehicle Inspection", 1, 800, "998714")],
        "SEST-005": [("part", "ITEM-coolant-010", "Coolant Pump", 1, 1500, "84138190")],
        "SEST-006": [("part", "ITEM-fuse-009", "Fuse Set", 2, 250, "85351000"), ("service", "ITEM-diag-011", "Basic Diagnostic", 1, 500, "998714")],
        "SEST-007": [("part", "ITEM-brake-005", "Brake Pad Set (EV)", 2, 650, "87083099"), ("service", "ITEM-motorserv-013", "Motor Servicing", 1, 2000, "998714")],
        "SEST-008": [("service", "ITEM-swupdate-015", "Software Update", 1, 1000, "998714"), ("service", "ITEM-diag-011", "Basic Diagnostic", 1, 500, "998714")],
        "SEST-009": [("part", "ITEM-bms-001", "BMS Module", 1, 4500, "85076000"), ("service", "ITEM-bmsrecal-012", "BMS Recalibration", 1, 1500, "998714"), ("service", "ITEM-swupdate-015", "Software Update", 1, 1000, "998714")],
        "SEST-010": [("service", "ITEM-inspect-014", "Full Vehicle Inspection", 2, 800, "998714"), ("service", "ITEM-swupdate-015", "Software Update", 1, 1000, "998714")],
    }

    est_count = 0
    for est_id, tkt_idx, est_status in EST_MAP:
        tdef = TICKET_DEFS[tkt_idx - 1]  # 1-indexed
        lines_raw = EST_LINES[est_id]

        # Build line items with tax
        line_items = []
        subtotal = 0
        for i, (ltype, item_id, name, qty, rate, hsn) in enumerate(lines_raw):
            line_total = qty * rate
            tax_amt = round(line_total * 0.18, 2)
            cgst, sgst, igst = gst_split(line_total, tdef["cstate"])
            li = {
                "line_item_id": f"eli_{est_id}_{i+1}",
                "estimate_id": est_id,
                "type": ltype,
                "item_id": item_id,
                "name": name,
                "description": name,
                "qty": float(qty),
                "unit": "pcs" if ltype == "part" else "nos",
                "unit_price": float(rate),
                "rate": float(rate),
                "discount": 0,
                "discount_percent": 0,
                "discount_amount": 0,
                "tax_rate": 18.0,
                "tax_name": "GST @18%",
                "tax_percentage": 18.0,
                "hsn_code": hsn,
                "gross_amount": float(line_total),
                "taxable_amount": float(line_total),
                "tax_amount": tax_amt,
                "cgst": cgst, "sgst": sgst, "igst": igst,
                "line_total": round(line_total + tax_amt, 2),
                "total": round(line_total + tax_amt, 2),
                "sort_index": i + 1,
                "line_number": i + 1,
            }
            line_items.append(li)
            subtotal += line_total

        tax_total = round(subtotal * 0.18, 2)
        grand_total = round(subtotal + tax_total, 2)

        est_doc = {
            "estimate_id": est_id,
            "estimate_number": f"TKT-EST-S{est_count+1:04d}",
            "organization_id": ORG_ID,
            "ticket_id": tdef["id"],
            "customer_id": tdef["customer"],
            "customer_name": tdef["cname"],
            "status": est_status,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "discount_total": 0,
            "grand_total": grand_total,
            "currency": "INR",
            "notes": "",
            "terms": "",
            "subject": f"Estimate for Ticket #{tdef['id']}",
            "version": 1,
            "created_at": iso(days_ago(25 - est_count)),
            "updated_at": iso(days_ago(24 - est_count)),
            "created_by": OWNER["id"],
            "created_by_name": OWNER["name"],
            "_seed": SEED_TAG,
        }

        await db.ticket_estimates.update_one(
            {"estimate_id": est_id, "organization_id": ORG_ID},
            {"$set": est_doc}, upsert=True)

        # Store line items in separate collection
        for li in line_items:
            li["organization_id"] = ORG_ID
            li["_seed"] = SEED_TAG
            await db.estimate_line_items.update_one(
                {"line_item_id": li["line_item_id"], "estimate_id": est_id},
                {"$set": li}, upsert=True)

        est_count += 1

    counts["estimates"] = est_count
    print(f"  {est_count} estimates seeded")

    # ================================================================
    # SECTION H — INVOICES (8) WITH JOURNAL ENTRIES
    # ================================================================
    print("[H] Seeding 8 invoices + sales journal entries...")

    # Invoice definitions: (inv_id, ticket_idx, est_id_or_none, status, payment_status)
    INV_DEFS = [
        ("SINV-001", 1, None, "paid", "paid"),           # T1 Rajesh Delhi
        ("SINV-002", 2, None, "paid", "paid"),           # T2 Sunita Mumbai
        ("SINV-003", 3, None, "paid", "paid"),           # T3 Manoj Delhi
        ("SINV-004", 4, None, "partially_paid", "partially_paid"),  # T4 Deepak Noida
        ("SINV-005", 5, "SEST-004", "partially_paid", "partially_paid"),  # T5 Fleet Delhi
        ("SINV-006", 6, "SEST-007", "sent", "unpaid"),   # T6 Amit Gurgaon
        ("SINV-007", 19, "SEST-009", "sent", "unpaid"),  # T19 Sunita Mumbai
        ("SINV-008", 20, "SEST-010", "sent", "unpaid"),  # T20 Fleet Delhi
    ]

    # Line items for invoices (use parts_used + services_used from ticket defs where available)
    def build_inv_lines(tdef, inv_id):
        lines = []
        idx = 0
        for item_id, name, _purchase, sell, hsn in tdef.get("parts_used", []):
            cgst, sgst, igst = gst_split(sell, tdef["cstate"])
            tax = round(sell * 0.18, 2)
            idx += 1
            lines.append({
                "line_item_id": f"ili_{inv_id}_{idx}",
                "type": "part", "item_id": item_id, "name": name, "description": name,
                "qty": 1.0, "unit": "pcs", "unit_price": float(sell),
                "discount": 0, "tax_rate": 18.0, "hsn_code": hsn,
                "line_total": round(sell + tax, 2),
            })
        for item_id, name, sell, sac in tdef.get("services_used", []):
            cgst, sgst, igst = gst_split(sell, tdef["cstate"])
            tax = round(sell * 0.18, 2)
            idx += 1
            lines.append({
                "line_item_id": f"ili_{inv_id}_{idx}",
                "type": "service", "item_id": item_id, "name": name, "description": name,
                "qty": 1.0, "unit": "nos", "unit_price": float(sell),
                "discount": 0, "tax_rate": 18.0, "hsn_code": sac,
                "line_total": round(sell + tax, 2),
            })
        return lines

    inv_count = 0
    je_count = 0
    invoice_data = {}  # store for payment reference

    for inv_id, tkt_idx, source_est, inv_status, pay_status in INV_DEFS:
        tdef = TICKET_DEFS[tkt_idx - 1]
        line_items = build_inv_lines(tdef, inv_id)
        subtotal = sum(li["unit_price"] * li["qty"] for li in line_items)
        tax_total = round(subtotal * 0.18, 2)
        grand_total = round(subtotal + tax_total, 2)
        cgst, sgst, igst = gst_split(subtotal, tdef["cstate"])

        amount_paid = 0
        balance_due = grand_total
        if pay_status == "paid":
            amount_paid = grand_total
            balance_due = 0
        elif pay_status == "partially_paid":
            amount_paid = round(grand_total * 0.5, 2)
            balance_due = round(grand_total - amount_paid, 2)

        inv_date = days_ago(20 - inv_count)
        inv_doc = {
            "invoice_id": inv_id,
            "invoice_number": f"TKT-INV-S{inv_count+1:04d}",
            "organization_id": ORG_ID,
            "source": "ticket_estimate",
            "source_estimate_id": source_est or "",
            "ticket_id": tdef["id"],
            "customer_id": tdef["customer"],
            "customer_name": tdef["cname"],
            "customer_email": "",
            "contact_number": tdef["cphone"],
            "vehicle_id": tdef.get("vehicle_id", ""),
            "vehicle_number": tdef.get("vreg", ""),
            "vehicle_make": tdef.get("vmake", ""),
            "vehicle_model": tdef.get("vmodel", ""),
            "line_items": line_items,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "discount_total": 0,
            "grand_total": grand_total,
            "currency": "INR",
            "status": inv_status,
            "payment_status": pay_status,
            "balance_due": balance_due,
            "amount_paid": amount_paid,
            "invoice_date": inv_date.strftime("%Y-%m-%d"),
            "due_date": (inv_date + timedelta(days=30)).strftime("%Y-%m-%d"),
            "created_at": iso(inv_date),
            "updated_at": iso(inv_date),
            "created_by": OWNER["id"],
            "created_by_name": OWNER["name"],
            "_seed": SEED_TAG,
        }
        if pay_status == "paid":
            inv_doc["paid_date"] = iso(inv_date + timedelta(days=2))

        await db.ticket_invoices.update_one(
            {"invoice_id": inv_id, "organization_id": ORG_ID},
            {"$set": inv_doc}, upsert=True)

        invoice_data[inv_id] = {
            "grand_total": grand_total, "subtotal": subtotal,
            "cgst": cgst, "sgst": sgst, "igst": igst,
            "customer": tdef["cname"], "customer_id": tdef["customer"],
            "cstate": tdef["cstate"], "amount_paid": amount_paid,
            "inv_number": inv_doc["invoice_number"], "inv_date": inv_date,
        }

        # --- Sales Journal Entry ---
        je_lines = [jl("AR", debit=grand_total, desc=f"Invoice {inv_doc['invoice_number']}")]
        je_lines.append(jl("REVENUE", credit=subtotal, desc=f"Sales revenue"))
        if cgst > 0:
            je_lines.append(jl("CGST_PAY", credit=cgst, desc="CGST @9%"))
            je_lines.append(jl("SGST_PAY", credit=sgst, desc="SGST @9%"))
        if igst > 0:
            je_lines.append(jl("IGST_PAY", credit=igst, desc="IGST @18%"))

        je_doc = {
            "entry_id": f"je_inv_{inv_id}",
            "entry_date": inv_date.strftime("%Y-%m-%d"),
            "reference_number": next_je_ref("JE-SLS"),
            "description": f"Sales Invoice {inv_doc['invoice_number']} - {tdef['cname']}",
            "organization_id": ORG_ID,
            "created_by": OWNER["id"],
            "entry_type": "SALES",
            "source_document_id": inv_id,
            "source_document_type": "invoice",
            "reference_id": inv_id,
            "reference_type": "invoice",
            "is_posted": True,
            "is_reversed": False,
            "lines": je_lines,
            "created_at": iso(inv_date),
            "_seed": SEED_TAG,
        }
        await db.journal_entries.update_one(
            {"entry_id": je_doc["entry_id"], "organization_id": ORG_ID},
            {"$set": je_doc}, upsert=True)
        je_count += 1
        inv_count += 1

    counts["invoices"] = inv_count
    print(f"  {inv_count} invoices + {je_count} sales JEs seeded")

    # ================================================================
    # SECTION I — PAYMENTS (5) WITH JOURNAL ENTRIES
    # ================================================================
    print("[I] Seeding 5 payments + payment journal entries...")

    PAY_DEFS = [
        ("SPAY-001", "SINV-001", "full",    "upi",           "UPI/987654321"),
        ("SPAY-002", "SINV-002", "full",    "cash",          "CASH-RECEIPT-001"),
        ("SPAY-003", "SINV-003", "full",    "bank_transfer", "NEFT/ABCD12345"),
        ("SPAY-004", "SINV-004", "partial", "upi",           "UPI/112233445"),
        ("SPAY-005", "SINV-005", "partial", "card",          "CARD/POS-00789"),
    ]

    pay_count = 0
    for pay_id, inv_id, pay_type, mode, ref in PAY_DEFS:
        idata = invoice_data[inv_id]
        amount = idata["grand_total"] if pay_type == "full" else idata["amount_paid"]
        pay_date = idata["inv_date"] + timedelta(days=2)

        pay_doc = {
            "payment_id": pay_id,
            "payment_number": f"PMT-S{pay_count+1:04d}",
            "organization_id": ORG_ID,
            "customer_id": idata["customer_id"],
            "customer_name": idata["customer"],
            "payment_date": pay_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "payment_mode": mode,
            "reference_number": ref,
            "deposit_to_account": "Bank Account - Current",
            "notes": f"Payment for {idata['inv_number']}",
            "allocations": [{"invoice_id": inv_id, "amount": amount}],
            "status": "received",
            "created_at": iso(pay_date),
            "updated_at": iso(pay_date),
            "_seed": SEED_TAG,
        }
        await db.payments_received.update_one(
            {"payment_id": pay_id, "organization_id": ORG_ID},
            {"$set": pay_doc}, upsert=True)

        # Payment journal: DR Bank, CR AR
        je_doc = {
            "entry_id": f"je_pay_{pay_id}",
            "entry_date": pay_date.strftime("%Y-%m-%d"),
            "reference_number": next_je_ref("JE-PMT"),
            "description": f"Payment {pay_doc['payment_number']} from {idata['customer']}",
            "organization_id": ORG_ID,
            "created_by": OWNER["id"],
            "entry_type": "PAYMENT",
            "source_document_id": pay_id,
            "source_document_type": "payment",
            "reference_id": pay_id,
            "reference_type": "payment",
            "is_posted": True, "is_reversed": False,
            "lines": [
                jl("BANK", debit=amount, desc=f"Payment received ({mode})"),
                jl("AR", credit=amount, desc=f"Against {idata['inv_number']}"),
            ],
            "created_at": iso(pay_date),
            "_seed": SEED_TAG,
        }
        await db.journal_entries.update_one(
            {"entry_id": je_doc["entry_id"], "organization_id": ORG_ID},
            {"$set": je_doc}, upsert=True)
        je_count += 1
        pay_count += 1

    counts["payments"] = pay_count
    print(f"  {pay_count} payments + JEs seeded")

    # ================================================================
    # SECTION J — COGS JOURNAL ENTRIES (5) + STOCK DEDUCTION
    # ================================================================
    print("[J] Seeding 5 COGS journal entries + deducting stock...")

    cogs_count = 0
    for tdef in TICKET_DEFS[:5]:  # First 5 are closed
        for item_id, name, purchase_price, _sell, hsn in tdef.get("parts_used", []):
            cogs_date = days_ago(18 - cogs_count)
            je_doc = {
                "entry_id": f"je_cogs_{tdef['id']}_{item_id}",
                "entry_date": cogs_date.strftime("%Y-%m-%d"),
                "reference_number": next_je_ref("JE-COGS"),
                "description": f"COGS - {name} consumed for ticket {tdef['id']}",
                "organization_id": ORG_ID,
                "created_by": "system",
                "entry_type": "COGS",
                "source_document_id": tdef["id"],
                "source_document_type": "ticket",
                "reference_id": tdef["id"],
                "reference_type": "ticket",
                "is_posted": True, "is_reversed": False,
                "lines": [
                    jl("COGS", debit=purchase_price, desc=f"COGS: {name}"),
                    jl("INV", credit=purchase_price, desc=f"Inventory reduction: {name}"),
                ],
                "created_at": iso(cogs_date),
                "_seed": SEED_TAG,
            }
            await db.journal_entries.update_one(
                {"entry_id": je_doc["entry_id"], "organization_id": ORG_ID},
                {"$set": je_doc}, upsert=True)

            # Deduct stock
            await db.items.update_one(
                {"item_id": item_id, "organization_id": ORG_ID},
                {"$inc": {"stock_on_hand": -1, "available_stock": -1}})

            cogs_count += 1

    counts["cogs_entries"] = cogs_count
    print(f"  {cogs_count} COGS JEs + stock deductions")

    # ================================================================
    # SECTION K — CREDIT NOTES (2)
    # ================================================================
    print("[K] Seeding 2 credit notes + reversal JEs...")

    # CN1: Against INV3 (Manoj, paid, Delhi → CGST+SGST)
    cn1_subtotal = 5000.0  # partial return of Battery Cell Pack
    cn1_cgst, cn1_sgst, cn1_igst = gst_split(cn1_subtotal, "07")
    cn1_total = round(cn1_subtotal + cn1_cgst + cn1_sgst + cn1_igst, 2)

    cn1 = {
        "credit_note_id": "SCN-001",
        "credit_note_number": "CN-S0001",
        "organization_id": ORG_ID,
        "original_invoice_id": "SINV-003",
        "original_invoice_number": "TKT-INV-S0003",
        "customer_name": "Manoj Tiwari",
        "customer_id": "CON-manoj-003",
        "customer_gstin": "",
        "reason": "Partial return — battery cell pack under warranty claim",
        "credit_note_date": (NOW - timedelta(days=5)).strftime("%Y-%m-%d"),
        "line_items": [{
            "name": "Battery Cell Pack (warranty return)", "description": "",
            "hsn_sac": "85076000", "quantity": 1.0, "rate": cn1_subtotal,
            "tax_rate": 18.0, "amount": cn1_subtotal,
            "tax_amount": round(cn1_subtotal * 0.18, 2), "total": cn1_total,
            "cgst_amount": cn1_cgst, "sgst_amount": cn1_sgst, "igst_amount": cn1_igst,
        }],
        "subtotal": cn1_subtotal, "tax_total": round(cn1_subtotal * 0.18, 2),
        "grand_total": cn1_total,
        "status": "applied",
        "created_at": iso(days_ago(5)), "updated_at": iso(days_ago(5)),
        "_seed": SEED_TAG,
    }

    # CN2: Against INV4 (Deepak, partially_paid, Noida → IGST)
    cn2_subtotal = 500.0  # return of diagnostic service
    cn2_cgst, cn2_sgst, cn2_igst = gst_split(cn2_subtotal, "09")
    cn2_total = round(cn2_subtotal + cn2_cgst + cn2_sgst + cn2_igst, 2)

    cn2 = {
        "credit_note_id": "SCN-002",
        "credit_note_number": "CN-S0002",
        "organization_id": ORG_ID,
        "original_invoice_id": "SINV-004",
        "original_invoice_number": "TKT-INV-S0004",
        "customer_name": "Deepak Singh",
        "customer_id": "CON-deepak-004",
        "customer_gstin": "",
        "reason": "Diagnostic fee waived — goodwill gesture",
        "credit_note_date": (NOW - timedelta(days=3)).strftime("%Y-%m-%d"),
        "line_items": [{
            "name": "Basic Diagnostic (waived)", "description": "",
            "hsn_sac": "998714", "quantity": 1.0, "rate": cn2_subtotal,
            "tax_rate": 18.0, "amount": cn2_subtotal,
            "tax_amount": round(cn2_subtotal * 0.18, 2), "total": cn2_total,
            "cgst_amount": cn2_cgst, "sgst_amount": cn2_sgst, "igst_amount": cn2_igst,
        }],
        "subtotal": cn2_subtotal, "tax_total": round(cn2_subtotal * 0.18, 2),
        "grand_total": cn2_total,
        "status": "applied",
        "created_at": iso(days_ago(3)), "updated_at": iso(days_ago(3)),
        "_seed": SEED_TAG,
    }

    for cn in [cn1, cn2]:
        await db.credit_notes.update_one(
            {"credit_note_id": cn["credit_note_id"], "organization_id": ORG_ID},
            {"$set": cn}, upsert=True)

        # Reversal journal: DR Revenue + DR GST, CR AR
        sub = cn["subtotal"]
        total = cn["grand_total"]
        li0 = cn["line_items"][0]
        je_lines = [jl("REVENUE", debit=sub, desc=f"Revenue reversal {cn['credit_note_number']}")]
        if li0["cgst_amount"] > 0:
            je_lines.append(jl("CGST_PAY", debit=li0["cgst_amount"], desc="CGST reversal"))
            je_lines.append(jl("SGST_PAY", debit=li0["sgst_amount"], desc="SGST reversal"))
        if li0["igst_amount"] > 0:
            je_lines.append(jl("IGST_PAY", debit=li0["igst_amount"], desc="IGST reversal"))
        je_lines.append(jl("AR", credit=total, desc=f"AR reduction {cn['credit_note_number']}"))

        je_doc = {
            "entry_id": f"je_cn_{cn['credit_note_id']}",
            "entry_date": cn["credit_note_date"],
            "reference_number": next_je_ref("JE-CN"),
            "description": f"Credit Note {cn['credit_note_number']} - {cn['customer_name']}",
            "organization_id": ORG_ID,
            "created_by": OWNER["id"],
            "entry_type": "CREDIT_NOTE",
            "source_document_id": cn["credit_note_id"],
            "source_document_type": "credit_note",
            "reference_id": cn["credit_note_id"],
            "reference_type": "credit_note",
            "is_posted": True, "is_reversed": False,
            "lines": je_lines,
            "created_at": cn["created_at"],
            "_seed": SEED_TAG,
        }
        await db.journal_entries.update_one(
            {"entry_id": je_doc["entry_id"], "organization_id": ORG_ID},
            {"$set": je_doc}, upsert=True)
        je_count += 1

    counts["credit_notes"] = 2
    print("  2 credit notes + reversal JEs seeded")

    # ================================================================
    # SECTION L — PAYROLL (March 2026)
    # ================================================================
    print("[L] Seeding payroll run (March 2026)...")

    PAYROLL_EMPLOYEES = [
        {"emp_id": "user-demo-owner-001", "name": "Demo Admin",   "role": "owner",      "gross": 60000, "basic": 30000, "pf_rate": 0.12, "pt": 200, "tds": 2000},
        {"emp_id": "user_priya_manager",  "name": "Priya Sharma", "role": "manager",     "gross": 45000, "basic": 22500, "pf_rate": 0.12, "pt": 200, "tds": 1000},
        {"emp_id": "user_ankit_tech",     "name": "Ankit Verma",  "role": "technician",  "gross": 30000, "basic": 15000, "pf_rate": 0.12, "pt": 200, "tds": 0},
        {"emp_id": "user_ravi_tech",      "name": "Ravi Kumar",   "role": "technician",  "gross": 30000, "basic": 15000, "pf_rate": 0.12, "pt": 200, "tds": 0},
        {"emp_id": "user_neha_acct",      "name": "Neha Gupta",   "role": "accountant",  "gross": 35000, "basic": 17500, "pf_rate": 0.12, "pt": 200, "tds": 500},
    ]

    total_gross = sum(e["gross"] for e in PAYROLL_EMPLOYEES)
    total_pf = sum(round(e["basic"] * e["pf_rate"]) for e in PAYROLL_EMPLOYEES)
    total_pt = sum(e["pt"] for e in PAYROLL_EMPLOYEES)
    total_tds = sum(e["tds"] for e in PAYROLL_EMPLOYEES)
    total_net = total_gross - total_pf - total_pt - total_tds

    pr_doc = {
        "payroll_run_id": "SPR-2026-03",
        "organization_id": ORG_ID,
        "period": "March 2026",
        "month": "March",
        "year": 2026,
        "status": "completed",
        "total_gross": total_gross,
        "total_net": total_net,
        "total_pf": total_pf,
        "employee_count": len(PAYROLL_EMPLOYEES),
        "generated_at": iso(days_ago(2)),
        "completed_at": iso(days_ago(1)),
        "created_at": iso(days_ago(2)),
        "_seed": SEED_TAG,
    }
    await db.payroll_runs.update_one(
        {"organization_id": ORG_ID, "period": "March 2026"},
        {"$set": pr_doc}, upsert=True)

    # Individual payslips
    for emp in PAYROLL_EMPLOYEES:
        pf = round(emp["basic"] * emp["pf_rate"])
        esi = round(emp["gross"] * 0.0075) if emp["gross"] < 21000 else 0
        net = emp["gross"] - pf - esi - emp["pt"] - emp["tds"]
        ps_doc = {
            "payslip_id": f"SPS-2026-03-{emp['emp_id']}",
            "payroll_run_id": "SPR-2026-03",
            "organization_id": ORG_ID,
            "employee_id": emp["emp_id"],
            "employee_name": emp["name"],
            "period": "March 2026",
            "month": "March",
            "year": 2026,
            "earnings": {
                "basic": emp["basic"],
                "hra": round(emp["basic"] * 0.4),
                "special_allowance": emp["gross"] - emp["basic"] - round(emp["basic"] * 0.4),
            },
            "deductions": {
                "pf_employee": pf,
                "esi_employee": esi,
                "professional_tax": emp["pt"],
                "tds": emp["tds"],
            },
            "gross_salary": emp["gross"],
            "total_deductions": pf + esi + emp["pt"] + emp["tds"],
            "net_salary": net,
            "status": "paid",
            "created_at": iso(days_ago(2)),
            "_seed": SEED_TAG,
        }
        await db.payroll_payslips.update_one(
            {"payslip_id": ps_doc["payslip_id"], "organization_id": ORG_ID},
            {"$set": ps_doc}, upsert=True)

    # Payroll journal entry
    je_doc = {
        "entry_id": "je_payroll_2026_03",
        "entry_date": days_ago(1).strftime("%Y-%m-%d"),
        "reference_number": next_je_ref("JE-PAY"),
        "description": "Payroll - March 2026",
        "organization_id": ORG_ID,
        "created_by": OWNER["id"],
        "entry_type": "PAYROLL",
        "source_document_id": "SPR-2026-03",
        "source_document_type": "payroll",
        "reference_id": "SPR-2026-03",
        "reference_type": "payroll",
        "is_posted": True, "is_reversed": False,
        "lines": [
            jl("SALARY", debit=total_gross, desc="Salary Expense - March 2026"),
            jl("PF_PAY", credit=total_pf, desc="PF Payable"),
            jl("PT_PAY", credit=total_pt, desc="Professional Tax"),
            jl("TDS_PAY", credit=total_tds, desc="TDS Payable"),
            jl("SAL_PAY", credit=total_net, desc="Net Salary Payable"),
        ],
        "created_at": iso(days_ago(1)),
        "_seed": SEED_TAG,
    }
    await db.journal_entries.update_one(
        {"entry_id": je_doc["entry_id"], "organization_id": ORG_ID},
        {"$set": je_doc}, upsert=True)
    je_count += 1

    counts["payroll_runs"] = 1
    counts["payslips"] = len(PAYROLL_EMPLOYEES)
    print(f"  1 payroll run, {len(PAYROLL_EMPLOYEES)} payslips, 1 payroll JE")

    # ================================================================
    # SECTION M — AMC CONTRACTS (2)
    # ================================================================
    print("[M] Seeding 2 AMC contracts...")

    amc_defs = [
        {
            "subscription_id": "SAMC-001",
            "plan_name": "EV Fleet Care Pro",
            "customer_id": "CON-devfleet-006",
            "customer_name": "Delhi EV Fleet Pvt Ltd",
            "vehicle_model": "Bajaj Chetak",
            "vehicle_registration": "DL03IJ7890",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "status": "active",
            "monthly_amount": 2999,
        },
        {
            "subscription_id": "SAMC-002",
            "plan_name": "EV Basic Care",
            "customer_id": "CON-greenride-007",
            "customer_name": "GreenRide Logistics",
            "vehicle_model": "Mahindra XUV400",
            "vehicle_registration": "MH02KL1234",
            "start_date": "2025-05-01",
            "end_date": "2026-04-30",
            "status": "expiring_soon",
            "monthly_amount": 1999,
        },
    ]

    for amc in amc_defs:
        amc_doc = {
            **amc,
            "organization_id": ORG_ID,
            "plan_id": f"plan_{amc['subscription_id']}",
            "vehicle_category": "2W" if "Chetak" in amc["vehicle_model"] else "4W",
            "services_used": random.randint(1, 5),
            "created_at": iso(days_ago(60)),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
        }
        await db.amc_subscriptions.update_one(
            {"subscription_id": amc["subscription_id"], "organization_id": ORG_ID},
            {"$set": amc_doc}, upsert=True)

    counts["amc"] = 2
    print("  2 AMC contracts seeded")

    # ================================================================
    # SECTION N — EVFI DATA (for 5 closed tickets)
    # ================================================================
    print("[N] Seeding EVFI data (failure cards, patterns, learning queue)...")

    efi_count = 0
    for tdef in TICKET_DEFS[:5]:  # 5 closed tickets
        # Failure Card
        symptom_text = ", ".join(tdef["symptoms"])
        embedding = [random.uniform(-1, 1) for _ in range(256)]

        fc_doc = {
            "card_id": f"sfc_{tdef['id']}",
            "organization_id": ORG_ID,
            "ticket_id": tdef["id"],
            "fault_category": tdef["category"],
            "subsystem": tdef["category"],
            "symptom_cluster": symptom_text,
            "symptoms": tdef["symptoms"],
            "dtc_codes": tdef.get("dtc", []),
            "vehicle_make": tdef.get("vmake", ""),
            "vehicle_model": tdef.get("vmodel", ""),
            "vehicle_category": tdef.get("vtype", "2W"),
            "root_cause": tdef.get("resolution", ""),
            "probable_root_cause": tdef.get("resolution", ""),
            "parts_required": [p[1] for p in tdef.get("parts_used", [])],
            "estimated_repair_time_minutes": random.choice([30, 45, 60, 90, 120]),
            "confidence_score": round(random.uniform(0.7, 0.95), 2),
            "historical_success_rate": round(random.uniform(0.8, 0.98), 2),
            "recurrence_counter": random.randint(1, 5),
            "positive_feedback_count": random.randint(2, 8),
            "negative_feedback_count": 0,
            "scope": "tenant",
            "source_type": "field_discovery",
            "status": "approved",
            "first_detected_at": iso(days_ago(30)),
            "last_used_at": iso(days_ago(5)),
            "created_at": iso(days_ago(30)),
            "embedding_vector": embedding,
            "_seed": SEED_TAG,
        }
        await db.failure_cards.update_one(
            {"card_id": fc_doc["card_id"], "organization_id": ORG_ID},
            {"$set": fc_doc}, upsert=True)

        # EVFI Platform Pattern (anonymized)
        symptom_hash = hashlib.md5(symptom_text.encode()).hexdigest()[:16]
        pattern_doc = {
            "pattern_id": f"spat_{tdef['id']}",
            "pattern_key": f"{tdef.get('vmodel', 'Unknown')}:{symptom_hash}",
            "organization_id": ORG_ID,
            "vehicle_model": tdef.get("vmodel", ""),
            "symptom_hash": symptom_hash,
            "confirmed_fault": tdef.get("resolution", ""),
            "occurrence_count": random.randint(3, 15),
            "correct_count": random.randint(2, 10),
            "confidence_score": round(random.uniform(0.6, 0.9), 2),
            "first_seen": iso(days_ago(60)),
            "last_seen": iso(days_ago(5)),
            "_seed": SEED_TAG,
        }
        await db.efi_platform_patterns.update_one(
            {"pattern_id": pattern_doc["pattern_id"]},
            {"$set": pattern_doc}, upsert=True)

        # Learning Queue entry (processed)
        lq_doc = {
            "event_id": f"SLE-{tdef['id']}",
            "event_type": "ticket_closure",
            "ticket_id": tdef["id"],
            "organization_id": ORG_ID,
            "vehicle_make": tdef.get("vmake"),
            "vehicle_model": tdef.get("vmodel"),
            "vehicle_category": tdef.get("vtype", "2W"),
            "category": tdef["category"],
            "subsystem": tdef["category"],
            "symptoms": tdef["symptoms"],
            "dtc_codes": tdef.get("dtc", []),
            "actual_root_cause": tdef.get("resolution", ""),
            "parts_replaced": [p[1] for p in tdef.get("parts_used", [])],
            "repair_actions": [tdef.get("resolution", "")],
            "status": "completed",
            "processed_at": iso(days_ago(15)),
            "processing_result": {"success": True, "actions_taken": ["failure_card_created", "pattern_updated"]},
            "created_at": iso(days_ago(20)),
            "_seed": SEED_TAG,
        }
        await db.efi_learning_queue.update_one(
            {"event_id": lq_doc["event_id"], "organization_id": ORG_ID},
            {"$set": lq_doc}, upsert=True)

        efi_count += 1

    counts["failure_cards"] = efi_count
    counts["efi_patterns"] = efi_count
    counts["learning_queue"] = efi_count
    print(f"  {efi_count} failure cards, {efi_count} patterns, {efi_count} learning queue entries")

    # ================================================================
    # SUMMARY
    # ================================================================
    print("\n" + "=" * 60)
    print("SEED PART 2 COMPLETE — Summary:")
    print("=" * 60)
    for key, val in counts.items():
        print(f"  {key}: {val}")
    print(f"  total_journal_entries: {je_count}")

    # Verify
    print("\nDatabase counts (seeded records):")
    for col_name in ['tickets', 'ticket_estimates', 'estimate_line_items',
                     'ticket_invoices', 'journal_entries', 'payments_received',
                     'credit_notes', 'failure_cards', 'efi_platform_patterns',
                     'efi_learning_queue', 'payroll_runs', 'payroll_payslips',
                     'amc_subscriptions']:
        total = await db[col_name].count_documents({"organization_id": ORG_ID})
        seeded = await db[col_name].count_documents({"organization_id": ORG_ID, "_seed": SEED_TAG})
        print(f"  {col_name}: {total} total ({seeded} seeded)")

    # Show a sample journal entry
    print("\nSample journal entry (COGS):")
    sample = await db.journal_entries.find_one(
        {"organization_id": ORG_ID, "entry_type": "COGS", "_seed": SEED_TAG},
        {"_id": 0, "entry_id": 1, "description": 1, "lines": 1})
    if sample:
        print(f"  {sample['description']}")
        for line in sample.get("lines", []):
            dr = line.get("debit_amount", 0)
            cr = line.get("credit_amount", 0)
            side = f"DR {dr}" if dr else f"CR {cr}"
            print(f"    {line['account_code']} {line['account_name']}: {side}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
