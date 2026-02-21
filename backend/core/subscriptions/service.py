"""
Subscription Service
====================

Core business logic for subscription and plan management.
Handles subscription lifecycle, usage tracking, and plan changes.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from .models import (
    Plan, PlanCode, PlanFeatures, PlanLimits,
    Subscription, SubscriptionCreate, SubscriptionUpdate,
    SubscriptionStatus, BillingCycle, UsageRecord,
    DEFAULT_PLANS, get_default_plan
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.plans = db.plans
        self.subscriptions = db.subscriptions
        self._plan_cache: Dict[str, Plan] = {}
    
    # ==================== PLAN MANAGEMENT ====================
    
    async def initialize_default_plans(self) -> List[Plan]:
        """Initialize default plans in database"""
        plans = []
        
        for plan_data in DEFAULT_PLANS:
            existing = await self.plans.find_one({"code": plan_data["code"].value})
            
            if not existing:
                plan = Plan(
                    code=plan_data["code"],
                    name=plan_data["name"],
                    description=plan_data["description"],
                    price_monthly=plan_data["price_monthly"],
                    price_annual=plan_data["price_annual"],
                    trial_days=plan_data["trial_days"],
                    support_level=plan_data["support_level"],
                    sort_order=plan_data["sort_order"],
                    features=plan_data["features"],
                    limits=plan_data["limits"]
                )
                await self.plans.insert_one(plan.model_dump())
                plans.append(plan)
                logger.info(f"Created default plan: {plan.name}")
            else:
                plans.append(Plan(**{k: v for k, v in existing.items() if k != "_id"}))
        
        # Refresh cache
        await self._refresh_plan_cache()
        
        return plans
    
    async def get_plan(self, plan_code: PlanCode) -> Optional[Plan]:
        """Get plan by code (cached)"""
        cache_key = plan_code.value
        
        if cache_key in self._plan_cache:
            return self._plan_cache[cache_key]
        
        doc = await self.plans.find_one({"code": plan_code.value}, {"_id": 0})
        if doc:
            plan = Plan(**doc)
            self._plan_cache[cache_key] = plan
            return plan
        
        return None
    
    async def get_plan_by_id(self, plan_id: str) -> Optional[Plan]:
        """Get plan by ID"""
        doc = await self.plans.find_one({"plan_id": plan_id}, {"_id": 0})
        return Plan(**doc) if doc else None
    
    async def list_plans(self, include_inactive: bool = False) -> List[Plan]:
        """List all available plans"""
        query = {} if include_inactive else {"is_active": True, "is_public": True}
        cursor = self.plans.find(query, {"_id": 0}).sort("sort_order", 1)
        return [Plan(**doc) async for doc in cursor]
    
    async def _refresh_plan_cache(self):
        """Refresh plan cache from database"""
        self._plan_cache.clear()
        cursor = self.plans.find({"is_active": True}, {"_id": 0})
        async for doc in cursor:
            plan = Plan(**doc)
            self._plan_cache[plan.code.value] = plan
    
    # ==================== SUBSCRIPTION MANAGEMENT ====================
    
    async def create_subscription(
        self,
        organization_id: str,
        data: SubscriptionCreate,
        created_by: Optional[str] = None
    ) -> Subscription:
        """Create a new subscription for an organization"""
        
        # Get plan
        plan = await self.get_plan(data.plan_code)
        if not plan:
            # Initialize default plans if missing
            await self.initialize_default_plans()
            plan = await self.get_plan(data.plan_code)
        
        now = datetime.now(timezone.utc)
        
        # Calculate periods
        if data.start_trial and plan.trial_days > 0:
            trial_end = now + timedelta(days=plan.trial_days)
            status = SubscriptionStatus.TRIALING
            period_start = now
            period_end = trial_end
        else:
            trial_end = None
            status = SubscriptionStatus.ACTIVE
            period_start = now
            if data.billing_cycle == BillingCycle.MONTHLY:
                period_end = now + timedelta(days=30)
            elif data.billing_cycle == BillingCycle.ANNUAL:
                period_end = now + timedelta(days=365)
            else:
                period_end = None
        
        subscription = Subscription(
            organization_id=organization_id,
            plan_id=plan.plan_id,
            plan_code=data.plan_code,
            status=status,
            billing_cycle=data.billing_cycle,
            current_period_start=period_start,
            current_period_end=period_end,
            trial_start=now if data.start_trial else None,
            trial_end=trial_end,
            payment_method=data.payment_method,
            created_by=created_by
        )
        
        await self.subscriptions.insert_one(subscription.model_dump())
        
        # Update organization with subscription reference
        await self.db.organizations.update_one(
            {"organization_id": organization_id},
            {
                "$set": {
                    "subscription_id": subscription.subscription_id,
                    "plan_type": data.plan_code.value,
                    "updated_at": now.isoformat()
                }
            }
        )
        
        logger.info(f"Created subscription {subscription.subscription_id} for org {organization_id} on plan {data.plan_code.value}")
        
        return subscription
    
    async def get_subscription(self, organization_id: str) -> Optional[Subscription]:
        """Get subscription for an organization"""
        doc = await self.subscriptions.find_one(
            {"organization_id": organization_id},
            {"_id": 0}
        )
        return Subscription(**doc) if doc else None
    
    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        doc = await self.subscriptions.find_one(
            {"subscription_id": subscription_id},
            {"_id": 0}
        )
        return Subscription(**doc) if doc else None
    
    async def update_subscription(
        self,
        organization_id: str,
        data: SubscriptionUpdate
    ) -> Optional[Subscription]:
        """Update subscription (plan change, cancellation, etc.)"""
        
        subscription = await self.get_subscription(organization_id)
        if not subscription:
            return None
        
        update_data = {"updated_at": datetime.now(timezone.utc)}
        
        # Plan change
        if data.plan_code and data.plan_code != subscription.plan_code:
            new_plan = await self.get_plan(data.plan_code)
            if new_plan:
                update_data["plan_id"] = new_plan.plan_id
                update_data["plan_code"] = data.plan_code.value
                
                # Also update organization
                await self.db.organizations.update_one(
                    {"organization_id": organization_id},
                    {"$set": {"plan_type": data.plan_code.value}}
                )
        
        # Billing cycle change
        if data.billing_cycle:
            update_data["billing_cycle"] = data.billing_cycle.value
        
        # Cancellation
        if data.cancel_at_period_end is not None:
            update_data["cancel_at_period_end"] = data.cancel_at_period_end
            if data.cancel_at_period_end:
                update_data["canceled_at"] = datetime.now(timezone.utc)
                update_data["cancellation_reason"] = data.cancellation_reason
        
        result = await self.subscriptions.find_one_and_update(
            {"organization_id": organization_id},
            {"$set": update_data},
            return_document=True,
            projection={"_id": 0}
        )
        
        return Subscription(**result) if result else None
    
    async def cancel_subscription(
        self,
        organization_id: str,
        reason: Optional[str] = None,
        immediate: bool = False
    ) -> Optional[Subscription]:
        """Cancel a subscription"""
        
        now = datetime.now(timezone.utc)
        
        update_data = {
            "canceled_at": now,
            "cancellation_reason": reason,
            "updated_at": now
        }
        
        if immediate:
            update_data["status"] = SubscriptionStatus.CANCELED.value
        else:
            update_data["cancel_at_period_end"] = True
        
        result = await self.subscriptions.find_one_and_update(
            {"organization_id": organization_id},
            {"$set": update_data},
            return_document=True,
            projection={"_id": 0}
        )
        
        if result:
            logger.info(f"Canceled subscription for org {organization_id}, immediate={immediate}")
        
        return Subscription(**result) if result else None
    
    async def reactivate_subscription(self, organization_id: str) -> Optional[Subscription]:
        """Reactivate a canceled subscription"""
        
        now = datetime.now(timezone.utc)
        
        result = await self.subscriptions.find_one_and_update(
            {"organization_id": organization_id},
            {
                "$set": {
                    "status": SubscriptionStatus.ACTIVE.value,
                    "cancel_at_period_end": False,
                    "canceled_at": None,
                    "cancellation_reason": None,
                    "updated_at": now
                }
            },
            return_document=True,
            projection={"_id": 0}
        )
        
        return Subscription(**result) if result else None
    
    # ==================== USAGE TRACKING ====================
    
    async def record_usage(
        self,
        organization_id: str,
        usage_type: str,
        increment: int = 1
    ) -> bool:
        """Record usage for a subscription"""
        
        field_map = {
            "invoices": "usage.invoices_created",
            "tickets": "usage.tickets_created",
            "vehicles": "usage.vehicles_added",
            "ai_calls": "usage.ai_calls_made",
            "api_calls": "usage.api_calls_made"
        }
        
        field = field_map.get(usage_type)
        if not field:
            return False
        
        result = await self.subscriptions.update_one(
            {"organization_id": organization_id},
            {
                "$inc": {field: increment},
                "$set": {"usage.last_updated": datetime.now(timezone.utc)}
            }
        )
        
        return result.modified_count > 0
    
    async def get_usage(self, organization_id: str) -> Optional[UsageRecord]:
        """Get current usage for an organization"""
        doc = await self.subscriptions.find_one(
            {"organization_id": organization_id},
            {"usage": 1, "_id": 0}
        )
        
        if doc and "usage" in doc:
            return UsageRecord(**doc["usage"])
        return None
    
    async def reset_usage(self, organization_id: str) -> bool:
        """Reset usage counters (called at period start)"""
        result = await self.subscriptions.update_one(
            {"organization_id": organization_id},
            {
                "$set": {
                    "usage": UsageRecord().model_dump(),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count > 0
    
    # ==================== SUBSCRIPTION LIFECYCLE ====================
    
    async def process_trial_expirations(self) -> int:
        """Process expired trials (cron job)"""
        now = datetime.now(timezone.utc)
        
        result = await self.subscriptions.update_many(
            {
                "status": SubscriptionStatus.TRIALING.value,
                "trial_end": {"$lt": now}
            },
            {
                "$set": {
                    "status": SubscriptionStatus.EXPIRED.value,
                    "updated_at": now
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Expired {result.modified_count} trial subscriptions")
        
        return result.modified_count
    
    async def process_period_renewals(self) -> int:
        """Process subscription renewals (cron job)"""
        now = datetime.now(timezone.utc)
        
        # Find subscriptions that need renewal
        cursor = self.subscriptions.find({
            "status": SubscriptionStatus.ACTIVE.value,
            "current_period_end": {"$lt": now},
            "cancel_at_period_end": False
        })
        
        renewed_count = 0
        
        async for doc in cursor:
            sub = Subscription(**{k: v for k, v in doc.items() if k != "_id"})
            
            # Calculate new period
            if sub.billing_cycle == BillingCycle.MONTHLY:
                new_end = now + timedelta(days=30)
            elif sub.billing_cycle == BillingCycle.ANNUAL:
                new_end = now + timedelta(days=365)
            else:
                continue
            
            # Reset usage and update period
            await self.subscriptions.update_one(
                {"subscription_id": sub.subscription_id},
                {
                    "$set": {
                        "current_period_start": now,
                        "current_period_end": new_end,
                        "usage": UsageRecord().model_dump(),
                        "updated_at": now
                    }
                }
            )
            renewed_count += 1
        
        if renewed_count > 0:
            logger.info(f"Renewed {renewed_count} subscriptions")
        
        return renewed_count
    
    async def process_cancellations(self) -> int:
        """Process end-of-period cancellations (cron job)"""
        now = datetime.now(timezone.utc)
        
        result = await self.subscriptions.update_many(
            {
                "cancel_at_period_end": True,
                "current_period_end": {"$lt": now}
            },
            {
                "$set": {
                    "status": SubscriptionStatus.CANCELED.value,
                    "updated_at": now
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Processed {result.modified_count} end-of-period cancellations")
        
        return result.modified_count
    
    # ==================== MIGRATION ====================
    
    async def migrate_existing_organizations(self) -> int:
        """Migrate existing organizations to subscription model"""
        
        # Ensure plans exist
        await self.initialize_default_plans()
        
        # Find orgs without subscription
        cursor = self.db.organizations.find(
            {"subscription_id": {"$exists": False}},
            {"organization_id": 1, "plan_type": 1, "created_at": 1}
        )
        
        migrated_count = 0
        
        async for org in cursor:
            org_id = org["organization_id"]
            plan_type = org.get("plan_type", "starter")
            
            # Map old plan_type to new PlanCode
            try:
                plan_code = PlanCode(plan_type)
            except ValueError:
                plan_code = PlanCode.STARTER
            
            # Create subscription (skip trial for existing orgs)
            data = SubscriptionCreate(
                plan_code=plan_code,
                billing_cycle=BillingCycle.MONTHLY,
                start_trial=False
            )
            
            await self.create_subscription(org_id, data)
            migrated_count += 1
        
        if migrated_count > 0:
            logger.info(f"Migrated {migrated_count} organizations to subscription model")
        
        return migrated_count


# ==================== SERVICE SINGLETON ====================

_subscription_service: Optional[SubscriptionService] = None


def init_subscription_service(db: AsyncIOMotorDatabase) -> SubscriptionService:
    """Initialize subscription service singleton"""
    global _subscription_service
    _subscription_service = SubscriptionService(db)
    logger.info("SubscriptionService initialized")
    return _subscription_service


def get_subscription_service() -> SubscriptionService:
    """Get subscription service singleton"""
    if _subscription_service is None:
        raise RuntimeError("SubscriptionService not initialized")
    return _subscription_service
