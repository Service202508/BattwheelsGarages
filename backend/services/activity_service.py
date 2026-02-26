# Activity Log Service
# Unified activity tracking for all modules - Activity tracking
# Provides consistent history logging and activity feeds

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import motor.motor_asyncio
import os
import uuid

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_dev")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
activity_log_collection = db["activity_logs"]

# ========================= ACTIVITY TYPES =========================

class ActivityType:
    """Standard activity types matching Battwheels"""
    # Document lifecycle
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    VOIDED = "voided"
    
    # Status changes
    STATUS_CHANGED = "status_changed"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    
    # Financial actions
    PAYMENT_RECORDED = "payment_recorded"
    PAYMENT_REMOVED = "payment_removed"
    REFUND_ISSUED = "refund_issued"
    CREDIT_APPLIED = "credit_applied"
    WRITE_OFF = "write_off"
    
    # Conversions
    CONVERTED = "converted"
    CLONED = "cloned"
    
    # Document actions
    PDF_GENERATED = "pdf_generated"
    PDF_DOWNLOADED = "pdf_downloaded"
    EMAIL_SENT = "email_sent"
    SHARE_LINK_CREATED = "share_link_created"
    SHARE_LINK_REVOKED = "share_link_revoked"
    
    # Attachments
    ATTACHMENT_ADDED = "attachment_added"
    ATTACHMENT_REMOVED = "attachment_removed"
    
    # Comments
    COMMENT_ADDED = "comment_added"
    COMMENT_REMOVED = "comment_removed"
    
    # Inventory
    STOCK_ADJUSTED = "stock_adjusted"
    FULFILLED = "fulfilled"

class EntityType:
    """Entity types for activity logging"""
    ESTIMATE = "estimate"
    QUOTE = "quote"
    INVOICE = "invoice"
    SALES_ORDER = "sales_order"
    PAYMENT = "payment"
    CREDIT_NOTE = "credit_note"
    CUSTOMER = "customer"
    VENDOR = "vendor"
    CONTACT = "contact"
    ITEM = "item"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"
    BILL = "bill"
    EXPENSE = "expense"

# ========================= HELPER FUNCTIONS =========================

def generate_activity_id() -> str:
    return f"ACT-{uuid.uuid4().hex[:12].upper()}"

def get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

# ========================= CORE FUNCTIONS =========================

async def log_activity(
    entity_type: str,
    entity_id: str,
    activity_type: str,
    description: str,
    details: Dict = None,
    old_value: Any = None,
    new_value: Any = None,
    user_id: str = "system",
    user_name: str = "System",
    organization_id: str = "",
    related_entity_type: str = "",
    related_entity_id: str = "",
    metadata: Dict = None
) -> str:
    """
    Log an activity event.
    
    Args:
        entity_type: Type of entity (invoice, estimate, payment, etc.)
        entity_id: ID of the entity
        activity_type: Type of activity (created, updated, status_changed, etc.)
        description: Human-readable description
        details: Additional details dict
        old_value: Previous value (for updates)
        new_value: New value (for updates)
        user_id: ID of user performing action
        user_name: Name of user
        organization_id: Organization ID
        related_entity_type: Related entity type (e.g., invoice for payment)
        related_entity_id: Related entity ID
        metadata: Additional metadata
    
    Returns:
        Activity log ID
    """
    activity_id = generate_activity_id()
    
    activity_doc = {
        "activity_id": activity_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "activity_type": activity_type,
        "description": description,
        "details": details or {},
        "old_value": old_value,
        "new_value": new_value,
        "user_id": user_id,
        "user_name": user_name,
        "organization_id": organization_id,
        "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
        "metadata": metadata or {},
        "timestamp": get_timestamp(),
        "created_at": get_timestamp()
    }
    
    await activity_log_collection.insert_one(activity_doc)
    return activity_id

async def get_entity_activities(
    entity_type: str,
    entity_id: str,
    limit: int = 50,
    skip: int = 0,
    activity_types: List[str] = None
) -> List[Dict]:
    """
    Get activity history for a specific entity.
    """
    query = {
        "entity_type": entity_type,
        "entity_id": entity_id
    }
    
    if activity_types:
        query["activity_type"] = {"$in": activity_types}
    
    activities = await activity_log_collection.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    return activities

