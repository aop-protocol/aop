"""Shared helpers for instrumentation modules.

These helpers build AOP events, manage span contexts, and safely emit
events without ever breaking the wrapped library if AOP itself fails.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from ..propagation import SpanContext, inject as inject_propagation
from ..trace import get_current_span_context, set_current_span_context
from ..utils import generate_span_id, generate_trace_id

if TYPE_CHECKING:
    from ..client import AOPClient

_log = logging.getLogger("aop.instrumentation")

# Sentinel attribute placed on patched callables so we never double-wrap.
_PATCH_ATTR = "__aop_patched__"


def already_patched(obj: Any) -> bool:
    return bool(getattr(obj, _PATCH_ATTR, False))


def mark_patched(obj: Any) -> None:
    try:
        setattr(obj, _PATCH_ATTR, True)
    except (AttributeError, TypeError):
        pass


def safe(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: never let AOP code break the wrapped library."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            _log.debug("aop instrumentation hook failed: %s", e)
            return None

    return wrapper


def ensure_context() -> SpanContext:
    """Return the current SpanContext, creating a fresh root if missing."""
    ctx = get_current_span_context()
    if ctx is not None:
        return ctx
    ctx = SpanContext(trace_id=generate_trace_id(), span_id=generate_span_id())
    set_current_span_context(ctx)
    return ctx


def child_span_id() -> str:
    return generate_span_id()


def inject_into_kwargs_headers(kwargs: Dict[str, Any], ctx: SpanContext) -> None:
    """Inject W3C headers into a kwargs['headers'] dict (creating it if absent)."""
    headers = kwargs.get("headers")
    if headers is None:
        headers = {}
        kwargs["headers"] = headers
    if hasattr(headers, "__setitem__"):
        try:
            inject_propagation(headers, ctx)
        except Exception:
            pass


def emit_event(
    client: Optional["AOPClient"],
    *,
    agent_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
    error: Optional[Dict[str, Any]] = None,
    severity: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    span_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    tokens: Optional[Dict[str, int]] = None,
    cost: Optional[Dict[str, Any]] = None,
) -> None:
    """Best-effort event emission. Never raises."""
    if client is None:
        from . import get_default_client
        client = get_default_client()
    if client is None:
        return
    try:
        ctx = get_current_span_context()
        ev: Dict[str, Any] = {
            "agent_id": agent_id,
            "event_type": event_type,
        }
        if data is not None:
            ev["data"] = data
        if duration_ms is not None:
            ev["duration_ms"] = int(duration_ms)
        if error is not None:
            ev["error"] = error
        if severity is not None:
            ev["severity"] = severity
        if parent_span_id is not None:
            ev["parent_span_id"] = parent_span_id
        elif ctx is not None:
            ev["parent_span_id"] = ctx.span_id
        if span_id is not None:
            ev["span_id"] = span_id
        if trace_id is not None:
            ev["trace_id"] = trace_id
        elif ctx is not None:
            ev["trace_id"] = ctx.trace_id
            ev["correlation_id"] = ctx.trace_id
        if attributes is not None:
            ev["attributes"] = attributes
        if tokens is not None:
            ev["tokens"] = tokens
        if cost is not None:
            ev["cost"] = cost
        client.log_event(ev, validate=False)
    except Exception as e:
        _log.debug("emit_event failed: %s", e)


def now_ns() -> int:
    return time.perf_counter_ns()


def ns_to_ms(start_ns: int, end_ns: int) -> int:
    return max(0, (end_ns - start_ns) // 1_000_000)


__all__ = [
    "safe",
    "ensure_context",
    "child_span_id",
    "inject_into_kwargs_headers",
    "emit_event",
    "already_patched",
    "mark_patched",
    "now_ns",
    "ns_to_ms",
]
