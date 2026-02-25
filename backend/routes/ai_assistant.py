"""
Battwheels OS - Unified AI Assistant Routes
Centralized AI endpoints for all portals
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
import logging

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


@router.post("/diagnose", response_model=AIQueryResponse)
async def ai_diagnose(request: Request, data: AIQueryRequest):
    """
    Unified AI Assistant endpoint for all portals.
    Routes queries to Gemini with portal-specific context.
    Tenant-scoped: uses organization_id from authenticated context.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    # CRITICAL: Extract tenant context from TenantGuardMiddleware
    org_id = getattr(request.state, "tenant_org_id", None)
    user_id = getattr(request.state, "tenant_user_id", None)
    user_role = getattr(request.state, "tenant_user_role", "viewer")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    
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
        
        # Portal-specific system prompts
        portal_prompts = {
            "admin": f"""You are an AI Business Assistant for Battwheels OS, an EV service management platform.
You are helping {user_name}, an administrator/manager.

Your expertise includes:
- Business operations and workflow optimization
- Financial reporting and analytics
- Inventory management and stock alerts
- Customer relationship management
- Service scheduling and resource allocation
- Invoice and payment tracking

Guidelines:
1. Provide actionable business insights
2. Reference relevant data and metrics when possible
3. Suggest optimizations and improvements
4. Be concise but comprehensive
5. Format responses with clear sections""",

            "technician": f"""You are an expert EV Service Technician AI Assistant for Battwheels.
You are helping {user_name} with EV repairs and diagnostics.

Your expertise includes:
- Electric 2-wheelers (Ola, Ather, TVS iQube, Hero Electric, Bajaj Chetak)
- Electric 3-wheelers (Mahindra Treo, Piaggio Ape E-City, Euler HiLoad)
- Electric 4-wheelers (Tata Nexon EV, MG ZS EV, Hyundai Kona)
- Battery systems (Li-ion, LFP, NMC), BMS diagnostics
- Motor controllers, BLDC/PMSM motors
- Charging systems (AC/DC chargers, CCS, CHAdeMO)
- CAN bus diagnostics and error code interpretation

Guidelines:
1. Be concise but thorough - technicians need actionable information
2. Include specific steps, measurements, and safety warnings
3. Reference common Indian EV models when relevant
4. Suggest proper tools and equipment needed
5. Highlight safety precautions for high-voltage work""",

            "business": f"""You are an AI Service Assistant for Battwheels, helping business customers manage their EV fleet.
You are assisting {user_name}.

Your expertise includes:
- Fleet service tracking and status updates
- Invoice and billing inquiries
- Service scheduling and appointments
- Vehicle maintenance recommendations
- Cost optimization for fleet operations

Guidelines:
1. Be helpful and professional
2. Provide clear status updates
3. Explain charges and invoices clearly
4. Help with scheduling and planning""",

            "customer": f"""You are a friendly AI Service Assistant for Battwheels EV Services.
You are helping {user_name} with their electric vehicle service needs.

Your expertise includes:
- Service status updates
- Invoice and payment inquiries
- Appointment scheduling
- General EV maintenance questions
- Warranty and service information

Guidelines:
1. Be friendly and approachable
2. Explain technical concepts simply
3. Provide clear, helpful answers
4. Guide users through processes step by step"""
        }
        
        # Category-specific additions
        category_focus = {
            "battery": "\n\nFocus on battery-related issues including BMS, cells, charging, and thermal management.",
            "motor": "\n\nFocus on motor and controller issues including BLDC motors, inverters, and regenerative braking.",
            "electrical": "\n\nFocus on electrical system issues including wiring, fuses, relays, and high-voltage systems.",
            "diagnosis": "\n\nFocus on systematic fault diagnosis using symptom analysis and error code interpretation.",
            "inventory": "\n\nFocus on inventory management, stock levels, and procurement planning.",
            "reports": "\n\nFocus on generating reports, analytics, and business insights.",
            "customers": "\n\nFocus on customer management, communication, and relationship building.",
            "invoices": "\n\nFocus on invoice details, payment tracking, and billing inquiries.",
            "service": "\n\nFocus on service requests, status updates, and maintenance schedules.",
            "vehicle": "\n\nFocus on vehicle-specific information, maintenance history, and recommendations.",
            "general": ""
        }
        
        system_message = portal_prompts.get(data.portal_type, portal_prompts["admin"])
        system_message += category_focus.get(data.category, "")
        
        system_message += """

Format your responses with:
- Clear headings using ## or ###
- Bullet points for lists
- **Bold** for important values or warnings
- Numbered lists for procedures"""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"ai_{org_id}_{data.portal_type}_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("gemini", "gemini-3-flash-preview")
        
        user_message = UserMessage(text=data.query)
        response = await chat.send_message(user_message)
        
        return AIQueryResponse(
            response=response,
            ai_enabled=True,
            category=data.category,
            confidence=0.85
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
