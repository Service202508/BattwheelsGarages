# Enhanced Customers Module for Zoho Books Clone
# Full customer management with Zoho-like features, GST compliance, and transaction linkages

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import motor.motor_asyncio
import os
import uuid
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers-enhanced", tags=["Customers Enhanced"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
customers_collection = db["customers_enhanced"]
customer_persons_collection = db["customer_persons"]
customer_addresses_collection = db["customer_addresses"]
customer_tags_collection = db["customer_tags"]
customer_history_collection = db["customer_history"]
customer_settings_collection = db["customer_settings"]
customer_credits_collection = db["customer_credits"]
customer_refunds_collection = db["customer_refunds"]

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
    "37": {"code": "AP", "name": "Andhra Pradesh (New)"}
}

ORG_STATE_CODE = "DL"  # Organization state

# ========================= PYDANTIC MODELS =========================

class PersonCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    designation: str = ""
    department: str = ""
    is_primary: bool = False
    salutation: str = ""
    notes: str = ""

class PersonUpdate(BaseModel):
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

class CustomerCreate(BaseModel):
    display_name: str = Field(..., min_length=1)
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
    # Classification
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

class CustomerUpdate(BaseModel):
    display_name: Optional[str] = None
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

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    color: str = "#3B82F6"

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
    customer_ids: List[str]
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
    
    # GSTIN format: 2 digits state + 10 char PAN + 1 entity + 1 Z + 1 checksum
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
    
    # Entity types
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

async def calculate_customer_balance(customer_id: str) -> dict:
    """Calculate customer's current balance from transactions"""
    # Get all invoices
    invoices = await db["invoices"].find(
        {"customer_id": customer_id, "status": {"$ne": "void"}},
        {"total": 1, "balance_due": 1, "status": 1}
    ).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_outstanding = sum(inv.get("balance_due", 0) for inv in invoices)
    
    # Get customer credits
    credits = await customer_credits_collection.find(
        {"customer_id": customer_id, "status": "active"},
        {"amount": 1, "used_amount": 1}
    ).to_list(100)
    
    total_credits = sum(c.get("amount", 0) - c.get("used_amount", 0) for c in credits)
    
    # Get payments received
    payments = await db["payments"].find(
        {"customer_id": customer_id},
        {"amount": 1}
    ).to_list(1000)
    
    total_payments = sum(p.get("amount", 0) for p in payments)
    
    return {
        "total_invoiced": round(total_invoiced, 2),
        "total_outstanding": round(total_outstanding, 2),
        "total_credits": round(total_credits, 2),
        "total_payments": round(total_payments, 2),
        "net_balance": round(total_outstanding - total_credits, 2)
    }

async def get_customer_aging(customer_id: str) -> dict:
    """Calculate aging buckets for customer"""
    today = datetime.now(timezone.utc).date()
    
    invoices = await db["invoices"].find(
        {"customer_id": customer_id, "status": {"$in": ["sent", "overdue", "partially_paid"]}, "balance_due": {"$gt": 0}},
        {"_id": 0, "invoice_number": 1, "due_date": 1, "balance_due": 1}
    ).to_list(1000)
    
    aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    
    for inv in invoices:
        due_date_str = inv.get("due_date", "")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.fromisoformat(due_date_str).date()
            days_overdue = (today - due_date).days
            balance = inv.get("balance_due", 0)
            
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

async def is_customer_used_in_transactions(customer_id: str) -> dict:
    """Check if customer is linked to any transactions"""
    # Check both by customer_id and contact_id (for cross-module compatibility)
    estimates_count = await db["estimates_enhanced"].count_documents(
        {"$or": [{"customer_id": customer_id}, {"contact_id": customer_id}]}
    )
    salesorders_count = await db["salesorders_enhanced"].count_documents(
        {"$or": [{"customer_id": customer_id}, {"contact_id": customer_id}]}
    )
    invoices_count = await db["invoices"].count_documents(
        {"$or": [{"customer_id": customer_id}, {"contact_id": customer_id}]}
    )
    
    # Also check if this customer exists in contacts_enhanced (linked)
    contacts_enhanced = await db["contacts_enhanced"].find_one(
        {"$or": [{"contact_id": customer_id}, {"linked_customer_id": customer_id}]}
    )
    has_contact_link = contacts_enhanced is not None
    
    is_used = estimates_count > 0 or salesorders_count > 0 or invoices_count > 0
    
    return {
        "is_used": is_used,
        "estimates_count": estimates_count,
        "salesorders_count": salesorders_count,
        "invoices_count": invoices_count,
        "total_transactions": estimates_count + salesorders_count + invoices_count,
        "has_contact_link": has_contact_link
    }

