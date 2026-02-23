"""
Feature Entitlement Service
============================

Central service for checking feature access based on subscription plans.
Provides middleware and decorators for protecting feature-specific API routes.

Usage:
    # As a dependency
    @router.get("/advanced-reports")
    async def get_advanced_reports(
        ctx: TenantContext = Depends(tenant_context_required),
        _: None = Depends(require_feature("advanced_reports"))
    ):
        ...

    # Direct check in code
    entitlement = get_entitlement_service()
    if await entitlement.has_feature(org_id, "efi_ai_guidance"):
        # Enable AI guidance
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from functools import wraps
from fastapi import HTTPException, Depends, Request
import logging

from .models import Plan, PlanCode, Subscription, FeatureLimit, PlanFeatures
from .service import get_subscription_service

logger = logging.getLogger(__name__)


class FeatureNotAvailable(HTTPException):
    """Exception raised when a feature is not available for the subscription"""

    # Human-readable names for features used in error messages
    FEATURE_DISPLAY_NAMES: Dict[str, str] = {
        "hr_payroll": "Payroll",
        "advanced_reports": "Advanced Reports",
        "project_management": "Project Management",
        "inventory_multi_warehouse": "Multi-Warehouse",
        "inventory_stock_transfers": "Stock Transfers",
        "einvoice": "E-Invoice",
        "accounting_module": "Accounting Module",
        "efi_failure_intelligence": "EFI Intelligence",
        "efi_ai_guidance": "EFI AI Guidance",
        "efi_knowledge_brain": "Knowledge Brain",
        "efi_expert_escalation": "Expert Escalation",
    }

    def __init__(self, feature: str, plan: str, required_plan: Optional[str] = None, upgrade_to: Optional[str] = None):
        display_name = self.FEATURE_DISPLAY_NAMES.get(feature, feature.replace("_", " ").title())
        req_plan_display = (required_plan or upgrade_to or "a higher").title()
        detail = {
            "error": "feature_not_available",
            "feature": display_name,
            "feature_key": feature,
            "current_plan": plan,
            "required_plan": required_plan or upgrade_to,
            "message": f"Upgrade to {req_plan_display} to access {display_name}",
            "upgrade_url": "/settings/billing",
        }
        super().__init__(status_code=403, detail=detail)


class UsageLimitExceeded(HTTPException):
    """Exception raised when usage limit is exceeded"""
    def __init__(self, feature: str, limit: int, current: int):
        super().__init__(
            status_code=429,
            detail={
                "error": "usage_limit_exceeded",
                "feature": feature,
                "limit": limit,
                "current": current,
                "message": f"You have reached your {feature} limit ({current}/{limit}). "
                           f"Upgrade your plan for higher limits."
            }
        )


class SubscriptionRequired(HTTPException):
    """Exception raised when no active subscription exists"""
    def __init__(self):
        super().__init__(
            status_code=402,
            detail={
                "error": "subscription_required",
                "message": "An active subscription is required to access this feature. "
                           "Please subscribe to a plan."
            }
        )


class SubscriptionExpired(HTTPException):
    """Exception raised when subscription has expired"""
    def __init__(self, expired_at: datetime):
        super().__init__(
            status_code=402,
            detail={
                "error": "subscription_expired",
                "expired_at": expired_at.isoformat(),
                "message": "Your subscription has expired. Please renew to continue access."
            }
        )


class EntitlementService:
    """
    Central service for feature entitlement checks.
    
    Provides methods to:
    - Check if a feature is enabled for an organization
    - Check if usage limits are within bounds
    - Get available features for a plan
    - Determine required plan for a feature
    """
    
    # Feature -> Minimum plan required mapping
    FEATURE_PLAN_REQUIREMENTS: Dict[str, PlanCode] = {
        # Operations - Available on all plans
        "ops_tickets": PlanCode.FREE,
        "ops_vehicles": PlanCode.FREE,
        "ops_estimates": PlanCode.FREE,
        "ops_amc": PlanCode.STARTER,
        
        # Finance
        "finance_invoicing": PlanCode.FREE,
        "finance_recurring_invoices": PlanCode.STARTER,
        "finance_payments": PlanCode.FREE,
        "finance_bills": PlanCode.PROFESSIONAL,
        "finance_expenses": PlanCode.PROFESSIONAL,
        "finance_banking": PlanCode.PROFESSIONAL,
        "finance_gst": PlanCode.FREE,
        
        # Inventory
        "inventory_tracking": PlanCode.STARTER,
        "inventory_serial_batch": PlanCode.PROFESSIONAL,
        "inventory_multi_warehouse": PlanCode.ENTERPRISE,
        "inventory_stock_transfers": PlanCode.ENTERPRISE,
        
        # HR
        "hr_employees": PlanCode.PROFESSIONAL,
        "hr_attendance": PlanCode.PROFESSIONAL,
        "hr_leave": PlanCode.PROFESSIONAL,
        "hr_payroll": PlanCode.PROFESSIONAL,
        
        # EFI/Intelligence
        "efi_failure_intelligence": PlanCode.STARTER,
        "efi_ai_guidance": PlanCode.STARTER,
        "efi_knowledge_brain": PlanCode.PROFESSIONAL,
        "efi_expert_escalation": PlanCode.ENTERPRISE,
        
        # Integrations
        "integrations_zoho_sync": PlanCode.PROFESSIONAL,
        "integrations_api_access": PlanCode.PROFESSIONAL,
        "integrations_webhooks": PlanCode.ENTERPRISE,
        
        # Portals
        "portal_customer": PlanCode.STARTER,
        "portal_business": PlanCode.PROFESSIONAL,
        "portal_technician": PlanCode.FREE,
        
        # Advanced
        "advanced_reports": PlanCode.STARTER,
        "advanced_custom_fields": PlanCode.PROFESSIONAL,
        "advanced_workflow_automation": PlanCode.ENTERPRISE,
        "advanced_pdf_templates": PlanCode.PROFESSIONAL,
        "advanced_audit_logs": PlanCode.PROFESSIONAL,
        "advanced_white_label": PlanCode.ENTERPRISE,
        "advanced_sso": PlanCode.ENTERPRISE,

        # Module-level gates
        "project_management": PlanCode.PROFESSIONAL,
        "einvoice": PlanCode.PROFESSIONAL,
        "accounting_module": PlanCode.PROFESSIONAL,
    }
    
    # Plan hierarchy for upgrade suggestions
    PLAN_HIERARCHY = [PlanCode.FREE, PlanCode.STARTER, PlanCode.PROFESSIONAL, PlanCode.ENTERPRISE]
    
    def __init__(self):
        self._feature_cache: Dict[str, Dict[str, FeatureLimit]] = {}
    
    async def get_subscription(self, org_id: str) -> Optional[Subscription]:
        """Get active subscription for organization"""
        service = get_subscription_service()
        return await service.get_subscription(org_id)
    
    async def get_plan(self, plan_code: PlanCode) -> Optional[Plan]:
        """Get plan by code"""
        service = get_subscription_service()
        return await service.get_plan(plan_code)
    
    async def has_active_subscription(self, org_id: str) -> bool:
        """Check if organization has an active subscription"""
        subscription = await self.get_subscription(org_id)
        return subscription is not None and subscription.is_active()
    
    async def get_feature_limit(
        self, 
        org_id: str, 
        feature: str
    ) -> Tuple[bool, Optional[int]]:
        """
        Get feature access and limit for an organization.
        
        Returns:
            Tuple of (is_enabled, limit) where limit is None if unlimited
        """
        subscription = await self.get_subscription(org_id)
        
        if not subscription:
            return (False, 0)
        
        if not subscription.is_active():
            return (False, 0)
        
        plan = await self.get_plan(subscription.plan_code)
        if not plan:
            return (False, 0)
        
        # Get feature from plan
        features = plan.features
        feature_data = getattr(features, feature, None)
        
        if feature_data is None:
            # Feature not defined in plan
            return (False, 0)
        
        return (feature_data.enabled, feature_data.limit)
    
    async def has_feature(self, org_id: str, feature: str) -> bool:
        """Check if organization has access to a feature"""
        enabled, _ = await self.get_feature_limit(org_id, feature)
        return enabled
    
    async def check_feature_access(
        self, 
        org_id: str, 
        feature: str,
        raise_exception: bool = True
    ) -> bool:
        """
        Check if organization can access a feature.
        
        Args:
            org_id: Organization ID
            feature: Feature key (e.g., "efi_ai_guidance")
            raise_exception: If True, raises HTTPException on denial
            
        Returns:
            True if access granted
            
        Raises:
            SubscriptionRequired: No active subscription
            FeatureNotAvailable: Feature not in plan
        """
        subscription = await self.get_subscription(org_id)
        
        if not subscription:
            if raise_exception:
                raise SubscriptionRequired()
            return False
        
        if not subscription.is_active():
            if raise_exception:
                if subscription.current_period_end:
                    raise SubscriptionExpired(subscription.current_period_end)
                raise SubscriptionRequired()
            return False
        
        enabled, _ = await self.get_feature_limit(org_id, feature)
        
        if not enabled:
            if raise_exception:
                required_plan = self.get_minimum_plan_for_feature(feature)
                upgrade_to = self._get_upgrade_suggestion(feature, subscription.plan_code)
                raise FeatureNotAvailable(
                    feature=feature,
                    plan=subscription.plan_code.value,
                    required_plan=required_plan.value if required_plan else None,
                    upgrade_to=upgrade_to
                )
            return False
        
        return True
    
    async def check_usage_limit(
        self,
        org_id: str,
        limit_type: str,
        increment: int = 1,
        raise_exception: bool = True
    ) -> bool:
        """
        Check if organization is within usage limits.
        
        Args:
            org_id: Organization ID
            limit_type: Type of limit (e.g., "max_invoices_per_month")
            increment: How much to add to current usage
            raise_exception: If True, raises HTTPException on limit exceeded
            
        Returns:
            True if within limits
        """
        subscription = await self.get_subscription(org_id)
        
        if not subscription:
            if raise_exception:
                raise SubscriptionRequired()
            return False
        
        plan = await self.get_plan(subscription.plan_code)
        if not plan:
            return False
        
        # Get limit from plan
        limit = getattr(plan.limits, limit_type, 0)
        
        # -1 means unlimited
        if limit == -1:
            return True
        
        # Get current usage
        usage = subscription.usage
        usage_map = {
            "max_invoices_per_month": usage.invoices_created,
            "max_tickets_per_month": usage.tickets_created,
            "max_vehicles": usage.vehicles_added,
            "max_ai_calls_per_month": usage.ai_calls_made,
            "max_api_calls_per_day": usage.api_calls_made,
        }
        
        current = usage_map.get(limit_type, 0)
        
        if current + increment > limit:
            if raise_exception:
                feature_name = limit_type.replace("max_", "").replace("_per_month", "").replace("_per_day", "")
                raise UsageLimitExceeded(
                    feature=feature_name,
                    limit=limit,
                    current=current
                )
            return False
        
        return True
    
    async def get_available_features(self, org_id: str) -> Dict[str, bool]:
        """Get all features with their availability for an organization"""
        result = {}
        
        for feature in self.FEATURE_PLAN_REQUIREMENTS.keys():
            result[feature] = await self.has_feature(org_id, feature)
        
        return result
    
    async def get_plan_comparison(self) -> List[Dict[str, Any]]:
        """Get comparison of all plans with features"""
        service = get_subscription_service()
        plans = await service.list_plans()
        
        comparison = []
        for plan in plans:
            features_dict = plan.features.model_dump() if hasattr(plan.features, 'model_dump') else {}
            limits_dict = plan.limits.model_dump() if hasattr(plan.limits, 'model_dump') else {}
            
            comparison.append({
                "code": plan.code.value,
                "name": plan.name,
                "price_monthly": plan.price_monthly,
                "price_annual": plan.price_annual,
                "features": features_dict,
                "limits": limits_dict,
                "support_level": plan.support_level
            })
        
        return comparison
    
    def _get_upgrade_suggestion(self, feature: str, current_plan: PlanCode) -> Optional[str]:
        """Get the plan to upgrade to for a specific feature"""
        required_plan = self.FEATURE_PLAN_REQUIREMENTS.get(feature)
        
        if not required_plan:
            return None
        
        current_idx = self.PLAN_HIERARCHY.index(current_plan)
        required_idx = self.PLAN_HIERARCHY.index(required_plan)
        
        if required_idx > current_idx:
            return required_plan.value.title()
        
        # Feature should be available, check next tier
        if current_idx < len(self.PLAN_HIERARCHY) - 1:
            return self.PLAN_HIERARCHY[current_idx + 1].value.title()
        
        return None
    
    def get_minimum_plan_for_feature(self, feature: str) -> Optional[PlanCode]:
        """Get the minimum plan required for a feature"""
        return self.FEATURE_PLAN_REQUIREMENTS.get(feature)


# ==================== SINGLETON ====================

_entitlement_service: Optional[EntitlementService] = None


def init_entitlement_service() -> EntitlementService:
    """Initialize the entitlement service singleton"""
    global _entitlement_service
    _entitlement_service = EntitlementService()
    logger.info("EntitlementService initialized")
    return _entitlement_service


def get_entitlement_service() -> EntitlementService:
    """Get the entitlement service singleton"""
    global _entitlement_service
    if _entitlement_service is None:
        _entitlement_service = EntitlementService()
    return _entitlement_service


# ==================== FASTAPI DEPENDENCIES ====================

def require_feature(feature: str):
    """
    FastAPI dependency that requires a specific feature.
    
    Usage:
        @router.get("/ai-guidance")
        async def get_guidance(
            ctx: TenantContext = Depends(tenant_context_required),
            _: None = Depends(require_feature("efi_ai_guidance"))
        ):
            ...
    """
    async def dependency(request: Request):
        from core.tenant.context import get_tenant_context
        
        ctx = get_tenant_context()
        if not ctx:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        entitlement = get_entitlement_service()
        await entitlement.check_feature_access(ctx.org_id, feature)
        
        return None
    
    return dependency


def require_usage_limit(limit_type: str, increment: int = 1):
    """
    FastAPI dependency that checks usage limits.
    
    Usage:
        @router.post("/invoices")
        async def create_invoice(
            ctx: TenantContext = Depends(tenant_context_required),
            _: None = Depends(require_usage_limit("max_invoices_per_month"))
        ):
            ...
    """
    async def dependency(request: Request):
        from core.tenant.context import get_tenant_context
        
        ctx = get_tenant_context()
        if not ctx:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        entitlement = get_entitlement_service()
        await entitlement.check_usage_limit(ctx.org_id, limit_type, increment)
        
        return None
    
    return dependency


def require_subscription():
    """
    FastAPI dependency that requires any active subscription.
    
    Usage:
        @router.get("/dashboard")
        async def get_dashboard(
            ctx: TenantContext = Depends(tenant_context_required),
            _: None = Depends(require_subscription())
        ):
            ...
    """
    async def dependency(request: Request):
        from core.tenant.context import get_tenant_context
        
        ctx = get_tenant_context()
        if not ctx:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        entitlement = get_entitlement_service()
        subscription = await entitlement.get_subscription(ctx.org_id)
        
        if not subscription:
            raise SubscriptionRequired()
        
        if not subscription.is_active():
            if subscription.current_period_end:
                raise SubscriptionExpired(subscription.current_period_end)
            raise SubscriptionRequired()
        
        return None
    
    return dependency


# ==================== DECORATOR ====================

def feature_gate(feature: str):
    """
    Decorator to protect a function with feature check.
    
    Usage:
        @feature_gate("efi_ai_guidance")
        async def generate_ai_guidance(org_id: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to find org_id in kwargs or first positional arg
            org_id = kwargs.get("org_id") or kwargs.get("organization_id")
            
            if not org_id and args:
                org_id = args[0] if isinstance(args[0], str) else None
            
            if not org_id:
                raise ValueError("org_id required for feature gate check")
            
            entitlement = get_entitlement_service()
            await entitlement.check_feature_access(org_id, feature)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
