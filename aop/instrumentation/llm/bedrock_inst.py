"""AWS Bedrock instrumentation (boto3 client.invoke_model)."""

from __future__ import annotations

import json
from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms
from ._llm_common import calc_cost

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "bedrock-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        import boto3  # type: ignore
    except ImportError:
        return

    # We patch botocore.client.BaseClient._make_api_call so we hit every
    # bedrock-runtime call uniformly. We only emit events for known operations.
    try:
        from botocore.client import BaseClient  # type: ignore
    except Exception:
        return
    if already_patched(BaseClient._make_api_call):  # type: ignore[attr-defined]
        return
    _originals["_make_api_call"] = BaseClient._make_api_call

    BEDROCK_OPS = {
        "InvokeModel", "InvokeModelWithResponseStream",
        "Converse", "ConverseStream",
    }

    def _make_api_call(self: Any, operation: str, params: Any) -> Any:
        if not (operation in BEDROCK_OPS and getattr(self, "meta", None)
                and "bedrock" in str(getattr(self.meta, "service_model", "")).lower()):
            return _originals["_make_api_call"](self, operation, params)

        ensure_context()
        model = params.get("modelId") or "unknown"
        emit_event(client, agent_id=agent_id, event_type="llm.completion.request",
                   data={"provider": "bedrock", "model": model, "operation": operation})
        start = now_ns()
        try:
            resp = _originals["_make_api_call"](self, operation, params)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="llm.completion.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"provider": "bedrock", "model": model})
            raise

        tokens = _extract_bedrock_tokens(resp)
        cost = calc_cost("bedrock", model, tokens["prompt"], tokens["completion"]) if tokens else None
        emit_event(client, agent_id=agent_id, event_type="llm.completion.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"provider": "bedrock", "model": model, "operation": operation},
                   tokens=tokens, cost=cost)
        return resp

    mark_patched(_make_api_call)
    BaseClient._make_api_call = _make_api_call  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from botocore.client import BaseClient  # type: ignore
        if "_make_api_call" in _originals:
            BaseClient._make_api_call = _originals.pop("_make_api_call")
    except Exception:
        pass
    _originals.clear()


def _extract_bedrock_tokens(resp: Any) -> Optional[dict]:
    try:
        usage = resp.get("usage") if isinstance(resp, dict) else None
        if usage:
            prompt = int(usage.get("inputTokens", 0))
            completion = int(usage.get("outputTokens", 0))
            return {"prompt": prompt, "completion": completion, "total": prompt + completion}
        # InvokeModel returns body with inline JSON
        body = resp.get("body") if isinstance(resp, dict) else None
        if body and hasattr(body, "read"):
            data = body.read()
            try:
                parsed = json.loads(data)
            except Exception:
                return None
            usage = parsed.get("usage") or {}
            prompt = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
            completion = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
            if prompt or completion:
                return {"prompt": prompt, "completion": completion, "total": prompt + completion}
    except Exception:
        return None
    return None
