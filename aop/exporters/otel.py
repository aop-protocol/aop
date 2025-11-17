"""
OpenTelemetry exporter for AOP events.

Converts AOP events to OpenTelemetry spans/traces for integration with
OTEL-compatible observability tools (Jaeger, Zipkin, Tempo, etc.).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Create dummy classes for type hints
    trace = None  # type: ignore
    Status = None  # type: ignore
    StatusCode = None  # type: ignore
    SpanKind = None  # type: ignore

from .base import BaseExporter
from ..client import AOPClient


class OpenTelemetryExporter(BaseExporter):
    """
    Exporter for OpenTelemetry format.
    
    Converts AOP events to OTEL spans, preserving:
    - Parent-child relationships (via parent_id)
    - Trace correlation (via correlation_id)
    - Event timing and duration
    - Error information
    """
    
    def __init__(
        self,
        client: Optional[AOPClient] = None,
        service_name: str = "aop-agent",
        resource_attributes: Optional[Dict[str, str]] = None
    ):
        """
        Initialize OpenTelemetry exporter.
        
        Args:
            client: Optional AOPClient for trace export
            service_name: Service name for OTEL resource
            resource_attributes: Additional resource attributes
            
        Raises:
            ImportError: If OpenTelemetry dependencies are not installed
        """
        if not OTEL_AVAILABLE:
            raise ImportError(
                "OpenTelemetry dependencies not installed. "
                "Install with: pip install aop[otel]"
            )
        
        super().__init__(client)
        
        # Initialize tracer provider
        resource_attrs = {"service.name": service_name}
        if resource_attributes:
            resource_attrs.update(resource_attributes)
        
        resource = Resource.create(resource_attrs)
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        self.tracer = trace.get_tracer(__name__)
        self._spans: List[Any] = []
    
    def _map_event_type_to_span_kind(self, event_type: str) -> Any:
        """
        Map AOP event type to OTEL span kind.
        
        Args:
            event_type: AOP event type string
            
        Returns:
            OTEL SpanKind
        """
        if not OTEL_AVAILABLE:
            return None
        
        # Tool calls are typically CLIENT (calling external service)
        if 'tool' in event_type or 'payment' in event_type:
            return SpanKind.CLIENT
        
        # Tasks and messages are INTERNAL (within system)
        if 'task' in event_type or 'message' in event_type:
            return SpanKind.INTERNAL
        
        # Default to INTERNAL
        return SpanKind.INTERNAL
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """
        Parse ISO 8601 timestamp to Unix timestamp.
        
        Args:
            timestamp_str: ISO 8601 timestamp string
            
        Returns:
            Unix timestamp (seconds since epoch)
        """
        # Handle both with and without 'Z'
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(timestamp_str)
        return dt.timestamp()
    
    def export_events(self, events: List[Dict[str, Any]]) -> List[Any]:
        """
        Convert AOP events to OTEL spans.

        Args:
            events: List of AOP event dictionaries

        Returns:
            List of OTEL span objects
        """
        if not OTEL_AVAILABLE:
            raise ImportError("OpenTelemetry dependencies not installed")

        spans: List[Any] = []
        spans_by_id: Dict[str, Any] = {}
        contexts_by_correlation: Dict[str, Any] = {}

        # Sort events by timestamp to ensure parents are created before children
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', ''))

        # Create spans for all events
        for event in sorted_events:
            event_id = event.get('id')
            event_type = event.get('event_type', '')
            timestamp_str = event.get('timestamp', '')
            duration_ms = event.get('duration_ms')
            correlation_id = event.get('correlation_id')
            parent_id = event.get('parent_id')
            data = event.get('data', {})
            error = event.get('error')

            # Determine span name from event
            if 'tool' in event_type:
                span_name = data.get('tool_name', event_type)
            elif 'task' in event_type:
                span_name = data.get('task_id', event_type)
            elif 'payment' in event_type:
                span_name = data.get('payment_id', event_type)
            else:
                span_name = event_type

            # Parse timestamps
            start_time = self._parse_timestamp(timestamp_str)
            end_time = start_time + (duration_ms / 1000.0) if duration_ms else start_time

            # Create span context
            span_kind = self._map_event_type_to_span_kind(event_type)

            # Determine parent context
            parent_context = None
            if parent_id and parent_id in spans_by_id:
                # Link to parent span
                parent_span = spans_by_id[parent_id]
                parent_context = trace.set_span_in_context(parent_span)
            elif correlation_id and correlation_id in contexts_by_correlation:
                # Use existing trace context for same correlation_id
                parent_context = contexts_by_correlation[correlation_id]

            # Create span with proper parent context
            span = self.tracer.start_span(
                span_name,
                context=parent_context,
                kind=span_kind,
                start_time=int(start_time * 1_000_000_000)  # nanoseconds
            )

            # Store context for same correlation_id spans
            if correlation_id and correlation_id not in contexts_by_correlation:
                contexts_by_correlation[correlation_id] = trace.set_span_in_context(span)

            # Set attributes
            if correlation_id:
                span.set_attribute("aop.correlation_id", correlation_id)
            span.set_attribute("aop.event_id", event_id)
            span.set_attribute("aop.event_type", event_type)
            span.set_attribute("aop.agent_id", event.get('agent_id', ''))
            span.set_attribute("aop.protocol", event.get('protocol', ''))
            if parent_id:
                span.set_attribute("aop.parent_id", parent_id)

            # Add data fields as attributes
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(f"aop.data.{key}", value)

            # Handle errors
            if error:
                span.set_status(Status(StatusCode.ERROR, error.get('message', '')))
                span.set_attribute("aop.error.code", error.get('code', ''))
                span.record_exception(Exception(error.get('message', '')))
            elif duration_ms:
                span.set_status(Status(StatusCode.OK))

            # Set end time
            if duration_ms:
                span.end(end_time=int(end_time * 1_000_000_000))
            else:
                span.end()

            spans.append(span)
            spans_by_id[event_id] = span

        return spans
    
    def export(self, events: List[Dict[str, Any]]) -> List[Any]:
        """
        Export events to OTEL spans (alias for export_events).
        
        Args:
            events: List of AOP event dictionaries
            
        Returns:
            List of OTEL span objects
        """
        return self.export_events(events)
    
    def export_to_collector(
        self,
        spans: Optional[List[Any]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        endpoint: str = "http://localhost:4317"
    ) -> None:
        """
        Export spans to OTEL collector.
        
        Args:
            spans: Optional list of spans (if None, will convert events)
            events: Optional list of events (if spans not provided)
            endpoint: OTEL collector endpoint
        """
        if not OTEL_AVAILABLE:
            raise ImportError("OpenTelemetry dependencies not installed")
        
        if spans is None:
            if events is None:
                raise ValueError("Must provide either spans or events")
            spans = self.export_events(events)
        
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
        
        # Get tracer provider and add processor
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(processor)
            
            # Force export
            processor.force_flush()
    
    def export_to_file(
        self,
        spans: Optional[List[Any]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        filepath: str = "aop_trace.json"
    ) -> None:
        """
        Export spans to JSON file (OTEL JSON format).
        
        Args:
            spans: Optional list of spans (if None, will convert events)
            events: Optional list of events (if spans not provided)
            filepath: Output file path
        """
        if not OTEL_AVAILABLE:
            raise ImportError("OpenTelemetry dependencies not installed")
        
        if spans is None:
            if events is None:
                raise ValueError("Must provide either spans or events")
            spans = self.export_events(events)
        
        # Convert spans to JSON-serializable format
        # This is a simplified version - in production you'd use proper OTEL JSON exporter
        import json
        from pathlib import Path
        
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # For now, export as simple JSON (spans are complex objects)
        # In production, use opentelemetry-exporter-json
        span_data = []
        for span in spans:
            # Extract basic info (simplified)
            span_data.append({
                "name": getattr(span, 'name', 'unknown'),
                "kind": str(getattr(span, 'kind', '')),
            })
        
        with open(output_path, 'w') as f:
            json.dump(span_data, f, indent=2, default=str)

