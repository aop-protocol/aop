"""Mistral AI SDK instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import calc_cost, extract_openai_tokens

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "mistralai-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from mistralai import Mistral  # type: ignore
    except ImportError:
        return
    # The SDK exposes a Chat resource on the client.  Patch its `complete` method.
    try:
        from mistralai.chat import Chat  # type: ignore
    except Exception:
        return
    if not hasattr(Chat, "complete") or already_patched(Chat.complete):
        return
    _originals["complete"] = Chat.complete

    def complete(self: Any, *args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model") or "unknown"
        ensure_context()
        emit_event(client, agent_id=agent_id, event_type="llm.completion.request",
                   data={"provider": "mistral", "model": model})
        start = now_ns()
        try:
            resp = _originals["complete"](self, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"provider": "mistral", "model": model})
            raise
        tokens = extract_openai_tokens(resp)  # mistral uses OpenAI-compatible usage shape
        cost = calc_cost("mistral", model, tokens["prompt"], tokens["completion"]) if tokens else None
        emit_event(client, agent_id=agent_id, event_type="llm.completion.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"provider": "mistral", "model": model},
                   tokens=tokens, cost=cost)
        return resp

    mark_patched(complete)
    Chat.complete = complete  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from mistralai.chat import Chat  # type: ignore
        if "complete" in _originals:
            Chat.complete = _originals.pop("complete")
    except Exception:
        pass
    _originals.clear()
