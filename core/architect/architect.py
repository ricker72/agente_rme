from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .style_engine import StyleEngine, StyleDNA
from .design_rules import DesignRules, ZoneDesign
from .layout_engine import LayoutEngine, LayoutPlan


@dataclass
class ArchitecturalDecision:
    """A single reasoned architectural decision."""
    question: str
    answer: str
    reason: str
    alternatives: List[str] = field(default_factory=list)


@dataclass
class DesignRationale:
    """Complete architectural rationale for a map design."""
    map_type: str
    style: str
    decisions: List[ArchitecturalDecision] = field(default_factory=list)
    why_this_layout: str = ""
    why_this_style: str = ""
    why_these_zones: str = ""
    what_to_avoid: List[str] = field(default_factory=list)
    risk_assessment: str = ""


class ArchitectAI:
    """
    Thinks like a professional Tibia mapper.

    Responde: "¿Qué debería existir aquí?" ANTES de "¿Qué tile colocar aquí?"

    Pipeline:
        Prompt → Style Detection → Design Rules → Zone Decisions → Rationale
    """

    def __init__(self):
        self.style_engine = StyleEngine()

    def analyze(self, prompt: str, map_type: str = "hunt") -> DesignRationale:
        """
        Analyze a prompt and produce architectural decisions.

        Returns a DesignRationale explaining WHY each choice was made.
        """
        # 1. Detect styles
        styles = self._extract_styles_from_prompt(prompt)
        dna = self.style_engine.merge(styles) if len(styles) > 1 else self.style_engine.detect(styles[0] if styles else "issavi")

        # 2. Load design rules
        rules = DesignRules.for_city() if map_type == "city" else (
            DesignRules.for_dungeon() if map_type == "dungeon" else DesignRules.for_hunt()
        )
        zones = DesignRules.zones_for(map_type)
        avoids = DesignRules.avoid_list(map_type)

        # 3. Generate architectural decisions
        rationale = DesignRationale(
            map_type=map_type,
            style=dna.style,
            what_to_avoid=avoids,
        )

        # Core decisions
        rationale.decisions = self._generate_decisions(map_type, dna, rules, zones, avoids)

        # Why statements
        rationale.why_this_layout = self._justify_layout(map_type, dna)
        rationale.why_this_style = self._justify_style(dna)
        rationale.why_these_zones = self._justify_zones(zones, map_type, dna)
        rationale.risk_assessment = self._assess_risks(map_type, dna, zones)

        return rationale

    def _extract_styles_from_prompt(self, prompt: str) -> List[str]:
        """Extract style names from a natural language prompt."""
        lower = prompt.lower().replace(" ", "")
        found = []
        for style in self.style_engine.KNOWN_STYLES:
            clean = style.lower().replace(" ", "")
            if clean in lower:
                found.append(style)
        if not found:
            found = ["issavi"]
        return found

    def _generate_decisions(self, map_type: str, dna: StyleDNA,
                             rules: List, zones: List[ZoneDesign],
                             avoids: List[str]) -> List[ArchitecturalDecision]:
        """Generate all architectural decisions with justifications."""
        decisions = []

        # Decision 1: Layout strategy
        if dna.symmetry > 0.5:
            decisions.append(ArchitecturalDecision(
                question="¿Qué estrategia de layout usar?",
                answer="Simétrica radial",
                reason=f"Style {dna.style} has high symmetry ({dna.symmetry:.1f}). "
                       f"Zones will be arranged in concentric rings around a central hub.",
                alternatives=["Grid-based", "Organic scatter"],
            ))
        elif dna.organic_layout > 0.5:
            decisions.append(ArchitecturalDecision(
                question="¿Qué estrategia de layout usar?",
                answer="Orgánica natural",
                reason=f"Style {dna.style} favors organic layouts ({dna.organic_layout:.1f}). "
                       f"Zones will follow natural-looking irregular placement.",
                alternatives=["Simétrica radial", "Grid-based"],
            ))
        else:
            decisions.append(ArchitecturalDecision(
                question="¿Qué estrategia de layout usar?",
                answer="Grid estructurado",
                reason=f"Style {dna.style} has balanced proportions. "
                       f"Grid-based layout provides predictable flow.",
                alternatives=["Simétrica radial", "Orgánica"],
            ))

        # Decision 2: Zone count
        decisions.append(ArchitecturalDecision(
            question="¿Cuántas zonas crear?",
            answer=str(len(zones)),
            reason=f"Design rules for {map_type} mandate {len(zones)} core zones: "
                   f"{', '.join(z.name for z in zones)}",
            alternatives=[str(len(zones) - 1), str(len(zones) + 1)],
        ))

        # Decision 3: Vertical strategy
        if map_type == "dungeon" and dna.verticality > 0.3:
            floors = max(2, int(dna.verticality * 5))
            decisions.append(ArchitecturalDecision(
                question="¿Cuántos pisos usar?",
                answer=str(floors),
                reason=f"Style {dna.style} verticality={dna.verticality:.1f} suggests "
                       f"{floors}-floor dungeon with stairs between levels.",
                alternatives=[str(floors - 1), str(floors + 1)],
            ))
        elif map_type == "dungeon":
            decisions.append(ArchitecturalDecision(
                question="¿Cuántos pisos usar?",
                answer="3",
                reason="Three floors provides good progression: entrance → combat → boss.",
                alternatives=["2", "4"],
            ))

        # Decision 4: Spawn strategy
        if dna.spawn_density > 0.6:
            decisions.append(ArchitecturalDecision(
                question="¿Cómo distribuir los spawns?",
                answer="Alta densidad con progresión",
                reason=f"High spawn density ({dna.spawn_density:.1f}). "
                       f"Monsters escalate from entry to boss room with 3+ tiers.",
                alternatives=["Densidad uniforme", "Solo jefes"],
            ))
        else:
            decisions.append(ArchitecturalDecision(
                question="¿Cómo distribuir los spawns?",
                answer="Densidad moderada y variada",
                reason=f"Moderate spawn density ({dna.spawn_density:.1f}). "
                       f"Varied monster types in distinct zones.",
                alternatives=["Alta densidad", "Baja densidad"],
            ))

        # Decision 5: What to avoid
        decisions.append(ArchitecturalDecision(
            question="¿Qué evitar en el diseño?",
            answer=f"{len(avoids)} patrones anti-diseño",
            reason="Evitar: " + "; ".join(avoids[:3]) + (
                f" (+{len(avoids)-3} more)" if len(avoids) > 3 else ""
            ),
            alternatives=[],
        ))

        # Decision 6: Entry placement
        decisions.append(ArchitecturalDecision(
            question="¿Dónde colocar la entrada?",
            answer="Borde sur del mapa" if map_type == "city" else "Centro del primer piso",
            reason="Cities enter from roads at borders; dungeons descend from a central entry point.",
            alternatives=["Borde norte", "Esquina aleatoria"],
        ))

        # Decision 7: Boss room placement
        if map_type in ("dungeon", "hunt"):
            decisions.append(ArchitecturalDecision(
                question="¿Dónde colocar el boss room?",
                answer="Último piso, punto más alejado de la entrada",
                reason="Boss should be the final challenge, requiring exploration "
                       "and risk to reach.",
                alternatives=["Cerca de entrada", "En todos los pisos"],
            ))

        return decisions

    def _justify_layout(self, map_type: str, dna: StyleDNA) -> str:
        """Explain why this layout was chosen."""
        if map_type == "city":
            return (
                f"A {map_type} layout was chosen because cities require "
                f"connected districts with clear roads and functional zones "
                f"(temple, depot, market). Style {dna.style} influences: "
                f"{'wide plazas' if dna.open_spaces > 0.6 else 'compact streets'}, "
                f"{'symmetric arrangement' if dna.symmetry > 0.5 else 'asymmetric flow'}."
            )
        elif map_type == "dungeon":
            return (
                f"A {map_type} layout was chosen for progressive difficulty. "
                f"{'Multi-floor' if dna.verticality > 0.3 else 'Single-floor'} design "
                f"with {'complex branching' if dna.complexity > 0.5 else 'linear progression'} "
                f"guides players from entrance to boss through escalating encounters."
            )
        else:
            return (
                f"A {map_type} layout optimizes for flow, risk, and reward. "
                f"Style {dna.style} contributes: "
                f"{'open hunting grounds' if dna.open_spaces > 0.6 else 'enclosed arenas'}, "
                f"{'high monster density' if dna.spawn_density > 0.6 else 'spread-out encounters'}."
            )

    def _justify_style(self, dna: StyleDNA) -> str:
        """Explain why this style was selected."""
        traits = []
        for attr in ["open_spaces", "symmetry", "darkness", "complexity",
                      "decoration_density", "reward_richness"]:
            val = getattr(dna, attr)
            if val > 0.6:
                traits.append(f"high {attr.replace('_', ' ')} ({val:.1f})")
            elif val < 0.4:
                traits.append(f"low {attr.replace('_', ' ')} ({val:.1f})")

        return (
            f"Style '{dna.style}' was selected/merged because it matches the desired "
            f"architectural character. Key traits: "
            f"{', '.join(traits[:5])}."
            f"{' Additional traits: ' + ', '.join(traits[5:]) + '.' if len(traits) > 5 else ''}"
        )

    def _justify_zones(self, zones: List[ZoneDesign], map_type: str, dna: StyleDNA) -> str:
        """Explain why these specific zones are needed."""
        names = [z.name for z in zones]
        purposes = [z.purpose for z in zones if z.purpose]

        return (
            f"For a {map_type}, the following zones are architecturally required: "
            f"{', '.join(names)}. "
            f"They serve these purposes: {', '.join(purposes)}. "
            f"This composition ensures {'city functionality' if map_type == 'city' else 'balanced gameplay progression' if map_type == 'dungeon' else 'optimal hunting flow'}."
        )

    def _assess_risks(self, map_type: str, dna: StyleDNA,
                       zones: List[ZoneDesign]) -> str:
        """Identify potential design risks."""
        risks = []

        if len(zones) < 3:
            risks.append("Too few zones: map may feel repetitive")
        if dna.symmetry > 0.8:
            risks.append("Excessive symmetry: may feel artificial and predictable")
        if dna.spawn_density > 0.8 and map_type == "hunt":
            risks.append("Very high spawn density: risk of overwhelming players")
        if dna.complexity > 0.8:
            risks.append("High complexity: players may get lost without waypoints")
        if dna.open_spaces < 0.3 and map_type == "city":
            risks.append("Tight spaces: city may feel claustrophobic")

        if not risks:
            return "No significant design risks identified. The composition is well-balanced."
        return "Risks: " + "; ".join(risks)

    def answer_why(self, question: str, rationale: DesignRationale) -> str:
        """
        Answer specific architectural questions.
        Example: "¿Por qué este templo está aquí?"
        """
        for decision in rationale.decisions:
            if decision.question.lower() in question.lower():
                return f"Decisión: {decision.answer}\nRazón: {decision.reason}"
        return (
            f"Para el mapa tipo '{rationale.map_type}' con estilo '{rationale.style}', "
            f"las decisiones se basan en reglas de diseño que priorizan "
            f"{'funcionalidad urbana' if rationale.map_type == 'city' else 'progresión de dificultad' if rationale.map_type == 'dungeon' else 'flujo de caza óptimo'}."
        )