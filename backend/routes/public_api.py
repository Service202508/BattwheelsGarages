"""
Battwheels OS - Public API Routes (extracted from server.py)
Contact form, Book demo (no auth required)
"""
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Public"])
db = None

def init_router(database):
    global db
    db = database

class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    type: str = "general"
    message: str


@router.post("/contact", tags=["Public"])
async def submit_contact_form(data: ContactFormRequest):
    """
    Public contact form submission.
    Sends the enquiry to hello@battwheels.com and a confirmation to the submitter.
    No auth required.
    """
    from services.email_service import EmailService

    type_labels = {
        "general": "General Enquiry",
        "enterprise": "Enterprise / OEM Partnership",
        "demo": "Book a Demo",
        "support": "Technical Support",
        "billing": "Billing Question",
        "security": "Security Report",
    }
    type_label = type_labels.get(data.type, data.type.replace("_", " ").title())
    company_line = f"<p><strong>Company:</strong> {data.company}</p>" if data.company else ""

    # Email to hello@battwheels.com (internal notification)
    internal_html = f"""
    <div style="font-family:monospace;background:#080C0F;color:#F4F6F0;padding:32px;border-radius:8px;max-width:560px">
      <div style="display:inline-block;background:#C8FF00;color:#080C0F;padding:4px 10px;font-size:11px;
                  font-weight:700;letter-spacing:0.15em;text-transform:uppercase;border-radius:3px;margin-bottom:24px">
        New Contact Form Submission
      </div>
      <h2 style="margin:0 0 4px;color:#F4F6F0;font-size:18px">{data.name}</h2>
      <p style="margin:0 0 20px;color:#9ca3af;font-size:13px">{data.email}</p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
        <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px;width:120px">Type</td>
            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#C8FF00;font-size:12px">{type_label}</td></tr>
        {"<tr><td style='padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px'>Company</td><td style='padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);font-size:12px'>" + (data.company or "") + "</td></tr>" if data.company else ""}
        <tr><td style="padding:8px 0;color:#9ca3af;font-size:12px;vertical-align:top">Message</td>
            <td style="padding:8px 0;font-size:13px;line-height:1.6">{data.message}</td></tr>
      </table>
      <p style="color:#6b7280;font-size:11px;margin:0">Submitted via battwheels.com/contact</p>
    </div>
    """

    # Confirmation email to the submitter
    confirm_html = f"""
    <div style="font-family:sans-serif;background:#080C0F;color:#F4F6F0;padding:32px;border-radius:8px;max-width:520px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:28px">
        <div style="width:28px;height:28px;background:#C8FF00;border-radius:4px;display:flex;align-items:center;justify-content:center">
          <span style="font-size:16px;font-weight:900;color:#080C0F">⚡</span>
        </div>
        <span style="font-size:17px;font-weight:800;letter-spacing:-0.5px">Battwheels OS</span>
      </div>
      <h2 style="margin:0 0 8px;font-size:20px;font-weight:800">We got your message, {data.name.split()[0]}.</h2>
      <p style="color:#9ca3af;font-size:14px;line-height:1.6;margin:0 0 20px">
        Thanks for reaching out. We'll get back to you at <strong style="color:#C8FF00">{data.email}</strong> 
        within 48 hours (Mon–Sat, 9 AM–6 PM IST).
      </p>
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:16px;margin-bottom:24px">
        <p style="margin:0 0 6px;font-size:11px;font-family:monospace;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em">Your message</p>
        <p style="margin:0;font-size:13px;color:#d1d5db;line-height:1.6">{data.message[:300]}{"..." if len(data.message) > 300 else ""}</p>
      </div>
      <p style="color:#6b7280;font-size:12px;margin:0">
        While you wait — <a href="https://battwheels.com/register" style="color:#C8FF00">start a free 14-day trial</a> 
        and explore the platform yourself. No credit card required.
      </p>
    </div>
    """

    # Fire both emails concurrently
    import asyncio as _asyncio
    results = await _asyncio.gather(
        EmailService.send_email(
            to="hello@battwheels.com",
            subject=f"[{type_label}] {data.name} — {data.email}",
            html_content=internal_html,
            reply_to=data.email,
        ),
        EmailService.send_email(
            to=data.email,
            subject="We received your message — Battwheels OS",
            html_content=confirm_html,
        ),
        return_exceptions=True
    )

    # Log any email failures but still return success (don't surface Resend errors to user)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Contact form email {i} failed: {result}")

    # Store in DB for reference
    await db.contact_submissions.insert_one({
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "type": data.type,
        "message": data.message,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"status": "ok", "message": "Message received. We'll be in touch within 48 hours."}


# ==================== BOOK DEMO ====================

class BookDemoRequest(BaseModel):
    name: str
    workshop_name: str
    city: str
    phone: str
    vehicles_per_month: str  # "<10" | "10-50" | "50-200" | "200+"


@router.post("/book-demo", tags=["Public"])
async def book_demo(data: BookDemoRequest):
    """
    Pre-sales demo request — no auth required.
    Stores lead in demo_requests collection and notifies sales@battwheels.com.
    """
    from services.email_service import EmailService
    import uuid as _uuid

    now_str = datetime.now(timezone.utc).isoformat()
    lead_id = f"demo_{_uuid.uuid4().hex[:10]}"

    # Internal notification to sales team
    sales_html = f"""
    <div style="font-family:monospace;background:#080C0F;color:#F4F6F0;padding:32px;border-radius:8px;max-width:560px">
      <div style="display:inline-block;background:#C8FF00;color:#080C0F;padding:4px 10px;font-size:11px;
                  font-weight:700;letter-spacing:0.15em;text-transform:uppercase;border-radius:3px;margin-bottom:24px">
        New Demo Request — {lead_id}
      </div>
      <h2 style="margin:0 0 4px;color:#F4F6F0;font-size:18px">{data.name}</h2>
      <p style="margin:0 0 20px;color:#9ca3af;font-size:13px">{data.phone} · {data.city}</p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
        <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px;width:180px">Workshop</td>
            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#C8FF00;font-size:12px">{data.workshop_name}</td></tr>
        <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);color:#9ca3af;font-size:12px">City</td>
            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);font-size:12px">{data.city}</td></tr>
        <tr><td style="padding:8px 0;color:#9ca3af;font-size:12px">Fleet size</td>
            <td style="padding:8px 0;font-size:12px">{data.vehicles_per_month} vehicles/month</td></tr>
      </table>
      <p style="color:#6b7280;font-size:11px;margin:0">Target SLA: call within 1 business day</p>
    </div>
    """

    result = await EmailService.send_email(
        to="sales@battwheels.com",
        subject=f"[Demo Request] {data.workshop_name} — {data.city} ({data.vehicles_per_month} vehicles/mo)",
        html_content=sales_html,
    )
    if isinstance(result, Exception):
        logger.warning(f"Demo request email failed: {result}")

    await db.demo_requests.insert_one({
        "lead_id": lead_id,
        "name": data.name,
        "workshop_name": data.workshop_name,
        "city": data.city,
        "phone": data.phone,
        "vehicles_per_month": data.vehicles_per_month,
        "status": "new",
        "submitted_at": now_str,
    })

    return {
        "status": "ok",
        "lead_id": lead_id,
        "message": "We'll call you within 1 business day."
    }
