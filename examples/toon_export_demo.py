"""
TOON Export Demo

Demonstrates using the TOON (Token-Oriented Object Notation) exporter
for LLM-optimized event export with 30-60% token reduction.

TOON is perfect for:
- AI-assisted debugging and trace analysis
- Reducing LLM API costs when analyzing large event datasets
- Passing observability data in prompts more efficiently
"""

from aop import AOPClient
from aop.exporters import ToonExporter
from aop.exporters.toon import export_events


def demo_basic_export():
    """Basic TOON export example."""
    print("=" * 70)
    print("DEMO 1: Basic TOON Export")
    print("=" * 70)

    # Initialize AOP client
    client = AOPClient(storage='sqlite:///aop_events.db')

    # Log some sample events
    print("\nLogging 5 sample events...")
    for i in range(5):
        client.log_mcp_tool_call(
            agent_id='demo-agent',
            tool_name='search',
            params={'query': f'test-{i}'},
            correlation_id='demo-trace'
        )

    # Query events
    events = client.query(correlation_id='demo-trace', limit=5)
    print(f"Retrieved {len(events)} events")

    # Export to TOON
    exporter = ToonExporter(flatten=True, delimiter='comma')
    toon_output = exporter.export(events)

    print("\n--- TOON Output ---")
    print(toon_output)

    # Show token savings
    stats = exporter.get_token_estimate(events)
    print(f"\n--- Token Savings ---")
    print(f"TOON tokens:  {stats['toon']}")
    print(f"JSON tokens:  {stats['json']}")
    print(f"Savings:      {stats['savings_percent']}%")

    client.close()


def demo_flattening():
    """Demonstrate field flattening."""
    print("\n" + "=" * 70)
    print("DEMO 2: Field Flattening Comparison")
    print("=" * 70)

    client = AOPClient(storage='sqlite:///aop_events.db')

    # Log event with nested data
    client.log_mcp_tool_call(
        agent_id='demo-agent',
        tool_name='database_query',
        params={'table': 'users', 'limit': 100},
        metadata={'user_id': 'user-123', 'session_id': 'sess-456'},
        correlation_id='flatten-demo'
    )

    events = client.query(correlation_id='flatten-demo', limit=1)

    # Without flattening
    print("\n--- Without Flattening (nested structure) ---")
    exporter_nested = ToonExporter(flatten=False)
    output_nested = exporter_nested.export(events)
    print(output_nested[:500] + "...")

    # With flattening (default)
    print("\n--- With Flattening (flat structure) ---")
    exporter_flat = ToonExporter(flatten=True)
    output_flat = exporter_flat.export(events)
    print(output_flat[:500] + "...")

    print(f"\nNested length: {len(output_nested)} chars")
    print(f"Flat length:   {len(output_flat)} chars")
    print(f"Reduction:     {((len(output_nested) - len(output_flat)) / len(output_nested) * 100):.1f}%")

    client.close()


def demo_delimiter_options():
    """Demonstrate different delimiter options."""
    print("\n" + "=" * 70)
    print("DEMO 3: Delimiter Options")
    print("=" * 70)

    client = AOPClient(storage='sqlite:///aop_events.db')

    # Create uniform events
    events = client.query(limit=3)

    if not events:
        print("No events found. Run demo_basic_export() first.")
        return

    # Comma delimiter (default, best for CSV-like data)
    print("\n--- Comma Delimiter (default) ---")
    exporter_comma = ToonExporter(flatten=True, delimiter='comma')
    print(exporter_comma.export(events)[:300] + "...")

    # Tab delimiter (compact, good for TSV-like data)
    print("\n--- Tab Delimiter ---")
    exporter_tab = ToonExporter(flatten=True, delimiter='tab')
    print(exporter_tab.export(events)[:300] + "...")

    # Pipe delimiter (readable, good for data with commas)
    print("\n--- Pipe Delimiter ---")
    exporter_pipe = ToonExporter(flatten=True, delimiter='pipe')
    print(exporter_pipe.export(events)[:300] + "...")

    client.close()


