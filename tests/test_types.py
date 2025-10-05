"""
Tests for aop.types module
"""

import pytest
from aop.types import (
    VERSION,
    SUPPORTED_PROTOCOLS,
    Protocol,
    Severity,
    MCPEventType,
    A2AEventType,
    AP2EventType,
    ALL_EVENT_TYPES
)


class TestConstants:
    """Test module constants"""
    
    def test_version(self):
        """Test VERSION constant"""
        assert VERSION == "1.0"
        assert isinstance(VERSION, str)
    
    def test_supported_protocols(self):
        """Test SUPPORTED_PROTOCOLS list"""
        assert len(SUPPORTED_PROTOCOLS) == 3
        assert "mcp" in SUPPORTED_PROTOCOLS
        assert "a2a" in SUPPORTED_PROTOCOLS
        assert "ap2" in SUPPORTED_PROTOCOLS


class TestProtocolEnum:
    """Test Protocol enum"""
    
    def test_protocol_values(self):
        """Test Protocol enum has correct values"""
        assert Protocol.MCP.value == "mcp"
        assert Protocol.A2A.value == "a2a"
        assert Protocol.AP2.value == "ap2"
    
    def test_protocol_count(self):
        """Test Protocol enum has 3 members"""
        assert len(Protocol) == 3


class TestSeverityEnum:
    """Test Severity enum"""
    
    def test_severity_values(self):
        """Test Severity enum has correct values"""
        assert Severity.ERROR.value == "error"
        assert Severity.WARN.value == "warn"
        assert Severity.INFO.value == "info"
        assert Severity.DEBUG.value == "debug"
    
    def test_severity_count(self):
        """Test Severity enum has 4 members"""
        assert len(Severity) == 4


class TestMCPEventTypes:
    """Test MCP event type constants"""
    
    def test_mcp_lifecycle_events(self):
        """Test MCP lifecycle event types"""
        assert MCPEventType.SERVER_INITIALIZED == "mcp.server.initialized"
        assert MCPEventType.SERVER_SHUTDOWN == "mcp.server.shutdown"
    
    def test_mcp_tool_events(self):
        """Test MCP tool event types"""
        assert MCPEventType.TOOL_CALLED == "mcp.tool.called"
        assert MCPEventType.TOOL_COMPLETED == "mcp.tool.completed"
        assert MCPEventType.TOOL_ERROR == "mcp.tool.error"
        assert MCPEventType.TOOL_LIST_CHANGED == "mcp.tool.list_changed"
    
    def test_mcp_resource_events(self):
        """Test MCP resource event types"""
        assert MCPEventType.RESOURCE_READ == "mcp.resource.read"
        assert MCPEventType.RESOURCE_UPDATED == "mcp.resource.updated"
        assert MCPEventType.RESOURCE_LIST_CHANGED == "mcp.resource.list_changed"
    
    def test_mcp_prompt_events(self):
        """Test MCP prompt event types"""
        assert MCPEventType.PROMPT_GET == "mcp.prompt.get"
        assert MCPEventType.PROMPT_LIST_CHANGED == "mcp.prompt.list_changed"
    
    def test_mcp_sampling_events(self):
        """Test MCP sampling event types"""
        assert MCPEventType.SAMPLING_REQUESTED == "mcp.sampling.requested"
        assert MCPEventType.SAMPLING_COMPLETED == "mcp.sampling.completed"
    
    def test_mcp_error_event(self):
        """Test MCP error event type"""
        assert MCPEventType.ERROR == "mcp.error.found"
    
    def test_mcp_event_count(self):
        """Test MCP has 15 event types"""
        mcp_events = [
            attr for attr in dir(MCPEventType)
            if not attr.startswith('_')
        ]
        assert len(mcp_events) == 15


