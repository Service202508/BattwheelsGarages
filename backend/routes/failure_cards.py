"""
Battwheels OS - Failure Cards API
==================================
Auto-generated failure cards on ticket close.
Feeds anonymised data to the EFI platform brain.
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException, Depends, Query

from utils.auth import get_current_user
from core.tenant.context import TenantContext, tenant_context_required

router = APIRouter(prefix="/failure-cards", tags=["failure-cards"])


def get_db():
    from server import db
    return db


# ==================== MODELS ====================

class FailureCardUpdate(BaseModel):
    root_cause: Optional[str] = None
    fault_category: Optional[str] = None
    diagnosis_steps: Optional[List[str]] = None
    resolution_steps: Optional[List[str]] = None
    efi_was_correct: Optional[bool] = None
    additional_notes: Optional[str] = None
    resolution_successful: Optional[bool] = True


# ==================== ENDPOINTS ====================

@router.post("")
async def create_failure_card(request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    """
    Create a failure card from a closed ticket.
    Typically called by the ticket close flow.
    Body: { ticket_id: str }
    """
    db = get_db()
    user = await get_current_user(request, db)
    body = await request.json()
    ticket_id = body.get("ticket_id")
    
    if not ticket_id:
        raise HTTPException(status_code=400, detail="ticket_id is required")
    
    # Check if card already exists for this ticket
    existing = await db.failure_cards.find_one(
        {"organization_id": ctx.org_id, "ticket_id": ticket_id},
        {"_id": 0, "card_id": 1}
    )
    if existing:
        return existing
    
    # Fetch the ticket
    ticket = await db.tickets.find_one(
        {"ticket_id": ticket_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Build failure card pre-populated from ticket data
    card_id = f"fc_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    failure_card = {
        "card_id": card_id,
        "organization_id": ctx.org_id,
        "ticket_id": ticket_id,
        "ticket_type": ticket.get("ticket_type", "onsite"),
        
        # Vehicle context
        "vehicle_category": ticket.get("vehicle_type") or ticket.get("vehicle_category"),
        "vehicle_make": ticket.get("vehicle_oem") or ticket.get("vehicle_make"),
        "vehicle_model": ticket.get("vehicle_model"),
        "vehicle_year": ticket.get("vehicle_year"),
        
        # Fault data
        "issue_title": ticket.get("title"),
        "issue_description": ticket.get("description"),
        "dtc_codes": ticket.get("error_codes_reported", []),
        "fault_category": ticket.get("category"),
        "root_cause": ticket.get("resolution") or "",
        
        # Resolution data (to be filled by technician)
        "diagnosis_steps": [],
        "resolution_steps": [],
        "parts_used": [],
        "labour_hours": ticket.get("labor_hours"),
        "resolution_successful": True,
        
        # EFI AI context
        "efi_suggested_fault": ticket.get("efi_suggested_fault"),
        "efi_confidence": ticket.get("efi_confidence"),
        "efi_was_correct": None,
        
        # Metadata
        "technician_id": ticket.get("assigned_technician_id"),
        "closed_by": user.get("user_id"),
        "closed_at": now,
        "created_at": now,
        
        # Brain feed status
        "anonymised": False,
        "fed_to_brain_at": None,
    }
    
    await db.failure_cards.insert_one(failure_card)
    
    # Return without _id
    failure_card.pop("_id", None)
    return failure_card


@router.get("/{card_id}")
async def get_failure_card(request: Request, card_id: str, ctx: TenantContext = Depends(tenant_context_required)):
    """Get a single failure card"""
    db = get_db()
    await get_current_user(request, db)
    
    card = await db.failure_cards.find_one(
        {"card_id": card_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    return card


@router.get("")
async def list_failure_cards(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    fault_category: Optional[str] = None,
    vehicle_make: Optional[str] = None,
):
    """List failure cards (org-scoped, paginated)"""
    db = get_db()
    await get_current_user(request, db)
    
    query = {"organization_id": ctx.org_id}
    if fault_category:
        query["fault_category"] = fault_category
    if vehicle_make:
        query["vehicle_make"] = vehicle_make
    
    skip = (page - 1) * limit
    total = await db.failure_cards.count_documents(query)
    cards = await db.failure_cards.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "data": cards,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": max(1, (total + limit - 1) // limit),
        }
    }


@router.put("/{card_id}")
async def update_failure_card(
    request: Request, card_id: str,
    data: FailureCardUpdate,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Update failure card details (technician fills in root cause, resolution, etc.)"""
    db = get_db()
    user = await get_current_user(request, db)
    
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_fields["updated_by"] = user.get("user_id")
    
    result = await db.failure_cards.update_one(
        {"card_id": card_id, "organization_id": ctx.org_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    # Check if card is complete enough to feed to brain
    card = await db.failure_cards.find_one(
        {"card_id": card_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    
    if card and card.get("root_cause") and not card.get("anonymised"):
        await feed_efi_brain(db, card)
    
    return card


@router.get("/by-ticket/{ticket_id}")
async def get_failure_card_by_ticket(request: Request, ticket_id: str, ctx: TenantContext = Depends(tenant_context_required)):
    """Get failure card linked to a specific ticket"""
    db = get_db()
    await get_current_user(request, db)
    
    card = await db.failure_cards.find_one(
        {"ticket_id": ticket_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    if not card:
        return {"card": None}
    return card


# ==================== EFI BRAIN FEEDING ====================

def hash_symptoms(text: str) -> str:
    """Create a deterministic hash of symptom text for pattern matching"""
    if not text:
        return ""
    normalized = text.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


async def feed_efi_brain(db, card: dict):
    """
    Create an anonymised platform pattern from a failure card.
    Strips all org-specific, customer, and technician data.
    """
    if card.get("anonymised"):
        return
    
    pattern = {
        "pattern_id": f"pat_{uuid.uuid4().hex[:12]}",
        "vehicle_category": card.get("vehicle_category"),
        "vehicle_make": card.get("vehicle_make"),
        "vehicle_model": card.get("vehicle_model"),
        "fault_category": card.get("fault_category"),
        "root_cause": card.get("root_cause"),
        "symptom_hash": hash_symptoms(card.get("issue_description", "")),
        "diagnosis_steps": card.get("diagnosis_steps", []),
        "resolution_steps": card.get("resolution_steps", []),
        "parts_used_names": [p.get("name", "") for p in card.get("parts_used", []) if isinstance(p, dict)],
        "resolution_successful": card.get("resolution_successful"),
        "efi_was_correct": card.get("efi_was_correct"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        # NO org_id, NO ticket_id, NO customer data, NO technician_id
    }
    
    await db.efi_platform_patterns.insert_one(pattern)
    await db.failure_cards.update_one(
        {"card_id": card["card_id"]},
        {"$set": {
            "anonymised": True,
            "fed_to_brain_at": datetime.now(timezone.utc).isoformat()
        }}
    )
