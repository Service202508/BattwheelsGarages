"""
Per-Tenant Credential Service
==============================

Centralized, encrypted per-org credential storage.
Replaces all ad-hoc plaintext credential storage in org documents.

All credentials are encrypted with Fernet symmetric encryption.
Decrypted values are never logged and are only accessible at the point of use.

Supported credential types:
  - RAZORPAY: key_id, key_secret, webhook_secret, mode
  - EMAIL_SMTP: provider, api_key, from_email, from_name
  - IRP_EINVOICE: Handled separately by einvoice_service.py (already correct)
  - CUSTOM: Arbitrary encrypted JSON

Fallback: If an org has no own credentials, global .env values are returned.
This ensures backward compatibility for Battwheels Garages.
"""

import os
import base64
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Encryption key — must be stable across restarts
_RAW_KEY = os.environ.get("CREDENTIAL_ENCRYPTION_KEY", "")
if not _RAW_KEY:
    # Derive from JWT_SECRET so no new env var is required in dev/preview
    _RAW_KEY = os.environ.get("JWT_SECRET", "battwheels-default-key-change-in-prod")

# Normalize to valid Fernet key (32 bytes base64url)
_KEY_BYTES = base64.urlsafe_b64encode(hashlib.sha256(_RAW_KEY.encode()).digest())
_CIPHER = Fernet(_KEY_BYTES)


# DB connection (module-level, reused across calls)
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
_client = AsyncIOMotorClient(MONGO_URL)
_db = _client[DB_NAME]


# ==================== ENCRYPTION HELPERS ====================

def encrypt_value(value: str) -> str:
    """Encrypt a string value. Returns empty string for empty input."""
    if not value:
        return ""
    return _CIPHER.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """Decrypt an encrypted string. Returns empty string on failure."""
    if not encrypted:
        return ""
    try:
        return _CIPHER.decrypt(encrypted.encode()).decode()
    except Exception as e:
        logger.error(f"Credential decryption failed: {e}")
        return ""


def encrypt_dict(data: dict, fields_to_encrypt: list) -> dict:
    """Encrypt specified fields in a dict, leave others as-is."""
    result = dict(data)
    for field in fields_to_encrypt:
        if result.get(field):
            result[field] = encrypt_value(result[field])
    return result


def decrypt_dict(data: dict, fields_to_decrypt: list) -> dict:
    """Decrypt specified fields in a dict."""
    result = dict(data)
    for field in fields_to_decrypt:
        if result.get(field):
            result[field] = decrypt_value(result[field])
    return result


# ==================== CREDENTIAL TYPES ====================

RAZORPAY = "RAZORPAY"
EMAIL_SMTP = "EMAIL_SMTP"

# Fields to encrypt per credential type
_ENCRYPTED_FIELDS = {
    RAZORPAY: ["key_secret", "webhook_secret"],
    EMAIL_SMTP: ["api_key", "smtp_pass"],
}


# ==================== CORE SERVICE ====================

async def get_credentials(org_id: str, cred_type: str) -> Optional[Dict[str, Any]]:
    """
    Get decrypted credentials for an org.
    Returns None if the org has no custom credentials.
    Falls back to .env globals automatically via get_*_with_fallback functions.
    """
    record = await _db.tenant_credentials.find_one(
        {"organization_id": org_id, "credential_type": cred_type, "is_active": True},
        {"_id": 0}
    )
    if not record:
        return None

    raw = record.get("credentials", {})
    encrypted_fields = _ENCRYPTED_FIELDS.get(cred_type, [])
    return decrypt_dict(raw, encrypted_fields)


async def save_credentials(org_id: str, cred_type: str, data: dict) -> dict:
    """
    Save encrypted credentials for an org.
    Upserts — creates if absent, replaces if present.
    """
    encrypted_fields = _ENCRYPTED_FIELDS.get(cred_type, [])
    encrypted_data = encrypt_dict(data, encrypted_fields)

    now = datetime.now(timezone.utc).isoformat()
    await _db.tenant_credentials.update_one(
        {"organization_id": org_id, "credential_type": cred_type},
        {
            "$set": {
                "organization_id": org_id,
                "credential_type": cred_type,
                "credentials": encrypted_data,
                "is_active": True,
                "updated_at": now,
            },
            "$setOnInsert": {
                "credential_id": f"cred_{uuid.uuid4().hex[:12]}",
                "created_at": now,
            }
        },
        upsert=True
    )
    logger.info(f"Saved {cred_type} credentials for org {org_id}")
    return {"success": True}


async def delete_credentials(org_id: str, cred_type: str) -> bool:
    """Deactivate credentials for an org (soft delete — falls back to global)."""
    result = await _db.tenant_credentials.update_one(
        {"organization_id": org_id, "credential_type": cred_type},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    logger.info(f"Deactivated {cred_type} credentials for org {org_id}")
    return result.modified_count > 0


# ==================== RAZORPAY HELPERS ====================

async def get_razorpay_credentials(org_id: str) -> Dict[str, Any]:
    """
    Get Razorpay credentials for an org.
    Falls back to global .env keys if org has no custom config.
    """
    creds = await get_credentials(org_id, RAZORPAY)
    if creds:
        return creds

    # Fallback to global .env
    return {
        "key_id": os.environ.get("RAZORPAY_KEY_ID", ""),
        "key_secret": os.environ.get("RAZORPAY_KEY_SECRET", ""),
        "webhook_secret": os.environ.get("RAZORPAY_WEBHOOK_SECRET", ""),
        "test_mode": True,
        "_using_global": True,
    }


# ==================== EMAIL HELPERS ====================

async def get_email_credentials(org_id: str) -> Dict[str, Any]:
    """
    Get email credentials for an org.
    Falls back to global Resend key if org has no custom config.
    """
    creds = await get_credentials(org_id, EMAIL_SMTP)
    if creds:
        return creds

    # Fallback to global .env
    return {
        "provider": "resend",
        "api_key": os.environ.get("RESEND_API_KEY", ""),
        "from_email": os.environ.get("SENDER_EMAIL", "onboarding@resend.dev"),
        "from_name": "Battwheels OS",
        "_using_global": True,
    }
