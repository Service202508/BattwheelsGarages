"""
Entitlement Migration Script
============================
1. Creates PROFESSIONAL subscription for Battwheels Garages (org: 6996dcf072ffd2a2395fee7b)
2. Updates existing plans in DB to add new feature fields and correct plan assignments
3. Safe to run multiple times (idempotent)
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv("/app/backend/.env")
except Exception:
    pass

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
BATTWHEELS_ORG_ID = "6996dcf072ffd2a2395fee7b"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # ─── 1. Verify Battwheels org exists ────────────────────────────────────
    from bson import ObjectId
    org = await db.organizations.find_one({"_id": ObjectId(BATTWHEELS_ORG_ID)})
    if not org:
        logger.error("Battwheels Garages org not found!")
        return

    logger.info(f"Found org: {org.get('name')} — proceeding with migration")

    # ─── 2. Create PROFESSIONAL subscription for Battwheels Garages ─────────
    existing_sub = await db.subscriptions.find_one({"organization_id": BATTWHEELS_ORG_ID})
    if not existing_sub:
        # Get the professional plan
        pro_plan = await db.plans.find_one({"code": "professional"})
        if not pro_plan:
            logger.error("Professional plan not found in DB!")
            return

        sub_doc = {
            "subscription_id": f"sub_battwheels_primary",
            "organization_id": BATTWHEELS_ORG_ID,
            "plan_id": pro_plan.get("plan_id", "plan_professional"),
            "plan_code": "professional",
            "status": "active",
            "billing_cycle": "annual",
            "current_period_start": datetime.now(timezone.utc),
            "current_period_end": None,
            "cancel_at_period_end": False,
            "payment_method": "manual",
            "usage": {
                "invoices_created": 0,
                "tickets_created": 0,
                "vehicles_added": 0,
                "ai_calls_made": 0,
                "api_calls_made": 0,
                "storage_used_mb": 0.0,
                "last_updated": datetime.now(timezone.utc)
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "migration_script",
            "note": "Primary org — set to Professional by entitlement migration"
        }
        await db.subscriptions.insert_one(sub_doc)
        logger.info("✅ Created PROFESSIONAL subscription for Battwheels Garages")
    else:
        logger.info(f"ℹ️  Battwheels already has subscription: plan={existing_sub.get('plan_code')}, status={existing_sub.get('status')}")
        # If not professional or higher, upgrade it
        current_plan = existing_sub.get("plan_code", "")
        if current_plan not in ("professional", "enterprise"):
            await db.subscriptions.update_one(
                {"organization_id": BATTWHEELS_ORG_ID},
                {"$set": {"plan_code": "professional", "status": "active", "updated_at": datetime.now(timezone.utc)}}
            )
            logger.info("✅ Upgraded Battwheels subscription to PROFESSIONAL")

    # ─── 3. Update plan features in DB ──────────────────────────────────────
    # New features to add to each plan
    plan_updates = {
        "free": {
            "features.project_management": {"enabled": False},
            "features.einvoice": {"enabled": False},
            "features.accounting_module": {"enabled": False},
        },
        "starter": {
            "features.project_management": {"enabled": False},
            "features.einvoice": {"enabled": False},
            "features.accounting_module": {"enabled": False},
            # advanced_reports enabled on starter
            "features.advanced_reports": {"enabled": True},
            # hr_payroll disabled on starter
            "features.hr_payroll": {"enabled": False},
            # multi-warehouse disabled on starter
            "features.inventory_multi_warehouse": {"enabled": False},
            "features.inventory_stock_transfers": {"enabled": False},
        },
        "professional": {
            "features.project_management": {"enabled": True},
            "features.einvoice": {"enabled": True},
            "features.accounting_module": {"enabled": True},
            # hr_payroll enabled on professional
            "features.hr_payroll": {"enabled": True},
            # advanced_reports enabled on professional too
            "features.advanced_reports": {"enabled": True},
            # multi-warehouse DISABLED on professional (moved to enterprise)
            "features.inventory_multi_warehouse": {"enabled": False},
            "features.inventory_stock_transfers": {"enabled": False},
        },
        "enterprise": {
            "features.project_management": {"enabled": True},
            "features.einvoice": {"enabled": True},
            "features.accounting_module": {"enabled": True},
            "features.hr_payroll": {"enabled": True},
            "features.advanced_reports": {"enabled": True},
            "features.inventory_multi_warehouse": {"enabled": True},
            "features.inventory_stock_transfers": {"enabled": True},
        }
    }

    for plan_code, updates in plan_updates.items():
        result = await db.plans.update_one(
            {"code": plan_code},
            {"$set": updates}
        )
        if result.modified_count > 0:
            logger.info(f"✅ Updated plan '{plan_code}' features in DB")
        else:
            logger.info(f"ℹ️  Plan '{plan_code}' features already up to date (or plan not found)")

    logger.info("\n=== MIGRATION COMPLETE ===")
    logger.info(f"Battwheels Garages ({BATTWHEELS_ORG_ID}) is now on PROFESSIONAL plan")
    logger.info("Plans updated with new entitlement structure")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
