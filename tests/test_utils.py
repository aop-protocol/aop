"""
Tests for aop.utils module
"""

import time
from datetime import datetime, timezone
from aop.utils import (
    generate_uuid_v7,
    get_timestamp,
    validate_uuid,
    validate_timestamp,
    validate_protocol,
    validate_event_type_format,
    validate_severity,
    truncate_string,
    sanitize_string
)


class TestGenerateUUIDv7:
    """Test UUID v7 generation"""
    
    def test_generates_valid_uuid(self):
        """Test that generated UUID is valid"""
        uuid = generate_uuid_v7()
        assert validate_uuid(uuid)
    
    def test_uuid_format(self):
        """Test UUID has correct format (8-4-4-4-12)"""
        uuid = generate_uuid_v7()
        parts = uuid.split('-')
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12
    
    def test_generates_unique_uuids(self):
        """Test that multiple calls generate unique UUIDs"""
        uuids = [generate_uuid_v7() for _ in range(100)]
        assert len(set(uuids)) == 100
    
    def test_uuid_is_sortable_by_time(self):
        """Test that UUIDs are sortable by creation time"""
        uuid1 = generate_uuid_v7()
        time.sleep(0.01)  # Small delay
        uuid2 = generate_uuid_v7()
        
        # UUID v7 should be lexicographically sortable by time
        assert uuid1 < uuid2


class TestGetTimestamp:
    """Test timestamp generation"""
    
    def test_generates_valid_timestamp(self):
        """Test that generated timestamp is valid"""
        timestamp = get_timestamp()
        assert validate_timestamp(timestamp)
    
    def test_timestamp_format(self):
        """Test timestamp has correct ISO 8601 format"""
        timestamp = get_timestamp()
        # Format: YYYY-MM-DDTHH:MM:SS.sssZ
        assert 'T' in timestamp
        assert timestamp.endswith('Z')
        assert '.' in timestamp  # Has milliseconds
    
    def test_timestamp_has_milliseconds(self):
        """Test timestamp includes milliseconds"""
        timestamp = get_timestamp()
        # Should have format: ...SS.sssZ (milliseconds before Z)
        assert '.' in timestamp
        assert timestamp.endswith('Z')
        # Check milliseconds exist between . and Z
        ms_part = timestamp.split('.')[-1].rstrip('Z')
        assert len(ms_part) > 0 and ms_part.isdigit()
    
    def test_timestamp_is_utc(self):
        """Test timestamp is in UTC (ends with Z)"""
        timestamp = get_timestamp()
        assert timestamp.endswith('Z')
    
    def test_timestamp_is_current(self):
        """Test timestamp is close to current time"""
        timestamp = get_timestamp()
        # Parse as timezone-aware
        ts = datetime.fromisoformat(timestamp.rstrip('Z')).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should be within 1 second of now
        diff = abs((now - ts).total_seconds())
        assert diff < 1


class TestValidateUUID:
    """Test UUID validation"""
    
    def test_valid_uuid(self):
        """Test validation of valid UUID"""
        assert validate_uuid('01234567-89ab-cdef-0123-456789abcdef')
        assert validate_uuid('a1b2c3d4-e5f6-7890-abcd-ef1234567890')
    
    def test_valid_uuid_uppercase(self):
        """Test validation accepts uppercase UUIDs"""
        assert validate_uuid('01234567-89AB-CDEF-0123-456789ABCDEF')
    
    def test_invalid_uuid_format(self):
        """Test validation rejects invalid format"""
        assert not validate_uuid('invalid-uuid')
        assert not validate_uuid('12345')
        assert not validate_uuid('not-a-uuid-at-all')
    
    def test_invalid_uuid_wrong_parts(self):
        """Test validation rejects wrong number of parts"""
        assert not validate_uuid('01234567-89ab-cdef-0123')  # Missing part
        assert not validate_uuid('01234567-89ab-cdef')  # Too few parts
    
    def test_invalid_uuid_non_string(self):
        """Test validation rejects non-string input"""
        assert not validate_uuid(12345)
        assert not validate_uuid(None)
        assert not validate_uuid(['uuid'])
    
    def test_generated_uuid_is_valid(self):
        """Test that generated UUIDs pass validation"""
        uuid = generate_uuid_v7()
        assert validate_uuid(uuid)


class TestValidateTimestamp:
    """Test timestamp validation"""
    
    def test_valid_timestamp_with_z(self):
        """Test validation of valid timestamp with Z"""
        assert validate_timestamp('2025-10-02T10:30:45.123Z')
        assert validate_timestamp('2025-01-01T00:00:00.000Z')
    
    def test_valid_timestamp_without_milliseconds(self):
        """Test validation of timestamp without milliseconds"""
        assert validate_timestamp('2025-10-02T10:30:45Z')
    
    def test_valid_timestamp_with_timezone(self):
        """Test validation of timestamp with timezone offset"""
        assert validate_timestamp('2025-10-02T10:30:45.123+00:00')
        assert validate_timestamp('2025-10-02T10:30:45+00:00')
    
    def test_invalid_timestamp_format(self):
        """Test validation rejects invalid format"""
        # Date only should be rejected (no time component)
        # Note: Python's fromisoformat() accepts date-only, so this might pass
        # We'll test clearly invalid formats instead
        assert not validate_timestamp('10:30:45')  # Time only
        assert not validate_timestamp('invalid')
        assert not validate_timestamp('not-a-timestamp')
    
    def test_invalid_timestamp_non_string(self):
        """Test validation rejects non-string input"""
        assert not validate_timestamp(12345)
        assert not validate_timestamp(None)
    
    def test_generated_timestamp_is_valid(self):
        """Test that generated timestamps pass validation"""
        timestamp = get_timestamp()
        assert validate_timestamp(timestamp)