async def get_related_activities(
    entity_type: str,
    entity_id: str,
    include_related: bool = True,
    limit: int = 50
) -> List[Dict]:
    """
    Get activities for an entity and optionally its related entities.
    """
    if include_related:
        query = {
            "$or": [
                {"entity_type": entity_type, "entity_id": entity_id},
                {"related_entity_type": entity_type, "related_entity_id": entity_id}
            ]
        }
    else:
        query = {"entity_type": entity_type, "entity_id": entity_id}
    
    activities = await activity_log_collection.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return activities

async def get_user_activities(
    user_id: str,
    entity_types: List[str] = None,
    limit: int = 50,
    from_date: str = None,
    to_date: str = None
) -> List[Dict]:
    """
    Get activities performed by a specific user.
    """
    query = {"user_id": user_id}
    
    if entity_types:
        query["entity_type"] = {"$in": entity_types}
    
    if from_date:
        query["timestamp"] = {"$gte": from_date}
    if to_date:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = to_date
        else:
            query["timestamp"] = {"$lte": to_date}
    
    activities = await activity_log_collection.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return activities

async def get_organization_feed(
    organization_id: str,
    entity_types: List[str] = None,
    limit: int = 100,
    from_date: str = None
) -> List[Dict]:
    """
    Get activity feed for an organization.
    """
    query = {"organization_id": organization_id}
    
    if entity_types:
        query["entity_type"] = {"$in": entity_types}
    
    if from_date:
        query["timestamp"] = {"$gte": from_date}
    
    activities = await activity_log_collection.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return activities

# ========================= CONVENIENCE FUNCTIONS =========================

async def log_create(
    entity_type: str,
    entity_id: str,
    entity_number: str,
    user_id: str = "system",
    user_name: str = "System",
    details: Dict = None
) -> str:
    """Log entity creation"""
    return await log_activity(
        entity_type=entity_type,
        entity_id=entity_id,
        activity_type=ActivityType.CREATED,
        description=f"{entity_type.replace('_', ' ').title()} {entity_number} was created",
        details=details or {"entity_number": entity_number},
        user_id=user_id,
        user_name=user_name
    )

async def log_update(
    entity_type: str,
    entity_id: str,
    entity_number: str,
    changed_fields: List[str] = None,
    user_id: str = "system",
    user_name: str = "System"
) -> str:
    """Log entity update"""
    return await log_activity(
        entity_type=entity_type,
        entity_id=entity_id,
        activity_type=ActivityType.UPDATED,
        description=f"{entity_type.replace('_', ' ').title()} {entity_number} was updated",
        details={"changed_fields": changed_fields or []},
        user_id=user_id,
        user_name=user_name
    )

async def log_status_change(
    entity_type: str,
    entity_id: str,
    entity_number: str,
    old_status: str,
    new_status: str,
    user_id: str = "system",
    user_name: str = "System"
) -> str:
    """Log status change"""
    return await log_activity(
        entity_type=entity_type,
        entity_id=entity_id,
        activity_type=ActivityType.STATUS_CHANGED,
        description=f"Status changed from '{old_status}' to '{new_status}'",
        old_value=old_status,
        new_value=new_status,
        details={"old_status": old_status, "new_status": new_status},
        user_id=user_id,
        user_name=user_name
    )

async def log_email_sent(
    entity_type: str,
    entity_id: str,
    entity_number: str,
    recipient_email: str,
    user_id: str = "system",
    user_name: str = "System"
) -> str:
    """Log email sent"""
    return await log_activity(
        entity_type=entity_type,
        entity_id=entity_id,
        activity_type=ActivityType.EMAIL_SENT,
        description=f"Email sent to {recipient_email}",
        details={"recipient": recipient_email},
        user_id=user_id,
        user_name=user_name
    )

async def log_payment(
    entity_type: str,
    entity_id: str,
    entity_number: str,
    payment_amount: float,
    payment_id: str,
    payment_mode: str = "",
    user_id: str = "system",
    user_name: str = "System"
) -> str:
    """Log payment recorded"""
    return await log_activity(
        entity_type=entity_type,
        entity_id=entity_id,
        activity_type=ActivityType.PAYMENT_RECORDED,
        description=f"Payment of ₹{payment_amount:,.2f} recorded",
        details={
            "payment_amount": payment_amount,
            "payment_id": payment_id,
            "payment_mode": payment_mode
        },
        related_entity_type="payment",
        related_entity_id=payment_id,
        user_id=user_id,
        user_name=user_name
    )

