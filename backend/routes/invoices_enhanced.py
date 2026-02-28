# Enhanced Invoices Module - Full Zoho Books Invoice Management
# Comprehensive invoicing with payment tracking, partial payments, credits, recurring, and GST compliance
# TENANT GUARD: Every MongoDB query in this file MUST include {"organization_id": org_id} — no exceptions.

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, UploadFile, File, Request, Depends
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import motor.motor_asyncio
import os
import uuid
import logging
import secrets
import base64
import io

# Import invoice validation
from services.invoice_validation import pre_save_validation, validate_and_correct_invoice

# Import tenant context for multi-tenant scoping
from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context

# Import double-entry posting hooks
from services.posting_hooks import post_invoice_journal_entry
from utils.audit_log import log_financial_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices-enhanced", tags=["Invoices Enhanced"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Use main collections with Zoho-synced data
invoices_collection = db["invoices"]
invoice_line_items_collection = db["invoice_line_items"]
invoice_payments_collection = db["invoice_payments"]
invoice_settings_collection = db["invoice_settings"]
invoice_templates_collection = db["invoice_templates"]
invoice_history_collection = db["invoice_history"]
invoice_comments_collection = db["invoice_comments"]
invoice_attachments_collection = db["invoice_attachments"]
invoice_share_links_collection = db["invoice_share_links"]
contacts_collection = db["contacts"]
items_collection = db["items"]
recurring_invoices_collection = db["recurring_invoices"]

# Multi-tenant helpers (Phase F migration - using TenantContext)
async def get_org_id(request: Request) -> str:
    """Get organization ID from request for multi-tenant scoping.
    Raises 403 if org context cannot be resolved — queries MUST be scoped.
    """
    try:
        ctx = await optional_tenant_context(request)
        if ctx and ctx.org_id:
            return ctx.org_id
    except Exception:
        pass
    raise HTTPException(status_code=403, detail="Organization context required")

def org_query(org_id: str, base_query: dict = None) -> dict:
    """Add org_id to query — org_id is always required."""
    query = base_query or {}
    query["organization_id"] = org_id
    return query

# Constants
MAX_ATTACHMENTS_PER_INVOICE = 5
MAX_ATTACHMENT_SIZE_MB = 10

# Tax rates mapping
GST_RATES = {
    "0": 0, "5": 5, "12": 12, "18": 18, "28": 28
}

# Invoice statuses
INVOICE_STATUSES = ["draft", "sent", "viewed", "partially_paid", "paid", "overdue", "void", "written_off"]

# ========================= PYDANTIC MODELS =========================

class LineItem(BaseModel):
    item_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    hsn_sac_code: str = ""
    quantity: float = Field(default=1, gt=0)
    unit: str = "pcs"
    rate: float = Field(..., ge=0)
    discount_type: str = "percentage"  # percentage, amount
    discount_value: float = 0
    tax_type: str = "gst"  # gst, igst, none
    tax_rate: float = 18
    account_id: str = ""
    # Computed fields
    amount: float = 0
    discount_amount: float = 0
    tax_amount: float = 0
    total: float = 0

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    payment_mode: str = "cash"  # cash, bank_transfer, cheque, card, upi, online
    reference_number: str = ""
    payment_date: str = ""
    bank_charges: float = 0
    notes: str = ""
    deposit_to_account: str = ""

class InvoiceCreate(BaseModel):
    # Contact
    customer_id: str = Field(..., min_length=1)
    # Reference
    reference_number: str = ""
    salesorder_id: Optional[str] = None
    estimate_id: Optional[str] = None
    # Dates
    invoice_date: str = ""
    due_date: str = ""
    payment_terms: int = 30
    # Line items
    line_items: List[LineItem] = []
    # Discount
    discount_type: str = "percentage"  # percentage, amount
    discount_value: float = 0
    # Shipping
    shipping_charge: float = 0
    # Tax adjustment
    adjustment: float = 0
    adjustment_description: str = ""
    # GST
    place_of_supply: str = ""
    is_inclusive_tax: bool = False
    reverse_charge: bool = False
    # Additional
    customer_notes: str = ""
    terms_conditions: str = ""
    template_id: str = ""
    # Attachments
    attachment_names: List[str] = []
    # Custom fields
    custom_fields: Dict[str, Any] = {}
    # Email options
    send_email: bool = False
    email_to: List[str] = []

class InvoiceUpdate(BaseModel):
    reference_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    payment_terms: Optional[int] = None
    line_items: Optional[List[LineItem]] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    shipping_charge: Optional[float] = None
    adjustment: Optional[float] = None
    adjustment_description: Optional[str] = None
    place_of_supply: Optional[str] = None
    customer_notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class RecurringInvoiceCreate(BaseModel):
    customer_id: str
    profile_name: str = ""
    start_date: str = ""
    end_date: str = ""
    repeat_every: int = 1
    repeat_unit: str = "month"  # day, week, month, year
    payment_terms: int = 30
    line_items: List[LineItem] = []
    discount_type: str = "percentage"
    discount_value: float = 0
    shipping_charge: float = 0
    customer_notes: str = ""
    terms_conditions: str = ""
    send_email: bool = True
    create_days_before: int = 0  # Create N days before due

class BulkActionRequest(BaseModel):
    invoice_ids: List[str]
    action: str  # send, void, mark_paid, delete

class InvoiceCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = True  # Internal notes vs customer-visible

class InvoiceShareConfig(BaseModel):
    expiry_days: int = 30
    allow_payment: bool = True
    password_protected: bool = False
    password: str = ""

# ========================= HELPER FUNCTIONS =========================

def generate_share_token() -> str:
    """Generate a secure share token for public links"""
    return secrets.token_urlsafe(32)

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def round_currency(value: float) -> float:
    """Round to 2 decimal places"""
    return round(value, 2)

def calculate_line_item(item: LineItem, is_igst: bool = False, is_inclusive: bool = False) -> dict:
    """Calculate line item totals"""
    quantity = item.quantity
    rate = item.rate
    
    # Calculate base amount
    amount = quantity * rate
    
    # Calculate discount
    if item.discount_type == "percentage":
        discount_amount = amount * (item.discount_value / 100)
    else:
        discount_amount = item.discount_value
    
    amount_after_discount = amount - discount_amount
    
    # Calculate tax
    tax_rate = item.tax_rate if item.tax_type != "none" else 0
    
    if is_inclusive:
        # Extract tax from amount
        tax_amount = amount_after_discount - (amount_after_discount / (1 + tax_rate / 100))
        taxable_amount = amount_after_discount - tax_amount
    else:
        # Add tax to amount
        taxable_amount = amount_after_discount
        tax_amount = taxable_amount * (tax_rate / 100)
    
    total = taxable_amount + tax_amount
    
    # Split GST into CGST/SGST or IGST
    if is_igst:
        igst_amount = tax_amount
        cgst_amount = 0
        sgst_amount = 0
    else:
        igst_amount = 0
        cgst_amount = tax_amount / 2
        sgst_amount = tax_amount / 2
    
    return {
        "item_id": item.item_id,
        "name": item.name,
        "description": item.description,
        "hsn_sac_code": item.hsn_sac_code,
        "quantity": quantity,
        "unit": item.unit,
        "rate": round_currency(rate),
        "discount_type": item.discount_type,
        "discount_value": item.discount_value,
        "discount_amount": round_currency(discount_amount),
        "tax_type": item.tax_type,
        "tax_rate": tax_rate,
        "taxable_amount": round_currency(taxable_amount),
        "cgst_rate": tax_rate / 2 if not is_igst else 0,
        "cgst_amount": round_currency(cgst_amount),
        "sgst_rate": tax_rate / 2 if not is_igst else 0,
        "sgst_amount": round_currency(sgst_amount),
        "igst_rate": tax_rate if is_igst else 0,
        "igst_amount": round_currency(igst_amount),
        "tax_amount": round_currency(tax_amount),
        "amount": round_currency(amount),
        "total": round_currency(total),
        "account_id": item.account_id
    }

def calculate_invoice_totals(line_items: List[dict], discount_type: str, discount_value: float, 
                             shipping_charge: float, adjustment: float, is_inclusive: bool = False) -> dict:
    """Calculate invoice-level totals"""
    # Sum line item totals
    sub_total = sum(item["amount"] for item in line_items)
    total_discount = sum(item["discount_amount"] for item in line_items)
    taxable_total = sum(item["taxable_amount"] for item in line_items)
    total_cgst = sum(item.get("cgst_amount", 0) for item in line_items)
    total_sgst = sum(item.get("sgst_amount", 0) for item in line_items)
    total_igst = sum(item.get("igst_amount", 0) for item in line_items)
    total_tax = sum(item["tax_amount"] for item in line_items)
    
    # Calculate invoice-level discount
    if discount_type == "percentage":
        invoice_discount = (sub_total - total_discount) * (discount_value / 100)
    else:
        invoice_discount = discount_value
    
    # Calculate grand total
    grand_total = taxable_total + total_tax - invoice_discount + shipping_charge + adjustment
    
    return {
        "sub_total": round_currency(sub_total),
        "item_discount": round_currency(total_discount),
        "invoice_discount": round_currency(invoice_discount),
        "total_discount": round_currency(total_discount + invoice_discount),
        "taxable_amount": round_currency(taxable_total - invoice_discount),
        "cgst_total": round_currency(total_cgst),
        "sgst_total": round_currency(total_sgst),
        "igst_total": round_currency(total_igst),
        "tax_total": round_currency(total_tax),
        "shipping_charge": round_currency(shipping_charge),
        "adjustment": round_currency(adjustment),
        "grand_total": round_currency(grand_total),
        "balance_due": round_currency(grand_total)  # Initial balance
    }

