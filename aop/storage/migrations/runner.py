"""Schema migration runner.

We avoid Alembic to keep the dependency footprint minimal. Migrations are
discovered in ``aop/storage/migrations/versions/*.py`` files. Each must
export:

    version = "0001"            # zero-padded, lexically sortable
    description = "..."
    def up(executor): ...        # executes DDL using the executor's API
    def down(executor): ...      # optional, for rollback

The ``executor`` is a small adapter exposing:
    .execute(sql, params=None)  -> rows
    .dialect                     -> "sqlite" | "postgresql"
"""

from __future__ import annotations

import importlib
import logging
import os
import pkgutil
from typing import Any, Callable, List, Optional, Tuple

_log = logging.getLogger("aop.storage.migrations")


# ---------------------------------------------------------------------------
# Executors
# ---------------------------------------------------------------------------

class _SQLiteExecutor:
    dialect = "sqlite"
    def __init__(self, conn: Any) -> None:
        self._conn = conn
    def execute(self, sql: str, params: Optional[tuple] = None) -> List[Any]:
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        try:
            rows = cur.fetchall()
        except Exception:
            rows = []
        self._conn.commit()
        return rows


class _PostgresExecutor:
    dialect = "postgresql"
    def __init__(self, conn: Any) -> None:
        self._conn = conn
    def execute(self, sql: str, params: Optional[tuple] = None) -> List[Any]:
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        rows: List[Any] = []
        try:
            rows = cur.fetchall()
        except Exception:
            pass
        self._conn.commit()
        return rows


def _build_executor(url: str) -> Tuple[Any, Callable[[], None]]:
    """Open a connection appropriate for the URL; return (executor, close)."""
    if url.startswith("sqlite"):
        import sqlite3
        path = url.split("://", 1)[1] if "://" in url else url
        path = path.lstrip("/")  # sqlite:///foo.db -> foo.db
        if not path:
            path = "aop_events.db"
        conn = sqlite3.connect(path)
        return _SQLiteExecutor(conn), conn.close
    if url.startswith("postgres"):
        try:
            import psycopg2  # type: ignore
        except ImportError as e:
            raise ImportError("psycopg2 required for Postgres migrations") from e
        conn = psycopg2.connect(url)
        return _PostgresExecutor(conn), conn.close
    raise ValueError(f"unsupported migration URL: {url!r}")


# ---------------------------------------------------------------------------
# Migration discovery
# ---------------------------------------------------------------------------

def list_migrations() -> List[Any]:
    from . import versions as versions_pkg
    pkg_path = versions_pkg.__path__  # type: ignore[attr-defined]
    modules = []
    for finder, name, ispkg in pkgutil.iter_modules(pkg_path):
        if name.startswith("_"):
            continue
        mod = importlib.import_module(f"aop.storage.migrations.versions.{name}")
        if hasattr(mod, "version") and hasattr(mod, "up"):
            modules.append(mod)
    modules.sort(key=lambda m: getattr(m, "version", ""))
    return modules


def _ensure_version_table(executor: Any) -> None:
    if executor.dialect == "sqlite":
        executor.execute(
            "CREATE TABLE IF NOT EXISTS aop_schema_version ("
            "version TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
    else:
        executor.execute(
            "CREATE TABLE IF NOT EXISTS aop_schema_version ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT NOW())"
        )


def current_version(url: str) -> Optional[str]:
    executor, close = _build_executor(url)
    try:
        _ensure_version_table(executor)
        rows = executor.execute(
            "SELECT version FROM aop_schema_version ORDER BY version DESC LIMIT 1"
        )
        return rows[0][0] if rows else None
    finally:
        close()


# ---------------------------------------------------------------------------
# Public migrate()
# ---------------------------------------------------------------------------

def migrate(url: str, *, target: Optional[str] = None) -> List[str]:
    """Apply all pending migrations up to ``target`` (or HEAD)."""
    executor, close = _build_executor(url)
    applied: List[str] = []
    try:
        _ensure_version_table(executor)
        rows = executor.execute("SELECT version FROM aop_schema_version")
        already = {r[0] for r in rows}
        for mod in list_migrations():
            v = mod.version
            if v in already:
                continue
            if target is not None and v > target:
                break
            _log.info("applying migration %s — %s", v, getattr(mod, "description", ""))
            mod.up(executor)
            executor.execute(
                "INSERT INTO aop_schema_version (version) VALUES (%s)" if executor.dialect == "postgresql"
                else "INSERT INTO aop_schema_version (version) VALUES (?)",
                (v,),
            )
            applied.append(v)
    finally:
        close()
    return applied
