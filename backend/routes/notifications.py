"""
Notification Service - Event-Driven Notifications
Handles notifications for invoice status, AMC expiry, stock alerts, and more
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
import uuid
import logging
from fastapi import Request
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])

# Database connection
def get_db():
    from server import db
    return db

# ============== MODELS ==============

class NotificationCreate(BaseModel):
    user_id: Optional[str] = ""
    role: Optional[str] = ""  # admin, technician, manager, customer
    notification_type: str  # invoice_sent, invoice_paid, invoice_overdue, amc_expiring, low_stock, ticket_update
    title: str
    message: str
    entity_type: Optional[str] = ""  # invoice, amc, item, ticket
    entity_id: Optional[str] = ""
    priority: str = "normal"  # low, normal, high, urgent
    metadata: Optional[Dict] = {}

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None

# ============== NOTIFICATION CRUD ==============

@router.post("")
async def create_notification(notification: NotificationCreate, request: Request)::
    org_id = extract_org_id(request)
    """Create a new notification"""
    db = get_db()
    notification_id = f"NOTIF-{uuid.uuid4().hex[:12].upper()}"
    
    notification_dict = {
        "notification_id": notification_id,
        **notification.dict(),
        "is_read": False,
        "is_archived": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_at": None
    }
    
    await db.notifications.insert_one(notification_dict)
    del notification_dict["_id"]
    
    return {"code": 0, "message": "Notification created", "notification": notification_dict}

@router.get("")
async def list_notifications(
    user_id: str = "",
    role: str = "",
    notification_type: str = "",
    is_read: str = "",
    priority: str = "",
    page: int = 1,
    per_page: int = 50, request: Request)::
    org_id = extract_org_id(request)
    """List notifications with filters"""
    db = get_db()
    query = {"is_archived": False}
    
    if user_id:
        query["$or"] = [{"user_id": user_id}, {"user_id": ""}, {"user_id": {"$exists": False}}]
    if role:
        query["$or"] = query.get("$or", []) + [{"role": role}, {"role": ""}, {"role": {"$exists": False}}]
    if notification_type:
        query["notification_type"] = notification_type
    if is_read:
        query["is_read"] = is_read.lower() == "true"
    if priority:
        query["priority"] = priority
    
    skip = (page - 1) * per_page
    cursor = db.notifications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(per_page)
    notifications = await cursor.to_list(length=per_page)
    total = await db.notifications.count_documents(query)
    unread = await db.notifications.count_documents({**query, "is_read": False})
    
    return {
        "code": 0,
        "notifications": notifications,
        "unread_count": unread,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/unread-count")
async def get_unread_count(user_id: str = "", role: str = "", request: Request)::
    org_id = extract_org_id(request)
    """Get unread notification count"""
    db = get_db()
    query = {"is_read": False, "is_archived": False}
    
    if user_id or role:
        query["$or"] = []
        if user_id:
            query["$or"].extend([{"user_id": user_id}, {"user_id": ""}, {"user_id": {"$exists": False}}])
        if role:
            query["$or"].extend([{"role": role}, {"role": ""}, {"role": {"$exists": False}}])
    
    count = await db.notifications.count_documents(query)
    return {"code": 0, "unread_count": count}

@router.get("/{notification_id}")
async def get_notification(notification_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Get notification details"""
    db = get_db()
    notification = await db.notifications.find_one({"notification_id": notification_id}, {"_id": 0})
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"code": 0, "notification": notification}

