"""Service registry for UI service dependencies."""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

from ui.services.service_exceptions import (
    ServiceAlreadyRegisteredError,
    ServiceNotFoundError,
)

T = TypeVar("T")
ServiceFactory = Callable[[], T]


class ServiceRegistry(Generic[T]):
    """Register, replace, and lazily resolve singleton services."""

    def __init__(self) -> None:
        self._instances: dict[str, T] = {}
        self._factories: dict[str, ServiceFactory[T]] = {}

    def register(
        self,
        name: str,
        service_or_factory: T | Callable[[], Any],
        *,
        force: bool = False,
    ) -> None:
        """Register a service instance or zero-argument lazy factory."""
        if not force and self.has(name):
            raise ServiceAlreadyRegisteredError(name)
        self._unregister(name)
        if callable(service_or_factory):
            self._factories[name] = service_or_factory
            return
        self._instances[name] = service_or_factory

    def register_factory(
        self,
        name: str,
        factory: ServiceFactory[T],
        *,
        force: bool = False,
    ) -> None:
        """Register a lazy singleton factory."""
        self.register(name, factory, force=force)

    def resolve(self, name: str) -> T:
        """Resolve a service, invoking and caching a factory if needed."""
        if name in self._instances:
            return self._instances[name]
        if name in self._factories:
            factory = self._factories.pop(name)
            instance = factory()
            self._instances[name] = instance
            return instance
        raise ServiceNotFoundError(name)

    def unregister(self, name: str) -> None:
        """Remove a service or factory if present."""
        self._unregister(name)

    def has(self, name: str) -> bool:
        """Return True when a service or factory is registered."""
        return name in self._instances or name in self._factories

    def clear(self) -> None:
        """Remove every registered service and factory."""
        self._instances.clear()
        self._factories.clear()

    def keys(self) -> list[str]:
        """Return all registered service names."""
        return sorted(set(self._instances) | set(self._factories))

    def _unregister(self, name: str) -> None:
        self._instances.pop(name, None)
        self._factories.pop(name, None)

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __len__(self) -> int:
        return len(self.keys())

    def __repr__(self) -> str:
        return f"ServiceRegistry(registered={self.keys()})"
