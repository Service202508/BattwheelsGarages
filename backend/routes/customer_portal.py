# Customer Portal Module - Self-Service Portal for Customers
# Allows customers to view invoices, estimates, statements, and make payments

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customer-portal", tags=["Customer Portal"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Use main collections with Zoho-synced data
contacts_collection = db["contacts"]
invoices_collection = db["invoices"]
estimates_collection = db["estimates"]
salesorders_collection = db["salesorders"]
payments_collection = db["customerpayments"]
portal_sessions_collection = db["portal_sessions"]

# ========================= MODELS =========================

class PortalLogin(BaseModel):
    token: str = Field(..., min_length=10)

class PortalPaymentRequest(BaseModel):
    invoice_id: str
    amount: float = Field(..., gt=0)
    payment_mode: str = "online"

# ========================= HELPERS =========================

def generate_session_token() -> str:
    return f"PS-{uuid.uuid4().hex}"

async def validate_portal_token(token: str) -> dict:
    """Validate portal token and return contact"""
    # Try to find contact with portal_token - check multiple status field formats
    contact = await contacts_collection.find_one(
        {
            "portal_token": token, 
            "portal_enabled": True,
            "$or": [
                {"is_active": True},
                {"status": "active"},
                {"status": {"$exists": False}}  # If status field doesn't exist, allow
            ]
        },
        {"_id": 0}
    )
    if not contact:
        raise HTTPException(status_code=401, detail="Invalid or expired portal token")
    return contact