async def add_customer_history(customer_id: str, action: str, details: str, user_id: str = ""):
    """Add entry to customer history"""
    history_entry = {
        "history_id": generate_id("CUSTHIST"),
        "customer_id": customer_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await customer_history_collection.insert_one(history_entry)

def mock_send_email(to_email: str, subject: str, body: str, attachment_name: str = ""):
    """Mock email sending - logs instead of actual send"""
    logger.info(f"[MOCK EMAIL] To: {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Attachment: {attachment_name}")
    logger.info(f"[MOCK EMAIL] Body Preview: {body[:200]}...")
    return True

def mock_generate_pdf(data: dict, template: str = "statement") -> bytes:
    """Mock PDF generation"""
    logger.info(f"[MOCK PDF] Generating {template} PDF for customer {data.get('customer_id', 'unknown')}")
    return b"PDF_CONTENT_MOCK"

async def get_next_customer_number() -> str:
    """Generate next customer number"""
    settings = await customer_settings_collection.find_one({"type": "numbering"})
    if not settings:
        settings = {"type": "numbering", "prefix": "CUST-", "next_number": 1, "padding": 5}
        await customer_settings_collection.insert_one(settings)
    
    number = str(settings["next_number"]).zfill(settings.get("padding", 5))
    next_num = f"{settings.get('prefix', 'CUST-')}{number}"
    
    await customer_settings_collection.update_one(
        {"type": "numbering"},
        {"$inc": {"next_number": 1}}
    )
    
    return next_num

# ========================= SETTINGS ENDPOINTS =========================

@router.get("/settings")
async def get_customer_settings():
    """Get customer module settings"""
    numbering = await customer_settings_collection.find_one({"type": "numbering"}, {"_id": 0})
    defaults = await customer_settings_collection.find_one({"type": "defaults"}, {"_id": 0})
    
    if not numbering:
        numbering = {"type": "numbering", "prefix": "CUST-", "next_number": 1, "padding": 5}
    if not defaults:
        defaults = {
            "type": "defaults",
            "payment_terms": 30,
            "credit_limit": 0,
            "currency_code": "INR",
            "gst_treatment": "registered",
            "portal_enabled_by_default": False
        }
    
    return {"code": 0, "settings": {"numbering": numbering, "defaults": defaults}}

@router.put("/settings")
async def update_customer_settings(settings: dict):
    """Update customer module settings"""
    if "numbering" in settings:
        await customer_settings_collection.update_one(
            {"type": "numbering"},
            {"$set": settings["numbering"]},
            upsert=True
        )
    if "defaults" in settings:
        await customer_settings_collection.update_one(
            {"type": "defaults"},
            {"$set": settings["defaults"]},
            upsert=True
        )
    return {"code": 0, "message": "Settings updated"}

# ========================= GSTIN VALIDATION =========================

@router.get("/validate-gstin/{gstin}")
async def validate_gstin_endpoint(gstin: str):
    """Validate GSTIN and return parsed information"""
    result = validate_gstin(gstin)
    return {"code": 0 if result["valid"] else 1, "result": result}

# ========================= SYNC CHECK ENDPOINT =========================

@router.get("/check-sync")
async def check_customers_sync():
    """Audit customers against Zoho-like features and check data quality"""
    total = await customers_collection.count_documents({})
    active = await customers_collection.count_documents({"is_active": True})
    inactive = await customers_collection.count_documents({"is_active": False})
    
    # Data quality checks
    missing_gstin = await customers_collection.count_documents({"gstin": {"$in": ["", None]}, "gst_treatment": "registered"})
    missing_email = await customers_collection.count_documents({"email": {"$in": ["", None]}})
    missing_phone = await customers_collection.count_documents({"phone": {"$in": ["", None]}, "mobile": {"$in": ["", None]}})
    missing_address = await customers_collection.count_documents({"$or": [{"has_billing_address": False}, {"has_billing_address": {"$exists": False}}]})
    
    # Linkage stats
    pipeline = [
        {"$lookup": {"from": "estimates_enhanced", "localField": "customer_id", "foreignField": "customer_id", "as": "estimates"}},
        {"$lookup": {"from": "salesorders_enhanced", "localField": "customer_id", "foreignField": "customer_id", "as": "salesorders"}},
        {"$lookup": {"from": "invoices", "localField": "customer_id", "foreignField": "customer_id", "as": "invoices"}},
        {"$project": {
            "customer_id": 1,
            "has_estimates": {"$gt": [{"$size": "$estimates"}, 0]},
            "has_salesorders": {"$gt": [{"$size": "$salesorders"}, 0]},
            "has_invoices": {"$gt": [{"$size": "$invoices"}, 0]}
        }},
        {"$group": {
            "_id": None,
            "with_estimates": {"$sum": {"$cond": ["$has_estimates", 1, 0]}},
            "with_salesorders": {"$sum": {"$cond": ["$has_salesorders", 1, 0]}},
            "with_invoices": {"$sum": {"$cond": ["$has_invoices", 1, 0]}}
        }}
    ]
    
    linkage_stats = await customers_collection.aggregate(pipeline).to_list(1)
    linkage = linkage_stats[0] if linkage_stats else {"with_estimates": 0, "with_salesorders": 0, "with_invoices": 0}
    
    # Portal stats
    portal_enabled = await customers_collection.count_documents({"portal_enabled": True})
    
    # GST treatment breakdown
    gst_breakdown = {}
    for treatment in ["registered", "unregistered", "consumer", "overseas", "sez"]:
        count = await customers_collection.count_documents({"gst_treatment": treatment})
        gst_breakdown[treatment] = count
    
    # Suggestions for data cleanup
    suggestions = []
    if missing_gstin > 0:
        suggestions.append(f"Update GSTIN for {missing_gstin} registered customers")
    if missing_email > 0:
        suggestions.append(f"Add email for {missing_email} customers to enable portal/statements")
    if missing_address > 0:
        suggestions.append(f"Add billing address for {missing_address} customers")
    
    return {
        "code": 0,
        "sync_report": {
            "summary": {
                "total_customers": total,
                "active": active,
                "inactive": inactive
            },
            "data_quality": {
                "missing_gstin_registered": missing_gstin,
                "missing_email": missing_email,
                "missing_phone": missing_phone,
                "missing_billing_address": missing_address
            },
            "linkages": {
                "linked_to_estimates": linkage.get("with_estimates", 0),
                "linked_to_salesorders": linkage.get("with_salesorders", 0),
                "linked_to_invoices": linkage.get("with_invoices", 0),
                "no_transactions": total - max(linkage.get("with_estimates", 0), linkage.get("with_salesorders", 0), linkage.get("with_invoices", 0))
            },
            "portal": {
                "enabled": portal_enabled,
                "not_enabled": total - portal_enabled
            },
            "gst_treatment_breakdown": gst_breakdown,
            "suggestions": suggestions
        }
    }

# ========================= SUMMARY ENDPOINT =========================

@router.get("/summary")
async def get_customers_summary():
    """Get customers summary statistics"""
    total = await customers_collection.count_documents({})
    active = await customers_collection.count_documents({"is_active": True})
    inactive = await customers_collection.count_documents({"is_active": False})
    with_gstin = await customers_collection.count_documents({"gstin": {"$nin": ["", None]}})
    with_portal = await customers_collection.count_documents({"portal_enabled": True})
    
    # Calculate total receivables
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": None,
            "total_receivable": {"$sum": "$outstanding_balance"},
            "total_credit_limit": {"$sum": "$credit_limit"}
        }}
    ]
    
    stats = await customers_collection.aggregate(pipeline).to_list(1)
    values = stats[0] if stats else {"total_receivable": 0, "total_credit_limit": 0}
    
    # New customers this month
    first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    new_this_month = await customers_collection.count_documents({"created_time": {"$gte": first_of_month}})
    
    return {
        "code": 0,
        "summary": {
            "total": total,
            "active": active,
            "inactive": inactive,
            "with_gstin": with_gstin,
            "with_portal": with_portal,
            "new_this_month": new_this_month,
            "total_receivable": round(values.get("total_receivable", 0), 2),
            "total_credit_limit": round(values.get("total_credit_limit", 0), 2)
        }
    }

