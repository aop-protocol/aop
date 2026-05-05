# Multi-language SDK home

This directory is reserved for the non-Python AOP SDKs that will be built
out in future milestones. The conformance fixtures under
`tests/conformance/fixtures/` are the source of truth they all consume.

Planned packages:

- `sdks/typescript/`   `@aop-protocol/sdk` (Node + browser)
- `sdks/go/`           `github.com/aop-protocol/aop-go`
- `sdks/rust/`         `aop` crate

Per the current scope of work, the Python SDK is the only language
implementation in this milestone. The directories below are placeholders so
the conformance test harness can locate language-native runners when they
arrive.
