"""
Battwheels OS - Events Module
Central event-driven architecture for EFI platform

This module provides:
- EventDispatcher: Central event routing
- EventType: All system event types
- Event handlers for tickets, failures, notifications

Usage:
    from events import init_event_system, emit_event, EventType
    
    # Initialize during startup
    dispatcher = init_event_system(db)
    
    # Emit events from routes
    await dispatcher.emit(EventType.TICKET_CREATED, {"ticket_id": "xxx"})
"""
from events.event_dispatcher import (
    EventDispatcher,
    EventType,
    EventPriority,
    Event,
    EventHandler,
    get_dispatcher,
    init_dispatcher,
    emit_event
)

from events.ticket_events import register_ticket_handlers
from events.failure_events import register_failure_handlers
from events.notification_events import register_notification_handlers

import logging

logger = logging.getLogger(__name__)


def init_event_system(db, notification_service=None) -> EventDispatcher:
    """
    Initialize the complete event system
    
    Call this during server startup after database is connected
    
    Args:
        db: MongoDB database instance
        notification_service: Optional notification service for sending messages
    
    Returns:
        Configured EventDispatcher instance
    """
    # Initialize dispatcher with database
    dispatcher = init_dispatcher(db)
    
    # Register all event handlers
    register_ticket_handlers(dispatcher, db)
    register_failure_handlers(dispatcher, db)
    register_notification_handlers(dispatcher, db, notification_service)
    
    logger.info(f"Event system initialized with {len(dispatcher.get_registered_events())} event types")
    
    return dispatcher


__all__ = [
    # Dispatcher
    "EventDispatcher",
    "init_dispatcher",
    "get_dispatcher",
    "init_event_system",
    
    # Event types and models
    "EventType",
    "EventPriority",
    "Event",
    "EventHandler",
    
    # Decorators
    "emit_event",
    
    # Handler registration
    "register_ticket_handlers",
    "register_failure_handlers",
    "register_notification_handlers",
]
