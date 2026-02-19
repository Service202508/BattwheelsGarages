"""
Battwheels OS - Settings Routes
Comprehensive settings API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from .service import get_settings_service, SettingsService
from .models import (
    OrganizationProfile, BrandingSettings, LocationCreate,
    GSTSettings, TDSSettings, MSMESettings,
    TaxRate, TaxGroup, HSNCode,
    CustomFieldCreate, NumberingSeries, WorkflowRuleCreate,
    VehicleSettings, TicketSettings, WorkOrderSettings,
    InventorySettings, CustomerSettings, BillingSettings, EFISettings,
    NotificationTemplate, PDFTemplate, PortalSettings,
    IntegrationSettings, WebhookEndpoint
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

# Will be set during initialization
_db = None
_get_current_user = None


def init_settings_routes(db, get_current_user):
    """Initialize routes with dependencies"""
    global _db, _get_current_user
    _db = db
    _get_current_user = get_current_user
    return router


async def get_org_id(request: Request) -> str:
    """Get organization ID from request"""
    try:
        from core.org import get_org_id_from_request
        return await get_org_id_from_request(request)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Organization context required")


async def require_admin(request: Request) -> Dict:
    """Require admin role"""
    if _get_current_user is None:
        raise HTTPException(status_code=500, detail="Auth not configured")
    
    user = await _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    # User is a pydantic model, convert to dict
    user_dict = user.model_dump() if hasattr(user, 'model_dump') else dict(user)
    if user_dict.get("role") not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_dict


# ==================== ALL SETTINGS ====================

@router.get("")
async def get_all_settings(request: Request):
    """Get all settings for the organization"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_all_settings(org_id)


