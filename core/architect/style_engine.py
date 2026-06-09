from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class StyleDNA:
    """
    Represents the architectural DNA of a Tibia style.

    Each float property ranges from 0.0 (none) to 1.0 (maximum).
    """
    style: str
    open_spaces: float = 0.5          # Prefer wide-open areas vs tight corridors
    symmetry: float = 0.3              # Prefer mirrored layouts
    decoration_density: float = 0.5    # How many decorative items per tile
    verticality: float = 0.2           # Use of height differences / stairs
    organic_layout: float = 0.5        # Irregular/natural shapes vs grid-aligned
    darkness: float = 0.3              # Dark/ominous atmosphere factor
    complexity: float = 0.5            # Layout intricacy (number of branches)
    water_presence: float = 0.1        # Water/lava features
    spawn_density: float = 0.5         # Monster placement density
    reward_richness: float = 0.5       # Loot quality factor

    def blend(self, other: StyleDNA, ratio: float = 0.5) -> StyleDNA:
        """Blend two StyleDNAs with given ratio (0.0 = all self, 1.0 = all other)."""
        ratio = max(0.0, min(1.0, ratio))
        fields = [f for f in self.__dataclass_fields__ if f != "style"]
        kwargs = {"style": f"{self.style}+{other.style}"}
        for f in fields:
            a = getattr(self, f)
            b = getattr(other, f)
            kwargs[f] = a * (1 - ratio) + b * ratio
        return StyleDNA(**kwargs)

    def to_dict(self) -> Dict:
        return {f: getattr(self, f) for f in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, data: Dict) -> StyleDNA:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================
# Known Style DNA profiles
# ============================================================

STYLE_DNA_REGISTRY: Dict[str, StyleDNA] = {
    "issavi": StyleDNA(
        style="issavi",
        open_spaces=0.8,
        symmetry=0.7,
        decoration_density=0.6,
        verticality=0.2,
        organic_layout=0.3,
        darkness=0.2,
        complexity=0.5,
        water_presence=0.3,
        spawn_density=0.6,
        reward_richness=0.7,
    ),
    "roshamuul": StyleDNA(
        style="roshamuul",
        open_spaces=0.4,
        symmetry=0.2,
        decoration_density=0.4,
        verticality=0.5,
        organic_layout=0.7,
        darkness=0.8,
        complexity=0.7,
        water_presence=0.1,
        spawn_density=0.7,
        reward_richness=0.6,
    ),
    "soulwar": StyleDNA(
        style="soulwar",
        open_spaces=0.3,
        symmetry=0.2,
        decoration_density=0.7,
        verticality=0.6,
        organic_layout=0.5,
        darkness=0.9,
        complexity=0.8,
        water_presence=0.2,
        spawn_density=0.8,
        reward_richness=0.9,
    ),
    "library": StyleDNA(
        style="library",
        open_spaces=0.5,
        symmetry=0.8,
        decoration_density=0.8,
        verticality=0.3,
        organic_layout=0.2,
        darkness=0.6,
        complexity=0.6,
        water_presence=0.1,
        spawn_density=0.5,
        reward_richness=0.7,
    ),
    "yalahar": StyleDNA(
        style="yalahar",
        open_spaces=0.6,
        symmetry=0.4,
        decoration_density=0.5,
        verticality=0.4,
        organic_layout=0.4,
        darkness=0.4,
        complexity=0.6,
        water_presence=0.5,
        spawn_density=0.5,
        reward_richness=0.5,
    ),
    "falcon": StyleDNA(
        style="falcon",
        open_spaces=0.3,
        symmetry=0.3,
        decoration_density=0.6,
        verticality=0.7,
        organic_layout=0.6,
        darkness=0.7,
        complexity=0.7,
        water_presence=0.0,
        spawn_density=0.7,
        reward_richness=0.8,
    ),
    "cobra": StyleDNA(
        style="cobra",
        open_spaces=0.4,
        symmetry=0.3,
        decoration_density=0.5,
        verticality=0.5,
        organic_layout=0.8,
        darkness=0.7,
        complexity=0.8,
        water_presence=0.3,
        spawn_density=0.6,
        reward_richness=0.7,
    ),
    "ice": StyleDNA(
        style="ice",
        open_spaces=0.5,
        symmetry=0.2,
        decoration_density=0.3,
        verticality=0.6,
        organic_layout=0.7,
        darkness=0.5,
        complexity=0.5,
        water_presence=0.4,
        spawn_density=0.5,
        reward_richness=0.4,
    ),
    "jungle": StyleDNA(
        style="jungle",
        open_spaces=0.4,
        symmetry=0.1,
        decoration_density=0.7,
        verticality=0.4,
        organic_layout=0.9,
        darkness=0.5,
        complexity=0.6,
        water_presence=0.6,
        spawn_density=0.6,
        reward_richness=0.5,
    ),
    "thais": StyleDNA(
        style="thais",
        open_spaces=0.5,
        symmetry=0.5,
        decoration_density=0.4,
        verticality=0.1,
        organic_layout=0.3,
        darkness=0.2,
        complexity=0.4,
        water_presence=0.3,
        spawn_density=0.3,
        reward_richness=0.4,
    ),
    "venore": StyleDNA(
        style="venore",
        open_spaces=0.4,
        symmetry=0.3,
        decoration_density=0.5,
        verticality=0.2,
        organic_layout=0.6,
        darkness=0.3,
        complexity=0.5,
        water_presence=0.7,
        spawn_density=0.4,
        reward_richness=0.4,
    ),
    "ankrahmun": StyleDNA(
        style="ankrahmun",
        open_spaces=0.6,
        symmetry=0.6,
        decoration_density=0.3,
        verticality=0.1,
        organic_layout=0.2,
        darkness=0.3,
        complexity=0.3,
        water_presence=0.1,
        spawn_density=0.3,
        reward_richness=0.4,
    ),
}


