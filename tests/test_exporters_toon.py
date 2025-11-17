"""
Tests for TOON (Token-Oriented Object Notation) exporter.

Comprehensive test coverage for:
- Core TOON encoder functionality
- AOP event exporter with flattening
- Field filtering
- Delimiter options
- Token savings estimation
"""

import json
import tempfile
from pathlib import Path

import pytest

from aop.exporters import ToonExporter
from aop.exporters.toon_encoder import ToonEncoder, encode


# ============================================================================
# TOON Encoder Tests
# ============================================================================

def test_encoder_basic_types():
    """Test encoding of basic types."""
    encoder = ToonEncoder()

    assert encoder._encode_value(None, 0) == 'null'
    assert encoder._encode_value(True, 0) == 'true'
    assert encoder._encode_value(False, 0) == 'false'
    assert encoder._encode_value(42, 0) == '42'
    assert encoder._encode_value(3.14, 0) == '3.14'


def test_encoder_string_quoting():
    """Test smart string quoting."""
    encoder = ToonEncoder()

    # Simple strings don't need quotes
    assert encoder._quote_string('hello') == 'hello'
    assert encoder._quote_string('test123') == 'test123'

    # Strings with special chars need quotes
    assert encoder._quote_string('hello world') == '"hello world"'
    assert encoder._quote_string('test,value') == '"test,value"'
    assert encoder._quote_string('test|value') == '"test|value"'
    assert encoder._quote_string('test:value') == '"test:value"'

    # Keywords need quotes
    assert encoder._quote_string('null') == '"null"'
    assert encoder._quote_string('true') == '"true"'
    assert encoder._quote_string('false') == '"false"'

    # Number-like strings need quotes
    assert encoder._quote_string('123') == '"123"'
    assert encoder._quote_string('3.14') == '"3.14"'


def test_encoder_string_escaping():
    """Test string escaping in quotes."""
    encoder = ToonEncoder()

    # Quotes are escaped
    result = encoder._quote_string('say "hello"')
    assert result == '"say \\"hello\\""'

    # Backslashes are escaped (when string needs quoting for other reasons)
    result = encoder._quote_string('path\\to\\file with spaces')
    assert '\\\\' in result  # Backslashes should be escaped


def test_encoder_simple_object():
    """Test encoding of simple objects."""
    encoder = ToonEncoder()

    obj = {
        'name': 'test',
        'count': 42,
        'active': True
    }

    result = encoder.encode(obj)

    # Should contain all keys and values
    assert 'name: test' in result
    assert 'count: 42' in result
    assert 'active: true' in result


def test_encoder_nested_object():
    """Test encoding of nested objects."""
    encoder = ToonEncoder()

    obj = {
        'user': {
            'name': 'Alice',
            'age': 30
        }
    }

    result = encoder.encode(obj)

    # Should have nested structure
    assert 'user:' in result
    assert 'name: Alice' in result
    assert 'age: 30' in result


def test_encoder_simple_array():
    """Test encoding of simple arrays."""
    encoder = ToonEncoder()

    # Short array - inline format
    arr = [1, 2, 3]
    result = encoder.encode(arr)
    assert result == '[1, 2, 3]'

    # Empty array
    arr = []
    result = encoder.encode(arr)
    assert result == '[]'


def test_encoder_uniform_object_array():
    """Test tabular format for uniform object arrays (TOON's killer feature)."""
    encoder = ToonEncoder(delimiter='comma')

    events = [
        {'id': 'evt-1', 'name': 'event1', 'count': 100},
        {'id': 'evt-2', 'name': 'event2', 'count': 150}
    ]

    result = encoder.encode(events)

    # Should have tabular header
    assert 'items[2]{id,name,count}:' in result

    # Should have data rows
    assert 'evt-1,event1,100' in result
    assert 'evt-2,event2,150' in result


def test_encoder_non_uniform_array():
    """Test that non-uniform arrays use list format."""
    encoder = ToonEncoder()

    # Mixed types - should use list format
    arr = [
        {'id': 1, 'name': 'test'},
        {'id': 2, 'count': 42}  # Different keys!
    ]

    result = encoder.encode(arr)

    # Should NOT use tabular format
    assert '{id,name,count}' not in result
    # Should use list format
    assert '[' in result


