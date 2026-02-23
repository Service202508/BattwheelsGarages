"""
Data Insights API Routes
========================
Aggregated business intelligence for the Data Insights module.

All endpoints:
  - Scoped to current org via TenantContext
  - Accept ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD (default: current month)
  - Return real aggregated data from MongoDB
"""
from fastapi import APIRouter, Request, Query
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["Data Insights"])

_db = None


def init_insights_router(db):
    global _db
    _db = db
    return router


def get_db():
    if _db is None:
        from server import db
        return db
    return _db


async def get_org_id(request: Request) -> str:
    ctx = getattr(request.state, "tenant_context", None)
    if ctx and getattr(ctx, "org_id", None):
        return ctx.org_id
    user = getattr(request.state, "user", None)
    if user:
        return user.get("organization_id", "")
    return ""


def get_date_range(date_from: Optional[str], date_to: Optional[str]):
    """Returns (start_date, end_date, prev_start_date, prev_end_date) as YYYY-MM-DD strings"""
    now = datetime.now(timezone.utc)
    if date_from:
        try:
            start = datetime.fromisoformat(date_from.replace("Z", "+00:00")).date()
        except Exception:
            start = now.date().replace(day=1)
    else:
        start = now.date().replace(day=1)

    if date_to:
        try:
            end = datetime.fromisoformat(date_to.replace("Z", "+00:00")).date()
        except Exception:
            end = now.date()
    else:
        end = now.date()

    period_days = max((end - start).days, 1)
    prev_end = start
    prev_start = start - timedelta(days=period_days)

    return start.isoformat(), end.isoformat(), prev_start.isoformat(), prev_end.isoformat()


def pct_change(curr, prev):
    if prev is None or prev == 0:
        return None if (curr is None or curr == 0) else 100.0
    return round((curr - prev) / prev * 100, 1)


def safe(val, default=0):
    return val if val is not None else default


# ======================== REVENUE INTELLIGENCE ========================

@router.get("/revenue")
async def get_revenue_insights(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    db = get_db()
    org_id = await get_org_id(request)
    start, end, prev_start, prev_end = get_date_range(date_from, date_to)

    def inv_match(s, e, extra=None):
        q = {
            "organization_id": org_id,
            "status": {"$ne": "void"},
            "invoice_date": {"$gte": s, "$lte": e},
        }
        if extra:
            q.update(extra)
        return q

    match = inv_match(start, end)
    prev_match = inv_match(prev_start, prev_end)

    # Current period paid revenue
    paid_agg = await db.invoices_enhanced.aggregate([
        {"$match": {**match, "status": "paid"}},
        {"$group": {"_id": None, "revenue": {"$sum": "$grand_total"}, "count": {"$sum": 1}}},
    ]).to_list(1)
    paid_data = paid_agg[0] if paid_agg else {}
    revenue = safe(paid_data.get("revenue"), 0)
    paid_count = safe(paid_data.get("count"), 0)

    # Previous period
    prev_agg = await db.invoices_enhanced.aggregate([
        {"$match": {**prev_match, "status": "paid"}},
        {"$group": {"_id": None, "revenue": {"$sum": "$grand_total"}}},
    ]).to_list(1)
    prev_revenue = safe(prev_agg[0]["revenue"] if prev_agg else 0)

    # Previous avg invoice
    prev_paid_count = 0
    if prev_agg:
        prev_paid_count_agg = await db.invoices_enhanced.count_documents({**prev_match, "status": "paid"})
        prev_paid_count = prev_paid_count_agg

    # Total invoices (for collection rate)
    total_count = await db.invoices_enhanced.count_documents(match)

    # Outstanding AR
    ar_agg = await db.invoices_enhanced.aggregate([
        {"$match": inv_match(start, end, {"status": {"$in": ["sent", "overdue", "partially_paid"]}})},
        {"$group": {"_id": None, "ar": {"$sum": {"$ifNull": ["$balance_due", "$grand_total"]}}}},
    ]).to_list(1)
    ar = safe(ar_agg[0]["ar"] if ar_agg else 0)

    # Daily revenue trend
    trend_agg = await db.invoices_enhanced.aggregate([
        {"$match": {**match, "status": "paid"}},
        {"$group": {"_id": "$invoice_date", "revenue": {"$sum": "$grand_total"}}},
        {"$sort": {"_id": 1}},
    ]).to_list(200)

    # Revenue by service type (lookup item_type from items)
    type_agg = await db.invoices_enhanced.aggregate([
        {"$match": {**match, "status": "paid", "line_items": {"$exists": True, "$ne": []}}},
        {"$unwind": "$line_items"},
        {"$lookup": {
            "from": "items",
            "localField": "line_items.item_id",
            "foreignField": "item_id",
            "as": "item_info",
        }},
        {"$project": {
            "amount": "$line_items.amount",
            "item_type": {
                "$ifNull": [{"$arrayElemAt": ["$item_info.item_type", 0]}, "inventory"]
            },
        }},
        {"$group": {
            "_id": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$item_type", "service"]}, "then": "Labour"},
                        {"case": {"$eq": ["$item_type", "amc"]}, "then": "AMC"},
                    ],
                    "default": "Parts",
                }
            },
            "revenue": {"$sum": "$amount"},
        }},
        {"$sort": {"revenue": -1}},
    ]).to_list(10)

    collection_rate = round(paid_count / total_count * 100, 1) if total_count > 0 else 0
    avg_invoice = round(revenue / paid_count, 2) if paid_count > 0 else 0
    prev_avg = round(prev_revenue / prev_paid_count, 2) if prev_paid_count > 0 else 0

    return {
        "kpis": {
            "revenue": round(revenue, 2),
            "revenue_delta": pct_change(revenue, prev_revenue),
            "avg_invoice": avg_invoice,
            "avg_invoice_delta": pct_change(avg_invoice, prev_avg),
            "collection_rate": collection_rate,
            "ar": round(ar, 2),
            "paid_count": paid_count,
            "total_count": total_count,
        },
        "trend": [
            {"date": t["_id"], "revenue": round(t["revenue"], 2)}
            for t in trend_agg if t["_id"]
        ],
        "by_type": [
            {"type": t["_id"] or "Other", "revenue": round(t["revenue"], 2)}
            for t in type_agg if t["_id"]
        ],
    }


