"""
Battwheels OS - Technician Portal API Routes
Technician-specific endpoints for their portal
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import jwt
import os
from utils.database import extract_org_id, org_query


def get_db():
    from server import db
    return db

router = APIRouter(prefix="/technician", tags=["Technician Portal"])

SECRET_KEY = os.environ.get("JWT_SECRET", "battwheels-secret")
ALGORITHM = "HS256"


async def get_current_technician(request: Request):
    """Extract technician info from token"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if role != "technician":
            raise HTTPException(status_code=403, detail="Technician access required")
        
        db = get_db()
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==================== DASHBOARD ====================

@router.get("/dashboard")
async def get_technician_dashboard(request: Request):
    """Get technician's personal dashboard data"""
    technician = await get_current_technician(request)
    db = get_db()
    
    tech_id = technician["user_id"]
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    # Get assigned tickets by status
    assigned_filter = {"assigned_to": tech_id}
    
    open_tickets = await db.tickets.count_documents({**assigned_filter, "status": {"$in": ["open", "assigned", "technician_assigned"]}})
    in_progress = await db.tickets.count_documents({**assigned_filter, "status": "work_in_progress"})
    pending_estimate = await db.tickets.count_documents({**assigned_filter, "status": {"$in": ["estimate_sent", "estimate_pending"]}})
    completed_today = await db.tickets.count_documents({
        **assigned_filter, 
        "status": {"$in": ["work_completed", "closed", "resolved"]},
        "updated_at": {"$gte": today_start.isoformat()}
    })
    completed_week = await db.tickets.count_documents({
        **assigned_filter,
        "status": {"$in": ["work_completed", "closed", "resolved"]},
        "updated_at": {"$gte": week_start.isoformat()}
    })
    completed_month = await db.tickets.count_documents({
        **assigned_filter,
        "status": {"$in": ["work_completed", "closed", "resolved"]},
        "updated_at": {"$gte": month_start.isoformat()}
    })
    
    # Calculate average resolution time (this month)
    resolved_tickets = await db.tickets.find(
        {
            **assigned_filter,
            "status": {"$in": ["resolved", "closed", "work_completed"]},
            "resolved_at": {"$exists": True},
            "created_at": {"$gte": month_start.isoformat()}
        },
        {"_id": 0, "created_at": 1, "resolved_at": 1}
    ).to_list(100)
    
    avg_resolution_hours = 0
    if resolved_tickets:
        total_hours = 0
        for t in resolved_tickets:
            try:
                created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(t["resolved_at"].replace("Z", "+00:00"))
                total_hours += (resolved - created).total_seconds() / 3600
            except:
                pass
        avg_resolution_hours = round(total_hours / len(resolved_tickets), 1) if resolved_tickets else 0
    
    # Get estimates pending approval
    estimates_pending = await db.ticket_estimates.count_documents({
        "technician_id": tech_id,
        "status": "sent"
    })
    
    # Today's attendance status
    attendance_today = await db.attendance.find_one({
        "user_id": tech_id,
        "date": today_start.strftime("%Y-%m-%d")
    }, {"_id": 0})
    
    # Pending leave requests
    pending_leaves = await db.leave_requests.count_documents({
        "user_id": tech_id,
        "status": "pending"
    })
    
    return {
        "technician": {
            "name": technician.get("name"),
            "email": technician.get("email"),
            "user_id": tech_id
        },
        "tickets": {
            "open": open_tickets,
            "in_progress": in_progress,
            "pending_estimate_approval": pending_estimate,
            "completed_today": completed_today,
            "completed_week": completed_week,
            "completed_month": completed_month,
            "total_assigned": open_tickets + in_progress + pending_estimate
        },
        "estimates_pending_approval": estimates_pending,
        "performance": {
            "avg_resolution_hours": avg_resolution_hours,
            "tickets_resolved_month": completed_month
        },
        "attendance": {
            "today": attendance_today.get("status") if attendance_today else None,
            "check_in": attendance_today.get("check_in") if attendance_today else None,
            "check_out": attendance_today.get("check_out") if attendance_today else None
        },
        "pending_leave_requests": pending_leaves
    }


# ==================== MY TICKETS ====================

