"""
Battwheels OS - Notification Service
Handles Email (Resend) and WhatsApp (Twilio) notifications
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import os
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# Database reference
db = None

def init_router(database):
    global db
    db = database
    return router

# Models
class EmailRequest(BaseModel):
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: Optional[str] = None  # Optional - will be auto-generated from template if not provided
    template: str  # ticket_created, ticket_assigned, estimate_shared, invoice_generated
    context: dict = {}

class WhatsAppRequest(BaseModel):
    phone_number: str  # E.164 format: +91XXXXXXXXXX
    template: str
    context: dict = {}

class NotificationLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    notification_id: str = ""
    channel: str  # email, whatsapp, sms
    recipient: str
    template: str
    status: str = "pending"
    error_message: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str = ""

# Email Templates
EMAIL_TEMPLATES = {
    "ticket_created": {
        "subject": "Service Ticket #{ticket_id} Created - Battwheels",
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; padding: 20px; text-align: center;">
                <h1 style="color: #eee; margin: 0;">Battwheels OS</h1>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h2 style="color: #333;">Service Ticket Created</h2>
                <p>Dear {customer_name},</p>
                <p>Your service ticket has been successfully created.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Ticket ID</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{ticket_id}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Vehicle</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{vehicle_number}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Issue</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{issue_title}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Priority</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{priority}</td></tr>
                </table>
                <p>We will assign a technician shortly and keep you updated.</p>
                <p>Best regards,<br>Battwheels Team</p>
            </div>
            <div style="background: #1a1a2e; padding: 15px; text-align: center; color: #888; font-size: 12px;">
                © 2026 Battwheels Services Pvt Ltd. All rights reserved.
            </div>
        </div>
        """
    },
    "ticket_assigned": {
        "subject": "Technician Assigned - Ticket #{ticket_id}",
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; padding: 20px; text-align: center;">
                <h1 style="color: #eee; margin: 0;">Battwheels OS</h1>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h2 style="color: #333;">Technician Assigned</h2>
                <p>Dear {customer_name},</p>
                <p>A technician has been assigned to your service ticket.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Ticket ID</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{ticket_id}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Technician</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{technician_name}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Contact</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{technician_phone}</td></tr>
                </table>
                <p>The technician will contact you shortly to schedule the service.</p>
                <p>Best regards,<br>Battwheels Team</p>
            </div>
        </div>
        """
    },
    "estimate_shared": {
        "subject": "Service Estimate Ready - Ticket #{ticket_id}",
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; padding: 20px; text-align: center;">
                <h1 style="color: #eee; margin: 0;">Battwheels OS</h1>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h2 style="color: #333;">Service Estimate Ready</h2>
                <p>Dear {customer_name},</p>
                <p>The service estimate for your vehicle is ready for review.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Ticket ID</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{ticket_id}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Vehicle</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{vehicle_number}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Estimated Cost</strong></td><td style="padding: 10px; border: 1px solid #ddd;">₹{estimated_cost}</td></tr>
                </table>
                <p>Please review and approve the estimate to proceed with repairs.</p>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{approve_url}" style="background: #22c55e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-right: 10px;">Approve Estimate</a>
                </div>
                <p>Best regards,<br>Battwheels Team</p>
            </div>
        </div>
        """
    },
    "invoice_generated": {
        "subject": "Invoice #{invoice_number} - Battwheels Services",
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; padding: 20px; text-align: center;">
                <h1 style="color: #eee; margin: 0;">Battwheels OS</h1>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h2 style="color: #333;">Invoice Generated</h2>
                <p>Dear {customer_name},</p>
                <p>Your invoice for the recent service has been generated.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Invoice Number</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{invoice_number}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Vehicle</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{vehicle_number}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Amount</strong></td><td style="padding: 10px; border: 1px solid #ddd;">₹{total_amount}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Due Date</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{due_date}</td></tr>
                </table>
                <p>Please find the invoice attached or download it using the link below:</p>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{invoice_url}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Download Invoice</a>
                </div>
                <p>Best regards,<br>Battwheels Team</p>
            </div>
        </div>
        """
    },
    "ticket_resolved": {
        "subject": "Service Completed - Ticket #{ticket_id}",
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; padding: 20px; text-align: center;">
                <h1 style="color: #eee; margin: 0;">Battwheels OS</h1>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h2 style="color: #22c55e;">Service Completed ✓</h2>
                <p>Dear {customer_name},</p>
                <p>Great news! The service on your vehicle has been completed.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Ticket ID</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{ticket_id}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Vehicle</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{vehicle_number}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Resolution</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{resolution}</td></tr>
                </table>
                <p>Your vehicle is ready for pickup. Please collect it at your earliest convenience.</p>
                <p>Best regards,<br>Battwheels Team</p>
            </div>
        </div>
        """
    }
}

