"""LangGraph instrumentation — emit events on graph nodes."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "langgraph-agent"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from langgraph.graph import CompiledGraph  # type: ignore
    except Exception:
        return
    if not hasattr(CompiledGraph, "invoke") or already_patched(CompiledGraph.invoke):
        return
    _originals["invoke"] = CompiledGraph.invoke

    def invoke(self: Any, *args: Any, **kwargs: Any) -> Any:
        ensure_context()
        emit_event(client, agent_id=agent_id, event_type="framework.langgraph.invoke.start")
        start = now_ns()
        try:
            res = _originals["invoke"](self, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="framework.langgraph.invoke.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error")
            raise
        emit_event(client, agent_id=agent_id, event_type="framework.langgraph.invoke.end",
                   duration_ms=ns_to_ms(start, now_ns()))
        return res

    mark_patched(invoke)
    CompiledGraph.invoke = invoke  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from langgraph.graph import CompiledGraph  # type: ignore
        if "invoke" in _originals:
            CompiledGraph.invoke = _originals.pop("invoke")
    except Exception:
        pass
    _originals.clear()
