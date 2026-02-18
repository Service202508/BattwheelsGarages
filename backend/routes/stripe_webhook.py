"""
Stripe Webhook Handler
Handles payment confirmations and updates from Stripe.
"""

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from emergentintegrations.payments.stripe.checkout import StripeCheckout

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(tags=["Webhooks"])

payment_transactions_collection = db["payment_transactions"]


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    Called by Stripe when payment status changes.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    # Initialize Stripe checkout
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Log the event
        print(f"[STRIPE WEBHOOK] Event: {webhook_response.event_type}, Session: {webhook_response.session_id}, Status: {webhook_response.payment_status}")
        
        # Update transaction if we have the session_id
        if webhook_response.session_id:
            await payment_transactions_collection.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {
                    "payment_status": webhook_response.payment_status,
                    "webhook_event_id": webhook_response.event_id,
                    "webhook_event_type": webhook_response.event_type,
                    "webhook_received_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"status": "ok", "event_id": webhook_response.event_id}
        
    except Exception as e:
        print(f"[STRIPE WEBHOOK ERROR] {str(e)}")
        # Return 200 to acknowledge receipt (Stripe will retry on non-200)
        return {"status": "error", "message": str(e)}
