# AOP Event Schema — v1.1

This document is **additive over v1.0**. All v1.0 events remain valid. v1.1
introduces:

1. An open **Protocol Registry** (no more closed enum of `mcp|a2a|ap2`).
2. **W3C TraceContext** fields (`trace_id`, `span_id`, `parent_span_id`).
3. **OpenTelemetry-compatible** `resource`, `links`, `attributes`.
4. First-class **token usage** and **cost** payloads.
5. **Extended event-type vocabularies** for MCP, A2A, AP2 and new built-ins
   (ACP, AGNTCY, ANP, AG-UI, OpenAI Agents, LLM, HTTP, vector DB, framework
   namespaces).

---

## 1. Required Fields

| Field         | Type     | Notes                                                   |
| ------------- | -------- | ------------------------------------------------------- |
| `id`          | string   | UUID v7                                                 |
| `version`     | string   | `"1.1"` (or `"1.0"` for backward-compat readers)        |
| `timestamp`   | string   | ISO 8601 with millisecond precision and `Z` suffix      |
| `agent_id`    | string   | `[A-Za-z0-9_\-:.]{1,255}`                               |
| `instance_id` | string   | UUID, identifies an instance of an agent process        |
| `protocol`    | string   | Must be a name registered with the protocol registry    |
| `event_type`  | string   | `<protocol>.<segment>(.<segment>)+` lowercase           |

## 2. Optional Fields (v1.0 carry-overs)

| Field            | Type    | Notes                                              |
| ---------------- | ------- | -------------------------------------------------- |
| `correlation_id` | string  | Logical trace id (free-form)                       |
| `parent_id`      | string  | Opaque parent event id (legacy linking)            |
| `severity`       | enum    | `error|warn|info|debug`                            |
| `duration_ms`    | number  | `>= 0`                                             |
| `data`           | object  | Protocol-specific payload                          |
| `metadata`       | object  | Free-form metadata                                 |
| `error`          | object  | `{code, message, details?, stack_trace?}`          |

## 3. New Optional Fields (v1.1)

| Field             | Type   | Notes                                                    |
| ----------------- | ------ | -------------------------------------------------------- |
| `trace_id`        | string | 32-char lower-hex (W3C TraceContext)                     |
| `span_id`         | string | 16-char lower-hex                                        |
| `parent_span_id`  | string | 16-char lower-hex                                        |
| `resource`        | object | `{service_name, service_version, deployment_environment, host_name, sdk_*}` |
| `links`           | array  | List of `{trace_id, span_id, attributes?}` cross-trace links |
| `attributes`      | object | OTel-flat key/value attributes (string scalars preferred) |
| `tokens`          | object | `{prompt, completion, total, cached?, reasoning?}` integers |
| `cost`            | object | `{amount, currency, model?, provider?, ...}` floats      |

## 4. Protocol Registry

A protocol is registered programmatically:

```python
from aop.registry import register_protocol, ProtocolSpec

register_protocol(ProtocolSpec(
    name="acp",
    version="0.1",
    event_types={"acp.invocation.started", "acp.invocation.completed"},
    description="IBM Agent Communication Protocol",
))
```

The registry is the source of truth for:

- `validate_event_type_exists`
- `validate_protocol`
- `validate_event_type_for_protocol`

### 4.1 Built-in protocols (v1.1)

`mcp`, `a2a`, `ap2`, `acp`, `agntcy`, `anp`, `ag_ui`, `openai_agents`,
`llm`, `http`, `vectordb`, `framework`, `feedback`.

### 4.2 Custom event types

Two escape hatches:

- **`<protocol>.custom.<org>.<category>.<action>`** — long-form, recommended
  when the user wants a stable name within a registered protocol.
- **`<protocol>.x.<...>`** — experimental short-form, allowed for any
  registered protocol.

## 5. Versioning

- `version` must be `"1.1"` for new producers.
- Consumers that only understand `"1.0"` can safely drop the v1.1 optional
  fields; required-field semantics are unchanged.
- Wire format (Phase 4) carries the schema version on the envelope so
  collectors can route by version.

## 6. W3C TraceContext interop

When emitting / consuming HTTP traffic (Phase 2), AOP injects/extracts the
standard `traceparent` and `tracestate` headers. Mapping:

- `traceparent: 00-<trace_id>-<span_id>-<flags>`
- `trace_id`, `span_id`, `parent_span_id` map directly into the W3C-format
  fields above.

Legacy `correlation_id` continues to work; it is treated as a logical alias
of `trace_id` when no `trace_id` is set.
