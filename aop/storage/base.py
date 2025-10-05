"""
Abstract base class for AOP storage backends.

All storage implementations must inherit from BaseStorage and implement
all abstract methods to ensure consistent behavior across backends.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime


class BaseStorage(ABC):
    """
    Abstract base class defining the storage interface for AOP events.
    
    All storage backends (SQLite, PostgreSQL, In-Memory, etc.) must
    implement this interface to ensure consistent API across different
    storage types.
    """
    
    @abstractmethod
    def log_event(self, event: Dict[str, Any]) -> None:
        """
        Store a single AOP event.
        
        Args:
            event: Complete AOP event dictionary with all required fields
            
        Raises:
            AOPStorageError: If event cannot be stored
            
        Example:
            >>> storage.log_event({
            ...     'id': '01HQRS...',
            ...     'version': '1.0',
            ...     'timestamp': '2025-10-04T10:30:00Z',
            ...     'agent_id': 'agent-1',
            ...     'event_type': 'mcp.tool.call',
            ...     # ... other fields
            ... })
        """
        pass
    
    @abstractmethod
    def query_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        protocol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query events with optional filters.
        
        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type (e.g., 'mcp.tool.call')
            protocol: Filter by protocol ('mcp', 'a2a', 'ap2')
            start_time: Events after this timestamp
            end_time: Events before this timestamp
            correlation_id: Filter by correlation ID (trace)
            limit: Maximum number of events to return
            
        Returns:
            List of matching events, sorted by timestamp (newest first)
            
        Example:
            >>> events = storage.query_events(
            ...     agent_id='agent-1',
            ...     event_type='mcp.tool.call',
            ...     limit=10
            ... )
        """
        pass
    
    @abstractmethod
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single event by its ID.
        
        Args:
            event_id: Unique event identifier (UUID v7)
            
        Returns:
            Event dictionary if found, None otherwise
            
        Example:
            >>> event = storage.get_event('01HQRS9XOP2JRBN7K01RGUWZ1W')
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Close storage connections and cleanup resources.
        
        Should be called when storage is no longer needed.
        Implementations should be idempotent (safe to call multiple times).
        
        Example:
            >>> storage.close()
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()