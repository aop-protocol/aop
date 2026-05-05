"""GDPR helpers: right to erasure, data export, consent tagging."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..client import AOPClient
from ..redaction import redact_event


def tag_consent(event: Dict[str, Any], *, consent_id: str, granted: bool,
                purposes: Optional[List[str]] = None) -> Dict[str, Any]:
    """Annotate an event with consent metadata."""
    metadata = dict(event.get("metadata") or {})
    metadata["gdpr"] = {
        "consent_id": consent_id,
        "granted": granted,
        "purposes": purposes or [],
        "timestamped_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**event, "metadata": metadata}


def export_user_data(client: AOPClient, *, subject_id: str,
                     limit: int = 100000) -> List[Dict[str, Any]]:
    """Right of access: return every event referencing a given subject."""
    out: List[Dict[str, Any]] = []
    for ev in client.query(limit=limit):
        meta = ev.get("metadata") or {}
        data = ev.get("data") or {}
        if subject_id in (meta.get("subject_id"), data.get("user_id"),
                          data.get("subject_id"), data.get("customer_id")):
            out.append(ev)
        elif _stringly_contains(ev, subject_id):
            out.append(ev)
    return out


def erase_user_data(client: AOPClient, *, subject_id: str) -> int:
    """Right to erasure: replace matching events' content with redacted placeholders.

    We don't delete: regulators generally accept tombstones with audit trail.
    """
    matched = export_user_data(client, subject_id=subject_id)
    n = 0
    for ev in matched:
        redacted = redact_event(ev)
        meta = dict(redacted.get("metadata") or {})
        meta["gdpr_erased"] = True
        meta["gdpr_erased_at"] = datetime.now(timezone.utc).isoformat()
        meta["gdpr_subject_hash"] = f"sha256:{_sha256_short(subject_id)}"
        redacted["metadata"] = meta
        # Re-log; storage backends are append-only so this layers a tombstone.
        try:
            client.log_event(redacted, validate=False, auto_build=False)
            n += 1
        except Exception:
            continue
    return n


def _stringly_contains(ev: Dict[str, Any], needle: str) -> bool:
    import json
    try:
        return needle in json.dumps(ev, default=str)
    except Exception:
        return False


def _sha256_short(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()[:16]
