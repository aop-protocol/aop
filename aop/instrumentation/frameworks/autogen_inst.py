"""AutoGen instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "autogen-agent"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from autogen.agentchat.conversable_agent import ConversableAgent  # type: ignore
    except Exception:
        return
    for name in ("send", "receive", "generate_reply"):
        fn = getattr(ConversableAgent, name, None)
        if fn is None or already_patched(fn):
            continue
        _originals[name] = fn

        def _make(label: str, original: Any) -> Any:
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                ensure_context()
                emit_event(client, agent_id=agent_id, event_type=f"framework.autogen.{label}.start",
                           data={"agent": getattr(self, "name", "?")})
                start = now_ns()
                try:
                    res = original(self, *args, **kwargs)
                except Exception as e:
                    emit_event(client, agent_id=agent_id, event_type=f"framework.autogen.{label}.error",
                               duration_ms=ns_to_ms(start, now_ns()),
                               error={"code": type(e).__name__, "message": str(e)}, severity="error")
                    raise
                emit_event(client, agent_id=agent_id, event_type=f"framework.autogen.{label}.end",
                           duration_ms=ns_to_ms(start, now_ns()))
                return res
            mark_patched(wrapper)
            return wrapper

        setattr(ConversableAgent, name, _make(name, fn))


def uninstall() -> None:
    try:
        from autogen.agentchat.conversable_agent import ConversableAgent  # type: ignore
        for name, fn in list(_originals.items()):
            setattr(ConversableAgent, name, fn)
    except Exception:
        pass
    _originals.clear()
