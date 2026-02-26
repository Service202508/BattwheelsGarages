"""
Technician Productivity Service
================================
Analytics and metrics for technician performance tracking based on service tickets.
"""
from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import os
from utils.database import extract_org_id, org_query


# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

router = APIRouter(prefix="/productivity", tags=["Technician Productivity"])

# ==================== MODELS ====================

class TechnicianStats(BaseModel):
    technician_id: str
    technician_name: str
    tickets_resolved: int
    tickets_in_progress: int
    avg_resolution_hours: float
    high_critical_tickets: int
    customer_rating: float
    first_time_fix_rate: float
    rework_count: int
    revenue_generated: float

class ProductivitySummary(BaseModel):
    active_technicians: int
    total_tickets_resolved: int
    avg_resolution_time_hours: float
    tickets_this_week: int
    tickets_this_month: int

# ==================== AUTH HELPERS ====================

async def get_current_user_from_request(request: Request):
    org_id = extract_org_id(request)
    """Extract current user from request"""
    from utils.auth import decode_token_safe
    
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            if user:
                return user
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_token_safe(token)
        if payload and payload.get("user_id"):
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
    return None

async def require_admin_or_manager(request: Request):
    org_id = extract_org_id(request)
    """Require admin or manager access"""
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin or manager access required")
    return user

# ==================== PRODUCTIVITY ENDPOINTS ====================

@router.get("/summary")
async def get_productivity_summary(request: Request):
    org_id = extract_org_id(request)
    """Get overall productivity summary"""
    user = await require_admin_or_manager(request)
    
    # Get date ranges
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Count active technicians (those with resolved tickets in last 30 days)
    pipeline = [
        {"$match": {
            "status": {"$in": ["resolved", "closed"]},
            "assigned_technician_id": {"$exists": True, "$ne": None}
        }},
        {"$group": {"_id": "$assigned_technician_id"}}
    ]
    active_techs = await db.tickets.aggregate(pipeline).to_list(100)
    active_technicians = len(active_techs)
    
    # Total resolved tickets
    total_resolved = await db.tickets.count_documents({
        "status": {"$in": ["resolved", "closed"]}
    })
    
    # Average resolution time
    resolution_pipeline = [
        {"$match": {
            "status": {"$in": ["resolved", "closed"]},
            "created_at": {"$exists": True},
            "updated_at": {"$exists": True}
        }},
        {"$addFields": {
            "created_date": {"$dateFromString": {"dateString": "$created_at", "onError": None}},
            "updated_date": {"$dateFromString": {"dateString": "$updated_at", "onError": None}}
        }},
        {"$match": {"created_date": {"$ne": None}, "updated_date": {"$ne": None}}},
        {"$project": {
            "resolution_ms": {"$subtract": ["$updated_date", "$created_date"]}
        }},
        {"$group": {
            "_id": None,
            "avg_resolution_ms": {"$avg": "$resolution_ms"}
        }}
    ]
    
    resolution_result = await db.tickets.aggregate(resolution_pipeline).to_list(1)
    avg_resolution_hours = 0
    if resolution_result and resolution_result[0].get("avg_resolution_ms"):
        avg_resolution_hours = round(resolution_result[0]["avg_resolution_ms"] / (1000 * 60 * 60), 1)
    
    # Tickets this week/month (use string date comparison)
    week_str = week_ago.isoformat()
    month_str = month_ago.isoformat()
    
    tickets_this_week = await db.tickets.count_documents({
        "status": {"$in": ["resolved", "closed"]},
        "created_at": {"$gte": week_str}
    })
    
    tickets_this_month = await db.tickets.count_documents({
        "status": {"$in": ["resolved", "closed"]},
        "created_at": {"$gte": month_str}
    })
    
    return {
        "active_technicians": active_technicians,
        "total_tickets_resolved": total_resolved,
        "avg_resolution_time_hours": avg_resolution_hours,
        "tickets_this_week": tickets_this_week,
        "tickets_this_month": tickets_this_month
    }

