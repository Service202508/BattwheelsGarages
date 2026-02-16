"""
Razorpay Payment Service
Handles payment link creation, order management, and webhook processing
"""
import razorpay
import os
import hmac
import hashlib
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Initialize Razorpay client (will use test keys if not configured)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')

def get_razorpay_client():
    """Get Razorpay client instance"""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return None
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def is_razorpay_configured():
    """Check if Razorpay is properly configured"""
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

async def create_razorpay_order(amount_inr: float, receipt: str, notes: dict = None) -> dict:
    """
    Create a Razorpay order
    
    Args:
        amount_inr: Amount in INR (rupees, not paise)
        receipt: Receipt ID (e.g., invoice number)
        notes: Additional notes
    
    Returns:
        Razorpay order object or mock order if not configured
    """
    # Convert to paise (Razorpay uses paise)
    amount_paise = int(amount_inr * 100)
    
    client = get_razorpay_client()
    
    if not client:
        # Return mock order for testing when keys not configured
        return {
            "id": f"order_MOCK_{receipt}",
            "amount": amount_paise,
            "amount_paid": 0,
            "amount_due": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "status": "created",
            "notes": notes or {},
            "created_at": int(datetime.now(timezone.utc).timestamp()),
            "_mock": True,
            "_message": "Razorpay not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env"
        }
    
    try:
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {},
            "payment_capture": 1  # Auto-capture payment
        })
        return order
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise


async def create_payment_link(
    amount_inr: float,
    description: str,
    customer_name: str,
    customer_email: str = "",
    customer_phone: str = "",
    reference_id: str = "",
    expire_by: int = None,
    callback_url: str = "",
    callback_method: str = "get"
) -> dict:
    """
    Create a Razorpay payment link
    
    Args:
        amount_inr: Amount in INR
        description: Payment description
        customer_name: Customer name
        customer_email: Customer email
        customer_phone: Customer phone
        reference_id: Reference ID (e.g., invoice ID)
        expire_by: Unix timestamp for link expiry
        callback_url: URL to redirect after payment
        callback_method: HTTP method for callback
    
    Returns:
        Payment link object
    """
    amount_paise = int(amount_inr * 100)
    
    client = get_razorpay_client()
    
    if not client:
        # Return mock payment link
        mock_link_id = f"plink_MOCK_{reference_id}"
        return {
            "id": mock_link_id,
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone
            },
            "reference_id": reference_id,
            "short_url": f"https://rzp.io/l/{mock_link_id}",
            "status": "created",
            "created_at": int(datetime.now(timezone.utc).timestamp()),
            "_mock": True,
            "_message": "Razorpay not configured. This is a mock payment link."
        }
    
    try:
        payment_link_data = {
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone
            },
            "notify": {
                "sms": bool(customer_phone),
                "email": bool(customer_email)
            },
            "reference_id": reference_id
        }
        
        if expire_by:
            payment_link_data["expire_by"] = expire_by
        
        if callback_url:
            payment_link_data["callback_url"] = callback_url
            payment_link_data["callback_method"] = callback_method
        
        payment_link = client.payment_link.create(payment_link_data)
        return payment_link
    except Exception as e:
        logger.error(f"Razorpay payment link creation failed: {e}")
        raise


async def fetch_payment(payment_id: str) -> dict:
    """Fetch payment details from Razorpay"""
    client = get_razorpay_client()
    
    if not client:
        return {
            "id": payment_id,
            "status": "mock",
            "_mock": True,
            "_message": "Razorpay not configured"
        }
    
    try:
        return client.payment.fetch(payment_id)
    except Exception as e:
        logger.error(f"Failed to fetch payment {payment_id}: {e}")
        raise


async def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verify Razorpay payment signature
    
    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Signature from Razorpay response
    
    Returns:
        True if signature is valid
    """
    client = get_razorpay_client()
    
    if not client:
        # For mock payments, always return True
        return True
    
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify Razorpay webhook signature
    
    Args:
        body: Raw request body
        signature: X-Razorpay-Signature header value
    
    Returns:
        True if signature is valid
    """
    if not RAZORPAY_WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured, skipping verification")
        return True
    
    expected_signature = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


async def capture_payment(payment_id: str, amount_paise: int) -> dict:
    """Capture an authorized payment"""
    client = get_razorpay_client()
    
    if not client:
        return {"id": payment_id, "status": "captured", "_mock": True}
    
    try:
        return client.payment.capture(payment_id, amount_paise)
    except Exception as e:
        logger.error(f"Failed to capture payment {payment_id}: {e}")
        raise


async def refund_payment(payment_id: str, amount_paise: int = None, notes: dict = None) -> dict:
    """
    Refund a payment (full or partial)
    
    Args:
        payment_id: Payment ID to refund
        amount_paise: Amount to refund in paise (None for full refund)
        notes: Refund notes
    
    Returns:
        Refund object
    """
    client = get_razorpay_client()
    
    if not client:
        return {
            "id": f"rfnd_MOCK_{payment_id}",
            "payment_id": payment_id,
            "amount": amount_paise,
            "status": "processed",
            "_mock": True
        }
    
    try:
        refund_data = {}
        if amount_paise:
            refund_data["amount"] = amount_paise
        if notes:
            refund_data["notes"] = notes
        
        return client.payment.refund(payment_id, refund_data)
    except Exception as e:
        logger.error(f"Failed to refund payment {payment_id}: {e}")
        raise
