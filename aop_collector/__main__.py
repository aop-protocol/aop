"""``python -m aop_collector serve`` entry point."""

from __future__ import annotations

import argparse
import logging
import sys

from .collector import Collector
from .config import CollectorConfig, ProcessorConfig, ReceiverConfig, load_config


def main(argv: list = None) -> int:
    parser = argparse.ArgumentParser("aop-collector")
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="Start the collector")
    serve.add_argument("--config", "-c", help="Path to YAML/JSON config")
    serve.add_argument("--port", type=int, default=4319)
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--exporter", default="stdout",
                       help="Quick exporter: stdout | sqlite:/// path | otlp_http:URL")
    serve.add_argument("--token", default=None, help="Single bearer token")
    serve.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.cmd == "serve":
        if args.config:
            cfg = load_config(args.config)
        else:
            cfg = CollectorConfig(
                receivers=[ReceiverConfig(host=args.host, port=args.port,
                                          auth_tokens=[args.token] if args.token else [])],
                processors=ProcessorConfig(),
                exporters=_quick_exporter(args.exporter),
            )
        c = Collector(cfg)
        c.serve(block=True)
        return 0
    return 1


def _quick_exporter(spec: str) -> list:
    from .config import ExporterConfig
    if spec == "stdout":
        return [ExporterConfig(type="stdout")]
    if spec.startswith("sqlite:"):
        return [ExporterConfig(type="sqlite", options={"url": spec})]
    if spec.startswith("otlp_http:"):
        return [ExporterConfig(type="otlp_http",
                               options={"endpoint": spec.split(":", 1)[1]})]
    return [ExporterConfig(type="stdout")]


if __name__ == "__main__":
    sys.exit(main())
