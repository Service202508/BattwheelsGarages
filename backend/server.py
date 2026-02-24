from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, Query
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
import logging
import calendar
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import bcrypt
import jwt
import httpx

# Import tenant context for multi-tenant routes
from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging (must be before validation)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== SENTRY MONITORING ====================
def _scrub_sensitive_data(event, hint):
    """Remove PII and credentials before sending to Sentry"""
    SENSITIVE_KEYS = {
        "password", "token", "secret", "api_key", "gstin", "pan_number",
        "bank_account", "ifsc_code", "jwt", "authorization", "key_secret",
        "webhook_secret", "razorpay_key", "otp", "pin"
    }
    def scrub_dict(d):
        if not isinstance(d, dict):
            return d
        return {
            k: "[FILTERED]" if k.lower() in SENSITIVE_KEYS else scrub_dict(v)
            for k, v in d.items()
        }
    if "request" in event:
        if "data" in event["request"]:
            event["request"]["data"] = scrub_dict(event["request"]["data"])
        if "headers" in event["request"]:
            event["request"]["headers"] = scrub_dict(event["request"]["headers"])
    return event

SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.environ.get("ENVIRONMENT", "development"),
            release=os.environ.get("APP_VERSION", "1.0.0"),
            before_send=_scrub_sensitive_data,
        )
        logger.info("Sentry monitoring initialized")
    except Exception as _sentry_err:
        logger.warning(f"Sentry initialization failed: {_sentry_err}")
else:
    logger.info("SENTRY_DSN not set — Sentry monitoring disabled")


# Validate environment variables on startup
from config.env_validator import check_and_report
if not check_and_report():
    logger.critical("Critical environment variables missing. Check .env file.")
    # Don't exit in development/preview - just warn
    logger.warning("Continuing with defaults - this may cause issues in production")

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'battwheels_db')]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

# Warn if JWT secret is weak
if len(JWT_SECRET) < 32:
    logger.warning("JWT_SECRET is shorter than 32 characters - consider using a stronger secret")

# ── Lifespan ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    try:
        from routes.sla import start_sla_background_job
        start_sla_background_job()
        logger.info("SLA background breach detection job started")
    except Exception as e:
        logger.warning(f"SLA background job failed to start: {e}")

    try:
        from migrations.add_org_id_indexes import run as run_index_migration
        await run_index_migration()
        logger.info("Index migration completed on startup")
    except Exception as e:
        logger.warning(f"Index migration failed on startup (non-fatal): {e}")

    try:
        from utils.indexes import ensure_compound_indexes
        await ensure_compound_indexes(db)
        logger.info("Compound indexes ensured on startup")
    except Exception as e:
        logger.warning(f"Compound index migration failed on startup (non-fatal): {e}")

    logger.info("Battwheels OS started successfully")
    yield
    # ── Shutdown ──
    client.close()
    logger.info("Battwheels OS shut down cleanly")

# Create the main app
app = FastAPI(title="Battwheels OS API", lifespan=lifespan)

# Create routers with API prefix structure
# /api       — auth, public, health (no version)
# /api/v1    — all business routes (versioned)
api_router = APIRouter(prefix="/api")
v1_router = APIRouter(prefix="/v1")

# Security
security = HTTPBearer(auto_error=False)

# ==================== TENANT EXCEPTION HANDLERS ====================

from core.tenant.exceptions import (
    TenantException, 
    TenantContextMissing, 
    TenantAccessDenied,
    TenantBoundaryViolation,
    TenantDataLeakAttempt,
    TenantQuotaExceeded,
    TenantSuspended
)
from fastapi.responses import JSONResponse

@app.exception_handler(TenantAccessDenied)
async def tenant_access_denied_handler(request: Request, exc: TenantAccessDenied):
    """Handle tenant access denied - user trying to access org they don't belong to"""
    logger.warning(f"Tenant access denied: {exc.message}")
    return JSONResponse(
        status_code=403,
        content={"detail": "Access denied to this organization", "code": "TENANT_ACCESS_DENIED"}
    )

@app.exception_handler(TenantContextMissing)
async def tenant_context_missing_handler(request: Request, exc: TenantContextMissing):
    """Handle missing tenant context - typically means user not properly authenticated"""
    logger.warning(f"Tenant context missing: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Organization context required", "code": "TENANT_CONTEXT_MISSING"}
    )

@app.exception_handler(TenantBoundaryViolation)
async def tenant_boundary_violation_handler(request: Request, exc: TenantBoundaryViolation):
    """Handle boundary violations - potential security issue"""
    logger.error(f"SECURITY: Tenant boundary violation: {exc.message}")
    return JSONResponse(
        status_code=403,
        content={"detail": "Operation not permitted", "code": "TENANT_BOUNDARY_VIOLATION"}
    )

@app.exception_handler(TenantDataLeakAttempt)
async def tenant_data_leak_handler(request: Request, exc: TenantDataLeakAttempt):
    """Handle potential data leak - critical security event"""
    logger.critical(f"SECURITY: Potential data leak attempt: {exc.message}")
    return JSONResponse(
        status_code=403,
        content={"detail": "Operation blocked for security", "code": "TENANT_DATA_LEAK_BLOCKED"}
    )

@app.exception_handler(TenantQuotaExceeded)
async def tenant_quota_exceeded_handler(request: Request, exc: TenantQuotaExceeded):
    """Handle quota exceeded - plan limit reached"""
    return JSONResponse(
        status_code=429,
        content={"detail": f"Quota exceeded: {exc.quota_type}", "code": "TENANT_QUOTA_EXCEEDED"}
    )

@app.exception_handler(TenantSuspended)
async def tenant_suspended_handler(request: Request, exc: TenantSuspended):
    """Handle suspended organization"""
    return JSONResponse(
        status_code=403,
        content={"detail": "Organization is suspended", "code": "TENANT_SUSPENDED"}
    )

# ==================== BASE MODELS ====================

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "customer"
    designation: Optional[str] = None
    phone: Optional[str] = None
    picture: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "customer"
    designation: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    created_at: datetime
    is_active: bool = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    manager_id: Optional[str] = None
    department: Optional[str] = None
    hourly_rate: Optional[float] = None

# ==================== EMPLOYEE MODELS ====================

EMPLOYEE_ROLES = ["admin", "manager", "technician", "accountant", "customer_support"]
EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "intern", "probation"]
DEPARTMENTS = ["operations", "hr", "finance", "service", "sales", "administration"]

class EmployeeSalaryStructure(BaseModel):
    basic_salary: float = 0.0
    hra: float = 0.0  # House Rent Allowance
    da: float = 0.0  # Dearness Allowance
    conveyance: float = 0.0
    medical_allowance: float = 0.0
    special_allowance: float = 0.0
    other_allowances: float = 0.0
    gross_salary: float = 0.0  # Calculated
    # Deductions
    pf_deduction: float = 0.0  # 12% of basic
    esi_deduction: float = 0.0  # 0.75% if gross <= 21000
    professional_tax: float = 0.0  # State-wise
    tds: float = 0.0  # Based on tax slab
    other_deductions: float = 0.0
    net_salary: float = 0.0  # Calculated

class EmployeeCompliance(BaseModel):
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pf_number: Optional[str] = None  # Provident Fund
    uan: Optional[str] = None  # Universal Account Number
    esi_number: Optional[str] = None  # Employee State Insurance
    pf_enrolled: bool = False
    esi_enrolled: bool = False

class EmployeeBankDetails(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None
    account_type: str = "savings"  # savings, current

class Employee(BaseModel):
    model_config = ConfigDict(extra="ignore")
    employee_id: str = Field(default_factory=lambda: f"emp_{uuid.uuid4().hex[:12]}")
    user_id: Optional[str] = None  # Linked user account
    
    # Personal Information
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD
    gender: Optional[str] = None  # male, female, other
    photo_url: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    # Address
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    # Employment Details
    employee_code: Optional[str] = None  # Custom employee ID like EMP001
    work_email: Optional[str] = None
    department: str = "operations"
    designation: str
    employment_type: str = "full_time"
    joining_date: str  # YYYY-MM-DD
    confirmation_date: Optional[str] = None
    probation_period_months: int = 0
    reporting_manager_id: Optional[str] = None
    reporting_manager_name: Optional[str] = None
    work_location: str = "office"
    shift: str = "general"  # general, morning, evening, night
    
    # Role & Access
    system_role: str = "technician"  # admin, manager, technician, accountant, customer_support
    
    # Salary Structure
    salary: EmployeeSalaryStructure = Field(default_factory=EmployeeSalaryStructure)
    
    # Compliance
    compliance: EmployeeCompliance = Field(default_factory=EmployeeCompliance)
    
    # Bank Details
    bank_details: EmployeeBankDetails = Field(default_factory=EmployeeBankDetails)
    
    # Status
    status: str = "active"  # active, inactive, terminated, resigned, on_notice
    termination_date: Optional[str] = None
    termination_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

class EmployeeCreate(BaseModel):
    # Personal Information
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    # Employment Details
    employee_code: Optional[str] = None
    work_email: str
    department: str = "operations"
    designation: str
    employment_type: str = "full_time"
    joining_date: str
    probation_period_months: int = 0
    reporting_manager_id: Optional[str] = None
    work_location: str = "office"
    shift: str = "general"
    
    # Role & Access
    system_role: str = "technician"
    password: str  # For creating user account
    
    # Salary Structure
    basic_salary: float = 0.0
    hra: float = 0.0
    da: float = 0.0
    conveyance: float = 0.0
    medical_allowance: float = 0.0
    special_allowance: float = 0.0
    other_allowances: float = 0.0
    
    # Compliance
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pf_number: Optional[str] = None
    uan: Optional[str] = None
    esi_number: Optional[str] = None
    pf_enrolled: bool = False
    esi_enrolled: bool = False
    
    # Bank Details
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None
    account_type: str = "savings"

class EmployeeUpdate(BaseModel):
    # Personal Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    # Employment Details
    department: Optional[str] = None
    designation: Optional[str] = None
    employment_type: Optional[str] = None
    confirmation_date: Optional[str] = None
    reporting_manager_id: Optional[str] = None
    work_location: Optional[str] = None
    shift: Optional[str] = None
    
    # Role & Access
    system_role: Optional[str] = None
    
    # Salary Structure
    basic_salary: Optional[float] = None
    hra: Optional[float] = None
    da: Optional[float] = None
    conveyance: Optional[float] = None
    medical_allowance: Optional[float] = None
    special_allowance: Optional[float] = None
    other_allowances: Optional[float] = None
    
    # Compliance
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pf_number: Optional[str] = None
    uan: Optional[str] = None
    esi_number: Optional[str] = None
    pf_enrolled: Optional[bool] = None
    esi_enrolled: Optional[bool] = None
    
    # Bank Details
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None
    account_type: Optional[str] = None
    
    # Status
    status: Optional[str] = None
    termination_date: Optional[str] = None
    termination_reason: Optional[str] = None

# ==================== ATTENDANCE MODELS ====================

class AttendanceRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    attendance_id: str = Field(default_factory=lambda: f"att_{uuid.uuid4().hex[:12]}")
    user_id: str
    user_name: Optional[str] = None
    date: str  # YYYY-MM-DD format
    clock_in: Optional[str] = None  # ISO datetime
    clock_out: Optional[str] = None  # ISO datetime
    break_minutes: int = 0
    total_hours: float = 0.0
    overtime_hours: float = 0.0
    status: str = "absent"  # present, absent, half_day, on_leave, holiday
    early_departure: bool = False
    late_arrival: bool = False
    remarks: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class ClockInRequest(BaseModel):
    location: Optional[str] = None
    remarks: Optional[str] = None

class ClockOutRequest(BaseModel):
    break_minutes: int = 0
    remarks: Optional[str] = None

# ==================== LEAVE MODELS ====================

class LeaveType(BaseModel):
    leave_type_id: str = Field(default_factory=lambda: f"lt_{uuid.uuid4().hex[:8]}")
    name: str
    code: str  # CL, SL, EL, etc.
    days_allowed: int
    carry_forward: bool = False
    is_paid: bool = True
    description: Optional[str] = None

class LeaveBalance(BaseModel):
    user_id: str
    year: int
    balances: dict = {}  # {leave_type_code: {total: x, used: y, pending: z}}

class LeaveRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    leave_id: str = Field(default_factory=lambda: f"lv_{uuid.uuid4().hex[:12]}")
    user_id: str
    user_name: Optional[str] = None
    leave_type: str  # CL, SL, EL, etc.
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    days: float = 1.0
    reason: str
    status: str = "pending"  # pending, approved, rejected, cancelled
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class LeaveRequestCreate(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    reason: str

class LeaveApproval(BaseModel):
    status: str  # approved, rejected
    rejection_reason: Optional[str] = None

# ==================== PAYROLL MODELS ====================

class PayrollRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    payroll_id: str = Field(default_factory=lambda: f"pay_{uuid.uuid4().hex[:12]}")
    user_id: str
    user_name: Optional[str] = None
    month: int  # 1-12
    year: int
    working_days: int = 0
    days_present: int = 0
    days_absent: int = 0
    days_leave: int = 0
    days_half: int = 0
    total_hours: float = 0.0
    overtime_hours: float = 0.0
    attendance_percentage: float = 0.0
    productivity_score: float = 0.0
    base_salary: float = 0.0
    overtime_pay: float = 0.0
    deductions: float = 0.0
    net_salary: float = 0.0
    status: str = "draft"  # draft, processed, paid
    processed_by: Optional[str] = None
    processed_at: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== SUPPLIER/VENDOR MODELS ====================

class Supplier(BaseModel):
    model_config = ConfigDict(extra="ignore")
    supplier_id: str = Field(default_factory=lambda: f"sup_{uuid.uuid4().hex[:12]}")
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    payment_terms: str = "net_30"  # net_15, net_30, net_45, net_60, immediate
    category: str = "parts"  # parts, equipment, services, consumables
    rating: float = 0.0
    total_orders: int = 0
    total_value: float = 0.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    payment_terms: str = "net_30"
    category: str = "parts"

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None

# ==================== ENHANCED INVENTORY MODELS ====================

class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    sku: Optional[str] = None
    name: str
    category: str
    quantity: int
    reserved_quantity: int = 0  # Reserved for tickets
    unit_price: float
    cost_price: float = 0.0
    min_stock_level: int
    max_stock_level: int = 1000
    reorder_quantity: int = 10
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    location: Optional[str] = None
    last_restock_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InventoryCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    category: str
    quantity: int
    unit_price: float
    cost_price: float = 0.0
    min_stock_level: int
    max_stock_level: int = 1000
    reorder_quantity: int = 10
    supplier_id: Optional[str] = None
    location: Optional[str] = None

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    reserved_quantity: Optional[int] = None
    unit_price: Optional[float] = None
    cost_price: Optional[float] = None
    min_stock_level: Optional[int] = None
    supplier_id: Optional[str] = None
    location: Optional[str] = None

# ==================== MATERIAL ALLOCATION MODELS ====================

class MaterialAllocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    allocation_id: str = Field(default_factory=lambda: f"mat_{uuid.uuid4().hex[:12]}")
    ticket_id: str
    item_id: str
    item_name: str
    quantity: int
    unit_price: float
    total_price: float
    status: str = "allocated"  # allocated, used, returned
    allocated_by: str
    allocated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used_at: Optional[datetime] = None

class MaterialAllocationCreate(BaseModel):
    ticket_id: str
    item_id: str
    quantity: int

# ==================== PURCHASE ORDER MODELS ====================

class PurchaseOrderItem(BaseModel):
    item_id: str
    item_name: str
    quantity: int
    unit_price: float
    total_price: float
    received_quantity: int = 0

class PurchaseOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    po_id: str = Field(default_factory=lambda: f"po_{uuid.uuid4().hex[:12]}")
    po_number: str
    supplier_id: str
    supplier_name: str
    items: List[PurchaseOrderItem]
    subtotal: float
    tax_amount: float = 0.0
    total_amount: float
    status: str = "draft"  # draft, pending_approval, approved, ordered, partially_received, received, cancelled
    approval_status: str = "pending"  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    items: List[dict]  # [{item_id, quantity, unit_price}]
    expected_delivery: Optional[str] = None
    notes: Optional[str] = None

class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    approval_status: Optional[str] = None
    notes: Optional[str] = None

class StockReceiving(BaseModel):
    receiving_id: str = Field(default_factory=lambda: f"rcv_{uuid.uuid4().hex[:12]}")
    po_id: str
    item_id: str
    quantity_received: int
    received_by: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

# ==================== SERVICE/SALES MODELS ====================

class ServiceOffering(BaseModel):
    model_config = ConfigDict(extra="ignore")
    service_id: str = Field(default_factory=lambda: f"srv_{uuid.uuid4().hex[:12]}")
    name: str
    description: Optional[str] = None
    category: str  # battery_service, motor_service, charging_service, inspection, maintenance
    base_price: float
    estimated_hours: float
    parts_included: List[str] = []  # List of item_ids
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServiceOfferingCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    base_price: float
    estimated_hours: float
    parts_included: List[str] = []

class SalesOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sales_id: str = Field(default_factory=lambda: f"sal_{uuid.uuid4().hex[:12]}")
    ticket_id: str
    customer_id: str
    customer_name: str
    vehicle_id: str
    services: List[dict]  # [{service_id, name, price, quantity}]
    parts: List[dict]  # [{item_id, name, quantity, price}]
    labor_charges: float = 0.0
    parts_total: float = 0.0
    services_total: float = 0.0
    subtotal: float
    tax_rate: float = 18.0  # GST
    tax_amount: float
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    total_amount: float
    status: str = "draft"  # draft, pending_approval, approved, invoiced, completed
    approval_status: str = "pending"  # pending, level1_approved, level2_approved, rejected
    approved_by: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SalesOrderCreate(BaseModel):
    ticket_id: str
    services: List[dict] = []
    parts: List[dict] = []
    labor_charges: float = 0.0
    discount_percent: float = 0.0

class SalesOrderUpdate(BaseModel):
    status: Optional[str] = None
    approval_status: Optional[str] = None
    discount_percent: Optional[float] = None

# ==================== INVOICE MODELS ====================

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    invoice_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    invoice_number: str
    sales_id: Optional[str] = None
    ticket_id: str
    customer_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    vehicle_id: Optional[str] = None
    vehicle_details: Optional[str] = None
    line_items: List[dict]
    subtotal: float
    tax_rate: float = 18.0
    tax_amount: float
    discount_amount: float = 0.0
    total_amount: float
    amount_paid: float = 0.0
    balance_due: float
    status: str = "draft"  # draft, sent, partially_paid, paid, overdue, cancelled
    payment_status: str = "unpaid"  # unpaid, partial, paid
    due_date: datetime
    paid_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InvoiceCreate(BaseModel):
    ticket_id: str
    sales_id: Optional[str] = None
    line_items: List[dict]
    discount_amount: float = 0.0
    due_days: int = 30
    notes: Optional[str] = None

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    payment_id: str = Field(default_factory=lambda: f"pay_{uuid.uuid4().hex[:12]}")
    invoice_id: str
    amount: float
    payment_method: str  # cash, card, upi, bank_transfer, cheque
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    received_by: str
    payment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None

# ==================== ACCOUNTING MODELS ====================

class LedgerEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    entry_id: str = Field(default_factory=lambda: f"led_{uuid.uuid4().hex[:12]}")
    entry_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    account_type: str  # revenue, expense, asset, liability
    account_name: str
    description: str
    reference_type: str  # invoice, payment, purchase, allocation
    reference_id: str
    ticket_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    balance: float = 0.0
    created_by: str

class AccountSummary(BaseModel):
    total_revenue: float = 0.0
    total_expenses: float = 0.0
    total_receivables: float = 0.0
    total_payables: float = 0.0
    gross_profit: float = 0.0
    net_profit: float = 0.0

class CostAllocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cost_id: str = Field(default_factory=lambda: f"cst_{uuid.uuid4().hex[:12]}")
    ticket_id: str
    vehicle_id: str
    cost_type: str  # parts, labor, overhead
    description: str
    amount: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== VEHICLE & TICKET MODELS ====================

class Vehicle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    vehicle_id: str = Field(default_factory=lambda: f"veh_{uuid.uuid4().hex[:12]}")
    owner_id: str
    owner_name: str
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    make: str
    model: str
    year: int
    registration_number: str
    battery_capacity: float
    current_status: str = "active"
    total_service_cost: float = 0.0
    total_visits: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VehicleCreate(BaseModel):
    owner_name: str
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    make: str
    model: str
    year: int
    registration_number: str
    battery_capacity: float

class Ticket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ticket_id: str = Field(default_factory=lambda: f"tkt_{uuid.uuid4().hex[:12]}")
    # Vehicle Info
    vehicle_id: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_number: Optional[str] = None
    # Customer Info
    customer_id: Optional[str] = None
    customer_type: Optional[str] = None
    customer_name: Optional[str] = None
    contact_number: Optional[str] = None
    customer_email: Optional[str] = None
    # Assignment
    assigned_technician_id: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    # Complaint Details
    title: str
    description: str
    category: str
    issue_type: Optional[str] = None
    resolution_type: Optional[str] = None  # workshop, onsite, pickup, remote
    priority: str = "medium"
    status: str = "open"
    # Location
    incident_location: Optional[str] = None
    location_coordinates: Optional[dict] = None
    # Attachments
    attachments: List[dict] = []
    attachments_count: int = 0
    # Diagnosis & Resolution
    ai_diagnosis: Optional[str] = None
    resolution: Optional[str] = None
    # Financial tracking
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    parts_cost: float = 0.0
    labor_cost: float = 0.0
    has_sales_order: bool = False
    has_invoice: bool = False
    invoice_id: Optional[str] = None
    # Job Card - Costing & History
    estimated_items: dict = Field(default_factory=lambda: {"parts": [], "services": []})
    actual_items: dict = Field(default_factory=lambda: {"parts": [], "services": []})
    status_history: List[dict] = Field(default_factory=list)
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class TicketCreate(BaseModel):
    # Vehicle Info
    vehicle_id: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_number: Optional[str] = None
    # Customer Info
    customer_type: Optional[str] = None
    customer_name: Optional[str] = None
    contact_number: Optional[str] = None
    customer_email: Optional[str] = None
    # Complaint Details
    title: str
    description: str
    category: str
    issue_type: Optional[str] = None
    resolution_type: Optional[str] = None
    priority: str = "medium"
    # Location
    incident_location: Optional[str] = None
    # Attachments
    attachments_count: int = 0
    estimated_cost: float = 0.0

class TicketUpdate(BaseModel):
    assigned_technician_id: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    priority: Optional[str] = None
    estimated_cost: Optional[float] = None
    resolution_type: Optional[str] = None
    incident_location: Optional[str] = None
    estimated_items: Optional[dict] = None  # {parts: [], services: []}
    actual_items: Optional[dict] = None  # {parts: [], services: []}
    status_history: Optional[list] = None

# ==================== CUSTOMER MODELS (NEW) ====================

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    customer_id: str = Field(default_factory=lambda: f"cust_{uuid.uuid4().hex[:12]}")
    legacy_id: Optional[str] = None
    customer_number: Optional[str] = None
    display_name: str
    company_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    gst_number: Optional[str] = None
    gst_treatment: Optional[str] = None
    pan_number: Optional[str] = None
    billing_address: Optional[dict] = None
    shipping_address: Optional[dict] = None
    currency_code: str = "INR"
    payment_terms: str = "Due on Receipt"
    credit_limit: float = 0.0
    opening_balance: float = 0.0
    outstanding_balance: float = 0.0
    notes: Optional[str] = None
    status: str = "active"
    portal_enabled: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    migrated_from: Optional[str] = None

class CustomerCreate(BaseModel):
    display_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    billing_address: Optional[dict] = None
    payment_terms: str = "Due on Receipt"
    credit_limit: float = 0.0

class CustomerUpdate(BaseModel):
    display_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    billing_address: Optional[dict] = None
    status: Optional[str] = None

# ==================== EXPENSE MODELS (NEW) ====================

class Expense(BaseModel):
    model_config = ConfigDict(extra="ignore")
    expense_id: str = Field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:12]}")
    legacy_id: Optional[str] = None
    expense_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None
    expense_account: str
    expense_account_code: Optional[str] = None
    paid_through: Optional[str] = None
    paid_through_code: Optional[str] = None
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    amount: float
    subtotal: float = 0.0
    tax_amount: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    hsn_sac: Optional[str] = None
    gst_treatment: Optional[str] = None
    gst_number: Optional[str] = None
    currency_code: str = "INR"
    reference_number: Optional[str] = None
    is_billable: bool = False
    customer_name: Optional[str] = None
    project_name: Optional[str] = None
    location_name: Optional[str] = None
    created_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    migrated_from: Optional[str] = None

