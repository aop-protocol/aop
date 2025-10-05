"""
Tests for aop.validation module
"""

import pytest
from aop.validation import (
    validate_required_fields,
    validate_field_types,
    validate_field_formats,
    validate_field_constraints,
    validate_event_type_for_protocol,
    validate_event_type_exists,
    validate_error_field,
    validate_event
)
from aop.exceptions import AOPValidationError
from aop.utils import generate_uuid_v7, get_timestamp


class TestValidateRequiredFields:
    """Test required fields validation"""
    
    def test_valid_event_with_all_required_fields(self):
        """Test that event with all required fields passes"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': 'test-agent',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        validate_required_fields(event)  # Should not raise
    
    def test_missing_single_required_field(self):
        """Test that missing single required field raises error"""
        event = {
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': 'test-agent',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
            # Missing 'id'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_required_fields(event)
        assert 'id' in str(exc_info.value)
    
    def test_missing_multiple_required_fields(self):
        """Test that missing multiple required fields raises error"""
        event = {
            'version': '1.0',
            'timestamp': get_timestamp()
            # Missing: id, agent_id, instance_id, protocol, event_type
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_required_fields(event)
        error_msg = str(exc_info.value)
        assert 'id' in error_msg
        assert 'agent_id' in error_msg
    
    def test_required_field_is_none(self):
        """Test that None value for required field raises error"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': None,  # None value
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_required_fields(event)
        assert 'agent_id' in str(exc_info.value)


