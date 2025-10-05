"""
AOP Storage Module

Provides pluggable storage backends for AOP events.

Supported backends:
- SQLite: sqlite:///path/to/file.db (default)
- PostgreSQL: postgresql://user:pass@host:5432/dbname
- In-Memory: memory

Usage:
    >>> from aop.storage import create_storage
    >>> storage = create_storage('postgresql://localhost/aop')
    >>> storage.log_event(event)
"""

from typing import Optional
from urllib.parse import urlparse

from .base import BaseStorage
from .sqlite import SQLiteStorage
from .postgresql import PostgreSQLStorage
from .memory import InMemoryStorage


def create_storage(connection_string: Optional[str] = None) -> BaseStorage:
    """
    Factory function to create appropriate storage backend.
    
    Args:
        connection_string: Storage connection string. Defaults to SQLite if None.
        
    Returns:
        Storage backend instance
        
    Raises:
        ValueError: If connection string format is invalid or backend unsupported
        
    Examples:
        >>> # SQLite (default)
        >>> storage = create_storage()
        >>> storage = create_storage('sqlite:///events.db')
        
        >>> # PostgreSQL
        >>> storage = create_storage('postgresql://localhost/aop')
        
        >>> # In-Memory (testing)
        >>> storage = create_storage('memory')
    """
    # Default to SQLite if no connection string provided
    if connection_string is None:
        return SQLiteStorage('sqlite:///aop_events.db')
    
    # Handle simple 'memory' keyword
    if connection_string == 'memory' or connection_string == 'memory://':
        return InMemoryStorage()
    
    # Parse URL-style connection strings
    try:
        parsed = urlparse(connection_string)
        scheme = parsed.scheme.lower()
        
        if scheme == 'sqlite':
            return SQLiteStorage(connection_string)
        
        elif scheme == 'postgresql' or scheme == 'postgres':
            return PostgreSQLStorage(connection_string)
        
        elif scheme == 'memory':
            return InMemoryStorage()
        
        else:
            raise ValueError(
                f"Unsupported storage backend: '{scheme}'. "
                f"Supported backends: sqlite, postgresql, memory"
            )
            
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(
            f"Invalid connection string format: '{connection_string}'. "
            f"Error: {e}"
        )


# Public API exports
__all__ = [
    'BaseStorage',
    'SQLiteStorage',
    'PostgreSQLStorage',
    'InMemoryStorage',
    'create_storage',
]