"""
Subscription & Plan Models
==========================

Enterprise SaaS subscription management for Battwheels OS.
Implements Zoho Books-style plan-based feature access with usage limits.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ==================== ENUMS ====================

class PlanCode(str, Enum):
    """Available subscription plans"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle states"""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class BillingCycle(str, Enum):
    """Billing frequency"""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    LIFETIME = "lifetime"


class OrgType(str, Enum):
    """Organization type for internal vs external handling"""
    CUSTOMER = "customer"      # External paying customers
    INTERNAL = "internal"      # Battwheels-owned garages
    PARTNER = "partner"        # Franchise/partner organizations
    DEMO = "demo"              # Demo/trial organizations


# ==================== FEATURE DEFINITIONS ====================

class FeatureLimit(BaseModel):
    """Feature with optional usage limit"""
    enabled: bool = True
    limit: Optional[int] = None  # None = unlimited
    description: Optional[str] = None


class PlanFeatures(BaseModel):
    """Complete feature set for a plan"""
    # Operations Module
    ops_tickets: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=True))
    ops_vehicles: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=True))
    ops_estimates: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=True))
    ops_amc: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    
    # Finance Module
    finance_invoicing: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=True))
    finance_recurring_invoices: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    finance_payments: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=True))
    finance_bills: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    finance_expenses: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    finance_banking: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    finance_gst: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=True))
    
    # Inventory Module
    inventory_tracking: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    inventory_serial_batch: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    inventory_multi_warehouse: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    inventory_stock_transfers: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    
    # HR & Payroll Module
    hr_employees: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    hr_attendance: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    hr_leave: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    hr_payroll: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    
    # Intelligence (EFI) Module
    efi_failure_intelligence: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    efi_ai_guidance: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    efi_knowledge_brain: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    efi_expert_escalation: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    
    # Integrations
    integrations_zoho_sync: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    integrations_api_access: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    integrations_webhooks: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    
    # Portals
    portal_customer: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    portal_business: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    portal_technician: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=True))
    
    # Advanced Features
    advanced_reports: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    advanced_custom_fields: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    advanced_workflow_automation: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    advanced_pdf_templates: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    advanced_audit_logs: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    advanced_white_label: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    advanced_sso: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))

    # Module-level gates (new)
    project_management: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    einvoice: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))
    accounting_module: FeatureLimit = Field(default_factory=lambda: FeatureLimit(enabled=False))


class PlanLimits(BaseModel):
    """Usage limits for a plan"""
    max_users: int = 1
    max_technicians: int = 1
    max_vehicles: int = 50
    max_invoices_per_month: int = 50
    max_tickets_per_month: int = 100
    max_ai_calls_per_month: int = 0
    max_storage_gb: float = 1.0
    max_api_calls_per_day: int = 0


# ==================== PLAN MODEL ====================

class Plan(BaseModel):
    """Subscription plan definition"""
    model_config = ConfigDict(extra="ignore")
    
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    code: PlanCode
    name: str
    description: str
    
    # Pricing
    price_monthly: float = 0.0
    price_annual: float = 0.0
    currency: str = "INR"
    
    # Features & Limits
    features: PlanFeatures = Field(default_factory=PlanFeatures)
    limits: PlanLimits = Field(default_factory=PlanLimits)
    
    # Trial
    trial_days: int = 14
    
    # Support level
    support_level: str = "email"  # email, priority, dedicated, 24x7
    
    # Metadata
    is_active: bool = True
    is_public: bool = True  # Show on pricing page
    sort_order: int = 0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== SUBSCRIPTION MODEL ====================

class UsageRecord(BaseModel):
    """Current period usage tracking"""
    invoices_created: int = 0
    tickets_created: int = 0
    vehicles_added: int = 0
    ai_calls_made: int = 0
    api_calls_made: int = 0
    storage_used_mb: float = 0.0
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Subscription(BaseModel):
    """Organization subscription record"""
    model_config = ConfigDict(extra="ignore")
    
    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    organization_id: str
    plan_id: str
    plan_code: PlanCode
    
    # Status
    status: SubscriptionStatus = SubscriptionStatus.TRIALING
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    
    # Period
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_period_end: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    
    # Cancellation
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    # Payment
    payment_method: Optional[str] = None  # stripe, razorpay, manual
    external_subscription_id: Optional[str] = None  # Stripe/Razorpay sub ID
    
    # Usage tracking
    usage: UsageRecord = Field(default_factory=UsageRecord)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if subscription allows feature access"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
    
    def is_in_trial(self) -> bool:
        """Check if currently in trial period"""
        return self.status == SubscriptionStatus.TRIALING


