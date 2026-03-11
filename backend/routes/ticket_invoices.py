"""
Ticket Invoices API
Provides CRUD endpoints for the ticket_invoices collection.
Includes PDF generation and payment recording.
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
import uuid
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ticket-invoices", tags=["Ticket Invoices"])

db = None

def init_router(database):
    global db
    db = database

def set_db(database):
    global db
    db = database

def _org_id(request: Request) -> str:
    return getattr(request.state, "tenant_org_id", None) or ""

def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    payment_mode: str = "cash"
    reference_number: str = ""
    payment_date: str = ""
    notes: str = ""

@router.get("/")
async def list_ticket_invoices(
    request: Request,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    org_id = _org_id(request)
    query = {"organization_id": org_id} if org_id else {}
    if status:
        query["status"] = status
    if payment_status:
        query["payment_status"] = payment_status
    total = await db.ticket_invoices.count_documents(query)
    docs = await db.ticket_invoices.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"code": 0, "total": total, "invoices": docs}

@router.get("/{invoice_id}")
async def get_ticket_invoice(request: Request, invoice_id: str):
    org_id = _org_id(request)
    query = {"invoice_id": invoice_id}
    if org_id:
        query["organization_id"] = org_id
    doc = await db.ticket_invoices.find_one(query, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket invoice not found")
    return {"code": 0, "invoice": doc}

# ========================= PDF ENDPOINT =========================

@router.get("/{invoice_id}/pdf")
async def get_ticket_invoice_pdf(request: Request, invoice_id: str):
    """Generate and download GST-compliant ticket invoice PDF.
    Reuses the same PDF generator as invoices_enhanced."""
    from services.pdf_service import generate_gst_invoice_html
    from weasyprint import HTML

    org_id = _org_id(request)
    invoice = await db.ticket_invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": org_id} if org_id else {"invoice_id": invoice_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Ticket invoice not found")

    # Line items are embedded in ticket_invoices
    line_items = invoice.get("line_items", [])

    # Get organization settings
    org_query = {"organization_id": org_id} if org_id else {}
    org_settings = await db["organizations"].find_one(org_query, {"_id": 0}) or {}
    if not org_settings:
        org_settings = await db["organization_settings"].find_one({}, {"_id": 0}) or {}

    # Bank details
    bank_details = None
    if org_id:
        bank_config = await db["organizations"].find_one(
            {"organization_id": org_id},
            {"_id": 0, "bank_name": 1, "bank_account_number": 1, "bank_ifsc": 1,
             "bank_account_type": 1, "upi_id": 1}
        )
        if bank_config and bank_config.get("bank_account_number"):
            bank_details = {
                "bank_name": bank_config.get("bank_name", ""),
                "account_number": bank_config.get("bank_account_number", ""),
                "ifsc_code": bank_config.get("bank_ifsc", ""),
                "account_type": bank_config.get("bank_account_type", "Current"),
                "upi_id": bank_config.get("upi_id", "")
            }

    try:
        html_content = generate_gst_invoice_html(
            invoice=invoice,
            line_items=line_items,
            org_settings=org_settings,
            irn_data=None,
            bank_details=bank_details,
            payment_qr_url=None,
            survey_qr_url=None
        )

        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        customer_name_safe = (invoice.get("customer_name", "") or "Customer").replace(" ", "_")[:30]
        filename = f"TKT-{invoice.get('invoice_number', invoice_id)}-{customer_name_safe}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"PDF generation failed for ticket invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

# ========================= PAYMENTS ENDPOINTS =========================

@router.get("/{invoice_id}/payments")
async def get_ticket_invoice_payments(request: Request, invoice_id: str):
    """Get all payments for a ticket invoice"""
    org_id = _org_id(request)
    invoice = await db.ticket_invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": org_id} if org_id else {"invoice_id": invoice_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Ticket invoice not found")

    payments = await db.invoice_payments.find(
        {"invoice_id": invoice_id}, {"_id": 0}
    ).sort("payment_date", -1).to_list(100)

    return {
        "code": 0,
        "payments": payments,
        "total_paid": invoice.get("amount_paid", 0),
        "balance_due": invoice.get("balance_due", 0)
    }

@router.post("/{invoice_id}/payments")
async def record_ticket_invoice_payment(request: Request, invoice_id: str, payment: PaymentCreate):
    """Record a payment against a ticket invoice.
    Updates balance_due, posts journal entry (DR Cash/Bank, CR Accounts Receivable)."""
    org_id = _org_id(request)
    invoice = await db.ticket_invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": org_id} if org_id else {"invoice_id": invoice_id}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Ticket invoice not found")

    if invoice.get("status") in ["void", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot record payment for {invoice.get('status')} invoice")

    if invoice.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Invoice is already fully paid")

    balance_due = invoice.get("balance_due", invoice.get("grand_total", 0))
    if payment.amount > balance_due:
        raise HTTPException(status_code=400, detail=f"Payment amount ({payment.amount}) exceeds balance due ({balance_due})")

    payment_id = _generate_id("PAY")
    now = datetime.now(timezone.utc).isoformat()
    payment_date = payment.payment_date or datetime.now(timezone.utc).date().isoformat()

    # 1. Create payment record
    payment_doc = {
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "organization_id": org_id,
        "customer_id": invoice.get("customer_id"),
        "invoice_number": invoice.get("invoice_number"),
        "amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "reference_number": payment.reference_number,
        "payment_date": payment_date,
        "notes": payment.notes,
        "source": "ticket_invoice",
        "created_time": now
    }
    await db.invoice_payments.insert_one(payment_doc)
    payment_doc.pop("_id", None)

    # 2. Update invoice balance_due and status
    new_amount_paid = (invoice.get("amount_paid", 0) or 0) + payment.amount
    new_balance = invoice.get("grand_total", 0) - new_amount_paid
    new_payment_status = "paid" if new_balance <= 0 else "partially_paid"

    update_fields = {
        "amount_paid": new_amount_paid,
        "balance_due": max(0, new_balance),
        "payment_status": new_payment_status,
        "updated_at": now
    }
    if new_payment_status == "paid":
        update_fields["paid_date"] = now

    await db.ticket_invoices.update_one({"invoice_id": invoice_id}, {"$set": update_fields})

    # 3. Post journal entry (DR Cash/Bank, CR Accounts Receivable)
    try:
        account_map = {
            "cash": "Cash", "upi": "Bank", "bank_transfer": "Bank",
            "card": "Bank", "cheque": "Bank", "online": "Bank"
        }
        debit_account = account_map.get(payment.payment_mode, "Cash")

        journal_entry = {
            "journal_entry_id": _generate_id("JE"),
            "organization_id": org_id,
            "date": payment_date,
            "reference_type": "ticket_invoice_payment",
            "reference_id": payment_id,
            "invoice_id": invoice_id,
            "description": f"Payment received for ticket invoice {invoice.get('invoice_number', invoice_id)}",
            "lines": [
                {"account": debit_account, "debit": payment.amount, "credit": 0,
                 "description": f"Payment via {payment.payment_mode}"},
                {"account": "Accounts Receivable", "debit": 0, "credit": payment.amount,
                 "description": f"Invoice {invoice.get('invoice_number', invoice_id)}"}
            ],
            "total_debit": payment.amount,
            "total_credit": payment.amount,
            "status": "posted",
            "created_time": now
        }
        await db.journal_entries.insert_one(journal_entry)
        journal_entry.pop("_id", None)
        logger.info(f"Journal entry {journal_entry['journal_entry_id']} posted for payment {payment_id}")
    except Exception as e:
        logger.error(f"Journal entry failed for payment {payment_id}: {e}")
        journal_entry = None

    return {
        "code": 0,
        "message": "Payment recorded",
        "payment": payment_doc,
        "new_balance": max(0, new_balance),
        "new_status": new_payment_status,
        "journal_entry_id": journal_entry["journal_entry_id"] if journal_entry else None
    }
