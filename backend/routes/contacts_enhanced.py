# Comprehensive Contacts Module for Zoho Books Clone
# Handles Customers, Vendors, Contact Persons, Addresses, Tags, Portal Access, Statements

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
import motor.motor_asyncio
import os
import re
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts-enhanced", tags=["Contacts Enhanced"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
contacts_collection = db["contacts_enhanced"]
contact_persons_collection = db["contact_persons"]
addresses_collection = db["addresses"]
contact_tags_collection = db["contact_tags"]
contact_statements_collection = db["contact_statements"]

# GSTIN Validation Regex
GSTIN_REGEX = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'

# Indian States mapping (GSTIN prefix to state code)
GSTIN_STATE_MAP = {
    "01": "JK", "02": "HP", "03": "PB", "04": "CH", "05": "UK", "06": "HR",
    "07": "DL", "08": "RJ", "09": "UP", "10": "BR", "11": "SK", "12": "AR",
    "13": "NL", "14": "MN", "15": "MZ", "16": "TR", "17": "ML", "18": "AS",
    "19": "WB", "20": "JH", "21": "OR", "22": "CG", "23": "MP", "24": "GJ",
    "26": "DD", "27": "MH", "28": "AP", "29": "KA", "30": "GA", "31": "LD",
    "32": "KL", "33": "TN", "34": "PY", "35": "AN", "36": "TG", "37": "AP",
    "38": "LD", "97": "OT"
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

# ========================= PYDANTIC MODELS =========================

class ContactTagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    color: str = "#3B82F6"  # Default blue

class ContactTagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class ContactPersonCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = ""
    email: Optional[EmailStr] = None
    phone: str = ""
    designation: str = ""
    department: str = ""
    is_primary: bool = False

class ContactPersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    is_primary: Optional[bool] = None

class AddressCreate(BaseModel):
    address_type: str = Field(..., pattern="^(billing|shipping)$")
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
    name: str = Field(..., min_length=1, max_length=200)
    company_name: str = ""
    contact_type: str = Field(default="customer", pattern="^(customer|vendor|both)$")
    email: Optional[EmailStr] = None
    phone: str = ""
    mobile: str = ""
    website: str = ""
    currency_code: str = "INR"
    payment_terms: int = Field(default=30, ge=0)
    credit_limit: float = 0
    gstin: str = ""
    pan: str = ""
    place_of_supply: str = ""
    tax_treatment: str = "business_gst"  # business_gst, business_none, consumer, overseas
    gst_treatment: str = "registered"  # registered, unregistered, consumer, overseas, sez
    opening_balance: float = 0
    opening_balance_type: str = "credit"  # credit or debit
    tags: List[str] = []
    notes: str = ""
    custom_fields: Dict[str, Any] = {}
    # Nested data for creation
    persons: List[ContactPersonCreate] = []
    addresses: List[AddressCreate] = []

    @validator('gstin')
    def validate_gstin(cls, v):
        if v and not re.match(GSTIN_REGEX, v):
            raise ValueError('Invalid GSTIN format')
        return v

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    contact_type: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    currency_code: Optional[str] = None
    payment_terms: Optional[int] = None
    credit_limit: Optional[float] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    place_of_supply: Optional[str] = None
    tax_treatment: Optional[str] = None
    gst_treatment: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

# ========================= HELPER FUNCTIONS =========================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def get_state_from_gstin(gstin: str) -> str:
    """Extract state code from GSTIN prefix"""
    if gstin and len(gstin) >= 2:
        prefix = gstin[:2]
        return GSTIN_STATE_MAP.get(prefix, "")
    return ""

async def get_contact_balance(contact_id: str) -> dict:
    """Calculate outstanding balance from invoices/bills"""
    # Check invoices (for customers)
    invoices = await db["invoices"].find(
        {"customer_id": contact_id, "status": {"$nin": ["paid", "void"]}},
        {"balance_due": 1}
    ).to_list(1000)
    receivable = sum(inv.get("balance_due", 0) for inv in invoices)
    
    # Check bills (for vendors)
    bills = await db["bills"].find(
        {"vendor_id": contact_id, "status": {"$nin": ["paid", "void"]}},
        {"balance_due": 1}
    ).to_list(1000)
    payable = sum(bill.get("balance_due", 0) for bill in bills)
    
    return {"receivable": receivable, "payable": payable, "net": receivable - payable}

async def check_contact_usage(contact_id: str) -> dict:
    """Check if contact is used in any transactions"""
    invoice_count = await db["invoices"].count_documents({"customer_id": contact_id})
    bill_count = await db["bills"].count_documents({"vendor_id": contact_id})
    estimate_count = await db["estimates"].count_documents({"customer_id": contact_id})
    po_count = await db["purchase_orders"].count_documents({"vendor_id": contact_id})
    payment_count = await db["payments"].count_documents({"contact_id": contact_id})
    
    return {
        "is_used": (invoice_count + bill_count + estimate_count + po_count + payment_count) > 0,
        "invoices": invoice_count,
        "bills": bill_count,
        "estimates": estimate_count,
        "purchase_orders": po_count,
        "payments": payment_count
    }

def mock_send_email(to_email: str, subject: str, body: str):
    """Mock email sending - logs instead of actual send"""
    logger.info(f"[MOCK EMAIL] To: {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Body Preview: {body[:200]}...")
    return True

# ========================= CONTACT TAGS ENDPOINTS =========================

@router.post("/tags")
async def create_contact_tag(tag: ContactTagCreate):
    """Create a new contact tag"""
    # Check for duplicate
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

@router.get("/tags")
async def list_contact_tags(include_inactive: bool = False):
    """List all contact tags"""
    query = {} if include_inactive else {"is_active": {"$ne": False}}
    tags = await contact_tags_collection.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    # Update contact counts
    for tag in tags:
        count = await contacts_collection.count_documents({"tags": tag["tag_id"], "is_active": True})
        tag["contact_count"] = count
    
    return {"code": 0, "tags": tags}

@router.get("/tags/{tag_id}")
async def get_contact_tag(tag_id: str):
    """Get a specific tag"""
    tag = await contact_tags_collection.find_one({"tag_id": tag_id}, {"_id": 0})
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Get contacts with this tag
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
    
    # Check usage
    usage_count = await contacts_collection.count_documents({"tags": tag_id})
    if usage_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete tag used by {usage_count} contacts")
    
    await contact_tags_collection.delete_one({"tag_id": tag_id})
    return {"code": 0, "message": "Tag deleted"}

# ========================= CONTACTS ENDPOINTS =========================

@router.post("/")
async def create_contact(contact: ContactCreate):
    """Create a new contact with persons and addresses"""
    # Auto-detect place of supply from GSTIN
    place_of_supply = contact.place_of_supply
    if contact.gstin and not place_of_supply:
        place_of_supply = get_state_from_gstin(contact.gstin)
    
    contact_id = generate_id("CON")
    
    contact_doc = {
        "contact_id": contact_id,
        "name": contact.name,
        "company_name": contact.company_name,
        "contact_type": contact.contact_type,
        "email": contact.email,
        "phone": contact.phone,
        "mobile": contact.mobile,
        "website": contact.website,
        "currency_code": contact.currency_code,
        "payment_terms": contact.payment_terms,
        "credit_limit": contact.credit_limit,
        "gstin": contact.gstin,
        "pan": contact.pan,
        "place_of_supply": place_of_supply,
        "tax_treatment": contact.tax_treatment,
        "gst_treatment": contact.gst_treatment,
        "opening_balance": contact.opening_balance,
        "opening_balance_type": contact.opening_balance_type,
        "tags": contact.tags,
        "notes": contact.notes,
        "custom_fields": contact.custom_fields,
        "is_active": True,
        "portal_enabled": False,
        "portal_token": "",
        "portal_last_login": None,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
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
    
    # Send welcome email (mocked)
    if contact.email:
        mock_send_email(
            contact.email,
            "Welcome to Battwheels OS",
            f"Dear {contact.name},\n\nYour contact has been created in our system.\n\nBest regards,\nBattwheels Team"
        )
    
    contact_doc.pop("_id", None)
    return {"code": 0, "message": "Contact created", "contact": contact_doc}

@router.get("/")
async def list_contacts(
    contact_type: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    is_active: Optional[bool] = None,
    has_balance: Optional[bool] = None,
    page: int = 1,
    per_page: int = 50
):
    """List contacts with filters"""
    query = {}
    
    if contact_type:
        if contact_type in ["customer", "vendor"]:
            query["contact_type"] = {"$in": [contact_type, "both"]}
        else:
            query["contact_type"] = contact_type
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"gstin": {"$regex": search, "$options": "i"}}
        ]
    
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        query["tags"] = {"$in": tag_list}
    
    if is_active is not None:
        query["is_active"] = is_active
    
    total = await contacts_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    contacts = await contacts_collection.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(per_page).to_list(per_page)
    
    # Enrich with balance and person/address counts
    for contact in contacts:
        contact["person_count"] = await contact_persons_collection.count_documents({"contact_id": contact["contact_id"]})
        contact["address_count"] = await addresses_collection.count_documents({"contact_id": contact["contact_id"]})
        balance = await get_contact_balance(contact["contact_id"])
        contact["balance"] = balance
    
    # Filter by balance if requested
    if has_balance is not None:
        if has_balance:
            contacts = [c for c in contacts if c["balance"]["receivable"] > 0 or c["balance"]["payable"] > 0]
        else:
            contacts = [c for c in contacts if c["balance"]["receivable"] == 0 and c["balance"]["payable"] == 0]
    
    return {
        "code": 0,
        "contacts": contacts,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }

