"""``requests`` library instrumentation.

Patches ``requests.Session.send`` to:

  • inject W3C ``traceparent`` headers into outgoing requests
  • emit ``http.client.request`` and ``http.client.response`` events
  • capture method, URL, status code, byte sizes, latency, and errors

We patch the ``Session`` because the module-level ``requests.get`` /
``requests.post`` helpers all funnel through it.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING
from urllib.parse import urlsplit

from .._common import (
    already_patched,
    emit_event,
    ensure_context,
    inject_into_kwargs_headers,
    mark_patched,
    now_ns,
    ns_to_ms,
    safe,
)

if TYPE_CHECKING:
    from ...client import AOPClient


_DEFAULT_AGENT_ID = "http-client"
_original_send = None  # type: ignore[var-annotated]


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _DEFAULT_AGENT_ID) -> None:
    global _original_send
    try:
        import requests
    except ImportError:
        return
    if already_patched(requests.Session.send):
        return

    _original_send = requests.Session.send

    def patched_send(self: Any, request: Any, **kwargs: Any) -> Any:
        ctx = ensure_context()
        try:
            if request.headers is not None:
                from ...propagation import inject as _inject
                _inject(request.headers, ctx)
        except Exception:
            pass

        url = getattr(request, "url", "") or ""
        method = getattr(request, "method", "GET") or "GET"
        parsed = urlsplit(url) if url else None
        host = parsed.netloc if parsed else ""
        path = parsed.path if parsed else ""

        req_size = len(request.body) if getattr(request, "body", None) else 0

        emit_event(
            client,
            agent_id=agent_id,
            event_type="http.client.request",
            data={
                "method": method,
                "url": url,
                "host": host,
                "path": path,
                "request_size": req_size,
            },
        )

        start = now_ns()
        try:
            response = _original_send(self, request, **kwargs)
        except Exception as e:
            emit_event(
                client,
                agent_id=agent_id,
                event_type="http.client.error",
                duration_ms=ns_to_ms(start, now_ns()),
                error={"code": type(e).__name__, "message": str(e)},
                severity="error",
                data={"method": method, "url": url},
            )
            raise

        status = getattr(response, "status_code", 0)
        emit_event(
            client,
            agent_id=agent_id,
            event_type="http.client.response",
            duration_ms=ns_to_ms(start, now_ns()),
            data={
                "method": method,
                "url": url,
                "host": host,
                "path": path,
                "status_code": status,
                "response_size": len(response.content) if hasattr(response, "content") else 0,
            },
            severity="error" if status >= 500 else None,
        )
        return response

    mark_patched(patched_send)
    requests.Session.send = patched_send  # type: ignore[assignment]


def uninstall() -> None:
    global _original_send
    if _original_send is None:
        return
    try:
        import requests
        requests.Session.send = _original_send  # type: ignore[assignment]
    except Exception:
        pass
    _original_send = None
