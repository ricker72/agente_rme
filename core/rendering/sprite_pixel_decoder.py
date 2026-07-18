"""Minimal PMX-03R1 decoder for Canary catalog sprite sheets."""

from __future__ import annotations

import lzma
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QImage

from .sprite_pixel_source import SpritePixelSourceDiscovery, SpriteSheetCatalogEntry

SPRITE_SHEET_WIDTH = 384
SPRITE_SHEET_HEIGHT = 384
SPRITE_SHEET_BYTES = SPRITE_SHEET_WIDTH * SPRITE_SHEET_HEIGHT * 4
LZMA_UNCOMPRESSED_SIZE = SPRITE_SHEET_BYTES + 512


@dataclass(frozen=True)
class DecodedSpritePixels:
    sprite_id: int
    status: str
    image: QImage | None = None
    source_path: str = ""
    reason: str = ""


class SpritePixelDecoder:
    """Decodes real pixels only when Canary sprite sheet files are present."""

    def __init__(self, discovery: SpritePixelSourceDiscovery | None = None) -> None:
        self.discovery = discovery or SpritePixelSourceDiscovery()
        self.entries = self.discovery.catalog_entries()

    def decode_sprite(self, sprite_id: int) -> DecodedSpritePixels:
        entry = self._entry_for_sprite(sprite_id)
        if entry is None:
            return DecodedSpritePixels(
                sprite_id=sprite_id,
                status="PIXEL_SOURCE_MISSING",
                reason="catalog-content.json or matching sprite sheet entry is missing",
            )
        path = Path(entry.path)
        if not path.exists():
            return DecodedSpritePixels(
                sprite_id=sprite_id,
                status="PIXEL_SOURCE_MISSING",
                source_path=str(path),
                reason="catalog references a sprite sheet file that is not present",
            )
        try:
            sheet = self._decode_canary_sheet(path)
            image = self._extract_sprite_image(sheet, sprite_id, entry)
            return DecodedSpritePixels(
                sprite_id=sprite_id,
                status="REAL_SPRITE_RENDERED",
                image=image,
                source_path=str(path),
            )
        except Exception as exc:
            return DecodedSpritePixels(
                sprite_id=sprite_id,
                status="DECODE_FAILED",
                source_path=str(path),
                reason=f"{type(exc).__name__}: {exc}",
            )

    def _entry_for_sprite(self, sprite_id: int) -> SpriteSheetCatalogEntry | None:
        for entry in self.entries:
            if entry.first_sprite_id <= sprite_id <= entry.last_sprite_id:
                return entry
        return None

    def _decode_canary_sheet(self, path: Path) -> QImage:
        data = path.read_bytes()
        for pos in self._lzma_offsets(data):
            decompressed = self._decompress_raw_lzma(data, pos)
            if not decompressed:
                continue
            sheet = QImage.fromData(decompressed, "BMP")
            if not sheet.isNull():
                return sheet.convertToFormat(QImage.Format.Format_ARGB32)
        raise ValueError("catalog sprite sheet could not be decoded as BMP LZMA")

    def _extract_sprite_image(
        self,
        sheet: QImage,
        sprite_id: int,
        entry: SpriteSheetCatalogEntry,
    ) -> QImage:
        width, height = self._sprite_size(entry.sprite_type)
        sprite_offset = sprite_id - entry.first_sprite_id
        columns = 12 if width == 32 else 6
        row = sprite_offset // columns
        column = sprite_offset % columns
        return sheet.copy(column * width, row * height, width, height)

    def _sprite_size(self, sprite_type: int) -> tuple[int, int]:
        if sprite_type == 1:
            return 32, 64
        if sprite_type == 2:
            return 64, 32
        if sprite_type == 3:
            return 64, 64
        return 32, 32

    def _lzma_offsets(self, data: bytes) -> list[int]:
        offsets: list[int] = []
        for index in range(min(len(data), 128)):
            if data[index] > (4 * 5 + 4) * 9 + 8:
                continue
            if index + 13 > len(data):
                continue
            dictionary_size = int.from_bytes(data[index + 1 : index + 5], "little")
            if dictionary_size <= 0 or dictionary_size > 1 << 30:
                continue
            offsets.append(index)
        return offsets

    def _decompress_raw_lzma(self, data: bytes, pos: int) -> bytes:
        try:
            lclppb = data[pos]
            lc = lclppb % 9
            remainder = lclppb // 9
            lp = remainder % 5
            pb = remainder // 5
            dictionary_size = int.from_bytes(data[pos + 1 : pos + 5], "little")
            decompressor = lzma.LZMADecompressor(
                format=lzma.FORMAT_RAW,
                filters=[
                    {
                        "id": lzma.FILTER_LZMA1,
                        "dict_size": dictionary_size,
                        "lc": lc,
                        "lp": lp,
                        "pb": pb,
                    }
                ],
            )
            return decompressor.decompress(data[pos + 13 :], max_length=LZMA_UNCOMPRESSED_SIZE)
        except lzma.LZMAError:
            return b""
