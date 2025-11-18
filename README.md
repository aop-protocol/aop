# AOP (Agentic Observability Protocol)

> **Universal AI Agent Observability** - Works with MCP, LangChain, CrewAI, or custom agents. Also supports A2A and AP2 protocols.

**A "black box recorder" for agentic systems** - Track, debug, and optimize agent behavior across any framework.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-green.svg)](https://github.com/aop-protocol/aop)

---

## Why AOP?

**The Problem:** When your AI agent fails, you have **NO idea why**.

- Which tool failed?
- What parameters caused the issue?
- How long did each step take?
- What was the full execution trace?

**Before AOP:**
```
❌ Agent failed (no context, no logs, no trace)
```

**After AOP:**
```bash
$ aop trace --correlation-id abc123

Execution Trace (850ms total):
  ├─ tool.called: search_web (120ms)
  │   └─ tool.completed ✓
  ├─ tool.called: parse_results (45ms)
  │   └─ tool.completed ✓
  └─ tool.called: generate_summary (685ms) ← SLOW!
      └─ tool.error: RateLimitError ❌

✅ Now you know: Rate limit on the summary API!
```

**AOP is like a flight recorder for AI agents** - complete visibility into what happened, when, and why.

---

## Use Cases

### 🐛 Debugging Agent Failures
**Problem:** Agent crashes in production, you don't know why.
**Solution:** Click the error event → "View Full Trace" → see entire execution chain

### 💸 Cost Optimization
**Problem:** Agent costs are exploding, unclear which tools/prompts are expensive.
**Solution:** Analytics tab shows: most-called tools, slowest operations, cost per workflow

### 🔍 Production Monitoring
**Problem:** Need to monitor agent health, response times, error rates.
**Solution:** Export to Prometheus, set up Grafana dashboards, get alerts

### 🏢 Compliance & Auditing
**Problem:** Enterprise needs audit trail of all agent actions.
**Solution:** PostgreSQL backend, queryable event log, exportable to compliance systems

### 👥 Multi-Agent Orchestration
**Problem:** Multiple agents coordinate on tasks, hard to track who did what.
**Solution:** Correlation IDs group related events, trace explorer shows agent interactions

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

## 5-Minute Quick Start

### Step 1: Install AOP

```bash
pip install aop[cli]
```

### Step 2: Add to Your MCP Server

```python
# your_mcp_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from aop import AOPClient
import asyncio

# Initialize AOP (creates local database automatically)
aop = AOPClient()

# Create MCP server
server = Server("my-server")

# Decorate your MCP tools with AOP
@server.call_tool()
@aop.mcp.observe_tool(agent_id='my-server')
async def search_web(query: str) -> dict:
    """Search the web for information."""
    # Your actual search implementation
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://api.duckduckgo.com/?q={query}&format=json')
        return response.json()

# Run the server
if __name__ == "__main__":
    asyncio.run(stdio_server(server))
```

⚠️ **IMPORTANT: Decorator Order Matters!**

```python
# ✅ CORRECT: MCP decorator FIRST, then AOP
@server.call_tool()
@aop.mcp.observe_tool(agent_id='my-server')
async def my_tool():
    ...

# ❌ WRONG: AOP first breaks MCP registration
@aop.mcp.observe_tool(agent_id='my-server')
@server.call_tool()
async def my_tool():
    ...
```

### Step 3: Use Your Tool Through an LLM

**Option A: Claude Desktop**

Add to your Claude Desktop MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/your_mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop, then in chat:
```
"Search the web for AI agent observability tools"
```

When Claude calls your `search_web` tool, **AOP automatically logs it!** ✨

**Option B: Any MCP Client**

```python
from mcp import ClientSession

async with ClientSession() as session:
    # When this runs, AOP captures it
    result = await session.call_tool("search_web", {"query": "AI agents"})
```

### Step 4: Verify AOP Captured It

```bash
# Query events
$ aop query --agent-id my-server --last 1h

┌────────────────────┬──────────────┬──────────┬──────────┬───────────┐
│ Timestamp          │ Agent        │ Tool     │ Duration │ Status    │
├────────────────────┼──────────────┼──────────┼──────────┼───────────┤
│ 2025-01-15 10:30   │ my-server    │ search   │ 145ms    │ ✓ Success │
└────────────────────┴──────────────┴──────────┴──────────┴───────────┘
```

### Step 5: View Live Dashboard

```bash
$ aop dashboard
# Open http://localhost:8000

# Watch live as Claude uses your tools!
```

**That's it!** All your MCP tools now have complete observability.

---

## Installation

```bash
# Core library (zero dependencies)
pip install aop

# With optional features
pip install aop[cli]            # Command-line tools
pip install aop[dashboard]      # Web dashboard
pip install aop[otel]          # OpenTelemetry export
pip install aop[prometheus]    # Prometheus metrics

# Everything
pip install aop[cli,dashboard,otel,prometheus]
```

---

## Framework Support

### ✅ Ready Now
- **MCP (Model Context Protocol)** - First-class support with `@observe_tool` decorator
- **Standalone Python tools** - Decorator-based observability for any function
- **FastMCP** - Works out of box with FastMCP servers
- **Official MCP SDK** - Full support for mcp.server

### 🚧 Coming Soon
- **LangChain** - Callback handler integration (basic support via decorators available now)
- **CrewAI** - Tool wrapper for CrewAI agents
- **AutoGPT** - Plugin support for AutoGPT
- **Semantic Kernel** - Middleware integration

### 💡 Custom Frameworks
Works with **any** agent framework - just log events manually:
```python
client.log_event({
    'agent_id': 'my-agent',
    'event_type': 'custom.tool.call',
    'protocol': 'custom',
    'data': {'tool': 'my-tool', 'params': {...}}
})
```

---

## Why AOP vs Alternatives?

| Feature | AOP | LangSmith | Helicone | Custom Logging |
|---------|-----|-----------|----------|----------------|
| **Setup time** | 1 minute | Account signup | Proxy setup | Days of dev |
| **Pricing** | Free | $99+/mo | Pay per request | Dev time cost |
| **Data location** | Your machine | Cloud | Cloud | Your choice |
| **Framework support** | Any | LangChain-first | LLM proxy only | Manual |
| **Dashboard** | Included | Cloud UI | Cloud UI | Build yourself |
| **Trace search** | Event ID/Correlation/Parent | Correlation only | Session only | Manual queries |
| **Export formats** | JSON/CSV/TOON/OTEL/Prometheus | Limited | Limited | Custom |
| **Privacy** | 100% local | Cloud-based | Cloud-based | Your choice |

**Choose AOP if:**
- Privacy/compliance requires local data
- Multi-framework setup (MCP + LangChain + custom)
- Don't want monthly subscription
- Need self-hosted solution
- Want full control over your observability data

**Choose alternatives if:**
- Want managed cloud service
- Only use LangChain
- Need enterprise support contracts
- Prefer SaaS over self-hosted

---

## Integrating with MCP Servers

### Using FastMCP

```python
from fastmcp import FastMCP
from aop import AOPClient

# Initialize AOP
aop = AOPClient()

# Create FastMCP server
mcp = FastMCP("my-server")

# Decorate your tools
@mcp.tool()
@aop.mcp.observe_tool(agent_id='my-server')
def calculator(operation: str, a: float, b: float) -> float:
    """Calculator tool with complete observability."""
    ops = {'add': a+b, 'sub': a-b, 'mul': a*b, 'div': a/b}
    return ops[operation]

@mcp.tool()
@aop.mcp.observe_tool(agent_id='my-server')
def search(query: str, max_results: int = 5) -> list:
    """Search tool with AOP logging."""
    import httpx
    response = httpx.get(f'https://api.example.com/search?q={query}')
    return response.json()['results'][:max_results]
```

### Using Official MCP SDK

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from aop import AOPClient
import asyncio

aop = AOPClient()
server = Server("my-server")

@server.call_tool()
@aop.mcp.observe_tool(agent_id='my-server')
async def get_weather(city: str) -> dict:
    """Get weather for a city."""
    # Your implementation
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://api.weather.com/{city}')
        return response.json()

if __name__ == "__main__":
    asyncio.run(stdio_server(server))
```

### Multi-Tool Server Example

```python
from mcp.server import Server
from aop import AOPClient

aop = AOPClient()
server = Server("research-assistant")

@server.call_tool()
@aop.mcp.observe_tool(agent_id='research-assistant')
async def search_papers(topic: str, year: int) -> list:
    """Search academic papers."""
    # Implementation
    pass

@server.call_tool()
@aop.mcp.observe_tool(agent_id='research-assistant')
async def summarize_paper(paper_id: str) -> str:
    """Summarize a paper."""
    # Implementation
    pass

@server.call_tool()
@aop.mcp.observe_tool(agent_id='research-assistant')
async def extract_citations(paper_id: str) -> list:
    """Extract citations from a paper."""
    # Implementation
    pass

# All three tools now have complete observability!
```

---

## Testing It Works

After decorating your tools, verify AOP is logging:

### 1. Check Events Were Logged

```bash
# View recent events
$ aop query --agent-id my-server

# Filter by tool name
$ aop query --agent-id my-server --event-type mcp.tool.called

# Last hour only
$ aop query --agent-id my-server --last 1h
```

### 2. Verify Output

**You should see:**
```
┌────────────────────┬──────────────┬──────────┬──────────┬───────────┐
│ Timestamp          │ Agent        │ Tool     │ Duration │ Status    │
├────────────────────┼──────────────┼──────────┼──────────┼───────────┤
│ 2025-01-15 10:30   │ my-server    │ search   │ 145ms    │ ✓ Success │
│ 2025-01-15 10:31   │ my-server    │ calc     │ 2ms      │ ✓ Success │
└────────────────────┴──────────────┴──────────┴──────────┴───────────┘
```

**If you see nothing:**
- Check decorator order (MCP decorator must be first!)
- Verify agent_id matches
- Check database file exists: `ls -la *.db`
- See [Common Pitfalls](#common-pitfalls) below

### 3. Check Database Location

```bash
# AOP creates database in current directory by default
$ ls -la aop_events.db

# Or specify custom location:
client = AOPClient(storage='sqlite:///path/to/events.db')
```

### 4. Test Without LLM (Manual Testing)

```python
# For testing, you can call tools directly
if __name__ == "__main__":
    result = search_web("AI agents")
    print(result)

    # Check AOP logged it
    events = aop.query(agent_id='my-server')
    print(f"Logged {len(events)} events")
```

---

## Basic Usage

### Decorator Pattern (Recommended)

```python
from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(agent_id='my-agent')
def search(query: str, max_results: int = 10):
    """Search for information."""
    import httpx
    response = httpx.get(f'https://api.duckduckgo.com/?q={query}&format=json')
    results = response.json().get('RelatedTopics', [])
    return results[:max_results]

# Use normally - everything is logged automatically!
result = search(query='AI agents', max_results=5)
```

**What gets logged automatically:**
- ✅ Tool name (`search`)
- ✅ Function parameters (`query='AI agents'`, `max_results=5`)
- ✅ Return value
- ✅ Execution duration
- ✅ Errors and exceptions (if any)
- ✅ Parent-child relationships (for multi-step workflows)

### Context Manager

```python
with client.mcp.tool_execution('my-agent', 'search', {'q': 'test'}) as handle:
    results = perform_search('test')
    handle.set_result(results)
```

### Manual Logging

```python
client.log_event({
    'agent_id': 'my-agent',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'data': {'tool_name': 'search', 'params': {'q': 'test'}}
})
```

---

## Core Features

### 1. Querying Events

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

### 2. Analytics & Insights

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

### 3. Command-Line Interface

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

### 4. Web Dashboard

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
- **Export from UI** - Export to JSON, CSV, TOON, OpenTelemetry, Prometheus
- **Real-time Stats** - Live performance metrics as events stream in

Access at `http://localhost:8000`

### 5. Exporters

#### JSON Export

```python
from aop.exporters import JSONExporter

exporter = JSONExporter(client)
events = client.query(agent_id='my-agent', limit=100)
json_output = exporter.export(events)

# Save to file
exporter.export_to_file(events, 'events.json')
```

#### CSV Export

```python
from aop.exporters import CSVExporter

exporter = CSVExporter(client)
events = client.query(agent_id='my-agent', limit=100)

# Export to file
exporter.export_to_file(events, 'events.csv')
```

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
from aop import Analytics
analytics = Analytics(client)
trace = analytics.reconstruct_trace(correlation_id=trace_id)
```

---

## 🔍 Trace Explorer - Multiple Search Methods

AOP supports **three ways** to view execution traces:

### 1. By Correlation ID (Original)
Group all events in a workflow using a shared correlation ID.

```python
# When logging events
with client.trace('user-request-123'):
    client.mcp.log_tool_call(...)  # Auto-tagged with correlation_id

# View trace
from aop import Analytics
analytics = Analytics(client)
trace = analytics.reconstruct_trace('user-request-123')
```

**Dashboard:** Enter correlation ID in Trace Explorer tab

**CLI:**
```bash
aop trace --correlation-id user-request-123
```

**API:**
```
GET /api/traces/{correlation_id}
```

### 2. By Event ID ⭐ NEW
Click any event to see its complete trace - **no correlation ID needed!**

**Dashboard:**
1. Click any event in Live Feed
2. Click "🔍 View Full Trace" button
3. Automatically shows root + all related events

**How it works:**
- Walks up `parent_id` chain to find root event
- Walks down to find all children
- Reconstructs complete execution tree

**API:**
```
GET /api/traces/by-event/{event_id}
```

**Example:**
```python
# Log events without correlation_id
call_event = client.mcp.log_tool_call(
    agent_id='my-agent',
    tool_name='search',
    params={'query': 'test'}
)

result_event = client.mcp.log_tool_result(
    agent_id='my-agent',
    tool_name='search',
    result={'found': 10},
    duration_ms=120,
    parent_id=call_event  # Links to parent
)

# Reconstruct trace using ANY event ID
analytics = Analytics(client)
trace = analytics.reconstruct_trace_from_event(result_event)
# Returns both events in tree structure!
```

### 3. By Parent ID ⭐ NEW
Search using any parent event ID to see all its children.

**API:**
```
GET /api/traces/by-parent/{parent_id}
```

**Why Multiple Search Methods?**

| Method | Use Case |
|--------|----------|
| **Correlation ID** | Planned workflows, multi-agent orchestration |
| **Event ID** | Debugging - "show me what led to this error" |
| **Parent ID** | Analyzing specific operation's sub-operations |

**No correlation_id? No problem!** Event ID search works even when you forgot to set correlation IDs.

---

## Verify It's Working (60 Second Test)

### 1. Install and start dashboard
```bash
pip install aop[dashboard]
aop dashboard
```

### 2. In another terminal, log a test event
```python
from aop import AOPClient

client = AOPClient()
client.log_event({
    'agent_id': 'test-agent',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'data': {'tool_name': 'test_tool', 'params': {'query': 'hello'}}
})
```

### 3. Check dashboard
Open `http://localhost:8000` - you should see your test event in Live Feed.

✅ **Working?** You're ready to integrate with your agent.
❌ **Not showing?** Check the [troubleshooting section](#common-pitfalls) below.

---

## How It Works

```
┌─────────────────┐
│  Your Agent     │
│ (MCP/LangChain) │
└────────┬────────┘
         │ @observe_tool decorator
         ▼
┌─────────────────┐
│   AOPClient     │ ← Logs events
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Storage      │ ← SQLite/PostgreSQL
│ (local/cloud)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │ ← Visualize & export
│   Analytics     │
└─────────────────┘
```

**Key Design Principles:**
- **Zero external dependencies** for core library
- **Local-first** - works offline, no cloud required
- **Async logging** - doesn't slow down your agent
- **Pluggable storage** - SQLite for dev, PostgreSQL for prod

---

## Common Pitfalls

### "I decorated my function but see no events"

**Solution 1: Check Decorator Order**
```python
# ✅ CORRECT
@server.call_tool()  # MCP decorator FIRST
@aop.mcp.observe_tool(agent_id='my-server')
async def my_tool():
    ...

# ❌ WRONG
@aop.mcp.observe_tool(agent_id='my-server')  # AOP first breaks MCP
@server.call_tool()
async def my_tool():
    ...
```

**Solution 2: Verify Database Location**
```bash
# Check if database was created
$ ls -la *.db
-rw-r--r--  1 user  staff  12288 Jan 15 10:30 aop_events.db

# If not found, specify explicit path
client = AOPClient(storage='sqlite:///./aop_events.db')
```

**Solution 3: Tool Must Be Called By LLM**
```
Remember: MCP tools only generate events when CALLED!
- Start your server
- Use tool through Claude Desktop or MCP client
- Then check: aop query --agent-id my-server
```

### "Events not showing in dashboard"

**Check agent_id matches:**
```python
# In code
@aop.mcp.observe_tool(agent_id='my-server')  # ← Note the ID

# In query
$ aop query --agent-id my-server  # ← Must match exactly!
```

### "Async function breaks with decorator"

**Decorator order is critical:**
```python
# ✅ Works with async
@server.call_tool()
@aop.mcp.observe_tool(agent_id='my-server')
async def my_async_tool():
    await asyncio.sleep(1)
    return "done"
```

### "Database locked" error

**Multiple processes accessing same database:**
```python
# Solution: Use PostgreSQL for multi-process
client = AOPClient(storage='postgresql://localhost/aop')

# Or: Use separate databases per process
client = AOPClient(storage=f'sqlite:///aop_{os.getpid()}.db')
```

### "No module named 'mcp'"

**Install MCP SDK:**
```bash
pip install mcp
# or
pip install fastmcp
```

---

## Examples

Complete working examples:

### Basic MCP Server with AOP

See [examples/mcp_server_with_aop.py](examples/mcp_server_with_aop.py) for a complete, runnable example.

### Decorator Usage

See [docs/examples/decorator_demo.py](docs/examples/decorator_demo.py) - Shows async/sync tools with decorators.

### Analytics and Tracing

See [docs/examples/analytics_demo.py](docs/examples/analytics_demo.py) - Analytics and trace reconstruction.

### TOON Export

See [examples/toon_export_demo.py](examples/toon_export_demo.py) - Export events in TOON format.

**Run examples:**
```bash
# Complete MCP server example
python examples/mcp_server_with_aop.py

# Decorator patterns
python docs/examples/decorator_demo.py

# Analytics demo
python docs/examples/analytics_demo.py
```

---

## Complete Real-World Example: Weather Agent

Here's a complete, copy-pasteable example of an MCP weather server with AOP:

```python
# weather_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from aop import AOPClient
import asyncio
import httpx

# Initialize AOP
aop = AOPClient(storage='sqlite:///weather_events.db')
server = Server("weather-agent")

@server.call_tool()
@aop.mcp.observe_tool(agent_id="weather-agent")
async def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": "YOUR_API_KEY", "units": "metric"}
        )
        data = response.json()
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }

@server.call_tool()
@aop.mcp.observe_tool(agent_id="weather-agent")
async def get_forecast(city: str, days: int = 5) -> dict:
    """Get weather forecast."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/forecast",
            params={"q": city, "appid": "YOUR_API_KEY", "units": "metric", "cnt": days}
        )
        return response.json()

if __name__ == "__main__":
    asyncio.run(stdio_server(server))
```

**Run it:**

```bash
# Install dependencies
pip install aop[cli,dashboard] mcp httpx

# Start server (in one terminal)
python weather_server.py &

# Start dashboard (in another terminal)
aop dashboard
```

**Use it in Claude Desktop:**

Add to your MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/path/to/weather_server.py"]
    }
  }
}
```

Restart Claude Desktop and ask:
```
"What's the weather in San Francisco?"
```

**See observability:**

1. **Live Feed:** Real-time tool calls as you chat
2. **Trace Explorer:** See which weather calls happened together
3. **Analytics:** Which cities you query most, average response time
4. **Export:** Download events as JSON, CSV, or TOON

```bash
# View recent tool calls
aop query --agent-id weather-agent --last 1h

# Export to TOON for LLM analysis
aop export -o weather_trace.toon -f toon --agent-id weather-agent
```

---

## Integrations

### LangChain

```python
from langchain.tools import Tool
from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(agent_id='langchain-agent')
def search_tool(query: str) -> str:
    import httpx
    response = httpx.get(f'https://api.duckduckgo.com/?q={query}&format=json')
    return str(response.json())

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

## Roadmap

See [RoadMap.md](RoadMap.md) for detailed development plan.

**v0.1.0-alpha** (Current)
- ✅ Core event logging and querying
- ✅ Protocol adapters (MCP, A2A, AP2)
- ✅ Analytics engine
- ✅ CLI tools
- ✅ Web dashboard
- ✅ OpenTelemetry and Prometheus exporters
- ✅ TOON export format

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
