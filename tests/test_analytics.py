"""
Tests for analytics module.
"""

import pytest
from datetime import datetime, timedelta
from aop import AOPClient, Analytics


@pytest.fixture
def client_with_data():
    """Create client with sample trace data"""
    client = AOPClient(storage='memory')

    # Create a trace with parent-child relationships
    # Tool call 1
    call1 = client.mcp.log_tool_call(
        agent_id='test-agent',
        tool_name='search',
        params={'query': 'test'},
        correlation_id='trace-123'
    )

    # Tool result 1
    client.mcp.log_tool_result(
        agent_id='test-agent',
        tool_name='search',
        result={'count': 10},
        duration_ms=150,
        correlation_id='trace-123',
        parent_id=call1.id
    )

    # Tool call 2
    call2 = client.mcp.log_tool_call(
        agent_id='test-agent',
        tool_name='process',
        params={'data': 'test'},
        correlation_id='trace-123'
    )

    # Tool result 2
    client.mcp.log_tool_result(
        agent_id='test-agent',
        tool_name='process',
        result={'status': 'ok'},
        duration_ms=50,
        correlation_id='trace-123',
        parent_id=call2.id
    )

    # Tool call 3 with error
    call3 = client.mcp.log_tool_call(
        agent_id='test-agent',
        tool_name='validate',
        params={'input': 'bad'},
        correlation_id='trace-123'
    )

    # Tool error
    client.mcp.log_tool_error(
        agent_id='test-agent',
        tool_name='validate',
        error_message='Validation failed',
        error_code='VALIDATION_ERROR',
        correlation_id='trace-123',
        parent_id=call3.id
    )

    return client


class TestTraceReconstruction:
    """Test trace reconstruction functionality"""

    def test_reconstruct_trace_by_correlation_id(self, client_with_data):
        """Test reconstructing trace by correlation ID"""
        analytics = Analytics(client_with_data)

        trace = analytics.reconstruct_trace(correlation_id='trace-123')

        assert trace['event_count'] == 6  # 3 calls + 2 results + 1 error
        assert trace['total_duration_ms'] == 200  # 150 + 50
        assert trace['error_count'] == 1
        assert trace['root_event'] is not None
        assert len(trace['children']) > 0

    def test_reconstruct_trace_by_root_event(self, client_with_data):
        """Test reconstructing trace by root event ID"""
        analytics = Analytics(client_with_data)

        # Get first call event
        events = client_with_data.query(event_type='mcp.tool.called', limit=1)
        root_id = events[0]['id']

        trace = analytics.reconstruct_trace(root_event_id=root_id)

        assert trace['event_count'] >= 2  # At least call + result
        assert trace['root_event']['id'] == root_id

    def test_reconstruct_empty_trace(self, client_with_data):
        """Test reconstructing non-existent trace"""
        analytics = Analytics(client_with_data)

        trace = analytics.reconstruct_trace(correlation_id='non-existent')

        assert trace['event_count'] == 0
        assert trace['total_duration_ms'] == 0
        assert trace['error_count'] == 0
        assert trace['root_event'] is None

    def test_reconstruct_trace_requires_id(self, client_with_data):
        """Test that reconstruction requires either correlation_id or root_event_id"""
        analytics = Analytics(client_with_data)

        with pytest.raises(ValueError):
            analytics.reconstruct_trace()


