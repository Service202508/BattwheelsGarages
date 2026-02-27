"""
Battwheels OS - CANONICAL Authentication Module
=================================================
This is the SINGLE source of truth for JWT creation, decoding,
and password hashing across the entire application.

DO NOT create JWT functions anywhere else. Import from here.
"""
import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

# ==================== JWT CONFIGURATION (SINGLE SOURCE) ====================
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "168"))  # 7 days default

# Legacy alias
ALGORITHM = JWT_ALGORITHM

# Module-level database connection (used by get_current_user_from_request)
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
_client = AsyncIOMotorClient(MONGO_URL)
_db = _client[DB_NAME]

def hash_password(password: str) -> str:
    """Hash password using bcrypt (correct — not SHA256)"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    Supports bcrypt (new) and SHA256 (legacy migration path only).
    On SHA256 match: caller should re-hash to bcrypt (transparent migration).
    """
    if not hashed_password:
        return False
    # Try bcrypt first (preferred)
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
        pass
    # Legacy SHA256 fallback (for migrating old users)
    import hashlib
    sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return sha256_hash == hashed_password

def create_access_token(data: dict) -> str:
    """
    Create JWT access token. CANONICAL token creator.
    data MUST include: user_id, role. SHOULD include: org_id.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token. Raises HTTPException on failure."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def decode_token_safe(token: str) -> Optional[dict]:
    """Decode JWT without raising. Returns None on any error. For middleware use."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def create_token(user_id: str, email: str, role: str, org_id: str = None, password_version: float = 0) -> str:
    """Compatibility wrapper for create_access_token with named params."""
    payload = {"user_id": user_id, "email": email, "role": role, "pwd_v": password_version}
    if org_id:
        payload["org_id"] = org_id
    return create_access_token(payload)


async def get_current_user_from_request(request: Request) -> dict:
    """
    Extract and validate current user from request.
    Uses module-level database connection.
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
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = await _db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account deactivated")
    
    # Include org_id from token if present
    if "org_id" in payload:
        user["org_id"] = payload["org_id"]
    
    return user


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

# User class for type hints — supports both attribute AND dict access
class UserContext:
    def __init__(self, user_dict: dict):
        self._data = user_dict
        self.user_id = user_dict.get("user_id")
        self.email = user_dict.get("email")
        self.name = user_dict.get("name")
        self.role = user_dict.get("role")
        self.is_active = user_dict.get("is_active", True)
        self.department = user_dict.get("department")
        self.designation = user_dict.get("designation")
        self.organization_id = user_dict.get("organization_id")
        self.picture = user_dict.get("picture")

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __repr__(self):
        return f"UserContext({self._data})"

async def require_auth(request: Request, db=None) -> UserContext:
    """Require any authenticated user. Uses module db if not passed."""
    user_dict = await get_current_user(request, db or _db)
    return UserContext(user_dict)

async def require_admin(request: Request, db) -> UserContext:
    """Require admin role"""
    user = await get_current_user(request, db)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return UserContext(user)

async def require_technician_or_admin(request: Request, db) -> UserContext:
    """Require technician or admin role"""
    user = await get_current_user(request, db)
    if user.get("role") not in ["admin", "technician", "manager"]:
        raise HTTPException(status_code=403, detail="Technician or Admin access required")
    return UserContext(user)

async def require_role(request: Request, db, roles: list) -> UserContext:
    """Require specific role(s)"""
    user = await get_current_user(request, db)
    if user.get("role") not in roles:
        raise HTTPException(status_code=403, detail=f"Required role: {', '.join(roles)}")
    return UserContext(user)
