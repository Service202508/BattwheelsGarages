# Data Migration Module - Legacy to Enhanced Migration
# Migrates legacy customers/vendors to unified contacts_enhanced collection

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import motor.motor_asyncio
import os
import uuid
import logging
from fastapi import Request
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-migration", tags=["Data Migration"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
contacts_enhanced_collection = db["contacts_enhanced"]
legacy_customers_collection = db["customers"]
legacy_vendors_collection = db["vendors"]
legacy_contacts_collection = db["contacts"]
migration_logs_collection = db["migration_logs"]

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

# ========================= MODELS =========================

class MigrationConfig(BaseModel):
    migrate_customers: bool = True
    migrate_vendors: bool = True
    skip_duplicates: bool = True
    dry_run: bool = False
    update_existing: bool = False

# ========================= HELPERS =========================

async def log_migration(action: str, details: str, count: int = 0, errors: List[str] = None):
    await migration_logs_collection.insert_one({
        "log_id": generate_id("LOG"),
        "action": action,
        "details": details,
        "count": count,
        "errors": errors or [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

def map_legacy_customer_to_contact(customer: dict) -> dict:
    """Map legacy customer document to contacts_enhanced format"""
    contact_id = customer.get("customer_id") or generate_id("CON")
    
    # Determine source
    source = "zoho_import" if customer.get("zoho_customer_id") else "legacy_migration"
    
    return {
        "contact_id": contact_id,
        "contact_number": customer.get("customer_number") or contact_id,
        "contact_type": "customer",
        "name": customer.get("customer_name") or customer.get("display_name") or customer.get("name", "Unknown"),
        "display_name": customer.get("display_name") or customer.get("customer_name") or customer.get("name", "Unknown"),
        "company_name": customer.get("company_name", ""),
        "first_name": customer.get("first_name", ""),
        "last_name": customer.get("last_name", ""),
        "email": (customer.get("email") or "").lower().strip(),
        "phone": customer.get("phone", ""),
        "mobile": customer.get("mobile", ""),
        "website": customer.get("website", ""),
        "currency_code": customer.get("currency_code") or customer.get("currency_id") or "INR",
        "payment_terms": customer.get("payment_terms") or 30,
        "credit_limit": float(customer.get("credit_limit") or 0),
        "opening_balance": float(customer.get("opening_balance") or 0),
        "opening_balance_type": "credit",
        "gstin": (customer.get("gst_no") or customer.get("gstin") or customer.get("gst_identification_number") or "").upper().strip(),
        "pan": (customer.get("pan_no") or customer.get("pan") or "").upper().strip(),
        "place_of_supply": customer.get("place_of_supply") or customer.get("gst_treatment_state") or "",
        "gst_treatment": customer.get("gst_treatment") or "registered",
        "tax_treatment": customer.get("tax_treatment") or "business_gst",
        "customer_type": customer.get("customer_type") or "business",
        "customer_segment": customer.get("customer_segment") or customer.get("customer_sub_type") or "",
        "industry": customer.get("industry") or "",
        "price_list_id": customer.get("price_list_id") or "",
        "discount_percent": float(customer.get("discount") or 0),
        "portal_enabled": customer.get("portal_enabled") or customer.get("customer_portal") or False,
        "portal_token": "",
        "notes": customer.get("notes") or customer.get("remarks") or "",
        "tags": customer.get("tags") or [],
        "custom_fields": customer.get("custom_fields") or customer.get("custom_field_hash") or {},
        "source": source,
        "referred_by": "",
        "is_active": customer.get("status") != "inactive" and customer.get("is_active", True),
        "outstanding_receivable": float(customer.get("outstanding_receivable_amount") or customer.get("balance") or 0),
        "outstanding_payable": 0,
        "unused_credits": float(customer.get("unused_credits") or 0),
        "has_billing_address": bool(customer.get("billing_address")),
        "has_shipping_address": bool(customer.get("shipping_address")),
        "contact_persons_count": len(customer.get("contact_persons") or []),
        "addresses_count": 0,
        "zoho_contact_id": customer.get("contact_id") or customer.get("zoho_customer_id") or "",
        "zoho_customer_id": customer.get("zoho_customer_id") or "",
        "created_time": customer.get("created_time") or datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat(),
        "last_activity_time": customer.get("last_modified_time") or datetime.now(timezone.utc).isoformat(),
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "migration_source": "legacy_customers"
    }

def map_legacy_vendor_to_contact(vendor: dict) -> dict:
    """Map legacy vendor document to contacts_enhanced format"""
    contact_id = vendor.get("vendor_id") or generate_id("CON")
    
    source = "zoho_import" if vendor.get("zoho_vendor_id") else "legacy_migration"
    
    return {
        "contact_id": contact_id,
        "contact_number": vendor.get("vendor_number") or contact_id,
        "contact_type": "vendor",
        "name": vendor.get("vendor_name") or vendor.get("display_name") or vendor.get("name", "Unknown"),
        "display_name": vendor.get("display_name") or vendor.get("vendor_name") or vendor.get("name", "Unknown"),
        "company_name": vendor.get("company_name", ""),
        "first_name": vendor.get("first_name", ""),
        "last_name": vendor.get("last_name", ""),
        "email": (vendor.get("email") or "").lower().strip(),
        "phone": vendor.get("phone", ""),
        "mobile": vendor.get("mobile", ""),
        "website": vendor.get("website", ""),
        "currency_code": vendor.get("currency_code") or vendor.get("currency_id") or "INR",
        "payment_terms": vendor.get("payment_terms") or 30,
        "credit_limit": 0,
        "opening_balance": float(vendor.get("opening_balance") or 0),
        "opening_balance_type": "debit",
        "gstin": (vendor.get("gst_no") or vendor.get("gstin") or vendor.get("gst_identification_number") or "").upper().strip(),
        "pan": (vendor.get("pan_no") or vendor.get("pan") or "").upper().strip(),
        "place_of_supply": vendor.get("place_of_supply") or "",
        "gst_treatment": vendor.get("gst_treatment") or "registered",
        "tax_treatment": vendor.get("tax_treatment") or "business_gst",
        "customer_type": "",
        "customer_segment": "",
        "industry": vendor.get("industry") or "",
        "price_list_id": "",
        "discount_percent": 0,
        "portal_enabled": False,
        "portal_token": "",
        "notes": vendor.get("notes") or vendor.get("remarks") or "",
        "tags": vendor.get("tags") or [],
        "custom_fields": vendor.get("custom_fields") or vendor.get("custom_field_hash") or {},
        "source": source,
        "referred_by": "",
        "is_active": vendor.get("status") != "inactive" and vendor.get("is_active", True),
        "outstanding_receivable": 0,
        "outstanding_payable": float(vendor.get("outstanding_payable_amount") or vendor.get("balance") or 0),
        "unused_credits": 0,
        "has_billing_address": bool(vendor.get("billing_address")),
        "has_shipping_address": bool(vendor.get("shipping_address")),
        "contact_persons_count": len(vendor.get("contact_persons") or []),
        "addresses_count": 0,
        "zoho_contact_id": vendor.get("contact_id") or vendor.get("zoho_vendor_id") or "",
        "zoho_vendor_id": vendor.get("zoho_vendor_id") or "",
        "created_time": vendor.get("created_time") or datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat(),
        "last_activity_time": vendor.get("last_modified_time") or datetime.now(timezone.utc).isoformat(),
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "migration_source": "legacy_vendors"
    }

# ========================= STATUS ENDPOINT =========================

@router.get("/status")
async def get_migration_status(request: Request):
    org_id = extract_org_id(request)
    """Get current migration status and statistics"""
    # Count legacy records
    legacy_customers = await legacy_customers_collection.count_documents(org_query(org_id))
    legacy_vendors = await legacy_vendors_collection.count_documents(org_query(org_id))
    legacy_contacts = await legacy_contacts_collection.count_documents(org_query(org_id))
    
    # Count enhanced records
    enhanced_total = await contacts_enhanced_collection.count_documents(org_query(org_id))
    enhanced_customers = await contacts_enhanced_collection.count_documents({"contact_type": {"$in": ["customer", "both"]}})
    enhanced_vendors = await contacts_enhanced_collection.count_documents({"contact_type": {"$in": ["vendor", "both"]}})
    
    # Count migrated records
    migrated_customers = await contacts_enhanced_collection.count_documents({"migration_source": "legacy_customers"})
    migrated_vendors = await contacts_enhanced_collection.count_documents({"migration_source": "legacy_vendors"})
    zoho_imported = await contacts_enhanced_collection.count_documents({"source": "zoho_import"})
    
    # Get recent logs
    recent_logs = await migration_logs_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)
    
    return {
        "code": 0,
        "status": {
            "legacy": {
                "customers": legacy_customers,
                "vendors": legacy_vendors,
                "contacts": legacy_contacts,
                "total": legacy_customers + legacy_vendors + legacy_contacts
            },
            "enhanced": {
                "total": enhanced_total,
                "customers": enhanced_customers,
                "vendors": enhanced_vendors
            },
            "migrated": {
                "from_legacy_customers": migrated_customers,
                "from_legacy_vendors": migrated_vendors,
                "from_zoho": zoho_imported,
                "total_migrated": migrated_customers + migrated_vendors
            },
            "pending": {
                "customers": legacy_customers - migrated_customers,
                "vendors": legacy_vendors - migrated_vendors
            }
        },
        "recent_logs": recent_logs
    }

# ========================= PREVIEW ENDPOINT =========================

@router.get("/preview")
async def preview_migration(request: Request, limit: int = 10):
    org_id = extract_org_id(request)
    """Preview records that will be migrated"""
    # Sample customers
    customers = await legacy_customers_collection.find({}, {"_id": 0}).limit(limit).to_list(limit)
    customer_previews = [
        {
            "source": "legacy_customers",
            "original": {"customer_id": c.get("customer_id"), "name": c.get("customer_name") or c.get("name"), "email": c.get("email")},
            "mapped": {"contact_id": c.get("customer_id"), "name": map_legacy_customer_to_contact(c)["name"], "type": "customer"}
        }
        for c in customers
    ]
    
    # Sample vendors
    vendors = await legacy_vendors_collection.find({}, {"_id": 0}).limit(limit).to_list(limit)
    vendor_previews = [
        {
            "source": "legacy_vendors",
            "original": {"vendor_id": v.get("vendor_id"), "name": v.get("vendor_name") or v.get("name"), "email": v.get("email")},
            "mapped": {"contact_id": v.get("vendor_id"), "name": map_legacy_vendor_to_contact(v)["name"], "type": "vendor"}
        }
        for v in vendors
    ]
    
    return {
        "code": 0,
        "preview": {
            "customers": customer_previews,
            "vendors": vendor_previews
        }
    }

# ========================= MIGRATION ENDPOINT =========================

@router.post("/run")
async def run_migration(request: Request, config: MigrationConfig, background_tasks: BackgroundTasks):
    org_id = extract_org_id(request)
    """Run the migration process"""
    results = {
        "customers_migrated": 0,
        "vendors_migrated": 0,
        "skipped_duplicates": 0,
        "errors": [],
        "dry_run": config.dry_run
    }
    
    # Migrate customers
    if config.migrate_customers:
        customers = await legacy_customers_collection.find(org_query(org_id)).to_list(5000)
        
        for customer in customers:
            try:
                mapped = map_legacy_customer_to_contact(customer)
                
                # Check for existing
                existing = await contacts_enhanced_collection.find_one({
                    "$or": [
                        {"contact_id": mapped["contact_id"]},
                        {"email": mapped["email"]} if mapped["email"] else {"_id": None},
                        {"gstin": mapped["gstin"]} if mapped["gstin"] else {"_id": None}
                    ]
                })
                
                if existing:
                    if config.skip_duplicates:
                        results["skipped_duplicates"] += 1
                        continue
                    elif config.update_existing:
                        if not config.dry_run:
                            mapped["contact_id"] = existing["contact_id"]
                            await contacts_enhanced_collection.update_one(
                                {"contact_id": existing["contact_id"]},
                                {"$set": mapped}
                            )
                        results["customers_migrated"] += 1
                        continue
                
                if not config.dry_run:
                    await contacts_enhanced_collection.insert_one(mapped)
                results["customers_migrated"] += 1
                
            except Exception as e:
                results["errors"].append(f"Customer {customer.get('customer_id', 'unknown')}: {str(e)}")
    
    # Migrate vendors
    if config.migrate_vendors:
        vendors = await legacy_vendors_collection.find(org_query(org_id)).to_list(5000)
        
        for vendor in vendors:
            try:
                mapped = map_legacy_vendor_to_contact(vendor)
                
                # Check for existing
                existing = await contacts_enhanced_collection.find_one({
                    "$or": [
                        {"contact_id": mapped["contact_id"]},
                        {"email": mapped["email"]} if mapped["email"] else {"_id": None},
                        {"gstin": mapped["gstin"]} if mapped["gstin"] else {"_id": None}
                    ]
                })
                
                if existing:
                    if config.skip_duplicates:
                        results["skipped_duplicates"] += 1
                        continue
                    elif config.update_existing:
                        # If existing is customer, upgrade to both
                        if existing.get("contact_type") == "customer" and not config.dry_run:
                            await contacts_enhanced_collection.update_one(
                                {"contact_id": existing["contact_id"]},
                                {"$set": {"contact_type": "both", "outstanding_payable": mapped["outstanding_payable"]}}
                            )
                        results["vendors_migrated"] += 1
                        continue
                
                if not config.dry_run:
                    await contacts_enhanced_collection.insert_one(mapped)
                results["vendors_migrated"] += 1
                
            except Exception as e:
                results["errors"].append(f"Vendor {vendor.get('vendor_id', 'unknown')}: {str(e)}")
    
    # Log the migration
    if not config.dry_run:
        await log_migration(
            "migration_completed",
            f"Migrated {results['customers_migrated']} customers, {results['vendors_migrated']} vendors",
            results["customers_migrated"] + results["vendors_migrated"],
            results["errors"]
        )
    
    return {
        "code": 0,
        "message": "Migration preview" if config.dry_run else "Migration completed",
        "results": results
    }

# ========================= ZOHO SYNC MIGRATION =========================

@router.post("/sync-from-zoho")
async def sync_from_zoho_contacts(request: Request):
    org_id = extract_org_id(request)
    """Migrate contacts that were synced from Zoho into enhanced collection"""
    results = {"migrated": 0, "skipped": 0, "errors": []}
    
    # Find Zoho-synced contacts in legacy collection
    zoho_contacts = await legacy_contacts_collection.find({"contact_id": {"$exists": True}}).to_list(5000)
    
    for contact in zoho_contacts:
        try:
            # Determine contact type from Zoho data
            contact_type = "customer"
            if contact.get("vendor_id"):
                contact_type = "vendor"
            elif contact.get("contact_type"):
                contact_type = contact.get("contact_type").lower()
            
            # Check if already exists
            existing = await contacts_enhanced_collection.find_one({
                "$or": [
                    {"zoho_contact_id": contact.get("contact_id")},
                    {"contact_id": contact.get("contact_id")}
                ]
            })
            
            if existing:
                results["skipped"] += 1
                continue
            
            mapped = {
                "contact_id": contact.get("contact_id") or generate_id("CON"),
                "contact_number": contact.get("contact_number") or contact.get("contact_id"),
                "contact_type": contact_type,
                "name": contact.get("contact_name") or contact.get("display_name", "Unknown"),
                "display_name": contact.get("display_name") or contact.get("contact_name", "Unknown"),
                "company_name": contact.get("company_name", ""),
                "first_name": contact.get("first_name", ""),
                "last_name": contact.get("last_name", ""),
                "email": (contact.get("email") or "").lower().strip(),
                "phone": contact.get("phone", ""),
                "mobile": contact.get("mobile", ""),
                "website": contact.get("website", ""),
                "currency_code": contact.get("currency_code") or "INR",
                "payment_terms": contact.get("payment_terms") or 30,
                "credit_limit": float(contact.get("credit_limit") or 0),
                "gstin": (contact.get("gst_no") or contact.get("gst_identification_number") or "").upper().strip(),
                "pan": (contact.get("pan_no") or "").upper().strip(),
                "place_of_supply": contact.get("place_of_supply", ""),
                "gst_treatment": contact.get("gst_treatment") or "registered",
                "notes": contact.get("notes", ""),
                "tags": [],
                "custom_fields": contact.get("custom_field_hash") or {},
                "source": "zoho_import",
                "is_active": contact.get("status") != "inactive",
                "outstanding_receivable": float(contact.get("outstanding_receivable_amount") or 0),
                "outstanding_payable": float(contact.get("outstanding_payable_amount") or 0),
                "unused_credits": float(contact.get("unused_credits") or 0),
                "zoho_contact_id": contact.get("contact_id"),
                "created_time": contact.get("created_time") or datetime.now(timezone.utc).isoformat(),
                "updated_time": datetime.now(timezone.utc).isoformat(),
                "migrated_at": datetime.now(timezone.utc).isoformat(),
                "migration_source": "zoho_contacts"
            }
            
            await contacts_enhanced_collection.insert_one(mapped)
            results["migrated"] += 1
            
        except Exception as e:
            results["errors"].append(f"Contact {contact.get('contact_id', 'unknown')}: {str(e)}")
    
    await log_migration("zoho_sync_migration", f"Migrated {results['migrated']} Zoho contacts", results["migrated"], results["errors"])
    
    return {"code": 0, "message": "Zoho contacts migration completed", "results": results}

# ========================= CLEANUP =========================

@router.post("/cleanup-duplicates")
async def cleanup_duplicates(request: Request, dry_run: bool = True):
    org_id = extract_org_id(request)
    """Find and optionally remove duplicate contacts"""
    # Find duplicates by email
    email_pipeline = [
        {"$match": {"email": {"$nin": ["", None]}}},
        {"$group": {"_id": "$email", "count": {"$sum": 1}, "ids": {"$push": "$contact_id"}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    email_dupes = await contacts_enhanced_collection.aggregate(email_pipeline).to_list(100)
    
    # Find duplicates by GSTIN
    gstin_pipeline = [
        {"$match": {"gstin": {"$nin": ["", None]}}},
        {"$group": {"_id": "$gstin", "count": {"$sum": 1}, "ids": {"$push": "$contact_id"}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    gstin_dupes = await contacts_enhanced_collection.aggregate(gstin_pipeline).to_list(100)
    
    removed = 0
    if not dry_run:
        # Keep the first (oldest) and remove duplicates
        for dupe in email_dupes:
            ids_to_remove = dupe["ids"][1:]  # Keep first
            await contacts_enhanced_collection.delete_many({"contact_id": {"$in": ids_to_remove}})
            removed += len(ids_to_remove)
        
        for dupe in gstin_dupes:
            ids_to_remove = dupe["ids"][1:]
            result = await contacts_enhanced_collection.delete_many({"contact_id": {"$in": ids_to_remove}})
            removed += result.deleted_count
    
    return {
        "code": 0,
        "duplicates_found": {
            "by_email": len(email_dupes),
            "by_gstin": len(gstin_dupes),
            "email_details": [{"email": d["_id"], "count": d["count"]} for d in email_dupes[:10]],
            "gstin_details": [{"gstin": d["_id"], "count": d["count"]} for d in gstin_dupes[:10]]
        },
        "removed": removed if not dry_run else "DRY RUN",
        "dry_run": dry_run
    }

# ========================= ROLLBACK =========================

@router.post("/rollback")
async def rollback_migration(request: Request, migration_source: str = "legacy_customers"):
    org_id = extract_org_id(request)
    """Rollback migrated contacts from a specific source"""
    if migration_source not in ["legacy_customers", "legacy_vendors", "zoho_contacts"]:
        raise HTTPException(status_code=400, detail="Invalid migration source")
    
    result = await contacts_enhanced_collection.delete_many({"migration_source": migration_source})
    
    await log_migration(
        "rollback",
        f"Rolled back {result.deleted_count} contacts from {migration_source}",
        result.deleted_count
    )
    
    return {"code": 0, "message": f"Rollback completed", "deleted": result.deleted_count}

# ========================= LOGS =========================

@router.get("/logs")
async def get_migration_logs(request: Request, limit: int = 50):
    org_id = extract_org_id(request)
    """Get migration logs"""
    logs = await migration_logs_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return {"code": 0, "logs": logs}
