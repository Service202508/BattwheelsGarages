"""
Battwheels OS - Public Ticket Routes
Public-facing ticket submission, tracking, and payment integration
No authentication required for these endpoints

Multi-Tenancy: org resolution via subdomain (workshopname.battwheels.com)
               with X-Organization-Slug header fallback for API/PWA clients.
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid

def get_db():
    from server import db
    return db

router = APIRouter(prefix="/public", tags=["Public Tickets"])


# ==================== ORG RESOLUTION ====================

async def get_org_from_request(request: Request, db) -> str:
    """
    Extract organization from subdomain.
    workshopname.battwheels.com → look up org where slug = 'workshopname'
    Falls back to X-Organization-Slug header for API clients and PWA.
    """
    host = request.headers.get("host", "")

    # Extract subdomain: "workshopname.battwheels.com" → "workshopname"
    parts = host.split(".")
    if len(parts) >= 3:
        candidate = parts[0]
        # Ignore known non-workshop prefixes (preview URLs, platform subdomains)
        if candidate in ("www", "app", "api", "platform", "production-deploy-7", "audit-fixes-5"):
            subdomain = None
        else:
            subdomain = candidate
    else:
        subdomain = None

    # Fallback: check header (for direct API calls, mobile PWA, preview URLs)
    if not subdomain:
        subdomain = request.headers.get("X-Organization-Slug", None)

    if not subdomain:
        raise HTTPException(
            status_code=400,
            detail="Cannot determine workshop. Please use your workshop URL (e.g. yourworkshop.battwheels.com)."
        )

    org = await db.organizations.find_one(
        {"slug": subdomain, "is_active": True},
        {"_id": 0, "organization_id": 1, "name": 1}
    )

    if not org:
        raise HTTPException(status_code=404, detail="Workshop not found or inactive.")

    return org["organization_id"]


# ==================== MODELS ====================

class PublicTicketCreate(BaseModel):
    # Vehicle Info
    vehicle_category: str  # e.g., "2W_EV"
    vehicle_model_id: Optional[str] = None
    vehicle_model_name: Optional[str] = None  # Free text if model not in list
    vehicle_oem: Optional[str] = None
    vehicle_number: str
    
    # Customer Info
    customer_type: str  # "individual" or "business"
    customer_name: str
    contact_number: str
    email: Optional[str] = None
    
    # For business customers
    business_name: Optional[str] = None
    gst_number: Optional[str] = None
    
    # Issue Details
    title: str
    description: str
    issue_type: str
    priority: str = "medium"
    
    # Resolution
    resolution_type: str  # "workshop", "onsite", "pickup", "remote"
    
    # Location (for onsite)
    incident_location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    
    # Payment selection (for individual + onsite)
    include_visit_fee: bool = False  # Rs. 299
    include_diagnostic_fee: bool = False  # Rs. 199


class TicketPaymentVerify(BaseModel):
    ticket_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class TicketLookup(BaseModel):
    ticket_id: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None


# ==================== PUBLIC TICKET SUBMISSION ====================

@router.post("/tickets/submit")
async def submit_public_ticket(request: Request, data: PublicTicketCreate, background_tasks: BackgroundTasks):
    """
    Submit a service ticket from public form.

    Organization is resolved from the request subdomain or X-Organization-Slug header.
    For Individual + OnSite: Returns payment details.
    For other combinations: Creates ticket directly.
    """
    db = get_db()

    # STEP 1 — resolve org from subdomain / header (never from a hardcoded default)
    organization_id = await get_org_from_request(request, db)

    # STEP 4 — guard: should never be None after get_org_from_request, but be explicit
    if not organization_id:
        raise HTTPException(
            status_code=400,
            detail="Workshop configuration error. Contact the workshop directly."
        )

    ticket_id = f"tkt_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Determine if payment is required
    requires_payment = data.customer_type == "individual" and data.resolution_type == "onsite"
    
    # Calculate fees
    visit_fee = 299 if data.include_visit_fee else 0
    diagnostic_fee = 199 if data.include_diagnostic_fee else 0
    total_fee = visit_fee + diagnostic_fee
    
    # If Individual + OnSite without visit fee selected, force visit fee
    if requires_payment and not data.include_visit_fee:
        visit_fee = 299
        data.include_visit_fee = True
        total_fee = visit_fee + diagnostic_fee
    
    # Get vehicle category details
    category = await db.vehicle_categories.find_one({"code": data.vehicle_category}, {"_id": 0})
    category_name = category.get("name", data.vehicle_category) if category else data.vehicle_category
    
    # Get vehicle model details if provided
    model_name = data.vehicle_model_name
    oem = data.vehicle_oem
    if data.vehicle_model_id:
        model = await db.vehicle_models.find_one({"model_id": data.vehicle_model_id}, {"_id": 0})
        if model:
            model_name = model.get("name")
            oem = model.get("oem")
    
    # Build ticket document
    ticket_doc = {
        "ticket_id": ticket_id,
        "organization_id": organization_id,  # Link to default organization
        "title": data.title,
        "description": data.description,
        "category": data.issue_type,
        "priority": data.priority,
        "status": "pending_payment" if requires_payment else "open",
        
        # Vehicle info
        "vehicle_type": data.vehicle_category,
        "vehicle_category": data.vehicle_category,
        "vehicle_category_name": category_name,
        "vehicle_model": model_name,
        "vehicle_model_id": data.vehicle_model_id,
        "vehicle_oem": oem,
        "vehicle_number": data.vehicle_number.upper(),
        
        # Customer info
        "customer_type": data.customer_type,
        "customer_name": data.customer_name,
        "contact_number": data.contact_number,
        "customer_email": data.email,
        "business_name": data.business_name,
        "gst_number": data.gst_number,
        
        # Issue details
        "issue_type": data.issue_type,
        "resolution_type": data.resolution_type,
        
        # Location
        "incident_location": data.incident_location,
        "location_coordinates": {
            "lat": data.location_lat,
            "lng": data.location_lng
        } if data.location_lat and data.location_lng else None,
        
        # Fees
        "visit_fee": visit_fee,
        "diagnostic_fee": diagnostic_fee,
        "initial_payment_amount": total_fee,
        "payment_status": "pending" if requires_payment else "not_required",
        
        # Status tracking
        "status_history": [{
            "status": "pending_payment" if requires_payment else "open",
            "timestamp": now.isoformat(),
            "notes": "Ticket submitted via public form"
        }],
        
        # Source
        "source": "public_form",
        "is_public_submission": True,
        
        # Timestamps
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        
        # Generate access token for public tracking
        "public_access_token": uuid.uuid4().hex,
    }
    
    # Store ticket
    await db.tickets.insert_one(ticket_doc)
    
    # Get stored ticket without _id
    stored_ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    
    if requires_payment and total_fee > 0:
        # Create Razorpay order for payment
        from services.razorpay_service import create_razorpay_order, is_razorpay_configured
        import os
        
        order = await create_razorpay_order(
            amount_inr=total_fee,
            receipt=ticket_id,
            notes={
                "ticket_id": ticket_id,
                "customer_name": data.customer_name,
                "customer_phone": data.contact_number,
                "visit_fee": visit_fee,
                "diagnostic_fee": diagnostic_fee
            }
        )
        
        # Store order reference
        await db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"razorpay_order_id": order["id"]}}
        )
        
        return {
            "ticket_id": ticket_id,
            "status": "pending_payment",
            "requires_payment": True,
            "payment_details": {
                "order_id": order["id"],
                "amount": total_fee,
                "amount_paise": int(total_fee * 100),
                "currency": "INR",
                "visit_fee": visit_fee,
                "diagnostic_fee": diagnostic_fee,
                "key_id": os.environ.get('RAZORPAY_KEY_ID', ''),
                "is_mock": order.get("_mock", False)
            },
            "customer": {
                "name": data.customer_name,
                "email": data.email,
                "phone": data.contact_number
            },
            "tracking_url": f"/track-ticket?id={ticket_id}&token={stored_ticket['public_access_token']}"
        }
    else:
        # Ticket created directly (Business customer or non-onsite)
        # Send notification in background
        background_tasks.add_task(send_ticket_notification, db, ticket_id, "ticket_created")
        
        return {
            "ticket_id": ticket_id,
            "status": "open",
            "requires_payment": False,
            "message": "Your service ticket has been submitted successfully",
            "tracking_url": f"/track-ticket?id={ticket_id}&token={stored_ticket['public_access_token']}"
        }


@router.post("/tickets/verify-payment")
async def verify_ticket_payment(data: TicketPaymentVerify, background_tasks: BackgroundTasks):
    """Verify payment and activate ticket"""
    db = get_db()
    
    # Get ticket
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.get("payment_status") == "paid":
        return {"message": "Payment already verified", "ticket_id": data.ticket_id}
    
    # Verify signature
    from services.razorpay_service import verify_payment_signature
    
    is_valid = await verify_payment_signature(
        data.razorpay_order_id,
        data.razorpay_payment_id,
        data.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    now = datetime.now(timezone.utc)
    
    # Update ticket status
    history = ticket.get("status_history", [])
    history.append({
        "status": "open",
        "timestamp": now.isoformat(),
        "notes": f"Payment verified - ₹{ticket.get('initial_payment_amount', 0)}"
    })
    
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id},
        {"$set": {
            "status": "open",
            "payment_status": "paid",
            "razorpay_payment_id": data.razorpay_payment_id,
            "payment_verified_at": now.isoformat(),
            "status_history": history,
            "updated_at": now.isoformat()
        }}
    )
    
    # Store payment record
    payment_record = {
        "payment_id": f"RPAY-{uuid.uuid4().hex[:12].upper()}",
        "ticket_id": data.ticket_id,
        "razorpay_order_id": data.razorpay_order_id,
        "razorpay_payment_id": data.razorpay_payment_id,
        "amount": ticket.get("initial_payment_amount", 0),
        "type": "service_fee",
        "description": "Visit & Diagnostic Charges",
        "status": "captured",
        "date": now.strftime("%Y-%m-%d"),
        "created_at": now.isoformat()
    }
    await db.ticket_payments.insert_one(payment_record)
    
    # Send notification
    background_tasks.add_task(send_ticket_notification, db, data.ticket_id, "ticket_created")
    
    return {
        "message": "Payment verified successfully",
        "ticket_id": data.ticket_id,
        "status": "open"
    }


# ==================== PUBLIC TICKET TRACKING ====================

@router.post("/tickets/lookup")
async def lookup_ticket(request: Request, data: TicketLookup):
    """Look up ticket(s) by ID, phone, or email — scoped to the requesting workshop."""
    db = get_db()

    if not data.ticket_id and not data.contact_number and not data.email:
        raise HTTPException(status_code=400, detail="Please provide ticket ID, phone number, or email")

    # STEP 2 — scope every lookup to the workshop that owns the request
    organization_id = await get_org_from_request(request, db)

    query = {"organization_id": organization_id}
    if data.ticket_id:
        query["ticket_id"] = data.ticket_id
    elif data.contact_number:
        query["contact_number"] = {"$regex": data.contact_number[-10:], "$options": "i"}
    elif data.email:
        query["customer_email"] = {"$regex": data.email, "$options": "i"}
    
    tickets = await db.tickets.find(
        query,
        {
            "_id": 0,
            "ticket_id": 1,
            "title": 1,
            "status": 1,
            "priority": 1,
            "vehicle_number": 1,
            "vehicle_model": 1,
            "created_at": 1,
            "customer_name": 1,
            "public_access_token": 1
        }
    ).sort("created_at", -1).to_list(20)
    
    if not tickets:
        raise HTTPException(status_code=404, detail="No tickets found")
    
    return {"tickets": tickets, "total": len(tickets)}


@router.get("/tickets/{ticket_id}")
async def get_public_ticket(
    ticket_id: str,
    token: Optional[str] = None,
    contact: Optional[str] = None
):
    """Get ticket details for public tracking"""
    db = get_db()
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Verify access (either token or contact number)
    is_authorized = False
    if token and ticket.get("public_access_token") == token:
        is_authorized = True
    elif contact:
        contact_clean = contact[-10:] if len(contact) >= 10 else contact
        ticket_contact = ticket.get("contact_number", "")[-10:]
        if contact_clean == ticket_contact:
            is_authorized = True
        if contact.lower() == ticket.get("customer_email", "").lower():
            is_authorized = True
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Access denied. Please verify your contact details.")
    
    # Get estimate if exists
    # STEP 3 — scope all linked data to the ticket's own org_id
    org_id = ticket["organization_id"]

    estimate = await db.ticket_estimates.find_one(
        {"ticket_id": ticket_id, "organization_id": org_id},
        {"_id": 0}
    )
    
    # Get estimate line items
    estimate_items = []
    if estimate:
        estimate_items = await db.ticket_estimate_line_items.find(
            {"estimate_id": estimate.get("estimate_id")},
            {"_id": 0}
        ).to_list(100)
    
    # Get invoice if exists
    invoice = await db.invoices.find_one(
        {"ticket_id": ticket_id, "organization_id": org_id},
        {"_id": 0, "invoice_id": 1, "invoice_number": 1, "total": 1, "balance": 1, "status": 1, "payment_link_url": 1}
    )
    
    # Get payments
    payments = await db.ticket_payments.find(
        {"ticket_id": ticket_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Get activities
    activities = await db.ticket_activities.find(
        {"ticket_id": ticket_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    
    # Build response with safe data only
    return {
        "ticket": {
            "ticket_id": ticket.get("ticket_id"),
            "title": ticket.get("title"),
            "description": ticket.get("description"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "vehicle_number": ticket.get("vehicle_number"),
            "vehicle_model": ticket.get("vehicle_model"),
            "vehicle_oem": ticket.get("vehicle_oem"),
            "vehicle_category_name": ticket.get("vehicle_category_name"),
            "resolution_type": ticket.get("resolution_type"),
            "incident_location": ticket.get("incident_location"),
            "customer_name": ticket.get("customer_name"),
            "assigned_technician_name": ticket.get("assigned_technician_name"),
            "payment_status": ticket.get("payment_status"),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at"),
            "status_history": ticket.get("status_history", [])
        },
        "estimate": {
            "estimate_id": estimate.get("estimate_id") if estimate else None,
            "status": estimate.get("status") if estimate else None,
            "subtotal": estimate.get("subtotal") if estimate else 0,
            "tax_total": estimate.get("tax_total") if estimate else 0,
            "grand_total": estimate.get("grand_total") if estimate else 0,
            "line_items": estimate_items,
            "can_approve": estimate.get("status") == "sent" if estimate else False
        } if estimate else None,
        "invoice": invoice,
        "payments": payments,
        "activities": [
            {
                "action": act.get("action"),
                "description": act.get("description"),
                "timestamp": act.get("timestamp"),
                "user_name": act.get("user_name")
            }
            for act in activities
        ]
    }


@router.post("/tickets/{ticket_id}/approve-estimate")
async def public_approve_estimate(
    ticket_id: str,
    token: str,
    background_tasks: BackgroundTasks
):
    """Allow customer to approve estimate from public tracking"""
    db = get_db()
    
    # Verify access
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.get("public_access_token") != token:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get estimate
    estimate = await db.ticket_estimates.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not estimate:
        raise HTTPException(status_code=404, detail="No estimate found for this ticket")
    
    if estimate.get("status") == "approved":
        return {"message": "Estimate already approved"}
    
    if estimate.get("status") not in ["draft", "sent"]:
        raise HTTPException(status_code=400, detail=f"Cannot approve estimate in '{estimate.get('status')}' status")
    
    now = datetime.now(timezone.utc)
    
    # Update estimate
    await db.ticket_estimates.update_one(
        {"estimate_id": estimate.get("estimate_id")},
        {"$set": {
            "status": "approved",
            "approved_at": now.isoformat(),
            "approved_by": "customer",
            "customer_approval": True,
            "updated_at": now.isoformat()
        }}
    )
    
    # Update ticket status to work_in_progress
    history = ticket.get("status_history", [])
    history.append({
        "status": "work_in_progress",
        "timestamp": now.isoformat(),
        "notes": "Estimate approved by customer"
    })
    
    await db.tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status": "work_in_progress",
            "estimate_approved_at": now.isoformat(),
            "status_history": history,
            "updated_at": now.isoformat()
        }}
    )
    
    # Log activity
    await db.ticket_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:12]}",
        "ticket_id": ticket_id,
        "action": "estimate_approved",
        "description": "Customer approved the service estimate",
        "user_id": "customer",
        "user_name": ticket.get("customer_name"),
        "timestamp": now.isoformat()
    })
    
    # Send notification
    background_tasks.add_task(send_ticket_notification, db, ticket_id, "estimate_approved")
    
    return {
        "message": "Estimate approved successfully",
        "ticket_status": "work_in_progress"
    }


# ==================== MASTER DATA FOR PUBLIC FORM ====================

@router.get("/vehicle-categories")
async def get_public_vehicle_categories():
    """Get vehicle categories for public form"""
    db = get_db()
    categories = await db.vehicle_categories.find(
        {"is_active": True},
        {"_id": 0, "category_id": 1, "code": 1, "name": 1, "icon": 1}
    ).sort("sort_order", 1).to_list(20)
    return {"categories": categories}

@router.get("/vehicle-models")
async def get_public_vehicle_models(category_code: Optional[str] = None):
    """Get vehicle models for public form"""
    db = get_db()
    query = {"is_active": True}
    if category_code:
        query["category_code"] = category_code
    
    models = await db.vehicle_models.find(
        query,
        {"_id": 0, "model_id": 1, "name": 1, "oem": 1, "category_code": 1, "range_km": 1}
    ).sort([("oem", 1), ("name", 1)]).to_list(200)
    
    # Group by OEM
    oems_map = {}
    for model in models:
        oem = model.get("oem", "Other")
        if oem not in oems_map:
            oems_map[oem] = []
        oems_map[oem].append(model)
    
    return {"models": models, "by_oem": oems_map}

@router.get("/issue-suggestions")
async def get_public_issue_suggestions(
    category_code: Optional[str] = None,
    model_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Get issue suggestions for public form"""
    db = get_db()
    query = {"is_active": True}
    
    if category_code:
        query["category_codes"] = category_code
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"common_symptoms": {"$elemMatch": {"$regex": search, "$options": "i"}}}
        ]
    
    suggestions = await db.ev_issue_suggestions.find(
        query,
        {"_id": 0, "suggestion_id": 1, "title": 1, "issue_type": 1, "common_symptoms": 1, "severity": 1}
    ).sort("usage_count", -1).to_list(30)
    
    return {"suggestions": suggestions}


