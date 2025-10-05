"""
Tests for aop.events module
"""

import pytest
from aop.events import (
    build_event,
    build_mcp_event,
    build_a2a_event,
    build_ap2_event,
    build_tool_call_event,
    build_tool_result_event,
    build_task_event,
    build_payment_event,
    build_error_event
)
from aop.exceptions import AOPEventError, AOPValidationError
from aop.utils import validate_uuid, validate_timestamp


class TestBuildEvent:
    """Test generic event builder"""
    
    def test_builds_valid_event(self):
        """Test that build_event creates valid event"""
        event = build_event(
            agent_id='test-agent',
            event_type='mcp.tool.called'
        )
        
        assert event['agent_id'] == 'test-agent'
        assert event['event_type'] == 'mcp.tool.called'
    
    def test_auto_fills_required_fields(self):
        """Test that required fields are auto-filled"""
        event = build_event(
            agent_id='test-agent',
            event_type='mcp.tool.called'
        )
        
        # Check auto-filled fields
        assert 'id' in event
        assert 'version' in event
        assert 'timestamp' in event
        assert 'instance_id' in event
        assert 'protocol' in event
        
        assert event['version'] == '1.0'
        assert validate_uuid(event['id'])
        assert validate_timestamp(event['timestamp'])
        assert validate_uuid(event['instance_id'])
    
    def test_extracts_protocol_from_event_type(self):
        """Test that protocol is extracted from event_type"""
        event = build_event(
            agent_id='test-agent',
            event_type='a2a.task.assigned'
        )
        
        assert event['protocol'] == 'a2a'
    
    def test_uses_same_id_for_instance_id_by_default(self):
        """Test that instance_id equals id by default"""
        event = build_event(
            agent_id='test-agent',
            event_type='mcp.tool.called'
        )
        
        assert event['id'] == event['instance_id']
    
    def test_allows_custom_instance_id(self):
        """Test that custom instance_id can be provided"""
        from aop.utils import generate_uuid_v7
        custom_instance_id = generate_uuid_v7()
        event = build_event(
            agent_id='test-agent',
            event_type='mcp.tool.called',
            instance_id=custom_instance_id
        )
        
        assert event['instance_id'] == custom_instance_id
        assert event['id'] != event['instance_id']
    
    def test_includes_optional_fields(self):
        """Test that optional fields are included when provided"""
        event = build_event(
            agent_id='test-agent',
            event_type='mcp.tool.called',
            correlation_id='trace-123',
            parent_id='parent-456',
            severity='info',
            duration_ms=100,
            data={'key': 'value'},
            metadata={'meta': 'data'}
        )
        
        assert event['correlation_id'] == 'trace-123'
        assert event['parent_id'] == 'parent-456'
        assert event['severity'] == 'info'
        assert event['duration_ms'] == 100
        assert event['data'] == {'key': 'value'}
        assert event['metadata'] == {'meta': 'data'}
    
    def test_validates_by_default(self):
        """Test that validation runs by default"""
        # Use AOPValidationError since validation happens before wrapping
        with pytest.raises((AOPValidationError, AOPEventError)):
            build_event(
                agent_id='',  # Invalid: empty agent_id
                event_type='mcp.tool.called'
            )
    
    def test_can_skip_validation(self):
        """Test that validation can be skipped"""
        event = build_event(
            agent_id='',  # Would fail validation
            event_type='mcp.tool.called',
            validate=False
        )
        
        assert event['agent_id'] == ''


class TestBuildMCPEvent:
    """Test MCP event builder"""
    
    def test_builds_mcp_event(self):
        """Test that MCP event is built correctly"""
        event = build_mcp_event(
            agent_id='test-agent',
            event_type='mcp.tool.called'
        )
        
        assert event['protocol'] == 'mcp'
        assert event['event_type'] == 'mcp.tool.called'
    
    def test_rejects_non_mcp_event_type(self):
        """Test that non-MCP event type raises error"""
        with pytest.raises(AOPEventError) as exc_info:
            build_mcp_event(
                agent_id='test-agent',
                event_type='a2a.task.assigned'  # Wrong protocol
            )
        
        assert 'mcp.' in str(exc_info.value)


class TestBuildA2AEvent:
    """Test A2A event builder"""
    
    def test_builds_a2a_event(self):
        """Test that A2A event is built correctly"""
        event = build_a2a_event(
            agent_id='test-agent',
            event_type='a2a.task.assigned'
        )
        
        assert event['protocol'] == 'a2a'
        assert event['event_type'] == 'a2a.task.assigned'
    
    def test_rejects_non_a2a_event_type(self):
        """Test that non-A2A event type raises error"""
        with pytest.raises(AOPEventError) as exc_info:
            build_a2a_event(
                agent_id='test-agent',
                event_type='mcp.tool.called'  # Wrong protocol
            )
        
        assert 'a2a.' in str(exc_info.value)


