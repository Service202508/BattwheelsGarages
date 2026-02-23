"""
E-Invoice API Routes for Battwheels OS
Handles IRN generation, cancellation, and configuration management
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging

# Import tenant context
from core.tenant.context import TenantContext, tenant_context_required

# Import E-Invoice service
from services.einvoice_service import (
    get_einvoice_config,
    save_einvoice_config,
    delete_einvoice_config,
    check_einvoice_eligibility,
    get_irn_details,
    list_irn_records,
    IRNGenerator,
    EInvoiceValidator,
    generate_qr_code_base64,
    generate_qr_code_image
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/einvoice", tags=["E-Invoice"])

# ==================== PYDANTIC MODELS ====================

class EInvoiceConfigInput(BaseModel):
    """E-Invoice configuration input"""
    gstin: str = Field(..., min_length=15, max_length=15, description="Organization GSTIN")
    irp_username: str = Field(..., min_length=1, description="IRP portal username")
    irp_password: str = Field(..., min_length=1, description="IRP portal password")
    client_id: str = Field(..., min_length=1, description="API client ID")
    client_secret: str = Field(..., min_length=1, description="API client secret")
    is_sandbox: bool = Field(default=True, description="Use sandbox environment")
    enabled: bool = Field(default=True, description="Enable E-Invoicing")
    turnover_threshold_met: bool = Field(default=False, description="Above ₹5Cr turnover threshold")

class IRNGenerateRequest(BaseModel):
    """IRN generation request"""
    invoice_id: str = Field(..., description="Invoice ID to generate IRN for")

class IRNCancelRequest(BaseModel):
    """IRN cancellation request"""
    irn: str = Field(..., min_length=64, max_length=64, description="IRN to cancel")
    reason: str = Field(..., description="Cancellation reason code: 1=Duplicate, 2=Data entry mistake, 3=Order cancelled, 4=Other")
    remarks: str = Field(default="", max_length=100, description="Additional remarks")

# ==================== DATABASE ACCESS ====================

def get_db():
    """Get database connection"""
    from server import db
    return db

# ==================== CONFIGURATION ENDPOINTS ====================

@router.get("/config")
async def get_config(ctx: TenantContext = Depends(tenant_context_required)):
    """Get E-Invoice configuration status for organization"""
    config = await get_einvoice_config(ctx.org_id)
    
    if not config:
        return {
            "code": 0,
            "configured": False,
            "message": "E-Invoice not configured. Configure in Organization Settings → Finance."
        }
    
    return {
        "code": 0,
        "configured": True,
        "gstin": config.get("gstin"),
        "irp_username": config.get("irp_username"),
        "has_password": bool(config.get("irp_password_encrypted")),
        "client_id": config.get("client_id"),
        "has_client_secret": bool(config.get("client_secret_encrypted")),
        "is_sandbox": config.get("is_sandbox", True),
        "enabled": config.get("enabled", False),
        "turnover_threshold_met": config.get("turnover_threshold_met", False),
        "updated_at": config.get("updated_at")
    }

@router.post("/config")
async def save_config(
    data: EInvoiceConfigInput,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Save E-Invoice configuration for organization"""
    
    # Validate GSTIN format
    if not EInvoiceValidator.validate_gstin(data.gstin):
        raise HTTPException(status_code=400, detail="Invalid GSTIN format")
    
    result = await save_einvoice_config(ctx.org_id, data.model_dump())
    return result

@router.delete("/config")
async def remove_config(ctx: TenantContext = Depends(tenant_context_required)):
    """Remove E-Invoice configuration"""
    result = await delete_einvoice_config(ctx.org_id)
    return result

@router.get("/eligibility")
async def check_eligibility(ctx: TenantContext = Depends(tenant_context_required)):
    """Check if organization is eligible for E-Invoicing"""
    result = await check_einvoice_eligibility(ctx.org_id)
    return {"code": 0, **result}

# ==================== IRN GENERATION ENDPOINTS ====================