# ==================== HELPER FUNCTIONS ====================

async def send_ticket_notification(db, ticket_id: str, notification_type: str):
    """Send email/SMS notification for ticket events"""
    try:
        from services.notification_service import send_email_async
        
        ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
        if not ticket:
            return
        
        customer_email = ticket.get("customer_email")
        if not customer_email:
            return
        
        # Build email context
        context = {
            "ticket_id": ticket_id,
            "customer_name": ticket.get("customer_name", "Customer"),
            "vehicle_number": ticket.get("vehicle_number", "N/A"),
            "issue_title": ticket.get("title", "Service Request"),
            "priority": ticket.get("priority", "medium"),
            "tracking_url": f"https://battwheels.com/track-ticket?id={ticket_id}&token={ticket.get('public_access_token', '')}"
        }
        
        # For now, just log - actual email sending requires RESEND_API_KEY
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Would send {notification_type} notification to {customer_email} for ticket {ticket_id}")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send notification: {e}")


# ==================== SERVICE CHARGES INFO ====================

@router.get("/service-charges")
async def get_service_charges():
    """Get current service charge rates"""
    return {
        "visit_fee": {
            "amount": 299,
            "currency": "INR",
            "description": "Visit Charges (Mandatory for On-Site Service)",
            "mandatory_for": ["individual_onsite"]
        },
        "diagnostic_fee": {
            "amount": 199,
            "currency": "INR", 
            "description": "Diagnostic Charges (Optional)",
            "mandatory_for": []
        },
        "note": "These charges are applicable for Individual customers opting for On-Site Resolution only."
    }


