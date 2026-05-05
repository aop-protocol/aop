"""
AOP Type Definitions
Contains type hints, enums, and constants for the AOP protocol.

NOTE (v1.1): The hard-coded ``Protocol`` enum and ``ALL_EVENT_TYPES`` list are
kept for backward compatibility. New code should use ``aop.registry`` to
discover supported protocols/event types because additional protocols (ACP,
AGNTCY, ANP, AG-UI, OpenAI Agents, etc.) are registered dynamically.
"""

from typing import TypedDict, Dict, Any, Literal, List
from enum import Enum

# ============================================================================
# SECTION 1: CONSTANTS
# ============================================================================

VERSION = "1.1"

# Back-compat: the legacy frozen list of "first three" protocols. Real lookups
# should call ``aop.registry.supported_protocols()`` instead.
SUPPORTED_PROTOCOLS = ["mcp", "a2a", "ap2"]

# ============================================================================
# SECTION 2: ENUMS
# ============================================================================


class Protocol(str, Enum):
    """Legacy enum of the original three protocols.

    Kept for backward compatibility. Use ``aop.register_protocol`` /
    ``aop.supported_protocols`` for the open registry.
    """

    MCP = "mcp"
    A2A = "a2a"
    AP2 = "ap2"


class Severity(str, Enum):
    """Event severity levels"""

    ERROR = "error"
    WARN = "warn"
    INFO = "info"
    DEBUG = "debug"


class SpanKind(str, Enum):
    """OpenTelemetry-compatible span kinds (v1.1).

    Used by the new ``Span`` API in ``aop.span``.
    """

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


# ============================================================================
# SECTION 3: EVENT TYPE CONSTANTS (legacy convenience)
# ============================================================================


class MCPEventType:
    """Model Context Protocol event types"""
    SERVER_INITIALIZED = "mcp.server.initialized"
    SERVER_SHUTDOWN = "mcp.server.shutdown"
    TOOL_CALLED = "mcp.tool.called"
    TOOL_COMPLETED = "mcp.tool.completed"
    TOOL_ERROR = "mcp.tool.error"
    TOOL_LIST_CHANGED = "mcp.tool.list_changed"
    RESOURCE_READ = "mcp.resource.read"
    RESOURCE_UPDATED = "mcp.resource.updated"
    RESOURCE_LIST_CHANGED = "mcp.resource.list_changed"
    PROMPT_GET = "mcp.prompt.get"
    PROMPT_LIST_CHANGED = "mcp.prompt.list_changed"
    SAMPLING_REQUESTED = "mcp.sampling.requested"
    SAMPLING_COMPLETED = "mcp.sampling.completed"
    ROOTS_LIST_CHANGED = "mcp.roots.list_changed"
    ERROR = "mcp.error.found"
    # extended
    NOTIFICATION_SENT = "mcp.notification.sent"
    SUBSCRIPTION_CREATED = "mcp.subscription.created"
    SUBSCRIPTION_CANCELLED = "mcp.subscription.cancelled"
    ELICITATION_REQUESTED = "mcp.elicitation.requested"
    ELICITATION_RESPONDED = "mcp.elicitation.responded"
    COMPLETION_REQUESTED = "mcp.completion.requested"
    COMPLETION_COMPLETED = "mcp.completion.completed"


class A2AEventType:
    """Agent-to-Agent protocol event types"""
    TASK_ASSIGNED = "a2a.task.assigned"
    TASK_ACCEPTED = "a2a.task.accepted"
    TASK_REJECTED = "a2a.task.rejected"
    TASK_COMPLETED = "a2a.task.completed"
    TASK_FAILED = "a2a.task.failed"
    MESSAGE_SENT = "a2a.message.sent"
    MESSAGE_RECEIVED = "a2a.message.received"
    AGENT_REGISTERED = "a2a.agent.registered"
    AGENT_DEREGISTERED = "a2a.agent.deregistered"
    DELEGATED = "a2a.task.delegated"
    ERROR = "a2a.error.occurred"
    # extended
    ARTIFACT_UPLOADED = "a2a.artifact.uploaded"
    ARTIFACT_DOWNLOADED = "a2a.artifact.downloaded"
    AGENTCARD_DISCOVERED = "a2a.agentcard.discovered"
    PUSH_SUBSCRIBED = "a2a.push.subscribed"
    PUSH_DELIVERED = "a2a.push.delivered"


