"""
Battwheels OS - RBAC Middleware
================================

CRITICAL SECURITY COMPONENT

Enforces role-based access control at the middleware level.
Works in conjunction with TenantIsolationMiddleware.

Security Principles:
1. DENY by default - routes not in ROUTE_PERMISSIONS are blocked
2. Check role from JWT against allowed roles for route
3. Log all unauthorized access attempts
"""

import re
import logging
from typing import List, Dict, Callable, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Role hierarchy (higher roles inherit lower role permissions)
ROLE_HIERARCHY = {
    "platform_admin": ["platform_admin", "owner", "org_admin", "admin", "manager", "accountant", "hr", "technician", "dispatcher", "viewer"],
    "org_admin": ["org_admin", "manager", "accountant", "technician", "dispatcher", "viewer"],
    "owner": ["owner", "org_admin", "manager", "accountant", "hr", "technician", "dispatcher", "viewer"],
    "admin": ["admin", "org_admin", "manager", "accountant", "hr", "technician", "dispatcher", "viewer"],
    "manager": ["manager", "technician", "dispatcher", "viewer"],
    "hr": ["hr", "viewer"],
    "accountant": ["accountant", "viewer"],
    "technician": ["technician", "viewer"],
    "dispatcher": ["dispatcher", "viewer"],
    "customer": ["customer"],
    "fleet_customer": ["fleet_customer", "customer"],
    "viewer": ["viewer"],
}

