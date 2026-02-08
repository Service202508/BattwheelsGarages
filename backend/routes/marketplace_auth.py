"""
Marketplace Auth Routes - Phone OTP Based Authentication
Supports role-based access: public, fleet, technician
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
import random
import string

router = APIRouter(prefix="/api/marketplace/auth", tags=["Marketplace Auth"])

from server import db

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "battwheels-marketplace-secret-key")
JWT_ALGORITHM = "HS256"
OTP_EXPIRY_MINUTES = 10

# ============== MODELS ==============

class SendOTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=13)

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
    device_info: Optional[dict] = None

class UserProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    business_name: Optional[str] = None
    gst_number: Optional[str] = None
    addresses: list = []

class AddressCreate(BaseModel):
    label: str  # home, work, warehouse
    name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    is_default: bool = False

# ============== HELPER FUNCTIONS ==============

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def create_token(user_id: str, phone: str, role: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "phone": phone,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def normalize_phone(phone: str) -> str:
    """Normalize phone number to +91XXXXXXXXXX format"""
    phone = ''.join(filter(str.isdigit, phone))
    if len(phone) == 10:
        return f"+91{phone}"
    elif len(phone) == 12 and phone.startswith("91"):
        return f"+{phone}"
    return phone

# ============== AUTH ENDPOINTS ==============

@router.post("/send-otp")
async def send_otp(request: SendOTPRequest):
    """Send OTP to phone number"""
    phone = normalize_phone(request.phone)
    otp = generate_otp()
    
    # Store OTP in database
    await db.marketplace_otps.update_one(
        {"phone": phone},
        {
            "$set": {
                "otp": otp,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
                "verified": False
            }
        },
        upsert=True
    )
    
    # In production, integrate with SMS gateway (MSG91, Twilio, etc.)
    # For now, return OTP in response for testing
    # TODO: Remove OTP from response in production
    
    return {
        "success": True,
        "message": f"OTP sent to {phone}",
        "expires_in_seconds": OTP_EXPIRY_MINUTES * 60,
        # REMOVE IN PRODUCTION - only for testing
        "debug_otp": otp
    }

@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and return JWT token"""
    phone = normalize_phone(request.phone)
    
    # Find OTP record
    otp_record = await db.marketplace_otps.find_one({"phone": phone})
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="OTP not found. Please request a new OTP.")
    
    if otp_record.get("verified"):
        raise HTTPException(status_code=400, detail="OTP already used. Please request a new OTP.")
    
    if datetime.utcnow() > otp_record.get("expires_at", datetime.utcnow()):
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new OTP.")
    
    if otp_record.get("otp") != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Mark OTP as verified
    await db.marketplace_otps.update_one(
        {"phone": phone},
        {"$set": {"verified": True}}
    )
    
    # Find or create user
    user = await db.marketplace_users.find_one({"phone": phone})
    
    if not user:
        # Create new user
        user_doc = {
            "phone": phone,
            "role": "public",  # Default role, can be upgraded
            "name": None,
            "email": None,
            "business_name": None,
            "gst_number": None,
            "addresses": [],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        result = await db.marketplace_users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        role = "public"
        is_new_user = True
    else:
        user_id = str(user["_id"])
        role = user.get("role", "public")
        is_new_user = False
        # Update last login
        await db.marketplace_users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    
    # Generate token
    token = create_token(user_id, phone, role)
    
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_id,
            "phone": phone,
            "role": role,
            "name": user.get("name") if user else None,
            "is_new_user": is_new_user
        }
    }

@router.get("/me")
async def get_current_user(token: str):
    """Get current user profile"""
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    from bson import ObjectId
    user = await db.marketplace_users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "phone": user.get("phone"),
        "role": user.get("role", "public"),
        "name": user.get("name"),
        "email": user.get("email"),
        "business_name": user.get("business_name"),
        "gst_number": user.get("gst_number"),
        "addresses": user.get("addresses", []),
        "created_at": user.get("created_at")
    }

@router.put("/profile")
async def update_profile(token: str, profile: UserProfile):
    """Update user profile"""
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    from bson import ObjectId
    update_data = {k: v for k, v in profile.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.marketplace_users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True, "message": "Profile updated"}

@router.post("/addresses")
async def add_address(token: str, address: AddressCreate):
    """Add shipping address"""
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    from bson import ObjectId
    import uuid
    
    address_doc = {
        "id": str(uuid.uuid4()),
        **address.dict(),
        "created_at": datetime.utcnow()
    }
    
    # If this is default address, unset other defaults
    if address.is_default:
        await db.marketplace_users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"addresses.$[].is_default": False}}
        )
    
    result = await db.marketplace_users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"addresses": address_doc}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True, "address": address_doc}

@router.delete("/addresses/{address_id}")
async def delete_address(token: str, address_id: str):
    """Delete shipping address"""
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    from bson import ObjectId
    
    result = await db.marketplace_users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"addresses": {"id": address_id}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    
    return {"success": True, "message": "Address deleted"}

# ============== ROLE MANAGEMENT (Admin) ==============

@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, admin_token: str):
    """Update user role - Admin only"""
    # Verify admin token (use existing admin auth)
    from routes.admin_auth import verify_admin_token
    verify_admin_token(admin_token)
    
    valid_roles = ["public", "fleet", "technician"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    from bson import ObjectId
    result = await db.marketplace_users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True, "message": f"User role updated to {role}"}
