from __future__ import annotations

import struct
from dataclasses import dataclass

OTBM_MAGIC = b"\x00\x00\x00\x00"
OTBM_VERSION = 4
ITEM_MAJOR_VERSION = 4
ITEM_MINOR_VERSION = 4


@dataclass(frozen=True)
class OtbmHeader:
    version: int
    width: int
    height: int
    item_major_version: int
    item_minor_version: int

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<IHHII",
            self.version,
            self.width,
            self.height,
            self.item_major_version,
            self.item_minor_version,
        )


def build_header(width: int, height: int) -> OtbmHeader:
    return OtbmHeader(
        version=OTBM_VERSION,
        width=max(1, min(0xFFFF, int(width))),
        height=max(1, min(0xFFFF, int(height))),
        item_major_version=ITEM_MAJOR_VERSION,
        item_minor_version=ITEM_MINOR_VERSION,
    )
