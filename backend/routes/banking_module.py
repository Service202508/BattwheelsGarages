"""
Banking & Accountant Module - Zoho Books Style
Comprehensive banking, chart of accounts, and financial reporting

Features:
- Bank Accounts Management
- Bank Transactions & Reconciliation
- Chart of Accounts with hierarchy
- Journal Entries
- P&L and Balance Sheet Reports
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import motor.motor_asyncio
import os
import uuid
import logging

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/banking", tags=["Banking & Accountant"])

# Collections
bank_accounts_col = db["bank_accounts"]
bank_transactions_col = db["bank_transactions"]
chart_of_accounts_col = db["chart_of_accounts"]
journal_entries_col = db["journal_entries"]
reconciliation_col = db["bank_reconciliations"]
counters_col = db["counters"]


def _get_org_id(request: Request) -> str:
    """Extract org_id from tenant middleware context. Raises 400 if missing."""
    org_id = getattr(request.state, "tenant_org_id", None)
    if not org_id:
        from fastapi import HTTPException as _H
        raise _H(status_code=400, detail="Organization context required")
    return org_id


# ==================== MODELS ====================

class BankAccountCreate(BaseModel):
    account_name: str = Field(..., min_length=1)
    account_type: str = "bank"  # bank, credit_card, cash
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    currency: str = "INR"
    opening_balance: float = 0
    opening_balance_date: Optional[str] = None
    description: Optional[str] = None
    is_primary: bool = False
    organization_id: Optional[str] = None


class BankTransactionCreate(BaseModel):
    bank_account_id: str
    transaction_type: str  # deposit, withdrawal, transfer_in, transfer_out
    amount: float = Field(..., gt=0)
    transaction_date: str
    reference_number: Optional[str] = None
    description: Optional[str] = None
    payee: Optional[str] = None
    category_id: Optional[str] = None  # Chart of accounts reference
    is_reconciled: bool = False
    organization_id: Optional[str] = None


class ReconciliationCreate(BaseModel):
    bank_account_id: str
    statement_date: str
    statement_balance: float
    organization_id: Optional[str] = None


class ChartOfAccountCreate(BaseModel):
    account_name: str = Field(..., min_length=1)
    account_type: str  # asset, liability, equity, income, expense
    account_sub_type: Optional[str] = None
    account_code: Optional[str] = None
    parent_account_id: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    organization_id: Optional[str] = None


class JournalEntryCreate(BaseModel):
    entry_date: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    lines: List[Dict[str, Any]]  # [{account_id, debit, credit, description}]
    organization_id: Optional[str] = None


# ==================== HELPERS ====================

async def get_next_number(prefix: str, org_id: str = None) -> str:
    """Generate next sequential number"""
    counter_id = f"{prefix}_{org_id}" if org_id else prefix
    counter = await counters_col.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return f"{prefix.upper()}-{str(counter['seq']).zfill(5)}"


async def update_account_balance(bank_account_id: str, amount: float, is_credit: bool = True):
    """Update bank account balance"""
    change = amount if is_credit else -amount
    await bank_accounts_col.update_one(
        {"bank_account_id": bank_account_id},
        {
            "$inc": {"current_balance": change},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )


# ==================== BANK ACCOUNTS ====================

@router.post("/accounts")
async def create_bank_account(request: Request, account: BankAccountCreate):
    """Create a new bank account"""
    org_id = getattr(request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
    account_id = f"ba_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    account_doc = {
        "bank_account_id": account_id,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "account_number": account.account_number,
        "bank_name": account.bank_name,
        "ifsc_code": account.ifsc_code,
        "currency": account.currency,
        "opening_balance": account.opening_balance,
        "current_balance": account.opening_balance,
        "opening_balance_date": account.opening_balance_date or now.strftime("%Y-%m-%d"),
        "description": account.description,
        "is_primary": account.is_primary,
        "is_active": True,
        "organization_id": org_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    # If marked as primary, unmark others
    if account.is_primary:
        await bank_accounts_col.update_many(
            {"organization_id": org_id, "is_primary": True},
            {"$set": {"is_primary": False}}
        )
    
    await bank_accounts_col.insert_one(account_doc)
    account_doc.pop("_id", None)
    
    return {"code": 0, "bank_account": account_doc}


@router.get("/accounts")
async def list_bank_accounts(
    request: Request,
    account_type: Optional[str] = None,
    is_active: bool = True,
):
    """List all bank accounts (org-scoped via auth context)"""
    org_id = getattr(request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
    query = {"is_active": is_active, "organization_id": org_id}
    if account_type:
        query["account_type"] = account_type
    
    accounts = await bank_accounts_col.find(query, {"_id": 0}).sort("account_name", 1).to_list(100)
    
    # Calculate total balance
    total_balance = sum(a.get("current_balance", 0) for a in accounts)
    
    return {
        "code": 0,
        "bank_accounts": accounts,
        "total_balance": total_balance,
        "count": len(accounts)
    }


@router.get("/accounts/{account_id}")
async def get_bank_account(request: Request, account_id: str):
    """Get bank account details with recent transactions"""
    org_id = _get_org_id(request)
    account = await bank_accounts_col.find_one(
        {"bank_account_id": account_id, "organization_id": org_id},
        {"_id": 0}
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    # Get recent transactions
    transactions = await bank_transactions_col.find(
        {"bank_account_id": account_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("transaction_date", -1).limit(20).to_list(20)
    
    account["recent_transactions"] = transactions
    return {"code": 0, "bank_account": account}


@router.put("/accounts/{account_id}")
async def update_bank_account(request: Request, account_id: str, updates: Dict[str, Any]):
    """Update bank account"""
    org_id = _get_org_id(request)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    updates.pop("bank_account_id", None)
    updates.pop("_id", None)
    updates.pop("organization_id", None)
    
    result = await bank_accounts_col.update_one(
        {"bank_account_id": account_id, "organization_id": org_id},
        {"$set": updates}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    updated = await bank_accounts_col.find_one({"bank_account_id": account_id, "organization_id": org_id}, {"_id": 0})
    return {"code": 0, "bank_account": updated}


# ==================== BANK TRANSACTIONS ====================

@router.post("/transactions")
async def create_bank_transaction(request: Request, txn: BankTransactionCreate):
    """Record a bank transaction"""
    org_id = _get_org_id(request)
    txn_id = f"bt_{uuid.uuid4().hex[:12]}"
    txn_number = await get_next_number("TXN", org_id)
    now = datetime.now(timezone.utc)
    
    # Verify bank account exists and belongs to this org
    account = await bank_accounts_col.find_one({"bank_account_id": txn.bank_account_id, "organization_id": org_id})
    if not account:
        raise HTTPException(status_code=400, detail="Bank account not found")
    
    txn_doc = {
        "transaction_id": txn_id,
        "transaction_number": txn_number,
        "bank_account_id": txn.bank_account_id,
        "bank_account_name": account.get("account_name"),
        "transaction_type": txn.transaction_type,
        "amount": txn.amount,
        "transaction_date": txn.transaction_date,
        "reference_number": txn.reference_number,
        "description": txn.description,
        "payee": txn.payee,
        "category_id": txn.category_id,
        "is_reconciled": txn.is_reconciled,
        "organization_id": org_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    await bank_transactions_col.insert_one(txn_doc)
    
    # Update account balance
    is_credit = txn.transaction_type in ["deposit", "transfer_in"]
    await update_account_balance(txn.bank_account_id, txn.amount, is_credit)
    
    txn_doc.pop("_id", None)
    return {"code": 0, "transaction": txn_doc}


@router.get("/transactions")
async def list_bank_transactions(
    request: Request,
    bank_account_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    is_reconciled: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List bank transactions with standardized pagination"""
    import math
    org_id = _get_org_id(request)
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {"organization_id": org_id}
    if bank_account_id:
        query["bank_account_id"] = bank_account_id
    if transaction_type:
        query["transaction_type"] = transaction_type
    if is_reconciled is not None:
        query["is_reconciled"] = is_reconciled
    if start_date:
        query["transaction_date"] = {"$gte": start_date}
    if end_date:
        if "transaction_date" in query:
            query["transaction_date"]["$lte"] = end_date
        else:
            query["transaction_date"] = {"$lte": end_date}

    total = await bank_transactions_col.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    transactions = await bank_transactions_col.find(
        query, {"_id": 0}
    ).sort("transaction_date", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": transactions,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


@router.post("/transactions/{txn_id}/reconcile")
async def reconcile_transaction(txn_id: str):
    """Mark a transaction as reconciled"""
    result = await bank_transactions_col.update_one(
        {"transaction_id": txn_id},
        {
            "$set": {
                "is_reconciled": True,
                "reconciled_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"code": 0, "message": "Transaction reconciled"}


# ==================== BANK RECONCILIATION ====================

@router.post("/reconciliation/start")
async def start_reconciliation(data: ReconciliationCreate):
    """Start a bank reconciliation session"""
    recon_id = f"rec_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Get current bank balance
    account = await bank_accounts_col.find_one({"bank_account_id": data.bank_account_id})
    if not account:
        raise HTTPException(status_code=400, detail="Bank account not found")
    
    book_balance = account.get("current_balance", 0)
    
    # Get unreconciled transactions
    unreconciled = await bank_transactions_col.find(
        {"bank_account_id": data.bank_account_id, "is_reconciled": False},
        {"_id": 0}
    ).to_list(500)
    
    recon_doc = {
        "reconciliation_id": recon_id,
        "bank_account_id": data.bank_account_id,
        "bank_account_name": account.get("account_name"),
        "statement_date": data.statement_date,
        "statement_balance": data.statement_balance,
        "book_balance": book_balance,
        "difference": data.statement_balance - book_balance,
        "unreconciled_count": len(unreconciled),
        "status": "in_progress",
        "organization_id": data.organization_id,
        "started_at": now.isoformat(),
        "created_at": now.isoformat(),
    }
    
    await reconciliation_col.insert_one(recon_doc)
    recon_doc.pop("_id", None)
    recon_doc["unreconciled_transactions"] = unreconciled
    
    return {"code": 0, "reconciliation": recon_doc}


@router.post("/reconciliation/{recon_id}/complete")
async def complete_reconciliation(recon_id: str, transaction_ids: List[str] = []):
    """Complete reconciliation by marking transactions"""
    recon = await reconciliation_col.find_one({"reconciliation_id": recon_id})
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    now = datetime.now(timezone.utc)
    
    # Mark selected transactions as reconciled
    if transaction_ids:
        await bank_transactions_col.update_many(
            {"transaction_id": {"$in": transaction_ids}},
            {
                "$set": {
                    "is_reconciled": True,
                    "reconciled_at": now.isoformat(),
                    "reconciliation_id": recon_id
                }
            }
        )
    
    # Get updated balance
    account = await bank_accounts_col.find_one({"bank_account_id": recon["bank_account_id"]})
    
    # Update reconciliation status
    await reconciliation_col.update_one(
        {"reconciliation_id": recon_id},
        {
            "$set": {
                "status": "completed",
                "completed_at": now.isoformat(),
                "reconciled_count": len(transaction_ids),
                "closing_balance": account.get("current_balance", 0)
            }
        }
    )
    
    updated = await reconciliation_col.find_one({"reconciliation_id": recon_id}, {"_id": 0})
    return {"code": 0, "reconciliation": updated, "message": "Reconciliation completed"}


@router.get("/reconciliation/history")
async def get_reconciliation_history(
    bank_account_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
):
    """Get reconciliation history"""
    query = {}
    if bank_account_id:
        query["bank_account_id"] = bank_account_id
    
    total = await reconciliation_col.count_documents(query)
    skip = (page - 1) * per_page
    
    reconciliations = await reconciliation_col.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "reconciliations": reconciliations,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }


# ==================== CHART OF ACCOUNTS ====================

@router.get("/chart-of-accounts")
async def list_chart_of_accounts(
    request: Request,
    account_type: Optional[str] = None,
    is_active: bool = True,
):
    """List chart of accounts with hierarchy"""
    org_id = _get_org_id(request)
    query = {"is_active": is_active, "organization_id": org_id}
    
    accounts = await chart_of_accounts_col.find(query, {"_id": 0}).sort("account_code", 1).to_list(500)
    
    # Group by type
    grouped = {
        "asset": [],
        "liability": [],
        "equity": [],
        "income": [],
        "expense": []
    }
    
    for acc in accounts:
        acc_type = acc.get("account_type", "expense")
        if acc_type in grouped:
            grouped[acc_type].append(acc)
    
    return {
        "code": 0,
        "chart_of_accounts": accounts,
        "by_type": grouped,
        "count": len(accounts)
    }


@router.post("/chart-of-accounts")
async def create_chart_account(account: ChartOfAccountCreate):
    """Create a new chart of account"""
    account_id = f"coa_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Generate account code if not provided
    code = account.account_code
    if not code:
        type_prefixes = {
            "asset": "1", "liability": "2", "equity": "3",
            "income": "4", "expense": "5"
        }
        prefix = type_prefixes.get(account.account_type, "9")
        count = await chart_of_accounts_col.count_documents({
            "account_type": account.account_type,
            "organization_id": account.organization_id
        })
        code = f"{prefix}{str(count + 1).zfill(4)}"
    
    account_doc = {
        "account_id": account_id,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "account_sub_type": account.account_sub_type,
        "account_code": code,
        "parent_account_id": account.parent_account_id,
        "description": account.description,
        "is_active": account.is_active,
        "balance": 0,
        "organization_id": account.organization_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    await chart_of_accounts_col.insert_one(account_doc)
    account_doc.pop("_id", None)
    
    return {"code": 0, "account": account_doc}


# ==================== JOURNAL ENTRIES ====================

@router.post("/journal-entries")
async def create_journal_entry(entry: JournalEntryCreate):
    """Create a journal entry (must be balanced)"""
    # Period lock check
    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(journal_entries_col.database, entry.organization_id, entry.entry_date)

    entry_id = f"je_{uuid.uuid4().hex[:12]}"
    entry_number = await get_next_number("JE", entry.organization_id)
    now = datetime.now(timezone.utc)
    
    # Validate balance (debits must equal credits)
    total_debit = sum(line.get("debit", 0) for line in entry.lines)
    total_credit = sum(line.get("credit", 0) for line in entry.lines)
    
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(
            status_code=400, 
            detail=f"Journal entry not balanced. Debit: {total_debit}, Credit: {total_credit}"
        )
    
    entry_doc = {
        "entry_id": entry_id,
        "entry_number": entry_number,
        "entry_date": entry.entry_date,
        "reference": entry.reference,
        "notes": entry.notes,
        "lines": entry.lines,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "status": "posted",
        "organization_id": entry.organization_id,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    await journal_entries_col.insert_one(entry_doc)
    
    # Update account balances
    for line in entry.lines:
        account_id = line.get("account_id")
        debit = line.get("debit", 0)
        credit = line.get("credit", 0)
        net_change = debit - credit  # Positive for debits, negative for credits
        
        await chart_of_accounts_col.update_one(
            {"account_id": account_id},
            {"$inc": {"balance": net_change}}
        )
    
    entry_doc.pop("_id", None)
    return {"code": 0, "journal_entry": entry_doc}


@router.get("/journal-entries")
async def list_journal_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
):
    """List journal entries"""
    query = {}
    if start_date:
        query["entry_date"] = {"$gte": start_date}
    if end_date:
        if "entry_date" in query:
            query["entry_date"]["$lte"] = end_date
        else:
            query["entry_date"] = {"$lte": end_date}
    
    total = await journal_entries_col.count_documents(query)
    skip = (page - 1) * per_page
    
    entries = await journal_entries_col.find(
        query, {"_id": 0}
    ).sort("entry_date", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "journal_entries": entries,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }


# ==================== FINANCIAL REPORTS ====================

@router.get("/reports/profit-loss")
async def get_profit_loss_report(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Generate Profit & Loss report"""
    org_id = _get_org_id(request)
    now = datetime.now(timezone.utc)
    if not start_date:
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")
    
    # Get income and expense accounts with balances
    query = {"is_active": True, "organization_id": org_id}
    
    # Get income accounts
    income_query = {**query, "account_type": "income"}
    income_accounts = await chart_of_accounts_col.find(income_query, {"_id": 0}).to_list(100)
    
    # Get expense accounts
    expense_query = {**query, "account_type": "expense"}
    expense_accounts = await chart_of_accounts_col.find(expense_query, {"_id": 0}).to_list(100)
    
    # Calculate totals from invoices and bills
    total_income = sum(acc.get("balance", 0) for acc in income_accounts)
    total_expenses = sum(acc.get("balance", 0) for acc in expense_accounts)
    
    # Also calculate from actual transactions
    invoices_pipeline = [
        {"$match": {"invoice_date": {"$gte": start_date, "$lte": end_date}, "status": {"$nin": ["void", "draft"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]
    
    bills_pipeline = [
        {"$match": {"bill_date": {"$gte": start_date, "$lte": end_date}, "status": {"$nin": ["void", "draft"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]
    
    invoice_result = await db.invoices.aggregate(invoices_pipeline).to_list(1)
    bill_result = await db.bills.aggregate(bills_pipeline).to_list(1)
    
    invoice_revenue = invoice_result[0]["total"] if invoice_result else 0
    bill_expenses = bill_result[0]["total"] if bill_result else 0
    
    # Use actual transaction data if available, otherwise use account balances
    revenue = invoice_revenue if invoice_revenue else total_income
    expenses = bill_expenses if bill_expenses else abs(total_expenses)
    net_profit = revenue - expenses
    
    return {
        "code": 0,
        "report": "profit_and_loss",
        "period": {"start_date": start_date, "end_date": end_date},
        "income": {
            "accounts": income_accounts,
            "total": revenue
        },
        "expenses": {
            "accounts": expense_accounts,
            "total": expenses
        },
        "gross_profit": revenue,
        "net_profit": net_profit,
        "profit_margin": round((net_profit / revenue * 100) if revenue else 0, 2)
    }


@router.get("/reports/balance-sheet")
async def get_balance_sheet_report(
    request: Request,
    as_of_date: Optional[str] = None,
):
    """Generate Balance Sheet report"""
    org_id = _get_org_id(request)
    now = datetime.now(timezone.utc)
    if not as_of_date:
        as_of_date = now.strftime("%Y-%m-%d")
    
    query = {"is_active": True, "organization_id": org_id}
    
    # Get accounts by type
    assets = await chart_of_accounts_col.find({**query, "account_type": "asset"}, {"_id": 0}).to_list(100)
    liabilities = await chart_of_accounts_col.find({**query, "account_type": "liability"}, {"_id": 0}).to_list(100)
    equity = await chart_of_accounts_col.find({**query, "account_type": "equity"}, {"_id": 0}).to_list(100)
    
    # Calculate totals
    total_assets = sum(acc.get("balance", 0) for acc in assets)
    total_liabilities = sum(acc.get("balance", 0) for acc in liabilities)
    total_equity = sum(acc.get("balance", 0) for acc in equity)
    
    # Add bank account balances to assets
    bank_accounts = await bank_accounts_col.find({"is_active": True}, {"_id": 0}).to_list(50)
    bank_total = sum(ba.get("current_balance", 0) for ba in bank_accounts)
    total_assets += bank_total
    
    # Add receivables
    receivables_result = await db.invoices.aggregate([
        {"$match": {"status": {"$in": ["sent", "overdue", "partially_paid"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance_due"}}}
    ]).to_list(1)
    receivables = receivables_result[0]["total"] if receivables_result else 0
    total_assets += receivables
    
    # Add payables to liabilities
    payables_result = await db.bills.aggregate([
        {"$match": {"status": {"$in": ["open", "overdue", "partially_paid"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance_due"}}}
    ]).to_list(1)
    payables = payables_result[0]["total"] if payables_result else 0
    total_liabilities += payables
    
    # Calculate retained earnings
    retained_earnings = total_assets - total_liabilities - total_equity
    
    return {
        "code": 0,
        "report": "balance_sheet",
        "as_of_date": as_of_date,
        "assets": {
            "accounts": assets,
            "bank_accounts": bank_accounts,
            "bank_total": bank_total,
            "receivables": receivables,
            "total": total_assets
        },
        "liabilities": {
            "accounts": liabilities,
            "payables": payables,
            "total": total_liabilities
        },
        "equity": {
            "accounts": equity,
            "retained_earnings": retained_earnings,
            "total": total_equity + retained_earnings
        },
        "total_liabilities_and_equity": total_liabilities + total_equity + retained_earnings,
        "is_balanced": abs(total_assets - (total_liabilities + total_equity + retained_earnings)) < 0.01
    }


@router.get("/reports/cash-flow")
async def get_cash_flow_report(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Generate Cash Flow report"""
    org_id = _get_org_id(request)
    now = datetime.now(timezone.utc)
    if not start_date:
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")
    
    # Get bank transactions by type — org-scoped
    deposits = await bank_transactions_col.aggregate([
        {"$match": {"organization_id": org_id, "transaction_type": {"$in": ["deposit", "transfer_in"]}, "transaction_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    withdrawals = await bank_transactions_col.aggregate([
        {"$match": {"organization_id": org_id, "transaction_type": {"$in": ["withdrawal", "transfer_out"]}, "transaction_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    total_inflow = deposits[0]["total"] if deposits else 0
    total_outflow = withdrawals[0]["total"] if withdrawals else 0
    net_cash_flow = total_inflow - total_outflow
    
    # Opening and closing balance
    opening_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    
    return {
        "code": 0,
        "report": "cash_flow",
        "period": {"start_date": start_date, "end_date": end_date},
        "cash_inflows": total_inflow,
        "cash_outflows": total_outflow,
        "net_cash_flow": net_cash_flow,
        "operating_activities": {
            "receipts_from_customers": total_inflow * 0.9,  # Approximation
            "payments_to_suppliers": total_outflow * 0.7
        },
        "investing_activities": {
            "total": 0  # Would need asset purchase tracking
        },
        "financing_activities": {
            "total": 0  # Would need loan/equity tracking
        }
    }


@router.get("/reports/trial-balance")
async def get_trial_balance(
    request: Request,
    as_of_date: Optional[str] = None,
):
    """Generate Trial Balance report"""
    org_id = _get_org_id(request)
    now = datetime.now(timezone.utc)
    if not as_of_date:
        as_of_date = now.strftime("%Y-%m-%d")
    
    query = {"is_active": True, "organization_id": org_id}
    
    accounts = await chart_of_accounts_col.find(query, {"_id": 0}).sort("account_code", 1).to_list(500)
    
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for acc in accounts:
        balance = acc.get("balance", 0)
        debit = balance if balance > 0 else 0
        credit = abs(balance) if balance < 0 else 0
        
        # Asset and expense accounts normally have debit balances
        if acc.get("account_type") in ["asset", "expense"]:
            debit = abs(balance) if balance else 0
            credit = 0
        # Liability, equity, and income accounts normally have credit balances
        else:
            credit = abs(balance) if balance else 0
            debit = 0
        
        total_debit += debit
        total_credit += credit
        
        trial_balance.append({
            "account_code": acc.get("account_code"),
            "account_name": acc.get("account_name"),
            "account_type": acc.get("account_type"),
            "debit": debit,
            "credit": credit
        })
    
    return {
        "code": 0,
        "report": "trial_balance",
        "as_of_date": as_of_date,
        "accounts": trial_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01
    }


# ==================== DASHBOARD STATS ====================

@router.get("/dashboard/stats")
async def get_banking_dashboard_stats(request: Request):
    """Get banking dashboard statistics"""
    org_id = _get_org_id(request)
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    
    # Bank account totals — org-scoped
    accounts = await bank_accounts_col.find({"is_active": True, "organization_id": org_id}, {"_id": 0}).to_list(50)
    total_balance = sum(a.get("current_balance", 0) for a in accounts)
    
    # Monthly transactions — org-scoped
    monthly_deposits = await bank_transactions_col.aggregate([
        {"$match": {"organization_id": org_id, "transaction_type": {"$in": ["deposit", "transfer_in"]}, "transaction_date": {"$gte": month_start.strftime("%Y-%m-%d")}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    monthly_withdrawals = await bank_transactions_col.aggregate([
        {"$match": {"organization_id": org_id, "transaction_type": {"$in": ["withdrawal", "transfer_out"]}, "transaction_date": {"$gte": month_start.strftime("%Y-%m-%d")}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    # Unreconciled count — org-scoped
    unreconciled = await bank_transactions_col.count_documents({"organization_id": org_id, "is_reconciled": False})
    
    # Recent reconciliations — org-scoped
    recent_recons = await reconciliation_col.find({"organization_id": org_id}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "code": 0,
        "stats": {
            "total_bank_balance": total_balance,
            "bank_accounts_count": len(accounts),
            "monthly_deposits": monthly_deposits[0]["total"] if monthly_deposits else 0,
            "monthly_withdrawals": monthly_withdrawals[0]["total"] if monthly_withdrawals else 0,
            "unreconciled_transactions": unreconciled,
            "recent_reconciliations": recent_recons
        }
    }
