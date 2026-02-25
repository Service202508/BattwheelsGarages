"""
Double-Entry Bookkeeping Service
================================
Implements proper double-entry accounting with:
- Journal entries with balanced debit/credit lines
- Auto-posting rules for invoices, payments, bills, expenses, payroll
- Trial balance generation
- Account-based P&L and Balance Sheet

Every journal entry MUST have:
    sum(debit_amount) = sum(credit_amount)

This is the CORE accounting engine for Battwheels OS.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)

# ========================= CONSTANTS =========================

CURRENCY_PRECISION = Decimal('0.01')

class EntryType(str, Enum):
    """Types of journal entries"""
    SALES = "SALES"
    PURCHASE = "PURCHASE"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"
    EXPENSE = "EXPENSE"
    JOURNAL = "JOURNAL"
    PAYROLL = "PAYROLL"
    DEPRECIATION = "DEPRECIATION"
    OPENING = "OPENING"
    ADJUSTMENT = "ADJUSTMENT"


class AccountType(str, Enum):
    """Account types for chart of accounts"""
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"


# Default system accounts (will be created if not exist)
SYSTEM_ACCOUNTS = {
    # Assets
    "ACCOUNTS_RECEIVABLE": {"name": "Accounts Receivable", "type": AccountType.ASSET, "code": "1100"},
    "BANK": {"name": "Bank Account", "type": AccountType.ASSET, "code": "1200"},
    "CASH": {"name": "Cash in Hand", "type": AccountType.ASSET, "code": "1210"},
    "INVENTORY": {"name": "Inventory", "type": AccountType.ASSET, "code": "1300"},
    "GST_INPUT_CGST": {"name": "GST Input Credit - CGST", "type": AccountType.ASSET, "code": "1410"},
    "GST_INPUT_SGST": {"name": "GST Input Credit - SGST", "type": AccountType.ASSET, "code": "1420"},
    "GST_INPUT_IGST": {"name": "GST Input Credit - IGST", "type": AccountType.ASSET, "code": "1430"},
    
    # Liabilities
    "ACCOUNTS_PAYABLE": {"name": "Accounts Payable", "type": AccountType.LIABILITY, "code": "2100"},
    "GST_PAYABLE_CGST": {"name": "GST Payable - CGST", "type": AccountType.LIABILITY, "code": "2210"},
    "GST_PAYABLE_SGST": {"name": "GST Payable - SGST", "type": AccountType.LIABILITY, "code": "2220"},
    "GST_PAYABLE_IGST": {"name": "GST Payable - IGST", "type": AccountType.LIABILITY, "code": "2230"},
    "SALARY_PAYABLE": {"name": "Salary Payable", "type": AccountType.LIABILITY, "code": "2310"},
    "TDS_PAYABLE": {"name": "TDS Payable", "type": AccountType.LIABILITY, "code": "2320"},
    "PF_EMPLOYEE_PAYABLE": {"name": "Employee PF Payable", "type": AccountType.LIABILITY, "code": "2330"},
    "PF_EMPLOYER_PAYABLE": {"name": "Employer PF Payable", "type": AccountType.LIABILITY, "code": "2331"},
    "ESI_PAYABLE": {"name": "ESI Payable", "type": AccountType.LIABILITY, "code": "2340"},
    "PROFESSIONAL_TAX_PAYABLE": {"name": "Professional Tax Payable", "type": AccountType.LIABILITY, "code": "2350"},
    
    # Equity
    "RETAINED_EARNINGS": {"name": "Retained Earnings", "type": AccountType.EQUITY, "code": "3100"},
    "OWNER_EQUITY": {"name": "Owner's Equity", "type": AccountType.EQUITY, "code": "3200"},
    
    # Income
    "SALES_REVENUE": {"name": "Sales Revenue", "type": AccountType.INCOME, "code": "4100"},
    "SERVICE_REVENUE": {"name": "Service Revenue", "type": AccountType.INCOME, "code": "4200"},
    "OTHER_INCOME": {"name": "Other Income", "type": AccountType.INCOME, "code": "4900"},
    
    # Expenses
    "PURCHASES": {"name": "Purchases", "type": AccountType.EXPENSE, "code": "5000"},
    "COST_OF_GOODS_SOLD": {"name": "Cost of Goods Sold", "type": AccountType.EXPENSE, "code": "5100"},
    "SALARY_EXPENSE": {"name": "Salary Expense", "type": AccountType.EXPENSE, "code": "6100"},
    "EMPLOYER_PF_EXPENSE": {"name": "Employer PF Contribution", "type": AccountType.EXPENSE, "code": "6110"},
    "EMPLOYER_ESI_EXPENSE": {"name": "Employer ESI Contribution", "type": AccountType.EXPENSE, "code": "6120"},
    "RENT_EXPENSE": {"name": "Rent Expense", "type": AccountType.EXPENSE, "code": "6200"},
    "UTILITIES_EXPENSE": {"name": "Utilities Expense", "type": AccountType.EXPENSE, "code": "6300"},
    "OFFICE_EXPENSE": {"name": "Office Supplies", "type": AccountType.EXPENSE, "code": "6400"},
    "PROFESSIONAL_FEES": {"name": "Professional Fees", "type": AccountType.EXPENSE, "code": "6500"},
    "DEPRECIATION_EXPENSE": {"name": "Depreciation Expense", "type": AccountType.EXPENSE, "code": "6600"},
    "TRAVEL_EXPENSE": {"name": "Travel & Conveyance", "type": AccountType.EXPENSE, "code": "6710"},
    "REPAIRS_EXPENSE": {"name": "Repairs & Maintenance", "type": AccountType.EXPENSE, "code": "6720"},
    "ADVERTISING_EXPENSE": {"name": "Advertising & Marketing", "type": AccountType.EXPENSE, "code": "6730"},
    "STAFF_WELFARE": {"name": "Staff Welfare", "type": AccountType.EXPENSE, "code": "6740"},
    "COMMUNICATION_EXPENSE": {"name": "Communication Expense", "type": AccountType.EXPENSE, "code": "6750"},
    "MISC_EXPENSE": {"name": "Miscellaneous Expense", "type": AccountType.EXPENSE, "code": "6900"},
    
    # Equity - Additional
    "OPENING_BALANCE_EQUITY": {"name": "Opening Balance Equity", "type": AccountType.EQUITY, "code": "3300"},
}


# ========================= DATA CLASSES =========================

@dataclass
class JournalEntryLine:
    """A single line in a journal entry"""
    line_id: str = field(default_factory=lambda: f"jel_{uuid.uuid4().hex[:12]}")
    account_id: str = ""
    account_name: str = ""
    account_code: str = ""
    account_type: str = ""
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_id": self.line_id,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "account_code": self.account_code,
            "account_type": self.account_type,
            "debit_amount": float(self.debit_amount),
            "credit_amount": float(self.credit_amount),
            "description": self.description
        }


@dataclass
class JournalEntry:
    """A complete journal entry with balanced lines"""
    entry_id: str = field(default_factory=lambda: f"je_{uuid.uuid4().hex[:12]}")
    entry_date: str = ""
    reference_number: str = ""
    description: str = ""
    organization_id: str = ""
    created_by: str = ""
    entry_type: EntryType = EntryType.JOURNAL
    source_document_id: str = ""
    source_document_type: str = ""
    is_posted: bool = True
    is_reversed: bool = False
    reversed_entry_id: str = ""
    lines: List[JournalEntryLine] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""
    
    def validate(self) -> Tuple[bool, str]:
        """Validate that debits equal credits"""
        total_debit = sum(line.debit_amount for line in self.lines)
        total_credit = sum(line.credit_amount for line in self.lines)
        
        if total_debit != total_credit:
            return False, f"Entry not balanced: Debit={total_debit}, Credit={total_credit}"
        
        if total_debit == 0:
            return False, "Entry has no amounts"
        
        if len(self.lines) < 2:
            return False, "Entry must have at least 2 lines"
        
        for line in self.lines:
            if line.debit_amount < 0 or line.credit_amount < 0:
                return False, "Negative amounts not allowed"
            if line.debit_amount > 0 and line.credit_amount > 0:
                return False, "Line cannot have both debit and credit"
            if line.debit_amount == 0 and line.credit_amount == 0:
                return False, "Line must have either debit or credit"
            if not line.account_id:
                return False, "All lines must have an account_id"
        
        return True, "Valid"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "entry_date": self.entry_date,
            "reference_number": self.reference_number,
            "description": self.description,
            "organization_id": self.organization_id,
            "created_by": self.created_by,
            "entry_type": self.entry_type.value if isinstance(self.entry_type, EntryType) else self.entry_type,
            "source_document_id": self.source_document_id,
            "source_document_type": self.source_document_type,
            "is_posted": self.is_posted,
            "is_reversed": self.is_reversed,
            "reversed_entry_id": self.reversed_entry_id,
            "lines": [line.to_dict() for line in self.lines],
            "total_debit": float(sum(line.debit_amount for line in self.lines)),
            "total_credit": float(sum(line.credit_amount for line in self.lines)),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


# ========================= HELPER FUNCTIONS =========================

def round_currency(amount: float | Decimal | int) -> Decimal:
    """Round to 2 decimal places"""
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    return amount.quantize(CURRENCY_PRECISION, rounding=ROUND_HALF_UP)


def generate_reference_number(prefix: str, sequence: int) -> str:
    """Generate sequential reference number"""
    return f"{prefix}-{datetime.now().strftime('%Y%m')}-{str(sequence).zfill(5)}"


# ========================= DOUBLE ENTRY SERVICE =========================

class DoubleEntryService:
    """
    Core double-entry bookkeeping service.
    
    Responsibilities:
    - Create and validate journal entries
    - Auto-post entries for invoices, payments, bills, expenses
    - Generate trial balance
    - Provide account balances for P&L and Balance Sheet
    """
    
    def __init__(self, db):
        self.db = db
        self.journal_entries = db.journal_entries
        self.chart_of_accounts = db.chart_of_accounts
        self._account_cache: Dict[str, Dict] = {}
    
    # ==================== ACCOUNT MANAGEMENT ====================
    
    async def ensure_system_accounts(self, organization_id: str) -> None:
        """Ensure all system accounts exist for an organization"""
        for key, account_def in SYSTEM_ACCOUNTS.items():
            existing = await self.chart_of_accounts.find_one({
                "organization_id": organization_id,
                "account_code": account_def["code"]
            })
            
            if not existing:
                account = {
                    "account_id": f"acc_{uuid.uuid4().hex[:12]}",
                    "account_name": account_def["name"],
                    "account_code": account_def["code"],
                    "account_type": account_def["type"].value,
                    "description": f"System account: {account_def['name']}",
                    "is_system": True,
                    "is_active": True,
                    "parent_account_id": None,
                    "organization_id": organization_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await self.chart_of_accounts.insert_one(account)
                logger.info(f"Created system account: {account_def['name']} for org {organization_id}")
    
    async def get_account_by_code(self, organization_id: str, code: str) -> Optional[Dict]:
        """Get account by code with caching"""
        cache_key = f"{organization_id}:{code}"
        if cache_key in self._account_cache:
            return self._account_cache[cache_key]
        
        account = await self.chart_of_accounts.find_one({
            "organization_id": organization_id,
            "account_code": code,
            "is_active": True
        }, {"_id": 0})
        
        if account:
            self._account_cache[cache_key] = account
        
        return account
    
    async def get_account_by_id(self, organization_id: str, account_id: str) -> Optional[Dict]:
        """Get account by ID"""
        return await self.chart_of_accounts.find_one({
            "organization_id": organization_id,
            "account_id": account_id,
            "is_active": True
        }, {"_id": 0})
    
    async def get_account_by_name(self, organization_id: str, name: str) -> Optional[Dict]:
        """Get account by name (case-insensitive)"""
        return await self.chart_of_accounts.find_one({
            "organization_id": organization_id,
            "account_name": {"$regex": f"^{name}$", "$options": "i"},
            "is_active": True
        }, {"_id": 0})
    
    async def get_or_create_account(
        self, 
        organization_id: str, 
        name: str, 
        account_type: AccountType,
        code: str = None
    ) -> Dict:
        """Get existing account or create new one"""
        # Try by name first
        account = await self.get_account_by_name(organization_id, name)
        if account:
            return account
        
        # Create new account
        if not code:
            # Generate code based on type
            type_prefix = {
                AccountType.ASSET: "1",
                AccountType.LIABILITY: "2",
                AccountType.EQUITY: "3",
                AccountType.INCOME: "4",
                AccountType.EXPENSE: "6"
            }
            prefix = type_prefix.get(account_type, "9")
            count = await self.chart_of_accounts.count_documents({
                "organization_id": organization_id,
                "account_type": account_type.value
            })
            code = f"{prefix}{str(count + 100).zfill(3)}"
        
        account = {
            "account_id": f"acc_{uuid.uuid4().hex[:12]}",
            "account_name": name,
            "account_code": code,
            "account_type": account_type.value,
            "description": "",
            "is_system": False,
            "is_active": True,
            "parent_account_id": None,
            "organization_id": organization_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.chart_of_accounts.insert_one(account)
        return account
    
    # ==================== JOURNAL ENTRY CREATION ====================
    
    async def get_next_reference_number(self, organization_id: str, entry_type: EntryType) -> str:
        """Generate next sequential reference number"""
        prefix_map = {
            EntryType.SALES: "JE-SLS",
            EntryType.PURCHASE: "JE-PUR",
            EntryType.PAYMENT: "JE-PAY",
            EntryType.RECEIPT: "JE-RCP",
            EntryType.EXPENSE: "JE-EXP",
            EntryType.JOURNAL: "JE-GEN",
            EntryType.PAYROLL: "JE-PAY",
            EntryType.DEPRECIATION: "JE-DEP",
            EntryType.OPENING: "JE-OPN",
            EntryType.ADJUSTMENT: "JE-ADJ"
        }
        prefix = prefix_map.get(entry_type, "JE")
        
        # Count existing entries for this month
        month_start = datetime.now().strftime("%Y-%m-01")
        count = await self.journal_entries.count_documents({
            "organization_id": organization_id,
            "entry_date": {"$gte": month_start}
        })
        
        return generate_reference_number(prefix, count + 1)
    
    async def create_journal_entry(
        self,
        organization_id: str,
        entry_date: str,
        description: str,
        lines: List[Dict],
        entry_type: EntryType = EntryType.JOURNAL,
        source_document_id: str = "",
        source_document_type: str = "",
        created_by: str = "",
        is_posted: bool = True
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new journal entry.
        
        Args:
            organization_id: Tenant ID
            entry_date: Date of entry (YYYY-MM-DD)
            description: Entry description
            lines: List of dicts with account_id, debit_amount, credit_amount, description
            entry_type: Type of entry
            source_document_id: Related document ID
            source_document_type: Type of source document (invoice, bill, etc.)
            created_by: User ID who created this
            is_posted: Whether to post immediately
        
        Returns:
            Tuple of (success, message, entry_dict)
        """
        # Ensure system accounts exist
        await self.ensure_system_accounts(organization_id)
        
        # IDEMPOTENCY CHECK: Prevent duplicate journal entries for the same source document
        if source_document_id:
            existing = await self.journal_entries.find_one({
                "organization_id": organization_id,
                "source_document_id": source_document_id,
                "source_document_type": source_document_type,
                "is_reversed": False
            }, {"_id": 0})
            if existing:
                logger.info(
                    f"Idempotency guard: journal entry already exists for "
                    f"{source_document_type} {source_document_id} in org {organization_id}"
                )
                return True, "Journal entry already exists (idempotent)", existing
        
        # Build entry lines with account details
        entry_lines = []
        for line_data in lines:
            account = await self.get_account_by_id(organization_id, line_data["account_id"])
            if not account:
                # Try by code
                account = await self.get_account_by_code(organization_id, line_data.get("account_code", ""))
            if not account:
                return False, f"Account not found: {line_data.get('account_id', line_data.get('account_code', ''))}", None
            
            line = JournalEntryLine(
                account_id=account["account_id"],
                account_name=account["account_name"],
                account_code=account["account_code"],
                account_type=account["account_type"],
                debit_amount=round_currency(line_data.get("debit_amount", 0)),
                credit_amount=round_currency(line_data.get("credit_amount", 0)),
                description=line_data.get("description", "")
            )
            entry_lines.append(line)
        
        # Create entry
        reference_number = await self.get_next_reference_number(organization_id, entry_type)
        
        entry = JournalEntry(
            entry_date=entry_date,
            reference_number=reference_number,
            description=description,
            organization_id=organization_id,
            created_by=created_by,
            entry_type=entry_type,
            source_document_id=source_document_id,
            source_document_type=source_document_type,
            is_posted=is_posted,
            lines=entry_lines
        )
        
        # Validate
        is_valid, validation_msg = entry.validate()
        if not is_valid:
            return False, validation_msg, None
        
        # Save to database
        entry_dict = entry.to_dict()
        await self.journal_entries.insert_one(entry_dict)
        
        # Remove MongoDB _id from response
        entry_dict.pop("_id", None)
        
        logger.info(f"Created journal entry {reference_number} for org {organization_id}")
        
        return True, "Journal entry created successfully", entry_dict
    
    async def reverse_journal_entry(
        self,
        organization_id: str,
        entry_id: str,
        reversal_date: str,
        created_by: str = "",
        reason: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Create a reversal entry for an existing journal entry"""
        # Get original entry
        original = await self.journal_entries.find_one({
            "entry_id": entry_id,
            "organization_id": organization_id,
            "is_posted": True,
            "is_reversed": False
        }, {"_id": 0})
        
        if not original:
            return False, "Entry not found or already reversed", None
        
        # Create reversal lines (swap debits and credits)
        reversal_lines = []
        for line in original["lines"]:
            reversal_lines.append({
                "account_id": line["account_id"],
                "debit_amount": line["credit_amount"],
                "credit_amount": line["debit_amount"],
                "description": f"Reversal: {line.get('description', '')}"
            })
        
        # Create reversal entry
        success, msg, reversal_entry = await self.create_journal_entry(
            organization_id=organization_id,
            entry_date=reversal_date,
            description=f"Reversal of {original['reference_number']}: {reason}",
            lines=reversal_lines,
            entry_type=EntryType(original["entry_type"]),
            source_document_id=original.get("source_document_id", ""),
            source_document_type=original.get("source_document_type", ""),
            created_by=created_by
        )
        
        if success:
            # Mark original as reversed
            await self.journal_entries.update_one(
                {"entry_id": entry_id},
                {"$set": {
                    "is_reversed": True,
                    "reversed_entry_id": reversal_entry["entry_id"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return success, msg, reversal_entry
    
    # ==================== AUTO-POSTING RULES ====================
    
    async def post_sales_invoice(
        self,
        organization_id: str,
        invoice: Dict,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Auto-post journal entry for a sales invoice.
        
        DEBIT:  Accounts Receivable (total amount)
        CREDIT: Sales Revenue (base amount)
        CREDIT: GST Payable - CGST (if intra-state)
        CREDIT: GST Payable - SGST (if intra-state)
        CREDIT: GST Payable - IGST (if inter-state)
        """
        await self.ensure_system_accounts(organization_id)
        
        # Get accounts
        ar_account = await self.get_account_by_code(organization_id, "1100")  # Accounts Receivable
        sales_account = await self.get_account_by_code(organization_id, "4100")  # Sales Revenue
        cgst_account = await self.get_account_by_code(organization_id, "2210")  # GST Payable CGST
        sgst_account = await self.get_account_by_code(organization_id, "2220")  # GST Payable SGST
        igst_account = await self.get_account_by_code(organization_id, "2230")  # GST Payable IGST
        
        if not all([ar_account, sales_account]):
            return False, "Required accounts not found", None
        
        # Calculate amounts
        sub_total = Decimal(str(invoice.get("sub_total", 0) or invoice.get("subtotal", 0) or 0))
        cgst = Decimal(str(invoice.get("cgst_amount", 0) or 0))
        sgst = Decimal(str(invoice.get("sgst_amount", 0) or 0))
        igst = Decimal(str(invoice.get("igst_amount", 0) or 0))
        total = Decimal(str(invoice.get("total", 0) or 0))
        
        # If tax fields not available, try to calculate from tax_total
        if cgst == 0 and sgst == 0 and igst == 0:
            tax_total = Decimal(str(invoice.get("tax_total", 0) or 0))
            # Default to intra-state (CGST/SGST split)
            cgst = round_currency(tax_total / 2)
            sgst = tax_total - cgst
        
        # If total not available, calculate it
        if total == 0:
            total = sub_total + cgst + sgst + igst
        
        # Build journal lines
        lines = []
        
        # DEBIT: Accounts Receivable
        lines.append({
            "account_id": ar_account["account_id"],
            "debit_amount": float(total),
            "credit_amount": 0,
            "description": f"Invoice {invoice.get('invoice_number', '')} - {invoice.get('customer_name', '')}"
        })
        
        # CREDIT: Sales Revenue
        lines.append({
            "account_id": sales_account["account_id"],
            "debit_amount": 0,
            "credit_amount": float(sub_total),
            "description": f"Sales - Invoice {invoice.get('invoice_number', '')}"
        })
        
        # CREDIT: GST Payable
        if cgst > 0 and cgst_account:
            lines.append({
                "account_id": cgst_account["account_id"],
                "debit_amount": 0,
                "credit_amount": float(cgst),
                "description": f"CGST on Invoice {invoice.get('invoice_number', '')}"
            })
        
        if sgst > 0 and sgst_account:
            lines.append({
                "account_id": sgst_account["account_id"],
                "debit_amount": 0,
                "credit_amount": float(sgst),
                "description": f"SGST on Invoice {invoice.get('invoice_number', '')}"
            })
        
        if igst > 0 and igst_account:
            lines.append({
                "account_id": igst_account["account_id"],
                "debit_amount": 0,
                "credit_amount": float(igst),
                "description": f"IGST on Invoice {invoice.get('invoice_number', '')}"
            })
        
        invoice_date = invoice.get("date", invoice.get("invoice_date", datetime.now().strftime("%Y-%m-%d")))
        
        return await self.create_journal_entry(
            organization_id=organization_id,
            entry_date=invoice_date,
            description=f"Sales Invoice {invoice.get('invoice_number', '')} - {invoice.get('customer_name', '')}",
            lines=lines,
            entry_type=EntryType.SALES,
            source_document_id=invoice.get("invoice_id", ""),
            source_document_type="invoice",
            created_by=created_by
        )
    
    async def post_payment_received(
        self,
        organization_id: str,
        payment: Dict,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Auto-post journal entry for payment received.
        
        DEBIT:  Bank / Cash account
        CREDIT: Accounts Receivable
        """
        await self.ensure_system_accounts(organization_id)
        
        # Determine which account to debit based on payment mode
        payment_mode = payment.get("payment_mode", "bank").lower()
        if payment_mode in ["cash"]:
            bank_account = await self.get_account_by_code(organization_id, "1210")  # Cash
        else:
            bank_account = await self.get_account_by_code(organization_id, "1200")  # Bank
        
        ar_account = await self.get_account_by_code(organization_id, "1100")  # Accounts Receivable
        
        if not all([bank_account, ar_account]):
            return False, "Required accounts not found", None
        
        amount = Decimal(str(payment.get("amount", 0)))
        
        lines = [
            {
                "account_id": bank_account["account_id"],
                "debit_amount": float(amount),
                "credit_amount": 0,
                "description": f"Payment received - {payment.get('reference_number', '')}"
            },
            {
                "account_id": ar_account["account_id"],
                "debit_amount": 0,
                "credit_amount": float(amount),
                "description": f"Payment for Invoice {payment.get('invoice_number', payment.get('invoice_id', ''))}"
            }
        ]
        
        payment_date = payment.get("payment_date", payment.get("date", datetime.now().strftime("%Y-%m-%d")))
        
        return await self.create_journal_entry(
            organization_id=organization_id,
            entry_date=payment_date,
            description=f"Payment Received - {payment.get('customer_name', '')} - {payment.get('reference_number', '')}",
            lines=lines,
            entry_type=EntryType.RECEIPT,
            source_document_id=payment.get("payment_id", ""),
            source_document_type="payment_received",
            created_by=created_by
        )
    
    async def post_purchase_bill(
        self,
        organization_id: str,
        bill: Dict,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Auto-post journal entry for purchase bill.
        
        DEBIT:  Expense / COGS account
        DEBIT:  GST Input Credit - CGST/SGST/IGST
        CREDIT: Accounts Payable
        """
        await self.ensure_system_accounts(organization_id)
        
        # Get accounts
        ap_account = await self.get_account_by_code(organization_id, "2100")  # Accounts Payable
        expense_account = await self.get_account_by_code(organization_id, "5100")  # COGS (default)
        cgst_input = await self.get_account_by_code(organization_id, "1410")  # GST Input CGST
        sgst_input = await self.get_account_by_code(organization_id, "1420")  # GST Input SGST
        igst_input = await self.get_account_by_code(organization_id, "1430")  # GST Input IGST
        
        # Try to get specific expense account from bill
        if bill.get("expense_account"):
            specific_account = await self.get_account_by_name(organization_id, bill["expense_account"])
            if specific_account:
                expense_account = specific_account
        
        if not all([ap_account, expense_account]):
            return False, "Required accounts not found", None
        
        # Calculate amounts
        sub_total = Decimal(str(bill.get("sub_total", 0) or bill.get("subtotal", 0) or 0))
        cgst = Decimal(str(bill.get("cgst_amount", 0) or 0))
        sgst = Decimal(str(bill.get("sgst_amount", 0) or 0))
        igst = Decimal(str(bill.get("igst_amount", 0) or 0))
        total = Decimal(str(bill.get("total", 0) or 0))
        
        # If tax fields not available, calculate
        if cgst == 0 and sgst == 0 and igst == 0:
            tax_total = Decimal(str(bill.get("tax_total", 0) or 0))
            cgst = round_currency(tax_total / 2)
            sgst = tax_total - cgst
        
        if total == 0:
            total = sub_total + cgst + sgst + igst
        
        lines = []
        
        # DEBIT: Expense account
        lines.append({
            "account_id": expense_account["account_id"],
            "debit_amount": float(sub_total),
            "credit_amount": 0,
            "description": f"Bill {bill.get('bill_number', '')} - {bill.get('vendor_name', '')}"
        })
        
        # DEBIT: GST Input Credit
        if cgst > 0 and cgst_input:
            lines.append({
                "account_id": cgst_input["account_id"],
                "debit_amount": float(cgst),
                "credit_amount": 0,
                "description": f"CGST Input on Bill {bill.get('bill_number', '')}"
            })
        
        if sgst > 0 and sgst_input:
            lines.append({
                "account_id": sgst_input["account_id"],
                "debit_amount": float(sgst),
                "credit_amount": 0,
                "description": f"SGST Input on Bill {bill.get('bill_number', '')}"
            })
        
        if igst > 0 and igst_input:
            lines.append({
                "account_id": igst_input["account_id"],
                "debit_amount": float(igst),
                "credit_amount": 0,
                "description": f"IGST Input on Bill {bill.get('bill_number', '')}"
            })
        
        # CREDIT: Accounts Payable
        lines.append({
            "account_id": ap_account["account_id"],
            "debit_amount": 0,
            "credit_amount": float(total),
            "description": f"Bill {bill.get('bill_number', '')} - {bill.get('vendor_name', '')}"
        })
        
        bill_date = bill.get("date", bill.get("bill_date", datetime.now().strftime("%Y-%m-%d")))
        
        return await self.create_journal_entry(
            organization_id=organization_id,
            entry_date=bill_date,
            description=f"Purchase Bill {bill.get('bill_number', '')} - {bill.get('vendor_name', '')}",
            lines=lines,
            entry_type=EntryType.PURCHASE,
            source_document_id=bill.get("bill_id", ""),
            source_document_type="bill",
            created_by=created_by
        )
    
    async def post_bill_payment(
        self,
        organization_id: str,
        payment: Dict,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Auto-post journal entry for bill payment.
        
        DEBIT:  Accounts Payable
        CREDIT: Bank / Cash account
        """
        await self.ensure_system_accounts(organization_id)
        
        ap_account = await self.get_account_by_code(organization_id, "2100")  # Accounts Payable
        
        payment_mode = payment.get("payment_mode", "bank").lower()
        if payment_mode in ["cash"]:
            bank_account = await self.get_account_by_code(organization_id, "1210")  # Cash
        else:
            bank_account = await self.get_account_by_code(organization_id, "1200")  # Bank
        
        if not all([ap_account, bank_account]):
            return False, "Required accounts not found", None
        
        amount = Decimal(str(payment.get("amount", 0)))
        
        lines = [
            {
                "account_id": ap_account["account_id"],
                "debit_amount": float(amount),
                "credit_amount": 0,
                "description": f"Payment for Bill {payment.get('bill_number', payment.get('bill_id', ''))}"
            },
            {
                "account_id": bank_account["account_id"],
                "debit_amount": 0,
                "credit_amount": float(amount),
                "description": f"Bill Payment - {payment.get('reference_number', '')}"
            }
        ]
        
        payment_date = payment.get("payment_date", payment.get("date", datetime.now().strftime("%Y-%m-%d")))
        
        return await self.create_journal_entry(
            organization_id=organization_id,
            entry_date=payment_date,
            description=f"Bill Payment - {payment.get('vendor_name', '')} - {payment.get('reference_number', '')}",
            lines=lines,
            entry_type=EntryType.PAYMENT,
            source_document_id=payment.get("payment_id", ""),
            source_document_type="bill_payment",
            created_by=created_by
        )
    
    async def post_expense(
        self,
        organization_id: str,
        expense: Dict,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Auto-post journal entry for expense.
        
        DEBIT:  Expense account
        CREDIT: Bank / Cash / Accounts Payable
        """
        await self.ensure_system_accounts(organization_id)
        
        # Get expense account
        expense_account_name = expense.get("expense_account", "Miscellaneous Expense")
        expense_account = await self.get_or_create_account(
            organization_id, 
            expense_account_name, 
            AccountType.EXPENSE
        )
        
        # Determine credit account
        paid_through = expense.get("paid_through", "bank").lower()
        if paid_through == "cash":
            credit_account = await self.get_account_by_code(organization_id, "1210")  # Cash
        elif paid_through in ["accounts payable", "payable", "credit"]:
            credit_account = await self.get_account_by_code(organization_id, "2100")  # AP
        else:
            credit_account = await self.get_account_by_code(organization_id, "1200")  # Bank
        
        if not all([expense_account, credit_account]):
            return False, "Required accounts not found", None
        
        amount = Decimal(str(expense.get("amount", 0)))
        
        lines = [
            {
                "account_id": expense_account["account_id"],
                "debit_amount": float(amount),
                "credit_amount": 0,
                "description": expense.get("description", "")
            },
            {
                "account_id": credit_account["account_id"],
                "debit_amount": 0,
                "credit_amount": float(amount),
                "description": f"Expense - {expense.get('reference_number', '')}"
            }
        ]
        
        expense_date = expense.get("expense_date", expense.get("date", datetime.now().strftime("%Y-%m-%d")))
        if isinstance(expense_date, datetime):
            expense_date = expense_date.strftime("%Y-%m-%d")
        
        return await self.create_journal_entry(
            organization_id=organization_id,
            entry_date=expense_date,
            description=f"Expense: {expense.get('description', expense_account_name)}",
            lines=lines,
            entry_type=EntryType.EXPENSE,
            source_document_id=expense.get("expense_id", ""),
            source_document_type="expense",
            created_by=created_by
        )
    
    async def post_payroll(
        self,
        organization_id: str,
        payroll: Dict,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Auto-post journal entry for individual payroll record (legacy support).
        For batch payroll processing, use post_payroll_run() instead.
        """
        return await self.post_payroll_run(organization_id, [payroll], created_by)
    
    async def post_payroll_run(
        self,
        organization_id: str,
        payroll_records: list,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Auto-post journal entry for payroll run (batch of all employees).
        
        DEBIT:  Salary Expense (total gross salaries)
        DEBIT:  Employer PF Contribution (employer PF)
        DEBIT:  Employer ESI Contribution (employer ESI)
        CREDIT: Salary Payable (total net take-home)
        CREDIT: TDS Payable (total TDS deducted)
        CREDIT: Employee PF Payable (total employee PF)
        CREDIT: Employer PF Payable (total employer PF)
        CREDIT: ESI Payable (total ESI - employee + employer)
        CREDIT: Professional Tax Payable (total PT)
        """
        await self.ensure_system_accounts(organization_id)
        
        # Get accounts
        salary_expense = await self.get_account_by_code(organization_id, "6100")
        employer_pf_expense = await self.get_account_by_code(organization_id, "6110")
        employer_esi_expense = await self.get_account_by_code(organization_id, "6120")
        salary_payable = await self.get_account_by_code(organization_id, "2310")
        tds_payable = await self.get_account_by_code(organization_id, "2320")
        employee_pf_payable = await self.get_account_by_code(organization_id, "2330")
        employer_pf_payable = await self.get_account_by_code(organization_id, "2331")
        esi_payable = await self.get_account_by_code(organization_id, "2340")
        pt_payable = await self.get_account_by_code(organization_id, "2350")
        
        if not all([salary_expense, salary_payable]):
            return False, "Required salary accounts not found", None
        
        # If employer accounts don't exist yet, create them
        if not employer_pf_expense:
            employer_pf_expense = await self.get_or_create_account(
                organization_id, "Employer PF Contribution", AccountType.EXPENSE, "6110"
            )
        if not employer_esi_expense:
            employer_esi_expense = await self.get_or_create_account(
                organization_id, "Employer ESI Contribution", AccountType.EXPENSE, "6120"
            )
        if not employee_pf_payable:
            employee_pf_payable = await self.get_or_create_account(
                organization_id, "Employee PF Payable", AccountType.LIABILITY, "2330"
            )
        if not employer_pf_payable:
            employer_pf_payable = await self.get_or_create_account(
                organization_id, "Employer PF Payable", AccountType.LIABILITY, "2331"
            )
        if not pt_payable:
            pt_payable = await self.get_or_create_account(
                organization_id, "Professional Tax Payable", AccountType.LIABILITY, "2350"
            )
        
        # Aggregate totals from all payroll records
        total_gross = Decimal("0")
        total_net = Decimal("0")
        total_tds = Decimal("0")
        total_employee_pf = Decimal("0")
        total_employer_pf = Decimal("0")
        total_employee_esi = Decimal("0")
        total_employer_esi = Decimal("0")
        total_pt = Decimal("0")
        employee_count = len(payroll_records)
        
        month = ""
        year = ""
        payroll_run_id = ""
        
        for record in payroll_records:
            # Handle both flat and nested structure
            earnings = record.get("earnings", {})
            deductions = record.get("deductions", {})
            employer_contrib = record.get("employer_contributions", {})
            
            gross = Decimal(str(
                earnings.get("gross", 0) or 
                record.get("gross_salary", 0) or 
                record.get("gross", 0) or 0
            ))
            net = Decimal(str(
                record.get("net_salary", 0) or 0
            ))
            tds = Decimal(str(
                deductions.get("tds", 0) or 
                record.get("tds", 0) or 0
            ))
            employee_pf = Decimal(str(
                deductions.get("pf_employee", 0) or 
                record.get("pf_employee", 0) or 0
            ))
            employee_esi = Decimal(str(
                deductions.get("esi_employee", 0) or 
                record.get("esi_employee", 0) or 0
            ))
            pt = Decimal(str(
                deductions.get("professional_tax", 0) or 
                record.get("professional_tax", 0) or 0
            ))
            employer_pf = Decimal(str(
                employer_contrib.get("pf_employer", 0) or 
                record.get("pf_employer", 0) or 0
            ))
            employer_esi = Decimal(str(
                employer_contrib.get("esi_employer", 0) or 
                record.get("esi_employer", 0) or 0
            ))
            
            total_gross += gross
            total_net += net
            total_tds += tds
            total_employee_pf += employee_pf
            total_employer_pf += employer_pf
            total_employee_esi += employee_esi
            total_employer_esi += employer_esi
            total_pt += pt
            
            # Get month/year from first record
            if not month:
                month = record.get("month", "")
                year = str(record.get("year", ""))
                payroll_run_id = record.get("payroll_id", "")
        
        total_esi = total_employee_esi + total_employer_esi
        
        lines = []
        
        # DEBIT: Salary Expense (gross salary)
        if total_gross > 0:
            lines.append({
                "account_id": salary_expense["account_id"],
                "debit_amount": float(total_gross),
                "credit_amount": 0,
                "description": f"Gross salary expense {month} {year}"
            })
        
        # DEBIT: Employer PF Contribution
        if total_employer_pf > 0 and employer_pf_expense:
            lines.append({
                "account_id": employer_pf_expense["account_id"],
                "debit_amount": float(total_employer_pf),
                "credit_amount": 0,
                "description": f"Employer PF contribution {month} {year}"
            })
        
        # DEBIT: Employer ESI Contribution
        if total_employer_esi > 0 and employer_esi_expense:
            lines.append({
                "account_id": employer_esi_expense["account_id"],
                "debit_amount": float(total_employer_esi),
                "credit_amount": 0,
                "description": f"Employer ESI contribution {month} {year}"
            })
        
        # CREDIT: Salary Payable (net take-home)
        if total_net > 0:
            lines.append({
                "account_id": salary_payable["account_id"],
                "debit_amount": 0,
                "credit_amount": float(total_net),
                "description": f"Net salary payable {month} {year}"
            })
        
        # CREDIT: TDS Payable
        if total_tds > 0 and tds_payable:
            lines.append({
                "account_id": tds_payable["account_id"],
                "debit_amount": 0,
                "credit_amount": float(total_tds),
                "description": f"TDS deducted {month} {year}"
            })
        
        # CREDIT: Employee PF Payable
        if total_employee_pf > 0 and employee_pf_payable:
            lines.append({
                "account_id": employee_pf_payable["account_id"],
                "debit_amount": 0,
                "credit_amount": float(total_employee_pf),
                "description": f"Employee PF deduction {month} {year}"
            })
        
        # CREDIT: Employer PF Payable
        if total_employer_pf > 0 and employer_pf_payable:
            lines.append({
                "account_id": employer_pf_payable["account_id"],
                "debit_amount": 0,
                "credit_amount": float(total_employer_pf),
                "description": f"Employer PF contribution {month} {year}"
            })
        
        # CREDIT: ESI Payable (employee + employer)
        if total_esi > 0 and esi_payable:
            lines.append({
                "account_id": esi_payable["account_id"],
                "debit_amount": 0,
                "credit_amount": float(total_esi),
                "description": f"ESI payable (employee + employer) {month} {year}"
            })
        
        # CREDIT: Professional Tax Payable
        if total_pt > 0 and pt_payable:
            lines.append({
                "account_id": pt_payable["account_id"],
                "debit_amount": 0,
                "credit_amount": float(total_pt),
                "description": f"Professional tax {month} {year}"
            })
        
        if not lines:
            return False, "No payroll amounts to post", None
        
        narration = (
            f"Payroll {month} {year} — {employee_count} employees | "
            f"Gross: ₹{total_gross:,.2f} | Net: ₹{total_net:,.2f} | TDS: ₹{total_tds:,.2f}"
        )
        
        return await self.create_journal_entry(
            organization_id=organization_id,
            entry_date=datetime.now().strftime("%Y-%m-%d"),
            description=narration,
            lines=lines,
            entry_type=EntryType.PAYROLL,
            source_document_id=payroll_run_id,
            source_document_type="PAYROLL_RUN",
            created_by=created_by
        )
    
    # ==================== REPORTING ====================
    
    async def get_trial_balance(
        self,
        organization_id: str,
        as_of_date: str = None
    ) -> Dict:
        """
        Generate Trial Balance from journal entries.
        
        Returns account-wise totals with debit and credit balances.
        Total debits must equal total credits.
        """
        if not as_of_date:
            as_of_date = datetime.now().strftime("%Y-%m-%d")
        
        # Aggregate all journal entry lines up to as_of_date
        pipeline = [
            {
                "$match": {
                    "organization_id": organization_id,
                    "is_posted": True,
                    "entry_date": {"$lte": as_of_date}
                }
            },
            {"$unwind": "$lines"},
            {
                "$group": {
                    "_id": {
                        "account_id": "$lines.account_id",
                        "account_name": "$lines.account_name",
                        "account_code": "$lines.account_code",
                        "account_type": "$lines.account_type"
                    },
                    "total_debit": {"$sum": "$lines.debit_amount"},
                    "total_credit": {"$sum": "$lines.credit_amount"}
                }
            },
            {"$sort": {"_id.account_code": 1}}
        ]
        
        results = await self.journal_entries.aggregate(pipeline).to_list(1000)
        
        accounts = []
        grand_total_debit = Decimal("0")
        grand_total_credit = Decimal("0")
        
        for row in results:
            debit = Decimal(str(row["total_debit"]))
            credit = Decimal(str(row["total_credit"]))
            net_balance = debit - credit
            
            # Determine debit/credit balance based on net balance direction.
            # Rule: if net (DR-CR) > 0 → show in Debit column; if < 0 → show in Credit column.
            # This applies uniformly to all account types to prevent double-counting.
            account_type = row["_id"]["account_type"]
            debit_balance = net_balance if net_balance > 0 else Decimal("0")
            credit_balance = abs(net_balance) if net_balance < 0 else Decimal("0")
            
            grand_total_debit += debit_balance
            grand_total_credit += credit_balance
            
            accounts.append({
                "account_id": row["_id"]["account_id"],
                "account_name": row["_id"]["account_name"],
                "account_code": row["_id"]["account_code"],
                "account_type": account_type,
                "total_debit": float(debit),
                "total_credit": float(credit),
                "debit_balance": float(debit_balance),
                "credit_balance": float(credit_balance),
                "net_balance": float(net_balance)
            })
        
        is_balanced = grand_total_debit == grand_total_credit
        
        return {
            "as_of_date": as_of_date,
            "accounts": accounts,
            "totals": {
                "total_debit": float(grand_total_debit),
                "total_credit": float(grand_total_credit),
                "is_balanced": is_balanced,
                "difference": float(grand_total_debit - grand_total_credit)
            },
            "status": "BALANCED" if is_balanced else "ERROR - UNBALANCED"
        }
    
    async def get_account_balance(
        self,
        organization_id: str,
        account_id: str,
        as_of_date: str = None,
        start_date: str = None
    ) -> Dict:
        """Get balance for a specific account"""
        if not as_of_date:
            as_of_date = datetime.now().strftime("%Y-%m-%d")
        
        match_query = {
            "organization_id": organization_id,
            "is_posted": True,
            "entry_date": {"$lte": as_of_date},
            "lines.account_id": account_id
        }
        
        if start_date:
            match_query["entry_date"]["$gte"] = start_date
        
        pipeline = [
            {"$match": match_query},
            {"$unwind": "$lines"},
            {"$match": {"lines.account_id": account_id}},
            {
                "$group": {
                    "_id": None,
                    "total_debit": {"$sum": "$lines.debit_amount"},
                    "total_credit": {"$sum": "$lines.credit_amount"}
                }
            }
        ]
        
        result = await self.journal_entries.aggregate(pipeline).to_list(1)
        
        if result:
            debit = result[0]["total_debit"]
            credit = result[0]["total_credit"]
            return {
                "account_id": account_id,
                "total_debit": debit,
                "total_credit": credit,
                "net_balance": debit - credit
            }
        
        return {
            "account_id": account_id,
            "total_debit": 0,
            "total_credit": 0,
            "net_balance": 0
        }
    
    async def get_profit_and_loss(
        self,
        organization_id: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Generate Profit & Loss from journal entries.
        
        Income accounts minus Expense accounts for the period.
        """
        # Aggregate income and expense accounts
        pipeline = [
            {
                "$match": {
                    "organization_id": organization_id,
                    "is_posted": True,
                    "entry_date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {"$unwind": "$lines"},
            {
                "$match": {
                    "lines.account_type": {"$in": [AccountType.INCOME.value, AccountType.EXPENSE.value]}
                }
            },
            {
                "$group": {
                    "_id": {
                        "account_id": "$lines.account_id",
                        "account_name": "$lines.account_name",
                        "account_code": "$lines.account_code",
                        "account_type": "$lines.account_type"
                    },
                    "total_debit": {"$sum": "$lines.debit_amount"},
                    "total_credit": {"$sum": "$lines.credit_amount"}
                }
            },
            {"$sort": {"_id.account_code": 1}}
        ]
        
        results = await self.journal_entries.aggregate(pipeline).to_list(1000)
        
        income_accounts = []
        expense_accounts = []
        total_income = Decimal("0")
        total_expenses = Decimal("0")
        
        for row in results:
            debit = Decimal(str(row["total_debit"]))
            credit = Decimal(str(row["total_credit"]))
            account_type = row["_id"]["account_type"]
            
            account_data = {
                "account_id": row["_id"]["account_id"],
                "account_name": row["_id"]["account_name"],
                "account_code": row["_id"]["account_code"],
                "total_debit": float(debit),
                "total_credit": float(credit)
            }
            
            if account_type == AccountType.INCOME.value:
                # Income accounts have credit balance
                balance = credit - debit
                account_data["balance"] = float(balance)
                income_accounts.append(account_data)
                total_income += balance
            else:
                # Expense accounts have debit balance
                balance = debit - credit
                account_data["balance"] = float(balance)
                expense_accounts.append(account_data)
                total_expenses += balance
        
        net_profit = total_income - total_expenses
        
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "income": {
                "accounts": income_accounts,
                "total": float(total_income)
            },
            "expenses": {
                "accounts": expense_accounts,
                "total": float(total_expenses)
            },
            "net_profit": float(net_profit),
            "gross_margin_percent": float(round((net_profit / total_income * 100), 2)) if total_income > 0 else 0
        }
    
    async def get_balance_sheet(
        self,
        organization_id: str,
        as_of_date: str
    ) -> Dict:
        """
        Generate Balance Sheet from journal entries.
        
        Assets = Liabilities + Equity
        """
        # Aggregate asset, liability, and equity accounts
        pipeline = [
            {
                "$match": {
                    "organization_id": organization_id,
                    "is_posted": True,
                    "entry_date": {"$lte": as_of_date}
                }
            },
            {"$unwind": "$lines"},
            {
                "$match": {
                    "lines.account_type": {"$in": [
                        AccountType.ASSET.value, 
                        AccountType.LIABILITY.value, 
                        AccountType.EQUITY.value
                    ]}
                }
            },
            {
                "$group": {
                    "_id": {
                        "account_id": "$lines.account_id",
                        "account_name": "$lines.account_name",
                        "account_code": "$lines.account_code",
                        "account_type": "$lines.account_type"
                    },
                    "total_debit": {"$sum": "$lines.debit_amount"},
                    "total_credit": {"$sum": "$lines.credit_amount"}
                }
            },
            {"$sort": {"_id.account_code": 1}}
        ]
        
        results = await self.journal_entries.aggregate(pipeline).to_list(1000)
        
        assets = []
        liabilities = []
        equity = []
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        total_equity = Decimal("0")
        
        for row in results:
            debit = Decimal(str(row["total_debit"]))
            credit = Decimal(str(row["total_credit"]))
            account_type = row["_id"]["account_type"]
            
            account_data = {
                "account_id": row["_id"]["account_id"],
                "account_name": row["_id"]["account_name"],
                "account_code": row["_id"]["account_code"]
            }
            
            if account_type == AccountType.ASSET.value:
                balance = debit - credit
                account_data["balance"] = float(balance)
                assets.append(account_data)
                total_assets += balance
            elif account_type == AccountType.LIABILITY.value:
                balance = credit - debit
                account_data["balance"] = float(balance)
                liabilities.append(account_data)
                total_liabilities += balance
            else:  # Equity
                balance = credit - debit
                account_data["balance"] = float(balance)
                equity.append(account_data)
                total_equity += balance
        
        # Add retained earnings (net income) to equity
        # Get all-time P&L
        pl = await self.get_profit_and_loss(organization_id, "1900-01-01", as_of_date)
        retained_earnings = Decimal(str(pl["net_profit"]))
        
        is_balanced = total_assets == (total_liabilities + total_equity + retained_earnings)
        
        return {
            "as_of_date": as_of_date,
            "assets": {
                "accounts": assets,
                "total": float(total_assets)
            },
            "liabilities": {
                "accounts": liabilities,
                "total": float(total_liabilities)
            },
            "equity": {
                "accounts": equity,
                "retained_earnings": float(retained_earnings),
                "total": float(total_equity + retained_earnings)
            },
            "is_balanced": is_balanced,
            "equation": {
                "assets": float(total_assets),
                "liabilities_plus_equity": float(total_liabilities + total_equity + retained_earnings)
            }
        }
    
    async def get_journal_entries(
        self,
        organization_id: str,
        start_date: str = None,
        end_date: str = None,
        entry_type: str = None,
        account_id: str = None,
        is_posted: bool = None,
        limit: int = 100,
        skip: int = 0
    ) -> Dict:
        """List journal entries with filters"""
        query = {"organization_id": organization_id}
        
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
        
        total = await self.journal_entries.count_documents(query)
        
        entries = await self.journal_entries.find(
            query,
            {"_id": 0}
        ).sort("entry_date", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "entries": entries,
            "total": total,
            "limit": limit,
            "skip": skip,
            "has_more": total > skip + limit
        }
    
    async def get_account_ledger(
        self,
        organization_id: str,
        account_id: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """Get ledger (all transactions) for a specific account with running balance"""
        if not start_date:
            start_date = "1900-01-01"
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get account details
        account = await self.get_account_by_id(organization_id, account_id)
        if not account:
            return {"error": "Account not found"}
        
        # Get opening balance (before start_date)
        opening_query = {
            "organization_id": organization_id,
            "is_posted": True,
            "entry_date": {"$lt": start_date},
            "lines.account_id": account_id
        }
        
        opening_pipeline = [
            {"$match": opening_query},
            {"$unwind": "$lines"},
            {"$match": {"lines.account_id": account_id}},
            {
                "$group": {
                    "_id": None,
                    "total_debit": {"$sum": "$lines.debit_amount"},
                    "total_credit": {"$sum": "$lines.credit_amount"}
                }
            }
        ]
        
        opening_result = await self.journal_entries.aggregate(opening_pipeline).to_list(1)
        opening_balance = Decimal("0")
        if opening_result:
            opening_balance = Decimal(str(opening_result[0]["total_debit"])) - Decimal(str(opening_result[0]["total_credit"]))
        
        # Get transactions in period
        period_query = {
            "organization_id": organization_id,
            "is_posted": True,
            "entry_date": {"$gte": start_date, "$lte": end_date},
            "lines.account_id": account_id
        }
        
        entries = await self.journal_entries.find(
            period_query,
            {"_id": 0}
        ).sort("entry_date", 1).to_list(10000)
        
        # Build ledger with running balance
        ledger_entries = []
        running_balance = opening_balance
        
        for entry in entries:
            for line in entry["lines"]:
                if line["account_id"] == account_id:
                    debit = Decimal(str(line["debit_amount"]))
                    credit = Decimal(str(line["credit_amount"]))
                    running_balance += debit - credit
                    
                    ledger_entries.append({
                        "entry_id": entry["entry_id"],
                        "entry_date": entry["entry_date"],
                        "reference_number": entry["reference_number"],
                        "description": entry["description"],
                        "line_description": line["description"],
                        "debit_amount": float(debit),
                        "credit_amount": float(credit),
                        "running_balance": float(running_balance)
                    })
        
        return {
            "account_id": account_id,
            "account_name": account["account_name"],
            "account_code": account["account_code"],
            "account_type": account["account_type"],
            "period": {"start_date": start_date, "end_date": end_date},
            "opening_balance": float(opening_balance),
            "closing_balance": float(running_balance),
            "total_debit": float(sum(Decimal(str(e["debit_amount"])) for e in ledger_entries)),
            "total_credit": float(sum(Decimal(str(e["credit_amount"])) for e in ledger_entries)),
            "entries": ledger_entries
        }


# ========================= SERVICE SINGLETON =========================

_double_entry_service: Optional[DoubleEntryService] = None


def init_double_entry_service(db) -> DoubleEntryService:
    """Initialize the double entry service singleton"""
    global _double_entry_service
    _double_entry_service = DoubleEntryService(db)
    logger.info("DoubleEntryService initialized")
    return _double_entry_service


def get_double_entry_service() -> DoubleEntryService:
    """Get the double entry service singleton"""
    if _double_entry_service is None:
        raise RuntimeError("DoubleEntryService not initialized")
    return _double_entry_service