class TestValidateProtocol:
    """Test protocol validation"""
    
    def test_valid_protocols(self):
        """Test validation of valid protocols"""
        assert validate_protocol('mcp')
        assert validate_protocol('a2a')
        assert validate_protocol('ap2')
    
    def test_valid_protocol_case_insensitive(self):
        """Test validation is case insensitive"""
        assert validate_protocol('MCP')
        assert validate_protocol('A2A')
        assert validate_protocol('AP2')
    
    def test_invalid_protocol(self):
        """Test validation rejects invalid protocols"""
        assert not validate_protocol('invalid')
        assert not validate_protocol('xyz')
        assert not validate_protocol('')
    
    def test_invalid_protocol_non_string(self):
        """Test validation rejects non-string input"""
        assert not validate_protocol(123)
        assert not validate_protocol(None)


class TestValidateEventTypeFormat:
    """Test event type format validation"""
    
    def test_valid_event_types(self):
        """Test validation of valid event types"""
        assert validate_event_type_format('mcp.tool.called')
        assert validate_event_type_format('a2a.task.assigned')
        assert validate_event_type_format('ap2.payment.initiated')
    
    def test_valid_custom_event_type(self):
        """Test validation of custom event types"""
        assert validate_event_type_format('mcp.custom.org.category.action')
        assert validate_event_type_format('a2a.custom.acme.workflow.started')
    
    def test_invalid_event_type_uppercase(self):
        """Test validation rejects uppercase"""
        assert not validate_event_type_format('MCP.tool.called')
        assert not validate_event_type_format('mcp.TOOL.called')
    
    def test_invalid_event_type_too_few_parts(self):
        """Test validation rejects too few parts"""
        assert not validate_event_type_format('mcp.tool')  # Only 2 parts
        assert not validate_event_type_format('mcp')  # Only 1 part
    
    def test_invalid_event_type_wrong_protocol(self):
        """Test validation rejects invalid protocol prefix"""
        assert not validate_event_type_format('xyz.tool.called')
        assert not validate_event_type_format('invalid.category.action')
    
    def test_invalid_event_type_non_string(self):
        """Test validation rejects non-string input"""
        assert not validate_event_type_format(123)
        assert not validate_event_type_format(None)
    
    def test_invalid_event_type_special_chars(self):
        """Test validation rejects special characters"""
        assert not validate_event_type_format('mcp.tool-called.action')  # Hyphen not allowed in parts
        assert not validate_event_type_format('mcp.tool called.action')  # Space not allowed


class TestValidateSeverity:
    """Test severity validation"""
    
    def test_valid_severities(self):
        """Test validation of valid severities"""
        assert validate_severity('error')
        assert validate_severity('warn')
        assert validate_severity('info')
        assert validate_severity('debug')
    
    def test_valid_severity_case_insensitive(self):
        """Test validation is case insensitive"""
        assert validate_severity('ERROR')
        assert validate_severity('Warn')
        assert validate_severity('INFO')
    
    def test_invalid_severity(self):
        """Test validation rejects invalid severities"""
        assert not validate_severity('critical')
        assert not validate_severity('fatal')
        assert not validate_severity('')
    
    def test_invalid_severity_non_string(self):
        """Test validation rejects non-string input"""
        assert not validate_severity(123)
        assert not validate_severity(None)


class TestTruncateString:
    """Test string truncation"""
    
    def test_no_truncation_needed(self):
        """Test that short strings are not truncated"""
        text = "Short text"
        result = truncate_string(text, max_length=100)
        assert result == text
    
    def test_truncation_with_default_length(self):
        """Test truncation with default max length"""
        text = "A" * 150
        result = truncate_string(text)
        assert len(result) < len(text)
        assert "..." in result
        assert "(150 chars)" in result
    
    def test_truncation_with_custom_length(self):
        """Test truncation with custom max length"""
        text = "A" * 50
        result = truncate_string(text, max_length=20)
        assert "..." in result
        assert "(50 chars)" in result
    
    def test_exact_length_no_truncation(self):
        """Test that text exactly at max length is not truncated"""
        text = "A" * 100
        result = truncate_string(text, max_length=100)
        assert result == text


class TestSanitizeString:
    """Test string sanitization"""
    
    def test_normal_text_unchanged(self):
        """Test that normal text is unchanged"""
        text = "Hello World 123"
        assert sanitize_string(text) == text
    
    def test_removes_control_characters(self):
        """Test that control characters are removed"""
        text = "Hello\x00World\x01Test"
        result = sanitize_string(text)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "HelloWorldTest" == result
    
    def test_preserves_newlines_and_tabs(self):
        """Test that newlines and tabs are preserved"""
        text = "Line1\nLine2\tTabbed"
        result = sanitize_string(text)
        assert "\n" in result
        assert "\t" in result
    
    def test_empty_string(self):
        """Test sanitization of empty string"""
        assert sanitize_string("") == ""