"""
Stock Seeding Utility
Seeds test data for stock and inventory testing

Features:
- Create test warehouses
- Create test items with stock
- Seed stock levels across warehouses
- Create test stock transfers
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
import uuid
import random
import logging

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/seed", tags=["Data Seeding"])

# Environment gate: all seed endpoints check this
_SEED_ALLOWED = os.environ.get("ENVIRONMENT", "development") != "production"

# Sample data
WAREHOUSE_NAMES = [
    ("Main Warehouse", "Mumbai"),
    ("Central Hub", "Delhi"),
    ("East Zone", "Kolkata"),
    ("South Hub", "Chennai"),
    ("West Storage", "Pune"),
]

ITEM_CATEGORIES = ["Battery", "Motor", "Controller", "Charger", "Harness", "Sensor", "Display", "Frame", "Wheel", "Accessory"]

ITEM_TEMPLATES = [
    {"prefix": "BAT", "name": "12V {size}Ah Battery", "sizes": [7, 12, 20, 35, 50], "base_price": 2000},
    {"prefix": "MTR", "name": "{power}W BLDC Motor", "power": [250, 350, 500, 750, 1000], "base_price": 3500},
    {"prefix": "CTL", "name": "{type} Controller", "type": ["Basic", "Advanced", "Smart", "Pro"], "base_price": 1500},
    {"prefix": "CHG", "name": "{amp}A Charger", "amp": [3, 5, 10, 15], "base_price": 800},
    {"prefix": "HRN", "name": "{vehicle} Wiring Harness", "vehicle": ["2W", "3W", "E-Rickshaw", "E-Car"], "base_price": 1200},
    {"prefix": "SNS", "name": "{type} Sensor", "type": ["Speed", "Temperature", "Current", "Voltage", "Hall"], "base_price": 250},
]


@router.post("/warehouses")
async def seed_warehouses(count: int = 5, organization_id: Optional[str] = None):
    """Seed test warehouses"""
    if not _SEED_ALLOWED:
        raise HTTPException(status_code=403, detail="Seed endpoints disabled in production")
    now = datetime.now(timezone.utc)
    created = []
    
    for i, (name, location) in enumerate(WAREHOUSE_NAMES[:count]):
        warehouse_id = f"wh_{uuid.uuid4().hex[:12]}"
        
        warehouse_doc = {
            "warehouse_id": warehouse_id,
            "name": name,
            "code": f"WH{str(i + 1).zfill(3)}",
            "location": location,
            "address": f"{location}, India",
            "is_primary": i == 0,
            "is_active": True,
            "organization_id": organization_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        await db.warehouses.update_one(
            {"name": name, "organization_id": organization_id},
            {"$setOnInsert": warehouse_doc},
            upsert=True
        )
        created.append(warehouse_doc)
    
    return {
        "code": 0,
        "message": f"Seeded {len(created)} warehouses",
        "warehouses": created
    }


@router.post("/items")
async def seed_items(count: int = 50, organization_id: Optional[str] = None):
    """Seed test inventory items"""
    now = datetime.now(timezone.utc)
    created = []
    
    for i in range(count):
        template = random.choice(ITEM_TEMPLATES)
        item_id = f"itm_{uuid.uuid4().hex[:12]}"
        
        # Generate variation
        if "sizes" in template:
            size = random.choice(template["sizes"])
            name = template["name"].format(size=size)
            sku = f"{template['prefix']}-{size}AH-{str(i).zfill(4)}"
        elif "power" in template:
            power = random.choice(template["power"])
            name = template["name"].format(power=power)
            sku = f"{template['prefix']}-{power}W-{str(i).zfill(4)}"
        elif "type" in template:
            item_type = random.choice(template["type"])
            name = template["name"].format(type=item_type)
            sku = f"{template['prefix']}-{item_type[:3].upper()}-{str(i).zfill(4)}"
        elif "amp" in template:
            amp = random.choice(template["amp"])
            name = template["name"].format(amp=amp)
            sku = f"{template['prefix']}-{amp}A-{str(i).zfill(4)}"
        elif "vehicle" in template:
            vehicle = random.choice(template["vehicle"])
            name = template["name"].format(vehicle=vehicle)
            sku = f"{template['prefix']}-{vehicle.replace('-', '')}-{str(i).zfill(4)}"
        else:
            name = f"Test Item {i + 1}"
            sku = f"TST-{str(i).zfill(6)}"
        
        price = template["base_price"] * random.uniform(0.8, 1.5)
        
        item_doc = {
            "item_id": item_id,
            "name": name,
            "sku": sku,
            "item_type": "inventory",
            "unit": "pcs",
            "rate": round(price, 2),
            "selling_price": round(price, 2),
            "purchase_price": round(price * 0.7, 2),
            "tax_percentage": 18,
            "hsn_code": f"8507{random.randint(10, 99)}",
            "category": random.choice(ITEM_CATEGORIES),
            "is_active": True,
            "track_inventory": True,
            "reorder_level": random.randint(5, 20),
            "organization_id": organization_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        await db.items.update_one(
            {"sku": sku, "organization_id": organization_id},
            {"$setOnInsert": item_doc},
            upsert=True
        )
        created.append(item_doc)
    
    return {
        "code": 0,
        "message": f"Seeded {len(created)} items",
        "items": created[:10]  # Return first 10
    }


@router.post("/stock")
async def seed_stock_levels(
    items_per_warehouse: int = 30,
    organization_id: Optional[str] = None
):
    """Seed stock levels across warehouses"""
    now = datetime.now(timezone.utc)
    
    # Get warehouses
    warehouses = await db.warehouses.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(20)
    
    if not warehouses:
        raise HTTPException(status_code=400, detail="No warehouses found. Seed warehouses first.")
    
    # Get items
    items = await db.items.find(
        {"track_inventory": True, "is_active": True},
        {"_id": 0}
    ).to_list(200)
    
    if not items:
        raise HTTPException(status_code=400, detail="No items found. Seed items first.")
    
    stock_created = 0
    
    for warehouse in warehouses:
        # Select random items for this warehouse
        selected_items = random.sample(items, min(items_per_warehouse, len(items)))
        
        for item in selected_items:
            stock_id = f"stk_{uuid.uuid4().hex[:12]}"
            quantity = random.randint(10, 200)
            
            stock_doc = {
                "stock_id": stock_id,
                "item_id": item["item_id"],
                "item_name": item["name"],
                "sku": item.get("sku"),
                "warehouse_id": warehouse["warehouse_id"],
                "warehouse_name": warehouse["name"],
                "quantity": quantity,
                "reserved_quantity": 0,
                "available_quantity": quantity,
                "reorder_level": item.get("reorder_level", 10),
                "unit_cost": item.get("purchase_price", 0),
                "organization_id": organization_id,
                "last_updated": now.isoformat(),
                "created_at": now.isoformat(),
            }
            
            await db.item_stock.update_one(
                {"item_id": item["item_id"], "warehouse_id": warehouse["warehouse_id"]},
                {"$set": stock_doc},
                upsert=True
            )
            stock_created += 1
    
    return {
        "code": 0,
        "message": f"Seeded {stock_created} stock records across {len(warehouses)} warehouses",
        "warehouses": len(warehouses),
        "stock_records": stock_created
    }


@router.post("/transfers")
async def seed_stock_transfers(
    count: int = 10,
    organization_id: Optional[str] = None
):
    """Seed sample stock transfer orders"""
    now = datetime.now(timezone.utc)
    
    # Get warehouses
    warehouses = await db.warehouses.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(20)
    
    if len(warehouses) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 warehouses for transfers")
    
    # Get items with stock
    stock_items = await db.item_stock.find(
        {"quantity": {"$gt": 5}},
        {"_id": 0}
    ).to_list(100)
    
    if not stock_items:
        raise HTTPException(status_code=400, detail="No stock items found. Seed stock first.")
    
    transfers_created = []
    statuses = ["draft", "in_transit", "received"]
    
    for i in range(count):
        transfer_id = f"sto_{uuid.uuid4().hex[:12]}"
        
        # Pick random source and destination
        source = random.choice(warehouses)
        dest = random.choice([w for w in warehouses if w["warehouse_id"] != source["warehouse_id"]])
        
        # Pick random items from source warehouse
        source_stock = [s for s in stock_items if s["warehouse_id"] == source["warehouse_id"]]
        if not source_stock:
            continue
            
        selected_items = random.sample(source_stock, min(3, len(source_stock)))
        
        line_items = []
        for stock in selected_items:
            qty = random.randint(1, min(5, stock["quantity"]))
            line_items.append({
                "line_id": f"stl_{uuid.uuid4().hex[:8]}",
                "item_id": stock["item_id"],
                "item_name": stock["item_name"],
                "sku": stock.get("sku"),
                "quantity": qty,
                "source_stock": stock["quantity"],
                "unit": "pcs",
                "status": "pending"
            })
        
        if not line_items:
            continue
        
        status = random.choice(statuses)
        transfer_date = (now - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        
        transfer_doc = {
            "transfer_id": transfer_id,
            "transfer_number": f"STO-{str(i + 1).zfill(5)}",
            "source_warehouse_id": source["warehouse_id"],
            "source_warehouse_name": source["name"],
            "destination_warehouse_id": dest["warehouse_id"],
            "destination_warehouse_name": dest["name"],
            "transfer_date": transfer_date,
            "expected_arrival_date": (datetime.strptime(transfer_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d"),
            "line_items": line_items,
            "total_items": len(line_items),
            "total_quantity": sum(li["quantity"] for li in line_items),
            "status": status,
            "reason": random.choice(["Replenishment", "Consolidation", "Seasonal demand", "Customer order"]),
            "organization_id": organization_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        if status in ["in_transit", "received"]:
            transfer_doc["shipped_at"] = (datetime.strptime(transfer_date, "%Y-%m-%d") + timedelta(hours=2)).isoformat()
            transfer_doc["shipped_by"] = "system"
        
        if status == "received":
            transfer_doc["received_at"] = (datetime.strptime(transfer_date, "%Y-%m-%d") + timedelta(days=1)).isoformat()
            transfer_doc["received_by"] = "system"
        
        await db.stock_transfers.insert_one(transfer_doc)
        transfers_created.append(transfer_doc)
    
    return {
        "code": 0,
        "message": f"Seeded {len(transfers_created)} stock transfers",
        "transfers": [{"transfer_number": t["transfer_number"], "status": t["status"]} for t in transfers_created]
    }


@router.post("/bank-accounts")
async def seed_bank_accounts(count: int = 3, organization_id: Optional[str] = None):
    """Seed test bank accounts"""
    now = datetime.now(timezone.utc)
    
    bank_names = [
        ("HDFC Bank - Current Account", "HDFC Bank", "HDFC0001234", 150000),
        ("ICICI Bank - Business Account", "ICICI Bank", "ICIC0005678", 85000),
        ("SBI - Operations Account", "State Bank of India", "SBIN0009012", 220000),
        ("Axis Bank - Payroll", "Axis Bank", "UTIB0003456", 45000),
        ("Kotak - Savings", "Kotak Mahindra Bank", "KKBK0007890", 32000),
    ]
    
    created = []
    for i, (name, bank, ifsc, balance) in enumerate(bank_names[:count]):
        account_id = f"ba_{uuid.uuid4().hex[:12]}"
        
        account_doc = {
            "bank_account_id": account_id,
            "account_name": name,
            "account_type": "bank",
            "account_number": f"{''.join([str(random.randint(0, 9)) for _ in range(12)])}",
            "bank_name": bank,
            "ifsc_code": ifsc,
            "currency": "INR",
            "opening_balance": balance,
            "current_balance": balance + random.randint(-5000, 15000),
            "opening_balance_date": "2026-01-01",
            "is_primary": i == 0,
            "is_active": True,
            "organization_id": organization_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        await db.bank_accounts.update_one(
            {"account_name": name, "organization_id": organization_id},
            {"$setOnInsert": account_doc},
            upsert=True
        )
        created.append(account_doc)
    
    return {
        "code": 0,
        "message": f"Seeded {len(created)} bank accounts",
        "bank_accounts": created
    }


@router.post("/chart-of-accounts")
async def seed_chart_of_accounts(organization_id: Optional[str] = None):
    """Seed standard chart of accounts"""
    now = datetime.now(timezone.utc)
    
    standard_accounts = [
        # Assets
        {"code": "1000", "name": "Cash", "type": "asset", "sub_type": "current_asset"},
        {"code": "1010", "name": "Petty Cash", "type": "asset", "sub_type": "current_asset"},
        {"code": "1100", "name": "Accounts Receivable", "type": "asset", "sub_type": "current_asset"},
        {"code": "1200", "name": "Inventory", "type": "asset", "sub_type": "current_asset"},
        {"code": "1300", "name": "Prepaid Expenses", "type": "asset", "sub_type": "current_asset"},
        {"code": "1500", "name": "Equipment", "type": "asset", "sub_type": "fixed_asset"},
        {"code": "1510", "name": "Vehicles", "type": "asset", "sub_type": "fixed_asset"},
        {"code": "1520", "name": "Furniture", "type": "asset", "sub_type": "fixed_asset"},
        
        # Liabilities
        {"code": "2000", "name": "Accounts Payable", "type": "liability", "sub_type": "current_liability"},
        {"code": "2100", "name": "Accrued Expenses", "type": "liability", "sub_type": "current_liability"},
        {"code": "2200", "name": "GST Payable", "type": "liability", "sub_type": "current_liability"},
        {"code": "2300", "name": "TDS Payable", "type": "liability", "sub_type": "current_liability"},
        {"code": "2500", "name": "Long-term Loans", "type": "liability", "sub_type": "long_term_liability"},
        
        # Equity
        {"code": "3000", "name": "Owner's Capital", "type": "equity", "sub_type": "equity"},
        {"code": "3100", "name": "Retained Earnings", "type": "equity", "sub_type": "equity"},
        {"code": "3200", "name": "Owner's Drawings", "type": "equity", "sub_type": "equity"},
        
        # Income
        {"code": "4000", "name": "Sales Revenue", "type": "income", "sub_type": "operating_income"},
        {"code": "4100", "name": "Service Revenue", "type": "income", "sub_type": "operating_income"},
        {"code": "4200", "name": "Labour Income", "type": "income", "sub_type": "operating_income"},
        {"code": "4500", "name": "Interest Income", "type": "income", "sub_type": "other_income"},
        {"code": "4600", "name": "Other Income", "type": "income", "sub_type": "other_income"},
        
        # Expenses
        {"code": "5000", "name": "Cost of Goods Sold", "type": "expense", "sub_type": "direct_expense"},
        {"code": "5100", "name": "Purchase of Parts", "type": "expense", "sub_type": "direct_expense"},
        {"code": "5200", "name": "Labour Cost", "type": "expense", "sub_type": "direct_expense"},
        {"code": "6000", "name": "Salaries & Wages", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6100", "name": "Rent Expense", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6200", "name": "Utilities", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6300", "name": "Insurance", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6400", "name": "Office Supplies", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6500", "name": "Marketing & Advertising", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6600", "name": "Professional Fees", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6700", "name": "Bank Charges", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6800", "name": "Depreciation", "type": "expense", "sub_type": "operating_expense"},
        {"code": "6900", "name": "Miscellaneous Expense", "type": "expense", "sub_type": "operating_expense"},
    ]
    
    created = 0
    for acc in standard_accounts:
        account_id = f"coa_{uuid.uuid4().hex[:12]}"
        
        account_doc = {
            "account_id": account_id,
            "account_code": acc["code"],
            "account_name": acc["name"],
            "account_type": acc["type"],
            "account_sub_type": acc["sub_type"],
            "balance": 0,
            "is_active": True,
            "is_system": True,
            "organization_id": organization_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        result = await db.chart_of_accounts.update_one(
            {"account_code": acc["code"], "organization_id": organization_id},
            {"$setOnInsert": account_doc},
            upsert=True
        )
        if result.upserted_id:
            created += 1
    
    return {
        "code": 0,
        "message": f"Seeded {created} chart of accounts entries",
        "total_accounts": len(standard_accounts)
    }


@router.post("/all")
async def seed_all_data(organization_id: Optional[str] = None):
    """Seed all test data in one call"""
    results = {}
    
    try:
        # 1. Warehouses
        wh_result = await seed_warehouses(5, organization_id)
        results["warehouses"] = wh_result["message"]
        
        # 2. Items
        items_result = await seed_items(50, organization_id)
        results["items"] = items_result["message"]
        
        # 3. Stock
        stock_result = await seed_stock_levels(30, organization_id)
        results["stock"] = stock_result["message"]
        
        # 4. Transfers
        transfers_result = await seed_stock_transfers(10, organization_id)
        results["transfers"] = transfers_result["message"]
        
        # 5. Bank Accounts
        bank_result = await seed_bank_accounts(3, organization_id)
        results["bank_accounts"] = bank_result["message"]
        
        # 6. Chart of Accounts
        coa_result = await seed_chart_of_accounts(organization_id)
        results["chart_of_accounts"] = coa_result["message"]
        
        return {
            "code": 0,
            "message": "All test data seeded successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
