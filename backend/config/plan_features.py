# Plan Features Configuration
# Subscription feature guardrails for Battwheels OS
# Implements Zoho Books-style plan-based feature access

from enum import Enum
from typing import Dict, List, Optional
from functools import wraps
from fastapi import HTTPException

# ========================= PLAN DEFINITIONS =========================

class PlanType(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"
    ULTIMATE = "ultimate"

# Plan feature matrix - matches Zoho Books plans
PLAN_FEATURES = {
    PlanType.FREE: {
        "name": "Free",
        "max_users": 1,
        "max_invoices_per_month": 50,
        "max_customers": 500,
        "max_items": 500,
        "features": {
            "invoicing": True,
            "estimates": True,
            "expense_tracking": False,
            "inventory_tracking": False,
            "serial_batch_tracking": False,
            "multi_currency": False,
            "multi_warehouse": False,
            "price_lists": False,
            "sales_orders": False,
            "purchase_orders": False,
            "recurring_invoices": False,
            "customer_portal": False,
            "custom_fields": False,
            "custom_reports": False,
            "api_access": False,
            "integrations": False,
            "workflow_automation": False,
            "pdf_templates": False,
            "payment_reminders": False,
            "audit_trail": False,
            "project_tracking": False,
            "time_tracking": False,
            "budgeting": False
        },
        "support": "email",
        "storage_gb": 1
    },
    PlanType.STANDARD: {
        "name": "Standard",
        "max_users": 3,
        "max_invoices_per_month": 500,
        "max_customers": 5000,
        "max_items": 5000,
        "features": {
            "invoicing": True,
            "estimates": True,
            "expense_tracking": True,
            "inventory_tracking": True,
            "serial_batch_tracking": False,
            "multi_currency": True,
            "multi_warehouse": False,
            "price_lists": True,
            "sales_orders": True,
            "purchase_orders": True,
            "recurring_invoices": True,
            "customer_portal": True,
            "custom_fields": True,
            "custom_reports": False,
            "api_access": True,
            "integrations": True,
            "workflow_automation": False,
            "pdf_templates": True,
            "payment_reminders": True,
            "audit_trail": True,
            "project_tracking": False,
            "time_tracking": False,
            "budgeting": False
        },
        "support": "email_phone",
        "storage_gb": 10
    },
    PlanType.PROFESSIONAL: {
        "name": "Professional",
        "max_users": 5,
        "max_invoices_per_month": 2000,
        "max_customers": 10000,
        "max_items": 10000,
        "features": {
            "invoicing": True,
            "estimates": True,
            "expense_tracking": True,
            "inventory_tracking": True,
            "serial_batch_tracking": True,
            "multi_currency": True,
            "multi_warehouse": True,
            "price_lists": True,
            "sales_orders": True,
            "purchase_orders": True,
            "recurring_invoices": True,
            "customer_portal": True,
            "custom_fields": True,
            "custom_reports": True,
            "api_access": True,
            "integrations": True,
            "workflow_automation": True,
            "pdf_templates": True,
            "payment_reminders": True,
            "audit_trail": True,
            "project_tracking": True,
            "time_tracking": False,
            "budgeting": False
        },
        "support": "priority",
        "storage_gb": 50
    },
    PlanType.PREMIUM: {
        "name": "Premium",
        "max_users": 10,
        "max_invoices_per_month": 5000,
        "max_customers": 50000,
        "max_items": 50000,
        "features": {
            "invoicing": True,
            "estimates": True,
            "expense_tracking": True,
            "inventory_tracking": True,
            "serial_batch_tracking": True,
            "multi_currency": True,
            "multi_warehouse": True,
            "price_lists": True,
            "sales_orders": True,
            "purchase_orders": True,
            "recurring_invoices": True,
            "customer_portal": True,
            "custom_fields": True,
            "custom_reports": True,
            "api_access": True,
            "integrations": True,
            "workflow_automation": True,
            "pdf_templates": True,
            "payment_reminders": True,
            "audit_trail": True,
            "project_tracking": True,
            "time_tracking": True,
            "budgeting": True
        },
        "support": "dedicated",
        "storage_gb": 100
    },
    PlanType.ULTIMATE: {
        "name": "Ultimate",
        "max_users": -1,  # Unlimited
        "max_invoices_per_month": -1,
        "max_customers": -1,
        "max_items": -1,
        "features": {
            "invoicing": True,
            "estimates": True,
            "expense_tracking": True,
            "inventory_tracking": True,
            "serial_batch_tracking": True,
            "multi_currency": True,
            "multi_warehouse": True,
            "price_lists": True,
            "sales_orders": True,
            "purchase_orders": True,
            "recurring_invoices": True,
            "customer_portal": True,
            "custom_fields": True,
            "custom_reports": True,
            "api_access": True,
            "integrations": True,
            "workflow_automation": True,
            "pdf_templates": True,
            "payment_reminders": True,
            "audit_trail": True,
            "project_tracking": True,
            "time_tracking": True,
            "budgeting": True
        },
        "support": "24x7",
        "storage_gb": -1  # Unlimited
    }
}

# ========================= FEATURE CHECK FUNCTIONS =========================

def get_plan_config(plan: str) -> Dict:
    """Get configuration for a plan"""
    try:
        plan_type = PlanType(plan.lower())
        return PLAN_FEATURES.get(plan_type, PLAN_FEATURES[PlanType.FREE])
    except (ValueError, KeyError):
        return PLAN_FEATURES[PlanType.FREE]

def has_feature(plan: str, feature: str) -> bool:
    """Check if a plan has a specific feature enabled"""
    config = get_plan_config(plan)
    return config.get("features", {}).get(feature, False)

def check_limit(plan: str, limit_type: str, current_count: int) -> Dict:
    """Check if a limit is reached for a plan"""
    config = get_plan_config(plan)
    limit = config.get(limit_type, 0)
    
    if limit == -1:  # Unlimited
        return {"allowed": True, "limit": -1, "current": current_count, "remaining": -1}
    
    remaining = max(0, limit - current_count)
    return {
        "allowed": current_count < limit,
        "limit": limit,
        "current": current_count,
        "remaining": remaining
    }

def get_available_features(plan: str) -> List[str]:
    """Get list of available features for a plan"""
    config = get_plan_config(plan)
    return [f for f, enabled in config.get("features", {}).items() if enabled]

def get_upgrade_features(current_plan: str, target_plan: str) -> List[str]:
    """Get features gained by upgrading from one plan to another"""
    current_features = set(get_available_features(current_plan))
    target_features = set(get_available_features(target_plan))
    return list(target_features - current_features)

# ========================= DECORATORS =========================

def require_feature(feature: str):
    """Decorator to require a feature for an endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get organization plan from request context
            # For now, assume Professional plan for all users
            org_plan = kwargs.get("org_plan", "professional")
            
            if not has_feature(org_plan, feature):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "feature_not_available",
                        "feature": feature,
                        "message": f"The '{feature}' feature is not available on your current plan. Please upgrade to access this feature.",
                        "upgrade_url": "/settings/subscription"
                    }
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_limit(limit_type: str, count_func=None):
    """Decorator to check limits before creating resources"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            org_plan = kwargs.get("org_plan", "professional")
            
            # Get current count
            if count_func:
                current_count = await count_func(*args, **kwargs)
            else:
                current_count = kwargs.get("current_count", 0)
            
            result = check_limit(org_plan, limit_type, current_count)
            
            if not result["allowed"]:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "limit_reached",
                        "limit_type": limit_type,
                        "message": f"You have reached the {limit_type.replace('_', ' ')} limit for your plan ({result['limit']}). Please upgrade to continue.",
                        "current": result["current"],
                        "limit": result["limit"],
                        "upgrade_url": "/settings/subscription"
                    }
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# ========================= FEATURE DESCRIPTIONS =========================

