"""
Migration: [DESCRIPTION]
Date: [YYYY-MM-DD]
Author: [Agent/Human]

Purpose:
    [What this migration does and why]

Idempotent: YES — safe to run multiple times.
Destructive: NO — does not delete or modify existing data content.

Test order: battwheels_dev → battwheels_staging → battwheels (production)
"""
import asyncio
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Migration metadata
MIGRATION_ID = "YYYYMMDD_NNN"
DESCRIPTION = "Template migration"


async def migrate(db):
    """Run the migration against the given database."""
    logger.info(f"Running migration {MIGRATION_ID}: {DESCRIPTION}")

    # --- YOUR MIGRATION LOGIC HERE ---
    # Example: Add a new index
    # await db.some_collection.create_index(
    #     [("field1", 1), ("field2", 1)],
    #     unique=False,
    #     background=True
    # )

    # Example: Add a new field with default value to all documents
    # result = await db.some_collection.update_many(
    #     {"new_field": {"$exists": False}},
    #     {"$set": {"new_field": "default_value"}}
    # )
    # logger.info(f"  Updated {result.modified_count} documents")

    logger.info(f"Migration {MIGRATION_ID} complete")


async def verify(db):
    """Verify the migration was applied correctly."""
    logger.info(f"Verifying migration {MIGRATION_ID}...")

    # --- YOUR VERIFICATION LOGIC HERE ---
    # Example: Check index exists
    # indexes = await db.some_collection.index_information()
    # assert "field1_1_field2_1" in indexes, "Index not found!"

    logger.info(f"Verification passed")


async def main():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "battwheels_dev")

    if not mongo_url:
        logger.error("MONGO_URL not set")
        return

    logger.info(f"Target database: {db_name}")

    # Safety prompt for production
    if db_name == "battwheels":
        confirm = input("WARNING: You are targeting PRODUCTION. Type 'yes' to continue: ")
        if confirm != "yes":
            logger.info("Aborted.")
            return

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    await migrate(db)
    await verify(db)

    client.close()
    logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
