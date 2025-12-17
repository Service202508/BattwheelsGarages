from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import ServiceBooking, BookingNote
from middleware import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/admin/bookings", tags=["admin-bookings"])
security = HTTPBearer()

from server import db


@router.get("")
async def get_all_bookings(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    vehicle_category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    skip: int = Query(0)
):
    """
    Get all bookings with filters
    """
    try:
        await get_current_user(credentials)
        
        query = {}
        if status:
            query["status"] = status
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        if vehicle_category:
            query["vehicle_category"] = vehicle_category
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}}
            ]
        
        total = await db.service_bookings.count_documents(query)
        bookings = await db.service_bookings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "total": total,
            "bookings": bookings,
            "limit": limit,
            "skip": skip
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bookings: {str(e)}")


@router.get("/{booking_id}")
async def get_booking_detail(
    booking_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get booking detail with notes
    """
    try:
        await get_current_user(credentials)
        
        booking = await db.service_bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Get notes for this booking
        notes = await db.booking_notes.find({"booking_id": booking_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        return {
            "booking": booking,
            "notes": notes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching booking: {str(e)}")


@router.patch("/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update booking status
    """
    try:
        user = await get_current_user(credentials)
        
        result = await db.service_bookings.update_one(
            {"id": booking_id},
            {"$set": {"status": status}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {"message": "Status updated successfully", "status": status}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@router.post("/{booking_id}/notes")
async def add_booking_note(
    booking_id: str,
    note_text: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Add internal note to booking
    """
    try:
        user = await get_current_user(credentials)
        
        # Verify booking exists
        booking = await db.service_bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        note = BookingNote(
            booking_id=booking_id,
            admin_email=user['email'],
            note=note_text
        )
        
        await db.booking_notes.insert_one(note.dict())
        
        return {"message": "Note added successfully", "note": note.dict()}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding note: {str(e)}")
