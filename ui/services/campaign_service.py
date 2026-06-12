"""Campaign service contract."""

from __future__ import annotations

from typing import Protocol

from ui.models.campaign_dto import CampaignDTO, CampaignRequestDTO


class CampaignService(Protocol):
    """Contract between UI pages and future campaign adapters."""

    def generate_campaign(self, request: CampaignRequestDTO) -> CampaignDTO:
        """Generate a campaign from a typed request."""
        ...

    def get_last_campaign(self) -> CampaignDTO:
        """Return the most recently generated campaign."""
        ...
