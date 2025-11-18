# Changelog

All notable changes to the AOP (Agentic Observability Protocol) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Batch insert optimization for high-throughput scenarios
- Stream processing API for real-time event handling
- Additional storage backends (Redis, MongoDB)
- Enhanced dashboard features (custom charts, saved filters)
- Performance improvements for large-scale deployments

---

## [0.1.0-alpha] - 2025-01-15

### Added

#### Core Features
- **Event Logging System**
  - Universal event logging API for AI agents
  - Support for multiple protocols (MCP, A2A, AP2)
  - Automatic capture of tool calls, parameters, results, and errors
  - Parent-child event relationships for distributed tracing
  - Correlation ID support for multi-agent workflows

#### Protocol Adapters
- **MCP (Model Context Protocol) Adapter**
  - `observe_tool()` decorator for automatic instrumentation
  - Tool execution tracking (call, result, error events)
  - LLM sampling request/response logging
  - Context manager API for manual control
  - Full async/await support

- **A2A (Agent-to-Agent Protocol) Adapter**
  - Task assignment and completion tracking
  - Inter-agent messaging support
  - Agent lifecycle events (start, stop, error)

- **AP2 (Agent Payments Protocol) Adapter**
  - Payment initiation and completion tracking
  - Cost tracking for LLM API calls and resources
  - Transaction logging with full audit trail

#### Storage Backends
- **SQLite Storage** (default)
  - File-based persistent storage
  - In-memory mode for testing
  - Connection pooling for performance
  - Automatic schema migrations

- **PostgreSQL Storage**
  - Production-ready relational database support
  - Full ACID compliance
  - Optimized queries with indexes
  - Multi-process safe

- **Memory Storage**
  - In-memory storage for testing and development
  - Fast performance for unit tests
  - No persistence (data lost on restart)

#### Query & Analytics
- **Querying API**
  - Filter by agent_id, event_type, protocol
  - Time range queries (start_time, end_time)
  - Limit and offset for pagination
  - Get complete traces by correlation_id

- **Analytics Engine**
  - Distributed trace reconstruction
  - Tool usage statistics (counts, durations)
  - Latency percentiles (P50, P95, P99)
  - Time-series analysis with bucketing
  - Event rate calculations
  - Error rate tracking

#### Command-Line Interface
- **Query Commands**
  - `aop query` - Query events with filters
  - `aop trace` - Visualize distributed traces
  - `aop stats` - View analytics and statistics

- **Export Commands**
  - `aop export` - Export events in multiple formats
  - Support for JSON, CSV, TOON, OpenTelemetry, Prometheus

- **Server Commands**
  - `aop dashboard` - Launch web dashboard
  - `aop prometheus` - Start Prometheus metrics server

#### Web Dashboard
- **Real-time Event Monitoring**
  - Tabular view with sortable columns
  - Live updates via WebSocket
  - Click-to-view event details panel
  - Color-coded status indicators (success, error, in-progress)

- **Filtering & Sorting**
  - Filter by agent, event type, protocol, time range
  - Sort by timestamp, agent name, duration
  - Search functionality

- **Export from UI**
  - Direct export to JSON, CSV, TOON formats
  - OpenTelemetry and Prometheus export
  - Download with auto-generated filenames

- **Professional UI**
  - Tailwind CSS styling
  - Responsive design
  - Dark mode support (indicators)
  - Clean, modern interface

#### Exporters
- **JSON Exporter**
  - Pretty-printed JSON output
  - Customizable indentation
  - File and string export

- **CSV Exporter**
  - Standard CSV format for spreadsheets
  - Header row with field names
  - Handles nested data via flattening

- **TOON Exporter** (Token-Oriented Object Notation)
  - **30-60% token reduction** for LLM consumption
  - Tabular format for uniform data
  - Multiple delimiter options (comma, tab, pipe)
  - Automatic flattening of nested structures
  - Token estimation with savings calculation
  - Perfect for AI-assisted debugging

- **OpenTelemetry Exporter**
  - Convert AOP events to OTLP spans
  - Full trace context preservation
  - Export to OTEL collectors (Jaeger, Zipkin, Tempo)
  - SpanKind mapping (CLIENT, INTERNAL, etc.)

- **Prometheus Exporter**
  - HTTP metrics server on configurable port
  - Standard Prometheus text format
  - Metrics exposed:
    - `aop_events_total` (counter by type, agent, protocol)
    - `aop_tool_duration_seconds` (histogram)
    - `aop_tool_errors_total` (counter)
    - `aop_event_rate` (gauge, events/minute)

#### Documentation
- Comprehensive README with quick start guide
- MCP server integration examples (FastMCP and official SDK)
- 5-minute quick start tutorial
- Common pitfalls and troubleshooting guide
- Code of Conduct (Contributor Covenant 2.1)
- Contributing guidelines
- Security policy
- Complete API examples

#### Examples
- `mcp_server_with_aop.py` - Complete working MCP server
- `toon_export_demo.py` - TOON format export demonstration
- Decorator usage examples
- Analytics and trace reconstruction examples

### Performance
- **<1ms P99 latency** for event logging
- **0.3ms median** insert time (SQLite)
- **2.5ms median** for querying 100 events
- Zero runtime dependencies in core library
- Async/await support throughout
- Connection pooling for database efficiency

### Developer Experience
- **Type Hints** - Full type annotations with mypy strict mode
- **Zero Dependencies** - Core library uses only Python stdlib
- **Simple API** - 1-line decorator for instrumentation
- **86% code reduction** compared to manual logging
- **Privacy-First** - Local storage by default, no telemetry
- **Protocol-Agnostic** - Works with any agent protocol

### Testing
- **384 passing tests** with 74% code coverage
- Unit tests for all core functionality
- Integration tests for storage backends
- Exporter tests with optional dependencies
- CI/CD pipeline with GitHub Actions
- Security scanning with Bandit
- Type checking with mypy
- Linting with flake8

### CI/CD
- Automated testing on Python 3.9, 3.10, 3.11, 3.12
- Code coverage reporting with Codecov
- Security scanning on push and weekly schedule
- Type checking and linting in CI pipeline

### Known Limitations (Alpha)
- Dashboard requires manual refresh for some views
- PostgreSQL schema migrations are manual
- Limited error handling in some edge cases
- No batch insert API yet
- TOON format is experimental
- Some mypy type errors exist (non-blocking)

### Breaking Changes
- None (initial release)

---

## Release Types

- **Alpha** (0.x.0-alpha) - Initial development, API may change
- **Beta** (0.x.0-beta) - Feature complete, API stabilizing
- **RC** (0.x.0-rc.1) - Release candidate, production-ready testing
- **Stable** (1.0.0+) - Production-ready, semantic versioning

---

## Links

- [Repository](https://github.com/aop-protocol/aop)
- [Documentation](https://docs.aop-protocol.org)
- [Issue Tracker](https://github.com/aop-protocol/aop/issues)
- [PyPI Package](https://pypi.org/project/aop/)

[Unreleased]: https://github.com/aop-protocol/aop/compare/v0.1.0-alpha...HEAD
[0.1.0-alpha]: https://github.com/aop-protocol/aop/releases/tag/v0.1.0-alpha
