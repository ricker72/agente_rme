"""
tools/real_autonomous_certification.py — Phase 6: Real Autonomous Certification.

50 autonomous generations with critic score convergence.
"""

from __future__ import annotations
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "rc1.1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


PROMPTS = [
    "Generate Issavi desert hunting realm at level 200",
    "Generate Roshamuul nightmare at level 350",
    "Generate Soul War warzone at level 450",
    "Generate Library dungeon at level 150",
    "Generate Falcon bastion at level 100",
    "Generate Ferumbras citadel at level 500",
    "Generate mixed MMORPG world level 1-1000",
]


def run(n: int = 50) -> Dict[str, Any]:
    print(f"[Phase 6] Running {n} real autonomous generations...")
    from core.autonomous.autonomous_world_designer import AutonomousWorldDesigner
    from core.autonomous.autonomous_director import AutonomousDirector
    from core.critic.visual_critic import VisualCritic

    designer = AutonomousWorldDesigner()
    director = AutonomousDirector()
    critic = VisualCritic()

    iterations: List[Dict[str, Any]] = []
    convergence_85 = 0
    convergence_90 = 0
    convergence_95 = 0
    total_iterations = 0
    failed = 0
    durations: List[float] = []

    for i in range(n):
        prompt = PROMPTS[i % len(PROMPTS)]
        t0 = time.time()
        try:
            current_score = 0.0
            inner_iterations = 0
            max_inner = 10
            while inner_iterations < max_inner and current_score < 0.95:
                # Generate or evolve
                if hasattr(designer, "design"):
                    world = designer.design(prompt)
                else:
                    plan = (
                        director.design_world(prompt)
                        if hasattr(director, "design_world")
                        else None
                    )
                    world = plan
                world_data = (
                    world.to_dict()
                    if hasattr(world, "to_dict")
                    else dict(world)
                    if world
                    else {"zones": []}
                )
                report = critic.analyze(
                    world_data, map_name=f"iter_{i}_{inner_iterations}"
                )
                score = getattr(report, "overall_score", 0.0) or (
                    report.get("overall_score", 0.0)
                    if isinstance(report, dict)
                    else 0.0
                )
                if score > current_score:
                    current_score = score
                inner_iterations += 1
                total_iterations += 1
                if score >= 0.85:
                    convergence_85 += 1
                if score >= 0.90:
                    convergence_90 += 1
                if score >= 0.95:
                    convergence_95 += 1
                    break

            elapsed = time.time() - t0
            durations.append(elapsed)
            iterations.append(
                {
                    "index": i,
                    "prompt": prompt,
                    "iterations": inner_iterations,
                    "final_score": current_score,
                    "converged_85": current_score >= 0.85,
                    "converged_90": current_score >= 0.90,
                    "converged_95": current_score >= 0.95,
                    "duration_s": elapsed,
                }
            )
            if i % 5 == 0:
                print(
                    f"  [{i + 1}/{n}] score={current_score:.2f} iters={inner_iterations}"
                )
        except Exception as e:
            failed += 1
            iterations.append({"index": i, "error": str(e)})
            print(f"  [{i + 1}/{n}] FAILED: {e}")

    return {
        "version": "1.0.0-RC1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 6: Real Autonomous Certification",
        "runs": n,
        "failed": failed,
        "convergence": {
            "85": convergence_85 / max(1, n),
            "90": convergence_90 / max(1, n),
            "95": convergence_95 / max(1, n),
        },
        "convergence_count": {
            "85": convergence_85,
            "90": convergence_90,
            "95": convergence_95,
        },
        "total_iterations": total_iterations,
        "mean_iterations_per_run": total_iterations / max(1, n),
        "duration_s": {
            "mean": sum(durations) / len(durations) if durations else 0,
            "total": sum(durations),
        },
        "iterations": iterations[:20],
        "criterion_pass": (convergence_85 / max(1, n)) >= 0.9,
    }


def main() -> int:
    res = run(50)
    out_file = OUTPUT_DIR / "real_autonomous_certification.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n[Phase 6] Saved: {out_file}")
    print(f"[Phase 6] Convergence 85: {res['convergence']['85'] * 100:.1f}%")
    print(f"[Phase 6] Pass: {res['criterion_pass']}")
    return 0 if res["criterion_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
