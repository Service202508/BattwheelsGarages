"""
Core Organization Module
Multi-tenant foundation for Battwheels OS
"""
from .models import (
    Organization, OrganizationCreate, OrganizationUpdate,
    OrganizationSettings, OrganizationSettingsUpdate,
    OrganizationUser, OrganizationUserCreate, OrganizationUserUpdate,
    OrganizationContext, OrgUserRole, OrgUserStatus, PlanType, IndustryType,
    get_role_permissions, has_permission, ROLE_PERMISSIONS
)
from .service import (
    OrganizationService,
    init_organization_service,
    get_organization_service
)
from .middleware import (
    OrganizationMiddleware,
    require_org_context,
    require_permission,
    org_scoped_query,
    add_org_id
)
from .routes import router as org_router, init_org_routes
from .dependencies import (
    init_org_dependencies,
    get_org_id_from_request,
    get_optional_org_id,
    get_org_context,
    OrgContext,
    org_scoped_query as dep_org_scoped_query,
    add_org_to_doc
)

__all__ = [
    # Models
    "Organization", "OrganizationCreate", "OrganizationUpdate",
    "OrganizationSettings", "OrganizationSettingsUpdate",
    "OrganizationUser", "OrganizationUserCreate", "OrganizationUserUpdate",
    "OrganizationContext", "OrgUserRole", "OrgUserStatus", "PlanType", "IndustryType",
    "get_role_permissions", "has_permission", "ROLE_PERMISSIONS",
    # Service
    "OrganizationService", "init_organization_service", "get_organization_service",
    # Middleware
    "OrganizationMiddleware", "require_org_context", "require_permission",
    "org_scoped_query", "add_org_id",
    # Dependencies
    "init_org_dependencies", "get_org_id_from_request", "get_optional_org_id",
    "get_org_context", "OrgContext", "add_org_to_doc",
    # Routes
    "org_router", "init_org_routes"
]
