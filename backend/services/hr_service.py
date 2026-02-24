"""
Battwheels OS - HR Service
Business logic for HR management with event emission

Handles:
- Employee CRUD
- Attendance (clock-in/out)
- Leave management
- Payroll calculation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid
import logging
import bcrypt

from events import get_dispatcher, EventType, EventPriority
from services.posting_hooks import post_payroll_run_journal_entry

logger = logging.getLogger(__name__)

# Constants
STANDARD_WORK_HOURS = 8
LATE_THRESHOLD_MINUTES = 15
EARLY_DEPARTURE_THRESHOLD_MINUTES = 15
OVERTIME_MULTIPLIER = 1.5


class HRService:
    """HR management service with event emission"""
    
    def __init__(self, db):
        self.db = db
        self.dispatcher = get_dispatcher()
        logger.info("HRService initialized")
    
    # ==================== EMPLOYEE MANAGEMENT ====================
    
    async def create_employee(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create new employee with Indian compliance fields and optional user account"""
        employee_id = f"emp_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        # Generate employee code if not provided
        employee_code = data.get("employee_code")
        if not employee_code:
            count = await self.db.employees.count_documents({})
            employee_code = f"EMP{str(count + 1).zfill(4)}"
        
        # Create user account if password is provided
        created_user_id = data.get("user_id")
        email = data.get("email")
        password = data.get("password")
        system_role = data.get("system_role", "technician")
        
        if password and email:
            # Check if user already exists with this email
            existing_user = await self.db.users.find_one({"email": email})
            if existing_user:
                raise ValueError(f"User with email {email} already exists")
            
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user account
            new_user_id = f"user_{uuid.uuid4().hex[:12]}"
            user_doc = {
                "user_id": new_user_id,
                "email": email,
                "password": hashed_password,
                "name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                "role": system_role,
                "status": "active",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            await self.db.users.insert_one(user_doc)
            created_user_id = new_user_id
            logger.info(f"Created user account for employee: {email}")
        
        # Build emergency contact
        emergency_contact = {}
        if data.get("emergency_contact_name"):
            emergency_contact = {
                "name": data.get("emergency_contact_name"),
                "phone": data.get("emergency_contact_phone"),
                "relation": data.get("emergency_contact_relation")
            }
        
        # Build address
        address = {}
        if data.get("current_address") or data.get("city"):
            address = {
                "current": data.get("current_address"),
                "permanent": data.get("permanent_address"),
                "city": data.get("city"),
                "state": data.get("state"),
                "pincode": data.get("pincode")
            }
        
        # Build compliance info
        compliance = {
            "pan_number": data.get("pan_number"),
            "aadhaar_number": data.get("aadhaar_number"),
            "pf_number": data.get("pf_number"),
            "uan": data.get("uan"),
            "esi_number": data.get("esi_number"),
            "pf_enrolled": data.get("pf_enrolled", False),
            "esi_enrolled": data.get("esi_enrolled", False)
        }
        
        employee = {
            "employee_id": employee_id,
            "employee_code": employee_code,
            "user_id": created_user_id,
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "full_name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
            "work_email": email,
            "email": email,
            "personal_email": data.get("personal_email"),
            "phone": data.get("phone"),
            "department": data.get("department"),
            "designation": data.get("designation"),
            "employment_type": data.get("employment_type", "full_time"),
            "joining_date": data.get("date_of_joining"),
            "date_of_joining": data.get("date_of_joining"),
            "date_of_birth": data.get("date_of_birth"),
            "gender": data.get("gender"),
            "marital_status": data.get("marital_status"),
            "blood_group": data.get("blood_group"),
            "emergency_contact": emergency_contact,
            "address": address,
            "work_location": data.get("work_location", "office"),
            "shift": data.get("shift", "general"),
            "probation_period_months": data.get("probation_period_months", 0),
            
            # System role
            "system_role": system_role,
            
            # Compensation
            "salary": data.get("salary_structure", {}),
            "salary_structure": data.get("salary_structure", {}),
            "bank_details": data.get("bank_details", {}),
            
            # Indian compliance
            "compliance": compliance,
            "pan_number": data.get("pan_number"),
            "aadhaar_number": data.get("aadhaar_number"),
            "pf_account_number": data.get("pf_number"),
            "uan_number": data.get("uan"),
            "esi_number": data.get("esi_number"),
            
            # Leave balances
            "leave_balances": {
                "casual": 12,
                "sick": 12,
                "earned": 15,
                "maternity": 26,
                "paternity": 5,
                "unpaid": 0
            },
            
            # Status
            "status": "active",
            "reporting_manager": data.get("reporting_manager"),
            "reporting_manager_id": data.get("reporting_manager"),
            "shift_timing": data.get("shift_timing", {"start": "09:00", "end": "18:00"}),
            
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await self.db.employees.insert_one(employee)
        
        # Emit event
        await self.dispatcher.emit(
            EventType.EMPLOYEE_CREATED,
            {"employee_id": employee_id, "name": f"{data.get('first_name')} {data.get('last_name')}"},
            source="hr_service",
            user_id=user_id
        )
        
        return await self.db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    
    async def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        return await self.db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    
    async def get_employee_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by user_id"""
        return await self.db.employees.find_one({"user_id": user_id}, {"_id": 0})
    
    async def list_employees(
        self,
        department: Optional[str] = None,
        status: str = "active",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List employees with filtering"""
        query = {"status": status}
        if department:
            query["department"] = department
        
        return await self.db.employees.find(query, {"_id": 0}).to_list(limit)
    
    async def update_employee(
        self,
        employee_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Update employee"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.db.employees.update_one(
            {"employee_id": employee_id},
            {"$set": updates}
        )
        
        return await self.db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    
    # ==================== ATTENDANCE MANAGEMENT ====================
    
    async def clock_in(self, user_id: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Record clock-in"""
        employee = await self.get_employee_by_user(user_id)
        if not employee:
            raise ValueError("Employee record not found")
        
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        
        # Check existing attendance
        existing = await self.db.attendance.find_one({
            "employee_id": employee["employee_id"],
            "date": today
        }, {"_id": 0})
        
        if existing and existing.get("clock_in"):
            raise ValueError("Already clocked in today")
        
        # Calculate late status
        shift_start = employee.get("shift_timing", {}).get("start", "09:00")
        shift_start_time = datetime.strptime(f"{today} {shift_start}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        
        is_late = now > (shift_start_time + timedelta(minutes=LATE_THRESHOLD_MINUTES))
        late_minutes = max(0, int((now - shift_start_time).total_seconds() / 60)) if is_late else 0
        
        attendance_id = f"att_{uuid.uuid4().hex[:12]}"
        
        attendance = {
            "attendance_id": attendance_id,
            "employee_id": employee["employee_id"],
            "user_id": user_id,
            "date": today,
            "clock_in": now.isoformat(),
            "clock_in_location": location,
            "is_late": is_late,
            "late_minutes": late_minutes,
            "status": "present",
            "created_at": now.isoformat()
        }
        
        await self.db.attendance.insert_one(attendance)
        
        # Emit event
        await self.dispatcher.emit(
            EventType.ATTENDANCE_MARKED,
            {"employee_id": employee["employee_id"], "action": "clock_in", "is_late": is_late},
            source="hr_service",
            user_id=user_id
        )
        
        return await self.db.attendance.find_one({"attendance_id": attendance_id}, {"_id": 0})
    
    async def clock_out(self, user_id: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Record clock-out"""
        employee = await self.get_employee_by_user(user_id)
        if not employee:
            raise ValueError("Employee record not found")
        
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        
        attendance = await self.db.attendance.find_one({
            "employee_id": employee["employee_id"],
            "date": today,
            "clock_in": {"$exists": True}
        }, {"_id": 0})
        
        if not attendance:
            raise ValueError("No clock-in record found for today")
        
        if attendance.get("clock_out"):
            raise ValueError("Already clocked out today")
        
        clock_in_time = datetime.fromisoformat(attendance["clock_in"])
        hours_worked = (now - clock_in_time).total_seconds() / 3600
        
        # Calculate early departure
        shift_end = employee.get("shift_timing", {}).get("end", "18:00")
        shift_end_time = datetime.strptime(f"{today} {shift_end}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        
        is_early = now < (shift_end_time - timedelta(minutes=EARLY_DEPARTURE_THRESHOLD_MINUTES))
        early_minutes = max(0, int((shift_end_time - now).total_seconds() / 60)) if is_early else 0
        
        # Calculate overtime
        overtime_hours = max(0, hours_worked - STANDARD_WORK_HOURS)
        
        await self.db.attendance.update_one(
            {"attendance_id": attendance["attendance_id"]},
            {"$set": {
                "clock_out": now.isoformat(),
                "clock_out_location": location,
                "hours_worked": round(hours_worked, 2),
                "overtime_hours": round(overtime_hours, 2),
                "is_early_departure": is_early,
                "early_departure_minutes": early_minutes,
                "updated_at": now.isoformat()
            }}
        )
        
        return await self.db.attendance.find_one({"attendance_id": attendance["attendance_id"]}, {"_id": 0})
    
    async def get_attendance_today(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get today's attendance for user"""
        employee = await self.get_employee_by_user(user_id)
        if not employee:
            return None
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return await self.db.attendance.find_one({
            "employee_id": employee["employee_id"],
            "date": today
        }, {"_id": 0})
    
    # ==================== LEAVE MANAGEMENT ====================
    
    async def request_leave(
        self,
        user_id: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str
    ) -> Dict[str, Any]:
        """Submit leave request"""
        employee = await self.get_employee_by_user(user_id)
        if not employee:
            raise ValueError("Employee record not found")
        
        # Calculate days
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        # Check balance
        balance = employee.get("leave_balances", {}).get(leave_type, 0)
        if leave_type != "unpaid" and days > balance:
            raise ValueError(f"Insufficient {leave_type} leave balance. Available: {balance}")
        
        leave_id = f"leave_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        leave = {
            "leave_id": leave_id,
            "employee_id": employee["employee_id"],
            "user_id": user_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "days_requested": days,
            "reason": reason,
            "status": "pending",
            "applied_at": now.isoformat(),
            "created_at": now.isoformat()
        }
        
        await self.db.leave_requests.insert_one(leave)
        
        # Emit event
        await self.dispatcher.emit(
            EventType.LEAVE_REQUESTED,
            {"leave_id": leave_id, "employee_id": employee["employee_id"], "days": days, "type": leave_type},
            source="hr_service",
            user_id=user_id
        )
        
        return await self.db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
    
    async def approve_leave(
        self,
        leave_id: str,
        approved_by: str,
        approved: bool,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve or reject leave request"""
        leave = await self.db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
        if not leave:
            raise ValueError(f"Leave request {leave_id} not found")
        
        if leave.get("status") != "pending":
            raise ValueError("Leave request already processed")
        
        now = datetime.now(timezone.utc)
        new_status = "approved" if approved else "rejected"
        
        await self.db.leave_requests.update_one(
            {"leave_id": leave_id},
            {"$set": {
                "status": new_status,
                "approved_by": approved_by,
                "approved_at": now.isoformat(),
                "approval_comments": comments
            }}
        )
        
        # Update leave balance if approved
        if approved:
            leave_type = leave.get("leave_type")
            days = leave.get("days_requested", 0)
            
            if leave_type != "unpaid":
                await self.db.employees.update_one(
                    {"employee_id": leave["employee_id"]},
                    {"$inc": {f"leave_balances.{leave_type}": -days}}
                )
            
            # Emit approval event
            await self.dispatcher.emit(
                EventType.LEAVE_APPROVED,
                {"leave_id": leave_id, "employee_id": leave["employee_id"], "days": days},
                source="hr_service",
                user_id=approved_by
            )
        
        return await self.db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
    
    # ==================== PAYROLL ====================
    
    async def calculate_payroll(self, employee_id: str, month: str, year: int) -> Dict[str, Any]:
        """Calculate payroll for employee"""
        employee = await self.get_employee(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        salary = employee.get("salary_structure", {})
        basic = salary.get("basic", 0)
        hra = salary.get("hra", 0)
        da = salary.get("da", 0)
        special = salary.get("special_allowance", 0)
        
        gross = basic + hra + da + special
        
        # Deductions
        pf_deduction = basic * 0.12  # 12% of basic
        esi_deduction = gross * 0.0075 if gross <= 21000 else 0  # ESI if gross <= 21000
        professional_tax = 200  # Standard PT
        tds = salary.get("tds", 0)
        
        total_deductions = pf_deduction + esi_deduction + professional_tax + tds
        net_salary = gross - total_deductions
        
        # Employer contributions
        employer_pf = basic * 0.13  # 13% of basic (12% PF + 1% admin)
        employer_esi = gross * 0.0325 if gross <= 21000 else 0
        
        return {
            "employee_id": employee_id,
            "employee_name": f"{employee.get('first_name')} {employee.get('last_name')}",
            "month": month,
            "year": year,
            "earnings": {
                "basic": basic,
                "hra": hra,
                "da": da,
                "special_allowance": special,
                "gross": gross
            },
            "deductions": {
                "pf_employee": round(pf_deduction, 2),
                "esi_employee": round(esi_deduction, 2),
                "professional_tax": professional_tax,
                "tds": tds,
                "total": round(total_deductions, 2)
            },
            "employer_contributions": {
                "pf_employer": round(employer_pf, 2),
                "esi_employer": round(employer_esi, 2)
            },
            "net_salary": round(net_salary, 2),
            "ctc": round(gross + employer_pf + employer_esi, 2)
        }
    
    async def generate_payroll(self, month: str, year: int, user_id: str) -> Dict[str, Any]:
        """Generate payroll for all active employees and post journal entry"""
        employees = await self.list_employees(status="active")
        
        # Get org_id from user
        user = await self.db.users.find_one({"user_id": user_id}, {"_id": 0, "organization_id": 1})
        org_id = user.get("organization_id") if user else None

        # Prevent duplicate payroll run for the same org/period
        period = f"{month} {year}"
        if org_id:
            try:
                await self.db.payroll_runs.insert_one({
                    "organization_id": org_id,
                    "period": period,
                    "status": "generated",
                    "generated_by": user_id,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                if "E11000" in str(e) or "duplicate key" in str(e).lower():
                    raise ValueError(f"Payroll for {period} has already been processed.")
                raise

        records = []
        total_gross = 0
        total_net = 0
        
        for emp in employees:
            payroll = await self.calculate_payroll(emp["employee_id"], month, year)
            
            # Store payroll record
            payroll_id = f"pay_{uuid.uuid4().hex[:12]}"
            record = {
                "payroll_id": payroll_id,
                "organization_id": org_id,
                **payroll,
                "status": "generated",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generated_by": user_id
            }
            
            await self.db.payroll.insert_one(record)
            records.append(record)
            
            total_gross += payroll["earnings"]["gross"]
            total_net += payroll["net_salary"]
        
        # Get organization_id from context
        org_id = None
        if records:
            # Fetch the org_id from the first employee
            first_emp = await self.db.employees.find_one(
                {"employee_id": records[0]["employee_id"]},
                {"_id": 0, "organization_id": 1}
            )
            if first_emp:
                org_id = first_emp.get("organization_id")
        
        # If no org_id from employee, try to get from user
        if not org_id:
            user = await self.db.users.find_one({"user_id": user_id}, {"_id": 0, "organization_id": 1})
            if user:
                org_id = user.get("organization_id")
        
        # Post journal entry for payroll run
        journal_entry_id = None
        if org_id and records:
            try:
                success, msg, entry = await post_payroll_run_journal_entry(
                    organization_id=org_id,
                    payroll_records=records,
                    created_by=user_id
                )
                if success and entry:
                    journal_entry_id = entry.get("entry_id")
                    logger.info(f"Posted payroll journal entry {journal_entry_id} for {month} {year}")
                else:
                    logger.warning(f"Failed to post payroll journal entry: {msg}")
            except Exception as e:
                logger.error(f"Exception posting payroll journal entry: {e}")
        
        # Audit log
        try:
            from utils.audit import log_audit, AuditAction
            await log_audit(self.db, AuditAction.PAYROLL_RUN, org_id or "", user_id,
                "payroll", period, {"total_net": round(total_net, 2), "employees": len(records)})
        except Exception:
            pass

        # Emit event
        await self.dispatcher.emit(
            EventType.PAYROLL_PROCESSED,
            {"month": month, "year": year, "employees": len(records), "total_net": total_net, "journal_entry_id": journal_entry_id},
            source="hr_service",
            user_id=user_id,
            priority=EventPriority.HIGH
        )
        
        return {
            "month": month,
            "year": year,
            "employees_processed": len(records),
            "total_gross": round(total_gross, 2),
            "total_net": round(total_net, 2),
            "status": "generated",
            "journal_entry_id": journal_entry_id
        }


# Service factory
_hr_service: Optional[HRService] = None

def get_hr_service() -> HRService:
    if _hr_service is None:
        raise ValueError("HRService not initialized")
    return _hr_service

def init_hr_service(db) -> HRService:
    global _hr_service
    _hr_service = HRService(db)
    return _hr_service