# ==================== AI ISSUE SUGGESTIONS ====================

class AIIssueSuggestionRequest(BaseModel):
    vehicle_category: str  # e.g., "2W_EV", "3W_EV", "4W_EV"
    vehicle_model: Optional[str] = None
    vehicle_oem: Optional[str] = None
    user_input: str  # What the user is typing/describing

@router.post("/ai/issue-suggestions")
async def get_ai_issue_suggestions(data: AIIssueSuggestionRequest):
    """
    Get AI-powered issue suggestions based on vehicle type and user input.
    Uses Gemini to analyze the input and suggest relevant issues.
    """
    import os
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        # Fallback to static suggestions if no API key
        return {
            "suggestions": [
                {"title": "Battery not charging", "issue_type": "battery", "severity": "high"},
                {"title": "Motor making noise", "issue_type": "motor", "severity": "medium"},
                {"title": "Display/Dashboard error", "issue_type": "electrical", "severity": "medium"},
            ],
            "ai_enabled": False
        }
    
    try:
        # Get vehicle category context
        vehicle_context = {
            "2W_EV": "Electric 2-wheeler (scooter/motorcycle)",
            "3W_EV": "Electric 3-wheeler (auto-rickshaw/cargo)",
            "4W_EV": "Electric 4-wheeler (car/SUV)",
            "COMM_EV": "Commercial Electric Vehicle (bus/truck)",
            "LEV": "Light Electric Vehicle"
        }.get(data.vehicle_category, "Electric Vehicle")
        
        # Create the prompt for Gemini
        system_message = f"""You are an expert EV service diagnostic assistant for Battwheels, an electric vehicle service company in India.

Based on the user's description of their vehicle issue, suggest the 3-5 most likely problems they might be facing.

Vehicle Type: {vehicle_context}
Vehicle Model: {data.vehicle_model or 'Not specified'}
Vehicle Manufacturer: {data.vehicle_oem or 'Not specified'}

For each suggestion, provide:
1. A clear, concise title (max 50 characters)
2. Issue type: one of [battery, motor, controller, charger, electrical, brakes, suspension, tires, body, software, other]
3. Severity: one of [low, medium, high, critical]
4. Brief description (max 100 characters)

Respond ONLY with a valid JSON array in this exact format:
[
  {{"title": "Issue title here", "issue_type": "battery", "severity": "high", "description": "Brief description"}},
  ...
]

Be specific to EV problems. Consider common issues for the vehicle type mentioned.
Do not include any text before or after the JSON array."""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"ai_suggestions_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("gemini", "gemini-3-flash-preview")
        
        user_message = UserMessage(
            text=f"Customer's description of the problem: {data.user_input}"
        )
        
        response = await chat.send_message(user_message)
        
        # Parse the response
        import json
        import re
        
        # Extract JSON from response (handle potential markdown wrapping)
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            suggestions = json.loads(json_match.group())
            return {
                "suggestions": suggestions[:5],  # Limit to 5 suggestions
                "ai_enabled": True
            }
        else:
            # If parsing fails, return fallback
            return {
                "suggestions": [
                    {"title": "Battery issue detected", "issue_type": "battery", "severity": "medium", "description": "Based on your description"},
                ],
                "ai_enabled": True,
                "parsing_note": "AI response parsed with fallback"
            }
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"AI suggestion error: {e}")
        
        # Return fallback suggestions on error
        return {
            "suggestions": [
                {"title": "Battery not holding charge", "issue_type": "battery", "severity": "high"},
                {"title": "Motor performance issue", "issue_type": "motor", "severity": "medium"},
                {"title": "Electrical system fault", "issue_type": "electrical", "severity": "medium"},
            ],
            "ai_enabled": False,
            "error": "AI service temporarily unavailable"
        }
