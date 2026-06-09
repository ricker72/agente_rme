"""
cli.py — Command Line Interface for RME Map AI Agent v2.0

Usage:
    python cli.py generate "Generate Issavi hunt level 300"
    python cli.py generate --type dungeon --theme issavi --level 200 --size 30x30
    python cli.py export --input output/map.otbm --format lua
    python cli.py import --input map.otbm --output output/imported.otbm
    python cli.py preview --input output/map.otbm --output output/preview.png
    python cli.py validate --input output/map.otbm
    python cli.py info
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _banner():
    print("=" * 60)
    print("  RME Map AI Agent v2.0 — Production Release")
    print("  AI-powered Tibia map generator for RME")
    print("=" * 60)


# ── generate ─────────────────────────────────────────────────────────────────

def cmd_generate(args):
    """Generate a world from a natural language prompt."""
    from core.generators import WorldGenerator
    from core.exporters import LuaExporter, LuaValidator
    from core.otbm import OTBMExporter
    from core.preview import PreviewGenerator

    prompt = args.prompt or ""
    config = {}

    if args.type:
        config["type"] = args.type
    if args.theme:
        config["theme"] = args.theme
    if args.level:
        config["level_min"] = max(1, args.level - 20)
        config["level_max"] = args.level + 20
    if args.size:
        parts = args.size.lower().split("x")
        if len(parts) == 2:
            config["width"] = int(parts[0])
            config["height"] = int(parts[1])

    if prompt:
        config["prompt"] = prompt

    seed = args.seed if args.seed is not None else 42
    output_dir = args.output or "output"

    print(f"\n[1/5] Generating world from prompt...")
    t0 = time.time()
    generator = WorldGenerator(seed=seed)
    world = generator.generate(config if config else prompt or "Generate Issavi hunt level 300")
    t1 = time.time()
    print(f"  WorldModel created: {world.tile_count()} tiles in {t1 - t0:.2f}s")

    # Lua export
    print(f"\n[2/5] Exporting Lua script...")
    lua_exporter = LuaExporter()
    lua_code = lua_exporter.export(world, title=prompt or "CLI Generated")
    lua_path = os.path.join(output_dir, "generated.lua")
    os.makedirs(output_dir, exist_ok=True)
    with open(lua_path, "w", encoding="utf-8") as f:
        f.write(lua_code)
    print(f"  Lua script: {lua_path} ({len(lua_code)} bytes)")

    # Validate Lua
    validator = LuaValidator()
    vresult = validator.validate(lua_code)
    if vresult.passed:
        print(f"  Lua validation: PASSED")
    else:
        print(f"  Lua validation: FAILED — {vresult.errors}")

    # OTBM export
    print(f"\n[3/5] Exporting OTBM binary...")
    otbm_exporter = OTBMExporter()
    otbm_path = os.path.join(output_dir, "generated.otbm")
    report = otbm_exporter.export(world, otbm_path)
    print(f"  OTBM: {otbm_path} — {report.get('status', 'unknown')}")
    print(f"  Tiles: {report.get('tiles', 0)}, Items: {report.get('items', 0)}, Spawns: {report.get('spawns', 0)}")

    # Preview
    print(f"\n[4/5] Generating preview PNG...")
    preview_gen = PreviewGenerator()
    preview_path = os.path.join(output_dir, "generated_preview.png")
    result = preview_gen.generate(world, output_png=preview_path)
    if result.get("png"):
        print(f"  Preview: {result['png']}")
    else:
        print(f"  Preview: generation skipped (no PIL or empty world)")

    # Summary
    print(f"\n[5/5] Pipeline complete!")
    total_time = time.time() - t0
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Output directory: {output_dir}/")
    print(f"    - generated.lua")
    print(f"    - generated.otbm")
    print(f"    - generated_preview.png")
    if report.get("files", {}).get("monster_xml"):
        print(f"    - generated.monster.xml")
    if report.get("files", {}).get("houses_xml"):
        print(f"    - generated.houses.xml")
    if report.get("files", {}).get("waypoints_xml"):
        print(f"    - generated.waypoints.xml")

    # Save report
    report_path = os.path.join(output_dir, "generated_report.json")

    # Convert config to JSON-safe dict (remove non-serializable objects)
    safe_config = {}
    for k, v in config.items():
        try:
            json.dumps(v)
            safe_config[k] = v
        except (TypeError, ValueError):
            safe_config[k] = str(v)

    # Make OTBM report JSON-safe too
    safe_report = {}
    for k, v in report.items():
        try:
            json.dumps(v)
            safe_report[k] = v
        except (TypeError, ValueError):
            safe_report[k] = str(v)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "prompt": prompt,
            "config": safe_config,
            "tiles": world.tile_count(),
            "regions": world.region_count(),
            "structures": len(world.structures),
            "lua_bytes": len(lua_code),
            "otbm_report": safe_report,
            "generation_time": total_time,
        }, f, indent=2, ensure_ascii=False)
    print(f"    - generated_report.json")
    print()


# ── export ───────────────────────────────────────────────────────────────────

def cmd_export(args):
    """Export a WorldModel to Lua or OTBM format."""
    from core.generators import WorldGenerator

    print(f"\nGenerating world for export...")
    generator = WorldGenerator(seed=args.seed or 42)
    config = {
        "type": args.type or "hunt",
        "theme": args.theme or "issavi",
        "level_min": 280,
        "level_max": 320,
    }
    world = generator.generate(config)

    output_dir = args.output or "output"
    os.makedirs(output_dir, exist_ok=True)

    fmt = args.format.lower() if args.format else "lua"

    if fmt == "lua":
        from core.exporters import LuaExporter
        exporter = LuaExporter()
        code = exporter.export(world, title="CLI Export")
        out_path = os.path.join(output_dir, "exported.lua")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  Exported Lua: {out_path} ({len(code)} bytes)")

    elif fmt == "otbm":
        from core.otbm import OTBMExporter
        exporter = OTBMExporter()
        out_path = os.path.join(output_dir, "exported.otbm")
        report = exporter.export(world, out_path)
        print(f"  Exported OTBM: {out_path}")
        print(f"  Report: {json.dumps(report, indent=2)}")

    else:
        print(f"  Unknown format: {fmt}. Use 'lua' or 'otbm'.")
        sys.exit(1)


# ── import ───────────────────────────────────────────────────────────────────

def cmd_import(args):
    """Import an OTBM file."""
    from core.otbm import OTBMImporter

    input_path = args.input
    if not input_path or not os.path.exists(input_path):
        print(f"  Error: File not found: {input_path}")
        sys.exit(1)

    print(f"\nImporting OTBM: {input_path}")
    importer = OTBMImporter()
    result = importer.import_file(input_path)

    if result.get("success"):
        print(f"  Import: SUCCESS")
        stats = result.get("stats", {})
        print(f"  Tiles: {stats.get('tiles', 0)}")
        print(f"  Spawns: {stats.get('spawns', 0)}")
        print(f"  Cities: {stats.get('cities', 0)}")
        print(f"  Waypoints: {stats.get('waypoints', 0)}")

        if args.output:
            # Re-export
            from core.otbm import OTBMExporter
            world_model = result.get("world_model")
            if world_model:
                exporter = OTBMExporter()
                report = exporter.export(world_model, args.output)
                print(f"  Re-exported to: {args.output}")
                print(f"  Report: {report.get('status', 'unknown')}")
    else:
        print(f"  Import: FAILED")
        print(f"  Error: {result.get('error', 'unknown')}")
        sys.exit(1)


# ── preview ──────────────────────────────────────────────────────────────────

def cmd_preview(args):
    """Generate a preview PNG from a world."""
    from core.generators import WorldGenerator
    from core.preview import PreviewGenerator

    print(f"\nGenerating preview...")
    generator = WorldGenerator(seed=args.seed or 42)
    config = {
        "type": args.type or "hunt",
        "theme": args.theme or "issavi",
        "level_min": 280,
        "level_max": 320,
    }
    world = generator.generate(config)

    output_path = args.output or "output/preview.png"
    preview_gen = PreviewGenerator()
    result = preview_gen.generate(world, output_png=output_path)

    if result.get("png"):
        print(f"  Preview: {result['png']}")
    else:
        print(f"  Preview: generation failed or PIL not installed")
        sys.exit(1)


# ── validate ─────────────────────────────────────────────────────────────────

def cmd_validate(args):
    """Validate an OTBM file."""
    from core.otbm import OtbmValidator

    input_path = args.input
    if not input_path or not os.path.exists(input_path):
        print(f"  Error: File not found: {input_path}")
        sys.exit(1)

    print(f"\nValidating OTBM: {input_path}")
    data = Path(input_path).read_bytes()
    validator = OtbmValidator()
    result = validator.validate(data)

    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    for err in result.errors[:10]:
        print(f"    - {err}")
    print(f"  Warnings: {len(result.warnings)}")
    for warn in result.warnings[:10]:
        print(f"    - {warn}")


# ── info ─────────────────────────────────────────────────────────────────────

def cmd_info(args):
    """Show system information."""
    _banner()
    print(f"\nSystem Information:")
    print(f"  Python: {sys.version}")
    print(f"  Platform: {sys.platform}")
    print(f"  Working directory: {os.getcwd()}")
    print(f"  Project root: {PROJECT_ROOT}")

    # Check dependencies
    deps = {
        "customtkinter": "GUI framework",
        "ollama": "AI model integration",
        "requests": "HTTP client",
        "PIL": "Image rendering (Pillow)",
        "lxml": "XML parsing",
        "numpy": "Numerical operations",
        "yaml": "YAML config (PyYAML)",
    }
    print(f"\nDependencies:")
    for mod, desc in deps.items():
        try:
            __import__(mod)
            print(f"  [OK] {mod} -- {desc}")
        except ImportError:
            print(f"  [--] {mod} -- {desc} (NOT INSTALLED)")

    # Check Ollama
    print(f"\nOllama:")
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get("models", [])
            print(f"  [OK] Running -- {len(models)} models available")
            for m in models[:5]:
                print(f"    - {m.get('name', 'unknown')}")
        else:
            print(f"  [--] Not responding (status {r.status_code})")
    except Exception:
        print(f"  [--] Not available at localhost:11434")

    print()


# ── knowledge ─────────────────────────────────────────────────────────────────

def _discover_sources(directory: str) -> list:
    """Discover .json files in a directory to use as knowledge sources."""
    if not os.path.isdir(directory):
        return []
    out = []
    for name in sorted(os.listdir(directory)):
        p = os.path.join(directory, name)
        if os.path.isfile(p) and p.lower().endswith((".json", ".otbm")):
            out.append(p)
    return out


def _load_or_build_engine(args) -> "KnowledgeEngine":
    from core.knowledge import KnowledgeEngine, DatasetBuilder

    dataset_path = getattr(args, "dataset", None) or "output/knowledge_dataset.json"
    if not os.path.isabs(dataset_path):
        dataset_path = os.path.abspath(dataset_path)
    if os.path.exists(dataset_path):
        return KnowledgeEngine.load(dataset_path)
    # Try to auto-discover sources
    auto_dir = getattr(args, "auto_dir", None) or "data"
    sources = _discover_sources(auto_dir)
    if not sources:
        return KnowledgeEngine()
    builder = DatasetBuilder()
    ds = builder.build_from_sources(sources)
    return KnowledgeEngine(dataset=ds)


def cmd_knowledge(args):
    """Dispatch `rme knowledge ...` sub-commands."""
    sub = getattr(args, "knowledge_command", None)
    if sub == "build":
        cmd_knowledge_build(args)
    elif sub == "search":
        cmd_knowledge_search(args)
    elif sub == "similar":
        cmd_knowledge_similar(args)
    elif sub == "stats":
        cmd_knowledge_stats(args)
    else:
        print("  Usage: rme knowledge {build|search|similar|stats}")
        print("  Run `python cli.py knowledge --help` for details")
        sys.exit(1)


def cmd_knowledge_build(args):
    """Build the knowledge dataset from sources."""
    from core.knowledge import DatasetBuilder, build_metrics
    from core.knowledge import KnowledgeReport, KnowledgeCatalog

    sources: list = []
    if args.sources:
        sources.extend(args.sources)
    if args.dir and os.path.isdir(args.dir):
        sources.extend(_discover_sources(args.dir))
    if args.otbm_dir and os.path.isdir(args.otbm_dir):
        sources.extend(_discover_sources(args.otbm_dir))
    if not sources:
        print("  Error: no sources provided (use --sources, --dir, --otbm-dir)")
        sys.exit(1)
    out_path = os.path.abspath(args.output or "output/knowledge_dataset.json")
    base_dir = os.path.dirname(out_path)
    catalog_path = os.path.abspath(args.catalog or os.path.join(base_dir, "knowledge_catalog.json"))
    metrics_path = os.path.abspath(args.metrics or os.path.join(base_dir, "knowledge_metrics.json"))
    report_path = os.path.abspath(args.report or os.path.join(base_dir, "knowledge_report.md"))
    print(f"\n[1/4] Building knowledge dataset from {len(sources)} sources...")
    builder = DatasetBuilder()
    ds = builder.build_from_sources(sources)
    ds.write(out_path)
    print(f"  Dataset: {out_path} ({ds.total()} entries)")
    print(f"  Build stats: {builder.last_stats.to_dict()}")
    print(f"\n[2/4] Building catalog...")
    cat = KnowledgeCatalog.build(ds, top_n=5)
    cat.write(catalog_path)
    print(f"  Catalog: {catalog_path}")
    print(f"\n[3/4] Computing metrics...")
    metrics = build_metrics(ds)
    metrics.write(metrics_path)
    print(f"  Metrics: {metrics_path}")
    print(f"  Coverage: {metrics.coverage_pct:.1f}%")
    print(f"\n[4/4] Generating report...")
    report = KnowledgeReport.build(ds, metrics, cat)
    report.write(report_path)
    print(f"  Report: {report_path}")
    print()


def cmd_knowledge_search(args):
    """Search the knowledge dataset."""
    from core.knowledge import KnowledgeEngine

    engine = _load_or_build_engine(args)
    if engine.dataset.total() == 0:
        print("  Error: no dataset found and no sources discovered")
        sys.exit(1)
    result = engine.query_text(args.query, k=args.k)
    if result.total == 0:
        print(f"  No results for: {args.query!r}")
        return
    print(f"\nSearch: {args.query!r}  ({result.total} matches, {result.took_ms:.2f}ms)")
    for i, m in enumerate(result.matches[: args.k], 1):
        print(f"  {i}. {m.entry.name}  (score={m.score:.4f}, "
              f"type={m.entry.entry_type.value}, biome={m.entry.biome}, "
              f"levels={m.entry.min_level}-{m.entry.max_level})")


def cmd_knowledge_similar(args):
    """Find similar entries by name."""
    from core.knowledge import KnowledgeEngine, EntryType

    engine = _load_or_build_engine(args)
    if engine.dataset.total() == 0:
        print("  Error: no dataset found and no sources discovered")
        sys.exit(1)
    et_map = {
        "hunt": EntryType.HUNT,
        "city": EntryType.CITY,
        "boss_room": EntryType.BOSS_ROOM,
        "boss": EntryType.BOSS_ROOM,
        "region": EntryType.REGION,
        "quest": EntryType.QUEST,
        "raid": EntryType.RAID,
    }
    et = et_map.get(args.type)
    if et is None:
        print(f"  Error: unknown type {args.type!r}")
        sys.exit(1)
    indexer = engine.index.indexer_for(et)
    if indexer is None or len(indexer) == 0:
        print(f"  No {args.type} entries in dataset")
        return
    direct = indexer.get(args.name)
    if direct is not None:
        results = engine._find_similar(et, args.name, k=args.k)  # noqa: SLF001
        print(f"\nSimilar to: {args.name!r} (type={args.type})")
        for i, r in enumerate(results[: args.k], 1):
            mark = " (exact)" if r.get("match_type") == "exact" else ""
            print(f"  {i}. {r['name']}  score={r['score']:.4f}{mark}")
    else:
        res = engine.search.find_by_text(args.name, k=args.k)
        print(f"\nBest matches for: {args.name!r} (type={args.type})")
        for i, m in enumerate(res.matches[: args.k], 1):
            print(f"  {i}. {m.entry.name}  score={m.score:.4f}")


def cmd_knowledge_stats(args):
    """Print dataset stats."""
    from core.knowledge import build_metrics

    engine = _load_or_build_engine(args)
    if engine.dataset.total() == 0:
        print("  Error: no dataset found and no sources discovered")
        sys.exit(1)
    ds = engine.dataset
    print(f"\nKnowledge dataset stats:")
    print(f"  Total entries: {ds.total()}")
    print(f"  Sources: {len(ds.sources)}")
    print("  By type:")
    for k, v in ds.counts().items():
        print(f"    {k:14s} {v}")
    metrics = build_metrics(ds)
    print(f"  Coverage:    {metrics.coverage_pct:.1f}%")
    print(f"  Avg quality: {metrics.avg_quality_score:.1f}")
    print(f"  Avg critic:  {metrics.avg_critic_score:.1f}")
    print(f"  Avg reuse:   {metrics.avg_reuse_score:.1f}")
    print(f"  Level coverage: {metrics.level_coverage}")
    cat = engine.build_catalog(top_n=5)
    print("  Top themes:")
    for t in cat.top_themes:
        print(f"    - {t['name']} ({t['count']})")
    print(f"  Index stats: {engine.index.stats()}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="RME Map AI Agent v2.0 — AI-powered Tibia map generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py generate "Generate Issavi hunt level 300"
  python cli.py generate --type dungeon --theme issavi --level 200 --size 30x30
  python cli.py export --format lua --output output/
  python cli.py import --input map.otbm --output output/imported.otbm
  python cli.py preview --output output/preview.png
  python cli.py validate --input map.otbm
  python cli.py info
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate a world from a prompt")
    gen_parser.add_argument("prompt", nargs="?", default="", help="Natural language prompt")
    gen_parser.add_argument("--type", choices=["hunt", "city", "dungeon"], help="Generator type")
    gen_parser.add_argument("--theme", help="Theme (issavi, roshamuul, etc.)")
    gen_parser.add_argument("--level", type=int, help="Target level")
    gen_parser.add_argument("--size", help="Map size (e.g., 30x30)")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    gen_parser.add_argument("--output", default="output", help="Output directory")

    # export
    exp_parser = subparsers.add_parser("export", help="Export world to Lua or OTBM")
    exp_parser.add_argument("--format", choices=["lua", "otbm"], default="lua", help="Export format")
    exp_parser.add_argument("--type", choices=["hunt", "city", "dungeon"], default="hunt")
    exp_parser.add_argument("--theme", default="issavi")
    exp_parser.add_argument("--seed", type=int, default=42)
    exp_parser.add_argument("--output", default="output", help="Output directory")

    # import
    imp_parser = subparsers.add_parser("import", help="Import an OTBM file")
    imp_parser.add_argument("--input", "-i", required=True, help="Input OTBM file")
    imp_parser.add_argument("--output", "-o", help="Output OTBM file (for re-export)")

    # preview
    prv_parser = subparsers.add_parser("preview", help="Generate preview PNG")
    prv_parser.add_argument("--type", choices=["hunt", "city", "dungeon"], default="hunt")
    prv_parser.add_argument("--theme", default="issavi")
    prv_parser.add_argument("--seed", type=int, default=42)
    prv_parser.add_argument("--output", default="output/preview.png")

    # validate
    val_parser = subparsers.add_parser("validate", help="Validate an OTBM file")
    val_parser.add_argument("--input", "-i", required=True, help="OTBM file to validate")

    # info
    subparsers.add_parser("info", help="Show system information")

    # knowledge subcommands
    kp = subparsers.add_parser("knowledge", help="Knowledge dataset commands")
    kp_subs = kp.add_subparsers(dest="knowledge_command", help="Knowledge subcommand")

    # knowledge build
    kbuild = kp_subs.add_parser("build", help="Build the knowledge dataset from sources")
    kbuild.add_argument("--sources", nargs="*", default=[], help="Source files (json/otbm)")
    kbuild.add_argument("--dir", default=None, help="Directory of source files")
    kbuild.add_argument("--otbm-dir", default=None, help="Directory of OTBM files")
    kbuild.add_argument("--output", "-o", default="output/knowledge_dataset.json")
    kbuild.add_argument("--catalog", default=None, help="Override catalog output path")
    kbuild.add_argument("--metrics", default=None, help="Override metrics output path")
    kbuild.add_argument("--report", default=None, help="Override report output path")

    # knowledge search
    ksearch = kp_subs.add_parser("search", help="Search the knowledge dataset")
    ksearch.add_argument("query", help="Free-text query")
    ksearch.add_argument("--dataset", default="output/knowledge_dataset.json")
    ksearch.add_argument("-k", type=int, default=5)
    ksearch.add_argument("--auto-dir", default="data")

    # knowledge similar
    ksim = kp_subs.add_parser("similar", help="Find similar entries by name")
    ksim.add_argument("type", choices=["hunt", "city", "boss_room", "region", "quest", "raid"])
    ksim.add_argument("name", help="Name of the reference entry")
    ksim.add_argument("--dataset", default="output/knowledge_dataset.json")
    ksim.add_argument("-k", type=int, default=5)
    ksim.add_argument("--auto-dir", default="data")

    # knowledge stats
    kstats = kp_subs.add_parser("stats", help="Print dataset statistics")
    kstats.add_argument("--dataset", default="output/knowledge_dataset.json")
    kstats.add_argument("--auto-dir", default="data")

    # blueprint subcommands
    bp = subparsers.add_parser("blueprint", help="Blueprint Intelligence commands")
    bp_subs = bp.add_subparsers(dest="blueprint_command", help="Blueprint subcommand")

    # blueprint build
    bp_build = bp_subs.add_parser("build", help="Build embeddings for blueprints")
    bp_build.add_argument("--blueprints", nargs="*", default=[], help="Blueprint JSON files")
    bp_build.add_argument("--dir", default=None, help="Directory of blueprints")
    bp_build.add_argument("--output", "-o", default="output/blueprint_embeddings.json")

    # blueprint similar
    bp_sim = bp_subs.add_parser("similar", help="Find similar blueprints")
    bp_sim.add_argument("name", help="Name of the reference blueprint")
    bp_sim.add_argument("--blueprints", nargs="*", default=[], help="Blueprint JSON files")
    bp_sim.add_argument("-k", type=int, default=10)
    bp_sim.add_argument("--output", "-o", default=None)

    # blueprint cluster
    bp_cluster = bp_subs.add_parser("cluster", help="Cluster blueprints by category")
    bp_cluster.add_argument("--blueprints", nargs="*", default=[], help="Blueprint JSON files")
    bp_cluster.add_argument("--output", "-o", default="output/blueprint_clusters.json")

    # blueprint evolve
    bp_evolve = bp_subs.add_parser("evolve", help="Evolve a blueprint")
    bp_evolve.add_argument("name", help="Name of blueprint to evolve")
    bp_evolve.add_argument("--target", type=float, default=90.0, help="Target critic score")
    bp_evolve.add_argument("--generations", type=int, default=10, help="Max generations")
    bp_evolve.add_argument("--output", "-o", default=None)

    # blueprint fuse
    bp_fuse = bp_subs.add_parser("fuse", help="Fuse two blueprints")
    bp_fuse.add_argument("name_a", help="First blueprint name")
    bp_fuse.add_argument("name_b", help="Second blueprint name")
    bp_fuse.add_argument("--ratio", type=float, default=0.5, help="Fusion ratio")
    bp_fuse.add_argument("--method", choices=["weighted", "interleave", "blend"], default="weighted")
    bp_fuse.add_argument("--output", "-o", default=None)

    # blueprint recommend
    bp_rec = bp_subs.add_parser("recommend", help="Get blueprint recommendations")
    bp_rec.add_argument("--type", default="", help="Recommendation type (hunt, city, boss)")
    bp_rec.add_argument("--blueprints", nargs="*", default=[], help="Blueprint JSON files")
    bp_rec.add_argument("-k", type=int, default=5)
    bp_rec.add_argument("--output", "-o", default=None)

    # blueprint rank
    bp_rank = bp_subs.add_parser("rank", help="Rank blueprints")
    bp_rank.add_argument("--blueprints", nargs="*", default=[], help="Blueprint JSON files")
    bp_rank.add_argument("--top", type=int, default=10, help="Number of top results")
    bp_rank.add_argument("--output", "-o", default=None)

    # blueprint generate
    bp_gen = bp_subs.add_parser("generate", help="Generate a blueprint from prompt")
    bp_gen.add_argument("prompt", help="Natural language prompt")
    bp_gen.add_argument("--blueprints", nargs="*", default=[], help="Reference blueprint files")
    bp_gen.add_argument("--output", "-o", default=None)

    # autonomous subcommands
    auto = subparsers.add_parser("autonomous", help="Autonomous World Designer commands")
    auto_subs = auto.add_subparsers(dest="autonomous_command", help="Autonomous subcommand")

    # autonomous generate
    auto_gen = auto_subs.add_parser("generate", help="Generate a world autonomously")
    auto_gen.add_argument("prompt", help="Natural language prompt")
    auto_gen.add_argument("--max-iterations", type=int, default=20, help="Max optimization iterations")
    auto_gen.add_argument("--output", "-o", default=None, help="Output directory")

    # autonomous optimize
    auto_opt = auto_subs.add_parser("optimize", help="Optimize a world design")
    auto_opt.add_argument("prompt", help="Natural language prompt")
    auto_opt.add_argument("--max-iterations", type=int, default=20, help="Max optimization iterations")
    auto_opt.add_argument("--output", "-o", default=None, help="Output directory")

    # autonomous benchmark
    auto_bench = auto_subs.add_parser("benchmark", help="Run benchmark with multiple worlds")
    auto_bench.add_argument("--count", type=int, default=50, help="Number of worlds to generate")
    auto_bench.add_argument("--output", "-o", default=None, help="Output directory")

    # autonomous report
    auto_subs.add_parser("report", help="Get report of all generations")

    args = parser.parse_args()

    if not args.command:
        _banner()
        parser.print_help()
        sys.exit(0)

    _banner()

    commands = {
        "generate": cmd_generate,
        "export": cmd_export,
        "import": cmd_import,
        "preview": cmd_preview,
        "validate": cmd_validate,
        "info": cmd_info,
        "knowledge": cmd_knowledge,
        "blueprint": cmd_blueprint,
        "autonomous": cmd_autonomous,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()
        sys.exit(1)


# ── blueprint ────────────────────────────────────────────────────────────────

def cmd_blueprint(args):
    """Dispatch `rme blueprint ...` sub-commands."""
    sub = getattr(args, "blueprint_command", None)
    if sub == "build":
        cmd_blueprint_build(args)
    elif sub == "similar":
        cmd_blueprint_similar(args)
    elif sub == "cluster":
        cmd_blueprint_cluster(args)
    elif sub == "evolve":
        cmd_blueprint_evolve(args)
    elif sub == "fuse":
        cmd_blueprint_fuse(args)
    elif sub == "recommend":
        cmd_blueprint_recommend(args)
    elif sub == "rank":
        cmd_blueprint_rank(args)
    elif sub == "generate":
        cmd_blueprint_gen(args)
    else:
        print("  Usage: rme blueprint {build|similar|cluster|evolve|fuse|recommend|rank|generate}")
        print("  Run `python cli.py blueprint --help` for details")
        sys.exit(1)


def _load_blueprint_files(paths):
    """Load blueprint files."""
    from core.blueprints.blueprint import Blueprint
    bps = []
    for p in paths:
        if os.path.exists(p):
            with open(p, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    bps.append(Blueprint.from_dict(item))
            else:
                bps.append(Blueprint.from_dict(data))
    return bps


def cmd_blueprint_build(args):
    """Build embeddings for blueprints."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    engine = BlueprintIntelligenceEngine()
    bps = _load_blueprint_files(args.blueprints or [])
    if not bps:
        print("  No blueprints loaded. Use --blueprints to specify blueprint files.")
        sys.exit(1)
    engine.load_blueprints(bps)
    embs = engine.build_embeddings()
    engine.export_embeddings(args.output)
    print(f"  Built {len(embs)} embeddings -> {args.output}")


