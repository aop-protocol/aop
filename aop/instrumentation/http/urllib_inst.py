"""``urllib.request`` instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_DEFAULT_AGENT_ID = "http-client"
_orig_open = None  # type: ignore[var-annotated]


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _DEFAULT_AGENT_ID) -> None:
    global _orig_open
    import urllib.request as _ur
    if already_patched(_ur.OpenerDirector.open):
        return
    _orig_open = _ur.OpenerDirector.open

    def patched_open(self: Any, fullurl: Any, data: Any = None, timeout: Any = ...) -> Any:
        ctx = ensure_context()
        try:
            if hasattr(fullurl, "add_header"):
                fullurl.add_header("traceparent", f"00-{ctx.trace_id}-{ctx.span_id}-01")
        except Exception:
            pass

        url = fullurl.full_url if hasattr(fullurl, "full_url") else str(fullurl)
        method = getattr(fullurl, "method", "GET")
        emit_event(client, agent_id=agent_id, event_type="http.client.request",
                   data={"method": method, "url": url})
        start = now_ns()
        try:
            resp = _orig_open(self, fullurl) if timeout is ... else _orig_open(self, fullurl, data, timeout)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="http.client.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)},
                       severity="error")
            raise
        status = getattr(resp, "status", 0) or 0
        emit_event(client, agent_id=agent_id, event_type="http.client.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"method": method, "url": url, "status_code": status})
        return resp

    mark_patched(patched_open)
    _ur.OpenerDirector.open = patched_open  # type: ignore[assignment]


def uninstall() -> None:
    global _orig_open
    try:
        import urllib.request as _ur
        if _orig_open is not None:
            _ur.OpenerDirector.open = _orig_open  # type: ignore[assignment]
    except Exception:
        pass
    _orig_open = None
