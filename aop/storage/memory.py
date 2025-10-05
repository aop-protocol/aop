"""
In-memory storage backend for AOP events.

Dictionary-based storage suitable for:
- Unit testing (fast, isolated)
- CI/CD pipelines (no I/O overhead)
- Temporary/ephemeral workloads
- Development prototyping

WARNING: All data is lost when process ends. Not suitable for production.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import copy

from .base import BaseStorage


class InMemoryStorage(BaseStorage):
    """
    In-memory storage implementation using Python dictionary.
    
    Provides ultra-fast event storage with no persistence.
    Perfect for testing scenarios where speed matters more than durability.
    
    Connection string format:
        memory                            # Simple keyword
        memory://                         # URL format
    """
    
    def __init__(self) -> None:
        """Initialize in-memory storage with empty dictionary."""
        self.events: Dict[str, Dict[str, Any]] = {}
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """
        Store event in memory.
        
        Args:
            event: Complete AOP event dictionary
            
        Note:
            Events are deep-copied to prevent external mutations
        """
        # Deep copy to prevent external modifications
        self.events[event['id']] = copy.deepcopy(event)
    
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
        Query events using in-memory filtering.
        
        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type
            protocol: Filter by protocol
            start_time: Events after this timestamp
            end_time: Events before this timestamp
            correlation_id: Filter by correlation ID
            limit: Maximum number of events
            
        Returns:
            List of matching events, sorted by timestamp (newest first)
        """
        results = []
        
        for event in self.events.values():
            # Apply filters
            if agent_id and event.get('agent_id') != agent_id:
                continue
            
            if event_type and event.get('event_type') != event_type:
                continue
            
            if protocol and event.get('protocol') != protocol:
                continue
            
            if correlation_id and event.get('correlation_id') != correlation_id:
                continue
            
            # Time-based filtering
            if start_time or end_time:
                event_time = datetime.fromisoformat(
                    event['timestamp'].replace('Z', '+00:00')
                )
                
                if start_time and event_time < start_time:
                    continue
                
                if end_time and event_time > end_time:
                    continue
            
            # Event passes all filters
            results.append(copy.deepcopy(event))
        
        # Sort by timestamp (newest first)
        results.sort(
            key=lambda e: e['timestamp'],
            reverse=True
        )
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        return results
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single event by ID.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Event dictionary or None if not found
        """
        event = self.events.get(event_id)
        return copy.deepcopy(event) if event else None
    
    def close(self) -> None:
        """
        Clear all events from memory.
        
        Note:
            This is idempotent - safe to call multiple times
        """
        self.events.clear()
    
    def count(self) -> int:
        """
        Get total number of events in storage.
        
        Returns:
            Event count
            
        Note:
            This is a convenience method specific to InMemoryStorage
        """
        return len(self.events)