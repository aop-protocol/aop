"""OTLP/HTTP transport — POST AOP events as OTel ``LogRecord`` JSON.

We piggyback on the OpenTelemetry log signal: every AOP event is encoded as
an OTel ``LogRecord`` whose ``body`` is the AOP event JSON and whose
attributes carry the AOP-specific keys. This makes any OTLP-compatible
collector (the upstream OpenTelemetry Collector, Datadog, Honeycomb,
Tempo, Grafana Cloud, ...) accept AOP events with no protobuf bridge needed.

Specifics:
  • Endpoint: <base>/v1/logs (POST)
  • Content-Type: application/json (the OTLP/HTTP "JSON" encoding)
  • Body: ``{"resourceLogs": [{...}]}``
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import BaseTransport

_log = logging.getLogger("aop.transport.otlp_http")

_SEVERITY_MAP = {"error": 17, "warn": 13, "info": 9, "debug": 5}


class OTLPHTTPTransport(BaseTransport):
    def __init__(
        self,
        endpoint: str,
        *,
        token: Optional[str] = None,
        timeout_s: float = 5.0,
        max_retries: int = 3,
        backoff_s: float = 0.5,
        service_name: str = "aop",
    ) -> None:
        self.endpoint = endpoint.rstrip("/") + "/v1/logs"
        self.token = token or os.environ.get("OTEL_EXPORTER_OTLP_HEADERS")
        self.timeout = timeout_s
        self.retries = max_retries
        self.backoff = backoff_s
        self.service_name = service_name

    def export(self, events: List[Dict[str, Any]]) -> None:
        if not events:
            return
        body = json.dumps(self._envelope(events)).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = (
                self.token if self.token.startswith("Bearer") else f"Bearer {self.token}"
            )

        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(self.endpoint, data=body,
                                             headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if 200 <= resp.status < 300:
                        return
                    last_err = RuntimeError(f"OTLP returned HTTP {resp.status}")
            except (urllib.error.URLError, OSError, RuntimeError) as e:
                last_err = e
            time.sleep(self.backoff * (2 ** attempt))
        _log.warning("OTLP/HTTP failed after %d retries: %s", self.retries, last_err)

    # ------------------------------------------------------------------

    def _envelope(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        log_records = [self._to_log_record(ev) for ev in events]
        return {
            "resourceLogs": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": self.service_name}},
                        {"key": "telemetry.sdk.name", "value": {"stringValue": "aop"}},
                        {"key": "telemetry.sdk.language", "value": {"stringValue": "python"}},
                    ]
                },
                "scopeLogs": [{
                    "scope": {"name": "aop.transport.otlp_http", "version": "1.1"},
                    "logRecords": log_records,
                }],
            }]
        }

    def _to_log_record(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        rec: Dict[str, Any] = {
            "timeUnixNano": _ts_to_nanos(ev.get("timestamp")),
            "severityNumber": _SEVERITY_MAP.get(ev.get("severity") or "info", 9),
            "severityText": (ev.get("severity") or "INFO").upper(),
            "body": {"stringValue": json.dumps(ev, default=str)},
            "attributes": _to_kv_list({
                "aop.event_type": ev.get("event_type"),
                "aop.protocol": ev.get("protocol"),
                "aop.agent_id": ev.get("agent_id"),
                "aop.event_id": ev.get("id"),
                "aop.duration_ms": ev.get("duration_ms"),
            }),
        }
        if ev.get("trace_id"):
            rec["traceId"] = ev["trace_id"]
        if ev.get("span_id"):
            rec["spanId"] = ev["span_id"]
        return rec


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _ts_to_nanos(ts: Any) -> str:
    if not ts or not isinstance(ts, str):
        return str(int(time.time() * 1e9))
    try:
        from datetime import datetime, timezone
        s = ts.rstrip("Z")
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        return str(int(dt.timestamp() * 1e9))
    except Exception:
        return str(int(time.time() * 1e9))


def _to_kv_list(d: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, bool):
            out.append({"key": k, "value": {"boolValue": v}})
        elif isinstance(v, int):
            out.append({"key": k, "value": {"intValue": str(v)}})
        elif isinstance(v, float):
            out.append({"key": k, "value": {"doubleValue": v}})
        else:
            out.append({"key": k, "value": {"stringValue": str(v)}})
    return out
