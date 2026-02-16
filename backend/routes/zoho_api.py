"""
Complete Zoho Books-like API Module
Mirrors Zoho Books API v3 structure with all modules and workflows
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from enum import Enum
import os
import uuid

router = APIRouter(prefix="/zoho", tags=["Zoho Books API"])

# Database connection
def get_db():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]

# ============== HELPER FUNCTIONS ==============

async def get_next_number(db, collection: str, prefix: str):
    """Get next sequential number for a document type"""
    counter = await db.counters.find_one_and_update(
        {"_id": collection},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return f"{prefix}-{str(counter['seq']).zfill(6)}"

def calculate_line_totals(line_items: List[Dict], discount_percent: float = 0, 
                          shipping_charge: float = 0, adjustment: float = 0):
    """Calculate all totals for a transaction"""
    subtotal = 0
    discount_total = 0
    tax_total = 0
    calculated_items = []
    
    for item in line_items:
        item_subtotal = item.get('quantity', 1) * item.get('rate', 0)
        item_discount = item_subtotal * (item.get('discount_percent', 0) / 100)
        taxable_amount = item_subtotal - item_discount
        item_tax = taxable_amount * (item.get('tax_rate', 18) / 100)
        
        calculated_items.append({
            **item,
            "item_subtotal": round(item_subtotal, 2),
            "discount_amount": round(item_discount, 2),
            "taxable_amount": round(taxable_amount, 2),
            "tax_amount": round(item_tax, 2),
            "item_total": round(taxable_amount + item_tax, 2)
        })
        
        subtotal += taxable_amount
        discount_total += item_discount
        tax_total += item_tax
    
    entity_discount = subtotal * (discount_percent / 100) if discount_percent > 0 else 0
    grand_total = subtotal - entity_discount + tax_total + shipping_charge + adjustment
    
    return {
        "line_items": calculated_items,
        "sub_total": round(subtotal, 2),
        "discount_total": round(discount_total + entity_discount, 2),
        "tax_total": round(tax_total, 2),
        "shipping_charge": round(shipping_charge, 2),
        "adjustment": round(adjustment, 2),
        "total": round(grand_total, 2)
    }

# ============== CONTACTS MODULE ==============
# Workflow: Create -> List/Get -> Update -> Mark Active/Inactive -> Enable Portal -> Email -> Delete

class ContactCreate(BaseModel):
    contact_name: str
    company_name: Optional[str] = ""
    contact_type: str = "customer"  # customer, vendor
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    mobile: Optional[str] = ""
    website: Optional[str] = ""
    gst_no: Optional[str] = ""
    gst_treatment: str = "business_gst"
    pan_no: Optional[str] = ""
    place_of_supply: str = "DL"
    billing_address: Optional[Dict] = {}
    shipping_address: Optional[Dict] = {}
    payment_terms: int = 15
    payment_terms_label: str = "Net 15"
    currency_code: str = "INR"
    notes: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/contacts")
async def create_contact(contact: ContactCreate):
    """Create a new contact (customer or vendor)"""
    db = get_db()
    contact_id = f"C-{uuid.uuid4().hex[:12].upper()}"
    contact_number = await get_next_number(db, "contacts", "CONT")
    
    contact_dict = {
        "contact_id": contact_id,
        "contact_number": contact_number,
        **contact.dict(),
        "status": "active",
        "outstanding_receivable_amount": 0,
        "outstanding_payable_amount": 0,
        "unused_credits_receivable_amount": 0,
        "unused_credits_payable_amount": 0,
        "portal_enabled": False,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.contacts.insert_one(contact_dict)
    del contact_dict["_id"]
    return {"code": 0, "message": "Contact created successfully", "contact": contact_dict}

@router.get("/contacts")
async def list_contacts(
    contact_type: str = "",
    status: str = "active",
    search_text: str = "",
    page: int = 1,
    per_page: int = 25,
    sort_column: str = "contact_name",
    sort_order: str = "ascending"
):
    """List all contacts with filters"""
    db = get_db()
    query = {}
    if contact_type:
        query["contact_type"] = contact_type
    if status:
        query["status"] = status
    if search_text:
        query["$or"] = [
            {"contact_name": {"$regex": search_text, "$options": "i"}},
            {"email": {"$regex": search_text, "$options": "i"}},
            {"phone": {"$regex": search_text, "$options": "i"}}
        ]
    
    sort_dir = 1 if sort_order == "ascending" else -1
    skip = (page - 1) * per_page
    
    cursor = db.contacts.find(query, {"_id": 0}).sort(sort_column, sort_dir).skip(skip).limit(per_page)
    contacts = await cursor.to_list(length=per_page)
    total = await db.contacts.count_documents(query)
    
    return {
        "code": 0,
        "contacts": contacts,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "has_more_page": total > page * per_page,
            "total": total
        }
    }

@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str):
    """Get contact details"""
    db = get_db()
    contact = await db.contacts.find_one({"contact_id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "contact": contact}

@router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, contact: ContactCreate):
    """Update contact details"""
    db = get_db()
    update_data = {**contact.dict(), "last_modified_time": datetime.now(timezone.utc).isoformat()}
    result = await db.contacts.update_one({"contact_id": contact_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Contact updated successfully"}

@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact"""
    db = get_db()
    result = await db.contacts.delete_one({"contact_id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Contact deleted successfully"}

@router.post("/contacts/{contact_id}/active")
async def mark_contact_active(contact_id: str):
    """Mark contact as active"""
    db = get_db()
    result = await db.contacts.update_one(
        {"contact_id": contact_id},
        {"$set": {"status": "active", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Contact marked as active"}

@router.post("/contacts/{contact_id}/inactive")
async def mark_contact_inactive(contact_id: str):
    """Mark contact as inactive"""
    db = get_db()
    result = await db.contacts.update_one(
        {"contact_id": contact_id},
        {"$set": {"status": "inactive", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Contact marked as inactive"}

@router.post("/contacts/{contact_id}/portal/enable")
async def enable_portal_access(contact_id: str):
    """Enable portal access for contact"""
    db = get_db()
    result = await db.contacts.update_one(
        {"contact_id": contact_id},
        {"$set": {"portal_enabled": True, "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "message": "Portal access enabled"}

# ============== CONTACT PERSONS MODULE ==============

class ContactPersonCreate(BaseModel):
    contact_id: str
    salutation: Optional[str] = ""
    first_name: str
    last_name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    mobile: Optional[str] = ""
    is_primary_contact: bool = False
    designation: Optional[str] = ""
    department: Optional[str] = ""

@router.post("/contacts/{contact_id}/contactpersons")
async def create_contact_person(contact_id: str, person: ContactPersonCreate):
    """Create contact person"""
    db = get_db()
    person_id = f"CP-{uuid.uuid4().hex[:12].upper()}"
    
    person_dict = {
        "contact_person_id": person_id,
        "contact_id": contact_id,
        **person.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.contact_persons.insert_one(person_dict)
    del person_dict["_id"]
    return {"code": 0, "message": "Contact person created", "contact_person": person_dict}

@router.get("/contacts/{contact_id}/contactpersons")
async def list_contact_persons(contact_id: str):
    """List contact persons for a contact"""
    db = get_db()
    cursor = db.contact_persons.find({"contact_id": contact_id}, {"_id": 0})
    persons = await cursor.to_list(length=100)
    return {"code": 0, "contact_persons": persons}

@router.post("/contacts/{contact_id}/contactpersons/{person_id}/primary")
async def mark_person_primary(contact_id: str, person_id: str):
    """Mark contact person as primary"""
    db = get_db()
    # Unmark all as primary first
    await db.contact_persons.update_many(
        {"contact_id": contact_id},
        {"$set": {"is_primary_contact": False}}
    )
    # Mark selected as primary
    result = await db.contact_persons.update_one(
        {"contact_person_id": person_id},
        {"$set": {"is_primary_contact": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact person not found")
    return {"code": 0, "message": "Contact person marked as primary"}

# ============== ITEMS MODULE ==============

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    sku: Optional[str] = ""
    rate: float = 0
    unit: str = "pcs"
    item_type: str = "sales"  # sales, purchases, sales_and_purchases, inventory
    product_type: str = "service"  # goods, service
    hsn_or_sac: Optional[str] = ""
    tax_id: Optional[str] = ""
    tax_name: Optional[str] = "GST18"
    tax_percentage: float = 18
    purchase_rate: float = 0
    purchase_account_id: Optional[str] = ""
    sales_account_id: Optional[str] = ""
    inventory_account_id: Optional[str] = ""
    initial_stock: float = 0
    initial_stock_rate: float = 0
    reorder_level: float = 0
    vendor_id: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/items")
async def create_item(item: ItemCreate):
    """Create a new item"""
    db = get_db()
    item_id = f"I-{uuid.uuid4().hex[:12].upper()}"
    
    item_dict = {
        "item_id": item_id,
        **item.dict(),
        "status": "active",
        "stock_on_hand": item.initial_stock,
        "available_stock": item.initial_stock,
        "actual_available_stock": item.initial_stock,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.items.insert_one(item_dict)
    del item_dict["_id"]
    return {"code": 0, "message": "Item created successfully", "item": item_dict}

@router.get("/items")
async def list_items(
    item_type: str = "",
    product_type: str = "",
    status: str = "active",
    search_text: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all items"""
    db = get_db()
    query = {}
    if item_type:
        query["item_type"] = item_type
    if product_type:
        query["product_type"] = product_type
    if status:
        query["status"] = status
    if search_text:
        query["name"] = {"$regex": search_text, "$options": "i"}
    
    skip = (page - 1) * per_page
    cursor = db.items.find(query, {"_id": 0}).skip(skip).limit(per_page)
    items = await cursor.to_list(length=per_page)
    total = await db.items.count_documents(query)
    
    return {
        "code": 0,
        "items": items,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/items/{item_id}")
async def get_item(item_id: str):
    """Get item details"""
    db = get_db()
    item = await db.items.find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 0, "item": item}

@router.put("/items/{item_id}")
async def update_item(item_id: str, item: ItemCreate):
    """Update item"""
    db = get_db()
    update_data = {**item.dict(), "last_modified_time": datetime.now(timezone.utc).isoformat()}
    result = await db.items.update_one({"item_id": item_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 0, "message": "Item updated successfully"}

@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete item"""
    db = get_db()
    result = await db.items.delete_one({"item_id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 0, "message": "Item deleted successfully"}

@router.post("/items/{item_id}/active")
async def mark_item_active(item_id: str):
    """Mark item as active"""
    db = get_db()
    await db.items.update_one({"item_id": item_id}, {"$set": {"status": "active"}})
    return {"code": 0, "message": "Item marked as active"}

@router.post("/items/{item_id}/inactive")
async def mark_item_inactive(item_id: str):
    """Mark item as inactive"""
    db = get_db()
    await db.items.update_one({"item_id": item_id}, {"$set": {"status": "inactive"}})
    return {"code": 0, "message": "Item marked as inactive"}

# ============== ESTIMATES MODULE ==============
# Workflow: Create -> Mark Sent -> Mark Accepted/Declined -> Convert to Invoice/SO -> Delete

class EstimateLineItem(BaseModel):
    item_id: Optional[str] = ""
    name: str
    description: Optional[str] = ""
    rate: float
    quantity: float = 1
    unit: str = "pcs"
    discount_percent: float = 0
    tax_id: Optional[str] = ""
    tax_name: str = "GST18"
    tax_percentage: float = 18
    hsn_or_sac: Optional[str] = ""

class EstimateCreate(BaseModel):
    customer_id: str
    customer_name: str
    estimate_number: Optional[str] = ""
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    expiry_date: Optional[str] = None
    line_items: List[EstimateLineItem]
    discount_percent: float = 0
    discount_type: str = "entity_level"  # item_level, entity_level
    shipping_charge: float = 0
    adjustment: float = 0
    adjustment_description: str = ""
    place_of_supply: str = "DL"
    gst_treatment: str = "business_gst"
    notes: Optional[str] = ""
    terms: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/estimates")
async def create_estimate(estimate: EstimateCreate):
    """Create a new estimate"""
    db = get_db()
    estimate_id = f"E-{uuid.uuid4().hex[:12].upper()}"
    estimate_number = estimate.estimate_number or await get_next_number(db, "estimates", "EST")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Calculate totals
    totals = calculate_line_totals(
        [item.dict() for item in estimate.line_items],
        estimate.discount_percent,
        estimate.shipping_charge,
        estimate.adjustment
    )
    
    estimate_dict = {
        "estimate_id": estimate_id,
        "estimate_number": estimate_number,
        "customer_id": estimate.customer_id,
        "customer_name": estimate.customer_name,
        "reference_number": estimate.reference_number,
        "date": estimate.date or today,
        "expiry_date": estimate.expiry_date or expiry,
        "status": "draft",
        "discount_type": estimate.discount_type,
        "discount_percent": estimate.discount_percent,
        "adjustment_description": estimate.adjustment_description,
        "place_of_supply": estimate.place_of_supply,
        "gst_treatment": estimate.gst_treatment,
        "notes": estimate.notes,
        "terms": estimate.terms,
        "custom_fields": estimate.custom_fields,
        **totals,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.estimates.insert_one(estimate_dict)
    del estimate_dict["_id"]
    return {"code": 0, "message": "Estimate created successfully", "estimate": estimate_dict}

@router.get("/estimates")
async def list_estimates(
    status: str = "",
    customer_id: str = "",
    date_start: str = "",
    date_end: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all estimates"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    if date_start:
        query["date"] = {"$gte": date_start}
    if date_end:
        query.setdefault("date", {})["$lte"] = date_end
    
    skip = (page - 1) * per_page
    cursor = db.estimates.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    estimates = await cursor.to_list(length=per_page)
    total = await db.estimates.count_documents(query)
    
    return {"code": 0, "estimates": estimates, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/estimates/{estimate_id}")
async def get_estimate(estimate_id: str):
    """Get estimate details"""
    db = get_db()
    estimate = await db.estimates.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return {"code": 0, "estimate": estimate}

@router.put("/estimates/{estimate_id}")
async def update_estimate(estimate_id: str, estimate: EstimateCreate):
    """Update estimate"""
    db = get_db()
    totals = calculate_line_totals(
        [item.dict() for item in estimate.line_items],
        estimate.discount_percent,
        estimate.shipping_charge,
        estimate.adjustment
    )
    
    update_data = {
        **estimate.dict(),
        **totals,
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    result = await db.estimates.update_one({"estimate_id": estimate_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return {"code": 0, "message": "Estimate updated successfully"}

@router.delete("/estimates/{estimate_id}")
async def delete_estimate(estimate_id: str):
    """Delete estimate"""
    db = get_db()
    result = await db.estimates.delete_one({"estimate_id": estimate_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return {"code": 0, "message": "Estimate deleted successfully"}

@router.post("/estimates/{estimate_id}/status/sent")
async def mark_estimate_sent(estimate_id: str):
    """Mark estimate as sent"""
    db = get_db()
    result = await db.estimates.update_one(
        {"estimate_id": estimate_id},
        {"$set": {"status": "sent", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return {"code": 0, "message": "Estimate marked as sent"}

@router.post("/estimates/{estimate_id}/status/accepted")
async def mark_estimate_accepted(estimate_id: str):
    """Mark estimate as accepted"""
    db = get_db()
    result = await db.estimates.update_one(
        {"estimate_id": estimate_id},
        {"$set": {"status": "accepted", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return {"code": 0, "message": "Estimate marked as accepted"}

@router.post("/estimates/{estimate_id}/status/declined")
async def mark_estimate_declined(estimate_id: str):
    """Mark estimate as declined"""
    db = get_db()
    result = await db.estimates.update_one(
        {"estimate_id": estimate_id},
        {"$set": {"status": "declined", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return {"code": 0, "message": "Estimate marked as declined"}

@router.post("/estimates/{estimate_id}/lineitems/invoices")
async def convert_estimate_to_invoice(estimate_id: str):
    """Convert estimate to invoice"""
    db = get_db()
    estimate = await db.estimates.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    invoice_number = await get_next_number(db, "invoices", "INV")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    invoice_dict = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "customer_id": estimate["customer_id"],
        "customer_name": estimate["customer_name"],
        "date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d"),
        "status": "draft",
        "reference_number": estimate.get("reference_number", ""),
        "from_estimate_id": estimate_id,
        "from_estimate_number": estimate["estimate_number"],
        "line_items": estimate["line_items"],
        "sub_total": estimate["sub_total"],
        "discount_total": estimate["discount_total"],
        "tax_total": estimate["tax_total"],
        "shipping_charge": estimate["shipping_charge"],
        "adjustment": estimate["adjustment"],
        "total": estimate["total"],
        "balance": estimate["total"],
        "payment_made": 0,
        "credits_applied": 0,
        "place_of_supply": estimate.get("place_of_supply", "DL"),
        "gst_treatment": estimate.get("gst_treatment", "business_gst"),
        "notes": estimate.get("notes", ""),
        "terms": estimate.get("terms", ""),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(invoice_dict)
    
    # Update estimate status
    await db.estimates.update_one(
        {"estimate_id": estimate_id},
        {"$set": {"status": "invoiced", "invoice_id": invoice_id}}
    )
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": estimate["customer_id"]},
        {"$inc": {"outstanding_receivable_amount": estimate["total"]}}
    )
    
    del invoice_dict["_id"]
    return {"code": 0, "message": "Invoice created from estimate", "invoice": invoice_dict}

@router.post("/estimates/{estimate_id}/lineitems/salesorders")
async def convert_estimate_to_salesorder(estimate_id: str):
    """Convert estimate to sales order"""
    db = get_db()
    estimate = await db.estimates.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    so_id = f"SO-{uuid.uuid4().hex[:12].upper()}"
    so_number = await get_next_number(db, "salesorders", "SO")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    so_dict = {
        "salesorder_id": so_id,
        "salesorder_number": so_number,
        "customer_id": estimate["customer_id"],
        "customer_name": estimate["customer_name"],
        "date": today,
        "shipment_date": (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
        "status": "draft",
        "reference_number": estimate.get("reference_number", ""),
        "from_estimate_id": estimate_id,
        "from_estimate_number": estimate["estimate_number"],
        "line_items": estimate["line_items"],
        "sub_total": estimate["sub_total"],
        "discount_total": estimate["discount_total"],
        "tax_total": estimate["tax_total"],
        "shipping_charge": estimate["shipping_charge"],
        "adjustment": estimate["adjustment"],
        "total": estimate["total"],
        "invoiced_status": "not_invoiced",
        "paid_status": "unpaid",
        "shipped_status": "pending",
        "place_of_supply": estimate.get("place_of_supply", "DL"),
        "notes": estimate.get("notes", ""),
        "terms": estimate.get("terms", ""),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.salesorders.insert_one(so_dict)
    
    # Update estimate status
    await db.estimates.update_one(
        {"estimate_id": estimate_id},
        {"$set": {"status": "accepted", "salesorder_id": so_id}}
    )
    
    del so_dict["_id"]
    return {"code": 0, "message": "Sales order created from estimate", "salesorder": so_dict}
