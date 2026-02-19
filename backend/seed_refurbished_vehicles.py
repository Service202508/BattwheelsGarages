"""
Seed script for Electric Vehicles Marketplace - Refurbished 2W and 3W only
Updates the marketplace with second-hand/refurbished vehicles as per requirement
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import random

MONGO_URL = 'mongodb://localhost:27017'
DB_NAME = 'test_database'

# Electric 2-Wheelers (Refurbished)
TWO_WHEELERS = [
    {"name": "Ola S1 Pro", "brand": "Ola Electric", "model": "S1 Pro", "type": "Scooter"},
    {"name": "Ola S1 Air", "brand": "Ola Electric", "model": "S1 Air", "type": "Scooter"},
    {"name": "Ather 450X", "brand": "Ather Energy", "model": "450X", "type": "Scooter"},
    {"name": "Ather 450S", "brand": "Ather Energy", "model": "450S", "type": "Scooter"},
    {"name": "TVS iQube", "brand": "TVS Motor", "model": "iQube", "type": "Scooter"},
    {"name": "Bajaj Chetak Electric", "brand": "Bajaj Auto", "model": "Chetak", "type": "Scooter"},
    {"name": "Hero Vida V1", "brand": "Hero MotoCorp", "model": "Vida V1", "type": "Scooter"},
    {"name": "Hero Optima", "brand": "Hero Electric", "model": "Optima", "type": "Scooter"},
    {"name": "Ampere Magnus EX", "brand": "Greaves Electric", "model": "Magnus EX", "type": "Scooter"},
    {"name": "Ampere Nexus", "brand": "Greaves Electric", "model": "Nexus", "type": "Scooter"},
    {"name": "Okinawa Praise Pro", "brand": "Okinawa", "model": "Praise Pro", "type": "Scooter"},
    {"name": "Okinawa iPraise+", "brand": "Okinawa", "model": "iPraise+", "type": "Scooter"},
    {"name": "Revolt RV400", "brand": "Revolt Motors", "model": "RV400", "type": "Motorcycle"},
    {"name": "Tork Kratos R", "brand": "Tork Motors", "model": "Kratos R", "type": "Motorcycle"},
    {"name": "Simple One", "brand": "Simple Energy", "model": "One", "type": "Scooter"},
    {"name": "Pure EV EPluto 7G", "brand": "PURE EV", "model": "EPluto 7G", "type": "Scooter"},
    {"name": "Oben Rorr", "brand": "Oben Electric", "model": "Rorr", "type": "Motorcycle"},
    {"name": "Ultraviolette F77", "brand": "Ultraviolette", "model": "F77", "type": "Motorcycle"},
    {"name": "Kinetic Green Zing", "brand": "Kinetic Green", "model": "Zing", "type": "Scooter"},
    {"name": "Joy e-Bike Mihos", "brand": "Wardwizard Joy e-Bike", "model": "Mihos", "type": "Scooter"},
]

# Electric 3-Wheelers (Refurbished) - Auto + Cargo/Loader
THREE_WHEELERS = [
    {"name": "Mahindra Treo", "brand": "Mahindra", "model": "Treo", "type": "Auto", "is_cargo": False},
    {"name": "Mahindra Treo Zor", "brand": "Mahindra", "model": "Treo Zor", "type": "Cargo", "is_cargo": True},
    {"name": "Mahindra e-Alfa Mini", "brand": "Mahindra", "model": "e-Alfa Mini", "type": "Auto", "is_cargo": False},
    {"name": "Bajaj RE E-TEC", "brand": "Bajaj Auto", "model": "RE E-TEC", "type": "Auto", "is_cargo": False},
    {"name": "Piaggio Ape E-City", "brand": "Piaggio", "model": "Ape E-City", "type": "Auto", "is_cargo": False},
    {"name": "Piaggio Ape E-Xtra", "brand": "Piaggio", "model": "Ape E-Xtra", "type": "Cargo", "is_cargo": True},
    {"name": "Euler HiLoad EV", "brand": "Euler Motors", "model": "HiLoad EV", "type": "Cargo", "is_cargo": True},
    {"name": "Euler Storm EV", "brand": "Euler Motors", "model": "Storm EV", "type": "Auto", "is_cargo": False},
    {"name": "Omega Seiki Rage+", "brand": "Omega Seiki", "model": "Rage+", "type": "Cargo", "is_cargo": True},
    {"name": "Omega Seiki Stream", "brand": "Omega Seiki", "model": "Stream", "type": "Auto", "is_cargo": False},
    {"name": "Kinetic Safar Jumbo", "brand": "Kinetic Green", "model": "Safar Jumbo", "type": "Cargo", "is_cargo": True},
    {"name": "Lohia Humsafar", "brand": "Lohia Auto", "model": "Humsafar", "type": "Auto", "is_cargo": False},
    {"name": "Lohia Narain", "brand": "Lohia Auto", "model": "Narain", "type": "Auto", "is_cargo": False},
    {"name": "Atul Elite Cargo", "brand": "Atul Auto", "model": "Elite Cargo", "type": "Cargo", "is_cargo": True},
    {"name": "YC Electric Yatri", "brand": "YC Electric", "model": "Yatri", "type": "Auto", "is_cargo": False},
    {"name": "Mini Metro E-Rickshaw", "brand": "Mini Metro", "model": "E-Rickshaw", "type": "E-Rickshaw", "is_cargo": False},
    {"name": "Saarthi DLX E-Rickshaw", "brand": "Saarthi", "model": "DLX", "type": "E-Rickshaw", "is_cargo": False},
    {"name": "Udaan E-Rickshaw", "brand": "Udaan", "model": "Standard", "type": "E-Rickshaw", "is_cargo": False},
    {"name": "TVS King EV Max", "brand": "TVS Motor", "model": "King EV Max", "type": "Auto", "is_cargo": False},
    {"name": "Montra Super Auto EV", "brand": "Montra Electric", "model": "Super Auto", "type": "Auto", "is_cargo": False},
]

# Brand colors for UI
BRAND_COLORS = {
    "Ola Electric": "#2ECC71",
    "Ather Energy": "#00A86B",
    "TVS Motor": "#1E90FF",
    "Bajaj Auto": "#FF6B00",
    "Hero MotoCorp": "#E31837",
    "Hero Electric": "#E31837",
    "Greaves Electric": "#4A90D9",
    "Okinawa": "#FF4500",
    "Revolt Motors": "#000000",
    "Tork Motors": "#FF0000",
    "Simple Energy": "#6B5B95",
    "PURE EV": "#32CD32",
    "Oben Electric": "#FF6347",
    "Ultraviolette": "#4B0082",
    "Kinetic Green": "#228B22",
    "Wardwizard Joy e-Bike": "#FFD700",
    "Mahindra": "#E31837",
    "Piaggio": "#00599C",
    "Euler Motors": "#FF8C00",
    "Omega Seiki": "#2F4F4F",
    "Lohia Auto": "#8B4513",
    "Atul Auto": "#006400",
    "YC Electric": "#4169E1",
    "Mini Metro": "#808080",
    "Saarthi": "#CD853F",
    "Udaan": "#20B2AA",
    "Montra Electric": "#9932CC",
}

# Stock images for vehicles (AI-generated from previous session)
SCOOTER_IMAGES = [
    "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/2cfbff61b57e21854174707d5ed2691103e2dc1d7440cadb391814217a7d1fa9.png",
    "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/89b0eb4308b646e697eb94de0f44f23cbaf7d1ec1156bfdb77c78a0e6d2d877f.png",
    "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/9975b063c8d484060705cf3bab886074e06dbc867fd740d3a7ef303e29ebee6f.png",
    "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/3291135fc06108e673aa1975e26d91630307ff04f45b4dff3176847a6b8ca2bd.png",
]

MOTORCYCLE_IMAGES = [
    "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800&q=80",
    "https://images.unsplash.com/photo-1558981285-6f0c94958bb6?w=800&q=80",
]

AUTO_IMAGES = [
    "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/878cb9a319ae190901568c029f05eb378dde05f120d5671af77a9a03808c44b8.png",
    "https://images.unsplash.com/photo-1761126088610-4277d86b6fb0?w=800&q=80",
    "https://images.unsplash.com/photo-1622877725017-db06daed68c9?w=800&q=80",
]

CARGO_IMAGES = [
    "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/75218e7369b765e13318d1d7261af95a47e26ff693207d45bd08e0b27547a4e4.png",
    "https://images.unsplash.com/photo-1702440976396-5d8ede3aaf8b?w=800&q=80",
]

def generate_slug(name):
    return name.lower().replace(" ", "-").replace("+", "plus").replace("(", "").replace(")", "")

def generate_sku(brand, model, category):
    prefix = "BW-REF"
    brand_code = brand[:3].upper()
    model_code = model.replace(" ", "")[:6].upper()
    cat_code = "2W" if category == "2W" else "3W"
    return f"{prefix}-{cat_code}-{brand_code}-{model_code}"

async def seed_vehicles():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Clear existing vehicles
    await db.marketplace_products.delete_many({"vehicle_category": {"$in": ["2W", "3W", "4W"]}})
    await db.marketplace_products.delete_many({"type": "vehicle"})
    print("Cleared existing vehicle data")
    
    vehicles_to_insert = []
    
    # Process 2-Wheelers
    print("\nProcessing 2-Wheelers...")
    for idx, vehicle in enumerate(TWO_WHEELERS):
        # Random pricing based on type
        if vehicle["type"] == "Motorcycle":
            base_price = random.randint(85000, 180000)
        else:
            base_price = random.randint(45000, 95000)
        
        # Determine image
        if vehicle["type"] == "Motorcycle":
            images = [random.choice(MOTORCYCLE_IMAGES)]
        else:
            images = [SCOOTER_IMAGES[idx % len(SCOOTER_IMAGES)]]
        
        doc = {
            "name": f"{vehicle['name']} (Certified Refurbished)",
            "slug": generate_slug(vehicle['name']) + "-refurbished",
            "sku": generate_sku(vehicle["brand"], vehicle["model"], "2W"),
            "brand": vehicle["brand"],
            "model": vehicle["model"],
            "category": "Electric Vehicles",
            "vehicle_category": "2W",
            "vehicle_type": vehicle["type"],
            "type": "vehicle",
            "condition": "refurbished",
            "price": base_price,
            "final_price": base_price,
            "stock_quantity": random.randint(1, 3),  # Minimal stock
            "stock_status": "low_stock",
            "is_certified": True,
            "is_active": True,
            "warranty_months": random.choice([6, 12]),
            "specifications": {
                "range_km": random.randint(80, 150),
                "battery_kwh": round(random.uniform(2.0, 4.0), 1),
                "top_speed_kmph": random.randint(70, 120),
                "charging_time_hrs": round(random.uniform(3, 6), 1),
            },
            "features": [
                "Certified by Battwheels",
                "Battery health checked",
                "Motor & controller tested",
                "New replacement battery (if needed)",
                "Service history available"
            ],
            "images": images,
            "brand_color": BRAND_COLORS.get(vehicle["brand"], "#12B76A"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        vehicles_to_insert.append(doc)
        print(f"  ✓ {vehicle['name']}")
    
    # Process 3-Wheelers
    print("\nProcessing 3-Wheelers...")
    for idx, vehicle in enumerate(THREE_WHEELERS):
        # Random pricing based on type
        if vehicle["is_cargo"]:
            base_price = random.randint(180000, 350000)
        elif vehicle["type"] == "E-Rickshaw":
            base_price = random.randint(95000, 150000)
        else:
            base_price = random.randint(200000, 400000)
        
        # Determine image
        if vehicle["is_cargo"]:
            images = [CARGO_IMAGES[idx % len(CARGO_IMAGES)]]
        else:
            images = [AUTO_IMAGES[idx % len(AUTO_IMAGES)]]
        
        subtype = "Cargo/Loader" if vehicle["is_cargo"] else ("E-Rickshaw" if vehicle["type"] == "E-Rickshaw" else "Passenger Auto")
        
        doc = {
            "name": f"{vehicle['name']} (Certified Refurbished)",
            "slug": generate_slug(vehicle['name']) + "-refurbished",
            "sku": generate_sku(vehicle["brand"], vehicle["model"], "3W"),
            "brand": vehicle["brand"],
            "model": vehicle["model"],
            "category": "Electric Vehicles",
            "vehicle_category": "3W",
            "vehicle_type": vehicle["type"],
            "vehicle_subtype": subtype,
            "is_cargo": vehicle["is_cargo"],
            "type": "vehicle",
            "condition": "refurbished",
            "price": base_price,
            "final_price": base_price,
            "stock_quantity": random.randint(1, 2),  # Minimal stock
            "stock_status": "low_stock",
            "is_certified": True,
            "is_active": True,
            "warranty_months": random.choice([6, 12, 18]),
            "specifications": {
                "range_km": random.randint(80, 120),
                "battery_kwh": round(random.uniform(4.0, 10.0), 1),
                "payload_kg": random.randint(300, 700) if vehicle["is_cargo"] else random.randint(3, 6),
                "charging_time_hrs": round(random.uniform(4, 8), 1),
            },
            "features": [
                "Certified by Battwheels",
                "Battery health verified",
                "Motor & controller tested",
                "Chassis inspection done",
                "Documentation complete"
            ],
            "images": images,
            "brand_color": BRAND_COLORS.get(vehicle["brand"], "#12B76A"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        vehicles_to_insert.append(doc)
        print(f"  ✓ {vehicle['name']}")
    
    # Insert all vehicles
    if vehicles_to_insert:
        result = await db.marketplace_products.insert_many(vehicles_to_insert)
        print(f"\n✅ Successfully inserted {len(result.inserted_ids)} vehicles")
        print(f"   - 2-Wheelers: {len(TWO_WHEELERS)}")
        print(f"   - 3-Wheelers: {len(THREE_WHEELERS)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_vehicles())