@router.get("/categories")
async def get_settings_categories():
    """Get available settings categories for UI navigation"""
    return {
        "categories": [
            {
                "id": "organization",
                "name": "Organization",
                "icon": "Building2",
                "color": "#10B981",
                "items": [
                    {"id": "profile", "name": "Organization Profile", "path": "/settings/organization/profile"},
                    {"id": "branding", "name": "Branding & Theme", "path": "/settings/organization/branding"},
                    {"id": "locations", "name": "Locations & Branches", "path": "/settings/organization/locations"},
                    {"id": "subscription", "name": "Subscription & Plans", "path": "/settings/organization/subscription"}
                ]
            },
            {
                "id": "users",
                "name": "Users & Roles",
                "icon": "Users",
                "color": "#3B82F6",
                "items": [
                    {"id": "users", "name": "Manage Users", "path": "/settings/users"},
                    {"id": "roles", "name": "Roles & Permissions", "path": "/settings/roles"},
                    {"id": "teams", "name": "Teams", "path": "/settings/teams"}
                ]
            },
            {
                "id": "taxes",
                "name": "Taxes & Compliance",
                "icon": "Receipt",
                "color": "#F59E0B",
                "items": [
                    {"id": "gst", "name": "GST Settings", "path": "/settings/taxes/gst"},
                    {"id": "tds", "name": "TDS/Direct Taxes", "path": "/settings/taxes/tds"},
                    {"id": "msme", "name": "MSME Compliance", "path": "/settings/taxes/msme"},
                    {"id": "tax-rates", "name": "Tax Rates", "path": "/settings/taxes/rates"},
                    {"id": "tax-groups", "name": "Tax Groups", "path": "/settings/taxes/groups"},
                    {"id": "hsn-codes", "name": "HSN/SAC Codes", "path": "/settings/taxes/hsn"},
                    {"id": "e-invoicing", "name": "E-Invoicing", "path": "/settings/taxes/e-invoicing"},
                    {"id": "eway-bill", "name": "E-Way Bill", "path": "/settings/taxes/eway-bill"}
                ]
            },
            {
                "id": "customization",
                "name": "Customization",
                "icon": "Palette",
                "color": "#8B5CF6",
                "items": [
                    {"id": "custom-fields", "name": "Custom Fields", "path": "/settings/customization/fields"},
                    {"id": "numbering", "name": "Numbering Series", "path": "/settings/customization/numbering"},
                    {"id": "pdf-templates", "name": "PDF Templates", "path": "/settings/customization/pdf"},
                    {"id": "email-templates", "name": "Email Templates", "path": "/settings/customization/email"},
                    {"id": "sms-templates", "name": "SMS Templates", "path": "/settings/customization/sms"}
                ]
            },
            {
                "id": "automation",
                "name": "Automation",
                "icon": "Zap",
                "color": "#EF4444",
                "items": [
                    {"id": "workflows", "name": "Workflow Rules", "path": "/settings/automation/workflows"},
                    {"id": "workflow-logs", "name": "Workflow Logs", "path": "/settings/automation/logs"},
                    {"id": "reminders", "name": "Reminders", "path": "/settings/automation/reminders"},
                    {"id": "notifications", "name": "Notifications", "path": "/settings/automation/notifications"}
                ]
            },
            {
                "id": "modules",
                "name": "Module Settings",
                "icon": "Settings2",
                "color": "#06B6D4",
                "items": [
                    {"id": "vehicles", "name": "Vehicles & Fleet", "path": "/settings/modules/vehicles"},
                    {"id": "tickets", "name": "Service Tickets", "path": "/settings/modules/tickets"},
                    {"id": "work-orders", "name": "Work Orders", "path": "/settings/modules/work-orders"},
                    {"id": "inventory", "name": "Parts & Inventory", "path": "/settings/modules/inventory"},
                    {"id": "customers", "name": "Customers", "path": "/settings/modules/customers"},
                    {"id": "billing", "name": "Billing & Invoices", "path": "/settings/modules/billing"},
                    {"id": "efi", "name": "Failure Intelligence", "path": "/settings/modules/efi"},
                    {"id": "portal", "name": "Customer Portal", "path": "/settings/modules/portal"}
                ]
            },
            {
                "id": "integrations",
                "name": "Integrations",
                "icon": "Plug",
                "color": "#EC4899",
                "items": [
                    {"id": "connections", "name": "Connected Apps", "path": "/settings/integrations"},
                    {"id": "payments", "name": "Payment Gateways", "path": "/settings/integrations/payments"},
                    {"id": "telematics", "name": "Telematics", "path": "/settings/integrations/telematics"},
                    {"id": "messaging", "name": "Messaging (WhatsApp/SMS)", "path": "/settings/integrations/messaging"}
                ]
            },
            {
                "id": "developer",
                "name": "Developer & API",
                "icon": "Code",
                "color": "#6366F1",
                "items": [
                    {"id": "api-keys", "name": "API Keys", "path": "/settings/developer/api-keys"},
                    {"id": "webhooks", "name": "Webhooks", "path": "/settings/developer/webhooks"},
                    {"id": "api-docs", "name": "API Documentation", "path": "/settings/developer/docs"}
                ]
            }
        ]
    }


# ==================== ORGANIZATION ====================

@router.get("/organization/profile")
async def get_organization_profile(request: Request):
    """Get organization profile"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_organization_profile(org_id)


@router.patch("/organization/profile")
async def update_organization_profile(request: Request, profile: OrganizationProfile):
    """Update organization profile"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_organization_profile(org_id, profile)


@router.get("/organization/branding")
async def get_branding(request: Request):
    """Get branding settings"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_branding(org_id)


@router.patch("/organization/branding")
async def update_branding(request: Request, branding: BrandingSettings):
    """Update branding settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_branding(org_id, branding)


# ==================== LOCATIONS ====================

@router.get("/locations")
async def get_locations(request: Request):
    """Get all locations"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_locations(org_id)


@router.post("/locations")
async def create_location(request: Request, data: LocationCreate):
    """Create a new location"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_location(org_id, data)


@router.patch("/locations/{location_id}")
async def update_location(request: Request, location_id: str, data: Dict[str, Any]):
    """Update a location"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_location(org_id, location_id, data)


@router.delete("/locations/{location_id}")
async def delete_location(request: Request, location_id: str):
    """Delete a location"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    success = await service.delete_location(org_id, location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted"}


# ==================== TAX SETTINGS ====================

