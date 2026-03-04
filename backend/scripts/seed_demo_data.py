#!/usr/bin/env python3
"""
Volt Motors Demo Data Seed Script
==================================
IDEMPOTENT: Clears all demo-seeded data for Volt Motors, then re-seeds fresh.
ONLY touches organization_id = "demo-volt-motors-001".
Spread across 6 months with increasing activity.
"""

import asyncio
import os
import uuid
import random
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# ── Config ──
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_dev")
ORG_ID = "demo-volt-motors-001"
OWNER_USER_ID = "user-demo-owner-001"
SEED_TAG = "seed_demo_v2"  # Tag to identify seeded records for safe cleanup

def uid(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:12]}"

def iso(dt):
    return dt.isoformat()

# ── Time helpers: 6 months back from now ──
NOW = datetime.now(timezone.utc)
MONTH_STARTS = []
for i in range(6, 0, -1):
    m = NOW - timedelta(days=30 * i)
    MONTH_STARTS.append(m)

def random_date_in_month(month_idx):
    """month_idx: 0=oldest, 5=most recent"""
    base = MONTH_STARTS[month_idx]
    offset = random.randint(0, 28)
    hour = random.randint(8, 18)
    minute = random.randint(0, 59)
    return base + timedelta(days=offset, hours=hour - base.hour, minutes=minute)

# ── CONTACTS (18 customers + 3 vendors) ──
CUSTOMERS = [
    {"name": "Rajesh Kumar", "first_name": "Rajesh", "last_name": "Kumar", "phone": "9876543201", "email": "rajesh.kumar@gmail.com", "city": "Delhi", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Priya Singh", "first_name": "Priya", "last_name": "Singh", "phone": "9876543202", "email": "priya.singh@yahoo.com", "city": "Noida", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Vikram Patel", "first_name": "Vikram", "last_name": "Patel", "phone": "9876543203", "email": "vikram.patel@outlook.com", "city": "Mumbai", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Ananya Sharma", "first_name": "Ananya", "last_name": "Sharma", "phone": "9876543204", "email": "ananya.sharma@gmail.com", "city": "Bangalore", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Suresh Yadav", "first_name": "Suresh", "last_name": "Yadav", "phone": "9876543205", "email": "suresh.yadav@hotmail.com", "city": "Delhi", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Meera Nair", "first_name": "Meera", "last_name": "Nair", "phone": "9876543206", "email": "meera.nair@gmail.com", "city": "Kochi", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Arun Joshi", "first_name": "Arun", "last_name": "Joshi", "phone": "9876543207", "email": "arun.joshi@gmail.com", "city": "Pune", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Deepa Menon", "first_name": "Deepa", "last_name": "Menon", "phone": "9876543208", "email": "deepa.menon@yahoo.com", "city": "Chennai", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Rohit Aggarwal", "first_name": "Rohit", "last_name": "Aggarwal", "phone": "9876543209", "email": "rohit.aggarwal@gmail.com", "city": "Delhi", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Kavita Deshmukh", "first_name": "Kavita", "last_name": "Deshmukh", "phone": "9876543210", "email": "kavita.d@gmail.com", "city": "Nagpur", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Mohammad Imran", "first_name": "Mohammad", "last_name": "Imran", "phone": "9876543211", "email": "imran.m@gmail.com", "city": "Lucknow", "customer_type": "individual", "gst_treatment": "consumer"},
    {"name": "Sneha Kulkarni", "first_name": "Sneha", "last_name": "Kulkarni", "phone": "9876543212", "email": "sneha.k@outlook.com", "city": "Pune", "customer_type": "individual", "gst_treatment": "consumer"},
    # Fleet companies
    {"name": "GreenFleet Logistics Pvt Ltd", "first_name": "GreenFleet", "last_name": "Logistics", "phone": "9876543213", "email": "fleet@greenfleet.in", "city": "Delhi", "customer_type": "business", "gst_treatment": "registered", "company_name": "GreenFleet Logistics Pvt Ltd", "gstin": "07AABCG1234F1Z5"},
    {"name": "Zomato Delivery Hub - Saket", "first_name": "Zomato", "last_name": "Hub", "phone": "9876543214", "email": "evfleet@zomato.com", "city": "Delhi", "customer_type": "business", "gst_treatment": "registered", "company_name": "Zomato Delivery Hub", "gstin": "07AABCZ5678G1ZP"},
    {"name": "Swiggy EV Fleet - Koramangala", "first_name": "Swiggy", "last_name": "Fleet", "phone": "9876543215", "email": "evops@swiggy.com", "city": "Bangalore", "customer_type": "business", "gst_treatment": "registered", "company_name": "Swiggy EV Fleet", "gstin": "29AABCS9012H1Z3"},
    {"name": "BlueDart EV Division", "first_name": "BlueDart", "last_name": "EV", "phone": "9876543216", "email": "ev@bluedart.com", "city": "Mumbai", "customer_type": "business", "gst_treatment": "registered", "company_name": "BlueDart EV Division", "gstin": "27AABCB3456I1Z7"},
    {"name": "Rapido Bike Taxi", "first_name": "Rapido", "last_name": "BikeT", "phone": "9876543217", "email": "fleet@rapido.bike", "city": "Hyderabad", "customer_type": "business", "gst_treatment": "registered", "company_name": "Rapido Bike Taxi", "gstin": "36AABCR7890J1Z1"},
    {"name": "Nandini Reddy", "first_name": "Nandini", "last_name": "Reddy", "phone": "9876543218", "email": "nandini.r@gmail.com", "city": "Hyderabad", "customer_type": "individual", "gst_treatment": "consumer"},
]

