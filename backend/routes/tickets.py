"""
Battwheels OS - Ticket Routes (Modular)
Thin controller layer - all business logic delegated to TicketService

Routes are thin:
- Parse request
- Call service
- Return response

All events are emitted from the service layer, not routes.

Multi-Tenant: Uses TenantContext for strict org_id enforcement.
"""
# TENANT GUARD: Every MongoDB query in this file MUST include {"organization_id": org_id} — no exceptions.
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import logging

from services.ticket_service import (
    TicketService, 
    TicketCreateData, 
    TicketUpdateData,
    TicketCloseData,
    get_ticket_service,
    init_ticket_service
)
from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Service instance
_service: Optional[TicketService] = None


def init_router(database):
    """Initialize router with database"""
    global _service
    _service = init_ticket_service(database)
    logger.info("Tickets router initialized with service")
    return router


def get_service() -> TicketService:
    """Get the ticket service instance"""
    if _service is None:
        raise HTTPException(status_code=500, detail="Ticket service not initialized")
    return _service


# ==================== REQUEST/RESPONSE MODELS ====================

class TicketCreateRequest(BaseModel):
    """API request model for ticket creation"""
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
    incident_location: Optional[str] = None
    attachments_count: int = 0
    estimated_cost: Optional[float] = None
    error_codes_reported: List[str] = []


