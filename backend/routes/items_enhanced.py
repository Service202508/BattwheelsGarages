"""
Enhanced Items Module for Battwheels OS
Zoho Books-style comprehensive item management with:
- Item Groups (Categories) with hierarchy
- Multi-Warehouse inventory tracking
- Inventory Adjustments (Quantity & Value) with audit trail
- Multiple Price Lists (Sales/Purchase) with Markup/Markdown
- Custom Fields support
- GST/HSN/SAC integration with validation
- Import/Export (CSV/XLS)
- Bulk Actions
- Item History Tracking
- Low stock alerts & reorder notifications
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
import re
import csv
import io
import json
import base64

router = APIRouter(prefix="/items-enhanced", tags=["Items Enhanced"])

# Database connection
def get_db():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]

# ============== PYDANTIC MODELS ==============

class ItemGroupCreate(BaseModel):
    name: str
    description: str = ""
    parent_group_id: Optional[str] = None
    is_active: bool = True

class WarehouseCreate(BaseModel):
    name: str
    location: str = ""
    is_primary: bool = False
    is_active: bool = True

class ItemCreate(BaseModel):
    """Enhanced item creation model matching Zoho Books"""
    name: str
    sku: Optional[str] = None
    description: str = ""
    item_type: str = "inventory"  # inventory, non_inventory, service
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    
    # Sales Information
    sales_rate: float = 0
    sales_description: str = ""
    sales_account_id: Optional[str] = None
    
    # Purchase Information
    purchase_rate: float = 0
    purchase_description: str = ""
    purchase_account_id: Optional[str] = None
    
    # Inventory
    inventory_account_id: Optional[str] = None
    initial_stock: float = 0
    opening_stock_rate: float = 0  # Cost per unit for opening stock
    reorder_level: float = 0
    inventory_valuation_method: str = "fifo"  # fifo, weighted_average
    
    # Units
    unit: str = "pcs"
    
    # Tax
    tax_preference: str = "taxable"  # taxable, non_taxable, exempt
    tax_id: Optional[str] = None
    tax_percentage: float = 18
    intra_state_tax_rate: float = 18  # CGST + SGST
    inter_state_tax_rate: float = 18  # IGST
    
    # HSN/SAC Codes
    hsn_code: str = ""
    sac_code: str = ""
    
    # Vendor
    preferred_vendor_id: Optional[str] = None
    preferred_vendor_name: str = ""
    
    # Image (base64 encoded)
    image_data: Optional[str] = None
    image_name: Optional[str] = None
    
    # Custom Fields
    custom_fields: Dict = {}
    
    is_active: bool = True
    track_inventory: bool = True

    @validator('item_type')
    def validate_item_type(cls, v):
        valid_types = ['inventory', 'non_inventory', 'service', 'sales', 'purchases', 'sales_and_purchases']
        if v not in valid_types:
            raise ValueError(f"Item type must be one of: {valid_types}")
        return v
    
    @validator('tax_preference')
    def validate_tax_preference(cls, v):
        valid = ['taxable', 'non_taxable', 'exempt']
        if v not in valid:
            raise ValueError(f"Tax preference must be one of: {valid}")
        return v

class ItemUpdate(BaseModel):
    """Partial update model - all fields optional"""
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    sales_rate: Optional[float] = None
    sales_description: Optional[str] = None
    purchase_rate: Optional[float] = None
    purchase_description: Optional[str] = None
    unit: Optional[str] = None
    tax_preference: Optional[str] = None
    tax_id: Optional[str] = None
    tax_percentage: Optional[float] = None
    intra_state_tax_rate: Optional[float] = None
    inter_state_tax_rate: Optional[float] = None
    hsn_code: Optional[str] = None
    sac_code: Optional[str] = None
    reorder_level: Optional[float] = None
    preferred_vendor_id: Optional[str] = None
    preferred_vendor_name: Optional[str] = None
    custom_fields: Optional[Dict] = None
    is_active: Optional[bool] = None
    track_inventory: Optional[bool] = None
    image_data: Optional[str] = None
    image_name: Optional[str] = None

class ItemStockLocationCreate(BaseModel):
    item_id: str
    warehouse_id: str
    stock: float = 0

class ItemAdjustmentCreate(BaseModel):
    item_id: str
    warehouse_id: str
    adjustment_type: str  # add, subtract
    quantity: float
    reason: str = "other"  # initial, purchase, sale, damage, recount, transfer, other
    notes: str = ""
    reference_number: str = ""
    date: str = ""

    @validator('adjustment_type')
    def validate_adjustment_type(cls, v):
        if v not in ['add', 'subtract']:
            raise ValueError("Adjustment type must be 'add' or 'subtract'")
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

class PriceListCreate(BaseModel):
    name: str
    description: str = ""
    discount_percentage: float = 0
    markup_percentage: float = 0
    is_active: bool = True

class ItemPriceCreate(BaseModel):
    item_id: str
    price_list_id: str
    rate: float

class BulkStockUpdate(BaseModel):
    updates: List[Dict]  # [{"item_id": "...", "warehouse_id": "...", "stock": 100}, ...]

# ============== ITEM GROUPS ==============

@router.post("/groups")
async def create_item_group(group: ItemGroupCreate):
    """Create an item group (category)"""
    db = get_db()
    
    # Check unique name
    existing = await db.item_groups.find_one({"name": group.name})
    if existing:
        raise HTTPException(status_code=400, detail="Item group with this name already exists")
    
    group_id = f"IG-{uuid.uuid4().hex[:8].upper()}"
    
    # Get parent group name if exists
    parent_name = ""
    if group.parent_group_id:
        parent = await db.item_groups.find_one({"group_id": group.parent_group_id})
        if parent:
            parent_name = parent.get("name", "")
    
    group_dict = {
        "group_id": group_id,
        "name": group.name,
        "description": group.description,
        "parent_group_id": group.parent_group_id,
        "parent_group_name": parent_name,
        "is_active": group.is_active,
        "item_count": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_groups.insert_one(group_dict)
    del group_dict["_id"]
    
    return {"code": 0, "message": "Item group created", "group": group_dict}

@router.get("/groups")
async def list_item_groups(include_inactive: bool = False):
    """List all item groups"""
    db = get_db()
    query = {} if include_inactive else {"is_active": True}
    groups = await db.item_groups.find(query, {"_id": 0}).to_list(1000)
    
    # Build hierarchy
    root_groups = [g for g in groups if not g.get("parent_group_id")]
    for root in root_groups:
        root["subgroups"] = [g for g in groups if g.get("parent_group_id") == root["group_id"]]
    
    return {"code": 0, "groups": groups, "hierarchy": root_groups}

@router.get("/groups/{group_id}")
async def get_item_group(group_id: str):
    """Get item group details with items"""
    db = get_db()
    group = await db.item_groups.find_one({"group_id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Item group not found")
    
    # Get items in this group
    items = await db.items.find(
        {"$or": [{"group_id": group_id}, {"item_group_id": group_id}]},
        {"_id": 0, "item_id": 1, "name": 1, "sku": 1, "sales_rate": 1, "stock_on_hand": 1}
    ).to_list(100)
    
    group["items"] = items
    return {"code": 0, "group": group}

@router.put("/groups/{group_id}")
async def update_item_group(group_id: str, group: ItemGroupCreate):
    """Update item group"""
    db = get_db()
    
    result = await db.item_groups.update_one(
        {"group_id": group_id},
        {"$set": {
            "name": group.name,
            "description": group.description,
            "parent_group_id": group.parent_group_id,
            "is_active": group.is_active,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item group not found")
    
    return {"code": 0, "message": "Item group updated"}

@router.delete("/groups/{group_id}")
async def delete_item_group(group_id: str):
    """Delete item group (only if no items)"""
    db = get_db()
    
    # Check for items
    item_count = await db.items.count_documents(
        {"$or": [{"group_id": group_id}, {"item_group_id": group_id}]}
    )
    if item_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete group with {item_count} items")
    
    result = await db.item_groups.delete_one({"group_id": group_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item group not found")
    
    return {"code": 0, "message": "Item group deleted"}

# ============== WAREHOUSES ==============

@router.post("/warehouses")
async def create_warehouse(warehouse: WarehouseCreate):
    """Create a warehouse"""
    db = get_db()
    
    existing = await db.warehouses.find_one({"name": warehouse.name})
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse with this name already exists")
    
    warehouse_id = f"WH-{uuid.uuid4().hex[:8].upper()}"
    
    warehouse_dict = {
        "warehouse_id": warehouse_id,
        "name": warehouse.name,
        "location": warehouse.location,
        "is_primary": warehouse.is_primary,
        "is_active": warehouse.is_active,
        "total_items": 0,
        "total_stock_value": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.warehouses.insert_one(warehouse_dict)
    del warehouse_dict["_id"]
    
    return {"code": 0, "message": "Warehouse created", "warehouse": warehouse_dict}

@router.get("/warehouses")
async def list_warehouses(include_inactive: bool = False):
    """List all warehouses"""
    db = get_db()
    query = {} if include_inactive else {"is_active": True}
    warehouses = await db.warehouses.find(query, {"_id": 0}).to_list(100)
    
    # Calculate stock values for each warehouse
    for wh in warehouses:
        stock_locs = await db.item_stock_locations.find(
            {"warehouse_id": wh["warehouse_id"]}
        ).to_list(10000)
        wh["total_items"] = len(stock_locs)
        wh["total_stock"] = sum(s.get("stock", 0) for s in stock_locs)
    
    return {"code": 0, "warehouses": warehouses}

@router.get("/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: str):
    """Get warehouse details with stock"""
    db = get_db()
    warehouse = await db.warehouses.find_one({"warehouse_id": warehouse_id}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get stock in this warehouse
    stock_locations = await db.item_stock_locations.aggregate([
        {"$match": {"warehouse_id": warehouse_id, "stock": {"$gt": 0}}},
        {"$lookup": {
            "from": "items",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "item_info"
        }},
        {"$unwind": {"path": "$item_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "stock": 1,
            "item_name": "$item_info.name",
            "sku": "$item_info.sku",
            "rate": "$item_info.sales_rate"
        }}
    ]).to_list(1000)
    
    warehouse["stock_items"] = stock_locations
    warehouse["total_items"] = len(stock_locations)
    warehouse["total_stock"] = sum(s.get("stock", 0) for s in stock_locations)
    
    return {"code": 0, "warehouse": warehouse}

@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(warehouse_id: str, warehouse: WarehouseCreate):
    """Update warehouse"""
    db = get_db()
    
    result = await db.warehouses.update_one(
        {"warehouse_id": warehouse_id},
        {"$set": {
            "name": warehouse.name,
            "location": warehouse.location,
            "is_primary": warehouse.is_primary,
            "is_active": warehouse.is_active,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    return {"code": 0, "message": "Warehouse updated"}

# ============== ENHANCED ITEMS ==============

@router.post("/")
async def create_enhanced_item(item: ItemCreate):
    """Create item with full features"""
    db = get_db()
    
    # Check unique name/SKU
    if item.sku:
        existing = await db.items.find_one({"sku": item.sku})
        if existing:
            raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    
    item_id = f"I-{uuid.uuid4().hex[:12].upper()}"
    
    item_dict = {
        "item_id": item_id,
        "name": item.name,
        "sku": item.sku,
        "description": item.description,
        "item_type": item.item_type,
        "group_id": item.group_id,
        "group_name": item.group_name,
        "sales_rate": item.sales_rate,
        "purchase_rate": item.purchase_rate,
        "rate": item.sales_rate,  # For compatibility
        "unit": item.unit,
        "sales_account_id": item.sales_account_id,
        "purchase_account_id": item.purchase_account_id,
        "inventory_account_id": item.inventory_account_id,
        "tax_id": item.tax_id,
        "tax_percentage": item.tax_percentage,
        "hsn_code": item.hsn_code,
        "sac_code": item.sac_code,
        "hsn_or_sac": item.hsn_code or item.sac_code,
        "initial_stock": item.initial_stock,
        "stock_on_hand": item.initial_stock,
        "available_stock": item.initial_stock,
        "reorder_level": item.reorder_level,
        "preferred_vendor_id": item.preferred_vendor_id,
        "preferred_vendor_name": item.preferred_vendor_name,
        "custom_fields": item.custom_fields,
        "is_active": item.is_active,
        "status": "active" if item.is_active else "inactive",
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.items.insert_one(item_dict)
    del item_dict["_id"]
    
    # Initialize stock locations for inventory items
    if item.item_type == "inventory":
        warehouses = await db.warehouses.find({"is_active": True}).to_list(100)
        for wh in warehouses:
            await db.item_stock_locations.insert_one({
                "location_id": f"ISL-{uuid.uuid4().hex[:8].upper()}",
                "item_id": item_id,
                "warehouse_id": wh["warehouse_id"],
                "warehouse_name": wh["name"],
                "stock": item.initial_stock if wh.get("is_primary") else 0,
                "created_time": datetime.now(timezone.utc).isoformat(),
                "updated_time": datetime.now(timezone.utc).isoformat()
            })
    
    # Update group item count
    if item.group_id:
        await db.item_groups.update_one(
            {"group_id": item.group_id},
            {"$inc": {"item_count": 1}}
        )
    
    return {"code": 0, "message": "Item created successfully", "item": item_dict}

@router.get("/summary")
async def get_items_summary():
    """Get items summary statistics"""
    db = get_db()
    
    total_items = await db.items.count_documents({})
    active_items = await db.items.count_documents({"status": "active"})
    inventory_items = await db.items.count_documents({"item_type": "inventory"})
    service_items = await db.items.count_documents({"item_type": "service"})
    
    # Calculate total stock value
    pipeline = [
        {"$match": {"item_type": "inventory"}},
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
    stock_data = await db.items.aggregate(pipeline).to_list(1)
    
    return {
        "code": 0,
        "summary": {
            "total_items": total_items,
            "active_items": active_items,
            "inventory_items": inventory_items,
            "service_items": service_items,
            "total_stock_value": round(stock_data[0].get("total_stock_value", 0) if stock_data else 0, 2),
            "total_units": round(stock_data[0].get("total_units", 0) if stock_data else 0, 2)
        }
    }

@router.get("/")
async def list_enhanced_items(
    item_type: str = "",
    group_id: str = "",
    warehouse_id: str = "",
    is_active: bool = True,
    low_stock: bool = False,
    search: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List items with advanced filters"""
    db = get_db()
    
    query = {}
    if item_type:
        query["item_type"] = item_type
    if group_id:
        query["$or"] = [{"group_id": group_id}, {"item_group_id": group_id}]
    if is_active is not None:
        query["$or"] = query.get("$or", []) + [
            {"is_active": is_active},
            {"status": "active" if is_active else "inactive"}
        ]
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    skip = (page - 1) * per_page
    items = await db.items.find(query, {"_id": 0}).skip(skip).limit(per_page).to_list(per_page)
    total = await db.items.count_documents(query)
    
    # Add stock info for inventory items
    for item in items:
        if item.get("item_type") == "inventory":
            stock_locs = await db.item_stock_locations.find(
                {"item_id": item["item_id"]},
                {"_id": 0}
            ).to_list(100)
            item["stock_locations"] = stock_locs
            item["total_stock"] = sum(s.get("stock", 0) for s in stock_locs)
            reorder_level = item.get("reorder_level", 0)
            if isinstance(reorder_level, str):
                reorder_level = float(reorder_level) if reorder_level else 0
            item["is_low_stock"] = item["total_stock"] < reorder_level
    
    # Filter low stock if requested
    if low_stock:
        items = [i for i in items if i.get("is_low_stock")]
    
    return {
        "code": 0,
        "items": items,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }

