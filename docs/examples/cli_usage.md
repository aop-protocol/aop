# AOP CLI Usage Guide

This guide demonstrates how to use the AOP command-line interface for querying events, visualizing traces, and analyzing agent behavior.

## Installation

```bash
# Install AOP with all features included
pip install aop-pack
```

## Commands Overview

- `aop query` - Query and filter events
- `aop trace` - Visualize execution traces
- `aop stats` - Show analytics and statistics
- `aop export` - Export events to JSON or CSV
- `aop validate` - Validate event files

## 1. Query Events

### Basic Query

```bash
# Query all events (default limit: 50)
aop query --storage sqlite:///analytics_demo.db

# Query with custom limit
aop query --storage sqlite:///analytics_demo.db --limit 100
```

### Filter by Agent

```bash
# Show events for a specific agent
aop query --agent-id demo-agent --limit 20
```

### Filter by Event Type

```bash
# Show only tool calls
aop query --agent-id demo-agent --event-type mcp.tool.called

# Show only completed events
aop query --agent-id demo-agent --event-type mcp.tool.completed

# Show only errors
aop query --agent-id demo-agent --event-type mcp.tool.error
```

### Filter by Time Window

```bash
# Events from last 30 minutes
aop query --agent-id demo-agent --last 30m

# Events from last 2 hours
aop query --agent-id demo-agent --last 2h

# Events from last day
aop query --agent-id demo-agent --last 1d
```

### Filter by Correlation ID

```bash
# Show all events in a trace
aop query --correlation-id demo-trace-001
```

### Output Formats

```bash
# Table format (default) - rich, formatted output
aop query --agent-id demo-agent --format table

# Compact format - one event per line
aop query --agent-id demo-agent --format compact

# JSON format - structured data
aop query --agent-id demo-agent --format json

# Export to file
aop query --agent-id demo-agent --format json > events.json
```

### Combined Filters

```bash
# Combine multiple filters
aop query \
  --agent-id demo-agent \
  --event-type mcp.tool.completed \
  --last 1h \
  --limit 50 \
  --format compact
```

## 2. Visualize Traces

### Basic Trace Visualization

```bash
# Show trace as a tree (default)
aop trace --correlation-id demo-trace-001

# Specify storage location
aop trace --storage sqlite:///analytics_demo.db --correlation-id demo-trace-001
```

Example output:
```
Trace
└── search_database (called)
    └── search_database (completed) 51ms
        └── process_results (called)
            └── process_results (completed) 20ms
                └── store_output (called)
                    └── store_output (completed) 10ms

╭─────────────────────────────── Trace Summary ────────────────────────────────╮
│                                                                              │
│ Correlation ID: demo-trace-001                                               │
│ Total Events: 6                                                              │
│ Total Duration: 81ms                                                         │
│ Errors: 0                                                                    │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Trace Output Formats

```bash
# Tree format (default) - hierarchical visualization
aop trace --correlation-id demo-trace-001 --format tree

# Table format - flat list of events
aop trace --correlation-id demo-trace-001 --format table

# JSON format - structured data
aop trace --correlation-id demo-trace-001 --format json
```

## 3. Analytics and Statistics

### Basic Stats

```bash
# Show comprehensive statistics for an agent
aop stats --agent-id demo-agent
```

Example output:
```
╭──────────────────────────────────────────────────────────────────────────────╮
│ Analytics for Agent: demo-agent                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

        Tool Usage
┏━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Tool Name       ┃ Calls ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ search_database │    12 │
│ process_results │     8 │
│ store_output    │     2 │
└─────────────────┴───────┘

Event Type Distribution:
  mcp.tool.called               :   22
  mcp.tool.completed            :   22
  mcp.tool.error                :    0

       Average Duration by Tool
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name       ┃ Avg Duration (ms) ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ search_database │              51.0 │
│ process_results │              20.6 │
│ store_output    │              10.5 │
└─────────────────┴───────────────────┘

Latency Percentiles:
  P50 (median):   51.0ms
  P95:            51.0ms
  P99:            51.0ms
```

### Stats with Time Window

```bash
# Include event rate for last hour
aop stats --agent-id demo-agent --window 1h

# Event rate for last 30 minutes
aop stats --agent-id demo-agent --window 30m
```

## 4. Export Events

Export events to JSON or CSV formats for analysis, archiving, or integration with other tools.

### Export to JSON

```bash
# Export all events to JSON
aop export --output events.json

# Export with filters
aop export --output events.json --agent-id my-agent --limit 1000

# Export specific time range
aop export --output last-week.json --last 7d

# Export by correlation ID
aop export --output trace.json --correlation-id demo-trace-001
```

### Export to CSV

```bash
# Export to CSV format
aop export --output events.csv --format csv

# Export with time range
aop export --output metrics.csv --format csv --last 30d

# Export specific agent's events
aop export --output agent-data.csv --format csv --agent-id production-agent
```

**CSV Fields:**
- `id`, `timestamp`, `agent_id`, `event_type`, `protocol`
- `correlation_id`, `parent_id`, `duration_ms`
- `tool_name`, `error_code`, `error_message`

### Export Examples

```bash
# Daily backup
aop export --output backup-$(date +%Y-%m-%d).json --last 1d

# Export errors only
aop export --output errors.json --event-type mcp.tool.error --last 7d

