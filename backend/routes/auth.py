"""
Battwheels OS - Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
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
    
    token = create_access_token({"user_id": user["user_id"], "role": user["role"]})
    
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
    
    user_response = {k: v for k, v in user.items() if k != "password_hash"}
    
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
    except Exception:
        # If org fetch fails, continue without orgs
        pass
    
    return {
        "token": token, 
        "user": user_response,
        "organizations": organizations,
        "organization": organizations[0] if len(organizations) == 1 else None
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
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
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
