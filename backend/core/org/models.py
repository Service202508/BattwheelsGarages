"""
Organization Models and Schemas
Multi-tenant foundation for Battwheels OS
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ==================== ENUMS ====================

class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrgType(str, Enum):
    """Organization type for internal vs external handling"""
    CUSTOMER = "customer"      # External paying customers
    INTERNAL = "internal"      # Battwheels-owned garages
    PARTNER = "partner"        # Franchise/partner organizations
    DEMO = "demo"              # Demo/trial organizations


class IndustryType(str, Enum):
    EV_GARAGE = "ev_garage"
    FLEET_OPERATOR = "fleet_operator"
    OEM_SERVICE = "oem_service"
    MULTI_BRAND = "multi_brand"
    FRANCHISE = "franchise"


class OrgUserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    DISPATCHER = "dispatcher"
    TECHNICIAN = "technician"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class OrgUserStatus(str, Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


# ==================== ORGANIZATION ====================

class OrganizationBase(BaseModel):
    """Base organization model"""
    name: str
    slug: str
    org_type: OrgType = OrgType.CUSTOMER  # NEW: internal vs customer
    industry_type: IndustryType = IndustryType.EV_GARAGE
    plan_type: PlanType = PlanType.STARTER
    logo_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    gstin: Optional[str] = None


class Organization(OrganizationBase):
    """Full organization model"""
    model_config = ConfigDict(extra="ignore")
    
    organization_id: str = Field(default_factory=lambda: f"org_{uuid.uuid4().hex[:12]}")
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    
    # Computed fields
    total_users: int = 0
    total_vehicles: int = 0
    total_tickets: int = 0


class OrganizationCreate(BaseModel):
    """Create organization request"""
    name: str
    slug: Optional[str] = None
    industry_type: IndustryType = IndustryType.EV_GARAGE
    plan_type: PlanType = PlanType.STARTER
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    gstin: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Update organization request"""
    name: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    industry_type: Optional[IndustryType] = None


# ==================== ORGANIZATION SETTINGS ====================

class TicketSettings(BaseModel):
    """Ticket-related settings"""
    default_priority: str = "medium"
    auto_assign_enabled: bool = True
    sla_hours_low: int = 72
    sla_hours_medium: int = 24
    sla_hours_high: int = 8
    sla_hours_critical: int = 2
    allow_customer_portal: bool = True
    require_approval_for_close: bool = False


class InventorySettings(BaseModel):
    """Inventory-related settings"""
    tracking_enabled: bool = True
    low_stock_threshold: int = 10
    auto_reorder_enabled: bool = False
    negative_stock_allowed: bool = False
    require_serial_tracking: bool = False
    require_batch_tracking: bool = False


class InvoiceSettings(BaseModel):
    """Invoice-related settings"""
    default_payment_terms: int = 30
    auto_number_enabled: bool = True
    invoice_prefix: str = "INV-"
    estimate_prefix: str = "EST-"
    salesorder_prefix: str = "SO-"
    gst_enabled: bool = True
    default_tax_rate: float = 18.0
    rounding_type: str = "round_half_up"


class NotificationSettings(BaseModel):
    """Notification preferences"""
    email_enabled: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    notify_on_ticket_create: bool = True
    notify_on_ticket_assign: bool = True
    notify_on_invoice_create: bool = True
    notify_on_payment_receive: bool = True


class EFISettings(BaseModel):
    """EV Failure Intelligence settings"""
    failure_learning_enabled: bool = True
    auto_suggest_diagnosis: bool = True
    min_confidence_threshold: float = 0.7
    require_checklist_completion: bool = True
    capture_diagnostic_photos: bool = True


