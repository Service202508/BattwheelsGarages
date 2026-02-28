# PRODUCTION: Run this before first customer signup.
# Safe to run multiple times — uses createIndex which is idempotent.
#
# Sprint 6D-01: Add compound indexes for cursor-based pagination
# on the 5 highest-traffic endpoints.
#
# Usage:
#   python scripts/add_pagination_indexes.py
#   python scripts/add_pagination_indexes.py --db battwheels  # production

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

INDEXES = [
    # tickets
    ("tickets", [
        {"keys": [("organization_id", 1), ("created_at", -1), ("ticket_id", -1)],
         "name": "idx_tickets_cursor_created"},
        {"keys": [("organization_id", 1), ("status", 1), ("created_at", -1)],
         "name": "idx_tickets_status_created"},
    ]),
    # invoices_enhanced
    ("invoices_enhanced", [
        {"keys": [("organization_id", 1), ("invoice_date", -1), ("invoice_id", -1)],
         "name": "idx_invoices_cursor_date"},
        {"keys": [("organization_id", 1), ("status", 1), ("invoice_date", -1)],
         "name": "idx_invoices_status_date"},
    ]),
    # employees
    ("employees", [
        {"keys": [("organization_id", 1), ("created_at", -1), ("employee_id", -1)],
         "name": "idx_employees_cursor_created"},
    ]),
    # failure_cards
    ("failure_cards", [
        {"keys": [("organization_id", 1), ("confidence_score", -1), ("failure_id", -1)],
         "name": "idx_fc_cursor_confidence"},
        {"keys": [("organization_id", 1), ("is_seed_data", 1), ("confidence_score", -1)],
         "name": "idx_fc_seed_confidence"},
    ]),
    # journal_entries
    ("journal_entries", [
        {"keys": [("organization_id", 1), ("entry_date", -1), ("entry_id", -1)],
         "name": "idx_je_cursor_date"},
        {"keys": [("organization_id", 1), ("is_posted", 1), ("entry_date", -1)],
         "name": "idx_je_posted_date"},
    ]),
]


async def create_indexes(db_name: str):
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[db_name]

    print(f"Creating pagination indexes on database: {db_name}")
    print("=" * 60)

    created = 0
    skipped = 0

    for coll_name, index_defs in INDEXES:
        coll = db[coll_name]
        for idx in index_defs:
            try:
                result = await coll.create_index(
                    idx["keys"],
                    name=idx["name"],
                    background=True,
                )
                print(f"  [{coll_name}] Created: {result}")
                created += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  [{coll_name}] Skipped (exists): {idx['name']}")
                    skipped += 1
                else:
                    print(f"  [{coll_name}] ERROR: {e}")

    print("=" * 60)
    print(f"Done. Created: {created}, Skipped: {skipped}")
    client.close()


if __name__ == "__main__":
    db_name = "battwheels_dev"
    if "--db" in sys.argv:
        idx = sys.argv.index("--db")
        if idx + 1 < len(sys.argv):
            db_name = sys.argv[idx + 1]
    asyncio.run(create_indexes(db_name))
