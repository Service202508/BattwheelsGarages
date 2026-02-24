"""
Composite Items Module - Kit/Assembly Items with Bill of Materials
Allows creating items that are composed of other items (bundles/kits)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import motor.motor_asyncio
import os
import uuid
import logging
from fastapi import Request
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/composite-items", tags=["Composite Items"])

items_collection = db["items"]
composite_collection = db["composite_items"]
bom_collection = db["bill_of_materials"]


# ==================== MODELS ====================

class BOMComponent(BaseModel):
    """Component in a Bill of Materials"""
    item_id: str
    item_name: Optional[str] = None
    quantity: float = 1
    unit: str = "pcs"
    waste_percentage: float = 0  # For manufacturing waste


class CompositeItemCreate(BaseModel):
    """Create a composite/kit item"""
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    type: str = "kit"  # kit, assembly, bundle
    components: List[BOMComponent]
    selling_price: Optional[float] = None  # Override calculated price
    auto_calculate_price: bool = True
    markup_percentage: float = 0
    track_inventory: bool = True
    auto_build: bool = False  # Auto-build when sold
    min_build_quantity: int = 1
    category: Optional[str] = None


class CompositeItemUpdate(BaseModel):
    """Update a composite item"""
    name: Optional[str] = None
    description: Optional[str] = None
    components: Optional[List[BOMComponent]] = None
    selling_price: Optional[float] = None
    auto_calculate_price: Optional[bool] = None
    markup_percentage: Optional[float] = None
    track_inventory: Optional[bool] = None
    auto_build: Optional[bool] = None
    is_active: Optional[bool] = None


class BuildRequest(BaseModel):
    """Request to build composite items"""
    quantity: int = 1
    notes: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

async def calculate_component_cost(components: List[dict]) -> dict:
    """Calculate total cost from components"""
    total_cost = 0
    component_details = []
    all_available = True
    
    for comp in components:
        item = await items_collection.find_one({"item_id": comp["item_id"]}, {"_id": 0})
        if not item:
            component_details.append({
                "item_id": comp["item_id"],
                "item_name": comp.get("item_name", "Unknown"),
                "status": "not_found",
                "available": False
            })
            all_available = False
            continue
        
        # Calculate cost with waste
        base_qty = comp["quantity"]
        waste = comp.get("waste_percentage", 0) / 100
        effective_qty = base_qty * (1 + waste)
        
        item_cost = item.get("purchase_rate", item.get("rate", 0)) * effective_qty
        total_cost += item_cost
        
        # Check availability
        stock = item.get("stock_on_hand", item.get("quantity", 0))
        available = stock >= effective_qty
        if not available:
            all_available = False
        
        component_details.append({
            "item_id": comp["item_id"],
            "item_name": item.get("name", comp.get("item_name", "")),
            "quantity_required": effective_qty,
            "stock_available": stock,
            "unit_cost": item.get("purchase_rate", item.get("rate", 0)),
            "total_cost": item_cost,
            "available": available
        })
    
    return {
        "total_cost": round(total_cost, 2),
        "components": component_details,
        "all_components_available": all_available
    }


async def deduct_component_stock(components: List[dict], quantity: int, reference_id: str):
    """Deduct component stock when building composite item"""
    deductions = []
    
    for comp in components:
        item = await items_collection.find_one({"item_id": comp["item_id"]})
        if not item:
            continue
        
        # Calculate quantity to deduct with waste
        base_qty = comp["quantity"] * quantity
        waste = comp.get("waste_percentage", 0) / 100
        deduct_qty = base_qty * (1 + waste)
        
        # Update stock
        current_stock = item.get("stock_on_hand", item.get("quantity", 0))
        new_stock = max(0, current_stock - deduct_qty)
        
        await items_collection.update_one(
            {"item_id": comp["item_id"]},
            {"$set": {
                "stock_on_hand": new_stock,
                "quantity": new_stock,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        deductions.append({
            "item_id": comp["item_id"],
            "item_name": item.get("name"),
            "quantity_deducted": deduct_qty,
            "previous_stock": current_stock,
            "new_stock": new_stock
        })
    
    # Log the build
    await bom_collection.insert_one({
        "build_id": f"BLD-{uuid.uuid4().hex[:12].upper()}",
        "composite_id": reference_id,
        "quantity_built": quantity,
        "component_deductions": deductions,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "type": "build"
    })
    
    return deductions


# ==================== API ENDPOINTS ====================

@router.post("")
async def create_composite_item(request: Request, data: CompositeItemCreate):
    org_id = extract_org_id(request)
    """Create a new composite/kit item"""
    # Validate all components exist
    for comp in data.components:
        item = await items_collection.find_one({"item_id": comp.item_id}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=400, detail=f"Component item {comp.item_id} not found")
        comp.item_name = item.get("name")
    
    # Calculate cost
    cost_calc = await calculate_component_cost([c.dict() for c in data.components])
    
    # Calculate selling price
    if data.auto_calculate_price:
        base_price = cost_calc["total_cost"]
        selling_price = base_price * (1 + data.markup_percentage / 100)
    else:
        selling_price = data.selling_price or cost_calc["total_cost"]
    
    composite_id = f"COMP-{uuid.uuid4().hex[:12].upper()}"
    
    composite = {
        "composite_id": composite_id,
        "name": data.name,
        "sku": data.sku or f"KIT-{uuid.uuid4().hex[:6].upper()}",
        "description": data.description,
        "type": data.type,
        "components": [c.dict() for c in data.components],
        "component_cost": cost_calc["total_cost"],
        "selling_price": round(selling_price, 2),
        "markup_percentage": data.markup_percentage,
        "auto_calculate_price": data.auto_calculate_price,
        "track_inventory": data.track_inventory,
        "auto_build": data.auto_build,
        "min_build_quantity": data.min_build_quantity,
        "category": data.category,
        "stock_on_hand": 0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await composite_collection.insert_one(composite)
    
    # Also create as regular item for use in transactions
    item_doc = {
        "item_id": composite_id,
        "name": data.name,
        "sku": composite["sku"],
        "description": data.description,
        "type": "goods",
        "item_type": "composite",
        "composite_id": composite_id,
        "rate": selling_price,
        "purchase_rate": cost_calc["total_cost"],
        "category": data.category,
        "stock_on_hand": 0,
        "quantity": 0,
        "is_active": True,
        "is_composite": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await items_collection.insert_one(item_doc)
    
    return {
        "code": 0,
        "message": "Composite item created",
        "composite_id": composite_id,
        "component_cost": cost_calc["total_cost"],
        "selling_price": selling_price,
        "components_available": cost_calc["all_components_available"]
    }


@router.get("")
async def list_composite_items(request: Request, type: Optional[str] = None, is_active: bool = True, skip: int = 0, limit: int = 50):
    org_id = extract_org_id(request)
    """List all composite items"""
    query = {"is_active": is_active}
    if type:
        query["type"] = type
    
    total = await composite_collection.count_documents(query)
    items = await composite_collection.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with availability status
    for item in items:
        cost_calc = await calculate_component_cost(item.get("components", []))
        item["components_available"] = cost_calc["all_components_available"]
        item["current_component_cost"] = cost_calc["total_cost"]
    
    return {
        "code": 0,
        "composite_items": items,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }


@router.get("/summary")
async def get_composite_summary(request: Request):
    org_id = extract_org_id(request)
    """Get summary statistics for composite items"""
    total = await composite_collection.count_documents(org_query(org_id))
    active = await composite_collection.count_documents({"is_active": True})
    kits = await composite_collection.count_documents({"type": "kit"})
    assemblies = await composite_collection.count_documents({"type": "assembly"})
    bundles = await composite_collection.count_documents({"type": "bundle"})
    
    # Total inventory value
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": None, "total": {"$sum": {"$multiply": ["$selling_price", "$stock_on_hand"]}}}}
    ]
    result = await composite_collection.aggregate(pipeline).to_list(1)
    inventory_value = result[0]["total"] if result else 0
    
    return {
        "code": 0,
        "total_items": total,
        "active": active,
        "kits": kits,
        "assemblies": assemblies,
        "bundles": bundles,
        "inventory_value": round(inventory_value, 2)
    }


@router.get("/{composite_id}")
async def get_composite_item(request: Request, composite_id: str):
    org_id = extract_org_id(request)
    """Get a specific composite item with component details"""
    item = await composite_collection.find_one({"composite_id": composite_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Composite item not found")
    
    # Get detailed component info
    cost_calc = await calculate_component_cost(item.get("components", []))
    item["component_details"] = cost_calc["components"]
    item["current_component_cost"] = cost_calc["total_cost"]
    item["components_available"] = cost_calc["all_components_available"]
    
    # Get build history
    builds = await bom_collection.find(
        {"composite_id": composite_id, "type": "build"},
        {"_id": 0}
    ).sort("built_at", -1).limit(10).to_list(10)
    item["recent_builds"] = builds
    
    return {"code": 0, "composite_item": item}


@router.put("/{composite_id}")
async def update_composite_item(request: Request, composite_id: str, data: CompositeItemUpdate):
    org_id = extract_org_id(request)
    """Update a composite item"""
    item = await composite_collection.find_one({"composite_id": composite_id})
    if not item:
        raise HTTPException(status_code=404, detail="Composite item not found")
    
    update_dict = {k: v for k, v in data.dict().items() if v is not None}
    
    # Recalculate if components changed
    if "components" in update_dict:
        components = [c.dict() if hasattr(c, 'dict') else c for c in update_dict["components"]]
        cost_calc = await calculate_component_cost(components)
        update_dict["component_cost"] = cost_calc["total_cost"]
        
        if item.get("auto_calculate_price", True):
            markup = update_dict.get("markup_percentage", item.get("markup_percentage", 0))
            update_dict["selling_price"] = round(cost_calc["total_cost"] * (1 + markup / 100), 2)
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await composite_collection.update_one(
        {"composite_id": composite_id},
        {"$set": update_dict}
    )
    
    # Update linked item
    item_update = {}
    if "name" in update_dict:
        item_update["name"] = update_dict["name"]
    if "selling_price" in update_dict:
        item_update["rate"] = update_dict["selling_price"]
    if "is_active" in update_dict:
        item_update["is_active"] = update_dict["is_active"]
    if item_update:
        await items_collection.update_one(
            {"item_id": composite_id},
            {"$set": item_update}
        )
    
    return {"code": 0, "message": "Composite item updated"}


@router.post("/{composite_id}/build")
async def build_composite_item(composite_id: str, request: BuildRequest):
    """Build/assemble composite items from components"""
    item = await composite_collection.find_one({"composite_id": composite_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Composite item not found")
    
    if request.quantity < item.get("min_build_quantity", 1):
        raise HTTPException(status_code=400, detail=f"Minimum build quantity is {item.get('min_build_quantity', 1)}")
    
    # Check component availability
    cost_calc = await calculate_component_cost(item.get("components", []))
    
    # Check if enough stock for requested quantity
    for comp in cost_calc["components"]:
        required = comp["quantity_required"] * request.quantity
        if comp["stock_available"] < required:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {comp['item_name']}: need {required}, have {comp['stock_available']}"
            )
    
    # Deduct component stock
    deductions = await deduct_component_stock(
        item.get("components", []),
        request.quantity,
        composite_id
    )
    
    # Increase composite stock
    current_stock = item.get("stock_on_hand", 0)
    new_stock = current_stock + request.quantity
    
    await composite_collection.update_one(
        {"composite_id": composite_id},
        {"$set": {
            "stock_on_hand": new_stock,
            "last_built_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        "$inc": {"total_builds": 1, "total_quantity_built": request.quantity}}
    )
    
    # Update linked item stock
    await items_collection.update_one(
        {"item_id": composite_id},
        {"$set": {"stock_on_hand": new_stock, "quantity": new_stock}}
    )
    
    return {
        "code": 0,
        "message": f"Built {request.quantity} {item['name']}",
        "quantity_built": request.quantity,
        "new_stock": new_stock,
        "component_deductions": deductions
    }


@router.post("/{composite_id}/unbuild")
async def unbuild_composite_item(composite_id: str, request: BuildRequest):
    """Disassemble composite items back to components"""
    item = await composite_collection.find_one({"composite_id": composite_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Composite item not found")
    
    current_stock = item.get("stock_on_hand", 0)
    if current_stock < request.quantity:
        raise HTTPException(status_code=400, detail=f"Only {current_stock} available to unbuild")
    
    # Return components to stock
    restorations = []
    for comp in item.get("components", []):
        component_item = await items_collection.find_one({"item_id": comp["item_id"]})
        if not component_item:
            continue
        
        restore_qty = comp["quantity"] * request.quantity
        current_comp_stock = component_item.get("stock_on_hand", component_item.get("quantity", 0))
        new_comp_stock = current_comp_stock + restore_qty
        
        await items_collection.update_one(
            {"item_id": comp["item_id"]},
            {"$set": {
                "stock_on_hand": new_comp_stock,
                "quantity": new_comp_stock
            }}
        )
        
        restorations.append({
            "item_id": comp["item_id"],
            "item_name": component_item.get("name"),
            "quantity_restored": restore_qty,
            "new_stock": new_comp_stock
        })
    
    # Decrease composite stock
    new_stock = current_stock - request.quantity
    await composite_collection.update_one(
        {"composite_id": composite_id},
        {"$set": {"stock_on_hand": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await items_collection.update_one(
        {"item_id": composite_id},
        {"$set": {"stock_on_hand": new_stock, "quantity": new_stock}}
    )
    
    # Log the unbuild
    await bom_collection.insert_one({
        "build_id": f"UBD-{uuid.uuid4().hex[:12].upper()}",
        "composite_id": composite_id,
        "quantity_unbuilt": request.quantity,
        "component_restorations": restorations,
        "unbuilt_at": datetime.now(timezone.utc).isoformat(),
        "type": "unbuild"
    })
    
    return {
        "code": 0,
        "message": f"Unbuilt {request.quantity} {item['name']}",
        "quantity_unbuilt": request.quantity,
        "new_stock": new_stock,
        "component_restorations": restorations
    }


@router.get("/{composite_id}/availability")
async def check_build_availability(request: Request, composite_id: str, quantity: int = 1):
    org_id = extract_org_id(request)
    """Check if components are available to build a quantity"""
    item = await composite_collection.find_one({"composite_id": composite_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Composite item not found")
    
    cost_calc = await calculate_component_cost(item.get("components", []))
    
    # Calculate max buildable
    max_buildable = float('inf')
    shortages = []
    
    for comp in cost_calc["components"]:
        if comp["quantity_required"] > 0:
            available_builds = int(comp["stock_available"] / comp["quantity_required"])
            max_buildable = min(max_buildable, available_builds)
            
            if comp["stock_available"] < comp["quantity_required"] * quantity:
                shortages.append({
                    "item_name": comp["item_name"],
                    "required": comp["quantity_required"] * quantity,
                    "available": comp["stock_available"],
                    "shortage": comp["quantity_required"] * quantity - comp["stock_available"]
                })
    
    if max_buildable == float('inf'):
        max_buildable = 0
    
    return {
        "code": 0,
        "can_build": quantity <= max_buildable,
        "requested_quantity": quantity,
        "max_buildable": max_buildable,
        "components": cost_calc["components"],
        "shortages": shortages,
        "estimated_cost": cost_calc["total_cost"] * quantity
    }


@router.delete("/{composite_id}")
async def delete_composite_item(request: Request, composite_id: str):
    org_id = extract_org_id(request)
    """Delete a composite item"""
    result = await composite_collection.delete_one({"composite_id": composite_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Composite item not found")
    
    # Also delete from items
    await items_collection.delete_one({"item_id": composite_id})
    
    return {"code": 0, "message": "Composite item deleted"}
