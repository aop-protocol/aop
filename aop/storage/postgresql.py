"""
PostgreSQL storage backend for AOP events.

Production-grade storage suitable for:
- Multi-agent deployments
- High concurrency (10K+ events/sec)
- Distributed systems
- Enterprise environments
- Complex analytics and queries
"""

import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2 import pool, extras
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    psycopg2 = None  # type: ignore

from .base import BaseStorage
from ..exceptions import AOPStorageError


class PostgreSQLStorage(BaseStorage):
    """
    PostgreSQL-based storage implementation with connection pooling.
    
    Provides high-performance, concurrent event storage with advanced
    querying capabilities using PostgreSQL's JSON features.
    
    Connection string format:
        postgresql://user:password@host:5432/database
        postgresql://host/database  # Uses env vars for credentials
    """
    
    def __init__(
        self,
        connection_string: str,
        min_connections: int = 1,
        max_connections: int = 10
    ):
        """
        Initialize PostgreSQL storage with connection pooling.
        
        Args:
            connection_string: PostgreSQL connection string
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
            
        Raises:
            ImportError: If psycopg2 is not installed
            AOPStorageError: If database cannot be initialized
        """
        if not HAS_PSYCOPG2:
            raise ImportError(
                "PostgreSQL support requires psycopg2. "
                "Install with: pip install psycopg2-binary"
            )
        
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        try:
            # Create connection pool
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                connection_string
            )
            
            # Initialize database schema
            self._create_tables()
            
        except Exception as e:
            raise AOPStorageError(
                f"Failed to initialize PostgreSQL storage: {e}",
                operation='init'
            )
    
    def _sanitize_connection_string(self, conn_str: str) -> str:
        """Remove password from connection string for logging."""
        parsed = urlparse(conn_str)
        if parsed.password:
            return conn_str.replace(parsed.password, '***')
        return conn_str
    
    @contextmanager
    def _get_connection(self):
        """Get connection from pool (context manager)."""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    def _create_tables(self) -> None:
        """Create events table and indexes if they don't exist."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Create events table with JSONB for data field
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT PRIMARY KEY,
                        version TEXT NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        agent_id TEXT NOT NULL,
                        instance_id TEXT,
                        protocol TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        correlation_id TEXT,
                        parent_id TEXT,
                        duration_ms INTEGER,
                        data JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for common queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_agent_id 
                    ON events(agent_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_event_type 
                    ON events(event_type)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_protocol 
                    ON events(protocol)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                    ON events(timestamp DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_correlation_id 
                    ON events(correlation_id) 
                    WHERE correlation_id IS NOT NULL
                """)
                
                # GIN index on JSONB for fast JSON queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_data_gin 
                    ON events USING GIN(data)
                """)
                
                conn.commit()
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """
        Store a single AOP event.
        
        Args:
            event: Complete AOP event dictionary
            
        Raises:
            AOPStorageError: If event cannot be stored
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO events (
                            id, version, timestamp, agent_id, instance_id,
                            protocol, event_type, correlation_id, parent_id,
                            duration_ms, data
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (id) DO NOTHING
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
                    conn.commit()
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
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if agent_id:
            query += " AND agent_id = %s"
            params.append(agent_id)
        
        if event_type:
            query += " AND event_type = %s"
            params.append(event_type)
        
        if protocol:
            query += " AND protocol = %s"
            params.append(protocol)
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        if correlation_id:
            query += " AND correlation_id = %s"
            params.append(correlation_id)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    events = []
                    for row in rows:
                        event = dict(row)
                        # Convert timestamp to ISO string
                        event['timestamp'] = event['timestamp'].isoformat()
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
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM events WHERE id = %s",
                        (event_id,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        event = dict(row)
                        event['timestamp'] = event['timestamp'].isoformat()
                        event.pop('created_at', None)
                        return event
                    
                    return None
        except Exception as e:
            raise AOPStorageError(
                f"Failed to get event: {e}",
                operation='get_event'
            )
    
    def close(self) -> None:
        """Close all connections in the pool."""
        if hasattr(self, 'pool') and self.pool:
            self.pool.closeall()