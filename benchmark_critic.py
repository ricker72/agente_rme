"""
Benchmark the Visual Map Critic AI across 10 distinct maps.

Generates 10 different map configurations, runs the critic on each,
and produces a summary report.

Usage:
    python benchmark_critic.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import random
from typing import Any, Dict, List

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.critic import VisualCritic
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region
from core.world.structure import Structure
from core.world.spawn import Spawn


def _make_blank_world(size: int = 20) -> WorldModel:
    w = WorldModel()
    for x in range(size):
        for y in range(size):
            w.set_tile(Tile(x=x, y=y, z=7, ground=100))
    return w


def _fill_with_items(w: WorldModel, density: float, rng: random.Random) -> None:
    for tile in list(w.tiles.values()):
        if rng.random() < density:
            n = rng.randint(1, 5)
            tile.items = [
                {"itemid": rng.randint(100, 999), "count": 1} for _ in range(n)
            ]


def _add_spawns(w: WorldModel, count: int, monster: str, rng: random.Random) -> None:
    keys = list(w.tiles.keys())
    rng.shuffle(keys)
    for i in range(min(count, len(keys))):
        key = keys[i]
        tile = w.tiles[key]
        tile.spawn = Spawn(monster=monster, respawn=60, radius=2)


# 10 distinct map configurations


def map_issavi_300() -> WorldModel:
    """1. Issavi 300-500: 3 hunts, 2 bosses, 1 raid, full city hub."""
    w = WorldModel()
    for x in range(0, 30):
        for y in range(0, 30):
            w.set_tile(
                Tile(x=x, y=y, z=7, ground=100, items=[{"itemid": 200, "count": 1}])
            )
    w.add_region(Region(name="city_issavi", min_level=1, max_level=500))
    w.add_region(Region(name="city_issavi_depot", min_level=1, max_level=500))
    w.add_region(Region(name="city_issavi_temple", min_level=1, max_level=500))
    w.add_region(Region(name="city_issavi_npc", min_level=1, max_level=500))
    for i in range(3):
        ox = 50 + i * 60
        for dx in range(20):
            for dy in range(20):
                t = Tile(
                    x=ox + dx,
                    y=dy,
                    z=7,
                    ground=200 + i,
                    items=[{"itemid": 300, "count": 1}],
                    zone=f"hunt_{i}",
                )
                if (dx + dy) % 5 == 0:
                    t.spawn = Spawn(monster="Demon", respawn=60, radius=2)
                w.set_tile(t)
        w.add_region(Region(name=f"hunt_{i}", min_level=300 + i * 50, max_level=500))
    for i in range(2):
        w.add_structure(
            Structure(
                name=f"boss_{i}",
                category="boss_room",
                x=30 + i * 100,
                y=60,
                z=7,
                width=15,
                height=15,
                tags=["boss"],
            )
        )
        for dx in range(15):
            for dy in range(15):
                w.set_tile(Tile(x=30 + i * 100 + dx, y=60 + dy, z=7, ground=500))
    w.add_region(Region(name="raid_zargoth", min_level=300, max_level=500))
    for x in range(180, 220):
        for y in range(180, 220):
            w.set_tile(
                Tile(
                    x=x,
                    y=y,
                    z=7,
                    ground=600,
                    items=[{"itemid": 777, "count": 1}],
                    zone="raid_zargoth",
                )
            )
    return w


def map_roshamuul_400() -> WorldModel:
    """2. Roshamuul 400-600: heavy spawn density, fewer decorative items."""
    w = _make_blank_world(40)
    _add_spawns(w, 200, "Gazer", random.Random(42))
    _fill_with_items(w, 0.4, random.Random(43))
    w.add_region(Region(name="hunt_roshamuul_main", min_level=400, max_level=600))
    return w


def map_soul_war() -> WorldModel:
    """3. Soul War: cathedral, many spawns, light decoration."""
    w = _make_blank_world(30)
    _add_spawns(w, 80, "Lost Soul", random.Random(7))
    _fill_with_items(w, 0.15, random.Random(8))
    w.add_region(Region(name="hunt_soulwar", min_level=200, max_level=400))
    return w


def map_library() -> WorldModel:
    """4. Library: heavy decoration, few spawns."""
    w = _make_blank_world(20)
    _add_spawns(w, 10, "Demon", random.Random(11))
    _fill_with_items(w, 0.95, random.Random(12))
    w.add_region(Region(name="library", min_level=150, max_level=300))
    return w


def map_falcon() -> WorldModel:
    """5. Falcon: balanced map, 1 hunt, 1 city."""
    w = _make_blank_world(25)
    _add_spawns(w, 30, "Wyvern", random.Random(15))
    _fill_with_items(w, 0.4, random.Random(16))
    w.add_region(Region(name="hunt_falcon", min_level=100, max_level=250))
    w.add_region(Region(name="city_falcon", min_level=1, max_level=100))
    w.add_region(Region(name="city_falcon_depot", min_level=1, max_level=100))
    w.add_region(Region(name="city_falcon_temple", min_level=1, max_level=100))
    return w


def map_darashia() -> WorldModel:
    """6. Darashia: city focus with depot/temple + small hunt."""
    w = _make_blank_world(20)
    _add_spawns(w, 5, "Scarab", random.Random(19))
    _fill_with_items(w, 0.5, random.Random(20))
    w.add_region(Region(name="city_darashia", min_level=1, max_level=200))
    w.add_region(Region(name="city_darashia_depot", min_level=1, max_level=200))
    w.add_region(Region(name="city_darashia_temple", min_level=1, max_level=200))
    w.add_region(Region(name="hunt_darashia", min_level=50, max_level=150))
    return w


def map_djinn() -> WorldModel:
    """7. Djinn arena: small map, 1 boss, few tiles."""
    w = WorldModel()
    for x in range(10):
        for y in range(10):
            w.set_tile(
                Tile(x=x, y=y, z=7, ground=100, items=[{"itemid": 200, "count": 1}])
            )
    w.add_structure(
        Structure(
            name="boss_djinn",
            category="boss_room",
            x=2,
            y=2,
            z=7,
            width=6,
            height=6,
            tags=["boss"],
        )
    )
    w.add_region(Region(name="boss_djinn_arena", min_level=200, max_level=350))
    return w


def map_ancient_temple() -> WorldModel:
    """8. Ancient Temple: heavy decoration, low spawns."""
    w = _make_blank_world(35)
    _add_spawns(w, 5, "Demon", random.Random(23))
    _fill_with_items(w, 0.85, random.Random(24))
    w.add_region(Region(name="ancient_temple", min_level=200, max_level=400))
    return w


def map_venore() -> WorldModel:
    """9. Venore: city, hunt, 2 small bosses."""
    w = _make_blank_world(30)
    _add_spawns(w, 40, "Rat", random.Random(27))
    _fill_with_items(w, 0.35, random.Random(28))
    w.add_region(Region(name="city_venore", min_level=1, max_level=100))
    w.add_region(Region(name="city_venore_depot", min_level=1, max_level=100))
    w.add_region(Region(name="city_venore_temple", min_level=1, max_level=100))
    w.add_region(Region(name="hunt_venore", min_level=30, max_level=80))
    for i in range(2):
        w.add_structure(
            Structure(
                name=f"boss_v_{i}",
                category="boss_room",
                x=20 + i * 5,
                y=20,
                z=7,
                width=5,
                height=5,
                tags=["boss"],
            )
        )
    return w


def map_deep_orc() -> WorldModel:
    """10. Deep Orc Cave: dense spawns, no decoration, large area."""
    w = _make_blank_world(50)
    _add_spawns(w, 500, "Orc", random.Random(31))
    _fill_with_items(w, 0.05, random.Random(32))
    w.add_region(Region(name="hunt_orc_cave", min_level=50, max_level=150))
    return w


# All 10 maps
MAP_BUILDERS = [
    ("issavi_300_500", map_issavi_300),
    ("roshamuul_400_600", map_roshamuul_400),
    ("soul_war_300", map_soul_war),
    ("library_200", map_library),
    ("falcon_150", map_falcon),
    ("darashia_150", map_darashia),
    ("djinn_arena_300", map_djinn),
    ("ancient_temple_300", map_ancient_temple),
    ("venore_80", map_venore),
    ("deep_orc_cave_100", map_deep_orc),
]


def run_benchmark(output_dir: str = "output_benchmark") -> Dict[str, Any]:
    """Run the critic on 10 distinct maps and produce a summary."""
    os.makedirs(output_dir, exist_ok=True)
    critic = VisualCritic()
    results: List[Dict[str, Any]] = []

    print(f"\n=== Visual Map Critic AI — Benchmark ({len(MAP_BUILDERS)} maps) ===\n")
    for name, builder in MAP_BUILDERS:
        t0 = time.time()
        try:
            world = builder()
            sub_dir = os.path.join(output_dir, name)
            os.makedirs(sub_dir, exist_ok=True)
            result = critic.analyze(
                world,
                map_name=name,
                output_dir=sub_dir,
                generate_heatmaps=True,
            )
            elapsed = time.time() - t0
            entry = {
                "name": name,
                "overall_score": round(result.overall_score, 2),
                "visual_score": round(result.visual_score, 2),
                "navigation_score": round(result.navigation_score, 2),
                "density_score": round(result.density_score, 2),
                "spawn_score": round(result.spawn_score, 2),
                "hunt_score": round(result.hunt_score, 2),
                "boss_score": round(result.boss_score, 2),
                "city_score": round(result.city_score, 2),
                "decor_score": round(result.decor_score, 2),
                "pathfinding_score": round(result.pathfinding_score, 2),
                "issue_count": len(result.issues),
                "recommendation_count": len(result.recommendations),
                "elapsed_seconds": round(elapsed, 3),
                "status": "ok",
            }
            print(
                f"  {name:30s}  overall={entry['overall_score']:6.2f}  "
                f"issues={entry['issue_count']:3d}  recs={entry['recommendation_count']:3d}  "
                f"({entry['elapsed_seconds']:.2f}s)"
            )
        except Exception as e:  # pragma: no cover — defensive
            elapsed = time.time() - t0
            entry = {
                "name": name,
                "status": "error",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 3),
            }
            print(f"  {name:30s}  ERROR: {e}")
        results.append(entry)

    # Summary
    ok = [r for r in results if r["status"] == "ok"]
    if ok:
        avg = sum(r["overall_score"] for r in ok) / len(ok)
        min_s = min(r["overall_score"] for r in ok)
        max_s = max(r["overall_score"] for r in ok)
    else:
        avg = min_s = max_s = 0.0

    summary = {
        "benchmark": "Visual Map Critic AI",
        "total_maps": len(MAP_BUILDERS),
        "successful": len(ok),
        "failed": len(results) - len(ok),
        "average_overall_score": round(avg, 2),
        "min_overall_score": round(min_s, 2),
        "max_overall_score": round(max_s, 2),
        "per_map": results,
    }
    summary_path = os.path.join(output_dir, "benchmark_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  Average overall score: {avg:.2f}")
    print(f"  Min: {min_s:.2f}  Max: {max_s:.2f}")
    print(f"  Summary written to: {summary_path}\n")
    return summary


if __name__ == "__main__":
    run_benchmark()
