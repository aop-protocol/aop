"""
AOP Client
Main client class for logging and querying AOP events.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager

from .types import AOPEvent
from .validation import validate_event
from .events import build_event
from .exceptions import AOPStorageError, AOPValidationError


class AOPClient:
    """
    AOP Client for logging and querying observability events.
    
    The client handles:
    - Event validation
    - Storage (SQLite by default)
    - Querying events
    - Trace reconstruction
    
    Example:
        >>> client = AOPClient('aop_events.db')
        >>> client.log_event({
        ...     'agent_id': 'my-agent',
        ...     'event_type': 'mcp.tool.called',
        ...     'data': {'tool_name': 'search'}
        ... })
        >>> events = client.query(agent_id='my-agent')
        >>> client.close()
        
    Or use as context manager:
        >>> with AOPClient('aop_events.db') as client:
        ...     client.log_event({...})
    """
    
    def __init__(self, storage_path: str = 'aop_events.db'):
        """
        Initialize AOP client.
        
        Args:
            storage_path: Path to SQLite database file (default: 'aop_events.db')
        """
        self.storage_path = storage_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Initialize SQLite storage and create schema if needed."""
        try:
            # Create parent directory if it doesn't exist
            storage_path = Path(self.storage_path)
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.conn = sqlite3.connect(str(storage_path))
            self.conn.row_factory = sqlite3.Row  # Allow dict-like access
            
            # Create schema
            self._create_schema()
            
        except Exception as e:
            raise AOPStorageError(
                f"Failed to initialize storage: {str(e)}",
                operation='init',
                context={'storage_path': self.storage_path}
            )
    
    def _create_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        if not self.conn:
            raise AOPStorageError("Database connection not initialized")
        
        try:
            cursor = self.conn.cursor()
            
            # Create events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    instance_id TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    correlation_id TEXT,
                    parent_id TEXT,
                    severity TEXT,
                    duration_ms INTEGER,
                    data TEXT,
                    metadata TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_id 
                ON events(agent_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON events(event_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON events(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_correlation_id 
                ON events(correlation_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_protocol 
                ON events(protocol)
            """)
            
            self.conn.commit()
            
        except Exception as e:
            raise AOPStorageError(
                f"Failed to create schema: {str(e)}",
                operation='create_schema'
            )
    
    def log_event(
        self,
        event: Union[Dict[str, Any], AOPEvent],
        validate: bool = True,
        auto_build: bool = True
    ) -> str:
        """
        Log a single event.
        
        Args:
            event: Event dictionary (can be partial if auto_build=True)
            validate: Whether to validate event (default: True)
            auto_build: Whether to auto-fill missing fields (default: True)
            
        Returns:
            str: Event ID
            
        Raises:
            AOPValidationError: If validation fails
            AOPStorageError: If storage operation fails
            
        Example:
            >>> event_id = client.log_event({
            ...     'agent_id': 'my-agent',
            ...     'event_type': 'mcp.tool.called',
            ...     'data': {'tool_name': 'search'}
            ... })
        """
        try:
            # Auto-build if needed
            if auto_build:
                # Check if required fields are missing
                required = ['agent_id', 'event_type']
                if not all(k in event for k in required):
                    raise AOPValidationError(
                        "Event must have at least 'agent_id' and 'event_type' fields"
                    )
                
                # Build complete event
                event = build_event(
                    agent_id=event['agent_id'],
                    event_type=event['event_type'],
                    data=event.get('data'),
                    instance_id=event.get('instance_id'),
                    correlation_id=event.get('correlation_id'),
                    parent_id=event.get('parent_id'),
                    severity=event.get('severity'),
                    duration_ms=event.get('duration_ms'),
                    metadata=event.get('metadata'),
                    error=event.get('error'),
                    validate=validate
                )
            elif validate:
                # Validate without building
                validate_event(event)
            
            # Write to storage
            event_id = self._write_event(event)
            
            return event_id
            
        except (AOPValidationError, AOPStorageError):
            raise
        except Exception as e:
            raise AOPStorageError(
                f"Failed to log event: {str(e)}",
                operation='log_event',
                context={'event_type': event.get('event_type')}
            )
    
    def log_events(
        self,
        events: List[Union[Dict[str, Any], AOPEvent]],
        validate: bool = True,
        auto_build: bool = True
    ) -> List[str]:
        """
        Log multiple events in batch.
        
        More efficient than calling log_event() multiple times.
        
        Args:
            events: List of event dictionaries
            validate: Whether to validate events (default: True)
            auto_build: Whether to auto-fill missing fields (default: True)
            
        Returns:
            List[str]: List of event IDs
            
        Raises:
            AOPValidationError: If validation fails
            AOPStorageError: If storage operation fails
        """
        event_ids = []
        
        for event in events:
            event_id = self.log_event(event, validate=validate, auto_build=auto_build)
            event_ids.append(event_id)
        
        return event_ids
    
    def _write_event(self, event: Dict[str, Any]) -> str:
        """
        Write event to SQLite storage.
        
        Args:
            event: Complete validated event
            
        Returns:
            str: Event ID
        """
        if not self.conn:
            raise AOPStorageError("Database connection not initialized")
        
        try:
            cursor = self.conn.cursor()
            
            # Serialize JSON fields
            data_json = json.dumps(event.get('data')) if event.get('data') else None
            metadata_json = json.dumps(event.get('metadata')) if event.get('metadata') else None
            error_json = json.dumps(event.get('error')) if event.get('error') else None
            
            # Insert event
            cursor.execute("""
                INSERT INTO events (
                    id, version, timestamp, agent_id, instance_id,
                    protocol, event_type, correlation_id, parent_id,
                    severity, duration_ms, data, metadata, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event['id'],
                event['version'],
                event['timestamp'],
                event['agent_id'],
                event['instance_id'],
                event['protocol'],
                event['event_type'],
                event.get('correlation_id'),
                event.get('parent_id'),
                event.get('severity'),
                event.get('duration_ms'),
                data_json,
                metadata_json,
                error_json
            ))
            
            self.conn.commit()
            
            return event['id']
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise AOPStorageError(
                f"Failed to write event: {str(e)}",
                operation='write',
                context={'event_id': event.get('id')}
            )
    
    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        protocol: Optional[str] = None,
        correlation_id: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        order_by: str = 'timestamp',
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query events with filters.
        
        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type
            protocol: Filter by protocol (mcp, a2a, ap2)
            correlation_id: Filter by correlation ID
            severity: Filter by severity level
            start_time: Filter events after this timestamp (ISO 8601)
            end_time: Filter events before this timestamp (ISO 8601)
            limit: Maximum number of events to return (default: 100)
            order_by: Field to order by (default: 'timestamp')
            order_desc: Order descending (default: True)
            
        Returns:
            List[Dict[str, Any]]: List of events
            
        Example:
            >>> events = client.query(
            ...     agent_id='my-agent',
            ...     event_type='mcp.tool.called',
            ...     limit=10
            ... )
        """
        if not self.conn:
            raise AOPStorageError("Database connection not initialized")
        
        try:
            cursor = self.conn.cursor()
            
            # Build query
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if protocol:
                query += " AND protocol = ?"
                params.append(protocol)
            
            if correlation_id:
                query += " AND correlation_id = ?"
                params.append(correlation_id)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            # Add ordering
            order = 'DESC' if order_desc else 'ASC'
            query += f" ORDER BY {order_by} {order}"
            
            # Add limit
            query += " LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dict and deserialize JSON fields
            events = []
            for row in rows:
                event = dict(row)
                
                # Deserialize JSON fields
                if event.get('data'):
                    event['data'] = json.loads(event['data'])
                if event.get('metadata'):
                    event['metadata'] = json.loads(event['metadata'])
                if event.get('error'):
                    event['error'] = json.loads(event['error'])
                
                # Remove created_at (internal field)
                event.pop('created_at', None)
                
                events.append(event)
            
            return events
            
        except Exception as e:
            raise AOPStorageError(
                f"Failed to query events: {str(e)}",
                operation='query'
            )
    
    def get_trace(self, correlation_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a trace by correlation_id.
        
        Returns events ordered by timestamp.
        
        Args:
            correlation_id: Trace correlation ID
            
        Returns:
            List[Dict[str, Any]]: List of events in trace
            
        Example:
            >>> trace = client.get_trace('trace-123')
            >>> print(f"Trace has {len(trace)} events")
        """
        return self.query(
            correlation_id=correlation_id,
            limit=10000,  # Large limit for complete trace
            order_by='timestamp',
            order_desc=False  # Chronological order
        )
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False