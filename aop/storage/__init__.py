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
    
    # Normalize to lowercase for comparison
    conn_lower = connection_string.lower()
    
    # Handle simple 'memory' keyword
    if conn_lower == 'memory' or conn_lower == 'memory://':
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

        elif scheme == 'clickhouse' or scheme == 'clickhouse+secure':
            from .clickhouse import ClickHouseStorage
            return ClickHouseStorage(connection_string)

        elif scheme == 's3':
            from .s3 import S3ArchiveStorage
            return S3ArchiveStorage(connection_string)

        else:
            raise ValueError(
                f"Unsupported storage backend: '{scheme}'. "
                f"Supported backends: sqlite, postgresql, clickhouse, s3, memory"
            )
            
    except ValueError:
        # Re-raise ValueError as-is (already formatted)
        raise
    except Exception as e:
        # Wrap other exceptions in ValueError with original error type
        raise ValueError(
            f"Invalid connection string format: '{connection_string}'. "
            f"Error: {type(e).__name__}: {str(e)}"
        )


# Public API exports
__all__ = [
    'BaseStorage',
    'SQLiteStorage',
    'PostgreSQLStorage',
    'InMemoryStorage',
    'create_storage',
]


# Re-export migration helpers / retention runner ----------------------------
def migrate(connection_string: str, target=None):
    """Run schema migrations on the given storage URL."""
    from .migrations import migrate as _migrate
    return _migrate(connection_string, target=target)


def apply_retention(connection_string: str, *, max_age_days=None,
                    tenant_id=None, dry_run=False):
    """Purge events past their retention window."""
    from .retention import apply_retention as _retention
    return _retention(connection_string, max_age_days=max_age_days,
                      tenant_id=tenant_id, dry_run=dry_run)