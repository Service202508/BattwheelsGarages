"""
Journal Entries Routes
======================
API endpoints for double-entry bookkeeping:
- List, create, view journal entries
- Trial Balance
- Account Ledger
- P&L and Balance Sheet from journal entries
"""
# TENANT GUARD: Every MongoDB query in this file MUST include {"organization_id": org_id} — no exceptions.

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import os
import logging
from io import BytesIO
import csv

from services.double_entry_service import (
    DoubleEntryService,
    init_double_entry_service,
    get_double_entry_service,
    EntryType,
    AccountType
)
from core.subscriptions.entitlement import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/journal-entries",
    tags=["Journal Entries"],
    dependencies=[Depends(require_feature("accounting_module"))]
)

# Service instance
_service: Optional[DoubleEntryService] = None


def init_router(database):
    """Initialize the router with database connection"""
    global _service
    _service = init_double_entry_service(database)
    logger.info("Journal Entries router initialized")
    return router


def get_service() -> DoubleEntryService:
    """Get the double entry service"""
    if _service is None:
        raise HTTPException(status_code=500, detail="Journal entries service not initialized")
    return _service


# ==================== REQUEST MODELS ====================

class JournalLineCreate(BaseModel):
    account_id: str = Field(..., min_length=1)
    debit_amount: float = 0
    credit_amount: float = 0
    description: str = ""


class JournalEntryCreate(BaseModel):
    entry_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    description: str = Field(..., min_length=1)
    lines: List[JournalLineCreate] = Field(..., min_items=2)
    entry_type: str = "JOURNAL"
    source_document_id: Optional[str] = None
    source_document_type: Optional[str] = None
    is_posted: bool = True


class JournalEntryReverse(BaseModel):
    reversal_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    reason: str = ""


# ==================== HELPER ====================

async def get_org_id(request: Request) -> str:
    """Get organization ID from request"""
    org_id = request.headers.get("X-Organization-ID")
    if not org_id:
        # Try to get from session/auth
        from server import db
        session_token = request.cookies.get("session_token")
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    # Get first organization
                    membership = await db.organization_users.find_one(
                        {"user_id": user["user_id"], "status": "active"},
                        {"organization_id": 1}
                    )
                    if membership:
                        org_id = membership["organization_id"]
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    return org_id


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request"""
    from server import db
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            return session.get("user_id", "")
    return ""


# ==================== JOURNAL ENTRY ENDPOINTS ====================

@router.get("")
async def list_journal_entries(request: Request, start_date: str = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    entry_type: str = Query(None, description="Filter by entry type"),
    account_id: str = Query(None, description="Filter by account"),
    is_posted: bool = Query(None, description="Filter by posted status"),
    cursor: Optional[str] = Query(None, description="Cursor for keyset pagination"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List journal entries with filters and cursor-based or legacy pagination"""
    import math
    from utils.pagination import paginate_keyset

    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    org_id = await get_org_id(request)
    service = get_service()

    if cursor:
        # Build query for cursor path
        query = {"organization_id": org_id}
        if start_date:
            query["entry_date"] = {"$gte": start_date}
        if end_date:
            query.setdefault("entry_date", {})["$lte"] = end_date
        if entry_type:
            query["entry_type"] = entry_type
        if account_id:
            query["lines.account_id"] = account_id
        if is_posted is not None:
            query["is_posted"] = is_posted

        return await paginate_keyset(
            service.journal_entries, query,
            sort_field="entry_date", sort_order=-1,
            tiebreaker_field="entry_id",
            limit=limit, cursor=cursor,
        )

    # Legacy skip/limit path
    skip = (page - 1) * limit
    result = await service.get_journal_entries(
        organization_id=org_id,
        start_date=start_date,
        end_date=end_date,
        entry_type=entry_type,
        account_id=account_id,
        is_posted=is_posted,
        limit=limit,
        skip=skip
    )

    total = result.get("total", len(result.get("entries", [])))
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "data": result.get("entries", []),
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


