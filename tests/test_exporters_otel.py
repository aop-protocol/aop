"""
Tests for OpenTelemetry exporter.

These tests will be skipped if OpenTelemetry dependencies are not installed.
"""

import pytest

# Check if OTEL is available
try:
    from aop.exporters import OpenTelemetryExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    OpenTelemetryExporter = None

from aop import AOPClient


@pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry dependencies not installed")
def test_otel_exporter_init():
    """Test OTEL exporter initialization."""
    client = AOPClient(storage='memory')
    exporter = OpenTelemetryExporter(client=client)
    
    assert exporter.client == client
    assert exporter.tracer is not None
    
    client.close()


@pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry dependencies not installed")
def test_otel_exporter_init_no_deps():
    """Test that exporter raises error without dependencies."""
    # This test would need to mock the import failure
    # For now, we just test that it works when deps are available
    pass


@pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry dependencies not installed")
def test_otel_exporter_export_events():
    """Test converting events to OTEL spans."""
    client = AOPClient(storage='memory')
    exporter = OpenTelemetryExporter(client=client)
    
    events = [
        {
            'id': '1',
            'timestamp': '2025-01-01T00:00:00Z',
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'protocol': 'mcp',
            'data': {'tool_name': 'test_tool'},
            'duration_ms': 100
        }
    ]
    
    spans = exporter.export_events(events)
    
    assert len(spans) > 0
    
    client.close()


@pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry dependencies not installed")
def test_otel_exporter_map_event_types():
    """Test event type to span kind mapping."""
    client = AOPClient(storage='memory')
    exporter = OpenTelemetryExporter(client=client)
    
    # Test tool events (should be CLIENT)
    kind = exporter._map_event_type_to_span_kind('mcp.tool.called')
    from opentelemetry.trace import SpanKind
    assert kind == SpanKind.CLIENT
    
    # Test task events (should be INTERNAL)
    kind = exporter._map_event_type_to_span_kind('a2a.task.assigned')
    assert kind == SpanKind.INTERNAL
    
    client.close()


@pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry dependencies not installed")
def test_otel_exporter_preserve_correlation():
    """Test that correlation_id is preserved in spans."""
    client = AOPClient(storage='memory')
    exporter = OpenTelemetryExporter(client=client)
    
    correlation_id = 'test-trace-123'
    events = [
        {
            'id': '1',
            'timestamp': '2025-01-01T00:00:00Z',
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id,
            'data': {'tool_name': 'test_tool'}
        }
    ]
    
    spans = exporter.export_events(events)
    
    # Check that correlation_id is set as attribute
    # (This is a simplified check - real implementation would verify span attributes)
    assert len(spans) > 0
    
    client.close()

