"""Collector YAML/JSON config loading."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ReceiverConfig:
    type: str = "http"
    host: str = "0.0.0.0"
    port: int = 4319
    auth_tokens: List[str] = field(default_factory=list)
    rate_limit_per_minute: Optional[int] = None
    require_tls: bool = False


@dataclass
class ProcessorConfig:
    redact: bool = True
    sampler: str = "always_on"           # always_on | always_off | trace_id_ratio
    sampler_ratio: float = 1.0
    enrich_resource: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExporterConfig:
    type: str                              # sqlite | postgres | clickhouse | otlp_http | otlp_grpc | s3
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectorConfig:
    receivers: List[ReceiverConfig] = field(default_factory=lambda: [ReceiverConfig()])
    processors: ProcessorConfig = field(default_factory=ProcessorConfig)
    exporters: List[ExporterConfig] = field(default_factory=list)


def load_config(path: str) -> CollectorConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r") as f:
        text = f.read()
    if path.endswith((".yml", ".yaml")):
        try:
            import yaml  # type: ignore
        except ImportError as e:
            raise ImportError("PyYAML required for YAML configs") from e
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return _from_dict(data or {})


def _from_dict(data: Dict[str, Any]) -> CollectorConfig:
    rcs = [ReceiverConfig(**r) for r in (data.get("receivers") or [{}])]
    proc_data = data.get("processors") or {}
    proc = ProcessorConfig(
        redact=proc_data.get("redact", True),
        sampler=proc_data.get("sampler", "always_on"),
        sampler_ratio=float(proc_data.get("sampler_ratio", 1.0)),
        enrich_resource=proc_data.get("enrich_resource") or {},
    )
    exps = [ExporterConfig(**e) for e in (data.get("exporters") or [])]
    return CollectorConfig(receivers=rcs, processors=proc, exporters=exps)
