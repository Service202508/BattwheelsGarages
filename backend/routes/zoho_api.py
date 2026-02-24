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
from fastapi import Request
from utils.database import extract_org_id, org_query


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

# Bulk Import Contacts - must be before {contact_id} route
@router.post("/contacts/bulk-import")
async def bulk_import_contacts(file: UploadFile = File(...)):
    """Bulk import contacts from CSV file."""
    import csv
    import io
    
    db = get_db()
    content = await file.read()
    try:
        decoded = content.decode('utf-8')
    except UnicodeDecodeError:
        decoded = content.decode('latin-1')
    
    reader = csv.DictReader(io.StringIO(decoded))
    contacts_created, contacts_updated, errors = [], [], []
    row_num = 1
    
    for row in reader:
        row_num += 1
        try:
            contact_name = row.get('contact_name', '').strip()
            if not contact_name:
                errors.append({"row": row_num, "error": "Contact name is required"})
                continue
            
            email = row.get('email', '').strip()
            existing = await db.contacts.find_one({"email": email}) if email else None
            if not existing:
                existing = await db.contacts.find_one({"contact_name": contact_name})
            
            contact_data = {
                "contact_name": contact_name,
                "company_name": row.get('company_name', '').strip(),
                "contact_type": row.get('contact_type', 'customer').strip() or 'customer',
                "email": email,
                "phone": row.get('phone', '').strip(),
                "mobile": row.get('mobile', '').strip(),
                "website": row.get('website', '').strip(),
                "billing_address": {
                    "address": row.get('billing_address', '').strip(),
                    "city": row.get('billing_city', '').strip(),
                    "state": row.get('billing_state', '').strip(),
                    "zip": row.get('billing_zip', '').strip(),
                    "country": row.get('billing_country', 'India').strip()
                },
                "gst_no": row.get('gst_no', '').strip(),
                "pan_no": row.get('pan_no', '').strip(),
                "payment_terms": int(row.get('payment_terms', 15) or 15),
                "last_modified_time": datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                await db.contacts.update_one({"_id": existing["_id"]}, {"$set": contact_data})
                contacts_updated.append({"row": row_num, "name": contact_name, "contact_id": existing.get("contact_id")})
            else:
                contact_id = f"C-{uuid.uuid4().hex[:12].upper()}"
                contact_data.update({
                    "contact_id": contact_id,
                    "status": "active",
                    "outstanding_receivable_amount": 0,
                    "outstanding_payable_amount": 0,
                    "created_time": datetime.now(timezone.utc).isoformat()
                })
                await db.contacts.insert_one(contact_data)
                contacts_created.append({"row": row_num, "name": contact_name, "contact_id": contact_id})
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
    
    return {
        "code": 0,
        "message": f"Import completed. Created: {len(contacts_created)}, Updated: {len(contacts_updated)}, Errors: {len(errors)}",
        "summary": {"total_rows": row_num - 1, "created": len(contacts_created), "updated": len(contacts_updated), "errors": len(errors)},
        "created_contacts": contacts_created,
        "updated_contacts": contacts_updated,
        "errors": errors
    }

@router.get("/contacts/export")
async def export_contacts(contact_type: str = ""):
    """Export contacts as CSV"""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    db = get_db()
    query = {"status": "active"}
    if contact_type:
        query["contact_type"] = contact_type
    
    contacts = await db.contacts.find(query, {"_id": 0}).to_list(10000)
    
    output = io.StringIO()
    fieldnames = ["contact_name", "company_name", "contact_type", "email", "phone", "mobile", "website", "gst_no", "pan_no", "payment_terms"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for contact in contacts:
        writer.writerow(contact)
    output.seek(0)
    
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=contacts_export.csv"})

@router.get("/contacts/import-template")
async def get_contacts_import_template():
    """Get CSV template for contacts bulk import"""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    output = io.StringIO()
    fieldnames = ["contact_name", "company_name", "contact_type", "email", "phone", "mobile", "website", "billing_address", "billing_city", "billing_state", "billing_zip", "billing_country", "gst_no", "pan_no", "payment_terms"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({
        "contact_name": "Sample Customer",
        "company_name": "Sample Corp",
        "contact_type": "customer",
        "email": "sample@example.com",
        "phone": "+91-9876543210",
        "mobile": "+91-9876543210",
        "website": "www.sample.com",
        "billing_address": "123 Main St",
        "billing_city": "Mumbai",
        "billing_state": "Maharashtra",
        "billing_zip": "400001",
        "billing_country": "India",
        "gst_no": "27AAACT1234A1ZB",
        "pan_no": "AAACT1234A",
        "payment_terms": "15"
    })
    output.seek(0)
    
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=contacts_import_template.csv"})

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

@router.post("/items/bulk-import")
async def bulk_import_items(file: UploadFile = File(...)):
    """Bulk import items from CSV file."""
    import csv
    import io
    
    db = get_db()
    content = await file.read()
    try:
        decoded = content.decode('utf-8')
    except UnicodeDecodeError:
        decoded = content.decode('latin-1')
    
    reader = csv.DictReader(io.StringIO(decoded))
    items_created, items_updated, errors = [], [], []
    row_num = 1
    
    for row in reader:
        row_num += 1
        try:
            name = row.get('name', '').strip()
            if not name:
                errors.append({"row": row_num, "error": "Name is required"})
                continue
            
            sku = row.get('sku', '').strip()
            existing = await db.items.find_one({"sku": sku}) if sku else None
            if not existing:
                existing = await db.items.find_one({"name": name})
            
            item_data = {
                "name": name, "sku": sku,
                "description": row.get('description', '').strip(),
                "rate": float(row.get('rate', 0) or 0),
                "purchase_rate": float(row.get('purchase_rate', 0) or 0),
                "item_type": row.get('item_type', 'sales').strip() or 'sales',
                "product_type": row.get('product_type', 'goods').strip() or 'goods',
                "unit": row.get('unit', 'pcs').strip() or 'pcs',
                "hsn_or_sac": row.get('hsn_or_sac', '').strip(),
                "tax_percentage": float(row.get('tax_percentage', 18) or 18),
                "stock_on_hand": float(row.get('stock_on_hand', 0) or 0),
                "reorder_level": float(row.get('reorder_level', 0) or 0),
                "last_modified_time": datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                await db.items.update_one({"_id": existing["_id"]}, {"$set": item_data})
                items_updated.append({"row": row_num, "name": name, "item_id": existing.get("item_id")})
            else:
                item_id = f"I-{uuid.uuid4().hex[:12].upper()}"
                item_data.update({"item_id": item_id, "status": "active", "available_stock": item_data["stock_on_hand"], "created_time": datetime.now(timezone.utc).isoformat()})
                await db.items.insert_one(item_data)
                items_created.append({"row": row_num, "name": name, "item_id": item_id})
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
    
    return {
        "code": 0, "message": f"Import completed. Created: {len(items_created)}, Updated: {len(items_updated)}, Errors: {len(errors)}",
        "summary": {"total_rows": row_num - 1, "created": len(items_created), "updated": len(items_updated), "errors": len(errors)},
        "created_items": items_created, "updated_items": items_updated, "errors": errors
    }

@router.get("/items/export")
async def export_items(format: str = "csv"):
    """Export all items as CSV"""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    db = get_db()
    items = await db.items.find({"status": "active"}, {"_id": 0}).to_list(10000)
    
    if format == "csv":
        output = io.StringIO()
        fieldnames = ["name", "sku", "description", "rate", "purchase_rate", "item_type", "product_type", "unit", "hsn_or_sac", "tax_percentage", "stock_on_hand", "reorder_level"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for item in items:
            writer.writerow(item)
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=items_export.csv"})
    return {"items": items}

@router.get("/items/import-template")
async def get_import_template():
    """Get CSV template for bulk import"""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    output = io.StringIO()
    fieldnames = ["name", "sku", "description", "rate", "purchase_rate", "item_type", "product_type", "unit", "hsn_or_sac", "tax_percentage", "stock_on_hand", "reorder_level"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({"name": "Sample Product", "sku": "SKU-001", "description": "Sample product", "rate": "1000", "purchase_rate": "800", "item_type": "sales_and_purchases", "product_type": "goods", "unit": "pcs", "hsn_or_sac": "84714100", "tax_percentage": "18", "stock_on_hand": "100", "reorder_level": "10"})
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=items_import_template.csv"})

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

@router.post("/estimates/{estimate_id}/email")
async def email_estimate(estimate_id: str, to_emails: str = "", subject: str = "", body: str = ""):
    """Email estimate to customer"""
    db = get_db()
    estimate = await db.estimates.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if not to_emails:
        customer = await db.contacts.find_one({"contact_id": estimate["customer_id"]}, {"_id": 0})
        to_emails = customer.get("email", "") if customer else ""
    
    if not to_emails:
        raise HTTPException(status_code=400, detail="No email address provided")
    
    default_subject = f"Estimate {estimate.get('estimate_number')} from Battwheels"
    default_body = f"""Dear {estimate.get('customer_name')},

Please find attached Estimate {estimate.get('estimate_number')} for ₹{estimate.get('total', 0):,.2f}.

This estimate is valid until {estimate.get('expiry_date')}.

Please let us know if you have any questions.

Best regards,
Battwheels Team"""
    
    email_log = {
        "email_id": f"EMAIL-{uuid.uuid4().hex[:12].upper()}",
        "entity_type": "estimate",
        "entity_id": estimate_id,
        "to_emails": to_emails.split(","),
        "subject": subject or default_subject,
        "body": body or default_body,
        "status": "queued",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    await db.email_logs.insert_one(email_log)
    
    if estimate.get("status") == "draft":
        await db.estimates.update_one({"estimate_id": estimate_id}, {"$set": {"status": "sent"}})
    
    return {"code": 0, "message": "Estimate email queued", "email": {"to": to_emails, "subject": subject or default_subject}}

@router.post("/estimates/{estimate_id}/clone")
async def clone_estimate(estimate_id: str):
    """Create a copy of an existing estimate"""
    db = get_db()
    estimate = await db.estimates.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    new_estimate_id = f"EST-{uuid.uuid4().hex[:12].upper()}"
    new_estimate_number = await get_next_number(db, "estimates", "EST")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    
    new_estimate = {
        **estimate,
        "estimate_id": new_estimate_id,
        "estimate_number": new_estimate_number,
        "date": today,
        "expiry_date": expiry,
        "status": "draft",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    new_estimate.pop("_id", None)
    new_estimate.pop("invoice_id", None)
    new_estimate.pop("salesorder_id", None)
    
    await db.estimates.insert_one(new_estimate)
    del new_estimate["_id"]
    
    return {"code": 0, "message": "Estimate cloned", "estimate": new_estimate}


# ============== INVOICES MODULE ==============
# Workflow: Create -> Mark Sent -> Record Payment -> Void/Write-off -> Delete

class InvoiceLineItem(BaseModel):
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

class InvoiceCreate(BaseModel):
    customer_id: str
    customer_name: str
    invoice_number: Optional[str] = ""
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    due_date: Optional[str] = None
    payment_terms: int = 15
    payment_terms_label: str = "Net 15"
    line_items: List[InvoiceLineItem]
    discount_percent: float = 0
    discount_type: str = "entity_level"
    shipping_charge: float = 0
    adjustment: float = 0
    adjustment_description: str = ""
    place_of_supply: str = "DL"
    gst_treatment: str = "business_gst"
    notes: Optional[str] = ""
    terms: Optional[str] = ""
    salesperson_name: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/invoices")
async def create_invoice(invoice: InvoiceCreate):
    """Create a new invoice"""
    db = get_db()
    invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    invoice_number = invoice.invoice_number or await get_next_number(db, "invoices", "INV")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due = (datetime.now(timezone.utc) + timedelta(days=invoice.payment_terms)).strftime("%Y-%m-%d")
    
    totals = calculate_line_totals(
        [item.dict() for item in invoice.line_items],
        invoice.discount_percent,
        invoice.shipping_charge,
        invoice.adjustment
    )
    
    invoice_dict = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "customer_id": invoice.customer_id,
        "customer_name": invoice.customer_name,
        "reference_number": invoice.reference_number,
        "date": invoice.date or today,
        "due_date": invoice.due_date or due,
        "payment_terms": invoice.payment_terms,
        "payment_terms_label": invoice.payment_terms_label,
        "status": "draft",
        "discount_type": invoice.discount_type,
        "discount_percent": invoice.discount_percent,
        "adjustment_description": invoice.adjustment_description,
        "place_of_supply": invoice.place_of_supply,
        "gst_treatment": invoice.gst_treatment,
        "notes": invoice.notes,
        "terms": invoice.terms,
        "salesperson_name": invoice.salesperson_name,
        "custom_fields": invoice.custom_fields,
        **totals,
        "balance": totals["total"],
        "payment_made": 0,
        "credits_applied": 0,
        "write_off_amount": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(invoice_dict)
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": invoice.customer_id},
        {"$inc": {"outstanding_receivable_amount": totals["total"]}}
    )
    
    del invoice_dict["_id"]
    return {"code": 0, "message": "Invoice created successfully", "invoice": invoice_dict}

@router.get("/invoices")
async def list_invoices(
    status: str = "",
    customer_id: str = "",
    date_start: str = "",
    date_end: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all invoices"""
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
    cursor = db.invoices.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    invoices = await cursor.to_list(length=per_page)
    total = await db.invoices.count_documents(query)
    
    return {"code": 0, "invoices": invoices, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Get invoice details"""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"code": 0, "invoice": invoice}

@router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, invoice: InvoiceCreate):
    """Update invoice"""
    db = get_db()
    totals = calculate_line_totals(
        [item.dict() for item in invoice.line_items],
        invoice.discount_percent,
        invoice.shipping_charge,
        invoice.adjustment
    )
    
    update_data = {
        **invoice.dict(),
        **totals,
        "balance": totals["total"],  # Reset balance on update
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    result = await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"code": 0, "message": "Invoice updated successfully"}

@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str):
    """Delete invoice"""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Reduce customer outstanding
    await db.contacts.update_one(
        {"contact_id": invoice["customer_id"]},
        {"$inc": {"outstanding_receivable_amount": -invoice["balance"]}}
    )
    
    await db.invoices.delete_one({"invoice_id": invoice_id})
    return {"code": 0, "message": "Invoice deleted successfully"}

@router.post("/invoices/{invoice_id}/status/sent")
async def mark_invoice_sent(invoice_id: str):
    """Mark invoice as sent"""
    db = get_db()
    result = await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "sent", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"code": 0, "message": "Invoice marked as sent"}

@router.post("/invoices/{invoice_id}/status/void")
async def void_invoice(invoice_id: str):
    """Void an invoice"""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": invoice["customer_id"]},
        {"$inc": {"outstanding_receivable_amount": -invoice["balance"]}}
    )
    
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "void", "balance": 0, "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    return {"code": 0, "message": "Invoice voided successfully"}

@router.post("/invoices/{invoice_id}/writeoff")
async def write_off_invoice(invoice_id: str, amount: float = 0):
    """Write off invoice balance"""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    write_off = amount if amount > 0 else invoice["balance"]
    new_balance = invoice["balance"] - write_off
    new_status = "paid" if new_balance <= 0 else invoice["status"]
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": invoice["customer_id"]},
        {"$inc": {"outstanding_receivable_amount": -write_off}}
    )
    
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "status": new_status,
            "balance": new_balance,
            "write_off_amount": invoice.get("write_off_amount", 0) + write_off,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"code": 0, "message": f"Invoice written off for {write_off}"}

@router.post("/invoices/{invoice_id}/payments")
async def record_invoice_payment(invoice_id: str, amount: float, payment_mode: str = "cash", reference_number: str = "", date: str = ""):
    """Record a payment directly against an invoice"""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice["status"] in ["void", "paid"]:
        raise HTTPException(status_code=400, detail=f"Cannot record payment for {invoice['status']} invoice")
    
    if amount > invoice["balance"]:
        raise HTTPException(status_code=400, detail="Payment amount exceeds invoice balance")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payment_id = f"CPMT-{uuid.uuid4().hex[:12].upper()}"
    payment_number = await get_next_number(db, "customerpayments", "CPMT")
    
    payment_dict = {
        "payment_id": payment_id,
        "payment_number": payment_number,
        "customer_id": invoice["customer_id"],
        "customer_name": invoice["customer_name"],
        "payment_mode": payment_mode,
        "amount": amount,
        "unused_amount": 0,
        "date": date or today,
        "reference_number": reference_number,
        "invoices": [{"invoice_id": invoice_id, "invoice_number": invoice.get("invoice_number"), "amount_applied": amount}],
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.customerpayments.insert_one(payment_dict)
    
    new_balance = invoice["balance"] - amount
    new_status = "paid" if new_balance <= 0 else "partial"
    
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"balance": new_balance, "status": new_status, "last_modified_time": datetime.now(timezone.utc).isoformat()},
         "$push": {"payments": {"payment_id": payment_id, "amount": amount, "date": date or today}}}
    )
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": invoice["customer_id"]},
        {"$inc": {"outstanding_receivable_amount": -amount}}
    )
    
    del payment_dict["_id"]
    return {"code": 0, "message": "Payment recorded", "payment": payment_dict, "invoice_balance": new_balance}

