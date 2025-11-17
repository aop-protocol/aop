"""
Tests for Dashboard backend.

Note: These tests require dashboard dependencies (fastapi, uvicorn).
Install with: pip install aop[dashboard]
"""

import pytest

# Check if dashboard dependencies are available
try:
    from fastapi.testclient import TestClient
    from aop.dashboard.server import app, storage_url
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False


@pytest.fixture
def test_client(tmp_path):
    """Create FastAPI test client with test database."""
    if not DASHBOARD_AVAILABLE:
        pytest.skip("Dashboard dependencies not installed")

    from aop import AOPClient
    from aop.dashboard import server

    # Create test database with sample data
    db_path = tmp_path / "test_dashboard.db"
    storage_string = f'sqlite:///{db_path}'
    client = AOPClient(storage=storage_string)

    # Create sample events
    correlation_id = 'dash-test-trace'

    call1 = client.mcp.log_tool_call(
        agent_id='dashboard-test-agent',
        tool_name='test_tool_1',
        params={'param': 'value1'},
        correlation_id=correlation_id
    )

    client.mcp.log_tool_result(
        agent_id='dashboard-test-agent',
        tool_name='test_tool_1',
        result={'result': 'success'},
        duration_ms=100,
        correlation_id=correlation_id,
        parent_id=call1.id
    )

    call2 = client.mcp.log_tool_call(
        agent_id='dashboard-test-agent',
        tool_name='test_tool_2',
        params={'param': 'value2'},
        correlation_id=correlation_id
    )

    client.mcp.log_tool_result(
        agent_id='dashboard-test-agent',
        tool_name='test_tool_2',
        result={'result': 'success'},
        duration_ms=50,
        correlation_id=correlation_id,
        parent_id=call2.id
    )

    client.close()

    # Set storage URL BEFORE creating test client (lifespan runs on creation)
    server.storage_url = storage_string

    # Create test client (this triggers lifespan which initializes client/analytics)
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.skipif(not DASHBOARD_AVAILABLE, reason="Dashboard dependencies not installed")
class TestDashboardAPI:
    """Test Dashboard REST API endpoints."""

    def test_health_check(self, test_client):
        """Test health endpoint."""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'

    def test_get_agents(self, test_client):
        """Test get agents endpoint."""
        response = test_client.get("/api/agents")
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)
        assert 'dashboard-test-agent' in agents

    def test_get_events(self, test_client):
        """Test get events endpoint."""
        response = test_client.get("/api/events")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        assert len(events) > 0

    def test_get_events_with_filter(self, test_client):
        """Test get events with agent filter."""
        response = test_client.get("/api/events?agent_id=dashboard-test-agent&limit=10")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        # All events should be from test agent
        for event in events:
            assert event['agent_id'] == 'dashboard-test-agent'

    def test_get_events_pagination(self, test_client):
        """Test events pagination."""
        # Get first page
        response1 = test_client.get("/api/events?limit=2&offset=0")
        assert response1.status_code == 200
        events1 = response1.json()
        assert len(events1) <= 2

        # Get second page
        response2 = test_client.get("/api/events?limit=2&offset=2")
        assert response2.status_code == 200
        events2 = response2.json()

        # Should be different events (if enough exist)
        if len(events1) == 2 and len(events2) > 0:
            assert events1[0]['id'] != events2[0]['id']

    def test_get_trace(self, test_client):
        """Test get trace endpoint."""
        response = test_client.get("/api/traces/dash-test-trace")
        assert response.status_code == 200
        trace = response.json()
        assert 'root_event' in trace
        assert 'children' in trace
        assert 'event_count' in trace

    def test_get_trace_not_found(self, test_client):
        """Test get trace with non-existent correlation ID."""
        response = test_client.get("/api/traces/non-existent-trace")
        assert response.status_code == 404

    def test_get_stats(self, test_client):
        """Test get stats endpoint."""
        response = test_client.get("/api/stats?agent_id=dashboard-test-agent")
        assert response.status_code == 200
        stats = response.json()
        assert 'agent_id' in stats
        assert 'tool_counts' in stats
        assert 'event_counts' in stats
        assert 'avg_durations' in stats
        assert 'percentiles' in stats
        assert stats['agent_id'] == 'dashboard-test-agent'

    def test_get_timeline(self, test_client):
        """Test get timeline endpoint."""
        response = test_client.get("/api/timeline?agent_id=dashboard-test-agent&bucket_size=1h")
        assert response.status_code == 200
        timeline = response.json()
        assert isinstance(timeline, list)

    def test_get_event_rate(self, test_client):
        """Test get event rate endpoint."""
        response = test_client.get("/api/rate?agent_id=dashboard-test-agent&window_minutes=60")
        assert response.status_code == 200
        rate = response.json()
        assert 'agent_id' in rate
        assert 'rate' in rate
        assert 'window_minutes' in rate
        assert isinstance(rate['rate'], (int, float))

    def test_frontend_placeholder(self, test_client):
        """Test frontend serves placeholder page."""
        response = test_client.get("/")
        assert response.status_code == 200
        # Should serve HTML
        assert 'text/html' in response.headers.get('content-type', '')


@pytest.mark.skipif(not DASHBOARD_AVAILABLE, reason="Dashboard dependencies not installed")
class TestDashboardCLI:
    """Test dashboard CLI command."""

    def test_dashboard_command_exists(self):
        """Test that dashboard command is registered."""
        from click.testing import CliRunner
        from aop.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ['--help'])

        assert result.exit_code == 0
        assert 'dashboard' in result.output

    def test_dashboard_help(self):
        """Test dashboard command help."""
        from click.testing import CliRunner
        from aop.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ['dashboard', '--help'])

        assert result.exit_code == 0
        assert 'web interface' in result.output.lower()
        assert '--storage' in result.output
        assert '--port' in result.output
