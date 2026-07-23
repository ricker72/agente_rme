from __future__ import annotations

import json
import lzma
import math
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from ..asset_paths import resolve_client_asset_root


@dataclass(frozen=True)
class SpriteBundleReference:
    first_sprite_id: int
    last_sprite_id: int
    path: Path
    sprite_type: int = 0

    @property
    def count(self) -> int:
        return self.last_sprite_id - self.first_sprite_id + 1

    def contains(self, sprite_id: int) -> bool:
        return self.first_sprite_id <= int(sprite_id) <= self.last_sprite_id


class OfficialSpritePixelDecoder:
    """Decode official catalog-content sprite bundles into 32x32 RGBA sprites."""

    def __init__(self, workspace_root: str | Path | None = None, sprite_size: int = 32) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self.assets_root = resolve_client_asset_root(self.workspace_root)
        self.sprite_size = int(sprite_size)
        self.bundles: list[SpriteBundleReference] = []
        self._sheet_cache: dict[Path, Image.Image | None] = {}
        self._sprite_cache: dict[int, Image.Image | None] = {}
        self.decode_attempts = 0
        self.decode_successes = 0
        self.decode_failures = 0
        self.load_catalog()

    def load_catalog(self) -> "OfficialSpritePixelDecoder":
        catalog_path = self.assets_root / "catalog-content.json"
        if not catalog_path.exists():
            return self
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        bundles = []
        for entry in catalog:
            if not isinstance(entry, dict) or entry.get("type") != "sprite":
                continue
            path = self.assets_root / str(entry.get("file", ""))
            if not path.exists():
                continue
            bundles.append(
                SpriteBundleReference(
                    first_sprite_id=int(entry.get("firstspriteid", 0)),
                    last_sprite_id=int(entry.get("lastspriteid", -1)),
                    sprite_type=int(entry.get("spritetype", 0) or 0),
                    path=path,
                )
            )
        self.bundles = sorted(bundles, key=lambda item: item.first_sprite_id)
        return self

    def decode_sprite(self, sprite_id: int) -> Image.Image | None:
        sprite_id = int(sprite_id)
        if sprite_id in self._sprite_cache:
            return self._sprite_cache[sprite_id]
        bundle = self.bundle_for(sprite_id)
        if bundle is None:
            self._sprite_cache[sprite_id] = None
            return None
        sheet = self.decode_bundle_sheet(bundle)
        if sheet is None:
            self._sprite_cache[sprite_id] = None
            return None

        offset = sprite_id - bundle.first_sprite_id
        sprite_width, sprite_height = self.sprite_dimensions(bundle)
        columns = self.columns_for_bundle(bundle, sheet)
        x = (offset % columns) * sprite_width
        y = (offset // columns) * sprite_height
        if x + sprite_width > sheet.width or y + sprite_height > sheet.height:
            self._sprite_cache[sprite_id] = None
            return None
        sprite = sheet.crop((x, y, x + sprite_width, y + sprite_height)).convert("RGBA")
        sprite = self.apply_transparency(sprite)
        self._sprite_cache[sprite_id] = sprite
        return sprite

    def decode_bundle_sheet(self, bundle: SpriteBundleReference) -> Image.Image | None:
        if bundle.path in self._sheet_cache:
            return self._sheet_cache[bundle.path]
        self.decode_attempts += 1
        payload = bundle.path.read_bytes()
        candidates = []
        if payload.startswith(b"BM"):
            candidates.append(payload)
        cip_image = self.decode_cip_lzma_sheet(payload)
        if cip_image is not None:
            self.decode_successes += 1
            self._sheet_cache[bundle.path] = cip_image
            return cip_image
        try:
            decompressed = lzma.decompress(payload)
            if decompressed:
                candidates.append(decompressed)
        except lzma.LZMAError:
            pass
        bm_offset = payload.find(b"BM")
        if bm_offset >= 0:
            candidates.append(payload[bm_offset:])

        for candidate in candidates:
            try:
                image = Image.open(BytesIO(candidate)).convert("RGBA")
                self.decode_successes += 1
                self._sheet_cache[bundle.path] = image
                return image
            except Exception:
                continue
        self.decode_failures += 1
        self._sheet_cache[bundle.path] = None
        return None

    def decode_cip_lzma_sheet(self, payload: bytes) -> Image.Image | None:
        if len(payload) < 48:
            return None
        try:
            pos = 0
            while pos < len(payload) and payload[pos] == 0:
                pos += 1
            if pos + 5 >= len(payload):
                return None
            if payload[pos:pos + 5] != b"\x70\x0A\xFA\x80\x24":
                return None
            pos += 5
            while pos < len(payload):
                value = payload[pos]
                pos += 1
                if (value & 0x80) != 0x80:
                    break
            if pos + 13 > len(payload):
                return None
            lclppb = payload[pos]
            pos += 1
            lc = lclppb % 9
            remainder = lclppb // 9
            lp = remainder % 5
            pb = remainder // 5
            dictionary_size = int.from_bytes(payload[pos:pos + 4], "little")
            pos += 4
            pos += 8
            decompressed = lzma.decompress(
                payload[pos:],
                format=lzma.FORMAT_RAW,
                filters=[{
                    "id": lzma.FILTER_LZMA1,
                    "dict_size": dictionary_size,
                    "lc": lc,
                    "lp": lp,
                    "pb": pb,
                }],
            )
            if len(decompressed) < 122 + 384 * 384 * 4:
                return None
            pixel_offset = int.from_bytes(decompressed[10:14], "little")
            pixel_data = bytearray(decompressed[pixel_offset:pixel_offset + 384 * 384 * 4])
            row_size = 384 * 4
            for y in range(384 // 2):
                top = y * row_size
                bottom = (384 - y - 1) * row_size
                top_row = pixel_data[top:top + row_size]
                pixel_data[top:top + row_size] = pixel_data[bottom:bottom + row_size]
                pixel_data[bottom:bottom + row_size] = top_row
            return Image.frombytes("RGBA", (384, 384), bytes(pixel_data), "raw", "BGRA")
        except Exception:
            return None

    def bundle_for(self, sprite_id: int) -> SpriteBundleReference | None:
        sprite_id = int(sprite_id)
        left = 0
        right = len(self.bundles) - 1
        while left <= right:
            mid = (left + right) // 2
            bundle = self.bundles[mid]
            if bundle.contains(sprite_id):
                return bundle
            if sprite_id < bundle.first_sprite_id:
                right = mid - 1
            else:
                left = mid + 1
        return None

    def columns_for_bundle(self, bundle: SpriteBundleReference, sheet: Image.Image) -> int:
        sprite_width, _sprite_height = self.sprite_dimensions(bundle)
        width_columns = max(1, sheet.width // sprite_width)
        if width_columns * sprite_width == sheet.width:
            return width_columns
        square = int(math.sqrt(max(1, bundle.count)))
        return max(1, square)

    def sprite_dimensions(self, bundle: SpriteBundleReference) -> tuple[int, int]:
        if bundle.sprite_type == 1:
            return 32, 64
        if bundle.sprite_type == 2:
            return 64, 32
        if bundle.sprite_type == 3:
            return 64, 64
        return 32, 32

    def apply_transparency(self, sprite: Image.Image) -> Image.Image:
        rgba = sprite.convert("RGBA")
        pixels = rgba.load()
        transparent_colors = {(255, 0, 255), (0, 0, 0)}
        for y in range(rgba.height):
            for x in range(rgba.width):
                r, g, b, a = pixels[x, y]
                if a == 0 or (r, g, b) in transparent_colors:
                    pixels[x, y] = (r, g, b, 0)
        return rgba

    def audit(self) -> dict[str, Any]:
        return {
            "official_sprite_decoder_ready": bool(self.bundles),
            "bundle_count": len(self.bundles),
            "decode_attempts": self.decode_attempts,
            "decode_successes": self.decode_successes,
            "decode_failures": self.decode_failures,
            "pixel_source": "OFFICIAL_BMP_LZMA_WHEN_DECODABLE",
            "fallback_required": self.decode_successes == 0 and self.decode_attempts > 0,
        }
