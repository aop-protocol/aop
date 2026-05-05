"""OpenAI Agents SDK / Responses-API adapter.

Models OpenAI Agents events: agent runs, handoffs, tool invocations, and
output messages. Mirrors the v1 Responses API event structure.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseAdapter, EventHandle


class OpenAIAgentsAdapter(BaseAdapter):
    PROTOCOL = "openai_agents"

    # Run lifecycle -----------------------------------------------------
    def log_run_started(
        self, agent_id: str, run_id: str, input_preview: str,
        model: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="openai_agents.run.started",
            data={"run_id": run_id, "input_preview": input_preview, "model": model},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_run_completed(
        self, agent_id: str, run_id: str, output_preview: str,
        duration_ms: Optional[int] = None,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="openai_agents.run.completed",
            data={"run_id": run_id, "output_preview": output_preview},
            duration_ms=duration_ms, parent_id=parent_id, correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_run_failed(
        self, agent_id: str, run_id: str,
        error_code: str, error_message: str,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="openai_agents.run.failed",
            data={"run_id": run_id}, severity="error",
            error={"code": error_code, "message": error_message},
            parent_id=parent_id, correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Handoff -----------------------------------------------------------
    def log_handoff(
        self, agent_id: str, from_agent: str, to_agent: str,
        run_id: str, reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="openai_agents.handoff",
            data={"from_agent": from_agent, "to_agent": to_agent,
                  "run_id": run_id, "reason": reason},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Tool calls --------------------------------------------------------
    def log_tool_invoked(
        self, agent_id: str, run_id: str, tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="openai_agents.tool.invoked",
            data={"run_id": run_id, "tool_name": tool_name, "args": args},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_tool_result(
        self, agent_id: str, run_id: str, tool_name: str,
        result: Any, duration_ms: Optional[int] = None,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="openai_agents.tool.result",
            data={"run_id": run_id, "tool_name": tool_name, "result": result},
            duration_ms=duration_ms, parent_id=parent_id, correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # Output messages ---------------------------------------------------
    def log_output_message(
        self, agent_id: str, run_id: str, role: str, content_preview: str,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="openai_agents.message.output",
            data={"run_id": run_id, "role": role, "content_preview": content_preview},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)
