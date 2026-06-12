"""UI service contracts and dependency injection helpers."""

from __future__ import annotations

from ui.services.autonomous_service import AutonomousService
from ui.services.base_service import BaseService
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
from ui.services.service_container import ServiceContainer
from ui.services.service_exceptions import (
    ServiceAlreadyRegisteredError,
    ServiceError,
    ServiceNotFoundError,
)
from ui.services.service_registry import ServiceRegistry
from ui.services.world_service import WorldService

__all__: list[str] = [
    "AutonomousService",
    "BaseService",
    "CampaignService",
    "CriticService",
    "DashboardService",
    "KnowledgeService",
    "NullAutonomousService",
    "NullCampaignService",
    "NullCriticService",
    "NullDashboardService",
    "NullKnowledgeService",
    "NullOTBMService",
    "NullWorldService",
    "OTBMService",
    "ServiceAlreadyRegisteredError",
    "ServiceContainer",
    "ServiceError",
    "ServiceNotFoundError",
    "ServiceRegistry",
    "WorldService",
]
