"""
Battwheels OS - Financial Dashboard API Routes
Zoho Books-style financial overview endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import os
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/dashboard/financial", tags=["Financial Dashboard"])

# Database connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def get_org_id(request: Request) -> Optional[str]:
    """Get organization ID from request header"""
    return request.headers.get("X-Organization-ID")


@router.get("/summary")
async def get_financial_summary(request: Request):
    """
    Get comprehensive financial summary for dashboard
    Similar to Zoho Books home page metrics
    """
    org_id = await get_org_id(request)
    
    # Return empty summary if no org context (graceful degradation)
    if not org_id:
        return {
            "code": 0,
            "summary": {
                "receivables": {
                    "total": 0,
                    "current": 0,
                    "overdue": 0,
                    "invoice_count": 0,
                    "paid_count": 0,
                    "overdue_count": 0
                },
                "payables": {
                    "total": 0,
                    "current": 0,
                    "overdue": 0,
                    "bill_count": 0,
                    "paid_count": 0
                },
                "as_of": datetime.now(timezone.utc).isoformat(),
                "org_missing": True
            }
        }
    
    today = datetime.now(timezone.utc)
    
    # Calculate receivables (unpaid invoices)
    total_receivables = 0
    current_receivables = 0
    overdue_receivables = 0
    
    invoices_cursor = db.invoices.find({
        "organization_id": org_id,
        "status": {"$nin": ["paid", "void", "draft"]}
    }, {"_id": 0, "balance": 1, "due_date": 1, "total": 1})
    
    async for invoice in invoices_cursor:
        balance = float(invoice.get("balance") or invoice.get("total") or 0)
        total_receivables += balance
        
        due_date_str = invoice.get("due_date")
        if due_date_str:
            try:
                if isinstance(due_date_str, str):
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                else:
                    due_date = due_date_str
                
                if due_date.replace(tzinfo=timezone.utc) < today:
                    overdue_receivables += balance
                else:
                    current_receivables += balance
            except:
                current_receivables += balance
        else:
            current_receivables += balance
    
    # Calculate payables (unpaid bills)
    total_payables = 0
    current_payables = 0
    overdue_payables = 0
    
    bills_cursor = db.bills.find({
        "organization_id": org_id,
        "status": {"$nin": ["paid", "void", "draft"]}
    }, {"_id": 0, "balance": 1, "due_date": 1, "total": 1})
    
    async for bill in bills_cursor:
        balance = float(bill.get("balance") or bill.get("total") or 0)
        total_payables += balance
        
        due_date_str = bill.get("due_date")
        if due_date_str:
            try:
                if isinstance(due_date_str, str):
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                else:
                    due_date = due_date_str
                
                if due_date.replace(tzinfo=timezone.utc) < today:
                    overdue_payables += balance
                else:
                    current_payables += balance
            except:
                current_payables += balance
        else:
            current_payables += balance
    
    # Get invoice counts
    total_invoices = await db.invoices.count_documents({"organization_id": org_id})
    paid_invoices = await db.invoices.count_documents({"organization_id": org_id, "status": "paid"})
    overdue_invoices = await db.invoices.count_documents({
        "organization_id": org_id,
        "status": {"$nin": ["paid", "void", "draft"]},
        "due_date": {"$lt": today.isoformat()}
    })
    
    # Get bill counts
    total_bills = await db.bills.count_documents({"organization_id": org_id})
    paid_bills = await db.bills.count_documents({"organization_id": org_id, "status": "paid"})
    
    return {
        "code": 0,
        "summary": {
            "receivables": {
                "total": round(total_receivables, 2),
                "current": round(current_receivables, 2),
                "overdue": round(overdue_receivables, 2),
                "invoice_count": total_invoices,
                "paid_count": paid_invoices,
                "overdue_count": overdue_invoices
            },
            "payables": {
                "total": round(total_payables, 2),
                "current": round(current_payables, 2),
                "overdue": round(overdue_payables, 2),
                "bill_count": total_bills,
                "paid_count": paid_bills
            },
            "as_of": today.isoformat()
        }
    }


@router.get("/cash-flow")
async def get_cash_flow(request: Request, period: str = "fiscal_year"):
    """
    Get cash flow data for chart visualization
    Returns monthly incoming/outgoing cash
    """
    org_id = await get_org_id(request)
    
    today = datetime.now(timezone.utc)
    
    # Return empty cash flow if no org context
    if not org_id:
        return {
            "code": 0,
            "cash_flow": {
                "period": period,
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
                "opening_balance": 0,
                "total_incoming": 0,
                "total_outgoing": 0,
                "closing_balance": 0,
                "monthly_data": [],
                "org_missing": True
            }
        }
    
    # Determine date range based on period
    if period == "fiscal_year":
        # Indian fiscal year: April to March
        if today.month >= 4:
            start_date = datetime(today.year, 4, 1, tzinfo=timezone.utc)
            end_date = datetime(today.year + 1, 3, 31, tzinfo=timezone.utc)
        else:
            start_date = datetime(today.year - 1, 4, 1, tzinfo=timezone.utc)
            end_date = datetime(today.year, 3, 31, tzinfo=timezone.utc)
    elif period == "last_12_months":
        start_date = today - relativedelta(months=12)
        end_date = today
    else:
        start_date = today - relativedelta(months=6)
        end_date = today
    
    # Initialize monthly data
    monthly_data = {}
    current = start_date
    while current <= end_date:
        month_key = current.strftime("%Y-%m")
        monthly_data[month_key] = {
            "month": current.strftime("%b %Y"),
            "month_short": current.strftime("%b"),
            "year": current.year,
            "incoming": 0,
            "outgoing": 0,
            "net": 0
        }
        current += relativedelta(months=1)
    
    # Calculate incoming (payments received)
    payments_cursor = db.customerpayments.find({
        "organization_id": org_id,
        "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }, {"_id": 0, "amount": 1, "date": 1})
    
    async for payment in payments_cursor:
        try:
            date_str = payment.get("date", "")
            if date_str:
                if isinstance(date_str, str):
                    payment_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    payment_date = date_str
                month_key = payment_date.strftime("%Y-%m")
                if month_key in monthly_data:
                    monthly_data[month_key]["incoming"] += float(payment.get("amount", 0))
        except:
            pass
    
    # Also add from invoices marked as paid
    paid_invoices_cursor = db.invoices.find({
        "organization_id": org_id,
        "status": "paid"
    }, {"_id": 0, "total": 1, "last_modified_time": 1, "invoice_date": 1})
    
    async for invoice in paid_invoices_cursor:
        try:
            date_str = invoice.get("last_modified_time") or invoice.get("invoice_date", "")
            if date_str:
                if isinstance(date_str, str):
                    inv_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    inv_date = date_str
                month_key = inv_date.strftime("%Y-%m")
                if month_key in monthly_data:
                    monthly_data[month_key]["incoming"] += float(invoice.get("total", 0))
        except:
            pass
    
    # Calculate outgoing (expenses + vendor payments)
    expenses_cursor = db.expenses.find({
        "organization_id": org_id,
        "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }, {"_id": 0, "amount": 1, "total": 1, "date": 1})
    
    async for expense in expenses_cursor:
        try:
            date_str = expense.get("date", "")
            if date_str:
                if isinstance(date_str, str):
                    expense_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    expense_date = date_str
                month_key = expense_date.strftime("%Y-%m")
                if month_key in monthly_data:
                    monthly_data[month_key]["outgoing"] += float(expense.get("amount") or expense.get("total") or 0)
        except:
            pass
    
    # Calculate net for each month
    running_balance = 0
    for month_key in sorted(monthly_data.keys()):
        monthly_data[month_key]["net"] = monthly_data[month_key]["incoming"] - monthly_data[month_key]["outgoing"]
        running_balance += monthly_data[month_key]["net"]
        monthly_data[month_key]["running_balance"] = round(running_balance, 2)
        monthly_data[month_key]["incoming"] = round(monthly_data[month_key]["incoming"], 2)
        monthly_data[month_key]["outgoing"] = round(monthly_data[month_key]["outgoing"], 2)
        monthly_data[month_key]["net"] = round(monthly_data[month_key]["net"], 2)
    
    # Calculate totals
    total_incoming = sum(m["incoming"] for m in monthly_data.values())
    total_outgoing = sum(m["outgoing"] for m in monthly_data.values())
    
    return {
        "code": 0,
        "cash_flow": {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "opening_balance": 0,  # Would need bank integration
            "total_incoming": round(total_incoming, 2),
            "total_outgoing": round(total_outgoing, 2),
            "closing_balance": round(total_incoming - total_outgoing, 2),
            "monthly_data": list(monthly_data.values())
        }
    }


@router.get("/income-expense")
async def get_income_expense(request: Request, period: str = "fiscal_year", method: str = "accrual"):
    """
    Get income vs expense comparison data
    Supports accrual and cash basis
    """
    org_id = await get_org_id(request)
    
    # Return empty if no org context
    if not org_id:
        return {
            "code": 0,
            "income_expense": {
                "period": period,
                "method": method,
                "total_income": 0,
                "total_expense": 0,
                "net_profit": 0,
                "monthly_data": [],
                "org_missing": True
            }
        }
    
    today = datetime.now(timezone.utc)
    
    # Determine date range
    if period == "fiscal_year":
        if today.month >= 4:
            start_date = datetime(today.year, 4, 1, tzinfo=timezone.utc)
            end_date = datetime(today.year + 1, 3, 31, tzinfo=timezone.utc)
        else:
            start_date = datetime(today.year - 1, 4, 1, tzinfo=timezone.utc)
            end_date = datetime(today.year, 3, 31, tzinfo=timezone.utc)
    else:
        start_date = today - relativedelta(months=12)
        end_date = today
    
    # Initialize monthly data
    monthly_data = {}
    current = start_date
    while current <= end_date:
        month_key = current.strftime("%Y-%m")
        monthly_data[month_key] = {
            "month": current.strftime("%b"),
            "year": current.year,
            "income": 0,
            "expense": 0
        }
        current += relativedelta(months=1)
    
    # Calculate income from invoices
    if method == "accrual":
        # Accrual: use invoice date
        invoices_cursor = db.invoices.find({
            "organization_id": org_id,
            "status": {"$ne": "void"}
        }, {"_id": 0, "total": 1, "invoice_date": 1, "date": 1})
    else:
        # Cash: use payment date
        invoices_cursor = db.invoices.find({
            "organization_id": org_id,
            "status": "paid"
        }, {"_id": 0, "total": 1, "last_modified_time": 1})
    
    async for invoice in invoices_cursor:
        try:
            if method == "accrual":
                date_str = invoice.get("invoice_date") or invoice.get("date", "")
            else:
                date_str = invoice.get("last_modified_time", "")
            
            if date_str:
                if isinstance(date_str, str):
                    inv_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    inv_date = date_str
                month_key = inv_date.strftime("%Y-%m")
                if month_key in monthly_data:
                    monthly_data[month_key]["income"] += float(invoice.get("total", 0))
        except:
            pass
    
    # Calculate expenses
    expenses_cursor = db.expenses.find({
        "organization_id": org_id
    }, {"_id": 0, "amount": 1, "total": 1, "date": 1})
    
    async for expense in expenses_cursor:
        try:
            date_str = expense.get("date", "")
            if date_str:
                if isinstance(date_str, str):
                    expense_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    expense_date = date_str
                month_key = expense_date.strftime("%Y-%m")
                if month_key in monthly_data:
                    monthly_data[month_key]["expense"] += float(expense.get("amount") or expense.get("total") or 0)
        except:
            pass
    
    # Round values
    for month_key in monthly_data:
        monthly_data[month_key]["income"] = round(monthly_data[month_key]["income"], 2)
        monthly_data[month_key]["expense"] = round(monthly_data[month_key]["expense"], 2)
    
    total_income = sum(m["income"] for m in monthly_data.values())
    total_expense = sum(m["expense"] for m in monthly_data.values())
    
    return {
        "code": 0,
        "income_expense": {
            "period": period,
            "method": method,
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_profit": round(total_income - total_expense, 2),
            "monthly_data": list(monthly_data.values())
        }
    }


@router.get("/top-expenses")
async def get_top_expenses(request: Request, period: str = "fiscal_year", limit: int = 6):
    """
    Get top expense categories for pie chart
    """
    org_id = await get_org_id(request)
    
    # Return empty if no org context
    if not org_id:
        return {
            "code": 0,
            "top_expenses": {
                "period": period,
                "total": 0,
                "categories": [],
                "org_missing": True
            }
        }
    
    today = datetime.now(timezone.utc)
    
    # Determine date range
    if period == "fiscal_year":
        if today.month >= 4:
            start_date = datetime(today.year, 4, 1, tzinfo=timezone.utc)
        else:
            start_date = datetime(today.year - 1, 4, 1, tzinfo=timezone.utc)
    else:
        start_date = today - relativedelta(months=12)
    
    # Aggregate expenses by category
    category_totals = {}
    
    expenses_cursor = db.expenses.find({
        "organization_id": org_id
    }, {"_id": 0, "amount": 1, "total": 1, "category_name": 1, "account_name": 1, "expense_type": 1})
    
    async for expense in expenses_cursor:
        category = expense.get("category_name") or expense.get("account_name") or expense.get("expense_type") or "Others"
        amount = float(expense.get("amount") or expense.get("total") or 0)
        category_totals[category] = category_totals.get(category, 0) + amount
    
    # Sort and get top categories
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    top_categories = sorted_categories[:limit-1]
    
    # Combine remaining into "Others"
    others_total = sum(amount for _, amount in sorted_categories[limit-1:])
    if others_total > 0:
        top_categories.append(("Others", others_total))
    
    total_expenses = sum(amount for _, amount in top_categories)
    
    # Format for chart
    colors = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6", "#6B7280"]
    expense_data = []
    for i, (category, amount) in enumerate(top_categories):
        expense_data.append({
            "category": category,
            "amount": round(amount, 2),
            "percentage": round((amount / total_expenses * 100) if total_expenses > 0 else 0, 1),
            "color": colors[i % len(colors)]
        })
    
    return {
        "code": 0,
        "top_expenses": {
            "period": period,
            "total": round(total_expenses, 2),
            "categories": expense_data
        }
    }


@router.get("/bank-accounts")
async def get_bank_accounts(request: Request):
    """
    Get bank and credit card account summaries
    """
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID header required")
    
    # Get bank accounts from Zoho sync
    accounts = []
    accounts_cursor = db.bankaccounts.find({
        "organization_id": org_id
    }, {"_id": 0})
    
    async for account in accounts_cursor:
        accounts.append({
            "account_id": account.get("account_id") or account.get("zoho_account_id"),
            "account_name": account.get("account_name") or account.get("name"),
            "account_type": account.get("account_type", "bank"),
            "balance": float(account.get("balance") or account.get("bank_balance") or 0),
            "currency": account.get("currency_code", "INR"),
            "uncategorized_count": account.get("uncategorized_transactions", 0),
            "last_sync": account.get("last_sync") or account.get("last_modified_time")
        })
    
    # If no accounts, show placeholder
    if not accounts:
        accounts = [
            {
                "account_id": "default",
                "account_name": "Primary Bank Account",
                "account_type": "bank",
                "balance": 0,
                "currency": "INR",
                "uncategorized_count": 0,
                "last_sync": None
            }
        ]
    
    total_balance = sum(a["balance"] for a in accounts)
    total_uncategorized = sum(a["uncategorized_count"] for a in accounts)
    
    return {
        "code": 0,
        "bank_accounts": {
            "accounts": accounts,
            "total_balance": round(total_balance, 2),
            "total_uncategorized": total_uncategorized
        }
    }


@router.get("/projects-watchlist")
async def get_projects_watchlist(request: Request, limit: int = 5):
    """
    Get active projects/work orders for watchlist
    """
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID header required")
    
    projects = []
    
    # Get active tickets/work orders
    tickets_cursor = db.tickets.find({
        "organization_id": org_id,
        "status": {"$in": ["open", "in_progress", "technician_assigned"]}
    }, {"_id": 0}).sort("created_at", -1).limit(limit)
    
    async for ticket in tickets_cursor:
        unbilled_amount = 0
        
        # Calculate unbilled from line items
        line_items = ticket.get("line_items") or ticket.get("estimated_items") or []
        for item in line_items:
            if not item.get("billed"):
                unbilled_amount += float(item.get("amount") or item.get("total") or 0)
        
        projects.append({
            "project_id": ticket.get("ticket_id"),
            "project_name": ticket.get("issue") or f"Ticket {ticket.get('ticket_id', '')[:8]}",
            "customer_name": ticket.get("customer_name", "N/A"),
            "vehicle_number": ticket.get("vehicle_number"),
            "status": ticket.get("status"),
            "unbilled_amount": round(unbilled_amount, 2),
            "unbilled_hours": ticket.get("unbilled_hours", 0),
            "created_at": ticket.get("created_at")
        })
    
    return {
        "code": 0,
        "projects": projects,
        "total_count": len(projects)
    }


@router.get("/quick-stats")
async def get_quick_stats(request: Request):
    """
    Get quick statistics for dashboard header
    """
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID header required")
    
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # This month's stats
    invoices_this_month = await db.invoices.count_documents({
        "organization_id": org_id,
        "invoice_date": {"$gte": month_start.isoformat()}
    })
    
    estimates_this_month = await db.estimates.count_documents({
        "organization_id": org_id,
        "estimate_date": {"$gte": month_start.isoformat()}
    })
    
    # Active items
    active_customers = await db.contacts.count_documents({
        "organization_id": org_id,
        "contact_type": "customer",
        "status": {"$ne": "inactive"}
    })
    
    active_vendors = await db.contacts.count_documents({
        "organization_id": org_id,
        "contact_type": "vendor",
        "status": {"$ne": "inactive"}
    })
    
    total_items = await db.items.count_documents({"organization_id": org_id})
    
    return {
        "code": 0,
        "quick_stats": {
            "invoices_this_month": invoices_this_month,
            "estimates_this_month": estimates_this_month,
            "active_customers": active_customers,
            "active_vendors": active_vendors,
            "total_items": total_items,
            "month": today.strftime("%B %Y")
        }
    }
