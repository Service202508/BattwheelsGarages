"""
Tenant Event Module
==================

Event emission system with mandatory tenant tagging.

Every event in the system MUST include:
- organization_id
- user_id  
- request_id
- timestamp

This ensures:
1. Event consumers can filter by tenant
2. Audit trail is complete
3. Cross-tenant event handling is impossible
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import uuid
import asyncio
import logging

from .context import TenantContext, get_tenant_context
from .exceptions import TenantContextMissing

logger = logging.getLogger(__name__)


class TenantEventType(str, Enum):
    """Standard tenant-scoped event types"""
    
    # Ticket lifecycle
    TICKET_CREATED = "tenant.ticket.created"
    TICKET_UPDATED = "tenant.ticket.updated"
    TICKET_ASSIGNED = "tenant.ticket.assigned"
    TICKET_CLOSED = "tenant.ticket.closed"
    TICKET_RESOLVED = "tenant.ticket.resolved"
    
    # Invoice lifecycle
    INVOICE_CREATED = "tenant.invoice.created"
    INVOICE_SENT = "tenant.invoice.sent"
    INVOICE_PAID = "tenant.invoice.paid"
    INVOICE_OVERDUE = "tenant.invoice.overdue"
    
    # Estimate lifecycle
    ESTIMATE_CREATED = "tenant.estimate.created"
    ESTIMATE_SENT = "tenant.estimate.sent"
    ESTIMATE_APPROVED = "tenant.estimate.approved"
    ESTIMATE_REJECTED = "tenant.estimate.rejected"
    ESTIMATE_CONVERTED = "tenant.estimate.converted"
    
    # Inventory
    INVENTORY_LOW_STOCK = "tenant.inventory.low_stock"
    INVENTORY_ALLOCATED = "tenant.inventory.allocated"
    INVENTORY_CONSUMED = "tenant.inventory.consumed"
    
    # EFI Intelligence
    FAILURE_CARD_CREATED = "tenant.efi.card_created"
    FAILURE_CARD_USED = "tenant.efi.card_used"
    FAILURE_CARD_RATED = "tenant.efi.card_rated"
    PATTERN_DETECTED = "tenant.efi.pattern_detected"
    ESCALATION_CREATED = "tenant.efi.escalation_created"
    
    # HR
    EMPLOYEE_CREATED = "tenant.hr.employee_created"
    ATTENDANCE_MARKED = "tenant.hr.attendance_marked"
    LEAVE_REQUESTED = "tenant.hr.leave_requested"
    LEAVE_APPROVED = "tenant.hr.leave_approved"
    PAYROLL_PROCESSED = "tenant.hr.payroll_processed"
    
    # User actions
    USER_ADDED = "tenant.user.added"
    USER_REMOVED = "tenant.user.removed"
    ROLE_CHANGED = "tenant.user.role_changed"
    
    # Settings
    SETTINGS_UPDATED = "tenant.settings.updated"
    INTEGRATION_CONNECTED = "tenant.integration.connected"
    INTEGRATION_DISCONNECTED = "tenant.integration.disconnected"
    
    # Sync
    ZOHO_SYNC_STARTED = "tenant.sync.zoho_started"
    ZOHO_SYNC_COMPLETED = "tenant.sync.zoho_completed"
    ZOHO_SYNC_FAILED = "tenant.sync.zoho_failed"


@dataclass
class TenantEvent:
    """
    Immutable tenant-scoped event.
    
    All events MUST have organization_id and user_id.
    This is enforced at creation time.
    """
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: str = ""
    
    # REQUIRED tenant context
    organization_id: str = ""
    user_id: str = ""
    request_id: str = ""
    
    # Event data
    resource_type: str = ""
    resource_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "api"  # api, background, webhook, sync
    priority: int = 5  # 1-10, lower = higher priority
    
    # Processing state
    processed: bool = False
    processed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.organization_id:
            raise ValueError("TenantEvent requires organization_id")
        if not self.user_id:
            raise ValueError("TenantEvent requires user_id")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "priority": self.priority,
            "processed": self.processed,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }
    
    @classmethod
    def from_context(
        cls,
        ctx: TenantContext,
        event_type: str,
        resource_type: str = "",
        resource_id: str = "",
        data: Dict = None,
        source: str = "api",
        priority: int = 5
    ) -> 'TenantEvent':
        """Create event from tenant context"""
        return cls(
            event_type=event_type,
            organization_id=ctx.org_id,
            user_id=ctx.user_id,
            request_id=ctx.request_id,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data or {},
            source=source,
            priority=priority
        )


class TenantEventHandler:
    """Wrapper for event handlers with tenant validation"""
    
    def __init__(
        self,
        handler: Callable,
        name: str,
        event_types: List[str],
        validate_tenant: bool = True
    ):
        self.handler = handler
        self.name = name
        self.event_types = event_types
        self.validate_tenant = validate_tenant
        self.call_count = 0
        self.error_count = 0
    
    async def execute(self, event: TenantEvent, ctx: Optional[TenantContext] = None) -> Dict:
        """Execute handler with tenant validation"""
        self.call_count += 1
        
        # Validate tenant context matches event
        if self.validate_tenant and ctx:
            if ctx.org_id != event.organization_id:
                self.error_count += 1
                logger.error(
                    f"Handler {self.name} received event for wrong tenant: "
                    f"handler_org={ctx.org_id}, event_org={event.organization_id}"
                )
                return {"status": "rejected", "reason": "tenant_mismatch"}
        
        try:
            if asyncio.iscoroutinefunction(self.handler):
                result = await self.handler(event)
            else:
                result = self.handler(event)
            return {"status": "success", "result": result}
        except Exception as e:
            self.error_count += 1
            logger.error(f"Handler {self.name} failed: {e}")
            return {"status": "error", "error": str(e)}


class TenantEventEmitter:
    """
    Event emitter with mandatory tenant tagging.
    
    All events are:
    1. Tagged with org_id
    2. Logged to event_log collection
    3. Dispatched to handlers filtered by org_id
    """
    
    def __init__(self, db):
        self.db = db
        self._handlers: Dict[str, List[TenantEventHandler]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
        self._stats = {
            "events_emitted": 0,
            "events_processed": 0,
            "events_failed": 0
        }
    
    def register_handler(
        self,
        handler: Callable,
        event_types: List[str],
        name: Optional[str] = None,
        validate_tenant: bool = True
    ):
        """Register an event handler"""
        handler_name = name or handler.__name__
        
        event_handler = TenantEventHandler(
            handler=handler,
            name=handler_name,
            event_types=event_types,
            validate_tenant=validate_tenant
        )
        
        for event_type in event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(event_handler)
        
        logger.info(f"Registered handler '{handler_name}' for events: {event_types}")
    
    def on(self, *event_types: str, validate_tenant: bool = True):
        """Decorator to register event handlers"""
        def decorator(func: Callable):
            self.register_handler(
                handler=func,
                event_types=list(event_types),
                name=func.__name__,
                validate_tenant=validate_tenant
            )
            return func
        return decorator
    
    async def emit(
        self,
        ctx: TenantContext,
        event_type: str,
        resource_type: str = "",
        resource_id: str = "",
        data: Dict = None,
        source: str = "api",
        wait: bool = False
    ) -> TenantEvent:
        """
        Emit a tenant-scoped event.
        
        Args:
            ctx: Tenant context (required)
            event_type: Type of event
            resource_type: Type of resource (ticket, invoice, etc.)
            resource_id: ID of the resource
            data: Event payload
            source: Source of event (api, background, webhook)
            wait: If True, wait for handlers to complete
        
        Returns:
            The emitted event
        """
        event = TenantEvent.from_context(
            ctx=ctx,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data or {},
            source=source
        )
        
        self._stats["events_emitted"] += 1
        
        # Log to database
        await self.db.tenant_events.insert_one(event.to_dict())
        
        # Get handlers for this event type
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for event: {event_type}")
            return event
        
        logger.info(
            f"Emitting {event_type} to {len(handlers)} handlers "
            f"(org={ctx.org_id}, resource={resource_type}/{resource_id})"
        )
        
        if wait:
            await self._process_event(event, handlers, ctx)
        else:
            await self._queue.put((event, handlers, ctx))
            if not self._processing:
                asyncio.create_task(self._process_queue())
        
        return event
    
    async def emit_raw(self, event: TenantEvent) -> TenantEvent:
        """Emit a pre-created event (used for background jobs)"""
        self._stats["events_emitted"] += 1
        await self.db.tenant_events.insert_one(event.to_dict())
        
        handlers = self._handlers.get(event.event_type, [])
        if handlers:
            await self._queue.put((event, handlers, None))
            if not self._processing:
                asyncio.create_task(self._process_queue())
        
        return event
    
    async def _process_event(
        self,
        event: TenantEvent,
        handlers: List[TenantEventHandler],
        ctx: Optional[TenantContext]
    ):
        """Process event with all handlers"""
        results = []
        
        for handler in handlers:
            result = await handler.execute(event, ctx)
            results.append({
                "handler": handler.name,
                **result
            })
        
        # Update event as processed
        await self.db.tenant_events.update_one(
            {"event_id": event.event_id},
            {"$set": {
                "processed": True,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "handler_results": results
            }}
        )
        
        self._stats["events_processed"] += 1
        
        failed = [r for r in results if r.get("status") != "success"]
        if failed:
            self._stats["events_failed"] += len(failed)
    
    async def _process_queue(self):
        """Background task to process event queue"""
        self._processing = True
        
        while not self._queue.empty():
            try:
                event, handlers, ctx = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                await self._process_event(event, handlers, ctx)
                self._queue.task_done()
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")
        
        self._processing = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get emitter statistics"""
        handler_stats = {}
        for event_type, handlers in self._handlers.items():
            handler_stats[event_type] = [
                {
                    "name": h.name,
                    "calls": h.call_count,
                    "errors": h.error_count
                }
                for h in handlers
            ]
        
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "handlers": handler_stats
        }


# Singleton emitter
_tenant_emitter: Optional[TenantEventEmitter] = None


def init_tenant_event_emitter(db) -> TenantEventEmitter:
    """Initialize the tenant event emitter"""
    global _tenant_emitter
    _tenant_emitter = TenantEventEmitter(db)
    logger.info("TenantEventEmitter initialized")
    return _tenant_emitter


def get_tenant_event_emitter() -> TenantEventEmitter:
    """Get the singleton emitter"""
    if _tenant_emitter is None:
        raise RuntimeError("TenantEventEmitter not initialized")
    return _tenant_emitter


async def emit_tenant_event(
    ctx: TenantContext,
    event_type: str,
    resource_type: str = "",
    resource_id: str = "",
    data: Dict = None
) -> TenantEvent:
    """Convenience function to emit a tenant event"""
    emitter = get_tenant_event_emitter()
    return await emitter.emit(
        ctx=ctx,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        data=data
    )
