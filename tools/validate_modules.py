"""
tools/validate_modules.py — RC1.1 Module Discovery Validator (REAL).

Validates that all critical subsystems of Agente RME can be loaded.
Produces module_validation.json.

CRITERION: 100% of expected real modules load successfully.
"""

from __future__ import annotations
import sys
import json
import importlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "rc1.1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Real modules that exist in the project
EXPECTED_MODULES: Dict[str, List[str]] = {
    "Knowledge Engine": [
        "core.knowledge.knowledge_engine",
        "core.knowledge.knowledge_search",
        "core.knowledge.knowledge_index",
        "core.knowledge.knowledge_ranker",
    ],
    "Blueprint Intelligence": [
        "core.blueprints.blueprint_registry",
        "core.blueprints.blueprint_extractor",
        "core.blueprint_intelligence.blueprint_intelligence_engine",
        "core.blueprint_intelligence.blueprint_embedding_engine",
        "core.blueprint_intelligence.blueprint_evolution_engine",
        "core.blueprint_intelligence.blueprint_fusion_engine",
        "core.blueprint_intelligence.blueprint_similarity_engine",
    ],
    "Visual Critic": [
        "core.critic.visual_critic",
        "core.critic.critic_engine",
        "core.critic.score_calculator",
    ],
    "Autonomous": [
        "core.autonomous.autonomous_director",
        "core.autonomous.autonomous_world_designer",
        "core.autonomous.autonomous_planner",
        "core.autonomous.autonomous_decision_engine",
        "core.world_brain.world_brain",
    ],
    "OTBM": [
        "core.otbm.otbm_exporter",
        "core.otbm.otbm_importer",
        "core.otbm.otbm_writer",
        "core.otbm.otbm_reader",
    ],
    "Playtest": [
        "core.playtest.playtest_engine",
        "core.playtest.combat_simulator",
    ],
    "Balance": [
        "core.balance.balance_engine",
        "core.balance.difficulty_balancer",
        "core.balance.xp_balancer",
    ],
    "WorldModel": [
        "core.world.world_model",
        "core.world.world_validator",
        "core.procedural.world_synthesizer",
    ],
    "Architect": [
        "core.architect.ai_architect",
        "core.architect.world_planner",
        "core.planner.planner",
    ],
    "Lua": [
        "core.lua.lua_generator",
    ],
    "Analyzer": [
        "core.analyzer.map_analyzer",
        "core.analyzer.density_analyzer",
    ],
    "Generators": [
        "core.generators.world_generator",
        "core.generators.dungeon_generator",
        "core.generators.city_generator",
    ],
    "Export": [
        "core.export.release_builder",
    ],
    "Learning": [
        "core.learning.blueprint_learner",
        "core.learning.similarity_engine",
        "core.learning.pattern_miner",
    ],
    "Factory": [
        "core.factory.world_builder",
        "core.factory.expansion_factory",
    ],
    "Game Design": [
        "core.game_design.content_designer",
        "core.game_design.hunt_designer",
        "core.game_design.boss_designer",
    ],
    "World Engine": [
        "core.world_engine.world_engine",
        "core.world_engine.world_builder",
        "core.world_engine.export_pipeline",
    ],
    "Agents": [
        "core.agents.architect_agent",
        "core.agents.mapper_agent",
        "core.agents.expansion_agent",
        "core.agents.quest_agent",
        "core.agents.playtest_agent",
        "core.agents.balance_agent",
        "core.agents.critic_agent",
        "core.agents.orchestrator_agent",
        "core.agents.export_agent",
    ],
}


def load_module(name: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Try to import a module by name. Returns (success, error, version_info)."""
    try:
        mod = importlib.import_module(name)
        return True, None, getattr(mod, "__version__", "1.0")
    except Exception as e:
        return False, str(e), None


def validate() -> Dict[str, Any]:
    """Run validation across all expected modules."""
    results: Dict[str, Any] = {
        "version": "1.0.0-RC1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules_loaded": [],
        "modules_failed": [],
        "subsystems": {},
        "summary": {},
    }

    total_modules = 0
    for subsystem, modules in EXPECTED_MODULES.items():
        sub_result = {
            "modules": [],
            "loaded": 0,
            "failed": 0,
        }
        for mod_name in modules:
            total_modules += 1
            ok, err, ver = load_module(mod_name)
            entry = {
                "module": mod_name,
                "loaded": ok,
                "version": ver,
                "error": err,
            }
            sub_result["modules"].append(entry)
            if ok:
                sub_result["loaded"] += 1
                results["modules_loaded"].append(mod_name)
            else:
                sub_result["failed"] += 1
                results["modules_failed"].append(
                    {
                        "module": mod_name,
                        "error": err,
                    }
                )
        sub_result["status"] = (
            "OK"
            if sub_result["failed"] == 0
            else "PARTIAL"
            if sub_result["loaded"] > 0
            else "FAIL"
        )
        results["subsystems"][subsystem] = sub_result

    results["summary"] = {
        "total_expected": total_modules,
        "total_loaded": len(results["modules_loaded"]),
        "total_failed": len(results["modules_failed"]),
        "success_rate": (
            (len(results["modules_loaded"]) / total_modules)
            if total_modules > 0
            else 0.0
        ),
        "all_loaded": len(results["modules_failed"]) == 0,
    }
    results["criterion_pass"] = results["summary"]["all_loaded"]
    results["status"] = (
        "PASS"
        if results["summary"]["all_loaded"]
        else "PARTIAL"
        if results["summary"]["total_loaded"] > 0
        else "FAIL"
    )
    return results


def main() -> int:
    print("=" * 60)
    print("RC1.1 MODULE DISCOVERY VALIDATOR")
    print("=" * 60)
    results = validate()
    out_file = OUTPUT_DIR / "module_validation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Subsystems: {len(results['subsystems'])}")
    print(f"Loaded: {results['summary']['total_loaded']}")
    print(f"Failed: {results['summary']['total_failed']}")
    print(f"Success rate: {results['summary']['success_rate'] * 100:.1f}%")
    print(f"Status: {results['status']}")
    print(f"Output: {out_file}")
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
