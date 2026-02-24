# Enhanced Estimates/Quotes Module for Zoho Books Clone
# Full sales cycle entry point with GST calculations, status workflow, and conversions
# Phase 1: Attachments, Public Share Links, Customer Viewed Status, PDF Generation
# Phase 2: Auto-conversion, PDF Templates, Import/Export, Custom Fields, Bulk Actions

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import motor.motor_asyncio
import os
import uuid
import logging
import hashlib
import base64
import io
import csv
import json
from decimal import Decimal, ROUND_HALF_UP

# Import tenant context for multi-tenant scoping
from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/estimates-enhanced", tags=["Estimates Enhanced"])

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "zoho_books_clone")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections - Use main collections with Zoho-synced data
estimates_collection = db["estimates"]
estimate_items_collection = db["estimate_line_items"]
estimate_history_collection = db["estimate_history"]
estimate_settings_collection = db["estimate_settings"]
estimate_attachments_collection = db["estimate_attachments"]
estimate_share_links_collection = db["estimate_share_links"]

# Multi-tenant helpers (Phase F migration - using TenantContext)
async def get_org_id(request: Request) -> Optional[str]:
    """Get organization ID from request for multi-tenant scoping"""
    try:
        ctx = await optional_tenant_context(request)
        return ctx.org_id if ctx else None
    except Exception:
        return None

def org_query(org_id: Optional[str], base_query: dict = None) -> dict:
    """Add org_id to query if available"""
    query = base_query or {}
    if org_id:
        query["organization_id"] = org_id
    return query

# Attachment limits (Zoho Books style)
MAX_ATTACHMENTS_PER_ESTIMATE = 3
MAX_ATTACHMENT_SIZE_MB = 10
ALLOWED_ATTACHMENT_TYPES = [
    "application/pdf", "image/jpeg", "image/png", "image/gif",
    "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv"
]

# GST State codes for intra/inter-state calculation
GSTIN_STATE_MAP = {
    "01": "JK", "02": "HP", "03": "PB", "04": "CH", "05": "UK", "06": "HR",
    "07": "DL", "08": "RJ", "09": "UP", "10": "BR", "11": "SK", "12": "AR",
    "13": "NL", "14": "MN", "15": "MZ", "16": "TR", "17": "ML", "18": "AS",
    "19": "WB", "20": "JH", "21": "OR", "22": "CG", "23": "MP", "24": "GJ",
    "26": "DD", "27": "MH", "28": "AP", "29": "KA", "30": "GA", "31": "LD",
    "32": "KL", "33": "TN", "34": "PY", "35": "AN", "36": "TG", "37": "AP"
}

# Organization state (default - should come from settings)
ORG_STATE_CODE = "DL"  # Delhi

# ========================= PYDANTIC MODELS =========================

class LineItemCreate(BaseModel):
    item_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: str = ""
    hsn_code: str = ""
    quantity: float = Field(default=1, gt=0)
    unit: str = "pcs"
    rate: float = Field(default=0, ge=0)
    discount_percent: float = Field(default=0, ge=0, le=100)
    discount_amount: float = Field(default=0, ge=0)
    tax_id: Optional[str] = None
    tax_name: str = ""
    tax_percentage: float = Field(default=0, ge=0)
    warehouse_id: Optional[str] = None

class LineItemUpdate(BaseModel):
    item_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    rate: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    tax_id: Optional[str] = None
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = None

class EstimateCreate(BaseModel):
    customer_id: str = Field(..., min_length=1)
    estimate_number: Optional[str] = None  # Auto-generated if not provided
    reference_number: str = ""
    date: str = ""  # ISO date string
    expiry_date: str = ""  # ISO date string
    salesperson_id: Optional[str] = None
    salesperson_name: str = ""
    project_id: Optional[str] = None
    subject: str = ""
    terms_and_conditions: str = ""
    notes: str = ""
    discount_type: str = "none"  # none, percent, amount
    discount_value: float = 0
    shipping_charge: float = 0
    adjustment: float = 0
    adjustment_description: str = ""
    custom_fields: Dict[str, Any] = {}
    line_items: List[LineItemCreate] = []
    # Address overrides (if different from contact defaults)
    billing_address: Optional[Dict[str, str]] = None
    shipping_address: Optional[Dict[str, str]] = None
    # Template
    template_id: Optional[str] = None

class EstimateUpdate(BaseModel):
    customer_id: Optional[str] = None
    reference_number: Optional[str] = None
    date: Optional[str] = None
    expiry_date: Optional[str] = None
    salesperson_id: Optional[str] = None
    salesperson_name: Optional[str] = None
    project_id: Optional[str] = None
    subject: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    notes: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    shipping_charge: Optional[float] = None
    adjustment: Optional[float] = None
    adjustment_description: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, str]] = None
    shipping_address: Optional[Dict[str, str]] = None
    template_id: Optional[str] = None
    line_items: Optional[List[Dict[str, Any]]] = None

class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|sent|customer_viewed|accepted|declined|expired|converted|void)$")
    reason: str = ""

class AttachmentResponse(BaseModel):
    attachment_id: str
    estimate_id: str
    filename: str
    file_size: int
    content_type: str
    uploaded_at: str
    uploaded_by: str

class ShareLinkCreate(BaseModel):
    expiry_days: int = 30
    allow_accept: bool = True
    allow_decline: bool = True
    password_protected: bool = False
    password: Optional[str] = None

class ShareLinkResponse(BaseModel):
    share_link_id: str
    estimate_id: str
    share_token: str
    public_url: str
    expires_at: str
    allow_accept: bool
    allow_decline: bool
    password_protected: bool
    created_at: str

class CustomerAction(BaseModel):
    action: str  # accept, decline
    comments: Optional[str] = None

class CustomFieldDefinition(BaseModel):
    field_name: str
    field_type: str = "text"  # text, number, date, dropdown, checkbox
    options: Optional[List[str]] = None  # For dropdown type
    is_required: bool = False
    default_value: Optional[str] = None
    show_in_pdf: bool = True
    show_in_portal: bool = True

class BulkStatusUpdate(BaseModel):
    estimate_ids: List[str]
    new_status: str
    reason: Optional[str] = None

class BulkAction(BaseModel):
    estimate_ids: List[str]
    action: str  # void, delete, mark_sent, mark_expired
    reason: Optional[str] = None

class ImportMapping(BaseModel):
    customer_name: str = "customer_name"
    customer_email: Optional[str] = "customer_email"
    date: str = "date"
    expiry_date: Optional[str] = "expiry_date"
    reference_number: Optional[str] = "reference_number"
    subject: Optional[str] = "subject"
    item_name: str = "item_name"
    quantity: str = "quantity"
    rate: str = "rate"
    tax_percentage: Optional[str] = "tax_percentage"
    notes: Optional[str] = "notes"
    terms: Optional[str] = "terms"

class EstimatePreferences(BaseModel):
    # Automation settings
    auto_convert_on_accept: bool = False
    auto_convert_to: str = "draft_invoice"  # draft_invoice, open_invoice, sales_order
    auto_send_converted: bool = False
    # Quote acceptance settings
    allow_public_accept: bool = True
    allow_public_decline: bool = True
    require_signature: bool = False
    # Field retention on conversion
    retain_customer_notes: bool = True
    retain_terms: bool = True
    retain_address: bool = True
    # Display settings
    hide_zero_value_items: bool = False
    show_discount_column: bool = True
    # Notification settings
    notify_on_view: bool = True
    notify_on_accept: bool = True
    notify_on_decline: bool = True
    # Numbering
    prefix: str = "EST-"
    next_number: int = 1
    padding: int = 5
    # Defaults
    validity_days: int = 30
    default_terms: str = "This estimate is valid for 30 days from the date of issue."
    default_notes: str = ""

# ========================= HELPER FUNCTIONS =========================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

async def get_next_estimate_number() -> str:
    """Generate next estimate number based on settings"""
    settings = await estimate_settings_collection.find_one({"type": "numbering"})
    if not settings:
        settings = {
            "type": "numbering",
            "prefix": "EST-",
            "next_number": 1,
            "padding": 5
        }
        await estimate_settings_collection.insert_one(settings)
    
    number = str(settings["next_number"]).zfill(settings.get("padding", 5))
    next_num = f"{settings.get('prefix', 'EST-')}{number}"
    
    # Increment for next time
    await estimate_settings_collection.update_one(
        {"type": "numbering"},
        {"$inc": {"next_number": 1}}
    )
    
    return next_num

