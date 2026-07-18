from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.otbm.otbm_importer import OTBMNodeReader


@dataclass(frozen=True)
class OTBMRoundtripReport:
    path: str
    status: str
    file_size: int
    tile_area_count: int
    estimated_tiles: int
    bytes_per_tile: float
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "file_size": self.file_size,
            "tile_area_count": self.tile_area_count,
            "estimated_tiles": self.estimated_tiles,
            "bytes_per_tile": self.bytes_per_tile,
            "diagnostics": list(self.diagnostics),
        }


class OTBMRoundtripValidator:
    def __init__(self, max_bytes_per_tile: float = 128.0) -> None:
        self.max_bytes_per_tile = max_bytes_per_tile

    def validate_file(self, path: str | Path, *, max_nodes: int = 500_000) -> OTBMRoundtripReport:
        target = Path(path)
        diagnostics: list[str] = []
        if not target.exists():
            return OTBMRoundtripReport(str(target), "FAIL", 0, 0, 0, 0.0, ("missing file",))
        file_size = target.stat().st_size
        try:
            with OTBMNodeReader(target) as reader:
                index = reader.build_index(max_nodes=max_nodes)
        except Exception as exc:  # pragma: no cover - defensive boundary for corrupted maps
            return OTBMRoundtripReport(str(target), "FAIL", file_size, 0, 0, 0.0, (f"parse failed: {exc}",))
        tile_areas = index.stats.tile_areas_detected
        estimated_tiles = index.stats.estimated_tiles
        bytes_per_tile = round(file_size / max(1, estimated_tiles), 4)
        if tile_areas <= 0:
            diagnostics.append("no OTBM_TILE_AREA nodes detected")
        if estimated_tiles <= 0:
            diagnostics.append("no OTBM_TILE/HOUSETILE nodes estimated")
        if bytes_per_tile > self.max_bytes_per_tile:
            diagnostics.append(f"bytes_per_tile {bytes_per_tile} exceeds {self.max_bytes_per_tile}")
        if index.stats.truncated:
            diagnostics.append("roundtrip scan truncated by node limit")
        status = "PASS" if not diagnostics else "FAIL"
        return OTBMRoundtripReport(
            path=str(target),
            status=status,
            file_size=file_size,
            tile_area_count=tile_areas,
            estimated_tiles=estimated_tiles,
            bytes_per_tile=bytes_per_tile,
            diagnostics=tuple(diagnostics),
        )
