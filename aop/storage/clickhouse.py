"""ClickHouse storage backend.

Designed for high-volume event streams (>10K events/s/node). Uses the
official ``clickhouse-connect`` driver and writes JSON columns for
nested objects.

Connection string format:
    clickhouse://user:password@host:8123/database
    clickhouse+secure://user:password@host:8443/database

We deliberately keep it lightweight: ClickHouse is the only sane choice
for time-series analytics at scale, but we don't force it as a hard dep.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .base import BaseStorage
from ..exceptions import AOPStorageError

_log = logging.getLogger("aop.storage.clickhouse")


class ClickHouseStorage(BaseStorage):
    """ClickHouse-backed storage."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        *,
        host: Optional[str] = None,
        port: int = 8123,
        username: str = "default",
        password: str = "",
        database: str = "aop",
        secure: bool = False,
        table: str = "aop_events",
    ) -> None:
        try:
            import clickhouse_connect  # type: ignore
        except ImportError as e:
            raise ImportError(
                "ClickHouse storage requires clickhouse-connect. "
                "Install with: pip install clickhouse-connect"
            ) from e

        if connection_string:
            parsed = urlparse(connection_string)
            host = parsed.hostname
            port = parsed.port or (8443 if parsed.scheme.endswith("+secure") else 8123)
            username = parsed.username or username
            password = parsed.password or password
            database = (parsed.path or "/aop").lstrip("/")
            secure = parsed.scheme.endswith("+secure")

        self._client = clickhouse_connect.get_client(
            host=host, port=port, username=username, password=password,
            database=database, secure=secure,
        )
        self.table = table
        self._ensure_table()

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {self.table} (
            id String,
            version LowCardinality(String),
            timestamp DateTime64(3, 'UTC'),
            agent_id String,
            instance_id String,
            protocol LowCardinality(String),
            event_type LowCardinality(String),
            correlation_id String DEFAULT '',
            parent_id String DEFAULT '',
            severity LowCardinality(String) DEFAULT '',
            duration_ms Int64 DEFAULT 0,
            data String DEFAULT '',
            metadata String DEFAULT '',
            error String DEFAULT '',
            trace_id String DEFAULT '',
            span_id String DEFAULT '',
            parent_span_id String DEFAULT '',
            resource String DEFAULT '',
            attributes String DEFAULT '',
            tokens String DEFAULT '',
            cost String DEFAULT '',
            tenant_id LowCardinality(String) DEFAULT '',
            retention_until Nullable(DateTime64(3, 'UTC')),
            created_at DateTime64(3, 'UTC') DEFAULT now64(3)
        ) ENGINE = MergeTree
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (agent_id, timestamp, id)
        SETTINGS index_granularity = 8192
        """
        self._client.command(ddl)

    # ------------------------------------------------------------------
    # BaseStorage interface
    # ------------------------------------------------------------------
    def log_event(self, event: Dict[str, Any]) -> None:
        try:
            row = self._row_from_event(event)
            self._client.insert(self.table, [row], column_names=list(row.keys()))
        except Exception as e:
            raise AOPStorageError(f"clickhouse insert failed: {e}", operation="log_event")

    def query_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        protocol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        clauses = ["1=1"]
        params: Dict[str, Any] = {}
        if agent_id:
            clauses.append("agent_id = %(agent_id)s"); params["agent_id"] = agent_id
        if event_type:
            clauses.append("event_type = %(event_type)s"); params["event_type"] = event_type
        if protocol:
            clauses.append("protocol = %(protocol)s"); params["protocol"] = protocol
        if start_time:
            clauses.append("timestamp >= %(start)s"); params["start"] = start_time
        if end_time:
            clauses.append("timestamp <= %(end)s"); params["end"] = end_time
        if correlation_id:
            clauses.append("correlation_id = %(corr)s"); params["corr"] = correlation_id

        sql = (
            f"SELECT * FROM {self.table} WHERE " + " AND ".join(clauses)
            + f" ORDER BY timestamp DESC LIMIT {int(limit)}"
        )
        rows = self._client.query(sql, parameters=params)
        return [self._event_from_row(dict(zip(rows.column_names, r))) for r in rows.result_rows]

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        rows = self._client.query(
            f"SELECT * FROM {self.table} WHERE id = %(id)s LIMIT 1",
            parameters={"id": event_id},
        )
        if not rows.result_rows:
            return None
        return self._event_from_row(dict(zip(rows.column_names, rows.result_rows[0])))

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    @staticmethod
    def _row_from_event(ev: Dict[str, Any]) -> Dict[str, Any]:
        def _j(v: Any) -> str:
            if v is None:
                return ""
            if isinstance(v, str):
                return v
            return json.dumps(v, default=str)

        ts = ev.get("timestamp")
        ts_dt: Any = ts
        if isinstance(ts, str):
            try:
                ts_dt = datetime.fromisoformat(ts.rstrip("Z"))
            except Exception:
                ts_dt = datetime.utcnow()

        return {
            "id": ev.get("id", ""),
            "version": ev.get("version", "1.1"),
            "timestamp": ts_dt,
            "agent_id": ev.get("agent_id", ""),
            "instance_id": ev.get("instance_id", ""),
            "protocol": ev.get("protocol", ""),
            "event_type": ev.get("event_type", ""),
            "correlation_id": ev.get("correlation_id") or "",
            "parent_id": ev.get("parent_id") or "",
            "severity": ev.get("severity") or "",
            "duration_ms": int(ev.get("duration_ms") or 0),
            "data": _j(ev.get("data")),
            "metadata": _j(ev.get("metadata")),
            "error": _j(ev.get("error")),
            "trace_id": ev.get("trace_id") or "",
            "span_id": ev.get("span_id") or "",
            "parent_span_id": ev.get("parent_span_id") or "",
            "resource": _j(ev.get("resource")),
            "attributes": _j(ev.get("attributes")),
            "tokens": _j(ev.get("tokens")),
            "cost": _j(ev.get("cost")),
            "tenant_id": ev.get("tenant_id") or "",
            "retention_until": ev.get("retention_until"),
        }

    @staticmethod
    def _event_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
        def _u(v: Any) -> Any:
            if isinstance(v, str) and v and v[0] in "{[":
                try:
                    return json.loads(v)
                except Exception:
                    return v
            return v

        out = dict(row)
        for k in ("data", "metadata", "error", "resource", "attributes", "tokens", "cost"):
            out[k] = _u(out.get(k))
        ts = out.get("timestamp")
        if isinstance(ts, datetime):
            out["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return out
