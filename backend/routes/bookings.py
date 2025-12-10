from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from models import ServiceBooking, ServiceBookingCreate
from typing import List
import os

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

# MongoDB connection (will be injected)
from server import db

@router.post("/", response_model=ServiceBooking)
async def create_booking(booking: ServiceBookingCreate):
    """
    Create a new service booking
    """
    try:
        booking_obj = ServiceBooking(**booking.dict())
        result = await db.service_bookings.insert_one(booking_obj.dict())
        
        # TODO: Send email notification
        # send_booking_confirmation_email(booking_obj)
        
        return booking_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating booking: {str(e)}")

@router.get("/", response_model=List[ServiceBooking])
async def get_all_bookings(status: str = None, limit: int = 100):
    """
    Get all service bookings (for admin)
    """
    try:
        query = {}
        if status:
            query["status"] = status
        
        bookings = await db.service_bookings.find(query).sort("created_at", -1).limit(limit).to_list(limit)
        return [ServiceBooking(**booking) for booking in bookings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bookings: {str(e)}")

@router.get("/{booking_id}", response_model=ServiceBooking)
async def get_booking(booking_id: str):
    """
    Get a specific booking by ID
    """
    try:
        booking = await db.service_bookings.find_one({"id": booking_id})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return ServiceBooking(**booking)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching booking: {str(e)}")

@router.patch("/{booking_id}/status")
async def update_booking_status(booking_id: str, status: str):
    """
    Update booking status
    """
    try:
        valid_statuses = ["new", "confirmed", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        result = await db.service_bookings.update_one(
            {"id": booking_id},
            {"$set": {"status": status}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {"message": "Status updated successfully", "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")
