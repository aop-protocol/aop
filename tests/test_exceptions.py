"""
Tests for aop.exceptions module
"""

import pytest
from aop.exceptions import (
    AOPException,
    AOPValidationError,
    AOPStorageError,
    AOPEventError,
    AOPProtocolError,
    AOPConfigError
)


class TestAOPException:
    """Test base AOPException class"""
    
    def test_basic_exception(self):
        """Test basic exception creation"""
        exc = AOPException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.context == {}
    
    def test_exception_with_context(self):
        """Test exception with context data"""
        exc = AOPException("Test error", context={'key': 'value'})
        assert exc.message == "Test error"
        assert exc.context == {'key': 'value'}
        assert "key=value" in str(exc)
    
    def test_exception_inheritance(self):
        """Test that AOPException inherits from Exception"""
        exc = AOPException("Test")
        assert isinstance(exc, Exception)
    
    def test_exception_can_be_raised(self):
        """Test that exception can be raised and caught"""
        with pytest.raises(AOPException) as exc_info:
            raise AOPException("Test error")
        assert "Test error" in str(exc_info.value)


class TestAOPValidationError:
    """Test AOPValidationError class"""
    
    def test_validation_error_inherits_from_aop_exception(self):
        """Test inheritance from AOPException"""
        exc = AOPValidationError("Validation failed")
        assert isinstance(exc, AOPException)
    
    def test_validation_error_basic(self):
        """Test basic validation error"""
        exc = AOPValidationError("Field is required")
        assert exc.message == "Field is required"
        assert exc.field is None
        assert exc.value is None
    
    def test_validation_error_with_field(self):
        """Test validation error with field"""
        exc = AOPValidationError("Invalid field", field="agent_id")
        assert exc.field == "agent_id"
        assert "field=agent_id" in str(exc)
    
    def test_validation_error_with_value(self):
        """Test validation error with value"""
        exc = AOPValidationError("Invalid value", field="age", value=150)
        assert exc.field == "age"
        assert exc.value == 150
        assert "field=age" in str(exc)
        assert "value=150" in str(exc)
    
    def test_validation_error_with_context(self):
        """Test validation error with additional context"""
        exc = AOPValidationError(
            "Invalid event",
            field="event_type",
            context={'expected': 'mcp.tool.called'}
        )
        assert exc.field == "event_type"
        assert "expected=mcp.tool.called" in str(exc)


class TestAOPStorageError:
    """Test AOPStorageError class"""
    
    def test_storage_error_inherits_from_aop_exception(self):
        """Test inheritance from AOPException"""
        exc = AOPStorageError("Storage failed")
        assert isinstance(exc, AOPException)
    
    def test_storage_error_basic(self):
        """Test basic storage error"""
        exc = AOPStorageError("Database connection failed")
        assert exc.message == "Database connection failed"
        assert exc.operation is None
    
    def test_storage_error_with_operation(self):
        """Test storage error with operation"""
        exc = AOPStorageError("Failed to write", operation="write")
        assert exc.operation == "write"
        assert "operation=write" in str(exc)
    
    def test_storage_error_with_context(self):
        """Test storage error with context"""
        exc = AOPStorageError(
            "Query failed",
            operation="query",
            context={'table': 'events', 'error_code': 1234}
        )
        assert exc.operation == "query"
        assert "operation=query" in str(exc)
        assert "table=events" in str(exc)


class TestAOPEventError:
    """Test AOPEventError class"""
    
    def test_event_error_inherits_from_aop_exception(self):
        """Test inheritance from AOPException"""
        exc = AOPEventError("Event creation failed")
        assert isinstance(exc, AOPException)
    
    def test_event_error_basic(self):
        """Test basic event error"""
        exc = AOPEventError("Invalid event data")
        assert exc.message == "Invalid event data"
        assert exc.event_type is None
    
    def test_event_error_with_event_type(self):
        """Test event error with event_type"""
        exc = AOPEventError("Build failed", event_type="mcp.tool.called")
        assert exc.event_type == "mcp.tool.called"
        assert "event_type=mcp.tool.called" in str(exc)
    
    def test_event_error_with_context(self):
        """Test event error with context"""
        exc = AOPEventError(
            "Serialization failed",
            event_type="mcp.tool.called",
            context={'reason': 'Invalid JSON'}
        )
        assert "event_type=mcp.tool.called" in str(exc)
        assert "reason=Invalid JSON" in str(exc)


class TestAOPProtocolError:
    """Test AOPProtocolError class"""
    
    def test_protocol_error_inherits_from_aop_exception(self):
        """Test inheritance from AOPException"""
        exc = AOPProtocolError("Protocol violation")
        assert isinstance(exc, AOPException)
    
    def test_protocol_error_basic(self):
        """Test basic protocol error"""
        exc = AOPProtocolError("Invalid protocol structure")
        assert exc.message == "Invalid protocol structure"
        assert exc.protocol is None
    
    def test_protocol_error_with_protocol(self):
        """Test protocol error with protocol"""
        exc = AOPProtocolError("Invalid MCP event", protocol="mcp")
        assert exc.protocol == "mcp"
        assert "protocol=mcp" in str(exc)
    
    def test_protocol_error_with_context(self):
        """Test protocol error with context"""
        exc = AOPProtocolError(
            "Missing required field",
            protocol="a2a",
            context={'field': 'task_id'}
        )
        assert "protocol=a2a" in str(exc)
        assert "field=task_id" in str(exc)


class TestAOPConfigError:
    """Test AOPConfigError class"""
    
    def test_config_error_inherits_from_aop_exception(self):
        """Test inheritance from AOPException"""
        exc = AOPConfigError("Configuration invalid")
        assert isinstance(exc, AOPException)
    
    def test_config_error_basic(self):
        """Test basic config error"""
        exc = AOPConfigError("Invalid configuration")
        assert exc.message == "Invalid configuration"
        assert exc.config_key is None
    
    def test_config_error_with_config_key(self):
        """Test config error with config_key"""
        exc = AOPConfigError("Invalid value", config_key="storage_path")
        assert exc.config_key == "storage_path"
        assert "config_key=storage_path" in str(exc)
    
    def test_config_error_with_context(self):
        """Test config error with context"""
        exc = AOPConfigError(
            "Parse error",
            config_key="database_url",
            context={'line': 42}
        )
        assert "config_key=database_url" in str(exc)
        assert "line=42" in str(exc)


class TestExceptionHierarchy:
    """Test exception hierarchy and catching"""
    
    def test_can_catch_all_with_base_exception(self):
        """Test that all AOP exceptions can be caught with AOPException"""
        exceptions_to_test = [
            AOPValidationError("test"),
            AOPStorageError("test"),
            AOPEventError("test"),
            AOPProtocolError("test"),
            AOPConfigError("test")
        ]
        
        for exc in exceptions_to_test:
            with pytest.raises(AOPException):
                raise exc
    
    def test_can_catch_specific_exceptions(self):
        """Test that specific exceptions can be caught individually"""
        with pytest.raises(AOPValidationError):
            raise AOPValidationError("validation error")
        
        with pytest.raises(AOPStorageError):
            raise AOPStorageError("storage error")
        
        with pytest.raises(AOPEventError):
            raise AOPEventError("event error")
    
    def test_exception_types_are_distinct(self):
        """Test that exception types are distinct"""
        validation_exc = AOPValidationError("test")
        storage_exc = AOPStorageError("test")
        
        assert type(validation_exc) != type(storage_exc)
        assert isinstance(validation_exc, AOPValidationError)
        assert not isinstance(validation_exc, AOPStorageError)