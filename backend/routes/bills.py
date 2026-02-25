"""
Bills API Routes - Vendor Invoice Management
============================================
RESTful API for vendor bills:
- CRUD operations with line items
- Approval workflow
- Payment recording
- Aging reports

Author: Battwheels OS
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from services.period_lock_service import check_period_lock
from datetime import datetime, timezone
import logging
import jwt

from services.bills_service import (
    init_bills_service,
    get_bills_service,
    BILL_STATUSES
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bills", tags=["Bills"])

# ==================== MODELS ====================

class LineItemCreate(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "nos"
    rate: float
    gst_rate: float = 18
    is_igst: bool = False
    hsn_sac_code: Optional[str] = None
    account_code: str = "5000"


class BillCreate(BaseModel):
    bill_number: str  # Vendor's invoice number
    vendor_id: str
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    bill_date: str
    due_date: str
    line_items: List[LineItemCreate]
    purchase_order_id: Optional[str] = None
    is_rcm: bool = False
    notes: Optional[str] = None


class BillUpdate(BaseModel):
    bill_number: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    bill_date: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None


class PaymentRecord(BaseModel):
    amount: float = Field(..., gt=0)
    payment_date: str
    payment_mode: str = "BANK"
    bank_account_id: Optional[str] = None
    reference_number: Optional[str] = None


# ==================== DEPENDENCIES ====================

db_ref = None


def set_db(db):
    global db_ref
    db_ref = db
    init_bills_service(db)


def get_service():
    return get_bills_service()


async def get_current_user_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        return user.get("user_id", "system")
    return "system"


async def get_org_id(request: Request) -> str:
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        return org_id
    
    org_id = request.cookies.get("org_id")
    if org_id:
        return org_id
    
    user = getattr(request.state, "user", None)
    if user and user.get("org_id"):
        return user.get("org_id")
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, options={"verify_signature": False})
            if payload.get("org_id"):
                return payload.get("org_id")
        except:
            pass
    
    raise HTTPException(status_code=400, detail="Organization ID required")


# ==================== ROUTES ====================

@router.get("/constants")
async def get_constants():
    """Get bill constants"""
    return {
        "code": 0,
        "statuses": BILL_STATUSES
    }


@router.get("/aging")
async def get_aging_report(request: Request):
    """Get bills aging report grouped by days overdue"""
    service = get_service()
    org_id = await get_org_id(request)
    
    report = await service.get_aging_report(org_id)
    
    return {"code": 0, **report}


@router.get("/aging/vendor")
async def get_vendor_aging_report(request: Request):
    """Get bills aging report grouped by vendor"""
    service = get_service()
    org_id = await get_org_id(request)
    
    report = await service.get_vendor_aging_report(org_id)
    
    return {"code": 0, **report}


@router.get("/export")
async def export_bills(request: Request, status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """Export bills as CSV"""
    import io
    import csv
    from fastapi.responses import StreamingResponse
    
    service = get_service()
    org_id = await get_org_id(request)
    
    bills, _ = await service.list_bills(
        org_id=org_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=1000
    )
    
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    
    writer.writerow([
        "Internal Ref", "Vendor Invoice #", "Vendor", "GSTIN", "Bill Date", "Due Date",
        "Subtotal", "CGST", "SGST", "IGST", "Total Amount",
        "Amount Paid", "Balance Due", "Status", "ITC Eligible", "RCM"
    ])
    
    for bill in bills:
        writer.writerow([
            bill.get("internal_ref"),
            bill.get("bill_number"),
            bill.get("vendor_name") or "",
            bill.get("vendor_gstin") or "",
            bill.get("bill_date"),
            bill.get("due_date"),
            bill.get("subtotal"),
            bill.get("cgst"),
            bill.get("sgst"),
            bill.get("igst"),
            bill.get("total_amount"),
            bill.get("amount_paid"),
            bill.get("balance_due"),
            bill.get("status"),
            "Yes" if bill.get("is_itc_eligible") else "No",
            "Yes" if bill.get("is_rcm") else "No"
        ])
    
    csv_buffer.seek(0)
    filename = f"bills_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("")
async def list_bills(request: Request, status: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List bills with filters and standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    service = get_service()
    org_id = await get_org_id(request)

    bills, total = await service.list_bills(
        org_id=org_id,
        status=status,
        vendor_id=vendor_id,
        date_from=date_from,
        date_to=date_to,
        overdue_only=overdue_only,
        page=page,
        limit=limit
    )

    total_pages = math.ceil(total / limit) if total > 0 else 1
    return {
        "data": bills,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


@router.post("")
async def create_bill(request: Request, data: BillCreate):
    """Create a new vendor bill"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id = await get_current_user_id(request)
    
    # Period lock check on bill_date
    if data.bill_date:
        await check_period_lock(org_id, data.bill_date)
    
    # Convert line items to dicts
    line_items = [item.dict() for item in data.line_items]
    
    bill = await service.create_bill(
        org_id=org_id,
        bill_number=data.bill_number,
        vendor_id=data.vendor_id,
        vendor_name=data.vendor_name,
        vendor_gstin=data.vendor_gstin,
        bill_date=data.bill_date,
        due_date=data.due_date,
        line_items=line_items,
        purchase_order_id=data.purchase_order_id,
        is_rcm=data.is_rcm,
        notes=data.notes,
        created_by=user_id
    )
    
    return {"code": 0, "message": "Bill created", "bill": bill}


