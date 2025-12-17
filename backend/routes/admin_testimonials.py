from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import Testimonial, TestimonialCreate, TestimonialUpdate
from middleware import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/admin/testimonials", tags=["admin-testimonials"])
security = HTTPBearer()

from server import db


@router.get("")
async def get_all_testimonials(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    featured: Optional[bool] = Query(None),
    limit: int = Query(100, le=500)
):
    """
    Get all testimonials
    """
    try:
        await get_current_user(credentials)
        
        query = {}
        if featured is not None:
            query["featured"] = featured
        
        testimonials = await db.testimonials.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {"testimonials": testimonials}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching testimonials: {str(e)}")


@router.post("")
async def create_testimonial(
    testimonial_data: TestimonialCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create new testimonial
    """
    try:
        await get_current_user(credentials)
        
        testimonial = Testimonial(**testimonial_data.dict())
        await db.testimonials.insert_one(testimonial.dict())
        
        return {"message": "Testimonial created successfully", "testimonial": testimonial.dict()}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating testimonial: {str(e)}")


@router.get("/{testimonial_id}")
async def get_testimonial(
    testimonial_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get testimonial by ID
    """
    try:
        await get_current_user(credentials)
        
        testimonial = await db.testimonials.find_one({"id": testimonial_id}, {"_id": 0})
        if not testimonial:
            raise HTTPException(status_code=404, detail="Testimonial not found")
        
        return testimonial
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching testimonial: {str(e)}")


@router.put("/{testimonial_id}")
async def update_testimonial(
    testimonial_id: str,
    testimonial_data: TestimonialUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update testimonial
    """
    try:
        await get_current_user(credentials)
        
        # Check if testimonial exists
        existing = await db.testimonials.find_one({"id": testimonial_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Testimonial not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in testimonial_data.dict(exclude_unset=True).items()}
        
        await db.testimonials.update_one(
            {"id": testimonial_id},
            {"$set": update_data}
        )
        
        updated_testimonial = await db.testimonials.find_one({"id": testimonial_id}, {"_id": 0})
        
        return {"message": "Testimonial updated successfully", "testimonial": updated_testimonial}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating testimonial: {str(e)}")


@router.delete("/{testimonial_id}")
async def delete_testimonial(
    testimonial_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete testimonial
    """
    try:
        await get_current_user(credentials)
        
        result = await db.testimonials.delete_one({"id": testimonial_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Testimonial not found")
        
        return {"message": "Testimonial deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting testimonial: {str(e)}")
