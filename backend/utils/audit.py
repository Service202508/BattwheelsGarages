"""
Structured audit logging for all significant operations.
Logs are immutable - no update or delete operations on audit_logs collection.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuditAction:
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_CLOSED = "ticket.closed"
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    INVOICE_VOIDED = "invoice.voided"
    JOURNAL_ENTRY_CREATED = "journal_entry.created"
    PAYMENT_RECORDED = "payment.recorded"
    EMPLOYEE_CREATED = "employee.created"
    EMPLOYEE_UPDATED = "employee.updated"
    PAYROLL_RUN = "payroll.run"
    USER_LOGIN = "auth.login"
    USER_REMOVED = "user.removed"
    PASSWORD_CHANGED = "auth.password_changed"
    PASSWORD_RESET = "auth.password_reset"
    ORG_SETTINGS_UPDATED = "org.settings_updated"


async def log_audit(
    db,
    action: str,
    org_id: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
):
    """Write an immutable audit log entry."""
    try:
        await db.audit_logs.insert_one({
            "action": action,
            "organization_id": org_id,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.error(f"Audit log write failed: {e}")
