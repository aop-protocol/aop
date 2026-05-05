"""
AOP Protocol Registry (Phase 0.1)

Replaces the closed-set Protocol enum and ALL_EVENT_TYPES list with an
extensible registry so that ANY agent communication protocol can register
its event vocabulary at runtime.

Built-in protocols (MCP, A2A, AP2) are registered automatically when this
module is imported. Third-party protocols can register themselves with:

    from aop.registry import register_protocol, ProtocolSpec

    register_protocol(ProtocolSpec(
        name="acp",
        version="0.1",
        event_types={"acp.invocation.started", "acp.invocation.completed"},
        description="IBM Agent Communication Protocol",
    ))

The registry is intentionally process-local (no I/O) so that import-time
registration is fast and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Dict, FrozenSet, Iterable, Optional, Set


# ---------------------------------------------------------------------------
# ProtocolSpec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolSpec:
    """Declarative spec for a protocol that can be observed by AOP.

    Attributes:
        name:           Lower-case protocol identifier (e.g. "mcp", "acp").
                        Becomes the first segment of every event_type.
        version:        Spec version (free-form, e.g. "1.0").
        event_types:    Closed set of canonical event types. Custom event
                        types under the same namespace are still allowed via
                        the ``<protocol>.custom.<org>.<category>.<action>``
                        pattern.
        description:    Human-readable description for docs/registry UI.
        required_data_keys: Mapping of event_type -> set of required keys
                        in the event ``data`` payload. Optional; the registry
                        does not enforce keys unless ``strict_data`` is True.
        strict_data:    If True, validation will reject events whose ``data``
                        is missing any of the keys declared in
                        ``required_data_keys``.
    """

    name: str
    version: str = "1.0"
    event_types: FrozenSet[str] = field(default_factory=frozenset)
    description: str = ""
    required_data_keys: Dict[str, FrozenSet[str]] = field(default_factory=dict)
    strict_data: bool = False

    def __post_init__(self) -> None:
        if not self.name or not self.name.islower():
            raise ValueError(
                f"Protocol name must be lower-case and non-empty, got: {self.name!r}"
            )
        if any("." in part for part in [self.name]):
            raise ValueError(f"Protocol name must not contain '.': {self.name!r}")
        for et in self.event_types:
            if not et.startswith(f"{self.name}."):
                raise ValueError(
                    f"event_type {et!r} does not start with protocol prefix "
                    f"{self.name!r}."
                )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class _ProtocolRegistry:
    """Singleton registry of protocol specs."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._specs: Dict[str, ProtocolSpec] = {}

    # -- registration ------------------------------------------------------

    def register(self, spec: ProtocolSpec, *, replace: bool = False) -> None:
        with self._lock:
            if spec.name in self._specs and not replace:
                if self._specs[spec.name] == spec:
                    return  # idempotent re-registration
                raise ValueError(
                    f"Protocol {spec.name!r} already registered "
                    "(use replace=True to override)"
                )
            self._specs[spec.name] = spec

    def unregister(self, name: str) -> None:
        with self._lock:
            self._specs.pop(name, None)

    # -- queries -----------------------------------------------------------

    def get(self, name: str) -> Optional[ProtocolSpec]:
        return self._specs.get(name)

    def names(self) -> FrozenSet[str]:
        return frozenset(self._specs.keys())

    def is_registered(self, name: str) -> bool:
        return name in self._specs

    def all_event_types(self) -> FrozenSet[str]:
        out: Set[str] = set()
        for s in self._specs.values():
            out.update(s.event_types)
        return frozenset(out)

    def specs(self) -> Iterable[ProtocolSpec]:
        return tuple(self._specs.values())


# Global singleton ----------------------------------------------------------
_REGISTRY = _ProtocolRegistry()


def register_protocol(spec: ProtocolSpec, *, replace: bool = False) -> None:
    """Register a protocol with the global registry."""
    _REGISTRY.register(spec, replace=replace)


