"""Run the conformance event/trace fixtures against the Python SDK."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path

import pytest

from aop.exceptions import AOPValidationError
from aop.validation import validate_event

FIX = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("path", sorted(glob.glob(str(FIX / "events" / "*.json"))))
def test_valid_events_pass(path: str) -> None:
    with open(path) as f:
        ev = json.load(f)
    validate_event(ev)


@pytest.mark.parametrize("path", sorted(glob.glob(str(FIX / "events_invalid" / "*.json"))))
def test_invalid_events_fail(path: str) -> None:
    with open(path) as f:
        ev = json.load(f)
    with pytest.raises(AOPValidationError):
        validate_event(ev)


def test_trace_fixture_validates() -> None:
    with open(FIX / "traces" / "01_multi_protocol_trace.json") as f:
        trace = json.load(f)
    seen_trace_ids = set()
    for ev in trace["events"]:
        validate_event(ev)
        seen_trace_ids.add(ev["trace_id"])
    # All events must belong to the same trace
    assert seen_trace_ids == {trace["trace_id"]}
