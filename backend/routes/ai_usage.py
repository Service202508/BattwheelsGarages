"""
AI Usage Routes
===============
Token status endpoint for the AI diagnostic system.
"""

from fastapi import APIRouter, HTTPException, Request
from utils.database import extract_org_id

router = APIRouter(prefix="/ai-usage", tags=["AI Usage"])

_db = None


def init_router(database):
    global _db
    _db = database


@router.get("/status")
async def get_ai_usage_status(request: Request):
    """Get AI diagnostic token status for the authenticated user's org."""
    # Auth check
    org_id = extract_org_id(request)
    if not org_id:
        raise HTTPException(status_code=401, detail="Organization context required")

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    from utils.auth import decode_token_safe
    payload = decode_token_safe(token)
    if not payload or not payload.get("user_id"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    from services.ai_token_service import get_token_status
    status = await get_token_status(org_id)
    return status
