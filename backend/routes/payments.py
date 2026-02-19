"""
Razorpay Payment Routes
Handles payment order creation, verification, and webhook processing
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import razorpay
import hmac
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Initialize Razorpay client
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None

# Database reference (will be set from server.py)
db = None

def set_database(database):
    global db
    db = database


# Pydantic Models
class OrderItem(BaseModel):
    product_id: str
    name: str
    quantity: int
    price: float
    sku: Optional[str] = None

class CreateOrderRequest(BaseModel):
    amount: float  # Amount in INR (will be converted to paise)
    currency: str = "INR"
    items: List[OrderItem]
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    notes: Optional[dict] = None

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.get("/config")
async def get_payment_config():
    """Get Razorpay public key for frontend"""
    if not RAZORPAY_KEY_ID:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    return {
        "key_id": RAZORPAY_KEY_ID,
        "currency": "INR",
        "name": "Battwheels Garages",
        "description": "EV Parts & Services Marketplace",
        "image": "https://battwheelsgarages.in/assets/battwheels-logo-new.png"
    }


@router.post("/create-order")
async def create_order(order_data: CreateOrderRequest):
    """Create a Razorpay order"""
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    try:
        # Convert amount to paise (Razorpay requires amount in smallest currency unit)
        amount_in_paise = int(order_data.amount * 100)
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": order_data.currency,
            "payment_capture": 1,  # Auto-capture payment
            "notes": {
                "customer_name": order_data.customer_name,
                "customer_email": order_data.customer_email,
                "customer_phone": order_data.customer_phone,
                **(order_data.notes or {})
            }
        })
        
        # Store order in database
        order_doc = {
            "razorpay_order_id": razorpay_order["id"],
            "amount": order_data.amount,
            "amount_paise": amount_in_paise,
            "currency": order_data.currency,
            "status": "created",
            "items": [item.dict() for item in order_data.items],
            "customer": {
                "name": order_data.customer_name,
                "email": order_data.customer_email,
                "phone": order_data.customer_phone,
                "shipping_address": order_data.shipping_address
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        if db:
            await db.marketplace_orders.insert_one(order_doc)
        
        return {
            "order_id": razorpay_order["id"],
            "amount": amount_in_paise,
            "currency": order_data.currency,
            "key_id": RAZORPAY_KEY_ID
        }
        
    except razorpay.errors.BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.post("/verify-payment")
async def verify_payment(payment_data: VerifyPaymentRequest):
    """Verify Razorpay payment signature"""
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    try:
        # Generate signature for verification
        message = f"{payment_data.razorpay_order_id}|{payment_data.razorpay_payment_id}"
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        if generated_signature != payment_data.razorpay_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Update order status in database
        if db:
            await db.marketplace_orders.update_one(
                {"razorpay_order_id": payment_data.razorpay_order_id},
                {
                    "$set": {
                        "status": "paid",
                        "razorpay_payment_id": payment_data.razorpay_payment_id,
                        "razorpay_signature": payment_data.razorpay_signature,
                        "paid_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        
        return {
            "success": True,
            "message": "Payment verified successfully",
            "order_id": payment_data.razorpay_order_id,
            "payment_id": payment_data.razorpay_payment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")


@router.get("/order/{order_id}")
async def get_order_status(order_id: str):
    """Get order status by Razorpay order ID"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    order = await db.marketplace_orders.find_one(
        {"razorpay_order_id": order_id},
        {"_id": 0}
    )
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/webhook")
async def handle_webhook(request: Request):
    """Handle Razorpay webhook events"""
    try:
        payload = await request.json()
        event = payload.get("event", "")
        
        # Log webhook event
        if db:
            await db.payment_webhooks.insert_one({
                "event": event,
                "payload": payload,
                "received_at": datetime.now(timezone.utc)
            })
        
        # Handle different events
        if event == "payment.captured":
            payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment.get("order_id")
            
            if order_id and db:
                await db.marketplace_orders.update_one(
                    {"razorpay_order_id": order_id},
                    {
                        "$set": {
                            "status": "captured",
                            "payment_details": payment,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
        
        elif event == "payment.failed":
            payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment.get("order_id")
            
            if order_id and db:
                await db.marketplace_orders.update_one(
                    {"razorpay_order_id": order_id},
                    {
                        "$set": {
                            "status": "failed",
                            "failure_reason": payment.get("error_description"),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
        
        return {"status": "processed"}
        
    except Exception as e:
        # Log error but don't fail (webhooks should return 200)
        print(f"Webhook processing error: {str(e)}")
        return {"status": "error", "message": str(e)}
