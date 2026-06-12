from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .style_engine import StyleDNA
from .design_rules import DesignRules, ZoneDesign


@dataclass
class LayoutDecision:
    """A single architectural placement decision."""

    zone: ZoneDesign
    position: Tuple[int, int]  # (x, y) center
    size: Tuple[int, int]  # (width, height)
    z_level: int = 7
    reason: str = ""
    priority: int = 5  # 1 (highest) to 10 (lowest)


@dataclass
class LayoutPlan:
    """The complete layout plan: what to build, where, and why."""

    map_type: str
    style: str
    zones: List[LayoutDecision] = field(default_factory=list)
    total_bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x1, y1, x2, y2
    decisions_log: List[str] = field(default_factory=list)
    avoid_list: List[str] = field(default_factory=list)


class LayoutEngine:
    """
    Decides DÓNDE construir, QUÉ construir, y QUÉ evitar.

    Uses DesignRules + StyleDNA to produce a LayoutPlan.

    This is the architectural "blueprint" phase — no tiles yet.
    """

    # Spacing constants
    ZONE_SPACING = 6
    MIN_ZONE_SIZE = 8
    MAX_ZONE_SIZE = 16
    ROAD_WIDTH = 2

    def plan(
        self,
        map_type: str,
        style_dna: StyleDNA,
        map_width: int = 50,
        map_height: int = 50,
    ) -> LayoutPlan:
        """
        Generate a complete layout plan for a given map type and style.

        Returns a LayoutPlan with all zone placements justified by design rules.
        """
        zones = DesignRules.zones_for(map_type)
        if not zones:
            return LayoutPlan(map_type=map_type, style=style_dna.style)

        plan = LayoutPlan(
            map_type=map_type,
            style=style_dna.style,
            avoid_list=DesignRules.avoid_list(map_type),
        )

        center_x = map_width // 2
        center_y = map_height // 2

        # Determine zone sizes based on StyleDNA
        zone_sizes = self._compute_zone_sizes(zones, style_dna, map_width, map_height)
        positions = self._compute_positions(
            zones, zone_sizes, center_x, center_y, style_dna
        )

        for i, zone in enumerate(zones):
            pos = positions[i]
            sz = zone_sizes[i]
            reason = self._justify_placement(zone, pos, style_dna, map_type)
            plan.zones.append(
                LayoutDecision(
                    zone=zone,
                    position=pos,
                    size=sz,
                    reason=reason,
                    priority=zone.purpose if zone.purpose else 5,
                )
            )
            plan.decisions_log.append(
                f"PLACE {zone.name} at ({pos[0]},{pos[1]}) size {sz[0]}x{sz[1]}: {reason}"
            )

        # Compute total bounds
        if plan.zones:
            xs = [z.position[0] - z.size[0] // 2 for z in plan.zones] + [
                z.position[0] + z.size[0] // 2 for z in plan.zones
            ]
            ys = [z.position[1] - z.size[1] // 2 for z in plan.zones] + [
                z.position[1] + z.size[1] // 2 for z in plan.zones
            ]
            plan.total_bounds = (min(xs), min(ys), max(xs), max(ys))

        return plan

    def _compute_zone_sizes(
        self, zones: List[ZoneDesign], dna: StyleDNA, map_w: int, map_h: int
    ) -> List[Tuple[int, int]]:
        """Determine each zone's size based on StyleDNA factors."""
        sizes = []
        for zone in zones:
            base = self.MIN_ZONE_SIZE
            if zone.suggested_size == "large":
                base = int(self.MIN_ZONE_SIZE * 1.8)
            elif zone.suggested_size == "small":
                base = int(self.MIN_ZONE_SIZE * 0.7)

            # Adjust by style factors
            if dna.open_spaces > 0.6:
                base = int(base * 1.2)
            if dna.complexity > 0.6 and base > 10:
                base -= 2  # more zones, slightly smaller

            base = max(self.MIN_ZONE_SIZE // 2, min(base, self.MAX_ZONE_SIZE))
            sizes.append((base, base))
        return sizes

    def _compute_positions(
        self,
        zones: List[ZoneDesign],
        sizes: List[Tuple[int, int]],
        cx: int,
        cy: int,
        dna: StyleDNA,
    ) -> List[Tuple[int, int]]:
        """Compute zone positions using style-driven layout algorithms."""
        n = len(zones)
        if n == 0:
            return []

        positions: List[Tuple[int, int]] = []

        # Radial layout (for symmetric styles) vs organic scatter
        if dna.symmetry > 0.5:
            positions = self._radial_positions(n, cx, cy, dna)
        elif dna.organic_layout > 0.5:
            positions = self._organic_positions(n, cx, cy, dna)
        else:
            # Grid-based layout
            cols = max(1, int(n**0.5))
            for i in range(n):
                col = i % cols
                row = i // cols
                px = cx + (col - cols // 2) * (self.MAX_ZONE_SIZE + self.ZONE_SPACING)
                py = cy + (row - n // cols // 2) * (
                    self.MAX_ZONE_SIZE + self.ZONE_SPACING
                )
                positions.append((px, py))

        return positions

    def _radial_positions(
        self, n: int, cx: int, cy: int, dna: StyleDNA
    ) -> List[Tuple[int, int]]:
        """Place zones in concentric rings around center (symmetric style)."""
        import math

        positions = [(cx, cy)]  # first zone at center
        radius = self.MAX_ZONE_SIZE + self.ZONE_SPACING
        for i in range(1, n):
            angle = (i - 1) * (2 * math.pi / max(1, n - 1))
            px = int(cx + radius * math.cos(angle))
            py = int(cy + radius * math.sin(angle))
            positions.append((px, py))
            if i % 4 == 0:
                radius += self.ZONE_SPACING
        return positions[:n]

    def _organic_positions(
        self, n: int, cx: int, cy: int, dna: StyleDNA
    ) -> List[Tuple[int, int]]:
        """Place zones with natural-looking irregular distribution."""
        import random

        rng = random.Random(42)  # deterministic seed for reproducibility
        positions = [(cx, cy)]
        for i in range(1, n):
            # Random offset from previous position with directional bias
            prev = positions[-1]
            dx = rng.randint(-self.MAX_ZONE_SIZE, self.MAX_ZONE_SIZE)
            dy = rng.randint(-self.MAX_ZONE_SIZE, self.MAX_ZONE_SIZE)
            # Bias toward unexplored areas
            if i > 1:
                avg_x = sum(p[0] for p in positions) / len(positions)
                avg_y = sum(p[1] for p in positions) / len(positions)
                dx += int((cx - avg_x) * 0.3)
                dy += int((cy - avg_y) * 0.3)
            positions.append((prev[0] + dx, prev[1] + dy))
        return positions

    def _justify_placement(
        self, zone: ZoneDesign, pos: Tuple[int, int], dna: StyleDNA, map_type: str
    ) -> str:
        """Explain WHY this zone is placed here."""
        reasons = []

        if zone.avoid_near:
            reasons.append(f"avoiding proximity to {', '.join(zone.avoid_near)}")

        if zone.adjacent_to:
            reasons.append(f"adjacent to {', '.join(zone.adjacent_to)}")

        if zone.min_distance_from_center > 0:
            reasons.append(f"min distance from center: {zone.min_distance_from_center}")

        purpose_map = {
            "safety": "provides safe regrouping zone",
            "warmup": "serves as introductory combat area",
            "grinding": "main monster hunting grounds",
            "risk": "high-risk, high-reward combat zone",
            "reward": "loot collection and treasure",
            "boss": "final challenge encounter",
        }
        if zone.purpose and zone.purpose in purpose_map:
            reasons.append(purpose_map[zone.purpose])

        if dna.open_spaces > 0.6:
            reasons.append("positioned for open visibility (style preference)")
        if dna.symmetry > 0.5:
            reasons.append("radial symmetric placement (style preference)")
        if dna.organic_layout > 0.6:
            reasons.append("organic natural placement (style preference)")

        return "; ".join(reasons) if reasons else f"default {map_type} zone placement"

    def to_dict(self, plan: LayoutPlan) -> Dict:
        """Serialize LayoutPlan to a dict for downstream consumers."""
        return {
            "map_type": plan.map_type,
            "style": plan.style,
            "zones": [
                {
                    "name": z.zone.name,
                    "type": z.zone.zone_type,
                    "purpose": z.zone.purpose,
                    "position": list(z.position),
                    "size": list(z.size),
                    "z_level": z.z_level,
                    "reason": z.reason,
                    "priority": z.priority,
                }
                for z in plan.zones
            ],
            "total_bounds": list(plan.total_bounds),
            "avoid_list": plan.avoid_list,
            "decisions_log": plan.decisions_log,
        }