class TestA2AEventTypes:
    """Test A2A event type constants"""
    
    def test_a2a_task_events(self):
        """Test A2A task event types"""
        assert A2AEventType.TASK_ASSIGNED == "a2a.task.assigned"
        assert A2AEventType.TASK_ACCEPTED == "a2a.task.accepted"
        assert A2AEventType.TASK_REJECTED == "a2a.task.rejected"
        assert A2AEventType.TASK_COMPLETED == "a2a.task.completed"
        assert A2AEventType.TASK_FAILED == "a2a.task.failed"
    
    def test_a2a_message_events(self):
        """Test A2A message event types"""
        assert A2AEventType.MESSAGE_SENT == "a2a.message.sent"
        assert A2AEventType.MESSAGE_RECEIVED == "a2a.message.received"
    
    def test_a2a_agent_events(self):
        """Test A2A agent event types"""
        assert A2AEventType.AGENT_REGISTERED == "a2a.agent.registered"
        assert A2AEventType.AGENT_DEREGISTERED == "a2a.agent.deregistered"
    
    def test_a2a_delegation_event(self):
        """Test A2A delegation event type"""
        assert A2AEventType.DELEGATED == "a2a.task.delegated"
    
    def test_a2a_event_count(self):
        """Test A2A has 10 event types"""
        a2a_events = [
            attr for attr in dir(A2AEventType)
            if not attr.startswith('_')
        ]
        assert len(a2a_events) == 11


class TestAP2EventTypes:
    """Test AP2 event type constants"""
    
    def test_ap2_mandate_events(self):
        """Test AP2 mandate event types"""
        assert AP2EventType.MANDATE_CREATED == "ap2.mandate.created"
        assert AP2EventType.MANDATE_REVOKED == "ap2.mandate.revoked"
    
    def test_ap2_approval_events(self):
        """Test AP2 approval event types"""
        assert AP2EventType.APPROVAL_REQUESTED == "ap2.approval.requested"
        assert AP2EventType.APPROVAL_GRANTED == "ap2.approval.granted"
    
    def test_ap2_payment_events(self):
        """Test AP2 payment event types"""
        assert AP2EventType.PAYMENT_INITIATED == "ap2.payment.initiated"
        assert AP2EventType.PAYMENT_COMPLETED == "ap2.payment.completed"
    
    def test_ap2_event_count(self):
        """Test AP2 has 7 event types"""
        ap2_events = [
            attr for attr in dir(AP2EventType)
            if not attr.startswith('_')
        ]
        assert len(ap2_events) == 7


class TestAllEventTypes:
    """Test ALL_EVENT_TYPES list"""
    
    def test_all_event_types_count(self):
        """Test ALL_EVENT_TYPES has 33 event types (15 + 10 + 6)"""
        assert len(ALL_EVENT_TYPES) == 33
    
    def test_all_event_types_contains_mcp(self):
        """Test ALL_EVENT_TYPES contains MCP events"""
        assert "mcp.tool.called" in ALL_EVENT_TYPES
        assert "mcp.server.initialized" in ALL_EVENT_TYPES
    
    def test_all_event_types_contains_a2a(self):
        """Test ALL_EVENT_TYPES contains A2A events"""
        assert "a2a.task.assigned" in ALL_EVENT_TYPES
        assert "a2a.message.sent" in ALL_EVENT_TYPES
    
    def test_all_event_types_contains_ap2(self):
        """Test ALL_EVENT_TYPES contains AP2 events"""
        assert "ap2.mandate.created" in ALL_EVENT_TYPES
        assert "ap2.payment.initiated" in ALL_EVENT_TYPES
    
    def test_all_event_types_no_duplicates(self):
        """Test ALL_EVENT_TYPES has no duplicate entries"""
        assert len(ALL_EVENT_TYPES) == len(set(ALL_EVENT_TYPES))
    
    def test_all_event_types_format(self):
        """Test all event types follow correct format"""
        for event_type in ALL_EVENT_TYPES:
            # Must be string
            assert isinstance(event_type, str)
            # Must have at least 3 parts (protocol.category.action)
            parts = event_type.split('.')
            assert len(parts) >= 3
            # Must be lowercase
            assert event_type == event_type.lower()
            # First part must be valid protocol
            assert parts[0] in ['mcp', 'a2a', 'ap2']