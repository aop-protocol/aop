"""
JSON exporter for AOP events.

Exports events to JSON format with options for pretty-printing and field selection.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseExporter


class JSONExporter(BaseExporter):
    """
    Exporter for JSON format.
    
    Supports:
    - Pretty-printed JSON output
    - Custom field selection
    - File or string output
    """
    
    def __init__(
        self,
        client: Optional[Any] = None,
        pretty: bool = True,
        fields: Optional[List[str]] = None
    ):
        """
        Initialize JSON exporter.
        
        Args:
            client: Optional AOPClient (not used for JSON export)
            pretty: Whether to pretty-print JSON (default: True)
            fields: Optional list of field names to include. If None, all fields included.
        """
        super().__init__(client)
        self.pretty = pretty
        self.fields = fields
    
    def export(self, events: List[Dict[str, Any]]) -> str:
        """
        Export events to JSON string.
        
        Args:
            events: List of AOP event dictionaries
            
        Returns:
            JSON string representation of events
        """
        # Filter fields if specified
        if self.fields:
            filtered_events = []
            for event in events:
                filtered = {k: v for k, v in event.items() if k in self.fields}
                filtered_events.append(filtered)
            events = filtered_events
        
        # Convert to JSON
        if self.pretty:
            return json.dumps(events, indent=2, default=str)
        else:
            return json.dumps(events, default=str)
    
    def export_to_file(self, events: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export events to JSON file.
        
        Args:
            events: List of AOP event dictionaries
            filepath: Path to output file
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        json_str = self.export(events)
        output_path.write_text(json_str, encoding='utf-8')

