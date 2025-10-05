"""
AOP Event Validation
Contains validation logic for AOP events to ensure specification compliance.
"""

import re
from typing import Dict, Any, List

from .types import (
    VERSION,
    SUPPORTED_PROTOCOLS,
    ALL_EVENT_TYPES,
    AOPEvent
)
from .exceptions import AOPValidationError
from .utils import (
    validate_uuid,
    validate_timestamp,
    validate_protocol,
    validate_event_type_format,
    validate_severity
)


# ============================================================================
# REQUIRED FIELDS VALIDATION
# ============================================================================

REQUIRED_FIELDS = [
    'id',
    'version',
    'timestamp',
    'agent_id',
    'instance_id',
    'protocol',
    'event_type'
]


def validate_required_fields(event: Dict[str, Any]) -> None:
    """
    Validate that all required fields are present in the event.
    
    Required fields:
    - id, version, timestamp, agent_id, instance_id, protocol, event_type
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If any required field is missing
    """
    missing_fields = []
    
    for field in REQUIRED_FIELDS:
        if field not in event or event[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise AOPValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            context={'missing_fields': missing_fields}
        )


# ============================================================================
# FIELD TYPE VALIDATION
# ============================================================================

def validate_field_types(event: Dict[str, Any]) -> None:
    """
    Validate that all fields have the correct data types.
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If any field has incorrect type
    """
    # String fields
    string_fields = [
        'id', 'version', 'timestamp', 'agent_id', 'instance_id',
        'protocol', 'event_type', 'correlation_id', 'parent_id', 'severity'
    ]
    
    for field in string_fields:
        if field in event and event[field] is not None:
            if not isinstance(event[field], str):
                raise AOPValidationError(
                    f"Field '{field}' must be a string",
                    field=field,
                    value=type(event[field]).__name__
                )
    
    # Integer fields
    if 'duration_ms' in event and event['duration_ms'] is not None:
        if not isinstance(event['duration_ms'], int):
            raise AOPValidationError(
                "Field 'duration_ms' must be an integer",
                field='duration_ms',
                value=type(event['duration_ms']).__name__
            )
    
    # Dict fields
    dict_fields = ['data', 'metadata', 'error']
    for field in dict_fields:
        if field in event and event[field] is not None:
            if not isinstance(event[field], dict):
                raise AOPValidationError(
                    f"Field '{field}' must be a dictionary",
                    field=field,
                    value=type(event[field]).__name__
                )


# ============================================================================
# FIELD FORMAT VALIDATION
# ============================================================================

def validate_field_formats(event: Dict[str, Any]) -> None:
    """
    Validate that all fields follow the correct format.
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If any field has invalid format
    """
    # Validate ID (UUID)
    if not validate_uuid(event['id']):
        raise AOPValidationError(
            "Field 'id' must be a valid UUID",
            field='id',
            value=event['id']
        )
    
    # Validate version
    if event['version'] != VERSION:
        raise AOPValidationError(
            f"Field 'version' must be '{VERSION}'",
            field='version',
            value=event['version']
        )
    
    # Validate timestamp
    if not validate_timestamp(event['timestamp']):
        raise AOPValidationError(
            "Field 'timestamp' must be a valid ISO 8601 timestamp",
            field='timestamp',
            value=event['timestamp']
        )
    
    # Validate instance_id (UUID)
    if not validate_uuid(event['instance_id']):
        raise AOPValidationError(
            "Field 'instance_id' must be a valid UUID",
            field='instance_id',
            value=event['instance_id']
        )
    
    # Validate protocol
    if not validate_protocol(event['protocol']):
        raise AOPValidationError(
            f"Field 'protocol' must be one of: {', '.join(SUPPORTED_PROTOCOLS)}",
            field='protocol',
            value=event['protocol']
        )
    
    # Validate event_type format
    if not validate_event_type_format(event['event_type']):
        raise AOPValidationError(
            "Field 'event_type' must follow format: protocol.category.action",
            field='event_type',
            value=event['event_type']
        )
    
    # Validate severity if present
    if 'severity' in event and event['severity'] is not None:
        if not validate_severity(event['severity']):
            raise AOPValidationError(
                "Field 'severity' must be one of: error, warn, info, debug",
                field='severity',
                value=event['severity']
            )


# ============================================================================
# FIELD CONSTRAINTS VALIDATION
# ============================================================================

def validate_field_constraints(event: Dict[str, Any]) -> None:
    """
    Validate that all fields meet their constraints.
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If any constraint is violated
    """
    # agent_id: 1-255 characters, alphanumeric + hyphens/underscores
    agent_id = event['agent_id']
    if not (1 <= len(agent_id) <= 255):
        raise AOPValidationError(
            "Field 'agent_id' must be between 1 and 255 characters",
            field='agent_id',
            value=f"length={len(agent_id)}"
        )
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        raise AOPValidationError(
            "Field 'agent_id' must contain only alphanumeric characters, hyphens, and underscores",
            field='agent_id',
            value=agent_id
        )
    
    # duration_ms: must be >= 0
    if 'duration_ms' in event and event['duration_ms'] is not None:
        if event['duration_ms'] < 0:
            raise AOPValidationError(
                "Field 'duration_ms' must be >= 0",
                field='duration_ms',
                value=event['duration_ms']
            )
    
    # correlation_id: if present, must not be empty
    if 'correlation_id' in event and event['correlation_id'] is not None:
        if not event['correlation_id'].strip():
            raise AOPValidationError(
                "Field 'correlation_id' must not be empty",
                field='correlation_id'
            )
    
    # parent_id: if present, must not be empty
    if 'parent_id' in event and event['parent_id'] is not None:
        if not event['parent_id'].strip():
            raise AOPValidationError(
                "Field 'parent_id' must not be empty",
                field='parent_id'
            )