@router.get("/summary")
async def get_contacts_summary():
    """Get contacts summary statistics"""
    total = await contacts_collection.count_documents({})
    customers = await contacts_collection.count_documents({"contact_type": {"$in": ["customer", "both"]}})
    vendors = await contacts_collection.count_documents({"contact_type": {"$in": ["vendor", "both"]}})
    active = await contacts_collection.count_documents({"is_active": True})
    inactive = await contacts_collection.count_documents({"is_active": False})
    with_gstin = await contacts_collection.count_documents({"gstin": {"$ne": ""}})
    portal_enabled = await contacts_collection.count_documents({"portal_enabled": True})
    
    # Calculate total receivables and payables
    all_contacts = await contacts_collection.find({}, {"contact_id": 1}).to_list(10000)
    total_receivable = 0
    total_payable = 0
    for c in all_contacts:
        balance = await get_contact_balance(c["contact_id"])
        total_receivable += balance["receivable"]
        total_payable += balance["payable"]
    
    return {
        "code": 0,
        "summary": {
            "total_contacts": total,
            "customers": customers,
            "vendors": vendors,
            "active": active,
            "inactive": inactive,
            "with_gstin": with_gstin,
            "portal_enabled": portal_enabled,
            "total_receivable": round(total_receivable, 2),
            "total_payable": round(total_payable, 2)
        }
    }

