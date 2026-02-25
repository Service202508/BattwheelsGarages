"""
Zoho Books Live Sync Service
Connects to actual Zoho Books account and syncs data to MongoDB
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import aiohttp
import os
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/zoho-sync", tags=["zoho-sync"])

# Database connection
def get_db():
    from server import db
    return db

# ============== OAUTH TOKEN MANAGEMENT ==============

class ZohoOAuth:
    """Manages Zoho OAuth tokens with automatic refresh"""
    
    def __init__(self):
        self.client_id = os.environ.get("ZOHO_CLIENT_ID", "")
        self.client_secret = os.environ.get("ZOHO_CLIENT_SECRET", "")
        self.refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN", "")
        self.base_url = os.environ.get("ZOHO_API_BASE_URL", "https://www.zohoapis.in")
        self.accounts_url = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
        self.access_token = None
        self.token_expiry = None
        self.organization_id = os.environ.get("ZOHO_ORGANIZATION_ID", "")
    
    async def get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary"""
        now = datetime.now(timezone.utc)
        
        # Return cached token if still valid (with 5-min buffer)
        if self.access_token and self.token_expiry and now < self.token_expiry - timedelta(minutes=5):
            return self.access_token
        
        # Refresh the token
        return await self._refresh_token()
    
    async def _refresh_token(self) -> str:
        """Refresh access token using refresh token"""
        url = f"{self.accounts_url}/oauth/v2/token"
        
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Token refresh failed: {error_text}")
                        raise Exception(f"Failed to refresh token: {response.status} - {error_text}")
                    
                    data = await response.json()
                    
                    if "error" in data:
                        raise Exception(f"OAuth error: {data.get('error')}")
                    
                    self.access_token = data["access_token"]
                    expires_in = data.get("expires_in", 3600)
                    self.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    
                    logger.info(f"Zoho token refreshed, valid until {self.token_expiry}")
                    return self.access_token
        
        except Exception as e:
            logger.error(f"Error refreshing Zoho token: {e}")
            raise
    
    async def get_organization_id(self) -> str:
        """Fetch organization ID from Zoho Books"""
        if self.organization_id:
            return self.organization_id
        
        access_token = await self.get_access_token()
        url = f"{self.base_url}/books/v3/organizations"
        
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to get organizations: {error_text}")
                    
                    data = await response.json()
                    orgs = data.get("organizations", [])
                    
                    if not orgs:
                        raise Exception("No organizations found in Zoho Books account")
                    
                    # Use first organization (or the one marked as primary)
                    for org in orgs:
                        if org.get("is_default_org", False):
                            self.organization_id = org["organization_id"]
                            break
                    
                    if not self.organization_id:
                        self.organization_id = orgs[0]["organization_id"]
                    
                    logger.info(f"Using Zoho Organization ID: {self.organization_id}")
                    return self.organization_id
        
        except Exception as e:
            logger.error(f"Error getting organization ID: {e}")
            raise

# Global OAuth instance
zoho_oauth = ZohoOAuth()

# ============== ZOHO BOOKS API CLIENT ==============

