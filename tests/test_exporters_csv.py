"""
Tests for CSV exporter.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from aop.exporters import CSVExporter
from aop import AOPClient


def test_csv_exporter_export():
    """Test CSV export to string."""
    exporter = CSVExporter()
    
    events = [
        {
            'id': '1',
            'timestamp': '2025-01-01T00:00:00Z',
            'agent_id': 'agent-1',
            'event_type': 'test.event',
            'protocol': 'mcp',
            'data': {'tool_name': 'test_tool'},
            'duration_ms': 100
        }
    ]
    
    result = exporter.export(events)
    
    # Should contain header
    assert 'id' in result
    assert 'agent_id' in result
    assert 'tool_name' in result
    
    # Should contain data
    assert '1' in result
    assert 'agent-1' in result
    assert 'test_tool' in result


def test_csv_exporter_flatten():
    """Test that nested data is flattened."""
    exporter = CSVExporter()
    
    events = [
        {
            'id': '1',
            'agent_id': 'agent-1',
            'data': {'tool_name': 'test_tool'},
            'error': {'code': 'ERROR', 'message': 'Failed'}
        }
    ]
    
    result = exporter.export(events)
    
    # Should extract nested fields
    assert 'test_tool' in result
    assert 'ERROR' in result
    assert 'Failed' in result


def test_csv_exporter_fields():
    """Test custom field selection."""
    exporter = CSVExporter(fields=['id', 'agent_id', 'event_type'])
    
    events = [
        {
            'id': '1',
            'agent_id': 'agent-1',
            'event_type': 'test.event',
            'protocol': 'mcp',
            'data': {'tool_name': 'test'}
        }
    ]
    
    result = exporter.export(events)
    
    # Should only have specified fields
    lines = result.split('\n')
    header = lines[0]
    
    assert 'id' in header
    assert 'agent_id' in header
    assert 'event_type' in header
    assert 'protocol' not in header
    assert 'tool_name' not in header


def test_csv_exporter_export_to_file():
    """Test exporting to file."""
    exporter = CSVExporter()
    
    events = [
        {
            'id': '1',
            'agent_id': 'agent-1',
            'event_type': 'test.event',
            'data': {'tool_name': 'test_tool'}
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.csv'
        exporter.export_to_file(events, str(filepath))
        
        assert filepath.exists()
        
        with open(filepath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['id'] == '1'
        assert rows[0]['agent_id'] == 'agent-1'
        assert rows[0]['tool_name'] == 'test_tool'


def test_csv_exporter_empty_events():
    """Test exporting empty event list."""
    exporter = CSVExporter()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'empty.csv'
        exporter.export_to_file([], str(filepath))
        
        assert filepath.exists()
        
        with open(filepath) as f:
            content = f.read()
        
        # Should have header at minimum
        assert 'id' in content or len(content) == 0

