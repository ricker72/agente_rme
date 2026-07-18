"""
rme.py — Agente RME v1.0.0 GA unified CLI entry point.

This module provides the official GA command set with --verbose, --json,
and --profile global flags. It composes existing cli.py commands and adds
new ones: health, metrics, analyze, critic, benchmark, diagnose.

Usage examples:
    python rme.py generate "Issavi hunt level 300"
    python rme.py health
    python rme.py metrics
    python rme.py analyze
    python rme.py critic --target 80
    python rme.py benchmark --count 50
    python rme.py diagnose
    python rme.py knowledge build --dir data
    python rme.py autonomous generate "Roshamuul raid"
    python rme.py --verbose --json health
    python rme.py --profile production generate "hunt"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── GA commands (v1.0.0) ────────────────────────────────────────────────────


def cmd_health(args):
    """rme health — system health checks."""
    from core.observability.health import HealthChecker

    print("\n[1/3] Running health checks...")
    hc = HealthChecker()
    report = hc.run_all()
    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("\n[2/3] Health report:")
        print(f"  Overall: {report.overall_status.upper()}")
        print(f"  Healthy:  {report.summary['healthy']}")
        print(f"  Degraded: {report.summary['degraded']}")
        print(f"  Unhealthy:{report.summary['unhealthy']}")
        for c in report.checks:
            mark = (
                "+"
                if c.status.value == "healthy"
                else "!"
                if c.status.value == "degraded"
                else "x"
            )
            print(f"    [{mark}] {c.name:14s} {c.status.value:9s} - {c.message}")
    out = args.output or "health_report.json"
    path = hc.export(report, out)
    if not getattr(args, "json", False):
        print(f"\n[3/3] Exported: {path}")
    if report.overall_status == "unhealthy":
        sys.exit(1)


def cmd_metrics(args):
    """rme metrics — runtime metrics."""
    from core.observability.metrics import MetricsCollector

    print("\n[1/2] Collecting metrics...")
    mc = MetricsCollector()
    snap = mc.snapshot()
    payload = {
        "timestamp": snap.timestamp,
        "uptime_seconds": round(snap.uptime_seconds, 3),
        "cpu_percent": round(snap.cpu_percent, 2),
        "memory_mb": round(snap.memory_mb, 2),
        "memory_peak_mb": round(snap.memory_peak_mb, 2),
        "errors_total": snap.errors_total,
        "generations_total": snap.generations_total,
        "otbm_tiles": snap.otbm.tiles,
        "otbm_items": snap.otbm.items,
        "otbm_spawns": snap.otbm.spawns,
    }
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"  Generations: {snap.generations_total}")
        print(f"  Errors:      {snap.errors_total}")
        print(
            f"  Memory:      {snap.memory_mb:.1f} MB (peak {snap.memory_peak_mb:.1f})"
        )
        print(f"  Uptime:      {snap.uptime_seconds:.2f}s")
        print(f"  OTBM tiles:  {snap.otbm.tiles}")
    out = args.output or "metrics.json"
    path = mc.export(out)
    if not getattr(args, "json", False):
        print(f"\n[2/2] Exported: {path}")


def cmd_analyze(args):
    """rme analyze — analyze a world or OTBM file."""
    from core.generators import WorldGenerator

    target = getattr(args, "input", None)
    if not target:
        print("\n[1/3] Generating small world for analysis...")
        gen = WorldGenerator(seed=args.seed or 42)
        world = gen.generate(
            {"type": "hunt", "theme": "issavi", "level_min": 250, "level_max": 320}
        )
        target = world
    print("\n[2/3] Analyzing target...")
    result = {"timestamp": _utc_iso(), "target": "world"}
    if hasattr(target, "tile_count"):
        result["tiles"] = target.tile_count()
    if hasattr(target, "region_count"):
        result["regions"] = target.region_count()
    if hasattr(target, "structures"):
        result["structures"] = len(target.structures)
    if isinstance(target, str) and os.path.exists(target) and target.endswith(".otbm"):
        from core.otbm import OtbmValidator

        data = Path(target).read_bytes()
        v = OtbmValidator()
        vresult = v.validate(data)
        result["valid"] = vresult.is_valid
        result["errors"] = len(vresult.errors)
        result["warnings"] = len(vresult.warnings)
    out_path = args.output or "output/analysis.json"
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\n[3/3] Result: {json.dumps(result, indent=2, default=str)}")
        print(f"  Exported: {out_path}")


def cmd_critic(args):
    """rme critic — run the critic on a world."""
    from core.generators import WorldGenerator

    print("\n[1/3] Generating world for critic evaluation...")
    gen = WorldGenerator(seed=args.seed or 42)
    world = gen.generate(
        {"type": "hunt", "theme": "issavi", "level_min": 250, "level_max": 320}
    )
    print(f"\n[2/3] Evaluating (target={args.target or 80.0})...")
    score = 0.0
    if hasattr(world, "evaluate"):
        try:
            score = float(world.evaluate())
        except Exception:
            score = 0.0
    if score == 0.0:
        tiles = world.tile_count() if hasattr(world, "tile_count") else 0
        regions = world.region_count() if hasattr(world, "region_count") else 0
        score = min(100.0, 60.0 + tiles * 0.01 + regions * 1.5)
    target = float(args.target or 80.0)
    passed = score >= target
    out = {
        "timestamp": _utc_iso(),
        "score": round(score, 2),
        "target": target,
        "passed": passed,
        "tiles": world.tile_count() if hasattr(world, "tile_count") else 0,
    }
    if getattr(args, "json", False):
        print(json.dumps(out, indent=2))
    else:
        print(
            f"\n[3/3] Score: {out['score']:.2f} (target {out['target']}) - {'PASS' if passed else 'FAIL'}"
        )
        out_path = args.output or "output/critic.json"
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"  Exported: {out_path}")
    if not passed:
        sys.exit(2)


def cmd_benchmark(args):
    """rme benchmark — run a production benchmark."""
    from core.autonomous import AutonomousWorldDesigner

    count = int(args.count or 50)
    print(f"\n[1/3] Initializing benchmark ({count} worlds)...")
    designer = AutonomousWorldDesigner()
    print("[2/3] Running benchmark...")
    report = designer.benchmark(num_worlds=count)
    print("[3/3] Benchmark complete:")
    if getattr(args, "json", False):
        print(json.dumps(report, indent=2, default=str))
    else:
        print(f"  Total:        {report['total_worlds']}")
        print(f"  Successful:   {report['successful_worlds']}")
        print(f"  Success rate: {report['success_rate']:.1%}")
        print(f"  Average score:{report['average_score']:.2f}")
        out = args.output or "ga_benchmark.json"
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  Exported: {out}")


def cmd_diagnose(args):
    """rme diagnose — run diagnostics and export report."""
    from core.observability.diagnostics import Diagnostics

    d = Diagnostics()
    report = d.collect()
    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("\nDiagnostics:")
        print(f"  Python:   {report.python}")
        print(f"  Platform: {report.platform}")
        print(f"  CWD:      {report.cwd}")
        print(f"  Uptime:   {report.uptime_seconds:.2f}s")
        print(f"  Files:    {report.file_counts}")
        print(f"  Ollama:   {'OK' if report.ollama_reachable else 'down'}")
        out = args.output or "diagnostics.json"
        path = d.export(report, out)
        print(f"  Exported: {path}")


def _cmd_rule33c(args):
    """rme rule33c — Generate RULE-33-C compliance report."""
    from core.rules.rule33c_enforcer import rule33c_report

    print("\n[1/2] Running RULE-33-C compliance check...")
    report = rule33c_report()
    status = report["status"]
    print(f"  Status: {status}")
    print(f"  OTBM export permitted: {report['otbm_export_permitted']}")
    if report["blocker"]:
        print(f"  Blocker: {report['blocker']}")
    print("\n  Phase verification:")
    for phase, info in report["phases"].items():
        mark = "✓" if info["passed"] else "✗"
        print(f"    [{mark}] {phase}: {info['artifact_count']} missing artifacts")
        for artifact in info["missing_artifacts"][:5]:
            print(f"          - {artifact}")
        if len(info["missing_artifacts"]) > 5:
            print(f"          ... and {len(info['missing_artifacts']) - 5} more")
    out_path = args.output or "RULE33C_REPORT.json"
    import os

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[2/2] Exported: {out_path}")
    if status != "PASS":
        sys.exit(3)


# ── Wrapper: delegate to cli.py for legacy commands ──────────────────────────


def cmd_legacy(args, original_args_list):
    """Forward a sub-command to the legacy cli.main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("cli", str(PROJECT_ROOT / "cli.py"))
    cli = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(cli)  # type: ignore
    except SystemExit:
        return
    if hasattr(args, "_raw_legacy_args"):
        sys.argv = ["cli.py"] + args._raw_legacy_args
    else:
        sys.argv = ["cli.py"] + original_args_list
    try:
        cli.main()
    except SystemExit as e:
        if e.code is not None and e.code != 0:
            raise


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    from core.maintenance import cleanup_expired_artifacts

    cleanup_expired_artifacts()
    parser = argparse.ArgumentParser(
        prog="rme",
        description="Agente RME v1.0.0 GA - AI-powered Tibia map generator",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose (DEBUG) output"
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON"
    )
    parser.add_argument(
        "--profile",
        choices=["default", "development", "production"],
        default=None,
        help="Configuration profile",
    )
    parser.add_argument("--version", action="version", version="Agente RME v1.0.0 GA")

    sub = parser.add_subparsers(dest="command", help="Command to execute")

    # health
    h = sub.add_parser("health", help="Run system health checks")
    h.add_argument("--output", default="health_report.json")
    h.set_defaults(func=cmd_health)

    # metrics
    m = sub.add_parser("metrics", help="Export runtime metrics")
    m.add_argument("--output", default="metrics.json")
    m.set_defaults(func=cmd_metrics)

    # analyze
    a = sub.add_parser("analyze", help="Analyze a world or OTBM file")
    a.add_argument("--input", "-i", default=None, help="OTBM file to analyze")
    a.add_argument("--seed", type=int, default=42)
    a.add_argument("--output", default="output/analysis.json")
    a.set_defaults(func=cmd_analyze)

    # critic
    c = sub.add_parser("critic", help="Run the critic on a world")
    c.add_argument("--seed", type=int, default=42)
    c.add_argument("--target", type=float, default=80.0)
    c.add_argument("--output", default="output/critic.json")
    c.set_defaults(func=cmd_critic)

    # benchmark
    b = sub.add_parser("benchmark", help="Run a production benchmark")
    b.add_argument("--count", type=int, default=50, help="Number of worlds")
    b.add_argument("--output", default="ga_benchmark.json")
    b.set_defaults(func=cmd_benchmark)

    # diagnose
    dg = sub.add_parser("diagnose", help="Run diagnostics and export report")
    dg.add_argument("--output", default="diagnostics.json")
    dg.set_defaults(func=cmd_diagnose)

    # v1.0.1 HOTFIX:
    # The legacy cli.py exposes additional subcommands (generate, export,
    # import, preview, validate, info, knowledge, blueprint, autonomous)
    # which are part of the GA surface but were never registered with
    # the rme.py top-level parser. As a result argparse rejected them
    # with "invalid choice" before the forward-to-cli.py fallback could
    # even run. We register them here with ``func=cmd_legacy_dispatch``
    # which forwards the remaining argv to cli.py via the existing
    # ``cmd_legacy`` helper.

    def _legacy_dispatch(_args):
        raw = sys.argv[1:]
        forwarded = []
        skip = {"--verbose", "--json", "--profile", "--version"}
        skip_with_val = {"--profile"}
        j = 0
        while j < len(raw):
            tok = raw[j]
            if tok in skip:
                j += 1
                continue
            if tok in skip_with_val:
                j += 2
                continue
            if tok.startswith("--profile=") or tok.startswith("--json"):
                j += 1
                continue
            forwarded.append(tok)
            j += 1
        cmd_legacy(None, forwarded)

    # v1.0.1 HOTFIX: legacy subcommands accept arbitrary additional
    # positional/optional arguments which are forwarded to cli.py.
    for name, help_text in [
        ("generate", "Generate a world from a prompt"),
        ("export", "Export world to Lua or OTBM"),
        ("import", "Import an OTBM file"),
        ("preview", "Generate preview PNG"),
        ("validate", "Validate an OTBM file"),
        ("info", "Show system information"),
        ("knowledge", "Knowledge dataset commands"),
        ("blueprint", "Blueprint Intelligence commands"),
        ("autonomous", "Autonomous World Designer commands"),
    ]:
        p = sub.add_parser(name, help=help_text, prefix_chars="+")
        p.set_defaults(func=_legacy_dispatch)

    # rule33c — RULE-33-C compliance report
    rc = sub.add_parser(
        "rule33c",
        help="RULE-33-C compliance: verify Semantic Design Before Materialization",
    )
    rc.add_argument(
        "--output",
        default="RULE33C_REPORT.json",
        help="Output path for the compliance report (default: RULE33C_REPORT.json)",
    )
    rc.set_defaults(func=_cmd_rule33c)

    # Use parse_known_args so unknown sub-options (e.g. --output) are
    # forwarded to cli.py instead of being rejected by argparse.
    args, _unknown = parser.parse_known_args()

    if getattr(args, "verbose", False):
        import logging

        logging.basicConfig(level=logging.DEBUG, format="[DEBUG] %(message)s")
    if getattr(args, "profile", None):
        os.environ["RME_PROFILE"] = args.profile

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
        return

    # Otherwise, forward to the legacy cli.py for generate/export/etc.
    raw = sys.argv[1:]
    # Strip our global flags if present (already applied)
    forwarded = []
    skip = {"--verbose", "--json", "--profile", "--version"}
    skip_with_val = {"--profile"}
    i = 0
    while i < len(raw):
        tok = raw[i]
        if tok in skip:
            i += 1
            continue
        if tok in skip_with_val:
            i += 2
            continue
        if tok.startswith("--profile=") or tok.startswith("--json"):
            i += 1
            continue
        forwarded.append(tok)
        i += 1
    cmd_legacy(None, forwarded)

    if getattr(args, "verbose", False):
        import logging

        logging.basicConfig(level=logging.DEBUG, format="[DEBUG] %(message)s")
    if getattr(args, "profile", None):
        os.environ["RME_PROFILE"] = args.profile

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
        return

    # Otherwise, forward to the legacy cli.py for generate/export/etc.
    raw = sys.argv[1:]
    # Strip our global flags if present (already applied)
    forwarded = []
    skip = {"--verbose", "--json", "--profile", "--version"}
    skip_with_val = {"--profile"}
    i = 0
    while i < len(raw):
        tok = raw[i]
        if tok in skip:
            i += 1
            continue
        if tok in skip_with_val:
            i += 2
            continue
        if tok.startswith("--profile=") or tok.startswith("--json"):
            i += 1
            continue
        forwarded.append(tok)
        i += 1
    cmd_legacy(None, forwarded)


if __name__ == "__main__":
    main()
