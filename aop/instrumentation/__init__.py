"""
AOP Auto-Instrumentation (Phase 2)

A single ``aop.autoinstrument()`` call patches popular libraries so AOP
captures HTTP traffic, LLM API calls, agent-framework callbacks, vector DB
queries, and database/cache operations automatically — without changing
user code.

Each integration is implemented in its own module under this package and
exposes ``install(client=None, **opts)`` / ``uninstall()`` functions. The
top-level dispatcher detects which optional dependencies are installed via
``importlib.util.find_spec`` and patches only those.

Usage:
    >>> import aop
    >>> aop.autoinstrument()                       # patch everything detected
    >>> aop.autoinstrument(targets=['openai', 'requests'])
    >>> aop.uninstrument()                         # remove all patches
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import AOPClient

_log = logging.getLogger("aop.instrumentation")


# Mapping: integration name -> (importable submodule path, dependency module)
_INTEGRATIONS: Dict[str, Dict[str, Any]] = {
    # HTTP clients
    "requests": {"module": ".http.requests_inst", "dep": "requests"},
    "httpx": {"module": ".http.httpx_inst", "dep": "httpx"},
    "aiohttp": {"module": ".http.aiohttp_inst", "dep": "aiohttp"},
    "urllib": {"module": ".http.urllib_inst", "dep": "urllib"},
    "urllib3": {"module": ".http.urllib3_inst", "dep": "urllib3"},

    # LLM SDKs
    "openai": {"module": ".llm.openai_inst", "dep": "openai"},
    "anthropic": {"module": ".llm.anthropic_inst", "dep": "anthropic"},
    "google_genai": {"module": ".llm.google_genai_inst", "dep": "google.genai"},
    "mistralai": {"module": ".llm.mistralai_inst", "dep": "mistralai"},
    "cohere": {"module": ".llm.cohere_inst", "dep": "cohere"},
    "bedrock": {"module": ".llm.bedrock_inst", "dep": "boto3"},
    "groq": {"module": ".llm.groq_inst", "dep": "groq"},
    "litellm": {"module": ".llm.litellm_inst", "dep": "litellm"},
    "ollama": {"module": ".llm.ollama_inst", "dep": "ollama"},

    # Vector DBs
    "pinecone": {"module": ".vectordb.pinecone_inst", "dep": "pinecone"},
    "weaviate": {"module": ".vectordb.weaviate_inst", "dep": "weaviate"},
    "qdrant": {"module": ".vectordb.qdrant_inst", "dep": "qdrant_client"},
    "chromadb": {"module": ".vectordb.chromadb_inst", "dep": "chromadb"},

    # Frameworks
    "langchain": {"module": ".frameworks.langchain_inst", "dep": "langchain_core"},
    "langgraph": {"module": ".frameworks.langgraph_inst", "dep": "langgraph"},
    "crewai": {"module": ".frameworks.crewai_inst", "dep": "crewai"},
    "autogen": {"module": ".frameworks.autogen_inst", "dep": "autogen"},
    "llamaindex": {"module": ".frameworks.llamaindex_inst", "dep": "llama_index"},
    "semantic_kernel": {"module": ".frameworks.semantic_kernel_inst", "dep": "semantic_kernel"},

    # DB / cache
    "sqlalchemy": {"module": ".db.sqlalchemy_inst", "dep": "sqlalchemy"},
    "redis": {"module": ".db.redis_inst", "dep": "redis"},
    "psycopg": {"module": ".db.psycopg_inst", "dep": "psycopg"},

    # Low-level
    "socket": {"module": ".socket_inst", "dep": "socket"},
}


_lock = RLock()
_installed: Dict[str, Any] = {}  # integration -> module reference
_default_client: Optional["AOPClient"] = None


def _is_available(spec: str) -> bool:
    if not spec:
        return False
    try:
        return importlib.util.find_spec(spec) is not None
    except (ImportError, ValueError):
        return False


def _resolve(name: str, client: Optional["AOPClient"]):
    cfg = _INTEGRATIONS.get(name)
    if cfg is None:
        raise ValueError(f"Unknown instrumentation target: {name!r}")
    if not _is_available(cfg["dep"]):
        _log.debug("instrumentation %s skipped: %s not installed", name, cfg["dep"])
        return None
    try:
        mod = importlib.import_module(cfg["module"], package=__name__)
    except Exception as e:
        _log.warning("Failed to import instrumentation %s: %s", name, e)
        return None
    return mod


def autoinstrument(
    *,
    client: Optional["AOPClient"] = None,
    targets: Optional[Iterable[str]] = None,
    all: bool = True,
    silent: bool = False,
) -> List[str]:
    """Install AOP patches into the named (or all detected) libraries.

    Args:
        client: Optional AOPClient to bind events to. If None, integrations
            buffer events into the global default until ``set_default_client``.
        targets: Iterable of integration names. If None and ``all=True``,
            every integration whose dependency is installed is patched.
        all: If True (default), enable everything detected when ``targets``
            is None.
        silent: If True, suppress per-integration log lines.

    Returns:
        List of integration names that were successfully installed.
    """
    global _default_client
    with _lock:
        if client is not None:
            _default_client = client

        if targets is None:
            targets = list(_INTEGRATIONS.keys()) if all else []

        installed: List[str] = []
        for name in targets:
            if name in _installed:
                installed.append(name)
                continue
            mod = _resolve(name, client)
            if mod is None:
                continue
            try:
                mod.install(client=client or _default_client)  # type: ignore[attr-defined]
            except Exception as e:
                _log.warning("Failed to install %s: %s", name, e)
                continue
            _installed[name] = mod
            installed.append(name)
            if not silent:
                _log.info("aop: instrumented %s", name)
        return installed


def uninstrument(targets: Optional[Iterable[str]] = None) -> List[str]:
    """Remove patches for the named integrations (or all)."""
    with _lock:
        if targets is None:
            targets = list(_installed.keys())
        removed: List[str] = []
        for name in list(targets):
            mod = _installed.pop(name, None)
            if mod is None:
                continue
            try:
                if hasattr(mod, "uninstall"):
                    mod.uninstall()
            except Exception as e:
                _log.warning("Failed to uninstall %s: %s", name, e)
            removed.append(name)
        return removed


def list_instrumentations() -> Dict[str, bool]:
    """Return a mapping of integration name -> available/installed flags."""
    out = {}
    for name, cfg in _INTEGRATIONS.items():
        out[name] = {
            "available": _is_available(cfg["dep"]),
            "installed": name in _installed,
        }
    return out


def set_default_client(client: "AOPClient") -> None:
    """Bind a default client used by integrations that didn't receive one."""
    global _default_client
    _default_client = client


def get_default_client() -> Optional["AOPClient"]:
    return _default_client


__all__ = [
    "autoinstrument",
    "uninstrument",
    "list_instrumentations",
    "set_default_client",
    "get_default_client",
]
