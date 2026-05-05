"""Pinecone Python client instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "pinecone-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from pinecone import Index  # type: ignore
    except Exception:
        try:
            from pinecone.data import Index  # type: ignore
        except Exception:
            return
    if not hasattr(Index, "query") or already_patched(Index.query):
        return
    _originals["query"] = Index.query

    def query(self: Any, *args: Any, **kwargs: Any) -> Any:
        ensure_context()
        index_name = getattr(self, "name", None) or kwargs.get("namespace") or "?"
        top_k = kwargs.get("top_k") or (args[1] if len(args) > 1 else None)
        emit_event(client, agent_id=agent_id, event_type="vectordb.query.request",
                   data={"vendor": "pinecone", "index": index_name, "top_k": top_k})
        start = now_ns()
        try:
            resp = _originals["query"](self, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="vectordb.query.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error")
            raise
        matches = getattr(resp, "matches", None) or (resp.get("matches") if isinstance(resp, dict) else None) or []
        emit_event(client, agent_id=agent_id, event_type="vectordb.query.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"vendor": "pinecone", "index": index_name,
                         "matches_count": len(matches)})
        return resp

    mark_patched(query)
    Index.query = query  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from pinecone import Index  # type: ignore
    except Exception:
        try:
            from pinecone.data import Index  # type: ignore
        except Exception:
            _originals.clear()
            return
    if "query" in _originals:
        Index.query = _originals.pop("query")
    _originals.clear()
