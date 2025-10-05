"""
AOP Utility Functions
Contains helper functions for UUID generation, timestamps, and validation.
"""

import uuid
import re
from datetime import datetime, timezone
from typing import Optional

from .types import SUPPORTED_PROTOCOLS


# ============================================================================
# UUID v7 GENERATION
# ============================================================================

def generate_uuid_v7() -> str:
    """
    Generate a UUID v7 (time-ordered UUID).
    
    UUID v7 format: xxxxxxxx-xxxx-7xxx-xxxx-xxxxxxxxxxxx
    - First 48 bits: Unix timestamp in milliseconds
    - Version bits: 0111 (7)
    - Variant bits: 10
    - Remaining bits: Random
    
    Returns:
        str: UUID v7 string in standard format
        
    Example:
        >>> generate_uuid_v7()
        '01HQRS9XOP2JRBN7K01RGUWZ1W'
    """
    # Get current timestamp in milliseconds
    timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    # Generate random bytes for the rest
    random_bytes = uuid.uuid4().bytes
    
    # Construct UUID v7
    # First 48 bits: timestamp
    uuid_int = timestamp_ms << 80
    
    # Version (4 bits): 0111 (7)
    uuid_int |= (7 << 76)
    
    # Variant (2 bits): 10
    uuid_int |= (2 << 62)
    
    # Random bits (62 bits from random UUID)
    uuid_int |= int.from_bytes(random_bytes[6:14], byteorder='big') & 0x3FFFFFFFFFFFFFFF
    
    # Convert to UUID format
    return str(uuid.UUID(int=uuid_int))


# ============================================================================
# TIMESTAMP FUNCTIONS
# ============================================================================

def get_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format with milliseconds.
    
    Format: YYYY-MM-DDTHH:MM:SS.sssZ
    Example: 2025-10-02T10:30:45.123Z
    
    Returns:
        str: ISO 8601 formatted timestamp with 'Z' suffix
        
    Example:
        >>> get_timestamp()
        '2025-10-02T10:30:45.123Z'
    """
    now = datetime.now(timezone.utc)
    # Format with milliseconds and Z suffix
    return now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_uuid(value: str) -> bool:
    """
    Validate if a string is a valid UUID.
    
    Accepts both standard UUID format (with hyphens) and compact format.
    
    Args:
        value: String to validate
        
    Returns:
        bool: True if valid UUID, False otherwise
        
    Example:
        >>> validate_uuid('01HQRS9X-OP2J-7RBN-K01R-GUWZ1W')
        True
        >>> validate_uuid('invalid')
        False
    """
    if not isinstance(value, str):
        return False
    
    # UUID regex pattern (8-4-4-4-12 format)
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    if uuid_pattern.match(value):
        return True
    
    # Also try parsing with uuid library
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_timestamp(value: str) -> bool:
    """
    Validate if a string is a valid ISO 8601 timestamp.
    
    Accepts formats:
    - 2025-10-02T10:30:45.123Z
    - 2025-10-02T10:30:45Z
    - 2025-10-02T10:30:45.123+00:00
    
    Args:
        value: String to validate
        
    Returns:
        bool: True if valid ISO 8601 timestamp, False otherwise
        
    Example:
        >>> validate_timestamp('2025-10-02T10:30:45.123Z')
        True
        >>> validate_timestamp('2025-10-02')
        False
    """
    if not isinstance(value, str):
        return False
    
    # Try parsing as ISO 8601
    try:
        # Remove 'Z' suffix and parse
        timestamp_str = value.rstrip('Z')
        datetime.fromisoformat(timestamp_str)
        return True
    except (ValueError, AttributeError):
        return False


def validate_protocol(value: str) -> bool:
    """
    Validate if a protocol value is supported.
    
    Valid protocols: mcp, a2a, ap2
    
    Args:
        value: Protocol string to validate
        
    Returns:
        bool: True if valid protocol, False otherwise
        
    Example:
        >>> validate_protocol('mcp')
        True
        >>> validate_protocol('xyz')
        False
    """
    if not isinstance(value, str):
        return False
    
    return value.lower() in SUPPORTED_PROTOCOLS


def validate_event_type_format(value: str) -> bool:
    """
    Validate if event_type follows the correct format.
    
    Format: protocol.category.action
    Examples:
    - mcp.tool.called
    - a2a.task.assigned
    - ap2.payment.completed
    - mcp.custom.org.category.action (custom events)
    
    Rules:
    - Must be lowercase
    - Must use dot notation
    - Must have at least 3 parts (protocol.category.action)
    - First part must be valid protocol
    
    Args:
        value: Event type string to validate
        
    Returns:
        bool: True if valid format, False otherwise
        
    Example:
        >>> validate_event_type_format('mcp.tool.called')
        True
        >>> validate_event_type_format('InvalidFormat')
        False
    """
    if not isinstance(value, str):
        return False
    
    # Check if lowercase
    if value != value.lower():
        return False
    
    # Split by dots
    parts = value.split('.')
    
    # Must have at least 3 parts
    if len(parts) < 3:
        return False
    
    # First part must be valid protocol
    if parts[0] not in SUPPORTED_PROTOCOLS:
        return False
    
    # All parts must be non-empty and alphanumeric (with underscores allowed)
    for part in parts:
        if not part or not re.match(r'^[a-z0-9_]+$', part):
            return False
    
    return True


def validate_severity(value: str) -> bool:
    """
    Validate if severity value is valid.
    
    Valid severities: error, warn, info, debug
    
    Args:
        value: Severity string to validate
        
    Returns:
        bool: True if valid severity, False otherwise
        
    Example:
        >>> validate_severity('error')
        True
        >>> validate_severity('critical')
        False
    """
    if not isinstance(value, str):
        return False
    
    valid_severities = ['error', 'warn', 'info', 'debug']
    return value.lower() in valid_severities


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def truncate_string(value: str, max_length: int = 100) -> str:
    """
    Truncate a string to a maximum length with ellipsis.
    
    Useful for logging long values.
    
    Args:
        value: String to truncate
        max_length: Maximum length (default: 100)
        
    Returns:
        str: Truncated string with '...' if needed
        
    Example:
        >>> truncate_string('A' * 150, 100)
        'AAAA...AAAA (150 chars)'
    """
    if len(value) <= max_length:
        return value
    
    return f"{value[:max_length]}... ({len(value)} chars)"


def sanitize_string(value: str) -> str:
    """
    Sanitize a string by removing control characters.
    
    Useful for preventing log injection attacks.
    
    Args:
        value: String to sanitize
        
    Returns:
        str: Sanitized string
    """
    # Remove control characters except newlines and tabs
    return ''.join(char for char in value if char.isprintable() or char in '\n\t')