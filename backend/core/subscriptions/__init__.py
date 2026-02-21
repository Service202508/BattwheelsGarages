"""
Subscriptions Module
====================

Enterprise subscription and plan management for Battwheels OS SaaS.
"""

from .models import (
    Plan, PlanCode, PlanFeatures, PlanLimits, FeatureLimit,
    Subscription, SubscriptionCreate, SubscriptionUpdate,
    SubscriptionStatus, BillingCycle, UsageRecord, OrgType,
    DEFAULT_PLANS, get_default_plan
)

from .service import (
    SubscriptionService,
    init_subscription_service,
    get_subscription_service
)

from .entitlement import (
    EntitlementService,
    init_entitlement_service,
    get_entitlement_service,
    require_feature,
    require_usage_limit,
    require_subscription,
    feature_gate,
    FeatureNotAvailable,
    UsageLimitExceeded,
    SubscriptionRequired,
    SubscriptionExpired
)

__all__ = [
    # Models
    "Plan", "PlanCode", "PlanFeatures", "PlanLimits", "FeatureLimit",
    "Subscription", "SubscriptionCreate", "SubscriptionUpdate",
    "SubscriptionStatus", "BillingCycle", "UsageRecord", "OrgType",
    "DEFAULT_PLANS", "get_default_plan",
    
    # Subscription Service
    "SubscriptionService",
    "init_subscription_service",
    "get_subscription_service",
    
    # Entitlement Service
    "EntitlementService",
    "init_entitlement_service",
    "get_entitlement_service",
    "require_feature",
    "require_usage_limit",
    "require_subscription",
    "feature_gate",
    "FeatureNotAvailable",
    "UsageLimitExceeded",
    "SubscriptionRequired",
    "SubscriptionExpired"
]
