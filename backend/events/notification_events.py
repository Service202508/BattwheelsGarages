"""
Battwheels OS - Notification Event Handlers
Handles notification triggers based on system events

Event Subscriptions:
TICKET_CREATED -> Notify assigned technician
TICKET_STATUS_CHANGED -> Notify customer
INVOICE_CREATED -> Send invoice email/WhatsApp
FAILURE_CARD_APPROVED -> Notify network
"""
from typing import Dict, Any
from datetime import datetime, timezone
import logging

from events.event_dispatcher import (
    EventType, EventPriority, Event,
    get_dispatcher, EventDispatcher
)

logger = logging.getLogger(__name__)


def register_notification_handlers(dispatcher: EventDispatcher, db, notification_service=None):
    """
    Register notification event handlers
    
    Note: notification_service should have send_email and send_whatsapp methods
    """
    
    @dispatcher.on(EventType.TICKET_CREATED, priority=EventPriority.LOW)
    async def handle_ticket_created_notification(event: Event):
        """
        Notify when new ticket is created:
        1. Notify assigned technician
        2. Log notification
        """
        ticket_id = event.data.get("ticket_id")
        assigned_to = event.data.get("assigned_to")
        priority = event.data.get("priority")
        
        if not ticket_id:
            return {"skipped": "missing_ticket_id"}
        
        # Get ticket details
        ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
        if not ticket:
            return {"skipped": "ticket_not_found"}
        
        # Log notification attempt
        notification = {
            "notification_id": f"ntf_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "ticket_created",
            "channel": "internal",
            "recipient": assigned_to or "unassigned",
            "ticket_id": ticket_id,
            "data": {
                "title": ticket.get("title"),
                "priority": ticket.get("priority"),
                "vehicle": f"{ticket.get('vehicle_make', '')} {ticket.get('vehicle_model', '')}"
            },
            "status": "logged", "organization_id": ticket.get("organization_id", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.notifications.insert_one(notification)
        
        logger.info(f"Logged ticket creation notification for {ticket_id}")
        
        return {"notification_logged": True}
    
    @dispatcher.on(EventType.TICKET_STATUS_CHANGED, priority=EventPriority.NORMAL)
    async def handle_status_change_notification(event: Event):
        """
        Notify customer when ticket status changes to resolved/closed
        """
        ticket_id = event.data.get("ticket_id")
        old_status = event.data.get("old_status")
        new_status = event.data.get("new_status")
        
        if new_status not in ["resolved", "closed"]:
            return {"skipped": "not_resolution_status"}
        
        # Get ticket with customer info
        ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
        if not ticket:
            return {"skipped": "ticket_not_found"}
        
        customer_id = ticket.get("customer_id")
        if not customer_id:
            return {"skipped": "no_customer"}
        
        customer = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
        if not customer:
            return {"skipped": "customer_not_found"}
        
        # Build notification
        notification = {
            "notification_id": f"ntf_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "ticket_resolved",
            "channel": "email" if customer.get("email") else "whatsapp",
            "recipient": customer.get("email") or customer.get("phone"),
            "ticket_id": ticket_id,
            "data": {
                "customer_name": customer.get("name"),
                "ticket_title": ticket.get("title"),
                "resolution": ticket.get("resolution"),
                "status": new_status
            },
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.notifications.insert_one(notification)
        
        # TODO: Actually send notification via notification_service
        # if notification_service:
        #     await notification_service.send(notification)
        
        logger.info(f"Queued resolution notification for ticket {ticket_id}")
        
        return {"notification_queued": True, "channel": notification["channel"]}
    
    @dispatcher.on(EventType.INVOICE_CREATED, priority=EventPriority.NORMAL)
    async def handle_invoice_notification(event: Event):
        """
        Send invoice to customer via email/WhatsApp
        """
        invoice_id = event.data.get("invoice_id")
        customer_id = event.data.get("customer_id")
        
        if not invoice_id:
            return {"skipped": "missing_invoice_id"}
        
        # Get invoice
        invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
        if not invoice:
            return {"skipped": "invoice_not_found"}
        
        # Get customer
        customer = None
        if customer_id:
            customer = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
        
        # Build notification
        notification = {
            "notification_id": f"ntf_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "invoice_sent",
            "channel": "email",
            "recipient": customer.get("email") if customer else invoice.get("customer_email"),
            "invoice_id": invoice_id,
            "data": {
                "invoice_number": invoice.get("invoice_number"),
                "total": invoice.get("total"),
                "due_date": invoice.get("due_date"),
                "customer_name": customer.get("name") if customer else invoice.get("customer_name")
            },
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.notifications.insert_one(notification)
        
        logger.info(f"Queued invoice notification for {invoice_id}")
        
        return {"notification_queued": True}
    
    @dispatcher.on(EventType.FAILURE_CARD_APPROVED, priority=EventPriority.LOW)
    async def handle_card_approved_notification(event: Event):
        """
        Notify when failure card is approved (for network distribution)
        """
        failure_id = event.data.get("failure_id")
        
        notification = {
            "notification_id": f"ntf_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "failure_card_approved",
            "channel": "internal",
            "recipient": "network",
            "failure_id": failure_id,
            "data": {"event": "card_approved_for_network"},
            "status": "logged", "organization_id": ticket.get("organization_id", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.notifications.insert_one(notification)
        
        return {"notification_logged": True}
    
    @dispatcher.on(EventType.INVENTORY_LOW, priority=EventPriority.HIGH)
    async def handle_low_inventory_alert(event: Event):
        """
        Alert when inventory is low
        """
        item_id = event.data.get("item_id")
        item_name = event.data.get("item_name")
        current_quantity = event.data.get("current_quantity")
        threshold = event.data.get("threshold")
        
        notification = {
            "notification_id": f"ntf_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "inventory_low",
            "channel": "internal",
            "recipient": "admin",
            "item_id": item_id,
            "data": {
                "item_name": item_name,
                "current_quantity": current_quantity,
                "threshold": threshold,
                "alert": "Low stock alert"
            },
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.notifications.insert_one(notification)
        
        logger.warning(f"Low inventory alert: {item_name} ({current_quantity}/{threshold})")
        
        return {"alert_created": True}
    
    logger.info("Notification event handlers registered")


async def get_pending_notifications(db, limit: int = 50) -> list:
    """Get pending notifications for processing"""
    notifications = await db.notifications.find(
        {"status": "pending"},
        {"_id": 0}
    ).sort("created_at", 1).limit(limit).to_list(limit)
    return notifications


async def mark_notification_sent(db, notification_id: str, result: dict):
    """Mark notification as sent"""
    await db.notifications.update_one(
        {"notification_id": notification_id},
        {"$set": {
            "status": "sent" if result.get("success") else "failed",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "result": result
        }}
    )
