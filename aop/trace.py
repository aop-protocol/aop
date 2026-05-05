"""
Trace context management — automatic correlation_id and SpanContext handling.

v1.1: extends the original ``trace_context`` (correlation_id only) with
``current_span_context`` / ``set_span_context`` — but the legacy API is fully
preserved so existing user code keeps working.
"""

from contextvars import ContextVar
from contextlib import contextmanager
from typing import Generator, Optional

from .propagation import SpanContext

# Legacy v1.0 context var ----------------------------------------------------
_current_correlation_id: ContextVar[Optional[str]] = ContextVar(
    'aop_correlation_id', default=None,
)

# v1.1 W3C trace context var -------------------------------------------------
_current_span_context: ContextVar[Optional[SpanContext]] = ContextVar(
    'aop_span_context', default=None,
)


# ---------------------------------------------------------------------------
# correlation_id (legacy)
# ---------------------------------------------------------------------------

def get_current_correlation_id() -> Optional[str]:
    cid = _current_correlation_id.get()
    if cid:
        return cid
    # Fallback: derive from span context's trace_id
    ctx = _current_span_context.get()
    if ctx is not None:
        return ctx.trace_id
    return None


def set_correlation_id(correlation_id: Optional[str]) -> None:
    _current_correlation_id.set(correlation_id)


@contextmanager
def trace_context(correlation_id: str) -> Generator[None, None, None]:
    """Bind a correlation id for the duration of the with-block."""
    previous = _current_correlation_id.get()
    token = _current_correlation_id.set(correlation_id)
    try:
        yield
    finally:
        _current_correlation_id.reset(token)


# ---------------------------------------------------------------------------
# SpanContext (v1.1)
# ---------------------------------------------------------------------------

def get_current_span_context() -> Optional[SpanContext]:
    return _current_span_context.get()


def set_current_span_context(ctx: Optional[SpanContext]) -> None:
    _current_span_context.set(ctx)


@contextmanager
def use_span_context(ctx: SpanContext) -> Generator[SpanContext, None, None]:
    """Bind a SpanContext for the duration of the with-block."""
    token = _current_span_context.set(ctx)
    try:
        yield ctx
    finally:
        _current_span_context.reset(token)
