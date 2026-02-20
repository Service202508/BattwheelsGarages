"""
Battwheels OS - Enhanced Zoho Books Real-Time Sync Service
Provides bidirectional sync with event-driven updates and webhook support
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
import os
import hashlib
import json

logger = logging.getLogger(__name__)


# ============== MODELS ==============

class SyncEntity(BaseModel):
    entity_type: str
    zoho_id: str
    local_id: Optional[str] = None
    organization_id: str
    last_synced: str
    sync_hash: str
    status: str = "synced"  # synced, pending, error
    error_message: Optional[str] = None


class SyncStatus(BaseModel):
    module: str
    last_sync: Optional[str] = None
    records_synced: int = 0
    records_pending: int = 0
    last_error: Optional[str] = None
    status: str = "idle"  # idle, syncing, error


class ZohoWebhookPayload(BaseModel):
    event_type: str  # created, updated, deleted
    module: str
    resource_id: str
    organization_id: str
    timestamp: str
    payload: Optional[Dict] = None


# ============== FIELD MAPPING ==============

# Zoho Books to Battwheels OS field mapping
FIELD_MAPPINGS = {
    "contacts": {
        "zoho_to_local": {
            "contact_id": "zoho_contact_id",
            "contact_name": "contact_name",
            "company_name": "company_name",
            "contact_type": "contact_type",
            "email": "email",
            "phone": "phone",
            "mobile": "mobile",
            "website": "website",
            "billing_address": "billing_address",
            "shipping_address": "shipping_address",
            "gst_no": "gstin",
            "pan_no": "pan",
            "place_of_supply": "place_of_supply",
            "payment_terms": "payment_terms",
            "currency_code": "currency_code",
            "outstanding_receivable_amount": "outstanding_receivable",
            "outstanding_payable_amount": "outstanding_payable",
        },
        "local_to_zoho": {
            "zoho_contact_id": "contact_id",
            "contact_name": "contact_name",
            "company_name": "company_name",
            "contact_type": "contact_type",
            "email": "email",
            "phone": "phone",
            "mobile": "mobile",
            "website": "website",
            "billing_address": "billing_address",
            "shipping_address": "shipping_address",
            "gstin": "gst_no",
            "pan": "pan_no",
            "place_of_supply": "place_of_supply",
            "payment_terms": "payment_terms",
            "currency_code": "currency_code",
        }
    },
    "items": {
        "zoho_to_local": {
            "item_id": "zoho_item_id",
            "name": "name",
            "sku": "sku",
            "description": "description",
            "rate": "rate",
            "purchase_rate": "purchase_rate",
            "unit": "unit",
            "item_type": "item_type",
            "product_type": "product_type",
            "hsn_or_sac": "hsn_code",
            "tax_id": "tax_id",
            "tax_name": "tax_name",
            "tax_percentage": "tax_percentage",
            "stock_on_hand": "stock_on_hand",
            "reorder_level": "reorder_level",
            "initial_stock": "initial_stock",
            "initial_stock_rate": "initial_stock_rate",
        }
    },
    "invoices": {
        "zoho_to_local": {
            "invoice_id": "zoho_invoice_id",
            "invoice_number": "invoice_number",
            "customer_id": "customer_id",
            "customer_name": "customer_name",
            "status": "status",
            "date": "invoice_date",
            "due_date": "due_date",
            "line_items": "line_items",
            "sub_total": "subtotal",           # Normalized field name
            "total": "grand_total",            # Fixed: map to grand_total
            "balance": "balance_due",          # Fixed: map to balance_due
            "currency_code": "currency_code",
            "exchange_rate": "exchange_rate",
            "taxes": "taxes",
            "tax_total": "total_tax",          # Added: tax total field
            "shipping_charge": "shipping_charge",
            "adjustment": "adjustment",
            "discount": "total_discount",      # Fixed: map to total_discount
            "notes": "notes",
            "terms": "terms",
        }
    },
    "bills": {
        "zoho_to_local": {
            "bill_id": "zoho_bill_id",
            "bill_number": "bill_number",
            "vendor_id": "vendor_id",
            "vendor_name": "vendor_name",
            "status": "status",
            "date": "bill_date",
            "due_date": "due_date",
            "line_items": "line_items",
            "sub_total": "subtotal",           # Normalized field name
            "total": "grand_total",            # Fixed: consistent naming
            "balance": "balance_due",          # Fixed: consistent naming
        }
    },
    "estimates": {
        "zoho_to_local": {
            "estimate_id": "zoho_estimate_id",
            "estimate_number": "estimate_number",
            "customer_id": "customer_id",
            "customer_name": "customer_name",
            "status": "status",
            "date": "estimate_date",
            "expiry_date": "expiry_date",
            "line_items": "line_items",
            "sub_total": "subtotal",           # Normalized field name
            "total": "grand_total",            # Fixed: consistent naming
        }
    },
    "taxes": {
        "zoho_to_local": {
            "tax_id": "zoho_tax_id",
            "tax_name": "tax_name",
            "tax_percentage": "tax_percentage",
            "tax_type": "tax_type",
        }
    }
}

# Module to collection mapping
MODULE_COLLECTION_MAP = {
    "contacts": "contacts",
    "items": "items",
    "invoices": "invoices",
    "bills": "bills",
    "estimates": "estimates",
    "expenses": "expenses",
    "customerpayments": "customerpayments",
    "vendorpayments": "vendorpayments",
    "purchaseorders": "purchaseorders",
    "salesorders": "salesorders",
    "creditnotes": "creditnotes",
    "vendorcredits": "vendorcredits",
    "bankaccounts": "bankaccounts",
    "taxes": "taxes",
}


class ZohoRealTimeSyncService:
    """Real-time synchronization service for Zoho Books integration"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.client_id = os.environ.get("ZOHO_CLIENT_ID", "")
        self.client_secret = os.environ.get("ZOHO_CLIENT_SECRET", "")
        self.refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN", "")
        self.base_url = os.environ.get("ZOHO_API_BASE_URL", "https://www.zohoapis.in")
        self.accounts_url = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
        self.zoho_org_id = os.environ.get("ZOHO_ORGANIZATION_ID", "")
        self._access_token = None
        self._token_expiry = None
    
    # ============== OAUTH ==============
    
    async def get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary"""
        now = datetime.now(timezone.utc)
        
        if self._access_token and self._token_expiry and now < self._token_expiry - timedelta(minutes=5):
            return self._access_token
        
        return await self._refresh_access_token()
    
    async def _refresh_access_token(self) -> str:
        """Refresh OAuth access token"""
        url = f"{self.accounts_url}/oauth/v2/token"
        
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Token refresh failed: {error}")
                
                data = await response.json()
                self._access_token = data["access_token"]
                self._token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=data.get("expires_in", 3600)
                )
                return self._access_token
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """Make authenticated request to Zoho Books API"""
        token = await self.get_access_token()
        url = f"{self.base_url}/books/v3/{endpoint}"
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json"
        }
        
        if params is None:
            params = {}
        params["organization_id"] = self.zoho_org_id
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 429:
                        await asyncio.sleep(60)
                        return await self._make_request(method, endpoint, params, data)
                    if response.status != 200:
                        error = await response.text()
                        raise Exception(f"API error: {response.status} - {error}")
                    return await response.json()
            
            elif method == "POST":
                async with session.post(url, headers=headers, params=params, json=data) as response:
                    return await response.json()
            
            elif method == "PUT":
                async with session.put(url, headers=headers, params=params, json=data) as response:
                    return await response.json()
            
            elif method == "DELETE":
                async with session.delete(url, headers=headers, params=params) as response:
                    return await response.json()
        
        return {}
    
    # ============== SYNC HELPERS ==============
    
    def _compute_hash(self, data: Dict) -> str:
        """Compute hash of record for change detection"""
        # Remove volatile fields
        clean_data = {k: v for k, v in data.items() 
                      if k not in ["_id", "synced_at", "last_modified_time", "created_time"]}
        json_str = json.dumps(clean_data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _map_zoho_to_local(self, module: str, zoho_record: Dict) -> Dict:
        """Map Zoho record fields to local schema"""
        mapping = FIELD_MAPPINGS.get(module, {}).get("zoho_to_local", {})
        
        local_record = {}
        for zoho_field, local_field in mapping.items():
            if zoho_field in zoho_record:
                local_record[local_field] = zoho_record[zoho_field]
        
        # Copy unmapped fields as-is
        for key, value in zoho_record.items():
            if key not in mapping and key not in local_record:
                local_record[key] = value
        
        return local_record
    
    async def _update_sync_status(
        self, 
        module: str, 
        organization_id: str,
        status: str,
        records_synced: int = 0,
        error: Optional[str] = None
    ):
        """Update sync status for a module"""
        await self.db.sync_status.update_one(
            {"module": module, "organization_id": organization_id},
            {"$set": {
                "status": status,
                "last_sync": datetime.now(timezone.utc).isoformat(),
                "records_synced": records_synced,
                "last_error": error
            }},
            upsert=True
        )
    
    # ============== SYNC OPERATIONS ==============
    
    async def sync_module(
        self, 
        module: str, 
        organization_id: str,
        full_sync: bool = False
    ) -> Dict:
        """Sync a single module from Zoho Books"""
        collection = MODULE_COLLECTION_MAP.get(module)
        if not collection:
            return {"status": "error", "message": f"Unknown module: {module}"}
        
        await self._update_sync_status(module, organization_id, "syncing")
        
        try:
            # Determine what to fetch
            if full_sync:
                # Fetch all records
                records = await self._fetch_all_records(module)
            else:
                # Fetch only changed records since last sync
                last_sync = await self._get_last_sync_time(module, organization_id)
                records = await self._fetch_changed_records(module, last_sync)
            
            synced_count = 0
            for record in records:
                # Map to local schema
                local_record = self._map_zoho_to_local(module, record)
                local_record["organization_id"] = organization_id
                local_record["source"] = "zoho_books"
                local_record["synced_at"] = datetime.now(timezone.utc).isoformat()
                local_record["sync_hash"] = self._compute_hash(local_record)
                
                # Upsert into local DB
                zoho_id_field = f"zoho_{module.rstrip('s')}_id"
                await self.db[collection].update_one(
                    {zoho_id_field: local_record.get(zoho_id_field)},
                    {"$set": local_record},
                    upsert=True
                )
                synced_count += 1
            
            await self._update_sync_status(module, organization_id, "synced", synced_count)
            
            # Emit sync event for dependent modules
            await self._emit_sync_event(module, organization_id, synced_count)
            
            return {
                "status": "success",
                "module": module,
                "records_synced": synced_count
            }
        
        except Exception as e:
            logger.error(f"Sync failed for {module}: {e}")
            await self._update_sync_status(module, organization_id, "error", error=str(e))
            return {"status": "error", "module": module, "message": str(e)}
    
    async def _fetch_all_records(self, module: str) -> List[Dict]:
        """Fetch all records from a Zoho module with pagination"""
        all_records = []
        page = 1
        
        while True:
            response = await self._make_request("GET", module, {"page": page, "per_page": 200})
            records = response.get(module, [])
            
            if not records:
                break
            
            all_records.extend(records)
            
            page_context = response.get("page_context", {})
            if not page_context.get("has_more_page", False):
                break
            
            page += 1
            await asyncio.sleep(0.5)  # Rate limit protection
        
        return all_records
    
    async def _fetch_changed_records(self, module: str, since: Optional[str]) -> List[Dict]:
        """Fetch records changed since a specific time"""
        params = {"page": 1, "per_page": 200}
        if since:
            params["last_modified_time"] = since
        
        response = await self._make_request("GET", module, params)
        return response.get(module, [])
    
    async def _get_last_sync_time(self, module: str, organization_id: str) -> Optional[str]:
        """Get last sync time for a module"""
        status = await self.db.sync_status.find_one(
            {"module": module, "organization_id": organization_id}
        )
        return status.get("last_sync") if status else None
    
    async def _emit_sync_event(self, module: str, organization_id: str, count: int):
        """Emit event for dependent modules to update"""
        event = {
            "type": "zoho_sync_complete",
            "module": module,
            "organization_id": organization_id,
            "records_synced": count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.sync_events.insert_one(event)
        
        # Update dependent modules
        dependencies = {
            "contacts": ["invoices", "estimates", "bills", "tickets"],
            "items": ["invoices", "estimates", "bills", "inventory"],
            "taxes": ["invoices", "estimates", "bills"],
        }
        
        if module in dependencies:
            for dep_module in dependencies[module]:
                await self.db.sync_status.update_one(
                    {"module": dep_module, "organization_id": organization_id},
                    {"$set": {"dependency_updated": datetime.now(timezone.utc).isoformat()}}
                )
    
    # ============== FULL SYNC ==============
    
    async def run_full_sync(self, organization_id: str) -> Dict:
        """Run full sync of all modules from Zoho Books"""
        sync_id = f"FULLSYNC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Create sync job record
        await self.db.sync_jobs.insert_one({
            "sync_id": sync_id,
            "type": "full_sync",
            "organization_id": organization_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "modules": {}
        })
        
        # Sync order (dependencies first)
        sync_order = [
            "contacts",
            "items", 
            "taxes",
            "estimates",
            "salesorders",
            "invoices",
            "purchaseorders",
            "bills",
            "creditnotes",
            "vendorcredits",
            "customerpayments",
            "vendorpayments",
            "expenses",
            "bankaccounts",
        ]
        
        results = {}
        total_synced = 0
        
        for module in sync_order:
            try:
                result = await self.sync_module(module, organization_id, full_sync=True)
                results[module] = result
                total_synced += result.get("records_synced", 0)
                
                # Update job status
                await self.db.sync_jobs.update_one(
                    {"sync_id": sync_id},
                    {"$set": {f"modules.{module}": result}}
                )
                
            except Exception as e:
                results[module] = {"status": "error", "message": str(e)}
        
        # Finalize job
        await self.db.sync_jobs.update_one(
            {"sync_id": sync_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "total_records_synced": total_synced
            }}
        )
        
        return {
            "sync_id": sync_id,
            "status": "completed",
            "total_records_synced": total_synced,
            "modules": results
        }
    
    # ============== WEBHOOK HANDLING ==============
    
    async def process_webhook(self, payload: ZohoWebhookPayload) -> Dict:
        """Process incoming webhook from Zoho Books"""
        module = payload.module
        collection = MODULE_COLLECTION_MAP.get(module)
        
        if not collection:
            return {"status": "ignored", "reason": f"Unknown module: {module}"}
        
        # Log webhook
        await self.db.webhook_logs.insert_one({
            "received_at": datetime.now(timezone.utc).isoformat(),
            "event_type": payload.event_type,
            "module": payload.module,
            "resource_id": payload.resource_id,
            "payload": payload.payload
        })
        
        try:
            if payload.event_type == "deleted":
                # Remove from local DB
                zoho_id_field = f"zoho_{module.rstrip('s')}_id"
                await self.db[collection].delete_one({zoho_id_field: payload.resource_id})
                
            else:
                # Fetch fresh data from Zoho
                record = await self._fetch_single_record(module, payload.resource_id)
                if record:
                    local_record = self._map_zoho_to_local(module, record)
                    local_record["organization_id"] = payload.organization_id
                    local_record["source"] = "zoho_books"
                    local_record["synced_at"] = datetime.now(timezone.utc).isoformat()
                    
                    zoho_id_field = f"zoho_{module.rstrip('s')}_id"
                    await self.db[collection].update_one(
                        {zoho_id_field: payload.resource_id},
                        {"$set": local_record},
                        upsert=True
                    )
            
            # Emit update event for real-time UI updates
            await self._emit_realtime_update(payload)
            
            return {"status": "processed", "event": payload.event_type, "module": module}
        
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _fetch_single_record(self, module: str, record_id: str) -> Optional[Dict]:
        """Fetch a single record from Zoho Books"""
        singular = module.rstrip('s')
        endpoint = f"{module}/{record_id}"
        
        response = await self._make_request("GET", endpoint)
        return response.get(singular)
    
    async def _emit_realtime_update(self, payload: ZohoWebhookPayload):
        """Emit real-time update event for SSE/WebSocket clients"""
        event = {
            "type": "realtime_update",
            "module": payload.module,
            "event": payload.event_type,
            "resource_id": payload.resource_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.realtime_events.insert_one(event)
    
    # ============== STATUS & MONITORING ==============
    
    async def get_sync_status(self, organization_id: str) -> Dict:
        """Get sync status for all modules"""
        cursor = self.db.sync_status.find(
            {"organization_id": organization_id},
            {"_id": 0}
        )
        statuses = await cursor.to_list(length=None)
        
        return {
            "organization_id": organization_id,
            "modules": {s["module"]: s for s in statuses},
            "last_full_sync": await self._get_last_full_sync(organization_id)
        }
    
    async def _get_last_full_sync(self, organization_id: str) -> Optional[str]:
        """Get timestamp of last full sync"""
        job = await self.db.sync_jobs.find_one(
            {"organization_id": organization_id, "type": "full_sync", "status": "completed"},
            sort=[("completed_at", -1)]
        )
        return job.get("completed_at") if job else None
    
    async def get_sync_history(self, organization_id: str, limit: int = 20) -> List[Dict]:
        """Get recent sync job history"""
        cursor = self.db.sync_jobs.find(
            {"organization_id": organization_id},
            {"_id": 0}
        ).sort("started_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def test_connection(self) -> Dict:
        """Test connection to Zoho Books"""
        try:
            token = await self.get_access_token()
            response = await self._make_request("GET", "organizations")
            
            orgs = response.get("organizations", [])
            
            return {
                "status": "connected",
                "organizations": len(orgs),
                "active_org": self.zoho_org_id,
                "token_valid": True
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "token_valid": False
            }
