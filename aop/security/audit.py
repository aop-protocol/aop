"""Append-only audit log with hash-chain tamper detection."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TextIO


class AuditLogger:
    """Persistent append-only audit log.

    Each line is a JSON object with the previous line's hash chained in,
    so any tampering breaks the chain on verification.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._prev_hash: Optional[str] = self._load_last_hash()

    def _load_last_hash(self) -> Optional[str]:
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r") as f:
                last = None
                for line in f:
                    last = line
                if last:
                    return json.loads(last).get("hash")
        except Exception:
            return None
        return None

    def log(self, *, actor: str, action: str, resource: str,
            outcome: str = "success", extra: Optional[Dict[str, Any]] = None) -> str:
        record: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "extra": extra or {},
            "prev_hash": self._prev_hash,
        }
        canonical = json.dumps({k: v for k, v in record.items() if k != "hash"},
                               sort_keys=True, default=str).encode("utf-8")
        h = hashlib.sha256()
        if self._prev_hash:
            h.update(self._prev_hash.encode("utf-8"))
        h.update(canonical)
        record["hash"] = h.hexdigest()
        line = json.dumps(record, default=str)
        with self._lock:
            with open(self.path, "a") as f:
                f.write(line + "\n")
            self._prev_hash = record["hash"]
        return record["hash"]

    def verify(self) -> int:
        """Walk the file end-to-end. Returns the line number of the first
        broken record, or -1 if the chain is intact."""
        prev: Optional[str] = None
        if not os.path.exists(self.path):
            return -1
        with open(self.path, "r") as f:
            for i, line in enumerate(f, start=1):
                rec = json.loads(line)
                claimed = rec.pop("hash", None)
                if rec.get("prev_hash") != prev:
                    return i
                canonical = json.dumps(rec, sort_keys=True, default=str).encode("utf-8")
                h = hashlib.sha256()
                if prev:
                    h.update(prev.encode("utf-8"))
                h.update(canonical)
                if h.hexdigest() != claimed:
                    return i
                prev = claimed
        return -1
