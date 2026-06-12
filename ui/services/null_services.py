"""Safe null implementations for UI service contracts."""

from __future__ import annotations

from ui.models.autonomous_dto import (
    AutonomousDesignRequestDTO,
    AutonomousIterationDTO,
    AutonomousMetricsDTO,
    AutonomousResultDTO,
)
from ui.models.campaign_dto import CampaignDTO, CampaignRequestDTO
from ui.models.critic_dto import CriticDTO, CriticRequestDTO, HeatmapDTO
from ui.models.dashboard_dto import DashboardDTO
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

STATUS = "Service not connected"


class _NullBase:
    """Shared null-service helpers."""

    service_name = "null"

    def is_connected(self) -> bool:
        """Null services are placeholders, not connected adapters."""
        return False


class NullWorldService(_NullBase):
    """Safe WorldService placeholder."""

    service_name = "world"

    def generate_world(self, request: WorldGenerationRequestDTO) -> WorldDTO:
        return WorldDTO(name=request.name, width=request.width, height=request.height)

    def get_recent_worlds(self) -> list[WorldDTO]:
        return []

    def get_world_summary(self, world_id: str) -> WorldSummaryDTO:
        return WorldSummaryDTO(world_id=world_id, status=STATUS)


class NullCriticService(_NullBase):
    """Safe CriticService placeholder."""

    service_name = "critic"

    def analyze_world(self, request: CriticRequestDTO) -> CriticDTO:
        return CriticDTO(summary=STATUS)

    def get_last_report(self) -> CriticDTO:
        return CriticDTO(summary=STATUS)

    def get_heatmaps(self) -> list[HeatmapDTO]:
        return []


class NullKnowledgeService(_NullBase):
    """Safe KnowledgeService placeholder."""

    service_name = "knowledge"

    def search(self, query: KnowledgeQueryDTO) -> list[KnowledgeResultDTO]:
        return []

    def find_similar(self, name: str, entry_type: str) -> list[KnowledgeResultDTO]:
        return []

    def get_metrics(self) -> KnowledgeMetricsDTO:
        return KnowledgeMetricsDTO(status=STATUS)


class NullCampaignService(_NullBase):
    """Safe CampaignService placeholder."""

    service_name = "campaign"

    def generate_campaign(self, request: CampaignRequestDTO) -> CampaignDTO:
        return CampaignDTO(name=request.name, status=STATUS)

    def get_last_campaign(self) -> CampaignDTO:
        return CampaignDTO(status=STATUS)


class NullOTBMService(_NullBase):
    """Safe OTBMService placeholder."""

    service_name = "otbm"

    def import_otbm(self, path: str) -> OTBMImportResultDTO:
        return OTBMImportResultDTO(path=path, message=STATUS)

    def export_otbm(self, request: OTBMExportRequestDTO) -> OTBMExportResultDTO:
        return OTBMExportResultDTO(path=request.output_path, message=STATUS)

    def validate_otbm(self, path: str) -> OTBMValidationDTO:
        return OTBMValidationDTO(path=path, message=STATUS)


class NullAutonomousService(_NullBase):
    """Safe AutonomousService placeholder."""

    service_name = "autonomous"

    def run_design(self, request: AutonomousDesignRequestDTO) -> AutonomousResultDTO:
        return AutonomousResultDTO(world_id=request.world_id, summary=STATUS)

    def get_iterations(self) -> list[AutonomousIterationDTO]:
        return []

    def get_metrics(self) -> AutonomousMetricsDTO:
        return AutonomousMetricsDTO(status=STATUS)


class NullDashboardService(_NullBase):
    """Safe DashboardService placeholder."""

    service_name = "dashboard"

    def load_dashboard(self) -> DashboardDTO:
        return DashboardDTO(status=STATUS)

    def refresh_dashboard(self) -> DashboardDTO:
        return DashboardDTO(status=STATUS)
