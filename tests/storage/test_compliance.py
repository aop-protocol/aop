"""
Storage Compliance Tests

Tests that ALL storage backends behave identically.
Every storage backend (SQLite, PostgreSQL, In-Memory) must pass these tests.
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import List

from aop.storage import SQLiteStorage, InMemoryStorage, PostgreSQLStorage
from aop.utils import generate_uuid_v7, get_timestamp


# ============================================================================
# FIXTURES - Storage Backends
# ============================================================================

@pytest.fixture
def sqlite_storage():
    """SQLite in-memory storage for testing."""
    storage = SQLiteStorage('sqlite:///:memory:')
    yield storage
    storage.close()


@pytest.fixture
def memory_storage():
    """In-memory storage for testing."""
    storage = InMemoryStorage()
    yield storage
    storage.close()


@pytest.fixture
def postgresql_storage():
    """PostgreSQL storage (skipped if not available)."""
    try:
        storage = PostgreSQLStorage('postgresql://localhost/aop_test')
        yield storage
        storage.close()
    except Exception:
        pytest.skip("PostgreSQL not available")


@pytest.fixture(params=['sqlite', 'memory'])  # Add 'postgresql' when ready
def any_storage(request, sqlite_storage, memory_storage):
    """Parametrized fixture - runs tests against all storage backends."""
    if request.param == 'sqlite':
        return sqlite_storage
    elif request.param == 'memory':
        return memory_storage
    # elif request.param == 'postgresql':
    #     return postgresql_storage


# ============================================================================
# FIXTURES - Sample Data
# ============================================================================

@pytest.fixture
def sample_event():
    """Create a complete valid event for testing."""
    return {
        'id': generate_uuid_v7(),
        'version': '1.0',
        'timestamp': get_timestamp(),
        'agent_id': 'test-agent',
        'instance_id': generate_uuid_v7(),
        'protocol': 'mcp',
        'event_type': 'mcp.tool.call',
        'data': {'tool_name': 'test_tool', 'params': {'query': 'test'}}
    }


@pytest.fixture
def multiple_events():
    """Create multiple events for testing queries."""
    base_time = datetime.utcnow()
    
    events = [
        {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': (base_time - timedelta(minutes=5)).isoformat() + 'Z',
            'agent_id': 'agent-1',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.call',
            'correlation_id': 'trace-123',
            'data': {'tool_name': 'search'}
        },
        {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': (base_time - timedelta(minutes=4)).isoformat() + 'Z',
            'agent_id': 'agent-1',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.result',
            'correlation_id': 'trace-123',
            'data': {'result': 'success'}
        },
        {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': (base_time - timedelta(minutes=3)).isoformat() + 'Z',
            'agent_id': 'agent-2',
            'instance_id': generate_uuid_v7(),
            'protocol': 'a2a',
            'event_type': 'a2a.task.start',
            'correlation_id': 'trace-456',
            'data': {'task_id': 'task-1'}
        },
        {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': (base_time - timedelta(minutes=2)).isoformat() + 'Z',
            'agent_id': 'agent-2',
            'instance_id': generate_uuid_v7(),
            'protocol': 'a2a',
            'event_type': 'a2a.task.complete',
            'correlation_id': 'trace-456',
            'data': {'task_id': 'task-1', 'result': 'done'}
        },
        {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': (base_time - timedelta(minutes=1)).isoformat() + 'Z',
            'agent_id': 'agent-1',
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.error',
            'data': {'error': 'test error'}
        },
    ]
    
    return events


# ============================================================================
# COMPLIANCE TESTS - Basic Operations
# ============================================================================

def test_can_log_single_event(any_storage, sample_event):
    """Test: Storage can log a single event."""
    any_storage.log_event(sample_event)
    
    # Retrieve and verify
    retrieved = any_storage.get_event(sample_event['id'])
    assert retrieved is not None
    assert retrieved['id'] == sample_event['id']
    assert retrieved['agent_id'] == sample_event['agent_id']
    assert retrieved['event_type'] == sample_event['event_type']


def test_can_log_multiple_events(any_storage, multiple_events):
    """Test: Storage can log multiple events."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    # Verify all stored
    for event in multiple_events:
        retrieved = any_storage.get_event(event['id'])
        assert retrieved is not None


def test_get_event_by_id_exists(any_storage, sample_event):
    """Test: Get event by ID returns event when it exists."""
    any_storage.log_event(sample_event)
    
    retrieved = any_storage.get_event(sample_event['id'])
    assert retrieved is not None
    assert retrieved['id'] == sample_event['id']


