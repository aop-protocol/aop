"""LiteLLM instrumentation (covers many providers via one wrapper)."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import calc_cost, extract_openai_tokens, summarize_messages

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "litellm-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        import litellm  # type: ignore
    except ImportError:
        return
    if already_patched(litellm.completion):
        return
    _originals["completion"] = litellm.completion

    def completion(*args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model") or "unknown"
        provider = _provider_from_model(model)
        ensure_context()
        emit_event(client, agent_id=agent_id, event_type="llm.completion.request",
                   data={"provider": provider, "model": model,
                         "messages_preview": summarize_messages(kwargs.get("messages") or [])})
        start = now_ns()
        try:
            resp = _originals["completion"](*args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"provider": provider, "model": model})
            raise
        tokens = extract_openai_tokens(resp)
        cost = calc_cost(provider, model, tokens["prompt"], tokens["completion"]) if tokens else None
        emit_event(client, agent_id=agent_id, event_type="llm.completion.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"provider": provider, "model": model},
                   tokens=tokens, cost=cost)
        return resp

    mark_patched(completion)
    litellm.completion = completion  # type: ignore[assignment]


def uninstall() -> None:
    try:
        import litellm  # type: ignore
        if "completion" in _originals:
            litellm.completion = _originals.pop("completion")
    except Exception:
        pass
    _originals.clear()


def _provider_from_model(model: str) -> str:
    if "/" in model:
        return model.split("/", 1)[0]
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gpt") or model.startswith("o1") or model.startswith("o3") or model.startswith("o4"):
        return "openai"
    if model.startswith("gemini"):
        return "google"
    if model.startswith("mistral"):
        return "mistral"
    return "unknown"
