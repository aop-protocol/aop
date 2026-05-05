"""ChromaDB instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "chromadb-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from chromadb.api.models.Collection import Collection  # type: ignore
    except Exception:
        return
    for action in ("query", "add", "get"):
        fn = getattr(Collection, action, None)
        if fn is None or already_patched(fn):
            continue
        _originals[action] = fn

        def _make(action: str, original: Any) -> Any:
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                ensure_context()
                emit_event(client, agent_id=agent_id, event_type=f"vectordb.{action}.request",
                           data={"vendor": "chromadb", "collection": getattr(self, "name", "?")})
                start = now_ns()
                try:
                    res = original(self, *args, **kwargs)
                except Exception as e:
                    emit_event(client, agent_id=agent_id, event_type=f"vectordb.{action}.error",
                               duration_ms=ns_to_ms(start, now_ns()),
                               error={"code": type(e).__name__, "message": str(e)}, severity="error")
                    raise
                emit_event(client, agent_id=agent_id, event_type=f"vectordb.{action}.response",
                           duration_ms=ns_to_ms(start, now_ns()),
                           data={"vendor": "chromadb"})
                return res
            mark_patched(wrapper)
            return wrapper

        setattr(Collection, action, _make(action, fn))


def uninstall() -> None:
    try:
        from chromadb.api.models.Collection import Collection  # type: ignore
        for action, fn in list(_originals.items()):
            setattr(Collection, action, fn)
    except Exception:
        pass
    _originals.clear()
