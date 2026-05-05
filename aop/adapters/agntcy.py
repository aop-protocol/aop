"""AGNTCY (Internet of Agents — Cisco/AGNTCY) adapter.

Models directory operations, DID-based agent identity, and connection
lifecycle for inter-organization agent networks.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseAdapter, EventHandle


class AGNTCYAdapter(BaseAdapter):
    PROTOCOL = "agntcy"

    # Identity ----------------------------------------------------------
    def log_identity_resolved(
        self, agent_id: str, did: str, did_method: str,
        public_key_fingerprint: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="agntcy.identity.resolved",
            data={"did": did, "did_method": did_method,
                  "public_key_fingerprint": public_key_fingerprint},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Directory ---------------------------------------------------------
    def log_directory_lookup(
        self, agent_id: str, query: str, result_count: int,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="agntcy.directory.lookup",
            data={"query": query, "result_count": result_count},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_directory_published(
        self, agent_id: str, agent_card: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="agntcy.directory.published",
            data={"agent_card": agent_card},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Connection lifecycle ----------------------------------------------
    def log_connection_opened(
        self, agent_id: str, peer_did: str, transport: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="agntcy.connection.opened",
            data={"peer_did": peer_did, "transport": transport},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_connection_closed(
        self, agent_id: str, peer_did: str, reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="agntcy.connection.closed",
            data={"peer_did": peer_did, "reason": reason},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Auth / capability -------------------------------------------------
    def log_capability_granted(
        self, agent_id: str, peer_did: str, capability: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="agntcy.capability.granted",
            data={"peer_did": peer_did, "capability": capability},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_capability_revoked(
        self, agent_id: str, peer_did: str, capability: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="agntcy.capability.revoked",
            data={"peer_did": peer_did, "capability": capability},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)
