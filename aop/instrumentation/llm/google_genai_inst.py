"""Google GenAI (google-genai) SDK instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import calc_cost, truncate_text

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "google-genai"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from google.genai import models as _models  # type: ignore
    except Exception:
        return

    cls = getattr(_models, "Models", None)
    if cls is None or already_patched(getattr(cls, "generate_content", None)):
        return
    if not hasattr(cls, "generate_content"):
        return
    _originals["generate_content"] = cls.generate_content

    def generate_content(self: Any, *args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model") or (args[0] if args else "unknown")
        ensure_context()
        emit_event(client, agent_id=agent_id, event_type="llm.completion.request",
                   data={"provider": "google", "model": model,
                         "contents_preview": truncate_text(str(kwargs.get("contents")))})
        start = now_ns()
        try:
            resp = _originals["generate_content"](self, *args, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)},
                       severity="error", data={"provider": "google", "model": model})
            raise
        tokens = _extract_google_tokens(resp)
        cost = calc_cost("google", model, tokens["prompt"], tokens["completion"]) if tokens else None
        emit_event(client, agent_id=agent_id, event_type="llm.completion.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"provider": "google", "model": model},
                   tokens=tokens, cost=cost)
        return resp

    mark_patched(generate_content)
    cls.generate_content = generate_content  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from google.genai import models as _models  # type: ignore
        cls = getattr(_models, "Models", None)
        if cls and "generate_content" in _originals:
            cls.generate_content = _originals.pop("generate_content")
    except Exception:
        pass
    _originals.clear()


def _extract_google_tokens(resp: Any) -> Optional[dict]:
    try:
        usage = getattr(resp, "usage_metadata", None)
        if usage is None:
            return None
        prompt = getattr(usage, "prompt_token_count", 0) or 0
        completion = getattr(usage, "candidates_token_count", 0) or 0
        total = getattr(usage, "total_token_count", prompt + completion) or (prompt + completion)
        return {"prompt": int(prompt), "completion": int(completion), "total": int(total)}
    except Exception:
        return None
