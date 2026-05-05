"""Weaviate client instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "weaviate-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        import weaviate  # type: ignore
    except ImportError:
        return
    # weaviate v4 uses Collection.query.* pipelines; we hook at the Collection
    # level if present. v3 is no longer instrumented.
    Collection = getattr(weaviate.collections, "Collection", None) if hasattr(weaviate, "collections") else None
    if Collection is None:
        return
    # Pick a stable method name to wrap if it exists.
    fn = getattr(Collection, "query", None)
    if fn is None or already_patched(fn):
        return
    _originals["query"] = fn

    def query(self: Any, *args: Any, **kwargs: Any) -> Any:
        ensure_context()
        emit_event(client, agent_id=agent_id, event_type="vectordb.query.request",
                   data={"vendor": "weaviate", "collection": getattr(self, "name", "?")})
        start = now_ns()
        try:
            res = _originals["query"](self, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="vectordb.query.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error")
            raise
        emit_event(client, agent_id=agent_id, event_type="vectordb.query.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"vendor": "weaviate"})
        return res

    mark_patched(query)
    Collection.query = query  # type: ignore[assignment]


def uninstall() -> None:
    try:
        import weaviate  # type: ignore
        Collection = getattr(weaviate.collections, "Collection", None) if hasattr(weaviate, "collections") else None
        if Collection and "query" in _originals:
            Collection.query = _originals.pop("query")
    except Exception:
        pass
    _originals.clear()
