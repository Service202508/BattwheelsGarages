"""
Plan Enforcement Middleware
===========================
Safety-net backend enforcement for subscription plan gating.
Only gates write operations (POST/PUT/PATCH/DELETE).
GET requests are allowed through (read-only browsing).
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# route_prefix → minimum plan required
PLAN_GATED_ROUTES = {
    "/api/v1/amc": "starter",
    "/api/v1/time-tracking": "professional",
    "/api/v1/sales-orders": "starter",
    "/api/v1/recurring": "professional",
    "/api/v1/credit-notes": "starter",
    "/api/v1/delivery-challans": "professional",
    "/api/v1/purchases": "starter",
    "/api/v1/bills": "starter",
    "/api/v1/vendor-credits": "professional",
    "/api/v1/stock-transfers": "professional",
    "/api/v1/serial-batch": "professional",
    "/api/v1/banking": "professional",
    "/api/v1/journal-entries": "professional",
    "/api/v1/hr": "professional",
    "/api/v1/employees": "professional",
    "/api/v1/attendance": "professional",
    "/api/v1/leave": "professional",
    "/api/v1/payroll": "professional",
    "/api/v1/projects": "professional",
    "/api/v1/knowledge-brain": "starter",
    "/api/v1/failure-intelligence": "professional",
    "/api/v1/fault-tree": "professional",
    "/api/v1/composite-items": "professional",
    "/api/v1/price-lists": "professional",
    "/api/v1/inventory-adjustments": "starter",
    "/api/v1/expenses": "starter",
    "/api/v1/recurring-expenses": "professional",
    "/api/v1/chart-of-accounts": "starter",
    "/api/v1/opening-balances": "professional",
    "/api/v1/period-locks": "professional",
    "/api/v1/branding": "professional",
    "/api/v1/data-management": "enterprise",
    "/api/v1/customer-portal": "professional",
    "/api/v1/documents": "starter",
}

PLAN_HIERARCHY = {
    "free": 0,
    "free_trial": 0,
    "starter": 1,
    "professional": 2,
    "enterprise": 3,
}

# Skip list — public or always-allowed prefixes
SKIP_PREFIXES = (
    "/api/auth",
    "/api/v1/auth",
    "/api/v1/organizations/signup",
    "/api/v1/organizations/my-organizations",
    "/health",
    "/api/health",
    "/docs",
    "/openapi",
)

_db = None

def set_plan_enforcement_db(db):
    global _db
    _db = db

class PlanEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Only gate write operations
        if request.method in ("GET", "OPTIONS", "HEAD"):
            return await call_next(request)

        path = request.url.path

        # Skip public endpoints
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        # Check if route is gated
        matched_prefix = None
        min_plan = None
        for route_prefix, required_plan in PLAN_GATED_ROUTES.items():
            if path.startswith(route_prefix):
                if matched_prefix is None or len(route_prefix) > len(matched_prefix):
                    matched_prefix = route_prefix
                    min_plan = required_plan

        if not matched_prefix:
            return await call_next(request)

        # Get org_id from tenant middleware
        org_id = getattr(request.state, "tenant_org_id", None)
        if not org_id:
            return await call_next(request)

        if _db is None:
            return await call_next(request)

        # Fetch org's plan
        try:
            org = await _db.organizations.find_one(
                {"organization_id": org_id},
                {"_id": 0, "plan_type": 1}
            )
            user_plan = (org.get("plan_type", "free_trial") if org else "free_trial").lower()
        except Exception:
            return await call_next(request)

        user_level = PLAN_HIERARCHY.get(user_plan, 0)
        required_level = PLAN_HIERARCHY.get(min_plan, 0)

        if user_level < required_level:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "plan_upgrade_required",
                    "message": f"This feature requires the {min_plan.replace('_', ' ').title()} plan or above.",
                    "current_plan": user_plan,
                    "required_plan": min_plan,
                    "upgrade_url": "/subscription",
                }
            )

        return await call_next(request)
