"""Hito 30 â€” Autonomous World Designer benchmark.

Generates a configurable number of worlds (default 50) and produces a
convergence report with critic/playtest score distributions, average
improvement per world, convergence ratio and total runtime.

The benchmark is fully self-contained and exercises every component of
the autonomous pipeline (Director, Planner, Decision Engine, Optimizer,
Goal Manager, Visual Critic, OTBM Exporter).

Usage:
    python benchmark_autonomous.py            # 50 worlds
    python benchmark_autonomous.py --count 5  # quick smoke test
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.autonomous import AutonomousWorldDesigner  # noqa: E402


PROMPTS = [
    "Issavi Roshamuul level 300-500 3 hunts 2 bosses 1 raid",
    "Compact desert city Issavi style",
    "Large endgame continent 3 cities 8 hunts 5 bosses 2 raids",
    "Forest hunt area level 200-300 2 hunts",
    "Ice dragon boss arena level 400 1 boss",
    "Underground raid dungeon level 350 1 raid",
    "Forest grove city 2 hunts 1 boss",
    "Hunt level 200",
    "Boss level 300 1 boss",
    "City level 150",
    "Raid level 400 1 raid",
    "Compact city level 100",
    "Roshamuul citadel hunt level 350",
    "Issavi dunes hunt 200-300 2 hunts",
    "Desert oasis city 1 hunt",
    "Multi-region world 3 cities 4 hunts 2 bosses",
    "Frosthold tundra level 250 1 hunt",
    "Forest treant boss level 280 1 boss",
    "Coastal city level 150 1 hunt",
    "Mountain pass hunt level 320 2 hunts",
    "Volcanic region level 380 1 boss 1 raid",
    "Swamp hunt level 200 1 hunt",
    "Sky island raid level 450 1 raid",
    "Dwarven mines hunt level 250 1 hunt",
    "Elven forest city level 200",
    "Demon lair boss level 400 1 boss",
    "Undead crypt raid level 300 1 raid",
    "Tropical island city level 100",
    "Frozen north hunt level 350 2 hunts",
    "Endgame fortress boss level 500 1 boss",
    "Coral reef hunt level 180 1 hunt",
    "Ancient ruins raid level 380 1 raid",
    "Royal city level 250",
    "Bandit camp hunt level 220 1 hunt",
    "Lich tower boss level 420 1 boss",
    "Goblin warren hunt level 180 2 hunts",
    "Haunted mansion raid level 320 1 raid",
    "Pirate cove city level 150",
    "Dragon's lair boss level 480 1 boss",
    "Sacred grove hunt level 280 1 hunt",
    "Sunken temple raid level 350 1 raid",
    "Wizard tower boss level 400 1 boss",
    "Mining town city level 200",
    "Wasteland hunt level 300 2 hunts",
    "Crystal caves raid level 380 1 raid",
    "Sky temple boss level 450 1 boss",
    "Desert nomad camp hunt level 200 1 hunt",
    "Fey realm city level 250",
    "Demonic incursion raid level 420 1 raid",
    "Hidden valley hunt level 240 1 hunt",
]


def run_benchmark(num_worlds: int = 50, max_iterations: int = 2, output_dir: str = "output/autonomous_benchmark") -> dict:
    print(f"=== Autonomous World Designer benchmark ===")
    print(f"  worlds     : {num_worlds}")
    print(f"  iterations : {max_iterations}")
    print(f"  output dir : {output_dir}")
    print()

    designer = AutonomousWorldDesigner(output_dir=output_dir)
    # Keep iterations low to make the benchmark feasible (full convergence
    # is verified in the unit tests, here we focus on coverage/throughput)
    designer.optimizer.max_iterations = max_iterations
    designer.optimizer.use_real_engines = True

    results = []
    critic_scores: List[float] = []
    playtest_scores: List[float] = []
    improvements: List[float] = []
    iteration_counts: List[int] = []
    errors: List[str] = []

    start = time.time()
    for i in range(num_worlds):
        prompt = PROMPTS[i % len(PROMPTS)]
        try:
            result = designer.generate(prompt, max_iterations=max_iterations)
            critic = result.final_scores.get("critic", 0.0)
            playtest = result.final_scores.get("playtest", 0.0)
            improvement = (
                result.convergence_data[-1] - result.convergence_data[0]
                if len(result.convergence_data) > 1
                else 0.0
            )
            results.append({
                "index": i,
                "prompt": prompt,
                "result_id": result.result_id,
                "iterations": len(result.iterations),
                "critic": critic,
                "playtest": playtest,
                "improvement": improvement,
                "success": result.success,
                "duration_s": result.total_duration_seconds,
            })
            critic_scores.append(critic)
            playtest_scores.append(playtest)
            improvements.append(improvement)
            iteration_counts.append(len(result.iterations))
            print(
                f"  [{i+1:3d}/{num_worlds}] "
                f"critic={critic:.3f} playtest={playtest:.3f} "
                f"iter={len(result.iterations):2d} "
                f"Î”={improvement:+.3f} ({result.total_duration_seconds:.2f}s)"
            )
        except Exception as exc:  # pragma: no cover
            errors.append(f"world {i}: {exc}")
            print(f"  [{i+1:3d}/{num_worlds}] FAILED: {exc}")

    total = time.time() - start

    report = {
        "total_worlds": len(results),
        "successful_worlds": sum(1 for r in results if r["success"]),
        "errors": errors,
        "average_critic_score": statistics.mean(critic_scores) if critic_scores else 0.0,
        "median_critic_score": statistics.median(critic_scores) if critic_scores else 0.0,
        "max_critic_score": max(critic_scores) if critic_scores else 0.0,
        "min_critic_score": min(critic_scores) if critic_scores else 0.0,
        "stdev_critic_score": statistics.pstdev(critic_scores) if len(critic_scores) > 1 else 0.0,
        "average_playtest_score": statistics.mean(playtest_scores) if playtest_scores else 0.0,
        "average_improvement": statistics.mean(improvements) if improvements else 0.0,
        "average_iterations": statistics.mean(iteration_counts) if iteration_counts else 0.0,
        "total_duration_seconds": total,
        "avg_duration_per_world": (total / len(results)) if results else 0.0,
        "convergence_rate": (
            sum(1 for imp in improvements if imp > 0) / len(improvements)
            if improvements else 0.0
        ),
        "converged_worlds": sum(
            1 for r in results
            if r.get("improvement", 0) >= 0
        ),
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }

    # Persist report
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)

    # Print summary
    print()
    print("=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"  Total worlds         : {report['total_worlds']}")
    print(f"  Successful worlds    : {report['successful_worlds']}")
    print(f"  Errors               : {len(report['errors'])}")
    print(f"  Avg critic score     : {report['average_critic_score']:.3f}")
    print(f"  Median critic score  : {report['median_critic_score']:.3f}")
    print(f"  Max critic score     : {report['max_critic_score']:.3f}")
    print(f"  Min critic score     : {report['min_critic_score']:.3f}")
    print(f"  Stdev critic score   : {report['stdev_critic_score']:.3f}")
    print(f"  Avg playtest score   : {report['average_playtest_score']:.3f}")
    print(f"  Avg improvement      : {report['average_improvement']:+.3f}")
    print(f"  Convergence rate     : {report['convergence_rate']:.1%}")
    print(f"  Avg iterations       : {report['average_iterations']:.1f}")
    print(f"  Total duration       : {total:.1f}s")
    print(f"  Avg per world        : {report['avg_duration_per_world']:.2f}s")
    print(f"  Report               : {report_path}")
    print()

    return report


def main():
    parser = argparse.ArgumentParser(description="Hito 30 â€” Autonomous World Designer benchmark")
    parser.add_argument("--count", type=int, default=50, help="Number of worlds to generate")
    parser.add_argument("--iterations", type=int, default=2, help="Max iterations per world")
    parser.add_argument("--output", default="output/autonomous_benchmark", help="Output directory")
    args = parser.parse_args()
    run_benchmark(num_worlds=args.count, max_iterations=args.iterations, output_dir=args.output)


if __name__ == "__main__":
    main()
