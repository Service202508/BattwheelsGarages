"""
Organization API Routes
Control plane for multi-tenant organization management
"""
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone
import logging

from core.org.models import (
    Organization, OrganizationCreate, OrganizationUpdate,
    OrganizationSettings, OrganizationSettingsUpdate,
    OrganizationUser, OrganizationUserCreate, OrganizationUserUpdate,
    OrganizationContext, OrgUserRole, OrgUserStatus
)
from core.org.service import get_organization_service
from core.org.middleware import require_org_context, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/org", tags=["Organization"])

# Database reference (set during init)
_db = None
_auth_func = None


def init_org_routes(database, auth_function):
    """Initialize routes with database and auth"""
    global _db, _auth_func
    _db = database
    _auth_func = auth_function
    return router


async def get_current_user(request: Request):
    """Get current authenticated user"""
    if _auth_func:
        return await _auth_func(request)
    raise HTTPException(status_code=401, detail="Authentication required")


# ==================== ORGANIZATION ENDPOINTS ====================

@router.get("", response_model=Organization)
async def get_current_organization(
    request: Request,
    org_id: Optional[str] = Query(None, description="Organization ID")
):
    """
    Get current organization details
    
    - If org_id provided, returns that org (if user is member)
    - Otherwise returns user's default organization
    """
    user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org
    if org_id:
        context = await service.get_organization_context(org_id, user.user_id)
        if not context:
            raise HTTPException(status_code=403, detail="Not a member of this organization")
        return context.organization
    
    # Get user's organizations
    user_orgs = await service.get_user_organizations(user.user_id)
    if not user_orgs:
        raise HTTPException(status_code=404, detail="No organization found")
    
    return user_orgs[0]["organization"]


@router.patch("", response_model=Organization)
async def update_current_organization(
    data: OrganizationUpdate,
    request: Request,
    org_id: Optional[str] = Query(None)
):
    """Update organization details (admin/owner only)"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org context
    resolved_org_id = org_id or request.headers.get("X-Organization-ID")
    if not resolved_org_id:
        user_orgs = await service.get_user_organizations(user.user_id)
        if user_orgs:
            resolved_org_id = user_orgs[0]["organization"].organization_id
    
    if not resolved_org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    context = await service.get_organization_context(resolved_org_id, user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check permission
    if not context.has_permission("org:update"):
        raise HTTPException(status_code=403, detail="Permission denied: org:update")
    
    org = await service.update_organization(resolved_org_id, data)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org


@router.post("", response_model=Organization)
async def create_organization(
    data: OrganizationCreate,
    request: Request
):
    """Create a new organization (user becomes owner)"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    org = await service.create_organization(data, user.user_id)
    
    return org


@router.get("/list")
async def list_user_organizations(request: Request):
    """List all organizations the user belongs to"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    user_orgs = await service.get_user_organizations(user.user_id)
    
    return {
        "organizations": [
            {
                "organization_id": item["organization"].organization_id,
                "name": item["organization"].name,
                "slug": item["organization"].slug,
                "role": item["membership"].role,
                "joined_at": item["membership"].joined_at
            }
            for item in user_orgs
        ],
        "total": len(user_orgs)
    }


@router.post("/switch/{org_id}")
async def switch_organization(
    org_id: str,
    request: Request
):
    """Switch to a different organization"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    context = await service.get_organization_context(org_id, user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    # Update last active
    await service.update_user_membership(
        org_id,
        user.user_id,
        OrganizationUserUpdate(last_active_at=datetime.now(timezone.utc))
    )
    
    return {
        "message": "Switched organization",
        "organization_id": context.organization_id,
        "organization_name": context.organization.name,
        "role": context.user_role
    }


# ==================== SETTINGS ENDPOINTS ====================

