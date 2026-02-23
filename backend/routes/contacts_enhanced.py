# Enhanced Contacts Module v2 - Unified Customer & Vendor Management
# Combines features from contacts_enhanced and customers_enhanced for single source of truth
# Supports contact_type: customer, vendor, both

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import motor.motor_asyncio
import os
import re
import uuid
import logging

# Import tenant context for multi-tenant scoping
from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts-enhanced", tags=["Contacts Enhanced v2"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Use main contacts collection which has Zoho-synced data
contacts_collection = db["contacts"]
contact_persons_collection = db["contact_persons"]
addresses_collection = db["addresses"]
contact_tags_collection = db["contact_tags"]
contact_statements_collection = db["contact_statements"]
contact_history_collection = db["contact_history"]
contact_credits_collection = db["contact_credits"]
contact_refunds_collection = db["contact_refunds"]
contact_settings_collection = db["contact_settings"]

# Multi-tenant helpers (Phase F migration - using TenantContext)
async def get_org_id(request: Request) -> Optional[str]:
    """Get organization ID from request for multi-tenant scoping"""
    try:
        ctx = await optional_tenant_context(request)
        return ctx.org_id if ctx else None
    except Exception:
        return None

def org_query(org_id: Optional[str], base_query: dict = None) -> dict:
    """Add org_id to query if available"""
    query = base_query or {}
    if org_id:
        query["organization_id"] = org_id
    return query

# GSTIN Validation Regex
GSTIN_REGEX = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'

# GST State codes mapping
GSTIN_STATE_MAP = {
    "01": {"code": "JK", "name": "Jammu & Kashmir"},
    "02": {"code": "HP", "name": "Himachal Pradesh"},
    "03": {"code": "PB", "name": "Punjab"},
    "04": {"code": "CH", "name": "Chandigarh"},
    "05": {"code": "UK", "name": "Uttarakhand"},
    "06": {"code": "HR", "name": "Haryana"},
    "07": {"code": "DL", "name": "Delhi"},
    "08": {"code": "RJ", "name": "Rajasthan"},
    "09": {"code": "UP", "name": "Uttar Pradesh"},
    "10": {"code": "BR", "name": "Bihar"},
    "11": {"code": "SK", "name": "Sikkim"},
    "12": {"code": "AR", "name": "Arunachal Pradesh"},
    "13": {"code": "NL", "name": "Nagaland"},
    "14": {"code": "MN", "name": "Manipur"},
    "15": {"code": "MZ", "name": "Mizoram"},
    "16": {"code": "TR", "name": "Tripura"},
    "17": {"code": "ML", "name": "Meghalaya"},
    "18": {"code": "AS", "name": "Assam"},
    "19": {"code": "WB", "name": "West Bengal"},
    "20": {"code": "JH", "name": "Jharkhand"},
    "21": {"code": "OR", "name": "Odisha"},
    "22": {"code": "CG", "name": "Chhattisgarh"},
    "23": {"code": "MP", "name": "Madhya Pradesh"},
    "24": {"code": "GJ", "name": "Gujarat"},
    "26": {"code": "DD", "name": "Daman & Diu"},
    "27": {"code": "MH", "name": "Maharashtra"},
    "28": {"code": "AP", "name": "Andhra Pradesh (Old)"},
    "29": {"code": "KA", "name": "Karnataka"},
    "30": {"code": "GA", "name": "Goa"},
    "31": {"code": "LD", "name": "Lakshadweep"},
    "32": {"code": "KL", "name": "Kerala"},
    "33": {"code": "TN", "name": "Tamil Nadu"},
    "34": {"code": "PY", "name": "Puducherry"},
    "35": {"code": "AN", "name": "Andaman & Nicobar"},
    "36": {"code": "TG", "name": "Telangana"},
    "37": {"code": "AP", "name": "Andhra Pradesh (New)"},
    "38": {"code": "LD", "name": "Lakshadweep"},
    "97": {"code": "OT", "name": "Other Territory"}
}

INDIAN_STATES = [
    ("AN", "Andaman and Nicobar Islands"), ("AP", "Andhra Pradesh"), ("AR", "Arunachal Pradesh"),
    ("AS", "Assam"), ("BR", "Bihar"), ("CH", "Chandigarh"), ("CG", "Chhattisgarh"),
    ("DD", "Dadra & Nagar Haveli and Daman & Diu"), ("DL", "Delhi"), ("GA", "Goa"),
    ("GJ", "Gujarat"), ("HR", "Haryana"), ("HP", "Himachal Pradesh"), ("JK", "Jammu & Kashmir"),
    ("JH", "Jharkhand"), ("KA", "Karnataka"), ("KL", "Kerala"), ("LD", "Lakshadweep"),
    ("MP", "Madhya Pradesh"), ("MH", "Maharashtra"), ("MN", "Manipur"), ("ML", "Meghalaya"),
    ("MZ", "Mizoram"), ("NL", "Nagaland"), ("OR", "Odisha"), ("PY", "Puducherry"),
    ("PB", "Punjab"), ("RJ", "Rajasthan"), ("SK", "Sikkim"), ("TN", "Tamil Nadu"),
    ("TG", "Telangana"), ("TR", "Tripura"), ("UK", "Uttarakhand"), ("UP", "Uttar Pradesh"),
    ("WB", "West Bengal"), ("OT", "Other Territory")
]

ORG_STATE_CODE = "DL"  # Organization state

# ========================= PYDANTIC MODELS =========================

class ContactTagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    color: str = "#3B82F6"

class ContactTagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class ContactPersonCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    designation: str = ""
    department: str = ""
    is_primary: bool = False
    salutation: str = ""
    notes: str = ""

class ContactPersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    is_primary: Optional[bool] = None
    salutation: Optional[str] = None
    notes: Optional[str] = None

class AddressCreate(BaseModel):
    address_type: str = Field(default="billing", pattern="^(billing|shipping)$")
    attention: str = ""
    street: str = ""
    street2: str = ""
    city: str = ""
    state: str = ""
    state_code: str = ""
    zip_code: str = ""
    country: str = "India"
    phone: str = ""
    fax: str = ""
    is_default: bool = False

class AddressUpdate(BaseModel):
    address_type: Optional[str] = None
    attention: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    is_default: Optional[bool] = None

class ContactCreate(BaseModel):
    # Required
    name: str = Field(..., min_length=1, max_length=200)
    contact_type: str = Field(default="customer", pattern="^(customer|vendor|both)$")
    # Basic Info
    company_name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    website: str = ""
    # Financial
    currency_code: str = "INR"
    payment_terms: int = Field(default=30, ge=0)
    credit_limit: float = Field(default=0, ge=0)
    opening_balance: float = 0
    opening_balance_type: str = "credit"  # credit or debit
    # GST
    gstin: str = ""
    pan: str = ""
    place_of_supply: str = ""
    gst_treatment: str = "registered"  # registered, unregistered, consumer, overseas, sez
    tax_treatment: str = "business_gst"  # business_gst, business_none, non_business
    # Classification (for customers)
    customer_type: str = "business"  # business, individual
    customer_segment: str = ""
    industry: str = ""
    # Pricing
    price_list_id: Optional[str] = None
    discount_percent: float = 0
    # Portal
    portal_enabled: bool = False
    # Additional
    notes: str = ""
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    # Source tracking
    source: str = "direct"  # direct, referral, website, import
    referred_by: str = ""
    # Nested data
    persons: List[ContactPersonCreate] = []
    addresses: List[AddressCreate] = []

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    contact_type: Optional[str] = None
    company_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    currency_code: Optional[str] = None
    payment_terms: Optional[int] = None
    credit_limit: Optional[float] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    place_of_supply: Optional[str] = None
    gst_treatment: Optional[str] = None
    tax_treatment: Optional[str] = None
    customer_type: Optional[str] = None
    customer_segment: Optional[str] = None
    industry: Optional[str] = None
    price_list_id: Optional[str] = None
    discount_percent: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class CreditNoteCreate(BaseModel):
    amount: float = Field(..., gt=0)
    reason: str = ""
    reference_number: str = ""
    date: str = ""

class RefundCreate(BaseModel):
    amount: float = Field(..., gt=0)
    mode: str = "cash"  # cash, bank_transfer, cheque, online
    reference_number: str = ""
    date: str = ""
    notes: str = ""

class StatementRequest(BaseModel):
    start_date: str = ""
    end_date: str = ""
    email_to: str = ""
    include_details: bool = True

class BulkActionRequest(BaseModel):
    contact_ids: List[str]
    action: str  # activate, deactivate, delete, add_tag, remove_tag
    tag_name: Optional[str] = None

