# Bills Enhanced Module - Full Purchase Side Accounting
# Vendor bills, payment tracking, and purchase management

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
import uuid
import logging

# Import double-entry posting hooks
from services.posting_hooks import post_bill_journal_entry, post_bill_payment_journal_entry
from services.inventory_service import get_inventory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bills-enhanced", tags=["Bills Enhanced"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Use main collections with Zoho-synced data
bills_collection = db["bills"]
bill_line_items_collection = db["bill_line_items"]
bill_payments_collection = db["bill_payments"]
bill_settings_collection = db["bill_settings"]
bill_history_collection = db["bill_history"]
contacts_collection = db["contacts"]
purchase_orders_collection = db["purchaseorders"]
po_line_items_collection = db["po_line_items"]

BILL_STATUSES = ["draft", "open", "partially_paid", "paid", "overdue", "void"]

# ========================= MODELS =========================

class LineItem(BaseModel):
    item_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: str = ""
    hsn_sac_code: str = ""
    quantity: float = Field(default=1, gt=0)
    unit: str = "pcs"
    rate: float = Field(..., ge=0)
    discount_type: str = "percentage"
    discount_value: float = 0
    tax_type: str = "gst"
    tax_rate: float = 18
    account_id: str = ""

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    payment_mode: str = "bank_transfer"
    reference_number: str = ""
    payment_date: str = ""
    notes: str = ""
    paid_from_account: str = ""

class BillCreate(BaseModel):
    vendor_id: str = Field(..., min_length=1)
    bill_number: str = ""
    reference_number: str = ""
    purchase_order_id: Optional[str] = None
    bill_date: str = ""
    due_date: str = ""
    payment_terms: int = 30
    line_items: List[LineItem] = []
    discount_type: str = "percentage"
    discount_value: float = 0
    tds_applicable: bool = False
    tds_rate: float = 0
    place_of_supply: str = ""
    is_inclusive_tax: bool = False
    reverse_charge: bool = False
    vendor_notes: str = ""
    custom_fields: Dict[str, Any] = {}

class BillUpdate(BaseModel):
    reference_number: Optional[str] = None
    bill_date: Optional[str] = None
    due_date: Optional[str] = None
    line_items: Optional[List[LineItem]] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    tds_rate: Optional[float] = None
    vendor_notes: Optional[str] = None

class PurchaseOrderCreate(BaseModel):
    vendor_id: str = Field(..., min_length=1)
    reference_number: str = ""
    order_date: str = ""
    expected_delivery_date: str = ""
    delivery_address: str = ""
    line_items: List[LineItem] = []
    discount_type: str = "percentage"
    discount_value: float = 0
    shipping_charge: float = 0
    place_of_supply: str = ""
    vendor_notes: str = ""
    terms_conditions: str = ""
    send_email: bool = False

# ========================= HELPERS =========================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def round_currency(value: float) -> float:
    return round(value, 2)

def calculate_line_item(item: LineItem, is_igst: bool = False) -> dict:
    quantity = item.quantity
    rate = item.rate
    amount = quantity * rate
    
    if item.discount_type == "percentage":
        discount_amount = amount * (item.discount_value / 100)
    else:
        discount_amount = item.discount_value
    
    taxable_amount = amount - discount_amount
    tax_rate = item.tax_rate if item.tax_type != "none" else 0
    tax_amount = taxable_amount * (tax_rate / 100)
    
    if is_igst:
        igst_amount = tax_amount
        cgst_amount = sgst_amount = 0
    else:
        igst_amount = 0
        cgst_amount = sgst_amount = tax_amount / 2
    
    return {
        "item_id": item.item_id,
        "name": item.name,
        "description": item.description,
        "hsn_sac_code": item.hsn_sac_code,
        "quantity": quantity,
        "unit": item.unit,
        "rate": round_currency(rate),
        "discount_type": item.discount_type,
        "discount_value": item.discount_value,
        "discount_amount": round_currency(discount_amount),
        "tax_type": item.tax_type,
        "tax_rate": tax_rate,
        "taxable_amount": round_currency(taxable_amount),
        "cgst_amount": round_currency(cgst_amount),
        "sgst_amount": round_currency(sgst_amount),
        "igst_amount": round_currency(igst_amount),
        "tax_amount": round_currency(tax_amount),
        "amount": round_currency(amount),
        "total": round_currency(taxable_amount + tax_amount),
        "account_id": item.account_id
    }

