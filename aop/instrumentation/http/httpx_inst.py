"""``httpx`` (sync + async) instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING
from urllib.parse import urlsplit

from .._common import (
    already_patched,
    emit_event,
    ensure_context,
    mark_patched,
    now_ns,
    ns_to_ms,
)

if TYPE_CHECKING:
    from ...client import AOPClient

_DEFAULT_AGENT_ID = "http-client"
_orig_sync_send = None  # type: ignore[var-annotated]
_orig_async_send = None  # type: ignore[var-annotated]


def _emit_request(client: Any, agent_id: str, request: Any) -> None:
    url = str(request.url)
    parsed = urlsplit(url)
    emit_event(
        client,
        agent_id=agent_id,
        event_type="http.client.request",
        data={
            "method": request.method,
            "url": url,
            "host": parsed.netloc,
            "path": parsed.path,
            "request_size": len(request.content or b""),
        },
    )


def _emit_response(client: Any, agent_id: str, request: Any, response: Any, dur_ms: int) -> None:
    url = str(request.url)
    parsed = urlsplit(url)
    status = getattr(response, "status_code", 0)
    emit_event(
        client,
        agent_id=agent_id,
        event_type="http.client.response",
        duration_ms=dur_ms,
        data={
            "method": request.method,
            "url": url,
            "host": parsed.netloc,
            "path": parsed.path,
            "status_code": status,
        },
        severity="error" if status >= 500 else None,
    )


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _DEFAULT_AGENT_ID) -> None:
    global _orig_sync_send, _orig_async_send
    try:
        import httpx
    except ImportError:
        return

    if not already_patched(httpx.Client.send):
        _orig_sync_send = httpx.Client.send

        def sync_send(self: Any, request: Any, **kwargs: Any) -> Any:
            ctx = ensure_context()
            try:
                from ...propagation import inject as _inject
                _inject(request.headers, ctx)
            except Exception:
                pass
            _emit_request(client, agent_id, request)
            start = now_ns()
            try:
                resp = _orig_sync_send(self, request, **kwargs)
            except Exception as e:
                emit_event(
                    client, agent_id=agent_id, event_type="http.client.error",
                    duration_ms=ns_to_ms(start, now_ns()),
                    error={"code": type(e).__name__, "message": str(e)},
                    severity="error",
                )
                raise
            _emit_response(client, agent_id, request, resp, ns_to_ms(start, now_ns()))
            return resp

        mark_patched(sync_send)
        httpx.Client.send = sync_send  # type: ignore[assignment]

    if not already_patched(httpx.AsyncClient.send):
        _orig_async_send = httpx.AsyncClient.send

        async def async_send(self: Any, request: Any, **kwargs: Any) -> Any:
            ctx = ensure_context()
            try:
                from ...propagation import inject as _inject
                _inject(request.headers, ctx)
            except Exception:
                pass
            _emit_request(client, agent_id, request)
            start = now_ns()
            try:
                resp = await _orig_async_send(self, request, **kwargs)
            except Exception as e:
                emit_event(
                    client, agent_id=agent_id, event_type="http.client.error",
                    duration_ms=ns_to_ms(start, now_ns()),
                    error={"code": type(e).__name__, "message": str(e)},
                    severity="error",
                )
                raise
            _emit_response(client, agent_id, request, resp, ns_to_ms(start, now_ns()))
            return resp

        mark_patched(async_send)
        httpx.AsyncClient.send = async_send  # type: ignore[assignment]


def uninstall() -> None:
    global _orig_sync_send, _orig_async_send
    try:
        import httpx
        if _orig_sync_send is not None:
            httpx.Client.send = _orig_sync_send  # type: ignore[assignment]
        if _orig_async_send is not None:
            httpx.AsyncClient.send = _orig_async_send  # type: ignore[assignment]
    except Exception:
        pass
    _orig_sync_send = None
    _orig_async_send = None
