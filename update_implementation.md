# AOP — Implementation Status Update

> **Branch:** `claude/analyze-observability-codebase-TGsMM`
> **Schema version produced by this work:** **v1.1**
> **SDK version (`aop.__version__`):** **1.1.0**
> **Last commit on this branch:** `945a780` — Phase 10 cost intelligence
> **No tests have been run on this branch yet** — all changes are
> code-only, committed and pushed but not validated against the test
> suite. See "Things a new agent should do first" at the bottom.

This document tells a brand-new agent (or contributor) **what was built,
where it lives, what is still open, and how to navigate the code**.

---

## 1. The 60-second mental model

```
                    ┌────────────────────────────────────┐
                    │  USER CODE (any AI agent)          │
                    │   • aop.autoinstrument()           │  Phase 2
                    │   • client.mcp.* / client.a2a.* …  │  Phase 3
                    │   • client.start_span(...)         │  Phase 1
                    └──────────────┬─────────────────────┘
                                   │ AOPEvent (v1.1)
                    ┌──────────────▼─────────────────────┐
                    │  aop.client.AOPClient.log_event    │  core
                    │   ├─ events.build_event            │  core
                    │   ├─ validation.validate_event     │  Phase 0
                    │   ├─ storage.<backend>.log_event   │  core/Phase 5
                    │   ├─ transport.export([ev])        │  Phase 4
                    │   └─ dashboard.sse.publish(ev)     │  Phase 7
                    └──────────────┬─────────────────────┘
            ┌──────────────────────┼─────────────────────────────┐
            ▼                      ▼                             ▼
   Local SQLite/PG/CH/S3   AOP Collector / OTLP backend    Dashboard SSE
   (Phase 5)                (Phase 4)                       /api/stream
                                                            (Phase 7)
```

Cross-cutting layers:

- **Phase 0** — `aop.registry` is the open set of protocols. **Every
  validation goes through it.**
- **Phase 1** — `aop.propagation` (W3C TraceContext) and `aop.span` (OTel-
  style spans) thread `trace_id` / `span_id` through every event.
- **Phase 6** — `aop.redaction` runs before persistence/export;
  `aop.compliance.*` and `aop.security.*` are opt-in helpers.
- **Phase 10** — `aop.pricing` book is consulted by every LLM auto-
  instrumentation hook, attaching `tokens` and `cost` to every event.

---

## 2. Where to start reading (recommended order)

If you want to understand the whole flow with the least friction, open
these files in this order:

1. `aop/__init__.py` — **the public API surface**. If a name isn't
   re-exported here, it is internal.
2. `aop/registry.py` — protocol registry and **the list of every built-in
   protocol** (`mcp`, `a2a`, `ap2`, `acp`, `agntcy`, `anp`, `ag_ui`,
   `openai_agents`, `feedback`, `http`, `llm`, `vectordb`, `framework`,
   `db`, `cache`, `tcp`).
3. `aop/types.py` — the `AOPEvent` TypedDict; this is the canonical
   v1.1 event shape.
4. `aop/validation.py` — the validation pipeline; mirrors the spec.
5. `aop/events.py` — `build_event(...)` and protocol-specific builders.
6. `aop/client.py` — `AOPClient`. Note `log_event` → `_ship_to_transport`
   → `dashboard.sse.publish` chain.
7. `aop/propagation.py` and `aop/span.py` — distributed tracing.
8. `aop/instrumentation/__init__.py` — the `autoinstrument()` dispatcher
   and the integrations table (one entry per supported library).
9. `aop/transport/__init__.py` — pluggable transports (Direct, Batch,
   HTTP-JSON, OTLP/HTTP, OTLP/gRPC).
10. `aop_collector/__init__.py` — the standalone Collector binary.
11. `docs/specification/event-schema-v1.1.md` — the canonical wire spec.
12. `tests/conformance/README.md` — the cross-language conformance suite.

---

## 3. Files added/changed by phase

### Phase 0 — Foundations (commit `ee45fc9`)

