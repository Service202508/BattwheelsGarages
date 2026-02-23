"""
Finance Dashboard Service
==========================
Aggregates data across Expenses, Bills, and Banking modules
for the Finance Dashboard overview.

Author: Battwheels OS
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FinanceDashboardService:
    """Service for aggregating finance dashboard data"""
    
    def __init__(self, db):
        self.db = db
        self.expenses = db.expenses
        self.bills = db.bills
        self.bank_accounts = db.bank_accounts
        self.bank_transactions = db.bank_transactions
        self.invoices = db.invoices
        self.journal_entries = db.journal_entries
        logger.info("FinanceDashboardService initialized")
    
    async def get_dashboard_data(self, org_id: str) -> Dict[str, Any]:
        """Get all dashboard data in a single call"""
        
        # Get all data in parallel-ish manner
        cash_position = await self._get_cash_position(org_id)
        cash_flow_chart = await self._get_cash_flow_trend(org_id)
        bank_accounts = await self._get_bank_accounts_summary(org_id)
        overdue_bills = await self._get_overdue_bills(org_id)
        pending_expenses = await self._get_pending_expenses(org_id)
        upcoming_bills = await self._get_upcoming_bills(org_id)
        
        return {
            "cash_position": cash_position,
            "cash_flow_chart": cash_flow_chart,
            "bank_accounts": bank_accounts,
            "overdue_bills": overdue_bills,
            "pending_expenses": pending_expenses,
            "upcoming_bills": upcoming_bills,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _get_cash_position(self, org_id: str) -> Dict[str, Any]:
        """Get the 6 cash position cards data"""
        today = datetime.now().strftime("%Y-%m-%d")
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        
        # 1. Total Bank Balance
        bank_accounts = await self.bank_accounts.find(
            {"organization_id": org_id, "is_active": True},
            {"_id": 0, "current_balance": 1}
        ).to_list(50)
        total_bank_balance = sum(a.get("current_balance", 0) for a in bank_accounts)
        num_accounts = len(bank_accounts)
        
        # 2. Accounts Receivable (Outstanding invoices)
        ar_pipeline = [
            {"$match": {
                "organization_id": org_id,
                "status": {"$in": ["sent", "partial", "overdue"]}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$balance_due"},
                "count": {"$sum": 1}
            }}
        ]
        ar_result = await self.invoices.aggregate(ar_pipeline).to_list(1)
        accounts_receivable = ar_result[0]["total"] if ar_result else 0
        ar_count = ar_result[0]["count"] if ar_result else 0
        
        # 3. Accounts Payable (Outstanding bills)
        ap_pipeline = [
            {"$match": {
                "organization_id": org_id,
                "status": {"$nin": ["PAID", "CANCELLED"]},
                "balance_due": {"$gt": 0}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$balance_due"},
                "count": {"$sum": 1}
            }}
        ]
        ap_result = await self.bills.aggregate(ap_pipeline).to_list(1)
        accounts_payable = ap_result[0]["total"] if ap_result else 0
        ap_count = ap_result[0]["count"] if ap_result else 0
        
        # 4. Expenses Pending Approval
        pending_exp_pipeline = [
            {"$match": {
                "organization_id": org_id,
                "status": "SUBMITTED"
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$total_amount"},
                "count": {"$sum": 1}
            }}
        ]
        pending_result = await self.expenses.aggregate(pending_exp_pipeline).to_list(1)
        pending_expenses_count = pending_result[0]["count"] if pending_result else 0
        pending_expenses_amount = pending_result[0]["total"] if pending_result else 0
        
        # 5. Overdue Bills
        overdue_pipeline = [
            {"$match": {
                "organization_id": org_id,
                "status": {"$nin": ["PAID", "CANCELLED"]},
                "due_date": {"$lt": today},
                "balance_due": {"$gt": 0}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$balance_due"},
                "count": {"$sum": 1}
            }}
        ]
        overdue_result = await self.bills.aggregate(overdue_pipeline).to_list(1)
        overdue_count = overdue_result[0]["count"] if overdue_result else 0
        overdue_amount = overdue_result[0]["total"] if overdue_result else 0
        
        # 6. Net Cash Flow This Month
        cash_flow_pipeline = [
            {"$match": {
                "organization_id": org_id,
                "transaction_date": {"$gte": month_start}
            }},
            {"$group": {
                "_id": "$transaction_type",
                "total": {"$sum": "$amount"}
            }}
        ]
        cash_flow_result = await self.bank_transactions.aggregate(cash_flow_pipeline).to_list(2)
        credits_this_month = 0
        debits_this_month = 0
        for r in cash_flow_result:
            if r["_id"] == "CREDIT":
                credits_this_month = r["total"]
            elif r["_id"] == "DEBIT":
                debits_this_month = r["total"]
        net_cash_flow = credits_this_month - debits_this_month
        
        return {
            "total_bank_balance": {
                "value": total_bank_balance,
                "num_accounts": num_accounts,
                "last_updated": datetime.now().isoformat()
            },
            "accounts_receivable": {
                "value": accounts_receivable,
                "count": ar_count
            },
            "accounts_payable": {
                "value": accounts_payable,
                "count": ap_count
            },
            "pending_expenses": {
                "count": pending_expenses_count,
                "amount": pending_expenses_amount
            },
            "overdue_bills": {
                "count": overdue_count,
                "amount": overdue_amount
            },
            "net_cash_flow": {
                "value": net_cash_flow,
                "credits": credits_this_month,
                "debits": debits_this_month
            }
        }
    
    async def _get_cash_flow_trend(self, org_id: str, months: int = 6) -> Dict[str, Any]:
        """Get cash flow data for the last N months"""
        # Calculate start date (6 months ago, first of month)
        today = datetime.now()
        start_date = (today.replace(day=1) - timedelta(days=months * 30)).replace(day=1)
        start_str = start_date.strftime("%Y-%m-%d")
        
        # Aggregate transactions by month
        pipeline = [
            {"$match": {
                "organization_id": org_id,
                "transaction_date": {"$gte": start_str}
            }},
            {"$group": {
                "_id": {
                    "month": {"$substr": ["$transaction_date", 0, 7]},
                    "type": "$transaction_type"
                },
                "total": {"$sum": "$amount"}
            }},
            {"$sort": {"_id.month": 1}}
        ]
        
        results = await self.bank_transactions.aggregate(pipeline).to_list(100)
        
        # Organize by month
        months_data = {}
        for r in results:
            month = r["_id"]["month"]
            txn_type = r["_id"]["type"]
            
            if month not in months_data:
                months_data[month] = {"credits": 0, "debits": 0}
            
            if txn_type == "CREDIT":
                months_data[month]["credits"] = r["total"]
            elif txn_type == "DEBIT":
                months_data[month]["debits"] = r["total"]
        
        # Convert to chart format
        chart_data = []
        total_in = 0
        total_out = 0
        
        for month in sorted(months_data.keys()):
            data = months_data[month]
            net = data["credits"] - data["debits"]
            chart_data.append({
                "month": month,
                "month_label": datetime.strptime(month, "%Y-%m").strftime("%b %Y"),
                "credits": data["credits"],
                "debits": data["debits"],
                "net": net
            })
            total_in += data["credits"]
            total_out += data["debits"]
        
        return {
            "data": chart_data,
            "totals": {
                "total_in": total_in,
                "total_out": total_out,
                "net": total_in - total_out
            }
        }
    
    async def _get_bank_accounts_summary(self, org_id: str) -> Dict[str, Any]:
        """Get bank accounts with balances"""
        accounts = await self.bank_accounts.find(
            {"organization_id": org_id, "is_active": True},
            {"_id": 0}
        ).sort([("is_default", -1), ("current_balance", -1)]).to_list(20)
        
        total_balance = sum(a.get("current_balance", 0) for a in accounts)
        
        return {
            "accounts": accounts,
            "total_balance": total_balance
        }
    
    async def _get_overdue_bills(self, org_id: str, limit: int = 5) -> Dict[str, Any]:
        """Get overdue bills for alerts"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        bills = await self.bills.find(
            {
                "organization_id": org_id,
                "status": {"$nin": ["PAID", "CANCELLED"]},
                "due_date": {"$lt": today},
                "balance_due": {"$gt": 0}
            },
            {"_id": 0}
        ).sort("due_date", 1).limit(limit).to_list(limit)
        
        # Calculate days overdue
        for bill in bills:
            due = datetime.strptime(bill["due_date"], "%Y-%m-%d")
            bill["days_overdue"] = (datetime.now() - due).days
        
        # Get total count
        total_count = await self.bills.count_documents({
            "organization_id": org_id,
            "status": {"$nin": ["PAID", "CANCELLED"]},
            "due_date": {"$lt": today},
            "balance_due": {"$gt": 0}
        })
        
        return {
            "bills": bills,
            "total_count": total_count
        }
    
    async def _get_pending_expenses(self, org_id: str, limit: int = 5) -> Dict[str, Any]:
        """Get expenses pending approval"""
        expenses = await self.expenses.find(
            {
                "organization_id": org_id,
                "status": "SUBMITTED"
            },
            {"_id": 0}
        ).sort("submitted_date", 1).limit(limit).to_list(limit)
        
        total_count = await self.expenses.count_documents({
            "organization_id": org_id,
            "status": "SUBMITTED"
        })
        
        return {
            "expenses": expenses,
            "total_count": total_count
        }
    
    async def _get_upcoming_bills(self, org_id: str, limit: int = 5) -> Dict[str, Any]:
        """Get bills due in next 7 days"""
        today = datetime.now().strftime("%Y-%m-%d")
        week_later = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        bills = await self.bills.find(
            {
                "organization_id": org_id,
                "status": {"$nin": ["PAID", "CANCELLED"]},
                "due_date": {"$gte": today, "$lte": week_later},
                "balance_due": {"$gt": 0}
            },
            {"_id": 0}
        ).sort("due_date", 1).limit(limit).to_list(limit)
        
        # Calculate days until due
        for bill in bills:
            due = datetime.strptime(bill["due_date"], "%Y-%m-%d")
            days_until = (due - datetime.now()).days
            bill["days_until_due"] = max(0, days_until)
        
        total_count = await self.bills.count_documents({
            "organization_id": org_id,
            "status": {"$nin": ["PAID", "CANCELLED"]},
            "due_date": {"$gte": today, "$lte": week_later},
            "balance_due": {"$gt": 0}
        })
        
        total_amount = 0
        for bill in bills:
            total_amount += bill.get("balance_due", 0)
        
        return {
            "bills": bills,
            "total_count": total_count,
            "total_amount": total_amount
        }


# Service factory
_finance_dashboard_service = None


def get_finance_dashboard_service():
    if _finance_dashboard_service is None:
        raise ValueError("FinanceDashboardService not initialized")
    return _finance_dashboard_service


def init_finance_dashboard_service(db):
    global _finance_dashboard_service
    _finance_dashboard_service = FinanceDashboardService(db)
    return _finance_dashboard_service
