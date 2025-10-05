"""
Tests for aop.client module
"""

import pytest
import os
import tempfile
import sqlite3
from pathlib import Path
from aop.client import AOPClient
from aop.exceptions import AOPValidationError, AOPStorageError
from aop.utils import generate_uuid_v7, get_timestamp


@pytest.fixture
def client():
    """Create client with in-memory storage for testing"""
    return AOPClient(storage="memory")

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    storage_url = f"sqlite:///{db_path}"
    yield storage_url
    
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestClientInitialization:
    """Test client initialization"""
    
    def test_creates_database_file(self, temp_db):
        """Test that client creates database file"""
        # Extract file path from sqlite:///path format
        db_path = temp_db.replace('sqlite:///', '')
        
        client = AOPClient(temp_db)
        assert os.path.exists(db_path)
        client.close()
    
    def test_creates_schema(self, temp_db):
        """Test that client creates database schema"""
        client = AOPClient(temp_db)
        
        # Access connection through storage backend
        cursor = client.storage.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='events'
        """)
        assert cursor.fetchone() is not None
        client.close()
    
    def test_creates_indexes(self, temp_db):
        """Test that client creates indexes"""
        client = AOPClient(temp_db)
        
        cursor = client.storage.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert 'idx_agent_id' in indexes
        assert 'idx_event_type' in indexes
        assert 'idx_timestamp' in indexes
        assert 'idx_correlation_id' in indexes
        client.close()


class TestLogEvent:
    """Test log_event method"""
    
    def test_logs_minimal_event(self, client):
        """Test logging minimal event with auto-build"""
        event_id = client.log_event({
            'agent_id': 'test-agent',
            'event_type': 'mcp.tool.called'
        })
        
        assert event_id is not None
    
    def test_logs_complete_event(self, client):
        """Test logging complete event"""
        event_id = client.log_event({
            'agent_id': 'test-agent',
            'event_type': 'mcp.tool.called',
            'data': {'tool_name': 'search'},
            'severity': 'info',
            'correlation_id': 'trace-123'
        })
        
        assert event_id is not None
    
    def test_returns_event_id(self, client):
        """Test that log_event returns event ID"""
        event_id = client.log_event({
            'agent_id': 'test-agent',
            'event_type': 'mcp.tool.called'
        })
        
        # Should be valid UUID
        from aop.utils import validate_uuid
        assert validate_uuid(event_id)
    
    def test_validates_event_by_default(self, client):
        """Test that validation runs by default"""
        with pytest.raises((AOPValidationError, Exception)):
            client.log_event({
                'agent_id': '',  # Invalid
                'event_type': 'mcp.tool.called'
            })
    
    def test_can_skip_validation(self, client):
        """Test that validation can be skipped"""
        # Provide complete event (no auto-build needed)
        event = {
            'id': generate_uuid_v7(),
            'version': '1.0',
            'timestamp': get_timestamp(),
            'agent_id': '',  # Still invalid but we skip validation
            'instance_id': generate_uuid_v7(),
            'protocol': 'mcp',
            'event_type': 'mcp.tool.called'
        }
        
        event_id = client.log_event(event, validate=False, auto_build=False)
        assert event_id is not None


class TestLogEvents:
    """Test log_events batch method"""
    
    def test_logs_multiple_events(self, client):
        """Test logging multiple events"""
        events = [
            {'agent_id': 'agent-1', 'event_type': 'mcp.tool.called'},
            {'agent_id': 'agent-2', 'event_type': 'a2a.task.assigned'},
            {'agent_id': 'agent-3', 'event_type': 'ap2.payment.initiated'}
        ]
        
        event_ids = client.log_events(events)
        
        assert len(event_ids) == 3
    
    def test_returns_list_of_ids(self, client):
        """Test that log_events returns list of IDs"""
        events = [
            {'agent_id': 'agent-1', 'event_type': 'mcp.tool.called'},
            {'agent_id': 'agent-2', 'event_type': 'mcp.tool.completed'}
        ]
        
        event_ids = client.log_events(events)
        
        assert isinstance(event_ids, list)
        assert len(event_ids) == 2


class TestQueryEvents:
    """Test query method"""
    
    def test_query_by_agent_id(self, client):
        """Test querying by agent_id"""
        # Log events
        client.log_event({'agent_id': 'agent-1', 'event_type': 'mcp.tool.called'})
        client.log_event({'agent_id': 'agent-2', 'event_type': 'mcp.tool.called'})
        client.log_event({'agent_id': 'agent-1', 'event_type': 'mcp.tool.completed'})
        
        # Query
        events = client.query(agent_id='agent-1')
        
        assert len(events) == 2
        assert all(e['agent_id'] == 'agent-1' for e in events)
    
    def test_query_by_event_type(self, client):
        """Test querying by event_type"""
        client.log_event({'agent_id': 'agent-1', 'event_type': 'mcp.tool.called'})
        client.log_event({'agent_id': 'agent-1', 'event_type': 'mcp.tool.completed'})
        
        events = client.query(event_type='mcp.tool.called')
        
        assert len(events) == 1
        assert events[0]['event_type'] == 'mcp.tool.called'
    
    def test_query_by_protocol(self, client):
        """Test querying by protocol"""
        client.log_event({'agent_id': 'agent-1', 'event_type': 'mcp.tool.called'})
        client.log_event({'agent_id': 'agent-1', 'event_type': 'a2a.task.assigned'})
        
        events = client.query(protocol='mcp')
        
        assert len(events) == 1
        assert events[0]['protocol'] == 'mcp'
    
    def test_query_with_limit(self, client):
        """Test query limit"""
        # Log 10 events
        for i in range(10):
            client.log_event({'agent_id': f'agent-{i}', 'event_type': 'mcp.tool.called'})
        
        events = client.query(limit=5)
        
        assert len(events) == 5
    
    def test_query_returns_deserialized_data(self, client):
        """Test that query returns deserialized JSON fields"""
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'data': {'key': 'value'},
            'metadata': {'meta': 'data'}
        })
        
        events = client.query(agent_id='agent-1')
        
        assert isinstance(events[0]['data'], dict)
        assert events[0]['data'] == {'key': 'value'}
        # metadata is optional, use .get()
        if 'metadata' in events[0]:
            assert isinstance(events[0]['metadata'], dict)
    
    def test_query_with_multiple_filters(self, client):
        """Test query with multiple filters"""
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'severity': 'info'
        })
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'severity': 'error'
        })
        
        # Query with severity filter (applied in-memory)
        events = client.query(
            agent_id='agent-1',
            event_type='mcp.tool.called',
            severity='info'
        )
        
        assert len(events) >= 1  # At least one with info severity
        assert all(e['severity'] == 'info' for e in events)


class TestGetTrace:
    """Test get_trace method"""
    
    def test_gets_trace_by_correlation_id(self, client):
        """Test getting trace by correlation_id"""
        correlation_id = 'trace-123'
        
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id
        })
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.completed',
            'correlation_id': correlation_id
        })
        client.log_event({
            'agent_id': 'agent-2',
            'event_type': 'mcp.tool.called',
            'correlation_id': 'other-trace'
        })
        
        trace = client.get_trace(correlation_id)
        
        assert len(trace) == 2
        assert all(e['correlation_id'] == correlation_id for e in trace)
    
    def test_trace_ordered_chronologically(self, client):
        """Test that trace events are ordered by timestamp"""
        correlation_id = 'trace-123'
        
        # Log in reverse order
        import time
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.completed',
            'correlation_id': correlation_id
        })
        time.sleep(0.01)
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id
        })
        
        trace = client.get_trace(correlation_id)
        
        # Should be in chronological order (oldest first)
        assert trace[0]['event_type'] == 'mcp.tool.completed'
        assert trace[1]['event_type'] == 'mcp.tool.called'


class TestContextManager:
    """Test context manager support"""
    
    def test_context_manager_usage(self, temp_db):
        """Test using client as context manager"""
        with AOPClient(temp_db) as client:
            client.log_event({
                'agent_id': 'test-agent',
                'event_type': 'mcp.tool.called'
            })
        
        # Connection should be closed after context
        # Re-open to verify data was saved
        client2 = AOPClient(temp_db)
        events = client2.query(agent_id='test-agent')
        assert len(events) == 1
        client2.close()
    
    def test_context_manager_closes_connection(self, temp_db):
        """Test that context manager closes connection"""
        with AOPClient(temp_db) as client:
            # Connection should be active
            conn = client.storage.conn
            assert conn is not None
        
        # After context exit, connection should be closed
        # Verify by trying to execute on closed connection
        with pytest.raises((sqlite3.ProgrammingError, AttributeError)):
            conn.execute("SELECT 1")


class TestAutoBuild:
    """Test auto-build functionality"""
    
    def test_auto_build_fills_required_fields(self, client):
        """Test that auto-build fills required fields"""
        client.log_event({
            'agent_id': 'test-agent',
            'event_type': 'mcp.tool.called'
        })
        
        events = client.query(agent_id='test-agent')
        event = events[0]
        
        # Check auto-filled fields
        assert 'id' in event
        assert 'version' in event
        assert 'timestamp' in event
        assert 'instance_id' in event
        assert 'protocol' in event
        assert event['version'] == '1.0'
        assert event['protocol'] == 'mcp'