async def get_next_invoice_number() -> str:
    """Generate next invoice number based on settings"""
    settings = await invoice_settings_collection.find_one({"type": "numbering"})
    if not settings:
        settings = {
            "type": "numbering",
            "prefix": "INV-",
            "next_number": 1,
            "padding": 5,
            "suffix": ""
        }
        await invoice_settings_collection.insert_one(settings)
    
    number = str(settings["next_number"]).zfill(settings.get("padding", 5))
    invoice_number = f"{settings.get('prefix', 'INV-')}{number}{settings.get('suffix', '')}"
    
    await invoice_settings_collection.update_one(
        {"type": "numbering"},
        {"$inc": {"next_number": 1}}
    )
    
    return invoice_number

async def add_invoice_history(invoice_id: str, action: str, details: str, user_id: str = ""):
    """Add entry to invoice history"""
    history_entry = {
        "history_id": generate_id("HIST"),
        "invoice_id": invoice_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await invoice_history_collection.insert_one(history_entry)

async def update_contact_balance(customer_id: str):
    """Update contact's outstanding balance"""
    pipeline = [
        {"$match": {"customer_id": customer_id, "status": {"$nin": ["draft", "void"]}}},
        {"$group": {
            "_id": None,
            "total_invoiced": {"$sum": "$grand_total"},
            "total_outstanding": {"$sum": "$balance_due"}
        }}
    ]
    
    result = await invoices_collection.aggregate(pipeline).to_list(1)
    if result:
        await contacts_collection.update_one(
            {"contact_id": customer_id},
            {"$set": {
                "outstanding_receivable": result[0].get("total_outstanding", 0),
                "total_invoiced": result[0].get("total_invoiced", 0),
                "updated_time": datetime.now(timezone.utc).isoformat()
            }}
        )

async def update_invoice_status(invoice_id: str):
    """Update invoice status based on payments and dates"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        return
    
    balance = invoice.get("balance_due", 0)
    grand_total = invoice.get("grand_total", 0)
    due_date = invoice.get("due_date", "")
    current_status = invoice.get("status", "draft")
    
    if current_status in ["void", "draft"]:
        return
    
    # Calculate new status
    if balance <= 0:
        new_status = "paid"
    elif balance < grand_total:
        new_status = "partially_paid"
    elif due_date:
        try:
            due = datetime.fromisoformat(due_date.replace('Z', '+00:00')).date()
            if due < datetime.now(timezone.utc).date():
                new_status = "overdue"
            else:
                new_status = "sent"
        except:
            new_status = "sent"
    else:
        new_status = "sent"
    
    if new_status != current_status:
        await invoices_collection.update_one(
            {"invoice_id": invoice_id},
            {"$set": {"status": new_status, "updated_time": datetime.now(timezone.utc).isoformat()}}
        )
        await add_invoice_history(invoice_id, "status_changed", f"Status changed from {current_status} to {new_status}")

def mock_send_email(to_emails: List[str], subject: str, body: str, attachment_name: str = ""):
    """Mock email sending"""
    logger.info(f"[MOCK EMAIL] To: {', '.join(to_emails)}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Attachment: {attachment_name}")
    return True

def mock_generate_pdf(invoice: dict) -> bytes:
    """Mock PDF generation"""
    logger.info(f"[MOCK PDF] Generating invoice PDF for {invoice.get('invoice_number')}")
    return b"PDF_CONTENT_MOCK"


async def update_item_stock_for_invoice(invoice_id: str, reverse: bool = False):
    """Update item stock when invoice is sent/voided
    
    Args:
        invoice_id: The invoice ID
        reverse: If True, add stock back (for voiding). If False, deduct stock.
    """
    # Get line items
    line_items = await invoice_line_items_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).to_list(100)
    
    for item in line_items:
        item_id = item.get("item_id")
        if not item_id:
            continue
        
        quantity = item.get("quantity", 0)
        if reverse:
            quantity = -quantity  # Add back for void
        
        # Get current item
        db_item = await items_collection.find_one({"item_id": item_id})
        if not db_item:
            continue
        
        # Only update stock for inventory items
        item_type = db_item.get("item_type", "inventory")
        if item_type not in ["inventory", "goods"]:
            continue
        
        current_stock = db_item.get("stock_on_hand", db_item.get("quantity", 0)) or 0
        new_stock = current_stock - quantity  # Deduct (or add if reversed)
        
        await items_collection.update_one(
            {"item_id": item_id},
            {"$set": {
                "stock_on_hand": new_stock,
                "quantity": new_stock,
                "total_stock": new_stock,
                "updated_time": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"[STOCK] Item {item_id}: {current_stock} -> {new_stock} (invoice {invoice_id})")


# ========================= SETTINGS ENDPOINTS =========================

@router.get("/settings")
async def get_invoice_settings():
    """Get invoice module settings"""
    numbering = await invoice_settings_collection.find_one({"type": "numbering"}, {"_id": 0})
    defaults = await invoice_settings_collection.find_one({"type": "defaults"}, {"_id": 0})
    
    if not numbering:
        numbering = {"type": "numbering", "prefix": "INV-", "next_number": 1, "padding": 5, "suffix": ""}
    if not defaults:
        defaults = {
            "type": "defaults",
            "payment_terms": 30,
            "default_tax_rate": 18,
            "gst_treatment": "registered",
            "auto_generate_number": True,
            "enable_recurring": True,
            "enable_partial_payments": True,
            "default_template": ""
        }
    
    return {"code": 0, "settings": {"numbering": numbering, "defaults": defaults}}

@router.put("/settings")
async def update_invoice_settings(settings: dict):
    """Update invoice settings"""
    for key in ["numbering", "defaults"]:
        if key in settings:
            await invoice_settings_collection.update_one(
                {"type": key},
                {"$set": settings[key]},
                upsert=True
            )
    return {"code": 0, "message": "Settings updated"}

# ========================= SUMMARY (Must be before /{invoice_id}) =========================

@router.get("/summary")
async def get_invoices_summary(request: Request, period: str = "all"):
    """Get invoices summary statistics — scoped to the authenticated organisation"""
    org_id = await get_org_id(request)
    query = org_query(org_id, {"status": {"$ne": "void"}})
    
    if period == "this_month":
        first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        query["invoice_date"] = {"$gte": first_of_month}
    elif period == "this_year":
        first_of_year = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        query["invoice_date"] = {"$gte": first_of_year}
    
    total = await invoices_collection.count_documents(query)
    draft = await invoices_collection.count_documents({**query, "status": "draft"})
    sent = await invoices_collection.count_documents({**query, "status": "sent"})
    overdue = await invoices_collection.count_documents({**query, "status": "overdue"})
    partially_paid = await invoices_collection.count_documents({**query, "status": "partially_paid"})
    paid = await invoices_collection.count_documents({**query, "status": "paid"})
    
    # Aggregate totals
    pipeline = [
        {"$match": {**query}},
        {"$group": {
            "_id": None,
            "total_invoiced": {"$sum": "$grand_total"},
            "total_outstanding": {"$sum": "$balance_due"},
            "total_paid": {"$sum": {"$subtract": ["$grand_total", "$balance_due"]}}
        }}
    ]
    
    totals = await invoices_collection.aggregate(pipeline).to_list(1)
    values = totals[0] if totals else {"total_invoiced": 0, "total_outstanding": 0, "total_paid": 0}
    
    return {
        "code": 0,
        "summary": {
            "total_invoices": total,
            "draft": draft,
            "sent": sent,
            "overdue": overdue,
            "partially_paid": partially_paid,
            "paid": paid,
            "total_invoiced": round_currency(values.get("total_invoiced", 0)),
            "total_outstanding": round_currency(values.get("total_outstanding", 0)),
            "total_collected": round_currency(values.get("total_paid", 0)),
            "period": period
        }
    }

# ========================= REPORTS (Must be before /{invoice_id}) =========================

@router.get("/reports/aging")
async def get_aging_report():
    """Get receivables aging report"""
    today = datetime.now(timezone.utc).date()
    
    invoices = await invoices_collection.find(
        {"status": {"$in": ["sent", "overdue", "partially_paid"]}, "balance_due": {"$gt": 0}},
        {"_id": 0, "invoice_id": 1, "invoice_number": 1, "customer_id": 1, "customer_name": 1, 
         "due_date": 1, "grand_total": 1, "balance_due": 1}
    ).to_list(1000)
    
    aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    aged_invoices = {"current": [], "1_30": [], "31_60": [], "61_90": [], "over_90": []}
    
    for inv in invoices:
        due_date_str = inv.get("due_date", "")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
            days_overdue = (today - due_date).days
            balance = inv.get("balance_due", 0)
            
            if days_overdue <= 0:
                bucket = "current"
            elif days_overdue <= 30:
                bucket = "1_30"
            elif days_overdue <= 60:
                bucket = "31_60"
            elif days_overdue <= 90:
                bucket = "61_90"
            else:
                bucket = "over_90"
            
            aging[bucket] += balance
            aged_invoices[bucket].append({
                "invoice_number": inv.get("invoice_number"),
                "customer_name": inv.get("customer_name"),
                "balance_due": balance,
                "days_overdue": days_overdue
            })
        except:
            continue
    
    return {
        "code": 0,
        "report": {
            "totals": {k: round_currency(v) for k, v in aging.items()},
            "grand_total": round_currency(sum(aging.values())),
            "invoices": aged_invoices
        }
    }

@router.get("/reports/customer-wise")
async def get_customer_wise_report(limit: int = 20):
    """Get invoices report grouped by customer"""
    pipeline = [
        {"$match": {"status": {"$ne": "void"}}},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "invoice_count": {"$sum": 1},
            "total_invoiced": {"$sum": "$grand_total"},
            "total_outstanding": {"$sum": "$balance_due"}
        }},
        {"$sort": {"total_outstanding": -1}},
        {"$limit": limit}
    ]
    
    results = await invoices_collection.aggregate(pipeline).to_list(limit)
    
    return {
        "code": 0,
        "report": [
            {
                "customer_id": r["_id"],
                "customer_name": r.get("customer_name", "Unknown"),
                "invoice_count": r["invoice_count"],
                "total_invoiced": round_currency(r["total_invoiced"]),
                "total_outstanding": round_currency(r["total_outstanding"])
            }
            for r in results
        ]
    }

@router.get("/reports/monthly")
async def get_monthly_report(year: int = None):
    """Get monthly invoice report"""
    if not year:
        year = datetime.now(timezone.utc).year
    
    pipeline = [
        {"$match": {
            "status": {"$ne": "void"},
            "invoice_date": {
                "$gte": f"{year}-01-01",
                "$lte": f"{year}-12-31"
            }
        }},
        {"$addFields": {
            "month": {"$substr": ["$invoice_date", 5, 2]}
        }},
        {"$group": {
            "_id": "$month",
            "invoice_count": {"$sum": 1},
            "total_invoiced": {"$sum": "$grand_total"},
            "total_collected": {"$sum": {"$subtract": ["$grand_total", "$balance_due"]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    results = await invoices_collection.aggregate(pipeline).to_list(12)
    
    # Fill missing months
    months = {f"{i:02d}": {"invoice_count": 0, "total_invoiced": 0, "total_collected": 0} for i in range(1, 13)}
    for r in results:
        months[r["_id"]] = {
            "invoice_count": r["invoice_count"],
            "total_invoiced": round_currency(r["total_invoiced"]),
            "total_collected": round_currency(r["total_collected"])
        }
    
    return {
        "code": 0,
        "report": {
            "year": year,
            "months": months
        }
    }

# ========================= TEMPLATES (Must be before /{invoice_id}) =========================

@router.get("/templates")
async def list_invoice_templates():
    """List available invoice templates"""
    templates = await invoice_templates_collection.find({}, {"_id": 0}).to_list(50)
    
    if not templates:
        # Create default templates
        default_templates = [
            {"template_id": generate_id("TMPL"), "name": "Standard", "description": "Basic invoice layout", "is_default": True, "styles": {}},
            {"template_id": generate_id("TMPL"), "name": "Professional", "description": "Corporate style", "is_default": False, "styles": {}},
            {"template_id": generate_id("TMPL"), "name": "Modern", "description": "Modern minimal design", "is_default": False, "styles": {}}
        ]
        for tmpl in default_templates:
            await invoice_templates_collection.insert_one(tmpl)
        templates = default_templates
    
    return {"code": 0, "templates": templates}

# ========================= INVOICE CRUD =========================

@router.post("/")
async def create_invoice(invoice: InvoiceCreate, background_tasks: BackgroundTasks, request: Request = None):
    """Create a new invoice"""
    # Get org context for multi-tenant scoping
    org_id = await get_org_id(request) if request else None

    # Period lock check
    from utils.period_lock import enforce_period_lock
    inv_date = invoice.invoice_date or datetime.now(timezone.utc).date().isoformat()
    await enforce_period_lock(invoices_collection.database, org_id, inv_date)

    # Validate customer
    customer_query = org_query(org_id, {"contact_id": invoice.customer_id})
    customer = await contacts_collection.find_one(customer_query)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if customer.get("contact_type") == "vendor":
        raise HTTPException(status_code=400, detail="Cannot create invoice for vendor-only contact")
    
    invoice_id = generate_id("INV")
    invoice_number = await get_next_invoice_number()
    
    # Determine if IGST applies (different state)
    org_state = "DL"  # Organization state
    customer_state = invoice.place_of_supply or customer.get("place_of_supply", "")
    is_igst = customer_state and customer_state != org_state
    
    # Calculate line items
    calculated_items = []
    for item in invoice.line_items:
        calc_item = calculate_line_item(item, is_igst, invoice.is_inclusive_tax)
        calc_item["line_item_id"] = generate_id("LI")
        calc_item["invoice_id"] = invoice_id
        calc_item["organization_id"] = org_id
        calculated_items.append(calc_item)
    
    # Calculate invoice totals
    totals = calculate_invoice_totals(
        calculated_items,
        invoice.discount_type,
        invoice.discount_value,
        invoice.shipping_charge,
        invoice.adjustment,
        invoice.is_inclusive_tax
    )
    
    # Set dates
    invoice_date = invoice.invoice_date or datetime.now(timezone.utc).date().isoformat()
    if invoice.due_date:
        due_date = invoice.due_date
    else:
        due_date = (datetime.fromisoformat(invoice_date) + timedelta(days=invoice.payment_terms)).date().isoformat()
    
    # Build invoice document
    invoice_doc = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "customer_id": invoice.customer_id,
        "customer_name": customer.get("name", ""),
        "customer_email": customer.get("email", ""),
        "customer_phone": customer.get("phone", ""),
        "customer_gstin": customer.get("gstin", ""),
        "billing_address": None,  # Can be enhanced with address lookup
        "shipping_address": None,
        "reference_number": invoice.reference_number,
        "salesorder_id": invoice.salesorder_id,
        "estimate_id": invoice.estimate_id,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "payment_terms": invoice.payment_terms,
        "place_of_supply": invoice.place_of_supply or customer_state,
        "is_inclusive_tax": invoice.is_inclusive_tax,
        "reverse_charge": invoice.reverse_charge,
        "discount_type": invoice.discount_type,
        "discount_value": invoice.discount_value,
        "shipping_charge": invoice.shipping_charge,
        "adjustment": invoice.adjustment,
        "adjustment_description": invoice.adjustment_description,
        **totals,
        "amount_paid": 0,
        "credits_applied": 0,
        "write_off_amount": 0,
        "status": "draft",
        "customer_notes": invoice.customer_notes,
        "terms_conditions": invoice.terms_conditions,
        "template_id": invoice.template_id,
        "attachment_names": invoice.attachment_names,
        "custom_fields": invoice.custom_fields,
        "payment_count": 0,
        "last_payment_date": None,
        "is_sent": False,
        "sent_date": None,
        "viewed_date": None,
        "paid_date": None,
        "voided_date": None,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Add org_id for multi-tenant scoping
    invoice_doc["organization_id"] = org_id
    
    # P2: Validate and auto-correct calculations before save
    invoice_doc = pre_save_validation(invoice_doc)
    logger.info(f"Invoice {invoice_number} validated before save")
    
    await invoices_collection.insert_one(invoice_doc)
    
    # Store line items separately for reporting
    for item in calculated_items:
        await invoice_line_items_collection.insert_one(item)
    
    # Add to history
    await add_invoice_history(invoice_id, "created", f"Invoice {invoice_number} created")
    
    # Send email if requested
    if invoice.send_email and (invoice.email_to or customer.get("email")):
        recipients = invoice.email_to if invoice.email_to else [customer.get("email")]
        background_tasks.add_task(
            mock_send_email,
            recipients,
            f"Invoice {invoice_number} from Battwheels",
            f"Dear {customer.get('name')},\n\nPlease find attached Invoice {invoice_number} for ₹{totals['grand_total']:,.2f}.",
            f"Invoice_{invoice_number}.pdf"
        )
        
        # Update status to sent
        await invoices_collection.update_one(
            {"invoice_id": invoice_id},
            {"$set": {
                "status": "sent",
                "is_sent": True,
                "sent_date": datetime.now(timezone.utc).isoformat()
            }}
        )
        await add_invoice_history(invoice_id, "sent", f"Invoice emailed to {', '.join(recipients)}")
    
    # Update contact balance
    if invoice_doc["status"] != "draft":
        await update_contact_balance(invoice.customer_id)
    
    invoice_doc.pop("_id", None)
    # Remove _id from line items as well
    cleaned_items = []
    for item in calculated_items:
        item.pop("_id", None)
        cleaned_items.append(item)
    invoice_doc["line_items"] = cleaned_items

    # Audit log: invoice CREATE
    await log_financial_action(
        org_id=org_id, action="CREATE", entity_type="invoice",
        entity_id=invoice_id, request=request,
        before_snapshot=None, after_snapshot=invoice_doc,
    )

    return {"code": 0, "message": "Invoice created", "invoice": invoice_doc}

@router.get("")
@router.get("/")
async def list_invoices(request: Request, customer_id: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, overdue_only: bool = False, sort_by: str = "invoice_date", sort_order: str = "desc", page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List invoices with filters and standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    # Get org context for multi-tenant scoping
    org_id = await get_org_id(request)
    query = org_query(org_id, {})

    if customer_id:
        query["customer_id"] = customer_id

    if status:
        query["status"] = status
    elif not overdue_only:
        query["status"] = {"$ne": "void"}

    if overdue_only:
        query["status"] = "overdue"

    if search:
        query["$or"] = [
            {"invoice_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"reference_number": {"$regex": search, "$options": "i"}}
        ]

    if date_from:
        query["invoice_date"] = {"$gte": date_from}
    if date_to:
        if "invoice_date" in query:
            query["invoice_date"]["$lte"] = date_to
        else:
            query["invoice_date"] = {"$lte": date_to}

    total = await invoices_collection.count_documents(query)
    skip = (page - 1) * limit
    sort_dir = -1 if sort_order == "desc" else 1
    total_pages = math.ceil(total / limit) if total > 0 else 1

    invoices = await invoices_collection.find(query, {"_id": 0}).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)

    return {
        "data": invoices,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{invoice_id}")
async def get_invoice(request: Request, invoice_id: str):
    """Get invoice details with line items, payments, and history"""
    # Get org context for multi-tenant scoping
    org_id = await get_org_id(request)
    invoice_query = org_query(org_id, {"invoice_id": invoice_id})
    
    invoice = await invoices_collection.find_one(invoice_query, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get line items
    line_items = await invoice_line_items_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).to_list(100)
    invoice["line_items"] = line_items
    
    # Get payments
    payments = await invoice_payments_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).sort("payment_date", -1).to_list(50)
    invoice["payments"] = payments
    
    # Get payments from payments_received module
    payments_received = await db["payments_received"].find({
        "allocations.invoice_id": invoice_id,
        "status": {"$ne": "refunded"}
    }, {"_id": 0, "payment_id": 1, "payment_number": 1, "payment_date": 1, "amount": 1, "payment_mode": 1, "allocations": 1}).to_list(50)
    
    for pr in payments_received:
        for alloc in pr.get("allocations", []):
            if alloc.get("invoice_id") == invoice_id:
                pr["amount_applied"] = alloc.get("amount", 0)
                break
    invoice["payments_received"] = payments_received
    
    # Get available customer credits
    customer_credits = await db["customer_credits"].find({
        "customer_id": invoice.get("customer_id"),
        "status": "available"
    }, {"_id": 0}).to_list(50)
    invoice["available_credits"] = customer_credits
    invoice["total_available_credits"] = sum(c.get("amount", 0) for c in customer_credits)
    
    # Get history
    history = await invoice_history_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20).to_list(20)
    invoice["history"] = history
    
    return {"code": 0, "invoice": invoice}


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(request: Request, invoice_id: str):
    """
    Generate and download GST-compliant invoice PDF
    
    Business Rules (E-Invoice Compliance - 4A):
    - If org has e-invoicing ENABLED AND invoice is B2B AND IRN status is PENDING:
      Block PDF download and return error
    - If IRN is REGISTERED: Generate PDF with full IRN block
    - If B2C or e-invoicing DISABLED: Generate standard PDF without IRN block
    """
    from services.pdf_service import generate_gst_invoice_html
    from weasyprint import HTML
    
    # Get org context
    org_id = await get_org_id(request)
    
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get line items
    line_items = await invoice_line_items_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get organization settings
    org_query_filter = {"organization_id": org_id} if org_id else {}
    org_settings = await db["organizations"].find_one(org_query_filter, {"_id": 0}) or {}
    if not org_settings:
        org_settings = await db["organization_settings"].find_one({}, {"_id": 0}) or {}
    
    # ==================== E-INVOICE BUSINESS RULES (4A) ====================
    customer_gstin = invoice.get('customer_gstin', invoice.get('gst_no', ''))
    is_b2b = bool(customer_gstin and customer_gstin not in ['', 'URP', None])
    
    # Check E-Invoice configuration
    einvoice_config = None
    einvoice_enabled = False
    if org_id:
        einvoice_config = await db["einvoice_config"].find_one(
            {"organization_id": org_id}, 
            {"_id": 0}
        )
        einvoice_enabled = einvoice_config.get("enabled", False) if einvoice_config else False
    
    irn_status = invoice.get('irn_status', 'pending')
    has_irn = invoice.get('irn') and irn_status == 'registered'
    
    # Rule 4A: Block PDF if e-invoicing enabled, B2B invoice, and IRN not registered
    if einvoice_enabled and is_b2b and not has_irn:
        raise HTTPException(
            status_code=400,
            detail="IRN registration required before PDF can be generated. Generate IRN first from the invoice detail page."
        )
    
    # ==================== PREPARE IRN DATA (4B) ====================
    irn_data = None
    if has_irn:
        irn_data = {
            'irn': invoice.get('irn'),
            'ack_no': invoice.get('irn_ack_no'),
            'ack_date': invoice.get('irn_ack_date'),
            'signed_qr_code': invoice.get('irn_signed_qr')
        }
    
    # ==================== GET BANK DETAILS ====================
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
    
    # ==================== GET SURVEY QR CODE ====================
    survey_qr_url = None
    ticket_id = invoice.get("ticket_id")
    if ticket_id:
        ticket = await db["tickets"].find_one(
            {"ticket_id": ticket_id},
            {"_id": 0, "survey_token": 1}
        )
        if ticket and ticket.get("survey_token"):
            # Check if survey not yet completed
            review = await db["ticket_reviews"].find_one(
                {"survey_token": ticket["survey_token"]},
                {"_id": 0, "completed": 1}
            )
            if review and not review.get("completed"):
                # Build frontend URL from CORS_ORIGINS env var
                import os as _os
                frontend_url = _os.environ.get("CORS_ORIGINS", "").split(",")[0].strip()
                if not frontend_url:
                    frontend_url = "https://accounting-sprint2d.preview.emergentagent.com"
                survey_qr_url = f"{frontend_url}/survey/{ticket['survey_token']}"

    # ==================== GENERATE PDF ====================
    try:
        # Generate comprehensive GST-compliant HTML
        html_content = generate_gst_invoice_html(
            invoice=invoice,
            line_items=line_items,
            org_settings=org_settings,
            irn_data=irn_data,
            bank_details=bank_details,
            payment_qr_url=None,        # Can be enhanced with Razorpay QR
            survey_qr_url=survey_qr_url # Survey feedback QR code
        )
        
        # Generate PDF
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        # File naming per 4E spec: INV-{invoice_number}-{customer_name}.pdf
        customer_name_safe = (invoice.get('customer_name', '') or 'Customer').replace(' ', '_')[:30]
        filename = f"INV-{invoice.get('invoice_number', invoice_id)}-{customer_name_safe}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.put("/{invoice_id}")
async def update_invoice(invoice_id: str, update: InvoiceUpdate, request: Request = None):
    """Update invoice (only drafts can be fully edited)"""
    existing = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Period lock check — check both existing date and new date
    from utils.period_lock import enforce_period_lock
    org_id = existing.get("organization_id", "")
    await enforce_period_lock(invoices_collection.database, org_id, existing.get("invoice_date", ""))
    if update.invoice_date:
        await enforce_period_lock(invoices_collection.database, org_id, update.invoice_date)

    # Capture before_snapshot for audit (strip _id)
    before_snapshot = {k: v for k, v in existing.items() if k != "_id"}
    
    if existing.get("status") not in ["draft"]:
        # Only allow limited updates for non-draft invoices
        allowed_fields = {"customer_notes", "terms_conditions", "custom_fields"}
        update_dict = {k: v for k, v in update.dict().items() if v is not None and k in allowed_fields}
    else:
        update_dict = {k: v for k, v in update.dict().items() if v is not None}
        
        # Recalculate totals if line items changed
        if update.line_items:
            customer = await contacts_collection.find_one({"contact_id": existing.get("customer_id")})
            org_state = "DL"
            customer_state = update.place_of_supply or existing.get("place_of_supply", "")
            is_igst = customer_state and customer_state != org_state
            is_inclusive = existing.get("is_inclusive_tax", False)
            
            # Delete old line items
            await invoice_line_items_collection.delete_many({"invoice_id": invoice_id})
            
            # Calculate new line items
            calculated_items = []
            for item in update.line_items:
                calc_item = calculate_line_item(item, is_igst, is_inclusive)
                calc_item["line_item_id"] = generate_id("LI")
                calc_item["invoice_id"] = invoice_id
                calculated_items.append(calc_item)
                await invoice_line_items_collection.insert_one(calc_item)
            
            # Recalculate totals
            totals = calculate_invoice_totals(
                calculated_items,
                update.discount_type or existing.get("discount_type", "percentage"),
                update.discount_value if update.discount_value is not None else existing.get("discount_value", 0),
                update.shipping_charge if update.shipping_charge is not None else existing.get("shipping_charge", 0),
                update.adjustment if update.adjustment is not None else existing.get("adjustment", 0),
                is_inclusive
            )
            
            update_dict.update(totals)
            del update_dict["line_items"]
    
    if update_dict:
        update_dict["updated_time"] = datetime.now(timezone.utc).isoformat()
        await invoices_collection.update_one({"invoice_id": invoice_id}, {"$set": update_dict})
    
    await add_invoice_history(invoice_id, "updated", "Invoice details updated")
    
    updated = await invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})

    # Audit log: invoice UPDATE
    await log_financial_action(
        org_id=existing.get("organization_id", ""), action="UPDATE", entity_type="invoice",
        entity_id=invoice_id, request=request,
        before_snapshot=before_snapshot, after_snapshot=updated,
    )

    return {"code": 0, "message": "Invoice updated", "invoice": updated}

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, force: bool = False):
    """Delete invoice (only drafts, or void if has payments)"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Period lock check
    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(invoices_collection.database, invoice.get("organization_id", ""), invoice.get("invoice_date", ""))

    # Check for payments
    payment_count = await invoice_payments_collection.count_documents({"invoice_id": invoice_id})
    
    if payment_count > 0:
        if force:
            # Void instead of delete
            await invoices_collection.update_one(
                {"invoice_id": invoice_id},
                {"$set": {
                    "status": "void",
                    "voided_date": datetime.now(timezone.utc).isoformat(),
                    "updated_time": datetime.now(timezone.utc).isoformat()
                }}
            )
            await add_invoice_history(invoice_id, "voided", "Invoice voided")
            await update_contact_balance(invoice["customer_id"])
            return {"code": 0, "message": "Invoice voided (has payments)", "voided": True}
        else:
            raise HTTPException(status_code=400, detail="Cannot delete invoice with payments. Use force=true to void.")
    
    if invoice.get("status") not in ["draft"]:
        if force:
            # Void
            await invoices_collection.update_one(
                {"invoice_id": invoice_id},
                {"$set": {
                    "status": "void",
                    "voided_date": datetime.now(timezone.utc).isoformat()
                }}
            )
            await add_invoice_history(invoice_id, "voided", "Invoice voided")
            await update_contact_balance(invoice["customer_id"])
            return {"code": 0, "message": "Invoice voided", "voided": True}
        else:
            raise HTTPException(status_code=400, detail="Only draft invoices can be deleted. Use force=true to void.")
    
    # Delete draft
    await invoice_line_items_collection.delete_many({"invoice_id": invoice_id})
    await invoice_history_collection.delete_many({"invoice_id": invoice_id})
    await invoices_collection.delete_one({"invoice_id": invoice_id})
    
    return {"code": 0, "message": "Invoice deleted"}

# ========================= INVOICE ACTIONS =========================

@router.post("/{invoice_id}/send")
async def send_invoice(request: Request, invoice_id: str, email_to: Optional[str] = Query(None),
    message: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),  # "email", "whatsapp", "both"
    background_tasks: BackgroundTasks = None
):
    """
    Send invoice via email with PDF attachment (5B)
    
    Pre-send checks:
    1. If e-invoicing enabled and B2B: IRN must be REGISTERED
    2. Customer must have email address
    3. Invoice must be finalized (not draft for B2B with e-invoice)
    """
    from services.pdf_service import generate_gst_invoice_html
    from services.email_service import EmailService
    from weasyprint import HTML
    
    # Get org context
    org_id = await get_org_id(request)
    
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") == "void":
        raise HTTPException(status_code=400, detail="Cannot send voided invoice")
    
    if invoice.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot send cancelled invoice")
    
    # Determine recipient
    recipient_email = email_to or invoice.get("customer_email")
    if not recipient_email:
        raise HTTPException(status_code=400, detail="No email address available. Add customer email first.")
    
    # ==================== E-INVOICE PRE-SEND CHECK (5B) ====================
    customer_gstin = invoice.get('customer_gstin', invoice.get('gst_no', ''))
    is_b2b = bool(customer_gstin and customer_gstin not in ['', 'URP', None])
    
    einvoice_config = None
    einvoice_enabled = False
    if org_id:
        einvoice_config = await db["einvoice_config"].find_one(
            {"organization_id": org_id}, 
            {"_id": 0}
        )
        einvoice_enabled = einvoice_config.get("enabled", False) if einvoice_config else False
    
    irn_status = invoice.get('irn_status', 'pending')
    has_irn = invoice.get('irn') and irn_status == 'registered'
    
    # Rule: If e-invoicing enabled and B2B, IRN must be registered
    if einvoice_enabled and is_b2b and not has_irn:
        raise HTTPException(
            status_code=400,
            detail="IRN registration required before sending B2B invoice. Generate IRN first from the invoice detail page."
        )
    
    # ==================== GENERATE PDF ====================
    try:
        # Get line items
        line_items = await invoice_line_items_collection.find(
            {"invoice_id": invoice_id},
            {"_id": 0}
        ).to_list(100)
        
        # Get organization settings
        org_settings = await db["organizations"].find_one(
            {"organization_id": org_id} if org_id else {},
            {"_id": 0}
        ) or {}
        if not org_settings:
            org_settings = await db["organization_settings"].find_one({}, {"_id": 0}) or {}
        
        # Prepare IRN data
        irn_data = None
        if has_irn:
            irn_data = {
                'irn': invoice.get('irn'),
                'ack_no': invoice.get('irn_ack_no'),
                'ack_date': invoice.get('irn_ack_date'),
                'signed_qr_code': invoice.get('irn_signed_qr')
            }
        
        # Get bank details
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
        
        # Generate HTML and PDF
        html_content = generate_gst_invoice_html(
            invoice=invoice,
            line_items=line_items,
            org_settings=org_settings,
            irn_data=irn_data,
            bank_details=bank_details
        )
        
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_content = pdf_buffer.getvalue()
        
        # File naming
        customer_name_safe = (invoice.get('customer_name', '') or 'Customer').replace(' ', '_')[:30]
        pdf_filename = f"INV-{invoice.get('invoice_number', invoice_id)}-{customer_name_safe}.pdf"
        
    except Exception as e:
        logger.error(f"PDF generation failed for invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed. Fix PDF issue before sending: {str(e)}")
    
    # ==================== GET PAYMENT LINK (if Razorpay configured) ====================
    payment_link = None
    if org_id:
        razorpay_config = await db["razorpay_config"].find_one(
            {"organization_id": org_id},
            {"_id": 0, "enabled": 1}
        )
        if razorpay_config and razorpay_config.get("enabled"):
            # Check for existing payment link or we can generate one
            payment_link = invoice.get('razorpay_payment_link')
    
    # ==================== DETERMINE DELIVERY CHANNEL ====================
    customer_phone = invoice.get("customer_phone", "") or invoice.get("contact_number", "")

    # Check if WhatsApp is configured for this org
    whatsapp_configured = False
    if org_id:
        from services.credential_service import get_credentials, WHATSAPP as WA_CRED
        wa_creds = await get_credentials(org_id, WA_CRED)
        whatsapp_configured = bool(wa_creds and wa_creds.get("phone_number_id"))

    # Default channel logic
    if not channel:
        channel = "whatsapp" if (whatsapp_configured and customer_phone) else "email"

    send_whatsapp_flag = channel in ("whatsapp", "both")
    send_email_flag = channel in ("email", "both") or (not whatsapp_configured and channel == "whatsapp")

    # ==================== SEND VIA WHATSAPP ====================
    whatsapp_result = None
    if send_whatsapp_flag and whatsapp_configured and customer_phone:
        try:
            from services.whatsapp_service import send_whatsapp_document, WhatsAppNotConfigured
            # Build a public URL for the PDF  (use the share-link endpoint)
            api_base = os.environ.get("REACT_APP_BACKEND_URL", "")
            pdf_url = f"{api_base}/api/invoices-enhanced/{invoice_id}/pdf"

            inv_number = invoice.get("invoice_number", invoice_id)
            customer_name = invoice.get("customer_name", "Customer")
            grand_total = invoice.get("grand_total", invoice.get("total", 0))
            org_name_wa = org_settings.get("company_name", org_settings.get("name", "Battwheels"))

            caption = (
                f"Hi {customer_name}, your invoice {inv_number} "
                f"for ₹{grand_total:,.0f} is ready. "
                f"Thank you for choosing {org_name_wa}."
            )
            whatsapp_result = await send_whatsapp_document(
                to_phone=customer_phone,
                document_url=pdf_url,
                filename=pdf_filename,
                caption=caption,
                org_id=org_id,
            )
        except Exception as wa_err:
            logger.warning(f"WhatsApp send failed for invoice {invoice_id}: {wa_err}. Falling back to email.")
            send_email_flag = True  # Auto-fallback

    # ==================== SEND EMAIL ====================
    email_result = {"status": "skipped"}
    if send_email_flag and recipient_email:
        try:
            email_result = await EmailService.send_invoice_email(
                to_email=recipient_email,
                customer_name=invoice.get('customer_name', 'Customer'),
                invoice_number=invoice.get('invoice_number', invoice_id),
                invoice_date=invoice.get('invoice_date', invoice.get('date', '')),
                due_date=invoice.get('due_date', ''),
                amount=invoice.get('sub_total', 0),
                tax_amount=invoice.get('tax_total', 0),
                total=invoice.get('grand_total', invoice.get('total', 0)),
                org_name=org_settings.get('company_name', org_settings.get('name', 'Battwheels')),
                org_address=f"{org_settings.get('address', '')} {org_settings.get('city', '')} {org_settings.get('pincode', '')}".strip(),
                org_gstin=org_settings.get('gstin', ''),
                org_logo_url=org_settings.get('logo_url'),
                org_email=org_settings.get('email'),
                irn=invoice.get('irn') if has_irn else None,
                irn_ack_no=invoice.get('irn_ack_no') if has_irn else None,
                payment_link=payment_link,
                pdf_content=pdf_content,
                pdf_filename=pdf_filename
            )
            if email_result.get("status") == "error":
                raise HTTPException(status_code=500, detail=f"Email sending failed: {email_result.get('message')}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email sending failed for invoice {invoice_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    # ==================== UPDATE INVOICE STATUS ====================
    was_draft = invoice.get("status") == "draft"
    if was_draft:
        await update_item_stock_for_invoice(invoice_id, reverse=False)

    new_status = "sent" if was_draft else invoice.get("status")
    channels_used = []
    if whatsapp_result:
        channels_used.append("whatsapp")
    if email_result.get("status") not in ("skipped", None):
        channels_used.append("email")

    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "status": new_status,
            "is_sent": True,
            "sent_date": datetime.now(timezone.utc).isoformat(),
            "sent_to_email": recipient_email if send_email_flag else None,
            "sent_to_whatsapp": customer_phone if whatsapp_result else None,
            "updated_time": datetime.now(timezone.utc).isoformat(),
            "stock_deducted": True
        }}
    )

    # Post journal entry for double-entry bookkeeping (only when transitioning from draft)
    if was_draft:
        if org_id:
            try:
                await post_invoice_journal_entry(org_id, invoice)
                logger.info(f"Posted journal entry for invoice {invoice.get('invoice_number')}")
            except Exception as e:
                logger.warning(f"Failed to post journal entry for invoice {invoice.get('invoice_number')}: {e}")

    channel_desc = " + ".join(channels_used) if channels_used else "none"
    await add_invoice_history(
        invoice_id,
        "sent",
        f"Invoice sent via {channel_desc}"
    )
    await update_contact_balance(invoice["customer_id"])

    return {
        "code": 0,
        "message": f"Invoice sent via {channel_desc}",
        "channels": channels_used,
        "email_status": email_result.get("status"),
        "whatsapp_message_id": whatsapp_result.get("message_id") if whatsapp_result else None,
    }

