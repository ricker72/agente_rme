"""
KnowledgeEntry — base unit of the knowledge dataset.

A KnowledgeEntry represents a single catalogued item extracted from a source
map (OTBM, WorldModel, blueprint, campaign, playtest report, critic report).

Each entry has:
  - Stable id (sha-style hash of type+name+source).
  - Source attribution (file path, blueprint name, or campaign id).
  - Free-form attributes (stored in `attributes` dict).
  - Pre-computed text signature for similarity / search.
  - Optional quality / critic / playtest / reuse scores.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class EntryType(str, Enum):
    """Catalogued entity categories."""

    CITY = "city"
    HUNT = "hunt"
    BOSS_ROOM = "boss_room"
    RAID = "raid"
    QUEST = "quest"
    REGION = "region"
    BIOME = "biome"
    SPAWN = "spawn"
    WAYPOINT = "waypoint"
    STRUCTURE = "structure"
    DUNGEON = "dungeon"
    NPC = "npc"


@dataclass
class KnowledgeEntry:
    """
    A catalogued knowledge unit.

    Attributes:
        id: Stable hash id (16 hex chars).
        entry_type: EntryType classification.
        name: Human-readable name (e.g. "Roshamuul", "Soul War Surface").
        source: Source file / blueprint / campaign identifier.
        biome: Biome name if known.
        min_level / max_level: Level range for the entry.
        tags: Free-form tags (e.g. ["desert", "circular_route"]).
        attributes: Arbitrary structured data extracted from the source.
        quality_score: 0..100 quality rating.
        critic_score: 0..100 critic evaluation.
        playtest_score: 0..100 playtest simulation.
        reuse_score: 0..100 how reusable this entry is.
        signature: Pre-tokenized text used for similarity.
    """

    id: str
    entry_type: EntryType
    name: str
    source: str
    biome: str = "generic"
    min_level: int = 1
    max_level: int = 9999
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    critic_score: float = 0.0
    playtest_score: float = 0.0
    reuse_score: float = 0.0
    signature: str = ""

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @staticmethod
    def compute_id(entry_type: EntryType, name: str, source: str) -> str:
        """Stable 16-char id derived from type+name+source."""
        raw = f"{entry_type.value}|{name.lower()}|{source.lower()}".encode("utf-8")
        return hashlib.sha1(raw, usedforsecurity=False).hexdigest()[:16]

    @staticmethod
    def build(
        entry_type: EntryType,
        name: str,
        source: str,
        biome: str = "generic",
        min_level: int = 1,
        max_level: int = 9999,
        tags: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> "KnowledgeEntry":
        """Convenience builder that computes id and signature."""
        eid = KnowledgeEntry.compute_id(entry_type, name, source)
        attrs = dict(attributes or {})
        sig = KnowledgeEntry._build_signature(
            entry_type=entry_type,
            name=name,
            biome=biome,
            min_level=min_level,
            max_level=max_level,
            tags=tags or [],
            attributes=attrs,
        )
        return KnowledgeEntry(
            id=eid,
            entry_type=entry_type,
            name=name,
            source=source,
            biome=biome,
            min_level=min_level,
            max_level=max_level,
            tags=list(tags or []),
            attributes=attrs,
            signature=sig,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["entry_type"] = self.entry_type.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntry":
        et = data.get("entry_type", "hunt")
        if isinstance(et, str):
            try:
                et = EntryType(et)
            except ValueError:
                # Unknown type — fall back to hunt.
                et = EntryType.HUNT
        return cls(
            id=data.get("id", ""),
            entry_type=et,
            name=data.get("name", ""),
            source=data.get("source", ""),
            biome=data.get("biome", "generic"),
            min_level=int(data.get("min_level", 1)),
            max_level=int(data.get("max_level", 9999)),
            tags=list(data.get("tags", []) or []),
            attributes=dict(data.get("attributes", {}) or {}),
            quality_score=float(data.get("quality_score", 0.0)),
            critic_score=float(data.get("critic_score", 0.0)),
            playtest_score=float(data.get("playtest_score", 0.0)),
            reuse_score=float(data.get("reuse_score", 0.0)),
            signature=data.get("signature", ""),
        )

    # ------------------------------------------------------------------
    # Signature
    # ------------------------------------------------------------------

    @staticmethod
    def _build_signature(
        entry_type: EntryType,
        name: str,
        biome: str,
        min_level: int,
        max_level: int,
        tags: List[str],
        attributes: Dict[str, Any],
    ) -> str:
        """Create a token signature used by similarity / search."""
        tokens: List[str] = [
            entry_type.value,
            name.lower().replace(" ", "_"),
            biome.lower().replace(" ", "_"),
            f"level_{_bucket_level(min_level, max_level)}",
        ]
        for t in tags:
            tokens.append(str(t).lower().replace(" ", "_"))
        # Pull useful categorical attributes
        for key in (
            "theme",
            "shape",
            "route",
            "arena_type",
            "layout",
            "difficulty",
            "size",
            "circular",
            "monster",
            "style",
        ):
            v = attributes.get(key)
            if v is not None:
                tokens.append(f"{key}_{str(v).lower().replace(' ', '_')}")
        # Monster list (capped) for hunt entries
        monsters = attributes.get("monsters") or []
        if isinstance(monsters, list):
            for m in monsters[:5]:
                tokens.append(f"monster_{str(m).lower().replace(' ', '_')}")
        # De-dup while preserving order
        seen: set = set()
        unique: List[str] = []
        for t in tokens:
            if t and t not in seen:
                seen.add(t)
                unique.append(t)
        return " ".join(unique)


def _bucket_level(min_level: int, max_level: int) -> str:
    """Bucket a level range into a discrete tag used by the signature."""
    if min_level >= 600 or max_level >= 600:
        return "600+"
    if min_level >= 400 or max_level >= 400:
        return "400_600"
    if min_level >= 250 or max_level >= 250:
        return "250_400"
    if min_level >= 150 or max_level >= 150:
        return "150_250"
    if min_level >= 80 or max_level >= 80:
        return "80_150"
    return "1_80"