class TestValidateFieldTypes:
    """Test field type validation"""
    
    def test_valid_field_types(self):
        """Test that correct field types pass validation"""
        event = {
            'id': 'uuid-string',
            'version': '1.0',
            'timestamp': '2025-10-02T10:30:45Z',
            'agent_id': 'test-agent',
            'severity': 'info',
            'duration_ms': 100,
            'data': {'key': 'value'},
            'metadata': {'meta': 'data'},
            'error': {'code': 'ERR', 'message': 'error'}
        }
        validate_field_types(event)  # Should not raise
    
    def test_invalid_string_field_type(self):
        """Test that non-string for string field raises error"""
        event = {
            'id': 123,  # Should be string
            'version': '1.0'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_types(event)
        assert 'id' in str(exc_info.value)
    
    def test_invalid_duration_ms_type(self):
        """Test that non-integer duration_ms raises error"""
        event = {
            'duration_ms': '100'  # Should be int
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_types(event)
        assert 'duration_ms' in str(exc_info.value)
    
    def test_invalid_dict_field_type(self):
        """Test that non-dict for dict field raises error"""
        event = {
            'data': 'not a dict'  # Should be dict
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_types(event)
        assert 'data' in str(exc_info.value)


class TestValidateFieldFormats:
    """Test field format validation"""
    
    def test_valid_field_formats(self):
        """Test that valid formats pass validation"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called',
            'severity': 'info'
        }
        validate_field_formats(event)  # Should not raise
    
    def test_invalid_id_format(self):
        """Test that invalid UUID for id raises error"""
        event = {
            'id': 'not-a-uuid',
            'version': '1.0',
            'timestamp': get_timestamp(),
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_formats(event)
        assert 'id' in str(exc_info.value)
    
    def test_invalid_version(self):
        """Test that wrong version raises error"""
        event = {
            'id': generate_uuid_v7(),
            'version': '2.0',  # Should be '1.0'
            'timestamp': get_timestamp(),
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_formats(event)
        assert 'version' in str(exc_info.value)
    
    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp raises error"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': 'not-a-timestamp',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_formats(event)
        assert 'timestamp' in str(exc_info.value)
    
    def test_invalid_protocol(self):
        """Test that invalid protocol raises error"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'instance_id': generate_uuid_v7(),
            'protocol': 'invalid',
            'event_type': 'mcp.tool.called'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_formats(event)
        assert 'protocol' in str(exc_info.value)
    
    def test_invalid_event_type_format(self):
        """Test that invalid event_type format raises error"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'INVALID.FORMAT'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_formats(event)
        assert 'event_type' in str(exc_info.value)


class TestValidateFieldConstraints:
    """Test field constraint validation"""
    
    def test_valid_agent_id(self):
        """Test that valid agent_id passes"""
        event = {
            'agent_id': 'test-agent-123'
        }
        validate_field_constraints(event)  # Should not raise
    
    def test_agent_id_too_short(self):
        """Test that empty agent_id raises error"""
        event = {
            'agent_id': ''
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_constraints(event)
        assert 'agent_id' in str(exc_info.value)
    
    def test_agent_id_too_long(self):
        """Test that agent_id > 255 chars raises error"""
        event = {
            'agent_id': 'a' * 256
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_constraints(event)
        assert 'agent_id' in str(exc_info.value)
    
    def test_agent_id_invalid_characters(self):
        """Test that agent_id with invalid chars raises error"""
        event = {
            'agent_id': 'agent@invalid'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_constraints(event)
        assert 'agent_id' in str(exc_info.value)
    
    def test_negative_duration_ms(self):
        """Test that negative duration_ms raises error"""
        event = {
            'agent_id': 'test-agent',
            'duration_ms': -1
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_field_constraints(event)
        assert 'duration_ms' in str(exc_info.value)
    
    def test_zero_duration_ms_allowed(self):
        """Test that zero duration_ms is allowed"""
        event = {
            'agent_id': 'test-agent',
            'duration_ms': 0
        }
        validate_field_constraints(event)  # Should not raise


class TestValidateEventTypeForProtocol:
    """Test event type protocol matching"""
    
    def test_mcp_event_type_matches_protocol(self):
        """Test that MCP event type matches MCP protocol"""
        event = {
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        validate_event_type_for_protocol(event)  # Should not raise
    
    def test_event_type_protocol_mismatch(self):
        """Test that mismatched protocol raises error"""
        event = {
            'protocol': 'mcp',
            'event_type': 'a2a.task.assigned'  # Wrong protocol
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_event_type_for_protocol(event)
        assert 'event_type' in str(exc_info.value)
        assert 'mcp.' in str(exc_info.value)


class TestValidateEventTypeExists:
    """Test event type existence validation"""
    
    def test_known_event_type(self):
        """Test that known event type passes"""
        event = {
            'event_type': 'mcp.tool.called'
        }
        validate_event_type_exists(event)  # Should not raise
    
    def test_valid_custom_event_type(self):
        """Test that valid custom event type passes"""
        event = {
            'event_type': 'mcp.custom.org.category.action'
        }
        validate_event_type_exists(event)  # Should not raise
    
    def test_unknown_non_custom_event_type(self):
        """Test that unknown non-custom event type raises error"""
        event = {
            'event_type': 'mcp.unknown.action'
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_event_type_exists(event)
        assert 'unknown' in str(exc_info.value).lower()


class TestValidateErrorField:
    """Test error field validation"""
    
    def test_valid_error_field(self):
        """Test that valid error field passes"""
        event = {
            'error': {
                'code': 'ERR001',
                'message': 'Something went wrong'
            }
        }
        validate_error_field(event)  # Should not raise
    
    def test_error_field_with_optional_fields(self):
        """Test error field with optional fields"""
        event = {
            'error': {
                'code': 'ERR001',
                'message': 'Error occurred',
                'details': {'info': 'extra'},
                'stack_trace': 'line 1\nline 2'
            }
        }
        validate_error_field(event)  # Should not raise
    
    def test_error_field_missing_code(self):
        """Test that error without code raises error"""
        event = {
            'error': {
                'message': 'Error occurred'
            }
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_error_field(event)
        assert 'code' in str(exc_info.value)
    
    def test_error_field_missing_message(self):
        """Test that error without message raises error"""
        event = {
            'error': {
                'code': 'ERR001'
            }
        }
        with pytest.raises(AOPValidationError) as exc_info:
            validate_error_field(event)
        assert 'message' in str(exc_info.value)


class TestValidateEvent:
    """Test master validation function"""
    
    def test_complete_valid_event(self):
        """Test that complete valid event passes all validation"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': 'test-agent',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called',
            'correlation_id': 'trace-123',
            'severity': 'info',
            'duration_ms': 100,
            'data': {'tool_name': 'search'}
        }
        validate_event(event)  # Should not raise
    
    def test_minimal_valid_event(self):
        """Test that minimal valid event passes"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': 'test-agent',
            'instance_id': generate_uuid_v7(),
            'protocol': 'a2a',
            'event_type': 'a2a.task.assigned'
        }
        validate_event(event)  # Should not raise
    
    def test_event_with_error_field(self):
        """Test that event with error field validates correctly"""
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': 'test-agent',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.error.found',
            'severity': 'error',
            'error': {
                'code': 'TOOL_ERROR',
                'message': 'Tool execution failed'
            }
        }
        validate_event(event)  # Should not raise
    
    def test_invalid_event_fails_validation(self):
        """Test that invalid event raises error"""
        event = {
            'id': 'invalid-uuid',
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': 'test-agent',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        with pytest.raises(AOPValidationError):
            validate_event(event)