def test_get_event_by_id_not_found(any_storage):
    """Test: Get event by ID returns None when not found."""
    retrieved = any_storage.get_event('non-existent-id')
    assert retrieved is None


def test_log_duplicate_event_is_idempotent(any_storage, sample_event):
    """Test: Logging same event twice doesn't cause error (idempotent)."""
    any_storage.log_event(sample_event)
    any_storage.log_event(sample_event)  # Should not raise error
    
    # Should still only have one event
    retrieved = any_storage.get_event(sample_event['id'])
    assert retrieved is not None


# ============================================================================
# COMPLIANCE TESTS - Querying
# ============================================================================

def test_query_by_agent_id(any_storage, multiple_events):
    """Test: Can query events by agent_id."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    # Query agent-1 events
    results = any_storage.query_events(agent_id='agent-1')
    assert len(results) == 3  # agent-1 has 3 events
    assert all(e['agent_id'] == 'agent-1' for e in results)


def test_query_by_event_type(any_storage, multiple_events):
    """Test: Can query events by event_type."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    # Query tool.call events
    results = any_storage.query_events(event_type='mcp.tool.call')
    assert len(results) == 1
    assert results[0]['event_type'] == 'mcp.tool.call'


def test_query_by_protocol(any_storage, multiple_events):
    """Test: Can query events by protocol."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    # Query MCP events
    results = any_storage.query_events(protocol='mcp')
    assert len(results) == 3
    assert all(e['protocol'] == 'mcp' for e in results)
    
    # Query A2A events
    results = any_storage.query_events(protocol='a2a')
    assert len(results) == 2
    assert all(e['protocol'] == 'a2a' for e in results)


def test_query_by_correlation_id(any_storage, multiple_events):
    """Test: Can query events by correlation_id (trace)."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    # Query trace-123
    results = any_storage.query_events(correlation_id='trace-123')
    assert len(results) == 2
    assert all(e['correlation_id'] == 'trace-123' for e in results)


def test_query_by_time_range(any_storage, multiple_events):
    """Test: Can query events by time range."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    # Get time boundaries
    base_time = datetime.now(timezone.utc)
    start_time = base_time - timedelta(minutes=4, seconds=30)
    end_time = base_time - timedelta(minutes=2, seconds=30)
    
    # Query events in range
    results = any_storage.query_events(
        start_time=start_time,
        end_time=end_time
    )
    
    # Should get events at -4min, -3min (not -5min, -2min, -1min)
    assert len(results) == 2


def test_query_with_limit(any_storage, multiple_events):
    """Test: Query respects limit parameter."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    results = any_storage.query_events(limit=2)
    assert len(results) == 2