class StyleEngine:
    """
    Detects and applies architectural styles to map generation.

    Usage:
        engine = StyleEngine()
        dna = engine.detect("issavi")
        merged = engine.merge(["issavi", "roshamuul"], ratios=[0.7, 0.3])
    """

    KNOWN_STYLES = {
        "issavi", "roshamuul", "soulwar", "soul war",
        "library", "yalahar", "falcon", "cobra",
        "ice", "jungle", "thais", "venore", "carlin",
        "ankrahmun", "darashia", "edron", "port hope",
        "svargrond", "liberty bay", "kazordoon", "ab'dendriel",
    }

    def detect(self, name: str) -> StyleDNA:
        """Detect the StyleDNA for a given style name."""
        name = name.lower().replace(" ", "")
        if name in STYLE_DNA_REGISTRY:
            return STYLE_DNA_REGISTRY[name]
        # Default to issavi-like
        return StyleDNA(style=name)

    def merge(self, styles: List[str], ratios: Optional[List[float]] = None) -> StyleDNA:
        """
        Merge multiple styles with given ratios.
        If ratios not provided, uses equal weighting.
        """
        if not styles:
            return StyleDNA(style="default")

        if len(styles) == 1:
            return self.detect(styles[0])

        if ratios is None:
            ratios = [1.0 / len(styles)] * len(styles)

        # Normalize ratios
        total = sum(ratios)
        if total == 0:
            ratios = [1.0 / len(styles)] * len(styles)
        else:
            ratios = [r / total for r in ratios]

        # Start with first style and blend sequentially
        result = self.detect(styles[0])
        remaining_weight = 1.0
        for i, style in enumerate(styles[1:], start=1):
            if remaining_weight <= 0:
                break
            blend_ratio = ratios[i] / remaining_weight if remaining_weight > 0 else 0.5
            result = result.blend(self.detect(style), blend_ratio)
            remaining_weight -= ratios[i]

        result.style = "+".join(styles)
        return result

    def get_recommendations(self, dna: StyleDNA, map_type: str) -> List[str]:
        """Generate architectural recommendations based on StyleDNA."""
        recs = []

        if dna.open_spaces > 0.7:
            recs.append(f"Use wide open plazas and broad corridors (open_spaces={dna.open_spaces})")
        if dna.symmetry > 0.6:
            recs.append(f"Apply symmetric layout principles (symmetry={dna.symmetry})")
        if dna.organic_layout > 0.6:
            recs.append(f"Prefer organic/natural shapes over grid-aligned (organic={dna.organic_layout})")
        if dna.verticality > 0.4:
            recs.append(f"Incorporate multi-floor vertical design (verticality={dna.verticality})")
        if dna.darkness > 0.5:
            recs.append(f"Use dark/ominous atmosphere with dim lighting (darkness={dna.darkness})")
        if dna.water_presence > 0.3:
            recs.append(f"Include water features: rivers, lakes, or underground pools")
        if dna.decoration_density > 0.6:
            recs.append(f"Apply high decoration density: statues, torches, rubble")
        if dna.complexity > 0.6:
            recs.append(f"Create complex multi-branch layouts with secondary paths")
        if dna.spawn_density > 0.6:
            recs.append(f"Pack monsters densely with varied tiers (spawn_density={dna.spawn_density})")
        if dna.reward_richness > 0.6:
            recs.append(f"Place high-value loot in treasure rooms (reward_richness={dna.reward_richness})")

        if map_type == "city":
            if dna.symmetry > 0.5:
                recs.append("Arrange districts in a radial pattern from central plaza")
            recs.append(f"Decorate streets with {dna.style}-themed items")
        elif map_type == "dungeon":
            if dna.complexity > 0.5:
                recs.append("Create branching paths with optional dead-ends containing loot")
            if dna.darkness > 0.5:
                recs.append("Use dim corridors and surprise monster ambushes")
        elif map_type == "hunt":
            recs.append("Ensure smooth monster flow from weak to strong encounters")

        return recs

    @classmethod
    def list_styles(cls) -> List[str]:
        return sorted(cls.KNOWN_STYLES)

    @classmethod
    def style_summary(cls, name: str) -> Dict:
        dna = STYLE_DNA_REGISTRY.get(name.lower())
        if not dna:
            return {"error": f"Unknown style: {name}"}
        return dna.to_dict()