| File | What it does |
|---|---|
| `aop/registry.py`                                     | **NEW.** Open ProtocolSpec registry. Replaces the closed `Protocol` enum. Pre-registers all built-in protocols. |
| `aop/types.py`                                        | Schema `VERSION = "1.1"`. Extended `AOPEvent` with `trace_id`, `span_id`, `parent_span_id`, `resource`, `links`, `attributes`, `tokens`, `cost`. Kept old enums for back-compat. |
| `aop/validation.py`                                   | Now consults the registry; accepts both v1.0 and v1.1 schema versions; validates new fields when present; supports `<protocol>.x.<...>` experimental escape hatch. |
| `aop/utils.py`                                        | `validate_protocol` / `validate_event_type_format` consult the registry. New: `generate_trace_id`, `generate_span_id`, `validate_trace_id`, `validate_span_id`. |
| `aop/events.py`                                       | `build_event` accepts the v1.1 fields and forwards them. |
| `docs/specification/event-schema-v1.1.md`             | **NEW.** Spec doc for v1.1. |
| `aop/__init__.py`                                     | Re-exports the registry API. |

### Phase 1 — W3C TraceContext + Span (commit `ee45fc9`)

| File | What it does |
|---|---|
| `aop/propagation.py`                                  | **NEW.** `SpanContext`, traceparent/tracestate/baggage parse + format, B3 single-header fallback, `inject` / `extract`. |
| `aop/span.py`                                         | **NEW.** OTel-style `Span` with start/end/record_exception. Emits `<protocol>.<name>.started/.completed/.error` events. |
| `aop/trace.py`                                        | Kept `trace_context(...)` for back-compat. Added `SpanContext` ContextVar + `use_span_context()`. |
| `aop/client.py`                                       | New `client.start_span(name, agent_id=..., protocol=...)` helper. |

### Phase 2 — Auto-instrumentation (commit `f0bfa57`)

| File | What it does |
|---|---|
| `aop/instrumentation/__init__.py`                     | **NEW.** `autoinstrument(targets=...)`, `uninstrument()`, `list_instrumentations()`, `set_default_client()`. Integrations table. |
| `aop/instrumentation/_common.py`                      | **NEW.** Shared helpers: `emit_event`, `ensure_context`, `mark_patched`, `safe`, ns timing, `inject_into_kwargs_headers`. |
| `aop/instrumentation/http/{requests,httpx,aiohttp,urllib,urllib3}_inst.py` | **NEW.** HTTP client wrappers; inject `traceparent`; emit `http.client.request`/`.response`/`.error`. |
| `aop/instrumentation/llm/{openai,anthropic,google_genai,mistralai,cohere,bedrock,groq,litellm,ollama}_inst.py` | **NEW.** LLM SDK wrappers; emit `llm.completion.*` with `tokens` + `cost` from `aop.pricing`. |
| `aop/instrumentation/vectordb/{pinecone,weaviate,qdrant,chromadb}_inst.py` | **NEW.** Vector-DB wrappers; emit `vectordb.query.*` etc. |
| `aop/instrumentation/frameworks/{langchain,langgraph,crewai,autogen,llamaindex,semantic_kernel}_inst.py` | **NEW.** Agent-framework callbacks; emit `framework.<lib>.*`. |
| `aop/instrumentation/db/{sqlalchemy,redis,psycopg}_inst.py` | **NEW.** DB / cache wrappers; emit `db.query.*` and `cache.command.*`. |
| `aop/instrumentation/socket_inst.py`                  | **NEW.** Opt-in raw-TCP socket tap; emits `tcp.connection.*`. |
| `aop/registry.py` (extended)                          | Pre-registers `http`, `llm`, `vectordb`, `framework`, `db`, `cache`, `tcp` protocols. |

### Phase 3 — Protocol adapters (commit `1a9d46a`)

