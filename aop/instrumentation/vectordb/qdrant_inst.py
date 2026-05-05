"""Qdrant client instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "qdrant-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from qdrant_client import QdrantClient  # type: ignore
    except ImportError:
        return
    targets = ("search", "query_points", "scroll", "upsert")
    for name in targets:
        fn = getattr(QdrantClient, name, None)
        if fn is None or already_patched(fn):
            continue
        _originals[name] = fn

        def _make(action: str, original: Any) -> Any:
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                ensure_context()
                col = kwargs.get("collection_name") or (args[0] if args else "?")
                emit_event(client, agent_id=agent_id, event_type=f"vectordb.{action}.request",
                           data={"vendor": "qdrant", "collection": col})
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
                           data={"vendor": "qdrant", "collection": col})
                return res
            mark_patched(wrapper)
            return wrapper

        setattr(QdrantClient, name, _make(name, fn))


def uninstall() -> None:
    try:
        from qdrant_client import QdrantClient  # type: ignore
        for name, fn in list(_originals.items()):
            setattr(QdrantClient, name, fn)
    except Exception:
        pass
    _originals.clear()
