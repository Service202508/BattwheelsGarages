# Advanced Reports Module - Comprehensive Analytics with Chart Data
# Provides data formatted for chart visualization in frontend

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from calendar import monthrange
import motor.motor_asyncio
import os

from core.subscriptions.entitlement import require_feature

router = APIRouter(prefix="/reports-advanced", tags=["Advanced Reports"])

# ==================== ROUTER-LEVEL ENTITLEMENT ====================
# All advanced report routes require the advanced_reports feature
_adv_reports_dep = [Depends(require_feature("advanced_reports"))]

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
invoices_collection = db["invoices_enhanced"]
estimates_collection = db["estimates_enhanced"]
salesorders_collection = db["salesorders_enhanced"]
contacts_collection = db["contacts_enhanced"]
payments_collection = db["invoice_payments"]
expenses_collection = db["expenses"]
items_collection = db["items"]

def round_currency(val: float) -> float:
    return round(val, 2)

# ========================= REVENUE REPORTS =========================

@router.get("/revenue/monthly")
async def get_monthly_revenue(year: int = None, months: int = 12):
    """Get monthly revenue data for charts"""
    if not year:
        year = datetime.now(timezone.utc).year
    
    # Calculate date range
    current_month = datetime.now(timezone.utc).month
    
    results = []
    for i in range(months):
        # Calculate month/year going backwards
        month = current_month - i
        y = year
        while month <= 0:
            month += 12
            y -= 1
        
        start_date = f"{y}-{month:02d}-01"
        _, last_day = monthrange(y, month)
        end_date = f"{y}-{month:02d}-{last_day}"
        
        # Get invoices
        pipeline = [
            {"$match": {
                "invoice_date": {"$gte": start_date, "$lte": end_date},
                "status": {"$nin": ["draft", "void"]}
            }},
            {"$group": {
                "_id": None,
                "invoiced": {"$sum": "$grand_total"},
                "collected": {"$sum": {"$subtract": ["$grand_total", "$balance_due"]}},
                "count": {"$sum": 1}
            }}
        ]
        
        data = await invoices_collection.aggregate(pipeline).to_list(1)
        values = data[0] if data else {"invoiced": 0, "collected": 0, "count": 0}
        
        results.append({
            "month": f"{y}-{month:02d}",
            "month_name": datetime(y, month, 1).strftime("%b %Y"),
            "invoiced": round_currency(values.get("invoiced", 0)),
            "collected": round_currency(values.get("collected", 0)),
            "invoice_count": values.get("count", 0)
        })
    
    results.reverse()  # Chronological order
    
    return {
        "code": 0,
        "chart_type": "bar",
        "data": results,
        "labels": [r["month_name"] for r in results],
        "datasets": [
            {"label": "Invoiced", "data": [r["invoiced"] for r in results], "color": "#3B82F6"},
            {"label": "Collected", "data": [r["collected"] for r in results], "color": "#22C55E"}
        ]
    }

@router.get("/revenue/quarterly")
async def get_quarterly_revenue(year: int = None):
    """Get quarterly revenue for charts"""
    if not year:
        year = datetime.now(timezone.utc).year
    
    quarters = [
        {"q": "Q1", "start": f"{year}-01-01", "end": f"{year}-03-31"},
        {"q": "Q2", "start": f"{year}-04-01", "end": f"{year}-06-30"},
        {"q": "Q3", "start": f"{year}-07-01", "end": f"{year}-09-30"},
        {"q": "Q4", "start": f"{year}-10-01", "end": f"{year}-12-31"}
    ]
    
    results = []
    for q in quarters:
        pipeline = [
            {"$match": {
                "invoice_date": {"$gte": q["start"], "$lte": q["end"]},
                "status": {"$nin": ["draft", "void"]}
            }},
            {"$group": {
                "_id": None,
                "invoiced": {"$sum": "$grand_total"},
                "collected": {"$sum": {"$subtract": ["$grand_total", "$balance_due"]}},
                "outstanding": {"$sum": "$balance_due"}
            }}
        ]
        
        data = await invoices_collection.aggregate(pipeline).to_list(1)
        values = data[0] if data else {"invoiced": 0, "collected": 0, "outstanding": 0}
        
        results.append({
            "quarter": q["q"],
            "year": year,
            "invoiced": round_currency(values.get("invoiced", 0)),
            "collected": round_currency(values.get("collected", 0)),
            "outstanding": round_currency(values.get("outstanding", 0))
        })
    
    return {
        "code": 0,
        "chart_type": "bar",
        "year": year,
        "data": results,
        "labels": [r["quarter"] for r in results],
        "datasets": [
            {"label": "Invoiced", "data": [r["invoiced"] for r in results], "color": "#3B82F6"},
            {"label": "Collected", "data": [r["collected"] for r in results], "color": "#22C55E"},
            {"label": "Outstanding", "data": [r["outstanding"] for r in results], "color": "#EF4444"}
        ]
    }

