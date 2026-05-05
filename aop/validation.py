"""
AOP Event Validation
Validation logic for AOP events to ensure specification compliance.

v1.1: Validation now consults the protocol registry instead of a hard-coded
list of three protocols. Events with version "1.0" are still accepted; new
events are written with version "1.1" by default. Optional v1.1 fields
(``trace_id``, ``span_id``, ``parent_span_id``, ``resource``, ``links``,
``attributes``, ``tokens``, ``cost``) are validated only when present.
"""

import re
from typing import Dict, Any

from .types import VERSION
from .exceptions import AOPValidationError
from .registry import (
    supported_protocols,
    all_event_types,
    is_protocol_registered,
    get_protocol,
)
from .utils import (
    validate_uuid,
    validate_timestamp,
    validate_event_type_format,
    validate_severity,
    validate_trace_id,
    validate_span_id,
)

# Accepted spec versions. v1.0 retained for back-compat.
ACCEPTED_VERSIONS = {"1.0", "1.1"}

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
    'event_type',
]


def validate_required_fields(event: Dict[str, Any]) -> None:
    """Ensure all v1.0 required fields are present."""
    missing_fields = [f for f in REQUIRED_FIELDS if f not in event or event[f] is None]
    if missing_fields:
        raise AOPValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            context={'missing_fields': missing_fields},
        )


# ============================================================================
# FIELD TYPE VALIDATION
# ============================================================================


def validate_field_types(event: Dict[str, Any]) -> None:
    """Type-check every field that is present."""
    string_fields = [
        'id', 'version', 'timestamp', 'agent_id', 'instance_id',
        'protocol', 'event_type', 'correlation_id', 'parent_id', 'severity',
        # v1.1
        'trace_id', 'span_id', 'parent_span_id',
    ]
    for field in string_fields:
        if field in event and event[field] is not None:
            if not isinstance(event[field], str):
                raise AOPValidationError(
                    f"Field '{field}' must be a string",
                    field=field, value=type(event[field]).__name__,
                )

    if 'duration_ms' in event and event['duration_ms'] is not None:
        if not isinstance(event['duration_ms'], (int, float)):
            raise AOPValidationError(
                "Field 'duration_ms' must be a number",
                field='duration_ms', value=type(event['duration_ms']).__name__,
            )

    dict_fields = ['data', 'metadata', 'error', 'resource', 'attributes', 'tokens', 'cost']
    for field in dict_fields:
        if field in event and event[field] is not None:
            if not isinstance(event[field], dict):
                raise AOPValidationError(
                    f"Field '{field}' must be a dictionary",
                    field=field, value=type(event[field]).__name__,
                )

    if 'links' in event and event['links'] is not None:
        if not isinstance(event['links'], list):
            raise AOPValidationError(
                "Field 'links' must be a list",
                field='links', value=type(event['links']).__name__,
            )


# ============================================================================
# FIELD FORMAT VALIDATION
# ============================================================================


def validate_field_formats(event: Dict[str, Any]) -> None:
    if not validate_uuid(event['id']):
        raise AOPValidationError(
            "Field 'id' must be a valid UUID",
            field='id', value=event['id'],
        )

    if event['version'] not in ACCEPTED_VERSIONS:
        raise AOPValidationError(
            f"Field 'version' must be one of {sorted(ACCEPTED_VERSIONS)}",
            field='version', value=event['version'],
        )

    if not validate_timestamp(event['timestamp']):
        raise AOPValidationError(
            "Field 'timestamp' must be a valid ISO 8601 timestamp",
            field='timestamp', value=event['timestamp'],
        )

    if not validate_uuid(event['instance_id']):
        raise AOPValidationError(
            "Field 'instance_id' must be a valid UUID",
            field='instance_id', value=event['instance_id'],
        )

    # Protocol must be registered (open-set check, not the legacy list)
    protocol = event['protocol']
    if not is_protocol_registered(protocol):
        raise AOPValidationError(
            f"Field 'protocol' is not registered. Known: {sorted(supported_protocols())}",
            field='protocol', value=protocol,
        )

    if not validate_event_type_format(event['event_type']):
        raise AOPValidationError(
            "Field 'event_type' must follow format: protocol.category.action",
            field='event_type', value=event['event_type'],
        )

    if 'severity' in event and event['severity'] is not None:
        if not validate_severity(event['severity']):
            raise AOPValidationError(
                "Field 'severity' must be one of: error, warn, info, debug",
                field='severity', value=event['severity'],
            )

    # v1.1 trace context format
    if 'trace_id' in event and event['trace_id'] is not None:
        if not validate_trace_id(event['trace_id']):
            raise AOPValidationError(
                "Field 'trace_id' must be a 32-char lowercase hex (W3C TraceContext)",
                field='trace_id', value=event['trace_id'],
            )
    for f in ('span_id', 'parent_span_id'):
        if f in event and event[f] is not None:
            if not validate_span_id(event[f]):
                raise AOPValidationError(
                    f"Field '{f}' must be a 16-char lowercase hex (W3C TraceContext)",
                    field=f, value=event[f],
                )


# ============================================================================
# FIELD CONSTRAINTS VALIDATION
# ============================================================================