# WhatsApp Templates
WHATSAPP_TEMPLATES = {
    "ticket_created": "🔧 *Battwheels Service*\n\nHi {customer_name},\n\nYour service ticket #{ticket_id} has been created.\n\nVehicle: {vehicle_number}\nIssue: {issue_title}\n\nWe'll assign a technician shortly.",
    "ticket_assigned": "👨‍🔧 *Technician Assigned*\n\nHi {customer_name},\n\nTechnician {technician_name} has been assigned to your ticket #{ticket_id}.\n\nContact: {technician_phone}\n\nThey will reach out shortly.",
    "estimate_shared": "💰 *Estimate Ready*\n\nHi {customer_name},\n\nYour service estimate for ticket #{ticket_id} is ready.\n\nEstimated Cost: ₹{estimated_cost}\n\nReply APPROVE to confirm.",
    "invoice_generated": "🧾 *Invoice Generated*\n\nHi {customer_name},\n\nInvoice {invoice_number} for ₹{total_amount} has been generated.\n\nDue: {due_date}\n\nPay via UPI: battwheels@kotak",
    "ticket_resolved": "✅ *Service Completed*\n\nHi {customer_name},\n\nYour vehicle {vehicle_number} service is complete!\n\nTicket: #{ticket_id}\n\nReady for pickup. Thank you!"
}

