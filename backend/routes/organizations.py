"""
SaaS Organization Management Routes
===================================

Complete organization lifecycle management for multi-tenant SaaS:
- Organization signup and onboarding
- User invitations and team management
- Organization settings and configuration
- Plan management and usage tracking
"""

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
import secrets
import logging
import bcrypt

from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["Organizations"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ==================== PYDANTIC MODELS ====================

class OrganizationCreate(BaseModel):
    """Create a new organization with admin user"""
    # Organization details
    name: str = Field(..., min_length=2, max_length=100)
    industry_type: str = Field(default="ev_garage")
    
    # Admin user details
    admin_name: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6)
    
    # Optional details
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    
    @validator('industry_type')
    def validate_industry(cls, v):
        valid = ['ev_garage', 'auto_repair', 'fleet_management', 'dealership', 'service_center', 'other']
        if v not in valid:
            raise ValueError(f'Industry must be one of: {valid}')
        return v


class OrganizationUpdate(BaseModel):
    """Update organization details"""
    name: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None


class UserInvite(BaseModel):
    """Invite a user to organization"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="technician")
    
    @validator('role')
    def validate_role(cls, v):
        valid = ['admin', 'manager', 'technician', 'accountant', 'customer']
        if v not in valid:
            raise ValueError(f'Role must be one of: {valid}')
        return v


class InviteAccept(BaseModel):
    """Accept an invitation"""
    invite_token: str
    password: str = Field(..., min_length=6)


class OrganizationResponse(BaseModel):
    """Organization response model"""
    organization_id: str
    name: str
    slug: str
    industry_type: str
    plan_type: str
    logo_url: Optional[str]
    is_active: bool
    created_at: str


# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def generate_slug(name: str) -> str:
    """Generate URL-safe slug from name"""
    import re
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug[:50]
    return f"{slug}-{uuid.uuid4().hex[:6]}"


# ==================== ORGANIZATION SIGNUP ====================

@router.post("/signup", response_model=Dict[str, Any])
async def signup_organization(data: OrganizationCreate):
    """
    Create a new organization with admin user.
    
    This is the main SaaS signup endpoint:
    1. Creates organization record
    2. Creates admin user
    3. Creates organization membership
    4. Returns JWT token for immediate login
    """
    # Check if admin email already exists
    existing_user = await db.users.find_one({"email": data.admin_email})
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Email already registered. Please login or use a different email."
        )
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate IDs
    org_id = f"org_{uuid.uuid4().hex[:12]}"
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    membership_id = f"mem_{uuid.uuid4().hex[:12]}"
    
    # Create organization
    org_doc = {
        "organization_id": org_id,
        "name": data.name,
        "slug": generate_slug(data.name),
        "industry_type": data.industry_type,
        "plan_type": "free_trial",  # Start with free trial
        "plan_expires_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        "logo_url": None,
        "website": data.website,
        "email": data.admin_email,
        "phone": data.phone,
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "country": data.country,
        "pincode": data.pincode,
        "gstin": data.gstin,
        "is_active": True,
        "is_onboarded": False,
        "total_users": 1,
        "total_vehicles": 0,
        "total_tickets": 0,
        "settings": {
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "date_format": "DD/MM/YYYY",
            "fiscal_year_start": "April"
        },
        "features": {
            "zoho_sync": False,
            "ai_assistant": True,
            "failure_intelligence": True,
            "multi_warehouse": False,
            "advanced_reports": False
        },
        "created_at": now,
        "updated_at": now,
        "created_by": user_id
    }
    
    # Create admin user
    user_doc = {
        "user_id": user_id,
        "email": data.admin_email,
        "password_hash": hash_password(data.admin_password),
        "name": data.admin_name,
        "role": "admin",
        "designation": "Owner",
        "phone": data.phone,
        "picture": None,
        "is_active": True,
        "email_verified": False,
        "created_at": now,
        "updated_at": now
    }
    
    # Create membership (owner role)
    membership_doc = {
        "membership_id": membership_id,
        "organization_id": org_id,
        "user_id": user_id,
        "role": "owner",
        "status": "active",
        "custom_permissions": [],
        "invited_by": None,
        "invited_at": None,
        "joined_at": now,
        "last_active_at": now,
        "created_at": now,
        "updated_at": now
    }
    
    # Insert all documents
    await db.organizations.insert_one(org_doc)
    await db.users.insert_one(user_doc)
    await db.organization_users.insert_one(membership_doc)
    
    # Initialize RBAC roles for the organization
    try:
        from core.tenant.rbac import get_tenant_rbac_service
        rbac_service = get_tenant_rbac_service()
        await rbac_service.initialize_org_roles(org_id, user_id)
    except Exception as e:
        logger.warning(f"Failed to initialize RBAC roles: {e}")
    
    # Create JWT token
    import jwt
    JWT_SECRET = os.environ.get("JWT_SECRET", "battwheels-secret-key")
    token = jwt.encode({
        "user_id": user_id,
        "email": data.admin_email,
        "role": "admin",
        "org_id": org_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }, JWT_SECRET, algorithm="HS256")
    
    # Log activity
    try:
        from core.tenant.observability import get_tenant_observability_service
        obs = get_tenant_observability_service()
        await obs.log_activity(
            organization_id=org_id,
            category="admin",
            action="organization_created",
            user_id=user_id,
            details={"name": data.name, "industry": data.industry_type}
        )
    except Exception as e:
        logger.warning(f"Failed to log activity: {e}")
    
    logger.info(f"New organization created: {data.name} ({org_id})")
    
    return {
        "success": True,
        "message": "Organization created successfully",
        "token": token,
        "organization": {
            "organization_id": org_id,
            "name": data.name,
            "slug": org_doc["slug"],
            "plan_type": "free_trial",
            "plan_expires_at": org_doc["plan_expires_at"]
        },
        "user": {
            "user_id": user_id,
            "email": data.admin_email,
            "name": data.admin_name,
            "role": "admin"
        }
    }


# ==================== ORGANIZATION DETAILS ====================

@router.get("/me")
async def get_current_organization(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get current user's organization details"""
    org = await db.organizations.find_one(
        {"organization_id": ctx.org_id},
        {"_id": 0}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get member count
    member_count = await db.organization_users.count_documents({
        "organization_id": ctx.org_id,
        "status": "active"
    })
    
    org["member_count"] = member_count
    
    return org


@router.put("/me")
async def update_organization(
    data: OrganizationUpdate,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Update organization details (admin only)"""
    # Check if user is admin/owner
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": ctx.user_id
    })
    
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update organization")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {"$set": update_dict}
    )
    
    return await get_current_organization(request, ctx)


@router.post("/me/complete-onboarding")
async def complete_onboarding(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Mark organization onboarding as complete"""
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {"$set": {
            "is_onboarded": True,
            "onboarded_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Onboarding completed"}


# ==================== USER INVITATIONS ====================

@router.post("/me/invite")
async def invite_user(
    data: UserInvite,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Invite a user to the organization.
    
    Creates an invitation record with a unique token.
    In production, this would send an email.
    """
    # Check if user is admin/owner
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": ctx.user_id
    })
    
    if not membership or membership.get("role") not in ["owner", "admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admins and managers can invite users")
    
    # Check if email already has a pending invite
    existing_invite = await db.organization_invites.find_one({
        "organization_id": ctx.org_id,
        "email": data.email,
        "status": "pending"
    })
    
    if existing_invite:
        raise HTTPException(status_code=400, detail="An invitation is already pending for this email")
    
    # Check if user already a member
    existing_user = await db.users.find_one({"email": data.email})
    if existing_user:
        existing_membership = await db.organization_users.find_one({
            "organization_id": ctx.org_id,
            "user_id": existing_user["user_id"]
        })
        if existing_membership:
            raise HTTPException(status_code=400, detail="User is already a member of this organization")
    
    now = datetime.now(timezone.utc)
    invite_token = secrets.token_urlsafe(32)
    
    invite_doc = {
        "invite_id": f"inv_{uuid.uuid4().hex[:12]}",
        "organization_id": ctx.org_id,
        "email": data.email,
        "name": data.name,
        "role": data.role,
        "token": invite_token,
        "status": "pending",
        "invited_by": ctx.user_id,
        "invited_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
        "accepted_at": None,
        "created_at": now.isoformat()
    }
    
    await db.organization_invites.insert_one(invite_doc)
    
    # Get organization name for the invite link
    org = await db.organizations.find_one({"organization_id": ctx.org_id})
    org_name = org.get("name", "Organization") if org else "Organization"
    
    # In production, send email here
    # For now, return the invite link
    invite_link = f"/accept-invite?token={invite_token}"
    
    logger.info(f"Invitation sent to {data.email} for org {ctx.org_id}")
    
    return {
        "success": True,
        "message": f"Invitation sent to {data.email}",
        "invite_id": invite_doc["invite_id"],
        "invite_link": invite_link,  # For development/testing
        "expires_at": invite_doc["expires_at"]
    }


@router.get("/me/invites")
async def list_invitations(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """List all pending invitations for the organization"""
    invites = await db.organization_invites.find(
        {"organization_id": ctx.org_id},
        {"_id": 0, "token": 0}  # Don't expose tokens
    ).sort("invited_at", -1).to_list(100)
    
    return {"invites": invites, "total": len(invites)}


@router.delete("/me/invites/{invite_id}")
async def cancel_invitation(
    invite_id: str,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Cancel a pending invitation"""
    result = await db.organization_invites.delete_one({
        "invite_id": invite_id,
        "organization_id": ctx.org_id,
        "status": "pending"
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")
    
    return {"success": True, "message": "Invitation cancelled"}


@router.post("/accept-invite")
async def accept_invitation(data: InviteAccept):
    """
    Accept an invitation and create user account.
    
    This endpoint is PUBLIC (no auth required) since the user
    doesn't have an account yet.
    """
    # Find the invitation
    invite = await db.organization_invites.find_one({
        "token": data.invite_token,
        "status": "pending"
    })
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    # Check expiration
    expires_at = datetime.fromisoformat(invite["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.organization_invites.update_one(
            {"invite_id": invite["invite_id"]},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": invite["email"]})
    
    if existing_user:
        user_id = existing_user["user_id"]
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": invite["email"],
            "password_hash": hash_password(data.password),
            "name": invite["name"],
            "role": invite["role"],
            "designation": None,
            "phone": None,
            "picture": None,
            "is_active": True,
            "email_verified": True,  # Verified via invite
            "created_at": now,
            "updated_at": now
        }
        await db.users.insert_one(user_doc)
    
    # Create organization membership
    membership_id = f"mem_{uuid.uuid4().hex[:12]}"
    membership_doc = {
        "membership_id": membership_id,
        "organization_id": invite["organization_id"],
        "user_id": user_id,
        "role": invite["role"],
        "status": "active",
        "custom_permissions": [],
        "invited_by": invite["invited_by"],
        "invited_at": invite["invited_at"],
        "joined_at": now,
        "last_active_at": now,
        "created_at": now,
        "updated_at": now
    }
    await db.organization_users.insert_one(membership_doc)
    
    # Update invitation status
    await db.organization_invites.update_one(
        {"invite_id": invite["invite_id"]},
        {"$set": {"status": "accepted", "accepted_at": now}}
    )
    
    # Update org user count
    await db.organizations.update_one(
        {"organization_id": invite["organization_id"]},
        {"$inc": {"total_users": 1}}
    )
    
    # Create JWT token
    import jwt
    JWT_SECRET = os.environ.get("JWT_SECRET", "battwheels-secret-key")
    token = jwt.encode({
        "user_id": user_id,
        "email": invite["email"],
        "role": invite["role"],
        "org_id": invite["organization_id"],
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }, JWT_SECRET, algorithm="HS256")
    
    # Get org details
    org = await db.organizations.find_one(
        {"organization_id": invite["organization_id"]},
        {"_id": 0, "name": 1, "slug": 1}
    )
    
    logger.info(f"User {invite['email']} accepted invite to org {invite['organization_id']}")
    
    return {
        "success": True,
        "message": "Welcome! You've joined the organization.",
        "token": token,
        "user": {
            "user_id": user_id,
            "email": invite["email"],
            "name": invite["name"],
            "role": invite["role"]
        },
        "organization": org
    }


# ==================== TEAM MANAGEMENT ====================

@router.get("/me/members")
async def list_members(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """List all members of the organization"""
    memberships = await db.organization_users.find(
        {"organization_id": ctx.org_id},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with user details
    members = []
    for m in memberships:
        user = await db.users.find_one(
            {"user_id": m["user_id"]},
            {"_id": 0, "password_hash": 0}
        )
        if user:
            members.append({
                "membership_id": m["membership_id"],
                "user_id": m["user_id"],
                "email": user.get("email"),
                "name": user.get("name"),
                "picture": user.get("picture"),
                "role": m["role"],
                "status": m["status"],
                "joined_at": m["joined_at"],
                "last_active_at": m.get("last_active_at")
            })
    
    return {"members": members, "total": len(members)}


@router.put("/me/members/{user_id}/role")
async def update_member_role(
    user_id: str,
    role: str,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Update a member's role (admin only)"""
    # Validate role
    valid_roles = ['admin', 'manager', 'technician', 'accountant', 'customer']
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # Check if current user is admin/owner
    current_membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": ctx.user_id
    })
    
    if not current_membership or current_membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    
    # Can't change owner's role
    target_membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": user_id
    })
    
    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if target_membership.get("role") == "owner":
        raise HTTPException(status_code=403, detail="Cannot change owner's role")
    
    await db.organization_users.update_one(
        {"organization_id": ctx.org_id, "user_id": user_id},
        {"$set": {"role": role, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"success": True, "message": f"Role updated to {role}"}


@router.delete("/me/members/{user_id}")
async def remove_member(
    user_id: str,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Remove a member from the organization"""
    # Check if current user is admin/owner
    current_membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": ctx.user_id
    })
    
    if not current_membership or current_membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    
    # Can't remove yourself or owner
    if user_id == ctx.user_id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    
    target_membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": user_id
    })
    
    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if target_membership.get("role") == "owner":
        raise HTTPException(status_code=403, detail="Cannot remove organization owner")
    
    await db.organization_users.delete_one({
        "organization_id": ctx.org_id,
        "user_id": user_id
    })
    
    # Update org user count
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {"$inc": {"total_users": -1}}
    )
    
    return {"success": True, "message": "Member removed"}


# ==================== USER'S ORGANIZATIONS ====================

@router.get("/my-organizations")
async def get_user_organizations(request: Request):
    """
    Get all organizations the current user belongs to.
    Used for organization switcher.
    """
    # Get user from token
    from utils.auth import get_current_user_from_request
    try:
        user = await get_current_user_from_request(request)
        user_id = user.get("user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get all memberships
    memberships = await db.organization_users.find(
        {"user_id": user_id, "status": "active"},
        {"_id": 0}
    ).to_list(20)
    
    organizations = []
    for m in memberships:
        org = await db.organizations.find_one(
            {"organization_id": m["organization_id"], "is_active": True},
            {"_id": 0}
        )
        if org:
            organizations.append({
                "organization_id": org["organization_id"],
                "name": org["name"],
                "slug": org["slug"],
                "logo_url": org.get("logo_url"),
                "plan_type": org.get("plan_type"),
                "role": m["role"],
                "joined_at": m["joined_at"]
            })
    
    return {
        "organizations": organizations,
        "total": len(organizations),
        "default_org": organizations[0]["organization_id"] if organizations else None
    }


# ==================== INITIALIZATION ====================

def init_organizations_router(app_db):
    """Initialize with app database connection"""
    global db
    db = app_db
    return router
