"""AOP Spec Conformance Suite.

This package contains language-agnostic JSON fixtures and a Python test
harness that validates an AOP implementation against the v1.1 spec.

The fixture layout:

    tests/conformance/fixtures/
        events/                 — golden event documents (must validate)
        events_invalid/         — events that MUST be rejected
        traces/                 — full multi-event traces
        propagation/            — W3C traceparent vectors
        registry/               — protocol-registry expectations

Other-language SDKs (TS, Go, Rust) load the same JSON files and run
language-native tests against them — guaranteeing wire-level compatibility
across implementations.
"""
