#!/usr/bin/env python3
"""Audit and prepare independently installable Agente RME applications."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "deployment" / "applications.json"


class IsolationError(RuntimeError):
    """Raised when an application cannot be isolated safely."""


@dataclass(frozen=True)
class ApplicationSpec:
    name: str
    version: str
    description: str
    entry_point: str
    owned_packages: tuple[str, ...]
    owned_modules: tuple[str, ...]
    internal_dependencies: tuple[str, ...]
    optional_provider_modules: dict[str, tuple[str, ...]]
    requirements: Path
    resources: tuple[str, ...]


def _load_specs(config_path: Path) -> dict[str, ApplicationSpec]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise IsolationError("Unsupported applications schema")
    specs: dict[str, ApplicationSpec] = {}
    for name, raw in payload.get("applications", {}).items():
        specs[name] = ApplicationSpec(
            name=name,
            version=str(raw["version"]),
            description=str(raw["description"]),
            entry_point=str(raw["entry_point"]),
            owned_packages=tuple(raw.get("owned_packages", ())),
            owned_modules=tuple(raw.get("owned_modules", ())),
            internal_dependencies=tuple(raw.get("internal_dependencies", ())),
            optional_provider_modules={
                str(provider): tuple(str(path).replace("\\", "/") for path in paths)
                for provider, paths in raw.get("optional_provider_modules", {}).items()
            },
            requirements=ROOT / raw["requirements"],
            resources=tuple(raw.get("resources", ())),
        )
    if not specs:
        raise IsolationError("No applications declared")
    return specs


def _ownership(specs: dict[str, ApplicationSpec]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for spec in specs.values():
        for package in spec.owned_packages:
            previous = owners.setdefault(package, spec.name)
            if previous != spec.name:
                raise IsolationError(f"Package {package!r} owned by {previous} and {spec.name}")
    return owners


def _top_level_imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise IsolationError(f"Cannot parse {path.relative_to(ROOT)}: {exc}") from exc
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.partition(".")[0])
    return imports


def audit(specs: dict[str, ApplicationSpec]) -> dict[str, Any]:
    owners = _ownership(specs)
    errors: list[str] = []
    applications: dict[str, Any] = {}
    for spec in specs.values():
        allowed_apps = {spec.name, *spec.internal_dependencies}
        files: list[Path] = []
        missing: list[str] = []
        for package in spec.owned_packages:
            package_dir = ROOT / package
            if not package_dir.is_dir():
                missing.append(package)
            else:
                files.extend(package_dir.rglob("*.py"))
        for module in spec.owned_modules:
            module_path = ROOT / module
            if not module_path.is_file():
                missing.append(module)
            else:
                files.append(module_path)
        if not spec.requirements.is_file():
            missing.append(str(spec.requirements.relative_to(ROOT)))
        undeclared: dict[str, list[str]] = {}
        optional_imports: dict[str, list[str]] = {}
        for path in files:
            relative_path = str(path.relative_to(ROOT)).replace("\\", "/")
            for imported in _top_level_imports(path):
                owner = owners.get(imported)
                if owner is not None and owner not in allowed_apps:
                    provider_paths = spec.optional_provider_modules.get(owner, ())
                    if relative_path in provider_paths:
                        optional_imports.setdefault(owner, []).append(relative_path)
                    else:
                        undeclared.setdefault(owner, []).append(relative_path)
        for owner, paths in undeclared.items():
            errors.append(
                f"{spec.name} imports {owner} without declaring it: "
                + ", ".join(sorted(set(paths))[:5])
            )
        if missing:
            errors.append(f"{spec.name} missing: {', '.join(missing)}")
        applications[spec.name] = {
            "python_files": len(files),
            "owned_packages": list(spec.owned_packages),
            "dependencies": list(spec.internal_dependencies),
            "missing": missing,
            "undeclared_internal_imports": undeclared,
            "optional_provider_imports": optional_imports,
        }
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "applications": applications}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pyproject(spec: ApplicationSpec) -> str:
    packages = ", ".join(json.dumps(f"{name}*") for name in spec.owned_packages)
    modules = [Path(name).stem for name in spec.owned_modules]
    module_line = f"py-modules = {json.dumps(modules)}\n" if modules else ""
    script_section = ""
    if spec.entry_point:
        module, function = spec.entry_point.split(":", 1)
        script_section = f"[project.scripts]\n{spec.name} = {json.dumps(f'{module}:{function}')}\n\n"
    return (
        "[build-system]\nrequires = [\"setuptools>=68\", \"wheel\"]\n"
        "build-backend = \"setuptools.build_meta\"\n\n"
        f"[project]\nname = {json.dumps(spec.name)}\nversion = {json.dumps(spec.version)}\n"
        f"description = {json.dumps(spec.description)}\nrequires-python = \">=3.11\"\n"
        "dynamic = [\"dependencies\"]\n\n"
        f"{script_section}"
        "[tool.setuptools.dynamic]\ndependencies = {file = [\"requirements.txt\"]}\n\n"
        f"[tool.setuptools]\n{module_line}include-package-data = true\n\n"
        f"[tool.setuptools.packages.find]\ninclude = [{packages}]\n"
    )


def prepare(spec: ApplicationSpec, output_root: Path, include_resources: bool) -> dict[str, Any]:
    destination = output_root / spec.name
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    copied: list[dict[str, Any]] = []
    for relative in (*spec.owned_packages, *spec.owned_modules):
        source = ROOT / relative
        target = destination / relative
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    shutil.copy2(spec.requirements, destination / "requirements.txt")
    (destination / "pyproject.toml").write_text(_pyproject(spec), encoding="utf-8")
    if include_resources:
        for relative in spec.resources:
            source = ROOT / relative
            if not source.exists():
                continue
            target = destination / relative
            if source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.tmp"))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            copied.append({"path": str(path.relative_to(destination)), "sha256": _sha256(path), "bytes": path.stat().st_size})
    manifest = {"application": spec.name, "version": spec.version, "files": copied}
    (destination / "isolation-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"application": spec.name, "destination": str(destination), "files": len(copied)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "prepare"))
    parser.add_argument("--app", action="append", dest="apps")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "isolated-apps")
    parser.add_argument("--include-resources", action="store_true")
    args = parser.parse_args(argv)
    try:
        specs = _load_specs(args.config.resolve())
        report = audit(specs)
        if report["status"] != "PASS":
            print(json.dumps(report, indent=2))
            return 1
        if args.command == "audit":
            print(json.dumps(report, indent=2))
            return 0
        selected = args.apps or list(specs)
        unknown = sorted(set(selected) - set(specs))
        if unknown:
            raise IsolationError(f"Unknown applications: {', '.join(unknown)}")
        results = [prepare(specs[name], args.output.resolve(), args.include_resources) for name in selected]
        print(json.dumps({"status": "PASS", "prepared": results}, indent=2))
        return 0
    except (IsolationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
