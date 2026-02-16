"""
Battwheels OS - HR Routes
Thin controller layer for HR management
"""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import logging

from services.hr_service import (
    HRService,
    get_hr_service,
    init_hr_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hr", tags=["HR"])

_service: Optional[HRService] = None


def init_router(database):
    global _service
    _service = init_hr_service(database)
    logger.info("HR router initialized")
    return router


def get_service() -> HRService:
    if _service is None:
        raise HTTPException(status_code=500, detail="HR service not initialized")
    return _service


# Request models
class EmployeeCreateRequest(BaseModel):
    user_id: Optional[str] = None
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: str
    designation: str
    employment_type: str = "full_time"
    date_of_joining: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    salary_structure: dict = {}
    bank_details: dict = {}
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    reporting_manager: Optional[str] = None


class EmployeeUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    salary_structure: Optional[dict] = None
    bank_details: Optional[dict] = None
    status: Optional[str] = None


class LeaveRequest(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    reason: str


class LeaveApprovalRequest(BaseModel):
    approved: bool
    comments: Optional[str] = None


class ClockRequest(BaseModel):
    location: Optional[str] = None


# Helper
async def get_current_user(request: Request, db) -> dict:
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            if user:
                return user
    raise HTTPException(status_code=401, detail="Not authenticated")


# ==================== EMPLOYEE ROUTES ====================

@router.post("/employees")
async def create_employee(data: EmployeeCreateRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    return await service.create_employee(data.model_dump(), user.get("user_id"))


@router.get("/employees")
async def list_employees(
    request: Request,
    department: Optional[str] = None,
    status: str = "active"
):
    service = get_service()
    return await service.list_employees(department=department, status=status)


@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, request: Request):
    service = get_service()
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeUpdateRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    return await service.update_employee(employee_id, updates, user.get("user_id"))


@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str, request: Request):
    service = get_service()
    await service.db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {"status": "terminated", "terminated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Employee terminated"}


@router.get("/employees/managers/list")
async def list_managers(request: Request):
    service = get_service()
    return await service.db.employees.find(
        {"status": "active", "designation": {"$regex": "manager|lead|head", "$options": "i"}},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1}
    ).to_list(100)


@router.get("/departments")
async def list_departments(request: Request):
    service = get_service()
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$department", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    return await service.db.employees.aggregate(pipeline).to_list(50)


# ==================== ATTENDANCE ROUTES ====================

@router.post("/attendance/clock-in")
async def clock_in(request: Request, data: ClockRequest = None):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    try:
        location = data.location if data else None
        return await service.clock_in(user.get("user_id"), location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/attendance/clock-out")
async def clock_out(request: Request, data: ClockRequest = None):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    try:
        location = data.location if data else None
        return await service.clock_out(user.get("user_id"), location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/attendance/today")
async def get_today_attendance(request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    attendance = await service.get_attendance_today(user.get("user_id"))
    return attendance or {"message": "No attendance record for today"}


@router.get("/attendance/my-records")
async def get_my_attendance(request: Request, limit: int = 30):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    employee = await service.get_employee_by_user(user.get("user_id"))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    return await service.db.attendance.find(
        {"employee_id": employee["employee_id"]},
        {"_id": 0}
    ).sort("date", -1).limit(limit).to_list(limit)


@router.get("/attendance/all")
async def get_all_attendance(
    request: Request,
    date: Optional[str] = None,
    department: Optional[str] = None
):
    service = get_service()
    
    query = {}
    if date:
        query["date"] = date
    
    if department:
        employees = await service.db.employees.find(
            {"department": department}, {"employee_id": 1}
        ).to_list(1000)
        emp_ids = [e["employee_id"] for e in employees]
        query["employee_id"] = {"$in": emp_ids}
    
    return await service.db.attendance.find(query, {"_id": 0}).sort("date", -1).to_list(500)


# ==================== LEAVE ROUTES ====================

@router.get("/leave/types")
async def get_leave_types(request: Request):
    return [
        {"type": "casual", "name": "Casual Leave", "default_balance": 12},
        {"type": "sick", "name": "Sick Leave", "default_balance": 12},
        {"type": "earned", "name": "Earned Leave", "default_balance": 15},
        {"type": "maternity", "name": "Maternity Leave", "default_balance": 26},
        {"type": "paternity", "name": "Paternity Leave", "default_balance": 5},
        {"type": "unpaid", "name": "Leave Without Pay", "default_balance": 0}
    ]


@router.get("/leave/balance")
async def get_leave_balance(request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    employee = await service.get_employee_by_user(user.get("user_id"))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    return employee.get("leave_balances", {})


@router.post("/leave/request")
async def request_leave(data: LeaveRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    try:
        return await service.request_leave(
            user_id=user.get("user_id"),
            leave_type=data.leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/leave/my-requests")
async def get_my_leave_requests(request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    return await service.db.leave_requests.find(
        {"user_id": user.get("user_id")},
        {"_id": 0}
    ).sort("applied_at", -1).to_list(50)


@router.get("/leave/pending-approvals")
async def get_pending_approvals(request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    # Get employees reporting to this manager
    reporting = await service.db.employees.find(
        {"reporting_manager": user.get("user_id")},
        {"user_id": 1}
    ).to_list(100)
    user_ids = [e["user_id"] for e in reporting]
    
    return await service.db.leave_requests.find(
        {"user_id": {"$in": user_ids}, "status": "pending"},
        {"_id": 0}
    ).to_list(50)


@router.put("/leave/{leave_id}/approve")
async def approve_leave(leave_id: str, data: LeaveApprovalRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    try:
        return await service.approve_leave(
            leave_id=leave_id,
            approved_by=user.get("user_id"),
            approved=data.approved,
            comments=data.comments
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/leave/{leave_id}")
async def cancel_leave(leave_id: str, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    leave = await service.db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.get("user_id") != user.get("user_id"):
        raise HTTPException(status_code=403, detail="Cannot cancel other's leave")
    
    if leave.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending requests")
    
    await service.db.leave_requests.update_one(
        {"leave_id": leave_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Leave request cancelled"}


# ==================== PAYROLL ROUTES ====================

@router.get("/payroll/calculate/{employee_id}")
async def calculate_payroll(employee_id: str, request: Request, month: str = None, year: int = None):
    service = get_service()
    
    now = datetime.now(timezone.utc)
    month = month or now.strftime("%B")
    year = year or now.year
    
    try:
        return await service.calculate_payroll(employee_id, month, year)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/payroll/generate")
async def generate_payroll(request: Request, month: str = None, year: int = None):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    now = datetime.now(timezone.utc)
    month = month or now.strftime("%B")
    year = year or now.year
    
    return await service.generate_payroll(month, year, user.get("user_id"))


@router.get("/payroll/records")
async def list_payroll_records(
    request: Request,
    month: Optional[str] = None,
    year: Optional[int] = None
):
    service = get_service()
    
    query = {}
    if month:
        query["month"] = month
    if year:
        query["year"] = year
    
    return await service.db.payroll.find(query, {"_id": 0}).sort("generated_at", -1).to_list(500)


@router.get("/payroll/my-records")
async def get_my_payroll(request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    employee = await service.get_employee_by_user(user.get("user_id"))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    return await service.db.payroll.find(
        {"employee_id": employee["employee_id"]},
        {"_id": 0}
    ).sort("generated_at", -1).to_list(24)
