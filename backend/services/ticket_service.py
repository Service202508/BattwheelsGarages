"""
Battwheels OS - Ticket Service
Core business logic for ticket lifecycle management

Service responsibilities:
- Ticket CRUD operations
- State machine for ticket lifecycle
- EFI integration (AI matching, failure card linking)
- Event emission for all ticket operations

Event Flow:
┌─────────────┐     ┌───────────────┐     ┌────────────────────┐
│ Create/     │ --> │ TicketService │ --> │ Event Dispatcher   │
│ Update      │     │ (business     │     │ - AI Matching      │
│ Request     │     │  logic)       │     │ - Confidence Eng   │
└─────────────┘     └───────────────┘     │ - Notifications    │
                                          └────────────────────┘
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid
import logging
import hashlib

from events import get_dispatcher, EventType, EventPriority

logger = logging.getLogger(__name__)


# ==================== TICKET STATES ====================

class TicketState:
    """
    Ticket lifecycle states
    
    Two workflows exist:
    1. Basic workflow: OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
    2. Estimate workflow: OPEN → ASSIGNED → ESTIMATE_SHARED → ESTIMATE_APPROVED → 
                         WORK_IN_PROGRESS → WORK_COMPLETED → INVOICED → PENDING_PAYMENT → CLOSED
    """
    # Basic states
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    
    # Extended estimate workflow states
    TECHNICIAN_ASSIGNED = "technician_assigned"  # Same as ASSIGNED, alias
    ESTIMATE_SHARED = "estimate_shared"
    ESTIMATE_APPROVED = "estimate_approved"
    WORK_IN_PROGRESS = "work_in_progress"
    WORK_COMPLETED = "work_completed"
    INVOICED = "invoiced"
    PENDING_PAYMENT = "pending_payment"  # Awaiting customer payment

# Valid state transitions - comprehensive workflow including estimate states
VALID_TRANSITIONS = {
    # Basic workflow
    TicketState.OPEN: [TicketState.ASSIGNED, TicketState.TECHNICIAN_ASSIGNED, TicketState.IN_PROGRESS, TicketState.CLOSED],
    TicketState.ASSIGNED: [TicketState.IN_PROGRESS, TicketState.ESTIMATE_SHARED, TicketState.OPEN, TicketState.CLOSED],
    TicketState.IN_PROGRESS: [TicketState.PENDING_PARTS, TicketState.RESOLVED, TicketState.ASSIGNED, TicketState.WORK_COMPLETED],
    TicketState.PENDING_PARTS: [TicketState.IN_PROGRESS, TicketState.WORK_IN_PROGRESS, TicketState.CLOSED],
    TicketState.RESOLVED: [TicketState.CLOSED, TicketState.REOPENED, TicketState.INVOICED],
    TicketState.CLOSED: [TicketState.REOPENED],
    TicketState.REOPENED: [TicketState.ASSIGNED, TicketState.IN_PROGRESS],
    
    # Extended estimate workflow
    TicketState.TECHNICIAN_ASSIGNED: [TicketState.ESTIMATE_SHARED, TicketState.IN_PROGRESS, TicketState.OPEN],
    TicketState.ESTIMATE_SHARED: [TicketState.ESTIMATE_APPROVED, TicketState.ASSIGNED, TicketState.CLOSED],
    TicketState.ESTIMATE_APPROVED: [TicketState.WORK_IN_PROGRESS, TicketState.ESTIMATE_SHARED, TicketState.CLOSED],
    TicketState.WORK_IN_PROGRESS: [TicketState.WORK_COMPLETED, TicketState.PENDING_PARTS, TicketState.ESTIMATE_APPROVED],
    TicketState.WORK_COMPLETED: [TicketState.INVOICED, TicketState.CLOSED, TicketState.WORK_IN_PROGRESS],
    TicketState.INVOICED: [TicketState.PENDING_PAYMENT, TicketState.CLOSED, TicketState.WORK_COMPLETED],
    TicketState.PENDING_PAYMENT: [TicketState.CLOSED, TicketState.INVOICED],
}


# ==================== DATA MODELS ====================

class TicketCreateData(BaseModel):
    """Input data for ticket creation"""
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
    customer_type: str = "individual"
    contact_number: Optional[str] = None
    customer_email: Optional[str] = None
    issue_type: Optional[str] = None
    resolution_type: str = "workshop"
    incident_location: Optional[str] = None
    attachments_count: int = 0
    estimated_cost: Optional[float] = None
    error_codes_reported: List[str] = []
    organization_id: Optional[str] = None  # Multi-tenant scoping


class TicketUpdateData(BaseModel):
    """Input data for ticket update"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_outcome: Optional[str] = None  # success, failure, partial
    selected_failure_card: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    labor_cost: Optional[float] = None


