"""
Base classes for protocol adapters.
"""

from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from ..client import AOPClient


class EventHandle:
    """
    Handle for a logged event that enables chaining related events.
    
    This lightweight object stores the event ID and provides helper
    methods to log related events (like results for a call).
    
    Attributes:
        id: The event ID
    """
    
    def __init__(
        self,
        event_id: str,
        client: 'AOPClient',
        adapter: 'BaseAdapter',
        event_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize event handle.
        
        Args:
            event_id: The event ID
            client: AOP client instance
            adapter: Adapter that created this event
            event_data: Optional event data for reference
        """
        self.id = event_id
        self._client = client
        self._adapter = adapter
        self._event_data = event_data or {}
    
    def __str__(self) -> str:
        return self.id
    
    def __repr__(self) -> str:
        return f"EventHandle(id='{self.id}')"


class BaseAdapter:
    """
    Base class for protocol adapters.
    
    Provides common functionality for all protocol adapters
    like correlation ID handling and event building.
    """
    
    def __init__(self, client: 'AOPClient'):
        """
        Initialize adapter.
        
        Args:
            client: AOP client instance
        """
        self.client = client
    
    def _get_correlation_id(
        self,
        explicit_correlation_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get correlation ID from explicit param or trace context.
        
        Args:
            explicit_correlation_id: Explicitly provided correlation ID
            
        Returns:
            Correlation ID (explicit or from context) or None
        """
        if explicit_correlation_id is not None:
            return explicit_correlation_id
        
        # Try to get from trace context
        from ..trace import get_current_correlation_id
        return get_current_correlation_id()
    
    def _build_event(
        self,
        agent_id: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        severity: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build event dictionary with correlation ID from context if available.
        
        Args:
            agent_id: Agent identifier
            event_type: Event type
            data: Event data
            correlation_id: Explicit correlation ID (overrides context)
            parent_id: Parent event ID
            severity: Event severity
            duration_ms: Duration in milliseconds
            metadata: Event metadata
            error: Error information
            
        Returns:
            Event dictionary
        """
        # Get correlation ID (explicit or from context)
        final_correlation_id = self._get_correlation_id(correlation_id)
        
        event: Dict[str, Any] = {
            'agent_id': agent_id,
            'event_type': event_type
        }
        
        if data is not None:
            event['data'] = data
        if final_correlation_id is not None:
            event['correlation_id'] = final_correlation_id
        if parent_id is not None:
            event['parent_id'] = parent_id
        if severity is not None:
            event['severity'] = severity
        if duration_ms is not None:
            event['duration_ms'] = duration_ms
        if metadata is not None:
            event['metadata'] = metadata
        if error is not None:
            event['error'] = error
        
        return event
    
    def _log_and_return_handle(
        self,
        event: Dict[str, Any],
        validate: bool = True
    ) -> EventHandle:
        """
        Log event and return handle.
        
        Args:
            event: Event dictionary
            validate: Whether to validate event
            
        Returns:
            EventHandle for the logged event
        """
        event_id = self.client.log_event(event, validate=validate)
        return EventHandle(
            event_id=event_id,
            client=self.client,
            adapter=self,
            event_data=event
        )