@router.get("/states")
async def get_indian_states():
    """Get list of Indian states for dropdowns"""
    return {"code": 0, "states": [{"code": s[0], "name": s[1]} for s in INDIAN_STATES]}

# ========================= BACKWARD COMPATIBILITY ENDPOINTS =========================
# These must be BEFORE /{contact_id} to avoid being caught by the parameterized route

@router.get("/customers")
async def list_customers(search: Optional[str] = None, page: int = 1, per_page: int = 50):
    """Backward compatible: List customers only"""
    return await list_contacts(contact_type="customer", search=search, page=page, per_page=per_page)

@router.get("/vendors")
async def list_vendors(search: Optional[str] = None, page: int = 1, per_page: int = 50):
    """Backward compatible: List vendors only"""
    return await list_contacts(contact_type="vendor", search=search, page=page, per_page=per_page)

# ========================= GSTIN VALIDATION ENDPOINT =========================
# Must be BEFORE /{contact_id} to avoid being caught by the parameterized route

@router.get("/validate-gstin/{gstin}")
async def validate_gstin(gstin: str):
    """Validate GSTIN format and extract details"""
    if not re.match(GSTIN_REGEX, gstin):
        return {
            "code": 1,
            "valid": False,
            "message": "Invalid GSTIN format",
            "details": None
        }
    
    state_code = get_state_from_gstin(gstin)
    state_name = next((s[1] for s in INDIAN_STATES if s[0] == state_code), "Unknown")
    
    # Extract PAN from GSTIN (characters 3-12)
    pan = gstin[2:12]
    
    # Entity type from 6th character of PAN
    entity_types = {
        'P': 'Individual', 'C': 'Company', 'H': 'HUF', 'F': 'Firm',
        'A': 'AOP', 'T': 'Trust', 'B': 'BOI', 'L': 'Local Authority',
        'J': 'Artificial Juridical Person', 'G': 'Government'
    }
    entity_type = entity_types.get(pan[3], 'Unknown')
    
    return {
        "code": 0,
        "valid": True,
        "message": "Valid GSTIN",
        "details": {
            "gstin": gstin,
            "state_code": state_code,
            "state_name": state_name,
            "pan": pan,
            "entity_type": entity_type,
            "checksum_digit": gstin[-1]
        }
    }

