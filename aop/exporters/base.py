"""
Base exporter class and registration system.

Provides abstract base class for all exporters and simple registration mechanism.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, Optional

from ..client import AOPClient


class BaseExporter(ABC):
    """
    Abstract base class for all AOP exporters.
    
    All exporters must inherit from this class and implement the required methods.
    """
    
    def __init__(self, client: Optional[AOPClient] = None):
        """
        Initialize exporter.
        
        Args:
            client: Optional AOPClient instance. If not provided, exporter
                    methods that need a client will raise an error.
        """
        self.client = client
    
    @abstractmethod
    def export(self, events: List[Dict[str, Any]]) -> Any:
        """
        Export a list of events to the target format.
        
        Args:
            events: List of AOP event dictionaries
            
        Returns:
            Exported data in target format (format depends on exporter)
            
        Raises:
            ValueError: If client is required but not provided
        """
        pass
    
    def export_trace(self, correlation_id: str) -> Any:
        """
        Export a complete trace by correlation_id.
        
        Args:
            correlation_id: Correlation ID of the trace to export
            
        Returns:
            Exported trace data in target format
            
        Raises:
            ValueError: If client is not provided
        """
        if not self.client:
            raise ValueError("AOPClient required for export_trace. Provide client in __init__.")
        
        # Get all events for this trace
        events = self.client.get_trace(correlation_id)
        return self.export(events)
    
    def validate_config(self) -> bool:
        """
        Validate exporter configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        return True


# Simple registration system (middle ground approach)
_registry: Dict[str, Type[BaseExporter]] = {}


def register_exporter(name: str, exporter_class: Type[BaseExporter]) -> None:
    """
    Register a custom exporter class.
    
    Args:
        name: Unique name for the exporter
        exporter_class: Exporter class (must inherit from BaseExporter)
        
    Raises:
        ValueError: If name is already registered or class is invalid
    """
    if not issubclass(exporter_class, BaseExporter):
        raise ValueError(f"Exporter class must inherit from BaseExporter")
    
    if name in _registry:
        raise ValueError(f"Exporter '{name}' is already registered")
    
    _registry[name] = exporter_class


def get_exporter(name: str, client: Optional[AOPClient] = None) -> BaseExporter:
    """
    Get a registered exporter instance.
    
    Args:
        name: Name of the exporter
        client: Optional AOPClient instance to pass to exporter
        
    Returns:
        Exporter instance
        
    Raises:
        ValueError: If exporter is not registered
    """
    if name not in _registry:
        raise ValueError(f"Exporter '{name}' is not registered. Available: {list_exporters()}")
    
    exporter_class = _registry[name]
    return exporter_class(client=client)


def list_exporters() -> List[str]:
    """
    List all registered exporter names.
    
    Returns:
        List of exporter names
    """
    return list(_registry.keys())

