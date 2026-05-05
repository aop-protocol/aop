"""Generic adapter scaffold for community-contributed protocols.

Subclass ``GenericAdapter`` and call ``register_protocol`` to add support
for any new protocol without modifying core AOP code.

Example:
    from aop.registry import ProtocolSpec, register_protocol
    from aop.adapters.generic import GenericAdapter

    register_protocol(ProtocolSpec(
        name="myproto",
        event_types=frozenset({
            "myproto.foo.started", "myproto.foo.completed",
        }),
    ))

    class MyProtoAdapter(GenericAdapter):
        PROTOCOL = "myproto"

        def log_foo_started(self, agent_id, foo_id, **kw):
            return self.log("myproto.foo.started",
                            agent_id=agent_id,
                            data={"foo_id": foo_id}, **kw)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseAdapter, EventHandle


class GenericAdapter(BaseAdapter):
    """Base class for community/third-party protocol adapters."""

    PROTOCOL: str = "x"

    def log(
        self,
        event_type: str,
        *,
        agent_id: str,
        data: Optional[Dict[str, Any]] = None,
        severity: Optional[str] = None,
        duration_ms: Optional[int] = None,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> EventHandle:
        if not event_type.startswith(f"{self.PROTOCOL}."):
            raise ValueError(
                f"event_type {event_type!r} must start with "
                f"{self.PROTOCOL!r} prefix"
            )
        ev = self._build_event(
            agent_id=agent_id, event_type=event_type, data=data,
            severity=severity, duration_ms=duration_ms,
            parent_id=parent_id, correlation_id=correlation_id,
            metadata=metadata, error=error,
        )
        return self._log_and_return_handle(ev)
