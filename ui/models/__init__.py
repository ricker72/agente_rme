"""Data-transfer objects for the UI service boundary."""

from __future__ import annotations

from ui.models.autonomous_dto import (
    AutonomousDesignRequestDTO,
    AutonomousIterationDTO,
    AutonomousMetricsDTO,
    AutonomousResultDTO,
)
from ui.models.campaign_dto import CampaignDTO, CampaignRequestDTO, CampaignStageDTO
from ui.models.critic_dto import CriticDTO, CriticIssueDTO, CriticRequestDTO, HeatmapDTO
from ui.models.dashboard_dto import (
    CertificationDTO,
    DashboardDTO,
    HealthStatusDTO,
    MetricsDTO,
)
from ui.models.knowledge_dto import (
    KnowledgeMetricsDTO,
    KnowledgeQueryDTO,
    KnowledgeResultDTO,
)
from ui.models.otbm_dto import (
    OTBMExportRequestDTO,
    OTBMExportResultDTO,
    OTBMImportResultDTO,
    OTBMValidationDTO,
)
from ui.models.world_dto import WorldDTO, WorldGenerationRequestDTO, WorldSummaryDTO

KnowledgeDTO = KnowledgeResultDTO
OTBMExportDTO = OTBMExportResultDTO
OTBMImportDTO = OTBMImportResultDTO

__all__: list[str] = [
    "AutonomousDesignRequestDTO",
    "AutonomousIterationDTO",
    "AutonomousMetricsDTO",
    "AutonomousResultDTO",
    "CampaignDTO",
    "CampaignRequestDTO",
    "CampaignStageDTO",
    "CertificationDTO",
    "CriticDTO",
    "CriticIssueDTO",
    "CriticRequestDTO",
    "DashboardDTO",
    "HealthStatusDTO",
    "HeatmapDTO",
    "KnowledgeDTO",
    "KnowledgeMetricsDTO",
    "KnowledgeQueryDTO",
    "KnowledgeResultDTO",
    "MetricsDTO",
    "OTBMExportDTO",
    "OTBMExportRequestDTO",
    "OTBMExportResultDTO",
    "OTBMImportDTO",
    "OTBMImportResultDTO",
    "OTBMValidationDTO",
    "WorldDTO",
    "WorldGenerationRequestDTO",
    "WorldSummaryDTO",
]
