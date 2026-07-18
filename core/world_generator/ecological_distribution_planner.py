from __future__ import annotations

from dataclasses import asdict, dataclass
from math import hypot
from typing import Any, Iterable

from core.world_generator.semantic_color_blueprint import BlueprintLayer, SemanticColorBlueprint


Position = tuple[int, int, int]


@dataclass(frozen=True)
class FamilyBudget:
    """Spatial budget for one semantic family backed by an official RME brush."""

    token: str
    habitats: tuple[str, ...]
    weight: float
    max_share: float
    min_distance: float
    cluster_span: int


KRAILOS_FAMILY_BUDGETS: tuple[FamilyBudget, ...] = (
    FamilyBudget("krailos_plant", ("oasis", "dry", "coast"), 0.38, 0.42, 2.0, 7),
    FamilyBudget("forest_shrub", ("oasis",), 0.16, 0.20, 2.0, 8),
    FamilyBudget("krailos_rocks", ("rocky", "dry", "coast"), 0.20, 0.24, 3.0, 10),
    FamilyBudget("dry_rock_detail", ("rocky", "dry"), 0.14, 0.18, 3.0, 11),
    FamilyBudget("krailos_mountains", ("rocky",), 0.07, 0.09, 6.0, 14),
    FamilyBudget("dark_fungi", ("rocky",), 0.05, 0.07, 4.0, 12),
)


class EcologicalDistributionPlanner:
    """Place official semantic brush families according to terrain ecology.

    This class never invents server item IDs. It only emits palette tokens that
    are already bound to brushes loaded from RME's ``data/materials`` catalog.
    """

    def apply(
        self,
        blueprint: SemanticColorBlueprint,
        plan: Any,
        *,
        available_tokens: Iterable[str],
    ) -> dict[str, Any]:
        if plan.policies.get("compact_objective_kind") != "krailos_island":
            report = {"status": "NOT_APPLICABLE", "profile": "default"}
            blueprint.metadata["ecological_distribution"] = report
            return report

        available = set(available_tokens)
        budgets = tuple(budget for budget in KRAILOS_FAMILY_BUDGETS if budget.token in available)
        missing = sorted(budget.token for budget in KRAILOS_FAMILY_BUDGETS if budget.token not in available)
        if missing:
            raise ValueError(f"Krailos ecology references unresolved official brush tokens: {missing}")

        terrain = blueprint.mask(BlueprintLayer.TERRAIN).cells
        blocked = self._blocked_positions(blueprint)
        candidates = {
            position: self._habitat(position, token, terrain)
            for position, token in terrain.items()
            if position not in blocked
        }
        nature = blueprint.mask(BlueprintLayer.NATURE).cells
        nature.clear()

        learned = float(plan.reference_style.get("nature_per_ground_tile", 0.075))
        requested = float(plan.policies.get("semantic_ai_nature_density", 0.45))
        requested = 0.035 + max(0.10, min(0.90, requested)) * 0.105
        density = max(0.035, min(0.105, learned * 0.70 + requested * 0.30))
        target_total = min(len(candidates), round(len(candidates) * density))
        quotas = self._quotas(target_total, budgets)

        occupied: dict[str, list[Position]] = {budget.token: [] for budget in budgets}
        for budget in sorted(budgets, key=lambda value: (value.max_share, value.token)):
            compatible = [
                position
                for position, habitat in candidates.items()
                if habitat in budget.habitats
            ]
            compatible.sort(
                key=lambda position: self._candidate_rank(
                    position, budget, candidates[position], plan.objective
                )
            )
            for position in compatible:
                if len(occupied[budget.token]) >= quotas[budget.token]:
                    break
                if not self._far_enough(position, occupied[budget.token], budget.min_distance):
                    continue
                nature[position] = budget.token
                occupied[budget.token].append(position)

        counts = {token: len(positions) for token, positions in occupied.items()}
        report = {
            "status": "PASS",
            "profile": "krailos_compact_ecology_v1",
            "eligible_tiles": len(candidates),
            "target_density": round(density, 6),
            "target_total": target_total,
            "placed_total": sum(counts.values()),
            "family_counts": counts,
            "family_quotas": quotas,
            "budgets": [asdict(budget) for budget in budgets],
            "habitat_counts": self._counts(candidates.values()),
            "blocked_tiles": len(blocked),
            "material_authority": "official RME palette tokens only",
        }
        blueprint.metadata["ecological_distribution"] = report
        return report

    @staticmethod
    def _blocked_positions(blueprint: SemanticColorBlueprint) -> set[Position]:
        hard_layers = (
            BlueprintLayer.ROAD,
            BlueprintLayer.STRUCTURE_GROUND,
            BlueprintLayer.WALL,
            BlueprintLayer.DOOR_WINDOW,
            BlueprintLayer.STAIRS_RAMP,
            BlueprintLayer.GAMEPLAY,
        )
        hard = {position for layer in hard_layers for position in blueprint.mask(layer).cells}
        protected = set(hard)
        for x, y, z in hard:
            protected.update((x + dx, y + dy, z) for dx in range(-2, 3) for dy in range(-2, 3))
        return protected

    @staticmethod
    def _habitat(position: Position, token: str, terrain: dict[Position, str]) -> str:
        x, y, z = position
        if token in {"krailos_grass", "grass"}:
            return "oasis"
        if token in {"mountain", "rock_soil", "krailos_yellow"}:
            return "rocky"
        if any((x + dx, y + dy, z) not in terrain for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            return "coast"
        return "dry"

    @staticmethod
    def _quotas(total: int, budgets: tuple[FamilyBudget, ...]) -> dict[str, int]:
        weight_total = sum(budget.weight for budget in budgets) or 1.0
        quotas: dict[str, int] = {}
        for budget in budgets:
            weighted = round(total * budget.weight / weight_total)
            quotas[budget.token] = max(0, min(weighted, round(total * budget.max_share)))
        return quotas

    @staticmethod
    def _candidate_rank(position: Position, budget: FamilyBudget, habitat: str, salt: str) -> tuple[int, int, int]:
        x, y, z = position
        cell_x, cell_y = x // budget.cluster_span, y // budget.cluster_span
        cluster = _stable_hash(cell_x, cell_y, z, f"{salt}:{budget.token}:cluster") % 100
        detail = _stable_hash(x, y, z, f"{salt}:{budget.token}:{habitat}")
        return cluster, detail, x * 65536 + y

    @staticmethod
    def _far_enough(position: Position, placed: list[Position], minimum: float) -> bool:
        if minimum <= 1.0:
            return True
        x, y, z = position
        return all(other_z != z or hypot(x - other_x, y - other_y) >= minimum for other_x, other_y, other_z in placed)

    @staticmethod
    def _counts(values: Iterable[str]) -> dict[str, int]:
        result: dict[str, int] = {}
        for value in values:
            result[value] = result.get(value, 0) + 1
        return dict(sorted(result.items()))


def _stable_hash(x: int, y: int, z: int, salt: str) -> int:
    value = x * 73_856_093 ^ y * 19_349_663 ^ z * 83_492_791
    value ^= sum((index + 1) * ord(character) for index, character in enumerate(salt))
    return abs(value)
