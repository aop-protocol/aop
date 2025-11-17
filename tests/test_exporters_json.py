"""
Tests for JSON exporter.
"""

import json
import tempfile
from pathlib import Path

import pytest

from aop.exporters import JSONExporter
from aop import AOPClient


def test_json_exporter_export():
    """Test JSON export to string."""
    exporter = JSONExporter()
    
    events = [
        {'id': '1', 'event_type': 'test.event', 'agent_id': 'agent-1'},
        {'id': '2', 'event_type': 'test.event', 'agent_id': 'agent-2'}
    ]
    
    result = exporter.export(events)
    parsed = json.loads(result)
    
    assert len(parsed) == 2
    assert parsed[0]['id'] == '1'
    assert parsed[1]['id'] == '2'


def test_json_exporter_pretty():
    """Test pretty-printed JSON."""
    exporter = JSONExporter(pretty=True)
    events = [{'id': '1'}]
    
    result = exporter.export(events)
    # Pretty JSON should have newlines
    assert '\n' in result


def test_json_exporter_not_pretty():
    """Test compact JSON."""
    exporter = JSONExporter(pretty=False)
    events = [{'id': '1'}]
    
    result = exporter.export(events)
    # Compact JSON should be on one line
    assert '\n' not in result or result.strip().count('\n') == 0


def test_json_exporter_fields():
    """Test field filtering."""
    exporter = JSONExporter(fields=['id', 'event_type'])
    
    events = [
        {'id': '1', 'event_type': 'test', 'agent_id': 'agent-1', 'extra': 'data'}
    ]
    
    result = exporter.export(events)
    parsed = json.loads(result)
    
    assert 'id' in parsed[0]
    assert 'event_type' in parsed[0]
    assert 'agent_id' not in parsed[0]
    assert 'extra' not in parsed[0]


def test_json_exporter_export_to_file():
    """Test exporting to file."""
    exporter = JSONExporter()
    
    events = [{'id': '1', 'test': 'data'}]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        exporter.export_to_file(events, str(filepath))
        
        assert filepath.exists()
        
        with open(filepath) as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['id'] == '1'


def test_json_exporter_empty_events():
    """Test exporting empty event list."""
    exporter = JSONExporter()
    result = exporter.export([])
    parsed = json.loads(result)
    assert parsed == []

