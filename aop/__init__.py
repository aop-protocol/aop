"""
AOP (Agentic Observability Protocol) — universal observability for AI agents
across MCP, A2A, AP2, ACP, AGNTCY, ANP, AG-UI, OpenAI Agents, LLM, HTTP and
custom protocols.

Quick start:
    >>> from aop import AOPClient
    >>> client = AOPClient('aop_events.db')
    >>> client.log_event({
    ...     'agent_id': 'my-agent',
    ...     'event_type': 'mcp.tool.called',
    ...     'data': {'tool_name': 'search'},
    ... })

Auto-instrument popular libraries (Phase 2):
    >>> import aop
    >>> aop.autoinstrument()        # patches everything detected
    >>> aop.autoinstrument(targets=['openai', 'requests'])
"""

__version__ = "1.1.0"
__author__ = "AOP Contributors"
__license__ = "MIT"

# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------
from .client import AOPClient

# ---------------------------------------------------------------------------
# Event builders
# ---------------------------------------------------------------------------
from .events import (
    build_event,
    build_mcp_event,
    build_a2a_event,
    build_ap2_event,
    build_tool_call_event,
    build_tool_result_event,
    build_task_event,
    build_payment_event,
    build_error_event,
)

# ---------------------------------------------------------------------------
# Types & enums
# ---------------------------------------------------------------------------
from .types import (
    Protocol,
    Severity,
    SpanKind,
    MCPEventType,
    A2AEventType,
    AP2EventType,
    VERSION,
    SUPPORTED_PROTOCOLS,
    ALL_EVENT_TYPES,
    refresh_all_event_types,
)

# ---------------------------------------------------------------------------
# Protocol registry (v1.1)
# ---------------------------------------------------------------------------
from .registry import (
    ProtocolSpec,
    register_protocol,
    unregister_protocol,
    get_protocol,
    supported_protocols,
    is_protocol_registered,
    all_event_types,
    all_specs,
)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
from .exceptions import (
    AOPException,
    AOPValidationError,
    AOPStorageError,
    AOPEventError,
    AOPProtocolError,
    AOPConfigError,
)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
from .validation import validate_event

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
from .utils import (
    generate_uuid_v7,
    get_timestamp,
    validate_uuid,
    validate_timestamp,
    validate_protocol,
    validate_event_type_format,
    validate_severity,
    generate_trace_id,
    generate_span_id,
    validate_trace_id,
    validate_span_id,
)

# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------
from .adapters.mcp import MCPAdapter
from .adapters.a2a import A2AAdapter
from .adapters.ap2 import AP2Adapter
from .adapters.acp import ACPAdapter
from .adapters.agntcy import AGNTCYAdapter
from .adapters.anp import ANPAdapter
from .adapters.ag_ui import AGUIAdapter
from .adapters.openai_agents import OpenAIAgentsAdapter
from .adapters.feedback import FeedbackAdapter
from .adapters.generic import GenericAdapter
from .trace import trace_context
from .span import Span, start_span, current_span

# ---------------------------------------------------------------------------
# W3C propagation
# ---------------------------------------------------------------------------
from .propagation import (
    SpanContext,
    inject as inject_trace_context,
    extract as extract_trace_context,
)

# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
from .analytics import Analytics

# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------
from .exporters import (
    BaseExporter,
    JSONExporter,
    CSVExporter,
    register_exporter,
    get_exporter,
    list_exporters,
)

try:
    from .exporters import OpenTelemetryExporter, PrometheusExporterServer  # type: ignore
except ImportError:
    OpenTelemetryExporter = None  # type: ignore
    PrometheusExporterServer = None  # type: ignore

# ---------------------------------------------------------------------------
# Auto-instrumentation (Phase 2)
# ---------------------------------------------------------------------------
from .instrumentation import autoinstrument, uninstrument, list_instrumentations

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
__all__ = [
    "__version__",

    # client
    "AOPClient",

    # event builders
    "build_event", "build_mcp_event", "build_a2a_event", "build_ap2_event",
    "build_tool_call_event", "build_tool_result_event", "build_task_event",
    "build_payment_event", "build_error_event",

    # types
    "Protocol", "Severity", "SpanKind",
    "MCPEventType", "A2AEventType", "AP2EventType",
    "VERSION", "SUPPORTED_PROTOCOLS", "ALL_EVENT_TYPES",
    "refresh_all_event_types",

    # registry
    "ProtocolSpec", "register_protocol", "unregister_protocol",
    "get_protocol", "supported_protocols", "is_protocol_registered",
    "all_event_types", "all_specs",

    # exceptions
    "AOPException", "AOPValidationError", "AOPStorageError",
    "AOPEventError", "AOPProtocolError", "AOPConfigError",

    # validation
    "validate_event",

    # utils
    "generate_uuid_v7", "get_timestamp",
    "validate_uuid", "validate_timestamp", "validate_protocol",
    "validate_event_type_format", "validate_severity",
    "generate_trace_id", "generate_span_id",
    "validate_trace_id", "validate_span_id",

    # adapters / spans
    "MCPAdapter", "A2AAdapter", "AP2Adapter",
    "ACPAdapter", "AGNTCYAdapter", "ANPAdapter",
    "AGUIAdapter", "OpenAIAgentsAdapter", "FeedbackAdapter", "GenericAdapter",
    "trace_context", "Span", "start_span", "current_span",

    # propagation
    "SpanContext", "inject_trace_context", "extract_trace_context",

    # analytics
    "Analytics",

    # exporters
    "BaseExporter", "JSONExporter", "CSVExporter",
    "OpenTelemetryExporter", "PrometheusExporterServer",
    "register_exporter", "get_exporter", "list_exporters",

    # auto-instrumentation
    "autoinstrument", "uninstrument", "list_instrumentations",
]
