"""
Battwheels OS — MongoDB Schema Validators
Applies validation rules to prevent documents without organization_id.
Run: python scripts/add_schema_validators.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

VALIDATORS = {
    "tickets": {
        "bsonType": "object",
        "required": ["ticket_id", "organization_id", "status", "created_at"],
        "properties": {
            "organization_id": {"bsonType": "string", "minLength": 1},
            "status": {"enum": ["open", "in_progress", "resolved", "closed",
                                "cancelled", "estimate_shared", "technician_assigned",
                                "work_started", "pending_parts", "quality_check"]}
        }
    },
    "invoices": {
        "bsonType": "object",
        "required": ["invoice_id", "organization_id"],
        "properties": {
            "organization_id": {"bsonType": "string", "minLength": 1}
        }
    },
    "journal_entries": {
        "bsonType": "object",
        "required": ["entry_id", "organization_id"],
        "properties": {
            "organization_id": {"bsonType": "string", "minLength": 1}
        }
    },
    "contacts": {
        "bsonType": "object",
        "required": ["contact_id", "organization_id"],
        "properties": {
            "organization_id": {"bsonType": "string", "minLength": 1}
        }
    },
    "employees": {
        "bsonType": "object",
        "required": ["employee_id", "organization_id"],
        "properties": {
            "organization_id": {"bsonType": "string", "minLength": 1}
        }
    },
    "inventory": {
        "bsonType": "object",
        "required": ["organization_id"],
        "properties": {
            "organization_id": {"bsonType": "string", "minLength": 1}
        }
    },
    "estimates": {
        "bsonType": "object",
        "required": ["organization_id"],
        "properties": {
            "organization_id": {"bsonType": "string", "minLength": 1}
        }
    },
}


async def apply_validators():
    url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(url)

    db_names = ["battwheels", "battwheels_staging", "battwheels_dev"]

    for db_name in db_names:
        db = client[db_name]
        print(f"\n=== {db_name} ===")

        # Check if DB exists (has collections)
        collections = await db.list_collection_names()
        if not collections:
            print(f"  Skipping (no collections)")
            continue

        for col_name, schema in VALIDATORS.items():
            try:
                await db.command({
                    "collMod": col_name,
                    "validator": {"$jsonSchema": schema},
                    "validationLevel": "moderate",
                    "validationAction": "warn"
                })
                print(f"  {col_name}: validator applied")
            except Exception as e:
                if "ns not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                    print(f"  {col_name}: collection doesn't exist (OK)")
                else:
                    print(f"  {col_name}: ERROR — {e}")

    # Test rejection on battwheels DB
    print("\n=== REJECTION TEST (battwheels) ===")
    db = client["battwheels"]
    try:
        await db.tickets.insert_one({
            "ticket_id": "test-validator-check",
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        # If we get here, validator didn't block it (validation=warn)
        await db.tickets.delete_one({"ticket_id": "test-validator-check"})
        print("  WARNING mode: Missing org_id generated a warning (not rejected)")
    except Exception as e:
        if "validation" in str(e).lower():
            print("  PASS: Missing org_id correctly rejected")
        else:
            print(f"  ERROR: {e}")

    client.close()


if __name__ == "__main__":
    asyncio.run(apply_validators())
