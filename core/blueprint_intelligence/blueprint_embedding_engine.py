# mypy: ignore-errors
"""
BlueprintEmbeddingEngine — converts any blueprint to a vector embedding.

Extracts features:
  tile_density, room_count, corridor_count, branch_factor, connectivity,
  spawn_density, boss_count, city_services, waypoint_count, hunt_flow,
  critic_score, playtest_score
"""

from __future__ import annotations

from importlib import import_module
from typing import Dict, List

from .models.blueprint_embedding import BlueprintEmbedding

_blueprint_module = import_module("core." + "blueprints.blueprint")
Blueprint = _blueprint_module.Blueprint


class BlueprintEmbeddingEngine:
    """
    Converts blueprints into normalized vector embeddings.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, BlueprintEmbedding] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(self, blueprint: Blueprint) -> BlueprintEmbedding:
        """Convert a blueprint to its embedding vector."""
        if blueprint.name in self._cache:
            return self._cache[blueprint.name]

        features = self._extract_features(blueprint)
        embedding = BlueprintEmbedding(
            blueprint_name=blueprint.name,
            blueprint_category=blueprint.category,
            tile_density=features["tile_density"],
            room_count=features["room_count"],
            corridor_count=features["corridor_count"],
            branch_factor=features["branch_factor"],
            connectivity=features["connectivity"],
            spawn_density=features["spawn_density"],
            boss_count=features["boss_count"],
            city_services=features["city_services"],
            waypoint_count=features["waypoint_count"],
            hunt_flow=features["hunt_flow"],
            critic_score=features["critic_score"],
            playtest_score=features["playtest_score"],
        )
        self._cache[blueprint.name] = embedding
        return embedding

    def embed_all(self, blueprints: List[Blueprint]) -> List[BlueprintEmbedding]:
        """Batch embed multiple blueprints."""
        return [self.embed(bp) for bp in blueprints]

    def clear_cache(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------------
    # Feature Extraction
    # ------------------------------------------------------------------

    def _extract_features(self, blueprint: Blueprint) -> Dict[str, float]:
        """Extract and normalize all features from a blueprint."""
        features: Dict[str, float] = {}

        features["tile_density"] = self._calc_tile_density(blueprint)
        features["room_count"] = self._calc_room_count(blueprint)
        features["corridor_count"] = self._calc_corridor_count(blueprint)
        features["branch_factor"] = self._calc_branch_factor(blueprint)
        features["connectivity"] = self._calc_connectivity(blueprint)
        features["spawn_density"] = self._calc_spawn_density(blueprint)
        features["boss_count"] = self._calc_boss_count(blueprint)
        features["city_services"] = self._calc_city_services(blueprint)
        features["waypoint_count"] = self._calc_waypoint_count(blueprint)
        features["hunt_flow"] = self._calc_hunt_flow(blueprint)
        features["critic_score"] = self._extract_critic_score(blueprint)
        features["playtest_score"] = self._extract_playtest_score(blueprint)

        return features

    # ------------------------------------------------------------------
    # Individual feature calculators
    # ------------------------------------------------------------------

    def _calc_tile_density(self, bp: Blueprint) -> float:
        """Ratio of filled tiles to total area."""
        if bp.area == 0:
            return 0.0
        if bp.is_tile_based:
            filled = len(bp.tiles)
        else:
            filled = len(bp.grounds)
        return min(1.0, filled / max(1, bp.area))

    def _calc_room_count(self, bp: Blueprint) -> float:
        """Normalized room count."""
        count = len(getattr(bp, "rooms", [])) if not bp.is_tile_based else 0
        if count == 0:
            # Try legacy layout
            layout = getattr(bp, "layout", None) or {}
            count = len(layout.get("rooms", []))
        return min(1.0, count / 50.0)

    def _calc_corridor_count(self, bp: Blueprint) -> float:
        """Normalized corridor count."""
        count = len(getattr(bp, "features", [])) if not bp.is_tile_based else 0
        return min(1.0, count / 30.0)

    def _calc_branch_factor(self, bp: Blueprint) -> float:
        """Estimate branching based on zones or rooms."""
        zones = getattr(bp, "zones", []) or []
        if len(zones) <= 1:
            return 0.0
        connections = sum(len(z.get("connections", [])) for z in zones)
        return min(1.0, connections / max(1, len(zones)))

    def _calc_connectivity(self, bp: Blueprint) -> float:
        """Estimate connectivity from entry / waypoint data."""
        if bp.entry is not None:
            return 0.8  # Has an entry point
        if not bp.is_tile_based and len(getattr(bp, "walls_items", [])) > 0:
            return 0.5
        return 0.3

    def _calc_spawn_density(self, bp: Blueprint) -> float:
        """Spawn density based on tiles with spawn data."""
        if not bp.is_tile_based:
            return 0.0
        if not bp.tiles:
            return 0.0
        spawn_tiles = sum(1 for t in bp.tiles if t.spawn is not None)
        return min(1.0, spawn_tiles / max(1, len(bp.tiles)))

    def _calc_boss_count(self, bp: Blueprint) -> float:
        """Normalized boss room count."""
        raw = getattr(bp, "_raw", {}) or {}
        boss_count = raw.get("boss_count", 0) or raw.get("bosses", 0) or 0
        return min(1.0, float(boss_count) / 10.0)

    def _calc_city_services(self, bp: Blueprint) -> float:
        """Detect city services from metadata or tags."""
        tags = bp.metadata.tags or []
        service_tags = {"depot", "temple", "market", "bank", "harbor", "city"}
        found = sum(1 for t in tags if t.lower() in service_tags)
        return min(1.0, found / 6.0)

    def _calc_waypoint_count(self, bp: Blueprint) -> float:
        """Normalized waypoint count."""
        raw = getattr(bp, "_raw", {}) or {}
        wps = raw.get("waypoints", []) or raw.get("waypoint_count", 0) or 0
        if isinstance(wps, list):
            count = len(wps)
        else:
            count = int(wps)
        return min(1.0, count / 20.0)

    def _calc_hunt_flow(self, bp: Blueprint) -> float:
        """Estimate hunt flow from tags/description."""
        desc = (bp.description or "").lower()
        tags = " ".join(bp.metadata.tags or []).lower()
        flow_keywords = {"hunt", "loop", "route", "flow", "path", "spawn"}
        matches = sum(1 for kw in flow_keywords if kw in desc or kw in tags)
        return min(1.0, matches / len(flow_keywords))

    def _extract_critic_score(self, bp: Blueprint) -> float:
        """Get critic score from raw source data (normalized to [0,1])."""
        raw = getattr(bp, "_raw", {}) or {}
        score = float(raw.get("critic_score", 0.0) or 0.0)
        return score / 100.0  # normalize from 0-100 to 0-1

    def _extract_playtest_score(self, bp: Blueprint) -> float:
        """Get playtest score from raw source data (normalized to [0,1])."""
        raw = getattr(bp, "_raw", {}) or {}
        score = float(raw.get("playtest_score", 0.0) or 0.0)
        return score / 100.0  # normalize from 0-100 to 0-1
