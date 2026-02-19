"""
Organization Middleware
Resolves organization context for every request
"""
from fastapi import Request, HTTPException, Depends
from typing import Optional
import logging

from .models import OrganizationContext
from .service import get_organization_service

logger = logging.getLogger(__name__)


class OrganizationMiddleware:
    """
    Middleware to resolve organization context from:
    1. X-Organization-ID header
    2. org_id query parameter
    3. User's default organization
    """
    
    @staticmethod
    async def resolve_organization(
        request: Request,
        user_id: str,
        org_id: Optional[str] = None
    ) -> OrganizationContext:
        """
        Resolve organization context for the request
        
        Args:
            request: FastAPI request object
            user_id: Authenticated user ID
            org_id: Optional explicit org ID
        
        Returns:
            OrganizationContext with full org info
        
        Raises:
            HTTPException if org not found or user not a member
        """
        service = get_organization_service()
        
        # Priority 1: Explicit org_id parameter
        resolved_org_id = org_id
        
        # Priority 2: Header
        if not resolved_org_id:
            resolved_org_id = request.headers.get("X-Organization-ID")
        
        # Priority 3: Query parameter
        if not resolved_org_id:
            resolved_org_id = request.query_params.get("org_id")
        
        # Priority 4: User's first/default organization
        if not resolved_org_id:
            user_orgs = await service.get_user_organizations(user_id)
            if user_orgs:
                resolved_org_id = user_orgs[0]["organization"]["organization_id"]
        
        if not resolved_org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization context required. Provide X-Organization-ID header or org_id parameter."
            )
        
        # Get full context
        context = await service.get_organization_context(resolved_org_id, user_id)
        
        if not context:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You are not a member of this organization."
            )
        
        # Attach to request state for later use
        request.state.org_context = context
        
        return context


def require_org_context():
    """
    Dependency to require organization context in route
    Use with: org_ctx: OrganizationContext = Depends(require_org_context())
    """
    async def _get_org_context(request: Request) -> OrganizationContext:
        if hasattr(request.state, "org_context"):
            return request.state.org_context
        raise HTTPException(
            status_code=500,
            detail="Organization context not resolved. Ensure auth middleware ran first."
        )
    return _get_org_context


def require_permission(permission: str):
    """
    Dependency to require specific permission
    Use with: Depends(require_permission("tickets:create"))
    """
    async def _check_permission(request: Request):
        if not hasattr(request.state, "org_context"):
            raise HTTPException(status_code=500, detail="Organization context missing")
        
        ctx: OrganizationContext = request.state.org_context
        if not ctx.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}"
            )
        return True
    return _check_permission


# ==================== SCOPED QUERY HELPERS ====================

def org_scoped_query(org_id: str, base_query: dict = None) -> dict:
    """
    Create organization-scoped query
    
    Example:
        query = org_scoped_query(ctx.organization_id, {"status": "open"})
        # Returns: {"organization_id": "org_xxx", "status": "open"}
    """
    query = {"organization_id": org_id}
    if base_query:
        query.update(base_query)
    return query


def add_org_id(data: dict, org_id: str) -> dict:
    """
    Add organization_id to data dict
    
    Example:
        ticket_data = add_org_id({"title": "Issue"}, ctx.organization_id)
        # Returns: {"title": "Issue", "organization_id": "org_xxx"}
    """
    data["organization_id"] = org_id
    return data
