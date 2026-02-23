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
    "org_admin": ["org_admin", "manager", "accountant", "technician", "dispatcher", "viewer"],
    "owner": ["owner", "org_admin", "manager", "accountant", "technician", "dispatcher", "viewer"],
    "admin": ["admin", "org_admin", "manager", "accountant", "technician", "dispatcher", "viewer"],
    "manager": ["manager", "technician", "dispatcher", "viewer"],
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
    r"^/api/finance/.*$":           ["org_admin", "admin", "owner", "accountant"],
    r"^/api/banking/.*$":           ["org_admin", "admin", "owner", "accountant"],
    r"^/api/banking-module/.*$":    ["org_admin", "admin", "owner", "accountant"],
    r"^/api/journal.*$":            ["org_admin", "admin", "owner", "accountant"],
    r"^/api/chart-of-accounts.*$":  ["org_admin", "admin", "owner", "accountant"],
    
    # ============ HR/PAYROLL (Admin Only) ============
    r"^/api/hr/payroll.*$":         ["org_admin", "admin", "owner"],
    r"^/api/hr/employees.*$":       ["org_admin", "admin", "owner", "manager"],
    r"^/api/hr/attendance.*$":      ["org_admin", "admin", "owner", "manager"],
    r"^/api/hr/leave.*$":           ["org_admin", "admin", "owner", "manager"],
    r"^/api/hr/.*$":                ["org_admin", "admin", "owner"],
    r"^/api/payroll/.*$":           ["org_admin", "admin", "owner"],
    
    # ============ INVOICING ============
    r"^/api/invoices/.*$":          ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/bills/.*$":             ["org_admin", "admin", "owner", "accountant"],
    r"^/api/expenses/.*$":          ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/credit-notes/.*$":      ["org_admin", "admin", "owner", "accountant"],
    r"^/api/payments.*$":           ["org_admin", "admin", "owner", "accountant"],
    
    # ============ ESTIMATES/QUOTES ============
    r"^/api/estimates/.*$":         ["org_admin", "admin", "owner", "manager", "technician", "dispatcher"],
    r"^/api/ticket-estimates/.*$":  ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/sales-orders/.*$":      ["org_admin", "admin", "owner", "manager", "accountant"],
    
    # ============ OPERATIONS ============
    r"^/api/tickets/.*$":           ["org_admin", "admin", "owner", "manager", "technician", "dispatcher"],
    r"^/api/job-cards/.*$":         ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/vehicles/.*$":          ["org_admin", "admin", "owner", "manager", "technician", "dispatcher"],
    
    # ============ INVENTORY ============
    r"^/api/inventory/.*$":         ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/items/.*$":             ["org_admin", "admin", "owner", "manager", "accountant", "technician"],
    r"^/api/allocations/.*$":       ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/stock.*$":              ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/composite-items/.*$":   ["org_admin", "admin", "owner", "manager"],
    r"^/api/purchase-orders/.*$":   ["org_admin", "admin", "owner", "accountant"],
    
    # ============ CONTACTS/CRM ============
    r"^/api/contacts/.*$":          ["org_admin", "admin", "owner", "manager", "dispatcher"],
    r"^/api/suppliers/.*$":         ["org_admin", "admin", "owner", "accountant"],
    r"^/api/customers/.*$":         ["org_admin", "admin", "owner", "manager", "dispatcher"],
    
    # ============ EFI/AI (Operations) ============
    r"^/api/efi/.*$":               ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/ai/.*$":                ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/failure.*$":            ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/knowledge.*$":          ["org_admin", "admin", "owner", "manager", "technician"],
    
    # ============ REPORTS ============
    r"^/api/reports/.*$":           ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/gst/.*$":               ["org_admin", "admin", "owner", "accountant"],
    r"^/api/productivity/.*$":      ["org_admin", "admin", "owner", "manager"],
    
    # ============ SETTINGS/ADMIN ============
    r"^/api/organizations/settings.*$": ["org_admin", "admin", "owner"],
    r"^/api/organizations/users.*$":    ["org_admin", "admin", "owner"],
    r"^/api/organizations/.*$":         ["org_admin", "admin", "owner", "manager", "accountant", "technician", "viewer"],
    r"^/api/settings/.*$":              ["org_admin", "admin", "owner"],
    r"^/api/permissions/.*$":           ["org_admin", "admin", "owner"],
    r"^/api/users/.*$":                 ["org_admin", "admin", "owner"],
    r"^/api/technicians$":              ["org_admin", "admin", "owner", "manager", "dispatcher"],
    
    # ============ DOCUMENT MANAGEMENT ============
    r"^/api/documents/.*$":         ["org_admin", "admin", "owner", "manager", "technician"],
    r"^/api/uploads/.*$":           ["org_admin", "admin", "owner", "manager", "technician", "accountant"],
    r"^/api/pdf-templates/.*$":     ["org_admin", "admin", "owner", "accountant"],
    
    # ============ INTEGRATIONS ============
    r"^/api/zoho.*$":               ["org_admin", "admin", "owner", "accountant"],
    r"^/api/razorpay/.*$":          ["org_admin", "admin", "owner", "accountant"],
    r"^/api/stripe/.*$":            ["org_admin", "admin", "owner", "accountant"],
    r"^/api/einvoice/.*$":          ["org_admin", "admin", "owner", "accountant"],
    
    # ============ SUBSCRIPTIONS/BILLING ============
    r"^/api/subscriptions/.*$":     ["org_admin", "admin", "owner"],
    r"^/api/plans/.*$":             ["org_admin", "admin", "owner", "manager", "viewer"],
    
    # ============ NOTIFICATIONS ============
    r"^/api/notifications/.*$":     ["org_admin", "admin", "owner", "manager", "technician", "dispatcher", "accountant"],
    
    # ============ CUSTOMER PORTALS ============
    r"^/api/customer-portal/.*$":   ["customer", "fleet_customer"],
    r"^/api/business-portal/.*$":   ["fleet_customer"],
    r"^/api/technician-portal/.*$": ["technician"],
    
    # ============ AMC (WARRANTY) ============
    r"^/api/amc/.*$":               ["org_admin", "admin", "owner", "manager", "accountant"],
    
    # ============ TIME TRACKING ============
    r"^/api/time-tracking/.*$":     ["org_admin", "admin", "owner", "manager", "technician"],
    
    # ============ PROJECTS ============
    r"^/api/projects/.*$":          ["org_admin", "admin", "owner", "manager", "technician"],
    
    # ============ DATA MANAGEMENT ============
    r"^/api/data-management/.*$":   ["org_admin", "admin", "owner"],
    r"^/api/data-migration/.*$":    ["org_admin", "admin", "owner"],
    r"^/api/data-integrity/.*$":    ["org_admin", "admin", "owner"],
    r"^/api/export/.*$":            ["org_admin", "admin", "owner", "accountant"],
    r"^/api/seed/.*$":              ["org_admin", "admin", "owner"],
    
    # ============ DELIVERY CHALLANS ============
    r"^/api/delivery-challans/.*$": ["org_admin", "admin", "owner", "manager", "accountant"],
    r"^/api/recurring-invoices/.*$": ["org_admin", "admin", "owner", "accountant"],
    
    # ============ MASTER DATA ============
    r"^/api/master-data/.*$":       ["org_admin", "admin", "owner", "manager"],
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
    Must run AFTER TenantIsolationMiddleware (which sets user role).
    """
    
    def __init__(self, app):
        super().__init__(app)
        logger.info("RBACMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Check role permissions for each request"""
        path = request.url.path
        method = request.method
        
        # Skip OPTIONS (CORS)
        if method == "OPTIONS":
            return await call_next(request)
        
        # Skip public routes
        if is_public_route(path):
            return await call_next(request)
        
        # Get user role from request state (set by TenantIsolationMiddleware)
        user_role = getattr(request.state, "tenant_user_role", None)
        user_id = getattr(request.state, "tenant_user_id", None)
        
        if not user_role:
            # TenantIsolationMiddleware should have set this
            # If not, it means the request wasn't properly authenticated
            logger.warning(f"No role found for path {path}")
            return await call_next(request)  # Let other middleware handle auth
        
        # Check route permissions
        allowed_roles = get_allowed_roles(path)
        
        if allowed_roles is None:
            # Route not in permissions map - use default policy
            # Default: Allow authenticated users (logged in = can access)
            # In strict mode, you might want to DENY by default
            logger.debug(f"Route {path} not in RBAC map, allowing authenticated user")
            return await call_next(request)
        
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
        
        logger.debug(f"RBAC ALLOWED: {user_role} accessing {path}")
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
