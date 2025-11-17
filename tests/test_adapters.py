"""
Integration tests for protocol adapters.
"""

import pytest
from aop import AOPClient
from aop.trace import trace_context


@pytest.fixture
def client():
    """Create client with in-memory storage for testing"""
    return AOPClient(storage="memory")


class TestMCPAdapter:
    """Test MCP protocol adapter"""
    
    def test_tool_call_and_result_workflow(self, client):
        """Test tool call/result workflow with parent-child relationship"""
        # Log tool call
        call = client.mcp.log_tool_call(
            agent_id='agent-1',
            tool_name='web_search',
            params={'query': 'AOP protocol'}
        )
        
        # Verify call handle has ID
        assert call.id is not None
        
        # Log result with parent_id
        result = client.mcp.log_tool_result(
            agent_id='agent-1',
            tool_name='web_search',
            result={'count': 10, 'items': []},
            duration_ms=150,
            parent_id=call.id
        )
        
        # Query both events
        events = client.query(agent_id='agent-1')
        assert len(events) == 2
        
        # Verify parent-child relationship
        call_event = next(e for e in events if e['event_type'] == 'mcp.tool.called')
        result_event = next(e for e in events if e['event_type'] == 'mcp.tool.completed')
        
        assert result_event['parent_id'] == call_event['id']
        assert result_event['duration_ms'] == 150
    
    def test_sampling_request_and_response_workflow(self, client):
        """Test LLM sampling request/response workflow"""
        # Log sampling request
        request = client.mcp.log_sampling_request(
            agent_id='llm-agent',
            prompt='What is AOP?',
            model='gpt-4',
            max_tokens=100,
            temperature=0.7
        )
        
        # Log sampling response
        response = client.mcp.log_sampling_response(
            agent_id='llm-agent',
            completion='AOP is...',
            model='gpt-4',
            tokens_used=50,
            duration_ms=500,
            parent_id=request.id
        )
        
        # Query events
        events = client.query(agent_id='llm-agent')
        assert len(events) == 2
        
        # Find events by type
        req_event = next((e for e in events if e['event_type'] == 'mcp.sampling.requested'), None)
        resp_event = next((e for e in events if e['event_type'] == 'mcp.sampling.completed'), None)
        
        assert req_event is not None, f"Request event not found. Events: {[e['event_type'] for e in events]}"
        assert resp_event is not None, f"Response event not found. Events: {[e['event_type'] for e in events]}"
        
        assert req_event['data']['prompt'] == 'What is AOP?'
        assert resp_event['data']['completion'] == 'AOP is...'
        assert resp_event['parent_id'] == request.id
    
    def test_tool_error_logging(self, client):
        """Test tool error event logging"""
        # Log tool call
        call = client.mcp.log_tool_call(
            agent_id='agent-1',
            tool_name='api_call'
        )
        
        # Log error
        error = client.mcp.log_tool_error(
            agent_id='agent-1',
            tool_name='api_call',
            error_message='Connection timeout',
            error_code='TIMEOUT',
            details={'url': 'https://api.example.com'},
            parent_id=call.id
        )
        
        # Query error event
        events = client.query(severity='error')
        assert len(events) == 1
        
        error_event = events[0]
        assert error_event['event_type'] == 'mcp.tool.error'
        assert error_event['error']['code'] == 'TIMEOUT'
        assert error_event['error']['message'] == 'Connection timeout'
        assert error_event['parent_id'] == call.id
    
    def test_tool_execution_context_manager_success(self, client):
        """Test tool execution context manager with successful execution"""
        with client.mcp.tool_execution(
            agent_id='agent-1',
            tool_name='calculator',
            params={'expression': '2 + 2'}
        ) as call:
            # Simulate tool execution
            result = 4
            call.set_result(result, duration_ms=5)
        
        # Verify both events logged
        events = client.query(agent_id='agent-1')
        assert len(events) == 2
        
        call_event = next(e for e in events if e['event_type'] == 'mcp.tool.called')
        result_event = next(e for e in events if e['event_type'] == 'mcp.tool.completed')
        
        assert call_event['data']['tool_name'] == 'calculator'
        assert result_event['data']['result'] == 4
        assert result_event['parent_id'] == call_event['id']
    
    def test_tool_execution_context_manager_error(self, client):
        """Test tool execution context manager with error"""
        with pytest.raises(ValueError):
            with client.mcp.tool_execution(
                agent_id='agent-1',
                tool_name='risky_tool'
            ) as call:
                raise ValueError('Something went wrong')
        
        # Verify call and error events logged
        events = client.query(agent_id='agent-1')
        assert len(events) == 2
        
        call_event = next((e for e in events if e['event_type'] == 'mcp.tool.called'), None)
        error_event = next((e for e in events if e['event_type'] == 'mcp.tool.error'), None)
        
        assert call_event is not None
        assert error_event is not None
        assert error_event['error']['code'] == 'ValueError'
        assert 'Something went wrong' in error_event['error']['message']
        assert error_event['parent_id'] == call_event['id']
    
    def test_manual_correlation_vs_trace_context(self, client):
        """Test manual correlation_id vs trace context auto-correlation"""
        correlation_id = 'test-trace-123'
        
        # Manual correlation
        call1 = client.mcp.log_tool_call(
            agent_id='agent-1',
            tool_name='tool1',
            correlation_id=correlation_id
        )
        
        # Trace context auto-correlation
        with client.trace(correlation_id):
            call2 = client.mcp.log_tool_call(
                agent_id='agent-1',
                tool_name='tool2'
            )
        
        # Both should have same correlation_id
        events = client.query(correlation_id=correlation_id)
        assert len(events) == 2
        assert all(e['correlation_id'] == correlation_id for e in events)

    def test_observe_tool_decorator_async(self, client):
        """Test observe_tool decorator with async function"""

        # Define async function with decorator
        @client.mcp.observe_tool(agent_id='test-agent')
        async def async_search(query: str, limit: int = 10) -> dict:
            """Async search function"""
            return {'query': query, 'results': [], 'limit': limit}

        # Call the decorated function
        import asyncio
        result = asyncio.run(async_search('test query', limit=20))

        # Verify result is returned correctly
        assert result == {'query': 'test query', 'results': [], 'limit': 20}

        # Verify events were logged
        events = client.query(agent_id='test-agent')
        assert len(events) == 2

        # Verify call event
        call_event = next(e for e in events if e['event_type'] == 'mcp.tool.called')
        assert call_event['data']['tool_name'] == 'async_search'
        assert call_event['data']['params']['query'] == 'test query'
        assert call_event['data']['params']['limit'] == 20

        # Verify completion event
        result_event = next(e for e in events if e['event_type'] == 'mcp.tool.completed')
        assert result_event['data']['tool_name'] == 'async_search'
        assert result_event['data']['result'] == result
        assert result_event['parent_id'] == call_event['id']
        assert result_event['duration_ms'] is not None
        assert result_event['duration_ms'] >= 0

    def test_observe_tool_decorator_sync(self, client):
        """Test observe_tool decorator with sync function"""

        # Define sync function with decorator
        @client.mcp.observe_tool(agent_id='test-agent')
        def sync_calculator(a: int, b: int, operation: str = 'add') -> int:
            """Sync calculator function"""
            if operation == 'add':
                return a + b
            elif operation == 'multiply':
                return a * b
            return 0

        # Call the decorated function
        result = sync_calculator(5, 3, operation='multiply')

        # Verify result is correct
        assert result == 15

        # Verify events were logged
        events = client.query(agent_id='test-agent')
        assert len(events) == 2

        # Verify call event
        call_event = next(e for e in events if e['event_type'] == 'mcp.tool.called')
        assert call_event['data']['tool_name'] == 'sync_calculator'
        assert call_event['data']['params']['a'] == 5
        assert call_event['data']['params']['b'] == 3
        assert call_event['data']['params']['operation'] == 'multiply'

        # Verify completion event
        result_event = next(e for e in events if e['event_type'] == 'mcp.tool.completed')
        assert result_event['data']['result'] == 15
        assert result_event['parent_id'] == call_event['id']
        assert result_event['duration_ms'] is not None

    def test_observe_tool_decorator_error_handling_async(self, client):
        """Test observe_tool decorator error handling with async function"""

        @client.mcp.observe_tool(agent_id='test-agent')
        async def failing_async_tool(should_fail: bool) -> str:
            """Tool that can fail"""
            if should_fail:
                raise ValueError('Intentional failure')
            return 'success'

        # Call with error
        import asyncio
        with pytest.raises(ValueError, match='Intentional failure'):
            asyncio.run(failing_async_tool(should_fail=True))

        # Verify events were logged
        events = client.query(agent_id='test-agent')
        assert len(events) == 2

        # Verify call event
        call_event = next(e for e in events if e['event_type'] == 'mcp.tool.called')
        assert call_event['data']['params']['should_fail'] is True

        # Verify error event
        error_event = next(e for e in events if e['event_type'] == 'mcp.tool.error')
        assert error_event['error']['code'] == 'ValueError'
        assert 'Intentional failure' in error_event['error']['message']
        assert error_event['parent_id'] == call_event['id']

    def test_observe_tool_decorator_error_handling_sync(self, client):
        """Test observe_tool decorator error handling with sync function"""

        @client.mcp.observe_tool(agent_id='test-agent')
        def failing_sync_tool(divisor: int) -> float:
            """Tool that can fail"""
            return 100 / divisor

        # Call with error
        with pytest.raises(ZeroDivisionError):
            failing_sync_tool(0)

        # Verify events were logged
        events = client.query(agent_id='test-agent')
        assert len(events) == 2

        # Verify call event
        call_event = next(e for e in events if e['event_type'] == 'mcp.tool.called')
        assert call_event['data']['params']['divisor'] == 0

        # Verify error event
        error_event = next(e for e in events if e['event_type'] == 'mcp.tool.error')
        assert error_event['error']['code'] == 'ZeroDivisionError'
        assert error_event['parent_id'] == call_event['id']

    def test_observe_tool_decorator_with_metadata(self, client):
        """Test observe_tool decorator with custom metadata"""

        @client.mcp.observe_tool(
            agent_id='test-agent',
            metadata={'version': '1.0', 'environment': 'test'}
        )
        def tool_with_metadata(value: str) -> str:
            return value.upper()

        result = tool_with_metadata('hello')

        assert result == 'HELLO'

        # Verify metadata is logged
        events = client.query(agent_id='test-agent')
        call_event = next(e for e in events if e['event_type'] == 'mcp.tool.called')
        assert call_event['metadata']['version'] == '1.0'
        assert call_event['metadata']['environment'] == 'test'

    def test_observe_tool_decorator_preserves_function_metadata(self, client):
        """Test that decorator preserves function name and docstring"""

        @client.mcp.observe_tool(agent_id='test-agent')
        def documented_tool(x: int) -> int:
            """This is a documented tool."""
            return x * 2

        # Verify function metadata is preserved
        assert documented_tool.__name__ == 'documented_tool'
        assert documented_tool.__doc__ == 'This is a documented tool.'


