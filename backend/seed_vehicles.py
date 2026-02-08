"""
Seed script for Electric Vehicles
New & Certified Refurbished EVs from top OEMs
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Electric Vehicles Catalog
VEHICLES = [
    # ============== 2W - NEW ==============
    {
        "sku": "BW-EV-2W-ATH-450X",
        "name": "Ather 450X Gen 3",
        "slug": "ather-450x-gen3",
        "category": "Electric Vehicles",
        "subcategory": "2W New",
        "description": "India's most powerful electric scooter with TrueRange™ technology. Features 7-inch touchscreen dashboard, Google Maps navigation, and connected vehicle features. Top speed of 90 kmph with sporty acceleration.",
        "short_description": "Premium smart electric scooter with connected features",
        "specifications": {
            "range": "146 km (Eco)",
            "top_speed": "90 kmph",
            "battery": "3.7 kWh",
            "motor": "6.4 kW PMSM",
            "charging_time": "5.45 hrs (0-80%)",
            "weight": "108 kg"
        },
        "compatibility": [],
        "vehicle_category": ["2W"],
        "brand": "Ather",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/ather-450x.jpg"],
        "tags": ["ather", "electric scooter", "smart", "connected", "premium"],
        "base_price": 149900,
        "stock_quantity": 5
    },
    {
        "sku": "BW-EV-2W-OLA-S1PRO",
        "name": "Ola S1 Pro",
        "slug": "ola-s1-pro",
        "category": "Electric Vehicles",
        "subcategory": "2W New",
        "description": "Ola's flagship electric scooter with industry-leading 181 km range. Features MoveOS with voice assistant, cruise control, and moods. Hyperdrive motor delivers 8.5 kW peak power.",
        "short_description": "High-range electric scooter with MoveOS",
        "specifications": {
            "range": "181 km (Eco)",
            "top_speed": "116 kmph",
            "battery": "4 kWh",
            "motor": "8.5 kW peak",
            "charging_time": "6.5 hrs (0-100%)",
            "weight": "125 kg"
        },
        "compatibility": [],
        "vehicle_category": ["2W"],
        "brand": "Ola",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/ola-s1-pro.jpg"],
        "tags": ["ola", "electric scooter", "high range", "moveos"],
        "base_price": 139999,
        "stock_quantity": 8
    },
    {
        "sku": "BW-EV-2W-TVS-IQUBE",
        "name": "TVS iQube Electric",
        "slug": "tvs-iqube-electric",
        "category": "Electric Vehicles",
        "subcategory": "2W New",
        "description": "TVS's smart connected electric scooter with SmartXconnect technology. Features navigation, geo-fencing, and remote diagnostics. Reliable performance from India's trusted brand.",
        "short_description": "Connected electric scooter from TVS",
        "specifications": {
            "range": "100 km",
            "top_speed": "78 kmph",
            "battery": "3.4 kWh",
            "motor": "4.4 kW",
            "charging_time": "5 hrs (0-80%)",
            "weight": "118 kg"
        },
        "compatibility": [],
        "vehicle_category": ["2W"],
        "brand": "TVS",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/tvs-iqube.jpg"],
        "tags": ["tvs", "electric scooter", "smart connect"],
        "base_price": 115990,
        "stock_quantity": 10
    },
    {
        "sku": "BW-EV-2W-BAJ-CHETAK",
        "name": "Bajaj Chetak Electric",
        "slug": "bajaj-chetak-electric",
        "category": "Electric Vehicles",
        "subcategory": "2W New",
        "description": "The iconic Chetak reborn as an electric. Premium metal body with retro design. IP67 rated battery and motor. Built for reliability and style.",
        "short_description": "Iconic design meets electric technology",
        "specifications": {
            "range": "108 km (Eco)",
            "top_speed": "73 kmph",
            "battery": "3 kWh",
            "motor": "4.08 kW",
            "charging_time": "5 hrs (0-100%)",
            "weight": "130 kg"
        },
        "compatibility": [],
        "vehicle_category": ["2W"],
        "brand": "Bajaj",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/bajaj-chetak.jpg"],
        "tags": ["bajaj", "chetak", "retro", "premium", "iconic"],
        "base_price": 148000,
        "stock_quantity": 4
    },
    
    # ============== 2W - REFURBISHED ==============
    {
        "sku": "BW-EV-2W-REF-ATH450",
        "name": "Ather 450 (Certified Refurbished)",
        "slug": "ather-450-refurbished",
        "category": "Electric Vehicles",
        "subcategory": "2W Refurbished",
        "description": "Certified refurbished Ather 450 with thorough inspection and reconditioning. Battery health certified at 85%+. All connected features working. 6-month Battwheels warranty.",
        "short_description": "Refurbished Ather 450 - Battery 85%+",
        "specifications": {
            "range": "85 km (estimated)",
            "top_speed": "80 kmph",
            "battery": "2.4 kWh",
            "motor": "5.4 kW",
            "condition": "Grade A Refurbished",
            "battery_health": "85%+"
        },
        "compatibility": [],
        "vehicle_category": ["2W"],
        "brand": "Ather",
        "oem_aftermarket": "refurbished",
        "is_certified": True,
        "warranty_months": 6,
        "original_price": 125000,
        "images": ["/marketplace/vehicles/ather-450-refurb.jpg"],
        "tags": ["ather", "refurbished", "certified", "budget"],
        "base_price": 75000,
        "stock_quantity": 3
    },
    {
        "sku": "BW-EV-2W-REF-OLAS1",
        "name": "Ola S1 (Certified Refurbished)",
        "slug": "ola-s1-refurbished",
        "category": "Electric Vehicles",
        "subcategory": "2W Refurbished",
        "description": "Certified refurbished Ola S1 with complete inspection. Battery reconditioned with 80%+ health. MoveOS updated to latest version. Perfect for daily commutes.",
        "short_description": "Refurbished Ola S1 - Full MoveOS features",
        "specifications": {
            "range": "100 km (estimated)",
            "top_speed": "90 kmph",
            "battery": "3 kWh",
            "motor": "8.5 kW peak",
            "condition": "Grade A Refurbished",
            "battery_health": "80%+"
        },
        "compatibility": [],
        "vehicle_category": ["2W"],
        "brand": "Ola",
        "oem_aftermarket": "refurbished",
        "is_certified": True,
        "warranty_months": 6,
        "original_price": 110000,
        "images": ["/marketplace/vehicles/ola-s1-refurb.jpg"],
        "tags": ["ola", "refurbished", "certified", "moveos"],
        "base_price": 68000,
        "stock_quantity": 2
    },
    
    # ============== 3W - NEW ==============
    {
        "sku": "BW-EV-3W-MAH-TREO",
        "name": "Mahindra Treo Electric Auto",
        "slug": "mahindra-treo-electric",
        "category": "Electric Vehicles",
        "subcategory": "3W New",
        "description": "India's bestselling electric auto rickshaw. Lithium-ion battery with 130 km range. Low running cost of ₹0.50/km. Perfect for last-mile mobility operators.",
        "short_description": "Bestselling electric auto rickshaw",
        "specifications": {
            "range": "130 km",
            "top_speed": "55 kmph",
            "battery": "7.37 kWh Li-ion",
            "motor": "8 kW",
            "payload": "415 kg",
            "seating": "Driver + 3 passengers"
        },
        "compatibility": [],
        "vehicle_category": ["3W"],
        "brand": "Mahindra",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/mahindra-treo.jpg"],
        "tags": ["mahindra", "auto rickshaw", "3 wheeler", "commercial"],
        "base_price": 329000,
        "stock_quantity": 6
    },
    {
        "sku": "BW-EV-3W-PIA-APE",
        "name": "Piaggio Ape E-City",
        "slug": "piaggio-ape-e-city",
        "category": "Electric Vehicles",
        "subcategory": "3W New",
        "description": "Piaggio's trusted electric cargo vehicle. Swappable battery system for zero downtime. 110 km range with 550 kg payload capacity. Built for commercial operations.",
        "short_description": "Electric cargo 3-wheeler with swappable battery",
        "specifications": {
            "range": "110 km",
            "top_speed": "45 kmph",
            "battery": "5.1 kWh (swappable)",
            "motor": "6 kW",
            "payload": "550 kg",
            "type": "Cargo"
        },
        "compatibility": [],
        "vehicle_category": ["3W"],
        "brand": "Piaggio",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 24,
        "images": ["/marketplace/vehicles/piaggio-ape.jpg"],
        "tags": ["piaggio", "cargo", "3 wheeler", "commercial", "swappable"],
        "base_price": 295000,
        "stock_quantity": 4
    },
    
    # ============== 3W - REFURBISHED ==============
    {
        "sku": "BW-EV-3W-REF-TREO",
        "name": "Mahindra Treo (Certified Refurbished)",
        "slug": "mahindra-treo-refurbished",
        "category": "Electric Vehicles",
        "subcategory": "3W Refurbished",
        "description": "Certified refurbished Mahindra Treo with replaced battery pack. Motor and controller verified. Ideal for fleet operators looking for budget options.",
        "short_description": "Refurbished electric auto with new battery",
        "specifications": {
            "range": "100 km (estimated)",
            "top_speed": "55 kmph",
            "battery": "New replacement battery",
            "motor": "8 kW (verified)",
            "condition": "Grade A Refurbished",
            "battery_health": "New"
        },
        "compatibility": [],
        "vehicle_category": ["3W"],
        "brand": "Mahindra",
        "oem_aftermarket": "refurbished",
        "is_certified": True,
        "warranty_months": 12,
        "original_price": 329000,
        "images": ["/marketplace/vehicles/treo-refurb.jpg"],
        "tags": ["mahindra", "refurbished", "3 wheeler", "fleet"],
        "base_price": 220000,
        "stock_quantity": 2
    },
    
    # ============== 4W - NEW ==============
    {
        "sku": "BW-EV-4W-TATA-NEXON",
        "name": "Tata Nexon EV Max",
        "slug": "tata-nexon-ev-max",
        "category": "Electric Vehicles",
        "subcategory": "4W New",
        "description": "India's bestselling electric SUV with 437 km ARAI certified range. Ziptron technology with fast charging. 5-star safety rating. Connected car features with iRA.",
        "short_description": "Bestselling electric SUV with 437 km range",
        "specifications": {
            "range": "437 km (ARAI)",
            "top_speed": "140 kmph",
            "battery": "40.5 kWh",
            "motor": "143 PS / 250 Nm",
            "charging_time": "56 min (10-80% DC)",
            "seating": "5"
        },
        "compatibility": [],
        "vehicle_category": ["4W"],
        "brand": "Tata",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/tata-nexon-ev.jpg"],
        "tags": ["tata", "suv", "nexon", "family", "ziptron"],
        "base_price": 1799000,
        "stock_quantity": 2
    },
    {
        "sku": "BW-EV-4W-MAH-XUV400",
        "name": "Mahindra XUV400 Electric",
        "slug": "mahindra-xuv400-electric",
        "category": "Electric Vehicles",
        "subcategory": "4W New",
        "description": "Mahindra's first electric SUV with 456 km range. Born Electric platform with fast charging. Premium interiors with AdrenoX connected technology.",
        "short_description": "Premium electric SUV from Mahindra",
        "specifications": {
            "range": "456 km (ARAI)",
            "top_speed": "150 kmph",
            "battery": "39.4 kWh",
            "motor": "150 PS / 310 Nm",
            "charging_time": "50 min (0-80% DC)",
            "seating": "5"
        },
        "compatibility": [],
        "vehicle_category": ["4W"],
        "brand": "Mahindra",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/mahindra-xuv400.jpg"],
        "tags": ["mahindra", "suv", "xuv", "premium", "born electric"],
        "base_price": 1599000,
        "stock_quantity": 2
    },
    {
        "sku": "BW-EV-4W-MG-ZS",
        "name": "MG ZS EV",
        "slug": "mg-zs-ev",
        "category": "Electric Vehicles",
        "subcategory": "4W New",
        "description": "Premium electric SUV with 461 km range. iSMART connected car technology. 176 PS motor with sporty driving experience. Global design with Indian features.",
        "short_description": "Global SUV with iSMART technology",
        "specifications": {
            "range": "461 km (ARAI)",
            "top_speed": "140 kmph",
            "battery": "50.3 kWh",
            "motor": "176 PS / 280 Nm",
            "charging_time": "60 min (0-80% DC)",
            "seating": "5"
        },
        "compatibility": [],
        "vehicle_category": ["4W"],
        "brand": "MG",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 36,
        "images": ["/marketplace/vehicles/mg-zs-ev.jpg"],
        "tags": ["mg", "suv", "ismart", "global", "premium"],
        "base_price": 2199000,
        "stock_quantity": 1
    },
    
    # ============== 4W - REFURBISHED ==============
    {
        "sku": "BW-EV-4W-REF-NEXON",
        "name": "Tata Nexon EV (Certified Refurbished)",
        "slug": "tata-nexon-ev-refurbished",
        "category": "Electric Vehicles",
        "subcategory": "4W Refurbished",
        "description": "Certified refurbished Nexon EV with comprehensive inspection. Battery health 85%+. All connected features working. 12-month Battwheels warranty with roadside assistance.",
        "short_description": "Refurbished Nexon EV - 85%+ battery health",
        "specifications": {
            "range": "280 km (estimated)",
            "top_speed": "120 kmph",
            "battery": "30.2 kWh",
            "motor": "129 PS / 245 Nm",
            "condition": "Grade A Refurbished",
            "battery_health": "85%+"
        },
        "compatibility": [],
        "vehicle_category": ["4W"],
        "brand": "Tata",
        "oem_aftermarket": "refurbished",
        "is_certified": True,
        "warranty_months": 12,
        "original_price": 1500000,
        "images": ["/marketplace/vehicles/nexon-refurb.jpg"],
        "tags": ["tata", "nexon", "refurbished", "certified", "suv"],
        "base_price": 950000,
        "stock_quantity": 1
    }
]

async def seed_vehicles():
    """Seed electric vehicles collection"""
    print("Starting electric vehicles seeding...")
    
    # Remove only Electric Vehicles category (keep spare parts)
    delete_result = await db.marketplace_products.delete_many({"category": "Electric Vehicles"})
    print(f"Cleared {delete_result.deleted_count} existing vehicles")
    
    # Add timestamps to all vehicles
    for vehicle in VEHICLES:
        vehicle["created_at"] = datetime.utcnow()
        vehicle["updated_at"] = datetime.utcnow()
        vehicle["is_active"] = True
    
    # Insert vehicles
    result = await db.marketplace_products.insert_many(VEHICLES)
    print(f"Inserted {len(result.inserted_ids)} vehicles")
    
    # Print summary
    pipeline = [
        {"$match": {"category": "Electric Vehicles"}},
        {"$group": {"_id": {"type": "$vehicle_category", "condition": "$oem_aftermarket"}, "count": {"$sum": 1}}}
    ]
    summary = await db.marketplace_products.aggregate(pipeline).to_list(length=20)
    
    print("\nVehicle Summary:")
    for item in summary:
        vtype = item["_id"]["type"][0] if item["_id"]["type"] else "Unknown"
        condition = "New" if item["_id"]["condition"] == "oem" else "Refurbished"
        print(f"  - {vtype} {condition}: {item['count']} vehicles")
    
    # Print OEMs
    oems = await db.marketplace_products.distinct("brand", {"category": "Electric Vehicles"})
    print(f"\nOEMs: {', '.join(oems)}")
    
    print("\n✅ Electric vehicles seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_vehicles())
