"""
TOON (Token-Oriented Object Notation) Encoder

Implements TOON v2.0 specification for LLM-optimized data serialization.
Achieves 30-60% token reduction compared to JSON on uniform object arrays.

TOON Format Overview:
- Indentation-based like YAML
- Tabular layout for uniform object arrays (CSV-style)
- Smart quoting (only when necessary)
- Three delimiter options: comma, tab, pipe

References:
- Specification: https://github.com/toon-format/toon
- Version: 2.0
"""

from typing import Any, Dict, List, Union, Optional, Literal
import re


DelimiterType = Literal['comma', 'tab', 'pipe']


class ToonEncoder:
    """
    Encodes Python data structures to TOON format.

    Features:
    - Automatic detection of uniform object arrays
    - Smart quoting (only when necessary)
    - Configurable delimiters (comma/tab/pipe)
    - Indentation-based hierarchy
    """

    DELIMITER_CHARS = {
        'comma': ',',
        'tab': '\t',
        'pipe': '|',
    }

    # Characters that require quoting in TOON
    QUOTE_REQUIRED_PATTERN = re.compile(r'[,\t\|\[\]\{\}\:\n\r\s]|^null$|^true$|^false$|^-?\d+(\.\d+)?$')

    def __init__(
        self,
        delimiter: DelimiterType = 'comma',
        indent: str = '  ',
        max_inline_items: int = 5,
    ):
        """
        Initialize TOON encoder.

        Args:
            delimiter: Delimiter type for tabular arrays ('comma', 'tab', 'pipe')
            indent: Indentation string (default: 2 spaces)
            max_inline_items: Maximum items to show inline for short arrays
        """
        self.delimiter = delimiter
        self.delimiter_char = self.DELIMITER_CHARS[delimiter]
        self.indent = indent
        self.max_inline_items = max_inline_items

    def encode(self, data: Any) -> str:
        """
        Encode data to TOON format.

        Args:
            data: Python object to encode (dict, list, or primitive)

        Returns:
            TOON formatted string
        """
        return self._encode_value(data, level=0, key=None)

    def _encode_value(self, value: Any, level: int, key: Optional[str] = None) -> str:
        """Encode a value at given indentation level."""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return self._quote_string(value)
        elif isinstance(value, dict):
            return self._encode_object(value, level, key)
        elif isinstance(value, list):
            return self._encode_array(value, level, key)
        else:
            # Fallback for unknown types
            return self._quote_string(str(value))

    def _encode_object(self, obj: Dict[str, Any], level: int, key: Optional[str] = None) -> str:
        """Encode a dictionary as TOON object."""
        if not obj:
            return '{}'

        lines = []
        indent = self.indent * level

        for obj_key, obj_value in obj.items():
            # Encode key
            encoded_key = self._quote_string(obj_key, force_quote=False)

            # Simple values on same line
            if isinstance(obj_value, (type(None), bool, int, float, str)):
                encoded_value = self._encode_value(obj_value, level + 1)
                lines.append(f"{indent}{encoded_key}: {encoded_value}")
            else:
                # Complex values on next line
                encoded_value = self._encode_value(obj_value, level + 1, key=obj_key)
                lines.append(f"{indent}{encoded_key}:")
                lines.append(encoded_value)

        return '\n'.join(lines)

    def _encode_array(self, arr: List[Any], level: int, key: Optional[str] = None) -> str:
        """
        Encode an array - with automatic tabular format detection.

        Detects if array contains uniform objects and uses tabular format,
        otherwise uses standard list format.
        """
        if not arr:
            return '[]'

        # Check if array is uniform objects (candidate for tabular format)
        if self._is_uniform_object_array(arr):
            return self._encode_tabular_array(arr, level, key)
        else:
            return self._encode_list_array(arr, level)

    def _is_uniform_object_array(self, arr: List[Any]) -> bool:
        """
        Check if array contains uniform objects (all dicts with same keys).

        Returns True only if:
        - All elements are dictionaries
        - All dictionaries have the exact same keys
        - Array has at least 2 elements (tabular format not worth it for single item)
        """
        if len(arr) < 2:
            return False

        if not all(isinstance(item, dict) for item in arr):
            return False

        # Get keys from first item
        first_keys = set(arr[0].keys())

        # Check all items have same keys
        return all(set(item.keys()) == first_keys for item in arr)

    def _encode_tabular_array(self, arr: List[Dict[str, Any]], level: int, key: Optional[str] = None) -> str:
        """
        Encode uniform object array in tabular format (TOON's killer feature).

        Format:
        key[count]{field1,field2,field3}:
          value1,value2,value3
          value4,value5,value6

        This is where TOON achieves 30-60% token savings vs JSON.
        """
        if not arr:
            return '[]'

        indent = self.indent * level

        # Get field names from first object
        fields = list(arr[0].keys())
        field_count = len(fields)

        # Build header
        array_key = key or 'items'
        field_list = ','.join(fields)
        header = f"{indent}{array_key}[{len(arr)}]{{{field_list}}}:"

        # Build rows
        rows = []
        for item in arr:
            values = []
            for field in fields:
                value = item.get(field)
                encoded = self._encode_value(value, level + 1)
                values.append(encoded)

            row = self.delimiter_char.join(values)
            rows.append(f"{indent}{self.indent}{row}")

        return '\n'.join([header] + rows)

    def _encode_list_array(self, arr: List[Any], level: int) -> str:
        """
        Encode array in standard list format.

        Format for short arrays (inline):
        [item1, item2, item3]

        Format for longer arrays (multiline):
        [
          item1
          item2
          item3
        ]
        """
        # Inline format for short arrays of primitives
        if len(arr) <= self.max_inline_items and all(
            isinstance(item, (type(None), bool, int, float, str)) for item in arr
        ):
            items = [self._encode_value(item, level) for item in arr]
            return '[' + ', '.join(items) + ']'

        # Multiline format
        indent = self.indent * level
        lines = ['[']
        for item in arr:
            encoded = self._encode_value(item, level + 1)
            # Indent each item
            if '\n' in encoded:
                # Multi-line item
                lines.append(f"{indent}{self.indent}{encoded}")
            else:
                # Single-line item
                lines.append(f"{indent}{self.indent}{encoded}")
        lines.append(f"{indent}]")

        return '\n'.join(lines)

    def _quote_string(self, s: str, force_quote: bool = False) -> str:
        """
        Smart quoting for TOON strings.

        Only quotes when necessary:
        - String contains special characters (, | tab [ ] { } : whitespace newline)
        - String looks like a number, boolean, or null
        - force_quote is True
        """
        if force_quote or self.QUOTE_REQUIRED_PATTERN.search(s):
            # Escape quotes and backslashes
            escaped = s.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        return s

    def _needs_quoting(self, s: str) -> bool:
        """Check if string needs quoting."""
        return bool(self.QUOTE_REQUIRED_PATTERN.search(s))


def encode(data: Any, delimiter: DelimiterType = 'comma') -> str:
    """
    Convenience function to encode data to TOON format.

    Args:
        data: Python object to encode
        delimiter: Delimiter type ('comma', 'tab', 'pipe')

    Returns:
        TOON formatted string

    Example:
        >>> events = [
        ...     {'id': 1, 'name': 'event1', 'duration': 100},
        ...     {'id': 2, 'name': 'event2', 'duration': 150}
        ... ]
        >>> print(encode(events))
        items[2]{id,name,duration}:
          1,event1,100
          2,event2,150
    """
    encoder = ToonEncoder(delimiter=delimiter)
    return encoder.encode(data)
