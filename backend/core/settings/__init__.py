"""
Battwheels OS - Settings Module
Comprehensive Zoho Books-style settings management
"""
from .models import (
    # Enums
    DataType, PrivacyLevel, TriggerType, ActionType, TaxType, ModuleName,
    # Organization
    OrganizationProfile, BrandingSettings, Location, LocationCreate, SubscriptionInfo,
    # Tax
    GSTSettings, TDSSettings, MSMESettings, TaxRate, TaxGroup, HSNCode,
    # Custom Fields
    CustomField, CustomFieldCreate, CustomFieldOption, ValidationRule,
    # Numbering
    NumberingSeries,
    # Workflow
    WorkflowRule, WorkflowRuleCreate, WorkflowAction, WorkflowCondition, WorkflowLog,
    EmailAlertAction, FieldUpdateAction, WebhookAction, CustomFunctionAction,
    # Module Settings
    VehicleSettings, TicketSettings, WorkOrderSettings, InventorySettings,
    CustomerSettings, BillingSettings, EFISettings,
    # Templates
    NotificationTemplate, PDFTemplate,
    # Portal & Integrations
    PortalSettings, IntegrationSettings, APIKeySettings, WebhookEndpoint,
    # Container
    AllSettings
)

from .service import (
    SettingsService,
    init_settings_service,
    get_settings_service
)

from .routes import router as settings_router, init_settings_routes

__all__ = [
    # Enums
    "DataType", "PrivacyLevel", "TriggerType", "ActionType", "TaxType", "ModuleName",
    # Models
    "OrganizationProfile", "BrandingSettings", "Location", "LocationCreate", "SubscriptionInfo",
    "GSTSettings", "TDSSettings", "MSMESettings", "TaxRate", "TaxGroup", "HSNCode",
    "CustomField", "CustomFieldCreate", "CustomFieldOption", "ValidationRule",
    "NumberingSeries",
    "WorkflowRule", "WorkflowRuleCreate", "WorkflowAction", "WorkflowCondition", "WorkflowLog",
    "EmailAlertAction", "FieldUpdateAction", "WebhookAction", "CustomFunctionAction",
    "VehicleSettings", "TicketSettings", "WorkOrderSettings", "InventorySettings",
    "CustomerSettings", "BillingSettings", "EFISettings",
    "NotificationTemplate", "PDFTemplate",
    "PortalSettings", "IntegrationSettings", "APIKeySettings", "WebhookEndpoint",
    "AllSettings",
    # Service
    "SettingsService", "init_settings_service", "get_settings_service",
    # Routes
    "settings_router", "init_settings_routes"
]
