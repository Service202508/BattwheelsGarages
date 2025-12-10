from fastapi import APIRouter, HTTPException
from models import FleetEnquiry, FleetEnquiryCreate
from typing import List

router = APIRouter(prefix="/api/fleet-enquiries", tags=["fleet"])

from server import db

@router.post("/", response_model=FleetEnquiry)
async def create_fleet_enquiry(enquiry: FleetEnquiryCreate):
    """
    Create a new fleet/OEM enquiry
    """
    try:
        enquiry_obj = FleetEnquiry(**enquiry.dict())
        result = await db.fleet_enquiries.insert_one(enquiry_obj.dict())
        
        # TODO: Send email notification
        # send_fleet_enquiry_email(enquiry_obj)
        
        return enquiry_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating enquiry: {str(e)}")

@router.get("/", response_model=List[FleetEnquiry])
async def get_all_enquiries(status: str = None, limit: int = 100):
    """
    Get all fleet enquiries (for admin)
    """
    try:
        query = {}
        if status:
            query["status"] = status
        
        enquiries = await db.fleet_enquiries.find(query).sort("created_at", -1).limit(limit).to_list(limit)
        return [FleetEnquiry(**enquiry) for enquiry in enquiries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching enquiries: {str(e)}")

@router.get("/{enquiry_id}", response_model=FleetEnquiry)
async def get_enquiry(enquiry_id: str):
    """
    Get a specific enquiry by ID
    """
    try:
        enquiry = await db.fleet_enquiries.find_one({"id": enquiry_id})
        if not enquiry:
            raise HTTPException(status_code=404, detail="Enquiry not found")
        return FleetEnquiry(**enquiry)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching enquiry: {str(e)}")

@router.patch("/{enquiry_id}/status")
async def update_enquiry_status(enquiry_id: str, status: str):
    """
    Update enquiry status
    """
    try:
        valid_statuses = ["new", "in_discussion", "closed"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        result = await db.fleet_enquiries.update_one(
            {"id": enquiry_id},
            {"$set": {"status": status}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Enquiry not found")
        
        return {"message": "Status updated successfully", "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")