# ======================== WORKSHOP OPERATIONS ========================

@router.get("/operations")
async def get_operations_insights(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    db = get_db()
    org_id = await get_org_id(request)
    start, end, prev_start, prev_end = get_date_range(date_from, date_to)

    def tkt_match(s, e, extra=None):
        q = {
            "organization_id": org_id,
            "created_at": {"$gte": s + "T00:00:00", "$lte": e + "T23:59:59"},
        }
        if extra:
            q.update(extra)
        return q

    match = tkt_match(start, end)
    prev_match = tkt_match(prev_start, prev_end)
    closed_statuses = ["closed", "resolved"]

    total_count = await db.tickets.count_documents(match)
    closed_count = await db.tickets.count_documents(
        tkt_match(start, end, {"status": {"$in": closed_statuses}})
    )
    prev_closed = await db.tickets.count_documents(
        tkt_match(prev_start, prev_end, {"status": {"$in": closed_statuses}})
    )

    # Avg resolution time in hours
    res_agg = await db.tickets.aggregate([
        {"$match": {
            **tkt_match(start, end, {"status": {"$in": closed_statuses}}),
            "closed_at": {"$exists": True, "$ne": None},
        }},
        {"$project": {
            "hours": {
                "$divide": [
                    {"$subtract": [{"$toDate": "$closed_at"}, {"$toDate": "$created_at"}]},
                    3600000,
                ]
            }
        }},
        {"$match": {"hours": {"$gt": 0, "$lt": 720}}},  # ignore outliers > 30 days
        {"$group": {"_id": None, "avg": {"$avg": "$hours"}}},
    ]).to_list(1)
    avg_hours = round(res_agg[0]["avg"], 1) if res_agg else None

    # SLA compliance
    sla_total = await db.tickets.count_documents({
        **tkt_match(start, end, {"status": {"$in": closed_statuses}}),
        "sla_resolution_due_at": {"$exists": True, "$ne": None},
    })
    sla_ok = 0
    if sla_total > 0:
        sla_ok = await db.tickets.count_documents({
            **tkt_match(start, end, {"status": {"$in": closed_statuses}}),
            "sla_resolution_due_at": {"$exists": True, "$ne": None},
            "$expr": {"$lte": ["$closed_at", "$sla_resolution_due_at"]},
        })
    sla_rate = round(sla_ok / sla_total * 100, 1) if sla_total > 0 else None

    # First-time fix rate
    reopened = await db.tickets.count_documents(tkt_match(start, end, {"status": "reopened"}))
    first_fix = round((closed_count - reopened) / closed_count * 100, 1) if closed_count > 0 else None

    # Daily volume by status
    volume_agg = await db.tickets.aggregate([
        {"$match": match},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},
            "total": {"$sum": 1},
            "closed": {"$sum": {"$cond": [{"$in": ["$status", closed_statuses]}, 1, 0]}},
            "in_progress": {"$sum": {"$cond": [
                {"$in": ["$status", ["in_progress", "work_in_progress", "assigned", "technician_assigned"]]}, 1, 0
            ]}},
            "open": {"$sum": {"$cond": [{"$eq": ["$status", "open"]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]).to_list(200)

    # Vehicle type breakdown
    vehicle_agg = await db.tickets.aggregate([
        {"$match": match},
        {"$group": {"_id": "$vehicle_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]).to_list(20)

    return {
        "kpis": {
            "tickets_resolved": closed_count,
            "tickets_delta": pct_change(closed_count, prev_closed),
            "avg_resolution_hours": avg_hours,
            "sla_compliance_rate": sla_rate,
            "first_fix_rate": first_fix,
            "total_tickets": total_count,
        },
        "volume": [
            {"date": v["_id"], "total": v["total"], "closed": v["closed"],
             "in_progress": v["in_progress"], "open": v["open"]}
            for v in volume_agg if v["_id"]
        ],
        "vehicle_dist": [
            {"type": (v["_id"] or "unknown").replace("_", " ").title(), "count": v["count"]}
            for v in vehicle_agg if v["_id"]
        ],
    }


# ======================== TECHNICIAN PERFORMANCE ========================

@router.get("/technicians")
async def get_technician_insights(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    db = get_db()
    org_id = await get_org_id(request)
    start, end, _, _ = get_date_range(date_from, date_to)

    closed_match = {
        "organization_id": org_id,
        "status": {"$in": ["closed", "resolved"]},
        "created_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
        "assigned_technician_id": {"$exists": True, "$ne": None},
    }

    # Technician aggregation
    tech_agg = await db.tickets.aggregate([
        {"$match": closed_match},
        {"$project": {
            "tech_id": "$assigned_technician_id",
            "tech_name": "$assigned_technician_name",
            "vehicle_type": 1,
            "res_hours": {
                "$cond": [
                    {"$and": [
                        {"$ifNull": ["$closed_at", False]},
                        {"$ifNull": ["$created_at", False]},
                    ]},
                    {"$divide": [
                        {"$subtract": [{"$toDate": "$closed_at"}, {"$toDate": "$created_at"}]},
                        3600000,
                    ]},
                    None,
                ]
            },
            "sla_ok": {
                "$cond": [
                    {"$and": [
                        {"$ifNull": ["$sla_resolution_due_at", False]},
                        {"$ifNull": ["$closed_at", False]},
                    ]},
                    {"$lte": ["$closed_at", "$sla_resolution_due_at"]},
                    None,
                ]
            },
        }},
        {"$group": {
            "_id": "$tech_id",
            "name": {"$first": "$tech_name"},
            "tickets_closed": {"$sum": 1},
            "avg_hours": {"$avg": "$res_hours"},
            "sla_ok": {"$sum": {"$cond": [{"$eq": ["$sla_ok", True]}, 1, 0]}},
            "sla_total": {"$sum": {"$cond": [{"$ne": ["$sla_ok", None]}, 1, 0]}},
            "vehicle_types": {"$push": "$vehicle_type"},
        }},
        {"$sort": {"tickets_closed": -1}},
        {"$limit": 20},
    ]).to_list(20)

    # Ratings
    ratings_agg = await db.ticket_reviews.aggregate([
        {"$match": {
            "organization_id": org_id,
            "completed": True,
            "completed_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
        }},
        {"$lookup": {
            "from": "tickets",
            "localField": "ticket_id",
            "foreignField": "ticket_id",
            "as": "tkt",
        }},
        {"$unwind": {"path": "$tkt", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$tkt.assigned_technician_id",
            "avg_rating": {"$avg": "$rating"},
            "review_count": {"$sum": 1},
        }},
    ]).to_list(50)
    ratings = {r["_id"]: r for r in ratings_agg}

    leaderboard = []
    for tech in tech_agg:
        tid = tech["_id"]
        rd = ratings.get(tid, {})
        sla_pct = round(tech["sla_ok"] / tech["sla_total"] * 100, 1) if tech["sla_total"] > 0 else None
        leaderboard.append({
            "id": tid,
            "name": tech["name"] or "Unknown",
            "tickets_closed": tech["tickets_closed"],
            "avg_hours": round(tech["avg_hours"], 1) if tech["avg_hours"] is not None else None,
            "avg_rating": round(rd["avg_rating"], 1) if rd.get("avg_rating") else None,
            "review_count": rd.get("review_count", 0),
            "sla_compliance": sla_pct,
        })

    # Specialisation heatmap
    heatmap_agg = await db.tickets.aggregate([
        {"$match": {
            **closed_match,
            "vehicle_type": {"$ne": None, "$exists": True},
        }},
        {"$group": {
            "_id": {"tech": "$assigned_technician_id", "vtype": "$vehicle_type"},
            "name": {"$first": "$assigned_technician_name"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 200},
    ]).to_list(200)

    techs_map = {}
    vtypes = set()
    matrix = {}
    for row in heatmap_agg:
        tid = row["_id"]["tech"]
        vt = (row["_id"]["vtype"] or "unknown").replace("_", " ").title()
        if tid not in techs_map:
            techs_map[tid] = row.get("name") or tid
        vtypes.add(vt)
        matrix[(tid, vt)] = row["count"]

    heatmap_rows = []
    for tid, tname in techs_map.items():
        row = {"tech_id": tid, "tech_name": tname}
        for v in sorted(vtypes):
            row[v] = matrix.get((tid, v), 0)
        heatmap_rows.append(row)

    return {
        "leaderboard": leaderboard,
        "heatmap": heatmap_rows,
        "vehicle_types": sorted(list(vtypes)),
    }


# ======================== EFI INTELLIGENCE ========================

@router.get("/efi")
async def get_efi_insights(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    db = get_db()
    org_id = await get_org_id(request)
    start, end, _, _ = get_date_range(date_from, date_to)

    tkt_base = {
        "organization_id": org_id,
        "created_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
    }

    # EFI session count (best-effort)
    efi_count = 0
    try:
        efi_count = await db.efi_sessions.count_documents({
            "created_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
        })
    except Exception:
        pass

    # Top failure patterns from ticket categories
    failure_agg = await db.tickets.aggregate([
        {"$match": {**tkt_base, "category": {"$exists": True, "$nin": [None, ""]}}},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "avg_cost": {"$avg": "$actual_cost"},
            "avg_fix_hours": {"$avg": {
                "$cond": [
                    {"$and": [{"$ifNull": ["$closed_at", False]}, {"$ifNull": ["$created_at", False]}]},
                    {"$divide": [
                        {"$subtract": [{"$toDate": "$closed_at"}, {"$toDate": "$created_at"}]},
                        3600000,
                    ]},
                    None,
                ]
            }},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]).to_list(10)

    # Failure trend by vehicle type × category
    vf_agg = await db.tickets.aggregate([
        {"$match": {
            **tkt_base,
            "vehicle_type": {"$ne": None, "$exists": True},
            "category": {"$ne": None, "$ne": ""},
        }},
        {"$group": {
            "_id": {"vehicle": "$vehicle_type", "fault": "$category"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 100},
    ]).to_list(100)

    vtypes_v = set()
    faults_v = {}
    vf_matrix = {}
    for row in vf_agg:
        v = (row["_id"]["vehicle"] or "unknown").replace("_", " ").title()
        f = row["_id"]["fault"]
        vtypes_v.add(v)
        faults_v[f] = faults_v.get(f, 0) + row["count"]
        vf_matrix[(v, f)] = row["count"]

    top_faults = sorted(faults_v, key=lambda x: -faults_v[x])[:5]
    vf_chart = []
    for v in sorted(vtypes_v):
        entry = {"vehicle": v}
        for f in top_faults:
            entry[f] = vf_matrix.get((v, f), 0)
        vf_chart.append(entry)

    most_common = failure_agg[0]["_id"] if failure_agg else None

    return {
        "stats": {
            "diagnoses_run": efi_count,
            "most_diagnosed": most_common,
            "total_fault_types": len(failure_agg),
            "total_in_period": sum(r["count"] for r in failure_agg),
        },
        "failure_patterns": [
            {
                "fault_type": r["_id"],
                "count": r["count"],
                "avg_cost": round(safe(r.get("avg_cost")), 2),
                "avg_fix_hours": round(r["avg_fix_hours"], 1) if r.get("avg_fix_hours") else None,
            }
            for r in failure_agg
        ],
        "vehicle_fault_chart": vf_chart,
        "fault_types": top_faults,
    }


# ======================== CUSTOMER INTELLIGENCE ========================

@router.get("/customers")
async def get_customer_insights(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    db = get_db()
    org_id = await get_org_id(request)
    start, end, _, _ = get_date_range(date_from, date_to)

    # New customers
    new_count = await db.customers.count_documents({
        "organization_id": org_id,
        "created_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
    })

    # Returning customers in period
    cids_in_period = await db.tickets.distinct("customer_id", {
        "organization_id": org_id,
        "created_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
        "customer_id": {"$nin": [None, ""]},
    })
    returning_count = 0
    if cids_in_period:
        returning_count = await db.tickets.count_documents({
            "organization_id": org_id,
            "created_at": {"$lt": start + "T00:00:00"},
            "customer_id": {"$in": cids_in_period},
        })
        returning_count = min(returning_count, len(cids_in_period))

    # Avg rating
    rating_agg = await db.ticket_reviews.aggregate([
        {"$match": {
            "organization_id": org_id,
            "completed": True,
            "completed_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
        }},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "total": {"$sum": 1}}},
    ]).to_list(1)
    avg_rating = round(rating_agg[0]["avg_rating"], 1) if rating_agg else None
    survey_done = rating_agg[0]["total"] if rating_agg else 0

    surveys_sent = await db.ticket_reviews.count_documents({
        "organization_id": org_id,
        "created_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
    })
    response_rate = round(survey_done / surveys_sent * 100, 1) if surveys_sent > 0 else None

    # Daily satisfaction trend
    trend_agg = await db.ticket_reviews.aggregate([
        {"$match": {
            "organization_id": org_id,
            "completed": True,
            "completed_at": {"$gte": start + "T00:00:00", "$lte": end + "T23:59:59"},
        }},
        {"$group": {
            "_id": {"$substr": ["$completed_at", 0, 10]},
            "avg_rating": {"$avg": "$rating"},
        }},
        {"$sort": {"_id": 1}},
    ]).to_list(200)

    # Top customers by revenue
    top_inv = await db.invoices_enhanced.aggregate([
        {"$match": {
            "organization_id": org_id,
            "status": "paid",
            "invoice_date": {"$gte": start, "$lte": end},
        }},
        {"$group": {
            "_id": "$customer_id",
            "name": {"$first": "$customer_name"},
            "total_spent": {"$sum": "$grand_total"},
            "invoice_count": {"$sum": 1},
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": 10},
    ]).to_list(10)

    sixty_ago = (datetime.now(timezone.utc).date() - timedelta(days=60)).isoformat()
    top_customers = []
    for c in top_inv:
        last_tkt = await db.tickets.find_one(
            {"organization_id": org_id, "customer_id": c["_id"]},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", -1)],
        )
        last_visit = (last_tkt["created_at"] or "")[:10] if last_tkt else None
        top_customers.append({
            "id": c["_id"],
            "name": c["name"] or "Unknown",
            "total_spent": round(c["total_spent"], 2),
            "invoice_count": c["invoice_count"],
            "last_visit": last_visit,
            "at_risk": (last_visit < sixty_ago) if last_visit else False,
        })

    # Vehicle make distribution
    make_agg = await db.vehicles.aggregate([
        {"$match": {"organization_id": org_id}},
        {"$group": {"_id": "$make", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]).to_list(10)

    return {
        "kpis": {
            "new_customers": new_count,
            "returning_customers": returning_count,
            "avg_rating": avg_rating,
            "response_rate": response_rate,
        },
        "rating_trend": [
            {"date": r["_id"], "rating": round(r["avg_rating"], 1)}
            for r in trend_agg if r["_id"]
        ],
        "top_customers": top_customers,
        "vehicle_makes": [
            {"make": m["_id"] or "Unknown", "count": m["count"]}
            for m in make_agg if m["_id"]
        ],
    }


# ======================== INVENTORY INTELLIGENCE ========================

@router.get("/inventory")
async def get_inventory_insights(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    db = get_db()
    org_id = await get_org_id(request)
    start, end, _, _ = get_date_range(date_from, date_to)

    item_base = {"organization_id": org_id}

    # Stock health aggregation
    val_agg = await db.items.aggregate([
        {"$match": item_base},
        {"$group": {
            "_id": None,
            "total_value": {"$sum": {
                "$multiply": [
                    {"$ifNull": ["$stock_on_hand", 0]},
                    {"$ifNull": ["$purchase_rate", {"$ifNull": ["$sales_rate", 0]}]},
                ]
            }},
            "total": {"$sum": 1},
            "healthy": {"$sum": {"$cond": [
                {"$and": [
                    {"$gt": ["$stock_on_hand", {"$ifNull": ["$reorder_level", 0]}]},
                    {"$gt": ["$stock_on_hand", 0]},
                ]},
                1, 0,
            ]}},
            "low": {"$sum": {"$cond": [
                {"$and": [
                    {"$gt": ["$stock_on_hand", 0]},
                    {"$gt": ["$reorder_level", 0]},
                    {"$lte": ["$stock_on_hand", "$reorder_level"]},
                ]},
                1, 0,
            ]}},
            "out": {"$sum": {"$cond": [{"$lte": ["$stock_on_hand", 0]}, 1, 0]}},
        }},
    ]).to_list(1)

    vd = val_agg[0] if val_agg else {}
    total_value = round(safe(vd.get("total_value")), 2)
    total_items = safe(vd.get("total"))
    healthy = safe(vd.get("healthy"))
    low_stock = safe(vd.get("low"))
    out_of_stock = safe(vd.get("out"))

    # Below reorder level
    below_reorder = await db.items.count_documents({
        **item_base,
        "reorder_level": {"$gt": 0},
        "$expr": {"$lt": ["$stock_on_hand", "$reorder_level"]},
    })

    # Fast movers in period (from invoice line_items embedded in invoices)
    fast_movers_agg = await db.invoices_enhanced.aggregate([
        {"$match": {
            "organization_id": org_id,
            "invoice_date": {"$gte": start, "$lte": end},
            "line_items": {"$exists": True, "$ne": []},
        }},
        {"$unwind": "$line_items"},
        {"$group": {
            "_id": "$line_items.item_id",
            "name": {"$first": "$line_items.name"},
            "qty": {"$sum": "$line_items.quantity"},
            "value": {"$sum": "$line_items.amount"},
        }},
        {"$sort": {"qty": -1}},
        {"$limit": 5},
    ]).to_list(5)
    parts_used = int(sum(f.get("qty", 0) or 0 for f in fast_movers_agg))

    # Dead stock — items with stock but not used in last 90 days
    ninety_ago = (datetime.now(timezone.utc).date() - timedelta(days=90)).isoformat()
    recent_ids_agg = await db.invoices_enhanced.aggregate([
        {"$match": {
            "organization_id": org_id,
            "invoice_date": {"$gte": ninety_ago},
            "line_items": {"$exists": True},
        }},
        {"$unwind": "$line_items"},
        {"$group": {"_id": "$line_items.item_id"}},
    ]).to_list(5000)
    recent_ids = [r["_id"] for r in recent_ids_agg if r["_id"]]

    dead_count = await db.items.count_documents({
        **item_base,
        "stock_on_hand": {"$gt": 0},
        "item_id": {"$nin": recent_ids},
    })

    dead_items_cursor = db.items.find(
        {**item_base, "stock_on_hand": {"$gt": 0}, "item_id": {"$nin": recent_ids[:1000]}},
        {"_id": 0, "name": 1, "stock_on_hand": 1, "purchase_rate": 1, "updated_time": 1},
    ).sort("stock_on_hand", -1).limit(5)
    dead_items = await dead_items_cursor.to_list(5)

    def stock_pct(n):
        return round(n / total_items * 100, 1) if total_items > 0 else 0

    dead_pct = round(dead_count / total_items * 100, 1) if total_items > 0 else 0

    return {
        "kpis": {
            "total_value": total_value,
            "below_reorder": below_reorder,
            "parts_used": parts_used,
            "dead_stock_count": dead_count,
        },
        "stock_health": [
            {"label": "Healthy", "value": stock_pct(healthy), "count": healthy, "color": "#C8FF00"},
            {"label": "Low Stock", "value": stock_pct(low_stock), "count": low_stock, "color": "#EAB308"},
            {"label": "Out of Stock", "value": stock_pct(out_of_stock), "count": out_of_stock, "color": "#EF4444"},
            {"label": "Dead Stock", "value": dead_pct, "count": dead_count, "color": "#6B7280"},
        ],
        "fast_movers": [
            {"name": f.get("name") or "Unknown", "qty": int(f.get("qty") or 0), "value": round(f.get("value") or 0, 2)}
            for f in fast_movers_agg
        ],
        "dead_stock": [
            {
                "name": d.get("name", "Unknown"),
                "stock": d.get("stock_on_hand", 0),
                "value": round((d.get("stock_on_hand") or 0) * (d.get("purchase_rate") or 0), 2),
                "last_updated": (d.get("updated_time") or "")[:10] or None,
            }
            for d in dead_items
        ],
    }
