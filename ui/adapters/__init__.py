"""Concrete UI adapters that bridge service contracts to frozen core APIs."""

from __future__ import annotations

from ui.adapters.autonomous_adapter import AutonomousAdapter
from ui.adapters.campaign_adapter import CampaignAdapter
from ui.adapters.critic_adapter import CriticAdapter
from ui.adapters.dashboard_adapter import DashboardAdapter
from ui.adapters.knowledge_adapter import KnowledgeAdapter
from ui.adapters.otbm_adapter import OTBMAdapter
from ui.adapters.world_adapter import WorldAdapter

__all__: list[str] = [
    "AutonomousAdapter",
    "CampaignAdapter",
    "CriticAdapter",
    "DashboardAdapter",
    "KnowledgeAdapter",
    "OTBMAdapter",
    "WorldAdapter",
]
