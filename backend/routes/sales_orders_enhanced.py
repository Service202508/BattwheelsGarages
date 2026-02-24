# Enhanced Sales Orders Module for Zoho Books Clone
# Handles post-estimate confirmation: reserve inventory, track fulfillment, convert to Invoice

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import motor.motor_asyncio
import os
import uuid
import logging

# Import tenant context for multi-tenant scoping
from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales-orders-enhanced", tags=["Sales Orders Enhanced"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Use main collections with Zoho-synced data
salesorders_collection = db["salesorders"]
salesorder_items_collection = db["salesorder_line_items"]
salesorder_history_collection = db["salesorder_history"]
salesorder_settings_collection = db["salesorder_settings"]

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

# GST State codes for intra/inter-state calculation
GSTIN_STATE_MAP = {
    "01": "JK", "02": "HP", "03": "PB", "04": "CH", "05": "UK", "06": "HR",
    "07": "DL", "08": "RJ", "09": "UP", "10": "BR", "11": "SK", "12": "AR",
    "13": "NL", "14": "MN", "15": "MZ", "16": "TR", "17": "ML", "18": "AS",
    "19": "WB", "20": "JH", "21": "OR", "22": "CG", "23": "MP", "24": "GJ",
    "26": "DD", "27": "MH", "28": "AP", "29": "KA", "30": "GA", "31": "LD",
    "32": "KL", "33": "TN", "34": "PY", "35": "AN", "36": "TG", "37": "AP"
}

ORG_STATE_CODE = "DL"  # Delhi - Organization state

# ========================= PYDANTIC MODELS =========================

class LineItemCreate(BaseModel):
    item_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: str = ""
    hsn_code: str = ""
    quantity: float = Field(default=1, gt=0)
    quantity_ordered: float = Field(default=0, ge=0)
    quantity_fulfilled: float = Field(default=0, ge=0)
    unit: str = "pcs"
    rate: float = Field(default=0, ge=0)
    discount_percent: float = Field(default=0, ge=0, le=100)
    discount_amount: float = Field(default=0, ge=0)
    tax_id: Optional[str] = None
    tax_name: str = ""
    tax_percentage: float = Field(default=0, ge=0)
    warehouse_id: Optional[str] = None

class LineItemUpdate(BaseModel):
    item_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: Optional[float] = None
    quantity_ordered: Optional[float] = None
    quantity_fulfilled: Optional[float] = None
    unit: Optional[str] = None
    rate: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    tax_id: Optional[str] = None
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = None

class SalesOrderCreate(BaseModel):
    customer_id: str = Field(..., min_length=1)
    salesorder_number: Optional[str] = None
    reference_number: str = ""
    date: str = ""  # ISO date string
    expected_shipment_date: str = ""
    salesperson_id: Optional[str] = None
    salesperson_name: str = ""
    project_id: Optional[str] = None
    terms_and_conditions: str = ""
    notes: str = ""
    discount_type: str = "none"  # none, percent, amount
    discount_value: float = 0
    shipping_charge: float = 0
    adjustment: float = 0
    adjustment_description: str = ""
    custom_fields: Dict[str, Any] = {}
    line_items: List[LineItemCreate] = []
    billing_address: Optional[Dict[str, str]] = None
    shipping_address: Optional[Dict[str, str]] = None
    # Source tracking
    from_estimate_id: Optional[str] = None
    from_estimate_number: Optional[str] = None
    # Delivery method
    delivery_method: str = ""  # pickup, delivery, shipping

class SalesOrderUpdate(BaseModel):
    customer_id: Optional[str] = None
    reference_number: Optional[str] = None
    date: Optional[str] = None
    expected_shipment_date: Optional[str] = None
    salesperson_id: Optional[str] = None
    salesperson_name: Optional[str] = None
    project_id: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    notes: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    shipping_charge: Optional[float] = None
    adjustment: Optional[float] = None
    adjustment_description: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, str]] = None
    shipping_address: Optional[Dict[str, str]] = None
    delivery_method: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|confirmed|open|fulfilled|partially_fulfilled|closed|void)$")
    reason: str = ""

class FulfillmentCreate(BaseModel):
    line_items: List[Dict[str, Any]]  # [{line_item_id, quantity_to_fulfill, warehouse_id}]
    shipment_date: str = ""
    tracking_number: str = ""
    carrier: str = ""
    notes: str = ""

# ========================= HELPER FUNCTIONS =========================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

async def get_next_salesorder_number() -> str:
    """Generate next sales order number based on settings"""
    settings = await salesorder_settings_collection.find_one({"type": "numbering"})
    if not settings:
        settings = {
            "type": "numbering",
            "prefix": "SO-",
            "next_number": 1,
            "padding": 5
        }
        await salesorder_settings_collection.insert_one(settings)
    
    number = str(settings["next_number"]).zfill(settings.get("padding", 5))
    next_num = f"{settings.get('prefix', 'SO-')}{number}"
    
    await salesorder_settings_collection.update_one(
        {"type": "numbering"},
        {"$inc": {"next_number": 1}}
    )
    
    return next_num

