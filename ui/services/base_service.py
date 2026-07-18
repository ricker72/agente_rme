"""Common base protocol for UI service implementations."""

from __future__ import annotations

from typing import Protocol


class BaseService(Protocol):
    """Minimal lifecycle contract shared by concrete services."""

    @property
    def service_name(self) -> str:
        """Return the stable service identifier."""
        ...

    def is_connected(self) -> bool:
        """Return whether this service has a real adapter behind it."""
        ...
