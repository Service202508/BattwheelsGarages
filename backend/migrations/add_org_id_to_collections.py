"""
Phase B - Data Layer Hardening: Organization ID Migration Script
================================================================

This script adds organization_id to all collections that need tenant scoping.
For existing single-org deployments, all data is assigned to the default org.

Collections are categorized as:
1. TENANT_DATA: Must have org_id for tenant isolation
2. SYSTEM_DATA: Shared across orgs (master data, system config)
3. HISTORY_DATA: Supporting tables that inherit from parent documents

Run: python migrations/add_org_id_to_collections.py
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Collections that MUST have organization_id for tenant isolation
TENANT_DATA_COLLECTIONS = [
    # Core business data
    "tickets", "vehicles", "inventory", "invoices", "estimates", "contacts",
    "customers", "suppliers", "items", "expenses", "payments",
    
    # Supporting business data
    "allocations", "sales_orders", "purchase_orders", "stock_transfers",
    "bills", "amc_contracts", "amc_subscriptions", "amc_plans",
    "ticket_estimates", "ticket_invoices", "employees", "bank_accounts",
    "journal_entries", "data_integrity_audits", "custom_fields",
    "expert_queue", "failure_cards", "efi_failure_cards",
    
    # History/Line items (must match parent org)
    "invoice_history", "invoice_line_items", "invoice_payments", "invoice_attachments",
    "estimate_history", "estimate_line_items", "estimate_attachments", "estimate_share_links",
    "ticket_estimate_history", "ticket_estimate_line_items", "ticket_payments",
    "salesorder_history", "salesorder_line_items", "salesorder_fulfillments",
    "po_line_items", "bill_history", "bill_line_items", "bill_payments",
    "contact_history", "contact_persons", "customer_history",
    "inventory_history", "item_history", "item_stock", "item_stock_locations",
    "item_prices", "item_variants", "item_bundles", "item_adjustments",
    "item_serial_numbers", "item_batch_numbers", "item_serial_batches",
    "payment_history", "payment_transactions",
    
    # Enhanced/v2 collections
    "invoices_enhanced", "estimates_enhanced", "contacts_enhanced",
    "customers_enhanced", "salesorders_enhanced", "bills_enhanced",
    "purchase_orders_enhanced", "inventory_adjustments_v2", "inv_adjustments_v2",
    
    # Supporting tables
    "addresses", "warehouses", "price_lists", "creditnotes", "vendorcredits",
    "vendorpayments", "customerpayments", "customer_credits", "customer_refunds",
    "recurring_invoices", "recurring_expenses", "delivery_challans",
    "fixed_assets", "shipments", "projects", "project_tasks",
    
    # EFI/AI data
    "efi_sessions", "efi_events", "efi_decision_trees", "ev_issue_suggestions",
    "ai_queries",
    
    # HR data
    "attendance", "leave_requests", "leave_balances", "leave_types", "payroll",
    
    # Audit/Logs
    "event_log", "notification_logs", "notifications", "technician_action_logs",
    "ticket_activities", "ticket_updates", "stock_transfer_audit",
    "reminder_history", "serial_batch_history", "adjustment_audit_log",
    
    # Settings (per-org)
    "invoice_settings", "estimate_settings", "bill_settings", "sales_order_settings",
    "salesorder_settings", "contact_settings", "customer_settings",
    "ticket_estimate_settings", "payment_settings", "reminder_settings",
    "notification_preferences", "organization_settings", "late_fee_settings",
    "item_preferences", "item_field_config", "item_custom_fields",
    
    # Other org-specific data
    "bankaccounts", "banktransactions", "chart_of_accounts", "chartofaccounts",
    "journals", "ledger", "opening_balances", "exchange_rates", "taxes",
    "counters", "pdf_templates", "role_permissions", "custom_modules",
    "import_jobs", "parsed_rows", "portal_sessions", "sync_logs",
    "parts", "service_items", "services", "bundle_components",
    "credit_applications", "business_customers", "payments_received",
    "books_customers", "books_invoices", "books_payments", "books_vendors",
    "salesorders", "purchaseorders", "inventory_adjustments",
    "bank_reconciliations", "adjustment_reasons", "contact_tags", "customer_tags",
    "item_groups", "active_timers", "time_entries", "workflow_rules",
]

# System/Master data - shared across all orgs or global configuration
SYSTEM_DATA_COLLECTIONS = [
    "users",  # Users are global, membership defines org access via organization_users
    "vehicle_categories",  # Master data
    "vehicle_models",  # Master data
    "organizations",  # Org definitions themselves
    "organization_users",  # Membership junction table
]

async def migrate_collection(db, collection_name: str, org_id: str) -> dict:
    """Add organization_id to all documents in a collection that don't have it"""
    
    # Check how many docs need migration
    missing_org = await db[collection_name].count_documents({"organization_id": {"$exists": False}})
    
    if missing_org == 0:
        return {"collection": collection_name, "migrated": 0, "status": "ALREADY_COMPLETE"}
    
    # Update all documents without org_id
    result = await db[collection_name].update_many(
        {"organization_id": {"$exists": False}},
        {"$set": {"organization_id": org_id}}
    )
    
    return {
        "collection": collection_name,
        "migrated": result.modified_count,
        "status": "MIGRATED"
    }

async def create_indexes(db, collection_name: str) -> dict:
    """Create index on organization_id for efficient tenant filtering"""
    try:
        await db[collection_name].create_index("organization_id")
        return {"collection": collection_name, "status": "INDEX_CREATED"}
    except Exception as e:
        return {"collection": collection_name, "status": f"INDEX_FAILED: {e}"}

async def run_migration():
    """Run the full migration"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Get the default organization
    org = await db.organizations.find_one({}, {"organization_id": 1})
    if not org:
        logger.error("No organization found! Cannot migrate.")
        return
    
    org_id = org["organization_id"]
    logger.info(f"Using organization: {org_id}")
    
    # Get existing collections
    existing_collections = set(await db.list_collection_names())
    
    # Filter to only collections that exist
    collections_to_migrate = [c for c in TENANT_DATA_COLLECTIONS if c in existing_collections]
    
    logger.info(f"Migrating {len(collections_to_migrate)} collections...")
    
    migration_results = []
    index_results = []
    
    for coll in collections_to_migrate:
        # Migrate data
        result = await migrate_collection(db, coll, org_id)
        migration_results.append(result)
        
        if result["migrated"] > 0:
            logger.info(f"  {coll}: migrated {result['migrated']} documents")
        
        # Create index
        idx_result = await create_indexes(db, coll)
        index_results.append(idx_result)
    
    # Summary
    total_migrated = sum(r["migrated"] for r in migration_results)
    collections_updated = len([r for r in migration_results if r["migrated"] > 0])
    
    logger.info("=" * 60)
    logger.info(f"Migration complete!")
    logger.info(f"  Total documents migrated: {total_migrated}")
    logger.info(f"  Collections updated: {collections_updated}")
    logger.info(f"  Collections already complete: {len(migration_results) - collections_updated}")
    logger.info(f"  Indexes created: {len(index_results)}")
    
    client.close()
    
    return {
        "total_migrated": total_migrated,
        "collections_updated": collections_updated,
        "results": migration_results
    }

if __name__ == "__main__":
    asyncio.run(run_migration())
