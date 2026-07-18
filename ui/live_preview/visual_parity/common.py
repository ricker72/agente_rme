"""
Shared WG-20U-C visual parity helpers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


DIRECTION_DELTAS = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}

CANONICAL_DATASETS = {
    "RME_BRUSH_INTELLIGENCE_CATALOG.json": ["RME_BRUSH_INTELLIGENCE_CATALOG.json"],
    "RME_AUTOMAPPING_RULES.json": [
        "RME_AUTOMAPPING_RULES.json",
        "WG20TC_AUTOMAPPING_RULES.json",
        "wg20tc_automapping_rules_v1.json",
    ],
    "RME_TRANSITION_RULES.json": [
        "RME_TRANSITION_RULES.json",
        "WG20TC_TRANSITION_RULES.json",
        "wg20tc_transition_rules_v1.json",
    ],
    "RME_COASTLINE_RULES.json": [
        "RME_COASTLINE_RULES.json",
        "WG20TC_COASTLINE_RULES.json",
    ],
    "RME_WALL_CONNECTION_RULES.json": [
        "RME_WALL_CONNECTION_RULES.json",
        "WG20TC_WALL_CONNECTION_RULES.json",
        "wg20tc_wall_rules_v1.json",
    ],
    "RME_STAIR_CONNECTION_RULES.json": [
        "RME_STAIR_CONNECTION_RULES.json",
        "WG20TC_STAIR_CONNECTION_RULES.json",
        "wg20te_stair_connectivity_rules_v1.json",
        "RME_STAIR_CONNECTIVITY_RULES.json",
    ],
    "RME_ROAD_PATTERN_RULES.json": [
        "RME_ROAD_PATTERN_RULES.json",
        "WG20TC_ROAD_PATTERN_RULES.json",
        "wg20tc_road_rules_v1.json",
    ],
}


class VisualParityDatasetLoader:
    """Loads certified datasets and records canonical alias resolution."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self.resolved_sources: Dict[str, str] = {}

    def load(self, canonical_name: str) -> Any:
        for candidate in CANONICAL_DATASETS.get(canonical_name, [canonical_name]):
            path = self.workspace_root / candidate
            if path.exists():
                self.resolved_sources[canonical_name] = candidate
                with open(path, "r", encoding="utf-8") as handle:
                    return json.load(handle)
        self.resolved_sources[canonical_name] = ""
        return {}

    def exists(self, name: str) -> bool:
        return bool(self.resolve(name))

    def resolve(self, name: str) -> str:
        for candidate in CANONICAL_DATASETS.get(name, [name]):
            if (self.workspace_root / candidate).exists():
                return candidate
        return ""


def normalize_role(tile: Mapping[str, Any]) -> str:
    return str(tile.get("semantic_role") or tile.get("role") or "").upper()


def normalize_brush(tile: Mapping[str, Any]) -> str:
    return str(tile.get("brush") or tile.get("source_brush") or "").lower()


def neighbor_list(neighbors: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"direction": direction, "tile": tile}
        for direction, tile in neighbors.items()
        if tile
    ]


def same_family(tile: Mapping[str, Any], other: Mapping[str, Any]) -> bool:
    return bool(other) and (
        normalize_role(tile) == normalize_role(other)
        or normalize_brush(tile) == normalize_brush(other)
    )


def trace_event(
    tile: Mapping[str, Any],
    *,
    source_rule: str,
    source_dataset: str,
    reason: str,
    correction: str,
    affected_tiles: Optional[Iterable[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "trace_id": tile.get("trace_id") or "WG20UC-TRACE",
        "event_id": tile.get("event_id") or f"WG20UC-{tile.get('x', 0)}-{tile.get('y', 0)}-{tile.get('floor', 7)}",
        "source_brush": tile.get("brush") or tile.get("source_brush") or normalize_role(tile).lower(),
        "source_rule": source_rule,
        "source_dataset": source_dataset,
        "reason": reason,
        "correction": correction,
        "affected_tiles": [
            {
                "x": other.get("x"),
                "y": other.get("y"),
                "floor": other.get("floor", other.get("z", 7)),
                "role": other.get("role") or other.get("semantic_role"),
                "brush": other.get("brush"),
            }
            for other in (affected_tiles or [])
        ],
    }