class TestBuildAP2Event:
    """Test AP2 event builder"""
    
    def test_builds_ap2_event(self):
        """Test that AP2 event is built correctly"""
        event = build_ap2_event(
            agent_id='test-agent',
            event_type='ap2.payment.initiated'
        )
        
        assert event['protocol'] == 'ap2'
        assert event['event_type'] == 'ap2.payment.initiated'
    
    def test_rejects_non_ap2_event_type(self):
        """Test that non-AP2 event type raises error"""
        with pytest.raises(AOPEventError) as exc_info:
            build_ap2_event(
                agent_id='test-agent',
                event_type='mcp.tool.called'  # Wrong protocol
            )
        
        assert 'ap2.' in str(exc_info.value)


class TestBuildToolCallEvent:
    """Test tool call convenience builder"""
    
    def test_builds_tool_call_event(self):
        """Test that tool call event is built correctly"""
        event = build_tool_call_event(
            agent_id='test-agent',
            tool_name='web_search',
            params={'query': 'test'}
        )
        
        assert event['event_type'] == 'mcp.tool.called'
        assert event['data']['tool_name'] == 'web_search'
        assert event['data']['params'] == {'query': 'test'}
    
    def test_tool_call_without_params(self):
        """Test tool call without parameters"""
        event = build_tool_call_event(
            agent_id='test-agent',
            tool_name='get_time'
        )
        
        assert event['data']['tool_name'] == 'get_time'
        assert 'params' not in event['data']


class TestBuildToolResultEvent:
    """Test tool result convenience builder"""
    
    def test_builds_tool_result_event(self):
        """Test that tool result event is built correctly"""
        event = build_tool_result_event(
            agent_id='test-agent',
            tool_name='web_search',
            result={'results': ['item1', 'item2']}
        )
        
        assert event['event_type'] == 'mcp.tool.completed'
        assert event['data']['tool_name'] == 'web_search'
        assert event['data']['result'] == {'results': ['item1', 'item2']}
    
    def test_tool_result_with_tracing(self):
        """Test tool result with correlation_id and parent_id"""
        event = build_tool_result_event(
            agent_id='test-agent',
            tool_name='web_search',
            result={'status': 'ok'},
            correlation_id='trace-123',
            parent_id='parent-456',
            duration_ms=150
        )
        
        assert event['correlation_id'] == 'trace-123'
        assert event['parent_id'] == 'parent-456'
        assert event['duration_ms'] == 150


class TestBuildTaskEvent:
    """Test task event convenience builder"""
    
    def test_builds_task_event(self):
        """Test that task event is built correctly"""
        event = build_task_event(
            agent_id='orchestrator',
            task_type='research',
            task_id='task-123'
        )
        
        assert event['event_type'] == 'a2a.task.assigned'
        assert event['data']['task_type'] == 'research'
        assert event['data']['task_id'] == 'task-123'
    
    def test_task_event_with_description(self):
        """Test task event with description and assignee"""
        event = build_task_event(
            agent_id='orchestrator',
            task_type='analysis',
            task_id='task-456',
            description='Analyze market data',
            assignee='analyst-agent'
        )
        
        assert event['data']['description'] == 'Analyze market data'
        assert event['data']['assignee'] == 'analyst-agent'


class TestBuildPaymentEvent:
    """Test payment event convenience builder"""
    
    def test_builds_payment_event(self):
        """Test that payment event is built correctly"""
        event = build_payment_event(
            agent_id='payment-agent',
            payment_id='pay-123',
            amount=99.99,
            currency='USD'
        )
        
        assert event['event_type'] == 'ap2.payment.initiated'
        assert event['data']['payment_id'] == 'pay-123'
        assert event['data']['amount'] == 99.99
        assert event['data']['currency'] == 'USD'
    
    def test_payment_event_with_method(self):
        """Test payment event with payment method"""
        event = build_payment_event(
            agent_id='payment-agent',
            payment_id='pay-456',
            amount=199.99,
            currency='EUR',
            payment_method='CARD'
        )
        
        assert event['data']['payment_method'] == 'CARD'


class TestBuildErrorEvent:
    """Test error event convenience builder"""
    
    def test_builds_error_event(self):
        """Test that error event is built correctly"""
        event = build_error_event(
            agent_id='test-agent',
            protocol='mcp',
            error_code='TOOL_ERROR',
            error_message='Tool execution failed'
        )
        
        # Error events use protocol.error format by default
        assert event['event_type'] == 'mcp.error.found'
        assert event['severity'] == 'error'
        assert event['error']['code'] == 'TOOL_ERROR'
        assert event['error']['message'] == 'Tool execution failed'
    
    def test_error_event_with_details(self):
        """Test error event with details and stack trace"""
        event = build_error_event(
            agent_id='test-agent',
            protocol='a2a',
            error_code='TASK_FAILED',
            error_message='Task execution failed',
            details={'task_id': 'task-123'},
            stack_trace='line 1\nline 2'
        )
        
        # A2A error uses the default pattern
        assert event['event_type'] == 'a2a.error.occurred'
        assert event['error']['details'] == {'task_id': 'task-123'}
        assert event['error']['stack_trace'] == 'line 1\nline 2'
    
    def test_error_event_custom_type(self):
        """Test error event with custom event_type"""
        event = build_error_event(
            agent_id='test-agent',
            protocol='mcp',
            error_code='CUSTOM_ERROR',
            error_message='Custom error occurred',
            event_type='mcp.tool.error'
        )
        
        assert event['event_type'] == 'mcp.tool.error'