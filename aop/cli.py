"""
AOP Command-Line Interface

Provides commands for querying events, visualizing traces, and viewing analytics.

Commands:
  aop query      - Query and filter events
  aop trace      - Visualize execution traces
  aop stats      - Show analytics and statistics
  aop export     - Export events to JSON or CSV
  aop validate   - Validate event files
  aop dashboard  - Launch web-based dashboard
"""

import sys
import time
from typing import Optional
from datetime import datetime, timedelta

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.text import Text
except ImportError:
    print("Error: CLI dependencies not installed.")
    print("Install with: pip install aop[cli]")
    sys.exit(1)

from .client import AOPClient
from .analytics import Analytics
from .exporters import JSONExporter, CSVExporter, ToonExporter, OpenTelemetryExporter, PrometheusExporterServer


console = Console()


@click.group()
@click.version_option(version='0.1.0')
def main():
    """
    AOP (Agentic Observability Protocol) CLI

    Query events, visualize traces, and analyze agent behavior.
    """
    pass


@main.command()
@click.option('--storage', '-s', default='sqlite:///aop_events.db', help='Storage connection string')
@click.option('--agent-id', '-a', help='Filter by agent ID')
@click.option('--event-type', '-e', help='Filter by event type')
@click.option('--protocol', '-p', help='Filter by protocol (mcp, a2a, ap2)')
@click.option('--correlation-id', '-c', help='Filter by correlation ID')
@click.option('--limit', '-l', type=int, default=50, help='Maximum number of events to show')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'compact']), default='table', help='Output format')
@click.option('--last', type=str, help='Show events from last N minutes/hours (e.g., "30m", "2h", "1d")')
def query(
    storage: str,
    agent_id: Optional[str],
    event_type: Optional[str],
    protocol: Optional[str],
    correlation_id: Optional[str],
    limit: int,
    format: str,
    last: Optional[str]
):
    """
    Query and filter AOP events.

    Examples:
      aop query --agent-id my-agent --limit 10
      aop query --event-type mcp.tool.called --last 1h
      aop query --correlation-id trace-123 --format json
    """
    try:
        client = AOPClient(storage=storage)

        # Parse --last option
        start_time = None
        if last:
            start_time = _parse_time_window(last)

        # Query events
        events = client.query(
            agent_id=agent_id,
            event_type=event_type,
            protocol=protocol,
            correlation_id=correlation_id,
            start_time=start_time,
            limit=limit
        )

        if not events:
            console.print("[yellow]No events found matching the criteria.[/yellow]")
            client.close()
            return

        # Display results
        if format == 'json':
            import json
            console.print_json(json.dumps(events, indent=2))
        elif format == 'compact':
            _display_compact(events)
        else:  # table
            _display_table(events)

        client.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option('--storage', '-s', default='sqlite:///aop_events.db', help='Storage connection string')
@click.option('--correlation-id', '-c', required=True, help='Correlation ID to reconstruct')
@click.option('--format', '-f', type=click.Choice(['tree', 'table', 'json']), default='tree', help='Output format')
def trace(
    storage: str,
    correlation_id: str,
    format: str
):
    """
    Visualize execution traces as a tree.

    Examples:
      aop trace --correlation-id trace-123
      aop trace -c demo-trace-001 --format table
    """
    try:
        client = AOPClient(storage=storage)
        analytics = Analytics(client)

        # Reconstruct trace
        trace_data = analytics.reconstruct_trace(correlation_id=correlation_id)

        if trace_data['event_count'] == 0:
            console.print(f"[yellow]No trace found for correlation_id: {correlation_id}[/yellow]")
            client.close()
            return

        # Display trace
        if format == 'json':
            import json
            console.print_json(json.dumps(trace_data, indent=2, default=str))
        elif format == 'table':
            _display_trace_table(trace_data)
        else:  # tree
            _display_trace_tree(trace_data)

        # Display summary
        _display_trace_summary(trace_data, correlation_id)

        client.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option('--storage', '-s', default='sqlite:///aop_events.db', help='Storage connection string')
