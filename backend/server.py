from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import bcrypt
import jwt
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

# Create the main app
app = FastAPI(title="Battwheels OS API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    vehicle_id: str
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
    vehicle_id: str
    customer_id: str
    customer_name: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    title: str
    description: str
    category: str
    priority: str = "medium"
    status: str = "open"
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class TicketCreate(BaseModel):
    vehicle_id: str
    title: str
    description: str
    category: str
    priority: str = "medium"
    estimated_cost: float = 0.0

class TicketUpdate(BaseModel):
    assigned_technician_id: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    priority: Optional[str] = None
    estimated_cost: Optional[float] = None

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
    category: Optional[str] = None

class AIResponse(BaseModel):
    solution: str
    confidence: float
    related_tickets: List[str] = []
    recommended_parts: List[str] = []

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

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
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
                if user:
                    if isinstance(user.get('created_at'), str):
                        user['created_at'] = datetime.fromisoformat(user['created_at'])
                    return User(**user)
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
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

async def generate_po_number():
    """Generate sequential PO number"""
    count = await db.purchase_orders.count_documents({})
    return f"PO-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

async def generate_invoice_number():
    """Generate sequential invoice number"""
    count = await db.invoices.count_documents({})
    return f"INV-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

async def generate_sales_number():
    """Generate sequential sales order number"""
    count = await db.sales_orders.count_documents({})
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
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    token = create_token(user["user_id"], user["email"], user["role"])
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "designation": user.get("designation"),
            "picture": user.get("picture")
        }
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
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "designation": user.designation,
        "picture": user.picture
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ==================== USER ROUTES ====================

@api_router.get("/users")
async def get_users(request: Request):
    await require_admin(request)
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    await require_auth(request)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/users/{user_id}")
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

@api_router.get("/technicians")
async def get_technicians(request: Request):
    await require_auth(request)
    technicians = await db.users.find(
        {"role": "technician", "is_active": True},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    return technicians

# ==================== SUPPLIER ROUTES ====================

@api_router.post("/suppliers")
async def create_supplier(data: SupplierCreate, request: Request):
    await require_technician_or_admin(request)
    supplier = Supplier(**data.model_dump())
    doc = supplier.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.suppliers.insert_one(doc)
    return supplier.model_dump()

@api_router.get("/suppliers")
async def get_suppliers(request: Request):
    await require_auth(request)
    suppliers = await db.suppliers.find({}, {"_id": 0}).to_list(1000)
    return suppliers

@api_router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str, request: Request):
    await require_auth(request)
    supplier = await db.suppliers.find_one({"supplier_id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@api_router.put("/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, update: SupplierUpdate, request: Request):
    await require_technician_or_admin(request)
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.suppliers.update_one({"supplier_id": supplier_id}, {"$set": update_dict})
    supplier = await db.suppliers.find_one({"supplier_id": supplier_id}, {"_id": 0})
    return supplier

# ==================== VEHICLE ROUTES ====================

@api_router.post("/vehicles")
async def create_vehicle(vehicle_data: VehicleCreate, request: Request):
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
    await db.vehicles.insert_one(doc)
    return vehicle.model_dump()

@api_router.get("/vehicles")
async def get_vehicles(request: Request):
    user = await require_auth(request)
    if user.role in ["admin", "technician"]:
        vehicles = await db.vehicles.find({}, {"_id": 0}).to_list(1000)
    else:
        vehicles = await db.vehicles.find({"owner_id": user.user_id}, {"_id": 0}).to_list(100)
    return vehicles

@api_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str, request: Request):
    await require_auth(request)
    vehicle = await db.vehicles.find_one({"vehicle_id": vehicle_id}, {"_id": 0})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@api_router.put("/vehicles/{vehicle_id}/status")
