"""
AOP Type Definitions
Contains all type hints, enums, and constants for the AOP protocol.
"""

from typing import TypedDict, Optional, Dict, Any, Literal, List
from enum import Enum

# ============================================================================
# SECTION 1: CONSTANTS
# ============================================================================

VERSION = "1.0"

SUPPORTED_PROTOCOLS = ["mcp", "a2a", "ap2"]

# ============================================================================
# SECTION 2: ENUMS
# ============================================================================

class Protocol(str, Enum):
    """Supported protocol types"""
    MCP = "mcp"
    A2A = "a2a"
    AP2 = "ap2"


class Severity(str, Enum):
    """Event severity levels"""
    ERROR = "error"
    WARN = "warn"
    INFO = "info"
    DEBUG = "debug"


# ============================================================================
# SECTION 3: EVENT TYPE CONSTANTS
# ============================================================================

# MCP Event Types (15 total)
class MCPEventType:
    """Model Context Protocol event types"""
    # Lifecycle
    SERVER_INITIALIZED = "mcp.server.initialized"
    SERVER_SHUTDOWN = "mcp.server.shutdown"
    
    # Tool Events
    TOOL_CALLED = "mcp.tool.called"
    TOOL_COMPLETED = "mcp.tool.completed"
    TOOL_ERROR = "mcp.tool.error"
    TOOL_LIST_CHANGED = "mcp.tool.list_changed"
    
    # Resource Events
    RESOURCE_READ = "mcp.resource.read"
    RESOURCE_UPDATED = "mcp.resource.updated"
    RESOURCE_LIST_CHANGED = "mcp.resource.list_changed"
    
    # Prompt Events
    PROMPT_GET = "mcp.prompt.get"
    PROMPT_LIST_CHANGED = "mcp.prompt.list_changed"
    
    # Sampling Events
    SAMPLING_REQUESTED = "mcp.sampling.requested"
    SAMPLING_COMPLETED = "mcp.sampling.completed"
    
    # Root List Events
    ROOTS_LIST_CHANGED = "mcp.roots.list_changed"
    
    # Error Events
    ERROR = "mcp.error.found"


# A2A Event Types (10 total)
class A2AEventType:
    """Agent-to-Agent protocol event types"""
    # Task Events
    TASK_ASSIGNED = "a2a.task.assigned"
    TASK_ACCEPTED = "a2a.task.accepted"
    TASK_REJECTED = "a2a.task.rejected"
    TASK_COMPLETED = "a2a.task.completed"
    TASK_FAILED = "a2a.task.failed"
    
    # Message Events
    MESSAGE_SENT = "a2a.message.sent"
    MESSAGE_RECEIVED = "a2a.message.received"
    
    # Agent Events
    AGENT_REGISTERED = "a2a.agent.registered"
    AGENT_DEREGISTERED = "a2a.agent.deregistered"
    
    # Delegation Events
    DELEGATED = "a2a.task.delegated"

    #Error Events
    ERROR = "a2a.error.occurred"


# AP2 Event Types (6 total)
class AP2EventType:
    """Agent Payments Protocol event types"""
    # Mandate Events
    MANDATE_CREATED = "ap2.mandate.created"
    MANDATE_REVOKED = "ap2.mandate.revoked"
    
    # Approval Events
    APPROVAL_REQUESTED = "ap2.approval.requested"
    APPROVAL_GRANTED = "ap2.approval.granted"
    
    # Payment Events
    PAYMENT_INITIATED = "ap2.payment.initiated"
    PAYMENT_COMPLETED = "ap2.payment.completed"

    # Error Events
    ERROR = "ap2.error.occurred"


# All valid event types (for validation)
ALL_EVENT_TYPES = (
    # MCP
    [MCPEventType.SERVER_INITIALIZED, MCPEventType.SERVER_SHUTDOWN,
     MCPEventType.TOOL_CALLED, MCPEventType.TOOL_COMPLETED,
     MCPEventType.TOOL_ERROR, MCPEventType.TOOL_LIST_CHANGED,
     MCPEventType.RESOURCE_READ, MCPEventType.RESOURCE_UPDATED,
     MCPEventType.RESOURCE_LIST_CHANGED, MCPEventType.PROMPT_GET,
     MCPEventType.PROMPT_LIST_CHANGED, MCPEventType.SAMPLING_REQUESTED,
     MCPEventType.SAMPLING_COMPLETED, MCPEventType.ROOTS_LIST_CHANGED,
     MCPEventType.ERROR] +
    # A2A
    [A2AEventType.TASK_ASSIGNED, A2AEventType.TASK_ACCEPTED,
     A2AEventType.TASK_REJECTED, A2AEventType.TASK_COMPLETED,
     A2AEventType.TASK_FAILED, A2AEventType.MESSAGE_SENT,
     A2AEventType.MESSAGE_RECEIVED, A2AEventType.AGENT_REGISTERED,
     A2AEventType.AGENT_DEREGISTERED, A2AEventType.DELEGATED,
     A2AEventType.ERROR] +
    # AP2
    [AP2EventType.MANDATE_CREATED, AP2EventType.MANDATE_REVOKED,
     AP2EventType.APPROVAL_REQUESTED, AP2EventType.APPROVAL_GRANTED,
     AP2EventType.PAYMENT_INITIATED, AP2EventType.PAYMENT_COMPLETED,
     AP2EventType.ERROR]
)


# ============================================================================
# SECTION 4: TYPEDDICT DEFINITIONS
# ============================================================================

class AOPEvent(TypedDict, total=False):
    """
    Complete AOP event structure.
    
    Required fields (total=False allows optional, but validation enforces these):
    - id: Unique event identifier (UUID v7)
    - version: Protocol version
    - timestamp: ISO 8601 timestamp
    - agent_id: Agent identifier
    - instance_id: Agent instance identifier
    - protocol: Protocol type (mcp, a2a, ap2)
    - event_type: Event type string
    
    Optional fields:
    - correlation_id: Trace correlation ID
    - parent_id: Parent span ID
    - severity: Event severity level
    - duration_ms: Event duration in milliseconds
    - data: Event-specific data payload
    - metadata: Additional metadata
    - error: Error information
    """
    # Required fields
    id: str
    version: str
    timestamp: str
    agent_id: str
    instance_id: str
    protocol: str
    event_type: str
    
    # Optional fields
    correlation_id: str
    parent_id: str
    severity: str
    duration_ms: int
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Dict[str, Any]


class ErrorInfo(TypedDict, total=False):
    """Error information structure"""
    code: str
    message: str
    details: Dict[str, Any]
    stack_trace: str


# ============================================================================
# SECTION 5: TYPE ALIASES
# ============================================================================

# Type aliases for clarity
EventData = Dict[str, Any]
EventMetadata = Dict[str, Any]
UUID = str
ISOTimestamp = str
CorrelationID = str
SpanID = str

# Literal types for validation
ProtocolType = Literal["mcp", "a2a", "ap2"]
SeverityType = Literal["error", "warn", "info", "debug"]