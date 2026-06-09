"""Tests for V1.0 production infrastructure modules."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_version():
    from core.versioning import ProjectVersion, __version__, VERSION
    v = ProjectVersion.current()
    assert v.major == 1
    assert v.minor == 0
    assert str(v) == "v1.0"
    assert v.is_stable

    parsed = ProjectVersion.parse("v2.1.3-beta")
    assert parsed.major == 2
    assert parsed.minor == 1
    assert parsed.patch == 3
    assert parsed.label == "beta"
    assert parsed.is_prerelease

    assert __version__ == "v1.0"
    assert VERSION == v
    print("[PASS] test_version")


def test_cache():
    import shutil
    from core.cache.generation_cache import GenerationCache

    cache = GenerationCache(cache_dir=".test_cache", max_size_mb=1, ttl_seconds=300)
    cache.set("key1", {"data": [1, 2, 3]})
    val = cache.get("key1")
    assert val == {"data": [1, 2, 3]}

    assert cache.get("missing") is None
    cache.invalidate("key1")
    assert cache.get("key1") is None

    stats = cache.stats()
    assert "entries" in stats
    assert "size_mb" in stats
    print(f"[PASS] test_cache (stats: {stats})")
    shutil.rmtree(".test_cache", ignore_errors=True)


def test_benchmark():
    import time
    from core.benchmark.runner import BenchmarkRunner

    bm = BenchmarkRunner(iterations=2)
    bm.start("smoke")
    time.sleep(0.002)
    result = bm.stop(tiles=100)
    assert result.name == "smoke"
    assert result.duration_ms > 0
    assert result.tiles_generated == 100
    assert result.tiles_per_second > 0
    assert result.total_iterations == 2

    summary = bm.summary()
    assert "smoke" in summary
    print(f"[PASS] test_benchmark ({result.duration_ms:.1f}ms, {result.tiles_per_second:.0f} tps)")


def test_asset_registry():
    from core.registry.asset_registry import AssetRegistry
    import xml.etree.ElementTree as ET
    import tempfile, os

    reg = AssetRegistry()

    # Create temp items.xml
    xml = """<?xml version="1.0"?>
<items>
  <item id="100" name="stone floor"/>
  <item id="200" name="wooden wall"/>
  <item id="300" name="torch"/>
  <item id="400" name="dragon statue"/>
</items>"""
    fd, path = tempfile.mkstemp(suffix=".xml")
    os.write(fd, xml.encode())
    os.close(fd)

    try:
        count = reg.load_items(path)
        assert count == 4
        assert reg.get_item_id("stone floor") == 100
        assert reg.get_item_name(200) == "wooden wall"
        assert 100 in reg.get_grounds()
        assert 200 in reg.get_walls()
        assert 300 in reg.get_decorations()
        summary = reg.summary()
        assert summary["items"] == 4
        print(f"[PASS] test_asset_registry ({summary})")
    finally:
        os.unlink(path)


def test_blueprint_registry():
    from core.registry.blueprint_registry import BlueprintRegistry

    reg = BlueprintRegistry()
    reg.register("issavi_temple", "temple", {"name": "Issavi Temple", "size": [8, 10]})
    reg.register("small_house", "house", {"name": "Small House", "size": [5, 5]})
    reg.register("grand_bridge", "bridge", {"name": "Grand Bridge", "length": 12})

    temple = reg.get_blueprint("temple", "issavi_temple")
    assert temple is not None
    assert temple["name"] == "Issavi Temple"

    all_houses = reg.get_all_of_type("house")
    assert len(all_houses) == 1

    types = reg.list_types()
    assert "temple" in types
    assert "house" in types
    assert "bridge" in types

    summary = reg.summary()
    assert summary["temple"] == 1
    print(f"[PASS] test_blueprint_registry ({summary})")


def test_logger():
    from core.logging.logger import Logger
    from core.logging.levels import LogLevel

    log = Logger.get_logger("test_logger", "DEBUG")
    log.debug("Infrastructure test debug message")

    Logger.generation_start("city", theme="issavi", tiles=500)
    Logger.generation_complete("city", tiles=500, duration_ms=123)
    Logger.validation_result("city", passed=True, errors=0, warnings=2)
    Logger.export_complete("otbm", path="test.otbm", size_bytes=4096)
    Logger.error_summary("otbm", error="simulated error")

    assert LogLevel.DEBUG.value == "DEBUG"
    assert LogLevel.ERROR.value == "ERROR"
    print(f"[PASS] test_logger (levels: {[e.value for e in LogLevel]})")


if __name__ == "__main__":
    print("=" * 50)
    print("  V1.0 Infrastructure Tests")
    print("=" * 50)
    print()

    tests = [
        test_version,
        test_cache,
        test_benchmark,
        test_asset_registry,
        test_blueprint_registry,
        test_logger,
    ]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            failed += 1
            import traceback
            print(f"[FAIL] {fn.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{'=' * 50}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 50}")
    sys.exit(0 if failed == 0 else 1)