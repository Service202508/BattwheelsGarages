"""
Tenant Token Vault Service (Phase F)
====================================

Secure, isolated token storage for third-party integrations per-organization.
Each organization's API tokens (Zoho, Stripe, etc.) are encrypted and isolated.

Security Features:
- Encryption at rest using Fernet
- Organization isolation (no cross-tenant access)
- Token rotation support
- Audit logging of all token operations
- Secure key derivation per-organization

Supported Integrations:
- Zoho Books API
- Stripe
- Razorpay
- Email providers (SendGrid, Resend)
- SMS providers (Twilio)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import logging
import os
import base64
import hashlib
import json

# Try to import cryptography, fallback to simple encoding if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography not installed - using base64 encoding (NOT SECURE FOR PRODUCTION)")

logger = logging.getLogger(__name__)

# Master encryption key (in production, use a secret manager)
VAULT_MASTER_KEY = os.environ.get("VAULT_MASTER_KEY", "battwheels-default-vault-key-change-in-prod")


@dataclass
class TokenEntry:
    """A token entry in the vault"""
    token_id: str
    organization_id: str
    provider: str  # e.g., "zoho", "stripe", "twilio"
    token_type: str  # e.g., "access_token", "refresh_token", "api_key"
    encrypted_value: str
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used_at: Optional[str] = None
    rotation_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "organization_id": self.organization_id,
            "provider": self.provider,
            "token_type": self.token_type,
            "encrypted_value": self.encrypted_value,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_used_at": self.last_used_at,
            "rotation_count": self.rotation_count
        }
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) > expires


class TenantTokenVault:
    """
    Secure token vault with per-organization isolation.
    
    Each organization's tokens are:
    - Encrypted with a derived key unique to the org
    - Stored in a separate namespace
    - Never accessible to other organizations
    """
    
    def __init__(self, db, master_key: str = VAULT_MASTER_KEY):
        self.db = db
        self.collection = db.token_vault
        self.master_key = master_key
        self._key_cache: Dict[str, bytes] = {}
    
    def _derive_org_key(self, organization_id: str) -> bytes:
        """Derive a unique encryption key for each organization"""
        if organization_id in self._key_cache:
            return self._key_cache[organization_id]
        
        if CRYPTO_AVAILABLE:
            # Use PBKDF2 for secure key derivation
            salt = hashlib.sha256(organization_id.encode()).digest()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        else:
            # Fallback: simple hash-based key (NOT SECURE)
            combined = f"{self.master_key}:{organization_id}"
            key = base64.urlsafe_b64encode(hashlib.sha256(combined.encode()).digest())
        
        self._key_cache[organization_id] = key
        return key
    
    def _encrypt(self, value: str, organization_id: str) -> str:
        """Encrypt a value using the org's derived key"""
        key = self._derive_org_key(organization_id)
        
        if CRYPTO_AVAILABLE:
            f = Fernet(key)
            encrypted = f.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        else:
            # Fallback: base64 encoding only (NOT SECURE)
            return base64.urlsafe_b64encode(value.encode()).decode()
    
    def _decrypt(self, encrypted_value: str, organization_id: str) -> str:
        """Decrypt a value using the org's derived key"""
        key = self._derive_org_key(organization_id)
        
        if CRYPTO_AVAILABLE:
            f = Fernet(key)
            decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_value))
            return decrypted.decode()
        else:
            # Fallback: base64 decoding only
            return base64.urlsafe_b64decode(encrypted_value).decode()
    
    async def store_token(
        self,
        organization_id: str,
        provider: str,
        token_type: str,
        token_value: str,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenEntry:
        """
        Store a token securely in the vault.
        
        Args:
            organization_id: Organization ID (REQUIRED)
            provider: Integration provider (zoho, stripe, etc.)
            token_type: Type of token (access_token, refresh_token, api_key)
            token_value: The actual token value (will be encrypted)
            expires_at: Optional expiration datetime
            metadata: Additional metadata
        
        Returns:
            Created TokenEntry
        """
        if not organization_id:
            raise ValueError("organization_id is required for token storage")
        
        import uuid
        token_id = f"tok_{uuid.uuid4().hex[:12]}"
        
        # Encrypt the token
        encrypted = self._encrypt(token_value, organization_id)
        
        entry = TokenEntry(
            token_id=token_id,
            organization_id=organization_id,
            provider=provider,
            token_type=token_type,
            encrypted_value=encrypted,
            expires_at=expires_at.isoformat() if expires_at else None,
            metadata=metadata or {}
        )
        
        # Upsert by org + provider + token_type
        await self.collection.update_one(
            {
                "organization_id": organization_id,
                "provider": provider,
                "token_type": token_type
            },
            {"$set": entry.to_dict()},
            upsert=True
        )
        
        logger.info(f"Stored {provider}/{token_type} token for org {organization_id}")
        return entry
    
    async def get_token(
        self,
        organization_id: str,
        provider: str,
        token_type: str
    ) -> Optional[str]:
        """
        Retrieve and decrypt a token.
        
        Returns the decrypted token value, or None if not found.
        Updates last_used_at timestamp.
        """
        if not organization_id:
            raise ValueError("organization_id is required")
        
        doc = await self.collection.find_one(
            {
                "organization_id": organization_id,
                "provider": provider,
                "token_type": token_type
            },
            {"_id": 0}
        )
        
        if not doc:
            return None
        
        # Check expiration
        if doc.get("expires_at"):
            expires = datetime.fromisoformat(doc["expires_at"].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires:
                logger.warning(f"Token {provider}/{token_type} for org {organization_id} is expired")
                return None
        
        # Update last_used_at
        await self.collection.update_one(
            {"token_id": doc["token_id"]},
            {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Decrypt and return
        return self._decrypt(doc["encrypted_value"], organization_id)
    
    async def rotate_token(
        self,
        organization_id: str,
        provider: str,
        token_type: str,
        new_value: str,
        new_expires_at: Optional[datetime] = None
    ) -> Optional[TokenEntry]:
        """
        Rotate a token with a new value.
        
        Increments rotation_count for audit purposes.
        """
        if not organization_id:
            raise ValueError("organization_id is required")
        
        # Get existing entry
        doc = await self.collection.find_one(
            {
                "organization_id": organization_id,
                "provider": provider,
                "token_type": token_type
            },
            {"_id": 0}
        )
        
        if not doc:
            # Create new if doesn't exist
            return await self.store_token(
                organization_id, provider, token_type, new_value, new_expires_at
            )
        
        # Encrypt new value
        encrypted = self._encrypt(new_value, organization_id)
        
        # Update with rotation tracking
        now = datetime.now(timezone.utc).isoformat()
        await self.collection.update_one(
            {"token_id": doc["token_id"]},
            {
                "$set": {
                    "encrypted_value": encrypted,
                    "expires_at": new_expires_at.isoformat() if new_expires_at else None,
                    "updated_at": now
                },
                "$inc": {"rotation_count": 1}
            }
        )
        
        logger.info(f"Rotated {provider}/{token_type} token for org {organization_id}")
        
        # Return updated entry
        updated = await self.collection.find_one({"token_id": doc["token_id"]}, {"_id": 0})
        return TokenEntry(**updated) if updated else None
    
    async def delete_token(
        self,
        organization_id: str,
        provider: str,
        token_type: str
    ) -> bool:
        """Delete a token from the vault"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        result = await self.collection.delete_one({
            "organization_id": organization_id,
            "provider": provider,
            "token_type": token_type
        })
        
        if result.deleted_count > 0:
            logger.info(f"Deleted {provider}/{token_type} token for org {organization_id}")
            return True
        return False
    
    async def list_tokens(
        self,
        organization_id: str,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List tokens for an organization (without values).
        
        Returns metadata only, never the actual token values.
        """
        if not organization_id:
            raise ValueError("organization_id is required")
        
        query = {"organization_id": organization_id}
        if provider:
            query["provider"] = provider
        
        # Exclude encrypted_value from results
        docs = await self.collection.find(
            query,
            {"_id": 0, "encrypted_value": 0}
        ).to_list(100)
        
        return docs
    
    async def get_provider_status(
        self,
        organization_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """Get status of all tokens for a provider"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        docs = await self.collection.find(
            {"organization_id": organization_id, "provider": provider},
            {"_id": 0, "encrypted_value": 0}
        ).to_list(10)
        
        tokens_status = []
        for doc in docs:
            is_expired = False
            if doc.get("expires_at"):
                expires = datetime.fromisoformat(doc["expires_at"].replace('Z', '+00:00'))
                is_expired = datetime.now(timezone.utc) > expires
            
            tokens_status.append({
                "token_type": doc["token_type"],
                "is_expired": is_expired,
                "last_used_at": doc.get("last_used_at"),
                "rotation_count": doc.get("rotation_count", 0)
            })
        
        return {
            "organization_id": organization_id,
            "provider": provider,
            "tokens": tokens_status,
            "is_configured": len(tokens_status) > 0
        }


# ==================== ZOHO SYNC TENANT INTEGRATION ====================

class TenantZohoSyncService:
    """
    Tenant-isolated Zoho Books synchronization service.
    
    Each organization has its own:
    - API tokens (stored in vault)
    - Sync state
    - Webhook configuration
    """
    
    def __init__(self, db, vault: TenantTokenVault):
        self.db = db
        self.vault = vault
        self.sync_state_collection = db.zoho_sync_state
    
    async def configure_zoho(
        self,
        organization_id: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        zoho_org_id: str
    ) -> Dict[str, Any]:
        """
        Configure Zoho Books integration for an organization.
        
        Stores credentials securely in the vault.
        """
        # Store tokens in vault
        await self.vault.store_token(
            organization_id, "zoho", "client_id", client_id
        )
        await self.vault.store_token(
            organization_id, "zoho", "client_secret", client_secret
        )
        await self.vault.store_token(
            organization_id, "zoho", "refresh_token", refresh_token
        )
        await self.vault.store_token(
            organization_id, "zoho", "zoho_org_id", zoho_org_id
        )
        
        # Initialize sync state
        now = datetime.now(timezone.utc).isoformat()
        await self.sync_state_collection.update_one(
            {"organization_id": organization_id},
            {
                "$set": {
                    "organization_id": organization_id,
                    "configured_at": now,
                    "status": "configured",
                    "modules": {}
                }
            },
            upsert=True
        )
        
        logger.info(f"Configured Zoho Books for organization {organization_id}")
        
        return {
            "status": "configured",
            "organization_id": organization_id,
            "configured_at": now
        }
    
    async def get_sync_status(self, organization_id: str) -> Dict[str, Any]:
        """Get Zoho sync status for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        state = await self.sync_state_collection.find_one(
            {"organization_id": organization_id},
            {"_id": 0}
        )
        
        if not state:
            return {
                "organization_id": organization_id,
                "status": "not_configured",
                "is_configured": False
            }
        
        # Get token status
        token_status = await self.vault.get_provider_status(organization_id, "zoho")
        
        return {
            "organization_id": organization_id,
            "status": state.get("status", "unknown"),
            "is_configured": token_status.get("is_configured", False),
            "configured_at": state.get("configured_at"),
            "last_sync": state.get("last_sync"),
            "modules": state.get("modules", {})
        }
    
    async def disconnect_zoho(self, organization_id: str) -> bool:
        """Remove Zoho integration for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        # Delete all Zoho tokens
        for token_type in ["client_id", "client_secret", "refresh_token", "access_token", "zoho_org_id"]:
            await self.vault.delete_token(organization_id, "zoho", token_type)
        
        # Clear sync state
        await self.sync_state_collection.delete_one({"organization_id": organization_id})
        
        logger.info(f"Disconnected Zoho Books for organization {organization_id}")
        return True


# ==================== SERVICE SINGLETON ====================

_token_vault: Optional[TenantTokenVault] = None
_zoho_sync: Optional[TenantZohoSyncService] = None


def init_tenant_token_vault(db, master_key: str = VAULT_MASTER_KEY) -> TenantTokenVault:
    """Initialize the tenant token vault singleton"""
    global _token_vault, _zoho_sync
    _token_vault = TenantTokenVault(db, master_key)
    _zoho_sync = TenantZohoSyncService(db, _token_vault)
    logger.info("TenantTokenVault initialized (Phase F)")
    return _token_vault


def get_tenant_token_vault() -> TenantTokenVault:
    """Get the tenant token vault singleton"""
    if _token_vault is None:
        raise RuntimeError("TenantTokenVault not initialized")
    return _token_vault


def get_tenant_zoho_sync() -> TenantZohoSyncService:
    """Get the tenant Zoho sync service singleton"""
    if _zoho_sync is None:
        raise RuntimeError("TenantZohoSyncService not initialized")
    return _zoho_sync
