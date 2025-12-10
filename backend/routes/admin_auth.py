from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import AdminUser, AdminUserCreate, AdminLogin
from auth import get_password_hash, verify_password, create_access_token
from middleware import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])
security = HTTPBearer()

from server import db


@router.post("/login")
async def admin_login(credentials: AdminLogin):
    """
    Admin login endpoint
    """
    try:
        # Find admin user by email
        admin = await db.admin_users.find_one({"email": credentials.email}, {"_id": 0})
        
        if not admin or not verify_password(credentials.password, admin['hashed_password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not admin.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Update last login
        await db.admin_users.update_one(
            {"email": credentials.email},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": admin['email'], "role": admin.get('role', 'admin')}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": admin['email'],
                "name": admin['name'],
                "role": admin.get('role', 'admin')
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@router.post("/register")
async def register_admin(admin_data: AdminUserCreate):
    """
    Register a new admin user (for initial setup)
    """
    try:
        # Check if admin already exists
        existing = await db.admin_users.find_one({"email": admin_data.email}, {"_id": 0})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user already exists"
            )
        
        # Create new admin user
        admin_user = AdminUser(
            email=admin_data.email,
            hashed_password=get_password_hash(admin_data.password),
            name=admin_data.name,
            role=admin_data.role
        )
        
        await db.admin_users.insert_one(admin_user.dict())
        
        return {
            "message": "Admin user created successfully",
            "email": admin_user.email
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


@router.get("/me")
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current authenticated admin user
    """
    try:
        user = await get_current_user(credentials)
        
        admin = await db.admin_users.find_one(
            {"email": user['email']},
            {"_id": 0, "hashed_password": 0}
        )
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )
        
        return admin
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.post("/logout")
async def admin_logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Admin logout (client should delete token)
    """
    return {"message": "Logged out successfully"}
