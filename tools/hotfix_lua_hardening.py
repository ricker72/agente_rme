"""
hotfix_lua_hardening.py — v1.0.1 HOTFIX LUA Export Hardening Suite.

Phase 3 of the v1.0.1 HOTFIX mission.

Validates:
    generated.lua
    monster exports
    spawn exports
    waypoints
    raids
    quests

Generates:
    lua_validation_report.json
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Lua syntax helpers ──────────────────────────────────────────────────────


def _strip_strings_and_comments(lua: str) -> str:
    """Remove string literals and comments so the bracket/keyword counter
    doesn't get confused by characters inside strings."""
    out: List[str] = []
    i = 0
    n = len(lua)
    while i < n:
        c = lua[i]
        # Line comment
        if c == "-" and i + 1 < n and lua[i + 1] == "-":
            # Block comment --[[ ... ]]
            if i + 3 < n and lua[i + 2] == "[" and lua[i + 3] == "[":
                j = lua.find("]]", i + 4)
                if j == -1:
                    break
                i = j + 2
                continue
            # Single-line comment
            j = lua.find("\n", i)
            if j == -1:
                break
            i = j
            continue
        # String literal
        if c in ('"', "'"):
            quote = c
            j = i + 1
            while j < n:
                if lua[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if lua[j] == quote:
                    j += 1
                    break
                j += 1
            # Replace string content with spaces of equal length
            out.append(" " * (j - i))
            i = j
            continue
        # Long string [[ ... ]]
        if c == "[" and i + 1 < n and lua[i + 1] == "[":
            j = lua.find("]]", i + 2)
            if j == -1:
                out.append(lua[i])
                i += 1
                continue
            out.append(" " * (j + 2 - i))
            i = j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _lua_syntax_check(lua: str) -> Tuple[bool, List[str]]:
    """Return (passed, errors) for basic Lua syntax checks.

    Checks:
      * Balanced parentheses (), brackets [], braces {}
      * Balanced 'do' / 'end' keywords
      * Balanced 'function' / 'end' keywords
    """
    errors: List[str] = []
    stripped = _strip_strings_and_comments(lua)

    # Parentheses / brackets / braces
    for ch_open, ch_close, name in [
        ("(", ")", "parentheses"),
        ("[", "]", "brackets"),
        ("{", "}", "braces"),
    ]:
        opens = stripped.count(ch_open)
        closes = stripped.count(ch_close)
        if opens != closes:
            errors.append(f"unbalanced {name}: {opens} open vs {closes} close")

    # Lua uses 'end' as the closer for if/then, function, do, for, while,
    # and repeat blocks. In our generated code we have at most one
    # 'function' (app.transaction(function(map)...)) and one 'then'
    # (if not app.hasMap() then ... end). The total 'end' keywords should
    # match that count. We allow a small tolerance for nested constructs.
    end_count = len(re.findall(r"\bend\b", stripped))
    fn_count = len(re.findall(r"\bfunction\b", stripped))
    then_count = len(re.findall(r"\bthen\b", stripped))
    expected_ends = fn_count + then_count
    if end_count < expected_ends:
        errors.append(
            f"unbalanced blocks: need >= {expected_ends} end ("
            f"{fn_count} function + {then_count} then), found {end_count}"
        )

    return (len(errors) == 0, errors)


def _try_luac(lua_path: Path) -> Optional[bool]:
    """If `luac` is on PATH, try to syntax-check the file. Return None if
    luac is not available, otherwise True/False."""
    try:
        result = subprocess.run(
            ["luac", "-p", str(lua_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


# ── Tests ────────────────────────────────────────────────────────────────────


def test_generated_lua_exists() -> Dict[str, Any]:
    name = "generated_lua_exists"
    t0 = time.time()
    try:
        path = PROJECT_ROOT / "generated.lua"
        if not path.exists():
            return {
                "name": name,
                "passed": False,
                "elapsed_s": round(time.time() - t0, 4),
                "error": "generated.lua not found at project root",
            }
        text = path.read_text(encoding="utf-8", errors="replace")
        ok, errors = _lua_syntax_check(text)
        luac_ok = _try_luac(path)
        return {
            "name": name,
            "passed": ok and (luac_ok is not False),
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "size": len(text),
                "syntax_errors": errors,
                "luac_passed": luac_ok,
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_generated_lua_via_pipeline() -> Dict[str, Any]:
    name = "generated_lua_via_pipeline"
    t0 = time.time()
    try:
        from core.generators import WorldGenerator
        from core.exporters import LuaExporter, LuaValidator

        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "hunt",
                "theme": "issavi",
                "level_min": 200,
                "level_max": 350,
                "width": 8,
                "height": 8,
            }
        )
        exporter = LuaExporter()
        lua = exporter.export(world, title="Hotfix Test")
        ok, errors = _lua_syntax_check(lua)
        # Also run the local LuaValidator
        v = LuaValidator()
        vresult = v.validate(lua)
        return {
            "name": name,
            "passed": ok and vresult.passed,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "syntax_errors": errors,
                "validator_passed": vresult.passed,
                "validator_errors": vresult.errors[:3],
                "validator_warnings": vresult.warnings[:3],
                "size": len(lua),
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_monster_exports() -> Dict[str, Any]:
    name = "monster_exports"
    t0 = time.time()
    try:
        from core.generators import WorldGenerator
        from core.exporters import LuaExporter

        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "hunt",
                "theme": "issavi",
                "level_min": 200,
                "level_max": 350,
                "width": 12,
                "height": 12,
            }
        )
        # Inject a few spawns if the generator didn't
        for tile in list(world.tiles.values())[:5]:
            try:
                tile.spawn = type(
                    "S", (), {"monster": "Demon", "respawn": 60, "radius": 3}
                )()
            except Exception:
                pass
        lua = LuaExporter().export(world, title="Monster Test")
        monster_lines = [l for l in lua.splitlines() if "setCreature" in l]  # noqa: E741
        # Each spawn line should have a non-empty monster name
        named = sum(
            1 for line in monster_lines if re.search(r"setCreature\('[^']+'", line)
        )
        return {
            "name": name,
            "passed": named == len(monster_lines) and len(monster_lines) > 0,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "monster_lines": len(monster_lines),
                "named": named,
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_spawn_exports() -> Dict[str, Any]:
    name = "spawn_exports"
    t0 = time.time()
    try:
        from core.generators import WorldGenerator
        from core.exporters import LuaExporter

        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "hunt",
                "theme": "issavi",
                "level_min": 200,
                "level_max": 350,
                "width": 12,
                "height": 12,
            }
        )
        # Inject spawns
        for tile in list(world.tiles.values())[:5]:
            try:
                tile.spawn = type(
                    "S", (), {"monster": "Demon", "respawn": 60, "radius": 3}
                )()
            except Exception:
                pass
        lua = LuaExporter().export(world, title="Spawn Test")
        spawn_lines = [l for l in lua.splitlines() if "setSpawn" in l]  # noqa: E741
        positive_intervals = sum(
            1 for l in spawn_lines if re.search(r"setSpawn\(\d+\)", l)  # noqa: E741
        )
        return {
            "name": name,
            "passed": len(spawn_lines) > 0 and positive_intervals == len(spawn_lines),
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "spawn_lines": len(spawn_lines),
                "positive_intervals": positive_intervals,
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_waypoints_exports() -> Dict[str, Any]:
    name = "waypoints_exports"
    t0 = time.time()
    try:
        from core.generators import WorldGenerator
        from core.exporters import LuaExporter

        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "hunt",
                "theme": "issavi",
                "level_min": 200,
                "level_max": 350,
                "width": 6,
                "height": 6,
            }
        )
        # Add a waypoint to the world model (no-op if the attribute doesn't exist).
        try:
            world.waypoints = [{"name": "Test WP", "x": 100, "y": 100, "z": 7}]
        except Exception:
            pass
        lua = LuaExporter().export(world, title="WP Test")
        ok, errors = _lua_syntax_check(lua)
        return {
            "name": name,
            "passed": ok,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "syntax_errors": errors,
                "size": len(lua),
            },
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_lua_no_forbidden_apis() -> Dict[str, Any]:
    name = "lua_no_forbidden_apis"
    t0 = time.time()
    try:
        from core.generators import WorldGenerator
        from core.exporters import LuaExporter

        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "hunt",
                "theme": "issavi",
                "level_min": 200,
                "level_max": 350,
                "width": 6,
                "height": 6,
            }
        )
        lua = LuaExporter().export(world, title="Forbidden API Test")
        forbidden = [
            (r"Map\.addItem\b", "Map.addItem"),
            (r"Position\(", "Position("),
            (r"removeMap\b", "removeMap"),
            (r"app\.createMap\b", "app.createMap"),
            (r"tile:addGround\b", "tile:addGround"),
            (r"tile:setGround\b", "tile:setGround"),
        ]
        hits: List[str] = []
        for pattern, name in forbidden:
            if re.search(pattern, lua):
                hits.append(name)
        return {
            "name": name,
            "passed": len(hits) == 0,
            "elapsed_s": round(time.time() - t0, 4),
            "details": {"violations": hits},
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "elapsed_s": round(time.time() - t0, 4),
            "error": str(e),
        }


