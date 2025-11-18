"""
FastAPI server for AOP Dashboard.

Provides REST API endpoints that wrap AOPClient and Analytics functionality.
"""

import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    import uvicorn
except ImportError:
    print("Error: Dashboard dependencies not installed.")
    print("Install with: pip install aop[dashboard]")
    sys.exit(1)

from aop import AOPClient, Analytics
from aop.exporters import JSONExporter, CSVExporter, ToonExporter, OpenTelemetryExporter, PrometheusExporter
from .websocket import EventStreamer


# Global state
client: Optional[AOPClient] = None
analytics: Optional[Analytics] = None
streamer: Optional[EventStreamer] = None
storage_url: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup, cleanup on shutdown."""
    global client, analytics, streamer

    # Startup
    client = AOPClient(storage=storage_url)
    analytics = Analytics(client)
    streamer = EventStreamer(client)

    yield

    # Shutdown
    if client:
        client.close()


# Create FastAPI app
app = FastAPI(
    title="AOP Dashboard",
    description="Web-based UI for AOP event exploration and analysis",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware (allow frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REST API ENDPOINTS
# =============================================================================

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "storage": storage_url}


@app.get("/api/agents")
def get_agents() -> List[str]:
    """
    Get list of all agent IDs in database.

    Returns:
        List of unique agent_id values
    """
    if not client:
        raise HTTPException(status_code=500, detail="Client not initialized")

    try:
        # Query all events and extract unique agent IDs
        events = client.query(limit=10000)  # Get recent events
        agent_ids = sorted(set(e.get('agent_id') for e in events if e.get('agent_id')))
        return agent_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
def get_events(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of events"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> List[Dict[str, Any]]:
    """
    Query events with filters.

    Returns:
        List of events matching criteria
    """
    if not client:
        raise HTTPException(status_code=500, detail="Client not initialized")

    try:
        events = client.query(
            agent_id=agent_id,
            event_type=event_type,
            correlation_id=correlation_id,
            protocol=protocol,
            limit=limit + offset  # Get extra for offset
        )

        # Apply offset manually (storage layer doesn't support it yet)
        if offset > 0:
            events = events[offset:]

        return events[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/{event_id}")
def get_event(event_id: str) -> Dict[str, Any]:
    """
    Get single event by ID.

    Args:
        event_id: Event ID

    Returns:
        Event object
    """
    if not client:
        raise HTTPException(status_code=500, detail="Client not initialized")

    try:
        # Query with ID filter (assuming storage supports it)
        events = client.query(limit=10000)
        event = next((e for e in events if e.get('id') == event_id), None)

        if not event:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/traces/{correlation_id}")
def get_trace(correlation_id: str) -> Dict[str, Any]:
    """
    Reconstruct trace by correlation ID.

    Args:
        correlation_id: Correlation ID to reconstruct

    Returns:
        Trace structure with root event, children, and summary stats
    """
    if not analytics:
        raise HTTPException(status_code=500, detail="Analytics not initialized")

    try:
        trace = analytics.reconstruct_trace(correlation_id)

        if not trace or not trace.get('root_event'):
            raise HTTPException(
                status_code=404,
                detail=f"No trace found for correlation_id: {correlation_id}"
            )

        return trace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/traces/by-event/{event_id}")
def get_trace_by_event(event_id: str) -> Dict[str, Any]:
    """
    Reconstruct trace from any event ID.
    
    Walks up parent chain to root, then returns full trace.
    
    Args:
        event_id: Any event ID in the trace
        
    Returns:
        Trace structure
    """
    if not analytics:
        raise HTTPException(status_code=500, detail="Analytics not initialized")
    
    try:
        trace = analytics.reconstruct_trace_from_event(event_id)
        
        if not trace or not trace.get('root_event'):
            raise HTTPException(
                status_code=404,
                detail=f"No trace found for event_id: {event_id}"
            )
        
        return trace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/traces/by-parent/{parent_id}")
def get_trace_by_parent(parent_id: str) -> Dict[str, Any]:
    """
    Reconstruct trace from parent event ID.
    
    Same as by-event - finds trace containing this parent.
    
    Args:
        parent_id: Parent event ID
        
    Returns:
        Trace structure
    """
    if not analytics:
        raise HTTPException(status_code=500, detail="Analytics not initialized")
    
    try:
        trace = analytics.reconstruct_trace_from_event(parent_id)
        
        if not trace or not trace.get('root_event'):
            raise HTTPException(
                status_code=404,
                detail=f"No trace found for parent_id: {parent_id}"
            )
        
        return trace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats(
    agent_id: str = Query(..., description="Agent ID for statistics"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)")
) -> Dict[str, Any]:
    """
    Get comprehensive statistics for an agent.

    Args:
        agent_id: Agent ID
        start_time: Optional start time filter
        end_time: Optional end time filter

    Returns:
        Statistics including tool counts, event counts, durations, percentiles
    """
    if not analytics:
        raise HTTPException(status_code=500, detail="Analytics not initialized")

    try:
        # Parse time filters (not implemented in analytics yet, but structure ready)
        # start = datetime.fromisoformat(start_time) if start_time else None
        # end = datetime.fromisoformat(end_time) if end_time else None

        # Get all statistics
        tool_counts = analytics.count_by_tool(agent_id)
        event_counts = analytics.count_by_event_type(agent_id)
        avg_durations = analytics.avg_duration_by_tool(agent_id)

        # Get percentiles
        p50 = analytics.percentile_duration(agent_id, percentile=50)
        p95 = analytics.percentile_duration(agent_id, percentile=95)
        p99 = analytics.percentile_duration(agent_id, percentile=99)

        return {
            'agent_id': agent_id,
            'tool_counts': tool_counts,
            'event_counts': event_counts,
            'avg_durations': avg_durations,
            'percentiles': {
                'p50': p50,
                'p95': p95,
                'p99': p99
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/timeline")
def get_timeline(
    agent_id: str = Query(..., description="Agent ID"),
    bucket_size: str = Query('1h', description="Time bucket size (1h, 1d, etc.)")
) -> List[Dict[str, Any]]:
    """
    Get events over time grouped by time buckets.

    Args:
        agent_id: Agent ID
        bucket_size: Time bucket size ('1h', '1d', etc.)

    Returns:
        List of time buckets with event counts
    """
    if not analytics:
        raise HTTPException(status_code=500, detail="Analytics not initialized")

    try:
        timeline = analytics.events_over_time(agent_id, bucket_size=bucket_size)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rate")
def get_event_rate(
    agent_id: str = Query(..., description="Agent ID"),
    window_minutes: int = Query(60, ge=1, le=1440, description="Time window in minutes")
) -> Dict[str, Any]:
    """
    Calculate event rate for an agent.

    Args:
        agent_id: Agent ID
        window_minutes: Time window in minutes

    Returns:
        Event rate (events per minute)
    """
    if not analytics:
        raise HTTPException(status_code=500, detail="Analytics not initialized")

    try:
        rate = analytics.event_rate(agent_id, window_minutes=window_minutes)
        return {
            'agent_id': agent_id,
            'window_minutes': window_minutes,
            'rate': rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@app.get("/api/export/json")
def export_json(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum events to export")
):
    """
    Export events as JSON file.

    Browser will prompt for download location.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Client not initialized")

    try:
        # Query events with filters
        events = client.query(
            agent_id=agent_id,
            event_type=event_type,
            correlation_id=correlation_id,
            protocol=protocol,
            limit=limit
        )

        # Export to JSON
        exporter = JSONExporter(pretty=True)
        json_output = exporter.export(events)

        # Return as downloadable file
        from fastapi.responses import Response
        filename = f"aop_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return Response(
            content=json_output,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/csv")
