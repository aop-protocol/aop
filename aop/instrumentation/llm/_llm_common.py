"""Common helpers for LLM SDK instrumentation: token extraction, cost lookup."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# Lazy import — we don't want to make pricing a hard dep here.

def calc_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> Optional[Dict[str, Any]]:
    try:
        from ...pricing import compute_cost
    except Exception:
        return None
    try:
        return compute_cost(provider=provider, model=model,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens)
    except Exception:
        return None


def extract_openai_tokens(response: Any) -> Optional[Dict[str, int]]:
    """Extract prompt/completion/total tokens from an OpenAI response object."""
    try:
        usage = getattr(response, "usage", None) or (response.get("usage") if isinstance(response, dict) else None)
        if usage is None:
            return None
        prompt = getattr(usage, "prompt_tokens", None)
        completion = getattr(usage, "completion_tokens", None)
        total = getattr(usage, "total_tokens", None)
        if prompt is None and isinstance(usage, dict):
            prompt = usage.get("prompt_tokens")
            completion = usage.get("completion_tokens")
            total = usage.get("total_tokens")
        if prompt is None:
            return None
        return {
            "prompt": int(prompt or 0),
            "completion": int(completion or 0),
            "total": int(total or (prompt or 0) + (completion or 0)),
        }
    except Exception:
        return None


def extract_anthropic_tokens(response: Any) -> Optional[Dict[str, int]]:
    try:
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return None
        prompt = getattr(usage, "input_tokens", None)
        completion = getattr(usage, "output_tokens", None)
        if prompt is None and isinstance(usage, dict):
            prompt = usage.get("input_tokens")
            completion = usage.get("output_tokens")
        if prompt is None:
            return None
        return {
            "prompt": int(prompt or 0),
            "completion": int(completion or 0),
            "total": int((prompt or 0) + (completion or 0)),
        }
    except Exception:
        return None


def truncate_text(value: Any, max_chars: int = 200) -> Any:
    """Best-effort truncation of long content for safe attribute capture."""
    if isinstance(value, str) and len(value) > max_chars:
        return value[:max_chars] + f"... (+{len(value) - max_chars} chars)"
    return value


def summarize_messages(messages: Any, max_chars: int = 200) -> Optional[list]:
    """Return a compact list of {role, content_preview} entries."""
    if not isinstance(messages, list):
        return None
    out = []
    for m in messages[:32]:
        if isinstance(m, dict):
            role = m.get("role")
            content = m.get("content")
        else:
            role = getattr(m, "role", None)
            content = getattr(m, "content", None)
        if isinstance(content, list):
            # multimodal — keep type counts only
            content = f"[{len(content)} parts]"
        out.append({"role": role, "preview": truncate_text(content, max_chars)})
    return out
