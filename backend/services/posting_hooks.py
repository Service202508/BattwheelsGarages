"""
Double-Entry Posting Hooks
==========================
Utility functions to auto-post journal entries when transactions occur.
Call these from invoice, payment, bill, expense, and payroll modules.
"""

import logging
import os
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

import motor.motor_asyncio

logger = logging.getLogger(__name__)

# Import will be lazy to avoid circular imports
_service = None


def _get_service():
    """Lazy import of double entry service"""
    global _service
    if _service is None:
        try:
            from services.double_entry_service import get_double_entry_service
            _service = get_double_entry_service()
        except Exception as e:
            logger.warning(f"Double entry service not available: {e}")
            return None
    return _service


# ==================== PERIOD LOCK CHECK (P1-05) ====================

async def _check_period_lock(organization_id: str, transaction_date: str) -> None:
    """
    Check if the period containing transaction_date is locked.
    Raises ValueError if the period is locked.
    
    transaction_date: ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    """
    if not organization_id or not transaction_date:
        return  # Cannot check without org or date
    
    try:
        dt = datetime.fromisoformat(transaction_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            dt = datetime.strptime(transaction_date[:10], "%Y-%m-%d")
        except Exception:
            return  # Unparseable date — let the posting proceed
    
    MONGO_URL = os.environ.get("MONGO_URL")
    DB_NAME = os.environ.get("DB_NAME")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    lock = await db.period_locks.find_one({
        "org_id": organization_id,
        "period_month": dt.month,
        "period_year": dt.year,
        "unlocked_at": None
    })
    
    if lock:
        raise ValueError(
            f"Cannot post journal entry: period {dt.month}/{dt.year} "
            f"is locked for organization {organization_id}"
        )


async def post_invoice_journal_entry(
    organization_id: str,
    invoice: Dict,
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Post journal entry when invoice is finalized (sent/approved).
    
    DEBIT:  Accounts Receivable
    CREDIT: Sales Revenue
    CREDIT: GST Payable (CGST/SGST/IGST)
    """
    service = _get_service()
    if not service:
        logger.warning("Cannot post invoice - double entry service not initialized")
        return False, "Double entry service not available", None
    
    try:
        # Period lock check — must be first operation (P1-05)
        invoice_date = invoice.get("invoice_date", invoice.get("date", ""))
        await _check_period_lock(organization_id, invoice_date)
        
        success, msg, entry = await service.post_sales_invoice(
            organization_id=organization_id,
            invoice=invoice,
            created_by=created_by
        )
        
        if success:
            logger.info(f"Posted journal entry for invoice {invoice.get('invoice_number', invoice.get('invoice_id', ''))}")
        else:
            logger.error(f"Failed to post journal entry for invoice: {msg}")
        
        return success, msg, entry
    except Exception as e:
        logger.error(f"Exception posting invoice journal entry: {e}")
        return False, str(e), None


async def post_payment_received_journal_entry(
    organization_id: str,
    payment: Dict,
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Post journal entry when payment is received.
    
    DEBIT:  Bank / Cash
    CREDIT: Accounts Receivable
    """
    service = _get_service()
    if not service:
        logger.warning("Cannot post payment - double entry service not initialized")
        return False, "Double entry service not available", None
    
    try:
        # Period lock check — must be first operation (P1-05)
        payment_date = payment.get("payment_date", payment.get("date", ""))
        await _check_period_lock(organization_id, payment_date)
        
        success, msg, entry = await service.post_payment_received(
            organization_id=organization_id,
            payment=payment,
            created_by=created_by
        )
        
        if success:
            logger.info(f"Posted journal entry for payment {payment.get('payment_number', payment.get('payment_id', ''))}")
        else:
            logger.error(f"Failed to post journal entry for payment: {msg}")
        
        return success, msg, entry
    except Exception as e:
        logger.error(f"Exception posting payment journal entry: {e}")
        return False, str(e), None


async def post_bill_journal_entry(
    organization_id: str,
    bill: Dict,
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Post journal entry when bill is recorded.
    
    DEBIT:  Expense / COGS account
    DEBIT:  GST Input Credit
    CREDIT: Accounts Payable
    """
    service = _get_service()
    if not service:
        logger.warning("Cannot post bill - double entry service not initialized")
        return False, "Double entry service not available", None
    
    try:
        # Period lock check — must be first operation (P1-05)
        bill_date = bill.get("bill_date", bill.get("date", ""))
        await _check_period_lock(organization_id, bill_date)
        
        success, msg, entry = await service.post_purchase_bill(
            organization_id=organization_id,
            bill=bill,
            created_by=created_by
        )
        
        if success:
            logger.info(f"Posted journal entry for bill {bill.get('bill_number', bill.get('bill_id', ''))}")
        else:
            logger.error(f"Failed to post journal entry for bill: {msg}")
        
        return success, msg, entry
    except Exception as e:
        logger.error(f"Exception posting bill journal entry: {e}")
        return False, str(e), None


async def post_bill_payment_journal_entry(
    organization_id: str,
    payment: Dict,
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Post journal entry when bill payment is made.
    
    DEBIT:  Accounts Payable
    CREDIT: Bank / Cash
    """
    service = _get_service()
    if not service:
        logger.warning("Cannot post bill payment - double entry service not initialized")
        return False, "Double entry service not available", None
    
    try:
        # Period lock check — must be first operation (P1-05)
        payment_date = payment.get("payment_date", payment.get("date", ""))
        await _check_period_lock(organization_id, payment_date)
        
        success, msg, entry = await service.post_bill_payment(
            organization_id=organization_id,
            payment=payment,
            created_by=created_by
        )
        
        if success:
            logger.info(f"Posted journal entry for bill payment {payment.get('payment_id', '')}")
        else:
            logger.error(f"Failed to post journal entry for bill payment: {msg}")
        
        return success, msg, entry
    except Exception as e:
        logger.error(f"Exception posting bill payment journal entry: {e}")
        return False, str(e), None


async def post_expense_journal_entry(
    organization_id: str,
    expense: Dict,
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Post journal entry when expense is recorded.
    
    DEBIT:  Expense account
    CREDIT: Bank / Cash / Accounts Payable
    """
    service = _get_service()
    if not service:
        logger.warning("Cannot post expense - double entry service not initialized")
        return False, "Double entry service not available", None
    
    try:
        # Period lock check — must be first operation (P1-05)
        expense_date = expense.get("expense_date", expense.get("date", ""))
        await _check_period_lock(organization_id, expense_date)
        
        success, msg, entry = await service.post_expense(
            organization_id=organization_id,
            expense=expense,
            created_by=created_by
        )
        
        if success:
            logger.info(f"Posted journal entry for expense {expense.get('expense_id', '')}")
        else:
            logger.error(f"Failed to post journal entry for expense: {msg}")
        
        return success, msg, entry
    except Exception as e:
        logger.error(f"Exception posting expense journal entry: {e}")
        return False, str(e), None


async def post_payroll_journal_entry(
    organization_id: str,
    payroll: Dict,
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Post journal entry when individual payroll is processed.
    For batch processing, use post_payroll_run_journal_entry() instead.
    """
    return await post_payroll_run_journal_entry(organization_id, [payroll], created_by)


async def post_payroll_run_journal_entry(
    organization_id: str,
    payroll_records: list,
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Post journal entry when payroll run is processed (batch of all employees).
    
    DEBIT:  Salary Expense (total gross salaries)
    DEBIT:  Employer PF Contribution
    DEBIT:  Employer ESI Contribution
    CREDIT: Salary Payable (total net take-home)
    CREDIT: TDS Payable
    CREDIT: Employee PF Payable
    CREDIT: Employer PF Payable
    CREDIT: ESI Payable (employee + employer)
    CREDIT: Professional Tax Payable
    """
    service = _get_service()
    if not service:
        logger.warning("Cannot post payroll - double entry service not initialized")
        return False, "Double entry service not available", None
    
    try:
        # Period lock check — must be first operation (P1-05)
        # Use the first payroll record's pay_date or generated_at as the transaction date
        if payroll_records:
            payroll_date = payroll_records[0].get("pay_date", payroll_records[0].get("generated_at", ""))
            await _check_period_lock(organization_id, payroll_date)
        
        success, msg, entry = await service.post_payroll_run(
            organization_id=organization_id,
            payroll_records=payroll_records,
            created_by=created_by
        )
        
        employee_count = len(payroll_records)
        if success:
            logger.info(f"Posted journal entry for payroll run - {employee_count} employees")
        else:
            logger.error(f"Failed to post journal entry for payroll: {msg}")
        
        return success, msg, entry
    except Exception as e:
        logger.error(f"Exception posting payroll journal entry: {e}")
        return False, str(e), None


async def reverse_transaction_journal_entry(
    organization_id: str,
    original_entry_id: str,
    reversal_date: str,
    reason: str = "",
    created_by: str = ""
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create a reversal entry for any transaction.
    Used when voiding invoices, refunding payments, etc.
    """
    service = _get_service()
    if not service:
        logger.warning("Cannot reverse entry - double entry service not initialized")
        return False, "Double entry service not available", None
    
    try:
        # Period lock check — must be first operation (P1-05)
        await _check_period_lock(organization_id, reversal_date)
        
        success, msg, entry = await service.reverse_journal_entry(
            organization_id=organization_id,
            entry_id=original_entry_id,
            reversal_date=reversal_date,
            created_by=created_by,
            reason=reason
        )
        
        if success:
            logger.info(f"Created reversal for entry {original_entry_id}")
        else:
            logger.error(f"Failed to create reversal: {msg}")
        
        return success, msg, entry
    except Exception as e:
        logger.error(f"Exception creating reversal: {e}")
        return False, str(e), None


# ==================== BATCH POSTING ====================

async def post_all_unposted_invoices(organization_id: str) -> Dict:
    """Post journal entries for all invoices that don't have entries yet"""
    service = _get_service()
    if not service:
        return {"success": False, "message": "Service not available"}
    
    # Get invoices without journal entries
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "battwheels")]
    
    # Get posted invoice IDs
    posted_ids = await service.journal_entries.distinct("source_document_id", {
        "organization_id": organization_id,
        "source_document_type": "invoice"
    })
    
    # Get invoices not yet posted
    invoices = await db.invoices_enhanced.find({
        "organization_id": organization_id,
        "status": {"$nin": ["draft", "void"]},
        "invoice_id": {"$nin": posted_ids}
    }, {"_id": 0}).to_list(1000)
    
    results = {"posted": 0, "failed": 0, "errors": []}
    
    for invoice in invoices:
        success, msg, _ = await post_invoice_journal_entry(
            organization_id=organization_id,
            invoice=invoice
        )
        if success:
            results["posted"] += 1
        else:
            results["failed"] += 1
            results["errors"].append(f"Invoice {invoice.get('invoice_number', '')}: {msg}")
    
    return results
