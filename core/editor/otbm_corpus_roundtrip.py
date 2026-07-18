"""Full-file lossless roundtrip certification for real OTBM corpora."""

from __future__ import annotations

import argparse
import json
import mmap
import re
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

@dataclass(frozen=True)
class OTBMStructuralFingerprint:
    metadata: dict[str, Any]
    map_attributes: dict[str, str]
    node_counts: dict[str, int]
    tile_area_count: int
    tile_count: int
    floors: tuple[int, ...]
    tile_areas: tuple[tuple[int, int, int, int], ...]


@dataclass(frozen=True)
class OTBMMapRoundtripResult:
    source: str
    status: str
    source_size: int
    output_size: int
    source_sha256: str
    output_sha256: str
    byte_identical: bool
    full_file_reopened: bool
    nodes: int
    tile_areas: int
    tiles: int
    floors: tuple[int, ...]
    elapsed_seconds: float
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OTBMCorpusRoundtripResult:
    status: str
    maps_checked: int
    maps_passed: int
    elapsed_seconds: float
    results: tuple[OTBMMapRoundtripResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "maps_checked": self.maps_checked,
            "maps_passed": self.maps_passed,
            "elapsed_seconds": self.elapsed_seconds,
            "results": [result.to_dict() for result in self.results],
        }


class OTBMCorpusRoundtripCertifier:
    """Certify lossless export and full structural re-open without retained artifacts."""

    def certify(self, sources: Iterable[str | Path]) -> OTBMCorpusRoundtripResult:
        started = time.perf_counter()
        paths = tuple(dict.fromkeys(Path(source).resolve() for source in sources))
        results: list[OTBMMapRoundtripResult] = []
        with tempfile.TemporaryDirectory(prefix="rme-otbm-roundtrip-") as temporary:
            root = Path(temporary)
            for index, source in enumerate(paths):
                results.append(self._certify_one(source, root / f"{index:03d}-{source.name}"))
        passed = sum(result.status == "PASS" for result in results)
        return OTBMCorpusRoundtripResult(
            status="PASS" if passed == len(results) and results else "FAIL",
            maps_checked=len(results),
            maps_passed=passed,
            elapsed_seconds=round(time.perf_counter() - started, 3),
            results=tuple(results),
        )

    def _certify_one(self, source: Path, output: Path) -> OTBMMapRoundtripResult:
        from core.otbm.lossless_document import LosslessOTBMDocument

        started = time.perf_counter()
        diagnostics: list[str] = []
        identity = None
        output_fingerprint = None
        try:
            if not source.is_file():
                raise FileNotFoundError(source)
            identity = LosslessOTBMDocument(source).write_unchanged(output)
            output_fingerprint = _fingerprint(output)
            if not identity.byte_identical:
                diagnostics.append("lossless export is not byte-identical")
        except Exception as exc:  # noqa: BLE001 - corpus boundary returns diagnostics
            diagnostics.append(f"roundtrip failed: {exc}")

        fingerprint = output_fingerprint
        return OTBMMapRoundtripResult(
            source=str(source),
            status="PASS" if not diagnostics else "FAIL",
            source_size=identity.source_size if identity else (source.stat().st_size if source.exists() else 0),
            output_size=identity.output_size if identity else (output.stat().st_size if output.exists() else 0),
            source_sha256=identity.source_sha256 if identity else "",
            output_sha256=identity.output_sha256 if identity else "",
            byte_identical=bool(identity and identity.byte_identical),
            full_file_reopened=output_fingerprint is not None,
            nodes=sum(fingerprint.node_counts.values()) if fingerprint else 0,
            tile_areas=fingerprint.tile_area_count if fingerprint else 0,
            tiles=fingerprint.tile_count if fingerprint else 0,
            floors=fingerprint.floors if fingerprint else (),
            elapsed_seconds=round(time.perf_counter() - started, 3),
            diagnostics=tuple(diagnostics),
        )


def discover_project_otbms(project_root: str | Path) -> tuple[Path, ...]:
    """Return world.otbm first, followed by every reference map deterministically."""
    root = Path(project_root)
    world = root / "world" / "world.otbm"
    references = sorted(
        (root / "Mapas Referencia").rglob("*.otbm"),
        key=lambda path: str(path).casefold(),
    )
    return tuple(path for path in (world, *references) if path.is_file())


