"""
core.campaign — Campaign generation pipeline.

Public API:
    Campaign           — main campaign data object
    CampaignGenerator  — orchestrator for lore/story/npc/faction/etc.
    CampaignPackage    — mandatory wrapper guaranteed to never be None
    CampaignValidator  — validates CampaignPackage structure
    LoreEntry, LoreGenerator
    StoryArc, StoryGenerator
    NPC, NPCGenerator
    Faction, FactionGenerator
    DialogGenerator, DialogLine
    EconomyGenerator, EconomyData

Hito 26.1C update: the ``CampaignPackage`` wrapper + ``CampaignValidator``
guarantee ``campaign.json`` is always written with the required keys
(``quests``, ``bosses``, ``raids``, ``story``, ``rewards``).
"""

from __future__ import annotations

from .campaign_generator import Campaign, CampaignGenerator
from .dialog_generator import DialogGenerator, DialogLine
from .economy_generator import EconomyData, EconomyGenerator
from .faction_generator import Faction, FactionGenerator
from .lore_generator import LoreEntry, LoreGenerator
from .npc_generator import NPC, NPCGenerator
from .package import CampaignPackage, PackageStatus, REQUIRED_KEYS
from .story_generator import StoryArc, StoryGenerator
from .validator import CampaignValidator, ValidationIssue, ValidationResult, Severity

__all__ = [
    # Original
    "Campaign",
    "CampaignGenerator",
    "LoreEntry",
    "LoreGenerator",
    "NPC",
    "NPCGenerator",
    "Faction",
    "FactionGenerator",
    "StoryArc",
    "StoryGenerator",
    "DialogGenerator",
    "DialogLine",
    "EconomyGenerator",
    "EconomyData",
    # Hito 26.1C additions
    "CampaignPackage",
    "CampaignValidator",
    "PackageStatus",
    "ValidationIssue",
    "ValidationResult",
    "Severity",
    "REQUIRED_KEYS",
]
