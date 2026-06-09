"""
HITO 15 — AI Architect: Difficulty Planner
==========================================

Plans difficulty PROGRESSION across a sequence of zones.

A single zone has its own difficulty band, but a world has many zones and
they should escalate smoothly: warmup hunts → mid hunts → elite hunts → boss.

The DifficultyPlanner takes:
    - A target level range (e.g. 300-500 from the prompt)
    - A list of zone kinds (e.g. ["hunt", "hunt", "hunt", "boss"])

And returns a per-zone level window so the world has a smooth ramp:

    hunt_1: 300-360
    hunt_2: 340-420
    hunt_3: 380-460
    boss:   420-500

Architecture:
    Prompt level range + zone count
        ↓
    DifficultyPlanner.plan_progression(...)
        ↓
    List[ZoneDifficulty]
        ├── zone_kind: str
        ├── level_min: int
        ├── level_max: int
        ├── band: str   ("easy" | "medium" | ... | "legendary")
        ├── spawn_density: str  ("low" | "medium" | "high" | "extreme")
        └── monster_subset: List[str]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Difficulty curve definitions
# =============================================================================

# How spawn density should ramp across zones
DENSITY_CURVE: Dict[str, str] = {
    "easy": "low",
    "medium": "medium",
    "hard": "medium",
    "extreme": "high",
    "epic": "high",
    "legendary": "extreme",
}


# =============================================================================
# ZoneDifficulty — one window in a multi-zone progression
# =============================================================================

@dataclass
class ZoneDifficulty:
    """
    A single difficulty window assigned to a zone.

    Used to drive spawn density, monster selection, and reward scaling.
    """
    zone_index: int
    zone_kind: str                # "city" | "dungeon" | "hunt" | "boss" | "quest"
    level_min: int
    level_max: int
    band: str                     # "easy" | "medium" | ... | "legendary"
    rank: int                     # 1..6
    spawn_density: str            # "low" | "medium" | "high" | "extreme"
    monster_pool: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_index": self.zone_index,
            "zone_kind": self.zone_kind,
            "level_min": self.level_min,
            "level_max": self.level_max,
            "band": self.band,
            "rank": self.rank,
            "spawn_density": self.spawn_density,
            "monster_pool": self.monster_pool,
            "notes": self.notes,
        }


# =============================================================================
# Internal band table (mirrors ZonePlanner but kept independent to avoid
# a circular import).
# =============================================================================

_BANDS: List[Dict[str, Any]] = [
    {"label": "easy",       "min": 1,   "max": 50,   "rank": 1},
    {"label": "medium",     "min": 50,  "max": 100,  "rank": 2},
    {"label": "hard",       "min": 100, "max": 200,  "rank": 3},
    {"label": "extreme",    "min": 200, "max": 300,  "rank": 4},
    {"label": "epic",       "min": 300, "max": 500,  "rank": 5},
    {"label": "legendary",  "min": 500, "max": 9999, "rank": 6},
]


# =============================================================================
# DifficultyPlanner
# =============================================================================

class DifficultyPlanner:
    """
    Plans difficulty progression for an ordered list of zones.

    The planner knows:
        - How to split a level range into N sub-windows with overlap
        - How to map sub-windows to difficulty bands
        - How to choose a monster subset that matches the window

    The progression can be:
        - linear: even split, no overlap
        - stepped: hard cliff between zones (good for distinct hunt tiers)
        - smooth: 30% overlap, feels continuous (default for hunt ramps)
        - spike:  boss is much harder than the last hunt

    Usage:
        planner = DifficultyPlanner()
        plan = planner.plan_progression(
            zone_kinds=["hunt", "hunt", "hunt", "boss"],
            level_min=300, level_max=500,
            theme_monsters=["Frazzlemaw", "Sphinx", "Cloak Of Terror", "Vexclaw"],
            style="smooth",
        )
        for zone in plan:
            print(zone.zone_kind, zone.level_min, zone.level_max, zone.band)
    """

    SUPPORTED_STYLES = ("linear", "stepped", "smooth", "spike")

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan_progression(
        self,
        zone_kinds: List[str],
        level_min: int,
        level_max: int,
        theme_monsters: Optional[List[str]] = None,
        style: str = "smooth",
    ) -> List[ZoneDifficulty]:
        """
        Build a per-zone difficulty progression.

        Args:
            zone_kinds: Ordered list of zone kinds
                        (e.g. ["city", "hunt", "hunt", "hunt", "boss"]).
            level_min:  Low end of the requested level range.
            level_max:  High end of the requested level range.
            theme_monsters: Optional list of monster names to slice into
                            the per-zone monster pool.
            style: Progression shape. One of "linear" | "stepped" |
                   "smooth" | "spike".

        Returns:
            List of ZoneDifficulty, one per input zone, in the same order.
        """
        if not zone_kinds:
            return []
        if level_min > level_max:
            level_min, level_max = level_max, level_min
        style = style if style in self.SUPPORTED_STYLES else "smooth"

        # Compute each zone's level window
        windows = self._compute_windows(
            zone_kinds, level_min, level_max, style,
        )

        # For "spike" style, push the boss's level well above the rest
        if style == "spike" and windows and "boss" in zone_kinds:
            windows = self._apply_spike(windows, zone_kinds, level_max)

        result: List[ZoneDifficulty] = []
        monsters = list(theme_monsters) if theme_monsters else []
        for idx, (kind, (lo, hi)) in enumerate(zip(zone_kinds, windows)):
            band = self._classify(lo, hi)
            rank = self._rank(band)
            density = DENSITY_CURVE.get(band, "medium")
            pool = self._slice_monster_pool(monsters, idx, len(zone_kinds))
            notes = self._notes_for(kind, band, style)
            result.append(ZoneDifficulty(
                zone_index=idx,
                zone_kind=kind,
                level_min=lo,
                level_max=hi,
                band=band,
                rank=rank,
                spawn_density=density,
                monster_pool=pool,
                notes=notes,
            ))

        return result

    def plan_single(
        self,
        zone_kind: str,
        level_min: int,
        level_max: int,
        theme_monsters: Optional[List[str]] = None,
    ) -> ZoneDifficulty:
        """Plan a single zone's difficulty (convenience helper)."""
        zones = self.plan_progression(
            [zone_kind], level_min, level_max, theme_monsters, style="linear",
        )
        return zones[0]

    def recommend_style(self, zone_kinds: List[str]) -> str:
        """
        Recommend a progression style based on the zone kinds.

        - Single zone: "linear"
        - Last zone is boss: "spike"
        - All same kind (multiple hunts): "smooth"
        - Mixed city/hunt/dungeon: "stepped"
        """
        if len(zone_kinds) <= 1:
            return "linear"
        if zone_kinds[-1] == "boss":
            return "spike"
        if len(set(zone_kinds)) == 1 and zone_kinds[0] in ("hunt", "dungeon"):
            return "smooth"
        return "stepped"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_windows(
        self,
        zone_kinds: List[str],
        level_min: int,
        level_max: int,
        style: str,
    ) -> List[Tuple[int, int]]:
        """Compute (level_min, level_max) for each zone."""
        n = len(zone_kinds)
        span = level_max - level_min
        if span <= 0:
            return [(level_min, level_max)] * n

        if style == "linear":
            # Even split, no overlap
            step = span / n
            return [
                (
                    int(level_min + i * step),
                    int(level_min + (i + 1) * step),
                )
                for i in range(n)
            ]
        elif style == "stepped":
            # Same as linear but with hard breaks (no overlap)
            return self._compute_windows(zone_kinds, level_min, level_max, "linear")
        elif style == "spike":
            # Last zone gets a bigger share
            if n == 1:
                return [(level_min, level_max)]
            main_share = span * 0.7
            main_step = main_share / (n - 1)
            windows: List[Tuple[int, int]] = []
            for i in range(n - 1):
                windows.append((
                    int(level_min + i * main_step),
                    int(level_min + (i + 1) * main_step),
                ))
            # Boss zone covers the rest
            windows.append((windows[-1][1] if windows else level_min, level_max))
            return windows
        else:  # smooth
            # Overlapping windows: each zone covers ~30% more than its share
            step = span / n
            overlap = step * 0.3
            windows = []
            for i in range(n):
                lo = int(max(level_min, level_min + i * step - overlap))
                hi = int(min(level_max, level_min + (i + 1) * step + overlap))
                windows.append((lo, hi))
            return windows

    def _apply_spike(
        self,
        windows: List[Tuple[int, int]],
        zone_kinds: List[str],
        level_max: int,
    ) -> List[Tuple[int, int]]:
        """Push the boss zone beyond the level_max (creates a hard cliff)."""
        result = list(windows)
        boss_indices = [i for i, k in enumerate(zone_kinds) if k == "boss"]
        if not boss_indices:
            return result
        for bi in boss_indices:
            prev_hi = windows[bi - 1][1] if bi > 0 else windows[bi][0]
            new_lo = max(prev_hi, windows[bi][0])
            new_hi = max(level_max, new_lo + 20)
            result[bi] = (new_lo, new_hi)
        return result

    def _classify(self, lo: int, hi: int) -> str:
        mid = (lo + hi) // 2
        for band in _BANDS:
            if band["min"] <= mid <= band["max"]:
                return band["label"]
        if mid < _BANDS[0]["min"]:
            return _BANDS[0]["label"]
        return _BANDS[-1]["label"]

    def _rank(self, label: str) -> int:
        for band in _BANDS:
            if band["label"] == label:
                return band["rank"]
        return 2

    def _slice_monster_pool(
        self,
        monsters: List[str],
        zone_index: int,
        total_zones: int,
    ) -> List[str]:
        """
        Pick a subset of the theme monsters for this specific zone.

        Strategy:
            - If the pool is small, return it whole
            - Otherwise, rotate through it so each zone gets unique
              monsters (avoiding repetition across the progression)
        """
        if not monsters:
            return []
        if len(monsters) <= 2:
            return list(monsters)
        if total_zones <= 1:
            return list(monsters)

        # Pick a contiguous slice for this zone
        per_zone = max(1, len(monsters) // total_zones)
        start = (zone_index * per_zone) % len(monsters)
        end = start + per_zone
        if end <= len(monsters):
            return monsters[start:end]
        # Wrap around if we exceeded the pool
        return monsters[start:] + monsters[: end - len(monsters)]

    def _notes_for(self, kind: str, band: str, style: str) -> List[str]:
        notes: List[str] = []
        if kind == "boss":
            notes.append(f"Final encounter — band={band} with boss mechanics")
        if kind == "hunt" and band in ("epic", "legendary"):
            notes.append("High-tier hunt; ensure escape routes and safe spots")
        if kind == "city":
            notes.append("Safe zone — low monster density")
        if kind == "dungeon" and style == "spike":
            notes.append("Dungeon feeds into boss; pace rooms accordingly")
        if style == "smooth" and kind == "hunt":
            notes.append("Smooth overlap with neighboring hunts for natural flow")
        return notes
