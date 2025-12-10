from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from middleware import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/admin/contacts", tags=["admin-contacts"])
security = HTTPBearer()

from server import db


@router.get("/")
async def get_all_contacts(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    skip: int = Query(0)
):
    """
    Get all contact messages
    """
    try:
        await get_current_user(credentials)
        
        query = {}
        if status:
            query["status"] = status
        
        total = await db.contact_messages.count_documents(query)
        contacts = await db.contact_messages.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "total": total,
            "contacts": contacts,
            "limit": limit,
            "skip": skip
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contacts: {str(e)}")


@router.patch("/{contact_id}/status")
async def update_contact_status(
    contact_id: str,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update contact message status
    """
    try:
        await get_current_user(credentials)
        
        result = await db.contact_messages.update_one(
            {"id": contact_id},
            {"$set": {"status": status}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return {"message": "Status updated successfully", "status": status}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@router.get("/enquiries")
async def get_fleet_enquiries(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    skip: int = Query(0)
):
    """
    Get all fleet enquiries
    """
    try:
        await get_current_user(credentials)
        
        query = {}
        if status:
            query["status"] = status
        
        total = await db.fleet_enquiries.count_documents(query)
        enquiries = await db.fleet_enquiries.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "total": total,
            "enquiries": enquiries,
            "limit": limit,
            "skip": skip
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching enquiries: {str(e)}")


@router.patch("/enquiries/{enquiry_id}/status")
async def update_enquiry_status(
    enquiry_id: str,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update fleet enquiry status
    """
    try:
        await get_current_user(credentials)
        
        result = await db.fleet_enquiries.update_one(
            {"id": enquiry_id},
            {"$set": {"status": status}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Enquiry not found")
        
        return {"message": "Status updated successfully", "status": status}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")
