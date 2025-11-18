# CLI Reference

Complete command-line interface reference for AOP.

## Installation

```bash
pip install aop-pack
```

All CLI dependencies (`click` and `rich`) are included in the package.

## Global Options

All commands support these global options:

```bash
aop --version    # Show AOP version
aop --help       # Show help
```

---

## Commands

- [query](#aop-query) - Query and filter events
- [trace](#aop-trace) - Visualize execution traces
- [stats](#aop-stats) - Show analytics and statistics
- [export](#aop-export) - Export events to JSON or CSV
- [validate](#aop-validate) - Validate event files
- [prometheus](#aop-prometheus) - Start Prometheus metrics server
- [export-otel](#aop-export-otel) - Export to OpenTelemetry
- [dashboard](#aop-dashboard) - Launch web dashboard

---

## aop query

Query and filter AOP events.

### Usage

```bash
aop query [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--storage` | `-s` | string | `sqlite:///aop_events.db` | Storage connection string |
| `--agent-id` | `-a` | string | - | Filter by agent ID |
| `--event-type` | `-e` | string | - | Filter by event type |
| `--protocol` | `-p` | string | - | Filter by protocol (mcp, a2a, ap2) |
| `--correlation-id` | `-c` | string | - | Filter by correlation ID |
| `--limit` | `-l` | int | 50 | Maximum number of events |
| `--format` | `-f` | choice | `table` | Output format: table, json, compact |
| `--last` | - | string | - | Show events from last N minutes/hours (e.g., "30m", "2h", "1d") |

### Examples

**Get last 10 events for an agent:**

```bash
aop query --agent-id my-agent --limit 10
```

**Filter by event type:**

```bash
aop query --event-type mcp.tool.called --limit 20
```

**Events from last hour:**

```bash
aop query --last 1h
```

**Events from last 30 minutes:**

```bash
aop query --last 30m --format compact
```

**Get trace events:**

```bash
aop query --correlation-id trace-123 --format json
```

**Multiple filters:**

```bash
aop query --agent-id my-agent --protocol mcp --last 2h --limit 100
```

**Different storage:**

```bash
aop query --storage postgresql://user:pass@localhost/aop --limit 10
```

### Output Formats

**Table format (default):**

```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Timestamp          ┃ Agent ID ┃ Event Type      ┃ Duration ┃ Data         ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 2025-01-15T10:30:0 │ my-agent │ mcp.tool.called │ 125ms    │ tool: search │
│ 2025-01-15T10:30:1 │ my-agent │ mcp.tool.compl… │ -        │ tool: search │
└────────────────────┴──────────┴─────────────────┴──────────┴──────────────┘
```

**Compact format:**

```
2025-01-15T10:30:00 [mcp.tool.called] search (125ms)
2025-01-15T10:30:01 [mcp.tool.completed] search
```

**JSON format:**

```json
[
  {
    "id": "01933d1e-...",
    "timestamp": "2025-01-15T10:30:00.123456Z",
    "agent_id": "my-agent",
    "event_type": "mcp.tool.called",
    ...
  }
]
```

---

## aop trace

Visualize execution traces as a tree.

### Usage

```bash
aop trace --correlation-id TRACE_ID [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--storage` | `-s` | string | `sqlite:///aop_events.db` | Storage connection string |
| `--correlation-id` | `-c` | string | **required** | Correlation ID to reconstruct |
| `--format` | `-f` | choice | `tree` | Output format: tree, table, json |

### Examples

**Visualize trace as tree:**

```bash
aop trace --correlation-id trace-123
```

**Table format:**

```bash
aop trace -c demo-trace-001 --format table
```

**JSON output:**

```bash
aop trace -c trace-123 --format json
```

### Output Formats

**Tree format (default):**

```
Trace
└─ search_database (called)
   └─ completed (52ms)
└─ process_results (called)
   └─ completed (25ms)
└─ store_output (called)
   └─ completed (10ms)

Trace Summary
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Correlation ID   ┃ trace-123 ┃
┃ Total Events     ┃ 6         ┃
┃ Total Duration   ┃ 87ms      ┃
┃ Errors           ┃ 0         ┃
┗━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━┛
```

**Table format:**

```
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ Event Type           ┃ Tool            ┃ Duration ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ mcp.tool.called      │ search_database │ -        │ -      │
│ mcp.tool.completed   │ search_database │ 52ms     │ OK     │
│ mcp.tool.called      │ process_results │ -        │ -      │
│ mcp.tool.completed   │ process_results │ 25ms     │ OK     │
└──────────────────────┴─────────────────┴──────────┴────────┘
```

---

## aop stats

Show analytics and statistics for an agent.

### Usage

```bash
aop stats --agent-id AGENT_ID [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--storage` | `-s` | string | `sqlite:///aop_events.db` | Storage connection string |
| `--agent-id` | `-a` | string | **required** | Agent ID to analyze |
| `--window` | `-w` | string | - | Time window (e.g., "30m", "2h", "1d") |

### Examples

**Show statistics for agent:**

```bash
aop stats --agent-id my-agent
```

**Statistics for last hour:**

```bash
aop stats -a demo-agent --window 1h
```

**Statistics for last 24 hours:**

```bash
aop stats --agent-id my-agent --window 1d
```

### Output

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Analytics for Agent: my-agent   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Tool Usage
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Tool Name          ┃ Calls ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ search             │   150 │
│ process            │    80 │
│ analyze            │    45 │
└────────────────────┴───────┘

Event Type Distribution:
  mcp.tool.called           : 275
  mcp.tool.completed        : 270
  mcp.tool.error            :   5

Average Duration by Tool
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name          ┃ Avg Duration (ms)  ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ analyze            │              320.8 │
│ search             │              125.5 │
│ process            │               45.2 │
└────────────────────┴────────────────────┘

Latency Percentiles:
  P50 (median):  105.2ms
  P95:           450.8ms
  P99:           825.3ms

Event Rate (1h): 45.30 events/min
```

---

## aop export

Export AOP events to JSON or CSV format.

### Usage

```bash
aop export --output FILE [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--storage` | `-s` | string | `sqlite:///aop_events.db` | Storage connection string |
| `--output` | `-o` | string | **required** | Output file path |
| `--format` | `-f` | choice | `json` | Output format: json, csv |
| `--agent-id` | `-a` | string | - | Filter by agent ID |
| `--event-type` | `-e` | string | - | Filter by event type |
| `--protocol` | `-p` | string | - | Filter by protocol |
| `--correlation-id` | `-c` | string | - | Filter by correlation ID |
| `--last` | - | string | - | Export from last N minutes/hours |
| `--limit` | `-l` | int | - | Maximum number of events |

### Examples

**Export all events to JSON:**

```bash
aop export --output events.json
```

**Export to CSV:**

```bash
aop export --output events.csv --format csv
```

**Export last 30 days to JSON:**

```bash
aop export --output monthly.json --last 30d
```

**Export specific agent:**

```bash
aop export -o my-agent.json --agent-id my-agent --limit 1000
```

**Export trace:**

```bash
aop export --output trace.json --correlation-id trace-123
```

**Export with filters:**

```bash
aop export --output tool-calls.csv --format csv \
  --event-type mcp.tool.called \
  --last 7d
```

### Output

```
✓ Exported 1,523 events to events.json (JSON)
```

---

## aop validate

Validate AOP event files against the schema.

### Usage

```bash
aop validate FILE [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--check-schema` | flag | - | Validate against AOP event schema |
| `--check-references` | flag | - | Check parent_id and correlation_id references |

### Examples

**Basic validation:**

```bash
aop validate events.json
```

**Schema validation:**

```bash
aop validate events.json --check-schema
```

**Full validation (schema + references):**

```bash
aop validate events.json --check-schema --check-references
```

### Output

**Valid file:**

```
Validating 125 event(s) from events.json...

Schema Validation:
  ✓ All events valid

Reference Validation:
  ✓ All parent references valid
  ℹ Found 5 unique correlation ID(s)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Validation Passed               ┃
┃ All checks successful!          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Invalid file:**

```
Validating 10 event(s) from bad-events.json...

Schema Validation:
  ✗ Found 3 schema error(s)
    • Event 2: Missing required field 'agent_id'
    • Event 5: Invalid event_type format
    • Event 8: timestamp must be ISO 8601 format

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Validation Failed               ┃
┃ 3 error(s), 0 warning(s)        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## aop prometheus

Start Prometheus metrics exporter server.

### Usage

```bash
aop prometheus [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--storage` | `-s` | string | `sqlite:///aop_events.db` | Storage connection string |
| `--port` | `-p` | int | 9090 | Port to run server on |
| `--poll-interval` | - | float | 30.0 | Polling interval in seconds |

### Examples

**Start server with defaults:**

```bash
aop prometheus
```

**Custom port and storage:**

```bash
aop prometheus --port 9090 --storage sqlite:///my_events.db
```

**Custom poll interval:**

```bash
aop prometheus --poll-interval 60.0
```

### Output

```
Starting Prometheus exporter server...
Storage: sqlite:///aop_events.db
Port: 9090
Metrics: http://localhost:9090/metrics

Press Ctrl+C to stop
```

### Metrics Exposed

Access metrics at `http://localhost:9090/metrics`

**Available metrics:**

```prometheus
# Total events by type, agent, protocol
aop_events_total{event_type="mcp.tool.called",agent_id="my-agent",protocol="mcp"} 150

# Tool duration histogram
aop_tool_duration_seconds_bucket{tool_name="search",agent_id="my-agent",le="0.1"} 45
aop_tool_duration_seconds_sum{tool_name="search",agent_id="my-agent"} 15.2
aop_tool_duration_seconds_count{tool_name="search",agent_id="my-agent"} 150

# Tool errors
aop_tool_errors_total{tool_name="search",agent_id="my-agent",error_code="TIMEOUT"} 3

# Event rate (events per minute)
aop_event_rate{agent_id="my-agent"} 45.3
```

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'aop'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
```

---

## aop export-otel

Export AOP events to OpenTelemetry format.

### Usage

```bash
aop export-otel [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--storage` | `-s` | string | `sqlite:///aop_events.db` | Storage connection string |
| `--output` | `-o` | string | - | Output file path (for JSON export) |
| `--endpoint` | `-e` | string | - | OTEL collector endpoint |
| `--agent-id` | `-a` | string | - | Filter by agent ID |
| `--correlation-id` | `-c` | string | - | Export trace by correlation ID |
| `--limit` | `-l` | int | 1000 | Maximum number of events |

### Examples

**Export to OTEL collector:**

```bash
aop export-otel --endpoint http://localhost:4317
```

**Export trace to collector:**

```bash
aop export-otel --endpoint http://localhost:4317 --correlation-id trace-123
```

**Export to JSON file:**

```bash
aop export-otel --output trace.json --correlation-id trace-123
```

**Export recent events:**

```bash
aop export-otel --endpoint http://localhost:4317 --agent-id my-agent --limit 1000
```

### Output

```
Exporting trace: trace-123
✓ Converted 6 events to OTEL spans
✓ Exported to OTEL collector: http://localhost:4317
```

---

## aop dashboard

Launch the AOP Dashboard web interface.

### Usage

```bash
aop dashboard [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--storage` | `-s` | string | `sqlite:///aop_events.db` | Storage connection string |
| `--port` | `-p` | int | 8000 | Port to run server on |
| `--no-browser` | - | flag | - | Don't open browser automatically |

### Examples

**Launch dashboard:**

```bash
aop dashboard
```

**Custom port:**

```bash
aop dashboard --port 8080
```

**Don't open browser:**

```bash
aop dashboard --no-browser
```

**Different storage:**

```bash
aop dashboard --storage postgresql://user:pass@localhost/aop
```

### Output

```
Starting AOP Dashboard...
Server running at http://localhost:8000
Opening browser...
Press Ctrl+C to stop
```

Access at `http://localhost:8000`

**Features:**
- Live event feed
- Trace visualization
- Analytics charts
- Query interface

See [Dashboard Guide](dashboard.md) for details.

---

## Common Workflows

### Daily Analysis

```bash
# Check recent activity
aop query --last 1d --format compact

# Analyze agent performance
aop stats --agent-id my-agent --window 1d

# Export for archival
aop export --output $(date +%Y-%m-%d)-events.json --last 1d
```

### Debugging a Trace

```bash
# Find correlation ID
aop query --agent-id my-agent --limit 10 --format json | jq '.[0].correlation_id'

# Visualize trace
aop trace --correlation-id <TRACE_ID>

# Export trace for analysis
aop export --output debug-trace.json --correlation-id <TRACE_ID>
```

### Production Monitoring

```bash
# Terminal 1: Start Prometheus exporter
aop prometheus --port 9090

# Terminal 2: Start dashboard
aop dashboard --port 8000

# Terminal 3: Watch live events
watch -n 5 'aop query --last 5m --format compact'
```

### Data Migration

```bash
# Export from SQLite
aop export --storage sqlite:///old.db --output all-events.json

# Import to PostgreSQL (requires custom script or use API)
python import_events.py all-events.json postgresql://localhost/new_db
```

---

## Environment Variables

Set default values with environment variables:

```bash
export AOP_STORAGE="postgresql://localhost/aop"
export AOP_DEFAULT_AGENT="my-agent"

# Now you can omit --storage option
aop query --agent-id my-agent
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid arguments, storage error, etc.) |

---

## Shell Completion

Generate shell completion (if supported by future versions):

```bash
# Bash
aop --install-completion bash

# Zsh
aop --install-completion zsh

# Fish
aop --install-completion fish
```

---

## Next Steps

- **[User Guide](user-guide.md)** - Learn to use AOP programmatically
- **[Dashboard Guide](dashboard.md)** - Web interface guide
- **[API Reference](api-reference.md)** - Python API documentation
