"""
Battwheels OS - Settings Models
Comprehensive settings models for Zoho Books-style configuration
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class DataType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    DROPDOWN = "dropdown"
    MULTI_SELECT = "multi_select"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    CURRENCY = "currency"
    PERCENT = "percent"
    TEXTAREA = "textarea"
    LOOKUP = "lookup"
    AUTO_NUMBER = "auto_number"
    FORMULA = "formula"


class PrivacyLevel(str, Enum):
    NONE = "none"
    PII = "pii"  # Personally Identifiable Information
    EPHI = "ephi"  # Electronic Protected Health Information
    SENSITIVE = "sensitive"


class TriggerType(str, Enum):
    ON_CREATE = "on_create"
    ON_UPDATE = "on_update"
    ON_CREATE_OR_UPDATE = "on_create_or_update"
    ON_DELETE = "on_delete"
    DATE_BASED = "date_based"
    FIELD_UPDATE = "field_update"


class ActionType(str, Enum):
    EMAIL_ALERT = "email_alert"
    FIELD_UPDATE = "field_update"
    WEBHOOK = "webhook"
    CUSTOM_FUNCTION = "custom_function"
    CREATE_TASK = "create_task"
    ASSIGN_USER = "assign_user"
    SEND_SMS = "send_sms"
    SEND_WHATSAPP = "send_whatsapp"


class TaxType(str, Enum):
    GST = "gst"
    IGST = "igst"
    CGST = "cgst"
    SGST = "sgst"
    CESS = "cess"
    VAT = "vat"
    SERVICE_TAX = "service_tax"
    CUSTOM = "custom"


class ModuleName(str, Enum):
    VEHICLES = "vehicles"
    TICKETS = "tickets"
    WORK_ORDERS = "work_orders"
    PARTS_INVENTORY = "parts_inventory"
    CUSTOMERS = "customers"
    VENDORS = "vendors"
    BILLING = "billing"
    INVOICES = "invoices"
    QUOTES = "quotes"
    SALES_ORDERS = "sales_orders"
    PURCHASE_ORDERS = "purchase_orders"
    PAYMENTS = "payments"
    EXPENSES = "expenses"
    EFI = "efi"


# ==================== ORGANIZATION SETTINGS ====================

class BrandingSettings(BaseModel):
    """Organization branding configuration"""
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#10B981"
    secondary_color: str = "#3B82F6"
    accent_color: str = "#F59E0B"
    dark_mode_enabled: bool = True
    custom_css: Optional[str] = None


class LocationCreate(BaseModel):
    """Branch/Location creation"""
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    is_primary: bool = False
    is_active: bool = True


class Location(LocationCreate):
    """Location with ID"""
    location_id: str
    organization_id: str
    created_at: str
    updated_at: str


class SubscriptionInfo(BaseModel):
    """Subscription/plan details"""
    plan_type: str = "professional"
    billing_cycle: str = "monthly"  # monthly, yearly
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    max_users: int = 10
    max_locations: int = 5
    features_enabled: List[str] = []
    add_ons: List[str] = []


class OrganizationProfile(BaseModel):
    """Complete organization profile settings"""
    name: str
    legal_name: Optional[str] = None
    industry: str = "ev_aftersales"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    msme_registration: Optional[str] = None
    msme_type: Optional[str] = None  # micro, small, medium
    timezone: str = "Asia/Kolkata"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "12h"  # 12h, 24h
    fiscal_year_start: str = "04"  # April
    currency: str = "INR"
    language: str = "en"


# ==================== TAX SETTINGS ====================

class TaxRate(BaseModel):
    """Individual tax rate"""
    tax_rate_id: Optional[str] = None
    name: str
    tax_type: TaxType
    rate: float
    description: Optional[str] = None
    is_compound: bool = False
    is_default: bool = False
    is_active: bool = True
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class TaxGroup(BaseModel):
    """Tax group combining multiple taxes"""
    tax_group_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    tax_rate_ids: List[str] = []
    combined_rate: float = 0.0
    is_default: bool = False
    is_active: bool = True


class HSNCode(BaseModel):
    """HSN/SAC code for GST"""
    hsn_code: str
    description: str
    gst_rate: float
    cess_rate: float = 0.0
    category: str  # goods, services
    is_active: bool = True


class GSTSettings(BaseModel):
    """GST compliance settings"""
    is_gst_registered: bool = True
    gstin: Optional[str] = None
    gst_treatment: str = "registered_business"  # registered_business, unregistered, consumer, overseas
    reverse_charge_applicable: bool = False
    composition_scheme: bool = False
    e_invoicing_enabled: bool = False
    e_invoicing_threshold: float = 50000000  # 5 Cr default
    eway_bill_enabled: bool = False
    eway_bill_threshold: float = 50000
    einvoice_username: Optional[str] = None
    einvoice_password: Optional[str] = None  # Encrypted
    eway_username: Optional[str] = None
    eway_password: Optional[str] = None  # Encrypted


class TDSSettings(BaseModel):
    """TDS/Direct tax settings"""
    is_tds_applicable: bool = False
    tan: Optional[str] = None
    deductor_type: Optional[str] = None
    default_tds_section: Optional[str] = None
    auto_calculate_tds: bool = True


class MSMESettings(BaseModel):
    """MSME compliance settings"""
    is_msme_registered: bool = False
    udyam_registration: Optional[str] = None
    msme_type: Optional[str] = None  # micro, small, medium
    payment_terms_days: int = 45  # MSME Act requirement


# ==================== CUSTOM FIELDS ====================

class CustomFieldOption(BaseModel):
    """Dropdown/multi-select option"""
    value: str
    label: str
    color: Optional[str] = None
    is_default: bool = False
    sort_order: int = 0


class ValidationRule(BaseModel):
    """Field validation rule"""
    rule_type: str  # required, min_length, max_length, regex, range, unique
    value: Any
    error_message: str


class CustomFieldCreate(BaseModel):
    """Custom field definition"""
    module: ModuleName
    field_name: str
    label: str
    data_type: DataType
    description: Optional[str] = None
    help_text: Optional[str] = None
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    is_required: bool = False
    is_unique: bool = False
    is_searchable: bool = True
    is_visible_in_list: bool = True
    is_visible_in_form: bool = True
    is_editable: bool = True
    privacy_level: PrivacyLevel = PrivacyLevel.NONE
    options: List[CustomFieldOption] = []
    validation_rules: List[ValidationRule] = []
    lookup_module: Optional[str] = None  # For lookup fields
    formula: Optional[str] = None  # For formula fields
    auto_number_prefix: Optional[str] = None
    auto_number_suffix: Optional[str] = None
    auto_number_start: int = 1
    sort_order: int = 0
    section: Optional[str] = None  # Group fields in sections
    column_span: int = 1  # 1 or 2 for form layout


class CustomField(CustomFieldCreate):
    """Custom field with ID"""
    field_id: str
    organization_id: str
    created_at: str
    updated_at: str
    created_by: Optional[str] = None


# ==================== NUMBERING SERIES ====================

class NumberingSeries(BaseModel):
    """Transaction numbering series"""
    series_id: Optional[str] = None
    module: ModuleName
    name: str
    prefix: str
    suffix: Optional[str] = None
    start_number: int = 1
    current_number: int = 1
    padding_zeros: int = 4  # e.g., 0001, 00001
    includes_year: bool = True
    year_format: str = "YY"  # YY or YYYY
    includes_month: bool = False
    separator: str = "-"
    is_default: bool = False
    is_active: bool = True
    reset_on_year: bool = True
    reset_on_month: bool = False
    location_id: Optional[str] = None  # Location-specific series


# ==================== WORKFLOW AUTOMATION ====================

class WorkflowCondition(BaseModel):
    """Workflow rule condition"""
    field: str
    operator: str  # equals, not_equals, contains, greater_than, less_than, is_empty, is_not_empty, changed_to
    value: Any
    logic: str = "and"  # and, or


class EmailAlertAction(BaseModel):
    """Email alert configuration"""
    template_id: Optional[str] = None
    subject: str
    body: str
    to_field: Optional[str] = None  # Field containing email
    to_emails: List[str] = []
    cc_emails: List[str] = []
    include_record_link: bool = True
    attach_pdf: bool = False


class FieldUpdateAction(BaseModel):
    """Field update configuration"""
    field: str
    update_type: str  # set_value, increment, decrement, clear, copy_from
    value: Any
    source_field: Optional[str] = None


class WebhookAction(BaseModel):
    """Webhook configuration"""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = {}
    payload_template: Optional[str] = None
    include_record_data: bool = True
    timeout_seconds: int = 30
    retry_count: int = 3


class CustomFunctionAction(BaseModel):
    """Custom function configuration"""
    function_name: str
    function_code: str
    language: str = "python"  # python, javascript
    parameters: Dict[str, Any] = {}


class WorkflowAction(BaseModel):
    """Workflow action definition"""
    action_id: Optional[str] = None
    action_type: ActionType
    name: str
    description: Optional[str] = None
    email_alert: Optional[EmailAlertAction] = None
    field_update: Optional[FieldUpdateAction] = None
    webhook: Optional[WebhookAction] = None
    custom_function: Optional[CustomFunctionAction] = None
    execution_order: int = 0
    is_active: bool = True


class WorkflowRuleCreate(BaseModel):
    """Workflow rule definition"""
    module: ModuleName
    name: str
    description: Optional[str] = None
    trigger_type: TriggerType
    trigger_field: Optional[str] = None  # For field_update trigger
    trigger_date_field: Optional[str] = None  # For date_based trigger
    trigger_days_before: int = 0
    trigger_days_after: int = 0
    trigger_time: Optional[str] = None  # HH:MM for date-based
    conditions: List[WorkflowCondition] = []
    condition_logic: str = "all"  # all, any, custom
    custom_condition_logic: Optional[str] = None  # e.g., "(1 AND 2) OR 3"
    actions: List[WorkflowAction] = []
    is_active: bool = True
    execution_order: int = 0


class WorkflowRule(WorkflowRuleCreate):
    """Workflow rule with ID"""
    rule_id: str
    organization_id: str
    created_at: str
    updated_at: str
    created_by: Optional[str] = None
    last_triggered: Optional[str] = None
    trigger_count: int = 0


class WorkflowLog(BaseModel):
    """Workflow execution log"""
    log_id: str
    rule_id: str
    rule_name: str
    module: str
    record_id: str
    trigger_type: str
    executed_at: str
    status: str  # success, failed, partial
    actions_executed: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    execution_time_ms: int = 0


# ==================== MODULE SETTINGS ====================

class VehicleSettings(BaseModel):
    """Vehicle module settings"""
    categories: List[str] = ["2-wheeler", "3-wheeler", "4-wheeler", "commercial"]
    statuses: List[str] = ["active", "in_workshop", "serviced", "sold", "scrapped"]
    default_warranty_months: int = 24
    battery_warranty_months: int = 36
    telemetry_enabled: bool = False
    telemetry_provider: Optional[str] = None
    vin_validation_enabled: bool = True
    auto_create_customer: bool = True


class TicketSettings(BaseModel):
    """Ticket/Service case settings"""
    categories: List[str] = ["breakdown", "maintenance", "recall", "warranty", "accident", "insurance"]
    priorities: List[str] = ["low", "medium", "high", "critical"]
    statuses: List[str] = ["open", "assigned", "in_progress", "pending_parts", "resolved", "closed"]
    default_priority: str = "medium"
    sla_enabled: bool = True
    sla_targets: Dict[str, int] = {
        "critical": 4,  # hours
        "high": 8,
        "medium": 24,
        "low": 48
    }
    auto_assign_enabled: bool = False
    auto_assign_by: str = "location"  # location, skill, workload
    escalation_enabled: bool = True
    escalation_hours: int = 24
    customer_notification_on_create: bool = True
    customer_notification_on_update: bool = True
    customer_notification_on_resolve: bool = True


class WorkOrderSettings(BaseModel):
    """Work order settings"""
    statuses: List[str] = ["draft", "pending_approval", "approved", "in_progress", "completed", "cancelled"]
    approval_required: bool = False
    approval_threshold: float = 10000
    default_labor_rate: float = 500
    labor_codes: List[Dict[str, Any]] = []
    checklist_required: bool = True
    default_checklist_items: List[str] = []
    parts_allocation_required: bool = True
    technician_signature_required: bool = True
    customer_signature_required: bool = True
    auto_generate_invoice: bool = False


class InventorySettings(BaseModel):
    """Parts/Inventory settings"""
    tracking_method: str = "fifo"  # fifo, lifo, average
    enable_serial_tracking: bool = True
    enable_batch_tracking: bool = True
    low_stock_alert_enabled: bool = True
    low_stock_threshold: int = 10
    reorder_point_enabled: bool = True
    auto_reorder_enabled: bool = False
    default_unit: str = "pcs"
    units_of_measure: List[str] = ["pcs", "kg", "ltr", "mtr", "set", "pair"]
    price_lists_enabled: bool = True
    multi_warehouse_enabled: bool = False
    barcode_enabled: bool = True
    barcode_format: str = "code128"


class CustomerSettings(BaseModel):
    """Customer module settings"""
    categories: List[str] = ["individual", "fleet", "dealer", "corporate"]
    credit_limit_enabled: bool = True
    default_credit_limit: float = 50000
    payment_terms_days: int = 30
    auto_send_statement: bool = False
    statement_frequency: str = "monthly"
    loyalty_program_enabled: bool = False
    portal_enabled: bool = True


class BillingSettings(BaseModel):
    """Billing/Invoice settings"""
    invoice_prefix: str = "INV"
    quote_prefix: str = "QT"
    sales_order_prefix: str = "SO"
    default_payment_terms: int = 30
    default_due_days: int = 30
    discount_type: str = "percentage"  # percentage, amount
    max_discount_percent: float = 20
    discount_approval_required: bool = False
    discount_approval_threshold: float = 10
    shipping_charges_enabled: bool = True
    adjustment_enabled: bool = True
    round_off_enabled: bool = True
    round_off_to: float = 1  # Round to nearest 1
    auto_send_invoice: bool = False
    auto_send_reminder: bool = True
    reminder_days_before_due: List[int] = [7, 3, 1]
    reminder_days_after_due: List[int] = [1, 7, 14, 30]
    late_fee_enabled: bool = False
    late_fee_type: str = "percentage"
    late_fee_value: float = 2
    credit_note_prefix: str = "CN"
    debit_note_prefix: str = "DN"


class EFISettings(BaseModel):
    """Failure Intelligence (EFI) settings"""
    failure_categories: List[str] = [
        "battery", "motor", "controller", "charger", "bms",
        "electrical", "mechanical", "software", "sensor", "other"
    ]
    severity_levels: List[str] = ["minor", "moderate", "major", "critical"]
    repeat_failure_threshold: int = 3
    repeat_failure_days: int = 90
    auto_escalate_repeat_failures: bool = True
    knowledge_base_suggestions_enabled: bool = True
    ai_diagnosis_enabled: bool = True
    parts_recommendation_enabled: bool = True
    warranty_check_enabled: bool = True


# ==================== NOTIFICATION TEMPLATES ====================

class NotificationTemplate(BaseModel):
    """Email/SMS/WhatsApp template"""
    template_id: Optional[str] = None
    name: str
    module: ModuleName
    event: str  # created, updated, reminder, etc.
    channel: str  # email, sms, whatsapp
    subject: Optional[str] = None  # For email
    body: str
    variables: List[str] = []  # Available merge fields
    is_default: bool = False
    is_active: bool = True


# ==================== PDF TEMPLATES ====================

class PDFTemplate(BaseModel):
    """PDF template for documents"""
    template_id: Optional[str] = None
    name: str
    module: ModuleName
    document_type: str  # invoice, quote, work_order, job_card, receipt
    html_template: str
    css_styles: Optional[str] = None
    header_html: Optional[str] = None
    footer_html: Optional[str] = None
    page_size: str = "A4"
    page_orientation: str = "portrait"
    margins: Dict[str, int] = {"top": 20, "right": 20, "bottom": 20, "left": 20}
    is_default: bool = False
    is_active: bool = True


# ==================== PORTAL SETTINGS ====================

class PortalSettings(BaseModel):
    """Customer/Vendor portal settings"""
    customer_portal_enabled: bool = True
    customer_portal_url: Optional[str] = None
    customer_can_view_invoices: bool = True
    customer_can_view_quotes: bool = True
    customer_can_accept_quotes: bool = True
    customer_can_pay_online: bool = True
    customer_can_raise_tickets: bool = True
    customer_can_track_service: bool = True
    vendor_portal_enabled: bool = False
    vendor_can_view_pos: bool = True
    vendor_can_update_delivery: bool = True


# ==================== INTEGRATION SETTINGS ====================

class IntegrationSettings(BaseModel):
    """Third-party integration settings"""
    integration_id: Optional[str] = None
    name: str
    provider: str  # zoho, tally, quickbooks, stripe, razorpay, etc.
    is_enabled: bool = False
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    sync_frequency: str = "realtime"  # realtime, hourly, daily
    last_sync: Optional[str] = None
    sync_status: str = "idle"
    config: Dict[str, Any] = {}


# ==================== DEVELOPER SETTINGS ====================

class APIKeySettings(BaseModel):
    """API key for external access"""
    key_id: Optional[str] = None
    name: str
    key: str  # The actual API key (show only once on creation)
    key_prefix: str  # First 8 chars for identification
    permissions: List[str] = []
    rate_limit: int = 1000  # requests per hour
    expires_at: Optional[str] = None
    last_used: Optional[str] = None
    is_active: bool = True
    created_at: str
    created_by: str


class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration"""
    webhook_id: Optional[str] = None
    name: str
    url: str
    events: List[str] = []  # ticket.created, invoice.paid, etc.
    secret: Optional[str] = None  # For signature verification
    is_active: bool = True
    last_triggered: Optional[str] = None
    failure_count: int = 0


# ==================== MASTER SETTINGS CONTAINER ====================

class AllSettings(BaseModel):
    """Container for all settings categories"""
    organization: OrganizationProfile
    branding: BrandingSettings
    locations: List[Location] = []
    subscription: SubscriptionInfo
    gst: GSTSettings
    tds: TDSSettings
    msme: MSMESettings
    tax_rates: List[TaxRate] = []
    tax_groups: List[TaxGroup] = []
    hsn_codes: List[HSNCode] = []
    custom_fields: List[CustomField] = []
    numbering_series: List[NumberingSeries] = []
    workflow_rules: List[WorkflowRule] = []
    vehicles: VehicleSettings
    tickets: TicketSettings
    work_orders: WorkOrderSettings
    inventory: InventorySettings
    customers: CustomerSettings
    billing: BillingSettings
    efi: EFISettings
    notification_templates: List[NotificationTemplate] = []
    pdf_templates: List[PDFTemplate] = []
    portal: PortalSettings
    integrations: List[IntegrationSettings] = []
