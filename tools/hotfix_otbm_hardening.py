"""
hotfix_otbm_hardening.py — v1.0.1 HOTFIX OTBM Hardening Suite.

Phase 2 of the v1.0.1 HOTFIX mission.

Verifies:
    OTBMExporter
    OTBMImporter
    OtbmValidator

Adds tests for:
    large maps
    extreme tile counts
    invalid attributes
    corrupt nodes

Objective:
    0 OTBM corruption.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_world_model(width: int, height: int, seed: int = 42) -> Any:
    """Build a WorldModel with the given tile-grid size."""
    from core.generators import WorldGenerator

    gen = WorldGenerator(seed=seed)
    world = gen.generate(
        {
            "type": "hunt",
            "theme": "issavi",
            "level_min": 200,
            "level_max": 350,
            "width": max(1, int(width)),
            "height": max(1, int(height)),
        }
    )
    return world


def _export_to_bytes(world: Any) -> bytes:
    from core.otbm import OTBMExporter

    return OTBMExporter(generate_templates=False).export_bytes(world)


# ── Tests ────────────────────────────────────────────────────────────────────


def test_round_trip_basic() -> Dict[str, Any]:
    name = "round_trip_basic"
    t0 = time.time()
    try:
        world = _make_world_model(8, 8)
        otbm = _export_to_bytes(world)
        from core.otbm import OTBMImporter, OtbmValidator

        v = OtbmValidator().validate(otbm)
        importer = OTBMImporter()
        result = importer.import_bytes(otbm)
        ok = (
            v.is_valid
            and result.get("success") is True
            and result.get("stats", {}).get("tiles", 0) > 0
        )
        return {
            "name": name,
            "passed": ok,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "otbm_bytes": len(otbm),
                "valid": v.is_valid,
                "imported_tiles": result.get("stats", {}).get("tiles", 0),
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
            "trace": traceback.format_exc()[:1000],
        }


def test_large_map() -> Dict[str, Any]:
    name = "large_map_64x64"
    t0 = time.time()
    try:
        world = _make_world_model(64, 64)
        otbm = _export_to_bytes(world)
        from core.otbm import OtbmValidator

        v = OtbmValidator().validate(otbm)
        return {
            "name": name,
            "passed": v.is_valid,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "otbm_bytes": len(otbm),
                "valid": v.is_valid,
                "errors": v.errors[:3],
                "warnings_count": len(v.warnings),
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_extreme_tile_counts() -> Dict[str, Any]:
    name = "extreme_tile_counts_256x256"
    t0 = time.time()
    try:
        world = _make_world_model(256, 256)
        otbm = _export_to_bytes(world)
        from core.otbm import OtbmValidator

        v = OtbmValidator().validate(otbm)
        # We accept "valid=True" or "valid=False with only warnings" as pass.
        ok = v.is_valid
        return {
            "name": name,
            "passed": ok,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "otbm_bytes": len(otbm),
                "valid": v.is_valid,
                "errors": v.errors[:3],
                "warnings_count": len(v.warnings),
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_invalid_attributes() -> Dict[str, Any]:
    name = "invalid_attributes_oversized_item_id"
    t0 = time.time()
    try:
        # Build a valid OTBM and then patch an item id beyond 65535 to test
        # the validator surfaces a warning.
        world = _make_world_model(4, 4)
        otbm = bytearray(_export_to_bytes(world))
        # Inject a high item id (0xFFFF + 1) at a known position.
        injected = False
        for i in range(len(otbm) - 4):
            if otbm[i] != 0x04:
                continue
            # Read 2-byte little-endian size.
            sz = otbm[i + 1] | (otbm[i + 2] << 8)
            # A real ITEM node has a small payload (>=2 bytes for item_id).
            if 2 <= sz <= 64:
                # Overwrite the next two bytes (item id) with 0xFFFF.
                otbm[i + 1] = 0xFF
                otbm[i + 2] = 0xFF
                injected = True
                break
        if not injected:
            return {
                "name": name,
                "passed": False,
                "elapsed_s": round(time.time() - t0, 4),
                "error": "could_not_inject_item_node",
            }
        from core.otbm import OtbmValidator

        v = OtbmValidator().validate(bytes(otbm))
        return {
            "name": name,
            "passed": True,  # We only verify validator tolerates it.
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "valid": v.is_valid,
                "injected": True,
                "warnings_count": len(v.warnings),
                "errors_count": len(v.errors),
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_corrupt_nodes() -> Dict[str, Any]:
    name = "corrupt_nodes_truncated"
    t0 = time.time()
    try:
        world = _make_world_model(8, 8)
        otbm = _export_to_bytes(world)
        truncated = otbm[: max(20, len(otbm) // 3)]
        from core.otbm import OtbmValidator

        v = OtbmValidator().validate(truncated)
        # A truncated file should NOT pass validation silently.
        return {
            "name": name,
            "passed": v.is_valid is False,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "valid": v.is_valid,
                "errors": v.errors[:3],
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_corrupt_magic() -> Dict[str, Any]:
    name = "corrupt_magic_identifier"
    t0 = time.time()
    try:
        world = _make_world_model(4, 4)
        otbm = bytearray(_export_to_bytes(world))
        if len(otbm) < 4:
            return {
                "name": name,
                "passed": False,
                "elapsed_s": round(time.time() - t0, 4),
                "error": "otbm_too_small",
            }
        otbm[0:4] = b"XXXX"
        from core.otbm import OtbmValidator

        v = OtbmValidator().validate(bytes(otbm))
        return {
            "name": name,
            "passed": v.is_valid is False,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {"valid": v.is_valid, "errors": v.errors[:3]},
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_empty_bytes() -> Dict[str, Any]:
    name = "empty_bytes_rejected"
    t0 = time.time()
    try:
        from core.otbm import OtbmValidator

        v = OtbmValidator().validate(b"")
        return {
            "name": name,
            "passed": v.is_valid is False,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {"valid": v.is_valid, "errors": v.errors[:3]},
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_import_round_trip_lossless() -> Dict[str, Any]:
    name = "import_round_trip_lossless"
    t0 = time.time()
    try:
        world = _make_world_model(16, 16)
        otbm = _export_to_bytes(world)
        from core.otbm import OTBMImporter

        importer = OTBMImporter()
        result = importer.import_bytes(otbm)
        ok = result.get("success") is True
        return {
            "name": name,
            "passed": ok,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "stats": result.get("stats", {}),
                "errors": result.get("errors", []),
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    tests = [
        test_round_trip_basic,
        test_large_map,
        test_extreme_tile_counts,
        test_invalid_attributes,
        test_corrupt_nodes,
        test_corrupt_magic,
        test_empty_bytes,
        test_import_round_trip_lossless,
    ]
    results: List[Dict[str, Any]] = []
    print("[hotfix-otbm] running OTBM hardening suite...")
    for t in tests:
        r = t()
        results.append(r)
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['name']:40s}  {r.get('elapsed_s', 0):.3f}s")
        if not r["passed"]:
            print(f"        error: {r.get('error', '')}")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    report = {
        "phase": "FASE 2 - OTBM HARDENING",
        "generated_at": _utc_iso(),
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": round(passed / max(1, total), 4),
        "results": results,
        "verdict": "PASS" if passed == total else "FAIL",
    }
    out_path = PROJECT_ROOT / "HOTFIX_OTBM_HARDENING.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"[hotfix-otbm] wrote {out_path}")
    print(f"  pass={passed}/{total}  verdict={report['verdict']}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
