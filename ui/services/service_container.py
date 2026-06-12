"""Dependency injection container for UI services."""

from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar, cast

from ui.services.autonomous_service import AutonomousService
from ui.services.campaign_service import CampaignService
from ui.services.critic_service import CriticService
from ui.services.dashboard_service import DashboardService
from ui.services.knowledge_service import KnowledgeService
from ui.services.null_services import (
    NullAutonomousService,
    NullCampaignService,
    NullCriticService,
    NullDashboardService,
    NullKnowledgeService,
    NullOTBMService,
    NullWorldService,
)
from ui.services.otbm_service import OTBMService
from ui.services.service_exceptions import ServiceNotFoundError
from ui.services.service_registry import ServiceRegistry
from ui.services.world_service import WorldService

T = TypeVar("T")
ServiceFactory = Callable[[], T]


class ServiceContainer:
    """Thread-safe dependency injection container for UI services."""

    WORLD = "world"
    CRITIC = "critic"
    KNOWLEDGE = "knowledge"
    CAMPAIGN = "campaign"
    OTBM = "otbm"
    AUTONOMOUS = "autonomous"
    DASHBOARD = "dashboard"

    def __init__(self, registry: ServiceRegistry[Any] | None = None) -> None:
        self._registry: ServiceRegistry[Any] = registry or ServiceRegistry()
        self._lock = threading.RLock()

    def register_defaults(self) -> None:
        """Register safe null services for every official service contract."""
        self.register(self.WORLD, NullWorldService(), force=True)
        self.register(self.CRITIC, NullCriticService(), force=True)
        self.register(self.KNOWLEDGE, NullKnowledgeService(), force=True)
        self.register(self.CAMPAIGN, NullCampaignService(), force=True)
        self.register(self.OTBM, NullOTBMService(), force=True)
        self.register(self.AUTONOMOUS, NullAutonomousService(), force=True)
        self.register(self.DASHBOARD, NullDashboardService(), force=True)

    def register_core_adapters(self) -> None:
        """Explicitly activate core-backed UI adapters.

        Imports are intentionally local so creating a container or registering
        null defaults does not import frozen core modules.
        """
        from ui.adapters.autonomous_adapter import AutonomousAdapter
        from ui.adapters.campaign_adapter import CampaignAdapter
        from ui.adapters.critic_adapter import CriticAdapter
        from ui.adapters.dashboard_adapter import DashboardAdapter
        from ui.adapters.knowledge_adapter import KnowledgeAdapter
        from ui.adapters.otbm_adapter import OTBMAdapter
        from ui.adapters.world_adapter import WorldAdapter

        self.register(self.WORLD, WorldAdapter(), force=True)
        self.register(self.CRITIC, CriticAdapter(), force=True)
        self.register(self.KNOWLEDGE, KnowledgeAdapter(), force=True)
        self.register(self.CAMPAIGN, CampaignAdapter(), force=True)
        self.register(self.OTBM, OTBMAdapter(), force=True)
        self.register(self.AUTONOMOUS, AutonomousAdapter(), force=True)
        self.register(self.DASHBOARD, DashboardAdapter(), force=True)

    def register(
        self,
        name: str,
        service_or_factory: T | Callable[[], Any],
        *,
        force: bool = False,
    ) -> None:
        """Register or replace a service instance or lazy factory."""
        with self._lock:
            self._registry.register(name, service_or_factory, force=force)

    def register_factory(
        self,
        name: str,
        factory: ServiceFactory[T],
        *,
        force: bool = False,
    ) -> None:
        """Register a lazy service factory."""
        self.register(name, factory, force=force)

    def resolve(self, name: str) -> Any:
        """Resolve a service by name."""
        with self._lock:
            return self._registry.resolve(name)

    def resolve_or_none(self, name: str) -> Any | None:
        """Resolve a service, returning None when absent."""
        try:
            return self.resolve(name)
        except ServiceNotFoundError:
            return None

    def unregister(self, name: str) -> None:
        """Remove a service registration."""
        with self._lock:
            self._registry.unregister(name)

    def has(self, name: str) -> bool:
        """Return True if the service name is registered."""
        with self._lock:
            return self._registry.has(name)

    def clear(self) -> None:
        """Remove every service registration."""
        with self._lock:
            self._registry.clear()

    def keys(self) -> list[str]:
        """Return registered service names."""
        with self._lock:
            return self._registry.keys()

    def register_mock(self, name: str, mock_instance: T) -> None:
        """Replace a service with a test double."""
        self.register(name, mock_instance, force=True)

    def get_world_service(self) -> WorldService:
        """Return the configured world service."""
        return cast(WorldService, self.resolve(self.WORLD))

    def get_critic_service(self) -> CriticService:
        """Return the configured critic service."""
        return cast(CriticService, self.resolve(self.CRITIC))

    def get_knowledge_service(self) -> KnowledgeService:
        """Return the configured knowledge service."""
        return cast(KnowledgeService, self.resolve(self.KNOWLEDGE))

    def get_campaign_service(self) -> CampaignService:
        """Return the configured campaign service."""
        return cast(CampaignService, self.resolve(self.CAMPAIGN))

    def get_otbm_service(self) -> OTBMService:
        """Return the configured OTBM service."""
        return cast(OTBMService, self.resolve(self.OTBM))

    def get_autonomous_service(self) -> AutonomousService:
        """Return the configured autonomous service."""
        return cast(AutonomousService, self.resolve(self.AUTONOMOUS))

    def get_dashboard_service(self) -> DashboardService:
        """Return the configured dashboard service."""
        return cast(DashboardService, self.resolve(self.DASHBOARD))

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __repr__(self) -> str:
        return f"ServiceContainer(registered={self.keys()})"
