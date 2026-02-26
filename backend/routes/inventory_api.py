"""
Battwheels OS - Inventory & Purchase Order Routes (extracted from server.py)
Inventory CRUD, Allocations, Purchase Orders, Services, Stocktakes
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from schemas.models import (
    InventoryItem, InventoryCreate, InventoryUpdate,
    MaterialAllocation, MaterialAllocationCreate,
    PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderItem,
    StockReceiving, StocktakeCreateModel,
    ServiceOffering, ServiceOfferingCreate,
)
from core.tenant.dependencies import tenant_context_required, TenantContext

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Inventory Core"])
db = None

def init_router(database):
    global db
    db = database

@router.post("/inventory")
async def create_inventory_item(
    item_data: InventoryCreate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    
    # Get supplier name if provided
    supplier_name = None
    if item_data.supplier_id:
        supplier_query = {"supplier_id": item_data.supplier_id, "organization_id": ctx.org_id}
        supplier = await db.suppliers.find_one(supplier_query, {"_id": 0})
        supplier_name = supplier.get("name") if supplier else None
    
    item = InventoryItem(**item_data.model_dump(), supplier_name=supplier_name)
    doc = item.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['organization_id'] = ctx.org_id
    await db.inventory.insert_one(doc)
    return item.model_dump()

@router.get("/inventory")
async def get_inventory(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1),
    category: Optional[str] = Query(None),
    low_stock: bool = Query(False)
):
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")
    await require_auth(request)
    query = {"organization_id": ctx.org_id}
    if category:
        query["category"] = category
    if low_stock:
        query["$expr"] = {"$lte": ["$quantity", "$reorder_level"]}
    total = await db.inventory.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1
    items = await db.inventory.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {
        "data": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/inventory/reorder-suggestions")
async def get_inventory_reorder_suggestions(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    GET /api/inventory/reorder-suggestions
    Items where qty <= reorder_level, grouped by preferred vendor.
    """
    await require_auth(request)
    query = {
        "organization_id": ctx.org_id,
        "$expr": {"$lte": ["$quantity", "$reorder_level"]}
    }
    items = await db.inventory.find(query, {"_id": 0}).to_list(500)

    suggestions = []
    by_vendor: dict = {}
    for item in items:
        qty = float(item.get("quantity", 0))
        reorder = float(item.get("reorder_level", 10))
        shortage = max(0.0, reorder - qty)
        suggested_qty = item.get("reorder_quantity", max(int(shortage * 1.5), 1))
        unit_cost = float(item.get("cost_price") or item.get("unit_price", 0))
        s = {
            "item_id": item.get("item_id", ""),
            "item_name": item.get("name", ""),
            "sku": item.get("sku", ""),
            "category": item.get("category", ""),
            "current_stock_qty": qty,
            "reorder_level": reorder,
            "shortage": round(shortage, 2),
            "suggested_qty": suggested_qty,
            "unit_cost": unit_cost,
            "estimated_cost": round(suggested_qty * unit_cost, 2),
            "vendor_id": item.get("preferred_vendor_id"),
            "vendor_name": item.get("preferred_vendor_name", "No preferred vendor"),
        }
        suggestions.append(s)
        key = s.get("vendor_id") or "no_vendor"
        if key not in by_vendor:
            by_vendor[key] = {
                "vendor_id": s.get("vendor_id"),
                "vendor_name": s.get("vendor_name", "No preferred vendor"),
                "items": [], "total_estimated_cost": 0.0
            }
        by_vendor[key]["items"].append(s)
        by_vendor[key]["total_estimated_cost"] = round(
            by_vendor[key]["total_estimated_cost"] + s["estimated_cost"], 2
        )

    return {
        "code": 0,
        "total_items_below_reorder": len(suggestions),
        "suggestions": suggestions,
        "grouped_by_vendor": list(by_vendor.values()),
    }


