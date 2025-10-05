"""
AOP Custom Exceptions
Contains all custom exception classes for error handling.
"""

from typing import Optional, Dict, Any


class AOPException(Exception):
    """
    Base exception for all AOP-related errors.
    
    All AOP exceptions inherit from this base class for easy catching.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize AOP exception.
        
        Args:
            message: Error message
            context: Optional context data for debugging
        """
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """String representation of the exception."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (context: {context_str})"
        return self.message


class AOPValidationError(AOPException):
    """
    Raised when event validation fails.
    
    Examples:
        - Missing required fields
        - Invalid field types
        - Invalid event_type format
        - Invalid protocol value
        - Field constraint violations
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Name of the field that failed validation
            value: The invalid value
            context: Additional context
        """
        self.field = field
        self.value = value
        
        error_context = context or {}
        if field:
            error_context['field'] = field
        if value is not None:
            error_context['value'] = value
        
        super().__init__(message, error_context)


class AOPStorageError(AOPException):
    """
    Raised when storage operations fail.
    
    Examples:
        - Database connection failed
        - Write operation failed
        - Query execution failed
        - Storage backend unavailable
        - Disk full or permission issues
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize storage error.
        
        Args:
            message: Error message
            operation: The storage operation that failed (e.g., 'write', 'query')
            context: Additional context
        """
        self.operation = operation
        
        error_context = context or {}
        if operation:
            error_context['operation'] = operation
        
        super().__init__(message, error_context)


class AOPEventError(AOPException):
    """
    Raised when event creation or building fails.
    
    Examples:
        - Event builder misconfiguration
        - Invalid event data structure
        - Event serialization failed
        - Event data type mismatch
    """
    
    def __init__(
        self,
        message: str,
        event_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize event error.
        
        Args:
            message: Error message
            event_type: The event type that failed
            context: Additional context
        """
        self.event_type = event_type
        
        error_context = context or {}
        if event_type:
            error_context['event_type'] = event_type
        
        super().__init__(message, error_context)


class AOPProtocolError(AOPException):
    """
    Raised when protocol-specific rules are violated.
    
    Examples:
        - Invalid MCP tool call structure
        - Invalid A2A task format
        - Invalid AP2 mandate structure
        - Protocol-specific field missing
        - Protocol version mismatch
    """
    
    def __init__(
        self,
        message: str,
        protocol: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize protocol error.
        
        Args:
            message: Error message
            protocol: The protocol that raised the error (mcp, a2a, ap2)
            context: Additional context
        """
        self.protocol = protocol
        
        error_context = context or {}
        if protocol:
            error_context['protocol'] = protocol
        
        super().__init__(message, error_context)


class AOPConfigError(AOPException):
    """
    Raised when client configuration is invalid.
    
    Examples:
        - Missing required configuration
        - Invalid storage backend configuration
        - Invalid client initialization parameters
        - Configuration file parsing failed
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: The configuration key that's invalid
            context: Additional context
        """
        self.config_key = config_key
        
        error_context = context or {}
        if config_key:
            error_context['config_key'] = config_key
        
        super().__init__(message, error_context)