async def get_portal_session(session_token: str) -> dict:
    """Get and validate portal session"""
    session = await portal_sessions_collection.find_one(
        {"session_token": session_token, "is_active": True},
        {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires = datetime.fromisoformat(session.get("expires_at", "2000-01-01"))
    if expires < datetime.now(timezone.utc):
        await portal_sessions_collection.update_one(
            {"session_token": session_token},
            {"$set": {"is_active": False}}
        )
        raise HTTPException(status_code=401, detail="Session expired")
    
    return session

# ========================= AUTH ENDPOINTS =========================

@router.post("/login")
async def portal_login(login: PortalLogin):
    """Login to customer portal with token"""
    contact = await validate_portal_token(login.token)
    
    # Create session
    session_token = generate_session_token()
    session = {
        "session_token": session_token,
        "contact_id": contact["contact_id"],
        "contact_name": contact.get("name", ""),
        "contact_email": contact.get("email", ""),
        "company_name": contact.get("company_name", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "is_active": True
    }
    await portal_sessions_collection.insert_one(session)
    
    # Update last login
    await contacts_collection.update_one(
        {"contact_id": contact["contact_id"]},
        {"$set": {"portal_last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "code": 0,
        "message": "Login successful",
        "session_token": session_token,
        "contact": {
            "contact_id": contact["contact_id"],
            "name": contact.get("name"),
            "company_name": contact.get("company_name"),
            "email": contact.get("email")
        },
        "expires_in": 86400  # 24 hours in seconds
    }

@router.post("/logout")
async def portal_logout(session_token: str):
    """Logout from portal"""
    await portal_sessions_collection.update_one(
        {"session_token": session_token},
        {"$set": {"is_active": False, "logged_out_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"code": 0, "message": "Logged out successfully"}

@router.get("/session")
async def get_session_info(session_token: str):
    """Get current session info"""
    session = await get_portal_session(session_token)
    return {"code": 0, "session": session}

# ========================= DASHBOARD =========================

@router.get("/dashboard")
async def get_portal_dashboard(session_token: str):
    """Get customer portal dashboard summary"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    # Get invoice stats
    total_invoices = await invoices_collection.count_documents({
        "customer_id": contact_id, "status": {"$ne": "void"}
    })
    pending_invoices = await invoices_collection.count_documents({
        "customer_id": contact_id, "status": {"$in": ["sent", "overdue", "partially_paid"]}
    })
    overdue_invoices = await invoices_collection.count_documents({
        "customer_id": contact_id, "status": "overdue"
    })
    
    # Get totals
    pipeline = [
        {"$match": {"customer_id": contact_id, "status": {"$ne": "void"}}},
        {"$group": {
            "_id": None,
            "total_invoiced": {"$sum": "$grand_total"},
            "total_outstanding": {"$sum": "$balance_due"},
            "total_paid": {"$sum": {"$subtract": ["$grand_total", "$balance_due"]}}
        }}
    ]
    totals = await invoices_collection.aggregate(pipeline).to_list(1)
    values = totals[0] if totals else {"total_invoiced": 0, "total_outstanding": 0, "total_paid": 0}
    
    # Get estimate stats
    total_estimates = await estimates_collection.count_documents({"customer_id": contact_id})
    pending_estimates = await estimates_collection.count_documents({
        "customer_id": contact_id, "status": "sent"
    })
    
    # Get recent activity
    recent_invoices = await invoices_collection.find(
        {"customer_id": contact_id, "status": {"$ne": "void"}},
        {"_id": 0, "invoice_id": 1, "invoice_number": 1, "invoice_date": 1, "grand_total": 1, "balance_due": 1, "status": 1}
    ).sort("invoice_date", -1).limit(5).to_list(5)
    
    return {
        "code": 0,
        "dashboard": {
            "contact": {
                "name": session.get("contact_name"),
                "company": session.get("company_name"),
                "email": session.get("contact_email")
            },
            "summary": {
                "total_invoices": total_invoices,
                "pending_invoices": pending_invoices,
                "overdue_invoices": overdue_invoices,
                "total_estimates": total_estimates,
                "pending_estimates": pending_estimates,
                "total_invoiced": round(values.get("total_invoiced", 0), 2),
                "total_outstanding": round(values.get("total_outstanding", 0), 2),
                "total_paid": round(values.get("total_paid", 0), 2)
            },
            "recent_invoices": recent_invoices
        }
    }

# ========================= INVOICES =========================

@router.get("/invoices")
async def get_portal_invoices(
    session_token: str,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
):
    """Get customer's invoices"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    query = {"customer_id": contact_id, "status": {"$nin": ["draft", "void"]}}
    if status:
        query["status"] = status
    
    total = await invoices_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    invoices = await invoices_collection.find(
        query,
        {"_id": 0, "invoice_id": 1, "invoice_number": 1, "invoice_date": 1, "due_date": 1,
         "grand_total": 1, "balance_due": 1, "status": 1, "is_sent": 1}
    ).sort("invoice_date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "invoices": invoices,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/invoices/{invoice_id}")
async def get_portal_invoice_detail(session_token: str, invoice_id: str):
    """Get invoice details for portal"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    invoice = await invoices_collection.find_one(
        {"invoice_id": invoice_id, "customer_id": contact_id, "status": {"$nin": ["draft", "void"]}},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get line items
    line_items = await db["invoice_line_items"].find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).to_list(100)
    invoice["line_items"] = line_items
    
    # Get payments
    payments = await payments_collection.find(
        {"invoice_id": invoice_id},
        {"_id": 0, "payment_id": 1, "amount": 1, "payment_date": 1, "payment_mode": 1}
    ).sort("payment_date", -1).to_list(50)
    invoice["payments"] = payments
    
    # Mark as viewed if first time
    if not invoice.get("viewed_date"):
        await invoices_collection.update_one(
            {"invoice_id": invoice_id},
            {"$set": {"viewed_date": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"code": 0, "invoice": invoice}

# ========================= ESTIMATES =========================

@router.get("/estimates")
async def get_portal_estimates(
    session_token: str,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
):
    """Get customer's estimates/quotes"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    query = {"customer_id": contact_id, "status": {"$nin": ["draft"]}}
    if status:
        query["status"] = status
    
    total = await estimates_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    estimates = await estimates_collection.find(
        query,
        {"_id": 0, "estimate_id": 1, "estimate_number": 1, "estimate_date": 1, "expiry_date": 1,
         "grand_total": 1, "status": 1}
    ).sort("estimate_date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "estimates": estimates,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/estimates/{estimate_id}")
async def get_portal_estimate_detail(session_token: str, estimate_id: str):
    """Get estimate details for portal"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    estimate = await estimates_collection.find_one(
        {"estimate_id": estimate_id, "customer_id": contact_id, "status": {"$ne": "draft"}},
        {"_id": 0}
    )
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Get line items
    line_items = await db["estimate_line_items"].find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).to_list(100)
    estimate["line_items"] = line_items
    
    return {"code": 0, "estimate": estimate}

@router.post("/estimates/{estimate_id}/accept")
async def accept_portal_estimate(session_token: str, estimate_id: str):
    """Accept an estimate from portal"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    estimate = await estimates_collection.find_one(
        {"estimate_id": estimate_id, "customer_id": contact_id, "status": "sent"}
    )
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found or not in sent status")
    
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "accepted",
            "accepted_date": datetime.now(timezone.utc).isoformat(),
            "accepted_via": "portal",
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"code": 0, "message": "Estimate accepted"}

@router.post("/estimates/{estimate_id}/decline")
async def decline_portal_estimate(session_token: str, estimate_id: str, reason: str = ""):
    """Decline an estimate from portal"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    estimate = await estimates_collection.find_one(
        {"estimate_id": estimate_id, "customer_id": contact_id, "status": "sent"}
    )
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found or not in sent status")
    
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "declined",
            "declined_date": datetime.now(timezone.utc).isoformat(),
            "declined_via": "portal",
            "decline_reason": reason,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"code": 0, "message": "Estimate declined"}

# ========================= STATEMENT =========================

@router.get("/statement")
async def get_portal_statement(
    session_token: str,
    start_date: str = "",
    end_date: str = ""
):
    """Get account statement for portal"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    # Build query
    query = {"customer_id": contact_id, "status": {"$nin": ["draft", "void"]}}
    if start_date:
        query["invoice_date"] = {"$gte": start_date}
    if end_date:
        if "invoice_date" in query:
            query["invoice_date"]["$lte"] = end_date
        else:
            query["invoice_date"] = {"$lte": end_date}
    
    # Get invoices
    invoices = await invoices_collection.find(
        query,
        {"_id": 0, "invoice_id": 1, "invoice_number": 1, "invoice_date": 1, "due_date": 1,
         "grand_total": 1, "balance_due": 1, "status": 1}
    ).sort("invoice_date", 1).to_list(500)
    
    # Get payments
    payments = await payments_collection.find(
        {"customer_id": contact_id},
        {"_id": 0, "payment_id": 1, "invoice_id": 1, "amount": 1, "payment_date": 1, "payment_mode": 1}
    ).sort("payment_date", 1).to_list(500)
    
    # Calculate totals
    total_invoiced = sum(inv.get("grand_total", 0) for inv in invoices)
    total_paid = sum(p.get("amount", 0) for p in payments)
    balance = total_invoiced - total_paid
    
    return {
        "code": 0,
        "statement": {
            "period": {"start_date": start_date, "end_date": end_date},
            "invoices": invoices,
            "payments": payments,
            "summary": {
                "total_invoiced": round(total_invoiced, 2),
                "total_paid": round(total_paid, 2),
                "balance_due": round(balance, 2)
            }
        }
    }

# ========================= PAYMENTS =========================

@router.get("/payments")
async def get_portal_payments(session_token: str, page: int = 1, per_page: int = 20):
    """Get customer's payment history"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    total = await payments_collection.count_documents({"customer_id": contact_id})
    skip = (page - 1) * per_page
    
    payments = await payments_collection.find(
        {"customer_id": contact_id},
        {"_id": 0}
    ).sort("payment_date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "payments": payments,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

# ========================= PROFILE =========================

@router.get("/profile")
async def get_portal_profile(session_token: str):
    """Get customer profile for portal"""
    session = await get_portal_session(session_token)
    contact_id = session["contact_id"]
    
    contact = await contacts_collection.find_one(
        {"contact_id": contact_id},
        {"_id": 0, "portal_token": 0}
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Get addresses
    addresses = await db["addresses"].find(
        {"contact_id": contact_id},
        {"_id": 0}
    ).to_list(20)
    contact["addresses"] = addresses
    
    return {"code": 0, "profile": contact}