def demo_field_filtering():
    """Demonstrate field filtering."""
    print("\n" + "=" * 70)
    print("DEMO 4: Field Filtering")
    print("=" * 70)

    client = AOPClient(storage='sqlite:///aop_events.db')
    events = client.query(limit=2)

    if not events:
        print("No events found. Run demo_basic_export() first.")
        return

    # Include only specific fields
    print("\n--- Include Only: id, timestamp, event_type ---")
    exporter_include = ToonExporter(
        flatten=True,
        include_fields=['id', 'timestamp', 'event_type']
    )
    print(exporter_include.export(events))

    # Exclude sensitive fields
    print("\n--- Exclude: agent_id, correlation_id ---")
    exporter_exclude = ToonExporter(
        flatten=True,
        exclude_fields=['agent_id', 'correlation_id']
    )
    print(exporter_exclude.export(events)[:300] + "...")

    client.close()


def demo_export_to_file():
    """Demonstrate exporting to file."""
    print("\n" + "=" * 70)
    print("DEMO 5: Export to File")
    print("=" * 70)

    client = AOPClient(storage='sqlite:///aop_events.db')
    events = client.query(limit=10)

    if not events:
        print("No events found. Run demo_basic_export() first.")
        return

    # Export to file
    exporter = ToonExporter(flatten=True, delimiter='comma')
    filepath = 'events_export.toon'
    exporter.export_to_file(events, filepath)

    print(f"\n✓ Exported {len(events)} events to {filepath}")

    # Read and display
    with open(filepath, 'r') as f:
        content = f.read()
        print(f"\nFile size: {len(content)} bytes")
        print("\nFirst 400 characters:")
        print(content[:400])

    client.close()


def demo_cli_usage():
    """Show CLI usage examples."""
    print("\n" + "=" * 70)
    print("DEMO 6: CLI Usage Examples")
    print("=" * 70)

    print("""
The TOON exporter can also be used via the AOP CLI:

# Basic export to TOON format
aop export --output events.toon --format toon

# Export with custom delimiter
aop export -o events.toon -f toon --toon-delimiter pipe

# Export without flattening
aop export -o events.toon -f toon --no-toon-flatten

# Export specific trace
aop export -o trace.toon -f toon --correlation-id abc123

# Export recent events only
aop export -o recent.toon -f toon --last 1h --limit 100

# Export filtered events
aop export -o filtered.toon -f toon --agent-id my-agent --event-type mcp.tool.called

The CLI will show token savings estimate:
  ✓ Exported 100 events to events.toon (TOON) (~45.2% fewer tokens vs JSON)
    """)


def demo_convenience_function():
    """Demonstrate convenience function."""
    print("\n" + "=" * 70)
    print("DEMO 7: Convenience Function")
    print("=" * 70)

    client = AOPClient(storage='sqlite:///aop_events.db')
    events = client.query(limit=3)

    if not events:
        print("No events found. Run demo_basic_export() first.")
        return

    # Use convenience function
    print("\nUsing export_events() convenience function:")
    toon_output = export_events(events, flatten=True, delimiter='comma')
    print(toon_output)

    client.close()


def demo_llm_use_case():
    """Demonstrate LLM debugging use case."""
    print("\n" + "=" * 70)
    print("DEMO 8: LLM-Assisted Debugging")
    print("=" * 70)

    client = AOPClient(storage='sqlite:///aop_events.db')

    # Get trace events
    events = client.query(correlation_id='demo-trace', limit=10)

    if not events:
        print("No events found. Run demo_basic_export() first.")
        return

    # Export to TOON for LLM prompt
    exporter = ToonExporter(
        flatten=True,
        delimiter='comma',
        include_fields=['id', 'timestamp', 'event_type', 'data.tool_name', 'data.duration_ms']
    )

    toon_output = exporter.export(events)

    print("\nPrompt for LLM:")
    print("-" * 70)
    print(f"""
Analyze this execution trace in TOON format:

{toon_output}

Questions:
1. Which tool took the longest to execute?
2. Are there any performance anomalies?
3. What is the average execution time?
    """)

    stats = exporter.get_token_estimate(events)
    print("-" * 70)
    print(f"\nToken savings: {stats['savings_percent']}% vs JSON")
    print(f"Cost savings:  ~${(stats['json'] - stats['toon']) * 0.00001:.4f} (at $10/1M tokens)")

    client.close()


if __name__ == '__main__':
    # Run all demos
    print("\n" + "🚀 AOP TOON Export Demo" + "\n")

    try:
        demo_basic_export()
        demo_flattening()
        demo_delimiter_options()
        demo_field_filtering()
        demo_export_to_file()
        demo_cli_usage()
        demo_convenience_function()
        demo_llm_use_case()

        print("\n" + "=" * 70)
        print("✓ All demos completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
