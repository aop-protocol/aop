"""
CSV exporter for AOP events.

Exports events to CSV format with flattening of nested data structures.
"""

import csv
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseExporter


class CSVExporter(BaseExporter):
    """
    Exporter for CSV format.
    
    Supports:
    - Flattening nested data structures
    - Custom field selection
    - File or string output
    """
    
    def __init__(
        self,
        client: Optional[Any] = None,
        fields: Optional[List[str]] = None
    ):
        """
        Initialize CSV exporter.
        
        Args:
            client: Optional AOPClient (not used for CSV export)
            fields: Optional list of field names to include. If None, uses default fields.
        """
        super().__init__(client)
        self.fields = fields or [
            'id', 'timestamp', 'agent_id', 'event_type', 'protocol',
            'correlation_id', 'parent_id', 'duration_ms', 'tool_name',
            'error_code', 'error_message'
        ]
    
    def _flatten_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten an event dictionary for CSV export.
        
        Args:
            event: AOP event dictionary
            
        Returns:
            Flattened dictionary
        """
        row: Dict[str, Any] = {}
        
        # Standard fields
        row['id'] = event.get('id')
        row['timestamp'] = event.get('timestamp')
        row['agent_id'] = event.get('agent_id')
        row['event_type'] = event.get('event_type')
        row['protocol'] = event.get('protocol')
        row['correlation_id'] = event.get('correlation_id')
        row['parent_id'] = event.get('parent_id')
        row['duration_ms'] = event.get('duration_ms')
        
        # Extract from nested data
        data = event.get('data', {})
        row['tool_name'] = data.get('tool_name')
        
        # Extract from nested error
        error = event.get('error')
        if error:
            row['error_code'] = error.get('code')
            row['error_message'] = error.get('message')
        else:
            row['error_code'] = None
            row['error_message'] = None
        
        # Filter to requested fields only
        if self.fields:
            row = {k: v for k, v in row.items() if k in self.fields}
        
        return row
    
    def export(self, events: List[Dict[str, Any]]) -> str:
        """
        Export events to CSV string.
        
        Args:
            events: List of AOP event dictionaries
            
        Returns:
            CSV string representation of events
        """
        if not events:
            return ""
        
        # Flatten all events
        flattened = [self._flatten_event(event) for event in events]
        
        # Get all unique field names
        all_fields = set()
        for row in flattened:
            all_fields.update(row.keys())
        
        # Use specified fields or all fields found
        fieldnames = self.fields if self.fields else sorted(all_fields)
        
        # Generate CSV
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(flattened)
        
        return output.getvalue()
    
    def export_to_file(self, events: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export events to CSV file.
        
        Args:
            events: List of AOP event dictionaries
            filepath: Path to output file
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not events:
            # Write empty file with just header
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fields, extrasaction='ignore')
                writer.writeheader()
            return
        
        # Flatten all events
        flattened = [self._flatten_event(event) for event in events]
        
        # Get all unique field names
        all_fields = set()
        for row in flattened:
            all_fields.update(row.keys())
        
        # Use specified fields or all fields found
        fieldnames = self.fields if self.fields else sorted(all_fields)
        
        # Write CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(flattened)

