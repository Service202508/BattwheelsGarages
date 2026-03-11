"""
Battwheels OS - Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import os

# CANONICAL JWT — single source from utils/auth
from utils.auth import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS,
    create_access_token, decode_token,
    hash_password, verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "customer"
    phone: Optional[str] = None

class TokenResponse(BaseModel):
    token: str
    user: dict

# These will be injected from main app
db = None

def init_router(database):
    global db
    db = database
    return router

@router.post("/login")
async def login(credentials: UserLogin, response: Response):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    # Include org_id in token if user has exactly 1 org
    token_data = {"user_id": user["user_id"], "role": user["role"], "email": user.get("email", "")}
    current_org_id = None
    
    # Fetch user's organizations for multi-org support
    organizations = []
    try:
        memberships = await db.organization_users.find(
            {"user_id": user["user_id"], "status": "active"},
            {"_id": 0}
        ).to_list(20)
        
        for m in memberships:
            org = await db.organizations.find_one(
                {"organization_id": m["organization_id"], "is_active": True},
                {"_id": 0}
            )
            if org:
                organizations.append({
                    "organization_id": org["organization_id"],
                    "name": org["name"],
                    "slug": org.get("slug"),
                    "logo_url": org.get("logo_url"),
                    "plan_type": org.get("plan_type", "free"),
                    "role": m["role"]
                })
        
        if len(organizations) >= 1:
            current_org_id = organizations[0]["organization_id"]
            token_data["org_id"] = current_org_id
            # Use the role from membership, not user record
            token_data["role"] = organizations[0]["role"]
    except Exception:
        pass
    
    token = create_access_token(token_data)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600
    )
    
    # Store session
    await db.sessions.insert_one({
        "session_token": token,
        "user_id": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    user_response = {k: v for k, v in user.items() if k not in ("password_hash", "password", "verification_token", "verification_token_expires")}
    
    return {
        "token": token, 
        "user": user_response,
        "email_verified": user.get("email_verified", True),
        "organizations": organizations,
        "organization": organizations[0] if len(organizations) == 1 else None,
        "current_organization": current_org_id
    }

@router.post("/register")
async def register(user_data: UserRegister):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "phone": user_data.phone,
        "picture": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_access_token({"user_id": user_id, "role": user_data.role})
    user_response = {k: v for k, v in user_doc.items() if k not in ["password_hash", "_id"]}
    
    return {"token": token, "user": user_response}


@router.get("/verify-email")
async def verify_email(token: str):
    """Verify user's email address via token from verification link."""
    now = datetime.now(timezone.utc).isoformat()
    user = await db.users.find_one({
        "verification_token": token,
        "verification_token_expires": {"$gt": now}
    }, {"_id": 1, "email": 1, "email_verified": 1})
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link. Please request a new one.")
    
    if user.get("email_verified"):
        return {"success": True, "message": "Email is already verified."}
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "email_verified": True,
            "verification_token": None,
            "verification_token_expires": None,
            "verified_at": now
        }}
    )
    return {"success": True, "message": "Email verified successfully. You can now login."}


@router.post("/resend-verification")
async def resend_verification(request: Request):
    """Resend verification email to a user who hasn't verified yet."""
    body = await request.json()
    email = body.get("email", "").strip().lower()
    
    # Generic response to avoid email enumeration
    generic_msg = "If this email is registered, a verification link has been sent."
    
    if not email:
        return {"message": generic_msg}
    
    user = await db.users.find_one({"email": email}, {"_id": 1, "email_verified": 1, "name": 1})
    if not user:
        return {"message": generic_msg}
    
    if user.get("email_verified"):
        return {"message": "Email is already verified."}
    
    new_token = str(uuid.uuid4())
    now_dt = datetime.now(timezone.utc)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "verification_token": new_token,
            "verification_token_expires": (now_dt + timedelta(hours=24)).isoformat()
        }}
    )
    
    # Send verification email
    try:
        from services.email_service import EmailService
        base_url = os.environ.get("APP_URL", "https://battwheels.com")
        verification_url = f"{base_url}/verify-email?token={new_token}"
        html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0e12; color: #f4f6f0; padding: 40px; border-radius: 8px;">
  <div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #CBFF00; font-size: 24px; margin: 0;">Battwheels OS</h1>
  </div>
  <h2 style="color: white; font-size: 20px;">Verify Your Email</h2>
  <p style="color: #9ca3af; line-height: 1.6;">
    Hi {user.get("name", "there")},<br><br>
    Please verify your email to activate your Battwheels OS account.
  </p>
  <div style="text-align: center; margin: 30px 0;">
    <a href="{verification_url}"
      style="background: #CBFF00; color: #0a0e12; padding: 14px 32px;
      text-decoration: none; font-weight: bold; border-radius: 8px;
      display: inline-block; font-size: 14px;">VERIFY MY EMAIL</a>
  </div>
  <p style="color: #6b7280; font-size: 13px;">This link expires in 24 hours.</p>
  <hr style="border-color: #1f2937; margin: 30px 0;">
  <p style="color: #4b5563; font-size: 12px; text-align: center;">&copy; 2026 Battwheels Services Private Limited</p>
</div>"""
        await EmailService.send_email(to=email, subject="Verify your Battwheels OS account", html_content=html_body)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to resend verification email: {e}")
    
    return {"message": generic_msg}


@router.post("/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_current_user(request: Request):
    # Get token from cookie or header
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0, "verification_token": 0, "verification_token_expires": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.post("/google")
async def google_auth(request: Request, response: Response):
    """Handle Google OAuth callback"""
    body = await request.json()
    # google_token could be used for validation in the future
    _ = body.get("token")
    user_info = body.get("user")
    
    if not user_info:
        raise HTTPException(status_code=400, detail="User info required")
    
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user = existing_user
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": email,
            "password_hash": "",
            "name": name,
            "role": "customer",
            "phone": None,
            "picture": picture,
            "is_active": True,
            "auth_provider": "google",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
    
    token = create_access_token({"user_id": user["user_id"], "role": user["role"]})
    
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600
    )
    
    user_response = {k: v for k, v in user.items() if k not in ["password_hash", "_id"]}
    return {"token": token, "user": user_response}


class SwitchOrganizationRequest(BaseModel):
    organization_id: str


@router.post("/switch-organization")
async def switch_organization(request: Request, body: SwitchOrganizationRequest, response: Response):
    """
    Switch to a different organization.
    Creates a new token with the selected org_id embedded.
    """
    # Get token from cookie or header
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Verify user is a member of the requested organization
    membership = await db.organization_users.find_one({
        "user_id": user_id,
        "organization_id": body.organization_id,
        "status": "active"
    })
    
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")
    
    # Get organization details
    org = await db.organizations.find_one(
        {"organization_id": body.organization_id, "is_active": True},
        {"_id": 0}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Create new token with org_id
    new_token = create_access_token({
        "user_id": user_id, 
        "role": membership["role"],
        "org_id": body.organization_id
    })
    
    # Update cookie
    response.set_cookie(
        key="session_token",
        value=new_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600
    )
    
    # Update last active timestamp
    await db.organization_users.update_one(
        {"user_id": user_id, "organization_id": body.organization_id},
        {"$set": {"last_active_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "token": new_token,
        "organization": {
            "organization_id": org["organization_id"],
            "name": org["name"],
            "slug": org.get("slug"),
            "logo_url": org.get("logo_url"),
            "plan_type": org.get("plan_type", "free")
        },
        "role": membership["role"]
    }
