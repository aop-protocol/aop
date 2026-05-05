"""Collector pipeline: receive → redact → sample → enrich → export."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Callable, Dict, List, Optional

_log = logging.getLogger("aop.collector.pipeline")


# ---------------------------------------------------------------------------
# Processors
# ---------------------------------------------------------------------------

class Processor:
    name: str = "noop"

    def process(self, ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return ev


class RedactingProcessor(Processor):
    """Run aop.redaction.redact_event on every event."""

    name = "redact"

    def process(self, ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            from aop.redaction import redact_event
            return redact_event(ev)
        except Exception:
            return ev


class TraceIdRatioSampler(Processor):
    name = "sample.trace_id_ratio"

    def __init__(self, ratio: float) -> None:
        self.ratio = max(0.0, min(1.0, ratio))

    def process(self, ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.ratio >= 1.0:
            return ev
        if self.ratio <= 0.0:
            return None
        trace_id = ev.get("trace_id") or ev.get("correlation_id") or ev.get("id") or ""
        if not trace_id:
            return ev
        # deterministic hash → in [0, 1)
        h = int(hashlib.md5(trace_id.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
        return ev if h < self.ratio else None


class AlwaysOffSampler(Processor):
    name = "sample.always_off"
    def process(self, ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None


class ResourceEnricher(Processor):
    name = "enrich.resource"

    def __init__(self, resource: Dict[str, Any]) -> None:
        self._resource = resource

    def process(self, ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self._resource:
            return ev
        existing = ev.get("resource") or {}
        merged = {**self._resource, **existing}  # event-supplied wins
        ev["resource"] = merged
        return ev


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class ProcessorChain:
    def __init__(self, processors: List[Processor]) -> None:
        self.processors = processors

    def run(self, ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for p in self.processors:
            ev = p.process(ev)  # type: ignore[assignment]
            if ev is None:
                return None
        return ev


class Pipeline:
    """One full receive→process→export pipeline."""

    def __init__(
        self,
        chain: ProcessorChain,
        exporters: List[Any],
    ) -> None:
        self.chain = chain
        self.exporters = exporters

    def ingest(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        accepted = 0
        dropped = 0
        out_batch: List[Dict[str, Any]] = []
        for ev in events:
            try:
                processed = self.chain.run(ev)
            except Exception as e:
                _log.warning("pipeline processor failed: %s", e)
                processed = ev
            if processed is None:
                dropped += 1
                continue
            out_batch.append(processed)
            accepted += 1
        for exporter in self.exporters:
            try:
                exporter.export(out_batch)
            except Exception as e:
                _log.warning("exporter %s failed: %s", type(exporter).__name__, e)
        return {"accepted": accepted, "dropped": dropped}