VENDORS = [
    {"name": "EV Parts India", "first_name": "EV Parts", "last_name": "India", "phone": "9800000001", "email": "sales@evpartsindia.com", "city": "Delhi", "company_name": "EV Parts India Pvt Ltd", "gstin": "07AABCE1234K1Z9"},
    {"name": "BatteryWala Enterprises", "first_name": "BatteryWala", "last_name": "Ent", "phone": "9800000002", "email": "orders@batterywala.in", "city": "Mumbai", "company_name": "BatteryWala Enterprises", "gstin": "27AABCB9876L1Z5"},
    {"name": "GreenDrive Components", "first_name": "GreenDrive", "last_name": "Comp", "phone": "9800000003", "email": "supply@greendrive.co.in", "city": "Pune", "company_name": "GreenDrive Components LLP", "gstin": "27AABCG5432M1Z2"},
]

# ── VEHICLES (25) ──
VEHICLE_DEFS = [
    ("Ola", "S1 Pro", "2W", 2024), ("Ola", "S1 Pro", "2W", 2023),
    ("Ather", "450X", "2W", 2024), ("Ather", "450X", "2W", 2023), ("Ather", "450S", "2W", 2024),
    ("TVS", "iQube", "2W", 2024), ("TVS", "iQube ST", "2W", 2023),
    ("Bajaj", "Chetak", "2W", 2024), ("Bajaj", "Chetak", "2W", 2023),
    ("Revolt", "RV400", "2W", 2024), ("Revolt", "RV400", "2W", 2023),
    ("Hero", "Vida V1", "2W", 2024),
    ("Tata", "Nexon EV", "4W", 2024), ("Tata", "Nexon EV Max", "4W", 2023),
    ("Tata", "Tiago EV", "4W", 2024),
    ("MG", "ZS EV", "4W", 2023), ("MG", "Comet EV", "4W", 2024),
    ("Mahindra", "XUV400", "4W", 2024),
    ("Ola", "S1 Air", "2W", 2024),
    ("Ather", "Rizta", "2W", 2024),
    ("TVS", "iQube S", "2W", 2023),
    ("Bajaj", "Chetak Premium", "2W", 2024),
    ("Piaggio", "Ape E-City", "3W", 2023),
    ("Mahindra", "Treo", "3W", 2024),
    ("Euler", "HiLoad", "3W", 2023),
]

REG_PREFIXES = ["MH01", "MH02", "DL01", "DL02", "KA01", "KA03", "TN01", "UP16"]
COLORS = ["White", "Black", "Grey", "Red", "Blue", "Green"]

# ── INVENTORY ITEMS (20 parts) ──
PARTS = [
    {"name": "Lithium Cell Module 48V", "sku": "LCM-48V-01", "hsn": "85076000", "cat": "Battery", "purchase": 8500, "sell": 12000, "tax": 18, "stock": 15, "unit": "nos"},
    {"name": "BMS Board - 16S", "sku": "BMS-16S-02", "hsn": "85389000", "cat": "Battery", "purchase": 3200, "sell": 4800, "tax": 18, "stock": 20, "unit": "nos"},
    {"name": "BLDC Motor Controller 72V", "sku": "MCU-72V-01", "hsn": "85044090", "cat": "Controller", "purchase": 6500, "sell": 9500, "tax": 18, "stock": 8, "unit": "nos"},
    {"name": "DC-DC Converter 48V-12V", "sku": "DCDC-4812-01", "hsn": "85044090", "cat": "Electrical", "purchase": 1800, "sell": 2800, "tax": 18, "stock": 12, "unit": "nos"},
    {"name": "Onboard Charger Module 3.3kW", "sku": "OBC-33KW-01", "hsn": "85044090", "cat": "Charging", "purchase": 5500, "sell": 8200, "tax": 18, "stock": 6, "unit": "nos"},
    {"name": "Wiring Harness - Main Loom", "sku": "WH-MAIN-01", "hsn": "85441900", "cat": "Electrical", "purchase": 1200, "sell": 2000, "tax": 18, "stock": 10, "unit": "set"},
    {"name": "EV Brake Pad Set (Front)", "sku": "BRK-FRT-01", "hsn": "68132090", "cat": "Braking", "purchase": 350, "sell": 600, "tax": 28, "stock": 30, "unit": "set"},
    {"name": "EV Brake Pad Set (Rear)", "sku": "BRK-RR-01", "hsn": "68132090", "cat": "Braking", "purchase": 300, "sell": 500, "tax": 28, "stock": 25, "unit": "set"},
    {"name": "Suspension Bush Kit", "sku": "SUS-BSH-01", "hsn": "40169990", "cat": "Suspension", "purchase": 450, "sell": 750, "tax": 28, "stock": 18, "unit": "kit"},
    {"name": "TFT Display Unit", "sku": "DSP-TFT-01", "hsn": "85285900", "cat": "Electronics", "purchase": 3800, "sell": 5500, "tax": 18, "stock": 5, "unit": "nos"},
    {"name": "Throttle Assembly", "sku": "THR-ASM-01", "hsn": "87089900", "cat": "Motor", "purchase": 800, "sell": 1400, "tax": 28, "stock": 14, "unit": "nos"},
    {"name": "Motor Bearing Set", "sku": "BRG-MOT-01", "hsn": "84821090", "cat": "Motor", "purchase": 420, "sell": 750, "tax": 18, "stock": 22, "unit": "set"},
    {"name": "Contactor Relay 200A", "sku": "CTR-200A-01", "hsn": "85364900", "cat": "Electrical", "purchase": 950, "sell": 1500, "tax": 18, "stock": 10, "unit": "nos"},
    {"name": "Charging Port Assembly", "sku": "CPA-01", "hsn": "85366990", "cat": "Charging", "purchase": 1600, "sell": 2500, "tax": 18, "stock": 8, "unit": "nos"},
    {"name": "Coolant Pump - BLDC", "sku": "CLP-BLDC-01", "hsn": "84138190", "cat": "Cooling", "purchase": 2200, "sell": 3500, "tax": 18, "stock": 6, "unit": "nos"},
    {"name": "Thermal Pad Pack (10pcs)", "sku": "TPD-10-01", "hsn": "39269099", "cat": "Battery", "purchase": 350, "sell": 600, "tax": 18, "stock": 40, "unit": "pack"},
    {"name": "CAN Bus Diagnostic Cable", "sku": "CAN-DG-01", "hsn": "85444299", "cat": "Electronics", "purchase": 650, "sell": 1100, "tax": 18, "stock": 7, "unit": "nos"},
    {"name": "Fuse Box Assembly 60A", "sku": "FUS-60A-01", "hsn": "85351000", "cat": "Electrical", "purchase": 380, "sell": 650, "tax": 18, "stock": 15, "unit": "nos"},
    {"name": "Regenerative Brake Module", "sku": "RGN-BRK-01", "hsn": "85044090", "cat": "Braking", "purchase": 4200, "sell": 6500, "tax": 18, "stock": 4, "unit": "nos"},
    {"name": "Key Fob / Immobilizer Unit", "sku": "KEY-IMM-01", "hsn": "85269200", "cat": "Electronics", "purchase": 1100, "sell": 1800, "tax": 18, "stock": 9, "unit": "nos"},
]

