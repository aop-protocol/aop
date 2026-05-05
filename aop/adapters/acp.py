"""ACP (Agent Communication Protocol — IBM) adapter.

Models discovery, REST-style invocation (sync + streaming), and
agent-card retrieval. Event types are registered in aop.registry.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseAdapter, EventHandle


class ACPAdapter(BaseAdapter):
    """Adapter for IBM Agent Communication Protocol events."""

    PROTOCOL = "acp"

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def log_agent_discovered(
        self,
        agent_id: str,
        discovered_agent: str,
        endpoint: str,
        capabilities: Optional[list] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="acp.agent.discovered",
            data={
                "discovered_agent": discovered_agent,
                "endpoint": endpoint,
                "capabilities": capabilities or [],
            },
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # ------------------------------------------------------------------
    # Invocation
    # ------------------------------------------------------------------
    def log_invocation_started(
        self,
        agent_id: str,
        target_agent: str,
        operation: str,
        request: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="acp.invocation.started",
            data={"target_agent": target_agent, "operation": operation, "request": request},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_invocation_completed(
        self,
        agent_id: str,
        target_agent: str,
        operation: str,
        response: Any,
        duration_ms: int,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="acp.invocation.completed",
            data={"target_agent": target_agent, "operation": operation, "response": response},
            duration_ms=duration_ms,
            parent_id=parent_id,
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_invocation_failed(
        self,
        agent_id: str,
        target_agent: str,
        operation: str,
        error_code: str,
        error_message: str,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="acp.invocation.failed",
            data={"target_agent": target_agent, "operation": operation},
            severity="error",
            error={"code": error_code, "message": error_message},
            parent_id=parent_id,
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------
    def log_stream_chunk(
        self,
        agent_id: str,
        target_agent: str,
        operation: str,
        chunk_index: int,
        chunk_size_bytes: int,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="acp.stream.chunk",
            data={
                "target_agent": target_agent,
                "operation": operation,
                "chunk_index": chunk_index,
                "chunk_size_bytes": chunk_size_bytes,
            },
            parent_id=parent_id,
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_stream_completed(
        self,
        agent_id: str,
        target_agent: str,
        operation: str,
        total_chunks: int,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id,
            event_type="acp.stream.completed",
            data={"target_agent": target_agent, "operation": operation, "total_chunks": total_chunks},
            parent_id=parent_id,
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)