@router.post("/{invoice_id}/mark-sent")
async def mark_invoice_sent(invoice_id: str):
    """Mark invoice as sent without emailing"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be marked as sent")
    
    # Deduct stock
    await update_item_stock_for_invoice(invoice_id, reverse=False)
    
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "status": "sent",
            "is_sent": True,
            "sent_date": datetime.now(timezone.utc).isoformat(),
            "updated_time": datetime.now(timezone.utc).isoformat(),
            "stock_deducted": True
        }}
    )
    
    # Post journal entry for double-entry bookkeeping
    org_id = invoice.get("organization_id", "")
    if org_id:
        try:
            await post_invoice_journal_entry(org_id, invoice)
            logger.info(f"Posted journal entry for invoice {invoice.get('invoice_number')}")
        except Exception as e:
            logger.warning(f"Failed to post journal entry for invoice {invoice.get('invoice_number')}: {e}")
    
    await add_invoice_history(invoice_id, "sent", "Invoice marked as sent manually")
    await update_contact_balance(invoice["customer_id"])
    
    return {"code": 0, "message": "Invoice marked as sent"}

@router.post("/{invoice_id}/void")
async def void_invoice(invoice_id: str, reason: str = "", request: Request = None):
    """Void an invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Capture before_snapshot for audit
    before_snapshot = {k: v for k, v in invoice.items() if k != "_id"}
    
    if invoice.get("status") == "void":
        raise HTTPException(status_code=400, detail="Invoice is already void")
    
    # Reverse stock if it was deducted
    if invoice.get("stock_deducted"):
        await update_item_stock_for_invoice(invoice_id, reverse=True)
    
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "status": "void",
            "voided_date": datetime.now(timezone.utc).isoformat(),
            "void_reason": reason,
            "balance_due": 0,
            "stock_deducted": False,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_invoice_history(invoice_id, "voided", f"Invoice voided. Reason: {reason or 'Not specified'}")
    await update_contact_balance(invoice["customer_id"])
    
    # Audit log: invoice VOID
    voided = await invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    await log_financial_action(
        org_id=invoice.get("organization_id", ""), action="VOID", entity_type="invoice",
        entity_id=invoice_id, request=request,
        before_snapshot=before_snapshot, after_snapshot=voided,
    )
    
    return {"code": 0, "message": "Invoice voided"}

