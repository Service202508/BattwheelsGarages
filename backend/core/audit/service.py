"""
Audit Service
Tracks all sensitive actions across the platform
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Standard audit actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    STATUS_CHANGE = "status_change"
    PAYMENT = "payment"
    INVOICE = "invoice"
    SETTINGS_CHANGE = "settings_change"


class AuditLog(BaseModel):
    """Audit log entry"""
    audit_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    organization_id: str
    user_id: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    # Action details
    action: AuditAction
    resource_type: str  # e.g., "ticket", "invoice", "vehicle"
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Change details
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changes_summary: Optional[str] = None
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditService:
    """Service for audit logging"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.audit_logs = db.audit_logs
    
    async def log(
        self,
        organization_id: str,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        changes_summary: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        
        # Get user details
        user = await self.db.users.find_one(
            {"user_id": user_id},
            {"email": 1, "name": 1}
        )
        
        log_entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            user_email=user.get("email") if user else None,
            user_name=user.get("name") if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            old_values=old_values,
            new_values=new_values,
            changes_summary=changes_summary,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        await self.audit_logs.insert_one(log_entry.model_dump())
        
        logger.info(
            f"AUDIT: {action} on {resource_type}/{resource_id} "
            f"by {user_id} in org {organization_id}"
        )
        
        return log_entry
    
    async def get_logs(
        self,
        organization_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Query audit logs with filters"""
        
        query = {"organization_id": organization_id}
        
        if resource_type:
            query["resource_type"] = resource_type
        if resource_id:
            query["resource_id"] = resource_id
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            query.setdefault("timestamp", {})["$lte"] = end_date
        
        total = await self.audit_logs.count_documents(query)
        skip = (page - 1) * per_page
        
        cursor = self.audit_logs.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(per_page)
        
        logs = [AuditLog(**doc) async for doc in cursor]
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    async def get_resource_history(
        self,
        organization_id: str,
        resource_type: str,
        resource_id: str
    ) -> List[AuditLog]:
        """Get complete history for a specific resource"""
        
        cursor = self.audit_logs.find(
            {
                "organization_id": organization_id,
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            {"_id": 0}
        ).sort("timestamp", -1)
        
        return [AuditLog(**doc) async for doc in cursor]


# Singleton
_audit_service: Optional[AuditService] = None


def init_audit_service(db: AsyncIOMotorDatabase) -> AuditService:
    """Initialize audit service"""
    global _audit_service
    _audit_service = AuditService(db)
    return _audit_service


def get_audit_service() -> AuditService:
    """Get audit service instance"""
    if _audit_service is None:
        raise RuntimeError("Audit service not initialized")
    return _audit_service


# ==================== HELPER DECORATOR ====================

def audit_action(action: AuditAction, resource_type: str):
    """
    Decorator to automatically audit route actions
    
    Usage:
        @router.post("/tickets")
        @audit_action(AuditAction.CREATE, "ticket")
        async def create_ticket(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Try to extract context and log
            try:
                request = kwargs.get("request")
                if request and hasattr(request.state, "org_context"):
                    ctx = request.state.org_context
                    
                    # Extract resource info from result
                    resource_id = None
                    resource_name = None
                    if isinstance(result, dict):
                        resource_id = result.get("id") or result.get(f"{resource_type}_id")
                        resource_name = result.get("name") or result.get("title")
                    
                    audit_svc = get_audit_service()
                    await audit_svc.log(
                        organization_id=ctx.organization_id,
                        user_id=ctx.user_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        resource_name=resource_name,
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent")
                    )
            except Exception as e:
                logger.warning(f"Failed to create audit log: {e}")
            
            return result
        return wrapper
    return decorator
