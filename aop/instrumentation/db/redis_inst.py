"""redis-py instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "redis-client"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from redis import Redis  # type: ignore
    except ImportError:
        return
    if not hasattr(Redis, "execute_command") or already_patched(Redis.execute_command):
        return
    _originals["execute_command"] = Redis.execute_command

    def execute_command(self: Any, *args: Any, **options: Any) -> Any:
        ensure_context()
        cmd = str(args[0]) if args else "?"
        start = now_ns()
        try:
            res = _originals["execute_command"](self, *args, **options)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="cache.command.error",
                       duration_ms=ns_to_ms(start, now_ns()),
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"vendor": "redis", "command": cmd})
            raise
        emit_event(client, agent_id=agent_id, event_type="cache.command.completed",
                   duration_ms=ns_to_ms(start, now_ns()),
                   data={"vendor": "redis", "command": cmd})
        return res

    mark_patched(execute_command)
    Redis.execute_command = execute_command  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from redis import Redis  # type: ignore
        if "execute_command" in _originals:
            Redis.execute_command = _originals.pop("execute_command")
    except Exception:
        pass
    _originals.clear()
