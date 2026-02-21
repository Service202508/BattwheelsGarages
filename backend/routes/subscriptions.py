"""
Subscription Routes
===================

API endpoints for subscription and plan management.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timezone

from core.subscriptions import (
    Plan, PlanCode, 
    Subscription, SubscriptionCreate, SubscriptionUpdate,
    SubscriptionStatus, BillingCycle,
    get_subscription_service
)
from core.tenant.context import TenantContext, tenant_context_required

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


# ==================== PLAN ENDPOINTS ====================

@router.get("/plans", response_model=List[dict])
async def list_plans():
    """List all available subscription plans (public)"""
    service = get_subscription_service()
    plans = await service.list_plans()
    
    return [
        {
            "plan_id": plan.plan_id,
            "code": plan.code.value,
            "name": plan.name,
            "description": plan.description,
            "price_monthly": plan.price_monthly,
            "price_annual": plan.price_annual,
            "currency": plan.currency,
            "trial_days": plan.trial_days,
            "support_level": plan.support_level,
            "features": {
                k: {"enabled": v.enabled, "limit": v.limit}
                for k, v in plan.features.model_dump().items()
            },
            "limits": plan.limits.model_dump()
        }
        for plan in plans
    ]


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
    
    return {
        "plan_id": plan.plan_id,
        "code": plan.code.value,
        "name": plan.name,
        "description": plan.description,
        "price_monthly": plan.price_monthly,
        "price_annual": plan.price_annual,
        "currency": plan.currency,
        "trial_days": plan.trial_days,
        "support_level": plan.support_level,
        "features": {
            k: {"enabled": v.enabled, "limit": v.limit}
            for k, v in plan.features.model_dump().items()
        },
        "limits": plan.limits.model_dump()
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
