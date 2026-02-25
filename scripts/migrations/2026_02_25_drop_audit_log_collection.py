"""
Migration: Drop empty audit_log collection
Target: battwheels (production)
Pre-tested on: battwheels_dev, battwheels_staging

The audit_log collection was a Week 2 artifact. All new code writes to
audit_logs (note the 's'). This migration drops the empty audit_log
collection to prevent future confusion.

Safety: Only drops if the collection has 0 documents. Aborts otherwise.
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone


async def migrate():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME must be set")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"  MIGRATION: Drop empty audit_log collection")
    print(f"  Database: {db_name}")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Pre-check: verify audit_log exists and is empty
    collections = await db.list_collection_names()

    if "audit_log" not in collections:
        print(f"\n  audit_log collection does not exist in {db_name}.")
        print("  Nothing to do. Migration complete.")
        client.close()
        return

    count = await db.audit_log.count_documents({})
    print(f"\n  audit_log record count: {count}")

    if count > 0:
        print(f"\n  ABORT: audit_log has {count} records — NOT empty.")
        print("  Manual review required before dropping.")
        print("  Run: db.audit_log.find().limit(5) to inspect records.")
        client.close()
        sys.exit(1)

    # Verify audit_logs (the correct collection) exists
    if "audit_logs" not in collections:
        print("\n  WARNING: audit_logs collection also doesn't exist.")
        print("  This is unexpected. Proceed with caution.")

    audit_logs_count = await db.audit_logs.count_documents({}) if "audit_logs" in collections else 0
    print(f"  audit_logs record count: {audit_logs_count} (this is the correct collection)")

    # Drop the empty collection
    await db.drop_collection("audit_log")
    print(f"\n  audit_log dropped from {db_name}")

    # Post-check: confirm it's gone
    collections_after = await db.list_collection_names()
    assert "audit_log" not in collections_after, "audit_log still exists after drop!"
    print("  Verified: audit_log no longer exists")

    print(f"\n{'='*60}")
    print("  MIGRATION COMPLETE")
    print(f"{'='*60}")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
