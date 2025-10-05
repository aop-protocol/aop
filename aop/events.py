"""
AOP Event Builders
Helper functions to create AOP events easily and correctly.
"""

from typing import Dict, Any, Optional

from .types import (
    VERSION,
    AOPEvent,
    MCPEventType,
    A2AEventType,
    AP2EventType
)
from .utils import generate_uuid_v7, get_timestamp
from .validation import validate_event
from .exceptions import AOPEventError


# ============================================================================
# GENERIC EVENT BUILDER
# ============================================================================

def build_event(
    agent_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    instance_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    severity: Optional[str] = None,
    duration_ms: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Build a generic AOP event with auto-filled fields.
    
    Auto-filled fields:
    - id: UUID v7 (generated)
    - version: "1.0"
    - timestamp: Current UTC timestamp
    - instance_id: UUID v7 (same as id unless specified)
    - protocol: Extracted from event_type
    
    Args:
        agent_id: Agent identifier (required)
        event_type: Event type (required, e.g., 'mcp.tool.called')
        data: Event-specific data payload
        instance_id: Agent instance ID (auto-generated if not provided)
        correlation_id: Trace correlation ID
        parent_id: Parent span ID
        severity: Event severity (error, warn, info, debug)
        duration_ms: Event duration in milliseconds
        metadata: Additional metadata
        error: Error information
        validate: Whether to validate event before returning (default: True)
        
    Returns:
        Dict[str, Any]: Complete AOP event
        
    Raises:
        AOPEventError: If event creation fails
        AOPValidationError: If validation fails
        
    Example:
        >>> event = build_event(
        ...     agent_id='my-agent',
        ...     event_type='mcp.tool.called',
        ...     data={'tool_name': 'search', 'params': {'query': 'test'}}
        ... )
    """
    try:
        # Extract protocol from event_type
        protocol = event_type.split('.')[0]
        
        # Generate IDs and timestamp
        event_id = generate_uuid_v7()
        timestamp = get_timestamp()
        
        # Use same ID for instance_id if not provided
        if instance_id is None:
            instance_id = event_id
        
        # Build event
        event: Dict[str, Any] = {
            'id': event_id,
            'version': VERSION,
            'timestamp': timestamp,
            'agent_id': agent_id,
            'instance_id': instance_id,
            'protocol': protocol,
            'event_type': event_type
        }
        
        # Add optional fields if provided
        if correlation_id is not None:
            event['correlation_id'] = correlation_id
        
        if parent_id is not None:
            event['parent_id'] = parent_id
        
        if severity is not None:
            event['severity'] = severity
        
        if duration_ms is not None:
            event['duration_ms'] = duration_ms
        
        if data is not None:
            event['data'] = data
        
        if metadata is not None:
            event['metadata'] = metadata
        
        if error is not None:
            event['error'] = error
        
        # Validate if requested
        if validate:
            validate_event(event)
        
        return event
        
    except Exception as e:
        if isinstance(e, AOPEventError):
            raise
        raise AOPEventError(
            f"Failed to build event: {str(e)}",
            event_type=event_type,
            context={'agent_id': agent_id}
        )


# ============================================================================
# PROTOCOL-SPECIFIC BUILDERS
# ============================================================================

def build_mcp_event(
    agent_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an MCP (Model Context Protocol) event.
    
    Validates that event_type starts with 'mcp.'
    
    Args:
        agent_id: Agent identifier
        event_type: MCP event type (must start with 'mcp.')
        data: Event data
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: Complete MCP event
        
    Raises:
        AOPEventError: If event_type doesn't start with 'mcp.'
        
    Example:
        >>> event = build_mcp_event(
        ...     agent_id='my-agent',
        ...     event_type='mcp.tool.called',
        ...     data={'tool_name': 'search'}
        ... )
    """
    if not event_type.startswith('mcp.'):
        raise AOPEventError(
            f"MCP event type must start with 'mcp.', got: {event_type}",
            event_type=event_type
        )
    
    return build_event(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        **kwargs
    )


def build_a2a_event(
    agent_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an A2A (Agent-to-Agent) event.
    
    Validates that event_type starts with 'a2a.'
    
    Args:
        agent_id: Agent identifier
        event_type: A2A event type (must start with 'a2a.')
        data: Event data
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: Complete A2A event
        
    Raises:
        AOPEventError: If event_type doesn't start with 'a2a.'
        
    Example:
        >>> event = build_a2a_event(
        ...     agent_id='orchestrator',
        ...     event_type='a2a.task.assigned',
        ...     data={'task_id': 'task-123', 'assignee': 'worker-1'}
        ... )
    """
    if not event_type.startswith('a2a.'):
        raise AOPEventError(
            f"A2A event type must start with 'a2a.', got: {event_type}",
            event_type=event_type
        )
    
    return build_event(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        **kwargs
    )


def build_ap2_event(
    agent_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an AP2 (Agent Payments) event.
    
    Validates that event_type starts with 'ap2.'
    
    Args:
        agent_id: Agent identifier
        event_type: AP2 event type (must start with 'ap2.')
        data: Event data
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: Complete AP2 event
        
    Raises:
        AOPEventError: If event_type doesn't start with 'ap2.'
        
    Example:
        >>> event = build_ap2_event(
        ...     agent_id='payment-agent',
        ...     event_type='ap2.payment.initiated',
        ...     data={'payment_id': 'pay-123', 'amount': 99.99}
        ... )
    """
    if not event_type.startswith('ap2.'):
        raise AOPEventError(
            f"AP2 event type must start with 'ap2.', got: {event_type}",
            event_type=event_type
        )
    
    return build_event(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        **kwargs
    )


# ============================================================================
# CONVENIENCE BUILDERS (COMMON EVENTS)
# ============================================================================

def build_tool_call_event(
    agent_id: str,
    tool_name: str,
    params: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an MCP tool call event.
    
    Convenience builder for 'mcp.tool.called' events.
    
    Args:
        agent_id: Agent identifier
        tool_name: Name of the tool being called
        params: Tool parameters
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: MCP tool call event
        
    Example:
        >>> event = build_tool_call_event(
        ...     agent_id='my-agent',
        ...     tool_name='web_search',
        ...     params={'query': 'AOP protocol'}
        ... )
    """
    data: Dict[str, Any] = {
        'tool_name': tool_name
    }
    if params is not None:
        data['params'] = params
    
    return build_mcp_event(
        agent_id=agent_id,
        event_type=MCPEventType.TOOL_CALLED,
        data=data,
        **kwargs
    )


def build_tool_result_event(
    agent_id: str,
    tool_name: str,
    result: Any,
    correlation_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an MCP tool result event.
    
    Convenience builder for 'mcp.tool.completed' events.
    
    Args:
        agent_id: Agent identifier
        tool_name: Name of the tool
        result: Tool execution result
        correlation_id: Trace correlation ID
        parent_id: Parent span ID (from tool call)
        duration_ms: Execution duration
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: MCP tool result event
        
    Example:
        >>> event = build_tool_result_event(
        ...     agent_id='my-agent',
        ...     tool_name='web_search',
        ...     result={'results': [...]},
        ...     duration_ms=150
        ... )
    """
    data = {
        'tool_name': tool_name,
        'result': result
    }
    
    return build_mcp_event(
        agent_id=agent_id,
        event_type=MCPEventType.TOOL_COMPLETED,
        data=data,
        correlation_id=correlation_id,
        parent_id=parent_id,
        duration_ms=duration_ms,
        **kwargs
    )


def build_task_event(
    agent_id: str,
    task_type: str,
    task_id: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an A2A task assigned event.
    
    Convenience builder for 'a2a.task.assigned' events.
    
    Args:
        agent_id: Agent identifier (assigner)
        task_type: Type of task
        task_id: Unique task identifier
        description: Task description
        assignee: Agent assigned to the task
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: A2A task event
        
    Example:
        >>> event = build_task_event(
        ...     agent_id='orchestrator',
        ...     task_type='research',
        ...     task_id='task-123',
        ...     description='Research market trends',
        ...     assignee='research-agent'
        ... )
    """
    task_data: Dict[str, Any] = {
        'task_type': task_type,
        'task_id': task_id
    }
    if description is not None:
        task_data['description'] = description
    if assignee is not None:
        task_data['assignee'] = assignee
    
    return build_a2a_event(
        agent_id=agent_id,
        event_type=A2AEventType.TASK_ASSIGNED,
        data=task_data,
        **kwargs
    )


def build_payment_event(
    agent_id: str,
    payment_id: str,
    amount: float,
    currency: str,
    payment_method: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an AP2 payment initiated event.
    
    Convenience builder for 'ap2.payment.initiated' events.
    
    Args:
        agent_id: Agent identifier
        payment_id: Unique payment identifier
        amount: Payment amount
        currency: Currency code (ISO 4217)
        payment_method: Payment method type
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: AP2 payment event
        
    Example:
        >>> event = build_payment_event(
        ...     agent_id='payment-agent',
        ...     payment_id='pay-123',
        ...     amount=99.99,
        ...     currency='USD',
        ...     payment_method='CARD'
        ... )
    """
    data = {
        'payment_id': payment_id,
        'amount': amount,
        'currency': currency
    }
    if payment_method is not None:
        data['payment_method'] = payment_method
    
    return build_ap2_event(
        agent_id=agent_id,
        event_type=AP2EventType.PAYMENT_INITIATED,
        data=data,
        **kwargs
    )


def build_error_event(
    agent_id: str,
    protocol: str,
    error_code: str,
    error_message: str,
    event_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    stack_trace: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build an error event for any protocol.
    
    Args:
        agent_id: Agent identifier
        protocol: Protocol type (mcp, a2a, ap2)
        error_code: Error code
        error_message: Error message
        event_type: Specific error event type (default: protocol.error)
        details: Additional error details
        stack_trace: Stack trace
        **kwargs: Additional optional fields
        
    Returns:
        Dict[str, Any]: Error event
        
    Example:
        >>> event = build_error_event(
        ...     agent_id='my-agent',
        ...     protocol='mcp',
        ...     error_code='TOOL_EXECUTION_ERROR',
        ...     error_message='Tool execution failed',
        ...     details={'tool': 'search'}
        ... )
    """
    # Determine event_type if not provided
    event_type_str: str
    if event_type is None:
        if protocol == 'mcp':
            event_type_str = MCPEventType.ERROR
        else:
            event_type_str = f"{protocol}.error.occurred"
    else:
        event_type_str = event_type
    
    error_data: Dict[str, Any] = {
        'code': error_code,
        'message': error_message
    }
    if details is not None:
        error_data['details'] = details
    if stack_trace is not None:
        error_data['stack_trace'] = stack_trace
    
    return build_event(
        agent_id=agent_id,
        event_type=event_type_str,
        error=error_data,
        severity='error',
        **kwargs
    )