class TicketCloseData(BaseModel):
    """Input data for closing a ticket"""
    resolution: str
    resolution_outcome: str = "success"  # success, failure, partial
    resolution_notes: Optional[str] = None
    selected_failure_card: Optional[str] = None


# ==================== TICKET SERVICE ====================

class TicketService:
    """
    Core ticket business logic service
    
    All ticket operations flow through this service.
    Service emits events - handlers process them.
    """
    
    def __init__(self, db):
        self.db = db
        self.dispatcher = get_dispatcher()
        logger.info("TicketService initialized")
    
    # ==================== TICKET CREATION ====================
    
    async def create_ticket(
        self, 
        data: TicketCreateData, 
        user_id: str, 
        user_name: str
    ) -> Dict[str, Any]:
        """
        Create a new service ticket
        
        Steps:
        1. Generate ticket ID and initial state
        2. Enrich with customer/vehicle data
        3. Store in database
        4. Emit TICKET_CREATED event (triggers AI matching)
        
        Returns:
            Created ticket document
        """
        ticket_id = f"tkt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        # Build initial status history
        status_history = [{
            "status": TicketState.OPEN,
            "timestamp": now.isoformat(),
            "updated_by": user_name
        }]
        
        # Build ticket document
        ticket_doc = {
            "ticket_id": ticket_id,
            "title": data.title,
            "description": data.description,
            "category": data.category,
            "priority": data.priority,
            "status": TicketState.OPEN,
            
            # Vehicle info
            "vehicle_id": data.vehicle_id,
            "vehicle_type": data.vehicle_type,
            "vehicle_make": data.vehicle_make,
            "vehicle_model": data.vehicle_model,
            "vehicle_number": data.vehicle_number,
            
            # Customer info
            "customer_id": data.customer_id or user_id,
            "customer_name": data.customer_name,
            "customer_type": data.customer_type,
            "contact_number": data.contact_number,
            "customer_email": data.customer_email,
            
            # Issue details
            "issue_type": data.issue_type or data.category,
            "resolution_type": data.resolution_type,
            "incident_location": data.incident_location,
            
            # Attachments
            "attachments": [],
            "attachments_count": data.attachments_count,
            
            # EFI Integration - to be populated by AI matching
            "suggested_failure_cards": [],
            "selected_failure_card": None,
            "ai_match_performed": False,
            "ai_match_timestamp": None,
            "error_codes_reported": data.error_codes_reported,
            
            # Resolution - empty initially
            "resolution": None,
            "resolution_notes": None,
            "resolution_outcome": None,
            
            # Status tracking
            "status_history": status_history,
            
            # Costs
            "estimated_cost": data.estimated_cost or 0.0,
            "actual_cost": 0.0,
            "parts_cost": 0.0,
            "labor_cost": 0.0,
            
            # Assignment
            "assigned_technician_id": None,
            "assigned_technician_name": None,
            
            # Financial flags
            "has_sales_order": False,
            "has_invoice": False,
            "invoice_id": None,
            
            # Timestamps
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "resolved_at": None,
            "closed_at": None,
            
            # Metadata
            "created_by": user_id,
        }
        
        # Add organization_id for multi-tenant scoping
        if data.organization_id:
            ticket_doc["organization_id"] = data.organization_id

        # ── SLA FIELDS: Calculate deadlines based on priority ──
        try:
            from routes.sla import get_sla_config_for_org, calculate_sla_deadlines
            if data.organization_id:
                sla_config = await get_sla_config_for_org(data.organization_id)
            else:
                from routes.sla import DEFAULT_SLA_CONFIG
                sla_config = DEFAULT_SLA_CONFIG
            sla_fields = calculate_sla_deadlines(
                created_at=now.isoformat(),
                priority=data.priority or "medium",
                sla_config=sla_config
            )
            ticket_doc.update(sla_fields)
        except Exception as _sla_err:
            # SLA is non-critical — ticket creation must not fail
            logger.warning(f"SLA deadline calculation failed: {_sla_err}")
        
        # Enrich with vehicle data if vehicle_id provided
        if data.vehicle_id:
            vehicle_query = {"vehicle_id": data.vehicle_id}
            if data.organization_id:
                vehicle_query["organization_id"] = data.organization_id
            vehicle = await self.db.vehicles.find_one(vehicle_query, {"_id": 0})
            if vehicle:
                if not ticket_doc["customer_name"]:
                    ticket_doc["customer_name"] = vehicle.get("owner_name")
                if not ticket_doc["contact_number"]:
                    ticket_doc["contact_number"] = vehicle.get("owner_phone")
                if not ticket_doc["customer_email"]:
                    ticket_doc["customer_email"] = vehicle.get("owner_email")
                if not ticket_doc["vehicle_make"]:
                    ticket_doc["vehicle_make"] = vehicle.get("make")
                if not ticket_doc["vehicle_model"]:
                    ticket_doc["vehicle_model"] = vehicle.get("model")
            
            # Update vehicle status to in_workshop
            await self.db.vehicles.update_one(
                {"vehicle_id": data.vehicle_id},
                {"$set": {"current_status": "in_workshop"}, "$inc": {"total_visits": 1}}
            )
        
        # Store ticket
        await self.db.tickets.insert_one(ticket_doc)
        
        # Get the stored ticket without _id for response
        stored_ticket = await self.db.tickets.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )
        
        # EMIT TICKET_CREATED EVENT (with organization_id for tenant filtering - Phase D)
        # This triggers: AI matching -> suggested_failure_cards population
        await self.dispatcher.emit(
            EventType.TICKET_CREATED,
            {
                "ticket_id": ticket_id,
                "title": data.title,
                "description": data.description,
                "category": data.category,
                "priority": data.priority,
                "vehicle_make": ticket_doc["vehicle_make"],
                "vehicle_model": ticket_doc["vehicle_model"],
                "error_codes_reported": data.error_codes_reported,
                "customer_id": ticket_doc["customer_id"],
            },
            source="ticket_service",
            user_id=user_id,
            priority=EventPriority.HIGH,
            organization_id=data.organization_id  # Phase D: Tenant tagging
        )
        
        logger.info(f"Created ticket {ticket_id}, emitted TICKET_CREATED")
        
        return stored_ticket
    
    # ==================== TICKET UPDATE ====================
    
    async def update_ticket(
        self, 
        ticket_id: str, 
        data: TicketUpdateData, 
        user_id: str, 
        user_name: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a ticket
        
        Steps:
        1. Validate ticket exists (scoped to org if provided)
        2. Validate state transition if status changing
        3. Update fields
        4. Emit appropriate events
        
        Returns:
            Updated ticket document
        """
        # Get existing ticket (with org scope if provided)
        query = {"ticket_id": ticket_id}
        if organization_id:
            query["organization_id"] = organization_id
        
        existing = await self.db.tickets.find_one(query, {"_id": 0})
        if not existing:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        now = datetime.now(timezone.utc)
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        update_dict["updated_at"] = now.isoformat()
        
        old_status = existing.get("status")
        new_status = data.status
        
        # Validate state transition
        if new_status and new_status != old_status:
            valid_next = VALID_TRANSITIONS.get(old_status, [])
            if new_status not in valid_next and new_status != old_status:
                logger.warning(f"Invalid transition {old_status} -> {new_status} allowed anyway")
            
            # Update status history
            history = existing.get("status_history", [])
            history.append({
                "status": new_status,
                "timestamp": now.isoformat(),
                "updated_by": user_name
            })
            update_dict["status_history"] = history
        
        # Get technician name if assigning
        if data.assigned_technician_id:
            tech = await self.db.users.find_one(
                {"user_id": data.assigned_technician_id}, {"_id": 0}
            )
            if tech:
                update_dict["assigned_technician_name"] = tech.get("name")
        
        # Apply update
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id}, {"$set": update_dict}
        )
        
        # AUTO-CREATE ESTIMATE on technician assignment
        if data.assigned_technician_id and existing.get("organization_id"):
            try:
                from services.ticket_estimate_service import get_ticket_estimate_service
                estimate_service = get_ticket_estimate_service()
                await estimate_service.ensure_estimate(
                    ticket_id=ticket_id,
                    organization_id=existing.get("organization_id"),
                    user_id=user_id,
                    user_name=user_name
                )
                logger.info(f"Auto-created estimate for ticket {ticket_id} on technician assignment")
            except Exception as e:
                # Don't fail ticket update if estimate creation fails
                logger.warning(f"Failed to auto-create estimate for ticket {ticket_id}: {e}")
        
        # Get org_id from existing ticket for event tagging
        ticket_org_id = existing.get("organization_id") or organization_id
        
        # EMIT TICKET_UPDATED EVENT (Phase D: with org_id)
        await self.dispatcher.emit(
            EventType.TICKET_UPDATED,
            {
                "ticket_id": ticket_id,
                "changes": list(update_dict.keys()),
                "updated_by": user_id
            },
            source="ticket_service",
            user_id=user_id,
            organization_id=ticket_org_id
        )
        
        # EMIT TICKET_STATUS_CHANGED if status changed (Phase D: with org_id)
        if new_status and new_status != old_status:
            await self.dispatcher.emit(
                EventType.TICKET_STATUS_CHANGED,
                {
                    "ticket_id": ticket_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "updated_by": user_id
                },
                source="ticket_service",
                user_id=user_id,
                priority=EventPriority.NORMAL,
                organization_id=ticket_org_id
            )
            logger.info(f"Ticket {ticket_id} status: {old_status} -> {new_status}")
        
        # Return updated ticket
        return await self.db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    
    # ==================== TICKET CLOSURE ====================
    
    async def close_ticket(
        self, 
        ticket_id: str, 
        data: TicketCloseData, 
        user_id: str, 
        user_name: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close a ticket with resolution details
        
        This is a CRITICAL EFI touchpoint:
        1. Validates resolution outcome is captured
        2. Ensures failure card is linked (or triggers draft creation)
        3. Emits TICKET_CLOSED (triggers confidence engine)
        
        Undocumented issue handling:
        - If no failure card selected AND outcome is success/partial,
          we emit NEW_FAILURE_DETECTED to auto-create draft card
        
        Returns:
            Closed ticket document
        """
        query = {"ticket_id": ticket_id}
        if organization_id:
            query["organization_id"] = organization_id
            
        existing = await self.db.tickets.find_one(query, {"_id": 0})
        if not existing:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        now = datetime.now(timezone.utc)
        old_status = existing.get("status")
        
        # Build update
        update_dict = {
            "status": TicketState.CLOSED,
            "resolution": data.resolution,
            "resolution_outcome": data.resolution_outcome,
            "resolution_notes": data.resolution_notes,
            "resolved_at": now.isoformat(),
            "closed_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        # Link failure card if provided
        if data.selected_failure_card:
            update_dict["selected_failure_card"] = data.selected_failure_card
            
            # Emit FAILURE_CARD_USED
            await self.dispatcher.emit(
                EventType.FAILURE_CARD_USED,
                {
                    "failure_id": data.selected_failure_card,
                    "ticket_id": ticket_id,
                    "selected_by": user_id
                },
                source="ticket_service",
                user_id=user_id
            )
        
        # Update status history
        history = existing.get("status_history", [])
        history.append({
            "status": TicketState.CLOSED,
            "timestamp": now.isoformat(),
            "updated_by": user_name,
            "notes": f"Resolution: {data.resolution_outcome}"
        })
        update_dict["status_history"] = history
        
        # Apply update
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id}, {"$set": update_dict}
        )
        
        # Update vehicle status if applicable
        if existing.get("vehicle_id"):
            await self.db.vehicles.update_one(
                {"vehicle_id": existing["vehicle_id"]},
                {"$set": {"current_status": "serviced"}}
            )
        
        # EMIT TICKET_CLOSED EVENT
        # This triggers: confidence_engine -> update failure card metrics
        await self.dispatcher.emit(
            EventType.TICKET_CLOSED,
            {
                "ticket_id": ticket_id,
                "resolution_outcome": data.resolution_outcome,
                "selected_failure_card": data.selected_failure_card,
                "old_status": old_status
            },
            source="ticket_service",
            user_id=user_id,
            priority=EventPriority.NORMAL
        )
        
        # HANDLE UNDOCUMENTED ISSUE:
        # If no failure card selected but issue was resolved,
        # this is a new failure pattern that needs to be documented
        if not data.selected_failure_card and data.resolution_outcome in ["success", "partial"]:
            suggested_cards = existing.get("suggested_failure_cards", [])
            
            # Check if this is truly undocumented (no good matches)
            if len(suggested_cards) == 0 or not existing.get("ai_match_performed"):
                logger.info(f"Undocumented issue detected for ticket {ticket_id}")
                
                # EMIT NEW_FAILURE_DETECTED
                # This triggers: auto-create draft FailureCard
                await self.dispatcher.emit(
                    EventType.NEW_FAILURE_DETECTED,
                    {
                        "ticket_id": ticket_id,
                        "description": existing.get("title"),
                        "root_cause": data.resolution_notes or "Undocumented",
                        "resolution": data.resolution,
                        "technician_id": user_id,
                        "vehicle_make": existing.get("vehicle_make"),
                        "vehicle_model": existing.get("vehicle_model"),
                        "category": existing.get("category"),
                    },
                    source="ticket_service",
                    user_id=user_id,
                    priority=EventPriority.HIGH
                )
        
        logger.info(f"Closed ticket {ticket_id} with outcome: {data.resolution_outcome}")
        
        return await self.db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    
    # ==================== TICKET ASSIGNMENT ====================
    
    async def assign_ticket(
        self, 
        ticket_id: str, 
        technician_id: str, 
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Assign ticket to a technician
        
        Emits: TICKET_ASSIGNED
        """
        existing = await self.db.tickets.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )
        if not existing:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        tech = await self.db.users.find_one(
            {"user_id": technician_id}, {"_id": 0}
        )
        if not tech:
            raise ValueError(f"Technician {technician_id} not found")
        
        now = datetime.now(timezone.utc)
        
        # Update status history
        history = existing.get("status_history", [])
        history.append({
            "status": TicketState.ASSIGNED,
            "timestamp": now.isoformat(),
            "updated_by": user_name,
            "notes": f"Assigned to {tech.get('name')}"
        })
        
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {
                "assigned_technician_id": technician_id,
                "assigned_technician_name": tech.get("name"),
                "status": TicketState.ASSIGNED,
                "status_history": history,
                "updated_at": now.isoformat()
            }}
        )
        
        # EMIT TICKET_ASSIGNED EVENT
        await self.dispatcher.emit(
            EventType.TICKET_ASSIGNED,
            {
                "ticket_id": ticket_id,
                "technician_id": technician_id,
                "technician_name": tech.get("name"),
                "assigned_by": user_id
            },
            source="ticket_service",
            user_id=user_id
        )
        
        return await self.db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    
    # ==================== WORKFLOW OPERATIONS ====================
    
    async def start_work(
        self,
        ticket_id: str,
        notes: Optional[str],
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Start work on a ticket - transitions to work_in_progress
        
        Usually auto-triggered when estimate is approved.
        Can be manually triggered if needed.
        """
        existing = await self.db.tickets.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )
        if not existing:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        current_status = existing.get("status")
        if current_status == "work_in_progress":
            raise ValueError("Work already in progress")
        
        if current_status == "closed":
            raise ValueError("Cannot start work on closed ticket")
        
        now = datetime.now(timezone.utc)
        
        # Update status history
        history = existing.get("status_history", [])
        history.append({
            "status": "work_in_progress",
            "timestamp": now.isoformat(),
            "updated_by": user_name,
            "notes": notes or "Work started"
        })
        
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {
                "status": "work_in_progress",
                "work_started_at": now.isoformat(),
                "status_history": history,
                "updated_at": now.isoformat()
            }}
        )
        
        # Log activity
        await self._log_activity(
            ticket_id, "work_started",
            notes or "Technician started working on this ticket",
            user_id, user_name
        )
        
        return await self.db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    
    async def complete_work(
        self,
        ticket_id: str,
        work_summary: str,
        parts_used: Optional[List[str]],
        labor_hours: Optional[float],
        notes: Optional[str],
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Mark work as completed on a ticket
        
        Transitions ticket to "work_completed" status.
        Ticket can still be edited until officially closed.
        """
        existing = await self.db.tickets.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )
        if not existing:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        current_status = existing.get("status")
        if current_status == "closed":
            raise ValueError("Ticket is already closed")
        
        if current_status not in ["work_in_progress", "estimate_approved", "technician_assigned"]:
            raise ValueError(f"Cannot complete work from status: {current_status}")
        
        now = datetime.now(timezone.utc)
        
        # Update status history
        history = existing.get("status_history", [])
        history.append({
            "status": "work_completed",
            "timestamp": now.isoformat(),
            "updated_by": user_name,
            "notes": f"Work completed: {work_summary}"
        })
        
        update_data = {
            "status": "work_completed",
            "work_completed_at": now.isoformat(),
            "work_summary": work_summary,
            "status_history": history,
            "updated_at": now.isoformat()
        }
        
        if parts_used:
            update_data["parts_used"] = parts_used
        if labor_hours:
            update_data["labor_hours"] = labor_hours
        if notes:
            update_data["completion_notes"] = notes
        
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": update_data}
        )
        
        # Deduct inventory for parts used
        if parts_used:
            org_id = existing.get("organization_id", "")
            for item_id in parts_used:
                try:
                    item = await self.db.inventory.find_one({"item_id": item_id}, {"_id": 0})
                    if item:
                        old_qty = float(item.get("quantity", 0))
                        new_qty = max(0, old_qty - 1)
                        await self.db.inventory.update_one(
                            {"item_id": item_id},
                            {"$set": {"quantity": new_qty, "updated_at": now.isoformat()}}
                        )
                        # Log stock movement
                        await self.db.stock_movements.insert_one({
                            "movement_id": f"sm_{ticket_id}_{item_id}",
                            "item_id": item_id,
                            "item_name": item.get("name", ""),
                            "movement_type": "TICKET_USAGE",
                            "reference_type": "TICKET",
                            "reference_id": ticket_id,
                            "movement_date": now.strftime("%Y-%m-%d"),
                            "quantity": -1,
                            "balance_qty": new_qty,
                            "organization_id": org_id,
                            "created_by": user_id,
                            "narration": f"Used on ticket {ticket_id}",
                            "created_at": now.isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Inventory deduction failed for {item_id}: {e}")
        
        # Log activity
        activity_desc = f"Work completed: {work_summary}"
        if labor_hours:
            activity_desc += f" | Labor: {labor_hours} hours"
        if parts_used:
            activity_desc += f" | Parts: {len(parts_used)} items used"
        
        await self._log_activity(
            ticket_id, "work_completed",
            activity_desc,
            user_id, user_name
        )
        
        return await self.db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    
    async def add_activity(
        self,
        ticket_id: str,
        action: str,
        description: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Add a manual activity log entry"""
        # Verify ticket exists
        existing = await self.db.tickets.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )
        if not existing:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        return await self._log_activity(
            ticket_id, action, description, user_id, user_name
        )
    
    async def update_activity(
        self,
        ticket_id: str,
        activity_id: str,
        description: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Update an activity log entry (admin only)"""
        # Verify activity exists
        existing = await self.db.ticket_activities.find_one({
            "activity_id": activity_id,
            "ticket_id": ticket_id
        }, {"_id": 0})
        
        if not existing:
            raise ValueError(f"Activity {activity_id} not found")
        
        now = datetime.now(timezone.utc)
        
        await self.db.ticket_activities.update_one(
            {"activity_id": activity_id},
            {"$set": {
                "description": description,
                "edited_at": now.isoformat(),
                "edited_by": user_name
            }}
        )
        
        return await self.db.ticket_activities.find_one(
            {"activity_id": activity_id}, {"_id": 0}
        )
    
    async def _log_activity(
        self,
        ticket_id: str,
        action: str,
        description: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Log activity to ticket activity log"""
        now = datetime.now(timezone.utc)
        activity = {
            "activity_id": f"act_{uuid.uuid4().hex[:12]}",
            "ticket_id": ticket_id,
            "action": action,
            "description": description,
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": now.isoformat(),
            "editable": True
        }
        await self.db.ticket_activities.insert_one(activity)
        
        # Return without _id
        return {k: v for k, v in activity.items() if k != "_id"}
    
    # ==================== TICKET QUERIES ====================
    
    async def get_ticket(self, ticket_id: str, organization_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a single ticket by ID, optionally scoped to organization"""
        query = {"ticket_id": ticket_id}
        if organization_id:
            query["organization_id"] = organization_id
        return await self.db.tickets.find_one(query, {"_id": 0})
    
    async def list_tickets(
        self,
        user_id: str,
        user_role: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List tickets with filtering and role-based access
        """
        query = {}
        
        # Multi-tenant scoping
        if organization_id:
            query["organization_id"] = organization_id
        
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if category:
            query["category"] = category
        
        # Role-based filtering
        if user_role == "customer":
            query["customer_id"] = user_id
        elif user_role == "technician":
            query["$or"] = [
                {"assigned_technician_id": user_id},
                {"assigned_technician_id": None}
            ]
        # Admins see all tickets
        
        tickets = await self.db.tickets.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await self.db.tickets.count_documents(query)
        
        return {
            "tickets": tickets,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    
    # ==================== EFI INTEGRATION ====================
    
    async def get_ticket_matches(self, ticket_id: str) -> Dict[str, Any]:
        """
        Get AI-suggested failure cards for a ticket
        
        Called after AI matching has populated suggested_failure_cards
        """
        ticket = await self.db.tickets.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        suggested_ids = ticket.get("suggested_failure_cards", [])
        
        if not suggested_ids:
            return {
                "ticket_id": ticket_id,
                "ai_match_performed": ticket.get("ai_match_performed", False),
                "matches": []
            }
        
        # Get failure card details
        cards = await self.db.failure_cards.find(
            {"failure_id": {"$in": suggested_ids}},
            {
                "_id": 0, 
                "failure_id": 1, 
                "title": 1, 
                "subsystem_category": 1,
                "root_cause": 1, 
                "confidence_score": 1, 
                "effectiveness_score": 1,
                "resolution_summary": 1
            }
        ).to_list(len(suggested_ids))
        
        return {
            "ticket_id": ticket_id,
            "ai_match_performed": ticket.get("ai_match_performed", False),
            "ai_match_timestamp": ticket.get("ai_match_timestamp"),
            "matches": cards
        }
    
    async def select_failure_card(
        self, 
        ticket_id: str, 
        failure_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Select a failure card for the ticket
        
        This links a ticket to a known failure pattern for diagnosis/resolution
        """
        ticket = await self.db.tickets.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        card = await self.db.failure_cards.find_one(
            {"failure_id": failure_id}, {"_id": 0}
        )
        if not card:
            raise ValueError(f"Failure card {failure_id} not found")
        
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {
                "selected_failure_card": failure_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # EMIT FAILURE_CARD_USED
        await self.dispatcher.emit(
            EventType.FAILURE_CARD_USED,
            {
                "failure_id": failure_id,
                "ticket_id": ticket_id,
                "selected_by": user_id
            },
            source="ticket_service",
            user_id=user_id
        )
        
        return {
            "message": "Failure card selected",
            "ticket_id": ticket_id,
            "failure_id": failure_id,
            "failure_title": card.get("title")
        }
    
    # ==================== STATISTICS ====================
    
    async def get_ticket_stats(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Get ticket statistics for dashboard, scoped to organization"""
        match_stage = {}
        if organization_id:
            match_stage = {"$match": {"organization_id": organization_id}}
        
        pipeline = []
        if match_stage:
            pipeline.append(match_stage)
        pipeline.append({
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        })
        
        status_counts = {}
        async for doc in self.db.tickets.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]
        
        total = sum(status_counts.values())
        open_count = status_counts.get(TicketState.OPEN, 0) + status_counts.get(TicketState.ASSIGNED, 0)
        in_progress = status_counts.get(TicketState.IN_PROGRESS, 0)
        resolved = status_counts.get(TicketState.RESOLVED, 0) + status_counts.get(TicketState.CLOSED, 0)
        
        return {
            "total": total,
            "open": open_count,
            "in_progress": in_progress,
            "resolved": resolved,
            "by_status": status_counts
        }


# ==================== SERVICE FACTORY ====================

_ticket_service: Optional[TicketService] = None


def get_ticket_service(db=None) -> TicketService:
    """Get the ticket service singleton"""
    global _ticket_service
    if _ticket_service is None:
        if db is None:
            raise ValueError("Database required to initialize TicketService")
        _ticket_service = TicketService(db)
    return _ticket_service


def init_ticket_service(db) -> TicketService:
    """Initialize the ticket service with database"""
    global _ticket_service
    _ticket_service = TicketService(db)
    return _ticket_service
