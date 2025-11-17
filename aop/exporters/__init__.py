"""
AOP Exporters Module

Provides exporters to integrate AOP events with standard observability formats:
- OpenTelemetry (OTEL)
- Prometheus
- JSON/CSV

All exporters use pull-based (on-demand) conversion.
"""

from typing import Dict, Type, Optional, Any

from .base import BaseExporter, register_exporter, get_exporter, list_exporters
from .json import JSONExporter
from .csv import CSVExporter
from .toon import ToonExporter

# Try to import optional exporters
OpenTelemetryExporter: Optional[Type[Any]] = None
PrometheusExporterServer: Optional[Type[Any]] = None
PrometheusExporter: Optional[Type[Any]] = None

try:
    from .otel import OpenTelemetryExporter
except ImportError:
    pass

try:
    from .prometheus import PrometheusExporterServer, PrometheusExporter
except ImportError:
    pass

__all__ = [
    # Base
    'BaseExporter',
    'register_exporter',
    'get_exporter',
    'list_exporters',

    # Exporters
    'OpenTelemetryExporter',
    'PrometheusExporterServer',
    'PrometheusExporter',
    'JSONExporter',
    'CSVExporter',
    'ToonExporter',
]

