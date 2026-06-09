from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DesignExplanation:
    """An explanation of why a design decision was made."""
    topic: str
    summary: str
    factors: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "summary": self.summary,
            "factors": self.factors,
            "alternatives": self.alternatives,
            "risk_level": self.risk_level,
        }


class ReasoningEngine:
    """
    Explains WHY design decisions are made.

    Capabilities:
      - Answer "why" questions about any design element
      - Trace design rationale back to goals and constraints
      - List alternative approaches that were rejected
      - Identify trade-offs and risks
    """

    def __init__(self):
        self._decision_log: List[Dict[str, Any]] = []
        self._explanations: Dict[str, DesignExplanation] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(self, question: str) -> DesignExplanation:
        """
        Answer a "why" question about the world design.

        Examples:
          "¿Por qué se creó esta dungeon?"
          "¿Por qué existe este boss?"
          "¿Por qué este templo tiene 4 pisos?"
          "¿Por qué hay una ciudad aquí?"
          "¿Por qué estos monstruos están juntos?"
        """
        lower = question.lower()
        topic = self._extract_topic(question)

        # Check if we have a stored explanation for this topic
        if topic in self._explanations:
            return self._explanations[topic]

        # Generate explanation based on keywords
        if "dungeon" in lower or "mazmorra" in lower or "cave" in lower:
            return self._explain_dungeon(question, topic)
        elif "boss" in lower:
            return self._explain_boss(question, topic)
        elif "templo" in lower or "temple" in lower:
            return self._explain_temple(question, topic)
        elif "ciudad" in lower or "city" in lower:
            return self._explain_city(question, topic)
        elif "monstruo" in lower or "monster" in lower:
            return self._explain_monster(question, topic)
        elif "decoración" in lower or "decoration" in lower:
            return self._explain_decoration(question, topic)
        elif "tamaño" in lower or "size" in lower or "grande" in lower:
            return self._explain_size(question, topic)
        elif "entrada" in lower or "entrance" in lower:
            return self._explain_entrance(question, topic)
        elif "zona vacía" in lower:
            return self._explain_empty(question, topic)
        else:
            # Generic fallback
            return DesignExplanation(
                topic=topic,
                summary=f"La decisión sobre '{topic}' se basa en objetivos de diseño global, "
                        f"restricciones de calidad y principios de game design.",
                factors=[
                    "Objetivos de diseño del World Brain",
                    "Restricciones de nivel y dificultad",
                    "Patrones de mapas exitosos",
                ],
                alternatives=["No crear este elemento", "Crearlo en otra ubicación"],
                risk_level="low",
            )

    def register_decision(self, topic: str, explanation: DesignExplanation) -> None:
        """Register a design decision for future explanation queries."""
        self._explanations[topic] = explanation
        self._decision_log.append({
            "topic": topic,
            "summary": explanation.summary,
        })

    def log_decision(self, what: str, why: str, context: Optional[Dict] = None) -> None:
        """Log a raw decision for the audit trail."""
        self._decision_log.append({
            "topic": what,
            "summary": why,
            "context": context or {},
        })

    def get_decision_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the complete decision audit trail."""
        return self._decision_log[-limit:]

    def find_explanation(self, keyword: str) -> Optional[DesignExplanation]:
        """Find an explanation by keyword."""
        for topic, explanation in self._explanations.items():
            if keyword.lower() in topic.lower():
                return explanation
        return None

    def last_decisions(self, n: int = 5) -> List[str]:
        """Get the last n decision summaries."""
        return [
            f"[{d['topic']}] {d['summary'][:100]}"
            for d in self._decision_log[-n:]
        ]

    # ------------------------------------------------------------------
    # Explanation generators
    # ------------------------------------------------------------------

    def _explain_dungeon(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="Esta dungeon fue creada para proporcionar contenido de progresión "
                    "con una curva de dificultad ascendente. Su diseño prioriza la "
                    "experiencia de exploración, combate táctico y recompensa al final.",
            factors=[
                "Necesidad de contenido endgame para jugadores nivel 150+",
                "Objetivo ADD_ENDGAME prioridad 9",
                "Restricciones: tamaño 30x30 a 200x200, dificultad 6-8",
                "Patrón aprendido: dungeons con 3 pisos tienen mejor retención",
                "Estilo visual determinó usar theme roshamuul/issavi",
            ],
            alternatives=[
                "Dungeon lineal de 1 piso (rechazada: muy simple)",
                "Área abierta tipo hunt (rechazada: no proporciona progresión)",
                "No crear dungeon (rechazada: faltaba contenido endgame)",
            ],
            risk_level="medium",
        )

    def _explain_boss(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="Este boss fue diseñado como punto culminante de la zona. "
                    "Su ubicación al final del dungeon, con minions y mecánicas "
                    "específicas, proporciona un desafío adecuado para grupos "
                    "organizados.",
            factors=[
                "Objetivo ADD_ENDGAME: 3+ bosses requeridos",
                "Restricción boss_room: dificultad 6-10, tamaño 8-30",
                "Boss colocado en el punto más alejado de la entrada",
                "Minions protegen al boss para evitar kiting",
                "XP y loot calculados para recompensar el esfuerzo",
            ],
            alternatives=[
                "Boss al inicio del dungeon (rechazado: muy fácil)",
                "Múltiples bosses pequeños (rechazado: diluye el foco)",
                "Sin boss (rechazado: zona sin recompensa final)",
            ],
            risk_level="medium",
        )

    def _explain_temple(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="El templo se colocó en el centro de la ciudad porque es el "
                    "punto de reaparición principal. Su tamaño y decoración "
                    "reflejan la importancia cultural y religiosa de la zona.",
            factors=[
                "El templo es el primer lugar que ve un jugador al aparecer",
                "Debe ser visualmente impactante y claramente identificable",
                "Cerca del depot y market para comodidad del jugador",
                "Estilo issavi determinó usar columnas, alfombras y fuego sagrado",
            ],
            alternatives=[
                "Templo en las afueras (rechazado: inconveniente para rez)",
                "Templo pequeño (rechazado: no cumple función ceremonial)",
            ],
            risk_level="low",
        )

    def _explain_city(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="La ciudad fue diseñada como centro neurálgico del mundo. "
                    "Sus distritos (templo, depot, market, residencial) están "
                    "conectados por calles principales que facilitan la navegación.",
            factors=[
                "Toda zona necesita una ciudad base cerca",
                "Restricción city: PZ zone, tamaño mínimo 20x20",
                "Calles principales de 4 tiles de ancho para tráfico fluido",
                "NPCs comerciales agrupados en el distrito de mercado",
                "Muralla con torres para dar sensación de seguridad",
            ],
            alternatives=[
                "Ciudad sin muralla (rechazada: no protege a low levels)",
                "Un solo distrito (rechazado: insuficiente variedad)",
                "Ciudad subterránea (rechazada: difícil de navegar)",
            ],
            risk_level="low",
        )

    def _explain_monster(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="Estos monstruos fueron seleccionados para la zona basándose "
                    "en compatibilidad temática, nivel de dificultad y sinergia "
                    "de gameplay. La combinación crea encuentros tácticos interesantes.",
            factors=[
                "Monstruos del mismo tema visual (issavi ↔ Frazzlemaw/Sphinx)",
                "Rango de XP apropiado para el nivel de la zona",
                "Variedad de tipos: cuerpo a cuerpo, mago, ranged",
                "Sinergia: algunos monstruos potencian a otros",
                "Densidad de spawn calculada para flujo de caza óptimo",
            ],
            alternatives=[
                "Monstruos aleatorios (rechazado: rompe inmersión)",
                "Un solo tipo de monstruo (rechazado: monótono)",
                "Monstruos de nivel muy bajo (rechazado: sin desafío)",
            ],
            risk_level="low",
        )

    def _explain_decoration(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="La decoración fue seleccionada del Asset Recommender para "
                    "coincidir con el tema de la zona. Items like torch, statue, "
                    "y fountain se colocaron estratégicamente para mejorar la estética.",
            factors=[
                "AssetClassifier determinó items compatibles con el tema",
                "AssetSimilarity encontró items visualmente coherentes",
                "AssetRecommender priorizó items con alta afinidad temática",
                "Densidad de decoración mínima: 15 items por cada 100 tiles",
            ],
            alternatives=[
                "Sin decoración (rechazado: mapa plano y aburrido)",
                "Decoración aleatoria (rechazado: falta coherencia visual)",
            ],
            risk_level="low",
        )

    def _explain_size(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="El tamaño fue determinado por las restricciones del perfil "
                    "de diseño y el análisis de calidad. El objetivo es balancear "
                    "suficiente espacio para gameplay sin crear zonas vacías.",
            factors=[
                f"Restricción del perfil activo para dimensiones",
                "Quality Detector penaliza zonas muy pequeñas o muy grandes",
                "Densidad ideal: 60% tiles transitables",
            ],
            alternatives=[
                "Tamaño más pequeño (rechazado: densidad muy alta)",
                "Tamaño más grande (rechazado: zonas vacías)",
            ],
            risk_level="low",
        )

    def _explain_entrance(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="La entrada se colocó siguiendo principios de diseño "
                    "estándar: ciudades entran desde el sur/borde, dungeons "
                    "desde el centro, y hunts desde el oeste para flujo natural.",
            factors=[
                "Regla de diseño: entrada en borde sur para ciudades",
                "Conexión con caminos existentes del mapa global",
                "Distancia al temple/depot razonable para el jugador",
            ],
            alternatives=[
                "Entrada por el norte (rechazado: contra flujo natural)",
                "Múltiples entradas (rechazado: difícil de defender)",
            ],
            risk_level="low",
        )

    def _explain_empty(self, question: str, topic: str) -> DesignExplanation:
        return DesignExplanation(
            topic=topic,
            summary="Las zonas vacías fueron detectadas por el Quality Detector "
                    "y priorizadas para mejora. El Improvement Engine las rellenará "
                    "con contenido procedural en la siguiente iteración.",
            factors=[
                "Quality Detector score bajo activó FILL_EMPTY_ZONES",
                "Goal FIX_QUALITY prioridad 6 objetivo: score > 85",
                "Improvement programado para añadir contenido básico",
            ],
            alternatives=[
                "Dejar vacío (rechazado: baja calidad del mapa)",
                "Eliminar zona (rechazado: rompe conectividad)",
            ],
            risk_level="medium",
        )

    # ------------------------------------------------------------------
    # Topic extraction
    # ------------------------------------------------------------------

    def _extract_topic(self, question: str) -> str:
        """Extract the main topic from a question."""
        lower = question.lower()
        # Remove "why" / "por que" prefixes
        for prefix in ["por que ", "por qué ", "why ", "why is ", "why are ",
                       "why does ", "why was ", "why did ", "why would "]:
            if lower.startswith(prefix):
                lower = lower[len(prefix):]

        # Remove trailing punctuation and question words
        topic = lower.strip()\
            .replace("?", "")\
            .replace("¿", "")\
            .replace("this ", "")\
            .replace("there ", "")\
            .replace("a ", " ")\
            .replace("an ", " ")\
            .replace("the ", " ")\
            .replace("se cre", "")\
            .replace("existe ", "")\
            .strip()

        return topic.capitalize()

    # ------------------------------------------------------------------
    # Audit & summary
    # ------------------------------------------------------------------

    def audit_summary(self) -> Dict[str, Any]:
        return {
            "total_decisions": len(self._decision_log),
            "explanations_available": list(self._explanations.keys()),
            "recent_decisions": self.last_decisions(5),
        }

    def clear(self) -> None:
        self._decision_log.clear()
        self._explanations.clear()