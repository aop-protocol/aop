# AOP Conformance Suite

Language-agnostic test fixtures + a Python harness validating any AOP
implementation against the v1.1 spec.

## Layout

```
fixtures/
  events/              valid events that MUST validate
  events_invalid/      events that MUST be rejected
  traces/              full multi-event traces
  propagation/         W3C traceparent vectors
  registry/            built-in protocol expectations
```

## Running the Python harness

```
pytest tests/conformance
```

## Re-using the fixtures from non-Python SDKs

Each fixture file is self-contained JSON. Other-language SDKs (TypeScript /
Go / Rust) are expected to load these same files and run language-native
test cases against them. This is what gives us cross-language wire
compatibility.

A future Phase 9 deliverable will add scaffolding for Node, Go, and Rust
SDK packages. They are intentionally not included in this Python-only
milestone, but the fixtures here are the source of truth they will share.