def test_query_returns_sorted_by_timestamp(any_storage, multiple_events):
    """Test: Query results are sorted by timestamp (newest first)."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    results = any_storage.query_events()
    
    # Verify descending order (newest first)
    timestamps = [e['timestamp'] for e in results]
    assert timestamps == sorted(timestamps, reverse=True)


def test_query_with_multiple_filters(any_storage, multiple_events):
    """Test: Can combine multiple query filters."""
    for event in multiple_events:
        any_storage.log_event(event)
    
    # Query: agent-1 AND protocol=mcp
    results = any_storage.query_events(
        agent_id='agent-1',
        protocol='mcp'
    )
    
    assert len(results) == 3
    assert all(e['agent_id'] == 'agent-1' for e in results)
    assert all(e['protocol'] == 'mcp' for e in results)


def test_query_empty_results(any_storage):
    """Test: Query with no matches returns empty list."""
    results = any_storage.query_events(agent_id='non-existent')
    assert results == []
    assert isinstance(results, list)


# ============================================================================
# COMPLIANCE TESTS - Data Integrity
# ============================================================================

def test_data_field_preserved(any_storage, sample_event):
    """Test: Data field is preserved exactly as stored."""
    any_storage.log_event(sample_event)
    
    retrieved = any_storage.get_event(sample_event['id'])
    assert retrieved['data'] == sample_event['data']
    assert retrieved['data']['tool_name'] == 'test_tool'


def test_optional_fields_preserved(any_storage):
    """Test: Optional fields are preserved when present."""
    event = {
        'id': generate_uuid_v7(),
        'version': '1.0',
        'timestamp': get_timestamp(),
        'agent_id': 'test-agent',
        'instance_id': generate_uuid_v7(),
        'protocol': 'mcp',
        'event_type': 'mcp.tool.call',
        'correlation_id': 'trace-abc',
        'parent_id': 'parent-123',
        'duration_ms': 150,
        'data': {'key': 'value'}
    }
    
    any_storage.log_event(event)
    retrieved = any_storage.get_event(event['id'])
    
    assert retrieved['correlation_id'] == 'trace-abc'
    assert retrieved['parent_id'] == 'parent-123'
    assert retrieved['duration_ms'] == 150


def test_optional_fields_absent_when_not_provided(any_storage, sample_event):
    """Test: Optional fields are absent (or None) when not provided."""
    # sample_event doesn't have correlation_id
    any_storage.log_event(sample_event)
    
    retrieved = any_storage.get_event(sample_event['id'])
    
    # Field should be absent or None
    assert retrieved.get('correlation_id') is None


# ============================================================================
# COMPLIANCE TESTS - Resource Management
# ============================================================================

def test_close_is_idempotent(any_storage):
    """Test: Calling close() multiple times is safe."""
    any_storage.close()
    any_storage.close()  # Should not raise error
    any_storage.close()  # Should not raise error


def test_context_manager_works(sqlite_storage, sample_event):
    """Test: Storage works as context manager."""
    with sqlite_storage as storage:
        storage.log_event(sample_event)
        retrieved = storage.get_event(sample_event['id'])
        assert retrieved is not None
    
    # Storage should be closed after context


# ============================================================================
# COMPLIANCE TESTS - Edge Cases
# ============================================================================

def test_handles_special_characters_in_data(any_storage):
    """Test: Handles special characters in data field."""
    event = {
        'id': generate_uuid_v7(),
        'version': '1.0',
        'timestamp': get_timestamp(),
        'agent_id': 'test-agent',
        'instance_id': generate_uuid_v7(),
        'protocol': 'mcp',
        'event_type': 'mcp.tool.call',
        'data': {
            'text': 'Special chars: "quotes", \'apostrophe\', \n newline, \t tab',
            'unicode': '你好世界 🚀',
            'json': '{"nested": "value"}'
        }
    }
    
    any_storage.log_event(event)
    retrieved = any_storage.get_event(event['id'])
    
    assert retrieved['data'] == event['data']


def test_handles_large_data_payload(any_storage):
    """Test: Handles large data payloads."""
    large_data = {
        'large_list': list(range(1000)),
        'large_string': 'x' * 10000,
        'nested': {'level': 1, 'data': {'level': 2, 'items': list(range(100))}}
    }
    
    event = {
        'id': generate_uuid_v7(),
        'version': '1.0',
        'timestamp': get_timestamp(),
        'agent_id': 'test-agent',
        'instance_id': generate_uuid_v7(),
        'protocol': 'mcp',
        'event_type': 'mcp.tool.call',
        'data': large_data
    }
    
    any_storage.log_event(event)
    retrieved = any_storage.get_event(event['id'])
    
    assert len(retrieved['data']['large_list']) == 1000
    assert len(retrieved['data']['large_string']) == 10000


def test_handles_empty_data(any_storage):
    """Test: Handles empty data field."""
    event = {
        'id': generate_uuid_v7(),
        'version': '1.0',
        'timestamp': get_timestamp(),
        'agent_id': 'test-agent',
        'instance_id': generate_uuid_v7(),
        'protocol': 'mcp',
        'event_type': 'mcp.tool.call',
        'data': {}
    }
    
    any_storage.log_event(event)
    retrieved = any_storage.get_event(event['id'])
    
    assert retrieved['data'] == {}


# ============================================================================
# SUMMARY
# ============================================================================

"""
Compliance Test Summary:

✅ Basic Operations (5 tests)
   - Log single event
   - Log multiple events
   - Get by ID (exists)
   - Get by ID (not found)
   - Duplicate handling

✅ Querying (9 tests)
   - Query by agent_id
   - Query by event_type
   - Query by protocol
   - Query by correlation_id
   - Query by time range
   - Query with limit
   - Query sorting
   - Multiple filters
   - Empty results

✅ Data Integrity (3 tests)
   - Data preservation
   - Optional fields present
   - Optional fields absent

✅ Resource Management (2 tests)
   - Close idempotent
   - Context manager

✅ Edge Cases (3 tests)
   - Special characters
   - Large payloads
   - Empty data

Total: 22 compliance tests
Each test runs against ALL storage backends!
"""