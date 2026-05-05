"""psycopg (v3) instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "psycopg-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        import psycopg  # type: ignore
    except ImportError:
        return
    Cursor = getattr(psycopg, "Cursor", None)
    if Cursor is None or not hasattr(Cursor, "execute") or already_patched(Cursor.execute):
        return
    _originals["execute"] = Cursor.execute

    def execute(self: Any, query: Any, params: Any = None, *args: Any, **kwargs: Any) -> Any:
        ensure_context()
        start = now_ns()
        try:
            res = _originals["execute"](self, query, params, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="db.query.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"vendor": "psycopg",
                             "statement_preview": str(query)[:200]})
            raise
        emit_event(client, agent_id=agent_id, event_type="db.query.completed",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"vendor": "psycopg",
                         "statement_preview": str(query)[:200]})
        return res

    mark_patched(execute)
    Cursor.execute = execute  # type: ignore[assignment]


def uninstall() -> None:
    try:
        import psycopg  # type: ignore
        Cursor = getattr(psycopg, "Cursor", None)
        if Cursor and "execute" in _originals:
            Cursor.execute = _originals.pop("execute")
    except Exception:
        pass
    _originals.clear()