class OrganizationSettings(BaseModel):
    """Complete organization settings"""
    model_config = ConfigDict(extra="ignore")
    
    settings_id: str = Field(default_factory=lambda: f"set_{uuid.uuid4().hex[:12]}")
    organization_id: str
    
    # General
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    date_format: str = "DD/MM/YYYY"
    fiscal_year_start: str = "04-01"  # April 1
    
    # Service
    service_radius_km: int = 50
    operating_hours_start: str = "09:00"
    operating_hours_end: str = "18:00"
    working_days: List[str] = Field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])
    
    # Nested settings
    tickets: TicketSettings = Field(default_factory=TicketSettings)
    inventory: InventorySettings = Field(default_factory=InventorySettings)
    invoices: InvoiceSettings = Field(default_factory=InvoiceSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    efi: EFISettings = Field(default_factory=EFISettings)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationSettingsUpdate(BaseModel):
    """Update settings request"""
    currency: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    fiscal_year_start: Optional[str] = None
    service_radius_km: Optional[int] = None
    operating_hours_start: Optional[str] = None
    operating_hours_end: Optional[str] = None
    working_days: Optional[List[str]] = None
    tickets: Optional[Dict[str, Any]] = None
    inventory: Optional[Dict[str, Any]] = None
    invoices: Optional[Dict[str, Any]] = None
    notifications: Optional[Dict[str, Any]] = None
    efi: Optional[Dict[str, Any]] = None


# ==================== ORGANIZATION USERS ====================

class OrganizationUser(BaseModel):
    """User membership in organization"""
    model_config = ConfigDict(extra="ignore")
    
    membership_id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    organization_id: str
    user_id: str
    role: OrgUserRole = OrgUserRole.VIEWER
    status: OrgUserStatus = OrgUserStatus.ACTIVE
    
    # Permissions override (optional)
    custom_permissions: List[str] = Field(default_factory=list)
    
    # Metadata
    invited_by: Optional[str] = None
    invited_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationUserCreate(BaseModel):
    """Add user to organization"""
    user_id: Optional[str] = None  # If existing user
    email: Optional[str] = None    # If inviting new user
    role: OrgUserRole = OrgUserRole.VIEWER
    send_invite: bool = True


class OrganizationUserUpdate(BaseModel):
    """Update user membership"""
    role: Optional[OrgUserRole] = None
    status: Optional[OrgUserStatus] = None
    custom_permissions: Optional[List[str]] = None


# ==================== ROLE PERMISSIONS ====================

# Default permissions per role
ROLE_PERMISSIONS = {
    OrgUserRole.OWNER: [
        "org:read", "org:update", "org:delete",
        "org:settings:read", "org:settings:update",
        "org:users:read", "org:users:create", "org:users:update", "org:users:delete",
        "org:billing:read", "org:billing:update",
        "vehicles:*", "tickets:*", "invoices:*", "estimates:*",
        "inventory:*", "payments:*", "contacts:*", "reports:*",
        "efi:*", "settings:*"
    ],
    OrgUserRole.ADMIN: [
        "org:read", "org:update",
        "org:settings:read", "org:settings:update",
        "org:users:read", "org:users:create", "org:users:update",
        "vehicles:*", "tickets:*", "invoices:*", "estimates:*",
        "inventory:*", "payments:*", "contacts:*", "reports:*",
        "efi:*"
    ],
    OrgUserRole.MANAGER: [
        "org:read",
        "org:settings:read",
        "org:users:read",
        "vehicles:read", "vehicles:update",
        "tickets:*", "invoices:read", "invoices:create",
        "estimates:*", "inventory:read",
        "payments:read", "contacts:*", "reports:read",
        "efi:read", "efi:use"
    ],
    OrgUserRole.DISPATCHER: [
        "org:read",
        "vehicles:read",
        "tickets:read", "tickets:create", "tickets:update",
        "contacts:read", "contacts:create",
        "efi:read", "efi:use"
    ],
    OrgUserRole.TECHNICIAN: [
        "org:read",
        "vehicles:read",
        "tickets:read", "tickets:update",
        "inventory:read",
        "efi:read", "efi:use", "efi:contribute"
    ],
    OrgUserRole.ACCOUNTANT: [
        "org:read",
        "invoices:*", "estimates:*",
        "payments:*", "contacts:read",
        "reports:read", "reports:financial"
    ],
    OrgUserRole.VIEWER: [
        "org:read",
        "vehicles:read", "tickets:read",
        "invoices:read", "estimates:read",
        "contacts:read"
    ]
}


def get_role_permissions(role: OrgUserRole) -> List[str]:
    """Get permissions for a role"""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(user_permissions: List[str], required: str) -> bool:
    """Check if user has required permission"""
    if "*" in user_permissions:
        return True
    
    # Check exact match
    if required in user_permissions:
        return True
    
    # Check wildcard (e.g., "tickets:*" covers "tickets:read")
    resource = required.split(":")[0]
    if f"{resource}:*" in user_permissions:
        return True
    
    return False


# ==================== ORGANIZATION CONTEXT ====================

class OrganizationContext(BaseModel):
    """Request context with organization info"""
    organization_id: str
    organization: Organization
    settings: OrganizationSettings
    user_id: str
    user_role: OrgUserRole
    user_permissions: List[str]
    
    def has_permission(self, permission: str) -> bool:
        """Check if current user has permission"""
        return has_permission(self.user_permissions, permission)
    
    def require_permission(self, permission: str):
        """Raise error if permission not granted"""
        if not self.has_permission(permission):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}"
            )
