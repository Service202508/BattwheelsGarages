"""
Organization Dependencies for Route Injection
Provides FastAPI dependencies for multi-tenant data isolation
"""
from fastapi import Request, HTTPException, Depends
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

# JWT — canonical source
from utils.auth import decode_token, JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)

# Database reference (set during init)
_db: Optional[AsyncIOMotorDatabase] = None


def init_org_dependencies(database: AsyncIOMotorDatabase):
    """Initialize dependencies with database"""
    global _db
    _db = database


async def get_user_id_from_request(request: Request) -> Optional[str]:
    """Extract user_id from JWT token in request"""
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check session cookie
    session_token = request.cookies.get("session_token")
    if session_token and _db:
        session = await _db.user_sessions.find_one({"session_token": session_token})
        if session:
            return session.get("user_id")
    
    return None


async def get_org_id_from_request(request: Request) -> str:
    """
    Get organization ID from request context.
    
    Resolution order:
    1. X-Organization-ID header
    2. org_id query parameter
    3. User's default (first active) organization
    
    Returns:
        str: Organization ID
    
    Raises:
        HTTPException: If no organization found or user not a member
    """
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    user_id = await get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Priority 1: Header
    org_id = request.headers.get("X-Organization-ID")
    
    # Priority 2: Query parameter
    if not org_id:
        org_id = request.query_params.get("org_id")
    
    # Priority 3: User's default organization
    if not org_id:
        membership = await _db.organization_users.find_one({
            "user_id": user_id,
            "status": "active"
        }, {"_id": 0, "organization_id": 1})
        
        if membership:
            org_id = membership.get("organization_id")
    
    if not org_id:
        raise HTTPException(
            status_code=400,
            detail="Organization context required. Use X-Organization-ID header or org_id parameter."
        )
    
    # Verify user is member of this org
    is_member = await _db.organization_users.find_one({
        "user_id": user_id,
        "organization_id": org_id,
        "status": "active"
    })
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You are not a member of this organization."
        )
    
    return org_id


async def get_optional_org_id(request: Request) -> Optional[str]:
    """
    Get organization ID if available, None if not authenticated.
    Used for routes that can work without org context but benefit from it.
    """
    try:
        return await get_org_id_from_request(request)
    except HTTPException:
        return None


def org_scoped_query(org_id: str, base_query: dict = None) -> dict:
    """
    Add organization_id to a MongoDB query for data isolation.
    
    Example:
        query = org_scoped_query(org_id, {"status": "active"})
        # Returns: {"organization_id": "org_xxx", "status": "active"}
    """
    query = {"organization_id": org_id}
    if base_query:
        query.update(base_query)
    return query


def add_org_to_doc(doc: dict, org_id: str) -> dict:
    """
    Add organization_id to a document before insert.
    
    Example:
        invoice_doc = add_org_to_doc({"total": 1000}, org_id)
        # Returns: {"total": 1000, "organization_id": "org_xxx"}
    """
    doc["organization_id"] = org_id
    return doc


class OrgContext:
    """
    Organization context object for route handlers.
    Provides helper methods for data scoping.
    """
    def __init__(self, org_id: str, user_id: str):
        self.org_id = org_id
        self.user_id = user_id
    
    def scope_query(self, base_query: dict = None) -> dict:
        """Add org_id to query"""
        return org_scoped_query(self.org_id, base_query)
    
    def scope_doc(self, doc: dict) -> dict:
        """Add org_id to document"""
        return add_org_to_doc(doc, self.org_id)


async def get_org_context(request: Request) -> OrgContext:
    """
    FastAPI dependency for getting organization context.
    
    Usage in routes:
        @router.get("/items")
        async def list_items(org: OrgContext = Depends(get_org_context)):
            query = org.scope_query({"is_active": True})
            items = await db.items.find(query).to_list()
    """
    org_id = await get_org_id_from_request(request)
    user_id = await get_user_id_from_request(request)
    return OrgContext(org_id, user_id)