class ZohoBooksClient:
    """Client for Zoho Books API operations"""
    
    def __init__(self, oauth: ZohoOAuth):
        self.oauth = oauth
        self.base_url = oauth.base_url
    
    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Zoho Books API"""
        access_token = await self.oauth.get_access_token()
        org_id = await self.oauth.get_organization_id()
        
        url = f"{self.base_url}/books/v3/{endpoint}"
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        
        if params is None:
            params = {}
        params["organization_id"] = org_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 429:
                        logger.warning("Rate limit hit, waiting 60 seconds...")
                        await asyncio.sleep(60)
                        return await self._request(endpoint, params)
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error for {endpoint}: {response.status} - {error_text}")
                        raise Exception(f"API error: {response.status}")
                    
                    return await response.json()
        
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            raise
    
    async def fetch_all_pages(self, endpoint: str, items_key: str, extra_params: Optional[Dict] = None) -> List[Dict]:
        """Fetch all pages of data from an endpoint"""
        all_items = []
        page = 1
        
        while True:
            params = {"page": page, "per_page": 200}
            if extra_params:
                params.update(extra_params)
            
            try:
                response = await self._request(endpoint, params)
                items = response.get(items_key, [])
                
                if not items:
                    break
                
                all_items.extend(items)
                logger.info(f"Fetched page {page} of {endpoint}: {len(items)} items")
                
                # Check for more pages
                page_context = response.get("page_context", {})
                if not page_context.get("has_more_page", False):
                    break
                
                page += 1
                
                # Rate limit protection - wait between pages
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Error fetching page {page} of {endpoint}: {e}")
                break
        
        return all_items
    
    # Specific API methods
    async def get_contacts(self, contact_type: str = None) -> List[Dict]:
        params = {}
        if contact_type:
            params["contact_type"] = contact_type
        return await self.fetch_all_pages("contacts", "contacts", params)
    
    async def get_items(self) -> List[Dict]:
        return await self.fetch_all_pages("items", "items")
    
    async def get_invoices(self) -> List[Dict]:
        return await self.fetch_all_pages("invoices", "invoices")
    
    async def get_bills(self) -> List[Dict]:
        return await self.fetch_all_pages("bills", "bills")
    
    async def get_estimates(self) -> List[Dict]:
        return await self.fetch_all_pages("estimates", "estimates")
    
    async def get_expenses(self) -> List[Dict]:
        return await self.fetch_all_pages("expenses", "expenses")
    
    async def get_customer_payments(self) -> List[Dict]:
        return await self.fetch_all_pages("customerpayments", "customerpayments")
    
    async def get_vendor_payments(self) -> List[Dict]:
        return await self.fetch_all_pages("vendorpayments", "vendorpayments")
    
    async def get_purchase_orders(self) -> List[Dict]:
        return await self.fetch_all_pages("purchaseorders", "purchaseorders")
    
    async def get_sales_orders(self) -> List[Dict]:
        return await self.fetch_all_pages("salesorders", "salesorders")
    
    async def get_credit_notes(self) -> List[Dict]:
        return await self.fetch_all_pages("creditnotes", "creditnotes")
    
    async def get_vendor_credits(self) -> List[Dict]:
        return await self.fetch_all_pages("vendorcredits", "vendorcredits")
    
    async def get_bank_accounts(self) -> List[Dict]:
        return await self.fetch_all_pages("bankaccounts", "bankaccounts")

# Global client instance
zoho_client = ZohoBooksClient(zoho_oauth)

# ============== SYNC ENDPOINTS ==============

class SyncStatus(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None

@router.get("/test-connection")
async def test_zoho_connection():
    """Test connection to Zoho Books API"""
    try:
        # Try to get access token
        access_token = await zoho_oauth.get_access_token()
        
        # Try to get organization
        org_id = await zoho_oauth.get_organization_id()
        
        return {
            "code": 0,
            "status": "connected",
            "message": "Successfully connected to Zoho Books",
            "organization_id": org_id,
            "token_valid": True
        }
    
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organizations")
async def get_organizations():
    """Get list of organizations in Zoho Books account"""
    try:
        access_token = await zoho_oauth.get_access_token()
        url = f"{zoho_oauth.base_url}/books/v3/organizations"
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                return {"code": 0, "organizations": data.get("organizations", [])}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/contacts")
async def import_contacts():
    """Import all contacts from Zoho Books"""
    db = get_db()
    
    try:
        customers = await zoho_client.get_contacts("customer")
        vendors = await zoho_client.get_contacts("vendor")
        
        all_contacts = customers + vendors
        imported = 0
        
        for contact in all_contacts:
            # Add source tracking
            contact["source"] = "zoho_books"
            contact["zoho_contact_id"] = contact.get("contact_id")
            contact["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.contacts.update_one(
                {"zoho_contact_id": contact["contact_id"]},
                {"$set": contact},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} contacts ({len(customers)} customers, {len(vendors)} vendors)"
        }
    
    except Exception as e:
        logger.error(f"Contact import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/items")
async def import_items():
    """Import all items from Zoho Books"""
    db = get_db()
    
    try:
        items = await zoho_client.get_items()
        imported = 0
        
        for item in items:
            item["source"] = "zoho_books"
            item["zoho_item_id"] = item.get("item_id")
            item["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.items.update_one(
                {"zoho_item_id": item["item_id"]},
                {"$set": item},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success", 
            "message": f"Imported {imported} items"
        }
    
    except Exception as e:
        logger.error(f"Items import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/invoices")
async def import_invoices():
    """Import all invoices from Zoho Books"""
    db = get_db()
    
    try:
        invoices = await zoho_client.get_invoices()
        imported = 0
        
        for invoice in invoices:
            invoice["source"] = "zoho_books"
            invoice["zoho_invoice_id"] = invoice.get("invoice_id")
            invoice["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.invoices.update_one(
                {"zoho_invoice_id": invoice["invoice_id"]},
                {"$set": invoice},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} invoices"
        }
    
    except Exception as e:
        logger.error(f"Invoices import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/bills")
async def import_bills():
    """Import all bills from Zoho Books"""
    db = get_db()
    
    try:
        bills = await zoho_client.get_bills()
        imported = 0
        
        for bill in bills:
            bill["source"] = "zoho_books"
            bill["zoho_bill_id"] = bill.get("bill_id")
            bill["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.bills.update_one(
                {"zoho_bill_id": bill["bill_id"]},
                {"$set": bill},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} bills"
        }
    
    except Exception as e:
        logger.error(f"Bills import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/estimates")
async def import_estimates():
    """Import all estimates from Zoho Books"""
    db = get_db()
    
    try:
        estimates = await zoho_client.get_estimates()
        imported = 0
        
        for estimate in estimates:
            estimate["source"] = "zoho_books"
            estimate["zoho_estimate_id"] = estimate.get("estimate_id")
            estimate["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.estimates.update_one(
                {"zoho_estimate_id": estimate["estimate_id"]},
                {"$set": estimate},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} estimates"
        }
    
    except Exception as e:
        logger.error(f"Estimates import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/expenses")
async def import_expenses():
    """Import all expenses from Zoho Books"""
    db = get_db()
    
    try:
        expenses = await zoho_client.get_expenses()
        imported = 0
        
        for expense in expenses:
            expense["source"] = "zoho_books"
            expense["zoho_expense_id"] = expense.get("expense_id")
            expense["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.expenses.update_one(
                {"zoho_expense_id": expense["expense_id"]},
                {"$set": expense},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} expenses"
        }
    
    except Exception as e:
        logger.error(f"Expenses import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/payments")
async def import_payments():
    """Import all payments from Zoho Books"""
    db = get_db()
    
    try:
        customer_payments = await zoho_client.get_customer_payments()
        vendor_payments = await zoho_client.get_vendor_payments()
        
        imported_customer = 0
        imported_vendor = 0
        
        for payment in customer_payments:
            payment["source"] = "zoho_books"
            payment["zoho_payment_id"] = payment.get("payment_id")
            payment["payment_type"] = "customer"
            payment["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.customerpayments.update_one(
                {"zoho_payment_id": payment["payment_id"]},
                {"$set": payment},
                upsert=True
            )
            imported_customer += 1
        
        for payment in vendor_payments:
            payment["source"] = "zoho_books"
            payment["zoho_payment_id"] = payment.get("payment_id")
            payment["payment_type"] = "vendor"
            payment["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.vendorpayments.update_one(
                {"zoho_payment_id": payment["payment_id"]},
                {"$set": payment},
                upsert=True
            )
            imported_vendor += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported_customer} customer payments, {imported_vendor} vendor payments"
        }
    
    except Exception as e:
        logger.error(f"Payments import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/purchase-orders")
async def import_purchase_orders():
    """Import all purchase orders from Zoho Books"""
    db = get_db()
    
    try:
        pos = await zoho_client.get_purchase_orders()
        imported = 0
        
        for po in pos:
            po["source"] = "zoho_books"
            po["zoho_purchaseorder_id"] = po.get("purchaseorder_id")
            po["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.purchaseorders.update_one(
                {"zoho_purchaseorder_id": po["purchaseorder_id"]},
                {"$set": po},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} purchase orders"
        }
    
    except Exception as e:
        logger.error(f"Purchase orders import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/sales-orders")
async def import_sales_orders():
    """Import all sales orders from Zoho Books"""
    db = get_db()
    
    try:
        sos = await zoho_client.get_sales_orders()
        imported = 0
        
        for so in sos:
            so["source"] = "zoho_books"
            so["zoho_salesorder_id"] = so.get("salesorder_id")
            so["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.salesorders.update_one(
                {"zoho_salesorder_id": so["salesorder_id"]},
                {"$set": so},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} sales orders"
        }
    
    except Exception as e:
        logger.error(f"Sales orders import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/credit-notes")
async def import_credit_notes():
    """Import all credit notes from Zoho Books"""
    db = get_db()
    
    try:
        cns = await zoho_client.get_credit_notes()
        imported = 0
        
        for cn in cns:
            cn["source"] = "zoho_books"
            cn["zoho_creditnote_id"] = cn.get("creditnote_id")
            cn["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.creditnotes.update_one(
                {"zoho_creditnote_id": cn["creditnote_id"]},
                {"$set": cn},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} credit notes"
        }
    
    except Exception as e:
        logger.error(f"Credit notes import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/bank-accounts")
async def import_bank_accounts():
    """Import all bank accounts from Zoho Books"""
    db = get_db()
    
    try:
        accounts = await zoho_client.get_bank_accounts()
        imported = 0
        
        for account in accounts:
            account["source"] = "zoho_books"
            account["zoho_account_id"] = account.get("account_id")
            account["synced_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.bankaccounts.update_one(
                {"zoho_account_id": account["account_id"]},
                {"$set": account},
                upsert=True
            )
            imported += 1
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Imported {imported} bank accounts"
        }
    
    except Exception as e:
        logger.error(f"Bank accounts import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== FULL IMPORT ==============

@router.post("/import/all")
async def import_all_data(background_tasks: BackgroundTasks):
    """Import all data from Zoho Books (runs in background)"""
    db = get_db()
    
    # Create sync log
    sync_id = f"SYNC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    await db.sync_logs.insert_one({
        "sync_id": sync_id,
        "status": "started",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "type": "full_import"
    })
    
    # Run import in background
    background_tasks.add_task(run_full_import, sync_id)
    
    return {
        "code": 0,
        "status": "started",
        "message": "Full import started in background",
        "sync_id": sync_id
    }

async def run_full_import(sync_id: str):
    """Execute full import from Zoho Books"""
    db = get_db()
    results = {}
    
    try:
        logger.info(f"Starting full Zoho Books import: {sync_id}")
        
        # Import in order of dependencies
        import_tasks = [
            ("contacts", import_contacts),
            ("items", import_items),
            ("estimates", import_estimates),
            ("sales_orders", import_sales_orders),
            ("invoices", import_invoices),
            ("purchase_orders", import_purchase_orders),
            ("bills", import_bills),
            ("credit_notes", import_credit_notes),
            ("expenses", import_expenses),
            ("payments", import_payments),
            ("bank_accounts", import_bank_accounts),
        ]
        
        for name, func in import_tasks:
            try:
                result = await func()
                results[name] = result
                logger.info(f"Imported {name}: {result.get('message', 'done')}")
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
                logger.error(f"Error importing {name}: {e}")
        
        # Update sync log
        await db.sync_logs.update_one(
            {"sync_id": sync_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "results": results
            }}
        )
        
        logger.info(f"Full import completed: {sync_id}")
    
    except Exception as e:
        logger.error(f"Full import failed: {e}")
        await db.sync_logs.update_one(
            {"sync_id": sync_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )

@router.get("/import/status/{sync_id}")
async def get_import_status(sync_id: str):
    """Get status of a sync operation"""
    db = get_db()
    
    sync_log = await db.sync_logs.find_one({"sync_id": sync_id}, {"_id": 0})
    
    if not sync_log:
        raise HTTPException(status_code=404, detail="Sync not found")
    
    return {"code": 0, "sync": sync_log}

@router.get("/import/history")
async def get_import_history(limit: int = 10):
    """Get recent sync history"""
    db = get_db()
    
    cursor = db.sync_logs.find({}, {"_id": 0}).sort("started_at", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    return {"code": 0, "sync_logs": logs}


# ============== DISCONNECT & PURGE ==============

class DisconnectRequest(BaseModel):
    confirm: bool = False

@router.post("/disconnect-and-purge")
async def disconnect_and_purge(request: Request, body: DisconnectRequest):
    """
    Disconnect from Zoho Books and purge synced data FOR THIS ORGANIZATION ONLY.
    This is a destructive operation that cannot be undone.
    """
    if not body.confirm:
        return {
            "code": 1,
            "message": "Confirmation required. Set confirm=true to proceed."
        }
    
    # CRITICAL: Get org_id from authenticated tenant context
    org_id = getattr(request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
    # Environment gate: block in production unless explicitly enabled
    env = os.environ.get("ENVIRONMENT", "development")
    if env == "production" and not os.environ.get("ALLOW_PRODUCTION_PURGE"):
        raise HTTPException(
            status_code=403,
            detail="Purge operations blocked in production. Set ALLOW_PRODUCTION_PURGE=1 to override."
        )
    
    db = get_db()
    purge_stats = {}
    
    try:
        logger.info(f"Starting Zoho Books disconnect and data purge for org {org_id}...")
        
        # ALL collections are scoped by organization_id.
        # Collections with Zoho source get an additional source filter.
        collections_to_purge = [
            # Primary business data (source-filtered + org-scoped)
            ("contacts", {"organization_id": org_id, "source": "zoho_books"}),
            ("contacts_enhanced", {"organization_id": org_id, "source": "zoho_books"}),
            ("customers", {"organization_id": org_id, "source": "zoho_books"}),
            ("suppliers", {"organization_id": org_id, "source": "zoho_books"}),
            ("items", {"organization_id": org_id, "source": "zoho_books"}),
            ("invoices", {"organization_id": org_id, "source": "zoho_books"}),
            ("invoices_enhanced", {"organization_id": org_id, "source": "zoho_books"}),
            ("estimates", {"organization_id": org_id, "source": "zoho_books"}),
            ("estimates_enhanced", {"organization_id": org_id, "source": "zoho_books"}),
            ("bills", {"organization_id": org_id, "source": "zoho_books"}),
            ("bills_enhanced", {"organization_id": org_id, "source": "zoho_books"}),
            ("expenses", {"organization_id": org_id, "source": "zoho_books"}),
            ("purchaseorders", {"organization_id": org_id, "source": "zoho_books"}),
            ("purchase_orders", {"organization_id": org_id, "source": "zoho_books"}),
            ("purchase_orders_enhanced", {"organization_id": org_id, "source": "zoho_books"}),
            ("salesorders", {"organization_id": org_id, "source": "zoho_books"}),
            ("sales_orders", {"organization_id": org_id, "source": "zoho_books"}),
            ("salesorders_enhanced", {"organization_id": org_id, "source": "zoho_books"}),
            ("creditnotes", {"organization_id": org_id, "source": "zoho_books"}),
            ("vendorcredits", {"organization_id": org_id, "source": "zoho_books"}),
            ("customerpayments", {"organization_id": org_id, "source": "zoho_books"}),
            ("vendorpayments", {"organization_id": org_id, "source": "zoho_books"}),
            ("payments", {"organization_id": org_id, "source": "zoho_books"}),
            ("bankaccounts", {"organization_id": org_id, "source": "zoho_books"}),
            ("bank_accounts", {"organization_id": org_id, "source": "zoho_books"}),
            
            # Line items and related data (org-scoped only)
            ("invoice_line_items", {"organization_id": org_id}),
            ("estimate_line_items", {"organization_id": org_id}),
            ("bill_line_items", {"organization_id": org_id}),
            ("salesorder_line_items", {"organization_id": org_id}),
            ("po_line_items", {"organization_id": org_id}),
            
            # History and audit logs (org-scoped only)
            ("invoice_history", {"organization_id": org_id}),
            ("estimate_history", {"organization_id": org_id}),
            ("bill_history", {"organization_id": org_id}),
            ("salesorder_history", {"organization_id": org_id}),
            ("contact_history", {"organization_id": org_id}),
            ("item_history", {"organization_id": org_id}),
            
            # Sync-related collections (org-scoped)
            ("sync_logs", {"organization_id": org_id}),
            ("sync_status", {"organization_id": org_id}),
            ("sync_events", {"organization_id": org_id}),
            ("sync_jobs", {"organization_id": org_id}),
            
            # Books-specific collections (org-scoped)
            ("books_customers", {"organization_id": org_id}),
            ("books_invoices", {"organization_id": org_id}),
            ("books_payments", {"organization_id": org_id}),
            ("books_vendors", {"organization_id": org_id}),
            
            # Item-related from sync (source + org scoped)
            ("item_prices", {"organization_id": org_id, "source": "zoho_books"}),
            ("item_stock", {"organization_id": org_id}),
            ("item_stock_locations", {"organization_id": org_id}),
            ("item_batch_numbers", {"organization_id": org_id}),
            ("item_serial_numbers", {"organization_id": org_id}),
            ("item_serial_batches", {"organization_id": org_id}),
            
            # Payments and financial data (org-scoped)
            ("payments_received", {"organization_id": org_id}),
            ("payment_history", {"organization_id": org_id}),
            ("invoice_payments", {"organization_id": org_id}),
            ("bill_payments", {"organization_id": org_id}),
        ]
        
        # Perform the purge — every query is org-scoped
        for collection_name, filter_query in collections_to_purge:
            try:
                result = await db[collection_name].delete_many(filter_query)
                if result.deleted_count > 0:
                    purge_stats[collection_name] = result.deleted_count
                    logger.info(f"Purged {result.deleted_count} records from {collection_name} for org {org_id}")
            except Exception as e:
                logger.warning(f"Error purging {collection_name}: {e}")
        
        # Clear backup collections scoped to this org (delete docs, never drop)
        all_collections = await db.list_collection_names()
        backup_deleted = 0
        for coll in all_collections:
            if coll.startswith("_backup_"):
                try:
                    r = await db[coll].delete_many({"organization_id": org_id})
                    backup_deleted += r.deleted_count
                except Exception:
                    pass
        if backup_deleted > 0:
            purge_stats["backup_records_deleted"] = backup_deleted
        
        # Log the disconnect event (org-scoped)
        await db.sync_logs.insert_one({
            "sync_id": f"DISCONNECT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "organization_id": org_id,
            "type": "disconnect_and_purge",
            "status": "completed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "purge_stats": purge_stats
        })
        
        logger.info(f"Zoho Books disconnect completed for org {org_id}. Stats: {purge_stats}")
        
        return {
            "code": 0,
            "status": "success",
            "message": f"Zoho Books disconnected and data purged for organization {org_id}",
            "purge_stats": purge_stats
        }
    
    except Exception as e:
        logger.error(f"Disconnect and purge failed for org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

