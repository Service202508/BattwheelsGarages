"""
Stock Transfers Module - Zoho Books Style
Transfer stock between warehouses with full audit trail

Workflow: Create -> Draft -> In Transit -> Received -> Void
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import motor.motor_asyncio
import os
import uuid
import logging

from core.subscriptions.entitlement import require_feature

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(
    prefix="/stock-transfers",
    tags=["Stock Transfers"],
    dependencies=[Depends(require_feature("inventory_stock_transfers"))]
)

# Collections
transfers_col = db["stock_transfers"]
transfer_items_col = db["stock_transfer_items"]
audit_col = db["stock_transfer_audit"]
items_col = db["items"]
warehouses_col = db["warehouses"]
stock_col = db["item_stock"]
counters_col = db["counters"]


# ==================== MODELS ====================

class TransferItemCreate(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: float = Field(..., gt=0)
    source_stock: Optional[float] = None  # Available at source
    unit: str = "pcs"
    notes: Optional[str] = None


class StockTransferCreate(BaseModel):
    source_warehouse_id: str
    source_warehouse_name: Optional[str] = None
    destination_warehouse_id: str
    destination_warehouse_name: Optional[str] = None
    transfer_date: Optional[str] = None
    expected_arrival_date: Optional[str] = None
    reference_number: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    line_items: List[TransferItemCreate] = []
    created_by: Optional[str] = None
    organization_id: Optional[str] = None


class StockTransferUpdate(BaseModel):
    expected_arrival_date: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    line_items: Optional[List[TransferItemCreate]] = None


# ==================== HELPERS ====================

async def get_next_transfer_number(org_id: str = None) -> str:
    """Generate next transfer order number"""
    counter_id = f"stock_transfer_{org_id}" if org_id else "stock_transfer"
    counter = await counters_col.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return f"STO-{str(counter['seq']).zfill(5)}"


async def get_warehouse_stock(item_id: str, warehouse_id: str) -> float:
    """Get current stock of an item in a warehouse"""
    stock = await stock_col.find_one(
        {"item_id": item_id, "warehouse_id": warehouse_id},
        {"_id": 0}
    )
    return stock.get("quantity", 0) if stock else 0


async def adjust_warehouse_stock(
    item_id: str, 
    warehouse_id: str, 
    qty_change: float,
    reason: str,
    reference_id: str
):
    """Adjust stock in a warehouse (positive or negative)"""
    # Update or create stock record
    result = await stock_col.update_one(
        {"item_id": item_id, "warehouse_id": warehouse_id},
        {
            "$inc": {"quantity": qty_change},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    # Log the adjustment
    await audit_col.insert_one({
        "audit_id": f"sta_{uuid.uuid4().hex[:12]}",
        "item_id": item_id,
        "warehouse_id": warehouse_id,
        "qty_change": qty_change,
        "reason": reason,
        "reference_id": reference_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return result


# ==================== ROUTES ====================

@router.post("/")
async def create_stock_transfer(transfer: StockTransferCreate):
    """Create a new stock transfer order"""
    transfer_id = f"sto_{uuid.uuid4().hex[:12]}"
    transfer_number = await get_next_transfer_number(transfer.organization_id)
    now = datetime.now(timezone.utc)
    
    # Validate warehouses
    source = await warehouses_col.find_one(
        {"warehouse_id": transfer.source_warehouse_id},
        {"_id": 0}
    )
    dest = await warehouses_col.find_one(
        {"warehouse_id": transfer.destination_warehouse_id},
        {"_id": 0}
    )
    
    if not source:
        raise HTTPException(status_code=400, detail="Source warehouse not found")
    if not dest:
        raise HTTPException(status_code=400, detail="Destination warehouse not found")
    if transfer.source_warehouse_id == transfer.destination_warehouse_id:
        raise HTTPException(status_code=400, detail="Source and destination cannot be the same")
    
    # Validate stock availability and enrich line items
    enriched_items = []
    for item in transfer.line_items:
        source_stock = await get_warehouse_stock(item.item_id, transfer.source_warehouse_id)
        if source_stock < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {item.item_name or item.item_id}. Available: {source_stock}"
            )
        
        # Get item details
        item_doc = await items_col.find_one({"item_id": item.item_id}, {"_id": 0})
        
        enriched_items.append({
            "line_id": f"stl_{uuid.uuid4().hex[:8]}",
            "item_id": item.item_id,
            "item_name": item.item_name or (item_doc.get("name") if item_doc else ""),
            "sku": item.sku or (item_doc.get("sku") if item_doc else ""),
            "quantity": item.quantity,
            "source_stock": source_stock,
            "unit": item.unit,
            "notes": item.notes,
            "status": "pending"
        })
    
    # Create transfer document
    transfer_doc = {
        "transfer_id": transfer_id,
        "transfer_number": transfer_number,
        "organization_id": transfer.organization_id,
        
        # Warehouses
        "source_warehouse_id": transfer.source_warehouse_id,
        "source_warehouse_name": transfer.source_warehouse_name or source.get("name"),
        "destination_warehouse_id": transfer.destination_warehouse_id,
        "destination_warehouse_name": transfer.destination_warehouse_name or dest.get("name"),
        
        # Details
        "transfer_date": transfer.transfer_date or now.strftime("%Y-%m-%d"),
        "expected_arrival_date": transfer.expected_arrival_date,
        "reference_number": transfer.reference_number,
        "reason": transfer.reason,
        "notes": transfer.notes,
        
        # Line items
        "line_items": enriched_items,
        "total_items": len(enriched_items),
        "total_quantity": sum(i["quantity"] for i in enriched_items),
        
        # Status
        "status": "draft",  # draft, in_transit, received, void
        
        # Timestamps
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "created_by": transfer.created_by,
    }
    
    await transfers_col.insert_one(transfer_doc)
    
    # Log creation
    await audit_col.insert_one({
        "audit_id": f"sta_{uuid.uuid4().hex[:12]}",
        "transfer_id": transfer_id,
        "action": "created",
        "details": f"Stock transfer {transfer_number} created",
        "user": transfer.created_by,
        "timestamp": now.isoformat()
    })
    
    transfer_doc.pop("_id", None)
    return {"code": 0, "transfer": transfer_doc}


@router.get("/")
async def list_stock_transfers(
    status: Optional[str] = None,
    source_warehouse: Optional[str] = None,
    destination_warehouse: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
):
    """List all stock transfers"""
    query = {}
    if status:
        query["status"] = status
    if source_warehouse:
        query["source_warehouse_id"] = source_warehouse
    if destination_warehouse:
        query["destination_warehouse_id"] = destination_warehouse
    
    total = await transfers_col.count_documents(query)
    skip = (page - 1) * per_page
    
    transfers = await transfers_col.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "transfers": transfers,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total
        }
    }


@router.get("/{transfer_id}")
async def get_stock_transfer(transfer_id: str):
    """Get a specific stock transfer"""
    transfer = await transfers_col.find_one(
        {"transfer_id": transfer_id},
        {"_id": 0}
    )
    
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    return {"code": 0, "transfer": transfer}


@router.post("/{transfer_id}/ship")
async def ship_transfer(transfer_id: str, shipped_by: str = "system"):
    """
    Mark transfer as shipped (in transit).
    Deducts stock from source warehouse.
    """
    transfer = await transfers_col.find_one({"transfer_id": transfer_id})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft transfers can be shipped")
    
    now = datetime.now(timezone.utc)
    
    # Deduct stock from source warehouse
    for item in transfer.get("line_items", []):
        await adjust_warehouse_stock(
            item_id=item["item_id"],
            warehouse_id=transfer["source_warehouse_id"],
            qty_change=-item["quantity"],  # Negative = deduct
            reason=f"Stock transfer to {transfer.get('destination_warehouse_name')}",
            reference_id=transfer_id
        )
    
    # Update transfer status
    await transfers_col.update_one(
        {"transfer_id": transfer_id},
        {
            "$set": {
                "status": "in_transit",
                "shipped_at": now.isoformat(),
                "shipped_by": shipped_by,
                "updated_at": now.isoformat()
            }
        }
    )
    
    # Log action
    await audit_col.insert_one({
        "audit_id": f"sta_{uuid.uuid4().hex[:12]}",
        "transfer_id": transfer_id,
        "action": "shipped",
        "details": f"Transfer shipped by {shipped_by}",
        "user": shipped_by,
        "timestamp": now.isoformat()
    })
    
    updated = await transfers_col.find_one({"transfer_id": transfer_id}, {"_id": 0})
    return {"code": 0, "transfer": updated, "message": "Transfer shipped successfully"}


@router.post("/{transfer_id}/receive")
async def receive_transfer(
    transfer_id: str, 
    received_by: str = "system",
    received_items: Optional[List[dict]] = None  # Optional partial receipt
):
    """
    Mark transfer as received.
    Adds stock to destination warehouse.
    """
    transfer = await transfers_col.find_one({"transfer_id": transfer_id})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.get("status") != "in_transit":
        raise HTTPException(status_code=400, detail="Only in-transit transfers can be received")
    
    now = datetime.now(timezone.utc)
    
    # Add stock to destination warehouse
    for item in transfer.get("line_items", []):
        # Check if partial receipt
        receive_qty = item["quantity"]
        if received_items:
            for ri in received_items:
                if ri.get("line_id") == item.get("line_id"):
                    receive_qty = ri.get("received_quantity", item["quantity"])
                    break
        
        await adjust_warehouse_stock(
            item_id=item["item_id"],
            warehouse_id=transfer["destination_warehouse_id"],
            qty_change=receive_qty,  # Positive = add
            reason=f"Stock transfer from {transfer.get('source_warehouse_name')}",
            reference_id=transfer_id
        )
    
    # Update transfer status
    await transfers_col.update_one(
        {"transfer_id": transfer_id},
        {
            "$set": {
                "status": "received",
                "received_at": now.isoformat(),
                "received_by": received_by,
                "updated_at": now.isoformat()
            }
        }
    )
    
    # Log action
    await audit_col.insert_one({
        "audit_id": f"sta_{uuid.uuid4().hex[:12]}",
        "transfer_id": transfer_id,
        "action": "received",
        "details": f"Transfer received by {received_by}",
        "user": received_by,
        "timestamp": now.isoformat()
    })
    
    updated = await transfers_col.find_one({"transfer_id": transfer_id}, {"_id": 0})
    return {"code": 0, "transfer": updated, "message": "Transfer received successfully"}


@router.post("/{transfer_id}/void")
async def void_transfer(transfer_id: str, voided_by: str = "system", reason: str = ""):
    """
    Void a transfer. Reverses stock movements if already shipped.
    """
    transfer = await transfers_col.find_one({"transfer_id": transfer_id})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.get("status") == "void":
        raise HTTPException(status_code=400, detail="Transfer is already voided")
    
    now = datetime.now(timezone.utc)
    
    # Reverse stock movements based on status
    if transfer.get("status") == "in_transit":
        # Return stock to source
        for item in transfer.get("line_items", []):
            await adjust_warehouse_stock(
                item_id=item["item_id"],
                warehouse_id=transfer["source_warehouse_id"],
                qty_change=item["quantity"],  # Add back
                reason="Stock transfer void",
                reference_id=transfer_id
            )
    elif transfer.get("status") == "received":
        # Return to source and remove from destination
        for item in transfer.get("line_items", []):
            await adjust_warehouse_stock(
                item_id=item["item_id"],
                warehouse_id=transfer["source_warehouse_id"],
                qty_change=item["quantity"],
                reason="Stock transfer void",
                reference_id=transfer_id
            )
            await adjust_warehouse_stock(
                item_id=item["item_id"],
                warehouse_id=transfer["destination_warehouse_id"],
                qty_change=-item["quantity"],
                reason="Stock transfer void",
                reference_id=transfer_id
            )
    
    # Update transfer status
    await transfers_col.update_one(
        {"transfer_id": transfer_id},
        {
            "$set": {
                "status": "void",
                "voided_at": now.isoformat(),
                "voided_by": voided_by,
                "void_reason": reason,
                "updated_at": now.isoformat()
            }
        }
    )
    
    # Log action
    await audit_col.insert_one({
        "audit_id": f"sta_{uuid.uuid4().hex[:12]}",
        "transfer_id": transfer_id,
        "action": "voided",
        "details": f"Transfer voided by {voided_by}: {reason}",
        "user": voided_by,
        "timestamp": now.isoformat()
    })
    
    updated = await transfers_col.find_one({"transfer_id": transfer_id}, {"_id": 0})
    return {"code": 0, "transfer": updated, "message": "Transfer voided successfully"}


@router.get("/stats/summary")
async def get_transfer_stats(organization_id: Optional[str] = None):
    """Get stock transfer statistics"""
    query = {}
    if organization_id:
        query["organization_id"] = organization_id
    
    total = await transfers_col.count_documents(query)
    draft = await transfers_col.count_documents({**query, "status": "draft"})
    in_transit = await transfers_col.count_documents({**query, "status": "in_transit"})
    received = await transfers_col.count_documents({**query, "status": "received"})
    void = await transfers_col.count_documents({**query, "status": "void"})
    
    # Calculate total quantity transferred this month
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
    monthly_received = await transfers_col.aggregate([
        {
            "$match": {
                **query,
                "status": "received",
                "received_at": {"$gte": month_start.isoformat()}
            }
        },
        {"$group": {"_id": None, "total_qty": {"$sum": "$total_quantity"}}}
    ]).to_list(1)
    
    monthly_qty = monthly_received[0]["total_qty"] if monthly_received else 0
    
    return {
        "code": 0,
        "stats": {
            "total_transfers": total,
            "by_status": {
                "draft": draft,
                "in_transit": in_transit,
                "received": received,
                "void": void
            },
            "monthly_quantity_transferred": monthly_qty
        }
    }
