"""
Battwheels OS - Data Management API Routes
Provides endpoints for data sanitization, sync management, and monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

from services.data_sanitization_service import DataSanitizationService, DataValidationService
from services.zoho_realtime_sync import ZohoRealTimeSyncService
from core.org.dependencies import get_org_id_from_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data-management", tags=["Data Management"])


def get_db():
    from server import db
    return db


# ============== SANITIZATION ENDPOINTS ==============

class SanitizationRequest(BaseModel):
    mode: str = "audit"  # "audit" or "delete"
    collections: Optional[List[str]] = None


async def get_org_id(request: Request) -> str:
    """Get organization ID from request header"""
    org_id = request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID header required")
    return org_id


@router.post("/sanitize")
async def sanitize_data(
    request: Request,
    sanitization_request: SanitizationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Sanitize test/dummy data from the organization.
    
    - mode: "audit" to preview, "delete" to actually remove data
    - collections: specific collections to sanitize (optional, defaults to all)
    """
    db = get_db()
    org_id = await get_org_id(request)
    service = DataSanitizationService(db)
    
    if sanitization_request.mode == "audit":
        # Run audit synchronously for preview
        report = await service.run_sanitization(
            organization_id=org_id,
            mode="audit",
            collections=sanitization_request.collections
        )
        return {"code": 0, "report": report.dict()}
    
    elif sanitization_request.mode == "delete":
        # Run deletion in background
        job_id = f"SAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        async def run_deletion():
            await service.run_sanitization(
                organization_id=org_id,
                mode="delete",
                collections=sanitization_request.collections
            )
        
        background_tasks.add_task(run_deletion)
        
        return {
            "code": 0,
            "message": "Sanitization started in background",
            "job_id": job_id
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'audit' or 'delete'")


@router.get("/sanitize/status/{job_id}")
async def get_sanitization_status(job_id: str, org_id: str = Depends(require_organization)):
    """Get status of a sanitization job"""
    db = get_db()
    service = DataSanitizationService(db)
    
    report = await service.get_sanitization_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"code": 0, "report": report.dict()}


@router.post("/sanitize/rollback/{job_id}")
async def rollback_sanitization(job_id: str, org_id: str = Depends(require_organization)):
    """Rollback a sanitization job using backups"""
    db = get_db()
    service = DataSanitizationService(db)
    
    result = await service.rollback_sanitization(job_id)
    return {"code": 0, "result": result}


@router.get("/sanitize/history")
async def get_sanitization_history(limit: int = 20, org_id: str = Depends(require_organization)):
    """Get history of sanitization jobs"""
    db = get_db()
    service = DataSanitizationService(db)
    
    jobs = await service.list_sanitization_jobs(org_id, limit)
    return {"code": 0, "jobs": jobs}


# ============== VALIDATION ENDPOINTS ==============

@router.get("/validate/integrity")
async def validate_data_integrity(org_id: str = Depends(require_organization)):
    """Validate referential integrity of data"""
    db = get_db()
    service = DataValidationService(db)
    
    result = await service.validate_referential_integrity(org_id)
    return {"code": 0, "validation": result}


@router.get("/validate/completeness")
async def validate_data_completeness(org_id: str = Depends(require_organization)):
    """Validate data completeness"""
    db = get_db()
    service = DataValidationService(db)
    
    result = await service.validate_data_completeness(org_id)
    return {"code": 0, "validation": result}


# ============== ZOHO SYNC ENDPOINTS ==============

@router.get("/sync/test-connection")
async def test_zoho_connection():
    """Test connection to Zoho Books"""
    db = get_db()
    service = ZohoRealTimeSyncService(db)
    
    result = await service.test_connection()
    return {"code": 0, "connection": result}


@router.post("/sync/full")
async def run_full_sync(
    background_tasks: BackgroundTasks,
    org_id: str = Depends(require_organization)
):
    """Run full sync from Zoho Books (runs in background)"""
    db = get_db()
    service = ZohoRealTimeSyncService(db)
    
    # Start sync in background
    sync_id = f"FULLSYNC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    async def run_sync():
        await service.run_full_sync(org_id)
    
    background_tasks.add_task(run_sync)
    
    return {
        "code": 0,
        "message": "Full sync started in background",
        "sync_id": sync_id
    }


class ModuleSyncRequest(BaseModel):
    module: str
    full_sync: bool = False


@router.post("/sync/module")
async def sync_single_module(
    request: ModuleSyncRequest,
    org_id: str = Depends(require_organization)
):
    """Sync a single module from Zoho Books"""
    db = get_db()
    service = ZohoRealTimeSyncService(db)
    
    result = await service.sync_module(
        module=request.module,
        organization_id=org_id,
        full_sync=request.full_sync
    )
    
    return {"code": 0, "result": result}


@router.get("/sync/status")
async def get_sync_status(org_id: str = Depends(require_organization)):
    """Get sync status for all modules"""
    db = get_db()
    service = ZohoRealTimeSyncService(db)
    
    status = await service.get_sync_status(org_id)
    return {"code": 0, "status": status}


@router.get("/sync/history")
async def get_sync_history(limit: int = 20, org_id: str = Depends(require_organization)):
    """Get sync job history"""
    db = get_db()
    service = ZohoRealTimeSyncService(db)
    
    history = await service.get_sync_history(org_id, limit)
    return {"code": 0, "history": history}


