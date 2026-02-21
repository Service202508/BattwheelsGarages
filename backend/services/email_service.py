"""
Email Service for Battwheels OS
================================

Handles transactional emails using Resend API:
- Team invitation emails
- Notification emails
- Password reset emails
"""

import os
import asyncio
import logging
from typing import Optional

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
    def _get_base_template(content: str) -> str:
        """Wrap content in base email template"""
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
                                <td style="padding: 20px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px 12px 0 0;">
                                    <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 600;">⚡ {APP_NAME}</h1>
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
                                <td style="padding: 20px; text-align: center; background-color: #f9fafb; border-radius: 0 0 12px 12px;">
                                    <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                        © 2026 Battwheels Services Private Limited. All rights reserved.
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
    async def send_email(
        to: str,
        subject: str,
        html_content: str
    ) -> dict:
        """Send an email using Resend"""
        if not EMAIL_ENABLED:
            logger.info(f"[EMAIL MOCK] To: {to}, Subject: {subject}")
            return {"status": "mocked", "message": f"Email logged (Resend not configured): {to}"}
        
        params = {
            "from": f"{APP_NAME} <{SENDER_EMAIL}>",
            "to": [to],
            "subject": subject,
            "html": html_content
        }
        
        try:
            email = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Email sent to {to}: {email.get('id')}")
            return {"status": "success", "email_id": email.get("id")}
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
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


# Singleton instance
email_service = EmailService()
