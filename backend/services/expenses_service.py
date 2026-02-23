"""
Expenses Service - Business Expense Management
===============================================
Complete expense tracking with:
- GST Input Credit (ITC) capture
- Multi-status workflow (Draft → Submitted → Approved → Paid)
- Category-based expense classification
- Double-entry accounting integration
- Receipt attachment support

Author: Battwheels OS
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import uuid
import logging
import re

logger = logging.getLogger(__name__)

# ========================= CONSTANTS =========================

EXPENSE_STATUSES = ["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "PAID"]
PAYMENT_MODES = ["CASH", "BANK", "CREDIT_CARD", "UPI", "PENDING"]
GST_RATES = [0, 5, 12, 18, 28]

# Default expense categories to seed
DEFAULT_EXPENSE_CATEGORIES = [
    {"name": "Travel & Conveyance", "code": "6710", "is_itc_eligible": True},
    {"name": "Office Supplies", "code": "6400", "is_itc_eligible": True},
    {"name": "Utilities", "code": "6300", "is_itc_eligible": True},
    {"name": "Rent", "code": "6200", "is_itc_eligible": True},
    {"name": "Repairs & Maintenance", "code": "6720", "is_itc_eligible": True},
    {"name": "Professional Fees", "code": "6500", "is_itc_eligible": True},
    {"name": "Advertising & Marketing", "code": "6730", "is_itc_eligible": True},
    {"name": "Staff Welfare", "code": "6740", "is_itc_eligible": False},
    {"name": "Communication", "code": "6750", "is_itc_eligible": True},
    {"name": "Miscellaneous", "code": "6900", "is_itc_eligible": False},
]


class ExpensesService:
    """Service for managing business expenses"""
    
    def __init__(self, db):
        self.db = db
        self.expenses = db.expenses
        self.categories = db.expense_categories
        self.counters = db.counters
        logger.info("ExpensesService initialized")
    
    # ==================== COUNTER MANAGEMENT ====================
    
    async def get_next_expense_number(self, org_id: str) -> str:
        """Generate next expense number: EXP-2024-0001"""
        year = datetime.now().year
        counter_id = f"expense_{org_id}_{year}"
        
        result = await self.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        
        seq = result.get("seq", 1)
        return f"EXP-{year}-{seq:04d}"
    
    # ==================== CATEGORY MANAGEMENT ====================
    
    async def seed_default_categories(self, org_id: str) -> int:
        """Seed default expense categories for an organization"""
        existing = await self.categories.count_documents({"organization_id": org_id})
        if existing > 0:
            return 0
        
        categories = []
        for cat in DEFAULT_EXPENSE_CATEGORIES:
            categories.append({
                "category_id": f"exp_cat_{uuid.uuid4().hex[:12]}",
                "organization_id": org_id,
                "name": cat["name"],
                "default_account_code": cat["code"],
                "is_itc_eligible": cat["is_itc_eligible"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        if categories:
            await self.categories.insert_many(categories)
            logger.info(f"Seeded {len(categories)} default expense categories for org {org_id}")
        
        return len(categories)
    
    async def list_categories(self, org_id: str) -> List[Dict[str, Any]]:
        """List all expense categories for an organization"""
        # Seed defaults if none exist
        await self.seed_default_categories(org_id)
        
        return await self.categories.find(
            {"organization_id": org_id, "is_active": True},
            {"_id": 0}
        ).sort("name", 1).to_list(100)
    
    async def create_category(
        self,
        org_id: str,
        name: str,
        default_account_code: str = "6900",
        is_itc_eligible: bool = False
    ) -> Dict[str, Any]:
        """Create a new expense category"""
        category_id = f"exp_cat_{uuid.uuid4().hex[:12]}"
        
        category = {
            "category_id": category_id,
            "organization_id": org_id,
            "name": name,
            "default_account_code": default_account_code,
            "is_itc_eligible": is_itc_eligible,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.categories.insert_one(category)
        return {k: v for k, v in category.items() if k != "_id"}
    
    async def update_category(
        self,
        category_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an expense category"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.categories.find_one_and_update(
            {"category_id": category_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get a single category"""
        result = await self.categories.find_one(
            {"category_id": category_id},
            {"_id": 0}
        )
        return result
    
    # ==================== EXPENSE CRUD ====================
    
    async def create_expense(
        self,
        org_id: str,
        expense_date: str,
        vendor_name: str,
        description: str,
        amount: float,
        category_id: str,
        employee_id: str,
        vendor_gstin: Optional[str] = None,
        gst_rate: float = 0,
        is_igst: bool = False,
        hsn_sac_code: Optional[str] = None,
        payment_mode: str = "PENDING",
        bank_account_id: Optional[str] = None,
        receipt_url: Optional[str] = None,
        project_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new expense in DRAFT status"""
        expense_id = f"exp_{uuid.uuid4().hex[:12]}"
        expense_number = await self.get_next_expense_number(org_id)
        
        # Calculate GST amounts
        base_amount = Decimal(str(amount))
        gst_rate_decimal = Decimal(str(gst_rate)) / 100
        
        if is_igst:
            igst_amount = (base_amount * gst_rate_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            cgst_amount = Decimal('0')
            sgst_amount = Decimal('0')
        else:
            half_rate = gst_rate_decimal / 2
            cgst_amount = (base_amount * half_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            sgst_amount = (base_amount * half_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            igst_amount = Decimal('0')
        
        total_amount = base_amount + cgst_amount + sgst_amount + igst_amount
        
        # Determine ITC eligibility
        is_itc_eligible = False
        if vendor_gstin and self._validate_gstin(vendor_gstin):
            category = await self.get_category(category_id)
            if category and category.get("is_itc_eligible", False):
                is_itc_eligible = True
        
        expense = {
            "expense_id": expense_id,
            "expense_number": expense_number,
            "organization_id": org_id,
            "expense_date": expense_date,
            "vendor_name": vendor_name,
            "vendor_gstin": vendor_gstin,
            "category_id": category_id,
            "description": description,
            "amount": float(base_amount),
            "gst_rate": gst_rate,
            "cgst_amount": float(cgst_amount),
            "sgst_amount": float(sgst_amount),
            "igst_amount": float(igst_amount),
            "total_amount": float(total_amount),
            "is_igst": is_igst,
            "hsn_sac_code": hsn_sac_code,
            "payment_mode": payment_mode,
            "bank_account_id": bank_account_id,
            "receipt_url": receipt_url,
            "project_id": project_id,
            "ticket_id": ticket_id,
            "employee_id": employee_id,
            "status": "DRAFT",
            "is_itc_eligible": is_itc_eligible,
            "itc_claimed": False,
            "approved_by": None,
            "approved_at": None,
            "rejection_reason": None,
            "journal_entry_id": None,
            "payment_journal_entry_id": None,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.expenses.insert_one(expense)
        logger.info(f"Created expense {expense_number} for org {org_id}")
        
        return {k: v for k, v in expense.items() if k != "_id"}
    
    def _validate_gstin(self, gstin: str) -> bool:
        """Validate GSTIN format: 2 digits + 10 chars PAN + 1 digit + Z + 1 check digit"""
        if not gstin:
            return False
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$'
        return bool(re.match(pattern, gstin.upper()))
    
    async def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
        """Get a single expense by ID"""
        result = await self.expenses.find_one(
            {"expense_id": expense_id},
            {"_id": 0}
        )
        return result
    
    async def update_expense(
        self,
        expense_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an expense (only if DRAFT or REJECTED)"""
        expense = await self.get_expense(expense_id)
        if not expense:
            return None
        
        if expense["status"] not in ["DRAFT", "REJECTED"]:
            raise ValueError(f"Cannot edit expense in {expense['status']} status")
        
        # Recalculate GST if amount or rate changed
        if "amount" in updates or "gst_rate" in updates:
            base_amount = Decimal(str(updates.get("amount", expense["amount"])))
            gst_rate = updates.get("gst_rate", expense["gst_rate"])
            is_igst = updates.get("is_igst", expense.get("is_igst", False))
            
            gst_rate_decimal = Decimal(str(gst_rate)) / 100
            
            if is_igst:
                igst_amount = (base_amount * gst_rate_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cgst_amount = Decimal('0')
                sgst_amount = Decimal('0')
            else:
                half_rate = gst_rate_decimal / 2
                cgst_amount = (base_amount * half_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                sgst_amount = (base_amount * half_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                igst_amount = Decimal('0')
            
            updates["cgst_amount"] = float(cgst_amount)
            updates["sgst_amount"] = float(sgst_amount)
            updates["igst_amount"] = float(igst_amount)
            updates["total_amount"] = float(base_amount + cgst_amount + sgst_amount + igst_amount)
        
        # Re-check ITC eligibility
        if "vendor_gstin" in updates or "category_id" in updates:
            vendor_gstin = updates.get("vendor_gstin", expense.get("vendor_gstin"))
            category_id = updates.get("category_id", expense.get("category_id"))
            
            is_itc_eligible = False
            if vendor_gstin and self._validate_gstin(vendor_gstin):
                category = await self.get_category(category_id)
                if category and category.get("is_itc_eligible", False):
                    is_itc_eligible = True
            updates["is_itc_eligible"] = is_itc_eligible
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # If re-submitting rejected expense, reset status to DRAFT
        if expense["status"] == "REJECTED":
            updates["status"] = "DRAFT"
            updates["rejection_reason"] = None
        
        result = await self.expenses.find_one_and_update(
            {"expense_id": expense_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense (only if DRAFT)"""
        expense = await self.get_expense(expense_id)
        if not expense:
            return False
        
        if expense["status"] != "DRAFT":
            raise ValueError(f"Cannot delete expense in {expense['status']} status")
        
        result = await self.expenses.delete_one({"expense_id": expense_id})
        return result.deleted_count > 0
    
    async def list_expenses(
        self,
        org_id: str,
        status: Optional[str] = None,
        category_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        project_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List expenses with filters and pagination"""
        query = {"organization_id": org_id}
        
        if status:
            query["status"] = status
        if category_id:
            query["category_id"] = category_id
        if date_from:
            query["expense_date"] = query.get("expense_date", {})
            query["expense_date"]["$gte"] = date_from
        if date_to:
            query["expense_date"] = query.get("expense_date", {})
            query["expense_date"]["$lte"] = date_to
        if project_id:
            query["project_id"] = project_id
        if employee_id:
            query["employee_id"] = employee_id
        if search:
            query["$or"] = [
                {"expense_number": {"$regex": search, "$options": "i"}},
                {"vendor_name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        total = await self.expenses.count_documents(query)
        skip = (page - 1) * limit
        
        expenses = await self.expenses.find(query, {"_id": 0}).sort(
            "expense_date", -1
        ).skip(skip).limit(limit).to_list(limit)
        
        # Enrich with category names
        for exp in expenses:
            if exp.get("category_id"):
                cat = await self.get_category(exp["category_id"])
                exp["category_name"] = cat.get("name") if cat else "Unknown"
        
        return expenses, total
    
    # ==================== WORKFLOW ====================
    
    async def submit_expense(self, expense_id: str) -> Dict[str, Any]:
        """Submit expense for approval (DRAFT → SUBMITTED)"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        
        if expense["status"] != "DRAFT":
            raise ValueError(f"Cannot submit expense in {expense['status']} status")
        
        result = await self.expenses.find_one_and_update(
            {"expense_id": expense_id},
            {"$set": {
                "status": "SUBMITTED",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            return_document=True
        )
        
        logger.info(f"Expense {expense_id} submitted for approval")
        return {k: v for k, v in result.items() if k != "_id"}
    
    async def approve_expense(
        self,
        expense_id: str,
        approved_by: str,
        de_service = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Approve expense (SUBMITTED → APPROVED)
        Posts journal entry for the expense
        
        Returns: (expense, journal_entry_id)
        """
        expense = await self.get_expense(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        
        if expense["status"] != "SUBMITTED":
            raise ValueError(f"Cannot approve expense in {expense['status']} status")
        
        now = datetime.now(timezone.utc).isoformat()
        journal_entry_id = None
        
        # Post journal entry if double_entry_service provided
        if de_service:
            journal_entry_id = await self._post_approval_journal_entry(expense, approved_by, de_service)
        
        updates = {
            "status": "APPROVED",
            "approved_by": approved_by,
            "approved_at": now,
            "updated_at": now
        }
        
        if journal_entry_id:
            updates["journal_entry_id"] = journal_entry_id
        
        result = await self.expenses.find_one_and_update(
            {"expense_id": expense_id},
            {"$set": updates},
            return_document=True
        )
        
        logger.info(f"Expense {expense_id} approved by {approved_by}")
        return {k: v for k, v in result.items() if k != "_id"}, journal_entry_id
    
    async def _post_approval_journal_entry(
        self,
        expense: Dict[str, Any],
        approved_by: str,
        de_service
    ) -> Optional[str]:
        """Post journal entry on expense approval"""
        try:
            org_id = expense["organization_id"]
            await de_service.ensure_system_accounts(org_id)
            
            # Get expense category for account code
            category = await self.get_category(expense["category_id"])
            expense_account_code = category.get("default_account_code", "6900") if category else "6900"
            
            expense_account = await de_service.get_account_by_code(org_id, expense_account_code)
            if not expense_account:
                # Fallback to misc expense
                expense_account = await de_service.get_account_by_code(org_id, "6900")
            
            payable_account = await de_service.get_account_by_code(org_id, "2100")  # Accounts Payable
            
            lines = []
            
            if expense.get("is_itc_eligible") and expense.get("vendor_gstin"):
                # ITC eligible - separate GST amounts
                base_amount = expense["amount"]
                
                # Debit expense account (base amount)
                lines.append({
                    "account_id": expense_account["account_id"],
                    "debit_amount": base_amount,
                    "credit_amount": 0,
                    "description": expense["description"]
                })
                
                # Debit GST input accounts
                if expense.get("is_igst") and expense.get("igst_amount", 0) > 0:
                    igst_account = await de_service.get_account_by_code(org_id, "1430")
                    if igst_account:
                        lines.append({
                            "account_id": igst_account["account_id"],
                            "debit_amount": expense["igst_amount"],
                            "credit_amount": 0,
                            "description": f"Input IGST - {expense['expense_number']}"
                        })
                else:
                    if expense.get("cgst_amount", 0) > 0:
                        cgst_account = await de_service.get_account_by_code(org_id, "1410")
                        if cgst_account:
                            lines.append({
                                "account_id": cgst_account["account_id"],
                                "debit_amount": expense["cgst_amount"],
                                "credit_amount": 0,
                                "description": f"Input CGST - {expense['expense_number']}"
                            })
                    if expense.get("sgst_amount", 0) > 0:
                        sgst_account = await de_service.get_account_by_code(org_id, "1420")
                        if sgst_account:
                            lines.append({
                                "account_id": sgst_account["account_id"],
                                "debit_amount": expense["sgst_amount"],
                                "credit_amount": 0,
                                "description": f"Input SGST - {expense['expense_number']}"
                            })
                
                # Credit accounts payable (total amount)
                lines.append({
                    "account_id": payable_account["account_id"],
                    "debit_amount": 0,
                    "credit_amount": expense["total_amount"],
                    "description": f"Expense payable - {expense['expense_number']}"
                })
            else:
                # Not ITC eligible - full amount as expense
                lines.append({
                    "account_id": expense_account["account_id"],
                    "debit_amount": expense["total_amount"],
                    "credit_amount": 0,
                    "description": expense["description"]
                })
                
                lines.append({
                    "account_id": payable_account["account_id"],
                    "debit_amount": 0,
                    "credit_amount": expense["total_amount"],
                    "description": f"Expense payable - {expense['expense_number']}"
                })
            
            narration = f"Expense: {expense['description']} | Vendor: {expense['vendor_name']}"
            if expense.get("vendor_gstin"):
                narration += f" | GSTIN: {expense['vendor_gstin']}"
            
            success, msg, entry = await de_service.create_journal_entry(
                organization_id=org_id,
                entry_date=expense["expense_date"],
                description=narration,
                lines=lines,
                entry_type="EXPENSE",
                source_document_id=expense["expense_id"],
                source_document_type="EXPENSE",
                created_by=approved_by
            )
            
            if success:
                logger.info(f"Posted expense journal entry: {entry.get('entry_id')}")
                return entry.get("entry_id")
            else:
                logger.warning(f"Failed to post expense journal entry: {msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error posting expense journal entry: {e}")
            return None
    
    async def reject_expense(
        self,
        expense_id: str,
        rejected_by: str,
        reason: str
    ) -> Dict[str, Any]:
        """Reject expense (SUBMITTED → REJECTED)"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        
        if expense["status"] != "SUBMITTED":
            raise ValueError(f"Cannot reject expense in {expense['status']} status")
        
        result = await self.expenses.find_one_and_update(
            {"expense_id": expense_id},
            {"$set": {
                "status": "REJECTED",
                "rejection_reason": reason,
                "approved_by": rejected_by,  # Track who rejected
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            return_document=True
        )
        
        logger.info(f"Expense {expense_id} rejected: {reason}")
        return {k: v for k, v in result.items() if k != "_id"}
    
    async def mark_paid(
        self,
        expense_id: str,
        payment_mode: str,
        bank_account_id: Optional[str] = None,
        paid_by: str = None,
        de_service = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Mark expense as paid (APPROVED → PAID)
        Posts payment journal entry
        
        Returns: (expense, journal_entry_id)
        """
        expense = await self.get_expense(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        
        if expense["status"] != "APPROVED":
            raise ValueError(f"Cannot mark as paid expense in {expense['status']} status")
        
        journal_entry_id = None
        
        # Post payment journal entry
        if de_service:
            journal_entry_id = await self._post_payment_journal_entry(
                expense, payment_mode, bank_account_id, paid_by, de_service
            )
        
        updates = {
            "status": "PAID",
            "payment_mode": payment_mode,
            "bank_account_id": bank_account_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if journal_entry_id:
            updates["payment_journal_entry_id"] = journal_entry_id
        
        result = await self.expenses.find_one_and_update(
            {"expense_id": expense_id},
            {"$set": updates},
            return_document=True
        )
        
        logger.info(f"Expense {expense_id} marked as paid via {payment_mode}")
        return {k: v for k, v in result.items() if k != "_id"}, journal_entry_id
    
    async def _post_payment_journal_entry(
        self,
        expense: Dict[str, Any],
        payment_mode: str,
        bank_account_id: Optional[str],
        paid_by: str,
        de_service
    ) -> Optional[str]:
        """Post journal entry for expense payment"""
        try:
            org_id = expense["organization_id"]
            await de_service.ensure_system_accounts(org_id)
            
            payable_account = await de_service.get_account_by_code(org_id, "2100")
            
            # Get payment account (Bank or Cash)
            if payment_mode in ["BANK", "UPI", "CREDIT_CARD"]:
                payment_account = await de_service.get_account_by_code(org_id, "1200")  # Bank
            else:
                payment_account = await de_service.get_account_by_code(org_id, "1210")  # Cash
            
            if not payable_account or not payment_account:
                return None
            
            narration = f"Expense payment: {expense['expense_number']} | Mode: {payment_mode}"
            
            success, msg, entry = await de_service.create_journal_entry(
                organization_id=org_id,
                entry_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                description=narration,
                lines=[
                    {
                        "account_id": payable_account["account_id"],
                        "debit_amount": expense["total_amount"],
                        "credit_amount": 0,
                        "description": f"Payment for {expense['expense_number']}"
                    },
                    {
                        "account_id": payment_account["account_id"],
                        "debit_amount": 0,
                        "credit_amount": expense["total_amount"],
                        "description": f"Expense payment - {expense['vendor_name']}"
                    }
                ],
                entry_type="PAYMENT",
                source_document_id=expense["expense_id"],
                source_document_type="EXPENSE_PAYMENT",
                created_by=paid_by
            )
            
            if success:
                logger.info(f"Posted expense payment journal entry: {entry.get('entry_id')}")
                return entry.get("entry_id")
            else:
                logger.warning(f"Failed to post expense payment journal entry: {msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error posting expense payment journal entry: {e}")
            return None
    
    # ==================== REPORTING ====================
    
    async def get_summary(
        self,
        org_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get expense summary statistics"""
        query = {"organization_id": org_id}
        
        if date_from:
            query["expense_date"] = query.get("expense_date", {})
            query["expense_date"]["$gte"] = date_from
        if date_to:
            query["expense_date"] = query.get("expense_date", {})
            query["expense_date"]["$lte"] = date_to
        
        # Total by status
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total": {"$sum": "$total_amount"}
            }}
        ]
        
        status_results = await self.expenses.aggregate(pipeline).to_list(10)
        by_status = {r["_id"]: {"count": r["count"], "total": r["total"]} for r in status_results}
        
        # Total by category
        pipeline = [
            {"$match": {**query, "status": {"$in": ["APPROVED", "PAID"]}}},
            {"$group": {
                "_id": "$category_id",
                "total": {"$sum": "$total_amount"},
                "count": {"$sum": 1}
            }}
        ]
        
        category_results = await self.expenses.aggregate(pipeline).to_list(20)
        by_category = []
        for r in category_results:
            cat = await self.get_category(r["_id"]) if r["_id"] else None
            by_category.append({
                "category_id": r["_id"],
                "category_name": cat.get("name") if cat else "Unknown",
                "total": r["total"],
                "count": r["count"]
            })
        
        # ITC Summary
        itc_query = {**query, "is_itc_eligible": True, "status": {"$in": ["APPROVED", "PAID"]}}
        pipeline = [
            {"$match": itc_query},
            {"$group": {
                "_id": None,
                "total_cgst": {"$sum": "$cgst_amount"},
                "total_sgst": {"$sum": "$sgst_amount"},
                "total_igst": {"$sum": "$igst_amount"},
                "count": {"$sum": 1}
            }}
        ]
        
        itc_results = await self.expenses.aggregate(pipeline).to_list(1)
        itc_summary = itc_results[0] if itc_results else {
            "total_cgst": 0, "total_sgst": 0, "total_igst": 0, "count": 0
        }
        itc_summary.pop("_id", None)
        itc_summary["total_itc"] = itc_summary.get("total_cgst", 0) + itc_summary.get("total_sgst", 0) + itc_summary.get("total_igst", 0)
        
        # Monthly trend (last 6 months)
        from datetime import timedelta
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {**query, "expense_date": {"$gte": six_months_ago}, "status": {"$in": ["APPROVED", "PAID"]}}},
            {"$group": {
                "_id": {"$substr": ["$expense_date", 0, 7]},  # YYYY-MM
                "total": {"$sum": "$total_amount"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        monthly_results = await self.expenses.aggregate(pipeline).to_list(12)
        by_month = [{"month": r["_id"], "total": r["total"], "count": r["count"]} for r in monthly_results]
        
        return {
            "by_status": by_status,
            "by_category": sorted(by_category, key=lambda x: x["total"], reverse=True),
            "itc_summary": itc_summary,
            "by_month": by_month
        }


# ==================== SERVICE FACTORY ====================

_expenses_service: Optional[ExpensesService] = None


def get_expenses_service() -> ExpensesService:
    if _expenses_service is None:
        raise ValueError("ExpensesService not initialized")
    return _expenses_service


def init_expenses_service(db) -> ExpensesService:
    global _expenses_service
    _expenses_service = ExpensesService(db)
    logger.info("Expenses Service initialized")
    return _expenses_service
