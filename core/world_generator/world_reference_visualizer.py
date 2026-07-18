from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from core.otbm.otbm_reference_inspector import inspect_otbm_file
from rme_rendering.rme_draw_order import RMEDrawOrderEngine, RMEStackItem
from rme_rendering.rme_visual_compat import RMEViewState
from rme_rendering.sprites import OfficialSpritePixelDecoder


ROLE_FILES = {
    "GROUND": "APPEARANCE_GROUND_IDS.json",
    "WALL": "APPEARANCE_WALL_IDS.json",
    "WATER": "APPEARANCE_WATER_IDS.json",
    "NATURE": "APPEARANCE_NATURE_IDS.json",
    "ROOF": "APPEARANCE_ROOF_IDS.json",
    "STAIR": "APPEARANCE_STAIR_IDS.json",
    "RAMP": "APPEARANCE_RAMP_IDS.json",
    "DOOR": "APPEARANCE_DOOR_IDS.json",
    "BORDER": "APPEARANCE_BORDER_IDS.json",
    "DECORATION": "APPEARANCE_DECORATION_IDS.json",
    "INTERIOR": "APPEARANCE_INTERIOR_IDS.json",
    "EXTERIOR": "APPEARANCE_EXTERIOR_IDS.json",
}

ROLE_COLORS = {
    "GROUND": (73, 126, 58),
    "WALL": (93, 86, 83),
    "WATER": (43, 105, 143),
    "NATURE": (39, 104, 59),
    "ROOF": (129, 70, 54),
    "STAIR": (164, 135, 84),
    "RAMP": (139, 116, 79),
    "DOOR": (112, 74, 44),
    "BORDER": (102, 94, 70),
    "DECORATION": (144, 119, 72),
    "INTERIOR": (123, 102, 75),
    "EXTERIOR": (111, 91, 68),
    "UNKNOWN": (24, 24, 24),
}

GROUND_ROLES = {"GROUND", "WATER", "MOUNTAIN", "ROAD", "DOCK", "INTERIOR", "EXTERIOR"}


@dataclass(frozen=True)
class ReferenceChunk:
    name: str
    bounds: tuple[int, int, int, int]
    z: int
    tile_count: int
    density_score: int

    def to_dict(self) -> dict[str, Any]:
        min_x, min_y, max_x, max_y = self.bounds
        return {
            "name": self.name,
            "bounds": [min_x, min_y, max_x, max_y],
            "z": self.z,
            "tile_count": self.tile_count,
            "density_score": self.density_score,
        }