class SubscriptionCreate(BaseModel):
    """Create subscription request"""
    plan_code: PlanCode = PlanCode.STARTER
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    payment_method: Optional[str] = None
    start_trial: bool = True


class SubscriptionUpdate(BaseModel):
    """Update subscription request"""
    plan_code: Optional[PlanCode] = None
    billing_cycle: Optional[BillingCycle] = None
    cancel_at_period_end: Optional[bool] = None
    cancellation_reason: Optional[str] = None


# ==================== DEFAULT PLAN DEFINITIONS ====================

DEFAULT_PLANS = [
    {
        "code": PlanCode.FREE,
        "name": "Free",
        "description": "Perfect for getting started with basic workshop management",
        "price_monthly": 0,
        "price_annual": 0,
        "trial_days": 0,
        "support_level": "community",
        "sort_order": 1,
        "features": PlanFeatures(
            ops_tickets=FeatureLimit(enabled=True, limit=50),
            ops_vehicles=FeatureLimit(enabled=True, limit=25),
            ops_estimates=FeatureLimit(enabled=True, limit=50),
            finance_invoicing=FeatureLimit(enabled=True, limit=50),
            finance_payments=FeatureLimit(enabled=True),
            finance_gst=FeatureLimit(enabled=True),
            portal_technician=FeatureLimit(enabled=True),
        ),
        "limits": PlanLimits(
            max_users=1,
            max_technicians=1,
            max_vehicles=25,
            max_invoices_per_month=50,
            max_tickets_per_month=50,
            max_ai_calls_per_month=0,
            max_storage_gb=0.5,
            max_api_calls_per_day=0
        )
    },
    {
        "code": PlanCode.STARTER,
        "name": "Starter",
        "description": "For small workshops ready to digitize operations",
        "price_monthly": 2999,
        "price_annual": 29990,
        "trial_days": 14,
        "support_level": "email",
        "sort_order": 2,
        "features": PlanFeatures(
            ops_tickets=FeatureLimit(enabled=True),
            ops_vehicles=FeatureLimit(enabled=True, limit=100),
            ops_estimates=FeatureLimit(enabled=True),
            ops_amc=FeatureLimit(enabled=True),
            finance_invoicing=FeatureLimit(enabled=True, limit=500),
            finance_recurring_invoices=FeatureLimit(enabled=True, limit=10),
            finance_payments=FeatureLimit(enabled=True),
            finance_gst=FeatureLimit(enabled=True),
            inventory_tracking=FeatureLimit(enabled=True),
            efi_failure_intelligence=FeatureLimit(enabled=True),
            efi_ai_guidance=FeatureLimit(enabled=True, limit=100),
            portal_customer=FeatureLimit(enabled=True),
            portal_technician=FeatureLimit(enabled=True),
            advanced_reports=FeatureLimit(enabled=True),
        ),
        "limits": PlanLimits(
            max_users=3,
            max_technicians=2,
            max_vehicles=100,
            max_invoices_per_month=500,
            max_tickets_per_month=500,
            max_ai_calls_per_month=100,
            max_storage_gb=5.0,
            max_api_calls_per_day=0
        )
    },
    {
        "code": PlanCode.PROFESSIONAL,
        "name": "Professional",
        "description": "For growing workshops with multiple technicians",
        "price_monthly": 7999,
        "price_annual": 79990,
        "trial_days": 14,
        "support_level": "priority",
        "sort_order": 3,
        "features": PlanFeatures(
            ops_tickets=FeatureLimit(enabled=True),
            ops_vehicles=FeatureLimit(enabled=True),
            ops_estimates=FeatureLimit(enabled=True),
            ops_amc=FeatureLimit(enabled=True),
            finance_invoicing=FeatureLimit(enabled=True),
            finance_recurring_invoices=FeatureLimit(enabled=True),
            finance_payments=FeatureLimit(enabled=True),
            finance_bills=FeatureLimit(enabled=True),
            finance_expenses=FeatureLimit(enabled=True),
            finance_banking=FeatureLimit(enabled=True),
            finance_gst=FeatureLimit(enabled=True),
            inventory_tracking=FeatureLimit(enabled=True),
            inventory_serial_batch=FeatureLimit(enabled=True),
            hr_employees=FeatureLimit(enabled=True),
            hr_attendance=FeatureLimit(enabled=True),
            hr_leave=FeatureLimit(enabled=True),
            hr_payroll=FeatureLimit(enabled=True),
            efi_failure_intelligence=FeatureLimit(enabled=True),
            efi_ai_guidance=FeatureLimit(enabled=True, limit=500),
            efi_knowledge_brain=FeatureLimit(enabled=True),
            integrations_zoho_sync=FeatureLimit(enabled=True),
            integrations_api_access=FeatureLimit(enabled=True, limit=1000),
            portal_customer=FeatureLimit(enabled=True),
            portal_business=FeatureLimit(enabled=True),
            portal_technician=FeatureLimit(enabled=True),
            advanced_reports=FeatureLimit(enabled=True),
            advanced_custom_fields=FeatureLimit(enabled=True),
            advanced_pdf_templates=FeatureLimit(enabled=True),
            advanced_audit_logs=FeatureLimit(enabled=True),
            project_management=FeatureLimit(enabled=True),
            einvoice=FeatureLimit(enabled=True),
            accounting_module=FeatureLimit(enabled=True),
        ),
        "limits": PlanLimits(
            max_users=10,
            max_technicians=5,
            max_vehicles=500,
            max_invoices_per_month=2000,
            max_tickets_per_month=2000,
            max_ai_calls_per_month=500,
            max_storage_gb=25.0,
            max_api_calls_per_day=1000
        )
    },
    {
        "code": PlanCode.ENTERPRISE,
        "name": "Enterprise",
        "description": "For large operations and Battwheels-owned garages",
        "price_monthly": 19999,
        "price_annual": 199990,
        "trial_days": 30,
        "support_level": "dedicated",
        "sort_order": 4,
        "features": PlanFeatures(
            # All features enabled with no limits
            ops_tickets=FeatureLimit(enabled=True),
            ops_vehicles=FeatureLimit(enabled=True),
            ops_estimates=FeatureLimit(enabled=True),
            ops_amc=FeatureLimit(enabled=True),
            finance_invoicing=FeatureLimit(enabled=True),
            finance_recurring_invoices=FeatureLimit(enabled=True),
            finance_payments=FeatureLimit(enabled=True),
            finance_bills=FeatureLimit(enabled=True),
            finance_expenses=FeatureLimit(enabled=True),
            finance_banking=FeatureLimit(enabled=True),
            finance_gst=FeatureLimit(enabled=True),
            inventory_tracking=FeatureLimit(enabled=True),
            inventory_serial_batch=FeatureLimit(enabled=True),
            inventory_multi_warehouse=FeatureLimit(enabled=True),
            inventory_stock_transfers=FeatureLimit(enabled=True),
            hr_employees=FeatureLimit(enabled=True),
            hr_attendance=FeatureLimit(enabled=True),
            hr_leave=FeatureLimit(enabled=True),
            hr_payroll=FeatureLimit(enabled=True),
            efi_failure_intelligence=FeatureLimit(enabled=True),
            efi_ai_guidance=FeatureLimit(enabled=True),
            efi_knowledge_brain=FeatureLimit(enabled=True),
            efi_expert_escalation=FeatureLimit(enabled=True),
            integrations_zoho_sync=FeatureLimit(enabled=True),
            integrations_api_access=FeatureLimit(enabled=True),
            integrations_webhooks=FeatureLimit(enabled=True),
            portal_customer=FeatureLimit(enabled=True),
            portal_business=FeatureLimit(enabled=True),
            portal_technician=FeatureLimit(enabled=True),
            advanced_reports=FeatureLimit(enabled=True),
            advanced_custom_fields=FeatureLimit(enabled=True),
            advanced_workflow_automation=FeatureLimit(enabled=True),
            advanced_pdf_templates=FeatureLimit(enabled=True),
            advanced_audit_logs=FeatureLimit(enabled=True),
            advanced_white_label=FeatureLimit(enabled=True),
            advanced_sso=FeatureLimit(enabled=True),
            project_management=FeatureLimit(enabled=True),
            einvoice=FeatureLimit(enabled=True),
            accounting_module=FeatureLimit(enabled=True),
        ),
        "limits": PlanLimits(
            max_users=-1,  # Unlimited
            max_technicians=-1,
            max_vehicles=-1,
            max_invoices_per_month=-1,
            max_tickets_per_month=-1,
            max_ai_calls_per_month=-1,
            max_storage_gb=-1,
            max_api_calls_per_day=-1
        )
    }
]


def get_default_plan(code: PlanCode) -> dict:
    """Get default plan configuration by code"""
    for plan in DEFAULT_PLANS:
        if plan["code"] == code:
            return plan
    return DEFAULT_PLANS[1]  # Return Starter as default