@router.post("/{invoice_id}/clone")
async def clone_invoice(invoice_id: str):
    """Clone an invoice as new draft"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get line items
    line_items = await invoice_line_items_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0, "line_item_id": 0, "invoice_id": 0}
    ).to_list(100)
    
    # Create new invoice
    new_invoice_id = generate_id("INV")
    new_invoice_number = await get_next_invoice_number()
    
    new_invoice = {
        **invoice,
        "invoice_id": new_invoice_id,
        "invoice_number": new_invoice_number,
        "invoice_date": datetime.now(timezone.utc).date().isoformat(),
        "due_date": (datetime.now(timezone.utc) + timedelta(days=invoice.get("payment_terms", 30))).date().isoformat(),
        "status": "draft",
        "amount_paid": 0,
        "credits_applied": 0,
        "balance_due": invoice.get("grand_total", 0),
        "payment_count": 0,
        "last_payment_date": None,
        "is_sent": False,
        "sent_date": None,
        "viewed_date": None,
        "paid_date": None,
        "voided_date": None,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await invoices_collection.insert_one(new_invoice)
    
    # Clone line items
    for item in line_items:
        item["line_item_id"] = generate_id("LI")
        item["invoice_id"] = new_invoice_id
        await invoice_line_items_collection.insert_one(item)
    
    await add_invoice_history(new_invoice_id, "created", f"Invoice cloned from {invoice.get('invoice_number')}")
    
    new_invoice.pop("_id", None)
    return {"code": 0, "message": "Invoice cloned", "invoice": new_invoice}

# ========================= PAYMENTS =========================

@router.get("/{invoice_id}/payments")
async def get_invoice_payments(invoice_id: str):
    """Get all payments for an invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payments = await invoice_payments_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).sort("payment_date", -1).to_list(100)
    
    return {
        "code": 0,
        "payments": payments,
        "total_paid": invoice.get("amount_paid", 0),
        "balance_due": invoice.get("balance_due", 0)
    }