| File | What it does |
|---|---|
| `aop/adapters/acp.py`                                 | **NEW.** ACP (IBM): discovery, REST invocation, streaming. |
| `aop/adapters/agntcy.py`                              | **NEW.** AGNTCY / Internet of Agents: DID identity, directory, connections. |
| `aop/adapters/anp.py`                                 | **NEW.** ANP: DID handshake, signed messages, routing. |
| `aop/adapters/ag_ui.py`                               | **NEW.** AG-UI: text/tool-call deltas, approvals, sessions. |
| `aop/adapters/openai_agents.py`                       | **NEW.** OpenAI Agents SDK: runs, handoffs, tool invocations. |
| `aop/adapters/feedback.py`                            | **NEW.** User feedback / eval signals (thumbs/score/edit/escalation). |
| `aop/adapters/generic.py`                             | **NEW.** Base for community-contributed adapters. |
| `aop/adapters/mcp.py` / `a2a.py` / `ap2.py`           | **EXTENDED** with notifications/subscriptions/elicitation/completion (MCP), artifact/agentcard/push (A2A), refunds/disputes/intent (AP2). |
| `aop/registry.py` (extended)                          | Pre-registers all the new protocols + extended event types. |
| `aop/client.py`                                       | New properties: `client.acp`, `.agntcy`, `.anp`, `.ag_ui`, `.openai_agents`, `.feedback`. |
| `aop/__init__.py`                                     | Re-exports all new adapter classes. |

### Phase 4 — Wire format, transports, Collector (commit `05edf89`)

| File | What it does |
|---|---|
| `aop/transport/__init__.py`                           | **NEW.** Re-exports BaseTransport, DirectTransport, BatchProcessor, HTTPJSONTransport, OTLPHTTPTransport, OTLPGRPCTransport. |
| `aop/transport/base.py`                               | **NEW.** `BaseTransport` ABC + `DirectTransport` (writes to local storage). |
| `aop/transport/batch.py`                              | **NEW.** `BatchProcessor` — async background batcher, drop-oldest, exponential backoff. |
| `aop/transport/http_json.py`                          | **NEW.** AOP-native `POST /v1/events` JSON, gzip, bearer auth. |
| `aop/transport/otlp_http.py`                          | **NEW.** OTLP/HTTP — encodes events as OTel `LogRecord` JSON; works with any OTel-compat collector. |
| `aop/transport/otlp_grpc.py`                          | **NEW.** OTLP/gRPC via the upstream `opentelemetry-exporter-otlp-proto-grpc` (lazy import). |
| `aop_collector/`                                      | **NEW PACKAGE** — the standalone Collector binary. |
| `aop_collector/__init__.py`                           | Public exports. |
| `aop_collector/__main__.py`                           | `python -m aop_collector serve [--config c.yaml \| --port 4319 --exporter ...]`. |
| `aop_collector/collector.py`                          | Top-level orchestrator wiring receivers → pipeline → exporters. |
| `aop_collector/config.py`                             | YAML/JSON config loader. |
| `aop_collector/receivers.py`                          | stdlib `http.server` receiver: `POST /v1/events` (AOP) + `POST /v1/logs` (OTLP/HTTP), bearer auth, per-IP rate limit, gzip. |
| `aop_collector/pipeline.py`                           | Receive → redact → sample → enrich → export pipeline. |
| `aop_collector/exporters.py`                          | sqlite/postgres/clickhouse/s3/stdout/OTLP-out exporters. |
| `aop_collector/examples/collector.yaml`               | Example YAML config. |
| `aop/proto/__init__.py`                               | Protobuf schema text exposed for inspection. |
| `aop/proto/aop_event.proto`                           | Protobuf schema for downstream codegen (Go/JS/Rust SDKs). |
| `aop/client.py`                                       | New `transport=` and `batch=` constructor args. URL-string transports `aop+http://`, `otlp+http://`, `otlp+grpc://`. |

### Phase 5 — Storage hardening (commit `499e980`)

