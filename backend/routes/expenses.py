"""
Expenses API Routes
===================
RESTful API for expense management:
- CRUD operations
- Workflow (submit, approve, reject, mark-paid)
- Categories management
- Summary and export

Author: Battwheels OS
"""

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from services.period_lock_service import check_period_lock
from datetime import datetime, timezone
import logging
import base64
import uuid

from services.expenses_service import (
    init_expenses_service,
    get_expenses_service,
    EXPENSE_STATUSES,
    PAYMENT_MODES,
    GST_RATES
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/expenses", tags=["Expenses"])

# ==================== MODELS ====================

class ExpenseCreate(BaseModel):
    expense_date: str
    vendor_name: str
    description: str
    amount: float = Field(..., gt=0)
    category_id: str
    vendor_gstin: Optional[str] = None
    gst_rate: float = 0
    is_igst: bool = False
    hsn_sac_code: Optional[str] = None
    payment_mode: str = "PENDING"
    bank_account_id: Optional[str] = None
    receipt_url: Optional[str] = None
    project_id: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    expense_date: Optional[str] = None
    vendor_name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    category_id: Optional[str] = None
    vendor_gstin: Optional[str] = None
    gst_rate: Optional[float] = None
    is_igst: Optional[bool] = None
    hsn_sac_code: Optional[str] = None
    payment_mode: Optional[str] = None
    bank_account_id: Optional[str] = None
    receipt_url: Optional[str] = None
    project_id: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class MarkPaidRequest(BaseModel):
    payment_mode: str = "BANK"
    bank_account_id: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    default_account_code: str = "6900"
    is_itc_eligible: bool = False


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    default_account_code: Optional[str] = None
    is_itc_eligible: Optional[bool] = None
    is_active: Optional[bool] = None


# ==================== DEPENDENCIES ====================

db_ref = None


def set_db(db):
    global db_ref
    db_ref = db
    init_expenses_service(db)


def get_service():
    return get_expenses_service()


async def get_current_user_id(request: Request) -> str:
    """Extract current user ID from request"""
    user = getattr(request.state, "user", None)
    if user:
        return user.get("user_id", "system")
    return "system"


async def get_org_id(request: Request) -> str:
    """Extract organization ID from request"""
    # Try from headers first (multi-tenant)
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        return org_id
    
    # Try from cookies
    org_id = request.cookies.get("org_id")
    if org_id:
        return org_id
    
    # Try from user state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user and user.get("org_id"):
        return user.get("org_id")
    
    # Try to decode from Authorization header directly
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            import jwt
            token = auth_header.split(" ")[1]
            # Decode without verification to get org_id
            payload = jwt.decode(token, options={"verify_signature": False})
            if payload.get("org_id"):
                return payload.get("org_id")
        except Exception:
            pass
    
    raise HTTPException(status_code=400, detail="Organization ID required")


# ==================== EXPENSE ROUTES ====================

# Static routes MUST come before dynamic routes ({expense_id})

@router.get("/constants")
async def get_constants():
    """Get expense constants (statuses, payment modes, GST rates)"""
    return {
        "code": 0,
        "statuses": EXPENSE_STATUSES,
        "payment_modes": PAYMENT_MODES,
        "gst_rates": GST_RATES
    }


@router.get("/categories")
async def list_categories(request: Request):
    """List all expense categories"""
    service = get_service()
    org_id = await get_org_id(request)
    
    categories = await service.list_categories(org_id)
    
    return {"code": 0, "categories": categories}


@router.post("/categories")
async def create_category(request: Request, data: CategoryCreate):
    """Create a new expense category"""
    service = get_service()
    org_id = await get_org_id(request)
    
    category = await service.create_category(
        org_id=org_id,
        name=data.name,
        default_account_code=data.default_account_code,
        is_itc_eligible=data.is_itc_eligible
    )
    
    return {"code": 0, "message": "Category created", "category": category}


@router.put("/categories/{category_id}")
async def update_category(request: Request, category_id: str, data: CategoryUpdate):
    """Update an expense category"""
    service = get_service()
    
    updates = {k: v for k, v in data.dict().items() if v is not None}
    category = await service.update_category(category_id, updates)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"code": 0, "message": "Category updated", "category": category}


