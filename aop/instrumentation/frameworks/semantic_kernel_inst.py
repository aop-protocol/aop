"""Microsoft Semantic Kernel instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "semantic-kernel-agent"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from semantic_kernel.kernel import Kernel  # type: ignore
    except Exception:
        return
    if hasattr(Kernel, "invoke") and not already_patched(Kernel.invoke):
        _originals["invoke"] = Kernel.invoke

        async def invoke(self: Any, *args: Any, **kwargs: Any) -> Any:
            ensure_context()
            emit_event(client, agent_id=agent_id, event_type="framework.semantic_kernel.invoke.start")
            start = now_ns()
            try:
                res = await _originals["invoke"](self, *args, **kwargs)
            except Exception as e:
                emit_event(client, agent_id=agent_id, event_type="framework.semantic_kernel.invoke.error",
                           duration_ms=ns_to_ms(start, now_ns()),
                           error={"code": type(e).__name__, "message": str(e)}, severity="error")
                raise
            emit_event(client, agent_id=agent_id, event_type="framework.semantic_kernel.invoke.end",
                       duration_ms=ns_to_ms(start, now_ns()))
            return res

        mark_patched(invoke)
        Kernel.invoke = invoke  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from semantic_kernel.kernel import Kernel  # type: ignore
        if "invoke" in _originals:
            Kernel.invoke = _originals.pop("invoke")
    except Exception:
        pass
    _originals.clear()