class TestA2AAdapter:
    """Test A2A protocol adapter"""
    
    def test_task_assignment_and_completion_workflow(self, client):
        """Test task assignment/completion workflow"""
        # Assign task
        task = client.a2a.log_task_assigned(
            agent_id='orchestrator',
            task_id='task-123',
            assignee='worker-1',
            task_type='research',
            description='Research market trends'
        )
        
        # Complete task
        completion = client.a2a.log_task_completed(
            agent_id='worker-1',
            task_id='task-123',
            result={'status': 'success', 'findings': []},
            duration_ms=5000,
            parent_id=task.id
        )
        
        # Query events
        events = client.query()
        assert len(events) == 2
        
        task_event = next(e for e in events if e['event_type'] == 'a2a.task.assigned')
        comp_event = next(e for e in events if e['event_type'] == 'a2a.task.completed')
        
        assert task_event['data']['assignee'] == 'worker-1'
        assert comp_event['parent_id'] == task.id
    
    def test_message_sent_and_received_workflow(self, client):
        """Test message sent/received workflow"""
        # Send message
        sent = client.a2a.log_message_sent(
            agent_id='agent-1',
            recipient='agent-2',
            content={'action': 'start', 'params': {}},
            message_type='command'
        )
        
        # Receive message
        received = client.a2a.log_message_received(
            agent_id='agent-2',
            sender='agent-1',
            content={'action': 'start', 'params': {}},
            message_type='command',
            parent_id=sent.id
        )
        
        # Verify
        events = client.query()
        assert len(events) == 2
        
        sent_event = next(e for e in events if e['event_type'] == 'a2a.message.sent')
        recv_event = next(e for e in events if e['event_type'] == 'a2a.message.received')
        
        assert sent_event['data']['recipient'] == 'agent-2'
        assert recv_event['data']['sender'] == 'agent-1'
        assert recv_event['parent_id'] == sent.id
    
    def test_multiple_agents_collaboration(self, client):
        """Test multi-agent collaboration trace"""
        correlation_id = 'collab-trace'
        
        # Orchestrator assigns task
        client.a2a.log_task_assigned(
            agent_id='orchestrator',
            task_id='task-456',
            assignee='worker-1',
            correlation_id=correlation_id
        )
        
        # Worker receives and processes
        client.a2a.log_message_received(
            agent_id='worker-1',
            sender='orchestrator',
            content='task assignment',
            correlation_id=correlation_id
        )
        
        # Query trace
        trace = client.get_trace(correlation_id)
        assert len(trace) == 2
        
        # Verify both agents in trace
        agents = {e['agent_id'] for e in trace}
        assert 'orchestrator' in agents
        assert 'worker-1' in agents
    
    def test_task_with_trace_context(self, client):
        """Test task events with trace context auto-correlation"""
        correlation_id = 'task-trace'
        
        with client.trace(correlation_id):
            task = client.a2a.log_task_assigned(
                agent_id='orchestrator',
                task_id='task-789',
                assignee='worker-1'
            )
            
            completion = client.a2a.log_task_completed(
                agent_id='worker-1',
                task_id='task-789',
                result={'done': True}
            )
        
        # Verify auto-correlation
        trace = client.get_trace(correlation_id)
        assert len(trace) == 2
        assert all(e['correlation_id'] == correlation_id for e in trace)


