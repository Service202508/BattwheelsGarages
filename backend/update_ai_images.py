"""
Script to update marketplace products with AI-generated custom images
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = 'mongodb://localhost:27017'
DB_NAME = 'test_database'

# AI-Generated image mappings for products
AI_PRODUCT_IMAGES = {
    # 2W Electric Scooters
    "ola-s1-pro": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/2cfbff61b57e21854174707d5ed2691103e2dc1d7440cadb391814217a7d1fa9.png"
    ],
    "ather-450x-gen3": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/89b0eb4308b646e697eb94de0f44f23cbaf7d1ec1156bfdb77c78a0e6d2d877f.png"
    ],
    "tvs-iqube-electric": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/9975b063c8d484060705cf3bab886074e06dbc867fd740d3a7ef303e29ebee6f.png"
    ],
    "bajaj-chetak-electric": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/3291135fc06108e673aa1975e26d91630307ff04f45b4dff3176847a6b8ca2bd.png"
    ],
    # Refurbished scooters use same images
    "ather-450-refurbished": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/89b0eb4308b646e697eb94de0f44f23cbaf7d1ec1156bfdb77c78a0e6d2d877f.png"
    ],
    "ola-s1-refurbished": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/2cfbff61b57e21854174707d5ed2691103e2dc1d7440cadb391814217a7d1fa9.png"
    ],
    
    # 4W Electric Cars
    "tata-nexon-ev-max": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/7110229be325b41178dac23682f9abe45198bd1acb00c204f191fdc1175cc06b.png"
    ],
    "tata-nexon-ev-refurbished": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/7110229be325b41178dac23682f9abe45198bd1acb00c204f191fdc1175cc06b.png"
    ],
    "mahindra-xuv400-electric": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/101a436fa54371142b5bdbe88434a18b8e774aaa930f6c8120aec0ce5bb6b5a2.png"
    ],
    "mg-zs-ev": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/b465218c989bca8da719163604437a733875cc485601515214b523828da5aeaa.png"
    ],
    
    # 3W Auto Rickshaws
    "mahindra-treo-electric": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/878cb9a319ae190901568c029f05eb378dde05f120d5671af77a9a03808c44b8.png"
    ],
    "mahindra-treo-refurbished": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/878cb9a319ae190901568c029f05eb378dde05f120d5671af77a9a03808c44b8.png"
    ],
    "piaggio-ape-e-city": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/75218e7369b765e13318d1d7261af95a47e26ff693207d45bd08e0b27547a4e4.png"
    ],
    
    # Batteries
    "nmc-battery-72v-40ah": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/acee2d1e4426ba0f5b25a563d0323bcf045a28d4d98e1f9b7f8a8cf40e40aecf.png"
    ],
    "lfp-battery-48v-30ah": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/acee2d1e4426ba0f5b25a563d0323bcf045a28d4d98e1f9b7f8a8cf40e40aecf.png"
    ],
    "refurbished-battery-48v-20ah": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/acee2d1e4426ba0f5b25a563d0323bcf045a28d4d98e1f9b7f8a8cf40e40aecf.png"
    ],
    
    # Controllers
    "bldc-motor-controller-48v-25a": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/31c477d1d18c3776c6c4226eda54f1c0738796428cd2750f41df6aafed45889e.png"
    ],
    "bldc-motor-controller-60v-45a-3w": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/31c477d1d18c3776c6c4226eda54f1c0738796428cd2750f41df6aafed45889e.png"
    ],
    "refurbished-controller-ola-s1-pro": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/31c477d1d18c3776c6c4226eda54f1c0738796428cd2750f41df6aafed45889e.png"
    ],
    
    # Hub Motors
    "hub-motor-1500w-e-rickshaw": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/e29fbd7dcf5a6d72525824e4327ea982974aff9deea9ff02a3c899651d6cd287.png"
    ],
    "refurbished-hub-motor-ather-450": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/e29fbd7dcf5a6d72525824e4327ea982974aff9deea9ff02a3c899651d6cd287.png"
    ],
    
    # Diagnostic Tools
    "ev-diagnostic-scanner-pro": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/26eaaac87fcb5d0ac4acfac18f913bd0a069a735bf2ff064775505756f2815e3.png"
    ],
    "bms-cell-tester-balancer": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/26eaaac87fcb5d0ac4acfac18f913bd0a069a735bf2ff064775505756f2815e3.png"
    ],
    "motor-analyzer-dyno-interface": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/26eaaac87fcb5d0ac4acfac18f913bd0a069a735bf2ff064775505756f2815e3.png"
    ],
    
    # Other Parts
    "universal-ev-throttle-assembly": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/8a3dd65f136e1d3a28c6093926f5aae8295a1986509c981a4ee53681fd3e2963.png"
    ],
    "lcd-display-speedometer-2w": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/759ff46645ac82333a767f14e5715177ace29ca4e858b7b45096e9a3a0411d6e.png"
    ],
    "on-board-charger-3-3kw-4w": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/a12e7d909f0c0553cd2474215a01867987835cc27a783ede365b41dbafb52b05.png"
    ],
    "battery-management-system-96s": [
        "https://static.prod-images.emergentagent.com/jobs/58c021dc-edd3-4be8-9b89-5ce7ff5c876c/images/31c477d1d18c3776c6c4226eda54f1c0738796428cd2750f41df6aafed45889e.png"
    ],
}

async def update_images():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("Updating products with AI-generated images...")
    updated = 0
    not_found = 0
    
    for slug, images in AI_PRODUCT_IMAGES.items():
        result = await db.marketplace_products.update_one(
            {"slug": slug},
            {"$set": {"images": images}}
        )
        if result.modified_count > 0:
            print(f"  ✓ {slug}")
            updated += 1
        else:
            exists = await db.marketplace_products.find_one({"slug": slug})
            if exists:
                print(f"  ~ {slug} (no change)")
            else:
                print(f"  ✗ {slug} not found")
                not_found += 1
    
    print(f"\n✅ Updated {updated} products with AI-generated images")
    if not_found > 0:
        print(f"⚠️  {not_found} products not found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_images())
