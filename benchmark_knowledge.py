"""
HITO 28 — Knowledge benchmark.

Process a large synthetic dataset, time the build, then run a battery of
queries to measure search throughput and memory footprint.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.knowledge import (  # noqa: E402
    DatasetBuilder,
    KnowledgeEngine,
)
from core.knowledge.knowledge_metrics import build_metrics  # noqa: E402

THEMES = [
    "roshamuul",
    "issavi",
    "yalahar",
    "venore",
    "thais",
    "carlin",
    "edron",
    "darashia",
    "ankrahmun",
    "asura",
    "krailos",
    "vippre",
    "hellgate",
    "orcsoberfest",
    "feyrist",
]
HUNT_PREFIX = ["outer", "inner", "upper", "lower", "circular", "sewer", "lair"]
BOSS_PREFIX = ["boss", "arena", "throne", "lair", "pit", "coliseum"]
MONSTER_NAMES = [
    "Guzzlemaw",
    "Hellflayer",
    "Demon",
    "Dragon Lord",
    "Grim Reaper",
    "Frazzlemaw",
    "Lizard Guard",
    "Scarab",
    "Vampire",
    "Hydra",
]
CITIES = [
    "Issavi",
    "Roshamuul",
    "Yalahar",
    "Venore",
    "Thais",
    "Carlin",
    "Edron",
    "Darashia",
    "Ankrahmun",
    "Asura",
    "Feyrist",
    "Krailos",
    "Vippre",
    "Farmine",
    "Liberty Bay",
]


def _make_source(idx: int) -> dict:
    rng = random.Random(idx)
    theme = rng.choice(THEMES)
    name = theme
    return {
        "meta": {"name": name, "theme": theme},
        "regions": [
            {
                "name": f"{rng.choice(HUNT_PREFIX)}_{name}_hunt_{idx}",
                "theme": theme,
                "min_level": rng.randint(50, 250),
                "max_level": rng.randint(300, 600),
                "tags": ["circular" if rng.random() > 0.5 else "linear"],
            }
            for _ in range(rng.randint(1, 3))
        ],
        "cities": [
            {
                "name": f"{rng.choice(CITIES)}_{idx}",
                "theme": theme,
                "min_level": 100,
                "max_level": 500,
            }
            for _ in range(rng.randint(0, 2))
        ],
        "structures": [
            {
                "name": f"{rng.choice(BOSS_PREFIX)}_arena_{name}_{idx}",
                "category": "boss_room",
                "theme": theme,
                "min_level": 300,
                "max_level": 600,
                "width": 30,
                "height": 30,
                "tags": ["boss", "circular"],
            }
        ],
        "spawns": [
            {
                "monster": rng.choice(MONSTER_NAMES),
                "zone": f"{rng.choice(HUNT_PREFIX)}_{name}_hunt_{idx}",
                "level": rng.randint(150, 500),
            }
            for _ in range(rng.randint(1, 3))
        ],
        "waypoints": [
            {"name": f"tp_{name}_{idx}", "theme": theme},
        ],
        "quests": [
            {
                "name": f"quest_{name}_{idx}",
                "theme": theme,
                "difficulty": rng.choice(["easy", "medium", "hard"]),
            }
        ],
    }


def run_benchmark(n_maps: int = 100):
    t0 = time.perf_counter()
    sources = [_make_source(i) for i in range(n_maps)]
    build_t0 = time.perf_counter()
    builder = DatasetBuilder()
    ds = builder.build_from_sources(sources)
    build_t = (time.perf_counter() - build_t0) * 1000
    print(f"[1/5] Built dataset from {n_maps} sources in {build_t:.0f}ms")
    print(f"  Total entries: {ds.total()}")
    print(f"  By type: {ds.counts()}")

    engine = KnowledgeEngine(dataset=ds)
    total_t = (time.perf_counter() - t0) * 1000
    print(f"[2/5] Engine ready in {total_t:.0f}ms total")
    print(f"  Index stats: {engine.index.stats()}")

    # Text queries
    queries = [
        "boss rooms level 500",
        "circular hunts",
        "roshamuul",
        "city",
        "quest",
        "spawns guzzlemaw",
        "hunts level 300-500",
    ]
    q_t0 = time.perf_counter()
    total_q = 0
    for q in queries * 5:  # 35 queries
        engine.query_text(q, k=10)
        total_q += 1
    q_t = (time.perf_counter() - q_t0) * 1000
    avg_ms = q_t / max(1, total_q)
    print(f"[3/5] Ran {total_q} text queries in {q_t:.0f}ms ({avg_ms:.2f}ms/query)")

    # Find-similar queries
    s_t0 = time.perf_counter()
    for hunt in ds.hunts[:20]:
        engine.find_similar_hunts(hunt.name, k=5)
    s_t = (time.perf_counter() - s_t0) * 1000
    print(f"[4/5] Ran 20 find-similar queries in {s_t:.0f}ms")

    # Metrics
    m = build_metrics(ds)
    print("[5/5] Metrics computed:")
    print(f"  Total entries: {m.total_entries}")
    print(f"  Coverage: {m.coverage_pct:.1f}%")
    print(f"  Avg quality: {m.avg_quality_score:.1f}")
    print(f"  Circular hunts: {m.circular_hunts}")
    print(f"  Circular boss rooms: {m.circular_boss_rooms}")
    print(f"  Level coverage: {m.level_coverage}")

    # Save artifacts
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    ds_path = out_dir / "knowledge_dataset.json"
    engine.save(str(ds_path))
    print(f"\nDataset saved to: {ds_path}")
    metrics_path = out_dir / "knowledge_metrics.json"
    m.write(str(metrics_path))
    print(f"Metrics saved to: {metrics_path}")
    catalog_path = out_dir / "knowledge_catalog.json"
    cat = engine.build_catalog(top_n=5)
    cat.write(str(catalog_path))
    print(f"Catalog saved to: {catalog_path}")
    report_path = out_dir / "knowledge_report.md"
    from core.knowledge import KnowledgeReport

    report = KnowledgeReport.build(ds, m, cat)
    report.write(str(report_path))
    print(f"Report saved to: {report_path}")

    total_t = (time.perf_counter() - t0) * 1000
    print(f"\nTotal benchmark time: {total_t:.0f}ms")
    return {
        "n_maps": n_maps,
        "total_entries": ds.total(),
        "build_ms": build_t,
        "query_count": total_q,
        "total_query_ms": q_t,
        "avg_query_ms": avg_ms,
        "coverage_pct": m.coverage_pct,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="Number of maps to process")
    args = parser.parse_args()
    summary = run_benchmark(n_maps=args.n)
    out = Path("output/knowledge_benchmark.json")
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nBenchmark summary written to: {out}")
