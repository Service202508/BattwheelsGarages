"""
Battwheels OS - Role Permissions Management
Comprehensive RBAC (Role-Based Access Control) System
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
from utils.database import extract_org_id, org_query


def get_db():
    from server import db
    return db

router = APIRouter(prefix="/permissions", tags=["Permissions"])


# ==================== MODELS ====================

class ModulePermission(BaseModel):
    module_id: str
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    custom_permissions: Dict[str, bool] = {}

class RolePermissions(BaseModel):
    role: str
    modules: List[ModulePermission]
    description: Optional[str] = None

class PermissionUpdate(BaseModel):
    role: str
    module_id: str
    permission_key: str
    value: bool


# ==================== DEFAULT PERMISSIONS ====================

DEFAULT_MODULES = [
    {"module_id": "dashboard", "name": "Dashboard", "category": "core", "icon": "LayoutDashboard"},
    {"module_id": "tickets", "name": "Service Tickets", "category": "operations", "icon": "Ticket"},
    {"module_id": "estimates", "name": "Estimates", "category": "operations", "icon": "FileText"},
    {"module_id": "invoices", "name": "Invoices", "category": "sales", "icon": "Receipt"},
    {"module_id": "customers", "name": "Customers", "category": "contacts", "icon": "Users"},
    {"module_id": "inventory", "name": "Inventory", "category": "inventory", "icon": "Package"},
    {"module_id": "items", "name": "Items/Products", "category": "inventory", "icon": "Box"},
    {"module_id": "quotes", "name": "Quotes", "category": "sales", "icon": "FileText"},
    {"module_id": "sales_orders", "name": "Sales Orders", "category": "sales", "icon": "ShoppingCart"},
    {"module_id": "purchase_orders", "name": "Purchase Orders", "category": "purchases", "icon": "ShoppingBag"},
    {"module_id": "suppliers", "name": "Suppliers/Vendors", "category": "purchases", "icon": "Truck"},
    {"module_id": "bills", "name": "Bills", "category": "purchases", "icon": "CreditCard"},
    {"module_id": "expenses", "name": "Expenses", "category": "finance", "icon": "Wallet"},
    {"module_id": "payments", "name": "Payments", "category": "finance", "icon": "Banknote"},
    {"module_id": "banking", "name": "Banking", "category": "finance", "icon": "Building2"},
    {"module_id": "reports", "name": "Reports", "category": "reports", "icon": "BarChart3"},
    {"module_id": "gst_reports", "name": "GST Reports", "category": "reports", "icon": "FileSpreadsheet"},
    {"module_id": "attendance", "name": "Attendance", "category": "hr", "icon": "Clock"},
    {"module_id": "leave", "name": "Leave Management", "category": "hr", "icon": "Calendar"},
    {"module_id": "payroll", "name": "Payroll", "category": "hr", "icon": "Wallet"},
    {"module_id": "employees", "name": "Employees", "category": "hr", "icon": "Users"},
    {"module_id": "productivity", "name": "Productivity", "category": "hr", "icon": "TrendingUp"},
    {"module_id": "ai_assistant", "name": "AI Assistant", "category": "intelligence", "icon": "Bot"},
    {"module_id": "failure_intelligence", "name": "Failure Intelligence", "category": "intelligence", "icon": "AlertTriangle"},
    {"module_id": "amc", "name": "AMC Management", "category": "operations", "icon": "Shield"},
    {"module_id": "vehicles", "name": "Vehicles", "category": "operations", "icon": "Car"},
    {"module_id": "users", "name": "User Management", "category": "admin", "icon": "UserCog"},
    {"module_id": "settings", "name": "Settings", "category": "admin", "icon": "Settings"},
    {"module_id": "organization", "name": "Organization Settings", "category": "admin", "icon": "Building"},
    {"module_id": "data_management", "name": "Data Management", "category": "admin", "icon": "Database"},
    {"module_id": "zoho_sync", "name": "Zoho Sync", "category": "admin", "icon": "RefreshCw"},
]

# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    "admin": {
        "description": "Full access to all modules and features",
        "modules": {mod["module_id"]: {"can_view": True, "can_create": True, "can_edit": True, "can_delete": True} for mod in DEFAULT_MODULES}
    },
    "manager": {
        "description": "Access to operations, sales, purchases, and reports",
        "modules": {
            "dashboard": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "tickets": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "estimates": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "invoices": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "customers": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "inventory": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "items": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "quotes": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "sales_orders": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "purchase_orders": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "suppliers": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "bills": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "expenses": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "payments": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False},
            "banking": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "reports": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "gst_reports": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "attendance": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "leave": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "payroll": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "employees": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "productivity": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "ai_assistant": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False},
            "failure_intelligence": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "amc": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "vehicles": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False},
            "users": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "settings": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "organization": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "data_management": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "zoho_sync": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
        }
    },
    "technician": {
        "description": "Access to assigned tickets, personal HR data, and AI assistant",
        "modules": {
            "dashboard": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "tickets": {"can_view": True, "can_create": False, "can_edit": True, "can_delete": False, "custom": {"assigned_only": True}},
            "estimates": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False, "custom": {"assigned_tickets_only": True}},
            "invoices": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"assigned_tickets_only": True}},
            "customers": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "inventory": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "items": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "quotes": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "sales_orders": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "purchase_orders": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "suppliers": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "bills": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "expenses": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "payments": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "banking": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "reports": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "gst_reports": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "attendance": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "leave": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "payroll": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "employees": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "productivity": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "ai_assistant": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False},
            "failure_intelligence": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "amc": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "vehicles": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False},
            "users": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "settings": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "organization": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "data_management": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
            "zoho_sync": {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False},
        }
    },
    "customer": {
        "description": "Individual customer with access to their own data",
        "modules": {
            "dashboard": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "tickets": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "estimates": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"self_only": True, "can_approve": True}},
            "invoices": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "payments": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "amc": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"self_only": True}},
            "vehicles": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": False, "custom": {"self_only": True}},
        }
    },
    "business_customer": {
        "description": "Business/OEM/Fleet customer with access to organization data",
        "modules": {
            "dashboard": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"organization_only": True}},
            "tickets": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False, "custom": {"organization_only": True}},
            "estimates": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"organization_only": True, "can_approve": True}},
            "invoices": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"organization_only": True}},
            "payments": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False, "custom": {"organization_only": True, "bulk_payment": True}},
            "amc": {"can_view": True, "can_create": True, "can_edit": False, "can_delete": False, "custom": {"organization_only": True}},
            "vehicles": {"can_view": True, "can_create": True, "can_edit": True, "can_delete": True, "custom": {"organization_only": True, "fleet_management": True}},
            "reports": {"can_view": True, "can_create": False, "can_edit": False, "can_delete": False, "custom": {"organization_only": True}},
        }
    }
}


# ==================== ROUTES ====================

@router.get("/modules")
async def list_modules(request: Request):
    org_id = extract_org_id(request)
    """List all available modules"""
    return {"modules": DEFAULT_MODULES}

@router.get("/roles")
async def list_roles(request: Request):
    org_id = extract_org_id(request)
    """List all available roles with their descriptions"""
    db = get_db()
    
    # Get custom roles from DB
    custom_roles = await db.role_permissions.find({}, {"_id": 0}).to_list(100)
    
    roles = []
    for role, config in DEFAULT_ROLE_PERMISSIONS.items():
        roles.append({
            "role": role,
            "description": config["description"],
            "is_system": True
        })
    
    # Add any custom roles
    for cr in custom_roles:
        if cr["role"] not in [r["role"] for r in roles]:
            roles.append({
                "role": cr["role"],
                "description": cr.get("description", ""),
                "is_system": False
            })
    
    return {"roles": roles}

@router.get("/roles/{role}")
async def get_role_permissions(role: str, request: Request):
    org_id = extract_org_id(request)
    """Get permissions for a specific role"""
    db = get_db()
    
    # Check for custom permissions in DB first
    custom = await db.role_permissions.find_one({"role": role}, {"_id": 0})
    if custom:
        return custom
    
    # Fall back to defaults
    if role in DEFAULT_ROLE_PERMISSIONS:
        return {
            "role": role,
            "description": DEFAULT_ROLE_PERMISSIONS[role]["description"],
            "modules": DEFAULT_ROLE_PERMISSIONS[role]["modules"],
            "is_system": True
        }
    
    raise HTTPException(status_code=404, detail=f"Role '{role}' not found")

@router.put("/roles/{role}")
async def update_role_permissions(role: str, data: RolePermissions, request: Request):
    org_id = extract_org_id(request)
    """Update permissions for a role (admin only)"""
    db = get_db()
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Convert modules list to dict
    modules_dict = {}
    for mod in data.modules:
        modules_dict[mod.module_id] = {
            "can_view": mod.can_view,
            "can_create": mod.can_create,
            "can_edit": mod.can_edit,
            "can_delete": mod.can_delete,
            "custom": mod.custom_permissions
        }
    
    permission_doc = {
        "role": role,
        "description": data.description or DEFAULT_ROLE_PERMISSIONS.get(role, {}).get("description", ""),
        "modules": modules_dict,
        "is_system": role in DEFAULT_ROLE_PERMISSIONS,
        "updated_at": now
    }
    
    await db.role_permissions.update_one(
        {"role": role},
        {"$set": permission_doc},
        upsert=True
    )
    
    return permission_doc

@router.patch("/roles/{role}/module/{module_id}")
async def update_module_permission(role: str, module_id: str, data: PermissionUpdate, request: Request):
    org_id = extract_org_id(request)
    """Update a single permission for a module"""
    db = get_db()
    
    # Get current permissions
    existing = await db.role_permissions.find_one({"role": role})
    
    if not existing:
        # Clone from defaults
        if role in DEFAULT_ROLE_PERMISSIONS:
            existing = {
                "role": role,
                "modules": DEFAULT_ROLE_PERMISSIONS[role]["modules"].copy(),
                "description": DEFAULT_ROLE_PERMISSIONS[role]["description"]
            }
        else:
            raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
    
    # Update the specific permission
    if module_id not in existing.get("modules", {}):
        existing["modules"][module_id] = {"can_view": False, "can_create": False, "can_edit": False, "can_delete": False}
    
    if data.permission_key.startswith("custom."):
        custom_key = data.permission_key.replace("custom.", "")
        if "custom" not in existing["modules"][module_id]:
            existing["modules"][module_id]["custom"] = {}
        existing["modules"][module_id]["custom"][custom_key] = data.value
    else:
        existing["modules"][module_id][data.permission_key] = data.value
    
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.role_permissions.update_one(
        {"role": role},
        {"$set": existing},
        upsert=True
    )
    
    return {"message": "Permission updated", "role": role, "module": module_id}

@router.post("/roles")
async def create_custom_role(data: RolePermissions, request: Request):
    org_id = extract_org_id(request)
    """Create a new custom role"""
    db = get_db()
    
    # Check if role already exists
    existing = await db.role_permissions.find_one({"role": data.role})
    if existing or data.role in DEFAULT_ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Role '{data.role}' already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    
    modules_dict = {}
    for mod in data.modules:
        modules_dict[mod.module_id] = {
            "can_view": mod.can_view,
            "can_create": mod.can_create,
            "can_edit": mod.can_edit,
            "can_delete": mod.can_delete,
            "custom": mod.custom_permissions
        }
    
    permission_doc = {
        "role": data.role,
        "description": data.description or "",
        "modules": modules_dict,
        "is_system": False,
        "created_at": now,
        "updated_at": now
    }
    
    await db.role_permissions.insert_one(permission_doc)
    del permission_doc["_id"]
    
    return permission_doc

@router.delete("/roles/{role}")
async def delete_custom_role(role: str, request: Request):
    org_id = extract_org_id(request)
    """Delete a custom role (system roles cannot be deleted)"""
    if role in DEFAULT_ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    
    db = get_db()
    result = await db.role_permissions.delete_one({"role": role})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
    
    return {"message": f"Role '{role}' deleted"}

@router.get("/check")
async def check_permission(
    role: str,
    module_id: str,
    action: str = "can_view", request: Request):
    org_id = extract_org_id(request)
    """Check if a role has permission for a specific action on a module"""
    db = get_db()
    
    # Check custom permissions first
    custom = await db.role_permissions.find_one({"role": role}, {"_id": 0})
    
    if custom and module_id in custom.get("modules", {}):
        module_perms = custom["modules"][module_id]
        if action.startswith("custom."):
            custom_key = action.replace("custom.", "")
            return {"allowed": module_perms.get("custom", {}).get(custom_key, False)}
        return {"allowed": module_perms.get(action, False)}
    
    # Check defaults
    if role in DEFAULT_ROLE_PERMISSIONS:
        module_perms = DEFAULT_ROLE_PERMISSIONS[role]["modules"].get(module_id, {})
        if action.startswith("custom."):
            custom_key = action.replace("custom.", "")
            return {"allowed": module_perms.get("custom", {}).get(custom_key, False)}
        return {"allowed": module_perms.get(action, False)}
    
    return {"allowed": False}

@router.post("/seed-defaults")
async def seed_default_permissions(request: Request):
    org_id = extract_org_id(request)
    """Seed default role permissions to database"""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    
    for role, config in DEFAULT_ROLE_PERMISSIONS.items():
        existing = await db.role_permissions.find_one({"role": role})
        if not existing:
            await db.role_permissions.insert_one({
                "role": role,
                "description": config["description"],
                "modules": config["modules"],
                "is_system": True,
                "created_at": now,
                "updated_at": now
            })
    
    return {"message": "Default permissions seeded", "roles": list(DEFAULT_ROLE_PERMISSIONS.keys())}