@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Mark notification as read"""
    db = get_db()
    result = await db.notifications.update_one(
        {"notification_id": notification_id},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"code": 0, "message": "Notification marked as read"}

@router.put("/mark-all-read")
async def mark_all_as_read(user_id: str = "", role: str = "", request: Request)::
    org_id = extract_org_id(request)
    """Mark all notifications as read"""
    db = get_db()
    query = {"is_read": False}
    
    if user_id or role:
        query["$or"] = []
        if user_id:
            query["$or"].extend([{"user_id": user_id}, {"user_id": ""}, {"user_id": {"$exists": False}}])
        if role:
            query["$or"].extend([{"role": role}, {"role": ""}, {"role": {"$exists": False}}])
    
    result = await db.notifications.update_many(
        query,
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"code": 0, "message": f"{result.modified_count} notifications marked as read"}

@router.delete("/{notification_id}")
async def archive_notification(notification_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Archive (soft delete) notification"""
    db = get_db()
    result = await db.notifications.update_one(
        {"notification_id": notification_id},
        {"$set": {"is_archived": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"code": 0, "message": "Notification archived"}

# ============== EVENT TRIGGERS ==============

async def notify_invoice_sent(invoice_id: str, invoice_number: str, customer_name: str, total: float):
    """Trigger notification when invoice is sent"""
    db = get_db()
    await create_notification(NotificationCreate(
        role="admin",
        notification_type="invoice_sent",
        title="Invoice Sent",
        message=f"Invoice {invoice_number} for ₹{total:,.2f} sent to {customer_name}",
        entity_type="invoice",
        entity_id=invoice_id,
        priority="normal"
    ))

async def notify_invoice_paid(invoice_id: str, invoice_number: str, customer_name: str, amount: float):
    """Trigger notification when invoice is paid"""
    db = get_db()
    await create_notification(NotificationCreate(
        role="admin",
        notification_type="invoice_paid",
        title="Payment Received",
        message=f"Payment of ₹{amount:,.2f} received for invoice {invoice_number} from {customer_name}",
        entity_type="invoice",
        entity_id=invoice_id,
        priority="normal",
        metadata={"amount": amount}
    ))

async def notify_invoice_overdue(invoice_id: str, invoice_number: str, customer_name: str, balance: float, days_overdue: int):
    """Trigger notification for overdue invoice"""
    db = get_db()
    priority = "high" if days_overdue > 30 else "normal"
    await create_notification(NotificationCreate(
        role="admin",
        notification_type="invoice_overdue",
        title="Invoice Overdue",
        message=f"Invoice {invoice_number} from {customer_name} is {days_overdue} days overdue. Balance: ₹{balance:,.2f}",
        entity_type="invoice",
        entity_id=invoice_id,
        priority=priority,
        metadata={"days_overdue": days_overdue, "balance": balance}
    ))

async def notify_amc_expiring(amc_id: str, customer_name: str, vehicle_number: str, expiry_date: str, days_until_expiry: int):
    """Trigger notification for expiring AMC"""
    db = get_db()
    priority = "urgent" if days_until_expiry <= 7 else "high" if days_until_expiry <= 15 else "normal"
    await create_notification(NotificationCreate(
        role="admin",
        notification_type="amc_expiring",
        title="AMC Expiring Soon",
        message=f"AMC for {vehicle_number} ({customer_name}) expires in {days_until_expiry} days on {expiry_date}",
        entity_type="amc",
        entity_id=amc_id,
        priority=priority,
        metadata={"days_until_expiry": days_until_expiry, "vehicle_number": vehicle_number}
    ))

async def notify_low_stock(item_id: str, item_name: str, current_stock: int, reorder_level: int):
    """Trigger notification for low stock"""
    db = get_db()
    await create_notification(NotificationCreate(
        role="admin",
        notification_type="low_stock",
        title="Low Stock Alert",
        message=f"Stock for '{item_name}' is low ({current_stock} units). Reorder level: {reorder_level}",
        entity_type="item",
        entity_id=item_id,
        priority="high",
        metadata={"current_stock": current_stock, "reorder_level": reorder_level}
    ))

async def notify_ticket_update(ticket_id: str, ticket_number: str, status: str, customer_id: str = ""):
    """Trigger notification for ticket status update"""
    db = get_db()
    await create_notification(NotificationCreate(
        user_id=customer_id,
        role="",
        notification_type="ticket_update",
        title="Service Ticket Update",
        message=f"Ticket {ticket_number} status updated to: {status}",
        entity_type="ticket",
        entity_id=ticket_id,
        priority="normal"
    ))

# ============== SCHEDULED CHECKS ==============

@router.post("/check-overdue-invoices")
async def check_overdue_invoices(request: Request)::
    org_id = extract_org_id(request)
    """Check and create notifications for overdue invoices"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    # Find invoices with balance > 0 and due_date < today
    invoices = await db.invoices.find(
        {"balance": {"$gt": 0}, "status": {"$nin": ["paid", "void"]}},
        {"_id": 0}
    ).to_list(length=1000)
    
    count = 0
    for inv in invoices:
        try:
            due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if due_date < today:
                days_overdue = (today - due_date).days
                # Check if notification already exists for this invoice (last 24h)
                existing = await db.notifications.find_one({
                    "entity_id": inv["invoice_id"],
                    "notification_type": "invoice_overdue",
                    "created_at": {"$gte": (today - timedelta(days=1)).isoformat()}
                })
                if not existing:
                    await notify_invoice_overdue(
                        inv["invoice_id"],
                        inv["invoice_number"],
                        inv.get("customer_name", "Unknown"),
                        inv["balance"],
                        days_overdue
                    )
                    count += 1
        except:
            continue
    
    return {"code": 0, "message": f"Created {count} overdue invoice notifications"}

@router.post("/check-expiring-amcs")
async def check_expiring_amcs(request: Request)::
    org_id = extract_org_id(request)
    """Check and create notifications for expiring AMCs"""
    db = get_db()
    today = datetime.now(timezone.utc)
    check_until = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Find AMCs expiring in next 30 days
    amcs = await db.amcs.find(
        {
            "status": "active",
            "end_date": {"$lte": check_until, "$gte": today.strftime("%Y-%m-%d")}
        },
        {"_id": 0}
    ).to_list(length=500)
    
    count = 0
    for amc in amcs:
        try:
            expiry_date = datetime.strptime(amc["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_until_expiry = (expiry_date - today).days
            
            # Check if notification already exists (last 7 days)
            existing = await db.notifications.find_one({
                "entity_id": amc["amc_id"],
                "notification_type": "amc_expiring",
                "created_at": {"$gte": (today - timedelta(days=7)).isoformat()}
            })
            if not existing:
                await notify_amc_expiring(
                    amc["amc_id"],
                    amc.get("customer_name", "Unknown"),
                    amc.get("vehicle_number", "Unknown"),
                    amc["end_date"],
                    days_until_expiry
                )
                count += 1
        except:
            continue
    
    return {"code": 0, "message": f"Created {count} expiring AMC notifications"}

@router.post("/check-low-stock")
async def check_low_stock(request: Request)::
    org_id = extract_org_id(request)
    """Check and create notifications for low stock items"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    # Find items with stock below reorder level
    items = await db.items.find(
        {
            "stock_on_hand": {"$exists": True},
            "reorder_level": {"$exists": True},
            "$expr": {"$lt": ["$stock_on_hand", "$reorder_level"]}
        },
        {"_id": 0}
    ).to_list(length=500)
    
    count = 0
    for item in items:
        try:
            # Check if notification already exists (last 24h)
            existing = await db.notifications.find_one({
                "entity_id": item["item_id"],
                "notification_type": "low_stock",
                "created_at": {"$gte": (today - timedelta(days=1)).isoformat()}
            })
            if not existing:
                await notify_low_stock(
                    item["item_id"],
                    item.get("name", "Unknown"),
                    item.get("stock_on_hand", 0),
                    item.get("reorder_level", 0)
                )
                count += 1
        except:
            continue
    
    return {"code": 0, "message": f"Created {count} low stock notifications"}

# ============== NOTIFICATION PREFERENCES ==============

class NotificationPreference(BaseModel):
    user_id: str
    email_notifications: bool = True
    push_notifications: bool = True
    invoice_alerts: bool = True
    amc_alerts: bool = True
    stock_alerts: bool = True
    ticket_alerts: bool = True

@router.get("/preferences/{user_id}")
async def get_notification_preferences(user_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Get user notification preferences"""
    db = get_db()
    prefs = await db.notification_preferences.find_one({"user_id": user_id}, {"_id": 0})
    if not prefs:
        # Return default preferences
        prefs = {
            "user_id": user_id,
            "email_notifications": True,
            "push_notifications": True,
            "invoice_alerts": True,
            "amc_alerts": True,
            "stock_alerts": True,
            "ticket_alerts": True
        }
    return {"code": 0, "preferences": prefs}

@router.put("/preferences/{user_id}")
async def update_notification_preferences(user_id: str, prefs: NotificationPreference, request: Request)::
    org_id = extract_org_id(request)
    """Update user notification preferences"""
    db = get_db()
    prefs_dict = prefs.dict()
    await db.notification_preferences.update_one(
        {"user_id": user_id},
        {"$set": prefs_dict},
        upsert=True
    )
    return {"code": 0, "message": "Preferences updated", "preferences": prefs_dict}