# ========================= CUSTOMER CRUD =========================

@router.post("/")
async def create_customer(customer: CustomerCreate, background_tasks: BackgroundTasks):
    """Create a new customer"""
    # Check for duplicate by GSTIN or email
    if customer.gstin:
        existing = await customers_collection.find_one({"gstin": customer.gstin.upper()})
        if existing:
            raise HTTPException(status_code=400, detail=f"Customer with GSTIN {customer.gstin} already exists")
    
    if customer.email:
        existing = await customers_collection.find_one({"email": customer.email.lower()})
        if existing:
            raise HTTPException(status_code=400, detail=f"Customer with email {customer.email} already exists")
    
    customer_id = generate_id("CUST")
    customer_number = await get_next_customer_number()
    
    # Validate and parse GSTIN
    gstin_info = None
    if customer.gstin:
        gstin_info = validate_gstin(customer.gstin)
        if not gstin_info["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid GSTIN: {gstin_info.get('error')}")
        customer.gstin = gstin_info["gstin"]
        if not customer.place_of_supply:
            customer.place_of_supply = gstin_info["state_code"]
        if not customer.pan:
            customer.pan = gstin_info["pan"]
    
    # Build customer document
    customer_doc = {
        "customer_id": customer_id,
        "customer_number": customer_number,
        "display_name": customer.display_name,
        "company_name": customer.company_name,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email.lower() if customer.email else "",
        "phone": customer.phone,
        "mobile": customer.mobile,
        "website": customer.website,
        "currency_code": customer.currency_code,
        "payment_terms": customer.payment_terms,
        "credit_limit": customer.credit_limit,
        "opening_balance": customer.opening_balance,
        "opening_balance_type": customer.opening_balance_type,
        "gstin": customer.gstin.upper() if customer.gstin else "",
        "pan": customer.pan.upper() if customer.pan else "",
        "place_of_supply": customer.place_of_supply,
        "gst_treatment": customer.gst_treatment,
        "tax_treatment": customer.tax_treatment,
        "customer_type": customer.customer_type,
        "customer_segment": customer.customer_segment,
        "industry": customer.industry,
        "price_list_id": customer.price_list_id,
        "discount_percent": customer.discount_percent,
        "portal_enabled": customer.portal_enabled,
        "portal_token": "",
        "notes": customer.notes,
        "tags": customer.tags,
        "custom_fields": customer.custom_fields,
        "source": customer.source,
        "referred_by": customer.referred_by,
        # Computed fields
        "is_active": True,
        "outstanding_balance": customer.opening_balance if customer.opening_balance_type == "debit" else -customer.opening_balance,
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
    
    await customers_collection.insert_one(customer_doc)
    await add_customer_history(customer_id, "created", f"Customer {customer_number} created")
    
    # Send welcome email (mocked)
    if customer.email:
        background_tasks.add_task(mock_send_email, customer.email, "Welcome to Battwheels", f"Dear {customer.display_name}, Welcome!")
    
    customer_doc.pop("_id", None)
    return {"code": 0, "message": "Customer created", "customer": customer_doc}

@router.get("/")
async def list_customers(
    search: Optional[str] = None,
    status: Optional[str] = None,  # active, inactive, all
    gst_treatment: Optional[str] = None,
    customer_type: Optional[str] = None,
    tag: Optional[str] = None,
    has_outstanding: Optional[bool] = None,
    sort_by: str = "display_name",
    sort_order: str = "asc",
    page: int = 1,
    per_page: int = 50
):
    """List customers with filters"""
    query = {}
    
    if status == "active":
        query["is_active"] = True
    elif status == "inactive":
        query["is_active"] = False
    
    if gst_treatment:
        query["gst_treatment"] = gst_treatment
    
    if customer_type:
        query["customer_type"] = customer_type
    
    if tag:
        query["tags"] = tag
    
    if has_outstanding is True:
        query["outstanding_balance"] = {"$gt": 0}
    elif has_outstanding is False:
        query["outstanding_balance"] = {"$lte": 0}
    
    if search:
        query["$or"] = [
            {"display_name": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"gstin": {"$regex": search, "$options": "i"}},
            {"customer_number": {"$regex": search, "$options": "i"}}
        ]
    
    total = await customers_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    sort_dir = 1 if sort_order == "asc" else -1
    
    customers = await customers_collection.find(query, {"_id": 0}).sort(sort_by, sort_dir).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "customers": customers,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }

