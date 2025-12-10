from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import Service, ServiceCreate, ServiceUpdate
from middleware import get_current_user
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/api/admin/services", tags=["admin-services"])
security = HTTPBearer()

from server import db


@router.get("/")
async def get_all_services(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, le=500)
):
    """
    Get all services
    """
    try:
        await get_current_user(credentials)
        
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        
        services = await db.services.find(query, {"_id": 0}).sort("display_order", 1).limit(limit).to_list(limit)
        
        return {"services": services}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching services: {str(e)}")


@router.post("/")
async def create_service(
    service_data: ServiceCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create new service
    """
    try:
        await get_current_user(credentials)
        
        # Check if slug already exists
        existing = await db.services.find_one({"slug": service_data.slug}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Service with this slug already exists")
        
        service = Service(**service_data.dict())
        await db.services.insert_one(service.dict())
        
        return {"message": "Service created successfully", "service": service.dict()}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating service: {str(e)}")


@router.get("/{service_id}")
async def get_service(
    service_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get service by ID
    """
    try:
        await get_current_user(credentials)
        
        service = await db.services.find_one({"id": service_id}, {"_id": 0})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return service
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching service: {str(e)}")


@router.put("/{service_id}")
async def update_service(
    service_id: str,
    service_data: ServiceUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update service
    """
    try:
        await get_current_user(credentials)
        
        # Check if service exists
        existing = await db.services.find_one({"id": service_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in service_data.dict(exclude_unset=True).items()}
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.services.update_one(
            {"id": service_id},
            {"$set": update_data}
        )
        
        updated_service = await db.services.find_one({"id": service_id}, {"_id": 0})
        
        return {"message": "Service updated successfully", "service": updated_service}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating service: {str(e)}")


@router.delete("/{service_id}")
async def delete_service(
    service_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete service
    """
    try:
        await get_current_user(credentials)
        
        result = await db.services.delete_one({"id": service_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return {"message": "Service deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting service: {str(e)}")
