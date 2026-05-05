"""S3-compatible cold-archive storage backend.

Stores events as line-delimited JSON in object storage (S3, MinIO, R2, GCS
via S3-compat endpoint, Azure via S3-compat front). Optimized for cheap
long-term retention; query path scans matching object prefixes.

Connection string format:
    s3://my-bucket/aop-archive
    s3://my-bucket/aop-archive?endpoint=https://minio.local&region=us-east-1
"""

from __future__ import annotations

import gzip
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from .base import BaseStorage
from ..exceptions import AOPStorageError

_log = logging.getLogger("aop.storage.s3")


class S3ArchiveStorage(BaseStorage):
    def __init__(
        self,
        connection_string: Optional[str] = None,
        *,
        bucket: Optional[str] = None,
        prefix: str = "aop-archive",
        endpoint_url: Optional[str] = None,
        region: Optional[str] = None,
        flush_size: int = 1000,
    ) -> None:
        try:
            import boto3  # type: ignore
        except ImportError as e:
            raise ImportError(
                "S3 storage requires boto3. Install with: pip install boto3"
            ) from e

        if connection_string:
            parsed = urlparse(connection_string)
            bucket = parsed.netloc or bucket
            prefix = (parsed.path or "/").lstrip("/") or prefix
            qs = parse_qs(parsed.query or "")
            endpoint_url = qs.get("endpoint", [endpoint_url])[0] if endpoint_url is None else endpoint_url
            region = qs.get("region", [region])[0] if region is None else region

        if not bucket:
            raise ValueError("S3ArchiveStorage requires a bucket")

        self._client = boto3.client("s3", endpoint_url=endpoint_url, region_name=region)
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self._buffer: List[Dict[str, Any]] = []
        self._flush_size = flush_size

    # ------------------------------------------------------------------
    # BaseStorage interface
    # ------------------------------------------------------------------
    def log_event(self, event: Dict[str, Any]) -> None:
        self._buffer.append(event)
        if len(self._buffer) >= self._flush_size:
            self._flush()

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
        # Naive scan implementation: iterate matching prefixes by date.
        out: List[Dict[str, Any]] = []
        for key in self._iter_keys(start_time, end_time):
            if len(out) >= limit:
                break
            try:
                obj = self._client.get_object(Bucket=self.bucket, Key=key)
                body = obj["Body"].read()
                if key.endswith(".gz"):
                    body = gzip.decompress(body)
                for line in body.splitlines():
                    if not line.strip():
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if agent_id and ev.get("agent_id") != agent_id:
                        continue
                    if event_type and ev.get("event_type") != event_type:
                        continue
                    if protocol and ev.get("protocol") != protocol:
                        continue
                    if correlation_id and ev.get("correlation_id") != correlation_id:
                        continue
                    out.append(ev)
                    if len(out) >= limit:
                        break
            except Exception as e:
                _log.debug("S3 archive scan miss for %s: %s", key, e)
        return out

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        for ev in self.query_events(limit=10000):
            if ev.get("id") == event_id:
                return ev
        return None

    def close(self) -> None:
        if self._buffer:
            self._flush()

    # ------------------------------------------------------------------
    def _flush(self) -> None:
        if not self._buffer:
            return
        now = datetime.now(timezone.utc)
        key = (
            f"{self.prefix}/{now.strftime('%Y/%m/%d/%H')}"
            f"/{now.strftime('%Y%m%dT%H%M%S')}-{now.microsecond:06d}.jsonl.gz"
        )
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            for ev in self._buffer:
                gz.write((json.dumps(ev, default=str) + "\n").encode("utf-8"))
        body = buf.getvalue()
        try:
            self._client.put_object(Bucket=self.bucket, Key=key, Body=body)
        except Exception as e:
            raise AOPStorageError(f"s3 put failed: {e}", operation="log_event")
        self._buffer.clear()

    def _iter_keys(self, start: Optional[datetime], end: Optional[datetime]):
        # All keys under prefix; for production the dashboard should narrow
        # via partition prefixes (year/month/day/hour).
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
            for obj in page.get("Contents", []) or []:
                yield obj["Key"]
