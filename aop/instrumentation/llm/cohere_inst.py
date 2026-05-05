"""Cohere SDK instrumentation (v5+)."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import calc_cost

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "cohere-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from cohere import Client  # type: ignore
    except ImportError:
        return
    if not hasattr(Client, "chat") or already_patched(Client.chat):
        return
    _originals["chat"] = Client.chat

    def chat(self: Any, *args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model") or "unknown"
        ensure_context()
        emit_event(client, agent_id=agent_id, event_type="llm.completion.request",
                   data={"provider": "cohere", "model": model})
        start = now_ns()
        try:
            resp = _originals["chat"](self, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"provider": "cohere", "model": model})
            raise
        tokens = _extract_cohere_tokens(resp)
        cost = calc_cost("cohere", model, tokens["prompt"], tokens["completion"]) if tokens else None
        emit_event(client, agent_id=agent_id, event_type="llm.completion.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"provider": "cohere", "model": model},
                   tokens=tokens, cost=cost)
        return resp

    mark_patched(chat)
    Client.chat = chat  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from cohere import Client  # type: ignore
        if "chat" in _originals:
            Client.chat = _originals.pop("chat")
    except Exception:
        pass
    _originals.clear()


def _extract_cohere_tokens(resp: Any) -> Optional[dict]:
    try:
        meta = getattr(resp, "meta", None)
        if meta is None:
            return None
        billed = getattr(meta, "billed_units", None)
        if billed is None:
            return None
        prompt = getattr(billed, "input_tokens", 0) or 0
        completion = getattr(billed, "output_tokens", 0) or 0
        return {"prompt": int(prompt), "completion": int(completion), "total": int(prompt + completion)}
    except Exception:
        return None
