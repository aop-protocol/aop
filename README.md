# AOP (Agentic Observability Protocol)

> **Universal observability standard for AI agents** - A "black box recorder" for agentic systems.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-green.svg)](https://github.com/aop-protocol/aop)

---

## What is AOP?

AOP is a **universal observability protocol for AI agents** that works across MCP, A2A, and AP2 protocols. It provides complete visibility into agent behavior with minimal code and zero performance impact.

**Key Features:**

- 🔒 **Privacy-First** - Local storage by default, you own your data
- ⚡ **Fast** - <1ms P99 overhead, production-ready performance
- 🌍 **Protocol-Agnostic** - Works with MCP, A2A, AP2 out of the box
- 📊 **Powerful Analytics** - Trace reconstruction, aggregations, time-series analysis
- 🎯 **Simple API** - 1-line decorator reduces code by 86%
- 🔓 **Open Source** - MIT licensed, community-driven

---

## Quick Start

### Installation

```bash
# Core library
pip install aop

# With optional features
pip install aop[cli]            # Command-line tools
pip install aop[dashboard]      # Web dashboard
pip install aop[otel]          # OpenTelemetry export
pip install aop[prometheus]    # Prometheus metrics

# Everything
pip install aop[cli,dashboard,otel,prometheus]
```

### Basic Usage (Decorator Pattern)

The decorator is the simplest way to add observability:

```python
from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(agent_id='my-agent')
def search(query: str, max_results: int = 10):
    """Search for information."""
    results = perform_search(query, max_results)
    return {'results': results, 'count': len(results)}

# Use normally - everything is logged automatically!
result = search(query='AI agents', max_results=5)
```

**What gets logged automatically:**
- ✅ Function parameters
- ✅ Return values
- ✅ Execution duration
- ✅ Errors and exceptions
- ✅ Parent-child relationships

### Code Comparison

**Without AOP (7 lines per tool):**
```python
start = time.time()
try:
    result = search_tool('AI agents')
    log_event('tool.called', {'duration': time.time() - start})
except Exception as e:
    log_event('tool.error', {'error': str(e)})
finally:
    log_event('tool.completed', {'duration': time.time() - start})
```

**With AOP (1 line):**
```python
@client.mcp.observe_tool(agent_id='my-agent')
def search_tool(query: str):
    return perform_search(query)
```

**86% less code!**

---

## Core Features

### 1. Event Logging

```python
from aop import AOPClient

client = AOPClient()

# Decorator (recommended)
@client.mcp.observe_tool(agent_id='my-agent')
def my_tool(param: str):
    return process(param)

# Context manager
with client.mcp.tool_execution('my-agent', 'search', {'q': 'test'}) as handle:
    result = search('test')
    handle.set_result(result)

# Manual
client.log_event({
    'agent_id': 'my-agent',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'data': {'tool_name': 'search'}
})
```

### 2. Querying Events

```python
# Get recent events
events = client.query(agent_id='my-agent', limit=50)

# Filter by event type
tool_calls = client.query(
    agent_id='my-agent',
    event_type='mcp.tool.called'
)

# Time range queries
from datetime import datetime, timedelta
recent = client.query(
    agent_id='my-agent',
    start_time=datetime.now() - timedelta(hours=1)
)

# Get complete trace
trace_events = client.get_trace(correlation_id='trace-123')
```

### 3. Analytics & Insights

```python
from aop import Analytics

analytics = Analytics(client)

# Reconstruct distributed traces
trace = analytics.reconstruct_trace(correlation_id='trace-123')
print(f"Duration: {trace['total_duration_ms']}ms")
print(f"Events: {trace['event_count']}")

# Tool usage analytics
tool_counts = analytics.count_by_tool('my-agent')
avg_durations = analytics.avg_duration_by_tool('my-agent')

# Latency percentiles
p95 = analytics.percentile_duration('my-agent', percentile=95)
p99 = analytics.percentile_duration('my-agent', percentile=99)

# Time-series analysis
timeline = analytics.events_over_time('my-agent', bucket_size='1h')
rate = analytics.event_rate('my-agent', window_minutes=60)
```

### 4. Command-Line Interface

```bash
# Query events
aop query --agent-id my-agent --last 1h

# Visualize traces
aop trace --correlation-id trace-123

# View analytics
aop stats --agent-id my-agent --window 24h

# Export data
aop export --output events.json --last 7d
aop export --output events.toon --format toon  # TOON format (30-60% fewer tokens)

# Start Prometheus exporter
aop prometheus --port 9090

# Launch web dashboard
aop dashboard
```

### 5. Web Dashboard

Launch a professional web interface for real-time monitoring:

```bash
pip install aop[dashboard]
aop dashboard
```

**Features:**
- **Tabular Event View** - Clean table with sortable columns (timestamp, agent, type, duration)
- **Live Updates** - New events smoothly push down existing ones via WebSocket
- **Click-to-View** - Click any event row to see full details in side panel
- **Smart Sorting** - Sort by date/time, agent (A-Z), event type, or duration
- **Color-Coded Status** - Visual indicators (🟢 success, 🔴 error, 🔵 in-progress)
- **Trace Visualization** - Interactive tree view of distributed traces
- **Analytics Charts** - Real-time performance metrics and statistics
- **Filtering** - Filter by agent, event type, protocol, time range

Access at `http://localhost:8000`

### 6. Exporters

#### OpenTelemetry

```python
from aop.exporters import OpenTelemetryExporter

exporter = OpenTelemetryExporter(client)
events = client.query(correlation_id='trace-123')
spans = exporter.export_events(events)

exporter.export_to_collector(
    spans=spans,
    endpoint='http://localhost:4317'
)
```

#### Prometheus

```bash
# Start metrics server
aop prometheus --port 9090

# Metrics available at http://localhost:9090/metrics
```

**Metrics exposed:**
- `aop_events_total` - Total events (by type, agent, protocol)
- `aop_tool_duration_seconds` - Tool duration histogram
- `aop_tool_errors_total` - Tool error counter
- `aop_event_rate` - Events per minute gauge

#### TOON (Token-Oriented Object Notation)

**LLM-optimized export format with 30-60% token reduction** - Perfect for AI-assisted debugging and trace analysis.

```python
from aop.exporters import ToonExporter

# Basic export
exporter = ToonExporter(flatten=True, delimiter='comma')
events = client.query(correlation_id='trace-123', limit=100)
toon_output = exporter.export(events)

# Export to file
exporter.export_to_file(events, 'trace.toon')

# Check token savings
stats = exporter.get_token_estimate(events)
print(f"Token savings: {stats['savings_percent']}%")
# Output: Token savings: 45.2%
```

**CLI Export:**
```bash
# Export to TOON format
aop export --output events.toon --format toon

# Export with options
aop export -o trace.toon -f toon --toon-delimiter pipe --correlation-id abc123

# Export recent events
aop export -o recent.toon -f toon --last 1h --limit 100
```

**Why TOON?**
- 📉 **30-60% fewer tokens** than JSON for uniform event arrays
- 💰 **Lower LLM costs** when analyzing traces in prompts
- 🎯 **Optimized for AI** consumption and debugging
- 📊 **Tabular format** for uniform data (similar to CSV)

**Use Cases:**
- AI-assisted debugging ("analyze this trace and find bottlenecks")
- Cost-effective trace analysis with GPT-4/Claude
- Passing large event datasets in LLM prompts
- Automated performance analysis

---

## Protocol Support

### MCP (Model Context Protocol)

```python
# Tool execution (decorator)
@client.mcp.observe_tool(agent_id='my-agent')
def my_tool(param: str):
    return process(param)

# LLM sampling
req_id = client.mcp.log_sampling_request(
    agent_id='my-agent',
    model='gpt-4',
    prompt='Explain AI'
)

client.mcp.log_sampling_response(
    agent_id='my-agent',
    model='gpt-4',
    response='AI is...',
    parent_id=req_id
)
```

### A2A (Agent-to-Agent Protocol)

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

# Messaging
client.a2a.log_message_sent(
    agent_id='agent-1',
    recipient='agent-2',
    message={'type': 'request', 'data': {...}}
)
```

### AP2 (Agent Payments Protocol)

```python
# Payment tracking
client.ap2.log_payment_initiated(
    agent_id='my-agent',
    payment_id='pay-123',
    amount=10.50,
    currency='USD',
    recipient='service-provider'
)

client.ap2.log_payment_completed(
    agent_id='my-agent',
    payment_id='pay-123',
    transaction_id='txn-456'
)

# Cost tracking
client.ap2.log_cost_incurred(
    agent_id='my-agent',
    cost_amount=0.15,
    currency='USD',
    resource_type='llm_api'
)
```

---

## Storage Backends

### SQLite (Default)

```python
# File-based
client = AOPClient(storage='sqlite:///aop_events.db')

# In-memory (testing)
client = AOPClient(storage='memory')
```

### PostgreSQL

```python
client = AOPClient(
    storage='postgresql://user:password@localhost:5432/aop_db'
)
```

### Custom Storage

Implement the `BaseStorage` interface for custom backends.

---

## Distributed Tracing

Link related events across agents using `correlation_id`:

```python
import uuid

trace_id = str(uuid.uuid4())

# All events use the same correlation_id
@client.mcp.observe_tool(agent_id='orchestrator', correlation_id=trace_id)
def step1():
    return process_step1()

@client.mcp.observe_tool(agent_id='worker', correlation_id=trace_id)
def step2(data):
    return process_step2(data)

# Execute workflow
result1 = step1()
result2 = step2(result1)

# Reconstruct complete trace
trace = analytics.reconstruct_trace(correlation_id=trace_id)
```

---

## Integrations

### LangChain

```python
from langchain.tools import Tool

@client.mcp.observe_tool(agent_id='langchain-agent')
def search_tool(query: str) -> str:
    return perform_search(query)

lc_tool = Tool(
    name="Search",
    func=search_tool,
    description="Search for information"
)

# All tool calls are now logged to AOP
```

### OpenTelemetry

```bash
aop export-otel --correlation-id trace-123 --endpoint http://localhost:4317
```

### Prometheus + Grafana

```bash
# Start Prometheus exporter
aop prometheus --port 9090

# Add to prometheus.yml
scrape_configs:
  - job_name: 'aop'
    static_configs:
      - targets: ['localhost:9090']
```

View metrics in Grafana with pre-built dashboards.

---

## Documentation

### Getting Started
- **[Installation & Quick Start](docs/getting-started.md)** - Get up and running in 5 minutes
- **[User Guide](docs/user-guide.md)** - Comprehensive usage guide
- **[Examples](docs/examples/)** - Code examples and tutorials

### Reference
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[CLI Reference](docs/cli.md)** - Command-line tools
- **[Event Schema Specification](docs/specification/event-schema-v1.0.md)** - Event schema details

### Advanced
- **[Protocol Guide](docs/protocols.md)** - MCP, A2A, AP2 protocols in depth
- **[Dashboard Guide](docs/dashboard.md)** - Web dashboard usage
- **[Integrations](docs/integrations.md)** - OpenTelemetry, Prometheus, frameworks
- **[Architecture](docs/architecture.md)** - System design and internals
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

---

## Examples

Complete working examples in the [`examples/`](examples/) directory:

- **[decorator_demo.py](examples/decorator_demo.py)** - Decorator usage with async/sync tools
- **[analytics_demo.py](examples/analytics_demo.py)** - Analytics and trace reconstruction
- **[More examples](docs/examples/)** - Additional patterns and use cases

Run examples:

```bash
python examples/decorator_demo.py
python examples/analytics_demo.py
```

---

## Performance

AOP is designed for production use with minimal overhead:

- **<1ms P99 latency** - Won't slow down your agents
- **Zero runtime dependencies** - Core library has no deps
- **Async support** - Non-blocking logging
- **Connection pooling** - Efficient database usage
- **Optional validation** - Skip in production for speed

**Benchmarks** (local SQLite):
- Insert event: 0.3ms median, 0.8ms P99
- Query 100 events: 2.5ms median

---

## Design Principles

1. **Privacy-First** - Local storage by default, no telemetry, you own your data
2. **Zero Dependencies** - Core library uses only Python stdlib
3. **Protocol-Agnostic** - Not tied to any specific agent protocol
4. **Storage-Flexible** - Pluggable backends (SQLite, PostgreSQL, custom)
5. **Minimal Overhead** - <1ms P99, production-ready performance
6. **Developer-Friendly** - Simple API, decorator pattern, type hints

---

## Roadmap

See [RoadMap.md](RoadMap.md) for detailed development plan.

**v0.1.0-alpha** (Current)
- ✅ Core event logging and querying
- ✅ Protocol adapters (MCP, A2A, AP2)
- ✅ Analytics engine
- ✅ CLI tools
- ✅ Web dashboard
- ✅ OpenTelemetry and Prometheus exporters

**v0.2.0** (Planned)
- Batch insert optimization
- Stream processing API
- Additional storage backends
- Enhanced dashboard features
- Performance improvements

---

## Contributing

AOP is open source and community-driven. Contributions are welcome!

**Ways to contribute:**
- Report bugs and request features via [GitHub Issues](https://github.com/aop-protocol/aop/issues)
- Submit pull requests
- Improve documentation
- Share examples and use cases

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Community

- **Questions:** [GitHub Discussions](https://github.com/aop-protocol/aop/discussions)
- **Issues:** [GitHub Issues](https://github.com/aop-protocol/aop/issues)
- **Documentation:** [docs.aop-protocol.org](https://docs.aop-protocol.org)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Citation

If you use AOP in your research or project, please cite:

```bibtex
@software{aop2025,
  title = {AOP: Agentic Observability Protocol},
  author = {AOP Contributors},
  year = {2025},
  url = {https://github.com/aop-protocol/aop},
  version = {0.1.0-alpha}
}
```

---

**Built with ❤️ by the AOP community**