async def send_email_async(recipient_email: str, subject: str, html_content: str) -> dict:
    """Send email using Resend API"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email")
        return {"status": "skipped", "reason": "API key not configured"}
    
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        
        params = {
            "from": SENDER_EMAIL,
            "to": [recipient_email],
            "subject": subject,
            "html": html_content
        }
        
        # Run sync SDK in thread to keep FastAPI non-blocking
        email = await asyncio.to_thread(resend.Emails.send, params)
        return {"status": "sent", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {"status": "failed", "error": str(e)}

async def send_whatsapp_async(phone_number: str, message: str) -> dict:
    """Send WhatsApp message using Twilio"""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured, skipping WhatsApp")
        return {"status": "skipped", "reason": "Twilio not configured"}
    
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Format phone number for WhatsApp
        if not phone_number.startswith("whatsapp:"):
            phone_number = f"whatsapp:{phone_number}"
        
        def send_message():
            return client.messages.create(
                body=message,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=phone_number
            )
        
        msg = await asyncio.to_thread(send_message)
        return {"status": "sent", "message_sid": msg.sid}
    except Exception as e:
        logger.error(f"Failed to send WhatsApp: {str(e)}")
        return {"status": "failed", "error": str(e)}

async def log_notification(channel: str, recipient: str, template: str, status: str, error: str = None, org_id: str = None):
    """Log notification to database"""
    log = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "organization_id": org_id,  # P1-03 FIX: org_id scoped — Sprint 1B
        "channel": channel,
        "recipient": recipient,
        "template": template,
        "status": status,
        "error_message": error,
        "sent_at": datetime.now(timezone.utc).isoformat() if status == "sent" else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notification_logs.insert_one(log)
    return log

# Routes
@router.post("/send-email")
async def send_email(request: EmailRequest, background_tasks: BackgroundTasks, req: Request = None):
    """Send email notification"""
    template = EMAIL_TEMPLATES.get(request.template)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown template: {request.template}")
    
    # P1-03 FIX: extract org_id from request context — Sprint 1B
    org_id = getattr(getattr(req, "state", None), "tenant_org_id", None) if req else None
    
    # Format subject and content
    subject = template["subject"].format(**request.context)
    html = template["html"].format(**request.context)
    
    # Send in background
    async def send_and_log():
        result = await send_email_async(request.recipient_email, subject, html)
        await log_notification(
            channel="email",
            recipient=request.recipient_email,
            template=request.template,
            status=result.get("status", "unknown"),
            error=result.get("error"),
            org_id=org_id
        )
    
    background_tasks.add_task(send_and_log)
    
    return {"status": "queued", "recipient": request.recipient_email, "template": request.template}

@router.post("/send-whatsapp")
async def send_whatsapp(request: WhatsAppRequest, background_tasks: BackgroundTasks, req: Request = None):
    """Send WhatsApp notification"""
    template = WHATSAPP_TEMPLATES.get(request.template)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown template: {request.template}")
    
    # P1-03 FIX: extract org_id from request context — Sprint 1B
    org_id = getattr(getattr(req, "state", None), "tenant_org_id", None) if req else None
    
    # Format message
    message = template.format(**request.context)
    
    # Send in background
    async def send_and_log():
        result = await send_whatsapp_async(request.phone_number, message)
        await log_notification(
            channel="whatsapp",
            recipient=request.phone_number,
            template=request.template,
            status=result.get("status", "unknown"),
            error=result.get("error"),
            org_id=org_id
        )
    
    background_tasks.add_task(send_and_log)
    
    return {"status": "queued", "recipient": request.phone_number, "template": request.template}

@router.post("/ticket-notification/{ticket_id}")
async def send_ticket_notification(
    ticket_id: str, 
    notification_type: str, 
    background_tasks: BackgroundTasks,
    req: Request = None
):
    """Send notification for ticket events"""
    # P1-03 FIX: extract org_id from request context — Sprint 1B
    org_id = getattr(getattr(req, "state", None), "tenant_org_id", None) if req else None
    
    # P1-03 FIX: scope ticket lookup by org_id — Sprint 1B
    ticket_query = {"ticket_id": ticket_id}
    if org_id:
        ticket_query["organization_id"] = org_id
    ticket = await db.tickets.find_one(ticket_query, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Build context
    context = {
        "ticket_id": ticket_id,
        "customer_name": ticket.get("customer_name", "Customer"),
        "vehicle_number": ticket.get("vehicle_number", "N/A"),
        "issue_title": ticket.get("title", "Service Request"),
        "priority": ticket.get("priority", "medium"),
        "technician_name": ticket.get("assigned_technician_name", ""),
        "technician_phone": "",
        "estimated_cost": ticket.get("estimated_cost", 0),
        "resolution": ticket.get("resolution", "Completed"),
        "approve_url": f"https://battwheels.com/approve/{ticket_id}"
    }
    
    # Get customer contact
    customer_email = ticket.get("customer_email")
    customer_phone = ticket.get("contact_number")
    
    results = []
    
    # Send email if available
    if customer_email:
        email_req = EmailRequest(
            recipient_email=customer_email,
            template=notification_type,
            context=context
        )
        result = await send_email(email_req, background_tasks)
        results.append({"channel": "email", **result})
    
    # Send WhatsApp if phone available
    if customer_phone:
        wa_req = WhatsAppRequest(
            phone_number=customer_phone,
            template=notification_type,
            context=context
        )
        result = await send_whatsapp(wa_req, background_tasks)
        results.append({"channel": "whatsapp", **result})
    
    return {"ticket_id": ticket_id, "notifications": results}

@router.get("/logs")
async def get_notification_logs(
    channel: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get notification logs"""
    query = {}
    if channel:
        query["channel"] = channel
    if status:
        query["status"] = status
    
    logs = await db.notification_logs.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return logs

@router.get("/stats")
async def get_notification_stats():
    """Get notification statistics"""
    pipeline = [
        {"$group": {
            "_id": {"channel": "$channel", "status": "$status"},
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": "$_id.channel",
            "stats": {
                "$push": {
                    "status": "$_id.status",
                    "count": "$count"
                }
            },
            "total": {"$sum": "$count"}
        }}
    ]
    
    result = await db.notification_logs.aggregate(pipeline).to_list(100)
    return result
