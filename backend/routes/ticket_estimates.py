"""
Battwheels OS - Ticket-Estimate Routes
API endpoints for ticket-estimate integration

Endpoints:
- POST /api/tickets/{id}/estimate/ensure - Create/get linked estimate
- GET /api/tickets/{id}/estimate - Get estimate + line items
- POST /api/ticket-estimates/{id}/line-items - Add line item
- PATCH /api/ticket-estimates/{id}/line-items/{line_id} - Update line item
- DELETE /api/ticket-estimates/{id}/line-items/{line_id} - Remove line item
- POST /api/ticket-estimates/{id}/approve - Approve estimate
- POST /api/ticket-estimates/{id}/send - Send estimate
- POST /api/ticket-estimates/{id}/lock - Lock estimate
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import os

from utils.auth import decode_token_safe

from services.ticket_estimate_service import (
    TicketEstimateService,
    EstimateLineItemCreate,
    EstimateLineItemUpdate,
    LockedEstimateError,
    ConcurrencyError,
    init_ticket_estimate_service,
    get_ticket_estimate_service
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ticket Estimates"])

_service: Optional[TicketEstimateService] = None
_db = None  # Store database reference


def init_router(database):
    """Initialize router with database"""
    global _service, _db
    _service = init_ticket_estimate_service(database)
    _db = database
    logger.info("Ticket-Estimate routes initialized")
    return router


def get_service() -> TicketEstimateService:
    """Get service instance"""
    if _service is None:
        raise HTTPException(status_code=500, detail="Ticket-Estimate service not initialized")
    return _service


# ==================== HELPERS ====================

async def get_current_user_from_token(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token or session"""
    global _db
    
    # Try JWT token first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_token_safe(token)
        if payload:
            # The JWT payload already contains user_id, email, role
            # Return it directly - role is in the token
            user_from_token = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            }
            
            # Optionally enrich with DB data if available
            if _db is not None:
                db_user = await _db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
                if db_user:
                    return db_user
            
            # Return token data if DB lookup failed
            return user_from_token
    
    # Try session cookie
    session_token = request.cookies.get("session_token")
    if session_token and _db is not None:
        session = await _db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            user = await _db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            if user:
                return user
    
    return None


async def get_org_id(request: Request) -> str:
    """Extract organization ID from request"""
    org_id = request.headers.get("X-Organization-ID")
    if not org_id:
        # Try from JWT user
        user = await get_current_user_from_token(request)
        if user:
            org_id = user.get("organization_id")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    return org_id


async def get_user_info(request: Request) -> tuple:
    """Extract user ID and name from request"""
    user = await get_current_user_from_token(request)
    if user:
        return user.get("user_id", "system"), user.get("name", "System")
    
    # Fallback
    return "system", "System"


# ==================== REQUEST MODELS ====================

class LineItemCreateRequest(BaseModel):
    """Request for adding a line item"""
    type: str = Field(default="part", pattern="^(part|labour|fee)$")
    item_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: str = ""
    qty: float = Field(default=1, gt=0)
    unit_price: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)
    tax_id: Optional[str] = None
    tax_rate: float = Field(default=0, ge=0, le=100)
    hsn_code: str = ""
    unit: str = "pcs"
    version: int = Field(..., description="Current estimate version for concurrency check")


class LineItemUpdateRequest(BaseModel):
    """Request for updating a line item"""
    name: Optional[str] = None
    description: Optional[str] = None
    qty: Optional[float] = None
    unit_price: Optional[float] = None
    discount: Optional[float] = None
    tax_id: Optional[str] = None
    tax_rate: Optional[float] = None
    version: int = Field(..., description="Current estimate version for concurrency check")


class LineItemDeleteRequest(BaseModel):
    """Request for deleting a line item"""
    version: int = Field(..., description="Current estimate version for concurrency check")


class LockEstimateRequest(BaseModel):
    """Request for locking an estimate"""
    reason: str = Field(..., min_length=1)


