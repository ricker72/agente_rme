"""Tests for UI service contracts and DTO boundaries."""

from __future__ import annotations

from dataclasses import is_dataclass

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
from ui.services.autonomous_service import AutonomousService
from ui.services.campaign_service import CampaignService
from ui.services.critic_service import CriticService
from ui.services.dashboard_service import DashboardService
from ui.services.knowledge_service import KnowledgeService
from ui.services.otbm_service import OTBMService
from ui.services.world_service import WorldService


class StubWorldService:
    def generate_world(self, request: WorldGenerationRequestDTO) -> WorldDTO:
        return WorldDTO(name=request.name)

    def get_recent_worlds(self) -> list[WorldDTO]:
        return [WorldDTO(world_id="w1")]

    def get_world_summary(self, world_id: str) -> WorldSummaryDTO:
        return WorldSummaryDTO(world_id=world_id)


class StubCriticService:
    def analyze_world(self, request: CriticRequestDTO) -> CriticDTO:
        return CriticDTO(analysis_id=request.world_id)

    def get_last_report(self) -> CriticDTO:
        return CriticDTO(analysis_id="last")

    def get_heatmaps(self) -> list[HeatmapDTO]:
        return [HeatmapDTO(heatmap_id="h1")]


class StubKnowledgeService:
    def search(self, query: KnowledgeQueryDTO) -> list[KnowledgeResultDTO]:
        return [KnowledgeResultDTO(title=query.text)]

    def find_similar(self, name: str, entry_type: str) -> list[KnowledgeResultDTO]:
        return [KnowledgeResultDTO(title=name, entry_type=entry_type)]

    def get_metrics(self) -> KnowledgeMetricsDTO:
        return KnowledgeMetricsDTO(total_entries=1)


class StubCampaignService:
    def generate_campaign(self, request: CampaignRequestDTO) -> CampaignDTO:
        return CampaignDTO(name=request.name)

    def get_last_campaign(self) -> CampaignDTO:
        return CampaignDTO(campaign_id="c1")


class StubOTBMService:
    def import_otbm(self, path: str) -> OTBMImportResultDTO:
        return OTBMImportResultDTO(path=path)

    def export_otbm(self, request: OTBMExportRequestDTO) -> OTBMExportResultDTO:
        return OTBMExportResultDTO(path=request.output_path)

    def validate_otbm(self, path: str) -> OTBMValidationDTO:
        return OTBMValidationDTO(path=path)


class StubAutonomousService:
    def run_design(self, request: AutonomousDesignRequestDTO) -> AutonomousResultDTO:
        return AutonomousResultDTO(world_id=request.world_id)

    def get_iterations(self) -> list[AutonomousIterationDTO]:
        return [AutonomousIterationDTO(iteration_number=1)]

    def get_metrics(self) -> AutonomousMetricsDTO:
        return AutonomousMetricsDTO(total_iterations=1)


class StubDashboardService:
    def load_dashboard(self) -> DashboardDTO:
        return DashboardDTO(status="loaded")

    def refresh_dashboard(self) -> DashboardDTO:
        return DashboardDTO(status="refreshed")


def test_world_service_contract_returns_dtos() -> None:
    service: WorldService = StubWorldService()
    assert isinstance(service.generate_world(WorldGenerationRequestDTO()), WorldDTO)
    assert isinstance(service.get_recent_worlds()[0], WorldDTO)
    assert isinstance(service.get_world_summary("w1"), WorldSummaryDTO)


def test_critic_service_contract_returns_dtos() -> None:
    service: CriticService = StubCriticService()
    assert isinstance(service.analyze_world(CriticRequestDTO()), CriticDTO)
    assert isinstance(service.get_last_report(), CriticDTO)
    assert isinstance(service.get_heatmaps()[0], HeatmapDTO)


def test_knowledge_service_contract_returns_dtos() -> None:
    service: KnowledgeService = StubKnowledgeService()
    assert isinstance(service.search(KnowledgeQueryDTO())[0], KnowledgeResultDTO)
    assert isinstance(service.find_similar("orc", "creature")[0], KnowledgeResultDTO)
    assert isinstance(service.get_metrics(), KnowledgeMetricsDTO)


def test_campaign_service_contract_returns_dtos() -> None:
    service: CampaignService = StubCampaignService()
    assert isinstance(service.generate_campaign(CampaignRequestDTO()), CampaignDTO)
    assert isinstance(service.get_last_campaign(), CampaignDTO)


def test_otbm_service_contract_returns_dtos() -> None:
    service: OTBMService = StubOTBMService()
    assert isinstance(service.import_otbm("in.otbm"), OTBMImportResultDTO)
    assert isinstance(service.export_otbm(OTBMExportRequestDTO()), OTBMExportResultDTO)
    assert isinstance(service.validate_otbm("in.otbm"), OTBMValidationDTO)


def test_autonomous_service_contract_returns_dtos() -> None:
    service: AutonomousService = StubAutonomousService()
    assert isinstance(service.run_design(AutonomousDesignRequestDTO()), AutonomousResultDTO)
    assert isinstance(service.get_iterations()[0], AutonomousIterationDTO)
    assert isinstance(service.get_metrics(), AutonomousMetricsDTO)


def test_dashboard_service_contract_returns_dto() -> None:
    service: DashboardService = StubDashboardService()
    assert isinstance(service.load_dashboard(), DashboardDTO)
    assert isinstance(service.refresh_dashboard(), DashboardDTO)


def test_dtos_are_dataclasses_with_slots() -> None:
    dto_types = [
        WorldGenerationRequestDTO,
        WorldDTO,
        WorldSummaryDTO,
        CriticRequestDTO,
        CriticDTO,
        HeatmapDTO,
        KnowledgeQueryDTO,
        KnowledgeResultDTO,
        KnowledgeMetricsDTO,
        CampaignRequestDTO,
        CampaignDTO,
        OTBMImportResultDTO,
        OTBMExportRequestDTO,
        OTBMExportResultDTO,
        OTBMValidationDTO,
        AutonomousDesignRequestDTO,
        AutonomousResultDTO,
        AutonomousIterationDTO,
        AutonomousMetricsDTO,
        DashboardDTO,
    ]
    for dto_type in dto_types:
        assert is_dataclass(dto_type)
        assert hasattr(dto_type, "__slots__")
        assert not isinstance(dto_type(), dict)