async def log_conversion(
    source_entity_type: str,
    source_entity_id: str,
    source_number: str,
    target_entity_type: str,
    target_entity_id: str,
    target_number: str,
    user_id: str = "system",
    user_name: str = "System"
) -> str:
    """Log entity conversion"""
    return await log_activity(
        entity_type=source_entity_type,
        entity_id=source_entity_id,
        activity_type=ActivityType.CONVERTED,
        description=f"Converted to {target_entity_type.replace('_', ' ')} {target_number}",
        details={
            "target_entity_type": target_entity_type,
            "target_entity_id": target_entity_id,
            "target_number": target_number
        },
        related_entity_type=target_entity_type,
        related_entity_id=target_entity_id,
        user_id=user_id,
        user_name=user_name
    )

async def log_void(
    entity_type: str,
    entity_id: str,
    entity_number: str,
    reason: str = "",
    user_id: str = "system",
    user_name: str = "System"
) -> str:
    """Log entity voided"""
    return await log_activity(
        entity_type=entity_type,
        entity_id=entity_id,
        activity_type=ActivityType.VOIDED,
        description=f"{entity_type.replace('_', ' ').title()} {entity_number} was voided",
        details={"reason": reason},
        user_id=user_id,
        user_name=user_name
    )

async def log_delete(
    entity_type: str,
    entity_id: str,
    entity_number: str,
    user_id: str = "system",
    user_name: str = "System"
) -> str:
    """Log entity deleted"""
    return await log_activity(
        entity_type=entity_type,
        entity_id=entity_id,
        activity_type=ActivityType.DELETED,
        description=f"{entity_type.replace('_', ' ').title()} {entity_number} was deleted",
        user_id=user_id,
        user_name=user_name
    )

# ========================= ACTIVITY FEED FORMATTING =========================

def format_activity_for_display(activity: Dict) -> Dict:
    """
    Format activity for UI display.
    Returns a consistent structure for rendering activity items.
    """
    activity_type = activity.get("activity_type", "")
    
    # Determine icon based on activity type
    icons = {
        ActivityType.CREATED: "plus-circle",
        ActivityType.UPDATED: "edit",
        ActivityType.DELETED: "trash",
        ActivityType.VOIDED: "x-circle",
        ActivityType.STATUS_CHANGED: "refresh",
        ActivityType.SENT: "send",
        ActivityType.VIEWED: "eye",
        ActivityType.ACCEPTED: "check-circle",
        ActivityType.DECLINED: "x-circle",
        ActivityType.PAYMENT_RECORDED: "dollar-sign",
        ActivityType.CONVERTED: "arrow-right",
        ActivityType.EMAIL_SENT: "mail",
        ActivityType.ATTACHMENT_ADDED: "paperclip",
        ActivityType.COMMENT_ADDED: "message-square"
    }
    
    # Determine color based on activity type
    colors = {
        ActivityType.CREATED: "green",
        ActivityType.UPDATED: "blue",
        ActivityType.DELETED: "red",
        ActivityType.VOIDED: "red",
        ActivityType.ACCEPTED: "green",
        ActivityType.DECLINED: "orange",
        ActivityType.PAYMENT_RECORDED: "green",
        ActivityType.EMAIL_SENT: "blue"
    }
    
    return {
        "id": activity.get("activity_id"),
        "type": activity_type,
        "description": activity.get("description"),
        "icon": icons.get(activity_type, "activity"),
        "color": colors.get(activity_type, "gray"),
        "timestamp": activity.get("timestamp"),
        "user": activity.get("user_name", "System"),
        "details": activity.get("details", {}),
        "entity": {
            "type": activity.get("entity_type"),
            "id": activity.get("entity_id")
        },
        "related": {
            "type": activity.get("related_entity_type"),
            "id": activity.get("related_entity_id")
        } if activity.get("related_entity_id") else None
    }
