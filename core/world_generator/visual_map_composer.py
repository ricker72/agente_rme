from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFilter

from core.otbm.otbm_reference_inspector import inspect_otbm_file
from core.world_generator.world_reference_visualizer import WorldReferenceVisualizer


@dataclass(frozen=True)
class CompositionReferenceMetrics:
    source_name: str
    width: int
    height: int
    entropy: float
    edge_density: float
    water_ratio: float
    nature_ratio: float
    dark_ratio: float


class VisualCompositionReferenceAnalyzer:
    """Learns composition statistics from reference PNGs without copying pixels."""

    def analyze(self, paths: Iterable[str | Path]) -> dict[str, Any]:
        metrics = tuple(self.analyze_one(path) for path in paths)
        if not metrics:
            raise ValueError("At least one visual composition reference is required")
        return {
            "status": "PASS",
            "reference_count": len(metrics),
            "references": [asdict(value) for value in metrics],
            "aggregate": {
                key: round(sum(getattr(value, key) for value in metrics) / len(metrics), 6)
                for key in ("entropy", "edge_density", "water_ratio", "nature_ratio", "dark_ratio")
            },
            "policy": "abstract composition metrics only; source pixels and geometry are never materialized",
        }

    def analyze_to_file(self, paths: Iterable[str | Path], output: str | Path) -> dict[str, Any]:
        report = self.analyze(paths)
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    def analyze_one(self, path: str | Path) -> CompositionReferenceMetrics:
        path = Path(path)
        image = Image.open(path).convert("RGB")
        return self.analyze_image(image, source_name=path.name)

    def analyze_image(
        self,
        image: Image.Image,
        *,
        source_name: str = "anonymous-in-memory-reference",
    ) -> CompositionReferenceMetrics:
        sample = image.convert("RGBA")
        sample.thumbnail((512, 512), Image.Resampling.LANCZOS)
        rgba_pixels = list(sample.get_flattened_data())
        pixels = [(red, green, blue) for red, green, blue, alpha in rgba_pixels if alpha > 16]
        total = max(1, len(pixels))
        edges = sample.convert("RGB").convert("L").filter(ImageFilter.FIND_EDGES)
        edge_values = [
            value
            for value, (_red, _green, _blue, alpha) in zip(edges.get_flattened_data(), rgba_pixels)
            if alpha > 16
        ]
        edge_density = sum(value > 36 for value in edge_values) / total
        return CompositionReferenceMetrics(
            source_name=source_name,
            width=image.width,
            height=image.height,
            entropy=round(_pixel_entropy(pixels), 6),
            edge_density=round(edge_density, 6),
            water_ratio=round(sum(_is_water(pixel) for pixel in pixels) / total, 6),
            nature_ratio=round(sum(_is_nature(pixel) for pixel in pixels) / total, 6),
            dark_ratio=round(sum(max(pixel) < 72 for pixel in pixels) / total, 6),
        )


class RMEFloorVisualComposer:
    """Renders one authoritative RME-style plan image per floor from a real OTBM."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.visualizer = WorldReferenceVisualizer(self.root)

    def compose(
        self,
        otbm_path: str | Path,
        output_dir: str | Path,
        *,
        floors: range = range(0, 8),
        canvas_size: tuple[int, int] = (1024, 768),
    ) -> dict[str, Any]:
        scan = inspect_otbm_file(otbm_path, max_nodes=1_000_000)
        tiles = [tile for tile in scan.get("tiles", ()) if tile.get("items")]
        bounds = _bounds(tiles)
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, Any]] = []
        floor_images: list[tuple[int, Image.Image]] = []
        for z in floors:
            floor_tiles = [tile for tile in tiles if int(tile["z"]) == z]
            image, tile_size = self._render_floor(floor_tiles, bounds, canvas_size)
            path = target / f"rme_plan_floor_z{z}.png"
            image.save(path)
            floor_images.append((z, image))
            rows.append({"floor": z, "tile_count": len(floor_tiles), "tile_size": tile_size, "image": str(path)})
        sheet = _contact_sheet(floor_images, canvas_size)
        sheet_path = target / "rme_plan_floors_0_7.png"
        sheet.save(sheet_path)
        report = {
            "status": "PASS",
            "source_otbm": str(otbm_path),
            "projection": "RME top-down orthographic sprite composition",
            "asset_policy": "official appearances.dat/catalog-content.json sprite-backed stacks only",
            "bounds": bounds,
            "floors": rows,
            "contact_sheet": str(sheet_path),
            "empty_design_floors": [row["floor"] for row in rows if row["tile_count"] == 0],
        }
        (target / "RME_FLOOR_VISUAL_PLAN.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    def _render_floor(
        self,
        tiles: list[dict[str, Any]],
        bounds: tuple[int, int, int, int],
        canvas_size: tuple[int, int],
    ) -> tuple[Image.Image, int]:
        min_x, min_y, max_x, max_y = bounds
        width_tiles = max(1, max_x - min_x + 1)
        height_tiles = max(1, max_y - min_y + 1)
        tile_size = max(1, min(canvas_size[0] // width_tiles, canvas_size[1] // height_tiles))
        image = Image.new("RGBA", canvas_size, (0, 0, 0, 255))
        offset_x = (canvas_size[0] - width_tiles * tile_size) // 2
        offset_y = (canvas_size[1] - height_tiles * tile_size) // 2
        for tile in sorted(tiles, key=lambda value: (int(value["y"]), int(value["x"]))):
            x, y = int(tile["x"]), int(tile["y"])
            stack = [int(value) for value in tile.get("items", ()) if int(value) > 0]
            self.visualizer.render_item_stack_on_image(
                image,
                stack,
                offset_x + (x - min_x) * tile_size,
                offset_y + (y - min_y) * tile_size,
                tile_size,
            )
        return image, tile_size


def _bounds(tiles: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    if not tiles:
        return 0, 0, 0, 0
    return (
        min(int(tile["x"]) for tile in tiles),
        min(int(tile["y"]) for tile in tiles),
        max(int(tile["x"]) for tile in tiles),
        max(int(tile["y"]) for tile in tiles),
    )


def _contact_sheet(floors: list[tuple[int, Image.Image]], canvas_size: tuple[int, int]) -> Image.Image:
    thumb_size = (canvas_size[0] // 4, canvas_size[1] // 2)
    sheet = Image.new("RGB", (thumb_size[0] * 4, thumb_size[1] * 2), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for index, (z, image) in enumerate(floors):
        thumb = image.convert("RGB").resize(thumb_size, Image.Resampling.LANCZOS)
        x, y = (index % 4) * thumb_size[0], (index // 4) * thumb_size[1]
        sheet.paste(thumb, (x, y))
        draw.text((x + 8, y + 8), f"Floor {z}", fill=(255, 255, 255))
    return sheet


def _is_water(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel
    return blue > 80 and blue > red * 1.25 and blue > green * 1.08


def _is_nature(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel
    return green > 55 and green > red * 1.08 and green > blue * 1.05


def _pixel_entropy(pixels: list[tuple[int, int, int]]) -> float:
    if not pixels:
        return 0.0
    histogram = Counter(pixels)
    total = len(pixels)
    return -sum((count / total) * math.log2(count / total) for count in histogram.values())