@router.get("/revenue/yearly-comparison")
async def get_yearly_comparison(years: int = 3):
    """Compare revenue across years"""
    current_year = datetime.now(timezone.utc).year
    results = []
    
    for y in range(current_year - years + 1, current_year + 1):
        pipeline = [
            {"$match": {
                "invoice_date": {"$gte": f"{y}-01-01", "$lte": f"{y}-12-31"},
                "status": {"$nin": ["draft", "void"]}
            }},
            {"$group": {
                "_id": None,
                "total_invoiced": {"$sum": "$grand_total"},
                "total_collected": {"$sum": {"$subtract": ["$grand_total", "$balance_due"]}},
                "invoice_count": {"$sum": 1}
            }}
        ]
        
        data = await invoices_collection.aggregate(pipeline).to_list(1)
        values = data[0] if data else {"total_invoiced": 0, "total_collected": 0, "invoice_count": 0}
        
        results.append({
            "year": y,
            "invoiced": round_currency(values.get("total_invoiced", 0)),
            "collected": round_currency(values.get("total_collected", 0)),
            "invoices": values.get("invoice_count", 0)
        })
    
    return {
        "code": 0,
        "chart_type": "bar",
        "data": results,
        "labels": [str(r["year"]) for r in results]
    }

# ========================= RECEIVABLES REPORTS =========================

@router.get("/receivables/aging")
async def get_receivables_aging_chart():
    """Get receivables aging for pie/bar chart"""
    today = datetime.now(timezone.utc).date()
    
    invoices = await invoices_collection.find(
        {"status": {"$in": ["sent", "overdue", "partially_paid"]}, "balance_due": {"$gt": 0}},
        {"_id": 0, "due_date": 1, "balance_due": 1}
    ).to_list(2000)
    
    buckets = {
        "current": {"label": "Current", "amount": 0, "count": 0, "color": "#22C55E"},
        "1_30": {"label": "1-30 Days", "amount": 0, "count": 0, "color": "#F59E0B"},
        "31_60": {"label": "31-60 Days", "amount": 0, "count": 0, "color": "#F97316"},
        "61_90": {"label": "61-90 Days", "amount": 0, "count": 0, "color": "#EF4444"},
        "over_90": {"label": "90+ Days", "amount": 0, "count": 0, "color": "#991B1B"}
    }
    
    for inv in invoices:
        due_date_str = inv.get("due_date", "")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
            days = (today - due_date).days
            balance = inv.get("balance_due", 0)
            
            if days <= 0:
                bucket = "current"
            elif days <= 30:
                bucket = "1_30"
            elif days <= 60:
                bucket = "31_60"
            elif days <= 90:
                bucket = "61_90"
            else:
                bucket = "over_90"
            
            buckets[bucket]["amount"] += balance
            buckets[bucket]["count"] += 1
        except:
            continue
    
    # Format for chart
    chart_data = [
        {"bucket": k, "label": v["label"], "amount": round_currency(v["amount"]), "count": v["count"], "color": v["color"]}
        for k, v in buckets.items()
    ]
    
    total = sum(b["amount"] for b in chart_data)
    
    return {
        "code": 0,
        "chart_type": "pie",
        "data": chart_data,
        "labels": [b["label"] for b in chart_data],
        "values": [b["amount"] for b in chart_data],
        "colors": [b["color"] for b in chart_data],
        "total_outstanding": round_currency(total)
    }

