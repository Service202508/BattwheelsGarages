"""
Zoho Books-like Operations Module
Handles: Items, Customers, Vendors, Invoices, Payments, Chart of Accounts
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
import os

router = APIRouter(prefix="/api/books", tags=["Zoho Books Operations"])

# Get database from server
def get_db():
    from server import db
    return db

# ============== MODELS ==============

class ServiceItem(BaseModel):
    name: str
    sku: Optional[str] = ""
    hsn_sac: Optional[str] = ""
    rate: float = 0
    description: Optional[str] = ""
    type: str = "service"  # service or goods
    tax_rate: float = 18.0  # GST rate
    is_active: bool = True

class Part(BaseModel):
    name: str
    sku: Optional[str] = ""
    hsn_sac: Optional[str] = ""
    rate: float = 0
    description: Optional[str] = ""
    type: str = "goods"
    stock_quantity: int = 0
    reorder_level: int = 5
    tax_rate: float = 18.0
    is_active: bool = True

class Customer(BaseModel):
    display_name: str
    company_name: Optional[str] = ""
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    gstin: Optional[str] = ""
    billing_address: Optional[str] = ""
    billing_city: Optional[str] = ""
    billing_state: Optional[str] = ""
    billing_pincode: Optional[str] = ""
    payment_terms: int = 15  # days
    is_active: bool = True

class Vendor(BaseModel):
    display_name: str
    company_name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    gstin: Optional[str] = ""
    is_active: bool = True

class Account(BaseModel):
    name: str
    code: Optional[str] = ""
    type: str  # Expense, Income, Asset, Liability, Equity
    description: Optional[str] = ""
    parent: Optional[str] = ""
    is_active: bool = True

class InvoiceLineItem(BaseModel):
    item_id: str
    item_name: str
    quantity: float = 1
    rate: float
    discount_percent: float = 0
    tax_rate: float = 18.0

class Invoice(BaseModel):
    customer_id: str
    customer_name: str
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    line_items: List[InvoiceLineItem]
    place_of_supply: str = "DL"
    gst_treatment: str = "business_gst"
    notes: Optional[str] = ""
    terms: Optional[str] = ""

class Payment(BaseModel):
    customer_id: str
    customer_name: str
    amount: float
    payment_mode: str = "Cash"  # Cash, UPI, Bank Transfer
    reference_number: Optional[str] = ""
    invoice_ids: List[str] = []
    notes: Optional[str] = ""

# ============== SERVICE ITEMS ==============

@router.get("/services")
async def list_services(skip: int = 0, limit: int = 100, search: str = ""):
    db = get_db()
    query = {"type": "service"}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    items = list(db.service_items.find(query, {"_id": 0}).skip(skip).limit(limit))
    total = db.service_items.count_documents(query)
    return {"items": items, "total": total}

@router.post("/services")
async def create_service(item: ServiceItem):
    db = get_db()
    item_dict = item.dict()
    item_dict["item_id"] = f"SRV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    item_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    db.service_items.insert_one(item_dict)
    del item_dict["_id"]
    return item_dict

@router.put("/services/{item_id}")
async def update_service(item_id: str, item: ServiceItem):
    db = get_db()
    result = db.service_items.update_one(
        {"item_id": item_id},
        {"$set": item.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service updated"}

# ============== PARTS/INVENTORY ==============

@router.get("/parts")
async def list_parts(skip: int = 0, limit: int = 100, search: str = ""):
    db = get_db()
    query = {"type": "goods"}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    items = list(db.parts.find(query, {"_id": 0}).skip(skip).limit(limit))
    total = db.parts.count_documents(query)
    return {"items": items, "total": total}

@router.post("/parts")
async def create_part(part: Part):
    db = get_db()
    part_dict = part.dict()
    part_dict["item_id"] = f"PRT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    part_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    db.parts.insert_one(part_dict)
    del part_dict["_id"]
    return part_dict

@router.put("/parts/{item_id}")
async def update_part(item_id: str, part: Part):
    db = get_db()
    result = db.parts.update_one(
        {"item_id": item_id},
        {"$set": part.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Part not found")
    return {"message": "Part updated"}

@router.put("/parts/{item_id}/stock")
async def update_stock(item_id: str, quantity_change: int):
    db = get_db()
    result = db.parts.update_one(
        {"item_id": item_id},
        {"$inc": {"stock_quantity": quantity_change}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Part not found")
    return {"message": "Stock updated"}

# ============== CUSTOMERS ==============

@router.get("/customers")
async def list_customers(skip: int = 0, limit: int = 100, search: str = ""):
    db = get_db()
    query = {}
    if search:
        query["$or"] = [
            {"display_name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}}
        ]
    
    customers = list(db.books_customers.find(query, {"_id": 0}).skip(skip).limit(limit))
    total = db.books_customers.count_documents(query)
    return {"customers": customers, "total": total}

@router.post("/customers")
async def create_customer(customer: Customer):
    db = get_db()
    cust_dict = customer.dict()
    cust_dict["customer_id"] = f"CUST-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    cust_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    cust_dict["outstanding_balance"] = 0
    db.books_customers.insert_one(cust_dict)
    del cust_dict["_id"]
    return cust_dict

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    db = get_db()
    customer = db.books_customers.find_one({"customer_id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, customer: Customer):
    db = get_db()
    result = db.books_customers.update_one(
        {"customer_id": customer_id},
        {"$set": customer.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer updated"}

# ============== VENDORS ==============

@router.get("/vendors")
async def list_vendors(skip: int = 0, limit: int = 100, search: str = ""):
    db = get_db()
    query = {}
    if search:
        query["display_name"] = {"$regex": search, "$options": "i"}
    
    vendors = list(db.books_vendors.find(query, {"_id": 0}).skip(skip).limit(limit))
    total = db.books_vendors.count_documents(query)
    return {"vendors": vendors, "total": total}

@router.post("/vendors")
async def create_vendor(vendor: Vendor):
    db = get_db()
    vendor_dict = vendor.dict()
    vendor_dict["vendor_id"] = f"VND-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    vendor_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    db.books_vendors.insert_one(vendor_dict)
    del vendor_dict["_id"]
    return vendor_dict

# ============== CHART OF ACCOUNTS ==============

@router.get("/accounts")
async def list_accounts(account_type: str = ""):
    db = get_db()
    query = {}
    if account_type:
        query["type"] = account_type
    
    accounts = list(db.chart_of_accounts.find(query, {"_id": 0}))
    return {"accounts": accounts, "total": len(accounts)}

@router.post("/accounts")
async def create_account(account: Account):
    db = get_db()
    acc_dict = account.dict()
    acc_dict["account_id"] = f"ACC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    acc_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    acc_dict["balance"] = 0
    db.chart_of_accounts.insert_one(acc_dict)
    del acc_dict["_id"]
    return acc_dict

# ============== INVOICES ==============

@router.get("/invoices")
async def list_invoices(
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
    
    invoices = list(db.books_invoices.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
    total = db.books_invoices.count_documents(query)
    return {"invoices": invoices, "total": total}

@router.post("/invoices")
async def create_invoice(invoice: Invoice):
    db = get_db()
    
    # Calculate totals
    subtotal = 0
    tax_total = 0
    line_items = []
    
    for item in invoice.line_items:
        item_subtotal = item.quantity * item.rate
        item_discount = item_subtotal * (item.discount_percent / 100)
        item_taxable = item_subtotal - item_discount
        item_tax = item_taxable * (item.tax_rate / 100)
        
        line_items.append({
            **item.dict(),
            "subtotal": item_subtotal,
            "discount_amount": item_discount,
            "tax_amount": item_tax,
            "total": item_taxable + item_tax
        })
        
        subtotal += item_taxable
        tax_total += item_tax
    
    # Get next invoice number
    last_invoice = db.books_invoices.find_one(sort=[("invoice_number", -1)])
    next_num = 1
    if last_invoice and "invoice_number" in last_invoice:
        try:
            next_num = int(last_invoice["invoice_number"].split("-")[1]) + 1
        except:
            next_num = db.books_invoices.count_documents({}) + 1
    
    invoice_dict = {
        "invoice_id": f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "invoice_number": f"INV-{str(next_num).zfill(6)}",
        "customer_id": invoice.customer_id,
        "customer_name": invoice.customer_name,
        "invoice_date": invoice.invoice_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "due_date": invoice.due_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "line_items": line_items,
        "subtotal": subtotal,
        "tax_total": tax_total,
        "total": subtotal + tax_total,
        "balance_due": subtotal + tax_total,
        "amount_paid": 0,
        "status": "draft",
        "place_of_supply": invoice.place_of_supply,
        "gst_treatment": invoice.gst_treatment,
        "notes": invoice.notes,
        "terms": invoice.terms,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    db.books_invoices.insert_one(invoice_dict)
    del invoice_dict["_id"]
    
    # Update customer outstanding balance
    db.books_customers.update_one(
        {"customer_id": invoice.customer_id},
        {"$inc": {"outstanding_balance": invoice_dict["total"]}}
    )
    
    return invoice_dict

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str):
    db = get_db()
    invoice = db.books_invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, status: str):
    db = get_db()
    valid_statuses = ["draft", "sent", "viewed", "paid", "partially_paid", "overdue", "void"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    result = db.books_invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": f"Invoice status updated to {status}"}

# ============== PAYMENTS ==============

@router.get("/payments")
async def list_payments(skip: int = 0, limit: int = 50, customer_id: str = ""):
    db = get_db()
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    
    payments = list(db.books_payments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
    total = db.books_payments.count_documents(query)
    return {"payments": payments, "total": total}

@router.post("/payments")
async def record_payment(payment: Payment):
    db = get_db()
    
    # Get next payment number
    last_payment = db.books_payments.find_one(sort=[("payment_number", -1)])
    next_num = 1
    if last_payment and "payment_number" in last_payment:
        try:
            next_num = int(last_payment["payment_number"].split("-")[1]) + 1
        except:
            next_num = db.books_payments.count_documents({}) + 1
    
    payment_dict = {
        "payment_id": f"PMT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "payment_number": f"PMT-{str(next_num).zfill(6)}",
        "customer_id": payment.customer_id,
        "customer_name": payment.customer_name,
        "amount": payment.amount,
        "payment_mode": payment.payment_mode,
        "reference_number": payment.reference_number,
        "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "invoice_ids": payment.invoice_ids,
        "notes": payment.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    db.books_payments.insert_one(payment_dict)
    del payment_dict["_id"]
    
    # Update invoices
    remaining = payment.amount
    for inv_id in payment.invoice_ids:
        if remaining <= 0:
            break
        invoice = db.books_invoices.find_one({"invoice_id": inv_id})
        if invoice:
            to_apply = min(remaining, invoice.get("balance_due", 0))
            new_balance = invoice.get("balance_due", 0) - to_apply
            new_status = "paid" if new_balance <= 0 else "partially_paid"
            
            db.books_invoices.update_one(
                {"invoice_id": inv_id},
                {
                    "$set": {"balance_due": new_balance, "status": new_status},
                    "$inc": {"amount_paid": to_apply}
                }
            )
            remaining -= to_apply
    
    # Update customer outstanding balance
    db.books_customers.update_one(
        {"customer_id": payment.customer_id},
        {"$inc": {"outstanding_balance": -payment.amount}}
    )
    
    return payment_dict

# ============== IMPORT DATA ==============

@router.post("/import")
async def import_zoho_data(data: Dict[str, Any]):
    """Import data from Zoho Books backup"""
    db = get_db()
    results = {}
    
    # Import Services
    if "services" in data:
        for svc in data["services"]:
            svc["item_id"] = f"SRV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            svc["created_at"] = datetime.now(timezone.utc).isoformat()
            svc["is_active"] = True
            svc["tax_rate"] = 18.0
        if data["services"]:
            db.service_items.insert_many(data["services"])
        results["services"] = len(data["services"])
    
    # Import Parts
    if "parts" in data:
        for part in data["parts"]:
            part["item_id"] = f"PRT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            part["created_at"] = datetime.now(timezone.utc).isoformat()
            part["is_active"] = True
            part["stock_quantity"] = 0
            part["reorder_level"] = 5
            part["tax_rate"] = 18.0
        if data["parts"]:
            db.parts.insert_many(data["parts"])
        results["parts"] = len(data["parts"])
    
    # Import Customers
    if "customers" in data:
        for cust in data["customers"]:
            cust["customer_id"] = f"CUST-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            cust["created_at"] = datetime.now(timezone.utc).isoformat()
            cust["is_active"] = True
            cust["outstanding_balance"] = 0
            cust["payment_terms"] = 15
        if data["customers"]:
            db.books_customers.insert_many(data["customers"])
        results["customers"] = len(data["customers"])
    
    # Import Vendors
    if "vendors" in data:
        for vnd in data["vendors"]:
            vnd["vendor_id"] = f"VND-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            vnd["created_at"] = datetime.now(timezone.utc).isoformat()
            vnd["is_active"] = True
        if data["vendors"]:
            db.books_vendors.insert_many(data["vendors"])
        results["vendors"] = len(data["vendors"])
    
    # Import Chart of Accounts
    if "accounts" in data:
        for acc in data["accounts"]:
            acc["account_id"] = f"ACC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            acc["created_at"] = datetime.now(timezone.utc).isoformat()
            acc["is_active"] = True
            acc["balance"] = 0
        if data["accounts"]:
            db.chart_of_accounts.insert_many(data["accounts"])
        results["accounts"] = len(data["accounts"])
    
    return {"message": "Import completed", "results": results}

# ============== ANALYTICS ==============

@router.get("/analytics/summary")
async def get_books_summary():
    db = get_db()
    
    # Invoice stats
    total_invoices = db.books_invoices.count_documents({})
    paid_invoices = db.books_invoices.count_documents({"status": "paid"})
    pending_invoices = db.books_invoices.count_documents({"status": {"$in": ["draft", "sent", "partially_paid"]}})
    
    # Revenue
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "collected": {"$sum": "$amount_paid"}}}
    ]
    revenue = list(db.books_invoices.aggregate(pipeline))
    total_revenue = revenue[0]["total"] if revenue else 0
    collected = revenue[0]["collected"] if revenue else 0
    
    # Counts
    total_customers = db.books_customers.count_documents({})
    total_services = db.service_items.count_documents({})
    total_parts = db.parts.count_documents({})
    total_vendors = db.books_vendors.count_documents({})
    
    return {
        "invoices": {
            "total": total_invoices,
            "paid": paid_invoices,
            "pending": pending_invoices
        },
        "revenue": {
            "total": total_revenue,
            "collected": collected,
            "outstanding": total_revenue - collected
        },
        "counts": {
            "customers": total_customers,
            "services": total_services,
            "parts": total_parts,
            "vendors": total_vendors
        }
    }
