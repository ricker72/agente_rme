"""Load RME/Canary tileset membership from official materials XML."""

from __future__ import annotations

from pathlib import Path

from .material_loader import _parse_xml


class TilesetLoader:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def load(self) -> dict[str, set[str]]:
        if not self.root.exists():
            raise FileNotFoundError(f"missing file: {self.root}")
        tilesets: dict[str, set[str]] = {}
        self.unsupported_sources: list[str] = []
        for path in sorted(self.root.glob("*.xml")):
            try:
                xml_root = _parse_xml(path)
            except ValueError as exc:
                self.unsupported_sources.append(str(exc))
                continue
            for tileset in xml_root.findall(".//tileset"):
                name = tileset.get("name") or path.stem.replace("_", " ").title()
                members = tilesets.setdefault(name, set())
                for brush in tileset.findall(".//brush"):
                    brush_name = brush.get("name")
                    if brush_name:
                        members.add(brush_name.lower())
        return tilesets
