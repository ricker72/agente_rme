#!/usr/bin/env python3
"""
Benchmark for Blueprint Intelligence Engine.

Processes 500+ blueprints and validates:
  - Embeddings generated
  - Clusters generated
  - Fusion functional
  - Evolution functional
  - No exceptions
"""

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata  # noqa: E402
from core.blueprint_intelligence.blueprint_intelligence_engine import (  # noqa: E402
    BlueprintIntelligenceEngine,
)


def _generate_blueprints(count: int) -> list:
    """Generate test blueprints."""
    bps = []
    categories = ["hunt", "city", "boss_room", "dungeon", "raid"]
    themes = [
        "roshamuul",
        "soul_war",
        "issavi",
        "falcon",
        "ferumbras",
        "library",
        "asylum",
        "catacomb",
        "ice",
        "fire",
    ]

    for i in range(count):
        cat = categories[i % len(categories)]
        theme = themes[i % len(themes)]
        tiles = [
            BlueprintTile(x=x, y=y, ground=100) for x in range(5) for y in range(5)
        ]
        bp = Blueprint(
            name=f"bench_bp_{i}",
            category=cat,
            theme=theme,
            size=(10, 10),
            tiles=tiles,
            metadata=BlueprintMetadata(tags=[cat, theme, f"benchmark_{i}"]),
            _raw={
                "critic_score": float(i % 100),
                "playtest_score": float((i * 7) % 100),
            },
            zones=[{"type": "zone", "name": f"zone_{i}"}],
        )
        bps.append(bp)
    return bps


def run_benchmark():
    """Run the Blueprint Intelligence benchmark."""
    print("=" * 60)
    print("  Blueprint Intelligence Engine Benchmark")
    print("=" * 60)

    # Generate test data
    print("\nGenerating 500+ blueprints...")
    blueprints = _generate_blueprints(500)
    print(f"  Created {len(blueprints)} blueprints")

    # Initialize engine
    engine = BlueprintIntelligenceEngine()
    engine.load_blueprints(blueprints)

    # 1. Embeddings
    print("\n1. Embedding Generation...")
    t0 = time.time()
    embeddings = engine.build_embeddings()
    t1 = time.time()
    print(f"   Generated {len(embeddings)} embeddings in {t1 - t0:.2f}s")
    assert len(embeddings) == 500, f"Expected 500 embeddings, got {len(embeddings)}"

    # 2. Similarity
    print("\n2. Similarity Search...")
    target = blueprints[0]
    t0 = time.time()
    similar = engine.find_similar(target, top_k=10)
    t1 = time.time()
    print(f"   Found {len(similar)} similar in {t1 - t0:.2f}s")

    # 3. Fusion
    print("\n3. Blueprint Fusion...")
    t0 = time.time()
    hybrid = engine.fuse(blueprints[0], blueprints[1], ratio=0.7)
    t1 = time.time()
    print(f"   Fusion result: {hybrid.name} in {t1 - t0:.2f}s")
    assert hybrid.is_valid, "Fusion should produce valid blueprint"

    # 4. Evolution
    print("\n4. Blueprint Evolution...")
    t0 = time.time()
    evolved = engine.evolve(blueprints[0], target_critic_score=60.0, max_generations=5)
    t1 = time.time()
    print(
        f"   Evolved to gen {evolved.generation}, score {evolved.critic_score:.1f} in {t1 - t0:.2f}s"
    )
    assert evolved.is_valid, "Evolution should produce valid result"

    # 5. Clustering
    print("\n5. Clustering...")
    t0 = time.time()
    clusters = engine.cluster()
    t1 = time.time()
    print(f"   Found {len(clusters)} clusters in {t1 - t0:.2f}s")
    assert len(clusters) > 0, "Should have at least 1 cluster"

    # 6. Ranking
    print("\n6. Ranking...")
    t0 = time.time()
    ranked = engine.rank_all(top_k=20)
    t1 = time.time()
    print(f"   Ranked {len(ranked)} top blueprints in {t1 - t0:.2f}s")
    assert len(ranked) == 20, "Should have 20 ranked results"

    # 7. Pattern Mining
    print("\n7. Pattern Mining...")
    t0 = time.time()
    patterns = engine.mine_patterns()
    t1 = time.time()
    print(f"   Mined {len(patterns)} patterns in {t1 - t0:.2f}s")

    # 8. Recommendations
    print("\n8. Recommendations...")
    t0 = time.time()
    recs = engine.recommend_patterns(top_k=5)
    t1 = time.time()
    print(f"   Generated {len(recs)} recommendations in {t1 - t0:.2f}s")

    # 9. Generation
    print("\n9. Blueprint Generation...")
    t0 = time.time()
    generated = engine.generate("Generate hunt level 400 roshamuul style")
    t1 = time.time()
    print(f"   Generated '{generated.name}' in {t1 - t0:.2f}s")

    # 10. Export
    print("\n10. Export...")
    export_dir = "output_benchmark"
    os.makedirs(export_dir, exist_ok=True)
    engine.export_embeddings(f"{export_dir}/blueprint_embeddings.json")
    engine.export_clusters(f"{export_dir}/blueprint_clusters.json")
    engine.export_patterns(f"{export_dir}/blueprint_patterns.json")
    engine.export_rankings(f"{export_dir}/blueprint_rankings.json")
    engine.export_recommendations(f"{export_dir}/blueprint_recommendations.json")
    print(f"   Exported to {export_dir}/")

    print("\n" + "=" * 60)
    print("  BENCHMARK PASSED - All checks OK")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