# Route permissions mapping
# Pattern -> List of allowed roles
ROUTE_PERMISSIONS: Dict[str, List[str]] = {
    # ============ FINANCE ROUTES (Restricted) ============
    r"^/api/finance(/.*)?$":           ["org_admin", "admin", "owner", "accountant"],
    r"^/api/banking(/.*)?$":           ["org_admin", "admin", "owner", "accountant"],
    r"^/api/banking-module(/.*)?$":    ["org_admin", "admin", "owner", "accountant"],
    r"^/api/journal.*$":            ["org_admin", "admin", "owner", "accountant"],
    r"^/api/chart-of-accounts.*$":  ["org_admin", "admin", "owner", "accountant"],
    
    # ============ HR/PAYROLL (Admin + HR) ============
    r"^/api/hr/payroll.*$":         ["org_admin", "admin", "owner", "hr"],
    r"^/api/hr/employees.*$":       ["org_admin", "admin", "owner", "manager", "hr"],
    r"^/api/hr/attendance.*$":      ["org_admin", "admin", "owner", "manager", "hr", "technician", "accountant"],
    r"^/api/hr/leave.*$":           ["org_admin", "admin", "owner", "manager", "hr", "technician", "accountant"],
    r"^/api/hr(/.*)?$":                ["org_admin", "admin", "owner", "hr"],
    r"^/api/payroll(/.*)?$":           ["org_admin", "admin", "owner", "hr"],
    
    # ============ INVOICING ============
    r"^/api/invoices(/.*)?$":          ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/bills(/.*)?$":             ["org_admin", "admin", "owner", "accountant"],
    r"^/api/expenses(/.*)?$":          ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/credit-notes(/.*)?$":      ["org_admin", "admin", "owner", "accountant"],
    r"^/api/payments.*$":           ["org_admin", "admin", "owner", "accountant"],
    
    # ============ ESTIMATES/QUOTES ============
    r"^/api/estimates(/.*)?$":         ["org_admin", "admin", "owner", "manager", "technician", "dispatcher"],
    r"^/api/ticket-estimates(/.*)?$":  ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/sales-orders(/.*)?$":      ["org_admin", "admin", "owner", "manager", "accountant"],
    
    # ============ OPERATIONS ============
    r"^/api/tickets(/.*)?$":           ["org_admin", "admin", "owner", "manager", "technician", "dispatcher"],
    r"^/api/job-cards(/.*)?$":         ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/vehicles(/.*)?$":          ["org_admin", "admin", "owner", "manager", "technician", "dispatcher"],
    
    # ============ INVENTORY ============
    r"^/api/inventory(/.*)?$":         ["org_admin", "admin", "owner", "manager", "accountant", "technician"],
    r"^/api/items(/.*)?$":             ["org_admin", "admin", "owner", "manager", "accountant", "technician"],
    r"^/api/allocations(/.*)?$":       ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/stock.*$":              ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/composite-items(/.*)?$":   ["org_admin", "admin", "owner", "manager"],
    r"^/api/purchase-orders(/.*)?$":   ["org_admin", "admin", "owner", "accountant"],
    
    # ============ CONTACTS/CRM ============
    r"^/api/contacts(/.*)?$":          ["org_admin", "admin", "owner", "manager", "dispatcher"],
    r"^/api/suppliers(/.*)?$":         ["org_admin", "admin", "owner", "accountant"],
    r"^/api/customers(/.*)?$":         ["org_admin", "admin", "owner", "manager", "dispatcher"],
    
    # ============ EVFI/AI (Operations) ============
    r"^/api/e?v?fi(/.*)?$":               ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/ai(/.*)?$":                ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/failure.*$":            ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/knowledge.*$":          ["org_admin", "admin", "owner", "manager", "technician"],
    
    # ============ REPORTS ============
    r"^/api/reports(/.*)?$":           ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/gst(/.*)?$":               ["org_admin", "admin", "owner", "accountant"],
    r"^/api/productivity(/.*)?$":      ["org_admin", "admin", "owner", "manager", "hr"],
    
    # ============ AUTHENTICATED AUTH ROUTES ============
    r"^/api/auth/change-password$":     ["org_admin", "admin", "owner", "manager", "accountant", "hr", "technician", "dispatcher", "viewer"],
    r"^/api/auth/switch-organization$": ["org_admin", "admin", "owner", "manager", "accountant", "hr", "technician", "dispatcher", "viewer"],
    r"^/api/employees(/.*)?$":          ["org_admin", "admin", "owner", "hr"],
    
    # ============ SETTINGS/ADMIN ============
    r"^/api/organizations/settings.*$": ["org_admin", "admin", "owner"],
    r"^/api/organizations/users.*$":    ["org_admin", "admin", "owner"],
    r"^/api/organizations(/.*)?$":         ["org_admin", "admin", "owner", "manager", "accountant", "technician", "viewer"],
    r"^/api/settings(/.*)?$":              ["org_admin", "admin", "owner"],
    r"^/api/permissions(/.*)?$":           ["org_admin", "admin", "owner"],
    r"^/api/users(/.*)?$":                 ["org_admin", "admin", "owner"],
    r"^/api/technicians$":              ["org_admin", "admin", "owner", "manager", "dispatcher"],
    
    # ============ PLATFORM ADMIN (Battwheels operator only) ============
    r"^/api/platform(/.*)?$":              ["platform_admin", "owner", "admin"],
    r"^/api/v1/platform(/.*)?$":           ["platform_admin", "owner", "admin"],
    
    # ============ DOCUMENT MANAGEMENT ============
    r"^/api/documents(/.*)?$":         ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/uploads(/.*)?$":           ["org_admin", "admin", "owner", "manager", "technician", "accountant"],
    r"^/api/pdf-templates(/.*)?$":     ["org_admin", "admin", "owner", "accountant"],
    
    # ============ INTEGRATIONS ============
    r"^/api/razorpay(/.*)?$":          ["org_admin", "admin", "owner", "accountant"],
    r"^/api/einvoice(/.*)?$":          ["org_admin", "admin", "owner", "accountant"],
    r"^/api/zoho(/.*)?$":              ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/v1/zoho(/.*)?$":           ["org_admin", "admin", "owner", "accountant", "manager"],
    
    # ============ SUBSCRIPTIONS/BILLING ============
    r"^/api/subscriptions(/.*)?$":     ["org_admin", "admin", "owner"],
    r"^/api/plans(/.*)?$":             ["org_admin", "admin", "owner", "manager", "viewer"],
    
    # ============ NOTIFICATIONS ============
    r"^/api/notifications(/.*)?$":     ["org_admin", "admin", "owner", "manager", "technician", "dispatcher", "accountant"],
    
    # ============ CUSTOMER PORTALS ============
    r"^/api/customer-portal(/.*)?$":   ["customer", "fleet_customer"],
    r"^/api/business-portal(/.*)?$":   ["fleet_customer"],
    r"^/api/technician-portal(/.*)?$": ["technician"],
    r"^/api/technician(/.*)?$":        ["technician"],
    
    # ============ AMC (WARRANTY) ============
    r"^/api/amc(/.*)?$":               ["org_admin", "admin", "owner", "manager", "accountant"],
    
    # ============ TIME TRACKING ============
    r"^/api/time-tracking(/.*)?$":     ["org_admin", "admin", "owner", "manager", "technician"],
    
    # ============ PROJECTS ============
    r"^/api/projects(/.*)?$":          ["org_admin", "admin", "owner", "manager", "technician"],
    
    # ============ DATA MANAGEMENT ============
    r"^/api/data-management(/.*)?$":   ["org_admin", "admin", "owner"],
    r"^/api/data-migration(/.*)?$":    ["org_admin", "admin", "owner"],
    r"^/api/data-integrity(/.*)?$":    ["org_admin", "admin", "owner"],
    r"^/api/export(/.*)?$":            ["org_admin", "admin", "owner", "accountant"],
    r"^/api/seed(/.*)?$":              ["org_admin", "admin", "owner"],
    
    # ============ DELIVERY CHALLANS ============
    r"^/api/delivery-challans(/.*)?$": ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/recurring-invoices(/.*)?$": ["org_admin", "admin", "owner", "accountant"],
    
    # ============ MASTER DATA ============
    r"^/api/master-data(/.*)?$":       ["org_admin", "admin", "owner", "manager"],
    
    # ============ BOOKS MODULE ============
    r"^/api/books(/.*)?$":                  ["org_admin", "admin", "owner", "accountant", "manager"],

    # ============ ENHANCED MODULES (P0 — previously unmapped) ============
    r"^/api/invoices-enhanced(/.*)?$":      ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/bills-enhanced(/.*)?$":         ["org_admin", "admin", "owner", "accountant"],
    r"^/api/items-enhanced(/.*)?$":         ["org_admin", "admin", "owner", "manager", "accountant", "technician"],
    r"^/api/contacts-enhanced(/.*)?$":      ["org_admin", "admin", "owner", "manager", "dispatcher"],
    r"^/api/estimates-enhanced(/.*)?$":     ["org_admin", "admin", "owner", "manager", "technician", "dispatcher"],
    r"^/api/inventory-enhanced(/.*)?$":     ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/sales-orders-enhanced(/.*)?$":  ["org_admin", "admin", "owner", "manager", "accountant"],
    
    # ============ ADVANCED/INTEGRATION MODULES (previously unmapped) ============
    r"^/api/reports-advanced(/.*)?$":       ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/contact-integration(/.*)?$":    ["org_admin", "admin", "owner", "manager", "dispatcher"],
    r"^/api/invoice-automation(/.*)?$":     ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/invoice-payments(/.*)?$":       ["org_admin", "admin", "owner", "accountant"],
    r"^/api/vendor-credits(/.*)?$":         ["org_admin", "admin", "owner", "accountant"],
    
    # ============ EVFI/AI EXTENDED (previously unmapped) ============
    r"^/api/e?v?fi-guided(/.*)?$":             ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/ai-assist(/.*)?$":              ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/expert-queue(/.*)?$":           ["org_admin", "admin", "owner", "manager", "technician"],
    
    # ============ INVENTORY EXTENDED (previously unmapped) ============
    r"^/api/inv-adjustments(/.*)?$":        ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/serial-batch(/.*)?$":           ["org_admin", "admin", "owner", "manager", "accountant"],
    
    # ============ CONFIG/ANALYTICS (previously unmapped) ============
    r"^/api/sla(/.*)?$":                    ["org_admin", "admin", "owner", "manager"],
    r"^/api/dashboard(/.*)?$":              ["org_admin", "admin", "owner", "manager", "accountant", "technician"],
    r"^/api/insights(/.*)?$":               ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/ai-usage(/.*)?$":                ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/operations(/.*)?$":          ["org_admin", "admin", "owner", "manager", "accountant", "technician"],

    # ============ PERIOD LOCKING ============
    r"^/api/finance/period-locks(/.*)?$":   ["org_admin", "admin", "owner", "accountant"],
    r"^/api/v1/finance/period-locks(/.*)?$": ["org_admin", "admin", "owner", "accountant"],
    r"^/api/v1/period-locks(/.*)?$":        ["org_admin", "admin", "owner", "accountant"],

    # ============ ACCOUNTING/FINANCE EXTENDED ============
    r"^/api/accounting(/.*)?$":             ["org_admin", "admin", "owner", "accountant"],
    r"^/api/journal-entries(/.*)?$":        ["org_admin", "admin", "owner", "accountant"],
    r"^/api/ledger(/.*)?$":                 ["org_admin", "admin", "owner", "accountant"],
    r"^/api/payments-received(/.*)?$":      ["org_admin", "admin", "owner", "accountant"],
    r"^/api/stock-transfers(/.*)?$":        ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/warehouses(/.*)?$":             ["org_admin", "admin", "owner", "manager", "accountant"],

    # ============ OPERATIONS EXTENDED ============
    r"^/api/failure-cards(/.*)?$":          ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/services(/.*)?$":              ["org_admin", "admin", "owner", "manager", "technician"],

    # ============ ADMIN/SYSTEM ============
    r"^/api/alerts(/.*)?$":                 ["org_admin", "admin", "owner", "manager"],
    r"^/api/audit-logs(/.*)?$":             ["org_admin", "admin", "owner"],
    r"^/api/import(/.*)?$":                 ["org_admin", "admin", "owner"],
    r"^/api/migration(/.*)?$":              ["org_admin", "admin", "owner"],
    r"^/api/reseed(/.*)?$":                 ["org_admin", "admin", "owner"],
    r"^/api/seed-customer-demo(/.*)?$":     ["org_admin", "admin", "owner"],
    r"^/api/business(/.*)?$":               ["org_admin", "admin", "owner", "manager"],

    # ============ CUSTOMERS MODULE ============
    r"^/api/customers-enhanced(/.*)?$":     ["org_admin", "admin", "owner", "manager", "dispatcher"],

    # ============ TICKET INVOICES MODULE ============
    r"^/api/ticket-invoices(/.*)?$":        ["org_admin", "admin", "owner", "manager", "accountant", "technician"],
    r"^/api/v1/ticket-invoices(/.*)?$":     ["org_admin", "admin", "owner", "manager", "accountant", "technician"],

    # ============ GST MODULE ============
    r"^/api/gst(/.*)?$":                    ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/v1/gst(/.*)?$":                 ["org_admin", "admin", "owner", "accountant", "manager"],
}

