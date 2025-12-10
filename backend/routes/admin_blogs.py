from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import BlogPost, BlogPostCreate, BlogPostUpdate
from middleware import get_current_user
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/api/admin/blogs", tags=["admin-blogs"])
security = HTTPBearer()

from server import db


@router.get("/")
async def get_all_blogs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    category: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    skip: int = Query(0)
):
    """
    Get all blog posts
    """
    try:
        await get_current_user(credentials)
        
        query = {}
        if category:
            query["category"] = category
        if is_published is not None:
            query["is_published"] = is_published
        
        total = await db.blog_posts.count_documents(query)
        blogs = await db.blog_posts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "total": total,
            "blogs": blogs,
            "limit": limit,
            "skip": skip
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")


@router.post("/")
async def create_blog(
    blog_data: BlogPostCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create new blog post
    """
    try:
        await get_current_user(credentials)
        
        # Check if slug already exists
        existing = await db.blog_posts.find_one({"slug": blog_data.slug}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Blog with this slug already exists")
        
        blog = BlogPost(**blog_data.dict())
        
        # Set published_at if is_published is True
        if blog.is_published and not blog.published_at:
            blog.published_at = datetime.now(timezone.utc)
        
        await db.blog_posts.insert_one(blog.dict())
        
        return {"message": "Blog created successfully", "blog": blog.dict()}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating blog: {str(e)}")


@router.get("/{blog_id}")
async def get_blog(
    blog_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get blog by ID
    """
    try:
        await get_current_user(credentials)
        
        blog = await db.blog_posts.find_one({"id": blog_id}, {"_id": 0})
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        return blog
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching blog: {str(e)}")


@router.put("/{blog_id}")
async def update_blog(
    blog_id: str,
    blog_data: BlogPostUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update blog post
    """
    try:
        await get_current_user(credentials)
        
        # Check if blog exists
        existing = await db.blog_posts.find_one({"id": blog_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in blog_data.dict(exclude_unset=True).items()}
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Set published_at if changing to published
        if update_data.get("is_published") and not existing.get("published_at"):
            update_data["published_at"] = datetime.now(timezone.utc)
        
        await db.blog_posts.update_one(
            {"id": blog_id},
            {"$set": update_data}
        )
        
        updated_blog = await db.blog_posts.find_one({"id": blog_id}, {"_id": 0})
        
        return {"message": "Blog updated successfully", "blog": updated_blog}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating blog: {str(e)}")


@router.delete("/{blog_id}")
async def delete_blog(
    blog_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete blog post
    """
    try:
        await get_current_user(credentials)
        
        result = await db.blog_posts.delete_one({"id": blog_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        return {"message": "Blog deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting blog: {str(e)}")
