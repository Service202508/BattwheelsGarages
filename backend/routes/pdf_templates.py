# PDF Template Customization Module
# Allows users to customize invoice, estimate, and other document templates

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import motor.motor_asyncio
import os
import uuid
from fastapi import Request
from utils.database import extract_org_id, org_query


router = APIRouter(prefix="/pdf-templates", tags=["PDF Templates"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
templates_collection = db["pdf_templates"]
org_settings_collection = db["organization_settings"]

# ========================= MODELS =========================

class TemplateColors(BaseModel):
    """Color scheme for templates"""
    primary: str = "#22EDA9"
    secondary: str = "#1a1a1a"
    accent: str = "#3B82F6"
    text: str = "#333333"
    muted: str = "#666666"
    border: str = "#e5e7eb"
    background: str = "#ffffff"

class TemplateFont(BaseModel):
    """Font settings"""
    family: str = "Helvetica Neue, Arial, sans-serif"
    size_heading: int = 24
    size_subheading: int = 14
    size_body: int = 10
    size_small: int = 9

class TemplateLayout(BaseModel):
    """Layout settings"""
    page_size: str = "A4"  # A4, Letter, Legal
    margin_top: int = 20
    margin_bottom: int = 20
    margin_left: int = 20
    margin_right: int = 20
    header_height: int = 80
    footer_height: int = 40

class TemplateElements(BaseModel):
    """Toggle visibility of elements"""
    show_logo: bool = True
    show_company_address: bool = True
    show_company_phone: bool = True
    show_company_email: bool = True
    show_company_gstin: bool = True
    show_customer_gstin: bool = True
    show_hsn_sac: bool = True
    show_tax_breakdown: bool = True
    show_payment_info: bool = True
    show_notes: bool = True
    show_terms: bool = True
    show_signature_line: bool = False
    show_watermark: bool = False
    show_qr_code: bool = False

class TemplateLabels(BaseModel):
    """Customize labels"""
    invoice_title: str = "INVOICE"
    estimate_title: str = "ESTIMATE"
    bill_to_label: str = "Bill To"
    ship_to_label: str = "Ship To"
    invoice_date_label: str = "Invoice Date"
    due_date_label: str = "Due Date"
    subtotal_label: str = "Subtotal"
    tax_label: str = "Tax (GST)"
    total_label: str = "Total"
    balance_due_label: str = "Balance Due"
    notes_label: str = "Notes"
    terms_label: str = "Terms & Conditions"

class PDFTemplateCreate(BaseModel):
    """Create a PDF template"""
    name: str
    template_type: str = "invoice"  # invoice, estimate, sales_order, credit_note
    style: str = "modern"  # modern, classic, minimal, professional
    colors: TemplateColors = TemplateColors()
    font: TemplateFont = TemplateFont()
    layout: TemplateLayout = TemplateLayout()
    elements: TemplateElements = TemplateElements()
    labels: TemplateLabels = TemplateLabels()
    custom_header_html: str = ""
    custom_footer_html: str = ""
    custom_css: str = ""
    is_default: bool = False

class PDFTemplateUpdate(BaseModel):
    """Update a PDF template"""
    name: Optional[str] = None
    style: Optional[str] = None
    colors: Optional[TemplateColors] = None
    font: Optional[TemplateFont] = None
    layout: Optional[TemplateLayout] = None
    elements: Optional[TemplateElements] = None
    labels: Optional[TemplateLabels] = None
    custom_header_html: Optional[str] = None
    custom_footer_html: Optional[str] = None
    custom_css: Optional[str] = None
    is_default: Optional[bool] = None

# ========================= DEFAULT TEMPLATES =========================

DEFAULT_TEMPLATES = [
    {
        "template_id": "TPL-DEFAULT-MODERN",
        "name": "Modern Green",
        "template_type": "invoice",
        "style": "modern",
        "colors": {
            "primary": "#22EDA9",
            "secondary": "#1a1a1a",
            "accent": "#22EDA9",
            "text": "#333333",
            "muted": "#666666",
            "border": "#e5e7eb",
            "background": "#ffffff"
        },
        "is_system": True,
        "is_default": True
    },
    {
        "template_id": "TPL-DEFAULT-CLASSIC",
        "name": "Classic Blue",
        "template_type": "invoice",
        "style": "classic",
        "colors": {
            "primary": "#3B82F6",
            "secondary": "#1e3a5f",
            "accent": "#3B82F6",
            "text": "#333333",
            "muted": "#666666",
            "border": "#e5e7eb",
            "background": "#ffffff"
        },
        "is_system": True,
        "is_default": False
    },
    {
        "template_id": "TPL-DEFAULT-MINIMAL",
        "name": "Minimal Gray",
        "template_type": "invoice",
        "style": "minimal",
        "colors": {
            "primary": "#6B7280",
            "secondary": "#374151",
            "accent": "#6B7280",
            "text": "#111827",
            "muted": "#9CA3AF",
            "border": "#E5E7EB",
            "background": "#ffffff"
        },
        "is_system": True,
        "is_default": False
    },
    {
        "template_id": "TPL-DEFAULT-PROFESSIONAL",
        "name": "Professional Dark",
        "template_type": "invoice",
        "style": "professional",
        "colors": {
            "primary": "#1F2937",
            "secondary": "#111827",
            "accent": "#F59E0B",
            "text": "#374151",
            "muted": "#6B7280",
            "border": "#D1D5DB",
            "background": "#ffffff"
        },
        "is_system": True,
        "is_default": False
    }
]

# ========================= HELPERS =========================

def generate_id() -> str:
    return f"TPL-{uuid.uuid4().hex[:12].upper()}"

async def ensure_default_templates():
    """Ensure default templates exist"""
    for template in DEFAULT_TEMPLATES:
        existing = await templates_collection.find_one({"template_id": template["template_id"]})
        if not existing:
            template["created_time"] = datetime.now(timezone.utc).isoformat()
            await templates_collection.insert_one(template)

# ========================= ENDPOINTS =========================

@router.get("/")
async def list_templates(template_type: Optional[str] = None, request: Request):
    org_id = extract_org_id(request)
    """List all available templates"""
    await ensure_default_templates()
    
    query = {}
    if template_type:
        query["template_type"] = template_type
    
    templates = await templates_collection.find(query, {"_id": 0}).to_list(100)
    
    return {
        "code": 0,
        "templates": templates,
        "total": len(templates)
    }

@router.get("/styles")
async def list_available_styles(request: Request):
    org_id = extract_org_id(request)
    """List available template styles"""
    return {
        "code": 0,
        "styles": [
            {"id": "modern", "name": "Modern", "description": "Clean, contemporary design with accent colors"},
            {"id": "classic", "name": "Classic", "description": "Traditional business document layout"},
            {"id": "minimal", "name": "Minimal", "description": "Simple, no-frills design focused on content"},
            {"id": "professional", "name": "Professional", "description": "Formal business style with dark accents"}
        ]
    }

@router.get("/{template_id}")
async def get_template(template_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get template details"""
    template = await templates_collection.find_one({"template_id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"code": 0, "template": template}

@router.post("/")
async def create_template(data: PDFTemplateCreate, request: Request):
    org_id = extract_org_id(request)
    """Create a custom template"""
    template_id = generate_id()
    
    template_doc = {
        "template_id": template_id,
        "name": data.name,
        "template_type": data.template_type,
        "style": data.style,
        "colors": data.colors.dict(),
        "font": data.font.dict(),
        "layout": data.layout.dict(),
        "elements": data.elements.dict(),
        "labels": data.labels.dict(),
        "custom_header_html": data.custom_header_html,
        "custom_footer_html": data.custom_footer_html,
        "custom_css": data.custom_css,
        "is_default": data.is_default,
        "is_system": False,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    # If setting as default, unset other defaults
    if data.is_default:
        await templates_collection.update_many(
            {"template_type": data.template_type, "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    await templates_collection.insert_one(template_doc)
    template_doc.pop("_id", None)
    
    return {"code": 0, "message": "Template created", "template": template_doc}

@router.put("/{template_id}")
async def update_template(template_id: str, data: PDFTemplateUpdate, request: Request):
    org_id = extract_org_id(request)
    """Update a template"""
    template = await templates_collection.find_one({"template_id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.get("is_system"):
        raise HTTPException(status_code=400, detail="System templates cannot be modified. Create a copy instead.")
    
    update_data = {"updated_time": datetime.now(timezone.utc).isoformat()}
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            if isinstance(value, dict):
                update_data[field] = value
            else:
                update_data[field] = value
    
    # Handle default flag
    if data.is_default:
        await templates_collection.update_many(
            {"template_type": template["template_type"], "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    await templates_collection.update_one(
        {"template_id": template_id},
        {"$set": update_data}
    )
    
    return {"code": 0, "message": "Template updated"}

@router.post("/{template_id}/duplicate")
async def duplicate_template(template_id: str, new_name: str = "", request: Request):
    org_id = extract_org_id(request)
    """Duplicate a template (useful for customizing system templates)"""
    template = await templates_collection.find_one({"template_id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    new_id = generate_id()
    new_template = template.copy()
    new_template["template_id"] = new_id
    new_template["name"] = new_name or f"{template['name']} (Copy)"
    new_template["is_system"] = False
    new_template["is_default"] = False
    new_template["created_time"] = datetime.now(timezone.utc).isoformat()
    new_template["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    await templates_collection.insert_one(new_template)
    new_template.pop("_id", None)
    
    return {"code": 0, "message": "Template duplicated", "template": new_template}

@router.delete("/{template_id}")
async def delete_template(template_id: str, request: Request):
    org_id = extract_org_id(request)
    """Delete a custom template"""
    template = await templates_collection.find_one({"template_id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.get("is_system"):
        raise HTTPException(status_code=400, detail="System templates cannot be deleted")
    
    await templates_collection.delete_one({"template_id": template_id})
    
    return {"code": 0, "message": "Template deleted"}

@router.post("/{template_id}/set-default")
async def set_default_template(template_id: str, request: Request):
    org_id = extract_org_id(request)
    """Set a template as default for its type"""
    template = await templates_collection.find_one({"template_id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Unset other defaults
    await templates_collection.update_many(
        {"template_type": template["template_type"], "is_default": True},
        {"$set": {"is_default": False}}
    )
    
    # Set this as default
    await templates_collection.update_one(
        {"template_id": template_id},
        {"$set": {"is_default": True}}
    )
    
    return {"code": 0, "message": f"Template '{template['name']}' set as default"}

@router.get("/default/{template_type}")
async def get_default_template(template_type: str, request: Request):
    org_id = extract_org_id(request)
    """Get the default template for a document type"""
    await ensure_default_templates()
    
    template = await templates_collection.find_one(
        {"template_type": template_type, "is_default": True},
        {"_id": 0}
    )
    
    if not template:
        # Fallback to first system template
        template = await templates_collection.find_one(
            {"template_type": template_type, "is_system": True},
            {"_id": 0}
        )
    
    if not template:
        raise HTTPException(status_code=404, detail=f"No template found for {template_type}")
    
    return {"code": 0, "template": template}

# ========================= PREVIEW =========================

@router.post("/preview")
async def preview_template(template_id: str, sample_data: Dict = None, request: Request):
    org_id = extract_org_id(request)
    """Generate a preview HTML for a template"""
    template = await templates_collection.find_one({"template_id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Sample data for preview
    if not sample_data:
        sample_data = {
            "invoice_number": "INV-2026-0001",
            "date": "2026-02-19",
            "due_date": "2026-03-05",
            "customer_name": "Sample Customer",
            "customer_address": "123 Main Street, City, State 12345",
            "line_items": [
                {"name": "Product A", "quantity": 2, "rate": 500, "item_total": 1000},
                {"name": "Service B", "quantity": 1, "rate": 750, "item_total": 750}
            ],
            "sub_total": 1750,
            "tax_total": 315,
            "total": 2065,
            "balance": 2065
        }
    
    # Generate HTML using template settings
    colors = template.get("colors", {})
    elements = template.get("elements", {})
    labels = template.get("labels", {})
    
    preview_html = f"""
    <div style="font-family: {template.get('font', {}).get('family', 'Arial')}; 
                max-width: 800px; margin: 0 auto; padding: 20px; 
                background: {colors.get('background', '#fff')}; 
                color: {colors.get('text', '#333')};">
        <div style="border-bottom: 3px solid {colors.get('primary', '#22EDA9')}; 
                    padding-bottom: 15px; margin-bottom: 20px; 
                    display: flex; justify-content: space-between;">
            <div>
                <div style="font-size: 24px; font-weight: bold;">Company Name</div>
                <div style="font-size: 10px; color: {colors.get('muted', '#666')};">
                    Company Address<br>Phone: 123-456-7890<br>Email: info@company.com
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 28px; color: {colors.get('primary', '#22EDA9')}; font-weight: bold;">
                    {labels.get('invoice_title', 'INVOICE')}
                </div>
                <div style="font-size: 12px; color: {colors.get('muted', '#666')};">
                    #{sample_data.get('invoice_number')}
                </div>
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
            <div>
                <div style="font-size: 9px; color: {colors.get('muted', '#888')}; 
                            text-transform: uppercase; margin-bottom: 5px;">
                    {labels.get('bill_to_label', 'Bill To')}
                </div>
                <div style="font-weight: bold;">{sample_data.get('customer_name')}</div>
                <div style="font-size: 9px; color: {colors.get('muted', '#666')};">
                    {sample_data.get('customer_address')}
                </div>
            </div>
            <div style="text-align: right;">
                <div>{labels.get('invoice_date_label', 'Invoice Date')}: {sample_data.get('date')}</div>
                <div>{labels.get('due_date_label', 'Due Date')}: {sample_data.get('due_date')}</div>
            </div>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="padding: 10px; text-align: left; 
                               border-bottom: 2px solid {colors.get('primary', '#22EDA9')};">Item</th>
                    <th style="padding: 10px; text-align: right; 
                               border-bottom: 2px solid {colors.get('primary', '#22EDA9')};">Qty</th>
                    <th style="padding: 10px; text-align: right; 
                               border-bottom: 2px solid {colors.get('primary', '#22EDA9')};">Rate</th>
                    <th style="padding: 10px; text-align: right; 
                               border-bottom: 2px solid {colors.get('primary', '#22EDA9')};">Amount</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''
                <tr style="border-bottom: 1px solid {colors.get('border', '#eee')};">
                    <td style="padding: 10px;">{item['name']}</td>
                    <td style="padding: 10px; text-align: right;">{item['quantity']}</td>
                    <td style="padding: 10px; text-align: right;">₹{item['rate']:,.2f}</td>
                    <td style="padding: 10px; text-align: right;">₹{item['item_total']:,.2f}</td>
                </tr>
                ''' for item in sample_data.get('line_items', [])])}
            </tbody>
        </table>
        
        <div style="display: flex; justify-content: flex-end;">
            <table style="width: 250px;">
                <tr>
                    <td style="padding: 8px; color: {colors.get('muted', '#666')};">{labels.get('subtotal_label', 'Subtotal')}:</td>
                    <td style="padding: 8px; text-align: right;">₹{sample_data.get('sub_total', 0):,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: {colors.get('muted', '#666')};">{labels.get('tax_label', 'Tax')}:</td>
                    <td style="padding: 8px; text-align: right;">₹{sample_data.get('tax_total', 0):,.2f}</td>
                </tr>
                <tr style="font-size: 14px; font-weight: bold; border-top: 2px solid #333;">
                    <td style="padding: 8px;">{labels.get('total_label', 'Total')}:</td>
                    <td style="padding: 8px; text-align: right;">₹{sample_data.get('total', 0):,.2f}</td>
                </tr>
                <tr style="background: {colors.get('primary', '#22EDA9')};">
                    <td style="padding: 8px; font-weight: bold;">{labels.get('balance_due_label', 'Balance Due')}:</td>
                    <td style="padding: 8px; text-align: right; font-weight: bold;">₹{sample_data.get('balance', 0):,.2f}</td>
                </tr>
            </table>
        </div>
    </div>
    """
    
    return {
        "code": 0,
        "template_id": template_id,
        "preview_html": preview_html
    }