@router.get("/{bill_id}")
async def get_bill(request: Request, bill_id: str):
    """Get a single bill with line items and payments"""
    service = get_service()
    
    bill = await service.get_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    return {"code": 0, "bill": bill}


@router.put("/{bill_id}")
async def update_bill(request: Request, bill_id: str, data: BillUpdate):
    """Update a bill (DRAFT only)"""
    service = get_service()
    
    try:
        updates = {k: v for k, v in data.dict().items() if v is not None}
        bill = await service.update_bill(bill_id, updates)
        
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        return {"code": 0, "message": "Bill updated", "bill": bill}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{bill_id}/approve")
async def approve_bill(request: Request, bill_id: str):
    """Approve bill and post journal entry"""
    from services.double_entry_service import get_double_entry_service, init_double_entry_service
    
    service = get_service()
    user_id = await get_current_user_id(request)
    
    try:
        de_service = get_double_entry_service()
    except:
        init_double_entry_service(db_ref)
        de_service = get_double_entry_service()
    
    try:
        bill, journal_entry_id = await service.approve_bill(
            bill_id=bill_id,
            approved_by=user_id,
            de_service=de_service
        )
        
        return {
            "code": 0,
            "message": "Bill approved",
            "bill": bill,
            "journal_entry_id": journal_entry_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{bill_id}/record-payment")
async def record_payment(request: Request, bill_id: str, data: PaymentRecord):
    """Record payment against a bill"""
    from services.double_entry_service import get_double_entry_service, init_double_entry_service
    
    service = get_service()
    user_id = await get_current_user_id(request)
    
    try:
        de_service = get_double_entry_service()
    except:
        init_double_entry_service(db_ref)
        de_service = get_double_entry_service()
    
    try:
        payment, journal_entry_id = await service.record_payment(
            bill_id=bill_id,
            amount=data.amount,
            payment_date=data.payment_date,
            payment_mode=data.payment_mode,
            bank_account_id=data.bank_account_id,
            reference_number=data.reference_number,
            paid_by=user_id,
            de_service=de_service
        )
        
        return {
            "code": 0,
            "message": f"Payment of ₹{data.amount} recorded",
            "payment": payment,
            "journal_entry_id": journal_entry_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{bill_id}/payments")
async def get_bill_payments(request: Request, bill_id: str):
    """Get all payments for a bill"""
    service = get_service()
    
    bill = await service.get_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    return {
        "code": 0,
        "payments": bill.get("payments", []),
        "total_paid": bill.get("amount_paid", 0),
        "balance_due": bill.get("balance_due", 0)
    }