def validate_field_constraints(event: Dict[str, Any]) -> None:
    agent_id = event['agent_id']
    if not (1 <= len(agent_id) <= 255):
        raise AOPValidationError(
            "Field 'agent_id' must be between 1 and 255 characters",
            field='agent_id', value=f"length={len(agent_id)}",
        )
    if not re.match(r'^[a-zA-Z0-9_\-:.]+$', agent_id):
        raise AOPValidationError(
            "Field 'agent_id' must contain only alphanumerics, hyphens, underscores, dots, or colons",
            field='agent_id', value=agent_id,
        )

    if 'duration_ms' in event and event['duration_ms'] is not None:
        if event['duration_ms'] < 0:
            raise AOPValidationError(
                "Field 'duration_ms' must be >= 0",
                field='duration_ms', value=event['duration_ms'],
            )

    for f in ('correlation_id', 'parent_id'):
        if f in event and event[f] is not None:
            if not str(event[f]).strip():
                raise AOPValidationError(
                    f"Field '{f}' must not be empty",
                    field=f,
                )


# ============================================================================
# PROTOCOL-SPECIFIC VALIDATION
# ============================================================================


def validate_event_type_for_protocol(event: Dict[str, Any]) -> None:
    protocol = event['protocol']
    event_type = event['event_type']
    expected_prefix = f"{protocol}."
    if not event_type.startswith(expected_prefix):
        raise AOPValidationError(
            f"Event type {event_type!r} must start with {expected_prefix!r}",
            field='event_type', value=event_type,
            context={'protocol': protocol},
        )


def validate_event_type_exists(event: Dict[str, Any]) -> None:
    """Validate event_type either against the registry or a custom-pattern."""
    event_type = event['event_type']
    if event_type in all_event_types():
        return

    parts = event_type.split('.')
    # Custom: <protocol>.custom.<org>.<category>.<action> (>=5 parts)
    if len(parts) >= 5 and parts[1] == 'custom':
        return
    # Experimental: <protocol>.x.<...>  — short escape hatch for new namespaces
    if len(parts) >= 3 and parts[1] == 'x':
        return

    raise AOPValidationError(
        f"Unknown event type: {event_type!r}. Use a registered type or "
        "follow protocol.custom.org.category.action / protocol.x.<...> patterns.",
        field='event_type', value=event_type,
    )


def validate_required_data_keys(event: Dict[str, Any]) -> None:
    """If the spec for this protocol declares required data keys, enforce them."""
    spec = get_protocol(event['protocol'])
    if not spec or not spec.strict_data:
        return
    required = spec.required_data_keys.get(event['event_type'])
    if not required:
        return
    data = event.get('data') or {}
    missing = [k for k in required if k not in data]
    if missing:
        raise AOPValidationError(
            f"data is missing required keys for {event['event_type']}: {missing}",
            field='data', context={'missing_keys': missing},
        )


# ============================================================================
# ERROR FIELD VALIDATION
# ============================================================================


def validate_error_field(event: Dict[str, Any]) -> None:
    if 'error' not in event or event['error'] is None:
        return
    error = event['error']
    if 'code' not in error or not isinstance(error['code'], str):
        raise AOPValidationError(
            "Error field must contain 'code' (string)", field='error.code',
        )
    if 'message' not in error or not isinstance(error['message'], str):
        raise AOPValidationError(
            "Error field must contain 'message' (string)", field='error.message',
        )
    if 'details' in error and error['details'] is not None:
        if not isinstance(error['details'], dict):
            raise AOPValidationError(
                "Error field 'details' must be a dictionary", field='error.details',
            )
    if 'stack_trace' in error and error['stack_trace'] is not None:
        if not isinstance(error['stack_trace'], str):
            raise AOPValidationError(
                "Error field 'stack_trace' must be a string", field='error.stack_trace',
            )


# ============================================================================
# v1.1 EXTENSION FIELDS VALIDATION
# ============================================================================


def validate_tokens_field(event: Dict[str, Any]) -> None:
    if 'tokens' not in event or event['tokens'] is None:
        return
    tokens = event['tokens']
    for k, v in tokens.items():
        if not isinstance(v, int) or v < 0:
            raise AOPValidationError(
                f"tokens.{k} must be a non-negative integer",
                field=f'tokens.{k}', value=v,
            )


def validate_cost_field(event: Dict[str, Any]) -> None:
    if 'cost' not in event or event['cost'] is None:
        return
    cost = event['cost']
    if 'amount' in cost and not isinstance(cost['amount'], (int, float)):
        raise AOPValidationError(
            "cost.amount must be numeric", field='cost.amount', value=cost['amount'],
        )
    if 'amount' in cost and cost['amount'] < 0:
        raise AOPValidationError(
            "cost.amount must be >= 0", field='cost.amount', value=cost['amount'],
        )
    if 'currency' in cost and not isinstance(cost['currency'], str):
        raise AOPValidationError(
            "cost.currency must be a string", field='cost.currency',
        )


# ============================================================================
# MASTER VALIDATION
# ============================================================================


def validate_event(event: Dict[str, Any]) -> None:
    """Run the full validation pipeline on an event dict."""
    validate_required_fields(event)
    validate_field_types(event)
    validate_field_formats(event)
    validate_field_constraints(event)
    validate_event_type_for_protocol(event)
    validate_event_type_exists(event)
    validate_required_data_keys(event)
    validate_error_field(event)
    validate_tokens_field(event)
    validate_cost_field(event)