@router.get("/invoices/{invoice_id}/payments")
async def get_invoice_payments(invoice_id: str):
    """Get all payments applied to an invoice"""
    db = get_db()
    payments = await db.customerpayments.find(
        {"invoices.invoice_id": invoice_id},
        {"_id": 0}
    ).to_list(length=100)
    return {"code": 0, "payments": payments}

@router.post("/invoices/{invoice_id}/email")
async def email_invoice(invoice_id: str, to_emails: str = "", cc_emails: str = "", subject: str = "", body: str = ""):
    """Email invoice to customer"""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get customer email if to_emails not provided
    if not to_emails:
        customer = await db.contacts.find_one({"contact_id": invoice["customer_id"]}, {"_id": 0})
        to_emails = customer.get("email", "") if customer else ""
    
    if not to_emails:
        raise HTTPException(status_code=400, detail="No email address provided")
    
    # Generate email subject and body
    default_subject = f"Invoice {invoice.get('invoice_number')} from Battwheels"
    default_body = f"""Dear {invoice.get('customer_name')},

Please find attached Invoice {invoice.get('invoice_number')} for ₹{invoice.get('total', 0):,.2f}.

Invoice Date: {invoice.get('date')}
Due Date: {invoice.get('due_date')}
Amount Due: ₹{invoice.get('balance', 0):,.2f}

Thank you for your business.

Best regards,
Battwheels Team"""
    
    # Log email activity (actual sending would require email service integration)
    email_log = {
        "email_id": f"EMAIL-{uuid.uuid4().hex[:12].upper()}",
        "entity_type": "invoice",
        "entity_id": invoice_id,
        "to_emails": to_emails.split(","),
        "cc_emails": cc_emails.split(",") if cc_emails else [],
        "subject": subject or default_subject,
        "body": body or default_body,
        "status": "queued",  # Would be 'sent' after actual email integration
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.email_logs.insert_one(email_log)
    
    # Mark invoice as sent if still draft
    if invoice.get("status") == "draft":
        await db.invoices.update_one(
            {"invoice_id": invoice_id},
            {"$set": {"status": "sent", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {
        "code": 0,
        "message": "Invoice email queued. Configure email service for actual delivery.",
        "email": {"to": to_emails, "subject": subject or default_subject}
    }

@router.post("/invoices/{invoice_id}/clone")
async def clone_invoice(invoice_id: str):
    """Create a copy of an existing invoice"""
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    new_invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    new_invoice_number = await get_next_number(db, "invoices", "INV")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_date = (datetime.now(timezone.utc) + timedelta(days=invoice.get("payment_terms", 30))).strftime("%Y-%m-%d")
    
    new_invoice = {
        **invoice,
        "invoice_id": new_invoice_id,
        "invoice_number": new_invoice_number,
        "date": today,
        "due_date": due_date,
        "status": "draft",
        "balance": invoice.get("total", 0),
        "payments": [],
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Remove fields that shouldn't be copied
    new_invoice.pop("_id", None)
    new_invoice.pop("from_estimate_id", None)
    new_invoice.pop("from_salesorder_id", None)
    
    await db.invoices.insert_one(new_invoice)
    del new_invoice["_id"]
    
    return {"code": 0, "message": "Invoice cloned", "invoice": new_invoice}

@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str, format: str = "pdf"):
    """Generate PDF for invoice using WeasyPrint"""
    from fastapi.responses import Response
    from services.pdf_service import generate_invoice_html, generate_pdf_from_html
    
    db = get_db()
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get organization settings
    org_settings = await db.organization_settings.find_one({}, {"_id": 0}) or {}
    
    # Generate HTML
    html_content = generate_invoice_html(invoice, org_settings)
    
    if format == "html":
        return {"code": 0, "invoice_id": invoice_id, "html": html_content}
    
    # Generate PDF
    try:
        pdf_bytes = generate_pdf_from_html(html_content)
        filename = f"Invoice_{invoice.get('invoice_number', invoice_id)}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.post("/invoices/bulk-action")
async def bulk_invoice_action(invoice_ids: List[str], action: str):
    """Perform bulk action on multiple invoices"""
    db = get_db()
    
    valid_actions = ["mark_sent", "void", "delete"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Valid: {valid_actions}")
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    for invoice_id in invoice_ids:
        try:
            invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
            if not invoice:
                results["failed"] += 1
                results["errors"].append({"invoice_id": invoice_id, "error": "Not found"})
                continue
            
            if action == "mark_sent":
                if invoice["status"] == "draft":
                    await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": {"status": "sent"}})
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({"invoice_id": invoice_id, "error": "Not in draft status"})
            
            elif action == "void":
                if invoice["status"] in ["sent", "partial", "overdue"]:
                    await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": {"status": "void", "balance": 0}})
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({"invoice_id": invoice_id, "error": f"Cannot void {invoice['status']} invoice"})
            
            elif action == "delete":
                if invoice["status"] == "draft":
                    await db.invoices.delete_one({"invoice_id": invoice_id})
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({"invoice_id": invoice_id, "error": "Can only delete draft invoices"})
        
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"invoice_id": invoice_id, "error": str(e)})
    
    return {"code": 0, "message": f"Bulk action completed", "results": results}

# ============== SALES ORDERS MODULE ==============
# Workflow: Create -> Confirm -> Convert to Invoice -> Mark Delivered -> Close

class SalesOrderCreate(BaseModel):
    customer_id: str
    customer_name: str
    salesorder_number: Optional[str] = ""
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    shipment_date: Optional[str] = None
    line_items: List[InvoiceLineItem]
    discount_percent: float = 0
    discount_type: str = "entity_level"
    shipping_charge: float = 0
    adjustment: float = 0
    place_of_supply: str = "DL"
    notes: Optional[str] = ""
    terms: Optional[str] = ""
    delivery_method: Optional[str] = ""
    salesperson_name: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/salesorders")
async def create_salesorder(so: SalesOrderCreate):
    """Create a new sales order"""
    db = get_db()
    so_id = f"SO-{uuid.uuid4().hex[:12].upper()}"
    so_number = so.salesorder_number or await get_next_number(db, "salesorders", "SO")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ship_date = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    
    totals = calculate_line_totals(
        [item.dict() for item in so.line_items],
        so.discount_percent,
        so.shipping_charge,
        so.adjustment
    )
    
    so_dict = {
        "salesorder_id": so_id,
        "salesorder_number": so_number,
        "customer_id": so.customer_id,
        "customer_name": so.customer_name,
        "reference_number": so.reference_number,
        "date": so.date or today,
        "shipment_date": so.shipment_date or ship_date,
        "status": "draft",
        "order_status": "open",
        "invoiced_status": "not_invoiced",
        "paid_status": "unpaid",
        "shipped_status": "pending",
        "discount_type": so.discount_type,
        "discount_percent": so.discount_percent,
        "place_of_supply": so.place_of_supply,
        "notes": so.notes,
        "terms": so.terms,
        "delivery_method": so.delivery_method,
        "salesperson_name": so.salesperson_name,
        "custom_fields": so.custom_fields,
        **totals,
        "invoiced_amount": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.salesorders.insert_one(so_dict)
    del so_dict["_id"]
    return {"code": 0, "message": "Sales order created successfully", "salesorder": so_dict}

@router.get("/salesorders")
async def list_salesorders(
    status: str = "",
    customer_id: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all sales orders"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    skip = (page - 1) * per_page
    cursor = db.salesorders.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    salesorders = await cursor.to_list(length=per_page)
    total = await db.salesorders.count_documents(query)
    
    return {"code": 0, "salesorders": salesorders, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/salesorders/{so_id}")
async def get_salesorder(so_id: str):
    """Get sales order details"""
    db = get_db()
    so = await db.salesorders.find_one({"salesorder_id": so_id}, {"_id": 0})
    if not so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return {"code": 0, "salesorder": so}

@router.put("/salesorders/{so_id}")
async def update_salesorder(so_id: str, so: SalesOrderCreate):
    """Update sales order"""
    db = get_db()
    totals = calculate_line_totals(
        [item.dict() for item in so.line_items],
        so.discount_percent,
        so.shipping_charge,
        so.adjustment
    )
    
    update_data = {
        **so.dict(),
        **totals,
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    result = await db.salesorders.update_one({"salesorder_id": so_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return {"code": 0, "message": "Sales order updated successfully"}

@router.delete("/salesorders/{so_id}")
async def delete_salesorder(so_id: str):
    """Delete sales order"""
    db = get_db()
    result = await db.salesorders.delete_one({"salesorder_id": so_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return {"code": 0, "message": "Sales order deleted successfully"}

@router.post("/salesorders/{so_id}/status/confirmed")
async def confirm_salesorder(so_id: str):
    """Confirm sales order"""
    db = get_db()
    result = await db.salesorders.update_one(
        {"salesorder_id": so_id},
        {"$set": {"status": "confirmed", "order_status": "open", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return {"code": 0, "message": "Sales order confirmed"}

@router.post("/salesorders/{so_id}/status/void")
async def void_salesorder(so_id: str):
    """Void sales order"""
    db = get_db()
    result = await db.salesorders.update_one(
        {"salesorder_id": so_id},
        {"$set": {"status": "void", "order_status": "closed", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return {"code": 0, "message": "Sales order voided"}

@router.post("/salesorders/{so_id}/invoices")
async def convert_salesorder_to_invoice(so_id: str):
    """Convert sales order to invoice"""
    db = get_db()
    so = await db.salesorders.find_one({"salesorder_id": so_id}, {"_id": 0})
    if not so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    invoice_number = await get_next_number(db, "invoices", "INV")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    invoice_dict = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "customer_id": so["customer_id"],
        "customer_name": so["customer_name"],
        "date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d"),
        "status": "draft",
        "reference_number": so.get("reference_number", ""),
        "from_salesorder_id": so_id,
        "from_salesorder_number": so["salesorder_number"],
        "line_items": so["line_items"],
        "sub_total": so["sub_total"],
        "discount_total": so["discount_total"],
        "tax_total": so["tax_total"],
        "shipping_charge": so["shipping_charge"],
        "adjustment": so["adjustment"],
        "total": so["total"],
        "balance": so["total"],
        "payment_made": 0,
        "credits_applied": 0,
        "place_of_supply": so.get("place_of_supply", "DL"),
        "notes": so.get("notes", ""),
        "terms": so.get("terms", ""),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(invoice_dict)
    
    # Update sales order
    await db.salesorders.update_one(
        {"salesorder_id": so_id},
        {"$set": {
            "invoiced_status": "invoiced",
            "invoiced_amount": so["total"],
            "invoice_id": invoice_id,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": so["customer_id"]},
        {"$inc": {"outstanding_receivable_amount": so["total"]}}
    )
    
    del invoice_dict["_id"]
    return {"code": 0, "message": "Invoice created from sales order", "invoice": invoice_dict}

# ============== PURCHASE ORDERS MODULE ==============
# Workflow: Create -> Mark Issued -> Convert to Bill -> Mark Delivered -> Close

class PurchaseOrderCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    purchaseorder_number: Optional[str] = ""
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    delivery_date: Optional[str] = None
    line_items: List[InvoiceLineItem]
    discount_percent: float = 0
    shipping_charge: float = 0
    adjustment: float = 0
    source_of_supply: str = "DL"
    destination_of_supply: str = "DL"
    notes: Optional[str] = ""
    terms: Optional[str] = ""
    delivery_address: Optional[Dict] = {}
    custom_fields: Optional[List[Dict]] = []

@router.post("/purchaseorders")
async def create_purchaseorder(po: PurchaseOrderCreate):
    """Create a new purchase order"""
    db = get_db()
    po_id = f"PO-{uuid.uuid4().hex[:12].upper()}"
    po_number = po.purchaseorder_number or await get_next_number(db, "purchaseorders", "PO")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    delivery = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d")
    
    totals = calculate_line_totals(
        [item.dict() for item in po.line_items],
        po.discount_percent,
        po.shipping_charge,
        po.adjustment
    )
    
    po_dict = {
        "purchaseorder_id": po_id,
        "purchaseorder_number": po_number,
        "vendor_id": po.vendor_id,
        "vendor_name": po.vendor_name,
        "reference_number": po.reference_number,
        "date": po.date or today,
        "delivery_date": po.delivery_date or delivery,
        "status": "draft",
        "order_status": "open",
        "billed_status": "unbilled",
        "source_of_supply": po.source_of_supply,
        "destination_of_supply": po.destination_of_supply,
        "discount_percent": po.discount_percent,
        "notes": po.notes,
        "terms": po.terms,
        "delivery_address": po.delivery_address,
        "custom_fields": po.custom_fields,
        **totals,
        "billed_amount": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.purchaseorders.insert_one(po_dict)
    del po_dict["_id"]
    return {"code": 0, "message": "Purchase order created successfully", "purchaseorder": po_dict}

@router.get("/purchaseorders")
async def list_purchaseorders(
    status: str = "",
    vendor_id: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all purchase orders"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    skip = (page - 1) * per_page
    cursor = db.purchaseorders.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    purchaseorders = await cursor.to_list(length=per_page)
    total = await db.purchaseorders.count_documents(query)
    
    return {"code": 0, "purchaseorders": purchaseorders, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/purchaseorders/{po_id}")
async def get_purchaseorder(po_id: str):
    """Get purchase order details"""
    db = get_db()
    po = await db.purchaseorders.find_one({"purchaseorder_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"code": 0, "purchaseorder": po}

@router.put("/purchaseorders/{po_id}")
async def update_purchaseorder(po_id: str, po: PurchaseOrderCreate):
    """Update purchase order"""
    db = get_db()
    totals = calculate_line_totals(
        [item.dict() for item in po.line_items],
        po.discount_percent,
        po.shipping_charge,
        po.adjustment
    )
    
    update_data = {
        **po.dict(),
        **totals,
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    result = await db.purchaseorders.update_one({"purchaseorder_id": po_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"code": 0, "message": "Purchase order updated successfully"}

@router.delete("/purchaseorders/{po_id}")
async def delete_purchaseorder(po_id: str):
    """Delete purchase order"""
    db = get_db()
    result = await db.purchaseorders.delete_one({"purchaseorder_id": po_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"code": 0, "message": "Purchase order deleted successfully"}

@router.post("/purchaseorders/{po_id}/status/issued")
async def issue_purchaseorder(po_id: str):
    """Mark purchase order as issued"""
    db = get_db()
    result = await db.purchaseorders.update_one(
        {"purchaseorder_id": po_id},
        {"$set": {"status": "issued", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"code": 0, "message": "Purchase order issued"}

@router.post("/purchaseorders/{po_id}/status/cancelled")
async def cancel_purchaseorder(po_id: str):
    """Cancel purchase order"""
    db = get_db()
    result = await db.purchaseorders.update_one(
        {"purchaseorder_id": po_id},
        {"$set": {"status": "cancelled", "order_status": "closed", "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"code": 0, "message": "Purchase order cancelled"}

@router.post("/purchaseorders/{po_id}/bills")
async def convert_purchaseorder_to_bill(po_id: str, bill_number: str = ""):
    """Convert purchase order to bill"""
    db = get_db()
    po = await db.purchaseorders.find_one({"purchaseorder_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    bill_id = f"BILL-{uuid.uuid4().hex[:12].upper()}"
    bill_num = bill_number or await get_next_number(db, "bills", "BILL")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    bill_dict = {
        "bill_id": bill_id,
        "bill_number": bill_num,
        "vendor_id": po["vendor_id"],
        "vendor_name": po["vendor_name"],
        "date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "status": "open",
        "reference_number": po.get("reference_number", ""),
        "from_purchaseorder_id": po_id,
        "from_purchaseorder_number": po["purchaseorder_number"],
        "line_items": po["line_items"],
        "sub_total": po["sub_total"],
        "discount_total": po["discount_total"],
        "tax_total": po["tax_total"],
        "shipping_charge": po["shipping_charge"],
        "adjustment": po["adjustment"],
        "total": po["total"],
        "balance": po["total"],
        "payment_made": 0,
        "source_of_supply": po.get("source_of_supply", "DL"),
        "destination_of_supply": po.get("destination_of_supply", "DL"),
        "notes": po.get("notes", ""),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bills.insert_one(bill_dict)
    
    # Update purchase order
    await db.purchaseorders.update_one(
        {"purchaseorder_id": po_id},
        {"$set": {
            "billed_status": "billed",
            "billed_amount": po["total"],
            "bill_id": bill_id,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update vendor outstanding
    await db.contacts.update_one(
        {"contact_id": po["vendor_id"]},
        {"$inc": {"outstanding_payable_amount": po["total"]}}
    )
    
    del bill_dict["_id"]
    return {"code": 0, "message": "Bill created from purchase order", "bill": bill_dict}

# ============== BILLS MODULE ==============
# Workflow: Create -> Record Payment -> Void -> Delete

class BillCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    bill_number: str
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    due_date: Optional[str] = None
    payment_terms: int = 30
    line_items: List[InvoiceLineItem]
    discount_percent: float = 0
    shipping_charge: float = 0
    adjustment: float = 0
    source_of_supply: str = "DL"
    destination_of_supply: str = "DL"
    notes: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/bills")
async def create_bill(bill: BillCreate):
    """Create a new bill"""
    db = get_db()
    bill_id = f"BILL-{uuid.uuid4().hex[:12].upper()}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due = (datetime.now(timezone.utc) + timedelta(days=bill.payment_terms)).strftime("%Y-%m-%d")
    
    totals = calculate_line_totals(
        [item.dict() for item in bill.line_items],
        bill.discount_percent,
        bill.shipping_charge,
        bill.adjustment
    )
    
    bill_dict = {
        "bill_id": bill_id,
        "bill_number": bill.bill_number,
        "vendor_id": bill.vendor_id,
        "vendor_name": bill.vendor_name,
        "reference_number": bill.reference_number,
        "date": bill.date or today,
        "due_date": bill.due_date or due,
        "payment_terms": bill.payment_terms,
        "status": "open",
        "source_of_supply": bill.source_of_supply,
        "destination_of_supply": bill.destination_of_supply,
        "discount_percent": bill.discount_percent,
        "notes": bill.notes,
        "custom_fields": bill.custom_fields,
        **totals,
        "balance": totals["total"],
        "payment_made": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bills.insert_one(bill_dict)
    
    # Update vendor outstanding
    await db.contacts.update_one(
        {"contact_id": bill.vendor_id},
        {"$inc": {"outstanding_payable_amount": totals["total"]}}
    )
    
    del bill_dict["_id"]
    return {"code": 0, "message": "Bill created successfully", "bill": bill_dict}

@router.get("/bills")
async def list_bills(
    status: str = "",
    vendor_id: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all bills"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    skip = (page - 1) * per_page
    cursor = db.bills.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    bills = await cursor.to_list(length=per_page)
    total = await db.bills.count_documents(query)
    
    return {"code": 0, "bills": bills, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/bills/{bill_id}")
async def get_bill(bill_id: str):
    """Get bill details"""
    db = get_db()
    bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"code": 0, "bill": bill}

@router.put("/bills/{bill_id}")
async def update_bill(bill_id: str, bill: BillCreate):
    """Update bill"""
    db = get_db()
    totals = calculate_line_totals(
        [item.dict() for item in bill.line_items],
        bill.discount_percent,
        bill.shipping_charge,
        bill.adjustment
    )
    
    update_data = {
        **bill.dict(),
        **totals,
        "balance": totals["total"],
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    result = await db.bills.update_one({"bill_id": bill_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"code": 0, "message": "Bill updated successfully"}

@router.delete("/bills/{bill_id}")
async def delete_bill(bill_id: str):
    """Delete bill"""
    db = get_db()
    bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Reduce vendor outstanding
    await db.contacts.update_one(
        {"contact_id": bill["vendor_id"]},
        {"$inc": {"outstanding_payable_amount": -bill["balance"]}}
    )
    
    await db.bills.delete_one({"bill_id": bill_id})
    return {"code": 0, "message": "Bill deleted successfully"}

@router.post("/bills/{bill_id}/status/void")
async def void_bill(bill_id: str):
    """Void a bill"""
    db = get_db()
    bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Update vendor outstanding
    await db.contacts.update_one(
        {"contact_id": bill["vendor_id"]},
        {"$inc": {"outstanding_payable_amount": -bill["balance"]}}
    )
    
    await db.bills.update_one(
        {"bill_id": bill_id},
        {"$set": {"status": "void", "balance": 0, "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    return {"code": 0, "message": "Bill voided successfully"}

@router.post("/bills/{bill_id}/payments")
async def record_bill_payment(bill_id: str, amount: float, payment_mode: str = "cash", reference_number: str = "", date: str = ""):
    """Record a payment directly against a bill"""
    db = get_db()
    bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    if bill["status"] in ["void", "paid"]:
        raise HTTPException(status_code=400, detail=f"Cannot record payment for {bill['status']} bill")
    
    if amount > bill["balance"]:
        raise HTTPException(status_code=400, detail="Payment amount exceeds bill balance")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payment_id = f"VPMT-{uuid.uuid4().hex[:12].upper()}"
    payment_number = await get_next_number(db, "vendorpayments", "VPMT")
    
    payment_dict = {
        "payment_id": payment_id,
        "payment_number": payment_number,
        "vendor_id": bill["vendor_id"],
        "vendor_name": bill["vendor_name"],
        "payment_mode": payment_mode,
        "amount": amount,
        "date": date or today,
        "reference_number": reference_number,
        "bills": [{"bill_id": bill_id, "bill_number": bill.get("bill_number"), "amount_applied": amount}],
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.vendorpayments.insert_one(payment_dict)
    
    new_balance = bill["balance"] - amount
    new_status = "paid" if new_balance <= 0 else "partial"
    
    await db.bills.update_one(
        {"bill_id": bill_id},
        {"$set": {"balance": new_balance, "status": new_status, "last_modified_time": datetime.now(timezone.utc).isoformat()},
         "$push": {"payments": {"payment_id": payment_id, "amount": amount, "date": date or today}}}
    )
    
    await db.contacts.update_one(
        {"contact_id": bill["vendor_id"]},
        {"$inc": {"outstanding_payable_amount": -amount}}
    )
    
    del payment_dict["_id"]
    return {"code": 0, "message": "Payment recorded", "payment": payment_dict, "bill_balance": new_balance}

@router.get("/bills/{bill_id}/payments")
async def get_bill_payments(bill_id: str):
    """Get all payments applied to a bill"""
    db = get_db()
    payments = await db.vendorpayments.find({"bills.bill_id": bill_id}, {"_id": 0}).to_list(length=100)
    return {"code": 0, "payments": payments}

@router.post("/bills/{bill_id}/clone")
async def clone_bill(bill_id: str):
    """Create a copy of an existing bill"""
    db = get_db()
    bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    new_bill_id = f"BILL-{uuid.uuid4().hex[:12].upper()}"
    new_bill_number = await get_next_number(db, "bills", "BILL")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_date = (datetime.now(timezone.utc) + timedelta(days=bill.get("payment_terms", 30))).strftime("%Y-%m-%d")
    
    new_bill = {
        **bill,
        "bill_id": new_bill_id,
        "bill_number": new_bill_number,
        "date": today,
        "due_date": due_date,
        "status": "draft",
        "balance": bill.get("total", 0),
        "payments": [],
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    new_bill.pop("_id", None)
    new_bill.pop("from_purchaseorder_id", None)
    
    await db.bills.insert_one(new_bill)
    del new_bill["_id"]
    
    return {"code": 0, "message": "Bill cloned", "bill": new_bill}

# ============== CREDIT NOTES MODULE ==============
# Workflow: Create -> Apply to Invoice -> Refund -> Delete

class CreditNoteCreate(BaseModel):
    customer_id: str
    customer_name: str
    creditnote_number: Optional[str] = ""
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    invoice_id: Optional[str] = ""
    line_items: List[InvoiceLineItem]
    discount_percent: float = 0
    place_of_supply: str = "DL"
    reason: str = ""
    notes: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/creditnotes")
async def create_creditnote(cn: CreditNoteCreate):
    """Create a new credit note"""
    db = get_db()
    cn_id = f"CN-{uuid.uuid4().hex[:12].upper()}"
    cn_number = cn.creditnote_number or await get_next_number(db, "creditnotes", "CN")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    totals = calculate_line_totals(
        [item.dict() for item in cn.line_items],
        cn.discount_percent, 0, 0
    )
    
    cn_dict = {
        "creditnote_id": cn_id,
        "creditnote_number": cn_number,
        "customer_id": cn.customer_id,
        "customer_name": cn.customer_name,
        "reference_number": cn.reference_number,
        "date": cn.date or today,
        "invoice_id": cn.invoice_id,
        "status": "open",
        "place_of_supply": cn.place_of_supply,
        "reason": cn.reason,
        "notes": cn.notes,
        "custom_fields": cn.custom_fields,
        **totals,
        "balance": totals["total"],
        "credits_remaining": totals["total"],
        "credits_used": 0,
        "refunded_amount": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.creditnotes.insert_one(cn_dict)
    
    # Update customer credits available
    await db.contacts.update_one(
        {"contact_id": cn.customer_id},
        {"$inc": {"unused_credits_receivable_amount": totals["total"], "outstanding_receivable_amount": -totals["total"]}}
    )
    
    del cn_dict["_id"]
    return {"code": 0, "message": "Credit note created successfully", "creditnote": cn_dict}

@router.get("/creditnotes")
async def list_creditnotes(
    status: str = "",
    customer_id: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all credit notes"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    skip = (page - 1) * per_page
    cursor = db.creditnotes.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    creditnotes = await cursor.to_list(length=per_page)
    total = await db.creditnotes.count_documents(query)
    
    return {"code": 0, "creditnotes": creditnotes, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/creditnotes/{cn_id}")
async def get_creditnote(cn_id: str):
    """Get credit note details"""
    db = get_db()
    cn = await db.creditnotes.find_one({"creditnote_id": cn_id}, {"_id": 0})
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    return {"code": 0, "creditnote": cn}

@router.delete("/creditnotes/{cn_id}")
async def delete_creditnote(cn_id: str):
    """Delete credit note"""
    db = get_db()
    cn = await db.creditnotes.find_one({"creditnote_id": cn_id}, {"_id": 0})
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    
    # Reduce customer credits
    await db.contacts.update_one(
        {"contact_id": cn["customer_id"]},
        {"$inc": {"unused_credits_receivable_amount": -cn["credits_remaining"]}}
    )
    
    await db.creditnotes.delete_one({"creditnote_id": cn_id})
    return {"code": 0, "message": "Credit note deleted successfully"}

@router.post("/creditnotes/{cn_id}/invoices/{invoice_id}/apply")
async def apply_creditnote_to_invoice(cn_id: str, invoice_id: str, amount: float):
    """Apply credit note to invoice"""
    db = get_db()
    cn = await db.creditnotes.find_one({"creditnote_id": cn_id}, {"_id": 0})
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if amount > cn["credits_remaining"]:
        raise HTTPException(status_code=400, detail="Insufficient credit balance")
    if amount > invoice["balance"]:
        raise HTTPException(status_code=400, detail="Amount exceeds invoice balance")
    
    # Update credit note
    new_credits_remaining = cn["credits_remaining"] - amount
    cn_status = "closed" if new_credits_remaining <= 0 else "open"
    await db.creditnotes.update_one(
        {"creditnote_id": cn_id},
        {"$set": {
            "credits_remaining": new_credits_remaining,
            "credits_used": cn["credits_used"] + amount,
            "status": cn_status,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update invoice
    new_balance = invoice["balance"] - amount
    inv_status = "paid" if new_balance <= 0 else "partially_paid" if invoice["payment_made"] > 0 else invoice["status"]
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "balance": new_balance,
            "credits_applied": invoice.get("credits_applied", 0) + amount,
            "status": inv_status,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update customer
    await db.contacts.update_one(
        {"contact_id": cn["customer_id"]},
        {"$inc": {"unused_credits_receivable_amount": -amount, "outstanding_receivable_amount": -amount}}
    )
    
    return {"code": 0, "message": f"Credit of {amount} applied to invoice"}

@router.post("/creditnotes/{cn_id}/refund")
async def refund_creditnote(cn_id: str, amount: float):
    """Refund credit note balance to customer"""
    db = get_db()
    cn = await db.creditnotes.find_one({"creditnote_id": cn_id}, {"_id": 0})
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    if amount > cn["credits_remaining"]:
        raise HTTPException(status_code=400, detail="Insufficient credit balance")
    
    # Create refund record
    refund_id = f"REF-{uuid.uuid4().hex[:12].upper()}"
    refund_dict = {
        "refund_id": refund_id,
        "creditnote_id": cn_id,
        "customer_id": cn["customer_id"],
        "amount": amount,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    await db.refunds.insert_one(refund_dict)
    
    # Update credit note
    new_credits_remaining = cn["credits_remaining"] - amount
    cn_status = "closed" if new_credits_remaining <= 0 else "open"
    await db.creditnotes.update_one(
        {"creditnote_id": cn_id},
        {"$set": {
            "credits_remaining": new_credits_remaining,
            "refunded_amount": cn.get("refunded_amount", 0) + amount,
            "status": cn_status,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update customer
    await db.contacts.update_one(
        {"contact_id": cn["customer_id"]},
        {"$inc": {"unused_credits_receivable_amount": -amount}}
    )
    
    return {"code": 0, "message": f"Refund of {amount} processed", "refund_id": refund_id}

# ============== VENDOR CREDITS MODULE ==============

class VendorCreditCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    vendorcredit_number: Optional[str] = ""
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    bill_id: Optional[str] = ""
    line_items: List[InvoiceLineItem]
    discount_percent: float = 0
    source_of_supply: str = "DL"
    reason: str = ""
    notes: Optional[str] = ""

@router.post("/vendorcredits")
async def create_vendorcredit(vc: VendorCreditCreate):
    """Create a new vendor credit"""
    db = get_db()
    vc_id = f"VC-{uuid.uuid4().hex[:12].upper()}"
    vc_number = vc.vendorcredit_number or await get_next_number(db, "vendorcredits", "VC")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    totals = calculate_line_totals(
        [item.dict() for item in vc.line_items],
        vc.discount_percent, 0, 0
    )
    
    vc_dict = {
        "vendorcredit_id": vc_id,
        "vendorcredit_number": vc_number,
        "vendor_id": vc.vendor_id,
        "vendor_name": vc.vendor_name,
        "reference_number": vc.reference_number,
        "date": vc.date or today,
        "bill_id": vc.bill_id,
        "status": "open",
        "source_of_supply": vc.source_of_supply,
        "reason": vc.reason,
        "notes": vc.notes,
        **totals,
        "balance": totals["total"],
        "credits_remaining": totals["total"],
        "credits_used": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.vendorcredits.insert_one(vc_dict)
    
    # Update vendor credits available
    await db.contacts.update_one(
        {"contact_id": vc.vendor_id},
        {"$inc": {"unused_credits_payable_amount": totals["total"], "outstanding_payable_amount": -totals["total"]}}
    )
    
    del vc_dict["_id"]
    return {"code": 0, "message": "Vendor credit created successfully", "vendorcredit": vc_dict}

@router.get("/vendorcredits")
async def list_vendorcredits(
    status: str = "",
    vendor_id: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all vendor credits"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    skip = (page - 1) * per_page
    cursor = db.vendorcredits.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    vendorcredits = await cursor.to_list(length=per_page)
    total = await db.vendorcredits.count_documents(query)
    
    return {"code": 0, "vendorcredits": vendorcredits, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/vendorcredits/{vc_id}")
async def get_vendorcredit(vc_id: str):
    """Get vendor credit details"""
    db = get_db()
    vc = await db.vendorcredits.find_one({"vendorcredit_id": vc_id}, {"_id": 0})
    if not vc:
        raise HTTPException(status_code=404, detail="Vendor credit not found")
    return {"code": 0, "vendorcredit": vc}

@router.post("/vendorcredits/{vc_id}/bills/{bill_id}/apply")
async def apply_vendorcredit_to_bill(vc_id: str, bill_id: str, amount: float):
    """Apply vendor credit to bill"""
    db = get_db()
    vc = await db.vendorcredits.find_one({"vendorcredit_id": vc_id}, {"_id": 0})
    bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
    
    if not vc:
        raise HTTPException(status_code=404, detail="Vendor credit not found")
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if amount > vc["credits_remaining"]:
        raise HTTPException(status_code=400, detail="Insufficient credit balance")
    if amount > bill["balance"]:
        raise HTTPException(status_code=400, detail="Amount exceeds bill balance")
    
    # Update vendor credit
    new_credits_remaining = vc["credits_remaining"] - amount
    vc_status = "closed" if new_credits_remaining <= 0 else "open"
    await db.vendorcredits.update_one(
        {"vendorcredit_id": vc_id},
        {"$set": {
            "credits_remaining": new_credits_remaining,
            "credits_used": vc["credits_used"] + amount,
            "status": vc_status,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update bill
    new_balance = bill["balance"] - amount
    bill_status = "paid" if new_balance <= 0 else "partially_paid" if bill["payment_made"] > 0 else bill["status"]
    await db.bills.update_one(
        {"bill_id": bill_id},
        {"$set": {
            "balance": new_balance,
            "status": bill_status,
            "last_modified_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update vendor
    await db.contacts.update_one(
        {"contact_id": vc["vendor_id"]},
        {"$inc": {"unused_credits_payable_amount": -amount, "outstanding_payable_amount": -amount}}
    )
    
    return {"code": 0, "message": f"Credit of {amount} applied to bill"}

# ============== CUSTOMER PAYMENTS MODULE ==============

class CustomerPaymentCreate(BaseModel):
    customer_id: str
    customer_name: str
    payment_number: Optional[str] = ""
    date: Optional[str] = None
    amount: float
    payment_mode: str = "Cash"
    reference_number: Optional[str] = ""
    bank_charges: float = 0
    description: Optional[str] = ""
    invoice_ids: List[str] = []

@router.post("/customerpayments")
async def create_customer_payment(payment: CustomerPaymentCreate):
    """Record a customer payment"""
    db = get_db()
    payment_id = f"CPMT-{uuid.uuid4().hex[:12].upper()}"
    payment_number = payment.payment_number or await get_next_number(db, "customerpayments", "CPMT")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    payment_dict = {
        "payment_id": payment_id,
        "payment_number": payment_number,
        "customer_id": payment.customer_id,
        "customer_name": payment.customer_name,
        "date": payment.date or today,
        "amount": payment.amount,
        "unused_amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "reference_number": payment.reference_number,
        "bank_charges": payment.bank_charges,
        "description": payment.description,
        "invoice_ids": [],
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Apply to invoices
    remaining = payment.amount
    applied_invoices = []
    
    for inv_id in payment.invoice_ids:
        if remaining <= 0:
            break
        invoice = await db.invoices.find_one({"invoice_id": inv_id}, {"_id": 0})
        if invoice and invoice["balance"] > 0:
            to_apply = min(remaining, invoice["balance"])
            new_balance = invoice["balance"] - to_apply
            new_status = "paid" if new_balance <= 0 else "partially_paid"
            
            await db.invoices.update_one(
                {"invoice_id": inv_id},
                {"$set": {
                    "balance": new_balance,
                    "payment_made": invoice.get("payment_made", 0) + to_apply,
                    "status": new_status,
                    "last_modified_time": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            applied_invoices.append({"invoice_id": inv_id, "amount_applied": to_apply})
            remaining -= to_apply
    
    payment_dict["invoice_ids"] = applied_invoices
    payment_dict["unused_amount"] = remaining
    
    await db.customerpayments.insert_one(payment_dict)
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": payment.customer_id},
        {"$inc": {"outstanding_receivable_amount": -(payment.amount - remaining)}}
    )
    
    del payment_dict["_id"]
    return {"code": 0, "message": "Payment recorded successfully", "payment": payment_dict}

@router.get("/customerpayments")
async def list_customer_payments(
    customer_id: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all customer payments"""
    db = get_db()
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    
    skip = (page - 1) * per_page
    cursor = db.customerpayments.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    payments = await cursor.to_list(length=per_page)
    total = await db.customerpayments.count_documents(query)
    
    return {"code": 0, "customerpayments": payments, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/customerpayments/{payment_id}")
async def get_customer_payment(payment_id: str):
    """Get customer payment details"""
    db = get_db()
    payment = await db.customerpayments.find_one({"payment_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"code": 0, "payment": payment}

@router.delete("/customerpayments/{payment_id}")
async def delete_customer_payment(payment_id: str):
    """Delete customer payment"""
    db = get_db()
    payment = await db.customerpayments.find_one({"payment_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Reverse invoice applications
    for applied in payment.get("invoice_ids", []):
        inv_id = applied.get("invoice_id")
        amount = applied.get("amount_applied", 0)
        if inv_id and amount > 0:
            invoice = await db.invoices.find_one({"invoice_id": inv_id}, {"_id": 0})
            if invoice:
                new_balance = invoice["balance"] + amount
                new_status = "sent" if new_balance == invoice["total"] else "partially_paid"
                await db.invoices.update_one(
                    {"invoice_id": inv_id},
                    {"$set": {
                        "balance": new_balance,
                        "payment_made": max(0, invoice.get("payment_made", 0) - amount),
                        "status": new_status
                    }}
                )
    
    # Update customer outstanding
    total_applied = sum(a.get("amount_applied", 0) for a in payment.get("invoice_ids", []))
    await db.contacts.update_one(
        {"contact_id": payment["customer_id"]},
        {"$inc": {"outstanding_receivable_amount": total_applied}}
    )
    
    await db.customerpayments.delete_one({"payment_id": payment_id})
    return {"code": 0, "message": "Payment deleted successfully"}

# ============== VENDOR PAYMENTS MODULE ==============

class VendorPaymentCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    payment_number: Optional[str] = ""
    date: Optional[str] = None
    amount: float
    payment_mode: str = "Bank Transfer"
    reference_number: Optional[str] = ""
    bank_charges: float = 0
    description: Optional[str] = ""
    bill_ids: List[str] = []

@router.post("/vendorpayments")
async def create_vendor_payment(payment: VendorPaymentCreate):
    """Record a vendor payment"""
    db = get_db()
    payment_id = f"VPMT-{uuid.uuid4().hex[:12].upper()}"
    payment_number = payment.payment_number or await get_next_number(db, "vendorpayments", "VPMT")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    payment_dict = {
        "payment_id": payment_id,
        "payment_number": payment_number,
        "vendor_id": payment.vendor_id,
        "vendor_name": payment.vendor_name,
        "date": payment.date or today,
        "amount": payment.amount,
        "unused_amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "reference_number": payment.reference_number,
        "bank_charges": payment.bank_charges,
        "description": payment.description,
        "bill_ids": [],
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Apply to bills
    remaining = payment.amount
    applied_bills = []
    
    for bill_id in payment.bill_ids:
        if remaining <= 0:
            break
        bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
        if bill and bill["balance"] > 0:
            to_apply = min(remaining, bill["balance"])
            new_balance = bill["balance"] - to_apply
            new_status = "paid" if new_balance <= 0 else "partially_paid"
            
            await db.bills.update_one(
                {"bill_id": bill_id},
                {"$set": {
                    "balance": new_balance,
                    "payment_made": bill.get("payment_made", 0) + to_apply,
                    "status": new_status,
                    "last_modified_time": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            applied_bills.append({"bill_id": bill_id, "amount_applied": to_apply})
            remaining -= to_apply
    
    payment_dict["bill_ids"] = applied_bills
    payment_dict["unused_amount"] = remaining
    
    await db.vendorpayments.insert_one(payment_dict)
    
    # Update vendor outstanding
    await db.contacts.update_one(
        {"contact_id": payment.vendor_id},
        {"$inc": {"outstanding_payable_amount": -(payment.amount - remaining)}}
    )
    
    del payment_dict["_id"]
    return {"code": 0, "message": "Payment recorded successfully", "payment": payment_dict}

@router.get("/vendorpayments")
async def list_vendor_payments(
    vendor_id: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all vendor payments"""
    db = get_db()
    query = {}
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    skip = (page - 1) * per_page
    cursor = db.vendorpayments.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    payments = await cursor.to_list(length=per_page)
    total = await db.vendorpayments.count_documents(query)
    
    return {"code": 0, "vendorpayments": payments, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/vendorpayments/{payment_id}")
async def get_vendor_payment(payment_id: str):
    """Get vendor payment details"""
    db = get_db()
    payment = await db.vendorpayments.find_one({"payment_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"code": 0, "payment": payment}

# ============== EXPENSES MODULE ==============

class ExpenseCreate(BaseModel):
    expense_account_id: str
    expense_account_name: str
    date: Optional[str] = None
    amount: float
    paid_through_account_id: Optional[str] = ""
    paid_through_account_name: Optional[str] = ""
    vendor_id: Optional[str] = ""
    vendor_name: Optional[str] = ""
    reference_number: Optional[str] = ""
    description: Optional[str] = ""
    is_billable: bool = False
    customer_id: Optional[str] = ""
    customer_name: Optional[str] = ""
    project_id: Optional[str] = ""
    tax_id: Optional[str] = ""
    tax_name: Optional[str] = ""
    tax_percentage: float = 0
    gst_treatment: str = "out_of_scope"
    hsn_or_sac: Optional[str] = ""
    custom_fields: Optional[List[Dict]] = []

@router.post("/expenses")
async def create_expense(expense: ExpenseCreate):
    """Create a new expense"""
    db = get_db()
    expense_id = f"EXP-{uuid.uuid4().hex[:12].upper()}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Calculate tax
    tax_amount = expense.amount * (expense.tax_percentage / 100)
    total = expense.amount + tax_amount
    
    expense_dict = {
        "expense_id": expense_id,
        "expense_account_id": expense.expense_account_id,
        "expense_account_name": expense.expense_account_name,
        "date": expense.date or today,
        "amount": expense.amount,
        "tax_amount": tax_amount,
        "total": total,
        "paid_through_account_id": expense.paid_through_account_id,
        "paid_through_account_name": expense.paid_through_account_name,
        "vendor_id": expense.vendor_id,
        "vendor_name": expense.vendor_name,
        "reference_number": expense.reference_number,
        "description": expense.description,
        "is_billable": expense.is_billable,
        "is_invoiced": False,
        "customer_id": expense.customer_id,
        "customer_name": expense.customer_name,
        "project_id": expense.project_id,
        "tax_id": expense.tax_id,
        "tax_name": expense.tax_name,
        "tax_percentage": expense.tax_percentage,
        "gst_treatment": expense.gst_treatment,
        "hsn_or_sac": expense.hsn_or_sac,
        "custom_fields": expense.custom_fields,
        "status": "recorded",
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.expenses.insert_one(expense_dict)
    del expense_dict["_id"]
    return {"code": 0, "message": "Expense created successfully", "expense": expense_dict}

@router.get("/expenses")
async def list_expenses(
    status: str = "",
    expense_account_id: str = "",
    vendor_id: str = "",
    date_start: str = "",
    date_end: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List all expenses"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if expense_account_id:
        query["expense_account_id"] = expense_account_id
    if vendor_id:
        query["vendor_id"] = vendor_id
    if date_start:
        query["date"] = {"$gte": date_start}
    if date_end:
        query.setdefault("date", {})["$lte"] = date_end
    
    skip = (page - 1) * per_page
    cursor = db.expenses.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    expenses = await cursor.to_list(length=per_page)
    total = await db.expenses.count_documents(query)
    
    # Calculate totals
    pipeline = [{"$match": query}, {"$group": {"_id": None, "total": {"$sum": "$total"}}}]
    agg = await db.expenses.aggregate(pipeline).to_list(1)
    expense_total = agg[0]["total"] if agg else 0
    
    return {
        "code": 0,
        "expenses": expenses,
        "expense_total": expense_total,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/expenses/{expense_id}")
async def get_expense(expense_id: str):
    """Get expense details"""
    db = get_db()
    expense = await db.expenses.find_one({"expense_id": expense_id}, {"_id": 0})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"code": 0, "expense": expense}

@router.put("/expenses/{expense_id}")
async def update_expense(expense_id: str, expense: ExpenseCreate):
    """Update expense"""
    db = get_db()
    tax_amount = expense.amount * (expense.tax_percentage / 100)
    total = expense.amount + tax_amount
    
    update_data = {
        **expense.dict(),
        "tax_amount": tax_amount,
        "total": total,
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    result = await db.expenses.update_one({"expense_id": expense_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"code": 0, "message": "Expense updated successfully"}

@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    """Delete expense"""
    db = get_db()
    result = await db.expenses.delete_one({"expense_id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"code": 0, "message": "Expense deleted successfully"}

# ============== BANK ACCOUNTS MODULE ==============

class BankAccountCreate(BaseModel):
    account_name: str
    account_type: str = "bank"  # bank, credit_card, cash, payment_gateway
    account_number: Optional[str] = ""
    bank_name: Optional[str] = ""
    routing_number: Optional[str] = ""
    currency_code: str = "INR"
    description: Optional[str] = ""
    opening_balance: float = 0

@router.post("/bankaccounts")
async def create_bank_account(account: BankAccountCreate):
    """Create a new bank account"""
    db = get_db()
    account_id = f"BA-{uuid.uuid4().hex[:12].upper()}"
    
    account_dict = {
        "account_id": account_id,
        **account.dict(),
        "balance": account.opening_balance,
        "uncategorized_transactions": 0,
        "is_active": True,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bankaccounts.insert_one(account_dict)
    del account_dict["_id"]
    return {"code": 0, "message": "Bank account created successfully", "bankaccount": account_dict}

@router.get("/bankaccounts")
async def list_bank_accounts(account_type: str = ""):
    """List all bank accounts"""
    db = get_db()
    query = {"is_active": True}
    if account_type:
        query["account_type"] = account_type
    
    cursor = db.bankaccounts.find(query, {"_id": 0})
    accounts = await cursor.to_list(length=100)
    
    return {"code": 0, "bankaccounts": accounts}

@router.get("/bankaccounts/{account_id}")
async def get_bank_account(account_id: str):
    """Get bank account details"""
    db = get_db()
    account = await db.bankaccounts.find_one({"account_id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return {"code": 0, "bankaccount": account}

@router.put("/bankaccounts/{account_id}")
async def update_bank_account(account_id: str, account: BankAccountCreate):
    """Update bank account"""
    db = get_db()
    update_data = {
        **account.dict(),
        "last_modified_time": datetime.now(timezone.utc).isoformat()
    }
    result = await db.bankaccounts.update_one({"account_id": account_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return {"code": 0, "message": "Bank account updated successfully"}

@router.delete("/bankaccounts/{account_id}")
async def delete_bank_account(account_id: str):
    """Delete (deactivate) bank account"""
    db = get_db()
    result = await db.bankaccounts.update_one(
        {"account_id": account_id},
        {"$set": {"is_active": False, "last_modified_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return {"code": 0, "message": "Bank account deleted successfully"}

# ============== BANK TRANSACTIONS MODULE ==============

class BankTransactionCreate(BaseModel):
    account_id: str
    date: Optional[str] = None
    amount: float
    transaction_type: str  # deposit, withdrawal
    reference_number: Optional[str] = ""
    description: Optional[str] = ""
    payee: Optional[str] = ""
    category_id: Optional[str] = ""
    category_name: Optional[str] = ""

@router.post("/banktransactions")
async def create_bank_transaction(txn: BankTransactionCreate):
    """Create a bank transaction"""
    db = get_db()
    txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    txn_dict = {
        "transaction_id": txn_id,
        **txn.dict(),
        "date": txn.date or today,
        "status": "categorized" if txn.category_id else "uncategorized",
        "is_matched": False,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.banktransactions.insert_one(txn_dict)
    
    # Update bank account balance
    balance_change = txn.amount if txn.transaction_type == "deposit" else -txn.amount
    await db.bankaccounts.update_one(
        {"account_id": txn.account_id},
        {
            "$inc": {"balance": balance_change},
            "$set": {"last_modified_time": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    del txn_dict["_id"]
    return {"code": 0, "message": "Transaction created successfully", "transaction": txn_dict}

@router.get("/banktransactions")
async def list_bank_transactions(
    account_id: str = "",
    status: str = "",
    date_start: str = "",
    date_end: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List bank transactions"""
    db = get_db()
    query = {}
    if account_id:
        query["account_id"] = account_id
    if status:
        query["status"] = status
    if date_start:
        query["date"] = {"$gte": date_start}
    if date_end:
        query.setdefault("date", {})["$lte"] = date_end
    
    skip = (page - 1) * per_page
    cursor = db.banktransactions.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    transactions = await cursor.to_list(length=per_page)
    total = await db.banktransactions.count_documents(query)
    
    return {"code": 0, "transactions": transactions, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.post("/banktransactions/{txn_id}/categorize")
async def categorize_transaction(txn_id: str, category_id: str, category_name: str):
    """Categorize a bank transaction"""
    db = get_db()
    result = await db.banktransactions.update_one(
        {"transaction_id": txn_id},
        {"$set": {
            "category_id": category_id,
            "category_name": category_name,
            "status": "categorized"
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"code": 0, "message": "Transaction categorized successfully"}

@router.post("/banktransactions/{txn_id}/match")
async def match_transaction(txn_id: str, reference_type: str, reference_id: str):
    """Match transaction to invoice/bill/payment"""
    db = get_db()
    result = await db.banktransactions.update_one(
        {"transaction_id": txn_id},
        {"$set": {
            "is_matched": True,
            "matched_reference_type": reference_type,
            "matched_reference_id": reference_id,
            "status": "matched"
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"code": 0, "message": "Transaction matched successfully"}

# ============== CHART OF ACCOUNTS MODULE ==============

class ChartOfAccountCreate(BaseModel):
    account_name: str
    account_code: Optional[str] = ""
    account_type: str  # asset, liability, equity, income, expense
    description: Optional[str] = ""
    parent_account_id: Optional[str] = ""
    is_user_created: bool = True

@router.post("/chartofaccounts")
async def create_chart_of_account(account: ChartOfAccountCreate):
    """Create a chart of account"""
    db = get_db()
    account_id = f"COA-{uuid.uuid4().hex[:12].upper()}"
    
    account_dict = {
        "account_id": account_id,
        **account.dict(),
        "balance": 0,
        "is_active": True,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chartofaccounts.insert_one(account_dict)
    del account_dict["_id"]
    return {"code": 0, "message": "Account created successfully", "account": account_dict}

@router.get("/chartofaccounts")
async def list_chart_of_accounts(account_type: str = ""):
    """List chart of accounts"""
    db = get_db()
    query = {"is_active": True}
    if account_type:
        query["account_type"] = account_type
    
    cursor = db.chartofaccounts.find(query, {"_id": 0}).sort("account_name", 1)
    accounts = await cursor.to_list(length=500)
    
    return {"code": 0, "chartofaccounts": accounts}

@router.get("/chartofaccounts/{account_id}")
async def get_chart_of_account(account_id: str):
    """Get chart of account details"""
    db = get_db()
    account = await db.chartofaccounts.find_one({"account_id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"code": 0, "account": account}

@router.put("/chartofaccounts/{account_id}")
async def update_chart_of_account(account_id: str, account: ChartOfAccountCreate):
    """Update chart of account"""
    db = get_db()
    update_data = account.dict()
    result = await db.chartofaccounts.update_one({"account_id": account_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"code": 0, "message": "Account updated successfully"}

@router.delete("/chartofaccounts/{account_id}")
async def delete_chart_of_account(account_id: str):
    """Delete (deactivate) chart of account"""
    db = get_db()
    result = await db.chartofaccounts.update_one(
        {"account_id": account_id},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"code": 0, "message": "Account deleted successfully"}

# ============== JOURNAL ENTRIES MODULE ==============

class JournalLine(BaseModel):
    account_id: str
    account_name: str
    debit: float = 0
    credit: float = 0
    description: Optional[str] = ""
    contact_id: Optional[str] = ""
    contact_name: Optional[str] = ""

class JournalEntryCreate(BaseModel):
    journal_number: Optional[str] = ""
    date: Optional[str] = None
    reference_number: Optional[str] = ""
    notes: Optional[str] = ""
    line_items: List[JournalLine]
    custom_fields: Optional[List[Dict]] = []

@router.post("/journals")
async def create_journal_entry(journal: JournalEntryCreate):
    """Create a journal entry"""
    db = get_db()
    journal_id = f"JE-{uuid.uuid4().hex[:12].upper()}"
    journal_number = journal.journal_number or await get_next_number(db, "journals", "JE")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Validate debits = credits
    total_debit = sum(line.debit for line in journal.line_items)
    total_credit = sum(line.credit for line in journal.line_items)
    
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Debits ({total_debit}) must equal Credits ({total_credit})"
        )
    
    journal_dict = {
        "journal_id": journal_id,
        "journal_number": journal_number,
        "date": journal.date or today,
        "reference_number": journal.reference_number,
        "notes": journal.notes,
        "line_items": [line.dict() for line in journal.line_items],
        "total_debit": total_debit,
        "total_credit": total_credit,
        "status": "published",
        "custom_fields": journal.custom_fields,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journals.insert_one(journal_dict)
    del journal_dict["_id"]
    return {"code": 0, "message": "Journal entry created successfully", "journal": journal_dict}

@router.get("/journals")
async def list_journal_entries(
    date_start: str = "",
    date_end: str = "",
    page: int = 1,
    per_page: int = 25
):
    """List journal entries"""
    db = get_db()
    query = {}
    if date_start:
        query["date"] = {"$gte": date_start}
    if date_end:
        query.setdefault("date", {})["$lte"] = date_end
    
    skip = (page - 1) * per_page
    cursor = db.journals.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page)
    journals = await cursor.to_list(length=per_page)
    total = await db.journals.count_documents(query)
    
    return {"code": 0, "journals": journals, "page_context": {"page": page, "per_page": per_page, "total": total}}

@router.get("/journals/{journal_id}")
async def get_journal_entry(journal_id: str):
    """Get journal entry details"""
    db = get_db()
    journal = await db.journals.find_one({"journal_id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"code": 0, "journal": journal}

@router.delete("/journals/{journal_id}")
async def delete_journal_entry(journal_id: str):
    """Delete journal entry"""
    db = get_db()
    result = await db.journals.delete_one({"journal_id": journal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"code": 0, "message": "Journal entry deleted successfully"}

# ============== REPORTS MODULE ==============

@router.get("/reports/balancesheet")
async def get_balance_sheet(as_of_date: str = ""):
    """Get Balance Sheet report"""
    db = get_db()
    
    if not as_of_date:
        as_of_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Assets
    receivables_pipeline = [
        {"$match": {"balance": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]
    receivables = await db.invoices.aggregate(receivables_pipeline).to_list(1)
    accounts_receivable = receivables[0]["total"] if receivables else 0
    
    # Bank balances
    bank_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]
    bank_result = await db.bankaccounts.aggregate(bank_pipeline).to_list(1)
    bank_balance = bank_result[0]["total"] if bank_result else 0
    
    # Liabilities
    payables_pipeline = [
        {"$match": {"balance": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]
    payables = await db.bills.aggregate(payables_pipeline).to_list(1)
    accounts_payable = payables[0]["total"] if payables else 0
    
    total_assets = accounts_receivable + bank_balance
    total_liabilities = accounts_payable
    equity = total_assets - total_liabilities
    
    return {
        "code": 0,
        "report": "balance_sheet",
        "as_of_date": as_of_date,
        "assets": {
            "current_assets": {
                "accounts_receivable": accounts_receivable,
                "bank_balance": bank_balance
            },
            "total_assets": total_assets
        },
        "liabilities": {
            "current_liabilities": {
                "accounts_payable": accounts_payable
            },
            "total_liabilities": total_liabilities
        },
        "equity": {
            "retained_earnings": equity,
            "total_equity": equity
        }
    }

@router.get("/reports/profitandloss")
async def get_profit_and_loss(start_date: str = "", end_date: str = ""):
    """Get Profit & Loss report"""
    db = get_db()
    
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Revenue from invoices
    revenue_pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "tax": {"$sum": "$tax_total"}}}
    ]
    revenue_result = await db.invoices.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    tax_collected = revenue_result[0]["tax"] if revenue_result else 0
    
    # Cost of goods from bills
    cogs_pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "tax": {"$sum": "$tax_total"}}}
    ]
    cogs_result = await db.bills.aggregate(cogs_pipeline).to_list(1)
    cost_of_goods = cogs_result[0]["total"] if cogs_result else 0
    tax_paid = cogs_result[0]["tax"] if cogs_result else 0
    
    # Operating expenses
    expense_pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": "$expense_account_name", "total": {"$sum": "$total"}}}
    ]
    expense_result = await db.expenses.aggregate(expense_pipeline).to_list(100)
    expenses_by_category = {e["_id"]: e["total"] for e in expense_result if e["_id"]}
    total_expenses = sum(expenses_by_category.values())
    
    gross_profit = total_revenue - cost_of_goods
    net_profit = gross_profit - total_expenses
    
    return {
        "code": 0,
        "report": "profit_and_loss",
        "period": {"start_date": start_date, "end_date": end_date},
        "income": {
            "operating_income": total_revenue,
            "tax_collected": tax_collected,
            "total_income": total_revenue
        },
        "cost_of_goods_sold": {
            "total": cost_of_goods,
            "tax_paid": tax_paid
        },
        "gross_profit": gross_profit,
        "operating_expenses": {
            "by_category": expenses_by_category,
            "total": total_expenses
        },
        "net_profit": net_profit,
        "margins": {
            "gross_margin_percent": round((gross_profit / total_revenue * 100), 2) if total_revenue > 0 else 0,
            "net_margin_percent": round((net_profit / total_revenue * 100), 2) if total_revenue > 0 else 0
        }
    }

@router.get("/reports/receivables")
async def get_receivables_aging():
    """Get Receivables Aging report"""
    db = get_db()
    
    today = datetime.now(timezone.utc)
    
    invoices = await db.invoices.find(
        {"balance": {"$gt": 0}},
        {"_id": 0}
    ).to_list(length=10000)
    
    aging = {
        "current": {"amount": 0, "count": 0},
        "1_30_days": {"amount": 0, "count": 0},
        "31_60_days": {"amount": 0, "count": 0},
        "61_90_days": {"amount": 0, "count": 0},
        "over_90_days": {"amount": 0, "count": 0}
    }
    
    customer_aging = {}
    
    for inv in invoices:
        try:
            due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except:
            continue
        days_overdue = (today - due_date).days
        balance = inv["balance"]
        customer = inv.get("customer_name", "Unknown")
        
        if customer not in customer_aging:
            customer_aging[customer] = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0, "total": 0}
        
        if days_overdue <= 0:
            aging["current"]["amount"] += balance
            aging["current"]["count"] += 1
            customer_aging[customer]["current"] += balance
        elif days_overdue <= 30:
            aging["1_30_days"]["amount"] += balance
            aging["1_30_days"]["count"] += 1
            customer_aging[customer]["1_30"] += balance
        elif days_overdue <= 60:
            aging["31_60_days"]["amount"] += balance
            aging["31_60_days"]["count"] += 1
            customer_aging[customer]["31_60"] += balance
        elif days_overdue <= 90:
            aging["61_90_days"]["amount"] += balance
            aging["61_90_days"]["count"] += 1
            customer_aging[customer]["61_90"] += balance
        else:
            aging["over_90_days"]["amount"] += balance
            aging["over_90_days"]["count"] += 1
            customer_aging[customer]["over_90"] += balance
        
        customer_aging[customer]["total"] += balance
    
    total_receivables = sum(a["amount"] for a in aging.values())
    
    return {
        "code": 0,
        "report": "receivables_aging",
        "aging_summary": aging,
        "total_receivables": total_receivables,
        "customer_breakdown": customer_aging
    }

@router.get("/reports/payables")
async def get_payables_aging():
    """Get Payables Aging report"""
    db = get_db()
    
    today = datetime.now(timezone.utc)
    
    bills = await db.bills.find(
        {"balance": {"$gt": 0}},
        {"_id": 0}
    ).to_list(length=10000)
    
    aging = {
        "current": {"amount": 0, "count": 0},
        "1_30_days": {"amount": 0, "count": 0},
        "31_60_days": {"amount": 0, "count": 0},
        "61_90_days": {"amount": 0, "count": 0},
        "over_90_days": {"amount": 0, "count": 0}
    }
    
    vendor_aging = {}
    
    for bill in bills:
        try:
            due_date = datetime.strptime(bill["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except:
            continue
        days_overdue = (today - due_date).days
        balance = bill["balance"]
        vendor = bill.get("vendor_name", "Unknown")
        
        if vendor not in vendor_aging:
            vendor_aging[vendor] = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0, "total": 0}
        
        if days_overdue <= 0:
            aging["current"]["amount"] += balance
            aging["current"]["count"] += 1
            vendor_aging[vendor]["current"] += balance
        elif days_overdue <= 30:
            aging["1_30_days"]["amount"] += balance
            aging["1_30_days"]["count"] += 1
            vendor_aging[vendor]["1_30"] += balance
        elif days_overdue <= 60:
            aging["31_60_days"]["amount"] += balance
            aging["31_60_days"]["count"] += 1
            vendor_aging[vendor]["31_60"] += balance
        elif days_overdue <= 90:
            aging["61_90_days"]["amount"] += balance
            aging["61_90_days"]["count"] += 1
            vendor_aging[vendor]["61_90"] += balance
        else:
            aging["over_90_days"]["amount"] += balance
            aging["over_90_days"]["count"] += 1
            vendor_aging[vendor]["over_90"] += balance
        
        vendor_aging[vendor]["total"] += balance
    
    total_payables = sum(a["amount"] for a in aging.values())
    
    return {
        "code": 0,
        "report": "payables_aging",
        "aging_summary": aging,
        "total_payables": total_payables,
        "vendor_breakdown": vendor_aging
    }

@router.get("/reports/gst")
async def get_gst_summary(start_date: str = "", end_date: str = ""):
    """Get GST Summary for filing"""
    db = get_db()
    
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Output GST (from sales invoices) - GSTR-1
    invoice_pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": None,
            "taxable_value": {"$sum": "$sub_total"},
            "total_gst": {"$sum": "$tax_total"},
            "invoice_count": {"$sum": 1}
        }}
    ]
    invoice_result = await db.invoices.aggregate(invoice_pipeline).to_list(1)
    
    # Input GST (from purchase bills) - GSTR-2
    bill_pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": None,
            "taxable_value": {"$sum": "$sub_total"},
            "total_gst": {"$sum": "$tax_total"},
            "bill_count": {"$sum": 1}
        }}
    ]
    bill_result = await db.bills.aggregate(bill_pipeline).to_list(1)
    
    output_gst = invoice_result[0]["total_gst"] if invoice_result else 0
    input_gst = bill_result[0]["total_gst"] if bill_result else 0
    net_gst_payable = output_gst - input_gst
    
    return {
        "code": 0,
        "report": "gst_summary",
        "period": {"start_date": start_date, "end_date": end_date},
        "gstr1_outward_supplies": {
            "taxable_value": invoice_result[0]["taxable_value"] if invoice_result else 0,
            "total_gst": output_gst,
            "invoice_count": invoice_result[0]["invoice_count"] if invoice_result else 0
        },
        "gstr2_inward_supplies": {
            "taxable_value": bill_result[0]["taxable_value"] if bill_result else 0,
            "total_gst": input_gst,
            "bill_count": bill_result[0]["bill_count"] if bill_result else 0
        },
        "gstr3b_summary": {
            "output_gst": output_gst,
            "input_gst_credit": input_gst,
            "net_gst_payable": net_gst_payable
        }
    }

@router.get("/reports/dashboard")
async def get_dashboard_summary():
    """Get comprehensive dashboard summary"""
    db = get_db()
    
    # Counts
    customers = await db.contacts.count_documents({"contact_type": "customer", "status": "active"})
    vendors = await db.contacts.count_documents({"contact_type": "vendor", "status": "active"})
    items = await db.items.count_documents({"status": "active"})
    
    # Sales Pipeline
    estimates = await db.estimates.count_documents({})
    open_estimates = await db.estimates.count_documents({"status": {"$in": ["draft", "sent"]}})
    salesorders = await db.salesorders.count_documents({})
    open_so = await db.salesorders.count_documents({"status": {"$in": ["draft", "confirmed"]}})
    invoices = await db.invoices.count_documents({})
    unpaid_invoices = await db.invoices.count_documents({"balance": {"$gt": 0}})
    
    # Purchase Pipeline
    purchaseorders = await db.purchaseorders.count_documents({})
    open_po = await db.purchaseorders.count_documents({"status": {"$in": ["draft", "issued"]}})
    bills = await db.bills.count_documents({})
    unpaid_bills = await db.bills.count_documents({"balance": {"$gt": 0}})
    
    # Financials
    rev_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total"}, "collected": {"$sum": "$payment_made"}}}]
    rev_result = await db.invoices.aggregate(rev_pipeline).to_list(1)
    total_revenue = rev_result[0]["total"] if rev_result else 0
    collected = rev_result[0]["collected"] if rev_result else 0
    
    pay_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total"}, "paid": {"$sum": "$payment_made"}}}]
    pay_result = await db.bills.aggregate(pay_pipeline).to_list(1)
    total_payables = pay_result[0]["total"] if pay_result else 0
    paid = pay_result[0]["paid"] if pay_result else 0
    
    exp_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total"}}}]
    exp_result = await db.expenses.aggregate(exp_pipeline).to_list(1)
    total_expenses = exp_result[0]["total"] if exp_result else 0
    
    return {
        "code": 0,
        "master_data": {
            "customers": customers,
            "vendors": vendors,
            "items": items
        },
        "sales_pipeline": {
            "estimates": {"total": estimates, "open": open_estimates},
            "salesorders": {"total": salesorders, "open": open_so},
            "invoices": {"total": invoices, "unpaid": unpaid_invoices}
        },
        "purchase_pipeline": {
            "purchaseorders": {"total": purchaseorders, "open": open_po},
            "bills": {"total": bills, "unpaid": unpaid_bills}
        },
        "financials": {
            "total_revenue": total_revenue,
            "collected": collected,
            "receivables": total_revenue - collected,
            "total_payables": total_payables,
            "paid": paid,
            "outstanding_payables": total_payables - paid,
            "total_expenses": total_expenses
        }
    }