# ========================= HELPER FUNCTIONS =========================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def validate_gstin(gstin: str) -> dict:
    """Validate GSTIN format and extract information"""
    if not gstin:
        return {"valid": False, "error": "Empty GSTIN"}
    
    gstin = gstin.upper().strip()
    
    pattern = r'^([0-9]{2})([A-Z]{5}[0-9]{4}[A-Z])([0-9A-Z])([Z])([0-9A-Z])$'
    match = re.match(pattern, gstin)
    
    if not match:
        return {"valid": False, "error": "Invalid GSTIN format"}
    
    state_code = match.group(1)
    pan = match.group(2)
    entity_code = match.group(3)
    
    if state_code not in GSTIN_STATE_MAP:
        return {"valid": False, "error": "Invalid state code"}
    
    state_info = GSTIN_STATE_MAP[state_code]
    
    entity_types = {
        "1": "Proprietorship", "2": "Partnership", "3": "HUF",
        "4": "Company", "5": "AOP/BOI", "6": "Local Authority",
        "7": "Government", "8": "Others", "9": "TDS", "A": "TCS"
    }
    
    return {
        "valid": True,
        "gstin": gstin,
        "state_code": state_info["code"],
        "state_name": state_info["name"],
        "pan": pan,
        "entity_type": entity_types.get(entity_code, "Unknown"),
        "gst_state_code": state_code
    }

async def calculate_contact_balance(contact_id: str) -> dict:
    """Calculate contact's current balance from transactions"""
    # Get all invoices (for customers)
    invoices = await db["invoices"].find(
        {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}], "status": {"$ne": "void"}},
        {"total": 1, "balance_due": 1, "status": 1}
    ).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_receivable = sum(inv.get("balance_due", 0) for inv in invoices)
    
    # Get all bills (for vendors)
    bills = await db["bills"].find(
        {"$or": [{"vendor_id": contact_id}, {"contact_id": contact_id}], "status": {"$ne": "void"}},
        {"total": 1, "balance_due": 1}
    ).to_list(1000)
    
    total_billed = sum(bill.get("total", 0) for bill in bills)
    total_payable = sum(bill.get("balance_due", 0) for bill in bills)
    
    # Get contact credits
    credits = await contact_credits_collection.find(
        {"contact_id": contact_id, "status": "active"},
        {"amount": 1, "used_amount": 1}
    ).to_list(100)
    
    total_credits = sum(c.get("amount", 0) - c.get("used_amount", 0) for c in credits)
    
    # Get payments received
    payments = await db["payments"].find(
        {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]},
        {"amount": 1}
    ).to_list(1000)
    
    total_payments = sum(p.get("amount", 0) for p in payments)
    
    return {
        "total_invoiced": round(total_invoiced, 2),
        "total_receivable": round(total_receivable, 2),
        "total_billed": round(total_billed, 2),
        "total_payable": round(total_payable, 2),
        "total_credits": round(total_credits, 2),
        "total_payments": round(total_payments, 2),
        "net_receivable": round(total_receivable - total_credits, 2),
        "net_balance": round(total_receivable - total_payable, 2)
    }

async def get_contact_aging(contact_id: str, aging_type: str = "receivable") -> dict:
    """Calculate aging buckets for contact"""
    today = datetime.now(timezone.utc).date()
    
    if aging_type == "receivable":
        docs = await db["invoices"].find(
            {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}], 
             "status": {"$in": ["sent", "overdue", "partially_paid"]}, 
             "balance_due": {"$gt": 0}},
            {"_id": 0, "invoice_number": 1, "due_date": 1, "balance_due": 1}
        ).to_list(1000)
    else:
        docs = await db["bills"].find(
            {"$or": [{"vendor_id": contact_id}, {"contact_id": contact_id}], 
             "status": {"$in": ["open", "overdue", "partially_paid"]}, 
             "balance_due": {"$gt": 0}},
            {"_id": 0, "bill_number": 1, "due_date": 1, "balance_due": 1}
        ).to_list(1000)
    
    aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    
    for doc in docs:
        due_date_str = doc.get("due_date", "")
        if not due_date_str:
            continue
        
        try:
            if isinstance(due_date_str, str):
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
            else:
                due_date = due_date_str.date() if hasattr(due_date_str, 'date') else due_date_str
            
            days_overdue = (today - due_date).days
            balance = doc.get("balance_due", 0)
            
            if days_overdue <= 0:
                aging["current"] += balance
            elif days_overdue <= 30:
                aging["1_30"] += balance
            elif days_overdue <= 60:
                aging["31_60"] += balance
            elif days_overdue <= 90:
                aging["61_90"] += balance
            else:
                aging["over_90"] += balance
        except:
            continue
    
    return {k: round(v, 2) for k, v in aging.items()}

async def is_contact_used_in_transactions(contact_id: str) -> dict:
    """Check if contact is linked to any transactions"""
    estimates_count = await db["estimates_enhanced"].count_documents(
        {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]}
    )
    salesorders_count = await db["salesorders_enhanced"].count_documents(
        {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]}
    )
    invoices_count = await db["invoices"].count_documents(
        {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]}
    )
    bills_count = await db["bills"].count_documents(
        {"$or": [{"vendor_id": contact_id}, {"contact_id": contact_id}]}
    )
    estimates_legacy = await db["estimates"].count_documents({"customer_id": contact_id})
    po_count = await db["purchase_orders"].count_documents({"vendor_id": contact_id})
    payment_count = await db["payments"].count_documents({"contact_id": contact_id})
    
    total = estimates_count + salesorders_count + invoices_count + bills_count + estimates_legacy + po_count + payment_count
    
    return {
        "is_used": total > 0,
        "estimates_count": estimates_count + estimates_legacy,
        "salesorders_count": salesorders_count,
        "invoices_count": invoices_count,
        "bills_count": bills_count,
        "purchase_orders_count": po_count,
        "payments_count": payment_count,
        "total_transactions": total
    }

