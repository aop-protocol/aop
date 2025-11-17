"""
TOON Exporter for AOP Events

Exports AOP events to TOON (Token-Oriented Object Notation) format
for LLM-optimized observability data.

Key Features:
- 30-60% token reduction vs JSON for uniform event arrays
- Field flattening (data.*, metadata.*, error.*) for maximum compactness
- Optional field filtering (include/exclude)
- Three delimiter options (comma/tab/pipe)

Perfect for:
- AI-assisted debugging and trace analysis
- Reducing LLM API costs
- Passing large event datasets in prompts
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseExporter
from .toon_encoder import ToonEncoder, DelimiterType


class ToonExporter(BaseExporter):
    """
    Exporter for TOON format - optimized for LLM consumption.

    Example output (flattened):
    events[100]{id,timestamp,event_type,data.tool_name,data.duration_ms}:
      evt-1,2025-01-15T10:00:00Z,mcp.tool.called,search,45
      evt-2,2025-01-15T10:00:01Z,mcp.tool.completed,search,120

    This achieves 30-60% token reduction compared to equivalent JSON.
    """

    def __init__(
        self,
        client: Optional[Any] = None,
        flatten: bool = True,
        delimiter: DelimiterType = 'comma',
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ):
        """
        Initialize TOON exporter.

        Args:
            client: Optional AOPClient instance
            flatten: Flatten nested data/metadata/error fields (default: True)
                     When True: data.tool_name, metadata.user_id, error.message
                     When False: Keep nested structure
            delimiter: Delimiter for tabular arrays ('comma', 'tab', 'pipe')
            include_fields: Only include these fields (None = include all)
            exclude_fields: Exclude these fields (None = exclude none)

        Note:
            flatten=True is recommended for maximum token savings.
            For 100 events, flattening can save 30-40% additional tokens.
        """
        super().__init__(client)
        self.flatten = flatten
        self.delimiter = delimiter
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields or []

        # Always exclude these internal fields by default
        self.exclude_fields.extend(['instance_id', 'version'])

        # Initialize encoder
        self.encoder = ToonEncoder(delimiter=delimiter)

    def export(self, events: List[Dict[str, Any]]) -> str:
        """
        Export events to TOON format string.

        Args:
            events: List of AOP event dictionaries

        Returns:
            TOON formatted string

        Example:
            >>> exporter = ToonExporter(flatten=True)
            >>> events = [
            ...     {
            ...         'id': 'evt-1',
            ...         'timestamp': '2025-01-15T10:00:00Z',
            ...         'event_type': 'mcp.tool.called',
            ...         'data': {'tool_name': 'search', 'duration_ms': 45}
            ...     }
            ... ]
            >>> print(exporter.export(events))
            events[1]{id,timestamp,event_type,data.tool_name,data.duration_ms}:
              evt-1,2025-01-15T10:00:00Z,mcp.tool.called,search,45
        """
        if not events:
            return 'events[0]{}:\n'

        # Process events (flatten, filter)
        processed_events = []
        for event in events:
            processed = self._process_event(event)
            processed_events.append(processed)

        # Encode to TOON
        # Wrap in dict with 'events' key for better TOON header
        toon_data = {'events': processed_events}
        return self.encoder.encode(toon_data)

    def export_to_file(self, events: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export events to TOON file.

        Args:
            events: List of AOP event dictionaries
            filepath: Path to output file (typically .toon extension)
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        toon_str = self.export(events)
        output_path.write_text(toon_str, encoding='utf-8')

    def _process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single event (flatten + filter).

        Args:
            event: Original AOP event

        Returns:
            Processed event dictionary
        """
        # Flatten if enabled
        if self.flatten:
            processed = self._flatten_event(event)
        else:
            processed = event.copy()

        # Apply field filtering
        processed = self._filter_fields(processed)

        return processed

    def _flatten_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested data, metadata, and error fields.

        Transform:
            {
                'id': 'evt-1',
                'data': {'tool_name': 'search', 'duration_ms': 45},
                'metadata': {'user_id': 'u123'}
            }

        Into:
            {
                'id': 'evt-1',
                'data.tool_name': 'search',
                'data.duration_ms': 45,
                'metadata.user_id': 'u123'
            }

        This enables TOON's tabular format to work optimally.
        """
        flattened = {}

        for key, value in event.items():
            if key in ('data', 'metadata', 'error') and isinstance(value, dict):
                # Flatten nested dict
                for nested_key, nested_value in value.items():
                    flat_key = f"{key}.{nested_key}"
                    flattened[flat_key] = nested_value
            else:
                # Keep as-is
                flattened[key] = value

        return flattened

    def _filter_fields(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter fields based on include/exclude lists.

        Args:
            event: Event dictionary

        Returns:
            Filtered event dictionary
        """
        # If include_fields specified, only keep those
        if self.include_fields:
            filtered = {k: v for k, v in event.items() if k in self.include_fields}
        else:
            filtered = event.copy()

        # Remove excluded fields
        for field in self.exclude_fields:
            filtered.pop(field, None)

        return filtered

    def get_token_estimate(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Estimate token counts for TOON vs JSON.

        Returns:
            Dictionary with 'toon', 'json', and 'savings_percent' keys

        Note:
            This is a rough estimate using character count / 4 as proxy.
            Actual token counts depend on the tokenizer used.
        """
        import json

        # Export to both formats
        toon_output = self.export(events)
        json_output = json.dumps(events, default=str)

        # Rough token estimation (chars / 4)
        toon_tokens = len(toon_output) // 4
        json_tokens = len(json_output) // 4

        savings = ((json_tokens - toon_tokens) / json_tokens * 100) if json_tokens > 0 else 0

        return {
            'toon': toon_tokens,
            'json': json_tokens,
            'savings_percent': round(savings, 1)
        }


def export_events(
    events: List[Dict[str, Any]],
    flatten: bool = True,
    delimiter: DelimiterType = 'comma'
) -> str:
    """
    Convenience function to export events to TOON format.

    Args:
        events: List of AOP event dictionaries
        flatten: Flatten nested fields (default: True)
        delimiter: Delimiter type ('comma', 'tab', 'pipe')

    Returns:
        TOON formatted string

    Example:
        >>> from aop.exporters.toon import export_events
        >>> toon_output = export_events(my_events, flatten=True)
        >>> print(toon_output)
    """
    exporter = ToonExporter(flatten=flatten, delimiter=delimiter)
    return exporter.export(events)