def calculate_totals(line_items: List[dict], discount_type: str, discount_value: float, tds_rate: float = 0) -> dict:
    sub_total = sum(item["amount"] for item in line_items)
    total_discount = sum(item["discount_amount"] for item in line_items)
    taxable_total = sum(item["taxable_amount"] for item in line_items)
    total_cgst = sum(item.get("cgst_amount", 0) for item in line_items)
    total_sgst = sum(item.get("sgst_amount", 0) for item in line_items)
    total_igst = sum(item.get("igst_amount", 0) for item in line_items)
    total_tax = sum(item["tax_amount"] for item in line_items)
    
    if discount_type == "percentage":
        bill_discount = (sub_total - total_discount) * (discount_value / 100)
    else:
        bill_discount = discount_value
    
    pre_tds_total = taxable_total + total_tax - bill_discount
    tds_amount = pre_tds_total * (tds_rate / 100) if tds_rate > 0 else 0
    grand_total = pre_tds_total - tds_amount
    
    return {
        "sub_total": round_currency(sub_total),
        "item_discount": round_currency(total_discount),
        "bill_discount": round_currency(bill_discount),
        "total_discount": round_currency(total_discount + bill_discount),
        "taxable_amount": round_currency(taxable_total - bill_discount),
        "cgst_total": round_currency(total_cgst),
        "sgst_total": round_currency(total_sgst),
        "igst_total": round_currency(total_igst),
        "tax_total": round_currency(total_tax),
        "tds_rate": tds_rate,
        "tds_amount": round_currency(tds_amount),
        "grand_total": round_currency(grand_total),
        "balance_due": round_currency(grand_total)
    }

async def get_next_bill_number() -> str:
    settings = await bill_settings_collection.find_one({"type": "numbering"})
    if not settings:
        settings = {"type": "numbering", "prefix": "BILL-", "next_number": 1, "padding": 5}
        await bill_settings_collection.insert_one(settings)
    
    number = str(settings["next_number"]).zfill(settings.get("padding", 5))
    bill_number = f"{settings.get('prefix', 'BILL-')}{number}"
    
    await bill_settings_collection.update_one({"type": "numbering"}, {"$inc": {"next_number": 1}})
    return bill_number

async def get_next_po_number() -> str:
    settings = await bill_settings_collection.find_one({"type": "po_numbering"})
    if not settings:
        settings = {"type": "po_numbering", "prefix": "PO-", "next_number": 1, "padding": 5}
        await bill_settings_collection.insert_one(settings)
    
    number = str(settings["next_number"]).zfill(settings.get("padding", 5))
    po_number = f"{settings.get('prefix', 'PO-')}{number}"
    
    await bill_settings_collection.update_one({"type": "po_numbering"}, {"$inc": {"next_number": 1}})
    return po_number

