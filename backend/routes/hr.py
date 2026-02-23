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
    password: Optional[str] = None  # Password for creating user account
    system_role: str = "technician"  # Role for the user
    # Additional fields from frontend
    personal_email: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    employee_code: Optional[str] = None
    work_location: Optional[str] = None
    shift: Optional[str] = None
    probation_period_months: Optional[int] = None
    pf_number: Optional[str] = None
    uan: Optional[str] = None
    esi_number: Optional[str] = None
    pf_enrolled: Optional[bool] = False
    esi_enrolled: Optional[bool] = False


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
    """Get current authenticated user - supports both session tokens and JWT"""
    # Try session token from cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user
    
    # Try Bearer token from header (JWT)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        import jwt
        import os
        try:
            JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
        except Exception:
            pass
    
    raise HTTPException(status_code=401, detail="Not authenticated")


# ==================== EMPLOYEE ROUTES ====================

@router.post("/employees")
async def create_employee(data: EmployeeCreateRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    try:
        return await service.create_employee(data.model_dump(), user.get("user_id"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create employee: {e}")
        raise HTTPException(status_code=500, detail="Failed to create employee")


@router.get("/employees")
async def list_employees(
    request: Request,
    department: Optional[str] = None,
    status: str = "active",
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List employees with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    service = get_service()

    # Build query for count
    query = {"status": status}
    if department:
        query["department"] = department
    total = await service.db.employees.count_documents(query)
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated data
    skip = (page - 1) * limit
    employees = await service.db.employees.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": employees,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


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
    year: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List payroll records with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    service = get_service()

    query = {}
    if month:
        query["month"] = month
    if year:
        query["year"] = year

    total = await service.db.payroll.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    records = await service.db.payroll.find(query, {"_id": 0}).sort("generated_at", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": records,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


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


# ==================== TDS ROUTES (P1) ====================

class TaxConfigUpdateRequest(BaseModel):
    """Employee tax configuration"""
    pan_number: Optional[str] = None
    tax_regime: str = "new"  # "new" or "old"
    declarations: dict = {}  # Chapter VIA declarations


class TDSChallanRequest(BaseModel):
    """TDS Challan deposit record"""
    quarter: str  # Q1, Q2, Q3, Q4
    financial_year: str
    challan_number: str
    deposit_date: str
    amount: float
    bank_name: Optional[str] = None


class TDSMarkDepositedRequest(BaseModel):
    """Mark TDS as deposited with challan details"""
    month: int
    year: int
    challan_number: str
    bsr_code: str
    deposit_date: str
    amount: float
    payment_mode: str = "net_banking"


@router.put("/employees/{employee_id}/tax-config")
async def update_employee_tax_config(
    employee_id: str,
    data: TaxConfigUpdateRequest,
    request: Request
):
    """
    Update employee tax configuration (Step 1)
    - PAN number with validation
    - Tax regime (New/Old)
    - Old regime declarations (HRA, 80C, 80D, etc.)
    """
    from services.tds_service import validate_pan
    
    service = get_service()
    
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Validate PAN if provided
    if data.pan_number:
        is_valid, message = validate_pan(data.pan_number)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
    
    tax_config = {
        "pan_number": data.pan_number.upper() if data.pan_number else None,
        "tax_regime": data.tax_regime,
        "declarations": data.declarations,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await service.db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {
            "tax_config": tax_config,
            "pan_number": tax_config["pan_number"]
        }}
    )
    
    return {
        "code": 0,
        "message": "Tax configuration updated",
        "tax_config": tax_config
    }


@router.get("/employees/{employee_id}/tax-config")
async def get_employee_tax_config(employee_id: str, request: Request):
    """Get employee tax configuration"""
    service = get_service()
    
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "employee_id": employee_id,
        "tax_config": employee.get("tax_config", {
            "pan_number": employee.get("pan_number"),
            "tax_regime": "new",
            "declarations": {}
        })
    }


@router.get("/tds/calculate/{employee_id}")
async def calculate_employee_tds(
    employee_id: str,
    request: Request,
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None)
):
    """
    Calculate TDS for an employee (Step 2)
    
    Returns:
    - Annual tax calculation breakdown
    - Monthly TDS amount
    - YTD TDS deducted
    """
    from services.tds_service import init_tds_service, get_tds_calculator
    
    service = get_service()
    
    # Initialize TDS service if not done
    try:
        tds_calc = get_tds_calculator()
    except:
        init_tds_service(service.db)
        tds_calc = get_tds_calculator()
    
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Default to current month
    now = datetime.now(timezone.utc)
    month = month or now.month
    year = year or now.year
    
    # Get tax config
    tax_config = employee.get("tax_config", {
        "pan_number": employee.get("pan_number"),
        "tax_regime": "new",
        "declarations": {}
    })
    
    # Get salary structure
    salary_structure = employee.get("salary_structure", {})
    
    # Determine financial year
    fy_start_year = year if month >= 4 else year - 1
    financial_year = f"{fy_start_year}-{str(fy_start_year + 1)[-2:]}"
    
    # Get YTD TDS
    ytd_tds = await tds_calc.get_ytd_tds(employee_id, financial_year)
    
    # Calculate monthly TDS
    result = await tds_calc.calculate_monthly_tds(
        employee_id=employee_id,
        month=month,
        year=year,
        salary_structure=salary_structure,
        tax_config=tax_config,
        ytd_tds_deducted=ytd_tds
    )
    
    return {
        "code": 0,
        "employee_id": employee_id,
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
        **result
    }


@router.get("/payroll/tds-summary")
async def get_tds_summary(
    request: Request,
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None)
):
    """
    Get TDS summary for all employees (Step 4)
    
    Shows:
    - Per employee TDS breakdown
    - Total TDS this month
    - Total TDS YTD
    - TDS due date alerts
    """
    from services.tds_service import init_tds_service, get_tds_calculator
    
    service = get_service()
    
    # Initialize TDS service if not done
    try:
        tds_calc = get_tds_calculator()
    except:
        init_tds_service(service.db)
        tds_calc = get_tds_calculator()
    
    now = datetime.now(timezone.utc)
    month = month or now.month
    year = year or now.year
    
    # Get all active employees
    employees = await service.list_employees(status="active")
    
    # Calculate TDS for each
    summary = []
    total_tds_month = 0
    total_tds_ytd = 0
    
    fy_start_year = year if month >= 4 else year - 1
    financial_year = f"{fy_start_year}-{str(fy_start_year + 1)[-2:]}"
    
    for emp in employees:
        tax_config = emp.get("tax_config", {
            "pan_number": emp.get("pan_number"),
            "tax_regime": "new",
            "declarations": {}
        })
        salary_structure = emp.get("salary_structure", {})
        
        ytd_tds = await tds_calc.get_ytd_tds(emp["employee_id"], financial_year)
        
        try:
            result = await tds_calc.calculate_monthly_tds(
                employee_id=emp["employee_id"],
                month=month,
                year=year,
                salary_structure=salary_structure,
                tax_config=tax_config,
                ytd_tds_deducted=ytd_tds
            )
            
            summary.append({
                "employee_id": emp["employee_id"],
                "employee_name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
                "pan_number": tax_config.get("pan_number"),
                "tax_regime": tax_config.get("tax_regime", "new"),
                "gross_monthly": salary_structure.get("basic", 0) + salary_structure.get("hra", 0) + 
                                salary_structure.get("da", 0) + salary_structure.get("special_allowance", 0),
                "annual_tax_liability": result["annual_tax_liability"],
                "monthly_tds": result["monthly_tds"],
                "ytd_tds": ytd_tds
            })
            
            total_tds_month += result["monthly_tds"]
            total_tds_ytd += ytd_tds
            
        except Exception as e:
            logger.warning(f"Failed to calculate TDS for {emp['employee_id']}: {e}")
    
    # TDS due date calculation
    # TDS due by 7th of next month
    if month == 12:
        due_month = 1
        due_year = year + 1
    else:
        due_month = month + 1
        due_year = year
    
    due_date = f"{due_year}-{str(due_month).zfill(2)}-07"
    
    # Check if overdue
    is_overdue = False
    is_due_soon = False
    current_day = now.day
    
    if now.month == due_month and now.year == due_year:
        if current_day <= 7:
            is_due_soon = True
        else:
            is_overdue = True
    elif (now.year > due_year) or (now.year == due_year and now.month > due_month):
        is_overdue = True
    
    return {
        "code": 0,
        "month": month,
        "year": year,
        "financial_year": financial_year,
        "employees": summary,
        "total_tds_this_month": round(total_tds_month, 2),
        "total_tds_ytd": round(total_tds_ytd, 2),
        "tds_due_date": due_date,
        "tds_due_alert": {
            "is_due_soon": is_due_soon,
            "is_overdue": is_overdue,
            "message": (
                f"TDS OVERDUE — ₹{total_tds_month:,.0f} was due on 7th. Interest @ 1.5% per month applies under Section 201(1A)."
                if is_overdue else
                f"TDS for last month due by 7th. Amount: ₹{total_tds_month:,.0f}. Mark as deposited after payment."
                if is_due_soon else None
            )
        }
    }


@router.post("/tds/challan")
async def record_tds_challan(data: TDSChallanRequest, request: Request):
    """Record TDS challan deposit"""
    import uuid
    
    service = get_service()
    user = await get_current_user(request, service.db)
    org_id = await get_org_id(request, service.db)
    
    challan_id = f"challan_{uuid.uuid4().hex[:12]}"
    
    challan = {
        "challan_id": challan_id,
        "organization_id": org_id,
        "quarter": data.quarter,
        "financial_year": data.financial_year,
        "challan_number": data.challan_number,
        "deposit_date": data.deposit_date,
        "amount": data.amount,
        "bank_name": data.bank_name,
        "recorded_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await service.db.tds_challans.insert_one(challan)
    
    return {
        "code": 0,
        "message": "TDS challan recorded",
        "challan": {k: v for k, v in challan.items() if k != "_id"}
    }


@router.post("/payroll/tds/mark-deposited")
async def mark_tds_deposited(data: TDSMarkDepositedRequest, request: Request):
    """
    Mark TDS as deposited with journal entry posting
    
    POST /api/payroll/tds/mark-deposited
    Payload: month, year, challan_number, bsr_code, deposit_date, amount, payment_mode
    
    Actions:
    - Validate challan_number is not duplicate
    - Post journal entry: DEBIT TDS Payable, CREDIT Bank
    - Update tds_deposit_status = DEPOSITED
    - Store challan_number, bsr_code against payroll month record
    - Return updated TDS summary
    """
    import uuid
    from services.double_entry_service import get_double_entry_service, init_double_entry_service
    
    service = get_service()
    user = await get_current_user(request, service.db)
    org_id = await get_org_id(request, service.db)
    
    # Validate challan_number is not duplicate
    existing_challan = await service.db.tds_challans.find_one({
        "organization_id": org_id,
        "challan_number": data.challan_number
    })
    
    if existing_challan:
        raise HTTPException(
            status_code=400, 
            detail=f"Challan number {data.challan_number} already exists. Cannot record duplicate."
        )
    
    # Determine quarter and financial year
    quarter = "Q4" if data.month <= 3 else "Q1" if data.month <= 6 else "Q2" if data.month <= 9 else "Q3"
    fy = f"{data.year}-{str(data.year + 1)[-2:]}" if data.month >= 4 else f"{data.year - 1}-{str(data.year)[-2:]}"
    
    month_names = ["", "January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    month_name = month_names[data.month]
    
    # Create challan record
    challan_id = f"challan_{uuid.uuid4().hex[:12]}"
    challan = {
        "challan_id": challan_id,
        "organization_id": org_id,
        "quarter": quarter,
        "financial_year": fy,
        "challan_number": data.challan_number,
        "bsr_code": data.bsr_code,
        "deposit_date": data.deposit_date,
        "amount": data.amount,
        "payment_mode": data.payment_mode,
        "month": data.month,
        "year": data.year,
        "status": "DEPOSITED",
        "recorded_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await service.db.tds_challans.insert_one(challan)
    
    # Post journal entry: DEBIT TDS Payable, CREDIT Bank
    try:
        try:
            de_service = get_double_entry_service()
        except:
            init_double_entry_service(service.db)
            de_service = get_double_entry_service()
        
        # Ensure system accounts exist
        await de_service.ensure_system_accounts(org_id)
        
        # Get TDS Payable and Bank accounts
        tds_payable = await de_service.get_account_by_code(org_id, "2320")  # TDS Payable
        bank_account = await de_service.get_account_by_code(org_id, "1200")  # Bank
        
        if tds_payable and bank_account:
            # Create journal entry
            narration = f"TDS deposit {month_name}/{data.year} — Challan: {data.challan_number} | BSR: {data.bsr_code} | Date: {data.deposit_date}"
            
            success, msg, entry = await de_service.create_journal_entry(
                organization_id=org_id,
                entry_date=data.deposit_date,
                description=narration,
                lines=[
                    {
                        "account_id": tds_payable["account_id"],
                        "debit_amount": data.amount,
                        "credit_amount": 0,
                        "description": f"TDS deposit for {month_name} {data.year}"
                    },
                    {
                        "account_id": bank_account["account_id"],
                        "debit_amount": 0,
                        "credit_amount": data.amount,
                        "description": f"TDS payment via {data.payment_mode} - Challan {data.challan_number}"
                    }
                ],
                entry_type="PAYMENT",
                source_document_id=challan_id,
                source_document_type="TDS_CHALLAN",
                created_by=user.get("user_id")
            )
            
            if success:
                logger.info(f"Posted TDS deposit journal entry: {entry.get('entry_id')}")
                challan["journal_entry_id"] = entry.get("entry_id")
                await service.db.tds_challans.update_one(
                    {"challan_id": challan_id},
                    {"$set": {"journal_entry_id": entry.get("entry_id")}}
                )
            else:
                logger.warning(f"Failed to post TDS journal entry: {msg}")
    except Exception as e:
        logger.warning(f"Failed to post TDS journal entry: {e}")
    
    # Update payroll records for this month with deposit status
    await service.db.payroll.update_many(
        {"organization_id": org_id, "month": month_name, "year": data.year},
        {"$set": {"tds_deposit_status": "DEPOSITED", "tds_challan_number": data.challan_number}}
    )
    
    # Fetch updated TDS summary to return
    from services.tds_service import init_tds_service, get_tds_calculator
    try:
        tds_calc = get_tds_calculator()
    except:
        init_tds_service(service.db)
        tds_calc = get_tds_calculator()
    
    # Get all active employees and calculate summary
    employees = await service.list_employees(status="active")
    total_tds_month = 0
    
    for emp in employees:
        tax_config = emp.get("tax_config", {"pan_number": emp.get("pan_number"), "tax_regime": "new", "declarations": {}})
        salary_structure = emp.get("salary_structure", {})
        ytd_tds = await tds_calc.get_ytd_tds(emp["employee_id"], fy)
        
        try:
            result = await tds_calc.calculate_monthly_tds(
                employee_id=emp["employee_id"],
                month=data.month,
                year=data.year,
                salary_structure=salary_structure,
                tax_config=tax_config,
                ytd_tds_deducted=ytd_tds
            )
            total_tds_month += result.get("monthly_tds", 0)
        except:
            pass
    
    # Get all challans YTD
    challans = await service.db.tds_challans.find(
        {"organization_id": org_id, "financial_year": fy},
        {"_id": 0}
    ).to_list(100)
    
    tds_deposited_ytd = sum(c.get("amount", 0) for c in challans)
    
    return {
        "code": 0,
        "message": f"TDS deposited — Challan {data.challan_number} recorded",
        "challan": {k: v for k, v in challan.items() if k != "_id"},
        "tds_summary": {
            "total_tds_this_month": round(total_tds_month, 2),
            "tds_deposited_ytd": round(tds_deposited_ytd, 2),
            "deposit_status": "UP_TO_DATE"
        }
    }


@router.get("/payroll/tds/export")
async def export_tds_data(
    request: Request,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...)
):
    """
    Export TDS data as CSV
    
    GET /api/payroll/tds/export?month={m}&year={y}
    
    CSV columns:
    Employee Name, PAN, Designation, Gross Salary, Taxable Income, New/Old Regime,
    80C Deductions, 80D Deductions, HRA Exemption, Standard Deduction, Net Taxable Income,
    Annual Tax, Monthly TDS, YTD TDS Deducted, YTD TDS Deposited, Balance TDS Pending
    """
    from services.tds_service import init_tds_service, get_tds_calculator
    import io
    import csv
    from fastapi.responses import StreamingResponse
    
    service = get_service()
    org_id = await get_org_id(request, service.db)
    
    # Initialize TDS service
    try:
        tds_calc = get_tds_calculator()
    except:
        init_tds_service(service.db)
        tds_calc = get_tds_calculator()
    
    # Determine FY
    fy_start_year = year if month >= 4 else year - 1
    financial_year = f"{fy_start_year}-{str(fy_start_year + 1)[-2:]}"
    
    # Get employees
    employees = await service.list_employees(status="active")
    
    # Get challans for YTD deposited
    challans = await service.db.tds_challans.find(
        {"organization_id": org_id, "financial_year": financial_year},
        {"_id": 0}
    ).to_list(100)
    tds_deposited_ytd = sum(c.get("amount", 0) for c in challans)
    
    # Build CSV data
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    
    # Header row
    writer.writerow([
        "Employee Name", "PAN", "Designation", "Gross Salary (Annual)", "Taxable Income",
        "Tax Regime", "80C Deductions", "80D Deductions", "HRA Exemption", "Standard Deduction",
        "Net Taxable Income", "Annual Tax", "Monthly TDS", "YTD TDS Deducted",
        "YTD TDS Deposited", "Balance TDS Pending"
    ])
    
    total_ytd_tds = 0
    
    for emp in employees:
        tax_config = emp.get("tax_config", {"pan_number": emp.get("pan_number"), "tax_regime": "new", "declarations": {}})
        salary_structure = emp.get("salary_structure", {})
        
        ytd_tds = await tds_calc.get_ytd_tds(emp["employee_id"], financial_year)
        total_ytd_tds += ytd_tds
        
        try:
            result = await tds_calc.calculate_monthly_tds(
                employee_id=emp["employee_id"],
                month=month,
                year=year,
                salary_structure=salary_structure,
                tax_config=tax_config,
                ytd_tds_deducted=ytd_tds
            )
            
            annual_calc = result.get("annual_calculation", {})
            breakdown = annual_calc.get("breakdown", {})
            chapter_via = breakdown.get("chapter_via", {})
            
            # Calculate gross annual
            basic = salary_structure.get("basic", 0)
            hra = salary_structure.get("hra", 0)
            da = salary_structure.get("da", 0)
            special = salary_structure.get("special_allowance", 0)
            gross_annual = (basic + hra + da + special) * 12
            
            writer.writerow([
                f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
                tax_config.get("pan_number") or "PAN MISSING",
                emp.get("designation", ""),
                round(gross_annual, 2),
                round(annual_calc.get("taxable_income", 0), 2),
                (tax_config.get("tax_regime") or "new").upper(),
                round(chapter_via.get("80C", 0), 2),
                round(chapter_via.get("80D", 0), 2),
                round(breakdown.get("hra_exemption", 0), 2),
                round(annual_calc.get("standard_deduction", 50000), 2),
                round(annual_calc.get("taxable_income", 0), 2),
                round(annual_calc.get("total_tax_liability", 0), 2),
                round(result.get("monthly_tds", 0), 2),
                round(ytd_tds, 2),
                round(tds_deposited_ytd, 2),
                round(ytd_tds - tds_deposited_ytd, 2)
            ])
        except Exception as e:
            logger.warning(f"Failed to calculate TDS for {emp['employee_id']}: {e}")
            writer.writerow([
                f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
                emp.get("pan_number", "PAN MISSING"),
                emp.get("designation", ""),
                0, 0, "NEW", 0, 0, 0, 50000, 0, 0, 0, 0, 0, 0
            ])
    
    csv_buffer.seek(0)
    
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    filename = f"TDS_Summary_{month_names[month]}_{year}.csv"
    
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/tds/challans")
async def list_tds_challans(
    request: Request,
    financial_year: Optional[str] = None
):
    """List TDS challans"""
    service = get_service()
    org_id = await get_org_id(request, service.db)
    
    query = {"organization_id": org_id}
    if financial_year:
        query["financial_year"] = financial_year
    
    challans = await service.db.tds_challans.find(query, {"_id": 0}).sort("deposit_date", -1).to_list(100)
    
    return {"code": 0, "challans": challans}


@router.get("/payroll/form16/{employee_id}/{fy}")
async def get_form16_data(
    employee_id: str,
    fy: str,
    request: Request
):
    """
    Get Form 16 data for an employee
    
    GET /api/payroll/form16/{employee_id}/{fy}
    FY format: "2024-25"
    
    Returns structured JSON with:
    - employee: name, pan, designation, period_from, period_to
    - employer: name, tan, pan, address, category
    - part_a: quarters with TDS deducted/deposited, challan_details
    - part_b: Full tax computation breakdown
    """
    from services.tds_service import init_tds_service, get_form16_generator
    
    service = get_service()
    org_id = await get_org_id(request, service.db)
    
    # Parse FY (format: "2024-25")
    try:
        fy_start_year = int(fy.split("-")[0])
        fy_end_year = fy_start_year + 1
        assessment_year = f"{fy_end_year}-{str(fy_end_year + 1)[-2:]}"
    except:
        raise HTTPException(status_code=400, detail="Invalid FY format. Expected: 2024-25")
    
    # Initialize TDS service if not done
    try:
        form16_gen = get_form16_generator()
    except:
        init_tds_service(service.db)
        form16_gen = get_form16_generator()
    
    # Get employee
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if employee has payroll data for this FY
    payroll_records = await service.db.payroll.find({
        "employee_id": employee_id,
        "$or": [
            {"year": fy_start_year, "month": {"$in": ["April", "May", "June", "July", "August", "September", "October", "November", "December"]}},
            {"year": fy_end_year, "month": {"$in": ["January", "February", "March"]}}
        ],
        "status": {"$in": ["processed", "paid"]}
    }, {"_id": 0}).to_list(12)
    
    if not payroll_records:
        raise HTTPException(
            status_code=404, 
            detail=f"No payroll data found for this employee in FY {fy}"
        )
    
    # Get employer details
    org = await service.db.organizations.find_one(
        {"organization_id": org_id},
        {"_id": 0}
    ) or {}
    
    employer_details = {
        "organization_id": org_id,
        "tan": org.get("tan_number"),
        "pan": org.get("pan_number", org.get("gstin", "")[2:12] if org.get("gstin") else None),
        "name": org.get("company_name", org.get("name")),
        "address": f"{org.get('address', '')} {org.get('city', '')} {org.get('pincode', '')}".strip(),
        "category": org.get("category", "Company")
    }
    
    # Get TDS challans for quarters
    challans = await service.db.tds_challans.find({
        "organization_id": org_id,
        "financial_year": fy
    }, {"_id": 0}).to_list(100)
    
    tax_config = employee.get("tax_config", {
        "pan_number": employee.get("pan_number"),
        "tax_regime": "new",
        "declarations": {}
    })
    
    # Build quarters data
    quarters = []
    quarter_defs = [
        {"quarter": "Q1", "period": f"Apr-Jun {fy_start_year}", "months": ["April", "May", "June"], "year": fy_start_year},
        {"quarter": "Q2", "period": f"Jul-Sep {fy_start_year}", "months": ["July", "August", "September"], "year": fy_start_year},
        {"quarter": "Q3", "period": f"Oct-Dec {fy_start_year}", "months": ["October", "November", "December"], "year": fy_start_year},
        {"quarter": "Q4", "period": f"Jan-Mar {fy_end_year}", "months": ["January", "February", "March"], "year": fy_end_year}
    ]
    
    total_tds_deducted = 0
    total_tds_deposited = 0
    
    for q_def in quarter_defs:
        # TDS deducted in quarter
        q_payroll = [p for p in payroll_records if p.get("month") in q_def["months"] and p.get("year") == q_def["year"]]
        q_tds_deducted = sum(p.get("deductions", {}).get("tds", 0) for p in q_payroll)
        total_tds_deducted += q_tds_deducted
        
        # TDS deposited (from challans)
        q_challans = [c for c in challans if c.get("quarter") == q_def["quarter"]]
        q_tds_deposited = sum(c.get("amount", 0) for c in q_challans)
        total_tds_deposited += q_tds_deposited
        
        quarters.append({
            "quarter": q_def["quarter"],
            "period": q_def["period"],
            "tds_deducted": round(q_tds_deducted, 2),
            "tds_deposited": round(q_tds_deposited, 2),
            "challan_details": [
                {
                    "challan_number": c.get("challan_number"),
                    "bsr_code": c.get("bsr_code"),
                    "date": c.get("deposit_date"),
                    "amount": c.get("amount", 0)
                } for c in q_challans
            ]
        })
    
    # Calculate tax computation using TDS service
    salary_structure = employee.get("salary_structure", {})
    
    try:
        from services.tds_service import get_tds_calculator
        tds_calc = get_tds_calculator()
        
        annual_calc = await tds_calc.calculate_annual_tax(
            employee_id=employee_id,
            financial_year=fy,
            salary_structure=salary_structure,
            tax_config=tax_config
        )
    except Exception as e:
        logger.warning(f"Tax calculation failed: {e}")
        annual_calc = {"gross_annual": 0, "taxable_income": 0, "total_tax_liability": 0, "breakdown": {}}
    
    breakdown = annual_calc.get("breakdown", {})
    chapter_via = breakdown.get("chapter_via", {})
    
    # Build Form 16 response
    form16_data = {
        "employee": {
            "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
            "pan": tax_config.get("pan_number") or employee.get("pan_number"),
            "designation": employee.get("designation"),
            "period_from": f"{fy_start_year}-04-01",
            "period_to": f"{fy_end_year}-03-31"
        },
        "employer": {
            "name": employer_details.get("name"),
            "tan": employer_details.get("tan"),
            "pan": employer_details.get("pan"),
            "address": employer_details.get("address"),
            "category": employer_details.get("category")
        },
        "part_a": {
            "quarters": quarters,
            "total_tds_deducted": round(total_tds_deducted, 2),
            "total_tds_deposited": round(total_tds_deposited, 2)
        },
        "part_b": {
            "gross_salary": round(annual_calc.get("gross_annual", 0), 2),
            "hra_exemption": round(breakdown.get("hra_exemption", 0), 2),
            "standard_deduction": round(annual_calc.get("standard_deduction", 50000), 2),
            "deduction_80c": round(chapter_via.get("80C", 0), 2),
            "deduction_80d": round(chapter_via.get("80D", 0), 2),
            "deduction_80ccd": round(chapter_via.get("80CCD_1B", 0), 2),
            "other_deductions": round(
                chapter_via.get("80E", 0) + chapter_via.get("80G", 0) + chapter_via.get("80TTA", 0), 2
            ),
            "net_taxable_income": round(annual_calc.get("taxable_income", 0), 2),
            "tax_on_income": round(annual_calc.get("tax_before_rebate", 0), 2),
            "rebate_87a": round(annual_calc.get("rebate_87a", 0), 2),
            "surcharge": round(annual_calc.get("surcharge", 0), 2),
            "cess": round(annual_calc.get("cess", 0), 2),
            "total_tax_liability": round(annual_calc.get("total_tax_liability", 0), 2),
            "tds_deducted": round(total_tds_deducted, 2),
            "balance_tax_payable": round(
                annual_calc.get("total_tax_liability", 0) - total_tds_deducted, 2
            )
        }
    }
    
    return {"code": 0, "form16": form16_data}


# Helper for org_id
async def get_org_id(request: Request, db) -> Optional[str]:
    """Extract organization ID from request"""
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            import jwt
            import os
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, os.environ.get("JWT_SECRET", "battwheels-secret"), algorithms=["HS256"])
            return payload.get("org_id")
    except:
        pass
    return None