# ==================== TICKET → ESTIMATE ROUTES ====================

@router.post("/tickets/{ticket_id}/estimate/ensure")
async def ensure_ticket_estimate(request: Request, ticket_id: str):
    """
    Ensure an estimate exists for a ticket.
    Creates if missing, returns existing if present.
    
    Idempotent: Multiple calls return the same estimate.
    """
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    try:
        estimate = await service.ensure_estimate(
            ticket_id=ticket_id,
            organization_id=org_id,
            user_id=user_id,
            user_name=user_name
        )
        return {"code": 0, "estimate": estimate}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error ensuring estimate for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/{ticket_id}/estimate")
async def get_ticket_estimate(request: Request, ticket_id: str):
    """Get estimate for a ticket with line items"""
    service = get_service()
    org_id = await get_org_id(request)
    
    estimate = await service.get_estimate_by_ticket(ticket_id, org_id)
    
    if not estimate:
        raise HTTPException(status_code=404, detail="No estimate found for this ticket")
    
    return {"code": 0, "estimate": estimate}


# ==================== ESTIMATE LINE ITEM ROUTES ====================

@router.post("/ticket-estimates/{estimate_id}/line-items")
async def add_estimate_line_item(request: Request, estimate_id: str, 
    data: LineItemCreateRequest
):
    """Add a line item to an estimate"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    item_data = EstimateLineItemCreate(
        type=data.type,
        item_id=data.item_id,
        name=data.name,
        description=data.description,
        qty=data.qty,
        unit_price=data.unit_price,
        discount=data.discount,
        tax_id=data.tax_id,
        tax_rate=data.tax_rate,
        hsn_code=data.hsn_code,
        unit=data.unit
    )
    
    try:
        estimate = await service.add_line_item(
            estimate_id=estimate_id,
            organization_id=org_id,
            item_data=item_data,
            user_id=user_id,
            user_name=user_name,
            version=data.version
        )
        return {"code": 0, "estimate": estimate}
    except LockedEstimateError as e:
        raise HTTPException(
            status_code=423, 
            detail={
                "message": str(e),
                "locked_at": e.locked_at,
                "locked_by": e.locked_by
            }
        )
    except ConcurrencyError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Estimate was modified by another user. Please refresh.",
                "current_estimate": e.current_estimate
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding line item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/ticket-estimates/{estimate_id}/line-items/{line_item_id}")
async def update_estimate_line_item(request: Request, estimate_id: str,
    line_item_id: str,
    data: LineItemUpdateRequest
):
    """Update a line item"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    item_data = EstimateLineItemUpdate(
        name=data.name,
        description=data.description,
        qty=data.qty,
        unit_price=data.unit_price,
        discount=data.discount,
        tax_id=data.tax_id,
        tax_rate=data.tax_rate
    )
    
    try:
        estimate = await service.update_line_item(
            estimate_id=estimate_id,
            line_item_id=line_item_id,
            organization_id=org_id,
            item_data=item_data,
            user_id=user_id,
            user_name=user_name,
            version=data.version
        )
        return {"code": 0, "estimate": estimate}
    except LockedEstimateError as e:
        raise HTTPException(
            status_code=423,
            detail={
                "message": str(e),
                "locked_at": e.locked_at,
                "locked_by": e.locked_by
            }
        )
    except ConcurrencyError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Estimate was modified by another user. Please refresh.",
                "current_estimate": e.current_estimate
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating line item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ticket-estimates/{estimate_id}/line-items/{line_item_id}")
async def delete_estimate_line_item(
    estimate_id: str,
    line_item_id: str,
    version: int = Query(..., description="Current estimate version"),
    request: Request = None
):
    """Delete a line item"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    try:
        estimate = await service.delete_line_item(
            estimate_id=estimate_id,
            line_item_id=line_item_id,
            organization_id=org_id,
            user_id=user_id,
            user_name=user_name,
            version=version
        )
        return {"code": 0, "estimate": estimate}
    except LockedEstimateError as e:
        raise HTTPException(
            status_code=423,
            detail={
                "message": str(e),
                "locked_at": e.locked_at,
                "locked_by": e.locked_by
            }
        )
    except ConcurrencyError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Estimate was modified by another user. Please refresh.",
                "current_estimate": e.current_estimate
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting line item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ESTIMATE STATUS ROUTES ====================

@router.post("/ticket-estimates/{estimate_id}/approve")
async def approve_estimate(request: Request, estimate_id: str):
    """Approve an estimate"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    try:
        estimate = await service.approve_estimate(
            estimate_id=estimate_id,
            organization_id=org_id,
            user_id=user_id,
            user_name=user_name
        )
        return {"code": 0, "estimate": estimate, "message": "Estimate approved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ticket-estimates/{estimate_id}/send")
