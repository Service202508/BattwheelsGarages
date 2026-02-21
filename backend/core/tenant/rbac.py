"""
Tenant-Scoped RBAC Service (Phase C)
====================================

Role-Based Access Control scoped to organizations.
Each organization can have its own custom roles and permissions.

Architecture:
- System roles (admin, manager, technician, customer) are cloned per-org
- Organizations can create custom roles
- Permissions are stored per-organization
- Role membership is via organization_users junction table
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# ==================== DEFAULT PERMISSION TEMPLATES ====================

DEFAULT_MODULES = [
    {"module_id": "dashboard", "name": "Dashboard", "category": "core"},
    {"module_id": "tickets", "name": "Service Tickets", "category": "operations"},
    {"module_id": "estimates", "name": "Estimates", "category": "operations"},
    {"module_id": "invoices", "name": "Invoices", "category": "sales"},
    {"module_id": "customers", "name": "Customers", "category": "contacts"},
    {"module_id": "inventory", "name": "Inventory", "category": "inventory"},
    {"module_id": "items", "name": "Items/Products", "category": "inventory"},
    {"module_id": "sales_orders", "name": "Sales Orders", "category": "sales"},
    {"module_id": "purchase_orders", "name": "Purchase Orders", "category": "purchases"},
    {"module_id": "suppliers", "name": "Suppliers/Vendors", "category": "purchases"},
    {"module_id": "bills", "name": "Bills", "category": "purchases"},
    {"module_id": "expenses", "name": "Expenses", "category": "finance"},
    {"module_id": "payments", "name": "Payments", "category": "finance"},
    {"module_id": "banking", "name": "Banking", "category": "finance"},
    {"module_id": "reports", "name": "Reports", "category": "reports"},
    {"module_id": "attendance", "name": "Attendance", "category": "hr"},
    {"module_id": "leave", "name": "Leave Management", "category": "hr"},
    {"module_id": "payroll", "name": "Payroll", "category": "hr"},
    {"module_id": "employees", "name": "Employees", "category": "hr"},
    {"module_id": "ai_assistant", "name": "AI Assistant", "category": "intelligence"},
    {"module_id": "failure_intelligence", "name": "Failure Intelligence", "category": "intelligence"},
    {"module_id": "amc", "name": "AMC Management", "category": "operations"},
    {"module_id": "vehicles", "name": "Vehicles", "category": "operations"},
    {"module_id": "users", "name": "User Management", "category": "admin"},
    {"module_id": "settings", "name": "Settings", "category": "admin"},
    {"module_id": "organization", "name": "Organization Settings", "category": "admin"},
]

# System role templates - cloned to each organization
SYSTEM_ROLE_TEMPLATES = {
    "admin": {
        "name": "Administrator",
        "description": "Full access to all modules and features",
        "is_system": True,
        "permissions": {mod["module_id"]: {"view": True, "create": True, "edit": True, "delete": True} for mod in DEFAULT_MODULES}
    },
    "manager": {
        "name": "Manager",
        "description": "Access to operations, sales, and reports",
        "is_system": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "tickets": {"view": True, "create": True, "edit": True, "delete": False},
            "estimates": {"view": True, "create": True, "edit": True, "delete": False},
            "invoices": {"view": True, "create": True, "edit": True, "delete": False},
            "customers": {"view": True, "create": True, "edit": True, "delete": False},
            "inventory": {"view": True, "create": True, "edit": True, "delete": False},
            "items": {"view": True, "create": True, "edit": True, "delete": False},
            "sales_orders": {"view": True, "create": True, "edit": True, "delete": False},
            "purchase_orders": {"view": True, "create": True, "edit": True, "delete": False},
            "suppliers": {"view": True, "create": True, "edit": True, "delete": False},
            "bills": {"view": True, "create": True, "edit": True, "delete": False},
            "expenses": {"view": True, "create": True, "edit": True, "delete": False},
            "payments": {"view": True, "create": True, "edit": False, "delete": False},
            "banking": {"view": True, "create": False, "edit": False, "delete": False},
            "reports": {"view": True, "create": False, "edit": False, "delete": False},
            "attendance": {"view": True, "create": True, "edit": True, "delete": False},
            "leave": {"view": True, "create": True, "edit": True, "delete": False},
            "payroll": {"view": True, "create": False, "edit": False, "delete": False},
            "employees": {"view": True, "create": True, "edit": True, "delete": False},
            "ai_assistant": {"view": True, "create": True, "edit": False, "delete": False},
            "failure_intelligence": {"view": True, "create": True, "edit": True, "delete": False},
            "amc": {"view": True, "create": True, "edit": True, "delete": False},
            "vehicles": {"view": True, "create": True, "edit": True, "delete": False},
            "users": {"view": False, "create": False, "edit": False, "delete": False},
            "settings": {"view": False, "create": False, "edit": False, "delete": False},
            "organization": {"view": True, "create": False, "edit": False, "delete": False},
        }
    },
    "technician": {
        "name": "Technician",
        "description": "Access to assigned tickets and AI assistant",
        "is_system": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "tickets": {"view": True, "create": True, "edit": True, "delete": False},
            "estimates": {"view": True, "create": True, "edit": True, "delete": False},
            "invoices": {"view": True, "create": False, "edit": False, "delete": False},
            "customers": {"view": True, "create": False, "edit": False, "delete": False},
            "inventory": {"view": True, "create": False, "edit": False, "delete": False},
            "items": {"view": True, "create": False, "edit": False, "delete": False},
            "ai_assistant": {"view": True, "create": True, "edit": False, "delete": False},
            "failure_intelligence": {"view": True, "create": True, "edit": False, "delete": False},
            "vehicles": {"view": True, "create": False, "edit": False, "delete": False},
            "attendance": {"view": True, "create": True, "edit": False, "delete": False},
            "leave": {"view": True, "create": True, "edit": False, "delete": False},
        }
    },
    "customer": {
        "name": "Customer",
        "description": "View own tickets and invoices",
        "is_system": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "tickets": {"view": True, "create": True, "edit": False, "delete": False},
            "estimates": {"view": True, "create": False, "edit": False, "delete": False},
            "invoices": {"view": True, "create": False, "edit": False, "delete": False},
            "vehicles": {"view": True, "create": True, "edit": True, "delete": False},
        }
    }
}


@dataclass
class TenantRole:
    """Role definition scoped to an organization"""
    role_id: str
    organization_id: str
    role_code: str  # e.g., "admin", "manager", "custom_auditor"
    name: str
    description: str
    is_system: bool  # True for cloned system roles
    permissions: Dict[str, Dict[str, bool]]  # module_id -> {view, create, edit, delete}
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "organization_id": self.organization_id,
            "role_code": self.role_code,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "permissions": self.permissions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by
        }
    
    def has_permission(self, module_id: str, action: str) -> bool:
        """Check if role has permission for action on module"""
        module_perms = self.permissions.get(module_id, {})
        return module_perms.get(action, False)
    
    def get_allowed_modules(self) -> List[str]:
        """Get list of modules this role can view"""
        return [mod_id for mod_id, perms in self.permissions.items() if perms.get("view", False)]


class TenantRBACService:
    """
    Organization-scoped Role-Based Access Control Service
    
    Each organization has its own set of roles:
    - System roles are cloned from templates when org is created
    - Custom roles can be created per-organization
    - Permissions are evaluated per-organization
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.tenant_roles
        self._cache: Dict[str, Dict[str, TenantRole]] = {}  # org_id -> {role_code -> TenantRole}
    
    async def initialize_org_roles(self, organization_id: str, created_by: Optional[str] = None) -> List[TenantRole]:
        """
        Initialize default system roles for a new organization.
        Called when an organization is created.
        """
        import uuid
        
        roles = []
        now = datetime.now(timezone.utc).isoformat()
        
        for role_code, template in SYSTEM_ROLE_TEMPLATES.items():
            role = TenantRole(
                role_id=f"role_{uuid.uuid4().hex[:12]}",
                organization_id=organization_id,
                role_code=role_code,
                name=template["name"],
                description=template["description"],
                is_system=True,
                permissions=template["permissions"].copy(),
                created_at=now,
                updated_at=now,
                created_by=created_by
            )
            roles.append(role)
            
            # Store in database
            await self.collection.update_one(
                {"organization_id": organization_id, "role_code": role_code},
                {"$set": role.to_dict()},
                upsert=True
            )
        
        # Clear cache for this org
        self._cache.pop(organization_id, None)
        
        logger.info(f"Initialized {len(roles)} system roles for organization {organization_id}")
        return roles
    
    async def get_role(self, organization_id: str, role_code: str) -> Optional[TenantRole]:
        """Get a specific role for an organization"""
        # Check cache first
        if organization_id in self._cache and role_code in self._cache[organization_id]:
            return self._cache[organization_id][role_code]
        
        # Query database
        doc = await self.collection.find_one(
            {"organization_id": organization_id, "role_code": role_code},
            {"_id": 0}
        )
        
        if doc:
            role = TenantRole(**doc)
            # Cache it
            if organization_id not in self._cache:
                self._cache[organization_id] = {}
            self._cache[organization_id][role_code] = role
            return role
        
        # If not found and it's a system role, initialize it
        if role_code in SYSTEM_ROLE_TEMPLATES:
            roles = await self.initialize_org_roles(organization_id)
            for r in roles:
                if r.role_code == role_code:
                    return r
        
        return None
    
    async def list_roles(self, organization_id: str) -> List[TenantRole]:
        """List all roles for an organization"""
        # Ensure system roles exist
        system_role = await self.get_role(organization_id, "admin")
        if not system_role:
            await self.initialize_org_roles(organization_id)
        
        docs = await self.collection.find(
            {"organization_id": organization_id},
            {"_id": 0}
        ).to_list(100)
        
        return [TenantRole(**doc) for doc in docs]
    
    async def create_custom_role(
        self,
        organization_id: str,
        role_code: str,
        name: str,
        description: str,
        permissions: Dict[str, Dict[str, bool]],
        created_by: Optional[str] = None
    ) -> TenantRole:
        """Create a custom role for an organization"""
        import uuid
        
        # Check if role_code already exists
        existing = await self.get_role(organization_id, role_code)
        if existing:
            raise ValueError(f"Role '{role_code}' already exists in this organization")
        
        now = datetime.now(timezone.utc).isoformat()
        
        role = TenantRole(
            role_id=f"role_{uuid.uuid4().hex[:12]}",
            organization_id=organization_id,
            role_code=role_code,
            name=name,
            description=description,
            is_system=False,
            permissions=permissions,
            created_at=now,
            updated_at=now,
            created_by=created_by
        )
        
        await self.collection.insert_one(role.to_dict())
        
        # Clear cache
        self._cache.pop(organization_id, None)
        
        logger.info(f"Created custom role '{role_code}' for organization {organization_id}")
        return role
    
    async def update_role_permissions(
        self,
        organization_id: str,
        role_code: str,
        permissions: Dict[str, Dict[str, bool]],
        updated_by: Optional[str] = None
    ) -> Optional[TenantRole]:
        """Update permissions for a role"""
        role = await self.get_role(organization_id, role_code)
        if not role:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Merge permissions
        updated_permissions = {**role.permissions, **permissions}
        
        await self.collection.update_one(
            {"organization_id": organization_id, "role_code": role_code},
            {"$set": {
                "permissions": updated_permissions,
                "updated_at": now,
                "updated_by": updated_by
            }}
        )
        
        # Clear cache
        self._cache.pop(organization_id, None)
        
        return await self.get_role(organization_id, role_code)
    
    async def delete_custom_role(self, organization_id: str, role_code: str) -> bool:
        """Delete a custom role (system roles cannot be deleted)"""
        role = await self.get_role(organization_id, role_code)
        if not role:
            return False
        
        if role.is_system:
            raise ValueError("Cannot delete system roles")
        
        result = await self.collection.delete_one(
            {"organization_id": organization_id, "role_code": role_code}
        )
        
        # Clear cache
        self._cache.pop(organization_id, None)
        
        return result.deleted_count > 0
    
    async def check_permission(
        self,
        organization_id: str,
        role_code: str,
        module_id: str,
        action: str
    ) -> bool:
        """Check if a role has permission for an action on a module"""
        role = await self.get_role(organization_id, role_code)
        if not role:
            return False
        
        return role.has_permission(module_id, action)
    
    async def get_user_permissions(
        self,
        organization_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get all permissions for a user in an organization"""
        # Get user's role in this organization
        membership = await self.db.organization_users.find_one(
            {"organization_id": organization_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not membership:
            return {"error": "User not a member of this organization"}
        
        role_code = membership.get("role", "customer")
        role = await self.get_role(organization_id, role_code)
        
        if not role:
            return {"error": f"Role '{role_code}' not found"}
        
        return {
            "user_id": user_id,
            "organization_id": organization_id,
            "role_code": role_code,
            "role_name": role.name,
            "permissions": role.permissions,
            "allowed_modules": role.get_allowed_modules()
        }


# ==================== SERVICE SINGLETON ====================

_rbac_service: Optional[TenantRBACService] = None


def init_tenant_rbac_service(db) -> TenantRBACService:
    """Initialize the tenant RBAC service singleton"""
    global _rbac_service
    _rbac_service = TenantRBACService(db)
    logger.info("TenantRBACService initialized")
    return _rbac_service


def get_tenant_rbac_service() -> TenantRBACService:
    """Get the tenant RBAC service singleton"""
    if _rbac_service is None:
        raise RuntimeError("TenantRBACService not initialized")
    return _rbac_service
