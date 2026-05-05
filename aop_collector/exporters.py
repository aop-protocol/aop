"""Collector-side exporters."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

_log = logging.getLogger("aop.collector.exporters")


def build_exporter(spec: Dict[str, Any]) -> Any:
    """Build a collector exporter from a config dict."""
    type_ = spec["type"]
    opts = spec.get("options", {}) or {}
    if type_ in ("sqlite", "postgres", "memory"):
        from aop.storage import create_storage
        url = opts.get("url") or {
            "sqlite": "sqlite:///aop_collector.db",
            "memory": "memory",
            "postgres": "postgresql://localhost/aop",
        }[type_]
        storage = create_storage(url)
        return _StorageExporter(storage)
    if type_ == "clickhouse":
        from aop.storage.clickhouse import ClickHouseStorage
        ch = ClickHouseStorage(**opts)
        return _StorageExporter(ch)
    if type_ == "s3":
        from aop.storage.s3 import S3ArchiveStorage
        return _StorageExporter(S3ArchiveStorage(**opts))
    if type_ in ("otlp_http", "otlp+http"):
        from aop.transport.otlp_http import OTLPHTTPTransport
        return OTLPHTTPTransport(**opts)
    if type_ in ("otlp_grpc", "otlp+grpc"):
        from aop.transport.otlp_grpc import OTLPGRPCTransport
        return OTLPGRPCTransport(**opts)
    if type_ == "stdout":
        return _StdoutExporter()
    raise ValueError(f"unknown exporter type: {type_!r}")


class _StorageExporter:
    """Adapter: BaseStorage → BaseTransport interface."""

    def __init__(self, storage: Any) -> None:
        self._storage = storage

    def export(self, events: List[Dict[str, Any]]) -> None:
        for ev in events:
            try:
                self._storage.log_event(ev)
            except Exception as e:
                _log.debug("storage exporter failed: %s", e)

    def shutdown(self, timeout_s: float = 5.0) -> None:
        try:
            self._storage.close()
        except Exception:
            pass


class _StdoutExporter:
    def export(self, events: List[Dict[str, Any]]) -> None:
        import json, sys
        for e in events:
            print(json.dumps(e, default=str), file=sys.stdout, flush=True)

    def shutdown(self, timeout_s: float = 5.0) -> None:
        pass
