"""CrewAI instrumentation."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .._common import already_patched, emit_event, ensure_context, mark_patched, now_ns, ns_to_ms

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "crewai-agent"
_originals: dict = {}


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    try:
        from crewai import Crew, Task  # type: ignore
    except Exception:
        return
    if hasattr(Crew, "kickoff") and not already_patched(Crew.kickoff):
        _originals["kickoff"] = Crew.kickoff

        def kickoff(self: Any, *args: Any, **kwargs: Any) -> Any:
            ensure_context()
            emit_event(client, agent_id=agent_id, event_type="framework.crewai.crew.kickoff.start",
                       data={"agent_count": len(getattr(self, "agents", []))})
            start = now_ns()
            try:
                res = _originals["kickoff"](self, *args, **kwargs)
            except Exception as e:
                emit_event(client, agent_id=agent_id, event_type="framework.crewai.crew.kickoff.error",
                           duration_ms=ns_to_ms(start, now_ns()),
                           error={"code": type(e).__name__, "message": str(e)}, severity="error")
                raise
            emit_event(client, agent_id=agent_id, event_type="framework.crewai.crew.kickoff.end",
                       duration_ms=ns_to_ms(start, now_ns()))
            return res
        mark_patched(kickoff)
        Crew.kickoff = kickoff  # type: ignore[assignment]

    if hasattr(Task, "execute") and not already_patched(Task.execute):
        _originals["task_execute"] = Task.execute

        def task_execute(self: Any, *args: Any, **kwargs: Any) -> Any:
            ensure_context()
            emit_event(client, agent_id=agent_id, event_type="framework.crewai.task.start",
                       data={"description_preview": str(getattr(self, "description", ""))[:200]})
            start = now_ns()
            try:
                res = _originals["task_execute"](self, *args, **kwargs)
            except Exception as e:
                emit_event(client, agent_id=agent_id, event_type="framework.crewai.task.error",
                           duration_ms=ns_to_ms(start, now_ns()),
                           error={"code": type(e).__name__, "message": str(e)}, severity="error")
                raise
            emit_event(client, agent_id=agent_id, event_type="framework.crewai.task.end",
                       duration_ms=ns_to_ms(start, now_ns()))
            return res
        mark_patched(task_execute)
        Task.execute = task_execute  # type: ignore[assignment]


def uninstall() -> None:
    try:
        from crewai import Crew, Task  # type: ignore
        if "kickoff" in _originals:
            Crew.kickoff = _originals.pop("kickoff")
        if "task_execute" in _originals:
            Task.execute = _originals.pop("task_execute")
    except Exception:
        pass
    _originals.clear()
