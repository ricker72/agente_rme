from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .style_engine import StyleEngine, StyleDNA


@dataclass
class StyleComposition:
    """Result of merging multiple styles."""

    name: str
    styles: List[Tuple[str, float]]  # (style_name, ratio)
    merged_dna: StyleDNA
    primary_style: str
    description: str


class CompositionEngine:
    """
    Mixes multiple Tibia styles into coherent architectural compositions.

    Examples:
        70% Issavi + 30% Roshamuul  → open+dark hybrid
        50% Library + 50% Soul War   → ornate+dark hybrid

    Capable of blending any number of styles with weighted ratios.
    """

    def __init__(self):
        self.style_engine = StyleEngine()

    def compose(self, styles: List[Tuple[str, float]]) -> StyleComposition:
        """
        Blend multiple styles with specific ratios.

        Args:
            styles: List of (style_name, ratio) tuples. Ratios should sum to 1.0.

        Returns:
            StyleComposition with merged DNA and description.
        """
        if not styles:
            return StyleComposition(
                name="default",
                styles=[],
                merged_dna=StyleDNA(style="default"),
                primary_style="default",
                description="Default balanced style",
            )

        # Parse
        names = [s[0] for s in styles]
        ratios = [s[1] for s in styles]

        # Get DNAs for each
        dnas = [self.style_engine.detect(name) for name in names]

        # Compute primary
        max_idx = max(range(len(ratios)), key=lambda i: ratios[i])
        primary = names[max_idx]

        # Blend
        merged = dnas[0]
        if len(dnas) > 1:
            merged = self.style_engine.merge(names, ratios)

        name = "+".join(names)
        desc = self._describe_composition(names, ratios, merged)

        return StyleComposition(
            name=name,
            styles=list(zip(names, ratios)),
            merged_dna=merged,
            primary_style=primary,
            description=desc,
        )

    def compose_from_prompt(
        self, styles: List[str], ratios: Optional[List[float]] = None
    ) -> StyleComposition:
        """
        Compose from a list of style names with optional ratios.

        If ratios not provided, uses equal weighting.
        """
        if ratios is None:
            ratios = [1.0 / len(styles)] * len(styles)
        return self.compose(list(zip(styles, ratios)))

    def _describe_composition(
        self, names: List[str], ratios: List[float], dna: StyleDNA
    ) -> str:
        """Generate a natural language description of the style blend."""
        parts = []

        # Ratio summary
        ratio_desc = ", ".join(f"{r * 100:.0f}% {n}" for n, r in zip(names, ratios))
        parts.append(f"Composition: {ratio_desc}")

        # Key traits
        if dna.open_spaces > 0.7:
            parts.append("open expansive layout")
        elif dna.open_spaces < 0.4:
            parts.append("tight, enclosed corridors")

        if dna.symmetry > 0.6:
            parts.append("highly symmetric and structured")
        elif dna.symmetry < 0.3:
            parts.append("asymmetric, organic flow")

        if dna.darkness > 0.6:
            parts.append("dark, ominous atmosphere")
        elif dna.darkness < 0.3:
            parts.append("bright, welcoming environment")

        if dna.complexity > 0.6:
            parts.append("intricate multi-branch layout")
        elif dna.complexity < 0.4:
            parts.append("straightforward linear progression")

        if dna.verticality > 0.4:
            parts.append("significant vertical dimension")
        if dna.water_presence > 0.3:
            parts.append("water features present")
        if dna.decoration_density > 0.6:
            parts.append("richly decorated")
        if dna.spawn_density > 0.6:
            parts.append("densely populated with monsters")
        if dna.reward_richness > 0.6:
            parts.append("high-value loot potential")

        return ". ".join(parts) + "."

    def suggest_ideal_ratio(self, style_names: List[str]) -> List[Tuple[str, float]]:
        """
        Suggest an ideal style ratio based on style compatibility.

        For 2 styles, the dominant one gets 65-75%.
        For 3+ styles, primary gets 50%, rest distributed.
        """
        if len(style_names) <= 1:
            return [(style_names[0], 1.0)] if style_names else []

        if len(style_names) == 2:
            # Primary style gets 70%, secondary 30%
            dnas = [self.style_engine.detect(n) for n in style_names]
            # Choose primary based on higher reward_richness
            idx = 0 if dnas[0].reward_richness >= dnas[1].reward_richness else 1
            other = 1 - idx
            result = [(style_names[idx], 0.7), (style_names[other], 0.3)]
            return result

        # 3+ styles: primary gets 50%, rest split equally
        primary = style_names[0]
        rest = style_names[1:]
        ratio_primary = 0.5
        ratio_rest = 0.5 / len(rest)
        result = [(primary, ratio_primary)]
        for s in rest:
            result.append((s, ratio_rest))
        return result