# ── EMPLOYEES (4 techs + 1 manager) ──
EMPLOYEES = [
    {"first_name": "Ravi", "last_name": "Sharma", "designation": "Lead EV Technician", "role": "technician", "phone": "9911001001", "skill": "Battery + BMS specialist"},
    {"first_name": "Deepak", "last_name": "Verma", "designation": "EV Technician", "role": "technician", "phone": "9911001002", "skill": "Motor + controller diagnostics"},
    {"first_name": "Sunita", "last_name": "Rao", "designation": "EV Technician", "role": "technician", "phone": "9911001003", "skill": "Electrical + charging systems"},
    {"first_name": "Ajay", "last_name": "Tiwari", "designation": "Junior Technician", "role": "technician", "phone": "9911001004", "skill": "General EV maintenance"},
    {"first_name": "Neha", "last_name": "Gupta", "designation": "Workshop Manager", "role": "admin", "phone": "9911001005", "skill": "Operations + scheduling"},
]

# ── TICKET TEMPLATES ──
TICKET_TEMPLATES = [
    {"title": "Battery not charging above 80%", "desc": "Customer reports battery stuck at 80%. SOC gauge shows full but actual range is 60% of rated.", "cat": "battery", "priority": "high", "codes": ["E401"]},
    {"title": "Motor making grinding noise at low speed", "desc": "Grinding noise from motor at speeds below 20 kmph. Noise disappears at higher speeds.", "cat": "motor", "priority": "medium", "codes": []},
    {"title": "Charger shows error E201 — no charging", "desc": "Onboard charger flashes red LED, error E201. Tried multiple outlets, same result.", "cat": "charging", "priority": "high", "codes": ["E201"]},
    {"title": "BMS error — cell voltage imbalance", "desc": "Dashboard shows BMS warning. Cells 3 and 7 showing 0.3V delta. Range dropping fast.", "cat": "battery", "priority": "critical", "codes": ["E501", "E502"]},
    {"title": "Display unit blank / flickering", "desc": "TFT display goes blank intermittently. Sometimes shows garbled data on startup.", "cat": "electrical", "priority": "medium", "codes": []},
    {"title": "Throttle response lag — 2 second delay", "desc": "Throttle has noticeable 2-second delay. Vehicle jerks on acceleration.", "cat": "motor", "priority": "high", "codes": ["E301"]},
    {"title": "Brake squeal — front disc", "desc": "High pitched squeal from front brakes during normal braking. Gets worse when wet.", "cat": "mechanical", "priority": "low", "codes": []},
    {"title": "Range dropped from 100km to 55km", "desc": "Vehicle barely does 55km on full charge. Was getting 100km 3 months ago. 18 months old.", "cat": "battery", "priority": "high", "codes": []},
    {"title": "DC-DC converter failure — 12V system dead", "desc": "All 12V accessories dead. Headlights, horn, indicators not working. Main battery OK.", "cat": "electrical", "priority": "critical", "codes": ["E601"]},
    {"title": "Controller overheating in traffic", "desc": "Controller thermal cutoff triggers in heavy traffic. Vehicle goes into limp mode.", "cat": "motor", "priority": "high", "codes": ["E302", "E303"]},
    {"title": "Charging port loose connection", "desc": "Charging cable keeps disconnecting. Port feels loose. Sometimes sparks visible.", "cat": "charging", "priority": "medium", "codes": []},
    {"title": "Suspension noise on speed bumps", "desc": "Clunking noise from front suspension on bumps. Bushings may be worn.", "cat": "mechanical", "priority": "low", "codes": []},
    {"title": "CAN bus communication fault", "desc": "Multiple systems showing intermittent errors. Suspect CAN bus wiring issue.", "cat": "electrical", "priority": "critical", "codes": ["E701", "E702"]},
    {"title": "Motor vibration at 40-50 kmph", "desc": "Noticeable vibration in the 40-50 kmph range. Smooth outside that range.", "cat": "motor", "priority": "medium", "codes": []},
    {"title": "Slow charging — takes 8 hours instead of 4", "desc": "Charging time doubled. Customer charges overnight but not reaching 100%.", "cat": "charging", "priority": "medium", "codes": ["E202"]},
    {"title": "Key fob not detected", "desc": "Keyless start not recognizing fob. Have to use manual override every time.", "cat": "electrical", "priority": "low", "codes": []},
    {"title": "Regen braking not working", "desc": "Regenerative braking completely stopped. No energy recovery shown on dashboard.", "cat": "braking", "priority": "high", "codes": ["E801"]},
    {"title": "Battery thermal runaway warning", "desc": "Thermal warning on dashboard during fast charge. Battery temp hitting 55C.", "cat": "battery", "priority": "critical", "codes": ["E503", "E504"]},
    {"title": "Motor stall at startup", "desc": "Motor stalls when starting from standstill. Have to try 2-3 times.", "cat": "motor", "priority": "high", "codes": ["E304"]},
    {"title": "Headlight flickering", "desc": "Both headlights flicker at random. DC-DC output may be unstable.", "cat": "electrical", "priority": "low", "codes": []},
    {"title": "AMC service — periodic checkup", "desc": "Scheduled AMC maintenance visit. Full diagnostic + fluid check.", "cat": "mechanical", "priority": "low", "codes": []},
    {"title": "Fleet vehicle — battery health audit", "desc": "Quarterly battery health check for fleet vehicle. Check SOH, cell balance, temps.", "cat": "battery", "priority": "medium", "codes": []},
    {"title": "Coolant leak near motor housing", "desc": "Small coolant puddle under vehicle after parking. Leak near motor housing seal.", "cat": "cooling", "priority": "high", "codes": []},
    {"title": "Software update required — firmware v3.2", "desc": "OEM advisory: firmware update v3.2 fixes throttle mapping and BMS calibration.", "cat": "software", "priority": "medium", "codes": []},
    {"title": "Contactor relay clicking — not engaging", "desc": "Main contactor relay clicks but doesn't engage. Vehicle won't power on.", "cat": "electrical", "priority": "critical", "codes": ["E603"]},
]

