"""Background async batch processor.

Buffers events, coalesces up to ``max_batch_size`` (or ``flush_interval_s``
seconds, whichever first), drops oldest on overflow, and ships through a
delegate transport.

Designed to be safe to shutdown at process exit and to never block the
calling thread on the wire.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Any, Dict, List, Optional

from .base import BaseTransport

_log = logging.getLogger("aop.transport.batch")


class BatchProcessor(BaseTransport):
    def __init__(
        self,
        delegate: BaseTransport,
        *,
        max_queue_size: int = 4096,
        max_batch_size: int = 256,
        flush_interval_s: float = 1.0,
        on_drop: Optional[Any] = None,
    ) -> None:
        self._delegate = delegate
        self._queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=max_queue_size)
        self._max_batch = max_batch_size
        self._flush_int = flush_interval_s
        self._on_drop = on_drop
        self._stopped = threading.Event()
        self._dropped = 0
        self._exported = 0
        self._thread = threading.Thread(target=self._loop, name="aop-batch", daemon=True)
        self._thread.start()

    # -- BaseTransport interface ----------------------------------------

    def export(self, events: List[Dict[str, Any]]) -> None:
        for ev in events:
            self._enqueue(ev)

    def shutdown(self, timeout_s: float = 5.0) -> None:
        self._stopped.set()
        self._thread.join(timeout=timeout_s)
        # final flush
        self._drain_and_export()
        try:
            self._delegate.shutdown(timeout_s=timeout_s)
        except Exception:
            pass

    # -- internals -------------------------------------------------------

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "queued": self._queue.qsize(),
            "exported": self._exported,
            "dropped": self._dropped,
        }

    def _enqueue(self, ev: Dict[str, Any]) -> None:
        try:
            self._queue.put_nowait(ev)
        except queue.Full:
            # drop-oldest semantics
            try:
                _ = self._queue.get_nowait()
                self._queue.put_nowait(ev)
                self._dropped += 1
                if self._on_drop is not None:
                    try:
                        self._on_drop(ev)
                    except Exception:
                        pass
            except Exception:
                self._dropped += 1

    def _loop(self) -> None:
        while not self._stopped.is_set():
            time.sleep(self._flush_int)
            self._drain_and_export()

    def _drain_and_export(self) -> None:
        batch: List[Dict[str, Any]] = []
        while len(batch) < self._max_batch:
            try:
                ev = self._queue.get_nowait()
            except queue.Empty:
                break
            batch.append(ev)
        if not batch:
            return
        try:
            self._delegate.export(batch)
            self._exported += len(batch)
        except Exception as e:
            _log.warning("batch export failed: %s", e)
