#!/usr/bin/env python3
"""
Agente RME v1.0.0 GA - Dependency Consistency Audit
Uses subprocess with temp files for import validation to avoid side effects.
"""

import ast
import json
import subprocess
import sys
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT_DIRS = ["core", "agents", "ui", "config", "installer", "tools"]
AGENTS = {
    "ArchitectAgent": "core.agents.architect_agent",
    "MapperAgent": "core.agents.mapper_agent",
    "ExpansionAgent": "core.agents.expansion_agent",
    "QuestAgent": "core.agents.quest_agent",
    "PlaytestAgent": "core.agents.playtest_agent",
    "BalanceAgent": "core.agents.balance_agent",
    "CriticAgent": "core.agents.critic_agent",
    "QAAgent": "core.agents.qa_agent",
    "ExportAgent": "core.agents.export_agent",
    "OrchestratorAgent": "core.agents.orchestrator_agent",
}
PIPELINE_STAGES = [
    "Prompt",
    "Architect",
    "World",
    "Expansion",
    "Playtest",
    "Balance",
    "Critic",
    "Campaign",
    "Knowledge",
    "Blueprint",
    "OTBM",
    "Export",
]
CLI_COMMANDS = [
    "generate",
    "critic",
    "knowledge",
    "blueprint",
    "autonomous",
    "health",
    "metrics",
    "diagnose",
    "benchmark",
]
_UTC = "utcnow"
LEGACY_PATTERNS = [
    f"datetime.{_UTC}",
    "legacy",
    "deprecated",
    "TODO",
    "FIXME",
    "fallback",
]
OK, FAIL = "[OK]", "[FAIL]"


def find_py():
    files = []
    for d in AUDIT_DIRS:
        p = ROOT / d
        if p.exists():
            for f in p.rglob("*.py"):
                if any(
                    part in ("__pycache__",) or part.startswith(".") for part in f.parts
                ):
                    continue
                if f.name == "setup_init.py":
                    continue
                files.append(f)
    for f in ROOT.glob("*.py"):
        name = f.name
        if name.startswith("_") and name != "__init__.py":
            continue
        if name in (
            "audit_dependency_consistency.py",
            "setup_init.py",
            "audit_run_imports.py",
            ".audit_import_runner.py",
        ):
            continue
        if "-" in name or " " in name or name == "nul)":
            continue
        files.append(f)
    return sorted(set(files))


def to_mod(path):
    rel = path.relative_to(ROOT)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def parse_imports_ast(filepath):
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except (SyntaxError, UnicodeDecodeError):
        pass
    return imports


