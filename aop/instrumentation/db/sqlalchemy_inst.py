"""SQLAlchemy instrumentation via the engine event system (no monkey patching)."""

from __future__ import annotations

import time
from typing import Any, Optional, TYPE_CHECKING

from .._common import emit_event, ensure_context

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "sqlalchemy-client"
_listeners: list = []


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from sqlalchemy import event  # type: ignore
        from sqlalchemy.engine import Engine  # type: ignore
    except Exception:
        return

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        ensure_context()
        context._aop_start = time.perf_counter_ns()

    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        start = getattr(context, "_aop_start", time.perf_counter_ns())
        dur_ms = max(0, (time.perf_counter_ns() - start) // 1_000_000)
        emit_event(
            client, agent_id=agent_id, event_type="db.query.completed",
            duration_ms=dur_ms,
            data={"vendor": "sqlalchemy", "statement_preview": (statement or "")[:200]},
        )

    def handle_error(ctx):  # type: ignore[no-untyped-def]
        emit_event(
            client, agent_id=agent_id, event_type="db.query.error",
            error={"code": type(ctx.original_exception).__name__,
                   "message": str(ctx.original_exception)},
            severity="error",
        )

    event.listen(Engine, "before_cursor_execute", before_cursor_execute)
    event.listen(Engine, "after_cursor_execute", after_cursor_execute)
    event.listen(Engine, "handle_error", handle_error)
    _listeners.extend([
        ("before_cursor_execute", before_cursor_execute),
        ("after_cursor_execute", after_cursor_execute),
        ("handle_error", handle_error),
    ])


def uninstall() -> None:
    try:
        from sqlalchemy import event  # type: ignore
        from sqlalchemy.engine import Engine  # type: ignore
        for name, fn in _listeners:
            try:
                event.remove(Engine, name, fn)
            except Exception:
                pass
    except Exception:
        pass
    _listeners.clear()