@click.option('--agent-id', '-a', required=True, help='Agent ID to analyze')
@click.option('--window', '-w', type=str, help='Time window (e.g., "30m", "2h", "1d")')
def stats(
    storage: str,
    agent_id: str,
    window: Optional[str]
):
    """
    Show analytics and statistics for an agent.

    Examples:
      aop stats --agent-id my-agent
      aop stats -a demo-agent --window 1h
    """
    try:
        client = AOPClient(storage=storage)
        analytics = Analytics(client)

        # Display header
        console.print(Panel(
            f"[bold cyan]Analytics for Agent: {agent_id}[/bold cyan]",
            border_style="cyan"
        ))
        console.print()

        # Event counts by tool
        tool_counts = analytics.count_by_tool(agent_id)
        if tool_counts:
            _display_tool_counts(tool_counts)
        else:
            console.print("[yellow]No tool executions found.[/yellow]")
            client.close()
            return

        # Event type distribution
        type_counts = analytics.count_by_event_type(agent_id)
        _display_event_type_counts(type_counts)

        # Duration statistics
        avg_durations = analytics.avg_duration_by_tool(agent_id)
        if avg_durations:
            _display_duration_stats(avg_durations)

        # Percentiles
        p50 = analytics.percentile_duration(agent_id, percentile=50)
        p95 = analytics.percentile_duration(agent_id, percentile=95)
        p99 = analytics.percentile_duration(agent_id, percentile=99)

        if p50 > 0:
            _display_percentiles(p50, p95, p99)

        # Event rate
        if window:
            minutes = _parse_window_to_minutes(window)
            rate = analytics.event_rate(agent_id, window_minutes=minutes)
            console.print(f"\n[bold]Event Rate ({window}):[/bold] {rate:.2f} events/min")

        client.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option('--storage', '-s', default='sqlite:///aop_events.db', help='Storage connection string')
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'toon']), default='json', help='Output format')
@click.option('--agent-id', '-a', help='Filter by agent ID')
@click.option('--event-type', '-e', help='Filter by event type')
@click.option('--protocol', '-p', help='Filter by protocol')
@click.option('--correlation-id', '-c', help='Filter by correlation ID')
@click.option('--last', type=str, help='Export events from last N minutes/hours (e.g., "30m", "2h", "1d")')
@click.option('--limit', '-l', type=int, help='Maximum number of events to export')
@click.option('--toon-flatten/--no-toon-flatten', default=True, help='[TOON] Flatten nested fields (default: True)')
@click.option('--toon-delimiter', type=click.Choice(['comma', 'tab', 'pipe']), default='comma', help='[TOON] Delimiter for tabular arrays')
def export(
    storage: str,
    output: str,
    format: str,
    agent_id: Optional[str],
    event_type: Optional[str],
    protocol: Optional[str],
    correlation_id: Optional[str],
    last: Optional[str],
    limit: Optional[int],
    toon_flatten: bool,
    toon_delimiter: str
):
    """
    Export AOP events to JSON, CSV, or TOON format.

    TOON (Token-Oriented Object Notation) achieves 30-60% token reduction
    vs JSON - perfect for LLM-assisted debugging and trace analysis.

    Examples:
      aop export --output events.json
      aop export --output metrics.csv --format csv --last 30d
      aop export -o data.json --agent-id my-agent --limit 1000
      aop export --output events.toon --format toon --toon-flatten
      aop export -o trace.toon -f toon --correlation-id abc123
    """
    try:
        client = AOPClient(storage=storage)

        # Parse --last option
        start_time = None
        if last:
            start_time = _parse_time_window(last)

        # Query events
        events = client.query(
            agent_id=agent_id,
            event_type=event_type,
            protocol=protocol,
            correlation_id=correlation_id,
            start_time=start_time,
            limit=limit
        )

        if not events:
            console.print("[yellow]No events found matching the criteria.[/yellow]")
            client.close()
            return

        # Export to file using exporter classes
        if format == 'json':
            exporter = JSONExporter()
            exporter.export_to_file(events, output)
            console.print(f"[green]✓[/green] Exported {len(events)} events to {output} (JSON)")

        elif format == 'csv':
            exporter = CSVExporter()
            exporter.export_to_file(events, output)
            console.print(f"[green]✓[/green] Exported {len(events)} events to {output} (CSV)")

        elif format == 'toon':
            exporter = ToonExporter(flatten=toon_flatten, delimiter=toon_delimiter)
            exporter.export_to_file(events, output)

            # Show token savings estimate
            stats = exporter.get_token_estimate(events)
            savings_msg = f"[dim](~{stats['savings_percent']}% fewer tokens vs JSON)[/dim]"
            console.print(f"[green]✓[/green] Exported {len(events)} events to {output} (TOON) {savings_msg}")

        client.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--check-schema', is_flag=True, help='Validate against AOP event schema')
