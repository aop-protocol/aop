"""Groq SDK instrumentation (OpenAI-compatible)."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import calc_cost, extract_openai_tokens, summarize_messages

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "groq-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from groq.resources.chat.completions import Completions  # type: ignore
    except ImportError:
        return
    if already_patched(Completions.create):
        return
    _originals["create"] = Completions.create

    def create(self: Any, *args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model") or "unknown"
        ensure_context()
        emit_event(client, agent_id=agent_id, event_type="llm.completion.request",
                   data={"provider": "groq", "model": model,
                         "messages_preview": summarize_messages(kwargs.get("messages") or [])})
        start = now_ns()
        try:
            resp = _originals["create"](self, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"provider": "groq", "model": model})
            raise
        tokens = extract_openai_tokens(resp)
        cost = calc_cost("groq", model, tokens["prompt"], tokens["completion"]) if tokens else None
        emit_event(client, agent_id=agent_id, event_type="llm.completion.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"provider": "groq", "model": model},
                   tokens=tokens, cost=cost)
        return resp

    mark_patched(create)
    Completions.create = create  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from groq.resources.chat.completions import Completions  # type: ignore
        if "create" in _originals:
            Completions.create = _originals.pop("create")
    except Exception:
        pass
    _originals.clear()
