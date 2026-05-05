"""AOP wire-format definitions.

We deliberately ship two transports:

  • aop-native JSON (HTTPJSONTransport)  — simplest possible, easy to
    inspect, no codegen required.
  • OTLP-compatible (OTLPHTTPTransport / OTLPGRPCTransport) — encodes AOP
    events as OTel ``LogRecord`` messages so any OTLP-compatible backend
    accepts them with no extra work.

The Protobuf schema below is provided for completeness for downstream
consumers who want strict binary framing. We keep a hand-written stub
instead of generated code so this module imports without ``protobuf`` as
a hard dep.
"""

from __future__ import annotations

# .proto source kept under proto/aop_event.proto for future codegen.
# At runtime, the JSON-on-the-wire path is canonical.

PROTO_SCHEMA = """
syntax = "proto3";
package aop.v1;

message AOPEvent {
  string id = 1;
  string version = 2;
  string timestamp = 3;
  string agent_id = 4;
  string instance_id = 5;
  string protocol = 6;
  string event_type = 7;
  string correlation_id = 8;
  string parent_id = 9;
  string severity = 10;
  int64 duration_ms = 11;
  bytes data = 12;          // JSON-encoded
  bytes metadata = 13;      // JSON-encoded
  bytes error = 14;         // JSON-encoded
  string trace_id = 15;
  string span_id = 16;
  string parent_span_id = 17;
  bytes resource = 18;      // JSON-encoded
  bytes attributes = 19;    // JSON-encoded
  bytes tokens = 20;        // JSON-encoded
  bytes cost = 21;          // JSON-encoded
}

message ExportEventsRequest {
  repeated AOPEvent events = 1;
  string schema_version = 2;
}

message ExportEventsResponse {
  int32 accepted = 1;
  int32 rejected = 2;
}

service AOPCollector {
  rpc ExportEvents(ExportEventsRequest) returns (ExportEventsResponse);
}
"""

__all__ = ["PROTO_SCHEMA"]