@router.get("/taxes/gst")
async def get_gst_settings(request: Request):
    """Get GST settings"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_gst_settings(org_id)


@router.patch("/taxes/gst")
async def update_gst_settings(request: Request, gst: GSTSettings):
    """Update GST settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_gst_settings(org_id, gst)


@router.get("/taxes/tds")
async def get_tds_settings(request: Request):
    """Get TDS settings"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_tds_settings(org_id)


@router.patch("/taxes/tds")
async def update_tds_settings(request: Request, tds: TDSSettings):
    """Update TDS settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_tds_settings(org_id, tds)


@router.get("/taxes/msme")
async def get_msme_settings(request: Request):
    """Get MSME settings"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_msme_settings(org_id)


@router.patch("/taxes/msme")
async def update_msme_settings(request: Request, msme: MSMESettings):
    """Update MSME settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_msme_settings(org_id, msme)


# ==================== TAX RATES & GROUPS ====================

@router.get("/taxes/rates")
async def get_tax_rates(request: Request):
    """Get all tax rates"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_tax_rates(org_id)


@router.post("/taxes/rates")
async def create_tax_rate(request: Request, data: TaxRate):
    """Create a tax rate"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_tax_rate(org_id, data)


@router.get("/taxes/groups")
async def get_tax_groups(request: Request):
    """Get all tax groups"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_tax_groups(org_id)


@router.post("/taxes/groups")
async def create_tax_group(request: Request, data: TaxGroup):
    """Create a tax group"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_tax_group(org_id, data)


@router.get("/taxes/hsn")
async def get_hsn_codes(request: Request, search: Optional[str] = None):
    """Get HSN codes"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_hsn_codes(org_id, search)


@router.post("/taxes/hsn")
async def create_hsn_code(request: Request, data: HSNCode):
    """Create HSN code"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_hsn_code(org_id, data)


# ==================== CUSTOM FIELDS ====================

@router.get("/custom-fields")
async def get_custom_fields(request: Request, module: Optional[str] = None):
    """Get custom fields"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_custom_fields(org_id, module)


@router.post("/custom-fields")
async def create_custom_field(request: Request, data: CustomFieldCreate):
    """Create a custom field"""
    user = await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_custom_field(org_id, user.get("user_id"), data)


@router.patch("/custom-fields/{field_id}")
async def update_custom_field(request: Request, field_id: str, data: Dict[str, Any]):
    """Update a custom field"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_custom_field(org_id, field_id, data)


@router.delete("/custom-fields/{field_id}")
async def delete_custom_field(request: Request, field_id: str):
    """Delete a custom field"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    success = await service.delete_custom_field(org_id, field_id)
    if not success:
        raise HTTPException(status_code=404, detail="Custom field not found")
    return {"message": "Custom field deleted"}


# ==================== NUMBERING SERIES ====================

@router.get("/numbering-series")
async def get_numbering_series(request: Request, module: Optional[str] = None):
    """Get numbering series"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_numbering_series(org_id, module)


@router.post("/numbering-series")
async def create_numbering_series(request: Request, data: NumberingSeries):
    """Create a numbering series"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_numbering_series(org_id, data)


# ==================== WORKFLOW RULES ====================

@router.get("/workflows")
async def get_workflow_rules(request: Request, module: Optional[str] = None):
    """Get workflow rules"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_workflow_rules(org_id, module)


@router.post("/workflows")
async def create_workflow_rule(request: Request, data: WorkflowRuleCreate):
    """Create a workflow rule"""
    user = await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_workflow_rule(org_id, user.get("user_id"), data)


@router.patch("/workflows/{rule_id}")
async def update_workflow_rule(request: Request, rule_id: str, data: Dict[str, Any]):
    """Update a workflow rule"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_workflow_rule(org_id, rule_id, data)


@router.delete("/workflows/{rule_id}")
async def delete_workflow_rule(request: Request, rule_id: str):
    """Delete a workflow rule"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    success = await service.delete_workflow_rule(org_id, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    return {"message": "Workflow rule deleted"}


