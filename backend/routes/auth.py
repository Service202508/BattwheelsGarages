"""
Battwheels OS - Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime, timezone, timedelta
import jwt
import uuid
import hashlib
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Import from main server (will be moved to separate modules)
SECRET_KEY = os.environ.get("SECRET_KEY", "battwheels-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

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

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )
    
    # Store session
    await db.sessions.insert_one({
        "session_token": token,
        "user_id": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    user_response = {k: v for k, v in user.items() if k != "password_hash"}
    return {"token": token, "user": user_response}

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
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/google")
async def google_auth(request: Request, response: Response):
    """Handle Google OAuth callback"""
    body = await request.json()
    google_token = body.get("token")
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
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )
    
    user_response = {k: v for k, v in user.items() if k not in ["password_hash", "_id"]}
    return {"token": token, "user": user_response}
