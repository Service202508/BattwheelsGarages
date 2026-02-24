# Inventory Enhanced Module - Variants, Bundles, Shipments, Returns
# Full Zoho-style inventory management with advanced features

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
import uuid
import logging

from core.subscriptions.entitlement import require_feature
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory-enhanced", tags=["Inventory Enhanced"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
items_collection = db["items"]  # Use same collection as items_enhanced route
variants_collection = db["item_variants"]
bundles_collection = db["item_bundles"]
bundle_components_collection = db["bundle_components"]
serial_batches_collection = db["item_serial_batches"]
warehouses_collection = db["warehouses"]
stock_locations_collection = db["item_stock_locations"]
shipments_collection = db["shipments"]
shipment_items_collection = db["shipment_items"]
returns_collection = db["inventory_returns"]
adjustments_collection = db["inventory_adjustments_v2"]
settings_collection = db["inventory_settings"]
history_collection = db["inventory_history"]
sales_orders_collection = db["salesorders_enhanced"]
so_line_items_collection = db["salesorder_line_items"]

# ========================= MODELS =========================

class VariantCreate(BaseModel):
    item_id: str
    variant_name: str
    sku: str = ""
    additional_rate: float = 0.0
    attributes: Dict[str, str] = {}  # e.g., {"size": "L", "color": "Red"}
    initial_stock: int = 0
    warehouse_id: str = ""

class VariantUpdate(BaseModel):
    variant_name: Optional[str] = None
    additional_rate: Optional[float] = None
    attributes: Optional[Dict[str, str]] = None
    sku: Optional[str] = None

class BundleCreate(BaseModel):
    name: str
    sku: str = ""
    description: str = ""
    rate: float = 0
    components: List[Dict[str, Any]] = []  # [{"item_id": "...", "quantity": 2}]
    auto_calculate_rate: bool = True

class BundleUpdate(BaseModel):
    name: Optional[str] = None
    rate: Optional[float] = None
    description: Optional[str] = None
    components: Optional[List[Dict[str, Any]]] = None

class SerialBatchCreate(BaseModel):
    item_id: str
    tracking_type: str = "serial"  # serial or batch
    number: str
    warehouse_id: str = ""
    expiry_date: Optional[str] = None
    quantity: int = 1  # For batch only, serial is always 1
    notes: str = ""

class ShipmentCreate(BaseModel):
    sales_order_id: str
    carrier: str = ""
    tracking_number: str = ""
    items: List[Dict[str, Any]] = []  # [{"line_item_id": "...", "quantity": 1, "serial_batch_id": "..."}]
    notes: str = ""

class ReturnCreate(BaseModel):
    shipment_id: str
    reason: str = ""
    restock: bool = True
    items: List[Dict[str, Any]] = []  # [{"shipment_item_id": "...", "quantity": 1}]
    notes: str = ""

class StockAdjustmentCreate(BaseModel):
    item_id: str
    variant_id: Optional[str] = None
    warehouse_id: str
    adjustment_type: str = "add"  # add, subtract, set
    quantity: float
    reason: str
    reference_number: str = ""
    notes: str = ""

class WarehouseCreate(BaseModel):
    name: str
    code: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    is_primary: bool = False
    is_active: bool = True

# ========================= HELPERS =========================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def round_qty(value: float) -> float:
    return round(value, 4)

async def get_item_stock(item_id: str, warehouse_id: str = None, variant_id: str = None) -> float:
    """Get available stock for an item"""
    query = {"item_id": item_id}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if variant_id:
        query["variant_id"] = variant_id
    
    locations = await stock_locations_collection.find(query).to_list(100)
    total = sum(loc.get("available_stock", 0) for loc in locations)
    return total

