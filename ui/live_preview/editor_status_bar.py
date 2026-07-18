"""Compact editor-first status text for the mapping workspace."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EditorStatus:
    project: str = "NECRO"
    town: str = "Necro"
    x: int = 1000
    y: int = 1000
    z: int = 7
    zoom: int = 100
    fps: float = 0.0
    visible_tiles: int = 0
    visible_chunks: int = 0
    item: str = "none"
    brush: str = "Terrain"
    client_id: str = "none"
    sprite_id: str = "none"
    safe_mode: bool = True

    def text(self) -> str:
        safe = "Safe Mode" if self.safe_mode else "Runtime Mode"
        return (
            f"Project: {self.project} | Town: {self.town} | "
            f"x:{self.x} y:{self.y} z:{self.z} | zoom:{self.zoom}% | "
            f"fps:{self.fps:.1f} | visible tiles:{self.visible_tiles} | "
            f"visible chunks:{self.visible_chunks} | item:{self.item} | "
            f"selected item:{self.item} | brush:{self.brush} | "
            f"ClientID:{self.client_id} | SpriteID:{self.sprite_id} | {safe}"
        )
