"""Conformance tests for W3C TraceContext propagation."""

import json
from pathlib import Path

import pytest

from aop.propagation import extract, inject

FIX = Path(__file__).parent / "fixtures" / "propagation" / "traceparent_vectors.json"


def _load():
    with open(FIX) as f:
        return json.load(f)


def test_valid_traceparent_extracts_correctly():
    for case in _load()["valid"]:
        ctx = extract({"traceparent": case["header"]})
        assert ctx is not None, case
        assert ctx.trace_id == case["trace_id"]
        assert ctx.span_id == case["span_id"]
        assert ctx.sampled == case["sampled"]


def test_invalid_traceparent_rejected():
    for case in _load()["invalid"]:
        ctx = extract({"traceparent": case["header"]})
        assert ctx is None, case


def test_inject_round_trip():
    cases = _load()["valid"]
    for case in cases:
        ctx_in = extract({"traceparent": case["header"]})
        carrier: dict = {}
        inject(carrier, ctx_in)
        assert "traceparent" in carrier
        # Round trip must produce the same header (lower-case hex)
        assert carrier["traceparent"] == case["header"].lower()