def cmd_blueprint_similar(args):
    """Find similar blueprints."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    engine = BlueprintIntelligenceEngine()
    bps = _load_blueprint_files(args.blueprints or [])
    if not bps:
        print("  No blueprints loaded.")
        sys.exit(1)
    engine.load_blueprints(bps)
    engine.build_embeddings()
    target = engine.get_blueprint(args.name)
    if not target:
        print(f"  Blueprint '{args.name}' not found.")
        sys.exit(1)
    results = engine.find_similar(target, top_k=args.k)
    print(f"\nSimilar blueprints to '{args.name}':")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r.target_blueprint} (hybrid={r.hybrid_score:.4f})")


def cmd_blueprint_cluster(args):
    """Cluster blueprints by category."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    engine = BlueprintIntelligenceEngine()
    bps = _load_blueprint_files(args.blueprints or [])
    if not bps:
        print("  No blueprints loaded.")
        sys.exit(1)
    engine.load_blueprints(bps)
    engine.build_embeddings()
    clusters = engine.cluster()
    engine.export_clusters(args.output)
    print(f"\nFound {len(clusters)} clusters:")
    for c in clusters:
        print(f"  {c.name}: {c.size} members, {c.dominant_category}")


def cmd_blueprint_evolve(args):
    """Evolve a blueprint."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    engine = BlueprintIntelligenceEngine()
    bp = Blueprint(name=args.name)
    result = engine.evolve(bp, target_critic_score=args.target, max_generations=args.generations)
    print(f"  Evolved {args.name}: gen {result.generation}, critic={result.critic_score:.1f}")


def cmd_blueprint_fuse(args):
    """Fuse two blueprints."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    from core.blueprints.blueprint import Blueprint
    engine = BlueprintIntelligenceEngine()
    bp_a = Blueprint(name=args.name_a)
    bp_b = Blueprint(name=args.name_b)
    result = engine.fuse(bp_a, bp_b, ratio=args.ratio, method=args.method)
    print(f"  Fused '{args.name_a}' + '{args.name_b}' -> {result.name}")


