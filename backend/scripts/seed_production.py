"""
Seed script for battwheels (PRODUCTION) — essentials only.
Connects DIRECTLY to battwheels. Does NOT use the running app.
NO demo orgs. NO test data. Seeds only platform-level reference data.
"""

import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = "battwheels"


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print(f"=== Seeding {DB_NAME} (PRODUCTION) ===\n")

    # ---------------------------------------------------------------
    # SECTION A — Platform Admin (fix role if needed)
    # ---------------------------------------------------------------
    print("SECTION A: Platform Admin")
    existing = await db.users.find_one({"email": "platform-admin@battwheels.in"})
    if existing:
        if existing.get("role") != "platform_admin":
            await db.users.update_one(
                {"email": "platform-admin@battwheels.in"},
                {"$set": {"role": "platform_admin"}}
            )
            print(f"  Updated role: {existing.get('role')} -> platform_admin")
        else:
            print("  Already exists with correct role — skipping")
    else:
        password = os.environ.get("PLATFORM_ADMIN_PASSWORD", "DevDefault@123")
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        await db.users.insert_one({
            "email": "platform-admin@battwheels.in",
            "password": hashed,
            "name": "Platform Admin",
            "role": "platform_admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        print("  Created: platform-admin@battwheels.in (platform_admin)")

    # ---------------------------------------------------------------
    # SECTION B — Pricing Plans (4)
    # ---------------------------------------------------------------
    print("\nSECTION B: Pricing Plans")
    plans = [
        {
            "plan_id": "free_trial",
            "name": "Free Trial",
            "price": 0,
            "currency": "INR",
            "billing_cycle": "monthly",
            "trial_days": 14,
            "max_users": 3,
            "features": ["all_modules", "efi_engine", "customer_portal", "invoicing", "estimates", "inventory", "hr_payroll", "reports"],
            "description": "Full access for 14 days. No credit card required.",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "plan_id": "starter",
            "name": "Starter",
            "price": 999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "max_users": 5,
            "features": ["tickets", "invoicing", "estimates", "contacts", "inventory_basic"],
            "description": "For small workshops getting started with digital operations.",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "plan_id": "professional",
            "name": "Professional",
            "price": 2499,
            "currency": "INR",
            "billing_cycle": "monthly",
            "max_users": 15,
            "features": ["all_modules", "efi_engine", "customer_portal", "invoicing", "estimates", "inventory", "hr_payroll", "reports", "multi_branch"],
            "description": "For growing service centers needing full platform access.",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "plan_id": "enterprise",
            "name": "Enterprise",
            "price": 4999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "max_users": -1,
            "features": ["all_modules", "efi_engine", "customer_portal", "invoicing", "estimates", "inventory", "hr_payroll", "reports", "multi_branch", "priority_support", "api_access", "custom_integrations"],
            "description": "Unlimited users. Priority support. For OEMs and large networks.",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    existing_plans = await db.pricing_plans.count_documents({})
    if existing_plans > 0:
        print(f"  {existing_plans} plans already exist — skipping")
    else:
        await db.pricing_plans.insert_many(plans)
        print(f"  Inserted {len(plans)} pricing plans")

    # ---------------------------------------------------------------
    # SECTION C — GST State Codes (37)
    # ---------------------------------------------------------------
    print("\nSECTION C: GST State Codes")
    gst_states = [
        {"code": "01", "name": "Jammu & Kashmir"},
        {"code": "02", "name": "Himachal Pradesh"},
        {"code": "03", "name": "Punjab"},
        {"code": "04", "name": "Chandigarh"},
        {"code": "05", "name": "Uttarakhand"},
        {"code": "06", "name": "Haryana"},
        {"code": "07", "name": "Delhi"},
        {"code": "08", "name": "Rajasthan"},
        {"code": "09", "name": "Uttar Pradesh"},
        {"code": "10", "name": "Bihar"},
        {"code": "11", "name": "Sikkim"},
        {"code": "12", "name": "Arunachal Pradesh"},
        {"code": "13", "name": "Nagaland"},
        {"code": "14", "name": "Manipur"},
        {"code": "15", "name": "Mizoram"},
        {"code": "16", "name": "Tripura"},
        {"code": "17", "name": "Meghalaya"},
        {"code": "18", "name": "Assam"},
        {"code": "19", "name": "West Bengal"},
        {"code": "20", "name": "Jharkhand"},
        {"code": "21", "name": "Odisha"},
        {"code": "22", "name": "Chhattisgarh"},
        {"code": "23", "name": "Madhya Pradesh"},
        {"code": "24", "name": "Gujarat"},
        {"code": "25", "name": "Daman & Diu"},
        {"code": "26", "name": "Dadra & Nagar Haveli"},
        {"code": "27", "name": "Maharashtra"},
        {"code": "28", "name": "Andhra Pradesh"},
        {"code": "29", "name": "Karnataka"},
        {"code": "30", "name": "Goa"},
        {"code": "31", "name": "Lakshadweep"},
        {"code": "32", "name": "Kerala"},
        {"code": "33", "name": "Tamil Nadu"},
        {"code": "34", "name": "Puducherry"},
        {"code": "35", "name": "Andaman & Nicobar Islands"},
        {"code": "36", "name": "Telangana"},
        {"code": "37", "name": "Ladakh"},
    ]

    existing_states = await db.gst_state_codes.count_documents({})
    if existing_states > 0:
        print(f"  {existing_states} state codes already exist — skipping")
    else:
        await db.gst_state_codes.insert_many(gst_states)
        print(f"  Inserted {len(gst_states)} GST state codes")

    # ---------------------------------------------------------------
    # SECTION D — Default Chart of Accounts Template
    # ---------------------------------------------------------------
    print("\nSECTION D: Chart of Accounts Template")
    coa_accounts = [
        {"code": "1100", "name": "Cash", "type": "asset", "sub_type": "current_asset", "is_default": True},
        {"code": "1200", "name": "Bank Account", "type": "asset", "sub_type": "current_asset", "is_default": True},
        {"code": "1300", "name": "Accounts Receivable", "type": "asset", "sub_type": "current_asset", "is_default": True},
        {"code": "1400", "name": "Inventory Asset", "type": "asset", "sub_type": "current_asset", "is_default": True},
        {"code": "1500", "name": "Fixed Assets", "type": "asset", "sub_type": "fixed_asset", "is_default": True},
        {"code": "2100", "name": "Accounts Payable", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2200", "name": "GST Payable CGST", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2201", "name": "GST Payable SGST", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2202", "name": "GST Payable IGST", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2210", "name": "GST Input CGST", "type": "asset", "sub_type": "current_asset", "is_default": True},
        {"code": "2211", "name": "GST Input SGST", "type": "asset", "sub_type": "current_asset", "is_default": True},
        {"code": "2212", "name": "GST Input IGST", "type": "asset", "sub_type": "current_asset", "is_default": True},
        {"code": "2300", "name": "PF Payable", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2301", "name": "ESI Payable", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2302", "name": "TDS Payable", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2303", "name": "PT Payable", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "2400", "name": "Salary Payable", "type": "liability", "sub_type": "current_liability", "is_default": True},
        {"code": "3100", "name": "Owner Capital", "type": "equity", "sub_type": "equity", "is_default": True},
        {"code": "3200", "name": "Retained Earnings", "type": "equity", "sub_type": "equity", "is_default": True},
        {"code": "4100", "name": "Sales Revenue", "type": "revenue", "sub_type": "operating_revenue", "is_default": True},
        {"code": "4200", "name": "Service Income", "type": "revenue", "sub_type": "operating_revenue", "is_default": True},
        {"code": "5100", "name": "Cost of Goods Sold", "type": "expense", "sub_type": "cost_of_goods", "is_default": True},
        {"code": "6100", "name": "Salary Expense", "type": "expense", "sub_type": "operating_expense", "is_default": True},
        {"code": "6200", "name": "Rent", "type": "expense", "sub_type": "operating_expense", "is_default": True},
        {"code": "6300", "name": "Utilities", "type": "expense", "sub_type": "operating_expense", "is_default": True},
    ]

    existing_coa = await db.chart_of_accounts_templates.count_documents({})
    if existing_coa > 0:
        print(f"  {existing_coa} accounts already exist — skipping")
    else:
        for acct in coa_accounts:
            acct["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.chart_of_accounts_templates.insert_many(coa_accounts)
        print(f"  Inserted {len(coa_accounts)} CoA template accounts")

    # ---------------------------------------------------------------
    # SECTION E — EVFI Platform Patterns (copy from dev)
    # ---------------------------------------------------------------
    print("\nSECTION E: EVFI Platform Patterns (from battwheels_dev)")
    dev_db = client["battwheels_dev"]

    existing_patterns = await db.efi_platform_patterns.count_documents({})
    if existing_patterns > 0:
        print(f"  {existing_patterns} patterns already exist — skipping")
    else:
        dev_patterns = await dev_db.efi_platform_patterns.find({}, {"_id": 0}).to_list(length=None)
        if dev_patterns:
            await db.efi_platform_patterns.insert_many(dev_patterns)
            print(f"  Copied {len(dev_patterns)} patterns from battwheels_dev")
        else:
            print("  WARNING: No patterns found in battwheels_dev")

    # ---------------------------------------------------------------
    # SECTION F — Default System Config
    # ---------------------------------------------------------------
    print("\nSECTION F: Default System Config")

    # SLA Config
    existing_sla = await db.sla_configs.count_documents({})
    if existing_sla > 0:
        print(f"  SLA config already exists ({existing_sla}) — skipping")
    else:
        await db.sla_configs.insert_one({
            "config_id": "default",
            "response_time_hours": 4,
            "resolution_time_hours": 24,
            "escalation_levels": [
                {"level": 1, "after_hours": 4, "notify": "assigned_technician"},
                {"level": 2, "after_hours": 12, "notify": "service_manager"},
                {"level": 3, "after_hours": 24, "notify": "owner"},
            ],
            "is_default": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        print("  Inserted default SLA config")

    # Ticket Priorities
    existing_priorities = await db.ticket_priorities.count_documents({})
    if existing_priorities > 0:
        print(f"  Ticket priorities already exist ({existing_priorities}) — skipping")
    else:
        priorities = [
            {"key": "low", "label": "Low", "sla_multiplier": 2.0, "color": "#22c55e", "sort_order": 1},
            {"key": "medium", "label": "Medium", "sla_multiplier": 1.0, "color": "#f59e0b", "sort_order": 2},
            {"key": "high", "label": "High", "sla_multiplier": 0.5, "color": "#f97316", "sort_order": 3},
            {"key": "critical", "label": "Critical", "sla_multiplier": 0.25, "color": "#ef4444", "sort_order": 4},
        ]
        await db.ticket_priorities.insert_many(priorities)
        print(f"  Inserted {len(priorities)} ticket priorities")

    # Ticket Categories
    existing_categories = await db.ticket_categories.count_documents({})
    if existing_categories > 0:
        print(f"  Ticket categories already exist ({existing_categories}) — skipping")
    else:
        categories = [
            {"key": "electrical", "label": "Electrical", "icon": "zap", "sort_order": 1},
            {"key": "mechanical", "label": "Mechanical", "icon": "wrench", "sort_order": 2},
            {"key": "software", "label": "Software / ECU", "icon": "cpu", "sort_order": 3},
            {"key": "battery", "label": "Battery / BMS", "icon": "battery", "sort_order": 4},
            {"key": "motor", "label": "Motor / Controller", "icon": "settings", "sort_order": 5},
            {"key": "charging", "label": "Charging System", "icon": "plug", "sort_order": 6},
            {"key": "body", "label": "Body / Frame", "icon": "shield", "sort_order": 7},
        ]
        await db.ticket_categories.insert_many(categories)
        print(f"  Inserted {len(categories)} ticket categories")

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n=== Production Seed Complete ===")
    for col in sorted(["users", "pricing_plans", "gst_state_codes",
                        "chart_of_accounts_templates", "efi_platform_patterns",
                        "sla_configs", "ticket_priorities", "ticket_categories"]):
        cnt = await db[col].count_documents({})
        print(f"  {col}: {cnt}")


if __name__ == "__main__":
    asyncio.run(seed())
