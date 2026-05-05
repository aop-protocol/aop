"""
AOP Client - Main interface for logging and querying AOP events.

Supports pluggable storage backends (SQLite, PostgreSQL, In-Memory).
"""

from typing import Dict, List, Optional, Any, ContextManager, Union, cast
from datetime import datetime

from .storage import create_storage, BaseStorage
from .validation import validate_event
from .events import build_event
from .types import AOPEvent
from .exceptions import AOPValidationError, AOPStorageError

from .adapters.mcp import MCPAdapter
from .adapters.a2a import A2AAdapter
from .adapters.ap2 import AP2Adapter
from .trace import trace_context


class AOPClient:
    """
    AOP Client for logging and querying observability events.
    
    The client handles:
    - Event validation
    - Multiple storage backends (SQLite, PostgreSQL, In-Memory)
    - Querying events
    - Trace reconstruction
    
    Storage backends:
    - SQLite: 'sqlite:///path/to/file.db' (default, file-based)
    - PostgreSQL: 'postgresql://user:pass@host:5432/dbname' (production)
    - In-Memory: 'memory' (testing only, no persistence)
    
    Examples:
        >>> # SQLite (default)
        >>> client = AOPClient()
        >>> client = AOPClient(storage='sqlite:///aop_events.db')
        
        >>> # PostgreSQL (production)
        >>> client = AOPClient(storage='postgresql://localhost/aop')
        
        >>> # In-Memory (testing)
        >>> client = AOPClient(storage='memory')
        
        >>> # Log events
        >>> client.log_event({
        ...     'agent_id': 'my-agent',
        ...     'event_type': 'mcp.tool.call',
        ...     'data': {'tool_name': 'search'}
        ... })
        
        >>> # Query events
        >>> events = client.query(agent_id='my-agent')
        
        >>> # Context manager
        >>> with AOPClient(storage='memory') as client:
        ...     client.log_event({...})
    """
    
    def __init__(
        self,
        storage: Optional[str] = None,
        *,
        transport: Optional[Any] = None,
        batch: bool = False,
        batch_max_size: int = 256,
        batch_flush_interval_s: float = 1.0,
    ) -> None:
        """Initialize AOP client.

        Args:
            storage: Storage connection string. Defaults to SQLite.
            transport: Optional pluggable transport. If provided, events are
                shipped through the transport instead of (or in addition to)
                the local storage. ``transport='otlp+http://...'`` /
                ``'aop+http://...'`` URL strings are also accepted.
            batch: If True, wrap the transport in a BatchProcessor for async
                batched export.
            batch_max_size / batch_flush_interval_s: BatchProcessor knobs.
        """
        self.storage: BaseStorage = create_storage(storage)

        # Optional remote transport ----------------------------------------
        self._transport: Optional[Any] = None
        if transport is not None:
            self._transport = self._build_transport(transport)
            if batch:
                from .transport.batch import BatchProcessor
                self._transport = BatchProcessor(
                    self._transport,
                    max_batch_size=batch_max_size,
                    flush_interval_s=batch_flush_interval_s,
                )

    @staticmethod
    def _build_transport(transport: Any) -> Any:
        """Resolve a transport from a URL string or pre-constructed object."""
        from .transport import (
            HTTPJSONTransport, OTLPHTTPTransport, OTLPGRPCTransport,
        )
        if isinstance(transport, str):
            if transport.startswith("aop+http://") or transport.startswith("aop+https://"):
                return HTTPJSONTransport(endpoint=transport[4:])
            if transport.startswith("otlp+http://") or transport.startswith("otlp+https://"):
                return OTLPHTTPTransport(endpoint=transport[5:])
            if transport.startswith("otlp+grpc://"):
                return OTLPGRPCTransport(endpoint=transport[12:])
            raise ValueError(f"Unknown transport URL scheme: {transport!r}")
        return transport
    
    def log_event(
        self,
        event: Union[Dict[str, Any], AOPEvent],
        validate: bool = True,
        auto_build: bool = True
    ) -> str:
        """
        Log a single event.
        
        Args:
            event: Event dictionary (can be partial if auto_build=True)
            validate: Whether to validate event (default: True)
            auto_build: Whether to auto-fill missing fields (default: True)
            
        Returns:
            Event ID
            
        Raises:
            AOPValidationError: If validation fails
            AOPStorageError: If storage operation fails
            
        Examples:
            >>> # Minimal event (auto-build fills in fields)
            >>> event_id = client.log_event({
            ...     'agent_id': 'my-agent',
            ...     'event_type': 'mcp.tool.call',
            ...     'data': {'tool_name': 'search'}
            ... })
            
            >>> # Complete event (no auto-build needed)
            >>> event_id = client.log_event({
            ...     'id': '01HQRS...',
            ...     'version': '1.0',
            ...     'timestamp': '2025-10-04T10:30:00Z',
            ...     'agent_id': 'agent-1',
            ...     'instance_id': '01HQRS...',
            ...     'protocol': 'mcp',
            ...     'event_type': 'mcp.tool.call',
            ...     'data': {'tool_name': 'search'}
            ... }, auto_build=False)
        """
        try:
            # Auto-build if needed
            if auto_build:
                # Check if required fields are missing
                required = ['agent_id', 'event_type']
                if not all(k in event for k in required):
                    raise AOPValidationError(
                        "Event must have at least 'agent_id' and 'event_type' fields"
                    )
                
                # Build complete event (forwards v1.1 fields if present)
                event_dict = build_event(
                    agent_id=event['agent_id'],
                    event_type=event['event_type'],
                    data=event.get('data'),
                    instance_id=event.get('instance_id'),
                    correlation_id=event.get('correlation_id'),
                    parent_id=event.get('parent_id'),
                    severity=event.get('severity'),
                    duration_ms=event.get('duration_ms'),
                    metadata=event.get('metadata'),
                    error=event.get('error'),
                    trace_id=event.get('trace_id'),
                    span_id=event.get('span_id'),
                    parent_span_id=event.get('parent_span_id'),
                    resource=event.get('resource'),
                    links=event.get('links'),
                    attributes=event.get('attributes'),
                    tokens=event.get('tokens'),
                    cost=event.get('cost'),
                    validate=validate,
                )

                self.storage.log_event(event_dict)
                self._ship_to_transport(event_dict)
                return str(event_dict['id'])

            else:
                # Event is already a complete dict or TypedDict, which is compatible
                # with Dict[str, Any] at runtime. We cast to satisfy mypy.
                final_event = cast(Dict[str, Any], event)

                # Validate if requested
                if validate:
                    validate_event(final_event)

                # Store event
                self.storage.log_event(final_event)
                self._ship_to_transport(final_event)
                return str(final_event['id'])
            
        except (AOPValidationError, AOPStorageError):
            raise
        except Exception as e:
            raise AOPStorageError(
                f"Failed to log event: {str(e)}",
                operation='log_event',
                context={'event_type': event.get('event_type')}
            )
    
    def log_events(
        self,
        events: List[Union[Dict[str, Any], AOPEvent]],
        validate: bool = True,
        auto_build: bool = True
    ) -> List[str]:
        """
        Log multiple events in batch.
        
        More efficient than calling log_event() multiple times.
        
        Args:
            events: List of event dictionaries
            validate: Whether to validate events (default: True)
            auto_build: Whether to auto-fill missing fields (default: True)
            
        Returns:
            List of event IDs
            
        Raises:
            AOPValidationError: If validation fails
            AOPStorageError: If storage operation fails
            
        Example:
            >>> event_ids = client.log_events([
            ...     {'agent_id': 'agent-1', 'event_type': 'mcp.tool.call', ...},
            ...     {'agent_id': 'agent-1', 'event_type': 'mcp.tool.result', ...}
            ... ])
        """
        event_ids = []
        
        for event in events:
            event_id = self.log_event(event, validate=validate, auto_build=auto_build)
            event_ids.append(event_id)
        
        return event_ids
    
    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        protocol: Optional[str] = None,
        correlation_id: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[Union[str, datetime]] = None,
        end_time: Optional[Union[str, datetime]] = None,
        limit: int = 100,
        order_by: str = 'timestamp',
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query events with filters.
        
        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type
            protocol: Filter by protocol (mcp, a2a, ap2)
            correlation_id: Filter by correlation ID (trace)
            severity: Filter by severity level
            start_time: Events after this timestamp (ISO 8601 or datetime)
            end_time: Events before this timestamp (ISO 8601 or datetime)
            limit: Maximum number of events (default: 100)
            order_by: Field to order by (default: 'timestamp')
            order_desc: Order descending (default: True)
            
        Returns:
            List of events
            
        Examples:
            >>> # Get recent events for an agent
            >>> events = client.query(agent_id='my-agent', limit=10)
            
            >>> # Get all tool calls in a time range
            >>> events = client.query(
            ...     event_type='mcp.tool.call',
            ...     start_time='2025-10-01T00:00:00Z',
            ...     end_time='2025-10-02T00:00:00Z'
            ... )
            
            >>> # Get all events in a trace
            >>> trace = client.query(correlation_id='trace-123')
        """
        # Convert string timestamps to datetime if needed
        start_dt = None
        end_dt = None
        
        if start_time:
            if isinstance(start_time, str):
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_dt = start_time
        
        if end_time:
            if isinstance(end_time, str):
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                end_dt = end_time
        
        # Query storage (base interface only supports subset of filters)
        events = self.storage.query_events(
            agent_id=agent_id,
            event_type=event_type,
            protocol=protocol,
            start_time=start_dt,
            end_time=end_dt,
            correlation_id=correlation_id,
            limit=limit
        )
        
        # Apply additional filters in-memory (severity, custom ordering)
        if severity:
            events = [e for e in events if e.get('severity') == severity]
        
        # Apply custom ordering if different from default
        if order_by != 'timestamp' or not order_desc:
            events.sort(
                key=lambda e: e.get(order_by, ''),
                reverse=order_desc
            )
        
        return events
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single event by its ID.
        
        Args:
            event_id: Unique event identifier (UUID v7)
            
        Returns:
            Event dictionary if found, None otherwise
            
        Example:
            >>> event = client.get_event('01HQRS9XOP2JRBN7K01RGUWZ1W')
            >>> if event:
            ...     print(event['event_type'])
        """
        return self.storage.get_event(event_id)
    
    def get_trace(self, correlation_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a trace by correlation_id.
        
        Returns events ordered chronologically (oldest first).
        
        Args:
            correlation_id: Trace correlation ID
            
        Returns:
            List of events in trace
            
        Example:
            >>> trace = client.get_trace('4bf92f3577b34da6a3ce929d0e0e4736')
            >>> print(f"Trace has {len(trace)} events")
            >>> for event in trace:
            ...     print(f"{event['timestamp']}: {event['event_type']}")
        """
        events = self.storage.query_events(
            correlation_id=correlation_id,
            limit=10000  # Large limit for complete trace
        )
        
        # Sort chronologically (oldest first) for trace reconstruction
        events.sort(key=lambda e: e.get('timestamp', ''))
        
        return events
    
    @property
    def mcp(self) -> MCPAdapter:
        """MCP protocol adapter."""
        if not hasattr(self, '_mcp_adapter'):
            self._mcp_adapter = MCPAdapter(self)
        return self._mcp_adapter

    @property
    def a2a(self) -> A2AAdapter:
        """A2A protocol adapter."""
        if not hasattr(self, '_a2a_adapter'):
            self._a2a_adapter = A2AAdapter(self)
        return self._a2a_adapter

    @property
    def ap2(self) -> AP2Adapter:
        """AP2 protocol adapter."""
        if not hasattr(self, '_ap2_adapter'):
            self._ap2_adapter = AP2Adapter(self)
        return self._ap2_adapter

    # Phase 3 protocol adapters --------------------------------------------
    @property
    def acp(self) -> Any:
        """ACP (IBM Agent Communication Protocol) adapter."""
        if not hasattr(self, '_acp_adapter'):
            from .adapters.acp import ACPAdapter
            self._acp_adapter = ACPAdapter(self)
        return self._acp_adapter

    @property
    def agntcy(self) -> Any:
        """AGNTCY (Internet of Agents) adapter."""
        if not hasattr(self, '_agntcy_adapter'):
            from .adapters.agntcy import AGNTCYAdapter
            self._agntcy_adapter = AGNTCYAdapter(self)
        return self._agntcy_adapter

    @property
    def anp(self) -> Any:
        """ANP (Agent Network Protocol) adapter."""
        if not hasattr(self, '_anp_adapter'):
            from .adapters.anp import ANPAdapter
            self._anp_adapter = ANPAdapter(self)
        return self._anp_adapter

    @property
    def ag_ui(self) -> Any:
        """AG-UI (Agent-User-Interface) adapter."""
        if not hasattr(self, '_ag_ui_adapter'):
            from .adapters.ag_ui import AGUIAdapter
            self._ag_ui_adapter = AGUIAdapter(self)
        return self._ag_ui_adapter

    @property
    def openai_agents(self) -> Any:
        """OpenAI Agents SDK adapter."""
        if not hasattr(self, '_openai_agents_adapter'):
            from .adapters.openai_agents import OpenAIAgentsAdapter
            self._openai_agents_adapter = OpenAIAgentsAdapter(self)
        return self._openai_agents_adapter

    @property
    def feedback(self) -> Any:
        """User feedback / eval signals adapter."""
        if not hasattr(self, '_feedback_adapter'):
            from .adapters.feedback import FeedbackAdapter
            self._feedback_adapter = FeedbackAdapter(self)
        return self._feedback_adapter

    def start_span(
        self,
        name: str,
        *,
        agent_id: str,
        protocol: str = "mcp",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Start an OTel-style Span attached to this client.

        Returns a context-manager that emits ``<protocol>.<name>.started`` and
        ``<protocol>.<name>.completed`` events, automatically populating
        ``trace_id`` / ``span_id`` / ``parent_span_id`` from the active
        SpanContext (or creating a fresh root context).
        """
        from .span import Span
        return Span(
            name=name,
            agent_id=agent_id,
            protocol=protocol,
            attributes=attributes,
            client=self,
        )

    def trace(self, correlation_id: str) -> ContextManager[None]:
        """
        Create trace context for automatic correlation.
        
        Args:
            correlation_id: Correlation ID for this trace
            
        Returns:
            Context manager for trace
            
        Example:
            >>> with client.trace('trace-123'):
            ...     client.mcp.log_tool_call(...)
            ...     client.a2a.log_task(...)
        """
        return trace_context(correlation_id)
    
    def _ship_to_transport(self, event: Dict[str, Any]) -> None:
        """Best-effort ship to the configured remote transport (if any)."""
        if self._transport is None:
            return
        try:
            self._transport.export([event])
        except Exception:
            pass

    def close(self) -> None:
        """
        Close storage connections and cleanup resources.
        
        Should be called when client is no longer needed.
        Safe to call multiple times.
        
        Example:
            >>> client = AOPClient()
            >>> # ... use client ...
            >>> client.close()
        """
        self.storage.close()
        if self._transport is not None:
            try:
                self._transport.shutdown()
            except Exception:
                pass

    def __enter__(self) -> 'AOPClient':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - ensures cleanup."""
        self.close()
    
    # Convenience methods for common event types
    
    def log_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Convenience method to log MCP tool call event.
        
        Args:
            agent_id: Agent identifier
            tool_name: Name of tool being called
            parameters: Tool parameters
            correlation_id: Optional correlation ID for tracing
            parent_id: Optional parent event ID
            
        Returns:
            Event ID
            
        Example:
            >>> event_id = client.log_tool_call(
            ...     agent_id='agent-1',
            ...     tool_name='web_search',
            ...     parameters={'query': 'AOP protocol'}
            ... )
        """
        return self.log_event({
            'agent_id': agent_id,
            'event_type': 'mcp.tool.call',
            'data': {
                'tool_name': tool_name,
                'parameters': parameters
            },
            'correlation_id': correlation_id,
            'parent_id': parent_id
        })
    
    def log_tool_result(
        self,
        agent_id: str,
        tool_name: str,
        result: Any,
        duration_ms: int,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Convenience method to log MCP tool result event.
        
        Args:
            agent_id: Agent identifier
            tool_name: Name of tool that was called
            result: Tool execution result
            duration_ms: Execution duration in milliseconds
            correlation_id: Optional correlation ID for tracing
            parent_id: Optional parent event ID
            
        Returns:
            Event ID
        """
        return self.log_event({
            'agent_id': agent_id,
            'event_type': 'mcp.tool.result',
            'data': {
                'tool_name': tool_name,
                'result': result
            },
            'duration_ms': duration_ms,
            'correlation_id': correlation_id,
            'parent_id': parent_id
        })
    
    def log_task_start(
        self,
        agent_id: str,
        task_id: str,
        task_description: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Convenience method to log A2A task start event.
        
        Args:
            agent_id: Agent identifier
            task_id: Unique task identifier
            task_description: Human-readable task description
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Event ID
        """
        return self.log_event({
            'agent_id': agent_id,
            'event_type': 'a2a.task.start',
            'data': {
                'task_id': task_id,
                'description': task_description
            },
            'correlation_id': correlation_id
        })
    
    def log_task_complete(
        self,
        agent_id: str,
        task_id: str,
        result: Any,
        duration_ms: int,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Convenience method to log A2A task completion event.
        
        Args:
            agent_id: Agent identifier
            task_id: Unique task identifier
            result: Task execution result
            duration_ms: Execution duration in milliseconds
            correlation_id: Optional correlation ID for tracing
            parent_id: Optional parent event ID
            
        Returns:
            Event ID
        """
        return self.log_event({
            'agent_id': agent_id,
            'event_type': 'a2a.task.complete',
            'data': {
                'task_id': task_id,
                'result': result
            },
            'duration_ms': duration_ms,
            'correlation_id': correlation_id,
            'parent_id': parent_id
        })