| File | What it does |
|---|---|
| `aop/storage/migrations/__init__.py`                  | **NEW.** `migrate(url)`, `current_version(url)`, `list_migrations()`. |
| `aop/storage/migrations/runner.py`                    | **NEW.** Lightweight Alembic-free runner (sqlite + postgres). Maintains `aop_schema_version` table. |
| `aop/storage/migrations/versions/v0001_initial_schema.py` | **NEW.** v1.0 baseline schema. |
| `aop/storage/migrations/versions/v0002_v11_fields.py` | **NEW.** Adds v1.1 columns + critical indexes. |
| `aop/storage/migrations/versions/v0003_tenancy.py`    | **NEW.** `tenant_id` + `retention_until`. |
| `aop/storage/clickhouse.py`                           | **NEW.** ClickHouse-backed storage (MergeTree, monthly partitioning, JSON columns). |
| `aop/storage/s3.py`                                   | **NEW.** S3-compat cold archive (gzipped JSONL, partitioned by hour). Works with MinIO, R2, GCS. |
| `aop/storage/retention.py`                            | **NEW.** `apply_retention(url, max_age_days=..., tenant_id=..., dry_run=...)`. |
| `aop/storage/__init__.py`                             | Factory accepts `clickhouse://`, `clickhouse+secure://`, `s3://`. Re-exports `migrate` and `apply_retention`. |

### Phase 6 — Privacy / compliance / security (commit `7a83314`)

| File | What it does |
|---|---|
| `aop/redaction/__init__.py`                           | **NEW.** Re-exports of `redact_event`, `redact_value`, `RedactionRule`, `add_rule`. |
| `aop/redaction/rules.py`                              | **NEW.** Default rules (email, SSN, Luhn-CC, phone, JWT, OpenAI/Anthropic/AWS/GitHub keys) + sensitive-field denylist. |
| `aop/redaction/presidio.py`                           | **NEW.** Optional Microsoft Presidio bridge. |
| `aop/compliance/{gdpr,hipaa,sox,pci_dss}.py`          | **NEW.** Compliance helpers (consent tagging, right-to-erasure tombstones, PHI patterns, SOX hash-chain audit, PAN masking). |
| `aop/security/encryption.py`                          | **NEW.** AES-GCM envelope encryption (`EncryptionKey`, `EnvelopeEncryptor`). |
| `aop/security/auth.py`                                | **NEW.** `APITokenAuthenticator`, `JWTAuthenticator` (PyJWT), `Role` RBAC, `require_role` decorator. |
| `aop/security/audit.py`                               | **NEW.** Append-only `AuditLogger` with SHA-256 hash chain + `verify()`. |

### Phase 7 — Dashboard upgrade (commit `de76542`)

| File | What it does |
|---|---|
| `aop/dashboard/sse.py`                                | **NEW.** `SSEHub` — in-process pub/sub with bounded queues, 15s heartbeat. |
| `aop/dashboard/server.py`                             | **EXTENDED.** Adds `GET /api/stream` (SSE), `POST /api/ingest` (remote agent push), `GET /api/feed` (polling fallback), `require_auth` dependency reading `AOP_DASHBOARD_TOKENS`/`AOP_DASHBOARD_TOKEN`. |
| `aop/client.py`                                       | `_ship_to_transport` also publishes to the SSE hub. |

### Phase 9 — Conformance suite + SDK home (commit `0b65435`)

| File | What it does |
|---|---|
| `tests/conformance/__init__.py`                       | **NEW.** Doc string for the harness. |
| `tests/conformance/README.md`                         | **NEW.** How to run and how non-Python SDKs reuse the same JSON. |
| `tests/conformance/fixtures/events/*.json`            | **NEW (5 files).** Golden valid events. |
| `tests/conformance/fixtures/events_invalid/*.json`    | **NEW (5 files).** Events that MUST be rejected. |
| `tests/conformance/fixtures/traces/*.json`            | **NEW (1 file).** Multi-protocol trace. |
| `tests/conformance/fixtures/propagation/*.json`       | **NEW.** W3C traceparent valid + invalid vectors. |
| `tests/conformance/fixtures/registry/*.json`          | **NEW.** Built-in protocol coverage expectations. |
| `tests/conformance/test_event_validation.py`          | **NEW.** Pytest harness that round-trips every fixture. |
| `tests/conformance/test_propagation.py`               | **NEW.** Round-trips traceparent vectors through `extract`/`inject`. |
| `tests/conformance/test_registry.py`                  | **NEW.** Asserts every required protocol+event is registered. |
| `sdks/README.md`                                      | **NEW.** Reservation / instructions for non-Python SDKs. |
| `sdks/{typescript,go,rust}/PLACEHOLDER`               | **NEW.** Empty placeholders. |

