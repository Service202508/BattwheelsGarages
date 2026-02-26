"""
Battwheels OS - HR & Payroll Routes (extracted from server.py)
Employees CRUD, Attendance, Leave, Payroll
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import logging

from utils.auth import create_access_token, hash_password
from schemas.models import (
    Employee, EmployeeCreate, EmployeeUpdate,
    EmployeeSalaryStructure, EmployeeCompliance, EmployeeBankDetails,
    AttendanceRecord, ClockInRequest, ClockOutRequest,
    LeaveType, LeaveBalance, LeaveRequest, LeaveRequestCreate, LeaveApproval,
    PayrollRecord,
)
from core.tenant.context import TenantContext, tenant_context_required

logger = logging.getLogger(__name__)

router = APIRouter(tags=["HR & Payroll Core"])
db = None

EMPLOYEE_ROLES = ["admin", "manager", "technician", "accountant", "customer_support"]
EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "intern", "probation"]
DEPARTMENTS = ["operations", "hr", "finance", "service", "sales", "administration"]

def init_router(database):
    global db
    db = database

@router.post("/employees")
async def create_employee(data: EmployeeCreate, request: Request):
    """Create a new employee with user account"""
    admin_user = await require_admin(request)
    
    # Check if work email already exists
    existing_user = await db.users.find_one({"email": data.work_email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Get reporting manager name if provided
    reporting_manager_name = None
    if data.reporting_manager_id:
        manager = await db.employees.find_one({"employee_id": data.reporting_manager_id}, {"_id": 0})
        if manager:
            reporting_manager_name = manager.get("full_name")
    
    # Calculate gross salary
    gross_salary = (
        data.basic_salary + data.hra + data.da + 
        data.conveyance + data.medical_allowance + 
        data.special_allowance + data.other_allowances
    )
    
    # Calculate deductions
    deductions = calculate_salary_deductions(
        data.basic_salary, gross_salary, 
        data.pf_enrolled, data.esi_enrolled
    )
    
    total_deductions = sum(deductions.values())
    net_salary = gross_salary - total_deductions
    
    # Create salary structure
    salary_structure = EmployeeSalaryStructure(
        basic_salary=data.basic_salary,
        hra=data.hra,
        da=data.da,
        conveyance=data.conveyance,
        medical_allowance=data.medical_allowance,
        special_allowance=data.special_allowance,
        other_allowances=data.other_allowances,
        gross_salary=gross_salary,
        pf_deduction=deductions["pf_deduction"],
        esi_deduction=deductions["esi_deduction"],
        professional_tax=deductions["professional_tax"],
        tds=deductions["tds"],
        net_salary=net_salary
    )
    
    # Create compliance
    compliance = EmployeeCompliance(
        pan_number=data.pan_number,
        aadhaar_number=data.aadhaar_number,
        pf_number=data.pf_number,
        uan=data.uan,
        esi_number=data.esi_number,
        pf_enrolled=data.pf_enrolled,
        esi_enrolled=data.esi_enrolled
    )
    
    # Create bank details
    bank_details = EmployeeBankDetails(
        bank_name=data.bank_name,
        account_number=data.account_number,
        ifsc_code=data.ifsc_code,
        branch_name=data.branch_name,
        account_type=data.account_type
    )
    
    # Create user account first
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": data.work_email,
        "password_hash": hash_password(data.password),
        "name": f"{data.first_name} {data.last_name}",
        "role": data.system_role,
        "designation": data.designation,
        "phone": data.phone,
        "picture": None,
        "is_active": True,
        "department": data.department,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Generate employee code if not provided
    employee_code = data.employee_code
    if not employee_code:
        count = await db.employees.count_documents({})
        employee_code = f"EMP{str(count + 1).zfill(4)}"
    
    # Create employee record
    employee = Employee(
        user_id=user_id,
        first_name=data.first_name,
        last_name=data.last_name,
        full_name=f"{data.first_name} {data.last_name}",
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        personal_email=data.personal_email,
        phone=data.phone,
        alternate_phone=data.alternate_phone,
        current_address=data.current_address,
        permanent_address=data.permanent_address,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        emergency_contact_name=data.emergency_contact_name,
        emergency_contact_phone=data.emergency_contact_phone,
        emergency_contact_relation=data.emergency_contact_relation,
        employee_code=employee_code,
        work_email=data.work_email,
        department=data.department,
        designation=data.designation,
        employment_type=data.employment_type,
        joining_date=data.joining_date,
        probation_period_months=data.probation_period_months,
        reporting_manager_id=data.reporting_manager_id,
        reporting_manager_name=reporting_manager_name,
        work_location=data.work_location,
        shift=data.shift,
        system_role=data.system_role,
        salary=salary_structure,
        compliance=compliance,
        bank_details=bank_details,
        created_by=admin_user.user_id
    )
    
    doc = employee.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.employees.insert_one(doc)
    
    # Initialize leave balance for the employee
    current_year = datetime.now(timezone.utc).year
    leave_balance = {
        "user_id": user_id,
        "year": current_year,
        "balances": {
            "CL": {"total": 12, "used": 0, "pending": 0},
            "SL": {"total": 6, "used": 0, "pending": 0},
            "PL": {"total": 0, "used": 0, "pending": 0},
            "EL": {"total": 15, "used": 0, "pending": 0},
            "LWP": {"total": 365, "used": 0, "pending": 0},
            "CO": {"total": 10, "used": 0, "pending": 0}
        }
    }
    await db.leave_balances.insert_one(leave_balance)
    
    return employee.model_dump()

@router.get("/employees")
async def get_employees(
    request: Request,
    department: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None
):
    """Get all employees with optional filters"""
    await require_auth(request)
    
    query = {}
    if department:
        query["department"] = department
    if status:
        query["status"] = status
    if role:
        query["system_role"] = role
    
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    return employees

@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, request: Request):
    """Get single employee details"""
    await require_auth(request)
    
    employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeUpdate, request: Request):
    """Update employee details"""
    await require_admin(request)
    
    employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Handle salary updates
    salary_fields = ["basic_salary", "hra", "da", "conveyance", "medical_allowance", "special_allowance", "other_allowances"]
    salary_updated = any(field in update_dict for field in salary_fields)
    
    if salary_updated:
        current_salary = employee.get("salary", {})
        for field in salary_fields:
            if field in update_dict:
                current_salary[field] = update_dict.pop(field)
        
        # Recalculate gross
        gross_salary = (
            current_salary.get("basic_salary", 0) + current_salary.get("hra", 0) +
            current_salary.get("da", 0) + current_salary.get("conveyance", 0) +
            current_salary.get("medical_allowance", 0) + current_salary.get("special_allowance", 0) +
            current_salary.get("other_allowances", 0)
        )
        current_salary["gross_salary"] = gross_salary
        
        # Recalculate deductions
        compliance = employee.get("compliance", {})
        pf_enrolled = data.pf_enrolled if data.pf_enrolled is not None else compliance.get("pf_enrolled", False)
        esi_enrolled = data.esi_enrolled if data.esi_enrolled is not None else compliance.get("esi_enrolled", False)
        
        deductions = calculate_salary_deductions(
            current_salary.get("basic_salary", 0), gross_salary,
            pf_enrolled, esi_enrolled
        )
        
        current_salary["pf_deduction"] = deductions["pf_deduction"]
        current_salary["esi_deduction"] = deductions["esi_deduction"]
        current_salary["professional_tax"] = deductions["professional_tax"]
        current_salary["tds"] = deductions["tds"]
        current_salary["net_salary"] = gross_salary - sum(deductions.values())
        
        update_dict["salary"] = current_salary
    
    # Handle compliance updates
    compliance_fields = ["pan_number", "aadhaar_number", "pf_number", "uan", "esi_number", "pf_enrolled", "esi_enrolled"]
    compliance_updated = any(field in update_dict for field in compliance_fields)
    
    if compliance_updated:
        current_compliance = employee.get("compliance", {})
        for field in compliance_fields:
            if field in update_dict:
                current_compliance[field] = update_dict.pop(field)
        update_dict["compliance"] = current_compliance
    
    # Handle bank details updates
    bank_fields = ["bank_name", "account_number", "ifsc_code", "branch_name", "account_type"]
    bank_updated = any(field in update_dict for field in bank_fields)
    
    if bank_updated:
        current_bank = employee.get("bank_details", {})
        for field in bank_fields:
            if field in update_dict:
                current_bank[field] = update_dict.pop(field)
        update_dict["bank_details"] = current_bank
    
    # Update full name if first or last name changed
    if "first_name" in update_dict or "last_name" in update_dict:
        first_name = update_dict.get("first_name", employee.get("first_name", ""))
        last_name = update_dict.get("last_name", employee.get("last_name", ""))
        update_dict["full_name"] = f"{first_name} {last_name}"
    
    # Update reporting manager name if manager changed
    if "reporting_manager_id" in update_dict and update_dict["reporting_manager_id"]:
        manager = await db.employees.find_one(
            {"employee_id": update_dict["reporting_manager_id"]}, {"_id": 0}
        )
        if manager:
            update_dict["reporting_manager_name"] = manager.get("full_name")
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.employees.update_one({"employee_id": employee_id}, {"$set": update_dict})
    
    # Update linked user account if role or designation changed
    if employee.get("user_id"):
        user_updates = {}
        if data.system_role:
            user_updates["role"] = data.system_role
        if data.designation:
            user_updates["designation"] = data.designation
        if data.department:
            user_updates["department"] = data.department
        if "full_name" in update_dict:
            user_updates["name"] = update_dict["full_name"]
        if data.status == "inactive" or data.status == "terminated":
            user_updates["is_active"] = False
        elif data.status == "active":
            user_updates["is_active"] = True
        
        if user_updates:
            await db.users.update_one(
                {"user_id": employee["user_id"]},
                {"$set": user_updates}
            )
    
    updated = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    return updated

@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str, request: Request):
    """Deactivate an employee (soft delete)"""
    await require_admin(request)
    
    employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Soft delete - mark as terminated
    await db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {
            "status": "terminated",
            "termination_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Deactivate linked user account
    if employee.get("user_id"):
        await db.users.update_one(
            {"user_id": employee["user_id"]},
            {"$set": {"is_active": False}}
        )
    
    return {"message": "Employee deactivated successfully"}

@router.get("/employees/managers/list")
async def get_managers(request: Request):
    """Get list of employees who can be managers (all active employees)"""
    await require_auth(request)
    
    # Return all active employees as potential reporting managers
    # In HRMS, any employee can potentially be a reporting manager
    managers = await db.employees.find(
        {"status": "active"},
        {"_id": 0, "employee_id": 1, "full_name": 1, "first_name": 1, "last_name": 1, "designation": 1, "department": 1, "system_role": 1}
    ).to_list(500)
    
    # Ensure full_name is populated
    for m in managers:
        if not m.get("full_name"):
            first = m.get("first_name", "")
            last = m.get("last_name", "")
            m["full_name"] = f"{first} {last}".strip() or "Unknown"
    
    return managers

@router.get("/employees/departments/list")
async def get_departments(request: Request):
    """Get list of departments"""
    await require_auth(request)
    return DEPARTMENTS

@router.get("/employees/roles/list")
async def get_roles(request: Request):
    """Get list of available roles"""
    await require_auth(request)
    return [
        {"value": "admin", "label": "Admin", "description": "Full access to all modules"},
        {"value": "manager", "label": "Manager", "description": "HR + Reports access"},
        {"value": "technician", "label": "Technician", "description": "Tickets + Job Cards access"},
        {"value": "accountant", "label": "Accountant", "description": "Finance modules only"},
        {"value": "customer_support", "label": "Customer Support", "description": "Tickets only"}
    ]

# ==================== ATTENDANCE ROUTES ====================

@router.post("/attendance/clock-in")
async def clock_in(data: ClockInRequest, request: Request):
    """Clock in for the day"""
    user = await require_auth(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc)
    
    # Check if already clocked in today
    existing = await db.attendance.find_one(
        {"user_id": user.user_id, "date": today}, {"_id": 0}
    )
    
    if existing and existing.get("clock_in"):
        raise HTTPException(status_code=400, detail="Already clocked in today")
    
    # Check for late arrival
    current_time = now.strftime("%H:%M")
    standard_start = datetime.strptime(STANDARD_START_TIME, "%H:%M")
    actual_start = datetime.strptime(current_time, "%H:%M")
    late_arrival = (actual_start - standard_start).total_seconds() > LATE_THRESHOLD_MINUTES * 60
    
    attendance_doc = {
        "attendance_id": f"att_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "user_name": user.name,
        "date": today,
        "clock_in": now.isoformat(),
        "clock_out": None,
        "break_minutes": 0,
        "total_hours": 0.0,
        "overtime_hours": 0.0,
        "status": "present",
        "early_departure": False,
        "late_arrival": late_arrival,
        "remarks": data.remarks,
        "location": data.location,
        "ip_address": request.client.host if request.client else None,
        "created_at": now.isoformat()
    }
    
    if existing:
        await db.attendance.update_one(
            {"user_id": user.user_id, "date": today},
            {"$set": attendance_doc}
        )
    else:
        await db.attendance.insert_one(attendance_doc)
    
    return {
        "message": "Clocked in successfully",
        "clock_in": now.isoformat(),
        "late_arrival": late_arrival,
        "late_by_minutes": int((actual_start - standard_start).total_seconds() / 60) if late_arrival else 0
    }

@router.post("/attendance/clock-out")
async def clock_out(data: ClockOutRequest, request: Request):
    """Clock out for the day"""
    user = await require_auth(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc)
    
    # Find today's attendance
    existing = await db.attendance.find_one(
        {"user_id": user.user_id, "date": today}, {"_id": 0}
    )
    
    if not existing:
        raise HTTPException(status_code=400, detail="Not clocked in today")
    
    if existing.get("clock_out"):
        raise HTTPException(status_code=400, detail="Already clocked out today")
    
    # Calculate hours worked
    clock_in_time = datetime.fromisoformat(existing["clock_in"].replace('Z', '+00:00'))
    total_minutes = (now - clock_in_time).total_seconds() / 60
    break_minutes = data.break_minutes or 0
    worked_minutes = total_minutes - break_minutes
    total_hours = round(worked_minutes / 60, 2)
    
    # Check for early departure
    current_time = now.strftime("%H:%M")
    standard_end = datetime.strptime(STANDARD_END_TIME, "%H:%M")
    actual_end = datetime.strptime(current_time, "%H:%M")
    early_departure = (standard_end - actual_end).total_seconds() > EARLY_DEPARTURE_THRESHOLD_MINUTES * 60
    
    # Calculate overtime
    overtime_hours = max(0, total_hours - STANDARD_WORK_HOURS)
    
    # Determine status
    status = "present"
    if total_hours < 4:
        status = "half_day"
    elif total_hours < STANDARD_WORK_HOURS - 1:
        status = "short_day"
    
    update_data = {
        "clock_out": now.isoformat(),
        "break_minutes": break_minutes,
        "total_hours": total_hours,
        "overtime_hours": round(overtime_hours, 2),
        "status": status,
        "early_departure": early_departure,
        "remarks": data.remarks or existing.get("remarks"),
        "updated_at": now.isoformat()
    }
    
    await db.attendance.update_one(
        {"user_id": user.user_id, "date": today},
        {"$set": update_data}
    )
    
    # Prepare response with warnings
    warnings = []
    if early_departure:
        early_by = int((standard_end - actual_end).total_seconds() / 60)
        warnings.append(f"Early departure by {early_by} minutes. Standard end time is {STANDARD_END_TIME}.")
    if total_hours < STANDARD_WORK_HOURS:
        shortage = round(STANDARD_WORK_HOURS - total_hours, 2)
        warnings.append(f"Work hours shortage: {shortage} hours below the standard {STANDARD_WORK_HOURS} hours.")
    
    return {
        "message": "Clocked out successfully",
        "clock_out": now.isoformat(),
        "total_hours": total_hours,
        "overtime_hours": overtime_hours,
        "early_departure": early_departure,
        "status": status,
        "warnings": warnings if warnings else None
    }

@router.get("/attendance/today")
async def get_today_attendance(request: Request):
    """Get current user's attendance for today"""
    user = await require_auth(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    attendance = await db.attendance.find_one(
        {"user_id": user.user_id, "date": today}, {"_id": 0}
    )
    
    return {
        "date": today,
        "attendance": attendance,
        "standard_hours": STANDARD_WORK_HOURS,
        "standard_start": STANDARD_START_TIME,
        "standard_end": STANDARD_END_TIME
    }

@router.get("/attendance/my-records")
async def get_my_attendance(
    request: Request,
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Get current user's attendance records"""
    user = await require_auth(request)
    
    now = datetime.now(timezone.utc)
    month = month or now.month
    year = year or now.year
    
    # Build date range
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    records = await db.attendance.find(
        {
            "user_id": user.user_id,
            "date": {"$gte": start_date, "$lt": end_date}
        },
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    
    # Calculate summary
    total_days = len(records)
    present_days = len([r for r in records if r["status"] == "present"])
    half_days = len([r for r in records if r["status"] == "half_day"])
    absent_days = len([r for r in records if r["status"] == "absent"])
    leave_days = len([r for r in records if r["status"] == "on_leave"])
    total_hours = sum(r.get("total_hours", 0) for r in records)
    overtime_hours = sum(r.get("overtime_hours", 0) for r in records)
    late_arrivals = len([r for r in records if r.get("late_arrival")])
    early_departures = len([r for r in records if r.get("early_departure")])
    
    # Calculate attendance percentage
    working_days = total_days - leave_days
    if working_days > 0:
        attendance_pct = round((present_days + half_days * 0.5) / working_days * 100, 1)
    else:
        attendance_pct = 0
    
    # Calculate productivity (hours worked vs expected) - cap at 0 minimum
    expected_hours = working_days * STANDARD_WORK_HOURS
    productivity_pct = max(0, round(total_hours / expected_hours * 100, 1)) if expected_hours > 0 else 0
    
    return {
        "month": month,
        "year": year,
        "records": records,
        "summary": {
            "total_days": total_days,
            "present_days": present_days,
            "half_days": half_days,
            "absent_days": absent_days,
            "leave_days": leave_days,
            "late_arrivals": late_arrivals,
            "early_departures": early_departures,
            "total_hours": max(0, round(total_hours, 2)),
            "overtime_hours": max(0, round(overtime_hours, 2)),
            "expected_hours": expected_hours,
            "attendance_percentage": max(0, attendance_pct),
            "productivity_percentage": productivity_pct
        }
    }

@router.get("/attendance/all")
async def get_all_attendance(
    request: Request,
    date: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Get all attendance records (admin/manager only)"""
    user = await require_technician_or_admin(request)
    
    query = {}
    if date:
        query["date"] = date
    else:
        query["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if user_id:
        query["user_id"] = user_id
    
    records = await db.attendance.find(query, {"_id": 0}).sort("user_name", 1).to_list(500)
    
    # Get all employees for comparison
    employees = await db.users.find(
        {"role": {"$in": ["admin", "technician"]}},
        {"_id": 0, "user_id": 1, "name": 1, "role": 1, "designation": 1}
    ).to_list(100)
    
    # Mark who hasn't clocked in
    clocked_in_ids = {r["user_id"] for r in records}
    not_clocked_in = [e for e in employees if e["user_id"] not in clocked_in_ids]
    
    return {
        "date": query.get("date"),
        "records": records,
        "not_clocked_in": not_clocked_in,
        "summary": {
            "total_employees": len(employees),
            "present": len([r for r in records if r["status"] == "present"]),
            "half_day": len([r for r in records if r["status"] == "half_day"]),
            "on_leave": len([r for r in records if r["status"] == "on_leave"]),
            "absent": len(not_clocked_in)
        }
    }

@router.get("/attendance/team-summary")
async def get_team_attendance_summary(
    request: Request,
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Get team attendance summary with productivity metrics (admin only)"""
    user = await require_admin(request)
    
    now = datetime.now(timezone.utc)
    month = month or now.month
    year = year or now.year
    
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    # Get all employees
    employees = await db.users.find(
        {"role": {"$in": ["admin", "technician"]}},
        {"_id": 0}
    ).to_list(100)
    
    team_stats = []
    for emp in employees:
        records = await db.attendance.find(
            {
                "user_id": emp["user_id"],
                "date": {"$gte": start_date, "$lt": end_date}
            },
            {"_id": 0}
        ).to_list(100)
        
        present = len([r for r in records if r["status"] == "present"])
        half = len([r for r in records if r["status"] == "half_day"])
        total_hours = sum(r.get("total_hours", 0) for r in records)
        overtime = sum(r.get("overtime_hours", 0) for r in records)
        late = len([r for r in records if r.get("late_arrival")])
        early = len([r for r in records if r.get("early_departure")])
        
        working_days = len(records)
        expected_hours = working_days * STANDARD_WORK_HOURS
        attendance_pct = round((present + half * 0.5) / working_days * 100, 1) if working_days > 0 else 0
        productivity_pct = round(total_hours / expected_hours * 100, 1) if expected_hours > 0 else 0
        
        team_stats.append({
            "user_id": emp["user_id"],
            "name": emp["name"],
            "role": emp["role"],
            "designation": emp.get("designation"),
            "days_present": present,
            "days_half": half,
            "total_hours": round(total_hours, 2),
            "overtime_hours": round(overtime, 2),
            "late_arrivals": late,
            "early_departures": early,
            "attendance_percentage": attendance_pct,
            "productivity_percentage": productivity_pct
        })
    
    # Sort by productivity
    team_stats.sort(key=lambda x: x["productivity_percentage"], reverse=True)
    
    return {
        "month": month,
        "year": year,
        "team_stats": team_stats,
        "averages": {
            "avg_attendance": round(sum(s["attendance_percentage"] for s in team_stats) / len(team_stats), 1) if team_stats else 0,
            "avg_productivity": round(sum(s["productivity_percentage"] for s in team_stats) / len(team_stats), 1) if team_stats else 0,
            "total_overtime": round(sum(s["overtime_hours"] for s in team_stats), 2)
        }
    }

# ==================== LEAVE MANAGEMENT ROUTES ====================

@router.get("/leave/types")
async def get_leave_types(request: Request):
    """Get all leave types"""
    await require_auth(request)
    
    types = await db.leave_types.find({}, {"_id": 0}).to_list(20)
    if not types:
        # Seed default leave types
        for lt in DEFAULT_LEAVE_TYPES:
            lt_doc = {
                "leave_type_id": f"lt_{uuid.uuid4().hex[:8]}",
                **lt
            }
            await db.leave_types.insert_one(lt_doc)
        types = await db.leave_types.find({}, {"_id": 0}).to_list(20)
    
    return types

@router.get("/leave/balance")
async def get_leave_balance(request: Request):
    """Get current user's leave balance"""
    user = await require_auth(request)
    year = datetime.now(timezone.utc).year
    
    balance = await db.leave_balances.find_one(
        {"user_id": user.user_id, "year": year}, {"_id": 0}
    )
    
    if not balance:
        # Initialize balance for new user
        leave_types = await get_leave_types(request)
        balances = {}
        for lt in leave_types:
            balances[lt["code"]] = {
                "total": lt["days_allowed"],
                "used": 0,
                "pending": 0,
                "available": lt["days_allowed"]
            }
        
        balance_doc = {
            "user_id": user.user_id,
            "year": year,
            "balances": balances
        }
        await db.leave_balances.insert_one(balance_doc)
        balance = balance_doc
    
    return balance

@router.post("/leave/request")
async def create_leave_request(data: LeaveRequestCreate, request: Request):
    """Create a new leave request"""
    user = await require_auth(request)
    
    # Calculate days
    start = datetime.strptime(data.start_date, "%Y-%m-%d")
    end = datetime.strptime(data.end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    
    if days <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    # Check leave balance
    year = datetime.now(timezone.utc).year
    balance = await db.leave_balances.find_one(
        {"user_id": user.user_id, "year": year}, {"_id": 0}
    )
    
    if balance:
        leave_balance = balance.get("balances", {}).get(data.leave_type, {})
        available = leave_balance.get("available", 0)
        if data.leave_type != "LWP" and days > available:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient leave balance. Available: {available} days"
            )
    
    # Get manager info (for now, use first admin)
    manager = await db.users.find_one({"role": "admin"}, {"_id": 0})
    
    leave_doc = {
        "leave_id": f"lv_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "user_name": user.name,
        "leave_type": data.leave_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days": days,
        "reason": data.reason,
        "status": "pending",
        "manager_id": manager["user_id"] if manager else None,
        "manager_name": manager["name"] if manager else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.leave_requests.insert_one(leave_doc)
    
    # Update pending in balance
    if balance:
        await db.leave_balances.update_one(
            {"user_id": user.user_id, "year": year},
            {"$inc": {f"balances.{data.leave_type}.pending": days}}
        )
    
    return {"message": "Leave request submitted", "leave": leave_doc}

@router.get("/leave/my-requests")
async def get_my_leave_requests(request: Request):
    """Get current user's leave requests"""
    user = await require_auth(request)
    
    requests = await db.leave_requests.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return requests

@router.get("/leave/pending-approvals")
async def get_pending_approvals(request: Request):
    """Get pending leave requests for approval (manager/admin)"""
    user = await require_technician_or_admin(request)
    
    query = {"status": "pending"}
    if user.role != "admin":
        query["manager_id"] = user.user_id
    
    requests = await db.leave_requests.find(query, {"_id": 0}).sort("created_at", 1).to_list(100)
    
    return requests

@router.put("/leave/{leave_id}/approve")
async def approve_leave(leave_id: str, data: LeaveApproval, request: Request):
    """Approve or reject a leave request"""
    user = await require_technician_or_admin(request)
    
    leave_req = await db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Leave request already processed")
    
    now = datetime.now(timezone.utc)
    year = now.year
    
    update_data = {
        "status": data.status,
        "approved_by": user.user_id,
        "approved_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    if data.status == "rejected":
        update_data["rejection_reason"] = data.rejection_reason
    
    await db.leave_requests.update_one(
        {"leave_id": leave_id},
        {"$set": update_data}
    )
    
    # Update leave balance
    leave_type = leave_req["leave_type"]
    days = leave_req["days"]
    
    if data.status == "approved":
        # Move from pending to used
        await db.leave_balances.update_one(
            {"user_id": leave_req["user_id"], "year": year},
            {
                "$inc": {
                    f"balances.{leave_type}.pending": -days,
                    f"balances.{leave_type}.used": days,
                    f"balances.{leave_type}.available": -days
                }
            }
        )
        
        # Mark attendance as on_leave for those dates
        start = datetime.strptime(leave_req["start_date"], "%Y-%m-%d")
        for i in range(int(days)):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            await db.attendance.update_one(
                {"user_id": leave_req["user_id"], "date": date},
                {
                    "$set": {
                        "user_id": leave_req["user_id"],
                        "user_name": leave_req["user_name"],
                        "date": date,
                        "status": "on_leave",
                        "remarks": f"On {leave_type} leave"
                    }
                },
                upsert=True
            )
    else:
        # Remove from pending
        await db.leave_balances.update_one(
            {"user_id": leave_req["user_id"], "year": year},
            {"$inc": {f"balances.{leave_type}.pending": -days}}
        )
    
    return {"message": f"Leave request {data.status}", "leave_id": leave_id}

@router.delete("/leave/{leave_id}")
async def cancel_leave_request(leave_id: str, request: Request):
    """Cancel a pending leave request"""
    user = await require_auth(request)
    
    leave_req = await db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_req["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if leave_req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending requests")
    
    # Update status
    await db.leave_requests.update_one(
        {"leave_id": leave_id},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Restore balance
    year = datetime.now(timezone.utc).year
    await db.leave_balances.update_one(
        {"user_id": user.user_id, "year": year},
        {"$inc": {f"balances.{leave_req['leave_type']}.pending": -leave_req['days']}}
    )
    
    return {"message": "Leave request cancelled"}

# ==================== PAYROLL ROUTES ====================

@router.get("/payroll/calculate/{user_id}")
async def calculate_payroll(
    user_id: str,
    month: int,
    year: int,
    request: Request
):
    """Calculate payroll for an employee"""
    await require_admin(request)
    
    # Get employee details
    employee = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get attendance records
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    records = await db.attendance.find(
        {
            "user_id": user_id,
            "date": {"$gte": start_date, "$lt": end_date}
        },
        {"_id": 0}
    ).to_list(50)
    
    # Calculate metrics
    days_present = len([r for r in records if r["status"] == "present"])
    days_half = len([r for r in records if r["status"] == "half_day"])
    days_leave = len([r for r in records if r["status"] == "on_leave"])
    total_hours = sum(r.get("total_hours", 0) for r in records)
    overtime_hours = sum(r.get("overtime_hours", 0) for r in records)
    
    # Calculate working days in month
    import calendar
    working_days = sum(1 for day in range(1, calendar.monthrange(year, month)[1] + 1)
                       if datetime(year, month, day).weekday() < 5)  # Mon-Fri
    
    days_absent = working_days - days_present - days_half - days_leave
    days_absent = max(0, days_absent)
    
    # Calculate salary (simplified)
    hourly_rate = employee.get("hourly_rate", 250)  # Default ₹250/hr
    base_salary = hourly_rate * STANDARD_WORK_HOURS * working_days
    overtime_pay = overtime_hours * hourly_rate * OVERTIME_MULTIPLIER
    
    # Deductions for absence
    daily_rate = base_salary / working_days if working_days > 0 else 0
    absence_deduction = days_absent * daily_rate + (days_half * daily_rate * 0.5)
    
    # Late penalty (example: ₹100 per late arrival)
    late_arrivals = len([r for r in records if r.get("late_arrival")])
    late_penalty = late_arrivals * 100
    
    total_deductions = absence_deduction + late_penalty
    net_salary = base_salary + overtime_pay - total_deductions
    
    # Productivity metrics
    expected_hours = working_days * STANDARD_WORK_HOURS
    attendance_pct = round((days_present + days_half * 0.5) / working_days * 100, 1) if working_days > 0 else 0
    productivity_pct = round(total_hours / expected_hours * 100, 1) if expected_hours > 0 else 0
    
    payroll_data = {
        "payroll_id": f"pay_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "user_name": employee["name"],
        "month": month,
        "year": year,
        "working_days": working_days,
        "days_present": days_present,
        "days_absent": days_absent,
        "days_leave": days_leave,
        "days_half": days_half,
        "total_hours": round(total_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "late_arrivals": late_arrivals,
        "attendance_percentage": attendance_pct,
        "productivity_score": productivity_pct,
        "hourly_rate": hourly_rate,
        "base_salary": round(base_salary, 2),
        "overtime_pay": round(overtime_pay, 2),
        "deductions": round(total_deductions, 2),
        "deduction_breakdown": {
            "absence": round(absence_deduction, 2),
            "late_penalty": late_penalty
        },
        "net_salary": round(net_salary, 2),
        "status": "draft"
    }
    
    return payroll_data

@router.post("/payroll/generate")
async def generate_payroll(
    month: int,
    year: int,
    request: Request
):
    """Generate payroll for all employees"""
    await require_admin(request)
    
    employees = await db.users.find(
        {"role": {"$in": ["admin", "technician"]}},
        {"_id": 0}
    ).to_list(100)
    
    payroll_records = []
    for emp in employees:
        payroll_data = await calculate_payroll(emp["user_id"], month, year, request)
        payroll_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        # Check if already exists
        existing = await db.payroll.find_one(
            {"user_id": emp["user_id"], "month": month, "year": year},
            {"_id": 0}
        )
        
        if existing:
            await db.payroll.update_one(
                {"user_id": emp["user_id"], "month": month, "year": year},
                {"$set": payroll_data}
            )
        else:
            await db.payroll.insert_one(payroll_data.copy())
        
        # Remove _id if present for response
        if "_id" in payroll_data:
            del payroll_data["_id"]
        payroll_records.append(payroll_data)
    
    return {
        "message": f"Payroll generated for {len(payroll_records)} employees",
        "month": month,
        "year": year,
        "records": payroll_records
    }

@router.get("/payroll/records")
async def get_payroll_records(
    month: Optional[int] = None,
    year: Optional[int] = None,
    request: Request = None
):
    """Get payroll records"""
    await require_admin(request)
    
    query = {}
    if month:
        query["month"] = month
    if year:
        query["year"] = year
    
    records = await db.payroll.find(query, {"_id": 0}).to_list(500)
    
    return records

@router.get("/payroll/my-records")
async def get_my_payroll(request: Request):
    """Get current user's payroll records"""
    user = await require_auth(request)
    
    records = await db.payroll.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort([("year", -1), ("month", -1)]).to_list(24)
    
    return records

# ==================== CUSTOMER ROUTES ====================