"""Bounded, UI-neutral RME copybuffer implementation."""

from __future__ import annotations

from .model import TileCoord, TileKey, WorkspaceTile


class CopyBuffer:
    def __init__(self, max_history: int = 32) -> None:
        self.max_history = max(1, int(max_history))
        self.tiles: dict[TileKey, WorkspaceTile] = {}
        self.history: list[dict[TileKey, WorkspaceTile]] = []

    def replace(self, tiles: dict[TileKey, WorkspaceTile], *, record: bool = True) -> int:
        self.tiles.clear()
        self.tiles.update({key: tile.copy() for key, tile in tiles.items()})
        if record and self.tiles:
            self.history.append(self.snapshot())
            del self.history[: max(0, len(self.history) - self.max_history)]
        return len(self.tiles)

    def snapshot(self) -> dict[TileKey, WorkspaceTile]:
        return {key: tile.copy() for key, tile in self.tiles.items()}

    def rotate_clockwise(self) -> int:
        if not self.tiles:
            return 0
        min_x = min(key[0] for key in self.tiles)
        min_y = min(key[1] for key in self.tiles)
        max_y = max(key[1] for key in self.tiles)
        rotated: dict[TileKey, WorkspaceTile] = {}
        for key, tile in self.tiles.items():
            rel_x = key[0] - min_x
            rel_y = key[1] - min_y
            coord = TileCoord(min_x + max_y - min_y - rel_y, min_y + rel_x, key[2])
            clone = tile.copy()
            clone.coord = coord
            rotated[coord.key()] = clone
        return self.replace(rotated)

    def mirror_horizontal(self) -> int:
        if not self.tiles:
            return 0
        min_x = min(key[0] for key in self.tiles)
        max_x = max(key[0] for key in self.tiles)
        mirrored: dict[TileKey, WorkspaceTile] = {}
        for key, tile in self.tiles.items():
            coord = TileCoord(max_x - (key[0] - min_x), key[1], key[2])
            clone = tile.copy()
            clone.coord = coord
            mirrored[coord.key()] = clone
        return self.replace(mirrored)

    def audit(self) -> dict[str, object]:
        return {
            "copybuffer_ready": True,
            "owner": "workspace_core",
            "tile_count": len(self.tiles),
            "history_depth": len(self.history),
            "history_limit": self.max_history,
        }


__all__ = ["CopyBuffer"]
