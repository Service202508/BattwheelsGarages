import os
import logging
from typing import Dict, Any
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service using SMTP (Gmail, SendGrid, or any SMTP provider)
    Configure via environment variables for easy switching
    """

    def __init__(self):
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('SMTP_FROM_EMAIL', self.smtp_user)
        self.environment = os.environ.get('ENVIRONMENT', 'development')

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None
    ) -> bool:
        """
        Send an email using SMTP
        In development mode, logs to console instead of sending
        """
        try:
            # Development mode: log to console
            if self.environment == 'development':
                logger.info(f"\n{'='*60}")
                logger.info("📧 EMAIL (DEV MODE - NOT SENT)")
                logger.info(f"To: {to_email}")
                logger.info(f"From: {self.from_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body:\n{text_content or html_content[:200]}...")
                logger.info(f"{'='*60}\n")
                return True

            # Production mode: send actual email
            if not self.smtp_user or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False

            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_email
            message['To'] = to_email

            if text_content:
                part1 = MIMEText(text_content, 'plain')
                message.attach(part1)

            part2 = MIMEText(html_content, 'html')
            message.attach(part2)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True
            )

            logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return False

    async def send_booking_notification(self, booking: Dict[str, Any]) -> bool:
        """
        Send service booking notification to Battwheels team
        """
        subject = f"🚗 New Service Booking - {booking['name']}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #16a34a;">New Service Booking Received</h2>
            
            <h3>Customer Details:</h3>
            <ul>
                <li><strong>Name:</strong> {booking['name']}</li>
                <li><strong>Email:</strong> {booking['email']}</li>
                <li><strong>Phone:</strong> {booking['phone']}</li>
            </ul>
            
            <h3>Vehicle Details:</h3>
            <ul>
                <li><strong>Category:</strong> {booking['vehicle_category']}</li>
                <li><strong>Customer Type:</strong> {booking['customer_type']}</li>
                <li><strong>Brand:</strong> {booking.get('brand', 'N/A')}</li>
                <li><strong>Model:</strong> {booking.get('model', 'N/A')}</li>
            </ul>
            
            <h3>Service Information:</h3>
            <ul>
                <li><strong>Service Needed:</strong> {booking['service_needed']}</li>
                <li><strong>Preferred Date:</strong> {booking['preferred_date']}</li>
                <li><strong>Time Slot:</strong> {booking.get('time_slot', 'N/A')}</li>
            </ul>
            
            <h3>Location:</h3>
            <ul>
                <li><strong>Address:</strong> {booking['address']}</li>
                <li><strong>City:</strong> {booking['city']}</li>
            </ul>
            
            <p style="margin-top: 20px; padding: 10px; background-color: #f0fdf4; border-left: 4px solid #16a34a;">
                Please contact the customer within 2 hours to confirm the booking.
            </p>
        </body>
        </html>
        """

        text_content = f"""
        New Service Booking Received
        
        Customer: {booking['name']}
        Email: {booking['email']}
        Phone: {booking['phone']}
        
        Vehicle: {booking['vehicle_category']} - {booking.get('brand', '')} {booking.get('model', '')}
        Service: {booking['service_needed']}
        Date: {booking['preferred_date']}
        Location: {booking['address']}, {booking['city']}
        """

        return await self.send_email(
            to_email='service@battwheelsgarages.in',
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    async def send_fleet_enquiry_notification(self, enquiry: Dict[str, Any]) -> bool:
        """
        Send fleet/OEM enquiry notification to Battwheels team
        """
        subject = f"🚛 New Fleet Enquiry - {enquiry['company_name']}"

        total_vehicles = (
            enquiry.get('vehicle_count_2w', 0) +
            enquiry.get('vehicle_count_3w', 0) +
            enquiry.get('vehicle_count_4w', 0) +
            enquiry.get('vehicle_count_commercial', 0)
        )

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #16a34a;">New Fleet/OEM Enquiry</h2>
            
            <h3>Company Details:</h3>
            <ul>
                <li><strong>Company:</strong> {enquiry['company_name']}</li>
                <li><strong>Contact Person:</strong> {enquiry['contact_person']}</li>
                <li><strong>Role:</strong> {enquiry['role']}</li>
                <li><strong>Email:</strong> {enquiry['email']}</li>
                <li><strong>Phone:</strong> {enquiry['phone']}</li>
                <li><strong>City:</strong> {enquiry['city']}</li>
            </ul>
            
            <h3>Fleet Size (Total: {total_vehicles} vehicles):</h3>
            <ul>
                <li><strong>2-Wheeler EVs:</strong> {enquiry.get('vehicle_count_2w', 0)}</li>
                <li><strong>3-Wheeler EVs:</strong> {enquiry.get('vehicle_count_3w', 0)}</li>
                <li><strong>4-Wheeler EVs:</strong> {enquiry.get('vehicle_count_4w', 0)}</li>
                <li><strong>Commercial EVs:</strong> {enquiry.get('vehicle_count_commercial', 0)}</li>
            </ul>
            
            <h3>Requirements:</h3>
            <p>{', '.join(enquiry.get('requirements', []))}</p>
            
            <h3>Additional Details:</h3>
            <p>{enquiry.get('details', 'N/A')}</p>
            
            <p style="margin-top: 20px; padding: 10px; background-color: #fef9c3; border-left: 4px solid #eab308;">
                🔥 HIGH PRIORITY: Fleet enquiry with {total_vehicles} vehicles. Contact immediately.
            </p>
        </body>
        </html>
        """

        text_content = f"""
        New Fleet/OEM Enquiry
        
        Company: {enquiry['company_name']}
        Contact: {enquiry['contact_person']} ({enquiry['role']})
        Email: {enquiry['email']}
        Phone: {enquiry['phone']}
        City: {enquiry['city']}
        
        Fleet Size: {total_vehicles} vehicles
        Requirements: {', '.join(enquiry.get('requirements', []))}
        """

        return await self.send_email(
            to_email='service@battwheelsgarages.in',
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    async def send_contact_notification(self, contact: Dict[str, Any]) -> bool:
        """
        Send contact form submission notification
        """
        subject = f"💬 New Contact Message - {contact['name']}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #16a34a;">New Contact Message</h2>
            
            <h3>Contact Details:</h3>
            <ul>
                <li><strong>Name:</strong> {contact['name']}</li>
                <li><strong>Email:</strong> {contact['email']}</li>
                <li><strong>Phone:</strong> {contact.get('phone', 'N/A')}</li>
            </ul>
            
            <h3>Message:</h3>
            <p style="padding: 15px; background-color: #f9fafb; border-radius: 5px;">
                {contact['message']}
            </p>
        </body>
        </html>
        """

        text_content = f"""
        New Contact Message
        
        Name: {contact['name']}
        Email: {contact['email']}
        Phone: {contact.get('phone', 'N/A')}
        
        Message:
        {contact['message']}
        """

        return await self.send_email(
            to_email='service@battwheelsgarages.in',
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


email_service = EmailService()