@router.post("/{invoice_id}/payments")
async def record_payment(invoice_id: str, payment: PaymentCreate, request: Request = None):
    """Record a payment against invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") in ["void", "paid"]:
        raise HTTPException(status_code=400, detail=f"Cannot record payment for {invoice.get('status')} invoice")
    
    balance_due = invoice.get("balance_due", 0)
    if payment.amount > balance_due:
        raise HTTPException(status_code=400, detail=f"Payment amount ({payment.amount}) exceeds balance due ({balance_due})")
    
    payment_id = generate_id("PAY")
    
    payment_doc = {
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "customer_id": invoice.get("customer_id"),
        "invoice_number": invoice.get("invoice_number"),
        "amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "reference_number": payment.reference_number,
        "payment_date": payment.payment_date or datetime.now(timezone.utc).date().isoformat(),
        "bank_charges": payment.bank_charges,
        "notes": payment.notes,
        "deposit_to_account": payment.deposit_to_account,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await invoice_payments_collection.insert_one(payment_doc)
    
    # Update invoice
    new_amount_paid = invoice.get("amount_paid", 0) + payment.amount
    new_balance = invoice.get("grand_total", 0) - new_amount_paid - invoice.get("credits_applied", 0) - invoice.get("write_off_amount", 0)
    new_status = "paid" if new_balance <= 0 else "partially_paid"
    
    update_fields = {
        "amount_paid": new_amount_paid,
        "balance_due": max(0, new_balance),
        "status": new_status,
        "payment_count": invoice.get("payment_count", 0) + 1,
        "last_payment_date": payment_doc["payment_date"],
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    if new_status == "paid":
        update_fields["paid_date"] = datetime.now(timezone.utc).isoformat()
    
    await invoices_collection.update_one({"invoice_id": invoice_id}, {"$set": update_fields})
    
    await add_invoice_history(invoice_id, "payment_received", f"Payment of ₹{payment.amount:,.2f} received via {payment.payment_mode}")
    await update_contact_balance(invoice["customer_id"])
    
    payment_doc.pop("_id", None)

    # Audit log: payment CREATE
    before_inv = {k: v for k, v in invoice.items() if k != "_id"}
    after_inv = await invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    await log_financial_action(
        org_id=invoice.get("organization_id", ""), action="CREATE", entity_type="payment",
        entity_id=payment_id, request=request,
        before_snapshot=before_inv, after_snapshot={"payment": payment_doc, "invoice_after": after_inv},
    )

    return {
        "code": 0,
        "message": "Payment recorded",
        "payment": payment_doc,
        "new_balance": max(0, new_balance),
        "new_status": new_status
    }

@router.delete("/{invoice_id}/payments/{payment_id}")
async def delete_payment(invoice_id: str, payment_id: str):
    """Delete a payment (reverses the payment)"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment = await invoice_payments_collection.find_one({"payment_id": payment_id, "invoice_id": invoice_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Delete payment
    await invoice_payments_collection.delete_one({"payment_id": payment_id})
    
    # Update invoice
    new_amount_paid = invoice.get("amount_paid", 0) - payment.get("amount", 0)
    new_balance = invoice.get("grand_total", 0) - new_amount_paid - invoice.get("credits_applied", 0)
    
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "amount_paid": max(0, new_amount_paid),
            "balance_due": new_balance,
            "status": "sent" if new_amount_paid == 0 else "partially_paid",
            "payment_count": max(0, invoice.get("payment_count", 1) - 1),
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_invoice_history(invoice_id, "payment_deleted", f"Payment of ₹{payment.get('amount', 0):,.2f} deleted")
    await update_contact_balance(invoice["customer_id"])
    
    return {"code": 0, "message": "Payment deleted", "new_balance": new_balance}

