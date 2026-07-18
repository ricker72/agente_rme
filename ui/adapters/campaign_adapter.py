"""Core-backed campaign adapter."""

from __future__ import annotations

import logging
import importlib
from typing import Any, Callable

from ui.adapters._helpers import CORE_EXECUTION_FAILED, CORE_UNAVAILABLE, read_attr, safe_str
from ui.models.campaign_dto import CampaignDTO, CampaignRequestDTO, CampaignStageDTO

logger = logging.getLogger(__name__)
CampaignGenerator: Any | None = None
_IMPORT_ERROR: BaseException | None = None


class CampaignAdapter:
    """Bridge CampaignService calls to the frozen core campaign generator."""

    def __init__(self, generator_factory: Callable[[], Any] | None = None) -> None:
        self._generator_factory = generator_factory
        self._last_campaign = CampaignDTO(status="No campaign", success=False)

    def generate_campaign(self, request: CampaignRequestDTO) -> CampaignDTO:
        generator_class = self._load_generator_class()
        if _IMPORT_ERROR is not None or generator_class is None:
            return self._failure(CORE_UNAVAILABLE, _IMPORT_ERROR)
        try:
            generator = (self._generator_factory or generator_class)()
            campaign = generator.generate(theme=request.objective or request.name or "default")
            self._last_campaign = self._from_core(campaign, request)
            return self._last_campaign
        except Exception as exc:
            logger.exception("Campaign adapter failed to generate campaign: %s", exc)
            self._last_campaign = self._failure(CORE_EXECUTION_FAILED, exc)
            return self._last_campaign

    def get_last_campaign(self) -> CampaignDTO:
        return self._last_campaign

    def _from_core(self, campaign: Any, request: CampaignRequestDTO) -> CampaignDTO:
        side_quests = list(read_attr(campaign, "side_quests", []) or [])
        stages = [
            CampaignStageDTO(
                stage_id=str(index),
                title=str(read_attr(stage, "title", f"Stage {index}")),
                objective=str(read_attr(stage, "objective", "")),
                status="generated",
            )
            for index, stage in enumerate(side_quests, start=1)
        ]
        return CampaignDTO(
            campaign_id=request.name or str(read_attr(campaign, "name", "")),
            name=str(read_attr(campaign, "name", request.name)),
            description=str(read_attr(campaign, "theme", request.objective)),
            stages=stages,
            status="Generated",
            success=True,
        )

    @staticmethod
    def _failure(status: str, error: BaseException | None) -> CampaignDTO:
        message = safe_str(error) if error is not None else status
        return CampaignDTO(status=status, success=False, error_message=message)

    @staticmethod
    def _load_generator_class() -> Any | None:
        global CampaignGenerator, _IMPORT_ERROR
        if CampaignGenerator is not None or _IMPORT_ERROR is not None:
            return CampaignGenerator
        try:
            module = importlib.import_module("core.campaign.campaign_generator")
            CampaignGenerator = getattr(module, "CampaignGenerator")
        except Exception as exc:  # pragma: no cover - import failure path
            _IMPORT_ERROR = exc
            CampaignGenerator = None
        return CampaignGenerator