FEATURE_DESCRIPTIONS = {
    "invoicing": "Create and manage invoices",
    "estimates": "Create and manage quotes/estimates",
    "expense_tracking": "Track business expenses",
    "inventory_tracking": "Track inventory levels",
    "serial_batch_tracking": "Track items by serial/batch numbers",
    "multi_currency": "Support for multiple currencies",
    "multi_warehouse": "Multiple warehouse management",
    "price_lists": "Custom price lists for customers",
    "sales_orders": "Sales order management",
    "purchase_orders": "Purchase order management",
    "recurring_invoices": "Automated recurring invoices",
    "customer_portal": "Customer self-service portal",
    "custom_fields": "Custom fields on transactions",
    "custom_reports": "Build custom reports",
    "api_access": "API access for integrations",
    "integrations": "Third-party integrations",
    "workflow_automation": "Automated workflows",
    "pdf_templates": "Custom PDF templates",
    "payment_reminders": "Automated payment reminders",
    "audit_trail": "Complete audit trail",
    "project_tracking": "Project-based billing",
    "time_tracking": "Time tracking for billing",
    "budgeting": "Budget management"
}

# ========================= API HELPERS =========================

def get_plan_comparison():
    """Get comparison of all plans for pricing page"""
    comparison = []
    for plan_type in PlanType:
        config = PLAN_FEATURES[plan_type]
        comparison.append({
            "plan": plan_type.value,
            "name": config["name"],
            "max_users": config["max_users"],
            "max_invoices_per_month": config["max_invoices_per_month"],
            "storage_gb": config["storage_gb"],
            "support": config["support"],
            "features": config["features"]
        })
    return comparison

def get_feature_list():
    """Get list of all features with descriptions"""
    return [
        {"id": f, "name": f.replace("_", " ").title(), "description": desc}
        for f, desc in FEATURE_DESCRIPTIONS.items()
    ]