def unregister_protocol(name: str) -> None:
    """Remove a protocol from the registry (mainly for tests)."""
    _REGISTRY.unregister(name)


def get_protocol(name: str) -> Optional[ProtocolSpec]:
    return _REGISTRY.get(name)


def supported_protocols() -> FrozenSet[str]:
    return _REGISTRY.names()


def is_protocol_registered(name: str) -> bool:
    return _REGISTRY.is_registered(name)


def all_event_types() -> FrozenSet[str]:
    return _REGISTRY.all_event_types()


def all_specs() -> Iterable[ProtocolSpec]:
    return _REGISTRY.specs()


# ---------------------------------------------------------------------------
# Built-in registrations
# ---------------------------------------------------------------------------
# We register the 3 historical protocols (MCP, A2A, AP2) here, then phase 3
# adds ACP, AGNTCY, ANP, AG-UI, OpenAI Agents and others.

_MCP_EVENT_TYPES: FrozenSet[str] = frozenset({
    "mcp.server.initialized",
    "mcp.server.shutdown",
    "mcp.tool.called",
    "mcp.tool.completed",
    "mcp.tool.error",
    "mcp.tool.list_changed",
    "mcp.resource.read",
    "mcp.resource.updated",
    "mcp.resource.list_changed",
    "mcp.prompt.get",
    "mcp.prompt.list_changed",
    "mcp.sampling.requested",
    "mcp.sampling.completed",
    "mcp.roots.list_changed",
    "mcp.error.found",
    # extended (Phase 3)
    "mcp.notification.sent",
    "mcp.subscription.created",
    "mcp.subscription.cancelled",
    "mcp.elicitation.requested",
    "mcp.elicitation.responded",
    "mcp.completion.requested",
    "mcp.completion.completed",
})

_A2A_EVENT_TYPES: FrozenSet[str] = frozenset({
    "a2a.task.assigned",
    "a2a.task.accepted",
    "a2a.task.rejected",
    "a2a.task.completed",
    "a2a.task.failed",
    "a2a.task.delegated",
    "a2a.message.sent",
    "a2a.message.received",
    "a2a.agent.registered",
    "a2a.agent.deregistered",
    "a2a.error.occurred",
    # extended (Phase 3)
    "a2a.artifact.uploaded",
    "a2a.artifact.downloaded",
    "a2a.agentcard.discovered",
    "a2a.push.subscribed",
    "a2a.push.delivered",
})

_AP2_EVENT_TYPES: FrozenSet[str] = frozenset({
    "ap2.mandate.created",
    "ap2.mandate.revoked",
    "ap2.approval.requested",
    "ap2.approval.granted",
    "ap2.payment.initiated",
    "ap2.payment.completed",
    "ap2.payment.failed",
    "ap2.error.occurred",
    # extended (Phase 3)
    "ap2.cost.incurred",
    "ap2.refund.initiated",
    "ap2.refund.completed",
    "ap2.dispute.opened",
    "ap2.dispute.resolved",
    "ap2.intent.resolved",
})

register_protocol(ProtocolSpec(
    name="mcp",
    version="1.0",
    event_types=_MCP_EVENT_TYPES,
    description="Model Context Protocol — tool/resource/prompt/sampling events",
))

register_protocol(ProtocolSpec(
    name="a2a",
    version="1.0",
    event_types=_A2A_EVENT_TYPES,
    description="Agent-to-Agent — task delegation, messaging, agent cards",
))

register_protocol(ProtocolSpec(
    name="ap2",
    version="1.0",
    event_types=_AP2_EVENT_TYPES,
    description="Agent Payments Protocol — mandates, payments, costs",
))


__all__ = [
    "ProtocolSpec",
    "register_protocol",
    "unregister_protocol",
    "get_protocol",
    "supported_protocols",
    "is_protocol_registered",
    "all_event_types",
    "all_specs",
]
