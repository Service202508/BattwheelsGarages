"""
Inventory Adjustments Module - Zoho Books Style
Full workflow: Create -> Draft -> Adjusted -> Void
Supports quantity and value adjustments with audit trail
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
import uuid
import base64
import logging

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/inv-adjustments", tags=["Inventory Adjustments V2"])

# Collections
adjustments_col = db["inv_adjustments_v2"]
reasons_col = db["adjustment_reasons"]
audit_col = db["adjustment_audit_log"]
items_col = db["items"]
warehouses_col = db["warehouses"]
counters_col = db["counters"]
settings_col = db["inventory_settings"]


# ==================== MODELS ====================

class AdjustmentLineCreate(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    quantity_available: Optional[float] = 0
    new_quantity: Optional[float] = None       # For quantity adjustment
    quantity_adjusted: Optional[float] = None   # Auto-calculated
    current_value: Optional[float] = None       # For value adjustment
    new_value: Optional[float] = None           # For value adjustment
    value_adjusted: Optional[float] = None      # Auto-calculated

class AdjustmentCreate(BaseModel):
    adjustment_type: str = "quantity"  # quantity or value
    date: Optional[str] = None
    reference_number: Optional[str] = None
    account: str = "Cost of Goods Sold"
    reason: str = ""
    reason_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    warehouse_name: Optional[str] = None
    description: Optional[str] = ""
    line_items: List[AdjustmentLineCreate] = []
    status: str = "draft"  # draft or adjusted
    created_by: Optional[str] = None

class AdjustmentUpdate(BaseModel):
    date: Optional[str] = None
    account: Optional[str] = None
    reason: Optional[str] = None
    reason_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    warehouse_name: Optional[str] = None
    description: Optional[str] = None
    line_items: Optional[List[AdjustmentLineCreate]] = None

class ReasonCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    is_active: bool = True
    sort_order: int = 0


# ==================== HELPERS ====================

async def generate_ref_number():
    """Generate auto-incrementing reference number"""
    prefs = await settings_col.find_one({"type": "adjustment_numbering"}, {"_id": 0})
    prefix = prefs.get("prefix", "ADJ") if prefs else "ADJ"
    
    counter = await counters_col.find_one_and_update(
        {"_id": "inv_adjustments_v2"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    seq = counter["seq"]
    return f"{prefix}-{str(seq).zfill(5)}"


async def log_audit(adjustment_id: str, action: str, details: str, user: str = "system"):
    """Log audit trail entry"""
    await audit_col.insert_one({
        "audit_id": f"AUD-{uuid.uuid4().hex[:10].upper()}",
        "adjustment_id": adjustment_id,
        "action": action,
        "details": details,
        "user": user,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


async def apply_stock_changes(line_items: list, adjustment_type: str, reverse: bool = False):
    """Apply or reverse stock/value changes for line items"""
    for line in line_items:
        item = await items_col.find_one({"item_id": line["item_id"]})
        if not item:
            continue

        if adjustment_type == "quantity":
            qty_change = line.get("quantity_adjusted", 0)
            if reverse:
                qty_change = -qty_change
            current = item.get("stock_on_hand", item.get("quantity", 0)) or 0
            new_stock = current + qty_change
            await items_col.update_one(
                {"item_id": line["item_id"]},
                {"$set": {
                    "stock_on_hand": new_stock,
                    "quantity": new_stock,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        elif adjustment_type == "value":
            new_val = line.get("new_value")
            if reverse:
                new_val = line.get("current_value", item.get("purchase_rate", 0))
            if new_val is not None:
                await items_col.update_one(
                    {"item_id": line["item_id"]},
                    {"$set": {
                        "purchase_rate": new_val,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )


def enrich_line_items(line_items: list, items_map: dict, adjustment_type: str) -> list:
    """Enrich line items with computed fields"""
    enriched = []
    for line in line_items:
        li = dict(line) if isinstance(line, dict) else line.dict()
        item = items_map.get(li["item_id"], {})
        li["item_name"] = li.get("item_name") or item.get("name", "Unknown")
        li["sku"] = item.get("sku", "")

        if adjustment_type == "quantity":
            available = item.get("stock_on_hand", item.get("quantity", 0)) or 0
            li["quantity_available"] = available
            new_qty = li.get("new_quantity")
            if new_qty is not None:
                li["quantity_adjusted"] = round(new_qty - available, 4)
            else:
                li["quantity_adjusted"] = li.get("quantity_adjusted", 0)
        elif adjustment_type == "value":
            current_cost = item.get("purchase_rate", 0) or 0
            li["current_value"] = current_cost
            new_val = li.get("new_value")
            if new_val is not None:
                li["value_adjusted"] = round(new_val - current_cost, 2)
            else:
                li["value_adjusted"] = li.get("value_adjusted", 0)

        enriched.append(li)
    return enriched


# ==================== ADJUSTMENT REASONS ====================

@router.get("/reasons")
async def list_reasons(active_only: bool = True):
    """List adjustment reasons"""
    query = {"is_active": True} if active_only else {}
    reasons = await reasons_col.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    if not reasons and active_only:
        # Seed defaults
        defaults = [
            {"name": "Stocktaking Variance", "sort_order": 1},
            {"name": "Damaged Goods", "sort_order": 2},
            {"name": "Stock Transfer", "sort_order": 3},
            {"name": "Returned to Vendor", "sort_order": 4},
            {"name": "Stolen", "sort_order": 5},
            {"name": "Written Off", "sort_order": 6},
            {"name": "Expired", "sort_order": 7},
            {"name": "Donation", "sort_order": 8},
            {"name": "Other", "sort_order": 99},
        ]
        for d in defaults:
            d["reason_id"] = f"RSN-{uuid.uuid4().hex[:8].upper()}"
            d["is_active"] = True
            d["description"] = ""
            d["created_at"] = datetime.now(timezone.utc).isoformat()
            await reasons_col.insert_one(d)
        reasons = await reasons_col.find({"is_active": True}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return {"code": 0, "reasons": reasons}


@router.post("/reasons")
async def create_reason(data: ReasonCreate):
    """Create an adjustment reason"""
    reason_id = f"RSN-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "reason_id": reason_id,
        **data.dict(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await reasons_col.insert_one(doc)
    return {"code": 0, "message": "Reason created", "reason_id": reason_id}


@router.put("/reasons/{reason_id}")
async def update_reason(reason_id: str, data: ReasonCreate):
    """Update an adjustment reason"""
    result = await reasons_col.update_one(
        {"reason_id": reason_id},
        {"$set": {**data.dict(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reason not found")
    return {"code": 0, "message": "Reason updated"}


@router.delete("/reasons/{reason_id}")
async def disable_reason(reason_id: str):
    """Disable an adjustment reason (soft delete)"""
    await reasons_col.update_one(
        {"reason_id": reason_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"code": 0, "message": "Reason disabled"}


# ==================== CORE ADJUSTMENT CRUD ====================

@router.post("")
async def create_adjustment(data: AdjustmentCreate):
    """Create a new inventory adjustment (draft or adjusted)"""
    adj_id = f"IA-{uuid.uuid4().hex[:12].upper()}"
    ref_number = data.reference_number or await generate_ref_number()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Fetch items to enrich line items
    item_ids = [li.item_id for li in data.line_items]
    items_cursor = items_col.find({"item_id": {"$in": item_ids}}, {"_id": 0})
    items_list = await items_cursor.to_list(len(item_ids))
    items_map = {i["item_id"]: i for i in items_list}

    enriched_lines = enrich_line_items(data.line_items, items_map, data.adjustment_type)

    # Calculate totals
    if data.adjustment_type == "quantity":
        total_increase = sum(max(0, l.get("quantity_adjusted", 0)) for l in enriched_lines)
        total_decrease = sum(abs(min(0, l.get("quantity_adjusted", 0))) for l in enriched_lines)
    else:
        total_increase = sum(max(0, l.get("value_adjusted", 0)) for l in enriched_lines)
        total_decrease = sum(abs(min(0, l.get("value_adjusted", 0))) for l in enriched_lines)

    adj_doc = {
        "adjustment_id": adj_id,
        "reference_number": ref_number,
        "adjustment_type": data.adjustment_type,
        "date": data.date or today,
        "account": data.account,
        "reason": data.reason,
        "reason_id": data.reason_id,
        "warehouse_id": data.warehouse_id,
        "warehouse_name": data.warehouse_name,
        "description": data.description or "",
        "line_items": enriched_lines,
        "line_item_count": len(enriched_lines),
        "total_increase": round(total_increase, 4),
        "total_decrease": round(total_decrease, 4),
        "status": data.status,
        "attachments": [],
        "created_by": data.created_by or "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "converted_at": None,
        "voided_at": None
    }

    # If status is adjusted, apply stock changes immediately
    if data.status == "adjusted":
        await apply_stock_changes(enriched_lines, data.adjustment_type)
        adj_doc["converted_at"] = datetime.now(timezone.utc).isoformat()

    await adjustments_col.insert_one(adj_doc)
    await log_audit(adj_id, "created", f"Adjustment {ref_number} created as {data.status}", data.created_by or "admin")

    return {
        "code": 0,
        "message": f"Adjustment created as {data.status}",
        "adjustment_id": adj_id,
        "reference_number": ref_number,
        "status": data.status
    }


@router.get("")
async def list_adjustments(
    status: Optional[str] = None,
    adjustment_type: Optional[str] = None,
    reason: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 25
):
    """List inventory adjustments with filters"""
    query = {}
    if status:
        query["status"] = status
    if adjustment_type:
        query["adjustment_type"] = adjustment_type
    if reason:
        query["reason"] = reason
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if search:
        query["$or"] = [
            {"reference_number": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"reason": {"$regex": search, "$options": "i"}}
        ]
    if date_from or date_to:
        date_q = {}
        if date_from:
            date_q["$gte"] = date_from
        if date_to:
            date_q["$lte"] = date_to
        query["date"] = date_q

    sort_dir = -1 if sort_order == "desc" else 1
    sort_field = sort_by if sort_by in ["date", "reference_number", "status", "adjustment_type", "created_at"] else "date"

    total = await adjustments_col.count_documents(query)
    skip = (page - 1) * per_page
    adjustments = await adjustments_col.find(query, {"_id": 0}).sort(sort_field, sort_dir).skip(skip).limit(per_page).to_list(per_page)

    return {
        "code": 0,
        "adjustments": adjustments,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.get("/summary")
async def get_adjustments_summary():
    """Summary stats for the adjustments dashboard"""
    total = await adjustments_col.count_documents({})
    draft = await adjustments_col.count_documents({"status": "draft"})
    adjusted = await adjustments_col.count_documents({"status": "adjusted"})
    voided = await adjustments_col.count_documents({"status": "void"})

    # This month stats
    month_start = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")
    this_month = await adjustments_col.count_documents({"date": {"$gte": month_start}})

    # Totals for adjusted only
    pipeline = [
        {"$match": {"status": "adjusted"}},
        {"$group": {
            "_id": None,
            "total_increases": {"$sum": "$total_increase"},
            "total_decreases": {"$sum": "$total_decrease"}
        }}
    ]
    agg = await adjustments_col.aggregate(pipeline).to_list(1)
    totals = agg[0] if agg else {"total_increases": 0, "total_decreases": 0}

    return {
        "code": 0,
        "total": total,
        "draft": draft,
        "adjusted": adjusted,
        "voided": voided,
        "this_month": this_month,
        "total_increases": round(totals.get("total_increases", 0), 2),
        "total_decreases": round(totals.get("total_decreases", 0), 2)
    }


@router.get("/{adjustment_id}")
async def get_adjustment(adjustment_id: str):
    """Get adjustment detail with audit trail"""
    adj = await adjustments_col.find_one({"adjustment_id": adjustment_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")

    # Get audit trail
    audit = await audit_col.find(
        {"adjustment_id": adjustment_id}, {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    adj["audit_trail"] = audit

    return {"code": 0, "adjustment": adj}


@router.put("/{adjustment_id}")
async def update_adjustment(adjustment_id: str, data: AdjustmentUpdate):
    """Update a draft adjustment"""
    adj = await adjustments_col.find_one({"adjustment_id": adjustment_id})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    if adj.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft adjustments can be edited")

    update = {k: v for k, v in data.dict().items() if v is not None}

    if "line_items" in update:
        item_ids = [li["item_id"] if isinstance(li, dict) else li.item_id for li in update["line_items"]]
        items_list = await items_col.find({"item_id": {"$in": item_ids}}, {"_id": 0}).to_list(len(item_ids))
        items_map = {i["item_id"]: i for i in items_list}
        at = data.dict().get("adjustment_type") or adj.get("adjustment_type", "quantity")
        raw_lines = [li if isinstance(li, dict) else li.dict() for li in update["line_items"]]
        update["line_items"] = enrich_line_items(raw_lines, items_map, at)
        update["line_item_count"] = len(update["line_items"])
        # Recalculate totals
        if at == "quantity":
            update["total_increase"] = round(sum(max(0, l.get("quantity_adjusted", 0)) for l in update["line_items"]), 4)
            update["total_decrease"] = round(sum(abs(min(0, l.get("quantity_adjusted", 0))) for l in update["line_items"]), 4)
        else:
            update["total_increase"] = round(sum(max(0, l.get("value_adjusted", 0)) for l in update["line_items"]), 2)
            update["total_decrease"] = round(sum(abs(min(0, l.get("value_adjusted", 0))) for l in update["line_items"]), 2)

    update["updated_at"] = datetime.now(timezone.utc).isoformat()

    await adjustments_col.update_one({"adjustment_id": adjustment_id}, {"$set": update})
    await log_audit(adjustment_id, "updated", "Adjustment updated")

    return {"code": 0, "message": "Adjustment updated"}


@router.post("/{adjustment_id}/convert")
async def convert_to_adjusted(adjustment_id: str):
    """Convert draft adjustment to adjusted (applies stock changes)"""
    adj = await adjustments_col.find_one({"adjustment_id": adjustment_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    if adj.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft adjustments can be converted")
    if not adj.get("line_items"):
        raise HTTPException(status_code=400, detail="Adjustment has no line items")

    # Apply stock/value changes
    await apply_stock_changes(adj["line_items"], adj["adjustment_type"])

    now = datetime.now(timezone.utc).isoformat()
    await adjustments_col.update_one(
        {"adjustment_id": adjustment_id},
        {"$set": {"status": "adjusted", "converted_at": now, "updated_at": now}}
    )
    await log_audit(adjustment_id, "converted", "Converted to Adjusted - stock updated")

    return {"code": 0, "message": "Adjustment converted and stock updated"}


@router.post("/{adjustment_id}/void")
async def void_adjustment(adjustment_id: str):
    """Void an adjusted adjustment (reverses stock changes)"""
    adj = await adjustments_col.find_one({"adjustment_id": adjustment_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    if adj.get("status") != "adjusted":
        raise HTTPException(status_code=400, detail="Only adjusted entries can be voided")

    # Reverse stock/value changes
    await apply_stock_changes(adj["line_items"], adj["adjustment_type"], reverse=True)

    now = datetime.now(timezone.utc).isoformat()
    await adjustments_col.update_one(
        {"adjustment_id": adjustment_id},
        {"$set": {"status": "void", "voided_at": now, "updated_at": now}}
    )
    await log_audit(adjustment_id, "voided", "Adjustment voided - stock changes reversed")

    return {"code": 0, "message": "Adjustment voided and stock changes reversed"}


@router.delete("/{adjustment_id}")
async def delete_adjustment(adjustment_id: str):
    """Delete a draft adjustment"""
    adj = await adjustments_col.find_one({"adjustment_id": adjustment_id})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    if adj.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft adjustments can be deleted")

    await adjustments_col.delete_one({"adjustment_id": adjustment_id})
    await audit_col.delete_many({"adjustment_id": adjustment_id})
    return {"code": 0, "message": "Draft adjustment deleted"}


# ==================== ATTACHMENTS ====================

@router.post("/{adjustment_id}/attachments")
async def add_attachment(
    adjustment_id: str,
    file: UploadFile = File(...)
):
    """Add attachment to an adjustment (max 5, 10MB each)"""
    adj = await adjustments_col.find_one({"adjustment_id": adjustment_id})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")

    current = adj.get("attachments", [])
    if len(current) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 attachments allowed")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    attachment = {
        "attachment_id": f"ATT-{uuid.uuid4().hex[:8].upper()}",
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "data": base64.b64encode(content).decode("utf-8"),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }

    await adjustments_col.update_one(
        {"adjustment_id": adjustment_id},
        {"$push": {"attachments": attachment}}
    )
    await log_audit(adjustment_id, "attachment_added", f"File '{file.filename}' attached")

    return {"code": 0, "message": "Attachment added", "attachment_id": attachment["attachment_id"]}


@router.delete("/{adjustment_id}/attachments/{attachment_id}")
async def remove_attachment(adjustment_id: str, attachment_id: str):
    """Remove attachment from adjustment"""
    result = await adjustments_col.update_one(
        {"adjustment_id": adjustment_id},
        {"$pull": {"attachments": {"attachment_id": attachment_id}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Attachment not found")

    await log_audit(adjustment_id, "attachment_removed", f"Attachment {attachment_id} removed")
    return {"code": 0, "message": "Attachment removed"}


# ==================== REPORTS ====================

@router.get("/reports/adjustment-summary")
async def adjustment_summary_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    warehouse_id: Optional[str] = None
):
    """Adjustment summary by reason, location, account"""
    match = {"status": "adjusted"}
    if date_from or date_to:
        date_q = {}
        if date_from:
            date_q["$gte"] = date_from
        if date_to:
            date_q["$lte"] = date_to
        match["date"] = date_q
    if warehouse_id:
        match["warehouse_id"] = warehouse_id

    # By reason
    by_reason = await adjustments_col.aggregate([
        {"$match": match},
        {"$group": {
            "_id": "$reason",
            "count": {"$sum": 1},
            "total_increase": {"$sum": "$total_increase"},
            "total_decrease": {"$sum": "$total_decrease"}
        }},
        {"$sort": {"count": -1}}
    ]).to_list(50)

    # By type
    by_type = await adjustments_col.aggregate([
        {"$match": match},
        {"$group": {
            "_id": "$adjustment_type",
            "count": {"$sum": 1},
            "total_increase": {"$sum": "$total_increase"},
            "total_decrease": {"$sum": "$total_decrease"}
        }}
    ]).to_list(10)

    # By account
    by_account = await adjustments_col.aggregate([
        {"$match": match},
        {"$group": {
            "_id": "$account",
            "count": {"$sum": 1},
            "total_increase": {"$sum": "$total_increase"},
            "total_decrease": {"$sum": "$total_decrease"}
        }}
    ]).to_list(20)

    total_adjustments = await adjustments_col.count_documents(match)

    return {
        "code": 0,
        "report": {
            "total_adjustments": total_adjustments,
            "by_reason": by_reason,
            "by_type": by_type,
            "by_account": by_account,
            "date_from": date_from,
            "date_to": date_to
        }
    }


@router.get("/reports/fifo-tracking")
async def fifo_cost_lot_tracking(item_id: Optional[str] = None, limit: int = 100):
    """FIFO Cost Lot Tracking - shows product-in and product-out lots"""
    match = {"status": "adjusted"}
    if item_id:
        match["line_items.item_id"] = item_id

    adjustments = await adjustments_col.find(match, {"_id": 0}).sort("date", 1).limit(limit).to_list(limit)

    lots = []
    for adj in adjustments:
        for line in adj.get("line_items", []):
            if item_id and line.get("item_id") != item_id:
                continue
            qty = line.get("quantity_adjusted", 0)
            lot = {
                "date": adj["date"],
                "reference": adj["reference_number"],
                "item_id": line["item_id"],
                "item_name": line.get("item_name", ""),
                "transaction_type": "Adjustment",
                "direction": "in" if qty > 0 else "out",
                "quantity": abs(qty),
                "cost_per_unit": line.get("current_value") or line.get("new_value") or 0,
                "total_cost": abs(qty) * (line.get("current_value") or line.get("new_value") or 0),
                "reason": adj.get("reason", ""),
                "warehouse": adj.get("warehouse_name", "")
            }
            lots.append(lot)

    return {
        "code": 0,
        "report": {
            "lots": lots,
            "total_lots": len(lots),
            "total_in": sum(l["quantity"] for l in lots if l["direction"] == "in"),
            "total_out": sum(l["quantity"] for l in lots if l["direction"] == "out")
        }
    }


@router.get("/reports/abc-classification")
async def abc_classification_report(
    period_days: int = 90,
    a_threshold: float = 80,
    b_threshold: float = 95
):
    """ABC Classification based on adjustment value over a period"""
    since = (datetime.now(timezone.utc) - timedelta(days=period_days)).strftime("%Y-%m-%d")

    pipeline = [
        {"$match": {"status": "adjusted", "date": {"$gte": since}}},
        {"$unwind": "$line_items"},
        {"$group": {
            "_id": "$line_items.item_id",
            "item_name": {"$first": "$line_items.item_name"},
            "adjustment_count": {"$sum": 1},
            "total_qty_adjusted": {"$sum": {"$abs": {"$ifNull": ["$line_items.quantity_adjusted", 0]}}},
            "total_value_adjusted": {"$sum": {"$abs": {"$ifNull": ["$line_items.value_adjusted", 0]}}}
        }},
        {"$sort": {"total_qty_adjusted": -1}}
    ]

    items = await adjustments_col.aggregate(pipeline).to_list(1000)

    # Calculate cumulative percentage and classify
    total_value = sum(i.get("total_qty_adjusted", 0) for i in items) or 1
    cumulative = 0
    for item in items:
        item["value_percentage"] = round(item["total_qty_adjusted"] / total_value * 100, 2)
        cumulative += item["value_percentage"]
        item["cumulative_percentage"] = round(cumulative, 2)
        if cumulative <= a_threshold:
            item["classification"] = "A"
        elif cumulative <= b_threshold:
            item["classification"] = "B"
        else:
            item["classification"] = "C"

    class_counts = {"A": 0, "B": 0, "C": 0}
    for item in items:
        class_counts[item["classification"]] += 1

    return {
        "code": 0,
        "report": {
            "items": items,
            "class_counts": class_counts,
            "period_days": period_days,
            "thresholds": {"a": a_threshold, "b": b_threshold}
        }
    }


# ==================== NUMBERING SETTINGS ====================

@router.get("/settings/numbering")
async def get_numbering_settings():
    """Get adjustment numbering settings"""
    settings = await settings_col.find_one({"type": "adjustment_numbering"}, {"_id": 0})
    if not settings:
        settings = {"prefix": "ADJ", "next_number": 1, "format": "{prefix}-{number:05d}"}
    return {"code": 0, "settings": settings}


@router.put("/settings/numbering")
async def update_numbering_settings(prefix: str = "ADJ", next_number: int = 1):
    """Update adjustment numbering settings"""
    await settings_col.update_one(
        {"type": "adjustment_numbering"},
        {"$set": {
            "type": "adjustment_numbering",
            "prefix": prefix,
            "next_number": next_number,
            "format": f"{prefix}-{{number:05d}}",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    # Also update the counter
    await counters_col.update_one(
        {"_id": "inv_adjustments_v2"},
        {"$set": {"seq": next_number - 1}},
        upsert=True
    )
    return {"code": 0, "message": "Numbering settings updated"}