# ============================================================================
# PROTOCOL-SPECIFIC VALIDATION
# ============================================================================

def validate_event_type_for_protocol(event: Dict[str, Any]) -> None:
    """
    Validate that event_type matches the protocol.
    
    Rules:
    - MCP events must start with 'mcp.'
    - A2A events must start with 'a2a.'
    - AP2 events must start with 'ap2.'
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If event_type doesn't match protocol
    """
    protocol = event['protocol']
    event_type = event['event_type']
    
    expected_prefix = f"{protocol}."
    
    if not event_type.startswith(expected_prefix):
        raise AOPValidationError(
            f"Event type '{event_type}' must start with '{expected_prefix}' for protocol '{protocol}'",
            field='event_type',
            value=event_type,
            context={'protocol': protocol}
        )


def validate_event_type_exists(event: Dict[str, Any]) -> None:
    """
    Validate that event_type is a known event type or follows custom event pattern.
    
    Known event types are validated against ALL_EVENT_TYPES.
    Custom event types must follow pattern: protocol.custom.org.category.action
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If event_type is invalid
    """
    event_type = event['event_type']
    
    # Check if it's a known event type
    if event_type in ALL_EVENT_TYPES:
        return
    
    # Check if it's a valid custom event type
    parts = event_type.split('.')
    
    # Custom events must have at least 5 parts: protocol.custom.org.category.action
    if len(parts) >= 5 and parts[1] == 'custom':
        return
    
    # Not a known type and not a valid custom type
    raise AOPValidationError(
        f"Unknown event type: '{event_type}'. Must be a standard event type or follow custom pattern: protocol.custom.org.category.action",
        field='event_type',
        value=event_type
    )


# ============================================================================
# ERROR FIELD VALIDATION
# ============================================================================

def validate_error_field(event: Dict[str, Any]) -> None:
    """
    Validate the error field structure if present.
    
    Required subfields in error:
    - code (string)
    - message (string)
    
    Optional subfields:
    - details (dict)
    - stack_trace (string)
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If error field structure is invalid
    """
    if 'error' not in event or event['error'] is None:
        return
    
    error = event['error']
    
    # Check required subfields
    if 'code' not in error or not isinstance(error['code'], str):
        raise AOPValidationError(
            "Error field must contain 'code' (string)",
            field='error.code'
        )
    
    if 'message' not in error or not isinstance(error['message'], str):
        raise AOPValidationError(
            "Error field must contain 'message' (string)",
            field='error.message'
        )
    
    # Validate optional subfields if present
    if 'details' in error and error['details'] is not None:
        if not isinstance(error['details'], dict):
            raise AOPValidationError(
                "Error field 'details' must be a dictionary",
                field='error.details'
            )
    
    if 'stack_trace' in error and error['stack_trace'] is not None:
        if not isinstance(error['stack_trace'], str):
            raise AOPValidationError(
                "Error field 'stack_trace' must be a string",
                field='error.stack_trace'
            )


# ============================================================================
# MASTER VALIDATION FUNCTION
# ============================================================================

def validate_event(event: Dict[str, Any]) -> None:
    """
    Master validation function for AOP events.
    
    Performs complete validation:
    1. Required fields present
    2. Field types correct
    3. Field formats valid
    4. Field constraints met
    5. Event type matches protocol
    6. Error field structure valid
    
    Args:
        event: Event dictionary to validate
        
    Raises:
        AOPValidationError: If any validation check fails
        
    Example:
        >>> event = {
        ...     'id': '01HQRS9XOP2JRBN7K01RGUWZ1W',
        ...     'version': '1.0',
        ...     'timestamp': '2025-10-02T10:30:45.123Z',
        ...     'agent_id': 'my-agent',
        ...     'instance_id': '01HQRS9XOP2JRBN7K01RGUWZ1W',
        ...     'protocol': 'mcp',
        ...     'event_type': 'mcp.tool.called'
        ... }
        >>> validate_event(event)  # Passes validation
    """
    # Step 1: Required fields
    validate_required_fields(event)
    
    # Step 2: Field types
    validate_field_types(event)
    
    # Step 3: Field formats
    validate_field_formats(event)
    
    # Step 4: Field constraints
    validate_field_constraints(event)
    
    # Step 5: Protocol-specific validation
    validate_event_type_for_protocol(event)
    validate_event_type_exists(event)
    
    # Step 6: Error field validation
    validate_error_field(event)