@click.option('--check-references', is_flag=True, help='Check parent_id and correlation_id references')
def validate(
    file_path: str,
    check_schema: bool,
    check_references: bool
):
    """
    Validate AOP event files.

    Examples:
      aop validate events.json
      aop validate events.json --check-schema
      aop validate events.json --check-schema --check-references
    """
    try:
        import json
        from .validation import validate_event

        # Read file
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Support both single event and array of events
        events = data if isinstance(data, list) else [data]

        console.print(f"[cyan]Validating {len(events)} event(s) from {file_path}...[/cyan]\n")

        errors = []
        warnings = []

        # Schema validation
        if check_schema or not check_references:  # Default to schema check
            console.print("[bold]Schema Validation:[/bold]")
            for i, event in enumerate(events):
                try:
                    validate_event(event)
                except Exception as e:
                    errors.append(f"Event {i}: {str(e)}")

            if errors:
                console.print(f"  [red]✗ Found {len(errors)} schema error(s)[/red]")
                for error in errors[:10]:  # Show first 10 errors
                    console.print(f"    • {error}")
                if len(errors) > 10:
                    console.print(f"    ... and {len(errors) - 10} more")
            else:
                console.print(f"  [green]✓ All events valid[/green]")

        # Reference validation
        if check_references:
            console.print("\n[bold]Reference Validation:[/bold]")
            event_ids = {e.get('id') for e in events if e.get('id')}
            correlation_ids = {e.get('correlation_id') for e in events if e.get('correlation_id')}

            # Check parent_id references
            orphaned = []
            for event in events:
                parent_id = event.get('parent_id')
                if parent_id and parent_id not in event_ids:
                    orphaned.append(f"Event {event.get('id')} references missing parent {parent_id}")

            if orphaned:
                warnings.extend(orphaned)
                console.print(f"  [yellow]⚠ Found {len(orphaned)} orphaned parent reference(s)[/yellow]")
                for warning in orphaned[:5]:
                    console.print(f"    • {warning}")
                if len(orphaned) > 5:
                    console.print(f"    ... and {len(orphaned) - 5} more")
            else:
                console.print(f"  [green]✓ All parent references valid[/green]")

            # Check correlation_id usage
            console.print(f"  [cyan]ℹ Found {len(correlation_ids)} unique correlation ID(s)[/cyan]")

        # Summary
        console.print()
        if errors:
            console.print(Panel(
                f"[red]Validation Failed[/red]\n{len(errors)} error(s), {len(warnings)} warning(s)",
                border_style="red"
            ))
            sys.exit(1)
        elif warnings:
            console.print(Panel(
                f"[yellow]Validation Passed with Warnings[/yellow]\n{len(warnings)} warning(s)",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                f"[green]Validation Passed[/green]\nAll checks successful!",
                border_style="green"
            ))

    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option('--storage', '-s', default='sqlite:///aop_events.db', help='Storage connection string')
