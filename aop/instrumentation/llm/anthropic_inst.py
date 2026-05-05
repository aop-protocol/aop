"""Anthropic SDK instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import calc_cost, extract_anthropic_tokens, summarize_messages, truncate_text

if TYPE_CHECKING:
    from ...client import AOPClient

_DEFAULT_AGENT_ID = "anthropic-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _DEFAULT_AGENT_ID) -> None:
    try:
        from anthropic.resources.messages import Messages  # type: ignore
    except ImportError:
        return
    if not already_patched(Messages.create):
        _originals["messages_create"] = Messages.create

        def messages_create(self: Any, *args: Any, **kwargs: Any) -> Any:
            model = kwargs.get("model") or "unknown"
            ensure_context()
            stream = kwargs.get("stream", False)
            emit_event(
                client, agent_id=agent_id, event_type="llm.completion.request",
                data={
                    "provider": "anthropic",
                    "model": model,
                    "stream": bool(stream),
                    "messages_preview": summarize_messages(kwargs.get("messages") or []),
                    "system_preview": truncate_text(kwargs.get("system")),
                    "max_tokens": kwargs.get("max_tokens"),
                },
            )
            start = now_ns()
            try:
                resp = _originals["messages_create"](self, *args, **kwargs)
            except Exception as e:
                emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                           duration_ms=ns_to_ms(start, now_ns()),
                           error={"code": type(e).__name__, "message": str(e)},
                           severity="error", data={"provider": "anthropic", "model": model})
                raise

            tokens = extract_anthropic_tokens(resp)
            cost = calc_cost("anthropic", model, tokens["prompt"], tokens["completion"]) if tokens else None
            emit_event(
                client, agent_id=agent_id, event_type="llm.completion.response",
                duration_ms=ns_to_ms(start, now_ns()),
                data={
                    "provider": "anthropic",
                    "model": model,
                    "stop_reason": getattr(resp, "stop_reason", None),
                    "response_preview": _preview_anthropic_response(resp),
                },
                tokens=tokens,
                cost=cost,
            )
            return resp

        mark_patched(messages_create)
        Messages.create = messages_create  # type: ignore[assignment]

    # Async resource
    try:
        from anthropic.resources.messages import AsyncMessages  # type: ignore
        if not already_patched(AsyncMessages.create):
            _originals["async_messages_create"] = AsyncMessages.create

            async def async_messages_create(self: Any, *args: Any, **kwargs: Any) -> Any:
                model = kwargs.get("model") or "unknown"
                ensure_context()
                emit_event(client, agent_id=agent_id, event_type="llm.completion.request",
                           data={"provider": "anthropic", "model": model})
                start = now_ns()
                try:
                    resp = await _originals["async_messages_create"](self, *args, **kwargs)
                except Exception as e:
                    emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                               duration_ms=ns_to_ms(start, now_ns()),
                               error={"code": type(e).__name__, "message": str(e)},
                               severity="error", data={"provider": "anthropic", "model": model})
                    raise
                tokens = extract_anthropic_tokens(resp)
                cost = calc_cost("anthropic", model, tokens["prompt"], tokens["completion"]) if tokens else None
                emit_event(client, agent_id=agent_id, event_type="llm.completion.response",
                           duration_ms=ns_to_ms(start, now_ns()),
                           data={"provider": "anthropic", "model": model},
                           tokens=tokens, cost=cost)
                return resp

            mark_patched(async_messages_create)
            AsyncMessages.create = async_messages_create  # type: ignore[assignment]
    except Exception:
        pass


def uninstall() -> None:
    try:
        from anthropic.resources.messages import Messages  # type: ignore
        if "messages_create" in _originals:
            Messages.create = _originals.pop("messages_create")
    except Exception:
        pass
    try:
        from anthropic.resources.messages import AsyncMessages  # type: ignore
        if "async_messages_create" in _originals:
            AsyncMessages.create = _originals.pop("async_messages_create")
    except Exception:
        pass
    _originals.clear()


def _preview_anthropic_response(resp: Any) -> Optional[str]:
    try:
        content = getattr(resp, "content", None)
        if not content:
            return None
        if isinstance(content, list) and content:
            first = content[0]
            text = getattr(first, "text", None)
            if text:
                return truncate_text(text)
    except Exception:
        pass
    return None
