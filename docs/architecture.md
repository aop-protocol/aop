# Architecture

System design and architecture of AOP (Agentic Observability Protocol).

## Table of Contents

- [Overview](#overview)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Storage Architecture](#storage-architecture)
- [Event Schema](#event-schema)
- [Protocol Adapters](#protocol-adapters)
- [Performance](#performance)
- [Scalability](#scalability)
- [Design Principles](#design-principles)

---

## Overview

AOP is designed as a **lightweight, privacy-first observability protocol** for AI agents with the following architecture goals:

- **<1ms P99 overhead** - Minimal performance impact
- **Protocol-agnostic** - Works with MCP, A2A, AP2
- **Storage-flexible** - SQLite, PostgreSQL, or custom backends
- **Privacy-first** - Local-only storage by default
- **Zero runtime dependencies** - Core library has no external deps

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Application                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│  │ Agent 1  │   │ Agent 2  │   │ Agent N  │                │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                │
│       │              │              │                        │
└───────┼──────────────┼──────────────┼────────────────────────┘
        │              │              │
        └──────────────┴──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │        AOPClient             │
        │  ┌────────────────────────┐  │
        │  │  Protocol Adapters     │  │
        │  │  ├─ MCPAdapter         │  │
        │  │  ├─ A2AAdapter         │  │
        │  │  └─ AP2Adapter         │  │
        │  └────────────────────────┘  │
        │  ┌────────────────────────┐  │
        │  │  Validation Layer      │  │
        │  └────────────────────────┘  │
        │  ┌────────────────────────┐  │
        │  │  Storage Interface     │  │
        │  └────────────────────────┘  │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │     Storage Backend          │
        │  ┌──────────────────────┐   │
        │  │  SQLite / PostgreSQL │   │
        │  │  / Custom Storage    │   │
        │  └──────────────────────┘   │
        └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Export & Analytics                         │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Analytics │  │   OTEL    │  │Prometheus│  │Dashboard │ │
│  └───────────┘  └───────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. AOPClient

**Purpose:** Main entry point for logging and querying events.

**Responsibilities:**
- Event validation and building
- Instance ID management
- Storage connection lifecycle
- Query interface

**Location:** `aop/client.py`

**Key Methods:**
```python
log_event(event, validate=True, auto_build=True) -> str
query(...) -> List[Dict[str, Any]]
get_trace(correlation_id) -> List[Dict[str, Any]]
close() -> None
```

### 2. Protocol Adapters

**Purpose:** Provide protocol-specific convenience APIs.

**Adapters:**
- **MCPAdapter** - Model Context Protocol (tools, LLM sampling)
- **A2AAdapter** - Agent-to-Agent (tasks, messages)
- **AP2Adapter** - Agent Payments (transactions, costs)

**Location:** `aop/adapters/`

**Design Pattern:** Facade pattern over `AOPClient.log_event()`

### 3. Storage Layer

**Purpose:** Persist and retrieve events.

**Interface:** `BaseStorage` abstract class

**Implementations:**
- `SQLiteStorage` - File-based or in-memory
- `PostgreSQLStorage` - Production database
- Custom implementations

**Location:** `aop/storage/`

### 4. Validation

**Purpose:** Ensure event schema compliance.

**Features:**
- Required field validation
- Type checking
- Event type format validation
- ISO 8601 timestamp validation

**Location:** `aop/validation.py`

### 5. Analytics

**Purpose:** Analyze and aggregate events.

**Features:**
- Trace reconstruction
- Aggregations (counts, averages, percentiles)
- Time-series analysis

**Location:** `aop/analytics.py`

### 6. Exporters

**Purpose:** Export to external observability systems.

**Exporters:**
- `OpenTelemetryExporter` - OTEL spans
- `PrometheusExporter` - Prometheus metrics
- `JSONExporter` / `CSVExporter` - File exports

**Location:** `aop/exporters/`

---

## Data Flow

### Event Logging Flow

```
┌─────────────┐
│ Application │
│   Code      │
└──────┬──────┘
       │
       │ 1. Call @observe_tool or log_event()
       ▼
┌──────────────────┐
│   Decorator /    │
│ Context Manager  │
└──────┬───────────┘
       │
       │ 2. Build event dict
       ▼
┌──────────────────┐
│   Validation     │
│   (optional)     │
└──────┬───────────┘
       │
       │ 3. Validate schema
       ▼
┌──────────────────┐
│   Auto-Build     │
│   (optional)     │
└──────┬───────────┘
       │
       │ 4. Fill id, timestamp, instance_id
       ▼
┌──────────────────┐
│ Storage Backend  │
│   INSERT         │
└──────────────────┘
```

**Timing:**
- Validation: ~0.1ms
- Auto-build: ~0.05ms
- SQLite insert: ~0.3ms
- **Total: <1ms P99**

### Query Flow

```
┌─────────────┐
│ Application │
│   Code      │
└──────┬──────┘
       │
       │ 1. client.query(agent_id='...')
       ▼
┌──────────────────┐
│   Query Builder  │
│  (SQL generation)│
└──────┬───────────┘
       │
       │ 2. Build SQL with filters
       ▼
┌──────────────────┐
│ Storage Backend  │
│   SELECT         │
└──────┬───────────┘
       │
       │ 3. Execute query
       ▼
┌──────────────────┐
│  Result Parser   │
│ (dict conversion)│
└──────┬───────────┘
       │
       │ 4. Return list of dicts
       ▼
┌─────────────┐
│ Application │
└─────────────┘
```

### Trace Reconstruction Flow

```
1. Query all events with correlation_id
   └─> SELECT * WHERE correlation_id = ?

2. Build parent-child map
   └─> {parent_id: [child_events]}

3. Find root event (no parent_id)
   └─> Root = event where parent_id is NULL

4. Recursively build tree
   └─> For each event, attach children from map

5. Calculate statistics
   └─> Total duration, event count, error count

6. Return trace structure
   └─> {root_event, children, stats}
```

---

## Storage Architecture

### Schema Design

**Events Table:**

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,           -- UUID v7 (time-ordered)
    version TEXT NOT NULL,         -- Event schema version
    timestamp TEXT NOT NULL,       -- ISO 8601 timestamp
    agent_id TEXT NOT NULL,        -- Agent identifier
    instance_id TEXT NOT NULL,     -- Instance identifier
    protocol TEXT NOT NULL,        -- mcp | a2a | ap2
    event_type TEXT NOT NULL,      -- Protocol-specific type

    -- Optional fields
    correlation_id TEXT,           -- Trace ID
    parent_id TEXT,                -- Parent event ID
    severity TEXT,                 -- error | warn | info | debug
    duration_ms INTEGER,           -- Duration in milliseconds

    -- JSON fields
    data TEXT,                     -- JSON data payload
    metadata TEXT,                 -- JSON metadata
    error TEXT,                    -- JSON error object

    -- Indexes
    INDEX idx_timestamp (timestamp),
    INDEX idx_agent_id (agent_id),
    INDEX idx_correlation_id (correlation_id),
    INDEX idx_event_type (event_type),
    INDEX idx_agent_timestamp (agent_id, timestamp)
);
```

**Index Strategy:**

1. **Primary Key**: `id` - UUID v7 provides time-ordered IDs
2. **timestamp**: For time-range queries
3. **agent_id**: For per-agent queries
4. **correlation_id**: For trace reconstruction
5. **event_type**: For type-specific queries
6. **agent_id + timestamp**: Composite for common query pattern

### Storage Implementations

#### SQLite

**Strengths:**
- Zero configuration
- File-based (portable)
- In-memory mode for testing
- Good for single-node deployments

**Limitations:**
- Single writer (lock contention)
- No network access
- Limited concurrency

**Use Cases:**
- Development
- Testing
- Single-agent deployments
- CLI tools

**Configuration:**

```python
# File-based
client = AOPClient(storage='sqlite:///aop_events.db')

# In-memory (testing)
client = AOPClient(storage='memory')

# WAL mode for better concurrency
client = AOPClient(storage='sqlite:///aop_events.db?mode=wal')
```

#### PostgreSQL

**Strengths:**
- Multi-writer support
- Network access
- High concurrency
- Better for production

**Limitations:**
- Requires PostgreSQL server
- More complex setup

**Use Cases:**
- Production deployments
- Multi-agent systems
- High-volume logging
- Distributed systems

**Configuration:**

```python
client = AOPClient(
    storage='postgresql://user:pass@localhost:5432/aop_db'
)

# With connection pool
from aop.storage import PostgreSQLStorage

storage = PostgreSQLStorage(
    connection_string,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600
)

client = AOPClient(storage=storage)
```

#### Custom Storage

Implement `BaseStorage` interface:

```python
from aop.storage.base import BaseStorage

class CustomStorage(BaseStorage):
    def insert_event(self, event: dict) -> None:
        """Insert event into storage."""
        pass

    def query_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        # ... filters
    ) -> List[dict]:
        """Query events with filters."""
        pass

    def close(self) -> None:
        """Close connections."""
        pass
```

---

## Event Schema

### Core Schema (v1.0)

```python
{
    # Required fields
    'id': str,              # UUID v7
    'version': str,         # "1.0"
    'timestamp': str,       # ISO 8601: "2025-01-15T10:30:00.123456Z"
    'agent_id': str,        # Agent identifier
    'instance_id': str,     # Instance UUID v7
    'protocol': str,        # "mcp" | "a2a" | "ap2"
    'event_type': str,      # "protocol.category.action"

    # Optional fields
    'correlation_id': str,  # Trace identifier
    'parent_id': str,       # Parent event ID
    'severity': str,        # "error" | "warn" | "info" | "debug"
    'duration_ms': int,     # Execution duration
    'data': dict,           # Protocol-specific data
    'metadata': dict,       # Additional metadata
    'error': {              # Error information
        'code': str,
        'message': str,
        'details': dict
    }
}
```

### Event Type Naming Convention

Format: `protocol.category.action`

**Examples:**
- `mcp.tool.called`
- `mcp.tool.completed`
- `mcp.tool.error`
- `a2a.task.assigned`
- `a2a.message.sent`
- `ap2.payment.initiated`

### UUID v7 for IDs

**Why UUID v7?**
- Time-ordered (monotonic)
- Globally unique
- Sortable by creation time
- 128-bit (no collisions)

**Generation:**

```python
import uuid_utils as uuid

event_id = str(uuid.uuid7())
# "01933d1e-7f8a-7890-b234-56789abcdef0"
```

---

## Protocol Adapters

### Design Pattern

Adapters follow the **Facade pattern**:

```python
class MCPAdapter:
    def __init__(self, client: AOPClient):
        self.client = client

    def log_tool_call(self, agent_id, tool_name, params, **kwargs):
        """Convenience wrapper over client.log_event()."""
        event = {
            'agent_id': agent_id,
            'event_type': 'mcp.tool.called',
            'protocol': 'mcp',
            'data': {
                'tool_name': tool_name,
                'params': params
            },
            **kwargs
        }
        return self.client.log_event(event)
```

### Decorator Implementation

**How @observe_tool works:**

```python
def observe_tool(self, agent_id, correlation_id=None, ...):
    """Decorator that wraps function to log events."""

    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 1. Log "called" event
            call_id = self.log_tool_call(
                agent_id=agent_id,
                tool_name=func.__name__,
                params=kwargs,
                correlation_id=correlation_id
            )

            # 2. Execute function
            start = time.time()
            try:
                result = func(*args, **kwargs)

                # 3. Log "completed" event
                self.log_tool_result(
                    agent_id=agent_id,
                    tool_name=func.__name__,
                    result=result,
                    parent_id=call_id,
                    duration_ms=(time.time() - start) * 1000,
                    correlation_id=correlation_id
                )

                return result

            except Exception as e:
                # 4. Log "error" event
                self.log_tool_error(
                    agent_id=agent_id,
                    tool_name=func.__name__,
                    error_code=type(e).__name__,
                    error_message=str(e),
                    parent_id=call_id,
                    correlation_id=correlation_id
                )
                raise

        # Async version similar but with async/await
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
```

---

## Performance

### Design for Speed

**Target: <1ms P99 overhead**

**Optimization Strategies:**

1. **Lazy Validation** - Optional, disabled in production
   ```python
   client.log_event(event, validate=False)  # Skip validation
   ```

2. **Minimal Serialization** - JSON only when writing to storage
   ```python
   # In-memory: Python dict
   # Storage: JSON.dumps() once
   ```

3. **Connection Pooling** - Reuse database connections
   ```python
   storage = PostgreSQLStorage(pool_size=20)
   ```

4. **Batch Inserts** - Future optimization
   ```python
   # Planned feature
   client.log_events_batch([event1, event2, event3])
   ```

5. **Async Support** - Non-blocking I/O
   ```python
   @client.mcp.observe_tool(agent_id='my-agent')
   async def async_tool():
       # Async logging doesn't block
       pass
   ```

### Benchmarks

**SQLite (in-memory):**
- Insert: 0.15ms median, 0.3ms P99
- Query (100 events): 1.2ms median

**SQLite (file, WAL mode):**
- Insert: 0.3ms median, 0.8ms P99
- Query (100 events): 2.5ms median

**PostgreSQL (local):**
- Insert: 0.5ms median, 1.2ms P99
- Query (100 events): 3.0ms median

**Total overhead with decorator:**
- <0.5ms P99 (validation disabled)
- <1.0ms P99 (validation enabled)

---

## Scalability

### Horizontal Scaling

**Multi-Instance Deployments:**

```python
# Each instance has unique instance_id
import socket

instance_id = socket.gethostname()
client = AOPClient(instance_id=instance_id)
```

**Centralized Storage:**

```python
# All instances write to same PostgreSQL
client = AOPClient(
    storage='postgresql://central-db:5432/aop',
    instance_id=instance_id
)
```

### Vertical Scaling

**Database Optimization:**

1. **Partitioning** (PostgreSQL)
   ```sql
   CREATE TABLE events_2025_01 PARTITION OF events
   FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
   ```

2. **Index Tuning**
   ```sql
   CREATE INDEX CONCURRENTLY idx_agent_time
   ON events(agent_id, timestamp DESC);
   ```

3. **Archival Strategy**
   ```python
   # Move old events to archive table
   archive_events(older_than_days=90)
   ```

### High-Volume Scenarios

**10,000+ events/second:**

1. Use PostgreSQL with connection pooling
2. Disable validation (pre-validate in application)
3. Use batch inserts (when available)
4. Partition by time
5. Consider write-ahead log optimization

---

## Design Principles

### 1. Privacy-First

- **Local storage by default** - No cloud dependencies
- **No telemetry** - AOP doesn't phone home
- **User-controlled** - You own your data

### 2. Zero Runtime Dependencies

All dependencies are included in the `aop-pack` package:

```bash
# Install complete package with all features
pip install aop-pack
```

The package includes:
- Core observability library
- OpenTelemetry exporters
- Prometheus exporters
- Dashboard and CLI tools
- All required dependencies

### 3. Protocol-Agnostic

- **Not tied to MCP** - Supports MCP, A2A, AP2
- **Extensible** - Add new protocols easily
- **Interoperable** - Protocols work together

### 4. Storage-Flexible

- **Pluggable backends** - SQLite, PostgreSQL, custom
- **Common interface** - BaseStorage abstraction
- **Migration support** - Export/import between backends

### 5. Minimal Overhead

- **<1ms P99** - Doesn't slow down your agents
- **Async support** - Non-blocking logging
- **Optional validation** - Skip in production

### 6. Developer-Friendly

- **Simple API** - Easy to use
- **Decorator pattern** - 1 line of code
- **Type hints** - IDE autocomplete
- **Comprehensive docs** - You're reading them!

---

## Next Steps

- **[User Guide](user-guide.md)** - Learn to use AOP
- **[API Reference](api-reference.md)** - Complete API docs
- **[Performance Tuning](user-guide.md#performance-tuning)** - Optimization tips
- **[Contributing](../CONTRIBUTING.md)** - Contribute to AOP
