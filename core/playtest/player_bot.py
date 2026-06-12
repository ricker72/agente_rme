"""
Player Bot — Simulates individual player characters across all vocations.

Models: Knight, Paladin, Druid, Sorcerer, Monk
Each bot carries stats, equipment coefficients, healing/damage logic,
and can be run through a simulated hunting session.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Vocations
# ---------------------------------------------------------------------------


class Vocation(Enum):
    KNIGHT = auto()
    PALADIN = auto()
    DRUID = auto()
    SORCERER = auto()
    MONK = auto()

    def __str__(self) -> str:
        return self.name.capitalize()


# ---------------------------------------------------------------------------
# Base Stats per Vocation at level L
# ---------------------------------------------------------------------------


@dataclass
class VocationStats:
    """Stat block describing a vocation at a given level."""

    level: int
    max_hp: int
    max_mp: int
    capacity: int
    base_damage: int  # average auto-attack damage per turn
    healing_per_turn: int  # self-sustain hp/turn
    magic_damage: int  # average spell/area damage per turn
    armor: int
    attack_speed: float  # attacks per second (approx)

    def effective_hp(self) -> float:
        """HP after armor mitigation for an incoming hit of `raw_dmg`."""
        mitigation = self.armor / (self.armor + 100.0)  # simple armor formula
        return self.max_hp / (1.0 - mitigation) if mitigation < 1.0 else float("inf")


# ---------------------------------------------------------------------------
# Level-scaling formulas (Tibia-inspired, simplified)
# ---------------------------------------------------------------------------


def _scale_stats(vocation: Vocation, level: int) -> VocationStats:
    """Return a VocationStats for the given vocation at `level`."""
    lvl = max(1, level)

    base = {
        Vocation.KNIGHT: (185, 90, 470, 25, 15, 0, 35, 1.0),
        Vocation.PALADIN: (155, 130, 310, 35, 20, 15, 25, 1.2),
        Vocation.DRUID: (105, 210, 230, 0, 30, 55, 15, 1.0),
        Vocation.SORCERER: (85, 240, 210, 0, 25, 75, 12, 1.0),
        Vocation.MONK: (150, 150, 290, 30, 22, 20, 28, 1.1),
    }[vocation]

    (
        hp_per_lv,
        mp_per_lv,
        cap_per_lv,
        atk_per_lv,
        heal_per_lv,
        magic_per_lv,
        arm_per_lv,
        atk_spd,
    ) = base

    hp_scale = 5
    mp_scale = 10
    cap_scale = 10
    atk_scale = 0.5
    heal_scale = 0.4
    magic_scale = 1.0
    arm_scale = 0.3

    return VocationStats(
        level=lvl,
        max_hp=int(hp_per_lv + hp_scale * lvl),
        max_mp=int(mp_per_lv + mp_scale * lvl),
        capacity=int(cap_per_lv + cap_scale * lvl),
        base_damage=int(atk_per_lv + atk_scale * lvl),
        healing_per_turn=int(heal_per_lv + heal_scale * lvl),
        magic_damage=int(magic_per_lv + magic_scale * lvl),
        armor=int(arm_per_lv + arm_scale * lvl),
        attack_speed=atk_spd,
    )


# ---------------------------------------------------------------------------
# PlayerBot
# ---------------------------------------------------------------------------


@dataclass
class PlayerBot:
    """
    Simulated player character.

    Holds current HP/MP, cooldowns, and exposes a step() method
    that processes one combat turn (≈2 seconds in Tibia).
    """

    name: str
    vocation: Vocation
    level: int
    equipment_coefficient: float = 1.0  # multiplies base damage & healing

    # Derived
    stats: VocationStats = field(init=False)

    # Runtime state
    current_hp: int = field(init=False)
    current_mp: int = field(init=False)
    alive: bool = field(init=False, default=True)

    # Cooldowns (in turns)
    _heal_cooldown: int = field(init=False, default=0)
    _spell_cooldown: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.stats = _scale_stats(self.vocation, self.level)
        self.current_hp = self.stats.max_hp
        self.current_mp = self.stats.max_mp

    # ------------------------------------------------------------------
    # Turn processing
    # ------------------------------------------------------------------

    def step(self, enemy_damage_incoming: int) -> int:
        """
        Process one combat turn.

        Returns damage dealt to enemy this turn.
        If the bot dies during this turn, sets alive=False and returns 0.
        """
        if not self.alive:
            return 0

        # --- incoming damage ---
        mitigated = max(0, enemy_damage_incoming - int(self.stats.armor * 0.3))
        self.current_hp -= mitigated

        if self.current_hp <= 0:
            self.current_hp = 0
            self.alive = False
            return 0

        # --- outgoing damage ---
        damage = self._auto_attack_damage() + self._spell_damage()

        # --- healing ---
        self._try_heal()

        # --- tick cooldowns ---
        self._heal_cooldown = max(0, self._heal_cooldown - 1)
        self._spell_cooldown = max(0, self._spell_cooldown - 1)

        return int(damage)

    def _auto_attack_damage(self) -> float:
        base = self.stats.base_damage * self.equipment_coefficient
        variance = random.uniform(0.85, 1.15)
        return base * variance * self.stats.attack_speed

    def _spell_damage(self) -> float:
        if self._spell_cooldown > 0:
            return 0.0
        if self.stats.magic_damage <= 0:
            return 0.0

        # Mages cast every 2 turns; paladins/monks every 3; knights cast rarely
        cd_map = {
            Vocation.KNIGHT: 6,
            Vocation.PALADIN: 3,
            Vocation.DRUID: 2,
            Vocation.SORCERER: 2,
            Vocation.MONK: 3,
        }
        self._spell_cooldown = cd_map[self.vocation]

        mana_cost = int(self.stats.magic_damage * 0.6)
        if self.current_mp < mana_cost:
            return 0.0

        self.current_mp -= mana_cost
        variance = random.uniform(0.8, 1.2)
        return self.stats.magic_damage * self.equipment_coefficient * variance

    def _try_heal(self) -> None:
        if self._heal_cooldown > 0:
            return
        heal = self.stats.healing_per_turn * self.equipment_coefficient
        if heal <= 0:
            return

        # Heal when below 70% HP (mages heal more aggressively at 60%)
        threshold = (
            0.60 if self.vocation in (Vocation.DRUID, Vocation.SORCERER) else 0.70
        )
        if self.current_hp / self.stats.max_hp < threshold:
            self.current_hp = min(self.stats.max_hp, int(self.current_hp + heal))
            self._heal_cooldown = 2

    # ------------------------------------------------------------------
    # Party buffs
    # ------------------------------------------------------------------

    def apply_party_buff(self, buff_multiplier: float) -> None:
        """Shared-experience or shared-boost multiplier (1.0 = no change)."""
        self.equipment_coefficient = min(
            2.0, self.equipment_coefficient * buff_multiplier
        )

    def reset(self) -> None:
        """Reset bot to full health for a new simulation run."""
        self.stats = _scale_stats(self.vocation, self.level)
        self.current_hp = self.stats.max_hp
        self.current_mp = self.stats.max_mp
        self.alive = True
        self._heal_cooldown = 0
        self._spell_cooldown = 0
        self.equipment_coefficient = 1.0

    def clone(self, name: Optional[str] = None) -> PlayerBot:
        """Return an independent copy with the same base parameters."""
        c = PlayerBot(
            name=name or self.name,
            vocation=self.vocation,
            level=self.level,
            equipment_coefficient=self.equipment_coefficient,
        )
        c.stats = self.stats
        c.current_hp = self.current_hp
        c.current_mp = self.current_mp
        c.alive = self.alive
        return c

    def summary(self) -> Dict:
        return {
            "name": self.name,
            "vocation": str(self.vocation),
            "level": self.level,
            "hp": f"{self.current_hp}/{self.stats.max_hp}",
            "mp": f"{self.current_mp}/{self.stats.max_mp}",
            "alive": self.alive,
            "dps": round(self._auto_attack_damage() + (self.stats.magic_damage / 2), 1),
        }