### Phase 10 — Cost intelligence (commit `945a780`)

| File | What it does |
|---|---|
| `aop/pricing/__init__.py`                             | **NEW.** Public API: `compute_cost`, `estimate_cost_usd`, `register_price`, `get_price`, `Budget`, `BudgetAlert`, `BudgetExceeded`, `PriceEntry`. |
| `aop/pricing/price_book.py`                           | **NEW.** Loads `data/price_book.json`, prefix matching for versioned model names, runtime overrides. |
| `aop/pricing/data/price_book.json`                    | **NEW.** ~50 model entries across OpenAI, Anthropic, Google, Mistral, Cohere, Groq, Together, Fireworks, Bedrock. |
| `aop/pricing/budget.py`                               | **NEW.** `Budget` with cap/period/scope, multiple alert thresholds, optional `raise_on_exceed`. |
| `aop/pricing/cli.py` + `__main__.py`                  | **NEW.** `python -m aop.pricing {estimate,list,set}`. |
| `aop/__init__.py`                                     | Re-exports pricing + redaction symbols. |

---

## 4. Full directory tree (post-implementation)

```
aop/                                      # the SDK
├── __init__.py                           # public API surface
├── client.py                             # AOPClient + transport hook + start_span
├── events.py                             # build_event + protocol builders
├── exceptions.py
├── registry.py                           # Phase 0  ★ start here for protocols
├── types.py                              # AOPEvent v1.1
├── validation.py                         # uses registry
├── utils.py                              # UUID v7 + W3C trace/span id helpers
├── trace.py                              # legacy correlation_id + SpanContext ctx-var
├── propagation.py                        # Phase 1  ★ W3C TraceContext
├── span.py                               # Phase 1  ★ OTel-style Span
├── analytics.py
├── cli.py
├── adapters/
│   ├── base.py
│   ├── mcp.py / a2a.py / ap2.py          # extended in Phase 3
│   ├── acp.py / agntcy.py / anp.py       # NEW Phase 3
│   ├── ag_ui.py / openai_agents.py       # NEW Phase 3
│   ├── feedback.py / generic.py          # NEW Phase 3
├── instrumentation/                      # Phase 2  ★ autoinstrument()
│   ├── __init__.py                       # dispatcher + integrations table
│   ├── _common.py                        # shared helpers
│   ├── http/                             # requests, httpx, aiohttp, urllib, urllib3
│   ├── llm/                              # openai, anthropic, google_genai, mistralai,
│   │                                     #   cohere, bedrock, groq, litellm, ollama
│   ├── vectordb/                         # pinecone, weaviate, qdrant, chromadb
│   ├── frameworks/                       # langchain, langgraph, crewai, autogen,
│   │                                     #   llamaindex, semantic_kernel
│   ├── db/                               # sqlalchemy, redis, psycopg
│   └── socket_inst.py                    # opt-in raw TCP tap
├── transport/                            # Phase 4  ★ pluggable transports
│   ├── base.py / batch.py
│   ├── http_json.py                      # AOP-native /v1/events
│   ├── otlp_http.py / otlp_grpc.py       # OTLP-compatible
├── proto/                                # Phase 4  ★ wire format
│   ├── __init__.py
│   └── aop_event.proto
├── storage/
│   ├── base.py / sqlite.py / postgresql.py / memory.py     # pre-existing
│   ├── clickhouse.py                     # Phase 5
│   ├── s3.py                             # Phase 5
│   ├── retention.py                      # Phase 5
│   └── migrations/                       # Phase 5  ★ schema migrations
│       ├── runner.py
│       └── versions/
│           ├── v0001_initial_schema.py
│           ├── v0002_v11_fields.py
│           └── v0003_tenancy.py
├── exporters/                            # pre-existing (json/csv/toon/otel/prometheus)
├── dashboard/
│   ├── server.py                         # extended in Phase 7
│   ├── sse.py                            # Phase 7  ★ real-time push hub
│   ├── websocket.py                      # legacy poller (kept for back-compat)
│   ├── frontend/                         # current static index.html
│   └── static/
├── redaction/                            # Phase 6
│   ├── rules.py
│   └── presidio.py
├── compliance/                           # Phase 6
│   ├── gdpr.py / hipaa.py / sox.py / pci_dss.py
├── security/                             # Phase 6
│   ├── encryption.py / auth.py / audit.py
└── pricing/                              # Phase 10  ★ token cost
    ├── price_book.py / budget.py
    ├── cli.py / __main__.py
    └── data/price_book.json

aop_collector/                            # Phase 4  ★ standalone Collector
├── collector.py / __main__.py
├── config.py / receivers.py / pipeline.py / exporters.py
└── examples/collector.yaml

tests/
├── conformance/                          # Phase 9
│   ├── README.md
│   ├── test_event_validation.py
│   ├── test_propagation.py
│   ├── test_registry.py
│   └── fixtures/
│       ├── events/                       # 5 valid files
│       ├── events_invalid/               # 5 files that must be rejected
│       ├── traces/                       # multi-protocol trace
│       ├── propagation/                  # traceparent vectors
│       └── registry/                     # registry coverage spec
└── (existing test_*.py from before this work)

sdks/                                     # Phase 9 placeholder
├── README.md
├── typescript/PLACEHOLDER
├── go/PLACEHOLDER
└── rust/PLACEHOLDER

docs/
├── specification/event-schema-v1.0.md    # pre-existing
└── specification/event-schema-v1.1.md    # NEW Phase 0
```