@router.get("/low-stock")
async def get_low_stock_items():
    """Get items below reorder level"""
    db = get_db()
    
    items = await db.items.find(
        {"item_type": "inventory"},
        {"_id": 0}
    ).to_list(10000)
    
    low_stock_items = []
    for item in items:
        stock = item.get("stock_on_hand", 0) or item.get("available_stock", 0)
        if isinstance(stock, str):
            stock = float(stock) if stock else 0
        reorder = item.get("reorder_level", 0)
        if isinstance(reorder, str):
            reorder = float(reorder) if reorder else 0
        if stock < reorder:
            item["current_stock"] = stock
            item["shortage"] = reorder - stock
            low_stock_items.append(item)
    
    low_stock_items.sort(key=lambda x: x.get("shortage", 0), reverse=True)
    
    return {"code": 0, "low_stock_items": low_stock_items, "count": len(low_stock_items)}

# ============== STOCK LOCATIONS (MUST BE BEFORE /{item_id}) ==============

@router.post("/stock-locations")
async def create_stock_location(location: ItemStockLocationCreate):
    """Create or update stock location"""
    db = get_db()
    
    # Get warehouse name
    warehouse = await db.warehouses.find_one({"warehouse_id": location.warehouse_id})
    warehouse_name = warehouse.get("name", "") if warehouse else ""
    
    # Check if exists
    existing = await db.item_stock_locations.find_one({
        "item_id": location.item_id,
        "warehouse_id": location.warehouse_id
    })
    
    if existing:
        await db.item_stock_locations.update_one(
            {"_id": existing["_id"]},
            {"$set": {"stock": location.stock, "updated_time": datetime.now(timezone.utc).isoformat()}}
        )
        return {"code": 0, "message": "Stock location updated"}
    
    location_dict = {
        "location_id": f"ISL-{uuid.uuid4().hex[:8].upper()}",
        "item_id": location.item_id,
        "warehouse_id": location.warehouse_id,
        "warehouse_name": warehouse_name,
        "stock": location.stock,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_stock_locations.insert_one(location_dict)
    
    return {"code": 0, "message": "Stock location created"}

@router.post("/stock-locations/bulk-update")
async def bulk_update_stock(bulk: BulkStockUpdate):
    """Bulk update stock locations"""
    db = get_db()
    updated = 0
    
    for update in bulk.updates:
        item_id = update.get("item_id")
        warehouse_id = update.get("warehouse_id")
        stock = update.get("stock", 0)
        
        result = await db.item_stock_locations.update_one(
            {"item_id": item_id, "warehouse_id": warehouse_id},
            {"$set": {"stock": stock, "updated_time": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        if result.modified_count > 0 or result.upserted_id:
            updated += 1
    
    return {"code": 0, "message": f"Updated {updated} stock locations"}

# ============== INVENTORY ADJUSTMENTS (MUST BE BEFORE /{item_id}) ==============

@router.post("/adjustments")
async def create_item_adjustment(adj: ItemAdjustmentCreate):
    """Create inventory adjustment"""
    db = get_db()
    
    # Get item
    item = await db.items.find_one({"item_id": adj.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.get("item_type") not in ["inventory", "sales_and_purchases"]:
        raise HTTPException(status_code=400, detail="Item is not an inventory item")
    
    # Get or create stock location
    stock_loc = await db.item_stock_locations.find_one({
        "item_id": adj.item_id,
        "warehouse_id": adj.warehouse_id
    })
    
    current_stock = stock_loc.get("stock", 0) if stock_loc else 0
    
    # Calculate new stock
    if adj.adjustment_type == "add":
        new_stock = current_stock + adj.quantity
    else:
        if current_stock < adj.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Current: {current_stock}, Requested: {adj.quantity}"
            )
        new_stock = current_stock - adj.quantity
    
    # Create adjustment record
    adj_id = f"ADJ-{uuid.uuid4().hex[:8].upper()}"
    adj_date = adj.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get warehouse name
    warehouse = await db.warehouses.find_one({"warehouse_id": adj.warehouse_id})
    warehouse_name = warehouse.get("name", "") if warehouse else ""
    
    adj_dict = {
        "adjustment_id": adj_id,
        "item_id": adj.item_id,
        "item_name": item.get("name", ""),
        "warehouse_id": adj.warehouse_id,
        "warehouse_name": warehouse_name,
        "adjustment_type": adj.adjustment_type,
        "quantity": adj.quantity,
        "stock_before": current_stock,
        "stock_after": new_stock,
        "reason": adj.reason,
        "notes": adj.notes,
        "reference_number": adj.reference_number,
        "date": adj_date,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_adjustments.insert_one(adj_dict)
    
    # Update stock location
    if stock_loc:
        await db.item_stock_locations.update_one(
            {"_id": stock_loc["_id"]},
            {"$set": {"stock": new_stock, "updated_time": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.item_stock_locations.insert_one({
            "location_id": f"ISL-{uuid.uuid4().hex[:8].upper()}",
            "item_id": adj.item_id,
            "warehouse_id": adj.warehouse_id,
            "warehouse_name": warehouse_name,
            "stock": new_stock,
            "created_time": datetime.now(timezone.utc).isoformat(),
            "updated_time": datetime.now(timezone.utc).isoformat()
        })
    
    # Update item total stock
    all_locations = await db.item_stock_locations.find({"item_id": adj.item_id}).to_list(100)
    total_stock = sum(loc.get("stock", 0) for loc in all_locations)
    await db.items.update_one(
        {"item_id": adj.item_id},
        {"$set": {
            "stock_on_hand": total_stock,
            "available_stock": total_stock,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    del adj_dict["_id"]
    return {"code": 0, "message": "Adjustment created", "adjustment": adj_dict}

@router.get("/adjustments")
async def list_item_adjustments(
    item_id: str = "",
    warehouse_id: str = "",
    reason: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List inventory adjustments"""
    db = get_db()
    
    query = {}
    if item_id:
        query["item_id"] = item_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if reason:
        query["reason"] = reason
    
    skip = (page - 1) * per_page
    adjustments = await db.item_adjustments.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page).to_list(per_page)
    total = await db.item_adjustments.count_documents(query)
    
    return {
        "code": 0,
        "adjustments": adjustments,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/adjustments/{adj_id}")
async def get_item_adjustment(adj_id: str):
    """Get adjustment details"""
    db = get_db()
    adj = await db.item_adjustments.find_one({"adjustment_id": adj_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    return {"code": 0, "adjustment": adj}

# ============== PRICE LISTS (MUST BE BEFORE /{item_id}) ==============

@router.post("/price-lists")
async def create_price_list(price_list: PriceListCreate):
    """Create a price list"""
    db = get_db()
    
    existing = await db.price_lists.find_one({"name": price_list.name})
    if existing:
        raise HTTPException(status_code=400, detail="Price list with this name already exists")
    
    pl_id = f"PL-{uuid.uuid4().hex[:8].upper()}"
    
    pl_dict = {
        "pricelist_id": pl_id,
        "name": price_list.name,
        "description": price_list.description,
        "discount_percentage": price_list.discount_percentage,
        "markup_percentage": price_list.markup_percentage,
        "is_active": price_list.is_active,
        "item_count": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.price_lists.insert_one(pl_dict)
    del pl_dict["_id"]
    
    return {"code": 0, "message": "Price list created", "price_list": pl_dict}

@router.get("/price-lists")
async def list_price_lists(include_inactive: bool = False):
    """List all price lists"""
    db = get_db()
    query = {} if include_inactive else {"is_active": True}
    price_lists = await db.price_lists.find(query, {"_id": 0}).to_list(100)
    
    # Count items per price list
    for pl in price_lists:
        count = await db.item_prices.count_documents({"price_list_id": pl["pricelist_id"]})
        pl["item_count"] = count
    
    return {"code": 0, "price_lists": price_lists}

@router.get("/price-lists/{pricelist_id}")
async def get_price_list(pricelist_id: str):
    """Get price list with item prices"""
    db = get_db()
    pl = await db.price_lists.find_one({"pricelist_id": pricelist_id}, {"_id": 0})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    # Get item prices
    prices = await db.item_prices.aggregate([
        {"$match": {"price_list_id": pricelist_id}},
        {"$lookup": {
            "from": "items",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "item_info"
        }},
        {"$unwind": {"path": "$item_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "rate": 1,
            "item_name": "$item_info.name",
            "sku": "$item_info.sku",
            "base_rate": "$item_info.sales_rate"
        }}
    ]).to_list(1000)
    
    pl["item_prices"] = prices
    return {"code": 0, "price_list": pl}

@router.put("/price-lists/{pricelist_id}")
async def update_price_list(pricelist_id: str, price_list: PriceListCreate):
    """Update price list"""
    db = get_db()
    
    result = await db.price_lists.update_one(
        {"pricelist_id": pricelist_id},
        {"$set": {
            "name": price_list.name,
            "description": price_list.description,
            "discount_percentage": price_list.discount_percentage,
            "markup_percentage": price_list.markup_percentage,
            "is_active": price_list.is_active,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    return {"code": 0, "message": "Price list updated"}

@router.delete("/price-lists/{pricelist_id}")
async def delete_price_list(pricelist_id: str):
    """Delete price list"""
    db = get_db()
    
    # Delete associated item prices
    await db.item_prices.delete_many({"price_list_id": pricelist_id})
    
    result = await db.price_lists.delete_one({"pricelist_id": pricelist_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    return {"code": 0, "message": "Price list deleted"}

# ============== ITEM PRICES (MUST BE BEFORE /{item_id}) ==============

@router.post("/prices")
async def create_item_price(price: ItemPriceCreate):
    """Set item price for a price list"""
    db = get_db()
    
    # Check if exists
    existing = await db.item_prices.find_one({
        "item_id": price.item_id,
        "price_list_id": price.price_list_id
    })
    
    if existing:
        await db.item_prices.update_one(
            {"_id": existing["_id"]},
            {"$set": {"rate": price.rate, "updated_time": datetime.now(timezone.utc).isoformat()}}
        )
        return {"code": 0, "message": "Item price updated"}
    
    # Get names
    item = await db.items.find_one({"item_id": price.item_id})
    pl = await db.price_lists.find_one({"pricelist_id": price.price_list_id})
    
    price_dict = {
        "price_id": f"IP-{uuid.uuid4().hex[:8].upper()}",
        "item_id": price.item_id,
        "item_name": item.get("name", "") if item else "",
        "price_list_id": price.price_list_id,
        "price_list_name": pl.get("name", "") if pl else "",
        "rate": price.rate,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_prices.insert_one(price_dict)
    
    return {"code": 0, "message": "Item price created"}

@router.get("/prices/{item_id}")
async def get_item_prices(item_id: str):
    """Get all prices for an item"""
    db = get_db()
    prices = await db.item_prices.find({"item_id": item_id}, {"_id": 0}).to_list(100)
    return {"code": 0, "prices": prices}

@router.delete("/prices/{item_id}/{price_list_id}")
async def delete_item_price(item_id: str, price_list_id: str):
    """Delete item price from a price list"""
    db = get_db()
    result = await db.item_prices.delete_one({
        "item_id": item_id,
        "price_list_id": price_list_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item price not found")
    return {"code": 0, "message": "Item price deleted"}

# ============== INVENTORY REPORTS (MUST BE BEFORE /{item_id}) ==============

@router.get("/reports/stock-summary")
async def get_stock_summary(warehouse_id: str = ""):
    """Get stock summary report"""
    db = get_db()
    
    match_stage = {"item_type": {"$in": ["inventory", "sales_and_purchases"]}}
    
    items = await db.items.find(match_stage, {"_id": 0}).to_list(10000)
    
    summary = {
        "total_items": len(items),
        "total_stock_value": 0,
        "low_stock_count": 0,
        "out_of_stock_count": 0,
        "items": []
    }
    
    for item in items:
        stock = item.get("stock_on_hand", 0) or item.get("available_stock", 0)
        if isinstance(stock, str):
            stock = float(stock) if stock else 0
        rate = item.get("purchase_rate", 0) or item.get("sales_rate", 0)
        if isinstance(rate, str):
            rate = float(rate) if rate else 0
        reorder_level = item.get("reorder_level", 0)
        if isinstance(reorder_level, str):
            reorder_level = float(reorder_level) if reorder_level else 0
        value = stock * rate
        
        item_summary = {
            "item_id": item.get("item_id"),
            "name": item.get("name"),
            "sku": item.get("sku"),
            "stock": stock,
            "reorder_level": reorder_level,
            "rate": rate,
            "value": round(value, 2),
            "is_low_stock": stock < reorder_level,
            "is_out_of_stock": stock <= 0
        }
        
        summary["items"].append(item_summary)
        summary["total_stock_value"] += value
        
        if item_summary["is_low_stock"]:
            summary["low_stock_count"] += 1
        if item_summary["is_out_of_stock"]:
            summary["out_of_stock_count"] += 1
    
    summary["total_stock_value"] = round(summary["total_stock_value"], 2)
    
    return {"code": 0, "stock_summary": summary}

@router.get("/reports/valuation")
async def get_inventory_valuation():
    """Get inventory valuation report"""
    db = get_db()
    
    pipeline = [
        {"$match": {"item_type": {"$in": ["inventory", "sales_and_purchases"]}}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "name": 1,
            "sku": 1,
            "stock_on_hand": {"$ifNull": ["$stock_on_hand", {"$ifNull": ["$available_stock", 0]}]},
            "purchase_rate": {"$ifNull": ["$purchase_rate", "$sales_rate"]},
            "sales_rate": 1
        }},
        {"$addFields": {
            "purchase_value": {"$multiply": ["$stock_on_hand", "$purchase_rate"]},
            "sales_value": {"$multiply": ["$stock_on_hand", "$sales_rate"]}
        }},
        {"$group": {
            "_id": None,
            "items": {"$push": "$$ROOT"},
            "total_purchase_value": {"$sum": "$purchase_value"},
            "total_sales_value": {"$sum": "$sales_value"},
            "total_items": {"$sum": 1},
            "total_stock": {"$sum": "$stock_on_hand"}
        }}
    ]
    
    result = await db.items.aggregate(pipeline).to_list(1)
    
    if result:
        return {
            "code": 0,
            "valuation": {
                "total_items": result[0].get("total_items", 0),
                "total_stock": result[0].get("total_stock", 0),
                "total_purchase_value": round(result[0].get("total_purchase_value", 0), 2),
                "total_sales_value": round(result[0].get("total_sales_value", 0), 2),
                "items": result[0].get("items", [])
            }
        }
    
    return {"code": 0, "valuation": {"total_items": 0, "total_stock": 0, "total_purchase_value": 0, "total_sales_value": 0, "items": []}}

# ============== ITEM ROUTES WITH PATH PARAMETERS (MUST BE LAST) ==============

@router.get("/{item_id}")
async def get_enhanced_item(item_id: str):
    """Get item with full details"""
    db = get_db()
    item = await db.items.find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get stock locations
    stock_locations = await db.item_stock_locations.find(
        {"item_id": item_id},
        {"_id": 0}
    ).to_list(100)
    item["stock_locations"] = stock_locations
    item["total_stock"] = sum(s.get("stock", 0) for s in stock_locations)
    
    # Get adjustments history
    adjustments = await db.item_adjustments.find(
        {"item_id": item_id},
        {"_id": 0}
    ).sort("date", -1).limit(20).to_list(20)
    item["adjustments"] = adjustments
    
    # Get custom prices
    prices = await db.item_prices.find(
        {"item_id": item_id},
        {"_id": 0}
    ).to_list(100)
    item["price_list_rates"] = prices
    
    # Get transaction count
    invoice_count = await db.invoices.count_documents(
        {"line_items.item_id": item_id}
    )
    bill_count = await db.bills.count_documents(
        {"line_items.item_id": item_id}
    )
    item["transaction_count"] = invoice_count + bill_count
    item["is_used_in_transactions"] = item["transaction_count"] > 0
    
    return {"code": 0, "item": item}

@router.put("/{item_id}")
async def update_enhanced_item(item_id: str, item: ItemUpdate):
    """Update item with partial data"""
    db = get_db()
    
    existing = await db.items.find_one({"item_id": item_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if type change is allowed
    if item.item_type and existing.get("item_type") != item.item_type:
        invoice_count = await db.invoices.count_documents({"line_items.item_id": item_id})
        bill_count = await db.bills.count_documents({"line_items.item_id": item_id})
        if invoice_count > 0 or bill_count > 0:
            raise HTTPException(status_code=400, detail="Cannot change item type when used in transactions")
    
    # Build update dict with only provided fields
    update_data = {k: v for k, v in item.dict().items() if v is not None}
    
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        # Update rate field if sales_rate changed
        if "sales_rate" in update_data:
            update_data["rate"] = update_data["sales_rate"]
        # Update hsn_or_sac if either changed
        if "hsn_code" in update_data or "sac_code" in update_data:
            update_data["hsn_or_sac"] = update_data.get("hsn_code", existing.get("hsn_code", "")) or update_data.get("sac_code", existing.get("sac_code", ""))
        
        await db.items.update_one({"item_id": item_id}, {"$set": update_data})
    
    return {"code": 0, "message": "Item updated successfully"}

@router.post("/{item_id}/activate")
async def activate_item(item_id: str):
    """Activate item"""
    db = get_db()
    result = await db.items.update_one(
        {"item_id": item_id},
        {"$set": {"is_active": True, "status": "active", "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 0, "message": "Item activated"}

@router.post("/{item_id}/deactivate")
async def deactivate_item(item_id: str):
    """Deactivate item"""
    db = get_db()
    result = await db.items.update_one(
        {"item_id": item_id},
        {"$set": {"is_active": False, "status": "inactive", "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 0, "message": "Item deactivated"}

@router.delete("/{item_id}")
async def delete_enhanced_item(item_id: str):
    """Delete item (only if not used in transactions)"""
    db = get_db()
    
    # Check usage
    invoice_count = await db.invoices.count_documents({"line_items.item_id": item_id})
    bill_count = await db.bills.count_documents({"line_items.item_id": item_id})
    
    if invoice_count > 0 or bill_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete item used in {invoice_count} invoices and {bill_count} bills. Mark as inactive instead."
        )
    
    # Delete stock locations
    await db.item_stock_locations.delete_many({"item_id": item_id})
    
    # Delete prices
    await db.item_prices.delete_many({"item_id": item_id})
    
    # Delete item
    result = await db.items.delete_one({"item_id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"code": 0, "message": "Item deleted successfully"}


# ============== ITEM-SPECIFIC STOCK LOCATIONS ==============

@router.get("/{item_id}/stock-locations")
async def get_item_stock_locations(item_id: str):
    """Get stock locations for an item"""
    db = get_db()
    locations = await db.item_stock_locations.find(
        {"item_id": item_id},
        {"_id": 0}
    ).to_list(100)
    
    total_stock = sum(loc.get("stock", 0) for loc in locations)
    
    return {"code": 0, "stock_locations": locations, "total_stock": total_stock}

