"""Ollama Python SDK instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "ollama-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        import ollama  # type: ignore
    except ImportError:
        return
    targets = []
    for fname in ("chat", "generate", "embeddings"):
        fn = getattr(ollama, fname, None)
        if fn and not already_patched(fn):
            targets.append((fname, fn))

    for fname, fn in targets:
        _originals[fname] = fn

        def make_wrapper(name: str, original: Any) -> Any:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                model = kwargs.get("model") or "unknown"
                ensure_context()
                emit_event(client, agent_id=agent_id, event_type=f"llm.{name}.request",
                           data={"provider": "ollama", "model": model})
                start = now_ns()
                try:
                    resp = original(*args, **kwargs)
                except Exception as e:
                    emit_event(client, agent_id=agent_id, event_type=f"llm.{name}.error",
                               duration_ms=ns_to_ms(start, now_ns()),
                               error={"code": type(e).__name__, "message": str(e)}, severity="error",
                               data={"provider": "ollama", "model": model})
                    raise
                emit_event(client, agent_id=agent_id, event_type=f"llm.{name}.response",
                           duration_ms=ns_to_ms(start, now_ns()),
                           data={"provider": "ollama", "model": model})
                return resp
            mark_patched(wrapper)
            return wrapper

        setattr(ollama, fname, make_wrapper(fname, fn))


def uninstall() -> None:
    try:
        import ollama  # type: ignore
        for fname, fn in list(_originals.items()):
            setattr(ollama, fname, fn)
    except Exception:
        pass
    _originals.clear()
