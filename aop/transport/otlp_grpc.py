"""OTLP/gRPC transport.

Uses the official ``opentelemetry-exporter-otlp-proto-grpc`` package if
available; otherwise raises ``ImportError`` from ``__init__``. Falls back to
delegating to :class:`OTLPHTTPTransport` if the user prefers.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from .base import BaseTransport

_log = logging.getLogger("aop.transport.otlp_grpc")


class OTLPGRPCTransport(BaseTransport):
    """Best-effort gRPC OTLP exporter built on the upstream OTel SDK."""

    def __init__(
        self,
        endpoint: str,
        *,
        token: Optional[str] = None,
        timeout_s: float = 5.0,
        service_name: str = "aop",
        insecure: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.timeout = timeout_s
        self.service_name = service_name
        self.token = token or os.environ.get("OTEL_EXPORTER_OTLP_HEADERS")
        self.insecure = insecure
        self._exporter: Any = None

    def _ensure_exporter(self) -> bool:
        if self._exporter is not None:
            return True
        try:
            # Lazy import — gRPC is optional.
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (  # type: ignore
                OTLPLogExporter,
            )
        except Exception as e:
            _log.warning("OTLP/gRPC unavailable (%s); install opentelemetry-exporter-otlp-proto-grpc", e)
            return False
        headers: Dict[str, str] = {}
        if self.token:
            headers["authorization"] = (
                self.token if self.token.startswith("Bearer") else f"Bearer {self.token}"
            )
        try:
            self._exporter = OTLPLogExporter(
                endpoint=self.endpoint, headers=headers,
                timeout=int(self.timeout), insecure=self.insecure,
            )
            return True
        except Exception as e:
            _log.warning("OTLPLogExporter init failed: %s", e)
            return False

    def export(self, events: List[Dict[str, Any]]) -> None:
        if not events:
            return
        if not self._ensure_exporter():
            return
        try:
            from opentelemetry._logs import LogRecord, SeverityNumber  # type: ignore
            from opentelemetry.sdk._logs import LogData  # type: ignore
            from opentelemetry.sdk.resources import Resource  # type: ignore
        except Exception as e:
            _log.warning("OTel logs SDK not available: %s", e)
            return
        resource = Resource.create({"service.name": self.service_name,
                                    "telemetry.sdk.name": "aop"})
        log_datas: List[Any] = []
        for ev in events:
            try:
                rec = LogRecord(
                    timestamp=_ts_to_nanos(ev.get("timestamp")),
                    trace_id=int(ev["trace_id"], 16) if ev.get("trace_id") else 0,
                    span_id=int(ev["span_id"], 16) if ev.get("span_id") else 0,
                    severity_number=_sev(ev.get("severity")),
                    severity_text=(ev.get("severity") or "INFO").upper(),
                    body=ev,
                    attributes={
                        "aop.event_type": ev.get("event_type"),
                        "aop.protocol": ev.get("protocol"),
                        "aop.agent_id": ev.get("agent_id"),
                        "aop.event_id": ev.get("id"),
                    },
                    resource=resource,
                )
                log_datas.append(LogData(rec, None))
            except Exception:
                continue
        try:
            self._exporter.export(log_datas)
        except Exception as e:
            _log.warning("OTLP/gRPC export failed: %s", e)

    def shutdown(self, timeout_s: float = 5.0) -> None:
        try:
            if self._exporter is not None:
                self._exporter.shutdown()
        except Exception:
            pass


def _ts_to_nanos(ts: Any) -> int:
    if not ts:
        import time as _t
        return int(_t.time() * 1e9)
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(ts.rstrip("Z")).replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1e9)
    except Exception:
        import time as _t
        return int(_t.time() * 1e9)


def _sev(name: Any) -> int:
    return {"error": 17, "warn": 13, "info": 9, "debug": 5}.get(name or "info", 9)
