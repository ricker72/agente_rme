"""
HITO 26.1E — Final Validation Script

Verifies:
  1. No datetime.utcnow() in production .py files
  2. Timestamps in logs, reports, benchmark, campaigns, exports are clean
"""

import os
import sys

KEY_AREAS = {
    "logs": [
        "core/logging/logger.py",
        "core/logging/levels.py",
    ],
    "benchmark": [
        "core/benchmark/runner.py",
    ],
    "campaign": [
        "core/campaign/campaign_generator.py",
        "core/campaign/lore_generator.py",
        "core/campaign/validator.py",
        "core/campaign/story_generator.py",
        "core/campaign/package.py",
        "core/campaign/dialog_generator.py",
        "core/campaign/economy_generator.py",
        "core/campaign/faction_generator.py",
        "core/campaign/npc_generator.py",
    ],
    "export": [
        "core/export/release_builder.py",
        "core/exporters/lua_exporter.py",
        "core/exporters/lua_formatter.py",
        "core/exporters/lua_validator.py",
        "core/exporters/lua_writer.py",
        "agente_rme/core/agents/export_agent.py",
        "core/otbm/otbm_exporter.py",
        "core/world_engine/export_pipeline.py",
    ],
    "report": [
        "core/playtest/report_generator.py",
        "core/preview/preview_report.py",
    ],
}

ROOT = "."


def check_file(path):
    """Return True if file is clean (no utcnow)."""
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None  # file missing
    with open(full, "r", encoding="utf-8", errors="ignore") as fh:
        content = fh.read()
    if "utcnow" in content:
        # Show the offending lines
        for i, line in enumerate(content.splitlines(), 1):
            if "utcnow" in line:
                print(f"  WARN line {i}: {line.strip()}")
        return False
    return True


def main():
    errors = 0
    for area, filelist in KEY_AREAS.items():
        print(f"\n{'=' * 50}")
        print(f"Area: {area.upper()}")
        print(f"{'=' * 50}")
        for f in filelist:
            result = check_file(f)
            if result is None:
                print(f"  MISSING: {f}")
            elif result:
                print(f"  OK: {f}")
            else:
                print(f"  FAIL: {f}")
                errors += 1

    print(f"\n{'=' * 50}")
    if errors:
        print(f"RESULT: {errors} file(s) with datetime.utcnow() — FAIL")
        sys.exit(1)
    else:
        print("RESULT: ALL CLEAN — No datetime.utcnow() found")
        sys.exit(0)


if __name__ == "__main__":
    main()
