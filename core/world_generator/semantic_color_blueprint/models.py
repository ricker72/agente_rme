from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Iterable


Position = tuple[int, int, int]


class BlueprintLayer(IntEnum):
    """RME-like construction order. A color is interpreted inside its layer."""

    SEA_FOUNDATION = 10
    TERRAIN = 20
    TERRAIN_BORDER = 30
    ROAD = 40
    STRUCTURE_GROUND = 50
    WALL = 60
    DOOR_WINDOW = 70
    ROOF = 75
    STAIRS_RAMP = 80
    NATURE = 90
    DECORATION = 100
    GAMEPLAY = 110


@dataclass
class ColorMaskLayer:
    layer: BlueprintLayer
    cells: dict[Position, str] = field(default_factory=dict)

    def paint(self, positions: Iterable[Position], token_id: str) -> None:
        if not token_id:
            raise ValueError("token_id cannot be empty")
        for position in positions:
            self.cells[tuple(map(int, position))] = token_id

    def erase(self, positions: Iterable[Position]) -> None:
        for position in positions:
            self.cells.pop(tuple(map(int, position)), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer.name,
            "cells": [
                {"x": x, "y": y, "z": z, "token": token}
                for (x, y, z), token in sorted(self.cells.items())
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ColorMaskLayer":
        result = cls(BlueprintLayer[str(data["layer"])])
        for cell in data.get("cells", []):
            result.cells[(int(cell["x"]), int(cell["y"]), int(cell["z"]))] = str(
                cell["token"]
            )
        return result


@dataclass
class SemanticColorBlueprint:
    name: str
    prompt: str = ""
    layers: dict[BlueprintLayer, ColorMaskLayer] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def mask(self, layer: BlueprintLayer) -> ColorMaskLayer:
        return self.layers.setdefault(layer, ColorMaskLayer(layer))

    def paint(
        self, layer: BlueprintLayer, positions: Iterable[Position], token_id: str
    ) -> None:
        self.mask(layer).paint(positions, token_id)

    @property
    def positions(self) -> set[Position]:
        return {position for mask in self.layers.values() for position in mask.cells}

    @property
    def bounds(self) -> tuple[int, int, int, int, int, int] | None:
        if not self.positions:
            return None
        xs, ys, zs = zip(*self.positions)
        return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "rme-semantic-color-blueprint-v1",
            "name": self.name,
            "prompt": self.prompt,
            "metadata": self.metadata,
            "layers": [self.layers[layer].to_dict() for layer in sorted(self.layers)],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SemanticColorBlueprint":
        if data.get("format") != "rme-semantic-color-blueprint-v1":
            raise ValueError("Unsupported semantic color blueprint format")
        result = cls(
            name=str(data["name"]),
            prompt=str(data.get("prompt", "")),
            metadata=dict(data.get("metadata", {})),
        )
        for layer_data in data.get("layers", []):
            mask = ColorMaskLayer.from_dict(layer_data)
            result.layers[mask.layer] = mask
        return result

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SemanticColorBlueprint":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def export_color_masks(self, directory: str | Path, palette: Any) -> list[Path]:
        """Write one lossless PNG per semantic layer plus coordinate metadata."""
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - workspace runtime includes Pillow
            raise RuntimeError("Pillow is required to export color masks") from exc
        bounds = self.bounds
        if bounds is None:
            return []
        min_x, min_y, min_z, max_x, max_y, max_z = bounds
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for layer in sorted(self.layers):
            for z in range(min_z, max_z + 1):
                cells = {
                    (x, y): token
                    for (x, y, cell_z), token in self.layers[layer].cells.items()
                    if cell_z == z
                }
                if not cells:
                    continue
                image = Image.new("RGBA", (max_x - min_x + 1, max_y - min_y + 1), (0, 0, 0, 0))
                pixels = image.load()
                for (x, y), token_id in cells.items():
                    pixels[x - min_x, y - min_y] = (*palette.get(token_id, layer).rgb, 255)
                path = target / f"{layer.name.lower()}_z{z}.png"
                image.save(path)
                written.append(path)
        manifest = {
            "blueprint": self.to_dict(),
            "palette": palette.to_manifest(),
            "origin": {"x": min_x, "y": min_y, "z": min_z},
            "bounds": {"max_x": max_x, "max_y": max_y, "max_z": max_z},
        }
        manifest_path = target / "semantic_color_blueprint.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        written.append(manifest_path)
        return written