def export_csv(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum events to export")
):
    """
    Export events as CSV file.

    Browser will prompt for download location.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Client not initialized")

    try:
        # Query events with filters
        events = client.query(
            agent_id=agent_id,
            event_type=event_type,
            correlation_id=correlation_id,
            protocol=protocol,
            limit=limit
        )

        # Export to CSV
        exporter = CSVExporter()
        csv_output = exporter.export(events)

        # Return as downloadable file
        from fastapi.responses import Response
        filename = f"aop_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/toon")
def export_toon(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum events to export"),
    flatten: bool = Query(True, description="Flatten nested fields (recommended)"),
    delimiter: str = Query('comma', description="Delimiter type (comma/tab/pipe)")
):
    """
    Export events as TOON file (Token-Oriented Object Notation).

    TOON achieves 30-60% token reduction vs JSON - perfect for LLM-assisted debugging.
    Browser will prompt for download location.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Client not initialized")

    try:
        # Query events with filters
        events = client.query(
            agent_id=agent_id,
            event_type=event_type,
            correlation_id=correlation_id,
            protocol=protocol,
            limit=limit
        )

        # Export to TOON
        exporter = ToonExporter(flatten=flatten, delimiter=delimiter)
        toon_output = exporter.export(events)

        # Calculate token savings for metadata
        stats = exporter.get_token_estimate(events)

        # Return as downloadable file
        from fastapi.responses import Response
        filename = f"aop_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.toon"
        return Response(
            content=toon_output,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Token-Savings": str(stats['savings_percent'])
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/otel")
def export_otel(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum events to export")
):
    """
    Export events as OpenTelemetry JSON format.

    Converts AOP events to OTLP spans for import into OpenTelemetry collectors.
    Browser will prompt for download location.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Client not initialized")

    try:
        # Query events with filters
        events = client.query(
            agent_id=agent_id,
            correlation_id=correlation_id,
            limit=limit
        )

        if not events:
            raise HTTPException(status_code=404, detail="No events found")

        # Check if OpenTelemetry exporter is available
        if OpenTelemetryExporter is None:
            raise HTTPException(
                status_code=501,
                detail="OpenTelemetry exporter not available. Install with: pip install aop[otel]"
            )

        # Export to OpenTelemetry format
        exporter = OpenTelemetryExporter()
        spans = exporter.export_events(events)

        # Convert spans to JSON
        import json

        # Wrap in OTLP ResourceSpans format
        otlp_output = {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "aop-export"}},
                        {"key": "aop.agent_id", "value": {"stringValue": events[0].get('agent_id', 'unknown')}}
                    ]
                },
                "scopeSpans": [{
                    "scope": {
                        "name": "aop",
                        "version": "0.1.0"
                    },
                    "spans": [exporter._span_to_dict(span) for span in spans]
                }]
            }]
        }

        json_output = json.dumps(otlp_output, indent=2, default=str)

        # Return as downloadable file
        from fastapi.responses import Response
        filename = f"aop_otel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return Response(
            content=json_output,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/prometheus")
def export_prometheus(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID")
):
    """
    Export current metrics snapshot in Prometheus format.

    Returns metrics in Prometheus text exposition format.
    Browser will prompt for download location.
    """
    if not client or not analytics:
        raise HTTPException(status_code=500, detail="Client/Analytics not initialized")

    try:
        # Check if Prometheus exporter is available
        if PrometheusExporter is None:
            raise HTTPException(
                status_code=501,
                detail="Prometheus exporter not available. Install with: pip install aop[prometheus]"
            )

        # Get current stats
        if agent_id:
            tool_counts = analytics.count_by_tool(agent_id)
            event_counts = analytics.count_by_event_type(agent_id)
            avg_durations = analytics.avg_duration_by_tool(agent_id)
        else:
            # Get stats for all agents (synchronous call)
            events = client.query(limit=10000)
            agent_ids = sorted(set(e.get('agent_id') for e in events if e.get('agent_id')))
            tool_counts = {}
            event_counts = {}
            avg_durations = {}
            for agent in agent_ids:
                tool_counts.update(analytics.count_by_tool(agent))
                event_counts.update(analytics.count_by_event_type(agent))
                avg_durations.update(analytics.avg_duration_by_tool(agent))

        # Build Prometheus format output
        lines = []

        # Event counts
        lines.append("# HELP aop_events_total Total number of AOP events")
        lines.append("# TYPE aop_events_total counter")
        for event_type, count in event_counts.items():
            agent_label = f'agent_id="{agent_id}"' if agent_id else 'agent_id="all"'
            lines.append(f'aop_events_total{{event_type="{event_type}",{agent_label}}} {count}')

        # Tool counts
        lines.append("")
        lines.append("# HELP aop_tool_calls_total Total number of tool calls")
        lines.append("# TYPE aop_tool_calls_total counter")
        for tool_name, count in tool_counts.items():
            agent_label = f'agent_id="{agent_id}"' if agent_id else 'agent_id="all"'
            lines.append(f'aop_tool_calls_total{{tool_name="{tool_name}",{agent_label}}} {count}')

        # Average durations
        lines.append("")
        lines.append("# HELP aop_tool_duration_avg_ms Average tool duration in milliseconds")
        lines.append("# TYPE aop_tool_duration_avg_ms gauge")
        for tool_name, duration in avg_durations.items():
            agent_label = f'agent_id="{agent_id}"' if agent_id else 'agent_id="all"'
            lines.append(f'aop_tool_duration_avg_ms{{tool_name="{tool_name}",{agent_label}}} {duration}')

        prometheus_output = "\n".join(lines)

        # Return as downloadable file
        from fastapi.responses import Response
        filename = f"aop_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return Response(
            content=prometheus_output,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WEBSOCKET ENDPOINT (Real-time Events)
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_id: Optional[str] = None
):
    """
    WebSocket endpoint for real-time event streaming.

    Query params:
        agent_id: Optional filter by agent ID

    Usage:
        ws://localhost:8000/ws?agent_id=my-agent
    """
    if not streamer:
        await websocket.close()
        return

    await streamer.connect(websocket)

    try:
        # Start streaming events
        await streamer.poll_and_stream(
            websocket,
            agent_id=agent_id,
            poll_interval=2.0
        )
    except WebSocketDisconnect:
        streamer.disconnect(websocket)


# =============================================================================
# STATIC FILE SERVING (Frontend)
# =============================================================================

@app.get("/")
def serve_frontend():
    """
    Serve frontend index.html.

    Modern, professional dashboard with live feed, trace explorer, and analytics.
    """
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"

    if index_file.exists():
        return FileResponse(index_file)
    else:
        # Placeholder HTML until frontend is built
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AOP Dashboard</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                }
                h1 { color: #333; }
                .endpoint {
                    background: #f5f5f5;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 4px;
                }
                code {
                    background: #e0e0e0;
                    padding: 2px 6px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <h1>AOP Dashboard</h1>
            <p>Backend is running! Frontend coming soon...</p>

            <h2>Available API Endpoints:</h2>
            <div class="endpoint">
                <strong>GET /api/health</strong> - Health check
            </div>
            <div class="endpoint">
                <strong>GET /api/agents</strong> - List all agents
            </div>
            <div class="endpoint">
                <strong>GET /api/events</strong> - Query events
                <br><small>Query params: agent_id, event_type, correlation_id, limit, offset</small>
            </div>
            <div class="endpoint">
                <strong>GET /api/traces/{correlation_id}</strong> - Get trace
            </div>
            <div class="endpoint">
                <strong>GET /api/stats?agent_id=...</strong> - Get statistics
            </div>
            <div class="endpoint">
                <strong>GET /api/timeline?agent_id=...</strong> - Get timeline
            </div>

            <h2>Try it:</h2>
            <p>
                Visit <a href="/api/agents">/api/agents</a> to see available agents<br>
                Visit <a href="/docs">/docs</a> for interactive API documentation
            </p>
        </body>
        </html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html)


# =============================================================================
# SERVER LAUNCHER
# =============================================================================

def run_server(storage: str = "sqlite:///aop_events.db", port: int = 8000, open_browser: bool = True):
    """
    Run the AOP Dashboard server.

    Args:
        storage: Storage connection string
        port: Port to run server on
        open_browser: Whether to open browser automatically
    """
    global storage_url
    storage_url = storage

    print(f"Starting AOP Dashboard...")
    print(f"Storage: {storage}")
    print(f"Server: http://localhost:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print()
    print("Press Ctrl+C to stop")

    # Open browser after short delay
    if open_browser:
        import threading
        def open_browser_delayed():
            import time
            time.sleep(1.5)  # Wait for server to start
            webbrowser.open(f"http://localhost:{port}")

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
