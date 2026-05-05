"""``aiohttp`` ClientSession instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING
from urllib.parse import urlsplit

from .._common import (
    already_patched, emit_event, ensure_context,
    mark_patched, now_ns, ns_to_ms,
)

if TYPE_CHECKING:
    from ...client import AOPClient

_DEFAULT_AGENT_ID = "http-client"
_orig_request = None  # type: ignore[var-annotated]


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _DEFAULT_AGENT_ID) -> None:
    global _orig_request
    try:
        import aiohttp
    except ImportError:
        return
    if already_patched(aiohttp.ClientSession._request):  # type: ignore[attr-defined]
        return
    _orig_request = aiohttp.ClientSession._request

    async def patched_request(self: Any, method: str, url: Any, **kwargs: Any) -> Any:
        ctx = ensure_context()
        headers = kwargs.get("headers") or {}
        if not isinstance(headers, dict):
            headers = dict(headers)
        try:
            from ...propagation import inject as _inject
            _inject(headers, ctx)
            kwargs["headers"] = headers
        except Exception:
            pass

        url_str = str(url)
        parsed = urlsplit(url_str)
        emit_event(
            client, agent_id=agent_id, event_type="http.client.request",
            data={"method": method, "url": url_str, "host": parsed.netloc, "path": parsed.path},
        )

        start = now_ns()
        try:
            resp = await _orig_request(self, method, url, **kwargs)
        except Exception as e:
            emit_event(
                client, agent_id=agent_id, event_type="http.client.error",
                duration_ms=ns_to_ms(start, now_ns()),
                error={"code": type(e).__name__, "message": str(e)},
                severity="error",
            )
            raise

        status = getattr(resp, "status", 0)
        emit_event(
            client, agent_id=agent_id, event_type="http.client.response",
            duration_ms=ns_to_ms(start, now_ns()),
            data={"method": method, "url": url_str, "status_code": status},
            severity="error" if status >= 500 else None,
        )
        return resp

    mark_patched(patched_request)
    aiohttp.ClientSession._request = patched_request  # type: ignore[assignment]


def uninstall() -> None:
    global _orig_request
    try:
        import aiohttp
        if _orig_request is not None:
            aiohttp.ClientSession._request = _orig_request  # type: ignore[assignment]
    except Exception:
        pass
    _orig_request = None
