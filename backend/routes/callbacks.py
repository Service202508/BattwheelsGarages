"""
Callback Request Routes - Lead capture for high-value EV purchases
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

router = APIRouter(prefix="/api/callbacks", tags=["callbacks"])

# Database reference
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'battwheels')]

class CallbackRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    preferred_time: str = Field(..., description="Preferred callback time slot")
    vehicle_id: Optional[str] = None
    vehicle_name: Optional[str] = None
    vehicle_slug: Optional[str] = None
    message: Optional[str] = Field(None, max_length=500)

class CallbackResponse(BaseModel):
    success: bool
    message: str
    request_id: Optional[str] = None

@router.post("", response_model=CallbackResponse)
async def create_callback_request(request: CallbackRequest):
    """Create a new callback request for vehicle inquiry"""
    try:
        callback_doc = {
            "name": request.name,
            "phone": request.phone,
            "preferred_time": request.preferred_time,
            "vehicle_id": request.vehicle_id,
            "vehicle_name": request.vehicle_name,
            "vehicle_slug": request.vehicle_slug,
            "message": request.message,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await db.callback_requests.insert_one(callback_doc)
        
        return CallbackResponse(
            success=True,
            message="Callback request submitted successfully. Our team will contact you soon.",
            request_id=str(result.inserted_id)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit callback request: {str(e)}")

@router.get("/count")
async def get_callback_count():
    """Get count of pending callback requests (for admin dashboard)"""
    try:
        total = await db.callback_requests.count_documents({})
        pending = await db.callback_requests.count_documents({"status": "pending"})
        return {"total": total, "pending": pending}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
