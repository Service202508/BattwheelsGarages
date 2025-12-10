import os
import logging
from typing import Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class FileStorageService:
    """
    File storage service supporting S3-compatible storage
    Falls back to local storage in development
    """

    def __init__(self):
        self.environment = os.environ.get('ENVIRONMENT', 'development')
        self.storage_type = os.environ.get('STORAGE_TYPE', 'local')  # 'local' or 's3'
        
        # S3 configuration
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', '')
        self.region = os.environ.get('S3_REGION', 'us-east-1')
        self.access_key = os.environ.get('S3_ACCESS_KEY', '')
        self.secret_key = os.environ.get('S3_SECRET_KEY', '')
        self.base_url = os.environ.get('S3_BASE_URL', '')
        self.endpoint_url = os.environ.get('S3_ENDPOINT_URL', None)  # For DigitalOcean Spaces, etc.
        
        # Local storage path
        self.local_storage_path = Path('/app/backend/uploads')
        self.local_storage_path.mkdir(exist_ok=True)
        
        # Initialize S3 client if configured
        self.s3_client = None
        if self.storage_type == 's3' and self.bucket_name:
            try:
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    endpoint_url=self.endpoint_url
                )
                logger.info(f"✅ S3 client initialized for bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize S3 client: {str(e)}")
                logger.info("Falling back to local storage")
                self.storage_type = 'local'

    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to avoid collisions
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        ext = Path(original_filename).suffix
        return f"{timestamp}_{unique_id}{ext}"

    async def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        folder: str = 'uploads'
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file to storage
        
        Returns:
            (success: bool, file_url: str, error_message: str)
        """
        try:
            unique_filename = self._generate_unique_filename(original_filename)
            file_key = f"{folder}/{unique_filename}"

            if self.storage_type == 's3' and self.s3_client:
                return await self._upload_to_s3(file_content, file_key, original_filename)
            else:
                return await self._upload_to_local(file_content, file_key)

        except Exception as e:
            logger.error(f"❌ File upload failed: {str(e)}")
            return False, None, str(e)

    async def _upload_to_s3(
        self,
        file_content: bytes,
        file_key: str,
        original_filename: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload file to S3-compatible storage
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentDisposition=f'attachment; filename="{original_filename}"'
            )

            # Generate file URL
            if self.base_url:
                file_url = f"{self.base_url}/{file_key}"
            elif self.endpoint_url:
                file_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
            else:
                file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_key}"

            logger.info(f"✅ File uploaded to S3: {file_url}")
            return True, file_url, None

        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {str(e)}")
            return False, None, str(e)

    async def _upload_to_local(
        self,
        file_content: bytes,
        file_key: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload file to local storage (development fallback)
        """
        try:
            file_path = self.local_storage_path / file_key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Generate local URL (relative to backend)
            file_url = f"/uploads/{file_key}"
            logger.info(f"✅ File uploaded locally: {file_url}")
            return True, file_url, None

        except Exception as e:
            logger.error(f"❌ Local upload failed: {str(e)}")
            return False, None, str(e)

    async def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from storage
        """
        try:
            if self.storage_type == 's3' and self.s3_client:
                # Extract file key from URL
                file_key = file_url.split(f"{self.bucket_name}/")[-1]
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
                logger.info(f"✅ File deleted from S3: {file_key}")
            else:
                # Delete from local storage
                file_path = self.local_storage_path / file_url.replace('/uploads/', '')
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"✅ File deleted locally: {file_path}")

            return True

        except Exception as e:
            logger.error(f"❌ File deletion failed: {str(e)}")
            return False


file_storage = FileStorageService()
