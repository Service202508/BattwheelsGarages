# Serial and Batch Tracking Module
# Comprehensive serial number and batch/lot tracking for inventory items

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
import uuid
from fastapi import Request
from utils.database import extract_org_id, org_query


router = APIRouter(prefix="/serial-batch", tags=["Serial & Batch Tracking"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
items_collection = db["items"]
serial_numbers_collection = db["item_serial_numbers"]
batch_numbers_collection = db["item_batch_numbers"]
tracking_history_collection = db["serial_batch_history"]

# ========================= MODELS =========================

class ItemTrackingConfig(BaseModel):
    """Configure tracking for an item"""
    item_id: str
    enable_serial: bool = False
    enable_batch: bool = False
    serial_prefix: str = ""
    batch_prefix: str = ""
    require_on_sale: bool = True
    require_on_purchase: bool = True
    auto_generate_serial: bool = False

class SerialNumberCreate(BaseModel):
    """Create a serial number"""
    item_id: str
    serial_number: str
    warehouse_id: str = ""
    purchase_id: str = ""
    purchase_date: str = ""
    cost_price: float = 0
    warranty_expiry: str = ""
    notes: str = ""
    custom_fields: Dict = {}

class SerialNumberBulkCreate(BaseModel):
    """Bulk create serial numbers"""
    item_id: str
    warehouse_id: str = ""
    prefix: str = ""
    start_number: int = 1
    count: int = 1
    purchase_id: str = ""
    purchase_date: str = ""
    cost_price: float = 0

class BatchNumberCreate(BaseModel):
    """Create a batch/lot number"""
    item_id: str
    batch_number: str
    warehouse_id: str = ""
    quantity: float = 0
    available_quantity: float = 0
    manufacturing_date: str = ""
    expiry_date: str = ""
    supplier_id: str = ""
    supplier_batch: str = ""
    cost_price: float = 0
    notes: str = ""

class SerialAssignment(BaseModel):
    """Assign serials to a transaction"""
    transaction_type: str  # invoice, shipment, return
    transaction_id: str
    line_item_id: str
    serial_ids: List[str]

class BatchAssignment(BaseModel):
    """Assign batch quantities to a transaction"""
    transaction_type: str
    transaction_id: str
    line_item_id: str
    batch_allocations: List[Dict]  # [{"batch_id": "...", "quantity": 5}]

# ========================= HELPERS =========================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def get_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ========================= ITEM TRACKING CONFIG =========================

@router.post("/items/{item_id}/configure")
async def configure_item_tracking(item_id: str, config: ItemTrackingConfig, request: Request)::
    org_id = extract_org_id(request)
    """Enable/configure serial or batch tracking for an item"""
    item = await items_collection.find_one({"item_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.get("item_type") not in ["inventory", "sales_and_purchases"]:
        raise HTTPException(status_code=400, detail="Only inventory items can have tracking enabled")
    
    update_data = {
        "enable_serial_tracking": config.enable_serial,
        "enable_batch_tracking": config.enable_batch,
        "serial_prefix": config.serial_prefix,
        "batch_prefix": config.batch_prefix,
        "require_tracking_on_sale": config.require_on_sale,
        "require_tracking_on_purchase": config.require_on_purchase,
        "auto_generate_serial": config.auto_generate_serial,
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await items_collection.update_one(
        {"item_id": item_id},
        {"$set": update_data}
    )
    
    return {
        "code": 0,
        "message": "Item tracking configuration updated",
        "config": {
            "item_id": item_id,
            "item_name": item.get("name"),
            **update_data
        }
    }

@router.get("/items/{item_id}/config")
async def get_item_tracking_config(item_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Get tracking configuration for an item"""
    item = await items_collection.find_one(
        {"item_id": item_id},
        {"_id": 0, "item_id": 1, "name": 1, "sku": 1,
         "enable_serial_tracking": 1, "enable_batch_tracking": 1,
         "serial_prefix": 1, "batch_prefix": 1,
         "require_tracking_on_sale": 1, "require_tracking_on_purchase": 1,
         "auto_generate_serial": 1}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get counts
    serial_count = await serial_numbers_collection.count_documents({"item_id": item_id})
    batch_count = await batch_numbers_collection.count_documents({"item_id": item_id})
    available_serials = await serial_numbers_collection.count_documents({"item_id": item_id, "status": "available"})
    
    return {
        "code": 0,
        "config": item,
        "stats": {
            "total_serials": serial_count,
            "available_serials": available_serials,
            "total_batches": batch_count
        }
    }

@router.get("/items/tracking-enabled")
async def list_tracking_enabled_items(request: Request)::
    org_id = extract_org_id(request)
    """List all items with serial or batch tracking enabled"""
    items = await items_collection.find(
        {"$or": [
            {"enable_serial_tracking": True},
            {"enable_batch_tracking": True}
        ]},
        {"_id": 0, "item_id": 1, "name": 1, "sku": 1,
         "enable_serial_tracking": 1, "enable_batch_tracking": 1,
         "stock_on_hand": 1}
    ).to_list(1000)
    
    # Enrich with counts
    for item in items:
        if item.get("enable_serial_tracking"):
            item["serial_count"] = await serial_numbers_collection.count_documents({
                "item_id": item["item_id"], "status": "available"
            })
        if item.get("enable_batch_tracking"):
            item["batch_count"] = await batch_numbers_collection.count_documents({
                "item_id": item["item_id"], "available_quantity": {"$gt": 0}
            })
    
    return {"code": 0, "items": items, "total": len(items)}

# ========================= SERIAL NUMBERS =========================

@router.post("/serials")
async def create_serial_number(data: SerialNumberCreate, request: Request)::
    org_id = extract_org_id(request)
    """Create a single serial number"""
    # Validate item
    item = await items_collection.find_one({"item_id": data.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check for duplicate
    existing = await serial_numbers_collection.find_one({
        "item_id": data.item_id,
        "serial_number": data.serial_number
    })
    if existing:
        raise HTTPException(status_code=400, detail="Serial number already exists for this item")
    
    serial_id = generate_id("SN")
    
    serial_doc = {
        "serial_id": serial_id,
        "item_id": data.item_id,
        "item_name": item.get("name"),
        "sku": item.get("sku"),
        "serial_number": data.serial_number,
        "warehouse_id": data.warehouse_id,
        "status": "available",  # available, sold, returned, damaged, reserved
        "purchase_id": data.purchase_id,
        "purchase_date": data.purchase_date or get_today(),
        "cost_price": data.cost_price,
        "warranty_expiry": data.warranty_expiry,
        "notes": data.notes,
        "custom_fields": data.custom_fields,
        "sold_invoice_id": None,
        "sold_date": None,
        "customer_id": None,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await serial_numbers_collection.insert_one(serial_doc)
    
    # Log history
    await tracking_history_collection.insert_one({
        "history_id": generate_id("TH"),
        "tracking_type": "serial",
        "tracking_id": serial_id,
        "item_id": data.item_id,
        "action": "created",
        "details": {"serial_number": data.serial_number},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    serial_doc.pop("_id", None)
    return {"code": 0, "message": "Serial number created", "serial": serial_doc}

@router.post("/serials/bulk")
async def bulk_create_serials(data: SerialNumberBulkCreate, request: Request)::
    org_id = extract_org_id(request)
    """Bulk create serial numbers with auto-numbering"""
    item = await items_collection.find_one({"item_id": data.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    created = []
    errors = []
    
    for i in range(data.count):
        serial_num = f"{data.prefix}{data.start_number + i:06d}"
        
        # Check duplicate
        existing = await serial_numbers_collection.find_one({
            "item_id": data.item_id,
            "serial_number": serial_num
        })
        if existing:
            errors.append({"serial": serial_num, "error": "Already exists"})
            continue
        
        serial_id = generate_id("SN")
        serial_doc = {
            "serial_id": serial_id,
            "item_id": data.item_id,
            "item_name": item.get("name"),
            "sku": item.get("sku"),
            "serial_number": serial_num,
            "warehouse_id": data.warehouse_id,
            "status": "available",
            "purchase_id": data.purchase_id,
            "purchase_date": data.purchase_date or get_today(),
            "cost_price": data.cost_price,
            "created_time": datetime.now(timezone.utc).isoformat()
        }
        
        await serial_numbers_collection.insert_one(serial_doc)
        created.append({"serial_id": serial_id, "serial_number": serial_num})
    
    return {
        "code": 0,
        "message": f"Created {len(created)} serial numbers",
        "created": created,
        "errors": errors
    }

@router.get("/serials")
async def list_serial_numbers(
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    status: Optional[str] = None,
    search: str = "",
    page: int = 1,
    per_page: int = 50, request: Request)::
    org_id = extract_org_id(request)
    """List serial numbers with filters"""
    query = {}
    if item_id:
        query["item_id"] = item_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"serial_number": {"$regex": search, "$options": "i"}},
            {"item_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await serial_numbers_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    serials = await serial_numbers_collection.find(query, {"_id": 0}) \
        .sort("created_time", -1) \
        .skip(skip) \
        .limit(per_page) \
        .to_list(per_page)
    
    return {
        "code": 0,
        "serials": serials,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/serials/{serial_id}")
async def get_serial_number(serial_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Get serial number details with history"""
    serial = await serial_numbers_collection.find_one({"serial_id": serial_id}, {"_id": 0})
    if not serial:
        raise HTTPException(status_code=404, detail="Serial number not found")
    
    # Get history
    history = await tracking_history_collection.find(
        {"tracking_id": serial_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    
    serial["history"] = history
    return {"code": 0, "serial": serial}

@router.get("/serials/lookup/{serial_number}")
async def lookup_serial_number(serial_number: str, item_id: Optional[str] = None, request: Request)::
    org_id = extract_org_id(request)
    """Look up a serial number across all items or for a specific item"""
    query = {"serial_number": serial_number}
    if item_id:
        query["item_id"] = item_id
    
    serial = await serial_numbers_collection.find_one(query, {"_id": 0})
    if not serial:
        raise HTTPException(status_code=404, detail="Serial number not found")
    
    return {"code": 0, "serial": serial}

@router.put("/serials/{serial_id}/status")
async def update_serial_status(serial_id: str, status: str, reason: str = "", request: Request)::
    org_id = extract_org_id(request)
    """Update serial number status"""
    valid_statuses = ["available", "sold", "returned", "damaged", "reserved"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    serial = await serial_numbers_collection.find_one({"serial_id": serial_id})
    if not serial:
        raise HTTPException(status_code=404, detail="Serial number not found")
    
    old_status = serial.get("status")
    
    await serial_numbers_collection.update_one(
        {"serial_id": serial_id},
        {"$set": {
            "status": status,
            "status_reason": reason,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log history
    await tracking_history_collection.insert_one({
        "history_id": generate_id("TH"),
        "tracking_type": "serial",
        "tracking_id": serial_id,
        "item_id": serial["item_id"],
        "action": "status_changed",
        "details": {"from": old_status, "to": status, "reason": reason},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"code": 0, "message": f"Status updated to {status}"}

# ========================= BATCH NUMBERS =========================

@router.post("/batches")
async def create_batch_number(data: BatchNumberCreate, request: Request)::
    org_id = extract_org_id(request)
    """Create a batch/lot number"""
    item = await items_collection.find_one({"item_id": data.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check for duplicate
    existing = await batch_numbers_collection.find_one({
        "item_id": data.item_id,
        "batch_number": data.batch_number
    })
    if existing:
        raise HTTPException(status_code=400, detail="Batch number already exists for this item")
    
    batch_id = generate_id("BN")
    
    batch_doc = {
        "batch_id": batch_id,
        "item_id": data.item_id,
        "item_name": item.get("name"),
        "sku": item.get("sku"),
        "batch_number": data.batch_number,
        "warehouse_id": data.warehouse_id,
        "quantity": data.quantity,
        "available_quantity": data.available_quantity or data.quantity,
        "manufacturing_date": data.manufacturing_date,
        "expiry_date": data.expiry_date,
        "supplier_id": data.supplier_id,
        "supplier_batch": data.supplier_batch,
        "cost_price": data.cost_price,
        "notes": data.notes,
        "status": "active",  # active, expired, depleted
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await batch_numbers_collection.insert_one(batch_doc)
    
    # Log history
    await tracking_history_collection.insert_one({
        "history_id": generate_id("TH"),
        "tracking_type": "batch",
        "tracking_id": batch_id,
        "item_id": data.item_id,
        "action": "created",
        "details": {"batch_number": data.batch_number, "quantity": data.quantity},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    batch_doc.pop("_id", None)
    return {"code": 0, "message": "Batch number created", "batch": batch_doc}

@router.get("/batches")
async def list_batch_numbers(
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    status: Optional[str] = None,
    expiring_within_days: Optional[int] = None,
    search: str = "",
    page: int = 1,
    per_page: int = 50, request: Request)::
    org_id = extract_org_id(request)
    """List batch numbers with filters"""
    query = {}
    if item_id:
        query["item_id"] = item_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"batch_number": {"$regex": search, "$options": "i"}},
            {"item_name": {"$regex": search, "$options": "i"}}
        ]
    if expiring_within_days:
        future_date = (datetime.now(timezone.utc) + timedelta(days=expiring_within_days)).strftime("%Y-%m-%d")
        query["expiry_date"] = {"$lte": future_date, "$gt": get_today()}
    
    total = await batch_numbers_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    batches = await batch_numbers_collection.find(query, {"_id": 0}) \
        .sort("created_time", -1) \
        .skip(skip) \
        .limit(per_page) \
        .to_list(per_page)
    
    # Add expiry status
    today = get_today()
    for batch in batches:
        if batch.get("expiry_date") and batch["expiry_date"] < today:
            batch["is_expired"] = True
        elif batch.get("expiry_date"):
            days_to_expiry = (datetime.strptime(batch["expiry_date"], "%Y-%m-%d") - datetime.now()).days
            batch["days_to_expiry"] = max(0, days_to_expiry)
    
    return {
        "code": 0,
        "batches": batches,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/batches/expiring")
async def get_expiring_batches(days: int = 30, request: Request)::
    org_id = extract_org_id(request)
    """Get batches expiring within specified days"""
    future_date = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    today = get_today()
    
    batches = await batch_numbers_collection.find({
        "expiry_date": {"$lte": future_date, "$gte": today},
        "available_quantity": {"$gt": 0}
    }, {"_id": 0}).sort("expiry_date", 1).to_list(100)
    
    for batch in batches:
        days_to_expiry = (datetime.strptime(batch["expiry_date"], "%Y-%m-%d") - datetime.now()).days
        batch["days_to_expiry"] = max(0, days_to_expiry)
    
    return {"code": 0, "expiring_batches": batches, "total": len(batches)}

@router.get("/batches/{batch_id}")
async def get_batch_number(batch_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Get batch number details with history"""
    batch = await batch_numbers_collection.find_one({"batch_id": batch_id}, {"_id": 0})
    if not batch:
        raise HTTPException(status_code=404, detail="Batch number not found")
    
    # Get history
    history = await tracking_history_collection.find(
        {"tracking_id": batch_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    
    batch["history"] = history
    return {"code": 0, "batch": batch}

@router.put("/batches/{batch_id}/quantity")
async def adjust_batch_quantity(batch_id: str, quantity_change: float, reason: str = "", request: Request)::
    org_id = extract_org_id(request)
    """Adjust batch quantity (positive to add, negative to deduct)"""
    batch = await batch_numbers_collection.find_one({"batch_id": batch_id})
    if not batch:
        raise HTTPException(status_code=404, detail="Batch number not found")
    
    old_quantity = batch.get("available_quantity", 0)
    new_quantity = old_quantity + quantity_change
    
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail=f"Insufficient batch quantity. Available: {old_quantity}")
    
    status = batch.get("status")
    if new_quantity == 0:
        status = "depleted"
    elif status == "depleted" and new_quantity > 0:
        status = "active"
    
    await batch_numbers_collection.update_one(
        {"batch_id": batch_id},
        {"$set": {
            "available_quantity": new_quantity,
            "status": status,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log history
    await tracking_history_collection.insert_one({
        "history_id": generate_id("TH"),
        "tracking_type": "batch",
        "tracking_id": batch_id,
        "item_id": batch["item_id"],
        "action": "quantity_adjusted",
        "details": {
            "from": old_quantity,
            "to": new_quantity,
            "change": quantity_change,
            "reason": reason
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "code": 0,
        "message": "Batch quantity adjusted",
        "new_quantity": new_quantity
    }

# ========================= TRANSACTION ASSIGNMENTS =========================

@router.post("/assign/serials")
async def assign_serials_to_transaction(assignment: SerialAssignment, request: Request)::
    org_id = extract_org_id(request)
    """Assign serial numbers to an invoice/shipment"""
    updated = 0
    errors = []
    
    for serial_id in assignment.serial_ids:
        serial = await serial_numbers_collection.find_one({"serial_id": serial_id})
        if not serial:
            errors.append({"serial_id": serial_id, "error": "Not found"})
            continue
        if serial.get("status") != "available":
            errors.append({"serial_id": serial_id, "error": f"Status is {serial.get('status')}, not available"})
            continue
        
        update_data = {
            "status": "sold",
            f"{assignment.transaction_type}_id": assignment.transaction_id,
            "sold_line_item_id": assignment.line_item_id,
            "sold_date": get_today(),
            "updated_time": datetime.now(timezone.utc).isoformat()
        }
        
        await serial_numbers_collection.update_one(
            {"serial_id": serial_id},
            {"$set": update_data}
        )
        
        # Log history
        await tracking_history_collection.insert_one({
            "history_id": generate_id("TH"),
            "tracking_type": "serial",
            "tracking_id": serial_id,
            "item_id": serial["item_id"],
            "action": "assigned",
            "details": {
                "transaction_type": assignment.transaction_type,
                "transaction_id": assignment.transaction_id
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        updated += 1
    
    return {
        "code": 0,
        "message": f"Assigned {updated} serial numbers",
        "assigned_count": updated,
        "errors": errors
    }

@router.post("/assign/batches")
async def assign_batches_to_transaction(assignment: BatchAssignment, request: Request)::
    org_id = extract_org_id(request)
    """Assign batch quantities to an invoice/shipment"""
    allocated = []
    errors = []
    
    for alloc in assignment.batch_allocations:
        batch_id = alloc.get("batch_id")
        qty = alloc.get("quantity", 0)
        
        batch = await batch_numbers_collection.find_one({"batch_id": batch_id})
        if not batch:
            errors.append({"batch_id": batch_id, "error": "Not found"})
            continue
        
        available = batch.get("available_quantity", 0)
        if available < qty:
            errors.append({"batch_id": batch_id, "error": f"Insufficient quantity. Available: {available}"})
            continue
        
        new_available = available - qty
        status = "depleted" if new_available == 0 else batch.get("status")
        
        await batch_numbers_collection.update_one(
            {"batch_id": batch_id},
            {"$set": {
                "available_quantity": new_available,
                "status": status,
                "updated_time": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Log history
        await tracking_history_collection.insert_one({
            "history_id": generate_id("TH"),
            "tracking_type": "batch",
            "tracking_id": batch_id,
            "item_id": batch["item_id"],
            "action": "allocated",
            "details": {
                "transaction_type": assignment.transaction_type,
                "transaction_id": assignment.transaction_id,
                "quantity": qty
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        allocated.append({
            "batch_id": batch_id,
            "batch_number": batch.get("batch_number"),
            "quantity_allocated": qty
        })
    
    return {
        "code": 0,
        "message": f"Allocated {len(allocated)} batches",
        "allocations": allocated,
        "errors": errors
    }

# ========================= REPORTS =========================

@router.get("/reports/serial-summary")
async def serial_tracking_summary(request: Request)::
    org_id = extract_org_id(request)
    """Get serial number tracking summary"""
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    status_counts = await serial_numbers_collection.aggregate(pipeline).to_list(10)
    status_dict = {s["_id"]: s["count"] for s in status_counts}
    
    total = sum(status_dict.values())
    
    return {
        "code": 0,
        "summary": {
            "total_serials": total,
            "available": status_dict.get("available", 0),
            "sold": status_dict.get("sold", 0),
            "returned": status_dict.get("returned", 0),
            "damaged": status_dict.get("damaged", 0),
            "reserved": status_dict.get("reserved", 0)
        }
    }

@router.get("/reports/batch-summary")
async def batch_tracking_summary(request: Request)::
    org_id = extract_org_id(request)
    """Get batch tracking summary"""
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_quantity": {"$sum": "$available_quantity"}
        }}
    ]
    
    status_data = await batch_numbers_collection.aggregate(pipeline).to_list(10)
    
    today = get_today()
    expiring_count = await batch_numbers_collection.count_documents({
        "expiry_date": {
            "$lte": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
            "$gte": today
        },
        "available_quantity": {"$gt": 0}
    })
    
    expired_count = await batch_numbers_collection.count_documents({
        "expiry_date": {"$lt": today},
        "available_quantity": {"$gt": 0}
    })
    
    return {
        "code": 0,
        "summary": {
            "total_batches": sum(s["count"] for s in status_data),
            "active_batches": next((s["count"] for s in status_data if s["_id"] == "active"), 0),
            "depleted_batches": next((s["count"] for s in status_data if s["_id"] == "depleted"), 0),
            "expiring_soon": expiring_count,
            "expired_with_stock": expired_count,
            "total_available_quantity": sum(s.get("total_quantity", 0) for s in status_data if s["_id"] == "active")
        }
    }

@router.get("/reports/item-tracking/{item_id}")
async def item_tracking_report(item_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Get comprehensive tracking report for an item"""
    item = await items_collection.find_one({"item_id": item_id}, {"_id": 0, "item_id": 1, "name": 1, "sku": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Serial stats
    serial_pipeline = [
        {"$match": {"item_id": item_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    serial_stats = await serial_numbers_collection.aggregate(serial_pipeline).to_list(10)
    
    # Batch stats
    batch_pipeline = [
        {"$match": {"item_id": item_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_qty": {"$sum": "$available_quantity"}
        }}
    ]
    batch_stats = await batch_numbers_collection.aggregate(batch_pipeline).to_list(10)
    
    # Recent history
    history = await tracking_history_collection.find(
        {"item_id": item_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20).to_list(20)
    
    return {
        "code": 0,
        "item": item,
        "serial_stats": {s["_id"]: s["count"] for s in serial_stats},
        "batch_stats": {s["_id"]: {"count": s["count"], "quantity": s["total_qty"]} for s in batch_stats},
        "recent_history": history
    }