@router.get("/tickets")
async def get_my_tickets(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """Get tickets assigned to the technician"""
    technician = await get_current_technician(request)
    db = get_db()
    
    query = {"assigned_to": technician["user_id"]}
    
    if status:
        if status == "active":
            query["status"] = {"$in": ["open", "assigned", "technician_assigned", "work_in_progress", "estimate_sent"]}
        elif status == "completed":
            query["status"] = {"$in": ["work_completed", "closed", "resolved"]}
        else:
            query["status"] = status
    
    if priority:
        query["priority"] = priority
    
    tickets = await db.tickets.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.tickets.count_documents(query)
    
    # Enrich with estimate status
    for ticket in tickets:
        estimate = await db.ticket_estimates.find_one(
            {"ticket_id": ticket["ticket_id"]},
            {"_id": 0, "estimate_id": 1, "status": 1, "grand_total": 1}
        )
        ticket["estimate"] = estimate
    
    return {
        "tickets": tickets,
        "total": total,
        "limit": limit,
        "skip": skip
    }

@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(request: Request, ticket_id: str):
    """Get detailed ticket info for technician"""
    technician = await get_current_technician(request)
    db = get_db()
    
    ticket = await db.tickets.find_one(
        {"ticket_id": ticket_id, "assigned_to": technician["user_id"]},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not assigned to you")
    
    # Get estimate
    estimate = await db.ticket_estimates.find_one({"ticket_id": ticket_id}, {"_id": 0})
    
    # Get estimate line items
    line_items = []
    if estimate:
        line_items = await db.ticket_estimate_line_items.find(
            {"estimate_id": estimate["estimate_id"]},
            {"_id": 0}
        ).to_list(100)
    
    # Get activities
    activities = await db.ticket_activities.find(
        {"ticket_id": ticket_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    
    # Get customer info
    customer = None
    if ticket.get("customer_id"):
        customer = await db.customers.find_one(
            {"customer_id": ticket["customer_id"]},
            {"_id": 0, "customer_id": 1, "name": 1, "phone": 1, "email": 1}
        )
    
    return {
        "ticket": ticket,
        "estimate": estimate,
        "line_items": line_items,
        "activities": activities,
        "customer": customer
    }


# ==================== WORK ACTIONS ====================

class StartWorkRequest(BaseModel):
    notes: Optional[str] = None

class CompleteWorkRequest(BaseModel):
    work_summary: str
    labor_hours: float
    parts_used: Optional[List[str]] = []
    notes: Optional[str] = None

@router.post("/tickets/{ticket_id}/start-work")
async def start_work(request: Request, ticket_id: str, data: StartWorkRequest):
    """Start work on assigned ticket"""
    technician = await get_current_technician(request)
    db = get_db()
    
    # Verify ticket is assigned to technician
    ticket = await db.tickets.find_one(
        {"ticket_id": ticket_id, "assigned_to": technician["user_id"]},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not assigned to you")
    
    if ticket.get("status") not in ["open", "assigned", "technician_assigned", "estimate_approved"]:
        raise HTTPException(status_code=400, detail=f"Cannot start work on ticket with status '{ticket.get('status')}'")
    
    now = datetime.now(timezone.utc)
    
    # Update ticket status
    history = ticket.get("status_history", [])
    history.append({
        "status": "work_in_progress",
        "timestamp": now.isoformat(),
        "user": technician["name"],
        "notes": data.notes or "Work started by technician"
    })
    
    await db.tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status": "work_in_progress",
            "work_started_at": now.isoformat(),
            "status_history": history,
            "updated_at": now.isoformat()
        }}
    )
    
    # Log activity
    await db.ticket_activities.insert_one({
        "activity_id": f"act_{now.timestamp()}",
        "ticket_id": ticket_id,
        "action": "work_started",
        "description": f"Work started by {technician['name']}",
        "user_id": technician["user_id"],
        "user_name": technician["name"],
        "timestamp": now.isoformat()
    })
    
    return {"message": "Work started", "status": "work_in_progress"}

@router.post("/tickets/{ticket_id}/complete-work")
async def complete_work(request: Request, ticket_id: str, data: CompleteWorkRequest):
    """Mark work as completed"""
    technician = await get_current_technician(request)
    db = get_db()
    
    ticket = await db.tickets.find_one(
        {"ticket_id": ticket_id, "assigned_to": technician["user_id"]},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not assigned to you")
    
    if ticket.get("status") != "work_in_progress":
        raise HTTPException(status_code=400, detail="Can only complete work on tickets in 'work_in_progress' status")
    
    now = datetime.now(timezone.utc)
    
    history = ticket.get("status_history", [])
    history.append({
        "status": "work_completed",
        "timestamp": now.isoformat(),
        "user": technician["name"],
        "notes": data.work_summary
    })
    
    await db.tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status": "work_completed",
            "work_completed_at": now.isoformat(),
            "work_summary": data.work_summary,
            "labor_hours": data.labor_hours,
            "parts_used": data.parts_used,
            "completion_notes": data.notes,
            "status_history": history,
            "updated_at": now.isoformat()
        }}
    )
    
    # Log activity
    await db.ticket_activities.insert_one({
        "activity_id": f"act_{now.timestamp()}",
        "ticket_id": ticket_id,
        "action": "work_completed",
        "description": f"Work completed by {technician['name']}: {data.work_summary}",
        "user_id": technician["user_id"],
        "user_name": technician["name"],
        "timestamp": now.isoformat(),
        "metadata": {
            "labor_hours": data.labor_hours,
            "parts_used": data.parts_used
        }
    })
    
    return {"message": "Work completed", "status": "work_completed"}