@router.post("")
async def create_journal_entry(request: Request, data: JournalEntryCreate
):
    """Create a new manual journal entry"""
    org_id = await get_org_id(request)
    user_id = await get_current_user_id(request)
    service = get_service()

    # Period lock check
    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(service.db, org_id, data.entry_date)
    
    # Convert lines to dict format
    lines = [
        {
            "account_id": line.account_id,
            "debit_amount": line.debit_amount,
            "credit_amount": line.credit_amount,
            "description": line.description
        }
        for line in data.lines
    ]
    
    try:
        entry_type = EntryType(data.entry_type.upper())
    except ValueError:
        entry_type = EntryType.JOURNAL
    
    success, message, entry = await service.create_journal_entry(
        organization_id=org_id,
        entry_date=data.entry_date,
        description=data.description,
        lines=lines,
        entry_type=entry_type,
        source_document_id=data.source_document_id or None,
        source_document_type=data.source_document_type or None,
        created_by=user_id,
        is_posted=data.is_posted
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"code": 0, "message": message, "entry": entry}


@router.get("/{entry_id}")
async def get_journal_entry(request: Request, entry_id: str):
    """Get a specific journal entry"""
    org_id = await get_org_id(request)
    service = get_service()
    
    entry = await service.journal_entries.find_one(
        {"entry_id": entry_id, "organization_id": org_id},
        {"_id": 0}
    )
    
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    return {"code": 0, "entry": entry}


@router.post("/{entry_id}/reverse")
async def reverse_journal_entry(request: Request, entry_id: str,
    data: JournalEntryReverse
):
    """Create a reversal entry for an existing journal entry"""
    org_id = await get_org_id(request)
    user_id = await get_current_user_id(request)
    service = get_service()

    # Period lock check on reversal date
    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(service.db, org_id, data.reversal_date)
    
    success, message, reversal = await service.reverse_journal_entry(
        organization_id=org_id,
        entry_id=entry_id,
        reversal_date=data.reversal_date,
        created_by=user_id,
        reason=data.reason
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"code": 0, "message": message, "reversal_entry": reversal}


@router.get("/export/csv")
async def export_journal_entries_csv(request: Request, start_date: str = Query(None),
    end_date: str = Query(None),
    entry_type: str = Query(None)
):
    """Export journal entries to CSV"""
    org_id = await get_org_id(request)
    service = get_service()
    
    result = await service.get_journal_entries(
        organization_id=org_id,
        start_date=start_date,
        end_date=end_date,
        entry_type=entry_type,
        limit=10000
    )
    
    # Build CSV
    output = BytesIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    
    # Header
    writer.writerow([
        "Entry ID", "Reference Number", "Entry Date", "Entry Type",
        "Description", "Account Code", "Account Name", 
        "Debit", "Credit", "Source Document"
    ])
    
    for entry in result["entries"]:
        for line in entry.get("lines", []):
            writer.writerow([
                entry["entry_id"],
                entry["reference_number"],
                entry["entry_date"],
                entry["entry_type"],
                entry["description"],
                line["account_code"],
                line["account_name"],
                line["debit_amount"],
                line["credit_amount"],
                entry.get("source_document_type", "")
            ])
    
    output.seek(0)
    
    filename = f"journal_entries_{start_date or 'all'}_{end_date or 'all'}.csv"
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== TRIAL BALANCE ====================

@router.get("/reports/trial-balance")
async def get_trial_balance(request: Request, as_of_date: str = Query(None, description="As of date (YYYY-MM-DD)")
):
    """
    Generate Trial Balance from journal entries.
    
    Returns account-wise totals. Total debits must equal total credits.
    If they don't match, returns ERROR status.
    """
    org_id = await get_org_id(request)
    service = get_service()
    
    if not as_of_date:
        as_of_date = datetime.now().strftime("%Y-%m-%d")
    
    result = await service.get_trial_balance(org_id, as_of_date)
    
    return {"code": 0, "report": "trial_balance", **result}


@router.get("/reports/trial-balance/csv")
async def export_trial_balance_csv(request: Request, as_of_date: str = Query(None)
):
    """Export Trial Balance to CSV"""
    org_id = await get_org_id(request)
    service = get_service()
    
    if not as_of_date:
        as_of_date = datetime.now().strftime("%Y-%m-%d")
    
    result = await service.get_trial_balance(org_id, as_of_date)
    
    output = BytesIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    
    writer.writerow([f"Trial Balance as of {as_of_date}"])
    writer.writerow([])
    writer.writerow(["Account Code", "Account Name", "Account Type", "Debit Balance", "Credit Balance"])
    
    for account in result["accounts"]:
        writer.writerow([
            account["account_code"],
            account["account_name"],
            account["account_type"],
            account["debit_balance"],
            account["credit_balance"]
        ])
    
    writer.writerow([])
    writer.writerow(["", "TOTALS", "", result["totals"]["total_debit"], result["totals"]["total_credit"]])
    writer.writerow(["", "Status", result["status"]])
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=trial_balance_{as_of_date}.csv"}
    )