# Export specific protocol events
aop export --output mcp-events.json --protocol mcp
```

## 5. Validate Event Files

Validate exported event files for schema compliance and reference integrity.

### Basic Validation

```bash
# Validate event file (schema check by default)
aop validate events.json

# Explicit schema validation
aop validate events.json --check-schema
```

### Reference Validation

```bash
# Check parent_id and correlation_id references
aop validate events.json --check-references

# Full validation (schema + references)
aop validate events.json --check-schema --check-references
```

### Validation Output

**Successful validation:**
```
Validating 100 event(s) from events.json...

Schema Validation:
  ✓ All events valid

Reference Validation:
  ✓ All parent references valid
  ℹ Found 5 unique correlation ID(s)

╭──────────────────────────────────────────────────────────────╮
│ Validation Passed                                            │
│ All checks successful!                                       │
╰──────────────────────────────────────────────────────────────╯
```

**With warnings:**
```
Validating 50 event(s) from events.json...

Schema Validation:
  ✓ All events valid

Reference Validation:
  ⚠ Found 3 orphaned parent reference(s)
    • Event abc-123 references missing parent xyz-456
    • Event def-789 references missing parent uvw-012
    ...

╭──────────────────────────────────────────────────────────────╮
│ Validation Passed with Warnings                              │
│ 3 warning(s)                                                 │
╰──────────────────────────────────────────────────────────────╯
```

**With errors:**
```
Validating 10 event(s) from invalid.json...

Schema Validation:
  ✗ Found 2 schema error(s)
    • Event 0: Missing required field 'agent_id'
    • Event 5: Invalid event_type format

╭──────────────────────────────────────────────────────────────╮
│ Validation Failed                                            │
│ 2 error(s), 0 warning(s)                                     │
╰──────────────────────────────────────────────────────────────╯
```

## Common Workflows

### Debugging a Failed Trace

```bash
# 1. Find recent errors
aop query --agent-id my-agent --event-type mcp.tool.error --last 1h

# 2. Get the correlation ID from the error event
# 3. Visualize the full trace
aop trace --correlation-id <correlation-id>

# 4. Export for detailed analysis
aop trace --correlation-id <correlation-id> --format json > trace.json
```

### Performance Analysis

```bash
# 1. View overall statistics
aop stats --agent-id my-agent

# 2. Check recent event rate
aop stats --agent-id my-agent --window 1h

# 3. Find slow operations
aop query --agent-id my-agent --event-type mcp.tool.completed --format json | \
  jq 'sort_by(.duration_ms) | reverse | .[0:10]'
```

### Daily Monitoring

```bash
# Morning check: events from last 24 hours
aop query --agent-id production-agent --last 1d --format compact

# Check for errors
aop query --agent-id production-agent --event-type mcp.tool.error --last 1d

# Performance overview
aop stats --agent-id production-agent --window 24h
```

## Help and Documentation

```bash
# General help
aop --help

# Command-specific help
aop query --help
aop trace --help
aop stats --help
aop export --help
aop validate --help

# Version information
aop --version
```

## Storage Connection Strings

The `--storage` option accepts different connection formats:

```bash
# SQLite (default)
--storage sqlite:///path/to/events.db

# SQLite (relative path)
--storage sqlite://./events.db

# In-memory (testing)
--storage memory

# PostgreSQL
--storage postgresql://user:pass@localhost/aop_db
```

## Tips and Best Practices

1. **Use compact format for quick checks**: `--format compact` is faster for reviewing many events
2. **Export to JSON for scripting**: Pipe to `jq` for advanced filtering and analysis
3. **Set default storage**: Use environment variable `AOP_STORAGE` to avoid typing `--storage` repeatedly
4. **Monitor event rates**: Use `--window` to track trends over time
5. **Combine filters**: Stack multiple filters for precise queries
6. **Save common queries**: Create shell aliases for frequently-used commands

## Advanced Examples

### Find Longest Running Operations

```bash
aop query --agent-id my-agent --event-type mcp.tool.completed --format json | \
  jq -r 'sort_by(.duration_ms) | reverse | .[0:5] |
  .[] | "\(.duration_ms)ms - \(.data.tool_name)"'
```

### Count Events by Hour

```bash
aop query --agent-id my-agent --last 24h --format json | \
  jq -r '.[].timestamp | split("T")[1] | split(":")[0]' | \
  sort | uniq -c
```

### Export Trace as Flamegraph Data

```bash
aop trace --correlation-id trace-123 --format json | \
  jq -r '.children[] | recurse(.children[]?) |
  "\(.event.data.tool_name) \(.event.duration_ms)"'
```

## Troubleshooting

### Command not found

```bash
# Ensure aop-pack is installed
pip install aop-pack

# If using virtual environment, activate it first
source .venv/bin/activate
```

### No events found

```bash
# Check database exists
ls -lh analytics_demo.db

# Verify agent ID is correct
aop query --limit 1  # Show any event to see agent IDs
```

### Performance with large databases

```bash
# Use smaller limits
aop query --limit 100

# Filter by time window
aop query --last 1h

# Use compact format
aop query --format compact
```

## Next Steps

- See [analytics_demo.py](analytics_demo.py) for generating sample data
- See [decorator_demo.py](decorator_demo.py) for instrumenting your code
- Check the [AOP Documentation](../README.md) for Python API details