---

## 5. Public API at a glance

```python
import aop

# Core
client = aop.AOPClient(storage="sqlite:///aop.db",
                       transport="otlp+http://collector.local",
                       batch=True)
client.log_event({...})

# Distributed tracing (Phase 1)
with client.start_span("plan", agent_id="my-agent", protocol="mcp",
                       attributes={"step": 1}) as span:
    ...
ctx = aop.SpanContext(trace_id="...", span_id="...")
aop.inject_trace_context(headers, ctx)

# Auto-instrumentation (Phase 2)
aop.autoinstrument()                       # patches everything detected
aop.autoinstrument(targets=["openai", "requests"])

# Protocol adapters (Phase 3)
client.mcp.log_tool_call(...)
client.a2a.log_task_assigned(...)
client.acp.log_invocation_started(...)
client.agntcy.log_identity_resolved(...)
client.anp.log_handshake_started(...)
client.ag_ui.log_text_delta(...)
client.openai_agents.log_run_started(...)
client.feedback.log_thumb(...)

# Custom protocol (Phase 0 + 3)
aop.register_protocol(aop.ProtocolSpec(name="myproto",
                                       event_types=frozenset({"myproto.foo.started"})))

# Storage hardening (Phase 5)
aop.storage.migrate("sqlite:///aop.db")
aop.storage.apply_retention("sqlite:///aop.db", max_age_days=30)

# Redaction & compliance (Phase 6)
clean = aop.redact_event(ev)
from aop.compliance.gdpr import erase_user_data
from aop.security import EnvelopeEncryptor, EncryptionKey
key = EncryptionKey.generate(); EnvelopeEncryptor(key).encrypt(ev)

# Cost intelligence (Phase 10)
cost = aop.compute_cost(provider="openai", model="gpt-4o-mini",
                        prompt_tokens=1000, completion_tokens=200)
budget = aop.Budget(name="daily", cap_amount=10.0, period="day")
budget.add_alert(0.8, lambda b, spent: print(f"{b.name} 80% used"))
budget.observe(ev)
```

