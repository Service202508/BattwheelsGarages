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

    # Self-serve signup extras
    vehicle_types: Optional[List[str]] = None  # ["2W", "3W", "4W"]

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


class BrandingSettings(BaseModel):
    """Organization branding configuration"""
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None  # Logo for dark backgrounds
    favicon_url: Optional[str] = None
    primary_color: str = "#10b981"  # Emerald-500 (default)
    secondary_color: str = "#059669"  # Emerald-600
    accent_color: str = "#f59e0b"  # Amber-500
    text_color: str = "#111827"  # Gray-900
    background_color: str = "#ffffff"  # White
    sidebar_color: str = "#1e293b"  # Slate-800
    company_tagline: Optional[str] = None
    custom_css: Optional[str] = None  # Advanced users only
    email_footer: Optional[str] = None
    show_powered_by: bool = True  # Show "Powered by Battwheels"


class CompleteStepRequest(BaseModel):
    step: str


ONBOARDING_STEPS = [
    "add_first_contact",
    "add_first_vehicle",
    "create_first_ticket",
    "add_inventory_item",
    "create_first_invoice",
    "invite_team_member",
]


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
    trial_ends_at = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()

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
        "plan_expires_at": trial_ends_at,
        "trial_ends_at": trial_ends_at,
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
        "vehicle_types": data.vehicle_types or [],
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
    
    # Create subscription for the organization
    try:
        from core.subscriptions import get_subscription_service, SubscriptionCreate, PlanCode, BillingCycle
        sub_service = get_subscription_service()
        
        # Create subscription with trial
        sub_data = SubscriptionCreate(
            plan_code=PlanCode.STARTER,
            billing_cycle=BillingCycle.MONTHLY,
            start_trial=True
        )
        subscription = await sub_service.create_subscription(org_id, sub_data, user_id)
        logger.info(f"Created subscription {subscription.subscription_id} for org {org_id}")
    except Exception as e:
        logger.warning(f"Failed to create subscription: {e}")
    
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

    # Send welcome email (non-blocking)
    try:
        from services.email_service import EmailService
        app_url = os.environ.get("REACT_APP_BACKEND_URL", "https://app.battwheels.in").replace("/api", "")
        trial_end_date = datetime.now(timezone.utc) + timedelta(days=14)
        trial_end_str = trial_end_date.strftime("%d %B %Y")
        subject = "Welcome to Battwheels OS — Your 14-day trial has started"
        html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #080C0F; color: #F4F6F0; padding: 32px; border-radius: 8px;">
  <h1 style="color: #C8FF00; font-size: 24px; margin-bottom: 8px;">Welcome to Battwheels OS</h1>
  <p>Hi {data.admin_name},</p>
  <p>Your workshop <strong>{data.name}</strong> is now live on Battwheels OS.</p>
  <p>
    <a href="{app_url}" style="display: inline-block; background: #C8FF00; color: #080C0F; font-weight: bold; padding: 12px 24px; border-radius: 4px; text-decoration: none; margin: 16px 0;">
      Log in to your dashboard →
    </a>
  </p>
  <p>Your free trial ends on <strong>{trial_end_str}</strong>. No credit card required until then.</p>
  <p>Need help? Just reply to this email — we're here.</p>
  <p style="color: rgba(244,246,240,0.45); font-size: 12px; margin-top: 32px;">
    Battwheels OS — EV Workshop Intelligence Platform<br>
    <a href="https://battwheels.in" style="color: #C8FF00;">battwheels.in</a>
  </p>
</div>
"""
        await EmailService.send_generic_email(
            to_email=data.admin_email,
            to_name=data.admin_name,
            subject=subject,
            html_body=html_body,
        )
        logger.info(f"Welcome email sent to {data.admin_email}")
    except Exception as e:
        logger.warning(f"Failed to send welcome email: {e}")

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
    
    # Get organization name and inviter name
    org = await db.organizations.find_one({"organization_id": ctx.org_id})
    org_name = org.get("name", "Organization") if org else "Organization"
    
    inviter = await db.users.find_one({"user_id": ctx.user_id})
    inviter_name = inviter.get("name", "Team Admin") if inviter else "Team Admin"
    
    # Send invitation email
    invite_link = f"/accept-invite?token={invite_token}"
    try:
        from services.email_service import email_service
        await email_service.send_invitation_email(
            to_email=data.email,
            to_name=data.name,
            org_name=org_name,
            inviter_name=inviter_name,
            role=data.role,
            invite_link=invite_link
        )
    except Exception as e:
        logger.warning(f"Failed to send invitation email: {e}")
    
    logger.info(f"Invitation sent to {data.email} for org {org_name} ({ctx.org_id})")
    
    return {
        "success": True,
        "message": f"Invitation sent to {data.email}",
        "invite_id": invite_doc["invite_id"],
        "invite_link": invite_link,
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
                "membership_id": m.get("membership_id") or f"mem_{m.get('user_id', '')}",
                "user_id": m["user_id"],
                "email": user.get("email"),
                "name": user.get("name"),
                "picture": user.get("picture"),
                "role": m["role"],
                "status": m["status"],
                "joined_at": m.get("joined_at", m.get("created_at", "")),
                "last_active_at": m.get("last_active_at")
            })
    
    return {"members": members, "total": len(members)}


@router.patch("/me/members/{user_id}/role")
async def update_member_role(
    user_id: str,
    data: dict,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Update a member's role (admin only)"""
    role = data.get("role")
    # Validate role
    valid_roles = ['admin', 'manager', 'technician', 'accountant', 'customer', 'viewer']
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
                "joined_at": m.get("joined_at", m.get("created_at", ""))
            })
    
    return {
        "organizations": organizations,
        "total": len(organizations),
        "default_org": organizations[0]["organization_id"] if organizations else None
    }