class TestAP2Adapter:
    """Test AP2 protocol adapter"""
    
    def test_payment_success_flow(self, client):
        """Test successful payment flow"""
        # Initiate payment
        payment = client.ap2.log_payment_initiated(
            agent_id='payment-agent',
            payment_id='pay-123',
            amount=99.99,
            currency='USD',
            payment_method='CARD'
        )
        
        # Complete payment
        completion = client.ap2.log_payment_completed(
            agent_id='payment-agent',
            payment_id='pay-123',
            transaction_id='txn-456',
            amount=99.99,
            currency='USD',
            duration_ms=2000,
            parent_id=payment.id
        )
        
        # Verify
        events = client.query(agent_id='payment-agent')
        assert len(events) == 2
        
        init_event = next(e for e in events if e['event_type'] == 'ap2.payment.initiated')
        comp_event = next(e for e in events if e['event_type'] == 'ap2.payment.completed')
        
        assert init_event['data']['amount'] == 99.99
        assert comp_event['data']['transaction_id'] == 'txn-456'
        assert comp_event['parent_id'] == payment.id
    
    def test_payment_failure_flow(self, client):
        """Test payment failure flow"""
        # Initiate payment
        payment = client.ap2.log_payment_initiated(
            agent_id='payment-agent',
            payment_id='pay-789',
            amount=200.00,
            currency='USD'
        )
        
        # Payment fails
        failure = client.ap2.log_payment_failed(
            agent_id='payment-agent',
            payment_id='pay-789',
            error_code='INSUFFICIENT_FUNDS',
            error_message='Payment declined',
            details={'reason': 'card limit exceeded'},
            parent_id=payment.id
        )
        
        # Verify error event
        events = client.query(severity='error')
        assert len(events) == 1
        
        fail_event = events[0]
        assert fail_event['event_type'] == 'ap2.payment.failed'
        assert fail_event['error']['code'] == 'INSUFFICIENT_FUNDS'
        assert fail_event['parent_id'] == payment.id
    
    def test_payment_with_trace_context(self, client):
        """Test payment flow with trace context"""
        correlation_id = 'payment-trace'
        
        with client.trace(correlation_id):
            payment = client.ap2.log_payment_initiated(
                agent_id='payment-agent',
                payment_id='pay-999',
                amount=50.00,
                currency='EUR'
            )
            
            completion = client.ap2.log_payment_completed(
                agent_id='payment-agent',
                payment_id='pay-999',
                transaction_id='txn-999'
            )
        
        # Verify auto-correlation
        trace = client.get_trace(correlation_id)
        assert len(trace) == 2
        assert all(e['correlation_id'] == correlation_id for e in trace)


