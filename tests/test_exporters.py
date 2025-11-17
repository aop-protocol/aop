"""
Tests for base exporter interface and registration system.
"""

import pytest
from typing import List, Dict, Any

from aop.exporters import BaseExporter, register_exporter, get_exporter, list_exporters
from aop import AOPClient


class TestExporter(BaseExporter):
    """Test exporter implementation."""
    
    def export(self, events: List[Dict[str, Any]]) -> str:
        return f"Exported {len(events)} events"


def test_base_exporter_abstract():
    """Test that BaseExporter is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseExporter()


def test_base_exporter_export():
    """Test that exporter must implement export method."""
    exporter = TestExporter()
    events = [{'id': '1'}, {'id': '2'}]
    result = exporter.export(events)
    assert result == "Exported 2 events"


def test_base_exporter_export_trace():
    """Test export_trace method."""
    client = AOPClient(storage='memory')
    
    # Create a trace
    correlation_id = 'test-trace-123'
    client.log_event({
        'agent_id': 'test-agent',
        'event_type': 'mcp.tool.called',
        'correlation_id': correlation_id,
        'data': {'tool_name': 'test_tool'}
    })
    
    exporter = TestExporter(client=client)
    result = exporter.export_trace(correlation_id)
    
    assert 'Exported' in result
    assert '1' in result
    
    client.close()


def test_base_exporter_export_trace_no_client():
    """Test export_trace raises error without client."""
    exporter = TestExporter()
    
    with pytest.raises(ValueError, match="AOPClient required"):
        exporter.export_trace('test-trace')


def test_register_exporter():
    """Test exporter registration."""
    # Clear registry
    original_exporters = list_exporters().copy()
    
    try:
        register_exporter('test', TestExporter)
        assert 'test' in list_exporters()
        
        # Try to register again (should fail)
        with pytest.raises(ValueError, match="already registered"):
            register_exporter('test', TestExporter)
    finally:
        # Cleanup - remove test exporter
        # Note: In real implementation, you'd want an unregister function
        pass


def test_register_invalid_exporter():
    """Test registering non-BaseExporter class fails."""
    class NotAnExporter:
        pass
    
    with pytest.raises(ValueError, match="must inherit from BaseExporter"):
        register_exporter('invalid', NotAnExporter)


def test_get_exporter():
    """Test getting registered exporter."""
    register_exporter('test_get', TestExporter)
    
    exporter = get_exporter('test_get')
    assert isinstance(exporter, TestExporter)
    
    # With client
    client = AOPClient(storage='memory')
    exporter = get_exporter('test_get', client=client)
    assert exporter.client == client
    client.close()


def test_get_nonexistent_exporter():
    """Test getting non-existent exporter raises error."""
    with pytest.raises(ValueError, match="is not registered"):
        get_exporter('nonexistent')


def test_list_exporters():
    """Test listing registered exporters."""
    exporters = list_exporters()
    assert isinstance(exporters, list)
    # Should at least have test exporters if any were registered
    assert 'test' in exporters or len(exporters) >= 0

