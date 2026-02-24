"""
Inventory Adjustments Module - Zoho Books Style
Full workflow: Create -> Draft -> Adjusted -> Void
Supports quantity and value adjustments with audit trail
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
import uuid
import base64
import csv
import io
import logging
from fastapi import Request
from utils.database import extract_org_id, org_query


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
    ticket_id: Optional[str] = None  # Optional link to ticket/complaint

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
        "ticket_id": data.ticket_id,
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
            qty = line.get("quantity_adjusted") or 0  # Handle None values
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


# ==================== EXPORT ====================

@router.get("/export/csv")
async def export_adjustments_csv(
    status: Optional[str] = None,
    adjustment_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Export adjustments to CSV"""
    query = {}
    if status:
        query["status"] = status
    if adjustment_type:
        query["adjustment_type"] = adjustment_type
    if date_from or date_to:
        dq = {}
        if date_from:
            dq["$gte"] = date_from
        if date_to:
            dq["$lte"] = date_to
        query["date"] = dq

    adjustments = await adjustments_col.find(query, {"_id": 0}).sort("date", -1).to_list(5000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Reference Number", "Date", "Type", "Status", "Account", "Reason",
        "Warehouse", "Description", "Item Name", "Item ID", "SKU",
        "Qty Available", "New Quantity", "Qty Adjusted",
        "Current Value", "New Value", "Value Adjusted",
        "Created By", "Ticket ID"
    ])

    for adj in adjustments:
        for line in adj.get("line_items", []):
            writer.writerow([
                adj.get("reference_number", ""),
                adj.get("date", ""),
                adj.get("adjustment_type", ""),
                adj.get("status", ""),
                adj.get("account", ""),
                adj.get("reason", ""),
                adj.get("warehouse_name", ""),
                adj.get("description", ""),
                line.get("item_name", ""),
                line.get("item_id", ""),
                line.get("sku", ""),
                line.get("quantity_available", ""),
                line.get("new_quantity", ""),
                line.get("quantity_adjusted", ""),
                line.get("current_value", ""),
                line.get("new_value", ""),
                line.get("value_adjusted", ""),
                adj.get("created_by", ""),
                adj.get("ticket_id", "")
            ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inventory_adjustments_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


# ==================== IMPORT ====================

@router.post("/import/validate")
async def validate_import(file: UploadFile = File(...)):
    """Validate CSV import file and return mapping preview"""
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    rows = []
    errors = []
    available_fields = list(reader.fieldnames or [])

    for i, row in enumerate(reader):
        if i >= 200:
            break
        rows.append(row)

    # Check for items that exist
    item_names = set()
    for row in rows:
        for f in ["Item Name", "item_name", "Item", "item"]:
            if row.get(f):
                item_names.add(row[f])
                break

    found_items = {}
    if item_names:
        items = await items_col.find(
            {"$or": [
                {"name": {"$in": list(item_names)}},
                {"item_id": {"$in": list(item_names)}}
            ]},
            {"_id": 0, "item_id": 1, "name": 1, "stock_on_hand": 1, "purchase_rate": 1}
        ).to_list(500)
        found_items = {i["name"]: i for i in items}
        found_items.update({i["item_id"]: i for i in items})

    return {
        "code": 0,
        "available_fields": available_fields,
        "row_count": len(rows),
        "preview_rows": rows[:5],
        "items_found": len(found_items),
        "items_not_found": [n for n in item_names if n not in found_items]
    }


@router.post("/import/process")
async def process_import(file: UploadFile = File(...)):
    """Process CSV import and create adjustments"""
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    errors = []
    grouped = {}

    for i, row in enumerate(reader):
        # Find item
        item_name = row.get("Item Name") or row.get("item_name") or row.get("Item") or row.get("item") or ""
        item_id = row.get("Item ID") or row.get("item_id") or ""

        item = None
        if item_id:
            item = await items_col.find_one({"item_id": item_id}, {"_id": 0})
        if not item and item_name:
            item = await items_col.find_one({"name": item_name}, {"_id": 0})

        if not item:
            errors.append(f"Row {i+2}: Item '{item_name or item_id}' not found")
            continue

        ref = row.get("Reference Number") or row.get("reference_number") or ""
        adj_type = row.get("Type") or row.get("adjustment_type") or "quantity"
        reason = row.get("Reason") or row.get("reason") or "Other"
        date = row.get("Date") or row.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        account = row.get("Account") or row.get("account") or "Cost of Goods Sold"
        desc = row.get("Description") or row.get("description") or ""

        # Group by reference number or create individual
        key = ref or f"IMPORT-{i}"
        if key not in grouped:
            grouped[key] = {
                "adjustment_type": adj_type.lower(),
                "reason": reason,
                "date": date,
                "account": account,
                "description": desc or f"Imported from CSV",
                "line_items": [],
                "reference_number": ref
            }

        current_stock = item.get("stock_on_hand", item.get("quantity", 0)) or 0
        current_cost = item.get("purchase_rate", 0) or 0

        try:
            new_qty = float(row.get("New Quantity") or row.get("new_quantity") or current_stock)
            new_val = float(row.get("New Value") or row.get("new_value") or current_cost)
        except (ValueError, TypeError):
            errors.append(f"Row {i+2}: Invalid numeric value")
            continue

        grouped[key]["line_items"].append({
            "item_id": item["item_id"],
            "item_name": item.get("name", ""),
            "quantity_available": current_stock,
            "new_quantity": new_qty if adj_type.lower() == "quantity" else None,
            "quantity_adjusted": round(new_qty - current_stock, 4) if adj_type.lower() == "quantity" else None,
            "current_value": current_cost,
            "new_value": new_val if adj_type.lower() == "value" else None,
            "value_adjusted": round(new_val - current_cost, 2) if adj_type.lower() == "value" else None,
        })

    # Create adjustments from grouped data
    for key, group_data in grouped.items():
        if not group_data["line_items"]:
            continue
        adj_id = f"IA-{uuid.uuid4().hex[:12].upper()}"
        ref = group_data["reference_number"] or await generate_ref_number()

        at = group_data["adjustment_type"]
        lines = group_data["line_items"]
        if at == "quantity":
            ti = round(sum(max(0, l.get("quantity_adjusted") or 0) for l in lines), 4)
            td = round(sum(abs(min(0, l.get("quantity_adjusted") or 0)) for l in lines), 4)
        else:
            ti = round(sum(max(0, l.get("value_adjusted") or 0) for l in lines), 2)
            td = round(sum(abs(min(0, l.get("value_adjusted") or 0)) for l in lines), 2)

        adj_doc = {
            "adjustment_id": adj_id,
            "reference_number": ref,
            "adjustment_type": at,
            "date": group_data["date"],
            "account": group_data["account"],
            "reason": group_data["reason"],
            "warehouse_id": None,
            "warehouse_name": None,
            "description": group_data["description"],
            "line_items": lines,
            "line_item_count": len(lines),
            "total_increase": ti,
            "total_decrease": td,
            "status": "draft",
            "attachments": [],
            "ticket_id": None,
            "created_by": "import",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "converted_at": None,
            "voided_at": None
        }
        await adjustments_col.insert_one(adj_doc)
        await log_audit(adj_id, "imported", f"Created from CSV import as draft")
        created += 1

    return {
        "code": 0,
        "message": f"Import complete: {created} adjustments created as drafts",
        "created": created,
        "errors": errors
    }


# ==================== PDF GENERATION ====================

def generate_adjustment_html(adj: dict) -> str:
    """Generate HTML for adjustment PDF"""
    lines_html = ""
    for line in adj.get("line_items", []):
        if adj.get("adjustment_type") == "quantity":
            lines_html += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb">{line.get('item_name','')}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:center">{line.get('sku','')}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right">{line.get('quantity_available',0)}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600">{line.get('new_quantity','')}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;color:{'#16a34a' if (line.get('quantity_adjusted') or 0) >= 0 else '#dc2626'}">{'+' if (line.get('quantity_adjusted') or 0) > 0 else ''}{line.get('quantity_adjusted',0)}</td>
            </tr>"""
        else:
            lines_html += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb">{line.get('item_name','')}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:center">{line.get('sku','')}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right">₹{line.get('current_value',0):,.2f}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600">₹{(line.get('new_value') or 0):,.2f}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;color:{'#16a34a' if (line.get('value_adjusted') or 0) >= 0 else '#dc2626'}">₹{(line.get('value_adjusted') or 0):,.2f}</td>
            </tr>"""

    qty_headers = """
        <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;background:#f9fafb">Item</th>
        <th style="padding:8px;text-align:center;border-bottom:2px solid #e5e7eb;background:#f9fafb">SKU</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;background:#f9fafb">Available</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;background:#f9fafb">New Qty</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;background:#f9fafb">Change</th>
    """
    val_headers = """
        <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;background:#f9fafb">Item</th>
        <th style="padding:8px;text-align:center;border-bottom:2px solid #e5e7eb;background:#f9fafb">SKU</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;background:#f9fafb">Current Cost</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;background:#f9fafb">New Cost</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;background:#f9fafb">Change</th>
    """
    headers = qty_headers if adj.get("adjustment_type") == "quantity" else val_headers

    status_color = {"draft": "#eab308", "adjusted": "#16a34a", "void": "#dc2626"}.get(adj.get("status"), "#6b7280")
    type_label = adj.get("adjustment_type", "quantity").title()

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin:0; padding:24px; color:#1f2937; font-size:13px; }}
  .header {{ display:flex; justify-content:space-between; margin-bottom:24px; }}
  .title {{ font-size:22px; font-weight:700; color:#111827; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; color:white; background:{status_color}; }}
  .meta-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px; }}
  .meta-item {{ }}
  .meta-label {{ font-size:11px; color:#6b7280; text-transform:uppercase; }}
  .meta-value {{ font-weight:500; margin-top:2px; }}
  table {{ width:100%; border-collapse:collapse; margin-top:16px; }}
  .footer {{ margin-top:24px; padding-top:16px; border-top:1px solid #e5e7eb; font-size:11px; color:#9ca3af; }}
</style></head><body>
<div class="header">
  <div>
    <div class="title">Inventory Adjustment</div>
    <div style="color:#6b7280;margin-top:4px">{adj.get('reference_number','')}</div>
  </div>
  <div style="text-align:right">
    <span class="badge">{adj.get('status','').upper()}</span>
    <div style="margin-top:8px;font-size:12px;color:#6b7280">{type_label} Adjustment</div>
  </div>
</div>
<div class="meta-grid">
  <div class="meta-item"><div class="meta-label">Date</div><div class="meta-value">{adj.get('date','')}</div></div>
  <div class="meta-item"><div class="meta-label">Account</div><div class="meta-value">{adj.get('account','')}</div></div>
  <div class="meta-item"><div class="meta-label">Reason</div><div class="meta-value">{adj.get('reason','')}</div></div>
  <div class="meta-item"><div class="meta-label">Warehouse</div><div class="meta-value">{adj.get('warehouse_name','N/A')}</div></div>
</div>
{f'<div style="margin-bottom:16px;padding:12px;background:#f9fafb;border-radius:8px"><div class="meta-label">Description</div><div style="margin-top:4px">{adj.get("description","")}</div></div>' if adj.get("description") else ''}
<table>
  <thead><tr>{headers}</tr></thead>
  <tbody>{lines_html}</tbody>
</table>
<div style="margin-top:12px;text-align:right;font-size:12px;color:#6b7280">
  Total Increase: <strong style="color:#16a34a">{adj.get('total_increase',0)}</strong> |
  Total Decrease: <strong style="color:#dc2626">{adj.get('total_decrease',0)}</strong>
</div>
<div class="footer">
  Created by {adj.get('created_by','')} on {adj.get('created_at','')[:10]}
  {f"| Converted: {adj.get('converted_at','')[:10]}" if adj.get('converted_at') else ''}
  {f"| Voided: {adj.get('voided_at','')[:10]}" if adj.get('voided_at') else ''}
  {f"| Ticket: {adj.get('ticket_id','')}" if adj.get('ticket_id') else ''}
</div>
</body></html>"""


@router.get("/{adjustment_id}/pdf")
async def generate_pdf(adjustment_id: str):
    """Generate and download PDF of adjustment"""
    adj = await adjustments_col.find_one({"adjustment_id": adjustment_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")

    html_content = generate_adjustment_html(adj)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Adjustment_{adj.get('reference_number', adjustment_id)}.pdf"}
        )
    except ImportError:
        return {"code": 1, "message": "WeasyPrint not available", "html": html_content}
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        return {"code": 1, "message": f"PDF error: {str(e)}", "html": html_content}


# ==================== ABC DRILL-DOWN ====================

@router.get("/reports/abc-classification/{item_id}")
async def abc_drill_down(item_id: str, period_days: int = 90):
    """Drill down into adjustments for a specific item in ABC report"""
    since = (datetime.now(timezone.utc) - timedelta(days=period_days)).strftime("%Y-%m-%d")

    adjustments = await adjustments_col.find(
        {"status": "adjusted", "date": {"$gte": since}, "line_items.item_id": item_id},
        {"_id": 0}
    ).sort("date", -1).to_list(200)

    details = []
    for adj in adjustments:
        for line in adj.get("line_items", []):
            if line.get("item_id") == item_id:
                details.append({
                    "adjustment_id": adj["adjustment_id"],
                    "reference_number": adj["reference_number"],
                    "date": adj["date"],
                    "reason": adj.get("reason", ""),
                    "type": adj["adjustment_type"],
                    "quantity_adjusted": line.get("quantity_adjusted") or 0,
                    "value_adjusted": line.get("value_adjusted") or 0,
                    "status": adj["status"],
                    "warehouse": adj.get("warehouse_name", "")
                })

    item = await items_col.find_one({"item_id": item_id}, {"_id": 0, "name": 1, "sku": 1, "stock_on_hand": 1, "purchase_rate": 1})

    return {
        "code": 0,
        "item": item,
        "adjustments": details,
        "total_adjustments": len(details),
        "total_qty_change": sum(d["quantity_adjusted"] for d in details),
        "total_value_change": sum(d["value_adjusted"] for d in details)
    }