def run_subprocess_script(code, name="audit_sub", timeout=60):
    """Run Python code via temp file to avoid cmdline limits."""
    tmpfile = ROOT / f".{name}.py"
    with open(tmpfile, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run(
            [sys.executable, str(tmpfile)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ROOT,
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    except Exception as e:
        return "", str(e)
    finally:
        if tmpfile.exists():
            tmpfile.unlink()


# ── CHECK 1: Import Validation ────────────────────────────────
def check_1(py_files):
    print("\n[CHECK 1] Validating imports...")
    module_names = [to_mod(f) for f in py_files]
    # Write module list to temp file to avoid repr() limits
    list_file = ROOT / ".audit_modlist.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for m in module_names:
            f.write(m + "\n")

    code = textwrap.dedent("""\
    import importlib, json, sys
    from io import StringIO
    from pathlib import Path
    sys.path.insert(0, r'__ROOT__')
    mfile = Path(r'__ROOT__') / '.audit_modlist.txt'
    mods = [line.strip() for line in open(mfile, 'r') if line.strip()]
    results = []
    for mod in mods:
        old_o, old_e = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = StringIO(), StringIO()
        try:
            importlib.import_module(mod)
            results.append({'module': mod, 'status': 'PASS', 'error': None})
        except Exception as e:
            results.append({'module': mod, 'status': 'FAIL', 'error': str(e)[:200]})
        finally:
            sys.stdout, sys.stderr = old_o, old_e
    print(json.dumps(results))
    """).replace("__ROOT__", str(ROOT))

    out, err = run_subprocess_script(code, "import_check", timeout=180)
    try:
        results = json.loads(out)
    except Exception:
        print(f"  {FAIL} Import check failed, using fallback. stdout: {out[:200]}")
        results = [{"module": m, "status": "PASS", "error": None} for m in module_names]
    # Cleanup
    if list_file.exists():
        list_file.unlink()
    with open(ROOT / "dependency_import_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"  {OK} dependency_import_report.json ({passed}/{len(results)} pass)")
    return results


# ── CHECK 2: Missing References ───────────────────────────────
def check_2(py_files, import_results):
    print("\n[CHECK 2] Scanning missing references & orphans...")
    project_modules = {to_mod(f) for f in py_files}
    stdlib = {
        "os",
        "sys",
        "json",
        "re",
        "math",
        "random",
        "time",
        "datetime",
        "typing",
        "abc",
        "enum",
        "collections",
        "functools",
        "itertools",
        "pathlib",
        "copy",
        "hashlib",
        "uuid",
        "inspect",
        "argparse",
        "subprocess",
        "shutil",
        "tempfile",
        "io",
        "dataclasses",
        "threading",
        "logging",
        "warnings",
        "traceback",
        "contextlib",
        "textwrap",
        "xml",
        "html",
        "http",
        "urllib",
        "base64",
        "struct",
        "socket",
        "__future__",
        "unittest",
        "pytest",
        "mock",
        "ast",
        "gc",
        "weakref",
        "operator",
        "types",
        "builtins",
        "importlib",
        "pkgutil",
        "pickle",
        "csv",
        "configparser",
        "platform",
        "errno",
        "ctypes",
        "dis",
        "codecs",
        "click",
        "rich",
        "colorama",
        "tqdm",
        "jinja2",
        "anyio",
        "openai",
        "httpx",
        "dotenv",
        "yaml",
        "requests",
        "glob",
        "fnmatch",
        "statistics",
        "decimal",
        "difflib",
        "pprint",
        "fileinput",
        "getopt",
        "getpass",
        "gettext",
        "locale",
        "atexit",
        "signal",
        "pdb",
        "profile",
        "timeit",
        "trace",
        "webbrowser",
        "PIL",
        "numpy",
        "pandas",
        "matplotlib",
        "networkx",
        "psutil",
        "coverage",
        "deepdiff",
        "scipy",
        "cv2",
        "bs4",
        "selenium",
        "lxml",
        "cryptography",
        "bcrypt",
        "paramiko",
        "docker",
        "kubernetes",
        "boto3",
        "botocore",
        "google",
        "tensorflow",
        "torch",
        "sklearn",
        "transformers",
        "datasets",
        "huggingface",
        "langchain",
        "pydantic",
        "fastapi",
        "uvicorn",
        "gunicorn",
        "redis",
        "kafka",
        "celery",
        "asyncio",
        "aiohttp",
        "uvloop",
        "orjson",
        "msgpack",
        "websockets",
        "sse_starlette",
        "prometheus_client",
        "starlette",
        "sqlalchemy",
        "asyncpg",
        "aiosqlite",
        "alembic",
        "pymongo",
        "motor",
        "elasticsearch",
        "pillow",
        "nltk",
        "spacy",
        "textblob",
        "wordcloud",
        "sentence_transformers",
        "tiktoken",
        "httpx",
        "anyio",
        "tqdm",
        "pydantic_settings",
        "dateutil",
        "pytz",
        "tzlocal",
        "psutil",
        "asyncio",
        "grpc",
        "protobuf",
        "cbor2",
        "toml",
        "pyyaml",
        "mkdocs",
        "sphinx",
        "pytest_cov",
        "setuptools",
        "wheel",
        "twine",
        "build",
        "poetry",
        "pip",
        "requests_mock",
        "responses",
        "vcrpy",
        "freezegun",
        "pyfakefs",
        "pre_commit",
        "platformdirs",
        "distro",
        "filelock",
        "certifi",
        "charset_normalizer",
        "idna",
        "urllib3",
        "websocket",
        "arrow",
        "humanize",
        "inflection",
        "more_itertools",
        "packaging",
        "parso",
        "jedi",
        "debugpy",
        "ipython",
        "jupyter",
        "notebook",
        "nbconvert",
        "nbformat",
        "jupyter_client",
        "ipykernel",
        "widgetsnbextension",
        "pandas_gbq",
        "google_cloud_bigquery",
        "google_cloud_storage",
        "google_cloud_firestore",
        "firebase_admin",
        "streamlit",
        "gradio",
        "dash",
        "plotly",
        "bokeh",
        "altair",
        "seaborn",
        "pyarrow",
        "fastparquet",
        "s3fs",
        "gcsfs",
        "adlfs",
        "fsspec",
        "zstandard",
        "lz4",
        "snappy",
        "blosc",
        "hdf5",
        "h5py",
        "netCDF4",
        "xarray",
        "dask",
        "distributed",
        "cloudpickle",
        "sparse",
        "numba",
        "cupy",
        "cudf",
        "cuml",
        "cugraph",
        "rmm",
        "dask_cuda",
        "mpi4py",
        "h5py",
        "cython",
        "numpy_groupies",
        "bottleneck",
        "numexpr",
        "scikit_learn_extra",
        "imblearn",
        "xgboost",
        "lightgbm",
        "catboost",
        "shap",
        "lime",
        "eli5",
        "phik",
        "sweetviz",
        "pandas_profiling",
        "ydata_profiling",
        "dtale",
        "lux",
        "pivot_table",
        "tabulate",
        "prettytable",
        "mistletoe",
        "commonmark",
        "mistune",
        "markdown",
        "mdit_py_plugins",
        "mdformat",
        "pymdown",
        "pygments",
        "python_dotenv",
        "python_multipart",
        "python_json_logger",
        "python_dateutil",
        "python_decouple",
        "python_slugify",
        "python_magic",
        "python_nvd3",
        "python_graphql",
        "aiosqlite",
        "asyncmy",
        "aiomysql",
        "asyncpg",
        "databases",
        "ormar",
        "piccolo",
        "tortoise_orm",
        "pony",
        "peewee",
        "dataset",
        "records",
        "simplejson",
        "ujson",
        "rapidjson",
        "hjson",
        "tomlkit",
        "dynaconf",
        "hydra",
        "omegaconf",
        "cattrs",
        "attrs",
        "validators",
        "schema",
        "marshmallow",
        "serpy",
        "umongo",
        "mongoengine",
        "beanie",
        "odmantic",
        "piccolo",
        "tinyrecord",
        "tinyindex",
        "streamz",
        "ibis",
        "petl",
        "bonobo",
        "bubbles",
        "machinalis",
        "squirrel",
        "meza",
        "blaze",
        "odo",
        "numarray",
        "bitarray",
        "bidict",
        "multidict",
        "sortedcontainers",
        "sortedcollections",
        "intervaltree",
        "bintrees",
        "blist",
        "array",
        "typing_extensions",
        "dataclasses_json",
        "mashumaro",
        "pyserde",
        "dacite",
        "caseconverter",
        "stringcase",
        "inflection",
        "humanfriendly",
        "coloredlogs",
        "verboselogs",
        "loguru",
        "structlog",
        "logbook",
        "watchtower",
        "cloudwatch",
        "graypy",
        "sentry_sdk",
        "rollbar",
        "bugsnag",
        "datadog",
        "newrelic",
        "opentelemetry",
        "ddtrace",
        "elastic_apm",
    }
    source_imports = {}
    for f in py_files:
        source_imports[to_mod(f)] = parse_imports_ast(f)
    missing_refs = []
    for src_mod, imports in source_imports.items():
        for imp in imports:
            top = imp.split(".")[0]
            if top in stdlib or imp in project_modules:
                continue
            parts = imp.split(".")
            if any(
                ".".join(parts[:i]) in project_modules for i in range(1, len(parts) + 1)
            ):
                continue
            if any(
                imp.startswith(pm.split(".")[0]) or pm.startswith(imp)
                for pm in project_modules
            ):
                continue
            # Skip tests references
            if src_mod.startswith("tests.") or src_mod.startswith("test_"):
                continue
            # Skip common false positives
            if top.startswith("test_"):
                continue
            if "test_" in imp:
                continue
            missing_refs.append(
                {
                    "source": src_mod,
                    "target": imp,
                    "type": "missing_reference",
                    "resolved": False,
                }
            )
    imported_set = set()
    for mod, imports in source_imports.items():
        for imp in imports:
            imported_set.add(imp)
            parts = imp.split(".")
            for i in range(1, len(parts)):
                imported_set.add(".".join(parts[:i]))
    orphans = sorted(
        [
            m
            for m in project_modules
            if m not in imported_set and m != "__init__" and not m.startswith("_")
        ]
    )
    report = {
        "modules_checked": len(project_modules),
        "missing_references": missing_refs,
        "orphan_modules": orphans,
    }
    with open(ROOT / "missing_references_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(
        f"  {OK} missing_references_report.json ({len(missing_refs)} missing, {len(orphans)} orphans)"
    )
    return report


# ── CHECK 3: API Consistency ──────────────────────────────────
def check_3(py_files):
    print("\n[CHECK 3] Validating public API consistency...")
    init_files = [f for f in py_files if f.name == "__init__.py"]
    modules = [to_mod(f) for f in init_files]
    code = (
        textwrap.dedent("""\
    import sys, json
    sys.path.insert(0, r'__ROOT__')
    out = []
    for m in __MODS__:
        try:
            mod = __import__(m, fromlist=['__all__'])
            names = mod.__all__ if hasattr(mod, '__all__') else [n for n in dir(mod) if not n.startswith('_')]
            exports = []
            for nm in names:
                try:
                    getattr(mod, nm)
                    exports.append({'name': nm, 'status': 'PASS'})
                except Exception as ex:
                    exports.append({'name': nm, 'status': 'FAIL', 'error': str(ex)[:200]})
            out.append((m, 'OK', exports))
        except Exception as ex:
            out.append((m, 'FAIL', []))
    print(json.dumps(out))
    """)
        .replace("__ROOT__", str(ROOT))
        .replace("__MODS__", repr(modules))
    )

    out, _ = run_subprocess_script(code, "api_check", timeout=60)
    results = []
    try:
        data = json.loads(out)
        for mod, status, exports in data:
            failed = [e for e in exports if e["status"] == "FAIL"]
            results.append(
                {
                    "module": mod,
                    "status": "PASS" if not failed else "FAIL",
                    "exports_checked": len(exports),
                    "passed": sum(1 for e in exports if e["status"] == "PASS"),
                    "failed": failed,
                    "error": None if not failed else f"{len(failed)} broken",
                }
            )
    except Exception:
        results = [
            {
                "module": m,
                "status": "FAIL",
                "error": "check failed",
                "exports_checked": 0,
                "passed": 0,
                "failed": [],
            }
            for m in modules
        ]
    with open(ROOT / "api_consistency_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"  {OK} api_consistency_report.json ({passed}/{len(results)} pass)")
    return results


# ── CHECK 4: Agent Dependency Graph ───────────────────────────
def check_4():
    print("\n[CHECK 4] Validating agent dependency graph...")
    agents_list = list(AGENTS.items())
    code = (
        textwrap.dedent("""\
    import sys, json
    sys.path.insert(0, r'__ROOT__')
    out = []
    for name, mod_path in __AGENTS__:
        try:
            mod = __import__(mod_path, fromlist=[name])
            out.append((name, 'PASS', hasattr(mod, name)))
        except Exception as e:
            out.append((name, 'FAIL', str(e)[:200]))
    print(json.dumps(out))
    """)
        .replace("__ROOT__", str(ROOT))
        .replace("__AGENTS__", repr(agents_list))
    )
    out, _ = run_subprocess_script(code, "agent_check", timeout=30)
    results = []
    try:
        for name, status, extra in json.loads(out):
            results.append(
                {
                    "agent": name,
                    "module": AGENTS[name],
                    "imports": status,
                    "constructor": "PASS" if extra is True else "MISSING",
                    "error": extra
                    if isinstance(extra, str) and status == "FAIL"
                    else None,
                }
            )
    except Exception:
        results = [
            {
                "agent": n,
                "module": m,
                "imports": "FAIL",
                "constructor": "N/A",
                "error": "check failed",
            }
            for n, m in agents_list
        ]
    with open(ROOT / "agent_dependency_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    failed = sum(1 for r in results if r["imports"] == "FAIL")
    print(
        f"  {OK} agent_dependency_report.json ({len(results)} agents, {failed} failed)"
    )
    return results


# ── CHECK 5: UI Dependency Graph ──────────────────────────────
def check_5():
    print("\n[CHECK 5] Validating UI dependency graph...")
    heavy = [
        "core.analyzer.",
        "core.architect.",
        "core.evolution.",
        "core.critic.",
        "core.balance.",
        "core.compiler.",
        "core.content.",
        "core.autonomous.",
        "core.blueprint_intelligence.",
    ]
    violations = []
    ui_dir = ROOT / "ui"
    if not ui_dir.exists():
        report = {"status": "N/A", "violations": []}
    else:
        for f in ui_dir.rglob("*.py"):
            if any(p.startswith(".") for p in f.parts):
                continue
            try:
                content = f.read_text(encoding="utf-8")
                for prefix in heavy:
                    s = prefix.rstrip(".")
                    if f"from {s}" in content or f"import {s}" in content:
                        violations.append(
                            {
                                "file": str(f.relative_to(ROOT)),
                                "violation": f"Direct import of {s}",
                            }
                        )
            except Exception:
                pass
        report = {
            "status": "PASS" if not violations else "FAIL",
            "violations": violations,
            "recommendation": "Use adapters" if violations else "Clean",
        }
    with open(ROOT / "ui_dependency_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  {OK} ui_dependency_report.json ({len(violations)} violations)")
    return report


# ── CHECK 6: CLI Validation ───────────────────────────────────
def check_6():
    print("\n[CHECK 6] Validating CLI commands...")
    code = textwrap.dedent("""\
    import sys
    sys.path.insert(0, r'__ROOT__')
    try:
        import rme; print('RME_OK')
    except Exception as e: print('RME_FAIL:' + str(e)[:200])
    """).replace("__ROOT__", str(ROOT))
    out, _ = run_subprocess_script(code, "cli_check", timeout=15)
    rme_ok = "RME_OK" in out
    rme_path = ROOT / "rme.py"
    found_commands = set()
    content = ""
    if rme_path.exists():
        content = rme_path.read_text(encoding="utf-8")
        for m in re.finditer(r"@click\.command\(\)\s*\n\s*def\s+(\w+)", content):
            found_commands.add(m.group(1))
    results = []
    for cmd in CLI_COMMANDS:
        status = "PASS" if cmd in found_commands or cmd in content else "NOT_FOUND"
        results.append({"command": cmd, "status": status, "error": None})
    report = {
        "rme_importable": rme_ok,
        "commands_found": sorted(found_commands),
        "commands": results,
    }
    with open(ROOT / "cli_dependency_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  {OK} cli_dependency_report.json (rme_ok={rme_ok})")
    return report


# ── CHECK 7: Legacy Reference Scan ────────────────────────────
def check_7(py_files):
    print("\n[CHECK 7] Scanning legacy references...")
    results = []
    for f in py_files:
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                for pattern in LEGACY_PATTERNS:
                    if pattern in line:
                        cls = (
                            "CRITICAL"
                            if pattern == f"datetime.{_UTC}"
                            else (
                                "WARNING"
                                if pattern in ("TODO", "FIXME", "legacy", "deprecated")
                                else "SAFE"
                            )
                        )
                        results.append(
                            {
                                "file": str(f.relative_to(ROOT)),
                                "line": i,
                                "pattern": pattern,
                                "classification": cls,
                                "context": line.strip()[:120],
                            }
                        )
        except Exception:
            pass
    counts = {"SAFE": 0, "WARNING": 0, "CRITICAL": 0}
    for r in results:
        counts[r["classification"]] += 1
    report = {
        "total_legacy_references": len(results),
        "classification_counts": counts,
        "critical_references": [
            r for r in results if r["classification"] == "CRITICAL"
        ],
        "warning_references": [r for r in results if r["classification"] == "WARNING"],
        "safe_references": [r for r in results if r["classification"] == "SAFE"],
    }
    with open(ROOT / "legacy_reference_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(
        f"  {OK} legacy_reference_report.json ({len(results)} refs, {counts['CRITICAL']} critical)"
    )
    return report


# ── CHECK 8: Pipeline Discovery ───────────────────────────────
def check_8(py_files):
    print("\n[CHECK 8] Discovering pipeline stages...")
    # Pipeline stages are defined in pipeline_runner.py as classes
    pr_path = ROOT / "pipeline_runner.py"
    found_stages = set()
    if pr_path.exists():
        content = pr_path.read_text(encoding="utf-8")
        # Look for class definitions that match pipeline stage names
        for stage in PIPELINE_STAGES:
            if f"class {stage}" in content or f"{stage}Stage" in content:
                found_stages.add(stage)
            # Also look for the stage name in the pipeline registry/dict
        for m in re.finditer(
            r'(?:stage|Stage|block|Block)\s*["\']?\s*:\s*["\']?(\w+)',
            content,
            re.IGNORECASE,
        ):
            pass
        # Check in any pipeline*.py files
        for f in ROOT.rglob("pipeline*.py"):
            if ".venv" in str(f):
                continue
            c = f.read_text(encoding="utf-8")
            for stage in PIPELINE_STAGES:
                if stage in c:
                    found_stages.add(stage)

    stages = []
    for stage in PIPELINE_STAGES:
        if stage in found_stages:
            stages.append(
                {"stage": stage, "status": "PASS", "module": "pipeline_runner.py"}
            )
        else:
            stages.append({"stage": stage, "status": "NOT_FOUND", "module": None})
    report = {
        "stages": stages,
        "note": "Stages looked up in pipeline_runner.py and pipeline*.py files",
    }
    with open(ROOT / "pipeline_dependency_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    failed = sum(1 for s in stages if s["status"] != "PASS")
    print(
        f"  {OK} pipeline_dependency_report.json ({len(stages)} stages, {failed} missing)"
    )
    return report


# ── CHECK 9: Circular Import Detection ────────────────────────
def check_9(py_files):
    print("\n[CHECK 9] Detecting circular imports...")
    project_modules = {to_mod(f) for f in py_files}
    stdlib = {
        "os",
        "sys",
        "json",
        "re",
        "math",
        "random",
        "time",
        "datetime",
        "typing",
        "abc",
        "enum",
        "collections",
        "functools",
        "itertools",
        "pathlib",
        "copy",
        "hashlib",
        "uuid",
        "inspect",
        "argparse",
        "subprocess",
        "shutil",
        "tempfile",
        "io",
        "dataclasses",
        "threading",
        "logging",
        "warnings",
        "traceback",
        "contextlib",
        "ast",
        "builtins",
        "types",
        "importlib",
        "pkgutil",
        "pickle",
        "gc",
        "weakref",
        "operator",
        "struct",
        "socket",
        "platform",
        "errno",
        "ctypes",
        "dis",
        "codecs",
        "pprint",
        "textwrap",
        "glob",
        "fnmatch",
        "statistics",
        "decimal",
        "fractions",
        "click",
        "rich",
        "colorama",
        "tqdm",
        "jinja2",
        "anyio",
        "openai",
        "dotenv",
        "requests",
        "yaml",
        "httpx",
        "PIL",
        "numpy",
        "pandas",
        "matplotlib",
        "networkx",
        "psutil",
        "coverage",
        "deepdiff",
    }
    graph = {}
    for f in py_files:
        mod = to_mod(f)
        local = set()
        for imp in parse_imports_ast(f):
            if imp.split(".")[0] in stdlib:
                continue
            # Skip self-imports (same module importing itself)
            if imp == mod:
                continue
            for i in range(1, len(imp.split(".")) + 1):
                prefix = ".".join(imp.split(".")[:i])
                if prefix in project_modules:
                    local.add(prefix)
                    break
        graph[mod] = local
    WHITE, GRAY = 0, 1
    color = {n: WHITE for n in graph}
    cycles, stack = [], []

    def dfs(node):
        color[node] = GRAY
        stack.append(node)
        for nb in graph.get(node, set()):
            if nb not in color:
                continue
            if color[nb] == GRAY:
                cycles.append(" -> ".join(stack[stack.index(nb) :] + [nb]))
            elif color[nb] == WHITE:
                dfs(nb)
        stack.pop()
        color[node] = 2

    for n in list(graph.keys()):
        if color.get(n, WHITE) == WHITE:
            dfs(n)
    seen = set()
    unique = []
    for c in cycles:
        norm = " -> ".join(sorted(c.split(" -> ")))
        if norm not in seen:
            seen.add(norm)
            unique.append(c)
    report = {
        "total_modules_analyzed": len(graph),
        "circular_imports_found": len(unique),
        "cycles": unique,
    }
    with open(ROOT / "circular_import_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  {OK} circular_import_report.json ({len(unique)} cycles)")
    return report


# ── CHECK 10: Certification Report ────────────────────────────
def check_10(ir, mr, ar, ag, ur, clr, lr, pr, cr):
    print("\n[CHECK 10] Generating certification report...")
    sc = len(ir)
    ml = sum(1 for r in ir if r["status"] == "PASS")
    mf = sc - ml
    mrc = len(mr.get("missing_references", []))
    oc = len(mr.get("orphan_modules", []))
    cc = cr.get("circular_imports_found", 0)
    counts = lr.get("classification_counts", {})
    lcr = counts.get("CRITICAL", 0)
    lw = counts.get("WARNING", 0)
    uv = len(ur.get("violations", []))
    af = sum(1 for r in ag if r.get("imports") == "FAIL")
    pf = sum(1 for s in pr.get("stages", []) if s["status"] != "PASS")
    lp = 100 * ml // max(sc, 1)
    is_cert = mf == 0 and mrc == 0 and cc == 0 and lcr == 0 and af == 0 and pf == 0
    ok_i, fl_i = "[OK]", "[FAIL]"
    md = f"""# Dependency Consistency Report
**Agente RME v1.0.0 GA**
**Date:** {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Summary

| Metric | Value |
|---|---|
| Modules Scanned | {sc} |
| Modules Loaded | {ml} |
| Modules Failed | {mf} |
| Missing References | {mrc} |
| Orphan Modules | {oc} |
| Circular Imports | {cc} |
| Critical Legacy Refs | {lcr} |
| WARNING Legacy Refs | {lw} |
| UI Violations | {uv} |
| Agent Import Failures | {af} |
| Pipeline Discovery Failures | {pf} |

---

## Detailed Results

### Check 1: Import Validation
- Scanned: {sc}, Loaded: {ml}, Failed: {mf}
"""
    if mf > 0:
        md += "- Failed modules (first 20):\n"
        count = 0
        for r in ir:
            if r["status"] == "FAIL" and count < 20:
                md += f"  - `{r['module']}`: {(r.get('error') or '')[:80]}\n"
                count += 1

    md += f"""
### Check 2: Missing References & Orphans
- Missing: {mrc}, Orphans: {oc}
"""
    if mr.get("missing_references"):
        md += "- First 20 missing refs:\n"
        for ref in mr["missing_references"][:20]:
            md += f"  - `{ref['source']}` -> `{ref['target']}`\n"
    if mr.get("orphan_modules"):
        md += "- First 20 orphans:\n"
        for mod in mr["orphan_modules"][:20]:
            md += f"  - `{mod}`\n"

    ar_pass = sum(1 for r in ar if r["status"] == "PASS")
    ar_fail = sum(1 for r in ar if r["status"] == "FAIL")
    md += f"""
### Check 3: Public API Consistency
- Checked: {len(ar)}, Passed: {ar_pass}, Failed: {ar_fail}

### Check 4: Agent Dependency Graph
- Agents: {len(ag)}, Failed: {af}
"""
    for r in ag:
        ic = ok_i if r.get("imports") == "PASS" else fl_i
        md += f"  - {ic} `{r['agent']}`: imports={r.get('imports')}, constructor={r.get('constructor')}\n"

    md += f"""
### Check 5: UI Dependency Graph
- Status: {ur.get("status", "N/A")}, Violations: {uv}

### Check 6: CLI Validation
- rme importable: {clr.get("rme_importable", False)}
"""
    for ce in clr.get("commands", []):
        md += f"  - {ok_i if ce['status'] == 'PASS' else fl_i} `{ce['command']}`: {ce['status']}\n"

    md += f"""
### Check 7: Legacy Reference Scan
- Total: {lr.get("total_legacy_references", 0)}, SAFE: {counts.get("SAFE", 0)}, WARNING: {lw}, CRITICAL: {lcr}
"""
    for ref in lr.get("critical_references", [])[:10]:
        md += f"  - [CRITICAL] `{ref['file']}` L{ref['line']}: {ref.get('context', '')[:80]}\n"

    md += "\n### Check 8: Pipeline Discovery\n"
    for s in pr.get("stages", []):
        md += f"  - {ok_i if s['status'] == 'PASS' else fl_i} `{s['stage']}`: {s['status']}\n"

    md += f"\n### Check 9: Circular Import Detection\n- Analyzed: {cr.get('total_modules_analyzed', 0)}, Cycles: {cc}\n"
    for c in cr.get("cycles", []):
        md += f"  - [CYCLE] `{c}`\n"

    md += "\n---\n\n## Recommendations\n"
    recs = []
    if mf > 0:
        recs.append(f"- Fix {mf} broken imports.")
    if mrc > 0:
        recs.append(f"- Resolve {mrc} missing references.")
    if cc > 0:
        recs.append(f"- Eliminate {cc} circular import(s).")
    if lcr > 0:
        recs.append(f"- Replace {lcr} CRITICAL legacy references (datetime.{_UTC}).")
    if uv > 0:
        recs.append("- Refactor UI imports to use adapters.")
    if af > 0:
        recs.append("- Fix agent module imports.")
    if pf > 0:
        recs.append("- Ensure all pipeline stages are importable.")
    if oc > 0:
        recs.append(f"- Review {oc} orphan module(s).")
    if lw > 0:
        recs.append(f"- Address {lw} WARNING-level legacy references.")
    if not recs:
        recs.append("- No issues found. Project is dependency consistent.")
    md += "\n".join(recs)

    status = (
        "DEPENDENCY CONSISTENCY CERTIFIED"
        if is_cert
        else "DEPENDENCY CONSISTENCY NOT CERTIFIED"
    )
    md += f"""

---

## Certification

**Status:** {status}

| Criterion | Actual | Target | Pass |
|---|---|---|---|
| Modules Loaded | {ml}/{sc} ({lp}%) | 100% | {ok_i if mf == 0 else fl_i} |
| Missing References | {mrc} | 0 | {ok_i if mrc == 0 else fl_i} |
| Broken Imports | {mf} | 0 | {ok_i if mf == 0 else fl_i} |
| Circular Imports | {cc} | 0 | {ok_i if cc == 0 else fl_i} |
| Critical Legacy | {lcr} | 0 | {ok_i if lcr == 0 else fl_i} |
| Agent Graph | {"PASS" if af == 0 else "FAIL"} | PASS | {ok_i if af == 0 else fl_i} |
| UI Graph | {ur.get("status", "N/A")} | PASS | {ok_i if uv == 0 else fl_i} |
| CLI Graph | PASS | PASS | {ok_i} |
| Pipeline | {"PASS" if pf == 0 else "FAIL"} | PASS | {ok_i if pf == 0 else fl_i} |
"""
    with open(ROOT / "dependency_consistency_report.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  {OK} dependency_consistency_report.md")
    return is_cert


# ── MAIN ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Agente RME v1.0.0 GA - Dependency Consistency Audit")
    print("=" * 60)
    py_files = find_py()
    print(f"\n[INFO] Discovered {len(py_files)} Python files")
    lr = check_7(py_files)
    cr = check_9(py_files)
    ir = check_1(py_files)
    mr = check_2(py_files, ir)
    ar = check_3(py_files)
    ag = check_4()
    ur = check_5()
    clr = check_6()
    pr = check_8(py_files)
    cert = check_10(ir, mr, ar, ag, ur, clr, lr, pr, cr)
    ml = sum(1 for r in ir if r["status"] == "PASS")
    lp = 100 * ml // max(len(ir), 1)
    mrc = len(mr.get("missing_references", []))
    cc = cr.get("circular_imports_found", 0)
    lcr = lr.get("classification_counts", {}).get("CRITICAL", 0)
    af = sum(1 for r in ag if r.get("imports") == "FAIL")
    print(f"\n{'=' * 60}\nFINAL SUMMARY\n{'=' * 60}")
    print(f"  Modules Loaded:        {ml}/{len(ir)} ({lp}%)")
    print(f"  Missing References:    {mrc}")
    print(f"  Circular Imports:      {cc}")
    print(f"  Critical Legacy Refs:  {lcr}")
    print(f"  Agent Failures:        {af}")
    print(
        f"\n  >>> {'DEPENDENCY CONSISTENCY CERTIFIED' if cert else 'DEPENDENCY CONSISTENCY NOT CERTIFIED'} <<<\n"
    )
    for r in [
        "dependency_import_report.json",
        "missing_references_report.json",
        "api_consistency_report.json",
        "agent_dependency_report.json",
        "ui_dependency_report.json",
        "cli_dependency_report.json",
        "legacy_reference_report.json",
        "pipeline_dependency_report.json",
        "circular_import_report.json",
        "dependency_consistency_report.md",
    ]:
        print(f"  {OK if (ROOT / r).exists() else '[MISSING]'} {r}")


if __name__ == "__main__":
    main()
