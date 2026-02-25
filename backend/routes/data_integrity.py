"""
Battwheels OS - Data Integrity API Routes
Endpoints for auditing and repairing data integrity issues
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data-integrity", tags=["data-integrity"])


def get_db():
    from server import db
    return db


def get_integrity_service():
    from services.data_integrity_service import DataIntegrityService
    return DataIntegrityService(get_db())


# ============== REQUEST/RESPONSE MODELS ==============

class AuditRequest(BaseModel):
    organization_id: Optional[str] = None  # Ignored — org comes from auth context


class RepairRequest(BaseModel):
    collection: str
    organization_id: Optional[str] = None
    dry_run: bool = True


class RefIntegrityRepairRequest(BaseModel):
    collection: str
    fk_field: str
    ref_collection: str
    ref_field: str
    organization_id: Optional[str] = None
    strategy: str = "create_placeholder"  # or "nullify"
    dry_run: bool = True


# ============== AUDIT ENDPOINTS ==============

@router.post("/audit")
async def run_data_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """
    Run comprehensive data integrity audit
    Checks field completeness, referential integrity, and data quality
    """
    service = get_integrity_service()
    
    try:
        results = await service.run_full_audit(request.organization_id)
        return {
            "code": 0,
            "status": "success",
            "audit": results
        }
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/history")
async def get_audit_history(limit: int = 10, organization_id: Optional[str] = None):
    """Get recent audit history"""
    db = get_db()
    
    filter_query = {}
    if organization_id:
        filter_query["organization_id"] = organization_id
    
    cursor = db.data_integrity_audits.find(
        filter_query,
        {"_id": 0}
    ).sort("started_at", -1).limit(limit)
    
    audits = await cursor.to_list(length=limit)
    
    return {"code": 0, "audits": audits}


@router.get("/audit/{audit_id}")
async def get_audit_details(audit_id: str):
    """Get details of a specific audit"""
    db = get_db()
    
    audit = await db.data_integrity_audits.find_one(
        {"audit_id": audit_id},
        {"_id": 0}
    )
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return {"code": 0, "audit": audit}


# ============== QUICK CHECK ENDPOINTS ==============

@router.get("/check/orphans/{collection}")
async def check_orphan_references(collection: str, organization_id: Optional[str] = None):
    """Quick check for orphan references in a collection"""
    service = get_integrity_service()
    
    fk_defs = service.FOREIGN_KEYS.get(collection)
    if not fk_defs:
        return {"code": 0, "message": f"No foreign key definitions for {collection}", "orphans": {}}
    
    results = await service._check_referential_integrity(collection, fk_defs, organization_id)
    
    return {
        "code": 0,
        "collection": collection,
        "orphan_checks": results
    }


@router.get("/check/completeness/{collection}")
async def check_field_completeness(collection: str, organization_id: Optional[str] = None):
    """Quick check for field completeness in a collection"""
    service = get_integrity_service()
    
    results = await service._check_field_completeness(collection, organization_id)
    
    return {
        "code": 0,
        "collection": collection,
        "completeness": results
    }


@router.get("/check/quality")
async def check_data_quality(organization_id: Optional[str] = None):
    """Quick check for data quality issues"""
    service = get_integrity_service()
    
    results = await service._check_data_quality(organization_id)
    
    return {
        "code": 0,
        "quality_checks": results
    }


# ============== REPAIR ENDPOINTS ==============

@router.post("/repair/normalize-fields")
async def repair_normalize_fields(request: RepairRequest):
    """
    Normalize field names (fix aliases) and set missing defaults
    Use dry_run=true to preview changes
    """
    service = get_integrity_service()
    
    try:
        results = await service.repair_field_completeness(
            request.collection,
            request.organization_id,
            request.dry_run
        )
        
        return {
            "code": 0,
            "status": "preview" if request.dry_run else "applied",
            "collection": request.collection,
            "repairs": results
        }
    except Exception as e:
        logger.error(f"Field normalization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repair/referential-integrity")
async def repair_referential_integrity(request: RefIntegrityRepairRequest):
    """
    Repair orphan references by creating placeholders or nullifying
    Strategies: 'create_placeholder' or 'nullify'
    """
    service = get_integrity_service()
    
    try:
        results = await service.repair_referential_integrity(
            request.collection,
            request.fk_field,
            request.ref_collection,
            request.ref_field,
            request.organization_id,
            request.strategy,
            request.dry_run
        )
        
        return {
            "code": 0,
            "status": "preview" if request.dry_run else "applied",
            "repairs": results
        }
    except Exception as e:
        logger.error(f"Referential integrity repair failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repair/normalize-invoices")
async def normalize_invoices(organization_id: Optional[str] = None):
    """
    Normalize invoice fields from various formats to standard Zoho Books format
    """
    service = get_integrity_service()
    
    try:
        results = await service.normalize_invoice_fields(organization_id)
        return {"code": 0, "status": "success", "results": results}
    except Exception as e:
        logger.error(f"Invoice normalization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repair/normalize-estimates")
async def normalize_estimates(organization_id: Optional[str] = None):
    """
    Normalize estimate fields from various formats to standard format
    """
    service = get_integrity_service()
    
    try:
        results = await service.normalize_estimate_fields(organization_id)
        return {"code": 0, "status": "success", "results": results}
    except Exception as e:
        logger.error(f"Estimate normalization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repair/sync-customer-refs")
async def sync_customer_references(organization_id: Optional[str] = None):
    """
    Synchronize customer IDs between Zoho-synced data and local records
    """
    service = get_integrity_service()
    
    try:
        results = await service.sync_customer_references(organization_id)
        return {"code": 0, "status": "success", "results": results}
    except Exception as e:
        logger.error(f"Customer reference sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repair/add-zoho-fields/{collection}")
async def add_zoho_standard_fields(collection: str, organization_id: Optional[str] = None):
    """
    Add missing Zoho Books standard fields with defaults
    """
    service = get_integrity_service()
    
    try:
        results = await service.add_missing_zoho_fields(collection, organization_id)
        return {"code": 0, "status": "success", "results": results}
    except Exception as e:
        logger.error(f"Adding Zoho fields failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== BATCH REPAIR ENDPOINTS ==============

@router.post("/repair/all")
async def repair_all_issues(
    organization_id: Optional[str] = None,
    dry_run: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Run all repairs in sequence:
    1. Normalize invoice fields
    2. Normalize estimate fields
    3. Sync customer references
    4. Add missing Zoho standard fields
    5. Create placeholder contacts for orphan references
    """
    service = get_integrity_service()
    db = get_db()
    
    repair_id = f"REPAIR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Log repair start
    await db.repair_logs.insert_one({
        "repair_id": repair_id,
        "status": "started",
        "dry_run": dry_run,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "organization_id": organization_id
    })
    
    results = {
        "repair_id": repair_id,
        "dry_run": dry_run,
        "steps": {}
    }
    
    try:
        # Step 1: Normalize invoices
        results["steps"]["normalize_invoices"] = await service.normalize_invoice_fields(organization_id)
        
        # Step 2: Normalize estimates
        results["steps"]["normalize_estimates"] = await service.normalize_estimate_fields(organization_id)
        
        # Step 3: Sync customer references
        results["steps"]["sync_customer_refs"] = await service.sync_customer_references(organization_id)
        
        # Step 4: Add Zoho fields to major collections
        for collection in ["invoices", "estimates", "contacts", "items", "bills"]:
            results["steps"][f"zoho_fields_{collection}"] = await service.add_missing_zoho_fields(
                collection, organization_id
            )
        
        # Step 5: Create placeholder contacts for orphan invoice customer_ids
        if not dry_run:
            results["steps"]["repair_invoice_customers"] = await service.repair_referential_integrity(
                "invoices", "customer_id", "contacts", "contact_id",
                organization_id, "create_placeholder", dry_run=False
            )
        
        # Update repair log
        await db.repair_logs.update_one(
            {"repair_id": repair_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "results": results
            }}
        )
        
        return {"code": 0, "status": "success", "results": results}
    
    except Exception as e:
        await db.repair_logs.update_one(
            {"repair_id": repair_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repair/history")
async def get_repair_history(limit: int = 10):
    """Get recent repair history"""
    db = get_db()
    
    cursor = db.repair_logs.find({}, {"_id": 0}).sort("started_at", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    return {"code": 0, "repair_logs": logs}


# ============== STATS ENDPOINT ==============

@router.get("/stats")
async def get_integrity_stats(organization_id: Optional[str] = None):
    """Get quick summary of data integrity status"""
    db = get_db()
    service = get_integrity_service()
    
    filter_query = {}
    if organization_id:
        filter_query["organization_id"] = organization_id
    
    stats = {
        "collections": {},
        "overall_health": "good"
    }
    
    # Get counts for major collections
    collections = ["invoices", "estimates", "contacts", "items", "bills", "payments", "expenses"]
    
    for coll in collections:
        total = await db[coll].count_documents(filter_query)
        stats["collections"][coll] = {"total": total}
    
    # Run quick quality check
    quality = await service._check_data_quality(organization_id)
    stats["quality_issues"] = quality
    
    # Determine overall health
    critical_issues = sum([
        quality.get("duplicate_invoice_numbers", 0),
        quality.get("invoices_balance_exceeds_total", 0),
        quality.get("negative_invoice_totals", 0),
    ])
    
    if critical_issues > 10:
        stats["overall_health"] = "critical"
    elif critical_issues > 0:
        stats["overall_health"] = "warning"
    
    return {"code": 0, "stats": stats}
