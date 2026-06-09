"""
ga_benchmark.py — Agente RME v1.0.0 GA production benchmark.

Runs a 500-world benchmark using the fast generator path and exports
ga_benchmark.json with success rate, memory, CPU, critic score, and
generation speed.

Usage:
    python ga_benchmark.py [--count 500] [--output ga_benchmark.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_benchmark(count: int = 500, seed_start: int = 1,
                  output_path: str = "ga_benchmark.json") -> dict:
    """Run the GA benchmark."""
    try:
        import psutil  # type: ignore
        proc = psutil.Process(os.getpid())
    except Exception:
        psutil = None
        proc = None

    from core.generators import WorldGenerator

    successes = 0
    failures: list = []
    scores: list = []
    durations_ms: list = []
    tiles_list: list = []
    regions_list: list = []
    cpu_samples: list = []
    mem_samples: list = []
    t_start = time.time()

    print(f"\n[GA BENCHMARK] Running {count} worlds...")
    for i in range(count):
        seed = seed_start + i
        t0 = time.time()
        try:
            gen = WorldGenerator(seed=seed)
            world = gen.generate({
                "type": "hunt",
                "theme": "issavi",
                "level_min": 250,
                "level_max": 320,
                "width": 12,
                "height": 12,
            })
            tiles = world.tile_count() if hasattr(world, "tile_count") else 0
            regions = world.region_count() if hasattr(world, "region_count") else 0
            if tiles > 0:
                successes += 1
                tiles_list.append(tiles)
                regions_list.append(regions)
                # Heuristic critic score
                score = min(100.0, 60.0 + tiles * 0.01 + regions * 1.5)
                scores.append(score)
            else:
                failures.append({"seed": seed, "error": "empty_world"})
        except Exception as e:  # noqa: BLE001
            failures.append({"seed": seed, "error": str(e)})
        finally:
            elapsed = (time.time() - t0) * 1000.0
            durations_ms.append(elapsed)
            if proc is not None and i % 25 == 0:
                try:
                    cpu_samples.append(proc.cpu_percent(interval=None))
                    mem_samples.append(proc.memory_info().rss / (1024 * 1024))
                except Exception:
                    pass
        if (i + 1) % 50 == 0 or i == count - 1:
            elapsed_total = time.time() - t_start
            rate = (i + 1) / elapsed_total if elapsed_total > 0 else 0.0
            print(f"  [{i + 1:4d}/{count}] {successes} ok | {rate:.1f} worlds/s "
                  f"| {elapsed_total:.1f}s elapsed")

    elapsed_total = time.time() - t_start
    success_rate = successes / count if count else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    avg_dur = sum(durations_ms) / len(durations_ms) if durations_ms else 0.0
    max_dur = max(durations_ms) if durations_ms else 0.0
    min_dur = min(durations_ms) if durations_ms else 0.0
    avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
    peak_mem = max(mem_samples) if mem_samples else 0.0
    avg_mem = sum(mem_samples) / len(mem_samples) if mem_samples else 0.0

    report = {
        "timestamp": _utc_iso(),
        "version": "Agente RME v1.0.0 GA",
        "benchmark": {
            "count": count,
            "successful": successes,
            "failed": count - successes,
            "success_rate": round(success_rate, 4),
            "elapsed_seconds": round(elapsed_total, 3),
            "worlds_per_second": round(count / elapsed_total, 3) if elapsed_total > 0 else 0.0,
            "score": {
                "avg": round(avg_score, 2),
                "min": round(min_score, 2),
                "max": round(max_score, 2),
            },
            "generation_ms": {
                "avg": round(avg_dur, 2),
                "min": round(min_dur, 2),
                "max": round(max_dur, 2),
            },
            "memory_mb": {
                "avg": round(avg_mem, 2),
                "peak": round(peak_mem, 2),
            },
            "cpu_percent_avg": round(avg_cpu, 2),
            "tiles": {
                "avg": round(sum(tiles_list) / len(tiles_list), 2) if tiles_list else 0,
                "min": min(tiles_list) if tiles_list else 0,
                "max": max(tiles_list) if tiles_list else 0,
            },
            "regions": {
                "avg": round(sum(regions_list) / len(regions_list), 2) if regions_list else 0,
                "min": min(regions_list) if regions_list else 0,
                "max": max(regions_list) if regions_list else 0,
            },
            "failures_sample": failures[:10],
        },
        "ga_status": "PASS" if success_rate >= 0.99 else ("DEGRADED" if success_rate >= 0.95 else "FAIL"),
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[GA BENCHMARK COMPLETE]")
    print(f"  Success rate:   {success_rate:.2%}  ({successes}/{count})")
    print(f"  Avg score:      {avg_score:.2f}  (min {min_score:.2f}, max {max_score:.2f})")
    print(f"  Avg duration:   {avg_dur:.2f}ms")
    print(f"  Worlds/second:  {report['benchmark']['worlds_per_second']:.2f}")
    print(f"  Peak memory:    {peak_mem:.1f} MB")
    print(f"  GA status:      {report['ga_status']}")
    print(f"  Exported:       {out}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Agente RME v1.0.0 GA production benchmark")
    parser.add_argument("--count", type=int, default=500, help="Number of worlds to generate")
    parser.add_argument("--output", default="ga_benchmark.json", help="Output JSON path")
    parser.add_argument("--seed", type=int, default=1, help="Starting seed")
    args = parser.parse_args()
    try:
        report = run_benchmark(count=args.count, seed_start=args.seed,
                               output_path=args.output)
        if report["ga_status"] == "FAIL":
            sys.exit(2)
    except KeyboardInterrupt:
        print("\n[GA BENCHMARK] interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[GA BENCHMARK] FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
