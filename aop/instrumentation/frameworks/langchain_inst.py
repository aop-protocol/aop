"""LangChain instrumentation via the BaseCallbackHandler interface.

We register a process-wide AOP callback handler and a
``langchain_core.tracers.context.register_configure_hook`` so every
chain/llm/tool/agent invocation produces AOP events automatically.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from .._common import emit_event, ensure_context

if TYPE_CHECKING:
    from ...client import AOPClient

_AGENT = "langchain-agent"
_handler_token: Any = None


class _AOPCallbackHandler:
    """Implements the LangChain BaseCallbackHandler interface lazily."""

    def __init__(self, client: Any, agent_id: str) -> None:
        self._client = client
        self._agent_id = agent_id

    # LLM ------------------------------------------------------------
    def on_llm_start(self, serialized: Dict[str, Any], prompts: list, **kwargs: Any) -> None:
        ensure_context()
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.llm.start",
                   data={"name": (serialized or {}).get("name"),
                         "prompt_count": len(prompts or [])})

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.llm.end")

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.llm.error",
                   error={"code": type(error).__name__, "message": str(error)},
                   severity="error")

    # Chain ----------------------------------------------------------
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.chain.start",
                   data={"name": (serialized or {}).get("name"),
                         "input_keys": list((inputs or {}).keys())})

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.chain.end",
                   data={"output_keys": list((outputs or {}).keys())})

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.chain.error",
                   error={"code": type(error).__name__, "message": str(error)},
                   severity="error")

    # Tool -----------------------------------------------------------
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.tool.start",
                   data={"name": (serialized or {}).get("name"),
                         "input_preview": (input_str or "")[:200]})

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.tool.end",
                   data={"output_preview": (output or "")[:200]})

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.tool.error",
                   error={"code": type(error).__name__, "message": str(error)},
                   severity="error")

    # Agent ----------------------------------------------------------
    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.agent.action",
                   data={"tool": getattr(action, "tool", None)})

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        emit_event(self._client, agent_id=self._agent_id,
                   event_type="framework.langchain.agent.finish")


def install(client: Optional["AOPClient"] = None, *, agent_id: str = _AGENT) -> None:
    global _handler_token
    try:
        from langchain_core.tracers.context import register_configure_hook  # type: ignore
        from langchain_core.callbacks.base import BaseCallbackHandler  # type: ignore
    except Exception:
        return

    # Make our handler subclass BaseCallbackHandler dynamically (so it works
    # without a hard dep at import time of this module).
    class AOPCallbackHandler(BaseCallbackHandler, _AOPCallbackHandler):  # type: ignore[misc]
        def __init__(self) -> None:
            BaseCallbackHandler.__init__(self)
            _AOPCallbackHandler.__init__(self, client, agent_id)

    handler = AOPCallbackHandler()

    # context-var hook so the handler is automatically attached to every run
    try:
        from contextvars import ContextVar
        _ctx_var: ContextVar = ContextVar("aop_lc_handler", default=handler)
        register_configure_hook(_ctx_var, True)
        _handler_token = _ctx_var
    except Exception:
        _handler_token = handler


def uninstall() -> None:
    # LangChain doesn't expose an "unregister" for configure hooks. Best we
    # can do is null the handler reference.
    global _handler_token
    _handler_token = None
