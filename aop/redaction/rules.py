"""Regex/rule-based redaction primitives."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Pattern, Set

REDACTED = "<redacted>"


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@dataclass
class RedactionRule:
    name: str
    pattern: Pattern[str]
    replacement: str = REDACTED
    validator: Optional[Callable[[str], bool]] = None  # additional check (e.g. Luhn)


def _luhn_valid(s: str) -> bool:
    digits = [int(c) for c in s if c.isdigit()]
    if not (12 <= len(digits) <= 19):
        return False
    checksum = 0
    parity = (len(digits) - 2) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


DEFAULT_RULES: List[RedactionRule] = [
    RedactionRule(
        name="email",
        pattern=re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    ),
    RedactionRule(
        name="ssn",
        pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    ),
    RedactionRule(
        name="credit_card",
        pattern=re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
        validator=_luhn_valid,
    ),
    RedactionRule(
        name="phone_e164",
        pattern=re.compile(r"\+?\d[\d\-\s().]{7,15}\d"),
    ),
    RedactionRule(
        name="jwt",
        pattern=re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),
    ),
    RedactionRule(
        name="openai_key",
        pattern=re.compile(r"sk-(?:proj-|svcacct-)?[A-Za-z0-9_\-]{20,}"),
    ),
    RedactionRule(
        name="anthropic_key",
        pattern=re.compile(r"sk-ant-(?:api|admin)\d{2}-[A-Za-z0-9_\-]{32,}"),
    ),
    RedactionRule(
        name="aws_access_key",
        pattern=re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    RedactionRule(
        name="aws_secret",
        pattern=re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"),
    ),
    RedactionRule(
        name="github_token",
        pattern=re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    ),
]


# Field-name based redaction --------------------------------------------------

SENSITIVE_FIELD_NAMES: Set[str] = {
    "password", "secret", "api_key", "apikey", "access_token",
    "auth", "authorization", "private_key", "session_id", "cookie",
    "x_api_key", "client_secret",
}


# ---------------------------------------------------------------------------

_CUSTOM_RULES: List[RedactionRule] = []


def add_rule(rule: RedactionRule) -> None:
    """Register an additional rule applied after the defaults."""
    _CUSTOM_RULES.append(rule)


def all_rules() -> List[RedactionRule]:
    return DEFAULT_RULES + _CUSTOM_RULES


def _is_sensitive_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.lower().replace("-", "_") in SENSITIVE_FIELD_NAMES


def redact_value(v: Any, *, depth: int = 0) -> Any:
    """Recursively redact strings inside arbitrary nested structures."""
    if depth > 16:
        return v
    if isinstance(v, str):
        return _redact_string(v)
    if isinstance(v, dict):
        return {
            k: REDACTED if _is_sensitive_key(k) else redact_value(val, depth=depth + 1)
            for k, val in v.items()
        }
    if isinstance(v, list):
        return [redact_value(x, depth=depth + 1) for x in v]
    if isinstance(v, tuple):
        return tuple(redact_value(x, depth=depth + 1) for x in v)
    return v


def _redact_string(s: str) -> str:
    out = s
    for rule in all_rules():
        def _replace(m: re.Match) -> str:
            text = m.group(0)
            if rule.validator and not rule.validator(text):
                return text
            return rule.replacement
        out = rule.pattern.sub(_replace, out)
    return out


def redact_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``ev`` with all sensitive content redacted.

    The id / timestamp / agent_id / instance_id / protocol / event_type /
    severity / duration_ms / trace_id / span_id / parent_span_id fields
    are preserved verbatim.
    """
    safe_keys = {
        "id", "version", "timestamp", "agent_id", "instance_id",
        "protocol", "event_type", "severity", "duration_ms",
        "trace_id", "span_id", "parent_span_id",
    }
    out: Dict[str, Any] = {}
    for k, v in ev.items():
        if k in safe_keys:
            out[k] = v
        else:
            out[k] = redact_value(v)
    return out
