"""
Party Bot — Simulates a party of player bots hunting together.

Handles party formation, role assignment, shared experience,
and cooperative combat dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

from .player_bot import PlayerBot, Vocation, VocationStats


# ---------------------------------------------------------------------------
# Party Roles
# ---------------------------------------------------------------------------

class PartyRole(Enum):
    TANK = auto()
    DAMAGE = auto()
    HEALER = auto()
    SUPPORT = auto()

    def __str__(self) -> str:
        return self.name.capitalize()


# Role assignment map
_ROLE_ASSIGN: Dict[Vocation, PartyRole] = {
    Vocation.KNIGHT:   PartyRole.TANK,
    Vocation.PALADIN:  PartyRole.DAMAGE,
    Vocation.DRUID:    PartyRole.HEALER,
    Vocation.SORCERER: PartyRole.DAMAGE,
    Vocation.MONK:     PartyRole.SUPPORT,
}


# ---------------------------------------------------------------------------
# Party Composition Templates
# ---------------------------------------------------------------------------

PARTY_TEMPLATES: Dict[str, List[Vocation]] = {
    "classic_4":  [Vocation.KNIGHT, Vocation.PALADIN, Vocation.DRUID, Vocation.SORCERER],
    "double_mage": [Vocation.KNIGHT, Vocation.DRUID, Vocation.SORCERER, Vocation.SORCERER],
    "monk_hybrid": [Vocation.KNIGHT, Vocation.DRUID, Vocation.MONK, Vocation.SORCERER],
    "duo_ek_ed":  [Vocation.KNIGHT, Vocation.DRUID],
    "duo_rp_ed":  [Vocation.PALADIN, Vocation.DRUID],
    "duo_ms_ed":  [Vocation.SORCERER, Vocation.DRUID],
    "solo":       [],  # filled dynamically
    "trio":       [Vocation.KNIGHT, Vocation.DRUID, Vocation.SORCERER],
}


# ---------------------------------------------------------------------------
# PartyBot
# ---------------------------------------------------------------------------

@dataclass
class PartyBot:
    """
    Manages a group of PlayerBot instances working together.

    Tracks aggro redistribution, healing assignment, and damage
    amplification from party buffs.
    """
    name: str
    members: List[PlayerBot] = field(default_factory=list)
    party_buff: float = 1.0  # flat multiplier applied during combat

    # Internal
    _aggro_table: Dict[str, int] = field(default_factory=dict)

    def add_member(self, bot: PlayerBot) -> None:
        """Add a bot to the party."""
        self.members.append(bot)
        self._aggro_table[bot.name] = 0

    @classmethod
    def from_template(
        cls,
        name: str,
        template: str,
        levels: Optional[List[int]] = None,
    ) -> PartyBot:
        """
        Build a party from a named template.

        If template is 'solo', returns an empty PartyBot (caller adds members).
        """
        vocs = PARTY_TEMPLATES.get(template, PARTY_TEMPLATES["classic_4"])
        if template == "solo":
            return cls(name=name)

        levels = levels or [150] * len(vocs)
        if len(levels) != len(vocs):
            levels = [levels[0]] * len(vocs) if levels else [150] * len(vocs)

        party = cls(name=name)
        for i, voc in enumerate(vocs):
            lvl = levels[i] if i < len(levels) else levels[-1]
            bot = PlayerBot(name=f"{name}_{voc}_{i+1}", vocation=voc, level=lvl)
            party.add_member(bot)

        return party

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def alive_members(self) -> List[PlayerBot]:
        return [m for m in self.members if m.alive]

    @property
    def all_dead(self) -> bool:
        return len(self.alive_members) == 0

    @property
    def tank(self) -> Optional[PlayerBot]:
        for m in self.members:
            if _ROLE_ASSIGN.get(m.vocation) == PartyRole.TANK and m.alive:
                return m
        # fallback: highest HP
        alive = self.alive_members
        if not alive:
            return None
        return max(alive, key=lambda b: b.current_hp)

    @property
    def healer(self) -> Optional[PlayerBot]:
        for m in self.members:
            if _ROLE_ASSIGN.get(m.vocation) == PartyRole.HEALER and m.alive:
                return m
        return None

    @property
    def total_dps(self) -> float:
        return sum(
            m._auto_attack_damage() + (m.stats.magic_damage / 2)
            for m in self.alive_members
        )

    # ------------------------------------------------------------------
    # Turn processing
    # ------------------------------------------------------------------

    def step(self, total_enemy_damage: int) -> List[int]:
        """
        Process one combat turn for the entire party.

        Distributes incoming damage across members (tank absorbs most).
        Returns list of damage dealt per member.
        """
        if self.all_dead:
            return [0] * self.size

        tank = self.tank
        alive = self.alive_members
        damage_dealt: List[int] = []

        for member in self.members:
            if not member.alive:
                damage_dealt.append(0)
                continue

            # Damage distribution: tank takes 60%, rest split evenly
            if member is tank and len(alive) > 1:
                inc_dmg = int(total_enemy_damage * 0.60)
                if len(alive) > 2:
                    remaining = total_enemy_damage - inc_dmg
                    per_other = remaining // (len(alive) - 1)
                    inc_dmg += per_other  # tank also gets share of remainder
            else:
                if len(alive) <= 1:
                    inc_dmg = total_enemy_damage
                elif tank is not None and len(alive) > 1:
                    remaining = total_enemy_damage - int(total_enemy_damage * 0.60)
                    inc_dmg = remaining // (len(alive) - 1)
                else:
                    inc_dmg = total_enemy_damage // len(alive)

            # Apply party buff as extra mitigation
            inc_dmg = max(0, inc_dmg - int(self.party_buff * 5))

            dmg = member.step(inc_dmg)
            damage_dealt.append(dmg)

        # Healer provides additional healing to lowest HP member
        healer = self.healer
        if healer and healer.alive and len(alive) > 1:
            lowest = min(
                (m for m in alive if m is not healer),
                key=lambda b: b.current_hp / b.stats.max_hp,
                default=None,
            )
            if lowest:
                heal_amt = int(healer.stats.magic_damage * 0.8 * self.party_buff)
                lowest.current_hp = min(lowest.stats.max_hp, lowest.current_hp + heal_amt)

        return damage_dealt

    # ------------------------------------------------------------------
    # Simulation lifecycle
    # ------------------------------------------------------------------

    def reset_all(self) -> None:
        """Reset every member to full HP/MP for a fresh simulation."""
        for m in self.members:
            m.reset()
        self._aggro_table.clear()
        for m in self.members:
            self._aggro_table[m.name] = 0

    def summary(self) -> Dict:
        return {
            "party_name": self.name,
            "size": self.size,
            "alive_count": len(self.alive_members),
            "all_dead": self.all_dead,
            "total_dps": round(self.total_dps, 1),
            "tank": self.tank.name if self.tank else "none",
            "members": [m.summary() for m in self.members],
        }