class TicketUpdateRequest(BaseModel):
    """API request model for ticket update"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_outcome: Optional[str] = None
    selected_failure_card: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    labor_cost: Optional[float] = None


class TicketCloseRequest(BaseModel):
    """API request model for closing a ticket"""
    resolution: str
    resolution_outcome: str = "success"
    resolution_notes: Optional[str] = None
    selected_failure_card: Optional[str] = None
    confirmed_fault: Optional[str] = None  # Technician-confirmed actual fault for EFI feedback


class AssignTicketRequest(BaseModel):
    """API request model for assigning a ticket"""
    technician_id: str


class SelectCardRequest(BaseModel):
    """API request model for selecting a failure card"""
    failure_id: str


# ==================== HELPER FUNCTIONS ====================

async def get_current_user(request: Request, db) -> dict:
    """Get current authenticated user"""
    # Try session token from cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user
    
    # Try Bearer token from header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        from utils.auth import decode_token_safe
        payload = decode_token_safe(token)
        if payload and payload.get("user_id"):
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
    
    raise HTTPException(status_code=401, detail="Not authenticated")


async def require_technician_or_admin(user: dict):
    """Require technician, admin, or owner role"""
    if user.get("role") not in ["admin", "technician", "manager", "owner"]:
        raise HTTPException(status_code=403, detail="Technician or admin access required")


# ==================== ROUTES ====================

@router.post("")
async def create_ticket(request: Request, data: TicketCreateRequest, ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Create a new service ticket
    
    - Creates ticket with initial "open" status
    - Triggers AI matching to suggest failure cards
    - Returns created ticket
    - Requires tenant context (X-Organization-ID header or user membership)
    - ticket_type is auto-set: "onsite" if customer_id is linked, "workshop" otherwise
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    
    # Auto-detect ticket_type based on creation context
    user_role = user.get("role", "")
    has_customer = bool(data.customer_id or data.customer_name or data.contact_number or data.customer_email)
    
    if user_role in ("customer", "fleet_customer"):
        ticket_type = "onsite"
    elif has_customer:
        ticket_type = "onsite"  # Created on behalf of customer
    else:
        ticket_type = "workshop"  # Internal workshop job
    
    # Use tenant context for org_id (strict enforcement)
    create_data = TicketCreateData(
        **data.model_dump(),
        organization_id=ctx.org_id,
        ticket_type=ticket_type
    )
    
    ticket = await service.create_ticket(
        data=create_data,
        user_id=user.get("user_id"),
        user_name=user.get("name", "System")
    )
    
    return ticket


@router.get("")
async def list_tickets(request: Request, ctx: TenantContext = Depends(tenant_context_required),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    ticket_type: Optional[str] = Query(None, description="Filter by ticket type: onsite or workshop"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: Optional[str] = Query(None, description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    """
    List tickets with pagination and filtering
    
    Returns standardized paginated response:
    - data: Array of tickets
    - pagination: {page, limit, total_count, total_pages, has_next, has_prev}
    
    - Customers see only their tickets
    - Technicians see assigned + unassigned tickets
    - Admins see all tickets
    - Strictly scoped to user's organization
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    
    # Cap limit at 100
    if limit > 100:
        limit = 100
    
    # Calculate skip for backward compatibility with service layer
    skip = (page - 1) * limit
    
    # Use tenant context for org_id (strict enforcement)
    result = await service.list_tickets(
        user_id=user.get("user_id"),
        user_role=user.get("role"),
        status=status,
        priority=priority,
        category=category,
        ticket_type=ticket_type,
        limit=limit,
        skip=skip,
        organization_id=ctx.org_id
    )
    
    # Get total count for pagination
    total_count = result.get("total", len(result.get("tickets", [])))
    import math
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
    
    return {
        "data": result.get("tickets", []),
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


@router.get("/stats")
async def get_ticket_stats(request: Request, ctx: TenantContext = Depends(tenant_context_required)
):
    """Get ticket statistics for dashboard (scoped to organization)"""
    service = get_service()
    await get_current_user(request, service.db)  # Auth check
    
    return await service.get_ticket_stats(organization_id=ctx.org_id)


@router.get("/{ticket_id}")
async def get_ticket(request: Request, ticket_id: str, ctx: TenantContext = Depends(tenant_context_required)
):
    """Get a single ticket by ID (must belong to user's organization)"""
    service = get_service()
    await get_current_user(request, service.db)  # Auth check
    
    ticket = await service.get_ticket(ticket_id, organization_id=ctx.org_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@router.put("/{ticket_id}")
async def update_ticket(request: Request, ticket_id: str, data: TicketUpdateRequest, ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Update a ticket
    
    - Updates specified fields
    - Tracks status changes in history
    - Emits appropriate events
    - Scoped to user's organization
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    update_data = TicketUpdateData(**data.model_dump())
    
    try:
        ticket = await service.update_ticket(
            ticket_id=ticket_id,
            data=update_data,
            user_id=user.get("user_id"),
            user_name=user.get("name", "System"),
            organization_id=ctx.org_id
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{ticket_id}/close")
async def close_ticket(request: Request, ticket_id: str, data: TicketCloseRequest, ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Close a ticket with resolution details
    
    CRITICAL EFI ENDPOINT:
    - Requires resolution and outcome
    - Triggers confidence engine updates
    - Auto-creates draft failure card for undocumented issues
    - Scoped to user's organization
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    close_data = TicketCloseData(**data.model_dump())
    
    try:
        ticket = await service.close_ticket(
            ticket_id=ticket_id,
            data=close_data,
            user_id=user.get("user_id"),
            user_name=user.get("name", "System"),
            organization_id=ctx.org_id
        )
        # Audit log
        from utils.audit import log_audit, AuditAction
        await log_audit(service.db, AuditAction.TICKET_CLOSED, ctx.org_id, user.get("user_id"),
            "ticket", ticket_id, {"resolution": data.resolution, "confirmed_fault": data.confirmed_fault})
        
        # Auto-create failure card for EFI brain
        try:
            from routes.failure_cards import router as _fc_router
            fc_card_id = f"fc_{__import__('uuid').uuid4().hex[:12]}"
            from datetime import timezone as _tz
            now_iso = datetime.now(_tz.utc).isoformat()
            
            failure_card = {
                "card_id": fc_card_id,
                "organization_id": ctx.org_id,
                "ticket_id": ticket_id,
                "ticket_type": ticket.get("ticket_type", "onsite"),
                "vehicle_category": ticket.get("vehicle_type") or ticket.get("vehicle_category"),
                "vehicle_make": ticket.get("vehicle_oem") or ticket.get("vehicle_make"),
                "vehicle_model": ticket.get("vehicle_model"),
                "vehicle_year": ticket.get("vehicle_year"),
                "issue_title": ticket.get("title"),
                "issue_description": ticket.get("description"),
                "dtc_codes": ticket.get("error_codes_reported", []),
                "fault_category": ticket.get("category"),
                "root_cause": data.resolution or "",
                "diagnosis_steps": [],
                "resolution_steps": [],
                "parts_used": [],
                "labour_hours": None,
                "resolution_successful": data.outcome in ("fixed", "resolved", True),
                "efi_suggested_fault": ticket.get("efi_suggested_fault"),
                "efi_confidence": ticket.get("efi_confidence"),
                "efi_was_correct": None,
                "technician_id": ticket.get("assigned_technician_id"),
                "closed_by": user.get("user_id"),
                "closed_at": now_iso,
                "created_at": now_iso,
                "anonymised": False,
                "fed_to_brain_at": None,
            }
            # Only create if one doesn't already exist
            existing_fc = await service.db.failure_cards.find_one(
                {"organization_id": ctx.org_id, "ticket_id": ticket_id}
            )
            if not existing_fc:
                await service.db.failure_cards.insert_one(failure_card)
                ticket["failure_card_id"] = fc_card_id
                
                # Sprint 3B-03: Auto-generate embedding for new failure card
                try:
                    from services.efi_embedding_service import EFIEmbeddingManager
                    efi_emb = EFIEmbeddingManager(service.db)
                    card_text = (
                        f"{failure_card.get('issue_title', '')} "
                        f"{failure_card.get('issue_description', '')} "
                        f"{failure_card.get('root_cause', '')} "
                        f"{failure_card.get('fault_category', '')}"
                    ).strip()
                    if card_text:
                        emb_result = await efi_emb.generate_complaint_embedding(card_text)
                        if emb_result and emb_result.get("embedding"):
                            await service.db.failure_cards.update_one(
                                {"card_id": fc_card_id},
                                {"$set": {
                                    "embedding_vector": emb_result["embedding"],
                                    "subsystem_category": emb_result.get("classified_subsystem"),
                                    "embedding_generated_at": datetime.now(_tz.utc).isoformat()
                                }}
                            )
                except Exception as emb_err:
                    logger.warning(f"Embedding generation failed for card {fc_card_id}: {emb_err}")
        except Exception as e:
            logger.warning(f"Failed to create failure card for ticket {ticket_id}: {e}")
        
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== WORKFLOW ROUTES ====================

class StartWorkRequest(BaseModel):
    """Request to start work on a ticket"""
    notes: Optional[str] = None


class CompleteWorkRequest(BaseModel):
    """Request to complete work on a ticket"""
    work_summary: str
    parts_used: Optional[List[str]] = None
    labor_hours: Optional[float] = None
    notes: Optional[str] = None


class AddActivityRequest(BaseModel):
    """Request to add activity log entry"""
    action: str
    description: str


class UpdateActivityRequest(BaseModel):
    """Request to update activity log entry"""
    description: str


@router.post("/{ticket_id}/start-work")
async def start_work(request: Request, ticket_id: str, data: StartWorkRequest):
    """
    Start work on a ticket (transitions to work_in_progress)
    
    - Usually auto-triggered when estimate is approved
    - Can be manually triggered if estimate was already approved
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    try:
        ticket = await service.start_work(
            ticket_id=ticket_id,
            notes=data.notes,
            user_id=user.get("user_id"),
            user_name=user.get("name", "System")
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{ticket_id}/complete-work")
async def complete_work(request: Request, ticket_id: str, data: CompleteWorkRequest):
    """
    Mark work as completed on a ticket
    
    - Transitions ticket to "work_completed" status
    - Records work summary and parts used
    - Ticket can still be edited until closed
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    try:
        ticket = await service.complete_work(
            ticket_id=ticket_id,
            work_summary=data.work_summary,
            parts_used=data.parts_used,
            labor_hours=data.labor_hours,
            notes=data.notes,
            user_id=user.get("user_id"),
            user_name=user.get("name", "System")
        )
        
        # P1-13B: Step 7→8 bridge — check if invoice exists for this ticket
        org_id = ticket.get("organization_id", "")
        if org_id:
            existing_invoice = await service.db.invoices.find_one(
                {"ticket_id": ticket_id, "organization_id": org_id}, {"_id": 0, "invoice_id": 1, "status": 1}
            )
            if existing_invoice:
                ticket["invoice_status"] = existing_invoice.get("status")
                ticket["invoice_id"] = existing_invoice.get("invoice_id")
            else:
                ticket["next_action"] = "create_invoice"
                ticket["invoice_prompt"] = (
                    "Ticket completed. No invoice found. "
                    "Create invoice from estimates?"
                )
        
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ticket_id}/activities")
async def get_ticket_activities(request: Request, ticket_id: str):
    """
    Get all activity logs for a ticket
    
    - Returns chronological list of all activities
    - Editable flag indicates if admin can edit
    """
    service = get_service()
    await get_current_user(request, service.db)
    
    activities = await service.db.ticket_activities.find(
        {"ticket_id": ticket_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(500)
    
    return {"activities": activities}


@router.post("/{ticket_id}/activities")
async def add_activity(request: Request, ticket_id: str, data: AddActivityRequest):
    """
    Add a manual activity log entry
    
    - Useful for recording notes, observations
    - All activities are editable by admin
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    try:
        activity = await service.add_activity(
            ticket_id=ticket_id,
            action=data.action,
            description=data.description,
            user_id=user.get("user_id"),
            user_name=user.get("name", "System")
        )
        return activity
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{ticket_id}/activities/{activity_id}")
async def update_activity(request: Request, ticket_id: str, 
    activity_id: str, 
    data: UpdateActivityRequest
):
    """
    Update an activity log entry (admin only)
    
    - Only admin can edit activities
    - Original timestamp preserved
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    
    # Only admin can edit activities
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can edit activities")
    
    try:
        activity = await service.update_activity(
            ticket_id=ticket_id,
            activity_id=activity_id,
            description=data.description,
            user_id=user.get("user_id"),
            user_name=user.get("name", "System")
        )
        return activity
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{ticket_id}/activities/{activity_id}")
async def delete_activity(request: Request, ticket_id: str, activity_id: str):
    """
    Delete an activity log entry (admin only)
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    
    # Only admin can delete activities
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete activities")
    
    result = await service.db.ticket_activities.delete_one({
        "activity_id": activity_id,
        "ticket_id": ticket_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return {"message": "Activity deleted"}


@router.post("/{ticket_id}/assign")
async def assign_ticket(request: Request, ticket_id: str, data: AssignTicketRequest):
    """
    Assign ticket to a technician
    
    - Updates ticket status to "assigned"
    - Records assignment in history
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    try:
        ticket = await service.assign_ticket(
            ticket_id=ticket_id,
            technician_id=data.technician_id,
            user_id=user.get("user_id"),
            user_name=user.get("name", "System")
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{ticket_id}/matches")
async def get_ticket_matches(request: Request, ticket_id: str):
    """
    Get AI-suggested failure cards for a ticket
    
    Returns cards matched by the EFI AI matching pipeline:
    1. Signature match
    2. Subsystem + vehicle filter
    3. Semantic similarity
    4. Keyword fallback
    """
    service = get_service()
    await get_current_user(request, service.db)  # Auth check
    
    try:
        result = await service.get_ticket_matches(ticket_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{ticket_id}/select-card")
async def select_failure_card(request: Request, ticket_id: str, data: SelectCardRequest):
    """
    Select a failure card for the ticket
    
    Links the ticket to a known failure pattern for:
    - Diagnosis guidance
    - Resolution steps
    - Parts recommendations
    """
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    try:
        result = await service.select_failure_card(
            ticket_id=ticket_id,
            failure_id=data.failure_id,
            user_id=user.get("user_id")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== LEGACY COMPATIBILITY ROUTES ====================
# These maintain backward compatibility with existing frontend

@router.post("/{ticket_id}/select-card/{failure_id}")
async def select_failure_card_legacy(request: Request, ticket_id: str, failure_id: str):
    """Legacy route - select failure card by path parameter"""
    service = get_service()
    user = await get_current_user(request, service.db)
    await require_technician_or_admin(user)
    
    try:
        result = await service.select_failure_card(
            ticket_id=ticket_id,
            failure_id=failure_id,
            user_id=user.get("user_id")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
