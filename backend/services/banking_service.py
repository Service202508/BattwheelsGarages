"""
Banking Service - Bank Account Management
==========================================
Complete banking module with:
- Multiple bank accounts tracking
- Transaction recording
- Balance calculation
- Reconciliation support

Author: Battwheels OS
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)

ACCOUNT_TYPES = ["CURRENT", "SAVINGS", "CASH", "CREDIT_CARD"]
TRANSACTION_TYPES = ["DEBIT", "CREDIT"]
TRANSACTION_CATEGORIES = [
    "CUSTOMER_PAYMENT", "VENDOR_PAYMENT", "EXPENSE", 
    "SALARY", "TAX", "TRANSFER", "OTHER"
]


class BankingService:
    """Service for managing bank accounts and transactions"""
    
    def __init__(self, db):
        self.db = db
        self.accounts = db.bank_accounts
        self.transactions = db.bank_transactions
        logger.info("BankingService initialized")
    
    # ==================== ACCOUNT MANAGEMENT ====================
    
    async def create_account(
        self,
        org_id: str,
        account_name: str,
        bank_name: str,
        account_number: str,
        ifsc_code: str,
        account_type: str = "CURRENT",
        opening_balance: float = 0,
        opening_balance_date: Optional[str] = None,
        upi_id: Optional[str] = None,
        is_default: bool = False,
        created_by: str = "system",
        de_service = None
    ) -> Dict[str, Any]:
        """Create a new bank account"""
        account_id = f"bank_{uuid.uuid4().hex[:12]}"
        
        # If this is default, unset other defaults
        if is_default:
            await self.accounts.update_many(
                {"organization_id": org_id},
                {"$set": {"is_default": False}}
            )
        
        # Check if this is the first account (make it default)
        existing_count = await self.accounts.count_documents({"organization_id": org_id})
        if existing_count == 0:
            is_default = True
        
        balance_date = opening_balance_date or datetime.now().strftime("%Y-%m-%d")
        
        account = {
            "account_id": account_id,
            "organization_id": org_id,
            "account_name": account_name,
            "bank_name": bank_name,
            "account_number": account_number,  # Consider encrypting in production
            "account_number_last4": account_number[-4:] if len(account_number) >= 4 else account_number,
            "ifsc_code": ifsc_code,
            "account_type": account_type,
            "opening_balance": opening_balance,
            "opening_balance_date": balance_date,
            "current_balance": opening_balance,
            "upi_id": upi_id,
            "is_active": True,
            "is_default": is_default,
            "created_by": created_by,
            "opening_journal_entry_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.accounts.insert_one(account)
        logger.info(f"Created bank account {account_name} for org {org_id}")
        
        # Post opening balance journal entry if there's an opening balance
        if opening_balance > 0 and de_service:
            journal_id = await self._post_opening_balance_journal(
                org_id, account_id, account_name, bank_name, 
                account_number[-4:] if len(account_number) >= 4 else account_number,
                opening_balance, balance_date, created_by, de_service
            )
            if journal_id:
                await self.accounts.update_one(
                    {"account_id": account_id},
                    {"$set": {"opening_journal_entry_id": journal_id}}
                )
        
        return {k: v for k, v in account.items() if k != "_id"}
    
    async def _post_opening_balance_journal(
        self,
        org_id: str,
        account_id: str,
        account_name: str,
        bank_name: str,
        last4: str,
        amount: float,
        balance_date: str,
        created_by: str,
        de_service
    ) -> Optional[str]:
        """Post journal entry for opening balance"""
        try:
            await de_service.ensure_system_accounts(org_id)
            
            # Get Bank and Opening Balance Equity accounts
            bank_account = await de_service.get_account_by_code(org_id, "1200")
            equity_account = await de_service.get_account_by_code(org_id, "3300")
            
            if not bank_account or not equity_account:
                logger.warning("Missing accounts for opening balance journal")
                return None
            
            narration = f"Opening balance - {bank_name} ****{last4}"
            
            success, msg, entry = await de_service.create_journal_entry(
                organization_id=org_id,
                entry_date=balance_date,
                description=narration,
                lines=[
                    {
                        "account_id": bank_account["account_id"],
                        "debit_amount": amount,
                        "credit_amount": 0,
                        "description": f"Opening balance - {account_name}"
                    },
                    {
                        "account_id": equity_account["account_id"],
                        "debit_amount": 0,
                        "credit_amount": amount,
                        "description": f"Opening balance equity - {bank_name}"
                    }
                ],
                entry_type="OPENING",
                source_document_id=account_id,
                source_document_type="BANK_OPENING",
                created_by=created_by
            )
            
            if success:
                logger.info(f"Posted opening balance journal: {entry.get('entry_id')}")
                return entry.get("entry_id")
            return None
            
        except Exception as e:
            logger.error(f"Error posting opening balance journal: {e}")
            return None
    
    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get a single bank account"""
        return await self.accounts.find_one(
            {"account_id": account_id},
            {"_id": 0}
        )
    
    async def list_accounts(
        self,
        org_id: str,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """List all bank accounts for an organization"""
        query = {"organization_id": org_id}
        if not include_inactive:
            query["is_active"] = True
        
        return await self.accounts.find(query, {"_id": 0}).sort(
            [("is_default", -1), ("account_name", 1)]
        ).to_list(50)
    
    async def update_account(
        self,
        account_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a bank account"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Handle default flag
        if updates.get("is_default"):
            account = await self.get_account(account_id)
            if account:
                await self.accounts.update_many(
                    {"organization_id": account["organization_id"]},
                    {"$set": {"is_default": False}}
                )
        
        result = await self.accounts.find_one_and_update(
            {"account_id": account_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def recalculate_balance(self, account_id: str) -> float:
        """Recalculate account balance from transactions"""
        account = await self.get_account(account_id)
        if not account:
            return 0
        
        opening = account.get("opening_balance", 0)
        
        # Sum all transactions
        pipeline = [
            {"$match": {"bank_account_id": account_id}},
            {"$group": {
                "_id": "$transaction_type",
                "total": {"$sum": "$amount"}
            }}
        ]
        
        results = await self.transactions.aggregate(pipeline).to_list(2)
        
        credits = 0
        debits = 0
        for r in results:
            if r["_id"] == "CREDIT":
                credits = r["total"]
            elif r["_id"] == "DEBIT":
                debits = r["total"]
        
        current_balance = opening + credits - debits
        
        # Update account balance
        await self.accounts.update_one(
            {"account_id": account_id},
            {"$set": {"current_balance": current_balance}}
        )
        
        return current_balance
    
    # ==================== TRANSACTION MANAGEMENT ====================
    
    async def record_transaction(
        self,
        account_id: str,
        transaction_date: str,
        description: str,
        transaction_type: str,  # DEBIT or CREDIT
        amount: float,
        category: str = "OTHER",
        reference_number: Optional[str] = None,
        journal_entry_id: Optional[str] = None,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """Record a bank transaction"""
        account = await self.get_account(account_id)
        if not account:
            raise ValueError("Bank account not found")
        
        transaction_id = f"bank_txn_{uuid.uuid4().hex[:12]}"
        
        # Calculate new balance
        current_balance = account.get("current_balance", 0)
        if transaction_type == "CREDIT":
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount
        
        transaction = {
            "transaction_id": transaction_id,
            "bank_account_id": account_id,
            "organization_id": account["organization_id"],
            "transaction_date": transaction_date,
            "value_date": transaction_date,
            "description": description,
            "reference_number": reference_number,
            "transaction_type": transaction_type,
            "amount": amount,
            "balance_after": new_balance,
            "category": category,
            "reconciled": False,
            "reconciled_date": None,
            "journal_entry_id": journal_entry_id,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.transactions.insert_one(transaction)
        
        # Update account balance
        await self.accounts.update_one(
            {"account_id": account_id},
            {"$set": {"current_balance": new_balance}}
        )
        
        logger.info(f"Recorded {transaction_type} of ₹{amount} for account {account_id}")
        
        return {k: v for k, v in transaction.items() if k != "_id"}
    
    async def get_transactions(
        self,
        account_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
        reconciled: Optional[bool] = None,
        page: int = 1,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get transactions for a bank account"""
        query = {"bank_account_id": account_id}
        
        if date_from:
            query["transaction_date"] = query.get("transaction_date", {})
            query["transaction_date"]["$gte"] = date_from
        if date_to:
            query["transaction_date"] = query.get("transaction_date", {})
            query["transaction_date"]["$lte"] = date_to
        if category:
            query["category"] = category
        if reconciled is not None:
            query["reconciled"] = reconciled
        
        total = await self.transactions.count_documents(query)
        skip = (page - 1) * limit
        
        transactions = await self.transactions.find(query, {"_id": 0}).sort(
            "transaction_date", -1
        ).skip(skip).limit(limit).to_list(limit)
        
        return transactions, total
    
    async def reconcile_transaction(
        self,
        transaction_id: str,
        reconciled: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Mark a transaction as reconciled"""
        result = await self.transactions.find_one_and_update(
            {"transaction_id": transaction_id},
            {"$set": {
                "reconciled": reconciled,
                "reconciled_date": datetime.now().strftime("%Y-%m-%d") if reconciled else None
            }},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def bulk_reconcile(
        self,
        transaction_ids: List[str],
        reconciled: bool = True
    ) -> int:
        """Bulk reconcile transactions"""
        result = await self.transactions.update_many(
            {"transaction_id": {"$in": transaction_ids}},
            {"$set": {
                "reconciled": reconciled,
                "reconciled_date": datetime.now().strftime("%Y-%m-%d") if reconciled else None
            }}
        )
        return result.modified_count
    
    # ==================== SUMMARY & REPORTING ====================
    
    async def get_summary(self, org_id: str) -> Dict[str, Any]:
        """Get banking summary for an organization"""
        accounts = await self.list_accounts(org_id)
        
        total_balance = sum(a.get("current_balance", 0) for a in accounts)
        
        # Get unreconciled count
        unreconciled_pipeline = [
            {"$match": {"organization_id": org_id, "reconciled": False}},
            {"$count": "count"}
        ]
        unreconciled = await self.transactions.aggregate(unreconciled_pipeline).to_list(1)
        unreconciled_count = unreconciled[0]["count"] if unreconciled else 0
        
        # Get this month's movement
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        month_pipeline = [
            {"$match": {
                "organization_id": org_id,
                "transaction_date": {"$gte": month_start}
            }},
            {"$group": {
                "_id": "$transaction_type",
                "total": {"$sum": "$amount"}
            }}
        ]
        
        month_results = await self.transactions.aggregate(month_pipeline).to_list(2)
        credits_this_month = 0
        debits_this_month = 0
        for r in month_results:
            if r["_id"] == "CREDIT":
                credits_this_month = r["total"]
            elif r["_id"] == "DEBIT":
                debits_this_month = r["total"]
        
        return {
            "total_accounts": len(accounts),
            "total_balance": total_balance,
            "accounts": accounts,
            "unreconciled_count": unreconciled_count,
            "this_month": {
                "credits": credits_this_month,
                "debits": debits_this_month,
                "net_movement": credits_this_month - debits_this_month
            }
        }
    
    async def get_transactions_by_month(
        self,
        account_id: str,
        months: int = 6
    ) -> List[Dict[str, Any]]:
        """Get transactions grouped by month"""
        from datetime import timedelta
        
        start_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
        
        pipeline = [
            {"$match": {
                "bank_account_id": account_id,
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {"$substr": ["$transaction_date", 0, 7]},
                "credits": {
                    "$sum": {"$cond": [{"$eq": ["$transaction_type", "CREDIT"]}, "$amount", 0]}
                },
                "debits": {
                    "$sum": {"$cond": [{"$eq": ["$transaction_type", "DEBIT"]}, "$amount", 0]}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.transactions.aggregate(pipeline).to_list(months)
        
        return [
            {
                "month": r["_id"],
                "credits": r["credits"],
                "debits": r["debits"],
                "net": r["credits"] - r["debits"],
                "count": r["count"]
            }
            for r in results
        ]
    
    # ==================== INTER-ACCOUNT TRANSFERS ====================
    
    async def transfer_between_accounts(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: float,
        transfer_date: str,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: str = "system",
        de_service = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Transfer funds between two bank accounts"""
        from_account = await self.get_account(from_account_id)
        to_account = await self.get_account(to_account_id)
        
        if not from_account:
            raise ValueError("Source account not found")
        if not to_account:
            raise ValueError("Destination account not found")
        
        if from_account["organization_id"] != to_account["organization_id"]:
            raise ValueError("Cannot transfer between different organizations")
        
        # Check sufficient balance (for non-credit card accounts)
        if from_account["account_type"] != "CREDIT_CARD":
            if from_account["current_balance"] < amount:
                raise ValueError(f"Insufficient balance in {from_account['account_name']}")
        
        transfer_id = f"transfer_{uuid.uuid4().hex[:12]}"
        
        # Record debit transaction (from account)
        debit_txn = await self.record_transaction(
            account_id=from_account_id,
            transaction_date=transfer_date,
            description=f"Transfer to {to_account['account_name']}",
            transaction_type="DEBIT",
            amount=amount,
            category="TRANSFER",
            reference_number=reference or transfer_id,
            created_by=created_by
        )
        
        # Record credit transaction (to account)
        credit_txn = await self.record_transaction(
            account_id=to_account_id,
            transaction_date=transfer_date,
            description=f"Transfer from {from_account['account_name']}",
            transaction_type="CREDIT",
            amount=amount,
            category="TRANSFER",
            reference_number=reference or transfer_id,
            created_by=created_by
        )
        
        # Post journal entry
        journal_entry_id = None
        if de_service:
            journal_entry_id = await self._post_transfer_journal(
                from_account, to_account, amount, transfer_date, created_by, de_service
            )
        
        transfer = {
            "transfer_id": transfer_id,
            "from_account_id": from_account_id,
            "from_account_name": from_account["account_name"],
            "to_account_id": to_account_id,
            "to_account_name": to_account["account_name"],
            "amount": amount,
            "transfer_date": transfer_date,
            "reference": reference,
            "notes": notes,
            "debit_transaction_id": debit_txn["transaction_id"],
            "credit_transaction_id": credit_txn["transaction_id"],
            "journal_entry_id": journal_entry_id,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Transferred ₹{amount} from {from_account['account_name']} to {to_account['account_name']}")
        
        return transfer, journal_entry_id
    
    async def _post_transfer_journal(
        self,
        from_account: Dict,
        to_account: Dict,
        amount: float,
        transfer_date: str,
        created_by: str,
        de_service
    ) -> Optional[str]:
        """Post journal entry for inter-account transfer"""
        try:
            org_id = from_account["organization_id"]
            await de_service.ensure_system_accounts(org_id)
            
            # Both accounts use Bank A/C (1200) in double-entry
            bank_account = await de_service.get_account_by_code(org_id, "1200")
            
            if not bank_account:
                return None
            
            narration = f"Bank transfer: {from_account['account_name']} → {to_account['account_name']}"
            
            success, msg, entry = await de_service.create_journal_entry(
                organization_id=org_id,
                entry_date=transfer_date,
                description=narration,
                lines=[
                    {
                        "account_id": bank_account["account_id"],
                        "debit_amount": amount,
                        "credit_amount": 0,
                        "description": f"Transfer to {to_account['account_name']}"
                    },
                    {
                        "account_id": bank_account["account_id"],
                        "debit_amount": 0,
                        "credit_amount": amount,
                        "description": f"Transfer from {from_account['account_name']}"
                    }
                ],
                entry_type="JOURNAL",
                source_document_id=f"{from_account['account_id']}_to_{to_account['account_id']}",
                source_document_type="BANK_TRANSFER",
                created_by=created_by
            )
            
            if success:
                return entry.get("entry_id")
            return None
            
        except Exception as e:
            logger.error(f"Error posting transfer journal: {e}")
            return None


# ==================== SERVICE FACTORY ====================

_banking_service: Optional[BankingService] = None


def get_banking_service() -> BankingService:
    if _banking_service is None:
        raise ValueError("BankingService not initialized")
    return _banking_service


def init_banking_service(db) -> BankingService:
    global _banking_service
    _banking_service = BankingService(db)
    return _banking_service
