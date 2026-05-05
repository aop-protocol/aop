"""Transport base class + DirectTransport (writes to a local storage)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..storage.base import BaseStorage


class BaseTransport(ABC):
    """Abstract transport — hand off events somewhere."""

    @abstractmethod
    def export(self, events: List[Dict[str, Any]]) -> None:
        """Ship a batch of events. Should be best-effort."""

    def shutdown(self, timeout_s: float = 5.0) -> None:
        """Flush and release resources. Default: no-op."""


class DirectTransport(BaseTransport):
    """Write events straight into a local ``BaseStorage`` (default behaviour)."""

    def __init__(self, storage: "BaseStorage") -> None:
        self._storage = storage

    def export(self, events: List[Dict[str, Any]]) -> None:
        for ev in events:
            try:
                self._storage.log_event(ev)
            except Exception:
                continue

    def shutdown(self, timeout_s: float = 5.0) -> None:
        try:
            self._storage.close()
        except Exception:
            pass