@router.post("/generate-irn")
async def generate_irn(
    data: IRNGenerateRequest,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Generate IRN for a B2B invoice"""
    db = get_db()
    
    # Check eligibility
    eligibility = await check_einvoice_eligibility(ctx.org_id)
    if not eligibility.get("eligible"):
        return {
            "code": 1,
            "success": False,
            "message": eligibility.get("reason", "E-Invoice not configured"),
            "skip_irn": True
        }
    
    # Get invoice
    invoice = await db.invoices.find_one(
        {"invoice_id": data.invoice_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if already has IRN
    if invoice.get("irn") and invoice.get("irn_status") == "registered":
        return {
            "code": 1,
            "success": False,
            "message": "Invoice already has a registered IRN",
            "irn": invoice.get("irn")
        }
    
    # Check invoice status - must be finalized/sent
    if invoice.get("status") == "draft":
        return {
            "code": 1,
            "success": False,
            "message": "Cannot generate IRN for draft invoice. Finalize the invoice first."
        }
    
    # Get line items
    line_items = await db.invoice_line_items.find(
        {"invoice_id": data.invoice_id},
        {"_id": 0}
    ).to_list(100)
    
    if not line_items:
        # Try embedded line_items
        line_items = invoice.get("line_items", [])
    
    if not line_items:
        return {
            "code": 1,
            "success": False,
            "message": "Invoice has no line items"
        }
    
    # Get supplier (organization) details
    org = await db.organizations.find_one(
        {"organization_id": ctx.org_id},
        {"_id": 0}
    )
    
    if not org:
        raise HTTPException(status_code=500, detail="Organization not found")
    
    # Build supplier details
    supplier = {
        "gstin": org.get("gstin", invoice.get("supplier_gstin", "")),
        "legal_name": org.get("legal_name", org.get("name", "")),
        "trade_name": org.get("trade_name", org.get("name", "")),
        "name": org.get("name", ""),
        "address_line1": org.get("address", org.get("billing_address", {}).get("address", "")),
        "address_line2": org.get("address_line2", ""),
        "city": org.get("city", org.get("billing_address", {}).get("city", "")),
        "pincode": org.get("pincode", org.get("billing_address", {}).get("zip", "")),
        "state_code": org.get("state_code", org.get("gstin", "")[:2] if org.get("gstin") else ""),
        "phone": org.get("phone", ""),
        "email": org.get("email", "")
    }
    
    # Get buyer (customer) details
    customer = None
    if invoice.get("customer_id"):
        customer = await db.contacts.find_one(
            {"contact_id": invoice.get("customer_id")},
            {"_id": 0}
        )
    
    buyer = {
        "gstin": invoice.get("customer_gstin", customer.get("gstin", "URP") if customer else "URP"),
        "legal_name": invoice.get("customer_name", customer.get("company_name", customer.get("name", "")) if customer else ""),
        "name": invoice.get("customer_name", customer.get("name", "") if customer else ""),
        "trade_name": customer.get("trade_name", "") if customer else "",
        "address_line1": invoice.get("billing_address", {}).get("address", customer.get("billing_address", {}).get("address", "") if customer else ""),
        "city": invoice.get("billing_address", {}).get("city", customer.get("billing_address", {}).get("city", "") if customer else ""),
        "pincode": invoice.get("billing_address", {}).get("zip", customer.get("billing_address", {}).get("zip", "") if customer else ""),
        "state_code": invoice.get("place_of_supply", customer.get("gstin", "")[:2] if customer and customer.get("gstin") else ""),
        "phone": customer.get("phone", "") if customer else "",
        "email": customer.get("email", invoice.get("customer_email", "")) if customer else invoice.get("customer_email", "")
    }
    
    # Prepare invoice with required fields
    invoice_data = {
        **invoice,
        "supplier_gstin": supplier["gstin"],
        "customer_gstin": buyer["gstin"],
        "place_of_supply": invoice.get("place_of_supply", buyer["state_code"]),
        "is_igst": invoice.get("is_igst", supplier["state_code"] != buyer["state_code"])
    }
    
    # Generate IRN
    config = await get_einvoice_config(ctx.org_id)
    generator = IRNGenerator(ctx.org_id, is_sandbox=config.get("is_sandbox", True))
    
    result = await generator.generate_irn(invoice_data, line_items, supplier, buyer)
    
    return result

@router.post("/cancel-irn")
async def cancel_irn(
    data: IRNCancelRequest,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Cancel an IRN within 24 hours of generation"""
    
    # Validate reason code
    valid_reasons = ["1", "2", "3", "4"]
    if data.reason not in valid_reasons:
        raise HTTPException(
            status_code=400,
            detail="Invalid reason code. Use: 1=Duplicate, 2=Data entry mistake, 3=Order cancelled, 4=Other"
        )
    
    config = await get_einvoice_config(ctx.org_id)
    if not config:
        raise HTTPException(status_code=400, detail="E-Invoice not configured")
    
    generator = IRNGenerator(ctx.org_id, is_sandbox=config.get("is_sandbox", True))
    result = await generator.cancel_irn(data.irn, data.reason, data.remarks)
    
    return result

@router.get("/irn/{invoice_id}")
async def get_invoice_irn(
    invoice_id: str,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get IRN details for an invoice"""
    irn_data = await get_irn_details(ctx.org_id, invoice_id)
    
    if not irn_data:
        return {
            "code": 0,
            "has_irn": False,
            "message": "No IRN found for this invoice"
        }
    
    return {
        "code": 0,
        "has_irn": True,
        **irn_data
    }

@router.get("/irn-list")
async def list_irns(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """List all IRN records for organization"""
    records = await list_irn_records(ctx.org_id, skip, limit, status)
    return {
        "code": 0,
        "records": records,
        "count": len(records)
    }

# ==================== VALIDATION ENDPOINT ====================

@router.post("/validate-invoice/{invoice_id}")
async def validate_invoice_for_einvoice(
    invoice_id: str,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Validate invoice for E-Invoice compliance before IRN generation"""
    db = get_db()
    
    # Get invoice
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get line items
    line_items = await db.invoice_line_items.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).to_list(100)
    
    if not line_items:
        line_items = invoice.get("line_items", [])
    
    # Validate
    is_valid, errors = EInvoiceValidator.validate_invoice(invoice, line_items)
    
    return {
        "code": 0,
        "is_valid": is_valid,
        "errors": errors,
        "message": "Invoice is valid for E-Invoice" if is_valid else "Invoice has validation errors"
    }

# ==================== QR CODE ENDPOINT ====================

@router.get("/qr-code/{invoice_id}")
async def get_qr_code(
    invoice_id: str,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get QR code image for invoice IRN (base64 encoded)"""
    db = get_db()
    
    # Get invoice with IRN
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": ctx.org_id},
        {"_id": 0, "irn_signed_qr": 1, "irn": 1, "irn_status": 1}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.get("irn_signed_qr"):
        return {
            "code": 1,
            "has_qr": False,
            "message": "Invoice does not have IRN QR code"
        }
    
    try:
        qr_base64 = generate_qr_code_base64(invoice["irn_signed_qr"], size=200)
        return {
            "code": 0,
            "has_qr": True,
            "irn": invoice.get("irn"),
            "qr_code_base64": qr_base64,
            "qr_code_data_uri": f"data:image/png;base64,{qr_base64}"
        }
    except Exception as e:
        logger.error(f"QR code generation failed: {e}")
        return {
            "code": 1,
            "has_qr": False,
            "message": f"Failed to generate QR code: {str(e)}"
        }

@router.get("/qr-code-image/{invoice_id}")
async def get_qr_code_image(
    invoice_id: str,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Get QR code as PNG image for invoice IRN"""
    from fastapi.responses import Response
    
    db = get_db()
    
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": ctx.org_id},
        {"_id": 0, "irn_signed_qr": 1}
    )
    
    if not invoice or not invoice.get("irn_signed_qr"):
        raise HTTPException(status_code=404, detail="QR code not available")
    
    try:
        img_bytes = generate_qr_code_image(invoice["irn_signed_qr"], size=200)
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR generation failed: {str(e)}")