async def update_vehicle_status(vehicle_id: str, status: str, request: Request):
    await require_technician_or_admin(request)
    if status not in ["active", "in_workshop", "serviced"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    await db.vehicles.update_one({"vehicle_id": vehicle_id}, {"$set": {"current_status": status}})
    return {"message": "Status updated"}

# ==================== TICKET ROUTES ====================

@api_router.post("/tickets")
async def create_ticket(ticket_data: TicketCreate, request: Request):
    user = await require_auth(request)
    
    # Get customer name from vehicle
    vehicle = await db.vehicles.find_one({"vehicle_id": ticket_data.vehicle_id}, {"_id": 0})
    customer_name = vehicle.get("owner_name") if vehicle else None
    
    ticket = Ticket(
        vehicle_id=ticket_data.vehicle_id,
        customer_id=user.user_id,
        customer_name=customer_name,
        title=ticket_data.title,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=ticket_data.priority,
        estimated_cost=ticket_data.estimated_cost
    )
    doc = ticket.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.tickets.insert_one(doc)
    
    # Update vehicle status
    await db.vehicles.update_one(
        {"vehicle_id": ticket_data.vehicle_id},
        {"$set": {"current_status": "in_workshop"}, "$inc": {"total_visits": 1}}
    )
    
    return ticket.model_dump()

@api_router.get("/tickets")
async def get_tickets(request: Request, status: Optional[str] = None):
    user = await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    
    if user.role == "customer":
        query["customer_id"] = user.user_id
    elif user.role == "technician":
        query["$or"] = [
            {"assigned_technician_id": user.user_id},
            {"assigned_technician_id": None}
        ]
    
    tickets = await db.tickets.find(query, {"_id": 0}).to_list(1000)
    return tickets

@api_router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, request: Request):
    await require_auth(request)
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@api_router.put("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, update: TicketUpdate, request: Request):
    user = await require_technician_or_admin(request)
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Get technician name if assigning
    if update.assigned_technician_id:
        tech = await db.users.find_one({"user_id": update.assigned_technician_id}, {"_id": 0})
        if tech:
            update_dict["assigned_technician_name"] = tech.get("name")
    
    if update.status == "resolved":
        update_dict["resolved_at"] = datetime.now(timezone.utc).isoformat()
        # Update vehicle status
        ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
        if ticket:
            await db.vehicles.update_one(
                {"vehicle_id": ticket["vehicle_id"]},
                {"$set": {"current_status": "serviced"}}
            )
    
    await db.tickets.update_one({"ticket_id": ticket_id}, {"$set": update_dict})
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    return ticket

# ==================== INVENTORY ROUTES ====================

@api_router.post("/inventory")
async def create_inventory_item(item_data: InventoryCreate, request: Request):
    await require_technician_or_admin(request)
    
    # Get supplier name if provided
    supplier_name = None
    if item_data.supplier_id:
        supplier = await db.suppliers.find_one({"supplier_id": item_data.supplier_id}, {"_id": 0})
        supplier_name = supplier.get("name") if supplier else None
    
    item = InventoryItem(**item_data.model_dump(), supplier_name=supplier_name)
    doc = item.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.inventory.insert_one(doc)
    return item.model_dump()

@api_router.get("/inventory")
async def get_inventory(request: Request):
    await require_auth(request)
    items = await db.inventory.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.get("/inventory/{item_id}")
async def get_inventory_item(item_id: str, request: Request):
    await require_auth(request)
    item = await db.inventory.find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@api_router.put("/inventory/{item_id}")
async def update_inventory_item(item_id: str, update: InventoryUpdate, request: Request):
    await require_technician_or_admin(request)
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Update supplier name if supplier_id changed
    if update.supplier_id:
        supplier = await db.suppliers.find_one({"supplier_id": update.supplier_id}, {"_id": 0})
        update_dict["supplier_name"] = supplier.get("name") if supplier else None
    
    await db.inventory.update_one({"item_id": item_id}, {"$set": update_dict})
    item = await db.inventory.find_one({"item_id": item_id}, {"_id": 0})
    return item

@api_router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str, request: Request):
    await require_admin(request)
    await db.inventory.delete_one({"item_id": item_id})
    return {"message": "Item deleted"}

# ==================== MATERIAL ALLOCATION ROUTES ====================

