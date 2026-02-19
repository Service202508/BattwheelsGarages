"""
Multi-Tenant Data Migration Script
Bootstraps default organization and migrates existing data

Run with: python -m scripts.migrate_multi_tenant
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import uuid

load_dotenv(Path(__file__).parent.parent / '.env')


async def migrate():
    """Run the multi-tenant migration"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 60)
    print("BATTWHEELS OS - MULTI-TENANT MIGRATION")
    print("=" * 60)
    
    # Step 1: Check if default organization exists
    existing_org = await db.organizations.find_one({"slug": "battwheels-default"})
    
    if existing_org:
        default_org_id = existing_org["organization_id"]
        print(f"✓ Default organization exists: {default_org_id}")
    else:
        # Create default organization
        default_org_id = f"org_{uuid.uuid4().hex[:12]}"
        default_org = {
            "organization_id": default_org_id,
            "name": "Battwheels Garages",
            "slug": "battwheels-default",
            "industry_type": "ev_garage",
            "plan_type": "professional",
            "logo_url": None,
            "website": "https://battwheels.in",
            "email": "admin@battwheels.in",
            "phone": "+91 9876543210",
            "address": "Sector 17, Gurugram",
            "city": "Gurugram",
            "state": "Haryana",
            "country": "India",
            "pincode": "122001",
            "gstin": "06AABCU9603R1ZM",
            "is_active": True,
            "total_users": 0,
            "total_vehicles": 0,
            "total_tickets": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": None
        }
        await db.organizations.insert_one(default_org)
        print(f"✓ Created default organization: {default_org_id}")
        
        # Create default settings
        default_settings = {
            "settings_id": f"set_{uuid.uuid4().hex[:12]}",
            "organization_id": default_org_id,
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "date_format": "DD/MM/YYYY",
            "fiscal_year_start": "04-01",
            "service_radius_km": 50,
            "operating_hours_start": "09:00",
            "operating_hours_end": "18:00",
            "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "tickets": {
                "default_priority": "medium",
                "auto_assign_enabled": True,
                "sla_hours_low": 72,
                "sla_hours_medium": 24,
                "sla_hours_high": 8,
                "sla_hours_critical": 2,
                "allow_customer_portal": True,
                "require_approval_for_close": False
            },
            "inventory": {
                "tracking_enabled": True,
                "low_stock_threshold": 10,
                "auto_reorder_enabled": False,
                "negative_stock_allowed": False,
                "require_serial_tracking": False,
                "require_batch_tracking": False
            },
            "invoices": {
                "default_payment_terms": 30,
                "auto_number_enabled": True,
                "invoice_prefix": "INV-",
                "estimate_prefix": "EST-",
                "salesorder_prefix": "SO-",
                "gst_enabled": True,
                "default_tax_rate": 18.0,
                "rounding_type": "round_half_up"
            },
            "notifications": {
                "email_enabled": True,
                "sms_enabled": False,
                "whatsapp_enabled": False,
                "notify_on_ticket_create": True,
                "notify_on_ticket_assign": True,
                "notify_on_invoice_create": True,
                "notify_on_payment_receive": True
            },
            "efi": {
                "failure_learning_enabled": True,
                "auto_suggest_diagnosis": True,
                "min_confidence_threshold": 0.7,
                "require_checklist_completion": True,
                "capture_diagnostic_photos": True
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.organization_settings.insert_one(default_settings)
        print("✓ Created default organization settings")
    
    # Step 2: Migrate existing users to organization
    print("\n--- Migrating Users ---")
    users = await db.users.find({}).to_list(1000)
    
    admin_user_id = None
    migrated_users = 0
    
    for user in users:
        user_id = user.get("user_id")
        
        # Check if already a member
        existing_membership = await db.organization_users.find_one({
            "organization_id": default_org_id,
            "user_id": user_id
        })
        
        if existing_membership:
            continue
        
        # Determine role based on existing role
        existing_role = user.get("role", "viewer")
        org_role = "viewer"
        if existing_role == "admin":
            org_role = "owner"
            admin_user_id = user_id
        elif existing_role == "manager":
            org_role = "admin"
        elif existing_role == "technician":
            org_role = "technician"
        elif existing_role == "dispatcher":
            org_role = "dispatcher"
        elif existing_role == "accountant":
            org_role = "accountant"
        
        membership = {
            "membership_id": f"mem_{uuid.uuid4().hex[:12]}",
            "organization_id": default_org_id,
            "user_id": user_id,
            "role": org_role,
            "status": "active",
            "custom_permissions": [],
            "invited_by": None,
            "invited_at": None,
            "joined_at": datetime.now(timezone.utc),
            "last_active_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.organization_users.insert_one(membership)
        migrated_users += 1
    
    print(f"✓ Migrated {migrated_users} users to organization")
    
    # Update organization creator
    if admin_user_id:
        await db.organizations.update_one(
            {"organization_id": default_org_id},
            {"$set": {"created_by": admin_user_id}}
        )
    
    # Step 3: Add organization_id to core collections
    print("\n--- Adding organization_id to Collections ---")
    
    collections_to_migrate = [
        ("vehicles", "vehicle_id"),
        ("tickets", "ticket_id"),
        ("invoices", "invoice_id"),
        ("estimates", "estimate_id"),
        ("sales_orders", "salesorder_id"),
        ("payments", "payment_id"),
        ("customers", "customer_id"),
        ("contacts", "contact_id"),
        ("inventory", "item_id"),
        ("items", "item_id"),
        ("suppliers", "supplier_id"),
        ("purchase_orders", "po_id"),
        ("expenses", "expense_id"),
        ("employees", "employee_id"),
        ("failure_cards", "card_id"),
        ("work_orders", "work_order_id"),
        ("amc_plans", "plan_id"),
        ("amc_subscriptions", "subscription_id"),
    ]
    
    for collection_name, id_field in collections_to_migrate:
        try:
            collection = db[collection_name]
            
            # Check if collection has documents without organization_id
            count_without_org = await collection.count_documents({
                "organization_id": {"$exists": False}
            })
            
            if count_without_org > 0:
                # Add organization_id to all documents
                result = await collection.update_many(
                    {"organization_id": {"$exists": False}},
                    {"$set": {"organization_id": default_org_id}}
                )
                print(f"  ✓ {collection_name}: Added org_id to {result.modified_count} documents")
            else:
                total = await collection.count_documents({})
                if total > 0:
                    print(f"  ✓ {collection_name}: Already has org_id ({total} documents)")
                else:
                    print(f"  - {collection_name}: Empty collection")
        except Exception as e:
            print(f"  ⚠ {collection_name}: {str(e)}")
    
    # Step 4: Create indexes for organization_id
    print("\n--- Creating Indexes ---")
    
    index_collections = [
        "vehicles", "tickets", "invoices", "estimates", "sales_orders",
        "payments", "customers", "contacts", "inventory", "items",
        "suppliers", "purchase_orders", "expenses", "employees",
        "failure_cards", "work_orders", "audit_logs"
    ]
    
    for collection_name in index_collections:
        try:
            collection = db[collection_name]
            await collection.create_index([("organization_id", 1)])
            print(f"  ✓ {collection_name}: Index created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  ✓ {collection_name}: Index already exists")
            else:
                print(f"  ⚠ {collection_name}: {str(e)}")
    
    # Step 5: Update organization stats
    print("\n--- Updating Organization Stats ---")
    
    user_count = await db.organization_users.count_documents({
        "organization_id": default_org_id,
        "status": "active"
    })
    
    vehicle_count = await db.vehicles.count_documents({
        "organization_id": default_org_id
    })
    
    ticket_count = await db.tickets.count_documents({
        "organization_id": default_org_id
    })
    
    await db.organizations.update_one(
        {"organization_id": default_org_id},
        {"$set": {
            "total_users": user_count,
            "total_vehicles": vehicle_count,
            "total_tickets": ticket_count,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    print(f"✓ Organization stats: {user_count} users, {vehicle_count} vehicles, {ticket_count} tickets")
    
    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"Default Organization ID: {default_org_id}")
    print(f"Default Organization Slug: battwheels-default")
    print(f"Users Migrated: {migrated_users}")
    print("\nNext steps:")
    print("1. Test organization endpoints: GET /api/org")
    print("2. Test settings endpoint: GET /api/org/settings")
    print("3. Test user listing: GET /api/org/users")
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