CLI tools added:

- `python -m aop_collector serve --port 4319 --exporter sqlite:aop.db`
- `python -m aop.pricing estimate --provider openai --model gpt-4o-mini --prompt 1000 --completion 200`
- `python -m aop.pricing list`

---

## 6. What is **NOT** done (scope still open)

The original plan had 12 phases. We executed **0, 1, 2, 3, 4, 5, 6, 7, 9, 10**. The
following are deliberately deferred:

### Phase 8 — Sampling, perf, batching polish (NOT done)
- Tail-based sampling in the collector
- Adaptive sampling
- Real `pytest-benchmark` perf suite
- Bounded-queue back-pressure metrics surfaced to Prometheus
- Status: `BatchProcessor` exists (Phase 4) but no benchmark/sampler wiring beyond `TraceIdRatioSampler`.

### Phase 9 — Multi-language SDKs (Python only here)
- `sdks/typescript/`, `sdks/go/`, `sdks/rust/` are placeholders only.
- Conformance fixtures exist and are language-agnostic — they are the
  contract any SDK must satisfy.

### Phase 11 — Evaluation / drift / replay (NOT done)
- LangSmith / Inspect / promptfoo / ragas integrations
- Trace replay against new model
- Statistical drift detection

### Phase 12 — Launch readiness (NOT done)
- External security audit
- Load test (100K eps single node)
- Reference Helm chart / Terraform
- Versioning policy + Buf for the proto
- Docusaurus docs site

### Smaller items still open inside completed phases

- **Phase 0:** the legacy `MCPEventType` / `A2AEventType` / `AP2EventType`
  classes still exist for back-compat. A future cleanup can drop them in
  favor of `aop.registry.get_protocol(...)`.
- **Phase 2:** body capture for HTTP / LLM is **off**. A `capture_bodies=True`
  flag on `autoinstrument()` would be a 1-day add.
- **Phase 4:** OTLP/gRPC transport relies on the upstream OTel SDK at runtime;
  no native protobuf codegen yet.
- **Phase 5:** ClickHouse retention uses `ALTER TABLE ... DELETE`, which is
  async on CH; no callback-based completion notification.
- **Phase 6:** `cryptography` and `pyjwt` are imported lazily; CI should
  install them for the security tests to actually exercise envelope
  encryption.
- **Phase 7:** the dashboard frontend is still the embedded `index.html`.
  It does NOT yet consume `/api/stream`; only the backend is ready.
  Replacing the frontend with a Next.js/Vite build is its own task.
- **Phase 10:** prices in `data/price_book.json` are best-effort May-2026
  list prices. There is no CI job yet that re-scrapes upstream pricing
  pages; a `scripts/update_prices.py` would close the loop.

---

## 7. Things a new agent should do FIRST

In strict priority order:

1. **Run the existing tests.** Nothing has been executed on this branch.
   ```
   pip install -e .
   pytest tests/ -x -q
   pytest tests/conformance -x -q
   ```
   Expect at least these likely failures to investigate:
   - Tests that hard-coded `version == "1.0"` may break on the bump to
     `"1.1"`.
   - Tests that asserted `SUPPORTED_PROTOCOLS == ["mcp", "a2a", "ap2"]`
     may break because the registry now includes the auto-instrumentation
     namespaces.
   - Anything importing `Protocol` enum and treating it as the source of
     truth — should now use `aop.supported_protocols()`.
2. **Run the import smoke test.** `python -c "import aop; print(aop.__version__)"`
   should print `1.1.0`. If it doesn't, there is a circular import to fix
   in the `__init__.py` chain (the most likely culprit is the new
   `aop.dashboard.sse` import inside `client._ship_to_transport`; it is
   intentionally inside a function to avoid a top-level cycle).