@router.get("/technicians")
async def get_technician_productivity(request: Request, period: str = "all", sort_by: str = "tickets_resolved"):
    org_id = extract_org_id(request)
    """Get productivity breakdown by technician"""
    user = await require_admin_or_manager(request)
    
    # Build date filter
    date_filter = {}
    now = datetime.now(timezone.utc)
    if period == "week":
        date_filter["created_at"] = {"$gte": (now - timedelta(days=7)).isoformat()}
    elif period == "month":
        date_filter["created_at"] = {"$gte": (now - timedelta(days=30)).isoformat()}
    
    # Get all technicians from users collection
    technicians = await db.users.find(
        {"role": "technician", "is_active": {"$ne": False}},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1}
    ).to_list(100)
    
    # Also check employees table for technicians
    employees = await db.employees.find(
        {"department": "Technical"},
        {"_id": 0, "employee_id": 1, "name": 1, "email": 1}
    ).to_list(100)
    
    productivity_data = []
    
    for tech in technicians:
        tech_id = tech.get("user_id")
        tech_name = tech.get("name", "Unknown")
        
        # Query filter for this technician
        tech_filter = {
            "$or": [
                {"assigned_technician_id": tech_id},
                {"assigned_technician_name": tech_name}
            ]
        }
        if date_filter:
            tech_filter.update(date_filter)
        
        # Resolved tickets
        resolved_filter = {**tech_filter, "status": {"$in": ["resolved", "closed"]}}
        tickets_resolved = await db.tickets.count_documents(resolved_filter)
        
        # In progress tickets
        in_progress_filter = {**tech_filter, "status": {"$in": ["in_progress", "technician_assigned"]}}
        tickets_in_progress = await db.tickets.count_documents(in_progress_filter)
        
        # High/Critical tickets resolved
        high_critical_filter = {
            **resolved_filter,
            "priority": {"$in": ["high", "critical"]}
        }
        high_critical_tickets = await db.tickets.count_documents(high_critical_filter)
        
        # Calculate average resolution time
        resolution_pipeline = [
            {"$match": resolved_filter},
            {"$addFields": {
                "created_date": {"$dateFromString": {"dateString": "$created_at", "onError": None}},
                "updated_date": {"$dateFromString": {"dateString": "$updated_at", "onError": None}}
            }},
            {"$match": {"created_date": {"$ne": None}, "updated_date": {"$ne": None}}},
            {"$project": {
                "resolution_ms": {"$subtract": ["$updated_date", "$created_date"]}
            }},
            {"$group": {
                "_id": None,
                "avg_resolution_ms": {"$avg": "$resolution_ms"},
                "total_tickets": {"$sum": 1}
            }}
        ]
        
        resolution_result = await db.tickets.aggregate(resolution_pipeline).to_list(1)
        avg_resolution_hours = 0
        if resolution_result and resolution_result[0].get("avg_resolution_ms"):
            avg_resolution_hours = round(resolution_result[0]["avg_resolution_ms"] / (1000 * 60 * 60), 1)
        
        # Revenue generated (sum of final_amount from resolved tickets)
        revenue_pipeline = [
            {"$match": resolved_filter},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$ifNull": ["$final_amount", 0]}}
            }}
        ]
        revenue_result = await db.tickets.aggregate(revenue_pipeline).to_list(1)
        revenue_generated = revenue_result[0]["total_revenue"] if revenue_result else 0
        
        # First time fix rate (tickets without rework/reopened status)
        # Simplified: tickets resolved without status going back to in_progress
        first_time_fix_rate = 85.0  # Default, would need status history analysis
        
        # Customer rating (would need feedback system)
        customer_rating = 4.5  # Default placeholder
        
        productivity_data.append({
            "technician_id": tech_id,
            "technician_name": tech_name,
            "email": tech.get("email", ""),
            "tickets_resolved": tickets_resolved,
            "tickets_in_progress": tickets_in_progress,
            "avg_resolution_hours": avg_resolution_hours,
            "high_critical_tickets": high_critical_tickets,
            "customer_rating": customer_rating,
            "first_time_fix_rate": first_time_fix_rate,
            "revenue_generated": revenue_generated
        })
    
    # Sort results
    if sort_by == "tickets_resolved":
        productivity_data.sort(key=lambda x: x["tickets_resolved"], reverse=True)
    elif sort_by == "avg_time":
        productivity_data.sort(key=lambda x: x["avg_resolution_hours"])
    elif sort_by == "rating":
        productivity_data.sort(key=lambda x: x["customer_rating"], reverse=True)
    
    return productivity_data

