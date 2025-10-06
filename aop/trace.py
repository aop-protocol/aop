"""
Trace context manager for automatic correlation ID handling.
"""

from contextvars import ContextVar
from typing import Optional, Generator
from contextlib import contextmanager

# Thread-safe storage for current correlation ID
_current_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_current_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return _current_correlation_id.get()


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set the current correlation ID in context."""
    _current_correlation_id.set(correlation_id)


@contextmanager
def trace_context(correlation_id: str) -> Generator[None, None, None]:
    """
    Context manager for automatic correlation ID handling.
    
    All events logged within this context will automatically
    receive the specified correlation_id.
    
    Args:
        correlation_id: Correlation ID for this trace
        
    Example:
        >>> with trace_context('trace-123'):
        ...     client.mcp.log_tool_call(...)  # Auto-correlated
        ...     client.a2a.log_task(...)       # Auto-correlated
    """
    # Save previous correlation ID (for nesting support)
    previous = get_current_correlation_id()
    
    try:
        # Set new correlation ID
        set_correlation_id(correlation_id)
        yield
    finally:
        # Restore previous correlation ID
        set_correlation_id(previous)