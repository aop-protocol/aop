# API Reference

Complete API documentation for AOP.

## Core Client

### AOPClient

Main client for logging and querying events.

```python
from aop import AOPClient

client = AOPClient(
    storage: str = "sqlite:///aop_events.db",
    instance_id: Optional[str] = None
)
```

**Parameters:**
- `storage` (str): Storage connection string
  - SQLite: `"sqlite:///path/to/file.db"`
  - PostgreSQL: `"postgresql://user:pass@host:port/db"`
  - Memory: `"memory"`
- `instance_id` (str, optional): Unique instance identifier (auto-generated if not provided)

#### Methods

##### log_event()

Log a single event.

```python
event_id = client.log_event(
    event: Union[Dict[str, Any], AOPEvent],
    validate: bool = True,
    auto_build: bool = True
) -> str
```

**Parameters:**
- `event`: Event dictionary or AOPEvent object
- `validate`: Whether to validate event schema (default: True)
- `auto_build`: Auto-fill missing fields like id, timestamp (default: True)

**Returns:** Event ID (UUID v7)

**Example:**
```python
event_id = client.log_event({
    'agent_id': 'my-agent',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'data': {'tool_name': 'search', 'params': {'q': 'test'}}
})
```

##### query()

Query events with filters.

```python
events = client.query(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    protocol: Optional[str] = None,
    correlation_id: Optional[str] = None,
    severity: Optional[str] = None,
    start_time: Optional[Union[str, datetime]] = None,
    end_time: Optional[Union[str, datetime]] = None,
    limit: int = 100,
    order_by: str = 'timestamp',
    order_desc: bool = True
) -> List[Dict[str, Any]]
```

**Returns:** List of event dictionaries

**Example:**
```python
# Get last 10 events for agent
events = client.query(agent_id='my-agent', limit=10)

# Get events in time range
from datetime import datetime, timedelta
events = client.query(
    start_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now()
)
```

##### get_trace()

Get all events for a trace.

```python
events = client.get_trace(correlation_id: str) -> List[Dict[str, Any]]
```

##### close()

Close storage connection.

```python
client.close()
```

---

## Protocol Adapters

### MCPAdapter

Model Context Protocol adapter.

```python
from aop import AOPClient

client = AOPClient()
mcp = client.mcp
```

#### Methods

##### observe_tool() (Decorator)

Automatically observe tool calls (sync and async).

```python
@client.mcp.observe_tool(
    agent_id: str,
    correlation_id: Optional[str] = None,
    capture_result: bool = True,
    capture_params: bool = True
)
def my_tool(arg1, arg2):
    ...
```

**Parameters:**
- `agent_id`: Agent identifier
- `correlation_id`: Trace correlation ID
- `capture_result`: Capture function return value (default: True)
- `capture_params`: Capture function parameters (default: True)

**Example:**
```python
@client.mcp.observe_tool(agent_id='my-agent')
def search(query: str, max_results: int = 10):
    return {'results': [...]}

# Async version
@client.mcp.observe_tool(agent_id='my-agent')
async def async_search(query: str):
    return await fetch_results(query)
```

##### tool_execution() (Context Manager)

Manual tool execution tracking.

```python
with client.mcp.tool_execution(
    agent_id: str,
    tool_name: str,
    params: Dict[str, Any],
    correlation_id: Optional[str] = None
) -> EventHandle:
    # Your tool code
    result = do_work()
```

**Example:**
```python
with client.mcp.tool_execution(
    agent_id='my-agent',
    tool_name='search',
    params={'query': 'AI'}
) as handle:
    results = perform_search('AI')
    handle.set_result(results)
```

##### log_tool_call() / log_tool_result() / log_tool_error()

Manual event logging.

```python
# Log tool call
call_id = client.mcp.log_tool_call(
    agent_id='my-agent',
    tool_name='search',
    params={'query': 'AI'},
    correlation_id='trace-123'
)

# Log result
client.mcp.log_tool_result(
    agent_id='my-agent',
    tool_name='search',
    result={'count': 10},
    parent_id=call_id,
    correlation_id='trace-123'
)

# Log error
client.mcp.log_tool_error(
    agent_id='my-agent',
    tool_name='search',
    error_code='TIMEOUT',
    error_message='Request timed out',
    parent_id=call_id,
    correlation_id='trace-123'
)
```

##### log_sampling_request() / log_sampling_response()

Track LLM sampling (prompts/completions).

```python
req_id = client.mcp.log_sampling_request(
    agent_id='my-agent',
    model='gpt-4',
    prompt='Explain AI',
    correlation_id='trace-123'
)

client.mcp.log_sampling_response(
    agent_id='my-agent',
    model='gpt-4',
    response='AI is...',
    parent_id=req_id,
    correlation_id='trace-123'
)
```

---

### A2AAdapter

Agent-to-Agent Protocol adapter.

```python
a2a = client.a2a
```

#### Methods

```python
# Task assignment
client.a2a.log_task_assigned(
    agent_id='orchestrator',
    task_id='task-123',
    assigned_to='worker-agent',
    task_data={'action': 'process'}
)

# Task completion
client.a2a.log_task_completed(
    agent_id='worker-agent',
    task_id='task-123',
    result={'status': 'done'}
)

# Message sent
client.a2a.log_message_sent(
    agent_id='agent-1',
    recipient='agent-2',
    message={'type': 'request', 'data': {...}}
)

# Message received
client.a2a.log_message_received(
    agent_id='agent-2',
    sender='agent-1',
    message={'type': 'request', 'data': {...}}
)
```

