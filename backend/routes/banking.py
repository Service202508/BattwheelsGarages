"""
Banking API Routes
==================
RESTful API for bank account management:
- Account CRUD
- Transaction recording
- Reconciliation
- Summary reports

Author: Battwheels OS
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging
import jwt

from services.banking_service import (
    init_banking_service,
    get_banking_service,
    ACCOUNT_TYPES,
    TRANSACTION_TYPES,
    TRANSACTION_CATEGORIES
)
from core.subscriptions.entitlement import require_feature

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/banking",
    tags=["Banking"],
    dependencies=[Depends(require_feature("accounting_module"))]
)

# ==================== MODELS ====================

class AccountCreate(BaseModel):
    account_name: str
    bank_name: str
    account_number: str
    ifsc_code: str
    account_type: str = "CURRENT"
    opening_balance: float = 0
    opening_balance_date: Optional[str] = None
    upi_id: Optional[str] = None
    is_default: bool = False


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    bank_name: Optional[str] = None
    upi_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class TransactionCreate(BaseModel):
    transaction_date: str
    description: str
    transaction_type: str  # DEBIT or CREDIT
    amount: float = Field(..., gt=0)
    category: str = "OTHER"
    reference_number: Optional[str] = None


class ReconcileRequest(BaseModel):
    transaction_ids: List[str]
    reconciled: bool = True


class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float = Field(..., gt=0)
    transfer_date: str
    reference: Optional[str] = None
    notes: Optional[str] = None


# ==================== DEPENDENCIES ====================

db_ref = None


def set_db(db):
    global db_ref
    db_ref = db
    init_banking_service(db)


def get_service():
    return get_banking_service()


async def get_current_user_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        return user.get("user_id", "system")
    return "system"


async def get_org_id(request: Request) -> str:
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        return org_id
    
    org_id = request.cookies.get("org_id")
    if org_id:
        return org_id
    
    user = getattr(request.state, "user", None)
    if user and user.get("org_id"):
        return user.get("org_id")
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, options={"verify_signature": False})
            if payload.get("org_id"):
                return payload.get("org_id")
        except:
            pass
    
    raise HTTPException(status_code=400, detail="Organization ID required")


# ==================== ROUTES ====================

@router.get("/constants")
async def get_constants():
    """Get banking constants"""
    return {
        "code": 0,
        "account_types": ACCOUNT_TYPES,
        "transaction_types": TRANSACTION_TYPES,
        "transaction_categories": TRANSACTION_CATEGORIES
    }


@router.get("/summary")
async def get_summary(request: Request):
    """Get banking summary for the organization"""
    service = get_service()
    org_id = await get_org_id(request)
    
    summary = await service.get_summary(org_id)
    
    return {"code": 0, "summary": summary}


@router.get("/accounts")
async def list_accounts(request: Request, include_inactive: bool = Query(False)
):
    """List all bank accounts"""
    service = get_service()
    org_id = await get_org_id(request)
    
    accounts = await service.list_accounts(org_id, include_inactive)
    
    return {"code": 0, "accounts": accounts}


@router.post("/accounts")
async def create_account(request: Request, data: AccountCreate):
    """Create a new bank account with opening balance journal entry"""
    from services.double_entry_service import get_double_entry_service, init_double_entry_service
    
    service = get_service()
    org_id = await get_org_id(request)
    user_id = await get_current_user_id(request)
    
    # Get double-entry service for opening balance journal
    de_service = None
    if data.opening_balance > 0:
        try:
            de_service = get_double_entry_service()
        except:
            init_double_entry_service(db_ref)
            de_service = get_double_entry_service()
    
    account = await service.create_account(
        org_id=org_id,
        account_name=data.account_name,
        bank_name=data.bank_name,
        account_number=data.account_number,
        ifsc_code=data.ifsc_code,
        account_type=data.account_type,
        opening_balance=data.opening_balance,
        opening_balance_date=data.opening_balance_date,
        upi_id=data.upi_id,
        is_default=data.is_default,
        created_by=user_id,
        de_service=de_service
    )
    
    return {"code": 0, "message": "Account created", "account": account}


@router.get("/accounts/{account_id}")
async def get_account(request: Request, account_id: str):
    """Get a single bank account"""
    service = get_service()
    
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"code": 0, "account": account}


@router.put("/accounts/{account_id}")
async def update_account(request: Request, account_id: str, data: AccountUpdate):
    """Update a bank account"""
    service = get_service()
    
    updates = {k: v for k, v in data.dict().items() if v is not None}
    account = await service.update_account(account_id, updates)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"code": 0, "message": "Account updated", "account": account}


@router.get("/accounts/{account_id}/transactions")
async def get_transactions(request: Request, account_id: str, date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    reconciled: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500)
):
    """Get transactions for a bank account"""
    service = get_service()
    
    transactions, total = await service.get_transactions(
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
        reconciled=reconciled,
        page=page,
        limit=limit
    )
    
    return {
        "code": 0,
        "transactions": transactions,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/accounts/{account_id}/transactions")
async def record_transaction(request: Request, account_id: str,
    data: TransactionCreate
):
    """Record a bank transaction"""
    service = get_service()
    user_id = await get_current_user_id(request)
    
    try:
        transaction = await service.record_transaction(
            account_id=account_id,
            transaction_date=data.transaction_date,
            description=data.description,
            transaction_type=data.transaction_type,
            amount=data.amount,
            category=data.category,
            reference_number=data.reference_number,
            created_by=user_id
        )
        
        return {"code": 0, "message": "Transaction recorded", "transaction": transaction}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}/balance")
async def get_balance(request: Request, account_id: str):
    """Get current balance for a bank account"""
    service = get_service()
    
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {
        "code": 0,
        "account_id": account_id,
        "account_name": account["account_name"],
        "current_balance": account.get("current_balance", 0),
        "opening_balance": account.get("opening_balance", 0)
    }


@router.post("/accounts/{account_id}/recalculate")
async def recalculate_balance(request: Request, account_id: str):
    """Recalculate account balance from transactions"""
    service = get_service()
    
    new_balance = await service.recalculate_balance(account_id)
    
    return {
        "code": 0,
        "message": "Balance recalculated",
        "current_balance": new_balance
    }


@router.get("/accounts/{account_id}/monthly")
async def get_monthly_summary(request: Request, account_id: str, months: int = Query(6, ge=1, le=12)
):
    """Get transactions grouped by month"""
    service = get_service()
    
    data = await service.get_transactions_by_month(account_id, months)
    
    return {"code": 0, "monthly": data}


@router.post("/reconcile")
async def bulk_reconcile(request: Request, data: ReconcileRequest):
    """Bulk reconcile transactions"""
    service = get_service()
    
    count = await service.bulk_reconcile(data.transaction_ids, data.reconciled)
    
    action = "reconciled" if data.reconciled else "unreconciled"
    return {
        "code": 0,
        "message": f"{count} transactions {action}",
        "modified_count": count
    }


@router.post("/reconcile/{transaction_id}")
async def reconcile_transaction(request: Request, transaction_id: str, reconciled: bool = Query(True)
):
    """Reconcile a single transaction"""
    service = get_service()
    
    transaction = await service.reconcile_transaction(transaction_id, reconciled)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    action = "reconciled" if reconciled else "unreconciled"
    return {"code": 0, "message": f"Transaction {action}", "transaction": transaction}


@router.post("/transfer")
async def transfer_funds(request: Request, data: TransferRequest):
    """Transfer funds between two bank accounts"""
    from services.double_entry_service import get_double_entry_service, init_double_entry_service
    
    service = get_service()
    user_id = await get_current_user_id(request)
    
    # Get double-entry service
    try:
        de_service = get_double_entry_service()
    except:
        init_double_entry_service(db_ref)
        de_service = get_double_entry_service()
    
    try:
        transfer, journal_entry_id = await service.transfer_between_accounts(
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            amount=data.amount,
            transfer_date=data.transfer_date,
            reference=data.reference,
            notes=data.notes,
            created_by=user_id,
            de_service=de_service
        )
        
        return {
            "code": 0,
            "message": f"Transferred ₹{data.amount}",
            "transfer": transfer,
            "journal_entry_id": journal_entry_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
