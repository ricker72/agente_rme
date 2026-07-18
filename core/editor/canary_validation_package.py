"""Build a self-contained Canary/RME manual-validation package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
MANIFEST_NAME = "CANARY_VALIDATION_MANIFEST.json"
LAUNCHER_NAME = "launch_canary_validation.ps1"


@dataclass(frozen=True)
class CanaryValidationPackageResult:
    status: str
    package: str
    package_sha256: str
    package_size: int
    files: int
    maps: int
    assets: int
    roundtrip_status: str
    manual_validation_status: str
    launcher: str
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _Entry:
    archive_path: str
    source: Path | None
    data: bytes | None
    kind: str
    size: int
    sha256: str


class CanaryValidationPackager:
    """Certify, package and verify maps plus the complete official client catalog."""

    def __init__(self, repository_root: str | Path) -> None:
        self.root = Path(repository_root).resolve()
        self.projects = self.root / "projects"
        self.assets = self.root / "assets"
        self.canary_root = (
            self.projects
            / "canary-extracted"
            / "canary-map-editor-v4.0-windows"
        )
        self.canary_executable = self.canary_root / "canary-map-editor-x64.exe"

    def build(
        self,
        output_directory: str | Path,
        *,
        sources: Iterable[str | Path] | None = None,
        certify_roundtrip: bool = True,
    ) -> CanaryValidationPackageResult:
        from core.editor.otbm_corpus_roundtrip import (
            OTBMCorpusRoundtripCertifier,
            discover_project_otbms,
        )

        diagnostics: list[str] = []
        output = Path(output_directory).resolve()
        output.mkdir(parents=True, exist_ok=True)
        maps = tuple(
            Path(path).resolve()
            for path in (sources or discover_project_otbms(self.projects))
        )
        if not maps:
            raise ValueError("No OTBM maps were selected for packaging")
        self._require_runtime_inputs(maps)

        if certify_roundtrip:
            roundtrip = OTBMCorpusRoundtripCertifier().certify(maps)
            if roundtrip.status != "PASS":
                failed = [item.source for item in roundtrip.results if item.status != "PASS"]
                raise ValueError(f"OTBM roundtrip certification failed: {failed}")
            roundtrip_by_source = {
                str(Path(item.source).resolve()): item.to_dict()
                for item in roundtrip.results
            }
            roundtrip_status = roundtrip.status
        else:
            roundtrip_by_source = {}
            roundtrip_status = "SKIPPED"

        entries = self._collect_entries(maps)
        launcher = _launcher_script(self.canary_executable)
        launcher_entry = _bytes_entry(LAUNCHER_NAME, launcher.encode("utf-8-sig"), "launcher")
        manifest = self._manifest(entries, maps, roundtrip_by_source)
        manifest_bytes = _json_bytes(manifest)
        manifest_entry = _bytes_entry(MANIFEST_NAME, manifest_bytes, "manifest")
        all_entries = tuple(entries) + (launcher_entry, manifest_entry)

        package = output / "canary_rme_validation_bundle.zip"
        temporary = output / f".{package.name}.tmp"
        if temporary.exists():
            temporary.unlink()
        try:
            self._write_zip(temporary, all_entries)
            diagnostics.extend(self._validate_zip(temporary, all_entries))
            if diagnostics:
                raise ValueError("; ".join(diagnostics))
            os.replace(temporary, package)
        finally:
            if temporary.exists():
                temporary.unlink()

        manifest_path = output / MANIFEST_NAME
        launcher_path = output / LAUNCHER_NAME
        manifest_path.write_bytes(manifest_bytes)
        launcher_path.write_bytes(launcher.encode("utf-8-sig"))
        package_hash = _sha256(package)
        return CanaryValidationPackageResult(
            status="PASS",
            package=str(package),
            package_sha256=package_hash,
            package_size=package.stat().st_size,
            files=len(all_entries),
            maps=len(maps),
            assets=sum(entry.kind == "client_asset" for entry in entries),
            roundtrip_status=roundtrip_status,
            manual_validation_status="PENDING_HUMAN_REVIEW",
            launcher=str(launcher_path),
            diagnostics=tuple(diagnostics),
        )

    def _require_runtime_inputs(self, maps: tuple[Path, ...]) -> None:
        required = (
            self.canary_executable,
            self.assets / "catalog-content.json",
        )
        missing = [str(path) for path in (*required, *maps) if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing Canary validation inputs: {missing}")

    def _collect_entries(self, maps: tuple[Path, ...]) -> tuple[_Entry, ...]:
        entries: dict[str, _Entry] = {}
        for map_path in maps:
            archive_map = self._map_archive_path(map_path)
            self._add_source(entries, archive_map, map_path, "otbm")
            for sidecar in _otbm_sidecars(map_path):
                if not sidecar.is_file():
                    raise FileNotFoundError(
                        f"OTBM sidecar declared by {map_path.name} is missing: {sidecar.name}"
                    )
                archive_sidecar = str(PurePosixPath(archive_map).parent / sidecar.name)
                self._add_source(entries, archive_sidecar, sidecar, "map_sidecar")

        catalog_path = self.assets / "catalog-content.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self._add_source(
            entries,
            "client/assets/catalog-content.json",
            catalog_path,
            "client_asset",
        )
        for item in catalog:
            filename = str(item.get("file", "")).strip()
            if not filename:
                continue
            source = (self.assets / filename).resolve()
            if source.parent != self.assets.resolve():
                raise ValueError(f"Unsafe catalog asset path: {filename}")
            if not source.is_file():
                raise FileNotFoundError(f"Catalog asset is missing: {filename}")
            self._add_source(
                entries,
                str(PurePosixPath("client/assets") / filename),
                source,
                "client_asset",
            )
        package_json = _json_bytes(
            {
                "version": "RME-Agent-Official-Assets",
                "catalog": "catalog-content.json",
            }
        )
        entries["client/package.json"] = _bytes_entry(
            "client/package.json", package_json, "client_config"
        )
        return tuple(entries[name] for name in sorted(entries))

    def _map_archive_path(self, path: Path) -> str:
        world = (self.projects / "world" / "world.otbm").resolve()
        if path == world:
            return "maps/world/world.otbm"
        references = (self.projects / "Mapas Referencia").resolve()
        try:
            relative = path.relative_to(references)
        except ValueError:
            return str(PurePosixPath("maps/custom") / path.name)
        return str(PurePosixPath("maps/references") / PurePosixPath(relative.as_posix()))

    @staticmethod
    def _add_source(
        entries: dict[str, _Entry], archive_path: str, source: Path, kind: str
    ) -> None:
        normalized = _safe_archive_path(archive_path)
        candidate = _Entry(
            archive_path=normalized,
            source=source,
            data=None,
            kind=kind,
            size=source.stat().st_size,
            sha256=_sha256(source),
        )
        existing = entries.get(normalized)
        if existing and existing.sha256 != candidate.sha256:
            raise ValueError(f"Conflicting package entry: {normalized}")
        entries[normalized] = candidate

    def _manifest(
        self,
        entries: tuple[_Entry, ...],
        maps: tuple[Path, ...],
        roundtrip: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        packaged_maps = []
        for path in maps:
            packaged_maps.append(
                {
                    "archive_path": self._map_archive_path(path),
                    "source_sha256": _sha256(path),
                    "roundtrip": roundtrip.get(str(path.resolve()), {"status": "SKIPPED"}),
                }
            )
        return {
            "schema": "rme-agent.canary-manual-validation.v1",
            "status": "CERTIFIED_PENDING_MANUAL_REVIEW",
            "canary": {
                "executable": self.canary_executable.name,
                "command_line_contract": "exactly one OTBM path argument",
                "source": "source/application.cpp:ParseCommandLineMap + OnEventLoopEnter",
            },
            "default_map": "maps/references/Krailos/Krailos.otbm",
            "maps": packaged_maps,
            "files": [
                {
                    "path": entry.archive_path,
                    "kind": entry.kind,
                    "size": entry.size,
                    "sha256": entry.sha256,
                }
                for entry in entries
            ],
        }

    @staticmethod
    def _write_zip(path: Path, entries: tuple[_Entry, ...]) -> None:
        with zipfile.ZipFile(
            path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as archive:
            for entry in entries:
                info = zipfile.ZipInfo(entry.archive_path, ZIP_TIMESTAMP)
                info.external_attr = 0o644 << 16
                info.compress_type = (
                    zipfile.ZIP_STORED
                    if Path(entry.archive_path).suffix.lower() in {".lzma", ".jpg", ".png"}
                    else zipfile.ZIP_DEFLATED
                )
                with archive.open(info, "w", force_zip64=True) as destination:
                    if entry.source is not None:
                        with entry.source.open("rb") as source:
                            shutil.copyfileobj(source, destination, 1024 * 1024)
                    else:
                        destination.write(entry.data or b"")

    @staticmethod
    def _validate_zip(path: Path, entries: tuple[_Entry, ...]) -> list[str]:
        diagnostics: list[str] = []
        expected = {entry.archive_path: entry for entry in entries}
        try:
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    diagnostics.append("ZIP CRC validation failed")
                names = set(archive.namelist())
                if names != set(expected):
                    diagnostics.append("ZIP file list differs from manifest inputs")
                for name, entry in expected.items():
                    digest = hashlib.sha256()
                    with archive.open(name) as source:
                        for chunk in iter(lambda: source.read(1024 * 1024), b""):
                            digest.update(chunk)
                    if digest.hexdigest() != entry.sha256:
                        diagnostics.append(f"ZIP hash mismatch: {name}")
        except (OSError, zipfile.BadZipFile) as exc:
            diagnostics.append(f"ZIP validation failed: {exc}")
        return diagnostics


def _otbm_sidecars(path: Path) -> tuple[Path, ...]:
    from core.otbm.otbm_importer import OTBMNodeReader

    with OTBMNodeReader(path) as reader:
        index = reader.build_index(max_nodes=2, max_bytes=100_000)
    names = {
        value
        for key, value in index.map_attributes.items()
        if key in {"spawn_file", "spawn_npc_file", "house_file", "zone_file"} and value
    }
    return tuple(path.parent / name for name in sorted(names))


def _bytes_entry(archive_path: str, data: bytes, kind: str) -> _Entry:
    return _Entry(
        archive_path=_safe_archive_path(archive_path),
        source=None,
        data=data,
        kind=kind,
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _safe_archive_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe ZIP path: {value}")
    return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _launcher_script(default_canary: Path) -> str:
    escaped_canary = str(default_canary).replace("'", "''")
    return f"""param(
    [string]$MapEntry = 'maps/references/Krailos/Krailos.otbm',
    [string]$CanaryExe = '{escaped_canary}'
)
$ErrorActionPreference = 'Stop'
$bundle = Join-Path $PSScriptRoot 'canary_rme_validation_bundle.zip'
if (-not (Test-Path -LiteralPath $bundle)) {{ throw "Validation bundle not found: $bundle" }}
if (-not (Test-Path -LiteralPath $CanaryExe)) {{ throw "Canary executable not found: $CanaryExe" }}
$tempBase = [IO.Path]::GetFullPath($env:TEMP)
$stage = [IO.Path]::GetFullPath((Join-Path $tempBase 'rme-canary-manual-validation'))
if (-not $stage.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase)) {{ throw 'Unsafe staging path' }}
if (Test-Path -LiteralPath $stage) {{ Remove-Item -LiteralPath $stage -Recurse -Force }}
New-Item -ItemType Directory -Path $stage | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($bundle)
try {{
    $mapDir = ([IO.Path]::GetDirectoryName($MapEntry)).Replace('\\','/') + '/'
    $selected = @($zip.Entries | Where-Object {{ $_.FullName.StartsWith($mapDir) -or $_.FullName.StartsWith('client/') }})
    if (-not ($selected | Where-Object {{ $_.FullName -eq $MapEntry }})) {{ throw "Map entry not found: $MapEntry" }}
    foreach ($entry in $selected) {{
        if ([string]::IsNullOrEmpty($entry.Name)) {{ continue }}
        $target = [IO.Path]::GetFullPath((Join-Path $stage $entry.FullName))
        if (-not $target.StartsWith($stage + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {{ throw 'Unsafe ZIP entry' }}
        New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $true)
    }}
}} finally {{ $zip.Dispose() }}
$mapPath = Join-Path $stage $MapEntry
$process = Start-Process -FilePath $CanaryExe -ArgumentList @('"' + $mapPath + '"') -WorkingDirectory ([IO.Path]::GetDirectoryName($CanaryExe)) -PassThru
$process.WaitForExit()
if (Test-Path -LiteralPath $stage) {{ Remove-Item -LiteralPath $stage -Recurse -Force }}
exit $process.ExitCode
"""


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-roundtrip", action="store_true")
    args = parser.parse_args(argv)
    result = CanaryValidationPackager(args.root).build(
        args.output, certify_roundtrip=not args.skip_roundtrip
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = ["CanaryValidationPackager", "CanaryValidationPackageResult"]
