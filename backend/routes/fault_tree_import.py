"""
Battwheels OS - Fault Tree Import Routes
Admin interface for importing EV Failure Intelligence from Excel
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, BackgroundTasks
from typing import Optional
from datetime import datetime, timezone
import os
import tempfile
import aiohttp
import logging
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["Fault Tree Import"])

# Service references
db = None
import_service = None

def init_router(database):
    global db, import_service
    db = database
    
    from services.fault_tree_import import FaultTreeImportService
    import_service = FaultTreeImportService(database)
    
    return router


@router.post("/upload")
async def upload_fault_tree(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload Excel file for fault tree import
    
    1. Saves file temporarily
    2. Creates import job
    3. Triggers parsing in background
    """
    # Verify file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")
    
    # Get user info
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = "system"
    if token and db is not None:
        session = await db.user_sessions.find_one({"session_token": token})
        if session:
            user_id = session.get("user_id", "system")
    
    # Save file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create import job
    job = await import_service.create_import_job(
        filename=file.filename,
        file_url=None,
        user_id=user_id
    )
    
    # Parse and preview in background
    async def process_file():
        try:
            preview = await import_service.parse_and_preview(job.job_id, temp_path)
            logger.info(f"Parsed {preview.total_rows} rows for job {job.job_id}")
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            await db.import_jobs.update_one(
                {"job_id": job.job_id},
                {"$set": {"status": "failed", "error_details": [{"error": str(e)}]}}
            )
        finally:
            # Cleanup
            try:
                os.remove(temp_path)
                os.rmdir(temp_dir)
            except OSError:
                pass
    
    background_tasks.add_task(process_file)
    
    return {
        "message": "File uploaded, parsing started",
        "job_id": job.job_id,
        "filename": file.filename,
        "status": "validating"
    }


@router.post("/upload-url")
async def upload_from_url(
    request: Request,
    background_tasks: BackgroundTasks,
    file_url: str,
    filename: Optional[str] = None
):
    """
    Import from a URL (e.g., pre-uploaded asset)
    """
    # Get user info
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = "system"
    if token and db is not None:
        session = await db.user_sessions.find_one({"session_token": token})
        if session:
            user_id = session.get("user_id", "system")
    
    # Download file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, filename or "import.xlsx")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to download file: {response.status}")
                
                with open(temp_path, "wb") as f:
                    f.write(await response.read())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error downloading file: {e}")
    
    # Create import job
    job = await import_service.create_import_job(
        filename=filename or "import.xlsx",
        file_url=file_url,
        user_id=user_id
    )
    
    # Parse in background
    async def process_file():
        try:
            preview = await import_service.parse_and_preview(job.job_id, temp_path)
            logger.info(f"Parsed {preview.total_rows} rows for job {job.job_id}")
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            await db.import_jobs.update_one(
                {"job_id": job.job_id},
                {"$set": {"status": "failed", "error_details": [{"error": str(e)}]}}
            )
        finally:
            try:
                os.remove(temp_path)
                os.rmdir(temp_dir)
            except:
                pass
    
    background_tasks.add_task(process_file)
    
    return {
        "message": "File download started, parsing queued",
        "job_id": job.job_id,
        "filename": filename or "import.xlsx",
        "status": "validating"
    }


