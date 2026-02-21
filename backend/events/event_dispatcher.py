"""
Battwheels OS - Event Dispatcher
Central event system for event-driven architecture

This is the CORE of the EFI platform. All business workflows flow through events.
Routes emit events -> Dispatcher routes to handlers -> Services process

Event Flow:
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Route  │ --> │  Dispatcher │ --> │   Handlers   │ --> │ Services │
└─────────┘     └─────────────┘     └──────────────┘     └──────────┘
                      │
                      v
              ┌─────────────┐
              │  Event Log  │
              └─────────────┘
"""
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import asyncio
import logging
import uuid
from functools import wraps

logger = logging.getLogger(__name__)


# ==================== EVENT TYPES ====================

class EventType(str, Enum):
    """All system events"""
    
    # Ticket Events
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_STATUS_CHANGED = "ticket.status_changed"
    TICKET_RESOLVED = "ticket.resolved"
    TICKET_CLOSED = "ticket.closed"
    
    # EFI Events
    FAILURE_CARD_CREATED = "failure_card.created"
    FAILURE_CARD_UPDATED = "failure_card.updated"
    FAILURE_CARD_APPROVED = "failure_card.approved"
    FAILURE_CARD_DEPRECATED = "failure_card.deprecated"
    FAILURE_CARD_USED = "failure_card.used"
    NEW_FAILURE_DETECTED = "failure.new_detected"
    
    # AI/Matching Events
    MATCH_REQUESTED = "ai.match_requested"
    MATCH_COMPLETED = "ai.match_completed"
    CONFIDENCE_UPDATED = "ai.confidence_updated"
    PATTERN_DETECTED = "ai.pattern_detected"
    
    # Technician Events
    TECHNICIAN_ACTION_STARTED = "technician.action_started"
    TECHNICIAN_ACTION_COMPLETED = "technician.action_completed"
    ACTION_COMPLETED = "technician.action_completed"  # Alias
    
    # Inventory Events
    INVENTORY_LOW = "inventory.low_stock"
    INVENTORY_ALLOCATED = "inventory.allocated"
    INVENTORY_USED = "inventory.used"
    INVENTORY_RETURNED = "inventory.returned"
    
    # Invoice Events
    INVOICE_CREATED = "invoice.created"
    INVOICE_SENT = "invoice.sent"
    PAYMENT_RECEIVED = "payment.received"
    
    # HR Events
    EMPLOYEE_CREATED = "employee.created"
    ATTENDANCE_MARKED = "attendance.marked"
    LEAVE_REQUESTED = "leave.requested"
    LEAVE_APPROVED = "leave.approved"
    PAYROLL_PROCESSED = "payroll.processed"
    
    # System Events
    SYSTEM_ERROR = "system.error"
    AUDIT_LOG = "system.audit"


class EventPriority(int, Enum):
    """Event processing priority"""
    CRITICAL = 1    # Process immediately
    HIGH = 2        # Process soon
    NORMAL = 5      # Default
    LOW = 8         # Process when idle
    BACKGROUND = 10 # Background processing


# ==================== EVENT MODEL ====================

class Event:
    """Base event class with tenant context support (Phase D)"""
    
    def __init__(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        organization_id: Optional[str] = None  # Phase D: Tenant tagging
    ):
        self.event_id = f"evt_{uuid.uuid4().hex[:12]}"
        self.event_type = event_type
        self.data = data
        self.source = source
        self.priority = priority
        self.user_id = user_id
        self.organization_id = organization_id  # Phase D: Required for tenant isolation
        self.correlation_id = correlation_id or self.event_id
        self.timestamp = datetime.now(timezone.utc)
        self.processed = False
        self.handlers_completed = []
        self.handlers_failed = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "data": self.data,
            "source": self.source,
            "priority": self.priority.value if isinstance(self.priority, EventPriority) else self.priority,
            "user_id": self.user_id,
            "organization_id": self.organization_id,  # Phase D: Include in serialization
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed,
            "handlers_completed": self.handlers_completed,
            "handlers_failed": self.handlers_failed
        }


