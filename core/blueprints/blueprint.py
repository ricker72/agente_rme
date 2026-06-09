from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BlueprintTile:
    """A single tile in a blueprint."""
    x: int
    y: int
    ground: int = 0
    item: Optional[int] = None
    decoration: Optional[int] = None
    spawn: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"x": self.x, "y": self.y, "ground": self.ground}
        if self.item is not None:
            d["item"] = self.item
        if self.decoration is not None:
            d["decoration"] = self.decoration
        if self.spawn is not None:
            d["spawn"] = self.spawn
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintTile:
        return cls(
            x=data["x"],
            y=data["y"],
            ground=data.get("ground", 0),
            item=data.get("item"),
            decoration=data.get("decoration"),
            spawn=data.get("spawn"),
        )


@dataclass
class BlueprintMetadata:
    """Metadata associated with a blueprint."""
    style: str = ""
    era: str = "modern"
    difficulty: str = "safe"
    tags: List[str] = field(default_factory=list)
    capacity: str = ""
    hybrid: bool = False


@dataclass
class Blueprint:
    """
    A reusable structure blueprint.

    Supports two modes:
      1. Tile-based: 'tiles' list with explicit (x, y, ground) entries.
      2. Descriptive: 'rooms', 'features', 'grounds', 'walls_items', 'decorations'
         which get expanded into tiles at placement time.
    """
    name: str
    theme: str = "generic"
    category: str = "unknown"
    version: str = "1.0.0"
    size: Tuple[int, int] = (10, 10)
    entry: Optional[Tuple[int, int]] = None
    description: str = ""

    # Tile-based mode
    tiles: List[BlueprintTile] = field(default_factory=list)

    # Descriptive mode (legacy)
    layout: Optional[Dict[str, Any]] = None
    rooms: List[Dict[str, Any]] = field(default_factory=list)
    features: List[Dict[str, Any]] = field(default_factory=list)
    zones: List[Dict[str, Any]] = field(default_factory=list)
    grounds: List[int] = field(default_factory=list)
    walls_items: List[int] = field(default_factory=list)
    decorations: List[int] = field(default_factory=list)

    # Metadata
    metadata: BlueprintMetadata = field(default_factory=BlueprintMetadata)

    # Raw source data (read-only reference)
    _raw: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def is_tile_based(self) -> bool:
        """Check if this blueprint uses the explicit tile-based format."""
        return len(self.tiles) > 0

    @property
    def tags(self) -> List[str]:
        return self.metadata.tags

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize blueprint to a dictionary."""
        d: Dict[str, Any] = {
            "name": self.name,
            "theme": self.theme,
            "category": self.category,
            "version": self.version,
            "size": list(self.size),
            "description": self.description,
        }
        if self.entry is not None:
            d["entry"] = list(self.entry)

        if self.is_tile_based:
            d["tiles"] = [t.to_dict() for t in self.tiles]
        else:
            if self.layout:
                d["layout"] = self.layout
            if self.rooms:
                d["rooms"] = self.rooms
            if self.features:
                d["features"] = self.features
            if self.zones:
                d["zones"] = self.zones
            if self.grounds:
                d["grounds"] = self.grounds
            if self.walls_items:
                d["walls_items"] = self.walls_items
            if self.decorations:
                d["decorations"] = self.decorations

        meta = {}
        if self.metadata.style:
            meta["style"] = self.metadata.style
        if self.metadata.era:
            meta["era"] = self.metadata.era
        if self.metadata.difficulty:
            meta["difficulty"] = self.metadata.difficulty
        if self.metadata.tags:
            meta["tags"] = self.metadata.tags
        if self.metadata.capacity:
            meta["capacity"] = self.metadata.capacity
        if self.metadata.hybrid:
            meta["hybrid"] = True
        if meta:
            d["metadata"] = meta

        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Blueprint:
        """Deserialize a dictionary into a Blueprint instance."""
        size_raw = data.get("size", [10, 10])
        size = (size_raw[0], size_raw[1]) if isinstance(size_raw, (list, tuple)) else (10, 10)

        entry_raw = data.get("entry")
        entry = (entry_raw[0], entry_raw[1]) if isinstance(entry_raw, (list, tuple)) and len(entry_raw) == 2 else None

        tiles_raw = data.get("tiles", [])
        tiles = [BlueprintTile.from_dict(t) for t in tiles_raw] if tiles_raw else []

        meta_raw = data.get("metadata", {})
        meta = BlueprintMetadata(
            style=meta_raw.get("style", ""),
            era=meta_raw.get("era", "modern"),
            difficulty=meta_raw.get("difficulty", "safe"),
            tags=meta_raw.get("tags", []),
            capacity=meta_raw.get("capacity", ""),
            hybrid=meta_raw.get("hybrid", False),
        )

        return cls(
            name=data.get("name", "unnamed"),
            theme=data.get("theme", "generic"),
            category=data.get("category", "unknown"),
            version=data.get("version", "1.0.0"),
            size=size,
            entry=entry,
            description=data.get("description", ""),
            tiles=tiles,
            layout=data.get("layout"),
            rooms=data.get("rooms", []),
            features=data.get("features", []),
            zones=data.get("zones", []),
            grounds=data.get("grounds", []),
            walls_items=data.get("walls_items", []),
            decorations=data.get("decorations", []),
            metadata=meta,
            _raw=data,
        )