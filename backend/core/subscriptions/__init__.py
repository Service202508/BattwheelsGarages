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

__all__ = [
    # Models
    "Plan", "PlanCode", "PlanFeatures", "PlanLimits", "FeatureLimit",
    "Subscription", "SubscriptionCreate", "SubscriptionUpdate",
    "SubscriptionStatus", "BillingCycle", "UsageRecord", "OrgType",
    "DEFAULT_PLANS", "get_default_plan",
    
    # Service
    "SubscriptionService",
    "init_subscription_service",
    "get_subscription_service"
]
