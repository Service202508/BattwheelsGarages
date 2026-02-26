"""
Migration Runner
================
Runs on application startup. Checks a `migrations` collection for which 
migrations have already run. Executes pending migrations in order.
Each migration is idempotent (safe to run multiple times).
"""

import importlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent


async def run_migrations(db):
    """
    Discover and run all pending migrations.
    Migrations are .py files in the migrations/ directory with naming:
      YYYY_MM_DD_NNN_description.py
    Each must have an `async def up(db)` function.
    """
    # Find all migration files
    migration_files = sorted([
        f.stem for f in MIGRATIONS_DIR.glob("*.py")
        if f.stem not in ("__init__", "runner") and not f.stem.startswith("_")
    ])
    
    if not migration_files:
        logger.info("No migration files found")
        return
    
    # Get already-run migrations
    completed = set()
    async for doc in db.migrations.find({}, {"name": 1, "_id": 0}):
        completed.add(doc["name"])
    
    pending = [m for m in migration_files if m not in completed]
    
    if not pending:
        logger.info(f"All {len(completed)} migrations already applied")
        return
    
    logger.info(f"Running {len(pending)} pending migration(s)...")
    
    for migration_name in pending:
        try:
            module = importlib.import_module(f"migrations.{migration_name}")
            if hasattr(module, "up"):
                result = await module.up(db)
                logger.info(f"Migration {migration_name}: {result or 'OK'}")
                
                # Record completion
                await db.migrations.insert_one({
                    "name": migration_name,
                    "result": str(result or "OK"),
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                })
            else:
                logger.warning(f"Migration {migration_name} has no 'up' function, skipping")
        except Exception as e:
            logger.error(f"Migration {migration_name} FAILED: {e}")
            # Don't continue if a migration fails
            raise