@router.get("/settings", response_model=OrganizationSettings)
async def get_organization_settings(
    request: Request,
    org_id: Optional[str] = Query(None)
):
    """Get organization settings"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org
    resolved_org_id = org_id or request.headers.get("X-Organization-ID")
    if not resolved_org_id:
        user_orgs = await service.get_user_organizations(user.user_id)
        if user_orgs:
            resolved_org_id = user_orgs[0]["organization"].organization_id
    
    if not resolved_org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    context = await service.get_organization_context(resolved_org_id, user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return context.settings


@router.patch("/settings", response_model=OrganizationSettings)
async def update_organization_settings(
    data: OrganizationSettingsUpdate,
    request: Request,
    org_id: Optional[str] = Query(None)
):
    """Update organization settings (admin/owner only)"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org
    resolved_org_id = org_id or request.headers.get("X-Organization-ID")
    if not resolved_org_id:
        user_orgs = await service.get_user_organizations(user.user_id)
        if user_orgs:
            resolved_org_id = user_orgs[0]["organization"].organization_id
    
    if not resolved_org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    context = await service.get_organization_context(resolved_org_id, user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not context.has_permission("org:settings:update"):
        raise HTTPException(status_code=403, detail="Permission denied: org:settings:update")
    
    settings = await service.update_settings(resolved_org_id, data)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return settings


# ==================== USERS ENDPOINTS ====================

@router.get("/users")
async def list_organization_users(
    request: Request,
    org_id: Optional[str] = Query(None),
    status: Optional[OrgUserStatus] = Query(None)
):
    """List all users in the organization"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org
    resolved_org_id = org_id or request.headers.get("X-Organization-ID")
    if not resolved_org_id:
        user_orgs = await service.get_user_organizations(user.user_id)
        if user_orgs:
            resolved_org_id = user_orgs[0]["organization"].organization_id
    
    if not resolved_org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    context = await service.get_organization_context(resolved_org_id, user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not context.has_permission("org:users:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    members = await service.list_org_users(resolved_org_id, status)
    
    # Enrich with user details
    enriched = []
    for member in members:
        user_doc = await _db.users.find_one(
            {"user_id": member.user_id},
            {"_id": 0, "user_id": 1, "name": 1, "email": 1, "picture": 1}
        )
        enriched.append({
            "membership": member.model_dump(),
            "user": user_doc
        })
    
    return {
        "users": enriched,
        "total": len(enriched)
    }


@router.post("/users", response_model=OrganizationUser)
async def add_user_to_organization(
    data: OrganizationUserCreate,
    request: Request,
    org_id: Optional[str] = Query(None)
):
    """Add a user to the organization"""
    user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org
    resolved_org_id = org_id or request.headers.get("X-Organization-ID")
    if not resolved_org_id:
        user_orgs = await service.get_user_organizations(user.user_id)
        if user_orgs:
            resolved_org_id = user_orgs[0]["organization"].organization_id
    
    if not resolved_org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    context = await service.get_organization_context(resolved_org_id, user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not context.has_permission("org:users:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Find user by email if not user_id
    if not data.user_id and data.email:
        existing_user = await _db.users.find_one({"email": data.email})
        if existing_user:
            data.user_id = existing_user["user_id"]
    
    if not data.user_id:
        raise HTTPException(status_code=400, detail="User not found")
    
    try:
        membership = await service.add_user_to_org(
            resolved_org_id,
            data,
            user.user_id
        )
        return membership
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/users/{user_id}", response_model=OrganizationUser)
async def update_user_membership(
    user_id: str,
    data: OrganizationUserUpdate,
    request: Request,
    org_id: Optional[str] = Query(None)
):
    """Update user's role or status in organization"""
    current_user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org
    resolved_org_id = org_id or request.headers.get("X-Organization-ID")
    if not resolved_org_id:
        user_orgs = await service.get_user_organizations(current_user.user_id)
        if user_orgs:
            resolved_org_id = user_orgs[0]["organization"].organization_id
    
    if not resolved_org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    context = await service.get_organization_context(resolved_org_id, current_user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not context.has_permission("org:users:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    membership = await service.update_user_membership(resolved_org_id, user_id, data)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    return membership


@router.delete("/users/{user_id}")
async def remove_user_from_organization(
    user_id: str,
    request: Request,
    org_id: Optional[str] = Query(None)
):
    """Remove user from organization"""
    current_user = await get_current_user(request)
    service = get_organization_service()
    
    # Resolve org
    resolved_org_id = org_id or request.headers.get("X-Organization-ID")
    if not resolved_org_id:
        user_orgs = await service.get_user_organizations(current_user.user_id)
        if user_orgs:
            resolved_org_id = user_orgs[0]["organization"].organization_id
    
    if not resolved_org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    context = await service.get_organization_context(resolved_org_id, current_user.user_id)
    if not context:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not context.has_permission("org:users:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        removed = await service.remove_user_from_org(resolved_org_id, user_id)
        if removed:
            return {"message": "User removed from organization"}
        raise HTTPException(status_code=404, detail="Membership not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ROLES INFO ====================

@router.get("/roles")
async def get_available_roles():
    """Get list of available roles and their permissions"""
    from core.org.models import ROLE_PERMISSIONS, OrgUserRole
    
    return {
        "roles": [
            {
                "role": role.value,
                "name": role.value.replace("_", " ").title(),
                "permissions": ROLE_PERMISSIONS.get(role, [])
            }
            for role in OrgUserRole
        ]
    }