class TestTraceContext:
    """Test trace context manager"""
    
    def test_basic_trace_context(self, client):
        """Test basic trace context auto-correlation"""
        correlation_id = 'trace-basic'
        
        with client.trace(correlation_id):
            client.mcp.log_tool_call(
                agent_id='agent-1',
                tool_name='tool1'
            )
            client.a2a.log_task_assigned(
                agent_id='agent-2',
                task_id='task-1',
                assignee='agent-3'
            )
            client.ap2.log_payment_initiated(
                agent_id='agent-4',
                payment_id='pay-1',
                amount=10.00,
                currency='USD'
            )
        
        # All events should have same correlation_id
        trace = client.get_trace(correlation_id)
        assert len(trace) == 3
        assert all(e['correlation_id'] == correlation_id for e in trace)
        
        # Verify different protocols
        protocols = {e['protocol'] for e in trace}
        assert protocols == {'mcp', 'a2a', 'ap2'}
    
    def test_nested_trace_contexts(self, client):
        """Test nested trace contexts"""
        outer_id = 'outer-trace'
        inner_id = 'inner-trace'
        
        with client.trace(outer_id):
            client.mcp.log_tool_call(
                agent_id='agent-1',
                tool_name='outer-tool'
            )
            
            with client.trace(inner_id):
                client.mcp.log_tool_call(
                    agent_id='agent-1',
                    tool_name='inner-tool'
                )
            
            # After inner context, outer should be restored
            client.mcp.log_tool_call(
                agent_id='agent-1',
                tool_name='outer-tool-2'
            )
        
        # Verify outer trace has 2 events
        outer_trace = client.get_trace(outer_id)
        assert len(outer_trace) == 2
        
        # Verify inner trace has 1 event
        inner_trace = client.get_trace(inner_id)
        assert len(inner_trace) == 1
    
    def test_manual_correlation_overrides_trace_context(self, client):
        """Test that explicit correlation_id overrides trace context"""
        context_id = 'context-trace'
        override_id = 'override-trace'
        
        with client.trace(context_id):
            # This uses context
            client.mcp.log_tool_call(
                agent_id='agent-1',
                tool_name='tool1'
            )
            
            # This overrides context
            client.mcp.log_tool_call(
                agent_id='agent-1',
                tool_name='tool2',
                correlation_id=override_id
            )
        
        # Verify separation
        context_trace = client.get_trace(context_id)
        override_trace = client.get_trace(override_id)
        
        assert len(context_trace) == 1
        assert len(override_trace) == 1
        assert context_trace[0]['data']['tool_name'] == 'tool1'
        assert override_trace[0]['data']['tool_name'] == 'tool2'