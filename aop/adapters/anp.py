"""ANP (Agent Network Protocol) adapter.

DID-based decentralized agent communication protocol. Models handshakes,
signed messages, signature verification, and routing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseAdapter, EventHandle


class ANPAdapter(BaseAdapter):
    PROTOCOL = "anp"

    # Handshake ---------------------------------------------------------
    def log_handshake_started(
        self, agent_id: str, peer_did: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="anp.handshake.started",
            data={"peer_did": peer_did}, correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_handshake_completed(
        self, agent_id: str, peer_did: str,
        session_id: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="anp.handshake.completed",
            data={"peer_did": peer_did, "session_id": session_id},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_handshake_failed(
        self, agent_id: str, peer_did: str,
        error_code: str, error_message: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="anp.handshake.failed",
            data={"peer_did": peer_did}, severity="error",
            error={"code": error_code, "message": error_message},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Message / signing -------------------------------------------------
    def log_message_signed(
        self, agent_id: str, peer_did: str,
        message_id: str, signature_alg: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="anp.message.signed",
            data={"peer_did": peer_did, "message_id": message_id,
                  "signature_alg": signature_alg},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_message_verified(
        self, agent_id: str, peer_did: str,
        message_id: str, valid: bool,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="anp.message.verified" if valid else "anp.message.rejected",
            data={"peer_did": peer_did, "message_id": message_id, "valid": valid},
            severity=None if valid else "warn",
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Routing -----------------------------------------------------------
    def log_route_resolved(
        self, agent_id: str, peer_did: str, hops: list,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="anp.route.resolved",
            data={"peer_did": peer_did, "hops": hops, "hop_count": len(hops)},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)
