from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.campaign.lore_generator import LoreGenerator
from core.campaign.npc_generator import NPCGenerator
from core.campaign.faction_generator import FactionGenerator, Faction
from core.campaign.story_generator import StoryGenerator
from core.campaign.dialog_generator import DialogGenerator
from core.campaign.economy_generator import EconomyGenerator

logger = logging.getLogger(__name__)


@dataclass
class Campaign:
    """A complete MMORPG campaign."""

    theme: str = ""
    name: str = ""
    level_range: tuple = (1, 100)
    lore: List[Dict[str, Any]] = field(default_factory=list)
    factions: List[Dict[str, Any]] = field(default_factory=list)
    npcs: List[Dict[str, Any]] = field(default_factory=list)
    main_story: Optional[Dict[str, Any]] = None
    side_quests: List[Dict[str, Any]] = field(default_factory=list)
    economy: Optional[Dict[str, Any]] = None
    dialogs: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    raids: List[Dict[str, Any]] = field(default_factory=list)
    bosses: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme": self.theme,
            "name": self.name,
            "level_range": list(self.level_range),
            "lore": self.lore,
            "factions": self.factions,
            "npcs": self.npcs,
            "main_story": self.main_story,
            "side_quests": self.side_quests,
            "economy": self.economy,
            "dialogs": self.dialogs,
            "raids": self.raids,
            "bosses": self.bosses,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class CampaignGenerator:
    """
    Master orchestrator for MMORPG campaign generation.

    Integrates:
      - LoreGenerator → world backstory
      - FactionGenerator → factions and relationships
      - NPCGenerator → characters with roles
      - StoryGenerator → quest arcs and main story
      - DialogGenerator → NPC conversations
      - EconomyGenerator → pricing and trade

    Usage:
        generator = CampaignGenerator()
        campaign = generator.generate(theme="Issavi", level_range=(300, 500))
        assert campaign.main_story is not None
    """

    def __init__(self, seed: int = 42):
        self._seed = seed
        self._lore_gen = LoreGenerator(seed)
        self._npc_gen = NPCGenerator(seed)
        self._faction_gen = FactionGenerator(seed)
        self._story_gen = StoryGenerator(seed)
        self._dialog_gen = DialogGenerator(seed)
        self._economy_gen = EconomyGenerator(seed)

    def generate(
        self,
        theme: str = "default",
        level_range: tuple = (1, 100),
        npc_count: int = 8,
        faction_count: int = 3,
    ) -> Campaign:
        """
        Generate a complete MMORPG campaign.

        Args:
            theme: Campaign theme (e.g. "Issavi", "Darashia").
            level_range: (min_level, max_level).
            npc_count: Number of NPCs to generate.
            faction_count: Number of factions.

        Returns:
            Complete Campaign object.

        Hito 26.1C contract: never returns ``None`` and never raises
        for bad input — falls back to a minimal Campaign instead.
        """
        # Normalize inputs safely
        key = (str(theme) if theme is not None else "default") or "default"
        if isinstance(level_range, (list, tuple)) and len(level_range) == 2:
            try:
                lo = int(level_range[0])
                hi = int(level_range[1])
                if lo > hi:
                    lo, hi = hi, lo
            except (TypeError, ValueError):
                lo, hi = 1, 200
        else:
            lo, hi = 1, 200
        try:
            npc_count = max(0, int(npc_count))
        except (TypeError, ValueError):
            npc_count = 8
        try:
            faction_count = max(0, int(faction_count))
        except (TypeError, ValueError):
            faction_count = 3

        try:
            return self._generate(key, (lo, hi), npc_count, faction_count)
        except Exception as exc:  # pragma: no cover — defensive
            logger.exception(
                "CampaignGenerator.generate failed; returning minimal fallback: %s",
                exc,
            )
            return self._minimal_campaign(theme=key, lo=lo, hi=hi, error=str(exc))

    def _generate(
        self,
        theme: str,
        level_range: tuple,
        npc_count: int,
        faction_count: int,
    ) -> Campaign:
        campaign = Campaign(
            theme=theme,
            name=f"The Chronicles of {theme}",
            level_range=level_range,
        )

        # Step 1: Generate factions
        factions = self._faction_gen.generate(theme, count=faction_count)
        campaign.factions = [f.to_dict() for f in factions]
        faction_names = [f.name for f in factions]

        # Step 2: Generate lore
        lore_entries = self._lore_gen.generate(
            theme, faction_names=faction_names, count=5
        )
        # Add prophecy
        prophecy = self._lore_gen.generate_prophecy(theme, faction_names[:2])
        lore_entries.append(prophecy)
        campaign.lore = [entry.to_dict() for entry in lore_entries]

        # Step 3: Generate NPCs
        locations = self._generate_locations(theme, factions)
        npcs = self._npc_gen.generate(
            theme, faction_names=faction_names, count=npc_count, locations=locations
        )
        campaign.npcs = [n.to_dict() for n in npcs]

        # Step 4: Generate story arcs
        story_arcs = self._story_gen.generate(theme, level_range)
        main_arcs = [a for a in story_arcs if a.is_main_story]
        side_arcs = [a for a in story_arcs if not a.is_main_story]

        if main_arcs:
            campaign.main_story = {
                "title": f"Main Campaign - {theme}",
                "chapters": [a.to_dict() for a in main_arcs],
            }
        campaign.side_quests = [a.to_dict() for a in side_arcs]

        # Step 5: Generate economy
        economy = self._economy_gen.generate(theme, level_range)
        campaign.economy = economy.to_dict()

        # Step 6: Generate dialogs
        for npc in npcs:
            dialog_lines = self._dialog_gen.generate(npc.name, npc.role)
            campaign.dialogs[npc.name] = [d.to_dict() for d in dialog_lines]

        # Step 7: Generate boss encounters from story
        bosses = [a.boss_name for a in story_arcs if a.boss_name]
        campaign.bosses = [
            {
                "name": b,
                "level": level_range[1],
                "theme": theme,
                "is_campaign_boss": True,
            }
            for b in bosses
        ]

        # Step 8: Generate raids
        campaign.raids = self._generate_raids(theme, level_range, bosses)

        return campaign

    def _generate_locations(self, theme: str, factions: List[Faction]) -> List[str]:
        """Generate location names based on theme and factions."""
        base_locations = [
            f"{theme} Town Center",
            f"{theme} Market",
            f"{theme} Temple",
            f"{theme} Outskirts",
        ]
        for faction in factions:
            base_locations.append(f"{faction.capital}")
        return base_locations

    def _generate_raids(
        self, theme: str, level_range: tuple, boss_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate raid encounters."""
        raids: List[Dict[str, Any]] = []
        for i, boss in enumerate(boss_names[:3]):
            raids.append(
                {
                    "name": f"Raid: {boss}",
                    "type": "raid",
                    "level_required": level_range[0]
                    + (level_range[1] - level_range[0]) * i // 3,
                    "boss": boss,
                    "max_players": 5 if i < 2 else 8,
                    "rewards": {
                        "gold": 50000 * (i + 1),
                        "items": [f"{theme} Raid Token {i + 1}"],
                    },
                }
            )
        return raids

    def save(self, campaign: Campaign, path: str) -> None:
        """Save campaign to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(campaign.to_json())

    def load(self, path: str) -> Campaign:
        """Load a campaign from a JSON file.

        Hito 26.1C contract: never raises — returns a minimal
        ``Campaign`` when the file is missing, unreadable or corrupt.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("Could not load campaign from %s: %s", path, exc)
            return self._minimal_campaign(theme="default", lo=1, hi=200, error=str(exc))
        try:
            return Campaign(
                theme=data.get("theme", ""),
                name=data.get("name", ""),
                level_range=tuple(data.get("level_range", [1, 100])),
                lore=data.get("lore", []),
                factions=data.get("factions", []),
                npcs=data.get("npcs", []),
                main_story=data.get("main_story"),
                side_quests=data.get("side_quests", []),
                economy=data.get("economy"),
                dialogs=data.get("dialogs", {}),
                raids=data.get("raids", []),
                bosses=data.get("bosses", []),
            )
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("Malformed campaign JSON: %s", exc)
            return self._minimal_campaign(theme="default", lo=1, hi=200, error=str(exc))

    def _minimal_campaign(
        self, theme: str = "default", lo: int = 1, hi: int = 200, error: str = ""
    ) -> Campaign:
        """Last-resort minimal campaign — never None."""
        return Campaign(
            theme=theme,
            name=f"Minimal Campaign ({theme})",
            level_range=(lo, hi),
            lore=[],
            factions=[],
            npcs=[],
            main_story=None,
            side_quests=[],
            economy=None,
            dialogs={},
            raids=[],
            bosses=[],
        )
