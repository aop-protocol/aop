"""Retention / TTL runner.

Purges events whose ``retention_until`` column has elapsed, or events older
than a global cutoff. Supports SQLite, PostgreSQL, and ClickHouse.

Usage:
    from aop.storage.retention import apply_retention
    apply_retention("sqlite:///aop_events.db", max_age_days=30)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

_log = logging.getLogger("aop.storage.retention")


def apply_retention(
    storage_url: str,
    *,
    max_age_days: Optional[int] = None,
    tenant_id: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """Delete events past their retention window. Returns rows deleted."""
    if storage_url.startswith("sqlite"):
        return _retention_sqlite(storage_url, max_age_days, tenant_id, dry_run)
    if storage_url.startswith("postgres"):
        return _retention_postgres(storage_url, max_age_days, tenant_id, dry_run)
    if storage_url.startswith("clickhouse"):
        return _retention_clickhouse(storage_url, max_age_days, tenant_id, dry_run)
    raise ValueError(f"unsupported storage URL: {storage_url!r}")


# ---------------------------------------------------------------------------
def _cutoff(max_age_days: Optional[int]) -> Optional[datetime]:
    if max_age_days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=max_age_days)


def _retention_sqlite(url: str, max_age: Optional[int], tenant: Optional[str], dry: bool) -> int:
    import sqlite3
    path = url.split("://", 1)[1].lstrip("/") or "aop_events.db"
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    where, params = _where_clause(max_age, tenant, dialect="sqlite")
    if dry:
        cur.execute(f"SELECT COUNT(*) FROM aop_events WHERE {where}", params)
        n = cur.fetchone()[0]
    else:
        cur.execute(f"DELETE FROM aop_events WHERE {where}", params)
        n = cur.rowcount
        conn.commit()
    conn.close()
    return int(n or 0)


def _retention_postgres(url: str, max_age: Optional[int], tenant: Optional[str], dry: bool) -> int:
    import psycopg2  # type: ignore
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    where, params = _where_clause(max_age, tenant, dialect="postgresql")
    if dry:
        cur.execute(f"SELECT COUNT(*) FROM aop_events WHERE {where}", params)
        n = cur.fetchone()[0]
    else:
        cur.execute(f"DELETE FROM aop_events WHERE {where}", params)
        n = cur.rowcount
        conn.commit()
    conn.close()
    return int(n or 0)


def _retention_clickhouse(url: str, max_age: Optional[int], tenant: Optional[str], dry: bool) -> int:
    from .clickhouse import ClickHouseStorage
    ch = ClickHouseStorage(url)
    cutoff = _cutoff(max_age)
    parts = []
    params: dict = {}
    if cutoff is not None:
        parts.append("timestamp < %(cutoff)s")
        params["cutoff"] = cutoff
    parts.append("(retention_until IS NOT NULL AND retention_until < now64(3))")
    if tenant:
        parts.append("tenant_id = %(tenant)s")
        params["tenant"] = tenant
    where = " OR ".join(parts) if cutoff is None else " OR ".join(parts[:1] + [f"({parts[1]})"])
    if dry:
        rows = ch._client.query(f"SELECT COUNT(*) FROM aop_events WHERE {where}", parameters=params)
        return int(rows.result_rows[0][0])
    ch._client.command(f"ALTER TABLE aop_events DELETE WHERE {where}", parameters=params)
    ch.close()
    return -1  # ClickHouse mutations are async; row count not directly available


def _where_clause(max_age: Optional[int], tenant: Optional[str], *, dialect: str):
    cutoff = _cutoff(max_age)
    parts: list = []
    params: list = []
    placeholder = "%s" if dialect == "postgresql" else "?"

    if cutoff is not None:
        parts.append(f"timestamp < {placeholder}")
        params.append(cutoff.isoformat() if dialect == "sqlite" else cutoff)

    parts.append(f"(retention_until IS NOT NULL AND retention_until < {placeholder})")
    params.append(datetime.now(timezone.utc).isoformat() if dialect == "sqlite"
                  else datetime.now(timezone.utc))

    where = "(" + " OR ".join(parts) + ")"
    if tenant:
        where = f"{where} AND tenant_id = {placeholder}"
        params.append(tenant)
    return where, tuple(params)
