"""
Quick script to add prices to refurbished vehicles
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random

async def update_prices():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Price ranges based on vehicle category
    # 2W: 50,000 - 1,50,000
    # 3W: 1,20,000 - 3,50,000
    
    # Update 2-Wheelers
    two_wheelers = await db.marketplace_products.find({"vehicle_category": "2W"}).to_list(length=100)
    for v in two_wheelers:
        base_price = random.randint(60000, 180000)
        # Round to nearest 5000
        base_price = round(base_price / 5000) * 5000
        final_price = int(base_price * 0.85)  # 15% discount for refurbished
        
        await db.marketplace_products.update_one(
            {"_id": v["_id"]},
            {"$set": {
                "price": base_price,
                "final_price": final_price,
                "discount_percent": 15
            }}
        )
        print(f"Updated 2W: {v.get('name')} - ₹{final_price:,}")
    
    # Update 3-Wheelers
    three_wheelers = await db.marketplace_products.find({"vehicle_category": "3W"}).to_list(length=100)
    for v in three_wheelers:
        base_price = random.randint(150000, 400000)
        # Round to nearest 10000
        base_price = round(base_price / 10000) * 10000
        final_price = int(base_price * 0.80)  # 20% discount for refurbished
        
        await db.marketplace_products.update_one(
            {"_id": v["_id"]},
            {"$set": {
                "price": base_price,
                "final_price": final_price,
                "discount_percent": 20
            }}
        )
        print(f"Updated 3W: {v.get('name')} - ₹{final_price:,}")
    
    print(f"\n✅ Updated prices for {len(two_wheelers)} 2-wheelers and {len(three_wheelers)} 3-wheelers")
    client.close()

if __name__ == "__main__":
    asyncio.run(update_prices())