@router.get("/receivables/trend")
async def get_receivables_trend(months: int = 6):
    """Get receivables trend over time"""
    current = datetime.now(timezone.utc)
    results = []
    
    for i in range(months):
        month = current.month - i
        year = current.year
        while month <= 0:
            month += 12
            year -= 1
        
        _, last_day = monthrange(year, month)
        as_of_date = f"{year}-{month:02d}-{last_day}"
        
        # Get outstanding as of end of month
        pipeline = [
            {"$match": {
                "invoice_date": {"$lte": as_of_date},
                "status": {"$nin": ["draft", "void", "paid"]}
            }},
            {"$group": {
                "_id": None,
                "total_outstanding": {"$sum": "$balance_due"}
            }}
        ]
        
        data = await invoices_collection.aggregate(pipeline).to_list(1)
        outstanding = data[0].get("total_outstanding", 0) if data else 0
        
        results.append({
            "month": f"{year}-{month:02d}",
            "month_name": datetime(year, month, 1).strftime("%b %Y"),
            "outstanding": round_currency(outstanding)
        })
    
    results.reverse()
    
    return {
        "code": 0,
        "chart_type": "line",
        "data": results,
        "labels": [r["month_name"] for r in results],
        "values": [r["outstanding"] for r in results]
    }

# ========================= CUSTOMER REPORTS =========================

@router.get("/customers/top-revenue")
async def get_top_customers_by_revenue(limit: int = 10):
    """Get top customers by revenue for chart"""
    pipeline = [
        {"$match": {"status": {"$nin": ["draft", "void"]}}},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "total_revenue": {"$sum": "$grand_total"},
            "invoice_count": {"$sum": 1}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": limit}
    ]
    
    results = await invoices_collection.aggregate(pipeline).to_list(limit)
    
    chart_data = [
        {
            "customer_id": r["_id"],
            "name": r.get("customer_name", "Unknown"),
            "revenue": round_currency(r.get("total_revenue", 0)),
            "invoices": r.get("invoice_count", 0)
        }
        for r in results
    ]
    
    return {
        "code": 0,
        "chart_type": "horizontal_bar",
        "data": chart_data,
        "labels": [c["name"][:20] for c in chart_data],
        "values": [c["revenue"] for c in chart_data]
    }

@router.get("/customers/top-outstanding")
async def get_top_customers_by_outstanding(limit: int = 10):
    """Get customers with highest outstanding"""
    pipeline = [
        {"$match": {"status": {"$in": ["sent", "overdue", "partially_paid"]}, "balance_due": {"$gt": 0}}},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "total_outstanding": {"$sum": "$balance_due"},
            "invoice_count": {"$sum": 1}
        }},
        {"$sort": {"total_outstanding": -1}},
        {"$limit": limit}
    ]
    
    results = await invoices_collection.aggregate(pipeline).to_list(limit)
    
    chart_data = [
        {
            "customer_id": r["_id"],
            "name": r.get("customer_name", "Unknown"),
            "outstanding": round_currency(r.get("total_outstanding", 0)),
            "invoices": r.get("invoice_count", 0)
        }
        for r in results
    ]
    
    return {
        "code": 0,
        "chart_type": "horizontal_bar",
        "data": chart_data,
        "labels": [c["name"][:20] for c in chart_data],
        "values": [c["outstanding"] for c in chart_data]
    }

@router.get("/customers/acquisition")
async def get_customer_acquisition(months: int = 12):
    """Get new customer acquisition over time"""
    current = datetime.now(timezone.utc)
    results = []
    
    for i in range(months):
        month = current.month - i
        year = current.year
        while month <= 0:
            month += 12
            year -= 1
        
        start = f"{year}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end = f"{year}-{month:02d}-{last_day}"
        
        new_customers = await contacts_collection.count_documents({
            "contact_type": {"$in": ["customer", "both"]},
            "created_time": {"$gte": start, "$lte": end}
        })
        
        results.append({
            "month": f"{year}-{month:02d}",
            "month_name": datetime(year, month, 1).strftime("%b %Y"),
            "new_customers": new_customers
        })
    
    results.reverse()
    
    return {
        "code": 0,
        "chart_type": "line",
        "data": results,
        "labels": [r["month_name"] for r in results],
        "values": [r["new_customers"] for r in results],
        "total_new": sum(r["new_customers"] for r in results)
    }

# ========================= SALES FUNNEL =========================

