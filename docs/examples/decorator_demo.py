"""
Demo script showing the @observe_tool decorator in action.

This demonstrates how the decorator reduces instrumentation code
from ~7 lines per tool to just 1 line.
"""

import asyncio
from aop import AOPClient


def main():
    # Initialize AOP client
    client = AOPClient(storage='sqlite:///decorator_demo.db')

    print("=== AOP Decorator Demo ===\n")

    # Example 1: Async tool with decorator
    print("1. Defining async tool with decorator...")

    @client.mcp.observe_tool(agent_id='demo-agent')
    async def search_database(query: str, limit: int = 10) -> dict:
        """Search tool that queries a database"""
        # Simulate some work
        await asyncio.sleep(0.05)
        return {
            'query': query,
            'results': ['result1', 'result2', 'result3'],
            'count': 3,
            'limit': limit
        }

    # Call the tool
    print("   Calling search_database('python', limit=20)...")
    result = asyncio.run(search_database('python', limit=20))
    print(f"   ✓ Result: {result['count']} results found\n")

    # Example 2: Sync tool with decorator
    print("2. Defining sync tool with decorator...")

    @client.mcp.observe_tool(agent_id='demo-agent')
    def calculate(operation: str, a: float, b: float) -> float:
        """Calculator tool"""
        operations = {
            'add': lambda x, y: x + y,
            'subtract': lambda x, y: x - y,
            'multiply': lambda x, y: x * y,
            'divide': lambda x, y: x / y
        }
        return operations[operation](a, b)

    # Call the tool
    print("   Calling calculate('multiply', 7, 6)...")
    result = calculate('multiply', 7, 6)
    print(f"   ✓ Result: {result}\n")

    # Example 3: Tool with error handling
    print("3. Testing error handling...")

    @client.mcp.observe_tool(agent_id='demo-agent')
    def risky_operation(value: int) -> float:
        """Operation that might fail"""
        return 100 / value

    # Call with error
    print("   Calling risky_operation(0)...")
    try:
        risky_operation(0)
    except ZeroDivisionError:
        print("   ✓ Error caught and logged automatically\n")

    # Query all events
    print("=== Querying Logged Events ===\n")
    events = client.query(agent_id='demo-agent')

    print(f"Total events logged: {len(events)}\n")

    # Group by event type
    from collections import Counter
    event_types = Counter(e['event_type'] for e in events)

    print("Events by type:")
    for event_type, count in event_types.items():
        print(f"  - {event_type}: {count}")

    print("\n=== Event Details ===\n")

    # Show details for each tool call
    call_events = [e for e in events if e['event_type'] == 'mcp.tool.called']

    for i, call in enumerate(call_events, 1):
        tool_name = call['data']['tool_name']
        params = call['data'].get('params', {})

        print(f"{i}. Tool: {tool_name}")
        print(f"   Event ID: {call['id']}")
        print(f"   Timestamp: {call['timestamp']}")
        print(f"   Parameters: {params}")

        # Find corresponding completion or error
        child_event = next(
            (e for e in events if e.get('parent_id') == call['id']),
            None
        )

        if child_event:
            event_type = child_event['event_type']
            if event_type == 'mcp.tool.completed':
                duration = child_event.get('duration_ms', 'N/A')
                result = child_event['data'].get('result')
                print(f"   Status: ✓ Completed in {duration}ms")
                print(f"   Result: {result}")
            elif event_type == 'mcp.tool.error':
                error = child_event.get('error', {})
                print(f"   Status: ✗ Error - {error.get('code')}")
                print(f"   Error: {error.get('message')}")

        print()

    # Cleanup
    client.close()

    print("=== Code Comparison ===\n")
    print("WITHOUT decorator (7 lines):")
    print("""
    with client.mcp.tool_execution('agent', 'search', {'query': q}) as call:
        result = perform_search(q)
        call.set_result(result, duration_ms=150)
    """)

    print("\nWITH decorator (1 line):")
    print("""
    @client.mcp.observe_tool('agent')
    async def search(query: str):
        return perform_search(query)
    """)

    print("\n✓ Demo complete! Events saved to decorator_demo.db")


if __name__ == '__main__':
    main()
