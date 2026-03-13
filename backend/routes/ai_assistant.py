"""
Battwheels OS - Unified AI Assistant Routes
Centralized AI endpoints for all portals — uses Battwheels EVFI™ system prompt
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
import logging

from services.ai_guidance_service import get_efi_system_prompt, inject_safety_warning, classify_efi_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-assist", tags=["AI Assistant"])

def get_db():
    from server import db
    return db


class AIQueryRequest(BaseModel):
    query: str
    category: str = "general"
    portal_type: str = "admin"  # admin, technician, business, customer
    context: Optional[Dict[str, Any]] = None


class AIQueryResponse(BaseModel):
    response: str
    ai_enabled: bool = True
    category: str = "general"
    confidence: Optional[float] = None
    sources: Optional[list] = None
    efi_classification: Optional[Dict[str, Any]] = None


@router.post("/diagnose", response_model=AIQueryResponse)
async def ai_diagnose(request: Request, data: AIQueryRequest):
    """
    Unified AI Assistant endpoint for all portals.
    Routes queries to Gemini with Battwheels EVFI™ system prompt.
    Tenant-scoped: uses organization_id from authenticated context.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    # CRITICAL: Extract tenant context from TenantGuardMiddleware
    org_id = getattr(request.state, "tenant_org_id", None)
    user_id = getattr(request.state, "tenant_user_id", None)
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
    # Enforce AI call limit before making LLM call
    try:
        from services.usage_tracker import get_usage_tracker
        tracker = get_usage_tracker()
        within_limit, current, limit = await tracker.check_limit(org_id, "ai_calls")
        if not within_limit:
            raise HTTPException(status_code=429, detail={
                "error": "ai_limit_exceeded",
                "message": f"AI call limit reached ({current}/{limit}). Upgrade your plan for more.",
                "current_usage": current,
                "limit": limit,
                "upgrade_url": "/subscription"
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to check AI limit for {org_id}: {e}")
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        return AIQueryResponse(
            response="AI assistant is currently unavailable. Please check your configuration or contact support.",
            ai_enabled=False,
            category=data.category
        )
    
    try:
        # Get user name from database (NOT from request body — prevents spoofing)
        db = get_db()
        user_name = "User"
        if user_id:
            user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "name": 1})
            if user_doc:
                user_name = user_doc.get("name", "User")
        
        # Use the canonical Battwheels EVFI™ system prompt
        system_message = get_efi_system_prompt()
        system_message += f"\n\nYou are helping {user_name} ({data.portal_type} portal)."
        
        # Category-specific focus addition
        category_focus = {
            "battery": "\nFocus on battery-related issues including BMS, cells, charging, and thermal management.",
            "motor": "\nFocus on motor and controller issues including BLDC motors, inverters, and regenerative braking.",
            "electrical": "\nFocus on electrical system issues including wiring, fuses, relays, and high-voltage systems.",
            "diagnosis": "\nFocus on systematic fault diagnosis using symptom analysis and error code interpretation.",
            "general": ""
        }
        system_message += category_focus.get(data.category, "")

        chat = LlmChat(
            api_key=api_key,
            session_id=f"ai_{org_id}_{data.portal_type}_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("gemini", "gemini-3-flash-preview")
        
        user_message = UserMessage(text=data.query)
        response = await chat.send_message(user_message)
        
        # Post-process: inject safety warning + classify
        ticket_data = {
            "description": data.query,
            "issue_type": data.category or "",
            "category": data.category or "",
            "vehicle_make": (data.context or {}).get("vehicle_make", ""),
            "vehicle_model": (data.context or {}).get("vehicle_model", ""),
        }
        processed_response = inject_safety_warning(response, ticket_data)
        efi_classification = classify_efi_response(ticket_data)
        
        # Track AI usage against subscription limits
        try:
            from services.usage_tracker import get_usage_tracker
            tracker = get_usage_tracker()
            await tracker.increment_usage(org_id, "ai_calls")
        except Exception as track_err:
            logger.warning(f"Failed to track AI usage for {org_id}: {track_err}")
        
        return AIQueryResponse(
            response=processed_response,
            ai_enabled=True,
            category=data.category,
            confidence=0.85,
            efi_classification=efi_classification
        )
            
    except Exception as e:
        logger.error(f"AI diagnose error: {e}")
        
        return AIQueryResponse(
            response="I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support if the issue persists.",
            ai_enabled=False,
            category=data.category
        )


@router.get("/health")
async def ai_health():
    """Check if AI service is available"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    return {
        "status": "available" if api_key else "unavailable",
        "model": "gemini-3-flash-preview"
    }
