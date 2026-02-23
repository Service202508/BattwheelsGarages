"""
Battwheels OS - Performance Indexes Migration
==============================================

MongoDB compound indexes for multi-tenant query optimization.
Run this migration to add all necessary indexes for production performance.

Usage:
    python migrations/add_performance_indexes.py

IMPORTANT: These indexes are created in the background (non-blocking).
MongoDB equivalent of CONCURRENTLY - no table locks on production.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Index definitions: (collection, index_spec, options)
# index_spec format: [(field, direction), ...] where direction is 1 (ASC) or -1 (DESC)
# Options include: name, unique, sparse, partialFilterExpression, background

INDEXES = [
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TICKETS (Highest query volume)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("tickets", [("organization_id", 1), ("status", 1)], {"name": "idx_tickets_org_status"}),
    ("tickets", [("organization_id", 1), ("created_at", -1)], {"name": "idx_tickets_org_created"}),
    ("tickets", [("organization_id", 1), ("customer_id", 1)], {"name": "idx_tickets_org_customer"}),
    ("tickets", [("organization_id", 1), ("technician_id", 1)], {"name": "idx_tickets_org_technician"}),
    ("tickets", [("ticket_id", 1)], {"name": "idx_tickets_id", "unique": True}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INVOICES (Critical for finance queries)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("invoices", [("organization_id", 1), ("status", 1)], {"name": "idx_invoices_org_status"}),
    ("invoices", [("organization_id", 1), ("customer_id", 1), ("status", 1)], {"name": "idx_invoices_org_customer_status"}),
    ("invoices", [("organization_id", 1), ("invoice_date", -1)], {"name": "idx_invoices_org_date"}),
    ("invoices", [("organization_id", 1), ("due_date", 1)], {
        "name": "idx_invoices_org_due_date_unpaid",
        "partialFilterExpression": {"status": {"$nin": ["paid", "cancelled"]}}
    }),
    ("invoices", [("invoice_id", 1)], {"name": "idx_invoices_id", "unique": True}),
    ("invoices", [("invoice_number", 1), ("organization_id", 1)], {"name": "idx_invoices_number_org"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # JOURNAL ENTRIES (Accounting queries)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("journal_entries", [("organization_id", 1), ("entry_date", -1)], {"name": "idx_journal_entries_org_date"}),
    ("journal_entries", [("organization_id", 1), ("entry_type", 1)], {"name": "idx_journal_entries_org_type"}),
    ("journal_entries", [("entry_id", 1)], {"name": "idx_journal_entries_id", "unique": True}),
    ("journal_entries", [("source_document_id", 1), ("source_document_type", 1)], {"name": "idx_journal_entries_source"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BILLS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("bills", [("organization_id", 1), ("status", 1)], {"name": "idx_bills_org_status"}),
    ("bills", [("organization_id", 1), ("vendor_id", 1), ("status", 1)], {"name": "idx_bills_org_vendor_status"}),
    ("bills", [("organization_id", 1), ("due_date", 1)], {
        "name": "idx_bills_org_due_date_unpaid",
        "partialFilterExpression": {"status": {"$nin": ["paid", "cancelled"]}}
    }),
    ("bills", [("bill_id", 1)], {"name": "idx_bills_id", "unique": True}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EXPENSES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("expenses", [("organization_id", 1), ("status", 1)], {"name": "idx_expenses_org_status"}),
    ("expenses", [("organization_id", 1), ("expense_date", -1)], {"name": "idx_expenses_org_date"}),
    ("expenses", [("organization_id", 1), ("employee_id", 1), ("status", 1)], {"name": "idx_expenses_org_employee"}),
    ("expenses", [("expense_id", 1)], {"name": "idx_expenses_id", "unique": True}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INVENTORY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("inventory", [("organization_id", 1), ("status", 1)], {"name": "idx_inventory_org_status"}),
    ("inventory", [("organization_id", 1), ("category", 1)], {"name": "idx_inventory_org_category"}),
    ("inventory", [("item_id", 1)], {"name": "idx_inventory_id", "unique": True}),
    ("inventory", [("sku", 1), ("organization_id", 1)], {"name": "idx_inventory_sku_org"}),
    
    # Items collection (Zoho-style)
    ("items", [("organization_id", 1), ("status", 1)], {"name": "idx_items_org_status"}),
    ("items", [("organization_id", 1), ("item_type", 1)], {"name": "idx_items_org_type"}),
    ("items", [("item_id", 1)], {"name": "idx_items_id", "unique": True}),
    
    # Stock Movements
    ("stock_movements", [("item_id", 1), ("movement_date", -1)], {"name": "idx_stock_movements_item_date"}),
    ("stock_movements", [("organization_id", 1), ("movement_date", -1)], {"name": "idx_stock_movements_org_date"}),
    ("stock_movements", [("movement_id", 1)], {"name": "idx_stock_movements_id", "unique": True}),
    ("stock_movements", [("reference_type", 1), ("reference_id", 1)], {"name": "idx_stock_movements_reference"}),
    
    # Allocations
    ("allocations", [("allocation_id", 1)], {"name": "idx_allocations_id", "unique": True}),
    ("allocations", [("ticket_id", 1)], {"name": "idx_allocations_ticket"}),
    ("allocations", [("item_id", 1), ("status", 1)], {"name": "idx_allocations_item_status"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CONTACTS / CUSTOMERS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("contacts", [("organization_id", 1), ("contact_type", 1)], {"name": "idx_contacts_org_type"}),
    ("contacts", [("organization_id", 1), ("status", 1)], {"name": "idx_contacts_org_status"}),
    ("contacts", [("contact_id", 1)], {"name": "idx_contacts_id", "unique": True}),
    ("contacts", [("email", 1), ("organization_id", 1)], {"name": "idx_contacts_email_org"}),
    ("contacts", [("phone", 1), ("organization_id", 1)], {"name": "idx_contacts_phone_org"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VEHICLES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("vehicles", [("organization_id", 1), ("customer_id", 1)], {"name": "idx_vehicles_org_customer"}),
    ("vehicles", [("vehicle_id", 1)], {"name": "idx_vehicles_id", "unique": True}),
    ("vehicles", [("registration_number", 1), ("organization_id", 1)], {"name": "idx_vehicles_reg_org"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # JOB CARDS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("job_cards", [("organization_id", 1), ("status", 1)], {"name": "idx_job_cards_org_status"}),
    ("job_cards", [("ticket_id", 1)], {"name": "idx_job_cards_ticket"}),
    ("job_cards", [("job_card_id", 1)], {"name": "idx_job_cards_id", "unique": True}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ESTIMATES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("estimates", [("organization_id", 1), ("status", 1)], {"name": "idx_estimates_org_status"}),
    ("estimates", [("organization_id", 1), ("customer_id", 1)], {"name": "idx_estimates_org_customer"}),
    ("estimates", [("estimate_id", 1)], {"name": "idx_estimates_id", "unique": True}),
    ("estimates", [("ticket_id", 1)], {"name": "idx_estimates_ticket"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AMC
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("amc_contracts", [("organization_id", 1), ("expiry_date", 1)], {
        "name": "idx_amc_org_expiry_active",
        "partialFilterExpression": {"status": "active"}
    }),
    ("amc_contracts", [("contract_id", 1)], {"name": "idx_amc_id", "unique": True}),
    ("amc_contracts", [("customer_id", 1), ("organization_id", 1)], {"name": "idx_amc_customer_org"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HR / PAYROLL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("employees", [("organization_id", 1), ("status", 1)], {"name": "idx_employees_org_status"}),
    ("employees", [("employee_id", 1)], {"name": "idx_employees_id", "unique": True}),
    ("employees", [("user_id", 1)], {"name": "idx_employees_user"}),
    
    ("payroll_runs", [("organization_id", 1), ("payroll_month", -1)], {"name": "idx_payroll_runs_org_month"}),
    ("payroll_runs", [("payroll_run_id", 1)], {"name": "idx_payroll_runs_id", "unique": True}),
    
    ("attendance", [("organization_id", 1), ("date", -1)], {"name": "idx_attendance_org_date"}),
    ("attendance", [("employee_id", 1), ("date", -1)], {"name": "idx_attendance_employee_date"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PROJECTS / TIME TRACKING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("projects", [("organization_id", 1), ("status", 1)], {"name": "idx_projects_org_status"}),
    ("projects", [("project_id", 1)], {"name": "idx_projects_id", "unique": True}),
    
    ("time_logs", [("project_id", 1), ("log_date", -1)], {"name": "idx_time_logs_project_date"}),
    ("time_logs", [("organization_id", 1), ("invoiced", 1)], {"name": "idx_time_logs_org_invoiced"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BANKING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("bank_accounts", [("organization_id", 1), ("is_active", 1)], {"name": "idx_bank_accounts_org_active"}),
    ("bank_accounts", [("account_id", 1)], {"name": "idx_bank_accounts_id", "unique": True}),
    
    ("bank_transactions", [("bank_account_id", 1), ("transaction_date", -1)], {"name": "idx_bank_txns_account_date"}),
    ("bank_transactions", [("organization_id", 1), ("reconciled", 1)], {"name": "idx_bank_txns_org_reconciled"}),
    ("bank_transactions", [("transaction_id", 1)], {"name": "idx_bank_txns_id", "unique": True}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # USERS / AUTH
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("users", [("email", 1)], {"name": "idx_users_email", "unique": True}),
    ("users", [("user_id", 1)], {"name": "idx_users_id", "unique": True}),
    
    ("organization_users", [("user_id", 1), ("organization_id", 1)], {"name": "idx_org_users_user_org", "unique": True}),
    ("organization_users", [("organization_id", 1), ("role", 1), ("status", 1)], {"name": "idx_org_users_org_role_status"}),
    
    ("organizations", [("organization_id", 1)], {"name": "idx_organizations_id", "unique": True}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FAILURE CARDS (EFI)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("failure_cards", [("organization_id", 1), ("status", 1)], {"name": "idx_failure_cards_org_status"}),
    ("failure_cards", [("failure_card_id", 1)], {"name": "idx_failure_cards_id", "unique": True}),
    ("failure_cards", [("category", 1), ("sub_category", 1)], {"name": "idx_failure_cards_category"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAYMENTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("payments_received", [("organization_id", 1), ("payment_date", -1)], {"name": "idx_payments_org_date"}),
    ("payments_received", [("invoice_id", 1)], {"name": "idx_payments_invoice"}),
    ("payments_received", [("payment_id", 1)], {"name": "idx_payments_id", "unique": True}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CREDIT NOTES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("credit_notes", [("organization_id", 1), ("status", 1)], {"name": "idx_credit_notes_org_status"}),
    ("credit_notes", [("credit_note_id", 1)], {"name": "idx_credit_notes_id", "unique": True}),
    ("credit_notes", [("invoice_id", 1)], {"name": "idx_credit_notes_invoice"}),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NOTIFICATIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ("notifications", [("user_id", 1), ("read", 1), ("created_at", -1)], {"name": "idx_notifications_user_read"}),
    ("notifications", [("organization_id", 1), ("created_at", -1)], {"name": "idx_notifications_org_created"}),
]


async def create_indexes():
    """Create all indexes with background=True (non-blocking)"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'battwheels_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    logger.info("=" * 60)
    logger.info("BATTWHEELS OS - PERFORMANCE INDEX MIGRATION")
    logger.info("=" * 60)
    logger.info(f"Database: {db_name}")
    logger.info(f"Total indexes to create: {len(INDEXES)}")
    logger.info("")
    
    created = 0
    skipped = 0
    failed = 0
    collections_touched = set()
    
    for collection_name, index_spec, options in INDEXES:
        try:
            # Add background=True for non-blocking index creation
            options['background'] = True
            
            collection = db[collection_name]
            collections_touched.add(collection_name)
            
            # Create the index
            result = await collection.create_index(index_spec, **options)
            
            logger.info(f"✓ Created: {options['name']} on {collection_name}")
            created += 1
            
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                logger.info(f"○ Skipped (exists): {options['name']} on {collection_name}")
                skipped += 1
            else:
                logger.error(f"✗ Failed: {options['name']} on {collection_name} - {e}")
                failed += 1
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("MIGRATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Created: {created}")
    logger.info(f"  Skipped (already exist): {skipped}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Collections touched: {len(collections_touched)}")
    logger.info(f"  Collections: {', '.join(sorted(collections_touched))}")
    logger.info("")
    
    if failed > 0:
        logger.warning("Some indexes failed to create. Review errors above.")
    else:
        logger.info("All indexes created successfully!")
    
    client.close()
    return created, skipped, failed


async def list_indexes():
    """List all indexes in the database"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'battwheels_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    collections = await db.list_collection_names()
    
    print("\n" + "=" * 60)
    print("CURRENT DATABASE INDEXES")
    print("=" * 60)
    
    total_indexes = 0
    for coll_name in sorted(collections):
        indexes = await db[coll_name].index_information()
        if len(indexes) > 1:  # More than just _id index
            print(f"\n{coll_name}:")
            for idx_name, idx_info in indexes.items():
                if idx_name != "_id_":
                    total_indexes += 1
                    keys = idx_info.get('key', [])
                    print(f"  - {idx_name}: {keys}")
    
    print(f"\nTotal custom indexes: {total_indexes}")
    client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        asyncio.run(list_indexes())
    else:
        asyncio.run(create_indexes())