class AP2EventType:
    """Agent Payments Protocol event types"""
    MANDATE_CREATED = "ap2.mandate.created"
    MANDATE_REVOKED = "ap2.mandate.revoked"
    APPROVAL_REQUESTED = "ap2.approval.requested"
    APPROVAL_GRANTED = "ap2.approval.granted"
    PAYMENT_INITIATED = "ap2.payment.initiated"
    PAYMENT_COMPLETED = "ap2.payment.completed"
    PAYMENT_FAILED = "ap2.payment.failed"
    ERROR = "ap2.error.occurred"
    # extended
    COST_INCURRED = "ap2.cost.incurred"
    REFUND_INITIATED = "ap2.refund.initiated"
    REFUND_COMPLETED = "ap2.refund.completed"
    DISPUTE_OPENED = "ap2.dispute.opened"
    DISPUTE_RESOLVED = "ap2.dispute.resolved"
    INTENT_RESOLVED = "ap2.intent.resolved"


# ``ALL_EVENT_TYPES`` is now a *list view* over the registry. Code that
# imports it gets a fresh snapshot on each access through ``__all_event_types``
# but for stability we expose a tuple computed at import time AND an updater.

def _build_legacy_event_type_list() -> List[str]:
    # Avoid circular import — registry imports this module's enums for some
    # docs, but does not import ALL_EVENT_TYPES.
    from .registry import all_event_types
    return sorted(all_event_types())


ALL_EVENT_TYPES: List[str] = _build_legacy_event_type_list()


def refresh_all_event_types() -> List[str]:
    """Re-read the registry. Useful after dynamic registrations."""
    global ALL_EVENT_TYPES
    ALL_EVENT_TYPES = _build_legacy_event_type_list()
    return ALL_EVENT_TYPES


# ============================================================================
# SECTION 4: TYPEDDICT DEFINITIONS
# ============================================================================


class AOPEvent(TypedDict, total=False):
    """Complete AOP event structure (v1.1).

    v1.1 additions (all optional, fully back-compatible with v1.0 readers):
        - trace_id          W3C 16-byte hex trace identifier
        - span_id           W3C 8-byte hex span identifier
        - parent_span_id    W3C 8-byte hex parent span identifier
        - resource          OTel-style Resource (service.name, host, env, ...)
        - links             List of {trace_id, span_id, attributes} cross links
        - attributes        Flat string->scalar OTel-style attributes
        - tokens            {"prompt": int, "completion": int, "total": int}
        - cost              {"amount": float, "currency": str, "model": str}
    """

    # Required fields ------------------------------------------------------
    id: str
    version: str
    timestamp: str
    agent_id: str
    instance_id: str
    protocol: str
    event_type: str

    # Original optional fields ---------------------------------------------
    correlation_id: str
    parent_id: str
    severity: str
    duration_ms: int
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Dict[str, Any]

    # v1.1 optional fields -------------------------------------------------
    trace_id: str
    span_id: str
    parent_span_id: str
    resource: Dict[str, Any]
    links: List[Dict[str, Any]]
    attributes: Dict[str, Any]
    tokens: Dict[str, int]
    cost: Dict[str, Any]


class ErrorInfo(TypedDict, total=False):
    """Error information structure"""

    code: str
    message: str
    details: Dict[str, Any]
    stack_trace: str


class ResourceInfo(TypedDict, total=False):
    """OTel-style resource description (v1.1)."""

    service_name: str
    service_version: str
    deployment_environment: str
    host_name: str
    process_pid: int
    sdk_name: str
    sdk_version: str
    sdk_language: str


class TokenUsage(TypedDict, total=False):
    """LLM token usage payload (v1.1)."""

    prompt: int
    completion: int
    total: int
    cached: int
    reasoning: int


class CostInfo(TypedDict, total=False):
    """Monetary cost payload (v1.1)."""

    amount: float
    currency: str
    model: str
    provider: str
    cost_per_input_token: float
    cost_per_output_token: float


# ============================================================================
# SECTION 5: TYPE ALIASES
# ============================================================================

EventData = Dict[str, Any]
EventMetadata = Dict[str, Any]
UUID = str
ISOTimestamp = str
CorrelationID = str
SpanID = str
TraceID = str

ProtocolType = str  # registry-validated; no longer a Literal
SeverityType = Literal["error", "warn", "info", "debug"]