# Compiled patterns for performance
_PERMISSION_PATTERNS = [(re.compile(pattern), roles) for pattern, roles in ROUTE_PERMISSIONS.items()]


def get_allowed_roles(path: str) -> Optional[List[str]]:
    """Get list of allowed roles for a route path"""
    for pattern, roles in _PERMISSION_PATTERNS:
        if pattern.match(path):
            return roles
    return None


def expand_role(role: str) -> List[str]:
    """Expand role to include inherited roles"""
    return ROLE_HIERARCHY.get(role, [role])


def check_role_permission(user_role: str, allowed_roles: List[str]) -> bool:
    """Check if user role is in allowed roles (considering hierarchy)"""
    if not allowed_roles:
        return False
    
    # Normalize role name
    normalized_role = user_role.lower().strip()
    
    # Check direct match
    if normalized_role in [r.lower() for r in allowed_roles]:
        return True
    
    # Check hierarchy - get all roles this user can act as
    effective_roles = expand_role(normalized_role)
    
    for effective_role in effective_roles:
        if effective_role.lower() in [r.lower() for r in allowed_roles]:
            return True
    
    return False


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Role-Based Access Control Middleware.
    
    Checks if user's role is authorized to access the requested route.
    Must run AFTER TenantGuardMiddleware (which sets user role).
    """
    
    # Public endpoints that skip RBAC
    PUBLIC_ENDPOINTS = {
        "/health", "/api/health", "/api/v1/health", "/api/", "/", "/docs", "/redoc", "/openapi.json",
        "/api/auth/login", "/api/auth/register", "/api/auth/session",
        "/api/auth/logout", "/api/auth/me", "/api/auth/google",
        "/api/auth/forgot-password", "/api/auth/reset-password",
        "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/session",
        "/api/v1/auth/logout", "/api/v1/auth/me",
        "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email", "/api/v1/auth/resend-verification",
        "/api/auth/verify-email", "/api/auth/resend-verification",
    }
    
    PUBLIC_PATTERNS = [
        r"^/api/public/.*",
        r"^/api/v1/public/.*",
        r"^/api/webhooks/.*",
        r"^/api/v1/webhooks/.*",
        r"^/api/payments/webhook$",
        r"^/api/v1/payments/webhook$",
        r"^/api/v1/razorpay/webhook$",
        r"^/api/customer-portal/.*",
        r"^/api/v1/customer-portal/.*",
        r"^/api/business-portal/.*",
        r"^/api/v1/business-portal/.*",
        r"^/api/business/.*",
        r"^/api/v1/business/.*",
        r"^/api/organizations/signup$",
        r"^/api/v1/organizations/signup$",
        r"^/api/organizations/register$",
        r"^/api/v1/organizations/register$",
        r"^/api/contact$",
        r"^/api/v1/contact$",
        r"^/api/book-demo$",
        r"^/api/v1/book-demo$",
        r"^/api/contact-form$",
        r"^/api/v1/contact-form$",
        r"^/api/demo-request$",
        r"^/api/v1/demo-request$",
        r"^/api/organizations/accept-invite$",
        r"^/api/v1/organizations/accept-invite$",
        r"^/api/v1/subscriptions/plans$",
        r"^/api/v1/subscriptions/plans/compare$",
        r"^/api/v1/subscriptions/plans/[^/]+$",
        # Platform version endpoint (public, exact path)
        r"^/api/platform/version$",
        r"^/api/v1/platform/version$",
        # Public estimate/invoice share links (no JWT — accessed by customers)
        r"^/api/estimates-enhanced/public/.*",
        r"^/api/v1/estimates-enhanced/public/.*",
        r"^/api/invoices-enhanced/public/.*",
        r"^/api/v1/invoices-enhanced/public/.*",
        r"^/api/estimates/public/.*",
        r"^/api/v1/estimates/public/.*",
        r"^/api/invoices/public/.*",
        r"^/api/v1/invoices/public/.*",
        # Master data (public read-only, matches TenantGuard config)
        r"^/api/master-data/.*",
        r"^/api/v1/master-data/.*",
    ]
    
    def __init__(self, app):
        super().__init__(app)
        logger.info("RBACMiddleware initialized")
    
    def _is_public(self, path: str) -> bool:
        """Check if path is public"""
        if path in self.PUBLIC_ENDPOINTS:
            return True
        for pattern in self.PUBLIC_PATTERNS:
            if re.match(pattern, path):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Check role permissions for each request"""
        path = request.url.path
        method = request.method
        
        # Skip OPTIONS (CORS)
        if method == "OPTIONS":
            return await call_next(request)
        
        # Skip public routes
        if self._is_public(path):
            return await call_next(request)
        
        # Get user role from request state (set by TenantGuardMiddleware)
        user_role = getattr(request.state, "tenant_user_role", None)
        user_id = getattr(request.state, "tenant_user_id", None)
        
        logger.info(f"RBAC CHECK: path={path}, role={user_role}, user={user_id}")
        
        if not user_role:
            # No role means not authenticated through TenantGuard.
            # Check if this path is in OUR public list.
            if self._is_public(path):
                return await call_next(request)
            # Otherwise DENY — do not pass through silently.
            logger.warning(
                "RBAC DENIED: No role set for %s %s. "
                "TenantGuard may have skipped auth.",
                method, path,
            )
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Authentication required.",
                    "code": "RBAC_NO_ROLE",
                }
            )
        
        # Normalize path: strip /v1 prefix so /api/v1/hr/... matches /api/hr/... patterns
        normalized_path = re.sub(r'^/api/v1/', '/api/', path)
        
        # Check route permissions
        allowed_roles = get_allowed_roles(normalized_path)
        
        if allowed_roles is None:
            # DENY by default — unmapped routes are blocked
            logger.warning(
                f"RBAC DENIED: Route {path} (normalized: {normalized_path}) "
                f"not in permission map. User {user_id} role={user_role}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Access denied. This route is not configured in the permission map.",
                    "code": "RBAC_UNMAPPED_ROUTE",
                    "your_role": user_role,
                }
            )
        
        # Check if user's role is authorized
        if not check_role_permission(user_role, allowed_roles):
            logger.warning(
                f"RBAC DENIED: User {user_id} with role '{user_role}' "
                f"attempted to access {path}. Allowed roles: {allowed_roles}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Access denied. This endpoint requires one of: {', '.join(allowed_roles)}",
                    "code": "RBAC_DENIED",
                    "your_role": user_role,
                    "required_roles": allowed_roles
                }
            )
        
        logger.info(f"RBAC ALLOWED: {user_role} accessing {path}")
        return await call_next(request)


def require_roles(*allowed_roles: str):
    """
    Route decorator for additional role checking.
    Use for fine-grained control within a route handler.
    
    Usage:
        @router.delete("/items/{item_id}")
        async def delete_item(request: Request, item_id: str):
            require_roles("org_admin", "admin")(request)  # Only admins can delete
            ...
    """
    def checker(request: Request):
        user_role = getattr(request.state, "tenant_user_role", "viewer")
        if not check_role_permission(user_role, list(allowed_roles)):
            raise HTTPException(
                status_code=403,
                detail=f"This action requires one of: {', '.join(allowed_roles)}"
            )
    return checker