# ============== WEBHOOK ENDPOINT ==============

class WebhookPayload(BaseModel):
    event_type: str
    module: str
    resource_id: str
    organization_id: str
    timestamp: Optional[str] = None
    payload: Optional[Dict] = None


@router.post("/sync/webhook")
async def receive_zoho_webhook(payload: WebhookPayload):
    """Receive webhook notifications from Zoho Books"""
    db = get_db()
    service = ZohoRealTimeSyncService(db)
    
    from services.zoho_realtime_sync import ZohoWebhookPayload
    
    webhook = ZohoWebhookPayload(
        event_type=payload.event_type,
        module=payload.module,
        resource_id=payload.resource_id,
        organization_id=payload.organization_id,
        timestamp=payload.timestamp or datetime.now(timezone.utc).isoformat(),
        payload=payload.payload
    )
    
    result = await service.process_webhook(webhook)
    return {"code": 0, "result": result}


# ============== DATA COUNTS ==============

@router.get("/counts")
async def get_data_counts(org_id: str = Depends(require_organization)):
    """Get record counts for all collections"""
    db = get_db()
    
    collections = [
        "vehicles", "tickets", "work_orders", "items", "contacts",
        "invoices", "estimates", "bills", "expenses", "payments",
        "customerpayments", "vendorpayments", "purchaseorders",
        "salesorders", "creditnotes", "failure_cards", "inventory"
    ]
    
    counts = {}
    for col in collections:
        try:
            total = await db[col].count_documents({"organization_id": org_id})
            zoho_synced = await db[col].count_documents({
                "organization_id": org_id,
                "source": "zoho_books"
            })
            counts[col] = {
                "total": total,
                "zoho_synced": zoho_synced,
                "local_only": total - zoho_synced
            }
        except Exception:
            counts[col] = {"total": 0, "zoho_synced": 0, "local_only": 0}
    
    return {"code": 0, "counts": counts}


# ============== CLEANUP OPERATIONS ==============

@router.post("/cleanup/negative-stock")
async def fix_negative_stock(org_id: str = Depends(require_organization)):
    """Fix negative stock values in inventory"""
    db = get_db()
    
    # Find items with negative stock
    result = await db.items.update_many(
        {"organization_id": org_id, "stock_on_hand": {"$lt": 0}},
        {"$set": {"stock_on_hand": 0, "stock_fixed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "code": 0,
        "message": f"Fixed {result.modified_count} items with negative stock"
    }


@router.post("/cleanup/orphaned-records")
async def cleanup_orphaned_records(org_id: str = Depends(require_organization)):
    """Clean up orphaned records (e.g., invoices without customers)"""
    db = get_db()
    
    cleaned = {
        "invoice_line_items_without_invoice": 0,
        "estimate_line_items_without_estimate": 0,
        "contact_persons_without_contact": 0
    }
    
    # Get valid parent IDs
    invoice_ids = set()
    async for inv in db.invoices.find({"organization_id": org_id}, {"invoice_id": 1}):
        invoice_ids.add(inv.get("invoice_id"))
    
    estimate_ids = set()
    async for est in db.estimates.find({"organization_id": org_id}, {"estimate_id": 1}):
        estimate_ids.add(est.get("estimate_id"))
    
    contact_ids = set()
    async for con in db.contacts.find({"organization_id": org_id}, {"contact_id": 1}):
        contact_ids.add(con.get("contact_id"))
    
    # Clean orphaned line items
    if invoice_ids:
        result = await db.invoice_line_items.delete_many({
            "organization_id": org_id,
            "invoice_id": {"$nin": list(invoice_ids)}
        })
        cleaned["invoice_line_items_without_invoice"] = result.deleted_count
    
    if estimate_ids:
        result = await db.estimate_line_items.delete_many({
            "organization_id": org_id,
            "estimate_id": {"$nin": list(estimate_ids)}
        })
        cleaned["estimate_line_items_without_estimate"] = result.deleted_count
    
    if contact_ids:
        result = await db.contact_persons.delete_many({
            "organization_id": org_id,
            "contact_id": {"$nin": list(contact_ids)}
        })
        cleaned["contact_persons_without_contact"] = result.deleted_count
    
    return {"code": 0, "cleaned": cleaned}


@router.delete("/cleanup/test-data")
async def delete_test_data(org_id: str = Depends(require_organization)):
    """Quick delete of obvious test data (TEST_, DUMMY_, etc.)"""
    db = get_db()
    
    test_patterns = ["^TEST_", "^DUMMY_", "^test_", "^dummy_"]
    deleted = {}
    
    collections = ["contacts", "items", "vehicles", "tickets"]
    
    for col in collections:
        total_deleted = 0
        for pattern in test_patterns:
            result = await db[col].delete_many({
                "organization_id": org_id,
                "$or": [
                    {"name": {"$regex": pattern, "$options": "i"}},
                    {"contact_name": {"$regex": pattern, "$options": "i"}},
                    {"item_name": {"$regex": pattern, "$options": "i"}}
                ]
            })
            total_deleted += result.deleted_count
        
        deleted[col] = total_deleted
    
    return {"code": 0, "deleted": deleted}
