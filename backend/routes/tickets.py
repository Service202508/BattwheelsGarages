"""
Battwheels OS - Ticket Routes (Modular)
Thin controller layer - business logic delegated to services via events

Routes emit events, services process them.
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid
import logging

from events import get_dispatcher, EventType, EventPriority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Database reference
db = None


def init_router(database):
    """Initialize router with database"""
    global db
    db = database
    return router


# ==================== MODELS ====================

class TicketCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = "medium"
    vehicle_id: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_number: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_type: Optional[str] = "individual"
    contact_number: Optional[str] = None
    customer_email: Optional[str] = None
    issue_type: Optional[str] = None
    resolution_type: Optional[str] = "workshop"
    incident_location: Optional[str] = None
    attachments_count: int = 0
    estimated_cost: Optional[float] = None
    error_codes_reported: List[str] = []


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    labor_cost: Optional[float] = None


class Ticket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: f"tkt_{uuid.uuid4().hex[:12]}")
    title: str
    description: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    category: Optional[str] = None
    
    # Vehicle
    vehicle_id: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_number: Optional[str] = None
    
    # Customer
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_type: str = "individual"
    contact_number: Optional[str] = None
    customer_email: Optional[str] = None
    
    # Assignment
    assigned_technician_id: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    
    # EFI Integration
    suggested_failure_cards: List[str] = []
    selected_failure_card: Optional[str] = None
    ai_match_performed: bool = False
    ai_match_timestamp: Optional[str] = None
    error_codes_reported: List[str] = []
    
    # Resolution
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_type: str = "workshop"
    
    # Status tracking
    status_history: List[dict] = []
    
    # Costs
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

async def get_current_user(request: Request):
    """Get current authenticated user"""
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


# ==================== ROUTES ====================

@router.post("")
async def create_ticket(data: TicketCreate, request: Request):
    """
    Create a new service ticket
    
    Emits: TICKET_CREATED -> triggers AI matching
    """
    user = await get_current_user(request)
    
    # Build ticket
    ticket = Ticket(
        title=data.title,
        description=data.description,
        category=data.category,
        priority=data.priority,
        vehicle_id=data.vehicle_id,
        vehicle_type=data.vehicle_type,
        vehicle_make=data.vehicle_make,
        vehicle_model=data.vehicle_model,
        vehicle_number=data.vehicle_number,
        customer_id=data.customer_id or user.get("user_id"),
        customer_name=data.customer_name,
        customer_type=data.customer_type,
        contact_number=data.contact_number,
        customer_email=data.customer_email,
        resolution_type=data.resolution_type,
        error_codes_reported=data.error_codes_reported,
        estimated_cost=data.estimated_cost,
        status_history=[{
            "status": "open",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("name", "System")
        }]
    )
    
    # Store ticket
    doc = ticket.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.tickets.insert_one(doc)
    
    # Update vehicle status if applicable
    if data.vehicle_id:
        await db.vehicles.update_one(
            {"vehicle_id": data.vehicle_id},
            {"$set": {"current_status": "in_workshop"}, "$inc": {"total_visits": 1}}
        )
    
    # EMIT EVENT - This triggers AI matching via event handlers
    dispatcher = get_dispatcher()
    await dispatcher.emit(
        EventType.TICKET_CREATED,
        {
            "ticket_id": ticket.ticket_id,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "vehicle_make": ticket.vehicle_make,
            "vehicle_model": ticket.vehicle_model,
            "error_codes_reported": ticket.error_codes_reported
        },
        source="tickets_routes",
        user_id=user.get("user_id"),
        priority=EventPriority.HIGH
    )
    
    logger.info(f"Created ticket {ticket.ticket_id}, emitted TICKET_CREATED event")
    
    return ticket.model_dump()


@router.get("")
async def list_tickets(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    skip: int = 0
):
    """List tickets with filtering"""
    user = await get_current_user(request)
    
    query = {}
    
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if category:
        query["category"] = category
    
    # Role-based filtering
    if user.get("role") == "customer":
        query["customer_id"] = user.get("user_id")
    elif user.get("role") == "technician":
        query["$or"] = [
            {"assigned_technician_id": user.get("user_id")},
            {"assigned_technician_id": None}
        ]
    
    tickets = await db.tickets.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.tickets.count_documents(query)
    
    return {
        "tickets": tickets,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, request: Request):
    """Get a single ticket"""
    await get_current_user(request)
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@router.put("/{ticket_id}")
async def update_ticket(ticket_id: str, data: TicketUpdate, request: Request):
    """
    Update a ticket
    
    Emits: TICKET_UPDATED, TICKET_STATUS_CHANGED (if status changed)
    """
    user = await get_current_user(request)
    
    # Get existing ticket
    existing = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Build update
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    old_status = existing.get("status")
    new_status = data.status
    
    # Get technician name if assigning
    if data.assigned_technician_id:
        tech = await db.users.find_one({"user_id": data.assigned_technician_id}, {"_id": 0})
        if tech:
            update_dict["assigned_technician_name"] = tech.get("name")
    
    # Update status history if status changed
    if new_status and new_status != old_status:
        history = existing.get("status_history", [])
        history.append({
            "status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("name", "System")
        })
        update_dict["status_history"] = history
        
        # Set resolved_at if resolving
        if new_status in ["resolved", "closed"]:
            update_dict["resolved_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update vehicle status
            if existing.get("vehicle_id"):
                await db.vehicles.update_one(
                    {"vehicle_id": existing["vehicle_id"]},
                    {"$set": {"current_status": "serviced"}}
                )
    
    # Apply update
    await db.tickets.update_one({"ticket_id": ticket_id}, {"$set": update_dict})
    
    # EMIT EVENTS
    dispatcher = get_dispatcher()
    
    # General update event
    await dispatcher.emit(
        EventType.TICKET_UPDATED,
        {
            "ticket_id": ticket_id,
            "changes": list(update_dict.keys()),
            "updated_by": user.get("user_id")
        },
        source="tickets_routes",
        user_id=user.get("user_id")
    )
    
    # Status change event (triggers confidence updates, notifications)
    if new_status and new_status != old_status:
        await dispatcher.emit(
            EventType.TICKET_STATUS_CHANGED,
            {
                "ticket_id": ticket_id,
                "old_status": old_status,
                "new_status": new_status,
                "updated_by": user.get("user_id")
            },
            source="tickets_routes",
            user_id=user.get("user_id"),
            priority=EventPriority.NORMAL
        )
        logger.info(f"Ticket {ticket_id} status changed: {old_status} -> {new_status}")
    
    # Return updated ticket
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    return ticket


@router.post("/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, technician_id: str, request: Request):
    """
    Assign ticket to a technician
    
    Emits: TICKET_ASSIGNED
    """
    user = await get_current_user(request)
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    tech = await db.users.find_one({"user_id": technician_id}, {"_id": 0})
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
    
    await db.tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "assigned_technician_id": technician_id,
            "assigned_technician_name": tech.get("name"),
            "status": "assigned",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Emit event
    dispatcher = get_dispatcher()
    await dispatcher.emit(
        EventType.TICKET_ASSIGNED,
        {
            "ticket_id": ticket_id,
            "technician_id": technician_id,
            "technician_name": tech.get("name"),
            "assigned_by": user.get("user_id")
        },
        source="tickets_routes",
        user_id=user.get("user_id")
    )
    
    updated = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    return updated


@router.get("/{ticket_id}/matches")
async def get_ticket_matches(ticket_id: str, request: Request):
    """Get AI-suggested failure cards for a ticket"""
    await get_current_user(request)
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    suggested_ids = ticket.get("suggested_failure_cards", [])
    
    if not suggested_ids:
        return {
            "ticket_id": ticket_id,
            "ai_match_performed": ticket.get("ai_match_performed", False),
            "matches": []
        }
    
    # Get failure cards
    cards = await db.failure_cards.find(
        {"failure_id": {"$in": suggested_ids}},
        {"_id": 0, "failure_id": 1, "title": 1, "subsystem_category": 1,
         "root_cause": 1, "confidence_score": 1, "effectiveness_score": 1}
    ).to_list(len(suggested_ids))
    
    return {
        "ticket_id": ticket_id,
        "ai_match_performed": ticket.get("ai_match_performed", False),
        "ai_match_timestamp": ticket.get("ai_match_timestamp"),
        "matches": cards
    }


@router.post("/{ticket_id}/select-card")
async def select_failure_card(ticket_id: str, failure_id: str, request: Request):
    """
    Select a failure card for the ticket
    
    Emits: FAILURE_CARD_USED
    """
    user = await get_current_user(request)
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    card = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    await db.tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "selected_failure_card": failure_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Emit event - tracks card usage
    dispatcher = get_dispatcher()
    await dispatcher.emit(
        EventType.FAILURE_CARD_USED,
        {
            "failure_id": failure_id,
            "ticket_id": ticket_id,
            "selected_by": user.get("user_id")
        },
        source="tickets_routes",
        user_id=user.get("user_id")
    )
    
    return {"message": "Failure card selected", "ticket_id": ticket_id, "failure_id": failure_id}
