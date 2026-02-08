"""
Script to update marketplace products and vehicles with high-quality stock images
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'battwheels')

# Image mappings for products (spares)
PRODUCT_IMAGES = {
    # Batteries
    "nmc-battery-72v-40ah": [
        "https://images.unsplash.com/photo-1676337167629-d896b3ed5724?w=800&q=80",  # Battery close-up
        "https://images.unsplash.com/photo-1600428235269-c326df6361fe?w=800&q=80"   # Battery pack
    ],
    "lfp-battery-48v-30ah": [
        "https://images.unsplash.com/photo-1600428235269-c326df6361fe?w=800&q=80",
        "https://images.unsplash.com/photo-1676337167629-d896b3ed5724?w=800&q=80"
    ],
    "refurbished-battery-48v-20ah": [
        "https://images.unsplash.com/photo-1600428235269-c326df6361fe?w=800&q=80"
    ],
    
    # Motors and Controllers
    "hub-motor-1500w-e-rickshaw": [
        "https://images.unsplash.com/photo-1700705581186-345f5e0c6ec4?w=800&q=80",  # Hub motor
        "https://images.unsplash.com/photo-1700705581242-71b4bdb23af8?w=800&q=80"
    ],
    "bldc-motor-controller-60v-45a-3w": [
        "https://images.unsplash.com/photo-1634452015397-ad0686a2ae2d?w=800&q=80",  # Circuit board
        "https://images.unsplash.com/photo-1587569087747-addba755bda6?w=800&q=80"
    ],
    
    # Diagnostic Tools
    "ev-diagnostic-scanner-pro": [
        "https://images.unsplash.com/photo-1653163048173-4305f65cf3f3?w=800&q=80",  # BMW engine
        "https://images.unsplash.com/photo-1564912139097-6e35a037c77f?w=800&q=80"   # Dashboard
    ],
    
    # Throttle and 2W Parts
    "universal-ev-throttle-assembly": [
        "https://images.unsplash.com/photo-1695560068569-e3282234cfdb?w=800&q=80",  # Handlebar close-up
        "https://images.unsplash.com/photo-1675247911627-0fb610250598?w=800&q=80"
    ],
}

# Image mappings for vehicles
VEHICLE_IMAGES = {
    # 2W Electric Scooters
    "ather-450x-gen3": [
        "https://images.unsplash.com/photo-1583322319396-08178ea4f8b3?w=800&q=80",  # Modern scooter
    ],
    "ola-s1-pro": [
        "https://images.unsplash.com/photo-1583322319396-08178ea4f8b3?w=800&q=80",
    ],
    "tvs-iqube-electric": [
        "https://images.unsplash.com/photo-1583322319396-08178ea4f8b3?w=800&q=80",
    ],
    "bajaj-chetak-electric": [
        "https://images.unsplash.com/photo-1583322319396-08178ea4f8b3?w=800&q=80",
    ],
    "ather-450-refurbished": [
        "https://images.unsplash.com/photo-1737636255616-2b99e1ef0edf?w=800&q=80",
    ],
    "ola-s1-refurbished": [
        "https://images.unsplash.com/photo-1737636255616-2b99e1ef0edf?w=800&q=80",
    ],
    
    # 3W Auto Rickshaws
    "mahindra-treo-electric": [
        "https://images.unsplash.com/photo-1761126088610-4277d86b6fb0?w=800&q=80",  # Auto rickshaw
    ],
    "piaggio-ape-e-city": [
        "https://images.unsplash.com/photo-1622877725017-db06daed68c9?w=800&q=80",
    ],
    "mahindra-treo-refurbished": [
        "https://images.unsplash.com/photo-1702440976396-5d8ede3aaf8b?w=800&q=80",
    ],
    
    # 4W Electric Cars
    "tata-nexon-ev-max": [
        "https://images.unsplash.com/photo-1615051050993-9502ba54aeff?w=800&q=80",  # Black SUV
    ],
    "mahindra-xuv400-electric": [
        "https://images.unsplash.com/photo-1767949374180-e5895daa1990?w=800&q=80",  # White SUV
    ],
    "mg-zs-ev": [
        "https://images.unsplash.com/photo-1767949374145-b450829c5abb?w=800&q=80",  # White car rural
    ],
    "tata-nexon-ev-refurbished": [
        "https://images.unsplash.com/photo-1615051050993-9502ba54aeff?w=800&q=80",
    ],
}

async def update_images():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Update product images
    print("Updating product images...")
    for slug, images in PRODUCT_IMAGES.items():
        result = await db.marketplace_products.update_one(
            {"slug": slug},
            {"$set": {"images": images}}
        )
        if result.modified_count > 0:
            print(f"  ✓ Updated {slug}")
        else:
            print(f"  - No match for {slug}")
    
    # Update vehicle images
    print("\nUpdating vehicle images...")
    for slug, images in VEHICLE_IMAGES.items():
        result = await db.marketplace_vehicles.update_one(
            {"slug": slug},
            {"$set": {"images": images}}
        )
        if result.modified_count > 0:
            print(f"  ✓ Updated {slug}")
        else:
            print(f"  - No match for {slug}")
    
    # Also update products collection for vehicles (since they might be there too)
    print("\nUpdating vehicles in products collection...")
    for slug, images in VEHICLE_IMAGES.items():
        result = await db.marketplace_products.update_one(
            {"slug": slug},
            {"$set": {"images": images}}
        )
        if result.modified_count > 0:
            print(f"  ✓ Updated {slug} in products")
    
    print("\n✅ Image update complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(update_images())
