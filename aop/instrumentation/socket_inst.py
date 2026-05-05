"""TCP socket-level instrumentation (opt-in, off by default).

Wraps ``socket.socket.connect`` to emit ``tcp.connection.opened`` events
for outbound TCP connections. Intentionally disabled unless ``install()``
is called explicitly because it is high-volume and privacy-relevant.

Use cases:
  • debugging zero-trust deployments where every outbound connection must
    be auditable
  • surfacing connections initiated by libraries we don't have specific
    instrumentation for
  • CTF / security research

This integration does NOT capture payload bytes.
"""

from __future__ import annotations

import socket as _socket
from typing import Any, Optional, TYPE_CHECKING

from ._common import already_patched, emit_event, ensure_context, mark_patched

if TYPE_CHECKING:
    from ..client import AOPClient

_AGENT = "tcp-monitor"
_orig_connect = None  # type: ignore[var-annotated]


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    global _orig_connect
    if already_patched(_socket.socket.connect):
        return
    _orig_connect = _socket.socket.connect

    def connect(self: Any, address: Any) -> Any:
        ensure_context()
        try:
            host, port = address if isinstance(address, tuple) else (str(address), None)
        except Exception:
            host, port = (str(address), None)
        emit_event(client, agent_id=agent_id, event_type="tcp.connection.opened",
                   data={"host": host, "port": port,
                         "family": int(self.family), "type": int(self.type)})
        try:
            return _orig_connect(self, address)
        except Exception as e:
            emit_event(client, agent_id=agent_id, event_type="tcp.connection.error",
                       error={"code": type(e).__name__, "message": str(e)}, severity="error",
                       data={"host": host, "port": port})
            raise

    mark_patched(connect)
    _socket.socket.connect = connect  # type: ignore[assignment]


def uninstall() -> None:
    global _orig_connect
    if _orig_connect is not None:
        _socket.socket.connect = _orig_connect  # type: ignore[assignment]
    _orig_connect = None
