"""
Email Service for Battwheels OS
================================

Handles transactional emails using Resend API:
- Team invitation emails
- Notification emails
- Password reset emails
- Invoice emails with PDF attachments
"""

import os
import asyncio
import logging
import base64
from typing import Optional, List

logger = logging.getLogger(__name__)

# Check if Resend is available
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend not installed. Email notifications will be logged only.")

# Configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
APP_NAME = "Battwheels OS"
APP_URL = os.environ.get("APP_URL", "https://battwheels.com")

# Initialize Resend
if RESEND_AVAILABLE and RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
    EMAIL_ENABLED = True
    logger.info("Resend email service initialized")
else:
    EMAIL_ENABLED = False
    logger.info("Email service disabled (no API key or Resend not installed)")


class EmailService:
    """Service for sending transactional emails"""
    
    @staticmethod
    def _get_base_template(content: str, org_name: str = None, org_logo_url: str = None) -> str:
        """Wrap content in base email template"""
        if org_logo_url:
            header_html = f"""
                <td style="padding: 20px; text-align: center; background-color: #080C0F; border-radius: 12px 12px 0 0;">
                    <img src="{org_logo_url}" alt="{org_name or APP_NAME}" height="40" style="max-height:40px; max-width:160px; margin-bottom:10px; display:block; margin-left:auto; margin-right:auto;">
                    <p style="margin:0; color:rgba(244,246,240,0.45); font-size:12px;">{APP_NAME}</p>
                </td>"""
        elif org_name:
            header_html = f"""
                <td style="padding: 20px; text-align: center; background-color: #080C0F; border-radius: 12px 12px 0 0;">
                    <div style="font-size:20px; font-weight:700; color:#C8FF00;">{org_name}</div>
                    <p style="margin:4px 0 0; color:rgba(244,246,240,0.45); font-size:12px;">{APP_NAME}</p>
                </td>"""
        else:
            header_html = f"""
                <td style="padding: 20px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px 12px 0 0;">
                    <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 600;">{APP_NAME}</h1>
                </td>"""

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse;">
                            <!-- Header -->
                            <tr>
                                {header_html}
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px; background-color: white;">
                                    {content}
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 20px; text-align: center; background-color: #f9fafb; border-radius: 0 0 12px 12px;">
                                    <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                        &copy; 2026 Battwheels Services Private Limited. All rights reserved.
                                    </p>
                                    <p style="margin: 8px 0 0; color: #9ca3af; font-size: 11px;">
                                        This email was sent by {APP_NAME}. If you didn't expect this email, you can ignore it.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_invoice_template(content: str, org_name: str, org_logo_url: str = None) -> str:
        """Invoice-specific email template with dark header"""
        logo_html = ""
        if org_logo_url:
            logo_html = f'<img src="{org_logo_url}" alt="{org_name}" style="max-height: 50px; max-width: 150px; margin-bottom: 10px;" />'
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse;">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 24px; text-align: center; background-color: #080C0F; border-radius: 12px 12px 0 0;">
                                    {logo_html}
                                    <h1 style="margin: 0; color: #C8FF00; font-size: 24px; font-weight: 600;">{org_name}</h1>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px; background-color: white;">
                                    {content}
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 20px; text-align: center; background-color: #080C0F; border-radius: 0 0 12px 12px;">
                                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                        This is a system generated email from {APP_NAME}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    async def send_email(
        to: str,
        subject: str,
        html_content: str,
        attachments: List[dict] = None,
        cc: List[str] = None,
        reply_to: str = None,
        org_id: str = None
    ) -> dict:
        """Send an email using Resend with optional per-org credentials"""
        # Resolve credentials — per-org if available, else global
        from_email = SENDER_EMAIL
        from_name = APP_NAME
        api_key_to_use = RESEND_API_KEY
        
        if org_id:
            try:
                from services.credential_service import get_email_credentials
                creds = await get_email_credentials(org_id)
                if creds.get("api_key"):
                    api_key_to_use = creds["api_key"]
                if creds.get("from_email"):
                    from_email = creds["from_email"]
                if creds.get("from_name"):
                    from_name = creds["from_name"]
            except Exception as e:
                logger.warning(f"Could not load org email creds for {org_id}: {e}")

        if not RESEND_AVAILABLE or not api_key_to_use:
            logger.info(f"[EMAIL MOCK] To: {to}, Subject: {subject}, Attachments: {len(attachments) if attachments else 0}")
            return {"status": "mocked", "message": f"Email logged (Resend not configured): {to}"}
        
        import resend as _resend
        _resend.api_key = api_key_to_use
        
        params = {
            "from": f"{from_name} <{from_email}>",
            "to": [to],
            "subject": subject,
            "html": html_content
        }
        
        if cc:
            params["cc"] = cc
        
        if reply_to:
            params["reply_to"] = reply_to
        
        if attachments:
            params["attachments"] = attachments
        
        try:
            email = await asyncio.to_thread(_resend.Emails.send, params)
            logger.info(f"Email sent to {to}: {email.get('id')}")
            return {"status": "success", "email_id": email.get("id")}
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def send_invoice_email(
        cls,
        to_email: str,
        customer_name: str,
        invoice_number: str,
        invoice_date: str,
        due_date: str,
        amount: float,
        tax_amount: float,
        total: float,
        org_name: str,
        org_address: str = "",
        org_gstin: str = "",
        org_logo_url: str = None,
        org_email: str = None,
        irn: str = None,
        irn_ack_no: str = None,
        payment_link: str = None,
        pdf_content: bytes = None,
        pdf_filename: str = None
    ) -> dict:
        """
        Send invoice email with PDF attachment (5B)
        """
        # Format currency
        def fmt(amt): return f"₹{amt:,.2f}"
        
        # IRN block (if B2B with IRN)
        irn_html = ""
        if irn:
            irn_display = f"{irn[:20]}...{irn[-8:]}" if len(irn) > 28 else irn
            irn_html = f"""
            <div style="margin: 20px 0; padding: 16px; background-color: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px;">
                <p style="margin: 0; color: #166534; font-size: 14px;">
                    <strong>✓ E-Invoice Registered</strong><br>
                    <span style="font-family: monospace; font-size: 12px;">IRN: {irn_display}</span><br>
                    <span style="font-size: 12px;">Ack No: {irn_ack_no or 'N/A'}</span>
                </p>
            </div>
            """
        
        # Pay Now button (if Razorpay configured)
        pay_button_html = ""
        if payment_link:
            pay_button_html = f"""
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 24px 0;">
                        <a href="{payment_link}" style="display: inline-block; padding: 16px 40px; background-color: #C8FF00; color: #080C0F; text-decoration: none; font-size: 16px; font-weight: 700; border-radius: 8px;">
                            Pay {fmt(total)} Online →
                        </a>
                    </td>
                </tr>
            </table>
            """
        
        # Build email content
        content = f"""
        <p style="margin: 0 0 20px; color: #111827; font-size: 16px;">Dear {customer_name},</p>
        
        <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            Please find attached your invoice <strong>{invoice_number}</strong> dated {invoice_date} 
            for <strong>{fmt(total)}</strong> due on <strong>{due_date}</strong>.
        </p>
        
        <!-- Invoice Summary Table -->
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
            <tr style="background-color: #f9fafb;">
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">Invoice Number</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #111827; font-size: 14px; font-weight: 600; text-align: right;">{invoice_number}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">Invoice Date</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #111827; font-size: 14px; text-align: right;">{invoice_date}</td>
            </tr>
            <tr style="background-color: #f9fafb;">
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">Due Date</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #111827; font-size: 14px; text-align: right;">{due_date}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">Amount Due</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #C8FF00; background-color: #080C0F; font-size: 14px; font-weight: 700; text-align: right;">{fmt(amount)}</td>
            </tr>
            <tr style="background-color: #f9fafb;">
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">GST Amount</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #111827; font-size: 14px; text-align: right;">{fmt(tax_amount)}</td>
            </tr>
            <tr>
                <td style="padding: 16px; color: #111827; font-size: 16px; font-weight: 600;">Total</td>
                <td style="padding: 16px; color: #111827; font-size: 20px; font-weight: 700; text-align: right;">{fmt(total)}</td>
            </tr>
        </table>
        
        {irn_html}
        
        {pay_button_html}
        
        <!-- Organization Details -->
        <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0; color: #111827; font-size: 14px; font-weight: 600;">{org_name}</p>
            <p style="margin: 4px 0 0; color: #6b7280; font-size: 12px;">{org_address}</p>
            {f'<p style="margin: 4px 0 0; color: #6b7280; font-size: 12px;">GSTIN: {org_gstin}</p>' if org_gstin else ''}
        </div>
        """
        
        html = cls._get_invoice_template(content, org_name, org_logo_url)
        
        # Prepare attachments
        attachments = None
        if pdf_content and pdf_filename:
            attachments = [{
                "filename": pdf_filename,
                "content": base64.b64encode(pdf_content).decode("utf-8")
            }]
        
        return await cls.send_email(
            to=to_email,
            subject=f"Invoice {invoice_number} from {org_name} — {fmt(total)}",
            html_content=html,
            attachments=attachments,
            cc=[org_email] if org_email else None,
            reply_to=org_email
        )
    
    @classmethod
    async def send_invitation_email(
        cls,
        to_email: str,
        to_name: str,
        org_name: str,
        inviter_name: str,
        role: str,
        invite_link: str
    ) -> dict:
        """Send team invitation email"""
        full_link = f"{APP_URL}{invite_link}"
        
        content = f"""
        <h2 style="margin: 0 0 20px; color: #111827; font-size: 20px;">You're invited to join {org_name}!</h2>
        <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            Hi {to_name},
        </p>
        <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            <strong>{inviter_name}</strong> has invited you to join <strong>{org_name}</strong> on {APP_NAME} as a <strong>{role}</strong>.
        </p>
        <p style="margin: 0 0 24px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            {APP_NAME} is a complete ERP platform for EV workshops with AI-powered diagnostics, invoicing, inventory management, and more.
        </p>
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <a href="{full_link}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                        Accept Invitation
                    </a>
                </td>
            </tr>
        </table>
        <p style="margin: 24px 0 0; color: #9ca3af; font-size: 14px; text-align: center;">
            This invitation expires in 7 days. If the button doesn't work, copy this link:<br>
            <a href="{full_link}" style="color: #10b981; word-break: break-all;">{full_link}</a>
        </p>
        """
        
        html = cls._get_base_template(content)
        return await cls.send_email(
            to=to_email,
            subject=f"You're invited to join {org_name} on {APP_NAME}",
            html_content=html
        )
    
    @classmethod
    async def send_welcome_email(
        cls,
        to_email: str,
        to_name: str,
        org_name: str
    ) -> dict:
        """Send welcome email after organization signup"""
        content = f"""
        <h2 style="margin: 0 0 20px; color: #111827; font-size: 20px;">Welcome to {APP_NAME}! 🎉</h2>
        <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            Hi {to_name},
        </p>
        <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            Congratulations! Your organization <strong>{org_name}</strong> has been successfully created on {APP_NAME}.
        </p>
        <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            You're now on a <strong>14-day free trial</strong> of our Starter plan. Here's what you can do next:
        </p>
        <ul style="margin: 0 0 24px; padding-left: 24px; color: #4b5563; font-size: 16px; line-height: 1.8;">
            <li>Set up your organization profile</li>
            <li>Invite your team members</li>
            <li>Create your first service ticket</li>
            <li>Explore AI-powered diagnostics</li>
        </ul>
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <a href="{APP_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                        Go to Dashboard
                    </a>
                </td>
            </tr>
        </table>
        <p style="margin: 24px 0 0; color: #6b7280; font-size: 14px;">
            Need help getting started? Check out our <a href="{APP_URL}/help" style="color: #10b981;">Help Center</a> or reply to this email.
        </p>
        """
        
        html = cls._get_base_template(content)
        return await cls.send_email(
            to=to_email,
            subject=f"Welcome to {APP_NAME} - Your trial has started!",
            html_content=html
        )
    
    @classmethod
    async def send_password_reset_email(
        cls,
        to_email: str,
        to_name: str,
        reset_link: str
    ) -> dict:
        """Send password reset email"""
        full_link = f"{APP_URL}{reset_link}"
        
        content = f"""
        <h2 style="margin: 0 0 20px; color: #111827; font-size: 20px;">Reset Your Password</h2>
        <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            Hi {to_name},
        </p>
        <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.6;">
            We received a request to reset your password. Click the button below to create a new password:
        </p>
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <a href="{full_link}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                        Reset Password
                    </a>
                </td>
            </tr>
        </table>
        <p style="margin: 24px 0 0; color: #9ca3af; font-size: 14px;">
            This link expires in 1 hour. If you didn't request a password reset, you can ignore this email.
        </p>
        """
        
        html = cls._get_base_template(content)
        return await cls.send_email(
            to=to_email,
            subject=f"Reset your {APP_NAME} password",
            html_content=html
        )


    @classmethod
    async def send_generic_email(
        cls,
        to_email: str,
        subject: str,
        body: str,
        org_name: str = None,
        org_logo_url: str = None,
    ) -> dict:
        """
        Send a simple text/HTML email.
        body: plain text; will be wrapped in HTML template.
        """
        content_html = "".join(
            f'<p style="margin: 0 0 12px; color: #374151; font-size: 15px; line-height: 1.6;">{line}</p>'
            for line in body.splitlines()
            if line.strip()
        )
        html = cls._get_base_template(content_html, org_name=org_name, org_logo_url=org_logo_url)
        return await cls.send_email(
            to=to_email,
            subject=subject,
            html_content=html,
        )


# Singleton instance
email_service = EmailService()
