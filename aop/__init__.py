"""
AOP (Agentic Observability Protocol)
A standardized protocol for AI agent observability across MCP, A2A, and AP2 protocols.

Usage:
    >>> from aop import AOPClient
    >>> 
    >>> # Initialize client
    >>> client = AOPClient('aop_events.db')
    >>> 
    >>> # Log an event
    >>> client.log_event({
    ...     'agent_id': 'my-agent',
    ...     'event_type': 'mcp.tool.called',
    ...     'data': {'tool_name': 'search'}
    ... })
    >>> 
    >>> # Query events
    >>> events = client.query(agent_id='my-agent', limit=10)
    >>> 
    >>> # Close client
    >>> client.close()

Or use as context manager:
    >>> with AOPClient('aop_events.db') as client:
    ...     client.log_event({...})
"""

__version__ = "0.1.0"
__author__ = "AOP Contributors"
__license__ = "MIT"

# ============================================================================
# MAIN CLIENT
# ============================================================================

from .client import AOPClient

# ============================================================================
# EVENT BUILDERS
# ============================================================================

from .events import (
    build_event,
    build_mcp_event,
    build_a2a_event,
    build_ap2_event,
    build_tool_call_event,
    build_tool_result_event,
    build_task_event,
    build_payment_event,
    build_error_event
)

# ============================================================================
# TYPES & ENUMS
# ============================================================================

from .types import (
    Protocol,
    Severity,
    MCPEventType,
    A2AEventType,
    AP2EventType,
    VERSION,
    SUPPORTED_PROTOCOLS,
    ALL_EVENT_TYPES
)

# ============================================================================
# EXCEPTIONS
# ============================================================================

from .exceptions import (
    AOPException,
    AOPValidationError,
    AOPStorageError,
    AOPEventError,
    AOPProtocolError,
    AOPConfigError
)

# ============================================================================
# VALIDATION
# ============================================================================

from .validation import validate_event

# ============================================================================
# UTILITIES
# ============================================================================

from .utils import (
    generate_uuid_v7,
    get_timestamp,
    validate_uuid,
    validate_timestamp,
    validate_protocol,
    validate_event_type_format,
    validate_severity
)

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Version
    '__version__',
    
    # Main Client
    'AOPClient',
    
    # Event Builders
    'build_event',
    'build_mcp_event',
    'build_a2a_event',
    'build_ap2_event',
    'build_tool_call_event',
    'build_tool_result_event',
    'build_task_event',
    'build_payment_event',
    'build_error_event',
    
    # Types & Enums
    'Protocol',
    'Severity',
    'MCPEventType',
    'A2AEventType',
    'AP2EventType',
    'VERSION',
    'SUPPORTED_PROTOCOLS',
    'ALL_EVENT_TYPES',
    
    # Exceptions
    'AOPException',
    'AOPValidationError',
    'AOPStorageError',
    'AOPEventError',
    'AOPProtocolError',
    'AOPConfigError',
    
    # Validation
    'validate_event',
    
    # Utilities
    'generate_uuid_v7',
    'get_timestamp',
    'validate_uuid',
    'validate_timestamp',
    'validate_protocol',
    'validate_event_type_format',
    'validate_severity',
]