"""
tools/real_otbm_certification.py — Phase 5: Real OTBM Certification.

100 real roundtrips: Export -> Import -> Export -> Import.
"""
from __future__ import annotations
import sys
import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "rc1.1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = OUTPUT_DIR / "otbm_tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)


def run_certification(n: int = 100) -> Dict[str, Any]:
    print(f"[Phase 5] Running {n} real OTBM roundtrips...", flush=True)
    from core.otbm.otbm_exporter import OTBMExporter
    from core.otbm.otbm_importer import OTBMImporter
    from core.world.world_model import WorldModel
    from core.world.spawn import Spawn
    from core.world.region import Region
    from core.world.structure import Structure
    from core.world.tile import Tile

    exporter = OTBMExporter()
    importer = OTBMImporter()

    results: List[Dict[str, Any]] = []
    tiles_total = 0
    spawns_total = 0
    bosses_total = 0
    waypoints_total = 0
    regions_total = 0
    pass_count = 0
    durations: List[float] = []
    failed = 0

    for i in range(n):
        t0 = time.time()
        try:
            world = WorldModel()
            world.name = f"OTBM_World_{i}"
            for x in range(20):
                for y in range(20):
                    tile = Tile(x=x, y=y, z=7, ground=100, spawn=None)
                    world.set_tile(tile)
            tile_with_spawn = Tile(x=5, y=5, z=7, ground=100,
                                    spawn=Spawn(monster="rat", respawn=60, radius=3))
            world.set_tile(tile_with_spawn)
            region = Region(name=f"region_{i}", theme="generic", min_level=1, max_level=100)
            world.add_region(region)
            structure = Structure(name=f"house_{i}", category="house", x=10, y=10, z=7, width=5, height=5)
            world.add_structure(structure)

            otbm_path = str(TMP_DIR / f"world_{i}_v1.otbm")
            exporter.export(world, otbm_path)

            data_v1 = importer.import_file(otbm_path)
            if isinstance(data_v1, dict):
                n_tiles_v1 = data_v1.get("tile_count", 0)
                n_spawns_v1 = data_v1.get("spawn_count", 0)
                n_bosses_v1 = data_v1.get("boss_count", 0)
                n_waypoints_v1 = data_v1.get("waypoint_count", 0)
                n_regions_v1 = data_v1.get("region_count", 0)
            else:
                n_tiles_v1 = len(data_v1.tiles)
                n_spawns_v1 = sum(1 for t in data_v1.tiles if getattr(t, "spawn_monster", None))
                n_bosses_v1 = sum(1 for r in data_v1.regions if r.region_type == "boss_room")
                n_waypoints_v1 = len(data_v1.waypoints)
                n_regions_v1 = len(data_v1.regions)

            otbm_path_v2 = str(TMP_DIR / f"world_{i}_v2.otbm")
            exporter.export(data_v1, otbm_path_v2)

            data_v2 = importer.import_file(otbm_path_v2)
            if isinstance(data_v2, dict):
                n_tiles_v2 = data_v2.get("tile_count", 0)
                n_spawns_v2 = data_v2.get("spawn_count", 0)
                n_bosses_v2 = data_v2.get("boss_count", 0)
                n_waypoints_v2 = data_v2.get("waypoint_count", 0)
                n_regions_v2 = data_v2.get("region_count", 0)
            else:
                n_tiles_v2 = len(data_v2.tiles)
                n_spawns_v2 = sum(1 for t in data_v2.tiles if getattr(t, "spawn_monster", None))
                n_bosses_v2 = sum(1 for r in data_v2.regions if r.region_type == "boss_room")
                n_waypoints_v2 = len(data_v2.waypoints)
                n_regions_v2 = len(data_v2.regions)

            integrity_ok = (
                n_tiles_v1 == n_tiles_v2
                and n_spawns_v1 == n_spawns_v2
                and n_bosses_v1 == n_bosses_v2
                and n_waypoints_v1 == n_waypoints_v2
                and n_regions_v1 == n_regions_v2
            )
            if integrity_ok:
                pass_count += 1
                tiles_total += n_tiles_v1
                spawns_total += n_spawns_v1
                bosses_total += n_bosses_v1
                waypoints_total += n_waypoints_v1
                regions_total += n_regions_v1

            elapsed = time.time() - t0
            durations.append(elapsed)
            results.append({
                "index": i,
                "success": integrity_ok,
                "tiles": n_tiles_v1,
                "spawns": n_spawns_v1,
                "bosses": n_bosses_v1,
                "waypoints": n_waypoints_v1,
                "regions": n_regions_v1,
                "duration_s": elapsed,
            })
            if i % 20 == 0:
                print(f"  [{i+1}/{n}] tiles={n_tiles_v1} spawns={n_spawns_v1} ok={integrity_ok}", flush=True)
        except Exception as e:
            failed += 1
            results.append({"index": i, "success": False, "error": str(e)})
            if failed < 3:
                print(f"  [{i+1}/{n}] FAILED: {e}", flush=True)

    return {
        "version": "1.0.0-RC1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 5: Real OTBM Certification",
        "iterations": n,
        "passed": pass_count,
        "failed": failed,
        "pass_rate": pass_count / n,
        "totals": {
            "tiles": tiles_total,
            "spawns": spawns_total,
            "bosses": bosses_total,
            "waypoints": waypoints_total,
            "regions": regions_total,
        },
        "duration_s": {
            "mean": sum(durations) / len(durations) if durations else 0,
            "min": min(durations) if durations else 0,
            "max": max(durations) if durations else 0,
            "total": sum(durations),
        },
        "results": results[:20],
        "criterion_pass": pass_count >= n * 0.8,
    }


def main() -> int:
    res = run_certification(100)
    out_file = OUTPUT_DIR / "real_otbm_certification.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    try:
        shutil.rmtree(TMP_DIR)
    except Exception:
        pass
    print(f"\n[Phase 5] Saved: {out_file}", flush=True)
    print(f"[Phase 5] Passed: {res['passed']}/100", flush=True)
    print(f"[Phase 5] Pass: {res['criterion_pass']}", flush=True)
    return 0 if res["criterion_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
