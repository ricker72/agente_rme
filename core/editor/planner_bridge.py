"""Cached bridge between desktop clients and planner knowledge services."""

from __future__ import annotations

import copy
import json
import sqlite3
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from core.world_generator.planner_knowledge_database import PlannerKnowledgeDatabase
from core.world_generator.planner_visual_memory import PlannerVisualMemoryCache
from core.world_generator.experience_learning_loop import ExperienceLearningLoop
from core.world_generator.planner_database_client import PlannerDatabaseClient
from core.world_generator.planner_material_brief import CertifiedMaterialBriefBuilder
from core.ai.model_provider_orchestrator import ModelProviderOrchestrator

if TYPE_CHECKING:
    from core.world_generator.mapper_planner import MapperPlan


class WorkspacePlannerBridge:
    def __init__(self, root: str | Path = ".", *, query_cache_limit: int = 128) -> None:
        self.root = Path(root).resolve()
        self.database_path = self.root / "exports" / "planner_knowledge" / "RME_PLANNER_KNOWLEDGE.sqlite3"
        self.experience_path = self.root / "exports" / "planner_knowledge" / "RME_PLANNER_EXPERIENCE.sqlite3"
        self.memory_path = self.root / "exports" / "planner_visual_memory" / "VISUAL_MEMORY_CACHE.json"
        self.database = PlannerKnowledgeDatabase(self.database_path)
        try:
            self.experience = PlannerDatabaseClient(self.root)
            self.database_server_mode = "LOCAL_SERVER"
        except (OSError, RuntimeError, ValueError):
            self.experience = ExperienceLearningLoop(self.experience_path)
            self.database_server_mode = "DIRECT_FALLBACK"
        self.visual_memory = PlannerVisualMemoryCache(self.memory_path)
        self.model_orchestrator = ModelProviderOrchestrator(self.root)
        self.query_cache_limit = max(1, int(query_cache_limit))
        self._query_cache: OrderedDict[tuple[str, int, int], tuple[dict[str, Any], ...]] = OrderedDict()
        self._memory_cache: dict[str, Any] | None = None
        self._memory_mtime_ns = -1
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_error = ""

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

    def search_materials(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        normalized = " ".join(str(query).lower().split())
        if not normalized or not self.database_path.is_file():
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
            if self.database_server_mode == "LOCAL_SERVER":
                rows = tuple(dict(row) for row in self.experience.search_materials(normalized, key[1]))
            else:
                rows = tuple(dict(row) for row in self.database.search_materials(normalized, key[1]))
        except (OSError, sqlite3.Error, ValueError) as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return []
        self._query_cache[key] = rows
        while len(self._query_cache) > self.query_cache_limit:
            self._query_cache.popitem(last=False)
        return [dict(row) for row in rows]

    def create_plan(self, objective: str) -> tuple["MapperPlan", dict[str, Any]]:
        from core.world_generator.hierarchical_architectural_planner import HierarchicalArchitecturalPlanner
        from core.world_generator.mapper_planner import build_mapper_plan

        memory = self.memory()
        experience_guidance = self.experience.guidance(objective)
        reference_archetypes: list[dict[str, Any]] = []
        reference_scans: list[dict[str, Any]] = []
        world_town_scans: list[dict[str, Any]] = []
        quest_script_patterns: list[dict[str, Any]] = []
        if self.database_path.is_file():
            queries = (
                ("reference_archetypes", self.database.reference_archetypes),
                ("reference_scans", self.database.reference_scans),
                ("world_town_scans", self.database.world_town_scans),
                ("quest_script_patterns", self.database.quest_script_patterns),
            )
            results: dict[str, list[dict[str, Any]]] = {}
            for name, query in queries:
                try:
                    results[name] = query(objective)
                except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError) as exc:
                    self.last_error = f"{name}: {type(exc).__name__}: {exc}"
                    results[name] = []
            reference_archetypes = results["reference_archetypes"]
            reference_scans = results["reference_scans"]
            world_town_scans = results["world_town_scans"]
            quest_script_patterns = results["quest_script_patterns"]
        ai_context = {
            "positive_rule_count": len(experience_guidance.get("positive_rules", ())),
            "negative_constraint_count": len(experience_guidance.get("negative_constraints", ())),
            "reference_names": [row.get("name", "") for row in reference_archetypes[:12]],
            "town_names": [row.get("town", "") for row in world_town_scans[:12]],
            "visual_tags": sorted(memory.get("learned_priors", {}).get("profiles_by_tag", {}))[:20],
        }
        material_brief: dict[str, Any] = {}
        reference_brief: dict[str, Any] = {}
        technical_grammar: dict[str, Any] = {}
        try:
            material_brief = (
                self.experience.material_brief(objective)
                if self.database_server_mode == "LOCAL_SERVER"
                else CertifiedMaterialBriefBuilder(self.database_path).build(objective)
            )
        except (OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
            self.last_error = f"Material brief: {type(exc).__name__}: {exc}"
        try:
            if self.database_server_mode == "LOCAL_SERVER":
                reference_brief = self.experience.reference_brief(objective)
            else:
                from core.world_generator.planner_reference_brief import CertifiedReferenceBriefBuilder

                reference_brief = CertifiedReferenceBriefBuilder(self.database_path).build(objective)
        except (OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
            self.last_error = f"Reference brief: {type(exc).__name__}: {exc}"
        try:
            technical_grammar = self.database.rme_technical_grammar(objective)
        except (OSError, RuntimeError, ValueError, sqlite3.Error, json.JSONDecodeError) as exc:
            self.last_error = f"RME grammar: {type(exc).__name__}: {exc}"
        ai_context["certified_material_brief"] = material_brief
        ai_context["certified_reference_brief"] = reference_brief
        ai_context["certified_rme_grammar"] = technical_grammar
        ai_context["validated_experience_rules"] = experience_guidance
        try:
            ai_proposal = (
                self.experience.ai_plan(objective, context=ai_context)
                if self.database_server_mode == "LOCAL_SERVER"
                else self.model_orchestrator.propose(objective, context=ai_context)
            )
        except (OSError, RuntimeError, ValueError) as exc:
            self.last_error = f"AI gateway: {type(exc).__name__}: {exc}"
            ai_proposal = self.model_orchestrator.propose(objective, context=ai_context)
        plan = build_mapper_plan(
            city_blueprint={},
            hunt_blueprint={},
            semantic_plan=SimpleNamespace(objective=objective),
            world_style_profile={
                "visual_memory": memory.get("learned_priors", {}),
                "memory_format": memory.get("format", ""),
                "reference_corpus": {
                    "archetypes": reference_archetypes,
                    "scanner_reports": reference_scans,
                    "world_town_scans": world_town_scans,
                    "variation_policy": "resample proportions and topology; never replay source coordinates",
                    "similarity_guard_required": True,
                },
                "quest_script_knowledge": {
                    "patterns": quest_script_patterns,
                    "source": "sqlite",
                    "executes_lua": False,
                    "returns_source_code": False,
                },
                "certified_material_catalog": {
                    "status": material_brief.get("status", "UNAVAILABLE"),
                    "catalog_hash": material_brief.get("catalog_hash", ""),
                    "materials": {
                        str(row.get("key")): {
                            "name": str(row.get("name", "")),
                            "type": str(row.get("type", "")),
                        }
                        for row in material_brief.get("brushes", ())
                        if isinstance(row, dict) and row.get("key")
                    },
                    "contains_raw_ids": False,
                },
                "certified_rme_grammar": technical_grammar,
                "certified_reference_grammar": {
                    "status": reference_brief.get("status", "UNAVAILABLE"),
                    "brief_hash": reference_brief.get("brief_hash", ""),
                    "reference_maps": [row.get("name", "") for row in reference_brief.get("reference_maps", ())],
                    "world_towns": [row.get("town", "") for row in reference_brief.get("world_towns", ())],
                    "source_geometry_included": False,
                },
            },
            experience_guidance=experience_guidance,
            semantic_ai_guidance=ai_proposal.get("guidance", {}),
        )
        plan.reference_style.setdefault("semantic_ai", {})["proposal_id"] = str(ai_proposal.get("proposal_id", ""))
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
            "experience_database": str(self.experience_path),
            "database_server_mode": self.database_server_mode,
            "experience_guidance": {
                "positive_rules": len(experience_guidance.get("positive_rules", ())),
                "negative_constraints": len(experience_guidance.get("negative_constraints", ())),
                "stores_source_geometry": experience_guidance.get("stores_source_geometry"),
            },
            "semantic_ai": {
                "status": ai_proposal.get("status"),
                "provider": ai_proposal.get("provider"),
                "model": ai_proposal.get("model"),
                "applied": bool(plan.policies.get("semantic_ai_applied")),
                "writes_tiles_directly": False,
                "errors": ai_proposal.get("errors", []),
                "contributors": ai_proposal.get("contributors", []),
                "agreement": ai_proposal.get("agreement", {}),
                "material_grounding": {
                    "status": material_brief.get("status", "UNAVAILABLE"),
                    "catalog_hash": material_brief.get("catalog_hash", ""),
                    "allowed_key_count": len(material_brief.get("allowed_material_keys", ())),
                    "model_writes_ids": False,
                    "placement_authority": "RME Brush Engine",
                },
                "reference_grounding": {
                    "status": reference_brief.get("status", "UNAVAILABLE"),
                    "brief_hash": reference_brief.get("brief_hash", ""),
                    "reference_maps": [row.get("name", "") for row in reference_brief.get("reference_maps", ())],
                    "world_towns": [row.get("town", "") for row in reference_brief.get("world_towns", ())],
                    "source_geometry_included": False,
                },
                "proposal_id": ai_proposal.get("proposal_id", ""),
            },
            "reference_archetypes": [row["name"] for row in reference_archetypes],
            "reference_scans": [row["map"] for row in reference_scans],
            "world_town_scans": [row["town"] for row in world_town_scans],
            "quest_script_patterns": [row["name"] for row in quest_script_patterns],
            "reference_scanner": {
                "source": "sqlite",
                "loads_world_otbm": False,
                "returns_source_layout": False,
            },
            "world_town_scanner": {
                "source": "sqlite",
                "loads_world_otbm": False,
                "floors": list(range(16)),
                "krailos_excluded": True,
            },
            "quest_script_scanner": {
                "source": "sqlite",
                "loads_server_scripts": False,
                "executes_lua": False,
                "returns_source_code": False,
            },
            "hierarchy": hierarchy,
            "plan": plan.to_report(),
        }

    def audit(self) -> dict[str, object]:
        return {
            "planner_bridge_ready": True,
            "database_available": self.database_path.is_file(),
            "visual_memory_available": self.memory_path.is_file(),
            "experience_learning": self.experience.audit(),
            "semantic_ai": self.model_orchestrator.audit(),
            "database_server_mode": self.database_server_mode,
            "reference_corpus_available": self.database_path.is_file(),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "last_error": self.last_error,
        }

    def ai_preferences(self) -> dict[str, Any]:
        if self.database_server_mode == "LOCAL_SERVER":
            return self.experience.ai_preferences()
        return {"status": "PASS", "mode": "auto"}

    def set_ai_mode(self, mode: str) -> dict[str, Any]:
        if self.database_server_mode != "LOCAL_SERVER":
            raise RuntimeError("AI preferences require the local Planner server")
        return self.experience.set_ai_mode(mode)


__all__ = ["WorkspacePlannerBridge"]