async def send_estimate(request: Request, estimate_id: str):
    """Mark estimate as sent"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    try:
        estimate = await service.send_estimate(
            estimate_id=estimate_id,
            organization_id=org_id,
            user_id=user_id,
            user_name=user_name
        )
        return {"code": 0, "estimate": estimate, "message": "Estimate sent"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ticket-estimates/{estimate_id}/lock")
async def lock_estimate(request: Request, estimate_id: str, 
    data: LockEstimateRequest
):
    """Lock an estimate to prevent further edits"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    # Check role - only admin/manager can lock
    user = await get_current_user_from_token(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, 
            detail="Only admin or manager can lock estimates"
        )
    
    try:
        estimate = await service.lock_estimate(
            estimate_id=estimate_id,
            organization_id=org_id,
            reason=data.reason,
            user_id=user_id,
            user_name=user_name
        )
        return {"code": 0, "estimate": estimate, "message": "Estimate locked"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error locking estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ticket-estimates/{estimate_id}/unlock")
async def unlock_estimate(request: Request, estimate_id: str
):
    """Unlock an estimate to allow further edits (admin only)"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    # Check role - only admin can unlock
    user = await get_current_user_from_token(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Only admin can unlock estimates"
        )
    
    try:
        estimate = await service.unlock_estimate(
            estimate_id=estimate_id,
            organization_id=org_id,
            user_id=user_id,
            user_name=user_name
        )
        return {"code": 0, "estimate": estimate, "message": "Estimate unlocked"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error unlocking estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ticket-estimates/{estimate_id}/convert-to-invoice")
async def convert_estimate_to_invoice(request: Request, estimate_id: str):
    """
    Convert an approved estimate to an invoice.
    Only approved estimates can be converted.
    """
    service = get_service()
    org_id = await get_org_id(request)
    user_id, user_name = await get_user_info(request)
    
    try:
        result = await service.convert_to_invoice(
            estimate_id=estimate_id,
            organization_id=org_id,
            user_id=user_id,
            user_name=user_name
        )
        return {
            "code": 0,
            "invoice": result["invoice"],
            "estimate": result["estimate"],
            "message": f"Invoice {result['invoice']['invoice_number']} created from estimate"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error converting estimate to invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticket-estimates/{estimate_id}")
async def get_estimate_by_id(request: Request, estimate_id: str):
    """Get estimate by ID"""
    service = get_service()
    org_id = await get_org_id(request)
    
    estimate = await service.get_estimate_by_id(estimate_id, org_id)
    
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    return {"code": 0, "estimate": estimate}


@router.get("/ticket-estimates")
async def list_ticket_estimates(request: Request, status: Optional[str] = None, page: int = 1, per_page: int = 20):
    """List all ticket estimates for organization"""
    service = get_service()
    org_id = await get_org_id(request)
    
    query = {"organization_id": org_id}
    if status:
        query["status"] = status
    
    total = await service.estimates.count_documents(query)
    skip = (page - 1) * per_page
    
    estimates = await service.estimates.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "estimates": estimates,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total
        }
    }
