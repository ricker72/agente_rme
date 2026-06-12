"""
tools/real_memory_profile.py — Phase 9: Real Memory Profile.

100 generations tracking memory to detect leaks, object accumulation, cache growth.
"""

from __future__ import annotations
import sys
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


def run(n: int = 100) -> Dict[str, Any]:
    print(f"[Phase 9] Memory profile over {n} generations...")
    from core.architect.ai_architect import AIArchitect
    from core.critic.visual_critic import VisualCritic

    ai = AIArchitect()
    critic = VisualCritic()

    tracemalloc.start()
    samples: List[Dict[str, float]] = []
    object_counts: List[int] = []
    durations: List[float] = []

    for i in range(n):
        t0 = time.time()
        try:
            plan = ai.plan(
                f"memory profile world {i}", world_width=128, world_height=128
            )
            critic.analyze(
                plan.to_dict() if hasattr(plan, "to_dict") else dict(plan),
                map_name=f"mem_{i}",
            )
        except Exception as e:
            print(f"  [{i + 1}/{n}] ERROR: {e}")
        elapsed = time.time() - t0
        durations.append(elapsed)

        current, peak = tracemalloc.get_traced_memory()
        obj_count = len(gc.get_objects())
        object_counts.append(obj_count)
        samples.append(
            {
                "iteration": i,
                "current_mb": current / (1024 * 1024),
                "peak_mb": peak / (1024 * 1024),
                "objects": obj_count,
                "duration_s": elapsed,
            }
        )
        if i % 20 == 0:
            print(
                f"  [{i + 1}/{n}] cur={current / (1024 * 1024):.2f}MB peak={peak / (1024 * 1024):.2f}MB objects={obj_count}"
            )
        # Force GC every 20 iterations
        if i % 20 == 0:
            gc.collect()

    # Analysis
    memory_mb = [s["current_mb"] for s in samples]
    objects_list = [s["objects"] for s in samples]
    growth_mb = memory_mb[-1] - memory_mb[0] if memory_mb else 0
    growth_obj = objects_list[-1] - objects_list[0] if objects_list else 0

    leak_detected = growth_mb > 50.0  # > 50MB growth indicates leak
    object_leak = growth_obj > 10000  # > 10k objects

    return {
        "version": "1.0.0-RC1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 9: Real Memory Profile",
        "iterations": n,
        "memory": {
            "start_mb": memory_mb[0] if memory_mb else 0,
            "end_mb": memory_mb[-1] if memory_mb else 0,
            "growth_mb": growth_mb,
            "peak_mb": max([s["peak_mb"] for s in samples]) if samples else 0,
        },
        "objects": {
            "start": objects_list[0] if objects_list else 0,
            "end": objects_list[-1] if objects_list else 0,
            "growth": growth_obj,
            "max": max(objects_list) if objects_list else 0,
        },
        "duration_s": {
            "mean": sum(durations) / len(durations) if durations else 0,
            "total": sum(durations),
        },
        "leak_detected": leak_detected,
        "object_leak": object_leak,
        "samples": samples[::5],  # every 5th sample
        "criterion_pass": not leak_detected and not object_leak,
    }


def main() -> int:
    res = run(100)
    out_file = OUTPUT_DIR / "real_memory_profile.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n[Phase 9] Saved: {out_file}")
    print(f"[Phase 9] Memory growth: {res['memory']['growth_mb']:.2f}MB")
    print(f"[Phase 9] Leak detected: {res['leak_detected']}")
    print(f"[Phase 9] Pass: {res['criterion_pass']}")
    return 0 if res["criterion_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
