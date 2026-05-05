"""
AOP Collector

A standalone receiver/processor/exporter pipeline that:

  • exposes an HTTP receiver on /v1/events for AOP-native JSON ingestion
  • exposes /v1/logs (OTLP/HTTP JSON) for OTel-compatible ingestion
  • runs configurable redaction, sampling, and enrichment processors
  • forwards to one or more exporters (SQLite, Postgres, ClickHouse, OTLP-out)

Run it from the command line:

    python -m aop_collector serve --config collector.yaml

or programmatically:

    from aop_collector import Collector
    c = Collector.from_yaml("collector.yaml"); c.serve()
"""

__version__ = "1.1.0"

from .collector import Collector
from .pipeline import Pipeline, ProcessorChain
from .receivers import HTTPReceiver
from .config import CollectorConfig, load_config

__all__ = [
    "__version__",
    "Collector",
    "Pipeline",
    "ProcessorChain",
    "HTTPReceiver",
    "CollectorConfig",
    "load_config",
]