@router.get("/workflows/logs")
async def get_workflow_logs(
    request: Request,
    rule_id: Optional[str] = None,
    module: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """Get workflow execution logs"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_workflow_logs(org_id, rule_id, module, limit)


# ==================== MODULE SETTINGS ====================

@router.get("/modules/{module}")
async def get_module_settings(request: Request, module: str):
    """Get settings for a specific module"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_module_settings(org_id, module)


@router.patch("/modules/{module}")
async def update_module_settings(request: Request, module: str, data: Dict[str, Any]):
    """Update module settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, module, data)


# Specific module endpoints for typed validation

@router.patch("/modules/vehicles")
async def update_vehicle_settings(request: Request, data: VehicleSettings):
    """Update vehicle settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "vehicles", data.model_dump())


@router.patch("/modules/tickets")
async def update_ticket_settings(request: Request, data: TicketSettings):
    """Update ticket settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "tickets", data.model_dump())


@router.patch("/modules/work-orders")
async def update_work_order_settings(request: Request, data: WorkOrderSettings):
    """Update work order settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "work_orders", data.model_dump())


@router.patch("/modules/inventory")
async def update_inventory_settings(request: Request, data: InventorySettings):
    """Update inventory settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "inventory", data.model_dump())


@router.patch("/modules/customers")
async def update_customer_settings(request: Request, data: CustomerSettings):
    """Update customer settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "customers", data.model_dump())


@router.patch("/modules/billing")
async def update_billing_settings(request: Request, data: BillingSettings):
    """Update billing settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "billing", data.model_dump())


@router.patch("/modules/efi")
async def update_efi_settings(request: Request, data: EFISettings):
    """Update EFI settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "efi", data.model_dump())


@router.patch("/modules/portal")
async def update_portal_settings(request: Request, data: PortalSettings):
    """Update portal settings"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_module_settings(org_id, "portal", data.model_dump())


# ==================== TEMPLATES ====================

@router.get("/templates/notification")
async def get_notification_templates(
    request: Request,
    module: Optional[str] = None,
    channel: Optional[str] = None
):
    """Get notification templates"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_notification_templates(org_id, module, channel)


@router.post("/templates/notification")
async def create_notification_template(request: Request, data: NotificationTemplate):
    """Create notification template"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_notification_template(org_id, data)


@router.get("/templates/pdf")
async def get_pdf_templates(request: Request, module: Optional[str] = None):
    """Get PDF templates"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_pdf_templates(org_id, module)


@router.post("/templates/pdf")
async def create_pdf_template(request: Request, data: PDFTemplate):
    """Create PDF template"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_pdf_template(org_id, data)


# ==================== INTEGRATIONS ====================

@router.get("/integrations")
async def get_integrations(request: Request):
    """Get all integrations"""
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_integrations(org_id)


@router.post("/integrations")
async def create_integration(request: Request, data: IntegrationSettings):
    """Create integration"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_integration(org_id, data)


@router.patch("/integrations/{integration_id}")
async def update_integration(request: Request, integration_id: str, data: Dict[str, Any]):
    """Update integration"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_integration(org_id, integration_id, data)


# ==================== DEVELOPER ====================

@router.get("/api-keys")
async def get_api_keys(request: Request):
    """Get API keys"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_api_keys(org_id)


@router.post("/api-keys")
async def create_api_key(request: Request, name: str, permissions: List[str] = None):
    """Create API key - returns full key only once"""
    user = await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_api_key(org_id, user.get("user_id"), name, permissions)


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(request: Request, key_id: str):
    """Revoke an API key"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    success = await service.revoke_api_key(org_id, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked"}


@router.get("/webhooks")
async def get_webhooks(request: Request):
    """Get webhooks"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.get_webhooks(org_id)


@router.post("/webhooks")
async def create_webhook(request: Request, data: WebhookEndpoint):
    """Create webhook - returns secret only once"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.create_webhook(org_id, data)


@router.patch("/webhooks/{webhook_id}")
async def update_webhook(request: Request, webhook_id: str, data: Dict[str, Any]):
    """Update webhook"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    return await service.update_webhook(org_id, webhook_id, data)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(request: Request, webhook_id: str):
    """Delete webhook"""
    await require_admin(request)
    org_id = await get_org_id(request)
    service = get_settings_service()
    success = await service.delete_webhook(org_id, webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}