async def add_bill_history(bill_id: str, action: str, details: str, user_id: str = ""):
    await bill_history_collection.insert_one({
        "history_id": generate_id("HIST"),
        "bill_id": bill_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

async def update_vendor_balance(vendor_id: str):
    pipeline = [
        {"$match": {"vendor_id": vendor_id, "status": {"$nin": ["draft", "void"]}}},
        {"$group": {"_id": None, "total_billed": {"$sum": "$grand_total"}, "total_payable": {"$sum": "$balance_due"}}}
    ]
    result = await bills_collection.aggregate(pipeline).to_list(1)
    if result:
        await contacts_collection.update_one(
            {"contact_id": vendor_id},
            {"$set": {"outstanding_payable": result[0].get("total_payable", 0), "total_billed": result[0].get("total_billed", 0)}}
        )

async def update_bill_status(bill_id: str):
    bill = await bills_collection.find_one({"bill_id": bill_id})
    if not bill or bill.get("status") in ["void", "draft"]:
        return
    
    balance = bill.get("balance_due", 0)
    grand_total = bill.get("grand_total", 0)
    due_date = bill.get("due_date", "")
    
    if balance <= 0:
        new_status = "paid"
    elif balance < grand_total:
        new_status = "partially_paid"
    elif due_date:
        try:
            due = datetime.fromisoformat(due_date.replace('Z', '+00:00')).date()
            new_status = "overdue" if due < datetime.now(timezone.utc).date() else "open"
        except:
            new_status = "open"
    else:
        new_status = "open"
    
    if new_status != bill.get("status"):
        await bills_collection.update_one({"bill_id": bill_id}, {"$set": {"status": new_status}})

# ========================= SUMMARY =========================

@router.get("/summary")
async def get_bills_summary(period: str = "all"):
    query = {"status": {"$ne": "void"}}
    
    if period == "this_month":
        first = datetime.now(timezone.utc).replace(day=1).date().isoformat()
        query["bill_date"] = {"$gte": first}
    elif period == "this_year":
        first = datetime.now(timezone.utc).replace(month=1, day=1).date().isoformat()
        query["bill_date"] = {"$gte": first}
    
    total = await bills_collection.count_documents(query)
    draft = await bills_collection.count_documents({**query, "status": "draft"})
    open_bills = await bills_collection.count_documents({**query, "status": "open"})
    overdue = await bills_collection.count_documents({**query, "status": "overdue"})
    partially_paid = await bills_collection.count_documents({**query, "status": "partially_paid"})
    paid = await bills_collection.count_documents({**query, "status": "paid"})
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "total_billed": {"$sum": "$grand_total"}, "total_payable": {"$sum": "$balance_due"}, "total_paid": {"$sum": {"$subtract": ["$grand_total", "$balance_due"]}}}}
    ]
    totals = await bills_collection.aggregate(pipeline).to_list(1)
    values = totals[0] if totals else {"total_billed": 0, "total_payable": 0, "total_paid": 0}
    
    return {
        "code": 0,
        "summary": {
            "total_bills": total, "draft": draft, "open": open_bills, "overdue": overdue,
            "partially_paid": partially_paid, "paid": paid,
            "total_billed": round_currency(values.get("total_billed", 0)),
            "total_payable": round_currency(values.get("total_payable", 0)),
            "total_paid": round_currency(values.get("total_paid", 0))
        }
    }

# ========================= PURCHASE ORDERS =========================
# NOTE: These routes MUST be defined before /{bill_id} routes to avoid path conflicts

@router.get("/purchase-orders/summary")
async def get_po_summary():
    total = await purchase_orders_collection.count_documents({"status": {"$ne": "void"}})
    draft = await purchase_orders_collection.count_documents({"status": "draft"})
    issued = await purchase_orders_collection.count_documents({"status": "issued"})
    received = await purchase_orders_collection.count_documents({"status": "received"})
    billed = await purchase_orders_collection.count_documents({"status": "billed"})
    
    pipeline = [
        {"$match": {"status": {"$nin": ["draft", "void"]}}},
        {"$group": {"_id": None, "total_ordered": {"$sum": "$grand_total"}}}
    ]
    totals = await purchase_orders_collection.aggregate(pipeline).to_list(1)
    
    return {"code": 0, "summary": {
        "total_orders": total, "draft": draft, "issued": issued, "received": received, "billed": billed,
        "total_ordered": round_currency(totals[0].get("total_ordered", 0) if totals else 0)
    }}