# ========================= WRITE-OFF =========================

@router.post("/{invoice_id}/write-off")
async def write_off_balance(invoice_id: str, amount: Optional[float] = None, reason: str = ""):
    """Write off invoice balance as bad debt"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    balance = invoice.get("balance_due", 0)
    if balance <= 0:
        raise HTTPException(status_code=400, detail="No balance to write off")
    
    write_off_amount = amount if amount and amount <= balance else balance
    new_balance = balance - write_off_amount
    
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "write_off_amount": invoice.get("write_off_amount", 0) + write_off_amount,
            "balance_due": new_balance,
            "status": "written_off" if new_balance <= 0 else invoice.get("status"),
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_invoice_history(invoice_id, "write_off", f"₹{write_off_amount:,.2f} written off as bad debt. Reason: {reason or 'Not specified'}")
    await update_contact_balance(invoice["customer_id"])
    
    return {"code": 0, "message": f"₹{write_off_amount:,.2f} written off", "new_balance": new_balance}

# ========================= BULK OPERATIONS =========================

@router.post("/bulk-action")
async def bulk_invoice_action(request: BulkActionRequest, background_tasks: BackgroundTasks):
    """Perform bulk action on invoices"""
    action = request.action
    invoice_ids = request.invoice_ids
    
    if not invoice_ids:
        raise HTTPException(status_code=400, detail="No invoices selected")
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    for invoice_id in invoice_ids:
        try:
            if action == "send":
                invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
                if invoice and invoice.get("customer_email"):
                    mock_send_email(
                        [invoice["customer_email"]],
                        f"Invoice {invoice['invoice_number']}",
                        "Please find attached invoice.",
                        f"Invoice_{invoice['invoice_number']}.pdf"
                    )
                    await invoices_collection.update_one(
                        {"invoice_id": invoice_id},
                        {"$set": {"is_sent": True, "status": "sent", "sent_date": datetime.now(timezone.utc).isoformat()}}
                    )
                    results["success"] += 1
                else:
                    results["errors"].append(f"{invoice_id}: No email")
                    results["failed"] += 1
            
            elif action == "void":
                await invoices_collection.update_one(
                    {"invoice_id": invoice_id},
                    {"$set": {"status": "void", "voided_date": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            elif action == "mark_paid":
                invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
                if invoice:
                    await invoices_collection.update_one(
                        {"invoice_id": invoice_id},
                        {"$set": {
                            "status": "paid",
                            "balance_due": 0,
                            "amount_paid": invoice.get("grand_total", 0),
                            "paid_date": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    results["success"] += 1
            
            elif action == "delete":
                invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
                if invoice and invoice.get("status") == "draft":
                    await invoice_line_items_collection.delete_many({"invoice_id": invoice_id})
                    await invoices_collection.delete_one({"invoice_id": invoice_id})
                    results["success"] += 1
                else:
                    results["errors"].append(f"{invoice_id}: Not a draft")
                    results["failed"] += 1
            
            else:
                results["errors"].append(f"Unknown action: {action}")
                results["failed"] += 1
        
        except Exception as e:
            results["errors"].append(f"{invoice_id}: {str(e)}")
            results["failed"] += 1
    
    return {"code": 0, "results": results}

# ========================= RECURRING INVOICES =========================

@router.get("/recurring")
async def list_recurring_profiles(status: str = "active"):
    """List recurring invoice profiles"""
    query = {} if status == "all" else {"status": status}
    profiles = await recurring_invoices_collection.find(query, {"_id": 0}).to_list(100)
    return {"code": 0, "profiles": profiles}

@router.post("/recurring")
async def create_recurring_profile(profile: RecurringInvoiceCreate):
    """Create a recurring invoice profile"""
    customer = await contacts_collection.find_one({"contact_id": profile.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    profile_id = generate_id("REC")
    
    profile_doc = {
        "profile_id": profile_id,
        "customer_id": profile.customer_id,
        "customer_name": customer.get("name", ""),
        "profile_name": profile.profile_name or f"Recurring - {customer.get('name')}",
        "start_date": profile.start_date or datetime.now(timezone.utc).date().isoformat(),
        "end_date": profile.end_date,
        "repeat_every": profile.repeat_every,
        "repeat_unit": profile.repeat_unit,
        "next_invoice_date": profile.start_date or datetime.now(timezone.utc).date().isoformat(),
        "payment_terms": profile.payment_terms,
        "line_items": [item.dict() for item in profile.line_items],
        "discount_type": profile.discount_type,
        "discount_value": profile.discount_value,
        "shipping_charge": profile.shipping_charge,
        "customer_notes": profile.customer_notes,
        "terms_conditions": profile.terms_conditions,
        "send_email": profile.send_email,
        "create_days_before": profile.create_days_before,
        "status": "active",
        "invoices_created": 0,
        "last_invoice_date": None,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await recurring_invoices_collection.insert_one(profile_doc)
    
    profile_doc.pop("_id", None)
    return {"code": 0, "message": "Recurring profile created", "profile": profile_doc}

@router.get("/recurring/{profile_id}")
async def get_recurring_profile(profile_id: str):
    """Get recurring profile details"""
    profile = await recurring_invoices_collection.find_one({"profile_id": profile_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get generated invoices
    invoices = await invoices_collection.find(
        {"recurring_profile_id": profile_id},
        {"_id": 0, "invoice_id": 1, "invoice_number": 1, "invoice_date": 1, "grand_total": 1, "status": 1}
    ).sort("invoice_date", -1).to_list(50)
    
    profile["invoices"] = invoices
    return {"code": 0, "profile": profile}

@router.post("/recurring/{profile_id}/pause")
async def pause_recurring_profile(profile_id: str):
    """Pause a recurring profile"""
    result = await recurring_invoices_collection.update_one(
        {"profile_id": profile_id},
        {"$set": {"status": "paused"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"code": 0, "message": "Profile paused"}

@router.post("/recurring/{profile_id}/resume")
async def resume_recurring_profile(profile_id: str):
    """Resume a paused recurring profile"""
    result = await recurring_invoices_collection.update_one(
        {"profile_id": profile_id},
        {"$set": {"status": "active"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"code": 0, "message": "Profile resumed"}

@router.delete("/recurring/{profile_id}")
async def delete_recurring_profile(profile_id: str):
    """Delete a recurring profile"""
    result = await recurring_invoices_collection.delete_one({"profile_id": profile_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"code": 0, "message": "Profile deleted"}

# ========================= CREATE FROM OTHER DOCUMENTS =========================

@router.post("/from-salesorder/{salesorder_id}")
async def create_invoice_from_salesorder(salesorder_id: str, background_tasks: BackgroundTasks):
    """Create invoice from sales order"""
    salesorder = await db["salesorders_enhanced"].find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Check if already invoiced
    existing = await invoices_collection.find_one({"salesorder_id": salesorder_id})
    if existing:
        raise HTTPException(status_code=400, detail=f"Sales order already invoiced: {existing.get('invoice_number')}")
    
    # Get line items
    line_items = await db["salesorder_line_items"].find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).to_list(100)
    
    # Convert to invoice line items
    invoice_items = [
        LineItem(
            item_id=item.get("item_id"),
            name=item.get("name"),
            description=item.get("description", ""),
            hsn_sac_code=item.get("hsn_sac_code", ""),
            quantity=item.get("quantity", 1),
            unit=item.get("unit", "pcs"),
            rate=item.get("rate", 0),
            discount_type=item.get("discount_type", "percentage"),
            discount_value=item.get("discount_value", 0),
            tax_type=item.get("tax_type", "gst"),
            tax_rate=item.get("tax_rate", 18)
        )
        for item in line_items
    ]
    
    # Create invoice
    invoice_data = InvoiceCreate(
        customer_id=salesorder.get("customer_id"),
        salesorder_id=salesorder_id,
        reference_number=salesorder.get("salesorder_number"),
        payment_terms=salesorder.get("payment_terms", 30),
        line_items=invoice_items,
        discount_type=salesorder.get("discount_type", "percentage"),
        discount_value=salesorder.get("discount_value", 0),
        shipping_charge=salesorder.get("shipping_charge", 0),
        adjustment=salesorder.get("adjustment", 0),
        adjustment_description=salesorder.get("adjustment_description", ""),
        place_of_supply=salesorder.get("place_of_supply", ""),
        customer_notes=salesorder.get("customer_notes", ""),
        terms_conditions=salesorder.get("terms_conditions", "")
    )
    
    result = await create_invoice(invoice_data, background_tasks)
    
    # Update sales order
    await db["salesorders_enhanced"].update_one(
        {"salesorder_id": salesorder_id},
        {"$set": {
            "status": "invoiced",
            "invoice_id": result["invoice"]["invoice_id"],
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return result

@router.post("/from-estimate/{estimate_id}")
async def create_invoice_from_estimate(estimate_id: str, background_tasks: BackgroundTasks):
    """Create invoice from estimate/quote"""
    estimate = await db["estimates"].find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if estimate.get("status") != "accepted":
        raise HTTPException(status_code=400, detail="Only accepted estimates can be converted to invoices")
    
    # Get line items
    line_items = await db["estimate_line_items"].find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).to_list(100)
    
    # Convert to invoice line items (handle field name differences between estimate and invoice)
    invoice_items = [
        LineItem(
            item_id=item.get("item_id"),
            name=item.get("name"),
            description=item.get("description", ""),
            hsn_sac_code=item.get("hsn_sac_code") or item.get("hsn_code", ""),
            quantity=item.get("quantity", 1),
            unit=item.get("unit", "pcs"),
            rate=item.get("rate", 0),
            discount_type=item.get("discount_type") or "percentage",
            discount_value=item.get("discount_value") or item.get("discount_percent", 0),
            tax_type=item.get("tax_type", "gst"),
            tax_rate=item.get("tax_rate") or item.get("tax_percentage", 18)
        )
        for item in line_items
    ]
    
    # Create invoice
    invoice_data = InvoiceCreate(
        customer_id=estimate.get("customer_id"),
        estimate_id=estimate_id,
        reference_number=estimate.get("estimate_number"),
        payment_terms=estimate.get("payment_terms", 30),
        line_items=invoice_items,
        discount_type=estimate.get("discount_type", "percentage"),
        discount_value=estimate.get("discount_value", 0),
        shipping_charge=estimate.get("shipping_charge", 0),
        adjustment=estimate.get("adjustment", 0),
        place_of_supply=estimate.get("place_of_supply", ""),
        customer_notes=estimate.get("customer_notes", ""),
        terms_conditions=estimate.get("terms_conditions", "")
    )
    
    result = await create_invoice(invoice_data, background_tasks)
    
    # Update estimate
    await db["estimates"].update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "invoiced",
            "invoice_id": result["invoice"]["invoice_id"],
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return result

# ========================= SHARE LINKS =========================

@router.post("/{invoice_id}/share")
async def create_invoice_share_link(invoice_id: str, config: InvoiceShareConfig):
    """Create a public share link for an invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") == "draft":
        raise HTTPException(status_code=400, detail="Cannot share draft invoices")
    
    # Deactivate existing share links
    await invoice_share_links_collection.update_many(
        {"invoice_id": invoice_id, "is_active": True},
        {"$set": {"is_active": False}}
    )
    
    # Create new share link
    share_token = generate_share_token()
    share_link_id = generate_id("INVLINK")
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=config.expiry_days)).isoformat()
    
    share_doc = {
        "share_link_id": share_link_id,
        "invoice_id": invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "customer_id": invoice.get("customer_id"),
        "share_token": share_token,
        "public_url": f"/public/invoice/{share_token}",
        "expiry_date": expiry_date,
        "allow_payment": config.allow_payment,
        "password_protected": config.password_protected,
        "password_hash": config.password if config.password_protected else None,
        "is_active": True,
        "view_count": 0,
        "first_viewed_at": None,
        "last_viewed_at": None,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await invoice_share_links_collection.insert_one(share_doc)
    await add_invoice_history(invoice_id, "share_link_created", f"Share link created, expires {expiry_date[:10]}")
    
    return {
        "code": 0,
        "share_link": {
            "share_link_id": share_link_id,
            "public_url": share_doc["public_url"],
            "expiry_date": expiry_date,
            "share_token": share_token
        }
    }

@router.get("/{invoice_id}/share-links")
async def list_invoice_share_links(invoice_id: str):
    """List all share links for an invoice"""
    links = await invoice_share_links_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0, "password_hash": 0}
    ).sort("created_time", -1).to_list(20)
    
    return {"code": 0, "share_links": links}