@router.get("/sales/funnel")
async def get_sales_funnel():
    """Get sales funnel data (estimates -> orders -> invoices)"""
    # Estimates
    total_estimates = await estimates_collection.count_documents({"status": {"$ne": "draft"}})
    estimates_value = 0
    est_data = await estimates_collection.aggregate([
        {"$match": {"status": {"$ne": "draft"}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]).to_list(1)
    if est_data:
        estimates_value = est_data[0].get("total", 0)
    
    accepted_estimates = await estimates_collection.count_documents({"status": "accepted"})
    
    # Sales Orders
    total_orders = await salesorders_collection.count_documents({"status": {"$nin": ["draft", "void"]}})
    orders_value = 0
    so_data = await salesorders_collection.aggregate([
        {"$match": {"status": {"$nin": ["draft", "void"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]).to_list(1)
    if so_data:
        orders_value = so_data[0].get("total", 0)
    
    # Invoices
    total_invoices = await invoices_collection.count_documents({"status": {"$nin": ["draft", "void"]}})
    invoices_value = 0
    inv_data = await invoices_collection.aggregate([
        {"$match": {"status": {"$nin": ["draft", "void"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]).to_list(1)
    if inv_data:
        invoices_value = inv_data[0].get("total", 0)
    
    # Paid
    paid_invoices = await invoices_collection.count_documents({"status": "paid"})
    paid_value = 0
    paid_data = await invoices_collection.aggregate([
        {"$match": {"status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]).to_list(1)
    if paid_data:
        paid_value = paid_data[0].get("total", 0)
    
    funnel = [
        {"stage": "Estimates", "count": total_estimates, "value": round_currency(estimates_value), "color": "#94A3B8"},
        {"stage": "Accepted", "count": accepted_estimates, "value": round_currency(estimates_value * 0.6), "color": "#60A5FA"},
        {"stage": "Orders", "count": total_orders, "value": round_currency(orders_value), "color": "#34D399"},
        {"stage": "Invoiced", "count": total_invoices, "value": round_currency(invoices_value), "color": "#FBBF24"},
        {"stage": "Paid", "count": paid_invoices, "value": round_currency(paid_value), "color": "#22C55E"}
    ]
    
    # Calculate conversion rates
    if total_estimates > 0:
        funnel[1]["conversion"] = round(accepted_estimates / total_estimates * 100, 1)
    if accepted_estimates > 0:
        funnel[2]["conversion"] = round(total_orders / accepted_estimates * 100, 1)
    if total_orders > 0:
        funnel[3]["conversion"] = round(total_invoices / total_orders * 100, 1)
    if total_invoices > 0:
        funnel[4]["conversion"] = round(paid_invoices / total_invoices * 100, 1)
    
    return {
        "code": 0,
        "chart_type": "funnel",
        "data": funnel,
        "labels": [f["stage"] for f in funnel],
        "values": [f["value"] for f in funnel],
        "counts": [f["count"] for f in funnel]
    }

# ========================= INVOICE STATUS =========================

@router.get("/invoices/status-distribution")
async def get_invoice_status_distribution():
    """Get invoice status distribution for pie chart"""
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "value": {"$sum": "$grand_total"}
        }}
    ]
    
    results = await invoices_collection.aggregate(pipeline).to_list(10)
    
    status_colors = {
        "draft": "#9CA3AF",
        "sent": "#3B82F6",
        "viewed": "#8B5CF6",
        "partially_paid": "#F59E0B",
        "paid": "#22C55E",
        "overdue": "#EF4444",
        "void": "#6B7280",
        "written_off": "#F97316"
    }
    
    status_labels = {
        "draft": "Draft",
        "sent": "Sent",
        "viewed": "Viewed",
        "partially_paid": "Partially Paid",
        "paid": "Paid",
        "overdue": "Overdue",
        "void": "Void",
        "written_off": "Written Off"
    }
    
    chart_data = [
        {
            "status": r["_id"],
            "label": status_labels.get(r["_id"], r["_id"]),
            "count": r["count"],
            "value": round_currency(r.get("value", 0)),
            "color": status_colors.get(r["_id"], "#9CA3AF")
        }
        for r in results if r["_id"]
    ]
    
    return {
        "code": 0,
        "chart_type": "doughnut",
        "data": chart_data,
        "labels": [d["label"] for d in chart_data],
        "values": [d["count"] for d in chart_data],
        "colors": [d["color"] for d in chart_data]
    }

# ========================= PAYMENT TRENDS =========================

@router.get("/payments/trend")
async def get_payment_trend(months: int = 6):
    """Get payment collection trend"""
    current = datetime.now(timezone.utc)
    results = []
    
    for i in range(months):
        month = current.month - i
        year = current.year
        while month <= 0:
            month += 12
            year -= 1
        
        start = f"{year}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end = f"{year}-{month:02d}-{last_day}"
        
        pipeline = [
            {"$match": {"payment_date": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": None,
                "total_collected": {"$sum": "$amount"},
                "payment_count": {"$sum": 1}
            }}
        ]
        
        data = await payments_collection.aggregate(pipeline).to_list(1)
        values = data[0] if data else {"total_collected": 0, "payment_count": 0}
        
        results.append({
            "month": f"{year}-{month:02d}",
            "month_name": datetime(year, month, 1).strftime("%b %Y"),
            "collected": round_currency(values.get("total_collected", 0)),
            "count": values.get("payment_count", 0)
        })
    
    results.reverse()
    
    return {
        "code": 0,
        "chart_type": "line",
        "data": results,
        "labels": [r["month_name"] for r in results],
        "values": [r["collected"] for r in results],
        "total_collected": round_currency(sum(r["collected"] for r in results))
    }

@router.get("/payments/by-mode")
async def get_payments_by_mode():
    """Get payment distribution by mode"""
    pipeline = [
        {"$group": {
            "_id": "$payment_mode",
            "count": {"$sum": 1},
            "total": {"$sum": "$amount"}
        }},
        {"$sort": {"total": -1}}
    ]
    
    results = await payments_collection.aggregate(pipeline).to_list(10)
    
    mode_colors = {
        "cash": "#22C55E",
        "bank_transfer": "#3B82F6",
        "cheque": "#8B5CF6",
        "card": "#F59E0B",
        "upi": "#EC4899",
        "online": "#14B8A6"
    }
    
    chart_data = [
        {
            "mode": r["_id"] or "Other",
            "count": r["count"],
            "total": round_currency(r.get("total", 0)),
            "color": mode_colors.get(r["_id"], "#9CA3AF")
        }
        for r in results
    ]
    
    return {
        "code": 0,
        "chart_type": "pie",
        "data": chart_data,
        "labels": [d["mode"].replace("_", " ").title() for d in chart_data],
        "values": [d["total"] for d in chart_data],
        "colors": [d["color"] for d in chart_data]
    }

# ========================= DASHBOARD SUMMARY =========================

@router.get("/dashboard-summary")
async def get_dashboard_summary():
    """Get comprehensive dashboard summary with KPIs"""
    today = datetime.now(timezone.utc)
    first_of_month = today.replace(day=1).date().isoformat()
    first_of_year = today.replace(month=1, day=1).date().isoformat()
    
    # This month revenue
    month_revenue = await invoices_collection.aggregate([
        {"$match": {"invoice_date": {"$gte": first_of_month}, "status": {"$nin": ["draft", "void"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    
    # Year to date
    ytd_revenue = await invoices_collection.aggregate([
        {"$match": {"invoice_date": {"$gte": first_of_year}, "status": {"$nin": ["draft", "void"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]).to_list(1)
    
    # Total outstanding
    outstanding = await invoices_collection.aggregate([
        {"$match": {"status": {"$in": ["sent", "overdue", "partially_paid"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance_due"}}}
    ]).to_list(1)
    
    # Overdue
    overdue = await invoices_collection.aggregate([
        {"$match": {"status": "overdue"}},
        {"$group": {"_id": None, "total": {"$sum": "$balance_due"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    
    # Active customers
    active_customers = await contacts_collection.count_documents({
        "contact_type": {"$in": ["customer", "both"]},
        "is_active": True
    })
    
    # Pending estimates
    pending_estimates = await estimates_collection.count_documents({"status": "sent"})
    
    return {
        "code": 0,
        "summary": {
            "this_month": {
                "revenue": round_currency(month_revenue[0].get("total", 0) if month_revenue else 0),
                "invoices": month_revenue[0].get("count", 0) if month_revenue else 0
            },
            "year_to_date": {
                "revenue": round_currency(ytd_revenue[0].get("total", 0) if ytd_revenue else 0)
            },
            "receivables": {
                "total_outstanding": round_currency(outstanding[0].get("total", 0) if outstanding else 0),
                "overdue_amount": round_currency(overdue[0].get("total", 0) if overdue else 0),
                "overdue_count": overdue[0].get("count", 0) if overdue else 0
            },
            "customers": {
                "active": active_customers
            },
            "pipeline": {
                "pending_estimates": pending_estimates
            }
        }
    }