def cmd_blueprint_recommend(args):
    """Get blueprint recommendations."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    engine = BlueprintIntelligenceEngine()
    bps = _load_blueprint_files(args.blueprints or [])
    engine.load_blueprints(bps)
    if args.type:
        recs = engine.recommend(args.type, top_k=args.k)
    else:
        recs = engine.recommend_patterns(top_k=args.k)
    print(f"\nRecommendations ({len(recs)}):")
    for r in recs:
        print(f"  - {r.get('recommendation', '')} (conf={r.get('confidence', 0):.2f})")


def cmd_blueprint_rank(args):
    """Rank blueprints."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    engine = BlueprintIntelligenceEngine()
    bps = _load_blueprint_files(args.blueprints or [])
    if not bps:
        print("  No blueprints loaded.")
        sys.exit(1)
    engine.load_blueprints(bps)
    ranked = engine.rank_all(top_k=args.top)
    print(f"\nTop {len(ranked)} blueprints:")
    for i, r in enumerate(ranked, 1):
        print(f"  {i}. {r.blueprint_name:20s} rank={r.overall_rank:6.2f} critic={r.critic_score:5.1f}")


def cmd_blueprint_gen(args):
    """Generate a blueprint from a prompt."""
    from core.blueprint_intelligence import BlueprintIntelligenceEngine
    engine = BlueprintIntelligenceEngine()
    bps = _load_blueprint_files(args.blueprints or [])
    engine.load_blueprints(bps)
    bp = engine.generate(args.prompt)
    print(f"  Generated '{bp.name}' (category={bp.category}, theme={bp.theme})")
    if args.output:
        with open(args.output, "w") as f:
            json.dump(bp.to_dict(), f, indent=2)
        print(f"  Written to {args.output}")


