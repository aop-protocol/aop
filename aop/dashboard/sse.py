"""Server-Sent Events stream for the dashboard.

A pub/sub hub that fans out new events to every connected SSE client. Replaces
the 30-s polling WebSocket with sub-second push.

Two ways to feed the hub:

  • Direct (in-process):
        from aop.dashboard.sse import publish
        publish(event)
  • Via a tail of the storage backend (handled in websocket.py for back-compat).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, AsyncIterator, Dict, Set

_log = logging.getLogger("aop.dashboard.sse")


class SSEHub:
    """In-process pub/sub hub for SSE listeners."""

    def __init__(self, *, max_queue: int = 256) -> None:
        self._subs: Set[asyncio.Queue] = set()
        self._max_queue = max_queue

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    def publish(self, event: Dict[str, Any]) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # drop oldest
                try:
                    _ = q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass

    async def stream(self, q: asyncio.Queue) -> AsyncIterator[str]:
        """Yield SSE-formatted lines."""
        try:
            yield f"event: ping\ndata: {{\"ts\": {time.time():.0f}}}\n\n"
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield "event: aop\n"
                    yield "data: " + json.dumps(ev, default=str) + "\n\n"
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: {{\"ts\": {time.time():.0f}}}\n\n"
        finally:
            self.unsubscribe(q)


# Module-level singleton ------------------------------------------------------
_hub = SSEHub()


def publish(event: Dict[str, Any]) -> None:
    _hub.publish(event)


def hub() -> SSEHub:
    return _hub
