from typing import Callable, Type, List

from app.core.events.document_events import DocumentGeneratedEvent

class EventBus:
    """In-memory for now, can be replaced with RabbitMQ/Kafka"""
    
    def __init__(self):
        self._handlers: dict[Type, List[Callable]] = {}
    
    def subscribe(self, event_type: Type, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event):
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            # Async execution in production
            handler(event)

# Usage: Multiple services react to one event
class NotificationService:
    def on_document_generated(self, event: DocumentGeneratedEvent):
        # Send email
        pass

class AnalyticsService:
    def on_document_generated(self, event: DocumentGeneratedEvent):
        # Update metrics
        pass

class AuditService:
    def on_document_generated(self, event: DocumentGeneratedEvent):
        # Log for compliance
        pass
