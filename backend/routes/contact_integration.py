# Contact Integration Service
# Bridges enhanced contacts with existing transactions (Invoices, Bills, Estimates, etc.)

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import motor.motor_asyncio
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact-integration", tags=["Contact Integration"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ========================= HELPER FUNCTIONS =========================

async def get_contact_by_id(contact_id: str) -> Optional[dict]:
    """Get contact from either enhanced or legacy collection"""
    # Try enhanced contacts first
    contact = await db["contacts_enhanced"].find_one({"contact_id": contact_id}, {"_id": 0})
    if contact:
        return contact
    
    # Fall back to legacy contacts
    contact = await db["contacts"].find_one({"contact_id": contact_id}, {"_id": 0})
    return contact

async def get_contact_for_transaction(contact_id: str) -> dict:
    """Get contact details formatted for transaction display"""
    contact = await get_contact_by_id(contact_id)
    if not contact:
        return {"name": "Unknown Contact", "contact_id": contact_id}
    
    # Get default billing address
    billing_address = await db["addresses"].find_one(
        {"contact_id": contact_id, "address_type": "billing", "is_default": True},
        {"_id": 0}
    )
    if not billing_address:
        billing_address = await db["addresses"].find_one(
            {"contact_id": contact_id, "address_type": "billing"},
            {"_id": 0}
        )
    
    # Get default shipping address
    shipping_address = await db["addresses"].find_one(
        {"contact_id": contact_id, "address_type": "shipping", "is_default": True},
        {"_id": 0}
    )
    if not shipping_address:
        shipping_address = await db["addresses"].find_one(
            {"contact_id": contact_id, "address_type": "shipping"},
            {"_id": 0}
        )
    
    # Get primary contact person
    primary_person = await db["contact_persons"].find_one(
        {"contact_id": contact_id, "is_primary": True},
        {"_id": 0}
    )
    
    return {
        "contact_id": contact_id,
        "name": contact.get("name") or contact.get("display_name", "Unknown"),
        "company_name": contact.get("company_name", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "gstin": contact.get("gstin", ""),
        "place_of_supply": contact.get("place_of_supply", ""),
        "payment_terms": contact.get("payment_terms", 30),
        "currency_code": contact.get("currency_code", "INR"),
        "billing_address": billing_address,
        "shipping_address": shipping_address,
        "primary_contact": primary_person,
        "contact_type": contact.get("contact_type", "customer")
    }

async def enrich_transaction_with_contact(transaction: dict, contact_field: str = "customer_id") -> dict:
    """Add contact details to a transaction record"""
    contact_id = transaction.get(contact_field)
    if contact_id:
        contact_details = await get_contact_for_transaction(contact_id)
        transaction["contact_details"] = contact_details
        transaction["contact_name"] = contact_details.get("name", "Unknown")
    return transaction

# ========================= CONTACT LOOKUP ENDPOINTS =========================

@router.get("/contacts/search")
async def search_contacts_for_transaction(
    q: str = "",
    contact_type: str = "all",  # customer, vendor, both, all
    limit: int = 20
):
    """Search contacts for use in transactions (unified search across both collections)"""
    results = []
    
    # Search enhanced contacts
    query = {"is_active": {"$ne": False}}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"company_name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"gstin": {"$regex": q, "$options": "i"}}
        ]
    
    if contact_type != "all":
        if contact_type in ["customer", "vendor"]:
            query["contact_type"] = {"$in": [contact_type, "both"]}
        else:
            query["contact_type"] = contact_type
    
    enhanced = await db["contacts_enhanced"].find(query, {"_id": 0}).limit(limit).to_list(limit)
    for c in enhanced:
        c["source"] = "enhanced"
        results.append(c)
    
    # Search legacy contacts if not enough results
    if len(results) < limit:
        legacy_query = {}
        if q:
            legacy_query["$or"] = [
                {"display_name": {"$regex": q, "$options": "i"}},
                {"company_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ]
        
        # Get IDs already found
        found_ids = [c["contact_id"] for c in results]
        if found_ids:
            legacy_query["contact_id"] = {"$nin": found_ids}
        
        remaining = limit - len(results)
        legacy = await db["contacts"].find(legacy_query, {"_id": 0}).limit(remaining).to_list(remaining)
        for c in legacy:
            c["source"] = "legacy"
            c["name"] = c.get("display_name", c.get("name", ""))
            results.append(c)
    
    return {"code": 0, "contacts": results, "count": len(results)}

@router.get("/contacts/{contact_id}/for-transaction")
async def get_contact_for_transaction_endpoint(contact_id: str):
    """Get full contact details formatted for transaction creation"""
    contact_details = await get_contact_for_transaction(contact_id)
    if contact_details.get("name") == "Unknown Contact":
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"code": 0, "contact": contact_details}

# ========================= TRANSACTION ENRICHMENT ENDPOINTS =========================

@router.get("/invoices/with-contacts")
async def list_invoices_with_contacts(
    status: str = "",
    customer_id: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List invoices with enriched contact details"""
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    total = await db["invoices"].count_documents(query)
    skip = (page - 1) * per_page
    
    invoices = await db["invoices"].find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    # Enrich with contact details
    for inv in invoices:
        await enrich_transaction_with_contact(inv, "customer_id")
    
    return {
        "code": 0,
        "invoices": invoices,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/bills/with-contacts")
async def list_bills_with_contacts(
    status: str = "",
    vendor_id: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List bills with enriched contact details"""
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    total = await db["bills"].count_documents(query)
    skip = (page - 1) * per_page
    
    bills = await db["bills"].find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    # Enrich with contact details
    for bill in bills:
        await enrich_transaction_with_contact(bill, "vendor_id")
    
    return {
        "code": 0,
        "bills": bills,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/estimates/with-contacts")
async def list_estimates_with_contacts(
    status: str = "",
    customer_id: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List estimates with enriched contact details"""
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    total = await db["estimates"].count_documents(query)
    skip = (page - 1) * per_page
    
    estimates = await db["estimates"].find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    # Enrich with contact details
    for est in estimates:
        await enrich_transaction_with_contact(est, "customer_id")
    
    return {
        "code": 0,
        "estimates": estimates,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/purchase-orders/with-contacts")
async def list_purchase_orders_with_contacts(
    status: str = "",
    vendor_id: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List purchase orders with enriched contact details"""
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    total = await db["purchase_orders"].count_documents(query)
    skip = (page - 1) * per_page
    
    pos = await db["purchase_orders"].find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    # Enrich with contact details
    for po in pos:
        await enrich_transaction_with_contact(po, "vendor_id")
    
    return {
        "code": 0,
        "purchase_orders": pos,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

# ========================= CONTACT TRANSACTION HISTORY =========================

@router.get("/contacts/{contact_id}/transactions")
async def get_contact_transactions(
    contact_id: str,
    transaction_type: str = "all",  # all, invoices, bills, estimates, purchase_orders
    page: int = 1,
    per_page: int = 50
):
    """Get all transactions for a contact"""
    transactions = []
    
    # Get invoices (as customer)
    if transaction_type in ["all", "invoices"]:
        invoices = await db["invoices"].find(
            {"customer_id": contact_id},
            {"_id": 0, "invoice_id": 1, "invoice_number": 1, "date": 1, "total": 1, "balance_due": 1, "status": 1}
        ).sort("date", -1).limit(100).to_list(100)
        for inv in invoices:
            inv["type"] = "invoice"
            inv["transaction_id"] = inv.get("invoice_id")
            inv["transaction_number"] = inv.get("invoice_number")
            transactions.append(inv)
    
    # Get bills (as vendor)
    if transaction_type in ["all", "bills"]:
        bills = await db["bills"].find(
            {"vendor_id": contact_id},
            {"_id": 0, "bill_id": 1, "bill_number": 1, "date": 1, "total": 1, "balance_due": 1, "status": 1}
        ).sort("date", -1).limit(100).to_list(100)
        for bill in bills:
            bill["type"] = "bill"
            bill["transaction_id"] = bill.get("bill_id")
            bill["transaction_number"] = bill.get("bill_number")
            transactions.append(bill)
    
    # Get estimates (as customer)
    if transaction_type in ["all", "estimates"]:
        estimates = await db["estimates"].find(
            {"customer_id": contact_id},
            {"_id": 0, "estimate_id": 1, "estimate_number": 1, "date": 1, "total": 1, "status": 1}
        ).sort("date", -1).limit(100).to_list(100)
        for est in estimates:
            est["type"] = "estimate"
            est["transaction_id"] = est.get("estimate_id")
            est["transaction_number"] = est.get("estimate_number")
            transactions.append(est)
    
    # Get purchase orders (as vendor)
    if transaction_type in ["all", "purchase_orders"]:
        pos = await db["purchase_orders"].find(
            {"vendor_id": contact_id},
            {"_id": 0, "purchaseorder_id": 1, "purchaseorder_number": 1, "date": 1, "total": 1, "status": 1}
        ).sort("date", -1).limit(100).to_list(100)
        for po in pos:
            po["type"] = "purchase_order"
            po["transaction_id"] = po.get("purchaseorder_id")
            po["transaction_number"] = po.get("purchaseorder_number")
            transactions.append(po)
    
    # Get credit notes (as customer)
    if transaction_type in ["all", "credit_notes"]:
        cns = await db["credit_notes"].find(
            {"customer_id": contact_id},
            {"_id": 0, "creditnote_id": 1, "creditnote_number": 1, "date": 1, "total": 1, "balance": 1, "status": 1}
        ).sort("date", -1).limit(100).to_list(100)
        for cn in cns:
            cn["type"] = "credit_note"
            cn["transaction_id"] = cn.get("creditnote_id")
            cn["transaction_number"] = cn.get("creditnote_number")
            transactions.append(cn)
    
    # Get payments
    if transaction_type in ["all", "payments"]:
        payments = await db["payments"].find(
            {"$or": [{"customer_id": contact_id}, {"contact_id": contact_id}]},
            {"_id": 0, "payment_id": 1, "payment_number": 1, "date": 1, "amount": 1, "payment_mode": 1}
        ).sort("date", -1).limit(100).to_list(100)
        for pmt in payments:
            pmt["type"] = "payment"
            pmt["transaction_id"] = pmt.get("payment_id")
            pmt["transaction_number"] = pmt.get("payment_number")
            pmt["total"] = pmt.get("amount", 0)
            transactions.append(pmt)
    
    # Sort all by date
    transactions.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # Paginate
    total = len(transactions)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = transactions[start:end]
    
    # Calculate totals
    total_invoiced = sum(t.get("total", 0) for t in transactions if t.get("type") == "invoice")
    total_billed = sum(t.get("total", 0) for t in transactions if t.get("type") == "bill")
    total_outstanding = sum(t.get("balance_due", 0) for t in transactions if t.get("type") in ["invoice", "bill"])
    
    return {
        "code": 0,
        "contact_id": contact_id,
        "transactions": paginated,
        "summary": {
            "total_invoiced": round(total_invoiced, 2),
            "total_billed": round(total_billed, 2),
            "total_outstanding": round(total_outstanding, 2),
            "transaction_count": total
        },
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/contacts/{contact_id}/balance-summary")
async def get_contact_balance_summary(contact_id: str):
    """Get detailed balance summary for a contact"""
    # Invoices (receivable)
    invoices = await db["invoices"].find(
        {"customer_id": contact_id, "status": {"$nin": ["paid", "void"]}},
        {"total": 1, "balance_due": 1, "status": 1}
    ).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_receivable = sum(inv.get("balance_due", 0) for inv in invoices)
    overdue_invoices = [inv for inv in invoices if inv.get("status") == "overdue"]
    overdue_amount = sum(inv.get("balance_due", 0) for inv in overdue_invoices)
    
    # Bills (payable)
    bills = await db["bills"].find(
        {"vendor_id": contact_id, "status": {"$nin": ["paid", "void"]}},
        {"total": 1, "balance_due": 1, "status": 1}
    ).to_list(1000)
    
    total_billed = sum(bill.get("total", 0) for bill in bills)
    total_payable = sum(bill.get("balance_due", 0) for bill in bills)
    overdue_bills = [bill for bill in bills if bill.get("status") == "overdue"]
    overdue_payable = sum(bill.get("balance_due", 0) for bill in overdue_bills)
    
    # Credit notes
    credit_notes = await db["credit_notes"].find(
        {"customer_id": contact_id, "status": {"$ne": "void"}},
        {"balance": 1}
    ).to_list(1000)
    unused_credits = sum(cn.get("balance", 0) for cn in credit_notes)
    
    # Vendor credits
    vendor_credits = await db["vendor_credits"].find(
        {"vendor_id": contact_id, "status": {"$ne": "void"}},
        {"balance": 1}
    ).to_list(1000)
    unused_vendor_credits = sum(vc.get("balance", 0) for vc in vendor_credits)
    
    return {
        "code": 0,
        "contact_id": contact_id,
        "balance_summary": {
            "receivable": {
                "total_invoiced": round(total_invoiced, 2),
                "outstanding": round(total_receivable, 2),
                "overdue": round(overdue_amount, 2),
                "overdue_count": len(overdue_invoices),
                "unused_credits": round(unused_credits, 2)
            },
            "payable": {
                "total_billed": round(total_billed, 2),
                "outstanding": round(total_payable, 2),
                "overdue": round(overdue_payable, 2),
                "overdue_count": len(overdue_bills),
                "unused_credits": round(unused_vendor_credits, 2)
            },
            "net_balance": round(total_receivable - total_payable, 2)
        }
    }

# ========================= DATA MIGRATION ENDPOINTS =========================

@router.post("/migrate/contacts-to-enhanced")
async def migrate_contacts_to_enhanced(dry_run: bool = True, org_id: Optional[str] = None):
    """Migrate legacy contacts to enhanced contacts collection (admin/migration tool, org-scoped)"""
    # This is an admin migration tool. Scope to org_id if provided.
    query = {"organization_id": org_id} if org_id else {}
    legacy_contacts = await db["contacts"].find(query, {"_id": 0}).to_list(1000)
    
    migrated = []
    skipped = []
    errors = []
    
    for contact in legacy_contacts:
        contact_id = contact.get("contact_id")
        
        # Check if already exists in enhanced
        existing = await db["contacts_enhanced"].find_one({"contact_id": contact_id})
        if existing:
            skipped.append({"contact_id": contact_id, "reason": "Already exists"})
            continue
        
        try:
            # Map legacy fields to enhanced format
            enhanced_contact = {
                "contact_id": contact_id,
                "name": contact.get("display_name") or contact.get("contact_name") or contact.get("name", ""),
                "company_name": contact.get("company_name", ""),
                "contact_type": contact.get("contact_type", "customer"),
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "mobile": contact.get("mobile", ""),
                "website": contact.get("website", ""),
                "currency_code": contact.get("currency_code", "INR"),
                "payment_terms": contact.get("payment_terms", 30),
                "credit_limit": contact.get("credit_limit", 0),
                "gstin": contact.get("gst_no") or contact.get("gstin", ""),
                "pan": contact.get("pan", ""),
                "place_of_supply": contact.get("place_of_supply", ""),
                "tax_treatment": contact.get("tax_treatment", "business_gst"),
                "gst_treatment": contact.get("gst_treatment", "registered"),
                "opening_balance": contact.get("opening_balance", 0),
                "opening_balance_type": contact.get("opening_balance_type", "credit"),
                "tags": [],
                "notes": contact.get("notes", ""),
                "custom_fields": contact.get("custom_fields", {}),
                "is_active": contact.get("is_active", True),
                "portal_enabled": contact.get("portal_enabled", False),
                "portal_token": contact.get("portal_token", ""),
                "created_time": contact.get("created_time") or datetime.now(timezone.utc).isoformat(),
                "updated_time": datetime.now(timezone.utc).isoformat(),
                "migrated_from_legacy": True
            }
            
            if not dry_run:
                await db["contacts_enhanced"].insert_one(enhanced_contact)
            
            migrated.append({"contact_id": contact_id, "name": enhanced_contact["name"]})
            
        except Exception as e:
            errors.append({"contact_id": contact_id, "error": str(e)})
    
    return {
        "code": 0,
        "dry_run": dry_run,
        "migrated_count": len(migrated),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "migrated": migrated if not dry_run else migrated[:10],  # Show sample in dry run
        "skipped": skipped[:10],
        "errors": errors
    }

@router.post("/migrate/link-transactions")
async def link_transactions_to_enhanced(dry_run: bool = True):
    """Update transactions to reference enhanced contacts (adds contact_details)"""
    updated_collections = {}
    
    collections_to_update = [
        ("invoices", "customer_id"),
        ("bills", "vendor_id"),
        ("estimates", "customer_id"),
        ("purchase_orders", "vendor_id"),
        ("credit_notes", "customer_id"),
        ("vendor_credits", "vendor_id"),
        ("recurring_invoices", "customer_id"),
        ("delivery_challans", "customer_id"),
        ("retainer_invoices", "customer_id"),
        ("projects", "customer_id")
    ]
    
    for collection_name, contact_field in collections_to_update:
        collection = db[collection_name]
        docs = await collection.find({contact_field: {"$exists": True, "$ne": ""}}, {"_id": 1, contact_field: 1}).to_list(10000)
        
        updated = 0
        for doc in docs:
            contact_id = doc.get(contact_field)
            if contact_id:
                contact_details = await get_contact_for_transaction(contact_id)
                if contact_details.get("name") != "Unknown Contact":
                    if not dry_run:
                        await collection.update_one(
                            {"_id": doc["_id"]},
                            {"$set": {"contact_name": contact_details.get("name", "")}}
                        )
                    updated += 1
        
        updated_collections[collection_name] = updated
    
    return {
        "code": 0,
        "dry_run": dry_run,
        "updated_collections": updated_collections,
        "total_updated": sum(updated_collections.values())
    }

# ========================= REPORTING ENDPOINTS =========================

@router.get("/reports/customers-by-revenue")
async def report_customers_by_revenue(limit: int = 20):
    """Get top customers by revenue"""
    pipeline = [
        {"$match": {"status": {"$nin": ["void", "draft"]}}},
        {"$group": {
            "_id": "$customer_id",
            "total_revenue": {"$sum": "$total"},
            "invoice_count": {"$sum": 1},
            "avg_invoice": {"$avg": "$total"}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": limit}
    ]
    
    results = await db["invoices"].aggregate(pipeline).to_list(limit)
    
    # Enrich with contact details
    for r in results:
        contact = await get_contact_for_transaction(r["_id"])
        r["contact_id"] = r["_id"]
        r["contact_name"] = contact.get("name", "Unknown")
        r["company_name"] = contact.get("company_name", "")
        r["total_revenue"] = round(r["total_revenue"], 2)
        r["avg_invoice"] = round(r["avg_invoice"], 2)
        del r["_id"]
    
    return {"code": 0, "top_customers": results}

@router.get("/reports/vendors-by-expense")
async def report_vendors_by_expense(limit: int = 20):
    """Get top vendors by expense"""
    pipeline = [
        {"$match": {"status": {"$nin": ["void", "draft"]}}},
        {"$group": {
            "_id": "$vendor_id",
            "total_expense": {"$sum": "$total"},
            "bill_count": {"$sum": 1},
            "avg_bill": {"$avg": "$total"}
        }},
        {"$sort": {"total_expense": -1}},
        {"$limit": limit}
    ]
    
    results = await db["bills"].aggregate(pipeline).to_list(limit)
    
    # Enrich with contact details
    for r in results:
        contact = await get_contact_for_transaction(r["_id"])
        r["contact_id"] = r["_id"]
        r["contact_name"] = contact.get("name", "Unknown")
        r["company_name"] = contact.get("company_name", "")
        r["total_expense"] = round(r["total_expense"], 2)
        r["avg_bill"] = round(r["avg_bill"], 2)
        del r["_id"]
    
    return {"code": 0, "top_vendors": results}

@router.get("/reports/receivables-aging")
async def report_receivables_aging():
    """Get accounts receivable aging report grouped by contact"""
    invoices = await db["invoices"].find(
        {"status": {"$nin": ["paid", "void"]}, "balance_due": {"$gt": 0}},
        {"_id": 0, "customer_id": 1, "balance_due": 1, "due_date": 1, "invoice_number": 1}
    ).to_list(10000)
    
    today = datetime.now(timezone.utc).date()
    
    # Group by customer
    customer_aging = {}
    for inv in invoices:
        customer_id = inv.get("customer_id")
        if not customer_id:
            continue
        
        if customer_id not in customer_aging:
            contact = await get_contact_for_transaction(customer_id)
            customer_aging[customer_id] = {
                "contact_id": customer_id,
                "contact_name": contact.get("name", "Unknown"),
                "company_name": contact.get("company_name", ""),
                "current": 0,
                "days_1_30": 0,
                "days_31_60": 0,
                "days_61_90": 0,
                "over_90": 0,
                "total": 0,
                "invoice_count": 0
            }
        
        # Calculate days overdue
        due_date_str = inv.get("due_date", "")
        balance = inv.get("balance_due", 0)
        
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00")).date()
                days_overdue = (today - due_date).days
                
                if days_overdue <= 0:
                    customer_aging[customer_id]["current"] += balance
                elif days_overdue <= 30:
                    customer_aging[customer_id]["days_1_30"] += balance
                elif days_overdue <= 60:
                    customer_aging[customer_id]["days_31_60"] += balance
                elif days_overdue <= 90:
                    customer_aging[customer_id]["days_61_90"] += balance
                else:
                    customer_aging[customer_id]["over_90"] += balance
            except:
                customer_aging[customer_id]["current"] += balance
        else:
            customer_aging[customer_id]["current"] += balance
        
        customer_aging[customer_id]["total"] += balance
        customer_aging[customer_id]["invoice_count"] += 1
    
    # Convert to list and sort by total
    aging_list = list(customer_aging.values())
    aging_list.sort(key=lambda x: x["total"], reverse=True)
    
    # Calculate totals
    totals = {
        "current": sum(a["current"] for a in aging_list),
        "days_1_30": sum(a["days_1_30"] for a in aging_list),
        "days_31_60": sum(a["days_31_60"] for a in aging_list),
        "days_61_90": sum(a["days_61_90"] for a in aging_list),
        "over_90": sum(a["over_90"] for a in aging_list),
        "total": sum(a["total"] for a in aging_list)
    }
    
    return {
        "code": 0,
        "aging_by_customer": aging_list,
        "totals": {k: round(v, 2) for k, v in totals.items()},
        "customer_count": len(aging_list)
    }

@router.get("/reports/payables-aging")
async def report_payables_aging():
    """Get accounts payable aging report grouped by vendor"""
    bills = await db["bills"].find(
        {"status": {"$nin": ["paid", "void"]}, "balance_due": {"$gt": 0}},
        {"_id": 0, "vendor_id": 1, "balance_due": 1, "due_date": 1, "bill_number": 1}
    ).to_list(10000)
    
    today = datetime.now(timezone.utc).date()
    
    # Group by vendor
    vendor_aging = {}
    for bill in bills:
        vendor_id = bill.get("vendor_id")
        if not vendor_id:
            continue
        
        if vendor_id not in vendor_aging:
            contact = await get_contact_for_transaction(vendor_id)
            vendor_aging[vendor_id] = {
                "contact_id": vendor_id,
                "contact_name": contact.get("name", "Unknown"),
                "company_name": contact.get("company_name", ""),
                "current": 0,
                "days_1_30": 0,
                "days_31_60": 0,
                "days_61_90": 0,
                "over_90": 0,
                "total": 0,
                "bill_count": 0
            }
        
        # Calculate days overdue
        due_date_str = bill.get("due_date", "")
        balance = bill.get("balance_due", 0)
        
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00")).date()
                days_overdue = (today - due_date).days
                
                if days_overdue <= 0:
                    vendor_aging[vendor_id]["current"] += balance
                elif days_overdue <= 30:
                    vendor_aging[vendor_id]["days_1_30"] += balance
                elif days_overdue <= 60:
                    vendor_aging[vendor_id]["days_31_60"] += balance
                elif days_overdue <= 90:
                    vendor_aging[vendor_id]["days_61_90"] += balance
                else:
                    vendor_aging[vendor_id]["over_90"] += balance
            except:
                vendor_aging[vendor_id]["current"] += balance
        else:
            vendor_aging[vendor_id]["current"] += balance
        
        vendor_aging[vendor_id]["total"] += balance
        vendor_aging[vendor_id]["bill_count"] += 1
    
    # Convert to list and sort by total
    aging_list = list(vendor_aging.values())
    aging_list.sort(key=lambda x: x["total"], reverse=True)
    
    # Calculate totals
    totals = {
        "current": sum(a["current"] for a in aging_list),
        "days_1_30": sum(a["days_1_30"] for a in aging_list),
        "days_31_60": sum(a["days_31_60"] for a in aging_list),
        "days_61_90": sum(a["days_61_90"] for a in aging_list),
        "over_90": sum(a["over_90"] for a in aging_list),
        "total": sum(a["total"] for a in aging_list)
    }
    
    return {
        "code": 0,
        "aging_by_vendor": aging_list,
        "totals": {k: round(v, 2) for k, v in totals.items()},
        "vendor_count": len(aging_list)
    }
