"""
Usage Tracking Service
======================

Tracks and updates subscription usage metrics for organizations.
Called when billable actions occur (invoices created, tickets created, etc.)
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks usage metrics for subscription billing.
    
    Usage types:
    - invoices_created: Number of invoices created this period
    - tickets_created: Number of service tickets created
    - vehicles_added: Total vehicles in the system
    - ai_calls_made: AI API calls made
    - api_calls_made: External API calls
    """
    
    USAGE_FIELDS = {
        "invoices": "invoices_created",
        "tickets": "tickets_created",
        "vehicles": "vehicles_added",
        "ai_calls": "ai_calls_made",
        "api_calls": "api_calls_made"
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.subscriptions = db.subscriptions
    
    async def increment_usage(
        self,
        org_id: str,
        usage_type: str,
        amount: int = 1
    ) -> bool:
        """
        Increment a usage counter for an organization.
        
        Args:
            org_id: Organization ID
            usage_type: Type of usage (invoices, tickets, vehicles, ai_calls, api_calls)
            amount: Amount to increment (default 1)
            
        Returns:
            True if successful, False if org has no subscription
        """
        field = self.USAGE_FIELDS.get(usage_type)
        if not field:
            logger.warning(f"Unknown usage type: {usage_type}")
            return False
        
        try:
            result = await self.subscriptions.update_one(
                {"organization_id": org_id, "status": {"$in": ["active", "trialing"]}},
                {
                    "$inc": {f"usage.{field}": amount},
                    "$set": {"usage.last_updated": datetime.now(timezone.utc)}
                }
            )
            
            if result.modified_count > 0:
                logger.debug(f"Usage incremented: {org_id} {usage_type} +{amount}")
                return True
            else:
                logger.warning(f"No active subscription found for org: {org_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to increment usage for {org_id}: {e}")
            return False
    
    async def decrement_usage(
        self,
        org_id: str,
        usage_type: str,
        amount: int = 1
    ) -> bool:
        """
        Decrement a usage counter (e.g., when deleting a vehicle).
        Ensures counter doesn't go below 0.
        """
        field = self.USAGE_FIELDS.get(usage_type)
        if not field:
            return False
        
        try:
            # First check current value
            subscription = await self.subscriptions.find_one(
                {"organization_id": org_id},
                {"usage": 1}
            )
            
            if not subscription:
                return False
            
            current = subscription.get("usage", {}).get(field, 0)
            new_value = max(0, current - amount)
            
            await self.subscriptions.update_one(
                {"organization_id": org_id},
                {
                    "$set": {
                        f"usage.{field}": new_value,
                        "usage.last_updated": datetime.now(timezone.utc)
                    }
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to decrement usage for {org_id}: {e}")
            return False
    
    async def get_usage(self, org_id: str) -> dict:
        """Get current usage for an organization"""
        try:
            subscription = await self.subscriptions.find_one(
                {"organization_id": org_id},
                {"_id": 0, "usage": 1}
            )
            
            if subscription:
                return subscription.get("usage", {})
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get usage for {org_id}: {e}")
            return {}
    
    async def reset_monthly_usage(self, org_id: str) -> bool:
        """
        Reset monthly usage counters (called at billing period start).
        Only resets per-period counters, not cumulative ones like vehicles.
        """
        try:
            await self.subscriptions.update_one(
                {"organization_id": org_id},
                {
                    "$set": {
                        "usage.invoices_created": 0,
                        "usage.tickets_created": 0,
                        "usage.ai_calls_made": 0,
                        "usage.api_calls_made": 0,
                        "usage.last_reset": datetime.now(timezone.utc)
                    }
                }
            )
            logger.info(f"Monthly usage reset for org: {org_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset usage for {org_id}: {e}")
            return False
    
    async def check_limit(
        self,
        org_id: str,
        usage_type: str,
        increment: int = 1
    ) -> tuple[bool, Optional[int], Optional[int]]:
        """
        Check if adding to usage would exceed limit.
        
        Returns:
            Tuple of (within_limit, current_usage, limit)
            limit is None if unlimited (-1)
        """
        from core.subscriptions import get_subscription_service
        
        service = get_subscription_service()
        subscription = await service.get_subscription(org_id)
        
        if not subscription:
            return (False, 0, 0)
        
        plan = await service.get_plan(subscription.plan_code)
        if not plan:
            return (False, 0, 0)
        
        # Map usage type to limit field
        limit_map = {
            "invoices": plan.limits.max_invoices_per_month,
            "tickets": plan.limits.max_tickets_per_month,
            "vehicles": plan.limits.max_vehicles,
            "ai_calls": plan.limits.max_ai_calls_per_month,
            "api_calls": plan.limits.max_api_calls_per_day
        }
        
        limit = limit_map.get(usage_type, 0)
        
        # -1 means unlimited
        if limit == -1:
            return (True, 0, None)
        
        # Get current usage
        field = self.USAGE_FIELDS.get(usage_type)
        usage = subscription.usage
        current = getattr(usage, field, 0) if usage else 0
        
        within_limit = (current + increment) <= limit
        return (within_limit, current, limit)


# Singleton
_usage_tracker: Optional[UsageTracker] = None


def init_usage_tracker(db: AsyncIOMotorDatabase) -> UsageTracker:
    """Initialize the usage tracker singleton"""
    global _usage_tracker
    _usage_tracker = UsageTracker(db)
    logger.info("UsageTracker initialized")
    return _usage_tracker


def get_usage_tracker() -> UsageTracker:
    """Get the usage tracker singleton"""
    global _usage_tracker
    if _usage_tracker is None:
        raise RuntimeError("UsageTracker not initialized")
    return _usage_tracker
