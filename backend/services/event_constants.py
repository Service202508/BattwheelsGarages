# Event Constants
# Standard event types for the event-driven architecture
# Ensures consistent event naming across all modules

class QuoteEvents:
    """Quote/Estimate events"""
    CREATED = "QUOTE_CREATED"
    UPDATED = "QUOTE_UPDATED"
    SENT = "QUOTE_SENT"
    VIEWED = "QUOTE_VIEWED"
    ACCEPTED = "QUOTE_ACCEPTED"
    DECLINED = "QUOTE_DECLINED"
    EXPIRED = "QUOTE_EXPIRED"
    CONVERTED_TO_INVOICE = "QUOTE_CONVERTED_TO_INVOICE"
    CONVERTED_TO_SALES_ORDER = "QUOTE_CONVERTED_TO_SALES_ORDER"
    VOIDED = "QUOTE_VOIDED"
    DELETED = "QUOTE_DELETED"

class InvoiceEvents:
    """Invoice events"""
    CREATED = "INVOICE_CREATED"
    UPDATED = "INVOICE_UPDATED"
    SENT = "INVOICE_SENT"
    VIEWED = "INVOICE_VIEWED"
    PARTIALLY_PAID = "INVOICE_PARTIALLY_PAID"
    FULLY_PAID = "INVOICE_FULLY_PAID"
    OVERDUE = "INVOICE_OVERDUE"
    VOIDED = "INVOICE_VOIDED"
    DELETED = "INVOICE_DELETED"
    WRITE_OFF = "INVOICE_WRITE_OFF"
    CREDIT_APPLIED = "INVOICE_CREDIT_APPLIED"

class SalesOrderEvents:
    """Sales Order events"""
    CREATED = "SALES_ORDER_CREATED"
    UPDATED = "SALES_ORDER_UPDATED"
    CONFIRMED = "SALES_ORDER_CONFIRMED"
    SENT = "SALES_ORDER_SENT"
    PARTIALLY_FULFILLED = "SALES_ORDER_PARTIALLY_FULFILLED"
    FULLY_FULFILLED = "SALES_ORDER_FULLY_FULFILLED"
    CONVERTED_TO_INVOICE = "SALES_ORDER_CONVERTED_TO_INVOICE"
    VOIDED = "SALES_ORDER_VOIDED"
    DELETED = "SALES_ORDER_DELETED"

class PaymentEvents:
    """Payment events"""
    CREATED = "PAYMENT_CREATED"
    UPDATED = "PAYMENT_UPDATED"
    APPLIED = "PAYMENT_APPLIED"
    UNAPPLIED = "PAYMENT_UNAPPLIED"
    REFUNDED = "PAYMENT_REFUNDED"
    DELETED = "PAYMENT_DELETED"

class ContactEvents:
    """Customer/Vendor/Contact events"""
    CREATED = "CONTACT_CREATED"
    UPDATED = "CONTACT_UPDATED"
    DELETED = "CONTACT_DELETED"
    MERGED = "CONTACT_MERGED"
    BALANCE_UPDATED = "CONTACT_BALANCE_UPDATED"

class ItemEvents:
    """Item events"""
    CREATED = "ITEM_CREATED"
    UPDATED = "ITEM_UPDATED"
    DELETED = "ITEM_DELETED"
    STOCK_UPDATED = "ITEM_STOCK_UPDATED"
    LOW_STOCK_ALERT = "ITEM_LOW_STOCK_ALERT"
    OUT_OF_STOCK = "ITEM_OUT_OF_STOCK"

class InventoryEvents:
    """Inventory events"""
    ADJUSTMENT_CREATED = "INVENTORY_ADJUSTMENT_CREATED"
    ADJUSTMENT_APPLIED = "INVENTORY_ADJUSTMENT_APPLIED"
    ADJUSTMENT_VOIDED = "INVENTORY_ADJUSTMENT_VOIDED"
    STOCK_TRANSFERRED = "INVENTORY_STOCK_TRANSFERRED"
    SHIPMENT_CREATED = "INVENTORY_SHIPMENT_CREATED"
    SHIPMENT_DISPATCHED = "INVENTORY_SHIPMENT_DISPATCHED"
    SHIPMENT_DELIVERED = "INVENTORY_SHIPMENT_DELIVERED"

class BillEvents:
    """Vendor Bill events"""
    CREATED = "BILL_CREATED"
    UPDATED = "BILL_UPDATED"
    APPROVED = "BILL_APPROVED"
    PAID = "BILL_PAID"
    PARTIALLY_PAID = "BILL_PARTIALLY_PAID"
    VOIDED = "BILL_VOIDED"
    DELETED = "BILL_DELETED"

class ExpenseEvents:
    """Expense events"""
    CREATED = "EXPENSE_CREATED"
    UPDATED = "EXPENSE_UPDATED"
    APPROVED = "EXPENSE_APPROVED"
    REJECTED = "EXPENSE_REJECTED"
    REIMBURSED = "EXPENSE_REIMBURSED"
    DELETED = "EXPENSE_DELETED"

# ========================= EVENT PAYLOAD STRUCTURE =========================

class EventPayload:
    """
    Standard event payload structure.
    All events should follow this format for consistency.
    """
    
    @staticmethod
    def create(
        event_type: str,
        entity_type: str,
        entity_id: str,
        entity_data: dict = None,
        user_id: str = "system",
        organization_id: str = "",
        metadata: dict = None
    ) -> dict:
        """
        Create a standard event payload.
        
        Args:
            event_type: Event type constant
            entity_type: Type of entity (invoice, quote, etc.)
            entity_id: ID of the entity
            entity_data: Key data from the entity
            user_id: User who triggered the event
            organization_id: Organization context
            metadata: Additional metadata
        
        Returns:
            Standardized event payload dict
        """
        from datetime import datetime, timezone
        
        return {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_data": entity_data or {},
            "user_id": user_id,
            "organization_id": organization_id,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        }

# ========================= EVENT HANDLERS REGISTRY =========================

class EventHandlerRegistry:
    """
    Registry for event handlers.
    Allows modules to subscribe to events.
    """
    
    _handlers = {}
    
    @classmethod
    def register(cls, event_type: str, handler):
        """Register a handler for an event type"""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
    
    @classmethod
    def get_handlers(cls, event_type: str) -> list:
        """Get all handlers for an event type"""
        return cls._handlers.get(event_type, [])
    
    @classmethod
    def unregister(cls, event_type: str, handler):
        """Unregister a handler"""
        if event_type in cls._handlers:
            cls._handlers[event_type] = [
                h for h in cls._handlers[event_type] if h != handler
            ]

# ========================= EVENT WORKFLOW TRIGGERS =========================

# Define which events trigger other events/actions
EVENT_TRIGGERS = {
    QuoteEvents.ACCEPTED: [
        # When quote is accepted, optionally create invoice
        {"action": "create_invoice", "condition": "auto_convert_enabled"}
    ],
    InvoiceEvents.FULLY_PAID: [
        # When invoice is fully paid, update customer balance
        {"action": "update_customer_balance"},
        # Update receivables
        {"action": "update_receivables"}
    ],
    PaymentEvents.CREATED: [
        # When payment is created, check if invoice is fully paid
        {"action": "check_invoice_payment_status"}
    ],
    InventoryEvents.ADJUSTMENT_APPLIED: [
        # When adjustment is applied, update item stock
        {"action": "update_item_stock"},
        # Check for low stock alerts
        {"action": "check_low_stock"}
    ],
    ItemEvents.STOCK_UPDATED: [
        # When stock is updated, check for alerts
        {"action": "check_low_stock_alert"}
    ]
}
