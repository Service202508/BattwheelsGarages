"""
Battwheels OS - Core Auth Routes (extracted from server.py)
Registration, login, session, password management
"""
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import os
import hashlib
import logging

from utils.auth import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS,
    create_access_token, decode_token, hash_password, verify_password,
)
from schemas.models import UserCreate, UserLogin, User, UserUpdate
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth Core"])
db = None

def init_router(database):
    global db
    db = database

@router.post("/auth/register")
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "designation": user_data.designation,
        "phone": user_data.phone,
        "picture": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, user_data.email, user_data.role)
    return {"token": token, "user_id": user_id, "role": user_data.role}

@router.post("/auth/login")
async def login(credentials: UserLogin):
    """
    Login endpoint with multi-organization support.
    
    Returns user's organizations for org switcher functionality.
    If user belongs to multiple orgs, they can switch after login.
    """
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    stored_hash = user.get("password_hash", "")
    if not verify_password(credentials.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    # Transparent migration: if stored hash is SHA256 (64-char hex), re-hash to bcrypt
    if stored_hash and not (stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$")):
        new_bcrypt_hash = hash_password(credentials.password)
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"password_hash": new_bcrypt_hash}}
        )
        logger.info(f"Migrated SHA256 password to bcrypt for user {user['user_id']}")
    
    # Get user's organizations
    memberships = await db.organization_users.find(
        {"user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    ).to_list(20)
    
    organizations = []
    default_org_id = None
    
    for m in memberships:
        org = await db.organizations.find_one(
            {"organization_id": m["organization_id"], "is_active": True},
            {"_id": 0, "organization_id": 1, "name": 1, "slug": 1, "logo_url": 1, "plan_type": 1}
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
            if default_org_id is None:
                default_org_id = org["organization_id"]
    
    # Create token with default org
    token = create_token(user["user_id"], user["email"], user["role"], org_id=default_org_id, password_version=user.get("password_version", 0))
    
    # Return single org object if user has exactly one organization (for auto-selection)
    single_org = organizations[0] if len(organizations) == 1 else None
    
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "designation": user.get("designation"),
            "picture": user.get("picture"),
            "is_platform_admin": bool(user.get("is_platform_admin", False))
        },
        "organizations": organizations,
        "organization": single_org,  # Include full org object for single org users
        "current_organization": default_org_id
    }

@router.post("/auth/switch-organization")
async def switch_organization(request: Request):
    """
    Switch to a different organization.
    
    Returns a new token with the selected organization context.
    """
    body = await request.json()
    target_org_id = body.get("organization_id")
    
    if not target_org_id:
        raise HTTPException(status_code=400, detail="organization_id is required")
    
    # Get current user
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify user is a member of the target org
    membership = await db.organization_users.find_one({
        "user_id": user.user_id,
        "organization_id": target_org_id,
        "status": "active"
    })
    
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")
    
    # Create new token with target org
    token = create_token(user.user_id, user.email, membership["role"], org_id=target_org_id)
    
    # Get org details
    org = await db.organizations.find_one(
        {"organization_id": target_org_id},
        {"_id": 0, "organization_id": 1, "name": 1, "slug": 1, "logo_url": 1, "plan_type": 1}
    )
    
    # Update last active
    await db.organization_users.update_one(
        {"organization_id": target_org_id, "user_id": user.user_id},
        {"$set": {"last_active_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "token": token,
        "organization": org,
        "role": membership["role"]
    }

@router.post("/auth/session")
async def process_google_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        google_data = resp.json()
    
    existing_user = await db.users.find_one({"email": google_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": google_data["name"], "picture": google_data["picture"]}}
        )
        role = existing_user["role"]
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": google_data["email"],
            "name": google_data["name"],
            "picture": google_data["picture"],
            "role": "customer",
            "designation": None,
            "phone": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        role = "customer"
    
    session_token = google_data["session_token"]
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return {
        "user": {
            "user_id": user_id,
            "email": google_data["email"],
            "name": google_data["name"],
            "role": role,
            "picture": google_data["picture"]
        }
    }

@router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Fetch full user doc to include is_platform_admin
    full_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "designation": user.designation,
        "picture": user.picture,
        "is_platform_admin": bool(full_user.get("is_platform_admin", False)) if full_user else False
    }

@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ==================== PASSWORD MANAGEMENT ====================


def _validate_password_strength(v: str) -> str:
    import re
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
        raise ValueError("Password must contain at least one special character")
    return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_new_password(cls, v):
        return _validate_password_strength(v)

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_new_password(cls, v):
        return _validate_password_strength(v)

class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_new_password(cls, v):
        return _validate_password_strength(v)


@router.post("/auth/change-password")
async def change_password(request: Request, data: ChangePasswordRequest):
    """Self-service password change — requires current password"""
    user = await require_auth(request)
    full_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stored_hash = full_user.get("password_hash", "")
    if not stored_hash:
        raise HTTPException(status_code=400, detail="Account uses social login — no password to change")
    
    if not verify_password(data.current_password, stored_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    new_hash = hash_password(data.new_password)
    new_pwd_version = datetime.now(timezone.utc).timestamp()
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "password_hash": new_hash,
            "password_version": new_pwd_version,
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    logger.info(f"Password changed for user {user.user_id}")
    from utils.audit import log_audit, AuditAction
    await log_audit(db, AuditAction.PASSWORD_CHANGED, "", user.user_id, "user", user.user_id)
    return {"message": "Password changed successfully"}


@router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Send a time-limited password reset link via email"""
    import secrets, hashlib
    user = await db.users.find_one({"email": data.email}, {"_id": 0, "password_hash": 0})
    # Always return success to prevent email enumeration
    if not user:
        logger.info(f"Forgot password for non-existent email: {data.email}")
        return {"message": "If an account with that email exists, a reset link has been sent."}
    
    # Generate a secure token
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Store hashed token with 1-hour expiry
    await db.password_reset_tokens.delete_many({"user_id": user["user_id"]})  # Remove old tokens
    await db.password_reset_tokens.insert_one({
        "user_id": user["user_id"],
        "email": user["email"],
        "token_hash": token_hash,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "used": False
    })
    
    # Build reset link using FRONTEND URL
    frontend_url = os.environ.get("APP_URL", os.environ.get("REACT_APP_BACKEND_URL", "https://battwheels.com"))
    reset_link = f"{frontend_url}/reset-password?token={raw_token}"
    
    # Send email
    try:
        from services.email_service import EmailService
        await EmailService.send_email(
            to=user["email"],
            subject="Reset your Battwheels OS password",
            html_content=f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h2 style="margin: 0 0 20px; color: #111827; font-size: 20px;">Reset Your Password</h2>
                <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                    Hi {user.get('name', 'there')},
                </p>
                <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                    We received a request to reset your password. Click the button below to create a new password:
                </p>
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td align="center" style="padding: 20px 0;">
                            <a href="{reset_link}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                                Reset Password
                            </a>
                        </td>
                    </tr>
                </table>
                <p style="margin: 24px 0 0; color: #9ca3af; font-size: 14px;">
                    This link expires in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                </p>
            </div>
            """
        )
        logger.info(f"Password reset email sent to {user['email']}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
    
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using a valid token from the forgot-password email"""
    import hashlib
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    
    token_doc = await db.password_reset_tokens.find_one({
        "token_hash": token_hash,
        "used": False,
    })
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    # Compare expiry — handle both naive and aware datetimes from MongoDB
    expires_at = token_doc["expires_at"]
    now_utc = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now_utc > expires_at:
        await db.password_reset_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    
    # Update password
    new_hash = hash_password(data.new_password)
    new_pwd_version = datetime.now(timezone.utc).timestamp()
    await db.users.update_one(
        {"user_id": token_doc["user_id"]},
        {"$set": {
            "password_hash": new_hash,
            "password_version": new_pwd_version,
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})
    
    logger.info(f"Password reset completed for user {token_doc['user_id']}")
    return {"message": "Password has been reset successfully. You can now log in with your new password."}


@router.post("/employees/{employee_id}/reset-password")
async def admin_reset_employee_password(employee_id: str, request: Request):
    """Admin/Owner resets an employee's password"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    from utils.auth import decode_token
    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if payload.get("role") not in ["owner", "admin", "org_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can reset passwords")
    
    employee = await db.users.find_one({"user_id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    import secrets
    temp_password = secrets.token_urlsafe(12)
    new_hash = hash_password(temp_password)
    
    await db.users.update_one(
        {"user_id": employee_id},
        {"$set": {
            "password_hash": new_hash,
            "password_version": datetime.now(timezone.utc).timestamp(),
            "must_change_password": True,
        }}
    )
    
    return {"message": "Password reset successfully", "temporary_password": temp_password}