---

### AP2Adapter

Agent Payments Protocol adapter.

```python
ap2 = client.ap2
```

#### Methods

```python
# Payment initiated
client.ap2.log_payment_initiated(
    agent_id='my-agent',
    payment_id='pay-123',
    amount=10.50,
    currency='USD',
    recipient='service-provider'
)

# Payment completed
client.ap2.log_payment_completed(
    agent_id='my-agent',
    payment_id='pay-123',
    transaction_id='txn-456'
)

# Payment failed
client.ap2.log_payment_failed(
    agent_id='my-agent',
    payment_id='pay-123',
    error_code='INSUFFICIENT_FUNDS',
    error_message='Not enough balance'
)
```

---

## Analytics

### Analytics

Analytics and trace reconstruction.

```python
from aop import Analytics

analytics = Analytics(client: AOPClient)
```

#### Methods

##### reconstruct_trace()

Reconstruct a distributed trace.

```python
trace = analytics.reconstruct_trace(correlation_id: str) -> Dict[str, Any]
```

**Returns:**
```python
{
    'correlation_id': 'trace-123',
    'root_event': {...},
    'children': [{...}, ...],
    'total_duration_ms': 1500,
    'event_count': 10,
    'error_count': 0
}
```

##### count_by_tool()

Count events by tool.

```python
counts = analytics.count_by_tool(
    agent_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> Dict[str, int]
```

**Returns:** `{'tool_name': count, ...}`

##### avg_duration_by_tool()

Average duration by tool.

```python
durations = analytics.avg_duration_by_tool(
    agent_id: Optional[str] = None
) -> Dict[str, float]
```

**Returns:** `{'tool_name': avg_ms, ...}`

##### percentile_duration()

Calculate duration percentiles.

```python
p95 = analytics.percentile_duration(
    percentile: float = 95.0,
    event_type: Optional[str] = None
) -> float
```

##### events_over_time()

Time-series event counts.

```python
timeseries = analytics.events_over_time(
    bucket: str = 'hour',  # 'hour', 'day', 'week'
    agent_id: Optional[str] = None
) -> Dict[str, int]
```

**Returns:** `{'2025-01-01T00:00:00Z': 50, ...}`

##### event_rate()

Calculate events per minute.

```python
rate = analytics.event_rate(
    agent_id: Optional[str] = None,
    time_window_minutes: int = 60
) -> float
```

---

## Exporters

### OpenTelemetryExporter

Export events to OpenTelemetry format.

```python
from aop.exporters import OpenTelemetryExporter

exporter = OpenTelemetryExporter(
    client: AOPClient,
    service_name: str = 'aop-agent',
    resource_attributes: Optional[Dict[str, str]] = None
)

# Export events to OTEL spans
spans = exporter.export_events(events)

# Export to collector
exporter.export_to_collector(
    events=events,
    endpoint='http://localhost:4317'
)
```

### PrometheusExporter

Export metrics to Prometheus.

```python
from aop.exporters import PrometheusExporterServer

server = PrometheusExporterServer(
    storage='sqlite:///aop_events.db',
    port=9090,
    poll_interval=30.0
)

server.start()
# Metrics available at http://localhost:9090/metrics
```

**Metrics Exposed:**
- `aop_events_total` - Total events (by type, agent, protocol)
- `aop_tool_duration_seconds` - Tool duration histogram
- `aop_tool_errors_total` - Tool errors counter
- `aop_event_rate` - Events per minute gauge

### JSONExporter / CSVExporter

```python
from aop.exporters import JSONExporter, CSVExporter

# JSON export
json_exporter = JSONExporter(client)
json_data = json_exporter.export(events)

# CSV export
csv_exporter = CSVExporter(client)
csv_data = csv_exporter.export(events)
```

---

## Storage Backends

### SQLiteStorage

```python
from aop.storage import SQLiteStorage

storage = SQLiteStorage('sqlite:///aop_events.db')
```

### PostgreSQLStorage

```python
from aop.storage import PostgreSQLStorage

storage = PostgreSQLStorage(
    'postgresql://user:pass@localhost:5432/aop'
)
```

### InMemoryStorage

```python
from aop.storage import InMemoryStorage

storage = InMemoryStorage()  # For testing only
```

---

## Event Schema

### AOPEvent

```python
from aop.types import AOPEvent

event = {
    # Required fields
    'id': 'UUID v7',
    'version': '1.0',
    'timestamp': 'ISO 8601 timestamp',
    'agent_id': 'string',
    'instance_id': 'UUID v7',
    'protocol': 'mcp | a2a | ap2',
    'event_type': 'protocol.category.action',

    # Optional fields
    'correlation_id': 'trace identifier',
    'parent_id': 'parent event ID',
    'severity': 'error | warn | info | debug',
    'duration_ms': 150,
    'data': {},
    'metadata': {},
    'error': {
        'code': 'ERROR_CODE',
        'message': 'Error message',
        'details': {}
    }
}
```

---

## Type Hints

```python
from aop.types import (
    AOPEvent,
    EventType,
    Protocol,
    Severity,
    ErrorInfo,
    ToolParams,
    ToolResult
)
```

See [Event Schema Specification](specification/event-schema-v1.0.md) for complete details.
