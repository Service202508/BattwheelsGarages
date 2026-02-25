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
    TICKET_ASSIGNED = "ticket.assigned"
    INVOICE_CREATED = "invoice.created"
    INVOICE_UPDATED = "invoice.updated"
    INVOICE_PAID = "invoice.paid"
    INVOICE_VOIDED = "invoice.voided"
    JOURNAL_ENTRY_CREATED = "journal_entry.created"
    JOURNAL_ENTRY_REVERSED = "journal_entry.reversed"
    PAYMENT_RECORDED = "payment.recorded"
    PAYMENT_DELETED = "payment.deleted"
    EMPLOYEE_CREATED = "employee.created"
    EMPLOYEE_UPDATED = "employee.updated"
    PAYROLL_RUN = "payroll.run"
    ESTIMATE_CREATED = "estimate.created"
    ESTIMATE_UPDATED = "estimate.updated"
    ESTIMATE_STATUS_CHANGED = "estimate.status_changed"
    ESTIMATE_CONVERTED_TO_TICKET = "estimate.converted_to_ticket"
    ESTIMATE_CONVERTED_TO_INVOICE = "estimate.converted_to_invoice"
    BILL_CREATED = "bill.created"
    BILL_UPDATED = "bill.updated"
    BILL_APPROVED = "bill.approved"
    EXPENSE_CREATED = "expense.created"
    EXPENSE_APPROVED = "expense.approved"
    BANK_TRANSACTION_CREATED = "bank_transaction.created"
    BANK_RECONCILED = "bank_transaction.reconciled"
    CREDIT_NOTE_CREATED = "credit_note.created"
    CONTACT_CREATED = "contact.created"
    CONTACT_UPDATED = "contact.updated"
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
