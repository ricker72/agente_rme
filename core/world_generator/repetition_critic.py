from __future__ import annotations

from collections import Counter, deque
from math import hypot
from typing import Any

from core.world_generator.ecological_distribution_planner import KRAILOS_FAMILY_BUDGETS
from core.world_generator.semantic_color_blueprint import BlueprintLayer, SemanticColorBlueprint


Position = tuple[int, int, int]


class RepetitionCritic:
    """Reject semantic monoculture and machine-like repeated brush placement."""

    def repair(self, blueprint: SemanticColorBlueprint, plan: Any) -> dict[str, Any]:
        if plan.policies.get("compact_objective_kind") != "krailos_island":
            report = {"status": "NOT_APPLICABLE", "removed": 0}
            blueprint.metadata["repetition_critic"] = report
            return report

        cells = blueprint.mask(BlueprintLayer.NATURE).cells
        removed: Counter[str] = Counter()
        max_shares = {budget.token: budget.max_share for budget in KRAILOS_FAMILY_BUDGETS}
        minimum_distances = {budget.token: budget.min_distance for budget in KRAILOS_FAMILY_BUDGETS}
        total = len(cells)
        counts = Counter(cells.values())
        for token, count in counts.items():
            limit = max_shares.get(token, 0.45)
            if total <= 0 or count / total <= limit:
                continue
            # Solve (count - removed) / (total - removed) <= limit.  Using
            # count - round(total * limit) is insufficient because removing a
            # cell also changes the denominator.
            remove_count = int((count - limit * total) / (1.0 - limit))
            while (count - remove_count) / (total - remove_count) > limit:
                remove_count += 1
            positions = sorted(
                (position for position, value in cells.items() if value == token),
                key=lambda position: _stable_hash(position, f"{plan.objective}:{token}:trim"),
                reverse=True,
            )
            for position in positions[:remove_count]:
                cells.pop(position, None)
                removed[token] += 1
            total -= remove_count

        # Large same-family connected components read as stamped patterns even
        # when the official DoodadBrush randomizes its concrete sprite.
        for token in sorted(set(cells.values())):
            positions = {position for position, value in cells.items() if value == token}
            for component in _components(positions):
                if len(component) <= 10:
                    continue
                excess = sorted(
                    component,
                    key=lambda position: _stable_hash(position, f"{plan.objective}:{token}:component"),
                    reverse=True,
                )[10:]
                for position in excess:
                    cells.pop(position, None)
                    removed[token] += 1

        # Component repair changes the denominator again. Rebalance until all
        # family shares satisfy their final-map budgets, not their pre-repair
        # counts.
        for _ in range(64):
            current = Counter(cells.values())
            current_total = sum(current.values())
            offender = next(
                (
                    (token, count, max_shares.get(token, 0.45))
                    for token, count in sorted(current.items())
                    if current_total and count / current_total > max_shares.get(token, 0.45)
                ),
                None,
            )
            if offender is None:
                break
            token, count, limit = offender
            remove_count = int((count - limit * current_total) / (1.0 - limit))
            while (count - remove_count) / (current_total - remove_count) > limit:
                remove_count += 1
            positions = sorted(
                (position for position, value in cells.items() if value == token),
                key=lambda position: _stable_hash(position, f"{plan.objective}:{token}:rebalance"),
                reverse=True,
            )
            for position in positions[:remove_count]:
                cells.pop(position, None)
                removed[token] += 1

        audit = self.evaluate(blueprint)
        audit["removed"] = dict(sorted(removed.items()))
        audit["repair_passes"] = 1
        blueprint.metadata["repetition_critic"] = audit
        if audit["status"] != "PASS":
            raise ValueError(f"Semantic repetition critic blocked generation: {audit['issues']}")
        return audit

    def evaluate(self, blueprint: SemanticColorBlueprint) -> dict[str, Any]:
        cells = blueprint.mask(BlueprintLayer.NATURE).cells
        counts = Counter(cells.values())
        total = sum(counts.values())
        max_shares = {budget.token: budget.max_share for budget in KRAILOS_FAMILY_BUDGETS}
        minimum_distances = {budget.token: budget.min_distance for budget in KRAILOS_FAMILY_BUDGETS}
        issues: list[dict[str, Any]] = []
        for token, count in sorted(counts.items()):
            share = count / total if total else 0.0
            allowed = max_shares.get(token, 0.45)
            if share > allowed + 0.01:
                issues.append({"code": "FAMILY_BUDGET_EXCEEDED", "token": token, "share": round(share, 6), "limit": allowed})
        largest_components: dict[str, int] = {}
        for token in counts:
            positions = {position for position, value in cells.items() if value == token}
            largest = max((len(component) for component in _components(positions)), default=0)
            largest_components[token] = largest
            if largest > 10:
                issues.append({"code": "STAMPED_COMPONENT", "token": token, "size": largest, "limit": 10})
            minimum = minimum_distances.get(token, 1.0)
            spacing_violation = _first_spacing_violation(positions, minimum)
            if spacing_violation is not None:
                first, second, distance = spacing_violation
                issues.append({
                    "code": "MINIMUM_SPACING_VIOLATED",
                    "token": token,
                    "positions": [first, second],
                    "distance": round(distance, 6),
                    "minimum": minimum,
                })
        return {
            "status": "PASS" if not issues else "BLOCKED",
            "issues": issues,
            "family_counts": dict(sorted(counts.items())),
            "family_shares": {token: round(count / total, 6) for token, count in sorted(counts.items())} if total else {},
            "largest_components": dict(sorted(largest_components.items())),
        }


def _components(positions: set[Position]) -> list[set[Position]]:
    remaining = set(positions)
    result: list[set[Position]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            x, y, z = queue.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = (x + dx, y + dy, z)
                    if neighbor not in remaining:
                        continue
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def _first_spacing_violation(
    positions: set[Position], minimum: float
) -> tuple[Position, Position, float] | None:
    if minimum <= 1.0 or len(positions) < 2:
        return None
    buckets: dict[tuple[int, int, int], list[Position]] = {}
    cell_size = max(1, int(minimum))
    for position in sorted(positions):
        x, y, z = position
        bucket = (x // cell_size, y // cell_size, z)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in buckets.get((bucket[0] + dx, bucket[1] + dy, z), ()):
                    distance = hypot(x - other[0], y - other[1])
                    if distance < minimum:
                        return other, position, distance
        buckets.setdefault(bucket, []).append(position)
    return None


def _stable_hash(position: Position, salt: str) -> int:
    x, y, z = position
    value = x * 73_856_093 ^ y * 19_349_663 ^ z * 83_492_791
    value ^= sum((index + 1) * ord(character) for index, character in enumerate(salt))
    return abs(value)