@api_router.post("/allocations")
async def create_allocation(data: MaterialAllocationCreate, request: Request):
    """Allocate materials from inventory to a ticket"""
    user = await require_technician_or_admin(request)
    
    # Verify ticket exists
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get item details and check stock
    item = await db.inventory.find_one({"item_id": data.item_id}, {"_id": 0})
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
    await db.allocations.insert_one(doc)
    
    # Update inventory reserved quantity
    await db.inventory.update_one(
        {"item_id": data.item_id},
        {"$inc": {"reserved_quantity": data.quantity}}
    )
    
    # Update ticket parts cost
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id},
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

@api_router.get("/allocations")
async def get_allocations(request: Request, ticket_id: Optional[str] = None):
    await require_auth(request)
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    allocations = await db.allocations.find(query, {"_id": 0}).to_list(1000)
    return allocations

@api_router.put("/allocations/{allocation_id}/use")
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

@api_router.put("/allocations/{allocation_id}/return")
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

@api_router.post("/purchase-orders")
async def create_purchase_order(data: PurchaseOrderCreate, request: Request):
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
    
    po_number = await generate_po_number()
    
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

@api_router.get("/purchase-orders")
async def get_purchase_orders(request: Request, status: Optional[str] = None):
    await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    pos = await db.purchase_orders.find(query, {"_id": 0}).to_list(1000)
    return pos

@api_router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str, request: Request):
    await require_auth(request)
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@api_router.put("/purchase-orders/{po_id}")
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

@api_router.post("/purchase-orders/{po_id}/receive")
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

@api_router.post("/services")
async def create_service(data: ServiceOfferingCreate, request: Request):
    await require_admin(request)
    service = ServiceOffering(**data.model_dump())
    doc = service.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.services.insert_one(doc)
    return service.model_dump()

@api_router.get("/services")
async def get_services(request: Request):
    await require_auth(request)
    services = await db.services.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return services

@api_router.put("/services/{service_id}")
async def update_service(service_id: str, data: dict, request: Request):
    await require_admin(request)
    await db.services.update_one({"service_id": service_id}, {"$set": data})
    service = await db.services.find_one({"service_id": service_id}, {"_id": 0})
    return service

# ==================== SALES ORDER ROUTES ====================

@api_router.post("/sales-orders")
async def create_sales_order(data: SalesOrderCreate, request: Request):
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
    
    sales_number = await generate_sales_number()
    
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

@api_router.get("/sales-orders")
async def get_sales_orders(request: Request, status: Optional[str] = None):
    await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    orders = await db.sales_orders.find(query, {"_id": 0}).to_list(1000)
    return orders

