"""
Battwheels OS - Pydantic Models (extracted from server.py)
All request/response models for the API
"""
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

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
