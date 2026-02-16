"""
Battwheels OS - Authentication Utilities
Shared auth helpers for all routes
"""
import os
import jwt
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
from typing import Optional

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "battwheels-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(request: Request, db) -> dict:
    """Extract and validate current user from request"""
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
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account deactivated")
    
    return user

async def require_auth(request: Request, db) -> dict:
    """Require any authenticated user"""
    return await get_current_user(request, db)

async def require_admin(request: Request, db) -> dict:
    """Require admin role"""
    user = await get_current_user(request, db)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_technician_or_admin(request: Request, db) -> dict:
    """Require technician or admin role"""
    user = await get_current_user(request, db)
    if user.get("role") not in ["admin", "technician", "manager"]:
        raise HTTPException(status_code=403, detail="Technician or Admin access required")
    return user

async def require_role(request: Request, db, roles: list) -> dict:
    """Require specific role(s)"""
    user = await get_current_user(request, db)
    if user.get("role") not in roles:
        raise HTTPException(status_code=403, detail=f"Required role: {', '.join(roles)}")
    return user

# User class for type hints
class UserContext:
    def __init__(self, user_dict: dict):
        self.user_id = user_dict.get("user_id")
        self.email = user_dict.get("email")
        self.name = user_dict.get("name")
        self.role = user_dict.get("role")
        self.is_active = user_dict.get("is_active", True)
        self.department = user_dict.get("department")
        self.designation = user_dict.get("designation")