def test_encoder_delimiter_options():
    """Test different delimiter options."""
    events = [
        {'id': 1, 'value': 'a'},
        {'id': 2, 'value': 'b'}
    ]

    # Comma delimiter
    encoder = ToonEncoder(delimiter='comma')
    result = encoder.encode(events)
    assert '1,a' in result and '2,b' in result

    # Tab delimiter
    encoder = ToonEncoder(delimiter='tab')
    result = encoder.encode(events)
    assert '1\ta' in result and '2\tb' in result

    # Pipe delimiter
    encoder = ToonEncoder(delimiter='pipe')
    result = encoder.encode(events)
    assert '1|a' in result and '2|b' in result


def test_encoder_convenience_function():
    """Test convenience encode() function."""
    events = [
        {'id': 1, 'name': 'test1'},
        {'id': 2, 'name': 'test2'}
    ]

    result = encode(events, delimiter='comma')

    assert 'items[2]{id,name}:' in result
    assert '1,test1' in result


# ============================================================================
# TOON Exporter Tests
# ============================================================================

def test_toon_exporter_basic():
    """Test basic TOON export."""
    exporter = ToonExporter()

    events = [
        {'id': 'evt-1', 'event_type': 'test.event', 'agent_id': 'agent-1'},
        {'id': 'evt-2', 'event_type': 'test.event', 'agent_id': 'agent-2'}
    ]

    result = exporter.export(events)

    # Should have TOON format
    assert 'events[2]' in result
    assert 'evt-1' in result
    assert 'evt-2' in result


def test_toon_exporter_flattening():
    """Test field flattening for nested data/metadata/error."""
    exporter = ToonExporter(flatten=True)

    events = [
        {
            'id': 'evt-1',
            'timestamp': '2025-01-15T10:00:00Z',
            'event_type': 'mcp.tool.called',
            'data': {
                'tool_name': 'search',
                'duration_ms': 45
            },
            'metadata': {
                'user_id': 'u123'
            }
        }
    ]

    result = exporter.export(events)

    # Should have flattened field names in header
    assert 'data.tool_name' in result
    assert 'data.duration_ms' in result
    assert 'metadata.user_id' in result


def test_toon_exporter_no_flattening():
    """Test export without flattening (nested structure preserved)."""
    exporter = ToonExporter(flatten=False)

    events = [
        {
            'id': 'evt-1',
            'data': {
                'tool_name': 'search'
            }
        }
    ]

    result = exporter.export(events)

    # Should NOT have flattened fields
    assert 'data.tool_name' not in result
    # Should have nested structure
    assert 'data:' in result


def test_toon_exporter_exclude_fields():
    """Test default exclusion of internal fields."""
    exporter = ToonExporter()

    events = [
        {
            'id': 'evt-1',
            'version': '1.0',
            'instance_id': 'inst-1',
            'event_type': 'test'
        }
    ]

    result = exporter.export(events)

    # version and instance_id should be excluded by default
    assert 'version' not in result
    assert 'instance_id' not in result
    # id and event_type should be included
    assert 'evt-1' in result
    assert 'test' in result


def test_toon_exporter_include_fields():
    """Test include_fields filtering."""
    exporter = ToonExporter(include_fields=['id', 'event_type'])

    events = [
        {
            'id': 'evt-1',
            'event_type': 'test',
            'agent_id': 'agent-1',
            'extra': 'data'
        }
    ]

    result = exporter.export(events)

    # Only included fields should appear
    assert 'evt-1' in result
    assert 'test' in result
    # Other fields excluded
    assert 'agent-1' not in result
    assert 'extra' not in result


def test_toon_exporter_delimiter_options():
    """Test delimiter options in exporter."""
    events = [
        {'id': 'evt-1', 'type': 'test'},
        {'id': 'evt-2', 'type': 'test'}
    ]

    # Comma (default)
    exporter = ToonExporter(delimiter='comma')
    result = exporter.export(events)
    assert 'evt-1,test' in result

    # Tab
    exporter = ToonExporter(delimiter='tab')
    result = exporter.export(events)
    assert 'evt-1\ttest' in result

    # Pipe
    exporter = ToonExporter(delimiter='pipe')
    result = exporter.export(events)
    assert 'evt-1|test' in result


def test_toon_exporter_empty_events():
    """Test exporting empty event list."""
    exporter = ToonExporter()
    result = exporter.export([])
    assert 'events[0]{}:' in result