def _fingerprint(path: Path) -> OTBMStructuralFingerprint:
    from core.otbm.otbm_importer import OTBMAttributeReader, RME_NODE_NAMES

    marker_pattern = re.compile(b"[\xfd-\xff]")
    node_counts: dict[str, int] = {}
    tile_areas: list[list[int]] = []
    floors: set[int] = set()
    metadata: dict[str, Any] = {}
    map_attributes: dict[str, str] = {}
    stack: list[tuple[int, int | None]] = []
    active_area: int | None = None
    escaped_position: int | None = None
    root_end = -1

    with path.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
            size = len(data)
            if size < 6 or data[:4] != b"\x00\x00\x00\x00" or data[4] != 0xFE:
                raise ValueError("invalid Canary/RME OTBM header")
            for marker in marker_pattern.finditer(data, 4):
                position = marker.start()
                if escaped_position is not None:
                    if position == escaped_position:
                        escaped_position = None
                        continue
                    if position > escaped_position:
                        escaped_position = None
                value = data[position]
                if value == 0xFD:
                    if position + 1 >= size:
                        raise ValueError("escape byte at end of OTBM")
                    escaped_position = position + 1
                    continue
                if value == 0xFE:
                    if root_end >= 0 or position + 1 >= size:
                        raise ValueError("node starts outside the root container")
                    node_type = data[position + 1]
                    if node_type in (0xFD, 0xFE, 0xFF):
                        raise ValueError(f"escaped node type is unsupported at {position}")
                    name = RME_NODE_NAMES.get(node_type, f"UNKNOWN_{node_type:02X}")
                    node_counts[name] = node_counts.get(name, 0) + 1
                    previous_area = active_area
                    if node_type == 0x04:
                        attrs = _decoded_prefix(data, position + 2, 5)
                        base_x, base_y, z = OTBMAttributeReader.parse_tile_area(attrs)
                        active_area = len(tile_areas)
                        tile_areas.append([base_x, base_y, z, 0])
                        floors.add(z)
                    elif node_type in (0x05, 0x0E) and active_area is not None:
                        tile_areas[active_area][3] += 1
                    if not stack:
                        metadata = OTBMAttributeReader.parse_root(
                            _decoded_prefix(data, position + 1, 17)
                        )
                    elif len(stack) == 1 and node_type == 0x02:
                        map_attributes = OTBMAttributeReader.parse_map_attributes(
                            _decoded_payload(data, position + 2)
                        )
                    stack.append((node_type, previous_area))
                    continue
                if not stack:
                    raise ValueError(f"unexpected NODE_END at {position}")
                _node_type, previous_area = stack.pop()
                active_area = previous_area
                if not stack:
                    root_end = position

            if escaped_position is not None and escaped_position >= size:
                raise ValueError("escape byte at end of OTBM")
            if stack:
                raise ValueError(f"unterminated OTBM tree with depth {len(stack)}")
            if root_end != size - 1:
                raise ValueError(f"unexpected trailing bytes after root node: {size - root_end - 1}")

    tile_count = sum(area[3] for area in tile_areas)
    return OTBMStructuralFingerprint(
        metadata=metadata,
        map_attributes=map_attributes,
        node_counts=dict(sorted(node_counts.items())),
        tile_area_count=len(tile_areas),
        tile_count=tile_count,
        floors=tuple(sorted(floors)),
        tile_areas=tuple(tuple(area) for area in tile_areas),
    )


def _decoded_prefix(data: mmap.mmap, offset: int, length: int) -> bytes:
    decoded = bytearray()
    cursor = offset
    while cursor < len(data) and len(decoded) < length:
        value = data[cursor]
        if value in (0xFE, 0xFF):
            break
        if value == 0xFD:
            cursor += 1
            if cursor >= len(data):
                raise ValueError("escape byte at end of node payload")
            value = data[cursor]
        decoded.append(value)
        cursor += 1
    return bytes(decoded)


def _decoded_payload(data: mmap.mmap, offset: int) -> bytes:
    decoded = bytearray()
    cursor = offset
    while cursor < len(data):
        value = data[cursor]
        if value in (0xFE, 0xFF):
            break
        if value == 0xFD:
            cursor += 1
            if cursor >= len(data):
                raise ValueError("escape byte at end of node payload")
            value = data[cursor]
        decoded.append(value)
        cursor += 1
    return bytes(decoded)


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="OTBM files to certify")
    parser.add_argument("--projects", type=Path, help="Discover world and Mapas Referencia")
    args = parser.parse_args(argv)
    sources = tuple(args.paths)
    if args.projects:
        sources += discover_project_otbms(args.projects)
    result = OTBMCorpusRoundtripCertifier().certify(sources)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "OTBMCorpusRoundtripCertifier",
    "OTBMCorpusRoundtripResult",
    "OTBMMapRoundtripResult",
    "OTBMStructuralFingerprint",
    "discover_project_otbms",
]