@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    """Get customer details with persons, addresses, balance, and transactions"""
    customer = await customers_collection.find_one({"customer_id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get contact persons
    persons = await customer_persons_collection.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("is_primary", -1).to_list(50)
    customer["persons"] = persons
    
    # Get addresses
    addresses = await customer_addresses_collection.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).to_list(20)
    customer["addresses"] = addresses
    
    # Get balance details
    balance = await calculate_customer_balance(customer_id)
    customer["balance_details"] = balance
    
    # Get aging
    aging = await get_customer_aging(customer_id)
    customer["aging"] = aging
    
    # Get transaction counts
    usage = await is_customer_used_in_transactions(customer_id)
    customer["transaction_counts"] = usage
    
    # Get history
    history = await customer_history_collection.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20).to_list(20)
    customer["history"] = history
    
    # Get credits
    credits = await customer_credits_collection.find(
        {"customer_id": customer_id, "status": "active"},
        {"_id": 0}
    ).to_list(20)
    customer["credits"] = credits
    
    return {"code": 0, "customer": customer}

@router.put("/{customer_id}")
async def update_customer(customer_id: str, customer: CustomerUpdate):
    """Update customer details"""
    existing = await customers_collection.find_one({"customer_id": customer_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = {k: v for k, v in customer.dict().items() if v is not None}
    
    # Validate GSTIN if changed
    if "gstin" in update_data and update_data["gstin"]:
        gstin_info = validate_gstin(update_data["gstin"])
        if not gstin_info["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid GSTIN: {gstin_info.get('error')}")
        update_data["gstin"] = gstin_info["gstin"]
        if not customer.place_of_supply:
            update_data["place_of_supply"] = gstin_info["state_code"]
        if not customer.pan:
            update_data["pan"] = gstin_info["pan"]
        
        # Check for duplicate
        dup = await customers_collection.find_one({"gstin": update_data["gstin"], "customer_id": {"$ne": customer_id}})
        if dup:
            raise HTTPException(status_code=400, detail="GSTIN already exists for another customer")
    
    # Check email duplicate
    if "email" in update_data and update_data["email"]:
        update_data["email"] = update_data["email"].lower()
        dup = await customers_collection.find_one({"email": update_data["email"], "customer_id": {"$ne": customer_id}})
        if dup:
            raise HTTPException(status_code=400, detail="Email already exists for another customer")
    
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        await customers_collection.update_one({"customer_id": customer_id}, {"$set": update_data})
    
    await add_customer_history(customer_id, "updated", "Customer details updated")
    
    updated = await customers_collection.find_one({"customer_id": customer_id}, {"_id": 0})
    return {"code": 0, "message": "Customer updated", "customer": updated}

@router.delete("/{customer_id}")
async def delete_customer(customer_id: str):
    """Delete a customer (only if not used in transactions)"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    usage = await is_customer_used_in_transactions(customer_id)
    if usage["is_used"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete customer with {usage['total_transactions']} transactions. Deactivate instead."
        )
    
    # Delete related data
    await customer_persons_collection.delete_many({"customer_id": customer_id})
    await customer_addresses_collection.delete_many({"customer_id": customer_id})
    await customer_history_collection.delete_many({"customer_id": customer_id})
    await customer_credits_collection.delete_many({"customer_id": customer_id})
    await customers_collection.delete_one({"customer_id": customer_id})
    
    return {"code": 0, "message": "Customer deleted"}

# ========================= CONTACT PERSONS =========================

@router.get("/{customer_id}/persons")
async def get_customer_persons(customer_id: str):
    """Get all contact persons for a customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    persons = await customer_persons_collection.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("is_primary", -1).to_list(50)
    
    return {"code": 0, "persons": persons}

@router.post("/{customer_id}/persons")
async def add_customer_person(customer_id: str, person: PersonCreate):
    """Add a contact person to customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # If setting as primary, unset existing primary
    if person.is_primary:
        await customer_persons_collection.update_many(
            {"customer_id": customer_id},
            {"$set": {"is_primary": False}}
        )
    
    person_id = generate_id("PERS")
    
    person_doc = {
        "person_id": person_id,
        "customer_id": customer_id,
        **person.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await customer_persons_collection.insert_one(person_doc)
    
    # Update count
    count = await customer_persons_collection.count_documents({"customer_id": customer_id})
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {"contact_persons_count": count, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_customer_history(customer_id, "person_added", f"Contact person {person.first_name} added")
    
    person_doc.pop("_id", None)
    return {"code": 0, "message": "Person added", "person": person_doc}

@router.put("/{customer_id}/persons/{person_id}")
async def update_customer_person(customer_id: str, person_id: str, person: PersonUpdate):
    """Update a contact person"""
    existing = await customer_persons_collection.find_one({"person_id": person_id, "customer_id": customer_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    
    update_data = {k: v for k, v in person.dict().items() if v is not None}
    
    # If setting as primary, unset existing primary
    if update_data.get("is_primary"):
        await customer_persons_collection.update_many(
            {"customer_id": customer_id, "person_id": {"$ne": person_id}},
            {"$set": {"is_primary": False}}
        )
    
    if update_data:
        await customer_persons_collection.update_one({"person_id": person_id}, {"$set": update_data})
    
    updated = await customer_persons_collection.find_one({"person_id": person_id}, {"_id": 0})
    return {"code": 0, "message": "Person updated", "person": updated}

@router.delete("/{customer_id}/persons/{person_id}")
async def delete_customer_person(customer_id: str, person_id: str):
    """Delete a contact person"""
    result = await customer_persons_collection.delete_one({"person_id": person_id, "customer_id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Update count
    count = await customer_persons_collection.count_documents({"customer_id": customer_id})
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {"contact_persons_count": count, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_customer_history(customer_id, "person_deleted", "Contact person deleted")
    
    return {"code": 0, "message": "Person deleted"}

@router.post("/{customer_id}/persons/{person_id}/set-primary")
async def set_primary_person(customer_id: str, person_id: str):
    """Set a person as primary contact"""
    existing = await customer_persons_collection.find_one({"person_id": person_id, "customer_id": customer_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    
    await customer_persons_collection.update_many(
        {"customer_id": customer_id},
        {"$set": {"is_primary": False}}
    )
    await customer_persons_collection.update_one(
        {"person_id": person_id},
        {"$set": {"is_primary": True}}
    )
    
    return {"code": 0, "message": "Primary contact set"}

# ========================= ADDRESSES =========================

@router.get("/{customer_id}/addresses")
async def get_customer_addresses(customer_id: str):
    """Get all addresses for a customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    addresses = await customer_addresses_collection.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).to_list(20)
    
    return {"code": 0, "addresses": addresses}

@router.post("/{customer_id}/addresses")
async def add_customer_address(customer_id: str, address: AddressCreate):
    """Add an address to customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # If setting as default, unset existing default of same type
    if address.is_default:
        await customer_addresses_collection.update_many(
            {"customer_id": customer_id, "address_type": address.address_type},
            {"$set": {"is_default": False}}
        )
    
    address_id = generate_id("ADDR")
    
    address_doc = {
        "address_id": address_id,
        "customer_id": customer_id,
        **address.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await customer_addresses_collection.insert_one(address_doc)
    
    # Update flags
    has_billing = await customer_addresses_collection.count_documents({"customer_id": customer_id, "address_type": "billing"}) > 0
    has_shipping = await customer_addresses_collection.count_documents({"customer_id": customer_id, "address_type": "shipping"}) > 0
    count = await customer_addresses_collection.count_documents({"customer_id": customer_id})
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {
            "has_billing_address": has_billing,
            "has_shipping_address": has_shipping,
            "addresses_count": count,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_customer_history(customer_id, "address_added", f"{address.address_type.title()} address added")
    
    address_doc.pop("_id", None)
    return {"code": 0, "message": "Address added", "address": address_doc}

@router.put("/{customer_id}/addresses/{address_id}")
async def update_customer_address(customer_id: str, address_id: str, address: AddressUpdate):
    """Update an address"""
    existing = await customer_addresses_collection.find_one({"address_id": address_id, "customer_id": customer_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Address not found")
    
    update_data = {k: v for k, v in address.dict().items() if v is not None}
    
    # If setting as default, unset existing default of same type
    if update_data.get("is_default"):
        addr_type = update_data.get("address_type") or existing.get("address_type")
        await customer_addresses_collection.update_many(
            {"customer_id": customer_id, "address_type": addr_type, "address_id": {"$ne": address_id}},
            {"$set": {"is_default": False}}
        )
    
    if update_data:
        await customer_addresses_collection.update_one({"address_id": address_id}, {"$set": update_data})
    
    updated = await customer_addresses_collection.find_one({"address_id": address_id}, {"_id": 0})
    return {"code": 0, "message": "Address updated", "address": updated}

@router.delete("/{customer_id}/addresses/{address_id}")
async def delete_customer_address(customer_id: str, address_id: str):
    """Delete an address"""
    result = await customer_addresses_collection.delete_one({"address_id": address_id, "customer_id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    
    # Update flags
    has_billing = await customer_addresses_collection.count_documents({"customer_id": customer_id, "address_type": "billing"}) > 0
    has_shipping = await customer_addresses_collection.count_documents({"customer_id": customer_id, "address_type": "shipping"}) > 0
    count = await customer_addresses_collection.count_documents({"customer_id": customer_id})
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {
            "has_billing_address": has_billing,
            "has_shipping_address": has_shipping,
            "addresses_count": count,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_customer_history(customer_id, "address_deleted", "Address deleted")
    
    return {"code": 0, "message": "Address deleted"}

# ========================= PORTAL ACCESS =========================

@router.post("/{customer_id}/enable-portal")
async def enable_customer_portal(customer_id: str, email_to: Optional[str] = None):
    """Enable portal access for customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    recipient = email_to or customer.get("email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    portal_token = str(uuid.uuid4())
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
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
        f"Dear {customer.get('display_name')},\n\nYour customer portal has been enabled.\nAccess Token: {portal_token}",
        ""
    )
    
    await add_customer_history(customer_id, "portal_enabled", f"Portal enabled, invite sent to {recipient}")
    
    return {"code": 0, "message": f"Portal enabled, invite sent to {recipient}", "token": portal_token}

@router.post("/{customer_id}/disable-portal")
async def disable_customer_portal(customer_id: str):
    """Disable portal access for customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {
            "portal_enabled": False,
            "portal_token": "",
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_customer_history(customer_id, "portal_disabled", "Portal access disabled")
    
    return {"code": 0, "message": "Portal disabled"}

@router.post("/{customer_id}/resend-portal-invite")
async def resend_portal_invite(customer_id: str, email_to: Optional[str] = None):
    """Resend portal invite email"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.get("portal_enabled"):
        raise HTTPException(status_code=400, detail="Portal not enabled")
    
    recipient = email_to or customer.get("email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    mock_send_email(
        recipient,
        "Portal Access Reminder - Battwheels",
        f"Dear {customer.get('display_name')},\n\nYour customer portal token: {customer.get('portal_token')}",
        ""
    )
    
    await add_customer_history(customer_id, "portal_invite_resent", f"Portal invite resent to {recipient}")
    
    return {"code": 0, "message": f"Portal invite resent to {recipient}"}

# ========================= STATEMENTS =========================

@router.post("/{customer_id}/email-statement")
async def email_customer_statement(customer_id: str, request: StatementRequest):
    """Email account statement to customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    recipient = request.email_to or customer.get("email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    # Get transactions for statement
    query = {"customer_id": customer_id}
    if request.start_date:
        query["date"] = {"$gte": request.start_date}
    if request.end_date:
        if "date" in query:
            query["date"]["$lte"] = request.end_date
        else:
            query["date"] = {"$lte": request.end_date}
    
    invoices = await db["invoices"].find(query, {"_id": 0, "invoice_number": 1, "date": 1, "total": 1, "balance_due": 1}).to_list(500)
    
    # Get balance
    balance = await calculate_customer_balance(customer_id)
    
    # Generate PDF (mocked)
    pdf_data = mock_generate_pdf({
        "customer_id": customer_id,
        "customer_name": customer.get("display_name"),
        "invoices": invoices,
        "balance": balance,
        "start_date": request.start_date,
        "end_date": request.end_date
    }, "statement")
    
    # Send email (mocked)
    mock_send_email(
        recipient,
        f"Account Statement - {customer.get('display_name')} - Battwheels",
        f"Dear {customer.get('display_name')},\n\nPlease find attached your account statement.\n\nCurrent Outstanding: ₹{balance.get('net_balance', 0):,.2f}",
        f"Statement_{customer.get('customer_number')}.pdf"
    )
    
    await add_customer_history(customer_id, "statement_sent", f"Statement emailed to {recipient}")
    
    return {"code": 0, "message": f"Statement sent to {recipient}"}

@router.get("/{customer_id}/statement")
async def get_customer_statement(customer_id: str, start_date: str = "", end_date: str = ""):
    """Get customer statement data"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    query = {"customer_id": customer_id}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
    
    # Get invoices
    invoices = await db["invoices"].find(query, {"_id": 0}).sort("date", 1).to_list(500)
    
    # Get payments
    payments = await db["payments"].find(query, {"_id": 0}).sort("date", 1).to_list(500)
    
    # Get credits
    credits = await customer_credits_collection.find({"customer_id": customer_id}, {"_id": 0}).to_list(100)
    
    # Calculate running balance
    balance = await calculate_customer_balance(customer_id)
    aging = await get_customer_aging(customer_id)
    
    return {
        "code": 0,
        "statement": {
            "customer": {
                "customer_id": customer_id,
                "display_name": customer.get("display_name"),
                "customer_number": customer.get("customer_number"),
                "email": customer.get("email"),
                "gstin": customer.get("gstin")
            },
            "period": {"start_date": start_date, "end_date": end_date},
            "invoices": invoices,
            "payments": payments,
            "credits": credits,
            "balance": balance,
            "aging": aging
        }
    }

# ========================= STATUS MANAGEMENT =========================

@router.post("/{customer_id}/activate")
async def activate_customer(customer_id: str):
    """Activate an inactive customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {"is_active": True, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_customer_history(customer_id, "activated", "Customer activated")
    
    return {"code": 0, "message": "Customer activated"}

@router.post("/{customer_id}/deactivate")
async def deactivate_customer(customer_id: str):
    """Deactivate a customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check for pending transactions
    pending_invoices = await db["invoices"].count_documents({
        "customer_id": customer_id,
        "status": {"$in": ["draft", "sent", "partially_paid"]},
        "balance_due": {"$gt": 0}
    })
    
    if pending_invoices > 0:
        raise HTTPException(status_code=400, detail=f"Customer has {pending_invoices} pending invoices. Clear them before deactivating.")
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {"is_active": False, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_customer_history(customer_id, "deactivated", "Customer deactivated")
    
    return {"code": 0, "message": "Customer deactivated"}

# ========================= CREDITS & REFUNDS =========================

@router.get("/{customer_id}/credits")
async def get_customer_credits(customer_id: str):
    """Get customer credits"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    credits = await customer_credits_collection.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_time", -1).to_list(100)
    
    return {"code": 0, "credits": credits}

@router.post("/{customer_id}/credits")
async def add_customer_credit(customer_id: str, credit: CreditNoteCreate):
    """Add a credit note to customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    credit_id = generate_id("CRED")
    
    credit_doc = {
        "credit_id": credit_id,
        "customer_id": customer_id,
        "amount": credit.amount,
        "used_amount": 0,
        "balance": credit.amount,
        "reason": credit.reason,
        "reference_number": credit.reference_number,
        "date": credit.date or datetime.now(timezone.utc).date().isoformat(),
        "status": "active",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await customer_credits_collection.insert_one(credit_doc)
    
    # Update unused credits on customer
    total_credits = await customer_credits_collection.aggregate([
        {"$match": {"customer_id": customer_id, "status": "active"}},
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    
    unused = total_credits[0]["total"] if total_credits else 0
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {"unused_credits": unused, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_customer_history(customer_id, "credit_added", f"Credit of ₹{credit.amount} added")
    
    credit_doc.pop("_id", None)
    return {"code": 0, "message": "Credit added", "credit": credit_doc}

@router.post("/{customer_id}/refunds")
async def create_customer_refund(customer_id: str, refund: RefundCreate):
    """Create a refund for customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check available credits
    credits = await customer_credits_collection.find(
        {"customer_id": customer_id, "status": "active", "balance": {"$gt": 0}},
        {"_id": 0}
    ).to_list(100)
    
    available = sum(c.get("balance", 0) for c in credits)
    if available < refund.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient credits. Available: ₹{available}")
    
    refund_id = generate_id("REF")
    
    refund_doc = {
        "refund_id": refund_id,
        "customer_id": customer_id,
        "amount": refund.amount,
        "mode": refund.mode,
        "reference_number": refund.reference_number,
        "date": refund.date or datetime.now(timezone.utc).date().isoformat(),
        "notes": refund.notes,
        "status": "completed",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await customer_refunds_collection.insert_one(refund_doc)
    
    # Deduct from credits
    remaining = refund.amount
    for credit in credits:
        if remaining <= 0:
            break
        deduct = min(credit.get("balance", 0), remaining)
        await customer_credits_collection.update_one(
            {"credit_id": credit["credit_id"]},
            {"$inc": {"used_amount": deduct, "balance": -deduct}}
        )
        remaining -= deduct
    
    # Update unused credits on customer
    total_credits = await customer_credits_collection.aggregate([
        {"$match": {"customer_id": customer_id, "status": "active"}},
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    
    unused = total_credits[0]["total"] if total_credits else 0
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": {"unused_credits": unused, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    await add_customer_history(customer_id, "refund_created", f"Refund of ₹{refund.amount} processed")
    
    refund_doc.pop("_id", None)
    return {"code": 0, "message": "Refund created", "refund": refund_doc}

# ========================= TAGS =========================

@router.get("/tags/all")
async def get_all_customer_tags():
    """Get all customer tags"""
    tags = await customer_tags_collection.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    return {"code": 0, "tags": tags}

@router.post("/tags")
async def create_customer_tag(tag: TagCreate):
    """Create a new customer tag"""
    existing = await customer_tags_collection.find_one({"name": {"$regex": f"^{tag.name}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    tag_id = generate_id("TAG")
    tag_doc = {
        "tag_id": tag_id,
        **tag.dict(),
        "customer_count": 0,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await customer_tags_collection.insert_one(tag_doc)
    tag_doc.pop("_id", None)
    return {"code": 0, "message": "Tag created", "tag": tag_doc}

@router.delete("/tags/{tag_id}")
async def delete_customer_tag(tag_id: str):
    """Delete a customer tag"""
    tag = await customer_tags_collection.find_one({"tag_id": tag_id})
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Remove from all customers
    await customers_collection.update_many(
        {"tags": tag["name"]},
        {"$pull": {"tags": tag["name"]}}
    )
    
    await customer_tags_collection.delete_one({"tag_id": tag_id})
    return {"code": 0, "message": "Tag deleted"}

@router.post("/{customer_id}/tags/{tag_name}")
async def add_tag_to_customer(customer_id: str, tag_name: str):
    """Add a tag to customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$addToSet": {"tags": tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update tag count
    count = await customers_collection.count_documents({"tags": tag_name})
    await customer_tags_collection.update_one({"name": tag_name}, {"$set": {"customer_count": count}}, upsert=True)
    
    return {"code": 0, "message": "Tag added"}

@router.delete("/{customer_id}/tags/{tag_name}")
async def remove_tag_from_customer(customer_id: str, tag_name: str):
    """Remove a tag from customer"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    await customers_collection.update_one(
        {"customer_id": customer_id},
        {"$pull": {"tags": tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update tag count
    count = await customers_collection.count_documents({"tags": tag_name})
    await customer_tags_collection.update_one({"name": tag_name}, {"$set": {"customer_count": count}})
    
    return {"code": 0, "message": "Tag removed"}

# ========================= TRANSACTIONS =========================

@router.get("/{customer_id}/transactions")
async def get_customer_transactions(customer_id: str, transaction_type: str = "all", limit: int = 50):
    """Get customer's transaction history"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    transactions = []
    
    if transaction_type in ["all", "estimate"]:
        estimates = await db["estimates_enhanced"].find(
            {"customer_id": customer_id},
            {"_id": 0, "estimate_id": 1, "estimate_number": 1, "date": 1, "grand_total": 1, "status": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for e in estimates:
            e["transaction_type"] = "estimate"
        transactions.extend(estimates)
    
    if transaction_type in ["all", "salesorder"]:
        salesorders = await db["salesorders_enhanced"].find(
            {"customer_id": customer_id},
            {"_id": 0, "salesorder_id": 1, "salesorder_number": 1, "date": 1, "grand_total": 1, "status": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for so in salesorders:
            so["transaction_type"] = "salesorder"
        transactions.extend(salesorders)
    
    if transaction_type in ["all", "invoice"]:
        invoices = await db["invoices"].find(
            {"customer_id": customer_id},
            {"_id": 0, "invoice_id": 1, "invoice_number": 1, "date": 1, "total": 1, "balance_due": 1, "status": 1}
        ).sort("date", -1).limit(limit).to_list(limit)
        for inv in invoices:
            inv["transaction_type"] = "invoice"
        transactions.extend(invoices)
    
    if transaction_type in ["all", "payment"]:
        payments = await db["payments"].find(
            {"customer_id": customer_id},
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
async def bulk_customer_action(request: BulkActionRequest):
    """Perform bulk action on customers"""
    action = request.action
    customer_ids = request.customer_ids
    
    if not customer_ids:
        raise HTTPException(status_code=400, detail="No customers selected")
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    for customer_id in customer_ids:
        try:
            if action == "activate":
                await customers_collection.update_one(
                    {"customer_id": customer_id},
                    {"$set": {"is_active": True, "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            elif action == "deactivate":
                await customers_collection.update_one(
                    {"customer_id": customer_id},
                    {"$set": {"is_active": False, "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            elif action == "delete":
                usage = await is_customer_used_in_transactions(customer_id)
                if usage["is_used"]:
                    results["errors"].append(f"{customer_id}: Has transactions")
                    results["failed"] += 1
                else:
                    await customer_persons_collection.delete_many({"customer_id": customer_id})
                    await customer_addresses_collection.delete_many({"customer_id": customer_id})
                    await customers_collection.delete_one({"customer_id": customer_id})
                    results["success"] += 1
            
            elif action == "add_tag" and request.tag_name:
                await customers_collection.update_one(
                    {"customer_id": customer_id},
                    {"$addToSet": {"tags": request.tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            elif action == "remove_tag" and request.tag_name:
                await customers_collection.update_one(
                    {"customer_id": customer_id},
                    {"$pull": {"tags": request.tag_name}, "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["success"] += 1
            
            else:
                results["errors"].append(f"Unknown action: {action}")
                results["failed"] += 1
        
        except Exception as e:
            results["errors"].append(f"{customer_id}: {str(e)}")
            results["failed"] += 1
    
    return {"code": 0, "results": results}

# ========================= REPORTS =========================

@router.get("/reports/by-segment")
async def report_by_segment():
    """Report: Customers by segment"""
    pipeline = [
        {"$group": {
            "_id": "$customer_segment",
            "count": {"$sum": 1},
            "total_outstanding": {"$sum": "$outstanding_balance"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = await customers_collection.aggregate(pipeline).to_list(50)
    
    return {
        "code": 0,
        "report": [{"segment": r["_id"] or "Unclassified", "count": r["count"], "total_outstanding": round(r["total_outstanding"], 2)} for r in results]
    }

@router.get("/reports/top-customers")
async def report_top_customers(limit: int = 20, by: str = "outstanding"):
    """Report: Top customers by outstanding or invoiced amount"""
    if by == "outstanding":
        sort_field = "outstanding_balance"
    else:
        sort_field = "total_invoiced"
    
    customers = await customers_collection.find(
        {"is_active": True},
        {"_id": 0, "customer_id": 1, "display_name": 1, "company_name": 1, "outstanding_balance": 1}
    ).sort(sort_field, -1).limit(limit).to_list(limit)
    
    return {"code": 0, "report": customers}

@router.get("/reports/aging-summary")
async def report_aging_summary():
    """Report: Aging summary across all customers"""
    customers = await customers_collection.find(
        {"is_active": True, "outstanding_balance": {"$gt": 0}},
        {"_id": 0, "customer_id": 1}
    ).to_list(1000)
    
    total_aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    
    for cust in customers:
        aging = await get_customer_aging(cust["customer_id"])
        for bucket in total_aging:
            total_aging[bucket] += aging.get(bucket, 0)
    
    return {
        "code": 0,
        "report": {k: round(v, 2) for k, v in total_aging.items()},
        "total": round(sum(total_aging.values()), 2)
    }

@router.get("/reports/new-customers")
async def report_new_customers(days: int = 30):
    """Report: New customers in last N days"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    customers = await customers_collection.find(
        {"created_time": {"$gte": cutoff}},
        {"_id": 0, "customer_id": 1, "display_name": 1, "company_name": 1, "email": 1, "created_time": 1, "source": 1}
    ).sort("created_time", -1).to_list(100)
    
    return {"code": 0, "report": customers, "total": len(customers)}

# ========================= QUICK ACTIONS =========================

@router.post("/{customer_id}/quick-estimate")
async def create_quick_estimate_for_customer(customer_id: str):
    """Quick action: Create estimate for customer - returns URL params"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "code": 0,
        "redirect": f"/estimates?customer_id={customer_id}&customer_name={customer.get('display_name', '')}",
        "message": "Navigate to estimates with customer pre-filled"
    }

@router.post("/{customer_id}/quick-invoice")
async def create_quick_invoice_for_customer(customer_id: str):
    """Quick action: Create invoice for customer - returns URL params"""
    customer = await customers_collection.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "code": 0,
        "redirect": f"/invoices?customer_id={customer_id}&customer_name={customer.get('display_name', '')}",
        "message": "Navigate to invoices with customer pre-filled"
    }
