"""
SQLite storage backend for AOP events.

File-based storage suitable for:
- Development and testing
- Single-agent deployments
- Embedded applications
- Scenarios with <1000 events/sec throughput
"""

from pathlib import Path
import sqlite3
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

from .base import BaseStorage
from ..exceptions import AOPStorageError


class SQLiteStorage(BaseStorage):
    """
    SQLite-based storage implementation.
    
    Stores events in a local SQLite database file with support for
    querying, filtering, and retrieval.
    
    Connection string format:
        sqlite:///path/to/file.db         # Absolute path
        sqlite://./relative/path.db       # Relative path
        sqlite://:memory:                  # In-memory SQLite
    """
    
    def __init__(self, connection_string: str = "sqlite:///aop_events.db"):
        """
        Initialize SQLite storage.
        
        Args:
            connection_string: SQLite connection string
            
        Raises:
            AOPStorageError: If database cannot be initialized
        """
        self.connection_string = connection_string
        self.db_path = self._parse_connection_string(connection_string)
        self.conn: Optional[sqlite3.Connection] = None
        
        try:
            # Create parent directory if it doesn't exist
            storage_path = Path(self.db_path)
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
        except (sqlite3.Error, OSError, IOError) as e:
            raise AOPStorageError(
                f"Failed to initialize SQLite storage: {e}",
                operation='init'
            )
    
    def _parse_connection_string(self, connection_string: str) -> str:
        """
        Parse SQLite connection string to extract file path.
        
        Args:
            connection_string: Connection string to parse
            
        Returns:
            Database file path
        """
        if connection_string.startswith('sqlite:///'):
            # sqlite:///path/to/file.db -> /path/to/file.db
            return connection_string[10:]
        elif connection_string.startswith('sqlite://'):
            # sqlite://./path/to/file.db -> ./path/to/file.db
            parsed = urlparse(connection_string)
            return parsed.path[1:] if parsed.path.startswith('/') else parsed.path
        else:
            # Assume it's a direct file path
            return connection_string
    
    def _create_tables(self) -> None:
        """Create events table if it doesn't exist."""
        assert self.conn is not None, "Connection must be initialized"
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                instance_id TEXT,
                protocol TEXT NOT NULL,
                event_type TEXT NOT NULL,
                correlation_id TEXT,
                parent_id TEXT,
                duration_ms INTEGER,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            CREATE INDEX IF NOT EXISTS idx_protocol 
            ON events(protocol)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON events(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_correlation_id 
            ON events(correlation_id)
        """)
        
        self.conn.commit()
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """
        Store a single AOP event.
        
        Args:
            event: Complete AOP event dictionary
            
        Raises:
            AOPStorageError: If event cannot be stored
        """
        assert self.conn is not None, "Connection must be initialized"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO events (
                    id, version, timestamp, agent_id, instance_id,
                    protocol, event_type, correlation_id, parent_id,
                    duration_ms, data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event['id'],
                event['version'],
                event['timestamp'],
                event['agent_id'],
                event.get('instance_id'),
                event['protocol'],
                event['event_type'],
                event.get('correlation_id'),
                event.get('parent_id'),
                event.get('duration_ms'),
                json.dumps(event.get('data', {}))
            ))
            self.conn.commit()
        except Exception as e:
            raise AOPStorageError(
                f"Failed to log event: {e}",
                operation='log_event'
            )
    
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
            event_type: Filter by event type
            protocol: Filter by protocol
            start_time: Events after this timestamp
            end_time: Events before this timestamp
            correlation_id: Filter by correlation ID
            limit: Maximum number of events
            
        Returns:
            List of matching events
        """
        assert self.conn is not None, "Connection must be initialized"
        
        query = "SELECT * FROM events WHERE 1=1"
        params: List[Any] = []
        
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        if correlation_id:
            query += " AND correlation_id = ?"
            params.append(correlation_id)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                event = dict(row)
                event['data'] = json.loads(event['data'])
                # Remove internal created_at field
                event.pop('created_at', None)
                events.append(event)
            
            return events
        except Exception as e:
            raise AOPStorageError(
                f"Failed to query events: {e}",
                operation='query_events'
            )
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single event by ID.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Event dictionary or None if not found
        """
        assert self.conn is not None, "Connection must be initialized"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            
            if row:
                event = dict(row)
                event['data'] = json.loads(event['data'])
                event.pop('created_at', None)
                return event
            
            return None
        except Exception as e:
            raise AOPStorageError(
                f"Failed to get event: {e}",
                operation='get_event'
            )
    
    def close(self) -> None:
        """Close database connection."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()