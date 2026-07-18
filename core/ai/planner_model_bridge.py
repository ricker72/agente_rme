"""Bidirectional, bounded dialogue between the deterministic Planner and models."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PlannerCritique:
    status: str
    issues: tuple[dict[str, str], ...]
    reference_facts: tuple[str, ...]


class PlannerResponseCritic:
    """Reject semantically incomplete guidance using coordinate-free evidence."""

    def critique(
        self,
        objective: str,
        guidance: Mapping[str, Any],
        reference_brief: Mapping[str, Any],
    ) -> PlannerCritique:
        text = " ".join([
            str(guidance.get("summary", "")),
            *[str(item) for key in ("architecture_rules", "biome_rules", "qa_intent") for item in guidance.get(key, ())],
            *[
                " ".join(str(item.get(key, "")) for key in ("zone_role", "reason", "ground_key", "wall_key"))
                for item in guidance.get("material_intents", ()) if isinstance(item, Mapping)
            ],
        ]).casefold()
        objective_tokens = _tokens(objective)
        roles = {str(item.get("zone_role", "")).casefold() for item in guidance.get("material_intents", ()) if isinstance(item, Mapping)}
        issues: list[dict[str, str]] = []
        required_roles: set[str] = set()
        if objective_tokens & {"city", "town", "ciudad", "depot", "temple", "tiendas", "shops", "houses", "casas"}:
            required_roles.update({"city", "road"})
        if objective_tokens & {"hunt", "hunts", "spawn", "respawn", "boss"}:
            required_roles.add("hunt")
        if objective_tokens & {"sea", "water", "coast", "island", "mar", "agua", "costa", "isla"}:
            required_roles.add("coast")
        missing_roles = sorted(required_roles - roles)
        if missing_roles:
            issues.append({
                "code": "MISSING_ZONE_ROLE",
                "message": f"Faltan intenciones materiales para: {', '.join(missing_roles)}.",
                "correction": "Agrega esos zone_role usando exclusivamente keys del catalogo certificado.",
            })
        intents = [item for item in guidance.get("material_intents", ()) if isinstance(item, Mapping)]
        if not intents or not any(item.get("ground_key") for item in intents):
            issues.append({
                "code": "MISSING_GROUND_INTENT",
                "message": "La propuesta no define GroundBrush contextual.",
                "correction": "Selecciona ground_key certificado por zona; el Brush Engine resolvera IDs y AutoBorders.",
            })
        requested_features = {
            "depot": {"depot", "depots"}, "temple": {"temple", "temples", "templo", "templos"},
            "npc": {"npc", "npcs"}, "quest": {"quest", "quests"},
            "shops": {"shop", "shops", "tienda", "tiendas"},
            "houses": {"house", "houses", "casa", "casas"},
            "mountain": {"mountain", "mountains", "montana", "montanas"},
            "bridge": {"bridge", "bridges", "puente", "puentes"},
        }
        for label, aliases in requested_features.items():
            if objective_tokens & aliases and not any(alias in text for alias in aliases):
                issues.append({
                    "code": "MISSING_REQUESTED_FEATURE",
                    "message": f"La guia omite la funcion solicitada: {label}.",
                    "correction": f"Incluye una regla abstracta y QA para {label}, sin copiar geometria fuente.",
                })
        facts = tuple(_reference_facts(reference_brief))
        return PlannerCritique("PASS" if not issues else "NEEDS_CORRECTION", tuple(issues[:8]), facts[:8])


class PlannerModelBridge:
    """Run model -> Planner critique -> correction, with bounded retries and audit."""

    def __init__(self, models: Any, experience: Any, *, max_rounds: int = 2) -> None:
        self.models = models
        self.experience = experience
        self.max_rounds = max(1, min(3, int(max_rounds)))
        self.critic = PlannerResponseCritic()

    def plan(
        self, objective: str, *, context: dict[str, Any], mode: str
    ) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        working_context = dict(context)
        dialogue: list[dict[str, Any]] = []
        for round_index in range(1, self.max_rounds + 1):
            result = self.models.propose(objective, context=working_context, mode=mode)
            guidance = result.get("guidance", {})
            if not guidance:
                self._record(objective, session_id, round_index, result, "PROVIDER_FALLBACK", ())
                result["planner_bridge"] = {"session_id": session_id, "status": "FALLBACK", "rounds": dialogue}
                return result
            critique = self.critic.critique(
                objective, guidance, context.get("certified_reference_brief", {})
            )
            dialogue.append({
                "round": round_index,
                "planner_status": critique.status,
                "issues": list(critique.issues),
                "reference_facts": list(critique.reference_facts),
            })
            self._record(objective, session_id, round_index, result, critique.status, critique.issues)
            if critique.status == "PASS":
                result["planner_bridge"] = {
                    "session_id": session_id, "status": "CERTIFIED", "rounds": dialogue,
                    "model_weights_modified": False, "knowledge_retrieved_each_round": True,
                }
                return result
            working_context["planner_feedback"] = {
                "round": round_index,
                "issues": list(critique.issues),
                "reference_facts": list(critique.reference_facts),
                "instruction": "Corrige la guia; no inventes IDs, materiales ni geometria.",
                "preserve_zone_roles": sorted(roles_from_guidance(guidance)),
                "preserve_rules": [
                    str(item)[:240]
                    for key in ("architecture_rules", "biome_rules")
                    for item in guidance.get(key, ())
                ][:12],
            }
        return {
            "status": "PLANNER_BLOCKED",
            "provider": result.get("provider", ""),
            "model": result.get("model", ""),
            "guidance": {},
            "errors": [
                {"provider": "planner", "code": str(issue.get("code", "SEMANTIC_REJECTION"))}
                for issue in dialogue[-1].get("issues", ())
            ],
            "secrets_exposed": False,
            "writes_tiles_directly": False,
            "planner_bridge": {
                "session_id": session_id, "status": "BLOCKED", "rounds": dialogue,
                "model_weights_modified": False, "knowledge_retrieved_each_round": True,
            },
        }

    def _record(
        self, objective: str, session_id: str, round_index: int, result: Mapping[str, Any], status: str,
        issues: Any,
    ) -> None:
        try:
            self.experience.record_ai_bridge_event(
                session_id=session_id,
                phase="planner_dialogue",
                round_index=round_index,
                provider=str(result.get("provider", "")),
                model=str(result.get("model", "")),
                status=status,
                objective_hash=hashlib.sha256(objective.encode("utf-8")).hexdigest(),
                critique={"issues": list(issues)},
                response_hash=hashlib.sha256(
                    json.dumps(result.get("guidance", {}), sort_keys=True, default=str).encode("utf-8")
                ).hexdigest(),
            )
        except Exception:
            # Audit failure must not take down planning; server diagnostics expose counts.
            return


def _reference_facts(reference_brief: Mapping[str, Any]):
    for town in list(reference_brief.get("world_towns", ()))[:2]:
        if not isinstance(town, Mapping):
            continue
        name = str(town.get("town", "reference town"))
        floor7 = next((row for row in town.get("floor_environment", ()) if row.get("floor") == 7), None)
        if floor7:
            yield (
                f"{name} z7 measured ratios: nature={float(floor7.get('nature_ratio', 0)):.3f}, "
                f"water={float(floor7.get('water_ratio', 0)):.3f}, edges={float(floor7.get('edge_density', 0)):.3f}."
            )
        counts = town.get("structure_counts", {})
        if isinstance(counts, Mapping):
            summary = ", ".join(f"{key}={int(value)}" for key, value in list(counts.items())[:7])
            if summary:
                yield f"{name} observed structure counts (style evidence only): {summary}."
    for reference in list(reference_brief.get("reference_maps", ()))[:2]:
        if not isinstance(reference, Mapping):
            continue
        brushes = [str(row.get("name", "")) for row in reference.get("dominant_brushes", ())[:6] if isinstance(row, Mapping)]
        if brushes:
            yield f"{reference.get('name', 'reference')} dominant brush families: {', '.join(brushes)}."


def _tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", str(value).casefold()).encode("ascii", "ignore").decode("ascii")
    return {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 2}


def roles_from_guidance(guidance: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("zone_role", "")).strip().casefold()
        for item in guidance.get("material_intents", ()) if isinstance(item, Mapping) and item.get("zone_role")
    }


__all__ = ["PlannerCritique", "PlannerModelBridge", "PlannerResponseCritic"]