async def add_contact_history(contact_id: str, action: str, details: str, user_id: str = ""):
    """Add entry to contact history"""
    history_entry = {
        "history_id": generate_id("HIST"),
        "contact_id": contact_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await contact_history_collection.insert_one(history_entry)

def mock_send_email(to_email: str, subject: str, body: str, attachment_name: str = ""):
    """Mock email sending - logs instead of actual send"""
    logger.info(f"[MOCK EMAIL] To: {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Attachment: {attachment_name}")
    logger.info(f"[MOCK EMAIL] Body Preview: {body[:200]}...")
    return True

def mock_generate_pdf(data: dict, template: str = "statement") -> bytes:
    """Mock PDF generation"""
    logger.info(f"[MOCK PDF] Generating {template} PDF for contact {data.get('contact_id', 'unknown')}")
    return b"PDF_CONTENT_MOCK"

async def get_next_contact_number(contact_type: str) -> str:
    """Generate next contact number"""
    prefix = "CUST-" if contact_type in ["customer", "both"] else "VEND-"
    settings = await contact_settings_collection.find_one({"type": f"numbering_{contact_type}"})
    if not settings:
        settings = {"type": f"numbering_{contact_type}", "prefix": prefix, "next_number": 1, "padding": 5}
        await contact_settings_collection.insert_one(settings)
    
    number = str(settings["next_number"]).zfill(settings.get("padding", 5))
    next_num = f"{settings.get('prefix', prefix)}{number}"
    
    await contact_settings_collection.update_one(
        {"type": f"numbering_{contact_type}"},
        {"$inc": {"next_number": 1}}
    )
    
    return next_num

# ========================= SETTINGS ENDPOINTS =========================

@router.get("/settings")
async def get_contact_settings():
    """Get contact module settings"""
    customer_numbering = await contact_settings_collection.find_one({"type": "numbering_customer"}, {"_id": 0})
    vendor_numbering = await contact_settings_collection.find_one({"type": "numbering_vendor"}, {"_id": 0})
    defaults = await contact_settings_collection.find_one({"type": "defaults"}, {"_id": 0})
    
    if not customer_numbering:
        customer_numbering = {"type": "numbering_customer", "prefix": "CUST-", "next_number": 1, "padding": 5}
    if not vendor_numbering:
        vendor_numbering = {"type": "numbering_vendor", "prefix": "VEND-", "next_number": 1, "padding": 5}
    if not defaults:
        defaults = {
            "type": "defaults",
            "payment_terms": 30,
            "credit_limit": 0,
            "currency_code": "INR",
            "gst_treatment": "registered",
            "portal_enabled_by_default": False
        }
    
    return {"code": 0, "settings": {
        "customer_numbering": customer_numbering, 
        "vendor_numbering": vendor_numbering, 
        "defaults": defaults
    }}

@router.put("/settings")
async def update_contact_settings(settings: dict):
    """Update contact module settings"""
    for key in ["customer_numbering", "vendor_numbering", "defaults"]:
        if key in settings:
            type_key = key.replace("_numbering", "")
            await contact_settings_collection.update_one(
                {"type": f"numbering_{type_key}" if "numbering" in key else key},
                {"$set": settings[key]},
                upsert=True
            )
    return {"code": 0, "message": "Settings updated"}

# ========================= GSTIN VALIDATION (Must be before /{contact_id}) =========================

@router.get("/validate-gstin/{gstin}")
async def validate_gstin_endpoint(gstin: str):
    """Validate GSTIN and return parsed information"""
    result = validate_gstin(gstin)
    return {"code": 0 if result["valid"] else 1, "result": result, "valid": result["valid"], "details": result if result["valid"] else None}

# ========================= STATES ENDPOINT =========================

@router.get("/states")
async def get_indian_states():
    """Get list of Indian states for dropdowns"""
    return {"code": 0, "states": [{"code": s[0], "name": s[1]} for s in INDIAN_STATES]}

# ========================= SUMMARY ENDPOINT (Must be before /{contact_id}) =========================

@router.get("/summary")
async def get_contacts_summary(contact_type: Optional[str] = None):
    """Get contacts summary statistics"""
    base_query = {}
    if contact_type:
        if contact_type == "customer":
            base_query["contact_type"] = {"$in": ["customer", "both"]}
        elif contact_type == "vendor":
            base_query["contact_type"] = {"$in": ["vendor", "both"]}
        else:
            base_query["contact_type"] = contact_type
    
    total = await contacts_collection.count_documents(base_query)
    customers = await contacts_collection.count_documents({**base_query, "contact_type": {"$in": ["customer", "both"]}})
    vendors = await contacts_collection.count_documents({**base_query, "contact_type": {"$in": ["vendor", "both"]}})
    active = await contacts_collection.count_documents({**base_query, "is_active": True})
    inactive = await contacts_collection.count_documents({**base_query, "is_active": False})
    with_gstin = await contacts_collection.count_documents({**base_query, "gstin": {"$nin": ["", None]}})
    with_portal = await contacts_collection.count_documents({**base_query, "portal_enabled": True})
    
    # Calculate total receivables and payables
    pipeline = [
        {"$match": {**base_query, "is_active": True}},
        {"$group": {
            "_id": None,
            "total_receivable": {"$sum": {"$ifNull": ["$outstanding_receivable", 0]}},
            "total_payable": {"$sum": {"$ifNull": ["$outstanding_payable", 0]}},
            "total_credit_limit": {"$sum": {"$ifNull": ["$credit_limit", 0]}}
        }}
    ]
    
    stats = await contacts_collection.aggregate(pipeline).to_list(1)
    values = stats[0] if stats else {"total_receivable": 0, "total_payable": 0, "total_credit_limit": 0}
    
    # New contacts this month
    first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    new_this_month = await contacts_collection.count_documents({**base_query, "created_time": {"$gte": first_of_month}})
    
    return {
        "code": 0,
        "summary": {
            "total_contacts": total,
            "customers": customers,
            "vendors": vendors,
            "active": active,
            "inactive": inactive,
            "with_gstin": with_gstin,
            "with_portal": with_portal,
            "new_this_month": new_this_month,
            "total_receivable": round(values.get("total_receivable", 0), 2),
            "total_payable": round(values.get("total_payable", 0), 2),
            "total_credit_limit": round(values.get("total_credit_limit", 0), 2)
        }
    }

# ========================= CHECK SYNC ENDPOINT =========================

@router.get("/check-sync")
async def check_contacts_sync(contact_type: Optional[str] = None):
    """Audit contacts against Zoho-like features and check data quality"""
    base_query = {}
    if contact_type:
        if contact_type == "customer":
            base_query["contact_type"] = {"$in": ["customer", "both"]}
        elif contact_type == "vendor":
            base_query["contact_type"] = {"$in": ["vendor", "both"]}
    
    total = await contacts_collection.count_documents(base_query)
    active = await contacts_collection.count_documents({**base_query, "is_active": True})
    inactive = await contacts_collection.count_documents({**base_query, "is_active": False})
    
    # Data quality checks
    missing_gstin = await contacts_collection.count_documents({**base_query, "gstin": {"$in": ["", None]}, "gst_treatment": "registered"})
    missing_email = await contacts_collection.count_documents({**base_query, "email": {"$in": ["", None]}})
    missing_phone = await contacts_collection.count_documents({**base_query, "phone": {"$in": ["", None]}, "mobile": {"$in": ["", None]}})
    
    # GST treatment breakdown
    gst_breakdown = {}
    for treatment in ["registered", "unregistered", "consumer", "overseas", "sez"]:
        count = await contacts_collection.count_documents({**base_query, "gst_treatment": treatment})
        gst_breakdown[treatment] = count
    
    # Contact type breakdown
    type_breakdown = {}
    for ctype in ["customer", "vendor", "both"]:
        count = await contacts_collection.count_documents({**base_query, "contact_type": ctype})
        type_breakdown[ctype] = count
    
    # Portal stats
    portal_enabled = await contacts_collection.count_documents({**base_query, "portal_enabled": True})
    
    # Suggestions for data cleanup
    suggestions = []
    if missing_gstin > 0:
        suggestions.append(f"Update GSTIN for {missing_gstin} registered contacts")
    if missing_email > 0:
        suggestions.append(f"Add email for {missing_email} contacts to enable portal/statements")
    
    return {
        "code": 0,
        "sync_report": {
            "summary": {"total": total, "active": active, "inactive": inactive},
            "data_quality": {
                "missing_gstin_registered": missing_gstin,
                "missing_email": missing_email,
                "missing_phone": missing_phone
            },
            "contact_type_breakdown": type_breakdown,
            "gst_treatment_breakdown": gst_breakdown,
            "portal": {"enabled": portal_enabled, "not_enabled": total - portal_enabled},
            "suggestions": suggestions
        }
    }

# ========================= TAGS ENDPOINTS =========================

@router.get("/tags")
async def list_contact_tags(include_inactive: bool = False):
    """List all contact tags"""
    query = {} if include_inactive else {"is_active": {"$ne": False}}
    tags = await contact_tags_collection.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    for tag in tags:
        count = await contacts_collection.count_documents({"tags": tag.get("tag_id", tag.get("name")), "is_active": True})
        tag["contact_count"] = count
    
    return {"code": 0, "tags": tags}

@router.post("/tags")
async def create_contact_tag(tag: ContactTagCreate):
    """Create a new contact tag"""
    existing = await contact_tags_collection.find_one({"name": {"$regex": f"^{tag.name}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")
    
    tag_doc = {
        "tag_id": generate_id("TAG"),
        "name": tag.name,
        "description": tag.description,
        "color": tag.color,
        "contact_count": 0,
        "is_active": True,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    await contact_tags_collection.insert_one(tag_doc)
    tag_doc.pop("_id", None)
    return {"code": 0, "message": "Tag created", "tag": tag_doc}

@router.get("/tags/{tag_id}")
async def get_contact_tag(tag_id: str):
    """Get a specific tag"""
    tag = await contact_tags_collection.find_one({"tag_id": tag_id}, {"_id": 0})
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    contacts = await contacts_collection.find(
        {"tags": tag_id, "is_active": True},
        {"_id": 0, "contact_id": 1, "name": 1, "contact_type": 1}
    ).to_list(100)
    tag["contacts"] = contacts
    
    return {"code": 0, "tag": tag}

@router.put("/tags/{tag_id}")
async def update_contact_tag(tag_id: str, tag: ContactTagUpdate):
    """Update a contact tag"""
    existing = await contact_tags_collection.find_one({"tag_id": tag_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    update_data = {k: v for k, v in tag.dict().items() if v is not None}
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        await contact_tags_collection.update_one({"tag_id": tag_id}, {"$set": update_data})
    
    updated = await contact_tags_collection.find_one({"tag_id": tag_id}, {"_id": 0})
    return {"code": 0, "message": "Tag updated", "tag": updated}

@router.delete("/tags/{tag_id}")
async def delete_contact_tag(tag_id: str):
    """Delete a contact tag (only if unused)"""
    tag = await contact_tags_collection.find_one({"tag_id": tag_id})
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    usage_count = await contacts_collection.count_documents({"tags": tag_id})
    if usage_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete tag used by {usage_count} contacts")
    
    await contact_tags_collection.delete_one({"tag_id": tag_id})
    return {"code": 0, "message": "Tag deleted"}

# ========================= BACKWARD COMPATIBILITY (Must be before /{contact_id}) =========================

@router.get("/customers")
async def list_customers_only(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1),
    request: Request = None
):
    """Backward compatible: List customers only"""
    return await list_contacts(request=request, contact_type="customer", search=search, page=page, limit=limit)

@router.get("/vendors")
async def list_vendors_only(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1),
    request: Request = None
):
    """Backward compatible: List vendors only"""
    return await list_contacts(request=request, contact_type="vendor", search=search, page=page, limit=limit)

# ========================= REPORTS (Must be before /{contact_id}) =========================

@router.get("/reports/by-segment")
async def report_by_segment():
    """Report: Contacts by segment"""
    pipeline = [
        {"$match": {"contact_type": {"$in": ["customer", "both"]}}},
        {"$group": {
            "_id": "$customer_segment",
            "count": {"$sum": 1},
            "total_outstanding": {"$sum": {"$ifNull": ["$outstanding_receivable", 0]}}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = await contacts_collection.aggregate(pipeline).to_list(50)
    
    return {
        "code": 0,
        "report": [{"segment": r["_id"] or "Unclassified", "count": r["count"], "total_outstanding": round(r["total_outstanding"], 2)} for r in results]
    }

@router.get("/reports/top-customers")
async def report_top_customers(limit: int = 20):
    """Report: Top customers by outstanding amount"""
    contacts = await contacts_collection.find(
        {"contact_type": {"$in": ["customer", "both"]}, "is_active": True},
        {"_id": 0, "contact_id": 1, "name": 1, "company_name": 1, "outstanding_receivable": 1}
    ).sort("outstanding_receivable", -1).limit(limit).to_list(limit)
    
    return {"code": 0, "report": contacts}

@router.get("/reports/top-vendors")
async def report_top_vendors(limit: int = 20):
    """Report: Top vendors by payable amount"""
    contacts = await contacts_collection.find(
        {"contact_type": {"$in": ["vendor", "both"]}, "is_active": True},
        {"_id": 0, "contact_id": 1, "name": 1, "company_name": 1, "outstanding_payable": 1}
    ).sort("outstanding_payable", -1).limit(limit).to_list(limit)
    
    return {"code": 0, "report": contacts}

@router.get("/reports/aging-summary")
async def report_aging_summary(aging_type: str = "receivable"):
    """Report: Aging summary across all contacts"""
    contact_type_filter = {"$in": ["customer", "both"]} if aging_type == "receivable" else {"$in": ["vendor", "both"]}
    
    contacts = await contacts_collection.find(
        {"contact_type": contact_type_filter, "is_active": True},
        {"_id": 0, "contact_id": 1}
    ).to_list(1000)
    
    total_aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    
    for contact in contacts:
        aging = await get_contact_aging(contact["contact_id"], aging_type)
        for bucket in total_aging:
            total_aging[bucket] += aging.get(bucket, 0)
    
    return {
        "code": 0,
        "report": {k: round(v, 2) for k, v in total_aging.items()},
        "total": round(sum(total_aging.values()), 2),
        "aging_type": aging_type
    }

@router.get("/reports/new-contacts")
async def report_new_contacts(days: int = 30, contact_type: Optional[str] = None):
    """Report: New contacts in last N days"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    query = {"created_time": {"$gte": cutoff}}
    if contact_type:
        if contact_type == "customer":
            query["contact_type"] = {"$in": ["customer", "both"]}
        elif contact_type == "vendor":
            query["contact_type"] = {"$in": ["vendor", "both"]}
    
    contacts = await contacts_collection.find(
        query,
        {"_id": 0, "contact_id": 1, "name": 1, "company_name": 1, "contact_type": 1, "email": 1, "created_time": 1, "source": 1}
    ).sort("created_time", -1).to_list(100)
    
    return {"code": 0, "report": contacts, "total": len(contacts)}

# ========================= CONTACT CRUD =========================

@router.post("/")
async def create_contact(contact: ContactCreate, background_tasks: BackgroundTasks, request: Request = None):
    """Create a new contact (customer, vendor, or both)"""
    # Get org context for multi-tenant scoping
    org_id = await get_org_id(request) if request else None
    
    # Check for duplicate by GSTIN or email (org-scoped)
    if contact.gstin:
        existing_query = org_query(org_id, {"gstin": contact.gstin.upper()})
        existing = await contacts_collection.find_one(existing_query)
        if existing:
            raise HTTPException(status_code=400, detail=f"Contact with GSTIN {contact.gstin} already exists")
    
    if contact.email:
        existing_query = org_query(org_id, {"email": contact.email.lower()})
        existing = await contacts_collection.find_one(existing_query)
        if existing:
            raise HTTPException(status_code=400, detail=f"Contact with email {contact.email} already exists")
    
    contact_id = generate_id("CON")
    contact_number = await get_next_contact_number(contact.contact_type)
    
    # Validate and parse GSTIN
    gstin_info = None
    if contact.gstin:
        gstin_info = validate_gstin(contact.gstin)
        if not gstin_info["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid GSTIN: {gstin_info.get('error')}")
        contact.gstin = gstin_info["gstin"]
        if not contact.place_of_supply:
            contact.place_of_supply = gstin_info["state_code"]
        if not contact.pan:
            contact.pan = gstin_info["pan"]
    
    # Build contact document
    contact_doc = {
        "contact_id": contact_id,
        "contact_number": contact_number,
        "contact_type": contact.contact_type,
        "name": contact.name,
        "display_name": contact.name,
        "company_name": contact.company_name,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email.lower() if contact.email else "",
        "phone": contact.phone,
        "mobile": contact.mobile,
        "website": contact.website,
        "currency_code": contact.currency_code,
        "payment_terms": contact.payment_terms,
        "credit_limit": contact.credit_limit,
        "opening_balance": contact.opening_balance,
        "opening_balance_type": contact.opening_balance_type,
        "gstin": contact.gstin.upper() if contact.gstin else "",
        "pan": contact.pan.upper() if contact.pan else "",
        "place_of_supply": contact.place_of_supply,
        "gst_treatment": contact.gst_treatment,
        "tax_treatment": contact.tax_treatment,
        "customer_type": contact.customer_type,
        "customer_segment": contact.customer_segment,
        "industry": contact.industry,
        "price_list_id": contact.price_list_id,
        "discount_percent": contact.discount_percent,
        "portal_enabled": contact.portal_enabled,
        "portal_token": "",
        "notes": contact.notes,
        "tags": contact.tags,
        "custom_fields": contact.custom_fields,
        "source": contact.source,
        "referred_by": contact.referred_by,
        # Computed fields
        "is_active": True,
        "outstanding_receivable": contact.opening_balance if contact.opening_balance_type == "debit" and contact.contact_type in ["customer", "both"] else 0,
        "outstanding_payable": contact.opening_balance if contact.opening_balance_type == "debit" and contact.contact_type in ["vendor", "both"] else 0,
        "unused_credits": 0,
        "has_billing_address": False,
        "has_shipping_address": False,
        "contact_persons_count": 0,
        "addresses_count": 0,
        # Timestamps
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat(),
        "last_activity_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Add org_id for multi-tenant scoping
    if org_id:
        contact_doc["organization_id"] = org_id
    
    await contacts_collection.insert_one(contact_doc)
    
    # Create contact persons
    for person in contact.persons:
        person_doc = {
            "person_id": generate_id("PER"),
            "contact_id": contact_id,
            **person.dict(),
            "created_time": datetime.now(timezone.utc).isoformat()
        }
        await contact_persons_collection.insert_one(person_doc)
    
    # Create addresses
    for address in contact.addresses:
        address_doc = {
            "address_id": generate_id("ADDR"),
            "contact_id": contact_id,
            **address.dict(),
            "created_time": datetime.now(timezone.utc).isoformat()
        }
        await addresses_collection.insert_one(address_doc)
    
    # Update counts
    person_count = len(contact.persons)
    address_count = len(contact.addresses)
    has_billing = any(a.address_type == "billing" for a in contact.addresses)
    has_shipping = any(a.address_type == "shipping" for a in contact.addresses)
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {
            "contact_persons_count": person_count,
            "addresses_count": address_count,
            "has_billing_address": has_billing,
            "has_shipping_address": has_shipping
        }}
    )
    
    await add_contact_history(contact_id, "created", f"Contact {contact_number} created")
    
    # Send welcome email (mocked)
    if contact.email:
        background_tasks.add_task(mock_send_email, contact.email, "Welcome to Battwheels", f"Dear {contact.name}, Welcome!")
    
    contact_doc.pop("_id", None)
    return {"code": 0, "message": "Contact created", "contact": contact_doc}

@router.get("/")
async def list_contacts(
    request: Request,
    contact_type: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    gst_treatment: Optional[str] = None,
    tag: Optional[str] = None,
    has_outstanding: Optional[bool] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List contacts with filters and standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    # Get org context for multi-tenant scoping
    org_id = await get_org_id(request)
    query = org_query(org_id, {})

    if contact_type:
        if contact_type == "customer":
            query["contact_type"] = {"$in": ["customer", "both"]}
        elif contact_type == "vendor":
            query["contact_type"] = {"$in": ["vendor", "both"]}
        else:
            query["contact_type"] = contact_type

    if status == "active":
        query["is_active"] = True
    elif status == "inactive":
        query["is_active"] = False

    if gst_treatment:
        query["gst_treatment"] = gst_treatment

    if tag:
        query["tags"] = tag

    if has_outstanding is True:
        query["$or"] = [{"outstanding_receivable": {"$gt": 0}}, {"outstanding_payable": {"$gt": 0}}]
    elif has_outstanding is False:
        query["outstanding_receivable"] = {"$lte": 0}
        query["outstanding_payable"] = {"$lte": 0}

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"display_name": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"gstin": {"$regex": search, "$options": "i"}},
            {"contact_number": {"$regex": search, "$options": "i"}}
        ]

    total = await contacts_collection.count_documents(query)
    skip = (page - 1) * limit
    sort_dir = 1 if sort_order == "asc" else -1
    total_pages = math.ceil(total / limit) if total > 0 else 1

    contacts = await contacts_collection.find(query, {"_id": 0}).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)

    # Enrich with balance and counts
    for contact in contacts:
        contact_id = contact.get("contact_id") or contact.get("zoho_contact_id") or str(contact.get("_id", ""))
        if contact_id:
            contact["person_count"] = await contact_persons_collection.count_documents({"contact_id": contact_id})
            contact["address_count"] = await addresses_collection.count_documents({"contact_id": contact_id})
            balance = await calculate_contact_balance(contact_id)
            contact["balance"] = balance
        else:
            contact["person_count"] = 0
            contact["address_count"] = 0
            contact["balance"] = {"total_receivable": 0, "total_payable": 0}

    return {
        "contacts": contacts,
        "data": contacts,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{contact_id}")
async def get_contact(contact_id: str, request: Request):
    """Get contact details with persons, addresses, balance, aging, and transactions"""
    # Get org context for multi-tenant scoping
    org_id = await get_org_id(request)
    contact_query = org_query(org_id, {"contact_id": contact_id})
    
    contact = await contacts_collection.find_one(contact_query, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Get contact persons
    persons = await contact_persons_collection.find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).sort("is_primary", -1).to_list(50)
    contact["persons"] = persons
    
    # Get addresses
    addresses = await addresses_collection.find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).to_list(20)
    contact["addresses"] = addresses
    
    # Get balance details
    balance = await calculate_contact_balance(contact_id)
    contact["balance_details"] = balance
    
    # Get aging (for customers)
    if contact.get("contact_type") in ["customer", "both"]:
        aging = await get_contact_aging(contact_id, "receivable")
        contact["aging"] = aging
    
    # Get aging (for vendors)
    if contact.get("contact_type") in ["vendor", "both"]:
        payable_aging = await get_contact_aging(contact_id, "payable")
        contact["payable_aging"] = payable_aging
    
    # Get transaction counts
    usage = await is_contact_used_in_transactions(contact_id)
    contact["transaction_counts"] = usage
    
    # Get history
    history = await contact_history_collection.find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20).to_list(20)
    contact["history"] = history
    
    # Get credits (for customers)
    if contact.get("contact_type") in ["customer", "both"]:
        credits = await contact_credits_collection.find(
            {"contact_id": contact_id, "status": "active"},
            {"_id": 0}
        ).to_list(20)
        contact["credits"] = credits
    
    # Get tags details
    if contact.get("tags"):
        tags = await contact_tags_collection.find({"tag_id": {"$in": contact["tags"]}}, {"_id": 0}).to_list(50)
        contact["tag_details"] = tags
    
    return {"code": 0, "contact": contact}

@router.put("/{contact_id}")
async def update_contact(contact_id: str, contact: ContactUpdate):
    """Update contact details"""
    existing = await contacts_collection.find_one({"contact_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = {k: v for k, v in contact.dict().items() if v is not None}
    
    # Validate GSTIN if changed
    if "gstin" in update_data and update_data["gstin"]:
        gstin_info = validate_gstin(update_data["gstin"])
        if not gstin_info["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid GSTIN: {gstin_info.get('error')}")
        update_data["gstin"] = gstin_info["gstin"]
        if not contact.place_of_supply:
            update_data["place_of_supply"] = gstin_info["state_code"]
        if not contact.pan:
            update_data["pan"] = gstin_info["pan"]
        
        # Check for duplicate
        dup = await contacts_collection.find_one({"gstin": update_data["gstin"], "contact_id": {"$ne": contact_id}})
        if dup:
            raise HTTPException(status_code=400, detail="GSTIN already exists for another contact")
    
    # Check email duplicate
    if "email" in update_data and update_data["email"]:
        update_data["email"] = update_data["email"].lower()
        dup = await contacts_collection.find_one({"email": update_data["email"], "contact_id": {"$ne": contact_id}})
        if dup:
            raise HTTPException(status_code=400, detail="Email already exists for another contact")
    
    # Update name fields
    if "name" in update_data:
        update_data["display_name"] = update_data["name"]
    
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        await contacts_collection.update_one({"contact_id": contact_id}, {"$set": update_data})
    
    await add_contact_history(contact_id, "updated", "Contact details updated")
    
    updated = await contacts_collection.find_one({"contact_id": contact_id}, {"_id": 0})
    return {"code": 0, "message": "Contact updated", "contact": updated}

@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, force: bool = False):
    """Delete a contact (only if not used in transactions or force=True to deactivate)"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    usage = await is_contact_used_in_transactions(contact_id)
    
    if usage["is_used"]:
        if force:
            # Deactivate instead of delete
            await contacts_collection.update_one(
                {"contact_id": contact_id},
                {"$set": {"is_active": False, "updated_time": datetime.now(timezone.utc).isoformat()}}
            )
            await add_contact_history(contact_id, "deactivated", "Contact deactivated (has transactions)")
            return {"code": 0, "message": "Contact deactivated (has transactions)", "deactivated": True}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete contact with {usage['total_transactions']} transactions. Use force=true to deactivate."
            )
    
    # Delete related data
    await contact_persons_collection.delete_many({"contact_id": contact_id})
    await addresses_collection.delete_many({"contact_id": contact_id})
    await contact_history_collection.delete_many({"contact_id": contact_id})
    await contact_credits_collection.delete_many({"contact_id": contact_id})
    await contacts_collection.delete_one({"contact_id": contact_id})
    
    return {"code": 0, "message": "Contact deleted"}

# ========================= CONTACT PERSONS =========================

@router.get("/{contact_id}/persons")
async def get_contact_persons(contact_id: str):
    """Get all contact persons for a contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    persons = await contact_persons_collection.find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).sort("is_primary", -1).to_list(50)
    
    return {"code": 0, "persons": persons}

@router.post("/{contact_id}/persons")
async def add_contact_person(contact_id: str, person: ContactPersonCreate):
    """Add a contact person to contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # If setting as primary, unset existing primary
    if person.is_primary:
        await contact_persons_collection.update_many(
            {"contact_id": contact_id},
            {"$set": {"is_primary": False}}
        )
    
    person_id = generate_id("PER")
    
    person_doc = {
        "person_id": person_id,
        "contact_id": contact_id,
        **person.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await contact_persons_collection.insert_one(person_doc)
    
    # Update count
    count = await contact_persons_collection.count_documents({"contact_id": contact_id})
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"contact_persons_count": count, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_contact_history(contact_id, "person_added", f"Contact person {person.first_name} added")
    
    person_doc.pop("_id", None)
    return {"code": 0, "message": "Person added", "person": person_doc}

@router.put("/{contact_id}/persons/{person_id}")
async def update_contact_person(contact_id: str, person_id: str, person: ContactPersonUpdate):
    """Update a contact person"""
    existing = await contact_persons_collection.find_one({"person_id": person_id, "contact_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    
    update_data = {k: v for k, v in person.dict().items() if v is not None}
    
    # If setting as primary, unset existing primary
    if update_data.get("is_primary"):
        await contact_persons_collection.update_many(
            {"contact_id": contact_id, "person_id": {"$ne": person_id}},
            {"$set": {"is_primary": False}}
        )
    
    if update_data:
        await contact_persons_collection.update_one({"person_id": person_id}, {"$set": update_data})
    
    updated = await contact_persons_collection.find_one({"person_id": person_id}, {"_id": 0})
    return {"code": 0, "message": "Person updated", "person": updated}

@router.delete("/{contact_id}/persons/{person_id}")
async def delete_contact_person(contact_id: str, person_id: str):
    """Delete a contact person"""
    result = await contact_persons_collection.delete_one({"person_id": person_id, "contact_id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Update count
    count = await contact_persons_collection.count_documents({"contact_id": contact_id})
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"contact_persons_count": count, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_contact_history(contact_id, "person_deleted", "Contact person deleted")
    
    return {"code": 0, "message": "Person deleted"}

@router.post("/{contact_id}/persons/{person_id}/set-primary")
async def set_primary_person(contact_id: str, person_id: str):
    """Set a person as primary contact"""
    existing = await contact_persons_collection.find_one({"person_id": person_id, "contact_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    
    await contact_persons_collection.update_many(
        {"contact_id": contact_id},
        {"$set": {"is_primary": False}}
    )
    await contact_persons_collection.update_one(
        {"person_id": person_id},
        {"$set": {"is_primary": True}}
    )
    
    return {"code": 0, "message": "Primary contact set"}

# ========================= ADDRESSES =========================

@router.get("/{contact_id}/addresses")
async def get_contact_addresses(contact_id: str, address_type: Optional[str] = None):
    """Get all addresses for a contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    query = {"contact_id": contact_id}
    if address_type:
        query["address_type"] = address_type
    
    addresses = await addresses_collection.find(query, {"_id": 0}).to_list(20)
    
    return {"code": 0, "addresses": addresses}

@router.post("/{contact_id}/addresses")
async def add_contact_address(contact_id: str, address: AddressCreate):
    """Add an address to contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # If setting as default, unset existing default of same type
    if address.is_default:
        await addresses_collection.update_many(
            {"contact_id": contact_id, "address_type": address.address_type},
            {"$set": {"is_default": False}}
        )
    
    address_id = generate_id("ADDR")
    
    address_doc = {
        "address_id": address_id,
        "contact_id": contact_id,
        **address.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await addresses_collection.insert_one(address_doc)
    
    # Update flags
    has_billing = await addresses_collection.count_documents({"contact_id": contact_id, "address_type": "billing"}) > 0
    has_shipping = await addresses_collection.count_documents({"contact_id": contact_id, "address_type": "shipping"}) > 0
    count = await addresses_collection.count_documents({"contact_id": contact_id})
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {
            "has_billing_address": has_billing,
            "has_shipping_address": has_shipping,
            "addresses_count": count,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_contact_history(contact_id, "address_added", f"{address.address_type.title()} address added")
    
    address_doc.pop("_id", None)
    return {"code": 0, "message": "Address added", "address": address_doc}

@router.put("/{contact_id}/addresses/{address_id}")
async def update_contact_address(contact_id: str, address_id: str, address: AddressUpdate):
    """Update an address"""
    existing = await addresses_collection.find_one({"address_id": address_id, "contact_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Address not found")
    
    update_data = {k: v for k, v in address.dict().items() if v is not None}
    
    # If setting as default, unset existing default of same type
    if update_data.get("is_default"):
        addr_type = update_data.get("address_type") or existing.get("address_type")
        await addresses_collection.update_many(
            {"contact_id": contact_id, "address_type": addr_type, "address_id": {"$ne": address_id}},
            {"$set": {"is_default": False}}
        )
    
    if update_data:
        await addresses_collection.update_one({"address_id": address_id}, {"$set": update_data})
    
    updated = await addresses_collection.find_one({"address_id": address_id}, {"_id": 0})
    return {"code": 0, "message": "Address updated", "address": updated}

@router.delete("/{contact_id}/addresses/{address_id}")
async def delete_contact_address(contact_id: str, address_id: str):
    """Delete an address"""
    result = await addresses_collection.delete_one({"address_id": address_id, "contact_id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    
    # Update flags
    has_billing = await addresses_collection.count_documents({"contact_id": contact_id, "address_type": "billing"}) > 0
    has_shipping = await addresses_collection.count_documents({"contact_id": contact_id, "address_type": "shipping"}) > 0
    count = await addresses_collection.count_documents({"contact_id": contact_id})
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {
            "has_billing_address": has_billing,
            "has_shipping_address": has_shipping,
            "addresses_count": count,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_contact_history(contact_id, "address_deleted", "Address deleted")
    
    return {"code": 0, "message": "Address deleted"}

# ========================= STATUS MANAGEMENT =========================

@router.post("/{contact_id}/activate")
async def activate_contact(contact_id: str):
    """Activate an inactive contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"is_active": True, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_contact_history(contact_id, "activated", "Contact activated")
    
    return {"code": 0, "message": "Contact activated"}

@router.post("/{contact_id}/deactivate")
async def deactivate_contact(contact_id: str):
    """Deactivate a contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Check for pending transactions (only for customers)
    if contact.get("contact_type") in ["customer", "both"]:
        pending_invoices = await db["invoices"].count_documents({
            "$or": [{"customer_id": contact_id}, {"contact_id": contact_id}],
            "status": {"$in": ["draft", "sent", "partially_paid"]},
            "balance_due": {"$gt": 0}
        })
        
        if pending_invoices > 0:
            raise HTTPException(status_code=400, detail=f"Contact has {pending_invoices} pending invoices. Clear them before deactivating.")
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"is_active": False, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_contact_history(contact_id, "deactivated", "Contact deactivated")
    
    return {"code": 0, "message": "Contact deactivated"}

# ========================= PORTAL ACCESS =========================

@router.post("/{contact_id}/enable-portal")
async def enable_contact_portal(contact_id: str, email_to: Optional[str] = None):
    """Enable portal access for contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    recipient = email_to or contact.get("email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    portal_token = str(uuid.uuid4())
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {
            "portal_enabled": True,
            "portal_token": portal_token,
            "portal_enabled_time": datetime.now(timezone.utc).isoformat(),
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send portal invite (mocked)
    mock_send_email(
        recipient,
        "Portal Access Enabled - Battwheels",
        f"Dear {contact.get('name')},\n\nYour portal has been enabled.\nAccess Token: {portal_token}",
        ""
    )
    
    await add_contact_history(contact_id, "portal_enabled", f"Portal enabled, invite sent to {recipient}")
    
    return {"code": 0, "message": f"Portal enabled, invite sent to {recipient}", "token": portal_token}

@router.post("/{contact_id}/disable-portal")
async def disable_contact_portal(contact_id: str):
    """Disable portal access for contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {
            "portal_enabled": False,
            "portal_token": "",
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_contact_history(contact_id, "portal_disabled", "Portal access disabled")
    
    return {"code": 0, "message": "Portal disabled"}

@router.post("/{contact_id}/resend-portal-invite")
async def resend_portal_invite(contact_id: str, email_to: Optional[str] = None):
    """Resend portal invite email"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    if not contact.get("portal_enabled"):
        raise HTTPException(status_code=400, detail="Portal not enabled")
    
    recipient = email_to or contact.get("email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    mock_send_email(
        recipient,
        "Portal Access Reminder - Battwheels",
        f"Dear {contact.get('name')},\n\nYour portal token: {contact.get('portal_token')}",
        ""
    )
    
    await add_contact_history(contact_id, "portal_invite_resent", f"Portal invite resent to {recipient}")
    
    return {"code": 0, "message": f"Portal invite resent to {recipient}"}

@router.post("/portal/validate-token")
async def validate_portal_token(token: str):
    """Validate a portal token (for portal login simulation)"""
    contact = await contacts_collection.find_one(
        {"portal_token": token, "portal_enabled": True},
        {"_id": 0, "contact_id": 1, "name": 1, "email": 1, "company_name": 1, "contact_type": 1}
    )
    if not contact:
        raise HTTPException(status_code=401, detail="Invalid or expired portal token")
    
    # Update last login
    await contacts_collection.update_one(
        {"portal_token": token},
        {"$set": {"portal_last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": "Token valid", "contact": contact}

# ========================= STATEMENTS =========================

@router.post("/{contact_id}/email-statement")
async def email_contact_statement(contact_id: str, request: StatementRequest):
    """Email account statement to contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    recipient = request.email_to or contact.get("email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    # Get transactions for statement
    query = {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]}
    if request.start_date:
        query["date"] = {"$gte": request.start_date}
    if request.end_date:
        if "date" in query:
            query["date"]["$lte"] = request.end_date
        else:
            query["date"] = {"$lte": request.end_date}
    
    invoices = await db["invoices"].find(query, {"_id": 0, "invoice_number": 1, "date": 1, "total": 1, "balance_due": 1}).to_list(500)
    
    # Get balance
    balance = await calculate_contact_balance(contact_id)
    
    # Generate PDF (mocked)
    pdf_data = mock_generate_pdf({
        "contact_id": contact_id,
        "contact_name": contact.get("name"),
        "invoices": invoices,
        "balance": balance,
        "start_date": request.start_date,
        "end_date": request.end_date
    }, "statement")
    
    # Send email (mocked)
    mock_send_email(
        recipient,
        f"Account Statement - {contact.get('name')} - Battwheels",
        f"Dear {contact.get('name')},\n\nPlease find attached your account statement.\n\nCurrent Outstanding: ₹{balance.get('net_receivable', 0):,.2f}",
        f"Statement_{contact.get('contact_number')}.pdf"
    )
    
    # Log statement
    statement_record = {
        "statement_id": generate_id("STMT"),
        "contact_id": contact_id,
        "generated_time": datetime.now(timezone.utc).isoformat(),
        "balance": balance,
        "email_sent_to": recipient,
        "date_range": {"start": request.start_date, "end": request.end_date}
    }
    await contact_statements_collection.insert_one(statement_record)
    
    await add_contact_history(contact_id, "statement_sent", f"Statement emailed to {recipient}")
    
    return {"code": 0, "message": f"Statement sent to {recipient}"}

@router.get("/{contact_id}/statement")
async def get_contact_statement(contact_id: str, start_date: str = "", end_date: str = ""):
    """Get contact statement data"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    query = {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
    
    # Get invoices (legacy and enhanced)
    invoices = await db["invoices"].find(query, {"_id": 0}).sort("date", 1).to_list(500)
    invoices_enhanced = await db["invoices_enhanced"].find(
        {"customer_id": contact_id}, {"_id": 0}
    ).sort("invoice_date", 1).to_list(500)
    
    # Combine invoices
    all_invoices = []
    for inv in invoices:
        all_invoices.append({
            "type": "invoice",
            "date": inv.get("date"),
            "number": inv.get("invoice_number"),
            "description": f"Invoice #{inv.get('invoice_number')}",
            "debit": inv.get("grand_total", 0),
            "credit": 0,
            "status": inv.get("status")
        })
    for inv in invoices_enhanced:
        all_invoices.append({
            "type": "invoice",
            "date": inv.get("invoice_date"),
            "number": inv.get("invoice_number"),
            "description": f"Invoice #{inv.get('invoice_number')}",
            "debit": inv.get("grand_total", 0),
            "credit": 0,
            "status": inv.get("status")
        })
    
    # Get payments (legacy)
    payments = await db["payments"].find(
        {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]},
        {"_id": 0}
    ).sort("date", 1).to_list(500)
    
    # Get payments from payments_received module
    payments_received = await db["payments_received"].find(
        {"customer_id": contact_id, "status": {"$ne": "refunded"}},
        {"_id": 0}
    ).sort("payment_date", 1).to_list(500)
    
    # Combine payments
    all_payments = []
    for p in payments:
        all_payments.append({
            "type": "payment",
            "date": p.get("date"),
            "number": p.get("payment_number"),
            "description": f"Payment #{p.get('payment_number')} ({p.get('payment_mode', '')})",
            "debit": 0,
            "credit": p.get("amount", 0),
            "payment_mode": p.get("payment_mode")
        })
    for p in payments_received:
        all_payments.append({
            "type": "payment",
            "date": p.get("payment_date"),
            "number": p.get("payment_number"),
            "description": f"Payment #{p.get('payment_number')} ({p.get('payment_mode', '')})",
            "debit": 0,
            "credit": p.get("amount", 0),
            "payment_mode": p.get("payment_mode"),
            "reference_number": p.get("reference_number")
        })
    
    # Get credits
    credits = await contact_credits_collection.find({"contact_id": contact_id}, {"_id": 0}).to_list(100)
    
    # Get customer credits from payments_received module
    customer_credits = await db["customer_credits"].find(
        {"customer_id": contact_id},
        {"_id": 0}
    ).to_list(100)
    
    # Build statement lines (chronological)
    statement_lines = sorted(all_invoices + all_payments, key=lambda x: x.get("date", ""))
    
    # Calculate running balance
    running_balance = 0
    for line in statement_lines:
        running_balance += line.get("debit", 0) - line.get("credit", 0)
        line["balance"] = running_balance
    
    # Calculate balance
    balance = await calculate_contact_balance(contact_id)
    aging = await get_contact_aging(contact_id, "receivable")
    
    # Get available credits
    available_credits = [c for c in customer_credits if c.get("status") == "available"]
    total_available_credits = sum(c.get("amount", 0) for c in available_credits)
    
    return {
        "code": 0,
        "statement": {
            "contact": {
                "contact_id": contact_id,
                "name": contact.get("name"),
                "display_name": contact.get("display_name"),
                "contact_number": contact.get("contact_number"),
                "email": contact.get("email"),
                "gstin": contact.get("gstin"),
                "credit_limit": contact.get("credit_limit", 0)
            },
            "period": {"start_date": start_date, "end_date": end_date},
            "statement_lines": statement_lines,
            "invoices": invoices + invoices_enhanced,
            "payments": all_payments,
            "credits": credits,
            "customer_credits": customer_credits,
            "available_credits": available_credits,
            "total_available_credits": total_available_credits,
            "balance": balance,
            "aging": aging,
            "summary": {
                "total_invoiced": sum(line.get("debit", 0) for line in statement_lines),
                "total_paid": sum(line.get("credit", 0) for line in statement_lines),
                "closing_balance": running_balance,
                "available_credits": total_available_credits
            }
        }
    }

@router.get("/{contact_id}/statement-history")
async def get_statement_history(contact_id: str):
    """Get history of generated statements"""
    statements = await contact_statements_collection.find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).sort("generated_time", -1).limit(50).to_list(50)
    return {"code": 0, "statements": statements}

# ========================= CREDITS & REFUNDS =========================

@router.get("/{contact_id}/credits")
async def get_contact_credits(contact_id: str):
    """Get contact credits"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    credits = await contact_credits_collection.find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).sort("created_time", -1).to_list(100)
    
    return {"code": 0, "credits": credits}

@router.post("/{contact_id}/credits")
async def add_contact_credit(contact_id: str, credit: CreditNoteCreate):
    """Add a credit note to contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    credit_id = generate_id("CRED")
    
    credit_doc = {
        "credit_id": credit_id,
        "contact_id": contact_id,
        "amount": credit.amount,
        "used_amount": 0,
        "balance": credit.amount,
        "reason": credit.reason,
        "reference_number": credit.reference_number,
        "date": credit.date or datetime.now(timezone.utc).date().isoformat(),
        "status": "active",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await contact_credits_collection.insert_one(credit_doc)
    
    # Update unused credits on contact
    total_credits = await contact_credits_collection.aggregate([
        {"$match": {"contact_id": contact_id, "status": "active"}},
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    
    unused = total_credits[0]["total"] if total_credits else 0
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"unused_credits": unused, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_contact_history(contact_id, "credit_added", f"Credit of ₹{credit.amount} added")
    
    credit_doc.pop("_id", None)
    return {"code": 0, "message": "Credit added", "credit": credit_doc}

@router.post("/{contact_id}/refunds")
async def create_contact_refund(contact_id: str, refund: RefundCreate):
    """Create a refund for contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Check available credits
    credits = await contact_credits_collection.find(
        {"contact_id": contact_id, "status": "active", "balance": {"$gt": 0}},
        {"_id": 0}
    ).to_list(100)
    
    available = sum(c.get("balance", 0) for c in credits)
    if available < refund.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient credits. Available: ₹{available}")
    
    refund_id = generate_id("REF")
    
    refund_doc = {
        "refund_id": refund_id,
        "contact_id": contact_id,
        "amount": refund.amount,
        "mode": refund.mode,
        "reference_number": refund.reference_number,
        "date": refund.date or datetime.now(timezone.utc).date().isoformat(),
        "notes": refund.notes,
        "status": "completed",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await contact_refunds_collection.insert_one(refund_doc)
    
    # Deduct from credits
    remaining = refund.amount
    for credit in credits:
        if remaining <= 0:
            break
        deduct = min(credit.get("balance", 0), remaining)
        await contact_credits_collection.update_one(
            {"credit_id": credit["credit_id"]},
            {"$inc": {"used_amount": deduct, "balance": -deduct}}
        )
        remaining -= deduct
    
    # Update unused credits on contact
    total_credits = await contact_credits_collection.aggregate([
        {"$match": {"contact_id": contact_id, "status": "active"}},
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    
    unused = total_credits[0]["total"] if total_credits else 0
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"unused_credits": unused, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_contact_history(contact_id, "refund_created", f"Refund of ₹{refund.amount} processed")
    
    refund_doc.pop("_id", None)
    return {"code": 0, "message": "Refund created", "refund": refund_doc}

# ========================= TAG MANAGEMENT ON CONTACTS =========================

@router.post("/{contact_id}/tags/{tag_name}")
async def add_tag_to_contact(contact_id: str, tag_name: str):
    """Add a tag to contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$addToSet": {"tags": tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update tag count
    count = await contacts_collection.count_documents({"tags": tag_name})
    await contact_tags_collection.update_one({"name": tag_name}, {"$set": {"contact_count": count}}, upsert=True)
    
    return {"code": 0, "message": "Tag added"}

@router.delete("/{contact_id}/tags/{tag_name}")
async def remove_tag_from_contact(contact_id: str, tag_name: str):
    """Remove a tag from contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$pull": {"tags": tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update tag count
    count = await contacts_collection.count_documents({"tags": tag_name})
    await contact_tags_collection.update_one({"name": tag_name}, {"$set": {"contact_count": count}})
    
    return {"code": 0, "message": "Tag removed"}

# ========================= TRANSACTIONS =========================

@router.get("/{contact_id}/transactions")
async def get_contact_transactions(contact_id: str, transaction_type: str = "all", limit: int = 50):
    """Get contact's transaction history"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    transactions = []
    
    if transaction_type in ["all", "estimate"]:
        estimates = await db["estimates_enhanced"].find(
            {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]},
            {"_id": 0, "estimate_id": 1, "estimate_number": 1, "date": 1, "grand_total": 1, "status": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for e in estimates:
            e["transaction_type"] = "estimate"
        transactions.extend(estimates)
    
    if transaction_type in ["all", "salesorder"]:
        salesorders = await db["salesorders_enhanced"].find(
            {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]},
            {"_id": 0, "salesorder_id": 1, "salesorder_number": 1, "date": 1, "grand_total": 1, "status": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for so in salesorders:
            so["transaction_type"] = "salesorder"
        transactions.extend(salesorders)
    
    if transaction_type in ["all", "invoice"]:
        invoices = await db["invoices"].find(
            {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]},
            {"_id": 0, "invoice_id": 1, "invoice_number": 1, "date": 1, "total": 1, "balance_due": 1, "status": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for inv in invoices:
            inv["transaction_type"] = "invoice"
        transactions.extend(invoices)
    
    if transaction_type in ["all", "bill"]:
        bills = await db["bills"].find(
            {"$or": [{"vendor_id": contact_id}, {"contact_id": contact_id}]},
            {"_id": 0, "bill_id": 1, "bill_number": 1, "date": 1, "total": 1, "balance_due": 1, "status": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for bill in bills:
            bill["transaction_type"] = "bill"
        transactions.extend(bills)
    
    if transaction_type in ["all", "payment"]:
        payments = await db["payments"].find(
            {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]},
            {"_id": 0, "payment_id": 1, "payment_number": 1, "date": 1, "amount": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for p in payments:
            p["transaction_type"] = "payment"
        transactions.extend(payments)
    
    # Sort by date descending
    transactions.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return {"code": 0, "transactions": transactions[:limit]}

# ========================= BULK OPERATIONS =========================

@router.post("/bulk-action")
async def bulk_contact_action(request: BulkActionRequest):
    """Perform bulk action on contacts"""
    action = request.action
    contact_ids = request.contact_ids
    
    if not contact_ids:
        raise HTTPException(status_code=400, detail="No contacts selected")
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    for contact_id in contact_ids:
        try:
            if action == "activate":
                await contacts_collection.update_one(
                    {"contact_id": contact_id},
                    {"$set": {"is_active": True, "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            elif action == "deactivate":
                await contacts_collection.update_one(
                    {"contact_id": contact_id},
                    {"$set": {"is_active": False, "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            elif action == "delete":
                usage = await is_contact_used_in_transactions(contact_id)
                if usage["is_used"]:
                    results["errors"].append(f"{contact_id}: Has transactions")
                    results["failed"] += 1
                else:
                    await contact_persons_collection.delete_many({"contact_id": contact_id})
                    await addresses_collection.delete_many({"contact_id": contact_id})
                    await contacts_collection.delete_one({"contact_id": contact_id})
                    results["success"] += 1
            
            elif action == "add_tag" and request.tag_name:
                await contacts_collection.update_one(
                    {"contact_id": contact_id},
                    {"$addToSet": {"tags": request.tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            elif action == "remove_tag" and request.tag_name:
                await contacts_collection.update_one(
                    {"contact_id": contact_id},
                    {"$pull": {"tags": request.tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            else:
                results["errors"].append(f"Unknown action: {action}")
                results["failed"] += 1
        
        except Exception as e:
            results["errors"].append(f"{contact_id}: {str(e)}")
            results["failed"] += 1
    
    return {"code": 0, "results": results}

@router.post("/bulk/import")
async def bulk_import_contacts(contacts: List[ContactCreate]):
    """Bulk import contacts"""
    created = []
    errors = []
    
    for i, contact in enumerate(contacts):
        try:
            result = await create_contact(contact, BackgroundTasks())
            created.append(result["contact"]["contact_id"])
        except Exception as e:
            errors.append({"index": i, "name": contact.name, "error": str(e)})
    
    return {
        "code": 0,
        "message": f"Imported {len(created)} contacts",
        "created_ids": created,
        "errors": errors
    }

@router.post("/bulk/update-tags")
async def bulk_update_tags(contact_ids: List[str], tags: List[str], action: str = "add"):
    """Bulk add/remove tags from contacts"""
    if action not in ["add", "remove", "set"]:
        raise HTTPException(status_code=400, detail="Action must be 'add', 'remove', or 'set'")
    
    updated = 0
    for contact_id in contact_ids:
        if action == "add":
            result = await contacts_collection.update_one(
                {"contact_id": contact_id},
                {"$addToSet": {"tags": {"$each": tags}}}
            )
        elif action == "remove":
            result = await contacts_collection.update_one(
                {"contact_id": contact_id},
                {"$pull": {"tags": {"$in": tags}}}
            )
        else:  # set
            result = await contacts_collection.update_one(
                {"contact_id": contact_id},
                {"$set": {"tags": tags}}
            )
        updated += result.modified_count
    
    return {"code": 0, "message": f"Updated {updated} contacts", "action": action}

@router.post("/bulk/activate")
async def bulk_activate(contact_ids: List[str], activate: bool = True):
    """Bulk activate/deactivate contacts"""
    result = await contacts_collection.update_many(
        {"contact_id": {"$in": contact_ids}},
        {"$set": {"is_active": activate, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    return {"code": 0, "message": f"Updated {result.modified_count} contacts", "is_active": activate}

# ========================= QUICK ACTIONS =========================

@router.post("/{contact_id}/quick-estimate")
async def create_quick_estimate_for_contact(contact_id: str):
    """Quick action: Create estimate for contact - returns URL params"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {
        "code": 0,
        "redirect": f"/estimates?customer_id={contact_id}&customer_name={contact.get('name', '')}",
        "message": "Navigate to estimates with contact pre-filled"
    }

@router.post("/{contact_id}/quick-invoice")
async def create_quick_invoice_for_contact(contact_id: str):
    """Quick action: Create invoice for contact - returns URL params"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {
        "code": 0,
        "redirect": f"/invoices?customer_id={contact_id}&customer_name={contact.get('name', '')}",
        "message": "Navigate to invoices with contact pre-filled"
    }

@router.post("/{contact_id}/quick-bill")
async def create_quick_bill_for_contact(contact_id: str):
    """Quick action: Create bill for vendor contact - returns URL params"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    if contact.get("contact_type") not in ["vendor", "both"]:
        raise HTTPException(status_code=400, detail="Contact is not a vendor")
    
    return {
        "code": 0,
        "redirect": f"/bills?vendor_id={contact_id}&vendor_name={contact.get('name', '')}",
        "message": "Navigate to bills with vendor pre-filled"
    }

# ==================== CONTACT ACTIVITY LOG ====================

@router.get("/{contact_id}/activity")
async def get_contact_activity(contact_id: str, limit: int = 50):
    """Get activity log for a contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Get from contact history collection
    history = await db["contact_history"].find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # If no history, create activity from related transactions
    if not history:
        activities = []
        
        # Add creation activity
        activities.append({
            "action": "created",
            "details": f"Contact {contact.get('display_name', '')} was created",
            "timestamp": contact.get("created_time", "")
        })
        
        # Get recent invoices
        invoices = await db["invoices_enhanced"].find(
            {"customer_id": contact_id},
            {"_id": 0, "invoice_number": 1, "grand_total": 1, "created_time": 1}
        ).sort("created_time", -1).limit(5).to_list(5)
        
        for inv in invoices:
            activities.append({
                "action": "invoice_created",
                "details": f"Invoice {inv.get('invoice_number', '')} created for ₹{inv.get('grand_total', 0):,.2f}",
                "timestamp": inv.get("created_time", ""),
                "related_type": "invoice",
                "related_id": inv.get("invoice_id", "")
            })
        
        # Get recent payments
        payments = await db["payments_received"].find(
            {"customer_id": contact_id},
            {"_id": 0, "payment_number": 1, "amount": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        for pmt in payments:
            activities.append({
                "action": "payment_received",
                "details": f"Payment {pmt.get('payment_number', '')} of ₹{pmt.get('amount', 0):,.2f} received",
                "timestamp": pmt.get("created_at", ""),
                "related_type": "payment",
                "related_id": pmt.get("payment_id", "")
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"code": 0, "activities": activities[:limit]}
    
    return {"code": 0, "activities": history}

async def add_contact_history(contact_id: str, action: str, details: str):
    """Add entry to contact history"""
    from datetime import datetime, timezone
    await db["contact_history"].insert_one({
        "history_id": f"CHIST-{uuid.uuid4().hex[:12].upper()}",
        "contact_id": contact_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