# ==================== ACCOUNT LEDGER ====================

@router.get("/accounts/{account_id}/ledger")
async def get_account_ledger(request: Request, account_id: str, start_date: str = Query(None),
    end_date: str = Query(None)
):
    """
    Get ledger (all transactions) for a specific account with running balance.
    """
    org_id = await get_org_id(request)
    service = get_service()
    
    result = await service.get_account_ledger(
        organization_id=org_id,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {"code": 0, **result}


@router.get("/accounts/{account_id}/balance")
async def get_account_balance(request: Request, account_id: str, as_of_date: str = Query(None),
    start_date: str = Query(None)
):
    """Get balance for a specific account"""
    org_id = await get_org_id(request)
    service = get_service()
    
    result = await service.get_account_balance(
        organization_id=org_id,
        account_id=account_id,
        as_of_date=as_of_date,
        start_date=start_date
    )
    
    return {"code": 0, **result}


# ==================== P&L AND BALANCE SHEET ====================

@router.get("/reports/profit-loss")
async def get_profit_loss_from_journal(request: Request, start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Generate Profit & Loss from journal entries.
    
    Income accounts minus Expense accounts for the period.
    """
    org_id = await get_org_id(request)
    service = get_service()
    
    if not start_date:
        # Default to current financial year
        today = datetime.now()
        if today.month >= 4:
            start_date = f"{today.year}-04-01"
        else:
            start_date = f"{today.year - 1}-04-01"
    
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    result = await service.get_profit_and_loss(org_id, start_date, end_date)
    
    return {"code": 0, "report": "profit_and_loss", **result}


@router.get("/reports/balance-sheet")
async def get_balance_sheet_from_journal(request: Request, as_of_date: str = Query(None, description="As of date (YYYY-MM-DD)")
):
    """
    Generate Balance Sheet from journal entries.
    
    Assets = Liabilities + Equity
    """
    org_id = await get_org_id(request)
    service = get_service()
    
    if not as_of_date:
        as_of_date = datetime.now().strftime("%Y-%m-%d")
    
    result = await service.get_balance_sheet(org_id, as_of_date)
    
    return {"code": 0, "report": "balance_sheet", **result}


# ==================== SYSTEM ACCOUNTS ====================

@router.post("/accounts/initialize-system")
async def initialize_system_accounts(request: Request):
    """Initialize all system accounts for the organization"""
    org_id = await get_org_id(request)
    service = get_service()
    
    await service.ensure_system_accounts(org_id)
    
    return {"code": 0, "message": "System accounts initialized"}


@router.get("/accounts/chart")
async def get_chart_of_accounts(request: Request, account_type: str = Query(None, description="Filter by account type")
):
    """Get chart of accounts"""
    org_id = await get_org_id(request)
    service = get_service()
    
    query = {"organization_id": org_id, "is_active": True}
    if account_type:
        query["account_type"] = account_type
    
    accounts = await service.chart_of_accounts.find(
        query,
        {"_id": 0}
    ).sort("account_code", 1).to_list(1000)
    
    # Group by type
    grouped = {}
    for acc in accounts:
        acc_type = acc["account_type"]
        if acc_type not in grouped:
            grouped[acc_type] = []
        grouped[acc_type].append(acc)
    
    return {
        "code": 0,
        "accounts": accounts,
        "grouped": grouped,
        "total": len(accounts)
    }


# ==================== ENTRY TYPE OPTIONS ====================

@router.get("/options/entry-types")
async def get_entry_types():
    """Get available entry types"""
    return {
        "code": 0,
        "entry_types": [
            {"value": e.value, "label": e.value.replace("_", " ").title()}
            for e in EntryType
        ]
    }


@router.get("/options/account-types")
async def get_account_types():
    """Get available account types"""
    return {
        "code": 0,
        "account_types": [
            {"value": a.value, "label": a.value}
            for a in AccountType
        ]
    }
