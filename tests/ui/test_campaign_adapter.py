"""Tests for CampaignAdapter."""

from __future__ import annotations

from pytest import MonkeyPatch

from ui.adapters import campaign_adapter
from ui.adapters.campaign_adapter import CampaignAdapter
from ui.models.campaign_dto import CampaignDTO, CampaignRequestDTO


class FakeCampaign:
    name = "Chronicles"
    theme = "Issavi"
    side_quests: list[dict[str, str]] = [{"title": "Start"}]


class FakeCampaignGenerator:
    def generate(self, theme: str = "default") -> FakeCampaign:
        return FakeCampaign()


def test_campaign_adapter_returns_dto() -> None:
    dto = CampaignAdapter(generator_factory=FakeCampaignGenerator).generate_campaign(
        CampaignRequestDTO(name="c1")
    )
    assert isinstance(dto, CampaignDTO)
    assert dto.success is True
    assert dto.stages[0].title == "Start"


def test_campaign_adapter_failure_returns_safe_dto(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(campaign_adapter, "_IMPORT_ERROR", ImportError("campaign missing"))
    monkeypatch.setattr(campaign_adapter, "CampaignGenerator", None)
    dto = CampaignAdapter().generate_campaign(CampaignRequestDTO())
    assert dto.status == "Core unavailable"
    assert dto.success is False
