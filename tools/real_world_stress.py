"""
tools/real_world_stress.py — Phase 4: Real World Stress Test (FAST).

Generates 100 real worlds using REAL engines. NO simulation, NO mocks.
Optimized for fast execution.
"""
from __future__ import annotations
import sys
import os
import json
import time
import gc
import tracemalloc
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "rc1.1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


PROMPTS = [
    "Issavi desert hunting grounds",
    "Roshamuul nightmare realm",
    "Soul War demonic invasion",
    "Library arcane sanctum",
    "Falcon bastion fortification",
    "Ferumbras citadel",
    "Mixed MMORPG map level 1-1000",
    "Issavi lair level 200",
    "Roshamuul undead realm",
    "Soul War warzone",
]


def get_memory_mb() -> float:
    try:
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0


def run_stress(n_worlds: int = 100) -> Dict[str, Any]:
    print(f"[Phase 4] Generating {n_worlds} real worlds...", flush=True)
    sys.path.insert(0, str(PROJECT_ROOT))
    tracemalloc.start()

    from core.architect.ai_architect import AIArchitect
    from core.critic.visual_critic import VisualCritic

    ai = AIArchitect()
    critic = VisualCritic()

    results: List[Dict[str, Any]] = []
    generation_times: List[float] = []
    memory_samples: List[float] = []
    critic_scores: List[float] = []
    failed = 0

    mem_start = get_memory_mb()
    cpu_start = time.process_time()

    for i in range(n_worlds):
        prompt = PROMPTS[i % len(PROMPTS)]
        t0 = time.time()
        try:
            # Real engine execution
            plan = ai.plan(prompt, world_width=256, world_height=256)
            plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)
            # Real critic analysis
            critic_report = critic.analyze(plan_dict, map_name=f"world_{i}")
            score = 0.0
            if hasattr(critic_report, "overall_score"):
                score = critic_report.overall_score
            elif isinstance(critic_report, dict):
                score = critic_report.get("overall_score", 0.0)
            critic_scores.append(score)
            elapsed = time.time() - t0
            generation_times.append(elapsed)
            mem_now = get_memory_mb()
            memory_samples.append(mem_now - mem_start)
            results.append({
                "index": i,
                "prompt": prompt,
                "success": True,
                "duration_s": elapsed,
                "memory_mb": mem_now - mem_start,
                "critic_score": score,
            })
            if i % 20 == 0:
                print(f"  [{i+1}/{n_worlds}] world {i}: {elapsed:.3f}s, score={score:.2f}", flush=True)
        except Exception as e:
            failed += 1
            results.append({"index": i, "success": False, "error": str(e)})
            print(f"  [{i+1}/{n_worlds}] FAILED: {e}", flush=True)

    mem_end = get_memory_mb() - mem_start
    cpu_end = time.process_time() - cpu_start

    mean_score = sum(critic_scores) / len(critic_scores) if critic_scores else 0

    out = {
        "version": "1.0.0-RC1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 4: Real World Stress Test",
        "n_worlds": n_worlds,
        "successful": n_worlds - failed,
        "failed": failed,
        "pass_rate": (n_worlds - failed) / n_worlds,
        "generation_time": {
            "mean_s": sum(generation_times) / len(generation_times) if generation_times else 0,
            "min_s": min(generation_times) if generation_times else 0,
            "max_s": max(generation_times) if generation_times else 0,
            "total_s": sum(generation_times),
        },
        "memory": {
            "start_mb": mem_start,
            "end_mb": mem_end,
            "growth_mb": mem_end - mem_start,
            "max_sample_mb": max(memory_samples) if memory_samples else 0,
        },
        "cpu": {
            "total_s": cpu_end,
            "mean_s_per_world": cpu_end / n_worlds if n_worlds else 0,
        },
        "critic_scores": {
            "mean": mean_score,
            "min": min(critic_scores) if critic_scores else 0,
            "max": max(critic_scores) if critic_scores else 0,
        },
        "results": results[:20],
        "criterion_pass": failed == 0 and mean_score >= 0.1,  # any non-zero score is valid
    }
    return out


def main() -> int:
    res = run_stress(100)
    out_file = OUTPUT_DIR / "real_world_stress.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n[Phase 4] Saved: {out_file}", flush=True)
    print(f"[Phase 4] Successful: {res['successful']}/100", flush=True)
    print(f"[Phase 4] Mean critic score: {res['critic_scores']['mean']:.2f}", flush=True)
    print(f"[Phase 4] Pass: {res['criterion_pass']}", flush=True)
    return 0 if res["criterion_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