# ==================== SETUP WIZARD ====================

@router.patch("/me/settings")
async def update_organization_settings(
    data: dict,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Update organization settings (used by setup wizard and settings page)"""
    # Check if user is admin/owner
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": ctx.user_id
    })
    
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update settings")
    
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Handle top-level fields
    if "name" in data:
        update_doc["name"] = data["name"]
    if "industry_type" in data:
        update_doc["industry_type"] = data["industry_type"]
    
    # Handle nested settings
    if "settings" in data:
        for key, value in data["settings"].items():
            update_doc[f"settings.{key}"] = value
    
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {"$set": update_doc}
    )
    
    return {"success": True, "message": "Settings updated"}


@router.post("/me/complete-setup")
async def complete_organization_setup(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Mark organization setup as complete"""
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {
            "$set": {
                "setup_completed": True,
                "setup_completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"success": True, "message": "Setup completed"}


@router.get("/me/setup-status")
async def get_setup_status(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Check if organization has completed setup"""
    org = await db.organizations.find_one(
        {"organization_id": ctx.org_id},
        {"_id": 0, "setup_completed": 1, "setup_completed_at": 1, "created_at": 1}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "setup_completed": org.get("setup_completed", False),
        "setup_completed_at": org.get("setup_completed_at"),
        "created_at": org.get("created_at")
    }


# ==================== ONBOARDING CHECKLIST ====================

@router.get("/onboarding/status")
async def get_onboarding_status(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get onboarding status with auto-detected completed steps"""
    org = await db.organizations.find_one(
        {"organization_id": ctx.org_id},
        {"_id": 0, "onboarding_completed": 1, "onboarding_steps_completed": 1, "created_at": 1}
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    onboarding_completed = org.get("onboarding_completed", False)
    created_at_str = org.get("created_at", "")

    # Determine if banner should be shown (< 7 days old and not completed)
    show_onboarding = False
    if not onboarding_completed:
        try:
            from dateutil.parser import parse as parse_date
            created_at = parse_date(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - created_at).days
            show_onboarding = age_days < 7
        except Exception:
            show_onboarding = True

    # Auto-detect completed steps by querying actual data counts
    auto_steps = []
    contacts_count = await db.contacts.count_documents({"organization_id": ctx.org_id})
    if contacts_count > 0:
        auto_steps.append("add_first_contact")

    vehicles_count = await db.vehicles.count_documents({"organization_id": ctx.org_id})
    if vehicles_count > 0:
        auto_steps.append("add_first_vehicle")

    tickets_count = await db.tickets.count_documents({"organization_id": ctx.org_id})
    if tickets_count > 0:
        auto_steps.append("create_first_ticket")

    items_count = await db.items.count_documents({"organization_id": ctx.org_id})
    if items_count > 0:
        auto_steps.append("add_inventory_item")

    invoices_count = await db.invoices.count_documents({"organization_id": ctx.org_id})
    if invoices_count > 0:
        auto_steps.append("create_first_invoice")

    members_count = await db.organization_users.count_documents(
        {"organization_id": ctx.org_id, "status": "active"}
    )
    if members_count > 1:
        auto_steps.append("invite_team_member")

    stored_steps = org.get("onboarding_steps_completed", [])
    all_completed = list(set(auto_steps + stored_steps))

    # Persist if new steps were auto-detected
    if set(auto_steps) - set(stored_steps):
        all_done = all(s in all_completed for s in ONBOARDING_STEPS)
        await db.organizations.update_one(
            {"organization_id": ctx.org_id},
            {"$set": {
                "onboarding_steps_completed": all_completed,
                "onboarding_completed": all_done or onboarding_completed,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        if all_done:
            onboarding_completed = True

    completed_count = len(all_completed)
    total_steps = len(ONBOARDING_STEPS)
    all_done_final = completed_count >= total_steps

    return {
        "onboarding_completed": onboarding_completed or all_done_final,
        "onboarding_steps_completed": all_completed,
        "show_onboarding": show_onboarding,
        "total_steps": total_steps,
        "completed_count": completed_count,
        "org_created_at": created_at_str
    }


@router.post("/onboarding/complete-step")
async def complete_onboarding_step(
    data: CompleteStepRequest,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Mark a specific onboarding step as complete"""
    if data.step not in ONBOARDING_STEPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step. Must be one of: {ONBOARDING_STEPS}"
        )

    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {"$addToSet": {"onboarding_steps_completed": data.step}}
    )

    org = await db.organizations.find_one(
        {"organization_id": ctx.org_id},
        {"_id": 0, "onboarding_steps_completed": 1}
    )
    steps = org.get("onboarding_steps_completed", [])
    all_done = all(s in steps for s in ONBOARDING_STEPS)

    if all_done:
        await db.organizations.update_one(
            {"organization_id": ctx.org_id},
            {"$set": {"onboarding_completed": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )

    return {
        "success": True,
        "step": data.step,
        "all_completed": all_done,
        "completed_steps": steps
    }


@router.post("/onboarding/skip")
async def skip_onboarding(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Skip/dismiss the onboarding checklist"""
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {"$set": {
            "onboarding_completed": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"success": True, "message": "Onboarding skipped"}


# ==================== BRANDING ====================

DEFAULT_BRANDING = {
    "logo_url": None,
    "logo_dark_url": None,
    "favicon_url": None,
    "primary_color": "#10b981",
    "secondary_color": "#059669",
    "accent_color": "#f59e0b",
    "text_color": "#111827",
    "background_color": "#ffffff",
    "sidebar_color": "#1e293b",
    "company_tagline": None,
    "custom_css": None,
    "email_footer": None,
    "show_powered_by": True
}


@router.get("/me/branding")
async def get_branding(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get organization branding settings"""
    org = await db.organizations.find_one(
        {"organization_id": ctx.org_id},
        {"_id": 0, "name": 1, "branding": 1, "logo_url": 1}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Merge with defaults
    branding = {**DEFAULT_BRANDING, **(org.get("branding", {}))}
    
    # Legacy logo_url support
    if not branding["logo_url"] and org.get("logo_url"):
        branding["logo_url"] = org["logo_url"]
    
    return {
        "organization_name": org.get("name"),
        "branding": branding
    }


@router.put("/me/branding")
async def update_branding(
    data: BrandingSettings,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Update organization branding settings (admin only)"""
    # Check admin permission
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": ctx.user_id
    })
    
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update branding")
    
    # Validate colors (basic hex validation)
    import re
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    
    for field in ["primary_color", "secondary_color", "accent_color", "text_color", "background_color", "sidebar_color"]:
        value = getattr(data, field, None)
        if value and not hex_pattern.match(value):
            raise HTTPException(status_code=400, detail=f"Invalid hex color for {field}: {value}")
    
    # Sanitize custom CSS (basic XSS prevention)
    if data.custom_css:
        # Remove script tags and javascript: urls
        data.custom_css = re.sub(r'<script[^>]*>.*?</script>', '', data.custom_css, flags=re.IGNORECASE | re.DOTALL)
        data.custom_css = re.sub(r'javascript:', '', data.custom_css, flags=re.IGNORECASE)
    
    branding_dict = data.model_dump(exclude_none=False)
    
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {
            "$set": {
                "branding": branding_dict,
                "logo_url": data.logo_url,  # Keep legacy field in sync
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Branding updated for org {ctx.org_id}")
    
    return {
        "success": True,
        "message": "Branding updated successfully",
        "branding": branding_dict
    }


@router.post("/me/branding/reset")
async def reset_branding(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Reset branding to defaults (admin only)"""
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id,
        "user_id": ctx.user_id
    })
    
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can reset branding")
    
    await db.organizations.update_one(
        {"organization_id": ctx.org_id},
        {
            "$set": {
                "branding": DEFAULT_BRANDING,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "success": True,
        "message": "Branding reset to defaults",
        "branding": DEFAULT_BRANDING
    }


# ==================== EMAIL SETTINGS (PER-ORG) ====================

class EmailSettings(BaseModel):
    provider: str = "resend"  # resend or smtp
    api_key: str = Field(..., min_length=1)
    from_email: str = Field(..., min_length=5)
    from_name: str = Field(..., min_length=1)


@router.get("/me/email-settings")
async def get_email_settings(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get email settings status (keys masked)"""
    from services.credential_service import get_email_credentials, EMAIL_SMTP
    creds = await get_email_credentials(ctx.org_id)
    has_own = not creds.get("_using_global", False)
    return {
        "configured": has_own,
        "using_global": creds.get("_using_global", True),
        "provider": creds.get("provider", "resend"),
        "from_email": creds.get("from_email", ""),
        "from_name": creds.get("from_name", ""),
        "api_key_masked": ("***" + creds.get("api_key", "")[-4:]) if creds.get("api_key") else None,
    }


@router.post("/me/email-settings")
async def save_email_settings(
    data: EmailSettings,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Save per-org email settings (admin only)"""
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id, "user_id": ctx.user_id
    })
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update email settings")

    from services.credential_service import save_credentials, EMAIL_SMTP
    await save_credentials(ctx.org_id, EMAIL_SMTP, {
        "provider": data.provider,
        "api_key": data.api_key,
        "from_email": data.from_email,
        "from_name": data.from_name,
    })
    return {"success": True, "message": "Email settings saved"}


@router.delete("/me/email-settings")
async def remove_email_settings(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Remove per-org email settings (falls back to global)"""
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id, "user_id": ctx.user_id
    })
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update email settings")

    from services.credential_service import delete_credentials, EMAIL_SMTP
    await delete_credentials(ctx.org_id, EMAIL_SMTP)
    return {"success": True, "message": "Email settings removed, using platform defaults"}


# ==================== WHATSAPP SETTINGS ====================

class WhatsAppSettings(BaseModel):
    phone_number_id: str = Field(..., min_length=1)
    access_token: str = Field(..., min_length=10)


@router.get("/me/whatsapp-settings")
async def get_whatsapp_settings(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get WhatsApp integration status (token masked)"""
    from services.credential_service import get_credentials, WHATSAPP
    creds = await get_credentials(ctx.org_id, WHATSAPP)
    configured = bool(creds and creds.get("phone_number_id") and creds.get("access_token"))
    return {
        "configured": configured,
        "phone_number_id": creds.get("phone_number_id", "") if creds else "",
        "access_token_masked": ("***" + creds.get("access_token", "")[-6:]) if (creds and creds.get("access_token")) else None,
    }


@router.post("/me/whatsapp-settings")
async def save_whatsapp_settings(
    data: WhatsAppSettings,
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Save WhatsApp Business API credentials (admin only)"""
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id, "user_id": ctx.user_id
    })
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update WhatsApp settings")

    from services.credential_service import save_credentials, WHATSAPP
    await save_credentials(ctx.org_id, WHATSAPP, {
        "phone_number_id": data.phone_number_id,
        "access_token": data.access_token,
    })
    return {"success": True, "message": "WhatsApp settings saved"}


@router.delete("/me/whatsapp-settings")
async def remove_whatsapp_settings(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Remove WhatsApp credentials"""
    membership = await db.organization_users.find_one({
        "organization_id": ctx.org_id, "user_id": ctx.user_id
    })
    if not membership or membership.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update WhatsApp settings")

    from services.credential_service import delete_credentials, WHATSAPP
    await delete_credentials(ctx.org_id, WHATSAPP)
    return {"success": True, "message": "WhatsApp settings removed"}


@router.post("/me/whatsapp-test")
async def test_whatsapp(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Send a test WhatsApp message to the org admin's phone.
    Returns { delivered: bool, message_id: str }
    """
    # Get admin user's phone number
    user = await db.users.find_one({"user_id": ctx.user_id}, {"_id": 0, "phone": 1, "name": 1})
    admin_phone = user.get("phone") if user else None

    if not admin_phone:
        # Try org phone
        org = await db.organizations.find_one({"organization_id": ctx.org_id}, {"_id": 0, "phone": 1})
        admin_phone = org.get("phone") if org else None

    if not admin_phone:
        raise HTTPException(
            status_code=400,
            detail="No phone number found on your user profile or organisation. Add a phone number first."
        )

    from services.whatsapp_service import send_whatsapp_text, WhatsAppNotConfigured, WhatsAppError
    try:
        result = await send_whatsapp_text(
            to_phone=admin_phone,
            message="Battwheels OS WhatsApp test — your integration is working ✓",
            org_id=ctx.org_id,
        )
        return {"delivered": True, "message_id": result.get("message_id")}
    except WhatsAppNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WhatsAppError as e:
        return {"delivered": False, "error": str(e)}


# ==================== INITIALIZATION ====================

def init_organizations_router(app_db):
    """Initialize with app database connection"""
    global db
    db = app_db
    return router
