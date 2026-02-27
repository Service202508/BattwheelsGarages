"""
Subscription Routes
===================

API endpoints for subscription and plan management.
Includes Razorpay subscription checkout flow.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import os, logging, uuid

from core.subscriptions import (
    Plan, PlanCode, 
    Subscription, SubscriptionCreate, SubscriptionUpdate,
    SubscriptionStatus, BillingCycle,
    get_subscription_service
)
from core.tenant.context import TenantContext, tenant_context_required

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


# ==================== PLAN ENDPOINTS ====================

@router.get("/plans", response_model=List[dict])
async def list_plans():
    """List all available subscription plans (public)"""
    service = get_subscription_service()
    plans = await service.list_plans()
    
    result = []
    for plan in plans:
        # Handle features - could be dict or PlanFeatures object
        if hasattr(plan.features, 'model_dump'):
            features_dict = plan.features.model_dump()
            features = {
                k: {"enabled": v.get("enabled", v) if isinstance(v, dict) else v.enabled, 
                    "limit": v.get("limit") if isinstance(v, dict) else v.limit}
                for k, v in features_dict.items()
            }
        else:
            features = plan.features if isinstance(plan.features, dict) else {}
        
        # Handle limits
        if hasattr(plan.limits, 'model_dump'):
            limits = plan.limits.model_dump()
        else:
            limits = plan.limits if isinstance(plan.limits, dict) else {}
        
        result.append({
            "plan_id": plan.plan_id,
            "code": plan.code.value if hasattr(plan.code, 'value') else plan.code,
            "name": plan.name,
            "description": plan.description,
            "price_monthly": plan.price_monthly,
            "price_annual": plan.price_annual,
            "currency": plan.currency,
            "trial_days": plan.trial_days,
            "support_level": plan.support_level,
            "features": features,
            "limits": limits
        })
    
    return result


@router.get("/plans/compare", response_model=List[dict])
async def compare_plans():
    """
    Get a comparison of all available plans with features.
    
    This is a public endpoint for displaying pricing pages.
    """
    from core.subscriptions.entitlement import get_entitlement_service
    
    entitlement = get_entitlement_service()
    return await entitlement.get_plan_comparison()


@router.get("/plans/{plan_code}", response_model=dict)
async def get_plan(plan_code: str):
    """Get details of a specific plan"""
    try:
        code = PlanCode(plan_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    service = get_subscription_service()
    plan = await service.get_plan(code)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Handle features - could be dict or PlanFeatures object
    if hasattr(plan.features, 'model_dump'):
        features_dict = plan.features.model_dump()
        features = {
            k: {"enabled": v.get("enabled", v) if isinstance(v, dict) else v.enabled, 
                "limit": v.get("limit") if isinstance(v, dict) else v.limit}
            for k, v in features_dict.items()
        }
    else:
        features = plan.features if isinstance(plan.features, dict) else {}
    
    # Handle limits
    if hasattr(plan.limits, 'model_dump'):
        limits = plan.limits.model_dump()
    else:
        limits = plan.limits if isinstance(plan.limits, dict) else {}
    
    return {
        "plan_id": plan.plan_id,
        "code": plan.code.value if hasattr(plan.code, 'value') else plan.code,
        "name": plan.name,
        "description": plan.description,
        "price_monthly": plan.price_monthly,
        "price_annual": plan.price_annual,
        "currency": plan.currency,
        "trial_days": plan.trial_days,
        "support_level": plan.support_level,
        "features": features,
        "limits": limits
    }


# ==================== SUBSCRIPTION ENDPOINTS ====================

@router.get("/current", response_model=dict)
async def get_current_subscription(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get current organization's subscription"""
    service = get_subscription_service()
    subscription = await service.get_subscription(ctx.org_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Get plan details
    plan = await service.get_plan(subscription.plan_code)
    
    return {
        "subscription_id": subscription.subscription_id,
        "organization_id": subscription.organization_id,
        "plan": {
            "code": subscription.plan_code.value,
            "name": plan.name if plan else subscription.plan_code.value.title(),
            "price_monthly": plan.price_monthly if plan else 0,
            "price_annual": plan.price_annual if plan else 0
        },
        "status": subscription.status.value,
        "billing_cycle": subscription.billing_cycle.value,
        "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "is_active": subscription.is_active(),
        "is_in_trial": subscription.is_in_trial(),
        "usage": subscription.usage.model_dump() if subscription.usage else None
    }


@router.get("/usage", response_model=dict)
async def get_subscription_usage(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get current subscription usage statistics"""
    service = get_subscription_service()
    subscription = await service.get_subscription(ctx.org_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    plan = await service.get_plan(subscription.plan_code)
    
    usage = subscription.usage
    limits = plan.limits if plan else None
    
    def format_usage(used: int, limit: int) -> dict:
        if limit == -1:
            return {"used": used, "limit": "unlimited", "percent": 0}
        elif limit == 0:
            return {"used": used, "limit": 0, "percent": 100 if used > 0 else 0}
        else:
            return {"used": used, "limit": limit, "percent": round((used / limit) * 100, 1)}
    
    return {
        "period": {
            "start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        },
        "usage": {
            "invoices": format_usage(usage.invoices_created, limits.max_invoices_per_month if limits else 0),
            "tickets": format_usage(usage.tickets_created, limits.max_tickets_per_month if limits else 0),
            "vehicles": format_usage(usage.vehicles_added, limits.max_vehicles if limits else 0),
            "ai_calls": format_usage(usage.ai_calls_made, limits.max_ai_calls_per_month if limits else 0),
            "api_calls": format_usage(usage.api_calls_made, limits.max_api_calls_per_day if limits else 0),
            "storage_mb": usage.storage_used_mb
        },
        "last_updated": usage.last_updated.isoformat() if usage.last_updated else None
    }


@router.post("/change-plan", response_model=dict)
async def change_plan(
    plan_code: str,
    billing_cycle: Optional[str] = None,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Change subscription plan"""
    # Verify permission
    ctx.require_permission("org:billing:update")
    
    try:
        new_plan_code = PlanCode(plan_code)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan code")
    
    service = get_subscription_service()
    
    # Get current subscription
    current_sub = await service.get_subscription(ctx.org_id)
    if not current_sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Prepare update
    update_data = SubscriptionUpdate(plan_code=new_plan_code)
    
    if billing_cycle:
        try:
            update_data.billing_cycle = BillingCycle(billing_cycle)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid billing cycle")
    
    # Update subscription
    updated = await service.update_subscription(ctx.org_id, update_data)
    
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update subscription")
    
    return {
        "success": True,
        "message": f"Plan changed to {new_plan_code.value}",
        "subscription_id": updated.subscription_id,
        "new_plan": updated.plan_code.value,
        "effective_date": datetime.now(timezone.utc).isoformat()
    }


@router.post("/cancel", response_model=dict)
async def cancel_subscription(
    reason: Optional[str] = None,
    immediate: bool = False,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Cancel subscription"""
    ctx.require_permission("org:billing:update")
    
    service = get_subscription_service()
    
    result = await service.cancel_subscription(
        ctx.org_id, 
        reason=reason, 
        immediate=immediate
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    return {
        "success": True,
        "message": "Subscription canceled" if immediate else "Subscription will be canceled at end of billing period",
        "cancel_at_period_end": result.cancel_at_period_end,
        "current_period_end": result.current_period_end.isoformat() if result.current_period_end else None
    }


@router.post("/reactivate", response_model=dict)
async def reactivate_subscription(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Reactivate a canceled subscription"""
    ctx.require_permission("org:billing:update")
    
    service = get_subscription_service()
    
    result = await service.reactivate_subscription(ctx.org_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    return {
        "success": True,
        "message": "Subscription reactivated",
        "status": result.status.value
    }


# ==================== RAZORPAY SUBSCRIPTION CHECKOUT ====================

def _get_razorpay_client():
    """Get Razorpay client using env credentials."""
    import razorpay
    key_id = os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))


def _get_db():
    """Get MongoDB database handle."""
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    return client[os.environ.get("DB_NAME", "battwheels_dev")]


class SubscribeRequest(BaseModel):
    plan_code: str
    billing_cycle: str = "monthly"


@router.post("/subscribe", response_model=dict)
async def subscribe_to_plan(
    data: SubscribeRequest,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Initiate a Razorpay subscription for the org.
    Returns subscription_id and checkout data for the frontend.
    """
    ctx.require_permission("org:billing:update")

    rp = _get_razorpay_client()
    if not rp:
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    # Resolve plan
    service = get_subscription_service()
    try:
        plan_code = PlanCode(data.plan_code)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan code")

    plan = await service.get_plan(plan_code)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.price_monthly == 0:
        raise HTTPException(status_code=400, detail="Free plan does not require payment")

    db = _get_db()

    # Get or create Razorpay Plan ID for this plan+cycle
    amount_paise = int(plan.price_monthly * 100) if data.billing_cycle == "monthly" else int(plan.price_annual * 100)
    period = "monthly" if data.billing_cycle == "monthly" else "yearly"
    interval = 1

    rp_plan_doc = await db.razorpay_plans.find_one(
        {"plan_code": plan_code.value, "period": period},
        {"_id": 0}
    )

    if not rp_plan_doc:
        # Create plan in Razorpay
        try:
            rp_plan = rp.plan.create({
                "period": period,
                "interval": interval,
                "item": {
                    "name": f"Battwheels {plan.name} ({period.title()})",
                    "amount": amount_paise,
                    "currency": "INR",
                    "description": plan.description or f"{plan.name} plan"
                }
            })
            rp_plan_doc = {
                "razorpay_plan_id": rp_plan["id"],
                "plan_code": plan_code.value,
                "period": period,
                "amount_paise": amount_paise,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.razorpay_plans.insert_one(rp_plan_doc)
            logger.info(f"Created Razorpay plan {rp_plan['id']} for {plan_code.value}/{period}")
        except Exception as e:
            logger.error(f"Failed to create Razorpay plan: {e}")
            raise HTTPException(status_code=502, detail=f"Payment gateway error: {str(e)}")

    # Get org for customer info
    org = await db.organizations.find_one(
        {"organization_id": ctx.org_id},
        {"_id": 0, "name": 1, "admin_email": 1, "phone": 1}
    )

    # Create Razorpay Subscription
    try:
        rp_sub = rp.subscription.create({
            "plan_id": rp_plan_doc["razorpay_plan_id"],
            "total_count": 12 if period == "monthly" else 3,
            "quantity": 1,
            "customer_notify": 1,
            "notes": {
                "org_id": ctx.org_id,
                "org_name": org.get("name", "") if org else "",
                "plan_name": plan.name,
                "plan_code": plan_code.value,
                "billing_cycle": period
            }
        })
    except Exception as e:
        logger.error(f"Failed to create Razorpay subscription: {e}")
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {str(e)}")

    # Store subscription reference
    await db.subscription_orders.insert_one({
        "subscription_order_id": f"subord_{uuid.uuid4().hex[:12]}",
        "organization_id": ctx.org_id,
        "razorpay_subscription_id": rp_sub["id"],
        "razorpay_plan_id": rp_plan_doc["razorpay_plan_id"],
        "plan_code": plan_code.value,
        "billing_cycle": period,
        "amount_paise": amount_paise,
        "status": rp_sub.get("status", "created"),
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {
        "success": True,
        "razorpay_subscription_id": rp_sub["id"],
        "razorpay_key_id": os.environ.get("RAZORPAY_KEY_ID", ""),
        "amount_paise": amount_paise,
        "plan_name": plan.name,
        "short_url": rp_sub.get("short_url"),
        "status": rp_sub.get("status"),
        "notes": rp_sub.get("notes", {})
    }


@router.post("/cancel-razorpay", response_model=dict)
async def cancel_razorpay_subscription(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Cancel the active Razorpay subscription for the org.
    The org stays active until the current billing period ends.
    """
    ctx.require_permission("org:billing:update")

    rp = _get_razorpay_client()
    if not rp:
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    db = _get_db()

    # Find the active subscription order
    sub_order = await db.subscription_orders.find_one(
        {"organization_id": ctx.org_id, "status": {"$in": ["active", "authenticated", "created"]}},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if not sub_order:
        raise HTTPException(status_code=404, detail="No active Razorpay subscription found")

    rp_sub_id = sub_order["razorpay_subscription_id"]

    try:
        rp.subscription.cancel(rp_sub_id, {"cancel_at_cycle_end": 1})
    except Exception as e:
        logger.error(f"Failed to cancel Razorpay subscription: {e}")
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {str(e)}")

    # Update local record
    await db.subscription_orders.update_one(
        {"razorpay_subscription_id": rp_sub_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )

    # Mark subscription as cancel_at_period_end
    service = get_subscription_service()
    await service.cancel_subscription(ctx.org_id, reason="User cancelled via Razorpay", immediate=False)

    return {
        "success": True,
        "message": "Subscription will cancel at end of current billing period",
        "razorpay_subscription_id": rp_sub_id
    }


@router.get("/payment-history", response_model=dict)
async def get_payment_history(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get subscription payment history for the org."""
    db = _get_db()

    payments = await db.subscription_payments.find(
        {"organization_id": ctx.org_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)

    return {"payments": payments, "count": len(payments)}


# ==================== ADMIN ENDPOINTS ====================

@router.post("/admin/initialize-plans", response_model=dict)
async def admin_initialize_plans(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Initialize default plans (admin only)"""
    ctx.require_permission("org:settings:update")
    
    service = get_subscription_service()
    plans = await service.initialize_default_plans()
    
    return {
        "success": True,
        "plans_created": len(plans),
        "plans": [p.name for p in plans]
    }


@router.post("/admin/migrate-organizations", response_model=dict)
async def admin_migrate_organizations(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Migrate existing organizations to subscription model (admin only)"""
    ctx.require_permission("org:settings:update")
    
    service = get_subscription_service()
    count = await service.migrate_existing_organizations()
    
    return {
        "success": True,
        "organizations_migrated": count
    }


@router.post("/admin/process-lifecycle", response_model=dict)
async def admin_process_lifecycle(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Process subscription lifecycle events (admin/cron)"""
    ctx.require_permission("org:settings:update")
    
    service = get_subscription_service()
    
    trials_expired = await service.process_trial_expirations()
    renewals = await service.process_period_renewals()
    cancellations = await service.process_cancellations()
    
    return {
        "success": True,
        "trials_expired": trials_expired,
        "subscriptions_renewed": renewals,
        "cancellations_processed": cancellations
    }



# ==================== ENTITLEMENT ENDPOINTS ====================

@router.get("/entitlements", response_model=dict)
async def get_entitlements(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Get all feature entitlements for the current organization.
    
    Returns a dictionary of feature keys with their availability status.
    """
    from core.subscriptions.entitlement import get_entitlement_service
    
    entitlement = get_entitlement_service()
    features = await entitlement.get_available_features(ctx.org_id)
    
    # Get subscription for additional context
    subscription = await entitlement.get_subscription(ctx.org_id)
    
    return {
        "organization_id": ctx.org_id,
        "plan": subscription.plan_code.value if subscription else None,
        "status": subscription.status.value if subscription else None,
        "features": features,
        "is_active": subscription.is_active() if subscription else False,
        "is_trial": subscription.is_in_trial() if subscription else False
    }


@router.get("/entitlements/{feature}", response_model=dict)
async def check_feature_entitlement(
    feature: str,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Check if a specific feature is available for the current organization.
    
    Returns detailed information about the feature access.
    """
    from core.subscriptions.entitlement import get_entitlement_service
    
    entitlement = get_entitlement_service()
    
    # Check if feature exists
    min_plan = entitlement.get_minimum_plan_for_feature(feature)
    if min_plan is None:
        raise HTTPException(status_code=404, detail=f"Unknown feature: {feature}")
    
    # Get access status
    enabled, limit = await entitlement.get_feature_limit(ctx.org_id, feature)
    
    # Get subscription for context
    subscription = await entitlement.get_subscription(ctx.org_id)
    
    response = {
        "feature": feature,
        "enabled": enabled,
        "limit": limit,
        "minimum_plan_required": min_plan.value,
        "current_plan": subscription.plan_code.value if subscription else None
    }
    
    if not enabled and subscription:
        response["upgrade_to"] = entitlement._get_upgrade_suggestion(feature, subscription.plan_code)
    
    return response


@router.get("/limits", response_model=dict)
async def get_usage_limits(
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Get usage limits and current usage for the organization.
    """
    service = get_subscription_service()
    subscription = await service.get_subscription(ctx.org_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    plan = await service.get_plan(subscription.plan_code)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    usage = subscription.usage
    limits = plan.limits
    
    def format_limit(current: int, limit: int) -> dict:
        if limit == -1:
            return {"current": current, "limit": "unlimited", "percent": 0, "remaining": "unlimited"}
        elif limit == 0:
            return {"current": current, "limit": 0, "percent": 100, "remaining": 0}
        else:
            percent = round((current / limit) * 100, 1) if limit > 0 else 0
            return {"current": current, "limit": limit, "percent": percent, "remaining": max(0, limit - current)}
    
    return {
        "organization_id": ctx.org_id,
        "plan": subscription.plan_code.value,
        "billing_cycle": subscription.billing_cycle.value,
        "period": {
            "start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        },
        "limits": {
            "invoices": format_limit(usage.invoices_created, limits.max_invoices_per_month),
            "tickets": format_limit(usage.tickets_created, limits.max_tickets_per_month),
            "vehicles": format_limit(usage.vehicles_added, limits.max_vehicles),
            "ai_calls": format_limit(usage.ai_calls_made, limits.max_ai_calls_per_month),
            "api_calls": format_limit(usage.api_calls_made, limits.max_api_calls_per_day),
            "users": {"limit": limits.max_users if limits.max_users != -1 else "unlimited"},
            "technicians": {"limit": limits.max_technicians if limits.max_technicians != -1 else "unlimited"},
            "storage_gb": {"limit": limits.max_storage_gb if limits.max_storage_gb != -1 else "unlimited"}
        }
    }
