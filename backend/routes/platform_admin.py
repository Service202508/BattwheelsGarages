"""
Platform Admin Routes
======================

Battwheels (the SaaS operator) management layer.
Separate from org-level admin — this is the platform owner layer.

Only accessible by users with is_platform_admin: true in their user record.
No org context required — operates across ALL organisations.

Endpoints:
  GET  /api/platform/organizations     — List all orgs
  GET  /api/platform/organizations/:id — Org detail
  POST /api/platform/organizations/:id/suspend
  POST /api/platform/organizations/:id/activate
  PUT  /api/platform/organizations/:id/plan
  GET  /api/platform/metrics           — Platform-wide KPIs
  POST /api/platform/run-audit         — Run 103-test production audit
  GET  /api/platform/audit-status      — Last audit result
  POST /api/platform/users/make-admin  — Grant platform admin
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import os
import logging
import json
import asyncio
import time
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["Platform Admin"])

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]


# ==================== AUTH ====================

async def require_platform_admin(request: Request) -> dict:
    """Dependency: requires is_platform_admin=True on user record"""
    from utils.auth import get_current_user_from_request
    user = await get_current_user_from_request(request)
    if not user.get("is_platform_admin"):
        raise HTTPException(
            status_code=403,
            detail="Platform admin access required",
            headers={"X-Error-Code": "PLATFORM_ADMIN_REQUIRED"}
        )
    return user


# ==================== MODELS ====================

class ChangePlanRequest(BaseModel):
    plan_type: str  # free, starter, professional, enterprise

class MakeAdminRequest(BaseModel):
    email: EmailStr


# ==================== ENDPOINTS ====================

@router.get("/organizations")
async def list_organizations(request: Request, _=Depends(require_platform_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    plan: Optional[str] = Query(None),
    status: Optional[str] = Query(None),  # active, suspended
):
    """List all registered organisations with key metrics"""
    query: Dict[str, Any] = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    if plan:
        query["plan_type"] = plan
    if status == "suspended":
        query["is_active"] = False
    elif status == "active":
        query["is_active"] = True

    total = await db.organizations.count_documents(query)
    skip = (page - 1) * limit
    orgs_raw = await db.organizations.find(
        query,
        {"_id": 0, "organization_id": 1, "name": 1, "slug": 1, "plan_type": 1,
         "is_active": 1, "created_at": 1, "email": 1, "industry_type": 1,
         "total_users": 1, "total_vehicles": 1, "total_tickets": 1}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    # Enrich with live counts
    result = []
    for org in orgs_raw:
        org_id = org["organization_id"]
        member_count = await db.organization_users.count_documents(
            {"organization_id": org_id, "status": "active"}
        )
        # Determine suspension status
        suspended_at = None
        if not org.get("is_active"):
            susp = await db.organizations.find_one(
                {"organization_id": org_id}, {"suspension_reason": 1, "suspended_at": 1, "_id": 0}
            )
            suspended_at = susp.get("suspended_at") if susp else None

        result.append({
            **org,
            "member_count": member_count,
            "status": "active" if org.get("is_active", True) else "suspended",
            "suspended_at": suspended_at,
        })

    return {
        "organizations": result,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.get("/organizations/{org_id}")
async def get_organization_detail(request: Request, org_id: str, _=Depends(require_platform_admin),
):
    """Get full details for one organisation"""
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    # Enrich with live counts
    member_count = await db.organization_users.count_documents(
        {"organization_id": org_id, "status": "active"}
    )
    ticket_count = await db.tickets.count_documents({"organization_id": org_id})
    invoice_count = await db.invoices.count_documents({"organization_id": org_id})

    # Members list
    memberships = await db.organization_users.find(
        {"organization_id": org_id},
        {"_id": 0, "user_id": 1, "role": 1, "status": 1, "joined_at": 1}
    ).to_list(50)
    member_details = []
    for m in memberships:
        u = await db.users.find_one(
            {"user_id": m["user_id"]},
            {"_id": 0, "email": 1, "name": 1, "is_active": 1}
        )
        if u:
            member_details.append({**m, **u})

    return {
        **org,
        "member_count": member_count,
        "ticket_count": ticket_count,
        "invoice_count": invoice_count,
        "members": member_details,
        "status": "active" if org.get("is_active", True) else "suspended",
    }


@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(request: Request, org_id: str, _=Depends(require_platform_admin),
):
    """Suspend an organisation — all users get 403 on next request"""
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    now = datetime.now(timezone.utc).isoformat()
    await db.organizations.update_one(
        {"organization_id": org_id},
        {"$set": {
            "is_active": False,
            "suspended_at": now,
            "suspension_reason": "Suspended by platform admin",
        }}
    )
    logger.warning(f"[PLATFORM] Organisation {org_id} suspended by platform admin")
    return {"success": True, "message": f"Organisation '{org.get('name')}' suspended"}


@router.post("/organizations/{org_id}/activate")
async def activate_organization(request: Request, org_id: str, _=Depends(require_platform_admin),
):
    """Re-activate a suspended organisation"""
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    await db.organizations.update_one(
        {"organization_id": org_id},
        {"$set": {"is_active": True}, "$unset": {"suspended_at": "", "suspension_reason": ""}}
    )
    logger.info(f"[PLATFORM] Organisation {org_id} activated by platform admin")
    return {"success": True, "message": f"Organisation '{org.get('name')}' activated"}


@router.put("/organizations/{org_id}/plan")
async def change_organization_plan(request: Request, org_id: str, data: ChangePlanRequest, _=Depends(require_platform_admin),
):
    """Change subscription plan for an organisation"""
    valid_plans = ["free", "starter", "professional", "enterprise"]
    if data.plan_type not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {valid_plans}")

    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    await db.organizations.update_one(
        {"organization_id": org_id},
        {"$set": {"plan_type": data.plan_type, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    # Also update subscription record if it exists
    await db.subscriptions.update_one(
        {"organization_id": org_id},
        {"$set": {"plan_code": data.plan_type, "status": "active"}}
    )
    logger.info(f"[PLATFORM] Organisation {org_id} plan changed to {data.plan_type}")
    return {"success": True, "message": f"Plan updated to {data.plan_type}"}


@router.get("/metrics")
async def get_platform_metrics(request: Request, _=Depends(require_platform_admin),
):
    """Platform-wide summary metrics"""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_orgs = await db.organizations.count_documents({})
    active_orgs = await db.organizations.count_documents({"is_active": True})
    suspended_orgs = await db.organizations.count_documents({"is_active": False})
    new_this_month = await db.organizations.count_documents({
        "created_at": {"$gte": month_start.isoformat()}
    })
    total_users = await db.users.count_documents({"is_active": True})
    total_tickets = await db.tickets.count_documents({})

    # Orgs by plan
    by_plan_cursor = db.organizations.aggregate([
        {"$group": {"_id": "$plan_type", "count": {"$sum": 1}}}
    ])
    by_plan_raw = await by_plan_cursor.to_list(20)
    by_plan = {item["_id"] or "unknown": item["count"] for item in by_plan_raw}

    # New orgs last 6 months
    monthly_signups = []
    for i in range(5, -1, -1):
        m_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if i == 0:
            m_end = now
        else:
            m_end = (m_start + timedelta(days=32)).replace(day=1)
        count = await db.organizations.count_documents({
            "created_at": {
                "$gte": m_start.isoformat(),
                "$lt": m_end.isoformat()
            }
        })
        monthly_signups.append({
            "month": m_start.strftime("%b %Y"),
            "count": count
        })

    return {
        "total_organizations": total_orgs,
        "active_organizations": active_orgs,
        "suspended_organizations": suspended_orgs,
        "new_this_month": new_this_month,
        "total_users": total_users,
        "total_tickets": total_tickets,
        "organizations_by_plan": by_plan,
        "monthly_signups": monthly_signups,
    }


@router.get("/revenue-health")
async def get_revenue_health(request: Request, _=Depends(require_platform_admin),
):
    """Revenue & Health metrics: MRR by plan, trial pipeline, churn risk, recent signups"""
    PLAN_MRR = {"free": 0, "starter": 2999, "professional": 7999, "enterprise": 24999}

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # MRR by plan
    by_plan_cursor = db.organizations.aggregate([
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$plan_type", "count": {"$sum": 1}}}
    ])
    by_plan_raw = await by_plan_cursor.to_list(20)
    mrr_by_plan = []
    total_mrr = 0
    for item in by_plan_raw:
        plan = item["_id"] or "free"
        count = item["count"]
        mrr = PLAN_MRR.get(plan, 0) * count
        total_mrr += mrr
        mrr_by_plan.append({"plan": plan, "count": count, "mrr": mrr})
    mrr_by_plan.sort(key=lambda x: x["mrr"], reverse=True)

    # Trial pipeline — free / free_trial orgs
    trial_orgs = await db.organizations.find(
        {"plan_type": {"$in": ["free", "free_trial"]}, "is_active": True},
        {"_id": 0, "name": 1, "plan_type": 1, "created_at": 1, "email": 1}
    ).sort("created_at", -1).limit(10).to_list(10)

    # Churn risk — active orgs with no tickets in 30+ days
    all_active_orgs = await db.organizations.find(
        {"is_active": True},
        {"_id": 0, "organization_id": 1, "name": 1, "plan_type": 1, "created_at": 1}
    ).to_list(200)

    churn_risk = []
    for org in all_active_orgs:
        oid = org.get("organization_id")
        if not oid:
            continue
        # Skip very new orgs (< 7 days old)
        created = org.get("created_at", "")
        if created:
            try:
                created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                if (now - created_dt).days < 7:
                    continue
            except Exception:
                pass
        recent_ticket = await db.tickets.find_one(
            {"organization_id": oid, "created_at": {"$gte": thirty_days_ago.isoformat()}},
            {"_id": 0, "ticket_id": 1}
        )
        if not recent_ticket:
            churn_risk.append({
                "name": org.get("name"),
                "plan": org.get("plan_type", "free"),
                "days_since_activity": 30
            })

    # Recent signups — last 5 orgs
    recent_signups = await db.organizations.find(
        {},
        {"_id": 0, "name": 1, "plan_type": 1, "created_at": 1, "email": 1}
    ).sort("created_at", -1).limit(5).to_list(5)

    return {
        "total_mrr": total_mrr,
        "mrr_by_plan": mrr_by_plan,
        "trial_pipeline": {"count": len(trial_orgs), "orgs": trial_orgs},
        "churn_risk": {"count": len(churn_risk), "orgs": churn_risk},
        "recent_signups": recent_signups,
    }



@router.get("/activity")
async def get_platform_activity(request: Request, _=Depends(require_platform_admin),
):
    """Last 20 platform-level audit runs"""
    runs = await db.platform_audit_runs.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    return {"runs": runs, "total": len(runs)}


@router.get("/audit-status")
async def get_audit_status(request: Request, _=Depends(require_platform_admin),
):
    """Return the most recent audit run result"""
    last = await db.platform_audit_runs.find_one(
        {}, {"_id": 0}, sort=[("created_at", -1)]
    )
    return last or {}


@router.post("/run-audit")
async def run_platform_audit(request: Request, _=Depends(require_platform_admin),
):
    """
    Run the full 103-test CTO production audit as a subprocess.
    Stores result in platform_audit_runs (keeps last 10 runs).
    """
    audit_script = "/app/backend/tests/cto_audit_92.py"
    if not os.path.exists(audit_script):
        raise HTTPException(status_code=404, detail="Audit script not found")

    start_time = time.time()
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", audit_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=200)
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(status_code=504, detail="Audit timed out after 200 seconds")

        duration = round(time.time() - start_time, 1)

        # Read the JSON report written by the script
        report_path = "/app/test_reports/cto_audit_92.json"
        if not os.path.exists(report_path):
            raise HTTPException(status_code=500, detail="Audit ran but report file not found")

        with open(report_path) as f:
            report = json.load(f)

        result = {
            "total": report.get("total_tests", 0),
            "passed": report.get("passed", 0),
            "failed": report.get("failed", 0),
            "score_pct": report.get("pass_rate", 0.0),
            "failures": report.get("failures", []),
            "duration_seconds": duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Persist to DB
        await db.platform_audit_runs.insert_one(dict(result))

        # Keep only last 10 runs
        all_runs = await db.platform_audit_runs.find(
            {}, {"_id": 1}
        ).sort("created_at", -1).to_list(100)
        if len(all_runs) > 10:
            ids_to_delete = [r["_id"] for r in all_runs[10:]]
            await db.platform_audit_runs.delete_many({"_id": {"$in": ids_to_delete}})

        # Remove MongoDB _id before returning
        result.pop("created_at", None)
        logger.info(f"[PLATFORM] Audit complete: {result['passed']}/{result['total']} ({result['score_pct']}%)")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PLATFORM] Audit failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audit execution error: {str(e)}")


@router.post("/users/make-admin")
async def make_platform_admin(request: Request, data: MakeAdminRequest, _=Depends(require_platform_admin),
):
    """Grant platform admin status to a user by email"""
    user = await db.users.find_one({"email": data.email}, {"_id": 0, "user_id": 1, "name": 1})
    if not user:
        raise HTTPException(status_code=404, detail=f"No user found with email: {data.email}")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"is_platform_admin": True}}
    )
    logger.info(f"[PLATFORM] Platform admin granted to user {user['user_id']} ({data.email})")
    return {"success": True, "message": f"Platform admin granted to {data.email}"}


@router.post("/users/revoke-admin")
async def revoke_platform_admin(request: Request, data: MakeAdminRequest, _=Depends(require_platform_admin),
):
    """Revoke platform admin from a user"""
    user = await db.users.find_one({"email": data.email}, {"_id": 0, "user_id": 1})
    if not user:
        raise HTTPException(status_code=404, detail=f"No user found with email: {data.email}")

    # Cannot revoke from the last platform admin
    admin_count = await db.users.count_documents({"is_platform_admin": True})
    if admin_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot revoke the last platform admin")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"is_platform_admin": False}}
    )
    return {"success": True, "message": f"Platform admin revoked from {data.email}"}


@router.get("/environment")
async def get_platform_environment(request: Request, _=Depends(require_platform_admin)):
    """Return the current deployment environment (production/staging/development)"""
    env = os.environ.get("ENVIRONMENT", "development")
    return {"environment": env}


def init_platform_admin_router(app_db):
    global db
    db = app_db
    return router


# ==================== LEADS (DEMO REQUESTS) ====================

LEAD_STATUSES = ["new", "called", "qualified", "closed_won", "closed_lost"]

class LeadStatusUpdate(BaseModel):
    status: str

class LeadNotesUpdate(BaseModel):
    notes: str


@router.get("/leads")
async def list_leads(request: Request, _=Depends(require_platform_admin),
    status: Optional[str] = Query(None),
):
    """List all demo requests with summary stats. Platform admin only."""
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    query = {}
    if status:
        query["status"] = status

    leads_raw = await db.demo_requests.find(query, {"_id": 0}).sort("submitted_at", -1).to_list(500)

    # Summary stats
    total = await db.demo_requests.count_documents({})
    new_this_week = await db.demo_requests.count_documents({"submitted_at": {"$gte": week_ago}})
    qualified = await db.demo_requests.count_documents({"status": "qualified"})
    closed_won = await db.demo_requests.count_documents({"status": "closed_won"})
    conversion_rate = round((closed_won / total) * 100, 1) if total > 0 else 0

    return {
        "leads": leads_raw,
        "summary": {
            "total": total,
            "new_this_week": new_this_week,
            "qualified": qualified,
            "closed_won": closed_won,
            "conversion_rate": conversion_rate,
        }
    }


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    data: LeadStatusUpdate,
    _=Depends(require_platform_admin),
):
    """Update the status of a demo request lead."""
    if data.status not in LEAD_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {LEAD_STATUSES}")

    result = await db.demo_requests.update_one(
        {"lead_id": lead_id},
        {"$set": {"status": data.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "lead_id": lead_id, "status": data.status}


@router.patch("/leads/{lead_id}/notes")
async def update_lead_notes(
    lead_id: str,
    data: LeadNotesUpdate,
    _=Depends(require_platform_admin),
):
    """Save call notes for a demo request lead."""
    result = await db.demo_requests.update_one(
        {"lead_id": lead_id},
        {"$set": {"notes": data.notes, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "lead_id": lead_id}



# ==================== FEATURE FLAGS ====================

class FeatureFlagCreate(BaseModel):
    feature_key: str
    name: str
    description: str = ""
    status: str = "off"  # off | canary | percentage | on
    canary_org_ids: List[str] = []
    percentage: int = 0
    version_introduced: str = ""

class FeatureFlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    canary_org_ids: Optional[List[str]] = None
    percentage: Optional[int] = None


@router.get("/feature-flags")
async def list_feature_flags(_=Depends(require_platform_admin)):
    """List all feature flags (platform admin only)"""
    flags = await db.feature_flags.find({}, {"_id": 0}).to_list(100)
    return {"data": flags}


@router.post("/feature-flags")
async def create_feature_flag(data: FeatureFlagCreate, _=Depends(require_platform_admin)):
    """Create a new feature flag"""
    existing = await db.feature_flags.find_one({"feature_key": data.feature_key})
    if existing:
        raise HTTPException(status_code=409, detail="Feature flag with this key already exists")
    
    flag = {
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.feature_flags.insert_one(flag)
    flag.pop("_id", None)
    return flag


@router.put("/feature-flags/{key}")
async def update_feature_flag(key: str, data: FeatureFlagUpdate, _=Depends(require_platform_admin)):
    """Update a feature flag"""
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.feature_flags.update_one(
        {"feature_key": key},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    updated = await db.feature_flags.find_one({"feature_key": key}, {"_id": 0})
    return updated


@router.delete("/feature-flags/{key}")
async def delete_feature_flag(key: str, _=Depends(require_platform_admin)):
    """Delete a feature flag"""
    result = await db.feature_flags.delete_one({"feature_key": key})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return {"success": True, "deleted": key}


# ==================== VERSION ====================

@router.get("/version")
async def get_platform_version():
    """Public endpoint: Returns platform version info"""
    from config.platform import PLATFORM_VERSION, RELEASE_DATE, CHANGELOG_URL
    return {
        "version": PLATFORM_VERSION,
        "release_date": RELEASE_DATE,
        "changelog_url": CHANGELOG_URL,
    }


# ==================== EFI BRAIN SEEDING ====================

@router.post("/efi/seed-brain")
async def seed_efi_brain(request: Request, _=Depends(require_platform_admin)):
    """
    Seed the EFI brain with initial failure card data.
    Sprint 3B-SEED: Populates failure_cards + efi_decision_trees
    with common Indian EV failure patterns and generates embeddings.
    
    Requires platform_admin role.
    Idempotent — skips cards that already exist.
    """
    try:
        from services.efi_seed_data import seed_failure_cards_and_trees
        result = await seed_failure_cards_and_trees(db)
        return {
            "success": True,
            "message": "EFI brain seeding complete",
            **result
        }
    except Exception as e:
        logger.error(f"EFI brain seeding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
