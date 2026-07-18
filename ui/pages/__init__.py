"""
Workspace pages for Agente RME Studio.

Each page occupies the main workspace area and provides a specific
function (e.g. world editor, critic dashboard, knowledge browser).

Pages are registered via the PageRegistry and lazy-loaded on first
navigation.
"""

from __future__ import annotations


from .campaign_page import CampaignPage
from .architect_page import ArchitectPage
from .critic_page import CriticPage
from .dashboard_page import DashboardPage
from .knowledge_page import KnowledgePage
from .otbm_page import OTBMPage
from .settings_page import SettingsPage
from .world_page import WorldPage

__all__: list[str] = [
    "DashboardPage",
    "WorldPage",
    "ArchitectPage",
    "CriticPage",
    "KnowledgePage",
    "CampaignPage",
    "OTBMPage",
    "SettingsPage",
]
