"""AG-UI (Agent-User-Interface) adapter.

Streaming UI deltas, tool-approval prompts, human-in-the-loop events
between an agent and the human-facing UI.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseAdapter, EventHandle


class AGUIAdapter(BaseAdapter):
    PROTOCOL = "ag_ui"

    # Stream deltas -----------------------------------------------------
    def log_text_delta(
        self, agent_id: str, session_id: str, delta: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="ag_ui.stream.text_delta",
            data={"session_id": session_id,
                  "delta_chars": len(delta),
                  "preview": delta[:120]},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_tool_call_delta(
        self, agent_id: str, session_id: str, tool_name: str, args_partial: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="ag_ui.stream.tool_call_delta",
            data={"session_id": session_id, "tool_name": tool_name, "args_partial": args_partial},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Human in the loop -------------------------------------------------
    def log_approval_requested(
        self, agent_id: str, session_id: str, approval_id: str, prompt: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="ag_ui.approval.requested",
            data={"session_id": session_id, "approval_id": approval_id, "prompt": prompt},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_approval_resolved(
        self, agent_id: str, session_id: str, approval_id: str, granted: bool,
        comment: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="ag_ui.approval.granted" if granted else "ag_ui.approval.denied",
            data={"session_id": session_id, "approval_id": approval_id, "comment": comment},
            severity=None if granted else "warn",
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Sessions ----------------------------------------------------------
    def log_session_started(
        self, agent_id: str, session_id: str, user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="ag_ui.session.started",
            data={"session_id": session_id, "user_id": user_id},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_session_ended(
        self, agent_id: str, session_id: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="ag_ui.session.ended",
            data={"session_id": session_id},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)