async def adjust_stock(
    item_id: str,
    quantity: float,
    warehouse_id: str,
    reason: str,
    variant_id: str = None,
    user_id: str = ""
):
    """Atomically adjust stock levels"""
    query = {"item_id": item_id, "warehouse_id": warehouse_id}
    if variant_id:
        query["variant_id"] = variant_id
    
    location = await stock_locations_collection.find_one(query)
    
    if not location:
        # Create new stock location
        location = {
            "location_id": generate_id("LOC"),
            "item_id": item_id,
            "variant_id": variant_id,
            "warehouse_id": warehouse_id,
            "available_stock": 0,
            "reserved_stock": 0,
            "created_time": datetime.now(timezone.utc).isoformat()
        }
        await stock_locations_collection.insert_one(location)
    
    new_stock = location.get("available_stock", 0) + quantity
    
    if new_stock < 0:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {location.get('available_stock', 0)}")
    
    await stock_locations_collection.update_one(
        query,
        {"$set": {"available_stock": new_stock, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Log history
    await history_collection.insert_one({
        "history_id": generate_id("HIST"),
        "item_id": item_id,
        "variant_id": variant_id,
        "warehouse_id": warehouse_id,
        "action": "stock_adjusted",
        "quantity_change": quantity,
        "new_stock": new_stock,
        "reason": reason,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return new_stock

async def add_history(entity_type: str, entity_id: str, action: str, details: str, user_id: str = ""):
    """Add inventory history entry"""
    await history_collection.insert_one({
        "history_id": generate_id("HIST"),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ========================= SUMMARY =========================

@router.get("/summary")
async def get_inventory_summary(request: Request):
    org_id = extract_org_id(request)
    """Get inventory summary statistics"""
    total_items = await items_collection.count_documents({"status": "active"})
    total_variants = await variants_collection.count_documents(org_query(org_id))
    total_bundles = await bundles_collection.count_documents({"status": "active"})
    total_warehouses = await warehouses_collection.count_documents({"is_active": True})
    
    # Stock value calculation
    pipeline = [
        {"$match": {"status": "active"}},
        {"$lookup": {
            "from": "item_stock_locations",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "stock"
        }},
        {"$unwind": {"path": "$stock", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": None,
            "total_stock_value": {"$sum": {"$multiply": [{"$ifNull": ["$stock.available_stock", 0]}, {"$ifNull": ["$purchase_rate", 0]}]}},
            "total_units": {"$sum": {"$ifNull": ["$stock.available_stock", 0]}}
        }}
    ]
    stock_data = await items_collection.aggregate(pipeline).to_list(1)
    
    # Low stock count
    low_stock_items = await items_collection.aggregate([
        {"$match": {"status": "active", "track_inventory": True}},
        {"$lookup": {
            "from": "item_stock_locations",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "stock"
        }},
        {"$addFields": {"total_stock": {"$sum": "$stock.available_stock"}}},
        {"$match": {"$expr": {"$lt": ["$total_stock", "$reorder_level"]}}}
    ]).to_list(1000)
    
    # Pending shipments
    pending_shipments = await shipments_collection.count_documents({"status": {"$in": ["packed", "shipped"]}})
    
    # Returns needing attention
    pending_returns = await returns_collection.count_documents({"status": "pending"})
    
    return {
        "code": 0,
        "summary": {
            "total_items": total_items,
            "total_variants": total_variants,
            "total_bundles": total_bundles,
            "total_warehouses": total_warehouses,
            "total_stock_value": round(stock_data[0].get("total_stock_value", 0) if stock_data else 0, 2),
            "total_units": round(stock_data[0].get("total_units", 0) if stock_data else 0, 2),
            "low_stock_count": len(low_stock_items),
            "pending_shipments": pending_shipments,
            "pending_returns": pending_returns
        }
    }

# ========================= WAREHOUSES =========================

@router.post("/warehouses")
async def create_warehouse(warehouse: WarehouseCreate, request: Request = None,
                           _: None = Depends(require_feature("inventory_multi_warehouse"))):
    org_id = extract_org_id(request)
    """Create a new warehouse"""
    warehouse_id = generate_id("WH")
    
    if warehouse.is_primary:
        # Unset other primary warehouses
        await warehouses_collection.update_many({"is_primary": True}, {"$set": {"is_primary": False}})
    
    warehouse_doc = {
        "warehouse_id": warehouse_id,
        **warehouse.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await warehouses_collection.insert_one(warehouse_doc)
    warehouse_doc.pop("_id", None)
    return {"code": 0, "message": "Warehouse created", "warehouse": warehouse_doc}

@router.get("/warehouses")
async def list_warehouses(active_only: bool = True, request: Request = None,
                          _: None = Depends(require_feature("inventory_multi_warehouse"))):
    org_id = extract_org_id(request)
    """List all warehouses"""
    query = {"is_active": True} if active_only else {}
    warehouses = await warehouses_collection.find(query, {"_id": 0}).to_list(100)
    return {"code": 0, "warehouses": warehouses}

@router.get("/stock")
async def get_stock(warehouse_id: str = None, request: Request):
    org_id = extract_org_id(request)
    """Get stock items, optionally filtered by warehouse"""
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    pipeline = [
        {"$match": query},
        {"$lookup": {"from": "items_enhanced", "localField": "item_id", "foreignField": "item_id", "as": "item"}},
        {"$unwind": {"path": "$item", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "warehouse_id": 1,
            "item_name": "$item.name",
            "sku": "$item.sku",
            "available_stock": 1,
            "reserved_stock": 1,
            "unit": "$item.unit"
        }}
    ]
    stock_items = await stock_locations_collection.aggregate(pipeline).to_list(1000)
    
    return {"code": 0, "stock": stock_items}

@router.get("/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: str, request: Request = None,
                        _: None = Depends(require_feature("inventory_multi_warehouse"))):
    org_id = extract_org_id(request)
    """Get warehouse details with stock summary"""
    warehouse = await warehouses_collection.find_one({"warehouse_id": warehouse_id}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get stock in this warehouse
    pipeline = [
        {"$match": {"warehouse_id": warehouse_id}},
        {"$lookup": {"from": "items_enhanced", "localField": "item_id", "foreignField": "item_id", "as": "item"}},
        {"$unwind": {"path": "$item", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "item_name": "$item.name",
            "available_stock": 1,
            "reserved_stock": 1
        }}
    ]
    stock_items = await stock_locations_collection.aggregate(pipeline).to_list(500)
    
    warehouse["stock_items"] = stock_items
    warehouse["item_count"] = len(stock_items)
    warehouse["total_units"] = sum(s.get("available_stock", 0) for s in stock_items)
    
    return {"code": 0, "warehouse": warehouse}

@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(warehouse_id: str, update: dict, request: Request = None,
                           _: None = Depends(require_feature("inventory_multi_warehouse"))):
    org_id = extract_org_id(request)
    """Update warehouse"""
    if update.get("is_primary"):
        await warehouses_collection.update_many({"is_primary": True}, {"$set": {"is_primary": False}})
    
    await warehouses_collection.update_one({"warehouse_id": warehouse_id}, {"$set": update})
    warehouse = await warehouses_collection.find_one({"warehouse_id": warehouse_id}, {"_id": 0})
    return {"code": 0, "warehouse": warehouse}

# ========================= VARIANTS =========================

@router.post("/variants")
async def create_variant(variant: VariantCreate, request: Request):
    org_id = extract_org_id(request)
    """Create item variant (e.g., size/color combinations)"""
    # Verify base item exists
    item = await items_collection.find_one({"item_id": variant.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Base item not found")
    
    variant_id = generate_id("VAR")
    sku = variant.sku or f"{item.get('sku', '')}-{variant.variant_name.upper().replace(' ', '-')}"
    
    variant_doc = {
        "variant_id": variant_id,
        "item_id": variant.item_id,
        "item_name": item.get("name"),
        "variant_name": variant.variant_name,
        "sku": sku,
        "additional_rate": variant.additional_rate,
        "attributes": variant.attributes,
        "effective_rate": item.get("sales_rate", 0) + variant.additional_rate,
        "status": "active",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await variants_collection.insert_one(variant_doc)
    
    # Initialize stock if warehouse provided
    if variant.warehouse_id and variant.initial_stock > 0:
        await adjust_stock(
            variant.item_id, 
            variant.initial_stock, 
            variant.warehouse_id, 
            "Initial variant stock",
            variant_id=variant_id
        )
    
    await add_history("variant", variant_id, "created", f"Variant '{variant.variant_name}' created for item '{item.get('name')}'")
    
    variant_doc.pop("_id", None)
    return {"code": 0, "message": "Variant created", "variant": variant_doc}

@router.get("/variants")
async def list_variants(item_id: Optional[str] = None, request: Request):
    org_id = extract_org_id(request)
    """List item variants"""
    query = {}
    if item_id:
        query["item_id"] = item_id
    
    variants = await variants_collection.find(query, {"_id": 0}).to_list(500)
    
    # Add stock info
    for v in variants:
        stock = await get_item_stock(v["item_id"], variant_id=v["variant_id"])
        v["available_stock"] = stock
    
    return {"code": 0, "variants": variants}

@router.get("/variants/{variant_id}")
async def get_variant(variant_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get variant details"""
    variant = await variants_collection.find_one({"variant_id": variant_id}, {"_id": 0})
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    # Get stock by warehouse
    stock_locations = await stock_locations_collection.find(
        {"item_id": variant["item_id"], "variant_id": variant_id},
        {"_id": 0}
    ).to_list(50)
    
    variant["stock_locations"] = stock_locations
    variant["total_stock"] = sum(s.get("available_stock", 0) for s in stock_locations)
    
    return {"code": 0, "variant": variant}

@router.put("/variants/{variant_id}")
async def update_variant(variant_id: str, update: VariantUpdate, request: Request):
    org_id = extract_org_id(request)
    """Update variant"""
    update_dict = {k: v for k, v in update.dict().items() if v is not None}
    
    if update_dict:
        # Recalculate effective rate if additional_rate changed
        if "additional_rate" in update_dict:
            variant = await variants_collection.find_one({"variant_id": variant_id})
            if variant:
                item = await items_collection.find_one({"item_id": variant["item_id"]})
                if item:
                    update_dict["effective_rate"] = item.get("sales_rate", 0) + update_dict["additional_rate"]
        
        update_dict["updated_time"] = datetime.now(timezone.utc).isoformat()
        await variants_collection.update_one({"variant_id": variant_id}, {"$set": update_dict})
    
    variant = await variants_collection.find_one({"variant_id": variant_id}, {"_id": 0})
    return {"code": 0, "variant": variant}

@router.delete("/variants/{variant_id}")
async def delete_variant(variant_id: str, request: Request):
    org_id = extract_org_id(request)
    """Delete variant (soft delete)"""
    await variants_collection.update_one({"variant_id": variant_id}, {"$set": {"status": "inactive"}})
    return {"code": 0, "message": "Variant deleted"}

# ========================= BUNDLES =========================

@router.post("/bundles")
async def create_bundle(bundle: BundleCreate, request: Request):
    org_id = extract_org_id(request)
    """Create item bundle (composite/kit)"""
    bundle_id = generate_id("BDL")
    sku = bundle.sku or f"BDL-{bundle.name.upper().replace(' ', '-')[:20]}"
    
    # Validate and enrich components
    components = []
    calculated_rate = 0
    
    for comp in bundle.components:
        item = await items_collection.find_one({"item_id": comp.get("item_id")})
        if not item:
            raise HTTPException(status_code=400, detail=f"Component item {comp.get('item_id')} not found")
        
        # Handle sales_rate that might be string or number
        sales_rate = item.get("sales_rate", 0) or item.get("rate", 0)
        if isinstance(sales_rate, str):
            try:
                sales_rate = float(sales_rate) if sales_rate else 0
            except:
                sales_rate = 0
        
        component_data = {
            "component_id": generate_id("COMP"),
            "bundle_id": bundle_id,
            "item_id": comp["item_id"],
            "item_name": item.get("name"),
            "quantity": comp.get("quantity", 1),
            "unit_rate": sales_rate
        }
        components.append(component_data)
        calculated_rate += component_data["unit_rate"] * component_data["quantity"]
    
    final_rate = calculated_rate if bundle.auto_calculate_rate else bundle.rate
    
    bundle_doc = {
        "bundle_id": bundle_id,
        "name": bundle.name,
        "sku": sku,
        "description": bundle.description,
        "rate": final_rate,
        "auto_calculate_rate": bundle.auto_calculate_rate,
        "component_count": len(components),
        "status": "active",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await bundles_collection.insert_one(bundle_doc)
    
    for comp in components:
        await bundle_components_collection.insert_one(comp)
        comp.pop("_id", None)  # Remove MongoDB _id after insert
    
    await add_history("bundle", bundle_id, "created", f"Bundle '{bundle.name}' created with {len(components)} components")
    
    bundle_doc.pop("_id", None)
    bundle_doc["components"] = components
    return {"code": 0, "message": "Bundle created", "bundle": bundle_doc}

@router.get("/bundles")
async def list_bundles(status: str = "active", request: Request):
    org_id = extract_org_id(request)
    """List item bundles"""
    query = {"status": status} if status != "all" else {}
    bundles = await bundles_collection.find(query, {"_id": 0}).to_list(200)
    return {"code": 0, "bundles": bundles}

@router.get("/bundles/{bundle_id}")
async def get_bundle(bundle_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get bundle with components"""
    bundle = await bundles_collection.find_one({"bundle_id": bundle_id}, {"_id": 0})
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    components = await bundle_components_collection.find({"bundle_id": bundle_id}, {"_id": 0}).to_list(50)
    
    # Add stock availability for each component
    for comp in components:
        stock = await get_item_stock(comp["item_id"])
        comp["available_stock"] = stock
        comp["can_assemble"] = int(stock / comp["quantity"]) if comp["quantity"] > 0 else 0
    
    bundle["components"] = components
    bundle["max_assemblable"] = min(c.get("can_assemble", 0) for c in components) if components else 0
    
    return {"code": 0, "bundle": bundle}

@router.post("/bundles/{bundle_id}/assemble")
async def assemble_bundle(bundle_id: str, quantity: int = 1, warehouse_id: str = "", request: Request):
    org_id = extract_org_id(request)
    """Assemble bundle by consuming component stock"""
    bundle = await bundles_collection.find_one({"bundle_id": bundle_id})
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    if not warehouse_id:
        warehouse = await warehouses_collection.find_one({"is_primary": True})
        warehouse_id = warehouse["warehouse_id"] if warehouse else ""
    
    if not warehouse_id:
        raise HTTPException(status_code=400, detail="Warehouse required for assembly")
    
    components = await bundle_components_collection.find({"bundle_id": bundle_id}).to_list(50)
    
    # Check stock availability
    for comp in components:
        needed = comp["quantity"] * quantity
        available = await get_item_stock(comp["item_id"], warehouse_id)
        if available < needed:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {comp['item_name']}. Need {needed}, available {available}"
            )
    
    # Deduct component stock
    for comp in components:
        await adjust_stock(
            comp["item_id"],
            -(comp["quantity"] * quantity),
            warehouse_id,
            f"Assembled into bundle {bundle['name']}"
        )
    
    await add_history("bundle", bundle_id, "assembled", f"Assembled {quantity} units of bundle '{bundle['name']}'")
    
    return {"code": 0, "message": f"Successfully assembled {quantity} units of {bundle['name']}"}

# ========================= SERIAL/BATCH TRACKING =========================

@router.post("/serial-batches")
async def create_serial_batch(data: SerialBatchCreate, request: Request):
    org_id = extract_org_id(request)
    """Create serial number or batch"""
    # Check for duplicate
    existing = await serial_batches_collection.find_one({"number": data.number, "item_id": data.item_id})
    if existing:
        raise HTTPException(status_code=400, detail="Serial/batch number already exists for this item")
    
    serial_id = generate_id("SB")
    
    serial_doc = {
        "serial_batch_id": serial_id,
        "item_id": data.item_id,
        "tracking_type": data.tracking_type,
        "number": data.number,
        "warehouse_id": data.warehouse_id,
        "quantity": 1 if data.tracking_type == "serial" else data.quantity,
        "available_quantity": 1 if data.tracking_type == "serial" else data.quantity,
        "expiry_date": data.expiry_date,
        "status": "available",  # available, sold, returned, damaged
        "notes": data.notes,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await serial_batches_collection.insert_one(serial_doc)
    
    serial_doc.pop("_id", None)
    return {"code": 0, "message": f"{data.tracking_type.title()} created", "serial_batch": serial_doc}

@router.get("/serial-batches")
async def list_serial_batches(
    item_id: Optional[str] = None,
    tracking_type: Optional[str] = None,
    status: str = "available", request: Request):
    org_id = extract_org_id(request)
    """List serial numbers and batches"""
    query = {}
    if item_id:
        query["item_id"] = item_id
    if tracking_type:
        query["tracking_type"] = tracking_type
    if status != "all":
        query["status"] = status
    
    serials = await serial_batches_collection.find(query, {"_id": 0}).to_list(500)
    return {"code": 0, "serial_batches": serials}

@router.get("/serial-batches/{serial_batch_id}")
async def get_serial_batch(serial_batch_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get serial/batch details with history"""
    serial = await serial_batches_collection.find_one({"serial_batch_id": serial_batch_id}, {"_id": 0})
    if not serial:
        raise HTTPException(status_code=404, detail="Serial/batch not found")
    
    # Get item details
    item = await items_collection.find_one({"item_id": serial["item_id"]}, {"_id": 0, "name": 1, "sku": 1})
    serial["item_name"] = item.get("name") if item else "Unknown"
    serial["item_sku"] = item.get("sku") if item else ""
    
    return {"code": 0, "serial_batch": serial}

@router.put("/serial-batches/{serial_batch_id}/status")
async def update_serial_status(serial_batch_id: str, status: str, reason: str = "", request: Request):
    org_id = extract_org_id(request)
    """Update serial/batch status"""
    valid_statuses = ["available", "sold", "returned", "damaged", "expired"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    await serial_batches_collection.update_one(
        {"serial_batch_id": serial_batch_id},
        {"$set": {"status": status, "status_reason": reason, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": f"Status updated to {status}"}

# ========================= SHIPMENTS =========================

@router.post("/shipments")
async def create_shipment(shipment: ShipmentCreate, request: Request):
    org_id = extract_org_id(request)
    """Create shipment from sales order"""
    # Verify sales order
    so = await sales_orders_collection.find_one({"salesorder_id": shipment.sales_order_id})
    if not so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    if so.get("status") not in ["confirmed", "open"]:
        raise HTTPException(status_code=400, detail=f"Cannot ship order in {so.get('status')} status")
    
    shipment_id = generate_id("SHP")
    package_number = f"PKG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    # Process shipment items
    shipment_items = []
    warehouse_id = ""
    
    for item_data in shipment.items:
        # Get SO line item
        line_item = await so_line_items_collection.find_one({"line_item_id": item_data.get("line_item_id")})
        if not line_item:
            continue
        
        if not warehouse_id:
            warehouse = await warehouses_collection.find_one({"is_primary": True})
            warehouse_id = warehouse["warehouse_id"] if warehouse else ""
        
        # Deduct stock
        await adjust_stock(
            line_item["item_id"],
            -item_data.get("quantity", 0),
            warehouse_id,
            f"Shipped in {package_number}"
        )
        
        shipment_item = {
            "shipment_item_id": generate_id("SI"),
            "shipment_id": shipment_id,
            "line_item_id": item_data.get("line_item_id"),
            "item_id": line_item.get("item_id"),
            "item_name": line_item.get("name"),
            "quantity_shipped": item_data.get("quantity", 0),
            "serial_batch_id": item_data.get("serial_batch_id")
        }
        shipment_items.append(shipment_item)
        await shipment_items_collection.insert_one(shipment_item)
        
        # Update serial/batch if tracked
        if item_data.get("serial_batch_id"):
            await serial_batches_collection.update_one(
                {"serial_batch_id": item_data["serial_batch_id"]},
                {"$set": {"status": "sold"}}
            )
    
    shipment_doc = {
        "shipment_id": shipment_id,
        "sales_order_id": shipment.sales_order_id,
        "sales_order_number": so.get("salesorder_number"),
        "customer_id": so.get("customer_id"),
        "customer_name": so.get("customer_name"),
        "package_number": package_number,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
        "status": "packed",
        "shipped_date": None,
        "delivered_date": None,
        "item_count": len(shipment_items),
        "notes": shipment.notes,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await shipments_collection.insert_one(shipment_doc)
    
    # Check if SO fully shipped
    # This is simplified - a full implementation would track quantities
    
    await add_history("shipment", shipment_id, "created", f"Shipment {package_number} created for SO {so.get('salesorder_number')}")
    
    shipment_doc.pop("_id", None)
    shipment_doc["items"] = shipment_items
    return {"code": 0, "message": "Shipment created", "shipment": shipment_doc}

@router.get("/shipments")
async def list_shipments(
    sales_order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1, request: Request),
    limit:: int = Query(25, ge=1)
):
    """List shipments with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {}
    if sales_order_id:
        query["sales_order_id"] = sales_order_id
    if status:
        query["status"] = status

    total = await shipments_collection.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    shipments = await shipments_collection.find(query, {"_id": 0}).sort("created_time", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": shipments,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/shipments/{shipment_id}")
async def get_shipment(shipment_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get shipment details"""
    shipment = await shipments_collection.find_one({"shipment_id": shipment_id}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    items = await shipment_items_collection.find({"shipment_id": shipment_id}, {"_id": 0}).to_list(100)
    shipment["items"] = items
    
    return {"code": 0, "shipment": shipment}

@router.post("/shipments/{shipment_id}/ship")
async def mark_shipped(shipment_id: str, tracking_number: str = "", request: Request):
    org_id = extract_org_id(request)
    """Mark shipment as shipped"""
    shipment = await shipments_collection.find_one({"shipment_id": shipment_id})
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if shipment.get("status") != "packed":
        raise HTTPException(status_code=400, detail="Only packed shipments can be marked as shipped")
    
    update = {
        "status": "shipped",
        "shipped_date": datetime.now(timezone.utc).isoformat()
    }
    if tracking_number:
        update["tracking_number"] = tracking_number
    
    await shipments_collection.update_one({"shipment_id": shipment_id}, {"$set": update})
    
    # TODO: Send customer notification
    
    return {"code": 0, "message": "Shipment marked as shipped"}

@router.post("/shipments/{shipment_id}/deliver")
async def mark_delivered(shipment_id: str, request: Request):
    org_id = extract_org_id(request)
    """Mark shipment as delivered"""
    shipment = await shipments_collection.find_one({"shipment_id": shipment_id})
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if shipment.get("status") != "shipped":
        raise HTTPException(status_code=400, detail="Only shipped shipments can be marked as delivered")
    
    await shipments_collection.update_one(
        {"shipment_id": shipment_id},
        {"$set": {"status": "delivered", "delivered_date": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": "Shipment marked as delivered"}

# ========================= RETURNS =========================

@router.post("/returns")
async def create_return(ret: ReturnCreate, request: Request):
    org_id = extract_org_id(request)
    """Create return from shipment"""
    shipment = await shipments_collection.find_one({"shipment_id": ret.shipment_id})
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    if shipment.get("status") != "delivered":
        raise HTTPException(status_code=400, detail="Can only return delivered shipments")
    
    return_id = generate_id("RET")
    
    warehouse = await warehouses_collection.find_one({"is_primary": True})
    warehouse_id = warehouse["warehouse_id"] if warehouse else ""
    
    return_doc = {
        "return_id": return_id,
        "shipment_id": ret.shipment_id,
        "sales_order_id": shipment.get("sales_order_id"),
        "customer_id": shipment.get("customer_id"),
        "customer_name": shipment.get("customer_name"),
        "reason": ret.reason,
        "restock": ret.restock,
        "status": "pending",
        "return_date": datetime.now(timezone.utc).isoformat(),
        "notes": ret.notes,
        "credit_note_id": None,
        "restocked_value": 0,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Process returned items
    total_value = 0
    for item_data in ret.items:
        shipment_item = await shipment_items_collection.find_one({"shipment_item_id": item_data.get("shipment_item_id")})
        if not shipment_item:
            continue
        
        qty = item_data.get("quantity", shipment_item.get("quantity_shipped", 0))
        
        if ret.restock and warehouse_id:
            await adjust_stock(
                shipment_item["item_id"],
                qty,
                warehouse_id,
                f"Returned from shipment {shipment.get('package_number')}"
            )
        
        # Update serial/batch if tracked
        if shipment_item.get("serial_batch_id"):
            await serial_batches_collection.update_one(
                {"serial_batch_id": shipment_item["serial_batch_id"]},
                {"$set": {"status": "returned"}}
            )
        
        # Get item rate for credit calculation
        item = await items_collection.find_one({"item_id": shipment_item["item_id"]})
        item_rate = item.get("sales_rate", 0) if item else 0
        total_value += item_rate * qty
    
    return_doc["restocked_value"] = total_value
    
    await returns_collection.insert_one(return_doc)
    
    await add_history("return", return_id, "created", f"Return created for shipment {shipment.get('package_number')}. Restock: {ret.restock}")
    
    return_doc.pop("_id", None)
    return {"code": 0, "message": "Return created", "return": return_doc, "credit_value": total_value}

@router.get("/returns")
async def list_returns(
    status: Optional[str] = None,
    page: int = Query(1, ge=1, request: Request),
    limit:: int = Query(25, ge=1)
):
    """List returns with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {}
    if status:
        query["status"] = status

    total = await returns_collection.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    returns = await returns_collection.find(query, {"_id": 0}).sort("created_time", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": returns,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/returns/{return_id}")
async def get_return(return_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get return details"""
    ret = await returns_collection.find_one({"return_id": return_id}, {"_id": 0})
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")
    return {"code": 0, "return": ret}

@router.post("/returns/{return_id}/process")
async def process_return(return_id: str, create_credit_note: bool = True, request: Request):
    org_id = extract_org_id(request)
    """Process pending return"""
    ret = await returns_collection.find_one({"return_id": return_id})
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")
    
    if ret.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Return already processed")
    
    # TODO: Create credit note if requested
    
    await returns_collection.update_one(
        {"return_id": return_id},
        {"$set": {"status": "processed", "processed_date": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": "Return processed"}

# ========================= STOCK ADJUSTMENTS =========================

@router.post("/adjustments")
async def create_adjustment(adjustment: StockAdjustmentCreate, request: Request):
    org_id = extract_org_id(request)
    """Create stock adjustment"""
    item = await items_collection.find_one({"item_id": adjustment.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    adjustment_id = generate_id("ADJ")
    
    current_stock = await get_item_stock(adjustment.item_id, adjustment.warehouse_id, adjustment.variant_id)
    
    if adjustment.adjustment_type == "add":
        qty_change = adjustment.quantity
    elif adjustment.adjustment_type == "subtract":
        qty_change = -adjustment.quantity
    else:  # set
        qty_change = adjustment.quantity - current_stock
    
    new_stock = await adjust_stock(
        adjustment.item_id,
        qty_change,
        adjustment.warehouse_id,
        adjustment.reason,
        adjustment.variant_id
    )
    
    adj_doc = {
        "adjustment_id": adjustment_id,
        "item_id": adjustment.item_id,
        "item_name": item.get("name"),
        "variant_id": adjustment.variant_id,
        "warehouse_id": adjustment.warehouse_id,
        "adjustment_type": adjustment.adjustment_type,
        "quantity_adjusted": qty_change,
        "stock_before": current_stock,
        "stock_after": new_stock,
        "reason": adjustment.reason,
        "reference_number": adjustment.reference_number,
        "notes": adjustment.notes,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await adjustments_collection.insert_one(adj_doc)
    
    adj_doc.pop("_id", None)
    return {"code": 0, "message": "Adjustment recorded", "adjustment": adj_doc}

@router.get("/adjustments")
async def list_adjustments(
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    page: int = Query(1, ge=1, request: Request),
    limit:: int = Query(25, ge=1)
):
    """List stock adjustments with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {}
    if item_id:
        query["item_id"] = item_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id

    total = await adjustments_collection.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    adjustments = await adjustments_collection.find(query, {"_id": 0}).sort("created_time", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": adjustments,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

# ========================= REPORTS =========================

@router.get("/reports/stock-summary")
async def stock_summary_report(warehouse_id: Optional[str] = None, request: Request):
    org_id = extract_org_id(request)
    """Stock summary report"""
    match = {"status": "active"}
    
    pipeline = [
        {"$match": match},
        {"$lookup": {
            "from": "item_stock_locations",
            "let": {"item_id": "$item_id"},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$item_id", "$$item_id"]}}},
                *([{"$match": {"warehouse_id": warehouse_id}}] if warehouse_id else [])
            ],
            "as": "stock"
        }},
        {"$addFields": {
            "total_stock": {"$sum": "$stock.available_stock"},
            "total_reserved": {"$sum": "$stock.reserved_stock"},
            "purchase_rate_num": {
                "$cond": {
                    "if": {"$or": [
                        {"$eq": ["$purchase_rate", ""]},
                        {"$eq": ["$purchase_rate", None]},
                        {"$not": {"$isNumber": "$purchase_rate"}}
                    ]},
                    "then": 0,
                    "else": {"$toDouble": "$purchase_rate"}
                }
            },
            "reorder_level_num": {
                "$cond": {
                    "if": {"$or": [
                        {"$eq": ["$reorder_level", ""]},
                        {"$eq": ["$reorder_level", None]},
                        {"$not": {"$isNumber": "$reorder_level"}}
                    ]},
                    "then": 0,
                    "else": {"$toDouble": "$reorder_level"}
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "name": 1,
            "sku": 1,
            "purchase_rate": "$purchase_rate_num",
            "sales_rate": 1,
            "total_stock": 1,
            "total_reserved": 1,
            "reorder_level": "$reorder_level_num",
            "stock_value": {"$multiply": ["$total_stock", "$purchase_rate_num"]}
        }}
    ]
    
    items = await items_collection.aggregate(pipeline).to_list(1000)
    
    total_value = sum(i.get("stock_value", 0) for i in items)
    total_units = sum(i.get("total_stock", 0) for i in items)
    low_stock = [i for i in items if i.get("total_stock", 0) < i.get("reorder_level", 0)]
    
    return {
        "code": 0,
        "report": {
            "items": items,
            "summary": {
                "total_items": len(items),
                "total_units": round_qty(total_units),
                "total_value": round(total_value, 2),
                "low_stock_count": len(low_stock)
            }
        }
    }

@router.get("/reports/low-stock")
async def low_stock_report(request: Request):
    org_id = extract_org_id(request)
    """Low stock items report"""
    pipeline = [
        {"$match": {"status": "active", "track_inventory": True}},
        {"$lookup": {
            "from": "item_stock_locations",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "stock"
        }},
        {"$addFields": {
            "total_stock": {"$sum": "$stock.available_stock"},
            "reorder_level_num": {
                "$cond": {
                    "if": {"$or": [
                        {"$eq": ["$reorder_level", ""]},
                        {"$eq": ["$reorder_level", None]},
                        {"$not": {"$isNumber": "$reorder_level"}}
                    ]},
                    "then": 0,
                    "else": {"$toDouble": "$reorder_level"}
                }
            }
        }},
        {"$match": {"$expr": {"$and": [
            {"$gt": ["$reorder_level_num", 0]},
            {"$lt": ["$total_stock", "$reorder_level_num"]}
        ]}}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "name": 1,
            "sku": 1,
            "total_stock": 1,
            "reorder_level": "$reorder_level_num",
            "shortage": {"$subtract": ["$reorder_level_num", "$total_stock"]}
        }},
        {"$sort": {"shortage": -1}}
    ]
    
    items = await items_collection.aggregate(pipeline).to_list(200)
    
    return {"code": 0, "report": {"low_stock_items": items, "total": len(items)}}

@router.get("/reports/valuation")
async def inventory_valuation_report(request: Request):
    org_id = extract_org_id(request)
    """Inventory valuation report"""
    pipeline = [
        {"$match": {"status": "active"}},
        {"$lookup": {
            "from": "item_stock_locations",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "stock"
        }},
        {"$addFields": {"total_stock": {"$sum": "$stock.available_stock"}}},
        {"$group": {
            "_id": "$item_type",
            "item_count": {"$sum": 1},
            "total_units": {"$sum": "$total_stock"},
            "purchase_value": {"$sum": {"$multiply": ["$total_stock", {"$ifNull": ["$purchase_rate", 0]}]}},
            "sales_value": {"$sum": {"$multiply": ["$total_stock", {"$ifNull": ["$sales_rate", 0]}]}}
        }}
    ]
    
    by_type = await items_collection.aggregate(pipeline).to_list(10)
    
    totals = {
        "total_items": sum(t.get("item_count", 0) for t in by_type),
        "total_units": sum(t.get("total_units", 0) for t in by_type),
        "total_purchase_value": round(sum(t.get("purchase_value", 0) for t in by_type), 2),
        "total_sales_value": round(sum(t.get("sales_value", 0) for t in by_type), 2)
    }
    
    return {"code": 0, "report": {"by_type": by_type, "totals": totals}}

@router.get("/reports/movement")
async def stock_movement_report(
    item_id: Optional[str] = None,
    days: int = 30, request: Request):
    org_id = extract_org_id(request)
    """Stock movement/history report"""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    query = {"timestamp": {"$gte": since}}
    if item_id:
        query["item_id"] = item_id
    
    movements = await history_collection.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    # Aggregate by action
    by_action = {}
    for m in movements:
        action = m.get("action", "unknown")
        if action not in by_action:
            by_action[action] = {"count": 0, "quantity": 0}
        by_action[action]["count"] += 1
        by_action[action]["quantity"] += m.get("quantity_change", 0)
    
    return {"code": 0, "report": {"movements": movements, "by_action": by_action, "period_days": days}}


# ========================= STOCK TRANSFER BETWEEN WAREHOUSES =========================

class StockTransferCreate(BaseModel):
    from_warehouse_id: str
    to_warehouse_id: str
    items: List[Dict[str, Any]]  # [{"item_id": ..., "quantity": ..., "serial_batch_id": ...optional}]
    notes: str = ""
    reference_number: str = ""


@router.post("/stock-transfers")
async def create_stock_transfer(data: StockTransferCreate, request: Request):
    org_id = extract_org_id(request)
    """Transfer stock between two warehouses"""
    if data.from_warehouse_id == data.to_warehouse_id:
        raise HTTPException(status_code=400, detail="Source and destination warehouses must differ")

    from_wh = await warehouses_collection.find_one({"warehouse_id": data.from_warehouse_id}, {"_id": 0, "name": 1})
    to_wh = await warehouses_collection.find_one({"warehouse_id": data.to_warehouse_id}, {"_id": 0, "name": 1})
    if not from_wh:
        raise HTTPException(status_code=404, detail="Source warehouse not found")
    if not to_wh:
        raise HTTPException(status_code=404, detail="Destination warehouse not found")

    transfer_id = generate_id("TRF")
    now_iso = datetime.now(timezone.utc).isoformat()
    errors = []
    transferred_items = []

    for item_data in data.items:
        item_id = item_data.get("item_id")
        qty = float(item_data.get("quantity", 0))
        serial_batch_id = item_data.get("serial_batch_id")

        if not item_id or qty <= 0:
            continue

        # Check source stock
        from_stock = await get_item_stock(item_id, data.from_warehouse_id)
        if from_stock < qty:
            item = await items_collection.find_one({"item_id": item_id}, {"_id": 0, "name": 1})
            errors.append(f"Insufficient stock for {item.get('name', item_id)}: available {from_stock}, requested {qty}")
            continue

        # Deduct from source
        await adjust_stock(item_id, None, data.from_warehouse_id, "subtract", qty,
                           f"Transfer to {to_wh['name']} | Ref: {transfer_id}", "system")
        # Add to destination
        await adjust_stock(item_id, None, data.to_warehouse_id, "add", qty,
                           f"Transfer from {from_wh['name']} | Ref: {transfer_id}", "system")

        # Update serial/batch warehouse if provided
        if serial_batch_id:
            await serial_batches_collection.update_one(
                {"serial_batch_id": serial_batch_id},
                {"$set": {"warehouse_id": data.to_warehouse_id, "updated_at": now_iso}}
            )

        item_doc = await items_collection.find_one({"item_id": item_id}, {"_id": 0, "name": 1, "sku": 1})
        transferred_items.append({
            "item_id": item_id,
            "item_name": item_doc.get("name") if item_doc else item_id,
            "quantity": qty,
            "serial_batch_id": serial_batch_id
        })

    if not transferred_items and errors:
        raise HTTPException(status_code=400, detail=f"Transfer failed: {'; '.join(errors)}")

    # Record transfer
    transfer_doc = {
        "transfer_id": transfer_id,
        "from_warehouse_id": data.from_warehouse_id,
        "from_warehouse_name": from_wh["name"],
        "to_warehouse_id": data.to_warehouse_id,
        "to_warehouse_name": to_wh["name"],
        "items": transferred_items,
        "notes": data.notes,
        "reference_number": data.reference_number,
        "status": "completed",
        "created_at": now_iso,
        "errors": errors
    }
    await db["stock_transfers"].insert_one(transfer_doc)
    transfer_doc.pop("_id", None)

    return {"code": 0, "message": "Stock transfer completed", "transfer": transfer_doc, "warnings": errors}


@router.get("/stock-transfers")
async def list_stock_transfers(limit: int = 50, request: Request):
    org_id = extract_org_id(request)
    """List recent stock transfers"""
    transfers = await db["stock_transfers"].find(
        {}, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return {"code": 0, "transfers": transfers}


# ========================= REORDER SUGGESTIONS & AUTO-PO =========================

@router.get("/reorder-suggestions")
async def get_reorder_suggestions(request: Request):
    org_id = extract_org_id(request)
    """
    Get items below reorder point with suggested PO quantities.
    Returns grouped-by-supplier suggestions ready for PO creation.
    """
    pipeline = [
        {"$match": {"status": "active", "track_inventory": {"$ne": False}}},
        {"$lookup": {
            "from": "item_stock_locations",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "stock_locs"
        }},
        {"$addFields": {
            "total_stock": {"$sum": "$stock_locs.available_stock"},
            "reorder_lvl": {
                "$cond": {
                    "if": {"$or": [{"$eq": ["$reorder_level", ""]}, {"$eq": ["$reorder_level", None]},
                                   {"$not": {"$isNumber": "$reorder_level"}}]},
                    "then": 0,
                    "else": {"$toDouble": "$reorder_level"}
                }
            }
        }},
        {"$match": {"$expr": {"$and": [{"$gt": ["$reorder_lvl", 0]}, {"$lt": ["$total_stock", "$reorder_lvl"]}]}}},
        {"$project": {
            "_id": 0, "item_id": 1, "name": 1, "sku": 1,
            "total_stock": 1, "reorder_level": "$reorder_lvl",
            "unit_price": 1, "purchase_rate": 1,
            "preferred_vendor_id": 1, "preferred_vendor_name": 1,
            "reorder_quantity": 1,
        }},
        {"$sort": {"name": 1}}
    ]

    items = await items_collection.aggregate(pipeline).to_list(500)

    suggestions = []
    for item in items:
        shortage = max(0, float(item.get("reorder_level", 0)) - float(item.get("total_stock", 0)))
        suggested_qty = item.get("reorder_quantity") or max(int(shortage * 1.5), 1)
        unit_cost = float(item.get("purchase_rate") or item.get("unit_price") or 0)
        suggestions.append({
            "item_id": item["item_id"],
            "item_name": item["name"],
            "sku": item.get("sku", ""),
            "current_stock": round_qty(item["total_stock"]),
            "reorder_level": round_qty(item["reorder_level"]),
            "shortage": round_qty(shortage),
            "suggested_order_qty": suggested_qty,
            "unit_cost": unit_cost,
            "estimated_cost": round(suggested_qty * unit_cost, 2),
            "vendor_id": item.get("preferred_vendor_id"),
            "vendor_name": item.get("preferred_vendor_name", "No preferred vendor"),
        })

    # Group by vendor
    by_vendor = {}
    for s in suggestions:
        vendor_key = s.get("vendor_id") or "no_vendor"
        if vendor_key not in by_vendor:
            by_vendor[vendor_key] = {
                "vendor_id": s.get("vendor_id"),
                "vendor_name": s.get("vendor_name", "No preferred vendor"),
                "items": [],
                "total_estimated_cost": 0,
            }
        by_vendor[vendor_key]["items"].append(s)
        by_vendor[vendor_key]["total_estimated_cost"] += s["estimated_cost"]

    return {
        "code": 0,
        "total_items_below_reorder": len(suggestions),
        "suggestions": suggestions,
        "grouped_by_vendor": list(by_vendor.values()),
    }


@router.post("/reorder-suggestions/create-po")
async def create_po_from_suggestions(data: dict, request: Request):
    org_id = extract_org_id(request)
    """
    Create a purchase order from reorder suggestions.
    Body: {"vendor_id": "...", "items": [{"item_id": ..., "quantity": ..., "unit_cost": ...}]}
    Returns the created PO.
    """
    vendor_id = data.get("vendor_id")
    items = data.get("items", [])
    notes = data.get("notes", "Auto-generated from reorder suggestions")

    if not items:
        raise HTTPException(status_code=400, detail="No items provided")

    now_iso = datetime.now(timezone.utc).isoformat()
    po_id = generate_id("PO")

    # Resolve vendor name
    vendor_name = "Unknown Vendor"
    if vendor_id:
        vendor = await db["contacts_enhanced"].find_one(
            {"contact_id": vendor_id},
            {"_id": 0, "display_name": 1, "contact_name": 1}
        )
        if vendor:
            vendor_name = vendor.get("display_name") or vendor.get("contact_name", vendor_name)

    line_items = []
    subtotal = 0.0
    for item_data in items:
        item_id = item_data.get("item_id")
        qty = float(item_data.get("quantity", 0))
        unit_cost = float(item_data.get("unit_cost", 0))
        item = await items_collection.find_one({"item_id": item_id}, {"_id": 0, "name": 1, "sku": 1})
        if not item or qty <= 0:
            continue
        line_total = qty * unit_cost
        subtotal += line_total
        line_items.append({
            "item_id": item_id,
            "item_name": item.get("name", ""),
            "sku": item.get("sku", ""),
            "quantity": qty,
            "unit_cost": unit_cost,
            "line_total": round(line_total, 2)
        })

    po_doc = {
        "po_id": po_id,
        "po_number": f"PO-AUTO-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "vendor_id": vendor_id,
        "vendor_name": vendor_name,
        "status": "draft",
        "source": "reorder_suggestion",
        "line_items": line_items,
        "subtotal": round(subtotal, 2),
        "total": round(subtotal, 2),
        "notes": notes,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    await db["purchase_orders"].insert_one(po_doc)
    po_doc.pop("_id", None)

    return {"code": 0, "message": "Purchase order created", "purchase_order": po_doc}


# ========================= STOCKTAKE / INVENTORY COUNT =========================

class StocktakeCreate(BaseModel):
    warehouse_id: str
    name: str = ""
    notes: str = ""
    item_ids: List[str] = []  # Specific items to count; empty = all items in warehouse


class StocktakeCountUpdate(BaseModel):
    counted_quantity: float
    notes: str = ""


@router.post("/stocktakes")
async def create_stocktake(data: StocktakeCreate, request: Request):
    org_id = extract_org_id(request)
    """
    Create a new stocktake (inventory count session) for a warehouse.
    If item_ids is empty, includes ALL items in that warehouse.
    """
    wh = await warehouses_collection.find_one({"warehouse_id": data.warehouse_id}, {"_id": 0, "name": 1})
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    stocktake_id = generate_id("ST")
    now_iso = datetime.now(timezone.utc).isoformat()

    # Get items to count
    if data.item_ids:
        item_query = {"item_id": {"$in": data.item_ids}, "status": "active"}
    else:
        # All items in the warehouse (have stock_location records)
        locs = await stock_locations_collection.find(
            {"warehouse_id": data.warehouse_id},
            {"_id": 0, "item_id": 1}
        ).to_list(2000)
        item_ids_in_wh = list({loc["item_id"] for loc in locs})
        item_query = {"item_id": {"$in": item_ids_in_wh}, "status": "active"} if item_ids_in_wh else {"status": "active", "track_inventory": True}

    items = await items_collection.find(item_query, {"_id": 0, "item_id": 1, "name": 1, "sku": 1}).to_list(2000)

    # Build count lines with current system stock
    lines = []
    for item in items:
        system_qty = await get_item_stock(item["item_id"], data.warehouse_id)
        lines.append({
            "item_id": item["item_id"],
            "item_name": item["name"],
            "item_sku": item.get("sku", ""),
            "system_quantity": round_qty(system_qty),
            "counted_quantity": None,  # to be filled
            "variance": None,
            "notes": "",
            "counted": False,
        })

    stocktake_doc = {
        "stocktake_id": stocktake_id,
        "name": data.name or f"Stocktake {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        "warehouse_id": data.warehouse_id,
        "warehouse_name": wh["name"],
        "status": "in_progress",  # in_progress → finalized
        "lines": lines,
        "total_lines": len(lines),
        "counted_lines": 0,
        "total_variance": 0,
        "notes": data.notes,
        "created_at": now_iso,
        "updated_at": now_iso,
        "finalized_at": None,
    }

    await db["stocktakes"].insert_one(stocktake_doc)
    stocktake_doc.pop("_id", None)

    return {"code": 0, "message": "Stocktake created", "stocktake": stocktake_doc}


@router.get("/stocktakes")
async def list_stocktakes(status: Optional[str] = None, request: Request):
    org_id = extract_org_id(request)
    """List all stocktakes"""
    query = {}
    if status:
        query["status"] = status
    stocktakes = await db["stocktakes"].find(query, {
        "_id": 0, "stocktake_id": 1, "name": 1, "warehouse_name": 1,
        "status": 1, "total_lines": 1, "counted_lines": 1,
        "total_variance": 1, "created_at": 1, "finalized_at": 1
    }).sort("created_at", -1).to_list(100)
    return {"code": 0, "stocktakes": stocktakes}


@router.get("/stocktakes/{stocktake_id}")
async def get_stocktake(stocktake_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get stocktake details with all count lines"""
    st = await db["stocktakes"].find_one({"stocktake_id": stocktake_id}, {"_id": 0})
    if not st:
        raise HTTPException(status_code=404, detail="Stocktake not found")
    return {"code": 0, "stocktake": st}


@router.put("/stocktakes/{stocktake_id}/lines/{item_id}")
async def update_stocktake_line(stocktake_id: str, item_id: str, data: StocktakeCountUpdate, request: Request):
    org_id = extract_org_id(request)
    """Submit a count for a specific item in the stocktake"""
    st = await db["stocktakes"].find_one({"stocktake_id": stocktake_id}, {"_id": 0})
    if not st:
        raise HTTPException(status_code=404, detail="Stocktake not found")
    if st["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Stocktake is not in progress")

    lines = st.get("lines", [])
    line_idx = next((i for i, ln in enumerate(lines) if ln["item_id"] == item_id), None)
    if line_idx is None:
        raise HTTPException(status_code=404, detail="Item not in this stocktake")

    system_qty = float(lines[line_idx]["system_quantity"])
    counted_qty = float(data.counted_quantity)
    variance = round_qty(counted_qty - system_qty)

    lines[line_idx]["counted_quantity"] = counted_qty
    lines[line_idx]["variance"] = variance
    lines[line_idx]["notes"] = data.notes
    lines[line_idx]["counted"] = True

    counted_count = sum(1 for ln in lines if ln["counted"])
    total_variance = round_qty(sum(ln["variance"] or 0 for ln in lines if ln["counted"]))
    now_iso = datetime.now(timezone.utc).isoformat()

    await db["stocktakes"].update_one(
        {"stocktake_id": stocktake_id},
        {"$set": {
            "lines": lines,
            "counted_lines": counted_count,
            "total_variance": total_variance,
            "updated_at": now_iso,
        }}
    )
    return {"code": 0, "message": "Count updated", "variance": variance}


@router.post("/stocktakes/{stocktake_id}/finalize")
async def finalize_stocktake(stocktake_id: str, request: Request):
    org_id = extract_org_id(request)
    """
    Finalize stocktake: apply all variances as stock adjustments.
    Only lines with variance != 0 are adjusted.
    """
    st = await db["stocktakes"].find_one({"stocktake_id": stocktake_id}, {"_id": 0})
    if not st:
        raise HTTPException(status_code=404, detail="Stocktake not found")
    if st["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Stocktake already finalized or not in progress")

    counted_lines = [ln for ln in st.get("lines", []) if ln["counted"]]
    if not counted_lines:
        raise HTTPException(status_code=400, detail="No items have been counted yet")

    now_iso = datetime.now(timezone.utc).isoformat()
    adjustments_made = 0
    adjustment_ids = []

    for line in counted_lines:
        variance = float(line.get("variance") or 0)
        if abs(variance) < 0.0001:
            continue  # No change needed

        adj_type = "add" if variance > 0 else "subtract"
        qty = abs(variance)
        reason = f"Stocktake {st['name']} — variance of {variance:+.2f} for {line['item_name']}"
        await adjust_stock(line["item_id"], None, st["warehouse_id"], adj_type, qty, reason, "system")

        adj_id = generate_id("ADJ")
        adj_doc = {
            "adjustment_id": adj_id,
            "item_id": line["item_id"],
            "item_name": line["item_name"],
            "warehouse_id": st["warehouse_id"],
            "adjustment_type": adj_type,
            "quantity": qty,
            "reason": reason,
            "source": "stocktake",
            "stocktake_id": stocktake_id,
            "created_at": now_iso
        }
        await adjustments_collection.insert_one(adj_doc)
        adjustment_ids.append(adj_id)
        adjustments_made += 1

    await db["stocktakes"].update_one(
        {"stocktake_id": stocktake_id},
        {"$set": {
            "status": "finalized",
            "finalized_at": now_iso,
            "adjustments_applied": adjustments_made,
            "adjustment_ids": adjustment_ids,
        }}
    )

    return {
        "code": 0,
        "message": f"Stocktake finalized. {adjustments_made} stock adjustments applied.",
        "adjustments_made": adjustments_made,
    }

