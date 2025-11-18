"""
Complete MCP Server Example with AOP Observability

This is a fully functional MCP server with AOP instrumentation.
You can use this as a template for your own MCP servers.

Usage:
1. Install dependencies: pip install aop[cli] mcp httpx
2. Add to Claude Desktop config:
   {
     "mcpServers": {
       "demo-server": {
         "command": "python",
         "args": ["/path/to/this/file.py"]
       }
     }
   }
3. Restart Claude Desktop
4. Use tools in Claude chat
5. View logs: aop query --agent-id demo-server
6. View dashboard: aop dashboard
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from aop import AOPClient
import asyncio
import httpx
from typing import Optional

# Initialize AOP (creates database in current directory)
aop = AOPClient(storage='sqlite:///demo_server_events.db')

# Create MCP server
server = Server("demo-server")


@server.call_tool()
@aop.mcp.observe_tool(agent_id='demo-server')
async def search_web(query: str, max_results: int = 5) -> dict:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Dictionary with search results
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                'https://api.duckduckgo.com/',
                params={'q': query, 'format': 'json'}
            )
            data = response.json()

            # Extract related topics
            results = []
            for topic in data.get('RelatedTopics', [])[:max_results]:
                if 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0],
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', '')
                    })

            return {
                'query': query,
                'count': len(results),
                'results': results
            }
        except Exception as e:
            return {
                'error': str(e),
                'query': query
            }


@server.call_tool()
@aop.mcp.observe_tool(agent_id='demo-server')
async def calculator(operation: str, a: float, b: float) -> dict:
    """
    Perform basic arithmetic operations.

    Args:
        operation: One of: add, subtract, multiply, divide
        a: First number
        b: Second number

    Returns:
        Dictionary with the result
    """
    operations = {
        'add': lambda x, y: x + y,
        'subtract': lambda x, y: x - y,
        'multiply': lambda x, y: x * y,
        'divide': lambda x, y: x / y if y != 0 else None
    }

    if operation not in operations:
        return {
            'error': f'Invalid operation: {operation}',
            'valid_operations': list(operations.keys())
        }

    result = operations[operation](a, b)

    if result is None:
        return {'error': 'Division by zero'}

    return {
        'operation': operation,
        'a': a,
        'b': b,
        'result': result
    }


@server.call_tool()
@aop.mcp.observe_tool(agent_id='demo-server')
async def get_time(timezone: Optional[str] = None) -> dict:
    """
    Get current time (optionally for a specific timezone).

    Args:
        timezone: Optional timezone (e.g., 'America/New_York')

    Returns:
        Current time information
    """
    from datetime import datetime, timezone as tz

    if timezone:
        # For demo, just return UTC
        # In production, use pytz or zoneinfo
        now = datetime.now(tz.utc)
        return {
            'timezone': 'UTC',
            'time': now.isoformat(),
            'note': 'Full timezone support requires pytz'
        }
    else:
        now = datetime.now()
        return {
            'timezone': 'local',
            'time': now.isoformat()
        }


async def main():
    """Run the MCP server."""
    print("Starting MCP server with AOP observability...")
    print("Database: demo_server_events.db")
    print("\nAvailable tools:")
    print("  - search_web(query, max_results=5)")
    print("  - calculator(operation, a, b)")
    print("  - get_time(timezone=None)")
    print("\nTo view logs:")
    print("  aop query --agent-id demo-server")
    print("\nTo view dashboard:")
    print("  aop dashboard")
    print("\n" + "="*50 + "\n")

    # Run the stdio server
    await stdio_server(server)


if __name__ == "__main__":
    asyncio.run(main())