@click.option('--port', '-p', default=9090, type=int, help='Port to run server on')
@click.option('--poll-interval', default=30.0, type=float, help='Polling interval in seconds')
def prometheus(storage: str, port: int, poll_interval: float):
    """
    Start Prometheus metrics exporter server.

    Exposes AOP events as Prometheus metrics at /metrics endpoint.
    Prometheus can scrape this endpoint to collect metrics.

    Examples:
      aop prometheus
      aop prometheus --port 9090 --storage sqlite:///my_events.db
    """
    try:
        if PrometheusExporterServer is None:
            console.print("[red]Error:[/red] Prometheus dependencies not installed.")
            console.print("Install with: [cyan]pip install aop[prometheus][/cyan]")
            sys.exit(1)

        server = PrometheusExporterServer(
            storage=storage,
            port=port,
            poll_interval=poll_interval
        )
        
        console.print(f"[green]Starting Prometheus exporter server...[/green]")
        console.print(f"Storage: {storage}")
        console.print(f"Port: {port}")
        console.print(f"Metrics: http://localhost:{port}/metrics")
        console.print()
        console.print("Press Ctrl+C to stop")
        
        server.start()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping server...[/yellow]")
            server.stop()
            console.print("[green]✓ Server stopped[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option('--storage', '-s', default='sqlite:///aop_events.db', help='Storage connection string')
@click.option('--output', '-o', help='Output file path (optional, for JSON export)')
@click.option('--endpoint', '-e', help='OTEL collector endpoint (e.g., http://localhost:4317)')
@click.option('--agent-id', '-a', help='Filter by agent ID')
@click.option('--correlation-id', '-c', help='Export trace by correlation ID')
@click.option('--limit', '-l', type=int, default=1000, help='Maximum number of events')
def export_otel(
    storage: str,
    output: Optional[str],
    endpoint: Optional[str],
    agent_id: Optional[str],
    correlation_id: Optional[str],
    limit: int
):
    """
    Export AOP events to OpenTelemetry format.

    Can export to OTEL collector or JSON file.

    Examples:
      aop export-otel --endpoint http://localhost:4317
      aop export-otel --output trace.json --correlation-id trace-123
    """
    try:
        if OpenTelemetryExporter is None:
            console.print("[red]Error:[/red] OpenTelemetry dependencies not installed.")
            console.print("Install with: [cyan]pip install aop[otel][/cyan]")
            sys.exit(1)

        client = AOPClient(storage=storage)
        exporter = OpenTelemetryExporter(client=client)

        # Get events
        if correlation_id:
            events = client.get_trace(correlation_id)
            console.print(f"[cyan]Exporting trace: {correlation_id}[/cyan]")
        else:
            events = client.query(agent_id=agent_id, limit=limit)
            console.print(f"[cyan]Exporting {len(events)} events[/cyan]")

        if not events:
            console.print("[yellow]No events found to export.[/yellow]")
            client.close()
            return

        # Convert to spans
        spans = exporter.export_events(events)
        console.print(f"[green]✓[/green] Converted {len(spans)} events to OTEL spans")

        # Export
        if endpoint:
            exporter.export_to_collector(spans=spans, endpoint=endpoint)
            console.print(f"[green]✓[/green] Exported to OTEL collector: {endpoint}")
        elif output:
            exporter.export_to_file(spans=spans, filepath=output)
            console.print(f"[green]✓[/green] Exported to file: {output}")
        else:
            console.print("[yellow]No export destination specified. Use --endpoint or --output[/yellow]")

        client.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option('--storage', '-s', default='sqlite:///aop_events.db', help='Storage connection string')
@click.option('--port', '-p', default=8000, type=int, help='Port to run server on')
@click.option('--no-browser', is_flag=True, help='Do not open browser automatically')
def dashboard(storage: str, port: int, no_browser: bool):
    """
    Launch the AOP Dashboard web interface.

    The dashboard provides a web-based UI for exploring events, visualizing traces,
    and analyzing agent behavior in real-time.

    Examples:
      aop dashboard
      aop dashboard --storage sqlite:///my_events.db
      aop dashboard --port 8080 --no-browser
    """
    try:
        from aop.dashboard import run_server

        run_server(
            storage=storage,
            port=port,
            open_browser=not no_browser
        )
    except ImportError:
        console.print("[red]Error:[/red] Dashboard dependencies not installed.")
        console.print("Install with: [cyan]pip install aop[dashboard][/cyan]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# =============================================================================
# DISPLAY HELPERS
# =============================================================================

def _display_table(events):
    """Display events as a Rich table."""
    table = Table(title="Events", show_lines=True)

    table.add_column("Timestamp", style="cyan", no_wrap=True)
    table.add_column("Agent ID", style="magenta")
    table.add_column("Event Type", style="green")
    table.add_column("Duration", style="yellow", justify="right")
    table.add_column("Data", style="white")

    for event in events:
        timestamp = event['timestamp'][:19]  # Trim milliseconds
        agent_id = event['agent_id']
        event_type = event['event_type']
        duration = f"{event.get('duration_ms', '-')}ms" if event.get('duration_ms') else '-'

        # Format data field
        data = event.get('data', {})
        if 'tool_name' in data:
            data_str = f"tool: {data['tool_name']}"
        elif 'task_id' in data:
            data_str = f"task: {data['task_id']}"
        else:
            data_str = str(data)[:50] + "..." if len(str(data)) > 50 else str(data)

        table.add_row(timestamp, agent_id, event_type, duration, data_str)

    console.print(table)


def _display_compact(events):
    """Display events in compact format."""
    for event in events:
        timestamp = event['timestamp'][:19]
        event_type = event['event_type']
        data = event.get('data', {})

        tool_name = data.get('tool_name', '')
        duration = event.get('duration_ms', '')

        line = f"[cyan]{timestamp}[/cyan] [{event_type}]"
        if tool_name:
            line += f" [magenta]{tool_name}[/magenta]"
        if duration:
            line += f" [yellow]({duration}ms)[/yellow]"

        console.print(line)


def _display_trace_tree(trace_data):
    """Display trace as a tree structure."""
    tree = Tree(f"[bold cyan]Trace[/bold cyan]")

    def build_tree_node(node_data, parent_tree):
        event = node_data.get('event')
        if event:
            event_type = event['event_type']
            data = event.get('data', {})
            tool_name = data.get('tool_name', 'N/A')
            duration = event.get('duration_ms', 'N/A')

            # Format node label
            if event_type.endswith('.called'):
                label = f"[magenta]{tool_name}[/magenta] (called)"
            elif event_type.endswith('.completed'):
                label = f"[green]{tool_name}[/green] (completed) [yellow]{duration}ms[/yellow]"
            elif event_type.endswith('.error'):
                error = event.get('error', {})
                error_code = error.get('code', 'ERROR')
                label = f"[red]{tool_name}[/red] (error: {error_code})"
            else:
                label = f"{event_type}"

            node = parent_tree.add(label)

            # Add children
            for child in node_data.get('children', []):
                build_tree_node(child, node)

    # Build tree from root
    root_node = {
        'event': trace_data['root_event'],
        'children': trace_data['children']
    }
    build_tree_node(root_node, tree)

    console.print(tree)


def _display_trace_table(trace_data):
    """Display trace as a table."""
    table = Table(title="Trace Events", show_lines=True)

    table.add_column("Event Type", style="cyan")
    table.add_column("Tool", style="magenta")
    table.add_column("Duration", style="yellow", justify="right")
    table.add_column("Status", style="white")

    def collect_events(node_data):
        events = []
        event = node_data.get('event')
        if event:
            events.append(event)
        for child in node_data.get('children', []):
            events.extend(collect_events(child))
        return events

    root_node = {
        'event': trace_data['root_event'],
        'children': trace_data['children']
    }
    events = collect_events(root_node)

    for event in events:
        event_type = event['event_type']
        data = event.get('data', {})
        tool_name = data.get('tool_name', 'N/A')
        duration = f"{event.get('duration_ms', '-')}ms" if event.get('duration_ms') else '-'

        if event_type.endswith('.error'):
            status = f"[red]ERROR[/red]"
        elif event_type.endswith('.completed'):
            status = f"[green]OK[/green]"
        else:
            status = "-"

        table.add_row(event_type, tool_name, duration, status)

    console.print(table)


def _display_trace_summary(trace_data, correlation_id):
    """Display trace summary panel."""
    summary = f"""
[bold]Correlation ID:[/bold] {correlation_id}
[bold]Total Events:[/bold] {trace_data['event_count']}
[bold]Total Duration:[/bold] {trace_data['total_duration_ms']}ms
[bold]Errors:[/bold] {trace_data['error_count']}
"""

    console.print(Panel(summary, title="Trace Summary", border_style="green"))


def _display_tool_counts(tool_counts):
    """Display tool usage counts."""
    table = Table(title="Tool Usage", show_header=True)
    table.add_column("Tool Name", style="magenta")
    table.add_column("Calls", style="cyan", justify="right")

    for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
        table.add_row(tool, str(count))

    console.print(table)


def _display_event_type_counts(type_counts):
    """Display event type distribution."""
    console.print("\n[bold]Event Type Distribution:[/bold]")

    for event_type, count in sorted(type_counts.items()):
        console.print(f"  {event_type:30s}: {count:4d}")


def _display_duration_stats(avg_durations):
    """Display average duration by tool."""
    table = Table(title="Average Duration by Tool", show_header=True)
    table.add_column("Tool Name", style="magenta")
    table.add_column("Avg Duration (ms)", style="yellow", justify="right")

    for tool, avg_ms in sorted(avg_durations.items(), key=lambda x: -x[1]):
        table.add_row(tool, f"{avg_ms:.1f}")

    console.print(table)


def _display_percentiles(p50, p95, p99):
    """Display latency percentiles."""
    console.print("\n[bold]Latency Percentiles:[/bold]")
    console.print(f"  P50 (median): [cyan]{p50:6.1f}ms[/cyan]")
    console.print(f"  P95:          [yellow]{p95:6.1f}ms[/yellow]")
    console.print(f"  P99:          [red]{p99:6.1f}ms[/red]")


# =============================================================================
# TIME PARSING HELPERS
# =============================================================================

def _parse_time_window(window: str) -> datetime:
    """Parse time window string like '30m', '2h', '1d' to datetime."""
    from datetime import timezone

    if window.endswith('m'):
        minutes = int(window[:-1])
        return datetime.now(timezone.utc) - timedelta(minutes=minutes)
    elif window.endswith('h'):
        hours = int(window[:-1])
        return datetime.now(timezone.utc) - timedelta(hours=hours)
    elif window.endswith('d'):
        days = int(window[:-1])
        return datetime.now(timezone.utc) - timedelta(days=days)
    else:
        raise ValueError(f"Invalid time window format: {window}. Use '30m', '2h', or '1d'.")


def _parse_window_to_minutes(window: str) -> int:
    """Parse time window string to total minutes."""
    if window.endswith('m'):
        return int(window[:-1])
    elif window.endswith('h'):
        return int(window[:-1]) * 60
    elif window.endswith('d'):
        return int(window[:-1]) * 24 * 60
    else:
        raise ValueError(f"Invalid time window format: {window}")


if __name__ == '__main__':
    main()