class WorldReferenceVisualizer:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path.cwd())
        self.item_catalog = self._load_json("APPEARANCE_ITEM_CATALOG.json", {})
        self.render_catalog = self._load_json("APPEARANCE_RENDER_CATALOG.json", {})
        self.role_lookup = self._build_role_lookup()
        self.sprite_decoder = OfficialSpritePixelDecoder(self.root)
        self.draw_order = RMEDrawOrderEngine()

    def build_reference_atlas(
        self,
        world_path: str | Path,
        output_dir: str | Path,
        *,
        chunk_size: int = 64,
        max_chunks: int = 4,
        max_nodes: int = 2_000_000,
        tile_size: int = 32,
    ) -> dict[str, Any]:
        scan = inspect_otbm_file(world_path, max_nodes=max_nodes)
        chunks = select_reference_chunks(scan["tiles"], chunk_size=chunk_size, max_chunks=max_chunks)
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        for stale in output.glob("world_ref_*"):
            if stale.is_file():
                stale.unlink()

        chunk_reports = []
        for chunk in chunks:
            image_path = output / f"{chunk.name}.png"
            index_path = output / f"{chunk.name}.tile_index.json"
            chunk_reports.append(
                self.render_chunk(
                    scan["tiles"],
                    chunk,
                    image_path=image_path,
                    index_path=index_path,
                    tile_size=tile_size,
                )
            )

        report = {
            "stage": "World OTBM Visual Reference Atlas",
            "status": "PASS" if chunk_reports else "BLOCKED",
            "source": str(world_path),
            "policy": {
                "purpose": "visual learning and exact tile/item inspection",
                "copy_tile_payloads": False,
                "copy_coordinates_into_generated_maps": False,
                "use_as_reference_only": True,
            },
            "scan": {
                "tile_count": len(scan["tiles"]),
                "item_count": len(scan["item_ids"]),
                "parse_truncated": scan["parse_truncated"],
                "node_limit": scan["parse_node_limit"],
            },
            "rendering": {
                "mode": "rme_like_multifloor_sprite_atlas",
                "tile_size": tile_size,
                "grid_visible": False,
                "ids_exported": True,
                "sprite_backed_validated": True,
                "floor_range_source": "Canary/RME MapDrawer::SetupVars",
                "floor_context": "nearby floors are rendered as dim ghost context before current z",
            },
            "chunks": chunk_reports,
        }
        (output / "WORLD_REFERENCE_VISUAL_ATLAS_REPORT.json").write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return report

    def render_chunk(
        self,
        tiles: list[dict[str, Any]],
        chunk: ReferenceChunk,
        *,
        image_path: str | Path,
        index_path: str | Path,
        tile_size: int = 10,
    ) -> dict[str, Any]:
        min_x, min_y, max_x, max_y = chunk.bounds
        padding = tile_size * 2
        width = (max_x - min_x + 1) * tile_size + padding * 2
        height = (max_y - min_y + 1) * tile_size + padding * 2
        image = Image.new("RGBA", (width, height), ROLE_COLORS["UNKNOWN"] + (255,))
        draw = ImageDraw.Draw(image)
        view_state = RMEViewState(floor=chunk.z, screen_width=width, screen_height=height)
        rme_floor_sequence = [z for z in view_state.visible_floor_sequence() if z != chunk.z]
        indexed_tiles = []
        role_counts: Counter[str] = Counter()
        missing_sprite_ids: Counter[int] = Counter()
        official_sprite_tiles = 0
        context_floor_tiles = 0
        fallback_tiles = 0
        empty_tile_count = 0
        tile_lookup = {
            (int(tile["x"]), int(tile["y"]), int(tile["z"])): tile
            for tile in tiles
            if min_x <= int(tile["x"]) <= max_x and min_y <= int(tile["y"]) <= max_y
        }

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                current_tile = tile_lookup.get((x, y, chunk.z))
                if current_tile and any(int(item_id) > 0 for item_id in current_tile.get("items", [])):
                    continue
                context_tile = self.context_tile_for(tile_lookup, x, y, rme_floor_sequence)
                if context_tile is None:
                    continue
                raw_item_ids = [int(item_id) for item_id in context_tile.get("items", [])]
                item_ids = [item_id for item_id in raw_item_ids if item_id > 0]
                if not item_ids:
                    continue
                px = padding + (x - min_x) * tile_size
                py = padding + (y - min_y) * tile_size
                rendered = self.render_item_stack_on_image(image, item_ids, px, py, tile_size, opacity=0.55)
                if rendered:
                    context_floor_tiles += 1

        for tile in tiles:
            if tile["z"] != chunk.z or not (min_x <= tile["x"] <= max_x and min_y <= tile["y"] <= max_y):
                continue
            raw_item_ids = [int(item_id) for item_id in tile.get("items", [])]
            item_ids = [item_id for item_id in raw_item_ids if item_id > 0]
            ground_id = self.ground_id_for_stack(item_ids)
            top_id = item_ids[-1] if item_ids else ground_id
            role = self.role_for_item(ground_id)
            if not item_ids:
                empty_tile_count += 1
                indexed_tiles.append(
                    {
                        "x": tile["x"],
                        "y": tile["y"],
                        "z": tile["z"],
                        "ground_id": 0,
                        "ground_name": self.item_name(0),
                        "ground_role": "UNKNOWN",
                        "ground_sprite_backed": False,
                        "raw_item_ids": raw_item_ids,
                        "item_ids": [],
                        "item_names": [],
                        "item_roles": [],
                        "sprite_backed_item_ids": [],
                        "missing_sprite_item_ids": [],
                        "render_note": "empty_current_floor_tile_preserves_multifloor_context",
                    }
                )
                continue
            if ground_id > 0:
                role_counts[role] += 1
            if ground_id > 0 and not self.sprite_backed(ground_id):
                missing_sprite_ids[ground_id] += 1

            px = padding + (tile["x"] - min_x) * tile_size
            py = padding + (tile["y"] - min_y) * tile_size
            rendered = self.render_item_stack_on_image(image, item_ids, px, py, tile_size)
            if rendered:
                official_sprite_tiles += 1
            else:
                draw.rectangle((px, py, px + tile_size - 1, py + tile_size - 1), fill=self.color_for_tile(ground_id, role) + (255,))
                if len(item_ids) > 1:
                    draw.rectangle(
                        (px + tile_size // 2, py + tile_size // 2, px + tile_size - 1, py + tile_size - 1),
                        fill=self.color_for_tile(top_id, self.role_for_item(top_id)) + (255,),
                    )
                if ground_id > 0 and not self.sprite_backed(ground_id):
                    draw.line((px, py, px + tile_size - 1, py + tile_size - 1), fill=(220, 40, 40))
                fallback_tiles += 1

            indexed_tiles.append(
                {
                    "x": tile["x"],
                    "y": tile["y"],
                    "z": tile["z"],
                    "ground_id": ground_id,
                    "ground_name": self.item_name(ground_id),
                    "ground_role": role,
                    "ground_sprite_backed": self.sprite_backed(ground_id),
                    "raw_item_ids": raw_item_ids,
                    "item_ids": item_ids,
                    "item_names": [self.item_name(item_id) for item_id in item_ids],
                    "item_roles": [self.role_for_item(item_id) for item_id in item_ids],
                    "sprite_backed_item_ids": [item_id for item_id in item_ids if self.sprite_backed(item_id)],
                    "missing_sprite_item_ids": [item_id for item_id in item_ids if not self.sprite_backed(item_id)],
                }
            )

        image_path = Path(image_path)
        index_path = Path(index_path)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        crop = image.crop((padding, padding, width - padding, height - padding))
        crop.convert("RGB").save(image_path)
        index_path.write_text(json.dumps(indexed_tiles, indent=2, sort_keys=True), encoding="utf-8")

        return {
            **chunk.to_dict(),
            "image": str(image_path),
            "tile_index": str(index_path),
            "indexed_tile_count": len(indexed_tiles),
            "empty_tile_count": empty_tile_count,
            "official_sprite_tiles": official_sprite_tiles,
            "context_floor_tiles": context_floor_tiles,
            "fallback_tiles": fallback_tiles,
            "role_counts": dict(role_counts),
            "missing_ground_sprite_ids": dict(sorted(missing_sprite_ids.items())),
            "all_ground_sprite_backed": not missing_sprite_ids,
            "sprite_decoder": self.sprite_decoder.audit(),
            "rme_floor_sequence": [chunk.z, *rme_floor_sequence],
        }

    def render_item_stack(self, item_ids: list[int], tile_size: int) -> Image.Image | None:
        canvas = Image.new("RGBA", (tile_size * 3, tile_size * 3), (0, 0, 0, 0))
        rendered = self.render_item_stack_on_image(canvas, item_ids, tile_size * 2, tile_size * 2, tile_size)
        return canvas if rendered else None

    def render_item_stack_on_image(
        self,
        image: Image.Image,
        item_ids: list[int],
        px: int,
        py: int,
        tile_size: int,
        opacity: float = 1.0,
    ) -> bool:
        stack = [
            RMEStackItem(
                item_id=item_id,
                appearance_id=self.appearance_id_for_item(item_id),
                role=self.role_for_item(item_id),
                name=self.item_name(item_id),
                source_index=index,
            )
            for index, item_id in enumerate(item_ids)
            if item_id > 0
        ]
        if not stack:
            return False
        rendered = 0
        for item in self.draw_order.sort_stack(stack):
            sprite = self.sprite_for_item(item.item_id)
            if sprite is None:
                continue
            scale = tile_size / 32
            scaled_size = (max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale)))
            scaled = sprite.resize(scaled_size)
            if opacity < 1.0:
                alpha = scaled.getchannel("A").point(lambda value: int(value * opacity))
                scaled.putalpha(alpha)
            paste_x = px - max(0, scaled.width - tile_size)
            paste_y = py - max(0, scaled.height - tile_size)
            image.alpha_composite(scaled, (paste_x, paste_y))
            rendered += 1
        return rendered > 0

    def ground_id_for_stack(self, item_ids: list[int]) -> int:
        for item_id in item_ids:
            if self.role_for_item(item_id) in GROUND_ROLES:
                return item_id
        return item_ids[0] if item_ids else 0

    def context_tile_for(
        self,
        tile_lookup: dict[tuple[int, int, int], dict[str, Any]],
        x: int,
        y: int,
        floor_sequence: list[int],
    ) -> dict[str, Any] | None:
        for z in floor_sequence:
            tile = tile_lookup.get((x, y, z))
            if tile and any(int(item_id) > 0 for item_id in tile.get("items", [])):
                return tile
        return None

    def sprite_for_item(self, item_id: int) -> Image.Image | None:
        appearance_id = self.appearance_id_for_item(item_id)
        if appearance_id is None:
            return None
        render = self.render_catalog.get(str(appearance_id), {})
        sprite_ids = render.get("sprite_ids") or []
        if not sprite_ids:
            return None
        return self.sprite_decoder.decode_sprite(int(sprite_ids[0]))

    def appearance_id_for_item(self, item_id: int) -> int | None:
        item = self.item_catalog.get(str(int(item_id)), {})
        for key in ("appearance_id", "client_id", "lookid", "id"):
            value = item.get(key)
            if value is not None and str(value).isdigit():
                return int(value)
        return None

    def role_for_item(self, item_id: int) -> str:
        item_id = int(item_id)
        for role, ids in self.role_lookup.items():
            if item_id in ids:
                return role
        item = self.item_catalog.get(str(item_id), {})
        roles = item.get("roles") or []
        if roles:
            return str(roles[0]).upper()
        return "UNKNOWN"

    def item_name(self, item_id: int) -> str:
        item = self.item_catalog.get(str(int(item_id)), {})
        return str(item.get("name") or f"item {item_id}")

    def sprite_backed(self, item_id: int) -> bool:
        item = self.item_catalog.get(str(int(item_id)), {})
        appearance_id = item.get("appearance_id") or item.get("client_id") or item.get("lookid") or item.get("id")
        render = self.render_catalog.get(str(appearance_id)) if appearance_id is not None else None
        return bool(render and render.get("sprite_ids"))

    def color_for_tile(self, item_id: int, role: str) -> tuple[int, int, int]:
        base = ROLE_COLORS.get(role, ROLE_COLORS["UNKNOWN"])
        if role == "UNKNOWN":
            return base
        jitter = (int(item_id) * 17) % 25 - 12
        return tuple(max(0, min(255, channel + jitter)) for channel in base)

    def _build_role_lookup(self) -> dict[str, set[int]]:
        lookup: dict[str, set[int]] = {}
        for role, filename in ROLE_FILES.items():
            values = self._load_json(filename, [])
            lookup[role] = {int(value) for value in values if str(value).isdigit()}
        return lookup

    def _load_json(self, filename: str, default: Any) -> Any:
        path = self.root / filename
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))