@router.delete("/{invoice_id}/share-links/{share_link_id}")
async def revoke_invoice_share_link(invoice_id: str, share_link_id: str):
    """Revoke a share link"""
    result = await invoice_share_links_collection.update_one(
        {"share_link_id": share_link_id, "invoice_id": invoice_id},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Share link not found")
    
    await add_invoice_history(invoice_id, "share_link_revoked", "Share link was revoked")
    return {"code": 0, "message": "Share link revoked"}

# ========================= ATTACHMENTS =========================

@router.post("/{invoice_id}/attachments")
async def upload_invoice_attachment(
    invoice_id: str,
    file: UploadFile = File(...)
):
    """Upload an attachment to an invoice (max 5 files, 10MB each)"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check attachment count
    existing_count = await invoice_attachments_collection.count_documents({"invoice_id": invoice_id})
    if existing_count >= MAX_ATTACHMENTS_PER_INVOICE:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_ATTACHMENTS_PER_INVOICE} attachments allowed")
    
    # Read and validate file
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_ATTACHMENT_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_ATTACHMENT_SIZE_MB}MB limit")
    
    # Store attachment
    attachment_id = generate_id("INVATT")
    attachment_doc = {
        "attachment_id": attachment_id,
        "invoice_id": invoice_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "file_data": base64.b64encode(content).decode("utf-8"),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": "system"
    }
    
    await invoice_attachments_collection.insert_one(attachment_doc)
    await add_invoice_history(invoice_id, "attachment_added", f"File attached: {file.filename}")
    
    return {
        "code": 0,
        "message": "Attachment uploaded",
        "attachment": {
            "attachment_id": attachment_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(content),
            "uploaded_at": attachment_doc["uploaded_at"]
        }
    }

@router.get("/{invoice_id}/attachments")
async def list_invoice_attachments(invoice_id: str):
    """List all attachments for an invoice"""
    attachments = await invoice_attachments_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0, "file_data": 0}
    ).to_list(MAX_ATTACHMENTS_PER_INVOICE)
    
    return {"code": 0, "attachments": attachments}

@router.get("/{invoice_id}/attachments/{attachment_id}")
async def download_invoice_attachment(invoice_id: str, attachment_id: str):
    """Download an attachment"""
    attachment = await invoice_attachments_collection.find_one({
        "attachment_id": attachment_id,
        "invoice_id": invoice_id
    })
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    content = base64.b64decode(attachment["file_data"])
    return Response(
        content=content,
        media_type=attachment["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{attachment["filename"]}"'
        }
    )

@router.delete("/{invoice_id}/attachments/{attachment_id}")
async def delete_invoice_attachment(invoice_id: str, attachment_id: str):
    """Delete an attachment"""
    result = await invoice_attachments_collection.delete_one({
        "attachment_id": attachment_id,
        "invoice_id": invoice_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    await add_invoice_history(invoice_id, "attachment_deleted", "Attachment removed")
    return {"code": 0, "message": "Attachment deleted"}

# ========================= COMMENTS =========================

@router.post("/{invoice_id}/comments")
async def add_invoice_comment(invoice_id: str, comment_data: InvoiceCommentCreate):
    """Add a comment/note to an invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    comment_id = generate_id("INVCMT")
    comment_doc = {
        "comment_id": comment_id,
        "invoice_id": invoice_id,
        "comment": comment_data.comment,
        "is_internal": comment_data.is_internal,
        "created_by": "system",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await invoice_comments_collection.insert_one(comment_doc)
    await add_invoice_history(invoice_id, "comment_added", "Comment added")
    
    comment_doc.pop("_id", None)
    return {"code": 0, "comment": comment_doc}

@router.get("/{invoice_id}/comments")
async def list_invoice_comments(invoice_id: str, include_internal: bool = True):
    """List all comments for an invoice"""
    query = {"invoice_id": invoice_id}
    if not include_internal:
        query["is_internal"] = False
    
    comments = await invoice_comments_collection.find(
        query, {"_id": 0}
    ).sort("created_time", -1).to_list(100)
    
    return {"code": 0, "comments": comments}

@router.delete("/{invoice_id}/comments/{comment_id}")
async def delete_invoice_comment(invoice_id: str, comment_id: str):
    """Delete a comment"""
    result = await invoice_comments_collection.delete_one({
        "comment_id": comment_id,
        "invoice_id": invoice_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return {"code": 0, "message": "Comment deleted"}

# ========================= HISTORY =========================

@router.get("/{invoice_id}/history")
async def get_invoice_history(invoice_id: str, limit: int = 50):
    """Get invoice history/activity log"""
    history = await invoice_history_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {"code": 0, "history": history}

# ========================= EXPORT =========================

@router.get("/export/csv")
async def export_invoices_csv(
    status: str = "",
    customer_id: str = "",
    from_date: str = "",
    to_date: str = ""
):
    """Export invoices to CSV"""
    import csv
    
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    if from_date:
        query["invoice_date"] = {"$gte": from_date}
    if to_date:
        if "invoice_date" in query:
            query["invoice_date"]["$lte"] = to_date
        else:
            query["invoice_date"] = {"$lte": to_date}
    
    invoices = await invoices_collection.find(query, {"_id": 0}).to_list(5000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Invoice Number", "Date", "Due Date", "Customer", "Status",
        "Subtotal", "Tax", "Total", "Paid", "Balance", "Reference"
    ])
    
    # Rows
    for inv in invoices:
        writer.writerow([
            inv.get("invoice_number", ""),
            inv.get("invoice_date", ""),
            inv.get("due_date", ""),
            inv.get("customer_name", ""),
            inv.get("status", ""),
            inv.get("sub_total", 0),
            inv.get("tax_total", 0),
            inv.get("grand_total", 0),
            inv.get("amount_paid", 0),
            inv.get("balance_due", 0),
            inv.get("reference_number", "")
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=invoices_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )
