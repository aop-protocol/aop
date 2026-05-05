"""
W3C TraceContext (and B3) propagation primitives.

Implements the subset of https://www.w3.org/TR/trace-context/ that AOP needs:

- ``traceparent``  ``00-<trace-id>-<parent-id>-<flags>``
- ``tracestate``   list of ``vendor=value`` pairs (max 32, max 512 bytes)
- ``baggage``      RFC 9009-style key=value pairs

Plus B3 single-header support (``b3: <trace>-<span>-<sampled>-<parent>``)
for compatibility with Zipkin-style services.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Dict, Mapping, MutableMapping, Optional, Tuple

from .utils import (
    generate_span_id,
    generate_trace_id,
    validate_span_id,
    validate_trace_id,
)

# ---------------------------------------------------------------------------
# SpanContext
# ---------------------------------------------------------------------------

# trace_flags bit 0 = sampled
SAMPLED_FLAG = 0x01


@dataclass(frozen=True)
class SpanContext:
    """Immutable W3C-compatible span context."""

    trace_id: str
    span_id: str
    trace_flags: int = SAMPLED_FLAG
    is_remote: bool = False
    trace_state: Tuple[Tuple[str, str], ...] = ()
    baggage: Tuple[Tuple[str, str], ...] = ()

    @property
    def sampled(self) -> bool:
        return bool(self.trace_flags & SAMPLED_FLAG)

    def is_valid(self) -> bool:
        return validate_trace_id(self.trace_id) and validate_span_id(self.span_id)

    def child(self, span_id: Optional[str] = None) -> "SpanContext":
        """Return a sibling context for the same trace with a new span id."""
        return replace(self, span_id=span_id or generate_span_id(), is_remote=False)

    def with_baggage(self, **kv: str) -> "SpanContext":
        existing = dict(self.baggage)
        existing.update({k: str(v) for k, v in kv.items()})
        return replace(self, baggage=tuple(existing.items()))


def new_root_context(sampled: bool = True) -> SpanContext:
    return SpanContext(
        trace_id=generate_trace_id(),
        span_id=generate_span_id(),
        trace_flags=SAMPLED_FLAG if sampled else 0,
    )


# ---------------------------------------------------------------------------
# traceparent / tracestate
# ---------------------------------------------------------------------------

_TRACEPARENT_RE = re.compile(
    r'^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$'
)


def _format_traceparent(ctx: SpanContext) -> str:
    return f"00-{ctx.trace_id}-{ctx.span_id}-{ctx.trace_flags:02x}"


def _parse_traceparent(value: str) -> Optional[SpanContext]:
    if not value:
        return None
    m = _TRACEPARENT_RE.match(value.strip().lower())
    if not m:
        return None
    version, trace_id, span_id, flags = m.groups()
    if version == "ff":  # forbidden by spec
        return None
    if not validate_trace_id(trace_id) or not validate_span_id(span_id):
        return None
    return SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        trace_flags=int(flags, 16),
        is_remote=True,
    )


def _format_tracestate(ctx: SpanContext) -> str:
    if not ctx.trace_state:
        return ""
    pairs = []
    for k, v in ctx.trace_state[:32]:
        if not k:
            continue
        pairs.append(f"{k}={v}")
    out = ",".join(pairs)
    return out[:512]


def _parse_tracestate(value: str) -> Tuple[Tuple[str, str], ...]:
    if not value:
        return ()
    out = []
    for item in value.split(","):
        item = item.strip()
        if not item or "=" not in item:
            continue
        k, v = item.split("=", 1)
        out.append((k.strip(), v.strip()))
        if len(out) >= 32:
            break
    return tuple(out)


def _format_baggage(ctx: SpanContext) -> str:
    if not ctx.baggage:
        return ""
    return ",".join(f"{k}={v}" for k, v in ctx.baggage if k)


def _parse_baggage(value: str) -> Tuple[Tuple[str, str], ...]:
    if not value:
        return ()
    out = []
    for item in value.split(","):
        item = item.strip()
        if not item or "=" not in item:
            continue
        k, v = item.split("=", 1)
        # baggage values may contain ;-separated properties; we strip them
        v = v.split(";", 1)[0]
        out.append((k.strip(), v.strip()))
    return tuple(out)


# ---------------------------------------------------------------------------
# B3 single-header support
# ---------------------------------------------------------------------------

_B3_RE = re.compile(
    r'^([0-9a-f]{16,32})-([0-9a-f]{16})(?:-([01d]))?(?:-([0-9a-f]{16}))?$'
)


def _parse_b3(value: str) -> Optional[SpanContext]:
    if not value:
        return None
    value = value.strip().lower()
    if value == "0":  # explicit do-not-trace
        return None
    m = _B3_RE.match(value)
    if not m:
        return None
    trace_id, span_id, sampled, _parent = m.groups()
    if len(trace_id) == 16:
        trace_id = "0" * 16 + trace_id
    if not validate_trace_id(trace_id) or not validate_span_id(span_id):
        return None
    flags = SAMPLED_FLAG if sampled in ("1", "d") else 0
    return SpanContext(
        trace_id=trace_id, span_id=span_id, trace_flags=flags, is_remote=True,
    )


def _format_b3(ctx: SpanContext) -> str:
    sampled = "1" if ctx.sampled else "0"
    return f"{ctx.trace_id}-{ctx.span_id}-{sampled}"


# ---------------------------------------------------------------------------
# Public API: inject / extract
# ---------------------------------------------------------------------------

# Header name constants — case sensitivity is handled by the helpers below.
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"
BAGGAGE_HEADER = "baggage"
B3_HEADER = "b3"


def inject(carrier: MutableMapping[str, str], ctx: SpanContext, *, b3: bool = False) -> None:
    """Inject a SpanContext into a header carrier (``dict``-like)."""
    carrier[TRACEPARENT_HEADER] = _format_traceparent(ctx)
    ts = _format_tracestate(ctx)
    if ts:
        carrier[TRACESTATE_HEADER] = ts
    bg = _format_baggage(ctx)
    if bg:
        carrier[BAGGAGE_HEADER] = bg
    if b3:
        carrier[B3_HEADER] = _format_b3(ctx)


def extract(carrier: Mapping[str, str]) -> Optional[SpanContext]:
    """Extract a SpanContext from a header carrier.

    Tries W3C ``traceparent`` first, then falls back to B3 single-header.
    Header lookup is case-insensitive.
    """
    lookup: Dict[str, str] = {}
    for k, v in carrier.items():
        if isinstance(k, str) and isinstance(v, str):
            lookup[k.lower()] = v

    ctx = _parse_traceparent(lookup.get(TRACEPARENT_HEADER, ""))
    if ctx is None:
        ctx = _parse_b3(lookup.get(B3_HEADER, ""))
    if ctx is None:
        return None

    state = _parse_tracestate(lookup.get(TRACESTATE_HEADER, ""))
    bag = _parse_baggage(lookup.get(BAGGAGE_HEADER, ""))
    if state or bag:
        ctx = replace(ctx, trace_state=state, baggage=bag)
    return ctx


# Aliases for documentation clarity --------------------------------------
inject_into_headers = inject
extract_from_headers = extract


__all__ = [
    "SpanContext",
    "SAMPLED_FLAG",
    "new_root_context",
    "inject",
    "extract",
    "inject_into_headers",
    "extract_from_headers",
    "TRACEPARENT_HEADER",
    "TRACESTATE_HEADER",
    "BAGGAGE_HEADER",
    "B3_HEADER",
]
