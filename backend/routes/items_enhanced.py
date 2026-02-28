"""
Enhanced Items Module for Battwheels OS
Zoho Books-style comprehensive item management with:
- Item Groups (Categories) with hierarchy
- Multi-Warehouse inventory tracking
- Inventory Adjustments (Quantity & Value) with audit trail
- Multiple Price Lists (Sales/Purchase) with Markup/Markdown
- Custom Fields support
- GST/HSN/SAC integration with validation
- Import/Export (CSV/XLS)
- Bulk Actions
- Item History Tracking
- Low stock alerts & reorder notifications
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
import re
import csv
import io
import json
import base64

# Import tenant context for multi-tenant scoping
from core.tenant.context import TenantContext, tenant_context_required, optional_tenant_context
from utils.database import extract_org_id

router = APIRouter(prefix="/items-enhanced", tags=["Items Enhanced"])

# Database connection
def get_db():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]

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

# ============== PYDANTIC MODELS ==============

class ItemGroupCreate(BaseModel):
    name: str
    description: str = ""
    parent_group_id: Optional[str] = None
    is_active: bool = True

class WarehouseCreate(BaseModel):
    name: str
    location: str = ""
    is_primary: bool = False
    is_active: bool = True

class ItemCreate(BaseModel):
    """Enhanced item creation model - Full Zoho Books CSV compatibility
    
    Columns supported:
    Item ID, Item Name, SKU, HSN/SAC, Description, Rate, Account, Account Code,
    Taxable, Exemption Reason, Taxability Type, Product Type,
    Intra State Tax Name/Rate/Type, Inter State Tax Name/Rate/Type,
    Source, Reference ID, Last Sync Time, Status, Usage unit, Unit Name,
    Purchase Rate, Purchase Account, Purchase Account Code, Purchase Description,
    Inventory Account, Inventory Account Code, Inventory Valuation Method,
    Reorder Point, Vendor, Location Name, Opening Stock, Opening Stock Value,
    Stock On Hand, Item Type, Sellable, Purchasable, Track Inventory
    """
    # Basic Info
    name: str = Field(..., alias="Item Name")
    sku: Optional[str] = Field(None, alias="SKU")
    description: str = Field("", alias="Description")
    item_type: str = Field("inventory", alias="Item Type")  # inventory, non_inventory, service, goods
    product_type: str = Field("goods", alias="Product Type")  # goods, service
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    
    # Sales Information
    rate: float = Field(0, alias="Rate")  # Selling price
    sales_rate: float = 0  # Same as rate
    sales_description: str = ""
    sales_account: Optional[str] = Field(None, alias="Account")  # Sales Account Name
    sales_account_id: Optional[str] = None
    sales_account_code: Optional[str] = Field(None, alias="Account Code")
    
    # Purchase Information
    purchase_rate: float = Field(0, alias="Purchase Rate")
    purchase_description: str = Field("", alias="Purchase Description")
    purchase_account: Optional[str] = Field(None, alias="Purchase Account")
    purchase_account_id: Optional[str] = None
    purchase_account_code: Optional[str] = Field(None, alias="Purchase Account Code")
    
    # Inventory Account
    inventory_account: Optional[str] = Field(None, alias="Inventory Account")
    inventory_account_id: Optional[str] = None
    inventory_account_code: Optional[str] = Field(None, alias="Inventory Account Code")
    inventory_valuation_method: str = Field("fifo", alias="Inventory Valuation Method")  # fifo, weighted_average
    
    # Inventory Levels
    opening_stock: float = Field(0, alias="Opening Stock")
    opening_stock_value: float = Field(0, alias="Opening Stock Value")  # Total value
    opening_stock_rate: float = 0  # Cost per unit (calculated from value/stock)
    stock_on_hand: float = Field(0, alias="Stock On Hand")
    reorder_level: float = Field(0, alias="Reorder Point")
    
    # Units
    unit: str = "pcs"
    usage_unit: str = Field("pcs", alias="Usage unit")
    unit_name: str = Field("", alias="Unit Name")  # Full unit name
    
    # Tax Information - Complete Zoho Fields
    taxable: bool = Field(True, alias="Taxable")
    tax_preference: str = "taxable"  # taxable, non_taxable, exempt
    taxability_type: str = Field("", alias="Taxability Type")  # Goods, Service
    exemption_reason: str = Field("", alias="Exemption Reason")
    tax_id: Optional[str] = None
    tax_percentage: float = 18
    
    # GST Taxes (India)
    intra_state_tax_name: str = Field("GST", alias="Intra State Tax Name")
    intra_state_tax_rate: float = Field(18, alias="Intra State Tax Rate")  # CGST + SGST
    intra_state_tax_type: str = Field("percentage", alias="Intra State Tax Type")
    inter_state_tax_name: str = Field("IGST", alias="Inter State Tax Name")
    inter_state_tax_rate: float = Field(18, alias="Inter State Tax Rate")  # IGST
    inter_state_tax_type: str = Field("percentage", alias="Inter State Tax Type")
    
    # HSN/SAC Codes (GST India)
    hsn_code: str = Field("", alias="HSN/SAC")
    sac_code: str = ""  # Service Accounting Code
    
    # Vendor Information
    vendor: Optional[str] = Field(None, alias="Vendor")  # Vendor name
    preferred_vendor_id: Optional[str] = None
    preferred_vendor_name: str = ""
    
    # Location/Warehouse
    location_name: str = Field("", alias="Location Name")
    warehouse_id: Optional[str] = None
    
    # Sync Information (Zoho Integration)
    source: str = Field("Manual", alias="Source")  # Manual, Zoho Books, Import
    reference_id: Optional[str] = Field(None, alias="Reference ID")  # External system ID
    zoho_item_id: Optional[str] = None
    last_sync_time: Optional[str] = Field(None, alias="Last Sync Time")
    
    # Status & Flags
    status: str = Field("active", alias="Status")  # active, inactive
    is_active: bool = True
    sellable: bool = Field(True, alias="Sellable")
    purchasable: bool = Field(True, alias="Purchasable")
    track_inventory: bool = Field(True, alias="Track Inventory")
    
    # Image (base64 encoded)
    image_data: Optional[str] = None
    image_name: Optional[str] = None
    
    # Custom Fields
    custom_fields: Dict = {}
    
    class Config:
        populate_by_name = True  # Allow both alias and field name

    @validator('item_type')
    def validate_item_type(cls, v):
        valid_types = ['inventory', 'non_inventory', 'service', 'sales', 'purchases', 'sales_and_purchases', 'goods']
        if v.lower() not in [t.lower() for t in valid_types]:
            raise ValueError(f"Item type must be one of: {valid_types}")
        return v.lower()
    
    @validator('tax_preference')
    def validate_tax_preference(cls, v):
        valid = ['taxable', 'non_taxable', 'exempt']
        if v.lower() not in [t.lower() for t in valid]:
            raise ValueError(f"Tax preference must be one of: {valid}")
        return v.lower()
    
    @validator('inventory_valuation_method')
    def validate_valuation_method(cls, v):
        valid = ['fifo', 'weighted_average', 'lifo', 'specific']
        if v.lower() not in valid:
            return 'fifo'  # Default to FIFO
        return v.lower()

class ItemUpdate(BaseModel):
    """Partial update model - all fields optional. Full Zoho Books compatibility."""
    # Basic Info
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    product_type: Optional[str] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    
    # Sales Information
    rate: Optional[float] = None
    sales_rate: Optional[float] = None
    sales_description: Optional[str] = None
    sales_account: Optional[str] = None
    sales_account_id: Optional[str] = None
    sales_account_code: Optional[str] = None
    
    # Purchase Information
    purchase_rate: Optional[float] = None
    purchase_description: Optional[str] = None
    purchase_account: Optional[str] = None
    purchase_account_id: Optional[str] = None
    purchase_account_code: Optional[str] = None
    
    # Inventory Account
    inventory_account: Optional[str] = None
    inventory_account_id: Optional[str] = None
    inventory_account_code: Optional[str] = None
    inventory_valuation_method: Optional[str] = None
    
    # Inventory Levels
    opening_stock: Optional[float] = None
    opening_stock_value: Optional[float] = None
    opening_stock_rate: Optional[float] = None
    stock_on_hand: Optional[float] = None
    reorder_level: Optional[float] = None
    
    # Units
    unit: Optional[str] = None
    usage_unit: Optional[str] = None
    unit_name: Optional[str] = None
    
    # Tax Information
    taxable: Optional[bool] = None
    tax_preference: Optional[str] = None
    taxability_type: Optional[str] = None
    exemption_reason: Optional[str] = None
    tax_id: Optional[str] = None
    tax_percentage: Optional[float] = None
    
    # GST Taxes
    intra_state_tax_name: Optional[str] = None
    intra_state_tax_rate: Optional[float] = None
    intra_state_tax_type: Optional[str] = None
    inter_state_tax_name: Optional[str] = None
    inter_state_tax_rate: Optional[float] = None
    inter_state_tax_type: Optional[str] = None
    
    # HSN/SAC
    hsn_code: Optional[str] = None
    sac_code: Optional[str] = None
    
    # Vendor
    vendor: Optional[str] = None
    preferred_vendor_id: Optional[str] = None
    preferred_vendor_name: Optional[str] = None
    
    # Location
    location_name: Optional[str] = None
    warehouse_id: Optional[str] = None
    
    # Sync Info
    source: Optional[str] = None
    reference_id: Optional[str] = None
    zoho_item_id: Optional[str] = None
    last_sync_time: Optional[str] = None
    
    # Status & Flags
    status: Optional[str] = None
    is_active: Optional[bool] = None
    sellable: Optional[bool] = None
    purchasable: Optional[bool] = None
    track_inventory: Optional[bool] = None
    
    # Image
    image_data: Optional[str] = None
    image_name: Optional[str] = None
    
    # Custom Fields
    custom_fields: Optional[Dict] = None

class ItemStockLocationCreate(BaseModel):
    item_id: str
    warehouse_id: str
    stock: float = 0

class ItemAdjustmentCreate(BaseModel):
    item_id: str
    warehouse_id: str
    adjustment_type: str  # add, subtract
    quantity: float
    reason: str = "other"  # initial, purchase, sale, damage, recount, transfer, other
    notes: str = ""
    reference_number: str = ""
    date: str = ""

    @validator('adjustment_type')
    def validate_adjustment_type(cls, v):
        if v not in ['add', 'subtract']:
            raise ValueError("Adjustment type must be 'add' or 'subtract'")
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

class PriceListCreate(BaseModel):
    name: str
    description: str = ""
    discount_percentage: float = 0
    markup_percentage: float = 0
    is_active: bool = True

class ItemPriceCreate(BaseModel):
    item_id: str
    price_list_id: str
    rate: float

class BulkStockUpdate(BaseModel):
    updates: List[Dict]  # [{"item_id": "...", "warehouse_id": "...", "stock": 100}, ...]

# ============== NEW MODELS FOR ZOHO FEATURES ==============

class BulkActionRequest(BaseModel):
    """Bulk action on multiple items"""
    item_ids: List[str]
    action: str  # activate, deactivate, delete, clone

class ValueAdjustmentCreate(BaseModel):
    """Inventory value adjustment (for depreciation, appreciation)"""
    item_id: str
    warehouse_id: str
    adjustment_account: str = "Inventory Adjustment"
    new_value_per_unit: float
    reason: str = "depreciation"  # depreciation, appreciation, revaluation
    notes: str = ""
    reference_number: str = ""

class ItemHistoryEntry(BaseModel):
    """Track item changes"""
    item_id: str
    action: str  # created, updated, stock_adjusted, value_adjusted, cloned, activated, deactivated
    changes: Dict = {}
    user_id: Optional[str] = None
    user_name: str = "System"
    timestamp: str = ""

class ItemPreferences(BaseModel):
    """Module preferences"""
    # SKU Settings
    enable_sku: bool = True
    auto_generate_sku: bool = False
    sku_prefix: str = "SKU-"
    sku_sequence_start: int = 1
    
    # HSN/SAC Settings
    require_hsn_sac: bool = False
    hsn_digits_required: int = 4  # 4, 6, or 8
    
    # Alerts
    enable_reorder_alerts: bool = True
    enable_low_stock_alerts: bool = True
    low_stock_threshold_days: int = 7
    
    # Defaults
    default_tax_preference: str = "taxable"
    default_unit: str = "pcs"
    default_item_type: str = "inventory"
    default_tax_rate: float = 18
    
    # Features
    enable_images: bool = True
    enable_custom_fields: bool = True
    enable_barcode: bool = True
    barcode_type: str = "CODE128"  # CODE128, EAN13, QR
    
    # Inventory
    default_valuation_method: str = "fifo"  # fifo, weighted_average
    track_serial_numbers: bool = False
    track_batch_numbers: bool = False

class FieldConfiguration(BaseModel):
    """Field visibility and access configuration"""
    field_name: str
    display_name: str = ""
    is_active: bool = True
    show_in_list: bool = True
    show_in_form: bool = True
    show_in_pdf: bool = True
    is_mandatory: bool = False
    allowed_roles: List[str] = ["admin", "manager", "user"]
    field_order: int = 0

class CustomFieldDefinition(BaseModel):
    """Custom field definition for items"""
    field_id: str = ""
    field_name: str
    field_type: str = "text"  # text, number, date, dropdown, checkbox, url, email
    is_required: bool = False
    show_in_list: bool = False
    show_in_pdf: bool = False
    show_in_form: bool = True
    dropdown_options: List[str] = []
    default_value: Optional[str] = None
    placeholder: str = ""
    help_text: str = ""
    validation_regex: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_roles: List[str] = ["admin", "manager", "user"]
    field_order: int = 0

class PriceListEnhanced(BaseModel):
    """Enhanced price list with type (Sales/Purchase)"""
    name: str
    description: str = ""
    price_list_type: str = "sales"  # sales, purchase
    pricing_scheme: str = "percentage"  # percentage, custom
    discount_percentage: float = 0
    markup_percentage: float = 0
    round_off_to: str = "none"  # none, nearest_1, nearest_5, nearest_10
    is_active: bool = True

# ============== PHASE 2 MODELS ==============

class ContactPriceListAssign(BaseModel):
    """Assign price list to customer/vendor"""
    contact_id: str
    sales_price_list_id: Optional[str] = None
    purchase_price_list_id: Optional[str] = None

class LineItemPriceRequest(BaseModel):
    """Calculate price for line items"""
    items: List[Dict]  # [{"item_id": "...", "quantity": 1}, ...]
    contact_id: Optional[str] = None
    price_list_id: Optional[str] = None
    transaction_type: str = "sales"  # sales, purchase

class BulkItemPriceSet(BaseModel):
    """Set prices for multiple items in a price list"""
    price_list_id: str
    pricing_method: str = "percentage"  # percentage, custom
    percentage: float = 0  # Markup (+) or Discount (-)
    items: List[Dict] = []  # [{"item_id": "...", "custom_rate": 100}, ...] for custom method

class ItemBarcodeCreate(BaseModel):
    """Barcode/QR for item"""
    item_id: str
    barcode_type: str = "CODE128"  # CODE128, EAN13, QR
    barcode_value: str = ""  # Auto-generate if empty

class SalesByItemFilter(BaseModel):
    """Filter for Sales by Item report"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    item_id: Optional[str] = None
    group_id: Optional[str] = None
    customer_id: Optional[str] = None

