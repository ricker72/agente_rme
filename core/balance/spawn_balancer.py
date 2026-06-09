from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region


@dataclass
class SpawnAdjustment:
    """Record of a single spawn adjustment made."""
    zone_name: str
    action: str  # "add", "remove", "modify_radius", "modify_respawn"
    monster: str
    x: int = 0
    y: int = 0
    z: int = 7
    old_value: Any = None
    new_value: Any = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "action": self.action,
            "monster": self.monster,
            "position": f"{self.x}:{self.y}:{self.z}",
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
        }


@dataclass
class SpawnBalanceResult:
    """Result of spawn balancing operation."""
    adjustments: List[SpawnAdjustment] = field(default_factory=list)
    zones_modified: List[str] = field(default_factory=list)
    spawns_added: int = 0
    spawns_removed: int = 0
    radii_adjusted: int = 0
    respawns_adjusted: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adjustments": [a.to_dict() for a in self.adjustments],
            "zones_modified": self.zones_modified,
            "spawns_added": self.spawns_added,
            "spawns_removed": self.spawns_removed,
            "radii_adjusted": self.radii_adjusted,
            "respawns_adjusted": self.respawns_adjusted,
        }


class SpawnBalancer:
    """
    Balances spawn density across zones.

    Corrects:
      - Overcrowded zones (too many spawns per area)
      - Empty zones (too few spawns)
      - Mismatched respawn rates
      - Inappropriate spawn radii

    Thresholds based on Tibia reference:
      - Ideal spawn density: 3-12 spawns per hunt zone
      - Respawn time: 30-180s
      - Spawn radius: 3-8 tiles
    """

    MIN_SPAWNS_PER_ZONE = 3
    MAX_SPAWNS_PER_ZONE = 12
    IDEAL_SPAWNS_PER_ZONE = 7
    MIN_RESPAWN = 30
    MAX_RESPAWN = 180
    IDEAL_RESPAWN = 60
    MIN_RADIUS = 3
    MAX_RADIUS = 8
    IDEAL_RADIUS = 5

    def balance(self, world: WorldModel, region: Region,
                spawns_per_zone: Optional[Dict[str, int]] = None) -> SpawnBalanceResult:
        """
        Balance spawns within a region of the world.

        Args:
            world: WorldModel to modify in-place.
            region: The region to balance.
            spawns_per_zone: Optional pre-computed zone spawn count mapping.

        Returns:
            SpawnBalanceResult with all adjustments made.
        """
        result = SpawnBalanceResult()

        zone_spawns = self._collect_spawns_in_region(world, region)
        current_count = len(zone_spawns)

        if current_count < self.MIN_SPAWNS_PER_ZONE:
            self._add_spawns(world, region, zone_spawns, result)
        elif current_count > self.MAX_SPAWNS_PER_ZONE:
            self._remove_spawns(world, region, zone_spawns, result)

        # Re-collect after add/remove operations
        zone_spawns = self._collect_spawns_in_region(world, region)
        self._adjust_respawn_times(world, zone_spawns, result)
        self._adjust_radii(world, zone_spawns, result)

        return result

    def _collect_spawns_in_region(self, world: WorldModel,
                                  region: Region) -> List[Tuple[int, int, int, Spawn]]:
        """Collect all spawn positions and data within a region."""
        zone_spawns: List[Tuple[int, int, int, Spawn]] = []
        for tile in world.tiles.values():
            if tile.zone == region.name and tile.spawn is not None:
                zone_spawns.append((tile.x, tile.y, tile.z, tile.spawn))
        return zone_spawns

    def _add_spawns(self, world: WorldModel, region: Region,
                    existing: List[Tuple[int, int, int, Spawn]],
                    result: SpawnBalanceResult) -> None:
        """Add spawns to fill underpopulated zones."""
        target = self.IDEAL_SPAWNS_PER_ZONE
        needed = target - len(existing)

        if needed <= 0:
            return

        existing_positions = {(x, y) for x, y, _, _ in existing}

        candidate_tiles: List[Tile] = []
        for tile in world.tiles.values():
            if tile.zone == region.name and tile.spawn is None:
                if (tile.x, tile.y) not in existing_positions:
                    candidate_tiles.append(tile)

        existing_monsters = [s.monster for _, _, _, s in existing]
        if not existing_monsters:
            return

        monster_cycle = list(set(existing_monsters))

        added = 0
        for tile in candidate_tiles:
            if added >= needed:
                break

            monster = monster_cycle[added % len(monster_cycle)]

            new_spawn = Spawn(
                monster=monster,
                respawn=self.IDEAL_RESPAWN,
                radius=self.IDEAL_RADIUS,
            )
            tile.spawn = new_spawn
            added += 1

            result.adjustments.append(SpawnAdjustment(
                zone_name=region.name,
                action="add",
                monster=monster,
                x=tile.x,
                y=tile.y,
                z=tile.z,
                old_value=None,
                new_value=new_spawn.to_dict(),
                reason=f"Zone had only {len(existing)} spawns (min={self.MIN_SPAWNS_PER_ZONE})",
            ))

        result.spawns_added += added
        if added > 0 and region.name not in result.zones_modified:
            result.zones_modified.append(region.name)

    def _remove_spawns(self, world: WorldModel, region: Region,
                       existing: List[Tuple[int, int, int, Spawn]],
                       result: SpawnBalanceResult) -> None:
        """Remove excess spawns from overcrowded zones."""
        target = self.IDEAL_SPAWNS_PER_ZONE
        excess = len(existing) - target

        if excess <= 0:
            return

        positions = [(x, y) for x, y, _, _ in existing]
        center_x = sum(p[0] for p in positions) / max(len(positions), 1)
        center_y = sum(p[1] for p in positions) / max(len(positions), 1)

        sorted_spawns = sorted(
            existing,
            key=lambda s: math.hypot(s[0] - center_x, s[1] - center_y),
            reverse=True,
        )

        removed = 0
        for x, y, z, spawn in sorted_spawns:
            if removed >= excess:
                break

            tile = world.get_tile(x, y, z)
            if tile is not None:
                monster_name = spawn.monster
                tile.spawn = None
                removed += 1

                result.adjustments.append(SpawnAdjustment(
                    zone_name=region.name,
                    action="remove",
                    monster=monster_name,
                    x=x,
                    y=y,
                    z=z,
                    old_value=spawn.to_dict(),
                    new_value=None,
                    reason=f"Zone had {len(existing)} spawns (max={self.MAX_SPAWNS_PER_ZONE})",
                ))

        result.spawns_removed += removed
        if removed > 0 and region.name not in result.zones_modified:
            result.zones_modified.append(region.name)

    def _adjust_respawn_times(self, world: WorldModel,
                              zone_spawns: List[Tuple[int, int, int, Spawn]],
                              result: SpawnBalanceResult) -> None:
        """Adjust respawn times to be within sane range."""
        for x, y, z, spawn in zone_spawns:
            if spawn.respawn < self.MIN_RESPAWN:
                old = spawn.respawn
                spawn.respawn = self.MIN_RESPAWN
                result.adjustments.append(SpawnAdjustment(
                    zone_name="",
                    action="modify_respawn",
                    monster=spawn.monster,
                    x=x, y=y, z=z,
                    old_value=old,
                    new_value=spawn.respawn,
                    reason=f"Respawn too fast ({old}s < {self.MIN_RESPAWN}s)",
                ))
                result.respawns_adjusted += 1

            elif spawn.respawn > self.MAX_RESPAWN:
                old = spawn.respawn
                spawn.respawn = self.MAX_RESPAWN
                result.adjustments.append(SpawnAdjustment(
                    zone_name="",
                    action="modify_respawn",
                    monster=spawn.monster,
                    x=x, y=y, z=z,
                    old_value=old,
                    new_value=spawn.respawn,
                    reason=f"Respawn too slow ({old}s > {self.MAX_RESPAWN}s)",
                ))
                result.respawns_adjusted += 1

    def _adjust_radii(self, world: WorldModel,
                      zone_spawns: List[Tuple[int, int, int, Spawn]],
                      result: SpawnBalanceResult) -> None:
        """Adjust spawn radii to be within sane range."""
        for x, y, z, spawn in zone_spawns:
            if spawn.radius < self.MIN_RADIUS:
                old = spawn.radius
                spawn.radius = self.MIN_RADIUS
                result.adjustments.append(SpawnAdjustment(
                    zone_name="",
                    action="modify_radius",
                    monster=spawn.monster,
                    x=x, y=y, z=z,
                    old_value=old,
                    new_value=spawn.radius,
                    reason=f"Radius too small ({old} < {self.MIN_RADIUS})",
                ))
                result.radii_adjusted += 1

            elif spawn.radius > self.MAX_RADIUS:
                old = spawn.radius
                spawn.radius = self.MAX_RADIUS
                result.adjustments.append(SpawnAdjustment(
                    zone_name="",
                    action="modify_radius",
                    monster=spawn.monster,
                    x=x, y=y, z=z,
                    old_value=old,
                    new_value=spawn.radius,
                    reason=f"Radius too large ({old} > {self.MAX_RADIUS})",
                ))
                result.radii_adjusted += 1

    def analyze_spawn_density(self, world: WorldModel,
                              region: Region) -> Dict[str, Any]:
        """
        Analyze spawn density for a region without modifying it.

        Returns:
            Dict with density metrics and recommendations.
        """
        zone_spawns = self._collect_spawns_in_region(world, region)
        count = len(zone_spawns)

        region_tiles = [t for t in world.tiles.values() if t.zone == region.name]
        tile_count = max(len(region_tiles), 1)

        density = count / tile_count

        monster_types: Dict[str, int] = {}
        for _, _, _, spawn in zone_spawns:
            monster_types[spawn.monster] = monster_types.get(spawn.monster, 0) + 1

        recommendations: List[str] = []
        if count < self.MIN_SPAWNS_PER_ZONE:
            recommendations.append(
                f"Add {self.IDEAL_SPAWNS_PER_ZONE - count} spawns to reach ideal density"
            )
        elif count > self.MAX_SPAWNS_PER_ZONE:
            recommendations.append(
                f"Remove {count - self.IDEAL_SPAWNS_PER_ZONE} spawns to reduce overcrowding"
            )

        avg_respawn = sum(s.respawn for _, _, _, s in zone_spawns) / max(count, 1)
        avg_radius = sum(s.radius for _, _, _, s in zone_spawns) / max(count, 1)

        return {
            "zone_name": region.name,
            "spawn_count": count,
            "tile_count": tile_count,
            "density_ratio": round(density, 4),
            "monster_types": monster_types,
            "avg_respawn": round(avg_respawn, 1),
            "avg_radius": round(avg_radius, 1),
            "in_range": self.MIN_SPAWNS_PER_ZONE <= count <= self.MAX_SPAWNS_PER_ZONE,
            "recommendations": recommendations,
        }