RESOLUTIONS = [
    "Replaced BMS module. Re-calibrated cells. Charging normal now.",
    "Motor bearings replaced. Test ride 10km — no noise.",
    "Onboard charger module swapped. Charging verified on AC and DC.",
    "Cell balancing performed. Delta reduced to 0.02V. Monitoring.",
    "Display ribbon cable re-seated. Firmware updated. Working fine.",
    "Throttle sensor replaced. Response time now under 100ms.",
    "Front brake pads replaced. Rotor cleaned. No squeal.",
    "Battery pack cells 3,7 replaced. SOH back to 94%. Range restored.",
    "DC-DC converter replaced. All 12V systems working.",
    "Controller heat sink cleaned. Thermal paste reapplied. Temp normal.",
    "Charging port assembly replaced. Secure connection verified.",
    "Front suspension bushings replaced. No noise on bumps.",
    "CAN bus harness repaired. All systems communicating normally.",
    "Motor balanced. Vibration eliminated. Test ride smooth.",
    "Charger module capacitor replaced. Charge time back to 4hrs.",
    "Key fob battery replaced + receiver antenna cleaned.",
    "Regen brake controller reflashed. Energy recovery working.",
    "Thermal pads replaced. Fast charge temp stays below 42C.",
    "Motor controller firmware updated. Startup reliable now.",
    "DC-DC output stabilized. Headlights steady.",
    "Coolant pump seal replaced. No leak after 48hr test.",
    "Firmware v3.2 flashed. Throttle smoother. BMS calibrated.",
    "Contactor relay replaced. Vehicle powers on normally.",
]

# ── Distribution: tickets per month (growing business) ──
TICKETS_PER_MONTH = [3, 5, 6, 8, 10, 13]  # total = 45

