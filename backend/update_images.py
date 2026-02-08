"""
Script to update marketplace products with high-quality stock images from Unsplash
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = 'mongodb://localhost:27017'
DB_NAME = 'test_database'

# Image mappings for ALL products
PRODUCT_IMAGES = {
    # 2W Parts
    "bldc-motor-controller-48v-25a": [
        "https://images.unsplash.com/photo-1634452015397-ad0686a2ae2d?w=800&q=80",  # Circuit board
        "https://images.unsplash.com/photo-1587569087747-addba755bda6?w=800&q=80"   # Electronics
    ],
    "universal-ev-throttle-assembly": [
        "https://images.unsplash.com/photo-1695560068569-e3282234cfdb?w=800&q=80",  # Handlebar close-up
        "https://images.unsplash.com/photo-1675247911627-0fb610250598?w=800&q=80"
    ],
    "lcd-display-speedometer-2w": [
        "https://images.unsplash.com/photo-1652510076706-636d4b641f37?w=800&q=80",  # Dashboard EQ display
    ],
    
    # 3W Parts
    "bldc-motor-controller-60v-45a-3w": [
        "https://images.unsplash.com/photo-1634452015397-ad0686a2ae2d?w=800&q=80",
        "https://images.unsplash.com/photo-1587569087747-addba755bda6?w=800&q=80"
    ],
    "hub-motor-1500w-e-rickshaw": [
        "https://images.unsplash.com/photo-1700705581186-345f5e0c6ec4?w=800&q=80",  # Hub motor
        "https://images.unsplash.com/photo-1700705581242-71b4bdb23af8?w=800&q=80"
    ],
    
    # 4W Parts
    "on-board-charger-3-3kw-4w": [
        "https://images.unsplash.com/photo-1732193889585-ed4747369d5a?w=800&q=80",  # EV charger
    ],
    "battery-management-system-96s": [
        "https://images.unsplash.com/photo-1634452015397-ad0686a2ae2d?w=800&q=80",
    ],
    
    # Batteries
    "lfp-battery-48v-30ah": [
        "https://images.unsplash.com/photo-1600428235269-c326df6361fe?w=800&q=80",  # Battery pack
        "https://images.unsplash.com/photo-1676337167629-d896b3ed5724?w=800&q=80"   # Battery close-up
    ],
    "nmc-battery-72v-40ah": [
        "https://images.unsplash.com/photo-1676337167629-d896b3ed5724?w=800&q=80",
        "https://images.unsplash.com/photo-1600428235269-c326df6361fe?w=800&q=80"
    ],
    "refurbished-battery-48v-20ah": [
        "https://images.unsplash.com/photo-1600428235269-c326df6361fe?w=800&q=80"
    ],
    
    # Diagnostic Tools
    "ev-diagnostic-scanner-pro": [
        "https://images.unsplash.com/photo-1653163048173-4305f65cf3f3?w=800&q=80",  # Engine close-up
    ],
    "bms-cell-tester-balancer": [
        "https://images.unsplash.com/photo-1634452015397-ad0686a2ae2d?w=800&q=80",
    ],
    "motor-analyzer-dyno-interface": [
        "https://images.unsplash.com/photo-1652510076706-636d4b641f37?w=800&q=80",  # Dashboard
    ],
    
    # Refurbished Components
    "refurbished-controller-ola-s1-pro": [
        "https://images.unsplash.com/photo-1634452015397-ad0686a2ae2d?w=800&q=80",
    ],
    "refurbished-hub-motor-ather-450": [
        "https://images.unsplash.com/photo-1700705581186-345f5e0c6ec4?w=800&q=80",
    ],
    
    # Electric Vehicles - 2W Scooters
    "ather-450x-gen3": [
        "https://images.unsplash.com/photo-1583322319396-08178ea4f8b3?w=800&q=80",  # Modern scooter
    ],
    "ola-s1-pro": [
        "https://images.unsplash.com/photo-1737636255623-42843f3ea30b?w=800&q=80",  # Electric scooter street
    ],
    "tvs-iqube-electric": [
        "https://images.unsplash.com/photo-1583322319396-08178ea4f8b3?w=800&q=80",
    ],
    "bajaj-chetak-electric": [
        "https://images.unsplash.com/photo-1583322319396-08178ea4f8b3?w=800&q=80",
    ],
    "ather-450-refurbished": [
        "https://images.unsplash.com/photo-1737636255616-2b99e1ef0edf?w=800&q=80",  # Scooter on sidewalk
    ],
    "ola-s1-refurbished": [
        "https://images.unsplash.com/photo-1737636255601-179dc7535116?w=800&q=80",
    ],
    
    # Electric Vehicles - 3W Auto Rickshaws
    "mahindra-treo-electric": [
        "https://images.unsplash.com/photo-1761126088610-4277d86b6fb0?w=800&q=80",  # Yellow auto rickshaw
    ],
    "piaggio-ape-e-city": [
        "https://images.unsplash.com/photo-1622877725017-db06daed68c9?w=800&q=80",  # Blue auto rickshaw
    ],
    "mahindra-treo-refurbished": [
        "https://images.unsplash.com/photo-1702440976396-5d8ede3aaf8b?w=800&q=80",  # Red three wheeler
    ],
    
    # Electric Vehicles - 4W Cars
    "tata-nexon-ev-max": [
        "https://images.unsplash.com/photo-1615051050993-9502ba54aeff?w=800&q=80",  # Black SUV
    ],
    "mahindra-xuv400-electric": [
        "https://images.unsplash.com/photo-1767949374180-e5895daa1990?w=800&q=80",  # White SUV driveway
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
    
    print("Updating product images in marketplace_products collection...")
    updated = 0
    not_found = 0
    
    for slug, images in PRODUCT_IMAGES.items():
        result = await db.marketplace_products.update_one(
            {"slug": slug},
            {"$set": {"images": images}}
        )
        if result.modified_count > 0:
            print(f"  ✓ {slug}")
            updated += 1
        else:
            # Check if exists but wasn't modified
            exists = await db.marketplace_products.find_one({"slug": slug})
            if exists:
                print(f"  ~ {slug} (already had same images)")
            else:
                print(f"  ✗ {slug} not found")
                not_found += 1
    
    print(f"\n✅ Updated {updated} products")
    if not_found > 0:
        print(f"⚠️  {not_found} products not found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_images())
