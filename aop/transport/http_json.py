"""AOP-native HTTP/JSON transport.

POSTs a batch of AOP events to a Collector's ``/v1/events`` endpoint as
``application/json``. Bearer-token auth via the ``Authorization`` header.

The wire format is the AOP event itself, wrapped in an envelope:

    {
      "schema_version": "1.1",
      "events": [ <AOPEvent>, ... ]
    }
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import BaseTransport

_log = logging.getLogger("aop.transport.http")


class HTTPJSONTransport(BaseTransport):
    def __init__(
        self,
        endpoint: str,
        *,
        token: Optional[str] = None,
        timeout_s: float = 5.0,
        max_retries: int = 3,
        backoff_s: float = 0.5,
        gzip_compression: bool = False,
    ) -> None:
        self.endpoint = endpoint.rstrip("/") + "/v1/events"
        self.token = token or os.environ.get("AOP_INGEST_TOKEN")
        self.timeout = timeout_s
        self.retries = max_retries
        self.backoff = backoff_s
        self.gzip = gzip_compression

    def export(self, events: List[Dict[str, Any]]) -> None:
        if not events:
            return
        body = json.dumps({"schema_version": "1.1", "events": events}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.gzip:
            try:
                import gzip
                body = gzip.compress(body)
                headers["Content-Encoding"] = "gzip"
            except Exception:
                pass

        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(self.endpoint, data=body,
                                             headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if 200 <= resp.status < 300:
                        return
                    last_err = RuntimeError(f"collector returned HTTP {resp.status}")
            except (urllib.error.URLError, OSError, RuntimeError) as e:
                last_err = e
            # backoff
            try:
                import time as _t
                _t.sleep(self.backoff * (2 ** attempt))
            except Exception:
                pass

        _log.warning("HTTP transport failed after %d retries: %s",
                     self.retries, last_err)