@router.get("/jobs")
async def list_import_jobs(request: Request, limit: int = 20):
    """List all import jobs"""
    jobs = await import_service.list_jobs(limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/jobs/{job_id}")
async def get_import_job(job_id: str, request: Request):
    """Get import job status and details"""
    job = await import_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


@router.get("/jobs/{job_id}/preview")
async def get_import_preview(job_id: str, request: Request):
    """Get parsed data preview before import"""
    job = await import_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    if job.get("status") not in ["validated", "completed", "partial"]:
        return {
            "message": f"Job status is '{job.get('status')}', preview not available yet",
            "job_id": job_id,
            "status": job.get("status")
        }
    
    # Get parsed rows
    valid_rows = await db.parsed_rows.find(
        {"job_id": job_id, "validation_status": "valid"},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    error_rows = await db.parsed_rows.find(
        {"job_id": job_id, "validation_status": "error"},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    warning_rows = await db.parsed_rows.find(
        {"job_id": job_id, "validation_status": "warning"},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    # Section breakdown
    pipeline = [
        {"$match": {"job_id": job_id}},
        {"$group": {
            "_id": {"vehicle": "$vehicle_category", "subsystem": "$subsystem_type"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    sections = await db.parsed_rows.aggregate(pipeline).to_list(20)
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "total_rows": job.get("total_rows", 0),
        "valid_rows": job.get("valid_rows", 0),
        "error_rows": job.get("error_rows", 0),
        "warning_rows": job.get("warning_rows", 0),
        "sections": [
            {
                "vehicle_category": s["_id"]["vehicle"],
                "subsystem_type": s["_id"]["subsystem"],
                "count": s["count"]
            }
            for s in sections
        ],
        "sample_valid": valid_rows,
        "sample_errors": error_rows,
        "sample_warnings": warning_rows
    }


@router.post("/jobs/{job_id}/execute")
async def execute_import(
    job_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    skip_duplicates: bool = True,
    batch_size: int = 50
):
    """
    Execute the import after preview confirmation
    
    - skip_duplicates: If true, update existing cards instead of creating duplicates
    - batch_size: Number of records to process per batch
    """
    job = await import_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    if job.get("status") not in ["validated"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Job status must be 'validated' to execute. Current: {job.get('status')}"
        )
    
    # Execute in background
    async def run_import():
        try:
            result = await import_service.execute_import(
                job_id=job_id,
                skip_duplicates=skip_duplicates,
                batch_size=batch_size
            )
            logger.info(f"Import completed: {result}")
        except Exception as e:
            logger.error(f"Import failed: {e}")
            await db.import_jobs.update_one(
                {"job_id": job_id},
                {"$set": {"status": "failed", "error_details": [{"error": str(e)}]}}
            )
    
    background_tasks.add_task(run_import)
    
    return {
        "message": "Import started",
        "job_id": job_id,
        "status": "importing",
        "skip_duplicates": skip_duplicates,
        "batch_size": batch_size
    }


@router.delete("/jobs/{job_id}")
async def cancel_import(job_id: str, request: Request):
    """Cancel and cleanup an import job"""
    job = await import_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    # Can't cancel completed imports
    if job.get("status") in ["completed", "partial"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed imports")
    
    # Delete parsed rows
    await db.parsed_rows.delete_many({"job_id": job_id})
    
    # Update job status
    await db.import_jobs.update_one(
        {"job_id": job_id},
        {"$set": {"status": "cancelled"}}
    )
    
    return {"message": "Import job cancelled", "job_id": job_id}


@router.get("/jobs/{job_id}/results")
async def get_import_results(job_id: str, request: Request, limit: int = 20):
    """Get created/updated failure cards from import"""
    job = await import_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    if job.get("status") not in ["completed", "partial"]:
        return {
            "message": f"Import not completed. Status: {job.get('status')}",
            "job_id": job_id
        }
    
    # Get created cards
    created_ids = job.get("created_card_ids", [])[:limit]
    created_cards = []
    if created_ids:
        created_cards = await db.failure_cards.find(
            {"failure_id": {"$in": created_ids}},
            {"_id": 0, "failure_id": 1, "title": 1, "subsystem_category": 1, "status": 1}
        ).to_list(limit)
    
    # Get updated cards
    updated_ids = job.get("updated_card_ids", [])[:limit]
    updated_cards = []
    if updated_ids:
        updated_cards = await db.failure_cards.find(
            {"failure_id": {"$in": updated_ids}},
            {"_id": 0, "failure_id": 1, "title": 1, "version": 1}
        ).to_list(limit)
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "summary": {
            "created": job.get("imported_count", 0),
            "updated": job.get("updated_count", 0),
            "skipped": job.get("skipped_count", 0),
            "errors": len(job.get("error_details", []))
        },
        "created_cards": created_cards,
        "updated_cards": updated_cards,
        "errors": job.get("error_details", [])[:10]
    }


# ==================== QUICK IMPORT ENDPOINT ====================

@router.post("/quick")
async def quick_import(
    request: Request,
    background_tasks: BackgroundTasks,
    file_url: str = "https://customer-assets.emergentagent.com/job_ev-command-3/artifacts/se20dto8_Fautl%20Tree%20-%20SOP%20V16_revision_fta_techn.xlsx"
):
    """
    Quick import from default Battwheels Master Fault Tree URL
    Single-click import for admin convenience
    """
    return await upload_from_url(
        request=request,
        background_tasks=background_tasks,
        file_url=file_url,
        filename="Battwheels_Master_Fault_Tree.xlsx"
    )