def test_toon_exporter_export_to_file():
    """Test exporting to file."""
    exporter = ToonExporter(flatten=True)

    events = [
        {'id': 'evt-1', 'data': {'test': 'value'}}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.toon'
        exporter.export_to_file(events, str(filepath))

        assert filepath.exists()

        content = filepath.read_text()
        assert 'evt-1' in content
        assert 'data.test' in content


def test_toon_exporter_token_estimate():
    """Test token savings estimation."""
    exporter = ToonExporter(flatten=True)

    # Create 100 uniform events (ideal for TOON)
    events = [
        {
            'id': f'evt-{i}',
            'timestamp': '2025-01-15T10:00:00Z',
            'event_type': 'mcp.tool.called',
            'agent_id': 'agent-1',
            'data': {
                'tool_name': 'search',
                'duration_ms': 100 + i
            }
        }
        for i in range(100)
    ]

    stats = exporter.get_token_estimate(events)

    # Should have all keys
    assert 'toon' in stats
    assert 'json' in stats
    assert 'savings_percent' in stats

    # TOON should use fewer tokens
    assert stats['toon'] < stats['json']

    # Should achieve significant savings (at least 20% for uniform data)
    assert stats['savings_percent'] > 20


def test_toon_exporter_real_world_aop_events():
    """Test with realistic AOP event structure."""
    exporter = ToonExporter(flatten=True, delimiter='comma')

    events = [
        {
            'id': 'evt-001',
            'version': '1.0',
            'timestamp': '2025-01-15T10:00:00Z',
            'agent_id': 'my-agent',
            'instance_id': 'inst-001',
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called',
            'correlation_id': 'trace-123',
            'severity': 'info',
            'data': {
                'tool_name': 'search',
                'params': {'query': 'test'},
                'duration_ms': 45
            },
            'metadata': {
                'user_id': 'user-1',
                'session_id': 'session-1'
            }
        },
        {
            'id': 'evt-002',
            'version': '1.0',
            'timestamp': '2025-01-15T10:00:01Z',
            'agent_id': 'my-agent',
            'instance_id': 'inst-001',
            'protocol': 'mcp',
            'event_type': 'mcp.tool.completed',
            'correlation_id': 'trace-123',
            'severity': 'info',
            'data': {
                'tool_name': 'search',
                'params': {'query': 'test'},
                'duration_ms': 120
            },
            'metadata': {
                'user_id': 'user-1',
                'session_id': 'session-1'
            }
        }
    ]

    result = exporter.export(events)

    # Check flattened fields appear
    assert 'data.tool_name' in result
    assert 'data.duration_ms' in result
    assert 'metadata.user_id' in result

    # Check excluded fields don't appear
    assert 'version' not in result
    assert 'instance_id' not in result

    # Check tabular format is used
    assert 'events[2]' in result
    assert 'evt-001' in result
    assert 'evt-002' in result


def test_toon_exporter_with_error_field():
    """Test flattening of error field."""
    exporter = ToonExporter(flatten=True)

    events = [
        {
            'id': 'evt-1',
            'event_type': 'mcp.tool.failed',
            'error': {
                'message': 'Connection timeout',
                'code': 'TIMEOUT'
            }
        }
    ]

    result = exporter.export(events)

    # Error fields should be flattened
    assert 'error.message' in result
    assert 'error.code' in result
    assert 'Connection timeout' in result


def test_toon_exporter_mixed_nested_and_flat():
    """Test events with both nested and flat fields."""
    exporter = ToonExporter(flatten=True)

    events = [
        {
            'id': 'evt-1',
            'agent_id': 'agent-1',  # Flat field
            'data': {  # Nested field
                'tool': 'search'
            }
        }
    ]

    result = exporter.export(events)

    # Both flat and flattened-nested should appear
    assert 'agent_id' in result or 'agent-1' in result
    assert 'data.tool' in result


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_encoder_special_characters():
    """Test handling of special characters."""
    encoder = ToonEncoder()

    obj = {
        'message': 'Line 1\nLine 2',
        'path': 'C:\\Users\\test',
        'unicode': '🚀 Test'
    }

    result = encoder.encode(obj)

    # Should handle without errors
    assert result is not None
    assert 'message' in result


def test_toon_exporter_single_event():
    """Test export of single event."""
    exporter = ToonExporter()

    events = [{'id': 'evt-1', 'type': 'test'}]

    result = exporter.export(events)

    # Single event uses list format (tabular requires 2+ events)
    assert 'events:' in result
    assert 'evt-1' in result


def test_toon_exporter_deeply_nested():
    """Test handling of deeply nested structures."""
    exporter = ToonExporter(flatten=True)

    events = [
        {
            'id': 'evt-1',
            'data': {
                'level1': {
                    'level2': {
                        'value': 'deep'
                    }
                }
            }
        }
    ]

    result = exporter.export(events)

    # Deep nesting should be handled (flattening only goes one level)
    assert result is not None
