"""HTTP receiver implementations.

Pure stdlib (``http.server``) so the collector starts with zero deps.
"""

from __future__ import annotations

import gzip
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

from .config import ReceiverConfig

_log = logging.getLogger("aop.collector.receiver")


class _RateLimiter:
    def __init__(self, per_minute: Optional[int]) -> None:
        self._per_min = per_minute
        self._buckets: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        if not self._per_min:
            return True
        now = time.time()
        cutoff = now - 60
        with self._lock:
            bucket = self._buckets.setdefault(key, [])
            bucket[:] = [t for t in bucket if t > cutoff]
            if len(bucket) >= self._per_min:
                return False
            bucket.append(now)
            return True


class HTTPReceiver:
    """Multi-threaded HTTP receiver supporting POST /v1/events and /v1/logs."""

    def __init__(
        self,
        config: ReceiverConfig,
        on_events: Callable[[List[Dict[str, Any]]], None],
    ) -> None:
        self._cfg = config
        self._on_events = on_events
        self._tokens: Set[str] = set(config.auth_tokens or [])
        self._rate = _RateLimiter(config.rate_limit_per_minute)
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def serve(self) -> None:
        cfg = self._cfg
        receiver = self
        tokens = self._tokens
        rate = self._rate
        on_events = self._on_events

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: Any) -> None:  # quiet logs
                _log.debug(fmt, *args)

            def _bad(self, status: int, msg: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": msg}).encode())

            def _ok(self, payload: Dict[str, Any]) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def do_GET(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                if path == "/healthz":
                    self._ok({"status": "ok"})
                else:
                    self._bad(404, "not found")

            def do_POST(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                if path not in ("/v1/events", "/v1/logs"):
                    return self._bad(404, "unknown path")

                # auth
                if tokens:
                    auth = self.headers.get("Authorization", "")
                    if not auth.startswith("Bearer "):
                        return self._bad(401, "missing bearer token")
                    if auth.split(" ", 1)[1] not in tokens:
                        return self._bad(403, "invalid token")

                # rate limit by client address
                if not rate.allow(self.client_address[0]):
                    return self._bad(429, "rate limit exceeded")

                # body
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(length) if length > 0 else b""
                    if self.headers.get("Content-Encoding", "").lower() == "gzip":
                        raw = gzip.decompress(raw)
                    payload = json.loads(raw.decode("utf-8")) if raw else {}
                except Exception as e:
                    return self._bad(400, f"invalid body: {e}")

                if path == "/v1/events":
                    events = payload.get("events") or []
                else:  # /v1/logs (OTLP/HTTP JSON)
                    events = receiver._parse_otlp_logs(payload)

                if not isinstance(events, list):
                    return self._bad(400, "expected events to be a list")

                try:
                    on_events(events)
                except Exception as e:
                    _log.warning("on_events callback failed: %s", e)
                    return self._bad(500, "ingest failed")

                self._ok({"accepted": len(events)})

        server = ThreadingHTTPServer((cfg.host, cfg.port), Handler)
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever, daemon=True)
        self._thread.start()
        _log.info("aop-collector listening on http://%s:%d", cfg.host, cfg.port)

    def shutdown(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()

    # ------------------------------------------------------------------
    # OTLP/HTTP JSON parsing
    # ------------------------------------------------------------------
    def _parse_otlp_logs(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for rl in payload.get("resourceLogs", []):
            for sl in rl.get("scopeLogs", []):
                for rec in sl.get("logRecords", []):
                    body = rec.get("body") or {}
                    body_str = body.get("stringValue") if isinstance(body, dict) else None
                    if body_str:
                        try:
                            events.append(json.loads(body_str))
                            continue
                        except Exception:
                            pass
                    # fall back to attribute-derived event
                    attrs = {a.get("key"): _otlp_value(a.get("value")) for a in rec.get("attributes", [])}
                    if attrs.get("aop.event_type"):
                        events.append({
                            "id": attrs.get("aop.event_id") or "",
                            "version": "1.1",
                            "timestamp": str(rec.get("timeUnixNano") or ""),
                            "agent_id": attrs.get("aop.agent_id") or "unknown",
                            "instance_id": attrs.get("aop.event_id") or "",
                            "protocol": attrs.get("aop.protocol") or "unknown",
                            "event_type": attrs.get("aop.event_type"),
                        })
        return events


def _otlp_value(v: Any) -> Any:
    if not isinstance(v, dict):
        return v
    for k, val in v.items():
        if k == "intValue":
            try:
                return int(val)
            except Exception:
                return val
        return val
    return None
