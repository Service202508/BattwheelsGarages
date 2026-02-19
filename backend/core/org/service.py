"""
Organization Service
Core business logic for multi-tenant organization management
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import re

from .models import (
    Organization, OrganizationCreate, OrganizationUpdate,
    OrganizationSettings, OrganizationSettingsUpdate,
    OrganizationUser, OrganizationUserCreate, OrganizationUserUpdate,
    OrganizationContext, OrgUserRole, OrgUserStatus, PlanType,
    get_role_permissions, ROLE_PERMISSIONS
)

logger = logging.getLogger(__name__)


class OrganizationService:
    """Service for organization management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.orgs = db.organizations
        self.settings = db.organization_settings
        self.org_users = db.organization_users
    
    # ==================== ORGANIZATION CRUD ====================
    
    async def create_organization(
        self,
        data: OrganizationCreate,
        owner_user_id: str
    ) -> Organization:
        """Create a new organization with default settings"""
        
        # Generate slug if not provided
        slug = data.slug or self._generate_slug(data.name)
        
        # Check slug uniqueness
        existing = await self.orgs.find_one({"slug": slug})
        if existing:
            slug = f"{slug}-{datetime.now().strftime('%H%M%S')}"
        
        # Create organization
        org = Organization(
            name=data.name,
            slug=slug,
            industry_type=data.industry_type,
            plan_type=data.plan_type,
            email=data.email,
            phone=data.phone,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            pincode=data.pincode,
            gstin=data.gstin,
            created_by=owner_user_id
        )
        
        # Insert organization
        org_dict = org.model_dump()
        await self.orgs.insert_one(org_dict)
        
        # Create default settings
        settings = OrganizationSettings(organization_id=org.organization_id)
        await self.settings.insert_one(settings.model_dump())
        
        # Add owner as first user
        owner_membership = OrganizationUser(
            organization_id=org.organization_id,
            user_id=owner_user_id,
            role=OrgUserRole.OWNER,
            status=OrgUserStatus.ACTIVE,
            joined_at=datetime.now(timezone.utc)
        )
        await self.org_users.insert_one(owner_membership.model_dump())
        
        logger.info(f"Created organization: {org.organization_id} ({org.name})")
        
        return org
    
    async def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        doc = await self.orgs.find_one(
            {"organization_id": org_id},
            {"_id": 0}
        )
        return Organization(**doc) if doc else None
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        doc = await self.orgs.find_one(
            {"slug": slug},
            {"_id": 0}
        )
        return Organization(**doc) if doc else None
    
    async def update_organization(
        self,
        org_id: str,
        data: OrganizationUpdate
    ) -> Optional[Organization]:
        """Update organization"""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.orgs.find_one_and_update(
            {"organization_id": org_id},
            {"$set": update_data},
            return_document=True,
            projection={"_id": 0}
        )
        
        return Organization(**result) if result else None
    
    async def list_organizations(
        self,
        page: int = 1,
        per_page: int = 25,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List all organizations (admin only)"""
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        
        total = await self.orgs.count_documents(query)
        skip = (page - 1) * per_page
        
        cursor = self.orgs.find(query, {"_id": 0}).skip(skip).limit(per_page)
        orgs = [Organization(**doc) async for doc in cursor]
        
        return {
            "organizations": orgs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    # ==================== ORGANIZATION SETTINGS ====================
    
    async def get_settings(self, org_id: str) -> Optional[OrganizationSettings]:
        """Get organization settings"""
        doc = await self.settings.find_one(
            {"organization_id": org_id},
            {"_id": 0}
        )
        if doc:
            return OrganizationSettings(**doc)
        
        # Create default settings if missing
        settings = OrganizationSettings(organization_id=org_id)
        await self.settings.insert_one(settings.model_dump())
        return settings
    
    async def update_settings(
        self,
        org_id: str,
        data: OrganizationSettingsUpdate
    ) -> Optional[OrganizationSettings]:
        """Update organization settings"""
        update_data = {}
        
        for key, value in data.model_dump().items():
            if value is not None:
                if isinstance(value, dict):
                    # Nested settings update (e.g., tickets.auto_assign_enabled)
                    for nested_key, nested_value in value.items():
                        update_data[f"{key}.{nested_key}"] = nested_value
                else:
                    update_data[key] = value
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.settings.find_one_and_update(
            {"organization_id": org_id},
            {"$set": update_data},
            return_document=True,
            projection={"_id": 0}
        )
        
        return OrganizationSettings(**result) if result else None
    
    # ==================== ORGANIZATION USERS ====================
    
    async def add_user_to_org(
        self,
        org_id: str,
        data: OrganizationUserCreate,
        invited_by: str
    ) -> OrganizationUser:
        """Add user to organization"""
        
        # Check if already member
        if data.user_id:
            existing = await self.org_users.find_one({
                "organization_id": org_id,
                "user_id": data.user_id
            })
            if existing:
                raise ValueError("User already a member of this organization")
        
        membership = OrganizationUser(
            organization_id=org_id,
            user_id=data.user_id or "",
            role=data.role,
            status=OrgUserStatus.INVITED if data.send_invite else OrgUserStatus.ACTIVE,
            invited_by=invited_by,
            invited_at=datetime.now(timezone.utc)
        )
        
        await self.org_users.insert_one(membership.model_dump())
        
        # Update org user count
        await self._update_org_stats(org_id)
        
        logger.info(f"Added user {data.user_id or data.email} to org {org_id}")
        
        return membership
    
    async def update_user_membership(
        self,
        org_id: str,
        user_id: str,
        data: OrganizationUserUpdate
    ) -> Optional[OrganizationUser]:
        """Update user membership in organization"""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.org_users.find_one_and_update(
            {"organization_id": org_id, "user_id": user_id},
            {"$set": update_data},
            return_document=True,
            projection={"_id": 0}
        )
        
        return OrganizationUser(**result) if result else None
    
    async def remove_user_from_org(self, org_id: str, user_id: str) -> bool:
        """Remove user from organization"""
        # Prevent removing last owner
        membership = await self.org_users.find_one({
            "organization_id": org_id,
            "user_id": user_id
        })
        
        if membership and membership.get("role") == OrgUserRole.OWNER:
            owner_count = await self.org_users.count_documents({
                "organization_id": org_id,
                "role": OrgUserRole.OWNER,
                "status": OrgUserStatus.ACTIVE
            })
            if owner_count <= 1:
                raise ValueError("Cannot remove the last owner")
        
        result = await self.org_users.delete_one({
            "organization_id": org_id,
            "user_id": user_id
        })
        
        if result.deleted_count > 0:
            await self._update_org_stats(org_id)
            return True
        return False
    
    async def get_user_membership(
        self,
        org_id: str,
        user_id: str
    ) -> Optional[OrganizationUser]:
        """Get user's membership in organization"""
        doc = await self.org_users.find_one(
            {"organization_id": org_id, "user_id": user_id},
            {"_id": 0}
        )
        return OrganizationUser(**doc) if doc else None
    
    async def list_org_users(
        self,
        org_id: str,
        status: Optional[OrgUserStatus] = None
    ) -> List[OrganizationUser]:
        """List all users in organization"""
        query = {"organization_id": org_id}
        if status:
            query["status"] = status
        
        cursor = self.org_users.find(query, {"_id": 0})
        return [OrganizationUser(**doc) async for doc in cursor]
    
    async def get_user_organizations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all organizations a user belongs to"""
        cursor = self.org_users.find(
            {"user_id": user_id, "status": OrgUserStatus.ACTIVE},
            {"_id": 0}
        )
        
        memberships = [OrganizationUser(**doc) async for doc in cursor]
        
        result = []
        for membership in memberships:
            org = await self.get_organization(membership.organization_id)
            if org:
                result.append({
                    "organization": org,
                    "membership": membership
                })
        
        return result
    
    # ==================== CONTEXT RESOLUTION ====================
    
    async def get_organization_context(
        self,
        org_id: str,
        user_id: str
    ) -> Optional[OrganizationContext]:
        """Get full organization context for request"""
        
        # Get organization
        org = await self.get_organization(org_id)
        if not org:
            return None
        
        # Get settings
        settings = await self.get_settings(org_id)
        
        # Get user membership
        membership = await self.get_user_membership(org_id, user_id)
        if not membership or membership.status != OrgUserStatus.ACTIVE:
            return None
        
        # Get permissions
        permissions = get_role_permissions(membership.role)
        if membership.custom_permissions:
            permissions = list(set(permissions + membership.custom_permissions))
        
        return OrganizationContext(
            organization_id=org_id,
            organization=org,
            settings=settings,
            user_id=user_id,
            user_role=membership.role,
            user_permissions=permissions
        )
    
    # ==================== HELPERS ====================
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug from name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug[:50]
    
    async def _update_org_stats(self, org_id: str):
        """Update organization statistics"""
        user_count = await self.org_users.count_documents({
            "organization_id": org_id,
            "status": OrgUserStatus.ACTIVE
        })
        
        await self.orgs.update_one(
            {"organization_id": org_id},
            {"$set": {"total_users": user_count, "updated_at": datetime.now(timezone.utc)}}
        )
    
    # ==================== BOOTSTRAP ====================
    
    async def bootstrap_default_organization(
        self,
        owner_user_id: str,
        owner_email: str
    ) -> Organization:
        """Create default organization for first user signup"""
        
        # Check if user already has an org
        existing = await self.org_users.find_one({"user_id": owner_user_id})
        if existing:
            org = await self.get_organization(existing["organization_id"])
            return org
        
        # Create default org
        org_name = owner_email.split("@")[0].replace(".", " ").title() + " Garage"
        
        data = OrganizationCreate(
            name=org_name,
            industry_type="ev_garage",
            plan_type=PlanType.STARTER,
            email=owner_email
        )
        
        return await self.create_organization(data, owner_user_id)


# Singleton instance
_organization_service: Optional[OrganizationService] = None


def init_organization_service(db: AsyncIOMotorDatabase) -> OrganizationService:
    """Initialize organization service"""
    global _organization_service
    _organization_service = OrganizationService(db)
    return _organization_service


def get_organization_service() -> OrganizationService:
    """Get organization service instance"""
    if _organization_service is None:
        raise RuntimeError("Organization service not initialized")
    return _organization_service