# ==================== EVENT HANDLER ====================

class EventHandler:
    """Wrapper for event handlers with metadata"""
    
    def __init__(
        self,
        handler: Callable,
        name: str,
        event_types: List[EventType],
        priority: EventPriority = EventPriority.NORMAL,
        async_handler: bool = True,
        retry_count: int = 3
    ):
        self.handler = handler
        self.name = name
        self.event_types = event_types
        self.priority = priority
        self.async_handler = async_handler
        self.retry_count = retry_count
        self.call_count = 0
        self.error_count = 0
        self.last_called = None
    
    async def execute(self, event: Event) -> Dict[str, Any]:
        """Execute the handler with retry logic"""
        self.call_count += 1
        self.last_called = datetime.now(timezone.utc)
        
        last_error = None
        for attempt in range(self.retry_count):
            try:
                if self.async_handler:
                    result = await self.handler(event)
                else:
                    result = self.handler(event)
                return {"status": "success", "result": result}
            except Exception as e:
                last_error = e
                self.error_count += 1
                logger.warning(f"Handler {self.name} failed attempt {attempt + 1}: {e}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))
        
        return {"status": "error", "error": str(last_error)}


# ==================== EVENT DISPATCHER ====================

class EventDispatcher:
    """
    Central event dispatcher for the EFI platform
    
    Usage:
        dispatcher = EventDispatcher(db)
        
        # Register handler
        @dispatcher.on(EventType.TICKET_CREATED)
        async def handle_ticket_created(event: Event):
            # Process event
            pass
        
        # Emit event
        await dispatcher.emit(EventType.TICKET_CREATED, {"ticket_id": "xxx"})
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db=None):
        if self._initialized:
            if db is not None:
                self.db = db
            return
        
        self.db = db
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
        self._stats = {
            "events_emitted": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_registered": 0
        }
        self._initialized = True
        logger.info("EventDispatcher initialized")
    
    def register_handler(
        self,
        handler: Callable,
        event_types: List[EventType],
        name: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        retry_count: int = 3
    ) -> EventHandler:
        """Register an event handler"""
        handler_name = name or handler.__name__
        is_async = asyncio.iscoroutinefunction(handler)
        
        event_handler = EventHandler(
            handler=handler,
            name=handler_name,
            event_types=event_types,
            priority=priority,
            async_handler=is_async,
            retry_count=retry_count
        )
        
        for event_type in event_types:
            key = event_type.value if isinstance(event_type, EventType) else event_type
            if key not in self._handlers:
                self._handlers[key] = []
            self._handlers[key].append(event_handler)
            # Sort by priority
            self._handlers[key].sort(key=lambda h: h.priority.value)
        
        self._stats["handlers_registered"] += 1
        logger.info(f"Registered handler '{handler_name}' for events: {[e.value for e in event_types]}")
        
        return event_handler
    
    def on(
        self,
        *event_types: EventType,
        priority: EventPriority = EventPriority.NORMAL,
        retry_count: int = 3
    ):
        """Decorator to register event handlers"""
        def decorator(func: Callable):
            self.register_handler(
                handler=func,
                event_types=list(event_types),
                name=func.__name__,
                priority=priority,
                retry_count=retry_count
            )
            return func
        return decorator
    
    async def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "api",
        priority: EventPriority = EventPriority.NORMAL,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        organization_id: Optional[str] = None,  # Phase D: Tenant tagging
        wait: bool = False
    ) -> Event:
        """
        Emit an event to all registered handlers
        
        Args:
            event_type: Type of event
            data: Event payload
            source: Source of the event (route name, service name)
            priority: Processing priority
            user_id: User who triggered the event
            correlation_id: ID to trace related events
            organization_id: Organization ID for tenant isolation (Phase D)
            wait: If True, wait for all handlers to complete
        
        Returns:
            The emitted event
        """
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            priority=priority,
            user_id=user_id,
            correlation_id=correlation_id,
            organization_id=organization_id  # Phase D: Pass to event
        )
        
        self._stats["events_emitted"] += 1
        
        # Log event to database (with organization_id for tenant filtering)
        if self.db is not None:
            try:
                event_doc = event.to_dict()
                # Ensure organization_id is always present in event_log
                if organization_id:
                    event_doc["organization_id"] = organization_id
                await self.db.event_log.insert_one(event_doc)
            except Exception as e:
                logger.error(f"Failed to log event: {e}")
        
        # Get handlers for this event type
        key = event_type.value if isinstance(event_type, EventType) else event_type
        handlers = self._handlers.get(key, [])
        
        if not handlers:
            logger.debug(f"No handlers registered for event: {key}")
            return event
        
        logger.info(f"Emitting {key} to {len(handlers)} handlers (org: {organization_id})")
        
        if wait:
            # Synchronous processing - wait for all handlers
            await self._process_event(event, handlers)
        else:
            # Asynchronous processing - add to queue
            await self._event_queue.put((event, handlers))
            # Ensure processor is running
            if not self._processing:
                asyncio.create_task(self._process_queue())
        
        return event
    
    async def _process_event(self, event: Event, handlers: List[EventHandler]):
        """Process an event with all handlers"""
        for handler in handlers:
            try:
                result = await handler.execute(event)
                if result["status"] == "success":
                    event.handlers_completed.append(handler.name)
                else:
                    event.handlers_failed.append({
                        "handler": handler.name,
                        "error": result.get("error")
                    })
            except Exception as e:
                logger.error(f"Error in handler {handler.name}: {e}")
                event.handlers_failed.append({
                    "handler": handler.name,
                    "error": str(e)
                })
        
        event.processed = True
        self._stats["events_processed"] += 1
        
        if event.handlers_failed:
            self._stats["events_failed"] += 1
        
        # Update event in database
        if self.db is not None:
            try:
                await self.db.event_log.update_one(
                    {"event_id": event.event_id},
                    {"$set": {
                        "processed": True,
                        "handlers_completed": event.handlers_completed,
                        "handlers_failed": event.handlers_failed,
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            except Exception as e:
                logger.error(f"Failed to update event log: {e}")
    
    async def _process_queue(self):
        """Background task to process event queue"""
        self._processing = True
        
        while not self._event_queue.empty():
            try:
                event, handlers = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self._process_event(event, handlers)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")
        
        self._processing = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics"""
        handler_stats = {}
        for event_type, handlers in self._handlers.items():
            handler_stats[event_type] = [
                {
                    "name": h.name,
                    "calls": h.call_count,
                    "errors": h.error_count,
                    "last_called": h.last_called.isoformat() if h.last_called else None
                }
                for h in handlers
            ]
        
        return {
            **self._stats,
            "queue_size": self._event_queue.qsize(),
            "handlers": handler_stats
        }
    
    def get_registered_events(self) -> List[str]:
        """Get list of registered event types"""
        return list(self._handlers.keys())


# ==================== GLOBAL DISPATCHER ====================

# Singleton instance - will be initialized with db in server.py
_dispatcher: Optional[EventDispatcher] = None


def get_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = EventDispatcher()
    return _dispatcher


def init_dispatcher(db) -> EventDispatcher:
    """Initialize the global event dispatcher with database"""
    global _dispatcher
    _dispatcher = EventDispatcher(db)
    return _dispatcher


# ==================== HELPER DECORATORS ====================

def emit_event(
    event_type: EventType,
    data_extractor: Optional[Callable] = None,
    source: str = "api"
):
    """
    Decorator to automatically emit events after route execution
    
    Usage:
        @router.post("/tickets")
        @emit_event(EventType.TICKET_CREATED, lambda result: {"ticket_id": result["ticket_id"]})
        async def create_ticket(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Extract event data
            if data_extractor:
                event_data = data_extractor(result)
            elif isinstance(result, dict):
                event_data = result
            else:
                event_data = {"result": result}
            
            # Emit event
            dispatcher = get_dispatcher()
            await dispatcher.emit(
                event_type=event_type,
                data=event_data,
                source=source
            )
            
            return result
        return wrapper
    return decorator
