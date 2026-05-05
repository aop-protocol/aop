"""HIPAA helpers: PHI masking, minimum-necessary policy, access logging."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from ..redaction import redact_event
from ..redaction.rules import RedactionRule, add_rule

# 18 HIPAA "Safe Harbor" identifier categories — implemented as best-effort
# regex add-ons to the default redaction set.

_PHI_RULES = [
    RedactionRule(name="mrn", pattern=re.compile(r"\bMRN[-:]?\s*\d{4,}\b", re.I)),
    RedactionRule(name="dob", pattern=re.compile(
        r"\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b")),
    RedactionRule(name="zip5", pattern=re.compile(r"\b\d{5}(?:-\d{4})?\b")),
    RedactionRule(name="us_ssn", pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]


def install_phi_rules() -> None:
    """Register the HIPAA-specific patterns alongside the default rules."""
    for r in _PHI_RULES:
        add_rule(r)


def tag_phi_access(event: Dict[str, Any], *, accessor_id: str,
                   purpose: str, lawful_basis: str = "treatment") -> Dict[str, Any]:
    """Decorate an event with PHI-access audit metadata."""
    metadata = dict(event.get("metadata") or {})
    metadata["hipaa"] = {
        "accessor_id": accessor_id,
        "purpose": purpose,
        "lawful_basis": lawful_basis,
        "accessed_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**event, "metadata": metadata}


def minimum_necessary(event: Dict[str, Any], *, allowed_fields: Iterable[str]) -> Dict[str, Any]:
    """Trim ``data`` down to only the allowed fields."""
    allowed = set(allowed_fields)
    if "data" in event and isinstance(event["data"], dict):
        event = {**event, "data": {k: v for k, v in event["data"].items() if k in allowed}}
    return event


def sanitize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience: PHI rules + base redaction in one call."""
    install_phi_rules()
    return redact_event(event)
