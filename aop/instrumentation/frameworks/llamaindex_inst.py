"""LlamaIndex instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "llamaindex-agent"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from llama_index.core.indices.base import BaseIndex  # type: ignore
        from llama_index.core.base.base_query_engine import BaseQueryEngine  # type: ignore
    except Exception:
        return

    if hasattr(BaseQueryEngine, "query") and not already_patched(BaseQueryEngine.query):
        _originals["query"] = BaseQueryEngine.query

        def query(self: Any, *args: Any, **kwargs: Any) -> Any:
            ensure_context()
            emit_event(client, agent_id=agent_id, event_type="framework.llamaindex.query.start")
            start = now_ns()
            try:
                res = _originals["query"](self, *args, **kwargs)
            except Exception as e:
                emit_event(client, agent_id=agent_id, event_type="framework.llamaindex.query.error",
                           duration_ms=ns_to_ms(start, now_ns()),
                           error={"code": type(e).__name__, "message": str(e)}, severity="error")
                raise
            emit_event(client, agent_id=agent_id, event_type="framework.llamaindex.query.end",
                       duration_ms=ns_to_ms(start, now_ns()))
            return res

        mark_patched(query)
        BaseQueryEngine.query = query  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from llama_index.core.base.base_query_engine import BaseQueryEngine  # type: ignore
        if "query" in _originals:
            BaseQueryEngine.query = _originals.pop("query")
    except Exception:
        pass
    _originals.clear()
