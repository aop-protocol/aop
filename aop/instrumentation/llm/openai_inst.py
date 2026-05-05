"""OpenAI SDK instrumentation (v1.x).

Patches both the chat-completions and Responses API. Captures model, message
preview, token usage, finish reason, tool calls, and computes cost via the
pricing book. Streaming responses are accommodated by wrapping the iterator
and emitting the usage event when the stream finishes.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import (
    calc_cost,
    extract_openai_tokens,
    summarize_messages,
    truncate_text,
)

if TYPE_CHECKING:
    from ...client import AOPClient

_DEFAULT_AGENT_ID = "openai-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _DEFAULT_AGENT_ID) -> None:
    try:
        import openai
    except ImportError:
        return

    # Patch chat.completions.create on the resource class
    try:
        from openai.resources.chat.completions import Completions  # type: ignore
        if not already_patched(Completions.create):
            _originals["chat_create"] = Completions.create

            def chat_create(self: Any, *args: Any, **kwargs: Any) -> Any:
                model = kwargs.get("model") or "unknown"
                messages = kwargs.get("messages") or []
                stream = kwargs.get("stream", False)

                ensure_context()
                emit_event(
                    client, agent_id=agent_id, event_type="llm.completion.request",
                    data={
                        "provider": "openai",
                        "model": model,
                        "stream": bool(stream),
                        "messages_preview": summarize_messages(messages),
                        "n": kwargs.get("n", 1),
                        "temperature": kwargs.get("temperature"),
                        "max_tokens": kwargs.get("max_tokens"),
                    },
                )
                start = now_ns()
                try:
                    resp = _originals["chat_create"](self, *args, **kwargs)
                except Exception as e:
                    emit_event(
                        client, agent_id=agent_id, event_type="llm.completion.error",
                        duration_ms=ns_to_ms(start, now_ns()),
                        error={"code": type(e).__name__, "message": str(e)},
                        severity="error",
                        data={"provider": "openai", "model": model},
                    )
                    raise

                if stream:
                    return _wrap_stream_iter(client, agent_id, "openai", model, resp, start)

                tokens = extract_openai_tokens(resp)
                cost = calc_cost("openai", model, tokens["prompt"], tokens["completion"]) if tokens else None
                emit_event(
                    client, agent_id=agent_id, event_type="llm.completion.response",
                    duration_ms=ns_to_ms(start, now_ns()),
                    data={
                        "provider": "openai",
                        "model": model,
                        "finish_reason": _get_finish_reason(resp),
                        "response_preview": _get_response_preview(resp),
                    },
                    tokens=tokens,
                    cost=cost,
                )
                return resp

            mark_patched(chat_create)
            Completions.create = chat_create  # type: ignore[assignment]
    except Exception:
        pass

    # Responses API (newer surface)
    try:
        from openai.resources.responses import Responses  # type: ignore
        if not already_patched(Responses.create):
            _originals["responses_create"] = Responses.create

            def responses_create(self: Any, *args: Any, **kwargs: Any) -> Any:
                model = kwargs.get("model") or "unknown"
                ensure_context()
                emit_event(client, agent_id=agent_id, event_type="llm.responses.request",
                           data={"provider": "openai", "model": model,
                                 "input_preview": truncate_text(kwargs.get("input"))})
                start = now_ns()
                try:
                    resp = _originals["responses_create"](self, *args, **kwargs)
                except Exception as e:
                    emit_event(client, agent_id=agent_id, event_type="llm.responses.error",
                               duration_ms=ns_to_ms(start, now_ns()),
                               error={"code": type(e).__name__, "message": str(e)},
                               severity="error", data={"provider": "openai", "model": model})
                    raise
                tokens = extract_openai_tokens(resp)
                cost = calc_cost("openai", model, tokens["prompt"], tokens["completion"]) if tokens else None
                emit_event(client, agent_id=agent_id, event_type="llm.responses.response",
                           duration_ms=ns_to_ms(start, now_ns()),
                           data={"provider": "openai", "model": model},
                           tokens=tokens, cost=cost)
                return resp

            mark_patched(responses_create)
            Responses.create = responses_create  # type: ignore[assignment]
    except Exception:
        pass

    # Embeddings
    try:
        from openai.resources.embeddings import Embeddings  # type: ignore
        if not already_patched(Embeddings.create):
            _originals["embeddings_create"] = Embeddings.create

            def emb_create(self: Any, *args: Any, **kwargs: Any) -> Any:
                model = kwargs.get("model") or "unknown"
                ensure_context()
                start = now_ns()
                try:
                    resp = _originals["embeddings_create"](self, *args, **kwargs)
                except Exception as e:
                    emit_event(client, agent_id=agent_id, event_type="llm.embedding.error",
                               duration_ms=ns_to_ms(start, now_ns()),
                               error={"code": type(e).__name__, "message": str(e)},
                               severity="error", data={"provider": "openai", "model": model})
                    raise
                tokens = extract_openai_tokens(resp)
                cost = calc_cost("openai", model, tokens["prompt"], 0) if tokens else None
                emit_event(client, agent_id=agent_id, event_type="llm.embedding.response",
                           duration_ms=ns_to_ms(start, now_ns()),
                           data={"provider": "openai", "model": model,
                                 "dimensions": _embedding_dim(resp)},
                           tokens=tokens, cost=cost)
                return resp

            mark_patched(emb_create)
            Embeddings.create = emb_create  # type: ignore[assignment]
    except Exception:
        pass


def uninstall() -> None:
    try:
        from openai.resources.chat.completions import Completions  # type: ignore
        if "chat_create" in _originals:
            Completions.create = _originals.pop("chat_create")
    except Exception:
        pass
    try:
        from openai.resources.responses import Responses  # type: ignore
        if "responses_create" in _originals:
            Responses.create = _originals.pop("responses_create")
    except Exception:
        pass
    try:
        from openai.resources.embeddings import Embeddings  # type: ignore
        if "embeddings_create" in _originals:
            Embeddings.create = _originals.pop("embeddings_create")
    except Exception:
        pass
    _originals.clear()


def _get_finish_reason(resp: Any) -> Optional[str]:
    try:
        choices = getattr(resp, "choices", None) or (resp.get("choices") if isinstance(resp, dict) else None)
        if choices:
            first = choices[0]
            return getattr(first, "finish_reason", None) or first.get("finish_reason")
    except Exception:
        pass
    return None


def _get_response_preview(resp: Any) -> Optional[str]:
    try:
        choices = getattr(resp, "choices", None) or (resp.get("choices") if isinstance(resp, dict) else None)
        if not choices:
            return None
        first = choices[0]
        msg = getattr(first, "message", None) or first.get("message")
        if msg is None:
            return None
        content = getattr(msg, "content", None) or msg.get("content")
        return truncate_text(content)
    except Exception:
        return None


def _embedding_dim(resp: Any) -> Optional[int]:
    try:
        data = getattr(resp, "data", None) or (resp.get("data") if isinstance(resp, dict) else None)
        if data:
            first = data[0]
            emb = getattr(first, "embedding", None) or first.get("embedding")
            return len(emb) if emb else None
    except Exception:
        pass
    return None


def _wrap_stream_iter(client: Any, agent_id: str, provider: str, model: str, stream: Any, start_ns: int) -> Any:
    """Wrap a streaming response so we still emit a single response event."""

    class _Wrapper:
        def __init__(self, inner: Any) -> None:
            self._inner = inner
            self._chunks = 0
            self._content_chars = 0
            self._closed = False
            self._tokens: Optional[dict] = None

        def __iter__(self) -> Any:
            return self

        def __next__(self) -> Any:
            try:
                chunk = next(self._inner)
            except StopIteration:
                self._finalize()
                raise
            self._absorb(chunk)
            return chunk

        def __aiter__(self) -> Any:  # async streams use the underlying obj
            return self._inner.__aiter__()

        def _absorb(self, chunk: Any) -> None:
            self._chunks += 1
            try:
                # SSE-style usage in last chunk in newer SDKs
                u = getattr(chunk, "usage", None)
                if u is not None:
                    tok = extract_openai_tokens(chunk)
                    if tok:
                        self._tokens = tok
                # accumulate content length for preview
                choices = getattr(chunk, "choices", None) or []
                for c in choices:
                    delta = getattr(c, "delta", None) or {}
                    text = getattr(delta, "content", None) or (
                        delta.get("content") if isinstance(delta, dict) else None
                    )
                    if isinstance(text, str):
                        self._content_chars += len(text)
            except Exception:
                pass

        def _finalize(self) -> None:
            if self._closed:
                return
            self._closed = True
            cost = (
                calc_cost(provider, model, self._tokens["prompt"], self._tokens["completion"])
                if self._tokens else None
            )
            emit_event(
                client, agent_id=agent_id, event_type="llm.completion.response",
                duration_ms=ns_to_ms(start_ns, now_ns()),
                data={"provider": provider, "model": model, "stream": True,
                      "stream_chunks": self._chunks, "stream_chars": self._content_chars},
                tokens=self._tokens, cost=cost,
            )

    return _Wrapper(stream)