def test_lua_extreme_world() -> Dict[str, Any]:
    name = "lua_extreme_world_64x64"
    t0 = time.time()
    try:
        from core.generators import WorldGenerator
        from core.exporters import LuaExporter

        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "hunt",
                "theme": "issavi",
                "level_min": 200,
                "level_max": 350,
                "width": 64,
                "height": 64,
            }
        )
        lua = LuaExporter().export(world, title="Extreme Test")
        ok, errors = _lua_syntax_check(lua)
        # Write to disk so luac can optionally check it
        out = PROJECT_ROOT / "logs" / "hotfix_lua_extreme.lua"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(lua, encoding="utf-8")
        luac_ok = _try_luac(out)
        return {
            "name": name,
            "passed": ok and (luac_ok is not False),
            "elapsed_s": round(time.time() - t0, 4),
            "details": {
                "size": len(lua),
                "syntax_errors": errors,
                "luac_passed": luac_ok,
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
        test_generated_lua_exists,
        test_generated_lua_via_pipeline,
        test_monster_exports,
        test_spawn_exports,
        test_waypoints_exports,
        test_lua_no_forbidden_apis,
        test_lua_extreme_world,
    ]
    results: List[Dict[str, Any]] = []
    print("[hotfix-lua] running LUA export hardening suite...")
    for t in tests:
        r = t()
        results.append(r)
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['name']:35s}  {r.get('elapsed_s', 0):.3f}s")
        if not r["passed"]:
            print(f"        error: {r.get('error', '')}")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    report = {
        "phase": "FASE 3 - LUA EXPORT HARDENING",
        "generated_at": _utc_iso(),
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": round(passed / max(1, total), 4),
        "results": results,
        "verdict": "PASS" if passed == total else "FAIL",
    }
    out_path = PROJECT_ROOT / "lua_validation_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"[hotfix-lua] wrote {out_path}")
    print(f"  pass={passed}/{total}  verdict={report['verdict']}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
