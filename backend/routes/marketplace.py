"""
Marketplace API Routes - Mock Battwheels OS Integration
These endpoints simulate the Battwheels OS backend for:
- Product catalog (SKU master data)
- Inventory availability
- Pricing (role-based)
- Order management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
import os

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])

# Get database reference
from server import db

# ============== MODELS ==============

class ProductBase(BaseModel):
    sku: str
    name: str
    slug: str
    category: str  # 2W Parts, 3W Parts, 4W Parts, Batteries, Diagnostic Tools, Refurbished
    subcategory: Optional[str] = None
    description: str
    short_description: Optional[str] = None
    specifications: Optional[dict] = {}
    compatibility: List[str] = []  # Vehicle models compatible
    vehicle_category: List[str] = []  # 2W, 3W, 4W
    brand: Optional[str] = None
    oem_aftermarket: str = "aftermarket"  # oem, aftermarket
    is_certified: bool = False
    warranty_months: int = 0
    weight_kg: Optional[float] = None
    dimensions: Optional[dict] = None
    images: List[str] = []
    tags: List[str] = []
    is_active: bool = True

class ProductCreate(ProductBase):
    base_price: float
    stock_quantity: int = 0

class ProductResponse(ProductBase):
    id: str
    base_price: float
    stock_quantity: int
    stock_status: str  # in_stock, low_stock, out_of_stock
    created_at: datetime
    updated_at: Optional[datetime] = None

class PricingTier(BaseModel):
    role: str  # public, fleet, technician
    discount_percent: float = 0
    final_price: float

class InventoryStatus(BaseModel):
    sku: str
    product_id: str
    stock_quantity: int
    stock_status: str
    nearest_locations: List[dict] = []
    estimated_delivery: Optional[str] = None

class CartItem(BaseModel):
    product_id: str
    quantity: int

class CartResponse(BaseModel):
    items: List[dict]
    subtotal: float
    discount: float
    total: float
    item_count: int

class OrderCreate(BaseModel):
    items: List[CartItem]
    shipping_address: dict
    payment_method: str  # razorpay, cod
    user_role: str = "public"
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    order_number: str
    status: str
    items: List[dict]
    subtotal: float
    discount: float
    shipping_charge: float
    total: float
    payment_method: str
    payment_status: str
    shipping_address: dict
    created_at: datetime
    estimated_delivery: Optional[str] = None

# ============== HELPER FUNCTIONS ==============

def get_stock_status(quantity: int) -> str:
    if quantity <= 0:
        return "out_of_stock"
    elif quantity <= 5:
        return "low_stock"
    return "in_stock"

def calculate_role_price(base_price: float, role: str) -> tuple:
    """Calculate price based on user role"""
    discounts = {
        "public": 0,
        "fleet": 15,  # 15% discount for fleet customers
        "technician": 20  # 20% discount for internal technicians
    }
    discount_percent = discounts.get(role, 0)
    discount_amount = base_price * (discount_percent / 100)
    final_price = base_price - discount_amount
    return discount_percent, round(final_price, 2)

def serialize_product(product: dict, role: str = "public") -> dict:
    """Serialize MongoDB product document"""
    discount_percent, final_price = calculate_role_price(product.get("base_price", 0), role)
    return {
        "id": str(product["_id"]),
        "sku": product.get("sku", ""),
        "name": product.get("name", ""),
        "slug": product.get("slug", ""),
        "category": product.get("category", ""),
        "subcategory": product.get("subcategory"),
        "description": product.get("description", ""),
        "short_description": product.get("short_description"),
        "specifications": product.get("specifications", {}),
        "compatibility": product.get("compatibility", []),
        "vehicle_category": product.get("vehicle_category", []),
        "brand": product.get("brand"),
        "oem_aftermarket": product.get("oem_aftermarket", "aftermarket"),
        "is_certified": product.get("is_certified", False),
        "warranty_months": product.get("warranty_months", 0),
        "weight_kg": product.get("weight_kg"),
        "dimensions": product.get("dimensions"),
        "images": product.get("images", []),
        "tags": product.get("tags", []),
        "is_active": product.get("is_active", True),
        "base_price": product.get("base_price", 0),
        "discount_percent": discount_percent,
        "final_price": final_price,
        "stock_quantity": product.get("stock_quantity", 0),
        "stock_status": get_stock_status(product.get("stock_quantity", 0)),
        "created_at": product.get("created_at", datetime.utcnow()),
        "updated_at": product.get("updated_at")
    }

# ============== PRODUCT ENDPOINTS ==============

@router.get("/products")
async def get_products(
    category: Optional[str] = None,
    vehicle_category: Optional[str] = None,
    oem_aftermarket: Optional[str] = None,
    is_certified: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    compatibility: Optional[str] = None,
    exclude_category: Optional[str] = None,
    brand: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 12,
    role: str = "public"
):
    """Get products with filters - simulates Battwheels OS product catalog"""
    query = {"is_active": True}
    
    if category:
        query["category"] = category
    if exclude_category:
        query["category"] = {"$ne": exclude_category}
    if vehicle_category:
        query["vehicle_category"] = vehicle_category
    if brand:
        query["brand"] = brand
    if oem_aftermarket:
        query["oem_aftermarket"] = oem_aftermarket
    if is_certified is not None:
        query["is_certified"] = is_certified
    if min_price is not None:
        query["base_price"] = {"$gte": min_price}
    if max_price is not None:
        if "base_price" in query:
            query["base_price"]["$lte"] = max_price
        else:
            query["base_price"] = {"$lte": max_price}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    if compatibility:
        query["compatibility"] = {"$regex": compatibility, "$options": "i"}
    
    sort_direction = -1 if sort_order == "desc" else 1
    skip = (page - 1) * limit
    
    total = await db.marketplace_products.count_documents(query)
    products_cursor = db.marketplace_products.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit)
    products = await products_cursor.to_list(length=limit)
    
    return {
        "products": [serialize_product(p, role) for p in products],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/products/slug/{slug}")
async def get_product_by_slug(slug: str, role: str = "public"):
    """Get product by slug - for product detail pages"""
    product = await db.marketplace_products.find_one({"slug": slug, "is_active": True})
    if not product:
        # Also check vehicles collection
        product = await db.marketplace_vehicles.find_one({"slug": slug, "is_active": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product, role)

@router.get("/products/{product_id}")
async def get_product(product_id: str, role: str = "public"):
    """Get single product details"""
    try:
        product = await db.marketplace_products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return serialize_product(product, role)

@router.get("/products/sku/{sku}")
async def get_product_by_sku(sku: str, role: str = "public"):
    """Get product by SKU - primary lookup method for Battwheels OS"""
    product = await db.marketplace_products.find_one({"sku": sku})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product, role)

# ============== INVENTORY ENDPOINTS ==============

# ============== ELECTRIC VEHICLES ENDPOINTS ==============

@router.get("/vehicles")
async def get_vehicles(
    vehicle_category: Optional[str] = None,
    brand: Optional[str] = None,
    oem_aftermarket: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 12,
    role: str = "public"
):
    """Get electric vehicles - New & Refurbished"""
    query = {"is_active": True, "category": "Electric Vehicles"}
    
    if vehicle_category:
        query["vehicle_category"] = vehicle_category
    if brand:
        query["brand"] = brand
    if oem_aftermarket:
        query["oem_aftermarket"] = oem_aftermarket
    if min_price is not None:
        query["base_price"] = {"$gte": min_price}
    if max_price is not None:
        if "base_price" in query:
            query["base_price"]["$lte"] = max_price
        else:
            query["base_price"] = {"$lte": max_price}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    sort_direction = -1 if sort_order == "desc" else 1
    skip = (page - 1) * limit
    
    total = await db.marketplace_products.count_documents(query)
    vehicles_cursor = db.marketplace_products.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit)
    vehicles = await vehicles_cursor.to_list(length=limit)
    
    return {
        "vehicles": [serialize_product(v, role) for v in vehicles],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/vehicles/oems")
async def get_vehicle_oems():
    """Get list of available OEMs/brands for vehicles"""
    pipeline = [
        {"$match": {"is_active": True, "category": "Electric Vehicles"}},
        {"$group": {"_id": "$brand"}},
        {"$sort": {"_id": 1}}
    ]
    oems = await db.marketplace_products.aggregate(pipeline).to_list(length=50)
    return {"oems": [oem["_id"] for oem in oems if oem["_id"]]}

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str, role: str = "public"):
    """Get single vehicle details"""
    try:
        vehicle = await db.marketplace_products.find_one({
            "_id": ObjectId(vehicle_id),
            "category": "Electric Vehicles"
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid vehicle ID")
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return serialize_product(vehicle, role)

# ============== INVENTORY ENDPOINTS ==============

@router.get("/inventory/{product_id}")
async def get_inventory(product_id: str):
    """Get real-time inventory status - simulates Battwheels OS inventory"""
    try:
        product = await db.marketplace_products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Simulate nearest location data
    nearest_locations = [
        {"location": "Delhi NCR - Okhla", "quantity": max(0, product.get("stock_quantity", 0) - 2), "distance_km": 5},
        {"location": "Delhi NCR - Dwarka", "quantity": max(0, product.get("stock_quantity", 0) - 5), "distance_km": 12},
        {"location": "Gurugram - Sector 37", "quantity": max(0, product.get("stock_quantity", 0) - 8), "distance_km": 18}
    ]
    
    return {
        "sku": product.get("sku"),
        "product_id": str(product["_id"]),
        "stock_quantity": product.get("stock_quantity", 0),
        "stock_status": get_stock_status(product.get("stock_quantity", 0)),
        "nearest_locations": [loc for loc in nearest_locations if loc["quantity"] > 0],
        "estimated_delivery": "2-4 business days" if product.get("stock_quantity", 0) > 0 else "Contact for availability"
    }

@router.post("/inventory/bulk-check")
async def bulk_inventory_check(product_ids: List[str]):
    """Check inventory for multiple products"""
    results = []
    for pid in product_ids:
        try:
            product = await db.marketplace_products.find_one({"_id": ObjectId(pid)})
            if product:
                results.append({
                    "product_id": pid,
                    "sku": product.get("sku"),
                    "stock_quantity": product.get("stock_quantity", 0),
                    "stock_status": get_stock_status(product.get("stock_quantity", 0))
                })
        except:
            continue
    return {"inventory": results}

# ============== PRICING ENDPOINTS ==============

@router.get("/pricing/{product_id}")
async def get_pricing(product_id: str, role: str = "public"):
    """Get role-based pricing - simulates Battwheels OS pricing engine"""
    try:
        product = await db.marketplace_products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    base_price = product.get("base_price", 0)
    tiers = []
    
    for r in ["public", "fleet", "technician"]:
        discount_percent, final_price = calculate_role_price(base_price, r)
        tiers.append({
            "role": r,
            "discount_percent": discount_percent,
            "final_price": final_price
        })
    
    current_discount, current_price = calculate_role_price(base_price, role)
    
    return {
        "product_id": str(product["_id"]),
        "sku": product.get("sku"),
        "base_price": base_price,
        "your_role": role,
        "your_discount_percent": current_discount,
        "your_price": current_price,
        "all_tiers": tiers
    }

# ============== CATEGORIES ENDPOINT ==============

@router.get("/categories")
async def get_categories():
    """Get all product categories with counts"""
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    categories = await db.marketplace_products.aggregate(pipeline).to_list(length=100)
    
    # Define category metadata
    category_meta = {
        "2W Parts": {"icon": "bike", "description": "Parts for 2-wheeler EVs"},
        "3W Parts": {"icon": "truck", "description": "Parts for 3-wheeler EVs"},
        "4W Parts": {"icon": "car", "description": "Parts for 4-wheeler EVs"},
        "Batteries": {"icon": "battery", "description": "EV batteries - new & refurbished"},
        "Diagnostic Tools": {"icon": "tool", "description": "Professional diagnostic equipment"},
        "Refurbished Components": {"icon": "recycle", "description": "Certified refurbished parts"}
    }
    
    return {
        "categories": [
            {
                "name": cat["_id"],
                "count": cat["count"],
                "slug": cat["_id"].lower().replace(" ", "-"),
                **category_meta.get(cat["_id"], {"icon": "box", "description": ""})
            }
            for cat in categories
        ]
    }

# ============== QUICK SEARCH (TECHNICIAN MODE) ==============

@router.get("/quick-search")
async def quick_search(
    q: str,
    vehicle_model: Optional[str] = None,
    failure_type: Optional[str] = None,
    limit: int = 10,
    role: str = "technician"
):
    """
    Quick search for technicians - optimized for field operations
    Searches by vehicle model compatibility and failure type keywords
    """
    query = {"is_active": True}
    
    search_conditions = [
        {"name": {"$regex": q, "$options": "i"}},
        {"sku": {"$regex": q, "$options": "i"}},
        {"tags": {"$regex": q, "$options": "i"}},
        {"compatibility": {"$regex": q, "$options": "i"}}
    ]
    
    if vehicle_model:
        search_conditions.append({"compatibility": {"$regex": vehicle_model, "$options": "i"}})
    
    if failure_type:
        search_conditions.append({"tags": {"$regex": failure_type, "$options": "i"}})
    
    query["$or"] = search_conditions
    
    products = await db.marketplace_products.find(query).limit(limit).to_list(length=limit)
    
    return {
        "results": [serialize_product(p, role) for p in products],
        "count": len(products),
        "search_query": q,
        "filters_applied": {
            "vehicle_model": vehicle_model,
            "failure_type": failure_type
        }
    }

# ============== ORDER ENDPOINTS ==============

@router.post("/orders")
async def create_order(order: OrderCreate):
    """Create order - triggers billing in Battwheels OS"""
    # Validate products and calculate totals
    items_detail = []
    subtotal = 0
    
    for item in order.items:
        try:
            product = await db.marketplace_products.find_one({"_id": ObjectId(item.product_id)})
        except:
            raise HTTPException(status_code=400, detail=f"Invalid product ID: {item.product_id}")
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        
        if product.get("stock_quantity", 0) < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {product.get('name')}. Available: {product.get('stock_quantity', 0)}"
            )
        
        _, unit_price = calculate_role_price(product.get("base_price", 0), order.user_role)
        item_total = unit_price * item.quantity
        
        items_detail.append({
            "product_id": item.product_id,
            "sku": product.get("sku"),
            "name": product.get("name"),
            "quantity": item.quantity,
            "unit_price": unit_price,
            "total": item_total
        })
        subtotal += item_total
    
    # Calculate totals
    discount_percent, _ = calculate_role_price(100, order.user_role)
    discount = subtotal * (discount_percent / 100) if discount_percent > 0 else 0
    shipping_charge = 0 if subtotal >= 2000 else 99  # Free shipping over ₹2000
    total = subtotal - discount + shipping_charge
    
    # Generate order number
    import random
    order_number = f"BW-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    # Create order document
    order_doc = {
        "order_number": order_number,
        "status": "pending",
        "items": items_detail,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping_charge": shipping_charge,
        "total": round(total, 2),
        "payment_method": order.payment_method,
        "payment_status": "pending",
        "user_role": order.user_role,
        "shipping_address": order.shipping_address,
        "notes": order.notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.marketplace_orders.insert_one(order_doc)
    
    # Deduct inventory (simulating Battwheels OS stock management)
    for item in order.items:
        await db.marketplace_products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"stock_quantity": -item.quantity}}
        )
    
    return {
        "id": str(result.inserted_id),
        "order_number": order_number,
        "status": "pending",
        "items": items_detail,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping_charge": shipping_charge,
        "total": round(total, 2),
        "payment_method": order.payment_method,
        "payment_status": "pending",
        "shipping_address": order.shipping_address,
        "created_at": order_doc["created_at"],
        "estimated_delivery": "3-5 business days",
        "message": "Order created successfully. Proceed to payment."
    }

@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order status"""
    try:
        order = await db.marketplace_orders.find_one({"_id": ObjectId(order_id)})
    except:
        # Try by order number
        order = await db.marketplace_orders.find_one({"order_number": order_id})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": str(order["_id"]),
        "order_number": order.get("order_number"),
        "status": order.get("status"),
        "items": order.get("items", []),
        "subtotal": order.get("subtotal"),
        "discount": order.get("discount"),
        "shipping_charge": order.get("shipping_charge"),
        "total": order.get("total"),
        "payment_method": order.get("payment_method"),
        "payment_status": order.get("payment_status"),
        "shipping_address": order.get("shipping_address"),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at")
    }

@router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    """Update order status - admin/internal use"""
    valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    try:
        result = await db.marketplace_orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
    except:
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order status updated", "status": status}