@router.get("/inventory/stocktakes")
async def list_stocktakes_api(
    request: Request,
    status: Optional[str] = None,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """GET /api/inventory/stocktakes — List stocktake sessions for org."""
    await require_auth(request)
    query: dict = {"organization_id": ctx.org_id}
    if status:
        query["status"] = status
    stocktakes = await db.stocktakes.find(
        query,
        {"_id": 0, "stocktake_id": 1, "name": 1, "status": 1,
         "total_lines": 1, "counted_lines": 1, "total_variance": 1,
         "created_at": 1, "finalized_at": 1}
    ).sort("created_at", -1).to_list(100)
    return {"code": 0, "stocktakes": stocktakes, "total": len(stocktakes)}


class StocktakeCreateModel(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    item_ids: Optional[list] = None


@router.post("/inventory/stocktakes")
async def create_stocktake_api(
    data: StocktakeCreateModel,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """POST /api/inventory/stocktakes — Create stocktake session."""
    import uuid as _uuid
    await require_technician_or_admin(request)
    org_id = ctx.org_id
    now_iso = datetime.now(timezone.utc).isoformat()
    stocktake_id = f"ST-{_uuid.uuid4().hex[:12].upper()}"

    item_query: dict = {"organization_id": org_id}
    if data.item_ids:
        item_query["item_id"] = {"$in": data.item_ids}

    items = await db.inventory.find(
        item_query, {"_id": 0, "item_id": 1, "name": 1, "sku": 1, "quantity": 1}
    ).to_list(2000)

    lines = [{
        "item_id": it["item_id"],
        "item_name": it["name"],
        "sku": it.get("sku", ""),
        "system_quantity": float(it.get("quantity", 0)),
        "counted_quantity": None,
        "variance": None,
        "notes": "",
        "counted": False,
    } for it in items]

    doc = {
        "stocktake_id": stocktake_id,
        "name": data.name or f"Stocktake {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "organization_id": org_id,
        "status": "in_progress",
        "lines": lines,
        "total_lines": len(lines),
        "counted_lines": 0,
        "total_variance": 0,
        "notes": data.notes or "",
        "created_at": now_iso,
        "updated_at": now_iso,
        "finalized_at": None,
    }
    await db.stocktakes.insert_one(doc)
    doc.pop("_id", None)
    return {"code": 0, "message": "Stocktake created", "stocktake": doc}


@router.get("/inventory/{item_id}")
async def get_inventory_item(
    item_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"item_id": item_id, "organization_id": ctx.org_id}
    item = await db.inventory.find_one(query, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/inventory/{item_id}")
async def update_inventory_item(
    item_id: str, 
    update: InventoryUpdate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    query = {"item_id": item_id, "organization_id": ctx.org_id}
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Update supplier name if supplier_id changed
    if update.supplier_id:
        supplier_query = {"supplier_id": update.supplier_id, "organization_id": ctx.org_id}
        supplier = await db.suppliers.find_one(supplier_query, {"_id": 0})
        update_dict["supplier_name"] = supplier.get("name") if supplier else None
    
    await db.inventory.update_one(query, {"$set": update_dict})
    item = await db.inventory.find_one(query, {"_id": 0})
    return item

@router.delete("/inventory/{item_id}")
async def delete_inventory_item(
    item_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_admin(request)
    query = {"item_id": item_id, "organization_id": ctx.org_id}
    await db.inventory.delete_one(query)
    return {"message": "Item deleted"}

# ==================== MATERIAL ALLOCATION ROUTES ====================

@router.post("/allocations")
async def create_allocation(data: MaterialAllocationCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    """Allocate materials from inventory to a ticket"""
    user = await require_technician_or_admin(request)
    org_id = ctx.org_id
    
    # Verify ticket exists AND belongs to this org
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id, "organization_id": org_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get item details and check stock — scoped to this org
    item = await db.inventory.find_one({"item_id": data.item_id, "organization_id": org_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    available = item["quantity"] - item.get("reserved_quantity", 0)
    if available < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {available}")
    
    # Create allocation
    allocation = MaterialAllocation(
        ticket_id=data.ticket_id,
        item_id=data.item_id,
        item_name=item["name"],
        quantity=data.quantity,
        unit_price=item["unit_price"],
        total_price=data.quantity * item["unit_price"],
        allocated_by=user.user_id
    )
    doc = allocation.model_dump()
    doc['allocated_at'] = doc['allocated_at'].isoformat()
    doc['organization_id'] = org_id
    await db.allocations.insert_one(doc)
    
    # Update inventory reserved quantity (scoped)
    await db.inventory.update_one(
        {"item_id": data.item_id, "organization_id": org_id},
        {"$inc": {"reserved_quantity": data.quantity}}
    )
    
    # Update ticket parts cost (scoped)
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id, "organization_id": org_id},
        {"$inc": {"parts_cost": allocation.total_price}}
    )
    
    # Create ledger entry for COGS
    await create_ledger_entry(
        account_type="expense",
        account_name="Cost of Goods Sold",
        description=f"Parts allocated: {item['name']} x {data.quantity}",
        reference_type="allocation",
        reference_id=allocation.allocation_id,
        debit=allocation.total_price,
        credit=0,
        created_by=user.user_id,
        ticket_id=data.ticket_id,
        vehicle_id=ticket.get("vehicle_id")
    )
    
    return allocation.model_dump()

@router.get("/allocations")
async def get_allocations(request: Request, ctx: TenantContext = Depends(tenant_context_required), ticket_id: Optional[str] = None):
    await require_auth(request)
    query = {"organization_id": ctx.org_id}
    if ticket_id:
        query["ticket_id"] = ticket_id
    allocations = await db.allocations.find(query, {"_id": 0}).to_list(1000)
    return allocations

@router.put("/allocations/{allocation_id}/use")
async def mark_allocation_used(allocation_id: str, request: Request):
    """Mark allocated materials as used"""
    user = await require_technician_or_admin(request)
    
    allocation = await db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    # Update allocation status
    await db.allocations.update_one(
        {"allocation_id": allocation_id},
        {"$set": {"status": "used", "used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Reduce actual inventory quantity
    await db.inventory.update_one(
        {"item_id": allocation["item_id"]},
        {
            "$inc": {
                "quantity": -allocation["quantity"],
                "reserved_quantity": -allocation["quantity"]
            }
        }
    )
    
    return {"message": "Allocation marked as used"}

@router.put("/allocations/{allocation_id}/return")
async def return_allocation(allocation_id: str, request: Request):
    """Return allocated materials to inventory"""
    user = await require_technician_or_admin(request)
    
    allocation = await db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    # Update allocation status
    await db.allocations.update_one(
        {"allocation_id": allocation_id},
        {"$set": {"status": "returned"}}
    )
    
    # Release reserved quantity
    await db.inventory.update_one(
        {"item_id": allocation["item_id"]},
        {"$inc": {"reserved_quantity": -allocation["quantity"]}}
    )
    
    # Update ticket parts cost
    await db.tickets.update_one(
        {"ticket_id": allocation["ticket_id"]},
        {"$inc": {"parts_cost": -allocation["total_price"]}}
    )
    
    return {"message": "Materials returned to inventory"}

# ==================== PURCHASE ORDER ROUTES ====================

@router.post("/purchase-orders")
async def create_purchase_order(data: PurchaseOrderCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_technician_or_admin(request)
    
    # Get supplier
    supplier = await db.suppliers.find_one({"supplier_id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Build order items
    order_items = []
    subtotal = 0
    for item_data in data.items:
        inv_item = await db.inventory.find_one({"item_id": item_data["item_id"]}, {"_id": 0})
        if inv_item:
            item_total = item_data["quantity"] * item_data.get("unit_price", inv_item.get("cost_price", inv_item["unit_price"]))
            order_items.append(PurchaseOrderItem(
                item_id=item_data["item_id"],
                item_name=inv_item["name"],
                quantity=item_data["quantity"],
                unit_price=item_data.get("unit_price", inv_item.get("cost_price", inv_item["unit_price"])),
                total_price=item_total
            ))
            subtotal += item_total
    
    tax_amount = subtotal * 0.18  # 18% GST
    total_amount = subtotal + tax_amount
    
    po_number = await generate_po_number(ctx.org_id)
    
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=data.supplier_id,
        supplier_name=supplier["name"],
        items=[item.model_dump() for item in order_items],
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        expected_delivery=datetime.fromisoformat(data.expected_delivery) if data.expected_delivery else None,
        notes=data.notes,
        created_by=user.user_id
    )
    
    doc = po.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    if doc['expected_delivery']:
        doc['expected_delivery'] = doc['expected_delivery'].isoformat()
    await db.purchase_orders.insert_one(doc)
    
    return po.model_dump()

@router.get("/purchase-orders")
async def get_purchase_orders(request: Request, status: Optional[str] = None):
    await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    pos = await db.purchase_orders.find(query, {"_id": 0}).to_list(1000)
    return pos

@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str, request: Request):
    await require_auth(request)
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@router.put("/purchase-orders/{po_id}")
async def update_purchase_order(po_id: str, update: PurchaseOrderUpdate, request: Request):
    user = await require_admin(request)
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update.approval_status == "approved":
        update_dict["approved_by"] = user.user_id
        update_dict["approved_at"] = datetime.now(timezone.utc).isoformat()
        update_dict["status"] = "approved"
    elif update.approval_status == "rejected":
        update_dict["status"] = "cancelled"
    
    await db.purchase_orders.update_one({"po_id": po_id}, {"$set": update_dict})
    
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    
    # Create ledger entry for approved PO
    if update.approval_status == "approved":
        await create_ledger_entry(
            account_type="liability",
            account_name="Accounts Payable",
            description=f"Purchase Order: {po['po_number']}",
            reference_type="purchase",
            reference_id=po_id,
            debit=0,
            credit=po["total_amount"],
            created_by=user.user_id
        )
    
    return po

@router.post("/purchase-orders/{po_id}/receive")
async def receive_stock(po_id: str, items: List[dict], request: Request):
    """Receive stock from purchase order and update inventory"""
    user = await require_technician_or_admin(request)
    
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    all_received = True
    for received_item in items:
        item_id = received_item["item_id"]
        qty = received_item["quantity"]
        
        # Update PO item received quantity
        for po_item in po["items"]:
            if po_item["item_id"] == item_id:
                new_received = po_item.get("received_quantity", 0) + qty
                if new_received < po_item["quantity"]:
                    all_received = False
                
                # Update inventory
                await db.inventory.update_one(
                    {"item_id": item_id},
                    {
                        "$inc": {"quantity": qty},
                        "$set": {"last_restock_date": datetime.now(timezone.utc).isoformat()}
                    }
                )
                
                # Log receiving
                receiving_doc = {
                    "receiving_id": f"rcv_{uuid.uuid4().hex[:12]}",
                    "po_id": po_id,
                    "item_id": item_id,
                    "quantity_received": qty,
                    "received_by": user.user_id,
                    "received_at": datetime.now(timezone.utc).isoformat()
                }
                await db.stock_receivings.insert_one(receiving_doc)
                break
    
    # Update PO status
    new_status = "received" if all_received else "partially_received"
    await db.purchase_orders.update_one(
        {"po_id": po_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update supplier stats
    await db.suppliers.update_one(
        {"supplier_id": po["supplier_id"]},
        {"$inc": {"total_orders": 1, "total_value": po["total_amount"]}}
    )
    
    return {"message": f"Stock received. Status: {new_status}"}

# ==================== SERVICE OFFERING ROUTES ====================

@router.post("/services")
async def create_service(data: ServiceOfferingCreate, request: Request):
    await require_admin(request)
    service = ServiceOffering(**data.model_dump())
    doc = service.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.services.insert_one(doc)
    return service.model_dump()

@router.get("/services")
async def get_services(request: Request):
    await require_auth(request)
    services = await db.services.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return services

@router.put("/services/{service_id}")
async def update_service(service_id: str, data: dict, request: Request):
    await require_admin(request)
    await db.services.update_one({"service_id": service_id}, {"$set": data})
    service = await db.services.find_one({"service_id": service_id}, {"_id": 0})
    return service

# ==================== SALES ORDER ROUTES ====================