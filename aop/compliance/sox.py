"""SOX helpers: financial event tagging, immutable hash-chain audit trails."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def is_financial_event(event: Dict[str, Any]) -> bool:
    et = event.get("event_type") or ""
    return et.startswith("ap2.") or et.startswith("openai_agents.tool.invoked") or \
        "payment" in et or "invoice" in et or "ledger" in et


def tag_control(event: Dict[str, Any], *, control_id: str,
                attestation_required: bool = True) -> Dict[str, Any]:
    metadata = dict(event.get("metadata") or {})
    metadata["sox"] = {
        "control_id": control_id,
        "attestation_required": attestation_required,
        "tagged_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**event, "metadata": metadata}


# ---------------------------------------------------------------------------
# Hash-chained audit trail
# ---------------------------------------------------------------------------

def _canonical(event: Dict[str, Any]) -> bytes:
    return json.dumps(event, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")


def append_to_chain(event: Dict[str, Any], *, prev_hash: Optional[str]) -> Dict[str, Any]:
    """Compute and attach a SHA-256 hash linking this event to ``prev_hash``."""
    h = hashlib.sha256()
    if prev_hash:
        h.update(prev_hash.encode("utf-8"))
    h.update(_canonical(event))
    metadata = dict(event.get("metadata") or {})
    metadata["sox_chain"] = {
        "prev_hash": prev_hash,
        "hash": h.hexdigest(),
    }
    return {**event, "metadata": metadata}


def verify_chain(events: List[Dict[str, Any]]) -> List[int]:
    """Verify a hash-chained sequence; returns list of event indices that fail."""
    failed: List[int] = []
    prev: Optional[str] = None
    for i, ev in enumerate(events):
        chain = ((ev.get("metadata") or {}).get("sox_chain") or {})
        if chain.get("prev_hash") != prev:
            failed.append(i); prev = chain.get("hash"); continue
        # recompute
        copy = dict(ev)
        meta_copy = dict(copy.get("metadata") or {})
        if "sox_chain" in meta_copy:
            meta_copy = dict(meta_copy)
            del meta_copy["sox_chain"]
            copy["metadata"] = meta_copy
        h = hashlib.sha256()
        if prev:
            h.update(prev.encode())
        h.update(_canonical(copy))
        if h.hexdigest() != chain.get("hash"):
            failed.append(i)
        prev = chain.get("hash")
    return failed
