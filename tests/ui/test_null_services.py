"""Tests for safe null service behavior."""

from __future__ import annotations

from ui.models.autonomous_dto import AutonomousDesignRequestDTO, AutonomousResultDTO
from ui.models.campaign_dto import CampaignRequestDTO
from ui.models.critic_dto import CriticRequestDTO
from ui.models.dashboard_dto import DashboardDTO
from ui.models.knowledge_dto import KnowledgeMetricsDTO, KnowledgeQueryDTO
from ui.models.otbm_dto import OTBMExportRequestDTO
from ui.models.world_dto import WorldGenerationRequestDTO
from ui.services.null_services import (
    STATUS,
    NullAutonomousService,
    NullCampaignService,
    NullCriticService,
    NullDashboardService,
    NullKnowledgeService,
    NullOTBMService,
    NullWorldService,
)


def test_null_world_service_is_safe() -> None:
    service = NullWorldService()
    world = service.generate_world(WorldGenerationRequestDTO(name="draft"))
    assert world.name == "draft"
    assert service.get_recent_worlds() == []
    assert service.get_world_summary("w1").status == STATUS
    assert not service.is_connected()


def test_null_critic_service_is_safe() -> None:
    service = NullCriticService()
    assert service.analyze_world(CriticRequestDTO()).summary == STATUS
    assert service.get_last_report().summary == STATUS
    assert service.get_heatmaps() == []


def test_null_knowledge_service_is_safe() -> None:
    service = NullKnowledgeService()
    assert service.search(KnowledgeQueryDTO()) == []
    assert service.find_similar("name", "type") == []
    assert isinstance(service.get_metrics(), KnowledgeMetricsDTO)
    assert service.get_metrics().status == STATUS


def test_null_campaign_service_is_safe() -> None:
    service = NullCampaignService()
    assert service.generate_campaign(CampaignRequestDTO(name="c")).status == STATUS
    assert service.get_last_campaign().status == STATUS


def test_null_otbm_service_is_safe() -> None:
    service = NullOTBMService()
    assert service.import_otbm("in.otbm").message == STATUS
    assert service.export_otbm(OTBMExportRequestDTO(output_path="out.otbm")).message == STATUS
    assert service.validate_otbm("in.otbm").message == STATUS


def test_null_autonomous_service_is_safe() -> None:
    service = NullAutonomousService()
    result = service.run_design(AutonomousDesignRequestDTO(world_id="w1"))
    assert isinstance(result, AutonomousResultDTO)
    assert result.summary == STATUS
    assert service.get_iterations() == []
    assert service.get_metrics().status == STATUS


def test_null_dashboard_service_is_safe() -> None:
    service = NullDashboardService()
    assert isinstance(service.load_dashboard(), DashboardDTO)
    assert service.load_dashboard().status == STATUS
    assert service.refresh_dashboard().status == STATUS