# ==================== PERSONAL HR ====================

@router.get("/attendance")
async def get_my_attendance(
    request: Request,
    month: Optional[str] = None,
    year: Optional[int] = None
):
    """Get technician's own attendance records"""
    technician = await get_current_technician(request)
    db = get_db()
    
    now = datetime.now(timezone.utc)
    target_month = int(month) if month else now.month
    target_year = year or now.year
    
    # Build date range
    start_date = f"{target_year}-{target_month:02d}-01"
    if target_month == 12:
        end_date = f"{target_year + 1}-01-01"
    else:
        end_date = f"{target_year}-{target_month + 1:02d}-01"
    
    records = await db.attendance.find(
        {
            "user_id": technician["user_id"],
            "date": {"$gte": start_date, "$lt": end_date}
        },
        {"_id": 0}
    ).sort("date", -1).to_list(31)
    
    # Calculate summary
    present = sum(1 for r in records if r.get("status") == "present")
    absent = sum(1 for r in records if r.get("status") == "absent")
    late = sum(1 for r in records if r.get("status") == "late")
    half_day = sum(1 for r in records if r.get("status") == "half_day")
    
    return {
        "records": records,
        "summary": {
            "present": present,
            "absent": absent,
            "late": late,
            "half_day": half_day,
            "total_days": len(records)
        },
        "month": target_month,
        "year": target_year
    }

