"""Non-destructive reference-world learning profiles for OpenTibia maps."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.otbm.otbm_reference_inspector import inspect_otbm_file

_PROFILE_CACHE: dict = {}


REFERENCE_LEARNING_DOMAINS = (
    "Cities",
    "Roads",
    "Decoration",
    "Nature",
    "Mountains",
    "Depots",
    "NPC placement",
    "Quest layout",
    "Boat systems",
    "Bridges",
    "Hunts",
    "Spawn distribution",
    "Waypoint organization",
    "Architecture",
    "Tile transitions",
    "Terrain composition",
)


@dataclass(frozen=True)
class ReferenceWorldProfile:
    source_path: str
    file_size: int
    sha256: str
    parse_truncated: bool
    parse_node_limit: int
    node_counts: dict[str, int]
    sampled_tile_count: int
    sampled_item_count: int
    sampled_town_count: int
    sampled_waypoint_count: int
    learning_domains: tuple[str, ...]
    copy_policy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "file_size": self.file_size,
            "sha256": self.sha256,
            "parse_truncated": self.parse_truncated,
            "parse_node_limit": self.parse_node_limit,
            "node_counts": self.node_counts,
            "sampled_tile_count": self.sampled_tile_count,
            "sampled_item_count": self.sampled_item_count,
            "sampled_town_count": self.sampled_town_count,
            "sampled_waypoint_count": self.sampled_waypoint_count,
            "learning_domains": list(self.learning_domains),
            "copy_policy": self.copy_policy,
        }


class ReferenceWorldAnalyzer:
    """Builds a bounded profile from an OTBM reference world without modifying it."""

    def __init__(self, world_path: str | Path = "projects/world/world.otbm", max_nodes: int = 12000) -> None:
        self.world_path = Path(world_path)
        self.max_nodes = max_nodes

    def analyze(self) -> ReferenceWorldProfile:
        if not self.world_path.exists():
            raise FileNotFoundError(f"missing reference world: {self.world_path}")
        before = self.world_path.stat()
        cache_key = (str(self.world_path.resolve()), before.st_size, before.st_mtime_ns, self.max_nodes)
        if cache_key in _PROFILE_CACHE:
            return _PROFILE_CACHE[cache_key]
        digest = self._sha256(self.world_path)
        inspection = inspect_otbm_file(self.world_path, max_nodes=self.max_nodes)
        after = self.world_path.stat()
        if before.st_mtime_ns != after.st_mtime_ns or before.st_size != after.st_size:
            raise RuntimeError("reference world changed during analysis")
        profile = ReferenceWorldProfile(
            source_path=str(self.world_path.resolve()),
            file_size=after.st_size,
            sha256=digest,
            parse_truncated=bool(inspection.get("parse_truncated")),
            parse_node_limit=int(inspection.get("parse_node_limit") or self.max_nodes),
            node_counts={str(k): int(v) for k, v in (inspection.get("node_counts") or {}).items()},
            sampled_tile_count=len(inspection.get("tiles") or []),
            sampled_item_count=len(inspection.get("items") or []),
            sampled_town_count=len(inspection.get("towns") or []),
            sampled_waypoint_count=len(inspection.get("waypoints") or []),
            learning_domains=REFERENCE_LEARNING_DOMAINS,
            copy_policy="Learn patterns only. Never copy, export, modify, clone, or reproduce layouts.",
        )
        _PROFILE_CACHE[cache_key] = profile
        return profile

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
