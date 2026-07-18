from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .architect import ArchitectAI, DesignRationale
from .design_rules import DesignRules
from .style_engine import StyleEngine
from .layout_engine import LayoutEngine, LayoutPlan
from .composition_engine import CompositionEngine, StyleComposition


@dataclass
class MapperDecision:
    """Complete architectural output from MapperAI."""

    prompt: str
    map_type: str
    rationale: DesignRationale
    composition: StyleComposition
    layout: LayoutPlan
    recommendation_count: int = 0
    decisions_log: List[str] = field(default_factory=list)


class MapperAI:
    """
    Full architectural pipeline: thinks before building.

    Pipeline:
        Prompt → Architect → DesignRules → StyleEngine → LayoutEngine → WorldPlan

    No tiles. No scripts. Only architectural decisions.
    """

    def __init__(self):
        self.architect = ArchitectAI()
        self.style_engine = StyleEngine()
        self.layout_engine = LayoutEngine()
        self.composer = CompositionEngine()

    def design(
        self,
        prompt: str,
        map_type: Optional[str] = None,
        map_width: int = 50,
        map_height: int = 50,
    ) -> MapperDecision:
        """
        Full architectural design pipeline.

        Args:
            prompt: Natural language prompt describing the desired map.
            map_type: 'city', 'dungeon', or 'hunt'. Auto-detected if None.
            map_width: Desired map width in tiles.
            map_height: Desired map height in tiles.

        Returns:
            MapperDecision with complete architectural output.
        """
        # 1. Detect map type if not provided
        if map_type is None:
            map_type = self._detect_type(prompt)

        # 2. Architect analyzes the prompt
        rationale = self.architect.analyze(prompt, map_type)

        # 3. Extract and compose styles
        styles = self._extract_styles(prompt)
        if len(styles) > 1:
            ratios = self.composer.suggest_ideal_ratio(styles)
            composition = self.composer.compose(ratios)
        else:
            composition = StyleComposition(
                name=styles[0] if styles else "issavi",
                styles=[(styles[0], 1.0)] if styles else [],
                merged_dna=self.style_engine.detect(styles[0] if styles else "issavi"),
                primary_style=styles[0] if styles else "issavi",
                description=f"Single style: {styles[0] if styles else 'issavi'}",
            )

        # 4. Layout engine decides where to place zones
        dna = composition.merged_dna
        layout = self.layout_engine.plan(map_type, dna, map_width, map_height)

        # 5. Architectural recommendations
        recommendations = self.style_engine.get_recommendations(dna, map_type)

        # 6. Validate against design rules
        zones_present = [z.zone.name for z in layout.zones]
        violations = DesignRules.violations_for(map_type, zones_present)

        # Build decision log
        log = []
        log.append(f"[ARCHITECT] Analyzing: {prompt}")
        log.append(f"[ARCHITECT] Map type: {map_type}")
        log.append(f"[ARCHITECT] Style: {composition.name}")
        log.append(f"[ARCHITECT] DNA: {dna.to_dict()}")
        log.append(
            f"[COMPOSITION] Ratio: {[f'{r * 100:.0f}% {n}' for n, r in composition.styles]}"
        )
        log.append(f"[COMPOSITION] Description: {composition.description}")
        for dec in rationale.decisions:
            log.append(
                f"[DECISION] {dec.question}: {dec.answer} ({dec.reason[:80]}...)"
            )
        for line in layout.decisions_log:
            log.append(f"[LAYOUT] {line}")
        for rec in recommendations:
            log.append(f"[RECOMMEND] {rec}")
        if violations:
            for v in violations:
                log.append(f"[VIOLATION] {v}")
        else:
            log.append("[VALIDATION] All design rules satisfied")

        return MapperDecision(
            prompt=prompt,
            map_type=map_type,
            rationale=rationale,
            composition=composition,
            layout=layout,
            recommendation_count=len(recommendations),
            decisions_log=log,
        )

    def _detect_type(self, prompt: str) -> str:
        """Auto-detect map type from prompt keywords."""
        lower = prompt.lower()
        if "ciudad" in lower or "city" in lower:
            return "city"
        if "dungeon" in lower or "mazmorra" in lower or "calabozo" in lower:
            return "dungeon"
        if "hunt" in lower or "caza" in lower:
            return "hunt"
        # Default: if mentions multiple themes/expansion, likely dungeon
        if len(self._extract_styles(prompt)) > 1:
            return "dungeon"
        return "hunt"

    def _extract_styles(self, prompt: str) -> List[str]:
        """Extract style names from prompt."""
        lower = prompt.lower().replace(" ", "")
        found = []
        for style in self.style_engine.KNOWN_STYLES:
            clean = style.lower().replace(" ", "")
            if clean in lower:
                found.append(style)
        if not found:
            found = ["issavi"]
        return found

    def answer_why(self, question: str, decision: MapperDecision) -> str:
        """
        Answer "why" questions about the design.

        Examples:
            "¿Por qué este templo está aquí?"
            "¿Por qué esta hunt funciona?"
        """
        return self.architect.answer_why(question, decision.rationale)

    def to_dict(self, decision: MapperDecision) -> Dict:
        """Serialize the full architectural decision for downstream consumers."""
        return {
            "prompt": decision.prompt,
            "map_type": decision.map_type,
            "style": decision.rationale.style,
            "composition": {
                "styles": [(n, r) for n, r in decision.composition.styles],
                "description": decision.composition.description,
            },
            "dna": decision.composition.merged_dna.to_dict(),
            "layout": self.layout_engine.to_dict(decision.layout),
            "rationale": {
                "why_layout": decision.rationale.why_this_layout,
                "why_style": decision.rationale.why_this_style,
                "why_zones": decision.rationale.why_these_zones,
                "risk_assessment": decision.rationale.risk_assessment,
            },
            "recommendations": decision.recommendation_count,
            "decisions_log": decision.decisions_log,
        }

    def explain(self, decision: MapperDecision) -> str:
        """Generate a complete natural-language explanation of the design."""
        lines = []
        lines.append("=" * 60)
        lines.append(
            f"  ARQUITECTURA: {decision.map_type.upper()} - {decision.rationale.style.upper()}"
        )
        lines.append("=" * 60)
        lines.append("")

        lines.append("POR QUÉ ESTE DISEÑO:")
        lines.append(f"  {decision.rationale.why_this_layout}")
        lines.append("")
        lines.append("POR QUÉ ESTE ESTILO:")
        lines.append(f"  {decision.rationale.why_this_style}")
        lines.append("")
        lines.append("POR QUÉ ESTAS ZONAS:")
        lines.append(f"  {decision.rationale.why_these_zones}")
        lines.append("")
        lines.append("RIESGOS IDENTIFICADOS:")
        lines.append(f"  {decision.rationale.risk_assessment}")
        lines.append("")

        lines.append("DECISIONES ARQUITECTONICAS:")
        for i, dec in enumerate(decision.rationale.decisions, 1):
            lines.append(f"  {i}. {dec.question}")
            lines.append(f"     -> {dec.answer}")
            lines.append(f"     Razón: {dec.reason}")
            if dec.alternatives:
                lines.append(f"     Alternativas: {', '.join(dec.alternatives)}")
            lines.append("")

        lines.append("COMPOSICIÓN DE ESTILOS:")
        for name, ratio in decision.composition.styles:
            lines.append(f"  {ratio * 100:.0f}% {name}")
        lines.append(f"  Descripción: {decision.composition.description}")
        lines.append("")

        lines.append("LAYOUT DE ZONAS:")
        for z in decision.layout.zones:
            lines.append(f"  [{z.zone.zone_type}] {z.zone.name}")
            lines.append(f"     Posición: ({z.position[0]}, {z.position[1]})")
            lines.append(f"     Tamaño: {z.size[0]}x{z.size[1]}")
            lines.append(f"     Propósito: {z.zone.purpose}")
            lines.append(f"     Razón: {z.reason}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