@router.get("")
async def list_expenses(request: Request, status: Optional[str] = Query(None, description="Filter by status"),
    category_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List expenses with filters and standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    service = get_service()
    org_id = await get_org_id(request)

    expenses, total = await service.list_expenses(
        org_id=org_id,
        status=status,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
        search=search,
        page=page,
        limit=limit
    )

    total_pages = math.ceil(total / limit) if total > 0 else 1
    return {
        "data": expenses,
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
async def create_expense(request: Request, data: ExpenseCreate):
    """Create a new expense in DRAFT status"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id = await get_current_user_id(request)
    
    # Period lock check on expense_date
    if data.expense_date:
        await check_period_lock(org_id, data.expense_date)
    
    expense = await service.create_expense(
        org_id=org_id,
        expense_date=data.expense_date,
        vendor_name=data.vendor_name,
        description=data.description,
        amount=data.amount,
        category_id=data.category_id,
        employee_id=user_id,
        vendor_gstin=data.vendor_gstin,
        gst_rate=data.gst_rate,
        is_igst=data.is_igst,
        hsn_sac_code=data.hsn_sac_code,
        payment_mode=data.payment_mode,
        bank_account_id=data.bank_account_id,
        receipt_url=data.receipt_url,
        project_id=data.project_id,
        ticket_id=data.ticket_id,
        notes=data.notes
    )
    
    # Audit: expense.created
    from utils.audit import log_audit, AuditAction
    await log_audit(service.db, AuditAction.EXPENSE_CREATED, org_id, user_id,
        "expense", expense.get("expense_id", ""), {"amount": data.amount, "vendor": data.vendor_name, "category": data.category_id})
    
    return {"code": 0, "message": "Expense created", "expense": expense}


@router.get("/summary")
async def get_expense_summary(request: Request, date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """Get expense summary statistics"""
    service = get_service()
    org_id = await get_org_id(request)
    
    summary = await service.get_summary(org_id, date_from, date_to)
    
    return {"code": 0, "summary": summary}


@router.get("/export")
async def export_expenses(request: Request, status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """Export expenses as CSV"""
    import io
    import csv
    from fastapi.responses import StreamingResponse
    
    service = get_service()
    org_id = await get_org_id(request)
    
    expenses, _ = await service.list_expenses(
        org_id=org_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=1000
    )
    
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    
    # Header
    writer.writerow([
        "Expense No.", "Date", "Vendor", "GSTIN", "Category", "Description",
        "Base Amount", "CGST", "SGST", "IGST", "Total", "GST Rate",
        "ITC Eligible", "Payment Mode", "Status", "Submitted By", "Approved By"
    ])
    
    for exp in expenses:
        writer.writerow([
            exp.get("expense_number"),
            exp.get("expense_date"),
            exp.get("vendor_name"),
            exp.get("vendor_gstin") or "",
            exp.get("category_name", ""),
            exp.get("description"),
            exp.get("amount"),
            exp.get("cgst_amount"),
            exp.get("sgst_amount"),
            exp.get("igst_amount"),
            exp.get("total_amount"),
            exp.get("gst_rate"),
            "Yes" if exp.get("is_itc_eligible") else "No",
            exp.get("payment_mode"),
            exp.get("status"),
            exp.get("employee_id"),
            exp.get("approved_by") or ""
        ])
    
    csv_buffer.seek(0)
    
    filename = f"expenses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{expense_id}")
async def get_expense(request: Request, expense_id: str):
    """Get a single expense by ID"""
    service = get_service()
    
    expense = await service.get_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Enrich with category
    if expense.get("category_id"):
        cat = await service.get_category(expense["category_id"])
        expense["category_name"] = cat.get("name") if cat else "Unknown"
    
    return {"code": 0, "expense": expense}


@router.put("/{expense_id}")
async def update_expense(request: Request, expense_id: str, data: ExpenseUpdate):
    """Update an expense (only DRAFT or REJECTED)"""
    service = get_service()
    
    try:
        updates = {k: v for k, v in data.dict().items() if v is not None}
        expense = await service.update_expense(expense_id, updates)
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        return {"code": 0, "message": "Expense updated", "expense": expense}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{expense_id}")
async def delete_expense(request: Request, expense_id: str):
    """Delete an expense (only DRAFT)"""
    service = get_service()
    
    try:
        deleted = await service.delete_expense(expense_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        return {"code": 0, "message": "Expense deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== WORKFLOW ROUTES ====================

@router.post("/{expense_id}/submit")
async def submit_expense(request: Request, expense_id: str):
    """Submit expense for approval (DRAFT → SUBMITTED)"""
    service = get_service()
    
    try:
        expense = await service.submit_expense(expense_id)
        return {"code": 0, "message": "Expense submitted for approval", "expense": expense}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{expense_id}/approve")
async def approve_expense(request: Request, expense_id: str):
    """
    Approve expense (SUBMITTED → APPROVED)
    Posts journal entry with ITC capture if eligible
    """
    from services.double_entry_service import get_double_entry_service, init_double_entry_service
    
    service = get_service()
    user_id = await get_current_user_id(request)
    
    # Get double-entry service
    try:
        de_service = get_double_entry_service()
    except:
        init_double_entry_service(db_ref)
        de_service = get_double_entry_service()
    
    try:
        expense, journal_entry_id = await service.approve_expense(
            expense_id=expense_id,
            approved_by=user_id,
            de_service=de_service
        )
        
        return {
            "code": 0,
            "message": "Expense approved",
            "expense": expense,
            "journal_entry_id": journal_entry_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{expense_id}/reject")
async def reject_expense(request: Request, expense_id: str, data: RejectRequest):
    """Reject expense (SUBMITTED → REJECTED)"""
    service = get_service()
    user_id = await get_current_user_id(request)
    
    try:
        expense = await service.reject_expense(
            expense_id=expense_id,
            rejected_by=user_id,
            reason=data.reason
        )
        
        return {"code": 0, "message": "Expense rejected", "expense": expense}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{expense_id}/mark-paid")
async def mark_expense_paid(request: Request, expense_id: str, data: MarkPaidRequest):
    """
    Mark expense as paid (APPROVED → PAID)
    Posts payment journal entry
    """
    from services.double_entry_service import get_double_entry_service, init_double_entry_service
    
    service = get_service()
    user_id = await get_current_user_id(request)
    
    # Get double-entry service
    try:
        de_service = get_double_entry_service()
    except:
        init_double_entry_service(db_ref)
        de_service = get_double_entry_service()
    
    try:
        expense, journal_entry_id = await service.mark_paid(
            expense_id=expense_id,
            payment_mode=data.payment_mode,
            bank_account_id=data.bank_account_id,
            paid_by=user_id,
            de_service=de_service
        )
        
        return {
            "code": 0,
            "message": f"Expense marked as paid via {data.payment_mode}",
            "expense": expense,
            "journal_entry_id": journal_entry_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== RECEIPT UPLOAD ====================

@router.post("/upload-receipt")
async def upload_receipt(request: Request, file: UploadFile = File(...)):
    """Upload expense receipt (image/PDF)"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB")
    
    # Store in DB as base64 (for simplicity - in production use object storage)
    org_id = await get_org_id(request)
    receipt_id = f"receipt_{uuid.uuid4().hex[:12]}"
    
    receipt_data = {
        "receipt_id": receipt_id,
        "organization_id": org_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "data": base64.b64encode(contents).decode("utf-8"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db_ref.expense_receipts.insert_one(receipt_data)
    
    # Return URL path (will be served by another endpoint)
    receipt_url = f"/api/expenses/receipts/{receipt_id}"
    
    return {"code": 0, "receipt_url": receipt_url, "receipt_id": receipt_id}


@router.get("/receipts/{receipt_id}")
async def get_receipt(request: Request, receipt_id: str):
    """Get uploaded receipt"""
    from fastapi.responses import Response
    
    receipt = await db_ref.expense_receipts.find_one(
        {"receipt_id": receipt_id},
        {"_id": 0}
    )
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Decode and return
    data = base64.b64decode(receipt["data"])
    
    return Response(
        content=data,
        media_type=receipt["content_type"],
        headers={
            "Content-Disposition": f"inline; filename={receipt['filename']}"
        }
    )