class ExpenseCreate(BaseModel):
    expense_date: str
    description: Optional[str] = None
    expense_account: str
    vendor_id: Optional[str] = None
    amount: float
    tax_amount: float = 0.0
    reference_number: Optional[str] = None
    is_billable: bool = False

# ==================== CHART OF ACCOUNTS MODEL (NEW) ====================

class ChartOfAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")
    account_id: str = Field(default_factory=lambda: f"acc_{uuid.uuid4().hex[:12]}")
    account_name: str
    account_code: Optional[str] = None
    description: Optional[str] = None
    account_type: str  # Asset, Liability, Equity, Income, Expense
    parent_account: Optional[str] = None
    is_active: bool = True
    currency: str = "INR"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    migrated_from: Optional[str] = None

# ==================== OTHER MODELS ====================

class AIQuery(BaseModel):
    issue_description: str
    vehicle_model: Optional[str] = None
    vehicle_category: Optional[str] = None
    category: Optional[str] = None

class AIResponse(BaseModel):
    solution: str
    confidence: float
    related_tickets: List[str] = []
    recommended_parts: List[str] = []
    diagnostic_steps: List[str] = []
    safety_warnings: List[str] = []
    estimated_cost_range: Optional[str] = None

class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    alert_id: str = Field(default_factory=lambda: f"alt_{uuid.uuid4().hex[:12]}")
    type: str
    title: str
    message: str
    severity: str = "info"
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardStats(BaseModel):
    vehicles_in_workshop: int
    open_repair_orders: int
    avg_repair_time: float
    available_technicians: int
    vehicle_status_distribution: dict
    monthly_repair_trends: List[dict]
    # Financial metrics
    total_revenue: float = 0.0
    pending_invoices: float = 0.0
    inventory_value: float = 0.0
    pending_purchase_orders: int = 0
    # Service Ticket Metrics (Enhanced)
    service_ticket_stats: dict = Field(default_factory=lambda: {
        "total_open": 0,
        "onsite_resolution": 0,
        "workshop_visit": 0,
        "pickup": 0,
        "remote": 0,
        "avg_resolution_time_hours": 0.0,
        "onsite_resolution_percentage": 0.0,
        "total_resolved_30d": 0,
        "total_onsite_resolved_30d": 0
    })

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str, role: str, org_id: str = None, password_version: float = 0) -> str:
    """Create JWT token with optional organization context and password version"""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "pwd_v": password_version,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    if org_id:
        payload["org_id"] = org_id
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> Optional[User]:
    session_token = request.cookies.get("session_token")
    auth_header = request.headers.get("Authorization")
    
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
                if user and user.get("is_active", True):
                    if isinstance(user.get('created_at'), str):
                        user['created_at'] = datetime.fromisoformat(user['created_at'])
                    return User(**user)
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                if not user.get("is_active", True):
                    return None
                token_pwd_v = payload.get("pwd_v", 0)
                db_pwd_v = user.get("password_version", 0)
                if token_pwd_v != db_pwd_v:
                    return None
                if isinstance(user.get('created_at'), str):
                    user['created_at'] = datetime.fromisoformat(user['created_at'])
                return User(**user)
        except:
            pass
    return None

async def require_auth(request: Request) -> User:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_admin(request: Request) -> User:
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_technician_or_admin(request: Request) -> User:
    user = await require_auth(request)
    if user.role not in ["admin", "technician"]:
        raise HTTPException(status_code=403, detail="Technician or admin access required")
    return user

# ==================== HELPER FUNCTIONS ====================

async def create_ledger_entry(
    account_type: str,
    account_name: str,
    description: str,
    reference_type: str,
    reference_id: str,
    debit: float,
    credit: float,
    created_by: str,
    ticket_id: Optional[str] = None,
    vehicle_id: Optional[str] = None
):
    """Create an accounting ledger entry for audit trail"""
    entry = {
        "entry_id": f"led_{uuid.uuid4().hex[:12]}",
        "entry_date": datetime.now(timezone.utc).isoformat(),
        "account_type": account_type,
        "account_name": account_name,
        "description": description,
        "reference_type": reference_type,
        "reference_id": reference_id,
        "ticket_id": ticket_id,
        "vehicle_id": vehicle_id,
        "debit": debit,
        "credit": credit,
        "balance": debit - credit,
        "created_by": created_by
    }
    await db.ledger.insert_one(entry)
    return entry

async def generate_po_number(org_id: str = None):
    """Generate sequential PO number per organisation (atomic, race-condition safe)"""
    if org_id:
        result = await db.sequences.find_one_and_update(
            {"organization_id": org_id, "sequence_type": "PURCHASE_ORDER"},
            {"$inc": {"current_value": 1}},
            upsert=True,
            return_document=True
        )
        seq = result["current_value"]
        return f"PO-{datetime.now().strftime('%Y%m')}-{str(seq).zfill(4)}"
    # Fallback for legacy calls without org_id
    count = await db.purchase_orders.count_documents({"organization_id": {"$exists": False}})
    return f"PO-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

async def generate_invoice_number(org_id: str = None):
    """Generate sequential invoice number per organisation (atomic, race-condition safe)"""
    if org_id:
        result = await db.sequences.find_one_and_update(
            {"organization_id": org_id, "sequence_type": "INVOICE"},
            {"$inc": {"current_value": 1}},
            upsert=True,
            return_document=True
        )
        seq = result["current_value"]
        return f"INV-{datetime.now().strftime('%Y%m')}-{str(seq).zfill(4)}"
    # Fallback
    count = await db.invoices.count_documents({"organization_id": {"$exists": False}})
    return f"INV-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

async def generate_sales_number(org_id: str = None):
    """Generate sequential sales order number per organisation (atomic, race-condition safe)"""
    if org_id:
        result = await db.sequences.find_one_and_update(
            {"organization_id": org_id, "sequence_type": "SALES_ORDER"},
            {"$inc": {"current_value": 1}},
            upsert=True,
            return_document=True
        )
        seq = result["current_value"]
        return f"SO-{datetime.now().strftime('%Y%m')}-{str(seq).zfill(4)}"
    # Fallback
    count = await db.sales_orders.count_documents({"organization_id": {"$exists": False}})
    return f"SO-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "designation": user_data.designation,
        "phone": user_data.phone,
        "picture": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, user_data.email, user_data.role)
    return {"token": token, "user_id": user_id, "role": user_data.role}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    """
    Login endpoint with multi-organization support.
    
    Returns user's organizations for org switcher functionality.
    If user belongs to multiple orgs, they can switch after login.
    """
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    stored_hash = user.get("password_hash", "")
    if not verify_password(credentials.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    # Transparent migration: if stored hash is SHA256 (64-char hex), re-hash to bcrypt
    if stored_hash and not (stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$")):
        new_bcrypt_hash = hash_password(credentials.password)
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"password_hash": new_bcrypt_hash}}
        )
        logger.info(f"Migrated SHA256 password to bcrypt for user {user['user_id']}")
    
    # Get user's organizations
    memberships = await db.organization_users.find(
        {"user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    ).to_list(20)
    
    organizations = []
    default_org_id = None
    
    for m in memberships:
        org = await db.organizations.find_one(
            {"organization_id": m["organization_id"], "is_active": True},
            {"_id": 0, "organization_id": 1, "name": 1, "slug": 1, "logo_url": 1, "plan_type": 1}
        )
        if org:
            organizations.append({
                "organization_id": org["organization_id"],
                "name": org["name"],
                "slug": org.get("slug"),
                "logo_url": org.get("logo_url"),
                "plan_type": org.get("plan_type", "free"),
                "role": m["role"]
            })
            if default_org_id is None:
                default_org_id = org["organization_id"]
    
    # Create token with default org
    token = create_token(user["user_id"], user["email"], user["role"], org_id=default_org_id, password_version=user.get("password_version", 0))
    
    # Return single org object if user has exactly one organization (for auto-selection)
    single_org = organizations[0] if len(organizations) == 1 else None
    
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "designation": user.get("designation"),
            "picture": user.get("picture"),
            "is_platform_admin": bool(user.get("is_platform_admin", False))
        },
        "organizations": organizations,
        "organization": single_org,  # Include full org object for single org users
        "current_organization": default_org_id
    }