# ============== ITEM GROUPS ==============

@router.post("/groups")
async def create_item_group(group: ItemGroupCreate, request: Request):
    """Create an item group (category)"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Check unique name
    existing = await db.item_groups.find_one({"name": group.name, "organization_id": org_id})
    if existing:
        raise HTTPException(status_code=400, detail="Item group with this name already exists")
    
    group_id = f"IG-{uuid.uuid4().hex[:8].upper()}"
    
    # Get parent group name if exists
    parent_name = ""
    if group.parent_group_id:
        parent = await db.item_groups.find_one({"group_id": group.parent_group_id, "organization_id": org_id})
        if parent:
            parent_name = parent.get("name", "")
    
    group_dict = {
        "group_id": group_id,
        "organization_id": org_id,
        "name": group.name,
        "description": group.description,
        "parent_group_id": group.parent_group_id,
        "parent_group_name": parent_name,
        "is_active": group.is_active,
        "item_count": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_groups.insert_one(group_dict)
    del group_dict["_id"]
    
    return {"code": 0, "message": "Item group created", "group": group_dict}

@router.get("/groups")
async def list_item_groups(request: Request, include_inactive: bool = False):
    """List all item groups"""
    db = get_db()
    org_id = extract_org_id(request)
    query = {"organization_id": org_id}
    if not include_inactive:
        query["is_active"] = True
    groups = await db.item_groups.find(query, {"_id": 0}).to_list(1000)
    
    # Build hierarchy
    root_groups = [g for g in groups if not g.get("parent_group_id")]
    for root in root_groups:
        root["subgroups"] = [g for g in groups if g.get("parent_group_id") == root["group_id"]]
    
    return {"code": 0, "groups": groups, "hierarchy": root_groups}


@router.get("/categories")
async def list_item_categories(request: Request, include_inactive: bool = False):
    """List all item categories (alias for groups for Zoho compatibility)"""
    db = get_db()
    org_id = extract_org_id(request)
    query = {"organization_id": org_id}
    if not include_inactive:
        query["is_active"] = True
    groups = await db.item_groups.find(query, {"_id": 0}).to_list(1000)
    
    # Also get distinct categories from items collection as fallback
    item_categories = await db.items.distinct("category", {"organization_id": org_id})
    
    # Combine groups and item categories
    categories = []
    for g in groups:
        categories.append({
            "category_id": g.get("group_id"),
            "name": g.get("name"),
            "description": g.get("description", ""),
            "is_group": True
        })
    
    for cat in item_categories:
        if cat and cat not in [g.get("name") for g in groups]:
            categories.append({
                "category_id": f"cat_{cat}",
                "name": cat,
                "description": "",
                "is_group": False
            })
    
    return {"code": 0, "categories": categories, "total": len(categories)}

@router.get("/groups/{group_id}")
async def get_item_group(group_id: str, request: Request):
    """Get item group details with items"""
    db = get_db()
    org_id = extract_org_id(request)
    group = await db.item_groups.find_one({"group_id": group_id, "organization_id": org_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Item group not found")
    
    # Get items in this group
    items = await db.items.find(
        {"organization_id": org_id, "$or": [{"group_id": group_id}, {"item_group_id": group_id}]},
        {"_id": 0, "item_id": 1, "name": 1, "sku": 1, "sales_rate": 1, "stock_on_hand": 1}
    ).to_list(100)
    
    group["items"] = items
    return {"code": 0, "group": group}

@router.put("/groups/{group_id}")
async def update_item_group(group_id: str, group: ItemGroupCreate, request: Request):
    """Update item group"""
    db = get_db()
    org_id = extract_org_id(request)
    
    result = await db.item_groups.update_one(
        {"group_id": group_id, "organization_id": org_id},
        {"$set": {
            "name": group.name,
            "description": group.description,
            "parent_group_id": group.parent_group_id,
            "is_active": group.is_active,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item group not found")
    
    return {"code": 0, "message": "Item group updated"}

@router.delete("/groups/{group_id}")
async def delete_item_group(group_id: str, request: Request):
    """Delete item group (only if no items)"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Check for items
    item_count = await db.items.count_documents(
        {"organization_id": org_id, "$or": [{"group_id": group_id}, {"item_group_id": group_id}]}
    )
    if item_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete group with {item_count} items")
    
    result = await db.item_groups.delete_one({"group_id": group_id, "organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item group not found")
    
    return {"code": 0, "message": "Item group deleted"}

# ============== WAREHOUSES ==============

@router.post("/warehouses")
async def create_warehouse(warehouse: WarehouseCreate, request: Request):
    """Create a warehouse"""
    db = get_db()
    org_id = extract_org_id(request)
    
    existing = await db.warehouses.find_one({"name": warehouse.name, "organization_id": org_id})
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse with this name already exists")
    
    warehouse_id = f"WH-{uuid.uuid4().hex[:8].upper()}"
    
    warehouse_dict = {
        "warehouse_id": warehouse_id,
        "organization_id": org_id,
        "name": warehouse.name,
        "location": warehouse.location,
        "is_primary": warehouse.is_primary,
        "is_active": warehouse.is_active,
        "total_items": 0,
        "total_stock_value": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.warehouses.insert_one(warehouse_dict)
    del warehouse_dict["_id"]
    
    return {"code": 0, "message": "Warehouse created", "warehouse": warehouse_dict}

@router.get("/warehouses")
async def list_warehouses(request: Request, include_inactive: bool = False):
    """List all warehouses"""
    db = get_db()
    org_id = extract_org_id(request)
    query = {"organization_id": org_id}
    if not include_inactive:
        query["is_active"] = True
    warehouses = await db.warehouses.find(query, {"_id": 0}).to_list(100)
    
    # Calculate stock values for each warehouse
    for wh in warehouses:
        # H-02: hard cap, Sprint 3 for cursor pagination
        stock_locs = await db.item_stock_locations.find(
            {"warehouse_id": wh["warehouse_id"], "organization_id": org_id}
        ).to_list(500)
        wh["total_items"] = len(stock_locs)
        wh["total_stock"] = sum(s.get("stock", 0) for s in stock_locs)
    
    return {"code": 0, "warehouses": warehouses}

@router.get("/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: str, request: Request):
    """Get warehouse details with stock"""
    db = get_db()
    org_id = extract_org_id(request)
    warehouse = await db.warehouses.find_one({"warehouse_id": warehouse_id, "organization_id": org_id}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get stock in this warehouse
    stock_locations = await db.item_stock_locations.aggregate([
        {"$match": {"warehouse_id": warehouse_id, "organization_id": org_id, "stock": {"$gt": 0}}},
        {"$lookup": {
            "from": "items",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "item_info"
        }},
        {"$unwind": {"path": "$item_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "stock": 1,
            "item_name": "$item_info.name",
            "sku": "$item_info.sku",
            "rate": "$item_info.sales_rate"
        }}
    ]).to_list(1000)
    
    warehouse["stock_items"] = stock_locations
    warehouse["total_items"] = len(stock_locations)
    warehouse["total_stock"] = sum(s.get("stock", 0) for s in stock_locations)
    
    return {"code": 0, "warehouse": warehouse}

@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(warehouse_id: str, warehouse: WarehouseCreate, request: Request):
    """Update warehouse"""
    db = get_db()
    org_id = extract_org_id(request)
    
    result = await db.warehouses.update_one(
        {"warehouse_id": warehouse_id, "organization_id": org_id},
        {"$set": {
            "name": warehouse.name,
            "location": warehouse.location,
            "is_primary": warehouse.is_primary,
            "is_active": warehouse.is_active,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    return {"code": 0, "message": "Warehouse updated"}

# ============== ENHANCED ITEMS ==============

@router.post("/")
async def create_enhanced_item(item: ItemCreate, request: Request):
    """Create item with full Zoho Books-style features and CSV compatibility"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Check unique name/SKU
    if item.sku:
        existing = await db.items.find_one({"sku": item.sku, "organization_id": org_id})
        if existing:
            raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    
    item_id = f"I-{uuid.uuid4().hex[:12].upper()}"
    
    # Handle image storage
    image_url = None
    if item.image_data:
        try:
            image_doc = {
                "image_id": f"IMG-{uuid.uuid4().hex[:8].upper()}",
                "item_id": item_id,
                "organization_id": org_id,
                "image_name": item.image_name or "item_image",
                "image_data": item.image_data,
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            await db.item_images.insert_one(image_doc)
            image_url = f"/api/items-enhanced/images/{image_doc['image_id']}"
        except:
            pass
    
    # Calculate opening stock rate if value provided
    opening_stock_rate = item.opening_stock_rate
    if not opening_stock_rate and item.opening_stock > 0 and item.opening_stock_value > 0:
        opening_stock_rate = item.opening_stock_value / item.opening_stock
    elif not opening_stock_rate:
        opening_stock_rate = item.purchase_rate
    
    item_dict = {
        "item_id": item_id,
        "organization_id": org_id,
        "name": item.name,
        "sku": item.sku,
        "description": item.description,
        "item_type": item.item_type,
        "product_type": item.product_type,
        "group_id": item.group_id,
        "group_name": item.group_name,
        
        # ===== SALES INFORMATION =====
        "rate": item.rate or item.sales_rate,  # Selling price
        "sales_rate": item.sales_rate or item.rate,
        "sales_description": item.sales_description,
        "sales_account": item.sales_account,
        "sales_account_id": item.sales_account_id,
        "sales_account_code": item.sales_account_code,
        
        # ===== PURCHASE INFORMATION =====
        "purchase_rate": item.purchase_rate,
        "purchase_description": item.purchase_description,
        "purchase_account": item.purchase_account,
        "purchase_account_id": item.purchase_account_id,
        "purchase_account_code": item.purchase_account_code,
        
        # ===== INVENTORY ACCOUNT =====
        "inventory_account": item.inventory_account,
        "inventory_account_id": item.inventory_account_id,
        "inventory_account_code": item.inventory_account_code,
        "inventory_valuation_method": item.inventory_valuation_method,
        
        # ===== INVENTORY LEVELS =====
        "opening_stock": item.opening_stock,
        "opening_stock_value": item.opening_stock_value or (item.opening_stock * opening_stock_rate),
        "opening_stock_rate": opening_stock_rate,
        "stock_on_hand": item.stock_on_hand or item.opening_stock,
        "available_stock": item.opening_stock,
        "committed_stock": 0,
        "stock_on_order": 0,
        "reorder_level": item.reorder_level,
        
        # ===== UNITS =====
        "unit": item.unit or item.usage_unit,
        "usage_unit": item.usage_unit,
        "unit_name": item.unit_name,
        
        # ===== TAX INFORMATION =====
        "taxable": item.taxable,
        "tax_preference": item.tax_preference,
        "taxability_type": item.taxability_type,
        "exemption_reason": item.exemption_reason,
        "tax_id": item.tax_id,
        "tax_percentage": item.tax_percentage,
        
        # ===== GST TAXES (INDIA) =====
        "intra_state_tax_name": item.intra_state_tax_name,
        "intra_state_tax_rate": item.intra_state_tax_rate,
        "intra_state_tax_type": item.intra_state_tax_type,
        "inter_state_tax_name": item.inter_state_tax_name,
        "inter_state_tax_rate": item.inter_state_tax_rate,
        "inter_state_tax_type": item.inter_state_tax_type,
        
        # ===== HSN/SAC CODES =====
        "hsn_code": item.hsn_code,
        "sac_code": item.sac_code,
        "hsn_or_sac": item.hsn_code or item.sac_code,
        
        # ===== VENDOR INFORMATION =====
        "vendor": item.vendor,
        "preferred_vendor_id": item.preferred_vendor_id,
        "preferred_vendor_name": item.preferred_vendor_name or item.vendor,
        
        # ===== LOCATION/WAREHOUSE =====
        "location_name": item.location_name,
        "warehouse_id": item.warehouse_id,
        
        # ===== SYNC INFORMATION =====
        "source": item.source,
        "reference_id": item.reference_id,
        "zoho_item_id": item.zoho_item_id,
        "last_sync_time": item.last_sync_time,
        
        # ===== STATUS & FLAGS =====
        "status": item.status if item.status else ("active" if item.is_active else "inactive"),
        "is_active": item.is_active,
        "sellable": item.sellable,
        "purchasable": item.purchasable,
        "track_inventory": item.track_inventory,
        
        # ===== IMAGE =====
        "image_url": image_url,
        
        # ===== CUSTOM FIELDS =====
        "custom_fields": item.custom_fields,
        
        # ===== TIMESTAMPS =====
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.items.insert_one(item_dict)
    del item_dict["_id"]
    
    # Initialize stock locations for inventory items
    if item.item_type == "inventory" or item.track_inventory:
        warehouses = await db.warehouses.find({"is_active": True, "organization_id": org_id}).to_list(100)
        target_warehouse_id = item.warehouse_id
        
        for wh in warehouses:
            stock_qty = 0
            if target_warehouse_id and wh["warehouse_id"] == target_warehouse_id:
                stock_qty = item.opening_stock
            elif not target_warehouse_id and wh.get("is_primary"):
                stock_qty = item.opening_stock
                
            await db.item_stock_locations.insert_one({
                "location_id": f"ISL-{uuid.uuid4().hex[:8].upper()}",
                "item_id": item_id,
                "organization_id": org_id,
                "warehouse_id": wh["warehouse_id"],
                "warehouse_name": wh["name"],
                "stock": stock_qty,
                "created_time": datetime.now(timezone.utc).isoformat(),
                "updated_time": datetime.now(timezone.utc).isoformat()
            })
    
    # Update group item count
    if item.group_id:
        await db.item_groups.update_one(
            {"group_id": item.group_id, "organization_id": org_id},
            {"$inc": {"item_count": 1}}
        )
    
    # Log history
    await log_item_history(db, item_id, "created", {"name": item.name, "type": item.item_type}, "System", org_id=org_id)
    
    return {"code": 0, "message": "Item created successfully", "item": item_dict}

# Image endpoint
@router.get("/images/{image_id}")
async def get_item_image(image_id: str, request: Request):
    """Get item image by ID"""
    db = get_db()
    org_id = extract_org_id(request)
    
    image = await db.item_images.find_one({"image_id": image_id, "organization_id": org_id}, {"_id": 0})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Return base64 image data
    return {"code": 0, "image": image}

@router.get("/summary")
async def get_items_summary(request: Request):
    """Get items summary statistics"""
    db = get_db()
    org_id = extract_org_id(request)
    base = org_query(org_id)
    
    total_items = await db.items.count_documents(base)
    active_items = await db.items.count_documents(org_query(org_id, {"status": "active"}))
    inventory_items = await db.items.count_documents(org_query(org_id, {"item_type": "inventory"}))
    service_items = await db.items.count_documents(org_query(org_id, {"item_type": "service"}))
    
    # Calculate total stock value
    pipeline = [
        {"$match": {"item_type": "inventory"}},
        {"$lookup": {
            "from": "item_stock_locations",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "stock"
        }},
        {"$unwind": {"path": "$stock", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": None,
            "total_stock_value": {"$sum": {"$multiply": [{"$ifNull": ["$stock.available_stock", 0]}, {"$ifNull": ["$purchase_rate", 0]}]}},
            "total_units": {"$sum": {"$ifNull": ["$stock.available_stock", 0]}}
        }}
    ]
    stock_data = await db.items.aggregate(pipeline).to_list(1)
    
    return {
        "code": 0,
        "summary": {
            "total_items": total_items,
            "active_items": active_items,
            "inventory_items": inventory_items,
            "service_items": service_items,
            "total_stock_value": round(stock_data[0].get("total_stock_value", 0) if stock_data else 0, 2),
            "total_units": round(stock_data[0].get("total_units", 0) if stock_data else 0, 2)
        }
    }

@router.get("/")
async def list_enhanced_items(
    request: Request,
    item_type: str = "",
    group_id: str = "",
    warehouse_id: str = "",
    is_active: Optional[bool] = None,
    low_stock: bool = False,
    search: str = "",
    sort_by: str = "name",  # name, sku, sales_rate, purchase_rate, stock_on_hand, created_time
    sort_order: str = "asc",  # asc, desc
    page: int = 1,
    per_page: int = 50
):
    """List items with advanced filters and sorting"""
    db = get_db()
    org_id = extract_org_id(request)
    
    query = {"organization_id": org_id}
    if item_type:
        query["item_type"] = item_type
    if group_id:
        query["$or"] = [{"group_id": group_id}, {"item_group_id": group_id}]
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"hsn_code": {"$regex": search, "$options": "i"}}
        ]
    
    # Sorting
    sort_direction = 1 if sort_order == "asc" else -1
    valid_sort_fields = ["name", "sku", "sales_rate", "purchase_rate", "stock_on_hand", "created_time", "updated_time"]
    if sort_by not in valid_sort_fields:
        sort_by = "name"
    
    skip = (page - 1) * per_page
    cursor = db.items.find(query, {"_id": 0}).sort(sort_by, sort_direction).skip(skip).limit(per_page)
    items = await cursor.to_list(per_page)
    total = await db.items.count_documents(query)
    
    # Add stock info for inventory items
    for item in items:
        # Handle both Zoho-synced data (item_id) and legacy data (may not have item_id)
        item_id = item.get("item_id") or item.get("zoho_item_id") or str(item.get("_id", ""))
        if item.get("item_type") == "inventory" and item_id:
            stock_locs = await db.item_stock_locations.find(
                {"item_id": item_id, "organization_id": org_id},
                {"_id": 0}
            ).to_list(100)
            item["stock_locations"] = stock_locs
            item["total_stock"] = sum(s.get("stock", 0) for s in stock_locs)
            reorder_level = item.get("reorder_level", 0)
            if isinstance(reorder_level, str):
                reorder_level = float(reorder_level) if reorder_level else 0
            item["is_low_stock"] = item["total_stock"] < reorder_level
        elif item.get("item_type") == "inventory":
            item["stock_locations"] = []
            item["total_stock"] = 0
            item["is_low_stock"] = False
    
    # Filter low stock if requested
    if low_stock:
        items = [i for i in items if i.get("is_low_stock")]
    
    return {
        "code": 0,
        "items": items,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }

@router.get("/low-stock")
async def get_low_stock_items(request: Request):
    """Get items below reorder level"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # H-02: hard cap, Sprint 3 for cursor pagination
    items = await db.items.find(
        {"item_type": "inventory", "organization_id": org_id},
        {"_id": 0}
    ).to_list(500)
    
    low_stock_items = []
    for item in items:
        stock = item.get("stock_on_hand", 0) or item.get("available_stock", 0)
        if isinstance(stock, str):
            stock = float(stock) if stock else 0
        reorder = item.get("reorder_level", 0)
        if isinstance(reorder, str):
            reorder = float(reorder) if reorder else 0
        if stock < reorder:
            item["current_stock"] = stock
            item["shortage"] = reorder - stock
            low_stock_items.append(item)
    
    low_stock_items.sort(key=lambda x: x.get("shortage", 0), reverse=True)
    
    return {"code": 0, "low_stock_items": low_stock_items, "count": len(low_stock_items)}

# ============== STOCK LOCATIONS (MUST BE BEFORE /{item_id}) ==============

@router.post("/stock-locations")
async def create_stock_location(location: ItemStockLocationCreate, request: Request):
    """Create or update stock location"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Get warehouse name
    warehouse = await db.warehouses.find_one({"warehouse_id": location.warehouse_id, "organization_id": org_id})
    warehouse_name = warehouse.get("name", "") if warehouse else ""
    
    # Check if exists
    existing = await db.item_stock_locations.find_one({
        "item_id": location.item_id,
        "warehouse_id": location.warehouse_id,
        "organization_id": org_id
    })
    
    if existing:
        await db.item_stock_locations.update_one(
            {"_id": existing["_id"]},
            {"$set": {"stock": location.stock, "updated_time": datetime.now(timezone.utc).isoformat()}}
        )
        return {"code": 0, "message": "Stock location updated"}
    
    location_dict = {
        "location_id": f"ISL-{uuid.uuid4().hex[:8].upper()}",
        "item_id": location.item_id,
        "organization_id": org_id,
        "warehouse_id": location.warehouse_id,
        "warehouse_name": warehouse_name,
        "stock": location.stock,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_stock_locations.insert_one(location_dict)
    
    return {"code": 0, "message": "Stock location created"}

@router.post("/stock-locations/bulk-update")
async def bulk_update_stock(bulk: BulkStockUpdate, request: Request):
    """Bulk update stock locations"""
    db = get_db()
    org_id = extract_org_id(request)
    updated = 0
    
    for update in bulk.updates:
        item_id = update.get("item_id")
        warehouse_id = update.get("warehouse_id")
        stock = update.get("stock", 0)
        
        result = await db.item_stock_locations.update_one(
            {"item_id": item_id, "warehouse_id": warehouse_id, "organization_id": org_id},
            {"$set": {"stock": stock, "updated_time": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        if result.modified_count > 0 or result.upserted_id:
            updated += 1
    
    return {"code": 0, "message": f"Updated {updated} stock locations"}

# ============== INVENTORY ADJUSTMENTS (MUST BE BEFORE /{item_id}) ==============

@router.post("/adjustments")
async def create_item_adjustment(adj: ItemAdjustmentCreate, request: Request):
    """Create inventory adjustment"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Get item
    item = await db.items.find_one({"item_id": adj.item_id, "organization_id": org_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.get("item_type") not in ["inventory", "sales_and_purchases"]:
        raise HTTPException(status_code=400, detail="Item is not an inventory item")
    
    # Get or create stock location
    stock_loc = await db.item_stock_locations.find_one({
        "item_id": adj.item_id,
        "warehouse_id": adj.warehouse_id,
        "organization_id": org_id
    })
    
    current_stock = stock_loc.get("stock", 0) if stock_loc else 0
    
    # Calculate new stock
    if adj.adjustment_type == "add":
        new_stock = current_stock + adj.quantity
    else:
        if current_stock < adj.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Current: {current_stock}, Requested: {adj.quantity}"
            )
        new_stock = current_stock - adj.quantity
    
    # Create adjustment record
    adj_id = f"ADJ-{uuid.uuid4().hex[:8].upper()}"
    adj_date = adj.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get warehouse name
    warehouse = await db.warehouses.find_one({"warehouse_id": adj.warehouse_id, "organization_id": org_id})
    warehouse_name = warehouse.get("name", "") if warehouse else ""
    
    adj_dict = {
        "adjustment_id": adj_id,
        "organization_id": org_id,
        "item_id": adj.item_id,
        "item_name": item.get("name", ""),
        "warehouse_id": adj.warehouse_id,
        "warehouse_name": warehouse_name,
        "adjustment_type": adj.adjustment_type,
        "quantity": adj.quantity,
        "stock_before": current_stock,
        "stock_after": new_stock,
        "reason": adj.reason,
        "notes": adj.notes,
        "reference_number": adj.reference_number,
        "date": adj_date,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_adjustments.insert_one(adj_dict)
    
    # Update stock location
    if stock_loc:
        await db.item_stock_locations.update_one(
            {"_id": stock_loc["_id"]},
            {"$set": {"stock": new_stock, "updated_time": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.item_stock_locations.insert_one({
            "location_id": f"ISL-{uuid.uuid4().hex[:8].upper()}",
            "item_id": adj.item_id,
            "organization_id": org_id,
            "warehouse_id": adj.warehouse_id,
            "warehouse_name": warehouse_name,
            "stock": new_stock,
            "created_time": datetime.now(timezone.utc).isoformat(),
            "updated_time": datetime.now(timezone.utc).isoformat()
        })
    
    # Update item total stock
    all_locations = await db.item_stock_locations.find({"item_id": adj.item_id, "organization_id": org_id}).to_list(100)
    total_stock = sum(loc.get("stock", 0) for loc in all_locations)
    await db.items.update_one(
        {"item_id": adj.item_id, "organization_id": org_id},
        {"$set": {
            "stock_on_hand": total_stock,
            "available_stock": total_stock,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    del adj_dict["_id"]
    return {"code": 0, "message": "Adjustment created", "adjustment": adj_dict}

@router.get("/adjustments")
async def list_item_adjustments(
    request: Request,
    item_id: str = "",
    warehouse_id: str = "",
    reason: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List inventory adjustments"""
    db = get_db()
    org_id = extract_org_id(request)
    
    query = {"organization_id": org_id}
    if item_id:
        query["item_id"] = item_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if reason:
        query["reason"] = reason
    
    skip = (page - 1) * per_page
    adjustments = await db.item_adjustments.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page).to_list(per_page)
    total = await db.item_adjustments.count_documents(query)
    
    return {
        "code": 0,
        "adjustments": adjustments,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/adjustments/{adj_id}")
async def get_item_adjustment(adj_id: str, request: Request):
    """Get adjustment details"""
    db = get_db()
    org_id = extract_org_id(request)
    adj = await db.item_adjustments.find_one({"adjustment_id": adj_id, "organization_id": org_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    return {"code": 0, "adjustment": adj}

# ============== PRICE LISTS (MUST BE BEFORE /{item_id}) ==============

@router.post("/price-lists")
async def create_price_list(price_list: PriceListCreate, request: Request):
    """Create a price list"""
    db = get_db()
    org_id = extract_org_id(request)
    
    existing = await db.price_lists.find_one({"name": price_list.name, "organization_id": org_id})
    if existing:
        raise HTTPException(status_code=400, detail="Price list with this name already exists")
    
    pl_id = f"PL-{uuid.uuid4().hex[:8].upper()}"
    
    pl_dict = {
        "pricelist_id": pl_id,
        "organization_id": org_id,
        "name": price_list.name,
        "description": price_list.description,
        "discount_percentage": price_list.discount_percentage,
        "markup_percentage": price_list.markup_percentage,
        "is_active": price_list.is_active,
        "item_count": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.price_lists.insert_one(pl_dict)
    del pl_dict["_id"]
    
    return {"code": 0, "message": "Price list created", "price_list": pl_dict}

@router.get("/price-lists")
async def list_price_lists(request: Request, include_inactive: bool = False):
    """List all price lists"""
    db = get_db()
    org_id = extract_org_id(request)
    query = {"organization_id": org_id}
    if not include_inactive:
        query["is_active"] = True
    price_lists = await db.price_lists.find(query, {"_id": 0}).to_list(100)
    
    # Normalize and count items per price list
    for pl in price_lists:
        # Handle both old (price_list_id) and new (pricelist_id) schemas
        pl_id = pl.get("pricelist_id") or pl.get("price_list_id", "")
        pl["pricelist_id"] = pl_id  # Ensure consistent field name
        
        # Normalize name field
        if "price_list_name" in pl and "name" not in pl:
            pl["name"] = pl["price_list_name"]
        
        count = await db.item_prices.count_documents({"price_list_id": pl_id, "organization_id": org_id})
        pl["item_count"] = count
    
    return {"code": 0, "price_lists": price_lists}

@router.get("/price-lists/{pricelist_id}")
async def get_price_list(pricelist_id: str, request: Request):
    """Get price list with item prices"""
    db = get_db()
    org_id = extract_org_id(request)
    pl = await db.price_lists.find_one({"pricelist_id": pricelist_id, "organization_id": org_id}, {"_id": 0})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    # Get item prices
    prices = await db.item_prices.aggregate([
        {"$match": {"price_list_id": pricelist_id, "organization_id": org_id}},
        {"$lookup": {
            "from": "items",
            "localField": "item_id",
            "foreignField": "item_id",
            "as": "item_info"
        }},
        {"$unwind": {"path": "$item_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "rate": 1,
            "item_name": "$item_info.name",
            "sku": "$item_info.sku",
            "base_rate": "$item_info.sales_rate"
        }}
    ]).to_list(1000)
    
    pl["item_prices"] = prices
    return {"code": 0, "price_list": pl}

@router.put("/price-lists/{pricelist_id}")
async def update_price_list(pricelist_id: str, price_list: PriceListCreate, request: Request):
    """Update price list"""
    db = get_db()
    org_id = extract_org_id(request)
    
    result = await db.price_lists.update_one(
        {"pricelist_id": pricelist_id, "organization_id": org_id},
        {"$set": {
            "name": price_list.name,
            "description": price_list.description,
            "discount_percentage": price_list.discount_percentage,
            "markup_percentage": price_list.markup_percentage,
            "is_active": price_list.is_active,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    return {"code": 0, "message": "Price list updated"}

@router.delete("/price-lists/{pricelist_id}")
async def delete_price_list(pricelist_id: str, request: Request):
    """Delete price list"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Delete associated item prices
    await db.item_prices.delete_many({"price_list_id": pricelist_id, "organization_id": org_id})
    
    result = await db.price_lists.delete_one({"pricelist_id": pricelist_id, "organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    return {"code": 0, "message": "Price list deleted"}

# ============== ITEM PRICES (MUST BE BEFORE /{item_id}) ==============

@router.post("/prices")
async def create_item_price(price: ItemPriceCreate, request: Request):
    """Set item price for a price list"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Check if exists
    existing = await db.item_prices.find_one({
        "item_id": price.item_id,
        "price_list_id": price.price_list_id,
        "organization_id": org_id
    })
    
    if existing:
        await db.item_prices.update_one(
            {"_id": existing["_id"]},
            {"$set": {"rate": price.rate, "updated_time": datetime.now(timezone.utc).isoformat()}}
        )
        return {"code": 0, "message": "Item price updated"}
    
    # Get names
    item = await db.items.find_one({"item_id": price.item_id, "organization_id": org_id})
    pl = await db.price_lists.find_one({"pricelist_id": price.price_list_id, "organization_id": org_id})
    
    price_dict = {
        "price_id": f"IP-{uuid.uuid4().hex[:8].upper()}",
        "item_id": price.item_id,
        "organization_id": org_id,
        "item_name": item.get("name", "") if item else "",
        "price_list_id": price.price_list_id,
        "price_list_name": pl.get("name", "") if pl else "",
        "rate": price.rate,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_prices.insert_one(price_dict)
    
    return {"code": 0, "message": "Item price created"}

@router.get("/prices/{item_id}")
async def get_item_prices(item_id: str, request: Request):
    """Get all prices for an item"""
    db = get_db()
    org_id = extract_org_id(request)
    prices = await db.item_prices.find({"item_id": item_id, "organization_id": org_id}, {"_id": 0}).to_list(100)
    return {"code": 0, "prices": prices}

@router.delete("/prices/{item_id}/{price_list_id}")
async def delete_item_price(item_id: str, price_list_id: str, request: Request):
    """Delete item price from a price list"""
    db = get_db()
    org_id = extract_org_id(request)
    result = await db.item_prices.delete_one({
        "item_id": item_id,
        "price_list_id": price_list_id,
        "organization_id": org_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item price not found")
    return {"code": 0, "message": "Item price deleted"}

# ============== PHASE 2: CONTACT PRICE LIST ASSOCIATION ==============

@router.post("/contact-price-lists")
async def assign_price_list_to_contact(assignment: ContactPriceListAssign, request: Request):
    """Assign sales/purchase price list to a customer/vendor"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Verify contact exists
    contact = await db.contacts_enhanced.find_one({"contact_id": assignment.contact_id, "organization_id": org_id})
    if not contact:
        contact = await db.contacts.find_one({"contact_id": assignment.contact_id, "organization_id": org_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Verify price lists exist
    if assignment.sales_price_list_id:
        pl = await db.price_lists.find_one({"pricelist_id": assignment.sales_price_list_id, "organization_id": org_id})
        if not pl:
            raise HTTPException(status_code=404, detail="Sales price list not found")
    
    if assignment.purchase_price_list_id:
        pl = await db.price_lists.find_one({"pricelist_id": assignment.purchase_price_list_id, "organization_id": org_id})
        if not pl:
            raise HTTPException(status_code=404, detail="Purchase price list not found")
    
    # Update contact with price lists
    update_data = {"updated_time": datetime.now(timezone.utc).isoformat()}
    if assignment.sales_price_list_id is not None:
        update_data["sales_price_list_id"] = assignment.sales_price_list_id
    if assignment.purchase_price_list_id is not None:
        update_data["purchase_price_list_id"] = assignment.purchase_price_list_id
    
    # Try both collections
    result = await db.contacts_enhanced.update_one(
        {"contact_id": assignment.contact_id, "organization_id": org_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        await db.contacts.update_one(
            {"contact_id": assignment.contact_id, "organization_id": org_id},
            {"$set": update_data}
        )
    
    return {"code": 0, "message": "Price list assigned to contact"}

@router.get("/contact-price-lists/{contact_id}")
async def get_contact_price_lists(contact_id: str, request: Request):
    """Get price lists assigned to a contact"""
    db = get_db()
    org_id = extract_org_id(request)
    
    contact = await db.contacts_enhanced.find_one({"contact_id": contact_id, "organization_id": org_id}, {"_id": 0})
    if not contact:
        contact = await db.contacts.find_one({"contact_id": contact_id, "organization_id": org_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    result = {
        "contact_id": contact_id,
        "contact_name": contact.get("company_name") or contact.get("contact_name") or contact.get("name", ""),
        "sales_price_list_id": contact.get("sales_price_list_id"),
        "purchase_price_list_id": contact.get("purchase_price_list_id"),
        "sales_price_list": None,
        "purchase_price_list": None
    }
    
    # Get price list details
    if result["sales_price_list_id"]:
        pl = await db.price_lists.find_one({"pricelist_id": result["sales_price_list_id"], "organization_id": org_id}, {"_id": 0})
        result["sales_price_list"] = pl
    
    if result["purchase_price_list_id"]:
        pl = await db.price_lists.find_one({"pricelist_id": result["purchase_price_list_id"], "organization_id": org_id}, {"_id": 0})
        result["purchase_price_list"] = pl
    
    return {"code": 0, "contact_price_lists": result}

# ============== PHASE 2: LINE ITEM PRICING ==============

@router.post("/calculate-line-prices")
async def calculate_line_item_prices(line_request: LineItemPriceRequest, request: Request):
    """Calculate prices for line items based on contact or specific price list"""
    db = get_db()
    org_id = extract_org_id(request)
    
    price_list_id = line_request.price_list_id
    
    # If contact provided, get their assigned price list
    if line_request.contact_id and not price_list_id:
        contact = await db.contacts_enhanced.find_one({"contact_id": line_request.contact_id, "organization_id": org_id})
        if not contact:
            contact = await db.contacts.find_one({"contact_id": line_request.contact_id, "organization_id": org_id})
        
        if contact:
            if line_request.transaction_type == "sales":
                price_list_id = contact.get("sales_price_list_id")
            else:
                price_list_id = contact.get("purchase_price_list_id")
    
    # Get price list settings
    price_list = None
    if price_list_id:
        price_list = await db.price_lists.find_one({"pricelist_id": price_list_id, "organization_id": org_id}, {"_id": 0})
    
    line_items = []
    total = 0
    
    for item_request in line_request.items:
        item_id = item_request.get("item_id")
        quantity = item_request.get("quantity", 1)
        
        item = await db.items.find_one({"item_id": item_id, "organization_id": org_id}, {"_id": 0})
        if not item:
            continue
        
        # Get base rate
        if line_request.transaction_type == "sales":
            base_rate = item.get("sales_rate", 0) or item.get("rate", 0)
        else:
            base_rate = item.get("purchase_rate", 0)
        
        final_rate = base_rate
        
        # Check for custom price in price list
        if price_list_id:
            custom_price = await db.item_prices.find_one({
                "item_id": item_id,
                "price_list_id": price_list_id,
                "organization_id": org_id
            })
            
            if custom_price:
                final_rate = custom_price.get("rate", base_rate)
            elif price_list:
                # Apply percentage markup/discount
                if price_list.get("pricing_scheme") == "percentage":
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
        
        line_total = final_rate * quantity
        total += line_total
        
        line_items.append({
            "item_id": item_id,
            "item_name": item.get("name"),
            "sku": item.get("sku"),
            "quantity": quantity,
            "unit": item.get("unit", "pcs"),
            "base_rate": base_rate,
            "final_rate": round(final_rate, 2),
            "discount_applied": round(base_rate - final_rate, 2) if base_rate > final_rate else 0,
            "markup_applied": round(final_rate - base_rate, 2) if final_rate > base_rate else 0,
            "line_total": round(line_total, 2),
            "tax_percentage": item.get("tax_percentage", 0),
            "hsn_code": item.get("hsn_code", "")
        })
    
    return {
        "code": 0,
        "price_list_id": price_list_id,
        "price_list_name": price_list.get("name") if price_list else None,
        "line_items": line_items,
        "sub_total": round(total, 2)
    }

# ============== PHASE 2: BULK PRICE SETTING ==============

@router.post("/price-lists/{pricelist_id}/set-prices")
async def bulk_set_prices(pricelist_id: str, price_data: BulkItemPriceSet, request: Request):
    """Set prices for multiple items in a price list"""
    db = get_db()
    org_id = extract_org_id(request)
    
    pl = await db.price_lists.find_one({"pricelist_id": pricelist_id, "organization_id": org_id})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    results = {"updated": 0, "created": 0, "errors": []}
    
    # If percentage method, apply to all items
    if price_data.pricing_method == "percentage" and price_data.percentage != 0:
        # H-02: hard cap, Sprint 3 for cursor pagination
        items = await db.items.find({"is_active": True, "organization_id": org_id}, {"_id": 0}).to_list(500)
        
        for item in items:
            base_rate = item.get("sales_rate", 0) or item.get("rate", 0)
            new_rate = base_rate * (1 + request.percentage / 100)
            
            existing = await db.item_prices.find_one({
                "item_id": item["item_id"],
                "price_list_id": pricelist_id,
                "organization_id": org_id
            })
            
            if existing:
                await db.item_prices.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"rate": round(new_rate, 2), "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["updated"] += 1
            else:
                await db.item_prices.insert_one({
                    "price_id": f"IP-{uuid.uuid4().hex[:8].upper()}",
                    "item_id": item["item_id"],
                    "organization_id": org_id,
                    "item_name": item.get("name", ""),
                    "price_list_id": pricelist_id,
                    "price_list_name": pl.get("name", ""),
                    "rate": round(new_rate, 2),
                    "created_time": datetime.now(timezone.utc).isoformat(),
                    "updated_time": datetime.now(timezone.utc).isoformat()
                })
                results["created"] += 1
    
    # Custom prices for specific items
    elif price_data.pricing_method == "custom" and price_data.items:
        for item_price in price_data.items:
            item_id = item_price.get("item_id")
            custom_rate = item_price.get("custom_rate", 0)
            
            item = await db.items.find_one({"item_id": item_id, "organization_id": org_id})
            if not item:
                results["errors"].append(f"Item {item_id} not found")
                continue
            
            existing = await db.item_prices.find_one({
                "item_id": item_id,
                "price_list_id": pricelist_id,
                "organization_id": org_id
            })
            
            if existing:
                await db.item_prices.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"rate": custom_rate, "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                results["updated"] += 1
            else:
                await db.item_prices.insert_one({
                    "price_id": f"IP-{uuid.uuid4().hex[:8].upper()}",
                    "item_id": item_id,
                    "organization_id": org_id,
                    "item_name": item.get("name", ""),
                    "price_list_id": pricelist_id,
                    "price_list_name": pl.get("name", ""),
                    "rate": custom_rate,
                    "created_time": datetime.now(timezone.utc).isoformat(),
                    "updated_time": datetime.now(timezone.utc).isoformat()
                })
                results["created"] += 1
    
    return {"code": 0, "message": "Prices updated", "results": results}

# ============== PHASE 2: BARCODE/QR SUPPORT ==============

@router.post("/barcodes")
async def create_item_barcode(barcode: ItemBarcodeCreate, request: Request):
    """Create or update barcode for an item"""
    db = get_db()
    org_id = extract_org_id(request)
    
    item = await db.items.find_one({"item_id": barcode.item_id, "organization_id": org_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Generate barcode value if not provided
    barcode_value = barcode.barcode_value
    if not barcode_value:
        # Use SKU if available, otherwise generate
        barcode_value = item.get("sku") or f"ITM{barcode.item_id[-8:].upper()}"
    
    # Update item with barcode
    await db.items.update_one(
        {"item_id": barcode.item_id, "organization_id": org_id},
        {"$set": {
            "barcode_type": barcode.barcode_type,
            "barcode_value": barcode_value,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log history
    await log_item_history(db, barcode.item_id, "barcode_added", {
        "barcode_type": barcode.barcode_type,
        "barcode_value": barcode_value
    }, "System", org_id=org_id)
    
    return {
        "code": 0,
        "message": "Barcode created",
        "barcode": {
            "item_id": barcode.item_id,
            "barcode_type": barcode.barcode_type,
            "barcode_value": barcode_value
        }
    }

@router.get("/lookup/barcode/{barcode_value}")
async def lookup_by_barcode(barcode_value: str, request: Request):
    """Look up item by barcode or SKU"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Search by barcode_value or SKU
    item = await db.items.find_one({
        "organization_id": org_id,
        "$or": [
            {"barcode_value": barcode_value},
            {"sku": barcode_value}
        ]
    }, {"_id": 0})
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found with this barcode/SKU")
    
    # Get stock info
    stock_locations = await db.item_stock_locations.find(
        {"item_id": item["item_id"], "organization_id": org_id},
        {"_id": 0}
    ).to_list(100)
    
    item["stock_locations"] = stock_locations
    
    return {"code": 0, "item": item}

@router.post("/lookup/batch")
async def batch_barcode_lookup(barcodes: List[str], request: Request):
    """Look up multiple items by barcode/SKU"""
    db = get_db()
    org_id = extract_org_id(request)
    
    results = []
    not_found = []
    
    for barcode in barcodes:
        item = await db.items.find_one({
            "organization_id": org_id,
            "$or": [
                {"barcode_value": barcode},
                {"sku": barcode}
            ]
        }, {"_id": 0})
        
        if item:
            results.append({
                "barcode": barcode,
                "item_id": item.get("item_id"),
                "name": item.get("name"),
                "sku": item.get("sku"),
                "stock": item.get("stock_on_hand", 0) or item.get("available_stock", 0),
                "rate": item.get("sales_rate", 0)
            })
        else:
            not_found.append(barcode)
    
    return {"code": 0, "items": results, "not_found": not_found}

# ============== SINGLE ITEM PRICE LOOKUP (FOR QUOTES/INVOICES INTEGRATION) ==============

@router.get("/item-price/{item_id}")
async def get_item_price_for_contact(
    item_id: str,
    request: Request,
    contact_id: str = "",
    transaction_type: str = "sales"
):
    """
    Get the price for a single item based on contact's assigned price list.
    Used by Quotes/Invoices for automatic pricing when selecting items.
    
    Returns:
    - base_rate: Standard item rate
    - final_rate: Rate after applying price list (if any)
    - price_list_id/name: The applied price list (if any)
    - discount/markup applied: The adjustment made
    """
    db = get_db()
    org_id = extract_org_id(request)
    
    # Get item
    item = await db.items.find_one({"item_id": item_id, "organization_id": org_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get base rate
    if transaction_type == "sales":
        base_rate = item.get("sales_rate", 0) or item.get("rate", 0)
    else:
        base_rate = item.get("purchase_rate", 0)
    
    result = {
        "item_id": item_id,
        "item_name": item.get("name"),
        "sku": item.get("sku"),
        "description": item.get("description", ""),
        "unit": item.get("unit", "pcs"),
        "base_rate": base_rate,
        "final_rate": base_rate,
        "price_list_id": None,
        "price_list_name": None,
        "discount_applied": 0,
        "markup_applied": 0,
        "tax_percentage": item.get("tax_percentage", 0),
        "hsn_code": item.get("hsn_code", ""),
        "stock_on_hand": item.get("stock_on_hand", 0)
    }
    
    # If no contact, return base rate
    if not contact_id:
        return {"code": 0, "pricing": result}
    
    # Get contact's price list
    contact = await db.contacts_enhanced.find_one({"contact_id": contact_id, "organization_id": org_id})
    if not contact:
        contact = await db.contacts.find_one({"contact_id": contact_id, "organization_id": org_id})
    
    if not contact:
        return {"code": 0, "pricing": result}
    
    # Get assigned price list
    if transaction_type == "sales":
        price_list_id = contact.get("sales_price_list_id")
    else:
        price_list_id = contact.get("purchase_price_list_id")
    
    if not price_list_id:
        return {"code": 0, "pricing": result}
    
    # Get price list details
    price_list = await db.price_lists.find_one({"pricelist_id": price_list_id, "organization_id": org_id}, {"_id": 0})
    if not price_list:
        return {"code": 0, "pricing": result}
    
    result["price_list_id"] = price_list_id
    result["price_list_name"] = price_list.get("name", "")
    
    final_rate = base_rate
    
    # Check for custom price in price list
    custom_price = await db.item_prices.find_one({
        "item_id": item_id,
        "price_list_id": price_list_id,
        "organization_id": org_id
    })
    
    if custom_price:
        final_rate = custom_price.get("rate", base_rate)
    else:
        # Apply percentage markup/discount from price list
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
    
    result["final_rate"] = round(final_rate, 2)
    
    if base_rate > final_rate:
        result["discount_applied"] = round(base_rate - final_rate, 2)
    elif final_rate > base_rate:
        result["markup_applied"] = round(final_rate - base_rate, 2)
    
    return {"code": 0, "pricing": result}


@router.get("/contact-pricing-summary/{contact_id}")
async def get_contact_pricing_summary(contact_id: str, request: Request):
    """
    Get a summary of the pricing configuration for a contact.
    Useful for displaying which price list is being applied in Quotes/Invoices UI.
    """
    db = get_db()
    org_id = extract_org_id(request)
    
    contact = await db.contacts_enhanced.find_one({"contact_id": contact_id, "organization_id": org_id})
    if not contact:
        contact = await db.contacts.find_one({"contact_id": contact_id, "organization_id": org_id})
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    result = {
        "contact_id": contact_id,
        "contact_name": contact.get("company_name") or contact.get("name") or contact.get("display_name", ""),
        "sales_price_list": None,
        "purchase_price_list": None
    }
    
    # Get sales price list
    sales_pl_id = contact.get("sales_price_list_id")
    if sales_pl_id:
        pl = await db.price_lists.find_one({"pricelist_id": sales_pl_id, "organization_id": org_id}, {"_id": 0})
        if pl:
            result["sales_price_list"] = {
                "pricelist_id": sales_pl_id,
                "name": pl.get("name", ""),
                "discount_percentage": pl.get("discount_percentage", 0),
                "markup_percentage": pl.get("markup_percentage", 0)
            }
    
    # Get purchase price list
    purchase_pl_id = contact.get("purchase_price_list_id")
    if purchase_pl_id:
        pl = await db.price_lists.find_one({"pricelist_id": purchase_pl_id, "organization_id": org_id}, {"_id": 0})
        if pl:
            result["purchase_price_list"] = {
                "pricelist_id": purchase_pl_id,
                "name": pl.get("name", ""),
                "discount_percentage": pl.get("discount_percentage", 0),
                "markup_percentage": pl.get("markup_percentage", 0)
            }
    
    return {"code": 0, "pricing_summary": result}


# ============== PHASE 3: ADVANCED REPORTS ==============

@router.get("/reports/sales-by-item")
async def get_sales_by_item_report(
    request: Request,
    start_date: str = "",
    end_date: str = "",
    item_id: str = "",
    group_id: str = "",
    customer_id: str = ""
):
    """Sales by Item report - shows quantity sold and revenue per item"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Build query for invoices
    query = {"organization_id": org_id, "status": {"$in": ["paid", "sent", "overdue", "partially_paid"]}}
    
    if start_date:
        query["invoice_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("invoice_date", {})["$lte"] = end_date
    if customer_id:
        query["customer_id"] = customer_id
    
    # H-02: hard cap, Sprint 3 for cursor pagination
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(500)
    
    # Aggregate sales by item
    item_sales = {}
    
    for invoice in invoices:
        for line in invoice.get("line_items", []):
            line_item_id = line.get("item_id")
            if not line_item_id:
                continue
            
            # Filter by item or group if specified
            if item_id and line_item_id != item_id:
                continue
            
            if line_item_id not in item_sales:
                item_sales[line_item_id] = {
                    "item_id": line_item_id,
                    "item_name": line.get("item_name", line.get("name", "")),
                    "sku": line.get("sku", ""),
                    "quantity_sold": 0,
                    "total_revenue": 0,
                    "invoice_count": 0,
                    "avg_selling_price": 0
                }
            
            qty = line.get("quantity", 0)
            rate = line.get("rate", 0)
            
            item_sales[line_item_id]["quantity_sold"] += qty
            item_sales[line_item_id]["total_revenue"] += qty * rate
            item_sales[line_item_id]["invoice_count"] += 1
    
    # Calculate averages and sort
    report_items = []
    for item_data in item_sales.values():
        if item_data["quantity_sold"] > 0:
            item_data["avg_selling_price"] = round(
                item_data["total_revenue"] / item_data["quantity_sold"], 2
            )
        item_data["total_revenue"] = round(item_data["total_revenue"], 2)
        report_items.append(item_data)
    
    report_items.sort(key=lambda x: x["total_revenue"], reverse=True)
    
    total_revenue = sum(i["total_revenue"] for i in report_items)
    total_quantity = sum(i["quantity_sold"] for i in report_items)
    
    return {
        "code": 0,
        "report": {
            "title": "Sales by Item",
            "period": {"start_date": start_date or "All time", "end_date": end_date or "Present"},
            "summary": {
                "total_items": len(report_items),
                "total_quantity_sold": total_quantity,
                "total_revenue": round(total_revenue, 2)
            },
            "items": report_items
        }
    }

@router.get("/reports/purchases-by-item")
async def get_purchases_by_item_report(
    request: Request,
    start_date: str = "",
    end_date: str = "",
    item_id: str = "",
    vendor_id: str = ""
):
    """Purchases by Item report"""
    db = get_db()
    org_id = extract_org_id(request)
    
    query = {"organization_id": org_id, "status": {"$in": ["paid", "pending", "overdue", "partially_paid"]}}
    
    if start_date:
        query["bill_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("bill_date", {})["$lte"] = end_date
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    # H-02: hard cap, Sprint 3 for cursor pagination
    bills = await db.bills.find(query, {"_id": 0}).to_list(500)
    
    item_purchases = {}
    
    for bill in bills:
        for line in bill.get("line_items", []):
            line_item_id = line.get("item_id")
            if not line_item_id:
                continue
            
            if item_id and line_item_id != item_id:
                continue
            
            if line_item_id not in item_purchases:
                item_purchases[line_item_id] = {
                    "item_id": line_item_id,
                    "item_name": line.get("item_name", line.get("name", "")),
                    "sku": line.get("sku", ""),
                    "quantity_purchased": 0,
                    "total_cost": 0,
                    "bill_count": 0,
                    "avg_purchase_price": 0
                }
            
            qty = line.get("quantity", 0)
            rate = line.get("rate", 0)
            
            item_purchases[line_item_id]["quantity_purchased"] += qty
            item_purchases[line_item_id]["total_cost"] += qty * rate
            item_purchases[line_item_id]["bill_count"] += 1
    
    report_items = []
    for item_data in item_purchases.values():
        if item_data["quantity_purchased"] > 0:
            item_data["avg_purchase_price"] = round(
                item_data["total_cost"] / item_data["quantity_purchased"], 2
            )
        item_data["total_cost"] = round(item_data["total_cost"], 2)
        report_items.append(item_data)
    
    report_items.sort(key=lambda x: x["total_cost"], reverse=True)
    
    total_cost = sum(i["total_cost"] for i in report_items)
    total_quantity = sum(i["quantity_purchased"] for i in report_items)
    
    return {
        "code": 0,
        "report": {
            "title": "Purchases by Item",
            "period": {"start_date": start_date or "All time", "end_date": end_date or "Present"},
            "summary": {
                "total_items": len(report_items),
                "total_quantity_purchased": total_quantity,
                "total_cost": round(total_cost, 2)
            },
            "items": report_items
        }
    }

@router.get("/reports/inventory-valuation")
async def get_inventory_valuation_report(
    request: Request,
    valuation_method: str = "fifo",
    warehouse_id: str = "",
    as_of_date: str = ""
):
    """Inventory valuation report with FIFO/LIFO tracking"""
    db = get_db()
    org_id = extract_org_id(request)
    
    query = {"organization_id": org_id, "item_type": {"$in": ["inventory", "sales_and_purchases"]}, "is_active": True}
    
    # H-02: hard cap, Sprint 3 for cursor pagination
    items = await db.items.find(query, {"_id": 0}).to_list(500)
    
    valuation_items = []
    total_value = 0
    
    for item in items:
        stock = item.get("stock_on_hand", 0) or item.get("available_stock", 0)
        if isinstance(stock, str):
            stock = float(stock) if stock else 0
        
        # Get cost rate (purchase rate or opening stock rate)
        cost_rate = item.get("purchase_rate", 0) or item.get("opening_stock_rate", 0)
        if isinstance(cost_rate, str):
            cost_rate = float(cost_rate) if cost_rate else 0
        
        stock_value = stock * cost_rate
        total_value += stock_value
        
        # Get recent purchase lots for FIFO display
        recent_adjustments = await db.item_adjustments.find(
            {"item_id": item.get("item_id"), "adjustment_type": "add", "organization_id": org_id},
            {"_id": 0}
        ).sort("created_time", -1).limit(5).to_list(5)
        
        valuation_items.append({
            "item_id": item.get("item_id"),
            "item_name": item.get("name"),
            "sku": item.get("sku"),
            "stock_on_hand": stock,
            "unit": item.get("unit", "pcs"),
            "cost_rate": round(cost_rate, 2),
            "stock_value": round(stock_value, 2),
            "valuation_method": item.get("inventory_valuation_method", valuation_method),
            "recent_lots": [{
                "date": adj.get("date", adj.get("created_time", ""))[:10],
                "quantity": adj.get("quantity", 0),
                "rate": adj.get("rate_per_unit", cost_rate)
            } for adj in recent_adjustments]
        })
    
    valuation_items.sort(key=lambda x: x["stock_value"], reverse=True)
    
    return {
        "code": 0,
        "report": {
            "title": "Inventory Valuation",
            "as_of_date": as_of_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "valuation_method": valuation_method.upper(),
            "summary": {
                "total_items": len(valuation_items),
                "total_stock_value": round(total_value, 2)
            },
            "items": valuation_items
        }
    }

@router.get("/reports/item-movement")
async def get_item_movement_report(
    request: Request,
    item_id: str,
    start_date: str = "",
    end_date: str = ""
):
    """Item movement report - all stock in/out for an item"""
    db = get_db()
    org_id = extract_org_id(request)
    
    item = await db.items.find_one({"item_id": item_id, "organization_id": org_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    movements = []
    
    # Get adjustments
    adj_query = {"item_id": item_id, "organization_id": org_id}
    if start_date:
        adj_query["created_time"] = {"$gte": start_date}
    if end_date:
        adj_query.setdefault("created_time", {})["$lte"] = end_date + "T23:59:59"
    
    adjustments = await db.item_adjustments.find(adj_query, {"_id": 0}).to_list(1000)
    
    for adj in adjustments:
        movements.append({
            "date": adj.get("date", adj.get("created_time", ""))[:10],
            "type": "adjustment",
            "direction": "in" if adj.get("adjustment_type") == "add" else "out",
            "quantity": adj.get("quantity", 0),
            "reference": adj.get("adjustment_id", ""),
            "reason": adj.get("reason", ""),
            "warehouse": adj.get("warehouse_name", "")
        })
    
    # Get invoice line items (sales = out)
    inv_query = {"organization_id": org_id, "line_items.item_id": item_id}
    if start_date:
        inv_query["invoice_date"] = {"$gte": start_date}
    if end_date:
        inv_query.setdefault("invoice_date", {})["$lte"] = end_date
    
    invoices = await db.invoices.find(inv_query, {"_id": 0}).to_list(1000)
    
    for inv in invoices:
        for line in inv.get("line_items", []):
            if line.get("item_id") == item_id:
                movements.append({
                    "date": inv.get("invoice_date", "")[:10],
                    "type": "sale",
                    "direction": "out",
                    "quantity": line.get("quantity", 0),
                    "reference": inv.get("invoice_number", inv.get("invoice_id", "")),
                    "reason": f"Sold to {inv.get('customer_name', '')}",
                    "warehouse": ""
                })
    
    # Get bill line items (purchases = in)
    bill_query = {"organization_id": org_id, "line_items.item_id": item_id}
    if start_date:
        bill_query["bill_date"] = {"$gte": start_date}
    if end_date:
        bill_query.setdefault("bill_date", {})["$lte"] = end_date
    
    bills = await db.bills.find(bill_query, {"_id": 0}).to_list(1000)
    
    for bill in bills:
        for line in bill.get("line_items", []):
            if line.get("item_id") == item_id:
                movements.append({
                    "date": bill.get("bill_date", "")[:10],
                    "type": "purchase",
                    "direction": "in",
                    "quantity": line.get("quantity", 0),
                    "reference": bill.get("bill_number", bill.get("bill_id", "")),
                    "reason": f"Purchased from {bill.get('vendor_name', '')}",
                    "warehouse": ""
                })
    
    # Sort by date
    movements.sort(key=lambda x: x["date"], reverse=True)
    
    # Calculate running balance
    total_in = sum(m["quantity"] for m in movements if m["direction"] == "in")
    total_out = sum(m["quantity"] for m in movements if m["direction"] == "out")
    
    return {
        "code": 0,
        "report": {
            "title": f"Item Movement: {item.get('name')}",
            "item": {
                "item_id": item_id,
                "name": item.get("name"),
                "sku": item.get("sku"),
                "current_stock": item.get("stock_on_hand", 0) or item.get("available_stock", 0)
            },
            "period": {"start_date": start_date or "All time", "end_date": end_date or "Present"},
            "summary": {
                "total_in": total_in,
                "total_out": total_out,
                "net_change": total_in - total_out,
                "transaction_count": len(movements)
            },
            "movements": movements
        }
    }

# ============== INVENTORY REPORTS (MUST BE BEFORE /{item_id}) ==============

@router.get("/reports/stock-summary")
async def get_stock_summary(request: Request, warehouse_id: str = ""):
    """Get stock summary report"""
    db = get_db()
    org_id = extract_org_id(request)
    
    match_stage = {"organization_id": org_id, "item_type": {"$in": ["inventory", "sales_and_purchases"]}}
    
    # H-02: hard cap, Sprint 3 for cursor pagination
    items = await db.items.find(match_stage, {"_id": 0}).to_list(500)
    
    summary = {
        "total_items": len(items),
        "total_stock_value": 0,
        "low_stock_count": 0,
        "out_of_stock_count": 0,
        "items": []
    }
    
    for item in items:
        stock = item.get("stock_on_hand", 0) or item.get("available_stock", 0)
        if isinstance(stock, str):
            stock = float(stock) if stock else 0
        rate = item.get("purchase_rate", 0) or item.get("sales_rate", 0)
        if isinstance(rate, str):
            rate = float(rate) if rate else 0
        reorder_level = item.get("reorder_level", 0)
        if isinstance(reorder_level, str):
            reorder_level = float(reorder_level) if reorder_level else 0
        value = stock * rate
        
        item_summary = {
            "item_id": item.get("item_id"),
            "name": item.get("name"),
            "sku": item.get("sku"),
            "stock": stock,
            "reorder_level": reorder_level,
            "rate": rate,
            "value": round(value, 2),
            "is_low_stock": stock < reorder_level,
            "is_out_of_stock": stock <= 0
        }
        
        summary["items"].append(item_summary)
        summary["total_stock_value"] += value
        
        if item_summary["is_low_stock"]:
            summary["low_stock_count"] += 1
        if item_summary["is_out_of_stock"]:
            summary["out_of_stock_count"] += 1
    
    summary["total_stock_value"] = round(summary["total_stock_value"], 2)
    
    return {"code": 0, "stock_summary": summary}

@router.get("/reports/valuation")
async def get_inventory_valuation(request: Request):
    """Get inventory valuation report"""
    db = get_db()
    org_id = extract_org_id(request)
    
    pipeline = [
        {"$match": {"organization_id": org_id, "item_type": {"$in": ["inventory", "sales_and_purchases"]}}},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "name": 1,
            "sku": 1,
            "stock_on_hand": {"$ifNull": ["$stock_on_hand", {"$ifNull": ["$available_stock", 0]}]},
            "purchase_rate": {"$ifNull": ["$purchase_rate", "$sales_rate"]},
            "sales_rate": 1
        }},
        {"$addFields": {
            "purchase_value": {"$multiply": ["$stock_on_hand", "$purchase_rate"]},
            "sales_value": {"$multiply": ["$stock_on_hand", "$sales_rate"]}
        }},
        {"$group": {
            "_id": None,
            "items": {"$push": "$$ROOT"},
            "total_purchase_value": {"$sum": "$purchase_value"},
            "total_sales_value": {"$sum": "$sales_value"},
            "total_items": {"$sum": 1},
            "total_stock": {"$sum": "$stock_on_hand"}
        }}
    ]
    
    result = await db.items.aggregate(pipeline).to_list(1)
    
    if result:
        return {
            "code": 0,
            "valuation": {
                "total_items": result[0].get("total_items", 0),
                "total_stock": result[0].get("total_stock", 0),
                "total_purchase_value": round(result[0].get("total_purchase_value", 0), 2),
                "total_sales_value": round(result[0].get("total_sales_value", 0), 2),
                "items": result[0].get("items", [])
            }
        }
    
    return {"code": 0, "valuation": {"total_items": 0, "total_stock": 0, "total_purchase_value": 0, "total_sales_value": 0, "items": []}}

# ============== BULK ACTIONS (MUST BE BEFORE /{item_id}) ==============

@router.post("/bulk-action")
async def perform_bulk_action(bulk_request: BulkActionRequest, request: Request):
    """Perform bulk actions on multiple items"""
    db = get_db()
    org_id = extract_org_id(request)
    
    if not bulk_request.item_ids:
        raise HTTPException(status_code=400, detail="No items selected")
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    for item_id in bulk_request.item_ids:
        try:
            if bulk_request.action == "activate":
                await db.items.update_one(
                    {"item_id": item_id, "organization_id": org_id},
                    {"$set": {"is_active": True, "status": "active", "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                await log_item_history(db, item_id, "activated", {}, "System", org_id=org_id)
                results["success"] += 1
                
            elif bulk_request.action == "deactivate":
                await db.items.update_one(
                    {"item_id": item_id, "organization_id": org_id},
                    {"$set": {"is_active": False, "status": "inactive", "updated_time": datetime.now(timezone.utc).isoformat()}}
                )
                await log_item_history(db, item_id, "deactivated", {}, "System", org_id=org_id)
                results["success"] += 1
                
            elif bulk_request.action == "delete":
                # Check for transactions
                invoice_count = await db.invoices.count_documents({"line_items.item_id": item_id, "organization_id": org_id})
                bill_count = await db.bills.count_documents({"line_items.item_id": item_id, "organization_id": org_id})
                
                if invoice_count > 0 or bill_count > 0:
                    results["errors"].append(f"Item {item_id} has transactions, cannot delete")
                    results["failed"] += 1
                else:
                    await db.item_stock_locations.delete_many({"item_id": item_id, "organization_id": org_id})
                    await db.item_prices.delete_many({"item_id": item_id, "organization_id": org_id})
                    await db.items.delete_one({"item_id": item_id, "organization_id": org_id})
                    results["success"] += 1
                    
            elif bulk_request.action == "clone":
                item = await db.items.find_one({"item_id": item_id, "organization_id": org_id}, {"_id": 0})
                if item:
                    new_id = f"I-{uuid.uuid4().hex[:12].upper()}"
                    item["item_id"] = new_id
                    item["name"] = f"{item['name']} (Copy)"
                    item["sku"] = f"{item.get('sku', '')}-COPY" if item.get('sku') else None
                    item["stock_on_hand"] = 0
                    item["available_stock"] = 0
                    item["created_time"] = datetime.now(timezone.utc).isoformat()
                    item["updated_time"] = datetime.now(timezone.utc).isoformat()
                    await db.items.insert_one(item)
                    await log_item_history(db, new_id, "cloned", {"source_item_id": item_id}, "System", org_id=org_id)
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    
        except Exception as e:
            results["errors"].append(f"Error on {item_id}: {str(e)}")
            results["failed"] += 1
    
    return {"code": 0, "results": results}

# ============== IMPORT/EXPORT (MUST BE BEFORE /{item_id}) ==============

@router.get("/export")
async def export_items(
    request: Request,
    format: str = "csv",
    item_type: str = "",
    group_id: str = "",
    include_inactive: bool = False
):
    """Export items to CSV (Zoho Books compatible) or JSON"""
    db = get_db()
    org_id = extract_org_id(request)
    
    query = {"organization_id": org_id}
    if item_type:
        query["item_type"] = item_type
    if group_id:
        query["$or"] = [{"group_id": group_id}, {"item_group_id": group_id}]
    if not include_inactive:
        query["is_active"] = True
    
    items = await db.items.find(query, {"_id": 0}).to_list(10000)
    
    if format == "json":
        return {"code": 0, "items": items, "count": len(items)}
    
    # CSV export - Zoho Books compatible columns
    output = io.StringIO()
    fieldnames = [
        "Item ID", "Item Name", "SKU", "HSN/SAC", "Description", "Rate",
        "Account", "Account Code", "Taxable", "Exemption Reason", "Taxability Type",
        "Product Type", "Intra State Tax Name", "Intra State Tax Rate", "Intra State Tax Type",
        "Inter State Tax Name", "Inter State Tax Rate", "Inter State Tax Type",
        "Source", "Reference ID", "Last Sync Time", "Status",
        "Usage unit", "Unit Name", "Purchase Rate", "Purchase Account", "Purchase Account Code",
        "Purchase Description", "Inventory Account", "Inventory Account Code",
        "Inventory Valuation Method", "Reorder Point", "Vendor", "Location Name",
        "Opening Stock", "Opening Stock Value", "Stock On Hand",
        "Item Type", "Sellable", "Purchasable", "Track Inventory"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for item in items:
        row = {
            "Item ID": item.get("item_id", ""),
            "Item Name": item.get("name", ""),
            "SKU": item.get("sku", ""),
            "HSN/SAC": item.get("hsn_code", "") or item.get("sac_code", ""),
            "Description": item.get("description", ""),
            "Rate": item.get("rate", "") or item.get("sales_rate", ""),
            "Account": item.get("sales_account", ""),
            "Account Code": item.get("sales_account_code", ""),
            "Taxable": "Yes" if item.get("taxable", True) else "No",
            "Exemption Reason": item.get("exemption_reason", ""),
            "Taxability Type": item.get("taxability_type", ""),
            "Product Type": item.get("product_type", "goods"),
            "Intra State Tax Name": item.get("intra_state_tax_name", "GST"),
            "Intra State Tax Rate": item.get("intra_state_tax_rate", 18),
            "Intra State Tax Type": item.get("intra_state_tax_type", "percentage"),
            "Inter State Tax Name": item.get("inter_state_tax_name", "IGST"),
            "Inter State Tax Rate": item.get("inter_state_tax_rate", 18),
            "Inter State Tax Type": item.get("inter_state_tax_type", "percentage"),
            "Source": item.get("source", "Manual"),
            "Reference ID": item.get("reference_id", "") or item.get("zoho_item_id", ""),
            "Last Sync Time": item.get("last_sync_time", ""),
            "Status": item.get("status", "active"),
            "Usage unit": item.get("usage_unit", "") or item.get("unit", "pcs"),
            "Unit Name": item.get("unit_name", ""),
            "Purchase Rate": item.get("purchase_rate", ""),
            "Purchase Account": item.get("purchase_account", ""),
            "Purchase Account Code": item.get("purchase_account_code", ""),
            "Purchase Description": item.get("purchase_description", ""),
            "Inventory Account": item.get("inventory_account", ""),
            "Inventory Account Code": item.get("inventory_account_code", ""),
            "Inventory Valuation Method": item.get("inventory_valuation_method", "FIFO").upper(),
            "Reorder Point": item.get("reorder_level", 0),
            "Vendor": item.get("vendor", "") or item.get("preferred_vendor_name", ""),
            "Location Name": item.get("location_name", ""),
            "Opening Stock": item.get("opening_stock", 0),
            "Opening Stock Value": item.get("opening_stock_value", 0),
            "Stock On Hand": item.get("stock_on_hand", item.get("available_stock", 0)),
            "Item Type": item.get("item_type", "inventory"),
            "Sellable": "Yes" if item.get("sellable", True) else "No",
            "Purchasable": "Yes" if item.get("purchasable", True) else "No",
            "Track Inventory": "Yes" if item.get("track_inventory", True) else "No"
        }
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=items_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.get("/export/template")
async def get_import_template():
    """Get CSV template for item import - Zoho Books compatible"""
    output = io.StringIO()
    fieldnames = [
        "Item Name", "SKU", "HSN/SAC", "Description", "Rate",
        "Account", "Account Code", "Taxable", "Exemption Reason", "Taxability Type",
        "Product Type", "Intra State Tax Name", "Intra State Tax Rate", "Intra State Tax Type",
        "Inter State Tax Name", "Inter State Tax Rate", "Inter State Tax Type",
        "Source", "Reference ID", "Status",
        "Usage unit", "Unit Name", "Purchase Rate", "Purchase Account", "Purchase Account Code",
        "Purchase Description", "Inventory Account", "Inventory Account Code",
        "Inventory Valuation Method", "Reorder Point", "Vendor", "Location Name",
        "Opening Stock", "Opening Stock Value",
        "Item Type", "Sellable", "Purchasable", "Track Inventory"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Sample rows
    writer.writerow({
        "Item Name": "12V 20Ah Battery",
        "SKU": "BAT-12V20-001",
        "HSN/SAC": "85076000",
        "Description": "Lithium-ion battery 12V 20Ah for E-Rickshaw",
        "Rate": "4500",
        "Account": "Sales",
        "Account Code": "4000",
        "Taxable": "Yes",
        "Exemption Reason": "",
        "Taxability Type": "Goods",
        "Product Type": "goods",
        "Intra State Tax Name": "GST",
        "Intra State Tax Rate": "18",
        "Intra State Tax Type": "percentage",
        "Inter State Tax Name": "IGST",
        "Inter State Tax Rate": "18",
        "Inter State Tax Type": "percentage",
        "Source": "Manual",
        "Reference ID": "",
        "Status": "active",
        "Usage unit": "pcs",
        "Unit Name": "Pieces",
        "Purchase Rate": "3500",
        "Purchase Account": "Cost of Goods Sold",
        "Purchase Account Code": "5000",
        "Purchase Description": "12V 20Ah Li-ion Battery",
        "Inventory Account": "Inventory",
        "Inventory Account Code": "1200",
        "Inventory Valuation Method": "FIFO",
        "Reorder Point": "10",
        "Vendor": "Battery Suppliers Ltd",
        "Location Name": "Main Warehouse",
        "Opening Stock": "50",
        "Opening Stock Value": "175000",
        "Item Type": "inventory",
        "Sellable": "Yes",
        "Purchasable": "Yes",
        "Track Inventory": "Yes"
    })
    
    writer.writerow({
        "Item Name": "Motor Service Labour",
        "SKU": "SRV-MOTOR-001",
        "HSN/SAC": "998719",
        "Description": "Motor repair and maintenance service",
        "Rate": "500",
        "Account": "Service Revenue",
        "Account Code": "4100",
        "Taxable": "Yes",
        "Exemption Reason": "",
        "Taxability Type": "Service",
        "Product Type": "service",
        "Intra State Tax Name": "GST",
        "Intra State Tax Rate": "18",
        "Intra State Tax Type": "percentage",
        "Inter State Tax Name": "IGST",
        "Inter State Tax Rate": "18",
        "Inter State Tax Type": "percentage",
        "Source": "Manual",
        "Reference ID": "",
        "Status": "active",
        "Usage unit": "hrs",
        "Unit Name": "Hours",
        "Purchase Rate": "",
        "Purchase Account": "",
        "Purchase Account Code": "",
        "Purchase Description": "",
        "Inventory Account": "",
        "Inventory Account Code": "",
        "Inventory Valuation Method": "",
        "Reorder Point": "",
        "Vendor": "",
        "Location Name": "",
        "Opening Stock": "",
        "Opening Stock Value": "",
        "Item Type": "service",
        "Sellable": "Yes",
        "Purchasable": "No",
        "Track Inventory": "No"
    })
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=items_import_template.csv"}
    )

@router.post("/import")
async def import_items(request: Request, file: UploadFile = File(...), overwrite_existing: bool = False):
    """Import items from CSV file"""
    db = get_db()
    org_id = extract_org_id(request)
    
    if not file.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Read file content
    content = await file.read()
    if len(content) > 1024 * 1024:  # 1MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 1MB limit")
    
    try:
        decoded = content.decode('utf-8')
    except:
        decoded = content.decode('latin-1')
    
    reader = csv.DictReader(io.StringIO(decoded))
    
    results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    
    for row_num, row in enumerate(reader, start=2):
        try:
            name = row.get("name", "").strip()
            if not name:
                results["errors"].append(f"Row {row_num}: Name is required")
                results["skipped"] += 1
                continue
            
            sku = row.get("sku", "").strip() or None
            
            # Check if exists
            existing = None
            if sku:
                existing = await db.items.find_one({"sku": sku, "organization_id": org_id})
            if not existing:
                existing = await db.items.find_one({"name": name, "organization_id": org_id})
            
            item_data = {
                "name": name,
                "sku": sku,
                "item_type": row.get("item_type", "inventory").strip() or "inventory",
                "group_name": row.get("group_name", "").strip(),
                "description": row.get("description", "").strip(),
                "sales_rate": float(row.get("sales_rate", 0) or 0),
                "purchase_rate": float(row.get("purchase_rate", 0) or 0),
                "unit": row.get("unit", "pcs").strip() or "pcs",
                "hsn_code": row.get("hsn_code", "").strip(),
                "sac_code": row.get("sac_code", "").strip(),
                "tax_percentage": float(row.get("tax_percentage", 18) or 18),
                "reorder_level": float(row.get("reorder_level", 0) or 0),
                "updated_time": datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                if overwrite_existing:
                    await db.items.update_one({"item_id": existing["item_id"], "organization_id": org_id}, {"$set": item_data})
                    await log_item_history(db, existing["item_id"], "updated", {"source": "import"}, "System", org_id=org_id)
                    results["updated"] += 1
                else:
                    results["skipped"] += 1
            else:
                item_id = f"I-{uuid.uuid4().hex[:12].upper()}"
                item_data["item_id"] = item_id
                item_data["organization_id"] = org_id
                item_data["rate"] = item_data["sales_rate"]
                item_data["hsn_or_sac"] = item_data["hsn_code"] or item_data["sac_code"]
                item_data["initial_stock"] = float(row.get("initial_stock", 0) or 0)
                item_data["stock_on_hand"] = item_data["initial_stock"]
                item_data["available_stock"] = item_data["initial_stock"]
                item_data["is_active"] = True
                item_data["status"] = "active"
                item_data["created_time"] = datetime.now(timezone.utc).isoformat()
                
                await db.items.insert_one(item_data)
                await log_item_history(db, item_id, "created", {"source": "import"}, "System", org_id=org_id)
                results["created"] += 1
                
        except Exception as e:
            results["errors"].append(f"Row {row_num}: {str(e)}")
            results["skipped"] += 1
    
    return {"code": 0, "results": results}

# ============== ITEM HISTORY (MUST BE BEFORE /{item_id}) ==============

async def log_item_history(db, item_id: str, action: str, changes: dict, user_name: str, org_id: str = None):
    """Helper function to log item history"""
    history_entry = {
        "history_id": f"IH-{uuid.uuid4().hex[:8].upper()}",
        "item_id": item_id,
        "organization_id": org_id,  # P1-01 FIX: org-scoped — Sprint 1C
        "action": action,
        "changes": changes,
        "user_name": user_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.item_history.insert_one(history_entry)

@router.get("/history")
async def get_all_item_history(
    request: Request,
    item_id: str = "",
    action: str = "",
    page: int = 1,
    per_page: int = 50
):
    """Get item history with filters"""
    db = get_db()
    org_id = extract_org_id(request)
    
    query = {"organization_id": org_id}
    if item_id:
        query["item_id"] = item_id
    if action:
        query["action"] = action
    
    skip = (page - 1) * per_page
    history = await db.item_history.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(per_page).to_list(per_page)
    total = await db.item_history.count_documents(query)
    
    return {
        "code": 0,
        "history": history,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

# ============== VALUE ADJUSTMENTS (MUST BE BEFORE /{item_id}) ==============

@router.post("/value-adjustments")
async def create_value_adjustment(adj: ValueAdjustmentCreate, request: Request):
    """Create inventory value adjustment"""
    db = get_db()
    org_id = extract_org_id(request)
    
    item = await db.items.find_one({"item_id": adj.item_id, "organization_id": org_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    current_rate = item.get("purchase_rate", 0) or item.get("sales_rate", 0)
    stock = item.get("stock_on_hand", 0) or item.get("available_stock", 0)
    
    old_value = stock * current_rate
    new_value = stock * adj.new_value_per_unit
    adjustment_amount = new_value - old_value
    
    adj_id = f"VADJ-{uuid.uuid4().hex[:8].upper()}"
    
    adj_dict = {
        "adjustment_id": adj_id,
        "organization_id": org_id,
        "item_id": adj.item_id,
        "item_name": item.get("name", ""),
        "warehouse_id": adj.warehouse_id,
        "adjustment_type": "value",
        "old_rate": current_rate,
        "new_rate": adj.new_value_per_unit,
        "stock_quantity": stock,
        "old_value": round(old_value, 2),
        "new_value": round(new_value, 2),
        "adjustment_amount": round(adjustment_amount, 2),
        "adjustment_account": adj.adjustment_account,
        "reason": adj.reason,
        "notes": adj.notes,
        "reference_number": adj.reference_number,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.item_adjustments.insert_one(adj_dict)
    
    # Update item rate
    await db.items.update_one(
        {"item_id": adj.item_id, "organization_id": org_id},
        {"$set": {
            "purchase_rate": adj.new_value_per_unit,
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_item_history(db, adj.item_id, "value_adjusted", {
        "old_rate": current_rate,
        "new_rate": adj.new_value_per_unit,
        "adjustment_amount": adjustment_amount
    }, "System")
    
    del adj_dict["_id"]
    return {"code": 0, "message": "Value adjustment created", "adjustment": adj_dict}

# ============== PREFERENCES & CUSTOM FIELDS (MUST BE BEFORE /{item_id}) ==============

@router.get("/preferences")
async def get_item_preferences(request: Request):
    """Get module preferences"""
    db = get_db()
    org_id = extract_org_id(request)
    
    prefs = await db.item_preferences.find_one({"type": "items_module", "organization_id": org_id}, {"_id": 0})
    if not prefs:
        prefs = ItemPreferences().dict()
        prefs["type"] = "items_module"
        prefs["organization_id"] = org_id
        prefs["created_time"] = datetime.now(timezone.utc).isoformat()
        await db.item_preferences.insert_one(prefs.copy())
        # Remove any _id that might have been added
        prefs.pop("_id", None)
    
    return {"code": 0, "preferences": prefs}

@router.put("/preferences")
async def update_item_preferences(prefs: ItemPreferences, request: Request):
    """Update module preferences"""
    db = get_db()
    org_id = extract_org_id(request)
    
    prefs_dict = prefs.dict()
    prefs_dict["type"] = "items_module"
    prefs_dict["organization_id"] = org_id
    prefs_dict["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    await db.item_preferences.update_one(
        {"type": "items_module", "organization_id": org_id},
        {"$set": prefs_dict},
        upsert=True
    )
    
    return {"code": 0, "message": "Preferences updated", "preferences": prefs_dict}

@router.get("/custom-fields")
async def get_custom_fields(request: Request):
    """Get custom field definitions"""
    db = get_db()
    org_id = extract_org_id(request)
    
    fields = await db.item_custom_fields.find({"organization_id": org_id}, {"_id": 0}).to_list(100)
    return {"code": 0, "custom_fields": fields}

@router.post("/custom-fields")
async def create_custom_field(field: CustomFieldDefinition, request: Request):
    """Create a custom field definition"""
    db = get_db()
    org_id = extract_org_id(request)
    
    if not field.field_id:
        field.field_id = f"CF-{uuid.uuid4().hex[:8].upper()}"
    
    # Check unique name
    existing = await db.item_custom_fields.find_one({"field_name": field.field_name, "organization_id": org_id})
    if existing:
        raise HTTPException(status_code=400, detail="Field with this name already exists")
    
    field_dict = field.dict()
    field_dict["organization_id"] = org_id
    field_dict["created_time"] = datetime.now(timezone.utc).isoformat()
    
    await db.item_custom_fields.insert_one(field_dict)
    del field_dict["_id"]
    
    return {"code": 0, "message": "Custom field created", "field": field_dict}

@router.put("/custom-fields/{field_id}")
async def update_custom_field(field_id: str, field: CustomFieldDefinition, request: Request):
    """Update a custom field"""
    db = get_db()
    org_id = extract_org_id(request)
    
    field_dict = field.dict()
    field_dict["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.item_custom_fields.update_one(
        {"field_id": field_id, "organization_id": org_id},
        {"$set": field_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Custom field not found")
    
    return {"code": 0, "message": "Custom field updated"}

@router.delete("/custom-fields/{field_id}")
async def delete_custom_field(field_id: str, request: Request):
    """Delete a custom field"""
    db = get_db()
    org_id = extract_org_id(request)
    
    result = await db.item_custom_fields.delete_one({"field_id": field_id, "organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Custom field not found")
    
    return {"code": 0, "message": "Custom field deleted"}

# ============== FIELD CONFIGURATION (Phase 3) ==============

# Default field definitions
DEFAULT_FIELDS = [
    {"field_name": "name", "display_name": "Item Name", "is_mandatory": True, "show_in_list": True, "show_in_pdf": True, "field_order": 1},
    {"field_name": "sku", "display_name": "SKU", "is_mandatory": False, "show_in_list": True, "show_in_pdf": True, "field_order": 2},
    {"field_name": "item_type", "display_name": "Item Type", "is_mandatory": True, "show_in_list": True, "show_in_pdf": False, "field_order": 3},
    {"field_name": "description", "display_name": "Description", "is_mandatory": False, "show_in_list": False, "show_in_pdf": True, "field_order": 4},
    {"field_name": "sales_rate", "display_name": "Selling Price", "is_mandatory": True, "show_in_list": True, "show_in_pdf": True, "field_order": 5},
    {"field_name": "purchase_rate", "display_name": "Cost Price", "is_mandatory": False, "show_in_list": True, "show_in_pdf": False, "field_order": 6},
    {"field_name": "unit", "display_name": "Unit", "is_mandatory": True, "show_in_list": True, "show_in_pdf": True, "field_order": 7},
    {"field_name": "hsn_code", "display_name": "HSN Code", "is_mandatory": False, "show_in_list": True, "show_in_pdf": True, "field_order": 8},
    {"field_name": "sac_code", "display_name": "SAC Code", "is_mandatory": False, "show_in_list": False, "show_in_pdf": True, "field_order": 9},
    {"field_name": "tax_percentage", "display_name": "Tax %", "is_mandatory": False, "show_in_list": False, "show_in_pdf": True, "field_order": 10},
    {"field_name": "stock_on_hand", "display_name": "Stock", "is_mandatory": False, "show_in_list": True, "show_in_pdf": False, "field_order": 11},
    {"field_name": "reorder_level", "display_name": "Reorder Level", "is_mandatory": False, "show_in_list": False, "show_in_pdf": False, "field_order": 12},
    {"field_name": "group_name", "display_name": "Item Group", "is_mandatory": False, "show_in_list": True, "show_in_pdf": False, "field_order": 13},
    {"field_name": "barcode_value", "display_name": "Barcode", "is_mandatory": False, "show_in_list": False, "show_in_pdf": True, "field_order": 14},
    {"field_name": "image_url", "display_name": "Image", "is_mandatory": False, "show_in_list": False, "show_in_pdf": True, "field_order": 15},
]

@router.get("/field-config")
async def get_field_configuration(request: Request):
    """Get field visibility and access configuration"""
    db = get_db()
    org_id = extract_org_id(request)
    
    fields = await db.item_field_config.find({"organization_id": org_id}, {"_id": 0}).sort("field_order", 1).to_list(100)
    
    # If no config exists, create defaults
    if not fields:
        for field in DEFAULT_FIELDS:
            field["is_active"] = True
            field["show_in_form"] = True
            field["allowed_roles"] = ["admin", "manager", "user"]
            field["organization_id"] = org_id
            field["created_time"] = datetime.now(timezone.utc).isoformat()
            await db.item_field_config.insert_one(field.copy())
        fields = DEFAULT_FIELDS
    
    return {"code": 0, "field_config": fields}

@router.put("/field-config")
async def update_field_configuration(fields: List[FieldConfiguration], request: Request):
    """Update field visibility and access configuration"""
    db = get_db()
    org_id = extract_org_id(request)
    
    for field in fields:
        field_dict = field.dict()
        field_dict["updated_time"] = datetime.now(timezone.utc).isoformat()
        
        await db.item_field_config.update_one(
            {"field_name": field.field_name, "organization_id": org_id},
            {"$set": field_dict},
            upsert=True
        )
    
    return {"code": 0, "message": "Field configuration updated"}

@router.put("/field-config/{field_name}")
async def update_single_field_config(field_name: str, config: FieldConfiguration, request: Request):
    """Update configuration for a single field"""
    db = get_db()
    org_id = extract_org_id(request)
    
    config_dict = config.dict()
    config_dict["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.item_field_config.update_one(
        {"field_name": field_name, "organization_id": org_id},
        {"$set": config_dict},
        upsert=True
    )
    
    return {"code": 0, "message": f"Field '{field_name}' configuration updated"}

@router.get("/field-config/for-role/{role}")
async def get_fields_for_role(role: str, request: Request):
    """Get visible fields for a specific role"""
    db = get_db()
    org_id = extract_org_id(request)
    
    fields = await db.item_field_config.find(
        {"is_active": True, "allowed_roles": role, "organization_id": org_id},
        {"_id": 0}
    ).sort("field_order", 1).to_list(100)
    
    return {
        "code": 0,
        "role": role,
        "list_fields": [f for f in fields if f.get("show_in_list")],
        "form_fields": [f for f in fields if f.get("show_in_form")],
        "pdf_fields": [f for f in fields if f.get("show_in_pdf")]
    }

# ============== AUTO SKU GENERATION ==============

@router.get("/generate-sku")
async def generate_sku(request: Request):
    """Generate next SKU based on preferences"""
    db = get_db()
    org_id = extract_org_id(request)
    
    prefs = await db.item_preferences.find_one({"type": "items_module", "organization_id": org_id})
    if not prefs or not prefs.get("auto_generate_sku"):
        return {"code": 1, "message": "Auto SKU generation is disabled"}
    
    prefix = prefs.get("sku_prefix", "SKU-")
    
    # Find the highest SKU number
    last_item = await db.items.find_one(
        {"sku": {"$regex": f"^{re.escape(prefix)}\\d+$"}, "organization_id": org_id},
        sort=[("sku", -1)]
    )
    
    if last_item and last_item.get("sku"):
        try:
            last_num = int(last_item["sku"].replace(prefix, ""))
            next_num = last_num + 1
        except:
            next_num = prefs.get("sku_sequence_start", 1)
    else:
        next_num = prefs.get("sku_sequence_start", 1)
    
    new_sku = f"{prefix}{next_num:04d}"
    
    return {"code": 0, "sku": new_sku, "next_sequence": next_num}

# ============== HSN/SAC VALIDATION (MUST BE BEFORE /{item_id}) ==============

@router.post("/validate-hsn")
async def validate_hsn_code(hsn_code: str = ""):
    """Validate HSN code format"""
    if not hsn_code:
        return {"code": 0, "valid": True, "message": "No HSN code provided"}
    
    # HSN codes should be 4, 6, or 8 digits
    if not re.match(r'^\d{4}$|^\d{6}$|^\d{8}$', hsn_code):
        return {"code": 1, "valid": False, "message": "HSN code must be 4, 6, or 8 digits"}
    
    return {"code": 0, "valid": True, "message": "Valid HSN code"}

@router.post("/validate-sac")
async def validate_sac_code(sac_code: str = ""):
    """Validate SAC code format"""
    if not sac_code:
        return {"code": 0, "valid": True, "message": "No SAC code provided"}
    
    # SAC codes are 6 digits starting with 99
    if not re.match(r'^99\d{4}$', sac_code):
        return {"code": 1, "valid": False, "message": "SAC code must be 6 digits starting with 99"}
    
    return {"code": 0, "valid": True, "message": "Valid SAC code"}

# ============== ITEM ROUTES WITH PATH PARAMETERS (MUST BE LAST) ==============

@router.get("/{item_id}")
async def get_enhanced_item(item_id: str, request: Request):
    """Get item with full details"""
    db = get_db()
    org_id = extract_org_id(request)
    item = await db.items.find_one({"item_id": item_id, "organization_id": org_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get stock locations
    stock_locations = await db.item_stock_locations.find(
        {"item_id": item_id, "organization_id": org_id},
        {"_id": 0}
    ).to_list(100)
    item["stock_locations"] = stock_locations
    item["total_stock"] = sum(s.get("stock", 0) for s in stock_locations)
    
    # Get adjustments history
    adjustments = await db.item_adjustments.find(
        {"item_id": item_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("date", -1).limit(20).to_list(20)
    item["adjustments"] = adjustments
    
    # Get custom prices
    prices = await db.item_prices.find(
        {"item_id": item_id, "organization_id": org_id},
        {"_id": 0}
    ).to_list(100)
    item["price_list_rates"] = prices
    
    # Get transaction count
    invoice_count = await db.invoices.count_documents(
        {"line_items.item_id": item_id, "organization_id": org_id}
    )
    bill_count = await db.bills.count_documents(
        {"line_items.item_id": item_id, "organization_id": org_id}
    )
    item["transaction_count"] = invoice_count + bill_count
    item["is_used_in_transactions"] = item["transaction_count"] > 0
    
    return {"code": 0, "item": item}

@router.put("/{item_id}")
async def update_enhanced_item(item_id: str, item: ItemUpdate, request: Request):
    """Update item with partial data"""
    db = get_db()
    org_id = extract_org_id(request)
    
    existing = await db.items.find_one({"item_id": item_id, "organization_id": org_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if type change is allowed
    if item.item_type and existing.get("item_type") != item.item_type:
        invoice_count = await db.invoices.count_documents({"line_items.item_id": item_id, "organization_id": org_id})
        bill_count = await db.bills.count_documents({"line_items.item_id": item_id, "organization_id": org_id})
        if invoice_count > 0 or bill_count > 0:
            raise HTTPException(status_code=400, detail="Cannot change item type when used in transactions")
    
    # Build update dict with only provided fields
    update_data = {k: v for k, v in item.dict().items() if v is not None}
    
    if update_data:
        update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
        # Update rate field if sales_rate changed
        if "sales_rate" in update_data:
            update_data["rate"] = update_data["sales_rate"]
        # Update hsn_or_sac if either changed
        if "hsn_code" in update_data or "sac_code" in update_data:
            update_data["hsn_or_sac"] = update_data.get("hsn_code", existing.get("hsn_code", "")) or update_data.get("sac_code", existing.get("sac_code", ""))
        
        await db.items.update_one({"item_id": item_id, "organization_id": org_id}, {"$set": update_data})
    
    return {"code": 0, "message": "Item updated successfully"}

@router.post("/{item_id}/activate")
async def activate_item(item_id: str, request: Request):
    """Activate item"""
    db = get_db()
    org_id = extract_org_id(request)
    result = await db.items.update_one(
        {"item_id": item_id, "organization_id": org_id},
        {"$set": {"is_active": True, "status": "active", "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 0, "message": "Item activated"}

@router.post("/{item_id}/deactivate")
async def deactivate_item(item_id: str, request: Request):
    """Deactivate item"""
    db = get_db()
    org_id = extract_org_id(request)
    result = await db.items.update_one(
        {"item_id": item_id, "organization_id": org_id},
        {"$set": {"is_active": False, "status": "inactive", "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 0, "message": "Item deactivated"}

@router.delete("/{item_id}")
async def delete_enhanced_item(item_id: str, request: Request):
    """Delete item (only if not used in transactions)"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Check usage
    invoice_count = await db.invoices.count_documents({"line_items.item_id": item_id, "organization_id": org_id})
    bill_count = await db.bills.count_documents({"line_items.item_id": item_id, "organization_id": org_id})
    
    if invoice_count > 0 or bill_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete item used in {invoice_count} invoices and {bill_count} bills. Mark as inactive instead."
        )
    
    # Delete stock locations
    await db.item_stock_locations.delete_many({"item_id": item_id, "organization_id": org_id})
    
    # Delete prices
    await db.item_prices.delete_many({"item_id": item_id, "organization_id": org_id})
    
    # Delete item
    result = await db.items.delete_one({"item_id": item_id, "organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"code": 0, "message": "Item deleted successfully"}


# ============== ITEM-SPECIFIC STOCK LOCATIONS ==============

@router.get("/{item_id}/stock-locations")
async def get_item_stock_locations(item_id: str, request: Request):
    """Get stock locations for an item"""
    db = get_db()
    org_id = extract_org_id(request)
    locations = await db.item_stock_locations.find(
        {"item_id": item_id, "organization_id": org_id},
        {"_id": 0}
    ).to_list(100)
    
    total_stock = sum(loc.get("stock", 0) for loc in locations)
    
    return {"code": 0, "stock_locations": locations, "total_stock": total_stock}



# ============== ADMIN DATA INTEGRITY ==============

@router.post("/admin/fix-negative-stock")
async def fix_negative_stock_items(request: Request):
    """Fix items with negative stock by setting stock_on_hand to 0"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Find all items with negative stock
    negative_items = await db.items.find(
        {"stock_on_hand": {"$lt": 0}, "organization_id": org_id},
        {"_id": 0, "item_id": 1, "name": 1, "stock_on_hand": 1}
    ).to_list(1000)
    
    fixed_count = 0
    fixed_items = []
    
    for item in negative_items:
        old_stock = item.get("stock_on_hand", 0)
        await db.items.update_one(
            {"item_id": item["item_id"], "organization_id": org_id},
            {"$set": {
                "stock_on_hand": 0,
                "quantity": 0,
                "total_stock": 0,
                "updated_time": datetime.now(timezone.utc).isoformat()
            }}
        )
        fixed_items.append({
            "item_id": item["item_id"],
            "name": item["name"],
            "old_stock": old_stock,
            "new_stock": 0
        })
        fixed_count += 1
    
    return {
        "code": 0,
        "message": f"Fixed {fixed_count} items with negative stock",
        "fixed_count": fixed_count,
        "fixed_items": fixed_items
    }


@router.get("/admin/stock-integrity-report")
async def get_stock_integrity_report(request: Request):
    """Get report of stock integrity issues"""
    db = get_db()
    org_id = extract_org_id(request)
    
    # Negative stock items
    negative_items = await db.items.find(
        {"stock_on_hand": {"$lt": 0}, "organization_id": org_id},
        {"_id": 0, "item_id": 1, "name": 1, "sku": 1, "stock_on_hand": 1}
    ).to_list(1000)
    
    # Items with mismatched quantity/stock_on_hand
    pipeline = [
        {"$match": {
            "organization_id": org_id,
            "$expr": {
                "$and": [
                    {"$ne": ["$quantity", "$stock_on_hand"]},
                    {"$ne": [{"$ifNull": ["$quantity", 0]}, {"$ifNull": ["$stock_on_hand", 0]}]}
                ]
            }
        }},
        {"$project": {
            "_id": 0,
            "item_id": 1,
            "name": 1,
            "quantity": 1,
            "stock_on_hand": 1
        }},
        {"$limit": 100}
    ]
    mismatched = await db.items.aggregate(pipeline).to_list(100)
    
    return {
        "code": 0,
        "negative_stock_items": negative_items,
        "negative_count": len(negative_items),
        "mismatched_quantity_items": mismatched,
        "mismatched_count": len(mismatched)
    }

