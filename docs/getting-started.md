# Getting Started with AOP

Get up and running with AOP in 5 minutes!

## Installation

### Complete Package Installation

```bash
pip install aop-pack
```

The `aop-pack` package includes all features and dependencies:
- ✅ Core observability library
- ✅ CLI tools
- ✅ Web dashboard
- ✅ OpenTelemetry export
- ✅ Prometheus metrics
- ✅ PostgreSQL support
- ✅ All required dependencies

### From Source

```bash
git clone https://github.com/aop-protocol/aop.git
cd aop
pip install -e .
```

## Quick Start (MCP Example)

### 1. Basic Event Logging

```python
from aop import AOPClient

# Initialize client (uses SQLite by default)
client = AOPClient()

# Log a tool call event
event_id = client.log_event({
    'agent_id': 'my-agent',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'data': {
        'tool_name': 'search',
        'params': {'query': 'AI agents'}
    }
})

print(f"Logged event: {event_id}")

# Query events
events = client.query(agent_id='my-agent', limit=10)
print(f"Found {len(events)} events")

client.close()
```

### 2. Using the Decorator (Recommended)

The decorator automatically captures parameters, results, duration, and errors:

```python
from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(agent_id='my-agent')
def search_tool(query: str, max_results: int = 10):
    """Search for information."""
    # Your tool implementation
    return {'results': ['result1', 'result2']}

# Use the tool normally - observability happens automatically!
result = search_tool(query='AI agents', max_results=5)

# Query the trace
events = client.query(agent_id='my-agent')
print(f"Captured {len(events)} events")  # 2 events: called + completed

client.close()
```

**Before/After Comparison:**

```python
# Without AOP: 7 lines of boilerplate
start = time.time()
try:
    result = search_tool('AI agents')
    log_event('tool.called', {'tool': 'search', 'duration': time.time() - start})
except Exception as e:
    log_event('tool.error', {'tool': 'search', 'error': str(e)})
finally:
    log_event('tool.completed', {'duration': time.time() - start})

# With AOP: 1 line!
@client.mcp.observe_tool(agent_id='my-agent')
def search_tool(query): ...
```

### 3. Distributed Tracing

Link related events with `correlation_id`:

```python
from aop import AOPClient

client = AOPClient()

trace_id = 'user-request-123'

# Parent event
parent_id = client.log_event({
    'agent_id': 'orchestrator',
    'event_type': 'a2a.task.assigned',
    'correlation_id': trace_id,
    'data': {'task': 'process_request'}
})

# Child event
client.log_event({
    'agent_id': 'worker',
    'event_type': 'mcp.tool.called',
    'correlation_id': trace_id,
    'parent_id': parent_id,  # Links to parent
    'data': {'tool_name': 'analyze'}
})

# Reconstruct the trace
from aop import Analytics

analytics = Analytics(client)
trace = analytics.reconstruct_trace(trace_id)

print(f"Trace has {trace['event_count']} events")
print(f"Total duration: {trace['total_duration_ms']}ms")

client.close()
```

## Storage Options

### SQLite (Default)

```python
# File-based
client = AOPClient(storage='sqlite:///my_events.db')

# In-memory (testing only)
client = AOPClient(storage='memory')
```

### PostgreSQL

```python
client = AOPClient(storage='postgresql://user:pass@localhost:5432/aop')
```

## Command-Line Interface

After installing `aop-pack`:

```bash
# Query events
aop query --agent-id my-agent --limit 10

# Visualize a trace
aop trace --correlation-id user-request-123

# View statistics
aop stats --agent-id my-agent

# Launch dashboard
aop dashboard
```

See [CLI Reference](cli.md) for complete documentation.

## Web Dashboard

Start the interactive dashboard:

```bash
# Launch dashboard (all dependencies included)
aop dashboard

# Or from Python
from aop.dashboard import DashboardServer

server = DashboardServer(storage='sqlite:///aop_events.db')
server.start()
```

Access at `http://localhost:8000`

Features:
- **Events Table** - Sortable, filterable table view with live updates
- **Click-to-View** - Click any event for detailed JSON view
- **Smart Sorting** - Sort by date/time, agent, event type, or duration
- **Trace Explorer** - Visualize distributed traces as trees
- **Analytics** - Charts and statistics
- **Real-time** - New events push down smoothly via WebSocket

See [Dashboard Guide](dashboard.md) for details.

## Next Steps

- **[User Guide](user-guide.md)** - Comprehensive guide to all features
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Protocols Guide](protocols.md)** - MCP, A2A, AP2 protocol details
- **[Examples](examples/)** - More code examples

## Need Help?

- **Questions:** [GitHub Discussions](https://github.com/aop-protocol/aop/discussions)
- **Issues:** [GitHub Issues](https://github.com/aop-protocol/aop/issues)
- **Documentation:** [docs.aop-protocol.org](https://docs.aop-protocol.org)
