from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["Public Content"])

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'test_database')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# ========== SERVICES ==========

@router.get("/services")
async def get_public_services():
    """Get all active services for public display"""
    try:
        services = await db.services.find(
            {"status": "active"},
            {"_id": 0}
        ).to_list(100)
        return {"services": services, "total": len(services)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{slug}")
async def get_service_by_slug(slug: str):
    """Get a single service by slug"""
    try:
        service = await db.services.find_one(
            {"slug": slug, "status": "active"},
            {"_id": 0}
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== BLOGS ==========

@router.get("/blogs")
async def get_public_blogs(limit: int = 20, skip: int = 0, category: Optional[str] = None):
    """Get all published blogs for public display"""
    try:
        query = {"status": "published"}
        if category:
            query["category"] = category
        
        # Try blog_posts collection first (used by admin), then blogs collection
        blogs = await db.blog_posts.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # If no results, try with is_published field
        if not blogs:
            query_alt = {"is_published": True}
            if category:
                query_alt["category"] = category
            blogs = await db.blog_posts.find(
                query_alt,
                {"_id": 0}
            ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Also check legacy blogs collection
        if not blogs:
            query = {"status": "published"}
            if category:
                query["category"] = category
            blogs = await db.blogs.find(
                query,
                {"_id": 0}
            ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total = len(blogs)
        
        return {"blogs": blogs, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blogs/{slug}")
async def get_blog_by_slug(slug: str):
    """Get a single blog post by slug"""
    try:
        # Try blog_posts collection first with status field
        blog = await db.blog_posts.find_one(
            {"slug": slug, "status": "published"},
            {"_id": 0}
        )
        
        # Try with is_published field
        if not blog:
            blog = await db.blog_posts.find_one(
                {"slug": slug, "is_published": True},
                {"_id": 0}
            )
        
        # Try legacy blogs collection
        if not blog:
            blog = await db.blogs.find_one(
                {"slug": slug, "status": "published"},
                {"_id": 0}
            )
        
        if not blog:
            raise HTTPException(status_code=404, detail="Blog post not found")
        return blog
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== TESTIMONIALS ==========

@router.get("/testimonials")
async def get_public_testimonials(category: Optional[str] = None, limit: int = 50):
    """Get all active testimonials for public display"""
    try:
        query = {"status": "active"}
        if category and category != "all":
            query["category"] = category
        
        testimonials = await db.testimonials.find(
            query,
            {"_id": 0}
        ).to_list(limit)
        
        return {"testimonials": testimonials, "total": len(testimonials)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== JOBS (CAREERS) ==========

@router.get("/jobs")
async def get_public_jobs():
    """Get all active job listings for public display"""
    try:
        jobs = await db.jobs.find(
            {"status": "active"},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}")
async def get_job_by_id(job_id: str):
    """Get a single job by ID"""
    try:
        job = await db.jobs.find_one(
            {"id": job_id, "status": "active"},
            {"_id": 0}
        )
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