# ── autonomous ────────────────────────────────────────────────────────────────

def cmd_autonomous(args):
    """Dispatch `rme autonomous ...` sub-commands."""
    sub = getattr(args, "autonomous_command", None)
    if sub == "generate":
        cmd_autonomous_generate(args)
    elif sub == "optimize":
        cmd_autonomous_optimize(args)
    elif sub == "benchmark":
        cmd_autonomous_benchmark(args)
    elif sub == "report":
        cmd_autonomous_report(args)
    else:
        print("  Usage: rme autonomous {generate|optimize|benchmark|report}")
        print("  Run `python cli.py autonomous --help` for details")
        sys.exit(1)


def cmd_autonomous_generate(args):
    """Generate a world autonomously from a prompt."""
    from core.autonomous import AutonomousWorldDesigner
    
    print(f"\n[1/3] Initializing Autonomous World Designer...")
    designer = AutonomousWorldDesigner()
    
    print(f"[2/3] Generating world from prompt: {args.prompt}")
    result = designer.generate(args.prompt, max_iterations=args.max_iterations)
    
    print(f"[3/3] Generation complete!")
    print(f"  Result ID: {result.result_id}")
    print(f"  Success: {result.success}")
    print(f"  Final Critic Score: {result.final_scores.get('critic', 0):.2f}")
    print(f"  Total Iterations: {len(result.iterations)}")
    print(f"  Duration: {result.total_duration_seconds:.2f}s")
    
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        result_path = os.path.join(args.output, "autonomous_result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        print(f"  Result exported to: {result_path}")


def cmd_autonomous_optimize(args):
    """Optimize an existing world design."""
    from core.autonomous import AutonomousWorldDesigner
    
    print(f"\n[1/3] Initializing Autonomous Optimizer...")
    designer = AutonomousWorldDesigner()
    
    print(f"[2/3] Optimizing world from prompt: {args.prompt}")
    result = designer.optimize(args.prompt, max_iterations=args.max_iterations)
    
    print(f"[3/3] Optimization complete!")
    print(f"  Result ID: {result.result_id}")
    print(f"  Success: {result.success}")
    print(f"  Final Critic Score: {result.final_scores.get('critic', 0):.2f}")
    print(f"  Total Iterations: {len(result.iterations)}")
    
    # Show convergence
    if len(result.convergence_data) > 1:
        improvement = result.convergence_data[-1] - result.convergence_data[0]
        print(f"  Score Improvement: {improvement:.2f}")
    
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        result_path = os.path.join(args.output, "autonomous_optimization.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        print(f"  Result exported to: {result_path}")


def cmd_autonomous_benchmark(args):
    """Run benchmark by generating multiple worlds."""
    from core.autonomous import AutonomousWorldDesigner
    
    print(f"\n[1/3] Initializing Benchmark...")
    designer = AutonomousWorldDesigner()
    
    print(f"[2/3] Running benchmark with {args.count} worlds...")
    report = designer.benchmark(num_worlds=args.count)
    
    print(f"[3/3] Benchmark complete!")
    print(f"  Total Worlds: {report['total_worlds']}")
    print(f"  Successful: {report['successful_worlds']}")
    print(f"  Success Rate: {report['success_rate']:.1%}")
    print(f"  Average Score: {report['average_score']:.2f}")
    print(f"  Max Score: {report['max_score']:.2f}")
    print(f"  Min Score: {report['min_score']:.2f}")
    print(f"  Total Duration: {report['total_duration_seconds']:.2f}s")
    
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        report_path = os.path.join(args.output, "benchmark_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  Report exported to: {report_path}")


def cmd_autonomous_report(args):
    """Get a report of all autonomous generations."""
    from core.autonomous import AutonomousWorldDesigner
    
    designer = AutonomousWorldDesigner()
    report = designer.report()
    
    print(f"\nAutonomous World Designer Report:")
    print(f"  Total Generations: {report['total_generations']}")
    print(f"  Decision Stats: {report['decision_stats']}")
    print(f"  Optimization Stats: {report['optimization_stats']}")
    
    if report['history']:
        print(f"\n  Recent Generations:")
        for i, gen in enumerate(report['history'][-5:], 1):
            print(f"    {i}. {gen['prompt'][:50]}... (success={gen['success']}, score={gen['final_scores'].get('critic', 0):.2f})")


if __name__ == "__main__":
    main()
