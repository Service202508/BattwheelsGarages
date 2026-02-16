"""
Battwheels OS - Database Configuration
Centralized database connection and utilities
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_os")

# Create client and database
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def get_database():
    """Get database instance for dependency injection"""
    return db

async def close_database():
    """Close database connection"""
    client.close()
