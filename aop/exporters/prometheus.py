"""
Prometheus exporter for AOP events.

Exposes AOP events as Prometheus metrics via HTTP endpoint for scraping.
"""

import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = None  # type: ignore
    Histogram = None  # type: ignore
    Gauge = None  # type: ignore
    generate_latest = None  # type: ignore
    REGISTRY = None  # type: ignore

from .base import BaseExporter
from ..client import AOPClient


class PrometheusMetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Prometheus metrics endpoint."""

    # Class variable to hold registry (set by server)
    registry = None

    def do_GET(self):
        """Handle GET requests to /metrics endpoint."""
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()

            if PROMETHEUS_AVAILABLE and self.registry:
                self.wfile.write(generate_latest(self.registry))
            else:
                self.wfile.write(b"# Prometheus client not available\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass


class PrometheusExporterServer:
    """
    Standalone HTTP server exposing Prometheus metrics from AOP events.

    Server polls AOP storage periodically and updates metrics.
    Exposes /metrics endpoint for Prometheus scraping.
    """

    def __init__(
        self,
        storage: str = "sqlite:///aop_events.db",
        port: int = 9090,
        poll_interval: float = 30.0
    ):
        """
        Initialize Prometheus exporter server.

        Args:
            storage: AOP storage connection string
            port: Port to run HTTP server on (default: 9090)
            poll_interval: How often to poll storage for updates (seconds, default: 30)

        Raises:
            ImportError: If prometheus-client is not installed
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError(
                "Prometheus dependencies not installed. "
                "Install with: pip install aop[prometheus]"
            )

        self.storage = storage
        self.port = port
        self.poll_interval = poll_interval
        self.client: Optional[AOPClient] = None
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.poll_thread: Optional[threading.Thread] = None
        self.running = False
        self.processed_event_ids: set = set()  # Track which events we've already counted

        # Use custom registry to avoid conflicts between multiple instances
        from prometheus_client import CollectorRegistry
        self.registry = CollectorRegistry()

        # Initialize metrics
        self._init_metrics()
    
    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Event counter by type, agent, protocol
        self.events_total = Counter(
            'aop_events_total',
            'Total number of AOP events',
            ['event_type', 'agent_id', 'protocol'],
            registry=self.registry
        )

        # Tool duration histogram
        self.tool_duration = Histogram(
            'aop_tool_duration_seconds',
            'Tool execution duration in seconds',
            ['tool_name', 'agent_id'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )

        # Tool errors counter
        self.tool_errors = Counter(
            'aop_tool_errors_total',
            'Total number of tool errors',
            ['tool_name', 'agent_id', 'error_code'],
            registry=self.registry
        )

        # Event rate gauge (events per minute)
        self.event_rate = Gauge(
            'aop_event_rate',
            'Event rate (events per minute)',
            ['agent_id'],
            registry=self.registry
        )
    
    def _update_metrics(self) -> None:
        """Update metrics from AOP storage (incremental updates only)."""
        if not self.client:
            return

        try:
            # Query recent events (last hour)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)

            events = self.client.query(
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )

            if not events:
                return

            # Process only NEW events (not yet in processed_event_ids)
            new_event_count = 0
            agent_event_counts: Dict[str, int] = {}

            for event in events:
                event_id = event.get('id')

                # Skip if already processed
                if event_id in self.processed_event_ids:
                    continue

                # Mark as processed
                self.processed_event_ids.add(event_id)
                new_event_count += 1

                event_type = event.get('event_type', '')
                agent_id = event.get('agent_id', 'unknown')
                protocol = event.get('protocol', 'unknown')

                # Track agent events for rate calculation
                agent_event_counts[agent_id] = agent_event_counts.get(agent_id, 0) + 1

                # Increment event counter (only once per event)
                self.events_total.labels(
                    event_type=event_type,
                    agent_id=agent_id,
                    protocol=protocol
                ).inc()

                # Track durations
                duration_ms = event.get('duration_ms')
                if duration_ms:
                    data = event.get('data', {})
                    tool_name = data.get('tool_name', 'unknown')
                    self.tool_duration.labels(
                        tool_name=tool_name,
                        agent_id=agent_id
                    ).observe(duration_ms / 1000.0)  # Convert to seconds

                # Track errors
                error = event.get('error')
                if error:
                    data = event.get('data', {})
                    tool_name = data.get('tool_name', 'unknown')
                    error_code = error.get('code', 'unknown')
                    self.tool_errors.labels(
                        tool_name=tool_name,
                        agent_id=agent_id,
                        error_code=error_code
                    ).inc()

            # Calculate event rate based on new events in this poll
            if new_event_count > 0:
                # Rate = events per poll interval
                rate_per_second = new_event_count / self.poll_interval
                rate_per_minute = rate_per_second * 60.0

                # Update rate for each agent
                for agent_id, count in agent_event_counts.items():
                    self.event_rate.labels(agent_id=agent_id).set(rate_per_minute)

            # Cleanup old event IDs to prevent memory leak (keep last 10000)
            if len(self.processed_event_ids) > 10000:
                # Keep only the most recent 5000
                self.processed_event_ids = set(list(self.processed_event_ids)[-5000:])

        except Exception as e:
            # Log error but don't crash
            print(f"Error updating Prometheus metrics: {e}")
    
    def _poll_loop(self) -> None:
        """Background thread that polls storage and updates metrics."""
        while self.running:
            self._update_metrics()
            time.sleep(self.poll_interval)
    
    def start(self) -> None:
        """Start the Prometheus exporter server."""
        if self.running:
            return

        # Initialize client
        from ..client import AOPClient
        self.client = AOPClient(storage=self.storage)

        # Set the registry for the handler
        PrometheusMetricsHandler.registry = self.registry

        # Create HTTP server
        self.server = HTTPServer(('0.0.0.0', self.port), PrometheusMetricsHandler)

        # Start server in background thread
        self.running = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        # Start polling thread
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()

        print(f"Prometheus exporter server started on port {self.port}")
        print(f"Metrics available at http://localhost:{self.port}/metrics")
    
    def stop(self) -> None:
        """Stop the Prometheus exporter server."""
        if not self.running:
            return
        
        self.running = False
        
        if self.server:
            self.server.shutdown()
        
        if self.client:
            self.client.close()
        
        print("Prometheus exporter server stopped")


class PrometheusExporter(BaseExporter):
    """
    Prometheus exporter (programmatic interface).
    
    For standalone server, use PrometheusExporterServer instead.
    """
    
    def __init__(self, client: Optional[AOPClient] = None):
        """
        Initialize Prometheus exporter.
        
        Args:
            client: AOPClient instance (required for export)
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError(
                "Prometheus dependencies not installed. "
                "Install with: pip install aop[prometheus]"
            )
        
        super().__init__(client)
        if not client:
            raise ValueError("AOPClient required for PrometheusExporter")
    
    def export(self, events: List[Dict[str, Any]]) -> str:
        """
        Export events as Prometheus metrics text format.
        
        Args:
            events: List of AOP event dictionaries
            
        Returns:
            Prometheus metrics text format string
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("Prometheus dependencies not installed")
        
        # This is a simplified exporter - for full metrics use PrometheusExporterServer
        # This method returns metrics in text format for the provided events
        
        lines = []
        lines.append("# AOP Events Export")
        lines.append(f"# Total events: {len(events)}")
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        for event_type, count in type_counts.items():
            lines.append(f'aop_events_total{{event_type="{event_type}"}} {count}')
        
        return '\n'.join(lines)

