"""
File Upload Routes
==================

Handles file uploads for organization assets (logos, documents).
"""

import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import FileResponse

from core.tenant.context import TenantContext, tenant_context_required
from services.file_upload_service import file_upload_service, LOGO_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uploads", tags=["uploads"])

# Database reference
db = None


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    logo_type: str = "main",
    ctx: TenantContext = Depends(tenant_context_required)
):
    """
    Upload organization logo.
    
    - **file**: Image file (jpg, jpeg, png, gif, bmp)
    - **logo_type**: Type of logo - main, dark, or favicon
    
    Requirements:
    - Maximum file size: 1MB
    - Supported formats: jpg, jpeg, png, gif, bmp
    - Recommended dimensions: 240x240 pixels
    """
    # Validate logo_type
    if logo_type not in ["main", "dark", "favicon"]:
        raise HTTPException(status_code=400, detail="Invalid logo_type. Use: main, dark, or favicon")
    
    # Upload the file
    result = await file_upload_service.upload_logo(file, ctx.org_id, logo_type)
    
    # Update organization branding in database
    if db is not None:
        field_map = {
            "main": "branding.logo_url",
            "dark": "branding.logo_dark_url",
            "favicon": "branding.favicon_url"
        }
        field = field_map.get(logo_type, "branding.logo_url")
        
        # Also update legacy logo_url for main logo
        update_doc = {field: result["file_url"]}
        if logo_type == "main":
            update_doc["logo_url"] = result["file_url"]
        
        await db.organizations.update_one(
            {"organization_id": ctx.org_id},
            {"$set": update_doc}
        )
    
    return result


@router.delete("/logo/{logo_type}")
async def delete_logo(
    logo_type: str,
    ctx: TenantContext = Depends(tenant_context_required)
):
    """Delete organization logo"""
    if logo_type not in ["main", "dark", "favicon"]:
        raise HTTPException(status_code=400, detail="Invalid logo_type")
    
    # Get current logo URL from database
    if db is not None:
        org = await db.organizations.find_one(
            {"organization_id": ctx.org_id},
            {"branding": 1, "logo_url": 1}
        )
        
        if org:
            branding = org.get("branding", {})
            field_map = {
                "main": "logo_url",
                "dark": "logo_dark_url", 
                "favicon": "favicon_url"
            }
            current_url = branding.get(field_map[logo_type])
            
            # Delete the file if it's a local upload
            if current_url and current_url.startswith("/api/uploads/logos/"):
                filename = current_url.split("/")[-1]
                file_upload_service.delete_logo(ctx.org_id, filename)
            
            # Clear from database
            update_field = f"branding.{field_map[logo_type]}"
            update_doc = {update_field: None}
            if logo_type == "main":
                update_doc["logo_url"] = None
            
            await db.organizations.update_one(
                {"organization_id": ctx.org_id},
                {"$set": update_doc}
            )
    
    return {"success": True, "message": f"{logo_type} logo deleted"}


@router.get("/logos/{org_id}/{filename}")
async def serve_logo(org_id: str, filename: str):
    """Serve uploaded logo file"""
    file_path = file_upload_service.get_logo_path(org_id, filename)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="Logo not found")
    
    # Determine content type
    ext = filename.rsplit(".", 1)[-1].lower()
    content_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp"
    }
    content_type = content_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        file_path,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"}  # Cache for 1 day
    )


@router.get("/logo-requirements")
async def get_logo_requirements():
    """Get logo upload requirements"""
    return {
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "max_file_size_bytes": MAX_FILE_SIZE,
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
        "recommended_dimensions": {
            "width": 240,
            "height": 240,
            "dpi": 72
        },
        "usage": [
            "Transaction PDFs",
            "Email notifications",
            "Application header",
            "Customer portal"
        ]
    }


def init_upload_routes(app_db):
    """Initialize with database connection"""
    global db
    db = app_db
    return router
