"""
Tenant Audit Module
==================

Comprehensive audit logging for all tenant actions.

Every sensitive operation is logged with:
- organization_id
- user_id
- action type
- before/after state
- IP address
- request context

This provides:
1. Compliance-grade audit trail
2. Security incident investigation
3. Change tracking for billing disputes
4. Cross-tenant access detection
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from functools import wraps
import uuid
import logging

from .context import TenantContext, get_tenant_context
from .exceptions import TenantContextMissing

logger = logging.getLogger(__name__)


class TenantAuditAction(str, Enum):
    """Standard audit actions"""
    # CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "pwd_change_event"
    
    # Data
    EXPORT = "export"
    IMPORT = "import"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"
    
    # Business
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    UNASSIGN = "unassign"
    STATUS_CHANGE = "status_change"
    
    # Financial
    PAYMENT = "payment"
    REFUND = "refund"
    INVOICE_SEND = "invoice_send"
    
    # Admin
    SETTINGS_CHANGE = "settings_change"
    ROLE_CHANGE = "role_change"
    PERMISSION_CHANGE = "permission_change"
    USER_INVITE = "user_invite"
    USER_REMOVE = "user_remove"
    
    # Integration
    SYNC_START = "sync_start"
    SYNC_COMPLETE = "sync_complete"
    INTEGRATION_CONNECT = "integration_connect"
    INTEGRATION_DISCONNECT = "integration_disconnect"
    
    # Security
    ACCESS_DENIED = "access_denied"
    BOUNDARY_VIOLATION = "boundary_violation"
    RATE_LIMIT_HIT = "rate_limit_hit"


class TenantAuditSeverity(str, Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TenantAuditLog(BaseModel):
    """Audit log entry model"""
    audit_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    
    # Tenant context (required)
    organization_id: str
    user_id: str
    request_id: Optional[str] = None
    
    # User info
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    
    # Action details
    action: TenantAuditAction
    severity: TenantAuditSeverity = TenantAuditSeverity.INFO
    
    # Resource
    resource_type: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Change details
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changes_summary: Optional[str] = None
    
    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    # Result
    success: bool = True
    error_message: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TenantAuditService:
    """
    Service for tenant audit logging.
    
    Usage:
        audit = TenantAuditService(db)
        await audit.log(
            ctx=tenant_context,
            action=TenantAuditAction.CREATE,
            resource_type="ticket",
            resource_id="tkt_xxx",
            new_values={"title": "New ticket", "status": "open"}
        )
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.tenant_audit_logs
    
    async def log(
        self,
        ctx: TenantContext,
        action: TenantAuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        changes_summary: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: TenantAuditSeverity = None,
        metadata: Optional[Dict] = None
    ) -> TenantAuditLog:
        """Create an audit log entry"""
        
        # Auto-determine severity
        if severity is None:
            severity = self._determine_severity(action, success)
        
        # Get user details
        user = await self.db.users.find_one(
            {"user_id": ctx.user_id},
            {"email": 1, "name": 1, "_id": 0}
        )
        
        log_entry = TenantAuditLog(
            organization_id=ctx.org_id,
            user_id=ctx.user_id,
            request_id=ctx.request_id,
            user_email=user.get("email") if user else None,
            user_name=user.get("name") if user else None,
            user_role=ctx.user_role,
            action=action,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            old_values=self._sanitize_values(old_values),
            new_values=self._sanitize_values(new_values),
            changes_summary=changes_summary,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        await self.collection.insert_one(log_entry.model_dump())
        
        # Log at appropriate level
        log_msg = (
            f"AUDIT: {action.value} {resource_type}"
            f"{f'/{resource_id}' if resource_id else ''} "
            f"by {ctx.user_id} in org {ctx.org_id}"
        )
        
        if severity == TenantAuditSeverity.CRITICAL:
            logger.critical(log_msg)
        elif severity == TenantAuditSeverity.ERROR:
            logger.error(log_msg)
        elif severity == TenantAuditSeverity.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        return log_entry
    
    async def log_security_event(
        self,
        organization_id: str,
        user_id: str,
        action: TenantAuditAction,
        details: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log a security-related event (can be called without full context)"""
        log_entry = TenantAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            severity=TenantAuditSeverity.CRITICAL,
            resource_type="security",
            changes_summary=details,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        await self.collection.insert_one(log_entry.model_dump())
        logger.critical(f"SECURITY: {action.value} - {details} (user={user_id}, org={organization_id})")
    
    async def get_logs(
        self,
        ctx: TenantContext,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[TenantAuditAction] = None,
        severity: Optional[TenantAuditSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Query audit logs for the tenant"""
        
        # ALWAYS filter by organization_id
        query = {"organization_id": ctx.org_id}
        
        if resource_type:
            query["resource_type"] = resource_type
        if resource_id:
            query["resource_id"] = resource_id
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action.value
        if severity:
            query["severity"] = severity.value
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            query.setdefault("timestamp", {})["$lte"] = end_date
        
        total = await self.collection.count_documents(query)
        skip = (page - 1) * per_page
        
        cursor = self.collection.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(per_page)
        
        logs = await cursor.to_list(length=per_page)
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    async def get_resource_history(
        self,
        ctx: TenantContext,
        resource_type: str,
        resource_id: str
    ) -> List[Dict]:
        """Get complete audit history for a resource"""
        cursor = self.collection.find(
            {
                "organization_id": ctx.org_id,
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            {"_id": 0}
        ).sort("timestamp", -1)
        
        return await cursor.to_list(length=None)
    
    async def get_user_activity(
        self,
        ctx: TenantContext,
        user_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get user's activity in the tenant"""
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        cursor = self.collection.find(
            {
                "organization_id": ctx.org_id,
                "user_id": user_id,
                "timestamp": {"$gte": start_date}
            },
            {"_id": 0}
        ).sort("timestamp", -1)
        
        return await cursor.to_list(length=None)
    
    def _determine_severity(
        self,
        action: TenantAuditAction,
        success: bool
    ) -> TenantAuditSeverity:
        """Auto-determine severity based on action"""
        if not success:
            if action in [TenantAuditAction.ACCESS_DENIED, TenantAuditAction.BOUNDARY_VIOLATION]:
                return TenantAuditSeverity.CRITICAL
            return TenantAuditSeverity.ERROR
        
        critical_actions = {
            TenantAuditAction.DELETE,
            TenantAuditAction.BULK_DELETE,
            TenantAuditAction.BOUNDARY_VIOLATION,
            TenantAuditAction.USER_REMOVE,
        }
        
        warning_actions = {
            TenantAuditAction.ROLE_CHANGE,
            TenantAuditAction.PERMISSION_CHANGE,
            TenantAuditAction.SETTINGS_CHANGE,
            TenantAuditAction.BULK_UPDATE,
            TenantAuditAction.ACCESS_DENIED,
        }
        
        if action in critical_actions:
            return TenantAuditSeverity.WARNING
        if action in warning_actions:
            return TenantAuditSeverity.WARNING
        
        return TenantAuditSeverity.INFO
    
    def _sanitize_values(self, values: Optional[Dict]) -> Optional[Dict]:
        """Remove sensitive fields from logged values"""
        if not values:
            return None
        
        sensitive_fields = {
            "password", "password_hash", "token", "api_key", "secret",
            "credit_card", "card_number", "cvv", "ssn", "aadhaar",
            "access_token", "refresh_token", "session_token"
        }
        
        sanitized = {}
        for key, value in values.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_values(value)
            else:
                sanitized[key] = value
        
        return sanitized


# Singleton service
_audit_service: Optional[TenantAuditService] = None


def init_tenant_audit_service(db) -> TenantAuditService:
    """Initialize the audit service"""
    global _audit_service
    _audit_service = TenantAuditService(db)
    logger.info("TenantAuditService initialized")
    return _audit_service


def get_tenant_audit_service() -> TenantAuditService:
    """Get the singleton audit service"""
    if _audit_service is None:
        raise RuntimeError("TenantAuditService not initialized")
    return _audit_service


def audit_tenant_action(
    action: TenantAuditAction,
    resource_type: str,
    get_resource_id: Optional[callable] = None
):
    """
    Decorator to automatically audit route actions.
    
    Usage:
        @router.post("/tickets")
        @audit_tenant_action(TenantAuditAction.CREATE, "ticket")
        async def create_ticket(ctx: TenantContext = Depends(tenant_context_required)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get tenant context from kwargs
            ctx = kwargs.get("ctx") or kwargs.get("tenant_context")
            if ctx is None:
                ctx = get_tenant_context()
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                success = True
                error_msg = None
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                # Log the action
                if ctx and _audit_service:
                    try:
                        resource_id = None
                        if get_resource_id and success:
                            resource_id = get_resource_id(result)
                        elif isinstance(result, dict):
                            resource_id = result.get("id") or result.get(f"{resource_type}_id")
                        
                        await _audit_service.log(
                            ctx=ctx,
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            success=success,
                            error_message=error_msg
                        )
                    except Exception as audit_err:
                        logger.warning(f"Failed to create audit log: {audit_err}")
            
            return result
        
        return wrapper
    return decorator