@router.post("/purchase-orders")
async def create_purchase_order(po: PurchaseOrderCreate, background_tasks: BackgroundTasks):
    vendor = await contacts_collection.find_one({"contact_id": po.vendor_id})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    po_id = generate_id("PO")
    po_number = await get_next_po_number()
    
    vendor_state = po.place_of_supply or vendor.get("place_of_supply", "")
    is_igst = vendor_state and vendor_state != "DL"
    
    calculated_items = []
    for item in po.line_items:
        calc = calculate_line_item(item, is_igst)
        calc["line_item_id"] = generate_id("LI")
        calc["po_id"] = po_id
        calculated_items.append(calc)
    
    totals = calculate_totals(calculated_items, po.discount_type, po.discount_value)
    totals["shipping_charge"] = po.shipping_charge
    totals["grand_total"] = round_currency(totals["grand_total"] + po.shipping_charge)
    
    po_doc = {
        "po_id": po_id,
        "po_number": po_number,
        "vendor_id": po.vendor_id,
        "vendor_name": vendor.get("name", ""),
        "reference_number": po.reference_number,
        "order_date": po.order_date or datetime.now(timezone.utc).date().isoformat(),
        "expected_delivery_date": po.expected_delivery_date,
        "delivery_address": po.delivery_address,
        "place_of_supply": vendor_state,
        "discount_type": po.discount_type,
        "discount_value": po.discount_value,
        **totals,
        "status": "draft",
        "vendor_notes": po.vendor_notes,
        "terms_conditions": po.terms_conditions,
        "is_sent": False,
        "received_date": None,
        "billed_date": None,
        "bill_id": None,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await purchase_orders_collection.insert_one(po_doc)
    for item in calculated_items:
        await po_line_items_collection.insert_one(item)
    
    po_doc.pop("_id", None)
    for item in calculated_items:
        item.pop("_id", None)
    po_doc["line_items"] = calculated_items
    return {"code": 0, "message": "Purchase order created", "purchase_order": po_doc}

@router.get("/purchase-orders")
async def list_purchase_orders(
    vendor_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List purchase orders with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {"status": {"$ne": "void"}}
    if vendor_id:
        query["vendor_id"] = vendor_id
    if status:
        query["status"] = status

    total = await purchase_orders_collection.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    orders = await purchase_orders_collection.find(query, {"_id": 0}).sort("order_date", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": orders,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str):
    po = await purchase_orders_collection.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    line_items = await po_line_items_collection.find({"po_id": po_id}, {"_id": 0}).to_list(100)
    po["line_items"] = line_items
    
    return {"code": 0, "purchase_order": po}

@router.post("/purchase-orders/{po_id}/issue")
async def issue_purchase_order(po_id: str):
    po = await purchase_orders_collection.find_one({"po_id": po_id})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft POs can be issued")
    
    await purchase_orders_collection.update_one({"po_id": po_id}, {"$set": {"status": "issued", "is_sent": True}})
    return {"code": 0, "message": "Purchase order issued"}

@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(po_id: str):
    po = await purchase_orders_collection.find_one({"po_id": po_id})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.get("status") not in ["issued"]:
        raise HTTPException(status_code=400, detail="Only issued POs can be received")
    
    await purchase_orders_collection.update_one({"po_id": po_id}, {"$set": {"status": "received", "received_date": datetime.now(timezone.utc).date().isoformat()}})
    return {"code": 0, "message": "Purchase order marked as received"}

@router.post("/purchase-orders/{po_id}/convert-to-bill")
async def convert_po_to_bill(po_id: str, background_tasks: BackgroundTasks):
    po = await purchase_orders_collection.find_one({"po_id": po_id})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.get("status") == "billed":
        raise HTTPException(status_code=400, detail="PO already converted to bill")
    
    line_items = await po_line_items_collection.find({"po_id": po_id}, {"_id": 0}).to_list(100)
    
    bill_items = [
        LineItem(
            item_id=item.get("item_id"),
            name=item.get("name"),
            description=item.get("description", ""),
            hsn_sac_code=item.get("hsn_sac_code", ""),
            quantity=item.get("quantity", 1),
            unit=item.get("unit", "pcs"),
            rate=item.get("rate", 0),
            tax_rate=item.get("tax_rate", 18)
        )
        for item in line_items
    ]
    
    bill_data = BillCreate(
        vendor_id=po.get("vendor_id"),
        reference_number=po.get("po_number"),
        purchase_order_id=po_id,
        payment_terms=30,
        line_items=bill_items,
        discount_type=po.get("discount_type", "percentage"),
        discount_value=po.get("discount_value", 0),
        place_of_supply=po.get("place_of_supply", ""),
        vendor_notes=po.get("vendor_notes", "")
    )
    
    result = await create_bill(bill_data, background_tasks)
    
    await purchase_orders_collection.update_one(
        {"po_id": po_id},
        {"$set": {"status": "billed", "bill_id": result["bill"]["bill_id"], "billed_date": datetime.now(timezone.utc).date().isoformat()}}
    )
    
    return result

# ========================= BILLS CRUD =========================

@router.post("/")
async def create_bill(bill: BillCreate, background_tasks: BackgroundTasks):
    vendor = await contacts_collection.find_one({"contact_id": bill.vendor_id})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    if vendor.get("contact_type") == "customer":
        raise HTTPException(status_code=400, detail="Cannot create bill for customer-only contact")
    
    bill_id = generate_id("BILL")
    bill_number = bill.bill_number or await get_next_bill_number()
    
    org_state = "DL"
    vendor_state = bill.place_of_supply or vendor.get("place_of_supply", "")
    is_igst = vendor_state and vendor_state != org_state
    
    calculated_items = []
    for item in bill.line_items:
        calc = calculate_line_item(item, is_igst)
        calc["line_item_id"] = generate_id("LI")
        calc["bill_id"] = bill_id
        calculated_items.append(calc)
    
    totals = calculate_totals(calculated_items, bill.discount_type, bill.discount_value, bill.tds_rate if bill.tds_applicable else 0)
    
    bill_date = bill.bill_date or datetime.now(timezone.utc).date().isoformat()
    due_date = bill.due_date or (datetime.fromisoformat(bill_date) + timedelta(days=bill.payment_terms)).date().isoformat()
    
    bill_doc = {
        "bill_id": bill_id,
        "bill_number": bill_number,
        "vendor_id": bill.vendor_id,
        "vendor_name": vendor.get("name", ""),
        "vendor_gstin": vendor.get("gstin", ""),
        "reference_number": bill.reference_number,
        "purchase_order_id": bill.purchase_order_id,
        "bill_date": bill_date,
        "due_date": due_date,
        "payment_terms": bill.payment_terms,
        "place_of_supply": vendor_state,
        "is_inclusive_tax": bill.is_inclusive_tax,
        "reverse_charge": bill.reverse_charge,
        "discount_type": bill.discount_type,
        "discount_value": bill.discount_value,
        "tds_applicable": bill.tds_applicable,
        **totals,
        "amount_paid": 0,
        "status": "draft",
        "vendor_notes": bill.vendor_notes,
        "custom_fields": bill.custom_fields,
        "payment_count": 0,
        "last_payment_date": None,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await bills_collection.insert_one(bill_doc)
    for item in calculated_items:
        await bill_line_items_collection.insert_one(item)
    
    await add_bill_history(bill_id, "created", f"Bill {bill_number} created")
    
    bill_doc.pop("_id", None)
    for item in calculated_items:
        item.pop("_id", None)
    bill_doc["line_items"] = calculated_items
    return {"code": 0, "message": "Bill created", "bill": bill_doc}

@router.get("/")
async def list_bills(
    vendor_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    overdue_only: bool = False,
    sort_by: str = "bill_date",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List bills with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {}
    if vendor_id:
        query["vendor_id"] = vendor_id
    if status:
        query["status"] = status
    elif not overdue_only:
        query["status"] = {"$ne": "void"}
    if overdue_only:
        query["status"] = "overdue"
    if search:
        query["$or"] = [
            {"bill_number": {"$regex": search, "$options": "i"}},
            {"vendor_name": {"$regex": search, "$options": "i"}},
            {"reference_number": {"$regex": search, "$options": "i"}}
        ]

    total = await bills_collection.count_documents(query)
    skip = (page - 1) * limit
    sort_dir = -1 if sort_order == "desc" else 1
    total_pages = math.ceil(total / limit) if total > 0 else 1

    bills = await bills_collection.find(query, {"_id": 0}).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)

    return {
        "data": bills,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

# ========================= REPORTS (Before dynamic routes) =========================

@router.get("/aging-report")
async def get_payables_aging():
    """Get payables aging report"""
    today = datetime.now(timezone.utc).date()
    
    bills = await bills_collection.find(
        {"status": {"$in": ["open", "overdue", "partially_paid"]}, "balance_due": {"$gt": 0}},
        {"_id": 0, "due_date": 1, "balance_due": 1}
    ).to_list(2000)
    
    aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    
    for bill in bills:
        due_str = bill.get("due_date", "")
        if not due_str:
            continue
        try:
            due = datetime.fromisoformat(due_str.replace('Z', '+00:00')).date()
            days = (today - due).days
            balance = bill.get("balance_due", 0)
            
            if days <= 0:
                aging["current"] += balance
            elif days <= 30:
                aging["1_30"] += balance
            elif days <= 60:
                aging["31_60"] += balance
            elif days <= 90:
                aging["61_90"] += balance
            else:
                aging["over_90"] += balance
        except:
            continue
    
    return {"code": 0, "report": {k: round_currency(v) for k, v in aging.items()}, "total": round_currency(sum(aging.values()))}

@router.get("/vendor-wise")
async def get_vendor_wise_report(limit: int = 20):
    """Get vendor-wise payables report"""
    pipeline = [
        {"$match": {"status": {"$ne": "void"}}},
        {"$group": {"_id": "$vendor_id", "vendor_name": {"$first": "$vendor_name"}, "bill_count": {"$sum": 1}, "total_billed": {"$sum": "$grand_total"}, "total_payable": {"$sum": "$balance_due"}}},
        {"$sort": {"total_payable": -1}},
        {"$limit": limit}
    ]
    
    results = await bills_collection.aggregate(pipeline).to_list(limit)
    return {"code": 0, "report": [{"vendor_id": r["_id"], "vendor_name": r.get("vendor_name", "Unknown"), "bill_count": r["bill_count"], "total_billed": round_currency(r["total_billed"]), "total_payable": round_currency(r["total_payable"])} for r in results]}

@router.get("/{bill_id}")
async def get_bill(bill_id: str):
    bill = await bills_collection.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    line_items = await bill_line_items_collection.find({"bill_id": bill_id}, {"_id": 0}).to_list(100)
    bill["line_items"] = line_items
    
    payments = await bill_payments_collection.find({"bill_id": bill_id}, {"_id": 0}).sort("payment_date", -1).to_list(50)
    bill["payments"] = payments
    
    history = await bill_history_collection.find({"bill_id": bill_id}, {"_id": 0}).sort("timestamp", -1).limit(20).to_list(20)
    bill["history"] = history
    
    return {"code": 0, "bill": bill}

@router.put("/{bill_id}")
async def update_bill(bill_id: str, update: BillUpdate):
    existing = await bills_collection.find_one({"bill_id": bill_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    if existing.get("status") not in ["draft"]:
        allowed = {"vendor_notes"}
        update_dict = {k: v for k, v in update.dict().items() if v is not None and k in allowed}
    else:
        update_dict = {k: v for k, v in update.dict().items() if v is not None}
        
        if update.line_items:
            await bill_line_items_collection.delete_many({"bill_id": bill_id})
            
            vendor = await contacts_collection.find_one({"contact_id": existing.get("vendor_id")})
            vendor_state = existing.get("place_of_supply", "")
            is_igst = vendor_state and vendor_state != "DL"
            
            calculated_items = []
            for item in update.line_items:
                calc = calculate_line_item(item, is_igst)
                calc["line_item_id"] = generate_id("LI")
                calc["bill_id"] = bill_id
                calculated_items.append(calc)
                await bill_line_items_collection.insert_one(calc)
            
            totals = calculate_totals(
                calculated_items,
                update.discount_type or existing.get("discount_type", "percentage"),
                update.discount_value if update.discount_value is not None else existing.get("discount_value", 0),
                update.tds_rate if update.tds_rate is not None else existing.get("tds_rate", 0)
            )
            update_dict.update(totals)
            del update_dict["line_items"]
    
    if update_dict:
        update_dict["updated_time"] = datetime.now(timezone.utc).isoformat()
        await bills_collection.update_one({"bill_id": bill_id}, {"$set": update_dict})
    
    await add_bill_history(bill_id, "updated", "Bill updated")
    updated = await bills_collection.find_one({"bill_id": bill_id}, {"_id": 0})
    return {"code": 0, "message": "Bill updated", "bill": updated}

@router.delete("/{bill_id}")
async def delete_bill(bill_id: str, force: bool = False):
    bill = await bills_collection.find_one({"bill_id": bill_id})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    payment_count = await bill_payments_collection.count_documents({"bill_id": bill_id})
    
    if payment_count > 0:
        if force:
            await bills_collection.update_one({"bill_id": bill_id}, {"$set": {"status": "void", "balance_due": 0}})
            await add_bill_history(bill_id, "voided", "Bill voided")
            await update_vendor_balance(bill["vendor_id"])
            return {"code": 0, "message": "Bill voided (has payments)", "voided": True}
        raise HTTPException(status_code=400, detail="Cannot delete bill with payments. Use force=true to void.")
    
    if bill.get("status") not in ["draft"]:
        if force:
            await bills_collection.update_one({"bill_id": bill_id}, {"$set": {"status": "void"}})
            await add_bill_history(bill_id, "voided", "Bill voided")
            await update_vendor_balance(bill["vendor_id"])
            return {"code": 0, "message": "Bill voided", "voided": True}
        raise HTTPException(status_code=400, detail="Only draft bills can be deleted. Use force=true to void.")
    
    await bill_line_items_collection.delete_many({"bill_id": bill_id})
    await bill_history_collection.delete_many({"bill_id": bill_id})
    await bills_collection.delete_one({"bill_id": bill_id})
    
    return {"code": 0, "message": "Bill deleted"}

# ========================= BILL ACTIONS =========================

@router.post("/{bill_id}/open")
async def open_bill(bill_id: str):
    bill = await bills_collection.find_one({"bill_id": bill_id})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft bills can be opened")
    
    await bills_collection.update_one({"bill_id": bill_id}, {"$set": {"status": "open", "updated_time": datetime.now(timezone.utc).isoformat()}})
    await add_bill_history(bill_id, "opened", "Bill marked as open")
    await update_vendor_balance(bill["vendor_id"])
    
    org_id = bill.get("organization_id", "")
    
    # Update inventory for line items (Fix 2: Bill → Inventory)
    if org_id:
        try:
            line_items = await bill_line_items_collection.find(
                {"bill_id": bill_id},
                {"_id": 0}
            ).to_list(100)
            
            inventory_service = get_inventory_service()
            inventory_result = await inventory_service.receive_from_bill(
                bill_id=bill_id,
                bill_number=bill.get("bill_number", ""),
                line_items=line_items,
                organization_id=org_id,
                user_id="system"  # Could be enhanced to pass actual user
            )
            logger.info(f"Inventory updated for bill {bill.get('bill_number')}: {inventory_result.get('items_updated', [])}")
        except Exception as e:
            logger.warning(f"Failed to update inventory for bill {bill.get('bill_number')}: {e}")
    
    # Post journal entry for double-entry bookkeeping
    if org_id:
        try:
            await post_bill_journal_entry(org_id, bill)
            logger.info(f"Posted journal entry for bill {bill.get('bill_number')}")
        except Exception as e:
            logger.warning(f"Failed to post journal entry for bill {bill.get('bill_number')}: {e}")
    
    return {"code": 0, "message": "Bill opened"}

@router.post("/{bill_id}/void")
async def void_bill(bill_id: str, reason: str = ""):
    bill = await bills_collection.find_one({"bill_id": bill_id})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.get("status") == "void":
        raise HTTPException(status_code=400, detail="Bill already voided")
    
    await bills_collection.update_one({"bill_id": bill_id}, {"$set": {"status": "void", "balance_due": 0, "void_reason": reason}})
    await add_bill_history(bill_id, "voided", f"Bill voided. Reason: {reason or 'Not specified'}")
    await update_vendor_balance(bill["vendor_id"])
    
    return {"code": 0, "message": "Bill voided"}

@router.post("/{bill_id}/clone")
async def clone_bill(bill_id: str):
    bill = await bills_collection.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    line_items = await bill_line_items_collection.find({"bill_id": bill_id}, {"_id": 0, "line_item_id": 0, "bill_id": 0}).to_list(100)
    
    new_id = generate_id("BILL")
    new_number = await get_next_bill_number()
    
    new_bill = {
        **bill,
        "bill_id": new_id,
        "bill_number": new_number,
        "bill_date": datetime.now(timezone.utc).date().isoformat(),
        "due_date": (datetime.now(timezone.utc) + timedelta(days=bill.get("payment_terms", 30))).date().isoformat(),
        "status": "draft",
        "amount_paid": 0,
        "balance_due": bill.get("grand_total", 0),
        "payment_count": 0,
        "last_payment_date": None,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await bills_collection.insert_one(new_bill)
    
    for item in line_items:
        item["line_item_id"] = generate_id("LI")
        item["bill_id"] = new_id
        await bill_line_items_collection.insert_one(item)
    
    await add_bill_history(new_id, "created", f"Bill cloned from {bill.get('bill_number')}")
    
    new_bill.pop("_id", None)
    return {"code": 0, "message": "Bill cloned", "bill": new_bill}

# ========================= PAYMENTS =========================

@router.get("/{bill_id}/payments")
async def get_bill_payments(bill_id: str):
    bill = await bills_collection.find_one({"bill_id": bill_id})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    payments = await bill_payments_collection.find({"bill_id": bill_id}, {"_id": 0}).sort("payment_date", -1).to_list(100)
    return {"code": 0, "payments": payments, "total_paid": bill.get("amount_paid", 0), "balance_due": bill.get("balance_due", 0)}

@router.post("/{bill_id}/payments")
async def record_bill_payment(bill_id: str, payment: PaymentCreate):
    bill = await bills_collection.find_one({"bill_id": bill_id})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.get("status") in ["void", "paid"]:
        raise HTTPException(status_code=400, detail=f"Cannot record payment for {bill.get('status')} bill")
    
    balance = bill.get("balance_due", 0)
    if payment.amount > balance:
        raise HTTPException(status_code=400, detail=f"Payment amount exceeds balance due ({balance})")
    
    payment_id = generate_id("PAY")
    payment_doc = {
        "payment_id": payment_id,
        "bill_id": bill_id,
        "vendor_id": bill.get("vendor_id"),
        "bill_number": bill.get("bill_number"),
        "amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "reference_number": payment.reference_number,
        "payment_date": payment.payment_date or datetime.now(timezone.utc).date().isoformat(),
        "notes": payment.notes,
        "paid_from_account": payment.paid_from_account,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await bill_payments_collection.insert_one(payment_doc)
    
    new_paid = bill.get("amount_paid", 0) + payment.amount
    new_balance = bill.get("grand_total", 0) - new_paid
    new_status = "paid" if new_balance <= 0 else "partially_paid"
    
    await bills_collection.update_one(
        {"bill_id": bill_id},
        {"$set": {
            "amount_paid": new_paid,
            "balance_due": max(0, new_balance),
            "status": new_status,
            "payment_count": bill.get("payment_count", 0) + 1,
            "last_payment_date": payment_doc["payment_date"]
        }}
    )
    
    await add_bill_history(bill_id, "payment_made", f"Payment of ₹{payment.amount:,.2f} made via {payment.payment_mode}")
    await update_vendor_balance(bill["vendor_id"])
    
    # Post journal entry for double-entry bookkeeping
    org_id = bill.get("organization_id", "")
    if org_id:
        try:
            await post_bill_payment_journal_entry(
                org_id,
                {
                    **payment_doc,
                    "vendor_name": bill.get("vendor_name", ""),
                    "bill_number": bill.get("bill_number", "")
                }
            )
            logger.info(f"Posted journal entry for bill payment {payment_id}")
        except Exception as e:
            logger.warning(f"Failed to post journal entry for bill payment: {e}")
    
    payment_doc.pop("_id", None)
    return {"code": 0, "message": "Payment recorded", "payment": payment_doc, "new_balance": max(0, new_balance), "new_status": new_status}

@router.delete("/{bill_id}/payments/{payment_id}")
async def delete_bill_payment(bill_id: str, payment_id: str):
    bill = await bills_collection.find_one({"bill_id": bill_id})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    payment = await bill_payments_collection.find_one({"payment_id": payment_id, "bill_id": bill_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    await bill_payments_collection.delete_one({"payment_id": payment_id})
    
    new_paid = bill.get("amount_paid", 0) - payment.get("amount", 0)
    new_balance = bill.get("grand_total", 0) - new_paid
    
    await bills_collection.update_one(
        {"bill_id": bill_id},
        {"$set": {
            "amount_paid": max(0, new_paid),
            "balance_due": new_balance,
            "status": "open" if new_paid == 0 else "partially_paid",
            "payment_count": max(0, bill.get("payment_count", 1) - 1)
        }}
    )
    
    await add_bill_history(bill_id, "payment_deleted", f"Payment of ₹{payment.get('amount', 0):,.2f} deleted")
    await update_vendor_balance(bill["vendor_id"])
    
    return {"code": 0, "message": "Payment deleted", "new_balance": new_balance}