def select_reference_chunks(
    tiles: list[dict[str, Any]],
    *,
    chunk_size: int = 64,
    max_chunks: int = 4,
) -> list[ReferenceChunk]:
    buckets: Counter[tuple[int, int, int]] = Counter()
    tile_counts: Counter[tuple[int, int, int]] = Counter()
    for tile in tiles:
        item_count = sum(1 for item_id in tile.get("items", []) if int(item_id) > 0)
        if item_count == 0:
            continue
        bucket = (int(tile["x"]) // chunk_size, int(tile["y"]) // chunk_size, int(tile["z"]))
        buckets[bucket] += item_count
        tile_counts[bucket] += 1
    chunks = []
    for index, ((bucket_x, bucket_y, z), score) in enumerate(buckets.most_common(max_chunks)):
        min_x = bucket_x * chunk_size
        min_y = bucket_y * chunk_size
        chunks.append(
            ReferenceChunk(
                name=f"world_ref_z{z}_x{min_x}_y{min_y}",
                bounds=(min_x, min_y, min_x + chunk_size - 1, min_y + chunk_size - 1),
                z=int(z),
                tile_count=tile_counts[(bucket_x, bucket_y, z)],
                density_score=score,
            )
        )
        if index + 1 >= max_chunks:
            break
    return chunks


def build_world_reference_visual_atlas(root: str | Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd())
    world_path = base / "projects" / "world" / "world.otbm"
    output_dir = base / "exports" / "world_reference_visual_atlas"
    return WorldReferenceVisualizer(base).build_reference_atlas(world_path, output_dir)