async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print(f"\n{'='*60}")
    print(f"  VOLT MOTORS DEMO DATA SEED")
    print(f"  Org: {ORG_ID}")
    print(f"  DB:  {DB_NAME}")
    print(f"{'='*60}\n")

    # ── STEP 0: Clear previous demo-seeded data ──
    print("[CLEANUP] Removing previous seed data...")
    seed_filter = {"organization_id": ORG_ID, "_seed": SEED_TAG}
    collections_to_clean = [
        "contacts", "vehicles", "items", "inventory", "employees",
        "tickets", "ticket_activities", "invoices", "estimates",
        "bills", "amc_plans", "amc_subscriptions", "journal_entries"
    ]
    for coll_name in collections_to_clean:
        result = await db[coll_name].delete_many(seed_filter)
        if result.deleted_count > 0:
            print(f"  Cleared {result.deleted_count} from {coll_name}")
    print("[CLEANUP] Done.\n")

    counts = {}

    # ── STEP 1: Contacts ──
    print("[1/9] Seeding contacts...")
    contact_ids = []
    vendor_ids = []
    contact_docs = []
    for i, c in enumerate(CUSTOMERS):
        cid = f"seed-cont-{uid()}"
        doc = {
            "contact_id": cid,
            "organization_id": ORG_ID,
            "name": c["name"],
            "first_name": c["first_name"],
            "last_name": c["last_name"],
            "email": c["email"],
            "phone": c["phone"],
            "mobile": c["phone"],
            "city": c["city"],
            "contact_type": "customer",
            "customer_type": c["customer_type"],
            "company_name": c.get("company_name", ""),
            "gstin": c.get("gstin", ""),
            "gst_treatment": c["gst_treatment"],
            "currency_code": "INR",
            "payment_terms": 15 if c["customer_type"] == "individual" else 30,
            "status": "active",
            "outstanding_receivable": 0,
            "unused_credits": 0,
            "source": "direct",
            "tags": ["demo-seed"],
            "created_at": iso(NOW - timedelta(days=random.randint(90, 180))),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
        }
        contact_docs.append(doc)
        contact_ids.append(cid)

    for v in VENDORS:
        vid = f"seed-vend-{uid()}"
        doc = {
            "contact_id": vid,
            "organization_id": ORG_ID,
            "name": v["name"],
            "first_name": v["first_name"],
            "last_name": v["last_name"],
            "email": v["email"],
            "phone": v["phone"],
            "mobile": v["phone"],
            "city": v["city"],
            "contact_type": "vendor",
            "customer_type": "business",
            "company_name": v["company_name"],
            "gstin": v["gstin"],
            "gst_treatment": "registered",
            "currency_code": "INR",
            "payment_terms": 30,
            "status": "active",
            "source": "direct",
            "tags": ["demo-seed"],
            "created_at": iso(NOW - timedelta(days=200)),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
        }
        contact_docs.append(doc)
        vendor_ids.append(vid)

    await db.contacts.insert_many(contact_docs)
    counts["contacts"] = len(contact_docs)
    print(f"  {len(contact_docs)} contacts ({len(contact_ids)} customers + {len(vendor_ids)} vendors)")

    # ── STEP 2: Vehicles ──
    print("[2/9] Seeding vehicles...")
    vehicle_docs = []
    vehicle_ids = []
    for i, (make, model, cat, year) in enumerate(VEHICLE_DEFS):
        vid = f"seed-vh-{uid()}"
        prefix = random.choice(REG_PREFIXES)
        reg = f"{prefix}EV{random.randint(1000, 9999)}"
        vin_str = f"VIN{uuid.uuid4().hex[:10].upper()}"
        owner_contact = contact_ids[i % len(contact_ids)]
        doc = {
            "vehicle_id": vid,
            "organization_id": ORG_ID,
            "make": make,
            "model": f"{make} {model}",
            "category": cat,
            "year": year,
            "registration_number": reg,
            "vin": vin_str,
            "color": random.choice(COLORS),
            "contact_id": owner_contact,
            "odometer_km": random.randint(2000, 35000),
            "status": "active",
            "created_at": iso(NOW - timedelta(days=random.randint(30, 180))),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
        }
        vehicle_docs.append(doc)
        vehicle_ids.append(vid)

    await db.vehicles.insert_many(vehicle_docs)
    counts["vehicles"] = len(vehicle_docs)
    print(f"  {len(vehicle_docs)} vehicles")

    # ── STEP 3: Inventory Items ──
    print("[3/9] Seeding inventory items...")
    item_docs = []
    item_ids = []
    for p in PARTS:
        iid = f"seed-item-{uid()}"
        doc = {
            "item_id": iid,
            "organization_id": ORG_ID,
            "name": p["name"],
            "sku": p["sku"],
            "description": p["name"],
            "hsn_sac_code": p["hsn"],
            "item_type": "inventory",
            "product_type": "goods",
            "category": p["cat"],
            "rate": p["sell"],
            "sales_rate": p["sell"],
            "purchase_rate": p["purchase"],
            "unit": p["unit"],
            "stock_on_hand": p["stock"],
            "opening_stock": p["stock"],
            "reorder_level": max(3, p["stock"] // 4),
            "tax_rate": p["tax"],
            "intra_state_tax_rate": p["tax"],
            "inter_state_tax_rate": p["tax"],
            "taxable": True,
            "status": "active",
            "track_inventory": True,
            "sellable": True,
            "purchasable": True,
            "currency_code": "INR",
            "created_at": iso(NOW - timedelta(days=180)),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
        }
        item_docs.append(doc)
        item_ids.append(iid)

    await db.items.insert_many(item_docs)
    counts["items"] = len(item_docs)
    print(f"  {len(item_docs)} inventory items")

    # ── STEP 4: Employees ──
    print("[4/9] Seeding employees...")
    emp_docs = []
    emp_ids = []
    for e in EMPLOYEES:
        eid = f"seed-emp-{uid()}"
        doc = {
            "employee_id": eid,
            "organization_id": ORG_ID,
            "first_name": e["first_name"],
            "last_name": e["last_name"],
            "name": f"{e['first_name']} {e['last_name']}",
            "email": f"{e['first_name'].lower()}.{e['last_name'].lower()}@voltmotors.in",
            "phone": e["phone"],
            "department": "Service",
            "designation": e["designation"],
            "employment_type": "full_time",
            "system_role": e["role"],
            "status": "active",
            "date_of_joining": "2025-06-01",
            "work_state_code": "DL",
            "state": "Delhi",
            "skills": e["skill"],
            "created_at": iso(NOW - timedelta(days=270)),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
        }
        emp_docs.append(doc)
        emp_ids.append(eid)

    await db.employees.insert_many(emp_docs)
    counts["employees"] = len(emp_docs)
    tech_ids = emp_ids[:4]  # first 4 are technicians
    print(f"  {len(emp_docs)} employees (4 techs + 1 manager)")

    # ── STEP 5: Tickets ──
    print("[5/9] Seeding tickets...")
    ticket_docs = []
    ticket_ids_all = []
    ticket_meta = []  # (ticket_id, status, contact_id, vehicle_idx, month_idx, created_at, template_idx)
    template_idx = 0

    for month_idx in range(6):
        n_tickets = TICKETS_PER_MONTH[month_idx]
        for _ in range(n_tickets):
            tpl = TICKET_TEMPLATES[template_idx % len(TICKET_TEMPLATES)]
            template_idx += 1
            tid = f"seed-tkt-{uid()}"
            contact_idx = random.randint(0, len(contact_ids) - 1)
            vh_idx = random.randint(0, len(vehicle_ids) - 1)
            vh = vehicle_docs[vh_idx]
            cust = contact_docs[contact_idx]
            tech = random.choice(tech_ids)
            tech_name = next(e["name"] for e in emp_docs if e["employee_id"] == tech)

            created = random_date_in_month(month_idx)

            # Status distribution: 60% resolved, 20% in_progress, 10% open, 10% cancelled
            roll = random.random()
            if month_idx <= 3:
                # Older months: mostly resolved
                if roll < 0.85:
                    status = "resolved"
                elif roll < 0.95:
                    status = "closed"
                else:
                    status = "cancelled"
            elif month_idx == 4:
                if roll < 0.60:
                    status = "resolved"
                elif roll < 0.80:
                    status = "in_progress"
                elif roll < 0.90:
                    status = "open"
                else:
                    status = "cancelled"
            else:
                # Most recent month
                if roll < 0.45:
                    status = "resolved"
                elif roll < 0.70:
                    status = "in_progress"
                elif roll < 0.90:
                    status = "open"
                else:
                    status = "cancelled"

            resolved_at = None
            resolution = None
            if status in ("resolved", "closed"):
                resolved_at = created + timedelta(days=random.randint(1, 5), hours=random.randint(1, 8))
                resolution = RESOLUTIONS[template_idx % len(RESOLUTIONS)]

            parts_cost = random.choice([0, 500, 1200, 2500, 4800, 8500, 12000, 3200])
            labor_cost = random.choice([300, 500, 800, 1200, 1500, 2000])
            actual_cost = parts_cost + labor_cost if status in ("resolved", "closed") else 0

            doc = {
                "ticket_id": tid,
                "organization_id": ORG_ID,
                "title": tpl["title"],
                "description": tpl["desc"],
                "status": status,
                "priority": tpl["priority"],
                "category": tpl["cat"],
                "ticket_type": "workshop",
                "customer_id": contact_ids[contact_idx],
                "customer_name": cust["name"],
                "customer_type": cust["customer_type"],
                "contact_number": cust["phone"],
                "vehicle_id": vehicle_ids[vh_idx],
                "vehicle_type": vh["model"],
                "vehicle_make": vh["make"],
                "vehicle_model": vh["model"],
                "vehicle_number": vh["registration_number"],
                "vehicle_category": vh["category"],
                "assigned_technician_id": tech,
                "assigned_technician_name": tech_name,
                "error_codes_reported": tpl["codes"],
                "estimated_cost": actual_cost * 1.1 if actual_cost else random.choice([2000, 5000, 8000]),
                "actual_cost": actual_cost,
                "parts_cost": parts_cost if status in ("resolved", "closed") else 0,
                "labor_cost": labor_cost if status in ("resolved", "closed") else 0,
                "resolution": resolution,
                "resolution_notes": resolution,
                "resolution_outcome": "success" if status == "resolved" else None,
                "resolved_at": iso(resolved_at) if resolved_at else None,
                "closed_at": iso(resolved_at) if status == "closed" else None,
                "suggested_failure_cards": [],
                "selected_failure_card": None,
                "ai_match_performed": False,
                "has_sales_order": False,
                "has_invoice": status == "resolved",
                "invoice_id": None,
                "status_history": [{"status": "open", "timestamp": iso(created), "updated_by": "System"}],
                "created_at": iso(created),
                "updated_at": iso(resolved_at or created),
                "created_by": OWNER_USER_ID,
                "_seed": SEED_TAG,
            }
            ticket_docs.append(doc)
            ticket_ids_all.append(tid)
            ticket_meta.append({
                "tid": tid, "status": status, "contact_id": contact_ids[contact_idx],
                "vehicle_idx": vh_idx, "month_idx": month_idx, "created_at": created,
                "template_idx": (template_idx - 1) % len(TICKET_TEMPLATES),
                "parts_cost": parts_cost, "labor_cost": labor_cost,
                "actual_cost": actual_cost, "customer_name": cust["name"],
                "vehicle_reg": vh["registration_number"],
            })

    await db.tickets.insert_many(ticket_docs)
    counts["tickets"] = len(ticket_docs)
    resolved_tickets = [m for m in ticket_meta if m["status"] in ("resolved", "closed")]
    open_tickets = [m for m in ticket_meta if m["status"] == "open"]
    ip_tickets = [m for m in ticket_meta if m["status"] == "in_progress"]
    print(f"  {len(ticket_docs)} tickets (resolved={len(resolved_tickets)}, in_progress={len(ip_tickets)}, open={len(open_tickets)})")

    # ── STEP 6: Invoices (for resolved tickets) ──
    print("[6/9] Seeding invoices...")
    invoice_docs = []
    journal_docs = []
    inv_num = 1

    for m in resolved_tickets:
        inv_id = f"seed-inv-{uid()}"
        inv_number = f"INV-SEED{str(inv_num).zfill(5)}"
        inv_num += 1

        # Build line items from ticket costs
        line_items = []
        if m["parts_cost"] > 0:
            part = random.choice(PARTS)
            qty = max(1, m["parts_cost"] // part["sell"])
            rate = part["sell"]
            amount = rate * qty
            tax_pct = part["tax"]
            tax_amt = round(amount * tax_pct / 100, 2)
            line_items.append({
                "line_item_id": f"LI-{uid()}",
                "type": "part",
                "name": part["name"],
                "description": part["name"],
                "item_id": item_ids[PARTS.index(part)],
                "hsn_sac_code": part["hsn"],
                "quantity": qty,
                "rate": rate,
                "amount": amount,
                "tax_percentage": tax_pct,
                "tax_amount": tax_amt,
            })

        labor_rate = m["labor_cost"]
        if labor_rate > 0:
            line_items.append({
                "line_item_id": f"LI-{uid()}",
                "type": "labor",
                "name": "Service Labor Charge",
                "description": "EV diagnostic and repair labor",
                "quantity": 1,
                "rate": labor_rate,
                "amount": labor_rate,
                "tax_percentage": 18,
                "tax_amount": round(labor_rate * 0.18, 2),
            })

        subtotal = sum(li["amount"] for li in line_items)
        tax_total = sum(li["tax_amount"] for li in line_items)
        cgst = round(tax_total / 2, 2)
        sgst = round(tax_total / 2, 2)
        total = round(subtotal + tax_total, 2)

        inv_date = m["created_at"] + timedelta(days=random.randint(1, 3))
        due_date = inv_date + timedelta(days=15)

        doc = {
            "invoice_id": inv_id,
            "invoice_number": inv_number,
            "organization_id": ORG_ID,
            "customer_id": m["contact_id"],
            "customer_name": m["customer_name"],
            "ticket_id": m["tid"],
            "invoice_date": inv_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "status": "paid",
            "payment_status": "paid",
            "line_items": line_items,
            "subtotal": subtotal,
            "tax_amount": tax_total,
            "cgst_amount": cgst,
            "sgst_amount": sgst,
            "igst_amount": 0,
            "total_amount": total,
            "amount_paid": total,
            "amount_due": 0,
            "currency_code": "INR",
            "place_of_supply": "07",
            "payment_terms": 15,
            "notes": f"Service invoice for ticket {m['tid']}",
            "vehicle_number": m["vehicle_reg"],
            "created_at": iso(inv_date),
            "updated_at": iso(inv_date),
            "_seed": SEED_TAG,
        }
        invoice_docs.append(doc)

        # Update ticket with invoice_id
        await db.tickets.update_one(
            {"ticket_id": m["tid"], "organization_id": ORG_ID},
            {"$set": {"invoice_id": inv_id, "has_invoice": True}}
        )

        # Journal entry (double-entry)
        je_id = f"seed-je-{uid()}"
        journal_docs.append({
            "entry_id": je_id,
            "entry_date": inv_date.strftime("%Y-%m-%d"),
            "reference_number": inv_number,
            "description": f"Revenue from invoice {inv_number} — {m['customer_name']}",
            "organization_id": ORG_ID,
            "created_by": OWNER_USER_ID,
            "entry_type": "INVOICE",
            "source_document_id": inv_id,
            "source_document_type": "INVOICE",
            "is_posted": True,
            "is_reversed": False,
            "lines": [
                {"line_id": f"jel_{uid()}", "account_name": "Accounts Receivable", "debit": total, "credit": 0},
                {"line_id": f"jel_{uid()}", "account_name": "Service Revenue", "debit": 0, "credit": subtotal},
                {"line_id": f"jel_{uid()}", "account_name": "CGST Output", "debit": 0, "credit": cgst},
                {"line_id": f"jel_{uid()}", "account_name": "SGST Output", "debit": 0, "credit": sgst},
            ],
            "total_debit": total,
            "total_credit": total,
            "created_at": iso(inv_date),
            "updated_at": "",
            "_seed": SEED_TAG,
        })

    if invoice_docs:
        await db.invoices.insert_many(invoice_docs)
    if journal_docs:
        await db.journal_entries.insert_many(journal_docs)
    counts["invoices"] = len(invoice_docs)
    counts["journal_entries"] = len(journal_docs)
    print(f"  {len(invoice_docs)} invoices + {len(journal_docs)} journal entries")

    # ── STEP 7: Estimates (for open + in_progress tickets) ──
    print("[7/9] Seeding estimates...")
    estimate_docs = []
    est_candidates = open_tickets + ip_tickets
    for m in est_candidates[:10]:
        est_id = f"seed-est-{uid()}"
        part = random.choice(PARTS)
        labor = random.choice([500, 800, 1200, 1500])
        qty = random.randint(1, 3)
        part_amount = part["sell"] * qty
        part_tax = round(part_amount * part["tax"] / 100, 2)
        labor_tax = round(labor * 0.18, 2)
        sub = part_amount + labor
        tax = part_tax + labor_tax
        grand = round(sub + tax, 2)

        doc = {
            "estimate_id": est_id,
            "ticket_id": m["tid"],
            "organization_id": ORG_ID,
            "status": "draft",
            "line_items": [
                {"line_item_id": f"LI-{uid()}", "type": "part", "name": part["name"], "description": part["name"],
                 "quantity": qty, "rate": part["sell"], "amount": part_amount,
                 "tax_percentage": part["tax"], "tax_amount": part_tax},
                {"line_item_id": f"LI-{uid()}", "type": "labor", "name": "Diagnostic + Repair Labor",
                 "description": "EV service labor", "quantity": 1, "rate": labor, "amount": labor,
                 "tax_percentage": 18, "tax_amount": labor_tax},
            ],
            "sub_total": sub,
            "tax_total": tax,
            "grand_total": grand,
            "created_at": iso(m["created_at"]),
            "created_by": OWNER_USER_ID,
            "updated_at": iso(m["created_at"]),
            "_seed": SEED_TAG,
        }
        estimate_docs.append(doc)

    if estimate_docs:
        await db.estimates.insert_many(estimate_docs)
    counts["estimates"] = len(estimate_docs)
    print(f"  {len(estimate_docs)} estimates")

    # ── STEP 8: Bills (supplier procurement) ──
    print("[8/9] Seeding bills...")
    bill_docs = []
    bill_journals = []
    bill_num = 1

    for i in range(12):
        vendor_idx = i % len(vendor_ids)
        vendor = next(c for c in contact_docs if c["contact_id"] == vendor_ids[vendor_idx])
        bill_id = f"seed-bill-{uid()}"
        bill_number = f"BILL-SEED{str(bill_num).zfill(4)}"
        bill_num += 1

        # 1-3 line items per bill
        n_items = random.randint(1, 3)
        chosen_parts = random.sample(PARTS, min(n_items, len(PARTS)))
        line_items = []
        for p in chosen_parts:
            qty = random.randint(3, 15)
            rate = p["purchase"]
            amount = rate * qty
            tax_pct = p["tax"]
            tax_amt = round(amount * tax_pct / 100, 2)
            line_items.append({
                "line_item_id": f"BLI-{uid()}",
                "name": p["name"],
                "description": p["name"],
                "hsn_sac_code": p["hsn"],
                "quantity": qty,
                "rate": rate,
                "amount": amount,
                "tax_percentage": tax_pct,
                "tax_amount": tax_amt,
            })

        subtotal = sum(li["amount"] for li in line_items)
        tax_total = sum(li["tax_amount"] for li in line_items)
        cgst = round(tax_total / 2, 2)
        sgst = round(tax_total / 2, 2)
        grand = round(subtotal + tax_total, 2)

        month_idx = i % 6
        bill_date = random_date_in_month(month_idx)
        due_date = bill_date + timedelta(days=30)

        paid = random.random() < 0.6
        doc = {
            "bill_id": bill_id,
            "bill_number": bill_number,
            "organization_id": ORG_ID,
            "vendor_id": vendor_ids[vendor_idx],
            "vendor_name": vendor["name"],
            "vendor_gstin": vendor.get("gstin", ""),
            "bill_date": bill_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "payment_terms": 30,
            "is_inclusive_tax": False,
            "reverse_charge": False,
            "line_items": line_items,
            "sub_total": subtotal,
            "taxable_amount": subtotal,
            "cgst_total": cgst,
            "sgst_total": sgst,
            "igst_total": 0,
            "tax_total": tax_total,
            "grand_total": grand,
            "balance_due": 0 if paid else grand,
            "amount_paid": grand if paid else 0,
            "status": "paid" if paid else "open",
            "created_time": iso(bill_date),
            "updated_time": iso(bill_date),
            "_seed": SEED_TAG,
        }
        bill_docs.append(doc)

        # Journal entry for bill
        je_id = f"seed-je-bill-{uid()}"
        bill_journals.append({
            "entry_id": je_id,
            "entry_date": bill_date.strftime("%Y-%m-%d"),
            "reference_number": bill_number,
            "description": f"Parts purchase from {vendor['name']}",
            "organization_id": ORG_ID,
            "created_by": OWNER_USER_ID,
            "entry_type": "BILL",
            "source_document_id": bill_id,
            "source_document_type": "BILL",
            "is_posted": True,
            "is_reversed": False,
            "lines": [
                {"line_id": f"jel_{uid()}", "account_name": "Inventory / Parts", "debit": subtotal, "credit": 0},
                {"line_id": f"jel_{uid()}", "account_name": "CGST Input", "debit": cgst, "credit": 0},
                {"line_id": f"jel_{uid()}", "account_name": "SGST Input", "debit": sgst, "credit": 0},
                {"line_id": f"jel_{uid()}", "account_name": "Accounts Payable", "debit": 0, "credit": grand},
            ],
            "total_debit": grand,
            "total_credit": grand,
            "created_at": iso(bill_date),
            "updated_at": "",
            "_seed": SEED_TAG,
        })

    if bill_docs:
        await db.bills.insert_many(bill_docs)
    if bill_journals:
        await db.journal_entries.insert_many(bill_journals)
    counts["bills"] = len(bill_docs)
    counts["journal_entries"] = counts.get("journal_entries", 0) + len(bill_journals)
    print(f"  {len(bill_docs)} bills + {len(bill_journals)} journal entries")

    # ── STEP 9: AMC Plans + Subscriptions ──
    print("[9/9] Seeding AMC contracts...")
    # Create 2 plans
    plan_ids = []
    plans = [
        {"name": "EV Care Basic — 2W", "tier": "starter", "vehicle_category": "2W", "price": 1999, "annual_price": 19999,
         "duration_months": 12, "billing_frequency": "monthly", "max_service_visits": 4, "includes_parts": False,
         "parts_discount_percent": 10, "priority_support": False, "roadside_assistance": True},
        {"name": "Fleet Pro — All Vehicles", "tier": "fleet_pro", "vehicle_category": "2W", "price": 4999, "annual_price": 49999,
         "duration_months": 12, "billing_frequency": "monthly", "max_service_visits": 12, "includes_parts": True,
         "parts_discount_percent": 25, "priority_support": True, "priority_response_minutes": 30,
         "roadside_assistance": True, "fleet_dashboard": True, "dedicated_manager": True},
    ]
    for plan in plans:
        pid = f"seed-plan-{uid()}"
        doc = {
            "plan_id": pid,
            "organization_id": ORG_ID,
            "is_active": True,
            "created_at": iso(NOW - timedelta(days=180)),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
            **plan,
        }
        await db.amc_plans.insert_one(doc)
        plan_ids.append(pid)

    # Subscribe fleet customers
    fleet_contacts = [c for c in contact_docs if c["customer_type"] == "business" and c["contact_type"] == "customer"]
    sub_docs = []
    for i, fc in enumerate(fleet_contacts[:6]):
        sub_id = f"seed-sub-{uid()}"
        plan_id = plan_ids[1] if i < 3 else plan_ids[0]  # first 3 get fleet pro
        vh_id = vehicle_ids[i % len(vehicle_ids)]
        start = NOW - timedelta(days=random.randint(30, 150))
        end = start + timedelta(days=365)
        status = "active" if end > NOW else "expired"
        # Make 1-2 expiring soon
        if i >= 4:
            end = NOW + timedelta(days=random.randint(5, 20))
            status = "active"

        doc = {
            "subscription_id": sub_id,
            "plan_id": plan_id,
            "organization_id": ORG_ID,
            "customer_id": fc["contact_id"],
            "customer_name": fc["name"],
            "vehicle_id": vh_id,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "status": status,
            "amount_paid": plans[1]["price"] * 3 if plan_id == plan_ids[1] else plans[0]["price"] * 3,
            "payment_status": "paid",
            "visits_used": random.randint(1, 6),
            "created_at": iso(start),
            "updated_at": iso(NOW),
            "_seed": SEED_TAG,
        }
        sub_docs.append(doc)

    if sub_docs:
        await db.amc_subscriptions.insert_many(sub_docs)
    counts["amc_plans"] = len(plan_ids)
    counts["amc_subscriptions"] = len(sub_docs)
    print(f"  {len(plan_ids)} AMC plans + {len(sub_docs)} subscriptions")

    # ── SUMMARY ──
    print(f"\n{'='*60}")
    print("  SEED COMPLETE — Records created:")
    print(f"{'='*60}")
    for k, v in sorted(counts.items()):
        print(f"  {k:25s}: {v}")
    total_records = sum(counts.values())
    print(f"  {'─'*35}")
    print(f"  {'TOTAL':25s}: {total_records}")
    print(f"{'='*60}\n")

    # ── VERIFICATION SAMPLE ──
    sample_ticket = resolved_tickets[0] if resolved_tickets else None
    if sample_ticket:
        print("  VERIFICATION SAMPLE:")
        print(f"  Ticket: {sample_ticket['tid']}")
        t = await db.tickets.find_one({"ticket_id": sample_ticket["tid"]}, {"_id": 0, "ticket_id": 1, "customer_id": 1, "vehicle_id": 1, "invoice_id": 1, "status": 1, "title": 1})
        print(f"    -> status={t['status']}, customer={t.get('customer_id')}, vehicle={t.get('vehicle_id')}")
        if t.get("invoice_id"):
            inv = await db.invoices.find_one({"invoice_id": t["invoice_id"]}, {"_id": 0, "invoice_number": 1, "total_amount": 1, "customer_id": 1})
            print(f"    -> invoice={inv}")
            je = await db.journal_entries.find_one({"source_document_id": t["invoice_id"]}, {"_id": 0, "entry_id": 1, "reference_number": 1, "total_debit": 1})
            print(f"    -> journal={je}")
        contact = await db.contacts.find_one({"contact_id": t.get("customer_id")}, {"_id": 0, "name": 1, "phone": 1})
        print(f"    -> contact={contact}")
        vehicle = await db.vehicles.find_one({"vehicle_id": t.get("vehicle_id")}, {"_id": 0, "model": 1, "registration_number": 1})
        print(f"    -> vehicle={vehicle}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