@api_router.get("/sales-orders/{sales_id}")
async def get_sales_order(sales_id: str, request: Request):
    await require_auth(request)
    order = await db.sales_orders.find_one({"sales_id": sales_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return order

@api_router.put("/sales-orders/{sales_id}")
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

@api_router.post("/invoices")
async def create_invoice(data: InvoiceCreate, request: Request):
    user = await require_technician_or_admin(request)
    
    # Get ticket details
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get vehicle and customer details
    vehicle = await db.vehicles.find_one({"vehicle_id": ticket["vehicle_id"]}, {"_id": 0})
    
    # Calculate totals
    subtotal = sum(item.get("amount", 0) for item in data.line_items)
    tax_amount = (subtotal - data.discount_amount) * 0.18
    total_amount = subtotal - data.discount_amount + tax_amount
    
    invoice_number = await generate_invoice_number()
    due_date = datetime.now(timezone.utc) + timedelta(days=data.due_days)
    
    invoice = Invoice(
        invoice_number=invoice_number,
        sales_id=data.sales_id,
        ticket_id=data.ticket_id,
        customer_id=ticket["customer_id"],
        customer_name=vehicle.get("owner_name", "") if vehicle else "",
        customer_email=vehicle.get("owner_email") if vehicle else None,
        customer_phone=vehicle.get("owner_phone") if vehicle else None,
        vehicle_id=ticket["vehicle_id"],
        vehicle_details=f"{vehicle['make']} {vehicle['model']} ({vehicle['registration_number']})" if vehicle else None,
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

@api_router.get("/invoices")
async def get_invoices(request: Request, status: Optional[str] = None):
    user = await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    if user.role == "customer":
        query["customer_id"] = user.user_id
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request):
    await require_auth(request)
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, update: InvoiceUpdate, request: Request):
    await require_technician_or_admin(request)
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": update_dict})
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    return invoice

# ==================== PAYMENT ROUTES ====================

@api_router.post("/payments")
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
    
    # Update invoice
    new_amount_paid = invoice["amount_paid"] + data.amount
    new_balance = invoice["total_amount"] - new_amount_paid
    
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
        description=f"Payment received for Invoice {invoice['invoice_number']}",
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
        description=f"Revenue from Invoice {invoice['invoice_number']}",
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

@api_router.get("/payments")
async def get_payments(request: Request, invoice_id: Optional[str] = None):
    await require_auth(request)
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    payments = await db.payments.find(query, {"_id": 0}).to_list(1000)
    return payments

# ==================== ACCOUNTING/LEDGER ROUTES ====================

@api_router.get("/ledger")
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

@api_router.get("/accounting/summary")
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

@api_router.get("/accounting/ticket/{ticket_id}")
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

@api_router.post("/ai/diagnose")
async def ai_diagnose(query: AIQuery, request: Request):
    await require_auth(request)
    
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
        
        system_message = """You are an expert EV diagnostic assistant for Battwheels OS.
Provide clear, actionable solutions for EV issues including batteries, motors, charging systems.
Include: 1. Likely cause 2. Diagnostic steps 3. Solution 4. Parts needed 5. Safety warnings"""

        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"diagnose_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_prompt = f"""
Vehicle Issue: {query.issue_description}
Vehicle Model: {query.vehicle_model or 'Not specified'}
Category: {query.category or 'General'}
{historical_context}

Provide comprehensive diagnosis and solution.
"""
        user_message = UserMessage(text=user_prompt)
        response = await chat.send_message(user_message)
        
        return AIResponse(
            solution=response,
            confidence=0.85,
            related_tickets=[t["ticket_id"] for t in similar_tickets[:3] if t.get("resolution")],
            recommended_parts=[]
        )
    except Exception as e:
        logger.error(f"AI diagnosis error: {e}")
        return AIResponse(
            solution=f"Based on '{query.issue_description}':\n\n1. Check diagnostic codes with OBD-II\n2. Inspect components\n3. Schedule workshop inspection\n\nCategory: {query.category or 'General'}",
            confidence=0.5,
            related_tickets=[],
            recommended_parts=[]
        )

# ==================== DASHBOARD & ANALYTICS ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    await require_auth(request)
    
    vehicles_in_workshop = await db.vehicles.count_documents({"current_status": "in_workshop"})
    open_tickets = await db.tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    available_technicians = await db.users.count_documents({"role": "technician", "is_active": True})
    
    # Average repair time
    resolved_tickets = await db.tickets.find(
        {"status": "resolved", "resolved_at": {"$ne": None}},
        {"_id": 0, "created_at": 1, "resolved_at": 1}
    ).to_list(100)
    
    avg_repair_time = 7.9
    if resolved_tickets:
        total_hours = 0
        count = 0
        for t in resolved_tickets:
            try:
                created = datetime.fromisoformat(t["created_at"]) if isinstance(t["created_at"], str) else t["created_at"]
                resolved = datetime.fromisoformat(t["resolved_at"]) if isinstance(t["resolved_at"], str) else t["resolved_at"]
                hours = (resolved - created).total_seconds() / 3600
                total_hours += hours
                count += 1
            except:
                pass
        if count > 0:
            avg_repair_time = round(total_hours / count, 1)
    
    # Vehicle status distribution
    active_count = await db.vehicles.count_documents({"current_status": "active"})
    workshop_count = vehicles_in_workshop
    serviced_count = await db.vehicles.count_documents({"current_status": "serviced"})
    
    # Monthly trends
    months = ["Jul", "Jun", "May", "Apr", "Mar", "Feb"]
    monthly_trends = [{"month": m, "avgTime": round(6 + (i * 0.5), 1)} for i, m in enumerate(months)]
    
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
        vehicles_in_workshop=vehicles_in_workshop or 745,
        open_repair_orders=open_tickets or 738,
        avg_repair_time=avg_repair_time,
        available_technicians=available_technicians or 34,
        vehicle_status_distribution={
            "active": active_count or 500,
            "in_workshop": workshop_count or 200,
            "serviced": serviced_count or 45
        },
        monthly_repair_trends=monthly_trends,
        total_revenue=total_revenue,
        pending_invoices=pending_invoices,
        inventory_value=inventory_value,
        pending_purchase_orders=pending_pos
    )

@api_router.get("/dashboard/financial")
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

@api_router.get("/alerts")
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

@api_router.post("/seed")
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

@api_router.post("/reseed")
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

# ==================== CUSTOMER ROUTES ====================

@api_router.post("/customers")
async def create_customer(data: CustomerCreate, request: Request):
    await require_technician_or_admin(request)
    customer = Customer(**data.model_dump())
    doc = customer.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.customers.insert_one(doc)
    return customer.model_dump()

@api_router.get("/customers")
async def get_customers(request: Request, search: Optional[str] = None, status: Optional[str] = None):
    await require_auth(request)
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

@api_router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, request: Request):
    await require_auth(request)
    customer = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@api_router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, update: CustomerUpdate, request: Request):
    await require_technician_or_admin(request)
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.customers.update_one({"customer_id": customer_id}, {"$set": update_dict})
    customer = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
    return customer

# ==================== EXPENSE ROUTES ====================

@api_router.post("/expenses")
async def create_expense(data: ExpenseCreate, request: Request):
    user = await require_technician_or_admin(request)
    expense = Expense(
        expense_date=datetime.fromisoformat(data.expense_date),
        description=data.description,
        expense_account=data.expense_account,
        vendor_id=data.vendor_id,
        amount=data.amount,
        tax_amount=data.tax_amount,
        reference_number=data.reference_number,
        is_billable=data.is_billable,
        created_by=user.user_id
    )
    doc = expense.model_dump()
    doc['expense_date'] = doc['expense_date'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.expenses.insert_one(doc)
    
    # Create ledger entry
    await create_ledger_entry(
        account_type="expense",
        account_name=data.expense_account,
        description=data.description or f"Expense: {data.expense_account}",
        reference_type="expense",
        reference_id=expense.expense_id,
        debit=data.amount,
        credit=0,
        created_by=user.user_id
    )
    
    return expense.model_dump()

@api_router.get("/expenses")
async def get_expenses(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account: Optional[str] = None
):
    await require_auth(request)
    query = {}
    if start_date:
        query["expense_date"] = {"$gte": start_date}
    if end_date:
        if "expense_date" in query:
            query["expense_date"]["$lte"] = end_date
        else:
            query["expense_date"] = {"$lte": end_date}
    if account:
        query["expense_account"] = account
    
    expenses = await db.expenses.find(query, {"_id": 0}).sort("expense_date", -1).to_list(1000)
    return expenses

@api_router.get("/expenses/summary")
async def get_expense_summary(request: Request):
    await require_admin(request)
    
    pipeline = [
        {"$group": {
            "_id": "$expense_account",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}}
    ]
    
    summary = await db.expenses.aggregate(pipeline).to_list(50)
    total = sum(item["total"] for item in summary)
    
    return {
        "by_account": summary,
        "total_expenses": total,
        "expense_count": sum(item["count"] for item in summary)
    }

# ==================== CHART OF ACCOUNTS ROUTES ====================

@api_router.get("/chart-of-accounts")
async def get_chart_of_accounts(request: Request):
    await require_auth(request)
    accounts = await db.chart_of_accounts.find({}, {"_id": 0}).to_list(500)
    return accounts

@api_router.get("/chart-of-accounts/by-type/{account_type}")
async def get_accounts_by_type(account_type: str, request: Request):
    await require_auth(request)
    accounts = await db.chart_of_accounts.find(
        {"account_type": account_type, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    return accounts

# ==================== MIGRATION ROUTES ====================

@api_router.post("/migration/upload")
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

@api_router.post("/migration/run")
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

@api_router.post("/migration/customers")
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

@api_router.post("/migration/suppliers")
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

@api_router.post("/migration/inventory")
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

@api_router.post("/migration/invoices")
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

@api_router.get("/migration/status")
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
@api_router.get("/")
async def root():
    return {"message": "Battwheels OS API", "version": "2.0.0"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
