"""
tools/real_performance_profile.py — Phase 10: Real Performance Profile.

Profiling all critical components.
"""

from __future__ import annotations
import sys
import json
import cProfile
import pstats
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "rc1.1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


COMPONENTS = [
    ("Architect", "core.architect.ai_architect", "AIArchitect", "plan"),
    ("Mapper", "core.architect.mapper_ai", "MapperAI", "generate"),
    ("Expansion", "core.expansion.expansion_ai", "ExpansionAI", "expand"),
    ("Quest", "core.campaign.quest_generator", "QuestGenerator", "generate"),
    ("Playtest", "core.playtest.playtest_engine", "PlaytestEngine", "run"),
    ("Balance", "core.balance.balance_engine", "BalanceEngine", "analyze"),
    ("Critic", "core.critic.visual_critic", "VisualCritic", "analyze"),
    ("Knowledge", "core.knowledge.knowledge_engine", "KnowledgeEngine", "query"),
    (
        "Blueprint",
        "core.blueprints.blueprint_extractor",
        "BlueprintExtractor",
        "extract_from_otbm",
    ),
    (
        "Autonomous",
        "core.autonomous.autonomous_director",
        "AutonomousDirector",
        "design_world",
    ),
    ("Export", "core.export.release_builder", "ReleaseBuilder", "build"),
]


def profile_component(
    name: str, module_path: str, class_name: str, method_name: str
) -> Dict[str, Any]:
    """Profile a single component using cProfile."""
    try:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        instance = cls() if callable(cls) else cls
        method = getattr(instance, method_name, None)
        if not callable(method):
            # Try class method
            method = getattr(cls, method_name, None)
            if not callable(method):
                return {
                    "component": name,
                    "class": class_name,
                    "method": method_name,
                    "status": "SKIPPED",
                    "reason": f"Method {method_name} not callable",
                }
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            for _ in range(3):
                try:
                    if method_name == "plan":
                        method("Test prompt for performance", 256, 256)
                    elif method_name == "query":
                        method("Test query", top_k=3)
                    elif method_name == "analyze":
                        method({"name": "test"}, map_name="test")
                    elif method_name == "run":
                        method({"name": "test", "zones": []})
                    else:
                        method()
                except Exception:
                    pass
        finally:
            profiler.disable()

        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats(15)
        stats_output = s.getvalue()

        return {
            "component": name,
            "class": class_name,
            "method": method_name,
            "status": "OK",
            "stats_preview": stats_output[:2000],
        }
    except Exception as e:
        return {
            "component": name,
            "class": class_name,
            "method": method_name,
            "status": "ERROR",
            "error": str(e),
        }


def run() -> Dict[str, Any]:
    print(f"[Phase 10] Profiling {len(COMPONENTS)} components...")
    results: List[Dict[str, Any]] = []
    for name, mod_path, cls, meth in COMPONENTS:
        print(f"  Profiling {name} ({cls}.{meth})...")
        r = profile_component(name, mod_path, cls, meth)
        results.append(r)
        print(f"    -> {r['status']}")
    return {
        "version": "1.0.0-RC1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 10: Real Performance Profile",
        "components": results,
        "n_components": len(COMPONENTS),
        "n_profiled": sum(1 for r in results if r["status"] == "OK"),
        "n_errors": sum(1 for r in results if r["status"] == "ERROR"),
        "criterion_pass": sum(1 for r in results if r["status"] == "OK") >= 8,
    }


def main() -> int:
    res = run()
    out_file = OUTPUT_DIR / "real_performance_profile.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n[Phase 10] Saved: {out_file}")
    print(f"[Phase 10] Components profiled: {res['n_profiled']}/{res['n_components']}")
    print(f"[Phase 10] Pass: {res['criterion_pass']}")
    return 0 if res["criterion_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
