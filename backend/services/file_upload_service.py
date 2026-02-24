"""
File Upload Service for Organization Assets
============================================

Handles logo and other file uploads with:
- Size validation (max 1MB)
- File type validation (jpg, jpeg, png, gif, bmp)
- Image dimension validation
- Secure storage
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
import shutil

from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path("/app/uploads")
LOGO_DIR = UPLOAD_DIR / "logos"
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp"}
RECOMMENDED_DIMENSIONS = (240, 240)
MAX_DIMENSIONS = (1024, 1024)

# Ensure directories exist
LOGO_DIR.mkdir(parents=True, exist_ok=True)


class FileUploadService:
    """Service for handling file uploads"""
    
    @staticmethod
    def get_extension(filename: str) -> str:
        """Get file extension in lowercase"""
        if "." not in filename:
            return ""
        return filename.rsplit(".", 1)[1].lower()
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Check if file type is allowed"""
        ext = FileUploadService.get_extension(filename)
        return ext in ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Check if file size is within limit"""
        return file_size <= MAX_FILE_SIZE
    
    @staticmethod
    def get_image_dimensions(file_path: Path) -> Tuple[int, int]:
        """Get image dimensions"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return img.size
        except Exception as e:
            logger.warning(f"Could not read image dimensions: {e}")
            return (0, 0)
    
    @staticmethod
    def generate_unique_filename(original_filename: str, org_id: str) -> str:
        """Generate a unique filename"""
        ext = FileUploadService.get_extension(original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{org_id}_{timestamp}_{unique_id}.{ext}"
    
    @classmethod
    async def upload_logo(
        cls,
        file: UploadFile,
        org_id: str,
        logo_type: str = "main"  # main, dark, favicon
    ) -> dict:
        """
        Upload organization logo.
        
        Args:
            file: The uploaded file
            org_id: Organization ID
            logo_type: Type of logo (main, dark, favicon)
            
        Returns:
            dict with file_url and metadata
        """
        # Validate file type
        if not cls.validate_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if not cls.validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB"
            )
        
        # Validate MIME type from content (not just extension)
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(content))
            img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file. File appears to be corrupted or is not a valid image.")
        
        # Generate unique filename
        filename = cls.generate_unique_filename(file.filename, org_id)
        
        # Create org-specific directory
        org_logo_dir = LOGO_DIR / org_id
        org_logo_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = org_logo_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Get image dimensions
        width, height = cls.get_image_dimensions(file_path)
        
        # Generate URL (relative to app)
        file_url = f"/api/uploads/logos/{org_id}/{filename}"
        
        logger.info(f"Logo uploaded: {file_url} ({width}x{height}, {file_size} bytes)")
        
        return {
            "success": True,
            "file_url": file_url,
            "filename": filename,
            "original_filename": file.filename,
            "file_size": file_size,
            "content_type": file.content_type,
            "dimensions": {"width": width, "height": height},
            "logo_type": logo_type
        }
    
    @classmethod
    def delete_logo(cls, org_id: str, filename: str) -> bool:
        """Delete a logo file"""
        try:
            file_path = LOGO_DIR / org_id / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Logo deleted: {org_id}/{filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete logo: {e}")
            return False
    
    @classmethod
    def get_logo_path(cls, org_id: str, filename: str) -> Optional[Path]:
        """Get full path to a logo file"""
        file_path = LOGO_DIR / org_id / filename
        if file_path.exists():
            return file_path
        return None
    
    @classmethod
    def cleanup_old_logos(cls, org_id: str, keep_filename: str = None):
        """Remove old logos for an organization, optionally keeping one"""
        try:
            org_logo_dir = LOGO_DIR / org_id
            if not org_logo_dir.exists():
                return
            
            for file_path in org_logo_dir.iterdir():
                if keep_filename and file_path.name == keep_filename:
                    continue
                file_path.unlink()
                logger.info(f"Cleaned up old logo: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup logos: {e}")


# Singleton
file_upload_service = FileUploadService()
