"""
Complete Zoho Books-like ERP Module
Handles: Quotes, Sales Orders, Invoices, Credit Notes, Purchase Orders, Bills, 
         Payments, Expenses, Banking, Journal Entries, Inventory Adjustments
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from enum import Enum
import os

router = APIRouter(prefix="/erp", tags=["ERP Operations"])

# Database connection
def get_db():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]

# ============== ENUMS ==============

class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    INVOICED = "invoiced"

class SalesOrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    CLOSED = "closed"
    VOID = "void"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"

class PurchaseOrderStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_BILLED = "partially_billed"
    BILLED = "billed"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class BillStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"

class PaymentMode(str, Enum):
    CASH = "Cash"
    UPI = "UPI"
    BANK_TRANSFER = "Bank Transfer"
    CHEQUE = "Cheque"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"

# ============== LINE ITEM MODEL ==============

class LineItem(BaseModel):
    item_id: str
    item_name: str
    item_type: str = "service"  # service or goods
    hsn_sac: Optional[str] = ""
    quantity: float = 1
    rate: float
    discount_percent: float = 0
    discount_amount: float = 0
    tax_rate: float = 18.0
    tax_type: str = "GST"  # GST, IGST, CGST+SGST
    description: Optional[str] = ""

# ============== QUOTE MODELS ==============

class QuoteCreate(BaseModel):
    customer_id: str
    customer_name: str
    reference_number: Optional[str] = ""
    quote_date: Optional[str] = None
    expiry_date: Optional[str] = None
    line_items: List[LineItem]
    place_of_supply: str = "DL"
    gst_treatment: str = "business_gst"
    discount_type: str = "item_level"  # item_level or entity_level
    entity_discount_percent: float = 0
    shipping_charge: float = 0
    adjustment: float = 0
    adjustment_description: str = ""
    notes: Optional[str] = ""
    terms: Optional[str] = ""

# ============== SALES ORDER MODELS ==============

class SalesOrderCreate(BaseModel):
    customer_id: str
    customer_name: str
    reference_number: Optional[str] = ""
    order_date: Optional[str] = None
    expected_shipment_date: Optional[str] = None
    line_items: List[LineItem]
    place_of_supply: str = "DL"
    gst_treatment: str = "business_gst"
    discount_type: str = "item_level"
    entity_discount_percent: float = 0
    shipping_charge: float = 0
    adjustment: float = 0
    notes: Optional[str] = ""
    terms: Optional[str] = ""
    from_quote_id: Optional[str] = None

# ============== PURCHASE ORDER MODELS ==============

class PurchaseOrderCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    reference_number: Optional[str] = ""
    order_date: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    line_items: List[LineItem]
    source_of_supply: str = "DL"
    destination_of_supply: str = "DL"
    gst_treatment: str = "business_gst"
    shipping_charge: float = 0
    adjustment: float = 0
    notes: Optional[str] = ""
    terms: Optional[str] = ""

# ============== BILL MODELS ==============

class BillCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    bill_number: str
    bill_date: Optional[str] = None
    due_date: Optional[str] = None
    line_items: List[LineItem]
    source_of_supply: str = "DL"
    destination_of_supply: str = "DL"
    gst_treatment: str = "business_gst"
    shipping_charge: float = 0
    adjustment: float = 0
    notes: Optional[str] = ""
    from_po_id: Optional[str] = None

# ============== CREDIT NOTE MODELS ==============

class CreditNoteCreate(BaseModel):
    customer_id: str
    customer_name: str
    invoice_id: Optional[str] = None
    credit_note_date: Optional[str] = None
    reason: str
    line_items: List[LineItem]
    place_of_supply: str = "DL"
    notes: Optional[str] = ""

# ============== PAYMENT MODELS ==============

class PaymentCreate(BaseModel):
    entity_type: str  # customer or vendor
    entity_id: str
    entity_name: str
    amount: float
    payment_mode: str = "Cash"
    payment_date: Optional[str] = None
    reference_number: Optional[str] = ""
    bank_account: Optional[str] = ""
    deposit_to: Optional[str] = ""
    invoice_ids: List[str] = []  # For customer payments
    bill_ids: List[str] = []  # For vendor payments
    notes: Optional[str] = ""

# ============== EXPENSE MODELS ==============

class ExpenseCreate(BaseModel):
    expense_date: Optional[str] = None
    expense_account: str
    amount: float
    paid_through: str
    vendor_id: Optional[str] = ""
    vendor_name: Optional[str] = ""
    reference_number: Optional[str] = ""
    description: Optional[str] = ""
    is_billable: bool = False
    customer_id: Optional[str] = ""
    project_id: Optional[str] = ""
    gst_treatment: str = "out_of_scope"
    tax_rate: float = 0

# ============== JOURNAL ENTRY MODELS ==============

class JournalLine(BaseModel):
    account_id: str
    account_name: str
    debit: float = 0
    credit: float = 0
    description: Optional[str] = ""

class JournalEntryCreate(BaseModel):
    journal_date: Optional[str] = None
    reference_number: Optional[str] = ""
    notes: Optional[str] = ""
    lines: List[JournalLine]

# ============== INVENTORY ADJUSTMENT ==============

class InventoryAdjustmentCreate(BaseModel):
    adjustment_date: Optional[str] = None
    adjustment_type: str  # quantity or value
    reason: str
    reference_number: Optional[str] = ""
    description: Optional[str] = ""
    items: List[Dict[str, Any]]  # [{item_id, item_name, quantity_adjusted, new_quantity}]

# ============== HELPER FUNCTIONS ==============

def calculate_line_totals(line_items: List[LineItem], entity_discount_percent: float = 0, 
                          shipping_charge: float = 0, adjustment: float = 0):
    """Calculate all totals for a transaction"""
    subtotal = 0
    discount_total = 0
    tax_total = 0
    calculated_items = []
    
    for item in line_items:
        item_subtotal = item.quantity * item.rate
        
        # Item-level discount
        if item.discount_percent > 0:
            item_discount = item_subtotal * (item.discount_percent / 100)
        else:
            item_discount = item.discount_amount
        
        taxable_amount = item_subtotal - item_discount
        item_tax = taxable_amount * (item.tax_rate / 100)
        
        calculated_items.append({
            **item.dict(),
            "subtotal": round(item_subtotal, 2),
            "discount_amount": round(item_discount, 2),
            "taxable_amount": round(taxable_amount, 2),
            "tax_amount": round(item_tax, 2),
            "total": round(taxable_amount + item_tax, 2)
        })
        
        subtotal += taxable_amount
        discount_total += item_discount
        tax_total += item_tax
    
    # Entity-level discount
    entity_discount = subtotal * (entity_discount_percent / 100) if entity_discount_percent > 0 else 0
    
    grand_total = subtotal - entity_discount + tax_total + shipping_charge + adjustment
    
    return {
        "line_items": calculated_items,
        "subtotal": round(subtotal, 2),
        "discount_total": round(discount_total + entity_discount, 2),
        "tax_total": round(tax_total, 2),
        "shipping_charge": round(shipping_charge, 2),
        "adjustment": round(adjustment, 2),
        "total": round(grand_total, 2)
    }

async def get_next_number(db, collection: str, prefix: str):
    """Get next sequential number for a document type"""
    last_doc = await db[collection].find_one(sort=[(f"{prefix.lower()}_number", -1)])
    if last_doc and f"{prefix.lower()}_number" in last_doc:
        try:
            num = int(last_doc[f"{prefix.lower()}_number"].split("-")[1]) + 1
        except:
            num = await db[collection].count_documents({}) + 1
    else:
        num = 1
    return f"{prefix}-{str(num).zfill(6)}"

# ============== QUOTES API ==============

@router.get("/quotes")
async def list_quotes(
    skip: int = 0,
    limit: int = 50,
    status: str = "",
    customer_id: str = ""
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.quotes.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    quotes = await cursor.to_list(length=limit)
    total = await db.quotes.count_documents(query)
    return {"quotes": quotes, "total": total}

@router.post("/quotes")
async def create_quote(quote: QuoteCreate):
    db = get_db()
    
    # Calculate totals
    totals = calculate_line_totals(
        quote.line_items, 
        quote.entity_discount_percent,
        quote.shipping_charge,
        quote.adjustment
    )
    
    quote_number = await get_next_number(db, "quotes", "QT")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    
    quote_dict = {
        "quote_id": f"QT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "quote_number": quote_number,
        "customer_id": quote.customer_id,
        "customer_name": quote.customer_name,
        "reference_number": quote.reference_number,
        "quote_date": quote.quote_date or today,
        "expiry_date": quote.expiry_date or expiry,
        "status": QuoteStatus.DRAFT.value,
        "place_of_supply": quote.place_of_supply,
        "gst_treatment": quote.gst_treatment,
        "discount_type": quote.discount_type,
        "entity_discount_percent": quote.entity_discount_percent,
        "adjustment_description": quote.adjustment_description,
        "notes": quote.notes,
        "terms": quote.terms,
        **totals,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.quotes.insert_one(quote_dict)
    del quote_dict["_id"]
    return quote_dict

@router.get("/quotes/{quote_id}")
async def get_quote(quote_id: str):
    db = get_db()
    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.put("/quotes/{quote_id}/status")
async def update_quote_status(quote_id: str, status: str):
    db = get_db()
    valid = [s.value for s in QuoteStatus]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be: {valid}")
    
    result = await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"message": f"Quote status updated to {status}"}

@router.post("/quotes/{quote_id}/convert-to-salesorder")
async def convert_quote_to_salesorder(quote_id: str):
    db = get_db()
    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Create Sales Order from Quote
    so_number = await get_next_number(db, "sales_orders", "SO")
    
    so_dict = {
        "salesorder_id": f"SO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "salesorder_number": so_number,
        "customer_id": quote["customer_id"],
        "customer_name": quote["customer_name"],
        "reference_number": quote.get("reference_number", ""),
        "order_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "expected_shipment_date": (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
        "status": SalesOrderStatus.CONFIRMED.value,
        "from_quote_id": quote_id,
        "from_quote_number": quote["quote_number"],
        "place_of_supply": quote["place_of_supply"],
        "gst_treatment": quote["gst_treatment"],
        "line_items": quote["line_items"],
        "subtotal": quote["subtotal"],
        "discount_total": quote["discount_total"],
        "tax_total": quote["tax_total"],
        "shipping_charge": quote["shipping_charge"],
        "adjustment": quote["adjustment"],
        "total": quote["total"],
        "invoiced_amount": 0,
        "notes": quote.get("notes", ""),
        "terms": quote.get("terms", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sales_orders.insert_one(so_dict)
    
    # Update quote status
    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": QuoteStatus.ACCEPTED.value}}
    )
    
    del so_dict["_id"]
    return so_dict

@router.post("/quotes/{quote_id}/convert-to-invoice")
async def convert_quote_to_invoice(quote_id: str):
    db = get_db()
    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Create Invoice from Quote
    inv_number = await get_next_number(db, "books_invoices", "INV")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    inv_dict = {
        "invoice_id": f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "invoice_number": inv_number,
        "customer_id": quote["customer_id"],
        "customer_name": quote["customer_name"],
        "invoice_date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d"),
        "status": InvoiceStatus.DRAFT.value,
        "from_quote_id": quote_id,
        "from_quote_number": quote["quote_number"],
        "place_of_supply": quote["place_of_supply"],
        "gst_treatment": quote["gst_treatment"],
        "line_items": quote["line_items"],
        "subtotal": quote["subtotal"],
        "discount_total": quote["discount_total"],
        "tax_total": quote["tax_total"],
        "shipping_charge": quote["shipping_charge"],
        "adjustment": quote["adjustment"],
        "total": quote["total"],
        "balance_due": quote["total"],
        "amount_paid": 0,
        "notes": quote.get("notes", ""),
        "terms": quote.get("terms", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.books_invoices.insert_one(inv_dict)
    
    # Update quote status
    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": QuoteStatus.INVOICED.value}}
    )
    
    # Update customer outstanding
    await db.books_customers.update_one(
        {"customer_id": quote["customer_id"]},
        {"$inc": {"outstanding_balance": inv_dict["total"]}}
    )
    
    del inv_dict["_id"]
    return inv_dict

# ============== SALES ORDERS API ==============

@router.get("/sales-orders")
async def list_sales_orders(
    skip: int = 0,
    limit: int = 50,
    status: str = "",
    customer_id: str = ""
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.sales_orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    total = await db.sales_orders.count_documents(query)
    return {"sales_orders": orders, "total": total}

@router.post("/sales-orders")
async def create_sales_order(order: SalesOrderCreate):
    db = get_db()
    
    totals = calculate_line_totals(
        order.line_items,
        order.entity_discount_percent,
        order.shipping_charge,
        order.adjustment
    )
    
    so_number = await get_next_number(db, "sales_orders", "SO")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    so_dict = {
        "salesorder_id": f"SO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "salesorder_number": so_number,
        "customer_id": order.customer_id,
        "customer_name": order.customer_name,
        "reference_number": order.reference_number,
        "order_date": order.order_date or today,
        "expected_shipment_date": order.expected_shipment_date or (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
        "status": SalesOrderStatus.DRAFT.value,
        "from_quote_id": order.from_quote_id,
        "place_of_supply": order.place_of_supply,
        "gst_treatment": order.gst_treatment,
        "notes": order.notes,
        "terms": order.terms,
        **totals,
        "invoiced_amount": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sales_orders.insert_one(so_dict)
    del so_dict["_id"]
    return so_dict

@router.get("/sales-orders/{so_id}")
async def get_sales_order(so_id: str):
    db = get_db()
    order = await db.sales_orders.find_one({"salesorder_id": so_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    return order

@router.put("/sales-orders/{so_id}/status")
async def update_sales_order_status(so_id: str, status: str):
    db = get_db()
    valid = [s.value for s in SalesOrderStatus]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be: {valid}")
    
    result = await db.sales_orders.update_one(
        {"salesorder_id": so_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    return {"message": f"Sales Order status updated to {status}"}

@router.post("/sales-orders/{so_id}/convert-to-invoice")
async def convert_salesorder_to_invoice(so_id: str, partial_items: List[Dict] = None):
    db = get_db()
    order = await db.sales_orders.find_one({"salesorder_id": so_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    
    # Use all items or partial items
    items_to_invoice = partial_items if partial_items else order["line_items"]
    
    # Recalculate totals for selected items
    totals = calculate_line_totals(
        [LineItem(**item) for item in items_to_invoice],
        0, order.get("shipping_charge", 0), order.get("adjustment", 0)
    )
    
    inv_number = await get_next_number(db, "books_invoices", "INV")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    inv_dict = {
        "invoice_id": f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "invoice_number": inv_number,
        "customer_id": order["customer_id"],
        "customer_name": order["customer_name"],
        "invoice_date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d"),
        "status": InvoiceStatus.DRAFT.value,
        "from_salesorder_id": so_id,
        "from_salesorder_number": order["salesorder_number"],
        "place_of_supply": order["place_of_supply"],
        "gst_treatment": order["gst_treatment"],
        **totals,
        "balance_due": totals["total"],
        "amount_paid": 0,
        "notes": order.get("notes", ""),
        "terms": order.get("terms", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.books_invoices.insert_one(inv_dict)
    
    # Update Sales Order
    new_invoiced = order.get("invoiced_amount", 0) + totals["total"]
    new_status = SalesOrderStatus.INVOICED.value if new_invoiced >= order["total"] else SalesOrderStatus.PARTIALLY_INVOICED.value
    
    await db.sales_orders.update_one(
        {"salesorder_id": so_id},
        {"$set": {"status": new_status, "invoiced_amount": new_invoiced}}
    )
    
    # Update customer outstanding
    await db.books_customers.update_one(
        {"customer_id": order["customer_id"]},
        {"$inc": {"outstanding_balance": totals["total"]}}
    )
    
    del inv_dict["_id"]
    return inv_dict

# ============== PURCHASE ORDERS API ==============

@router.get("/purchase-orders")
async def list_purchase_orders(
    skip: int = 0,
    limit: int = 50,
    status: str = "",
    vendor_id: str = ""
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    cursor = db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    total = await db.purchase_orders.count_documents(query)
    return {"purchase_orders": orders, "total": total}

@router.post("/purchase-orders")
async def create_purchase_order(order: PurchaseOrderCreate):
    db = get_db()
    
    totals = calculate_line_totals(
        order.line_items, 0,
        order.shipping_charge,
        order.adjustment
    )
    
    po_number = await get_next_number(db, "purchase_orders", "PO")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    po_dict = {
        "po_id": f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "po_number": po_number,
        "vendor_id": order.vendor_id,
        "vendor_name": order.vendor_name,
        "reference_number": order.reference_number,
        "order_date": order.order_date or today,
        "expected_delivery_date": order.expected_delivery_date,
        "status": PurchaseOrderStatus.DRAFT.value,
        "source_of_supply": order.source_of_supply,
        "destination_of_supply": order.destination_of_supply,
        "gst_treatment": order.gst_treatment,
        "notes": order.notes,
        "terms": order.terms,
        **totals,
        "billed_amount": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.purchase_orders.insert_one(po_dict)
    del po_dict["_id"]
    return po_dict

@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str):
    db = get_db()
    order = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return order

@router.put("/purchase-orders/{po_id}/status")
async def update_purchase_order_status(po_id: str, status: str):
    db = get_db()
    valid = [s.value for s in PurchaseOrderStatus]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be: {valid}")
    
    result = await db.purchase_orders.update_one(
        {"po_id": po_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return {"message": f"Purchase Order status updated to {status}"}

@router.post("/purchase-orders/{po_id}/convert-to-bill")
async def convert_po_to_bill(po_id: str, bill_number: str):
    db = get_db()
    order = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    bill_dict = {
        "bill_id": f"BILL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "bill_number": bill_number,
        "vendor_id": order["vendor_id"],
        "vendor_name": order["vendor_name"],
        "bill_date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "status": BillStatus.OPEN.value,
        "from_po_id": po_id,
        "from_po_number": order["po_number"],
        "source_of_supply": order["source_of_supply"],
        "destination_of_supply": order["destination_of_supply"],
        "gst_treatment": order["gst_treatment"],
        "line_items": order["line_items"],
        "subtotal": order["subtotal"],
        "discount_total": order["discount_total"],
        "tax_total": order["tax_total"],
        "shipping_charge": order["shipping_charge"],
        "adjustment": order["adjustment"],
        "total": order["total"],
        "balance_due": order["total"],
        "amount_paid": 0,
        "notes": order.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bills.insert_one(bill_dict)
    
    # Update PO status
    await db.purchase_orders.update_one(
        {"po_id": po_id},
        {"$set": {"status": PurchaseOrderStatus.BILLED.value, "billed_amount": order["total"]}}
    )
    
    # Update vendor outstanding
    await db.books_vendors.update_one(
        {"vendor_id": order["vendor_id"]},
        {"$inc": {"outstanding_balance": order["total"]}}
    )
    
    del bill_dict["_id"]
    return bill_dict

# ============== BILLS API ==============

@router.get("/bills")
async def list_bills(
    skip: int = 0,
    limit: int = 50,
    status: str = "",
    vendor_id: str = ""
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    cursor = db.bills.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    bills = await cursor.to_list(length=limit)
    total = await db.bills.count_documents(query)
    return {"bills": bills, "total": total}

@router.post("/bills")
async def create_bill(bill: BillCreate):
    db = get_db()
    
    totals = calculate_line_totals(
        bill.line_items, 0,
        bill.shipping_charge,
        bill.adjustment
    )
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    bill_dict = {
        "bill_id": f"BILL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "bill_number": bill.bill_number,
        "vendor_id": bill.vendor_id,
        "vendor_name": bill.vendor_name,
        "bill_date": bill.bill_date or today,
        "due_date": bill.due_date or (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "status": BillStatus.OPEN.value,
        "from_po_id": bill.from_po_id,
        "source_of_supply": bill.source_of_supply,
        "destination_of_supply": bill.destination_of_supply,
        "gst_treatment": bill.gst_treatment,
        "notes": bill.notes,
        **totals,
        "balance_due": totals["total"],
        "amount_paid": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bills.insert_one(bill_dict)
    
    # Update vendor outstanding
    await db.books_vendors.update_one(
        {"vendor_id": bill.vendor_id},
        {"$inc": {"outstanding_balance": totals["total"]}}
    )
    
    del bill_dict["_id"]
    return bill_dict

@router.get("/bills/{bill_id}")
async def get_bill(bill_id: str):
    db = get_db()
    bill = await db.bills.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

# ============== CREDIT NOTES API ==============

@router.get("/credit-notes")
async def list_credit_notes(skip: int = 0, limit: int = 50, customer_id: str = ""):
    db = get_db()
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.credit_notes.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    notes = await cursor.to_list(length=limit)
    total = await db.credit_notes.count_documents(query)
    return {"credit_notes": notes, "total": total}

@router.post("/credit-notes")
async def create_credit_note(cn: CreditNoteCreate):
    db = get_db()
    
    totals = calculate_line_totals(cn.line_items, 0, 0, 0)
    cn_number = await get_next_number(db, "credit_notes", "CN")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    cn_dict = {
        "creditnote_id": f"CN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "creditnote_number": cn_number,
        "customer_id": cn.customer_id,
        "customer_name": cn.customer_name,
        "invoice_id": cn.invoice_id,
        "credit_note_date": cn.credit_note_date or today,
        "reason": cn.reason,
        "status": "open",
        "place_of_supply": cn.place_of_supply,
        "notes": cn.notes,
        **totals,
        "balance": totals["total"],
        "credits_used": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.credit_notes.insert_one(cn_dict)
    
    # Update customer outstanding (reduce)
    await db.books_customers.update_one(
        {"customer_id": cn.customer_id},
        {"$inc": {"outstanding_balance": -totals["total"], "credits_available": totals["total"]}}
    )
    
    del cn_dict["_id"]
    return cn_dict

# ============== PAYMENTS API ==============

@router.get("/customer-payments")
async def list_customer_payments(skip: int = 0, limit: int = 50, customer_id: str = ""):
    db = get_db()
    query = {"entity_type": "customer"}
    if customer_id:
        query["entity_id"] = customer_id
    
    cursor = db.erp_payments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    payments = await cursor.to_list(length=limit)
    total = await db.erp_payments.count_documents(query)
    return {"payments": payments, "total": total}

@router.post("/customer-payments")
async def record_customer_payment(payment: PaymentCreate):
    db = get_db()
    
    pmt_number = await get_next_number(db, "erp_payments", "PMT")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    pmt_dict = {
        "payment_id": f"PMT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "payment_number": pmt_number,
        "entity_type": "customer",
        "entity_id": payment.entity_id,
        "entity_name": payment.entity_name,
        "amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "payment_date": payment.payment_date or today,
        "reference_number": payment.reference_number,
        "bank_account": payment.bank_account,
        "deposit_to": payment.deposit_to,
        "invoice_ids": payment.invoice_ids,
        "notes": payment.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.erp_payments.insert_one(pmt_dict)
    
    # Apply to invoices
    remaining = payment.amount
    for inv_id in payment.invoice_ids:
        if remaining <= 0:
            break
        invoice = await db.books_invoices.find_one({"invoice_id": inv_id})
        if invoice:
            to_apply = min(remaining, invoice.get("balance_due", 0))
            new_balance = invoice.get("balance_due", 0) - to_apply
            new_status = InvoiceStatus.PAID.value if new_balance <= 0 else InvoiceStatus.PARTIALLY_PAID.value
            
            await db.books_invoices.update_one(
                {"invoice_id": inv_id},
                {"$set": {"balance_due": new_balance, "status": new_status},
                 "$inc": {"amount_paid": to_apply}}
            )
            remaining -= to_apply
    
    # Update customer outstanding
    await db.books_customers.update_one(
        {"customer_id": payment.entity_id},
        {"$inc": {"outstanding_balance": -payment.amount}}
    )
    
    del pmt_dict["_id"]
    return pmt_dict

@router.get("/vendor-payments")
async def list_vendor_payments(skip: int = 0, limit: int = 50, vendor_id: str = ""):
    db = get_db()
    query = {"entity_type": "vendor"}
    if vendor_id:
        query["entity_id"] = vendor_id
    
    cursor = db.erp_payments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    payments = await cursor.to_list(length=limit)
    total = await db.erp_payments.count_documents(query)
    return {"payments": payments, "total": total}

@router.post("/vendor-payments")
async def record_vendor_payment(payment: PaymentCreate):
    db = get_db()
    
    pmt_number = await get_next_number(db, "erp_payments", "VPM")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    pmt_dict = {
        "payment_id": f"VPM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "payment_number": pmt_number,
        "entity_type": "vendor",
        "entity_id": payment.entity_id,
        "entity_name": payment.entity_name,
        "amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "payment_date": payment.payment_date or today,
        "reference_number": payment.reference_number,
        "bank_account": payment.bank_account,
        "bill_ids": payment.bill_ids,
        "notes": payment.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.erp_payments.insert_one(pmt_dict)
    
    # Apply to bills
    remaining = payment.amount
    for bill_id in payment.bill_ids:
        if remaining <= 0:
            break
        bill = await db.bills.find_one({"bill_id": bill_id})
        if bill:
            to_apply = min(remaining, bill.get("balance_due", 0))
            new_balance = bill.get("balance_due", 0) - to_apply
            new_status = BillStatus.PAID.value if new_balance <= 0 else BillStatus.PARTIALLY_PAID.value
            
            await db.bills.update_one(
                {"bill_id": bill_id},
                {"$set": {"balance_due": new_balance, "status": new_status},
                 "$inc": {"amount_paid": to_apply}}
            )
            remaining -= to_apply
    
    # Update vendor outstanding
    await db.books_vendors.update_one(
        {"vendor_id": payment.entity_id},
        {"$inc": {"outstanding_balance": -payment.amount}}
    )
    
    del pmt_dict["_id"]
    return pmt_dict

# ============== EXPENSES API ==============

@router.get("/expenses")
async def list_expenses(
    skip: int = 0,
    limit: int = 50,
    expense_account: str = "",
    vendor_id: str = ""
):
    db = get_db()
    query = {}
    if expense_account:
        query["expense_account"] = {"$regex": expense_account, "$options": "i"}
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    cursor = db.expenses.find(query, {"_id": 0}).sort("expense_date", -1).skip(skip).limit(limit)
    expenses = await cursor.to_list(length=limit)
    total = await db.expenses.count_documents(query)
    
    # Calculate totals
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    agg = await db.expenses.aggregate(pipeline).to_list(1)
    expense_total = agg[0]["total"] if agg else 0
    
    return {"expenses": expenses, "total": total, "expense_total": expense_total}

@router.post("/expenses")
async def create_expense(expense: ExpenseCreate):
    db = get_db()
    
    exp_number = await get_next_number(db, "expenses", "EXP")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Calculate tax
    tax_amount = expense.amount * (expense.tax_rate / 100) if expense.tax_rate > 0 else 0
    total = expense.amount + tax_amount
    
    exp_dict = {
        "expense_id": f"EXP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "expense_number": exp_number,
        "expense_date": expense.expense_date or today,
        "expense_account": expense.expense_account,
        "amount": expense.amount,
        "tax_rate": expense.tax_rate,
        "tax_amount": tax_amount,
        "total": total,
        "paid_through": expense.paid_through,
        "vendor_id": expense.vendor_id,
        "vendor_name": expense.vendor_name,
        "reference_number": expense.reference_number,
        "description": expense.description,
        "is_billable": expense.is_billable,
        "customer_id": expense.customer_id,
        "project_id": expense.project_id,
        "gst_treatment": expense.gst_treatment,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.expenses.insert_one(exp_dict)
    del exp_dict["_id"]
    return exp_dict

# ============== JOURNAL ENTRIES API ==============

@router.get("/journal-entries")
async def list_journal_entries(skip: int = 0, limit: int = 50):
    db = get_db()
    cursor = db.journal_entries.find({}, {"_id": 0}).sort("journal_date", -1).skip(skip).limit(limit)
    entries = await cursor.to_list(length=limit)
    total = await db.journal_entries.count_documents({})
    return {"journal_entries": entries, "total": total}

@router.post("/journal-entries")
async def create_journal_entry(entry: JournalEntryCreate):
    db = get_db()
    
    # Validate debits = credits
    total_debit = sum(line.debit for line in entry.lines)
    total_credit = sum(line.credit for line in entry.lines)
    
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail=f"Debits ({total_debit}) must equal Credits ({total_credit})")
    
    je_number = await get_next_number(db, "journal_entries", "JE")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    je_dict = {
        "journal_id": f"JE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "journal_number": je_number,
        "journal_date": entry.journal_date or today,
        "reference_number": entry.reference_number,
        "notes": entry.notes,
        "lines": [line.dict() for line in entry.lines],
        "total_debit": total_debit,
        "total_credit": total_credit,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal_entries.insert_one(je_dict)
    del je_dict["_id"]
    return je_dict

# ============== INVENTORY ADJUSTMENTS API ==============

@router.get("/inventory-adjustments")
async def list_inventory_adjustments(skip: int = 0, limit: int = 50):
    db = get_db()
    cursor = db.inventory_adjustments.find({}, {"_id": 0}).sort("adjustment_date", -1).skip(skip).limit(limit)
    adjustments = await cursor.to_list(length=limit)
    total = await db.inventory_adjustments.count_documents({})
    return {"adjustments": adjustments, "total": total}

@router.post("/inventory-adjustments")
async def create_inventory_adjustment(adj: InventoryAdjustmentCreate):
    db = get_db()
    
    adj_number = await get_next_number(db, "inventory_adjustments", "ADJ")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    adj_dict = {
        "adjustment_id": f"ADJ-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "adjustment_number": adj_number,
        "adjustment_date": adj.adjustment_date or today,
        "adjustment_type": adj.adjustment_type,
        "reason": adj.reason,
        "reference_number": adj.reference_number,
        "description": adj.description,
        "items": adj.items,
        "status": "adjusted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update part quantities
    for item in adj.items:
        if "quantity_adjusted" in item:
            await db.parts.update_one(
                {"item_id": item["item_id"]},
                {"$inc": {"stock_quantity": item["quantity_adjusted"]}}
            )
    
    await db.inventory_adjustments.insert_one(adj_dict)
    del adj_dict["_id"]
    return adj_dict

# ============== REPORTS API ==============

@router.get("/reports/receivables-aging")
async def get_receivables_aging():
    """Get aging report of customer receivables"""
    db = get_db()
    
    today = datetime.now(timezone.utc)
    
    # Get all unpaid invoices
    invoices = await db.books_invoices.find(
        {"balance_due": {"$gt": 0}},
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
        due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_overdue = (today - due_date).days
        balance = inv["balance_due"]
        customer = inv["customer_name"]
        
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
        "aging_summary": aging,
        "total_receivables": total_receivables,
        "customer_breakdown": customer_aging
    }

@router.get("/reports/payables-aging")
async def get_payables_aging():
    """Get aging report of vendor payables"""
    db = get_db()
    
    today = datetime.now(timezone.utc)
    
    bills = await db.bills.find(
        {"balance_due": {"$gt": 0}},
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
        due_date = datetime.strptime(bill["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_overdue = (today - due_date).days
        balance = bill["balance_due"]
        vendor = bill["vendor_name"]
        
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
        "aging_summary": aging,
        "total_payables": total_payables,
        "vendor_breakdown": vendor_aging
    }

@router.get("/reports/profit-loss")
async def get_profit_loss(start_date: str = "", end_date: str = ""):
    """Get Profit & Loss statement"""
    db = get_db()
    
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Revenue from invoices
    inv_pipeline = [
        {"$match": {"invoice_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "total_revenue": {"$sum": "$total"}, "tax_collected": {"$sum": "$tax_total"}}}
    ]
    inv_result = await db.books_invoices.aggregate(inv_pipeline).to_list(1)
    revenue = inv_result[0]["total_revenue"] if inv_result else 0
    tax_collected = inv_result[0]["tax_collected"] if inv_result else 0
    
    # Cost of goods from bills
    bill_pipeline = [
        {"$match": {"bill_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "total_cost": {"$sum": "$total"}, "tax_paid": {"$sum": "$tax_total"}}}
    ]
    bill_result = await db.bills.aggregate(bill_pipeline).to_list(1)
    cost_of_goods = bill_result[0]["total_cost"] if bill_result else 0
    tax_paid = bill_result[0]["tax_paid"] if bill_result else 0
    
    # Operating expenses
    exp_pipeline = [
        {"$match": {"expense_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": "$expense_account", "total": {"$sum": "$amount"}}}
    ]
    exp_result = await db.expenses.aggregate(exp_pipeline).to_list(100)
    expenses_by_category = {e["_id"]: e["total"] for e in exp_result}
    total_expenses = sum(expenses_by_category.values())
    
    gross_profit = revenue - cost_of_goods
    net_profit = gross_profit - total_expenses
    
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "revenue": {
            "total_revenue": revenue,
            "tax_collected": tax_collected
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
        "gross_margin_percent": (gross_profit / revenue * 100) if revenue > 0 else 0,
        "net_margin_percent": (net_profit / revenue * 100) if revenue > 0 else 0
    }

@router.get("/reports/gst-summary")
async def get_gst_summary(start_date: str = "", end_date: str = ""):
    """Get GST summary for filing"""
    db = get_db()
    
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Output GST (from sales invoices)
    inv_pipeline = [
        {"$match": {"invoice_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": None,
            "taxable_value": {"$sum": "$subtotal"},
            "total_gst": {"$sum": "$tax_total"},
            "invoice_count": {"$sum": 1}
        }}
    ]
    inv_result = await db.books_invoices.aggregate(inv_pipeline).to_list(1)
    
    # Input GST (from purchase bills)
    bill_pipeline = [
        {"$match": {"bill_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": None,
            "taxable_value": {"$sum": "$subtotal"},
            "total_gst": {"$sum": "$tax_total"},
            "bill_count": {"$sum": 1}
        }}
    ]
    bill_result = await db.bills.aggregate(bill_pipeline).to_list(1)
    
    output_gst = inv_result[0]["total_gst"] if inv_result else 0
    input_gst = bill_result[0]["total_gst"] if bill_result else 0
    net_gst_payable = output_gst - input_gst
    
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "gstr1_outward_supplies": {
            "taxable_value": inv_result[0]["taxable_value"] if inv_result else 0,
            "total_gst": output_gst,
            "invoice_count": inv_result[0]["invoice_count"] if inv_result else 0
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

@router.get("/reports/dashboard-summary")
async def get_dashboard_summary():
    """Get complete dashboard summary"""
    db = get_db()
    
    # Counts
    customers = await db.books_customers.count_documents({})
    vendors = await db.books_vendors.count_documents({})
    services = await db.service_items.count_documents({})
    parts = await db.parts.count_documents({})
    
    # Invoices
    invoices = await db.books_invoices.count_documents({})
    unpaid_invoices = await db.books_invoices.count_documents({"balance_due": {"$gt": 0}})
    
    # Revenue
    rev_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total"}, "collected": {"$sum": "$amount_paid"}}}]
    rev_result = await db.books_invoices.aggregate(rev_pipeline).to_list(1)
    total_revenue = rev_result[0]["total"] if rev_result else 0
    collected = rev_result[0]["collected"] if rev_result else 0
    
    # Bills
    bills = await db.bills.count_documents({})
    unpaid_bills = await db.bills.count_documents({"balance_due": {"$gt": 0}})
    
    # Payables
    pay_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total"}, "paid": {"$sum": "$amount_paid"}}}]
    pay_result = await db.bills.aggregate(pay_pipeline).to_list(1)
    total_payables = pay_result[0]["total"] if pay_result else 0
    paid = pay_result[0]["paid"] if pay_result else 0
    
    # Expenses
    exp_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    exp_result = await db.expenses.aggregate(exp_pipeline).to_list(1)
    total_expenses = exp_result[0]["total"] if exp_result else 0
    
    # Quotes & Sales Orders
    quotes = await db.quotes.count_documents({})
    open_quotes = await db.quotes.count_documents({"status": {"$in": ["draft", "sent"]}})
    sales_orders = await db.sales_orders.count_documents({})
    open_so = await db.sales_orders.count_documents({"status": {"$in": ["draft", "confirmed", "partially_invoiced"]}})
    
    # Purchase Orders
    purchase_orders = await db.purchase_orders.count_documents({})
    open_po = await db.purchase_orders.count_documents({"status": {"$in": ["draft", "issued", "partially_billed"]}})
    
    return {
        "master_data": {
            "customers": customers,
            "vendors": vendors,
            "services": services,
            "parts": parts
        },
        "sales": {
            "quotes": {"total": quotes, "open": open_quotes},
            "sales_orders": {"total": sales_orders, "open": open_so},
            "invoices": {"total": invoices, "unpaid": unpaid_invoices}
        },
        "purchases": {
            "purchase_orders": {"total": purchase_orders, "open": open_po},
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
