"""AOP transports: client-side carriers that deliver events to a Collector.

A *transport* is the moral equivalent of an OTel ``SpanExporter`` — it takes
batches of AOP events and ships them somewhere. The default
``DirectTransport`` writes straight to a local storage backend (the v1.0
behaviour). Other transports send over the wire to an AOP Collector or to
any OTLP-compatible endpoint (Datadog, Honeycomb, Tempo, Grafana Cloud, ...).

Transports compose:

    BatchProcessor ── HTTPTransport / OTLPHTTPTransport / OTLPGRPCTransport
                       ↓
                   AOP Collector or third-party OTLP backend

Tests + dev usage typically just use ``DirectTransport`` (no network).
"""

from __future__ import annotations

from .base import BaseTransport, DirectTransport
from .batch import BatchProcessor
from .http_json import HTTPJSONTransport
from .otlp_http import OTLPHTTPTransport
from .otlp_grpc import OTLPGRPCTransport

__all__ = [
    "BaseTransport",
    "DirectTransport",
    "BatchProcessor",
    "HTTPJSONTransport",
    "OTLPHTTPTransport",
    "OTLPGRPCTransport",
]
