from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Battwheels Garages API", version="1.0.0")

# Import routes
from routes import bookings, fleet_enquiries, contacts, careers, public_content, seo
from routes import admin_auth, admin_bookings, admin_contacts, admin_services, admin_blogs, admin_testimonials, admin_jobs
from routes import marketplace, marketplace_auth
from routes import payments

# Health check routes (both /health and /api/health for Kubernetes compatibility)
@app.get("/health")
async def health_check_root():
    return {"status": "healthy", "message": "Battwheels Garages API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Battwheels Garages API is running"}

# Include public routers
app.include_router(bookings.router)
app.include_router(fleet_enquiries.router)
app.include_router(contacts.router)
app.include_router(careers.router)
app.include_router(public_content.router)
app.include_router(seo.router)

# Include admin routers
app.include_router(admin_auth.router)
app.include_router(admin_bookings.router)
app.include_router(admin_contacts.router)
app.include_router(admin_services.router)
app.include_router(admin_blogs.router)
app.include_router(admin_testimonials.router)
app.include_router(admin_jobs.router)

# Include marketplace routers
app.include_router(marketplace.router)
app.include_router(marketplace_auth.router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()