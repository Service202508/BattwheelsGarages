"""
Organization Context Utilities
Helpers for adding org scoping to existing routes
"""
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


async def get_user_org_id(request: Request, db: AsyncIOMotorDatabase) -> str:
    """
    Get the organization ID for the current authenticated user.
    
    Resolution order:
    1. X-Organization-ID header
    2. org_id query parameter
    3. User's default organization (first active membership)
    
    Returns:
        str: Organization ID
    
    Raises:
        HTTPException: If no organization found
    """
    # Get user from request state (set by auth middleware)
    user = getattr(request.state, 'user', None)
    if not user:
        # Try to get user_id from the auth check
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Decode token using canonical JWT module
        from utils.auth import decode_token
        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
            user_id = payload.get("user_id")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        user_id = user.user_id if hasattr(user, 'user_id') else user.get('user_id')
    
    # Priority 1: Header
    org_id = request.headers.get("X-Organization-ID")
    
    # Priority 2: Query parameter
    if not org_id:
        org_id = request.query_params.get("org_id")
    
    # Priority 3: User's default organization
    if not org_id:
        membership = await db.organization_users.find_one({
            "user_id": user_id,
            "status": "active"
        })
        if membership:
            org_id = membership.get("organization_id")
    
    if not org_id:
        raise HTTPException(
            status_code=400, 
            detail="Organization context required. Use X-Organization-ID header."
        )
    
    # Verify user is member of this org
    is_member = await db.organization_users.find_one({
        "user_id": user_id,
        "organization_id": org_id,
        "status": "active"
    })
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Not a member of this organization."
        )
    
    return org_id


def add_org_scope(query: Dict[str, Any], org_id: str) -> Dict[str, Any]:
    """
    Add organization_id to a MongoDB query.
    
    Example:
        query = add_org_scope({"status": "open"}, org_id)
        # Returns: {"status": "open", "organization_id": "org_xxx"}
    """
    query["organization_id"] = org_id
    return query


def org_doc(data: Dict[str, Any], org_id: str) -> Dict[str, Any]:
    """
    Add organization_id to a document before insert.
    
    Example:
        doc = org_doc({"name": "Test"}, org_id)
        # Returns: {"name": "Test", "organization_id": "org_xxx"}
    """
    data["organization_id"] = org_id
    return data


async def verify_org_resource(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    resource_id: str,
    id_field: str,
    org_id: str
) -> Dict[str, Any]:
    """
    Verify a resource belongs to the organization.
    
    Args:
        db: Database connection
        collection_name: Collection to query
        resource_id: Resource ID to check
        id_field: Name of the ID field (e.g., "ticket_id", "invoice_id")
        org_id: Organization ID to verify against
    
    Returns:
        The document if found and belongs to org
    
    Raises:
        HTTPException: If not found or doesn't belong to org
    """
    collection = db[collection_name]
    doc = await collection.find_one({
        id_field: resource_id,
        "organization_id": org_id
    })
    
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Resource not found or access denied"
        )
    
    return doc


# ==================== RETROFIT HELPERS ====================

async def retrofit_org_id_to_query(
    request: Request,
    db: AsyncIOMotorDatabase,
    base_query: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Helper to retrofit org_id to existing queries.
    Use in routes that haven't been fully refactored yet.
    
    Example:
        # In an existing route
        org_query = await retrofit_org_id_to_query(request, db, {"status": "active"})
        results = await db.tickets.find(org_query).to_list()
    """
    try:
        org_id = await get_user_org_id(request, db)
        query = base_query or {}
        query["organization_id"] = org_id
        return query
    except HTTPException:
        # Fallback for routes that don't strictly require org yet
        # This allows gradual migration
        return base_query or {}


async def retrofit_org_id_to_insert(
    request: Request,
    db: AsyncIOMotorDatabase,
    document: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Helper to add org_id to documents before insert.
    
    Example:
        doc = await retrofit_org_id_to_insert(request, db, {"title": "New Ticket"})
        await db.tickets.insert_one(doc)
    """
    try:
        org_id = await get_user_org_id(request, db)
        document["organization_id"] = org_id
        return document
    except HTTPException:
        # Fallback - insert without org_id (legacy mode)
        return document