class TestAggregations:
    """Test aggregation functionality"""

    def test_count_by_tool(self, client_with_data):
        """Test counting events by tool name"""
        analytics = Analytics(client_with_data)

        counts = analytics.count_by_tool('test-agent')

        assert counts['search'] == 1
        assert counts['process'] == 1
        assert counts['validate'] == 1

    def test_count_by_event_type(self, client_with_data):
        """Test counting events by event type"""
        analytics = Analytics(client_with_data)

        counts = analytics.count_by_event_type('test-agent')

        assert counts['mcp.tool.called'] == 3
        assert counts['mcp.tool.completed'] == 2
        assert counts['mcp.tool.error'] == 1

    def test_avg_duration_by_tool(self, client_with_data):
        """Test calculating average duration by tool"""
        analytics = Analytics(client_with_data)

        avgs = analytics.avg_duration_by_tool('test-agent')

        assert avgs['search'] == 150.0
        assert avgs['process'] == 50.0

    def test_percentile_duration_all_tools(self, client_with_data):
        """Test percentile calculation across all tools"""
        analytics = Analytics(client_with_data)

        p95 = analytics.percentile_duration('test-agent', percentile=95)

        assert p95 > 0
        assert p95 <= 150  # Max duration

    def test_percentile_duration_specific_tool(self, client_with_data):
        """Test percentile calculation for specific tool"""
        analytics = Analytics(client_with_data)

        p50 = analytics.percentile_duration('test-agent', 'search', percentile=50)

        assert p50 == 150.0

    def test_percentile_empty_data(self):
        """Test percentile with no data"""
        client = AOPClient(storage='memory')
        analytics = Analytics(client)

        p95 = analytics.percentile_duration('test-agent', percentile=95)

        assert p95 == 0.0


class TestTimeSeries:
    """Test time-series functionality"""

    def test_events_over_time_hourly(self, client_with_data):
        """Test grouping events by hour"""
        analytics = Analytics(client_with_data)

        timeline = analytics.events_over_time('test-agent', bucket_size='1h')

        assert len(timeline) > 0
        assert all('time' in bucket and 'count' in bucket for bucket in timeline)
        assert sum(b['count'] for b in timeline) == 6  # Total events

    def test_events_over_time_daily(self, client_with_data):
        """Test grouping events by day"""
        analytics = Analytics(client_with_data)

        timeline = analytics.events_over_time('test-agent', bucket_size='1d')

        assert len(timeline) > 0

    def test_events_over_time_with_range(self, client_with_data):
        """Test time-series with time range"""
        analytics = Analytics(client_with_data)

        from datetime import timezone
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=1)

        timeline = analytics.events_over_time(
            'test-agent',
            bucket_size='1h',
            start_time=start_time,
            end_time=end_time
        )

        assert isinstance(timeline, list)

    def test_events_over_time_empty(self):
        """Test time-series with no events"""
        client = AOPClient(storage='memory')
        analytics = Analytics(client)

        timeline = analytics.events_over_time('test-agent', bucket_size='1h')

        assert timeline == []

    def test_event_rate(self, client_with_data):
        """Test calculating event rate"""
        analytics = Analytics(client_with_data)

        rate = analytics.event_rate('test-agent', window_minutes=60)

        assert rate > 0  # Should have events in last hour
        assert isinstance(rate, float)

    def test_event_rate_empty(self):
        """Test event rate with no events"""
        client = AOPClient(storage='memory')
        analytics = Analytics(client)

        rate = analytics.event_rate('test-agent', window_minutes=60)

        assert rate == 0.0

    def test_invalid_bucket_size(self, client_with_data):
        """Test that invalid bucket size raises error"""
        analytics = Analytics(client_with_data)

        with pytest.raises(ValueError):
            analytics.events_over_time('test-agent', bucket_size='invalid')


class TestAnalyticsIntegration:
    """Integration tests for analytics"""

    def test_full_workflow(self):
        """Test complete analytics workflow"""
        client = AOPClient(storage='memory')
        analytics = Analytics(client)

        # Create some events
        correlation_id = 'workflow-test'

        call = client.mcp.log_tool_call(
            agent_id='workflow-agent',
            tool_name='step1',
            params={'input': 'test'},
            correlation_id=correlation_id
        )

        client.mcp.log_tool_result(
            agent_id='workflow-agent',
            tool_name='step1',
            result={'output': 'processed'},
            duration_ms=100,
            correlation_id=correlation_id,
            parent_id=call.id
        )

        # Reconstruct trace
        trace = analytics.reconstruct_trace(correlation_id=correlation_id)
        assert trace['event_count'] == 2

        # Get aggregations
        counts = analytics.count_by_tool('workflow-agent')
        assert counts['step1'] == 1

        # Get timeline
        timeline = analytics.events_over_time('workflow-agent')
        assert len(timeline) > 0

        # Get rate
        rate = analytics.event_rate('workflow-agent', window_minutes=1)
        assert rate > 0
