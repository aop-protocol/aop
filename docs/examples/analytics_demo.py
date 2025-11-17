"""
Demo script showing AOP Analytics capabilities.

Shows how to analyze agent behavior using:
- Trace reconstruction
- Aggregations
- Time-series analysis
"""

import asyncio
from aop import AOPClient, Analytics


async def main():
    # Initialize client
    client = AOPClient(storage='sqlite:///analytics_demo.db')
    analytics = Analytics(client)

    print("=== AOP Analytics Demo ===\n")

    # Generate some sample events with a trace
    print("1. Generating sample events...")

    correlation_id = 'demo-trace-001'

    # Tool 1: Search
    @client.mcp.observe_tool(agent_id='demo-agent', correlation_id=correlation_id)
    async def search_database(query: str) -> dict:
        """Search the database"""
        await asyncio.sleep(0.05)  # Simulate work
        return {'results': [f'result-{i}' for i in range(10)], 'count': 10}

    # Tool 2: Process results
    @client.mcp.observe_tool(agent_id='demo-agent', correlation_id=correlation_id)
    async def process_results(data: dict) -> dict:
        """Process search results"""
        await asyncio.sleep(0.02)  # Simulate work
        return {'processed': len(data['results']), 'status': 'ok'}

    # Tool 3: Store output
    @client.mcp.observe_tool(agent_id='demo-agent', correlation_id=correlation_id)
    async def store_output(data: dict) -> dict:
        """Store the processed data"""
        await asyncio.sleep(0.01)  # Simulate work
        return {'stored': True, 'id': 'output-123'}

    # Execute the workflow
    search_results = await search_database('test query')
    processed = await process_results(search_results)
    stored = await store_output(processed)

    print(f"   ✓ Generated workflow with {stored['id']}\n")

    # Generate more events for aggregation testing
    print("2. Generating additional events for analytics...")

    for i in range(5):
        await search_database(f'query-{i}')

    for i in range(3):
        await process_results({'results': [f'r{i}']})

    print(f"   ✓ Generated total events across multiple tools\n")

    # ========================================================================
    # TRACE RECONSTRUCTION
    # ========================================================================

    print("=" * 60)
    print("TRACE RECONSTRUCTION")
    print("=" * 60)

    trace = analytics.reconstruct_trace(correlation_id=correlation_id)

    print(f"\nTrace: {correlation_id}")
    print(f"  Total Events: {trace['event_count']}")
    print(f"  Total Duration: {trace['total_duration_ms']}ms")
    print(f"  Errors: {trace['error_count']}")

    print("\n  Event Flow:")
    def print_tree(node, depth=0):
        indent = "  " * depth
        event = node.get('event')
        if event:
            event_type = event['event_type']
            tool_name = event.get('data', {}).get('tool_name', 'N/A')
            duration = event.get('duration_ms', 'N/A')

            if event_type.endswith('.called'):
                print(f"{indent}└─ {tool_name} (call)")
            elif event_type.endswith('.completed'):
                print(f"{indent}   └─ completed ({duration}ms)")
            elif event_type.endswith('.error'):
                error = event.get('error', {})
                print(f"{indent}   └─ ERROR: {error.get('code')}")

        for child in node.get('children', []):
            print_tree(child, depth + 1)

    # Print from root
    print_tree({'event': trace['root_event'], 'children': trace['children']})

    # ========================================================================
    # AGGREGATIONS
    # ========================================================================

    print("\n" + "=" * 60)
    print("AGGREGATIONS")
    print("=" * 60)

    # Count by tool
    counts = analytics.count_by_tool('demo-agent')
    print("\nTool Call Counts:")
    for tool, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {tool:20s}: {count:3d} calls")

    # Count by event type
    type_counts = analytics.count_by_event_type('demo-agent')
    print("\nEvent Type Counts:")
    for event_type, count in sorted(type_counts.items()):
        print(f"  {event_type:25s}: {count:3d}")

    # Average duration by tool
    avg_durations = analytics.avg_duration_by_tool('demo-agent')
    print("\nAverage Duration by Tool:")
    for tool, avg_ms in sorted(avg_durations.items(), key=lambda x: -x[1]):
        print(f"  {tool:20s}: {avg_ms:6.1f}ms")

    # Percentiles
    p50 = analytics.percentile_duration('demo-agent', percentile=50)
    p95 = analytics.percentile_duration('demo-agent', percentile=95)
    p99 = analytics.percentile_duration('demo-agent', percentile=99)

    print("\nLatency Percentiles (all tools):")
    print(f"  P50 (median):  {p50:6.1f}ms")
    print(f"  P95:           {p95:6.1f}ms")
    print(f"  P99:           {p99:6.1f}ms")

    # Tool-specific percentile
    search_p95 = analytics.percentile_duration(
        'demo-agent',
        'search_database',
        percentile=95
    )
    print(f"\nSearch Tool P95: {search_p95:.1f}ms")

    # ========================================================================
    # TIME-SERIES ANALYSIS
    # ========================================================================

    print("\n" + "=" * 60)
    print("TIME-SERIES ANALYSIS")
    print("=" * 60)

    # Events over time (hourly buckets)
    timeline = analytics.events_over_time('demo-agent', bucket_size='1h')

    print("\nEvents Over Time (hourly):")
    for bucket in timeline[:5]:  # Show first 5 buckets
        print(f"  {bucket['time']:25s}: {bucket['count']:3d} events")

    if len(timeline) > 5:
        print(f"  ... and {len(timeline) - 5} more time buckets")

    # Event rate
    rate_1min = analytics.event_rate('demo-agent', window_minutes=1)
    rate_60min = analytics.event_rate('demo-agent', window_minutes=60)

    print("\nEvent Rate:")
    print(f"  Last 1 minute:  {rate_1min:.2f} events/min")
    print(f"  Last 60 minutes: {rate_60min:.2f} events/min")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_events = client.query(agent_id='demo-agent')

    print(f"\nTotal Events Stored: {len(all_events)}")
    print(f"Total Tools Used: {len(counts)}")
    print(f"Traces Captured: 1")
    print(f"Database: analytics_demo.db")

    print("\n" + "=" * 60)
    print("\n✓ Demo complete!")
    print("\nYou can now query the database with:")
    print("  from aop import AOPClient, Analytics")
    print("  client = AOPClient(storage='sqlite:///analytics_demo.db')")
    print("  analytics = Analytics(client)")
    print("  # Then use any analytics methods shown above")

    # Cleanup
    client.close()


if __name__ == '__main__':
    asyncio.run(main())
