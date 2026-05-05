"""``urllib3`` PoolManager instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_DEFAULT_AGENT_ID = "http-client"
_orig_urlopen = None  # type: ignore[var-annotated]


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _DEFAULT_AGENT_ID) -> None:
    global _orig_urlopen
    try:
        import urllib3
    except ImportError:
        return
    if already_patched(urllib3.PoolManager.urlopen):
        return
    _orig_urlopen = urllib3.PoolManager.urlopen

    def patched_urlopen(self: Any, method: str, url: str, **kwargs: Any) -> Any:
        ctx = ensure_context()
        headers = kwargs.get("headers") or {}
        try:
            headers = dict(headers)
            from ...propagation import inject as _inject
            _inject(headers, ctx)
            kwargs["headers"] = headers
        except Exception:
            pass

        emit_event(client, agent_id=agent_id, event_type="http.client.request",
                   data={"method": method, "url": url})
        start = now_ns()
        try:
            resp = _orig_urlopen(self, method, url, **kwargs)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="http.client.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)},
                       severity="error")
            raise
        emit_event(client, agent_id=agent_id, event_type="http.client.response",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"method": method, "url": url,
                         "status_code": getattr(resp, "status", 0)})
        return resp

    mark_patched(patched_urlopen)
    urllib3.PoolManager.urlopen = patched_urlopen  # type: ignore[assignment]


def uninstall() -> None:
    global _orig_urlopen
    try:
        import urllib3
        if _orig_urlopen is not None:
            urllib3.PoolManager.urlopen = _orig_urlopen  # type: ignore[assignment]
    except Exception:
        pass
    _orig_urlopen = None
