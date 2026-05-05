"""Top-level Collector that wires receivers, pipeline, and exporters."""

from __future__ import annotations

import logging
import signal
import threading
import time
from typing import List

from .config import CollectorConfig, load_config
from .pipeline import (
    AlwaysOffSampler,
    Pipeline,
    Processor,
    ProcessorChain,
    RedactingProcessor,
    ResourceEnricher,
    TraceIdRatioSampler,
)
from .receivers import HTTPReceiver
from .exporters import build_exporter

_log = logging.getLogger("aop.collector")


class Collector:
    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self.pipeline = self._build_pipeline()
        self.receivers: List[HTTPReceiver] = []
        for rcfg in config.receivers:
            self.receivers.append(HTTPReceiver(rcfg, on_events=self.pipeline.ingest))
        self._stop = threading.Event()

    @classmethod
    def from_yaml(cls, path: str) -> "Collector":
        return cls(load_config(path))

    def _build_pipeline(self) -> Pipeline:
        proc_cfg = self.config.processors
        chain: List[Processor] = []

        if proc_cfg.redact:
            chain.append(RedactingProcessor())

        if proc_cfg.sampler == "always_off":
            chain.append(AlwaysOffSampler())
        elif proc_cfg.sampler == "trace_id_ratio":
            chain.append(TraceIdRatioSampler(proc_cfg.sampler_ratio))

        if proc_cfg.enrich_resource:
            chain.append(ResourceEnricher(proc_cfg.enrich_resource))

        exporters = []
        if not self.config.exporters:
            # default: stdout
            exporters.append(build_exporter({"type": "stdout"}))
        else:
            for e in self.config.exporters:
                exporters.append(build_exporter({"type": e.type, "options": e.options}))

        return Pipeline(ProcessorChain(chain), exporters)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def serve(self, *, block: bool = True) -> None:
        for r in self.receivers:
            r.serve()
        if not block:
            return
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except (ValueError, OSError):
            # not in main thread; caller is responsible for shutdown
            pass
        while not self._stop.is_set():
            time.sleep(0.5)
        self.shutdown()

    def shutdown(self) -> None:
        self._stop.set()
        for r in self.receivers:
            try:
                r.shutdown()
            except Exception:
                pass

    def _handle_signal(self, signum: int, frame) -> None:  # type: ignore[no-untyped-def]
        _log.info("aop-collector shutting down (signal %s)", signum)
        self._stop.set()
