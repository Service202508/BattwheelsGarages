from fastapi import APIRouter, HTTPException
from models import ContactMessage, ContactMessageCreate
from typing import List

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

from server import db

@router.post("/", response_model=ContactMessage)
async def create_contact_message(message: ContactMessageCreate):
    """
    Create a new contact message
    """
    try:
        message_obj = ContactMessage(**message.dict())
        result = await db.contact_messages.insert_one(message_obj.dict())
        
        # TODO: Send email notification
        # send_contact_message_email(message_obj)
        
        return message_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

@router.get("/", response_model=List[ContactMessage])
async def get_all_messages(status: str = None, limit: int = 100):
    """
    Get all contact messages (for admin)
    """
    try:
        query = {}
        if status:
            query["status"] = status
        
        messages = await db.contact_messages.find(query).sort("created_at", -1).limit(limit).to_list(limit)
        return [ContactMessage(**message) for message in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@router.patch("/{message_id}/status")
async def update_message_status(message_id: str, status: str):
    """
    Update message status
    """
    try:
        valid_statuses = ["new", "responded"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        result = await db.contact_messages.update_one(
            {"id": message_id},
            {"$set": {"status": status}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return {"message": "Status updated successfully", "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")
