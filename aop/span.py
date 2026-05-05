"""
Span — lightweight OpenTelemetry-style span that emits AOP events on
lifecycle transitions.

Spans replace the ad-hoc parent_id linking used in v1.0. A span:

  • carries a ``SpanContext`` (trace_id / span_id / parent_span_id)
  • automatically picks up a parent span/SpanContext from contextvars
  • emits a ``<protocol>.<name>.started`` event on entry and a
    ``<protocol>.<name>.completed`` (or ``.error``) event on exit
  • can have additional events attached via ``add_event``

Usage:
    with start_span("my_op", protocol="mcp", agent_id="a1", attributes={"foo":"bar"}):
        do_work()

The Span integrates with auto-instrumentation (Phase 2) so that wrapped
LLM/HTTP calls automatically inherit the parent context.
"""

from __future__ import annotations

import time
import traceback
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Generator, List, Optional, TYPE_CHECKING

from .propagation import SpanContext, new_root_context
from .trace import get_current_span_context, set_current_span_context
from .types import SpanKind
from .utils import generate_span_id

if TYPE_CHECKING:
    from .client import AOPClient

# Active span stack ----------------------------------------------------------
_active_span: ContextVar[Optional["Span"]] = ContextVar('aop_active_span', default=None)


def current_span() -> Optional["Span"]:
    return _active_span.get()


# ---------------------------------------------------------------------------
# Span class
# ---------------------------------------------------------------------------


class Span:
    """An in-flight observable operation."""

    __slots__ = (
        "name",
        "agent_id",
        "protocol",
        "kind",
        "attributes",
        "events",
        "context",
        "parent_context",
        "_client",
        "_start_ns",
        "_end_ns",
        "_ended",
        "_status_code",
        "_status_description",
        "_error",
        "_token",
    )

    def __init__(
        self,
        name: str,
        *,
        agent_id: str,
        protocol: str = "mcp",
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        client: Optional["AOPClient"] = None,
        parent: Optional[SpanContext] = None,
    ) -> None:
        self.name = name
        self.agent_id = agent_id
        self.protocol = protocol
        self.kind = kind
        self.attributes: Dict[str, Any] = dict(attributes or {})
        self.events: List[Dict[str, Any]] = []
        self._client = client

        # Establish context: explicit parent > parent span > current ctx > new root
        if parent is not None:
            parent_ctx = parent
        else:
            current = current_span()
            if current is not None:
                parent_ctx = current.context
            else:
                parent_ctx = get_current_span_context()

        if parent_ctx is not None:
            self.context = SpanContext(
                trace_id=parent_ctx.trace_id,
                span_id=generate_span_id(),
                trace_flags=parent_ctx.trace_flags,
                trace_state=parent_ctx.trace_state,
                baggage=parent_ctx.baggage,
            )
            self.parent_context: Optional[SpanContext] = parent_ctx
        else:
            self.context = new_root_context()
            self.parent_context = None

        self._start_ns: int = 0
        self._end_ns: int = 0
        self._ended = False
        self._status_code = "ok"
        self._status_description: Optional[str] = None
        self._error: Optional[Dict[str, Any]] = None
        self._token = None  # type: ignore[assignment]

    # ---- lifecycle -----------------------------------------------------

    def start(self) -> "Span":
        if self._start_ns:
            return self
        self._start_ns = time.perf_counter_ns()
        self._token = _active_span.set(self)  # type: ignore[assignment]
        set_current_span_context(self.context)
        self._emit_started()
        return self

    def end(self) -> None:
        if self._ended:
            return
        self._end_ns = time.perf_counter_ns()
        self._ended = True
        try:
            self._emit_completed()
        finally:
            if self._token is not None:
                _active_span.reset(self._token)  # type: ignore[arg-type]
            # Restore the parent's span context so downstream code sees the
            # right trace_id after the child ends.
            parent = current_span()
            set_current_span_context(parent.context if parent is not None else self.parent_context)

    # ---- attributes / events ------------------------------------------

    def set_attribute(self, key: str, value: Any) -> "Span":
        self.attributes[key] = value
        return self

    def set_attributes(self, mapping: Dict[str, Any]) -> "Span":
        self.attributes.update(mapping)
        return self

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> "Span":
        self.events.append({
            "name": name,
            "attributes": attributes or {},
            "timestamp_ns": time.perf_counter_ns(),
        })
        return self

    def set_status(self, code: str, description: Optional[str] = None) -> "Span":
        if code not in ("ok", "error", "unset"):
            raise ValueError(f"Invalid status code: {code}")
        self._status_code = code
        self._status_description = description
        return self

    def record_exception(self, exc: BaseException) -> "Span":
        self._error = {
            "code": type(exc).__name__,
            "message": str(exc),
            "stack_trace": "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ),
        }
        self.set_status("error", str(exc))
        return self

    # ---- helpers -------------------------------------------------------

    @property
    def duration_ms(self) -> Optional[int]:
        if self._start_ns and self._end_ns:
            return max(0, (self._end_ns - self._start_ns) // 1_000_000)
        return None

    @property
    def trace_id(self) -> str:
        return self.context.trace_id

    @property
    def span_id(self) -> str:
        return self.context.span_id

    @property
    def parent_span_id(self) -> Optional[str]:
        return self.parent_context.span_id if self.parent_context else None

    # ---- context-manager protocol -------------------------------------

    def __enter__(self) -> "Span":
        return self.start()

    def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
        if exc is not None:
            self.record_exception(exc)
        self.end()
        return False  # never swallow

    # ---- emission ------------------------------------------------------

    def _common_event(self, suffix: str) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "event_type": f"{self.protocol}.{self.name}.{suffix}",
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "correlation_id": self.trace_id,  # legacy alias
            "attributes": self.attributes.copy(),
        }

    def _emit_started(self) -> None:
        if self._client is None:
            return
        ev = self._common_event("started")
        try:
            self._client.log_event(ev, validate=False)
        except Exception:
            pass

    def _emit_completed(self) -> None:
        if self._client is None:
            return
        suffix = "error" if self._status_code == "error" else "completed"
        ev = self._common_event(suffix)
        if self.duration_ms is not None:
            ev["duration_ms"] = self.duration_ms
        if self._error is not None:
            ev["error"] = self._error
            ev["severity"] = "error"
        try:
            self._client.log_event(ev, validate=False)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

@contextmanager
def start_span(
    name: str,
    *,
    agent_id: str,
    protocol: str = "mcp",
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
    client: Optional["AOPClient"] = None,
    parent: Optional[SpanContext] = None,
) -> Generator[Span, None, None]:
    """Start a span as a context manager."""
    span = Span(
        name,
        agent_id=agent_id,
        protocol=protocol,
        kind=kind,
        attributes=attributes,
        client=client,
        parent=parent,
    )
    with span as s:
        yield s


__all__ = ["Span", "start_span", "current_span"]