@router.post("/attendance/check-in")
async def check_in(request: Request):
    """Record check-in time"""
    technician = await get_current_technician(request)
    db = get_db()
    
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    
    existing = await db.attendance.find_one({
        "user_id": technician["user_id"],
        "date": today
    })
    
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    check_in_time = now.strftime("%H:%M:%S")
    
    # Determine status based on check-in time (assuming 9 AM is on-time)
    status = "present"
    hour = now.hour
    if hour >= 10:  # After 10 AM is late
        status = "late"
    
    await db.attendance.update_one(
        {"user_id": technician["user_id"], "date": today},
        {"$set": {
            "user_id": technician["user_id"],
            "user_name": technician["name"],
            "date": today,
            "check_in": check_in_time,
            "status": status,
            "updated_at": now.isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Checked in successfully", "check_in": check_in_time, "status": status}

@router.post("/attendance/check-out")
async def check_out(request: Request):
    """Record check-out time"""
    technician = await get_current_technician(request)
    db = get_db()
    
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    
    existing = await db.attendance.find_one({
        "user_id": technician["user_id"],
        "date": today
    })
    
    if not existing or not existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Must check in first")
    
    if existing.get("check_out"):
        raise HTTPException(status_code=400, detail="Already checked out today")
    
    check_out_time = now.strftime("%H:%M:%S")
    
    # Calculate working hours
    check_in = datetime.strptime(f"{today} {existing['check_in']}", "%Y-%m-%d %H:%M:%S")
    check_out = datetime.strptime(f"{today} {check_out_time}", "%Y-%m-%d %H:%M:%S")
    working_hours = round((check_out - check_in).total_seconds() / 3600, 2)
    
    # Update status if worked less than 4 hours
    status = existing.get("status", "present")
    if working_hours < 4:
        status = "half_day"
    
    await db.attendance.update_one(
        {"user_id": technician["user_id"], "date": today},
        {"$set": {
            "check_out": check_out_time,
            "working_hours": working_hours,
            "status": status,
            "updated_at": now.isoformat()
        }}
    )
    
    return {"message": "Checked out successfully", "check_out": check_out_time, "working_hours": working_hours}

@router.get("/leave")
async def get_my_leave_requests(request: Request):
    """Get technician's leave requests"""
    technician = await get_current_technician(request)
    db = get_db()
    
    requests = await db.leave_requests.find(
        {"user_id": technician["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Get leave balance
    balance = await db.leave_balances.find_one(
        {"user_id": technician["user_id"]},
        {"_id": 0}
    )
    
    return {
        "requests": requests,
        "balance": balance or {"casual": 12, "sick": 12, "earned": 15, "used": {"casual": 0, "sick": 0, "earned": 0}}
    }

class LeaveRequest(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    reason: str

@router.post("/leave")
async def request_leave(request: Request, data: LeaveRequest):
    """Submit leave request"""
    technician = await get_current_technician(request)
    db = get_db()
    
    now = datetime.now(timezone.utc)
    
    # Calculate days
    start = datetime.strptime(data.start_date, "%Y-%m-%d")
    end = datetime.strptime(data.end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    
    leave_doc = {
        "leave_id": f"LV-{now.strftime('%Y%m%d')}-{technician['user_id'][-4:]}",
        "user_id": technician["user_id"],
        "user_name": technician["name"],
        "leave_type": data.leave_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days": days,
        "reason": data.reason,
        "status": "pending",
        "created_at": now.isoformat()
    }
    
    await db.leave_requests.insert_one(leave_doc)
    del leave_doc["_id"]
    
    return leave_doc

@router.get("/payroll")
async def get_my_payroll(request: Request, months: int = 3):
    """Get technician's payroll history"""
    technician = await get_current_technician(request)
    db = get_db()
    
    payslips = await db.payroll.find(
        {"user_id": technician["user_id"]},
        {"_id": 0}
    ).sort("month", -1).limit(months).to_list(months)
    
    return {"payslips": payslips}


# ==================== PRODUCTIVITY ====================

@router.get("/productivity")
async def get_my_productivity(request: Request):
    """Get technician's own productivity metrics"""
    technician = await get_current_technician(request)
    db = get_db()
    
    tech_id = technician["user_id"]
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # This month's stats
    resolved_this_month = await db.tickets.count_documents({
        "assigned_to": tech_id,
        "status": {"$in": ["resolved", "closed", "work_completed"]},
        "updated_at": {"$gte": month_start.isoformat()}
    })
    
    # Get all resolved tickets for average time
    resolved_tickets = await db.tickets.find(
        {
            "assigned_to": tech_id,
            "status": {"$in": ["resolved", "closed", "work_completed"]},
            "resolved_at": {"$exists": True}
        },
        {"_id": 0, "created_at": 1, "resolved_at": 1, "priority": 1}
    ).sort("resolved_at", -1).limit(100).to_list(100)
    
    avg_resolution = 0
    priority_breakdown = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    if resolved_tickets:
        total_hours = 0
        for t in resolved_tickets:
            try:
                created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(t["resolved_at"].replace("Z", "+00:00"))
                total_hours += (resolved - created).total_seconds() / 3600
                priority = t.get("priority", "medium")
                if priority in priority_breakdown:
                    priority_breakdown[priority] += 1
            except:
                pass
        avg_resolution = round(total_hours / len(resolved_tickets), 1)
    
    # Get weekly trend (last 4 weeks)
    weekly_trend = []
    for i in range(4):
        week_end = now - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=7)
        count = await db.tickets.count_documents({
            "assigned_to": tech_id,
            "status": {"$in": ["resolved", "closed", "work_completed"]},
            "updated_at": {"$gte": week_start.isoformat(), "$lt": week_end.isoformat()}
        })
        weekly_trend.append({
            "week": f"Week {4 - i}",
            "resolved": count
        })
    weekly_trend.reverse()
    
    # Get rank among technicians
    all_tech_resolved = await db.tickets.aggregate([
        {"$match": {
            "assigned_to": {"$exists": True},
            "status": {"$in": ["resolved", "closed", "work_completed"]},
            "updated_at": {"$gte": month_start.isoformat()}
        }},
        {"$group": {"_id": "$assigned_to", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(100)
    
    rank = 1
    for i, t in enumerate(all_tech_resolved):
        if t["_id"] == tech_id:
            rank = i + 1
            break
    
    return {
        "this_month": {
            "tickets_resolved": resolved_this_month,
            "avg_resolution_hours": avg_resolution
        },
        "priority_breakdown": priority_breakdown,
        "weekly_trend": weekly_trend,
        "rank": rank,
        "total_technicians": len(all_tech_resolved)
    }



# ==================== AI ASSISTANT ====================

class AIAssistRequest(BaseModel):
    query: str
    category: str = "general"
    context: Optional[dict] = None

@router.post("/ai-assist")
async def technician_ai_assist(data: AIAssistRequest, user: dict = Depends(get_current_technician)):
    """
    AI-powered diagnostic assistant for technicians.
    Uses Gemini to provide repair guidance and fault diagnosis.
    """
    import os
    import uuid
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        return {
            "response": "AI assistant is currently unavailable. Please check your configuration or contact support.",
            "ai_enabled": False
        }
    
    try:
        # Build system message based on category
        category_prompts = {
            "battery": "Focus on battery-related issues including BMS, cells, charging, and thermal management.",
            "motor": "Focus on motor and controller issues including BLDC motors, inverters, and regenerative braking.",
            "electrical": "Focus on electrical system issues including wiring, fuses, relays, and high-voltage systems.",
            "diagnosis": "Focus on systematic fault diagnosis using symptom analysis and error code interpretation.",
            "general": "Provide comprehensive EV service guidance."
        }
        
        category_focus = category_prompts.get(data.category, category_prompts["general"])
        
        technician_name = data.context.get("technician_name", "Technician") if data.context else "Technician"
        
        system_message = f"""You are an expert EV Service Technician AI Assistant for Battwheels, an electric vehicle service company in India. You are helping {technician_name} with EV repairs and diagnostics.

Your expertise includes:
- Electric 2-wheelers (Ola, Ather, TVS iQube, Hero Electric, Bajaj Chetak)
- Electric 3-wheelers (Mahindra Treo, Piaggio Ape E-City, Euler HiLoad)
- Electric 4-wheelers (Tata Nexon EV, MG ZS EV, Hyundai Kona)
- Battery systems (Li-ion, LFP, NMC), BMS diagnostics
- Motor controllers, BLDC/PMSM motors
- Charging systems (AC/DC chargers, CCS, CHAdeMO)
- CAN bus diagnostics and error code interpretation

{category_focus}

Guidelines:
1. Be concise but thorough - technicians need actionable information
2. Include specific steps, measurements, and safety warnings where applicable
3. Reference common Indian EV models when relevant
4. Suggest proper tools and equipment needed
5. Highlight safety precautions for high-voltage work
6. If uncertain, recommend escalation or further diagnosis

Format your responses with:
- Clear headings using ## or ###
- Bullet points for steps
- **Bold** for important values or warnings
- Numbered lists for procedures"""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"tech_ai_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("gemini", "gemini-3-flash-preview")
        
        user_message = UserMessage(
            text=f"Query: {data.query}"
        )
        
        response = await chat.send_message(user_message)
        
        return {
            "response": response,
            "ai_enabled": True,
            "category": data.category
        }
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"AI assist error: {e}")
        
        return {
            "response": "I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support if the issue persists.",
            "ai_enabled": False,
            "error": str(e)
        }