@router.get("/{contact_id}")
async def get_contact(contact_id: str):
    """Get contact details with persons, addresses, balance, and usage"""
    contact = await contacts_collection.find_one({"contact_id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Get persons
    persons = await contact_persons_collection.find({"contact_id": contact_id}, {"_id": 0}).to_list(100)
    contact["persons"] = persons
    
    # Get addresses
    addresses = await addresses_collection.find({"contact_id": contact_id}, {"_id": 0}).to_list(100)
    contact["addresses"] = addresses
    
    # Get balance
    contact["balance"] = await get_contact_balance(contact_id)
    
    # Get usage stats
    contact["usage"] = await check_contact_usage(contact_id)
    
    # Get tags details
    if contact.get("tags"):
        tags = await contact_tags_collection.find({"tag_id": {"$in": contact["tags"]}}, {"_id": 0}).to_list(50)
        contact["tag_details"] = tags
    
    return {"code": 0, "contact": contact}

@router.put("/{contact_id}")
async def update_contact(contact_id: str, contact: ContactUpdate):
    """Update a contact"""
    existing = await contacts_collection.find_one({"contact_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = {k: v for k, v in contact.dict().items() if v is not None}
    
    # Re-validate GSTIN if provided
    if "gstin" in update_data and update_data["gstin"]:
        if not re.match(GSTIN_REGEX, update_data["gstin"]):
            raise HTTPException(status_code=400, detail="Invalid GSTIN format")
        # Auto-update place of supply
        if "place_of_supply" not in update_data:
            update_data["place_of_supply"] = get_state_from_gstin(update_data["gstin"])
    
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        await contacts_collection.update_one({"contact_id": contact_id}, {"$set": update_data})
    
    updated = await contacts_collection.find_one({"contact_id": contact_id}, {"_id": 0})
    return {"code": 0, "message": "Contact updated", "contact": updated}

@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, force: bool = False):
    """Delete a contact (only if unused or force=True to deactivate)"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    usage = await check_contact_usage(contact_id)
    
    if usage["is_used"]:
        if force:
            # Deactivate instead of delete
            await contacts_collection.update_one(
                {"contact_id": contact_id},
                {"$set": {"is_active": False, "updated_time": datetime.now(timezone.utc).isoformat()}}
            )
            return {"code": 0, "message": "Contact deactivated (has transactions)", "deactivated": True}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete contact with transactions. Use force=true to deactivate. Usage: {usage}"
            )
    
    # Delete related data
    await contact_persons_collection.delete_many({"contact_id": contact_id})
    await addresses_collection.delete_many({"contact_id": contact_id})
    await contacts_collection.delete_one({"contact_id": contact_id})
    
    return {"code": 0, "message": "Contact deleted"}

@router.put("/{contact_id}/activate")
async def activate_contact(contact_id: str):
    """Activate a contact"""
    result = await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"is_active": True, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Contact activated"}

@router.put("/{contact_id}/deactivate")
async def deactivate_contact(contact_id: str):
    """Deactivate a contact"""
    result = await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {"is_active": False, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Contact deactivated"}

# ========================= PORTAL ACCESS ENDPOINTS =========================

@router.post("/{contact_id}/enable-portal")
async def enable_portal_access(contact_id: str, background_tasks: BackgroundTasks):
    """Enable portal access and send invite email"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    if not contact.get("email"):
        raise HTTPException(status_code=400, detail="Contact has no email address")
    
    # Generate portal token
    portal_token = str(uuid.uuid4())
    
    await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {
            "portal_enabled": True,
            "portal_token": portal_token,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send invite email (mocked)
    mock_send_email(
        contact["email"],
        "Portal Access Enabled - Battwheels OS",
        f"""Dear {contact['name']},

Your self-service portal access has been enabled.

Portal Token: {portal_token}

Use this token to access your:
- Invoices and Statements
- Payment History
- Account Balance

Best regards,
Battwheels Team"""
    )
    
    return {"code": 0, "message": "Portal access enabled, invite email sent", "portal_token": portal_token}

@router.post("/{contact_id}/disable-portal")
async def disable_portal_access(contact_id: str):
    """Disable portal access"""
    result = await contacts_collection.update_one(
        {"contact_id": contact_id},
        {"$set": {
            "portal_enabled": False,
            "portal_token": "",
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Portal access disabled"}

@router.post("/portal/validate-token")
async def validate_portal_token(token: str):
    """Validate a portal token (for portal login simulation)"""
    contact = await contacts_collection.find_one(
        {"portal_token": token, "portal_enabled": True},
        {"_id": 0, "contact_id": 1, "name": 1, "email": 1, "company_name": 1}
    )
    if not contact:
        raise HTTPException(status_code=401, detail="Invalid or expired portal token")
    
    # Update last login
    await contacts_collection.update_one(
        {"portal_token": token},
        {"$set": {"portal_last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": "Token valid", "contact": contact}

# ========================= CONTACT STATEMENTS ENDPOINTS =========================

@router.post("/{contact_id}/email-statement")
async def email_statement(contact_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Generate and email account statement"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    if not contact.get("email"):
        raise HTTPException(status_code=400, detail="Contact has no email address")
    
    # Build statement
    balance = await get_contact_balance(contact_id)
    
    # Get recent transactions (mock data structure)
    invoices = await db["invoices"].find(
        {"customer_id": contact_id},
        {"_id": 0, "invoice_number": 1, "date": 1, "total": 1, "balance_due": 1, "status": 1}
    ).sort("date", -1).limit(20).to_list(20)
    
    bills = await db["bills"].find(
        {"vendor_id": contact_id},
        {"_id": 0, "bill_number": 1, "date": 1, "total": 1, "balance_due": 1, "status": 1}
    ).sort("date", -1).limit(20).to_list(20)
    
    # Build statement text
    statement_lines = [
        f"Account Statement for {contact['name']}",
        f"{'=' * 50}",
        f"",
        f"Current Balance:",
        f"  Receivable: ₹{balance['receivable']:,.2f}",
        f"  Payable: ₹{balance['payable']:,.2f}",
        f"  Net: ₹{balance['net']:,.2f}",
        f"",
    ]
    
    if invoices:
        statement_lines.append("Recent Invoices:")
        for inv in invoices[:5]:
            statement_lines.append(f"  {inv.get('invoice_number', 'N/A')} - ₹{inv.get('total', 0):,.2f} ({inv.get('status', 'N/A')})")
    
    if bills:
        statement_lines.append("\nRecent Bills:")
        for bill in bills[:5]:
            statement_lines.append(f"  {bill.get('bill_number', 'N/A')} - ₹{bill.get('total', 0):,.2f} ({bill.get('status', 'N/A')})")
    
    statement_text = "\n".join(statement_lines)
    
    # Log statement generation
    statement_record = {
        "statement_id": generate_id("STMT"),
        "contact_id": contact_id,
        "generated_time": datetime.now(timezone.utc).isoformat(),
        "balance": balance,
        "email_sent_to": contact["email"],
        "date_range": {"start": start_date, "end": end_date}
    }
    await contact_statements_collection.insert_one(statement_record)
    
    # Send email (mocked)
    mock_send_email(
        contact["email"],
        f"Account Statement - {contact['name']}",
        statement_text
    )
    
    return {
        "code": 0,
        "message": "Statement generated and emailed",
        "statement_preview": statement_text[:500],
        "balance": balance
    }

@router.get("/{contact_id}/statement-history")
async def get_statement_history(contact_id: str):
    """Get history of generated statements"""
    statements = await contact_statements_collection.find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).sort("generated_time", -1).limit(50).to_list(50)
    return {"code": 0, "statements": statements}

# ========================= CONTACT PERSONS ENDPOINTS =========================

@router.post("/{contact_id}/persons")
async def add_contact_person(contact_id: str, person: ContactPersonCreate):
    """Add a person to a contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # If primary, unset other primaries
    if person.is_primary:
        await contact_persons_collection.update_many(
            {"contact_id": contact_id, "is_primary": True},
            {"$set": {"is_primary": False}}
        )
    
    person_doc = {
        "person_id": generate_id("PER"),
        "contact_id": contact_id,
        **person.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    await contact_persons_collection.insert_one(person_doc)
    person_doc.pop("_id", None)
    
    return {"code": 0, "message": "Person added", "person": person_doc}

@router.get("/{contact_id}/persons")
async def list_contact_persons(contact_id: str):
    """List all persons for a contact"""
    persons = await contact_persons_collection.find({"contact_id": contact_id}, {"_id": 0}).to_list(100)
    return {"code": 0, "persons": persons}

@router.put("/{contact_id}/persons/{person_id}")
async def update_contact_person(contact_id: str, person_id: str, person: ContactPersonUpdate):
    """Update a contact person"""
    existing = await contact_persons_collection.find_one({"person_id": person_id, "contact_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    
    update_data = {k: v for k, v in person.dict().items() if v is not None}
    
    # Handle primary flag
    if update_data.get("is_primary"):
        await contact_persons_collection.update_many(
            {"contact_id": contact_id, "is_primary": True, "person_id": {"$ne": person_id}},
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
    return {"code": 0, "message": "Person deleted"}

# ========================= ADDRESSES ENDPOINTS =========================

@router.post("/{contact_id}/addresses")
async def add_address(contact_id: str, address: AddressCreate):
    """Add an address to a contact"""
    contact = await contacts_collection.find_one({"contact_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # If default, unset other defaults of same type
    if address.is_default:
        await addresses_collection.update_many(
            {"contact_id": contact_id, "address_type": address.address_type, "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    address_doc = {
        "address_id": generate_id("ADDR"),
        "contact_id": contact_id,
        **address.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    await addresses_collection.insert_one(address_doc)
    address_doc.pop("_id", None)
    
    return {"code": 0, "message": "Address added", "address": address_doc}

@router.get("/{contact_id}/addresses")
async def list_addresses(contact_id: str, address_type: Optional[str] = None):
    """List all addresses for a contact"""
    query = {"contact_id": contact_id}
    if address_type:
        query["address_type"] = address_type
    addresses = await addresses_collection.find(query, {"_id": 0}).to_list(100)
    return {"code": 0, "addresses": addresses}

@router.put("/{contact_id}/addresses/{address_id}")
async def update_address(contact_id: str, address_id: str, address: AddressUpdate):
    """Update an address"""
    existing = await addresses_collection.find_one({"address_id": address_id, "contact_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Address not found")
    
    update_data = {k: v for k, v in address.dict().items() if v is not None}
    
    # Handle default flag
    if update_data.get("is_default"):
        addr_type = update_data.get("address_type", existing.get("address_type"))
        await addresses_collection.update_many(
            {"contact_id": contact_id, "address_type": addr_type, "is_default": True, "address_id": {"$ne": address_id}},
            {"$set": {"is_default": False}}
        )
    
    if update_data:
        await addresses_collection.update_one({"address_id": address_id}, {"$set": update_data})
    
    updated = await addresses_collection.find_one({"address_id": address_id}, {"_id": 0})
    return {"code": 0, "message": "Address updated", "address": updated}

@router.delete("/{contact_id}/addresses/{address_id}")
async def delete_address(contact_id: str, address_id: str):
    """Delete an address"""
    result = await addresses_collection.delete_one({"address_id": address_id, "contact_id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    return {"code": 0, "message": "Address deleted"}

# ========================= BULK OPERATIONS =========================

@router.post("/bulk/import")
async def bulk_import_contacts(contacts: List[ContactCreate]):
    """Bulk import contacts"""
    created = []
    errors = []
    
    for i, contact in enumerate(contacts):
        try:
            result = await create_contact(contact)
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