async def get_contact_details(contact_id: str) -> dict:
    """Get contact details for estimate"""
    # Try enhanced contacts first
    contact = await db["contacts_enhanced"].find_one({"contact_id": contact_id}, {"_id": 0})
    if not contact:
        # Fall back to legacy
        contact = await db["contacts"].find_one({"contact_id": contact_id}, {"_id": 0})
    
    if not contact:
        return None
    
    # Get default addresses
    billing_address = await db["addresses"].find_one(
        {"contact_id": contact_id, "address_type": "billing", "is_default": True},
        {"_id": 0}
    )
    if not billing_address:
        billing_address = await db["addresses"].find_one(
            {"contact_id": contact_id, "address_type": "billing"},
            {"_id": 0}
        )
    
    shipping_address = await db["addresses"].find_one(
        {"contact_id": contact_id, "address_type": "shipping", "is_default": True},
        {"_id": 0}
    )
    if not shipping_address:
        shipping_address = await db["addresses"].find_one(
            {"contact_id": contact_id, "address_type": "shipping"},
            {"_id": 0}
        )
    
    return {
        "contact_id": contact_id,
        "name": contact.get("name") or contact.get("display_name", ""),
        "company_name": contact.get("company_name", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "gstin": contact.get("gstin") or contact.get("gst_no", ""),
        "place_of_supply": contact.get("place_of_supply", ""),
        "payment_terms": contact.get("payment_terms", 30),
        "currency_code": contact.get("currency_code", "INR"),
        "billing_address": billing_address,
        "shipping_address": shipping_address
    }

async def get_item_details(item_id: str) -> dict:
    """Get item details for line item"""
    # Try enhanced items first
    item = await db["items_enhanced"].find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        # Fall back to legacy items
        item = await db["items"].find_one({"item_id": item_id}, {"_id": 0})
    
    if not item:
        return None
    
    return {
        "item_id": item_id,
        "name": item.get("name", ""),
        "description": item.get("description", ""),
        "sku": item.get("sku", ""),
        "hsn_code": item.get("hsn_code", ""),
        "unit": item.get("unit", "pcs"),
        "rate": item.get("sales_rate") or item.get("rate", 0),
        "tax_percentage": item.get("tax_percentage", 0),
        "item_type": item.get("item_type", "service"),
        "stock_on_hand": item.get("stock_on_hand") or item.get("total_stock", 0)
    }


async def get_item_price_for_customer(item_id: str, customer_id: str) -> dict:
    """
    Get item price applying customer's assigned price list.
    Returns base rate and adjusted rate based on price list.
    """
    # Get base item details
    item = await db["items_enhanced"].find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        item = await db["items"].find_one({"item_id": item_id}, {"_id": 0})
    
    if not item:
        return None
    
    base_rate = item.get("sales_rate", 0) or item.get("rate", 0)
    
    result = {
        "item_id": item_id,
        "name": item.get("name", ""),
        "description": item.get("description", ""),
        "sku": item.get("sku", ""),
        "hsn_code": item.get("hsn_code", ""),
        "unit": item.get("unit", "pcs"),
        "base_rate": base_rate,
        "rate": base_rate,  # Final rate after price list
        "tax_percentage": item.get("tax_percentage", 0),
        "item_type": item.get("item_type", "service"),
        "stock_on_hand": item.get("stock_on_hand") or item.get("total_stock", 0),
        "price_list_id": None,
        "price_list_name": None,
        "discount_applied": 0,
        "markup_applied": 0
    }
    
    if not customer_id:
        return result
    
    # Get customer's assigned price list
    contact = await db["contacts_enhanced"].find_one({"contact_id": customer_id})
    if not contact:
        contact = await db["contacts"].find_one({"contact_id": customer_id})
    
    if not contact:
        return result
    
    price_list_id = contact.get("sales_price_list_id")
    if not price_list_id:
        return result
    
    # Get price list
    price_list = await db["price_lists"].find_one({"pricelist_id": price_list_id}, {"_id": 0})
    if not price_list:
        return result
    
    result["price_list_id"] = price_list_id
    result["price_list_name"] = price_list.get("name", "")
    
    final_rate = base_rate
    
    # Check for custom price
    custom_price = await db["item_prices"].find_one({
        "item_id": item_id,
        "price_list_id": price_list_id
    })
    
    if custom_price:
        final_rate = custom_price.get("rate", base_rate)
    else:
        # Apply percentage markup/discount
        markup = price_list.get("markup_percentage", 0)
        discount = price_list.get("discount_percentage", 0)
        
        if markup > 0:
            final_rate = base_rate * (1 + markup / 100)
        elif discount > 0:
            final_rate = base_rate * (1 - discount / 100)
        
        # Round off
        round_to = price_list.get("round_off_to", "none")
        if round_to == "nearest_1":
            final_rate = round(final_rate)
        elif round_to == "nearest_5":
            final_rate = round(final_rate / 5) * 5
        elif round_to == "nearest_10":
            final_rate = round(final_rate / 10) * 10
    
    result["rate"] = round(final_rate, 2)
    
    if base_rate > final_rate:
        result["discount_applied"] = round(base_rate - final_rate, 2)
    elif final_rate > base_rate:
        result["markup_applied"] = round(final_rate - base_rate, 2)
    
    return result

def calculate_gst_type(org_state: str, customer_state: str) -> str:
    """Determine if IGST or CGST+SGST applies"""
    if not org_state or not customer_state:
        return "igst"  # Default to IGST if state unknown
    return "cgst_sgst" if org_state == customer_state else "igst"

def calculate_line_item_totals(item: dict, gst_type: str) -> dict:
    """Calculate totals for a line item"""
    quantity = float(item.get("quantity", 1))
    rate = float(item.get("rate", 0))
    
    # Gross amount
    gross = quantity * rate
    
    # Discount
    discount_percent = float(item.get("discount_percent", 0))
    discount_amount = float(item.get("discount_amount", 0))
    
    if discount_percent > 0:
        discount = gross * (discount_percent / 100)
    else:
        discount = discount_amount
    
    # Taxable amount
    taxable = gross - discount
    
    # Tax calculation
    tax_percentage = float(item.get("tax_percentage", 0))
    tax_amount = taxable * (tax_percentage / 100)
    
    # Split tax based on GST type
    if gst_type == "cgst_sgst":
        cgst = tax_amount / 2
        sgst = tax_amount / 2
        igst = 0
    else:
        cgst = 0
        sgst = 0
        igst = tax_amount
    
    # Total
    total = taxable + tax_amount
    
    return {
        "gross_amount": round(gross, 2),
        "discount": round(discount, 2),
        "taxable_amount": round(taxable, 2),
        "tax_amount": round(tax_amount, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "igst": round(igst, 2),
        "total": round(total, 2)
    }

def calculate_estimate_totals(line_items: List[dict], discount_type: str, discount_value: float, 
                              shipping_charge: float, adjustment: float, gst_type: str) -> dict:
    """Calculate estimate totals"""
    subtotal = sum(item.get("taxable_amount", 0) for item in line_items)
    total_tax = sum(item.get("tax_amount", 0) for item in line_items)
    total_cgst = sum(item.get("cgst", 0) for item in line_items)
    total_sgst = sum(item.get("sgst", 0) for item in line_items)
    total_igst = sum(item.get("igst", 0) for item in line_items)
    
    # Apply document-level discount
    if discount_type == "percent":
        doc_discount = subtotal * (discount_value / 100)
    elif discount_type == "amount":
        doc_discount = discount_value
    else:
        doc_discount = 0
    
    # Grand total
    grand_total = subtotal - doc_discount + total_tax + shipping_charge + adjustment
    
    return {
        "subtotal": round(subtotal, 2),
        "total_discount": round(doc_discount + sum(item.get("discount", 0) for item in line_items), 2),
        "document_discount": round(doc_discount, 2),
        "total_tax": round(total_tax, 2),
        "total_cgst": round(total_cgst, 2),
        "total_sgst": round(total_sgst, 2),
        "total_igst": round(total_igst, 2),
        "shipping_charge": round(shipping_charge, 2),
        "adjustment": round(adjustment, 2),
        "grand_total": round(grand_total, 2),
        "gst_type": gst_type
    }

async def add_estimate_history(estimate_id: str, action: str, details: str, user_id: str = ""):
    """Add entry to estimate history"""
    history_entry = {
        "history_id": generate_id("EHIST"),
        "estimate_id": estimate_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await estimate_history_collection.insert_one(history_entry)

def mock_send_email(to_email: str, subject: str, body: str, attachment_name: str = ""):
    """Mock email sending - logs instead of actual send"""
    logger.info(f"[MOCK EMAIL] To: {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Attachment: {attachment_name}")
    logger.info(f"[MOCK EMAIL] Body Preview: {body[:200]}...")
    return True

def generate_share_token() -> str:
    """Generate a secure share token for public links"""
    return hashlib.sha256(f"{uuid.uuid4().hex}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:32]

# PDF Templates System
PDF_TEMPLATES = {
    "standard": {
        "name": "Standard",
        "description": "Clean, professional layout with green branding",
        "primary_color": "#0B462F",
        "secondary_color": "#22EDA9",
        "font_family": "'Segoe UI', Arial, sans-serif",
        "header_style": "modern"
    },
    "professional": {
        "name": "Professional",
        "description": "Formal business style with navy blue accents",
        "primary_color": "#1e3a5f",
        "secondary_color": "#3b82f6",
        "font_family": "'Georgia', serif",
        "header_style": "classic"
    },
    "minimal": {
        "name": "Minimal",
        "description": "Simple, clean design with minimal styling",
        "primary_color": "#374151",
        "secondary_color": "#6b7280",
        "font_family": "'Helvetica', Arial, sans-serif",
        "header_style": "minimal"
    }
}

def generate_pdf_html(estimate: dict, line_items: list, template: str = "standard") -> str:
    """Generate HTML for PDF rendering with template support"""
    tmpl = PDF_TEMPLATES.get(template, PDF_TEMPLATES["standard"])
    primary = tmpl["primary_color"]
    font = tmpl["font_family"]
    
    items_html = ""
    for idx, item in enumerate(line_items, 1):
        items_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{idx}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                <strong>{item.get('name', '')}</strong>
                {f"<br><small style='color: #6b7280;'>{item.get('description', '')}</small>" if item.get('description') else ''}
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center;">{item.get('hsn_code', '-')}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">{item.get('quantity', 1)} {item.get('unit', 'pcs')}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">₹{item.get('rate', 0):,.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">{item.get('tax_percentage', 0)}%</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right; font-weight: 600;">₹{item.get('total', 0):,.2f}</td>
        </tr>
        """
    
    # Custom fields section
    custom_fields_html = ""
    if estimate.get("custom_fields"):
        cf_items = []
        for key, value in estimate.get("custom_fields", {}).items():
            if value:
                cf_items.append(f"<div><strong>{key}:</strong> {value}</div>")
        if cf_items:
            custom_fields_html = f"""
            <div class="info-box" style="margin-top: 20px;">
                <div class="info-label">Additional Information</div>
                {''.join(cf_items)}
            </div>
            """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: {font}; margin: 0; padding: 20px; color: #1f2937; font-size: 12px; }}
            .header {{ display: flex; justify-content: space-between; margin-bottom: 30px; border-bottom: 2px solid {primary}; padding-bottom: 20px; }}
            .company {{ font-size: 24px; font-weight: bold; color: {primary}; }}
            .estimate-title {{ font-size: 28px; color: {primary}; text-align: right; }}
            .estimate-number {{ color: #6b7280; font-size: 14px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }}
            .info-box {{ background: #f9fafb; padding: 15px; border-radius: 8px; }}
            .info-label {{ color: #6b7280; font-size: 11px; text-transform: uppercase; margin-bottom: 5px; }}
            .info-value {{ font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th {{ background: {primary}; color: white; padding: 10px 8px; text-align: left; font-weight: 600; }}
            .totals {{ margin-left: auto; width: 300px; }}
            .totals-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
            .totals-row.grand {{ font-size: 16px; font-weight: bold; color: {primary}; border-top: 2px solid {primary}; border-bottom: none; }}
            .terms {{ margin-top: 30px; padding: 15px; background: #f9fafb; border-radius: 8px; }}
            .terms-title {{ font-weight: 600; margin-bottom: 10px; }}
            .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
            .status-draft {{ background: #e5e7eb; color: #374151; }}
            .status-sent {{ background: #dbeafe; color: #1d4ed8; }}
            .status-accepted {{ background: #d1fae5; color: #065f46; }}
            .footer {{ margin-top: 40px; text-align: center; color: #9ca3af; font-size: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <div class="company">Battwheels OS</div>
                <div style="color: #6b7280; margin-top: 5px;">Your Onsite EV Resolution Partner</div>
            </div>
            <div style="text-align: right;">
                <div class="estimate-title">ESTIMATE</div>
                <div class="estimate-number">{estimate.get('estimate_number', '')}</div>
                <div style="margin-top: 10px;">
                    <span class="status-badge status-{estimate.get('status', 'draft')}">{estimate.get('status', 'draft').upper()}</span>
                </div>
            </div>
        </div>
        
        <div class="info-grid">
            <div class="info-box">
                <div class="info-label">Bill To</div>
                <div class="info-value">{estimate.get('customer_name', '')}</div>
                {f"<div>{estimate.get('customer_email', '')}</div>" if estimate.get('customer_email') else ''}
                {f"<div>GSTIN: {estimate.get('customer_gstin', '')}</div>" if estimate.get('customer_gstin') else ''}
            </div>
            <div class="info-box">
                <div class="info-label">Estimate Details</div>
                <div><strong>Date:</strong> {estimate.get('date', '')}</div>
                <div><strong>Valid Until:</strong> {estimate.get('expiry_date', '')}</div>
                {f"<div><strong>Reference:</strong> {estimate.get('reference_number', '')}</div>" if estimate.get('reference_number') else ''}
                {f"<div><strong>Subject:</strong> {estimate.get('subject', '')}</div>" if estimate.get('subject') else ''}
            </div>
        </div>
        
        {custom_fields_html}
        
        <table>
            <thead>
                <tr>
                    <th style="width: 30px;">#</th>
                    <th>Item & Description</th>
                    <th style="width: 80px; text-align: center;">HSN/SAC</th>
                    <th style="width: 80px; text-align: right;">Qty</th>
                    <th style="width: 90px; text-align: right;">Rate</th>
                    <th style="width: 60px; text-align: right;">Tax</th>
                    <th style="width: 100px; text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <div class="totals">
            <div class="totals-row"><span>Subtotal:</span><span>₹{estimate.get('subtotal', 0):,.2f}</span></div>
            {f'<div class="totals-row"><span>Discount:</span><span>-₹{estimate.get("total_discount", 0):,.2f}</span></div>' if estimate.get('total_discount', 0) > 0 else ''}
            <div class="totals-row"><span>Tax ({estimate.get('gst_type', 'GST').upper()}):</span><span>₹{estimate.get('total_tax', 0):,.2f}</span></div>
            {f'<div class="totals-row"><span>Shipping:</span><span>₹{estimate.get("shipping_charge", 0):,.2f}</span></div>' if estimate.get('shipping_charge', 0) > 0 else ''}
            {f'<div class="totals-row"><span>Adjustment:</span><span>₹{estimate.get("adjustment", 0):,.2f}</span></div>' if estimate.get('adjustment', 0) != 0 else ''}
            <div class="totals-row grand"><span>Grand Total:</span><span>₹{estimate.get('grand_total', 0):,.2f}</span></div>
        </div>
        
        {f'<div class="terms"><div class="terms-title">Terms & Conditions</div><div>{estimate.get("terms_and_conditions", "")}</div></div>' if estimate.get('terms_and_conditions') else ''}
        {f'<div class="terms"><div class="terms-title">Notes</div><div>{estimate.get("notes", "")}</div></div>' if estimate.get('notes') else ''}
        
        <div class="footer">
            <p>Generated by Battwheels OS • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC</p>
        </div>
    </body>
    </html>
    """
    return html

async def get_estimate_preferences() -> dict:
    """Get estimate preferences with defaults"""
    prefs = await estimate_settings_collection.find_one({"type": "preferences"}, {"_id": 0})
    if not prefs:
        prefs = EstimatePreferences().dict()
        prefs["type"] = "preferences"
    return prefs

async def auto_convert_estimate(estimate_id: str, preferences: dict):
    """Auto-convert accepted estimate based on preferences"""
    if not preferences.get("auto_convert_on_accept", False):
        return None
    
    convert_to = preferences.get("auto_convert_to", "draft_invoice")
    
    if convert_to in ["draft_invoice", "open_invoice"]:
        # Import the conversion function
        result = await convert_to_invoice_internal(estimate_id, auto_send=preferences.get("auto_send_converted", False))
        return result
    elif convert_to == "sales_order":
        result = await convert_to_sales_order_internal(estimate_id)
        return result
    
    return None

async def convert_to_invoice_internal(estimate_id: str, auto_send: bool = False):
    """Internal conversion to invoice"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        return None
    
    line_items = await estimate_items_collection.find({"estimate_id": estimate_id}, {"_id": 0}).to_list(100)
    
    # Generate invoice number
    inv_settings = await db["invoice_settings"].find_one({"type": "numbering"})
    if not inv_settings:
        inv_settings = {"prefix": "INV-", "next_number": 1, "padding": 5}
        await db["invoice_settings"].insert_one({**inv_settings, "type": "numbering"})
    
    invoice_number = f"{inv_settings.get('prefix', 'INV-')}{str(inv_settings.get('next_number', 1)).zfill(inv_settings.get('padding', 5))}"
    await db["invoice_settings"].update_one({"type": "numbering"}, {"$inc": {"next_number": 1}})
    
    invoice_id = generate_id("INV")
    today = datetime.now(timezone.utc).date().isoformat()
    
    invoice_doc = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "customer_id": estimate["customer_id"],
        "customer_name": estimate.get("customer_name", ""),
        "customer_email": estimate.get("customer_email", ""),
        "customer_gstin": estimate.get("customer_gstin", ""),
        "place_of_supply": estimate.get("place_of_supply", ""),
        "date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat(),
        "status": "draft",
        "reference_number": estimate.get("reference_number", ""),
        "estimate_id": estimate_id,
        "estimate_number": estimate.get("estimate_number", ""),
        "salesperson_id": estimate.get("salesperson_id"),
        "salesperson_name": estimate.get("salesperson_name", ""),
        "project_id": estimate.get("project_id"),
        "subject": estimate.get("subject", ""),
        "billing_address": estimate.get("billing_address"),
        "shipping_address": estimate.get("shipping_address"),
        "line_items_count": estimate.get("line_items_count", 0),
        "discount_type": estimate.get("discount_type", "none"),
        "discount_value": estimate.get("discount_value", 0),
        "shipping_charge": estimate.get("shipping_charge", 0),
        "adjustment": estimate.get("adjustment", 0),
        "adjustment_description": estimate.get("adjustment_description", ""),
        "subtotal": estimate.get("subtotal", 0),
        "total_discount": estimate.get("total_discount", 0),
        "total_tax": estimate.get("total_tax", 0),
        "total_cgst": estimate.get("total_cgst", 0),
        "total_sgst": estimate.get("total_sgst", 0),
        "total_igst": estimate.get("total_igst", 0),
        "grand_total": estimate.get("grand_total", 0),
        "total": estimate.get("grand_total", 0),
        "balance_due": estimate.get("grand_total", 0),
        "amount_paid": 0,
        "gst_type": estimate.get("gst_type", "igst"),
        "terms_and_conditions": estimate.get("terms_and_conditions", ""),
        "notes": estimate.get("notes", ""),
        "custom_fields": estimate.get("custom_fields", {}),
        "auto_converted": True,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db["invoices"].insert_one(invoice_doc)
    
    for item in line_items:
        item["invoice_id"] = invoice_id
        item["line_item_id"] = generate_id("LI")
        item.pop("estimate_id", None)
        await db["invoice_line_items"].insert_one(item)
    
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "converted",
            "converted_to": f"invoice:{invoice_id}",
            "converted_date": today,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_estimate_history(estimate_id, "auto_converted", f"Auto-converted to Invoice {invoice_number}")
    
    return {"invoice_id": invoice_id, "invoice_number": invoice_number}

async def convert_to_sales_order_internal(estimate_id: str):
    """Internal conversion to sales order"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        return None
    
    line_items = await estimate_items_collection.find({"estimate_id": estimate_id}, {"_id": 0}).to_list(100)
    
    so_settings = await db["sales_order_settings"].find_one({"type": "numbering"})
    if not so_settings:
        so_settings = {"prefix": "SO-", "next_number": 1, "padding": 5}
        await db["sales_order_settings"].insert_one({**so_settings, "type": "numbering"})
    
    so_number = f"{so_settings.get('prefix', 'SO-')}{str(so_settings.get('next_number', 1)).zfill(so_settings.get('padding', 5))}"
    await db["sales_order_settings"].update_one({"type": "numbering"}, {"$inc": {"next_number": 1}})
    
    so_id = generate_id("SO")
    today = datetime.now(timezone.utc).date().isoformat()
    
    so_doc = {
        "salesorder_id": so_id,
        "salesorder_number": so_number,
        "customer_id": estimate["customer_id"],
        "customer_name": estimate.get("customer_name", ""),
        "customer_email": estimate.get("customer_email", ""),
        "customer_gstin": estimate.get("customer_gstin", ""),
        "place_of_supply": estimate.get("place_of_supply", ""),
        "date": today,
        "expected_shipment_date": (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat(),
        "status": "draft",
        "fulfillment_status": "unfulfilled",
        "reference_number": estimate.get("reference_number", ""),
        "estimate_id": estimate_id,
        "estimate_number": estimate.get("estimate_number", ""),
        "salesperson_id": estimate.get("salesperson_id"),
        "salesperson_name": estimate.get("salesperson_name", ""),
        "project_id": estimate.get("project_id"),
        "billing_address": estimate.get("billing_address"),
        "shipping_address": estimate.get("shipping_address"),
        "line_items_count": estimate.get("line_items_count", 0),
        "discount_type": estimate.get("discount_type", "none"),
        "discount_value": estimate.get("discount_value", 0),
        "shipping_charge": estimate.get("shipping_charge", 0),
        "adjustment": estimate.get("adjustment", 0),
        "subtotal": estimate.get("subtotal", 0),
        "total_discount": estimate.get("total_discount", 0),
        "total_tax": estimate.get("total_tax", 0),
        "grand_total": estimate.get("grand_total", 0),
        "total": estimate.get("grand_total", 0),
        "gst_type": estimate.get("gst_type", "igst"),
        "terms_and_conditions": estimate.get("terms_and_conditions", ""),
        "notes": estimate.get("notes", ""),
        "custom_fields": estimate.get("custom_fields", {}),
        "auto_converted": True,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db["sales_orders"].insert_one(so_doc)
    
    for item in line_items:
        item["salesorder_id"] = so_id
        item["line_item_id"] = generate_id("LI")
        item["quantity_ordered"] = item.get("quantity", 0)
        item["quantity_fulfilled"] = 0
        item.pop("estimate_id", None)
        await db["salesorder_line_items"].insert_one(item)
    
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "converted",
            "converted_to": f"salesorder:{so_id}",
            "converted_date": today,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_estimate_history(estimate_id, "auto_converted", f"Auto-converted to Sales Order {so_number}")
    
    return {"salesorder_id": so_id, "salesorder_number": so_number}

# ========================= SETTINGS ENDPOINTS =========================

@router.get("/settings")
async def get_estimate_settings():
    """Get estimate module settings"""
    numbering = await estimate_settings_collection.find_one({"type": "numbering"}, {"_id": 0})
    defaults = await estimate_settings_collection.find_one({"type": "defaults"}, {"_id": 0})
    preferences = await estimate_settings_collection.find_one({"type": "preferences"}, {"_id": 0})
    
    if not numbering:
        numbering = {"type": "numbering", "prefix": "EST-", "next_number": 1, "padding": 5}
    if not defaults:
        defaults = {
            "type": "defaults",
            "validity_days": 30,
            "terms_and_conditions": "This estimate is valid for 30 days from the date of issue.",
            "notes": ""
        }
    if not preferences:
        preferences = EstimatePreferences().dict()
        preferences["type"] = "preferences"
    
    return {"code": 0, "settings": {"numbering": numbering, "defaults": defaults, "preferences": preferences}}

@router.put("/settings")
async def update_estimate_settings(settings: dict):
    """Update estimate module settings"""
    if "numbering" in settings:
        await estimate_settings_collection.update_one(
            {"type": "numbering"},
            {"$set": settings["numbering"]},
            upsert=True
        )
    if "defaults" in settings:
        await estimate_settings_collection.update_one(
            {"type": "defaults"},
            {"$set": settings["defaults"]},
            upsert=True
        )
    if "preferences" in settings:
        await estimate_settings_collection.update_one(
            {"type": "preferences"},
            {"$set": settings["preferences"]},
            upsert=True
        )
    return {"code": 0, "message": "Settings updated"}

@router.get("/preferences")
async def get_preferences():
    """Get estimate preferences for automation"""
    prefs = await get_estimate_preferences()
    return {"code": 0, "preferences": prefs}

@router.put("/preferences")
async def update_preferences(preferences: EstimatePreferences):
    """Update estimate preferences"""
    prefs_dict = preferences.dict()
    prefs_dict["type"] = "preferences"
    await estimate_settings_collection.update_one(
        {"type": "preferences"},
        {"$set": prefs_dict},
        upsert=True
    )
    return {"code": 0, "message": "Preferences updated", "preferences": prefs_dict}
    return {"code": 0, "message": "Settings updated"}

# ========================= ESTIMATE CRUD ENDPOINTS =========================

@router.post("/")
async def create_estimate(estimate: EstimateCreate, background_tasks: BackgroundTasks):
    """Create a new estimate/quote"""
    # Validate customer
    customer = await get_contact_details(estimate.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Generate estimate number if not provided
    estimate_number = estimate.estimate_number or await get_next_estimate_number()
    
    # Check for duplicate estimate number
    existing = await estimates_collection.find_one({"estimate_number": estimate_number})
    if existing:
        raise HTTPException(status_code=400, detail=f"Estimate number {estimate_number} already exists")
    
    # Determine GST type based on place of supply
    customer_state = customer.get("place_of_supply", "")
    if not customer_state and customer.get("gstin"):
        gstin = customer.get("gstin", "")
        if len(gstin) >= 2:
            customer_state = GSTIN_STATE_MAP.get(gstin[:2], "")
    
    gst_type = calculate_gst_type(ORG_STATE_CODE, customer_state)
    
    # Set dates
    today = datetime.now(timezone.utc).date().isoformat()
    estimate_date = estimate.date or today
    
    defaults = await estimate_settings_collection.find_one({"type": "defaults"})
    validity_days = defaults.get("validity_days", 30) if defaults else 30
    
    if estimate.expiry_date:
        expiry_date = estimate.expiry_date
    else:
        expiry_date = (datetime.fromisoformat(estimate_date) + timedelta(days=validity_days)).date().isoformat()
    
    estimate_id = generate_id("EST")
    
    # Get customer's price list info for the estimate header
    customer_price_list = None
    customer_price_list_id = None
    contact_for_pricing = await db["contacts_enhanced"].find_one({"contact_id": estimate.customer_id})
    if not contact_for_pricing:
        contact_for_pricing = await db["contacts"].find_one({"contact_id": estimate.customer_id})
    if contact_for_pricing:
        customer_price_list_id = contact_for_pricing.get("sales_price_list_id")
        if customer_price_list_id:
            customer_price_list = await db["price_lists"].find_one({"pricelist_id": customer_price_list_id}, {"_id": 0})
    
    # Process line items
    processed_items = []
    for idx, item in enumerate(estimate.line_items):
        item_dict = item.dict()
        
        # If item_id provided, fetch item details WITH price list applied
        if item.item_id:
            # Use new pricing function that applies customer's price list
            item_details = await get_item_price_for_customer(item.item_id, estimate.customer_id)
            if item_details:
                # Use item details as defaults, but allow overrides
                item_dict["name"] = item.name or item_details.get("name", "")
                item_dict["description"] = item.description or item_details.get("description", "")
                item_dict["hsn_code"] = item.hsn_code or item_details.get("hsn_code", "")
                item_dict["unit"] = item.unit or item_details.get("unit", "pcs")
                # Apply price list rate if user hasn't overridden
                if item.rate == 0:
                    item_dict["rate"] = item_details.get("rate", 0)
                    item_dict["base_rate"] = item_details.get("base_rate", 0)
                    item_dict["price_list_applied"] = item_details.get("price_list_name")
                    item_dict["discount_from_pricelist"] = item_details.get("discount_applied", 0)
                    item_dict["markup_from_pricelist"] = item_details.get("markup_applied", 0)
                if item.tax_percentage == 0:
                    item_dict["tax_percentage"] = item_details.get("tax_percentage", 0)
        
        # Calculate line item totals
        totals = calculate_line_item_totals(item_dict, gst_type)
        item_dict.update(totals)
        item_dict["line_item_id"] = generate_id("LI")
        item_dict["estimate_id"] = estimate_id
        item_dict["line_number"] = idx + 1
        
        processed_items.append(item_dict)
    
    # Calculate estimate totals
    totals = calculate_estimate_totals(
        processed_items,
        estimate.discount_type,
        estimate.discount_value,
        estimate.shipping_charge,
        estimate.adjustment,
        gst_type
    )
    
    # Use addresses from request or customer defaults
    billing_address = estimate.billing_address or customer.get("billing_address")
    shipping_address = estimate.shipping_address or customer.get("shipping_address")
    
    # Build estimate document
    estimate_doc = {
        "estimate_id": estimate_id,
        "estimate_number": estimate_number,
        "reference_number": estimate.reference_number,
        "customer_id": estimate.customer_id,
        "customer_name": customer.get("name", ""),
        "customer_email": customer.get("email", ""),
        "customer_gstin": customer.get("gstin", ""),
        "place_of_supply": customer_state,
        "price_list_id": customer_price_list_id,
        "price_list_name": customer_price_list.get("name") if customer_price_list else None,
        "date": estimate_date,
        "expiry_date": expiry_date,
        "status": "draft",
        "salesperson_id": estimate.salesperson_id,
        "salesperson_name": estimate.salesperson_name,
        "project_id": estimate.project_id,
        "subject": estimate.subject,
        "billing_address": billing_address,
        "shipping_address": shipping_address,
        "line_items_count": len(processed_items),
        "discount_type": estimate.discount_type,
        "discount_value": estimate.discount_value,
        "shipping_charge": estimate.shipping_charge,
        "adjustment": estimate.adjustment,
        "adjustment_description": estimate.adjustment_description,
        **totals,
        "terms_and_conditions": estimate.terms_and_conditions or (defaults.get("terms_and_conditions", "") if defaults else ""),
        "notes": estimate.notes,
        "custom_fields": estimate.custom_fields,
        "template_id": estimate.template_id,
        "converted_to": None,  # Will be set when converted to SO/Invoice
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Insert estimate and line items
    await estimates_collection.insert_one(estimate_doc)
    if processed_items:
        await estimate_items_collection.insert_many(processed_items)
    
    # Add history entry
    await add_estimate_history(estimate_id, "created", f"Estimate {estimate_number} created")
    
    # Remove _id from response
    estimate_doc.pop("_id", None)
    estimate_doc["line_items"] = [{k: v for k, v in item.items() if k != "_id"} for item in processed_items]
    
    return {"code": 0, "message": "Estimate created", "estimate": estimate_doc}

@router.get("/")
async def list_estimates(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    expiry_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List estimates with filters and standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    query = {}

    if status:
        query["status"] = status

    if customer_id:
        query["customer_id"] = customer_id

    if search:
        query["$or"] = [
            {"estimate_number": {"$regex": search, "$options": "i"}},
            {"reference_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"subject": {"$regex": search, "$options": "i"}}
        ]

    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}

    today = datetime.now(timezone.utc).date().isoformat()
    if expiry_status == "expired":
        query["expiry_date"] = {"$lt": today}
        query["status"] = {"$nin": ["accepted", "declined", "converted", "void"]}
    elif expiry_status == "active":
        query["expiry_date"] = {"$gte": today}

    total = await estimates_collection.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    estimates = await estimates_collection.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": estimates,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/summary")
async def get_estimates_summary():
    """Get estimates summary statistics"""
    today = datetime.now(timezone.utc).date().isoformat()
    
    total = await estimates_collection.count_documents({})
    draft = await estimates_collection.count_documents({"status": "draft"})
    sent = await estimates_collection.count_documents({"status": "sent"})
    customer_viewed = await estimates_collection.count_documents({"status": "customer_viewed"})
    accepted = await estimates_collection.count_documents({"status": "accepted"})
    declined = await estimates_collection.count_documents({"status": "declined"})
    converted = await estimates_collection.count_documents({"status": "converted"})
    expired = await estimates_collection.count_documents({
        "status": {"$nin": ["accepted", "declined", "converted", "void"]},
        "expiry_date": {"$lt": today}
    })
    
    # Calculate totals
    pipeline = [
        {"$match": {"status": {"$nin": ["void"]}}},
        {"$group": {
            "_id": None,
            "total_value": {"$sum": "$grand_total"},
            "accepted_value": {"$sum": {"$cond": [{"$eq": ["$status", "accepted"]}, "$grand_total", 0]}},
            "pending_value": {"$sum": {"$cond": [{"$in": ["$status", ["draft", "sent", "customer_viewed"]]}, "$grand_total", 0]}}
        }}
    ]
    
    stats = await estimates_collection.aggregate(pipeline).to_list(1)
    values = stats[0] if stats else {"total_value": 0, "accepted_value": 0, "pending_value": 0}
    
    return {
        "code": 0,
        "summary": {
            "total": total,
            "by_status": {
                "draft": draft,
                "sent": sent,
                "customer_viewed": customer_viewed,
                "accepted": accepted,
                "declined": declined,
                "converted": converted,
                "expired": expired
            },
            "total_value": round(values.get("total_value", 0), 2),
            "accepted_value": round(values.get("accepted_value", 0), 2),
            "pending_value": round(values.get("pending_value", 0), 2)
        }
    }

# ========================= REPORTING ENDPOINTS (Before dynamic routes) =========================

@router.get("/reports/by-status")
async def report_by_status(date_from: str = "", date_to: str = ""):
    """Report: Estimates by status"""
    query = {}
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_value": {"$sum": "$grand_total"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = await estimates_collection.aggregate(pipeline).to_list(10)
    
    return {
        "code": 0,
        "report": [{"status": r["_id"], "count": r["count"], "total_value": round(r["total_value"], 2)} for r in results]
    }

@router.get("/reports/by-customer")
async def report_by_customer(limit: int = 20):
    """Report: Top customers by estimate value"""
    pipeline = [
        {"$match": {"status": {"$nin": ["void"]}}},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "count": {"$sum": 1},
            "total_value": {"$sum": "$grand_total"},
            "accepted_count": {"$sum": {"$cond": [{"$eq": ["$status", "accepted"]}, 1, 0]}},
            "converted_count": {"$sum": {"$cond": [{"$eq": ["$status", "converted"]}, 1, 0]}}
        }},
        {"$sort": {"total_value": -1}},
        {"$limit": limit}
    ]
    
    results = await estimates_collection.aggregate(pipeline).to_list(limit)
    
    for r in results:
        r["customer_id"] = r.pop("_id")
        r["total_value"] = round(r["total_value"], 2)
        r["conversion_rate"] = round((r["converted_count"] / r["count"]) * 100, 1) if r["count"] > 0 else 0
    
    return {"code": 0, "report": results}

@router.get("/reports/conversion-funnel")
async def report_conversion_funnel():
    """Report: Estimate conversion funnel"""
    total = await estimates_collection.count_documents({"status": {"$ne": "void"}})
    sent = await estimates_collection.count_documents({"status": {"$in": ["sent", "accepted", "declined", "expired", "converted"]}})
    accepted = await estimates_collection.count_documents({"status": {"$in": ["accepted", "converted"]}})
    converted = await estimates_collection.count_documents({"status": "converted"})
    
    return {
        "code": 0,
        "funnel": {
            "total_created": total,
            "sent_to_customer": sent,
            "accepted": accepted,
            "converted": converted,
            "send_rate": round((sent / total) * 100, 1) if total > 0 else 0,
            "acceptance_rate": round((accepted / sent) * 100, 1) if sent > 0 else 0,
            "conversion_rate": round((converted / accepted) * 100, 1) if accepted > 0 else 0,
            "overall_conversion": round((converted / total) * 100, 1) if total > 0 else 0
        }
    }

# ========================= PDF TEMPLATES ENDPOINTS (Static routes before dynamic) =========================

@router.get("/templates")
async def list_pdf_templates():
    """List available PDF templates"""
    templates = [
        {"id": key, **value}
        for key, value in PDF_TEMPLATES.items()
    ]
    return {"code": 0, "templates": templates}

# ========================= PRICING INTEGRATION ENDPOINTS =========================

@router.get("/item-pricing/{item_id}")
async def get_item_pricing_for_estimate(item_id: str, customer_id: str = ""):
    """
    Get item pricing for a customer when creating/editing estimates.
    Applies the customer's assigned price list automatically.
    
    This endpoint allows the frontend to display the correct price
    when an item is selected, based on the selected customer.
    """
    item_details = await get_item_price_for_customer(item_id, customer_id)
    if not item_details:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"code": 0, "item": item_details}


@router.get("/customer-pricing/{customer_id}")
async def get_customer_pricing_info(customer_id: str):
    """
    Get pricing info for a customer - which price list is assigned.
    Useful for displaying in the UI when a customer is selected.
    """
    contact = await db["contacts_enhanced"].find_one({"contact_id": customer_id})
    if not contact:
        contact = await db["contacts"].find_one({"contact_id": customer_id})
    
    if not contact:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    result = {
        "customer_id": customer_id,
        "customer_name": contact.get("company_name") or contact.get("name") or contact.get("display_name", ""),
        "sales_price_list": None
    }
    
    price_list_id = contact.get("sales_price_list_id")
    if price_list_id:
        pl = await db["price_lists"].find_one({"pricelist_id": price_list_id}, {"_id": 0})
        if pl:
            result["sales_price_list"] = {
                "pricelist_id": price_list_id,
                "name": pl.get("name", ""),
                "discount_percentage": pl.get("discount_percentage", 0),
                "markup_percentage": pl.get("markup_percentage", 0),
                "description": pl.get("description", "")
            }
    
    return {"code": 0, "pricing": result}


# ========================= CUSTOM FIELDS ENDPOINTS =========================

@router.get("/custom-fields")
async def list_custom_fields():
    """List all custom field definitions for estimates"""
    fields = await estimate_settings_collection.find_one({"type": "custom_fields"}, {"_id": 0})
    return {"code": 0, "custom_fields": fields.get("fields", []) if fields else []}

@router.post("/custom-fields")
async def add_custom_field(field: CustomFieldDefinition):
    """Add a new custom field definition"""
    existing = await estimate_settings_collection.find_one({"type": "custom_fields"})
    
    if existing:
        for f in existing.get("fields", []):
            if f["field_name"].lower() == field.field_name.lower():
                raise HTTPException(status_code=400, detail="Field with this name already exists")
        
        await estimate_settings_collection.update_one(
            {"type": "custom_fields"},
            {"$push": {"fields": field.dict()}}
        )
    else:
        await estimate_settings_collection.insert_one({
            "type": "custom_fields",
            "fields": [field.dict()]
        })
    
    return {"code": 0, "message": f"Custom field '{field.field_name}' added"}

@router.put("/custom-fields/{field_name}")
async def update_custom_field(field_name: str, field: CustomFieldDefinition):
    """Update a custom field definition"""
    existing = await estimate_settings_collection.find_one({"type": "custom_fields"})
    if not existing:
        raise HTTPException(status_code=404, detail="No custom fields defined")
    
    fields = existing.get("fields", [])
    field_found = False
    for i, f in enumerate(fields):
        if f["field_name"].lower() == field_name.lower():
            fields[i] = field.dict()
            field_found = True
            break
    
    if not field_found:
        raise HTTPException(status_code=404, detail="Custom field not found")
    
    await estimate_settings_collection.update_one(
        {"type": "custom_fields"},
        {"$set": {"fields": fields}}
    )
    
    return {"code": 0, "message": f"Custom field '{field_name}' updated"}

@router.delete("/custom-fields/{field_name}")
async def delete_custom_field(field_name: str):
    """Delete a custom field definition"""
    result = await estimate_settings_collection.update_one(
        {"type": "custom_fields"},
        {"$pull": {"fields": {"field_name": {"$regex": f"^{field_name}$", "$options": "i"}}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Custom field not found")
    
    return {"code": 0, "message": f"Custom field '{field_name}' deleted"}

# ========================= BULK ACTIONS ENDPOINTS =========================

@router.post("/bulk/status")
async def bulk_update_status(bulk_update: BulkStatusUpdate):
    """Update status for multiple estimates"""
    valid_statuses = ["draft", "sent", "customer_viewed", "accepted", "declined", "expired", "void"]
    if bulk_update.new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {valid_statuses}")
    
    estimates = await estimates_collection.find(
        {"estimate_id": {"$in": bulk_update.estimate_ids}}
    ).to_list(1000)
    
    updated_count = 0
    errors = []
    
    for est in estimates:
        current_status = est.get("status")
        valid_transitions = {
            "draft": ["sent", "void"],
            "sent": ["customer_viewed", "accepted", "declined", "expired", "void"],
            "customer_viewed": ["accepted", "declined", "expired", "void"],
            "accepted": ["converted", "void"],
            "declined": ["sent", "void"],
            "expired": ["sent", "void"],
            "converted": [],
            "void": []
        }
        
        if bulk_update.new_status in valid_transitions.get(current_status, []):
            await estimates_collection.update_one(
                {"estimate_id": est["estimate_id"]},
                {"$set": {
                    "status": bulk_update.new_status,
                    "updated_time": datetime.now(timezone.utc).isoformat()
                }}
            )
            await add_estimate_history(
                est["estimate_id"],
                "bulk_status_update",
                f"Status changed to '{bulk_update.new_status}' via bulk action"
            )
            updated_count += 1
        else:
            errors.append({
                "estimate_id": est["estimate_id"],
                "error": f"Cannot transition from '{current_status}' to '{bulk_update.new_status}'"
            })
    
    return {
        "code": 0,
        "message": f"Updated {updated_count} estimates",
        "updated": updated_count,
        "errors": errors
    }

@router.post("/bulk/action")
async def bulk_action(action: BulkAction):
    """Perform bulk action on multiple estimates"""
    valid_actions = ["void", "delete", "mark_sent", "mark_expired"]
    if action.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Valid: {valid_actions}")
    
    updated_count = 0
    deleted_count = 0
    errors = []
    
    for estimate_id in action.estimate_ids:
        try:
            if action.action == "void":
                result = await estimates_collection.update_one(
                    {"estimate_id": estimate_id, "status": {"$nin": ["converted", "void"]}},
                    {"$set": {"status": "void", "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                if result.modified_count > 0:
                    await add_estimate_history(estimate_id, "voided", f"Voided via bulk action. Reason: {action.reason or 'N/A'}")
                    updated_count += 1
                else:
                    errors.append({"estimate_id": estimate_id, "error": "Cannot void (already converted or voided)"})
                    
            elif action.action == "delete":
                est = await estimates_collection.find_one({"estimate_id": estimate_id})
                if est and est.get("status") == "draft":
                    await estimates_collection.delete_one({"estimate_id": estimate_id})
                    await estimate_items_collection.delete_many({"estimate_id": estimate_id})
                    await estimate_attachments_collection.delete_many({"estimate_id": estimate_id})
                    deleted_count += 1
                else:
                    errors.append({"estimate_id": estimate_id, "error": "Can only delete draft estimates"})
                    
            elif action.action == "mark_sent":
                result = await estimates_collection.update_one(
                    {"estimate_id": estimate_id, "status": "draft"},
                    {"$set": {"status": "sent", "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                if result.modified_count > 0:
                    await add_estimate_history(estimate_id, "marked_sent", "Marked as sent via bulk action")
                    updated_count += 1
                else:
                    errors.append({"estimate_id": estimate_id, "error": "Can only mark draft estimates as sent"})
                    
            elif action.action == "mark_expired":
                result = await estimates_collection.update_one(
                    {"estimate_id": estimate_id, "status": {"$in": ["sent", "customer_viewed"]}},
                    {"$set": {"status": "expired", "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                if result.modified_count > 0:
                    await add_estimate_history(estimate_id, "expired", "Marked as expired via bulk action")
                    updated_count += 1
                else:
                    errors.append({"estimate_id": estimate_id, "error": "Can only expire sent or viewed estimates"})
                    
        except Exception as e:
            errors.append({"estimate_id": estimate_id, "error": str(e)})
    
    return {
        "code": 0,
        "message": f"Action '{action.action}' completed",
        "updated": updated_count,
        "deleted": deleted_count,
        "errors": errors
    }

# ========================= IMPORT/EXPORT ENDPOINTS =========================

@router.get("/export")
async def export_estimates(
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    format: str = "csv"
):
    """Export estimates to CSV or JSON"""
    query = {}
    if status:
        query["status"] = status
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    estimates = await estimates_collection.find(query, {"_id": 0}).to_list(10000)
    
    if format == "json":
        return JSONResponse({
            "code": 0,
            "count": len(estimates),
            "estimates": estimates
        })
    
    output = io.StringIO()
    
    if estimates:
        all_keys = set()
        for est in estimates:
            all_keys.update(est.keys())
            if "custom_fields" in est and est["custom_fields"]:
                for cf_key in est["custom_fields"].keys():
                    all_keys.add(f"cf_{cf_key}")
        
        headers = sorted([k for k in all_keys if k not in ["line_items", "custom_fields", "history", "billing_address", "shipping_address"]])
        
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        
        for est in estimates:
            row = {k: est.get(k, "") for k in headers}
            if "custom_fields" in est and est["custom_fields"]:
                for cf_key, cf_val in est["custom_fields"].items():
                    row[f"cf_{cf_key}"] = cf_val
            writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=estimates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.post("/import")
async def import_estimates(
    file: UploadFile = File(...),
    skip_errors: bool = True
):
    """Import estimates from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported = 0
    errors = []
    estimates_data = {}
    
    for row_num, row in enumerate(reader, start=2):
        try:
            group_key = row.get('reference_number') or f"{row.get('customer_name', '')}_{row.get('date', '')}"
            
            if group_key not in estimates_data:
                customer_name = row.get('customer_name', '').strip()
                customer = await db["contacts_enhanced"].find_one(
                    {"name": {"$regex": f"^{customer_name}$", "$options": "i"}, "contact_type": "customer"}
                )
                
                if not customer:
                    if not skip_errors:
                        errors.append({"row": row_num, "error": f"Customer '{customer_name}' not found"})
                        continue
                    customer_id = f"IMPORT-{uuid.uuid4().hex[:8]}"
                else:
                    customer_id = customer.get("contact_id")
                
                estimate_number = await get_next_estimate_number()
                estimate_id = generate_id("EST")
                today = datetime.now(timezone.utc).date().isoformat()
                
                estimates_data[group_key] = {
                    "estimate_id": estimate_id,
                    "estimate_number": estimate_number,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "customer_email": row.get('customer_email', ''),
                    "date": row.get('date', today),
                    "expiry_date": row.get('expiry_date', (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()),
                    "reference_number": row.get('reference_number', ''),
                    "subject": row.get('subject', ''),
                    "status": "draft",
                    "notes": row.get('notes', ''),
                    "terms_and_conditions": row.get('terms', ''),
                    "line_items": [],
                    "created_time": datetime.now(timezone.utc).isoformat(),
                    "updated_time": datetime.now(timezone.utc).isoformat(),
                    "imported": True
                }
            
            if row.get('item_name'):
                quantity = float(row.get('quantity', 1) or 1)
                rate = float(row.get('rate', 0) or 0)
                tax_pct = float(row.get('tax_percentage', 18) or 18)
                
                gross = quantity * rate
                tax_amount = gross * (tax_pct / 100)
                total = gross + tax_amount
                
                line_item = {
                    "line_item_id": generate_id("LI"),
                    "estimate_id": estimates_data[group_key]["estimate_id"],
                    "name": row.get('item_name', ''),
                    "description": row.get('item_description', ''),
                    "quantity": quantity,
                    "unit": row.get('unit', 'pcs'),
                    "rate": rate,
                    "tax_percentage": tax_pct,
                    "hsn_code": row.get('hsn_code', ''),
                    "gross_amount": gross,
                    "tax_amount": tax_amount,
                    "total": total,
                    "line_number": len(estimates_data[group_key]["line_items"]) + 1
                }
                estimates_data[group_key]["line_items"].append(line_item)
                
        except Exception as e:
            if skip_errors:
                errors.append({"row": row_num, "error": str(e)})
            else:
                raise HTTPException(status_code=400, detail=f"Error on row {row_num}: {str(e)}")
    
    for group_key, est_data in estimates_data.items():
        try:
            subtotal = sum(item["gross_amount"] for item in est_data["line_items"])
            total_tax = sum(item["tax_amount"] for item in est_data["line_items"])
            grand_total = subtotal + total_tax
            
            est_data["subtotal"] = subtotal
            est_data["total_tax"] = total_tax
            est_data["grand_total"] = grand_total
            est_data["line_items_count"] = len(est_data["line_items"])
            
            line_items = est_data.pop("line_items")
            
            await estimates_collection.insert_one(est_data)
            
            for item in line_items:
                await estimate_items_collection.insert_one(item)
            
            await add_estimate_history(est_data["estimate_id"], "imported", f"Imported from CSV file: {file.filename}")
            imported += 1
            
        except Exception as e:
            errors.append({"group": group_key, "error": str(e)})
    
    return {
        "code": 0,
        "message": f"Import completed. {imported} estimates created.",
        "imported": imported,
        "errors": errors
    }

@router.get("/import/template")
async def get_import_template():
    """Download CSV template for importing estimates"""
    headers = [
        "customer_name", "customer_email", "date", "expiry_date", "reference_number",
        "subject", "item_name", "item_description", "quantity", "unit", "rate",
        "tax_percentage", "hsn_code", "notes", "terms"
    ]
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow([
        "ABC Company", "contact@abc.com", "2026-02-18", "2026-03-20", "REF-001",
        "Website Development", "Web Design", "Landing page design", "1", "hrs", "5000",
        "18", "998314", "Thank you for your business", "Payment due within 30 days"
    ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=estimates_import_template.csv"
        }
    )

# ========================= DYNAMIC ESTIMATE ROUTES =========================

@router.get("/{estimate_id}")
async def get_estimate(estimate_id: str):
    """Get estimate details with line items and history"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Get line items
    line_items = await estimate_items_collection.find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).sort("line_number", 1).to_list(100)
    estimate["line_items"] = line_items
    
    # Get customer details
    customer = await get_contact_details(estimate["customer_id"])
    estimate["customer_details"] = customer
    
    # Get history
    history = await estimate_history_collection.find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    estimate["history"] = history
    
    # Check if expired
    today = datetime.now(timezone.utc).date().isoformat()
    estimate["is_expired"] = estimate.get("expiry_date", "") < today and estimate.get("status") not in ["accepted", "declined", "converted", "void"]
    
    return {"code": 0, "estimate": estimate}

@router.put("/{estimate_id}")
async def update_estimate(estimate_id: str, estimate: EstimateUpdate):
    """Update an estimate (available until converted to invoice)"""
    existing = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Allow editing for all statuses except converted and void
    if existing.get("status") in ["converted", "void"]:
        raise HTTPException(status_code=400, detail="Converted or void estimates cannot be edited")
    
    update_data = {k: v for k, v in estimate.dict().items() if v is not None}
    
    # If customer changed, recalculate GST type
    if "customer_id" in update_data:
        customer = await get_contact_details(update_data["customer_id"])
        if customer:
            customer_state = customer.get("place_of_supply", "")
            gst_type = calculate_gst_type(ORG_STATE_CODE, customer_state)
            update_data["customer_name"] = customer.get("name", "")
            update_data["customer_email"] = customer.get("email", "")
            update_data["customer_gstin"] = customer.get("gstin", "")
            update_data["place_of_supply"] = customer_state
            update_data["gst_type"] = gst_type
    
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        await estimates_collection.update_one({"estimate_id": estimate_id}, {"$set": update_data})
    
    await add_estimate_history(estimate_id, "updated", "Estimate details updated")
    
    updated = await estimates_collection.find_one({"estimate_id": estimate_id}, {"_id": 0})
    return {"code": 0, "message": "Estimate updated", "estimate": updated}

@router.delete("/{estimate_id}")
async def delete_estimate(estimate_id: str):
    """Delete an estimate (only if draft status)"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if estimate.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Only draft estimates can be deleted")
    
    # Delete estimate and line items
    await estimates_collection.delete_one({"estimate_id": estimate_id})
    await estimate_items_collection.delete_many({"estimate_id": estimate_id})
    await estimate_history_collection.delete_many({"estimate_id": estimate_id})
    
    return {"code": 0, "message": "Estimate deleted"}

# ========================= LINE ITEMS ENDPOINTS =========================

@router.post("/{estimate_id}/line-items")
async def add_line_item(estimate_id: str, item: LineItemCreate):
    """Add a line item to an estimate"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Allow modifications for all statuses except converted and void
    if estimate.get("status") in ["converted", "void"]:
        raise HTTPException(status_code=400, detail="Cannot modify converted or void estimates")
    
    gst_type = estimate.get("gst_type", "igst")
    customer_id = estimate.get("customer_id")
    
    item_dict = item.dict()
    
    # Fetch item details with price list applied if item_id provided
    if item.item_id:
        # Use new pricing function that applies customer's price list
        item_details = await get_item_price_for_customer(item.item_id, customer_id)
        if item_details:
            item_dict["name"] = item.name or item_details.get("name", "")
            item_dict["hsn_code"] = item.hsn_code or item_details.get("hsn_code", "")
            item_dict["unit"] = item.unit or item_details.get("unit", "pcs")
            if item.rate == 0:
                item_dict["rate"] = item_details.get("rate", 0)
                item_dict["base_rate"] = item_details.get("base_rate", 0)
                item_dict["price_list_applied"] = item_details.get("price_list_name")
                item_dict["discount_from_pricelist"] = item_details.get("discount_applied", 0)
                item_dict["markup_from_pricelist"] = item_details.get("markup_applied", 0)
            if item.tax_percentage == 0:
                item_dict["tax_percentage"] = item_details.get("tax_percentage", 0)
    
    # Calculate totals
    totals = calculate_line_item_totals(item_dict, gst_type)
    item_dict.update(totals)
    
    # Get next line number
    max_line = await estimate_items_collection.find_one(
        {"estimate_id": estimate_id},
        sort=[("line_number", -1)]
    )
    next_line = (max_line.get("line_number", 0) if max_line else 0) + 1
    
    item_dict["line_item_id"] = generate_id("LI")
    item_dict["estimate_id"] = estimate_id
    item_dict["line_number"] = next_line
    
    await estimate_items_collection.insert_one(item_dict)
    
    # Recalculate estimate totals
    await recalculate_estimate_totals(estimate_id)
    
    item_dict.pop("_id", None)
    return {"code": 0, "message": "Line item added", "line_item": item_dict}

@router.put("/{estimate_id}/line-items/{line_item_id}")
async def update_line_item(estimate_id: str, line_item_id: str, item: LineItemUpdate):
    """Update a line item"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Allow modifications for all statuses except converted and void
    if estimate.get("status") in ["converted", "void"]:
        raise HTTPException(status_code=400, detail="Cannot modify converted or void estimates")
    
    existing = await estimate_items_collection.find_one({"line_item_id": line_item_id, "estimate_id": estimate_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    update_data = {k: v for k, v in item.dict().items() if v is not None}
    
    if update_data:
        # Merge with existing and recalculate
        merged = {**existing, **update_data}
        gst_type = estimate.get("gst_type", "igst")
        totals = calculate_line_item_totals(merged, gst_type)
        update_data.update(totals)
        
        await estimate_items_collection.update_one(
            {"line_item_id": line_item_id},
            {"$set": update_data}
        )
    
    # Recalculate estimate totals
    await recalculate_estimate_totals(estimate_id)
    
    updated = await estimate_items_collection.find_one({"line_item_id": line_item_id}, {"_id": 0})
    return {"code": 0, "message": "Line item updated", "line_item": updated}

@router.delete("/{estimate_id}/line-items/{line_item_id}")
async def delete_line_item(estimate_id: str, line_item_id: str):
    """Delete a line item"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Allow modifications for all statuses except converted and void
    if estimate.get("status") in ["converted", "void"]:
        raise HTTPException(status_code=400, detail="Cannot modify converted or void estimates")
    
    result = await estimate_items_collection.delete_one({"line_item_id": line_item_id, "estimate_id": estimate_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Recalculate estimate totals
    await recalculate_estimate_totals(estimate_id)
    
    return {"code": 0, "message": "Line item deleted"}

async def recalculate_estimate_totals(estimate_id: str):
    """Recalculate and update estimate totals"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        return
    
    line_items = await estimate_items_collection.find({"estimate_id": estimate_id}, {"_id": 0}).to_list(100)
    
    totals = calculate_estimate_totals(
        line_items,
        estimate.get("discount_type", "none"),
        estimate.get("discount_value", 0),
        estimate.get("shipping_charge", 0),
        estimate.get("adjustment", 0),
        estimate.get("gst_type", "igst")
    )
    
    totals["line_items_count"] = len(line_items)
    totals["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    await estimates_collection.update_one({"estimate_id": estimate_id}, {"$set": totals})

# ========================= STATUS WORKFLOW ENDPOINTS =========================

@router.put("/{estimate_id}/status")
async def update_estimate_status(estimate_id: str, status_update: StatusUpdate):
    """Update estimate status"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    current_status = estimate.get("status")
    new_status = status_update.status
    
    # Validate status transitions (including customer_viewed)
    valid_transitions = {
        "draft": ["sent", "void"],
        "sent": ["customer_viewed", "accepted", "declined", "expired", "void"],
        "customer_viewed": ["accepted", "declined", "expired", "void"],
        "accepted": ["converted", "void"],
        "declined": ["sent"],  # Can resend
        "expired": ["sent"],  # Can resend
        "converted": [],  # Final state
        "void": []  # Final state
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status}' to '{new_status}'"
        )
    
    update_data = {
        "status": new_status,
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    if new_status == "accepted":
        update_data["accepted_date"] = datetime.now(timezone.utc).date().isoformat()
        # Check for auto-conversion
        preferences = await get_estimate_preferences()
        if preferences.get("auto_convert_on_accept", False):
            # Will be handled after status update
            pass
    elif new_status == "declined":
        update_data["declined_date"] = datetime.now(timezone.utc).date().isoformat()
        update_data["decline_reason"] = status_update.reason
    elif new_status == "customer_viewed":
        update_data["first_viewed_at"] = datetime.now(timezone.utc).isoformat()
    
    await estimates_collection.update_one({"estimate_id": estimate_id}, {"$set": update_data})
    
    await add_estimate_history(
        estimate_id,
        "status_changed",
        f"Status changed from '{current_status}' to '{new_status}'" + (f": {status_update.reason}" if status_update.reason else "")
    )
    
    # Handle auto-conversion for accepted status
    conversion_result = None
    if new_status == "accepted":
        preferences = await get_estimate_preferences()
        if preferences.get("auto_convert_on_accept", False):
            conversion_result = await auto_convert_estimate(estimate_id, preferences)
    
    return {"code": 0, "message": f"Status updated to {new_status}", "conversion": conversion_result}

@router.post("/{estimate_id}/send")
async def send_estimate(estimate_id: str, email_to: Optional[str] = None, message: str = ""):
    """Send estimate to customer (mocked)"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if estimate.get("status") not in ["draft", "sent", "declined", "expired"]:
        raise HTTPException(status_code=400, detail="Estimate cannot be sent in current status")
    
    recipient = email_to or estimate.get("customer_email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available")
    
    # Mock send email
    email_body = f"""
Dear {estimate.get('customer_name', 'Customer')},

Please find attached the estimate {estimate.get('estimate_number')} for your review.

Subject: {estimate.get('subject', 'Estimate')}
Amount: ₹{estimate.get('grand_total', 0):,.2f}
Valid Until: {estimate.get('expiry_date', 'N/A')}

{message}

Best regards,
Battwheels Team
"""
    
    mock_send_email(
        recipient,
        f"Estimate {estimate.get('estimate_number')} from Battwheels",
        email_body,
        f"Estimate_{estimate.get('estimate_number')}.pdf"
    )
    
    # Update status to sent
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "sent",
            "sent_date": datetime.now(timezone.utc).isoformat(),
            "sent_to": recipient,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_estimate_history(estimate_id, "sent", f"Estimate sent to {recipient}")
    
    return {"code": 0, "message": f"Estimate sent to {recipient}"}

@router.post("/{estimate_id}/mark-accepted")
async def mark_accepted(estimate_id: str):
    """Mark estimate as accepted"""
    return await update_estimate_status(estimate_id, StatusUpdate(status="accepted"))

@router.post("/{estimate_id}/mark-declined")
async def mark_declined(estimate_id: str, reason: str = ""):
    """Mark estimate as declined"""
    return await update_estimate_status(estimate_id, StatusUpdate(status="declined", reason=reason))

# ========================= CONVERSION ENDPOINTS =========================

@router.post("/{estimate_id}/convert-to-invoice")
async def convert_to_invoice(estimate_id: str, request: Request):
    """Convert estimate to invoice"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if estimate.get("status") != "accepted":
        raise HTTPException(status_code=400, detail="Only accepted estimates can be converted to invoices")
    
    if estimate.get("converted_to"):
        raise HTTPException(status_code=400, detail=f"Estimate already converted to {estimate.get('converted_to')}")

    # Get org_id from tenant context
    org_id = await get_org_id(request)
    if not org_id:
        org_id = estimate.get("organization_id", "")
    
    # Get line items
    line_items = await estimate_items_collection.find({"estimate_id": estimate_id}, {"_id": 0}).to_list(100)
    
    # Use per-org sequence for invoice numbering (same as invoices_enhanced create)
    from server import db as server_db
    seq = await server_db.sequences.find_one_and_update(
        {"organization_id": org_id, "type": "invoice"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    next_num = seq.get("seq", 1) if seq else 1
    invoice_number = f"INV-{str(next_num).zfill(5)}"
    
    invoice_id = generate_id("INV")
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Create invoice document — insert into invoices_enhanced (correct collection)
    invoice_doc = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "organization_id": org_id,                        # ← FIXED: always set org_id
        "customer_id": estimate["customer_id"],
        "customer_name": estimate.get("customer_name", ""),
        "customer_email": estimate.get("customer_email", ""),
        "customer_gstin": estimate.get("customer_gstin", ""),
        "place_of_supply": estimate.get("place_of_supply", ""),
        "date": today,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat(),
        "status": "draft",
        "reference_number": estimate.get("reference_number", ""),
        "estimate_id": estimate_id,
        "estimate_number": estimate.get("estimate_number", ""),
        "salesperson_id": estimate.get("salesperson_id"),
        "salesperson_name": estimate.get("salesperson_name", ""),
        "project_id": estimate.get("project_id"),
        "subject": estimate.get("subject", ""),
        "billing_address": estimate.get("billing_address"),
        "shipping_address": estimate.get("shipping_address"),
        "line_items_count": estimate.get("line_items_count", 0),
        "discount_type": estimate.get("discount_type", "none"),
        "discount_value": estimate.get("discount_value", 0),
        "shipping_charge": estimate.get("shipping_charge", 0),
        "adjustment": estimate.get("adjustment", 0),
        "adjustment_description": estimate.get("adjustment_description", ""),
        "subtotal": estimate.get("subtotal", 0),
        "total_discount": estimate.get("total_discount", 0),
        "total_tax": estimate.get("total_tax", 0),
        "total_cgst": estimate.get("total_cgst", 0),
        "total_sgst": estimate.get("total_sgst", 0),
        "total_igst": estimate.get("total_igst", 0),
        "grand_total": estimate.get("grand_total", 0),
        "total": estimate.get("grand_total", 0),
        "balance_due": estimate.get("grand_total", 0),
        "amount_paid": 0,
        "gst_type": estimate.get("gst_type", "igst"),
        "terms_and_conditions": estimate.get("terms_and_conditions", ""),
        "notes": estimate.get("notes", ""),
        "custom_fields": estimate.get("custom_fields", {}),
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    # ← FIXED: insert into invoices collection (same as invoices_enhanced.py reads from)
    await db["invoices"].insert_one(invoice_doc)
    
    # Copy line items with org_id
    for item in line_items:
        item["invoice_id"] = invoice_id
        item["organization_id"] = org_id
        item["line_item_id"] = generate_id("LI")
        item.pop("estimate_id", None)
        item.pop("_id", None)
        await db["invoice_line_items"].insert_one(item)
    
    # Update estimate
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "converted",
            "converted_to": f"invoice:{invoice_id}",
            "converted_date": today,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_estimate_history(estimate_id, "converted", f"Converted to Invoice {invoice_number}")
    
    invoice_doc.pop("_id", None)
    return {
        "code": 0,
        "message": f"Estimate converted to Invoice {invoice_number}",
        "invoice_id": invoice_id,
        "invoice_number": invoice_number
    }

@router.post("/{estimate_id}/convert-to-sales-order")
async def convert_to_sales_order(estimate_id: str):
    """Convert estimate to sales order"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if estimate.get("status") != "accepted":
        raise HTTPException(status_code=400, detail="Only accepted estimates can be converted to sales orders")
    
    if estimate.get("converted_to"):
        raise HTTPException(status_code=400, detail=f"Estimate already converted to {estimate.get('converted_to')}")
    
    # Get line items
    line_items = await estimate_items_collection.find({"estimate_id": estimate_id}, {"_id": 0}).to_list(100)
    
    # Generate SO number
    so_settings = await db["sales_order_settings"].find_one({"type": "numbering"})
    if not so_settings:
        so_settings = {"prefix": "SO-", "next_number": 1, "padding": 5}
        await db["sales_order_settings"].insert_one({**so_settings, "type": "numbering"})
    
    so_number = f"{so_settings.get('prefix', 'SO-')}{str(so_settings.get('next_number', 1)).zfill(so_settings.get('padding', 5))}"
    await db["sales_order_settings"].update_one({"type": "numbering"}, {"$inc": {"next_number": 1}})
    
    so_id = generate_id("SO")
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Create sales order
    so_doc = {
        "salesorder_id": so_id,
        "salesorder_number": so_number,
        "customer_id": estimate["customer_id"],
        "customer_name": estimate.get("customer_name", ""),
        "customer_email": estimate.get("customer_email", ""),
        "customer_gstin": estimate.get("customer_gstin", ""),
        "place_of_supply": estimate.get("place_of_supply", ""),
        "date": today,
        "expected_shipment_date": (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat(),
        "status": "draft",
        "fulfillment_status": "unfulfilled",
        "reference_number": estimate.get("reference_number", ""),
        "estimate_id": estimate_id,
        "estimate_number": estimate.get("estimate_number", ""),
        "salesperson_id": estimate.get("salesperson_id"),
        "salesperson_name": estimate.get("salesperson_name", ""),
        "project_id": estimate.get("project_id"),
        "billing_address": estimate.get("billing_address"),
        "shipping_address": estimate.get("shipping_address"),
        "line_items_count": estimate.get("line_items_count", 0),
        "discount_type": estimate.get("discount_type", "none"),
        "discount_value": estimate.get("discount_value", 0),
        "shipping_charge": estimate.get("shipping_charge", 0),
        "adjustment": estimate.get("adjustment", 0),
        "subtotal": estimate.get("subtotal", 0),
        "total_discount": estimate.get("total_discount", 0),
        "total_tax": estimate.get("total_tax", 0),
        "grand_total": estimate.get("grand_total", 0),
        "total": estimate.get("grand_total", 0),
        "gst_type": estimate.get("gst_type", "igst"),
        "terms_and_conditions": estimate.get("terms_and_conditions", ""),
        "notes": estimate.get("notes", ""),
        "custom_fields": estimate.get("custom_fields", {}),
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db["sales_orders"].insert_one(so_doc)
    
    # Copy line items
    for item in line_items:
        item["salesorder_id"] = so_id
        item["line_item_id"] = generate_id("LI")
        item["quantity_ordered"] = item.get("quantity", 0)
        item["quantity_fulfilled"] = 0
        item.pop("estimate_id", None)
        await db["salesorder_line_items"].insert_one(item)
    
    # Update estimate
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "status": "converted",
            "converted_to": f"salesorder:{so_id}",
            "converted_date": today,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await add_estimate_history(estimate_id, "converted", f"Converted to Sales Order {so_number}")
    
    so_doc.pop("_id", None)
    return {
        "code": 0,
        "message": f"Estimate converted to Sales Order {so_number}",
        "salesorder_id": so_id,
        "salesorder_number": so_number
    }

# ========================= CLONE/DUPLICATE ENDPOINT =========================

@router.post("/{estimate_id}/clone")
async def clone_estimate(estimate_id: str):
    """Clone an estimate"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Get line items
    line_items = await estimate_items_collection.find({"estimate_id": estimate_id}, {"_id": 0}).to_list(100)
    
    # Create new estimate
    new_estimate_id = generate_id("EST")
    new_estimate_number = await get_next_estimate_number()
    today = datetime.now(timezone.utc).date().isoformat()
    
    defaults = await estimate_settings_collection.find_one({"type": "defaults"})
    validity_days = defaults.get("validity_days", 30) if defaults else 30
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=validity_days)).date().isoformat()
    
    # Clone estimate
    new_estimate = {**estimate}
    new_estimate["estimate_id"] = new_estimate_id
    new_estimate["estimate_number"] = new_estimate_number
    new_estimate["date"] = today
    new_estimate["expiry_date"] = expiry_date
    new_estimate["status"] = "draft"
    new_estimate["converted_to"] = None
    new_estimate["sent_date"] = None
    new_estimate["accepted_date"] = None
    new_estimate["declined_date"] = None
    new_estimate["created_time"] = datetime.now(timezone.utc).isoformat()
    new_estimate["updated_time"] = datetime.now(timezone.utc).isoformat()
    new_estimate.pop("_id", None)
    
    await estimates_collection.insert_one(new_estimate)
    
    # Clone line items
    for item in line_items:
        new_item = {**item}
        new_item["line_item_id"] = generate_id("LI")
        new_item["estimate_id"] = new_estimate_id
        new_item.pop("_id", None)
        await estimate_items_collection.insert_one(new_item)
    
    await add_estimate_history(new_estimate_id, "created", f"Cloned from {estimate.get('estimate_number')}")
    
    return {
        "code": 0,
        "message": f"Estimate cloned as {new_estimate_number}",
        "estimate_id": new_estimate_id,
        "estimate_number": new_estimate_number
    }

# ========================= BATCH OPERATIONS =========================

@router.post("/batch/mark-expired")
async def batch_mark_expired():
    """Mark all expired estimates"""
    today = datetime.now(timezone.utc).date().isoformat()
    
    result = await estimates_collection.update_many(
        {
            "status": {"$in": ["draft", "sent"]},
            "expiry_date": {"$lt": today}
        },
        {"$set": {"status": "expired", "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": f"Marked {result.modified_count} estimates as expired"}

@router.post("/batch/void")
async def batch_void(estimate_ids: List[str]):
    """Void multiple estimates"""
    result = await estimates_collection.update_many(
        {"estimate_id": {"$in": estimate_ids}, "status": {"$in": ["draft", "sent", "expired"]}},
        {"$set": {"status": "void", "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": f"Voided {result.modified_count} estimates"}

# ========================= ATTACHMENT ENDPOINTS =========================

@router.post("/{estimate_id}/attachments")
async def upload_attachment(
    estimate_id: str,
    file: UploadFile = File(...),
    uploaded_by: str = Form(default="system")
):
    """Upload an attachment to an estimate (max 3 files, 10MB each)"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Check attachment count
    existing_count = await estimate_attachments_collection.count_documents({"estimate_id": estimate_id})
    if existing_count >= MAX_ATTACHMENTS_PER_ESTIMATE:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_ATTACHMENTS_PER_ESTIMATE} attachments allowed")
    
    # Validate file type
    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")
    
    # Read and validate file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_ATTACHMENT_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_ATTACHMENT_SIZE_MB}MB limit")
    
    # Store attachment
    attachment_id = generate_id("ATT")
    attachment_doc = {
        "attachment_id": attachment_id,
        "estimate_id": estimate_id,
        "filename": file.filename,
        "file_size": file_size,
        "content_type": file.content_type,
        "file_data": base64.b64encode(file_content).decode('utf-8'),
        "uploaded_by": uploaded_by,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await estimate_attachments_collection.insert_one(attachment_doc)
    await add_estimate_history(estimate_id, "attachment_added", f"File attached: {file.filename}")
    
    return {
        "code": 0,
        "message": "Attachment uploaded",
        "attachment": {
            "attachment_id": attachment_id,
            "filename": file.filename,
            "file_size": file_size,
            "content_type": file.content_type,
            "uploaded_at": attachment_doc["uploaded_at"]
        }
    }

@router.get("/{estimate_id}/attachments")
async def list_attachments(estimate_id: str):
    """List all attachments for an estimate"""
    attachments = await estimate_attachments_collection.find(
        {"estimate_id": estimate_id},
        {"_id": 0, "file_data": 0}
    ).to_list(10)
    
    return {"code": 0, "attachments": attachments}

@router.get("/{estimate_id}/attachments/{attachment_id}")
async def download_attachment(estimate_id: str, attachment_id: str):
    """Download an attachment"""
    attachment = await estimate_attachments_collection.find_one(
        {"attachment_id": attachment_id, "estimate_id": estimate_id}
    )
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    file_data = base64.b64decode(attachment["file_data"])
    
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=attachment["content_type"],
        headers={"Content-Disposition": f"attachment; filename={attachment['filename']}"}
    )

@router.delete("/{estimate_id}/attachments/{attachment_id}")
async def delete_attachment(estimate_id: str, attachment_id: str):
    """Delete an attachment"""
    result = await estimate_attachments_collection.delete_one(
        {"attachment_id": attachment_id, "estimate_id": estimate_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    await add_estimate_history(estimate_id, "attachment_removed", f"Attachment {attachment_id} removed")
    
    return {"code": 0, "message": "Attachment deleted"}

# ========================= SHARE LINK ENDPOINTS =========================

@router.post("/{estimate_id}/share")
async def create_share_link(estimate_id: str, share_config: ShareLinkCreate = None):
    """Generate a public share link for the estimate"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    if estimate.get("status") == "void":
        raise HTTPException(status_code=400, detail="Cannot share a voided estimate")
    
    config = share_config or ShareLinkCreate()
    
    # Generate unique share token
    share_token = generate_share_token()
    
    # Calculate expiry
    expires_at = (datetime.now(timezone.utc) + timedelta(days=config.expiry_days)).isoformat()
    
    # Hash password if provided
    password_hash = None
    if config.password_protected and config.password:
        password_hash = hashlib.sha256(config.password.encode()).hexdigest()
    
    share_link_id = generate_id("SHL")
    share_doc = {
        "share_link_id": share_link_id,
        "estimate_id": estimate_id,
        "share_token": share_token,
        "expires_at": expires_at,
        "allow_accept": config.allow_accept,
        "allow_decline": config.allow_decline,
        "password_protected": config.password_protected,
        "password_hash": password_hash,
        "view_count": 0,
        "last_viewed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await estimate_share_links_collection.insert_one(share_doc)
    await add_estimate_history(estimate_id, "share_link_created", f"Public share link created (expires: {expires_at[:10]})")
    
    # Update estimate with share info
    await estimates_collection.update_one(
        {"estimate_id": estimate_id},
        {"$set": {
            "has_share_link": True,
            "share_token": share_token,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Generate public URL (will be relative - frontend needs to construct full URL)
    public_url = f"/quote/{share_token}"
    
    return {
        "code": 0,
        "message": "Share link created",
        "share_link": {
            "share_link_id": share_link_id,
            "share_token": share_token,
            "public_url": public_url,
            "expires_at": expires_at,
            "allow_accept": config.allow_accept,
            "allow_decline": config.allow_decline,
            "password_protected": config.password_protected
        }
    }

@router.get("/{estimate_id}/share-links")
async def list_share_links(estimate_id: str):
    """List all share links for an estimate"""
    links = await estimate_share_links_collection.find(
        {"estimate_id": estimate_id, "is_active": True},
        {"_id": 0, "password_hash": 0}
    ).to_list(10)
    
    return {"code": 0, "share_links": links}

@router.delete("/{estimate_id}/share/{share_link_id}")
async def revoke_share_link(estimate_id: str, share_link_id: str):
    """Revoke a share link"""
    result = await estimate_share_links_collection.update_one(
        {"share_link_id": share_link_id, "estimate_id": estimate_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Share link not found")
    
    await add_estimate_history(estimate_id, "share_link_revoked", f"Share link {share_link_id} revoked")
    
    return {"code": 0, "message": "Share link revoked"}

# ========================= PDF GENERATION ENDPOINTS =========================

@router.get("/{estimate_id}/pdf")
async def generate_pdf(estimate_id: str):
    """Generate and download PDF of the estimate"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    line_items = await estimate_items_collection.find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).sort("line_number", 1).to_list(100)
    
    # Generate HTML
    html_content = generate_pdf_html(estimate, line_items)
    
    # Try to use WeasyPrint for PDF generation
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Estimate_{estimate.get('estimate_number', estimate_id)}.pdf"
            }
        )
    except ImportError:
        # WeasyPrint not available - return HTML for client-side rendering
        logger.warning("WeasyPrint not available, returning HTML for client-side PDF generation")
        return JSONResponse({
            "code": 1,
            "message": "PDF generation requires WeasyPrint. Returning HTML.",
            "html": html_content,
            "estimate": estimate
        })
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        # Return HTML as fallback
        return JSONResponse({
            "code": 1,
            "message": f"PDF generation failed: {str(e)}. Returning HTML.",
            "html": html_content,
            "estimate": estimate
        })

@router.get("/{estimate_id}/pdf/{template_id}")
async def generate_pdf_with_template(estimate_id: str, template_id: str = "standard"):
    """Generate PDF with specific template"""
    if template_id not in PDF_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid template. Available: {list(PDF_TEMPLATES.keys())}")
    
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    line_items = await estimate_items_collection.find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).sort("line_number", 1).to_list(100)
    
    html_content = generate_pdf_html(estimate, line_items, template_id)
    
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Estimate_{estimate.get('estimate_number', estimate_id)}_{template_id}.pdf"
            }
        )
    except Exception as e:
        logger.warning(f"PDF generation with template failed: {e}")
        return JSONResponse({
            "code": 1,
            "message": "PDF generation requires WeasyPrint. Returning HTML.",
            "html": html_content,
            "template": template_id
        })

@router.get("/{estimate_id}/preview-html")
async def get_preview_html(estimate_id: str):
    """Get HTML preview of the estimate (for client-side PDF generation)"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    line_items = await estimate_items_collection.find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).sort("line_number", 1).to_list(100)
    
    html_content = generate_pdf_html(estimate, line_items)
    
    return {"code": 0, "html": html_content}

# ========================= PUBLIC ACCESS ENDPOINTS =========================
# These endpoints are accessed via the public share link (no auth required)

@router.get("/public/{share_token}")
async def get_public_estimate(share_token: str, password: Optional[str] = None):
    """Get estimate details via public share link"""
    # Find share link
    share_link = await estimate_share_links_collection.find_one(
        {"share_token": share_token, "is_active": True}
    )
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")
    
    # Check expiry
    expires_at = datetime.fromisoformat(share_link["expires_at"].replace('Z', '+00:00'))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link has expired")
    
    # Check password if required
    if share_link.get("password_protected"):
        if not password:
            return {"code": 2, "message": "Password required", "password_protected": True}
        if hashlib.sha256(password.encode()).hexdigest() != share_link.get("password_hash"):
            raise HTTPException(status_code=401, detail="Invalid password")
    
    # Get estimate
    estimate = await estimates_collection.find_one(
        {"estimate_id": share_link["estimate_id"]},
        {"_id": 0}
    )
    
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Get line items
    line_items = await estimate_items_collection.find(
        {"estimate_id": share_link["estimate_id"]},
        {"_id": 0}
    ).sort("line_number", 1).to_list(100)
    
    estimate["line_items"] = line_items
    
    # Update view count and mark as customer_viewed if first view
    view_count = share_link.get("view_count", 0) + 1
    await estimate_share_links_collection.update_one(
        {"share_token": share_token},
        {
            "$set": {"last_viewed_at": datetime.now(timezone.utc).isoformat()},
            "$inc": {"view_count": 1}
        }
    )
    
    # Update estimate status to customer_viewed if it was sent
    if estimate.get("status") == "sent":
        await estimates_collection.update_one(
            {"estimate_id": share_link["estimate_id"]},
            {
                "$set": {
                    "status": "customer_viewed",
                    "first_viewed_at": datetime.now(timezone.utc).isoformat(),
                    "updated_time": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        estimate["status"] = "customer_viewed"
        await add_estimate_history(share_link["estimate_id"], "customer_viewed", "Customer viewed the estimate via public link")
    
    # Get attachments (metadata only)
    attachments = await estimate_attachments_collection.find(
        {"estimate_id": share_link["estimate_id"]},
        {"_id": 0, "file_data": 0}
    ).to_list(10)
    
    return {
        "code": 0,
        "estimate": estimate,
        "attachments": attachments,
        "can_accept": share_link.get("allow_accept", True) and estimate.get("status") in ["sent", "customer_viewed"],
        "can_decline": share_link.get("allow_decline", True) and estimate.get("status") in ["sent", "customer_viewed"],
        "view_count": view_count
    }

@router.post("/public/{share_token}/action")
async def customer_action(share_token: str, action: CustomerAction):
    """Handle customer accept/decline via public link"""
    # Find share link
    share_link = await estimate_share_links_collection.find_one(
        {"share_token": share_token, "is_active": True}
    )
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")
    
    # Check expiry
    expires_at = datetime.fromisoformat(share_link["expires_at"].replace('Z', '+00:00'))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link has expired")
    
    # Get estimate
    estimate = await estimates_collection.find_one({"estimate_id": share_link["estimate_id"]})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Validate action is allowed
    if action.action == "accept":
        if not share_link.get("allow_accept", True):
            raise HTTPException(status_code=403, detail="Acceptance not allowed via this link")
        if estimate.get("status") not in ["sent", "customer_viewed"]:
            raise HTTPException(status_code=400, detail="Estimate cannot be accepted in current status")
        
        # Mark as accepted
        update_data = {
            "status": "accepted",
            "accepted_date": datetime.now(timezone.utc).date().isoformat(),
            "accepted_via": "public_link",
            "customer_comments": action.comments,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }
        await estimates_collection.update_one(
            {"estimate_id": share_link["estimate_id"]},
            {"$set": update_data}
        )
        await add_estimate_history(share_link["estimate_id"], "accepted", f"Customer accepted via public link. Comments: {action.comments or 'None'}")
        
        # Check for auto-conversion
        preferences = await get_estimate_preferences()
        conversion_result = None
        if preferences.get("auto_convert_on_accept", False):
            conversion_result = await auto_convert_estimate(share_link["estimate_id"], preferences)
        
        return {
            "code": 0,
            "message": "Estimate accepted successfully",
            "status": "accepted",
            "conversion": conversion_result
        }
    
    elif action.action == "decline":
        if not share_link.get("allow_decline", True):
            raise HTTPException(status_code=403, detail="Decline not allowed via this link")
        if estimate.get("status") not in ["sent", "customer_viewed"]:
            raise HTTPException(status_code=400, detail="Estimate cannot be declined in current status")
        
        # Mark as declined
        update_data = {
            "status": "declined",
            "declined_date": datetime.now(timezone.utc).date().isoformat(),
            "declined_via": "public_link",
            "decline_reason": action.comments,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }
        await estimates_collection.update_one(
            {"estimate_id": share_link["estimate_id"]},
            {"$set": update_data}
        )
        await add_estimate_history(share_link["estimate_id"], "declined", f"Customer declined via public link. Reason: {action.comments or 'None'}")
        
        return {
            "code": 0,
            "message": "Estimate declined",
            "status": "declined"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'accept' or 'decline'")

@router.get("/public/{share_token}/pdf")
async def get_public_pdf(share_token: str):
    """Download PDF via public share link"""
    # Find share link
    share_link = await estimate_share_links_collection.find_one(
        {"share_token": share_token, "is_active": True}
    )
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")
    
    # Check expiry
    expires_at = datetime.fromisoformat(share_link["expires_at"].replace('Z', '+00:00'))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link has expired")
    
    return await generate_pdf(share_link["estimate_id"])

@router.get("/public/{share_token}/attachment/{attachment_id}")
async def download_public_attachment(share_token: str, attachment_id: str):
    """Download attachment via public share link"""
    # Find share link
    share_link = await estimate_share_links_collection.find_one(
        {"share_token": share_token, "is_active": True}
    )
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")
    
    return await download_attachment(share_link["estimate_id"], attachment_id)

# ========================= ACTIVITY LOG ENDPOINT =========================

@router.get("/{estimate_id}/activity")
async def get_estimate_activity(estimate_id: str, limit: int = 50):
    """Get activity log for an estimate"""
    estimate = await estimates_collection.find_one({"estimate_id": estimate_id})
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Get from history collection
    history = await estimate_history_collection.find(
        {"estimate_id": estimate_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Also get from unified activity log if available
    try:
        from services.activity_service import get_entity_activities, EntityType
        activities = await get_entity_activities(
            entity_type=EntityType.ESTIMATE,
            entity_id=estimate_id,
            limit=limit
        )
        # Merge and sort
        all_activities = history + activities
        all_activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"code": 0, "activities": all_activities[:limit]}
    except:
        return {"code": 0, "activities": history}
