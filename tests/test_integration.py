"""
Integration tests for AOP - End-to-end scenarios
"""

import pytest
import os
import tempfile
from aop import (
    AOPClient,
    build_tool_call_event,
    build_tool_result_event,
    build_task_event,
    build_payment_event,
    build_error_event
)


@pytest.fixture
def client():
    """Create temporary client for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    client = AOPClient(db_path)
    yield client
    
    client.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestCompleteWorkflow:
    """Test complete event workflow"""
    
    def test_build_log_query_workflow(self, client):
        """Test complete workflow: build → log → query"""
        # Build event
        event = build_tool_call_event(
            agent_id='my-agent',
            tool_name='web_search',
            params={'query': 'AOP protocol'}
        )
        
        # Log event
        event_id = client.log_event(event, auto_build=False)
        
        # Query event
        events = client.query(agent_id='my-agent')
        
        assert len(events) == 1
        assert events[0]['id'] == event_id
        assert events[0]['data']['tool_name'] == 'web_search'
    
    def test_simple_trace_workflow(self, client):
        """Test simple trace: start → end"""
        correlation_id = 'trace-simple'
        
        # Log start event
        start_event = build_tool_call_event(
            agent_id='agent-1',
            tool_name='search',
            correlation_id=correlation_id
        )
        start_id = client.log_event(start_event, auto_build=False)
        
        # Log end event
        end_event = build_tool_result_event(
            agent_id='agent-1',
            tool_name='search',
            result={'status': 'ok'},
            correlation_id=correlation_id,
            parent_id=start_id,
            duration_ms=150
        )
        client.log_event(end_event, auto_build=False)
        
        # Get trace
        trace = client.get_trace(correlation_id)
        
        assert len(trace) == 2
        assert trace[0]['event_type'] == 'mcp.tool.called'
        assert trace[1]['event_type'] == 'mcp.tool.completed'
        assert trace[1]['parent_id'] == start_id


class TestMultiAgentScenario:
    """Test multi-agent collaboration"""
    
    def test_orchestrator_worker_pattern(self, client):
        """Test orchestrator delegating to worker agents"""
        correlation_id = 'trace-multi-agent'
        
        # Orchestrator assigns task
        task_event = build_task_event(
            agent_id='orchestrator',
            task_type='research',
            task_id='task-123',
            description='Research market trends',
            assignee='worker-1',
            correlation_id=correlation_id
        )
        client.log_event(task_event, auto_build=False)
        
        # Worker executes tool
        tool_event = build_tool_call_event(
            agent_id='worker-1',
            tool_name='web_search',
            params={'query': 'market trends'},
            correlation_id=correlation_id
        )
        client.log_event(tool_event, auto_build=False)
        
        # Get trace
        trace = client.get_trace(correlation_id)
        
        assert len(trace) == 2
        # Verify both agents in trace
        agents = {e['agent_id'] for e in trace}
        assert 'orchestrator' in agents
        assert 'worker-1' in agents
    
    def test_cross_protocol_trace(self, client):
        """Test trace spanning multiple protocols"""
        correlation_id = 'trace-cross-protocol'
        
        # A2A: Task assignment
        client.log_event({
            'agent_id': 'orchestrator',
            'event_type': 'a2a.task.assigned',
            'correlation_id': correlation_id,
            'data': {'task_id': 'task-456'}
        })
        
        # MCP: Tool execution
        client.log_event({
            'agent_id': 'worker',
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id,
            'data': {'tool_name': 'database_query'}
        })
        
        # AP2: Payment initiation
        client.log_event({
            'agent_id': 'payment-agent',
            'event_type': 'ap2.payment.initiated',
            'correlation_id': correlation_id,
            'data': {'payment_id': 'pay-789', 'amount': 10.00}
        })
        
        # Get trace
        trace = client.get_trace(correlation_id)
        
        assert len(trace) == 3
        protocols = {e['protocol'] for e in trace}
        assert protocols == {'a2a', 'mcp', 'ap2'}


class TestErrorHandling:
    """Test error scenarios"""
    
    def test_log_error_event(self, client):
        """Test logging error event"""
        error_event = build_error_event(
            agent_id='my-agent',
            protocol='mcp',
            error_code='TOOL_FAILED',
            error_message='Tool execution failed',
            details={'tool': 'web_search', 'reason': 'timeout'}
        )
        
        event_id = client.log_event(error_event, auto_build=False)
        
        # Query error
        events = client.query(severity='error')
        
        assert len(events) == 1
        assert events[0]['error']['code'] == 'TOOL_FAILED'
        assert events[0]['error']['details']['tool'] == 'web_search'
    
    def test_trace_with_error(self, client):
        """Test trace containing error event"""
        correlation_id = 'trace-with-error'
        
        # Start
        client.log_event({
            'agent_id': 'agent-1',
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id,
            'data': {'tool_name': 'api_call'}
        })
        
        # Error
        error_event = build_error_event(
            agent_id='agent-1',
            protocol='mcp',
            error_code='API_ERROR',
            error_message='API returned 500',
            correlation_id=correlation_id
        )
        client.log_event(error_event, auto_build=False)
        
        # Get trace
        trace = client.get_trace(correlation_id)
        
        assert len(trace) == 2
        # Find error event
        error_events = [e for e in trace if 'error' in e and e['error']]
        assert len(error_events) == 1
        assert error_events[0]['error']['code'] == 'API_ERROR'


class TestToolExecutionTracing:
    """Test tool execution tracing"""
    
    def test_tool_call_and_result(self, client):
        """Test tool call and result tracking"""
        correlation_id = 'tool-trace'
        
        # Tool call
        call_event = build_tool_call_event(
            agent_id='agent-1',
            tool_name='calculator',
            params={'expression': '2 + 2'},
            correlation_id=correlation_id
        )
        call_id = client.log_event(call_event, auto_build=False)
        
        # Tool result
        result_event = build_tool_result_event(
            agent_id='agent-1',
            tool_name='calculator',
            result={'answer': 4},
            correlation_id=correlation_id,
            parent_id=call_id,
            duration_ms=5
        )
        client.log_event(result_event, auto_build=False)
        
        # Verify
        trace = client.get_trace(correlation_id)
        assert len(trace) == 2
        assert trace[0]['event_type'] == 'mcp.tool.called'
        assert trace[1]['event_type'] == 'mcp.tool.completed'
        assert trace[1]['duration_ms'] == 5
    
    def test_nested_tool_calls(self, client):
        """Test nested tool execution"""
        correlation_id = 'nested-tools'
        
        # Parent tool
        parent_event = build_tool_call_event(
            agent_id='agent-1',
            tool_name='process_data',
            correlation_id=correlation_id
        )
        parent_id = client.log_event(parent_event, auto_build=False)
        
        # Child tool 1
        child1_event = build_tool_call_event(
            agent_id='agent-1',
            tool_name='fetch_data',
            correlation_id=correlation_id,
            parent_id=parent_id
        )
        client.log_event(child1_event, auto_build=False)
        
        # Child tool 2
        child2_event = build_tool_call_event(
            agent_id='agent-1',
            tool_name='transform_data',
            correlation_id=correlation_id,
            parent_id=parent_id
        )
        client.log_event(child2_event, auto_build=False)
        
        # Verify
        trace = client.get_trace(correlation_id)
        assert len(trace) == 3
        
        # Check parent-child relationships
        children = [e for e in trace if e.get('parent_id') == parent_id]
        assert len(children) == 2


class TestPaymentFlowTracing:
    """Test payment flow tracing"""
    
    def test_complete_payment_flow(self, client):
        """Test complete payment flow"""
        correlation_id = 'payment-flow'
        
        # Payment initiated
        payment_event = build_payment_event(
            agent_id='payment-agent',
            payment_id='pay-123',
            amount=99.99,
            currency='USD',
            payment_method='CARD',
            correlation_id=correlation_id
        )
        client.log_event(payment_event, auto_build=False)
        
        # Payment completed
        client.log_event({
            'agent_id': 'payment-agent',
            'event_type': 'ap2.payment.completed',
            'correlation_id': correlation_id,
            'data': {
                'payment_id': 'pay-123',
                'transaction_id': 'txn-456',
                'amount': 99.99
            },
            'duration_ms': 2000
        })
        
        # Verify
        trace = client.get_trace(correlation_id)
        assert len(trace) == 2
        assert trace[0]['event_type'] == 'ap2.payment.initiated'
        assert trace[1]['event_type'] == 'ap2.payment.completed'
        assert trace[1]['data']['transaction_id'] == 'txn-456'


class TestRealWorldScenarios:
    """Test real-world use cases"""
    
    def test_research_agent_workflow(self, client):
        """Test research agent workflow"""
        correlation_id = 'research-workflow'
        agent_id = 'research-agent'
        
        # 1. Receive task
        client.log_event({
            'agent_id': agent_id,
            'event_type': 'a2a.task.assigned',
            'correlation_id': correlation_id,
            'data': {'task_type': 'research', 'topic': 'AI trends'}
        })
        
        # 2. Search web
        client.log_event({
            'agent_id': agent_id,
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id,
            'data': {'tool_name': 'web_search', 'params': {'query': 'AI trends 2025'}}
        })
        
        # 3. Search results
        client.log_event({
            'agent_id': agent_id,
            'event_type': 'mcp.tool.completed',
            'correlation_id': correlation_id,
            'data': {'tool_name': 'web_search', 'result': {'count': 10}}
        })
        
        # 4. Complete task
        client.log_event({
            'agent_id': agent_id,
            'event_type': 'a2a.task.completed',
            'correlation_id': correlation_id,
            'data': {'task_id': 'task-123', 'summary': 'Research complete'}
        })
        
        # Verify complete workflow
        trace = client.get_trace(correlation_id)
        assert len(trace) == 4
        
        # Verify workflow steps
        event_types = [e['event_type'] for e in trace]
        assert 'a2a.task.assigned' in event_types
        assert 'mcp.tool.called' in event_types
        assert 'mcp.tool.completed' in event_types
        assert 'a2a.task.completed' in event_types
    
    def test_agent_collaboration_scenario(self, client):
        """Test multiple agents collaborating"""
        correlation_id = 'collaboration'
        
        # Agent 1: Data collector
        client.log_event({
            'agent_id': 'collector',
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id,
            'data': {'tool_name': 'fetch_data'}
        })
        
        # Agent 1 → Agent 2: Pass data
        client.log_event({
            'agent_id': 'collector',
            'event_type': 'a2a.message.sent',
            'correlation_id': correlation_id,
            'data': {'recipient': 'analyzer', 'content': 'data_ready'}
        })
        
        # Agent 2: Analyze data
        client.log_event({
            'agent_id': 'analyzer',
            'event_type': 'a2a.message.received',
            'correlation_id': correlation_id,
            'data': {'sender': 'collector', 'content': 'data_ready'}
        })
        
        # Agent 2: Process
        client.log_event({
            'agent_id': 'analyzer',
            'event_type': 'mcp.tool.called',
            'correlation_id': correlation_id,
            'data': {'tool_name': 'analyze'}
        })
        
        # Verify collaboration
        trace = client.get_trace(correlation_id)
        assert len(trace) == 4
        
        # Check both agents participated
        agents = {e['agent_id'] for e in trace}
        assert agents == {'collector', 'analyzer'}


class TestDataIntegrity:
    """Test data integrity"""
    
    def test_all_fields_preserved(self, client):
        """Test that all fields are preserved correctly"""
        event = {
            'agent_id': 'test-agent',
            'event_type': 'mcp.tool.called',
            'correlation_id': 'test-trace',
            'parent_id': 'parent-123',
            'severity': 'info',
            'duration_ms': 100,
            'data': {'complex': {'nested': {'value': 123}}},
            'metadata': {'key1': 'value1', 'key2': 'value2'}
        }
        
        event_id = client.log_event(event)
        
        # Retrieve and verify
        events = client.query(agent_id='test-agent')
        retrieved = events[0]
        
        assert retrieved['agent_id'] == 'test-agent'
        assert retrieved['event_type'] == 'mcp.tool.called'
        assert retrieved['correlation_id'] == 'test-trace'
        assert retrieved['parent_id'] == 'parent-123'
        assert retrieved['severity'] == 'info'
        assert retrieved['duration_ms'] == 100
        assert retrieved['data']['complex']['nested']['value'] == 123
        assert retrieved['metadata'] == {'key1': 'value1', 'key2': 'value2'}