# User Guide

Complete guide to using AOP for observability in your AI agents.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Event Logging Patterns](#event-logging-patterns)
- [Distributed Tracing](#distributed-tracing)
- [Querying Events](#querying-events)
- [Analytics](#analytics)
- [Protocol Adapters](#protocol-adapters)
- [Storage Backends](#storage-backends)
- [Best Practices](#best-practices)
- [Performance Tuning](#performance-tuning)
- [Error Handling](#error-handling)

---

## Core Concepts

### What is AOP?

**AOP (Agentic Observability Protocol)** is a universal standard for observing AI agent behavior. It provides:

- **Event logging** - Capture every action agents take
- **Distributed tracing** - Track workflows across multiple agents
- **Analytics** - Understand agent behavior patterns
- **Protocol support** - Works with MCP, A2A, AP2 protocols
- **Privacy-first** - All data stays on your infrastructure

### Key Components

#### 1. AOPClient

The main interface for logging and querying events.

```python
from aop import AOPClient

client = AOPClient(storage='sqlite:///aop_events.db')
```

#### 2. Event

An event represents a single action or state change. Each event has:

- **id** - Unique UUID v7 identifier
- **timestamp** - When it occurred
- **agent_id** - Which agent performed the action
- **event_type** - What happened (e.g., `mcp.tool.called`)
- **protocol** - Which protocol (mcp, a2a, ap2)
- **data** - Additional context (params, results, etc.)
- **correlation_id** - Trace identifier for related events
- **parent_id** - Link to parent event

#### 3. Protocol Adapters

Specialized helpers for different protocols:

- **MCPAdapter** - Model Context Protocol (tool calls, LLM sampling)
- **A2AAdapter** - Agent-to-Agent (tasks, messages)
- **AP2Adapter** - Agent Payments (transactions)

#### 4. Analytics

Tools for analyzing collected events:

```python
from aop import Analytics

analytics = Analytics(client)
trace = analytics.reconstruct_trace('trace-123')
```

---

## Event Logging Patterns

AOP provides three ways to log events, from most to least automated.

### Pattern 1: Decorator (Recommended)

**Best for:** MCP tool functions

The decorator automatically captures:
- Function parameters
- Return values
- Execution duration
- Errors and exceptions

```python
from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(agent_id='my-agent')
def search_tool(query: str, max_results: int = 10):
    """Search for information."""
    # Your implementation
    results = perform_search(query, max_results)
    return {'results': results, 'count': len(results)}

# Use normally - observability happens automatically!
result = search_tool(query='AI agents', max_results=5)
```

**Async support:**

```python
@client.mcp.observe_tool(agent_id='my-agent')
async def async_search(query: str):
    """Async search tool."""
    results = await fetch_from_api(query)
    return results

# Works with async/await
result = await async_search('test')
```

**With correlation ID:**

```python
@client.mcp.observe_tool(agent_id='my-agent', correlation_id='trace-123')
def tool_in_trace(param: str):
    """Tool that's part of a larger trace."""
    return process(param)
```

**Control what's captured:**

```python
@client.mcp.observe_tool(
    agent_id='my-agent',
    capture_result=False,  # Don't log return value
    capture_params=False   # Don't log parameters
)
def sensitive_tool(api_key: str):
    """Tool with sensitive data."""
    return call_api(api_key)
```

### Pattern 2: Context Manager

**Best for:** Manual control with automatic cleanup

The context manager tracks execution and handles errors, but you control when to log results.

```python
from aop import AOPClient

client = AOPClient()

with client.mcp.tool_execution(
    agent_id='my-agent',
    tool_name='search',
    params={'query': 'AI', 'limit': 10},
    correlation_id='trace-123'
) as handle:
    # Your tool code
    results = perform_search('AI', limit=10)

    # Optionally set result
    handle.set_result(results)

    # Exceptions are automatically logged
    # Duration is automatically calculated
```

**Error handling:**

```python
with client.mcp.tool_execution('my-agent', 'risky_operation', {}) as handle:
    try:
        result = might_fail()
        handle.set_result(result)
    except ValueError as e:
        # Exception is automatically logged with context
        raise
```

### Pattern 3: Manual Logging

**Best for:** Maximum control, non-tool events

Log events directly for complete control.

```python
from aop import AOPClient

client = AOPClient()

# Log tool call
call_id = client.mcp.log_tool_call(
    agent_id='my-agent',
    tool_name='search',
    params={'query': 'AI'},
    correlation_id='trace-123'
)

# ... perform work ...
results = perform_search('AI')

# Log result
client.mcp.log_tool_result(
    agent_id='my-agent',
    tool_name='search',
    result=results,
    parent_id=call_id,
    correlation_id='trace-123',
    duration_ms=150
)
```

**Log errors:**

```python
try:
    result = risky_operation()
except Exception as e:
    client.mcp.log_tool_error(
        agent_id='my-agent',
        tool_name='risky_operation',
        error_code='OPERATION_FAILED',
        error_message=str(e),
        parent_id=call_id,
        correlation_id='trace-123'
    )
    raise
```

---

## Distributed Tracing

Distributed tracing links related events across multiple agents and tools using **correlation_id**.

### Creating a Trace

```python
from aop import AOPClient
import uuid

client = AOPClient()

# Generate a unique trace ID
trace_id = str(uuid.uuid4())

# All events in this workflow use the same correlation_id
@client.mcp.observe_tool(agent_id='orchestrator', correlation_id=trace_id)
def orchestrate_workflow(request: str):
    # Step 1: Parse request
    parsed = parse_request(request)

    # Step 2: Process data
    result = process_data(parsed)

    return result

@client.mcp.observe_tool(agent_id='orchestrator', correlation_id=trace_id)
def parse_request(request: str):
    return {'task': 'process', 'data': request}

@client.mcp.observe_tool(agent_id='worker', correlation_id=trace_id)
def process_data(data: dict):
    return {'status': 'completed', 'data': data}
```

### Parent-Child Relationships

Use `parent_id` to create explicit hierarchies:

```python
# Parent event
parent_id = client.log_event({
    'agent_id': 'orchestrator',
    'event_type': 'a2a.task.assigned',
    'protocol': 'a2a',
    'correlation_id': trace_id,
    'data': {'task': 'process_request'}
})

# Child event
client.log_event({
    'agent_id': 'worker',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'correlation_id': trace_id,
    'parent_id': parent_id,  # Links to parent
    'data': {'tool_name': 'process'}
})
```

### Reconstructing Traces

```python
from aop import Analytics

analytics = Analytics(client)

# Reconstruct complete trace
trace = analytics.reconstruct_trace(correlation_id=trace_id)

print(f"Events: {trace['event_count']}")
print(f"Duration: {trace['total_duration_ms']}ms")
print(f"Errors: {trace['error_count']}")

# Access root and children
root_event = trace['root_event']
children = trace['children']
```

**Trace structure:**

```python
{
    'correlation_id': 'trace-123',
    'root_event': {
        'id': '...',
        'event_type': 'mcp.tool.called',
        'timestamp': '2025-01-15T10:30:00Z',
        # ... other fields
    },
    'children': [
        {
            'event': {...},
            'children': [...]
        }
    ],
    'total_duration_ms': 1500,
    'event_count': 10,
    'error_count': 0
}
```

---

## Querying Events

### Basic Queries

```python
from aop import AOPClient

client = AOPClient()

# Get last 50 events (default)
events = client.query()

# Filter by agent
events = client.query(agent_id='my-agent')

# Filter by event type
events = client.query(event_type='mcp.tool.called')

# Filter by protocol
events = client.query(protocol='mcp')

# Combine filters
events = client.query(
    agent_id='my-agent',
    event_type='mcp.tool.called',
    limit=100
)
```

### Time-Based Queries

```python
from datetime import datetime, timedelta

# Events from last hour
events = client.query(
    start_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now()
)

# Events from specific date
events = client.query(
    start_time=datetime(2025, 1, 15, 0, 0, 0),
    end_time=datetime(2025, 1, 15, 23, 59, 59)
)
```

### Trace Queries

```python
# Get all events for a trace
events = client.get_trace(correlation_id='trace-123')

# Or use query with correlation_id
events = client.query(correlation_id='trace-123')
```

### Sorting and Ordering

```python
# Most recent first (default)
events = client.query(order_by='timestamp', order_desc=True)

# Oldest first
events = client.query(order_by='timestamp', order_desc=False)

# Sort by different field
events = client.query(order_by='agent_id', order_desc=False)
```

### Pagination

```python
# First page (50 events)
page1 = client.query(limit=50)

# You can implement pagination by tracking timestamps
last_timestamp = page1[-1]['timestamp']
page2 = client.query(
    start_time=last_timestamp,
    limit=50
)
```

---

## Analytics

The `Analytics` class provides powerful analysis capabilities.

### Setup

```python
from aop import AOPClient, Analytics

client = AOPClient()
analytics = Analytics(client)
```

### Tool Usage Analysis

**Count by tool:**

```python
# How many times each tool was called
counts = analytics.count_by_tool(agent_id='my-agent')
# {'search': 150, 'process': 80, 'analyze': 45}

# All agents
counts = analytics.count_by_tool()
```

**Count by event type:**

```python
type_counts = analytics.count_by_event_type(agent_id='my-agent')
# {
#   'mcp.tool.called': 275,
#   'mcp.tool.completed': 270,
#   'mcp.tool.error': 5
# }
```

### Duration Analysis

**Average duration by tool:**

```python
avg_durations = analytics.avg_duration_by_tool(agent_id='my-agent')
# {'search': 125.5, 'process': 45.2, 'analyze': 320.8}

# Tool name is in milliseconds
for tool, avg_ms in avg_durations.items():
    print(f"{tool}: {avg_ms:.1f}ms average")
```

**Percentiles:**

```python
# Get P95 latency for all tools
p95 = analytics.percentile_duration(
    agent_id='my-agent',
    percentile=95.0
)
print(f"P95 latency: {p95:.1f}ms")

# For specific tool
p95_search = analytics.percentile_duration(
    agent_id='my-agent',
    tool_name='search',
    percentile=95.0
)

# Common percentiles
p50 = analytics.percentile_duration('my-agent', percentile=50)  # Median
p95 = analytics.percentile_duration('my-agent', percentile=95)
p99 = analytics.percentile_duration('my-agent', percentile=99)
```

### Time-Series Analysis

**Events over time:**

```python
# Hourly buckets
hourly = analytics.events_over_time(
    agent_id='my-agent',
    bucket_size='1h'
)
# [
#   {'time': '2025-01-15T10:00:00Z', 'count': 45},
#   {'time': '2025-01-15T11:00:00Z', 'count': 62},
#   ...
# ]

# Daily buckets
daily = analytics.events_over_time(bucket_size='1d')

# 5-minute buckets
minutes = analytics.events_over_time(bucket_size='5m')
```

**Event rate:**

```python
# Events per minute in last hour
rate = analytics.event_rate(
    agent_id='my-agent',
    window_minutes=60
)
print(f"Event rate: {rate:.2f} events/min")

# Last 5 minutes
recent_rate = analytics.event_rate('my-agent', window_minutes=5)
```

### Error Analysis

```python
# Get all error events
errors = client.query(event_type='mcp.tool.error')

# Analyze error codes
from collections import Counter
error_codes = Counter(
    e.get('error', {}).get('code', 'UNKNOWN')
    for e in errors
)

# Most common errors
for code, count in error_codes.most_common(5):
    print(f"{code}: {count} occurrences")
```

---

## Protocol Adapters

### MCP (Model Context Protocol)

**Tool execution:**

```python
# Decorator (recommended)
@client.mcp.observe_tool(agent_id='my-agent')
def my_tool(param: str):
    return process(param)

# Context manager
with client.mcp.tool_execution('my-agent', 'search', {'q': 'test'}) as handle:
    result = search('test')
    handle.set_result(result)

# Manual
call_id = client.mcp.log_tool_call('my-agent', 'search', {'q': 'test'})
client.mcp.log_tool_result('my-agent', 'search', result, parent_id=call_id)
```

**LLM sampling:**

```python
# Log prompt
req_id = client.mcp.log_sampling_request(
    agent_id='my-agent',
    model='gpt-4',
    prompt='Explain quantum computing',
    correlation_id='trace-123'
)

# Log completion
client.mcp.log_sampling_response(
    agent_id='my-agent',
    model='gpt-4',
    response='Quantum computing uses...',
    parent_id=req_id,
    correlation_id='trace-123'
)
```

### A2A (Agent-to-Agent)

**Task management:**

```python
# Assign task
client.a2a.log_task_assigned(
    agent_id='orchestrator',
    task_id='task-123',
    assigned_to='worker-agent',
    task_data={'action': 'process', 'input': 'data'},
    correlation_id='trace-123'
)

# Complete task
client.a2a.log_task_completed(
    agent_id='worker-agent',
    task_id='task-123',
    result={'status': 'done', 'output': 'result'},
    correlation_id='trace-123'
)

# Task failed
client.a2a.log_task_failed(
    agent_id='worker-agent',
    task_id='task-123',
    error_code='PROCESSING_ERROR',
    error_message='Failed to process data',
    correlation_id='trace-123'
)
```

**Messaging:**

```python
# Send message
client.a2a.log_message_sent(
    agent_id='agent-1',
    recipient='agent-2',
    message={'type': 'request', 'data': {'query': 'status'}},
    correlation_id='trace-123'
)

# Receive message
client.a2a.log_message_received(
    agent_id='agent-2',
    sender='agent-1',
    message={'type': 'request', 'data': {'query': 'status'}},
    correlation_id='trace-123'
)
```

### AP2 (Agent Payments)

**Payment tracking:**

```python
# Initiate payment
client.ap2.log_payment_initiated(
    agent_id='my-agent',
    payment_id='pay-123',
    amount=10.50,
    currency='USD',
    recipient='service-provider',
    correlation_id='trace-123'
)

# Payment succeeded
client.ap2.log_payment_completed(
    agent_id='my-agent',
    payment_id='pay-123',
    transaction_id='txn-456',
    correlation_id='trace-123'
)

# Payment failed
client.ap2.log_payment_failed(
    agent_id='my-agent',
    payment_id='pay-123',
    error_code='INSUFFICIENT_FUNDS',
    error_message='Not enough balance',
    correlation_id='trace-123'
)
```

---

## Storage Backends

### SQLite (Default)

**File-based:**

```python
client = AOPClient(storage='sqlite:///aop_events.db')
```

**In-memory (testing only):**

```python
client = AOPClient(storage='memory')
```

**Custom path:**

```python
client = AOPClient(storage='sqlite:////absolute/path/to/events.db')
```

### PostgreSQL

```python
client = AOPClient(
    storage='postgresql://user:password@localhost:5432/aop_db'
)
```

**Connection pool:**

```python
from aop.storage import PostgreSQLStorage

storage = PostgreSQLStorage(
    'postgresql://user:password@localhost:5432/aop_db',
    pool_size=10,
    max_overflow=20
)

client = AOPClient(storage=storage)
```

### Custom Storage

Implement the `BaseStorage` interface:

```python
from aop.storage.base import BaseStorage

class CustomStorage(BaseStorage):
    def insert_event(self, event: dict) -> None:
        # Your implementation
        pass

    def query_events(self, filters: dict) -> list:
        # Your implementation
        pass

    def close(self) -> None:
        # Your implementation
        pass
```

---

## Best Practices

### 1. Use Decorators for Tools

Decorators reduce boilerplate from 7 lines to 1 line:

```python
# Good: 1 line
@client.mcp.observe_tool(agent_id='my-agent')
def search(query: str):
    return perform_search(query)

# Avoid: 7 lines
def search(query: str):
    call_id = client.mcp.log_tool_call('my-agent', 'search', {'query': query})
    try:
        result = perform_search(query)
        client.mcp.log_tool_result('my-agent', 'search', result, parent_id=call_id)
        return result
    except Exception as e:
        client.mcp.log_tool_error('my-agent', 'search', str(e), parent_id=call_id)
        raise
```

### 2. Always Use Correlation IDs for Workflows

```python
trace_id = generate_trace_id()

@client.mcp.observe_tool(agent_id='my-agent', correlation_id=trace_id)
def step1():
    pass

@client.mcp.observe_tool(agent_id='my-agent', correlation_id=trace_id)
def step2():
    pass
```

### 3. Don't Log Sensitive Data

```python
# Good: Exclude sensitive params
@client.mcp.observe_tool(
    agent_id='my-agent',
    capture_params=False  # Don't log API keys
)
def call_api(api_key: str, data: dict):
    return api.call(api_key, data)

# Or manually filter
params = {'query': 'test', 'api_key': '***'}  # Redact sensitive fields
client.mcp.log_tool_call('my-agent', 'search', params)
```

### 4. Close Connections

```python
# Good: Use context manager
from contextlib import closing

with closing(AOPClient()) as client:
    client.log_event({...})

# Or explicit close
client = AOPClient()
try:
    client.log_event({...})
finally:
    client.close()
```

### 5. Batch Queries When Possible

```python
# Good: Single query with filters
events = client.query(agent_id='my-agent', limit=1000)

# Avoid: Multiple small queries
for event_type in ['mcp.tool.called', 'mcp.tool.completed']:
    events = client.query(event_type=event_type)  # Inefficient
```

### 6. Use Appropriate Storage

- **Development**: SQLite in-memory (`memory`)
- **Testing**: SQLite file (`sqlite:///test.db`)
- **Production**: PostgreSQL for high volume
- **Local tools**: SQLite file

### 7. Set Instance IDs for Multi-Instance Deployments

```python
import socket

instance_id = socket.gethostname()  # Or use container ID
client = AOPClient(instance_id=instance_id)
```

### 8. Monitor Performance

```python
from aop import Analytics

analytics = Analytics(client)

# Check slow tools
avg_durations = analytics.avg_duration_by_tool('my-agent')
slow_tools = {k: v for k, v in avg_durations.items() if v > 1000}

if slow_tools:
    print(f"Slow tools (>1s): {slow_tools}")
```

---

## Performance Tuning

### Client Performance

AOP is designed for <1ms P99 overhead. Tips:

**1. Use appropriate validation:**

```python
# Skip validation in production if events are pre-validated
client.log_event(event, validate=False)

# Let auto_build fill required fields
client.log_event(event, auto_build=True)
```

**2. Batch inserts (when available):**

```python
# Some storage backends support batching
events = [event1, event2, event3]
for event in events:
    client.log_event(event)
```

**3. Use connection pooling for PostgreSQL:**

```python
from aop.storage import PostgreSQLStorage

storage = PostgreSQLStorage(
    connection_string,
    pool_size=20,  # Adjust based on load
    max_overflow=40
)
```

### Query Optimization

**1. Add time filters:**

```python
# Good: Limit time range
events = client.query(
    agent_id='my-agent',
    start_time=datetime.now() - timedelta(hours=1)
)

# Avoid: Query all time
events = client.query(agent_id='my-agent', limit=10000)
```

**2. Use appropriate limits:**

```python
# For display: Small limit
recent = client.query(limit=50)

# For analysis: Larger limit or no limit
all_events = client.query(limit=100000)
```

**3. Index important fields (PostgreSQL):**

```sql
CREATE INDEX idx_agent_timestamp ON events(agent_id, timestamp);
CREATE INDEX idx_correlation ON events(correlation_id);
CREATE INDEX idx_event_type ON events(event_type);
```

---

## Error Handling

### Handling Storage Errors

```python
from aop import AOPClient
from aop.exceptions import StorageError

client = AOPClient()

try:
    events = client.query(agent_id='my-agent')
except StorageError as e:
    print(f"Storage error: {e}")
    # Fallback logic
```

### Handling Validation Errors

```python
from aop.exceptions import ValidationError

try:
    client.log_event({
        'agent_id': 'my-agent',
        # Missing required fields
    })
except ValidationError as e:
    print(f"Invalid event: {e}")
```

### Graceful Degradation

```python
def log_with_fallback(event):
    """Log event with fallback to local file on failure."""
    try:
        client.log_event(event)
    except Exception as e:
        # Fallback: Write to local file
        import json
        with open('failed_events.jsonl', 'a') as f:
            f.write(json.dumps(event) + '\n')
        print(f"Failed to log event, wrote to file: {e}")
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def log_event_with_retry(event):
    client.log_event(event)
```

---

## Next Steps

- **[API Reference](api-reference.md)** - Complete API documentation
- **[Protocols Guide](protocols.md)** - Protocol-specific details
- **[CLI Reference](cli.md)** - Command-line tools
- **[Dashboard Guide](dashboard.md)** - Web interface
- **[Integrations](integrations.md)** - OpenTelemetry, Prometheus
- **[Examples](examples/)** - More code examples