3. **mypy the new modules.** `mypy aop/registry.py aop/propagation.py aop/span.py aop/transport aop/instrumentation aop/pricing`.
4. **End-to-end sanity:**
   ```
   python -m aop_collector serve --port 4319 --exporter stdout &
   python -c "
   import aop
   c = aop.AOPClient(storage='memory', transport='aop+http://localhost:4319')
   with c.start_span('demo', agent_id='a1', protocol='mcp') as s: pass
   c.close()
   "
   ```
   You should see two events (started/completed) on stdout from the
   collector.
5. **Verify SSE push:** `curl -N http://localhost:8000/api/stream` while
   the dashboard runs, then in another terminal log a few events — they
   should arrive within 1 second.
6. **Stress-test redaction:** run a fixture event containing fake API
   keys / SSNs through `aop.redact_event` and confirm `<redacted>`
   replacement.

---

## 8. Things to watch out for (footguns + design notes)

- **Validation skip in instrumentation.** `_common.emit_event(...)` calls
  `client.log_event(ev, validate=False)`. This is intentional — the
  instrumentation events use namespaces like `framework.langchain.llm.start`
  that are pre-registered; validation off is a perf win. If you ever
  see a malformed instrumentation event, fix the helper, don't toggle
  validation back on globally.
- **Span events use `validate=False` too.** Same reason — `<protocol>.<name>.started`
  is dynamic and won't be in any built-in event-type set unless it
  matches `<protocol>.x.<...>` or `<protocol>.custom.<org>.<...>`.
- **W3C `traceparent` injection.** Performed in every HTTP wrapper. If
  someone reports duplicate headers, check the wrapper for the library —
  some clients pass `headers` as an immutable mapping; we always copy
  before mutating.
- **`aop.dashboard.sse.publish` is called in-process.** It does NOT cross
  process boundaries. To get fan-out across multiple dashboard replicas
  you will need a Redis Pub/Sub bridge — left for a later phase.
- **Collector `tcp` is opt-in.** The `socket` integration is not enabled
  by `autoinstrument(all=True)` because it is high-volume and privacy
  relevant. Users must call `aop.autoinstrument(targets=["socket"])`
  explicitly.
- **PG pooling already existed.** The original analysis claimed it was
  missing — it wasn't. `aop/storage/postgresql.py` uses
  `psycopg2.pool.ThreadedConnectionPool`. We kept it as-is and only
  added migrations + retention.
- **Pricing prefix matching.** `get_price("openai", "gpt-4o-mini-2024-07-18")`
  falls back to the `gpt-4o-mini` entry. This means long versioned model
  names "just work" but an exact match always wins.
- **Budget reset semantics.** `Budget.observe()` rolls the period
  automatically when more than `period` time has elapsed since the last
  reset. There is no scheduler — the rollover happens lazily on the next
  observe call.

---

## 9. Quick links to the most important commits

| Phase | SHA | Files added/changed |
|---|---|---|
| 0 + 1 | `ee45fc9` | 13 |
| 2 | `f0bfa57` | 35 |
| 3 | `1a9d46a` | 13 |
| 4 | `05edf89` | 17 |
| 5 | `499e980` | 10 |
| 6 | `7a83314` | 12 |
| 7 | `de76542` | 3 |
| 9 | `0b65435` | 22 |
| 10 | `945a780` | 7 |

`git log --stat <SHA>` for the full diff per phase.

---

## 10. TL;DR for the next agent

> AOP just grew from a "manual MCP event logger" into a real protocol:
> registry-based, distributed-tracing-aware, auto-instrumenting, with a
> wire format, a collector, hardened storage, redaction/auth, real-time
> push, conformance fixtures, and cost intelligence. **Run the tests
> first.** The most likely breakage is in pre-existing tests that
> hard-coded the old 3-protocol list or `version == "1.0"`. After tests
> pass, the next high-value work items are:
>
> 1. Replace the embedded dashboard `index.html` with a real frontend
>    that consumes `/api/stream`.
> 2. Build the TypeScript SDK against `tests/conformance/fixtures/`.
> 3. Wire a CI job that re-scrapes LLM provider pricing into
>    `aop/pricing/data/price_book.json`.
> 4. Add tail-based sampling to the collector pipeline.
