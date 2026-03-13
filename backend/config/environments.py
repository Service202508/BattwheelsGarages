"""
Environment Configuration for Battwheels OS
============================================
Three environments: development, staging, production
Config is read from environment variables with safe fallbacks.

MONGO_URL and DB_NAME are NEVER hardcoded for staging/production.
They MUST come from injected environment variables (Emergent secrets).

Development uses localhost fallbacks for local container work.
"""
import os
import logging

logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Database configuration — injected secrets override everything
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "battwheels_dev")

def is_development() -> bool:
    return ENVIRONMENT == "development"

def is_staging() -> bool:
    return ENVIRONMENT == "staging"

def is_production() -> bool:
    return ENVIRONMENT == "production"

def get_environment_info() -> dict:
    """Return safe environment info (no secrets) for health/status endpoints."""
    return {
        "environment": ENVIRONMENT,
        "db_name": DB_NAME,
        "mongo_host": MONGO_URL.split("@")[-1].split("/")[0] if "@" in MONGO_URL else MONGO_URL.split("//")[-1].split("/")[0],
    }

# Log environment on import
logger.info(f"Environment: {ENVIRONMENT} | DB: {DB_NAME} | Mongo: {'Atlas' if 'mongodb+srv' in MONGO_URL else 'localhost'}")
