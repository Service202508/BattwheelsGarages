"""
Migration: Consolidate invoices → invoices_enhanced
Target: battwheels (production)
Pre-tested on: battwheels_dev

Copies any records from the legacy `invoices` collection into `invoices_enhanced`
using the enhanced schema. The original `invoices` records are preserved (not deleted)
until the migration is verified.

Safety:
- Read-only on source collection (invoices)
- Additive to target collection (invoices_enhanced)
- Skips records that already exist in invoices_enhanced (by invoice_number)
- Preserves originals — manual deletion after verification
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid


async def transform_invoice(legacy_doc, db):
    """Transform a legacy invoices document to invoices_enhanced schema."""
    # Remove MongoDB _id before reinserting
    legacy_doc.pop("_id", None)

    # Fix 1: Fetch line items from invoice_line_items collection
    invoice_id = legacy_doc.get("invoice_id", "")
    items = await db.invoice_line_items.find(
        {"invoice_id": invoice_id}
    ).to_list(None)
    for item in items:
        item.pop("_id", None)
    line_items = items or legacy_doc.get("line_items", legacy_doc.get("items", []))

    # Fix 2: Derive payment_status from existing financial fields
    balance_due = legacy_doc.get("balance_due", 0)
    amount_paid = legacy_doc.get("amount_paid", 0)
    grand_total = legacy_doc.get("grand_total", legacy_doc.get("total", 0))
    if balance_due == 0 and amount_paid > 0:
        payment_status = "paid"
    elif amount_paid > 0 and balance_due > 0:
        payment_status = "partial"
    else:
        payment_status = legacy_doc.get("payment_status", "unpaid")

    # Fix 3: Preserve original timestamp
    created_at = (legacy_doc.get("created_at") or
                  legacy_doc.get("created_time") or
                  datetime.now(timezone.utc).isoformat())

    return {
        "invoice_id": invoice_id or f"inv-{uuid.uuid4().hex[:12]}",
        "invoice_number": legacy_doc.get("invoice_number", ""),
        "organization_id": legacy_doc.get("organization_id", ""),
        "customer_id": legacy_doc.get("customer_id", ""),
        "customer_name": legacy_doc.get("customer_name", ""),
        "date": legacy_doc.get("date", legacy_doc.get("invoice_date", "")),
        "due_date": legacy_doc.get("due_date", ""),
        "status": legacy_doc.get("status", "draft"),
        "line_items": line_items,
        "subtotal": legacy_doc.get("subtotal", legacy_doc.get("sub_total", 0)),
        "total_discount": legacy_doc.get("total_discount", legacy_doc.get("discount", 0)),
        "total_tax": legacy_doc.get("total_tax", legacy_doc.get("tax_total", 0)),
        "grand_total": grand_total,
        "amount_paid": amount_paid,
        "balance_due": balance_due,
        "payment_status": payment_status,
        "notes": legacy_doc.get("notes", ""),
        "terms_and_conditions": legacy_doc.get("terms_and_conditions", ""),
        "gst_type": legacy_doc.get("gst_type", "intra_state"),
        "created_at": created_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "migrated_from": "invoices",
        "migration_date": datetime.now(timezone.utc).isoformat(),
        # Fix 4: Preserve all GST and financial fields
        "total_cgst": legacy_doc.get("total_cgst", 0),
        "total_sgst": legacy_doc.get("total_sgst", 0),
        "total_igst": legacy_doc.get("total_igst", 0),
        "place_of_supply": legacy_doc.get("place_of_supply", ""),
        "customer_email": legacy_doc.get("customer_email", ""),
        "customer_gstin": legacy_doc.get("customer_gstin", ""),
        "estimate_id": legacy_doc.get("estimate_id", ""),
        "estimate_number": legacy_doc.get("estimate_number", ""),
        "shipping_charge": legacy_doc.get("shipping_charge", 0),
        "adjustment": legacy_doc.get("adjustment", 0),
        "paid_date": legacy_doc.get("paid_date", ""),
        "payment_count": legacy_doc.get("payment_count", 0),
    }


async def migrate():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME must be set")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"  MIGRATION: Consolidate invoices → invoices_enhanced")
    print(f"  Database: {db_name}")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    collections = await db.list_collection_names()

    if "invoices" not in collections:
        print(f"\n  invoices collection does not exist in {db_name}.")
        print("  Nothing to migrate. Done.")
        client.close()
        return

    # Count source records
    source_count = await db.invoices.count_documents({})
    target_count_before = await db.invoices_enhanced.count_documents({}) if "invoices_enhanced" in collections else 0

    print(f"\n  Source (invoices): {source_count} records")
    print(f"  Target (invoices_enhanced): {target_count_before} records")

    if source_count == 0:
        print("\n  invoices collection is empty. Nothing to migrate.")
        print("  Safe to drop: db.invoices.drop()")
        client.close()
        return

    # Get existing invoice numbers in target to avoid duplicates
    existing_numbers = set()
    if "invoices_enhanced" in collections:
        async for doc in db.invoices_enhanced.find({}, {"_id": 0, "invoice_number": 1}):
            if doc.get("invoice_number"):
                existing_numbers.add(doc["invoice_number"])

    # Process each legacy invoice
    migrated = 0
    skipped = 0
    errors = 0

    async for legacy_doc in db.invoices.find({}):
        inv_num = legacy_doc.get("invoice_number", "")

        if inv_num in existing_numbers:
            print(f"    SKIP: {inv_num} already exists in invoices_enhanced")
            skipped += 1
            continue

        try:
            enhanced = await transform_invoice(legacy_doc, db)
            await db.invoices_enhanced.insert_one(enhanced)
            migrated += 1
            print(f"    MIGRATED: {inv_num} ({enhanced.get('customer_name', 'unknown')})")
        except Exception as e:
            errors += 1
            print(f"    ERROR: {inv_num} — {e}")

    target_count_after = await db.invoices_enhanced.count_documents({})

    print(f"\n{'='*60}")
    print(f"  MIGRATION RESULTS")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  invoices_enhanced before: {target_count_before}")
    print(f"  invoices_enhanced after: {target_count_after}")
    print(f"\n  NOTE: Original invoices collection preserved ({source_count} records)")
    print(f"  After verifying migration, run: db.invoices.drop()")
    print(f"{'='*60}")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
