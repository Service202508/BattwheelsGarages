from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import Job, JobCreate, JobUpdate
from middleware import get_current_user
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/api/admin/jobs", tags=["admin-jobs"])
security = HTTPBearer()

from server import db


@router.get("/")
async def get_all_jobs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    is_active: Optional[bool] = Query(None),
    department: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """
    Get all job postings
    """
    try:
        await get_current_user(credentials)
        
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        if department:
            query["department"] = department
        
        jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {"jobs": jobs}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


@router.post("/")
async def create_job(
    job_data: JobCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create new job posting
    """
    try:
        await get_current_user(credentials)
        
        job = Job(**job_data.dict())
        await db.jobs.insert_one(job.dict())
        
        return {"message": "Job created successfully", "job": job.dict()}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get job by ID
    """
    try:
        await get_current_user(credentials)
        
        job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")


@router.put("/{job_id}")
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update job posting
    """
    try:
        await get_current_user(credentials)
        
        # Check if job exists
        existing = await db.jobs.find_one({"id": job_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in job_data.dict(exclude_unset=True).items()}
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": update_data}
        )
        
        updated_job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
        
        return {"message": "Job updated successfully", "job": updated_job}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating job: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete job posting
    """
    try:
        await get_current_user(credentials)
        
        result = await db.jobs.delete_one({"id": job_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"message": "Job deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")


@router.get("/{job_id}/applications")
async def get_job_applications(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = Query(100, le=500)
):
    """
    Get applications for a specific job
    """
    try:
        await get_current_user(credentials)
        
        applications = await db.career_applications.find(
            {"job_id": job_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {"applications": applications}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applications: {str(e)}")