@router.get("/technicians/{technician_id}")
async def get_technician_detail(request: Request, technician_id: str):
    org_id = extract_org_id(request)
    """Get detailed productivity for a specific technician"""
    user = await require_admin_or_manager(request)
    
    # Get technician info
    technician = await db.users.find_one(
        {"user_id": technician_id},
        {"_id": 0}
    )
    
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    
    tech_name = technician.get("name", "Unknown")
    
    # Get all tickets for this technician
    tech_filter = {
        "$or": [
            {"assigned_technician_id": technician_id},
            {"assigned_technician_name": tech_name}
        ]
    }
    
    # Ticket counts by status
    status_counts = {}
    for status in ["open", "technician_assigned", "in_progress", "resolved", "closed"]:
        count = await db.tickets.count_documents({**tech_filter, "status": status})
        status_counts[status] = count
    
    # Tickets by priority
    priority_counts = {}
    for priority in ["low", "medium", "high", "critical"]:
        count = await db.tickets.count_documents({
            **tech_filter,
            "priority": priority,
            "status": {"$in": ["resolved", "closed"]}
        })
        priority_counts[priority] = count
    
    # Monthly breakdown (last 6 months)
    monthly_data = []
    now = datetime.now(timezone.utc)
    for i in range(6):
        month_start = now.replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        count = await db.tickets.count_documents({
            **tech_filter,
            "status": {"$in": ["resolved", "closed"]},
            "created_at": {
                "$gte": month_start.isoformat(),
                "$lt": month_end.isoformat()
            }
        })
        
        monthly_data.append({
            "month": month_start.strftime("%b %Y"),
            "tickets_resolved": count
        })
    
    monthly_data.reverse()
    
    # Recent tickets
    recent_tickets = await db.tickets.find(
        tech_filter,
        {"_id": 0, "ticket_id": 1, "title": 1, "status": 1, "priority": 1, 
         "created_at": 1, "vehicle_number": 1, "final_amount": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "technician": {
            "id": technician_id,
            "name": tech_name,
            "email": technician.get("email", ""),
            "role": technician.get("role", ""),
            "joined_date": technician.get("created_at", "")
        },
        "status_breakdown": status_counts,
        "priority_breakdown": priority_counts,
        "monthly_trend": monthly_data,
        "recent_tickets": recent_tickets
    }

@router.get("/leaderboard")
async def get_productivity_leaderboard(request: Request, period: str = "month", metric: str = "tickets"):
    org_id = extract_org_id(request)
    """Get top performing technicians"""
    user = await require_admin_or_manager(request)
    
    # Get all technician productivity
    technicians = await get_technician_productivity(request, period=period)
    
    # Sort by selected metric
    if metric == "tickets":
        technicians.sort(key=lambda x: x["tickets_resolved"], reverse=True)
    elif metric == "revenue":
        technicians.sort(key=lambda x: x["revenue_generated"], reverse=True)
    elif metric == "rating":
        technicians.sort(key=lambda x: x["customer_rating"], reverse=True)
    
    # Add rank
    for i, tech in enumerate(technicians):
        tech["rank"] = i + 1
    
    return technicians[:10]  # Top 10

@router.get("/trends")
async def get_productivity_trends(request: Request):
    org_id = extract_org_id(request)
    """Get productivity trends over time"""
    user = await require_admin_or_manager(request)
    
    now = datetime.now(timezone.utc)
    trends = []
    
    # Last 12 weeks
    for i in range(12):
        week_start = now - timedelta(weeks=i+1)
        week_end = now - timedelta(weeks=i)
        
        resolved = await db.tickets.count_documents({
            "status": {"$in": ["resolved", "closed"]},
            "created_at": {
                "$gte": week_start.isoformat(),
                "$lt": week_end.isoformat()
            }
        })
        
        trends.append({
            "week": week_start.strftime("%b %d"),
            "tickets_resolved": resolved
        })
    
    trends.reverse()
    return trends

@router.get("/kpis")
async def get_productivity_kpis(request: Request):
    org_id = extract_org_id(request)
    """Get key performance indicators"""
    user = await require_admin_or_manager(request)
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Today's tickets
    tickets_today = await db.tickets.count_documents({
        "status": {"$in": ["resolved", "closed"]},
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # Pending tickets (open or assigned but not in progress)
    pending_tickets = await db.tickets.count_documents({
        "status": {"$in": ["open", "technician_assigned"]}
    })
    
    # Overdue tickets (open for more than 48 hours)
    overdue_threshold = (now - timedelta(hours=48)).isoformat()
    overdue_tickets = await db.tickets.count_documents({
        "status": {"$nin": ["resolved", "closed"]},
        "created_at": {"$lt": overdue_threshold}
    })
    
    # SLA compliance (resolved within 24 hours)
    sla_pipeline = [
        {"$match": {"status": {"$in": ["resolved", "closed"]}}},
        {"$addFields": {
            "created_date": {"$dateFromString": {"dateString": "$created_at", "onError": None}},
            "updated_date": {"$dateFromString": {"dateString": "$updated_at", "onError": None}}
        }},
        {"$match": {"created_date": {"$ne": None}, "updated_date": {"$ne": None}}},
        {"$project": {
            "resolution_hours": {
                "$divide": [
                    {"$subtract": ["$updated_date", "$created_date"]},
                    3600000  # Convert ms to hours
                ]
            }
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "within_sla": {"$sum": {"$cond": [{"$lte": ["$resolution_hours", 24]}, 1, 0]}}
        }}
    ]
    
    sla_result = await db.tickets.aggregate(sla_pipeline).to_list(1)
    sla_compliance = 0
    if sla_result and sla_result[0].get("total", 0) > 0:
        sla_compliance = round((sla_result[0]["within_sla"] / sla_result[0]["total"]) * 100, 1)
    
    return {
        "tickets_resolved_today": tickets_today,
        "pending_tickets": pending_tickets,
        "overdue_tickets": overdue_tickets,
        "sla_compliance_percent": sla_compliance
    }
