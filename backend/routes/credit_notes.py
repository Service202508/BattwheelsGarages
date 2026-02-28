"""
Credit Notes Routes
==================
GST-compliant credit note management.
POST /api/v1/credit-notes/ — Create credit note against an invoice
GET  /api/v1/credit-notes/ — List credit notes (org-scoped)
GET  /api/v1/credit-notes/{credit_note_id} — Get single credit note
GET  /api/v1/credit-notes/{credit_note_id}/pdf — Download PDF
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from io import BytesIO

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from utils.audit_log import log_financial_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/credit-notes", tags=["credit-notes"])


def get_db():
    from server import db
    return db


# ========================= MODELS =========================

class CreditNoteLineItem(BaseModel):
    name: str
    description: str = ""
    hsn_sac: str = ""
    quantity: float = 1
    rate: float = 0
    tax_rate: float = 18
    amount: float = 0
    tax_amount: float = 0
    total: float = 0


class CreateCreditNoteRequest(BaseModel):
    original_invoice_id: str
    reason: str
    line_items: list[CreditNoteLineItem]
    notes: str = ""
    credit_note_date: str = ""


# ========================= HELPERS =========================

async def get_next_cn_number(db, organization_id: str) -> str:
    """Atomic sequence number via sequences collection. Format: CN-00001"""
    result = await db.sequences.find_one_and_update(
        {"sequence_id": f"credit_note_{organization_id}", "organization_id": organization_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    seq = result["seq"]
    return f"CN-{seq:05d}"


def compute_line_totals(item: dict, gst_treatment: str, original_cgst_rate: float, original_sgst_rate: float, original_igst_rate: float) -> dict:
    """Compute amount, tax, and total for a line item, matching original invoice GST treatment."""
    qty = float(item.get("quantity", 1))
    rate = float(item.get("rate", 0))
    amount = round(qty * rate, 2)
    tax_rate = float(item.get("tax_rate", 18))
    tax_amount = round(amount * tax_rate / 100, 2)
    total = round(amount + tax_amount, 2)
    
    # Split tax based on GST treatment
    if gst_treatment == "igst":
        cgst_amount = 0
        sgst_amount = 0
        igst_amount = tax_amount
    else:
        cgst_amount = round(tax_amount / 2, 2)
        sgst_amount = tax_amount - cgst_amount
        igst_amount = 0
    
    return {
        **item,
        "quantity": qty,
        "rate": rate,
        "amount": amount,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "cgst_amount": cgst_amount,
        "sgst_amount": sgst_amount,
        "igst_amount": igst_amount,
        "total": total
    }


# ========================= ROUTES =========================

@router.post("/")
async def create_credit_note(request: Request, body: CreateCreditNoteRequest):
    """Create a credit note against an existing invoice."""
    org_id = getattr(request.state, "tenant_org_id", None)
    user_id = getattr(request.state, "tenant_user_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")

    db = get_db()

    # Period lock check
    from utils.period_lock import enforce_period_lock
    cn_date = body.credit_note_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await enforce_period_lock(db, org_id, cn_date)

    # 1. Fetch original invoice
    invoice = await db.invoices_enhanced.find_one(
        {"invoice_id": body.original_invoice_id, "organization_id": org_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # 2. Validation: Cannot CN a draft invoice
    if invoice.get("status") == "draft":
        raise HTTPException(status_code=400, detail="Cannot raise a credit note against a DRAFT invoice")
    
    # 3. Check total credited so far
    existing_cns = await db.credit_notes.find(
        {
            "organization_id": org_id,
            "original_invoice_id": body.original_invoice_id,
            "status": {"$ne": "cancelled"}
        },
        {"_id": 0, "total": 1}
    ).to_list(100)
    total_already_credited = sum(cn.get("total", 0) for cn in existing_cns)
    invoice_total = float(invoice.get("grand_total", 0) or invoice.get("total", 0) or 0)
    
    # 4. Determine GST treatment from original invoice
    cgst_on_invoice = float(invoice.get("cgst_amount", 0) or 0)
    sgst_on_invoice = float(invoice.get("sgst_amount", 0) or 0)
    igst_on_invoice = float(invoice.get("igst_amount", 0) or 0)
    gst_treatment = "igst" if igst_on_invoice > 0 and cgst_on_invoice == 0 else "cgst_sgst"
    
    # 5. Compute line items
    computed_items = []
    for item in body.line_items:
        computed = compute_line_totals(
            item.model_dump(), gst_treatment,
            cgst_on_invoice, sgst_on_invoice, igst_on_invoice
        )
        computed_items.append(computed)
    
    subtotal = round(sum(i["amount"] for i in computed_items), 2)
    total_cgst = round(sum(i["cgst_amount"] for i in computed_items), 2)
    total_sgst = round(sum(i["sgst_amount"] for i in computed_items), 2)
    total_igst = round(sum(i["igst_amount"] for i in computed_items), 2)
    gst_amount = round(total_cgst + total_sgst + total_igst, 2)
    total = round(subtotal + gst_amount, 2)
    
    # 6. Validate: CN cannot exceed original invoice value
    if total > invoice_total:
        raise HTTPException(
            status_code=400,
            detail=f"Credit note total ({total}) exceeds original invoice total ({invoice_total})"
        )
    
    # 7. Validate: Cannot exceed remaining creditable amount
    remaining = round(invoice_total - total_already_credited, 2)
    if total > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Credit note total ({total}) exceeds remaining creditable amount ({remaining}). Already credited: {total_already_credited}"
        )
    
    # 8. Generate credit note number
    cn_number = await get_next_cn_number(db, org_id)
    cn_id = f"cn_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    # 9. Determine if invoice is paid or outstanding
    amount_paid = float(invoice.get("amount_paid", 0) or 0)
    balance_due = float(invoice.get("balance_due", invoice_total - amount_paid))
    is_paid = balance_due <= 0 or invoice.get("status") == "paid"
    
    # 10. Build the credit note document
    credit_note = {
        "credit_note_id": cn_id,
        "credit_note_number": cn_number,
        "organization_id": org_id,
        "original_invoice_id": body.original_invoice_id,
        "original_invoice_number": invoice.get("invoice_number", ""),
        "customer_name": invoice.get("customer_name", ""),
        "customer_id": invoice.get("customer_id", ""),
        "customer_gstin": invoice.get("customer_gstin", invoice.get("customer", {}).get("gstin", "")),
        "reason": body.reason,
        "notes": body.notes,
        "line_items": computed_items,
        "subtotal": subtotal,
        "cgst_amount": total_cgst,
        "sgst_amount": total_sgst,
        "igst_amount": total_igst,
        "gst_amount": gst_amount,
        "gst_treatment": gst_treatment,
        "total": total,
        "status": "issued",
        "invoice_was_paid": is_paid,
        "place_of_supply": invoice.get("place_of_supply", ""),
        "place_of_supply_code": invoice.get("place_of_supply_code", ""),
        "created_at": now,
        "updated_at": now,
        "created_by": user_id or "",
    }
    
    await db.credit_notes.insert_one(credit_note)
    credit_note.pop("_id", None)
    
    # 11. Post journal entries via double-entry service
    journal_result = await post_credit_note_journal(db, org_id, credit_note, is_paid, user_id or "")
    
    # 12. Update invoice with credit note reference
    await db.invoices_enhanced.update_one(
        {"invoice_id": body.original_invoice_id, "organization_id": org_id},
        {
            "$push": {"credit_notes": {"credit_note_id": cn_id, "credit_note_number": cn_number, "amount": total, "date": now}},
            "$inc": {"total_credits_applied": total}
        }
    )
    
    logger.info(f"Credit note {cn_number} created for invoice {invoice.get('invoice_number')} in org {org_id}")
    
    # Audit log: credit_note CREATE
    await log_financial_action(
        org_id=org_id, action="CREATE", entity_type="credit_note",
        entity_id=cn_id, request=request,
        before_snapshot=None, after_snapshot=credit_note,
    )
    
    return {
        "status": "success",
        "credit_note": credit_note,
        "journal_entry": journal_result
    }


@router.get("/")
async def list_credit_notes(request: Request, status: Optional[str] = None, invoice_id: Optional[str] = None):
    """List credit notes for the organization."""
    org_id = getattr(request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
    db = get_db()
    query = {"organization_id": org_id}
    if status:
        query["status"] = status
    if invoice_id:
        query["original_invoice_id"] = invoice_id
    
    credit_notes = await db.credit_notes.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return {"credit_notes": credit_notes, "total": len(credit_notes)}


@router.get("/{credit_note_id}")
async def get_credit_note(request: Request, credit_note_id: str):
    """Get a single credit note."""
    org_id = getattr(request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
    db = get_db()
    cn = await db.credit_notes.find_one(
        {"credit_note_id": credit_note_id, "organization_id": org_id},
        {"_id": 0}
    )
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    
    return cn


@router.get("/{credit_note_id}/pdf")
async def download_credit_note_pdf(request: Request, credit_note_id: str):
    """Generate and download credit note PDF."""
    org_id = getattr(request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
    db = get_db()
    cn = await db.credit_notes.find_one(
        {"credit_note_id": credit_note_id, "organization_id": org_id},
        {"_id": 0}
    )
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    
    # Fetch org settings for company info
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    
    pdf_bytes = generate_credit_note_pdf(cn, org)
    
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={cn['credit_note_number']}.pdf"}
    )


# ========================= JOURNAL POSTING =========================

async def post_credit_note_journal(db, org_id: str, cn: dict, is_paid: bool, user_id: str) -> dict:
    """
    Post journal entries for a credit note.
    
    If invoice outstanding (unpaid): Reverse AR, reverse GST payable, reduce revenue
        DEBIT:  Sales Revenue (subtotal)
        DEBIT:  GST Payable - CGST/SGST or IGST (tax amounts)
        CREDIT: Accounts Receivable (total)
    
    If invoice already paid: Create refund payable instead of reversing AR
        DEBIT:  Sales Revenue (subtotal)
        DEBIT:  GST Payable - CGST/SGST or IGST (tax amounts)
        CREDIT: Refund Payable (total)
    """
    from services.double_entry_service import DoubleEntryService, EntryType
    
    service = DoubleEntryService(db)
    await service.ensure_system_accounts(org_id)
    
    # Get accounts (Refund Payable 2410 is created by ensure_system_accounts)
    refund_account = await service.get_account_by_code(org_id, "2410")
    sales_account = await service.get_account_by_code(org_id, "4100")
    ar_account = await service.get_account_by_code(org_id, "1100")
    cgst_account = await service.get_account_by_code(org_id, "2210")
    sgst_account = await service.get_account_by_code(org_id, "2220")
    igst_account = await service.get_account_by_code(org_id, "2230")
    
    lines = []
    
    # DEBIT: Sales Revenue (reduce revenue)
    if cn["subtotal"] > 0:
        lines.append({
            "account_id": sales_account["account_id"],
            "debit_amount": cn["subtotal"],
            "credit_amount": 0,
            "description": f"CN {cn['credit_note_number']} - Revenue reversal for {cn['original_invoice_number']}"
        })
    
    # DEBIT: GST Payable (reverse tax liability)
    if cn["gst_treatment"] == "igst":
        if cn["igst_amount"] > 0 and igst_account:
            lines.append({
                "account_id": igst_account["account_id"],
                "debit_amount": cn["igst_amount"],
                "credit_amount": 0,
                "description": f"CN {cn['credit_note_number']} - IGST reversal"
            })
    else:
        if cn["cgst_amount"] > 0 and cgst_account:
            lines.append({
                "account_id": cgst_account["account_id"],
                "debit_amount": cn["cgst_amount"],
                "credit_amount": 0,
                "description": f"CN {cn['credit_note_number']} - CGST reversal"
            })
        if cn["sgst_amount"] > 0 and sgst_account:
            lines.append({
                "account_id": sgst_account["account_id"],
                "debit_amount": cn["sgst_amount"],
                "credit_amount": 0,
                "description": f"CN {cn['credit_note_number']} - SGST reversal"
            })
    
    # CREDIT: AR reversal (outstanding) or Refund Payable (paid)
    credit_account = refund_account if is_paid else ar_account
    credit_label = "Refund payable" if is_paid else "AR reversal"
    
    lines.append({
        "account_id": credit_account["account_id"],
        "debit_amount": 0,
        "credit_amount": cn["total"],
        "description": f"CN {cn['credit_note_number']} - {credit_label} for {cn['original_invoice_number']}"
    })
    
    cn_date = (cn.get("credit_note_date") or cn.get("date") or 
              cn.get("created_at", datetime.now(timezone.utc).isoformat()))[:10]
    
    success, msg, entry = await service.create_journal_entry(
        organization_id=org_id,
        entry_date=cn_date,
        description=f"Credit Note {cn['credit_note_number']} against {cn['original_invoice_number']} - {cn['reason']}",
        lines=lines,
        entry_type=EntryType.SALES,
        source_document_id=cn["credit_note_id"],
        source_document_type="credit_note",
        created_by=user_id
    )
    
    if not success:
        logger.error(f"Failed to post journal for CN {cn['credit_note_number']}: {msg}")
        return {"posted": False, "message": msg}
    
    return {"posted": True, "message": msg, "entry_id": entry.get("entry_id") if entry else None}


# ========================= PDF GENERATION =========================

def generate_credit_note_pdf(cn: dict, org: dict = None) -> bytes:
    """Generate a GST-compliant Credit Note PDF using WeasyPrint."""
    company = {}
    if org:
        settings = org.get("settings", {})
        company = {
            "name": org.get("name", ""),
            "address": settings.get("address", ""),
            "city": settings.get("city", ""),
            "state": settings.get("state", ""),
            "pincode": settings.get("pincode", ""),
            "gstin": settings.get("gstin", ""),
            "phone": settings.get("phone", ""),
            "email": settings.get("email", ""),
        }
    
    if not company.get("name"):
        company = {
            "name": "Battwheels Garages Private Limited",
            "address": "127, First Floor, Udyog Vihar Phase 1",
            "city": "Gurugram",
            "state": "Haryana",
            "pincode": "122016",
            "gstin": "06AAQCB8091H1ZS",
            "phone": "",
            "email": "",
        }
    
    is_igst = cn.get("gst_treatment") == "igst"
    
    # Build line items HTML
    lines_html = ""
    for i, item in enumerate(cn.get("line_items", []), 1):
        tax_col = ""
        if is_igst:
            tax_col = f'<td style="text-align:right;">{item.get("tax_rate",18)}%</td><td style="text-align:right;">{item.get("igst_amount",0):,.2f}</td>'
        else:
            half_tax = item.get("tax_rate", 18) / 2
            tax_col = f'<td style="text-align:right;">{half_tax}%</td><td style="text-align:right;">{half_tax}%</td><td style="text-align:right;">{item.get("tax_amount",0):,.2f}</td>'
        
        lines_html += f'''<tr>
            <td>{i}</td>
            <td>{item.get("name","")}<br><small style="color:#666;">{item.get("description","")}</small></td>
            <td>{item.get("hsn_sac","")}</td>
            <td style="text-align:right;">{item.get("quantity",1)}</td>
            <td style="text-align:right;">{item.get("rate",0):,.2f}</td>
            {tax_col}
            <td style="text-align:right;font-weight:600;">{item.get("total",0):,.2f}</td>
        </tr>'''
    
    if is_igst:
        header_cols = '<th>IGST %</th><th>Tax Amt</th>'
    else:
        header_cols = '<th>CGST %</th><th>SGST %</th><th>Tax</th>'
    
    # Tax breakdown
    tax_rows = ""
    if is_igst:
        tax_rows = f'<tr><td>IGST</td><td style="text-align:right;">{cn.get("igst_amount",0):,.2f}</td></tr>'
    else:
        tax_rows = f'''
        <tr><td>CGST</td><td style="text-align:right;">{cn.get("cgst_amount",0):,.2f}</td></tr>
        <tr><td>SGST</td><td style="text-align:right;">{cn.get("sgst_amount",0):,.2f}</td></tr>'''
    
    html = f'''<!DOCTYPE html>
<html><head><style>
    @page {{ size: A4; margin: 15mm; }}
    body {{ font-family: Arial, sans-serif; font-size: 10px; color: #1a1a1a; }}
    .header {{ text-align: center; margin-bottom: 15px; }}
    .header h1 {{ margin: 0; font-size: 16px; }}
    .header p {{ margin: 2px 0; font-size: 10px; color: #444; }}
    .cn-title {{ text-align: center; font-size: 18px; font-weight: 700; color: #c00;
                 border: 2px solid #c00; padding: 6px 20px; display: inline-block; margin: 10px auto; letter-spacing: 2px; }}
    .cn-title-wrap {{ text-align: center; margin-bottom: 15px; }}
    .info-grid {{ display: flex; justify-content: space-between; margin-bottom: 12px; }}
    .info-box {{ width: 48%; }}
    .info-box h3 {{ font-size: 10px; text-transform: uppercase; color: #888; margin-bottom: 4px; }}
    table.items {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    table.items th {{ background: #f5f5f5; border: 1px solid #ddd; padding: 5px 6px; font-size: 9px; text-transform: uppercase; }}
    table.items td {{ border: 1px solid #ddd; padding: 4px 6px; font-size: 9px; }}
    .totals {{ width: 250px; margin-left: auto; margin-top: 8px; }}
    .totals td {{ padding: 3px 8px; font-size: 10px; }}
    .totals .grand {{ font-weight: 700; font-size: 12px; border-top: 2px solid #333; }}
    .reason {{ background: #fff8f0; border: 1px solid #f0d0a0; padding: 8px 12px; margin: 10px 0; border-radius: 3px; }}
    .reason strong {{ color: #b45300; }}
    .footer {{ margin-top: 30px; font-size: 8px; color: #999; text-align: center; }}
</style></head><body>

<div class="header">
    <h1>{company["name"]}</h1>
    <p>{company["address"]}, {company["city"]}, {company["state"]} - {company["pincode"]}</p>
    <p><b>GSTIN:</b> {company["gstin"]}</p>
</div>

<div class="cn-title-wrap"><div class="cn-title">CREDIT NOTE</div></div>

<div class="info-grid">
    <div class="info-box">
        <p><b>Credit Note #:</b> {cn.get("credit_note_number","")}</p>
        <p><b>Date:</b> {cn.get("created_at","")[:10]}</p>
        <p><b>Original Invoice:</b> {cn.get("original_invoice_number","")}</p>
        <p><b>Place of Supply:</b> {cn.get("place_of_supply","")} ({cn.get("place_of_supply_code","")})</p>
    </div>
    <div class="info-box">
        <h3>Credit To</h3>
        <p><b>{cn.get("customer_name","")}</b></p>
        <p><b>GSTIN:</b> {cn.get("customer_gstin","N/A")}</p>
    </div>
</div>

<div class="reason"><strong>Reason:</strong> {cn.get("reason","")}</div>

<table class="items">
    <thead><tr>
        <th>SN</th><th>Description</th><th>HSN/SAC</th><th>Qty</th><th>Rate</th>
        {header_cols}
        <th>Amount</th>
    </tr></thead>
    <tbody>{lines_html}</tbody>
</table>

<table class="totals">
    <tr><td>Sub Total</td><td style="text-align:right;">{cn.get("subtotal",0):,.2f}</td></tr>
    {tax_rows}
    <tr class="grand"><td>Total</td><td style="text-align:right;">{cn.get("total",0):,.2f}</td></tr>
</table>

{f'<p style="margin-top:8px;font-size:9px;color:#666;text-align:right;"><i>Notes: {cn.get("notes","")}</i></p>' if cn.get("notes") else ''}

<div class="footer">
    <p>This is a computer-generated credit note. | {company["name"]} | GSTIN: {company["gstin"]}</p>
</div>

</body></html>'''
    
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except Exception as e:
        logger.warning(f"WeasyPrint PDF generation failed: {e}, returning HTML")
        return html.encode("utf-8")
