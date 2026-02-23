"""
Bills Service - Vendor Invoice Management
==========================================
Complete bill/vendor invoice tracking with:
- Line items with GST per item
- Payment tracking (partial/full)
- Aging reports
- Double-entry accounting integration

Author: Battwheels OS
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
import uuid
import logging

logger = logging.getLogger(__name__)

BILL_STATUSES = ["DRAFT", "RECEIVED", "APPROVED", "PARTIAL_PAID", "PAID", "OVERDUE", "CANCELLED"]


class BillsService:
    """Service for managing vendor bills/invoices"""
    
    def __init__(self, db):
        self.db = db
        self.bills = db.bills
        self.line_items = db.bill_line_items
        self.payments = db.bill_payments
        self.counters = db.counters
        logger.info("BillsService initialized")
    
    async def get_next_bill_ref(self, org_id: str) -> str:
        """Generate next internal bill reference: BILL-2024-0001"""
        year = datetime.now().year
        counter_id = f"bill_{org_id}_{year}"
        
        result = await self.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        
        seq = result.get("seq", 1)
        return f"BILL-{year}-{seq:04d}"
    
    async def create_bill(
        self,
        org_id: str,
        bill_number: str,  # Vendor's invoice number
        vendor_id: str,
        bill_date: str,
        due_date: str,
        line_items: List[Dict[str, Any]],
        vendor_name: Optional[str] = None,
        vendor_gstin: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        is_rcm: bool = False,
        notes: Optional[str] = None,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """Create a new vendor bill"""
        bill_id = f"bill_{uuid.uuid4().hex[:12]}"
        internal_ref = await self.get_next_bill_ref(org_id)
        
        # Calculate totals from line items
        subtotal = Decimal('0')
        total_cgst = Decimal('0')
        total_sgst = Decimal('0')
        total_igst = Decimal('0')
        
        saved_items = []
        for idx, item in enumerate(line_items):
            item_id = f"bill_item_{uuid.uuid4().hex[:12]}"
            qty = Decimal(str(item.get("quantity", 1)))
            rate = Decimal(str(item.get("rate", 0)))
            amount = qty * rate
            gst_rate = Decimal(str(item.get("gst_rate", 0))) / 100
            
            is_igst = item.get("is_igst", False)
            if is_igst:
                igst = (amount * gst_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cgst = sgst = Decimal('0')
            else:
                half_rate = gst_rate / 2
                cgst = (amount * half_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                sgst = (amount * half_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                igst = Decimal('0')
            
            item_total = amount + cgst + sgst + igst
            subtotal += amount
            total_cgst += cgst
            total_sgst += sgst
            total_igst += igst
            
            line_item_doc = {
                "item_id": item_id,
                "bill_id": bill_id,
                "organization_id": org_id,
                "item_description": item.get("description", ""),
                "hsn_sac_code": item.get("hsn_sac_code"),
                "quantity": float(qty),
                "unit": item.get("unit", "nos"),
                "rate": float(rate),
                "amount": float(amount),
                "gst_rate": item.get("gst_rate", 0),
                "is_igst": is_igst,
                "cgst": float(cgst),
                "sgst": float(sgst),
                "igst": float(igst),
                "total": float(item_total),
                "account_code": item.get("account_code", "5000"),  # Default expense account
                "order": idx + 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            saved_items.append(line_item_doc)
        
        # Insert line items
        if saved_items:
            await self.line_items.insert_many(saved_items)
        
        total_amount = subtotal + total_cgst + total_sgst + total_igst
        
        bill = {
            "bill_id": bill_id,
            "internal_ref": internal_ref,
            "bill_number": bill_number,
            "organization_id": org_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "vendor_gstin": vendor_gstin,
            "bill_date": bill_date,
            "due_date": due_date,
            "purchase_order_id": purchase_order_id,
            "status": "DRAFT",
            "subtotal": float(subtotal),
            "cgst": float(total_cgst),
            "sgst": float(total_sgst),
            "igst": float(total_igst),
            "total_amount": float(total_amount),
            "amount_paid": 0,
            "balance_due": float(total_amount),
            "is_rcm": is_rcm,
            "is_itc_eligible": bool(vendor_gstin),
            "notes": notes,
            "created_by": created_by,
            "approved_by": None,
            "approved_at": None,
            "journal_entry_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.bills.insert_one(bill)
        logger.info(f"Created bill {internal_ref} (vendor invoice: {bill_number})")
        
        result = {k: v for k, v in bill.items() if k != "_id"}
        result["line_items"] = [{k: v for k, v in item.items() if k != "_id"} for item in saved_items]
        
        return result
    
    async def get_bill(self, bill_id: str, include_items: bool = True) -> Optional[Dict[str, Any]]:
        """Get a single bill by ID"""
        bill = await self.bills.find_one({"bill_id": bill_id}, {"_id": 0})
        if bill and include_items:
            items = await self.line_items.find(
                {"bill_id": bill_id}, {"_id": 0}
            ).sort("order", 1).to_list(100)
            bill["line_items"] = items
            
            # Get payments
            payments = await self.payments.find(
                {"bill_id": bill_id}, {"_id": 0}
            ).sort("payment_date", -1).to_list(50)
            bill["payments"] = payments
        
        return bill
    
    async def list_bills(
        self,
        org_id: str,
        status: Optional[str] = None,
        vendor_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        overdue_only: bool = False,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List bills with filters"""
        query = {"organization_id": org_id}
        
        if status:
            query["status"] = status
        if vendor_id:
            query["vendor_id"] = vendor_id
        if date_from:
            query["bill_date"] = query.get("bill_date", {})
            query["bill_date"]["$gte"] = date_from
        if date_to:
            query["bill_date"] = query.get("bill_date", {})
            query["bill_date"]["$lte"] = date_to
        if overdue_only:
            today = datetime.now().strftime("%Y-%m-%d")
            query["due_date"] = {"$lt": today}
            query["status"] = {"$nin": ["PAID", "CANCELLED"]}
        
        total = await self.bills.count_documents(query)
        skip = (page - 1) * limit
        
        bills = await self.bills.find(query, {"_id": 0}).sort(
            "bill_date", -1
        ).skip(skip).limit(limit).to_list(limit)
        
        return bills, total
    
    async def update_bill(self, bill_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a bill (only if DRAFT)"""
        bill = await self.get_bill(bill_id, include_items=False)
        if not bill:
            return None
        
        if bill["status"] != "DRAFT":
            raise ValueError(f"Cannot edit bill in {bill['status']} status")
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.bills.find_one_and_update(
            {"bill_id": bill_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def approve_bill(
        self,
        bill_id: str,
        approved_by: str,
        de_service = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Approve bill and post journal entry"""
        bill = await self.get_bill(bill_id)
        if not bill:
            raise ValueError("Bill not found")
        
        if bill["status"] not in ["DRAFT", "RECEIVED"]:
            raise ValueError(f"Cannot approve bill in {bill['status']} status")
        
        journal_entry_id = None
        
        # Post journal entry
        if de_service:
            journal_entry_id = await self._post_approval_journal(bill, approved_by, de_service)
        
        # Update bill status
        result = await self.bills.find_one_and_update(
            {"bill_id": bill_id},
            {"$set": {
                "status": "APPROVED",
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "journal_entry_id": journal_entry_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            return_document=True
        )
        
        logger.info(f"Bill {bill_id} approved")
        return {k: v for k, v in result.items() if k != "_id"}, journal_entry_id
    
    async def _post_approval_journal(
        self,
        bill: Dict[str, Any],
        approved_by: str,
        de_service
    ) -> Optional[str]:
        """Post journal entry on bill approval"""
        try:
            org_id = bill["organization_id"]
            await de_service.ensure_system_accounts(org_id)
            
            lines = []
            
            # Debit expense accounts per line item
            for item in bill.get("line_items", []):
                account_code = item.get("account_code", "5000")
                expense_account = await de_service.get_account_by_code(org_id, account_code)
                if not expense_account:
                    expense_account = await de_service.get_account_by_code(org_id, "5000")
                
                if expense_account:
                    lines.append({
                        "account_id": expense_account["account_id"],
                        "debit_amount": item["amount"],
                        "credit_amount": 0,
                        "description": item["item_description"][:100]
                    })
            
            # Debit input GST if ITC eligible
            if bill.get("is_itc_eligible"):
                if bill.get("cgst", 0) > 0:
                    cgst_account = await de_service.get_account_by_code(org_id, "1410")
                    if cgst_account:
                        lines.append({
                            "account_id": cgst_account["account_id"],
                            "debit_amount": bill["cgst"],
                            "credit_amount": 0,
                            "description": f"Input CGST - Bill {bill['internal_ref']}"
                        })
                if bill.get("sgst", 0) > 0:
                    sgst_account = await de_service.get_account_by_code(org_id, "1420")
                    if sgst_account:
                        lines.append({
                            "account_id": sgst_account["account_id"],
                            "debit_amount": bill["sgst"],
                            "credit_amount": 0,
                            "description": f"Input SGST - Bill {bill['internal_ref']}"
                        })
                if bill.get("igst", 0) > 0:
                    igst_account = await de_service.get_account_by_code(org_id, "1430")
                    if igst_account:
                        lines.append({
                            "account_id": igst_account["account_id"],
                            "debit_amount": bill["igst"],
                            "credit_amount": 0,
                            "description": f"Input IGST - Bill {bill['internal_ref']}"
                        })
            
            # Credit accounts payable
            payable_account = await de_service.get_account_by_code(org_id, "2100")
            if payable_account:
                lines.append({
                    "account_id": payable_account["account_id"],
                    "debit_amount": 0,
                    "credit_amount": bill["total_amount"],
                    "description": f"Bill payable - {bill['internal_ref']}"
                })
            
            if not lines:
                return None
            
            narration = f"Bill: {bill['bill_number']} | Vendor: {bill.get('vendor_name', 'N/A')} | Ref: {bill['internal_ref']}"
            
            success, msg, entry = await de_service.create_journal_entry(
                organization_id=org_id,
                entry_date=bill["bill_date"],
                description=narration,
                lines=lines,
                entry_type="BILL",
                source_document_id=bill["bill_id"],
                source_document_type="VENDOR_BILL",
                created_by=approved_by
            )
            
            if success:
                return entry.get("entry_id")
            return None
            
        except Exception as e:
            logger.error(f"Error posting bill journal: {e}")
            return None
    
    async def record_payment(
        self,
        bill_id: str,
        amount: float,
        payment_date: str,
        payment_mode: str,
        bank_account_id: Optional[str] = None,
        reference_number: Optional[str] = None,
        paid_by: str = "system",
        de_service = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Record payment against a bill"""
        bill = await self.get_bill(bill_id, include_items=False)
        if not bill:
            raise ValueError("Bill not found")
        
        if bill["status"] in ["PAID", "CANCELLED"]:
            raise ValueError(f"Cannot record payment for {bill['status']} bill")
        
        if amount > bill["balance_due"]:
            raise ValueError(f"Payment amount (₹{amount}) exceeds balance due (₹{bill['balance_due']})")
        
        # Create payment record
        payment_id = f"bill_pmt_{uuid.uuid4().hex[:12]}"
        new_amount_paid = bill["amount_paid"] + amount
        new_balance = bill["balance_due"] - amount
        new_status = "PAID" if new_balance <= 0 else "PARTIAL_PAID"
        
        payment = {
            "payment_id": payment_id,
            "bill_id": bill_id,
            "organization_id": bill["organization_id"],
            "payment_date": payment_date,
            "amount": amount,
            "payment_mode": payment_mode,
            "bank_account_id": bank_account_id,
            "reference_number": reference_number,
            "created_by": paid_by,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Post journal entry
        journal_entry_id = None
        if de_service:
            journal_entry_id = await self._post_payment_journal(bill, payment, de_service)
            payment["journal_entry_id"] = journal_entry_id
        
        await self.payments.insert_one(payment)
        
        # Update bill
        await self.bills.update_one(
            {"bill_id": bill_id},
            {"$set": {
                "amount_paid": new_amount_paid,
                "balance_due": new_balance,
                "status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Recorded payment of ₹{amount} for bill {bill_id}")
        return {k: v for k, v in payment.items() if k != "_id"}, journal_entry_id
    
    async def _post_payment_journal(
        self,
        bill: Dict[str, Any],
        payment: Dict[str, Any],
        de_service
    ) -> Optional[str]:
        """Post journal entry for bill payment"""
        try:
            org_id = bill["organization_id"]
            await de_service.ensure_system_accounts(org_id)
            
            payable_account = await de_service.get_account_by_code(org_id, "2100")
            
            mode = payment.get("payment_mode", "BANK")
            if mode in ["BANK", "UPI"]:
                payment_account = await de_service.get_account_by_code(org_id, "1200")
            else:
                payment_account = await de_service.get_account_by_code(org_id, "1210")
            
            if not payable_account or not payment_account:
                return None
            
            narration = f"Bill payment: {bill['internal_ref']} | Vendor: {bill.get('vendor_name', 'N/A')} | Mode: {mode}"
            
            success, msg, entry = await de_service.create_journal_entry(
                organization_id=org_id,
                entry_date=payment["payment_date"],
                description=narration,
                lines=[
                    {
                        "account_id": payable_account["account_id"],
                        "debit_amount": payment["amount"],
                        "credit_amount": 0,
                        "description": f"Payment for {bill['internal_ref']}"
                    },
                    {
                        "account_id": payment_account["account_id"],
                        "debit_amount": 0,
                        "credit_amount": payment["amount"],
                        "description": f"Bill payment - {bill.get('vendor_name', 'Vendor')}"
                    }
                ],
                entry_type="PAYMENT",
                source_document_id=payment["payment_id"],
                source_document_type="BILL_PAYMENT",
                created_by=payment.get("created_by", "system")
            )
            
            if success:
                return entry.get("entry_id")
            return None
            
        except Exception as e:
            logger.error(f"Error posting payment journal: {e}")
            return None
    
    async def get_aging_report(self, org_id: str) -> Dict[str, Any]:
        """Get bills aging report grouped by days overdue"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get all unpaid bills
        bills = await self.bills.find({
            "organization_id": org_id,
            "status": {"$nin": ["PAID", "CANCELLED"]},
            "balance_due": {"$gt": 0}
        }, {"_id": 0}).to_list(500)
        
        aging = {
            "current": {"bills": [], "total": 0},      # Not yet due
            "1_30": {"bills": [], "total": 0},         # 1-30 days overdue
            "31_60": {"bills": [], "total": 0},        # 31-60 days
            "61_90": {"bills": [], "total": 0},        # 61-90 days
            "over_90": {"bills": [], "total": 0}       # 90+ days
        }
        
        for bill in bills:
            due_date = bill.get("due_date", today)
            days_overdue = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(due_date, "%Y-%m-%d")).days
            balance = bill.get("balance_due", 0)
            
            bill_summary = {
                "bill_id": bill["bill_id"],
                "internal_ref": bill["internal_ref"],
                "vendor_name": bill.get("vendor_name"),
                "due_date": due_date,
                "balance_due": balance,
                "days_overdue": max(0, days_overdue)
            }
            
            if days_overdue <= 0:
                aging["current"]["bills"].append(bill_summary)
                aging["current"]["total"] += balance
            elif days_overdue <= 30:
                aging["1_30"]["bills"].append(bill_summary)
                aging["1_30"]["total"] += balance
            elif days_overdue <= 60:
                aging["31_60"]["bills"].append(bill_summary)
                aging["31_60"]["total"] += balance
            elif days_overdue <= 90:
                aging["61_90"]["bills"].append(bill_summary)
                aging["61_90"]["total"] += balance
            else:
                aging["over_90"]["bills"].append(bill_summary)
                aging["over_90"]["total"] += balance
        
        # Calculate grand total
        grand_total = sum(bucket["total"] for bucket in aging.values())
        
        return {
            "aging": aging,
            "grand_total": grand_total,
            "as_of_date": today
        }
    
    async def get_vendor_aging_report(self, org_id: str) -> Dict[str, Any]:
        """Get bills aging report grouped by vendor"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get all unpaid bills
        bills = await self.bills.find({
            "organization_id": org_id,
            "status": {"$nin": ["PAID", "CANCELLED"]},
            "balance_due": {"$gt": 0}
        }, {"_id": 0}).to_list(500)
        
        vendor_aging = {}
        
        for bill in bills:
            vendor_id = bill.get("vendor_id", "unknown")
            vendor_name = bill.get("vendor_name", "Unknown Vendor")
            due_date = bill.get("due_date", today)
            days_overdue = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(due_date, "%Y-%m-%d")).days
            balance = bill.get("balance_due", 0)
            
            if vendor_id not in vendor_aging:
                vendor_aging[vendor_id] = {
                    "vendor_id": vendor_id,
                    "vendor_name": vendor_name,
                    "current": 0,
                    "days_1_30": 0,
                    "days_31_60": 0,
                    "days_61_90": 0,
                    "days_over_90": 0,
                    "total": 0
                }
            
            # Categorize by aging bucket
            if days_overdue <= 0:
                vendor_aging[vendor_id]["current"] += balance
            elif days_overdue <= 30:
                vendor_aging[vendor_id]["days_1_30"] += balance
            elif days_overdue <= 60:
                vendor_aging[vendor_id]["days_31_60"] += balance
            elif days_overdue <= 90:
                vendor_aging[vendor_id]["days_61_90"] += balance
            else:
                vendor_aging[vendor_id]["days_over_90"] += balance
            
            vendor_aging[vendor_id]["total"] += balance
        
        # Convert to list sorted by total descending
        vendors = sorted(vendor_aging.values(), key=lambda x: x["total"], reverse=True)
        
        # Calculate totals
        totals = {
            "current": sum(v["current"] for v in vendors),
            "days_1_30": sum(v["days_1_30"] for v in vendors),
            "days_31_60": sum(v["days_31_60"] for v in vendors),
            "days_61_90": sum(v["days_61_90"] for v in vendors),
            "days_over_90": sum(v["days_over_90"] for v in vendors),
            "grand_total": sum(v["total"] for v in vendors)
        }
        
        return {
            "vendors": vendors,
            "totals": totals,
            "as_of_date": today
        }


# ==================== SERVICE FACTORY ====================

_bills_service: Optional[BillsService] = None


def get_bills_service() -> BillsService:
    if _bills_service is None:
        raise ValueError("BillsService not initialized")
    return _bills_service


def init_bills_service(db) -> BillsService:
    global _bills_service
    _bills_service = BillsService(db)
    return _bills_service
