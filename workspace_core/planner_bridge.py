"""Safe, cached bridge from Workspace Core to Planner knowledge services."""

from __future__ import annotations

import copy
import sqlite3
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from core.world_generator.planner_knowledge_database import PlannerKnowledgeDatabase
from core.world_generator.planner_visual_memory import PlannerVisualMemoryCache

if TYPE_CHECKING:
    from core.world_generator.mapper_planner import MapperPlan


class WorkspacePlannerBridge:
    """Read-only Planner context with bounded process-local caches."""

    def __init__(
        self,
        root: str | Path = ".",
        *,
        query_cache_limit: int = 128,
    ) -> None:
        self.root = Path(root).resolve()
        self.database_path = (
            self.root
            / "exports"
            / "planner_knowledge"
            / "RME_PLANNER_KNOWLEDGE.sqlite3"
        )
        self.memory_path = (
            self.root
            / "exports"
            / "planner_visual_memory"
            / "VISUAL_MEMORY_CACHE.json"
        )
        self.database = PlannerKnowledgeDatabase(self.database_path)
        self.visual_memory = PlannerVisualMemoryCache(self.memory_path)
        self.query_cache_limit = max(1, int(query_cache_limit))
        self._query_cache: OrderedDict[
            tuple[str, int, int], tuple[dict[str, Any], ...]
        ] = OrderedDict()
        self._memory_cache: dict[str, Any] | None = None
        self._memory_mtime_ns = -1
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_error = ""

    def ensure_database(self, *, build_if_missing: bool = False) -> dict[str, Any]:
        if self.database_path.is_file():
            return {
                "status": "PASS",
                "database": str(self.database_path),
                "existing": True,
            }
        if not build_if_missing:
            return {
                "status": "BLOCKED",
                "database": str(self.database_path),
                "reason": "planner database missing; explicit build required",
            }
        report = self.database.build(self.root)
        self.clear_cache()
        return report

    def search_materials(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        normalized = " ".join(query.lower().split())
        if not normalized:
            return []
        if not self.database_path.is_file():
            return []
        mtime = self.database_path.stat().st_mtime_ns
        key = (normalized, max(1, min(500, int(limit))), mtime)
        cached = self._query_cache.pop(key, None)
        if cached is not None:
            self.cache_hits += 1
            self._query_cache[key] = cached
            return [dict(row) for row in cached]
        self.cache_misses += 1
        try:
            rows = self.database.search_materials(normalized, key[1])
        except (OSError, sqlite3.Error, ValueError) as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return []
        self._query_cache[key] = tuple(dict(row) for row in rows)
        while len(self._query_cache) > self.query_cache_limit:
            self._query_cache.popitem(last=False)
        return [dict(row) for row in rows]

    def memory(self) -> dict[str, Any]:
        mtime = self.memory_path.stat().st_mtime_ns if self.memory_path.is_file() else -1
        if self._memory_cache is not None and mtime == self._memory_mtime_ns:
            self.cache_hits += 1
            return copy.deepcopy(self._memory_cache)
        self.cache_misses += 1
        payload = self.visual_memory.load()
        self._memory_cache = dict(payload)
        self._memory_mtime_ns = mtime
        return copy.deepcopy(payload)

    def create_plan(self, objective: str) -> tuple["MapperPlan", dict[str, Any]]:
        from core.world_generator.hierarchical_architectural_planner import (
            HierarchicalArchitecturalPlanner,
        )
        from core.world_generator.mapper_planner import build_mapper_plan

        memory = self.memory()
        plan = build_mapper_plan(
            city_blueprint={},
            hunt_blueprint={},
            semantic_plan=SimpleNamespace(objective=objective),
            world_style_profile={
                "visual_memory": memory.get("learned_priors", {}),
                "memory_format": memory.get("format", ""),
            },
        )
        try:
            hierarchy = HierarchicalArchitecturalPlanner(self.root).enrich(plan)
        except (OSError, sqlite3.Error, ValueError) as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            hierarchy = {"status": "BLOCKED", "reason": self.last_error}
        return plan, {
            "status": "PASS" if hierarchy.get("status") == "PASS" else "BLOCKED",
            "proposal_only": True,
            "writes_tiles_directly": False,
            "knowledge_database": str(self.database_path),
            "visual_memory": str(self.memory_path),
            "hierarchy": hierarchy,
            "plan": plan.to_report(),
        }

    def clear_cache(self) -> None:
        self._query_cache.clear()
        self._memory_cache = None
        self._memory_mtime_ns = -1

    def audit(self) -> dict[str, object]:
        return {
            "workspace_planner_bridge_ready": True,
            "proposal_only": True,
            "database_available": self.database_path.is_file(),
            "visual_memory_available": self.memory_path.is_file(),
            "query_cache_entries": len(self._query_cache),
            "query_cache_limit": self.query_cache_limit,
            "memory_cached": self._memory_cache is not None,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "last_error": self.last_error,
        }


__all__ = ["WorkspacePlannerBridge"]