async def get_contact_details(contact_id: str) -> dict:
    """Get contact details for sales order"""
    contact = await db["contacts_enhanced"].find_one({"contact_id": contact_id}, {"_id": 0})
    if not contact:
        contact = await db["contacts"].find_one({"contact_id": contact_id}, {"_id": 0})
    
    if not contact:
        return None
    
    billing_address = await db["addresses"].find_one(
        {"contact_id": contact_id, "address_type": "billing", "is_default": True},
        {"_id": 0}
    )
    if not billing_address:
        billing_address = await db["addresses"].find_one(
            {"contact_id": contact_id, "address_type": "billing"},
            {"_id": 0}
        )
    
    shipping_address = await db["addresses"].find_one(
        {"contact_id": contact_id, "address_type": "shipping", "is_default": True},
        {"_id": 0}
    )
    if not shipping_address:
        shipping_address = await db["addresses"].find_one(
            {"contact_id": contact_id, "address_type": "shipping"},
            {"_id": 0}
        )
    
    return {
        "contact_id": contact_id,
        "name": contact.get("name") or contact.get("display_name", ""),
        "company_name": contact.get("company_name", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "gstin": contact.get("gstin") or contact.get("gst_no", ""),
        "place_of_supply": contact.get("place_of_supply", ""),
        "payment_terms": contact.get("payment_terms", 30),
        "currency_code": contact.get("currency_code", "INR"),
        "billing_address": billing_address,
        "shipping_address": shipping_address
    }

async def get_item_details(item_id: str) -> dict:
    """Get item details for line item"""
    item = await db["items_enhanced"].find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        item = await db["items"].find_one({"item_id": item_id}, {"_id": 0})
    
    if not item:
        return None
    
    return {
        "item_id": item_id,
        "name": item.get("name", ""),
        "description": item.get("description", ""),
        "sku": item.get("sku", ""),
        "hsn_code": item.get("hsn_code", ""),
        "unit": item.get("unit", "pcs"),
        "rate": item.get("sales_rate") or item.get("rate", 0),
        "tax_percentage": item.get("tax_percentage", 0),
        "item_type": item.get("item_type", "service"),
        "stock_on_hand": item.get("stock_on_hand") or item.get("total_stock", 0),
        "track_inventory": item.get("track_inventory", False)
    }

def calculate_gst_type(org_state: str, customer_state: str) -> str:
    """Determine if IGST or CGST+SGST applies"""
    if not org_state or not customer_state:
        return "igst"
    return "cgst_sgst" if org_state == customer_state else "igst"

def calculate_line_item_totals(item: dict, gst_type: str) -> dict:
    """Calculate totals for a line item"""
    quantity = float(item.get("quantity", 1))
    rate = float(item.get("rate", 0))
    
    gross = quantity * rate
    
    discount_percent = float(item.get("discount_percent", 0))
    discount_amount = float(item.get("discount_amount", 0))
    
    if discount_percent > 0:
        discount = gross * (discount_percent / 100)
    else:
        discount = discount_amount
    
    taxable = gross - discount
    
    tax_percentage = float(item.get("tax_percentage", 0))
    tax_amount = taxable * (tax_percentage / 100)
    
    if gst_type == "cgst_sgst":
        cgst = tax_amount / 2
        sgst = tax_amount / 2
        igst = 0
    else:
        cgst = 0
        sgst = 0
        igst = tax_amount
    
    total = taxable + tax_amount
    
    return {
        "gross_amount": round(gross, 2),
        "discount": round(discount, 2),
        "taxable_amount": round(taxable, 2),
        "tax_amount": round(tax_amount, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "igst": round(igst, 2),
        "total": round(total, 2)
    }

def calculate_salesorder_totals(line_items: List[dict], discount_type: str, discount_value: float, 
                                shipping_charge: float, adjustment: float, gst_type: str) -> dict:
    """Calculate sales order totals"""
    subtotal = sum(item.get("taxable_amount", 0) for item in line_items)
    total_tax = sum(item.get("tax_amount", 0) for item in line_items)
    total_cgst = sum(item.get("cgst", 0) for item in line_items)
    total_sgst = sum(item.get("sgst", 0) for item in line_items)
    total_igst = sum(item.get("igst", 0) for item in line_items)
    
    if discount_type == "percent":
        doc_discount = subtotal * (discount_value / 100)
    elif discount_type == "amount":
        doc_discount = discount_value
    else:
        doc_discount = 0
    
    grand_total = subtotal - doc_discount + total_tax + shipping_charge + adjustment
    
    return {
        "subtotal": round(subtotal, 2),
        "total_discount": round(doc_discount + sum(item.get("discount", 0) for item in line_items), 2),
        "document_discount": round(doc_discount, 2),
        "total_tax": round(total_tax, 2),
        "total_cgst": round(total_cgst, 2),
        "total_sgst": round(total_sgst, 2),
        "total_igst": round(total_igst, 2),
        "shipping_charge": round(shipping_charge, 2),
        "adjustment": round(adjustment, 2),
        "grand_total": round(grand_total, 2),
        "gst_type": gst_type
    }

async def add_salesorder_history(salesorder_id: str, action: str, details: str, user_id: str = ""):
    """Add entry to sales order history"""
    history_entry = {
        "history_id": generate_id("SOHIST"),
        "salesorder_id": salesorder_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await salesorder_history_collection.insert_one(history_entry)

async def reserve_stock(salesorder_id: str, line_items: List[dict]):
    """Reserve stock for inventory items"""
    for item in line_items:
        if item.get("item_id") and item.get("track_inventory", False):
            quantity = float(item.get("quantity", 0))
            await db["items_enhanced"].update_one(
                {"item_id": item["item_id"]},
                {"$inc": {"reserved_stock": quantity}}
            )
            
            # Create adjustment record
            adjustment = {
                "adjustment_id": generate_id("ADJ"),
                "item_id": item["item_id"],
                "adjustment_type": "reserve",
                "quantity": quantity,
                "reason": f"Reserved for Sales Order",
                "reference_type": "salesorder",
                "reference_id": salesorder_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db["item_adjustments"].insert_one(adjustment)

async def release_reserved_stock(salesorder_id: str):
    """Release reserved stock when SO is voided/cancelled"""
    line_items = await salesorder_items_collection.find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).to_list(100)
    
    for item in line_items:
        if item.get("item_id") and item.get("track_inventory", False):
            reserved = float(item.get("quantity", 0)) - float(item.get("quantity_fulfilled", 0))
            if reserved > 0:
                await db["items_enhanced"].update_one(
                    {"item_id": item["item_id"]},
                    {"$inc": {"reserved_stock": -reserved}}
                )

async def deduct_stock(salesorder_id: str, fulfillment_items: List[dict]):
    """Deduct stock when items are fulfilled/shipped"""
    for item in fulfillment_items:
        if item.get("item_id"):
            quantity = float(item.get("quantity_to_fulfill", 0))
            # Reduce actual stock and reserved stock
            await db["items_enhanced"].update_one(
                {"item_id": item["item_id"]},
                {"$inc": {"stock_on_hand": -quantity, "reserved_stock": -quantity}}
            )
            
            # Update line item fulfilled quantity
            await salesorder_items_collection.update_one(
                {"line_item_id": item["line_item_id"]},
                {"$inc": {"quantity_fulfilled": quantity}}
            )

def mock_send_email(to_email: str, subject: str, body: str, attachment_name: str = ""):
    """Mock email sending - logs instead of actual send"""
    logger.info(f"[MOCK EMAIL] To: {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Attachment: {attachment_name}")
    logger.info(f"[MOCK EMAIL] Body Preview: {body[:200]}...")
    return True

# ========================= SETTINGS ENDPOINTS =========================

@router.get("/settings")
async def get_salesorder_settings():
    """Get sales order module settings"""
    numbering = await salesorder_settings_collection.find_one({"type": "numbering"}, {"_id": 0})
    defaults = await salesorder_settings_collection.find_one({"type": "defaults"}, {"_id": 0})
    
    if not numbering:
        numbering = {"type": "numbering", "prefix": "SO-", "next_number": 1, "padding": 5}
    if not defaults:
        defaults = {
            "type": "defaults",
            "shipment_days": 7,
            "terms_and_conditions": "Terms & Conditions apply.",
            "notes": ""
        }
    
    return {"code": 0, "settings": {"numbering": numbering, "defaults": defaults}}

@router.put("/settings")
async def update_salesorder_settings(settings: dict):
    """Update sales order module settings"""
    if "numbering" in settings:
        await salesorder_settings_collection.update_one(
            {"type": "numbering"},
            {"$set": settings["numbering"]},
            upsert=True
        )
    if "defaults" in settings:
        await salesorder_settings_collection.update_one(
            {"type": "defaults"},
            {"$set": settings["defaults"]},
            upsert=True
        )
    return {"code": 0, "message": "Settings updated"}

# ========================= SALES ORDER CRUD ENDPOINTS =========================

@router.post("/")
async def create_sales_order(salesorder: SalesOrderCreate, background_tasks: BackgroundTasks):
    """Create a new sales order"""
    # Validate customer
    customer = await get_contact_details(salesorder.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Generate salesorder number if not provided
    salesorder_number = salesorder.salesorder_number or await get_next_salesorder_number()
    
    # Check for duplicate
    existing = await salesorders_collection.find_one({"salesorder_number": salesorder_number})
    if existing:
        raise HTTPException(status_code=400, detail=f"Sales Order number {salesorder_number} already exists")
    
    # Determine GST type based on place of supply
    customer_state = customer.get("place_of_supply", "")
    if not customer_state and customer.get("gstin"):
        gstin = customer.get("gstin", "")
        if len(gstin) >= 2:
            customer_state = GSTIN_STATE_MAP.get(gstin[:2], "")
    
    gst_type = calculate_gst_type(ORG_STATE_CODE, customer_state)
    
    # Set dates
    today = datetime.now(timezone.utc).date().isoformat()
    salesorder_date = salesorder.date or today
    
    defaults = await salesorder_settings_collection.find_one({"type": "defaults"})
    shipment_days = defaults.get("shipment_days", 7) if defaults else 7
    
    if salesorder.expected_shipment_date:
        expected_shipment_date = salesorder.expected_shipment_date
    else:
        expected_shipment_date = (datetime.fromisoformat(salesorder_date) + timedelta(days=shipment_days)).date().isoformat()
    
    salesorder_id = generate_id("SO")
    
    # Process line items
    processed_items = []
    for idx, item in enumerate(salesorder.line_items):
        item_dict = item.dict()
        
        # If item_id provided, fetch item details
        if item.item_id:
            item_details = await get_item_details(item.item_id)
            if item_details:
                item_dict["name"] = item.name or item_details.get("name", "")
                item_dict["description"] = item.description or item_details.get("description", "")
                item_dict["hsn_code"] = item.hsn_code or item_details.get("hsn_code", "")
                item_dict["unit"] = item.unit or item_details.get("unit", "pcs")
                item_dict["track_inventory"] = item_details.get("track_inventory", False)
                if item.rate == 0:
                    item_dict["rate"] = item_details.get("rate", 0)
                if item.tax_percentage == 0:
                    item_dict["tax_percentage"] = item_details.get("tax_percentage", 0)
                
                # Check stock availability for inventory items
                if item_details.get("track_inventory"):
                    available = item_details.get("stock_on_hand", 0) - item_details.get("reserved_stock", 0)
                    if item.quantity > available:
                        item_dict["stock_warning"] = f"Only {available} available"
        
        # Calculate line item totals
        totals = calculate_line_item_totals(item_dict, gst_type)
        item_dict.update(totals)
        item_dict["line_item_id"] = generate_id("LI")
        item_dict["salesorder_id"] = salesorder_id
        item_dict["line_number"] = idx + 1
        item_dict["quantity_ordered"] = item.quantity
        item_dict["quantity_fulfilled"] = 0
        
        processed_items.append(item_dict)
    
    # Calculate salesorder totals
    totals = calculate_salesorder_totals(
        processed_items,
        salesorder.discount_type,
        salesorder.discount_value,
        salesorder.shipping_charge,
        salesorder.adjustment,
        gst_type
    )
    
    # Use addresses from request or customer defaults
    billing_address = salesorder.billing_address or customer.get("billing_address")
    shipping_address = salesorder.shipping_address or customer.get("shipping_address")
    
    # Build sales order document
    salesorder_doc = {
        "salesorder_id": salesorder_id,
        "salesorder_number": salesorder_number,
        "reference_number": salesorder.reference_number,
        "customer_id": salesorder.customer_id,
        "customer_name": customer.get("name", ""),
        "customer_email": customer.get("email", ""),
        "customer_gstin": customer.get("gstin", ""),
        "place_of_supply": customer_state,
        "date": salesorder_date,
        "expected_shipment_date": expected_shipment_date,
        "status": "draft",
        "fulfillment_status": "unfulfilled",  # unfulfilled, partially_fulfilled, fulfilled
        "salesperson_id": salesorder.salesperson_id,
        "salesperson_name": salesorder.salesperson_name,
        "project_id": salesorder.project_id,
        "billing_address": billing_address,
        "shipping_address": shipping_address,
        "line_items_count": len(processed_items),
        "discount_type": salesorder.discount_type,
        "discount_value": salesorder.discount_value,
        "shipping_charge": salesorder.shipping_charge,
        "adjustment": salesorder.adjustment,
        "adjustment_description": salesorder.adjustment_description,
        **totals,
        "terms_and_conditions": salesorder.terms_and_conditions or (defaults.get("terms_and_conditions", "") if defaults else ""),
        "notes": salesorder.notes,
        "custom_fields": salesorder.custom_fields,
        "delivery_method": salesorder.delivery_method,
        # Source tracking
        "from_estimate_id": salesorder.from_estimate_id,
        "from_estimate_number": salesorder.from_estimate_number,
        # Conversion tracking
        "converted_to": None,
        "invoiced_amount": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Insert salesorder and line items
    await salesorders_collection.insert_one(salesorder_doc)
    if processed_items:
        await salesorder_items_collection.insert_many(processed_items)
    
    # Add history entry
    await add_salesorder_history(salesorder_id, "created", f"Sales Order {salesorder_number} created")
    
    # Remove _id from response
    salesorder_doc.pop("_id", None)
    salesorder_doc["line_items"] = [{k: v for k, v in item.items() if k != "_id"} for item in processed_items]
    
    return {"code": 0, "message": "Sales Order created", "salesorder": salesorder_doc}

@router.get("/")
async def list_sales_orders(
    status: Optional[str] = None,
    fulfillment_status: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List sales orders with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {}

    if status:
        query["status"] = status

    if fulfillment_status:
        query["fulfillment_status"] = fulfillment_status

    if customer_id:
        query["customer_id"] = customer_id

    if search:
        query["$or"] = [
            {"salesorder_number": {"$regex": search, "$options": "i"}},
            {"reference_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}}
        ]

    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}

    total = await salesorders_collection.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    salesorders = await salesorders_collection.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": salesorders,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/summary")
async def get_salesorders_summary(request: Request):
    """Get sales orders summary statistics"""
    org_id = extract_org_id(request)
    base = org_query(org_id)
    total = await salesorders_collection.count_documents(base)
    draft = await salesorders_collection.count_documents(org_query(org_id, {"status": "draft"}))
    confirmed = await salesorders_collection.count_documents(org_query(org_id, {"status": "confirmed"}))
    open_count = await salesorders_collection.count_documents(org_query(org_id, {"status": "open"}))
    fulfilled = await salesorders_collection.count_documents(org_query(org_id, {"fulfillment_status": "fulfilled"}))
    partially_fulfilled = await salesorders_collection.count_documents(org_query(org_id, {"fulfillment_status": "partially_fulfilled"}))
    closed = await salesorders_collection.count_documents(org_query(org_id, {"status": "closed"}))
    voided = await salesorders_collection.count_documents(org_query(org_id, {"status": "void"}))
    
    # Calculate totals
    pipeline = [
        {"$match": {"status": {"$nin": ["void"]}}},
        {"$group": {
            "_id": None,
            "total_value": {"$sum": "$grand_total"},
            "open_value": {"$sum": {"$cond": [{"$in": ["$status", ["confirmed", "open"]]}, "$grand_total", 0]}},
            "invoiced_amount": {"$sum": "$invoiced_amount"}
        }}
    ]
    
    stats = await salesorders_collection.aggregate(pipeline).to_list(1)
    values = stats[0] if stats else {"total_value": 0, "open_value": 0, "invoiced_amount": 0}
    
    return {
        "code": 0,
        "summary": {
            "total": total,
            "by_status": {
                "draft": draft,
                "confirmed": confirmed,
                "open": open_count,
                "closed": closed,
                "void": voided
            },
            "by_fulfillment": {
                "unfulfilled": total - fulfilled - partially_fulfilled,
                "partially_fulfilled": partially_fulfilled,
                "fulfilled": fulfilled
            },
            "total_value": round(values.get("total_value", 0), 2),
            "open_value": round(values.get("open_value", 0), 2),
            "invoiced_amount": round(values.get("invoiced_amount", 0), 2),
            "pending_invoice": round(values.get("open_value", 0) - values.get("invoiced_amount", 0), 2)
        }
    }

@router.get("/{salesorder_id}")
async def get_sales_order(salesorder_id: str):
    """Get sales order details with line items and history"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id}, {"_id": 0})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    # Get line items
    line_items = await salesorder_items_collection.find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).sort("line_number", 1).to_list(100)
    salesorder["line_items"] = line_items
    
    # Get customer details
    customer = await get_contact_details(salesorder["customer_id"])
    salesorder["customer_details"] = customer
    
    # Get history
    history = await salesorder_history_collection.find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    salesorder["history"] = history
    
    # Get fulfillments
    fulfillments = await db["salesorder_fulfillments"].find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    salesorder["fulfillments"] = fulfillments
    
    return {"code": 0, "salesorder": salesorder}

@router.put("/{salesorder_id}")
async def update_sales_order(salesorder_id: str, salesorder: SalesOrderUpdate):
    """Update a sales order (only if draft status)"""
    existing = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    if existing.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Only draft sales orders can be edited")
    
    update_data = {k: v for k, v in salesorder.dict().items() if v is not None}
    
    # If customer changed, recalculate GST type
    if "customer_id" in update_data:
        customer = await get_contact_details(update_data["customer_id"])
        if customer:
            customer_state = customer.get("place_of_supply", "")
            gst_type = calculate_gst_type(ORG_STATE_CODE, customer_state)
            update_data["customer_name"] = customer.get("name", "")
            update_data["customer_email"] = customer.get("email", "")
            update_data["customer_gstin"] = customer.get("gstin", "")
            update_data["place_of_supply"] = customer_state
            update_data["gst_type"] = gst_type
    
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        await salesorders_collection.update_one({"salesorder_id": salesorder_id}, {"$set": update_data})
    
    await add_salesorder_history(salesorder_id, "updated", "Sales Order details updated")
    
    updated = await salesorders_collection.find_one({"salesorder_id": salesorder_id}, {"_id": 0})
    return {"code": 0, "message": "Sales Order updated", "salesorder": updated}

@router.delete("/{salesorder_id}")
async def delete_sales_order(salesorder_id: str):
    """Delete a sales order (only if draft status)"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    if salesorder.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Only draft sales orders can be deleted")
    
    # Delete salesorder and line items
    await salesorders_collection.delete_one({"salesorder_id": salesorder_id})
    await salesorder_items_collection.delete_many({"salesorder_id": salesorder_id})
    await salesorder_history_collection.delete_many({"salesorder_id": salesorder_id})
    
    return {"code": 0, "message": "Sales Order deleted"}

# ========================= LINE ITEMS ENDPOINTS =========================

@router.post("/{salesorder_id}/line-items")
async def add_line_item(salesorder_id: str, item: LineItemCreate):
    """Add a line item to a sales order"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    if salesorder.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Cannot modify non-draft sales orders")
    
    gst_type = salesorder.get("gst_type", "igst")
    
    item_dict = item.dict()
    
    if item.item_id:
        item_details = await get_item_details(item.item_id)
        if item_details:
            item_dict["name"] = item.name or item_details.get("name", "")
            item_dict["hsn_code"] = item.hsn_code or item_details.get("hsn_code", "")
            item_dict["unit"] = item.unit or item_details.get("unit", "pcs")
            item_dict["track_inventory"] = item_details.get("track_inventory", False)
            if item.rate == 0:
                item_dict["rate"] = item_details.get("rate", 0)
            if item.tax_percentage == 0:
                item_dict["tax_percentage"] = item_details.get("tax_percentage", 0)
    
    # Calculate totals
    totals = calculate_line_item_totals(item_dict, gst_type)
    item_dict.update(totals)
    
    # Get next line number
    max_line = await salesorder_items_collection.find_one(
        {"salesorder_id": salesorder_id},
        sort=[("line_number", -1)]
    )
    next_line = (max_line.get("line_number", 0) if max_line else 0) + 1
    
    item_dict["line_item_id"] = generate_id("LI")
    item_dict["salesorder_id"] = salesorder_id
    item_dict["line_number"] = next_line
    item_dict["quantity_ordered"] = item.quantity
    item_dict["quantity_fulfilled"] = 0
    
    await salesorder_items_collection.insert_one(item_dict)
    
    # Recalculate salesorder totals
    await recalculate_salesorder_totals(salesorder_id)
    
    item_dict.pop("_id", None)
    return {"code": 0, "message": "Line item added", "line_item": item_dict}

@router.put("/{salesorder_id}/line-items/{line_item_id}")
async def update_line_item(salesorder_id: str, line_item_id: str, item: LineItemUpdate):
    """Update a line item"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    if salesorder.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Cannot modify non-draft sales orders")
    
    existing = await salesorder_items_collection.find_one({"line_item_id": line_item_id, "salesorder_id": salesorder_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    update_data = {k: v for k, v in item.dict().items() if v is not None}
    
    if update_data:
        merged = {**existing, **update_data}
        gst_type = salesorder.get("gst_type", "igst")
        totals = calculate_line_item_totals(merged, gst_type)
        update_data.update(totals)
        update_data["quantity_ordered"] = merged.get("quantity", existing.get("quantity_ordered", 0))
        
        await salesorder_items_collection.update_one(
            {"line_item_id": line_item_id},
            {"$set": update_data}
        )
    
    # Recalculate salesorder totals
    await recalculate_salesorder_totals(salesorder_id)
    
    updated = await salesorder_items_collection.find_one({"line_item_id": line_item_id}, {"_id": 0})
    return {"code": 0, "message": "Line item updated", "line_item": updated}

@router.delete("/{salesorder_id}/line-items/{line_item_id}")
async def delete_line_item(salesorder_id: str, line_item_id: str):
    """Delete a line item"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    if salesorder.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Cannot modify non-draft sales orders")
    
    result = await salesorder_items_collection.delete_one({"line_item_id": line_item_id, "salesorder_id": salesorder_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Recalculate salesorder totals
    await recalculate_salesorder_totals(salesorder_id)
    
    return {"code": 0, "message": "Line item deleted"}

async def recalculate_salesorder_totals(salesorder_id: str):
    """Recalculate and update sales order totals"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        return
    
    line_items = await salesorder_items_collection.find({"salesorder_id": salesorder_id}, {"_id": 0}).to_list(100)
    
    totals = calculate_salesorder_totals(
        line_items,
        salesorder.get("discount_type", "none"),
        salesorder.get("discount_value", 0),
        salesorder.get("shipping_charge", 0),
        salesorder.get("adjustment", 0),
        salesorder.get("gst_type", "igst")
    )
    
    totals["line_items_count"] = len(line_items)
    totals["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    await salesorders_collection.update_one({"salesorder_id": salesorder_id}, {"$set": totals})

# ========================= STATUS WORKFLOW ENDPOINTS =========================

@router.put("/{salesorder_id}/status")
async def update_salesorder_status(salesorder_id: str, status_update: StatusUpdate):
    """Update sales order status"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    current_status = salesorder.get("status")
    new_status = status_update.status
    
    # Validate status transitions
    valid_transitions = {
        "draft": ["confirmed", "void"],
        "confirmed": ["open", "void"],
        "open": ["fulfilled", "partially_fulfilled", "closed", "void"],
        "partially_fulfilled": ["fulfilled", "closed", "void"],
        "fulfilled": ["closed"],
        "closed": [],  # Final state
        "void": []  # Final state
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status}' to '{new_status}'"
        )
    
    update_data = {
        "status": new_status,
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Handle stock reservation when confirming
    if new_status == "confirmed" and current_status == "draft":
        line_items = await salesorder_items_collection.find({"salesorder_id": salesorder_id}, {"_id": 0}).to_list(100)
        await reserve_stock(salesorder_id, line_items)
        update_data["confirmed_date"] = datetime.now(timezone.utc).date().isoformat()
    
    # Release stock when voiding
    if new_status == "void":
        await release_reserved_stock(salesorder_id)
        update_data["void_reason"] = status_update.reason
    
    await salesorders_collection.update_one({"salesorder_id": salesorder_id}, {"$set": update_data})
    
    await add_salesorder_history(
        salesorder_id,
        f"status_changed",
        f"Status changed from '{current_status}' to '{new_status}'" + (f": {status_update.reason}" if status_update.reason else "")
    )
    
    return {"code": 0, "message": f"Status updated to {new_status}"}

@router.post("/{salesorder_id}/confirm")
async def confirm_sales_order(salesorder_id: str):
    """Confirm sales order and reserve stock"""
    return await update_salesorder_status(salesorder_id, StatusUpdate(status="confirmed"))

@router.post("/{salesorder_id}/void")
async def void_sales_order(salesorder_id: str, reason: str = ""):
    """Void sales order and release reserved stock"""
    return await update_salesorder_status(salesorder_id, StatusUpdate(status="void", reason=reason))

# ========================= FULFILLMENT ENDPOINTS =========================

@router.post("/{salesorder_id}/fulfill")
async def create_fulfillment(salesorder_id: str, fulfillment: FulfillmentCreate):
    """Create a fulfillment/shipment for sales order"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    if salesorder.get("status") not in ["confirmed", "open", "partially_fulfilled"]:
        raise HTTPException(status_code=400, detail="Sales Order must be confirmed to fulfill")
    
    # Validate and process fulfillment items
    fulfillment_id = generate_id("FUL")
    fulfilled_items = []
    
    for item in fulfillment.line_items:
        line_item = await salesorder_items_collection.find_one(
            {"line_item_id": item.get("line_item_id"), "salesorder_id": salesorder_id},
            {"_id": 0}
        )
        if not line_item:
            continue
        
        remaining = float(line_item.get("quantity_ordered", 0)) - float(line_item.get("quantity_fulfilled", 0))
        qty_to_fulfill = min(float(item.get("quantity_to_fulfill", 0)), remaining)
        
        if qty_to_fulfill > 0:
            fulfilled_items.append({
                **item,
                "quantity_to_fulfill": qty_to_fulfill,
                "item_name": line_item.get("name", ""),
                "item_id": line_item.get("item_id")
            })
    
    if not fulfilled_items:
        raise HTTPException(status_code=400, detail="No valid items to fulfill")
    
    # Create fulfillment record
    fulfillment_doc = {
        "fulfillment_id": fulfillment_id,
        "salesorder_id": salesorder_id,
        "shipment_date": fulfillment.shipment_date or datetime.now(timezone.utc).date().isoformat(),
        "tracking_number": fulfillment.tracking_number,
        "carrier": fulfillment.carrier,
        "notes": fulfillment.notes,
        "items": fulfilled_items,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["salesorder_fulfillments"].insert_one(fulfillment_doc)
    
    # Deduct stock
    await deduct_stock(salesorder_id, fulfilled_items)
    
    # Update fulfillment status
    line_items = await salesorder_items_collection.find({"salesorder_id": salesorder_id}, {"_id": 0}).to_list(100)
    total_ordered = sum(float(li.get("quantity_ordered", 0)) for li in line_items)
    total_fulfilled = sum(float(li.get("quantity_fulfilled", 0)) for li in line_items)
    
    if total_fulfilled >= total_ordered:
        fulfillment_status = "fulfilled"
    elif total_fulfilled > 0:
        fulfillment_status = "partially_fulfilled"
    else:
        fulfillment_status = "unfulfilled"
    
    new_status = "fulfilled" if fulfillment_status == "fulfilled" else "open"
    
    await salesorders_collection.update_one(
        {"salesorder_id": salesorder_id},
        {"$set": {
            "fulfillment_status": fulfillment_status,
            "status": new_status,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_salesorder_history(salesorder_id, "fulfilled", f"Fulfillment {fulfillment_id} created")
    
    fulfillment_doc.pop("_id", None)
    return {"code": 0, "message": "Fulfillment created", "fulfillment": fulfillment_doc}

@router.get("/{salesorder_id}/fulfillments")
async def get_fulfillments(salesorder_id: str):
    """Get all fulfillments for a sales order"""
    fulfillments = await db["salesorder_fulfillments"].find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"code": 0, "fulfillments": fulfillments}

# ========================= CONVERSION ENDPOINTS =========================

@router.post("/{salesorder_id}/convert-to-invoice")
async def convert_to_invoice(salesorder_id: str, invoice_all: bool = True):
    """Convert sales order to invoice"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    if salesorder.get("status") not in ["confirmed", "open", "fulfilled", "partially_fulfilled"]:
        raise HTTPException(status_code=400, detail="Sales Order must be confirmed to invoice")
    
    # Get line items
    line_items = await salesorder_items_collection.find({"salesorder_id": salesorder_id}, {"_id": 0}).to_list(100)
    
    # Generate invoice number
    inv_settings = await db["invoice_settings"].find_one({"type": "numbering"})
    if not inv_settings:
        inv_settings = {"prefix": "INV-", "next_number": 1, "padding": 5}
        await db["invoice_settings"].insert_one({**inv_settings, "type": "numbering"})
    
    invoice_number = f"{inv_settings.get('prefix', 'INV-')}{str(inv_settings.get('next_number', 1)).zfill(inv_settings.get('padding', 5))}"
    await db["invoice_settings"].update_one({"type": "numbering"}, {"$inc": {"next_number": 1}})
    
    invoice_id = generate_id("INV")
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Determine quantities to invoice
    items_to_invoice = []
    for item in line_items:
        if invoice_all:
            qty = float(item.get("quantity_ordered", 0))
        else:
            qty = float(item.get("quantity_fulfilled", 0))
        
        if qty > 0:
            items_to_invoice.append({**item, "quantity": qty})
    
    # Create invoice
    invoice_doc = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "customer_id": salesorder["customer_id"],
        "customer_name": salesorder.get("customer_name", ""),
        "customer_email": salesorder.get("customer_email", ""),
        "customer_gstin": salesorder.get("customer_gstin", ""),
        "place_of_supply": salesorder.get("place_of_supply", ""),
        "date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat(),
        "status": "draft",
        "reference_number": salesorder.get("reference_number", ""),
        "salesorder_id": salesorder_id,
        "salesorder_number": salesorder.get("salesorder_number", ""),
        "salesperson_id": salesorder.get("salesperson_id"),
        "salesperson_name": salesorder.get("salesperson_name", ""),
        "project_id": salesorder.get("project_id"),
        "billing_address": salesorder.get("billing_address"),
        "shipping_address": salesorder.get("shipping_address"),
        "line_items_count": len(items_to_invoice),
        "discount_type": salesorder.get("discount_type", "none"),
        "discount_value": salesorder.get("discount_value", 0),
        "shipping_charge": salesorder.get("shipping_charge", 0),
        "adjustment": salesorder.get("adjustment", 0),
        "adjustment_description": salesorder.get("adjustment_description", ""),
        "subtotal": salesorder.get("subtotal", 0),
        "total_discount": salesorder.get("total_discount", 0),
        "total_tax": salesorder.get("total_tax", 0),
        "total_cgst": salesorder.get("total_cgst", 0),
        "total_sgst": salesorder.get("total_sgst", 0),
        "total_igst": salesorder.get("total_igst", 0),
        "grand_total": salesorder.get("grand_total", 0),
        "total": salesorder.get("grand_total", 0),
        "balance_due": salesorder.get("grand_total", 0),
        "amount_paid": 0,
        "gst_type": salesorder.get("gst_type", "igst"),
        "terms_and_conditions": salesorder.get("terms_and_conditions", ""),
        "notes": salesorder.get("notes", ""),
        "custom_fields": salesorder.get("custom_fields", {}),
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db["invoices"].insert_one(invoice_doc)
    
    # Copy line items
    for item in items_to_invoice:
        item["invoice_id"] = invoice_id
        item["line_item_id"] = generate_id("LI")
        item.pop("salesorder_id", None)
        await db["invoice_line_items"].insert_one(item)
    
    # Update sales order
    await salesorders_collection.update_one(
        {"salesorder_id": salesorder_id},
        {"$set": {
            "converted_to": f"invoice:{invoice_id}",
            "invoiced_amount": salesorder.get("grand_total", 0),
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_salesorder_history(salesorder_id, "converted", f"Converted to Invoice {invoice_number}")
    
    invoice_doc.pop("_id", None)
    return {
        "code": 0,
        "message": f"Sales Order converted to Invoice {invoice_number}",
        "invoice_id": invoice_id,
        "invoice_number": invoice_number
    }

# ========================= CLONE ENDPOINT =========================

@router.post("/{salesorder_id}/clone")
async def clone_sales_order(salesorder_id: str):
    """Clone a sales order"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    # Get line items
    line_items = await salesorder_items_collection.find({"salesorder_id": salesorder_id}, {"_id": 0}).to_list(100)
    
    # Create new sales order
    new_salesorder_id = generate_id("SO")
    new_salesorder_number = await get_next_salesorder_number()
    today = datetime.now(timezone.utc).date().isoformat()
    
    defaults = await salesorder_settings_collection.find_one({"type": "defaults"})
    shipment_days = defaults.get("shipment_days", 7) if defaults else 7
    expected_shipment = (datetime.now(timezone.utc) + timedelta(days=shipment_days)).date().isoformat()
    
    # Clone sales order
    new_salesorder = {**salesorder}
    new_salesorder["salesorder_id"] = new_salesorder_id
    new_salesorder["salesorder_number"] = new_salesorder_number
    new_salesorder["date"] = today
    new_salesorder["expected_shipment_date"] = expected_shipment
    new_salesorder["status"] = "draft"
    new_salesorder["fulfillment_status"] = "unfulfilled"
    new_salesorder["converted_to"] = None
    new_salesorder["invoiced_amount"] = 0
    new_salesorder["from_estimate_id"] = None
    new_salesorder["from_estimate_number"] = None
    new_salesorder["created_time"] = datetime.now(timezone.utc).isoformat()
    new_salesorder["updated_time"] = datetime.now(timezone.utc).isoformat()
    new_salesorder.pop("_id", None)
    
    await salesorders_collection.insert_one(new_salesorder)
    
    # Clone line items
    for item in line_items:
        new_item = {**item}
        new_item["line_item_id"] = generate_id("LI")
        new_item["salesorder_id"] = new_salesorder_id
        new_item["quantity_fulfilled"] = 0
        new_item.pop("_id", None)
        await salesorder_items_collection.insert_one(new_item)
    
    await add_salesorder_history(new_salesorder_id, "created", f"Cloned from {salesorder.get('salesorder_number')}")
    
    return {
        "code": 0,
        "message": f"Sales Order cloned as {new_salesorder_number}",
        "salesorder_id": new_salesorder_id,
        "salesorder_number": new_salesorder_number
    }

# ========================= EMAIL ENDPOINT =========================

@router.post("/{salesorder_id}/send")
async def send_sales_order(salesorder_id: str, email_to: Optional[str] = None, message: str = ""):
    """Send sales order to customer (mocked)"""
    salesorder = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not salesorder:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    recipient = email_to or salesorder.get("customer_email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    email_body = f"""
Dear {salesorder.get('customer_name', 'Customer')},

Please find attached the Sales Order {salesorder.get('salesorder_number')} for your records.

Order Total: ₹{salesorder.get('grand_total', 0):,.2f}
Expected Shipment: {salesorder.get('expected_shipment_date', 'N/A')}

{message}

Best regards,
Battwheels Team
"""
    
    mock_send_email(
        recipient,
        f"Sales Order {salesorder.get('salesorder_number')} from Battwheels",
        email_body,
        f"SalesOrder_{salesorder.get('salesorder_number')}.pdf"
    )
    
    await salesorders_collection.update_one(
        {"salesorder_id": salesorder_id},
        {"$set": {
            "sent_date": datetime.now(timezone.utc).isoformat(),
            "sent_to": recipient,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_salesorder_history(salesorder_id, "sent", f"Sales Order sent to {recipient}")
    
    return {"code": 0, "message": f"Sales Order sent to {recipient}"}

# ========================= REPORTING ENDPOINTS =========================

@router.get("/reports/by-status")
async def report_by_status(date_from: str = "", date_to: str = ""):
    """Report: Sales Orders by status"""
    query = {}
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_value": {"$sum": "$grand_total"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = await salesorders_collection.aggregate(pipeline).to_list(10)
    
    return {
        "code": 0,
        "report": [{"status": r["_id"], "count": r["count"], "total_value": round(r["total_value"], 2)} for r in results]
    }

@router.get("/reports/by-customer")
async def report_by_customer(limit: int = 20):
    """Report: Top customers by sales order value"""
    pipeline = [
        {"$match": {"status": {"$nin": ["void"]}}},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "count": {"$sum": 1},
            "total_value": {"$sum": "$grand_total"},
            "fulfilled_count": {"$sum": {"$cond": [{"$eq": ["$fulfillment_status", "fulfilled"]}, 1, 0]}}
        }},
        {"$sort": {"total_value": -1}},
        {"$limit": limit}
    ]
    
    results = await salesorders_collection.aggregate(pipeline).to_list(limit)
    
    for r in results:
        r["customer_id"] = r.pop("_id")
        r["total_value"] = round(r["total_value"], 2)
        r["fulfillment_rate"] = round((r["fulfilled_count"] / r["count"]) * 100, 1) if r["count"] > 0 else 0
    
    return {"code": 0, "report": results}

@router.get("/reports/fulfillment-summary")
async def report_fulfillment_summary():
    """Report: Fulfillment summary"""
    total = await salesorders_collection.count_documents({"status": {"$ne": "void"}})
    unfulfilled = await salesorders_collection.count_documents({"fulfillment_status": "unfulfilled", "status": {"$nin": ["void", "draft"]}})
    partially = await salesorders_collection.count_documents({"fulfillment_status": "partially_fulfilled"})
    fulfilled = await salesorders_collection.count_documents({"fulfillment_status": "fulfilled"})
    
    # Value breakdown
    pipeline = [
        {"$match": {"status": {"$nin": ["void"]}}},
        {"$group": {
            "_id": "$fulfillment_status",
            "total_value": {"$sum": "$grand_total"}
        }}
    ]
    
    values = await salesorders_collection.aggregate(pipeline).to_list(5)
    value_map = {v["_id"]: v["total_value"] for v in values}
    
    return {
        "code": 0,
        "summary": {
            "total_orders": total,
            "unfulfilled": unfulfilled,
            "partially_fulfilled": partially,
            "fulfilled": fulfilled,
            "unfulfilled_value": round(value_map.get("unfulfilled", 0), 2),
            "partially_fulfilled_value": round(value_map.get("partially_fulfilled", 0), 2),
            "fulfilled_value": round(value_map.get("fulfilled", 0), 2),
            "fulfillment_rate": round((fulfilled / total) * 100, 1) if total > 0 else 0
        }
    }

# ==================== SALES ORDER PDF ====================

@router.get("/{salesorder_id}/pdf")
async def get_sales_order_pdf(salesorder_id: str):
    """Generate Sales Order PDF"""
    from io import BytesIO
    
    order = await salesorders_collection.find_one({"salesorder_id": salesorder_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    # Get line items
    line_items = await salesorder_items_collection.find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get organization settings
    org_settings = await db["organization_settings"].find_one({}, {"_id": 0}) or {}
    
    # Generate HTML
    status_badge = {
        "draft": "#6B7280",
        "confirmed": "#3B82F6",
        "fulfilled": "#22C55E",
        "partially_fulfilled": "#F59E0B",
        "closed": "#9333EA",
        "void": "#EF4444"
    }.get(order.get("status", "draft"), "#6B7280")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; color: #333; font-size: 12px; }}
            .document {{ max-width: 800px; margin: 0 auto; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #22EDA9; padding-bottom: 20px; margin-bottom: 20px; }}
            .company-name {{ font-size: 20px; font-weight: bold; }}
            .doc-title {{ font-size: 24px; color: #22EDA9; font-weight: bold; }}
            .doc-number {{ color: #666; font-size: 14px; }}
            .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; color: white; font-size: 11px; background: {status_badge}; }}
            .section {{ margin-bottom: 20px; }}
            .section-title {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #f8f9fa; padding: 10px; text-align: left; font-size: 11px; text-transform: uppercase; border-bottom: 2px solid #22EDA9; }}
            td {{ padding: 10px; border-bottom: 1px solid #eee; }}
            .totals {{ margin-top: 20px; text-align: right; }}
            .totals-row {{ display: flex; justify-content: flex-end; margin-bottom: 5px; }}
            .totals-label {{ width: 150px; color: #666; }}
            .totals-value {{ width: 100px; font-weight: bold; }}
            .grand-total {{ font-size: 18px; color: #22EDA9; background: #f8f9fa; padding: 10px; }}
        </style>
    </head>
    <body>
        <div class="document">
            <div class="header">
                <div>
                    <div class="company-name">{org_settings.get('company_name', 'Battwheels OS')}</div>
                    <div style="color: #666; margin-top: 5px;">
                        {org_settings.get('address', '')}<br>
                        GSTIN: {org_settings.get('gstin', '')}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="doc-title">SALES ORDER</div>
                    <div class="doc-number">#{order.get('salesorder_number', salesorder_id)}</div>
                    <div style="margin-top: 10px;"><span class="status-badge">{order.get('status', 'draft').upper()}</span></div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between;">
                <div class="section">
                    <div class="section-title">Customer</div>
                    <div style="font-weight: bold;">{order.get('customer_name', 'N/A')}</div>
                    <div style="color: #666;">{order.get('billing_address', {}).get('street', '')}</div>
                    <div style="color: #666;">{order.get('billing_address', {}).get('city', '')} {order.get('billing_address', {}).get('state', '')}</div>
                </div>
                <div class="section" style="text-align: right;">
                    <div class="section-title">Order Date</div>
                    <div>{order.get('date', '')}</div>
                    <div class="section-title" style="margin-top: 10px;">Expected Ship Date</div>
                    <div>{order.get('expected_shipment_date', 'N/A')}</div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Item</th>
                        <th style="text-align: center;">Qty</th>
                        <th style="text-align: right;">Rate</th>
                        <th style="text-align: right;">Tax</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for idx, item in enumerate(line_items, 1):
        html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td>
                            <div style="font-weight: bold;">{item.get('name', item.get('item_name', ''))}</div>
                            <div style="font-size: 10px; color: #666;">{item.get('description', '')}</div>
                        </td>
                        <td style="text-align: center;">{item.get('quantity', 0)} {item.get('unit', '')}</td>
                        <td style="text-align: right;">₹{item.get('rate', 0):,.2f}</td>
                        <td style="text-align: right;">{item.get('tax_percentage', item.get('tax_rate', 0))}%</td>
                        <td style="text-align: right;">₹{item.get('item_total', item.get('amount', 0)):,.2f}</td>
                    </tr>
        """
    
    html_content += f"""
                </tbody>
            </table>
            
            <div class="totals">
                <div class="totals-row">
                    <div class="totals-label">Sub Total:</div>
                    <div class="totals-value">₹{order.get('sub_total', 0):,.2f}</div>
                </div>
                {f'<div class="totals-row"><div class="totals-label">Discount:</div><div class="totals-value">-₹{order.get("discount_total", 0):,.2f}</div></div>' if order.get('discount_total', 0) > 0 else ''}
                <div class="totals-row">
                    <div class="totals-label">Tax:</div>
                    <div class="totals-value">₹{order.get('tax_total', 0):,.2f}</div>
                </div>
                {f'<div class="totals-row"><div class="totals-label">Shipping:</div><div class="totals-value">₹{order.get("shipping_charge", 0):,.2f}</div></div>' if order.get('shipping_charge', 0) > 0 else ''}
                <div class="totals-row grand-total">
                    <div class="totals-label">Grand Total:</div>
                    <div class="totals-value">₹{order.get('grand_total', 0):,.2f}</div>
                </div>
            </div>
            
            {f'<div class="section" style="margin-top: 30px;"><div class="section-title">Notes</div><div>{order.get("notes", "")}</div></div>' if order.get('notes') else ''}
            {f'<div class="section"><div class="section-title">Terms & Conditions</div><div style="font-size: 10px; color: #666;">{order.get("terms_conditions", "")}</div></div>' if order.get('terms_conditions') else ''}
        </div>
    </body>
    </html>
    """
    
    try:
        from weasyprint import HTML
        from fastapi.responses import StreamingResponse
        
        pdf_buffer = BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=SalesOrder_{order.get('salesorder_number', salesorder_id)}.pdf"
            }
        )
    except Exception as e:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

# ==================== ACTIVITY LOG ====================

@router.get("/{salesorder_id}/activity")
async def get_sales_order_activity(salesorder_id: str, limit: int = 50):
    """Get activity log for a sales order"""
    order = await salesorders_collection.find_one({"salesorder_id": salesorder_id})
    if not order:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    # Get from history collection
    history = await salesorder_history_collection.find(
        {"salesorder_id": salesorder_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    if not history:
        # Create basic activity from order data
        history = [
            {
                "action": "created",
                "details": f"Sales Order {order.get('salesorder_number', '')} created",
                "timestamp": order.get("created_at", order.get("date", ""))
            }
        ]
    
    return {"code": 0, "activities": history}
