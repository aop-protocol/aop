"""Conformance tests for the protocol registry."""

import json
from pathlib import Path

from aop.registry import all_event_types, supported_protocols

FIX = Path(__file__).parent / "fixtures" / "registry" / "builtin_protocols.json"


def _load():
    with open(FIX) as f:
        return json.load(f)


def test_all_required_protocols_registered():
    fix = _load()
    registered = supported_protocols()
    for name in fix["must_be_registered"]:
        assert name in registered, f"{name!r} is not in supported_protocols()"


def test_required_event_types_present():
    fix = _load()
    types = all_event_types()
    for proto, expected in fix["must_contain_event_types"].items():
        for et in expected:
            assert et in types, f"{et!r} should be registered for {proto}"
