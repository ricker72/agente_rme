"""Service-layer exceptions for UI dependency injection."""

from __future__ import annotations


class ServiceError(RuntimeError):
    """Base class for UI service-layer errors."""


class ServiceNotFoundError(ServiceError, LookupError):
    """Raised when a requested service is not registered."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' is not registered")


class ServiceAlreadyRegisteredError(ServiceError):
    """Raised when attempting to register a duplicate service."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' is already registered")