@api_router.post("/auth/switch-organization")
async def switch_organization(request: Request):
    """
    Switch to a different organization.
    
    Returns a new token with the selected organization context.
    """
    body = await request.json()
    target_org_id = body.get("organization_id")
    
    if not target_org_id:
        raise HTTPException(status_code=400, detail="organization_id is required")
    
    # Get current user
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify user is a member of the target org
    membership = await db.organization_users.find_one({
        "user_id": user.user_id,
        "organization_id": target_org_id,
        "status": "active"
    })
    
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")
    
    # Create new token with target org
    token = create_token(user.user_id, user.email, membership["role"], org_id=target_org_id)
    
    # Get org details
    org = await db.organizations.find_one(
        {"organization_id": target_org_id},
        {"_id": 0, "organization_id": 1, "name": 1, "slug": 1, "logo_url": 1, "plan_type": 1}
    )
    
    # Update last active
    await db.organization_users.update_one(
        {"organization_id": target_org_id, "user_id": user.user_id},
        {"$set": {"last_active_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "token": token,
        "organization": org,
        "role": membership["role"]
    }

@api_router.post("/auth/session")
async def process_google_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        google_data = resp.json()
    
    existing_user = await db.users.find_one({"email": google_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": google_data["name"], "picture": google_data["picture"]}}
        )
        role = existing_user["role"]
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": google_data["email"],
            "name": google_data["name"],
            "picture": google_data["picture"],
            "role": "customer",
            "designation": None,
            "phone": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        role = "customer"
    
    session_token = google_data["session_token"]
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return {
        "user": {
            "user_id": user_id,
            "email": google_data["email"],
            "name": google_data["name"],
            "role": role,
            "picture": google_data["picture"]
        }
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Fetch full user doc to include is_platform_admin
    full_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "designation": user.designation,
        "picture": user.picture,
        "is_platform_admin": bool(full_user.get("is_platform_admin", False)) if full_user else False
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ==================== PASSWORD MANAGEMENT ====================

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6)


@api_router.post("/auth/change-password")
async def change_password(request: Request, data: ChangePasswordRequest):
    """Self-service password change — requires current password"""
    user = await require_auth(request)
    full_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stored_hash = full_user.get("password_hash", "")
    if not stored_hash:
        raise HTTPException(status_code=400, detail="Account uses social login — no password to change")
    
    if not verify_password(data.current_password, stored_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    new_hash = hash_password(data.new_password)
    new_pwd_version = datetime.now(timezone.utc).timestamp()
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "password_hash": new_hash,
            "password_version": new_pwd_version,
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    logger.info(f"Password changed for user {user.user_id}")
    from utils.audit import log_audit, AuditAction
    await log_audit(db, AuditAction.PASSWORD_CHANGED, "", user.user_id, "user", user.user_id)
    return {"message": "Password changed successfully"}


@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Send a time-limited password reset link via email"""
    import secrets, hashlib
    user = await db.users.find_one({"email": data.email}, {"_id": 0, "password_hash": 0})
    # Always return success to prevent email enumeration
    if not user:
        logger.info(f"Forgot password for non-existent email: {data.email}")
        return {"message": "If an account with that email exists, a reset link has been sent."}
    
    # Generate a secure token
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Store hashed token with 1-hour expiry
    await db.password_reset_tokens.delete_many({"user_id": user["user_id"]})  # Remove old tokens
    await db.password_reset_tokens.insert_one({
        "user_id": user["user_id"],
        "email": user["email"],
        "token_hash": token_hash,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "used": False
    })
    
    # Build reset link using FRONTEND URL
    frontend_url = os.environ.get("APP_URL", os.environ.get("REACT_APP_BACKEND_URL", "https://battwheels.com"))
    reset_link = f"{frontend_url}/reset-password?token={raw_token}"
    
    # Send email
    try:
        from services.email_service import EmailService
        await EmailService.send_email(
            to=user["email"],
            subject="Reset your Battwheels OS password",
            html_content=f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h2 style="margin: 0 0 20px; color: #111827; font-size: 20px;">Reset Your Password</h2>
                <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                    Hi {user.get('name', 'there')},
                </p>
                <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                    We received a request to reset your password. Click the button below to create a new password:
                </p>
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td align="center" style="padding: 20px 0;">
                            <a href="{reset_link}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                                Reset Password
                            </a>
                        </td>
                    </tr>
                </table>
                <p style="margin: 24px 0 0; color: #9ca3af; font-size: 14px;">
                    This link expires in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                </p>
            </div>
            """
        )
        logger.info(f"Password reset email sent to {user['email']}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
    
    return {"message": "If an account with that email exists, a reset link has been sent."}


@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using a valid token from the forgot-password email"""
    import hashlib
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    
    token_doc = await db.password_reset_tokens.find_one({
        "token_hash": token_hash,
        "used": False,
    })
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    if datetime.now(timezone.utc) > token_doc["expires_at"]:
        await db.password_reset_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    
    # Update password
    new_hash = hash_password(data.new_password)
    new_pwd_version = datetime.now(timezone.utc).timestamp()
    await db.users.update_one(
        {"user_id": token_doc["user_id"]},
        {"$set": {
            "password_hash": new_hash,
            "password_version": new_pwd_version,
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})
    
    logger.info(f"Password reset completed for user {token_doc['user_id']}")
    return {"message": "Password has been reset successfully. You can now log in with your new password."}


@v1_router.post("/employees/{employee_id}/reset-password")
async def admin_reset_employee_password(employee_id: str, data: AdminResetPasswordRequest, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    """Admin resets an employee's login password"""
    admin_user = await require_admin(request)
    
    # Find the employee — check org-scoped first, then fallback to unscoped (legacy data)
    employee = await db.employees.find_one({"employee_id": employee_id, "organization_id": ctx.org_id}, {"_id": 0})
    if not employee:
        employee = await db.employees.find_one({"employee_id": employee_id, "organization_id": {"$in": [None, ""]}}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    work_email = employee.get("work_email")
    if not work_email:
        raise HTTPException(status_code=400, detail="Employee has no work email — cannot reset password")
    
    # Find the user account linked to this employee's work email
    user = await db.users.find_one({"email": work_email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="No user account found for this employee's work email")
    
    new_hash = hash_password(data.new_password)
    new_pwd_version = datetime.now(timezone.utc).timestamp()
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "password_hash": new_hash,
            "password_version": new_pwd_version,
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    logger.info(f"Admin {admin_user.user_id} reset password for employee {employee_id} (user {user['user_id']})")
    return {"message": f"Password reset successfully for {employee.get('full_name', work_email)}"}


# ==================== USER ROUTES ====================

@v1_router.get("/users")
async def get_users(request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    await require_admin(request)
    # Return only users who are members of this organisation (not all platform users)
    memberships = await db.organization_users.find(
        {"organization_id": ctx.org_id, "status": "active"},
        {"user_id": 1}
    ).to_list(1000)
    member_ids = [m["user_id"] for m in memberships]
    users = await db.users.find(
        {"user_id": {"$in": member_ids}},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    return users

@v1_router.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    await require_auth(request)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@v1_router.put("/users/{user_id}")
async def update_user(user_id: str, update: UserUpdate, request: Request):
    current_user = await require_auth(request)
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot update other users")
    if update.role and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_dict:
        await db.users.update_one({"user_id": user_id}, {"$set": update_dict})
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return user

@v1_router.get("/technicians")
async def get_technicians(request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    await require_auth(request)
    # Return technicians belonging to this org only
    memberships = await db.organization_users.find(
        {"organization_id": ctx.org_id, "role": "technician", "status": "active"},
        {"user_id": 1}
    ).to_list(200)
    tech_ids = [m["user_id"] for m in memberships]
    technicians = await db.users.find(
        {"user_id": {"$in": tech_ids}, "is_active": True},
        {"_id": 0, "password_hash": 0}
    ).to_list(200)
    return technicians

# ==================== SUPPLIER ROUTES ====================

@v1_router.post("/suppliers")
async def create_supplier(
    data: SupplierCreate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    
    supplier = Supplier(**data.model_dump())
    doc = supplier.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['organization_id'] = ctx.org_id
    await db.suppliers.insert_one(doc)
    return supplier.model_dump()

@v1_router.get("/suppliers")
async def get_suppliers(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"organization_id": ctx.org_id}
    suppliers = await db.suppliers.find(query, {"_id": 0}).to_list(1000)
    return suppliers

@v1_router.get("/suppliers/{supplier_id}")
async def get_supplier(
    supplier_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"supplier_id": supplier_id, "organization_id": ctx.org_id}
    supplier = await db.suppliers.find_one(query, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@v1_router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: str, 
    update: SupplierUpdate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    query = {"supplier_id": supplier_id, "organization_id": ctx.org_id}
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.suppliers.update_one(query, {"$set": update_dict})
    supplier = await db.suppliers.find_one(query, {"_id": 0})
    return supplier

# ==================== VEHICLE ROUTES ====================

@v1_router.post("/vehicles")
async def create_vehicle(
    vehicle_data: VehicleCreate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    user = await require_auth(request)
    
    vehicle = Vehicle(
        owner_id=user.user_id,
        owner_name=vehicle_data.owner_name,
        owner_email=vehicle_data.owner_email,
        owner_phone=vehicle_data.owner_phone,
        make=vehicle_data.make,
        model=vehicle_data.model,
        year=vehicle_data.year,
        registration_number=vehicle_data.registration_number,
        battery_capacity=vehicle_data.battery_capacity
    )
    doc = vehicle.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['organization_id'] = ctx.org_id
    await db.vehicles.insert_one(doc)
    return vehicle.model_dump()

@v1_router.get("/vehicles")
async def get_vehicles(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    user = await require_auth(request)
    base_query = {"organization_id": ctx.org_id}
    
    if user.role in ["admin", "technician"]:
        vehicles = await db.vehicles.find(base_query, {"_id": 0}).to_list(1000)
    else:
        query = {**base_query, "owner_id": user.user_id}
        vehicles = await db.vehicles.find(query, {"_id": 0}).to_list(100)
    return vehicles

@v1_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"vehicle_id": vehicle_id, "organization_id": ctx.org_id}
    
    vehicle = await db.vehicles.find_one(query, {"_id": 0})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@v1_router.put("/vehicles/{vehicle_id}/status")
async def update_vehicle_status(
    vehicle_id: str, 
    status: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    if status not in ["active", "in_workshop", "serviced"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    query = {"vehicle_id": vehicle_id, "organization_id": ctx.org_id}
    await db.vehicles.update_one(query, {"$set": {"current_status": status}})
    return {"message": "Status updated"}

# ==================== TICKET ROUTES (MIGRATED TO /routes/tickets.py) ====================
# Old monolithic ticket routes have been moved to the event-driven tickets module.
# See: /app/backend/routes/tickets.py and /app/backend/services/ticket_service.py
# The new module:
# - Emits events (TICKET_CREATED, TICKET_UPDATED, TICKET_CLOSED)
# - Integrates with EFI AI matching pipeline
# - Triggers confidence engine on ticket closure
# - Auto-creates draft failure cards for undocumented issues

# ==================== INVENTORY ROUTES ====================

@v1_router.post("/inventory")
async def create_inventory_item(
    item_data: InventoryCreate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    
    # Get supplier name if provided
    supplier_name = None
    if item_data.supplier_id:
        supplier_query = {"supplier_id": item_data.supplier_id, "organization_id": ctx.org_id}
        supplier = await db.suppliers.find_one(supplier_query, {"_id": 0})
        supplier_name = supplier.get("name") if supplier else None
    
    item = InventoryItem(**item_data.model_dump(), supplier_name=supplier_name)
    doc = item.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['organization_id'] = ctx.org_id
    await db.inventory.insert_one(doc)
    return item.model_dump()

@v1_router.get("/inventory")
async def get_inventory(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1),
    category: Optional[str] = Query(None),
    low_stock: bool = Query(False)
):
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")
    await require_auth(request)
    query = {"organization_id": ctx.org_id}
    if category:
        query["category"] = category
    if low_stock:
        query["$expr"] = {"$lte": ["$quantity", "$reorder_level"]}
    total = await db.inventory.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1
    items = await db.inventory.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {
        "data": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@v1_router.get("/inventory/reorder-suggestions")
async def get_inventory_reorder_suggestions(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    GET /api/inventory/reorder-suggestions
    Items where qty <= reorder_level, grouped by preferred vendor.
    """
    await require_auth(request)
    query = {
        "organization_id": ctx.org_id,
        "$expr": {"$lte": ["$quantity", "$reorder_level"]}
    }
    items = await db.inventory.find(query, {"_id": 0}).to_list(500)

    suggestions = []
    by_vendor: dict = {}
    for item in items:
        qty = float(item.get("quantity", 0))
        reorder = float(item.get("reorder_level", 10))
        shortage = max(0.0, reorder - qty)
        suggested_qty = item.get("reorder_quantity", max(int(shortage * 1.5), 1))
        unit_cost = float(item.get("cost_price") or item.get("unit_price", 0))
        s = {
            "item_id": item.get("item_id", ""),
            "item_name": item.get("name", ""),
            "sku": item.get("sku", ""),
            "category": item.get("category", ""),
            "current_stock_qty": qty,
            "reorder_level": reorder,
            "shortage": round(shortage, 2),
            "suggested_qty": suggested_qty,
            "unit_cost": unit_cost,
            "estimated_cost": round(suggested_qty * unit_cost, 2),
            "vendor_id": item.get("preferred_vendor_id"),
            "vendor_name": item.get("preferred_vendor_name", "No preferred vendor"),
        }
        suggestions.append(s)
        key = s.get("vendor_id") or "no_vendor"
        if key not in by_vendor:
            by_vendor[key] = {
                "vendor_id": s.get("vendor_id"),
                "vendor_name": s.get("vendor_name", "No preferred vendor"),
                "items": [], "total_estimated_cost": 0.0
            }
        by_vendor[key]["items"].append(s)
        by_vendor[key]["total_estimated_cost"] = round(
            by_vendor[key]["total_estimated_cost"] + s["estimated_cost"], 2
        )

    return {
        "code": 0,
        "total_items_below_reorder": len(suggestions),
        "suggestions": suggestions,
        "grouped_by_vendor": list(by_vendor.values()),
    }


@v1_router.get("/inventory/stocktakes")
async def list_stocktakes_api(
    request: Request,
    status: Optional[str] = None,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """GET /api/inventory/stocktakes — List stocktake sessions for org."""
    await require_auth(request)
    query: dict = {"organization_id": ctx.org_id}
    if status:
        query["status"] = status
    stocktakes = await db.stocktakes.find(
        query,
        {"_id": 0, "stocktake_id": 1, "name": 1, "status": 1,
         "total_lines": 1, "counted_lines": 1, "total_variance": 1,
         "created_at": 1, "finalized_at": 1}
    ).sort("created_at", -1).to_list(100)
    return {"code": 0, "stocktakes": stocktakes, "total": len(stocktakes)}


class StocktakeCreateModel(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    item_ids: Optional[list] = None


@v1_router.post("/inventory/stocktakes")
async def create_stocktake_api(
    data: StocktakeCreateModel,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """POST /api/inventory/stocktakes — Create stocktake session."""
    import uuid as _uuid
    await require_technician_or_admin(request)
    org_id = ctx.org_id
    now_iso = datetime.now(timezone.utc).isoformat()
    stocktake_id = f"ST-{_uuid.uuid4().hex[:12].upper()}"

    item_query: dict = {"organization_id": org_id}
    if data.item_ids:
        item_query["item_id"] = {"$in": data.item_ids}

    items = await db.inventory.find(
        item_query, {"_id": 0, "item_id": 1, "name": 1, "sku": 1, "quantity": 1}
    ).to_list(2000)

    lines = [{
        "item_id": it["item_id"],
        "item_name": it["name"],
        "sku": it.get("sku", ""),
        "system_quantity": float(it.get("quantity", 0)),
        "counted_quantity": None,
        "variance": None,
        "notes": "",
        "counted": False,
    } for it in items]

    doc = {
        "stocktake_id": stocktake_id,
        "name": data.name or f"Stocktake {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "organization_id": org_id,
        "status": "in_progress",
        "lines": lines,
        "total_lines": len(lines),
        "counted_lines": 0,
        "total_variance": 0,
        "notes": data.notes or "",
        "created_at": now_iso,
        "updated_at": now_iso,
        "finalized_at": None,
    }
    await db.stocktakes.insert_one(doc)
    doc.pop("_id", None)
    return {"code": 0, "message": "Stocktake created", "stocktake": doc}


@v1_router.get("/inventory/{item_id}")
async def get_inventory_item(
    item_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"item_id": item_id, "organization_id": ctx.org_id}
    item = await db.inventory.find_one(query, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@v1_router.put("/inventory/{item_id}")
async def update_inventory_item(
    item_id: str, 
    update: InventoryUpdate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    query = {"item_id": item_id, "organization_id": ctx.org_id}
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Update supplier name if supplier_id changed
    if update.supplier_id:
        supplier_query = {"supplier_id": update.supplier_id, "organization_id": ctx.org_id}
        supplier = await db.suppliers.find_one(supplier_query, {"_id": 0})
        update_dict["supplier_name"] = supplier.get("name") if supplier else None
    
    await db.inventory.update_one(query, {"$set": update_dict})
    item = await db.inventory.find_one(query, {"_id": 0})
    return item

@v1_router.delete("/inventory/{item_id}")
async def delete_inventory_item(
    item_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_admin(request)
    query = {"item_id": item_id, "organization_id": ctx.org_id}
    await db.inventory.delete_one(query)
    return {"message": "Item deleted"}

# ==================== MATERIAL ALLOCATION ROUTES ====================

@v1_router.post("/allocations")
async def create_allocation(data: MaterialAllocationCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    """Allocate materials from inventory to a ticket"""
    user = await require_technician_or_admin(request)
    org_id = ctx.org_id
    
    # Verify ticket exists AND belongs to this org
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id, "organization_id": org_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get item details and check stock — scoped to this org
    item = await db.inventory.find_one({"item_id": data.item_id, "organization_id": org_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    available = item["quantity"] - item.get("reserved_quantity", 0)
    if available < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {available}")
    
    # Create allocation
    allocation = MaterialAllocation(
        ticket_id=data.ticket_id,
        item_id=data.item_id,
        item_name=item["name"],
        quantity=data.quantity,
        unit_price=item["unit_price"],
        total_price=data.quantity * item["unit_price"],
        allocated_by=user.user_id
    )
    doc = allocation.model_dump()
    doc['allocated_at'] = doc['allocated_at'].isoformat()
    doc['organization_id'] = org_id
    await db.allocations.insert_one(doc)
    
    # Update inventory reserved quantity (scoped)
    await db.inventory.update_one(
        {"item_id": data.item_id, "organization_id": org_id},
        {"$inc": {"reserved_quantity": data.quantity}}
    )
    
    # Update ticket parts cost (scoped)
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id, "organization_id": org_id},
        {"$inc": {"parts_cost": allocation.total_price}}
    )
    
    # Create ledger entry for COGS
    await create_ledger_entry(
        account_type="expense",
        account_name="Cost of Goods Sold",
        description=f"Parts allocated: {item['name']} x {data.quantity}",
        reference_type="allocation",
        reference_id=allocation.allocation_id,
        debit=allocation.total_price,
        credit=0,
        created_by=user.user_id,
        ticket_id=data.ticket_id,
        vehicle_id=ticket.get("vehicle_id")
    )
    
    return allocation.model_dump()

@v1_router.get("/allocations")
async def get_allocations(request: Request, ctx: TenantContext = Depends(tenant_context_required), ticket_id: Optional[str] = None):
    await require_auth(request)
    query = {"organization_id": ctx.org_id}
    if ticket_id:
        query["ticket_id"] = ticket_id
    allocations = await db.allocations.find(query, {"_id": 0}).to_list(1000)
    return allocations

@v1_router.put("/allocations/{allocation_id}/use")
async def mark_allocation_used(allocation_id: str, request: Request):
    """Mark allocated materials as used"""
    user = await require_technician_or_admin(request)
    
    allocation = await db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    # Update allocation status
    await db.allocations.update_one(
        {"allocation_id": allocation_id},
        {"$set": {"status": "used", "used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Reduce actual inventory quantity
    await db.inventory.update_one(
        {"item_id": allocation["item_id"]},
        {
            "$inc": {
                "quantity": -allocation["quantity"],
                "reserved_quantity": -allocation["quantity"]
            }
        }
    )
    
    return {"message": "Allocation marked as used"}

@v1_router.put("/allocations/{allocation_id}/return")
async def return_allocation(allocation_id: str, request: Request):
    """Return allocated materials to inventory"""
    user = await require_technician_or_admin(request)
    
    allocation = await db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    # Update allocation status
    await db.allocations.update_one(
        {"allocation_id": allocation_id},
        {"$set": {"status": "returned"}}
    )
    
    # Release reserved quantity
    await db.inventory.update_one(
        {"item_id": allocation["item_id"]},
        {"$inc": {"reserved_quantity": -allocation["quantity"]}}
    )
    
    # Update ticket parts cost
    await db.tickets.update_one(
        {"ticket_id": allocation["ticket_id"]},
        {"$inc": {"parts_cost": -allocation["total_price"]}}
    )
    
    return {"message": "Materials returned to inventory"}

# ==================== PURCHASE ORDER ROUTES ====================

@v1_router.post("/purchase-orders")
async def create_purchase_order(data: PurchaseOrderCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_technician_or_admin(request)
    
    # Get supplier
    supplier = await db.suppliers.find_one({"supplier_id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Build order items
    order_items = []
    subtotal = 0
    for item_data in data.items:
        inv_item = await db.inventory.find_one({"item_id": item_data["item_id"]}, {"_id": 0})
        if inv_item:
            item_total = item_data["quantity"] * item_data.get("unit_price", inv_item.get("cost_price", inv_item["unit_price"]))
            order_items.append(PurchaseOrderItem(
                item_id=item_data["item_id"],
                item_name=inv_item["name"],
                quantity=item_data["quantity"],
                unit_price=item_data.get("unit_price", inv_item.get("cost_price", inv_item["unit_price"])),
                total_price=item_total
            ))
            subtotal += item_total
    
    tax_amount = subtotal * 0.18  # 18% GST
    total_amount = subtotal + tax_amount
    
    po_number = await generate_po_number(ctx.org_id)
    
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=data.supplier_id,
        supplier_name=supplier["name"],
        items=[item.model_dump() for item in order_items],
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        expected_delivery=datetime.fromisoformat(data.expected_delivery) if data.expected_delivery else None,
        notes=data.notes,
        created_by=user.user_id
    )
    
    doc = po.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    if doc['expected_delivery']:
        doc['expected_delivery'] = doc['expected_delivery'].isoformat()
    await db.purchase_orders.insert_one(doc)
    
    return po.model_dump()

@v1_router.get("/purchase-orders")
async def get_purchase_orders(request: Request, status: Optional[str] = None):
    await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    pos = await db.purchase_orders.find(query, {"_id": 0}).to_list(1000)
    return pos

@v1_router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str, request: Request):
    await require_auth(request)
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@v1_router.put("/purchase-orders/{po_id}")
async def update_purchase_order(po_id: str, update: PurchaseOrderUpdate, request: Request):
    user = await require_admin(request)
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update.approval_status == "approved":
        update_dict["approved_by"] = user.user_id
        update_dict["approved_at"] = datetime.now(timezone.utc).isoformat()
        update_dict["status"] = "approved"
    elif update.approval_status == "rejected":
        update_dict["status"] = "cancelled"
    
    await db.purchase_orders.update_one({"po_id": po_id}, {"$set": update_dict})
    
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    
    # Create ledger entry for approved PO
    if update.approval_status == "approved":
        await create_ledger_entry(
            account_type="liability",
            account_name="Accounts Payable",
            description=f"Purchase Order: {po['po_number']}",
            reference_type="purchase",
            reference_id=po_id,
            debit=0,
            credit=po["total_amount"],
            created_by=user.user_id
        )
    
    return po

@v1_router.post("/purchase-orders/{po_id}/receive")
async def receive_stock(po_id: str, items: List[dict], request: Request):
    """Receive stock from purchase order and update inventory"""
    user = await require_technician_or_admin(request)
    
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    all_received = True
    for received_item in items:
        item_id = received_item["item_id"]
        qty = received_item["quantity"]
        
        # Update PO item received quantity
        for po_item in po["items"]:
            if po_item["item_id"] == item_id:
                new_received = po_item.get("received_quantity", 0) + qty
                if new_received < po_item["quantity"]:
                    all_received = False
                
                # Update inventory
                await db.inventory.update_one(
                    {"item_id": item_id},
                    {
                        "$inc": {"quantity": qty},
                        "$set": {"last_restock_date": datetime.now(timezone.utc).isoformat()}
                    }
                )
                
                # Log receiving
                receiving_doc = {
                    "receiving_id": f"rcv_{uuid.uuid4().hex[:12]}",
                    "po_id": po_id,
                    "item_id": item_id,
                    "quantity_received": qty,
                    "received_by": user.user_id,
                    "received_at": datetime.now(timezone.utc).isoformat()
                }
                await db.stock_receivings.insert_one(receiving_doc)
                break
    
    # Update PO status
    new_status = "received" if all_received else "partially_received"
    await db.purchase_orders.update_one(
        {"po_id": po_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update supplier stats
    await db.suppliers.update_one(
        {"supplier_id": po["supplier_id"]},
        {"$inc": {"total_orders": 1, "total_value": po["total_amount"]}}
    )
    
    return {"message": f"Stock received. Status: {new_status}"}

# ==================== SERVICE OFFERING ROUTES ====================

@v1_router.post("/services")
async def create_service(data: ServiceOfferingCreate, request: Request):
    await require_admin(request)
    service = ServiceOffering(**data.model_dump())
    doc = service.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.services.insert_one(doc)
    return service.model_dump()

@v1_router.get("/services")
async def get_services(request: Request):
    await require_auth(request)
    services = await db.services.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return services

@v1_router.put("/services/{service_id}")
async def update_service(service_id: str, data: dict, request: Request):
    await require_admin(request)
    await db.services.update_one({"service_id": service_id}, {"$set": data})
    service = await db.services.find_one({"service_id": service_id}, {"_id": 0})
    return service

# ==================== SALES ORDER ROUTES ====================

@v1_router.post("/sales-orders")
async def create_sales_order(data: SalesOrderCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_technician_or_admin(request)
    
    # Get ticket details
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get vehicle details
    vehicle = await db.vehicles.find_one({"vehicle_id": ticket["vehicle_id"]}, {"_id": 0})
    
    # Calculate totals
    services_total = sum(s.get("price", 0) * s.get("quantity", 1) for s in data.services)
    parts_total = sum(p.get("price", 0) * p.get("quantity", 1) for p in data.parts)
    subtotal = services_total + parts_total + data.labor_charges
    
    discount_amount = subtotal * (data.discount_percent / 100)
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * 0.18  # 18% GST
    total_amount = taxable_amount + tax_amount
    
    sales_number = await generate_sales_number(ctx.org_id)
    
    sales_order = SalesOrder(
        ticket_id=data.ticket_id,
        customer_id=ticket["customer_id"],
        customer_name=vehicle.get("owner_name", "") if vehicle else "",
        vehicle_id=ticket["vehicle_id"],
        services=data.services,
        parts=data.parts,
        labor_charges=data.labor_charges,
        parts_total=parts_total,
        services_total=services_total,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_percent=data.discount_percent,
        discount_amount=discount_amount,
        total_amount=total_amount,
        created_by=user.user_id
    )
    
    doc = sales_order.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.sales_orders.insert_one(doc)
    
    # Update ticket
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id},
        {"$set": {"has_sales_order": True, "estimated_cost": total_amount}}
    )
    
    return sales_order.model_dump()

@v1_router.get("/sales-orders")
async def get_sales_orders(request: Request, status: Optional[str] = None):
    await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    orders = await db.sales_orders.find(query, {"_id": 0}).to_list(1000)
    return orders

@v1_router.get("/sales-orders/{sales_id}")
async def get_sales_order(sales_id: str, request: Request):
    await require_auth(request)
    order = await db.sales_orders.find_one({"sales_id": sales_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return order

@v1_router.put("/sales-orders/{sales_id}")
async def update_sales_order(sales_id: str, update: SalesOrderUpdate, request: Request):
    user = await require_auth(request)
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update.approval_status in ["level1_approved", "level2_approved"]:
        update_dict["approved_by"] = user.user_id
        if update.approval_status == "level2_approved":
            update_dict["status"] = "approved"
    
    await db.sales_orders.update_one({"sales_id": sales_id}, {"$set": update_dict})
    order = await db.sales_orders.find_one({"sales_id": sales_id}, {"_id": 0})
    return order

# ==================== INVOICE ROUTES ====================

@v1_router.post("/invoices")
async def create_invoice(data: InvoiceCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_technician_or_admin(request)
    
    # Get ticket details
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get vehicle and customer details (vehicle_id may be None)
    vehicle_id = ticket.get("vehicle_id")
    vehicle = None
    if vehicle_id:
        vehicle = await db.vehicles.find_one({"vehicle_id": vehicle_id}, {"_id": 0})
    
    # Calculate totals
    subtotal = sum(item.get("amount", 0) for item in data.line_items)
    tax_amount = (subtotal - data.discount_amount) * 0.18
    total_amount = subtotal - data.discount_amount + tax_amount
    
    invoice_number = await generate_invoice_number(ctx.org_id)
    due_date = datetime.now(timezone.utc) + timedelta(days=data.due_days)
    
    invoice = Invoice(
        invoice_number=invoice_number,
        sales_id=data.sales_id,
        ticket_id=data.ticket_id,
        customer_id=ticket.get("customer_id", user.user_id),
        customer_name=ticket.get("customer_name") or (vehicle.get("owner_name", "") if vehicle else ""),
        customer_email=ticket.get("customer_email") or (vehicle.get("owner_email") if vehicle else None),
        customer_phone=ticket.get("contact_number") or (vehicle.get("owner_phone") if vehicle else None),
        vehicle_id=vehicle_id,
        vehicle_details=f"{vehicle['make']} {vehicle['model']} ({vehicle['registration_number']})" if vehicle else ticket.get("vehicle_number"),
        line_items=data.line_items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=data.discount_amount,
        total_amount=total_amount,
        balance_due=total_amount,
        due_date=due_date,
        notes=data.notes,
        created_by=user.user_id
    )
    
    doc = invoice.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['due_date'] = doc['due_date'].isoformat()
    doc['organization_id'] = ctx.org_id   # tenant scope
    await db.invoices.insert_one(doc)
    
    # Update ticket
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id},
        {"$set": {"has_invoice": True, "invoice_id": invoice.invoice_id, "actual_cost": total_amount}}
    )
    
    # Create ledger entry
    await create_ledger_entry(
        account_type="asset",
        account_name="Accounts Receivable",
        description=f"Invoice: {invoice_number}",
        reference_type="invoice",
        reference_id=invoice.invoice_id,
        debit=total_amount,
        credit=0,
        created_by=user.user_id,
        ticket_id=data.ticket_id,
        vehicle_id=ticket["vehicle_id"]
    )
    
    return invoice.model_dump()

@v1_router.get("/invoices")
async def get_invoices(request: Request, status: Optional[str] = None, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_auth(request)
    query = {"organization_id": ctx.org_id}   # tenant-scoped
    if status:
        query["status"] = status
    if user.role == "customer":
        query["customer_id"] = user.user_id
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices

@v1_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    await require_auth(request)
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@v1_router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, update: InvoiceUpdate, request: Request):
    await require_technician_or_admin(request)
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": update_dict})
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    return invoice

@v1_router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, request: Request):
    """Generate and download invoice PDF with GST compliance"""
    from services.invoice_service import generate_invoice_pdf
    from fastapi.responses import StreamingResponse
    
    await require_auth(request)
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Transform existing invoice format to PDF service format
    customer_data = {
        "name": invoice.get("customer_name", "Customer"),
        "address": "",
        "city": "Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "gstin": None
    }
    
    # Try to get customer details
    if invoice.get("customer_id"):
        customer = await db.customers.find_one({"customer_id": invoice["customer_id"]}, {"_id": 0})
        if customer:
            customer_data = {
                "name": customer.get("name", invoice.get("customer_name", "")),
                "address": customer.get("address", ""),
                "city": customer.get("city", "Delhi"),
                "state": customer.get("state", "Delhi"),
                "pincode": customer.get("pincode", "110001"),
                "gstin": customer.get("gstin")
            }
    
    # Transform line items
    line_items = []
    for item in invoice.get("line_items", []):
        line_items.append({
            "description": item.get("description", item.get("name", "Service")),
            "hsn_sac": item.get("hsn_sac", "998714"),
            "quantity": item.get("quantity", 1),
            "unit": item.get("unit", "pcs"),
            "rate": item.get("rate", item.get("amount", 0)),
            "gst_percent": 18
        })
    
    # Build PDF-compatible invoice
    pdf_invoice = {
        "invoice_id": invoice.get("invoice_id"),
        "invoice_number": invoice.get("invoice_number"),
        "invoice_date": invoice.get("created_at", datetime.now(timezone.utc).isoformat())[:10].replace("-", "/"),
        "due_date": invoice.get("due_date", datetime.now(timezone.utc).isoformat())[:10].replace("-", "/"),
        "terms": "Due on Receipt",
        "vehicle_number": invoice.get("vehicle_details", "").split("(")[-1].replace(")", "") if invoice.get("vehicle_details") else "N/A",
        "po_number": invoice.get("invoice_number"),
        "place_of_supply": customer_data.get("state", "Delhi"),
        "place_of_supply_code": "07",  # Default to Delhi
        "customer": customer_data,
        "line_items": line_items,
        "sub_total": invoice.get("subtotal", 0),
        "igst_amount": invoice.get("tax_amount", 0),
        "cgst_amount": 0,
        "sgst_amount": 0,
        "rounding": 0,
        "total_amount": invoice.get("total_amount", 0),
        "total_in_words": ""
    }
    
    # Calculate total in words
    from services.invoice_service import number_to_words
    pdf_invoice["total_in_words"] = number_to_words(pdf_invoice["total_amount"])
    
    # Generate PDF
    pdf_buffer = generate_invoice_pdf(pdf_invoice)
    
    filename = f"{invoice.get('invoice_number', invoice_id)}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== PAYMENT ROUTES ====================

@v1_router.post("/payments")
async def record_payment(data: PaymentCreate, request: Request):
    user = await require_technician_or_admin(request)
    
    # Get invoice
    invoice = await db.invoices.find_one({"invoice_id": data.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment = Payment(
        invoice_id=data.invoice_id,
        amount=data.amount,
        payment_method=data.payment_method,
        reference_number=data.reference_number,
        notes=data.notes,
        received_by=user.user_id
    )
    
    doc = payment.model_dump()
    doc['payment_date'] = doc['payment_date'].isoformat()
    await db.payments.insert_one(doc)
    
    # Update invoice — support both legacy (total_amount) and enhanced (grand_total) schema
    total = invoice.get("grand_total") or invoice.get("total_amount", 0)
    current_paid = invoice.get("amount_paid", 0)
    new_amount_paid = current_paid + data.amount
    new_balance = total - new_amount_paid
    
    payment_status = "paid" if new_balance <= 0 else "partial"
    invoice_status = "paid" if new_balance <= 0 else "partially_paid"
    
    update_data = {
        "amount_paid": new_amount_paid,
        "balance_due": max(0, new_balance),
        "payment_status": payment_status,
        "status": invoice_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if new_balance <= 0:
        update_data["paid_date"] = datetime.now(timezone.utc).isoformat()
    
    await db.invoices.update_one({"invoice_id": data.invoice_id}, {"$set": update_data})
    
    # Create ledger entries
    await create_ledger_entry(
        account_type="asset",
        account_name="Cash/Bank",
        description=f"Payment received: {data.payment_method}",
        reference_type="payment",
        reference_id=payment.payment_id,
        debit=data.amount,
        credit=0,
        created_by=user.user_id,
        ticket_id=invoice.get("ticket_id"),
        vehicle_id=invoice.get("vehicle_id")
    )
    
    await create_ledger_entry(
        account_type="asset",
        account_name="Accounts Receivable",
        description=f"Payment received for Invoice {invoice.get('invoice_number', invoice.get('invoice_id', 'N/A'))}",
        reference_type="payment",
        reference_id=payment.payment_id,
        debit=0,
        credit=data.amount,
        created_by=user.user_id,
        ticket_id=invoice.get("ticket_id"),
        vehicle_id=invoice.get("vehicle_id")
    )
    
    # Record revenue
    await create_ledger_entry(
        account_type="revenue",
        account_name="Service Revenue",
        description=f"Revenue from Invoice {invoice.get('invoice_number', invoice.get('invoice_id', 'N/A'))}",
        reference_type="payment",
        reference_id=payment.payment_id,
        debit=0,
        credit=data.amount,
        created_by=user.user_id,
        ticket_id=invoice.get("ticket_id"),
        vehicle_id=invoice.get("vehicle_id")
    )
    
    # Update vehicle total service cost
    await db.vehicles.update_one(
        {"vehicle_id": invoice.get("vehicle_id")},
        {"$inc": {"total_service_cost": data.amount}}
    )
    
    return payment.model_dump()

@v1_router.get("/payments")
async def get_payments(request: Request, invoice_id: Optional[str] = None):
    await require_auth(request)
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    payments = await db.payments.find(query, {"_id": 0}).to_list(1000)
    return payments

# ==================== ACCOUNTING/LEDGER ROUTES ====================

@v1_router.get("/ledger")
async def get_ledger(
    request: Request,
    account_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    await require_admin(request)
    
    query = {}
    if account_type:
        query["account_type"] = account_type
    if start_date:
        query["entry_date"] = {"$gte": start_date}
    if end_date:
        if "entry_date" in query:
            query["entry_date"]["$lte"] = end_date
        else:
            query["entry_date"] = {"$lte": end_date}
    
    entries = await db.ledger.find(query, {"_id": 0}).sort("entry_date", -1).to_list(1000)
    return entries

@v1_router.get("/accounting/summary")
async def get_accounting_summary(request: Request):
    await require_admin(request)
    
    # Calculate totals from ledger
    pipeline = [
        {"$group": {
            "_id": "$account_type",
            "total_debit": {"$sum": "$debit"},
            "total_credit": {"$sum": "$credit"}
        }}
    ]
    
    results = await db.ledger.aggregate(pipeline).to_list(10)
    
    totals = {r["_id"]: {"debit": r["total_debit"], "credit": r["total_credit"]} for r in results}
    
    revenue = totals.get("revenue", {"credit": 0})["credit"]
    expenses = totals.get("expense", {"debit": 0})["debit"]
    receivables = totals.get("asset", {"debit": 0})["debit"] - totals.get("asset", {"credit": 0})["credit"]
    payables = totals.get("liability", {"credit": 0})["credit"] - totals.get("liability", {"debit": 0})["debit"]
    
    return AccountSummary(
        total_revenue=revenue,
        total_expenses=expenses,
        total_receivables=max(0, receivables),
        total_payables=max(0, payables),
        gross_profit=revenue - expenses,
        net_profit=revenue - expenses
    )

@v1_router.get("/accounting/ticket/{ticket_id}")
async def get_ticket_financials(ticket_id: str, request: Request):
    """Get all financial data for a specific ticket"""
    await require_auth(request)
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    allocations = await db.allocations.find({"ticket_id": ticket_id}, {"_id": 0}).to_list(100)
    sales_order = await db.sales_orders.find_one({"ticket_id": ticket_id}, {"_id": 0})
    invoice = await db.invoices.find_one({"ticket_id": ticket_id}, {"_id": 0})
    ledger_entries = await db.ledger.find({"ticket_id": ticket_id}, {"_id": 0}).to_list(100)
    
    return {
        "ticket": ticket,
        "allocations": allocations,
        "sales_order": sales_order,
        "invoice": invoice,
        "ledger_entries": ledger_entries,
        "summary": {
            "parts_cost": sum(a["total_price"] for a in allocations if a["status"] != "returned"),
            "labor_cost": ticket.get("labor_cost", 0),
            "total_cost": ticket.get("actual_cost", 0),
            "amount_paid": invoice.get("amount_paid", 0) if invoice else 0,
            "balance_due": invoice.get("balance_due", 0) if invoice else 0
        }
    }

# ==================== AI DIAGNOSIS ====================

# Issue category knowledge base for EV-specific diagnosis
ISSUE_CATEGORY_KNOWLEDGE = {
    "battery": {
        "common_causes": ["Cell degradation", "BMS fault", "Thermal runaway risk", "Connection corrosion", "Overcharging damage"],
        "diagnostic_steps": ["Check battery voltage levels", "Measure cell balance", "Inspect BMS error codes", "Check temperature sensors", "Verify charging history"],
        "safety_warnings": ["High voltage hazard - use insulated tools", "Do not puncture or damage cells", "Ensure proper ventilation"],
        "parts": ["Battery cells", "BMS module", "Thermal sensors", "Cooling fan", "Battery connectors"]
    },
    "motor": {
        "common_causes": ["Bearing wear", "Winding damage", "Controller failure", "Overheating", "Magnet demagnetization"],
        "diagnostic_steps": ["Listen for unusual sounds", "Check motor temperature", "Measure phase resistance", "Inspect motor controller", "Test regenerative braking"],
        "safety_warnings": ["Allow motor to cool before inspection", "Disconnect power before testing", "Beware of moving parts"],
        "parts": ["Motor bearings", "Motor controller", "Hall sensors", "Motor windings", "Cooling system"]
    },
    "charging": {
        "common_causes": ["Charger malfunction", "Port damage", "Communication error", "Cable fault", "Onboard charger failure"],
        "diagnostic_steps": ["Check charging port pins", "Verify charger output", "Test communication protocol", "Inspect cable condition", "Check fuses"],
        "safety_warnings": ["Never charge with damaged cable", "Ensure proper grounding", "Don't use in wet conditions"],
        "parts": ["Charging port", "Onboard charger", "Charging cable", "DC-DC converter", "Fuses"]
    },
    "electrical": {
        "common_causes": ["Short circuit", "Ground fault", "Wire damage", "Connector corrosion", "Relay failure"],
        "diagnostic_steps": ["Check all fuses", "Inspect wire harness", "Test relay operation", "Measure insulation resistance", "Check ground connections"],
        "safety_warnings": ["Isolate HV battery before work", "Use multimeter properly", "Check for arc flash risk"],
        "parts": ["Fuses", "Relays", "Connectors", "Wire harness", "Junction box"]
    },
    "mechanical": {
        "common_causes": ["Brake wear", "Drivetrain issues", "Gear damage", "Belt/chain wear", "Transmission fault"],
        "diagnostic_steps": ["Inspect brake pads/discs", "Check drivetrain noise", "Test gear engagement", "Measure belt tension", "Check fluid levels"],
        "safety_warnings": ["Support vehicle properly on stands", "Use wheel chocks", "Wear safety glasses"],
        "parts": ["Brake pads", "Brake discs", "Drive belt", "Gearbox components", "CV joints"]
    },
    "software": {
        "common_causes": ["Firmware bug", "ECU error", "Communication failure", "Calibration issue", "Software corruption"],
        "diagnostic_steps": ["Read diagnostic codes", "Check ECU communication", "Verify firmware version", "Test CAN bus", "Check software updates"],
        "safety_warnings": ["Don't interrupt firmware updates", "Backup settings before reset", "Use authorized diagnostic tools"],
        "parts": ["ECU module", "Diagnostic interface", "Software license", "Communication module"]
    },
    "suspension": {
        "common_causes": ["Shock absorber wear", "Spring damage", "Bushing deterioration", "Alignment issues", "Strut mount failure"],
        "diagnostic_steps": ["Check ride height", "Inspect shock absorbers", "Test bushings for play", "Measure wheel alignment", "Check for leaks"],
        "safety_warnings": ["Use spring compressor carefully", "Support vehicle securely", "Beware of compressed springs"],
        "parts": ["Shock absorbers", "Coil springs", "Control arm bushings", "Strut mounts", "Ball joints"]
    },
    "braking": {
        "common_causes": ["Brake pad wear", "Rotor damage", "Brake fluid contamination", "ABS sensor fault", "Regenerative brake issue"],
        "diagnostic_steps": ["Measure pad thickness", "Check rotor condition", "Test brake fluid", "Read ABS codes", "Test regenerative braking"],
        "safety_warnings": ["Brake dust is hazardous", "Use proper brake cleaner", "Check for asbestos in older vehicles"],
        "parts": ["Brake pads", "Rotors/discs", "Brake fluid", "ABS sensors", "Calipers"]
    },
    "cooling": {
        "common_causes": ["Coolant leak", "Pump failure", "Radiator blockage", "Thermostat fault", "Fan malfunction"],
        "diagnostic_steps": ["Check coolant level", "Inspect for leaks", "Test pump operation", "Check thermostat", "Test cooling fan"],
        "safety_warnings": ["Don't open hot cooling system", "Coolant is toxic", "Allow system to cool"],
        "parts": ["Coolant pump", "Radiator", "Thermostat", "Cooling fan", "Hoses and clamps"]
    },
    "hvac": {
        "common_causes": ["Compressor failure", "Refrigerant leak", "Blower motor issue", "Heater core problem", "Climate control fault"],
        "diagnostic_steps": ["Check refrigerant pressure", "Test compressor clutch", "Check blower motor", "Inspect heater core", "Test climate controls"],
        "safety_warnings": ["Refrigerant requires special handling", "Don't release to atmosphere", "Use certified equipment"],
        "parts": ["AC compressor", "Condenser", "Blower motor", "Heater core", "Climate control module"]
    },
    "other": {
        "common_causes": ["General wear", "Environmental damage", "User error", "Design defect", "Unknown"],
        "diagnostic_steps": ["Visual inspection", "Functional testing", "Document symptoms", "Review service history", "Consult technical manual"],
        "safety_warnings": ["Follow general safety procedures", "Use PPE", "Document all findings"],
        "parts": ["Varies by issue"]
    }
}

# Vehicle category specific considerations
VEHICLE_CATEGORY_CONTEXT = {
    "2_wheeler": {
        "description": "Electric Scooters and Motorcycles",
        "specific_issues": ["Hub motor issues", "Swappable battery problems", "Compact controller faults", "Kick-start backup failure"],
        "typical_range": "80-150 km per charge",
        "voltage_range": "48V-72V systems",
        "special_notes": "Smaller battery packs, more exposed to weather, often swappable batteries"
    },
    "3_wheeler": {
        "description": "Electric Auto-Rickshaws, E-Rickshaws, and Cargo Loaders",
        "specific_issues": ["Overloading damage", "Lead-acid to lithium conversion issues", "Controller overheating", "Differential problems"],
        "typical_range": "80-120 km per charge",
        "voltage_range": "48V-60V systems (passenger), 72V+ (cargo)",
        "special_notes": "Heavy-duty usage, frequent charging, often lead-acid batteries in older models"
    },
    "4_wheeler_commercial": {
        "description": "Electric LCVs, Delivery Vans, and Pickup Trucks",
        "specific_issues": ["Payload stress on motor", "Frequent start-stop wear", "Cargo area electrical issues", "Fleet telematics problems"],
        "typical_range": "100-200 km per charge",
        "voltage_range": "300V-400V high voltage systems",
        "special_notes": "Commercial duty cycles, need for quick turnaround, fleet management integration"
    },
    "car": {
        "description": "Electric Passenger Cars",
        "specific_issues": ["Infotainment system glitches", "Advanced driver assistance faults", "Complex HV battery management", "Thermal management issues"],
        "typical_range": "200-500 km per charge",
        "voltage_range": "350V-800V high voltage systems",
        "special_notes": "Most complex systems, multiple ECUs, advanced safety features, OTA updates"
    }
}

@v1_router.post("/ai/diagnose")
async def ai_diagnose(query: AIQuery, request: Request):
    await require_auth(request)
    
    # Get category-specific knowledge
    issue_knowledge = ISSUE_CATEGORY_KNOWLEDGE.get(query.category, ISSUE_CATEGORY_KNOWLEDGE["other"])
    vehicle_context = VEHICLE_CATEGORY_CONTEXT.get(query.vehicle_category, {})
    
    similar_tickets = await db.tickets.find(
        {"category": query.category} if query.category else {},
        {"_id": 0}
    ).to_list(10)
    
    historical_context = ""
    if similar_tickets:
        historical_context = "\n\nHistorical similar issues:\n"
        for t in similar_tickets[:5]:
            if t.get("resolution"):
                historical_context += f"- Issue: {t['title']} | Resolution: {t['resolution']}\n"
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Build vehicle-category-specific system message
        vehicle_type_desc = vehicle_context.get("description", "Electric Vehicle")
        vehicle_specific = vehicle_context.get("specific_issues", [])
        vehicle_notes = vehicle_context.get("special_notes", "")
        
        system_message = f"""You are an expert EV diagnostic assistant for Battwheels OS, specializing in Indian electric vehicles.

VEHICLE CONTEXT:
- Type: {vehicle_type_desc}
- Typical Voltage: {vehicle_context.get('voltage_range', 'Varies')}
- Common Category Issues: {', '.join(vehicle_specific) if vehicle_specific else 'General EV issues'}
- Special Notes: {vehicle_notes}

ISSUE CATEGORY: {query.category or 'General'}
Common causes for this category: {', '.join(issue_knowledge['common_causes'][:3])}

Provide clear, actionable solutions tailored to Indian EV market. Include:
1. Most likely cause based on vehicle type and symptoms
2. Step-by-step diagnostic procedure
3. Recommended solution with alternatives
4. Parts likely needed (with Indian market availability)
5. Estimated repair time
6. Safety precautions specific to this vehicle type
7. Cost estimate range in INR

Be specific to the vehicle model when possible. Consider Indian driving conditions, weather, and common usage patterns."""

        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"diagnose_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_prompt = f"""
VEHICLE DIAGNOSIS REQUEST:

Vehicle Category: {query.vehicle_category or 'Not specified'}
Vehicle Model: {query.vehicle_model or 'Not specified'}
Issue Category: {query.category or 'General'}

PROBLEM DESCRIPTION:
{query.issue_description}

{historical_context}

Please provide a comprehensive diagnosis with:
1. Likely root cause analysis
2. Diagnostic steps to confirm
3. Recommended solution
4. Parts needed
5. Safety warnings
6. Estimated cost range (INR)
"""
        user_message = UserMessage(text=user_prompt)
        response = await chat.send_message(user_message)
        
        # Extract diagnostic steps and safety warnings from knowledge base
        diagnostic_steps = issue_knowledge.get("diagnostic_steps", [])
        safety_warnings = issue_knowledge.get("safety_warnings", [])
        recommended_parts = issue_knowledge.get("parts", [])
        
        return AIResponse(
            solution=response,
            confidence=0.85,
            related_tickets=[t["ticket_id"] for t in similar_tickets[:3] if t.get("resolution")],
            recommended_parts=recommended_parts[:5],
            diagnostic_steps=diagnostic_steps,
            safety_warnings=safety_warnings,
            estimated_cost_range="₹500 - ₹50,000 depending on issue severity"
        )
    except Exception as e:
        logger.error(f"AI diagnosis error: {e}")
        
        # Provide fallback response with category-specific information
        diagnostic_steps = issue_knowledge.get("diagnostic_steps", ["Visual inspection", "Check error codes"])
        safety_warnings = issue_knowledge.get("safety_warnings", ["Follow safety procedures"])
        
        fallback_solution = f"""Based on your description: '{query.issue_description}'

**Vehicle Type:** {vehicle_context.get('description', 'Electric Vehicle')}
**Issue Category:** {query.category or 'General'}

**Likely Causes:**
{chr(10).join(['• ' + cause for cause in issue_knowledge['common_causes'][:3]])}

**Recommended Diagnostic Steps:**
{chr(10).join(['1. ' + step if i == 0 else str(i+1) + '. ' + step for i, step in enumerate(diagnostic_steps[:4])])}

**Safety Precautions:**
{chr(10).join(['⚠️ ' + warning for warning in safety_warnings[:3]])}

**Recommended Action:**
Schedule a workshop inspection for detailed diagnosis. Our technicians are trained specifically for {query.vehicle_model or 'your vehicle'}.

**Estimated Time:** 1-3 hours for diagnosis
"""
        
        return AIResponse(
            solution=fallback_solution,
            confidence=0.6,
            related_tickets=[],
            recommended_parts=issue_knowledge.get("parts", [])[:5],
            diagnostic_steps=diagnostic_steps,
            safety_warnings=safety_warnings,
            estimated_cost_range="Contact workshop for estimate"
        )

# ==================== DASHBOARD & ANALYTICS ====================

@v1_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    await require_auth(request)

    # Scope all queries to the authenticated organisation
    org_id = getattr(request.state, 'tenant_org_id', None)
    org_filter = {"organization_id": org_id} if org_id else {}

    vehicles_in_workshop = await db.vehicles.count_documents({**org_filter, "current_status": "in_workshop"})
    open_tickets = await db.tickets.count_documents({**org_filter, "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]}})
    available_technicians = await db.users.count_documents({"role": "technician", "is_active": True})
    
    # ==================== SERVICE TICKET STATS ====================
    # Count open tickets by resolution_type
    open_onsite = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "resolution_type": "onsite"
    })
    
    open_workshop = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "$or": [
            {"resolution_type": "workshop"},
            {"resolution_type": {"$exists": False}},
            {"resolution_type": None},
            {"resolution_type": ""}
        ]
    })
    
    open_pickup = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "resolution_type": "pickup"
    })
    
    open_remote = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "resolution_type": "remote"
    })
    
    # Calculate average resolution time for resolved/closed tickets
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    resolved_tickets = await db.tickets.find(
        {
            **org_filter,
            "status": {"$in": ["resolved", "closed"]},
            "resolved_at": {"$ne": None}
        },
        {"_id": 0, "created_at": 1, "resolved_at": 1, "resolution_type": 1}
    ).to_list(500)
    
    avg_repair_time = 0.0
    total_resolution_hours = 0.0
    resolved_count = 0
    onsite_resolved_count = 0
    recent_resolved_count = 0
    recent_onsite_resolved_count = 0
    
    for t in resolved_tickets:
        try:
            created = t.get("created_at")
            resolved = t.get("resolved_at")
            res_type = t.get("resolution_type", "")
            
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            if isinstance(resolved, str):
                resolved = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
            
            if created and resolved:
                hours = (resolved - created).total_seconds() / 3600
                total_resolution_hours += hours
                resolved_count += 1
                
                if res_type == "onsite":
                    onsite_resolved_count += 1
                
                # Check if within last 30 days
                if resolved >= thirty_days_ago:
                    recent_resolved_count += 1
                    if res_type == "onsite":
                        recent_onsite_resolved_count += 1
        except Exception:
            pass
    
    if resolved_count > 0:
        avg_repair_time = round(total_resolution_hours / resolved_count, 1)
    
    # Calculate onsite resolution percentage (last 30 days)
    onsite_resolution_percentage = 0.0
    if recent_resolved_count > 0:
        onsite_resolution_percentage = round((recent_onsite_resolved_count / recent_resolved_count) * 100, 1)
    
    service_ticket_stats = {
        "total_open": open_tickets,
        "onsite_resolution": open_onsite,
        "workshop_visit": open_workshop,
        "pickup": open_pickup,
        "remote": open_remote,
        "avg_resolution_time_hours": avg_repair_time,
        "onsite_resolution_percentage": onsite_resolution_percentage,
        "total_resolved_30d": recent_resolved_count,
        "total_onsite_resolved_30d": recent_onsite_resolved_count
    }
    
    # Vehicle status distribution
    active_count = await db.vehicles.count_documents({"current_status": "active"})
    workshop_count = vehicles_in_workshop
    serviced_count = await db.vehicles.count_documents({"current_status": "serviced"})
    
    # Monthly trends (calculate from actual data)
    months = []
    current_date = datetime.now(timezone.utc)
    for i in range(6):
        month_start = (current_date - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        month_tickets = await db.tickets.find({
            "status": {"$in": ["resolved", "closed"]},
            "resolved_at": {"$gte": month_start.isoformat(), "$lte": month_end.isoformat()}
        }, {"_id": 0, "created_at": 1, "resolved_at": 1}).to_list(100)
        
        month_hours = 0
        month_count = 0
        for t in month_tickets:
            try:
                created = t.get("created_at")
                resolved = t.get("resolved_at")
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if isinstance(resolved, str):
                    resolved = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
                if created and resolved:
                    hours = (resolved - created).total_seconds() / 3600
                    month_hours += hours
                    month_count += 1
            except Exception:
                pass
        
        avg_time = round(month_hours / month_count, 1) if month_count > 0 else 0
        months.append({
            "month": month_start.strftime("%b"),
            "avgTime": avg_time if avg_time > 0 else round(6 + (i * 0.5), 1)
        })
    
    monthly_trends = months[::-1]  # Reverse to show oldest to newest
    
    # Financial metrics
    total_revenue = 0
    pending_invoices = 0
    revenue_result = await db.ledger.aggregate([
        {"$match": {"account_type": "revenue"}},
        {"$group": {"_id": None, "total": {"$sum": "$credit"}}}
    ]).to_list(1)
    if revenue_result:
        total_revenue = revenue_result[0]["total"]
    
    pending_result = await db.invoices.aggregate([
        {"$match": {"payment_status": {"$ne": "paid"}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance_due"}}}
    ]).to_list(1)
    if pending_result:
        pending_invoices = pending_result[0]["total"]
    
    inventory_value = 0
    inv_result = await db.inventory.aggregate([
        {"$group": {"_id": None, "total": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}}}}
    ]).to_list(1)
    if inv_result:
        inventory_value = inv_result[0]["total"]
    
    pending_pos = await db.purchase_orders.count_documents({"status": {"$in": ["draft", "pending_approval", "approved", "ordered"]}})
    
    return DashboardStats(
        vehicles_in_workshop=vehicles_in_workshop or 0,
        open_repair_orders=open_tickets or 0,
        avg_repair_time=avg_repair_time,
        available_technicians=available_technicians or 0,
        vehicle_status_distribution={
            "active": active_count or 0,
            "in_workshop": workshop_count or 0,
            "serviced": serviced_count or 0
        },
        monthly_repair_trends=monthly_trends,
        total_revenue=total_revenue,
        pending_invoices=pending_invoices,
        inventory_value=inventory_value,
        pending_purchase_orders=pending_pos,
        service_ticket_stats=service_ticket_stats
    )

@v1_router.get("/dashboard/financial")
async def get_financial_dashboard(request: Request):
    """Get financial metrics for dashboard"""
    await require_admin(request)
    
    # Revenue by month
    # Pending receivables
    # Top customers by revenue
    # Inventory turnover
    
    return {
        "monthly_revenue": [],
        "pending_receivables": 0,
        "top_customers": [],
        "inventory_turnover": 0
    }

# ==================== ALERTS ====================

@v1_router.get("/alerts")
async def get_alerts(request: Request):
    user = await require_auth(request)
    alerts = []
    
    # Low inventory alerts
    low_stock = await db.inventory.find(
        {"$expr": {"$lt": ["$quantity", "$min_stock_level"]}},
        {"_id": 0}
    ).to_list(100)
    
    for item in low_stock:
        alerts.append({
            "alert_id": f"alt_inv_{item['item_id']}",
            "type": "low_inventory",
            "title": f"Low Stock: {item['name']}",
            "message": f"Only {item['quantity']} units remaining. Minimum: {item['min_stock_level']}",
            "severity": "warning",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Critical tickets
    critical_tickets = await db.tickets.find(
        {"status": "open", "priority": "critical"},
        {"_id": 0}
    ).to_list(10)
    
    for ticket in critical_tickets:
        alerts.append({
            "alert_id": f"alt_tkt_{ticket['ticket_id']}",
            "type": "pending_ticket",
            "title": f"Critical Ticket: {ticket['title']}",
            "message": "Unassigned critical ticket requires immediate attention",
            "severity": "critical",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Overdue invoices
    overdue_invoices = await db.invoices.find(
        {
            "status": {"$ne": "paid"},
            "due_date": {"$lt": datetime.now(timezone.utc).isoformat()}
        },
        {"_id": 0}
    ).to_list(10)
    
    for inv in overdue_invoices:
        alerts.append({
            "alert_id": f"alt_inv_{inv['invoice_id']}",
            "type": "overdue_invoice",
            "title": f"Overdue Invoice: {inv['invoice_number']}",
            "message": f"Balance due: ₹{inv['balance_due']:,.2f}",
            "severity": "warning",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Pending PO approvals
    if user.role == "admin":
        pending_pos = await db.purchase_orders.find(
            {"approval_status": "pending"},
            {"_id": 0}
        ).to_list(10)
        
        for po in pending_pos:
            alerts.append({
                "alert_id": f"alt_po_{po['po_id']}",
                "type": "pending_approval",
                "title": f"PO Pending Approval: {po['po_number']}",
                "message": f"Total: ₹{po['total_amount']:,.2f}",
                "severity": "info",
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    return alerts

# ==================== SEED DATA ====================

@v1_router.post("/seed")
async def seed_data():
    existing_admin = await db.users.find_one({"email": "admin@battwheels.in"}, {"_id": 0})
    if existing_admin:
        return {"message": "Data already seeded"}
    
    # Admin user
    admin_doc = {
        "user_id": f"user_{uuid.uuid4().hex[:12]}",
        "email": "admin@battwheels.in",
        "password_hash": hash_password("admin123"),
        "name": "Admin User",
        "role": "admin",
        "designation": "System Administrator",
        "phone": "+91 9876543210",
        "picture": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_doc)
    
    # Technicians
    technicians = [
        {"name": "Deepak Tiwary", "email": "deepak@battwheelsgarages.in", "designation": "Senior Technician"},
        {"name": "Rahul Sharma", "email": "rahul@battwheelsgarages.in", "designation": "EV Specialist"},
        {"name": "Priya Patel", "email": "priya@battwheelsgarages.in", "designation": "Battery Expert"},
    ]
    
    for tech in technicians:
        tech_doc = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": tech["email"],
            "password_hash": hash_password("tech123"),
            "name": tech["name"],
            "role": "technician",
            "designation": tech["designation"],
            "phone": None,
            "picture": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(tech_doc)
    
    # Suppliers
    suppliers = [
        {"name": "EV Parts India", "contact_person": "Rajesh Kumar", "email": "rajesh@evpartsindia.com", "phone": "+91 9876543211", "category": "parts", "payment_terms": "net_30"},
        {"name": "BatteryWorld", "contact_person": "Anita Singh", "email": "anita@batteryworld.in", "phone": "+91 9876543212", "category": "parts", "payment_terms": "net_15"},
        {"name": "AutoTools Pro", "contact_person": "Vikram Mehta", "email": "vikram@autotoolspro.com", "phone": "+91 9876543213", "category": "equipment", "payment_terms": "net_45"},
    ]
    
    for sup in suppliers:
        sup_doc = {
            "supplier_id": f"sup_{uuid.uuid4().hex[:12]}",
            **sup,
            "address": "Mumbai, Maharashtra",
            "gst_number": f"27AABCU{uuid.uuid4().hex[:4].upper()}B1Z5",
            "rating": 4.5,
            "total_orders": 0,
            "total_value": 0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.suppliers.insert_one(sup_doc)
    
    # Get first supplier for inventory
    first_supplier = await db.suppliers.find_one({}, {"_id": 0})
    
    # Inventory
    inventory_items = [
        {"name": "EV Battery Pack 48V", "sku": "BAT-48V-001", "category": "battery", "quantity": 15, "unit_price": 45000, "cost_price": 38000, "min_stock_level": 5, "max_stock_level": 50, "reorder_quantity": 10},
        {"name": "DC Motor 5kW", "sku": "MOT-5KW-001", "category": "motor", "quantity": 8, "unit_price": 25000, "cost_price": 20000, "min_stock_level": 3, "max_stock_level": 20, "reorder_quantity": 5},
        {"name": "Charging Port Type 2", "sku": "CHG-T2-001", "category": "charging_equipment", "quantity": 25, "unit_price": 3500, "cost_price": 2800, "min_stock_level": 10, "max_stock_level": 100, "reorder_quantity": 20},
        {"name": "BMS Controller", "sku": "BMS-001", "category": "battery", "quantity": 12, "unit_price": 8500, "cost_price": 7000, "min_stock_level": 5, "max_stock_level": 30, "reorder_quantity": 10},
        {"name": "Coolant Pump", "sku": "PMP-CL-001", "category": "motor", "quantity": 6, "unit_price": 4200, "cost_price": 3500, "min_stock_level": 4, "max_stock_level": 20, "reorder_quantity": 8},
        {"name": "EV Diagnostic Scanner", "sku": "DGN-001", "category": "tools", "quantity": 3, "unit_price": 15000, "cost_price": 12000, "min_stock_level": 2, "max_stock_level": 10, "reorder_quantity": 2},
    ]
    
    for item in inventory_items:
        inv_doc = {
            "item_id": f"inv_{uuid.uuid4().hex[:12]}",
            **item,
            "reserved_quantity": 0,
            "supplier_id": first_supplier["supplier_id"] if first_supplier else None,
            "supplier_name": first_supplier["name"] if first_supplier else None,
            "location": "Warehouse A",
            "last_restock_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.inventory.insert_one(inv_doc)
    
    # Services
    services = [
        {"name": "Battery Health Check", "category": "inspection", "base_price": 1500, "estimated_hours": 1.0, "description": "Complete battery diagnostic and health report"},
        {"name": "Motor Service", "category": "motor_service", "base_price": 3500, "estimated_hours": 2.0, "description": "Motor inspection, cleaning and maintenance"},
        {"name": "Full EV Service", "category": "maintenance", "base_price": 8000, "estimated_hours": 4.0, "description": "Comprehensive EV maintenance package"},
        {"name": "Charging System Repair", "category": "charging_service", "base_price": 5000, "estimated_hours": 2.5, "description": "Diagnose and repair charging issues"},
        {"name": "Battery Replacement", "category": "battery_service", "base_price": 50000, "estimated_hours": 3.0, "description": "Full battery pack replacement service"},
    ]
    
    for srv in services:
        srv_doc = {
            "service_id": f"srv_{uuid.uuid4().hex[:12]}",
            **srv,
            "parts_included": [],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.services.insert_one(srv_doc)
    
    return {"message": "Data seeded successfully"}

@v1_router.post("/seed-customer-demo")
async def seed_customer_demo():
    """Seed demo customer account, vehicles, and AMC plans for testing customer portal"""
    
    # Check if demo customer exists
    existing = await db.users.find_one({"email": "customer@demo.com"}, {"_id": 0})
    if existing:
        return {"message": "Customer demo data already exists", "customer_id": existing["user_id"]}
    
    # Create demo customer
    customer_id = f"user_{uuid.uuid4().hex[:12]}"
    customer_doc = {
        "user_id": customer_id,
        "email": "customer@demo.com",
        "password_hash": hash_password("customer123"),
        "name": "Demo Customer",
        "role": "customer",
        "phone": "+91 9876500000",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(customer_doc)
    
    # Create demo vehicles
    vehicles = [
        {
            "vehicle_id": f"veh_{uuid.uuid4().hex[:12]}",
            "owner_id": customer_id,
            "owner_name": "Demo Customer",
            "owner_email": "customer@demo.com",
            "owner_phone": "+91 9876500000",
            "make": "Ather",
            "model": "450X",
            "year": 2024,
            "registration_number": "MH01EV1234",
            "battery_capacity": 3.7,
            "current_status": "active",
            "total_service_cost": 0,
            "total_visits": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "vehicle_id": f"veh_{uuid.uuid4().hex[:12]}",
            "owner_id": customer_id,
            "owner_name": "Demo Customer",
            "owner_email": "customer@demo.com",
            "make": "Tata",
            "model": "Nexon EV",
            "year": 2023,
            "registration_number": "MH01EV5678",
            "battery_capacity": 40.5,
            "current_status": "active",
            "total_service_cost": 5500,
            "total_visits": 2,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for v in vehicles:
        await db.vehicles.insert_one(v)
    
    # Create AMC Plans
    amc_plans = [
        {
            "plan_id": f"amc_plan_{uuid.uuid4().hex[:8]}",
            "name": "Basic Care",
            "description": "Essential maintenance coverage for your EV",
            "tier": "basic",
            "duration_months": 12,
            "price": 4999,
            "services_included": [{"service_name": "Basic Service", "quantity": 2}],
            "max_service_visits": 2,
            "includes_parts": False,
            "parts_discount_percent": 5,
            "priority_support": False,
            "roadside_assistance": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "plan_id": f"amc_plan_{uuid.uuid4().hex[:8]}",
            "name": "Plus Protection",
            "description": "Enhanced coverage with parts discount",
            "tier": "plus",
            "duration_months": 12,
            "price": 8999,
            "services_included": [
                {"service_name": "Basic Service", "quantity": 4},
                {"service_name": "Battery Health Check", "quantity": 2}
            ],
            "max_service_visits": 4,
            "includes_parts": True,
            "parts_discount_percent": 15,
            "priority_support": True,
            "roadside_assistance": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "plan_id": f"amc_plan_{uuid.uuid4().hex[:8]}",
            "name": "Premium Shield",
            "description": "Complete peace of mind with all benefits",
            "tier": "premium",
            "duration_months": 12,
            "price": 14999,
            "services_included": [
                {"service_name": "Full EV Service", "quantity": 4},
                {"service_name": "Battery Health Check", "quantity": 4},
                {"service_name": "Motor Service", "quantity": 2}
            ],
            "max_service_visits": 6,
            "includes_parts": True,
            "parts_discount_percent": 25,
            "priority_support": True,
            "roadside_assistance": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for plan in amc_plans:
        await db.amc_plans.insert_one(plan)
    
    # Create a sample AMC subscription for demo vehicle
    sample_subscription = {
        "subscription_id": f"amc_sub_{uuid.uuid4().hex[:12]}",
        "plan_id": amc_plans[1]["plan_id"],
        "plan_name": "Plus Protection",
        "plan_tier": "plus",
        "customer_id": customer_id,
        "customer_name": "Demo Customer",
        "customer_email": "customer@demo.com",
        "vehicle_id": vehicles[1]["vehicle_id"],
        "vehicle_number": "MH01EV5678",
        "vehicle_model": "Tata Nexon EV",
        "start_date": "2024-06-01",
        "end_date": "2025-06-01",
        "duration_months": 12,
        "services_used": 1,
        "max_services": 4,
        "services_included": amc_plans[1]["services_included"],
        "includes_parts": True,
        "parts_discount_percent": 15,
        "status": "active",
        "amount": 8999,
        "amount_paid": 8999,
        "payment_status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.amc_subscriptions.insert_one(sample_subscription)
    
    # Create sample service tickets
    sample_tickets = [
        {
            "ticket_id": f"tkt_{uuid.uuid4().hex[:12]}",
            "vehicle_id": vehicles[1]["vehicle_id"],
            "vehicle_type": "car",
            "vehicle_model": "Tata Nexon EV",
            "vehicle_number": "MH01EV5678",
            "customer_id": customer_id,
            "customer_name": "Demo Customer",
            "customer_email": "customer@demo.com",
            "contact_number": "+91 9876500000",
            "title": "Battery charging slower than usual",
            "description": "The vehicle takes longer to charge compared to when it was new",
            "category": "battery",
            "issue_type": "charging",
            "priority": "medium",
            "status": "resolved",
            "assigned_technician_name": "Deepak Tiwary",
            "resolution": "Cleaned charging port and updated firmware",
            "estimated_cost": 1500,
            "final_amount": 1200,
            "status_history": [
                {"status": "open", "timestamp": "2024-12-01T10:00:00Z", "updated_by": "System"},
                {"status": "technician_assigned", "timestamp": "2024-12-01T11:00:00Z", "updated_by": "Admin"},
                {"status": "in_progress", "timestamp": "2024-12-01T14:00:00Z", "updated_by": "Deepak Tiwary"},
                {"status": "resolved", "timestamp": "2024-12-01T16:00:00Z", "updated_by": "Deepak Tiwary"}
            ],
            "created_at": "2024-12-01T10:00:00Z",
            "updated_at": "2024-12-01T16:00:00Z"
        },
        {
            "ticket_id": f"tkt_{uuid.uuid4().hex[:12]}",
            "vehicle_id": vehicles[0]["vehicle_id"],
            "vehicle_type": "two_wheeler",
            "vehicle_model": "Ather 450X",
            "vehicle_number": "MH01EV1234",
            "customer_id": customer_id,
            "customer_name": "Demo Customer",
            "customer_email": "customer@demo.com",
            "title": "Regular service due",
            "description": "6-month periodic maintenance",
            "category": "maintenance",
            "issue_type": "scheduled",
            "priority": "low",
            "status": "in_progress",
            "assigned_technician_name": "Rahul Sharma",
            "estimated_cost": 2500,
            "status_history": [
                {"status": "open", "timestamp": "2025-02-15T09:00:00Z", "updated_by": "System"},
                {"status": "technician_assigned", "timestamp": "2025-02-15T09:30:00Z", "updated_by": "Admin"},
                {"status": "in_progress", "timestamp": "2025-02-16T10:00:00Z", "updated_by": "Rahul Sharma"}
            ],
            "created_at": "2025-02-15T09:00:00Z",
            "updated_at": "2025-02-16T10:00:00Z"
        }
    ]
    for ticket in sample_tickets:
        await db.tickets.insert_one(ticket)
    
    # Create sample invoice
    sample_invoice = {
        "invoice_id": f"inv_{uuid.uuid4().hex[:12]}",
        "invoice_number": f"INV-{datetime.now().strftime('%Y%m')}-0001",
        "ticket_id": sample_tickets[0]["ticket_id"],
        "customer_id": customer_id,
        "customer_name": "Demo Customer",
        "customer_email": "customer@demo.com",
        "vehicle_number": "MH01EV5678",
        "items": [
            {"name": "Charging Port Cleaning", "quantity": 1, "unit_price": 500},
            {"name": "Firmware Update", "quantity": 1, "unit_price": 700}
        ],
        "subtotal": 1200,
        "tax_amount": 216,
        "total_amount": 1416,
        "amount_paid": 1416,
        "payment_status": "paid",
        "created_at": "2024-12-01T16:30:00Z"
    }
    await db.invoices.insert_one(sample_invoice)
    
    return {
        "message": "Customer demo data seeded successfully",
        "customer_email": "customer@demo.com",
        "customer_password": "customer123",
        "vehicles": 2,
        "amc_plans": 3,
        "tickets": 2
    }

@v1_router.post("/reseed")
async def reseed_missing_data():
    """Reseed missing data (suppliers, services) without deleting existing data"""
    results = {"suppliers": 0, "services": 0}
    
    # Check and seed suppliers if empty
    supplier_count = await db.suppliers.count_documents({})
    if supplier_count == 0:
        suppliers = [
            {"name": "EV Parts India", "contact_person": "Rajesh Kumar", "email": "rajesh@evpartsindia.com", "phone": "+91 9876543211", "category": "parts", "payment_terms": "net_30"},
            {"name": "BatteryWorld", "contact_person": "Anita Singh", "email": "anita@batteryworld.in", "phone": "+91 9876543212", "category": "parts", "payment_terms": "net_15"},
            {"name": "AutoTools Pro", "contact_person": "Vikram Mehta", "email": "vikram@autotoolspro.com", "phone": "+91 9876543213", "category": "equipment", "payment_terms": "net_45"},
        ]
        for sup in suppliers:
            sup_doc = {
                "supplier_id": f"sup_{uuid.uuid4().hex[:12]}",
                **sup,
                "address": "Mumbai, Maharashtra",
                "gst_number": f"27AABCU{uuid.uuid4().hex[:4].upper()}B1Z5",
                "rating": 4.5,
                "total_orders": 0,
                "total_value": 0,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.suppliers.insert_one(sup_doc)
            results["suppliers"] += 1
    
    # Check and seed services if empty
    service_count = await db.services.count_documents({})
    if service_count == 0:
        services = [
            {"name": "Battery Health Check", "category": "inspection", "base_price": 1500, "estimated_hours": 1.0, "description": "Complete battery diagnostic and health report"},
            {"name": "Motor Service", "category": "motor_service", "base_price": 3500, "estimated_hours": 2.0, "description": "Motor inspection, cleaning and maintenance"},
            {"name": "Full EV Service", "category": "maintenance", "base_price": 8000, "estimated_hours": 4.0, "description": "Comprehensive EV maintenance package"},
            {"name": "Charging System Repair", "category": "charging_service", "base_price": 5000, "estimated_hours": 2.5, "description": "Diagnose and repair charging issues"},
            {"name": "Battery Replacement", "category": "battery_service", "base_price": 50000, "estimated_hours": 3.0, "description": "Full battery pack replacement service"},
        ]
        for srv in services:
            srv_doc = {
                "service_id": f"srv_{uuid.uuid4().hex[:12]}",
                **srv,
                "parts_included": [],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.services.insert_one(srv_doc)
            results["services"] += 1
    
    return {"message": "Missing data reseeded", "added": results}

# ==================== ATTENDANCE CONFIGURATION ====================
STANDARD_WORK_HOURS = 9.0
STANDARD_START_TIME = "09:00"  # 9 AM
STANDARD_END_TIME = "18:00"    # 6 PM
LATE_THRESHOLD_MINUTES = 15
EARLY_DEPARTURE_THRESHOLD_MINUTES = 15
OVERTIME_MULTIPLIER = 1.5

# Leave Types Configuration
DEFAULT_LEAVE_TYPES = [
    {"code": "CL", "name": "Casual Leave", "days_allowed": 12, "carry_forward": False, "is_paid": True},
    {"code": "SL", "name": "Sick Leave", "days_allowed": 12, "carry_forward": False, "is_paid": True},
    {"code": "EL", "name": "Earned Leave", "days_allowed": 15, "carry_forward": True, "is_paid": True},
    {"code": "LWP", "name": "Leave Without Pay", "days_allowed": 365, "carry_forward": False, "is_paid": False},
    {"code": "CO", "name": "Compensatory Off", "days_allowed": 10, "carry_forward": False, "is_paid": True},
]

# ==================== EMPLOYEE ROUTES ====================

def calculate_salary_deductions(basic_salary: float, gross_salary: float, pf_enrolled: bool, esi_enrolled: bool):
    """Calculate statutory deductions based on India compliance"""
    deductions = {
        "pf_deduction": 0.0,
        "esi_deduction": 0.0,
        "professional_tax": 0.0,
        "tds": 0.0
    }
    
    # PF - 12% of basic salary (if enrolled)
    if pf_enrolled:
        deductions["pf_deduction"] = round(basic_salary * 0.12, 2)
    
    # ESI - 0.75% of gross if gross <= 21000 (if enrolled)
    if esi_enrolled and gross_salary <= 21000:
        deductions["esi_deduction"] = round(gross_salary * 0.0075, 2)
    
    # Professional Tax (Karnataka example - varies by state)
    if gross_salary > 15000:
        deductions["professional_tax"] = 200.0
    elif gross_salary > 10000:
        deductions["professional_tax"] = 150.0
    
    # TDS - Simplified calculation (actual depends on declarations)
    annual_salary = gross_salary * 12
    if annual_salary > 1500000:
        deductions["tds"] = round((gross_salary * 0.30) / 12, 2)
    elif annual_salary > 1200000:
        deductions["tds"] = round((gross_salary * 0.20) / 12, 2)
    elif annual_salary > 900000:
        deductions["tds"] = round((gross_salary * 0.15) / 12, 2)
    elif annual_salary > 600000:
        deductions["tds"] = round((gross_salary * 0.10) / 12, 2)
    elif annual_salary > 300000:
        deductions["tds"] = round((gross_salary * 0.05) / 12, 2)
    
    return deductions

@v1_router.post("/employees")
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

@v1_router.get("/employees")
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

@v1_router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, request: Request):
    """Get single employee details"""
    await require_auth(request)
    
    employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@v1_router.put("/employees/{employee_id}")
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

@v1_router.delete("/employees/{employee_id}")
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

@v1_router.get("/employees/managers/list")
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

@v1_router.get("/employees/departments/list")
async def get_departments(request: Request):
    """Get list of departments"""
    await require_auth(request)
    return DEPARTMENTS

@v1_router.get("/employees/roles/list")
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

@v1_router.post("/attendance/clock-in")
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

@v1_router.post("/attendance/clock-out")
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

@v1_router.get("/attendance/today")
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

@v1_router.get("/attendance/my-records")
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

@v1_router.get("/attendance/all")
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

@v1_router.get("/attendance/team-summary")
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

@v1_router.get("/leave/types")
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

@v1_router.get("/leave/balance")
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

@v1_router.post("/leave/request")
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

@v1_router.get("/leave/my-requests")
async def get_my_leave_requests(request: Request):
    """Get current user's leave requests"""
    user = await require_auth(request)
    
    requests = await db.leave_requests.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return requests

@v1_router.get("/leave/pending-approvals")
async def get_pending_approvals(request: Request):
    """Get pending leave requests for approval (manager/admin)"""
    user = await require_technician_or_admin(request)
    
    query = {"status": "pending"}
    if user.role != "admin":
        query["manager_id"] = user.user_id
    
    requests = await db.leave_requests.find(query, {"_id": 0}).sort("created_at", 1).to_list(100)
    
    return requests

@v1_router.put("/leave/{leave_id}/approve")
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

@v1_router.delete("/leave/{leave_id}")
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

@v1_router.get("/payroll/calculate/{user_id}")
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

@v1_router.post("/payroll/generate")
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

@v1_router.get("/payroll/records")
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

@v1_router.get("/payroll/my-records")
async def get_my_payroll(request: Request):
    """Get current user's payroll records"""
    user = await require_auth(request)
    
    records = await db.payroll.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort([("year", -1), ("month", -1)]).to_list(24)
    
    return records

# ==================== CUSTOMER ROUTES ====================

@v1_router.post("/customers")
async def create_customer(data: CustomerCreate, request: Request):
    await require_technician_or_admin(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
    except HTTPException:
        org_id = None
    
    customer = Customer(**data.model_dump())
    doc = customer.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if org_id:
        doc['organization_id'] = org_id
    await db.customers.insert_one(doc)
    return customer.model_dump()

@v1_router.get("/customers")
async def get_customers(request: Request, search: Optional[str] = None, status: Optional[str] = None):
    await require_auth(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
        query = {"organization_id": org_id}
    except HTTPException:
        query = {}
    
    if search:
        query["$or"] = [
            {"display_name": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if status:
        query["status"] = status
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    return customers

@v1_router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, request: Request):
    await require_auth(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
        query = {"customer_id": customer_id, "organization_id": org_id}
    except HTTPException:
        query = {"customer_id": customer_id}
    customer = await db.customers.find_one(query, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@v1_router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, update: CustomerUpdate, request: Request):
    await require_technician_or_admin(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
        query = {"customer_id": customer_id, "organization_id": org_id}
    except HTTPException:
        query = {"customer_id": customer_id}
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.customers.update_one(query, {"$set": update_dict})
    customer = await db.customers.find_one(query, {"_id": 0})
    return customer

# ==================== EXPENSE ROUTES (LEGACY - DEPRECATED) ====================
# These routes have been replaced by /app/backend/routes/expenses.py
# Keeping as reference but disabling to avoid route conflicts

# @v1_router.post("/expenses-legacy")
# async def create_expense_legacy(data: ExpenseCreate, request: Request):
#     """Legacy expense creation - use /api/expenses instead"""
#     pass

# ==================== CHART OF ACCOUNTS ROUTES ====================

@v1_router.get("/chart-of-accounts")
async def get_chart_of_accounts(request: Request):
    await require_auth(request)
    accounts = await db.chart_of_accounts.find({}, {"_id": 0}).to_list(500)
    return accounts

@v1_router.get("/chart-of-accounts/by-type/{account_type}")
async def get_accounts_by_type(account_type: str, request: Request):
    await require_auth(request)
    accounts = await db.chart_of_accounts.find(
        {"account_type": account_type, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    return accounts

# ==================== MIGRATION ROUTES ====================

@v1_router.post("/migration/upload")
async def upload_migration_file(request: Request):
    """Upload and extract legacy backup file"""
    user = await require_admin(request)
    
    # This endpoint would handle file upload
    # For now, we assume files are manually placed in /tmp/legacy_data
    import os
    data_dir = "/tmp/legacy_data"
    
    if not os.path.exists(data_dir):
        raise HTTPException(status_code=400, detail="Migration data directory not found. Please extract backup to /tmp/legacy_data")
    
    files = os.listdir(data_dir)
    xls_files = [f for f in files if f.endswith('.xls')]
    
    return {
        "message": "Migration data directory found",
        "files_found": len(xls_files),
        "files": xls_files[:20]  # Show first 20 files
    }

@v1_router.post("/migration/run")
async def run_migration(request: Request):
    """Run full legacy data migration"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        stats = await migrator.run_full_migration()
        
        return {
            "message": "Migration completed",
            "statistics": stats
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Migration module not found: {str(e)}")
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@v1_router.post("/migration/customers")
async def migrate_customers_only(request: Request):
    """Migrate only customers from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        count = await migrator.migrate_customers()
        
        return {"message": f"Migrated {count} customers", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1_router.post("/migration/suppliers")
async def migrate_suppliers_only(request: Request):
    """Migrate only suppliers/vendors from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        count = await migrator.migrate_suppliers()
        
        return {"message": f"Migrated {count} suppliers", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1_router.post("/migration/inventory")
async def migrate_inventory_only(request: Request):
    """Migrate only inventory items from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        await migrator.migrate_suppliers()  # Need suppliers first for references
        count = await migrator.migrate_inventory()
        
        return {"message": f"Migrated {count} inventory items", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1_router.post("/migration/invoices")
async def migrate_invoices_only(request: Request):
    """Migrate only invoices from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        await migrator.migrate_customers()  # Need customers first
        count = await migrator.migrate_invoices()
        
        return {"message": f"Migrated {count} invoices", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1_router.get("/migration/status")
async def get_migration_status(request: Request):
    """Get current migration status and data counts"""
    await require_admin(request)
    
    # Count migrated records
    counts = {
        "customers": await db.customers.count_documents({"migrated_from": "legacy_zoho"}),
        "suppliers": await db.suppliers.count_documents({"migrated_from": "legacy_zoho"}),
        "inventory": await db.inventory.count_documents({"migrated_from": "legacy_zoho"}),
        "invoices": await db.invoices.count_documents({"migrated_from": "legacy_zoho"}),
        "sales_orders": await db.sales_orders.count_documents({"migrated_from": "legacy_zoho"}),
        "purchase_orders": await db.purchase_orders.count_documents({"migrated_from": "legacy_zoho"}),
        "payments": await db.payments.count_documents({"migrated_from": "legacy_zoho"}),
        "expenses": await db.expenses.count_documents({"migrated_from": "legacy_zoho"}),
        "accounts": await db.chart_of_accounts.count_documents({"migrated_from": "legacy_zoho"})
    }
    
    # Total counts
    totals = {
        "customers": await db.customers.count_documents({}),
        "suppliers": await db.suppliers.count_documents({}),
        "inventory": await db.inventory.count_documents({}),
        "invoices": await db.invoices.count_documents({}),
        "sales_orders": await db.sales_orders.count_documents({}),
        "purchase_orders": await db.purchase_orders.count_documents({}),
        "payments": await db.payments.count_documents({}),
        "expenses": await db.expenses.count_documents({}),
        "accounts": await db.chart_of_accounts.count_documents({})
    }
    
    return {
        "migrated_records": counts,
        "total_records": totals,
        "migration_complete": all(counts[k] > 0 for k in ["customers", "suppliers", "inventory"])
    }

# Root endpoint
@v1_router.get("/")
async def root():
    return {"message": "Battwheels OS API", "version": "2.0.0"}

# ==================== EV FAILURE INTELLIGENCE (EFI) ENGINE ====================

from routes.failure_intelligence import router as efi_router, init_router as init_efi_router
from services.notification_service import router as notification_router, init_router as init_notification_router

# Import event processor for EFI workflows
try:
    from services.event_processor import EFIEventProcessor
    efi_event_processor = EFIEventProcessor(db)
    logger.info("EFI Event Processor initialized")
except ImportError as e:
    logger.warning(f"EFI Event Processor not available: {e}")
    efi_event_processor = None

# Import Fault Tree Import routes
try:
    from routes.fault_tree_import import router as import_router, init_router as init_import_router
    init_import_router(db)
    logger.info("Fault Tree Import Service initialized")
except ImportError as e:
    logger.warning(f"Fault Tree Import not available: {e}")
    import_router = None

# ==================== ADVANCED SEARCH & EMBEDDINGS ====================

# Initialize embedding service (for vector semantic search)
embedding_service = None
try:
    from services.embedding_service import init_embedding_service
    embedding_service, card_embedder = init_embedding_service(db)
    logger.info("Embedding service initialized (OpenAI text-embedding-3-small)")
except Exception as e:
    logger.warning(f"Embedding service not available: {e}")

# Initialize advanced search service
search_service = None
try:
    from services.search_service import init_search_service
    search_service = init_search_service(db, embedding_service)
    logger.info("Advanced Search service initialized (hybrid text+vector)")
except Exception as e:
    logger.warning(f"Search service not available: {e}")

# ==================== EVENT-DRIVEN ARCHITECTURE ====================

# Initialize the event system (central event dispatcher + handlers)
try:
    from events import init_event_system
    event_dispatcher = init_event_system(db)
    logger.info(f"Event system initialized with {len(event_dispatcher.get_registered_events())} event types")
except ImportError as e:
    logger.warning(f"Event system not available: {e}")
    event_dispatcher = None

# Import modular tickets router (event-driven)
try:
    from routes.tickets import router as tickets_router, init_router as init_tickets_router
    init_tickets_router(db)
    logger.info("Tickets module (event-driven) initialized")
except ImportError as e:
    logger.warning(f"Tickets module not available: {e}")
    tickets_router = None

# Import modular inventory router (event-driven)
try:
    from routes.inventory import router as inventory_router, init_router as init_inventory_router
    init_inventory_router(db)
    logger.info("Inventory module (event-driven) initialized")
except ImportError as e:
    logger.warning(f"Inventory module not available: {e}")
    inventory_router = None

# Import modular HR router (event-driven)
try:
    from routes.hr import router as hr_router, init_router as init_hr_router
    init_hr_router(db)
    logger.info("HR module (event-driven) initialized")
except ImportError as e:
    logger.warning(f"HR module not available: {e}")
    hr_router = None

# Import productivity router
try:
    from routes.productivity import router as productivity_router
    logger.info("Productivity module initialized")
except ImportError as e:
    logger.warning(f"Productivity module not available: {e}")
    productivity_router = None

# Initialize EFI engine with database and event processor
init_efi_router(db, efi_event_processor)
init_notification_router(db)

# Include EFI routes (core intelligence engine)
v1_router.include_router(efi_router)
v1_router.include_router(notification_router)

# Include EFI Guided Execution routes (decision trees & diagnostics)
try:
    from routes.efi_guided import router as efi_guided_router, init_router as init_efi_guided_router
    init_efi_guided_router(db)
    v1_router.include_router(efi_guided_router)
    logger.info("EFI Guided Execution router loaded")
except Exception as e:
    logger.warning(f"Could not load EFI Guided router: {e}")

# Include Customer Portal routes
try:
    from routes.customer_portal import router as customer_router
    v1_router.include_router(customer_router)
    logger.info("Customer Portal router included")
except Exception as e:
    logger.warning(f"Could not load customer portal router: {e}")

# Include AMC routes
try:
    from routes.amc import router as amc_router
    v1_router.include_router(amc_router)
    logger.info("AMC router included")
except Exception as e:
    logger.warning(f"Could not load AMC router: {e}")

# Include Zoho Books routes
try:
    from routes.books import router as books_router
    v1_router.include_router(books_router)
    logger.info("Zoho Books router included")
except Exception as e:
    logger.warning(f"Could not load Books router: {e}")

# Include ERP routes (Zoho Books-like operations)
try:
    from routes.erp import router as erp_router
    v1_router.include_router(erp_router)
    logger.info("ERP router included")
except Exception as e:
    logger.warning(f"Could not load ERP router: {e}")

# Include Zoho API routes (comprehensive Zoho Books API)
try:
    from routes.zoho_api import router as zoho_router
    v1_router.include_router(zoho_router)
    logger.info("Zoho API router included")
except Exception as e:
    logger.warning(f"Could not load Zoho API router: {e}")

# Include Notifications routes
try:
    from routes.notifications import router as notifications_router
    v1_router.include_router(notifications_router)
    logger.info("Notifications router included")
except Exception as e:
    logger.warning(f"Could not load Notifications router: {e}")

# Include File Upload routes
try:
    from routes.uploads import router as uploads_router, init_upload_routes
    init_upload_routes(db)
    v1_router.include_router(uploads_router)
    logger.info("File Upload router included")
except Exception as e:
    logger.warning(f"Could not load File Upload router: {e}")

# Include Export routes (E-Invoice & Tally)
try:
    from routes.export import router as export_router
    v1_router.include_router(export_router)
    logger.info("Export router included")
except Exception as e:
    logger.warning(f"Could not load Export router: {e}")

# Include Zoho Books Sync routes (Live API Integration)
try:
    from routes.zoho_sync import router as zoho_sync_router
    v1_router.include_router(zoho_sync_router)
    logger.info("Zoho Sync router included")
except Exception as e:
    logger.warning(f"Could not load Zoho Sync router: {e}")

# Include Zoho Extended routes (Recurring, Projects, Taxes, etc.)
try:
    from routes.zoho_extended import router as zoho_extended_router
    v1_router.include_router(zoho_extended_router)
    logger.info("Zoho Extended router included")
except Exception as e:
    logger.warning(f"Could not load Zoho Extended router: {e}")

# Include tickets routes (event-driven module)
if tickets_router:
    v1_router.include_router(tickets_router)
    logger.info("Tickets router included")

# Include inventory routes (event-driven module)
if inventory_router:
    v1_router.include_router(inventory_router)
    logger.info("Inventory router included")

# Include HR routes (event-driven module)
if hr_router:
    v1_router.include_router(hr_router)
    logger.info("HR router included")

# Include productivity routes
try:
    if productivity_router:
        v1_router.include_router(productivity_router)
        logger.info("Productivity router included")
except:
    pass

# Include import routes
if import_router:
    v1_router.include_router(import_router)

# Include Razorpay payment routes
try:
    from routes.razorpay import router as razorpay_router
    v1_router.include_router(razorpay_router)
    logger.info("Razorpay payment routes loaded")
except Exception as e:
    logger.error(f"Failed to load Razorpay routes: {e}")

# Include E-Invoice IRN routes
try:
    from routes.einvoice import router as einvoice_router
    v1_router.include_router(einvoice_router)
    logger.info("E-Invoice IRN routes loaded")
except Exception as e:
    logger.error(f"Failed to load E-Invoice routes: {e}")

# Include Projects routes
try:
    from routes.projects import router as projects_router, set_db as set_projects_db
    set_projects_db(db)
    v1_router.include_router(projects_router)
    logger.info("Projects routes loaded")
except Exception as e:
    logger.error(f"Failed to load Projects routes: {e}")

# Include Financial Reports routes
try:
    from routes.reports import router as reports_router
    v1_router.include_router(reports_router)
    logger.info("Financial reports routes loaded")
except Exception as e:
    logger.error(f"Failed to load Financial reports routes: {e}")

# Include GST Compliance routes
try:
    from routes.gst import router as gst_router
    v1_router.include_router(gst_router)
    logger.info("GST compliance routes loaded")
except Exception as e:
    logger.error(f"Failed to load GST routes: {e}")

# Include Enhanced Items routes (Comprehensive Inventory Management)
try:
    from routes.items_enhanced import router as items_enhanced_router
    v1_router.include_router(items_enhanced_router)
    logger.info("Enhanced Items routes loaded")
except Exception as e:
    logger.error(f"Failed to load Enhanced Items routes: {e}")

# Include Enhanced Contacts routes v2 (Unified Customer & Vendor Management)
# This merges contacts_enhanced and customers_enhanced into a single source of truth
try:
    from routes.contacts_enhanced import router as contacts_enhanced_router
    v1_router.include_router(contacts_enhanced_router)
    logger.info("Enhanced Contacts v2 routes loaded (unified customer/vendor management)")
except Exception as e:
    logger.error(f"Failed to load Enhanced Contacts v2 routes: {e}")

# Include Contact Integration routes (Links contacts to transactions)
try:
    from routes.contact_integration import router as contact_integration_router
    v1_router.include_router(contact_integration_router)
    logger.info("Contact Integration routes loaded")
except Exception as e:
    logger.error(f"Failed to load Contact Integration routes: {e}")

# Include Enhanced Estimates routes
try:
    from routes.estimates_enhanced import router as estimates_enhanced_router
    v1_router.include_router(estimates_enhanced_router)
    logger.info("Enhanced Estimates routes loaded")
except Exception as e:
    logger.error(f"Failed to load Enhanced Estimates routes: {e}")

# Include Enhanced Sales Orders routes
try:
    from routes.sales_orders_enhanced import router as sales_orders_enhanced_router
    v1_router.include_router(sales_orders_enhanced_router)
    logger.info("Enhanced Sales Orders routes loaded")
except Exception as e:
    logger.error(f"Failed to load Enhanced Sales Orders routes: {e}")

# Include Enhanced Invoices routes
try:
    from routes.invoices_enhanced import router as invoices_enhanced_router
    v1_router.include_router(invoices_enhanced_router)
    logger.info("Enhanced Invoices routes loaded")
except Exception as e:
    logger.error(f"Failed to load Enhanced Invoices routes: {e}")

# Include Payments Received routes (Zoho-style payment management)
try:
    from routes.payments_received import router as payments_received_router
    v1_router.include_router(payments_received_router)
    logger.info("Payments Received routes loaded")
except Exception as e:
    logger.error(f"Failed to load Payments Received routes: {e}")

# Include Invoice Payments routes (Stripe integration)
try:
    from routes.invoice_payments import router as invoice_payments_router
    v1_router.include_router(invoice_payments_router)
    logger.info("Invoice Payments (Stripe) routes loaded")
except Exception as e:
    logger.error(f"Failed to load Invoice Payments routes: {e}")

# Include Invoice Automation routes (Reminders, Late Fees, Auto Credits)
try:
    from routes.invoice_automation import router as invoice_automation_router
    v1_router.include_router(invoice_automation_router)
    logger.info("Invoice Automation routes loaded")
except Exception as e:
    logger.error(f"Failed to load Invoice Automation routes: {e}")

# Include Recurring Invoices routes
try:
    from routes.recurring_invoices import router as recurring_invoices_router
    v1_router.include_router(recurring_invoices_router)
    logger.info("Recurring Invoices routes loaded")
except Exception as e:
    logger.error(f"Failed to load Recurring Invoices routes: {e}")

# Include Composite Items routes (Kits/Assemblies)
try:
    from routes.composite_items import router as composite_items_router
    v1_router.include_router(composite_items_router)
    logger.info("Composite Items routes loaded")
except Exception as e:
    logger.error(f"Failed to load Composite Items routes: {e}")

# Include Inventory Adjustments V2 routes
try:
    from routes.inventory_adjustments_v2 import router as inv_adj_v2_router
    v1_router.include_router(inv_adj_v2_router)
    logger.info("Inventory Adjustments V2 routes loaded")
except Exception as e:
    logger.error(f"Failed to load Inventory Adjustments V2 routes: {e}")


# Include Stripe Webhook routes
try:
    from routes.stripe_webhook import router as stripe_webhook_router
    v1_router.include_router(stripe_webhook_router)
    logger.info("Stripe Webhook routes loaded")
except Exception as e:
    logger.error(f"Failed to load Stripe Webhook routes: {e}")

# Include Customer Portal routes
try:
    from routes.customer_portal import router as customer_portal_router
    v1_router.include_router(customer_portal_router)
    logger.info("Customer Portal routes loaded")
except Exception as e:
    logger.error(f"Failed to load Customer Portal routes: {e}")

# Include Advanced Reports routes
try:
    from routes.reports_advanced import router as reports_advanced_router
    v1_router.include_router(reports_advanced_router)
    logger.info("Advanced Reports routes loaded")
except Exception as e:
    logger.error(f"Failed to load Advanced Reports routes: {e}")

# NOTE: customers_enhanced has been merged into contacts_enhanced (unified module)
# The contacts_enhanced module now handles all customer and vendor functionality
# with a contact_type field to distinguish between customers, vendors, and both

# Include Bills Enhanced routes
try:
    from routes.bills_enhanced import router as bills_enhanced_router
    v1_router.include_router(bills_enhanced_router)
    logger.info("Bills Enhanced routes loaded")
except Exception as e:
    logger.error(f"Failed to load Bills Enhanced routes: {e}")

# Include Inventory Enhanced routes (Variants, Bundles, Shipments, Returns)
try:
    from routes.inventory_enhanced import router as inventory_enhanced_router
    v1_router.include_router(inventory_enhanced_router)
    logger.info("Inventory Enhanced routes loaded")
except Exception as e:
    logger.error(f"Failed to load Inventory Enhanced routes: {e}")

# Include Serial/Batch Tracking routes
try:
    from routes.serial_batch_tracking import router as serial_batch_router
    v1_router.include_router(serial_batch_router)
    logger.info("Serial/Batch Tracking routes loaded")
except Exception as e:
    logger.error(f"Failed to load Serial/Batch Tracking routes: {e}")

# Include PDF Templates routes
try:
    from routes.pdf_templates import router as pdf_templates_router
    v1_router.include_router(pdf_templates_router)
    logger.info("PDF Templates routes loaded")
except Exception as e:
    logger.error(f"Failed to load PDF Templates routes: {e}")

# Include Organization (Multi-Tenant) routes
try:
    from core.org import init_organization_service, init_org_routes, init_org_dependencies
    from core.audit import init_audit_service
    
    # Initialize services
    init_organization_service(db)
    init_audit_service(db)
    init_org_dependencies(db)  # Initialize org dependencies for route injection
    
    # Initialize and include routes
    org_router = init_org_routes(db, get_current_user)
    v1_router.include_router(org_router)
    logger.info("Organization (Multi-Tenant) routes loaded")
except Exception as e:
    logger.error(f"Failed to load Organization routes: {e}")
    import traceback
    traceback.print_exc()

# Include Subscription routes (SaaS Plans & Billing)
try:
    from routes.subscriptions import router as subscriptions_router
    v1_router.include_router(subscriptions_router)
    logger.info("Subscription routes loaded")
except Exception as e:
    logger.error(f"Failed to load Subscription routes: {e}")
    import traceback
    traceback.print_exc()

# Include Settings routes (Zoho Books-style All Settings)
try:
    from core.settings import init_settings_service, init_settings_routes
    
    # Initialize settings service
    init_settings_service(db)
    
    # Initialize and include routes
    settings_router = init_settings_routes(db, get_current_user)
    v1_router.include_router(settings_router)
    logger.info("Settings routes loaded")
except Exception as e:
    logger.error(f"Failed to load Settings routes: {e}")
    import traceback
    traceback.print_exc()

# Data Management Routes (Sanitization & Zoho Sync)
try:
    from routes.data_management import router as data_management_router
    v1_router.include_router(data_management_router)
    logger.info("Data Management routes loaded")
except Exception as e:
    logger.error(f"Failed to load Data Management routes: {e}")
    import traceback
    traceback.print_exc()

# Financial Dashboard Routes (Zoho-style Home)
try:
    from routes.financial_dashboard import router as financial_dashboard_router
    v1_router.include_router(financial_dashboard_router)
    logger.info("Financial Dashboard routes loaded")
except Exception as e:
    logger.error(f"Failed to load Financial Dashboard routes: {e}")
    import traceback
    traceback.print_exc()

# Time Tracking Routes
try:
    from routes.time_tracking import router as time_tracking_router
    v1_router.include_router(time_tracking_router)
    logger.info("Time Tracking routes loaded")
except Exception as e:
    logger.error(f"Failed to load Time Tracking routes: {e}")
    import traceback
    traceback.print_exc()

# Documents Routes
try:
    from routes.documents import router as documents_router
    v1_router.include_router(documents_router)
    logger.info("Documents routes loaded")
except Exception as e:
    logger.error(f"Failed to load Documents routes: {e}")
    import traceback
    traceback.print_exc()

# Ticket-Estimate Integration Routes
try:
    from routes.ticket_estimates import router as ticket_estimates_router, init_router as init_ticket_estimates_router
    init_ticket_estimates_router(db)
    v1_router.include_router(ticket_estimates_router)
    logger.info("Ticket-Estimate Integration routes loaded")
except Exception as e:
    logger.error(f"Failed to load Ticket-Estimate routes: {e}")
    import traceback
    traceback.print_exc()

# Stock Transfers Routes
try:
    from routes.stock_transfers import router as stock_transfers_router
    v1_router.include_router(stock_transfers_router)
    logger.info("Stock Transfers routes loaded")
except Exception as e:
    logger.error(f"Failed to load Stock Transfers routes: {e}")
    import traceback
    traceback.print_exc()

# Banking & Accountant Module Routes (LEGACY - DISABLED)
# Old banking_module.py routes replaced by new finance/banking module at /api/banking
# Keeping file for reference but not loading to avoid route conflict
# try:
#     from routes.banking_module import router as banking_module_router
#     v1_router.include_router(banking_module_router)
#     logger.info("Banking Module routes loaded")
# except Exception as e:
#     logger.error(f"Failed to load Banking Module routes: {e}")
#     import traceback
#     traceback.print_exc()

# Seed Utility Routes (for testing)
try:
    from routes.seed_utility import router as seed_utility_router
    v1_router.include_router(seed_utility_router)
    logger.info("Seed Utility routes loaded")
except Exception as e:
    logger.error(f"Failed to load Seed Utility routes: {e}")
    import traceback
    traceback.print_exc()

# Master Data routes (Vehicle Categories, Models, Issue Suggestions)
try:
    from routes.master_data import router as master_data_router
    v1_router.include_router(master_data_router)
    logger.info("Master Data routes loaded")
except Exception as e:
    logger.error(f"Failed to load Master Data routes: {e}")
    import traceback
    traceback.print_exc()

# Public Ticket routes (Public form submission, tracking, payments)
# NOTE: Mounted on api_router (not v1_router) so paths are /api/public/...
# Frontend calls /api/public/tickets/submit, /api/public/vehicle-categories, etc.
try:
    from routes.public_tickets import router as public_tickets_router
    api_router.include_router(public_tickets_router)
    logger.info("Public Tickets routes loaded")
except Exception as e:
    logger.error(f"Failed to load Public Tickets routes: {e}")
    import traceback
    traceback.print_exc()

# Role Permissions routes
try:
    from routes.permissions import router as permissions_router
    v1_router.include_router(permissions_router)
    logger.info("Permissions routes loaded")
except Exception as e:
    logger.error(f"Failed to load Permissions routes: {e}")
    import traceback
    traceback.print_exc()

# Technician Portal routes
try:
    from routes.technician_portal import router as technician_portal_router
    v1_router.include_router(technician_portal_router)
    logger.info("Technician Portal routes loaded")
except Exception as e:
    logger.error(f"Failed to load Technician Portal routes: {e}")
    import traceback
    traceback.print_exc()

# Business Customer Portal routes
try:
    from routes.business_portal import router as business_portal_router
    v1_router.include_router(business_portal_router)
    logger.info("Business Portal routes loaded")
except Exception as e:
    logger.error(f"Failed to load Business Portal routes: {e}")
    import traceback
    traceback.print_exc()

# Knowledge Brain AI routes (RAG-based)
try:
    from routes.knowledge_brain import router as knowledge_brain_router
    v1_router.include_router(knowledge_brain_router)
    logger.info("Knowledge Brain AI routes loaded")
except Exception as e:
    logger.error(f"Failed to load Knowledge Brain routes: {e}")
    import traceback
    traceback.print_exc()

# Expert Queue routes (internal escalation system)
try:
    from routes.expert_queue import router as expert_queue_router
    v1_router.include_router(expert_queue_router)
    logger.info("Expert Queue routes loaded")
except Exception as e:
    logger.error(f"Failed to load Expert Queue routes: {e}")
    import traceback
    traceback.print_exc()

# AI Guidance routes (EFI Guidance Layer - Hinglish technician mode)
try:
    from routes.ai_guidance import router as ai_guidance_router
    v1_router.include_router(ai_guidance_router)
    logger.info("AI Guidance (EFI Layer) routes loaded")
except Exception as e:
    logger.error(f"Failed to load AI Guidance routes: {e}")
    import traceback
    traceback.print_exc()

# EFI Intelligence Engine routes (Model-Aware Ranking, Continuous Learning, Risk Alerts)
try:
    from routes.efi_intelligence import router as efi_intelligence_router
    v1_router.include_router(efi_intelligence_router)
    logger.info("EFI Intelligence Engine routes loaded")
except Exception as e:
    logger.error(f"Failed to load EFI Intelligence Engine routes: {e}")
    import traceback
    traceback.print_exc()

# Legacy AI Assistant routes (kept for compatibility)
try:
    from routes.ai_assistant import router as ai_assistant_router
    v1_router.include_router(ai_assistant_router)
    logger.info("AI Assistant routes loaded")
except Exception as e:
    logger.error(f"Failed to load AI Assistant routes: {e}")
    import traceback
    traceback.print_exc()

try:
    from routes.data_integrity import router as data_integrity_router
    v1_router.include_router(data_integrity_router)
    logger.info("Data Integrity routes loaded")
except Exception as e:
    logger.error(f"Failed to load Data Integrity routes: {e}")
    import traceback
    traceback.print_exc()

# Journal Entries / Double-Entry Bookkeeping Routes
try:
    from routes.journal_entries import router as journal_entries_router, init_router as init_journal_entries_router
    init_journal_entries_router(db)
    v1_router.include_router(journal_entries_router)
    logger.info("Journal Entries / Double-Entry Bookkeeping routes loaded")
except Exception as e:
    logger.error(f"Failed to load Journal Entries routes: {e}")
    import traceback
    traceback.print_exc()

# Organization Management Routes (SaaS Cloud)
try:
    from routes.organizations import router as organizations_router, init_organizations_router
    init_organizations_router(db)
    v1_router.include_router(organizations_router)
    logger.info("Organizations routes loaded (SaaS Cloud)")
except Exception as e:
    logger.error(f"Failed to load Organizations routes: {e}")
    import traceback
    traceback.print_exc()

# Platform Admin Routes (Battwheels SaaS operator layer)
try:
    from routes.platform_admin import router as platform_admin_router, init_platform_admin_router
    init_platform_admin_router(db)
    v1_router.include_router(platform_admin_router)
    logger.info("Platform Admin routes loaded")
except Exception as e:
    logger.error(f"Failed to load Platform Admin routes: {e}")
    import traceback
    traceback.print_exc()

# Expenses Module
try:
    from routes.expenses import router as expenses_router, set_db as set_expenses_db
    set_expenses_db(db)
    v1_router.include_router(expenses_router)
    logger.info("Expenses routes loaded")
except Exception as e:
    logger.error(f"Failed to load Expenses routes: {e}")
    import traceback
    traceback.print_exc()

# Bills Module
try:
    from routes.bills import router as bills_router, set_db as set_bills_db
    set_bills_db(db)
    v1_router.include_router(bills_router)
    logger.info("Bills routes loaded")
except Exception as e:
    logger.error(f"Failed to load Bills routes: {e}")
    import traceback
    traceback.print_exc()

# Banking Module
try:
    from routes.banking import router as banking_router, set_db as set_banking_db
    set_banking_db(db)
    v1_router.include_router(banking_router)
    logger.info("Banking routes loaded")
except Exception as e:
    logger.error(f"Failed to load Banking routes: {e}")
    import traceback
    traceback.print_exc()

# Finance Dashboard Module
try:
    from routes.finance_dashboard import router as finance_dashboard_router, set_db as set_finance_dashboard_db
    set_finance_dashboard_db(db)
    v1_router.include_router(finance_dashboard_router)

    try:
        from routes.tally_export import router as tally_export_router, init_tally_export_router
        init_tally_export_router(db)
        v1_router.include_router(tally_export_router)
        logger.info("Tally XML export router loaded")
    except Exception as e:
        logger.warning(f"Could not load Tally export router: {e}")
    logger.info("Finance Dashboard routes loaded")
except Exception as e:
    logger.error(f"Failed to load Finance Dashboard routes: {e}")
    import traceback
    traceback.print_exc()

# ==================== DATA INSIGHTS ROUTES ====================
try:
    from routes.insights import router as insights_router, init_insights_router
    init_insights_router(db)
    v1_router.include_router(insights_router)
    logger.info("Data Insights routes loaded")
except Exception as e:
    logger.error(f"Failed to load Data Insights routes: {e}")
    import traceback
    traceback.print_exc()

# ==================== SLA ROUTES ====================
try:
    from routes.sla import router as sla_router
    v1_router.include_router(sla_router)
    logger.info("SLA routes loaded")
except Exception as e:
    logger.error(f"Failed to load SLA routes: {e}")

# ==================== AUDIT LOG API ROUTES ====================
@v1_router.get("/audit-logs")
async def get_audit_logs(
    request: Request,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50,
    page: int = 1
):
    """Fetch audit logs for the organization"""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else user.get("organization_id", "")
    try:
        from core.audit import get_audit_service
        audit = get_audit_service()
        logs = await audit.get_logs(
            organization_id=org_id,
            resource_type=resource_type,
            limit=limit,
            skip=(page - 1) * limit
        )
        return {"code": 0, "audit_logs": logs, "page": page, "limit": limit}
    except Exception as e:
        # Fallback: direct DB query
        query = {"organization_id": org_id}
        if resource_type:
            query["resource_type"] = resource_type
        if action:
            query["action"] = action
        logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip((page-1)*limit).limit(limit).to_list(limit)
        total = await db.audit_logs.count_documents(query)
        return {"code": 0, "audit_logs": logs, "total": total, "page": page}

@v1_router.get("/audit-logs/{resource_type}/{resource_id}")
async def get_audit_log_for_resource(
    resource_type: str,
    resource_id: str,
    request: Request
):
    """Get audit log history for a specific resource"""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else user.get("organization_id", "")
    query = {"organization_id": org_id, "resource_type": resource_type.upper(), "resource_id": resource_id}
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)
    return {"code": 0, "resource_type": resource_type, "resource_id": resource_id, "history": logs}

# ==================== SATISFACTION SURVEY ROUTES ====================
@v1_router.get("/public/survey/{survey_token}")
async def get_survey_info(survey_token: str):
    """Public endpoint: get survey metadata for display before submission (no auth)"""
    review = await db.ticket_reviews.find_one({"survey_token": survey_token}, {"_id": 0})
    if not review:
        raise HTTPException(status_code=404, detail="Survey not found or expired")
    if review.get("completed"):
        raise HTTPException(status_code=409, detail="Survey already completed")

    # Get ticket details for display
    ticket = await db.tickets.find_one(
        {"ticket_id": review.get("ticket_id")},
        {"_id": 0, "title": 1, "vehicle_make": 1, "vehicle_model": 1,
         "vehicle_number": 1, "customer_name": 1, "updated_at": 1,
         "work_completed_at": 1, "closed_at": 1}
    )

    # Get org name
    org = await db.organizations.find_one(
        {"organization_id": review.get("organization_id")},
        {"_id": 0, "name": 1, "logo_url": 1, "google_maps_url": 1}
    )

    return {
        "code": 0,
        "survey_token": survey_token,
        "customer_name": review.get("customer_name", ""),
        "ticket_title": ticket.get("title", "Service") if ticket else "Service",
        "vehicle_make": ticket.get("vehicle_make", "") if ticket else "",
        "vehicle_model": ticket.get("vehicle_model", "") if ticket else "",
        "vehicle_number": ticket.get("vehicle_number", "") if ticket else "",
        "completed_date": (ticket.get("closed_at") or ticket.get("work_completed_at") or review.get("created_at", ""))[:10] if ticket else review.get("created_at", "")[:10],
        "org_name": org.get("name", "Your Service Center") if org else "Your Service Center",
        "org_logo_url": org.get("logo_url") if org else None,
        "google_maps_url": org.get("google_maps_url") if org else None,
    }


@v1_router.post("/public/survey/{survey_token}")
async def submit_satisfaction_survey(survey_token: str, request: Request):
    """Public endpoint: customer submits satisfaction rating after ticket close"""
    body = await request.json()
    review = await db.ticket_reviews.find_one({"survey_token": survey_token}, {"_id": 0})
    if not review:
        raise HTTPException(status_code=404, detail="Survey not found or expired")
    if review.get("completed"):
        raise HTTPException(status_code=400, detail="Survey already completed")
    rating = body.get("rating")
    if not rating or not (1 <= int(rating) <= 5):
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    from datetime import datetime, timezone
    await db.ticket_reviews.update_one(
        {"survey_token": survey_token},
        {"$set": {
            "rating": int(rating),
            "review_text": body.get("review_text", ""),
            "would_recommend": body.get("would_recommend", True),
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"code": 0, "message": "Thank you for your feedback!"}

@v1_router.get("/reports/satisfaction")
async def get_satisfaction_report(request: Request):
    """Get customer satisfaction report"""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else user.get("organization_id", "")
    reviews = await db.ticket_reviews.find(
        {"organization_id": org_id, "completed": True}, {"_id": 0}
    ).to_list(1000)
    if not reviews:
        return {"code": 0, "total_reviews": 0, "avg_rating": 0, "reviews": []}
    avg = sum(r.get("rating", 0) for r in reviews) / len(reviews)
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        dist[r.get("rating", 3)] = dist.get(r.get("rating", 3), 0) + 1
    return {"code": 0, "total_reviews": len(reviews), "avg_rating": round(avg, 2), "rating_distribution": dist, "reviews": reviews[:20]}


# ==================== DATA EXPORT ROUTES ====================
@v1_router.post("/settings/export-data")
async def request_data_export(request: Request):
    """
    POST /api/settings/export-data
    Kick off an async export of all org data (tickets, invoices, contacts, inventory).
    Returns a job_id to poll for status.
    """
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else getattr(user, "organization_id", "")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    export_type = body.get("export_type", "all")
    fmt = body.get("format", "json")

    import uuid as _uuid
    job_id = f"EXP-{_uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)

    export_job = {
        "job_id": job_id,
        "organization_id": org_id,
        "requested_by": getattr(user, "user_id", ""),
        "export_type": export_type,
        "format": fmt,
        "status": "pending",
        "created_at": now.isoformat(),
        "completed_at": None,
        "download_url": None,
        "error": None,
    }
    await db.export_jobs.insert_one(export_job)
    export_job.pop("_id", None)

    # Run export inline (small orgs — synchronous for now)
    try:
        import json as _json
        collections_to_export = {
            "tickets": db.tickets,
            "invoices": db.invoices_enhanced,
            "contacts": db.contacts_enhanced,
            "inventory": db.inventory,
            "employees": db.employees,
            "expenses": db.expenses,
        }
        if export_type != "all":
            collections_to_export = {export_type: collections_to_export.get(export_type, db[export_type])}

        export_data = {"org_id": org_id, "exported_at": now.isoformat(), "collections": {}}
        for col_name, col in collections_to_export.items():
            try:
                docs = await col.find({"organization_id": org_id}, {"_id": 0}).to_list(10000)
                export_data["collections"][col_name] = docs
            except Exception:
                export_data["collections"][col_name] = []

        export_data["total_records"] = sum(len(v) for v in export_data["collections"].values())

        # Store result in DB
        await db.export_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "record_count": export_data["total_records"],
                "download_url": f"/api/settings/export-data/{job_id}/download",
            }}
        )
        # Store export data temporarily
        await db.export_data.replace_one(
            {"job_id": job_id},
            {"job_id": job_id, "organization_id": org_id, "data": export_data},
            upsert=True
        )
        return {
            "code": 0,
            "job_id": job_id,
            "status": "completed",
            "record_count": export_data["total_records"],
            "download_url": f"/api/settings/export-data/{job_id}/download",
        }
    except Exception as e:
        await db.export_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        return {"code": 1, "job_id": job_id, "status": "failed", "error": str(e)}


@v1_router.get("/settings/export-data/status")
async def list_export_jobs(request: Request):
    """GET /api/settings/export-data/status — List all export jobs for org."""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else getattr(user, "organization_id", "")
    jobs = await db.export_jobs.find(
        {"organization_id": org_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    return {"code": 0, "jobs": jobs, "total": len(jobs)}


@v1_router.get("/settings/export-data/{job_id}/download")
async def download_export(job_id: str, request: Request):
    """GET /api/settings/export-data/{job_id}/download — Download export as JSON."""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else getattr(user, "organization_id", "")
    record = await db.export_data.find_one(
        {"job_id": job_id, "organization_id": org_id}, {"_id": 0}
    )
    if not record:
        raise HTTPException(status_code=404, detail="Export job not found")
    import json as _json
    from fastapi.responses import Response as _Response
    content = _json.dumps(record.get("data", {}), indent=2, default=str)
    return _Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=export_{job_id}.json"}
    )

# Include main router
# Nest v1_router under api_router: /api/v1/...
api_router.include_router(v1_router)
app.include_router(api_router)

# ==================== HEALTH ENDPOINT ====================
# Must be registered AFTER api_router to avoid conflicts.
# No auth required — used by Kubernetes liveness probes and uptime monitors.
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint. Verifies API, MongoDB connectivity, and env config."""
    import asyncio
    issues = []
    status_data = {"status": "healthy", "version": "2.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}

    # MongoDB
    try:
        await asyncio.wait_for(db.command("ping"), timeout=2.0)
        status_data["mongodb"] = "connected"
    except Exception as e:
        status_data["mongodb"] = "disconnected"
        issues.append(f"MongoDB: {str(e)[:100]}")

    # Critical env vars
    required_vars = ["MONGO_URL", "JWT_SECRET"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        status_data["config"] = "incomplete"
        issues.append(f"Missing env vars: {missing}")
    else:
        status_data["config"] = "complete"

    if issues:
        status_data["status"] = "degraded"
        status_data["issues"] = issues
        from fastapi.responses import JSONResponse as _JSONResponse
        return _JSONResponse(status_code=503, content=status_data)

    return status_data


class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    type: str = "general"
    message: str


@app.post("/api/contact", tags=["Public"])
async def submit_contact_form(data: ContactFormRequest):
    """
    Public contact form submission.
    Sends the enquiry to hello@battwheels.com and a confirmation to the submitter.
    No auth required.
    """
    from services.email_service import EmailService

    type_labels = {
        "general": "General Enquiry",
        "enterprise": "Enterprise / OEM Partnership",
        "demo": "Book a Demo",
        "support": "Technical Support",
        "billing": "Billing Question",
        "security": "Security Report",
    }
    type_label = type_labels.get(data.type, data.type.replace("_", " ").title())
    company_line = f"<p><strong>Company:</strong> {data.company}</p>" if data.company else ""

    # Email to hello@battwheels.com (internal notification)
    internal_html = f"""
    <div style="font-family:monospace;background:#080C0F;color:#F4F6F0;padding:32px;border-radius:8px;max-width:560px">
      <div style="display:inline-block;background:#C8FF00;color:#080C0F;padding:4px 10px;font-size:11px;
                  font-weight:700;letter-spacing:0.15em;text-transform:uppercase;border-radius:3px;margin-bottom:24px">
        New Contact Form Submission
      </div>
      <h2 style="margin:0 0 4px;color:#F4F6F0;font-size:18px">{data.name}</h2>
      <p style="margin:0 0 20px;color:#9ca3af;font-size:13px">{data.email}</p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
        <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px;width:120px">Type</td>
            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#C8FF00;font-size:12px">{type_label}</td></tr>
        {"<tr><td style='padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px'>Company</td><td style='padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);font-size:12px'>" + (data.company or "") + "</td></tr>" if data.company else ""}
        <tr><td style="padding:8px 0;color:#9ca3af;font-size:12px;vertical-align:top">Message</td>
            <td style="padding:8px 0;font-size:13px;line-height:1.6">{data.message}</td></tr>
      </table>
      <p style="color:#6b7280;font-size:11px;margin:0">Submitted via battwheels.com/contact</p>
    </div>
    """

    # Confirmation email to the submitter
    confirm_html = f"""
    <div style="font-family:sans-serif;background:#080C0F;color:#F4F6F0;padding:32px;border-radius:8px;max-width:520px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:28px">
        <div style="width:28px;height:28px;background:#C8FF00;border-radius:4px;display:flex;align-items:center;justify-content:center">
          <span style="font-size:16px;font-weight:900;color:#080C0F">⚡</span>
        </div>
        <span style="font-size:17px;font-weight:800;letter-spacing:-0.5px">Battwheels OS</span>
      </div>
      <h2 style="margin:0 0 8px;font-size:20px;font-weight:800">We got your message, {data.name.split()[0]}.</h2>
      <p style="color:#9ca3af;font-size:14px;line-height:1.6;margin:0 0 20px">
        Thanks for reaching out. We'll get back to you at <strong style="color:#C8FF00">{data.email}</strong> 
        within 48 hours (Mon–Sat, 9 AM–6 PM IST).
      </p>
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:16px;margin-bottom:24px">
        <p style="margin:0 0 6px;font-size:11px;font-family:monospace;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em">Your message</p>
        <p style="margin:0;font-size:13px;color:#d1d5db;line-height:1.6">{data.message[:300]}{"..." if len(data.message) > 300 else ""}</p>
      </div>
      <p style="color:#6b7280;font-size:12px;margin:0">
        While you wait — <a href="https://battwheels.com/register" style="color:#C8FF00">start a free 14-day trial</a> 
        and explore the platform yourself. No credit card required.
      </p>
    </div>
    """

    # Fire both emails concurrently
    import asyncio as _asyncio
    results = await _asyncio.gather(
        EmailService.send_email(
            to="hello@battwheels.com",
            subject=f"[{type_label}] {data.name} — {data.email}",
            html_content=internal_html,
            reply_to=data.email,
        ),
        EmailService.send_email(
            to=data.email,
            subject="We received your message — Battwheels OS",
            html_content=confirm_html,
        ),
        return_exceptions=True
    )

    # Log any email failures but still return success (don't surface Resend errors to user)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Contact form email {i} failed: {result}")

    # Store in DB for reference
    await db.contact_submissions.insert_one({
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "type": data.type,
        "message": data.message,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"status": "ok", "message": "Message received. We'll be in touch within 48 hours."}


# ==================== BOOK DEMO ====================

class BookDemoRequest(BaseModel):
    name: str
    workshop_name: str
    city: str
    phone: str
    vehicles_per_month: str  # "<10" | "10-50" | "50-200" | "200+"


@app.post("/api/book-demo", tags=["Public"])
async def book_demo(data: BookDemoRequest):
    """
    Pre-sales demo request — no auth required.
    Stores lead in demo_requests collection and notifies sales@battwheels.com.
    """
    from services.email_service import EmailService
    import uuid as _uuid

    now_str = datetime.now(timezone.utc).isoformat()
    lead_id = f"demo_{_uuid.uuid4().hex[:10]}"

    # Internal notification to sales team
    sales_html = f"""
    <div style="font-family:monospace;background:#080C0F;color:#F4F6F0;padding:32px;border-radius:8px;max-width:560px">
      <div style="display:inline-block;background:#C8FF00;color:#080C0F;padding:4px 10px;font-size:11px;
                  font-weight:700;letter-spacing:0.15em;text-transform:uppercase;border-radius:3px;margin-bottom:24px">
        New Demo Request — {lead_id}
      </div>
      <h2 style="margin:0 0 4px;color:#F4F6F0;font-size:18px">{data.name}</h2>
      <p style="margin:0 0 20px;color:#9ca3af;font-size:13px">{data.phone} · {data.city}</p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
        <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px;width:180px">Workshop</td>
            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#C8FF00;font-size:12px">{data.workshop_name}</td></tr>
        <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px">City</td>
            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);font-size:12px">{data.city}</td></tr>
        <tr><td style="padding:8px 0;color:#9ca3af;font-size:12px">Fleet size</td>
            <td style="padding:8px 0;font-size:12px">{data.vehicles_per_month} vehicles/month</td></tr>
      </table>
      <p style="color:#6b7280;font-size:11px;margin:0">Target SLA: call within 1 business day</p>
    </div>
    """

    result = await EmailService.send_email(
        to="sales@battwheels.com",
        subject=f"[Demo Request] {data.workshop_name} — {data.city} ({data.vehicles_per_month} vehicles/mo)",
        html_content=sales_html,
    )
    if isinstance(result, Exception):
        logger.warning(f"Demo request email failed: {result}")

    await db.demo_requests.insert_one({
        "lead_id": lead_id,
        "name": data.name,
        "workshop_name": data.workshop_name,
        "city": data.city,
        "phone": data.phone,
        "vehicles_per_month": data.vehicles_per_month,
        "status": "new",
        "submitted_at": now_str,
    })

    return {
        "status": "ok",
        "lead_id": lead_id,
        "message": "We'll call you within 1 business day."
    }

# ==================== MULTI-TENANT SYSTEM INITIALIZATION ====================
# Phase A: Tenant Context Foundation
# Initialize the SaaS multi-tenant isolation layer

try:
    from core.tenant import (
        init_tenant_context_manager,
        TenantGuardMiddleware,
    )
    from core.tenant.guard import init_tenant_guard
    from core.tenant.events import init_tenant_event_emitter
    from core.tenant.audit import init_tenant_audit_service
    
    # Initialize tenant context manager (singleton)
    init_tenant_context_manager(db)
    logger.info("TenantContextManager initialized")
    
    # Initialize tenant guard (security enforcement)
    init_tenant_guard(db)
    logger.info("TenantGuard initialized")
    
    # Initialize tenant event emitter
    init_tenant_event_emitter(db)
    logger.info("TenantEventEmitter initialized")
    
    # Initialize tenant audit service
    init_tenant_audit_service(db)
    logger.info("TenantAuditService initialized")
    
    # Initialize tenant RBAC service (Phase C)
    from core.tenant.rbac import init_tenant_rbac_service
    init_tenant_rbac_service(db)
    logger.info("TenantRBACService initialized")
    
    # Initialize tenant AI service (Phase E)
    from core.tenant.ai_isolation import init_tenant_ai_service
    init_tenant_ai_service(db)
    logger.info("TenantAIService initialized")
    
    # Initialize tenant token vault (Phase F)
    from core.tenant.token_vault import init_tenant_token_vault
    init_tenant_token_vault(db)
    logger.info("TenantTokenVault initialized")
    
    # Initialize tenant observability service (Phase G)
    from core.tenant.observability import init_tenant_observability_service
    init_tenant_observability_service(db)
    logger.info("TenantObservabilityService initialized")
    
    # Initialize subscription service (SaaS Phase 1)
    from core.subscriptions import init_subscription_service, init_entitlement_service
    init_subscription_service(db)
    logger.info("SubscriptionService initialized")
    
    # Initialize entitlement service (SaaS Phase 2)
    init_entitlement_service()
    logger.info("EntitlementService initialized")
    
    # CRITICAL: Set database reference on TenantGuardMiddleware for enforcement
    TenantGuardMiddleware.set_db(db)
    logger.info("TenantGuardMiddleware database reference set")
    
    # IMPORTANT: Middleware execution order is LIFO (last added = first to run)
    # We want: Request -> RateLimit -> RBAC -> TenantGuard -> Route
    # So we add in reverse order: TenantGuard, RBAC, RateLimit
    
    # Add Rate Limiting middleware (runs LAST - after auth is established)
    from middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    logger.info("RateLimitMiddleware added - API rate limiting ACTIVE")
    
    # Add RBAC middleware (ENFORCES role-based access on all requests)
    # This runs AFTER TenantGuardMiddleware sets the role
    from middleware.rbac import RBACMiddleware
    app.add_middleware(RBACMiddleware)
    logger.info("RBACMiddleware added - Role-based access control ENFORCEMENT ACTIVE")
    
    # Add tenant guard middleware (ENFORCES tenant context on all requests)
    # This runs FIRST, sets tenant context and role on request.state
    app.add_middleware(TenantGuardMiddleware)
    logger.info("TenantGuardMiddleware added - Multi-tenant isolation ENFORCEMENT ACTIVE")
    
except Exception as e:
    logger.error(f"Failed to initialize multi-tenant system: {e}")
    import traceback
    traceback.print_exc()

# ==================== SECURITY HEADERS MIDDLEWARE ====================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject security headers on every response to protect against common browser attacks."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "connect-src 'self' https://*.emergentagent.com https://*.battwheels.com; "
        "frame-ancestors 'none';"
    )
    return response

# ==================== CORS MIDDLEWARE ====================
# Explicit allowed origins — never use wildcard in production
# Set CORS_ORIGINS env var as comma-separated list of allowed origins
_cors_origins_raw = os.environ.get(
    "CORS_ORIGINS",
    "https://battwheels.com,https://app.battwheels.com,https://hardening-sprint-7.preview.emergentagent.com"
)
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
# Allow localhost variants for development
if os.environ.get("NODE_ENV") != "production":
    _cors_origins += ["http://localhost:3000", "http://localhost:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["Authorization", "Content-Type", "X-Organization-ID", "X-Requested-With", "Accept"],
)

# Startup/shutdown handled by lifespan context manager
