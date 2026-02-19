"""
Battwheels OS - Settings Service
Business logic for all settings operations with multi-tenant support
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import (
    OrganizationProfile, BrandingSettings, Location, LocationCreate,
    SubscriptionInfo, GSTSettings, TDSSettings, MSMESettings,
    TaxRate, TaxGroup, HSNCode, CustomField, CustomFieldCreate,
    NumberingSeries, WorkflowRule, WorkflowRuleCreate, WorkflowLog,
    VehicleSettings, TicketSettings, WorkOrderSettings, InventorySettings,
    CustomerSettings, BillingSettings, EFISettings,
    NotificationTemplate, PDFTemplate, PortalSettings,
    IntegrationSettings, APIKeySettings, WebhookEndpoint,
    ModuleName, DataType, TaxType
)

logger = logging.getLogger(__name__)


def generate_id(prefix: str = "SET") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SettingsService:
    """Service for managing all organization settings"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # Collections
        self.settings = db["organization_settings"]
        self.locations = db["locations"]
        self.tax_rates = db["tax_rates"]
        self.tax_groups = db["tax_groups"]
        self.hsn_codes = db["hsn_codes"]
        self.custom_fields = db["custom_fields"]
        self.numbering_series = db["numbering_series"]
        self.workflow_rules = db["workflow_rules"]
        self.workflow_logs = db["workflow_logs"]
        self.notification_templates = db["notification_templates"]
        self.pdf_templates = db["pdf_templates"]
        self.integrations = db["integrations"]
        self.api_keys = db["api_keys"]
        self.webhooks = db["webhooks"]
    
    # ==================== ORGANIZATION PROFILE ====================
    
    async def get_organization_profile(self, org_id: str) -> Dict[str, Any]:
        """Get organization profile settings"""
        org = await self.db.organizations.find_one(
            {"organization_id": org_id},
            {"_id": 0}
        )
        return org or {}
    
    async def update_organization_profile(
        self, org_id: str, profile: OrganizationProfile
    ) -> Dict[str, Any]:
        """Update organization profile"""
        update_data = profile.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.db.organizations.update_one(
            {"organization_id": org_id},
            {"$set": update_data}
        )
        
        return await self.get_organization_profile(org_id)
    
    # ==================== BRANDING ====================
    
    async def get_branding(self, org_id: str) -> Dict[str, Any]:
        """Get branding settings"""
        settings = await self.settings.find_one(
            {"organization_id": org_id},
            {"_id": 0, "branding": 1}
        )
        return settings.get("branding", BrandingSettings().model_dump()) if settings else BrandingSettings().model_dump()
    
    async def update_branding(self, org_id: str, branding: BrandingSettings) -> Dict[str, Any]:
        """Update branding settings"""
        await self.settings.update_one(
            {"organization_id": org_id},
            {"$set": {"branding": branding.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return await self.get_branding(org_id)
    
    # ==================== LOCATIONS ====================
    
    async def get_locations(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all locations for organization"""
        locations = await self.locations.find(
            {"organization_id": org_id, "is_active": True},
            {"_id": 0}
        ).to_list(100)
        return locations
    
    async def create_location(self, org_id: str, data: LocationCreate) -> Dict[str, Any]:
        """Create a new location"""
        location_id = generate_id("LOC")
        now = datetime.now(timezone.utc).isoformat()
        
        location_doc = {
            "location_id": location_id,
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        # If this is primary, unset other primaries
        if data.is_primary:
            await self.locations.update_many(
                {"organization_id": org_id},
                {"$set": {"is_primary": False}}
            )
        
        await self.locations.insert_one(location_doc)
        return {k: v for k, v in location_doc.items() if k != "_id"}
    
    async def update_location(self, org_id: str, location_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a location"""
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.locations.update_one(
            {"organization_id": org_id, "location_id": location_id},
            {"$set": data}
        )
        
        location = await self.locations.find_one(
            {"organization_id": org_id, "location_id": location_id},
            {"_id": 0}
        )
        return location
    
    async def delete_location(self, org_id: str, location_id: str) -> bool:
        """Soft delete a location"""
        result = await self.locations.update_one(
            {"organization_id": org_id, "location_id": location_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0
    
    # ==================== TAX SETTINGS ====================
    
    async def get_gst_settings(self, org_id: str) -> Dict[str, Any]:
        """Get GST settings"""
        settings = await self.settings.find_one(
            {"organization_id": org_id},
            {"_id": 0, "gst": 1}
        )
        return settings.get("gst", GSTSettings().model_dump()) if settings else GSTSettings().model_dump()
    
    async def update_gst_settings(self, org_id: str, gst: GSTSettings) -> Dict[str, Any]:
        """Update GST settings"""
        await self.settings.update_one(
            {"organization_id": org_id},
            {"$set": {"gst": gst.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return await self.get_gst_settings(org_id)
    
    async def get_tds_settings(self, org_id: str) -> Dict[str, Any]:
        """Get TDS settings"""
        settings = await self.settings.find_one(
            {"organization_id": org_id},
            {"_id": 0, "tds": 1}
        )
        return settings.get("tds", TDSSettings().model_dump()) if settings else TDSSettings().model_dump()
    
    async def update_tds_settings(self, org_id: str, tds: TDSSettings) -> Dict[str, Any]:
        """Update TDS settings"""
        await self.settings.update_one(
            {"organization_id": org_id},
            {"$set": {"tds": tds.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return await self.get_tds_settings(org_id)
    
    async def get_msme_settings(self, org_id: str) -> Dict[str, Any]:
        """Get MSME settings"""
        settings = await self.settings.find_one(
            {"organization_id": org_id},
            {"_id": 0, "msme": 1}
        )
        return settings.get("msme", MSMESettings().model_dump()) if settings else MSMESettings().model_dump()
    
    async def update_msme_settings(self, org_id: str, msme: MSMESettings) -> Dict[str, Any]:
        """Update MSME settings"""
        await self.settings.update_one(
            {"organization_id": org_id},
            {"$set": {"msme": msme.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return await self.get_msme_settings(org_id)
    
    # ==================== TAX RATES & GROUPS ====================
    
    async def get_tax_rates(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all tax rates"""
        rates = await self.tax_rates.find(
            {"organization_id": org_id, "is_active": True},
            {"_id": 0}
        ).to_list(100)
        return rates
    
    async def create_tax_rate(self, org_id: str, data: TaxRate) -> Dict[str, Any]:
        """Create a tax rate"""
        tax_rate_id = generate_id("TAX")
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "tax_rate_id": tax_rate_id,
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        await self.tax_rates.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def get_tax_groups(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all tax groups"""
        groups = await self.tax_groups.find(
            {"organization_id": org_id, "is_active": True},
            {"_id": 0}
        ).to_list(100)
        return groups
    
    async def create_tax_group(self, org_id: str, data: TaxGroup) -> Dict[str, Any]:
        """Create a tax group"""
        tax_group_id = generate_id("TGR")
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "tax_group_id": tax_group_id,
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        await self.tax_groups.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def get_hsn_codes(self, org_id: str, search: str = None) -> List[Dict[str, Any]]:
        """Get HSN codes with optional search"""
        query = {"organization_id": org_id, "is_active": True}
        if search:
            query["$or"] = [
                {"hsn_code": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        codes = await self.hsn_codes.find(query, {"_id": 0}).to_list(500)
        return codes
    
    async def create_hsn_code(self, org_id: str, data: HSNCode) -> Dict[str, Any]:
        """Create an HSN code"""
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        await self.hsn_codes.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    # ==================== CUSTOM FIELDS ====================
    
    async def get_custom_fields(self, org_id: str, module: str = None) -> List[Dict[str, Any]]:
        """Get custom fields, optionally filtered by module"""
        query = {"organization_id": org_id}
        if module:
            query["module"] = module
        
        fields = await self.custom_fields.find(query, {"_id": 0}).sort("sort_order", 1).to_list(200)
        return fields
    
    async def create_custom_field(self, org_id: str, user_id: str, data: CustomFieldCreate) -> Dict[str, Any]:
        """Create a custom field"""
        field_id = generate_id("CF")
        now = datetime.now(timezone.utc).isoformat()
        
        # Generate field name from label if not provided
        field_name = data.field_name or data.label.lower().replace(" ", "_")
        
        doc = {
            "field_id": field_id,
            "organization_id": org_id,
            **data.model_dump(),
            "field_name": field_name,
            "created_at": now,
            "updated_at": now,
            "created_by": user_id
        }
        
        await self.custom_fields.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def update_custom_field(self, org_id: str, field_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a custom field"""
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.custom_fields.update_one(
            {"organization_id": org_id, "field_id": field_id},
            {"$set": data}
        )
        
        field = await self.custom_fields.find_one(
            {"organization_id": org_id, "field_id": field_id},
            {"_id": 0}
        )
        return field
    
    async def delete_custom_field(self, org_id: str, field_id: str) -> bool:
        """Delete a custom field"""
        result = await self.custom_fields.delete_one(
            {"organization_id": org_id, "field_id": field_id}
        )
        return result.deleted_count > 0
    
    # ==================== NUMBERING SERIES ====================
    
    async def get_numbering_series(self, org_id: str, module: str = None) -> List[Dict[str, Any]]:
        """Get numbering series"""
        query = {"organization_id": org_id}
        if module:
            query["module"] = module
        
        series = await self.numbering_series.find(query, {"_id": 0}).to_list(100)
        return series
    
    async def create_numbering_series(self, org_id: str, data: NumberingSeries) -> Dict[str, Any]:
        """Create a numbering series"""
        series_id = generate_id("SER")
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "series_id": series_id,
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        # If this is default, unset other defaults for same module
        if data.is_default:
            await self.numbering_series.update_many(
                {"organization_id": org_id, "module": data.module},
                {"$set": {"is_default": False}}
            )
        
        await self.numbering_series.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def get_next_number(self, org_id: str, module: str, series_id: str = None) -> str:
        """Get next number from series and increment"""
        query = {"organization_id": org_id, "module": module}
        if series_id:
            query["series_id"] = series_id
        else:
            query["is_default"] = True
        
        series = await self.numbering_series.find_one_and_update(
            query,
            {"$inc": {"current_number": 1}},
            return_document=True,
            projection={"_id": 0}
        )
        
        if not series:
            # Return simple fallback
            return f"{module.upper()[:3]}-{datetime.now().strftime('%Y%m%d')}-001"
        
        # Build number
        parts = []
        if series.get("prefix"):
            parts.append(series["prefix"])
        
        if series.get("includes_year"):
            year_format = series.get("year_format", "YY")
            if year_format == "YYYY":
                parts.append(datetime.now().strftime("%Y"))
            else:
                parts.append(datetime.now().strftime("%y"))
        
        if series.get("includes_month"):
            parts.append(datetime.now().strftime("%m"))
        
        # Padded number
        padding = series.get("padding_zeros", 4)
        number_str = str(series["current_number"]).zfill(padding)
        parts.append(number_str)
        
        if series.get("suffix"):
            parts.append(series["suffix"])
        
        separator = series.get("separator", "-")
        return separator.join(parts)
    
    # ==================== WORKFLOW RULES ====================
    
    async def get_workflow_rules(self, org_id: str, module: str = None) -> List[Dict[str, Any]]:
        """Get workflow rules"""
        query = {"organization_id": org_id}
        if module:
            query["module"] = module
        
        rules = await self.workflow_rules.find(query, {"_id": 0}).sort("execution_order", 1).to_list(100)
        return rules
    
    async def create_workflow_rule(self, org_id: str, user_id: str, data: WorkflowRuleCreate) -> Dict[str, Any]:
        """Create a workflow rule"""
        rule_id = generate_id("WF")
        now = datetime.now(timezone.utc).isoformat()
        
        # Generate action IDs
        actions = []
        for i, action in enumerate(data.actions):
            action_dict = action.model_dump()
            action_dict["action_id"] = generate_id("ACT")
            actions.append(action_dict)
        
        doc = {
            "rule_id": rule_id,
            "organization_id": org_id,
            **data.model_dump(exclude={"actions"}),
            "actions": actions,
            "created_at": now,
            "updated_at": now,
            "created_by": user_id,
            "trigger_count": 0
        }
        
        await self.workflow_rules.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def update_workflow_rule(self, org_id: str, rule_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a workflow rule"""
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.workflow_rules.update_one(
            {"organization_id": org_id, "rule_id": rule_id},
            {"$set": data}
        )
        
        rule = await self.workflow_rules.find_one(
            {"organization_id": org_id, "rule_id": rule_id},
            {"_id": 0}
        )
        return rule
    
    async def delete_workflow_rule(self, org_id: str, rule_id: str) -> bool:
        """Delete a workflow rule"""
        result = await self.workflow_rules.delete_one(
            {"organization_id": org_id, "rule_id": rule_id}
        )
        return result.deleted_count > 0
    
    async def log_workflow_execution(
        self, org_id: str, rule_id: str, rule_name: str,
        module: str, record_id: str, trigger_type: str,
        status: str, actions_executed: List[Dict], error: str = None,
        execution_time_ms: int = 0
    ) -> Dict[str, Any]:
        """Log workflow execution"""
        log_id = generate_id("WFL")
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "log_id": log_id,
            "organization_id": org_id,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "module": module,
            "record_id": record_id,
            "trigger_type": trigger_type,
            "executed_at": now,
            "status": status,
            "actions_executed": actions_executed,
            "error_message": error,
            "execution_time_ms": execution_time_ms
        }
        
        await self.workflow_logs.insert_one(doc)
        
        # Update rule trigger count
        await self.workflow_rules.update_one(
            {"rule_id": rule_id},
            {"$inc": {"trigger_count": 1}, "$set": {"last_triggered": now}}
        )
        
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def get_workflow_logs(
        self, org_id: str, rule_id: str = None,
        module: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get workflow execution logs"""
        query = {"organization_id": org_id}
        if rule_id:
            query["rule_id"] = rule_id
        if module:
            query["module"] = module
        
        logs = await self.workflow_logs.find(query, {"_id": 0}).sort("executed_at", -1).limit(limit).to_list(limit)
        return logs
    
    # ==================== MODULE SETTINGS ====================
    
    async def get_module_settings(self, org_id: str, module: str) -> Dict[str, Any]:
        """Get settings for a specific module"""
        settings = await self.settings.find_one(
            {"organization_id": org_id},
            {"_id": 0, module: 1}
        )
        
        # Return defaults if not set
        defaults = {
            "vehicles": VehicleSettings().model_dump(),
            "tickets": TicketSettings().model_dump(),
            "work_orders": WorkOrderSettings().model_dump(),
            "inventory": InventorySettings().model_dump(),
            "customers": CustomerSettings().model_dump(),
            "billing": BillingSettings().model_dump(),
            "efi": EFISettings().model_dump(),
            "portal": PortalSettings().model_dump()
        }
        
        if settings and module in settings:
            return settings[module]
        return defaults.get(module, {})
    
    async def update_module_settings(self, org_id: str, module: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update module settings"""
        await self.settings.update_one(
            {"organization_id": org_id},
            {"$set": {module: data, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return await self.get_module_settings(org_id, module)
    
    # ==================== NOTIFICATION TEMPLATES ====================
    
    async def get_notification_templates(self, org_id: str, module: str = None, channel: str = None) -> List[Dict[str, Any]]:
        """Get notification templates"""
        query = {"organization_id": org_id}
        if module:
            query["module"] = module
        if channel:
            query["channel"] = channel
        
        templates = await self.notification_templates.find(query, {"_id": 0}).to_list(200)
        return templates
    
    async def create_notification_template(self, org_id: str, data: NotificationTemplate) -> Dict[str, Any]:
        """Create notification template"""
        template_id = generate_id("NT")
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "template_id": template_id,
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        await self.notification_templates.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    # ==================== PDF TEMPLATES ====================
    
    async def get_pdf_templates(self, org_id: str, module: str = None) -> List[Dict[str, Any]]:
        """Get PDF templates"""
        query = {"organization_id": org_id}
        if module:
            query["module"] = module
        
        templates = await self.pdf_templates.find(query, {"_id": 0}).to_list(100)
        return templates
    
    async def create_pdf_template(self, org_id: str, data: PDFTemplate) -> Dict[str, Any]:
        """Create PDF template"""
        template_id = generate_id("PDF")
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "template_id": template_id,
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        await self.pdf_templates.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    # ==================== INTEGRATIONS ====================
    
    async def get_integrations(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all integrations"""
        integrations = await self.integrations.find(
            {"organization_id": org_id},
            {"_id": 0, "api_secret": 0}  # Exclude secrets
        ).to_list(50)
        return integrations
    
    async def create_integration(self, org_id: str, data: IntegrationSettings) -> Dict[str, Any]:
        """Create integration"""
        integration_id = generate_id("INT")
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "integration_id": integration_id,
            "organization_id": org_id,
            **data.model_dump(),
            "created_at": now,
            "updated_at": now
        }
        
        await self.integrations.insert_one(doc)
        return {k: v for k, v in doc.items() if k not in ["_id", "api_secret"]}
    
    async def update_integration(self, org_id: str, integration_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update integration"""
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.integrations.update_one(
            {"organization_id": org_id, "integration_id": integration_id},
            {"$set": data}
        )
        
        integration = await self.integrations.find_one(
            {"organization_id": org_id, "integration_id": integration_id},
            {"_id": 0, "api_secret": 0}
        )
        return integration
    
    # ==================== API KEYS ====================
    
    async def get_api_keys(self, org_id: str) -> List[Dict[str, Any]]:
        """Get API keys (without full key)"""
        keys = await self.api_keys.find(
            {"organization_id": org_id, "is_active": True},
            {"_id": 0, "key": 0}  # Exclude actual key
        ).to_list(50)
        return keys
    
    async def create_api_key(self, org_id: str, user_id: str, name: str, permissions: List[str] = None) -> Dict[str, Any]:
        """Create API key - returns full key only once"""
        import secrets
        
        key_id = generate_id("KEY")
        api_key = f"bw_{secrets.token_urlsafe(32)}"
        key_prefix = api_key[:12]
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "key_id": key_id,
            "organization_id": org_id,
            "name": name,
            "key": api_key,  # Store full key (hashed in production)
            "key_prefix": key_prefix,
            "permissions": permissions or ["read"],
            "rate_limit": 1000,
            "is_active": True,
            "created_at": now,
            "created_by": user_id
        }
        
        await self.api_keys.insert_one(doc)
        
        # Return with full key (only time it's shown)
        return {
            "key_id": key_id,
            "name": name,
            "key": api_key,  # Full key shown only on creation
            "key_prefix": key_prefix,
            "permissions": permissions or ["read"],
            "created_at": now
        }
    
    async def revoke_api_key(self, org_id: str, key_id: str) -> bool:
        """Revoke an API key"""
        result = await self.api_keys.update_one(
            {"organization_id": org_id, "key_id": key_id},
            {"$set": {"is_active": False, "revoked_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0
    
    # ==================== WEBHOOKS ====================
    
    async def get_webhooks(self, org_id: str) -> List[Dict[str, Any]]:
        """Get webhooks"""
        webhooks = await self.webhooks.find(
            {"organization_id": org_id},
            {"_id": 0, "secret": 0}
        ).to_list(50)
        return webhooks
    
    async def create_webhook(self, org_id: str, data: WebhookEndpoint) -> Dict[str, Any]:
        """Create webhook endpoint"""
        import secrets
        
        webhook_id = generate_id("WH")
        webhook_secret = f"whsec_{secrets.token_urlsafe(24)}"
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "webhook_id": webhook_id,
            "organization_id": org_id,
            **data.model_dump(),
            "secret": webhook_secret,
            "created_at": now,
            "updated_at": now
        }
        
        await self.webhooks.insert_one(doc)
        
        return {
            "webhook_id": webhook_id,
            "name": data.name,
            "url": data.url,
            "events": data.events,
            "secret": webhook_secret,  # Show secret only on creation
            "is_active": data.is_active,
            "created_at": now
        }
    
    async def update_webhook(self, org_id: str, webhook_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update webhook"""
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.webhooks.update_one(
            {"organization_id": org_id, "webhook_id": webhook_id},
            {"$set": data}
        )
        
        webhook = await self.webhooks.find_one(
            {"organization_id": org_id, "webhook_id": webhook_id},
            {"_id": 0, "secret": 0}
        )
        return webhook
    
    async def delete_webhook(self, org_id: str, webhook_id: str) -> bool:
        """Delete webhook"""
        result = await self.webhooks.delete_one(
            {"organization_id": org_id, "webhook_id": webhook_id}
        )
        return result.deleted_count > 0
    
    # ==================== ALL SETTINGS ====================
    
    async def get_all_settings(self, org_id: str) -> Dict[str, Any]:
        """Get all settings for organization"""
        # Fetch all settings in parallel would be ideal, but for clarity:
        settings = {
            "organization": await self.get_organization_profile(org_id),
            "branding": await self.get_branding(org_id),
            "locations": await self.get_locations(org_id),
            "gst": await self.get_gst_settings(org_id),
            "tds": await self.get_tds_settings(org_id),
            "msme": await self.get_msme_settings(org_id),
            "tax_rates": await self.get_tax_rates(org_id),
            "tax_groups": await self.get_tax_groups(org_id),
            "custom_fields": await self.get_custom_fields(org_id),
            "numbering_series": await self.get_numbering_series(org_id),
            "workflow_rules": await self.get_workflow_rules(org_id),
            "vehicles": await self.get_module_settings(org_id, "vehicles"),
            "tickets": await self.get_module_settings(org_id, "tickets"),
            "work_orders": await self.get_module_settings(org_id, "work_orders"),
            "inventory": await self.get_module_settings(org_id, "inventory"),
            "customers": await self.get_module_settings(org_id, "customers"),
            "billing": await self.get_module_settings(org_id, "billing"),
            "efi": await self.get_module_settings(org_id, "efi"),
            "portal": await self.get_module_settings(org_id, "portal"),
            "notification_templates": await self.get_notification_templates(org_id),
            "pdf_templates": await self.get_pdf_templates(org_id),
            "integrations": await self.get_integrations(org_id),
            "api_keys": await self.get_api_keys(org_id),
            "webhooks": await self.get_webhooks(org_id)
        }
        
        return settings


# Global service instance
_settings_service: Optional[SettingsService] = None


def init_settings_service(db: AsyncIOMotorDatabase):
    """Initialize the settings service"""
    global _settings_service
    _settings_service = SettingsService(db)
    return _settings_service


def get_settings_service() -> SettingsService:
    """Get the settings service instance"""
    if _settings_service is None:
        raise RuntimeError("Settings service not initialized")
    return _settings_service
