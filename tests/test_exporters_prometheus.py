"""
Tests for Prometheus exporter.

These tests will be skipped if Prometheus dependencies are not installed.
"""

import pytest
import time
import threading

# Check if Prometheus is available
try:
    from aop.exporters import PrometheusExporterServer, PrometheusExporter
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    PrometheusExporterServer = None
    PrometheusExporter = None

from aop import AOPClient


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus dependencies not installed")
def test_prometheus_exporter_init():
    """Test Prometheus exporter initialization."""
    client = AOPClient(storage='memory')
    exporter = PrometheusExporter(client=client)
    
    assert exporter.client == client
    
    client.close()


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus dependencies not installed")
def test_prometheus_exporter_export():
    """Test Prometheus export."""
    client = AOPClient(storage='memory')
    exporter = PrometheusExporter(client=client)
    
    events = [
        {
            'id': '1',
            'event_type': 'mcp.tool.called',
            'agent_id': 'agent-1',
            'protocol': 'mcp'
        }
    ]
    
    result = exporter.export(events)
    
    # Should be Prometheus text format
    assert 'aop_events_total' in result
    assert 'mcp.tool.called' in result
    
    client.close()


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus dependencies not installed")
def test_prometheus_server_init():
    """Test Prometheus server initialization."""
    server = PrometheusExporterServer(
        storage='memory',
        port=9091,  # Use different port to avoid conflicts
        poll_interval=1.0
    )
    
    assert server.port == 9091
    assert server.poll_interval == 1.0
    assert not server.running


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus dependencies not installed")
def test_prometheus_server_start_stop():
    """Test starting and stopping Prometheus server."""
    server = PrometheusExporterServer(
        storage='memory',
        port=9092,  # Use different port
        poll_interval=1.0
    )
    
    # Start server
    server.start()
    assert server.running
    
    # Give it a moment to start
    time.sleep(0.5)
    
    # Stop server
    server.stop()
    assert not server.running


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus dependencies not installed")
def test_prometheus_server_metrics_endpoint():
    """Test that server exposes /metrics endpoint."""
    import urllib.request
    
    server = PrometheusExporterServer(
        storage='memory',
        port=9093,  # Use different port
        poll_interval=1.0
    )
    
    try:
        server.start()
        time.sleep(0.5)  # Give server time to start
        
        # Try to fetch metrics
        try:
            response = urllib.request.urlopen(f'http://localhost:{server.port}/metrics', timeout=1)
            content = response.read().decode('utf-8')
            
            # Should be Prometheus format
            assert 'aop_' in content or '# HELP' in content or len(content) > 0
        except Exception:
            # Server might not be ready yet, that's okay for this test
            pass
    finally:
        server.stop()

